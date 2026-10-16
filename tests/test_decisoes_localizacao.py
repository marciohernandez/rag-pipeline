"""Localização do trecho alvo e classificação clara/incerta (SPEC-0039)."""

from __future__ import annotations

from tests._fase1_decisoes import IaDecisoes, exigir

DOC = (
    "# Política\n\n"
    "O cancelamento pode ser feito em até 15 dias.\n\n"
    "O reembolso ocorre em até 10 dias úteis.\n"
)
MENSAGEM = "Não foi possível localizar o trecho; indique qual corrigir"


def _ocorrencia():
    return {
        "id": "o1",
        "assunto": "cancelamento",
        "trechos": [
            {"arquivo": "marketing.md", "texto": "Cancelamento em até 15 dias."},
            {"arquivo": "comercial.md", "texto": "Cancelamento em até 7 dias."},
        ],
    }


def _interpretar(trecho: str, confianca: str = "clara"):
    interpretacao = exigir("src.pipeline.decisoes.interpretacao")
    modelo = IaDecisoes(
        {
            "cancelamento": {
                "arquivo": "marketing.md",
                "trecho_alvo": trecho,
                "texto_corrigido": "O cancelamento pode ser feito em até 7 dias.",
                "confianca": confianca,
            }
        }
    )
    return interpretacao.interpretar_resposta(
        modelo, "Vale 7 dias.", [_ocorrencia()], {"marketing.md": DOC}
    )


def test_spec_0039_ac_005_trecho_nao_localizado_vira_incerta_com_mensagem() -> None:
    """SPECSFY: SPEC-0039 US-001 FR-002 FR-004 NFR-003 AC-005"""
    propostas = _interpretar("O cancelamento é feito em qualquer data do ano.")

    assert len(propostas) == 1
    assert propostas[0].situacao == "incerta"
    assert propostas[0].motivo == MENSAGEM


def test_spec_0039_ac_005_localiza_trecho_exato_e_aproximado() -> None:
    """SPECSFY: SPEC-0039 US-001 FR-002 FR-004 NFR-003 AC-005"""
    localizacao = exigir("src.pipeline.decisoes.localizacao")

    exato = localizacao.localizar_trecho(DOC, "O cancelamento pode ser feito em até 15 dias.")
    assert exato is not None and exato.exata is True
    assert DOC[exato.inicio : exato.fim] == "O cancelamento pode ser feito em até 15 dias."

    aproximado = localizacao.localizar_trecho(DOC, "o cancelamento pode ser feito em ate 15 dias")
    assert aproximado is not None and aproximado.exata is False

    assert localizacao.localizar_trecho(DOC, "Assunto sem relação alguma com o documento.") is None


def test_spec_0039_ac_005_trecho_repetido_e_ambiguo_e_nao_e_localizado() -> None:
    """SPECSFY: SPEC-0039 US-001 FR-002 FR-004 NFR-003 AC-005"""
    localizacao = exigir("src.pipeline.decisoes.localizacao")
    repetido = "Prazo de 15 dias.\n\nOutro assunto.\n\nPrazo de 15 dias.\n"

    assert localizacao.localizar_trecho(repetido, "Prazo de 15 dias.") is None


def test_spec_0039_ac_024_nenhuma_proposta_sem_trecho_localizado_e_clara() -> None:
    """SPECSFY: SPEC-0039 NFR-003 FR-002 AC-024"""
    casos = [
        "Texto que não existe no documento de forma alguma.",
        "",
        "   ",
        "O reembolso",  # curto demais e sem correspondência única de trecho completo
    ]
    for trecho in casos:
        propostas = _interpretar(trecho, confianca="clara")
        assert propostas[0].situacao != "clara", f"trecho {trecho!r} virou clara"


def test_spec_0039_ac_024_trecho_localizado_e_confianca_clara_vira_clara() -> None:
    """SPECSFY: SPEC-0039 NFR-003 FR-002 AC-024"""
    propostas = _interpretar("O cancelamento pode ser feito em até 15 dias.", confianca="clara")

    assert propostas[0].situacao == "clara"

    incerta = _interpretar("O cancelamento pode ser feito em até 15 dias.", confianca="incerta")
    assert incerta[0].situacao == "incerta"
