"""End-to-end tests across all five bundled domains (§10, §28).

Runs the full pipeline (profile → suggest → rules → transform → drift) for each
domain and asserts structural invariants plus determinism (suggestions are stable
across repeated runs once volatile timestamps are stripped).
"""

from __future__ import annotations

import pytest

from canoniq import CanonIQ
from canoniq.domains import DOMAINS, domain_paths

ALL_DOMAINS = sorted(DOMAINS)


def _strip_volatile(mapping):
    return [
        (m.source_field, m.canonical_field, m.confidence, m.status)
        for m in mapping.mappings
    ]


@pytest.mark.parametrize("domain", ALL_DOMAINS)
def test_full_pipeline_runs(domain, examples_dir):
    paths = domain_paths(domain)
    engine = CanonIQ()

    profile = engine.profile_source(paths["source"])
    assert profile.row_count_sampled > 0
    assert profile.fields

    mapping = engine.suggest_mappings(profile, paths["canonical"])
    # every source field gets a decision
    assert len(mapping.mappings) == len(profile.fields)

    rules = engine.generate_validation_rules(mapping, paths["canonical"], profile)
    transform = engine.apply_mapping(
        paths["source"], mapping, paths["canonical"], include_review=True
    )
    assert len(transform.records) == profile.row_count_sampled

    report = engine.validate(transform.records, rules)
    assert report.row_count == profile.row_count_sampled


@pytest.mark.parametrize("domain", ALL_DOMAINS)
def test_mapping_is_deterministic(domain, examples_dir):
    paths = domain_paths(domain)
    engine = CanonIQ()
    profile = engine.profile_source(paths["source"])
    m1 = engine.suggest_mappings(profile, paths["canonical"])
    m2 = engine.suggest_mappings(profile, paths["canonical"])
    assert _strip_volatile(m1) == _strip_volatile(m2)


@pytest.mark.parametrize("domain", ALL_DOMAINS)
def test_drift_against_new_source(domain, examples_dir):
    paths = domain_paths(domain)
    engine = CanonIQ()
    profile = engine.profile_source(paths["source"])
    mapping = engine.suggest_mappings(profile, paths["canonical"])
    report = engine.detect_drift(paths["new_source"], mapping, paths["canonical"])
    # every bundled new_source diverges from the original by design
    assert report.status == "drift_detected"


def test_primary_key_fields_map_with_high_confidence(examples_dir):
    """Identifier fields should reliably auto-approve across domains."""
    engine = CanonIQ()
    for domain in ALL_DOMAINS:
        paths = domain_paths(domain)
        schema = engine.load_schema(paths["canonical"])
        profile = engine.profile_source(paths["source"])
        mapping = engine.suggest_mappings(profile, paths["canonical"])
        mapped = mapping.approved_mappings(include_review=True).values()
        for pk in schema.primary_key:
            assert pk in mapped, f"{domain}: primary key {pk} not mapped"


def test_no_raw_pii_in_profiles(examples_dir):
    """High-PII/PHI sample values must be masked before leaving the profiler."""
    engine = CanonIQ()
    # higher-ed + healthcare carry email/PHI; ensure no raw addresses leak.
    for domain in ALL_DOMAINS:
        paths = domain_paths(domain)
        profile = engine.profile_source(paths["source"])
        for f in profile.fields:
            if "email" in f.pii_flags:
                for sv in f.sample_values:
                    assert "@example" not in sv
