"""API key lifecycle management: creation, rotation, revocation."""

import hashlib
import secrets
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey

logger = structlog.get_logger()

_PREFIX = "atx_"


class APIKeyManager:
    """Manage API key lifecycle in the database."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_key(
        self,
        name: str,
        permissions: list[str] | None = None,
        created_by: uuid.UUID | None = None,
    ) -> dict:
        """
        Create a new API key.

        Returns the raw key **only once** — it is never stored in plain text.
        """
        raw_key = f"{_PREFIX}{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = APIKey(
            key_hash=key_hash,
            name=name,
            permissions=permissions or ["read"],
            is_active=True,
            created_by=created_by,
        )
        self.session.add(api_key)
        await self.session.flush()

        logger.info("api_key_created", name=name, key_id=str(api_key.id))
        return {
            "key": raw_key,  # Shown ONLY on creation
            "key_id": str(api_key.id),
            "name": name,
            "permissions": permissions or ["read"],
        }

    async def rotate_key(self, key_id: str) -> dict:
        """
        Rotate an API key: deactivate the old one and create a replacement
        with the same name and permissions.
        """
        from app.core.exceptions import NotFoundException

        old_key = await self.session.get(APIKey, uuid.UUID(key_id))
        if not old_key:
            raise NotFoundException("API key not found")

        old_key.is_active = False

        # Extract base name (strip previous "(rotated)" suffix)
        base_name = old_key.name.replace(" (rotated)", "")
        new_name = f"{base_name} (rotated)"

        permissions: list[str] = []
        if isinstance(old_key.permissions, list):
            permissions = old_key.permissions

        result = await self.create_key(
            name=new_name,
            permissions=permissions,
            created_by=old_key.created_by,
        )
        await self.session.flush()

        logger.info("api_key_rotated", old_key_id=key_id, new_key_id=result["key_id"])
        return result

    async def revoke_key(self, key_id: str) -> None:
        """Permanently deactivate an API key."""
        from app.core.exceptions import NotFoundException

        api_key = await self.session.get(APIKey, uuid.UUID(key_id))
        if not api_key:
            raise NotFoundException("API key not found")
        api_key.is_active = False
        await self.session.flush()
        logger.info("api_key_revoked", key_id=key_id)

    async def list_keys(self) -> list[dict]:
        """List all API keys without exposing raw key values."""
        result = await self.session.execute(
            select(APIKey).order_by(APIKey.created_at.desc())
        )
        keys = result.scalars().all()
        return [
            {
                "id": str(k.id),
                "name": k.name,
                "permissions": k.permissions,
                "is_active": k.is_active,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "created_at": k.created_at.isoformat(),
                "key_preview": f"{_PREFIX}****{k.key_hash[:8]}",
            }
            for k in keys
        ]

    @staticmethod
    def verify_key(raw_key: str, key_hash: str) -> bool:
        """Verify a raw API key against its stored SHA-256 hash."""
        return hashlib.sha256(raw_key.encode()).hexdigest() == key_hash
