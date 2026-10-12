"""Fachada do pipeline para o fluxo de ingestão (SPEC-0026, T025)."""

from __future__ import annotations

from src.pipeline import indexing, service
from src.pipeline.providers.factory import ProviderFactory


def _config(pasta: str) -> dict:
    return {
        "projeto": {"nome": "previa"},
        "caminhos": {"input_dir": pasta, "chunks_file": f"{pasta}/chunks.json"},
        "embedding": {"provider": "fake", "dimensions": 8},
        "vector_store": {"provider": "qdrant", "collection_name": "c"},
        "chunking": {"default_splitter": "header", "default_chunk_size": 400},
    }


def test_preview_chunks_divide_sem_sincronizar(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-002 FR-005 FR-007 NFR-003 AC-007 AC-008"""
    (tmp_path / "a.md").write_text("# Título\n\n## Seção\n\nConteúdo útil.", encoding="utf-8")
    monkeypatch.setattr(
        service, "sync_vector_store", lambda *a, **k: (_ for _ in ()).throw(AssertionError)
    )
    monkeypatch.setattr(
        ProviderFactory,
        "create_vector_store",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError),
    )

    resultado = service.preview_chunks(_config(str(tmp_path)), input_dir=str(tmp_path))

    assert resultado.chunks and resultado.sync_counts is None
    assert {chunk.metadata["nome_arquivo"] for chunk in resultado.chunks} == {"a.md"}


def test_preview_chunks_respeita_o_frontmatter_do_arquivo(tmp_path) -> None:
    """SPECSFY: SPEC-0026 US-002 FR-005 FR-007 NFR-003 AC-007 AC-008"""
    (tmp_path / "qa.md").write_text(
        "---\nsplitter: qa\n---\nP: Um?\nR: Um.\n\n++++\n\nP: Dois?\nR: Dois.", encoding="utf-8"
    )

    resultado = service.preview_chunks(_config(str(tmp_path)), input_dir=str(tmp_path))

    detalhes = [c for c in resultado.chunks if c.metadata.get("chunk_type") == "detail"]
    assert len(detalhes) == 2


def test_describe_collection_devolve_existencia_e_dimensao_sem_criar(monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-002 FR-005 FR-007 FR-009 AC-011"""

    class Adapter:
        def __init__(self, descricao):
            self.descricao = descricao

        def describe_scope(self, scope):
            return self.descricao

        def ensure_ready(self, *a, **k):
            raise AssertionError("descrever nunca prepara o destino")

    monkeypatch.setattr(
        indexing, "build_vector_store", lambda cfg: Adapter({"exists": True, "dimensions": 3072})
    )
    existente = service.describe_collection({"provider": "qdrant", "collection_name": "c"})
    monkeypatch.setattr(indexing, "build_vector_store", lambda cfg: Adapter({}))
    ausente = service.describe_collection({"provider": "qdrant", "collection_name": "c"})

    assert existente == {"exists": True, "dimensions": 3072}
    assert ausente == {"exists": False, "dimensions": None}


def test_conexao_repassa_url_e_chave_aos_adapters(monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-002 FR-005 FR-007 FR-009 AC-011"""
    vector_stores: list[dict] = []
    embeddings: list[dict] = []
    monkeypatch.setattr(
        ProviderFactory,
        "create_vector_store",
        lambda nome, s: vector_stores.append(dict(s)) or object(),
    )
    monkeypatch.setattr(
        ProviderFactory,
        "create_embedding",
        lambda nome, s: embeddings.append(dict(s)) or object(),
    )

    indexing.build_vector_store(
        {
            "provider": "qdrant",
            "collection_name": "c",
            "url": "https://q.exemplo.com",
            "api_key": "k1",
        }
    )
    indexing.build_vector_store({"provider": "qdrant", "collection_name": "c"})
    indexing.build_embeddings(
        {
            "provider": "openai",
            "model": "m",
            "dimensions": 8,
            "api_key": "k2",
            "base_url": "https://api.exemplo.com/v1",
        }
    )

    assert vector_stores[0]["url"] == "https://q.exemplo.com"
    assert vector_stores[0]["api_key"] == "k1"
    assert "url" not in vector_stores[1] and "api_key" not in vector_stores[1]
    assert embeddings[0] == {
        "model": "m",
        "dimensions": 8,
        "api_key": "k2",
        "base_url": "https://api.exemplo.com/v1",
    }
