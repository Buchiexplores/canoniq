"""Confidence combination + status gating (§13.1, §13.2)."""

from __future__ import annotations

from canoniq.core.constants import (
    STATUS_AUTO_APPROVED,
    STATUS_LOW_CONFIDENCE,
    STATUS_REQUIRES_REVIEW,
)


def combine_confidence(signals: dict[str, float], weights: dict[str, float]) -> float:
    """Weighted sum of per-signal scores, clamped to [0, 1].

    Weights are normalized so the active signals' weights sum to 1.0 (this lets the
    optional semantic signal be added without re-tuning the others).
    """
    active = {k: w for k, w in weights.items() if w > 0.0}
    total_weight = sum(active.values()) or 1.0
    score = 0.0
    for key, weight in active.items():
        score += (weight / total_weight) * float(signals.get(key, 0.0))
    return max(0.0, min(1.0, round(score, 4)))


def status_for_confidence(
    confidence: float,
    *,
    auto_threshold: float,
    review_threshold: float,
) -> str:
    if confidence >= auto_threshold:
        return STATUS_AUTO_APPROVED
    if confidence >= review_threshold:
        return STATUS_REQUIRES_REVIEW
    return STATUS_LOW_CONFIDENCE
