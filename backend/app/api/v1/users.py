"""User management endpoints (admin only)."""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.core.exceptions import DuplicateException, NotFoundException, ValidationException
from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.common import PaginatedResponse, SuccessResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str | None = None
    password: str = Field(..., min_length=6)
    role: str = Field("teacher", pattern="^(super_admin|admin|teacher)$")


class UserUpdateRequest(BaseModel):
    email: str | None = None
    role: str | None = Field(None, pattern="^(super_admin|admin|teacher)$")
    is_active: bool | None = None


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: str | None = Query(None, description="Filter by role"),
):
    """List all users with pagination."""
    query = select(User)
    count_query = select(func.count(User.id))

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    users = result.scalars().all()

    data = [UserResponse.model_validate(u) for u in users]
    return PaginatedResponse.create(data, total, page, per_page)


@router.post("", response_model=SuccessResponse[UserResponse], status_code=201)
async def create_user(
    body: UserCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[User, Depends(require_role("admin"))],
):
    """Create a new user."""
    existing = (
        await db.execute(select(User).where(User.username == body.username))
    ).scalar_one_or_none()
    if existing:
        raise DuplicateException(
            f"Username '{body.username}' already exists.",
        )

    user = User(
        id=uuid.uuid4(),
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    logger.info("user_created", username=body.username, role=body.role)
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.put("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("admin"))],
):
    """Update a user's role, email, or active status."""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException(
            "User not found."
        )

    # Prevent demoting the only super_admin
    if user.role == "super_admin" and body.role and body.role != "super_admin":
        count = (
            await db.execute(
                select(func.count(User.id)).where(User.role == "super_admin")
            )
        ).scalar() or 0
        if count <= 1:
            raise ValidationException("Cannot demote the only super_admin.")

    update_data = body.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    await db.flush()
    await db.refresh(user)

    logger.info("user_updated", user_id=str(user_id))
    return SuccessResponse(data=UserResponse.model_validate(user))


@router.delete("/{user_id}", response_model=SuccessResponse[dict])
async def delete_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("admin"))],
):
    """Delete a user. Cannot delete super_admin accounts."""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException(
            "User not found."
        )

    if user.role == "super_admin":
        raise ValidationException("Cannot delete a super_admin account.")

    if user.id == current_user.id:
        raise ValidationException("Cannot delete your own account.")

    await db.delete(user)
    await db.flush()

    logger.info("user_deleted", user_id=str(user_id), username=user.username)
    return SuccessResponse(data={"message": f"User '{user.username}' deleted."})
