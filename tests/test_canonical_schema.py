"""Canonical schema loader tests (§9)."""

from __future__ import annotations

import os

import pytest

from canoniq.registry import load_canonical_schema
from canoniq.registry.canonical_schema import CanonicalSchemaError


def test_loads_student_schema(examples_dir):
    schema = load_canonical_schema(
        os.path.join(examples_dir, "higher_ed", "canonical_student.yml")
    )
    assert schema.domain == "higher_ed"
    assert schema.entity == "student"
    assert schema.version == 1
    assert schema.primary_key == ["student_id"]
    assert "student_id" in schema.fields
    assert schema.fields["email"].type == "email"
    assert schema.fields["email"].pii == "moderate"
    assert "banner_id" in schema.fields["student_id"].aliases


def test_missing_file_raises(tmp_path):
    with pytest.raises(CanonicalSchemaError):
        load_canonical_schema(str(tmp_path / "nope.yml"))


def test_unknown_type_rejected(tmp_path):
    p = tmp_path / "bad.yml"
    p.write_text(
        "domain: d\nentity: e\nversion: 1\nfields:\n  x:\n    type: not_a_type\n"
    )
    with pytest.raises(CanonicalSchemaError):
        load_canonical_schema(str(p))


def test_invalid_pii_level_rejected(tmp_path):
    p = tmp_path / "bad.yml"
    p.write_text(
        "domain: d\nentity: e\nversion: 1\nfields:\n  x:\n    type: string\n    pii: super_secret\n"
    )
    with pytest.raises(CanonicalSchemaError):
        load_canonical_schema(str(p))


def test_primary_key_must_reference_known_field(tmp_path):
    p = tmp_path / "bad.yml"
    p.write_text(
        "domain: d\nentity: e\nversion: 1\nprimary_key: [ghost]\n"
        "fields:\n  x:\n    type: string\n"
    )
    with pytest.raises(CanonicalSchemaError):
        load_canonical_schema(str(p))
