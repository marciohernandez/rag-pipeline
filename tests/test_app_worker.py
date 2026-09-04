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
    # backend real do SDK é substituído por um dublê em memória, sem rede,
    # como nos demais testes que provam comportamento real de indexação.
    monkeypatch.setattr(
        "src.pipeline.indexing.build_vector_store",
        lambda *args, **kwargs: InMemoryVectorStoreAdapter(),
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
