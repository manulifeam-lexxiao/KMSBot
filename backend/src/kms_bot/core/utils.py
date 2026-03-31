"""Shared low-level utilities.

Centralises helpers that would otherwise be copy-pasted across service
modules (sync, search, placeholders).  Keep this module dependency-free
(stdlib only).
"""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def make_job_id(prefix: str) -> str:
    """Build a sortable, human-readable job identifier.

    Format: ``<prefix>-YYYYMMDDHHMMSS``
    """
    return f"{prefix}-{utcnow().strftime('%Y%m%d%H%M%S')}"
