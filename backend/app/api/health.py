"""Health check endpoints (basic and detailed)."""

import time
from datetime import date
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_db, get_redis, require_role
from app.models.attendance import AttendanceLog
from app.models.device import Device
from app.models.student import Student
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter(tags=["health"])

# Set at import time so uptime is relative to process start
APP_START_TIME = time.time()


@router.get("/health")
async def basic_health() -> dict:
    """Basic health check — suitable for load balancer / uptime monitoring."""
    from datetime import datetime, timezone

    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/detailed")
async def detailed_health(
    _current_user: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis=Depends(get_redis),
) -> dict:
    """
    Detailed health check (admin-only).

    Checks: database, redis, disk, worker heartbeat, devices, data summary.
    """
    import shutil
    from datetime import datetime, timezone

    checks: dict = {}
    overall = "ok"

    # -- Database ---------------------------------------------------------------
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok", "type": "postgresql"}
    except Exception as exc:
        checks["database"] = {"status": "error", "message": str(exc)[:100]}
        overall = "degraded"

    # -- Redis ------------------------------------------------------------------
    try:
        await redis.ping()
        info = await redis.info("memory")
        checks["redis"] = {
            "status": "ok",
            "used_memory": info.get("used_memory_human", "unknown"),
        }
    except Exception as exc:
        checks["redis"] = {"status": "error", "message": str(exc)[:100]}
        overall = "degraded"

    # -- Disk space ------------------------------------------------------------
    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024**3)
        checks["disk"] = {
            "status": "ok" if free_gb > 1 else "warning",
            "free_gb": round(free_gb, 2),
            "used_percent": round(used / total * 100, 1),
        }
        if free_gb < 1:
            overall = "warning"
    except Exception:
        checks["disk"] = {"status": "unknown"}

    # -- Worker heartbeat -------------------------------------------------------
    try:
        worker_ts = await redis.get("worker:heartbeat")
        if worker_ts:
            age = time.time() - float(worker_ts)
            checks["worker"] = {
                "status": "ok" if age < 30 else "warning",
                "last_heartbeat_seconds_ago": round(age),
            }
            if age > 60:
                overall = "degraded"
        else:
            checks["worker"] = {"status": "not_running"}
            if overall == "ok":
                overall = "degraded"
    except Exception:
        checks["worker"] = {"status": "unknown"}

    # -- Devices ----------------------------------------------------------------
    try:
        ids_result = await db.execute(
            select(Device.id).where(Device.is_active == True)  # noqa: E712
        )
        device_ids = ids_result.scalars().all()

        online_count = 0
        for dev_id in device_ids:
            status = await redis.get(f"device:{dev_id}:online")
            if status == "1":
                online_count += 1

        checks["devices"] = {"total": len(device_ids), "online": online_count}
    except Exception:
        checks["devices"] = {"status": "unknown"}

    # -- Data summary ----------------------------------------------------------
    try:
        student_count = (
            await db.execute(
                select(func.count(Student.id)).where(Student.is_active == True)  # noqa: E712
            )
        ).scalar() or 0

        today_events = (
            await db.execute(
                select(func.count(AttendanceLog.id)).where(
                    func.date(AttendanceLog.event_time) == date.today()
                )
            )
        ).scalar() or 0

        checks["data"] = {
            "active_students": student_count,
            "today_events": today_events,
        }
    except Exception:
        checks["data"] = {"status": "unknown"}

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - APP_START_TIME),
        "checks": checks,
    }
