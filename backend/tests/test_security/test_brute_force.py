"""Tests for BruteForceProtection using a mock Redis."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.rate_limiter import BruteForceProtection


def _make_redis(stored_value=None):
    """Create a minimal async mock Redis client."""
    r = AsyncMock()
    r.get = AsyncMock(return_value=stored_value)
    r.incr = AsyncMock(return_value=1)
    r.delete = AsyncMock()
    r.expire = AsyncMock()
    r.ttl = AsyncMock(return_value=900)
    r.keys = AsyncMock(return_value=[])
    return r


class TestCheckLoginAttempt:
    @pytest.mark.asyncio
    async def test_allowed_with_no_attempts(self):
        redis = _make_redis(stored_value=None)
        brute = BruteForceProtection(redis)
        result = await brute.check_login_attempt("user1")
        assert result["allowed"] is True
        assert result["remaining_attempts"] == 5

    @pytest.mark.asyncio
    async def test_allowed_with_few_attempts(self):
        redis = _make_redis(stored_value="3")
        brute = BruteForceProtection(redis)
        result = await brute.check_login_attempt("user1")
        assert result["allowed"] is True
        assert result["remaining_attempts"] == 2

    @pytest.mark.asyncio
    async def test_locked_after_5_attempts(self):
        redis = _make_redis(stored_value="5")
        redis.ttl = AsyncMock(return_value=900)
        brute = BruteForceProtection(redis)
        result = await brute.check_login_attempt("user1")
        assert result["allowed"] is False
        assert result["lockout_level"] == "medium"

    @pytest.mark.asyncio
    async def test_locked_after_10_attempts(self):
        redis = _make_redis(stored_value="10")
        redis.ttl = AsyncMock(return_value=3600)
        brute = BruteForceProtection(redis)
        result = await brute.check_login_attempt("user1")
        assert result["allowed"] is False
        assert result["lockout_level"] == "high"

    @pytest.mark.asyncio
    async def test_locked_after_20_attempts(self):
        redis = _make_redis(stored_value="20")
        redis.ttl = AsyncMock(return_value=86400)
        brute = BruteForceProtection(redis)
        result = await brute.check_login_attempt("user1")
        assert result["allowed"] is False
        assert result["lockout_level"] == "critical"


class TestRecordFailedAttempt:
    @pytest.mark.asyncio
    async def test_increments_counter(self):
        redis = _make_redis()
        brute = BruteForceProtection(redis)
        await brute.record_failed_attempt("user1")
        redis.incr.assert_called_once_with("bruteforce:login:user1")

    @pytest.mark.asyncio
    async def test_sets_ttl_for_first_tier(self):
        redis = _make_redis()
        redis.incr = AsyncMock(return_value=5)
        brute = BruteForceProtection(redis)
        await brute.record_failed_attempt("user1")
        # Should set 15-minute TTL for medium tier
        redis.expire.assert_called_once_with("bruteforce:login:user1", 900)


class TestRecordSuccessfulLogin:
    @pytest.mark.asyncio
    async def test_deletes_key(self):
        redis = _make_redis()
        brute = BruteForceProtection(redis)
        await brute.record_successful_login("user1")
        redis.delete.assert_called_once_with("bruteforce:login:user1")


class TestIpRateLimiting:
    @pytest.mark.asyncio
    async def test_ip_based_lockout(self):
        redis = _make_redis(stored_value="5")
        redis.ttl = AsyncMock(return_value=900)
        brute = BruteForceProtection(redis)
        result = await brute.check_login_attempt("ip:192.168.1.1")
        assert result["allowed"] is False
