"""Compare a new source profile against a previous mapping + canonical schema (§16)."""

from __future__ import annotations

from canoniq import __version__
from canoniq.core.constants import (
    STATUS_APPROVED,
    STATUS_AUTO_APPROVED,
    STATUS_REQUIRES_REVIEW,
)
from canoniq.core.models import (
    CanonicalEntity,
    DriftReport,
    MappingResult,
    SourceProfile,
)
from canoniq.core.util import now_iso
from canoniq.matcher.mapping_engine import MappingEngine


def detect_drift(
    new_profile: SourceProfile,
    previous_mapping: MappingResult,
    schema: CanonicalEntity,
    engine: MappingEngine | None = None,
) -> DriftReport:
    """Detect missing/new/type-changed fields, unmapped required fields, and remaps."""
    engine = engine or MappingEngine()

    # Previously known source fields and their inferred types (from prior mapping signals
    # we don't have types, so recompute by re-mapping the new profile for type comparison).
    prev_source_fields = {m.source_field for m in previous_mapping.mappings}
    prev_mapped = {
        m.source_field: m.canonical_field
        for m in previous_mapping.mappings
        if m.canonical_field
        and m.status in {STATUS_AUTO_APPROVED, STATUS_APPROVED, STATUS_REQUIRES_REVIEW}
    }

    new_fields_set = {f.name for f in new_profile.fields}
    new_types = {f.name: f.inferred_type for f in new_profile.fields}

    missing_fields = sorted(prev_source_fields - new_fields_set)
    new_fields = sorted(new_fields_set - prev_source_fields)

    # Type changes: we only have prior signals, not prior types. Compare prior mapped
    # source fields that still exist — re-mapping gives current type via profile.
    # We approximate prior type as unknown; report change only when a prior signal
    # recorded a type. Since the prior mapping stores signals, surface explicit changes
    # by re-running suggestion on the new profile and comparing the matched canonical.
    type_changes: list[dict] = []
    prev_types = {
        m.source_field: m.signals.get("_inferred_type")
        for m in previous_mapping.mappings
        if m.signals.get("_inferred_type")
    }
    for name in prev_source_fields & new_fields_set:
        old_t = prev_types.get(name)
        if old_t and old_t != new_types.get(name):
            type_changes.append({"field": name, "old_type": old_t, "new_type": new_types[name]})

    # Required canonical fields no longer mapped.
    new_result = engine.suggest(new_profile, schema)
    now_mapped_canonical = {
        m.canonical_field
        for m in new_result.mappings
        if m.canonical_field
        and m.status in {STATUS_AUTO_APPROVED, STATUS_APPROVED, STATUS_REQUIRES_REVIEW}
    }
    required = {name for name, f in schema.fields.items() if f.required}
    unmapped_required = sorted(required - now_mapped_canonical)

    # Suggested remappings: new source fields that now map (≥ review) to a canonical
    # field that was previously mapped by a now-missing source field (orphaned).
    orphaned_canonical = {
        prev_mapped[src] for src in missing_fields if src in prev_mapped
    }
    suggested_remappings: list[dict] = []
    for m in new_result.mappings:
        if (
            m.source_field in new_fields
            and m.canonical_field
            and m.canonical_field in orphaned_canonical
            and m.status in {STATUS_AUTO_APPROVED, STATUS_REQUIRES_REVIEW}
        ):
            suggested_remappings.append(
                {
                    "source_field": m.source_field,
                    "canonical_field": m.canonical_field,
                    "confidence": m.confidence,
                }
            )

    drifted = bool(
        missing_fields or new_fields or type_changes or unmapped_required
    )
    return DriftReport(
        status="drift_detected" if drifted else "no_drift",
        missing_fields=missing_fields,
        new_fields=new_fields,
        type_changes=type_changes,
        unmapped_required=unmapped_required,
        suggested_remappings=suggested_remappings,
        created_at=now_iso(),
        canoniq_version=__version__,
    )
