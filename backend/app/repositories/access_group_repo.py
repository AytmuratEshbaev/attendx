"""AccessGroup repository — CRUD + membership + plan template operations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access_group import (
    AccessGroup,
    AccessGroupDevicePlanTemplate,
    AccessGroupStudent,
)
from app.repositories.base import BaseRepository


class AccessGroupRepository(BaseRepository[AccessGroup]):
    def __init__(self, session: AsyncSession):
        super().__init__(AccessGroup, session)

    async def get_membership(
        self, access_group_id: int, student_id: uuid.UUID
    ) -> AccessGroupStudent | None:
        result = await self.session.execute(
            select(AccessGroupStudent).where(
                AccessGroupStudent.access_group_id == access_group_id,
                AccessGroupStudent.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_student_memberships(
        self, student_id: uuid.UUID
    ) -> list[AccessGroupStudent]:
        result = await self.session.execute(
            select(AccessGroupStudent).where(
                AccessGroupStudent.student_id == student_id
            )
        )
        return list(result.scalars().all())

    async def update_sync_status(
        self,
        membership_id: int,
        status: str,
        error: str | None = None,
    ) -> None:
        m = await self.session.get(AccessGroupStudent, membership_id)
        if m:
            m.sync_status = status
            m.sync_error = error
            if status == "synced":
                m.synced_at = datetime.now(timezone.utc)
            await self.session.flush()

    async def upsert_plan_template(
        self, access_group_id: int, device_id: int, plan_template_id: int
    ) -> AccessGroupDevicePlanTemplate:
        """Insert or update the plan template record for (access_group, device)."""
        result = await self.session.execute(
            select(AccessGroupDevicePlanTemplate).where(
                AccessGroupDevicePlanTemplate.access_group_id == access_group_id,
                AccessGroupDevicePlanTemplate.device_id == device_id,
            )
        )
        record = result.scalar_one_or_none()
        if record:
            record.plan_template_id = plan_template_id
            await self.session.flush()
        else:
            record = AccessGroupDevicePlanTemplate(
                access_group_id=access_group_id,
                device_id=device_id,
                plan_template_id=plan_template_id,
            )
            self.session.add(record)
            await self.session.flush()
            await self.session.refresh(record)
        return record
