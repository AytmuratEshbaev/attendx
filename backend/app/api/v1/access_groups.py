"""AccessGroup endpoints — manage access groups with devices and students."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user import User
from app.schemas.access_group import (
    AccessGroupCreate,
    AccessGroupMembershipResponse,
    AccessGroupResponse,
    AccessGroupUpdate,
    SyncResult,
)
from app.schemas.common import SuccessResponse
from app.services.access_group_service import AccessGroupService

router = APIRouter(prefix="/access-groups", tags=["access-groups"])


def _svc(db: AsyncSession) -> AccessGroupService:
    return AccessGroupService(db)


@router.get("", response_model=SuccessResponse[list[AccessGroupResponse]])
async def list_groups(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """List all access groups."""
    groups = await _svc(db).list_groups()
    return SuccessResponse(
        data=[AccessGroupResponse.model_validate(g) for g in groups]
    )


@router.post("", response_model=SuccessResponse[AccessGroupResponse], status_code=201)
async def create_group(
    body: AccessGroupCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Create a new access group."""
    group = await _svc(db).create(body.model_dump())
    return SuccessResponse(data=AccessGroupResponse.model_validate(group))


@router.get("/{group_id}", response_model=SuccessResponse[AccessGroupResponse])
async def get_group(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Get a single access group with its devices and students."""
    group = await _svc(db).get_group(group_id)
    return SuccessResponse(data=AccessGroupResponse.model_validate(group))


@router.put("/{group_id}", response_model=SuccessResponse[AccessGroupResponse])
async def update_group(
    group_id: int,
    body: AccessGroupUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Update access group fields."""
    group = await _svc(db).update_group(
        group_id, body.model_dump(exclude_unset=True)
    )
    return SuccessResponse(data=AccessGroupResponse.model_validate(group))


@router.delete("/{group_id}", response_model=SuccessResponse[dict])
async def delete_group(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Delete an access group."""
    await _svc(db).delete_group(group_id)
    return SuccessResponse(data={"message": "AccessGroup deleted"})


# -- Devices ------------------------------------------------------------------


@router.post(
    "/{group_id}/devices/{device_id}",
    response_model=SuccessResponse[AccessGroupResponse],
)
async def add_device(
    group_id: int,
    device_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Add a terminal device to the access group."""
    group = await _svc(db).add_device(group_id, device_id)
    return SuccessResponse(data=AccessGroupResponse.model_validate(group))


@router.delete(
    "/{group_id}/devices/{device_id}",
    response_model=SuccessResponse[AccessGroupResponse],
)
async def remove_device(
    group_id: int,
    device_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Remove a terminal device from the access group."""
    group = await _svc(db).remove_device(group_id, device_id)
    return SuccessResponse(data=AccessGroupResponse.model_validate(group))


# -- Students -----------------------------------------------------------------


@router.post(
    "/{group_id}/students/{student_id}",
    response_model=SuccessResponse[AccessGroupMembershipResponse],
    status_code=201,
)
async def add_student(
    group_id: int,
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Add student to access group and trigger terminal sync in background."""
    membership = await _svc(db).add_student(group_id, student_id)
    return SuccessResponse(
        data=AccessGroupMembershipResponse.model_validate(membership)
    )


@router.delete(
    "/{group_id}/students/{student_id}",
    response_model=SuccessResponse[dict],
)
async def remove_student(
    group_id: int,
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Remove student from access group and delete from terminal in background."""
    await _svc(db).remove_student(group_id, student_id)
    return SuccessResponse(data={"message": "Student removed from access group"})


@router.post(
    "/{group_id}/students/{student_id}/sync",
    response_model=SuccessResponse[AccessGroupMembershipResponse],
)
async def retry_student_sync(
    group_id: int,
    student_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Retry sync for a single student in the access group."""
    membership = await _svc(db).retry_student_sync(group_id, student_id)
    return SuccessResponse(
        data=AccessGroupMembershipResponse.model_validate(membership)
    )


# -- Categories (bulk add) ----------------------------------------------------


@router.post(
    "/{group_id}/categories/{category_id}",
    response_model=SuccessResponse[dict],
)
async def add_category(
    group_id: int,
    category_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Add all active students from a category to the access group."""
    result = await _svc(db).add_category(group_id, category_id)
    return SuccessResponse(data=result)


# -- Sync ---------------------------------------------------------------------


@router.post("/{group_id}/sync", response_model=SuccessResponse[SyncResult])
async def sync_group(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Manually trigger a full sync of all students in this group to all terminals."""
    result = await _svc(db).sync_group(group_id)
    return SuccessResponse(data=SyncResult(**result))
