"""Device business logic service."""

import time

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

from app.core.security import decrypt_device_password, encrypt_device_password
from app.models.device import Device
from app.repositories.device_repo import DeviceRepository
from app.schemas.device import DeviceCreate, DeviceHealth, DeviceUpdate


class DeviceService:
    def __init__(self, session: AsyncSession):
        self.repo = DeviceRepository(session)
        self.session = session

    async def create_device(self, data: DeviceCreate) -> Device:
        device_data = data.model_dump(exclude={"password"})
        device_data["password_enc"] = encrypt_device_password(data.password)
        return await self.repo.create(device_data)

    async def get_device(self, device_id: int) -> Device:
        return await self.repo.get_or_404(device_id)

    async def list_devices(self) -> list[Device]:
        return await self.repo.get_active_devices()

    async def update_device(
        self, device_id: int, data: DeviceUpdate
    ) -> Device:
        update_data = data.model_dump(exclude_unset=True)
        # Re-encrypt password if changed
        if "password" in update_data:
            password = update_data.pop("password")
            if password:
                update_data["password_enc"] = encrypt_device_password(password)
        if not update_data:
            return await self.repo.get_or_404(device_id)
        return await self.repo.update(device_id, update_data)

    async def delete_device(self, device_id: int) -> Device:
        """Soft delete a device."""
        return await self.repo.soft_delete(device_id)

    async def check_health(self, device_id: int) -> DeviceHealth:
        """Ping device via ISAPI and return real health status."""
        from worker.hikvision.client import HikvisionClient

        device = await self.repo.get_or_404(device_id)
        password = decrypt_device_password(device.password_enc)
        client = HikvisionClient(
            host=device.ip_address,
            port=device.port,
            username=device.username,
            password=password,
            timeout=5.0,
        )

        is_online = False
        response_time_ms: float | None = None
        try:
            t0 = time.monotonic()
            await client.get_device_info()
            response_time_ms = round((time.monotonic() - t0) * 1000, 1)
            is_online = True
            await self.repo.update_online_status(device_id, True)
            await self.session.commit()
        except Exception:
            logger.debug("device_health_check_error", device_id=device_id, exc_info=True)

        device = await self.repo.get_or_404(device_id)
        return DeviceHealth(
            id=device.id,
            name=device.name,
            is_online=is_online,
            last_online_at=device.last_online_at,
            response_time_ms=response_time_ms,
        )

    async def sync_device(self, device_id: int, redis=None) -> dict:
        """
        Queue a full device sync job.

        Publishes a message to the Redis channel "worker:sync_jobs" which
        the Hikvision worker picks up and performs a full student/face push.
        """
        import json
        from datetime import datetime, timezone

        device = await self.repo.get_or_404(device_id)

        if redis is not None:
            job = {
                "job_type": "full_sync",
                "device_id": device_id,
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }
            await redis.publish("worker:sync_jobs", json.dumps(job))
            # Also set a flag so the worker can pick it up via polling
            await redis.setex(f"sync:device:{device_id}", 300, "1")

        return {
            "status": "queued",
            "device_id": device_id,
            "device_name": device.name,
            "message": "Sync job queued. Worker will process shortly.",
        }
