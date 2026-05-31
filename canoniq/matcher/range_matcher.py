"""Range signal: whether observed min/max fall within canonical min/max (§13)."""

from __future__ import annotations

from canoniq.core.models import CanonicalField, SourceFieldProfile


def range_score(source: SourceFieldProfile, canonical: CanonicalField) -> tuple[float, str | None]:
    # Only meaningful when the canonical field declares numeric bounds.
    if canonical.min is None and canonical.max is None:
        return 0.0, None
    if source.min is None or source.max is None:
        return 0.0, None

    lo = canonical.min if canonical.min is not None else float("-inf")
    hi = canonical.max if canonical.max is not None else float("inf")

    if source.min >= lo and source.max <= hi:
        return 1.0, f"observed range [{source.min}, {source.max}] within [{lo}, {hi}]"

    # Partial: overlapping but exceeding bounds.
    if source.max < lo or source.min > hi:
        return 0.0, f"observed range [{source.min}, {source.max}] outside [{lo}, {hi}]"
    return 0.4, f"observed range [{source.min}, {source.max}] partially within [{lo}, {hi}]"
