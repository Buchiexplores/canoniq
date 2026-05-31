"""Small shared utilities (timestamps, name normalization)."""

from __future__ import annotations

import re
from datetime import datetime, timezone

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def now_iso() -> str:
    """Current UTC time as an ISO 8601 string (seconds precision, 'Z' suffix)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_name(name: str) -> str:
    """Lowercase a field name and collapse separators to single underscores.

    'Banner ID' -> 'banner_id', 'studentEmail' -> 'student_email'.
    """
    # split camelCase / PascalCase boundaries
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    lowered = spaced.lower().strip()
    collapsed = _NON_ALNUM.sub("_", lowered)
    return collapsed.strip("_")


def tokens(name: str) -> set[str]:
    """Token set for a normalized name."""
    return {t for t in normalize_name(name).split("_") if t}
