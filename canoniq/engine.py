"""CanonIQ SDK facade (§22).

Local-first by default — no network access unless an external AI adapter is explicitly
configured. The CLI is built on top of this same engine.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any

from canoniq.ai.base import BaseAIMatcher
from canoniq.ai.registry import build_ai_matcher
from canoniq.config import CanonIQConfig
from canoniq.connectors import CSVConnector, JSONConnector, JSONLConnector
from canoniq.core.models import (
    CanonicalEntity,
    DriftReport,
    MappingResult,
    SourceProfile,
    ValidationReport,
    ValidationRule,
)
from canoniq.drift.drift_detector import detect_drift
from canoniq.matcher.mapping_engine import MappingEngine
from canoniq.profiler import Profiler
from canoniq.registry import load_canonical_schema
from canoniq.sources import build_connector, load_source_config
from canoniq.transform import TransformResult, apply_mapping
from canoniq.validation import generate_validation_rules, validate_records


class CanonIQ:
    """High-level engine. Wraps connectors, profiler, matcher, validation, transform, drift."""

    def __init__(
        self,
        config: CanonIQConfig | None = None,
        ai_matcher: BaseAIMatcher | None = None,
    ):
        self.config = config or CanonIQConfig()
        # Build the semantic matcher from config when one isn't supplied explicitly.
        # An explicit ``ai_matcher`` always wins. When a configured adapter is enabled
        # we also turn on the semantic weight (without mutating the caller's config),
        # otherwise the signal would be computed but never contribute.
        if ai_matcher is None and self.config.ai.enabled:
            ai_matcher = build_ai_matcher(self.config.ai)
            if self.config.weights.get("semantic", 0.0) <= 0.0:
                new_weights = dict(self.config.weights)
                new_weights["semantic"] = self.config.ai.weight
                self.config = self.config.with_overrides(weights=new_weights)
        self.ai_matcher = ai_matcher
        self.profiler = Profiler(
            sample_values=self.config.sample_values, mask_pii=self.config.mask_pii
        )
        self.mapping_engine = MappingEngine(config=self.config, ai_matcher=self.ai_matcher)

    # --- profiling ---------------------------------------------------------

    def profile_records(
        self, records: list[dict[str, Any]], source_metadata: dict[str, Any] | None = None
    ) -> SourceProfile:
        return self.profiler.profile(records, source_metadata or {"type": "records"})

    def profile_csv(self, path: str, limit: int | None = None) -> SourceProfile:
        conn = CSVConnector(path)
        records = conn.sample(limit=limit or self.config.sample_limit)
        return self.profiler.profile(records, conn.get_metadata())

    def profile_json(self, path: str, limit: int | None = None) -> SourceProfile:
        conn = JSONConnector(path)
        records = conn.sample(limit=limit or self.config.sample_limit)
        return self.profiler.profile(records, conn.get_metadata())

    def profile_jsonl(self, path: str, limit: int | None = None) -> SourceProfile:
        conn = JSONLConnector(path)
        records = conn.sample(limit=limit or self.config.sample_limit)
        return self.profiler.profile(records, conn.get_metadata())

    def profile_source_config(self, config_path: str) -> SourceProfile:
        source = load_source_config(config_path)
        connector, resolved = build_connector(source)
        entity = resolved.get("entity", "default")
        limit = int(resolved.get("sample_limit", self.config.sample_limit))
        records = connector.sample(entity=entity, limit=limit)
        metadata = connector.get_metadata(entity)
        return self.profiler.profile(records, metadata)

    def profile_source(self, path: str, limit: int | None = None) -> SourceProfile:
        """Profile a file, dispatching on extension."""
        ext = os.path.splitext(path)[1].lower()
        if ext == ".csv":
            return self.profile_csv(path, limit)
        if ext == ".json":
            return self.profile_json(path, limit)
        if ext in {".jsonl", ".ndjson"}:
            return self.profile_jsonl(path, limit)
        raise ValueError(f"Unsupported file extension {ext!r}. Use --source-config for other types.")

    # --- mapping -----------------------------------------------------------

    def load_schema(self, canonical_schema_path: str) -> CanonicalEntity:
        return load_canonical_schema(canonical_schema_path)

    def suggest_mappings(
        self, profile: SourceProfile, canonical_schema_path: str
    ) -> MappingResult:
        schema = load_canonical_schema(canonical_schema_path)
        return self.mapping_engine.suggest(profile, schema)

    # --- validation --------------------------------------------------------

    def generate_validation_rules(
        self,
        suggestions: MappingResult,
        canonical_schema_path: str,
        profile: SourceProfile | None = None,
    ) -> list[ValidationRule]:
        schema = load_canonical_schema(canonical_schema_path)
        return generate_validation_rules(schema, suggestions, profile)

    def validate(
        self, records: list[dict[str, Any]], rules: list[ValidationRule]
    ) -> ValidationReport:
        return validate_records(records, rules)

    # --- transform ---------------------------------------------------------

    def apply_mapping(
        self,
        source_path: str,
        mapping: MappingResult,
        canonical_schema_path: str | None = None,
        *,
        keep_unmapped: bool = False,
        include_review: bool = False,
        limit: int | None = None,
    ) -> TransformResult:
        records = self._read_records(source_path, limit)
        schema = load_canonical_schema(canonical_schema_path) if canonical_schema_path else None
        return apply_mapping(
            records,
            mapping,
            schema,
            keep_unmapped=keep_unmapped,
            include_review=include_review,
        )

    # --- drift -------------------------------------------------------------

    def detect_drift(
        self,
        source_path: str,
        previous_mapping: MappingResult,
        canonical_schema_path: str,
        limit: int | None = None,
    ) -> DriftReport:
        new_profile = self.profile_source(source_path, limit)
        schema = load_canonical_schema(canonical_schema_path)
        return detect_drift(new_profile, previous_mapping, schema, self.mapping_engine)

    # --- helpers -----------------------------------------------------------

    def _read_records(self, path: str, limit: int | None = None) -> list[dict[str, Any]]:
        ext = os.path.splitext(path)[1].lower()
        n = limit or self.config.sample_limit
        if ext == ".csv":
            return CSVConnector(path).sample(limit=n)
        if ext == ".json":
            return JSONConnector(path).sample(limit=n)
        if ext in {".jsonl", ".ndjson"}:
            return JSONLConnector(path).sample(limit=n)
        raise ValueError(f"Unsupported file extension {ext!r}.")

    @staticmethod
    def write_canonical_csv(result: TransformResult, path: str) -> None:
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=result.columns)
            writer.writeheader()
            for rec in result.records:
                writer.writerow({k: ("" if v is None else v) for k, v in rec.items()})

    @staticmethod
    def write_json(obj: Any, path: str) -> None:
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        payload = obj.model_dump() if hasattr(obj, "model_dump") else obj
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.write("\n")
