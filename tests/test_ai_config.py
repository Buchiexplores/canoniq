"""AI adapter configuration, registry/factory, and engine wiring (§23).

These tests must make ZERO network calls. The sentence-transformers provider is
checked only at the factory level (object construction), which must NOT import the
heavy optional dependency — the import is deferred until the model is actually used.
"""

from __future__ import annotations

import pytest

from canoniq.ai import NoOpAIMatcher
from canoniq.ai.base import BaseAIMatcher
from canoniq.ai.registry import (
    available_providers,
    build_ai_matcher,
    register_ai_provider,
)
from canoniq.config import AIConfig, CanonIQConfig
from canoniq.core.models import CanonicalField, SourceFieldProfile
from canoniq.engine import CanonIQ


class _StubMatcher(BaseAIMatcher):
    """Deterministic, offline stub used to exercise wiring without a real model."""

    def __init__(self, score: float = 1.0) -> None:
        self.score = score

    def semantic_score(
        self, source_field: SourceFieldProfile, canonical_field: CanonicalField
    ) -> float:
        return self.score


# --- AIConfig --------------------------------------------------------------


def test_ai_config_defaults_disabled():
    cfg = AIConfig()
    assert cfg.provider == "none"
    assert cfg.model is None  # provider supplies its own default model
    assert cfg.api_key_env is None
    assert cfg.weight == 0.15
    assert cfg.enabled is False


@pytest.mark.parametrize("provider", ["none", "None", "noop", "off", ""])
def test_ai_config_disabled_aliases(provider):
    assert AIConfig(provider=provider).enabled is False


def test_ai_config_enabled_when_provider_set():
    assert AIConfig(provider="sentence-transformers").enabled is True


def test_canoniq_config_has_default_ai_block():
    cfg = CanonIQConfig()
    assert isinstance(cfg.ai, AIConfig)
    assert cfg.ai.enabled is False


def test_canoniq_config_ai_block_from_yaml(tmp_path):
    p = tmp_path / "cfg.yml"
    p.write_text(
        "ai:\n"
        "  provider: sentence-transformers\n"
        "  model: all-mpnet-base-v2\n"
        "  weight: 0.25\n"
    )
    cfg = CanonIQConfig.from_yaml(str(p))
    assert cfg.ai.provider == "sentence-transformers"
    assert cfg.ai.model == "all-mpnet-base-v2"
    assert cfg.ai.weight == 0.25
    assert cfg.ai.enabled is True


# --- registry / factory ----------------------------------------------------


def test_build_ai_matcher_none_returns_none():
    assert build_ai_matcher(AIConfig(provider="none")) is None


def test_build_ai_matcher_unknown_provider_raises():
    with pytest.raises(ValueError) as exc:
        build_ai_matcher(AIConfig(provider="does-not-exist"))
    assert "does-not-exist" in str(exc.value)
    assert "Available" in str(exc.value)


def test_sentence_transformers_is_registered():
    assert "sentence-transformers" in available_providers()


def test_build_sentence_transformers_does_not_import_heavy_dep():
    # Constructing the adapter must be cheap and offline; the heavy import is deferred.
    matcher = build_ai_matcher(AIConfig(provider="sentence-transformers", model="x"))
    assert isinstance(matcher, BaseAIMatcher)
    assert getattr(matcher, "model_name", None) == "x"


def test_register_custom_provider_and_build():
    register_ai_provider("stub-test", lambda cfg: _StubMatcher(score=0.5))
    matcher = build_ai_matcher(AIConfig(provider="stub-test"))
    assert isinstance(matcher, _StubMatcher)
    assert matcher.score == 0.5


# --- engine wiring ---------------------------------------------------------


def test_engine_default_has_no_ai_matcher():
    engine = CanonIQ()
    assert engine.ai_matcher is None
    assert engine.config.weights.get("semantic", 0.0) == 0.0


def test_engine_builds_ai_matcher_and_enables_semantic_weight():
    register_ai_provider("stub-wire", lambda cfg: _StubMatcher(score=1.0))
    cfg = CanonIQConfig(ai=AIConfig(provider="stub-wire", weight=0.2))
    engine = CanonIQ(cfg)
    assert isinstance(engine.ai_matcher, _StubMatcher)
    # semantic weight must be turned on so the signal actually contributes
    assert engine.config.weights["semantic"] == 0.2
    # original config object must not be mutated (immutability)
    assert cfg.weights.get("semantic", 0.0) == 0.0


def test_explicit_ai_matcher_overrides_config():
    explicit = _StubMatcher(score=0.3)
    cfg = CanonIQConfig(ai=AIConfig(provider="sentence-transformers"))
    engine = CanonIQ(cfg, ai_matcher=explicit)
    assert engine.ai_matcher is explicit


def test_semantic_signal_flows_through_suggest(examples_dir):
    """An enabled adapter must actually contribute a 'semantic' signal to mappings."""
    import os

    register_ai_provider("stub-flow", lambda cfg: _StubMatcher(score=1.0))
    cfg = CanonIQConfig(ai=AIConfig(provider="stub-flow", weight=0.2))
    engine = CanonIQ(cfg)

    source = os.path.join(examples_dir, "retail", "source_products.csv")
    canonical = os.path.join(examples_dir, "retail", "canonical_product.yml")
    profile = engine.profile_source(source)
    result = engine.suggest_mappings(profile, canonical)

    scored = [m for m in result.mappings if m.canonical_field is not None]
    assert scored, "expected at least one scored mapping"
    assert any("semantic" in m.signals for m in scored)


def test_noop_matcher_still_importable():
    assert NoOpAIMatcher().semantic_score(
        SourceFieldProfile(name="a", inferred_type="string", null_rate=0.0, unique_rate=1.0),
        CanonicalField(name="b", type="string"),
    ) == 0.0
