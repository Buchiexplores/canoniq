"""AI matcher interface (§23)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from canoniq.core.models import CanonicalField, SourceFieldProfile


class BaseAIMatcher(ABC):
    """Optional 6th signal: semantic similarity between a source and canonical field."""

    @abstractmethod
    def semantic_score(
        self, source_field: SourceFieldProfile, canonical_field: CanonicalField
    ) -> float:
        """Return a semantic-similarity score in [0, 1]."""
