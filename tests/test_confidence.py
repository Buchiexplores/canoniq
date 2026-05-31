"""Confidence combination + status gating tests (§13.1, §13.2)."""

from __future__ import annotations

from canoniq.core.constants import (
    DEFAULT_AUTO_APPROVE_THRESHOLD,
    DEFAULT_REVIEW_THRESHOLD,
    DEFAULT_WEIGHTS,
    STATUS_AUTO_APPROVED,
    STATUS_LOW_CONFIDENCE,
    STATUS_REQUIRES_REVIEW,
)
from canoniq.scoring.confidence import combine_confidence, status_for_confidence


def test_perfect_signals_give_full_confidence():
    signals = {"alias": 1.0, "name": 1.0, "type": 1.0, "pattern": 1.0, "range": 1.0}
    assert combine_confidence(signals, DEFAULT_WEIGHTS) == 1.0


def test_zero_signals_give_zero():
    assert combine_confidence({}, DEFAULT_WEIGHTS) == 0.0


def test_alias_only_uses_weight():
    signals = {"alias": 1.0}
    # alias weight 0.40 of total active weight (1.0) → 0.40
    assert combine_confidence(signals, DEFAULT_WEIGHTS) == 0.40


def test_active_weights_renormalize_when_semantic_enabled():
    weights = dict(DEFAULT_WEIGHTS, semantic=0.10)
    # all-1 signals still normalize to 1.0 regardless of added semantic weight
    signals = {k: 1.0 for k in weights}
    assert combine_confidence(signals, weights) == 1.0


def test_confidence_clamped_to_unit_interval():
    assert combine_confidence({"alias": 5.0}, {"alias": 1.0}) == 1.0
    assert combine_confidence({"alias": -5.0}, {"alias": 1.0}) == 0.0


def test_status_thresholds():
    assert status_for_confidence(
        0.95, auto_threshold=DEFAULT_AUTO_APPROVE_THRESHOLD,
        review_threshold=DEFAULT_REVIEW_THRESHOLD,
    ) == STATUS_AUTO_APPROVED
    assert status_for_confidence(
        0.80, auto_threshold=DEFAULT_AUTO_APPROVE_THRESHOLD,
        review_threshold=DEFAULT_REVIEW_THRESHOLD,
    ) == STATUS_REQUIRES_REVIEW
    assert status_for_confidence(
        0.50, auto_threshold=DEFAULT_AUTO_APPROVE_THRESHOLD,
        review_threshold=DEFAULT_REVIEW_THRESHOLD,
    ) == STATUS_LOW_CONFIDENCE
