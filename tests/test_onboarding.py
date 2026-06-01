"""Tests for the config-driven auto-onboarding workflow.

Covers config loading + path resolution, readiness scoring math and status bands,
the per-entity required-field union rule, and the end-to-end orchestrator against
the two bundled examples: the higher-education providers (Northlake / Redwood /
Pacific State) and the retail vendors (BrightMart / Coastal / Anvil). Both share
the exact same provider-neutral engine, which is the point of having both.
"""

from __future__ import annotations

import os

import pytest

from canoniq.onboarding import (
    STATUS_BLOCKED,
    STATUS_NEEDS_REVIEW,
    STATUS_READY_AUTO,
    STATUS_READY_MINOR,
    SourceOutcome,
    compute_readiness,
    load_onboarding_config,
    onboard_provider,
    onboard_providers,
    status_for_score,
)
from canoniq.onboarding.readiness import WEIGHTS


@pytest.fixture(scope="module")
def config_dir(examples_dir: str) -> str:
    return os.path.join(examples_dir, "higher_ed_auto_onboarding", "onboarding_configs")


@pytest.fixture(scope="module")
def retail_config_dir(examples_dir: str) -> str:
    return os.path.join(examples_dir, "retail_vendor_onboarding", "onboarding_configs")


# --- weights / bands -------------------------------------------------------


def test_weights_sum_to_one():
    assert round(sum(WEIGHTS.values()), 6) == 1.0


@pytest.mark.parametrize(
    "score,expected",
    [
        (100, STATUS_READY_AUTO),
        (90, STATUS_READY_AUTO),
        (89, STATUS_READY_MINOR),
        (80, STATUS_READY_MINOR),
        (79, STATUS_NEEDS_REVIEW),
        (60, STATUS_NEEDS_REVIEW),
        (59, STATUS_BLOCKED),
        (0, STATUS_BLOCKED),
    ],
)
def test_status_bands(score, expected):
    assert status_for_score(score) == expected


# --- config loading --------------------------------------------------------


def test_load_config_resolves_paths(config_dir: str):
    cfg = load_onboarding_config(os.path.join(config_dir, "northlake_university.yml"))
    assert cfg.provider_id == "northlake_university"
    assert cfg.provider_name == "Northlake University"
    assert cfg.deployment.minimum_readiness_score == 90
    assert len(cfg.sources) == 3
    for source in cfg.sources:
        assert os.path.isabs(source.path)
        assert os.path.isfile(source.path), source.path
        assert os.path.isfile(source.canonical), source.canonical


def test_load_retail_config_resolves_paths(retail_config_dir: str):
    cfg = load_onboarding_config(os.path.join(retail_config_dir, "coastal_goods.yml"))
    assert cfg.provider_id == "coastal_goods"
    assert cfg.provider_name == "Coastal Goods Co"
    assert {s.entity for s in cfg.sources} == {"product", "inventory", "order"}
    for source in cfg.sources:
        assert os.path.isfile(source.path), source.path
        assert os.path.isfile(source.canonical), source.canonical


def test_load_config_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_onboarding_config(str(tmp_path / "nope.yml"))


# --- readiness math --------------------------------------------------------


def _outcome(**kw) -> SourceOutcome:
    base = dict(
        source="s",
        entity="student",
        total_source_fields=2,
        auto_approved=2,
        requires_review=0,
        low_confidence=0,
        unmapped=0,
        covered_canonical_fields=frozenset({"student_id", "email"}),
        required_fields=frozenset({"student_id", "email"}),
        validation_passed=True,
        validation_findings=2,
        validation_failures=0,
        drift_status="no_drift",
    )
    base.update(kw)
    return SourceOutcome(**base)


def test_perfect_outcome_scores_100():
    result = compute_readiness([_outcome()])
    assert result.score == 100
    assert result.required_fields_covered is True
    assert result.validation_passed is True


def test_required_coverage_uses_union_across_sources():
    """An entity split across two sources should cover required fields jointly."""
    sis = _outcome(
        source="sis",
        total_source_fields=1,
        auto_approved=1,
        covered_canonical_fields=frozenset({"email"}),
    )
    lms = _outcome(
        source="lms",
        total_source_fields=1,
        auto_approved=1,
        covered_canonical_fields=frozenset({"student_id"}),
    )
    result = compute_readiness([sis, lms])
    # Neither source alone covers both required fields, but together they do.
    assert result.required_fields_covered is True
    assert result.component_scores["required_fields"].ratio == 1.0


def test_missing_required_field_lowers_score_and_flag():
    no_email = _outcome(
        total_source_fields=1,
        auto_approved=1,
        covered_canonical_fields=frozenset({"student_id"}),
    )
    result = compute_readiness([no_email])
    assert result.required_fields_covered is False
    assert result.component_scores["required_fields"].ratio == 0.5


def test_validation_failures_drive_component_down():
    failing = _outcome(validation_passed=False, validation_findings=4, validation_failures=2)
    result = compute_readiness([failing])
    assert result.validation_passed is False
    assert result.component_scores["validation"].ratio == 0.5


# --- end-to-end orchestrator: higher-education example --------------------


def test_onboard_northlake_ready(config_dir: str):
    report = onboard_provider(
        os.path.join(config_dir, "northlake_university.yml"), write_outputs=False
    )
    assert report.status == STATUS_READY_AUTO
    assert report.readiness_score >= 90
    assert report.auto_deploy_allowed is True
    assert report.summary.required_fields_covered is True
    assert report.next_action == "auto_deploy"


def test_onboard_pacific_blocked(config_dir: str):
    report = onboard_provider(
        os.path.join(config_dir, "pacific_state_university.yml"), write_outputs=False
    )
    # Missing email + drift + cryptic headers → low score, no auto-deploy.
    assert report.auto_deploy_allowed is False
    assert report.summary.required_fields_covered is False
    assert report.readiness_score < 90


def test_auto_deploy_blocked_when_required_incomplete(config_dir: str):
    """Redwood scores well but lacks a required field → auto-deploy withheld."""
    report = onboard_provider(
        os.path.join(config_dir, "redwood_college.yml"), write_outputs=False
    )
    assert report.summary.required_fields_covered is False
    assert report.auto_deploy_allowed is False


def test_onboard_providers_combined(config_dir: str):
    reports, combined = onboard_providers(config_dir, write_outputs=False)
    assert combined.total_providers == len(reports) == 3
    tally = (
        combined.ready_for_auto_deploy
        + combined.ready_with_minor_review
        + combined.needs_mapping_review
        + combined.blocked
    )
    assert tally == 3
    assert {e.provider_id for e in combined.providers} == {
        "northlake_university",
        "redwood_college",
        "pacific_state_university",
    }


def test_onboard_providers_writes_outputs(config_dir: str, tmp_path):
    combined_out = tmp_path / "combined.json"
    reports, _ = onboard_providers(
        config_dir, write_outputs=True, combined_out=str(combined_out)
    )
    assert combined_out.is_file()
    # Each provider writes its own readiness report into its configured output dir.
    for report in reports:
        cfg = load_onboarding_config(
            os.path.join(config_dir, f"{report.provider_id}.yml")
        )
        assert cfg.output_dir is not None
        out = os.path.join(cfg.output_dir, f"{report.provider_id}_readiness.json")
        assert os.path.isfile(out)


def test_onboard_providers_empty_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        onboard_providers(str(tmp_path))


# --- end-to-end orchestrator: retail example (same engine, new domain) ----


def test_onboard_brightmart_ready(retail_config_dir: str):
    report = onboard_provider(
        os.path.join(retail_config_dir, "brightmart_distribution.yml"), write_outputs=False
    )
    assert report.provider_name == "BrightMart Distribution"
    assert report.status == STATUS_READY_AUTO
    assert report.readiness_score >= 90
    assert report.auto_deploy_allowed is True
    assert report.summary.required_fields_covered is True


def test_onboard_coastal_minor_review(retail_config_dir: str):
    """Coastal's sales export lacks the required ordered_at → auto-deploy withheld."""
    report = onboard_provider(
        os.path.join(retail_config_dir, "coastal_goods.yml"), write_outputs=False
    )
    assert report.summary.required_fields_covered is False
    assert report.auto_deploy_allowed is False


def test_onboard_anvil_blocked(retail_config_dir: str):
    report = onboard_provider(
        os.path.join(retail_config_dir, "anvil_hardware.yml"), write_outputs=False
    )
    assert report.status == STATUS_BLOCKED
    assert report.auto_deploy_allowed is False
    assert report.readiness_score < 60


def test_onboard_retail_providers_combined(retail_config_dir: str):
    reports, combined = onboard_providers(retail_config_dir, write_outputs=False)
    assert combined.total_providers == len(reports) == 3
    assert {e.provider_id for e in combined.providers} == {
        "brightmart_distribution",
        "coastal_goods",
        "anvil_hardware",
    }
    # The retail example spans the full spectrum: one of each headline outcome.
    assert combined.ready_for_auto_deploy == 1
    assert combined.blocked == 1
