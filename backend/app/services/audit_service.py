"""Audit logging service for compliance and debugging."""

import uuid
from datetime import date, datetime, timedelta, timezone

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = structlog.get_logger()


class AuditService:
    """Create and query AuditLog entries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        user_id: str | uuid.UUID | None,
        action: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        The caller is responsible for committing the session (this method only
        flushes so the ID is available before commit).
        """
        entry = AuditLog(
            user_id=uuid.UUID(str(user_id)) if user_id else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            details=details,
            ip_address=ip_address,
        )
        self.session.add(entry)
        await self.session.flush()
        logger.debug(
            "audit_logged",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return entry

    async def get_logs(
        self,
        user_id: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Query audit logs with optional filters; returns (items, total)."""
        base = select(AuditLog)
        count_base = select(func.count(AuditLog.id))

        if user_id:
            uid = uuid.UUID(user_id)
            base = base.where(AuditLog.user_id == uid)
            count_base = count_base.where(AuditLog.user_id == uid)
        if action:
            base = base.where(AuditLog.action == action)
            count_base = count_base.where(AuditLog.action == action)
        if entity_type:
            base = base.where(AuditLog.entity_type == entity_type)
            count_base = count_base.where(AuditLog.entity_type == entity_type)
        if date_from:
            base = base.where(func.date(AuditLog.created_at) >= date_from)
            count_base = count_base.where(func.date(AuditLog.created_at) >= date_from)
        if date_to:
            base = base.where(func.date(AuditLog.created_at) <= date_to)
            count_base = count_base.where(func.date(AuditLog.created_at) <= date_to)

        total = (await self.session.execute(count_base)).scalar() or 0
        results = (
            await self.session.execute(
                base.order_by(AuditLog.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
        ).scalars().all()

        return list(results), total

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """Delete audit logs older than *days* days. Returns deleted row count."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.session.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)
        )
        await self.session.commit()
        deleted: int = result.rowcount
        logger.info("audit_logs_cleaned_up", deleted=deleted, days=days)
        return deleted
