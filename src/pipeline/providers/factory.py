"""Factory de providers por nome (SPEC-0003).

A factory apenas despacha pelo nome e delega a validação local ao adapter.
Ela não lê segredos como critério de despacho nem cria cliente remoto: o
cliente é sempre lazy dentro do adapter.
"""

from __future__ import annotations

import importlib
from collections.abc import Mapping

from src.pipeline.providers.errors import UnknownProviderError

_EMBEDDINGS = {
    "openai": ("src.pipeline.providers.embeddings.openai", "OpenAIEmbeddingAdapter"),
    "openrouter": ("src.pipeline.providers.embeddings.openrouter", "OpenRouterEmbeddingAdapter"),
    "huggingface": ("src.pipeline.providers.embeddings.huggingface", "HuggingFaceEmbeddingAdapter"),
    "fake": ("src.pipeline.providers.embeddings.fake", "FakeEmbeddingAdapter"),
}

_VECTOR_STORES = {
    "qdrant": ("src.pipeline.providers.vectorstores.qdrant", "QdrantVectorStoreAdapter"),
    "chroma": ("src.pipeline.providers.vectorstores.chroma", "ChromaVectorStoreAdapter"),
    "pinecone": ("src.pipeline.providers.vectorstores.pinecone", "PineconeVectorStoreAdapter"),
    "in_memory": ("src.pipeline.providers.vectorstores.in_memory", "InMemoryVectorStoreAdapter"),
}


def _resolve(name: str, registry: dict[str, tuple[str, str]], familia: str):
    key = (name or "").strip().lower()
    if key not in registry:
        raise UnknownProviderError(
            f"Provider {familia} desconhecido: {name!r}. "
            f"Opções: {', '.join(sorted(registry))}."
        )
    module_name, class_name = registry[key]
    return getattr(importlib.import_module(module_name), class_name)


class ProviderFactory:
    """Cria adapters de embeddings e vector stores a partir do nome local."""

    @staticmethod
    def create_embedding(name: str, settings: Mapping | None = None):
        adapter_cls = _resolve(name, _EMBEDDINGS, "de embeddings")
        return adapter_cls(**dict(settings or {}))

    @staticmethod
    def create_vector_store(name: str, settings: Mapping | None = None):
        adapter_cls = _resolve(name, _VECTOR_STORES, "de vector store")
        return adapter_cls(**dict(settings or {}))
