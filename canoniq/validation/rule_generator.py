"""Generate validation rules from canonical schema + source profile (§14)."""

from __future__ import annotations

import os

import yaml

from canoniq.core import constants as C
from canoniq.core.models import (
    CanonicalEntity,
    MappingResult,
    SourceProfile,
    ValidationRule,
)
from canoniq.validation.formats import CHECKSUM_FORMATS

_NUMERIC = {C.TYPE_INTEGER, C.TYPE_DECIMAL, C.TYPE_PERCENTAGE}


def generate_validation_rules(
    schema: CanonicalEntity,
    mapping: MappingResult,
    profile: SourceProfile | None = None,
) -> list[ValidationRule]:
    """Derive validation rules for canonical fields that are actually mapped."""
    mapped_fields = {
        m.canonical_field
        for m in mapping.mappings
        if m.canonical_field and m.status in {C.STATUS_AUTO_APPROVED, C.STATUS_APPROVED, C.STATUS_REQUIRES_REVIEW}
    }
    # source field that feeds each canonical field (to look up profile stats)
    source_for_canonical = {
        m.canonical_field: m.source_field
        for m in mapping.mappings
        if m.canonical_field
    }

    rules: list[ValidationRule] = []

    def profile_field(canonical_name: str):
        if profile is None:
            return None
        src = source_for_canonical.get(canonical_name)
        return profile.field(src) if src else None

    for name, field in schema.fields.items():
        if name not in mapped_fields:
            continue

        if field.required:
            rules.append(ValidationRule(field=name, rule="not_null", severity="error"))

        fmt = field.format
        if field.type == C.TYPE_EMAIL or fmt == "email":
            rules.append(ValidationRule(field=name, rule="valid_email", severity="error"))
        elif fmt in {"iso8601"} or field.type in {C.TYPE_DATE, C.TYPE_TIMESTAMP} or fmt == "date":
            rules.append(
                ValidationRule(
                    field=name,
                    rule="valid_datetime",
                    severity="error",
                    params={"format": fmt or ("date" if field.type == C.TYPE_DATE else "iso8601")},
                )
            )

        if fmt == "iso4217" or field.type == C.TYPE_CURRENCY_CODE:
            rules.append(ValidationRule(field=name, rule="valid_currency_code", severity="error"))
        elif fmt in CHECKSUM_FORMATS:
            rules.append(
                ValidationRule(field=name, rule="valid_checksum", severity="error", params={"format": fmt})
            )
        elif fmt and fmt not in {"date", "iso8601", "email"}:
            rules.append(
                ValidationRule(field=name, rule="valid_format", severity="error", params={"format": fmt})
            )

        if field.type in _NUMERIC and (field.min is not None or field.max is not None):
            params: dict = {}
            if field.min is not None:
                params["min"] = field.min
            if field.max is not None:
                params["max"] = field.max
            rules.append(ValidationRule(field=name, rule="range", severity="error", params=params))

        if field.enum:
            rules.append(
                ValidationRule(
                    field=name, rule="allowed_values", severity="error", params={"values": list(field.enum)}
                )
            )

        pf = profile_field(name)
        if pf is not None:
            if "identifier" in field.semantic_tags and C.PATTERN_MOSTLY_UNIQUE in pf.patterns:
                rules.append(ValidationRule(field=name, rule="unique", severity="warning"))
            if field.required and C.PATTERN_HIGH_NULL_RATE in pf.patterns:
                rules.append(
                    ValidationRule(field=name, rule="unexpected_nulls", severity="warning")
                )

        if field.pii in {"high", "phi"}:
            rules.append(ValidationRule(field=name, rule="pii_present", severity="info"))

    return rules


def save_rules(rules: list[ValidationRule], path: str, *, canoniq_version: str | None = None) -> None:
    """Serialize rules to a YAML file grouped by field (§20 contract)."""
    from canoniq.core.util import now_iso

    grouped: dict[str, list[dict]] = {}
    for r in rules:
        grouped.setdefault(r.field, []).append(
            {"rule": r.rule, "severity": r.severity, **({"params": r.params} if r.params else {})}
        )
    doc = {
        "canoniq_version": canoniq_version,
        "created_at": now_iso(),
        "rules": grouped,
    }
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(doc, fh, sort_keys=False, default_flow_style=False)
