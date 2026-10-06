"""Endpoints de execução do pipeline (SPEC-0012, US-001/US-002)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.app import publicacao, repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import Execution

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
        "criado_por": (
            {
                "id": execution.autor.id,
                "nome": execution.autor.nome,
                "desativada": execution.autor.situacao != "ativa",
            }
            if execution.autor is not None
            else None
        ),
    }


def _exigir_conexoes_ativas(session, identity: Identity, base) -> None:
    """Uma Base com conexões só executa enquanto as duas estiverem ativas (409)."""
    if base.conexao_embeddings_id and base.conexao_vector_store_id:
        publicacao.resolver_conexoes(
            session, identity, base.conexao_embeddings_id, base.conexao_vector_store_id
        )


def _agendar(
    execution_id: str,
    base_id: str,
    identity: Identity,
    collection_name: str,
    conexoes_da_base: tuple[str | None, str | None],
) -> None:
    publicacao.agendar_execucao(
        execution_id,
        base_id,
        identity,
        collection_name,
        conexao_embeddings_id=conexoes_da_base[0],
        conexao_vector_store_id=conexoes_da_base[1],
    )


def _detail_execucao_ativa(session, base_id: str) -> dict:
    ativa = next(
        (
            execucao
            for execucao in repo.list_executions_for_base(session, base_id)
            if execucao.situacao in ("pending", "running")
        ),
        None,
    )
    return {
        "execution_id": ativa.id if ativa else None,
        "situacao": ativa.situacao if ativa else None,
    }


@router.post("/bases/{base_id}/executions", status_code=202)
def iniciar_execucao(base_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        base = repo.get_base_or_404(session, base_id, identity)
        _exigir_conexoes_ativas(session, identity, base)
        if repo.has_active_execution(session, base.id):
            raise HTTPException(status_code=409, detail=_detail_execucao_ativa(session, base.id))
        execution = repo.inserir_execucao_ativa(session, base.id, criado_por=identity.person_id)
        execution_id = execution.id
        collection_name = base.collection_name
        conexoes_da_base = (base.conexao_embeddings_id, base.conexao_vector_store_id)

    _agendar(execution_id, base_id, identity, collection_name, conexoes_da_base)
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
                status_code=409, detail=_detail_execucao_ativa(session, execution.base_id)
            )
        base = repo.get_base_or_404(session, execution.base_id, identity)
        _exigir_conexoes_ativas(session, identity, base)
        nova = repo.inserir_execucao_ativa(
            session, execution.base_id, criado_por=identity.person_id
        )
        nova_id = nova.id
        base_id = execution.base_id
        collection_name = base.collection_name
        conexoes_da_base = (base.conexao_embeddings_id, base.conexao_vector_store_id)

    _agendar(nova_id, base_id, identity, collection_name, conexoes_da_base)
    return {"execution_id": nova_id, "situacao": "pending"}
