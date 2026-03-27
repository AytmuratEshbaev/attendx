"""Redis connection pool and helpers."""

import redis.asyncio as aioredis
import structlog

from app.config import settings

logger = structlog.get_logger()

redis_pool: aioredis.Redis | None = None


async def init_redis() -> None:
    """Create the Redis connection pool on startup."""
    global redis_pool  # noqa: PLW0603
    redis_pool = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )
    await redis_pool.ping()
    logger.info("redis_connected", url=settings.REDIS_URL)


async def close_redis() -> None:
    """Close the Redis connection pool on shutdown."""
    global redis_pool  # noqa: PLW0603
    if redis_pool is not None:
        await redis_pool.close()
        redis_pool = None
        logger.info("redis_disconnected")


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency that returns the Redis connection."""
    if redis_pool is None:
        raise RuntimeError("Redis not initialized")
    return redis_pool


# -- Token Blacklist -----------------------------------------------------------


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JWT id to the blacklist with TTL."""
    r = await get_redis()
    await r.setex(f"blacklist:{jti}", ttl_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    """Check if a JWT id is blacklisted."""
    r = await get_redis()
    return await r.exists(f"blacklist:{jti}") > 0
