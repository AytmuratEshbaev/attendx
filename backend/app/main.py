"""AttendX -- FastAPI Application Entrypoint."""

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.health import router as health_router
from app.api.v1 import router as api_v1_router
from app.config import settings
from app.core.database import close_db, engine, init_db
from app.core.exceptions import AttendXException
from app.core.logging import (
    LoggingMiddleware,
    RequestIDMiddleware,
    setup_logging,
)
from app.core.rate_limit import limiter
from app.core.redis import close_redis, get_redis as _get_redis, init_redis, redis_pool
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.sentry_config import init_sentry

# -- Module-level timestamp for uptime tracking --------------------------------
APP_START_TIME = time.time()

# -- Structured Logging Setup --------------------------------------------------
setup_logging()
logger = structlog.get_logger()

# -- Sentry error tracking (no-op if SENTRY_DSN is empty) ----------------------
init_sentry(
    settings.SENTRY_DSN,
    environment="production" if settings.LOG_LEVEL != "DEBUG" else "development",
)


# -- Lifespan ------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown events."""
    logger.info("attendx_startup", version=settings.APP_VERSION)
    await init_db()
    await init_redis()

    # Initialize webhook engine
    from app.core.database import AsyncSessionLocal
    from app.services.webhook_engine import WebhookEngine
    from app.services.webhook_events import WebhookEventManager, set_webhook_event_manager
    from app.services.webhook_retry import WebhookRetryManager

    webhook_engine = None
    retry_manager = None
    try:
        r = await _get_redis()
        webhook_engine = WebhookEngine(AsyncSessionLocal, r)
        await webhook_engine.initialize()
        retry_manager = WebhookRetryManager(webhook_engine, AsyncSessionLocal, r)
        webhook_engine.set_retry_manager(retry_manager)
        set_webhook_event_manager(WebhookEventManager(webhook_engine))
        logger.info("webhook_engine_initialized")
    except Exception as e:
        logger.warning("webhook_engine_init_failed", error=str(e))

    yield

    # Cleanup
    set_webhook_event_manager(None)
    if retry_manager:
        await retry_manager.stop()
    if webhook_engine:
        await webhook_engine.close()

    await close_redis()
    await close_db()
    logger.info("attendx_shutdown")


# -- App Instance --------------------------------------------------------------

app = FastAPI(
    title="AttendX API",
    description="""
## AttendX — Face Recognition Attendance Platform

REST API for managing Hikvision terminals, students, and attendance monitoring.

### Authentication
- **JWT Bearer**: For admin/teacher dashboard access
- **API Key**: For external system integration (X-API-Key header)

### Rate Limits
- Default: 100 requests/minute
- Login: 10 requests/minute
- Reports/Export: 10 requests/minute
""",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "Authentication & authorization"},
        {"name": "students", "description": "Student management"},
        {"name": "attendance", "description": "Attendance records & statistics"},
        {"name": "devices", "description": "Hikvision terminal management"},
        {"name": "webhooks", "description": "Webhook management & delivery"},
        {"name": "reports", "description": "Report generation (PDF/Excel)"},
        {"name": "external", "description": "External system API (API Key auth)"},
        {"name": "health", "description": "Health checks"},
        {"name": "api-keys", "description": "API key management"},
        {"name": "audit", "description": "Audit log viewer"},
        {"name": "security", "description": "Security administration"},
    ],
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Optional Prometheus metrics
if settings.ENABLE_METRICS:
    from app.core.metrics import setup_metrics
    setup_metrics(app)

# -- Middleware (order matters: last added = first executed) -------------------

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# -- Standard Error Response Helper --------------------------------------------


def _error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str | None = None,
    details: dict | None = None,
) -> JSONResponse:
    error_body: dict = {"code": code, "message": message}
    if details:
        error_body["details"] = details
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error_body,
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
            },
        },
    )


# -- Exception Handlers --------------------------------------------------------


@app.exception_handler(AttendXException)
async def attendx_exception_handler(
    request: Request, exc: AttendXException
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return _error_response(exc.status_code, exc.error_code, exc.message, request_id)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    field_errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        field_errors.append(f"{loc}: {err.get('msg', '')}")
    message = "; ".join(field_errors) if field_errors else "Request validation failed."
    return _error_response(422, "VALIDATION_ERROR", message, request_id)


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        429: "TOO_MANY_REQUESTS",
    }
    error_code = code_map.get(exc.status_code, "HTTP_ERROR")
    return _error_response(exc.status_code, error_code, str(exc.detail), request_id)


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error("unhandled_exception", exc_info=exc)
    return _error_response(
        500, "INTERNAL_ERROR", "An unexpected error occurred.", request_id
    )


# -- API Routers ---------------------------------------------------------------

app.include_router(api_v1_router)
app.include_router(health_router)
