"""Cloud embedding adapters for the optional semantic signal (§23).

Opt-in only. These adapters send text to a hosted embeddings API — the only path by
which data can leave the machine — so they are **off by default** and require an API
key supplied via an environment variable (never stored in config).

Privacy: only source field *names* and canonical schema metadata are sent (see
``canoniq.ai._text``). Sample values — including masked PII/PHI — are never sent.

No third-party SDKs are required: requests use the Python standard library, so the
core install stays lean. Per-text embeddings are cached so a full mapping run makes
roughly ``(unique source names + unique canonical fields)`` calls, not N×M.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from canoniq.ai._text import canonical_text, cosine_to_unit, source_text
from canoniq.ai.base import BaseAIMatcher
from canoniq.core.models import CanonicalField, SourceFieldProfile


class EmbeddingMatcher(BaseAIMatcher):
    """Base class for embedding-API matchers. Subclasses implement ``_embed``."""

    provider_name: str = "embedding"
    default_model: str = ""
    default_key_env: str = ""

    def __init__(
        self,
        model: str | None = None,
        api_key_env: str | None = None,
        timeout: float = 30.0,
        **options: Any,
    ) -> None:
        self.model = model or self.default_model
        self.api_key_env = api_key_env or self.default_key_env
        self.timeout = timeout
        self._options = options
        self._cache: dict[str, list[float]] = {}

    # --- helpers -----------------------------------------------------------

    def _api_key(self) -> str:
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise RuntimeError(
                f"The '{self.provider_name}' embedding provider needs an API key. "
                f"Set the {self.api_key_env} environment variable "
                "(CanonIQ never stores keys in config)."
            )
        return key

    def _post_json(
        self, url: str, payload: dict[str, Any], headers: dict[str, str]
    ) -> dict[str, Any]:  # pragma: no cover - network path, exercised via stubs in tests
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(  # noqa: S310 - fixed https provider endpoints
            url,
            data=data,
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))

    def _embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def _embedding(self, text: str) -> list[float]:
        if text not in self._cache:
            self._cache[text] = self._embed([text])[0]
        return self._cache[text]

    # --- public API --------------------------------------------------------

    def semantic_score(
        self, source_field: SourceFieldProfile, canonical_field: CanonicalField
    ) -> float:
        a = self._embedding(source_text(source_field))
        b = self._embedding(canonical_text(canonical_field))
        return cosine_to_unit(a, b)


class OpenAIEmbeddingMatcher(EmbeddingMatcher):
    """OpenAI embeddings (e.g. text-embedding-3-small / -large)."""

    provider_name = "openai"
    default_model = "text-embedding-3-small"
    default_key_env = "OPENAI_API_KEY"
    base_url = "https://api.openai.com/v1"

    def _embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover - network
        url = str(self._options.get("base_url", self.base_url)).rstrip("/") + "/embeddings"
        resp = self._post_json(
            url,
            {"model": self.model, "input": texts},
            {"Authorization": f"Bearer {self._api_key()}"},
        )
        rows = sorted(resp["data"], key=lambda r: r["index"])
        return [row["embedding"] for row in rows]


class GeminiEmbeddingMatcher(EmbeddingMatcher):
    """Google Gemini embeddings (e.g. text-embedding-004)."""

    provider_name = "gemini"
    default_model = "text-embedding-004"
    default_key_env = "GEMINI_API_KEY"
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    def _embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover - network
        model_path = self.model if self.model.startswith("models/") else f"models/{self.model}"
        base = str(self._options.get("base_url", self.base_url)).rstrip("/")
        url = f"{base}/{model_path}:batchEmbedContents"
        payload = {
            "requests": [
                {"model": model_path, "content": {"parts": [{"text": text}]}}
                for text in texts
            ]
        }
        # Key sent as a header (not a query param) to avoid leaking it into URL logs.
        resp = self._post_json(url, payload, {"x-goog-api-key": self._api_key()})
        return [item["values"] for item in resp["embeddings"]]
