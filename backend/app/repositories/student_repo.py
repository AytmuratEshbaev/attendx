"""Student repository."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    def __init__(self, session: AsyncSession):
        super().__init__(Student, session)

    async def get_by_external_id(self, external_id: str) -> Student | None:
        result = await self.session.execute(
            select(Student).where(Student.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def get_by_employee_no(self, employee_no: str) -> Student | None:
        result = await self.session.execute(
            select(Student).where(Student.employee_no == employee_no)
        )
        return result.scalar_one_or_none()

    async def get_by_class(
        self, class_name: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[Student], int]:
        return await self.get_all(
            skip=skip, limit=limit, filters={"class_name": class_name}
        )

    async def search(
        self, query: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[Student], int]:
        pattern = f"%{query}%"
        stmt = (
            select(Student)
            .where(
                or_(
                    Student.name.ilike(pattern),
                    Student.class_name.ilike(pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        count_stmt = (
            select(func.count())
            .select_from(Student)
            .where(
                or_(
                    Student.name.ilike(pattern),
                    Student.class_name.ilike(pattern),
                )
            )
        )
        total = (await self.session.execute(count_stmt)).scalar() or 0
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_active_students(self) -> list[Student]:
        result = await self.session.execute(
            select(Student).where(Student.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def bulk_create(self, students: list[dict]) -> list[Student]:
        instances = [Student(**data) for data in students]
        self.session.add_all(instances)
        await self.session.flush()
        for inst in instances:
            await self.session.refresh(inst)
        return instances

    async def get_all_students(
        self,
        skip: int = 0,
        limit: int = 100,
        class_name: str | None = None,
        search: str | None = None,
        is_active: bool = True,
        sort: str = "-created_at",
        category_id: int | None = None,
        no_category: bool = False,
    ) -> tuple[list[Student], int]:
        """Get students with optional class, search, active filters, and sorting."""
        stmt = select(Student).where(Student.is_active.is_(is_active))
        count_stmt = (
            select(func.count())
            .select_from(Student)
            .where(Student.is_active.is_(is_active))
        )

        if no_category:
            stmt = stmt.where(Student.category_id.is_(None))
            count_stmt = count_stmt.where(Student.category_id.is_(None))
        elif category_id is not None:
            stmt = stmt.where(Student.category_id == category_id)
            count_stmt = count_stmt.where(Student.category_id == category_id)
        elif class_name:
            stmt = stmt.where(Student.class_name == class_name)
            count_stmt = count_stmt.where(Student.class_name == class_name)

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Student.name.ilike(pattern),
                    Student.class_name.ilike(pattern),
                )
            )
            count_stmt = count_stmt.where(
                or_(
                    Student.name.ilike(pattern),
                    Student.class_name.ilike(pattern),
                )
            )

        # Sorting
        desc = sort.startswith("-")
        sort_field = sort.lstrip("-")
        sort_col = getattr(Student, sort_field, Student.created_at)
        stmt = stmt.order_by(sort_col.desc() if desc else sort_col.asc())

        total = (await self.session.execute(count_stmt)).scalar() or 0
        result = await self.session.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    async def get_class_names(self) -> list[str]:
        """Get distinct class names."""
        result = await self.session.execute(
            select(Student.class_name)
            .where(Student.class_name.isnot(None))
            .distinct()
        )
        return [r for r in result.scalars().all() if r]

    async def count_by_class(self, class_name: str) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Student)
            .where(Student.class_name == class_name, Student.is_active.is_(True))
        )
        return result.scalar() or 0

    async def count_active(self) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Student)
            .where(Student.is_active.is_(True))
        )
        return result.scalar() or 0

    async def find_by_id(self, student_id: uuid.UUID) -> Student | None:
        return await self.get(student_id)
