"""Testes de integração do worker Procrastinate real (SPEC-0012, Fase 9 — T044–T047).

Reabertura de 2026-09-07: um teste de ponta a ponta manual mostrou que o
caminho assíncrono nunca funcionou fora da suíte. ``configure_connector``
(``src/app/tasks.py``) só reatribui ``app.connector``, deixando
``app.job_manager.connector`` no ``InMemoryConnector`` de placeholder — e é o
``job_manager`` que ``task.defer()`` usa. Resultado: nenhum job chega a
``procrastinate_jobs`` no Postgres e nenhum worker fora do processo o consome.
O teste anterior (``test_worker_procrastinate_processa_execucao_real``)
mascarava rodando ``app.run_worker(wait=False)`` no mesmo processo contra esse
mesmo connector em memória.

Estes quatro casos provam o ciclo real pela fila no Postgres de teste. Ver a
seção 8 da spec ("Fiação do connector Procrastinate") e a seção 11
("Worker assíncrono real").
"""

from __future__ import annotations

from collections.abc import Iterator

import psycopg
import pytest
from fastapi.testclient import TestClient


def _conninfo() -> str:
    """Conninfo libpq puro do Postgres de teste (mesmo destino do ``APP_DATABASE_URL``)."""
    from src.app.main import _procrastinate_conninfo

    return _procrastinate_conninfo()


def _linhas_process_envio_task() -> list[tuple[str, str]]:
    """``(id, status)`` de cada job ``process_envio_task`` em ``procrastinate_jobs``."""
    with psycopg.connect(_conninfo()) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id::text, status::text FROM procrastinate_jobs WHERE task_name = %s",
            ("process_envio_task",),
        )
        return list(cur.fetchall())


@pytest.fixture(autouse=True)
def _fila_limpa(_isolar_backend) -> Iterator[None]:
    """Cada caso recebe uma fila nova no schema exclusivo, sem apagar jobs."""
    assert _linhas_process_envio_task() == []
    yield


def _preparar_backend(monkeypatch, tmp_path) -> object:
    """Dubla embeddings e vector store na fronteira do pipeline, sem rede.

    Devolve o backend em memória para inspeção. ``SyncSafetyPolicy`` só aceita
    ``provider: "qdrant"`` para sincronizar, então o dublê é injetado por
    ``monkeypatch`` de ``build_vector_store`` e ``build_embeddings``.
    """
    from src.pipeline.providers.vectorstores.in_memory import InMemoryVectorStoreAdapter
    from tests._colecoes import EmbeddingsFalso
    from tests._conexoes import storage_temporario

    storage_temporario(tmp_path, monkeypatch)
    backend = InMemoryVectorStoreAdapter()
    monkeypatch.setattr(
        "src.pipeline.indexing.build_vector_store",
        lambda *args, **kwargs: backend,
    )
    monkeypatch.setattr("src.pipeline.indexing.build_embeddings", lambda cfg: EmbeddingsFalso())
    return backend


def _enviar_e_agendar(client: TestClient) -> tuple[str, str]:
    """Envia um documento e agenda o processamento pelo caminho real da API.

    Devolve ``(colecao_id, envio_id)``.
    """
    from tests._conexoes import (
        criar_conexao_ok,
        criar_workspace,
        payload_embeddings,
        payload_qdrant,
    )

    embeddings = criar_conexao_ok(client, payload_embeddings())
    qdrant = criar_conexao_ok(client, payload_qdrant())
    envio = client.post(
        "/api/v1/envios",
        data={
            "workspace_id": criar_workspace(client),
            "nova_colecao": "worker",
            "conexao_embeddings_id": embeddings["id"],
            "conexao_vector_store_id": qdrant["id"],
        },
        files=[("arquivos", ("doc.md", b"# Titulo\nConteudo de teste.", "text/markdown"))],
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert envio.status_code == 201, envio.text
    return envio.json()["colecao_id"], envio.json()["envio_id"]


def _drenar_worker_fora_do_processo() -> None:
    """Consome a fila com um ``App``/``PsycopgConnector`` próprio, que NÃO
    compartilha o objeto ``app`` em memória do processo da API.

    Um ``App`` novo com connector real ligado ao mesmo ``APP_DATABASE_URL``,
    reaproveitando só o registro de tarefas — equivale a outro processo
    consumindo a fila, sem tocar ``src.app.tasks.app`` (cujo
    ``job_manager.connector`` continua o placeholder até o fix da Fase 9).
    Uma alternativa seria um subprocesso ``python -m procrastinate ... worker``,
    mas ele não herdaria os ``monkeypatch`` de embeddings/vector store do teste.
    """
    from procrastinate import App, PsycopgConnector

    from src.app.tasks import app as api_app

    worker_app = App(connector=PsycopgConnector(conninfo=_conninfo()))
    worker_app.tasks = api_app.tasks
    worker_app.run_worker(wait=False, install_signal_handlers=False)


def test_configure_connector_liga_o_job_manager() -> None:
    """SPECSFY: US-001 FR-001

    ``configure_connector`` precisa ligar **os dois** ponteiros de connector do
    ``App`` — ``connector`` e ``job_manager.connector`` —, porque ``task.defer()``
    roteia pelo ``job_manager``. Trocar só ``app.connector`` faz o agendamento
    cair no ``InMemoryConnector`` de placeholder.
    """
    from procrastinate.testing import InMemoryConnector

    from src.app import tasks

    connector_original = tasks.app.connector
    job_manager_original = tasks.app.job_manager.connector
    dublê = InMemoryConnector()
    try:
        tasks.configure_connector(dublê)
        assert tasks.app.connector is dublê
        assert tasks.app.job_manager.connector is dublê, (
            "configure_connector não ligou o job_manager ao novo connector — "
            "task.defer() continuaria usando o connector antigo"
        )
    finally:
        tasks.app.connector = connector_original
        tasks.app.job_manager.connector = job_manager_original


def test_agendamento_persiste_linha_em_procrastinate_jobs(monkeypatch, tmp_path) -> None:
    """SPECSFY: US-001 FR-001 FR-002

    ``POST /api/v1/bases/{id}/executions`` (caminho real da API) deve gravar um
    job em ``procrastinate_jobs`` no Postgres de teste, consultável por outro
    processo. Hoje o ``defer`` cai no connector em memória e nada é persistido.
    """
    _preparar_backend(monkeypatch, tmp_path)
    from src.app.main import app

    assert _linhas_process_envio_task() == []

    client = TestClient(app)
    _enviar_e_agendar(client)

    linhas = _linhas_process_envio_task()
    assert linhas, (
        "nenhuma linha process_envio_task em procrastinate_jobs — o defer não "
        "chegou ao Postgres (job_manager ainda no InMemoryConnector)"
    )


def test_worker_fora_do_processo_conclui_execucao(monkeypatch, tmp_path) -> None:
    """SPECSFY: US-001 FR-001 FR-009

    Um worker que não compartilha o objeto ``app`` em memória do processo da API
    — connector ``PsycopgConnector`` real ligado ao mesmo Postgres — drena a
    fila e leva a ``Execution`` agendada pela API a ``succeeded`` com
    ``inseridos >= 1``.
    """
    _preparar_backend(monkeypatch, tmp_path)
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Envio

    client = TestClient(app)
    _colecao_id, envio_id = _enviar_e_agendar(client)

    with SessionLocal() as session:
        assert session.get(Envio, envio_id).situacao == "queued"

    _drenar_worker_fora_do_processo()

    with SessionLocal() as session:
        execution = session.get(Envio, envio_id)
        assert execution.situacao == "succeeded", execution.erro
        assert execution.inseridos >= 1


def test_estado_recuperavel_apos_worker_externo(monkeypatch, tmp_path) -> None:
    """SPECSFY: US-001 FR-002 NFR-004

    NFR-004: depois de um worker fora do processo concluir, uma sessão nova do
    lado da API lê o estado íntegro da ``Execution`` do Postgres — não de
    memória do processo que agendou.
    """
    _preparar_backend(monkeypatch, tmp_path)
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Envio

    client = TestClient(app)
    _colecao_id, envio_id = _enviar_e_agendar(client)

    _drenar_worker_fora_do_processo()

    # Sessão nova = simula outro processo (API reiniciada) lendo o mesmo Postgres.
    with SessionLocal() as session:
        execution = session.get(Envio, envio_id)
        assert execution.situacao == "succeeded", execution.erro
        assert execution.etapa == "concluido"
        assert execution.previstos >= 1
        assert execution.concluido_em is not None


# ---------------------------------------------------------------------------
# Fase 10 (reabertura 2026-09-07): entrypoint de worker documentado
# ---------------------------------------------------------------------------


def test_worker_entrypoint_usa_connector_real_do_postgres() -> None:
    """SPECSFY: US-001 FR-001

    O comando documentado no README (`python -m procrastinate --app
    src.app.worker.app worker`) só consome a fila do Postgres se o `app` que a
    CLI recebe já estiver ligado ao `PsycopgConnector` real. `src.app.tasks.app`
    nasce com `InMemoryConnector` e só `src.app.main` o religa; `src.app.worker`
    importa `src.app.main` para herdar essa fiação antes de expor `app`.
    """
    from procrastinate import PsycopgConnector
    from procrastinate.testing import InMemoryConnector

    from src.app import worker

    assert isinstance(worker.app.connector, PsycopgConnector)
    assert isinstance(worker.app.job_manager.connector, PsycopgConnector)
    assert not isinstance(worker.app.job_manager.connector, InMemoryConnector)
    # `task.defer()` roteia pelo job_manager: os dois ponteiros precisam ser o mesmo connector real.
    assert worker.app.connector is worker.app.job_manager.connector


def test_worker_entrypoint_reexpoe_o_mesmo_app_de_tasks() -> None:
    """SPECSFY: US-001 FR-001

    O `app` que a CLI recebe precisa ser o mesmo objeto de `src.app.tasks` —
    é nele que `@app.task(name="process_envio_task")` está registrada. Um `App`
    paralelo não conheceria a tarefa e o worker recusaria o job da fila.
    """
    from src.app import tasks, worker

    assert worker.app is tasks.app
    assert "process_envio_task" in worker.app.tasks


def test_worker_entrypoint_dispara_a_fiacao_do_main() -> None:
    """SPECSFY: US-001 FR-001

    Importar `src.app.worker` precisa disparar o efeito colateral de
    `src.app.main` (resolve `APP_DATABASE_URL`, configura o engine). Sem isso,
    `process_envio_task` quebraria ao abrir `SessionLocal` no worker.
    """
    from src.app import db, worker  # noqa: F401 — import de `worker` é o gatilho

    # Não levanta "Banco de dados não configurado": o entrypoint já rodou.
    assert db.get_engine() is not None
