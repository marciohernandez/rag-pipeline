"""Rotas de grupos de imagens do lote de conversão (SPEC-0040)."""

from __future__ import annotations

import socket

from tests._fase1_grupos import (
    AUTH_MEMBER,
    AUTH_OWNER,
    Img,
    confirmar,
    dados_do_lote,
    documentos_do_grupo,
    enviar,
    executar_todos,
    grupos,
    markdown_de,
    preparar,
)

ANA = [Img(f"ana-{i}.png", 100 + i, i, "ana") for i in range(1, 5)]
BIA = [Img(f"bia-{i}.png", 200 + i, 100 + i, "bia") for i in range(1, 4)]
PASSOS = [Img(f"passo-{i}.png", 300 + i, 400 + i, "tutorial") for i in range(1, 3)]
OCR = {largura: f"texto {largura}" for largura in (101, 102, 103, 104, 201, 202, 203, 301, 302)}


def _nomes_dos_grupos(proposta) -> list[list[str]]:
    return [[i["nome_arquivo"] for i in g["imagens"]] for g in proposta["grupos"]]


def test_spec_0040_ac_005_nada_e_gerado_antes_de_confirmar(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0040 US-002 FR-002 FR-008 NFR-001 AC-005"""
    ctx = preparar(tmp_path, monkeypatch, OCR)

    lote = enviar(ctx, ANA + BIA)

    assert lote["situacao"] == "aguardando_grupos"
    assert ctx.enfileirados == []
    assert {d["situacao"] for d in lote["documentos"]} == {"aguardando_grupos"}
    primeira = grupos(ctx, lote["id"])
    assert _nomes_dos_grupos(primeira) == [[i.nome for i in ANA], [i.nome for i in BIA]]
    assert grupos(ctx, lote["id"]) == primeira  # reabrir preserva a proposta
    assert dados_do_lote(ctx, lote["id"])["situacao"] == "aguardando_grupos"
    for documento in lote["documentos"]:
        resposta = ctx.c.get(
            f"/api/v1/conversoes/{lote['id']}/documentos/{documento['id']}/markdown",
            headers=AUTH_OWNER,
        )
        assert resposta.status_code == 404


def test_spec_0040_ac_005_envio_de_uma_unica_imagem_nao_pede_aprovacao(tmp_path, monkeypatch):
    """SPECSFY: SPEC-0040 US-002 FR-002 FR-008 NFR-001 AC-005"""
    ctx = preparar(tmp_path, monkeypatch, OCR)

    lote = enviar(ctx, ANA[:1])

    assert lote["situacao"] != "aguardando_grupos"
    assert len(ctx.enfileirados) == 1


def test_spec_0040_ac_008_imagem_isolada_vira_documento_proprio(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0040 US-003 FR-003 AC-008"""
    ctx = preparar(tmp_path, monkeypatch, {**OCR, 401: "texto solto"})
    lote = enviar(ctx, ANA[:3] + [Img("solo.png", 401, 900, "outra-pasta")])

    assert confirmar(ctx, lote["id"]).status_code in (200, 202)
    executar_todos(ctx)

    docs = [d for d in dados_do_lote(ctx, lote["id"])["documentos"] if d["situacao"] == "concluido"]
    textos = [markdown_de(ctx, lote["id"], d["id"]) for d in docs]
    assert len(textos) == 2
    assert any("Origem: solo.png" in t and "Origem: ana-1.png" not in t for t in textos)
    assert any(t.count("Origem:") == 3 for t in textos)


def test_spec_0040_ac_010_falha_em_um_grupo_nao_derruba_os_outros(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0040 US-003 FR-004 FR-008 AC-010"""
    erros = {largura: RuntimeError("falha de leitura") for largura in (201, 202, 203)}
    ctx = preparar(tmp_path, monkeypatch, {**OCR, **erros})
    lote = enviar(ctx, ANA + BIA + PASSOS)
    assert confirmar(ctx, lote["id"]).status_code in (200, 202)

    executar_todos(ctx)

    situacoes = [d["situacao"] for d in documentos_do_grupo(ctx, lote["id"])]
    assert situacoes == ["concluido", "falhou", "concluido"]
    falhou = documentos_do_grupo(ctx, lote["id"])[1]
    assert falhou["erro"] and "falha de leitura" not in falhou["erro"]


def test_spec_0040_ac_018_member_nao_ajusta_nem_confirma_mas_ve_a_proposta(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0040 US-002 FR-007 AC-018"""
    ctx = preparar(tmp_path, monkeypatch, OCR)
    lote = enviar(ctx, ANA + BIA)

    ajuste = ctx.c.put(
        f"/api/v1/conversoes/{lote['id']}/grupos",
        json={"grupos": [{"imagens": [d["id"]]} for d in lote["documentos"]]},
        headers=AUTH_MEMBER,
    )

    assert ajuste.status_code == 403
    assert confirmar(ctx, lote["id"], headers=AUTH_MEMBER).status_code == 403
    assert len(grupos(ctx, lote["id"], headers=AUTH_MEMBER)["grupos"]) == 2


def test_spec_0040_ac_019_confirmacao_de_member_nao_gera_documento(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0040 US-002 FR-007 AC-019"""
    ctx = preparar(tmp_path, monkeypatch, OCR)
    lote = enviar(ctx, ANA + BIA)

    resposta = confirmar(ctx, lote["id"], headers=AUTH_MEMBER)

    assert resposta.status_code == 403
    assert ctx.enfileirados == []
    atual = dados_do_lote(ctx, lote["id"])
    assert atual["situacao"] == "aguardando_grupos"
    assert documentos_do_grupo(ctx, lote["id"]) == []


def test_spec_0040_ac_019_ajuste_invalido_e_recusado_com_422(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0040 US-002 FR-007 AC-019"""
    ctx = preparar(tmp_path, monkeypatch, OCR)
    lote = enviar(ctx, ANA[:2] + BIA[:2])
    ids = [d["id"] for d in lote["documentos"]]

    duplicada = ctx.c.put(
        f"/api/v1/conversoes/{lote['id']}/grupos",
        json={"grupos": [{"imagens": ids[:2]}, {"imagens": [ids[1], ids[2], ids[3]]}]},
        headers=AUTH_OWNER,
    )
    vazio = ctx.c.put(
        f"/api/v1/conversoes/{lote['id']}/grupos",
        json={"grupos": [{"imagens": ids}, {"imagens": []}]},
        headers=AUTH_OWNER,
    )

    assert duplicada.status_code == 422
    assert vazio.status_code == 422


def test_spec_0040_ac_023_agrupar_e_confirmar_nao_faz_chamada_externa(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0040 US-001 FR-001 NFR-002 AC-023"""
    from src.pipeline import service

    chamadas: list[object] = []
    monkeypatch.setattr(socket.socket, "connect", lambda *a, **k: chamadas.append(a))
    monkeypatch.setattr(
        service, "criar_modelo_chat", lambda *a, **k: chamadas.append("ia"), raising=False
    )
    ctx = preparar(tmp_path, monkeypatch, OCR)
    lote = enviar(ctx, ANA + BIA)

    assert confirmar(ctx, lote["id"]).status_code in (200, 202)
    executar_todos(ctx)

    assert chamadas == []
    assert all(d["situacao"] == "concluido" for d in documentos_do_grupo(ctx, lote["id"]))


def test_spec_0040_ac_024_reenviar_um_grupo_mantem_a_ordem_aprovada(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0040 FR-003 NFR-001 AC-024"""
    ctx = preparar(tmp_path, monkeypatch, {**OCR, 102: RuntimeError("falha")})
    lote = enviar(ctx, ANA)
    ids_por_nome = {d["nome_arquivo"]: d["id"] for d in lote["documentos"]}
    ordem = ["ana-4.png", "ana-1.png", "ana-3.png", "ana-2.png"]
    ajuste = ctx.c.put(
        f"/api/v1/conversoes/{lote['id']}/grupos",
        json={"grupos": [{"imagens": [ids_por_nome[n] for n in ordem]}]},
        headers=AUTH_OWNER,
    )
    assert ajuste.status_code == 200, ajuste.text
    assert confirmar(ctx, lote["id"]).status_code in (200, 202)
    executar_todos(ctx)
    grupo = documentos_do_grupo(ctx, lote["id"])[0]
    assert grupo["situacao"] == "falhou"

    ctx.estado.ocr[102] = "texto 102"
    resposta = ctx.c.post(
        f"/api/v1/conversoes/{lote['id']}/documentos/{grupo['id']}/reenviar", headers=AUTH_OWNER
    )
    assert resposta.status_code == 200, resposta.text
    executar_todos(ctx)

    md = markdown_de(ctx, lote["id"], grupo["id"])
    posicoes = [md.index(f"Origem: {n}") for n in ordem]
    assert posicoes == sorted(posicoes)


def test_spec_0040_ac_026_vinte_imagens_geram_em_segundo_plano_com_progresso(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0040 US-002 FR-003 NFR-003 AC-026"""
    imagens = [
        Img(f"c{g}-{i:02d}.png", 1000 + g * 10 + i, g * 200 + i, f"conversa-{g}")
        for g in range(4)
        for i in range(1, 6)
    ]
    ocr = {i.largura: f"texto {i.nome}" for i in imagens}
    ctx = preparar(tmp_path, monkeypatch, ocr)
    lote = enviar(ctx, imagens)
    assert len(grupos(ctx, lote["id"])["grupos"]) == 4

    assert confirmar(ctx, lote["id"]).status_code in (200, 202)

    docs = documentos_do_grupo(ctx, lote["id"])
    assert [d["situacao"] for d in docs] == ["fila"] * 4
    assert len(ctx.enfileirados) == 4
    assert dados_do_lote(ctx, lote["id"])["situacao"] == "processando"
    executar_todos(ctx)
    assert [d["situacao"] for d in documentos_do_grupo(ctx, lote["id"])] == ["concluido"] * 4


def test_spec_0040_ac_003_proposta_incerta_nao_traz_nenhum_grupo_pre_aprovado(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0040 US-001 FR-001 FR-002 AC-003"""
    ctx = preparar(tmp_path, monkeypatch, OCR)
    # a conversa da Ana é certa; as duas telas sem numeração deixam a proposta incerta
    soltas = [Img("foto.png", 401, 900, "app"), Img("tela.png", 402, 900, "app")]

    lote = enviar(ctx, ANA + soltas)

    proposta = grupos(ctx, lote["id"])
    assert proposta["certeza"] == "incerta"
    assert [g["certeza"] for g in proposta["grupos"]] == ["total", "incerta"]
    assert [g["aprovado"] for g in proposta["grupos"]] == [False, False]
