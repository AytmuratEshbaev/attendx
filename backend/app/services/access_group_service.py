"""AccessGroup business logic — groups, device/student management, and Hikvision sync."""

from __future__ import annotations

import asyncio
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateException, NotFoundException
from app.models.access_group import AccessGroup, AccessGroupStudent
from app.repositories.access_group_repo import AccessGroupRepository
from app.repositories.device_repo import DeviceRepository
from app.repositories.student_repo import StudentRepository
from app.services import hikvision_sync

logger = structlog.get_logger()


class AccessGroupService:
    def __init__(self, session: AsyncSession):
        self.repo = AccessGroupRepository(session)
        self.device_repo = DeviceRepository(session)
        self.student_repo = StudentRepository(session)
        self.session = session

    async def create(self, data: dict) -> AccessGroup:
        from sqlalchemy.exc import IntegrityError

        try:
            return await self.repo.create(data)
        except IntegrityError:
            raise DuplicateException(
                "An access group with this name already exists."
            )

    async def list_groups(self) -> list[AccessGroup]:
        groups, _ = await self.repo.get_all()
        return groups

    async def get_group(self, group_id: int) -> AccessGroup:
        group = await self.repo.get(group_id)
        if not group:
            raise NotFoundException(f"AccessGroup {group_id} not found.")
        return group

    async def update_group(self, group_id: int, data: dict) -> AccessGroup:
        return await self.repo.update(group_id, data)

    async def delete_group(self, group_id: int) -> None:
        await self.repo.hard_delete(group_id)

    # ------------------------------------------------------------------
    # Devices
    # ------------------------------------------------------------------

    async def add_device(self, group_id: int, device_id: int) -> AccessGroup:
        group = await self.get_group(group_id)
        device = await self.device_repo.get(device_id)
        if not device:
            raise NotFoundException(f"Device {device_id} not found.")
        existing_ids = {d.id for d in group.devices}
        if device_id not in existing_ids:
            group.devices.append(device)
            await self.session.flush()
            await self.session.refresh(group)
        return group

    async def remove_device(self, group_id: int, device_id: int) -> AccessGroup:
        group = await self.get_group(group_id)
        group.devices = [d for d in group.devices if d.id != device_id]
        await self.session.flush()
        await self.session.refresh(group)
        return group

    # ------------------------------------------------------------------
    # Students
    # ------------------------------------------------------------------

    async def add_student(
        self, group_id: int, student_id: uuid.UUID
    ) -> AccessGroupStudent:
        group = await self.get_group(group_id)
        student = await self.student_repo.get(student_id)
        if not student:
            raise NotFoundException(f"Student {student_id} not found.")

        existing = await self.repo.get_membership(group_id, student_id)
        if existing:
            raise DuplicateException("Student already in this access group.")

        membership = AccessGroupStudent(
            access_group_id=group_id,
            student_id=student_id,
            sync_status="pending",
        )
        self.session.add(membership)
        await self.session.flush()
        await self.session.refresh(membership)

        device_ids = [d.id for d in group.devices]
        timetable_id = group.timetable_id
        asyncio.create_task(
            _bg_sync_student(
                membership.id, group_id, student_id, device_ids, timetable_id
            )
        )
        return membership

    async def remove_student(
        self, group_id: int, student_id: uuid.UUID
    ) -> None:
        group = await self.get_group(group_id)
        student = await self.student_repo.get(student_id)
        if not student:
            raise NotFoundException(f"Student {student_id} not found.")

        membership = await self.repo.get_membership(group_id, student_id)
        if not membership:
            raise NotFoundException("Student is not in this access group.")

        await self.session.delete(membership)
        await self.session.flush()

        device_ids = [d.id for d in group.devices]
        asyncio.create_task(_bg_remove_student(student_id, device_ids))

    async def retry_student_sync(
        self, group_id: int, student_id: uuid.UUID
    ) -> AccessGroupStudent:
        """Retry sync for a single student in the group."""
        group = await self.get_group(group_id)
        membership = await self.repo.get_membership(group_id, student_id)
        if not membership:
            raise NotFoundException("Student is not in this access group.")

        # Reset to pending
        await self.repo.update_sync_status(membership.id, "pending")
        await self.session.commit()

        device_ids = [d.id for d in group.devices]
        timetable_id = group.timetable_id
        asyncio.create_task(
            _bg_sync_student(
                membership.id, group_id, student_id, device_ids, timetable_id
            )
        )
        await self.session.refresh(membership)
        return membership

    # ------------------------------------------------------------------
    # Categories (bulk add)
    # ------------------------------------------------------------------

    async def add_category(self, group_id: int, category_id: int) -> dict:
        group = await self.get_group(group_id)
        students, _ = await self.student_repo.get_all_students(
            category_id=category_id, limit=10000, is_active=True
        )

        device_ids = [d.id for d in group.devices]
        timetable_id = group.timetable_id
        skipped = 0
        new_memberships: list[tuple] = []

        for student in students:
            existing = await self.repo.get_membership(group_id, student.id)
            if existing:
                skipped += 1
                continue
            membership = AccessGroupStudent(
                access_group_id=group_id,
                student_id=student.id,
                sync_status="pending",
            )
            self.session.add(membership)
            new_memberships.append((membership, student.id))

        if new_memberships:
            await self.session.flush()
            for membership, student_id in new_memberships:
                await self.session.refresh(membership)
                asyncio.create_task(
                    _bg_sync_student(
                        membership.id, group_id, student_id, device_ids, timetable_id
                    )
                )

        return {"added": len(new_memberships), "skipped": skipped}

    # ------------------------------------------------------------------
    # Full sync
    # ------------------------------------------------------------------

    async def sync_group(self, group_id: int) -> dict:
        """Manually trigger full re-sync of all students in the group."""
        group = await self.get_group(group_id)
        device_ids = [d.id for d in group.devices]
        timetable_id = group.timetable_id

        for membership in group.students:
            asyncio.create_task(
                _bg_sync_student(
                    membership.id,
                    group_id,
                    membership.student_id,
                    device_ids,
                    timetable_id,
                )
            )

        return {
            "synced": len(group.students),
            "failed": 0,
            "devices": len(group.devices),
        }

    async def sync_student_to_all_groups(self, student_id: uuid.UUID) -> None:
        """Called after face upload — re-sync student across all their groups."""
        memberships = await self.repo.get_student_memberships(student_id)
        for membership in memberships:
            group = await self.repo.get(membership.access_group_id)
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


# ---------------------------------------------------------------------------
# Background tasks — use their own DB sessions (safe after request ends)
# ---------------------------------------------------------------------------


async def _bg_sync_student(
    membership_id: int,
    group_id: int,
    student_id: uuid.UUID,
    device_ids: list[int],
    timetable_id: int | None,
) -> None:
    from app.core.database import AsyncSessionLocal
    from app.models.access_group import AccessGroup
    from app.models.device import Device
    from app.models.student import Student
    from app.models.timetable import Timetable

    async with AsyncSessionLocal() as session:
        repo = AccessGroupRepository(session)
        student = await session.get(Student, student_id)
        group = await session.get(AccessGroup, group_id)
        if not student or not group:
            return
        devices = [
            d
            for did in device_ids
            if (d := await session.get(Device, did)) is not None
        ]
        timetable = (
            await session.get(Timetable, timetable_id) if timetable_id else None
        )
        try:
            for device in devices:
                if timetable:
                    try:
                        template_id = await hikvision_sync.ensure_plan_template(
                            timetable, device
                        )
                        await repo.upsert_plan_template(group_id, device.id, template_id)
                    except hikvision_sync.HikvisionSyncError as plan_err:
                        logger.warning(
                            "plan_template_push_failed_using_default",
                            device=device.name,
                            timetable=timetable.name,
                            error=str(plan_err)[:200],
                        )
                        template_id = 1  # fallback to 24/7 default plan
                else:
                    template_id = 1  # default Hikvision plan
                await hikvision_sync.sync_person(student, device, template_id)
                await hikvision_sync.sync_face(student, device)
            await repo.update_sync_status(membership_id, "synced")
            await session.commit()
            logger.info(
                "bg_sync_done",
                student=student.name,
                devices=len(devices),
            )
        except Exception as exc:
            err = (repr(exc) or type(exc).__name__)[:500]
            logger.error("bg_sync_failed", membership_id=membership_id, error=err)
            await repo.update_sync_status(membership_id, "failed", err)
            await session.commit()


async def _bg_remove_student(
    student_id: uuid.UUID,
    device_ids: list[int],
) -> None:
    from app.core.database import AsyncSessionLocal
    from app.models.device import Device
    from app.models.student import Student

    async with AsyncSessionLocal() as session:
        student = await session.get(Student, student_id)
        if not student:
            return
        for did in device_ids:
            device = await session.get(Device, did)
            if device:
                try:
                    await hikvision_sync.remove_person(student, device)
                except Exception as exc:
                    logger.warning(
                        "bg_remove_failed",
                        device=device.name,
                        error=str(exc),
                    )
