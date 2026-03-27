"""Attendance repository."""

import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceLog
from app.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[AttendanceLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AttendanceLog, session)

    async def get_today(
        self, class_name: str | None = None
    ) -> list[AttendanceLog]:
        today_start = datetime.combine(
            date.today(), time.min, tzinfo=timezone.utc
        )
        today_end = datetime.combine(
            date.today(), time.max, tzinfo=timezone.utc
        )
        stmt = select(AttendanceLog).where(
            AttendanceLog.event_time.between(today_start, today_end)
        )
        if class_name:
            from app.models.student import Student

            stmt = stmt.join(Student).where(Student.class_name == class_name)
        stmt = stmt.order_by(AttendanceLog.event_time.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 100) -> list[AttendanceLog]:
        stmt = (
            select(AttendanceLog)
            .order_by(AttendanceLog.event_time.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start: date,
        end: date,
        filters: dict | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[AttendanceLog], int]:
        start_dt = datetime.combine(start, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(end, time.max, tzinfo=timezone.utc)

        stmt = select(AttendanceLog).where(
            AttendanceLog.event_time.between(start_dt, end_dt)
        )
        count_stmt = (
            select(func.count())
            .select_from(AttendanceLog)
            .where(AttendanceLog.event_time.between(start_dt, end_dt))
        )

        if filters:
            if filters.get("student_id"):
                stmt = stmt.where(
                    AttendanceLog.student_id == filters["student_id"]
                )
                count_stmt = count_stmt.where(
                    AttendanceLog.student_id == filters["student_id"]
                )
            if filters.get("event_type"):
                stmt = stmt.where(
                    AttendanceLog.event_type == filters["event_type"]
                )
                count_stmt = count_stmt.where(
                    AttendanceLog.event_type == filters["event_type"]
                )

        total = (await self.session.execute(count_stmt)).scalar() or 0
        result = await self.session.execute(
            stmt.offset(skip)
            .limit(limit)
            .order_by(AttendanceLog.event_time.desc())
        )
        return list(result.scalars().all()), total

    async def get_daily_stats(self, target_date: date) -> dict:
        start_dt = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

        result = await self.session.execute(
            select(func.count(func.distinct(AttendanceLog.student_id))).where(
                AttendanceLog.event_time.between(start_dt, end_dt)
            )
        )
        return {"date": target_date.isoformat(), "present": result.scalar() or 0}

    async def get_weekly_stats(
        self, start_date: date
    ) -> list[dict]:
        from datetime import timedelta

        stats = []
        for i in range(7):
            d = start_date + timedelta(days=i)
            day_stats = await self.get_daily_stats(d)
            stats.append(day_stats)
        return stats

    async def check_duplicate(self, raw_event_id: str) -> bool:
        result = await self.session.execute(
            select(func.count())
            .select_from(AttendanceLog)
            .where(AttendanceLog.raw_event_id == raw_event_id)
        )
        return (result.scalar() or 0) > 0

    async def get_student_attendance(
        self,
        student_id: uuid.UUID,
        date_from: date,
        date_to: date,
    ) -> list[AttendanceLog]:
        start_dt = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        result = await self.session.execute(
            select(AttendanceLog)
            .where(
                AttendanceLog.student_id == student_id,
                AttendanceLog.event_time.between(start_dt, end_dt),
            )
            .order_by(AttendanceLog.event_time.desc())
        )
        return list(result.scalars().all())

    async def count_present_today(self) -> int:
        today_start = datetime.combine(
            date.today(), time.min, tzinfo=timezone.utc
        )
        today_end = datetime.combine(
            date.today(), time.max, tzinfo=timezone.utc
        )
        result = await self.session.execute(
            select(func.count(func.distinct(AttendanceLog.student_id))).where(
                AttendanceLog.event_time.between(today_start, today_end)
            )
        )
        return result.scalar() or 0
