"""Hikvision worker process entry point.

Run from the backend/ directory:
    python -m worker.main

Or:
    poetry run python -m worker.main
"""

from __future__ import annotations

import asyncio

import redis.asyncio as aioredis
import structlog

from app.config import settings
from app.core.database import AsyncSessionLocal, close_db, init_db
from app.core.logging import setup_logging

setup_logging()
logger = structlog.get_logger()


async def _init_webhook_engine(redis: aioredis.Redis) -> None:
    """Initialize the webhook engine singleton (same as FastAPI lifespan)."""
    from app.services.webhook_engine import WebhookEngine
    from app.services.webhook_events import WebhookEventManager, set_webhook_event_manager
    from app.services.webhook_retry import WebhookRetryManager

    try:
        engine = WebhookEngine(AsyncSessionLocal, redis)
        await engine.initialize()
        retry_mgr = WebhookRetryManager(engine, AsyncSessionLocal, redis)
        engine.set_retry_manager(retry_mgr)
        set_webhook_event_manager(WebhookEventManager(engine))
        logger.info("webhook_engine_initialized")
    except Exception as exc:
        logger.warning("webhook_engine_init_failed", error=str(exc))


async def main() -> None:
    logger.info("worker_starting", poll_interval=settings.HIKVISION_POLL_INTERVAL)

    # Connect to database
    await init_db()

    # Connect to Redis
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis.ping()
    logger.info("redis_connected")

    # Initialize webhook engine so events fire on attendance
    await _init_webhook_engine(redis)

    # Start poller
    from worker.hikvision.poller import AttendancePoller

    poller = AttendancePoller(redis=redis)
    try:
        await poller.run_forever()
    finally:
        await redis.aclose()
        await close_db()
        logger.info("worker_stopped")


if __name__ == "__main__":
    asyncio.run(main())
