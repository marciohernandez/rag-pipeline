"""Adapter de vector store Pinecone (SPEC-0003).

Opera em ``append``, preservando namespace e ID estável. A releitura dos IDs do
escopo acontece antes do upsert para que as contagens sejam exatas; quando essa
releitura não puder ser concluída, a sincronização é bloqueada em vez de
publicar números aproximados. Sem extensão ``mirror`` nesta fatia.
"""

from __future__ import annotations

import os
from collections.abc import Sequence

from src.providers.contracts import LogicalScope, SearchResult, VectorRecord
from src.providers.errors import (
    InvalidProviderConfigError,
    MissingCredentialError,
    UnreliableScopeReadError,
)
from src.providers.vectorstores.base import BaseVectorStoreAdapter

_PAGE = 100


class _PineconeBackend:
    """Backend port sobre o SDK do Pinecone."""

    def __init__(self, index_name: str, namespace: str, api_key: str) -> None:
        self._index_name = index_name
        self._namespace = namespace
        self._api_key = api_key
        self._index = None

    def _conn(self):
        if self._index is None:
            from pinecone import Pinecone

            self._index = Pinecone(api_key=self._api_key).Index(self._index_name)
        return self._index

    def _prefix(self, scope: LogicalScope) -> str:
        tenant = scope.tenant_id or "-"
        return f"{scope.project_id}|{tenant}|"

    def ensure(self, scope: LogicalScope, dimensions: int) -> None:
        from pinecone import Pinecone

        description = Pinecone(api_key=self._api_key).describe_index(self._index_name)
        if description.dimension != dimensions:
            raise InvalidProviderConfigError(
                f"Dimensão do índice Pinecone {self._index_name!r} "
                f"({description.dimension}) difere da dimensão configurada "
                f"para embeddings ({dimensions})."
            )

    def describe(self, scope: LogicalScope) -> dict:
        """Lê a descrição do índice sem criá-lo.

        ``describe_index`` é a mesma leitura já usada por ``ensure`` para
        comparar dimensões, aqui sem levantar erro: índice ausente ou destino
        inacessível devolvem mapa vazio.
        """
        from pinecone import Pinecone

        try:
            description = Pinecone(api_key=self._api_key).describe_index(
                self._index_name
            )
        except Exception:  # índice ausente ou destino inacessível
            return {}
        return {"exists": True, "dimensions": getattr(description, "dimension", None)}

    def scope_ids(self, scope: LogicalScope) -> set[str]:
        found: set[str] = set()
        try:
            for page in self._conn().list(
                prefix=self._prefix(scope), namespace=self._namespace, limit=_PAGE
            ):
                found.update(str(identifier) for identifier in page)
        except Exception as error:
            raise UnreliableScopeReadError(
                "A releitura paginada do escopo no Pinecone falhou; "
                "sincronização bloqueada e nenhuma contagem aproximada publicada."
            ) from error
        return {identifier.split("|")[-1] for identifier in found}

    def write(self, scope: LogicalScope, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        prefix = self._prefix(scope)
        vectors = [
            {
                "id": f"{prefix}{record.id}",
                "values": list(record.vector),
                "metadata": {
                    **dict(record.metadata),
                    "page_content": record.content,
                    "project_id": scope.project_id,
                    **({"tenant_id": scope.tenant_id} if scope.tenant_id else {}),
                },
            }
            for record in records
        ]
        self._conn().upsert(vectors=vectors, namespace=self._namespace)

    def search(
        self, scope: LogicalScope, embedding: Sequence[float], k: int
    ) -> list[SearchResult]:
        scope_filter: dict[str, object] = {"project_id": {"$eq": scope.project_id}}
        if scope.tenant_id is not None:
            scope_filter["tenant_id"] = {"$eq": scope.tenant_id}
        else:
            scope_filter["tenant_id"] = {"$exists": False}
        response = self._conn().query(
            vector=list(embedding),
            top_k=k,
            namespace=self._namespace,
            filter=scope_filter,
            include_metadata=True,
        )
        results = []
        for match in response.get("matches", []):
            metadata = dict(match.get("metadata") or {})
            results.append(
                SearchResult(
                    content=metadata.pop("page_content", ""),
                    metadata=metadata,
                    score=float(match.get("score", 0.0)),
                )
            )
        return results


class PineconeVectorStoreAdapter(BaseVectorStoreAdapter):
    provider = "pinecone"

    def __init__(
        self,
        *,
        index_name: str | None = None,
        namespace: str | None = None,
        api_key: str | None = None,
        client: object | None = None,
        **_ignored: object,
    ) -> None:
        resolved_index = index_name or os.getenv("PINECONE_INDEX", "")
        if not isinstance(resolved_index, str) or not resolved_index.strip():
            raise InvalidProviderConfigError(
                "Pinecone exige index_name (config local ou PINECONE_INDEX)."
            )
        if not isinstance(namespace, str) or not namespace.strip():
            raise InvalidProviderConfigError(
                "Pinecone exige namespace não vazio para isolar esta base."
            )
        resolved_key = api_key or os.getenv("PINECONE_API_KEY", "")
        if not resolved_key:
            raise MissingCredentialError(
                "Pinecone exige api_key na configuração ou PINECONE_API_KEY."
            )
        super().__init__(client=client)
        self._index_name = resolved_index.strip()
        self._namespace = namespace.strip()
        self._api_key = resolved_key

    def _create_backend(self) -> _PineconeBackend:
        return _PineconeBackend(self._index_name, self._namespace, self._api_key)
