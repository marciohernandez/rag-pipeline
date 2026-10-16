"""Aplicação da correção confirmada: checkpoint humano, trecho alvo e publicação (SPEC-0039)."""

from __future__ import annotations

from tests._colecoes import documentos, enviar, md
from tests._fase1_decisoes import (
    CORRECAO,
    OWNER,
    TRECHO_MARKETING,
    exigir,
    hash_de,
    interpretar,
    ler_md,
    modelo_orm,
    montar_ciclo,
    proposta_clara,
    propostas,
    publicar,
    url,
)

PRECO = "# Preço\n\nO plano básico custa R$ 50 por mês.\n"
SITE = "# Site\n\nO plano básico custa R$ 70 por mês.\n"
ARQUIVOS = {
    "comercial.md": "# Comercial\n\nO cancelamento pode ser feito em até 7 dias.\n",
    "marketing.md": "# Marketing\n\nO cancelamento pode ser feito em até 15 dias.\n",
    "preco.md": PRECO,
    "site.md": SITE,
}
EXTRACAO = {
    "comercial.md": [("cancelamento prazo", "Cancelamento em até 7 dias.", "alto")],
    "marketing.md": [("prazo de cancelamento", "Cancelamento em até 15 dias.", "alto")],
    "preco.md": [("plano preço", "O plano custa R$ 50.", "alto")],
    "site.md": [("preço do plano", "O plano custa R$ 70.", "alto")],
}
VEREDITO = {
    "cancelamento": ("conflito", "Os prazos divergem."),
    "plano": ("conflito", "Os preços divergem."),
}
CLARA_PRAZO = proposta_clara()
CLARA_PRECO = proposta_clara(
    "site.md", "O plano básico custa R$ 70 por mês.", "O plano básico custa R$ 50 por mês."
)


def _ciclo(tmp_path, monkeypatch, roteiro):
    return montar_ciclo(
        tmp_path,
        monkeypatch,
        roteiro,
        arquivos=ARQUIVOS,
        extracao=EXTRACAO,
        veredito=VEREDITO,
    )


def _confirmar(ctx, **corpo):
    return ctx.c.post(
        url(ctx, "/decisoes/propostas/confirmar"),
        json={"confirmado": True, **corpo},
        headers=OWNER,
    )


def test_spec_0039_ac_007_claras_so_mudam_o_documento_apos_confirmar_o_bloco(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0039 US-002 FR-003 NFR-002 AC-007"""
    ctx = _ciclo(tmp_path, monkeypatch, {"prazo": CLARA_PRAZO, "plano": CLARA_PRECO})
    antes = {nome: ler_md(ctx, nome) for nome in ARQUIVOS}

    lista = interpretar(ctx)

    assert sorted(p["situacao"] for p in lista) == ["clara", "clara"]
    assert {nome: ler_md(ctx, nome) for nome in ARQUIVOS} == antes
    assert publicar(ctx) == 0  # nada foi enviado à coleção

    sem_confirmacao = ctx.c.post(
        url(ctx, "/decisoes/propostas/confirmar"), json={"confirmado": False}, headers=OWNER
    )
    assert sem_confirmacao.status_code == 422
    assert {nome: ler_md(ctx, nome) for nome in ARQUIVOS} == antes

    confirmada = _confirmar(ctx)
    assert confirmada.status_code == 200, confirmada.text
    assert confirmada.json()["aplicadas"] == 2
    publicar(ctx)
    assert "7 dias" in ler_md(ctx, "marketing.md")
    assert "R$ 50" in ler_md(ctx, "site.md")


def test_spec_0039_ac_008_incerta_sem_decisao_nao_muda_o_documento(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-002 FR-003 NFR-002 AC-008"""
    incerta = {**CLARA_PRECO, "confianca": "incerta"}
    ctx = _ciclo(tmp_path, monkeypatch, {"prazo": CLARA_PRAZO, "plano": incerta})
    interpretar(ctx)

    confirmada = _confirmar(ctx)

    assert confirmada.json()["aplicadas"] == 1
    publicar(ctx)
    assert ler_md(ctx, "site.md") == SITE
    restantes = [p for p in propostas(ctx)["propostas"] if p["arquivo"] == "site.md"]
    assert [p["situacao"] for p in restantes] == ["incerta"]


def test_spec_0039_ac_011_so_o_paragrafo_alvo_muda() -> None:
    """SPECSFY: SPEC-0039 US-003 FR-004 NFR-002 AC-011"""
    aplicacao = exigir("src.pipeline.decisoes.aplicacao")
    paragrafos = [f"Parágrafo {i} do documento com texto próprio." for i in range(1, 11)]
    original = "\n\n".join(paragrafos) + "\n"
    novo_quarto = "Parágrafo 4 corrigido pela empresa."

    novo = aplicacao.aplicar_correcao(original, paragrafos[3], novo_quarto)

    esperado = paragrafos[:3] + [novo_quarto] + paragrafos[4:]
    assert novo == "\n\n".join(esperado) + "\n"
    assert novo.encode().startswith(original[: original.index(paragrafos[3])].encode())
    diferentes = [
        a for a, b in zip(original.split("\n\n"), novo.split("\n\n"), strict=True) if a != b
    ]
    assert diferentes == [paragrafos[3]]


def test_spec_0039_ac_011_trecho_nao_localizado_nao_altera_nada() -> None:
    """SPECSFY: SPEC-0039 US-003 FR-004 NFR-002 AC-011"""
    aplicacao = exigir("src.pipeline.decisoes.aplicacao")

    try:
        aplicacao.aplicar_correcao("# Doc\n\nTexto.\n", "Trecho inexistente.", "Novo.")
    except ValueError:
        return
    raise AssertionError("trecho não localizado deveria levantar ValueError")


def test_spec_0039_ac_011_versao_anterior_fica_guardada(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-003 FR-004 NFR-002 AC-011"""
    from src.app.db import SessionLocal

    ctx = _ciclo(tmp_path, monkeypatch, {"prazo": CLARA_PRAZO})
    original = ler_md(ctx, "marketing.md")
    interpretar(ctx)

    assert _confirmar(ctx).status_code == 200
    publicar(ctx)

    Versao = modelo_orm("VersaoDocumento")
    with SessionLocal() as session:
        versoes = session.query(Versao).order_by(Versao.numero).all()
    assert [v.numero for v in versoes] == [1, 2]
    assert versoes[0].hash == hash_de(original)
    assert versoes[1].hash == hash_de(ler_md(ctx, "marketing.md"))
    assert versoes[0].expira_em is not None and versoes[1].expira_em is None


def test_spec_0039_ac_011_documento_alterado_depois_da_analise_recusa_a_correcao(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0039 US-003 FR-004 NFR-002 AC-011"""
    ctx = _ciclo(tmp_path, monkeypatch, {"prazo": CLARA_PRAZO})
    interpretar(ctx)
    alterado = "# Marketing\n\nO cancelamento pode ser feito em até 30 dias.\n"
    assert (
        enviar(ctx.amb, [md("marketing.md", alterado)], colecao_id=ctx.colecao_id).status_code
        == 201
    )

    confirmada = _confirmar(ctx)

    assert confirmada.status_code == 409
    assert ler_md(ctx, "marketing.md") == alterado


def test_spec_0039_ac_015_correcao_reindexa_sem_duplicar_o_documento(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-003 FR-004 AC-015"""
    ctx = _ciclo(tmp_path, monkeypatch, {"prazo": CLARA_PRAZO})
    assert any("15 dias" in r.content for r in ctx.amb.armazem.do_arquivo("marketing.md"))
    interpretar(ctx)

    assert _confirmar(ctx).status_code == 200
    assert publicar(ctx) == 1

    nomes = [d["nome_arquivo"] for d in documentos(ctx.amb, ctx.colecao_id)]
    assert nomes.count("marketing.md") == 1
    vetores = ctx.amb.armazem.do_arquivo("marketing.md")
    assert vetores and all("15 dias" not in r.content for r in vetores)
    assert any(CORRECAO.split(" em ")[-1].rstrip(".") in r.content for r in vetores)
    assert TRECHO_MARKETING not in ler_md(ctx, "marketing.md")
