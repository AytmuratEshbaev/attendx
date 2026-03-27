"""Tests for webhook admin API endpoints (new Phase 5 endpoints)."""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_redis
from app.core.security import hash_password
from app.models.user import User
from app.models.webhook import Webhook
from app.models.webhook_log import WebhookLog
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models import Base

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
async def setup_db():
    """Fresh in-memory SQLite database per test."""
    pass  # db_session fixture handles table creation per-test


@pytest.fixture
async def db_session():
    engine = create_async_engine(
        _TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def sample_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        username="testadmin",
        email="test@attendx.local",
        password_hash=hash_password("testpass123"),
        role="super_admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def mock_redis():
    """Mock Redis for webhook API tests."""
    store = {}
    lists = {}

    async def mock_get(key):
        return store.get(key)

    async def mock_set(key, value):
        store[key] = value

    async def mock_delete(key):
        store.pop(key, None)

    async def mock_incr(key):
        store[key] = int(store.get(key, 0)) + 1
        return store[key]

    async def mock_zcard(key):
        return 0

    async def mock_llen(key):
        return len(lists.get(key, []))

    async def mock_lrange(key, start, end):
        return lists.get(key, [])[start : end + 1]

    async def mock_lindex(key, index):
        lst = lists.get(key, [])
        return lst[index] if 0 <= index < len(lst) else None

    r = AsyncMock()
    r.get = AsyncMock(side_effect=mock_get)
    r.set = AsyncMock(side_effect=mock_set)
    r.delete = AsyncMock(side_effect=mock_delete)
    r.incr = AsyncMock(side_effect=mock_incr)
    r.zcard = AsyncMock(side_effect=mock_zcard)
    r.llen = AsyncMock(side_effect=mock_llen)
    r.lrange = AsyncMock(side_effect=mock_lrange)
    r.lindex = AsyncMock(side_effect=mock_lindex)
    r.zadd = AsyncMock()
    r.lrem = AsyncMock()
    r.lpush = AsyncMock()
    r.ltrim = AsyncMock()
    return r


@pytest.fixture
async def client(
    db_session: AsyncSession, sample_user: User, mock_redis
):
    from app.main import app

    async def _override_get_db():
        yield db_session

    async def _override_get_user():
        return sample_user

    async def _override_get_redis():
        return mock_redis

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_active_user] = _override_get_user
    app.dependency_overrides[get_redis] = _override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_webhook(db_session: AsyncSession, sample_user: User):
    webhook = Webhook(
        url="https://example.com/webhook",
        secret="test-secret-key",
        events=["student.created", "attendance.entry"],
        is_active=True,
        description="Test webhook",
        created_by=sample_user.id,
    )
    db_session.add(webhook)
    await db_session.commit()
    await db_session.refresh(webhook)
    return webhook


class TestWebhookStats:
    @pytest.mark.asyncio
    async def test_get_stats(self, client, sample_webhook):
        resp = await client.get("/api/v1/webhooks/stats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_webhooks" in data
        assert "active_webhooks" in data
        assert "total_deliveries_today" in data
        assert "success_rate_today" in data
        assert "retry_queue_size" in data
        assert "dead_letter_count" in data
        assert "circuit_breakers" in data
        assert data["total_webhooks"] >= 1
        assert data["active_webhooks"] >= 1


class TestCircuitBreakerAPI:
    @pytest.mark.asyncio
    async def test_get_circuit_breaker_status(
        self, client, sample_webhook
    ):
        resp = await client.get(
            f"/api/v1/webhooks/{sample_webhook.id}/circuit-breaker"
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["state"] == "closed"
        assert data["consecutive_failures"] == 0

    @pytest.mark.asyncio
    async def test_reset_circuit_breaker(self, client, sample_webhook):
        resp = await client.post(
            f"/api/v1/webhooks/{sample_webhook.id}/circuit-breaker/reset"
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["state"] == "closed"
        assert "Circuit breaker reset" in data["message"]


class TestDeadLetterAPI:
    @pytest.mark.asyncio
    async def test_get_empty_dead_letter_queue(self, client):
        resp = await client.get("/api/v1/webhooks/dead-letter")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    @pytest.mark.asyncio
    async def test_retry_nonexistent_dead_letter(self, client):
        resp = await client.post(
            "/api/v1/webhooks/dead-letter/0/retry"
        )
        assert resp.status_code == 404


class TestManualRetry:
    @pytest.mark.asyncio
    async def test_retry_nonexistent_webhook(self, client):
        fake_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/webhooks/{fake_id}/retry?log_id={uuid.uuid4()}"
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_retry_nonexistent_log(
        self, client, sample_webhook
    ):
        fake_log_id = uuid.uuid4()
        resp = await client.post(
            f"/api/v1/webhooks/{sample_webhook.id}/retry?log_id={fake_log_id}"
        )
        assert resp.status_code == 404
