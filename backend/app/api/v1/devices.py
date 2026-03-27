"""Hikvision device management endpoints."""

from typing import Annotated

import httpx
import structlog
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_redis, require_role
from app.core.exceptions import NotFoundException
from app.models.student import Student
from app.models.user import User
from app.repositories.student_repo import StudentRepository
from app.schemas.common import SuccessResponse
from app.schemas.device import (
    DeviceCreate,
    DeviceHealth,
    DeviceResponse,
    DeviceUpdate,
)
from app.services import hikvision_sync
from app.services.device_service import DeviceService

logger = structlog.get_logger()
router = APIRouter(prefix="/devices", tags=["devices"])


def _svc(db: AsyncSession) -> DeviceService:
    return DeviceService(db)


@router.get("", response_model=SuccessResponse[list[DeviceResponse]])
async def list_devices(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """List all active devices."""
    devices = await _svc(db).list_devices()
    data = [DeviceResponse.model_validate(d) for d in devices]
    return SuccessResponse(data=data)


@router.post("", response_model=SuccessResponse[DeviceResponse], status_code=201)
async def create_device(
    body: DeviceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Register a new Hikvision device."""
    device = await _svc(db).create_device(body)
    return SuccessResponse(data=DeviceResponse.model_validate(device))


@router.put("/{device_id}", response_model=SuccessResponse[DeviceResponse])
async def update_device(
    device_id: int,
    body: DeviceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Update a device."""
    device = await _svc(db).update_device(device_id, body)
    return SuccessResponse(data=DeviceResponse.model_validate(device))


@router.delete("/{device_id}", response_model=SuccessResponse[dict])
async def delete_device(
    device_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Delete a device."""
    await _svc(db).delete_device(device_id)
    return SuccessResponse(data={"message": "Device deleted."})


@router.post("/{device_id}/sync", response_model=SuccessResponse[dict])
async def sync_device(
    device_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
    redis=Depends(get_redis),
):
    """Trigger full sync for a device (publishes job to Redis queue)."""
    result = await _svc(db).sync_device(device_id, redis=redis)
    return SuccessResponse(data=result)


@router.get("/{device_id}/health", response_model=SuccessResponse[DeviceHealth])
async def device_health(
    device_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Check device health status."""
    health = await _svc(db).check_health(device_id)
    return SuccessResponse(data=health)


@router.get("/{device_id}/snapshot")
async def device_snapshot(
    device_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
    channel: int = 1,
):
    """Proxy a live JPEG snapshot from Hikvision device."""
    from app.core.security import decrypt_device_password

    device = await _svc(db).get_device(device_id)
    if not device:
        raise NotFoundException(f"Device {device_id} not found.")

    password = decrypt_device_password(device.password_enc)
    url = (
        f"http://{device.ip_address}:{device.port}"
        f"/ISAPI/Streaming/channels/{channel}01/picture"
    )
    try:
        async with httpx.AsyncClient(
            auth=httpx.DigestAuth(device.username, password), timeout=5.0
        ) as client:
            resp = await client.get(url)
        if resp.status_code == 200:
            return Response(
                content=resp.content,
                media_type="image/jpeg",
                headers={"Cache-Control": "no-store"},
            )
    except Exception:
        pass
    # Return transparent 1×1 pixel on error so <img> doesn't break
    import base64
    placeholder = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    return Response(content=placeholder, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.post("/{device_id}/import-persons", response_model=SuccessResponse[dict])
async def import_persons(
    device_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
    category_id: int | None = None,
):
    """Fetch all persons from Hikvision device and import missing ones as students."""
    device = await _svc(db).get_device(device_id)
    if not device:
        raise NotFoundException(f"Device {device_id} not found.")

    persons = await hikvision_sync.fetch_persons_from_device(device)

    repo = StudentRepository(db)
    created = 0
    skipped = 0
    errors: list[str] = []

    for person in persons:
        try:
            existing = await repo.get_by_employee_no(person["employee_no"])
            if existing:
                skipped += 1
                continue
            student = Student(
                name=person["name"],
                employee_no=person["employee_no"],
                category_id=category_id,
            )
            db.add(student)
            created += 1
        except Exception as exc:
            errors.append(f"{person.get('name', '?')}: {exc}")

    await db.commit()

    logger.info(
        "persons_imported",
        device=device.name,
        total=len(persons),
        created=created,
        skipped=skipped,
    )

    return SuccessResponse(data={
        "total": len(persons),
        "created": created,
        "skipped": skipped,
        "errors": errors,
    })
