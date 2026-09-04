"""Tarefa assíncrona de processamento de uma base (SPEC-0012, seção 8).

Usa Procrastinate sobre o mesmo PostgreSQL da aplicação. O app é criado com um
conector substituível: produção usa ``PsycopgConnector``; testes usam
``procrastinate.testing.InMemoryConnector`` (nenhum worker real precisa rodar
para provar FR-001 — a asserção é que a tarefa foi agendada sem bloquear).
"""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from typing import Any

import procrastinate
from procrastinate import testing as procrastinate_testing

from src.app.storage import Storage

app = procrastinate.App(connector=procrastinate_testing.InMemoryConnector())


def _agora() -> datetime:
    return datetime.now(UTC)


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
                    base_project_id=project_id,
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
