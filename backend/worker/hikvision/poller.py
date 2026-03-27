"""Periodic poller for Hikvision attendance events."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import decrypt_device_password
from app.models.attendance import AttendanceLog
from app.models.device import Device
from app.models.student import Student
from app.repositories.attendance_repo import AttendanceRepository
from app.repositories.device_repo import DeviceRepository
from app.services.webhook_events import get_webhook_event_manager
from worker.hikvision.client import AttendanceEvent, HikvisionClient

logger = structlog.get_logger()

_LAST_POLL_KEY = "hikvision:last_poll:{device_id}"
# On first poll (no Redis key yet), look back this many seconds
_FIRST_POLL_LOOKBACK = 86400  # 24 hours on first poll


class AttendancePoller:
    """Polls all active Hikvision devices and stores new attendance events."""

    def __init__(self, redis: aioredis.Redis) -> None:
        self.redis = redis
        self.interval = settings.HIKVISION_POLL_INTERVAL

    async def run_forever(self) -> None:
        """Run the poll loop indefinitely."""
        import time

        logger.info("poller_started", interval_seconds=self.interval)
        while True:
            try:
                await self._poll_all_devices()
                # Update heartbeat so /health/detailed can report worker status
                await self.redis.set("worker:heartbeat", str(time.time()))
            except Exception:
                logger.exception("poller_cycle_error")
            await asyncio.sleep(self.interval)

    async def _poll_all_devices(self) -> None:
        async with AsyncSessionLocal() as session:
            repo = DeviceRepository(session)
            devices = await repo.get_active_devices()

        for device in devices:
            try:
                await self._poll_device(device)
            except Exception:
                logger.warning(
                    "device_poll_failed",
                    device_id=device.id,
                    name=device.name,
                    exc_info=True,
                )

    async def _poll_device(self, device: Device) -> None:
        redis_key = _LAST_POLL_KEY.format(device_id=device.id)
        last_poll_str: str | None = await self.redis.get(redis_key)
        now = datetime.now(timezone.utc)

        if last_poll_str:
            start_time = datetime.fromisoformat(last_poll_str)
        else:
            start_time = now - timedelta(seconds=_FIRST_POLL_LOOKBACK)

        # Hikvision devices interpret time strings without tz suffix as LOCAL time.
        # Shift our UTC times by the configured offset so the device receives
        # the equivalent local time values.
        offset = timedelta(hours=settings.DEVICE_TZ_OFFSET_HOURS)
        start_for_device = start_time + offset
        # Add 2-hour buffer to account for device clock drift (device may run ahead)
        end_for_device = now + offset + timedelta(hours=2)

        password = decrypt_device_password(device.password_enc)
        client = HikvisionClient(
            host=device.ip_address,
            port=device.port,
            username=device.username,
            password=password,
        )

        # On the very first poll of this device, log device's reported time to diagnose tz issues
        if not last_poll_str:
            device_time_raw = await client.get_device_time()
            logger.info("device_time_check", device_id=device.id, name=device.name, raw=device_time_raw[:300])

        logger.info(
            "device_poll_range",
            device_id=device.id,
            name=device.name,
            start=start_for_device.strftime("%Y-%m-%dT%H:%M:%S"),
            end=end_for_device.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        events = await client.get_attendance_logs(start_for_device, end_for_device)
        new_count = 0
        if events:
            new_count = await self._save_events(device, events)

        # Update last poll time and device online status
        await self.redis.set(redis_key, now.isoformat())
        async with AsyncSessionLocal() as session:
            repo = DeviceRepository(session)
            await repo.update_online_status(device.id, True)
            await session.commit()

        logger.info(
            "device_polled",
            device_id=device.id,
            name=device.name,
            fetched=len(events),
            new=new_count,
        )

    async def _save_events(self, device: Device, events: list[AttendanceEvent]) -> int:
        """Save new attendance events to DB and fire webhooks. Returns count saved."""
        saved = 0
        async with AsyncSessionLocal() as session:
            attendance_repo = AttendanceRepository(session)

            for event in events:
                raw_event_id = f"{device.id}_{event.serial_no}"

                if await attendance_repo.check_duplicate(raw_event_id):
                    continue

                # Resolve student by employee_no
                result = await session.execute(
                    select(Student).where(Student.employee_no == event.employee_no)
                )
                student = result.scalar_one_or_none()
                if student is None:
                    logger.warning(
                        "student_not_found_for_event",
                        employee_no=event.employee_no,
                        name=event.name,
                        device_id=device.id,
                    )
                    continue

                log = AttendanceLog(
                    student_id=student.id,
                    device_id=device.id,
                    event_time=event.event_time,
                    event_type=event.event_type,
                    verify_mode=event.verify_mode,
                    raw_event_id=raw_event_id,
                    picture_url=event.picture_url,
                )
                session.add(log)
                saved += 1

                # Publish to SSE channel for real-time dashboard updates
                import json
                sse_payload = json.dumps({
                    "student_id": str(student.id),
                    "student_name": student.name,
                    "class_name": student.class_name or "",
                    "device_name": device.name,
                    "event_type": event.event_type,
                    "event_time": event.event_time.isoformat(),
                    "verify_mode": event.verify_mode,
                    "picture_url": event.picture_url,
                })
                try:
                    await self.redis.publish("notifications:attendance", sse_payload)
                except Exception:
                    logger.warning(
                        "sse_publish_failed",
                        student_id=str(student.id),
                        event_time=event.event_time.isoformat(),
                    )

                # Fire webhook (fire-and-forget)
                mgr = get_webhook_event_manager()
                if mgr:
                    if event.event_type == "entry":
                        asyncio.create_task(
                            mgr.on_attendance_entry(student, device, event.event_time)
                        )
                    else:
                        asyncio.create_task(
                            mgr.on_attendance_exit(student, device, event.event_time)
                        )

            await session.commit()

        return saved
