"""Config models + loader for the auto-onboarding workflow.

An onboarding config describes *one provider*: its identity, the deployment policy,
and the list of sources to profile/map/validate. A "provider" is whatever supplies
data in your domain — a school, a retail vendor, a hospital, a SaaS tenant. Every
file reference in the YAML is resolved **relative to the config file's directory**,
so configs and data can live side-by-side and move together.

The structure mirrors the rest of CanonIQ: Pydantic models with ``extra="forbid"``
and a thin ``load_onboarding_config`` that reads YAML and resolves paths.
"""

from __future__ import annotations

import os

import yaml
from pydantic import BaseModel, ConfigDict, Field

# Default deployment gate: a provider must score at least this high (and clear the
# required-field + validation checks) before auto-deploy is permitted.
DEFAULT_MINIMUM_READINESS_SCORE = 90
DEFAULT_ENVIRONMENT = "staging"


class OnboardingSource(BaseModel):
    """One source file to onboard, mapped to a single canonical entity."""

    model_config = ConfigDict(extra="forbid")

    name: str
    entity: str
    path: str  # source data file (CSV/JSON/JSONL), resolved on load
    canonical: str  # canonical schema YAML, resolved on load
    drift_path: str | None = None  # optional "next batch" file to drift-check against


class DeploymentPolicy(BaseModel):
    """Provider-level gate that decides whether auto-deploy is allowed."""

    model_config = ConfigDict(extra="forbid")

    minimum_readiness_score: int = DEFAULT_MINIMUM_READINESS_SCORE
    require_required_fields: bool = True
    require_validation_pass: bool = True


class OnboardingConfig(BaseModel):
    """Fully-resolved onboarding plan for a single provider."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str
    provider_name: str
    environment: str = DEFAULT_ENVIRONMENT
    deployment: DeploymentPolicy = Field(default_factory=DeploymentPolicy)
    sources: list[OnboardingSource] = Field(default_factory=list)
    output_dir: str | None = None


def _resolve(base_dir: str, path: str | None) -> str | None:
    if path is None:
        return None
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(base_dir, path))


def load_onboarding_config(path: str) -> OnboardingConfig:
    """Load + validate an onboarding config, resolving every path relative to it.

    Accepts the nested YAML shape::

        provider: {id, name, environment}
        deployment: {minimum_readiness_score, ...}
        sources: [{name, entity, path, canonical, drift_path?}, ...]
        output: {dir}
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Onboarding config not found: {path}")
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    base_dir = os.path.dirname(os.path.abspath(path))
    provider = data.get("provider", {}) or {}
    output = data.get("output", {}) or {}

    sources = [
        OnboardingSource(
            name=raw["name"],
            entity=raw["entity"],
            path=_resolve(base_dir, raw["path"]),  # type: ignore[arg-type]
            canonical=_resolve(base_dir, raw["canonical"]),  # type: ignore[arg-type]
            drift_path=_resolve(base_dir, raw.get("drift_path")),
        )
        for raw in data.get("sources", []) or []
    ]

    return OnboardingConfig(
        provider_id=provider.get("id") or data.get("provider_id", "unknown"),
        provider_name=provider.get("name") or data.get("provider_name", "Unknown Provider"),
        environment=provider.get("environment", DEFAULT_ENVIRONMENT),
        deployment=DeploymentPolicy(**(data.get("deployment", {}) or {})),
        sources=sources,
        output_dir=_resolve(base_dir, output.get("dir")),
    )
