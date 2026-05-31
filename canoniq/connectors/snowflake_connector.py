"""Snowflake source connector (placeholder; planned v0.3)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class SnowflakeConnector(PlaceholderConnector):
    """Samples rows from a Snowflake table. Requires ``canoniq[snowflake]``. Planned: v0.3.

    Implementation plan: use ``snowflake-connector-python`` with ``${ENV}`` credentials;
    ``sample`` runs ``SELECT * FROM <db>.<schema>.<table> LIMIT <n>``; ``get_metadata``
    reads ``INFORMATION_SCHEMA.COLUMNS`` for declared types and nullability.
    """

    source_type = "snowflake"
    target_version = "v0.3"
    extra = "snowflake"
