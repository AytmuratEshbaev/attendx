"""Async database engine and session management."""

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

logger = structlog.get_logger()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Test the database connection on startup."""
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )
    logger.info("database_connected", url=settings.DATABASE_URL.split("@")[-1])


async def close_db() -> None:
    """Dispose the engine on shutdown."""
    await engine.dispose()
    logger.info("database_disconnected")
