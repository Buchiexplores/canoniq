"""Core data models and constants.

The Pydantic models below are CanonIQ's public data types — the objects the
:class:`~canoniq.engine.CanonIQ` facade returns and accepts. They are re-exported
here so callers can ``from canoniq.core import MappingResult, ValidationReport``
without reaching into submodules. All models forbid unknown fields and serialize to
stable JSON.
"""

from __future__ import annotations

from canoniq.core.models import (
    CanonicalEntity,
    CanonicalField,
    DriftReport,
    MappingResult,
    MappingSuggestion,
    SourceFieldProfile,
    SourceProfile,
    ValidationFinding,
    ValidationReport,
    ValidationRule,
)

__all__ = [
    "SourceFieldProfile",
    "SourceProfile",
    "CanonicalField",
    "CanonicalEntity",
    "MappingSuggestion",
    "MappingResult",
    "ValidationRule",
    "ValidationFinding",
    "ValidationReport",
    "DriftReport",
]
