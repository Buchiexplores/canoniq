"""Transform source records into canonical output (§15).

Renames mapped columns to canonical names, drops unmapped columns by default, and
coerces values toward canonical types where lossless. Coercion failures are reported,
never silently swallowed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from canoniq.core import constants as C
from canoniq.core.models import CanonicalEntity, MappingResult


@dataclass
class TransformResult:
    records: list[dict[str, Any]]
    columns: list[str]
    coercion_errors: list[dict[str, Any]] = field(default_factory=list)


def _coerce(value: Any, canonical_type: str) -> tuple[Any, bool]:
    """Return (coerced_value, ok). ok=False means coercion failed (value kept as-is)."""
    if value is None or str(value).strip() == "":
        return None, True
    sval = str(value).strip()
    try:
        if canonical_type == C.TYPE_INTEGER:
            return int(float(sval.replace(",", ""))) if "." in sval else int(sval.replace(",", "")), True
        if canonical_type == C.TYPE_DECIMAL:
            return float(sval.replace(",", "")), True
        if canonical_type == C.TYPE_PERCENTAGE:
            return float(sval.rstrip("%").replace(",", "")), True
        if canonical_type == C.TYPE_BOOLEAN:
            low = sval.lower()
            if low in {"true", "yes", "y", "t", "1"}:
                return True, True
            if low in {"false", "no", "n", "f", "0"}:
                return False, True
            return sval, False
        if canonical_type == C.TYPE_CURRENCY_CODE:
            return sval.upper(), True
    except (ValueError, TypeError):
        return sval, False
    return sval, True


def apply_mapping(
    records: list[dict[str, Any]],
    mapping: MappingResult,
    schema: CanonicalEntity | None = None,
    *,
    keep_unmapped: bool = False,
    include_review: bool = False,
) -> TransformResult:
    """Produce canonical records from source records using approved mappings."""
    col_map = mapping.approved_mappings(include_review=include_review)  # source -> canonical

    # Output column order follows the canonical schema when provided, else mapping order.
    if schema is not None:
        canonical_order = [name for name in schema.fields if name in set(col_map.values())]
    else:
        canonical_order = list(dict.fromkeys(col_map.values()))

    types = {name: schema.fields[name].type for name in canonical_order} if schema else {}

    unmapped_cols: list[str] = []
    if keep_unmapped and records:
        mapped_sources = set(col_map)
        for key in records[0].keys():
            if key not in mapped_sources:
                unmapped_cols.append(key)

    out_columns = canonical_order + unmapped_cols
    out_records: list[dict[str, Any]] = []
    coercion_errors: list[dict[str, Any]] = []

    for row_idx, rec in enumerate(records):
        out: dict[str, Any] = {}
        for src, canonical in col_map.items():
            raw = rec.get(src)
            ctype = types.get(canonical)
            if ctype:
                coerced, ok = _coerce(raw, ctype)
                if not ok:
                    coercion_errors.append(
                        {"row": row_idx, "field": canonical, "value": str(raw), "target_type": ctype}
                    )
                out[canonical] = coerced
            else:
                out[canonical] = raw
        if keep_unmapped:
            for col in unmapped_cols:
                out[col] = rec.get(col)
        # ensure stable key order
        out_records.append({c: out.get(c) for c in out_columns})

    return TransformResult(records=out_records, columns=out_columns, coercion_errors=coercion_errors)
