"""Optional Prometheus metrics for AttendX.

Enabled when ENABLE_METRICS=true in environment.
Requires: pip install prometheus-fastapi-instrumentator
"""

import structlog

logger = structlog.get_logger()

# Metric objects populated by setup_metrics(); None when metrics are disabled.
ATTENDANCE_EVENTS = None
LOGIN_ATTEMPTS = None
WEBHOOK_DELIVERIES = None
DEVICES_ONLINE = None
ACTIVE_STUDENTS = None


def setup_metrics(app) -> None:
    """
    Instrument the FastAPI app with Prometheus metrics.
    Exposes /metrics endpoint.
    """
    global ATTENDANCE_EVENTS, LOGIN_ATTEMPTS, WEBHOOK_DELIVERIES, DEVICES_ONLINE, ACTIVE_STUDENTS  # noqa: PLW0603

    try:
        from prometheus_client import Counter, Gauge
        from prometheus_fastapi_instrumentator import Instrumentator

        ATTENDANCE_EVENTS = Counter(
            "attendx_attendance_events_total",
            "Total attendance events processed",
            ["event_type", "device_id"],
        )

        LOGIN_ATTEMPTS = Counter(
            "attendx_login_attempts_total",
            "Total login attempts",
            ["status"],  # success | failed | locked
        )

        WEBHOOK_DELIVERIES = Counter(
            "attendx_webhook_deliveries_total",
            "Total webhook delivery attempts",
            ["status", "event_type"],
        )

        DEVICES_ONLINE = Gauge(
            "attendx_devices_online",
            "Number of currently online devices",
        )

        ACTIVE_STUDENTS = Gauge(
            "attendx_active_students",
            "Number of active students",
        )

        Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            excluded_handlers=["/health", "/health/detailed", "/metrics"],
        ).instrument(app).expose(app, endpoint="/metrics")

        logger.info("prometheus_metrics_enabled")

    except ImportError:
        logger.warning(
            "prometheus_not_installed",
            hint="Run: pip install prometheus-fastapi-instrumentator",
        )
