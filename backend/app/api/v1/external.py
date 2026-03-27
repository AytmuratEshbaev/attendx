"""External system API endpoints (API Key authentication)."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_api_key, get_db
from app.models.api_key import APIKey
from app.schemas.attendance import AttendanceFilter, AttendanceResponse
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.student import StudentResponse
from app.services.attendance_service import AttendanceService
from app.services.student_service import StudentService

router = APIRouter(prefix="/external", tags=["external"])


class AttendanceQueryRequest(BaseModel):
    date_from: date
    date_to: date
    class_name: str | None = None
    external_ids: list[str] | None = None


def _log_to_response(log) -> AttendanceResponse:
    return AttendanceResponse(
        id=log.id,
        student_id=log.student_id,
        student_name=log.student.name if log.student else "Unknown",
        class_name=log.student.class_name if log.student else None,
        device_name=log.device.name if log.device else None,
        event_time=log.event_time,
        event_type=log.event_type,
        verify_mode=log.verify_mode,
    )


@router.get("/students", response_model=PaginatedResponse[StudentResponse])
async def list_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    _key: Annotated[APIKey, Depends(get_api_key)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    class_name: str | None = None,
    search: str | None = None,
):
    """List students (read-only, API key auth)."""
    svc = StudentService(db)
    skip = (page - 1) * per_page
    students, total = await svc.list_students(skip, per_page, class_name, search)
    data = [StudentResponse.model_validate(s) for s in students]
    return PaginatedResponse.create(data, total, page, per_page)


@router.get(
    "/attendance/today",
    response_model=SuccessResponse[list[AttendanceResponse]],
)
async def today_attendance(
    db: Annotated[AsyncSession, Depends(get_db)],
    _key: Annotated[APIKey, Depends(get_api_key)],
    class_name: str | None = None,
):
    """Get today's attendance (API key auth)."""
    svc = AttendanceService(db)
    logs = await svc.get_today(class_name)
    return SuccessResponse(data=[_log_to_response(log) for log in logs])


@router.post(
    "/attendance/query",
    response_model=PaginatedResponse[AttendanceResponse],
)
async def query_attendance(
    body: AttendanceQueryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _key: Annotated[APIKey, Depends(get_api_key)],
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Query attendance with filters (for MBI-Chat, Kundalik integration)."""
    svc = AttendanceService(db)
    filters = AttendanceFilter(
        date_from=body.date_from,
        date_to=body.date_to,
        class_name=body.class_name,
    )
    skip = (page - 1) * per_page
    logs, total = await svc.get_attendance(filters, skip, per_page)

    # Filter by external_ids if provided
    if body.external_ids:
        logs = [
            log for log in logs
            if log.student and log.student.external_id in body.external_ids
        ]
        total = len(logs)

    data = [_log_to_response(log) for log in logs]
    return PaginatedResponse.create(data, total, page, per_page)
