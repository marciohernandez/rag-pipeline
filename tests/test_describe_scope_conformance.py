"""Conformidade de `describe_scope` — TDD da SPEC-0004.

Arquivo próprio, e não `tests/test_vectorstore_conformance.py`, porque aquele
carrega marcadores da SPEC-0003 cujos IDs coincidem com os desta fatia.

A leitura de metadados do escopo é a única forma de o preflight conferir
existência e dimensão sem `ensure_ready`, que cria a coleção ausente.
"""

from __future__ import annotations

import pytest

BACKENDS = ("in_memory", "qdrant", "chroma", "pinecone")
DIMENSIONS = 8


def _make_adapter(name: str):
    from tests._fakes_vectorstore import FakeVectorBackend

    from src.providers.factory import ProviderFactory

    backend = FakeVectorBackend()
    backend.declared_dimensions = DIMENSIONS
    settings = {
        "collection_name": "conformidade",
        "index_name": "conformidade",
        "namespace": "ns",
        "url": "http://localhost:6333",
        "api_key": "seg-teste",
        "client": backend,
    }
    return ProviderFactory.create_vector_store(name, settings), backend


def _scope(project_id: str = "projeto", tenant_id: str | None = None):
    from src.providers.contracts import LogicalScope

    return LogicalScope(project_id=project_id, tenant_id=tenant_id)


@pytest.mark.parametrize("name", BACKENDS)
def test_describe_scope_declara_a_dimensao_do_escopo_existente(name) -> None:
    # SPECSFY: FR-002 NFR-002 AC-003 AC-016
    adapter, backend = _make_adapter(name)
    scope = _scope()
    backend.seed(scope, {"r1"})

    metadados = adapter.describe_scope(scope)

    assert metadados.get("exists") is True
    assert metadados.get("dimensions") == DIMENSIONS


@pytest.mark.parametrize("name", BACKENDS)
def test_describe_scope_de_escopo_ausente_devolve_vazio(name) -> None:
    # SPECSFY: FR-002 NFR-002 AC-003 AC-016
    adapter, _backend = _make_adapter(name)

    assert not adapter.describe_scope(_scope("projeto-inexistente"))


@pytest.mark.parametrize("name", BACKENDS)
def test_describe_scope_nao_prepara_nem_escreve_no_destino(name) -> None:
    # SPECSFY: FR-002 NFR-001 AC-003 AC-013
    adapter, backend = _make_adapter(name)
    scope = _scope()

    adapter.describe_scope(scope)
    backend.seed(scope, {"r1"})
    adapter.describe_scope(scope)

    assert backend.ensure_ready_calls == 0
    assert backend.upsert_calls == []
    assert backend.deleted_ids == []
