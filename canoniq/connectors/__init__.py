"""Source connectors — the source-agnostic data-access boundary (§17).

Real connectors (v0.1): CSV, JSON, JSONL.
Placeholder connectors raise ``NotImplementedError`` naming target version + extra.
"""

from __future__ import annotations

from canoniq.connectors.azure_blob_connector import AzureBlobConnector
from canoniq.connectors.base import BaseSourceConnector
from canoniq.connectors.bigquery_connector import BigQueryConnector
from canoniq.connectors.csv_connector import CSVConnector
from canoniq.connectors.excel_connector import ExcelConnector
from canoniq.connectors.gcs_connector import GCSConnector
from canoniq.connectors.json_connector import JSONConnector
from canoniq.connectors.jsonl_connector import JSONLConnector
from canoniq.connectors.mysql_connector import MySQLConnector
from canoniq.connectors.parquet_connector import ParquetConnector
from canoniq.connectors.postgres_connector import PostgresConnector
from canoniq.connectors.redshift_connector import RedshiftConnector
from canoniq.connectors.rest_api_connector import RestAPIConnector
from canoniq.connectors.s3_connector import S3Connector
from canoniq.connectors.snowflake_connector import SnowflakeConnector
from canoniq.connectors.sqlite_connector import SQLiteConnector

__all__ = [
    "BaseSourceConnector",
    "CSVConnector",
    "JSONConnector",
    "JSONLConnector",
    "ParquetConnector",
    "ExcelConnector",
    "SQLiteConnector",
    "PostgresConnector",
    "MySQLConnector",
    "BigQueryConnector",
    "SnowflakeConnector",
    "RedshiftConnector",
    "S3Connector",
    "GCSConnector",
    "AzureBlobConnector",
    "RestAPIConnector",
    "connector_for_type",
]

# Registry mapping a source-config ``type`` to its connector class.
_REGISTRY: dict[str, type[BaseSourceConnector]] = {
    "csv": CSVConnector,
    "json": JSONConnector,
    "jsonl": JSONLConnector,
    "parquet": ParquetConnector,
    "excel": ExcelConnector,
    "sqlite": SQLiteConnector,
    "postgres": PostgresConnector,
    "postgresql": PostgresConnector,
    "mysql": MySQLConnector,
    "bigquery": BigQueryConnector,
    "snowflake": SnowflakeConnector,
    "redshift": RedshiftConnector,
    "s3": S3Connector,
    "gcs": GCSConnector,
    "azure_blob": AzureBlobConnector,
    "azure": AzureBlobConnector,
    "rest_api": RestAPIConnector,
    "rest": RestAPIConnector,
}


def connector_for_type(source_type: str) -> type[BaseSourceConnector]:
    """Return the connector class registered for a source-config ``type``."""
    key = source_type.strip().lower()
    if key not in _REGISTRY:
        raise ValueError(
            f"Unknown source type {source_type!r}. "
            f"Known types: {', '.join(sorted(_REGISTRY))}."
        )
    return _REGISTRY[key]
