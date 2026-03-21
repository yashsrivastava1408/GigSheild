from __future__ import annotations

from datetime import datetime, timezone

try:
    from datetime import UTC as _UTC
except ImportError:  # pragma: no cover - Python 3.10 fallback
    _UTC = timezone.utc

UTC = _UTC


def utcnow() -> datetime:
    return datetime.now(UTC)
