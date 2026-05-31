"""JSON Lines source connector (implemented, v0.1)."""

from __future__ import annotations

import json
import os
from typing import Any

from canoniq.connectors.base import BaseSourceConnector

_DEFAULT_ENTITY = "default"


class JSONLConnector(BaseSourceConnector):
    """Reads a local newline-delimited JSON file (one object per line)."""

    def __init__(self, path: str, *, encoding: str = "utf-8"):
        self.path = path
        self.encoding = encoding

    def test_connection(self) -> bool:
        return os.path.isfile(self.path)

    def list_entities(self) -> list[str]:
        return [_DEFAULT_ENTITY]

    def sample(self, entity: str = _DEFAULT_ENTITY, limit: int = 1000) -> list[dict[str, Any]]:
        if not self.test_connection():
            raise FileNotFoundError(f"JSONL source not found: {self.path}")
        rows: list[dict[str, Any]] = []
        with open(self.path, encoding=self.encoding) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                if limit is not None and len(rows) >= limit:
                    break
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
        return rows

    def get_metadata(self, entity: str = _DEFAULT_ENTITY) -> dict[str, Any]:
        return {"type": "jsonl", "path": self.path, "format": "jsonl", "entity": entity}
