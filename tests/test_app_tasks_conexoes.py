"""Worker com conexões e compatibilidade com Bases anteriores (SPEC-0026, US-003).

Fase RED: o worker ainda recebe `embedding` e `vector_store` pela fila, não
decifra chaves, não injeta `chunking` e não revalida URLs.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace

from tests._conexoes import (
    CHAVE_EMBEDDINGS,
    CHAVE_QDRANT,
    OWNER,
    capturar_agendamento,
    cliente,
    criar_conexao_ok,
    criar_workspace,
    descrever_colecao,
    payload_embeddings,
    payload_qdrant,
    publicar,
    storage_temporario,
)
from tests._pessoas import recurso, sessao_do_banco


def _publicar_base(client, tmp_path, monkeypatch):
    storage_temporario(tmp_path, monkeypatch)
    descrever_colecao(monkeypatch, existe=False)
    agendamentos = capturar_agendamento(monkeypatch)
    embeddings = criar_conexao_ok(client, payload_embeddings())
    qdrant = criar_conexao_ok(client, payload_qdrant())
    resposta = publicar(
        client, criar_workspace(client), embeddings["id"], qdrant["id"], colecao="politicas"
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json(), embeddings, qdrant, agendamentos


def _executar(agendamento: dict, monkeypatch, *, falhar: bool = False) -> dict:
    """Roda o worker com a fachada falsa e devolve a configuração que ele montou."""
    from src.app import tasks

    capturado: dict = {}

    def run_pipeline(config, **kwargs):
        capturado["config"] = config
        return SimpleNamespace(chunks=[])

    def sync(config, chunks):
        if falhar:
            raise RuntimeError("falha simulada do destino")
        return SimpleNamespace(previstos=0, inseridos=0, mantidos=0, removidos=0)

    monkeypatch.setattr("src.pipeline.service.run_pipeline", run_pipeline)
    monkeypatch.setattr("src.pipeline.service.sync_vector_store", sync)
    argumentos = dict(agendamento)
    tasks.process_base_task.func(argumentos.pop("execution_id"), **argumentos)
    return capturado


def test_worker_decifra_so_em_memoria_e_a_repeticao_reusa_os_parametros(
    tmp_path, monkeypatch, caplog
) -> None:
    """SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-001 NFR-005 AC-013"""
    client = cliente()
    publicada, embeddings, qdrant, agendamentos = _publicar_base(client, tmp_path, monkeypatch)
    argumentos = agendamentos[0]

    texto_dos_argumentos = json.dumps(argumentos, default=str)
    assert CHAVE_EMBEDDINGS not in texto_dos_argumentos
    assert CHAVE_QDRANT not in texto_dos_argumentos
    assert embeddings["id"] in texto_dos_argumentos
    assert qdrant["id"] in texto_dos_argumentos
    assert "embedding" not in argumentos and "vector_store" not in argumentos

    with caplog.at_level(logging.DEBUG):
        configuracao = _executar(argumentos, monkeypatch, falhar=True)["config"]
    assert configuracao["chunking"]["default_splitter"] == "header"
    assert configuracao["chunking"]["default_chunk_size"] == 800
    assert configuracao["chunking"]["default_chunk_overlap"] == 100
    assert CHAVE_EMBEDDINGS not in caplog.text and CHAVE_QDRANT not in caplog.text
    execucao = client.get(f"/api/v1/executions/{publicada['execution_id']}", headers=OWNER)
    assert execucao.json()["situacao"] == "failed"

    repeticao = client.post(f"/api/v1/executions/{publicada['execution_id']}/retry", headers=OWNER)
    assert repeticao.status_code == 202, repeticao.text
    reagendado = agendamentos[-1]
    assert reagendado["conexao_embeddings_id"] == embeddings["id"]
    assert reagendado["conexao_vector_store_id"] == qdrant["id"]


def test_worker_revalida_a_url_da_conexao_antes_de_conectar(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-001 NFR-005 AC-013"""
    client = cliente()
    publicada, _embeddings, qdrant, agendamentos = _publicar_base(client, tmp_path, monkeypatch)
    conexao = recurso("src.app.models", "Conexao")
    with sessao_do_banco() as sessao:
        linha = sessao.get(conexao, qdrant["id"])
        linha.configuracao = {"url": "http://169.254.169.254/latest"}
        sessao.commit()

    configuracao = _executar(agendamentos[0], monkeypatch)

    assert "config" not in configuracao
    execucao = client.get(f"/api/v1/executions/{publicada['execution_id']}", headers=OWNER)
    assert execucao.json()["situacao"] == "failed"
    assert "169.254" not in execucao.text


def test_base_anterior_sem_vinculos_usa_a_configuracao_global(monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-005 AC-014"""
    import src.app.main  # noqa: F401 — liga banco e configuração
    from src.app import settings
    from src.app.models import Base, Execution, Workspace
    from src.app.settings import AppSettings

    monkeypatch.setattr(
        settings,
        "_SETTINGS",
        AppSettings(
            embedding={"provider": "fake", "dimensions": 16},
            vector_store={"provider": "in_memory", "collection_name": "global"},
        ),
    )
    with sessao_do_banco() as sessao:
        workspace = Workspace(tenant_id="tenant-1", project_id="projeto-1", nome="WS legado")
        sessao.add(workspace)
        sessao.flush()
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            workspace_id=workspace.id,
            nome="legada.md",
            origem="upload",
            collection_name="global",
            documentos=1,
        )
        sessao.add(base)
        sessao.flush()
        execucao = Execution(base_id=base.id, situacao="pending", etapa="")
        sessao.add(execucao)
        sessao.commit()
        base_id, execucao_id = base.id, execucao.id
    capturado: dict = {}
    monkeypatch.setattr(
        "src.pipeline.service.run_pipeline",
        lambda config, **kw: capturado.update(config=config) or SimpleNamespace(chunks=[]),
    )
    monkeypatch.setattr(
        "src.pipeline.service.sync_vector_store",
        lambda config, chunks: SimpleNamespace(previstos=0, inseridos=0, mantidos=0, removidos=0),
    )
    from src.app import tasks

    tasks.process_base_task.func(
        execucao_id,
        base_id=base_id,
        tenant_id="tenant-1",
        project_id="projeto-1",
        conexao_embeddings_id=None,
        conexao_vector_store_id=None,
    )

    assert capturado["config"]["embedding"]["provider"] == "fake"
    assert capturado["config"]["vector_store"]["collection_name"] == "global"
    assert capturado["config"].get("chunking", {}).get("default_splitter") in (None, "header")
    with sessao_do_banco() as sessao:
        assert sessao.get(Execution, execucao_id).situacao == "succeeded"
