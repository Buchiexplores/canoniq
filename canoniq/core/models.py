"""Pydantic v2 data models for CanonIQ (§8).

All public outputs serialize to stable JSON. Models are configured to forbid
unknown fields at construction time, but canonical-field metadata stays open via
the schema loader (which maps YAML keys explicitly).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SourceFieldProfile(BaseModel):
    """Field-level statistics produced by the profiler."""

    model_config = ConfigDict(extra="forbid")

    name: str
    inferred_type: str
    null_rate: float
    unique_rate: float
    sample_values: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    min: float | None = None
    max: float | None = None
    avg_str_len: float | None = None
    distinct_count: int | None = None
    enum_candidates: list[str] | None = None
    pii_flags: list[str] = Field(default_factory=list)
    position: int | None = None
    declared_type: str | None = None  # native type from connector metadata, when present


class SourceProfile(BaseModel):
    """Structure + statistics for a sampled source dataset."""

    model_config = ConfigDict(extra="forbid")

    source_metadata: dict = Field(default_factory=dict)
    row_count_sampled: int
    fields: list[SourceFieldProfile] = Field(default_factory=list)
    profiler_version: str
    created_at: str
    canoniq_version: str | None = None

    def field(self, name: str) -> SourceFieldProfile | None:
        for f in self.fields:
            if f.name == name:
                return f
        return None


class CanonicalField(BaseModel):
    """A single field in a canonical entity, with production-grade metadata (§9)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    type: str
    required: bool = False
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    min: float | None = None
    max: float | None = None
    enum: list[str] | None = None
    unit: str | None = None
    format: str | None = None
    pii: str | None = None
    standard: dict | None = None
    semantic_tags: list[str] = Field(default_factory=list)


class CanonicalEntity(BaseModel):
    """A versioned canonical model for one entity within a domain."""

    model_config = ConfigDict(extra="forbid")

    domain: str
    entity: str
    version: int
    primary_key: list[str] = Field(default_factory=list)
    standards: list[str] = Field(default_factory=list)
    fields: dict[str, CanonicalField]


class MappingSuggestion(BaseModel):
    """A scored, explained source→canonical proposal."""

    model_config = ConfigDict(extra="forbid")

    source_field: str
    canonical_field: str | None
    confidence: float
    status: str
    reasons: list[str] = Field(default_factory=list)
    signals: dict = Field(default_factory=dict)


class MappingResult(BaseModel):
    """The full mapping output: canonical identity + per-source suggestions."""

    model_config = ConfigDict(extra="forbid")

    canonical: dict  # {domain, entity, version}
    mappings: list[MappingSuggestion] = Field(default_factory=list)
    canoniq_version: str | None = None
    created_at: str | None = None

    def approved_mappings(self, include_review: bool = False) -> dict[str, str]:
        """Return {source_field: canonical_field} for usable mappings."""
        from canoniq.core.constants import (
            STATUS_APPROVED,
            STATUS_AUTO_APPROVED,
            STATUS_REQUIRES_REVIEW,
        )

        usable = {STATUS_AUTO_APPROVED, STATUS_APPROVED}
        if include_review:
            usable.add(STATUS_REQUIRES_REVIEW)
        out: dict[str, str] = {}
        for m in self.mappings:
            if m.canonical_field and m.status in usable:
                out[m.source_field] = m.canonical_field
        return out


class ValidationRule(BaseModel):
    """A validation rule derived from canonical schema + profile."""

    model_config = ConfigDict(extra="forbid")

    field: str
    rule: str
    severity: str
    params: dict = Field(default_factory=dict)


class ValidationFinding(BaseModel):
    """A single rule outcome when a validator runs against data."""

    model_config = ConfigDict(extra="forbid")

    field: str
    rule: str
    severity: str
    passed: bool
    failed_count: int = 0
    message: str | None = None


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    findings: list[ValidationFinding] = Field(default_factory=list)
    row_count: int = 0
    canoniq_version: str | None = None
    created_at: str | None = None


class DriftReport(BaseModel):
    """Divergence between a new source and a prior mapping/schema (§16)."""

    model_config = ConfigDict(extra="forbid")

    status: str
    missing_fields: list[str] = Field(default_factory=list)
    new_fields: list[str] = Field(default_factory=list)
    type_changes: list[dict] = Field(default_factory=list)
    unmapped_required: list[str] = Field(default_factory=list)
    suggested_remappings: list[dict] = Field(default_factory=list)
    created_at: str
    canoniq_version: str | None = None
