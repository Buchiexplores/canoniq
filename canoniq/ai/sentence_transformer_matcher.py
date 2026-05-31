"""Local sentence-transformers semantic matcher (§23).

Opt-in only. This is the one place CanonIQ can load an external model, and it runs
**locally** — embeddings are computed on-device; no source data, schema, or values
are sent to a hosted service. The model files are downloaded from the model hub on
first use (the only network access), then cached locally for offline runs.

Requires the optional dependency: ``pip install "canoniq[ai]"``.
"""

from __future__ import annotations

from typing import Any

from canoniq.ai._text import canonical_text, cosine_to_unit, source_text
from canoniq.ai.base import BaseAIMatcher
from canoniq.core.models import CanonicalField, SourceFieldProfile

_INSTALL_HINT = (
    "The 'sentence-transformers' provider requires the optional 'ai' extra. "
    "Install it with: pip install 'canoniq[ai]'"
)


class SentenceTransformerMatcher(BaseAIMatcher):
    """Cosine similarity between source and canonical field descriptions.

    The heavy ``sentence_transformers`` import and model load are deferred until the
    first ``semantic_score`` call, so constructing this object is cheap and offline
    (and importing the module never requires the optional dependency).
    """

    def __init__(self, model: str | None = None, **options: Any) -> None:
        self.model_name = model or "all-MiniLM-L6-v2"
        self._options = options
        self._model: Any | None = None

    def _ensure_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - exercised only without extra
                raise ImportError(_INSTALL_HINT) from exc
            self._model = SentenceTransformer(self.model_name, **self._options)
        return self._model

    def semantic_score(
        self, source_field: SourceFieldProfile, canonical_field: CanonicalField
    ) -> float:
        model = self._ensure_model()
        embeddings = model.encode(
            [source_text(source_field), canonical_text(canonical_field)],
            normalize_embeddings=False,
        )
        return cosine_to_unit(list(embeddings[0]), list(embeddings[1]))
