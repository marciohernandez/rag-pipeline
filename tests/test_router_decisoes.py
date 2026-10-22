"""Rotas da decisão da empresa: permissões, registro, versões, rodadas e liberação (SPEC-0039)."""

from __future__ import annotations

from tests._colecoes import colecao_do_banco, documentos
from tests._fase1_contradicoes import analisar, relatorio, rodar_fila
from tests._fase1_decisoes import (
    CORRECAO,
    MARKETING,
    MEMBER,
    OWNER,
    RESPOSTA,
    TRECHO_MARKETING,
    colar,
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

INCERTA = {**proposta_clara(), "confianca": "incerta"}


def _ciclo(tmp_path, monkeypatch, roteiro=None, **extra):
    return montar_ciclo(
        tmp_path,
        monkeypatch,
        {"cancelamento": proposta_clara()} if roteiro is None else roteiro,
        **extra,
    )


def _decidir(ctx, proposta_id, headers=OWNER, **corpo):
    return ctx.c.post(
        url(ctx, f"/decisoes/propostas/{proposta_id}/decisao"), json=corpo, headers=headers
    )


def _confirmar(ctx, headers=OWNER):
    return ctx.c.post(
        url(ctx, "/decisoes/propostas/confirmar"), json={"confirmado": True}, headers=headers
    )


def _revisar(ctx, confirmado=True, headers=OWNER):
    return ctx.c.post(url(ctx, "/revisar"), json={"confirmado": confirmado}, headers=headers)


def _documento_id(ctx, nome="marketing.md") -> str:
    return next(d["id"] for d in documentos(ctx.amb, ctx.colecao_id) if d["nome_arquivo"] == nome)


def test_spec_0039_ac_002_sem_ia_externa_avisa_nao_chama_a_ia_e_permite_decisao_manual(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0039 US-001 FR-001 NFR-001 AC-002"""
    ctx = _ciclo(tmp_path, monkeypatch)
    desligar = ctx.c.patch(
        f"/api/v1/workspaces/{ctx.workspace_id}/analise-ia",
        json={"ia_externa_permitida": False},
        headers=OWNER,
    )
    assert desligar.status_code == 200, desligar.text

    resposta = colar(ctx)

    assert resposta.status_code == 409
    assert "IA externa" in resposta.json()["detail"]
    assert ctx.modelo_decisoes.chamadas == 0 and not ctx.fila_decisoes

    manual = ctx.c.post(
        url(ctx, "/decisoes/respostas"), json={"texto": RESPOSTA, "manual": True}, headers=OWNER
    )
    assert manual.status_code == 201, manual.text
    lista = propostas(ctx)["propostas"]
    assert [p["situacao"] for p in lista] == ["sem_decisao"]
    decidida = _decidir(
        ctx,
        lista[0]["id"],
        acao="editar",
        arquivo="marketing.md",
        trecho_alvo=TRECHO_MARKETING,
        texto_corrigido=CORRECAO,
    )
    assert decidida.status_code == 200, decidida.text
    publicar(ctx)
    assert CORRECAO in ler_md(ctx, "marketing.md")
    assert ctx.modelo_decisoes.chamadas == 0


def test_spec_0039_ac_006_member_so_consulta(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-001 FR-001 FR-008 AC-006"""
    ctx = _ciclo(tmp_path, monkeypatch)
    lista = interpretar(ctx)
    pid = lista[0]["id"]

    assert colar(ctx, headers=MEMBER).status_code == 403
    assert _confirmar(ctx, headers=MEMBER).status_code == 403
    assert _decidir(ctx, pid, headers=MEMBER, acao="manter").status_code == 403
    assert _revisar(ctx, headers=MEMBER).status_code == 403

    assert propostas(ctx, headers=MEMBER)["propostas"]
    for caminho in ("/decisoes/registro", "/decisoes/rodada"):
        assert ctx.c.get(url(ctx, caminho), headers=MEMBER).status_code == 200
    doc = _documento_id(ctx)
    assert ctx.c.get(url(ctx, f"/documentos/{doc}/versoes"), headers=MEMBER).status_code == 200


def test_spec_0039_ac_009_editar_e_aceitar_aplica_o_texto_editado(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-002 FR-003 FR-004 AC-009"""
    ctx = _ciclo(tmp_path, monkeypatch, {"cancelamento": INCERTA})
    pid = interpretar(ctx)[0]["id"]
    editado = "O cancelamento pode ser feito em até 8 dias."

    resposta = _decidir(ctx, pid, acao="editar", texto_corrigido=editado)

    assert resposta.status_code == 200, resposta.text
    publicar(ctx)
    assert editado in ler_md(ctx, "marketing.md")
    registro = ctx.c.get(url(ctx, "/decisoes/registro"), headers=OWNER).json()
    assert [r["editada"] for r in registro] == [True]
    assert propostas(ctx)["propostas"][0]["situacao"] == "editada"


def test_spec_0039_ac_010_manter_sem_decisao_deixa_a_contradicao_aberta(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0039 US-002 FR-003 AC-010"""
    ctx = _ciclo(tmp_path, monkeypatch, {"cancelamento": INCERTA})
    pid = interpretar(ctx)[0]["id"]

    assert _decidir(ctx, pid, acao="manter").status_code == 200

    assert ler_md(ctx, "marketing.md") == MARKETING
    assert publicar(ctx) == 0
    assert propostas(ctx)["propostas"][0]["situacao"] == "mantida"
    rodada = ctx.c.get(url(ctx, "/decisoes/rodada"), headers=OWNER).json()
    assert rodada["abertas"] == 1


def test_spec_0039_ac_012_registro_de_decisao_completo(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-003 FR-005 AC-012"""
    ctx = _ciclo(tmp_path, monkeypatch)
    interpretar(ctx)
    ocorrencia_id = relatorio(ctx)["ocorrencias"][0]["id"]

    assert _confirmar(ctx).status_code == 200

    registro = ctx.c.get(url(ctx, "/decisoes/registro"), headers=OWNER).json()
    assert len(registro) == 1
    item = registro[0]
    assert item["confirmado_por"] and item["confirmado_em"]
    assert item["ocorrencia_id"] == ocorrencia_id
    assert "7 dias" in item["resposta_trecho"]
    assert item["proposta"] == CORRECAO
    assert item["editada"] is False and item["versao"] == 2 and item["arquivo"] == "marketing.md"


def test_spec_0039_ac_013_owner_volta_a_versao_antiga_e_member_nao(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-003 FR-004 FR-005 FR-008 AC-013"""
    ctx = _ciclo(tmp_path, monkeypatch)
    interpretar(ctx)
    assert _confirmar(ctx).status_code == 200
    publicar(ctx)
    doc = _documento_id(ctx)
    restaurar = url(ctx, f"/documentos/{doc}/versoes/1/restaurar")

    assert ctx.c.post(restaurar, json={"confirmado": True}, headers=MEMBER).status_code == 403
    assert ctx.c.post(restaurar, json={"confirmado": False}, headers=OWNER).status_code == 422
    resposta = ctx.c.post(restaurar, json={"confirmado": True}, headers=OWNER)

    assert resposta.status_code == 200, resposta.text
    publicar(ctx)
    assert ler_md(ctx, "marketing.md") == MARKETING
    versoes = ctx.c.get(url(ctx, f"/documentos/{doc}/versoes"), headers=OWNER).json()
    assert [v["numero"] for v in versoes] == [1, 2, 3]
    assert versoes[2]["hash"] == hash_de(MARKETING) and versoes[2]["atual"] is True
    registro = ctx.c.get(url(ctx, "/decisoes/registro"), headers=OWNER).json()
    assert any(r.get("restaurada_de") == 1 for r in registro)


def test_spec_0039_ac_016_novo_ciclo_mostra_resolvido_novo_e_aberto(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-004 FR-006 AC-016"""
    ctx = _ciclo(tmp_path, monkeypatch)
    interpretar(ctx)
    assert _confirmar(ctx).status_code == 200
    publicar(ctx)
    # a segunda rodada não acha mais o cancelamento, mas acha um assunto novo (reembolso)
    ctx.contradicoes.extracao = {
        "comercial.md": [("reembolso prazo", "Reembolso em até 10 dias.", "alto")],
        "marketing.md": [("prazo de reembolso", "Reembolso em até 30 dias.", "alto")],
    }
    ctx.contradicoes.veredito = {"reembolso": ("conflito", "Os prazos divergem.")}

    assert analisar(ctx).status_code == 202
    rodar_fila(ctx)

    rodada = ctx.c.get(url(ctx, "/decisoes/rodada"), headers=OWNER).json()
    assert (rodada["resolvidas"], rodada["novas"], rodada["abertas"]) == (1, 1, 1)


def test_spec_0039_ac_019_libera_sem_contradicoes_abertas(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-005 FR-007 AC-019"""
    ctx = _ciclo(tmp_path, monkeypatch, {}, veredito={"nenhum-assunto": ("conflito", "x")})
    assert relatorio(ctx)["ocorrencias"] == []

    resposta = _revisar(ctx)

    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["abertas"] == 0
    colecao = colecao_do_banco(ctx.colecao_id)
    assert colecao.revisada_em is not None and colecao.revisada_por


def test_spec_0039_ac_019_com_abertas_exige_confirmacao_explicita(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-005 FR-007 AC-019"""
    ctx = _ciclo(tmp_path, monkeypatch)

    sem = _revisar(ctx, confirmado=False)

    assert sem.status_code == 409
    assert sem.json()["abertas"] == 1
    assert colecao_do_banco(ctx.colecao_id).revisada_em is None
    com = _revisar(ctx, confirmado=True)
    assert com.status_code == 200 and com.json()["abertas"] == 1
    assert colecao_do_banco(ctx.colecao_id).revisada_em is not None
    assert modelo_orm("RespostaEmpresa") is not None


def test_spec_0039_ac_021_member_nao_libera(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0039 US-005 FR-007 FR-008 AC-021"""
    ctx = _ciclo(tmp_path, monkeypatch)

    assert _revisar(ctx, headers=MEMBER).status_code == 403
    assert colecao_do_banco(ctx.colecao_id).revisada_em is None
