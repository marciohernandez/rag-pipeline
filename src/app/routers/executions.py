"""Endpoints de execução do pipeline (SPEC-0012, US-001/US-002)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.app import repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import Execution
from src.app.settings import get_settings

router = APIRouter(prefix="/api/v1", tags=["execucoes"])


def _serializar(execution: Execution) -> dict:
    return {
        "execution_id": execution.id,
        "base_id": execution.base_id,
        "situacao": execution.situacao,
        "etapa": execution.etapa,
        "previstos": execution.previstos,
        "inseridos": execution.inseridos,
        "mantidos": execution.mantidos,
        "removidos": execution.removidos,
        "erro": execution.erro,
    }


def _agendar(execution_id: str, base_id: str, identity: Identity) -> None:
    from src.app.tasks import process_base_task

    settings = get_settings()
    process_base_task.defer(
        execution_id=execution_id,
        base_id=base_id,
        tenant_id=identity.tenant_id,
        project_id=identity.project_id,
        embedding=settings.embedding,
        vector_store=settings.vector_store,
    )


@router.post("/bases/{base_id}/executions", status_code=202)
def iniciar_execucao(base_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        base = repo.get_base_or_404(session, base_id, identity)
        if repo.has_active_execution(session, base.id):
            raise HTTPException(
                status_code=409, detail="Já existe uma execução ativa para esta base."
            )
        execution = Execution(base_id=base.id, situacao="pending", etapa="agendado")
        session.add(execution)
        session.commit()
        execution_id = execution.id

    _agendar(execution_id, base_id, identity)
    return {"execution_id": execution_id, "situacao": "pending"}


@router.get("/executions/{execution_id}")
def obter_execucao(execution_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    with SessionLocal() as session:
        execution = repo.get_execution_or_404(session, execution_id, identity)
        return _serializar(execution)


@router.post("/executions/{execution_id}/retry", status_code=202)
def repetir_execucao(execution_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        execution = repo.get_execution_or_404(session, execution_id, identity)
        if execution.situacao != "failed":
            raise HTTPException(
                status_code=409, detail="Só é possível repetir uma execução que falhou."
            )
        if repo.has_active_execution(session, execution.base_id):
            raise HTTPException(
                status_code=409, detail="Já existe uma execução ativa para esta base."
            )
        nova = Execution(base_id=execution.base_id, situacao="pending", etapa="agendado")
        session.add(nova)
        session.commit()
        nova_id = nova.id
        base_id = execution.base_id

    _agendar(nova_id, base_id, identity)
    return {"execution_id": nova_id, "situacao": "pending"}
