"""Pydantic models for the config-driven onboarding workflow (auto-onboarding).

These models describe the *readiness* output produced when CanonIQ onboards one or
more data providers. A "provider" is whatever entity supplies data in your domain —
a school, a retail vendor, a hospital, a SaaS tenant, a partner bank. CanonIQ
profiles each source, maps it to canonical models, validates, and scores how
deployment-ready the result is.

All models forbid unknown fields and serialize to stable JSON.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# Readiness status bands (see ``readiness.status_for_score``).
STATUS_READY_AUTO = "ready_for_auto_deploy"
STATUS_READY_MINOR = "ready_with_minor_review"
STATUS_NEEDS_REVIEW = "needs_mapping_review"
STATUS_BLOCKED = "blocked"


class ComponentScore(BaseModel):
    """One weighted component of the readiness score."""

    model_config = ConfigDict(extra="forbid")

    ratio: float  # 0.0–1.0 raw coverage/quality for this component
    weight: float  # contribution weight (the five weights sum to 1.0)
    points: float  # ratio * weight * 100, rounded


class SourceReadiness(BaseModel):
    """Per-source onboarding outcome for a single data file."""

    model_config = ConfigDict(extra="forbid")

    source: str
    entity: str
    total_source_fields: int
    mapped_fields: int
    auto_approved: int
    requires_review: int
    low_confidence: int
    unmapped: int
    validation_passed: bool
    validation_findings: int = 0
    validation_failures: int = 0
    drift_status: str = "not_checked"


class ReadinessSummary(BaseModel):
    """Aggregate counts across all of a provider's sources."""

    model_config = ConfigDict(extra="forbid")

    total_fields: int
    mapped_fields: int
    auto_approved_mappings: int
    requires_review: int
    low_confidence: int
    required_fields_covered: bool


class ReadinessReport(BaseModel):
    """Deployment-readiness report for one onboarded provider."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str
    provider_name: str
    environment: str
    status: str
    readiness_score: int
    summary: ReadinessSummary
    component_scores: dict[str, ComponentScore] = Field(default_factory=dict)
    sources: list[SourceReadiness] = Field(default_factory=list)
    deployment_recommendation: str
    auto_deploy_allowed: bool
    next_action: str
    created_at: str
    canoniq_version: str | None = None


class CombinedReportEntry(BaseModel):
    """One provider's headline result inside a combined multi-provider summary."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str
    provider_name: str
    readiness_score: int
    status: str
    auto_deploy_allowed: bool


class CombinedReport(BaseModel):
    """Roll-up across every provider onboarded in a multi-provider run."""

    model_config = ConfigDict(extra="forbid")

    total_providers: int
    ready_for_auto_deploy: int
    ready_with_minor_review: int
    needs_mapping_review: int
    blocked: int
    providers: list[CombinedReportEntry] = Field(default_factory=list)
    created_at: str
    canoniq_version: str | None = None
