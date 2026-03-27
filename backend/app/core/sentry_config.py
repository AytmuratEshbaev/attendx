"""Sentry error tracking configuration."""

import structlog

logger = structlog.get_logger()


def init_sentry(dsn: str | None, environment: str = "production") -> None:
    """
    Initialize Sentry SDK with FastAPI, SQLAlchemy, and Redis integrations.

    Does nothing if dsn is empty/None — safe to call unconditionally.
    """
    if not dsn:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        from app.core.data_masking import DataMasker

        def _filter_sensitive_data(event: dict, hint: dict) -> dict:
            """Strip sensitive fields from Sentry events before sending."""
            if "request" in event:
                if "data" in event["request"] and isinstance(
                    event["request"]["data"], dict
                ):
                    event["request"]["data"] = DataMasker.mask_dict(
                        event["request"]["data"]
                    )
                if "headers" in event["request"]:
                    headers = event["request"]["headers"]
                    for sensitive in ("authorization", "x-api-key", "cookie"):
                        if sensitive in headers:
                            headers[sensitive] = "***"
            return event

        def _filter_transaction(event: dict, hint: dict) -> dict | None:
            """Drop health-check transactions to reduce noise."""
            if event.get("transaction") in ("/health", "/health/detailed"):
                return None
            return event

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            send_default_pii=False,
            before_send=_filter_sensitive_data,
            before_send_transaction=_filter_transaction,
        )
        logger.info("sentry_initialized", environment=environment)

    except ImportError:
        logger.warning(
            "sentry_sdk_not_installed",
            hint="Add sentry-sdk[fastapi] to dependencies to enable error tracking",
        )
