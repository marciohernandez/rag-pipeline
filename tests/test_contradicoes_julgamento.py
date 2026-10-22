"""Julgamento de um assunto: etiquetas e origem (SPEC-0038, FR-003, FR-004, NFR-002)."""

from __future__ import annotations

import json

import pytest

from tests._fase1_contradicoes import exigir
from tests._fase1_limpeza import EspiaoIa


def _julgar(afirmacoes, resposta):
    contratos = exigir("src.pipeline.contradicoes.contratos")
    julgamento = exigir("src.pipeline.contradicoes.julgamento")
    itens = [contratos.Afirmacao(arquivo=a, assunto="preços", texto=t) for a, t in afirmacoes]
    return julgamento.julgar_assunto(EspiaoIa(texto=json.dumps(resposta)), "preços", itens)


def test_spec_0038_ac_002_versao_desatualizada_indica_o_trecho_mais_antigo() -> None:
    """SPECSFY: SPEC-0038 US-002 FR-003 FR-004 NFR-002 AC-002"""
    ocorrencias = _julgar(
        [
            ("precos-2024.md", "Tabela de março de 2024: plano básico a 39 reais."),
            ("precos-2025.md", "Tabela de março de 2025: plano básico a 49 reais."),
        ],
        [
            {
                "etiqueta": "versao_desatualizada",
                "indices": [0, 1],
                "explicacao": "A mesma tabela de preços aparece com datas e valores diferentes.",
                "mais_antigo": 0,
            }
        ],
    )

    assert len(ocorrencias) == 1
    ocorrencia = ocorrencias[0]
    assert ocorrencia.etiqueta == "versao_desatualizada"
    assert ocorrencia.arquivo_mais_antigo == "precos-2024.md"
    assert {t.arquivo for t in ocorrencia.trechos} == {"precos-2024.md", "precos-2025.md"}
    assert ocorrencia.explicacao


def test_spec_0038_ac_003_duplicado_lista_os_dois_arquivos_de_origem() -> None:
    """SPECSFY: SPEC-0038 US-002 FR-003 FR-004 AC-003"""
    ocorrencias = _julgar(
        [
            ("a.md", "O suporte atende por e-mail em dias úteis."),
            ("b.md", "Atendemos por e-mail nos dias úteis."),
        ],
        [
            {
                "etiqueta": "duplicado",
                "indices": [0, 1],
                "explicacao": "O mesmo fato escrito de forma equivalente.",
                "mais_antigo": None,
            }
        ],
    )

    assert [o.etiqueta for o in ocorrencias] == ["duplicado"]
    assert {t.arquivo for t in ocorrencias[0].trechos} == {"a.md", "b.md"}
    assert len(ocorrencias[0].trechos) >= 2


def test_spec_0038_ac_003_resposta_invalida_da_ia_nao_vira_ocorrencia() -> None:
    """SPECSFY: SPEC-0038 US-002 FR-003 FR-004 AC-003"""
    contratos = exigir("src.pipeline.contradicoes.contratos")
    julgamento = exigir("src.pipeline.contradicoes.julgamento")
    afirmacoes = [
        contratos.Afirmacao(arquivo="a.md", assunto="preços", texto="49 reais"),
        contratos.Afirmacao(arquivo="b.md", assunto="preços", texto="59 reais"),
    ]

    with pytest.raises(ValueError, match="inválid"):
        julgamento.julgar_assunto(EspiaoIa(texto="isto não é json"), "preços", afirmacoes)
