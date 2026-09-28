"""Camada de providers plugáveis (SPEC-0003).

Reexporta os contratos neutros, os erros locais e a Factory. O serviço
``synchronize`` é acrescentado por ``src/pipeline/providers/vectorstores/base.py``.
"""

from src.pipeline.providers.contracts import (
    ChatMessage,
    ChatModelAdapter,
    EmbeddingAdapter,
    LogicalScope,
    MirrorCapableVectorStore,
    ProviderCapabilities,
    SearchResult,
    SyncCounts,
    VectorRecord,
    VectorStoreAdapter,
)
from src.pipeline.providers.errors import (
    ChatProviderError,
    InvalidProviderConfigError,
    InvalidScopeError,
    LegacyDestinationError,
    MissingCredentialError,
    ProviderError,
    UnknownProviderError,
    UnreliableScopeReadError,
)
from src.pipeline.providers.factory import ProviderFactory
from src.pipeline.providers.vectorstores.base import synchronize

__all__ = [
    "ChatMessage",
    "ChatModelAdapter",
    "ChatProviderError",
    "EmbeddingAdapter",
    "InvalidProviderConfigError",
    "InvalidScopeError",
    "LegacyDestinationError",
    "LogicalScope",
    "MirrorCapableVectorStore",
    "MissingCredentialError",
    "ProviderCapabilities",
    "ProviderError",
    "ProviderFactory",
    "SearchResult",
    "SyncCounts",
    "UnknownProviderError",
    "UnreliableScopeReadError",
    "VectorRecord",
    "VectorStoreAdapter",
    "synchronize",
]
