"""Central webhook event dispatcher."""

from datetime import datetime, timezone

import structlog

from app.services.webhook_engine import WebhookEngine

logger = structlog.get_logger()

# Global singleton instance
_webhook_event_manager: "WebhookEventManager | None" = None


def get_webhook_event_manager() -> "WebhookEventManager | None":
    """Get the global webhook event manager instance (None if not initialized)."""
    return _webhook_event_manager


def set_webhook_event_manager(manager: "WebhookEventManager | None") -> None:
    """Set the global webhook event manager instance."""
    global _webhook_event_manager  # noqa: PLW0603
    _webhook_event_manager = manager


class WebhookEventManager:
    """
    Central event dispatcher -- called by services when events occur.
    Maps application events to webhook deliveries.
    """

    def __init__(self, webhook_engine: WebhookEngine):
        self.engine = webhook_engine

    async def on_attendance_entry(
        self, student, device, event_time: datetime
    ) -> None:
        """Triggered when a student enters (from Hikvision worker)."""
        await self.engine.dispatch_event(
            "attendance.entry",
            {
                "student_id": str(student.id),
                "external_id": student.external_id,
                "employee_no": student.employee_no,
                "student_name": student.name,
                "class_name": student.class_name,
                "event_time": event_time.isoformat(),
                "device_name": device.name if device else None,
                "device_id": str(device.id) if device else None,
                "verify_mode": "face",
            },
        )

    async def on_attendance_exit(
        self, student, device, event_time: datetime
    ) -> None:
        """Triggered when a student exits."""
        await self.engine.dispatch_event(
            "attendance.exit",
            {
                "student_id": str(student.id),
                "external_id": student.external_id,
                "employee_no": student.employee_no,
                "student_name": student.name,
                "class_name": student.class_name,
                "event_time": event_time.isoformat(),
                "device_name": device.name if device else None,
                "device_id": str(device.id) if device else None,
                "verify_mode": "face",
            },
        )

    async def on_student_created(self, student) -> None:
        """Triggered when a new student is created via API."""
        await self.engine.dispatch_event(
            "student.created",
            {
                "student_id": str(student.id),
                "external_id": student.external_id,
                "employee_no": student.employee_no,
                "name": student.name,
                "class_name": student.class_name,
                "parent_phone": student.parent_phone,
            },
        )

    async def on_student_updated(
        self, student, changed_fields: list[str]
    ) -> None:
        """Triggered when student info is updated."""
        await self.engine.dispatch_event(
            "student.updated",
            {
                "student_id": str(student.id),
                "external_id": student.external_id,
                "employee_no": student.employee_no,
                "name": student.name,
                "class_name": student.class_name,
                "changed_fields": changed_fields,
            },
        )

    async def on_student_deleted(self, student) -> None:
        """Triggered when student is deactivated/deleted."""
        await self.engine.dispatch_event(
            "student.deleted",
            {
                "student_id": str(student.id),
                "external_id": student.external_id,
                "employee_no": student.employee_no,
                "name": student.name,
            },
        )

    async def on_device_online(self, device) -> None:
        """Triggered when terminal comes online."""
        await self.engine.dispatch_event(
            "device.online",
            {
                "device_id": str(device.id),
                "device_name": device.name,
                "ip_address": device.ip_address,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def on_device_offline(self, device) -> None:
        """Triggered when terminal goes offline."""
        await self.engine.dispatch_event(
            "device.offline",
            {
                "device_id": str(device.id),
                "device_name": device.name,
                "ip_address": device.ip_address,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def on_face_registered(
        self, student, device_count: int
    ) -> None:
        """Triggered when face is registered on terminals."""
        await self.engine.dispatch_event(
            "face.registered",
            {
                "student_id": str(student.id),
                "external_id": student.external_id,
                "employee_no": student.employee_no,
                "name": student.name,
                "devices_synced": device_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
