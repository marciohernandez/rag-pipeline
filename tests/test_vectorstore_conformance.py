"""Suíte de conformidade de vector store — TDD informado pelo BDD da SPEC-0003.

AC-004: todos os vector stores passam pelo núcleo completo (``ensure_ready``,
``list_ids``, ``upsert``, ``query``) com dependências falsas; nenhuma asserção
do núcleo é pulada e somente Qdrant e in-memory executam a extensão ``mirror``.

Casos adicionais das demais fatias (AC-006, AC-008..AC-011) são acrescentados a
este arquivo pelas tarefas seguintes. Enquanto ``src/providers/`` não existir,
cada caso falha por comportamento ausente.
"""

from __future__ import annotations

import pytest

CORE_METHODS = ("ensure_ready", "list_ids", "upsert", "query")
BACKENDS = ("in_memory", "qdrant", "chroma", "pinecone")
MIRROR_CAPABLE = {"in_memory", "qdrant"}
DIMENSIONS = 8


def _make_adapter(name: str):
    """Cria o adapter alvo com cliente falso injetado.

    O seam ``settings['client']`` é resolvido pela implementação GREEN
    (T024..T027); o adapter ``in_memory`` não usa SDK e ignora o cliente.
    """
    from tests._fakes_vectorstore import FakeVectorBackend  # RED: helper ainda não existe

    from src.providers.factory import ProviderFactory

    settings = {
        "collection_name": "conformidade",
        "index_name": "conformidade",
        "namespace": "ns",
        "url": "http://localhost:6333",
        "api_key": "seg-teste",
        "client": FakeVectorBackend(),
    }
    return ProviderFactory.create_vector_store(name, settings)


def _scope(project_id: str = "projeto", tenant_id: str | None = None):
    from src.providers.contracts import LogicalScope

    return LogicalScope(project_id=project_id, tenant_id=tenant_id)


def _record(record_id: str):
    from src.providers.contracts import VectorRecord

    return VectorRecord(
        id=record_id,
        content=f"conteúdo {record_id}",
        vector=[0.1] * DIMENSIONS,
        metadata={"chunk_id": record_id},
    )


@pytest.mark.parametrize("name", BACKENDS)
def test_nucleo_completo_sem_asssercao_pulada(name) -> None:
    # SPECSFY: US-001 US-002 FR-001 FR-002 FR-003 FR-008 NFR-003 NFR-004 AC-004
    from src.providers.contracts import SearchResult

    adapter = _make_adapter(name)
    scope = _scope()

    exercised = set()

    adapter.ensure_ready(scope, dimensions=DIMENSIONS)
    adapter.ensure_ready(scope, dimensions=DIMENSIONS)  # idempotente
    exercised.add("ensure_ready")

    assert adapter.list_ids(scope) == set()
    exercised.add("list_ids")

    adapter.upsert(scope, [_record("r1"), _record("r2")])
    exercised.add("upsert")
    assert adapter.list_ids(scope) == {"r1", "r2"}

    resultados = adapter.query(scope, [0.1] * DIMENSIONS, k=2)
    exercised.add("query")
    assert resultados and all(isinstance(item, SearchResult) for item in resultados)
    assert all(hasattr(item, "score") and hasattr(item, "content") for item in resultados)

    assert exercised == set(CORE_METHODS)


@pytest.mark.parametrize("name", BACKENDS)
def test_consulta_isola_por_escopo_logico(name) -> None:
    # SPECSFY: US-001 US-002 FR-001 FR-002 FR-003 FR-008 NFR-003 NFR-004 AC-004
    adapter = _make_adapter(name)
    escopo_a = _scope("projeto-a")
    escopo_b = _scope("projeto-b")

    adapter.ensure_ready(escopo_a, dimensions=DIMENSIONS)
    adapter.ensure_ready(escopo_b, dimensions=DIMENSIONS)
    adapter.upsert(escopo_a, [_record("somente-a")])

    assert adapter.list_ids(escopo_a) == {"somente-a"}
    assert adapter.list_ids(escopo_b) == set()


@pytest.mark.parametrize("name", BACKENDS)
def test_extensao_mirror_somente_em_qdrant_e_in_memory(name) -> None:
    # SPECSFY: US-001 US-002 FR-001 FR-002 FR-003 FR-008 NFR-003 NFR-004 AC-004
    adapter = _make_adapter(name)
    scope = _scope()
    adapter.ensure_ready(scope, dimensions=DIMENSIONS)
    adapter.upsert(scope, [_record("r1"), _record("r2")])

    if name in MIRROR_CAPABLE:
        assert adapter.capabilities().supports_mirror is True
        adapter.delete_ids(scope, ["r1"])
        assert adapter.list_ids(scope) == {"r2"}
    else:
        assert adapter.capabilities().supports_mirror is False
        assert not hasattr(adapter, "delete_ids")


# ─────────────────────────────────────────────
# AC-006 — Reexecução append com contagens exatas (T009)
# ─────────────────────────────────────────────

APPEND_BACKENDS = ("chroma", "pinecone")


@pytest.mark.parametrize("name", APPEND_BACKENDS)
def test_reexecucao_append_sem_mudanca_zera_insercoes_e_remocoes(name) -> None:
    # SPECSFY: US-002 FR-004 FR-005 FR-008 NFR-002 NFR-004 AC-006
    from src.providers import synchronize
    from src.providers.contracts import SyncCounts

    adapter = _make_adapter(name)
    scope = _scope()
    registros = [_record("r1"), _record("r2"), _record("r3")]

    primeira = synchronize(adapter, scope, registros, mode="append")
    assert isinstance(primeira, SyncCounts)
    assert (primeira.previstos, primeira.inseridos, primeira.removidos) == (3, 3, 0)

    segunda = synchronize(adapter, scope, registros, mode="append")
    assert segunda.previstos == 3
    assert segunda.inseridos == 0
    assert segunda.mantidos == 3
    assert segunda.removidos == 0
    assert adapter.list_ids(scope) == {"r1", "r2", "r3"}


# ─────────────────────────────────────────────
# AC-008 — ChromaDB novo não duplica (T011)
# ─────────────────────────────────────────────


def test_chroma_destino_novo_usa_chunk_id_e_nao_cresce_na_segunda_execucao() -> None:
    # SPECSFY: US-002 FR-004 FR-005 FR-008 NFR-002 NFR-004 AC-008
    from src.providers import synchronize

    adapter = _make_adapter("chroma")
    scope = _scope()
    registros = [_record("chunk-a"), _record("chunk-b")]

    synchronize(adapter, scope, registros, mode="append")
    apos_primeira = adapter.list_ids(scope)

    synchronize(adapter, scope, registros, mode="append")
    apos_segunda = adapter.list_ids(scope)

    assert apos_primeira == {"chunk-a", "chunk-b"}
    assert apos_segunda == apos_primeira


# ─────────────────────────────────────────────
# AC-009 — Legado ou releitura não confiável bloqueia (T012)
# ─────────────────────────────────────────────


def test_chroma_com_ids_legados_incompativeis_bloqueia_antes_do_upsert() -> None:
    # SPECSFY: US-002 FR-004 FR-005 FR-006 FR-008 NFR-001 NFR-002 NFR-004 AC-009
    from tests._fakes_vectorstore import FakeVectorBackend

    from src.providers import synchronize
    from src.providers.errors import LegacyDestinationError

    backend = FakeVectorBackend()
    backend.seed_legacy(_scope(), ["id-fora-do-padrao-chunk_id"])
    from src.providers.factory import ProviderFactory

    adapter = ProviderFactory.create_vector_store(
        "chroma",
        {"collection_name": "legado", "persist_directory": "/tmp/none", "client": backend},
    )

    with pytest.raises(LegacyDestinationError) as excinfo:
        synchronize(adapter, _scope(), [_record("chunk-a")], mode="append")

    assert "destino" in str(excinfo.value).lower()
    assert backend.upsert_calls == []


def test_releitura_incompleta_do_escopo_bloqueia_sem_contagem_aproximada() -> None:
    # SPECSFY: US-002 FR-004 FR-005 FR-006 FR-008 NFR-001 NFR-002 NFR-004 AC-009
    from tests._fakes_vectorstore import FakeVectorBackend

    from src.providers import synchronize
    from src.providers.errors import UnreliableScopeReadError
    from src.providers.factory import ProviderFactory

    backend = FakeVectorBackend()
    backend.fail_list_ids = True
    adapter = ProviderFactory.create_vector_store(
        "pinecone",
        {"index_name": "i", "namespace": "ns", "api_key": "pc", "client": backend},
    )

    with pytest.raises(UnreliableScopeReadError):
        synchronize(adapter, _scope(), [_record("chunk-a")], mode="append")

    assert backend.upsert_calls == []


# ─────────────────────────────────────────────
# AC-010 — Consulta isolada por tenant (T013)
# ─────────────────────────────────────────────


@pytest.mark.parametrize("name", BACKENDS)
def test_query_retorna_somente_o_tenant_solicitado(name) -> None:
    # SPECSFY: US-003 FR-006 FR-007 FR-008 NFR-001 NFR-003 NFR-004 AC-010
    adapter = _make_adapter(name)
    escopo_a = _scope("projeto", "cliente-a")
    escopo_b = _scope("projeto", "cliente-b")

    adapter.ensure_ready(escopo_a, dimensions=DIMENSIONS)
    adapter.upsert(escopo_a, [_record("a1")])
    adapter.upsert(escopo_b, [_record("b1")])

    resultados = adapter.query(escopo_a, [0.1] * DIMENSIONS, k=10)
    assert {item.metadata["chunk_id"] for item in resultados} == {"a1"}


def test_query_aceita_apenas_escopo_logico_sem_filtro_de_sdk() -> None:
    # SPECSFY: US-003 FR-006 FR-007 FR-008 NFR-001 NFR-003 NFR-004 AC-010
    import inspect

    from src.providers.factory import ProviderFactory

    adapter = ProviderFactory.create_vector_store("in_memory", {})
    parametros = set(inspect.signature(adapter.query).parameters)
    assert parametros <= {"scope", "embedding", "k"}
    assert "filter" not in parametros and "where" not in parametros


# ─────────────────────────────────────────────
# AC-011 — Ausência de tenant é escopo estrito (T014)
# ─────────────────────────────────────────────


@pytest.mark.parametrize("name", BACKENDS)
def test_query_sem_tenant_alcanca_somente_registros_sem_tenant(name) -> None:
    # SPECSFY: US-003 FR-006 FR-007 FR-008 NFR-001 NFR-003 NFR-004 AC-011
    adapter = _make_adapter(name)
    escopo_com_tenant = _scope("projeto", "cliente-a")
    escopo_sem_tenant = _scope("projeto", None)

    adapter.ensure_ready(escopo_sem_tenant, dimensions=DIMENSIONS)
    adapter.upsert(escopo_com_tenant, [_record("com-tenant")])
    adapter.upsert(escopo_sem_tenant, [_record("sem-tenant")])

    resultados = adapter.query(escopo_sem_tenant, [0.1] * DIMENSIONS, k=10)
    ids = {item.metadata["chunk_id"] for item in resultados}
    assert ids == {"sem-tenant"}
    assert "com-tenant" not in ids  # omitir tenant_id não equivale a omitir o filtro
