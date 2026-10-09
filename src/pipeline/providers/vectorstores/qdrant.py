"""Adapter de vector store Qdrant (SPEC-0003).

Validação local no construtor; o cliente Qdrant só é criado no primeiro acesso
ao destino. Preserva a seleção de porta HTTP(S) do helper atual, a paginação
completa do escopo lógico, o payload (`page_content` + `metadata`), a dimensão,
a distância COSINE e o espelho idempotente.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from urllib.parse import urlsplit

from src.pipeline.providers.contracts import LogicalScope, SearchResult, VectorRecord
from src.pipeline.providers.errors import InvalidProviderConfigError, UnreliableScopeReadError
from src.pipeline.providers.vectorstores.base import BaseVectorStoreAdapter, MirrorMixin

_PAGE = 256

# Limite de pontos por requisição de upsert. Um único POST com centenas de
# vetores de 1536 dimensões estoura o timeout de escrita do SDK em endpoints
# atrás de proxy; lotear mantém cada requisição pequena e previsível.
_UPSERT_BATCH = 64

# O ``qdrant-client`` 1.10.1 usa 5s de timeout no cliente REST, curto demais
# para escrita/leitura em endpoints publicados por proxy. 60s dá folga sem
# mascarar um destino realmente indisponível.
_CLIENT_TIMEOUT = 60


def testar_acesso(url: str, api_key: str | None) -> dict:
    """Lista as coleções para testar URL e chave, sem criar nada (SPEC-0029).

    Devolve só mensagens próprias, nunca o texto da exceção, para que a chave
    não vaze em respostas ou logs.
    """
    from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

    try:
        _build_client(url, api_key).get_collections()
    except UnexpectedResponse as erro:
        if erro.status_code == 401 and not api_key:
            return {"sucesso": False, "mensagem": "O servidor exige uma chave de API."}
        if erro.status_code in (401, 403):
            return {"sucesso": False, "mensagem": "O servidor recusou a chave informada."}
        return {"sucesso": False, "mensagem": f"O servidor respondeu com erro {erro.status_code}."}
    except (ResponseHandlingException, OSError, TimeoutError):
        return {"sucesso": False, "mensagem": "Não foi possível alcançar o servidor."}
    except Exception as erro:  # noqa: BLE001 - httpx e o SDK não têm base comum de rede
        if type(erro).__module__.startswith("httpx"):
            return {"sucesso": False, "mensagem": "Não foi possível alcançar o servidor."}
        return {"sucesso": False, "mensagem": "Não foi possível testar a conexão."}
    return {"sucesso": True, "mensagem": "Conexão testada com sucesso."}


def _build_client(url: str, api_key: str | None):
    """Cria o cliente respeitando a porta indicada pela URL.

    O ``qdrant-client`` 1.10.1 usa 6333 como padrão mesmo em HTTPS; para
    endpoints publicados por proxy sem porta explícita usamos a porta padrão do
    protocolo (443 em HTTPS, 80 em HTTP).
    """
    from qdrant_client import QdrantClient

    parsed = urlsplit(url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return QdrantClient(
        url=url,
        port=port,
        https=parsed.scheme == "https",
        api_key=api_key or None,
        timeout=_CLIENT_TIMEOUT,
    )


class _QdrantBackend:
    """Backend port sobre o SDK do Qdrant."""

    def __init__(self, collection: str, url: str, api_key: str | None) -> None:
        self._collection = collection
        self._url = url
        self._api_key = api_key
        self._client = None

    def _conn(self):
        if self._client is None:
            self._client = _build_client(self._url, self._api_key)
        return self._client

    def _scope_filter(self, scope: LogicalScope):
        from qdrant_client.http.models import FieldCondition, Filter, MatchValue

        conditions = [
            FieldCondition(key="metadata.project_id", match=MatchValue(value=scope.project_id))
        ]
        if scope.tenant_id is not None:
            conditions.append(
                FieldCondition(key="metadata.tenant_id", match=MatchValue(value=scope.tenant_id))
            )
        return Filter(must=conditions)

    def ensure(self, scope: LogicalScope, dimensions: int) -> None:
        from qdrant_client.http.models import Distance, VectorParams

        client = self._conn()
        existing = {item.name for item in client.get_collections().collections}
        if self._collection not in existing:
            client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=dimensions, distance=Distance.COSINE),
            )

    def describe(self, scope: LogicalScope) -> dict:
        """Lê os metadados da coleção sem criá-la.

        Contraste deliberado com ``ensure``, que chama ``create_collection``
        quando a coleção não existe: aqui, coleção ausente ou destino
        inacessível devolvem mapa vazio e o preflight decide o impedimento.
        """
        try:
            info = self._conn().get_collection(collection_name=self._collection)
        except Exception:  # noqa: BLE001 - SDK não expõe erro comum de inspeção
            return {}
        params = getattr(getattr(info, "config", None), "params", None)
        vectors = getattr(params, "vectors", None)
        size = getattr(vectors, "size", None)
        if size is None and isinstance(vectors, dict):
            declared = {getattr(item, "size", None) for item in vectors.values()}
            size = declared.pop() if len(declared) == 1 else None
        return {"exists": True, "dimensions": size}

    def scope_ids(self, scope: LogicalScope) -> set[str]:
        client = self._conn()
        found: set[str] = set()
        offset = None
        while True:
            try:
                records, offset = client.scroll(
                    collection_name=self._collection,
                    scroll_filter=self._scope_filter(scope),
                    limit=_PAGE,
                    offset=offset,
                    with_payload=False,
                    with_vectors=False,
                )
            except Exception as error:  # releitura incompleta bloqueia a sincronização
                raise UnreliableScopeReadError(
                    "A releitura paginada do escopo no Qdrant falhou; sincronização bloqueada."
                ) from error
            found.update(str(record.id) for record in records)
            if offset is None:
                return found

    def write(self, scope: LogicalScope, records: Sequence[VectorRecord]) -> None:
        if not records:
            return
        from qdrant_client.http.models import PointStruct

        points = [
            PointStruct(
                id=record.id,
                vector=list(record.vector),
                payload={
                    "page_content": record.content,
                    "metadata": dict(record.metadata),
                },
            )
            for record in records
        ]
        client = self._conn()
        for start in range(0, len(points), _UPSERT_BATCH):
            client.upsert(
                collection_name=self._collection,
                points=points[start : start + _UPSERT_BATCH],
                wait=True,
            )

    def remove(self, scope: LogicalScope, ids: Iterable[str]) -> None:
        from qdrant_client.http.models import PointIdsList

        identifiers = list(ids)
        if not identifiers:
            return
        self._conn().delete(
            collection_name=self._collection,
            points_selector=PointIdsList(points=identifiers),
            wait=True,
        )

    def search(self, scope: LogicalScope, embedding: Sequence[float], k: int) -> list[SearchResult]:
        hits = self._conn().search(
            collection_name=self._collection,
            query_vector=list(embedding),
            query_filter=self._scope_filter(scope),
            limit=k,
            with_payload=True,
        )
        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                SearchResult(
                    content=payload.get("page_content", ""),
                    metadata=payload.get("metadata", {}),
                    score=float(getattr(hit, "score", 0.0)),
                )
            )
        return results


class QdrantVectorStoreAdapter(MirrorMixin, BaseVectorStoreAdapter):
    provider = "qdrant"

    def __init__(
        self,
        *,
        collection_name: str | None = None,
        url: str | None = None,
        api_key: str | None = None,
        client: object | None = None,
        **_ignored: object,
    ) -> None:
        if not isinstance(collection_name, str) or not collection_name.strip():
            raise InvalidProviderConfigError("Qdrant exige collection_name não vazio.")
        resolved_url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        parsed = urlsplit(resolved_url or "")
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise InvalidProviderConfigError(
                "Qdrant exige uma URL HTTP(S) válida, por exemplo https://qdrant.example.com."
            )
        super().__init__(client=client)
        self._collection = collection_name.strip()
        self._url = resolved_url
        self._api_key = api_key or os.getenv("QDRANT_API_KEY") or None

    def _create_backend(self) -> _QdrantBackend:
        return _QdrantBackend(self._collection, self._url, self._api_key)
