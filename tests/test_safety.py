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
import src.embedder as embedder
import upsert_from_chunks


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
    """Registra qualquer tentativa de criar cliente remoto ou embeddings."""
    acionamentos: list[str] = []

    def _cliente():
        acionamentos.append("cliente")
        return ClienteProibido()

    def _embeddings(_cfg):
        acionamentos.append("embeddings")
        return EmbeddingsProibidos()

    monkeypatch.setattr(embedder, "_get_qdrant_client", _cliente)
    monkeypatch.setattr(embedder, "get_embeddings", _embeddings)
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
        embedder.index_chunks(chunks, embedding_cfg, vector_cfg, str(tmp_path))

    assert acionamentos == []


def test_modo_espelho_recusado_em_provider_sem_garantia(monkeypatch, tmp_path) -> None:
    # SPECSFY: US-001 FR-002 FR-005 NFR-001 AC-008
    acionamentos = _espionar_destino(monkeypatch)
    embedding_cfg, vector_cfg = _configuracao(provider="chroma", sync_mode="mirror")

    with pytest.raises(ValueError, match="espelho"):
        embedder.index_chunks(
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
    assert "recreate" not in inspect.signature(embedder.index_chunks).parameters

    embeddings = EmbeddingsFalsos()
    monkeypatch.setattr(embedder, "get_embeddings", lambda _cfg: embeddings)
    embedding_cfg, vector_cfg = _configuracao(provider="chroma", sync_mode="append")

    embedder.index_chunks(
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
        embedder.index_chunks([], embedding_cfg, vector_cfg, str(tmp_path))

    assert acionamentos == []
