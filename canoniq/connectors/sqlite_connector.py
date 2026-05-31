"""SQLite source connector (placeholder; planned v0.2)."""

from __future__ import annotations

from canoniq.connectors._placeholder import PlaceholderConnector


class SQLiteConnector(PlaceholderConnector):
    """Samples rows from a SQLite database file. Uses the stdlib ``sqlite3``. Planned: v0.2.

    Implementation plan: ``list_entities`` queries ``sqlite_master`` for tables;
    ``sample`` runs ``SELECT * FROM <table> LIMIT <n>`` with a quoted identifier;
    ``get_metadata`` reads ``PRAGMA table_info`` for column types and nullability.
    """

    source_type = "sqlite"
    target_version = "v0.2"
    extra = None
