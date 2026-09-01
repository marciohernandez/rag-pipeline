"""Backend falso compartilhado pela suíte de conformidade da SPEC-0003.

Implementa o mesmo *backend port* consumido por ``BaseVectorStoreAdapter``
(``ensure``/``scope_ids``/``write``/``remove``/``search``) e expõe atributos
observáveis para provar que nenhuma mutação remota acontece antes das guardas:

``ensure_ready_calls``, ``upsert_calls``, ``deleted_ids``, ``query_calls`` e
``confirmed_before_delete``. Os interruptores ``confirm_writes`` e
``fail_list_ids`` simulam destino que não confirma gravações e releitura de
escopo incompleta.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from src.providers.contracts import LogicalScope, SearchResult, VectorRecord
from src.providers.errors import UnreliableScopeReadError


class FakeVectorBackend:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str | None], dict[str, VectorRecord | None]] = {}
        self._legacy: dict[tuple[str, str | None], set[str]] = {}
        self._wrote = False
        # interruptores de cenário
        self.confirm_writes = True
        self.fail_list_ids = False
        self.fail_write = False
        # observabilidade
        self.ensure_ready_calls = 0
        self.upsert_calls: list[list[VectorRecord]] = []
        self.deleted_ids: list[str] = []
        self.query_calls: list[tuple[Sequence[float], int]] = []
        self.confirmed_before_delete = False

    @staticmethod
    def _key(scope: LogicalScope) -> tuple[str, str | None]:
        return (scope.project_id, scope.tenant_id)

    # preparação de cenário -------------------------------------------------
    def seed(self, scope: LogicalScope, ids: Iterable[str]) -> None:
        bucket = self._records.setdefault(self._key(scope), {})
        for identifier in ids:
            bucket.setdefault(identifier, None)

    def seed_legacy(self, scope: LogicalScope, ids: Iterable[str]) -> None:
        self._legacy.setdefault(self._key(scope), set()).update(ids)

    # backend port ----------------------------------------------------------
    def ensure(self, scope: LogicalScope, dimensions: int) -> None:
        self.ensure_ready_calls += 1
        self._records.setdefault(self._key(scope), {})

    def incompatible_ids(self, scope: LogicalScope) -> set[str]:
        return set(self._legacy.get(self._key(scope), set()))

    def scope_ids(self, scope: LogicalScope) -> set[str]:
        if self.fail_list_ids:
            raise UnreliableScopeReadError(
                "A releitura do escopo não pôde ser concluída; sincronização bloqueada."
            )
        if self._wrote and not self.deleted_ids:
            self.confirmed_before_delete = True
        return set(self._records.get(self._key(scope), {}))

    def write(self, scope: LogicalScope, records: Sequence[VectorRecord]) -> None:
        self.upsert_calls.append(list(records))
        if not records:
            return
        if self.fail_write:
            raise RuntimeError("falha de rede simulada")
        self._wrote = True
        if not self.confirm_writes:
            return
        bucket = self._records.setdefault(self._key(scope), {})
        for record in records:
            bucket[record.id] = record

    def remove(self, scope: LogicalScope, ids: Iterable[str]) -> None:
        identifiers = list(ids)
        self.deleted_ids.extend(identifiers)
        bucket = self._records.get(self._key(scope), {})
        for identifier in identifiers:
            bucket.pop(identifier, None)

    def search(
        self, scope: LogicalScope, embedding: Sequence[float], k: int
    ) -> list[SearchResult]:
        self.query_calls.append((list(embedding), k))
        bucket = self._records.get(self._key(scope), {})
        results: list[SearchResult] = []
        for identifier, record in list(bucket.items())[: max(k, 0)]:
            content = record.content if record is not None else identifier
            metadata = record.metadata if record is not None else {"chunk_id": identifier}
            results.append(SearchResult(content=content, metadata=metadata, score=1.0))
        return results
