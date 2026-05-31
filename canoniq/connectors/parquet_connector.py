"""Parquet source connector (placeholder; planned v0.2)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class ParquetConnector(PlaceholderConnector):
    """Samples rows from a local Parquet file. Requires ``canoniq[files]``. Planned: v0.2.

    Implementation plan: use pyarrow to read row groups lazily and return up to
    ``limit`` records as dicts; expose Arrow schema (names, types, nullability) via
    ``get_metadata`` so the profiler can reconcile declared vs. inferred types.
    """

    source_type = "parquet"
    target_version = "v0.2"
    extra = "files"
