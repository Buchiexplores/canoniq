"""Drift detection tests: missing/new/type-change/unmapped-required/remap (§16)."""

from __future__ import annotations

import os

from canoniq.connectors import CSVConnector
from canoniq.drift.drift_detector import detect_drift
from canoniq.matcher.mapping_engine import MappingEngine
from canoniq.profiler import Profiler
from canoniq.registry import load_canonical_schema


def _profile_csv(path):
    conn = CSVConnector(path)
    return Profiler().profile(conn.sample(), conn.get_metadata())


def _higher_ed_drift(examples_dir):
    base = os.path.join(examples_dir, "higher_ed")
    schema = load_canonical_schema(os.path.join(base, "canonical_student.yml"))
    engine = MappingEngine()
    old_profile = _profile_csv(os.path.join(base, "source_students.csv"))
    old_mapping = engine.suggest(old_profile, schema)
    new_profile = _profile_csv(os.path.join(base, "new_source_students.csv"))
    return detect_drift(new_profile, old_mapping, schema, engine), schema


def test_detects_drift_status(examples_dir):
    report, _ = _higher_ed_drift(examples_dir)
    assert report.status == "drift_detected"


def test_missing_field_detected(examples_dir):
    # new_source renames banner_id -> student_number and drops status
    report, _ = _higher_ed_drift(examples_dir)
    assert "banner_id" in report.missing_fields
    assert "status" in report.missing_fields


def test_new_field_detected(examples_dir):
    report, _ = _higher_ed_drift(examples_dir)
    assert "student_number" in report.new_fields
    assert "program_code" in report.new_fields


def test_no_drift_when_profile_unchanged(examples_dir):
    base = os.path.join(examples_dir, "higher_ed")
    schema = load_canonical_schema(os.path.join(base, "canonical_student.yml"))
    engine = MappingEngine()
    profile = _profile_csv(os.path.join(base, "source_students.csv"))
    mapping = engine.suggest(profile, schema)
    report = detect_drift(profile, mapping, schema, engine)
    assert report.status == "no_drift"
    assert report.missing_fields == []
    assert report.new_fields == []


def test_type_change_detected():
    from canoniq.core.models import (
        CanonicalEntity,
        CanonicalField,
        MappingResult,
        MappingSuggestion,
    )

    schema = CanonicalEntity(
        domain="d", entity="e", version=1, primary_key=["id"],
        fields={"id": CanonicalField(name="id", type="string", aliases=["uid"])},
    )
    # prior mapping recorded uid as integer
    old_mapping = MappingResult(
        canonical={"domain": "d", "entity": "e", "version": 1},
        mappings=[
            MappingSuggestion(
                source_field="uid", canonical_field="id", confidence=1.0,
                status="auto_approved", signals={"_inferred_type": "integer"},
            )
        ],
    )
    new_profile = Profiler().profile([{"uid": "abc-123"}, {"uid": "def-456"}], {"type": "records"})
    report = detect_drift(new_profile, old_mapping, schema, MappingEngine())
    changes = {c["field"]: c for c in report.type_changes}
    assert "uid" in changes
    assert changes["uid"]["old_type"] == "integer"
