"""Student management endpoints."""

import asyncio
import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_role
from app.models.user import User
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.student import (
    StudentCreate,
    StudentImportResult,
    StudentResponse,
    StudentUpdate,
)
from app.services.student_service import StudentService
from app.services.webhook_events import get_webhook_event_manager

logger = structlog.get_logger()
router = APIRouter(prefix="/students", tags=["students"])


def _svc(db: AsyncSession) -> StudentService:
    return StudentService(db)


def _fire_webhook(coro) -> None:
    """Fire-and-forget a webhook event coroutine."""
    try:
        loop = asyncio.get_running_loop()
        task = loop.create_task(coro)
        task.add_done_callback(
            lambda t: (
                logger.error("webhook_fire_error", error=str(t.exception()))
                if t.exception()
                else None
            )
        )
    except RuntimeError:
        pass


async def _bg_sync_all_groups(student_id: uuid.UUID) -> None:
    """Re-sync student face to all access groups using its own DB session."""
    from app.core.database import AsyncSessionLocal
    from app.services.access_group_service import _bg_sync_student
    from app.repositories.access_group_repo import AccessGroupRepository
    from app.models.access_group import AccessGroup

    async with AsyncSessionLocal() as session:
        repo = AccessGroupRepository(session)
        memberships = await repo.get_student_memberships(student_id)
        for membership in memberships:
            group = await session.get(AccessGroup, membership.access_group_id)
            if not group:
                continue
            device_ids = [d.id for d in group.devices]
            timetable_id = group.timetable_id
            asyncio.create_task(
                _bg_sync_student(
                    membership.id,
                    membership.access_group_id,
                    student_id,
                    device_ids,
                    timetable_id,
                )
            )


# IMPORTANT: /import and /export must be registered BEFORE /{student_id}


@router.post(
    "/import",
    response_model=SuccessResponse[StudentImportResult],
)
async def import_students(
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Bulk import students from Excel (.xlsx)."""
    result = await _svc(db).import_from_excel(file)
    return SuccessResponse(data=result)


@router.get("/export", response_model=None)
async def export_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
    class_name: str | None = None,
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
):
    """Export students to Excel or CSV."""
    svc = _svc(db)
    if format == "csv":
        content = await svc.export_to_csv(class_name)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=students.csv"},
        )
    content = await svc.export_to_excel(class_name)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=students.xlsx"},
    )


@router.get("", response_model=PaginatedResponse[StudentResponse])
async def list_students(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    class_name: str | None = Query(None, description="Filter by class name"),
    category_id: int | None = Query(None, description="Filter by category id"),
    no_category: bool = Query(False, description="Filter students with no category"),
    search: str | None = Query(None, description="Search by name"),
    is_active: bool = Query(True, description="Filter by active status"),
    sort: str = Query(
        "-created_at",
        description="Sort field. Prefix '-' for desc. Options: name, class_name, created_at",
    ),
):
    """List students with pagination, filtering, and sorting."""
    skip = (page - 1) * per_page
    students, total = await _svc(db).list_students(
        skip, per_page, class_name, search, is_active, sort,
        category_id, no_category=no_category,
    )
    data = [StudentResponse.model_validate(s) for s in students]
    return PaginatedResponse.create(data, total, page, per_page)


@router.post("", response_model=SuccessResponse[StudentResponse], status_code=201)
async def create_student(
    body: StudentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Create a new student."""
    student = await _svc(db).create_student(body)

    mgr = get_webhook_event_manager()
    if mgr:
        _fire_webhook(mgr.on_student_created(student))

    return SuccessResponse(data=StudentResponse.model_validate(student))


@router.get("/{student_id}", response_model=SuccessResponse[StudentResponse])
async def get_student(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
):
    """Get a single student by ID."""
    student = await _svc(db).get_student(student_id)
    return SuccessResponse(data=StudentResponse.model_validate(student))


@router.put("/{student_id}", response_model=SuccessResponse[StudentResponse])
async def update_student(
    student_id: uuid.UUID,
    body: StudentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Update a student."""
    changed_fields = list(body.model_dump(exclude_unset=True).keys())
    student = await _svc(db).update_student(student_id, body)

    mgr = get_webhook_event_manager()
    if mgr and changed_fields:
        _fire_webhook(mgr.on_student_updated(student, changed_fields))

    return SuccessResponse(data=StudentResponse.model_validate(student))


@router.delete("/{student_id}", response_model=SuccessResponse[dict])
async def delete_student(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Soft-delete a student (set is_active=False)."""
    student = await _svc(db).delete_student(student_id)

    mgr = get_webhook_event_manager()
    if mgr:
        _fire_webhook(mgr.on_student_deleted(student))

    return SuccessResponse(data={"message": "Student deactivated"})


@router.get("/{student_id}/face")
async def get_face(
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
):
    """Return the stored face image for a student."""
    from pathlib import Path

    student = await _svc(db).get_student(student_id)
    path = Path(f"./data/faces/{student_id}.jpg")
    if not path.exists():
        return Response(status_code=404)
    return Response(content=path.read_bytes(), media_type="image/jpeg", headers={"Cache-Control": "max-age=3600"})


@router.post(
    "/{student_id}/face",
    response_model=SuccessResponse[StudentResponse],
)
async def upload_face(
    student_id: uuid.UUID,
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Upload a face image for a student (JPEG/PNG, max 5MB)."""
    student = await _svc(db).register_face(student_id, file)

    mgr = get_webhook_event_manager()
    if mgr:
        _fire_webhook(mgr.on_face_registered(student, device_count=0))

    # Re-sync to all access groups (own session — request session closes before task runs)
    _fire_webhook(_bg_sync_all_groups(student.id))

    return SuccessResponse(data=StudentResponse.model_validate(student))
