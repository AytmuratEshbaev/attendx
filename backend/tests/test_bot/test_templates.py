"""Tests for bot.templates Telegram message formatters."""

from datetime import datetime, timezone

import pytest

from bot.templates import (
    format_absent_notification,
    format_attendance_message,
    format_late_notification,
    format_weekly_summary,
)


class TestFormatAttendanceMessage:
    def test_entry_message_contains_student_name(self):
        data = {
            "student_name": "Ali Valiyev",
            "class_name": "7-A",
            "event_time": "2025-09-01T08:00:00+05:00",
            "event_type": "entry",
            "device_name": "Main Entrance",
        }
        msg = format_attendance_message(data)
        assert "Ali Valiyev" in msg
        assert "7-A" in msg

    def test_entry_message_has_check_icon(self):
        data = {
            "student_name": "Test",
            "class_name": "7-A",
            "event_time": "2025-09-01T08:00:00+05:00",
            "event_type": "entry",
            "device_name": "Gate",
        }
        msg = format_attendance_message(data)
        assert "✅" in msg

    def test_exit_message_has_house_icon(self):
        data = {
            "student_name": "Barno Karimova",
            "class_name": "8-B",
            "event_time": "2025-09-01T16:00:00+05:00",
            "event_type": "exit",
            "device_name": "Exit Gate",
        }
        msg = format_attendance_message(data)
        assert "🏠" in msg
        assert "Barno Karimova" in msg

    def test_returns_string(self):
        data = {
            "student_name": "Test",
            "class_name": "1-A",
            "event_time": "2025-09-01T08:00:00",
            "event_type": "entry",
            "device_name": "Device",
        }
        assert isinstance(format_attendance_message(data), str)

    def test_message_not_empty(self):
        data = {
            "student_name": "Test",
            "class_name": "1-A",
            "event_time": "2025-09-01T08:00:00",
            "event_type": "entry",
            "device_name": "Device",
        }
        assert len(format_attendance_message(data)) > 10

    def test_includes_device_name(self):
        data = {
            "student_name": "Test",
            "class_name": "1-A",
            "event_time": "2025-09-01T08:00:00",
            "event_type": "entry",
            "device_name": "Main Gate Sensor",
        }
        msg = format_attendance_message(data)
        assert "Main Gate Sensor" in msg


class TestFormatLateNotification:
    def test_contains_student_name(self):
        data = {
            "student_name": "Otabek",
            "class_name": "9-C",
            "arrival_time": "09:15",
            "device_name": "Front Door",
        }
        msg = format_late_notification(data)
        assert "Otabek" in msg

    def test_contains_late_indicator(self):
        data = {
            "student_name": "Late",
            "class_name": "5-A",
            "arrival_time": "09:20",
            "device_name": "Device",
        }
        msg = format_late_notification(data)
        assert "kechik" in msg.lower() or "⚠️" in msg

    def test_returns_string(self):
        data = {
            "student_name": "Late",
            "class_name": "5-A",
            "arrival_time": "09:20",
            "device_name": "Device",
        }
        assert isinstance(format_late_notification(data), str)


class TestFormatAbsentNotification:
    """format_absent_notification(student_name, class_name, date_str) → str"""

    def test_returns_string(self):
        msg = format_absent_notification("Zulfiya", "7-A", "2025-09-01")
        assert isinstance(msg, str)
        assert len(msg) > 5

    def test_contains_student_name(self):
        msg = format_absent_notification("Sardor", "8-B", "2025-09-01")
        assert "Sardor" in msg

    def test_contains_class_name(self):
        msg = format_absent_notification("Ali", "9-C", "2025-09-01")
        assert "9-C" in msg

    def test_contains_absent_indicator(self):
        msg = format_absent_notification("Test", "1-A", "2025-09-01")
        assert "❌" in msg or "kelm" in msg.lower()


class TestFormatWeeklySummary:
    """format_weekly_summary(student_name, class_name, present, total) → str"""

    def test_returns_string(self):
        msg = format_weekly_summary("Ali", "8-A", 4, 5)
        assert isinstance(msg, str)
        assert len(msg) > 10

    def test_contains_student_name(self):
        msg = format_weekly_summary("Sardor", "9-B", 3, 5)
        assert "Sardor" in msg

    def test_contains_percentage(self):
        msg = format_weekly_summary("Test", "1-A", 5, 5)
        assert "100%" in msg

    def test_zero_out_of_zero(self):
        """Division by zero should be handled gracefully."""
        msg = format_weekly_summary("Test", "1-A", 0, 0)
        assert isinstance(msg, str)

    def test_partial_attendance(self):
        msg = format_weekly_summary("Ali", "7-B", 3, 5)
        assert "3" in msg
        assert "5" in msg
