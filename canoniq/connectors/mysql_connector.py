"""MySQL source connector (placeholder; planned v0.2/0.3)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class MySQLConnector(PlaceholderConnector):
    """Samples rows from a MySQL table. Requires ``canoniq[databases]``. Planned: v0.2/0.3.

    Implementation plan: connect via SQLAlchemy/PyMySQL using ``${ENV}`` credentials;
    ``sample`` runs ``SELECT * FROM `db`.`table` LIMIT <n>`` with backtick-quoted
    identifiers; ``get_metadata`` reads ``information_schema.columns``.
    """

    source_type = "mysql"
    target_version = "v0.2"
    extra = "databases"
