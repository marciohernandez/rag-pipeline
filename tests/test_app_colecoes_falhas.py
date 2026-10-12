"""Falhas em envios e exclusões de coleção (SPEC-0030, AC-007 e AC-015)."""

from __future__ import annotations

from tests._colecoes import (
    CHAVE_QDRANT,
    MEMBER,
    OWNER,
    criar_colecao,
    documentos,
    enviar,
    md,
    preparar,
    texto_com_secoes,
)


def test_falha_do_qdrant_preserva_documento_e_permite_repetir(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-002 FR-005 FR-012 NFR-004 AC-007"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "manuais", [md("a.md", texto_com_secoes(3))])
    antes = documentos(ambiente, colecao_id)[0]
    ambiente.armazem.falhar_escrita = True

    resposta = enviar(ambiente, [md("a.md", texto_com_secoes(3, "v2"))], colecao_id=colecao_id)

    assert resposta.status_code == 201, resposta.text
    envio_id = resposta.json()["envio_id"]
    envio = ambiente.client.get(f"/api/v1/envios/{envio_id}", headers=OWNER).json()
    assert envio["situacao"] == "failed"
    assert envio["erro"]
    assert CHAVE_QDRANT not in envio["erro"]
    assert "qdrant recusou" not in envio["erro"]
    depois = documentos(ambiente, colecao_id)[0]
    assert (depois["chunks"], depois["ultimo_envio_em"]) == (
        antes["chunks"],
        antes["ultimo_envio_em"],
    )
    assert (
        ambiente.client.post(f"/api/v1/envios/{envio_id}/retry", headers=OWNER).status_code == 202
    )
    assert (
        ambiente.client.post(f"/api/v1/envios/{envio_id}/retry", headers=MEMBER).status_code == 403
    )


def test_qdrant_recusa_exclusao_nao_deixa_estado_parcial(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-005 FR-011 NFR-004 NFR-001 AC-015"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "manuais")

    def recusar(*args, **kwargs):
        raise RuntimeError(f"qdrant recusou a exclusão ({CHAVE_QDRANT})")

    monkeypatch.setattr("src.pipeline.service.drop_collection", recusar, raising=False)

    resposta = ambiente.client.request(
        "DELETE",
        f"/api/v1/colecoes/{colecao_id}",
        json={"confirmacao_nome": "manuais"},
        headers=OWNER,
    )

    assert resposta.status_code == 502, resposta.text
    assert "Não foi possível apagar a coleção. Tente novamente." in resposta.text
    assert CHAVE_QDRANT not in resposta.text
    assert "qdrant recusou" not in resposta.text
    assert ambiente.client.get(f"/api/v1/colecoes/{colecao_id}", headers=OWNER).status_code == 200
    assert [d["nome_arquivo"] for d in documentos(ambiente, colecao_id)] == ["a.md"]
