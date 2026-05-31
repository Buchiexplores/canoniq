"""Default local, no-op AI matcher (§23).

Returns 0.0 and makes no external calls. Enabling a real adapter (e.g. local
sentence-transformers, or a hosted provider via an extra) is the only path by which
data could leave the machine, and is strictly opt-in.
"""

from __future__ import annotations

from canoniq.ai.base import BaseAIMatcher
from canoniq.core.models import CanonicalField, SourceFieldProfile


class NoOpAIMatcher(BaseAIMatcher):
    """No-op semantic matcher. Always returns 0.0; never contacts the network."""

    def semantic_score(
        self, source_field: SourceFieldProfile, canonical_field: CanonicalField
    ) -> float:
        return 0.0
