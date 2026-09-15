"""RED do Ato II da SPEC-0014 — decisão sobre a colocação do resumo de seção.

Cada teste chama o harness de comparação/decisão ainda não implementado
(`tests._spec0014_resumo_secao`, seguindo a convenção local de `tests.
_fakes_vectorstore`), definido aqui apenas como contrato. T007 (Ato III,
fora do escopo desta etapa) materializa o módulo e faz estes testes
passarem — nenhuma chamada real à API OpenAI acontece antes disso, porque o
import falha antes de qualquer consulta ser feita.
"""

from __future__ import annotations

import pytest

GABARITO = "documentos/vivo_gold_banda_larga_pf/consultas.yaml"
ALTERNATIVAS = ("metadado", "chunk_com_peso", "indice_de_roteamento")


@pytest.mark.parametrize("alternativa", ALTERNATIVAS)
def test_comparacao_alternativas(alternativa):
    """SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-001"""
    from tests._spec0014_resumo_secao import comparar_alternativa

    resultado = comparar_alternativa(alternativa, gabarito_path=GABARITO)

    assert resultado["alternativa"] == alternativa
    assert resultado["total"] == 10
    assert 0 <= resultado["aprovadas"] <= resultado["total"]
    assert isinstance(resultado["ruido"], list)


def test_decisao_manter_como_esta_quando_nenhuma_supera():
    """SPECSFY: US-001 FR-002 FR-003 NFR-001 AC-002"""
    from tests._spec0014_resumo_secao import decidir

    comparacao = {
        "atual": {"aprovadas": 8, "ruido": []},
        "metadado": {"aprovadas": 7, "ruido": ["seção sem contexto"]},
        "chunk_com_peso": {"aprovadas": 8, "ruido": []},
        "indice_de_roteamento": {"aprovadas": 6, "ruido": ["seção errada"]},
    }

    decisao = decidir(comparacao)

    assert decisao["alternativa"] is None
    assert "manter como está" in decisao["justificativa"].lower()


def test_decisao_lista_parametros_chunker():
    """SPECSFY: US-001 FR-003 NFR-001 AC-003"""
    from tests._spec0014_resumo_secao import decidir

    comparacao = {
        "atual": {"aprovadas": 6, "ruido": ["resumo competindo"]},
        "metadado": {"aprovadas": 9, "ruido": []},
        "chunk_com_peso": {"aprovadas": 7, "ruido": []},
        "indice_de_roteamento": {"aprovadas": 7, "ruido": []},
    }

    decisao = decidir(comparacao)

    assert decisao["alternativa"] == "metadado"
    assert isinstance(decisao["parametros_chunker"], dict)
    assert decisao["parametros_chunker"]


def test_decisao_sinaliza_impacto_chunk_type():
    """SPECSFY: US-001 FR-003 NFR-001 AC-004"""
    from tests._spec0014_resumo_secao import decidir

    comparacao = {
        "atual": {"aprovadas": 6, "ruido": ["resumo competindo"]},
        "metadado": {"aprovadas": 9, "ruido": []},
        "chunk_com_peso": {"aprovadas": 7, "ruido": []},
        "indice_de_roteamento": {"aprovadas": 7, "ruido": []},
    }

    decisao = decidir(comparacao)

    assert decisao["alternativa"] == "metadado"
    assert decisao["impacto_chunk_type"] is True


def test_erro_prototipo_nao_afeta_producao(monkeypatch):
    """SPECSFY: US-001 FR-001 NFR-001 AC-005"""
    from tests._spec0014_resumo_secao import comparar_alternativa

    producao_tocada = {"chamada": False}

    def _sentinela_producao(*_args, **_kwargs):
        producao_tocada["chamada"] = True
        raise AssertionError("protótipo não deve tocar produção")

    monkeypatch.setattr(
        "tests._spec0014_resumo_secao._build_vector_store_producao",
        _sentinela_producao,
        raising=False,
    )

    resultado = comparar_alternativa(
        "metadado", gabarito_path=GABARITO, simular_erro_na_consulta=0
    )

    assert producao_tocada["chamada"] is False
    assert resultado["erro_em"] == [0]
    assert resultado["total"] == 10


def test_gabarito_insuficiente_registra_limitacao(tmp_path):
    """SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-006"""
    from tests._spec0014_resumo_secao import comparar_alternativa

    gabarito_sem_resumo = tmp_path / "consultas_sem_resumo.yaml"
    gabarito_sem_resumo.write_text(
        '- pergunta: "teste sem seção com resumo"\n'
        '  categoria: ampla\n'
        '  deve_conter: ["x"]\n',
        encoding="utf-8",
    )

    resultado = comparar_alternativa(
        "metadado", gabarito_path=str(gabarito_sem_resumo)
    )

    assert resultado.get("limitacao") == "gabarito não cobre seção com resumo"
