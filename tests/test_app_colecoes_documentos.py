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


def test_apagar_documento_e_colecao_remove_o_conteudo_guardado(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0031 US-003 FR-005 FR-009 FR-010 AC-010"""
    from tests._copilot import (
        ModeloCopilot,
        conteudos_do_banco,
        perguntar,
        preparar_copilot,
    )
    from tests._pessoas import pessoa_com_sessao

    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(
        ambiente,
        "manuais",
        [md("manual.md", texto_com_secoes(3, "mm")), md("guia.md", texto_com_secoes(2, "gg"))],
    )
    por_nome = {d["nome_arquivo"]: d for d in documentos(ambiente, colecao_id)}
    assert len(conteudos_do_banco(colecao_id)) == 2

    apagado = ambiente.client.delete(
        f"/api/v1/colecoes/{colecao_id}/documentos/{por_nome['manual.md']['id']}", headers=OWNER
    )
    assert apagado.status_code == 204, apagado.text
    restantes = conteudos_do_banco(colecao_id)
    assert [c.documento_id for c in restantes] == [por_nome["guia.md"]["id"]]

    modelo, _ = preparar_copilot(monkeypatch, modelo=ModeloCopilot(classificacao="processado"))
    _, cab = pessoa_com_sessao(ambiente.client, papel="member")
    resposta = perguntar(ambiente.client, cab, "o que diz o texto mm da seção 1 do manual.md?")
    assert resposta.status_code == 201, resposta.text
    assert "Texto mm da seção 1" not in modelo.contexto()
    assert "não encontr" in modelo.contexto().lower()

    monkeypatch.setattr("src.pipeline.service.drop_collection", lambda *a, **k: None, raising=False)
    removida = ambiente.client.request(
        "DELETE",
        f"/api/v1/colecoes/{colecao_id}",
        json={"confirmacao_nome": "manuais"},
        headers=OWNER,
    )
    assert removida.status_code == 204, removida.text
    assert conteudos_do_banco(colecao_id) == []
