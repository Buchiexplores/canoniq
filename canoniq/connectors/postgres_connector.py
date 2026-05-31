"""PostgreSQL source connector (placeholder; planned v0.2/0.3)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class PostgresConnector(PlaceholderConnector):
    """Samples rows from a PostgreSQL table. Requires ``canoniq[databases]``. Planned: v0.2/0.3.

    Implementation plan: connect via SQLAlchemy/psycopg2 using ``${ENV}``-interpolated
    credentials; ``sample`` runs ``SELECT * FROM <schema>.<table> LIMIT <n>`` with safely
    quoted identifiers; ``get_metadata`` reads ``information_schema.columns`` for declared
    types, nullability, and comments to assist type-aware matching.
    """

    source_type = "postgres"
    target_version = "v0.2"
    extra = "databases"
