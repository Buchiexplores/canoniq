# Connectors

A **connector** is the only part of CanonIQ that touches a data source. Connectors return records
in the common internal format `list[dict[str, Any]]` plus metadata, so the profiler and matcher stay
completely source-agnostic.

## The interface

Every connector subclasses `BaseSourceConnector` (`canoniq/connectors/base.py`):

```python
from abc import ABC, abstractmethod
from typing import Any

class BaseSourceConnector(ABC):
    @abstractmethod
    def test_connection(self) -> bool: ...
    @abstractmethod
    def list_entities(self) -> list[str]: ...
    @abstractmethod
    def sample(self, entity: str, limit: int = 1000) -> list[dict[str, Any]]: ...
    @abstractmethod
    def get_metadata(self, entity: str) -> dict[str, Any]: ...
```

- `sample` returns a representative slice of records for profiling.
- `get_metadata` returns name/schema/path/format, declared column types, nullability, comments, and
  a row-count estimate **when available** (these become `declared_type` hints in the profile).

## What ships in v0.1

**Real (implemented):** `csv`, `json`, `jsonl`/`ndjson`.

**Placeholders:** Parquet, Excel, SQLite, Postgres, MySQL, BigQuery, Snowflake, Redshift, S3, GCS,
Azure Blob, REST API. Each follows `BaseSourceConnector`, carries a docstring with its
implementation plan, and raises a clear `NotImplementedError` naming its `target_version` and
required `extra`. They accept arbitrary config so source-config files load today.

```python
class RedshiftConnector(PlaceholderConnector):
    source_type = "redshift"
    target_version = "v0.3"
    extra = "databases"
```

## Resolving a connector

The registry maps a `type` string to a connector class:

```python
from canoniq.connectors import connector_for_type
connector_for_type("csv")         # -> CSVConnector
connector_for_type("postgresql")  # -> PostgresConnector
connector_for_type("quantum_db")  # -> ValueError: unknown type
```

Aliases are supported (`postgres`/`postgresql`, `azure`/`azure_blob`, `rest`/`rest_api`).

## Adding a connector

1. **Subclass `BaseSourceConnector`** in `canoniq/connectors/<name>_connector.py` and implement all
   four methods. Return the common `list[dict]` format from `sample`.
2. **Declare its extra.** If it needs third-party packages, add a dependency group in
   `pyproject.toml` (e.g. `[project.optional-dependencies] mysource = [...]`) and import those
   packages lazily inside the methods so the core install stays light.
3. **Register it.** Add the class to `_REGISTRY` in `canoniq/connectors/__init__.py` (with any
   aliases) and to `__all__`.
4. **Surface metadata.** Populate `get_metadata` with declared types/nullability when the source
   exposes them — the profiler uses these as hints.
5. **Test it.** Add a unit test. Tests must make **zero** network calls; use local fixtures or a
   temporary local file. Network is blocked in the test session by a socket guard.

Source-config files reference the connector by its `type` — see [sources.md](sources.md).
