"""Ciclo de vida da coleção (SPEC-0030, AC-013, AC-014 e AC-018)."""

from __future__ import annotations

from tests._colecoes import (
    ADMIN,
    OWNER,
    colecao_do_banco,
    criar_colecao,
    enviar,
    md,
    preparar,
    texto_com_secoes,
)


def test_renomear_so_muda_nome_exibido_e_respeita_unicidade(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-005 FR-010 FR-001 AC-013"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "manuais")
    fisico = colecao_do_banco(colecao_id).nome_fisico
    outra = enviar(ambiente, [md("c.md", texto_com_secoes(2))], nova="politicas")
    assert outra.status_code == 201, outra.text

    resposta = ambiente.client.patch(
        f"/api/v1/colecoes/{colecao_id}", json={"nome": "manuais técnicos"}, headers=ADMIN
    )

    assert resposta.status_code == 200, resposta.text
    detalhe = ambiente.client.get(f"/api/v1/colecoes/{colecao_id}", headers=OWNER).json()
    assert detalhe["nome"] == "manuais técnicos"
    assert colecao_do_banco(colecao_id).nome_fisico == fisico

    conflito = ambiente.client.patch(
        f"/api/v1/colecoes/{colecao_id}", json={"nome": "Politicas"}, headers=ADMIN
    )
    assert conflito.status_code == 409, conflito.text
    assert "Já existe uma coleção com esse nome neste Workspace." in conflito.text
    nome = ambiente.client.get(f"/api/v1/colecoes/{colecao_id}", headers=OWNER).json()["nome"]
    assert nome == "manuais técnicos"


def test_apagar_colecao_remove_fisica_e_registros(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-005 FR-011 FR-015 AC-014"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(
        ambiente, "manuais", [md("a.md", texto_com_secoes(3)), md("b.md", texto_com_secoes(2))]
    )
    fisico = colecao_do_banco(colecao_id).nome_fisico
    removidas: list[str] = []
    monkeypatch.setattr(
        "src.pipeline.service.drop_collection",
        lambda config, *a, **k: removidas.append(config["vector_store"]["collection_name"]),
        raising=False,
    )
    url = f"/api/v1/colecoes/{colecao_id}"

    errada = ambiente.client.request(
        "DELETE", url, json={"confirmacao_nome": "outra"}, headers=OWNER
    )
    assert errada.status_code == 422, errada.text
    assert removidas == []

    resposta = ambiente.client.request(
        "DELETE", url, json={"confirmacao_nome": "manuais"}, headers=OWNER
    )

    assert resposta.status_code == 204, resposta.text
    assert removidas == [fisico]
    assert ambiente.client.get(url, headers=OWNER).status_code == 404
    listagem = ambiente.client.get(
        f"/api/v1/workspaces/{ambiente.workspace_id}/colecoes", headers=OWNER
    )
    assert listagem.json() == []
    assert not list(ambiente.pasta.rglob("*.md"))


def test_workspace_com_colecao_nao_pode_ser_apagado(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-006 FR-014 FR-001 AC-018"""
    ambiente = preparar(tmp_path, monkeypatch)
    criar_colecao(ambiente, "manuais")

    resposta = ambiente.client.delete(f"/api/v1/workspaces/{ambiente.workspace_id}", headers=OWNER)

    assert resposta.status_code == 409, resposta.text
    assert (
        "Workspace possui coleções ativas. Apague as coleções antes de continuar." in resposta.text
    )
    nomes = [w["id"] for w in ambiente.client.get("/api/v1/workspaces", headers=OWNER).json()]
    assert ambiente.workspace_id in nomes


def test_lista_colecoes_do_projeto_para_o_assistente(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-006 FR-013 NFR-001 AC-016"""
    from tests._colecoes import OUTRA_EQUIPE

    ambiente = preparar(tmp_path, monkeypatch)
    criar_colecao(ambiente, "manuais")

    do_projeto = ambiente.client.get("/api/v1/colecoes", headers=OWNER)
    de_fora = ambiente.client.get("/api/v1/colecoes", headers=OUTRA_EQUIPE)

    assert do_projeto.status_code == 200, do_projeto.text
    assert [(c["nome"], c["documentos"]) for c in do_projeto.json()] == [("manuais", 1)]
    assert {"id", "workspace_id", "workspace_nome"} <= set(do_projeto.json()[0])
    assert de_fora.json() == []
