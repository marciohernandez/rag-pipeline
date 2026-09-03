"""Núcleo comum dos vector stores e o serviço de sincronização (SPEC-0003).

``BaseVectorStoreAdapter`` implementa o contrato neutro delegando a um *backend
port* (``ensure``/``scope_ids``/``write``/``remove``/``search``). O backend real
é criado sob demanda por cada adapter; nos testes um backend falso é injetado
por ``settings['client']``.

``synchronize`` orquestra a sincronização: valida modo e lote pela
``SyncSafetyPolicy`` (SPEC-0001) antes de qualquer acesso ao destino, calcula os
conjuntos exatos e emite ``SyncCounts`` com as quatro contagens.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Sequence
from dataclasses import replace

from src.providers.contracts import (
    LogicalScope,
    ProviderCapabilities,
    SearchResult,
    SyncCounts,
    VectorRecord,
)
from src.providers.errors import InvalidScopeError
from src.safety import SyncSafetyPolicy, UnsupportedSyncModeError

logger = logging.getLogger("src.providers.vectorstores")

_REAL_PROVIDERS = frozenset({"qdrant", "chroma", "pinecone"})


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    """Similaridade de cosseno; 0.0 quando algum vetor é nulo ou incompatível."""
    if len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm_left = sum(a * a for a in left) ** 0.5
    norm_right = sum(b * b for b in right) ** 0.5
    if not norm_left or not norm_right:
        return 0.0
    return float(dot / (norm_left * norm_right))


class DictVectorBackend:
    """Backend em memória, sem SDK. Referência do núcleo e do mirror."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str | None], dict[str, VectorRecord]] = {}
        self._dimensions: dict[tuple[str, str | None], int] = {}

    @staticmethod
    def _key(scope: LogicalScope) -> tuple[str, str | None]:
        return (scope.project_id, scope.tenant_id)

    def ensure(self, scope: LogicalScope, dimensions: int) -> None:
        self._records.setdefault(self._key(scope), {})
        self._dimensions.setdefault(self._key(scope), dimensions)

    def describe(self, scope: LogicalScope) -> dict:
        """Leitura pura: escopo ausente devolve mapa vazio, sem criar nada."""
        key = self._key(scope)
        if key not in self._records:
            return {}
        dimensions = self._dimensions.get(key)
        if dimensions is None:
            for record in self._records[key].values():
                if record is not None and record.vector:
                    dimensions = len(record.vector)
                    break
        return {"exists": True, "dimensions": dimensions}

    def scope_ids(self, scope: LogicalScope) -> set[str]:
        return set(self._records.get(self._key(scope), {}))

    def write(self, scope: LogicalScope, records: Sequence[VectorRecord]) -> None:
        bucket = self._records.setdefault(self._key(scope), {})
        for record in records:
            bucket[record.id] = record

    def remove(self, scope: LogicalScope, ids: Iterable[str]) -> None:
        bucket = self._records.get(self._key(scope), {})
        for identifier in ids:
            bucket.pop(identifier, None)

    def search(
        self, scope: LogicalScope, embedding: Sequence[float], k: int
    ) -> list[SearchResult]:
        bucket = self._records.get(self._key(scope), {})
        ranked = sorted(
            ((_cosine(embedding, record.vector), record) for record in bucket.values()),
            key=lambda item: item[0],
            reverse=True,
        )
        return [
            SearchResult(content=record.content, metadata=record.metadata, score=score)
            for score, record in ranked[: max(k, 0)]
        ]


class BaseVectorStoreAdapter:
    """Implementa o contrato neutro sobre um backend port."""

    provider: str = "base"

    def __init__(self, *, client: object | None = None, **_ignored: object) -> None:
        self._injected_backend = client
        self._backend: object | None = None

    # backend ------------------------------------------------------------
    def _create_backend(self):  # pragma: no cover - sobrescrito pelos adapters reais
        raise NotImplementedError

    def _resolve_backend(self):
        if self._backend is None:
            self._backend = (
                self._injected_backend
                if self._injected_backend is not None
                else self._create_backend()
            )
        return self._backend

    # contrato ---------------------------------------------------------------
    def ensure_ready(self, scope: LogicalScope, *, dimensions: int) -> None:
        self._resolve_backend().ensure(scope, dimensions)

    def describe_scope(self, scope: LogicalScope) -> dict:
        """Delegação da leitura de metadados; nunca prepara o destino."""
        return dict(self._resolve_backend().describe(scope))

    def list_ids(self, scope: LogicalScope) -> set[str]:
        return set(self._resolve_backend().scope_ids(scope))

    def upsert(self, scope: LogicalScope, records: Sequence[VectorRecord]) -> None:
        self._resolve_backend().write(scope, list(records))

    def query(
        self, scope: LogicalScope, embedding: Sequence[float], k: int
    ) -> list[SearchResult]:
        return list(self._resolve_backend().search(scope, embedding, k))

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            name=self.provider, supports_mirror=isinstance(self, MirrorMixin)
        )


class MirrorMixin:
    """Adiciona a extensão destrutiva ``delete_ids`` aos adapters capazes."""

    def delete_ids(self, scope: LogicalScope, ids: Iterable[str]) -> None:
        self._resolve_backend().remove(scope, list(ids))  # type: ignore[attr-defined]


# ─────────────────────────────────────────────
# Serviço de sincronização
# ─────────────────────────────────────────────


def _validate_mode(adapter, mode: str, policy: SyncSafetyPolicy) -> None:
    if adapter.provider in _REAL_PROVIDERS:
        policy.assert_sync_mode_supported(adapter.provider, mode)
    elif mode not in {"append", "mirror"}:
        raise UnsupportedSyncModeError(f"Modo de sincronização não suportado: {mode!r}.")
    if mode == "mirror" and not adapter.capabilities().supports_mirror:
        raise UnsupportedSyncModeError(
            f"O provider {adapter.provider!r} não oferece a garantia de escopo "
            "exigida pelo modo mirror; use append."
        )


def _validate_batch(scope: LogicalScope, records: Sequence[VectorRecord]) -> None:
    if not records:
        raise InvalidScopeError(
            "O conjunto de registros está vazio; sincronização bloqueada."
        )
    ids = [record.id for record in records]
    if any(not isinstance(identifier, str) or not identifier.strip() for identifier in ids):
        raise InvalidScopeError(
            "O lote contém registro com chunk_id ausente ou vazio; "
            "sincronização bloqueada."
        )
    if len(ids) != len(set(ids)):
        raise InvalidScopeError(
            "O lote contém id duplicado; sincronização bloqueada."
        )
    tenants: set[str] = set()
    sem_tenant = False
    for record in records:
        raw = record.metadata.get("tenant_id")
        tenant = raw.strip() if isinstance(raw, str) else ""
        if tenant:
            tenants.add(tenant)
        else:
            sem_tenant = True
    if tenants and sem_tenant:
        raise InvalidScopeError(
            "O lote mistura registros com e sem tenant_id; sincronização bloqueada."
        )
    if len(tenants) > 1:
        raise InvalidScopeError(
            "O lote possui tenant_id divergentes; sincronização bloqueada."
        )
    if tenants and scope.tenant_id is not None and next(iter(tenants)) != scope.tenant_id:
        raise InvalidScopeError(
            "O tenant_id dos registros diverge do escopo lógico informado."
        )


def synchronize(
    adapter,
    scope: LogicalScope,
    records: Iterable[VectorRecord],
    *,
    mode: str = "append",
    safety_policy: SyncSafetyPolicy | None = None,
    dimensions: int | None = None,
    embed: Callable[[list[str]], list[Sequence[float]]] | None = None,
) -> SyncCounts:
    """Sincroniza ``records`` no ``adapter`` e devolve contagens exatas.

    Quando ``embed`` é informado, os vetores são gerados somente para os
    registros realmente ausentes no destino, preservando o custo observado no
    comportamento anterior; nesse caso ``dimensions`` é obrigatório porque os
    registros chegam sem vetor.
    """

    records = list(records)
    policy = safety_policy or SyncSafetyPolicy()

    _validate_mode(adapter, mode, policy)
    _validate_batch(scope, records)

    if dimensions is None:
        dimensions = len(records[0].vector)
    adapter.ensure_ready(scope, dimensions=dimensions)

    existing = set(adapter.list_ids(scope))
    expected = {record.id for record in records}
    to_insert = [record for record in records if record.id not in existing]

    if embed is not None and to_insert:
        vectors = embed([record.content for record in to_insert])
        to_insert = [
            replace(record, vector=list(vector))
            for record, vector in zip(to_insert, vectors, strict=True)
        ]

    adapter.upsert(scope, to_insert)

    removidos = 0
    if mode == "mirror":
        confirmed = set(adapter.list_ids(scope))
        policy.assert_removal_allowed(expected, confirmed)
        stale = sorted(existing - expected)
        if stale:
            adapter.delete_ids(scope, stale)
        removidos = len(stale)

    counts = SyncCounts(
        previstos=len(expected),
        inseridos=len(to_insert),
        mantidos=len(expected & existing),
        removidos=removidos,
    )
    logger.info(
        "Sincronizacao concluida: modo=%s escopo=%s previstos=%d inseridos=%d "
        "mantidos=%d removidos=%d",
        mode,
        scope.project_id,
        counts.previstos,
        counts.inseridos,
        counts.mantidos,
        counts.removidos,
    )
    return counts
