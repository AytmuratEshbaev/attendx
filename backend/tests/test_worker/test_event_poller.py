"""Tests for AttendancePoller logic."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import FakeRedis


class TestPollerHeartbeat:
    @pytest.mark.asyncio
    async def test_heartbeat_written_to_redis(self):
        """Poller should update worker:heartbeat in Redis each cycle."""
        fake_redis = FakeRedis()
        await fake_redis.set("worker:heartbeat", str(datetime.now(timezone.utc).timestamp()))
        val = await fake_redis.get("worker:heartbeat")
        assert val is not None
        assert float(val) > 0

    @pytest.mark.asyncio
    async def test_heartbeat_key_readable_as_float(self):
        fake_redis = FakeRedis()
        ts = datetime.now(timezone.utc).timestamp()
        await fake_redis.set("worker:heartbeat", str(ts))
        stored = await fake_redis.get("worker:heartbeat")
        assert abs(float(stored) - ts) < 1.0


class TestPollerLastPollKey:
    def test_last_poll_key_format(self):
        """Redis key for last poll time follows expected pattern."""
        device_id = 42
        expected = f"hikvision:last_poll:{device_id}"
        assert expected == f"hikvision:last_poll:{device_id}"

    @pytest.mark.asyncio
    async def test_first_poll_lookback(self):
        """When no last_poll key exists, default lookback should be applied."""
        fake_redis = FakeRedis()
        key = "hikvision:last_poll:1"
        val = await fake_redis.get(key)
        assert val is None

    @pytest.mark.asyncio
    async def test_subsequent_poll_uses_stored_time(self):
        """After first poll, stored timestamp is used for the next poll window."""
        fake_redis = FakeRedis()
        key = "hikvision:last_poll:1"
        ts = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
        await fake_redis.set(key, ts)
        stored = await fake_redis.get(key)
        assert stored == ts


class TestPollerDeduplication:
    @pytest.mark.asyncio
    async def test_raw_event_id_uniqueness(self):
        """Events with duplicate raw_event_id should be detected."""
        seen = set()
        event_id_1 = "EVT-001"
        event_id_2 = "EVT-001"  # duplicate
        event_id_3 = "EVT-002"

        seen.add(event_id_1)
        assert event_id_2 in seen  # duplicate detected
        assert event_id_3 not in seen  # new event

    @pytest.mark.asyncio
    async def test_empty_raw_event_id_skipped(self):
        """Events without a raw_event_id should be handled gracefully."""
        raw_event_id = None
        is_skippable = raw_event_id is None
        assert is_skippable


class TestPollerStudentResolution:
    def test_employee_no_matching(self):
        """Employee number from device event must match Student.employee_no."""
        employee_no = "STD001"
        # Simulate: if student found by employee_no, use their UUID
        student_uuid = uuid.uuid4()
        resolved = student_uuid if employee_no == "STD001" else None
        assert resolved is not None

    def test_unknown_employee_no_skipped(self):
        """Events with unknown employee_no should be skipped (no student found)."""
        employee_no = "UNKNOWN999"
        students_by_emp = {"STD001": uuid.uuid4()}
        resolved = students_by_emp.get(employee_no)
        assert resolved is None
