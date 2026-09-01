"""Adapter de vector store ChromaDB (SPEC-0003).

Destinos novos usam ``chunk_id`` como identidade, o que torna a reexecução
idempotente. Identidades incompatíveis (base legada) bloqueiam antes do upsert
e o destino permanece intacto — esta fatia nunca migra, limpa ou apaga legado.
A ausência de ``tenant_id`` é escopo estrito. Sem extensão ``mirror``.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from src.providers.contracts import LogicalScope, SearchResult, VectorRecord
from src.providers.errors import (
    InvalidProviderConfigError,
    LegacyDestinationError,
    UnreliableScopeReadError,
)
from src.providers.vectorstores.base import BaseVectorStoreAdapter


def _is_chunk_id(value: str) -> bool:
    try:
        UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return False
    return True


class _ChromaBackend:
    """Backend port sobre ``langchain-chroma``."""

    def __init__(self, collection: str, persist_directory: str | None) -> None:
        self._collection = collection
        self._persist_directory = persist_directory
        self._store = None

    def _conn(self):
        if self._store is None:
            from langchain_chroma import Chroma

            self._store = Chroma(
                collection_name=self._collection,
                persist_directory=self._persist_directory,
            )
        return self._store

    def _where(self, scope: LogicalScope) -> dict:
        # tenant ausente é escopo próprio: filtra explicitamente por ausência.
        clauses: list[dict] = [{"project_id": scope.project_id}]
        clauses.append({"tenant_id": scope.tenant_id if scope.tenant_id else ""})
        return {"$and": clauses}

    def ensure(self, scope: LogicalScope, dimensions: int) -> None:
        self._conn()

    def _raw_ids(self, scope: LogicalScope) -> list[str]:
        try:
            found = self._conn().get(where=self._where(scope), include=[])
        except Exception as error:
            raise UnreliableScopeReadError(
                "A releitura do escopo no ChromaDB falhou; sincronização bloqueada."
            ) from error
        return [str(identifier) for identifier in (found or {}).get("ids", [])]

    def incompatible_ids(self, scope: LogicalScope) -> set[str]:
        return {identifier for identifier in self._raw_ids(scope) if not _is_chunk_id(identifier)}

    def scope_ids(self, scope: LogicalScope) -> set[str]:
        return set(self._raw_ids(scope))

    def write(self, scope: LogicalScope, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        from langchain_core.documents import Document

        documents = [
            Document(page_content=record.content, metadata=dict(record.metadata))
            for record in records
        ]
        self._conn().add_documents(
            documents=documents, ids=[record.id for record in records]
        )

    def search(
        self, scope: LogicalScope, embedding: Sequence[float], k: int
    ) -> list[SearchResult]:
        hits = self._conn().similarity_search_by_vector_with_relevance_scores(
            embedding=list(embedding), k=k, filter=self._where(scope)
        )
        return [
            SearchResult(
                content=document.page_content,
                metadata=document.metadata,
                score=float(score),
            )
            for document, score in hits
        ]


class ChromaVectorStoreAdapter(BaseVectorStoreAdapter):
    provider = "chroma"

    def __init__(
        self,
        *,
        collection_name: str | None = None,
        persist_directory: str | None = None,
        client: object | None = None,
        **_ignored: object,
    ) -> None:
        if not isinstance(collection_name, str) or not collection_name.strip():
            raise InvalidProviderConfigError("ChromaDB exige collection_name não vazio.")
        super().__init__(client=client)
        self._collection = collection_name.strip()
        self._persist_directory = persist_directory

    def _create_backend(self) -> _ChromaBackend:
        return _ChromaBackend(self._collection, self._persist_directory)

    def list_ids(self, scope: LogicalScope) -> set[str]:
        backend = self._resolve_backend()
        incompatible = getattr(backend, "incompatible_ids", None)
        if incompatible is not None and incompatible(scope):
            raise LegacyDestinationError(
                "O destino ChromaDB contém identidades incompatíveis com chunk_id "
                "e permanece intacto. Aponte um destino novo: outro "
                "collection_name ou um persist_directory vazio."
            )
        return set(backend.scope_ids(scope))
