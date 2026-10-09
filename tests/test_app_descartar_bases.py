"""Descarte das Bases antigas e fim das rotas de Base (SPEC-0030, AC-017)."""

from __future__ import annotations

from tests._colecoes import OWNER, preparar
from tests._conexoes import criar_base_vinculada
from tests._pessoas import recurso, sessao_do_banco


def test_descarte_usa_exclusao_existente_e_rotas_de_base_somem(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-006 FR-014 FR-013 AC-017"""
    ambiente = preparar(tmp_path, monkeypatch)
    base_id = criar_base_vinculada(ambiente.embeddings_id, ambiente.qdrant_id)
    removidas: list[str] = []
    monkeypatch.setattr(
        "src.pipeline.service.delete_scope",
        lambda config, **kwargs: removidas.append(config["projeto"]["nome"]) or 0,
    )

    descartar = recurso("src.app.descartar_bases", "descartar_bases")
    descartar()

    from src.app.models import Base

    with sessao_do_banco() as sessao:
        assert sessao.get(Base, base_id).apagada_em is not None
    assert len(removidas) == 1 and base_id in removidas[0]
    client = ambiente.client
    assert client.get("/api/v1/bases", headers=OWNER).status_code == 404
    assert client.post("/api/v1/bases", headers=OWNER).status_code in {404, 405}
    assert (
        client.post(
            f"/api/v1/bases/{base_id}/query", json={"pergunta": "x"}, headers=OWNER
        ).status_code
        == 404
    )
    assert client.get(f"/api/v1/executions/{base_id}", headers=OWNER).status_code == 404
