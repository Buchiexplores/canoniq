"""Type signal: compatibility between inferred source type and canonical type (§13)."""

from __future__ import annotations

from canoniq.core.constants import (
    TYPE_DATE,
    TYPE_DECIMAL,
    TYPE_EMAIL,
    TYPE_INTEGER,
    TYPE_PERCENTAGE,
    TYPE_STRING,
    TYPE_TEXT,
    TYPE_TIMESTAMP,
    TYPE_UNKNOWN,
)
from canoniq.core.models import CanonicalField, SourceFieldProfile

# Partial-compatibility matrix: (source_type, canonical_type) -> score.
# Exact match → 1.0; listed pairs → partial; anything to string/text → 0.5; else 0.2.
_PARTIAL: dict[tuple[str, str], float] = {
    (TYPE_INTEGER, TYPE_DECIMAL): 0.85,
    (TYPE_DECIMAL, TYPE_INTEGER): 0.6,
    (TYPE_INTEGER, TYPE_PERCENTAGE): 0.7,
    (TYPE_DECIMAL, TYPE_PERCENTAGE): 0.85,
    (TYPE_PERCENTAGE, TYPE_DECIMAL): 0.85,
    (TYPE_DATE, TYPE_TIMESTAMP): 0.85,
    (TYPE_TIMESTAMP, TYPE_DATE): 0.8,
    (TYPE_EMAIL, TYPE_STRING): 0.7,
    (TYPE_STRING, TYPE_EMAIL): 0.5,
    (TYPE_TEXT, TYPE_STRING): 0.9,
    (TYPE_STRING, TYPE_TEXT): 0.9,
}

_LENIENT_TARGETS = {TYPE_STRING, TYPE_TEXT}


def type_score(source: SourceFieldProfile, canonical: CanonicalField) -> tuple[float, str | None]:
    src_type = source.declared_type or source.inferred_type
    can_type = canonical.type

    if src_type == TYPE_UNKNOWN:
        return 0.3, "source type unknown (neutral)"
    if src_type == can_type:
        return 1.0, f"types match ({src_type})"
    pair = (src_type, can_type)
    if pair in _PARTIAL:
        score = _PARTIAL[pair]
        return score, f"types compatible ({src_type}→{can_type})"
    if can_type in _LENIENT_TARGETS:
        return 0.5, f"source {src_type} fits permissive canonical {can_type}"
    return 0.2, f"types differ ({src_type}≠{can_type})"
