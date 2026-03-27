"""Audit log viewer endpoint (super_admin only)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=SuccessResponse[dict])
async def list_audit_logs(
    _current_user: Annotated[User, Depends(require_role("super_admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: str | None = Query(None),
    action: str | None = Query(None),
    entity_type: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> SuccessResponse[dict]:
    """
    List audit logs with optional filters.

    Filters:
    - ``user_id`` — UUID of the acting user
    - ``action`` — e.g. "login", "create", "delete"
    - ``entity_type`` — e.g. "student", "device", "user"
    - ``date_from`` / ``date_to`` — ISO date strings (YYYY-MM-DD)
    """
    svc = AuditService(db)
    logs, total = await svc.get_logs(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )

    items = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]

    return SuccessResponse(
        data={
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    )
