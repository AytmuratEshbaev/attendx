"""Tests for webhook event manager."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.webhook_events import WebhookEventManager


@pytest.fixture
def mock_engine():
    engine = AsyncMock()
    engine.dispatch_event = AsyncMock(
        return_value={"total": 1, "delivered": 1, "failed": 0, "skipped": 0}
    )
    return engine


@pytest.fixture
def event_mgr(mock_engine):
    return WebhookEventManager(mock_engine)


@pytest.fixture
def mock_student():
    s = MagicMock()
    s.id = uuid.uuid4()
    s.external_id = "EXT001"
    s.employee_no = "STD001"
    s.name = "Test Student"
    s.class_name = "7-A"
    s.parent_phone = "+1234567890"
    return s


@pytest.fixture
def mock_device():
    d = MagicMock()
    d.id = uuid.uuid4()
    d.name = "Terminal 1"
    d.ip_address = "192.168.1.100"
    return d


class TestAttendanceEvents:
    @pytest.mark.asyncio
    async def test_on_attendance_entry(
        self, event_mgr, mock_engine, mock_student, mock_device
    ):
        event_time = datetime.now(timezone.utc)
        await event_mgr.on_attendance_entry(
            mock_student, mock_device, event_time
        )

        mock_engine.dispatch_event.assert_called_once()
        args = mock_engine.dispatch_event.call_args
        assert args[0][0] == "attendance.entry"
        payload = args[0][1]
        assert payload["student_id"] == str(mock_student.id)
        assert payload["student_name"] == "Test Student"
        assert payload["device_name"] == "Terminal 1"
        assert payload["verify_mode"] == "face"

    @pytest.mark.asyncio
    async def test_on_attendance_exit(
        self, event_mgr, mock_engine, mock_student, mock_device
    ):
        event_time = datetime.now(timezone.utc)
        await event_mgr.on_attendance_exit(
            mock_student, mock_device, event_time
        )

        args = mock_engine.dispatch_event.call_args
        assert args[0][0] == "attendance.exit"


class TestStudentEvents:
    @pytest.mark.asyncio
    async def test_on_student_created(
        self, event_mgr, mock_engine, mock_student
    ):
        await event_mgr.on_student_created(mock_student)

        args = mock_engine.dispatch_event.call_args
        assert args[0][0] == "student.created"
        payload = args[0][1]
        assert payload["student_id"] == str(mock_student.id)
        assert payload["name"] == "Test Student"
        assert payload["class_name"] == "7-A"
        assert payload["parent_phone"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_on_student_updated(
        self, event_mgr, mock_engine, mock_student
    ):
        await event_mgr.on_student_updated(
            mock_student, ["name", "class_name"]
        )

        args = mock_engine.dispatch_event.call_args
        assert args[0][0] == "student.updated"
        payload = args[0][1]
        assert payload["changed_fields"] == ["name", "class_name"]

    @pytest.mark.asyncio
    async def test_on_student_deleted(
        self, event_mgr, mock_engine, mock_student
    ):
        await event_mgr.on_student_deleted(mock_student)

        args = mock_engine.dispatch_event.call_args
        assert args[0][0] == "student.deleted"
        payload = args[0][1]
        assert payload["student_id"] == str(mock_student.id)
        assert payload["name"] == "Test Student"


class TestDeviceEvents:
    @pytest.mark.asyncio
    async def test_on_device_online(
        self, event_mgr, mock_engine, mock_device
    ):
        await event_mgr.on_device_online(mock_device)

        args = mock_engine.dispatch_event.call_args
        assert args[0][0] == "device.online"
        payload = args[0][1]
        assert payload["device_name"] == "Terminal 1"
        assert payload["ip_address"] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_on_device_offline(
        self, event_mgr, mock_engine, mock_device
    ):
        await event_mgr.on_device_offline(mock_device)

        args = mock_engine.dispatch_event.call_args
        assert args[0][0] == "device.offline"


class TestFaceEvents:
    @pytest.mark.asyncio
    async def test_on_face_registered(
        self, event_mgr, mock_engine, mock_student
    ):
        await event_mgr.on_face_registered(mock_student, device_count=3)

        args = mock_engine.dispatch_event.call_args
        assert args[0][0] == "face.registered"
        payload = args[0][1]
        assert payload["devices_synced"] == 3
        assert payload["name"] == "Test Student"
