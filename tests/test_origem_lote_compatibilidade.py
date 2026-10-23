"""O caminho manual segue igual e as três origens são exclusivas (SPEC-0043, AC-008)."""

from __future__ import annotations

from tests._origem_lote import (
    OWNER,
    criar_lote_concluido,
    md,
    preparar,
    previa_do_lote,
    texto_com_secoes,
)


def test_upload_manual_segue_igual_e_combinar_origens_e_recusado(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0043 US-002 FR-009 NFR-004 AC-008"""
    ambiente = preparar(tmp_path, monkeypatch)
    lote_id, ids = criar_lote_concluido(ambiente, {"l.md": texto_com_secoes(2, "l")})
    arquivo = md("m.md", texto_com_secoes(2, "m"))
    base = {
        "workspace_id": ambiente.workspace_id,
        "splitter": "header",
        "chunk_size": "800",
        "chunk_overlap": "100",
    }

    previa_manual = ambiente.client.post(
        "/api/v1/ingestao/previa", data=base, files=[arquivo], headers=OWNER
    )
    envio_manual = ambiente.client.post(
        "/api/v1/envios",
        data={
            **base,
            "nova_colecao": "manuais",
            "conexao_embeddings_id": ambiente.embeddings_id,
            "conexao_vector_store_id": ambiente.qdrant_id,
        },
        files=[arquivo],
        headers=OWNER,
    )
    envio_misto = ambiente.client.post(
        "/api/v1/envios",
        data={
            **base,
            "nova_colecao": "mistas",
            "lote_id": lote_id,
            "documento_ids": list(ids.values()),
            "conexao_embeddings_id": ambiente.embeddings_id,
            "conexao_vector_store_id": ambiente.qdrant_id,
        },
        files=[arquivo],
        headers=OWNER,
    )
    envio_com_preparada = ambiente.client.post(
        "/api/v1/envios",
        data={
            **base,
            "nova_colecao": "preparadas",
            "lote_id": lote_id,
            "documento_ids": list(ids.values()),
            "usar_base_preparada": "true",
            "conexao_embeddings_id": ambiente.embeddings_id,
            "conexao_vector_store_id": ambiente.qdrant_id,
        },
        headers=OWNER,
    )
    previa_mista = previa_do_lote(
        ambiente.client, lote_id, list(ids.values()), usar_base_preparada="true"
    )

    assert previa_manual.status_code == 200, previa_manual.text
    assert envio_manual.status_code == 201, envio_manual.text
    assert envio_misto.status_code == 422, envio_misto.text
    assert envio_com_preparada.status_code == 422, envio_com_preparada.text
    assert previa_mista.status_code == 422, previa_mista.text
