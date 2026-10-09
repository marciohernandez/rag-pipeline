"""Consulta por coleção (SPEC-0030, AC-016)."""

from __future__ import annotations

from tests._colecoes import (
    MEMBER,
    OWNER,
    criar_colecao,
    documentos,
    md,
    preparar,
    texto_com_secoes,
)


def test_consulta_so_devolve_chunks_da_colecao(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-006 FR-013 FR-005 AC-016"""
    ambiente = preparar(tmp_path, monkeypatch)
    manuais = criar_colecao(
        ambiente, "manuais", [md("a.md", texto_com_secoes(2)), md("b.md", texto_com_secoes(2))]
    )
    criar_colecao(ambiente, "politicas", [md("c.md", texto_com_secoes(2))])

    resposta = ambiente.client.post(
        f"/api/v1/colecoes/{manuais}/query",
        json={"pergunta": "o que diz o manual?", "top_k": 10},
        headers=MEMBER,
    )

    assert resposta.status_code == 200, resposta.text
    fontes = {fonte["documento"] for fonte in resposta.json()["chunks_fontes"]}
    assert fontes == {"a.md", "b.md"}
    assert ambiente.client.get(f"/api/v1/colecoes/{manuais}", headers=OWNER).status_code == 200


def test_consulta_sem_documentos_indexados_responde_409(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-006 FR-013 AC-016"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "manuais")
    documento_id = documentos(ambiente, colecao_id)[0]["id"]
    apagado = ambiente.client.delete(
        f"/api/v1/colecoes/{colecao_id}/documentos/{documento_id}", headers=OWNER
    )
    assert apagado.status_code == 204

    resposta = ambiente.client.post(
        f"/api/v1/colecoes/{colecao_id}/query", json={"pergunta": "x"}, headers=OWNER
    )

    assert resposta.status_code == 409
    assert "ainda não tem documentos" in resposta.text


def test_consulta_com_destino_indisponivel_nao_vaza_detalhe(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-006 FR-013 NFR-001 AC-016"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "manuais")

    def falhar(*args, **kwargs):
        raise RuntimeError("endpoint https://qdrant.interno:6333 recusou a chave qd-segredo")

    monkeypatch.setattr("src.pipeline.service.query_base", falhar)
    resposta = ambiente.client.post(
        f"/api/v1/colecoes/{colecao_id}/query", json={"pergunta": "x"}, headers=OWNER
    )

    assert resposta.status_code == 502
    assert "qd-segredo" not in resposta.text and "qdrant.interno" not in resposta.text
