"""Permissões e isolamento de coleções (SPEC-0030, AC-012 e AC-019)."""

from __future__ import annotations

import pytest

from tests._colecoes import (
    MEMBER,
    OUTRA_EQUIPE,
    OWNER,
    criar_colecao,
    documentos,
    enviar,
    md,
    preparar,
    texto_com_secoes,
)


@pytest.mark.parametrize("acao", ["envio", "apagar_documento", "renomear", "apagar_colecao"])
def test_member_recebe_403_nas_acoes_de_escrita(acao, tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-004 US-001 FR-010 FR-011 FR-015 NFR-001 AC-012"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "manuais")
    documento_id = documentos(ambiente, colecao_id)[0]["id"]
    client = ambiente.client

    if acao == "envio":
        resposta = enviar(
            ambiente, [md("b.md", texto_com_secoes(2))], colecao_id=colecao_id, headers=MEMBER
        )
    elif acao == "apagar_documento":
        resposta = client.delete(
            f"/api/v1/colecoes/{colecao_id}/documentos/{documento_id}", headers=MEMBER
        )
    elif acao == "renomear":
        resposta = client.patch(
            f"/api/v1/colecoes/{colecao_id}", json={"nome": "outro"}, headers=MEMBER
        )
    else:
        resposta = client.request(
            "DELETE",
            f"/api/v1/colecoes/{colecao_id}",
            json={"confirmacao_nome": "manuais"},
            headers=MEMBER,
        )

    assert resposta.status_code == 403, resposta.text
    assert client.get(f"/api/v1/colecoes/{colecao_id}", headers=OWNER).json()["nome"] == "manuais"
    assert [d["nome_arquivo"] for d in documentos(ambiente, colecao_id)] == ["a.md"]
    assert member_le(ambiente, colecao_id)


def member_le(ambiente, colecao_id: str) -> bool:
    resposta = ambiente.client.get(f"/api/v1/colecoes/{colecao_id}/documentos", headers=MEMBER)
    return resposta.status_code == 200


@pytest.mark.parametrize("acao", ["documentos", "consulta", "renomear"])
def test_outro_tenant_recebe_404(acao, tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 NFR-001 FR-013 FR-008 FR-010 AC-019"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "manuais")
    client = ambiente.client

    if acao == "documentos":
        resposta = client.get(f"/api/v1/colecoes/{colecao_id}/documentos", headers=OUTRA_EQUIPE)
    elif acao == "consulta":
        resposta = client.post(
            f"/api/v1/colecoes/{colecao_id}/query", json={"pergunta": "x"}, headers=OUTRA_EQUIPE
        )
    else:
        resposta = client.patch(
            f"/api/v1/colecoes/{colecao_id}", json={"nome": "invasão"}, headers=OUTRA_EQUIPE
        )

    assert resposta.status_code == 404, resposta.text
    assert "manuais" not in resposta.text
    assert client.get(f"/api/v1/colecoes/{colecao_id}", headers=OWNER).json()["nome"] == "manuais"
