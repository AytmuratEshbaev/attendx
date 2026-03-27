"""API key management endpoints (super_admin only)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_manager import APIKeyManager
from app.core.dependencies import get_db, require_role
from app.models.user import User
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=SuccessResponse[dict])
async def create_api_key(
    body: dict,
    current_user: Annotated[User, Depends(require_role("super_admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
) -> SuccessResponse[dict]:
    """
    Create a new API key.

    The raw key value is returned **once only** — store it securely.
    Body: {"name": str, "permissions": list[str]}
    """
    name: str = body.get("name", "")
    if not name:
        from app.core.exceptions import ValidationException
        raise ValidationException("name is required")

    permissions: list[str] | None = body.get("permissions")
    manager = APIKeyManager(db)
    result = await manager.create_key(
        name=name,
        permissions=permissions,
        created_by=current_user.id,
    )
    await db.commit()
    return SuccessResponse(data=result)


@router.get("", response_model=SuccessResponse[list])
async def list_api_keys(
    _current_user: Annotated[User, Depends(require_role("super_admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[list]:
    """List all API keys (raw key values are never returned)."""
    manager = APIKeyManager(db)
    keys = await manager.list_keys()
    return SuccessResponse(data=keys)


@router.post("/{key_id}/rotate", response_model=SuccessResponse[dict])
async def rotate_api_key(
    key_id: str,
    _current_user: Annotated[User, Depends(require_role("super_admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[dict]:
    """
    Rotate an API key: deactivate the old one and return a new one.

    The new raw key is returned once — store it securely.
    """
    manager = APIKeyManager(db)
    result = await manager.rotate_key(key_id)
    await db.commit()
    return SuccessResponse(data=result)


@router.delete("/{key_id}", response_model=SuccessResponse[dict])
async def revoke_api_key(
    key_id: str,
    _current_user: Annotated[User, Depends(require_role("super_admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[dict]:
    """Permanently deactivate an API key."""
    manager = APIKeyManager(db)
    await manager.revoke_key(key_id)
    await db.commit()
    return SuccessResponse(data={"message": "API key revoked", "key_id": key_id})
