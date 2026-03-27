"""
Notification processor for attendance events.

Publishes attendance notifications to the Redis pub/sub channel
"notifications:telegram" so the Telegram bot can forward them to parents.
"""

import json
from datetime import datetime

import structlog

logger = structlog.get_logger()


class NotificationProcessor:
    """
    Publishes attendance events to Redis for downstream consumers.

    Usage (from the Hikvision poller):
        processor = NotificationProcessor(redis)
        await processor.publish_attendance(student, device, event_time, event_type)
    """

    CHANNEL = "notifications:telegram"

    def __init__(self, redis) -> None:
        self.redis = redis

    async def publish_attendance(
        self,
        student,
        device,
        event_time: datetime,
        event_type: str,
    ) -> None:
        """
        Publish an attendance event to the Telegram notification channel.

        Args:
            student: Student ORM instance (must have .id, .name, .class_name)
            device:  Device ORM instance or None (used for .name)
            event_time: UTC datetime of the event
            event_type: "entry" or "exit"
        """
        await self._handle_attendance_notification(
            student=student,
            device=device,
            event_time=event_time,
            event_type=event_type,
        )

    async def _handle_attendance_notification(
        self,
        student,
        device,
        event_time: datetime,
        event_type: str,
    ) -> None:
        """Serialize and publish attendance data to Redis pub/sub."""
        payload = {
            "student_id": str(student.id),
            "student_name": student.name,
            "class_name": student.class_name or "",
            "event_type": event_type,
            "event_time": event_time.isoformat(),
            "device_name": device.name if device else "",
        }

        try:
            await self.redis.publish(self.CHANNEL, json.dumps(payload))
            logger.debug(
                "telegram_notification_published",
                student_id=payload["student_id"],
                event_type=event_type,
            )
        except Exception as e:
            logger.error(
                "telegram_notification_publish_failed",
                student_id=payload["student_id"],
                error=str(e),
            )
