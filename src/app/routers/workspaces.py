"""CRUD de Workspaces com isolamento por tenant/projeto (SPEC-0019)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.app import conexoes, limpeza, repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import Conexao, DominioWorkspace, Pessoa, Workspace

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
        if repo.has_active_colecoes_for_workspace(session, workspace.id):
            raise HTTPException(
                status_code=409,
                detail="Workspace possui coleções ativas. Apague as coleções antes de continuar.",
            )
        if repo.has_active_bases_for_workspace(session, workspace.id):
            raise HTTPException(
                status_code=409,
                detail="Workspace possui Bases ativas. Apague ou mova as Bases antes de continuar.",
            )
        workspace.apagada_em = _agora()
        session.commit()


class DominioInput(BaseModel):
    texto: str


class AnaliseIaInput(BaseModel):
    ia_externa_permitida: bool | None = None
    conexao_ia_id: str | None = None


def _dominio(session, versao: DominioWorkspace) -> dict:
    pessoa = session.get(Pessoa, versao.aprovado_por) if versao.aprovado_por else None
    return {
        "versao": versao.versao,
        "texto": versao.texto,
        "vigente": versao.vigente,
        "aprovado_por": versao.aprovado_por,
        "aprovado_por_nome": pessoa.nome if pessoa else None,
        "criado_em": versao.criado_em.isoformat(),
    }


@router.get("/workspaces/{workspace_id}/dominio")
def obter_dominio(workspace_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    with SessionLocal() as session:
        repo.get_workspace_or_404(session, workspace_id, identity)
        vigente = limpeza.dominio_vigente(session, workspace_id)
        if vigente is None:
            return {"versao": None, "texto": "", "vigente": False, "aprovado_por": None}
        return _dominio(session, vigente)


@router.get("/workspaces/{workspace_id}/dominio/versoes")
def listar_versoes_do_dominio(
    workspace_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    require_write_role(identity)
    with SessionLocal() as session:
        repo.get_workspace_or_404(session, workspace_id, identity)
        versoes = (
            session.query(DominioWorkspace)
            .filter_by(workspace_id=workspace_id)
            .order_by(DominioWorkspace.versao.desc())
            .all()
        )
        return [_dominio(session, v) for v in versoes]


@router.put("/workspaces/{workspace_id}/dominio")
def salvar_dominio(
    workspace_id: str,
    payload: DominioInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        repo.get_workspace_or_404(session, workspace_id, identity)
        try:
            nova = limpeza.salvar_dominio(session, workspace_id, payload.texto, identity.person_id)
        except ValueError as erro:
            raise HTTPException(status_code=422, detail=str(erro)) from None
        session.commit()
        return _dominio(session, nova)


def _analise_ia(workspace: Workspace) -> dict:
    return {
        "ia_externa_permitida": bool(workspace.ia_externa_permitida),
        "conexao_ia_id": workspace.conexao_ia_id,
    }


@router.get("/workspaces/{workspace_id}/analise-ia")
def obter_analise_ia(workspace_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        return _analise_ia(repo.get_workspace_or_404(session, workspace_id, identity))


@router.patch("/workspaces/{workspace_id}/analise-ia")
def alterar_analise_ia(
    workspace_id: str,
    payload: AnaliseIaInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        workspace = repo.get_workspace_or_404(session, workspace_id, identity)
        if "conexao_ia_id" in payload.model_fields_set:
            if payload.conexao_ia_id:
                conexao = session.get(Conexao, payload.conexao_ia_id)
                if (
                    conexao is None
                    or conexao.tenant_id != identity.tenant_id
                    or conexao.project_id != identity.project_id
                    or conexao.situacao != "ativa"
                    or conexao.tipo != conexoes.TIPO_IA
                ):
                    raise HTTPException(
                        status_code=422,
                        detail="Escolha uma conexão ativa do tipo IA para análise de documentos.",
                    )
            workspace.conexao_ia_id = payload.conexao_ia_id or None
        if payload.ia_externa_permitida is not None:
            workspace.ia_externa_permitida = payload.ia_externa_permitida
        session.commit()
        return _analise_ia(workspace)
