"""Cloud embedding adapters: OpenAI, Gemini, Anthropic (§23).

These tests make ZERO network calls. The provider-specific ``_embed`` HTTP method is
either stubbed or never reached; we exercise text-building, cosine scoring, caching,
API-key resolution, error handling, config, and registry wiring.
"""

from __future__ import annotations

import pytest

from canoniq.ai.embedding_matcher import (
    EmbeddingMatcher,
    GeminiEmbeddingMatcher,
    OpenAIEmbeddingMatcher,
)
from canoniq.ai.registry import available_providers, build_ai_matcher
from canoniq.config import AIConfig
from canoniq.core.models import CanonicalField, SourceFieldProfile


def _src(name: str) -> SourceFieldProfile:
    return SourceFieldProfile(name=name, inferred_type="string", null_rate=0.0, unique_rate=1.0)


def _canon(name: str, **kw) -> CanonicalField:
    return CanonicalField(name=name, type="string", **kw)


class _CountingMatcher(EmbeddingMatcher):
    """Offline matcher with a deterministic, call-counting fake embedder."""

    provider_name = "counting"
    default_model = "fake-embed"
    default_key_env = "FAKE_KEY"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.calls: list[list[str]] = []

    def _embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        # Deterministic 3-d vector; identical text -> identical vector -> cosine 1.0.
        return [[float(sum(ord(c) for c in t)), float(len(t)), 1.0] for t in texts]


# --- scoring / caching -----------------------------------------------------


def test_identical_text_scores_one():
    m = _CountingMatcher()
    score = m.semantic_score(_src("account_id"), _canon("account id"))
    assert score == pytest.approx(1.0)


def test_score_within_unit_interval():
    m = _CountingMatcher()
    score = m.semantic_score(_src("xyz"), _canon("account_id"))
    assert 0.0 <= score <= 1.0


def test_embeddings_are_cached_per_text():
    m = _CountingMatcher()
    src = _src("status")
    m.semantic_score(src, _canon("enrollment_status"))
    m.semantic_score(src, _canon("account_status"))
    # Unique texts embedded: "status", "enrollment status", "account status" = 3 calls.
    flat = [t for call in m.calls for t in call]
    assert flat.count("status") == 1
    assert len(flat) == 3


# --- API-key resolution ----------------------------------------------------


def test_missing_api_key_raises_with_env_var_name(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    m = OpenAIEmbeddingMatcher()
    with pytest.raises(RuntimeError) as exc:
        m._api_key()
    assert "OPENAI_API_KEY" in str(exc.value)


def test_custom_api_key_env(monkeypatch):
    monkeypatch.setenv("MY_KEY", "secret-123")
    m = OpenAIEmbeddingMatcher(api_key_env="MY_KEY")
    assert m._api_key() == "secret-123"


# --- provider defaults -----------------------------------------------------


def test_openai_defaults():
    m = OpenAIEmbeddingMatcher()
    assert m.model == "text-embedding-3-small"
    assert m.api_key_env == "OPENAI_API_KEY"


def test_gemini_defaults():
    m = GeminiEmbeddingMatcher()
    assert m.model == "text-embedding-004"
    assert m.api_key_env == "GEMINI_API_KEY"


def test_model_version_is_configurable():
    m = OpenAIEmbeddingMatcher(model="text-embedding-3-large")
    assert m.model == "text-embedding-3-large"


# --- registry wiring -------------------------------------------------------


@pytest.mark.parametrize("provider", ["openai", "gemini", "google", "anthropic", "claude"])
def test_cloud_providers_registered(provider):
    assert provider in available_providers()


def test_build_openai_via_config():
    m = build_ai_matcher(AIConfig(provider="openai", model="text-embedding-3-large"))
    assert isinstance(m, OpenAIEmbeddingMatcher)
    assert m.model == "text-embedding-3-large"


def test_build_gemini_via_config_default_model():
    m = build_ai_matcher(AIConfig(provider="gemini"))
    assert isinstance(m, GeminiEmbeddingMatcher)
    assert m.model == "text-embedding-004"  # provider default applies when unset


def test_build_passes_api_key_env_and_options():
    m = build_ai_matcher(
        AIConfig(provider="openai", api_key_env="CUSTOM_KEY", options={"timeout": 5.0})
    )
    assert isinstance(m, OpenAIEmbeddingMatcher)
    assert m.api_key_env == "CUSTOM_KEY"
    assert m.timeout == 5.0


# --- Anthropic: honest, actionable failure ---------------------------------


@pytest.mark.parametrize("provider", ["anthropic", "claude"])
def test_anthropic_embeddings_raise_clear_error(provider):
    with pytest.raises(ValueError) as exc:
        build_ai_matcher(AIConfig(provider=provider))
    msg = str(exc.value).lower()
    assert "embedding" in msg
    assert "openai" in msg or "gemini" in msg
