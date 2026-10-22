"""Interpretação da resposta da empresa em propostas por contradição (SPEC-0039)."""

from __future__ import annotations

import copy

from tests._fase1_decisoes import IaDecisoes, exigir

DOCS = {
    "preco.md": "# Preço\n\nO plano básico custa R$ 50 por mês.\n",
    "site.md": "# Site\n\nO plano básico custa R$ 70 por mês.\n",
    "cancelamento.md": "# Cancelamento\n\nO cancelamento ocorre em até 15 dias.\n",
    "suporte.md": "# Suporte\n\nO suporte atende das 8h às 18h.\n",
    "horario.md": "# Horário\n\nO suporte atende das 9h às 17h.\n",
}


def _ocorrencias():
    return [
        {
            "id": "o-preco",
            "assunto": "preço do plano básico",
            "trechos": [
                {"arquivo": "preco.md", "texto": "O plano básico custa R$ 50 por mês."},
                {"arquivo": "site.md", "texto": "O plano básico custa R$ 70 por mês."},
            ],
        },
        {
            "id": "o-cancelamento",
            "assunto": "prazo de cancelamento",
            "trechos": [
                {"arquivo": "cancelamento.md", "texto": "O cancelamento ocorre em até 15 dias."},
                {"arquivo": "preco.md", "texto": "Cancelar leva 7 dias."},
            ],
        },
        {
            "id": "o-suporte",
            "assunto": "horário do suporte",
            "trechos": [
                {"arquivo": "suporte.md", "texto": "O suporte atende das 8h às 18h."},
                {"arquivo": "horario.md", "texto": "O suporte atende das 9h às 17h."},
            ],
        },
    ]


def _roteiro(cobrir: tuple[str, ...] = ("preço", "cancelamento", "suporte")):
    todos = {
        "preço": {
            "arquivo": "site.md",
            "trecho_alvo": "O plano básico custa R$ 70 por mês.",
            "texto_corrigido": "O plano básico custa R$ 50 por mês.",
            "confianca": "clara",
        },
        "cancelamento": {
            "arquivo": "cancelamento.md",
            "trecho_alvo": "O cancelamento ocorre em até 15 dias.",
            "texto_corrigido": "O cancelamento ocorre em até 7 dias.",
            "confianca": "incerta",
        },
        "suporte": {
            "arquivo": "horario.md",
            "trecho_alvo": "O suporte atende das 9h às 17h.",
            "texto_corrigido": "O suporte atende das 8h às 18h.",
            "confianca": "clara",
        },
    }
    return {chave: todos[chave] for chave in cobrir}


def test_spec_0039_ac_001_resposta_gera_uma_proposta_por_contradicao() -> None:
    """SPECSFY: SPEC-0039 US-001 FR-001 FR-002 NFR-001 AC-001"""
    interpretacao = exigir("src.pipeline.decisoes.interpretacao")
    modelo = IaDecisoes(_roteiro())
    documentos = copy.deepcopy(DOCS)

    propostas = interpretacao.interpretar_resposta(
        modelo, "Vale R$ 50, 7 dias e 8h às 18h.", _ocorrencias(), documentos
    )

    assert [p.ocorrencia_id for p in propostas] == ["o-preco", "o-cancelamento", "o-suporte"]
    assert {p.situacao for p in propostas} <= {"clara", "incerta"}
    assert propostas[0].arquivo == "site.md"
    assert propostas[0].texto_corrigido == "O plano básico custa R$ 50 por mês."
    assert modelo.chamadas >= 1
    assert "Vale R$ 50, 7 dias e 8h às 18h." in modelo.prompts[0]
    assert documentos == DOCS  # nenhuma escrita na interpretação


def test_spec_0039_ac_004_contradicao_nao_coberta_fica_sem_decisao() -> None:
    """SPECSFY: SPEC-0039 US-001 FR-002 AC-004"""
    interpretacao = exigir("src.pipeline.decisoes.interpretacao")
    modelo = IaDecisoes(_roteiro(("preço", "cancelamento")))

    propostas = interpretacao.interpretar_resposta(
        modelo, "Vale R$ 50 e 7 dias.", _ocorrencias(), copy.deepcopy(DOCS)
    )

    por_id = {p.ocorrencia_id: p for p in propostas}
    assert len(propostas) == 3
    assert por_id["o-suporte"].situacao == "sem_decisao"
    assert por_id["o-preco"].situacao == "clara"


def test_spec_0039_ac_001_ia_indisponivel_nao_devolve_propostas_parciais() -> None:
    """SPECSFY: SPEC-0039 US-001 FR-001 FR-002 NFR-001 AC-001"""
    interpretacao = exigir("src.pipeline.decisoes.interpretacao")
    modelo = IaDecisoes(_roteiro(), indisponivel=True)

    try:
        interpretacao.interpretar_resposta(modelo, "Vale R$ 50.", _ocorrencias(), DOCS)
    except Exception as erro:  # noqa: BLE001 — qualquer falha deve subir, sem propostas parciais
        assert "Vale R$ 50" not in str(erro)
    else:
        raise AssertionError("a falha da IA deveria interromper a interpretação")


def test_spec_0039_ac_023_corpus_sintetico_corrige_ao_menos_70_por_cento_sem_edicao() -> None:
    """SPECSFY: SPEC-0039 NFR-003 AC-023"""
    interpretacao = exigir("src.pipeline.decisoes.interpretacao")
    aplicacao = exigir("src.pipeline.decisoes.aplicacao")
    documentos, ocorrencias, roteiro, esperado = {}, [], {}, {}
    for i in range(1, 11):
        errado = f"O prazo do item {i} é de 15 dias."
        certo = f"O prazo do item {i} é de 7 dias."
        documentos[f"d{i}.md"] = f"# Item {i}\n\n{errado}\n\nOutro parágrafo {i}.\n"
        esperado[f"d{i}.md"] = f"# Item {i}\n\n{certo}\n\nOutro parágrafo {i}.\n"
        ocorrencias.append(
            {
                "id": f"o{i}",
                "assunto": f"prazo do item {i}",
                "trechos": [
                    {"arquivo": f"d{i}.md", "texto": errado},
                    {"arquivo": "x.md", "texto": certo},
                ],
            }
        )
        # a chave termina em quebra de linha: o bloco traz o assunto em uma linha própria
        # dois de dez vêm com o trecho adulterado: o sistema não deve aplicá-los
        trecho = errado if i <= 8 else errado.replace("prazo", "período")
        roteiro[f"prazo do item {i}\n"] = {
            "arquivo": f"d{i}.md",
            "trecho_alvo": trecho,
            "texto_corrigido": certo,
            "confianca": "clara",
        }
    modelo = IaDecisoes(roteiro)

    propostas = interpretacao.interpretar_resposta(modelo, "Vale 7 dias.", ocorrencias, documentos)

    iguais = 0
    for proposta in propostas:
        if proposta.situacao != "clara":
            continue
        novo = aplicacao.aplicar_correcao(
            documentos[proposta.arquivo], proposta.trecho_alvo, proposta.texto_corrigido
        )
        iguais += novo == esperado[proposta.arquivo]
    assert iguais / len(documentos) >= 0.7
