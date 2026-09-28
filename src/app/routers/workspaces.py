"""CRUD de Workspaces com isolamento por tenant/projeto (SPEC-0019)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.app import repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import Workspace

router = APIRouter(prefix="/api/v1", tags=["workspaces"])


class WorkspaceInput(BaseModel):
    nome: str


def _agora() -> datetime:
    return datetime.now(UTC)


def _nome_valido(nome: str) -> str:
    normalizado = nome.strip()
    if not normalizado:
        raise HTTPException(status_code=400, detail="Informe um nome para o Workspace.")
    return normalizado


def _autor(workspace: Workspace) -> dict | None:
    if workspace.autor is None:
        return None
    return {
        "id": workspace.autor.id,
        "nome": workspace.autor.nome,
        "desativada": workspace.autor.situacao != "ativa",
    }


def _serializar(workspace: Workspace) -> dict:
    return {"id": workspace.id, "nome": workspace.nome, "criado_por": _autor(workspace)}


@router.post("/workspaces", status_code=201)
def criar_workspace(
    payload: WorkspaceInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        workspace = Workspace(
            tenant_id=identity.tenant_id,
            project_id=identity.project_id,
            nome=_nome_valido(payload.nome),
            criado_por=identity.person_id,
        )
        session.add(workspace)
        session.commit()
        return _serializar(workspace)


@router.get("/workspaces")
def listar_workspaces(
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    with SessionLocal() as session:
        return [_serializar(item) for item in repo.list_workspaces_for_identity(session, identity)]


@router.get("/workspaces/{workspace_id}")
def obter_workspace(
    workspace_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    with SessionLocal() as session:
        return _serializar(repo.get_workspace_or_404(session, workspace_id, identity))


@router.patch("/workspaces/{workspace_id}")
def editar_workspace(
    workspace_id: str,
    payload: WorkspaceInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        workspace = repo.get_workspace_or_404(session, workspace_id, identity)
        workspace.nome = _nome_valido(payload.nome)
        session.commit()
        return _serializar(workspace)


@router.delete("/workspaces/{workspace_id}", status_code=204)
def apagar_workspace(
    workspace_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> None:
    require_write_role(identity)
    with SessionLocal() as session:
        workspace = repo.get_workspace_or_404(session, workspace_id, identity)
        if repo.has_active_bases_for_workspace(session, workspace.id):
            raise HTTPException(
                status_code=409,
                detail="Workspace possui Bases ativas. Apague ou mova as Bases antes de continuar.",
            )
        workspace.apagada_em = _agora()
        session.commit()
