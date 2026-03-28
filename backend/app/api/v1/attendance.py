"""Attendance tracking endpoints."""

import asyncio
import base64
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as aioredis
import structlog

from app.core.dependencies import get_current_active_user, get_db, get_redis, require_role
from app.models.user import User
from app.schemas.attendance import (
    AttendanceFilter,
    AttendanceResponse,
    AttendanceStats,
    DailyAttendance,
    DeviceLiveEvent,
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.student import StudentResponse
from app.services.attendance_service import AttendanceService
from app.services.student_service import StudentService

router = APIRouter(prefix="/attendance", tags=["attendance"])
logger = structlog.get_logger()


def _svc(db: AsyncSession) -> AttendanceService:
    return AttendanceService(db)


def _log_to_response(log) -> AttendanceResponse:
    return AttendanceResponse(
        id=log.id,
        student_id=log.student_id,
        student_name=log.student.name if log.student else "Unknown",
        class_name=log.student.class_name if log.student else None,
        category_name=(
            log.student.category.name
            if log.student and log.student.category
            else None
        ),
        device_name=log.device.name if log.device else None,
        event_time=log.event_time,
        event_type=log.event_type,
        verify_mode=log.verify_mode,
        picture_url=log.picture_url,
    )


@router.get("/today", response_model=SuccessResponse[list[AttendanceResponse]])
async def today_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
    class_name: str | None = None,
):
    """Get today's attendance records."""
    logs = await _svc(db).get_today(class_name)
    return SuccessResponse(data=[_log_to_response(log) for log in logs])


@router.get("/capture-image")
async def capture_image_proxy(
    db: Annotated[AsyncSession, Depends(get_db)],
    url: str = Query(..., description="base64-encoded Hikvision pictureURL"),
):
    """Proxy a Hikvision capture image URL using device Digest credentials."""
    from urllib.parse import urlparse
    from app.core.security import decrypt_device_password
    from app.repositories.device_repo import DeviceRepository

    try:
        decoded_url = base64.b64decode(url).decode()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid url encoding")

    parsed = urlparse(decoded_url)
    if parsed.scheme != "http" or not parsed.hostname:
        raise HTTPException(status_code=403, detail="URL not allowed")

    # Find device by IP to get Digest credentials
    device_repo = DeviceRepository(db)
    devices = await device_repo.get_active_devices()
    device = next((d for d in devices if d.ip_address == parsed.hostname), None)

    auth = None
    if device:
        password = decrypt_device_password(device.password_enc)
        auth = httpx.DigestAuth(device.username, password)

    try:
        async with httpx.AsyncClient(timeout=2.0, auth=auth) as client:
            resp = await client.get(decoded_url)
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found on device")
        content_type = resp.headers.get("content-type", "")
        # Hikvision returns HTML error page (session expired) with status 200 —
        # detect this and return 404 so frontend falls back to stored profile photo
        if "text/html" in content_type or (
            resp.content[:4] not in (b"\xff\xd8\xff", b"\x89PN", b"GIF") and
            b"<html" in resp.content[:200].lower()
        ):
            raise HTTPException(status_code=404, detail="Image not available (session expired)")
        return Response(
            content=resp.content,
            media_type=content_type or "image/jpeg",
        )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not reach device")


@router.get("/device-live", response_model=SuccessResponse[list[DeviceLiveEvent]])
async def device_live_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=500),
):
    """Fetch the most recent attendance events directly from all active devices (no DB write)."""
    from app.config import settings
    from app.core.security import decrypt_device_password
    from app.repositories.device_repo import DeviceRepository
    from worker.hikvision.client import HikvisionClient

    repo = DeviceRepository(db)
    devices = await repo.get_active_devices()

    now = datetime.now(timezone.utc)
    offset = timedelta(hours=settings.DEVICE_TZ_OFFSET_HOURS)
    start_for_device = (now - timedelta(hours=hours)) + offset
    end_for_device = now + offset + timedelta(hours=2)  # buffer for device clock drift

    async def fetch_device(device) -> list[DeviceLiveEvent]:
        try:
            password = decrypt_device_password(device.password_enc)
            client = HikvisionClient(
                host=device.ip_address,
                port=device.port,
                username=device.username,
                password=password,
            )
            events = await client.get_attendance_logs(start_for_device, end_for_device)
            return [
                DeviceLiveEvent(
                    device_name=device.name,
                    employee_no=e.employee_no,
                    student_name=e.name,
                    event_time=e.event_time,
                    event_type=e.event_type,
                    verify_mode=e.verify_mode,
                    picture_url=e.picture_url,
                )
                for e in events
            ]
        except Exception:
            logger.warning("device_live_fetch_failed", device_id=device.id, name=device.name, exc_info=True)
            return []

    results = await asyncio.gather(*[fetch_device(d) for d in devices])
    all_events: list[DeviceLiveEvent] = []
    for batch in results:
        all_events.extend(batch)

    all_events.sort(key=lambda e: e.event_time, reverse=True)
    return SuccessResponse(data=all_events[:limit])


@router.post("/force-poll", response_model=SuccessResponse[dict])
async def force_poll(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
    hours: int = Query(24, ge=1, le=168),
):
    """Reset last_poll Redis keys so the worker re-fetches the last N hours from all devices."""
    from app.repositories.device_repo import DeviceRepository
    repo = DeviceRepository(db)
    devices = await repo.get_active_devices()

    lookback = datetime.now(timezone.utc) - timedelta(hours=hours)
    reset_count = 0
    for device in devices:
        key = f"hikvision:last_poll:{device.id}"
        await redis.set(key, lookback.isoformat())
        reset_count += 1

    return SuccessResponse(data={"reset_devices": reset_count, "lookback_hours": hours})


@router.get("/recent", response_model=SuccessResponse[list[AttendanceResponse]])
async def recent_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(100, ge=1, le=200),
):
    """Get the most recent N attendance records regardless of date."""
    logs = await _svc(db).get_recent(limit)
    return SuccessResponse(data=[_log_to_response(log) for log in logs])


@router.get("/stats", response_model=SuccessResponse[AttendanceStats])
async def attendance_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
    target_date: date | None = Query(None, alias="date", description="Date for stats (default: today)"),
    class_name: str | None = Query(None),
):
    """Get attendance statistics for a given date."""
    stats = await _svc(db).get_stats(target_date, class_name)
    return SuccessResponse(data=stats)


@router.get("/weekly", response_model=SuccessResponse[list[DailyAttendance]])
async def weekly_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
    start_date: date | None = Query(None, description="Week start (default: this Monday)"),
    class_name: str | None = Query(None),
):
    """Get daily attendance for a week (7 days)."""
    stats = await _svc(db).get_weekly_stats(start_date, class_name)
    return SuccessResponse(data=stats)


@router.get("/report")
async def attendance_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("teacher"))],
    date_from: date = Query(..., description="Report start date"),
    date_to: date = Query(..., description="Report end date"),
    class_name: str | None = Query(None),
    format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
):
    """Generate attendance report (Excel or PDF)."""
    content = await _svc(db).generate_report(date_from, date_to, class_name, format)
    if format == "pdf":
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=attendance_report.pdf"},
        )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=attendance_report.xlsx"},
    )


@router.get(
    "/student/{student_id}",
    response_model=SuccessResponse[dict],
)
async def student_attendance(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
):
    """Get attendance history for a specific student."""
    student_svc = StudentService(db)
    student = await student_svc.get_student(student_id)

    records = await _svc(db).get_student_attendance(student_id, date_from, date_to)
    record_data = [_log_to_response(r) for r in records]

    # Calculate stats
    if records:
        d_from = date_from or (date.today() - timedelta(days=30))
        d_to = date_to or date.today()
        total_days = (d_to - d_from).days + 1
        present_days = len({r.event_time.date() for r in records})
    else:
        total_days = 0
        present_days = 0

    pct = round((present_days / total_days * 100), 1) if total_days else 0.0

    return SuccessResponse(data={
        "student": StudentResponse.model_validate(student).model_dump(),
        "records": [r.model_dump() for r in record_data],
        "stats": {
            "total_days": total_days,
            "present_days": present_days,
            "percentage": pct,
        },
    })


@router.get("", response_model=PaginatedResponse[AttendanceResponse])
async def list_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    date_from: date | None = None,
    date_to: date | None = None,
    class_name: str | None = None,
    student_id: uuid.UUID | None = None,
    event_type: str | None = Query(None, pattern="^(entry|exit)$"),
    sort: str = Query("-event_time"),
):
    """List attendance records with comprehensive filtering."""
    skip = (page - 1) * per_page
    filters = AttendanceFilter(
        date_from=date_from,
        date_to=date_to,
        class_name=class_name,
        student_id=student_id,
        event_type=event_type,
    )
    logs, total = await _svc(db).get_attendance(filters, skip, per_page)
    data = [_log_to_response(log) for log in logs]
    return PaginatedResponse.create(data, total, page, per_page)
