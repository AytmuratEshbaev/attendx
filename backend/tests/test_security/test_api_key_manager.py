"""Tests for APIKeyManager."""

import uuid
from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.api_key_manager import APIKeyManager
from app.models import Base

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


class TestCreateKey:
    @pytest.mark.asyncio
    async def test_returns_raw_key_once(self, db_session: AsyncSession):
        manager = APIKeyManager(db_session)
        result = await manager.create_key("Test Key")
        await db_session.commit()

        assert "key" in result
        assert result["key"].startswith("atx_")
        assert "key_id" in result
        assert result["name"] == "Test Key"

    @pytest.mark.asyncio
    async def test_raw_key_not_stored_in_db(self, db_session: AsyncSession):
        manager = APIKeyManager(db_session)
        result = await manager.create_key("Test Key")
        await db_session.commit()

        # Verify the raw key is NOT stored — only the hash
        from app.models.api_key import APIKey
        from sqlalchemy import select

        api_key = (
            await db_session.execute(
                select(APIKey).where(APIKey.id == uuid.UUID(result["key_id"]))
            )
        ).scalar_one()
        assert api_key.key_hash != result["key"]

    @pytest.mark.asyncio
    async def test_verify_key_works(self, db_session: AsyncSession):
        manager = APIKeyManager(db_session)
        result = await manager.create_key("Test Key")
        await db_session.commit()

        from app.models.api_key import APIKey
        from sqlalchemy import select

        api_key = (
            await db_session.execute(
                select(APIKey).where(APIKey.id == uuid.UUID(result["key_id"]))
            )
        ).scalar_one()
        assert APIKeyManager.verify_key(result["key"], api_key.key_hash) is True
        assert APIKeyManager.verify_key("wrong_key", api_key.key_hash) is False


class TestRotateKey:
    @pytest.mark.asyncio
    async def test_old_key_deactivated(self, db_session: AsyncSession):
        manager = APIKeyManager(db_session)
        created = await manager.create_key("Original")
        await db_session.commit()

        await manager.rotate_key(created["key_id"])
        await db_session.commit()

        from app.models.api_key import APIKey

        old = await db_session.get(APIKey, uuid.UUID(created["key_id"]))
        assert old is not None
        assert old.is_active is False

    @pytest.mark.asyncio
    async def test_new_key_returned(self, db_session: AsyncSession):
        manager = APIKeyManager(db_session)
        created = await manager.create_key("Original")
        await db_session.commit()

        new = await manager.rotate_key(created["key_id"])
        assert new["key"].startswith("atx_")
        assert new["key_id"] != created["key_id"]


class TestRevokeKey:
    @pytest.mark.asyncio
    async def test_key_deactivated(self, db_session: AsyncSession):
        manager = APIKeyManager(db_session)
        created = await manager.create_key("To Revoke")
        await db_session.commit()

        await manager.revoke_key(created["key_id"])
        await db_session.commit()

        from app.models.api_key import APIKey

        key = await db_session.get(APIKey, uuid.UUID(created["key_id"]))
        assert key is not None
        assert key.is_active is False
