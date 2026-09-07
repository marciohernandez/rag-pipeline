"""Tarefa assíncrona de processamento de uma base (SPEC-0012, seção 8).

Usa Procrastinate sobre o mesmo PostgreSQL da aplicação. O app nasce com
``InMemoryConnector`` (nenhuma fila real antes de configurado); o entrypoint
(``src/app/main.py``) chama ``configure_connector`` com um
``procrastinate.PsycopgConnector`` real assim que a aplicação sobe — inclusive
em teste, contra o Postgres de teste isolado, para que um worker fora do
processo consuma a mesma fila que a API agenda.

``configure_connector`` precisa reatribuir **os dois** ponteiros de connector
do ``App``: ``app.connector`` e ``app.job_manager.connector``. ``task.defer()``
roteia pelo ``job_manager``; trocar só ``app.connector`` faz todo agendamento
cair no ``InMemoryConnector`` de placeholder — o job nunca chega ao Postgres e
nenhum worker externo o consome (SPEC-0012, Fase 9, T044–T048).
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from typing import Any

import procrastinate
from procrastinate import testing as procrastinate_testing
from procrastinate.connector import BaseConnector

from src.app.storage import Storage

app = procrastinate.App(connector=procrastinate_testing.InMemoryConnector())


def configure_connector(connector: BaseConnector) -> None:
    """Troca o conector do app Procrastinate e o abre (chamado uma vez no entrypoint).

    Reatribui ``app.connector`` **e** ``app.job_manager.connector`` — este último
    é o que ``task.defer()`` usa. É o que o próprio ``App.replace_connector`` do
    procrastinate faz; aqui a troca é permanente, não escopada a um ``with``.
    """
    app.connector = connector
    app.job_manager.connector = connector
    app.open()


def _agora() -> datetime:
    return datetime.now(UTC)


def scope_project_id(tenant_id: str, project_id: str, base_id: str) -> str:
    """Compõe o identificador de escopo lógico isolado por base e por tenant.

    ``LogicalScope`` (src/pipeline/) só distingue project_id/tenant_id; sem
    incorporar ``base_id`` aqui, todas as bases do mesmo tenant/projeto
    compartilhariam o mesmo escopo no vector store — o DELETE de uma base
    removeria (ou deixaria de remover) pontos de outra, e uma consulta
    misturaria conteúdo de bases distintas (achado registrado na reabertura
    do Ato II desta spec, T029–T031).

    ``tenant_id`` também entra na string, e não é mais passado como
    ``LogicalScope.tenant_id`` separado (ver ``query_base``/``delete_scope``
    em ``src/app/routers/``): o caminho de escrita (``run_pipeline`` →
    ``chunk_documents`` → ``assign_document_identity``, em ``src/pipeline/``)
    nunca grava ``tenant_id`` no metadata do chunk — só ``project_id``. Se o
    caminho de leitura/exclusão continuasse passando
    ``tenant_id=identity.tenant_id`` explícito para ``LogicalScope``, o
    escopo da escrita (sempre ``tenant_id=None``) nunca bateria com o da
    leitura/exclusão, e toda consulta real voltaria vazia e todo DELETE
    deixaria os pontos reais órfãos. Achado durante o `/code-review` desta
    reabertura (T031 original só isolava por base, não fechava esse
    descompasso). Corrigir isso dentro de `src/pipeline/` está fora de
    escopo desta spec (seção 3); dobrar o tenant na mesma string de
    `project_id`, já sob controle total de `src/app/` nos dois lados, evita
    tocar `src/pipeline/`.
    """
    return f"{tenant_id}::{project_id}::{base_id}"


def build_pipeline_config(
    *,
    base_project_id: str,
    embedding: dict[str, Any],
    vector_store: dict[str, Any],
    input_dir: str,
) -> dict[str, Any]:
    """Monta a configuração injetada na fachada para uma base específica."""
    return {
        "projeto": {"nome": base_project_id},
        "caminhos": {
            "input_dir": input_dir,
            "chunks_file": f"{input_dir}/chunks.json",
        },
        "embedding": dict(embedding),
        "vector_store": dict(vector_store),
    }


@app.task(name="process_base_task")
def process_base_task(
    execution_id: str,
    *,
    base_id: str,
    tenant_id: str,
    project_id: str,
    embedding: dict[str, Any],
    vector_store: dict[str, Any],
) -> None:
    """Processa uma execução: carrega, faz chunk, gera embeddings e sincroniza."""
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira
    from src.app.db import SessionLocal
    from src.app.models import Execution

    with SessionLocal() as session:
        execution = session.get(Execution, execution_id)
        if execution is None:
            return
        execution.situacao = "running"
        execution.etapa = "carregando"
        session.commit()

        try:
            with tempfile.TemporaryDirectory(prefix=f"base-{base_id}-") as pasta:
                from src.app.storage import get_storage

                storage: Storage = get_storage()
                storage.materialize(base_id, pasta)
                config = build_pipeline_config(
                    base_project_id=scope_project_id(tenant_id, project_id, base_id),
                    embedding=embedding,
                    vector_store=vector_store,
                    input_dir=pasta,
                )
                execution.etapa = "chunking"
                session.commit()
                resultado = service.run_pipeline(config)
                execution.etapa = "indexando"
                execution.previstos = len(resultado.chunks)
                session.commit()
                contagens = resultado.sync_counts
                if contagens is None:
                    contagens = service.sync_vector_store(config, resultado.chunks)
                execution.inseridos = contagens.inseridos
                execution.mantidos = contagens.mantidos
                execution.removidos = contagens.removidos
                execution.situacao = "succeeded"
                execution.etapa = "concluido"
        except Exception:  # noqa: BLE001 — erro seguro, sem detalhe interno do provedor
            execution.situacao = "failed"
            execution.erro = "Falha ao processar a base; ver logs do worker para detalhes."
            execution.etapa = execution.etapa or "falha"
        finally:
            execution.concluido_em = _agora()
            session.commit()
