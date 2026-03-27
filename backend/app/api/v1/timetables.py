"""Timetable endpoints — manage recurring and one-time access schedules."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.timetable import (
    TimetableCreate,
    TimetableResponse,
    TimetableUpdate,
)
from app.services.timetable_service import TimetableService

router = APIRouter(prefix="/timetables", tags=["timetables"])


def _svc(db: AsyncSession) -> TimetableService:
    return TimetableService(db)


@router.get("", response_model=SuccessResponse[list[TimetableResponse]])
async def list_timetables(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
    timetable_type: str | None = Query(
        None,
        pattern="^(recurring|one_time)$",
        description="Filter by timetable type",
    ),
):
    """List all timetables, optionally filtered by timetable_type."""
    items = await _svc(db).list_timetables(timetable_type)
    return SuccessResponse(data=[TimetableResponse.model_validate(t) for t in items])


@router.post("", response_model=SuccessResponse[TimetableResponse], status_code=201)
async def create_timetable(
    body: TimetableCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Create a new recurring or one-time timetable."""
    data = body.model_dump()
    timetable = await _svc(db).create(data)
    return SuccessResponse(data=TimetableResponse.model_validate(timetable))


@router.get("/{timetable_id}", response_model=SuccessResponse[TimetableResponse])
async def get_timetable(
    timetable_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Get a single timetable."""
    timetable = await _svc(db).get_timetable(timetable_id)
    return SuccessResponse(data=TimetableResponse.model_validate(timetable))


@router.put("/{timetable_id}", response_model=SuccessResponse[TimetableResponse])
async def update_timetable(
    timetable_id: int,
    body: TimetableUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Update timetable fields."""
    timetable = await _svc(db).update_timetable(
        timetable_id, body.model_dump(exclude_unset=True)
    )
    return SuccessResponse(data=TimetableResponse.model_validate(timetable))


@router.delete("/{timetable_id}", response_model=SuccessResponse[dict])
async def delete_timetable(
    timetable_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Delete a timetable."""
    await _svc(db).delete_timetable(timetable_id)
    return SuccessResponse(data={"message": "Timetable deleted"})
