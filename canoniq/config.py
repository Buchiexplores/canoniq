"""Runtime configuration: thresholds, scoring weights, sampling, profiling (§13, §17.3).

Defaults are local-first and deterministic. A config can be loaded from YAML and
overridden field-by-field; unspecified values fall back to the constants module.
"""

from __future__ import annotations

import os
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from canoniq.core import constants as C

# Provider names that mean "no semantic matcher / fully offline".
_DISABLED_PROVIDERS = frozenset({"", "none", "noop", "off"})


class AIConfig(BaseModel):
    """Optional semantic-matching adapter configuration (§23).

    Off by default (``provider="none"``) to honor the local-first guarantee: no model
    is loaded and no network access occurs. Set ``provider`` to a registered adapter
    to enable the optional 6th "semantic" signal:

    - ``sentence-transformers`` — local, on-device embeddings (no egress).
    - ``openai`` / ``gemini`` — hosted embeddings (data egress; opt-in).

    ``model`` selects the provider-specific model version (``None`` → provider default).
    ``api_key_env`` names the environment variable holding the API key for hosted
    providers (``None`` → the provider's default var, e.g. ``OPENAI_API_KEY``); keys
    are never stored in config. ``weight`` is the semantic signal's contribution,
    applied automatically when the adapter is enabled.
    """

    model_config = ConfigDict(extra="forbid")

    provider: str = "none"
    model: str | None = None
    api_key_env: str | None = None
    weight: float = 0.15
    options: dict[str, Any] = Field(default_factory=dict)

    @property
    def enabled(self) -> bool:
        return self.provider.strip().lower() not in _DISABLED_PROVIDERS


class CanonIQConfig(BaseModel):
    """Engine configuration. Frozen-ish: callers build a new instance to override."""

    model_config = ConfigDict(extra="forbid")

    auto_approve_threshold: float = C.DEFAULT_AUTO_APPROVE_THRESHOLD
    review_threshold: float = C.DEFAULT_REVIEW_THRESHOLD
    mapping_floor: float = C.DEFAULT_MAPPING_FLOOR
    weights: dict[str, float] = Field(default_factory=lambda: dict(C.DEFAULT_WEIGHTS))
    sample_limit: int = C.DEFAULT_SAMPLE_LIMIT
    sample_values: int = C.DEFAULT_SAMPLE_VALUES
    mask_pii: bool = True
    ai: AIConfig = Field(default_factory=AIConfig)

    @classmethod
    def from_yaml(cls, path: str) -> CanonIQConfig:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Config not found: {path}")
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return cls(**data)

    def with_overrides(self, **kwargs: object) -> CanonIQConfig:
        merged = self.model_dump()
        for key, value in kwargs.items():
            if value is not None and key in merged:
                merged[key] = value
        return CanonIQConfig(**merged)
