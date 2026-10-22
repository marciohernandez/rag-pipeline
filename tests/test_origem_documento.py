"""Origem do documento indexado a partir de um lote (SPEC-0043, AC-009, 010, 011 e 015).

Fase RED: ``OrigemDocumento``, ``indexado`` no lote e ``origem`` nos documentos da coleção ainda
não existem.
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
    lote_da_api,
    origem_do_banco,
    preparar,
    texto_com_secoes,
)

A = texto_com_secoes(2, "a")
COLUNAS_PERMITIDAS = {
    "id",
    "documento_colecao_id",
    "lote_id",
    "documento_conversao_id",
    "envio_id",
    "hash_md",
    "criado_em",
    "atualizado_em",
}


def _indexar(ambiente, conteudos=None):
    lote_id, ids = criar_lote_concluido(ambiente, conteudos or {"a.md": A})
    resposta = enviar_do_lote(ambiente, lote_id, list(ids.values()), nova="manuais")
    assert resposta.status_code == 201, resposta.text
    return lote_id, ids, resposta.json()["colecao_id"]


def _documento_do_lote(ambiente, lote_id, documento_id, headers=OWNER) -> dict:
    lote = lote_da_api(ambiente, lote_id, headers)
    return next(d for d in lote["documentos"] if d["id"] == documento_id)


def test_documento_indexado_lembra_o_lote_sem_guardar_texto(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0043 US-003 FR-006 NFR-002 AC-009"""
    ambiente = preparar(tmp_path, monkeypatch)
    lote_id, ids, colecao_id = _indexar(ambiente)

    origem = documentos(ambiente, colecao_id)[0]["origem"]
    registro = origem_do_banco(colecao_id, "a.md")

    assert origem["lote_id"] == lote_id
    assert origem["documento_conversao_id"] == ids["a.md"]
    assert registro.hash_md == hash_do(A)
    assert {c.name for c in registro.__table__.columns} <= COLUNAS_PERMITIDAS


def test_md_do_lote_alterado_marca_alterado_desde_a_indexacao(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0043 US-003 FR-006 FR-007 FR-008 NFR-003 AC-010"""
    ambiente = preparar(tmp_path, monkeypatch)
    lote_id, ids, colecao_id = _indexar(ambiente)
    em_dia = _documento_do_lote(ambiente, lote_id, ids["a.md"])["indexado"]
    assert em_dia["situacao_origem"] == "em_dia"
    assert em_dia["colecao_id"] == colecao_id

    alterar_markdown(ids["a.md"], "a.md", texto_com_secoes(3, "reprocessado"))

    do_lote = _documento_do_lote(ambiente, lote_id, ids["a.md"])["indexado"]
    da_colecao = documentos(ambiente, colecao_id)[0]["origem"]
    assert do_lote["situacao_origem"] == "alterado"
    assert da_colecao["situacao_origem"] == "alterado"


def test_arquivo_do_lote_apagado_mostra_expirado_e_mantem_a_origem(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0043 US-003 FR-007 NFR-002 AC-011"""
    ambiente = preparar(tmp_path, monkeypatch)
    lote_id, ids, colecao_id = _indexar(ambiente)

    apagar_arquivos(ids["a.md"])

    do_lote = _documento_do_lote(ambiente, lote_id, ids["a.md"])["indexado"]
    da_colecao = documentos(ambiente, colecao_id)[0]["origem"]
    assert do_lote["situacao_origem"] == "expirado"
    assert da_colecao["situacao_origem"] == "expirado"
    assert da_colecao["lote_id"] == lote_id
    assert origem_do_banco(colecao_id, "a.md").hash_md == hash_do(A)


def test_member_ve_a_origem_e_a_marca_mas_nao_reindexa(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0043 US-003 FR-007 FR-008 FR-010 NFR-001 AC-015"""
    ambiente = preparar(tmp_path, monkeypatch)
    lote_id, ids, colecao_id = _indexar(ambiente)
    alterar_markdown(ids["a.md"], "a.md", texto_com_secoes(3, "reprocessado"))

    visto = documentos(ambiente, colecao_id, headers=MEMBER)[0]["origem"]
    tentativa = enviar_do_lote(
        ambiente, lote_id, list(ids.values()), colecao_id=colecao_id, headers=MEMBER, executar=False
    )

    assert visto["situacao_origem"] == "alterado"
    assert tentativa.status_code == 403, tentativa.text
