"""Envio e prévia com origem no lote de conversão (SPEC-0043, AC-003, 006, 007, 012 e 013).

Fase RED: ``lote_id`` e ``documento_ids`` ainda não são aceitos por ``POST /envios`` nem por
``POST /ingestao/previa``. O banco é o de testes isolado (transações da suíte) e o vector store
e os embeddings são dublados na fronteira de ``src.pipeline.indexing``.
"""

from __future__ import annotations

from tests._origem_lote import (
    MEMBER,
    OWNER,
    alterar_markdown,
    apagar_arquivos,
    criar_lote_concluido,
    documentos,
    enviar_do_lote,
    hash_do,
    origem_do_banco,
    preparar,
    previa_do_lote,
    texto_com_secoes,
)

A = texto_com_secoes(2, "a")
B = texto_com_secoes(2, "b")


def test_member_nao_usa_o_lote_e_owner_usa(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0043 US-001 FR-010 NFR-001 AC-003"""
    ambiente = preparar(tmp_path, monkeypatch)
    lote_id, ids = criar_lote_concluido(ambiente, {"a.md": A})
    documento_ids = list(ids.values())

    do_member = enviar_do_lote(
        ambiente, lote_id, documento_ids, nova="manuais", headers=MEMBER, executar=False
    )
    previa_member = previa_do_lote(ambiente.client, lote_id, documento_ids, headers=MEMBER)
    do_owner = enviar_do_lote(
        ambiente, lote_id, documento_ids, nova="manuais", headers=OWNER, executar=False
    )

    assert do_member.status_code == 403, do_member.text
    assert previa_member.status_code == 403, previa_member.text
    assert do_owner.status_code == 201, do_owner.text


def test_previa_e_envio_leem_os_md_guardados_no_lote(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0043 US-002 FR-003 FR-004 FR-005 NFR-002 NFR-003 AC-006"""
    ambiente = preparar(tmp_path, monkeypatch)
    lote_id, ids = criar_lote_concluido(ambiente, {"a.md": A, "b.md": B})
    documento_ids = list(ids.values())

    previa = previa_do_lote(ambiente.client, lote_id, documento_ids)
    assert previa.status_code == 200, previa.text
    assert previa.json()["resumo"]["documentos"] == 2

    resposta = enviar_do_lote(ambiente, lote_id, documento_ids, nova="manuais")

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert sorted(d["nome_arquivo"] for d in documentos(ambiente, corpo["colecao_id"])) == [
        "a.md",
        "b.md",
    ]
    assert origem_do_banco(corpo["colecao_id"], "a.md").hash_md == hash_do(A)
    assert origem_do_banco(corpo["colecao_id"], "b.md").hash_md == hash_do(B)


def test_documento_apagado_pela_retencao_recusa_o_envio_sem_criar_nada(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0043 US-002 FR-003 FR-004 NFR-003 AC-007"""
    ambiente = preparar(tmp_path, monkeypatch)
    lote_id, ids = criar_lote_concluido(ambiente, {"a.md": A, "b.md": B})
    apagar_arquivos(ids["b.md"])

    resposta = enviar_do_lote(ambiente, lote_id, list(ids.values()), nova="manuais", executar=False)

    assert resposta.status_code == 409, resposta.text
    assert "b.md" in resposta.text
    listagem = ambiente.client.get(
        f"/api/v1/workspaces/{ambiente.workspace_id}/colecoes", headers=OWNER
    )
    assert listagem.status_code == 200, listagem.text
    assert listagem.json() == []
    assert ambiente.agendamentos == []


def test_reindexar_documento_alterado_substitui_a_versao_e_atualiza_o_hash(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0043 US-003 FR-006 FR-008 FR-010 AC-012"""
    ambiente = preparar(tmp_path, monkeypatch)
    lote_id, ids = criar_lote_concluido(ambiente, {"a.md": A})
    primeiro = enviar_do_lote(ambiente, lote_id, list(ids.values()), nova="manuais")
    assert primeiro.status_code == 201, primeiro.text
    colecao_id = primeiro.json()["colecao_id"]
    novo_texto = texto_com_secoes(3, "revisado")
    alterar_markdown(ids["a.md"], "a.md", novo_texto)

    do_member = enviar_do_lote(
        ambiente, lote_id, list(ids.values()), colecao_id=colecao_id, headers=MEMBER, executar=False
    )
    reindexado = enviar_do_lote(ambiente, lote_id, list(ids.values()), colecao_id=colecao_id)

    assert do_member.status_code == 403, do_member.text
    assert reindexado.status_code == 201, reindexado.text
    assert [d["nome_arquivo"] for d in documentos(ambiente, colecao_id)] == ["a.md"]
    assert origem_do_banco(colecao_id, "a.md").hash_md == hash_do(novo_texto)


def test_lote_de_outro_workspace_responde_404_sem_ler_arquivos(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0043 US-002 FR-004 FR-010 NFR-001 AC-013"""
    ambiente = preparar(tmp_path, monkeypatch)
    lote_alheio, ids = criar_lote_concluido(
        ambiente, {"x.md": A}, tenant="outra-equipe", projeto="outro-projeto"
    )

    envio = enviar_do_lote(
        ambiente, lote_alheio, list(ids.values()), nova="manuais", executar=False
    )
    previa = previa_do_lote(ambiente.client, lote_alheio, list(ids.values()))

    assert envio.status_code == 404, envio.text
    assert previa.status_code == 404, previa.text
    assert ambiente.agendamentos == []
    listagem = ambiente.client.get(
        f"/api/v1/workspaces/{ambiente.workspace_id}/colecoes", headers=OWNER
    )
    assert listagem.json() == []
