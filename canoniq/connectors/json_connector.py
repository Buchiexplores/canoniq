"""JSON source connector (implemented, v0.1).

Supports a top-level array of objects, or an object wrapping a list under a
``records``/``data``/``items`` key.
"""

from __future__ import annotations

import json
import os
from typing import Any

from canoniq.connectors.base import BaseSourceConnector

_DEFAULT_ENTITY = "default"
_LIST_KEYS = ("records", "data", "items", "rows", "results")


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in _LIST_KEYS:
            value = payload.get(key)
            if isinstance(value, list):
                return [r for r in value if isinstance(r, dict)]
        # single object → one record
        return [payload]
    raise ValueError("Unsupported JSON structure: expected array or object with a list field.")


class JSONConnector(BaseSourceConnector):
    """Reads a local JSON file containing an array (or wrapped array) of objects."""

    def __init__(self, path: str, *, encoding: str = "utf-8"):
        self.path = path
        self.encoding = encoding

    def test_connection(self) -> bool:
        return os.path.isfile(self.path)

    def list_entities(self) -> list[str]:
        return [_DEFAULT_ENTITY]

    def sample(self, entity: str = _DEFAULT_ENTITY, limit: int = 1000) -> list[dict[str, Any]]:
        if not self.test_connection():
            raise FileNotFoundError(f"JSON source not found: {self.path}")
        with open(self.path, encoding=self.encoding) as fh:
            payload = json.load(fh)
        records = _extract_records(payload)
        return records[:limit] if limit is not None else records

    def get_metadata(self, entity: str = _DEFAULT_ENTITY) -> dict[str, Any]:
        return {"type": "json", "path": self.path, "format": "json", "entity": entity}
