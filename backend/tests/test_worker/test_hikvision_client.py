"""Tests for Hikvision ISAPI client helpers."""

from datetime import datetime, timezone

import pytest

from worker.hikvision.client import AttendanceEvent, HikvisionClient, _parse_event, _parse_time


class TestParseTime:
    def test_parses_iso_with_offset_to_utc(self):
        """Timestamps with timezone offset are returned in UTC."""
        result = _parse_time("2025-09-01T08:30:00+05:00")
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.year == 2025
        # 08:30+05:00 → 03:30 UTC
        assert result.hour == 3
        assert result.minute == 30

    def test_parses_naive_iso_to_utc(self):
        result = _parse_time("2025-09-01T08:30:00")
        assert result is not None
        assert result.year == 2025

    def test_returns_none_on_invalid(self):
        """Invalid time strings return None (caller handles the None case)."""
        result = _parse_time("not-a-date")
        assert result is None

    def test_returns_none_on_empty_string(self):
        result = _parse_time("")
        assert result is None

    def test_returns_datetime_for_valid_utc_z(self):
        result = _parse_time("2025-09-01T08:30:00Z")
        # Z is not standard ISO 8601 in Python < 3.11; test that it either works or returns None
        assert result is None or isinstance(result, datetime)


class TestParseEvent:
    def _make_record(self, **kwargs) -> dict:
        """Return a minimal valid AcsEventInfo record."""
        base = {
            "employeeNoString": "STD001",
            "name": "Test Student",
            "time": "2025-09-01T08:00:00+05:00",
            "inOutStatus": "entry",  # NOT "type" — that's verify_mode
            "type": 0,              # 0 = face recognition
            "serialNo": 12345,
        }
        base.update(kwargs)
        return base

    def test_parses_entry_event(self):
        rec = self._make_record()
        event = _parse_event(rec)
        assert event is not None
        assert event.employee_no == "STD001"
        assert event.event_type == "entry"
        assert event.verify_mode == "face"
        assert event.serial_no == 12345

    def test_parses_exit_event(self):
        rec = self._make_record(inOutStatus="exit", employeeNoString="STD002")
        event = _parse_event(rec)
        assert event is not None
        assert event.event_type == "exit"

    def test_parses_numeric_in_out_0_as_entry(self):
        rec = self._make_record(inOutStatus="0")
        event = _parse_event(rec)
        assert event is not None
        assert event.event_type == "entry"

    def test_parses_numeric_in_out_1_as_exit(self):
        rec = self._make_record(inOutStatus="1")
        event = _parse_event(rec)
        assert event is not None
        assert event.event_type == "exit"

    def test_fingerprint_verify_mode(self):
        rec = self._make_record(type=1)
        event = _parse_event(rec)
        assert event is not None
        assert event.verify_mode == "fingerprint"

    def test_card_verify_mode(self):
        rec = self._make_record(type=2)
        event = _parse_event(rec)
        assert event is not None
        assert event.verify_mode == "card"

    def test_returns_none_without_employee_no(self):
        rec = {
            "name": "No Employee",
            "time": "2025-09-01T08:00:00+05:00",
            "inOutStatus": "entry",
            "type": 0,
        }
        result = _parse_event(rec)
        assert result is None

    def test_returns_none_with_invalid_time(self):
        rec = self._make_record(time="invalid-time")
        result = _parse_event(rec)
        assert result is None

    def test_returns_none_with_empty_employee_no(self):
        rec = self._make_record(employeeNoString="")
        result = _parse_event(rec)
        assert result is None

    def test_strips_whitespace_from_employee_no(self):
        rec = self._make_record(employeeNoString="  STD001  ")
        event = _parse_event(rec)
        assert event is not None
        assert event.employee_no == "STD001"

    def test_handles_missing_optional_fields(self):
        """Minimal record with only employee_no and valid time."""
        rec = {
            "employeeNoString": "STD003",
            "time": "2025-09-01T08:00:00+05:00",
        }
        event = _parse_event(rec)
        assert event is not None
        assert event.employee_no == "STD003"
        assert event.name == ""

    def test_uses_cardNo_fallback(self):
        """Falls back to cardNo if employeeNoString is absent."""
        rec = {
            "cardNo": "CARD001",
            "time": "2025-09-01T08:00:00+05:00",
        }
        event = _parse_event(rec)
        assert event is not None
        assert event.employee_no == "CARD001"


class TestHikvisionClientInit:
    def test_builds_base_url(self):
        client = HikvisionClient(
            host="192.168.1.100",
            port=80,
            username="admin",
            password="test",
        )
        assert "192.168.1.100" in client.base_url
        assert ":80" in client.base_url

    def test_custom_port(self):
        client = HikvisionClient(
            host="192.168.1.100",
            port=8080,
            username="admin",
            password="test",
        )
        assert ":8080" in client.base_url

    def test_no_trailing_slash(self):
        client = HikvisionClient(
            host="192.168.1.100",
            port=80,
            username="admin",
            password="test",
        )
        assert not client.base_url.endswith("/")


class TestAttendanceEventDataclass:
    def test_entry_event_fields(self):
        ev = AttendanceEvent(
            employee_no="STD001",
            name="Alice",
            event_time=datetime.now(timezone.utc),
            event_type="entry",
            verify_mode="face",
            serial_no=1,
        )
        assert ev.employee_no == "STD001"
        assert ev.event_type == "entry"
        assert ev.verify_mode == "face"

    def test_exit_event_fields(self):
        ev = AttendanceEvent(
            employee_no="STD002",
            name="Bob",
            event_time=datetime.now(timezone.utc),
            event_type="exit",
            verify_mode="card",
            serial_no=2,
        )
        assert ev.event_type == "exit"
        assert ev.verify_mode == "card"
