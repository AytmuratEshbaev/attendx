"""Tests for webhook retry manager."""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.webhook_retry import WebhookRetryManager


@pytest.fixture
def mock_redis():
    """Mock Redis with in-memory sorted set and list."""
    sorted_set = {}  # member -> score
    lists = {}

    async def mock_zadd(key, mapping):
        if key not in sorted_set:
            sorted_set[key] = {}
        sorted_set[key].update(mapping)

    async def mock_zrangebyscore(key, min_score, max_score, start=0, num=50):
        if key not in sorted_set:
            return []
        max_val = float(max_score) if max_score != "-inf" else float("-inf")
        results = [
            member
            for member, score in sorted_set[key].items()
            if score <= max_val
        ]
        return results[start : start + num]

    async def mock_zrem(key, member):
        if key in sorted_set and member in sorted_set[key]:
            del sorted_set[key][member]
            return 1
        return 0

    async def mock_zcard(key):
        return len(sorted_set.get(key, {}))

    async def mock_lpush(key, value):
        if key not in lists:
            lists[key] = []
        lists[key].insert(0, value)

    async def mock_ltrim(key, start, end):
        if key in lists:
            lists[key] = lists[key][start : end + 1]

    async def mock_llen(key):
        return len(lists.get(key, []))

    async def mock_lindex(key, index):
        lst = lists.get(key, [])
        if 0 <= index < len(lst):
            return lst[index]
        return None

    async def mock_lrem(key, count, value):
        if key in lists and value in lists[key]:
            lists[key].remove(value)
            return 1
        return 0

    r = AsyncMock()
    r.zadd = AsyncMock(side_effect=mock_zadd)
    r.zrangebyscore = AsyncMock(side_effect=mock_zrangebyscore)
    r.zrem = AsyncMock(side_effect=mock_zrem)
    r.zcard = AsyncMock(side_effect=mock_zcard)
    r.lpush = AsyncMock(side_effect=mock_lpush)
    r.ltrim = AsyncMock(side_effect=mock_ltrim)
    r.llen = AsyncMock(side_effect=mock_llen)
    r.lindex = AsyncMock(side_effect=mock_lindex)
    r.lrem = AsyncMock(side_effect=mock_lrem)
    r.lrange = AsyncMock(return_value=[])
    r.get = AsyncMock(return_value=None)
    r.set = AsyncMock()
    r.delete = AsyncMock()
    r.incr = AsyncMock(return_value=1)
    r._sorted_set = sorted_set
    r._lists = lists
    return r


@pytest.fixture
def mock_engine():
    engine = AsyncMock()
    engine.circuit_breaker = AsyncMock()
    engine.circuit_breaker.record_success = AsyncMock()
    engine.circuit_breaker.record_failure = AsyncMock()
    return engine


@pytest.fixture
def retry_mgr(mock_engine, mock_redis):
    return WebhookRetryManager(mock_engine, AsyncMock(), mock_redis)


class TestQueueRetry:
    @pytest.mark.asyncio
    async def test_queues_with_correct_delay(self, retry_mgr, mock_redis):
        await retry_mgr.queue_retry(
            "wh-123", "student.created", {"name": "Test"}, 1
        )

        queue = mock_redis._sorted_set.get("webhook:retry:queue", {})
        assert len(queue) == 1
        member = list(queue.keys())[0]
        data = json.loads(member)
        assert data["webhook_id"] == "wh-123"
        assert data["event_type"] == "student.created"
        assert data["attempt"] == 2  # Next attempt

    @pytest.mark.asyncio
    async def test_retry_delays_escalate(self, retry_mgr, mock_redis):
        """Attempt 1 -> 10s, attempt 2 -> 60s, attempt 3 -> 300s."""
        now = datetime.now(timezone.utc).timestamp()

        await retry_mgr.queue_retry(
            "wh-1", "test", {}, 1
        )
        queue = mock_redis._sorted_set.get("webhook:retry:queue", {})
        score = list(queue.values())[0]
        assert abs(score - (now + 10)) < 2  # ~10 seconds delay

    @pytest.mark.asyncio
    async def test_exceeding_max_retries_goes_to_dead_letter(
        self, retry_mgr, mock_redis
    ):
        await retry_mgr.queue_retry(
            "wh-1", "test", {"data": "test"}, 4  # > MAX_RETRIES (3)
        )

        # Should NOT be in retry queue
        queue = mock_redis._sorted_set.get("webhook:retry:queue", {})
        assert len(queue) == 0

        # Should be in dead letter
        dead_letters = mock_redis._lists.get("webhook:dead_letter", [])
        assert len(dead_letters) == 1
        data = json.loads(dead_letters[0])
        assert data["webhook_id"] == "wh-1"
        assert data["max_retries_exceeded"] is True


class TestRetryQueueInfo:
    @pytest.mark.asyncio
    async def test_get_retry_queue_size(self, retry_mgr, mock_redis):
        await retry_mgr.queue_retry("wh-1", "test", {}, 1)
        size = await retry_mgr.get_retry_queue_size()
        assert size == 1

    @pytest.mark.asyncio
    async def test_get_dead_letter_count(self, retry_mgr, mock_redis):
        await retry_mgr.queue_retry("wh-1", "test", {}, 4)  # Goes to DLQ
        count = await retry_mgr.get_dead_letter_count()
        assert count == 1


class TestRetryDeadLetter:
    @pytest.mark.asyncio
    async def test_retry_dead_letter_requeues(
        self, retry_mgr, mock_redis
    ):
        # Put something in dead letter
        await retry_mgr.queue_retry("wh-1", "test", {"d": 1}, 4)
        assert await retry_mgr.get_dead_letter_count() == 1

        # Retry it
        result = await retry_mgr.retry_dead_letter(0)
        assert result is True

        # Should be back in retry queue
        size = await retry_mgr.get_retry_queue_size()
        assert size == 1

    @pytest.mark.asyncio
    async def test_retry_nonexistent_dead_letter(self, retry_mgr):
        result = await retry_mgr.retry_dead_letter(99)
        assert result is False
