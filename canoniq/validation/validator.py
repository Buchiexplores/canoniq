"""Apply validation rules to canonical records and produce a report (§14)."""

from __future__ import annotations

from typing import Any

from canoniq import __version__
from canoniq.core.models import ValidationFinding, ValidationReport, ValidationRule
from canoniq.core.util import now_iso
from canoniq.validation.formats import is_date, is_email, is_iso8601, validate_format


def _non_empty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _check_row(rule: ValidationRule, value: Any) -> bool:
    """Return True if the value passes the rule. Empty values pass non-null-specific rules."""
    present = _non_empty(value)
    sval = str(value).strip() if present else ""

    if rule.rule == "not_null":
        return present
    if not present:
        # Other rules only apply to present values.
        return True
    if rule.rule == "valid_email":
        return is_email(sval)
    if rule.rule == "valid_datetime":
        fmt = rule.params.get("format", "iso8601")
        return is_date(sval) if fmt == "date" else is_iso8601(sval)
    if rule.rule == "valid_currency_code":
        return validate_format("iso4217", sval)
    if rule.rule in {"valid_checksum", "valid_format"}:
        return validate_format(rule.params.get("format", ""), sval)
    if rule.rule == "range":
        try:
            num = float(sval.rstrip("%").replace(",", ""))
        except ValueError:
            return False
        if "min" in rule.params and num < float(rule.params["min"]):
            return False
        if "max" in rule.params and num > float(rule.params["max"]):
            return False
        return True
    if rule.rule == "allowed_values":
        return sval in {str(v) for v in rule.params.get("values", [])}
    # advisory rules always "pass" (they don't fail a dataset)
    return True


def validate_records(
    records: list[dict[str, Any]], rules: list[ValidationRule]
) -> ValidationReport:
    """Run rules against canonical records (keyed by canonical field name)."""
    findings: list[ValidationFinding] = []
    overall_pass = True

    advisory = {"pii_present"}
    uniqueness_rules = {"unique"}

    for rule in rules:
        if rule.rule in advisory:
            findings.append(
                ValidationFinding(
                    field=rule.field, rule=rule.rule, severity=rule.severity, passed=True,
                    message="advisory",
                )
            )
            continue

        if rule.rule in uniqueness_rules:
            seen: dict[str, int] = {}
            for rec in records:
                v = rec.get(rule.field)
                if _non_empty(v):
                    seen[str(v)] = seen.get(str(v), 0) + 1
            dupes = sum(c - 1 for c in seen.values() if c > 1)
            passed = dupes == 0
            findings.append(
                ValidationFinding(
                    field=rule.field, rule=rule.rule, severity=rule.severity,
                    passed=passed, failed_count=dupes,
                    message=None if passed else f"{dupes} duplicate value(s)",
                )
            )
            if not passed and rule.severity == "error":
                overall_pass = False
            continue

        if rule.rule == "unexpected_nulls":
            nulls = sum(1 for rec in records if not _non_empty(rec.get(rule.field)))
            passed = nulls == 0
            findings.append(
                ValidationFinding(
                    field=rule.field, rule=rule.rule, severity=rule.severity,
                    passed=passed, failed_count=nulls,
                    message=None if passed else f"{nulls} null value(s)",
                )
            )
            continue

        failed = 0
        for rec in records:
            if not _check_row(rule, rec.get(rule.field)):
                failed += 1
        passed = failed == 0
        if not passed and rule.severity == "error":
            overall_pass = False
        findings.append(
            ValidationFinding(
                field=rule.field, rule=rule.rule, severity=rule.severity,
                passed=passed, failed_count=failed,
                message=None if passed else f"{failed} row(s) failed {rule.rule}",
            )
        )

    return ValidationReport(
        passed=overall_pass,
        findings=findings,
        row_count=len(records),
        canoniq_version=__version__,
        created_at=now_iso(),
    )
