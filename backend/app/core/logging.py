"""Structured logging configuration with structlog."""

import time
import uuid

import structlog
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

_LOG_LEVELS = {
    "critical": 50,
    "exception": 40,
    "error": 40,
    "warn": 30,
    "warning": 30,
    "info": 20,
    "debug": 10,
    "notset": 0,
}


def _mask_sensitive_processor(logger, method_name, event_dict):  # type: ignore[no-untyped-def]
    """Structlog processor — mask sensitive fields before emitting log records."""
    from app.core.data_masking import DataMasker

    return DataMasker.mask_dict(event_dict)


def setup_logging() -> None:
    """Configure structlog for the application."""
    level = _LOG_LEVELS.get(settings.LOG_LEVEL.lower(), 20)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            _mask_sensitive_processor,
            structlog.dev.ConsoleRenderer()
            if settings.APP_ENV == "development"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a bound logger, optionally with a name."""
    log = structlog.get_logger()
    if name:
        log = log.bind(logger=name)
    return log


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a unique request_id into every request/response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get(
            "X-Request-ID", str(uuid.uuid4())
        )
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status, duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        log = structlog.get_logger()
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        log.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
