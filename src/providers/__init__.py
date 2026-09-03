"""Camada de providers plugáveis (SPEC-0003).

Reexporta os contratos neutros, os erros locais e a Factory. O serviço
``synchronize`` é acrescentado por ``src/providers/vectorstores/base.py``.
"""

from src.providers.contracts import (
    EmbeddingAdapter,
    LogicalScope,
    MirrorCapableVectorStore,
    ProviderCapabilities,
    SearchResult,
    SyncCounts,
    VectorRecord,
    VectorStoreAdapter,
)
from src.providers.errors import (
    InvalidProviderConfigError,
    InvalidScopeError,
    LegacyDestinationError,
    MissingCredentialError,
    ProviderError,
    UnknownProviderError,
    UnreliableScopeReadError,
)
from src.providers.factory import ProviderFactory
from src.providers.vectorstores.base import synchronize

__all__ = [
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
