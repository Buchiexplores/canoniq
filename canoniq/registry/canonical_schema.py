"""Canonical-schema YAML loader + validation (§9).

Supports the production-grade format: ``domain``, ``entity``, ``version``, optional
``primary_key`` / ``standards``, and per-field metadata (type, required, description,
aliases, min, max, enum, unit, format, pii, standard, semantic_tags).
"""

from __future__ import annotations

import os
from typing import Any

import yaml

from canoniq.core.constants import CANONICAL_TYPES, PII_LEVELS
from canoniq.core.models import CanonicalEntity, CanonicalField

_REQUIRED_TOP_KEYS = ("domain", "entity", "version", "fields")


class CanonicalSchemaError(ValueError):
    """Raised when a canonical schema file is malformed."""


def _coerce_field(name: str, spec: dict[str, Any]) -> CanonicalField:
    if not isinstance(spec, dict):
        raise CanonicalSchemaError(f"Field {name!r} must be a mapping, got {type(spec).__name__}.")
    ftype = spec.get("type")
    if ftype is None:
        raise CanonicalSchemaError(f"Field {name!r} is missing required key 'type'.")
    if ftype not in CANONICAL_TYPES:
        raise CanonicalSchemaError(
            f"Field {name!r} has unknown type {ftype!r}. Allowed: {', '.join(CANONICAL_TYPES)}."
        )
    pii = spec.get("pii")
    if pii is not None and pii not in PII_LEVELS:
        raise CanonicalSchemaError(
            f"Field {name!r} has invalid pii level {pii!r}. Allowed: {', '.join(PII_LEVELS)}."
        )
    try:
        return CanonicalField(name=name, **spec)
    except TypeError as exc:
        raise CanonicalSchemaError(f"Field {name!r}: {exc}") from exc


def load_canonical_schema(path: str) -> CanonicalEntity:
    """Load a canonical schema YAML file into a validated ``CanonicalEntity``."""
    if not os.path.isfile(path):
        raise CanonicalSchemaError(f"Canonical schema not found: {path}")
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict):
        raise CanonicalSchemaError("Canonical schema must be a YAML mapping.")
    for key in _REQUIRED_TOP_KEYS:
        if key not in doc:
            raise CanonicalSchemaError(f"Canonical schema missing required key {key!r}.")

    raw_fields = doc["fields"]
    if not isinstance(raw_fields, dict) or not raw_fields:
        raise CanonicalSchemaError("'fields' must be a non-empty mapping.")

    fields = {name: _coerce_field(name, spec) for name, spec in raw_fields.items()}

    primary_key = doc.get("primary_key", []) or []
    for pk in primary_key:
        if pk not in fields:
            raise CanonicalSchemaError(f"primary_key references unknown field {pk!r}.")

    try:
        return CanonicalEntity(
            domain=str(doc["domain"]),
            entity=str(doc["entity"]),
            version=int(doc["version"]),
            primary_key=list(primary_key),
            standards=list(doc.get("standards", []) or []),
            fields=fields,
        )
    except (TypeError, ValueError) as exc:
        raise CanonicalSchemaError(f"Invalid canonical schema: {exc}") from exc
