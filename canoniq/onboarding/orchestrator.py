"""Auto-onboarding orchestrator.

Runs the full CanonIQ pipeline for a provider's sources, scores deployment
readiness, and emits a report. It never deploys anything — the output is a
*readiness verdict* plus the canonical artifacts a deploy step could consume.

Per source: profile → suggest mappings → generate validation rules → transform →
(optional) drift-check. Per provider: aggregate into a weighted readiness score
and a clear next action.
"""

from __future__ import annotations

import os

from canoniq.core.constants import (
    STATUS_AUTO_APPROVED,
    STATUS_LOW_CONFIDENCE,
    STATUS_REQUIRES_REVIEW,
    STATUS_UNMAPPED,
)
from canoniq.core.util import now_iso
from canoniq.engine import CanonIQ
from canoniq.onboarding.config import OnboardingConfig, load_onboarding_config
from canoniq.onboarding.models import (
    STATUS_BLOCKED,
    STATUS_NEEDS_REVIEW,
    STATUS_READY_AUTO,
    STATUS_READY_MINOR,
    CombinedReport,
    CombinedReportEntry,
    ReadinessReport,
)
from canoniq.onboarding.readiness import (
    DRIFT_NOT_CHECKED,
    ReadinessResult,
    SourceOutcome,
    compute_readiness,
    status_for_score,
)

# Human-facing guidance per status band.
_RECOMMENDATIONS: dict[str, str] = {
    STATUS_READY_AUTO: (
        "All required fields are mapped with high confidence and validation passed — "
        "promote the generated canonical package to the target environment."
    ),
    STATUS_READY_MINOR: (
        "Coverage is strong; a reviewer should confirm the flagged review-grade mappings "
        "before promotion."
    ),
    STATUS_NEEDS_REVIEW: (
        "Several mappings need human review or required fields are incomplete — resolve "
        "them, then re-run onboarding."
    ),
    STATUS_BLOCKED: (
        "Critical gaps remain (missing required fields or failing validation) — this "
        "provider cannot be onboarded automatically yet."
    ),
}

_NEXT_ACTIONS: dict[str, str] = {
    STATUS_READY_AUTO: "auto_deploy",
    STATUS_READY_MINOR: "review_then_deploy",
    STATUS_NEEDS_REVIEW: "resolve_mappings",
    STATUS_BLOCKED: "block_and_escalate",
}


def _build_outcome(engine: CanonIQ, source, schema) -> SourceOutcome:
    """Run the pipeline for one source and collapse it into a ``SourceOutcome``."""
    profile = engine.profile_source(source.path)
    mapping = engine.suggest_mappings(profile, source.canonical)

    auto = sum(1 for m in mapping.mappings if m.status == STATUS_AUTO_APPROVED)
    review = sum(1 for m in mapping.mappings if m.status == STATUS_REQUIRES_REVIEW)
    low = sum(1 for m in mapping.mappings if m.status == STATUS_LOW_CONFIDENCE)
    unmapped = sum(1 for m in mapping.mappings if m.status == STATUS_UNMAPPED)

    covered = frozenset(mapping.approved_mappings(include_review=True).values())
    required = frozenset(name for name, f in schema.fields.items() if f.required)

    rules = engine.generate_validation_rules(mapping, source.canonical, profile)
    transformed = engine.apply_mapping(
        source.path, mapping, source.canonical, include_review=True
    )
    report = engine.validate(transformed.records, rules)
    failures = sum(1 for f in report.findings if not f.passed and f.severity == "error")

    drift_status = DRIFT_NOT_CHECKED
    if source.drift_path:
        drift = engine.detect_drift(source.drift_path, mapping, source.canonical)
        drift_status = drift.status

    return SourceOutcome(
        source=source.name,
        entity=source.entity,
        total_source_fields=len(mapping.mappings),
        auto_approved=auto,
        requires_review=review,
        low_confidence=low,
        unmapped=unmapped,
        covered_canonical_fields=covered,
        required_fields=required,
        validation_passed=report.passed,
        validation_findings=len(report.findings),
        validation_failures=failures,
        drift_status=drift_status,
    )


def _auto_deploy_allowed(config: OnboardingConfig, result: ReadinessResult) -> bool:
    policy = config.deployment
    if result.score < policy.minimum_readiness_score:
        return False
    if policy.require_required_fields and not result.required_fields_covered:
        return False
    if policy.require_validation_pass and not result.validation_passed:
        return False
    return True


def onboard_provider(
    config_path: str,
    *,
    engine: CanonIQ | None = None,
    write_outputs: bool = True,
    canoniq_version: str | None = None,
) -> ReadinessReport:
    """Onboard one provider and return its deployment-readiness report."""
    config = load_onboarding_config(config_path)
    eng = engine or CanonIQ()

    outcomes: list[SourceOutcome] = []
    for source in config.sources:
        schema = eng.load_schema(source.canonical)
        outcomes.append(_build_outcome(eng, source, schema))

    result = compute_readiness(outcomes)
    status = status_for_score(result.score)
    auto_deploy = _auto_deploy_allowed(config, result)

    report = ReadinessReport(
        provider_id=config.provider_id,
        provider_name=config.provider_name,
        environment=config.environment,
        status=status,
        readiness_score=result.score,
        summary=result.summary,
        component_scores=result.component_scores,
        sources=result.sources,
        deployment_recommendation=_RECOMMENDATIONS[status],
        auto_deploy_allowed=auto_deploy,
        next_action=_NEXT_ACTIONS[status],
        created_at=now_iso(),
        canoniq_version=canoniq_version,
    )

    if write_outputs and config.output_dir:
        out_path = os.path.join(config.output_dir, f"{config.provider_id}_readiness.json")
        CanonIQ.write_json(report, out_path)

    return report


def onboard_providers(
    config_dir: str,
    *,
    engine: CanonIQ | None = None,
    write_outputs: bool = True,
    combined_out: str | None = None,
    canoniq_version: str | None = None,
) -> tuple[list[ReadinessReport], CombinedReport]:
    """Onboard every ``*.yml``/``*.yaml`` config in a directory; roll up the results."""
    if not os.path.isdir(config_dir):
        raise NotADirectoryError(f"Config directory not found: {config_dir}")

    config_files = sorted(
        os.path.join(config_dir, name)
        for name in os.listdir(config_dir)
        if name.endswith((".yml", ".yaml"))
    )
    if not config_files:
        raise FileNotFoundError(f"No onboarding configs (*.yml) in {config_dir}")

    eng = engine or CanonIQ()
    reports = [
        onboard_provider(
            path, engine=eng, write_outputs=write_outputs, canoniq_version=canoniq_version
        )
        for path in config_files
    ]

    combined = CombinedReport(
        total_providers=len(reports),
        ready_for_auto_deploy=sum(1 for r in reports if r.status == STATUS_READY_AUTO),
        ready_with_minor_review=sum(1 for r in reports if r.status == STATUS_READY_MINOR),
        needs_mapping_review=sum(1 for r in reports if r.status == STATUS_NEEDS_REVIEW),
        blocked=sum(1 for r in reports if r.status == STATUS_BLOCKED),
        providers=[
            CombinedReportEntry(
                provider_id=r.provider_id,
                provider_name=r.provider_name,
                readiness_score=r.readiness_score,
                status=r.status,
                auto_deploy_allowed=r.auto_deploy_allowed,
            )
            for r in reports
        ],
        created_at=now_iso(),
        canoniq_version=canoniq_version,
    )

    if write_outputs and combined_out:
        CanonIQ.write_json(combined, combined_out)

    return reports, combined
