"""Resumo do domínio por Workspace (SPEC-0037, US-002, FR-003, FR-007, FR-008, FR-009)."""

from __future__ import annotations

from tests._fase1_limpeza import (
    AUTH_MEMBER,
    AUTH_OWNER,
    DOMINIO,
    EspiaoIa,
    definir_dominio,
    exigir,
    preparar_lote,
)

PROPOSTA = "A empresa presta consultoria de recursos humanos para o varejo."


def test_spec_0037_ac_005_proposta_e_confirmacao_do_dominio(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0037 US-002 FR-003 FR-004 FR-009 AC-005"""
    limpeza = exigir("src.app.limpeza")
    modelo = EspiaoIa(texto=PROPOSTA)
    monkeypatch.setattr(limpeza, "criar_modelo_ia", lambda session, workspace: modelo)
    enfileirados: list[str] = []
    monkeypatch.setattr(limpeza, "enfileirar_limpeza", enfileirados.append)
    ctx = preparar_lote(tmp_path, monkeypatch, {"a.md": "# A\n\nTexto.\n"}, ia=True)

    limpeza.preparar_limpeza_do_lote(ctx.lote_id)

    lote = ctx.c.get(f"/api/v1/conversoes/{ctx.lote_id}", headers=AUTH_OWNER).json()
    assert lote["situacao"] == "aguardando_dominio"
    proposta = ctx.c.get(f"/api/v1/conversoes/{ctx.lote_id}/dominio-proposto", headers=AUTH_OWNER)
    assert proposta.status_code == 200 and proposta.json()["texto"] == PROPOSTA
    confirmar = ctx.c.post(
        f"/api/v1/conversoes/{ctx.lote_id}/dominio/confirmar",
        json={"texto": PROPOSTA},
        headers=AUTH_OWNER,
    )
    assert confirmar.status_code == 200
    vigente = ctx.c.get(f"/api/v1/workspaces/{ctx.workspace_id}/dominio", headers=AUTH_OWNER).json()
    assert vigente["versao"] == 1 and vigente["texto"] == PROPOSTA
    assert vigente["aprovado_por"] and vigente["criado_em"]
    assert enfileirados == list(ctx.docs.values())


def test_spec_0037_ac_006_reajuste_cria_versao_e_o_relatorio_cita(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0037 US-002 FR-003 FR-007 FR-009 AC-006"""
    limpeza = exigir("src.app.limpeza")
    monkeypatch.setattr(limpeza, "enfileirar_limpeza", lambda documento_id: None)
    ctx = preparar_lote(tmp_path, monkeypatch, {"a.md": "# A\n\nO plano custa 49 reais.\n"})
    assert definir_dominio(ctx, DOMINIO).status_code == 200
    assert definir_dominio(ctx, DOMINIO + " Atendemos o Brasil inteiro.").status_code == 200

    limpeza.preparar_limpeza_do_lote(ctx.lote_id)
    limpeza.limpar_documento(ctx.docs["a.md"])
    limpeza.finalizar_limpeza_lote(ctx.lote_id)

    base = f"/api/v1/workspaces/{ctx.workspace_id}/dominio"
    versoes = ctx.c.get(f"{base}/versoes", headers=AUTH_OWNER).json()
    assert [v["versao"] for v in versoes] == [2, 1]
    assert [v["vigente"] for v in versoes] == [True, False]
    relatorio = ctx.c.get(f"/api/v1/conversoes/{ctx.lote_id}/relatorio", headers=AUTH_OWNER)
    assert "Versão do domínio: 2" in relatorio.text
    assert ctx.c.get(base, headers=AUTH_MEMBER).status_code == 200
    assert ctx.c.get(f"{base}/versoes", headers=AUTH_MEMBER).status_code == 403


def test_spec_0037_ac_007_sem_confirmacao_a_limpeza_nao_comeca(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0037 US-002 FR-003 FR-008 AC-007"""
    limpeza = exigir("src.app.limpeza")
    modelo = EspiaoIa()
    monkeypatch.setattr(limpeza, "criar_modelo_ia", lambda session, workspace: modelo)
    ctx = preparar_lote(tmp_path, monkeypatch, {"a.md": "# A\n\nTexto.\n"}, ia=True)

    limpeza.preparar_limpeza_do_lote(ctx.lote_id)
    limpeza.limpar_documento(ctx.docs["a.md"])

    lote = ctx.c.get(f"/api/v1/conversoes/{ctx.lote_id}", headers=AUTH_OWNER).json()
    assert lote["situacao"] == "aguardando_dominio"
    assert lote["documentos"][0]["limpeza_situacao"] == "aguardando_limpeza"
    assert modelo.chamadas == 0
