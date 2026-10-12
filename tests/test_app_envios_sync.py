"""Sincronização por documento nos envios (SPEC-0030, AC-004, AC-005 e AC-020).

Fase RED: o worker ``process_envio_task`` e a identidade por documento não existem.
"""

from __future__ import annotations

from tests._colecoes import (
    OWNER,
    criar_colecao,
    documentos,
    enviar,
    md,
    preparar,
    texto_com_secoes,
)


def _envio(ambiente, envio_id: str) -> dict:
    resposta = ambiente.client.get(f"/api/v1/envios/{envio_id}", headers=OWNER)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_reenvio_identico_nao_gera_embedding(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-002 FR-004 FR-005 NFR-002 AC-004"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "manuais", [md("a.md", texto_com_secoes(3))])
    antes = documentos(ambiente, colecao_id)[0]
    embeddings_antes = len(ambiente.embeddings.textos)
    ids_antes = {r.id for r in ambiente.armazem.todos()}
    assert antes["chunks"] >= 2

    resposta = enviar(ambiente, [md("a.md", texto_com_secoes(3))], colecao_id=colecao_id)

    assert resposta.status_code == 201, resposta.text
    envio = _envio(ambiente, resposta.json()["envio_id"])
    assert envio["situacao"] == "succeeded"
    assert (envio["previstos"], envio["inseridos"], envio["mantidos"], envio["removidos"]) == (
        antes["chunks"],
        0,
        antes["chunks"],
        0,
    )
    assert len(ambiente.embeddings.textos) == embeddings_antes
    assert {r.id for r in ambiente.armazem.todos()} == ids_antes
    depois = documentos(ambiente, colecao_id)
    assert [(d["id"], d["chunks"]) for d in depois] == [(antes["id"], antes["chunks"])]


def test_nova_versao_substitui_so_o_documento(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-002 FR-004 FR-005 FR-006 AC-005"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(
        ambiente,
        "manuais",
        [md("a.md", texto_com_secoes(3, "v1")), md("b.md", texto_com_secoes(2, "b1"))],
    )
    b_antes = {r.id for r in ambiente.armazem.do_arquivo("b.md")}
    assert b_antes
    nova_versao = "Conteúdo reescrito da versão dois do documento A, sem cabeçalhos. " * 4

    resposta = enviar(
        ambiente,
        [md("a.md", nova_versao)],
        colecao_id=colecao_id,
        splitter="character_split",
    )

    assert resposta.status_code == 201, resposta.text
    registros_a = ambiente.armazem.do_arquivo("a.md")
    assert registros_a
    assert all("v1" not in r.content for r in registros_a)
    assert all("versão dois" in r.content for r in registros_a)
    assert {r.id for r in ambiente.armazem.do_arquivo("b.md")} == b_antes
    por_nome = {d["nome_arquivo"]: d for d in documentos(ambiente, colecao_id)}
    assert "character_split" in str(por_nome["a.md"]["chunking"])
    assert "character_split" not in str(por_nome["b.md"]["chunking"])
    assert por_nome["a.md"]["chunks"] == len(registros_a)


def test_envio_misto_gera_embeddings_so_do_necessario(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 NFR-002 FR-005 FR-006 AC-020"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(
        ambiente,
        "manuais",
        [md("a.md", texto_com_secoes(3)), md("b.md", texto_com_secoes(2, "b1"))],
    )
    embeddings_antes = len(ambiente.embeddings.textos)
    b_alterado = texto_com_secoes(2, "b1").replace("Texto b1 da seção 2", "Texto b2 da seção 2")

    resposta = enviar(
        ambiente,
        [
            md("a.md", texto_com_secoes(3)),
            md("b.md", b_alterado),
            md("c.md", texto_com_secoes(4, "c1")),
        ],
        colecao_id=colecao_id,
    )

    assert resposta.status_code == 201, resposta.text
    novos = ambiente.embeddings.textos[embeddings_antes:]
    assert len(novos) == 5
    assert sum("b2" in texto for texto in novos) == 1
    assert sum("c1" in texto for texto in novos) == 4
    assert not any("Texto v1" in texto for texto in novos)
