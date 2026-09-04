"""Caracterização do comportamento observável da camada de providers.

Criado em T003 contra `src/pipeline/embedder.py` para servir de rede de segurança do
corte, e migrado em T030–T033 para a fronteira nova (`src/pipeline/indexing.py` +
`src/pipeline/providers/`). Cada caso continua congelando o mesmo comportamento
observável exigido pela NFR-004 — despacho por nome, erros locais antes de
qualquer acesso remoto, contagens do espelho, `batch_size` e guardas
fail-closed — agora através dos contratos neutros.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from uuid import uuid4

import pytest
from langchain_core.documents import Document

from src.pipeline import indexing, service
from src.pipeline.providers.factory import ProviderFactory
from tests._fakes_vectorstore import FakeVectorBackend

# ─────────────────────────────────────────────
# Dublês
# ─────────────────────────────────────────────


class FakeEmbeddings:
    def __init__(self) -> None:
        self.document_calls: list[list[str]] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_calls.append(list(texts))
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
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


def _qdrant_config() -> tuple[dict, dict]:
    return (
        {"provider": "openai", "model": "text-embedding-3-small", "dimensions": 3},
        {"provider": "qdrant", "collection_name": "collection", "sync_mode": "mirror"},
    )


def _instalar(monkeypatch, backend: FakeVectorBackend, embeddings=None) -> FakeEmbeddings:
    embeddings = embeddings or FakeEmbeddings()
    adapter = ProviderFactory.create_vector_store(
        "qdrant",
        {"collection_name": "collection", "url": "http://localhost:6333", "client": backend},
    )
    monkeypatch.setattr(indexing, "build_vector_store", lambda *_a, **_k: adapter)
    monkeypatch.setattr(indexing, "build_embeddings", lambda *_a, **_k: embeddings)
    return embeddings


def _scope(project_id: str = "projeto", tenant_id: str | None = None):
    return indexing.build_scope(project_id, tenant_id)


# ─────────────────────────────────────────────
# Fábrica de embeddings — despacho e erros locais
# ─────────────────────────────────────────────


def test_embeddings_provider_desconhecido_gera_value_error() -> None:
    # SPECSFY: FR-007 NFR-004
    with pytest.raises(ValueError):
        indexing.build_embeddings({"provider": "inexistente"})


def test_embeddings_openai_sem_credencial_gera_environment_error(monkeypatch) -> None:
    # SPECSFY: FR-007 NFR-004
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(EnvironmentError):
        indexing.build_embeddings(
            {"provider": "openai", "model": "text-embedding-3-small"}
        )


def test_embeddings_openai_com_credencial_nao_acessa_rede(monkeypatch) -> None:
    # SPECSFY: FR-007 NFR-004
    monkeypatch.setenv("OPENAI_API_KEY", "chave-de-teste")
    adapter = indexing.build_embeddings(
        {"provider": "openai", "model": "text-embedding-3-small", "dimensions": 3}
    )
    assert adapter.provider == "openai"
    assert callable(adapter.embed_documents)


# ─────────────────────────────────────────────
# Fábrica de vector store — despacho e erros locais
# ─────────────────────────────────────────────


def test_vector_store_provider_desconhecido_gera_value_error() -> None:
    # SPECSFY: FR-007 NFR-004
    with pytest.raises(ValueError):
        indexing.build_vector_store({"provider": "inexistente"})


def test_vector_store_chroma_nao_acessa_rede(tmp_path) -> None:
    # SPECSFY: FR-007 NFR-004
    store = indexing.build_vector_store(
        {"provider": "chroma", "collection_name": "rag_docs"}, str(tmp_path)
    )
    assert store.provider == "chroma"
    assert store.capabilities().supports_mirror is False


# ─────────────────────────────────────────────
# Sincronização Qdrant — contagens e espelho
# ─────────────────────────────────────────────


def test_index_chunks_qdrant_mirror_remove_somente_obsoletos_e_registra_quatro_contagens(
    monkeypatch, caplog
) -> None:
    # SPECSFY: FR-007 NFR-004
    obsoleto, atual = str(uuid4()), str(uuid4())
    backend = FakeVectorBackend()
    backend.seed(_scope(), [obsoleto])
    embeddings = _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _qdrant_config()

    with caplog.at_level(logging.INFO):
        indexing.index_chunks([_chunk(atual)], embedding_cfg, vector_cfg)

    assert [len(call) for call in backend.upsert_calls] == [1]
    assert embeddings.document_calls == [["conteúdo"]]
    assert backend.deleted_ids == [obsoleto]
    registro = " ".join(item.getMessage().lower() for item in caplog.records)
    for termo in ("previstos", "inseridos", "mantidos", "removidos"):
        assert termo in registro


def test_index_chunks_batch_size_respeita_a_configuracao_de_embedding(monkeypatch) -> None:
    # SPECSFY: FR-007 NFR-004
    backend = FakeVectorBackend()
    embeddings = _instalar(monkeypatch, backend)
    embedding_cfg, vector_cfg = _qdrant_config()
    embedding_cfg["batch_size"] = 2

    indexing.index_chunks(
        [_chunk(str(uuid4())) for _ in range(5)], embedding_cfg, vector_cfg
    )

    assert [len(call) for call in embeddings.document_calls] == [2, 2, 1]


# ─────────────────────────────────────────────
# Guardas fail-closed antes de qualquer provider
# ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "chunks",
    [
        pytest.param([], id="lote-vazio"),
        pytest.param(
            [_chunk("id-repetido"), _chunk("id-repetido")], id="chunk_id-duplicado"
        ),
        pytest.param(
            [_chunk(str(uuid4()), tenant_id="a"), _chunk(str(uuid4()), tenant_id="b")],
            id="tenants-misturados",
        ),
    ],
)
def test_index_chunks_escopo_invalido_bloqueia_antes_de_compor_provider(
    monkeypatch, chunks
) -> None:
    # SPECSFY: FR-007 NFR-004
    def _proibido(*_args, **_kwargs):
        raise AssertionError("provider não deveria ser composto")

    monkeypatch.setattr(indexing, "build_vector_store", _proibido)
    monkeypatch.setattr(indexing, "build_embeddings", _proibido)
    embedding_cfg, vector_cfg = _qdrant_config()

    with pytest.raises(ValueError):
        indexing.index_chunks(chunks, embedding_cfg, vector_cfg)


def test_index_chunks_mirror_fora_do_qdrant_bloqueia_antes_de_compor_provider(
    monkeypatch,
) -> None:
    # SPECSFY: FR-007 NFR-004
    def _proibido(*_args, **_kwargs):
        raise AssertionError("provider não deveria ser composto")

    monkeypatch.setattr(indexing, "build_vector_store", _proibido)
    monkeypatch.setattr(indexing, "build_embeddings", _proibido)
    embedding_cfg, vector_cfg = _qdrant_config()
    vector_cfg["provider"] = "chroma"

    with pytest.raises(ValueError, match="espelho"):
        indexing.index_chunks([_chunk(str(uuid4()))], embedding_cfg, vector_cfg)


# ─────────────────────────────────────────────
# Fronteira dos consumidores
# ─────────────────────────────────────────────


def test_pipeline_e_upsert_reutilizam_a_mesma_fachada_de_sincronizacao() -> None:
    # SPECSFY: FR-007 NFR-004
    # A SPEC-0008 elevou a fronteira: os dois CLIs agora consomem a fachada,
    # que delega ao serviço de indexação por contratos neutros.
    pipeline = importlib.import_module("pipeline")
    upsert_from_chunks = importlib.import_module("upsert_from_chunks")
    assert pipeline.service.sync_vector_store is service.sync_vector_store
    assert upsert_from_chunks.service.sync_vector_store is service.sync_vector_store


def test_consumidores_de_recuperacao_usam_as_fabricas_por_contrato() -> None:
    # SPECSFY: FR-007 NFR-004
    # ``chat.py`` ainda troca ``sys.stdout`` no import, então a fronteira
    # continua sendo caracterizada pela fonte. Search e chat usam a fachada;
    # demo_rag.py permanece fora dos cinco entrypoints da SPEC-0008.
    raiz = Path(__file__).resolve().parent.parent
    for nome in ("search.py", "chat.py"):
        fonte = (raiz / nome).read_text(encoding="utf-8")
        assert "from src.pipeline import service" in fonte
        assert "service.query_base" in fonte
        assert "build_embeddings" not in fonte
        assert "build_vector_store" not in fonte
        assert "from src.pipeline.embedder import" not in fonte

    demo = (raiz / "demo_rag.py").read_text(encoding="utf-8")
    assert "from src.pipeline.indexing import" in demo
    assert "build_embeddings" in demo
    assert "build_vector_store" in demo
