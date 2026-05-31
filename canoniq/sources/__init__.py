"""Source configuration loading (§19)."""

from canoniq.sources.config_loader import (
    SourceConfigError,
    build_connector,
    load_source_config,
)

__all__ = ["SourceConfigError", "load_source_config", "build_connector"]
