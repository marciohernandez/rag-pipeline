"""Testes da autoria dos registros do backend de aplicação (SPEC-0020, fase RED)."""

from __future__ import annotations

from tests._pessoas import atualizar, cliente, pessoa_com_sessao


def _base_por_api(cli, cabecalho, workspace_id: str, tmp_path, monkeypatch) -> str:
    from src.app import storage as storage_module
    from src.app.storage import LocalDirectoryStorage

    monkeypatch.setattr(
        storage_module, "_STORAGE", LocalDirectoryStorage(str(tmp_path / "uploads-spec-0020"))
    )
    envio = cli.post(
        "/api/v1/bases",
        data={"workspace_id": workspace_id},
        files=[("arquivos", ("doc.md", b"# Titulo\n\nConteudo.", "text/markdown"))],
        headers=cabecalho,
    )
    assert envio.status_code == 201
    return envio.json()["base_id"]


def _marcar_processada(base_id: str) -> None:
    from src.app.db import SessionLocal
    from src.app.models import Execution

    with SessionLocal() as sessao:
        sessao.add(Execution(base_id=base_id, situacao="succeeded", etapa="concluido", previstos=1))
        sessao.commit()


def test_autoria_distingue_pessoas_do_mesmo_papel(
    vector_store_em_memoria, tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0020 US-005 FR-010 FR-011 AC-016"""
    from src.pipeline import service
    from src.pipeline.providers.contracts import SearchResult

    monkeypatch.setattr(
        service,
        "query_base",
        lambda _config, _pergunta: [SearchResult(content="trecho", metadata={}, score=1.0)],
    )
    cli = cliente()
    ana, sessao_ana = pessoa_com_sessao(cli, papel="owner", nome="Ana")
    bruno, sessao_bruno = pessoa_com_sessao(cli, papel="owner", nome="Bruno")

    workspace = cli.post("/api/v1/workspaces", json={"nome": "Da Ana"}, headers=sessao_ana)
    assert workspace.status_code == 201
    workspace_id = workspace.json()["id"]
    base_id = _base_por_api(cli, sessao_ana, workspace_id, tmp_path, monkeypatch)
    execucao = cli.post(f"/api/v1/bases/{base_id}/executions", headers=sessao_bruno)
    assert execucao.status_code == 202
    _marcar_processada(base_id)
    consulta = cli.post(
        f"/api/v1/bases/{base_id}/query", json={"pergunta": "o que diz?"}, headers=sessao_bruno
    )
    assert consulta.status_code == 200

    do_workspace = next(
        w
        for w in cli.get("/api/v1/workspaces", headers=sessao_ana).json()
        if w["id"] == workspace_id
    )
    assert do_workspace["criado_por"]["id"] == ana["id"]
    assert do_workspace["criado_por"]["nome"] == "Ana"
    base = cli.get(f"/api/v1/bases/{base_id}", headers=sessao_ana).json()
    assert base["criado_por"]["id"] == ana["id"]
    detalhe = cli.get(f"/api/v1/executions/{execucao.json()['execution_id']}", headers=sessao_ana)
    assert detalhe.json()["criado_por"]["id"] == bruno["id"]
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
