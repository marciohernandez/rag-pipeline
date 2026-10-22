"""Regras fixas de limpeza (SPEC-0037, US-001, FR-001, FR-002)."""

from __future__ import annotations

from tests._fase1_limpeza import exigir, linhas

RODAPE = "Empresa XPTO — Documento confidencial"
COM_RUIDO = f"""# Política comercial

O plano básico custa 49 reais por mês.

{RODAPE}

Cancelamento em até 7 dias.

1

{RODAPE}

O suporte atende de segunda a sexta.

2

{RODAPE}
"""


def _regras():
    return exigir("src.pipeline.limpeza.regras")


def test_spec_0037_ac_001_ruido_obvio_sai_e_o_negocio_permanece() -> None:
    """SPECSFY: SPEC-0037 US-001 FR-001 FR-002 NFR-002 AC-001"""
    resultado = _regras().aplicar_regras_fixas(COM_RUIDO, "doc.md")

    saida = linhas(resultado.markdown)
    assert RODAPE not in resultado.markdown
    assert "1" not in saida and "2" not in saida
    for frase in (
        "O plano básico custa 49 reais por mês.",
        "Cancelamento em até 7 dias.",
        "O suporte atende de segunda a sexta.",
    ):
        assert frase in resultado.markdown
    assert len(resultado.exclusoes) >= 5
    for exclusao in resultado.exclusoes:
        assert exclusao.arquivo == "doc.md"
        assert exclusao.motivo
        assert exclusao.posicao >= 1
        assert exclusao.camada == "regra"


def test_spec_0037_ac_002_numero_dentro_de_frase_permanece() -> None:
    """SPECSFY: SPEC-0037 US-001 FR-001 NFR-002 AC-002"""
    texto = "O plano básico custa 49 reais por mês.\n\n42\n\nHorário: 8 às 18 horas.\n"

    resultado = _regras().aplicar_regras_fixas(texto, "doc.md")

    assert "O plano básico custa 49 reais por mês." in resultado.markdown
    assert "Horário: 8 às 18 horas." in resultado.markdown
    assert "42" not in linhas(resultado.markdown)
    assert [e.trecho for e in resultado.exclusoes] == ["42"]


def test_spec_0037_ac_003_documento_sem_ruido_nao_muda() -> None:
    """SPECSFY: SPEC-0037 US-001 FR-001 FR-002 AC-003"""
    limpo = (
        "# Planos\n\nO plano básico custa 49 reais por mês.\n\n"
        "O plano pro custa 99 reais por mês.\n"
    )

    resultado = _regras().aplicar_regras_fixas(limpo, "doc.md")

    assert resultado.markdown == limpo
    assert resultado.exclusoes == []
