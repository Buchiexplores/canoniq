"""Mapping engine tests: scoring, gating, one-to-one assignment, determinism (§13)."""

from __future__ import annotations

import os

from canoniq.connectors import CSVConnector
from canoniq.core.constants import STATUS_UNMAPPED
from canoniq.matcher.mapping_engine import MappingEngine
from canoniq.profiler import Profiler
from canoniq.registry import load_canonical_schema


def _student_mapping(examples_dir):
    base = os.path.join(examples_dir, "higher_ed")
    conn = CSVConnector(os.path.join(base, "source_students.csv"))
    profile = Profiler().profile(conn.sample(), conn.get_metadata())
    schema = load_canonical_schema(os.path.join(base, "canonical_student.yml"))
    return MappingEngine().suggest(profile, schema), profile, schema


def test_alias_match_auto_approves_banner_id(examples_dir):
    result, _, _ = _student_mapping(examples_dir)
    by_src = {m.source_field: m for m in result.mappings}
    assert by_src["banner_id"].canonical_field == "student_id"
    assert by_src["banner_id"].status == "auto_approved"
    assert by_src["banner_id"].confidence >= 0.90


def test_each_canonical_claimed_once(examples_dir):
    result, _, _ = _student_mapping(examples_dir)
    claimed = [m.canonical_field for m in result.mappings if m.canonical_field]
    assert len(claimed) == len(set(claimed))


def test_suggestions_in_source_order(examples_dir):
    result, profile, _ = _student_mapping(examples_dir)
    assert [m.source_field for m in result.mappings] == [f.name for f in profile.fields]


def test_determinism(examples_dir):
    r1, profile, schema = _student_mapping(examples_dir)
    r2 = MappingEngine().suggest(profile, schema)
    assert [(m.source_field, m.canonical_field, m.confidence) for m in r1.mappings] == [
        (m.source_field, m.canonical_field, m.confidence) for m in r2.mappings
    ]


def test_unmatched_field_is_unmapped(examples_dir):
    base = os.path.join(examples_dir, "higher_ed")
    schema = load_canonical_schema(os.path.join(base, "canonical_student.yml"))
    profile = Profiler().profile(
        [{"banner_id": "B1", "totally_unrelated_xyzzy": "qwerty"}],
        {"type": "records"},
    )
    result = MappingEngine().suggest(profile, schema)
    by_src = {m.source_field: m for m in result.mappings}
    assert by_src["totally_unrelated_xyzzy"].status == STATUS_UNMAPPED
    assert by_src["totally_unrelated_xyzzy"].canonical_field is None


def test_signals_include_inferred_type(examples_dir):
    result, _, _ = _student_mapping(examples_dir)
    for m in result.mappings:
        assert "_inferred_type" in m.signals
