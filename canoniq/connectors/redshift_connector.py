"""Amazon Redshift source connector (placeholder; planned v0.3)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class RedshiftConnector(PlaceholderConnector):
    """Samples rows from a Redshift table. Requires ``canoniq[databases]``. Planned: v0.3.

    Implementation plan: connect via SQLAlchemy/psycopg2 using ``${ENV}`` credentials;
    ``sample`` runs ``SELECT * FROM <schema>.<table> LIMIT <n>``; ``get_metadata`` reads
    ``svv_columns`` / ``information_schema.columns`` for declared types.
    """

    source_type = "redshift"
    target_version = "v0.3"
    extra = "databases"
