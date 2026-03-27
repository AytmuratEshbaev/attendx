"""Webhook management endpoints."""

import hashlib
import hmac
import json
import secrets
import time
import uuid
from datetime import datetime, timezone
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_redis, require_role
from app.core.error_codes import ErrorCode
from app.core.exceptions import NotFoundException, ValidationException
from app.models.user import User
from app.models.webhook import Webhook
from app.models.webhook_log import WebhookLog
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.webhook import (
    WebhookCreate,
    WebhookLogResponse,
    WebhookResponse,
    WebhookUpdate,
)
from app.services.webhook_circuit_breaker import CircuitBreaker

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

ALLOWED_EVENTS = {
    "attendance.entry",
    "attendance.exit",
    "student.created",
    "student.updated",
    "student.deleted",
    "device.online",
    "device.offline",
    "face.registered",
    "webhook.test",
}


def _validate_webhook_events(events: list[str]) -> None:
    invalid = set(events) - ALLOWED_EVENTS
    if invalid:
        raise ValidationException(
            f"Invalid webhook events: {invalid}. "
            f"Allowed: {sorted(ALLOWED_EVENTS)}",
            error_code=ErrorCode.INVALID_WEBHOOK_EVENT,
        )


def _validate_webhook_url(url: str) -> None:
    if not (url.startswith("https://") or url.startswith("http://")):
        raise ValidationException(
            "Webhook URL must start with https:// or http://",
            error_code=ErrorCode.INVALID_WEBHOOK_URL,
        )


# --------------------------------------------------------------------------- #
# CRUD Endpoints
# --------------------------------------------------------------------------- #


@router.get("", response_model=SuccessResponse[list[WebhookResponse]])
async def list_webhooks(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """List all webhooks (secret excluded from response)."""
    result = await db.execute(select(Webhook))
    webhooks = result.scalars().all()
    data = [WebhookResponse.model_validate(w) for w in webhooks]
    return SuccessResponse(data=data)


@router.post("", response_model=SuccessResponse[WebhookResponse], status_code=201)
async def create_webhook(
    body: WebhookCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin"))],
):
    """Create a new webhook. Secret is shown only on creation."""
    _validate_webhook_url(body.url)
    _validate_webhook_events(body.events)

    secret = body.secret or secrets.token_urlsafe(32)
    webhook = Webhook(
        url=body.url,
        events=body.events,
        secret=secret,
        description=body.description,
        created_by=user.id,
    )
    db.add(webhook)
    await db.flush()
    await db.refresh(webhook)
    return SuccessResponse(data=WebhookResponse.model_validate(webhook))


@router.put("/{webhook_id}", response_model=SuccessResponse[WebhookResponse])
async def update_webhook(
    webhook_id: uuid.UUID,
    body: WebhookUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Update a webhook. Cannot change secret (must delete and recreate)."""
    webhook = await db.get(Webhook, webhook_id)
    if not webhook:
        raise NotFoundException(
            "Webhook not found.", error_code=ErrorCode.WEBHOOK_NOT_FOUND
        )

    update_data = body.model_dump(exclude_unset=True)
    if "events" in update_data:
        _validate_webhook_events(update_data["events"])
    if "url" in update_data:
        _validate_webhook_url(update_data["url"])

    for key, value in update_data.items():
        setattr(webhook, key, value)
    await db.flush()
    await db.refresh(webhook)
    return SuccessResponse(data=WebhookResponse.model_validate(webhook))


@router.delete("/{webhook_id}", response_model=SuccessResponse[dict])
async def delete_webhook(
    webhook_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Delete a webhook and all associated logs."""
    webhook = await db.get(Webhook, webhook_id)
    if not webhook:
        raise NotFoundException(
            "Webhook not found.", error_code=ErrorCode.WEBHOOK_NOT_FOUND
        )

    # Delete associated logs first
    logs_result = await db.execute(
        select(WebhookLog).where(WebhookLog.webhook_id == webhook_id)
    )
    for log in logs_result.scalars().all():
        await db.delete(log)

    await db.delete(webhook)
    await db.flush()
    return SuccessResponse(data={"message": "Webhook deleted."})


# --------------------------------------------------------------------------- #
# Logs
# --------------------------------------------------------------------------- #


@router.get(
    "/{webhook_id}/logs",
    response_model=PaginatedResponse[WebhookLogResponse],
)
async def webhook_logs(
    webhook_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    success: bool | None = Query(None, description="Filter by success status"),
):
    """Get delivery logs for a webhook."""
    webhook = await db.get(Webhook, webhook_id)
    if not webhook:
        raise NotFoundException(
            "Webhook not found.", error_code=ErrorCode.WEBHOOK_NOT_FOUND
        )

    skip = (page - 1) * per_page

    where_clause = WebhookLog.webhook_id == webhook_id
    if success is not None:
        where_clause = where_clause & (WebhookLog.success == success)

    total_result = await db.execute(
        select(func.count())
        .select_from(WebhookLog)
        .where(where_clause)
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        select(WebhookLog)
        .where(where_clause)
        .order_by(WebhookLog.created_at.desc())
        .offset(skip)
        .limit(per_page)
    )
    logs = result.scalars().all()
    data = [WebhookLogResponse.model_validate(log) for log in logs]
    return PaginatedResponse.create(data, total, page, per_page)


# --------------------------------------------------------------------------- #
# Test Delivery
# --------------------------------------------------------------------------- #


@router.post("/{webhook_id}/test", response_model=SuccessResponse[dict])
async def test_webhook(
    webhook_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Send a test ping to the webhook."""
    webhook = await db.get(Webhook, webhook_id)
    if not webhook:
        raise NotFoundException(
            "Webhook not found.", error_code=ErrorCode.WEBHOOK_NOT_FOUND
        )

    payload = {
        "event": "webhook.test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Test from AttendX",
    }

    body = json.dumps(payload)
    signature = hmac.new(
        webhook.secret.encode(), body.encode(), hashlib.sha256
    ).hexdigest()

    delivered = False
    status_code = 0
    response_time_ms = 0
    response_body = ""

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                webhook.url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-AttendX-Signature": f"sha256={signature}",
                    "X-AttendX-Event": "webhook.test",
                },
            )
            status_code = resp.status_code
            response_body = resp.text[:500]
            delivered = 200 <= status_code < 300
    except Exception as e:
        response_body = str(e)[:500]
    finally:
        response_time_ms = int((time.monotonic() - start) * 1000)

    # Log the delivery
    log_entry = WebhookLog(
        webhook_id=webhook_id,
        event_type="webhook.test",
        payload=payload,
        response_status=status_code or None,
        response_body=response_body,
        success=delivered,
        duration_ms=response_time_ms,
    )
    db.add(log_entry)
    await db.flush()

    return SuccessResponse(data={
        "delivered": delivered,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
    })


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #


@router.get("/stats", response_model=SuccessResponse[dict])
async def webhook_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
    redis=Depends(get_redis),
):
    """Get overall webhook system statistics."""
    # Total and active webhooks
    total_wh = await db.execute(
        select(func.count()).select_from(Webhook)
    )
    active_wh = await db.execute(
        select(func.count())
        .select_from(Webhook)
        .where(Webhook.is_active.is_(True))
    )

    # Today's deliveries
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_total = await db.execute(
        select(func.count())
        .select_from(WebhookLog)
        .where(WebhookLog.created_at >= today_start)
    )
    today_success = await db.execute(
        select(func.count())
        .select_from(WebhookLog)
        .where(
            (WebhookLog.created_at >= today_start)
            & WebhookLog.success.is_(True)
        )
    )
    total_today = today_total.scalar() or 0
    success_today = today_success.scalar() or 0

    # Retry queue and dead letter counts
    retry_queue_size = await redis.zcard("webhook:retry:queue")
    dead_letter_count = await redis.llen("webhook:dead_letter")

    # Circuit breaker statuses for all active webhooks
    cb = CircuitBreaker(redis)
    active_webhooks_result = await db.execute(
        select(Webhook).where(Webhook.is_active.is_(True))
    )
    circuit_breakers = []
    for wh in active_webhooks_result.scalars().all():
        status = await cb.get_status(str(wh.id))
        if status["state"] != "closed" or status["consecutive_failures"] > 0:
            circuit_breakers.append(status)

    return SuccessResponse(data={
        "total_webhooks": total_wh.scalar() or 0,
        "active_webhooks": active_wh.scalar() or 0,
        "total_deliveries_today": total_today,
        "success_rate_today": (
            round(success_today / total_today * 100, 2)
            if total_today > 0
            else 0.0
        ),
        "retry_queue_size": retry_queue_size,
        "dead_letter_count": dead_letter_count,
        "circuit_breakers": circuit_breakers,
    })


# --------------------------------------------------------------------------- #
# Manual Retry
# --------------------------------------------------------------------------- #


@router.post("/{webhook_id}/retry", response_model=SuccessResponse[dict])
async def manual_retry(
    webhook_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
    redis=Depends(get_redis),
    log_id: uuid.UUID = Query(..., description="Webhook log ID to retry"),
):
    """Manually retry a specific failed delivery."""
    webhook = await db.get(Webhook, webhook_id)
    if not webhook:
        raise NotFoundException(
            "Webhook not found.", error_code=ErrorCode.WEBHOOK_NOT_FOUND
        )

    log = await db.get(WebhookLog, log_id)
    if not log or log.webhook_id != webhook_id:
        raise NotFoundException(
            "Webhook log not found.", error_code=ErrorCode.WEBHOOK_NOT_FOUND
        )

    from app.services.webhook_retry import WebhookRetryManager
    from app.services.webhook_engine import WebhookEngine
    from app.core.database import AsyncSessionLocal

    engine = WebhookEngine(AsyncSessionLocal, redis)
    await engine.initialize()
    try:
        result = await engine.deliver(webhook, log.event_type, log.payload)
        # Log the retry
        retry_log = WebhookLog(
            webhook_id=webhook_id,
            event_type=log.event_type,
            payload=log.payload,
            response_status=result.status_code or None,
            response_body=(
                result.response_body[:2000] if result.response_body else None
            ),
            attempts=log.attempts + 1,
            success=result.success,
            delivery_id=result.delivery_id,
            duration_ms=result.duration_ms,
            error_message=result.error,
        )
        db.add(retry_log)
        await db.flush()
    finally:
        await engine.close()

    return SuccessResponse(data={
        "retried": True,
        "success": result.success,
        "status_code": result.status_code,
        "duration_ms": result.duration_ms,
    })


# --------------------------------------------------------------------------- #
# Circuit Breaker
# --------------------------------------------------------------------------- #


@router.get(
    "/{webhook_id}/circuit-breaker", response_model=SuccessResponse[dict]
)
async def circuit_breaker_status(
    webhook_id: uuid.UUID,
    _user: Annotated[User, Depends(require_role("admin"))],
    redis=Depends(get_redis),
):
    """Get circuit breaker status for a webhook."""
    cb = CircuitBreaker(redis)
    status = await cb.get_status(str(webhook_id))
    return SuccessResponse(data=status)


@router.post(
    "/{webhook_id}/circuit-breaker/reset",
    response_model=SuccessResponse[dict],
)
async def reset_circuit_breaker(
    webhook_id: uuid.UUID,
    _user: Annotated[User, Depends(require_role("admin"))],
    redis=Depends(get_redis),
):
    """Manually reset circuit breaker for a webhook."""
    cb = CircuitBreaker(redis)
    await cb.reset(str(webhook_id))
    return SuccessResponse(data={
        "webhook_id": str(webhook_id),
        "state": "closed",
        "message": "Circuit breaker reset successfully.",
    })


# --------------------------------------------------------------------------- #
# Dead Letter Queue
# --------------------------------------------------------------------------- #


@router.get("/dead-letter", response_model=SuccessResponse[list[dict]])
async def dead_letter_queue(
    _user: Annotated[User, Depends(require_role("admin"))],
    redis=Depends(get_redis),
    limit: int = Query(20, ge=1, le=100),
):
    """View dead letter queue (permanently failed deliveries)."""
    items = await redis.lrange("webhook:dead_letter", 0, limit - 1)
    result = []
    for i, item in enumerate(items):
        data = json.loads(item)
        data["index"] = i
        result.append(data)
    return SuccessResponse(data=result)


@router.post(
    "/dead-letter/{index}/retry", response_model=SuccessResponse[dict]
)
async def retry_dead_letter(
    index: int,
    _user: Annotated[User, Depends(require_role("admin"))],
    redis=Depends(get_redis),
):
    """Retry a specific dead letter item."""
    item = await redis.lindex("webhook:dead_letter", index)
    if not item:
        raise NotFoundException("Dead letter item not found.")

    data = json.loads(item)
    # Re-queue for retry (attempt 0 = immediate)
    from app.services.webhook_retry import WebhookRetryManager
    from app.services.webhook_engine import WebhookEngine
    from app.core.database import AsyncSessionLocal

    engine = WebhookEngine(AsyncSessionLocal, redis)
    retry_mgr = WebhookRetryManager(engine, AsyncSessionLocal, redis)
    await retry_mgr.queue_retry(
        data["webhook_id"], data["event_type"], data["payload"], 0
    )
    await redis.lrem("webhook:dead_letter", 1, item)

    return SuccessResponse(data={
        "message": "Dead letter item re-queued for delivery.",
        "webhook_id": data["webhook_id"],
        "event_type": data["event_type"],
    })
