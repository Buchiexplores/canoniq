"""Source-agnostic profiler (§18).

Turns ``records + metadata`` into a ``SourceProfile``. It never cares which connector
produced the records. When the connector supplies native column types, the declared
type is recorded alongside the inferred type.
"""

from __future__ import annotations

from typing import Any

from canoniq import __version__
from canoniq.core.constants import (
    DEFAULT_SAMPLE_VALUES,
    ENUM_CARDINALITY_MAX,
    PROFILER_VERSION,
    TYPE_DECIMAL,
    TYPE_INTEGER,
    TYPE_PERCENTAGE,
)
from canoniq.core.models import SourceFieldProfile, SourceProfile
from canoniq.core.util import now_iso
from canoniq.profiler.base import BaseProfiler
from canoniq.profiler.pattern_detection import detect_patterns
from canoniq.profiler.pii_detection import detect_pii_flags, mask_value, should_mask
from canoniq.profiler.type_inference import infer_column_type

_NUMERIC_TYPES = {TYPE_INTEGER, TYPE_DECIMAL, TYPE_PERCENTAGE}


def _to_number(value: str) -> float | None:
    v = str(value).strip().rstrip("%").replace(",", "")
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


class Profiler(BaseProfiler):
    """Default profiler: computes per-field statistics from sampled records."""

    def __init__(self, *, sample_values: int = DEFAULT_SAMPLE_VALUES, mask_pii: bool = True):
        self.sample_values = sample_values
        self.mask_pii = mask_pii

    def profile(
        self,
        records: list[dict[str, Any]],
        source_metadata: dict[str, Any] | None = None,
    ) -> SourceProfile:
        source_metadata = dict(source_metadata or {})
        declared_types: dict[str, str] = source_metadata.get("column_types", {}) or {}

        # Preserve column order: first-seen order across the sample.
        ordered_names: list[str] = []
        seen: set[str] = set()
        for rec in records:
            for key in rec.keys():
                if key not in seen:
                    seen.add(key)
                    ordered_names.append(key)

        row_count = len(records)
        fields: list[SourceFieldProfile] = []

        for position, name in enumerate(ordered_names):
            raw_values = [rec.get(name) for rec in records]
            string_values = [
                "" if v is None else str(v)
                for v in raw_values
            ]
            non_empty = [v for v in string_values if v.strip() != ""]

            null_count = row_count - len(non_empty)
            null_rate = (null_count / row_count) if row_count else 0.0
            distinct = set(non_empty)
            distinct_count = len(distinct)
            unique_rate = (distinct_count / len(non_empty)) if non_empty else 0.0

            inferred_type = infer_column_type(non_empty)

            numeric_min = numeric_max = None
            avg_str_len = None
            if non_empty:
                avg_str_len = sum(len(v) for v in non_empty) / len(non_empty)
            if inferred_type in _NUMERIC_TYPES:
                numbers = [n for n in (_to_number(v) for v in non_empty) if n is not None]
                if numbers:
                    numeric_min = min(numbers)
                    numeric_max = max(numbers)

            enum_candidates = None
            if 0 < distinct_count <= ENUM_CARDINALITY_MAX and unique_rate < 0.5:
                enum_candidates = sorted(distinct)

            pii_flags = detect_pii_flags(name, non_empty)

            patterns = detect_patterns(
                non_empty,
                null_rate=null_rate,
                unique_rate=unique_rate,
                numeric_min=numeric_min,
                numeric_max=numeric_max,
                distinct_count=distinct_count,
            )

            # Sample values (masked when PII-sensitive and masking enabled).
            sample = non_empty[: self.sample_values]
            if self.mask_pii and should_mask(pii_flags):
                sample = [mask_value(v, pii_flags) for v in sample]

            fields.append(
                SourceFieldProfile(
                    name=name,
                    inferred_type=inferred_type,
                    null_rate=round(null_rate, 4),
                    unique_rate=round(unique_rate, 4),
                    sample_values=sample,
                    patterns=patterns,
                    min=numeric_min,
                    max=numeric_max,
                    avg_str_len=round(avg_str_len, 2) if avg_str_len is not None else None,
                    distinct_count=distinct_count,
                    enum_candidates=enum_candidates,
                    pii_flags=pii_flags,
                    position=position,
                    declared_type=declared_types.get(name),
                )
            )

        return SourceProfile(
            source_metadata=source_metadata,
            row_count_sampled=row_count,
            fields=fields,
            profiler_version=PROFILER_VERSION,
            created_at=now_iso(),
            canoniq_version=__version__,
        )
