"""Source connector interface (§17).

Connectors are the ONLY place that touches a data source. They return records in
the common internal format ``list[dict[str, Any]]`` plus metadata, so the profiler
and matching engine stay completely source-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseSourceConnector(ABC):
    """Abstract base for every data-access connector."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify the source is reachable."""

    @abstractmethod
    def list_entities(self) -> list[str]:
        """List available tables, files, collections, or entities."""

    @abstractmethod
    def sample(self, entity: str, limit: int = 1000) -> list[dict[str, Any]]:
        """Return a representative sample of records for profiling."""

    @abstractmethod
    def get_metadata(self, entity: str) -> dict[str, Any]:
        """Return source metadata: name, schema, path, format, column types,
        nullability, comments, row-count estimate (when available)."""
