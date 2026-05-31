"""Shared helpers for semantic matchers (§23).

Centralizes how a field becomes the *text* an embedding model sees, and how two
embeddings become a unit-interval score. Keeping this in one place guarantees every
adapter (local or cloud) sends the same minimal, PII-safe text: source field *names*
and canonical schema metadata only — never sample values.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from canoniq.core.models import CanonicalField, SourceFieldProfile


def source_text(field: SourceFieldProfile) -> str:
    """Text representation of a source field. Uses the name only (no sample values)."""
    return field.name.replace("_", " ").strip()


def canonical_text(field: CanonicalField) -> str:
    """Text representation of a canonical field: name, aliases, tags, description."""
    parts = [field.name.replace("_", " ")]
    parts.extend(field.aliases)
    parts.extend(field.semantic_tags)
    if field.description:
        parts.append(field.description)
    return " ".join(p for p in parts if p).strip()


def cosine_to_unit(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity of two vectors, mapped from [-1, 1] to [0, 1].

    Returns 0.0 for a zero-magnitude vector so the signal composes safely.
    """
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    cosine = dot / (norm_a * norm_b)
    return max(0.0, min(1.0, (cosine + 1.0) / 2.0))
