"""Timetable repository."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timetable import Timetable
from app.repositories.base import BaseRepository


class TimetableRepository(BaseRepository[Timetable]):
    def __init__(self, session: AsyncSession):
        super().__init__(Timetable, session)
