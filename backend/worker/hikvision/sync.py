"""Sync student face data to Hikvision terminals.

The actual sync logic lives in app/services/hikvision_sync.py so it can be
called from both the API layer (access group endpoints) and the worker.
This module re-exports the public helpers for worker-side usage.
"""

from app.services.hikvision_sync import (  # noqa: F401
    HikvisionSyncError,
    remove_person,
    sync_face,
    sync_person,
)
