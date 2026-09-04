"""Adapter de embeddings OpenAI (SPEC-0003).

Validação local no construtor; o cliente ``OpenAIEmbeddings`` de
``langchain-openai`` é criado sob demanda no primeiro ``embed_*`` (lazy) e
reutilizado. Preserva modelo, dimensões e ``base_url`` observados.
"""

from __future__ import annotations

import os
from collections.abc import Sequence

from src.pipeline.providers.embeddings.base import BaseEmbeddingAdapter
from src.pipeline.providers.errors import MissingCredentialError

_PLACEHOLDERS = ("sk-...", "sk-or-...")


class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    provider = "openai"
    _env_var = "OPENAI_API_KEY"
    _default_base_url: str | None = None

    def __init__(
        self,
        *,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        dimensions: int | None = None,
        base_url: str | None = None,
        **_ignored: object,
    ) -> None:
        resolved = api_key or os.getenv(self._env_var, "")
        if not resolved or resolved.startswith(_PLACEHOLDERS):
            raise MissingCredentialError(
                f"{type(self).__name__} exige credencial: informe api_key na "
                f"configuração ou defina {self._env_var}."
            )
        self._model = model
        self._api_key = resolved
        self._dimensions = int(dimensions) if dimensions else None
        self._base_url = base_url or self._default_base_url
        self._client = None

    def _build_client(self):
        from langchain_openai import OpenAIEmbeddings

        kwargs: dict[str, object] = {"model": self._model, "api_key": self._api_key}
        if self._dimensions:
            kwargs["dimensions"] = self._dimensions
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return OpenAIEmbeddings(**kwargs)

    def _ensure_client(self):
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        return self._ensure_client().embed_documents(list(texts))

    def embed_query(self, text: str) -> list[float]:
        return self._ensure_client().embed_query(text)
