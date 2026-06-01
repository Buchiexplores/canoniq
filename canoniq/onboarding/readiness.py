"""Readiness scoring for auto-onboarding.

Turns the per-source pipeline outcomes (mapping counts, validation results,
required-field coverage, drift status) into a single 0–100 readiness score and a
deployment recommendation.

The score is a weighted blend of five components (weights sum to 1.0):

============================  ======  ======================================================
component                     weight  ratio (0.0–1.0)
============================  ======  ======================================================
schema_mapping                 0.35   mapped source fields / total source fields
required_fields                0.25   required canonical fields covered / required total
validation                     0.15   passing validation findings / total findings
auto_approved                  0.15   auto-approved mappings / mapped fields
drift                          0.10   sources with no drift / drift-checked sources
============================  ======  ======================================================

Required-field coverage is computed **per entity** using the union of every source
that targets that entity — a single source need not carry every required field.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from canoniq.onboarding.models import (
    STATUS_BLOCKED,
    STATUS_NEEDS_REVIEW,
    STATUS_READY_AUTO,
    STATUS_READY_MINOR,
    ComponentScore,
    ReadinessSummary,
    SourceReadiness,
)

# Readiness component weights (§10). Must sum to 1.0.
WEIGHTS: dict[str, float] = {
    "schema_mapping": 0.35,
    "required_fields": 0.25,
    "validation": 0.15,
    "auto_approved": 0.15,
    "drift": 0.10,
}

# Score → status bands (§10).
BAND_READY_AUTO = 90
BAND_READY_MINOR = 80
BAND_NEEDS_REVIEW = 60

DRIFT_NO_DRIFT = "no_drift"
DRIFT_DETECTED = "drift_detected"
DRIFT_NOT_CHECKED = "not_checked"


@dataclass(frozen=True)
class SourceOutcome:
    """Per-source pipeline result feeding the readiness calculation."""

    source: str
    entity: str
    total_source_fields: int
    auto_approved: int
    requires_review: int
    low_confidence: int
    unmapped: int
    covered_canonical_fields: frozenset[str]
    required_fields: frozenset[str]
    validation_passed: bool
    validation_findings: int = 0
    validation_failures: int = 0
    drift_status: str = DRIFT_NOT_CHECKED

    @property
    def mapped_fields(self) -> int:
        """Source fields with a usable or review-grade canonical target."""
        return self.auto_approved + self.requires_review


@dataclass(frozen=True)
class ReadinessResult:
    """Computed readiness, ready to assemble into a ``ReadinessReport``."""

    score: int
    summary: ReadinessSummary
    component_scores: dict[str, ComponentScore]
    sources: list[SourceReadiness] = field(default_factory=list)
    required_fields_covered: bool = False
    validation_passed: bool = False


def status_for_score(score: int) -> str:
    """Map a 0–100 readiness score to its status band."""
    if score >= BAND_READY_AUTO:
        return STATUS_READY_AUTO
    if score >= BAND_READY_MINOR:
        return STATUS_READY_MINOR
    if score >= BAND_NEEDS_REVIEW:
        return STATUS_NEEDS_REVIEW
    return STATUS_BLOCKED


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 1.0  # nothing to satisfy → fully satisfied (neutral)
    return max(0.0, min(1.0, numerator / denominator))


def _component(ratio: float, weight: float) -> ComponentScore:
    return ComponentScore(
        ratio=round(ratio, 4),
        weight=weight,
        points=round(ratio * weight * 100, 2),
    )


def _required_coverage(outcomes: list[SourceOutcome]) -> tuple[int, int, bool]:
    """Per-entity required-field coverage via the union of an entity's sources.

    Returns ``(covered_count, required_count, all_covered)`` aggregated across entities.
    """
    by_entity: dict[str, dict[str, frozenset[str]]] = {}
    for o in outcomes:
        bucket = by_entity.setdefault(o.entity, {"required": frozenset(), "covered": frozenset()})
        bucket["required"] = bucket["required"] | o.required_fields
        bucket["covered"] = bucket["covered"] | o.covered_canonical_fields

    covered_total = 0
    required_total = 0
    all_covered = True
    for bucket in by_entity.values():
        required = bucket["required"]
        covered_required = required & bucket["covered"]
        required_total += len(required)
        covered_total += len(covered_required)
        if covered_required != required:
            all_covered = False
    return covered_total, required_total, all_covered


def compute_readiness(outcomes: list[SourceOutcome]) -> ReadinessResult:
    """Blend per-source outcomes into a weighted readiness score + summary."""
    total_fields = sum(o.total_source_fields for o in outcomes)
    mapped_fields = sum(o.mapped_fields for o in outcomes)
    auto_approved = sum(o.auto_approved for o in outcomes)
    requires_review = sum(o.requires_review for o in outcomes)
    low_confidence = sum(o.low_confidence for o in outcomes)

    covered_required, required_total, required_covered = _required_coverage(outcomes)

    total_findings = sum(o.validation_findings for o in outcomes)
    total_failures = sum(o.validation_failures for o in outcomes)
    validation_passed = all(o.validation_passed for o in outcomes) if outcomes else True

    checked = [o for o in outcomes if o.drift_status != DRIFT_NOT_CHECKED]
    no_drift = sum(1 for o in checked if o.drift_status == DRIFT_NO_DRIFT)

    components = {
        "schema_mapping": _component(_ratio(mapped_fields, total_fields), WEIGHTS["schema_mapping"]),
        "required_fields": _component(
            _ratio(covered_required, required_total), WEIGHTS["required_fields"]
        ),
        "validation": _component(
            _ratio(total_findings - total_failures, total_findings), WEIGHTS["validation"]
        ),
        "auto_approved": _component(_ratio(auto_approved, mapped_fields), WEIGHTS["auto_approved"]),
        "drift": _component(_ratio(no_drift, len(checked)), WEIGHTS["drift"]),
    }
    score = round(sum(c.points for c in components.values()))

    summary = ReadinessSummary(
        total_fields=total_fields,
        mapped_fields=mapped_fields,
        auto_approved_mappings=auto_approved,
        requires_review=requires_review,
        low_confidence=low_confidence,
        required_fields_covered=required_covered,
    )

    sources = [
        SourceReadiness(
            source=o.source,
            entity=o.entity,
            total_source_fields=o.total_source_fields,
            mapped_fields=o.mapped_fields,
            auto_approved=o.auto_approved,
            requires_review=o.requires_review,
            low_confidence=o.low_confidence,
            unmapped=o.unmapped,
            validation_passed=o.validation_passed,
            validation_findings=o.validation_findings,
            validation_failures=o.validation_failures,
            drift_status=o.drift_status,
        )
        for o in outcomes
    ]

    return ReadinessResult(
        score=score,
        summary=summary,
        component_scores=components,
        sources=sources,
        required_fields_covered=required_covered,
        validation_passed=validation_passed,
    )
