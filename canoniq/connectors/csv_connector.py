"""CSV source connector (implemented, v0.1)."""

from __future__ import annotations

import csv
import os
from typing import Any

from canoniq.connectors.base import BaseSourceConnector

_DEFAULT_ENTITY = "default"


class CSVConnector(BaseSourceConnector):
    """Reads a local CSV file. Values are returned as strings; the profiler infers types."""

    def __init__(self, path: str, *, delimiter: str | None = None, encoding: str = "utf-8"):
        self.path = path
        self.delimiter = delimiter
        self.encoding = encoding

    def test_connection(self) -> bool:
        return os.path.isfile(self.path)

    def list_entities(self) -> list[str]:
        return [_DEFAULT_ENTITY]

    def _sniff_delimiter(self, sample: str) -> str:
        if self.delimiter:
            return self.delimiter
        try:
            return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
        except csv.Error:
            return ","

    def sample(self, entity: str = _DEFAULT_ENTITY, limit: int = 1000) -> list[dict[str, Any]]:
        if not self.test_connection():
            raise FileNotFoundError(f"CSV source not found: {self.path}")
        with open(self.path, encoding=self.encoding, newline="") as fh:
            head = fh.read(8192)
            fh.seek(0)
            delimiter = self._sniff_delimiter(head)
            reader = csv.DictReader(fh, delimiter=delimiter)
            rows: list[dict[str, Any]] = []
            for i, row in enumerate(reader):
                if limit is not None and i >= limit:
                    break
                rows.append(dict(row))
        return rows

    def get_metadata(self, entity: str = _DEFAULT_ENTITY) -> dict[str, Any]:
        return {
            "type": "csv",
            "path": self.path,
            "format": "csv",
            "entity": entity,
        }
