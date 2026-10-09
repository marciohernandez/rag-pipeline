"""Documentos da coleção (SPEC-0030, AC-010)."""

from __future__ import annotations

from tests._colecoes import (
    OWNER,
    criar_colecao,
    documentos,
    md,
    preparar,
    texto_com_secoes,
)


def test_apagar_documento_remove_so_os_chunks_dele(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-004 FR-009 FR-015 NFR-004 AC-010"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(
        ambiente,
        "manuais",
        [md("a.md", texto_com_secoes(3)), md("b.md", texto_com_secoes(2, "b1"))],
    )
    por_nome = {d["nome_arquivo"]: d for d in documentos(ambiente, colecao_id)}
    b_antes = {r.id for r in ambiente.armazem.do_arquivo("b.md")}
    envios_antes = ambiente.client.get(
        f"/api/v1/colecoes/{colecao_id}/envios", headers=OWNER
    ).json()
    assert ambiente.armazem.do_arquivo("a.md")

    resposta = ambiente.client.delete(
        f"/api/v1/colecoes/{colecao_id}/documentos/{por_nome['a.md']['id']}", headers=OWNER
    )

    assert resposta.status_code == 204, resposta.text
    assert ambiente.armazem.do_arquivo("a.md") == []
    assert {r.id for r in ambiente.armazem.do_arquivo("b.md")} == b_antes
    assert [d["nome_arquivo"] for d in documentos(ambiente, colecao_id)] == ["b.md"]
    envios_depois = ambiente.client.get(
        f"/api/v1/colecoes/{colecao_id}/envios", headers=OWNER
    ).json()
    assert envios_depois == envios_antes
    assert len(envios_depois) >= 1
