"""Contratos neutros de fornecedor para embeddings e vector stores (SPEC-0003).

Nenhum tipo aqui depende de SDK. Consumidores e o serviço de sincronização
conhecem apenas estes value objects e Protocols; a Factory devolve adapters que
os satisfazem.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from src.pipeline.providers.errors import InvalidScopeError


def _clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


@dataclass(frozen=True)
class LogicalScope:
    """Escopo lógico de uma operação.

    ``project_id`` é obrigatório. ``tenant_id`` é opcional e estrito: quando
    ``None`` a operação alcança somente registros sem tenant — omitir o tenant
    nunca equivale a omitir o filtro. ``document_id`` (SPEC-0030) restringe a
    operação aos registros de um único documento dentro do escopo.
    """

    project_id: str
    tenant_id: str | None = None
    document_id: str | None = None

    def __post_init__(self) -> None:
        project = _clean(self.project_id)
        if not project:
            raise InvalidScopeError(
                "project_id é obrigatório e não pode ser vazio para sincronizar ou recuperar."
            )
        object.__setattr__(self, "project_id", project)
        tenant = _clean(self.tenant_id) if self.tenant_id is not None else ""
        object.__setattr__(self, "tenant_id", tenant or None)
        documento = _clean(self.document_id) if self.document_id is not None else ""
        object.__setattr__(self, "document_id", documento or None)


@dataclass(frozen=True)
class VectorRecord:
    """Registro independente de SDK a ser gravado em um vector store."""

    id: str
    content: str
    vector: Sequence[float]
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    """Resultado neutro de uma consulta de similaridade."""

    content: str
    metadata: Mapping[str, object]
    score: float


@dataclass(frozen=True)
class SyncCounts:
    """Contagens exatas e não negativas de uma sincronização concluída."""

    previstos: int
    inseridos: int
    mantidos: int
    removidos: int

    def __post_init__(self) -> None:
        for name in ("previstos", "inseridos", "mantidos", "removidos"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"SyncCounts.{name} deve ser inteiro não negativo.")


@dataclass(frozen=True)
class ProviderCapabilities:
    """Capacidades declaradas por um adapter, orientando a Strategy."""

    name: str
    supports_mirror: bool = False


@runtime_checkable
class EmbeddingAdapter(Protocol):
    """Contrato comum dos providers de embeddings."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


@runtime_checkable
class VectorStoreAdapter(Protocol):
    """Núcleo obrigatório de cada vector store.

    ``describe_scope`` é leitura pura de metadados do escopo: devolve existência
    e dimensão declaradas pelo destino, ou um mapa vazio quando o escopo não
    existe. Ela nunca cria, altera ou remove — ao contrário de ``ensure_ready``,
    que prepara o destino e cria a coleção ausente.
    """

    def ensure_ready(self, scope: LogicalScope, *, dimensions: int) -> None: ...

    def describe_scope(self, scope: LogicalScope) -> Mapping[str, object]: ...

    def list_ids(self, scope: LogicalScope) -> set[str]: ...

    def upsert(self, scope: LogicalScope, records: Sequence[VectorRecord]) -> None: ...

    def query(
        self, scope: LogicalScope, embedding: Sequence[float], k: int
    ) -> list[SearchResult]: ...

    def capabilities(self) -> ProviderCapabilities: ...


@runtime_checkable
class MirrorCapableVectorStore(VectorStoreAdapter, Protocol):
    """Extensão destrutiva disponível somente em adapters com garantia de escopo."""

    def delete_ids(self, scope: LogicalScope, ids: Iterable[str]) -> None: ...


@dataclass(frozen=True)
class ChatImage:
    """Imagem do documento, codificada em base64; sem endereço remoto."""

    base64: str
    mime_type: str = "image/png"


@dataclass(frozen=True)
class ChatMessage:
    """Mensagem neutra enviada a um modelo de linguagem.

    ``papel`` é ``sistema``, ``pessoa`` ou ``assistente``; cada adapter traduz
    esses nomes para o vocabulário do seu SDK.
    """

    papel: str
    conteudo: str
    imagens: tuple[ChatImage, ...] = ()


@runtime_checkable
class ChatModelAdapter(Protocol):
    """Contrato comum dos providers de modelo de linguagem para chat.

    O adapter não expõe ferramentas: o assistente apenas orienta (SPEC-0021,
    FR-008). Falhas do provedor sobem como ``ChatProviderError`` sem detalhe
    interno nem credencial.
    """

    def responder(self, mensagens: Sequence[ChatMessage], timeout: float | None = None) -> str: ...
