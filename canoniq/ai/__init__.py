"""Optional, pluggable AI matching adapter (§23).

The core engine is deterministic and offline. This package adds an *optional* 6th
"semantic" signal. The default is a local no-op (off); adapters are selected by name
from config via the registry, so enabling a model is a one-line YAML change.

No external calls are made unless a user explicitly enables an external adapter.
"""

from canoniq.ai.base import BaseAIMatcher
from canoniq.ai.embedding_matcher import (
    EmbeddingMatcher,
    GeminiEmbeddingMatcher,
    OpenAIEmbeddingMatcher,
)
from canoniq.ai.optional_ai_matcher import NoOpAIMatcher
from canoniq.ai.registry import (
    available_providers,
    build_ai_matcher,
    register_ai_provider,
)

__all__ = [
    "BaseAIMatcher",
    "EmbeddingMatcher",
    "GeminiEmbeddingMatcher",
    "NoOpAIMatcher",
    "OpenAIEmbeddingMatcher",
    "available_providers",
    "build_ai_matcher",
    "register_ai_provider",
]
