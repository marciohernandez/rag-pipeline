"""Pipeline por documento e exclusão de coleção (SPEC-0030, unidade).

Cobre o filtro de escopo com ``document_id``, a sincronização por documento e a
política que só deixa apagar coleções com o prefixo do app.
"""

from __future__ import annotations

import pytest
from langchain_core.documents import Document

from src.pipeline import indexing
from src.pipeline.providers.contracts import LogicalScope
from src.pipeline.safety import UnsafeRemovalError
from src.pipeline.service import drop_collection, list_document_chunks
from tests._colecoes import AdaptadorFalso, ArmazemFalso, EmbeddingsFalso


def _chunk(doc: str, indice: int, texto: str) -> Document:
    return Document(
        page_content=texto,
        metadata={
            "project_id": "col-x",
            "document_id": doc,
            "chunk_id": f"{doc}-{indice}",
            "nome_arquivo": f"{doc}.md",
        },
    )


@pytest.fixture
def ambiente(monkeypatch):
    armazem, embeddings = ArmazemFalso(), EmbeddingsFalso()
    adaptador = AdaptadorFalso(client=armazem)
    monkeypatch.setattr(indexing, "build_embeddings", lambda cfg: embeddings)
    monkeypatch.setattr(indexing, "build_vector_store", lambda cfg, persist_dir=None: adaptador)
    return armazem, embeddings, adaptador


def test_escopo_com_document_id_enxerga_so_o_documento() -> None:
    escopo = LogicalScope(project_id="col-x", document_id="  doc-a ")
    assert escopo.document_id == "doc-a"
    assert LogicalScope(project_id="col-x", document_id="  ").document_id is None


def test_sincroniza_cada_documento_no_proprio_escopo(ambiente) -> None:
    armazem, embeddings, _ = ambiente
    cfg = {"provider": "qdrant", "collection_name": "col-x"}
    indexing.index_documents(
        [_chunk("a", 1, "A1"), _chunk("a", 2, "A2"), _chunk("b", 1, "B1")], {}, cfg
    )
    assert sorted(embeddings.textos) == ["A1", "A2", "B1"]

    visto: list[str] = []
    contagens = indexing.index_documents(
        [_chunk("a", 1, "A1"), _chunk("a", 3, "A3")],
        {},
        cfg,
        on_document=lambda doc, c, grupo: visto.append(doc),
    )

    assert (contagens.previstos, contagens.inseridos, contagens.mantidos, contagens.removidos) == (
        2,
        1,
        1,
        1,
    )
    assert visto == ["a"]
    ids = {r.id for r in armazem.todos()}
    assert ids == {"a-1", "a-3", "b-1"}


def test_apagar_por_documento(ambiente) -> None:
    armazem, _, _ = ambiente
    cfg = {"provider": "qdrant", "collection_name": "col-x"}
    indexing.index_documents([_chunk("a", 1, "A1"), _chunk("b", 1, "B1")], {}, cfg)
    config = {"projeto": {"nome": "col-x"}, "embedding": {}, "vector_store": cfg}

    from src.pipeline.service import delete_scope

    assert delete_scope(config, document_id="a") == 1
    assert {r.id for r in armazem.todos()} == {"b-1"}


def test_listar_chunks_do_documento(ambiente) -> None:
    cfg = {"provider": "qdrant", "collection_name": "col-x"}
    indexing.index_documents([_chunk("a", 1, "A1"), _chunk("b", 1, "B1")], {}, cfg)
    config = {"projeto": {"nome": "col-x"}, "embedding": {}, "vector_store": cfg}

    chunks = list_document_chunks(config, "a", 200)

    assert [c["texto"] for c in chunks] == ["A1"]


def test_so_apaga_colecao_com_prefixo_do_app(ambiente) -> None:
    _, _, adaptador = ambiente
    apagadas: list[str] = []
    adaptador.drop = lambda: apagadas.append("ok")  # type: ignore[method-assign]

    drop_collection(
        {"projeto": {"nome": "x"}, "embedding": {}, "vector_store": {"collection_name": "col-ws-1"}}
    )
    assert apagadas == ["ok"]

    for nome in ("rag_docs", "produtos", ""):
        with pytest.raises(UnsafeRemovalError):
            drop_collection(
                {
                    "projeto": {"nome": "x"},
                    "embedding": {},
                    "vector_store": {"collection_name": nome},
                }
            )
    assert apagadas == ["ok"]
