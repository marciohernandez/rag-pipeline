"""RED revisado da SPEC-0014: comparação objetiva de estratégias de resumo."""

from __future__ import annotations

import os

import pytest
from langchain_core.documents import Document

from src.pipeline.providers.factory import ProviderFactory
from src.pipeline.validation import QueryCase

GABARITO = "documentos/vivo_gold_banda_larga_pf/consultas.yaml"
INPUT_DIR = "documentos/vivo_gold_banda_larga_pf"
ESTRATEGIAS = {"atual", "metadado", "chunk_com_peso", "indice_de_roteamento"}


def _chunks_sinteticos() -> list[Document]:
    comum = {
        "document_id": "doc-1",
        "titulo": "Catálogo",
        "secao": "Planos",
        "nome_arquivo": "catalogo.md",
    }
    return [
        Document(
            page_content="Itens disponíveis nesta seção:\n- Plano A\n- Plano B",
            metadata={
                **comum,
                "subsecao": "",
                "chunk_type": "section_summary",
                "chunk_id": "summary-1",
            },
        ),
        Document(
            page_content="Plano A custa R$ 100.",
            metadata={
                **comum,
                "subsecao": "Plano A",
                "chunk_type": "detail",
                "chunk_id": "detail-1",
            },
        ),
        Document(
            page_content="Plano B custa R$ 120.",
            metadata={
                **comum,
                "subsecao": "Plano B",
                "chunk_type": "detail",
                "chunk_id": "detail-2",
            },
        ),
    ]


def _resultado(
    *, aprovadas: int = 10, ruido: int = 4, colisoes: int = 1, status: str = "concluido"
) -> dict:
    return {
        "status": status,
        "total": 10,
        "aprovadas": aprovadas,
        "regressoes": [] if aprovadas == 10 else ["consulta-regredida"],
        "ruido": ruido,
        "colisoes": colisoes,
    }


def test_controle_preserva_busca_plana_e_parametros_fixos():
    """SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-001"""
    from tests.spec0014._harness import projetar_estrategia

    plano = projetar_estrategia("atual", _chunks_sinteticos())

    assert [item.metadata["chunk_type"] for item in plano["searchable"]] == [
        "section_summary",
        "detail",
        "detail",
    ]
    assert plano["top_k"] == 4


def test_metadado_nao_vetoriza_resumo_e_enriquece_detalhes():
    """SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-001"""
    from tests.spec0014._harness import projetar_estrategia

    plano = projetar_estrategia("metadado", _chunks_sinteticos())

    assert {item.metadata["chunk_type"] for item in plano["searchable"]} == {"detail"}
    assert all(item.metadata["section_summary_text"] for item in plano["searchable"])
    assert len({item.metadata["section_key"] for item in plano["searchable"]}) == 1


def test_chunk_com_peso_define_candidatos_e_penaliza_resumo():
    """SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-001"""
    from tests.spec0014._harness import projetar_estrategia, reranquear_com_peso

    chunks = _chunks_sinteticos()
    plano = projetar_estrategia("chunk_com_peso", chunks)
    ranking = reranquear_com_peso([(0.8, chunks[0]), (0.8, chunks[1])])

    assert plano["candidate_k"] == 12
    assert plano["summary_weight"] == 0.85
    assert ranking[0][1].metadata["chunk_type"] == "detail"
    assert ranking[1][0] == pytest.approx(0.68)


def test_indice_de_roteamento_separa_indices_e_usa_chave_composta():
    """SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-001"""
    from tests.spec0014._harness import projetar_estrategia

    plano = projetar_estrategia("indice_de_roteamento", _chunks_sinteticos())

    assert {item.metadata["chunk_type"] for item in plano["router"]} == {
        "section_summary"
    }
    assert {item.metadata["chunk_type"] for item in plano["searchable"]} == {"detail"}
    assert plano["route_top_k"] == 1
    assert plano["route_threshold"] == 0.5
    assert plano["router"][0].metadata["section_key"] == "doc-1|Catálogo|Planos"


@pytest.mark.skipif(
    os.getenv("RUN_SPEC0014_REAL") != "1",
    reason="comparação paga exige RUN_SPEC0014_REAL=1",
)
def test_comparacao_real_reproduzivel():
    """SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-001"""
    from tests.spec0014._harness import comparar_todas

    from src.bootstrap import load_env

    load_env()
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY ausente; T008 permanece pendente")

    comparacao = comparar_todas(input_dir=INPUT_DIR, gabarito_path=GABARITO)

    assert set(comparacao["estrategias"]) == ESTRATEGIAS
    assert comparacao["config"] == {
        "model": "text-embedding-3-small",
        "dimensions": 1536,
        "top_k": 4,
        "threshold": 0.5,
    }
    assert len(comparacao["corpus_sha256"]) == 64
    assert len(comparacao["gabarito_sha256"]) == 64
    for resultado in comparacao["estrategias"].values():
        assert resultado["total"] == 10
        assert isinstance(resultado["ruido"], int)
        assert isinstance(resultado["colisoes"], int)
        assert isinstance(resultado["regressoes"], list)


def test_decisao_rejeita_regressao_e_exige_melhoria_estrita():
    """SPECSFY: US-001 FR-002 FR-003 NFR-001 AC-002"""
    from tests.spec0014._harness import decidir

    com_regressao = {
        "atual": _resultado(ruido=4, colisoes=1),
        "metadado": _resultado(aprovadas=9, ruido=0, colisoes=0),
        "chunk_com_peso": _resultado(ruido=4, colisoes=1),
        "indice_de_roteamento": _resultado(ruido=5, colisoes=0),
    }
    assert decidir(com_regressao)["estrategia"] == "atual"

    com_melhoria = {
        **com_regressao,
        "metadado": _resultado(ruido=3, colisoes=0),
        "chunk_com_peso": _resultado(ruido=3, colisoes=0),
    }
    decisao = decidir(com_melhoria)
    assert decisao["estrategia"] == "metadado"
    assert decisao["criterio"] == ["sem_regressao", "ruido", "colisoes", "custo"]


def test_decisao_lista_parametros_da_estrategia_vencedora():
    """SPECSFY: US-001 FR-003 NFR-001 AC-003"""
    from tests.spec0014._harness import decidir

    comparacao = {
        "atual": _resultado(ruido=4, colisoes=2),
        "metadado": _resultado(ruido=4, colisoes=1),
        "chunk_com_peso": _resultado(ruido=5, colisoes=0),
        "indice_de_roteamento": _resultado(ruido=2, colisoes=0),
    }
    decisao = decidir(comparacao)

    assert decisao["estrategia"] == "indice_de_roteamento"
    assert decisao["parametros_chunker"] == {}
    assert decisao["parametros_recuperacao"] == {
        "top_k": 4,
        "route_top_k": 1,
        "route_threshold": 0.5,
    }


def test_decisao_sinaliza_impacto_em_chunk_type():
    """SPECSFY: US-001 FR-003 NFR-001 AC-004"""
    from tests.spec0014._harness import decidir

    comparacao = {
        "atual": _resultado(ruido=4, colisoes=2),
        "metadado": _resultado(ruido=2, colisoes=0),
        "chunk_com_peso": _resultado(ruido=5, colisoes=0),
        "indice_de_roteamento": _resultado(ruido=3, colisoes=0),
    }
    decisao = decidir(comparacao)

    assert decisao["impacto_chunk_type"] is True
    assert decisao["revisar_quality"] is True


class _EmbeddingDeterministico:
    def embed_documents(self, texts):
        return [[float(index + 1), 1.0] for index, _text in enumerate(texts)]

    def embed_query(self, _text):
        return [1.0, 1.0]


def test_falha_nao_toca_qdrant_e_torna_comparacao_inconclusiva(monkeypatch):
    """SPECSFY: US-001 FR-001 NFR-001 AC-005"""
    from tests.spec0014._harness import comparar_todas

    original = ProviderFactory.create_vector_store
    providers: list[str] = []

    def guard(name, settings=None):
        providers.append(name)
        assert name == "in_memory"
        return original(name, settings)

    monkeypatch.setattr(ProviderFactory, "create_vector_store", staticmethod(guard))
    resultado = comparar_todas(
        chunks=_chunks_sinteticos(),
        cases=[QueryCase("Quais planos?", "ampla", ("Plano A",))],
        embeddings=_EmbeddingDeterministico(),
        simular_erro={"metadado": 0},
    )

    assert providers and set(providers) == {"in_memory"}
    assert resultado["status"] == "inconclusivo"
    assert resultado["estrategias"]["metadado"]["status"] == "falhou"
    assert resultado["decisao"] is None


def test_empate_sem_evidencia_registra_limitacao():
    """SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-006"""
    from tests.spec0014._harness import decidir

    empate = {nome: _resultado() for nome in ESTRATEGIAS}
    decisao_empate = decidir(empate)
    assert decisao_empate["estrategia"] == "atual"
    assert decisao_empate["limitacao"] == "gabarito não diferenciou as estratégias"

    baseline_invalido = {**empate, "atual": _resultado(aprovadas=9)}
    decisao_invalida = decidir(baseline_invalido)
    assert decisao_invalida["status"] == "inconclusiva"
    assert decisao_invalida["estrategia"] is None
