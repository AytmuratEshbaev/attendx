"""Tests for AuditService."""

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.services.audit_service import AuditService

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(TEST_DB_URL, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class TestAuditLog:
    @pytest.mark.asyncio
    async def test_creates_log_entry(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        entry = await svc.log(
            user_id=None,
            action="login",
            entity_type="user",
            entity_id="test_user",
            ip_address="127.0.0.1",
        )
        await db_session.commit()
        assert entry.id is not None
        assert entry.action == "login"
        assert entry.ip_address == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_log_with_details(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        details = {"old_value": "foo", "new_value": "bar"}
        entry = await svc.log(
            user_id=None,
            action="update",
            entity_type="student",
            details=details,
        )
        await db_session.commit()
        assert entry.details == details

    @pytest.mark.asyncio
    async def test_get_logs_returns_items(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        for action in ("login", "logout", "login"):
            await svc.log(user_id=None, action=action)
        await db_session.commit()

        items, total = await svc.get_logs()
        assert total == 3
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_filter_by_action(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        await svc.log(user_id=None, action="login")
        await svc.log(user_id=None, action="logout")
        await db_session.commit()

        items, total = await svc.get_logs(action="login")
        assert total == 1
        assert items[0].action == "login"

    @pytest.mark.asyncio
    async def test_filter_by_entity_type(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        await svc.log(user_id=None, action="create", entity_type="student")
        await svc.log(user_id=None, action="create", entity_type="device")
        await db_session.commit()

        items, total = await svc.get_logs(entity_type="student")
        assert total == 1
        assert items[0].entity_type == "student"

    @pytest.mark.asyncio
    async def test_pagination(self, db_session: AsyncSession):
        svc = AuditService(db_session)
        for i in range(10):
            await svc.log(user_id=None, action=f"action_{i}")
        await db_session.commit()

        items, total = await svc.get_logs(skip=0, limit=3)
        assert total == 10
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_cleanup_old_logs(self, db_session: AsyncSession):
        from datetime import datetime, timedelta

        from sqlalchemy import text

        svc = AuditService(db_session)

        # Create old and new logs
        await svc.log(user_id=None, action="old_action")
        await db_session.commit()

        # Manually age the log
        await db_session.execute(
            text(
                "UPDATE audit_logs SET created_at = :old_date"
            ),
            {"old_date": (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()},
        )
        await db_session.commit()

        await svc.log(user_id=None, action="new_action")
        await db_session.commit()

        deleted = await svc.cleanup_old_logs(days=90)
        assert deleted == 1
