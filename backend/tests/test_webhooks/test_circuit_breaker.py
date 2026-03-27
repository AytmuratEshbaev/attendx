"""Tests for webhook circuit breaker."""

import pytest
from unittest.mock import AsyncMock

from app.services.webhook_circuit_breaker import CircuitBreaker


@pytest.fixture
def redis():
    """Mock Redis with in-memory state."""
    store = {}

    async def mock_get(key):
        return store.get(key)

    async def mock_set(key, value):
        store[key] = value

    async def mock_delete(key):
        store.pop(key, None)

    async def mock_incr(key):
        store[key] = int(store.get(key, 0)) + 1
        return store[key]

    r = AsyncMock()
    r.get = AsyncMock(side_effect=mock_get)
    r.set = AsyncMock(side_effect=mock_set)
    r.delete = AsyncMock(side_effect=mock_delete)
    r.incr = AsyncMock(side_effect=mock_incr)
    r._store = store  # For test inspection
    return r


@pytest.fixture
def cb(redis):
    return CircuitBreaker(redis)


class TestCircuitBreakerStates:
    @pytest.mark.asyncio
    async def test_starts_closed(self, cb):
        assert await cb.can_deliver("wh1") is True

    @pytest.mark.asyncio
    async def test_stays_closed_under_threshold(self, cb):
        for _ in range(4):  # Under FAILURE_THRESHOLD of 5
            await cb.record_failure("wh1")
        assert await cb.can_deliver("wh1") is True

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self, cb):
        for _ in range(5):
            await cb.record_failure("wh1")
        assert await cb.can_deliver("wh1") is False

    @pytest.mark.asyncio
    async def test_open_state_blocks_delivery(self, cb, redis):
        # Force open state
        redis._store["webhook:circuit:wh1:state"] = "open"
        redis._store["webhook:circuit:wh1:opened_at"] = "9999999999"
        assert await cb.can_deliver("wh1") is False

    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_timeout(self, cb, redis):
        redis._store["webhook:circuit:wh1:state"] = "open"
        redis._store["webhook:circuit:wh1:opened_at"] = "0"  # Long ago
        assert await cb.can_deliver("wh1") is True
        # State should now be half_open
        assert redis._store["webhook:circuit:wh1:state"] == "half_open"

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self, cb, redis):
        redis._store["webhook:circuit:wh1:state"] = "half_open"
        await cb.record_success("wh1")
        assert redis._store["webhook:circuit:wh1:state"] == "closed"

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self, cb, redis):
        redis._store["webhook:circuit:wh1:state"] = "half_open"
        await cb.record_failure("wh1")
        assert redis._store["webhook:circuit:wh1:state"] == "open"

    @pytest.mark.asyncio
    async def test_success_resets_failure_counter(self, cb, redis):
        for _ in range(3):
            await cb.record_failure("wh1")
        await cb.record_success("wh1")
        # Failure counter should be deleted
        assert "webhook:circuit:wh1:failures" not in redis._store

    @pytest.mark.asyncio
    async def test_reset_returns_to_closed(self, cb, redis):
        for _ in range(5):
            await cb.record_failure("wh1")
        assert await cb.can_deliver("wh1") is False

        await cb.reset("wh1")
        assert await cb.can_deliver("wh1") is True

    @pytest.mark.asyncio
    async def test_get_status(self, cb):
        status = await cb.get_status("wh1")
        assert status["webhook_id"] == "wh1"
        assert status["state"] == "closed"
        assert status["consecutive_failures"] == 0
        assert status["recovery_timeout_seconds"] == 60
