"""Testes da autoria dos registros do backend de aplicação (SPEC-0020, fase RED)."""

from __future__ import annotations

from tests._pessoas import atualizar, cliente, pessoa_com_sessao


def test_autoria_distingue_pessoas_do_mesmo_papel(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0020 US-005 FR-010 FR-011 AC-016"""
    from tests._colecoes import AdaptadorFalso, ArmazemFalso, EmbeddingsFalso, md
    from tests._conexoes import (
        criar_conexao_ok,
        payload_embeddings,
        payload_qdrant,
        storage_temporario,
    )

    storage_temporario(tmp_path, monkeypatch)
    armazem = ArmazemFalso()
    monkeypatch.setattr("src.pipeline.indexing.build_embeddings", lambda cfg: EmbeddingsFalso())
    monkeypatch.setattr(
        "src.pipeline.indexing.build_vector_store",
        lambda cfg, persist_dir=None: AdaptadorFalso(client=armazem),
    )
    cli = cliente()
    ana, sessao_ana = pessoa_com_sessao(cli, papel="owner", nome="Ana")
    bruno, sessao_bruno = pessoa_com_sessao(cli, papel="owner", nome="Bruno")

    workspace = cli.post("/api/v1/workspaces", json={"nome": "Da Ana"}, headers=sessao_ana)
    assert workspace.status_code == 201
    workspace_id = workspace.json()["id"]
    embeddings = criar_conexao_ok(cli, payload_embeddings(), headers=sessao_ana)
    qdrant = criar_conexao_ok(cli, payload_qdrant(), headers=sessao_ana)
    envio = cli.post(
        "/api/v1/envios",
        data={
            "workspace_id": workspace_id,
            "nova_colecao": "da-ana",
            "conexao_embeddings_id": embeddings["id"],
            "conexao_vector_store_id": qdrant["id"],
        },
        files=[md("doc.md", "# Titulo\n\n## Parte\n\nConteudo.")],
        headers=sessao_ana,
    )
    assert envio.status_code == 201, envio.text
    colecao_id, envio_id = envio.json()["colecao_id"], envio.json()["envio_id"]
    from tests._colecoes import executar_envio

    executar_envio(envio_id)
    consulta = cli.post(
        f"/api/v1/colecoes/{colecao_id}/query",
        json={"pergunta": "o que diz?"},
        headers=sessao_bruno,
    )
    assert consulta.status_code == 200, consulta.text

    do_workspace = next(
        w
        for w in cli.get("/api/v1/workspaces", headers=sessao_ana).json()
        if w["id"] == workspace_id
    )
    assert do_workspace["criado_por"]["id"] == ana["id"]
    assert do_workspace["criado_por"]["nome"] == "Ana"
    colecao = cli.get(f"/api/v1/colecoes/{colecao_id}", headers=sessao_bruno).json()
    assert colecao["criado_por"]["id"] == ana["id"]
    detalhe = cli.get(f"/api/v1/envios/{envio_id}", headers=sessao_bruno)
    assert detalhe.json()["criado_por"]["id"] == ana["id"]
    assert consulta.json()["criado_por"]["id"] == bruno["id"]


def test_exibe_autor_nao_identificado_e_desativado() -> None:
    """SPECSFY: SPEC-0020 US-005 FR-011 AC-017"""
    from src.app.db import SessionLocal
    from src.app.models import Workspace

    cli = cliente()
    carla, sessao_carla = pessoa_com_sessao(cli, papel="owner", nome="Carla")
    _, sessao_dono = pessoa_com_sessao(cli, papel="owner", nome="Dono")

    with SessionLocal() as sessao:
        legado = Workspace(tenant_id="tenant-1", project_id="projeto-1", nome="Anterior")
        sessao.add(legado)
        sessao.commit()
        legado_id = legado.id
    da_carla = cli.post("/api/v1/workspaces", json={"nome": "Da Carla"}, headers=sessao_carla)
    assert da_carla.status_code == 201

    atualizar("Pessoa", lambda m: m.id == carla["id"], situacao="desativada")
    listagem = {w["id"]: w for w in cli.get("/api/v1/workspaces", headers=sessao_dono).json()}
    assert listagem[legado_id]["criado_por"] is None
    assert listagem[da_carla.json()["id"]]["criado_por"] == {
        "id": carla["id"],
        "nome": "Carla",
        "desativada": True,
    }
