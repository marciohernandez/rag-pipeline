"""Sincronização Qdrant sobre os contratos neutros.

Este arquivo preserva as garantias da SPEC-0001 (espelho idempotente, remoção
apenas após confirmação, contagens auditáveis, isolamento por projeto e tenant,
log sem segredo) e acrescenta os casos da SPEC-0003 (AC-005).

Migrado em T033: os dublês com formato do SDK Qdrant foram substituídos pelo
``FakeVectorBackend`` neutro, injetado por ``settings['client']``. A entrada da
aplicação passou de ``src.embedder.index_chunks`` para
``src.indexing.index_chunks``.
"""

from __future__ import annotations

import logging
from uuid import uuid4

import pytest
from langchain_core.documents import Document

import src.indexing as indexing
from src.providers import synchronize
from src.providers.contracts import LogicalScope, SyncCounts, VectorRecord
from src.providers.factory import ProviderFactory
from tests._fakes_vectorstore import FakeVectorBackend


class FakeEmbeddings:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, _text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


def _chunk(chunk_id: str, *, project_id: str = "projeto", tenant_id: str | None = None) -> Document:
    metadata = {
        "project_id": project_id,
        "document_id": str(uuid4()),
        "chunk_id": chunk_id,
        "chunk_type": "detail",
    }
    if tenant_id is not None:
        metadata["tenant_id"] = tenant_id
    return Document(page_content="conteúdo", metadata=metadata)


def _config(sync_mode: str = "mirror") -> tuple[dict, dict]:
    return (
        {"provider": "openai", "model": "text-embedding-3-small", "dimensions": 3},
        {
            "provider": "qdrant",
            "collection_name": "collection",
            "sync_mode": sync_mode,
        },
    )


def _qdrant_adapter(backend: FakeVectorBackend):
    return ProviderFactory.create_vector_store(
        "qdrant",
        {"collection_name": "collection", "url": "http://localhost:6333", "client": backend},
    )


def _instalar(monkeypatch, backend: FakeVectorBackend, embeddings=None) -> FakeEmbeddings:
    """Substitui a composição de providers pelo backend/embeddings falsos."""
    embeddings = embeddings or FakeEmbeddings()
    adapter = _qdrant_adapter(backend)
    monkeypatch.setattr(indexing, "build_vector_store", lambda *_a, **_k: adapter)
    monkeypatch.setattr(indexing, "build_embeddings", lambda *_a, **_k: embeddings)
    return embeddings


def _scope(project_id: str = "projeto", tenant_id: str | None = None) -> LogicalScope:
    return LogicalScope(project_id=project_id, tenant_id=tenant_id)


def _removidos(backend: FakeVectorBackend) -> list[str]:
    return list(backend.deleted_ids)


# ═════════════════════════════════════════════════════════════════
# SPEC-0001 — garantias preservadas através do stack novo
# ═════════════════════════════════════════════════════════════════


def test_upserts_new_points_then_removes_only_stale_points(monkeypatch) -> None:
    # SPECSFY: US-001 FR-003 NFR-002 NFR-003 AC-004
    stale_id, current_id = str(uuid4()), str(uuid4())
    backend = FakeVectorBackend()
    backend.seed(_scope(), [stale_id])
    embeddings = _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _config()

    indexing.index_chunks([_chunk(current_id)], embedding_cfg, vector_cfg)

    assert [len(call) for call in backend.upsert_calls] == [1]
    assert embeddings.calls == [["conteúdo"]]
    assert _removidos(backend) == [stale_id]


def test_upsert_failure_never_removes_existing_points(monkeypatch) -> None:
    # SPECSFY: US-001 FR-003 FR-004 NFR-001 AC-005
    stale_id = str(uuid4())
    backend = FakeVectorBackend()
    backend.seed(_scope(), [stale_id])
    backend.fail_write = True
    _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _config()

    with pytest.raises(RuntimeError, match="falha de rede"):
        indexing.index_chunks([_chunk(str(uuid4()))], embedding_cfg, vector_cfg)

    assert _removidos(backend) == []


def test_reexecucao_identica_nao_altera_a_base_e_registra_contagens(
    monkeypatch, caplog
) -> None:
    # SPECSFY: US-001 FR-003 NFR-002 NFR-003 AC-004
    chunk_id = str(uuid4())
    backend = FakeVectorBackend()
    backend.seed(_scope(), [chunk_id])
    embeddings = _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _config()

    with caplog.at_level(logging.INFO):
        counts = indexing.index_chunks([_chunk(chunk_id)], embedding_cfg, vector_cfg)

    assert counts == SyncCounts(previstos=1, inseridos=0, mantidos=1, removidos=0)
    assert backend.upsert_calls == [[]]
    assert _removidos(backend) == []
    assert embeddings.calls == []  # nada a inserir, nada a embeddar
    registro = " ".join(item.getMessage().lower() for item in caplog.records)
    for termo in ("previstos", "inseridos", "mantidos", "removidos"):
        assert termo in registro


def test_espelho_nunca_le_nem_remove_pontos_de_outro_projeto(monkeypatch) -> None:
    # SPECSFY: US-001 US-002 FR-003 FR-004 NFR-002 NFR-003 AC-006 AC-018
    # Também cobre o AC-018 da SPEC-0002: lote sem tenant_id em nenhum chunk
    # preserva o filtro apenas por project_id na remoção de obsoletos.
    obsoleto, preservado, intocado = str(uuid4()), str(uuid4()), str(uuid4())
    backend = FakeVectorBackend()
    backend.seed(_scope("projeto"), [obsoleto, preservado])
    backend.seed(_scope("outro"), [intocado])
    _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _config()

    indexing.index_chunks(
        [_chunk(preservado), _chunk(str(uuid4()))], embedding_cfg, vector_cfg
    )

    removidos = _removidos(backend)
    assert removidos == [obsoleto]
    assert intocado not in removidos


def test_registro_da_sincronizacao_nao_expoe_segredos(monkeypatch, caplog) -> None:
    # SPECSFY: US-001 FR-003 FR-006 NFR-002 AC-010
    backend = FakeVectorBackend()
    backend.seed(_scope(), [str(uuid4())])
    _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _config()
    monkeypatch.setenv("QDRANT_URL", "https://destino-secreto.example")
    monkeypatch.setenv("QDRANT_API_KEY", "chave-secreta")

    with caplog.at_level(logging.INFO):
        indexing.index_chunks([_chunk(str(uuid4()))], embedding_cfg, vector_cfg)

    registro = " ".join(item.getMessage() for item in caplog.records)
    assert "projeto" in registro
    for termo in ("previstos", "inseridos", "mantidos", "removidos"):
        assert termo in registro.lower()
    assert "destino-secreto.example" not in registro
    assert "chave-secreta" not in registro


def test_limpeza_bloqueada_quando_o_destino_nao_confirma_os_esperados(
    monkeypatch,
) -> None:
    # SPECSFY: US-001 FR-003 FR-007 NFR-001 AC-014
    backend = FakeVectorBackend()
    backend.seed(_scope(), [str(uuid4())])
    backend.confirm_writes = False
    _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _config()

    with pytest.raises(ValueError, match="confirm"):
        indexing.index_chunks([_chunk(str(uuid4()))], embedding_cfg, vector_cfg)

    assert _removidos(backend) == []


def test_substituicao_total_do_escopo_permanece_permitida(monkeypatch) -> None:
    # SPECSFY: US-001 FR-003 FR-007 NFR-003 AC-015
    anterior_a, anterior_b = str(uuid4()), str(uuid4())
    backend = FakeVectorBackend()
    backend.seed(_scope(), [anterior_a, anterior_b])
    _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _config()

    novo_a, novo_b = str(uuid4()), str(uuid4())
    counts = indexing.index_chunks(
        [_chunk(novo_a), _chunk(novo_b)], embedding_cfg, vector_cfg
    )

    assert set(_removidos(backend)) == {anterior_a, anterior_b}
    assert counts == SyncCounts(previstos=2, inseridos=2, mantidos=0, removidos=2)


def test_espelho_com_tenant_id_nao_remove_pontos_de_outro_tenant(monkeypatch) -> None:
    # SPECSFY: US-002 FR-004 AC-007
    obsoleto_a, preservado_b = str(uuid4()), str(uuid4())
    backend = FakeVectorBackend()
    backend.seed(_scope("projeto", "cliente-a"), [obsoleto_a])
    backend.seed(_scope("projeto", "cliente-b"), [preservado_b])
    _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _config()

    indexing.index_chunks(
        [_chunk(str(uuid4()), tenant_id="cliente-a")], embedding_cfg, vector_cfg
    )

    removidos = _removidos(backend)
    assert obsoleto_a in removidos
    assert preservado_b not in removidos


def test_leitura_de_escopo_nao_inclui_pontos_de_outro_tenant_id(monkeypatch) -> None:
    # SPECSFY: US-002 FR-004 AC-024
    id_colidente = str(uuid4())
    backend = FakeVectorBackend()
    backend.seed(_scope("projeto", "cliente-b"), [id_colidente])
    _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _config()

    indexing.index_chunks(
        [_chunk(id_colidente, tenant_id="cliente-a")], embedding_cfg, vector_cfg
    )

    upsertados = {record.id for call in backend.upsert_calls for record in call}
    assert id_colidente in upsertados


def test_tenant_id_invalido_bloqueia_antes_de_cliente_ou_embedding(monkeypatch) -> None:
    # SPECSFY: US-002 FR-003 NFR-001 AC-025
    def _proibido(*_args, **_kwargs):
        raise AssertionError("provider não deveria ser composto")

    monkeypatch.setattr(indexing, "build_vector_store", _proibido)
    monkeypatch.setattr(indexing, "build_embeddings", _proibido)
    embedding_cfg, vector_cfg = _config()

    chunks = [
        _chunk(str(uuid4()), tenant_id="cliente-a"),
        _chunk(str(uuid4()), tenant_id="cliente-b"),
    ]

    with pytest.raises(ValueError):
        indexing.index_chunks(chunks, embedding_cfg, vector_cfg)


# ═════════════════════════════════════════════════════════════════
# SPEC-0003 — Sincronização Qdrant sobre os contratos neutros (T008)
# ═════════════════════════════════════════════════════════════════


def test_espelho_confirma_todos_os_esperados_antes_de_remover_e_registra_quatro_contagens() -> None:
    # SPECSFY: US-002 FR-004 FR-006 FR-008 NFR-001 NFR-002 NFR-004 AC-005
    scope = LogicalScope(project_id="projeto")
    backend = FakeVectorBackend()
    backend.seed(scope, ["manter", "obsoleto"])
    adapter = _qdrant_adapter(backend)

    def _rec(rid: str) -> VectorRecord:
        return VectorRecord(id=rid, content=rid, vector=[0.1] * 8, metadata={"chunk_id": rid})

    counts = synchronize(adapter, scope, [_rec("manter"), _rec("novo")], mode="mirror")

    assert isinstance(counts, SyncCounts)
    assert (counts.previstos, counts.inseridos, counts.mantidos, counts.removidos) == (
        2,
        1,
        1,
        1,
    )
    assert backend.deleted_ids == ["obsoleto"]
    # A remoção só ocorre depois da releitura que confirma os esperados.
    assert backend.confirmed_before_delete is True


def test_espelho_bloqueia_remocao_quando_o_destino_nao_confirma_os_esperados() -> None:
    # SPECSFY: US-002 FR-004 FR-006 FR-008 NFR-001 NFR-002 NFR-004 AC-005
    from src.providers.errors import UnsafeRemovalError

    scope = LogicalScope(project_id="projeto")
    backend = FakeVectorBackend()
    backend.seed(scope, ["obsoleto"])
    backend.confirm_writes = False  # releitura não devolve os pontos upsertados
    adapter = _qdrant_adapter(backend)

    registro = VectorRecord(id="novo", content="n", vector=[0.1] * 8, metadata={"chunk_id": "novo"})
    with pytest.raises(UnsafeRemovalError):
        synchronize(adapter, scope, [registro], mode="mirror")

    assert backend.deleted_ids == []
