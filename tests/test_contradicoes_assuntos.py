"""Normalização e agrupamento por assunto (SPEC-0038, FR-002, FR-003, NFR-002, NFR-003)."""

from __future__ import annotations

from tests._fase1_contradicoes import exigir


def _contratos():
    return exigir("src.pipeline.contradicoes.contratos")


def _assuntos():
    return exigir("src.pipeline.contradicoes.assuntos")


def _afirmacao(arquivo: str, assunto: str, texto: str):
    return _contratos().Afirmacao(arquivo=arquivo, assunto=assunto, texto=texto)


def test_spec_0038_ac_007_um_julgamento_por_assunto_com_so_as_afirmacoes_dele() -> None:
    """SPECSFY: SPEC-0038 US-001 FR-002 NFR-003 AC-007"""
    afirmacoes = [
        _afirmacao("a.md", "cancelamento", "Cancelamento em 7 dias."),
        _afirmacao("b.md", "cancelamento", "Cancelamento em 15 dias."),
        _afirmacao("c.md", "horário de atendimento", "Atendimento até 18h."),
        _afirmacao("d.md", "horário de atendimento", "Atendimento até 20h."),
    ]

    julgamentos = _assuntos().planejar_julgamentos(afirmacoes)

    assert len(julgamentos) == 2
    por_assunto = {j.assunto: {a.arquivo for a in j.afirmacoes} for j in julgamentos}
    assert sorted(por_assunto.values(), key=sorted) == [{"a.md", "b.md"}, {"c.md", "d.md"}]
    todos_os_pares = len(afirmacoes) * (len(afirmacoes) - 1) // 2
    assert len(julgamentos) < todos_os_pares


def test_spec_0038_ac_008_assuntos_diferentes_nao_geram_julgamento() -> None:
    """SPECSFY: SPEC-0038 FR-002 FR-003 NFR-002 AC-008"""
    afirmacoes = [
        _afirmacao("a.md", "horário de atendimento", "Atendimento até 18h."),
        _afirmacao("b.md", "cancelamento", "Cancelamento em 7 dias."),
    ]

    assert _assuntos().planejar_julgamentos(afirmacoes) == []


def test_spec_0038_ac_009_assunto_escrito_de_formas_equivalentes_vira_um_grupo() -> None:
    """SPECSFY: SPEC-0038 US-001 FR-002 NFR-003 AC-009"""
    assuntos = _assuntos()
    assert assuntos.normalizar_assunto("Prazo de Cancelamento") == assuntos.normalizar_assunto(
        "cancelamento: prazo"
    )
    afirmacoes = [
        _afirmacao("a.md", "Prazo de cancelamento", "Cancelamento em 7 dias."),
        _afirmacao("b.md", "cancelamento: prazo", "Cancelamento em 15 dias."),
    ]

    julgamentos = assuntos.planejar_julgamentos(afirmacoes)

    assert len(julgamentos) == 1
    assert {a.arquivo for a in julgamentos[0].afirmacoes} == {"a.md", "b.md"}
