"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    access_groups,
    api_keys,
    attendance,
    audit,
    auth,
    categories,
    devices,
    external,
    reports,
    security,
    sse,
    students,
    telegram,
    timetables,
    users,
    webhooks,
)

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(timetables.router)
router.include_router(access_groups.router)
router.include_router(categories.router)
router.include_router(students.router)
router.include_router(attendance.router)
router.include_router(devices.router)
router.include_router(webhooks.router)
router.include_router(reports.router)
router.include_router(external.router)
router.include_router(api_keys.router)
router.include_router(audit.router)
router.include_router(security.router)
router.include_router(users.router)
router.include_router(sse.router)
router.include_router(telegram.router)
