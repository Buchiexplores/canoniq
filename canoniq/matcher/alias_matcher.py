"""Alias signal: exact/normalized match against canonical aliases + the field name (§13)."""

from __future__ import annotations

from canoniq.core.models import CanonicalField, SourceFieldProfile
from canoniq.core.util import normalize_name


def alias_score(source: SourceFieldProfile, canonical: CanonicalField) -> tuple[float, str | None]:
    """Return (score, reason). 1.0 on exact normalized alias/name match, else 0.0."""
    src = normalize_name(source.name)
    targets = {normalize_name(canonical.name)} | {normalize_name(a) for a in canonical.aliases}

    if src == normalize_name(canonical.name):
        return 1.0, f"'{source.name}' matches canonical name '{canonical.name}'"
    if src in targets:
        return 1.0, f"'{source.name}' is a declared alias of '{canonical.name}'"
    return 0.0, None
