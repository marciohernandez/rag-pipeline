"""Teste de integração do worker Procrastinate real (SPEC-0012, T039/T040).

Diferente dos demais testes de execução (que só provam o agendamento, sem
rodar a tarefa), este roda o worker real do Procrastinate — o mesmo `app`
configurado por `src/app/main.py` com um `PsycopgConnector` real sobre o
Postgres de teste — e confirma que `process_base_task` conclui de ponta a
ponta uma execução agendada pela API de verdade.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_worker_procrastinate_processa_execucao_real(monkeypatch) -> None:
    """SPECSFY: US-001 FR-001 FR-009"""
    from src.app import settings
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Execution
    from src.app.settings import AppSettings
    from src.app.tasks import app as procrastinate_app
    from src.pipeline.providers.vectorstores.in_memory import InMemoryVectorStoreAdapter

    # Config real de escrita exige provider "qdrant" (SyncSafetyPolicy); o
    # backend real do SDK é substituído por um dublê em memória fixo, sem
    # rede — uma única instância compartilhada entre a indexação (via
    # worker) e a consulta/exclusão feitas depois neste teste, para provar
    # de ponta a ponta que o escopo bate nos três caminhos.
    backend_compartilhado = InMemoryVectorStoreAdapter()
    monkeypatch.setattr(
        "src.pipeline.indexing.build_vector_store",
        lambda *args, **kwargs: backend_compartilhado,
    )
    monkeypatch.setattr(
        settings,
        "_SETTINGS",
        AppSettings(
            embedding={"provider": "fake", "dimensions": 16},
            vector_store={"provider": "qdrant", "collection_name": "worker-test"},
        ),
    )

    client = TestClient(app)

    envio = client.post(
        "/api/v1/bases",
        files=[("arquivos", ("doc.md", b"# Titulo\nConteudo de teste.", "text/markdown"))],
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert envio.status_code == 201
    base_id = envio.json()["base_id"]

    inicio = client.post(
        f"/api/v1/bases/{base_id}/executions",
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert inicio.status_code == 202
    execution_id = inicio.json()["execution_id"]

    with SessionLocal() as session:
        execution = session.get(Execution, execution_id)
        assert execution.situacao == "pending"

    # Roda o worker real até esvaziar a fila (sem `wait`, retorna quando não
    # há mais job pendente) — é o mesmo `app` que a API usou para agendar.
    procrastinate_app.run_worker(wait=False, install_signal_handlers=False)

    with SessionLocal() as session:
        execution = session.get(Execution, execution_id)
        assert execution.situacao == "succeeded", execution.erro
        assert execution.inseridos >= 1

    # Prova de ponta a ponta de que o escopo da escrita (via run_pipeline
    # real, sem tenant_id no metadata do chunk — src/pipeline/identity.py)
    # bate com o escopo usado por consulta e exclusão: sem essa consistência
    # (achado do /code-review desta reabertura, corrigido em
    # scope_project_id), a consulta abaixo voltaria sempre vazia e o DELETE
    # nunca encontraria pontos reais para remover.
    consulta = client.post(
        f"/api/v1/bases/{base_id}/query",
        json={"pergunta": "Qual o conteudo de teste?"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert consulta.status_code == 200
    assert consulta.json()["chunks_fontes"], "consulta real voltou vazia — escopo não bateu"

    exclusao = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert exclusao.status_code == 204

    from src.app.tasks import scope_project_id
    from src.pipeline.providers.contracts import LogicalScope

    escopo = LogicalScope(project_id=scope_project_id("tenant-1", "projeto-1", base_id))
    assert backend_compartilhado.list_ids(escopo) == set(), (
        "DELETE não removeu os pontos reais indexados pelo worker"
    )
