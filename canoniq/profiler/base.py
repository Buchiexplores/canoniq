"""Profiler interface (§18)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from canoniq.core.models import SourceProfile


class BaseProfiler(ABC):
    @abstractmethod
    def profile(
        self,
        records: list[dict[str, Any]],
        source_metadata: dict[str, Any],
    ) -> SourceProfile:
        """Profile records into field-level statistics."""
