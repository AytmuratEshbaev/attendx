"""Reporting endpoints."""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user import User
from app.schemas.attendance import AttendanceStats, DailyAttendance
from app.schemas.common import SuccessResponse
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily")
async def daily_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("teacher"))],
    target_date: date | None = Query(None, alias="date", description="Report date, default today"),
    class_name: str | None = Query(None),
    format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
):
    """Generate daily attendance report."""
    svc = AttendanceService(db)
    d = target_date or date.today()
    content = await svc.generate_report(d, d, class_name, format)
    if format == "pdf":
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=daily_report_{d}.pdf"},
        )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=daily_report_{d}.xlsx"},
    )


@router.get("/weekly")
async def weekly_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("teacher"))],
    start_date: date | None = Query(None, description="Week start date, default this Monday"),
    class_name: str | None = Query(None),
    format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
):
    """Generate weekly attendance report."""
    svc = AttendanceService(db)
    start = start_date or (date.today() - timedelta(days=date.today().weekday()))
    end = start + timedelta(days=6)
    content = await svc.generate_report(start, end, class_name, format)
    if format == "pdf":
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=weekly_report_{start}.pdf"},
        )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=weekly_report_{start}.xlsx"},
    )


@router.get("/monthly")
async def monthly_report(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("teacher"))],
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    class_name: str | None = Query(None),
    format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
):
    """Generate monthly attendance report with summary statistics."""
    import calendar

    svc = AttendanceService(db)
    start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end = date(year, month, last_day)

    # Don't go past today
    if end > date.today():
        end = date.today()

    content = await svc.generate_report(start, end, class_name, format)
    if format == "pdf":
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=monthly_report_{year}-{month:02d}.pdf"},
        )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=monthly_report_{year}-{month:02d}.xlsx"},
    )
