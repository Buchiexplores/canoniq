"""Registry/factory for optional semantic-matching adapters (§23).

Adapters are selected *by name* from configuration, so enabling an AI model is a
declarative, one-line change in a YAML config — no code required for the bundled
providers. Custom adapters can be registered at runtime via ``register_ai_provider``.

Local-first guarantee: the default (``provider="none"``) returns ``None`` so the
mapping engine skips the semantic signal entirely and never loads a model.
"""

from __future__ import annotations

from collections.abc import Callable

from canoniq.ai.base import BaseAIMatcher
from canoniq.config import AIConfig

AIMatcherFactory = Callable[[AIConfig], BaseAIMatcher]

_PROVIDERS: dict[str, AIMatcherFactory] = {}


def register_ai_provider(name: str, factory: AIMatcherFactory) -> None:
    """Register a semantic-matcher factory under ``name`` (case-insensitive)."""
    _PROVIDERS[name.strip().lower()] = factory


def available_providers() -> list[str]:
    """Return the sorted names of all registered providers."""
    return sorted(_PROVIDERS)


def build_ai_matcher(config: AIConfig) -> BaseAIMatcher | None:
    """Construct the configured semantic matcher, or ``None`` when disabled.

    Raises ``ValueError`` for an unknown provider so misconfiguration fails fast
    with an actionable message listing the available options.
    """
    if not config.enabled:
        return None
    name = config.provider.strip().lower()
    factory = _PROVIDERS.get(name)
    if factory is None:
        raise ValueError(
            f"Unknown AI provider {config.provider!r}. "
            f"Available: {', '.join(available_providers()) or '(none registered)'}, "
            "or 'none' to disable."
        )
    return factory(config)


def _provider_kwargs(config: AIConfig, *, include_key_env: bool = False) -> dict:
    """Build adapter kwargs from config, omitting unset fields so adapter defaults win."""
    kwargs = dict(config.options)
    if config.model is not None:
        kwargs["model"] = config.model
    if include_key_env and config.api_key_env is not None:
        kwargs["api_key_env"] = config.api_key_env
    return kwargs


def _build_sentence_transformers(config: AIConfig) -> BaseAIMatcher:
    # Imported lazily so the registry stays importable without the optional extra.
    from canoniq.ai.sentence_transformer_matcher import SentenceTransformerMatcher

    return SentenceTransformerMatcher(**_provider_kwargs(config))


def _build_openai(config: AIConfig) -> BaseAIMatcher:
    from canoniq.ai.embedding_matcher import OpenAIEmbeddingMatcher

    return OpenAIEmbeddingMatcher(**_provider_kwargs(config, include_key_env=True))


def _build_gemini(config: AIConfig) -> BaseAIMatcher:
    from canoniq.ai.embedding_matcher import GeminiEmbeddingMatcher

    return GeminiEmbeddingMatcher(**_provider_kwargs(config, include_key_env=True))


def _build_anthropic(config: AIConfig) -> BaseAIMatcher:
    # Anthropic offers no first-party text-embeddings API, so it cannot power the
    # embedding-based semantic signal. Fail fast with an actionable message.
    raise ValueError(
        "Anthropic (Claude) does not provide a text-embeddings API, so it cannot power "
        "the embedding-based semantic signal. Use provider 'openai' or 'gemini' for "
        "embeddings (or 'sentence-transformers' to stay fully local). Claude is intended "
        "for the upcoming optional LLM reasoning stage, not embeddings."
    )


# Built-in providers. Aliases let users write the most natural name.
for _alias in ("sentence-transformers", "sentence_transformers", "sbert", "local"):
    register_ai_provider(_alias, _build_sentence_transformers)
register_ai_provider("openai", _build_openai)
for _alias in ("gemini", "google", "google-gemini"):
    register_ai_provider(_alias, _build_gemini)
for _alias in ("anthropic", "claude"):
    register_ai_provider(_alias, _build_anthropic)
