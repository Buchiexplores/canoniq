"""Config-driven auto-onboarding for CanonIQ.

Profiles each of a provider's sources, maps them to canonical models, validates,
checks drift, and scores how deployment-ready the result is — without deploying
anything. A "provider" is whatever supplies data in your domain (a school, a retail
vendor, a hospital, a SaaS tenant). See :func:`onboard_provider` and
:func:`onboard_providers`.
"""

from __future__ import annotations

from canoniq.onboarding.config import (
    DeploymentPolicy,
    OnboardingConfig,
    OnboardingSource,
    load_onboarding_config,
)
from canoniq.onboarding.models import (
    STATUS_BLOCKED,
    STATUS_NEEDS_REVIEW,
    STATUS_READY_AUTO,
    STATUS_READY_MINOR,
    CombinedReport,
    CombinedReportEntry,
    ComponentScore,
    ReadinessReport,
    ReadinessSummary,
    SourceReadiness,
)
from canoniq.onboarding.orchestrator import onboard_provider, onboard_providers
from canoniq.onboarding.readiness import (
    WEIGHTS,
    SourceOutcome,
    compute_readiness,
    status_for_score,
)

__all__ = [
    "DeploymentPolicy",
    "OnboardingConfig",
    "OnboardingSource",
    "load_onboarding_config",
    "ComponentScore",
    "SourceReadiness",
    "ReadinessSummary",
    "ReadinessReport",
    "CombinedReportEntry",
    "CombinedReport",
    "STATUS_READY_AUTO",
    "STATUS_READY_MINOR",
    "STATUS_NEEDS_REVIEW",
    "STATUS_BLOCKED",
    "onboard_provider",
    "onboard_providers",
    "WEIGHTS",
    "SourceOutcome",
    "compute_readiness",
    "status_for_score",
]
