"""Source-config YAML loader with ``${ENV}`` interpolation and secret-leak warnings (§19).

Security requirement: credentials must never be stored inline. Any ``${VAR}`` token is
resolved from the environment at load time. A config that appears to contain a literal
secret (e.g. an inline password value) triggers a warning.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import yaml

from canoniq.connectors import BaseSourceConnector, connector_for_type

logger = logging.getLogger("canoniq.sources")

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")

# Keys whose inline (non-${ENV}) values are suspicious and likely leaked secrets.
_SECRET_KEYS = frozenset({
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "access_key", "secret_key", "private_key", "credentials",
})

# Connector constructor params keyed by source type. ``path`` etc. are filtered
# against each connector's __init__ so unknown config keys raise clearly.
_RESERVED_KEYS = frozenset({"type", "sample_limit"})


class SourceConfigError(ValueError):
    """Raised when a source config is malformed or references a missing env var."""


def _interpolate(value: Any) -> Any:
    """Recursively replace ``${VAR}`` tokens from the environment."""
    if isinstance(value, str):
        def repl(match: re.Match[str]) -> str:
            var = match.group(1)
            if var not in os.environ:
                raise SourceConfigError(
                    f"Environment variable ${{{var}}} referenced in source config is not set."
                )
            return os.environ[var]

        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(v) for v in value]
    return value


def _warn_on_inline_secrets(raw_source: dict[str, Any]) -> None:
    for key, value in raw_source.items():
        if key.lower() in _SECRET_KEYS and isinstance(value, str):
            if value and not _ENV_PATTERN.search(value):
                logger.warning(
                    "Source config key %r looks like an inline secret. Use ${ENV} "
                    "interpolation instead of committing credentials.",
                    key,
                )


def load_source_config(path: str) -> dict[str, Any]:
    """Load and validate a source-config YAML file, returning the ``source`` dict."""
    if not os.path.isfile(path):
        raise SourceConfigError(f"Source config not found: {path}")
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or "source" not in doc:
        raise SourceConfigError("Source config must be a mapping with a top-level 'source' key.")
    raw_source = doc["source"]
    if not isinstance(raw_source, dict) or "type" not in raw_source:
        raise SourceConfigError("source must be a mapping that includes a 'type'.")

    _warn_on_inline_secrets(raw_source)
    resolved = _interpolate(raw_source)
    return resolved


def build_connector(source: dict[str, Any]) -> tuple[BaseSourceConnector, dict[str, Any]]:
    """Construct a connector from a resolved source dict.

    Returns the connector and the resolved source mapping (so the caller can read
    ``sample_limit`` and ``entity``). Unknown keys for the chosen connector raise.
    """
    source_type = source["type"]
    connector_cls = connector_for_type(source_type)
    kwargs = {k: v for k, v in source.items() if k not in _RESERVED_KEYS}
    try:
        connector = connector_cls(**kwargs)
    except TypeError as exc:  # bad/unknown kwargs for this connector
        raise SourceConfigError(
            f"Invalid configuration for source type {source_type!r}: {exc}"
        ) from exc
    return connector, source
