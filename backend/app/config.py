"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # -- Application -----------------------------------------------------------
    APP_NAME: str = "AttendX"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # -- Database --------------------------------------------------------------
    DATABASE_URL: str = (
        "postgresql+asyncpg://attendx:password@db:5432/attendx"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql://attendx:password@db:5432/attendx"
    )

    # -- Redis -----------------------------------------------------------------
    REDIS_URL: str = "redis://redis:6379/0"

    # -- Auth & Security -------------------------------------------------------
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    JWT_SECRET: str = "change-me-to-a-random-32-char-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRY_MINUTES: int = 60
    JWT_REFRESH_EXPIRY_DAYS: int = 7

    # -- Encryption ------------------------------------------------------------
    FERNET_KEY: str = "change-me"

    # -- Telegram --------------------------------------------------------------
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""  # e.g. "AttendXBot" (without @)
    ADMIN_CHAT_ID: int = 0  # Telegram chat ID for admin alerts (0 = disabled)
    WEBHOOK_DOMAIN: str = ""  # Public domain for webhook mode (e.g. example.com)

    # -- API Keys --------------------------------------------------------------
    API_KEY_HEADER: str = "X-API-Key"
    DEFAULT_API_KEY: str = "change-me"

    # -- Sentry ----------------------------------------------------------------
    SENTRY_DSN: str = ""

    # -- CORS ------------------------------------------------------------------
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost"

    # -- Metrics ---------------------------------------------------------------
    ENABLE_METRICS: bool = False  # Set true to expose /metrics (Prometheus)

    # -- Hikvision -------------------------------------------------------------
    HIKVISION_POLL_INTERVAL: int = 5
    # Hours to add to UTC when sending timestamps to Hikvision device API.
    # Devices interpret times without tz suffix as their local time.
    # Set to 5 for Uzbekistan (UTC+5).
    DEVICE_TZ_OFFSET_HOURS: int = 5

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, v: str | list[str]) -> str:
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
