"""Security utilities: JWT, password hashing, Fernet encryption, API keys."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet  # noqa: PLW0603
    if _fernet is None:
        _fernet = Fernet(settings.FERNET_KEY.encode())
    return _fernet


# -- JWT -----------------------------------------------------------------------


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_EXPIRY_MINUTES
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_EXPIRY_DAYS
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise


# -- Password ------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# -- Fernet Encryption --------------------------------------------------------


def encrypt_device_password(password: str) -> str:
    """Encrypt a device password with Fernet."""
    return _get_fernet().encrypt(password.encode()).decode()


def decrypt_device_password(encrypted: str) -> str:
    """Decrypt a device password with Fernet."""
    return _get_fernet().decrypt(encrypted.encode()).decode()


# -- API Keys -----------------------------------------------------------------


def generate_api_key() -> tuple[str, str]:
    """Generate (raw_key, hashed_key) pair."""
    raw_key = f"ax_{secrets.token_urlsafe(32)}"
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, hashed_key


def hash_api_key(key: str) -> str:
    """Hash an API key with SHA256."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(raw_key: str, hashed_key: str) -> bool:
    """Verify a raw API key against its hash."""
    return hash_api_key(raw_key) == hashed_key
