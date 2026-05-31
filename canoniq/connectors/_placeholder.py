"""Shared scaffolding for placeholder connectors (§17.1).

Each placeholder subclasses ``BaseSourceConnector`` and raises a clear
``NotImplementedError`` naming the target version and required optional-dependency
extra. This keeps the connector surface complete while the real implementations
land in later releases.
"""

from __future__ import annotations

from typing import Any

from canoniq.connectors.base import BaseSourceConnector


class PlaceholderConnector(BaseSourceConnector):
    """Base for not-yet-implemented connectors.

    Subclasses set ``source_type``, ``target_version`` and ``extra`` so the raised
    error is specific and actionable.
    """

    source_type: str = "source"
    target_version: str = "future"
    extra: str | None = None

    def __init__(self, **config: Any) -> None:
        # Placeholders accept whatever the source config provides and defer
        # validation to the real implementation. Stored for introspection only.
        self.config = config

    def _not_implemented(self) -> NotImplementedError:
        extra_hint = f" (extra: {self.extra})" if self.extra else ""
        return NotImplementedError(
            f"{type(self).__name__} ({self.source_type}) will be implemented in "
            f"{self.target_version}{extra_hint}."
        )

    def test_connection(self) -> bool:
        raise self._not_implemented()

    def list_entities(self) -> list[str]:
        raise self._not_implemented()

    def sample(self, entity: str, limit: int = 1000) -> list[dict[str, Any]]:
        raise self._not_implemented()

    def get_metadata(self, entity: str) -> dict[str, Any]:
        raise self._not_implemented()
