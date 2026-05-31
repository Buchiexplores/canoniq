"""Placeholder connectors must raise NotImplementedError, not silently no-op (§17.1)."""

from __future__ import annotations

import pytest

from canoniq.connectors import (
    AzureBlobConnector,
    BigQueryConnector,
    ExcelConnector,
    GCSConnector,
    MySQLConnector,
    ParquetConnector,
    PostgresConnector,
    RedshiftConnector,
    RestAPIConnector,
    S3Connector,
    SnowflakeConnector,
    SQLiteConnector,
    connector_for_type,
)

PLACEHOLDERS = [
    ParquetConnector, ExcelConnector, SQLiteConnector, PostgresConnector,
    MySQLConnector, BigQueryConnector, SnowflakeConnector, RedshiftConnector,
    S3Connector, GCSConnector, AzureBlobConnector, RestAPIConnector,
]


@pytest.mark.parametrize("cls", PLACEHOLDERS)
def test_placeholder_accepts_arbitrary_config(cls):
    # Placeholders absorb whatever config the source file provides.
    conn = cls(foo="bar", anything=123)
    assert conn.config == {"foo": "bar", "anything": 123}


@pytest.mark.parametrize("cls", PLACEHOLDERS)
def test_placeholder_sample_raises(cls):
    conn = cls()
    with pytest.raises(NotImplementedError):
        conn.sample("entity")


@pytest.mark.parametrize("cls", PLACEHOLDERS)
def test_placeholder_other_methods_raise(cls):
    conn = cls()
    with pytest.raises(NotImplementedError):
        conn.test_connection()
    with pytest.raises(NotImplementedError):
        conn.list_entities()
    with pytest.raises(NotImplementedError):
        conn.get_metadata("entity")


def test_unknown_source_type_raises():
    with pytest.raises(ValueError):
        connector_for_type("quantum_database")


def test_registry_resolves_known_types():
    assert connector_for_type("csv").__name__ == "CSVConnector"
    assert connector_for_type("postgresql").__name__ == "PostgresConnector"
