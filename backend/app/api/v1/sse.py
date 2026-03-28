"""Server-Sent Events endpoint for real-time attendance streaming."""

import asyncio
import json
import uuid
from datetime import date, datetime, timezone
from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from jose import JWTError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.core.dependencies import get_redis
from app.core.security import verify_token
from app.models.attendance import AttendanceLog
from app.models.device import Device
from app.models.student import Student
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter(prefix="/sse", tags=["sse"])

_SSE_KEEPALIVE_INTERVAL = 15  # seconds


async def _get_sse_user(request: Request, token: str | None = None) -> User:
    """
    Authenticate SSE connections via:
    1. Authorization: Bearer <token> header (standard)
    2. ?token=<jwt> query param (EventSource fallback — browsers can't set custom headers)
    """
    raw_token: str | None = None

    # Try query param first (for browser EventSource)
    if token:
        raw_token = token
    else:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            raw_token = auth.split(" ", 1)[1]

    if not raw_token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    try:
        payload = verify_token(raw_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid user id in token")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


async def _attendance_event_generator(
    redis,
    class_name: str | None,
    request: Request,
) -> AsyncGenerator[str, None]:
    """
    Subscribe to Redis pub/sub channel and forward attendance events as SSE.
    """
    channel = "notifications:attendance"
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    try:
        yield "event: connected\ndata: {}\n\n"

        last_keepalive = asyncio.get_event_loop().time()

        while True:
            if await request.is_disconnected():
                break

            now = asyncio.get_event_loop().time()
            if now - last_keepalive > _SSE_KEEPALIVE_INTERVAL:
                yield ": keepalive\n\n"
                last_keepalive = now

            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )
            if message is None:
                await asyncio.sleep(0.1)
                continue

            try:
                raw = message.get("data", "")
                if isinstance(raw, bytes):
                    raw = raw.decode()
                payload = json.loads(raw)

                if class_name and payload.get("class_name") != class_name:
                    continue

                event_data = json.dumps(payload, ensure_ascii=False)
                yield f"event: attendance\ndata: {event_data}\n\n"

            except json.JSONDecodeError as e:
                logger.warning("sse_parse_error", error=str(e))
            except Exception as e:
                logger.warning("sse_unexpected_error", error=str(e))

    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
        except Exception:
            logger.debug("sse_pubsub_cleanup_error", exc_info=True)


@router.get("/attendance")
async def attendance_stream(
    request: Request,
    redis=Depends(get_redis),
    class_name: str | None = Query(None, description="Filter by class name"),
    token: str | None = Query(None, description="JWT token for EventSource clients"),
):
    """
    SSE stream for real-time attendance events.

    Subscribe to receive live push notifications instead of polling.

    **Auth**: Pass JWT as `Authorization: Bearer <token>` header,
    or as `?token=<jwt>` query param (required for browser EventSource).

    **Events emitted**:
    - `connected` — initial confirmation
    - `attendance` — new attendance record (JSON)
    - `: keepalive` — heartbeat comment every 15s
    """
    _user = await _get_sse_user(request, token)

    return StreamingResponse(
        _attendance_event_generator(redis, class_name, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


_STATS_CACHE_KEY = "sse:stats:cache"
_STATS_CACHE_TTL = 30  # seconds


async def _fetch_stats(redis) -> dict:
    """Fetch attendance stats — Redis-cached for 30s so all SSE clients share one DB query."""
    cached = await redis.get(_STATS_CACHE_KEY)
    if cached:
        return json.loads(cached)

    today = date.today()
    async with AsyncSessionLocal() as db:
        total = (await db.execute(
            select(func.count(Student.id)).where(Student.is_active.is_(True))
        )).scalar() or 0

        present = (await db.execute(
            select(func.count(func.distinct(AttendanceLog.student_id))).where(
                func.date(AttendanceLog.event_time) == today
            )
        )).scalar() or 0

    payload = {
        "total_students": total,
        "present_today": present,
        "absent_today": max(0, total - present),
        "attendance_percentage": round(present / total * 100) if total else 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await redis.set(_STATS_CACHE_KEY, json.dumps(payload), ex=_STATS_CACHE_TTL)
    return payload


@router.get("/stats")
async def stats_stream(
    request: Request,
    redis=Depends(get_redis),
    token: str | None = Query(None),
):
    """
    SSE stream for live dashboard statistics (refreshed every 30s).
    Stats are Redis-cached so all connected clients share one DB query per 30s.
    """
    _user = await _get_sse_user(request, token)

    async def generate():
        yield "event: connected\ndata: {}\n\n"

        while True:
            if await request.is_disconnected():
                break

            try:
                payload = await _fetch_stats(redis)
                yield f"event: stats\ndata: {json.dumps(payload)}\n\n"
            except Exception as e:
                logger.warning("sse_stats_error", error=str(e))

            for _ in range(300):  # ~30 seconds in 0.1s steps
                if await request.is_disconnected():
                    return
                await asyncio.sleep(0.1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
