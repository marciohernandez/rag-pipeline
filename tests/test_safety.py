"""Testes TDD derivados dos cenários BDD da SPEC-0001.

Cada caso prova que nenhuma mutação remota acontece antes da validação
completa de opção, configuração e escopo lógico.
"""

from __future__ import annotations

import inspect
import sys
from uuid import uuid4

import pytest
from langchain_core.documents import Document

import pipeline
import upsert_from_chunks
from src.pipeline import indexing


class ConfiguracaoTocada(Exception):
    """Sinaliza que a execução chegou a carregar configuração."""


class ClienteProibido:
    """Cliente que falha se qualquer método for usado."""

    def __getattr__(self, nome: str):  # pragma: no cover - guarda defensiva
        raise AssertionError(f"cliente remoto acionado: {nome}")


class EmbeddingsProibidos:
    def embed_documents(self, _textos):  # pragma: no cover - guarda defensiva
        raise AssertionError("geração de embeddings acionada")


def _chunk(chunk_id: str, project_id: str = "projeto") -> Document:
    return Document(
        page_content="conteúdo",
        metadata={
            "project_id": project_id,
            "document_id": str(uuid4()),
            "chunk_id": chunk_id,
            "chunk_type": "detail",
        },
    )


def _configuracao(provider: str = "qdrant", sync_mode: str = "mirror") -> tuple[dict, dict]:
    return (
        {"provider": "openai", "model": "text-embedding-3-small", "dimensions": 3},
        {
            "provider": provider,
            "collection_name": "collection",
            "index_name": "indice",
            "namespace": "namespace",
            "sync_mode": sync_mode,
        },
    )


def _espionar_destino(monkeypatch) -> list[str]:
    """Registra qualquer tentativa de criar vector store remoto ou embeddings.

    Migrado em T033 para a fronteira nova: o alvo é o serviço de aplicação
    `src.pipeline.indexing`, que compõe os adapters por contrato.
    """
    acionamentos: list[str] = []

    def _store(*_args, **_kwargs):
        acionamentos.append("cliente")
        return ClienteProibido()

    def _embeddings(*_args, **_kwargs):
        acionamentos.append("embeddings")
        return EmbeddingsProibidos()

    monkeypatch.setattr(indexing, "build_vector_store", _store)
    monkeypatch.setattr(indexing, "build_embeddings", _embeddings)
    return acionamentos


def test_pipeline_rejeita_opcao_destrutiva_antes_de_ler_configuracao(monkeypatch) -> None:
    # SPECSFY: US-002 FR-001 FR-002 NFR-001 AC-001
    def _config_proibida(*_args, **_kwargs):
        raise ConfiguracaoTocada("a execução avançou além da rejeição")

    monkeypatch.setattr(pipeline, "load_config", _config_proibida)
    monkeypatch.setattr(sys, "argv", ["pipeline.py", "--recreate"])

    with pytest.raises(SystemExit) as saida:
        pipeline.main()

    assert saida.value.code != 0


def test_reupsert_rejeita_opcao_destrutiva_sem_cliente_nem_embeddings(monkeypatch) -> None:
    # SPECSFY: US-002 FR-001 FR-002 NFR-001 AC-002
    acionamentos = _espionar_destino(monkeypatch)

    def _config_proibida(*_args, **_kwargs):
        raise ConfiguracaoTocada("a execução avançou além da rejeição")

    monkeypatch.setattr(upsert_from_chunks, "load_config", _config_proibida)
    monkeypatch.setattr(
        sys, "argv", ["upsert_from_chunks.py", "--provider", "qdrant", "--recreate"]
    )

    with pytest.raises(SystemExit):
        upsert_from_chunks.main()

    assert acionamentos == []


def test_mensagem_de_migracao_indica_a_sincronizacao_idempotente(
    monkeypatch, capsys
) -> None:
    # SPECSFY: US-002 US-003 FR-001 FR-006 AC-003
    def _config_proibida(*_args, **_kwargs):
        raise ConfiguracaoTocada("a execução avançou além da rejeição")

    monkeypatch.setattr(pipeline, "load_config", _config_proibida)
    monkeypatch.setattr(sys, "argv", ["pipeline.py", "--recreate"])

    with pytest.raises(SystemExit):
        pipeline.main()

    mensagem = "".join(capsys.readouterr()).lower()
    assert "--recreate" in mensagem
    assert "idempotente" in mensagem


def test_escopo_invalido_bloqueia_antes_de_acionar_o_destino(monkeypatch, tmp_path) -> None:
    # SPECSFY: US-001 US-003 FR-004 NFR-001 AC-007
    acionamentos = _espionar_destino(monkeypatch)
    embedding_cfg, vector_cfg = _configuracao()
    chunks = [_chunk(str(uuid4()), project_id="projeto"), _chunk(str(uuid4()), project_id="outro")]

    with pytest.raises(ValueError):
        indexing.index_chunks(chunks, embedding_cfg, vector_cfg, str(tmp_path))

    assert acionamentos == []


def test_modo_espelho_recusado_em_provider_sem_garantia(monkeypatch, tmp_path) -> None:
    # SPECSFY: US-001 FR-002 FR-005 NFR-001 AC-008
    # SPEC-0010: Chroma e Pinecone deixaram de existir. Uma configuração que
    # ainda aponte para um provider removido é rejeitada fail-closed, antes de
    # qualquer acesso ao destino.
    acionamentos = _espionar_destino(monkeypatch)
    embedding_cfg, vector_cfg = _configuracao(provider="chroma", sync_mode="mirror")

    with pytest.raises(ValueError, match=r"(?i)não suportado"):
        indexing.index_chunks(
            [_chunk(str(uuid4()))], embedding_cfg, vector_cfg, str(tmp_path)
        )

    assert acionamentos == []


class EmbeddingsFalsos:
    def __init__(self) -> None:
        self.chamadas: list[list[str]] = []

    def embed_documents(self, textos: list[str]) -> list[list[float]]:
        self.chamadas.append(textos)
        return [[0.1, 0.2, 0.3] for _ in textos]

    def embed_query(self, _texto: str) -> list[float]:
        return [0.1, 0.2, 0.3]


def test_modo_incremental_preservado_e_parametro_destrutivo_ausente(
    monkeypatch, tmp_path
) -> None:
    # SPECSFY: US-003 FR-002 FR-005 NFR-003 AC-009
    assert "recreate" not in inspect.signature(indexing.index_chunks).parameters

    embeddings = EmbeddingsFalsos()
    monkeypatch.setattr(indexing, "build_embeddings", lambda _cfg: embeddings)

    from src.pipeline.providers.factory import ProviderFactory
    from tests._fakes_vectorstore import FakeVectorBackend

    adapter = ProviderFactory.create_vector_store(
        "qdrant", {"collection_name": "collection", "client": FakeVectorBackend()}
    )
    monkeypatch.setattr(indexing, "build_vector_store", lambda *_a, **_k: adapter)
    embedding_cfg, vector_cfg = _configuracao(provider="qdrant", sync_mode="append")

    indexing.index_chunks(
        [_chunk(str(uuid4()))], embedding_cfg, vector_cfg, str(tmp_path)
    )

    assert embeddings.chamadas == [["conteúdo"]]


def test_conjunto_esperado_vazio_bloqueia_antes_de_acionar_o_destino(
    monkeypatch, tmp_path
) -> None:
    # SPECSFY: US-001 FR-004 FR-007 NFR-001 AC-013
    acionamentos = _espionar_destino(monkeypatch)
    embedding_cfg, vector_cfg = _configuracao()

    with pytest.raises(ValueError, match="vazio"):
        indexing.index_chunks([], embedding_cfg, vector_cfg, str(tmp_path))

    assert acionamentos == []


# ═════════════════════════════════════════════════════════════════
# SPEC-0003 — Fail-closed uniforme no serviço de sincronização (T010)
# ═════════════════════════════════════════════════════════════════

_LOTE_INVALIDO_IDS = ["lote-vazio", "chunk_id-duplicado", "tenants-misturados"]


def _registros_invalidos(caso: str):
    from src.pipeline.providers.contracts import VectorRecord

    def _rec(rid: str, tenant: str | None = None) -> VectorRecord:
        meta = {"chunk_id": rid}
        if tenant is not None:
            meta["tenant_id"] = tenant
        return VectorRecord(id=rid, content=rid, vector=[0.1] * 8, metadata=meta)

    if caso == "lote-vazio":
        return []
    if caso == "chunk_id-duplicado":
        return [_rec("repetido"), _rec("repetido")]
    return [_rec("a", tenant="cliente-a"), _rec("b", tenant="cliente-b")]


@pytest.mark.parametrize("backend_name", ["qdrant"])
@pytest.mark.parametrize("caso", _LOTE_INVALIDO_IDS)
def test_escopo_invalido_encerra_antes_de_qualquer_cliente_remoto(backend_name, caso) -> None:
    # SPECSFY: US-002 FR-002 FR-004 FR-006 FR-008 NFR-001 NFR-002 AC-007
    from src.pipeline.providers import synchronize
    from src.pipeline.providers.contracts import LogicalScope
    from src.pipeline.providers.errors import ProviderError
    from src.pipeline.providers.factory import ProviderFactory
    from src.pipeline.safety import SyncSafetyError
    from tests._fakes_vectorstore import FakeVectorBackend

    backend = FakeVectorBackend()
    adapter = ProviderFactory.create_vector_store(
        backend_name,
        {
            "collection_name": "c",
            "index_name": "i",
            "namespace": "ns",
            "url": "http://localhost:6333",
            "api_key": "seg",
            "client": backend,
        },
    )

    with pytest.raises((SyncSafetyError, ProviderError)):
        synchronize(
            adapter,
            LogicalScope(project_id="projeto"),
            _registros_invalidos(caso),
            mode="append",
        )

    assert backend.ensure_ready_calls == 0
    assert backend.upsert_calls == []
    assert backend.deleted_ids == []


# SPEC-0010: `test_modo_mirror_fora_do_qdrant_encerra_antes_do_cliente` foi
# removido — Chroma e Pinecone não existem mais como providers. A garantia
# "modo mirror exige `supports_mirror`" continua provada por
# `tests/test_characterization_providers.py::test_mirror_rejected_for_non_mirror_adapter`
# (SPEC-0010 AC-009), sobre um adapter-dublê sintético.


# ═════════════════════════════════════════════════════════════════
# SPEC-0003 — Validação do escopo de recuperação (T015)
# ═════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("project_id", ["", "   ", None])
def test_recuperacao_sem_project_id_valido_falha_localmente(project_id) -> None:
    # SPECSFY: US-003 FR-002 FR-006 FR-007 FR-008 NFR-001 NFR-003 NFR-004 AC-012
    from src.pipeline.providers.contracts import LogicalScope
    from src.pipeline.providers.errors import InvalidScopeError

    with pytest.raises(InvalidScopeError):
        LogicalScope(project_id=project_id)


def test_query_nao_e_alcancada_quando_o_escopo_e_invalido() -> None:
    # SPECSFY: US-003 FR-002 FR-006 FR-007 FR-008 NFR-001 NFR-003 NFR-004 AC-012
    from src.pipeline.providers.contracts import LogicalScope
    from src.pipeline.providers.errors import InvalidScopeError
    from src.pipeline.providers.factory import ProviderFactory
    from tests._fakes_vectorstore import FakeVectorBackend

    backend = FakeVectorBackend()
    adapter = ProviderFactory.create_vector_store("in_memory", {"client": backend})

    with pytest.raises(InvalidScopeError):
        scope = LogicalScope(project_id="")
        adapter.query(scope, [0.1] * 8, k=4)

    assert backend.query_calls == []


def test_consumidores_de_recuperacao_constroem_logical_scope_antes_de_query() -> None:
    # SPECSFY: US-003 FR-007 FR-006 AC-012
    from pathlib import Path

    raiz = Path(__file__).resolve().parent.parent
    for nome in ("search.py", "chat.py"):
        fonte = (raiz / nome).read_text(encoding="utf-8")
        assert "service.query_base" in fonte, f"{nome} não delega a recuperação à fachada"
        assert "tenant_id=tenant_id" in fonte, f"{nome} não repassa o tenant explícito"

    fachada = (raiz / "src" / "pipeline" / "service.py").read_text(encoding="utf-8")
    assert "project_id=project_id" in fachada
    assert "tenant_id=tenant_id" in fachada
    assert "_retrieve(" in fachada

    demo = (raiz / "demo_rag.py").read_text(encoding="utf-8")
    assert "LogicalScope" in demo or "build_scope" in demo
