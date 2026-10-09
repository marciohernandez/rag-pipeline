"""Adapter de embeddings Hugging Face locais (SPEC-0003).

Baseado em ``langchain-huggingface``. Não exige credencial; o modelo é carregado
sob demanda no primeiro ``embed_*`` (lazy) e reutilizado.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.pipeline.providers.embeddings.base import BaseEmbeddingAdapter
from src.pipeline.providers.errors import InvalidProviderConfigError

_DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class HuggingFaceEmbeddingAdapter(BaseEmbeddingAdapter):
    provider = "huggingface"

    def __init__(self, *, model: str | None = None, **_ignored: object) -> None:
        model_name = model or _DEFAULT_MODEL
        if not isinstance(model_name, str) or not model_name.strip():
            raise InvalidProviderConfigError("HuggingFace exige um nome de modelo não vazio.")
        self._model = model_name.strip()
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from langchain_huggingface import HuggingFaceEmbeddings

            self._client = HuggingFaceEmbeddings(model_name=self._model)
        return self._client

    def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        return self._ensure_client().embed_documents(list(texts))

    def embed_query(self, text: str) -> list[float]:
        return self._ensure_client().embed_query(text)
