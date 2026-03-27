"""Device repository."""

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    def __init__(self, session: AsyncSession):
        super().__init__(Device, session)

    async def get_active_devices(self) -> list[Device]:
        result = await self.session.execute(
            select(Device).where(Device.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_by_ip(self, ip_address: str) -> Device | None:
        result = await self.session.execute(
            select(Device).where(Device.ip_address == ip_address)
        )
        return result.scalar_one_or_none()

    async def update_online_status(
        self, device_id: int, is_online: bool
    ) -> None:
        values: dict = {}
        if is_online:
            values["last_online_at"] = datetime.now(timezone.utc)
        if values:
            await self.session.execute(
                update(Device).where(Device.id == device_id).values(**values)
            )
            await self.session.flush()

    async def update_last_online(self, device_id: int) -> Device:
        """Update last_online_at timestamp and return the device."""
        return await self.update(
            device_id, {"last_online_at": datetime.now(timezone.utc)}
        )
