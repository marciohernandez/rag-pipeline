"""Duplicidade entre documentos do lote (SPEC-0037, US-004, FR-006, FR-007)."""

from __future__ import annotations

from tests._fase1_limpeza import exigir

BASE = (
    "A política de cancelamento permite que o cliente desista do contrato em até sete dias "
    "corridos após a assinatura, sem multa, mediante aviso por escrito enviado ao suporte "
    "da empresa, que confirma o cancelamento em até dois dias úteis e devolve o valor pago "
    "integralmente na mesma forma de pagamento escolhida pelo cliente no momento da compra."
)


def _variar(texto: str, quantidade: int) -> str:
    """Troca `quantidade` caracteres por 'Z', que não existem no texto base."""
    return "Z" * quantidade + texto[quantidade:]


def _dedup():
    return exigir("src.pipeline.limpeza.duplicidade")


def test_spec_0037_ac_011_paragrafo_repetido_fica_uma_vez() -> None:
    """SPECSFY: SPEC-0037 US-004 FR-006 FR-007 AC-011"""
    resultado = _dedup().deduplicar(
        [("a.md", f"# A\n\n{BASE}\n"), ("b.md", f"# B\n\n{BASE}\n\nOutro assunto qualquer.\n")]
    )

    assert BASE in resultado.documentos["a.md"]
    assert BASE not in resultado.documentos["b.md"]
    assert "Outro assunto qualquer." in resultado.documentos["b.md"]
    [exclusao] = resultado.exclusoes
    assert exclusao.camada == "duplicidade"
    assert exclusao.arquivo == "b.md" and exclusao.mantido_em == "a.md"


def test_spec_0037_ac_012_limite_de_semelhanca_e_trecho_curto() -> None:
    """SPECSFY: SPEC-0037 US-004 FR-006 NFR-002 AC-012

    O 96% e o 94% da spec são exercitados por 97% e 93% para não depender da
    fórmula exata de razão; o limite configurado continua 95%.
    """
    quase = _variar(BASE, 12)
    abaixo = _variar(BASE, 28)
    curto_a = "O plano básico custa 49 reais por mês, sem fidelidade."
    curto_b = "O plano básico custa 59 reais por mês, sem fidelidade."

    removido = _dedup().deduplicar([("a.md", BASE + "\n"), ("b.md", quase + "\n")])
    mantido = _dedup().deduplicar([("a.md", BASE + "\n"), ("b.md", abaixo + "\n")])
    curtos = _dedup().deduplicar([("a.md", curto_a + "\n"), ("b.md", curto_b + "\n")])

    assert quase not in removido.documentos["b.md"]
    assert removido.exclusoes and removido.exclusoes[0].camada == "duplicidade"
    assert abaixo in mantido.documentos["b.md"]
    assert not mantido.exclusoes
    assert curto_b in curtos.documentos["b.md"] and not curtos.exclusoes


def test_spec_0037_ac_019_semelhante_vai_ao_relatorio_sem_remover() -> None:
    """SPECSFY: SPEC-0037 US-004 FR-006 FR-007 AC-019"""
    parecido = _variar(BASE, 60)

    resultado = _dedup().deduplicar([("a.md", BASE + "\n"), ("b.md", parecido + "\n")])

    assert BASE in resultado.documentos["a.md"]
    assert parecido in resultado.documentos["b.md"]
    assert not resultado.exclusoes
    assert [(p.arquivo_a, p.arquivo_b) for p in resultado.provaveis] == [("a.md", "b.md")]
