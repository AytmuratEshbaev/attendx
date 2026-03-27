"""Base repository with generic async CRUD operations."""

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic CRUD repository for SQLAlchemy models."""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, data: dict) -> ModelType:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get(self, id: Any) -> ModelType | None:
        return await self.session.get(self.model, id)

    async def get_or_404(self, id: Any) -> ModelType:
        instance = await self.get(id)
        if instance is None:
            raise NotFoundException(
                f"{self.model.__name__} with id '{id}' not found."
            )
        return instance

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict | None = None,
    ) -> tuple[list[ModelType], int]:
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    col = getattr(self.model, key)
                    query = query.where(col == value)
                    count_query = count_query.where(col == value)

        total = (await self.session.execute(count_query)).scalar() or 0
        result = await self.session.execute(
            query.offset(skip).limit(limit).order_by(self.model.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def update(self, id: Any, data: dict) -> ModelType:
        instance = await self.get_or_404(id)
        for key, value in data.items():
            if value is not None:
                setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def soft_delete(self, id: Any) -> ModelType:
        instance = await self.get_or_404(id)
        instance.is_active = False  # type: ignore[attr-defined]
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def hard_delete(self, id: Any) -> None:
        instance = await self.get_or_404(id)
        await self.session.delete(instance)
        await self.session.flush()

    async def count(self, filters: dict | None = None) -> int:
        query = select(func.count()).select_from(self.model)
        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def exists(self, **kwargs: Any) -> bool:
        query = select(func.count()).select_from(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0
