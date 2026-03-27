"""Timetable business logic — recurring and one-time access schedules."""

from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateException, NotFoundException
from app.models.timetable import Timetable
from app.repositories.timetable_repo import TimetableRepository


class TimetableService:
    def __init__(self, session: AsyncSession):
        self.repo = TimetableRepository(session)

    async def create(self, data: dict) -> Timetable:
        from sqlalchemy.exc import IntegrityError

        if "weekdays" in data and isinstance(data["weekdays"], list):
            data["weekdays"] = json.dumps(data["weekdays"])
        try:
            return await self.repo.create(data)
        except IntegrityError:
            raise DuplicateException("A timetable with this name already exists.")

    async def list_timetables(
        self, timetable_type: str | None = None
    ) -> list[Timetable]:
        filters = {}
        if timetable_type:
            filters["timetable_type"] = timetable_type
        timetables, _ = await self.repo.get_all(filters=filters)
        return timetables

    async def get_timetable(self, timetable_id: int) -> Timetable:
        timetable = await self.repo.get(timetable_id)
        if not timetable:
            raise NotFoundException(f"Timetable {timetable_id} not found.")
        return timetable

    async def update_timetable(self, timetable_id: int, data: dict) -> Timetable:
        if "weekdays" in data and isinstance(data["weekdays"], list):
            data["weekdays"] = json.dumps(data["weekdays"])
        return await self.repo.update(timetable_id, data)

    async def delete_timetable(self, timetable_id: int) -> None:
        await self.repo.hard_delete(timetable_id)
