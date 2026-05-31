"""Validation rule generation + execution tests (§14)."""

from __future__ import annotations

import os

from canoniq.connectors import CSVConnector
from canoniq.matcher.mapping_engine import MappingEngine
from canoniq.profiler import Profiler
from canoniq.registry import load_canonical_schema
from canoniq.validation import generate_validation_rules, validate_records


def _finance_setup(examples_dir):
    base = os.path.join(examples_dir, "finance")
    conn = CSVConnector(os.path.join(base, "source_transactions.csv"))
    records = conn.sample()
    profile = Profiler().profile(records, conn.get_metadata())
    schema = load_canonical_schema(os.path.join(base, "canonical_transaction.yml"))
    mapping = MappingEngine().suggest(profile, schema)
    return records, profile, schema, mapping


def test_rules_only_for_mapped_fields(examples_dir):
    _, profile, schema, mapping = _finance_setup(examples_dir)
    rules = generate_validation_rules(schema, mapping, profile)
    mapped = mapping.approved_mappings(include_review=True).values()
    for r in rules:
        assert r.field in set(mapped)


def test_checksum_rule_generated_for_iban(examples_dir):
    _, profile, schema, mapping = _finance_setup(examples_dir)
    rules = generate_validation_rules(schema, mapping, profile)
    iban_rules = [r for r in rules if r.field == "account_id"]
    assert any(r.rule == "valid_checksum" and r.params.get("format") == "iban" for r in iban_rules)


def test_currency_code_rule_generated(examples_dir):
    _, profile, schema, mapping = _finance_setup(examples_dir)
    rules = generate_validation_rules(schema, mapping, profile)
    assert any(r.field == "amount_currency" and r.rule == "valid_currency_code" for r in rules)


def test_validation_passes_on_clean_canonical_data():
    from canoniq.core.models import ValidationRule

    rules = [
        ValidationRule(field="email", rule="valid_email", severity="error"),
        ValidationRule(field="id", rule="not_null", severity="error"),
    ]
    records = [{"email": "a@b.com", "id": "1"}, {"email": "c@d.org", "id": "2"}]
    report = validate_records(records, rules)
    assert report.passed is True
    assert report.row_count == 2


def test_validation_flags_bad_email_and_missing_required():
    from canoniq.core.models import ValidationRule

    rules = [
        ValidationRule(field="email", rule="valid_email", severity="error"),
        ValidationRule(field="id", rule="not_null", severity="error"),
    ]
    records = [{"email": "not-an-email", "id": ""}]
    report = validate_records(records, rules)
    assert report.passed is False
    failed = {f.rule for f in report.findings if not f.passed}
    assert "valid_email" in failed
    assert "not_null" in failed


def test_range_rule_execution():
    from canoniq.core.models import ValidationRule

    rules = [ValidationRule(field="gpa", rule="range", severity="error", params={"min": 0.0, "max": 4.0})]
    ok = validate_records([{"gpa": "3.5"}], rules)
    assert ok.passed is True
    bad = validate_records([{"gpa": "5.0"}], rules)
    assert bad.passed is False
