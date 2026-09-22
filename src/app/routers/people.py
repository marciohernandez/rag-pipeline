"""CRUD sem exclusão física das pessoas do tenant e projeto atuais."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.app import accounts, repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal

router = APIRouter(prefix="/api/v1/pessoas", tags=["pessoas"])


class PessoaCreate(BaseModel):
    nome: str
    email: str
    papel: str
    senha_inicial: str


class PessoaUpdate(BaseModel):
    nome: str | None = None
    email: str | None = None
    papel: str | None = None


class RedefinirSenhaInput(BaseModel):
    senha_temporaria: str


def _http(error: accounts.AccountError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


@router.get("")
def listar(identity: Identity = Depends(get_identity)) -> list[dict]:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        return [
            accounts.serializar_pessoa(session, pessoa, vinculo)
            for pessoa, vinculo in repo.list_pessoas_for_identity(session, identity)
        ]


@router.post("", status_code=201)
def criar(
    payload: PessoaCreate, identity: Identity = Depends(get_identity)  # noqa: B008
) -> dict:
    with SessionLocal() as session:
        try:
            pessoa, vinculo = accounts.criar_pessoa(
                session,
                identity,
                nome=payload.nome,
                email=payload.email,
                papel=payload.papel,
                senha_inicial=payload.senha_inicial,
            )
        except accounts.AccountError as error:
            raise _http(error) from error
        return accounts.serializar_pessoa(session, pessoa, vinculo)


@router.get("/{pessoa_id}")
def detalhe(pessoa_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        pessoa, vinculo = repo.get_pessoa_or_404(session, pessoa_id, identity)
        return accounts.serializar_pessoa(session, pessoa, vinculo)


@router.patch("/{pessoa_id}")
def editar(
    pessoa_id: str,
    payload: PessoaUpdate,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    with SessionLocal() as session:
        try:
            pessoa, vinculo = accounts.atualizar_pessoa(
                session,
                identity,
                pessoa_id,
                nome=payload.nome,
                email=payload.email,
                papel=payload.papel,
            )
        except accounts.AccountError as error:
            raise _http(error) from error
        return accounts.serializar_pessoa(session, pessoa, vinculo)


@router.post("/{pessoa_id}/desativar", status_code=204)
def desativar(pessoa_id: str, identity: Identity = Depends(get_identity)) -> None:  # noqa: B008
    with SessionLocal() as session:
        try:
            accounts.desativar_pessoa(session, identity, pessoa_id)
        except accounts.AccountError as error:
            raise _http(error) from error


@router.post("/{pessoa_id}/reativar", status_code=204)
def reativar(pessoa_id: str, identity: Identity = Depends(get_identity)) -> None:  # noqa: B008
    with SessionLocal() as session:
        try:
            accounts.reativar_pessoa(session, identity, pessoa_id)
        except accounts.AccountError as error:
            raise _http(error) from error


@router.post("/{pessoa_id}/redefinir-senha", status_code=204)
def redefinir_senha(
    pessoa_id: str,
    payload: RedefinirSenhaInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> None:
    with SessionLocal() as session:
        try:
            accounts.redefinir_senha(session, identity, pessoa_id, payload.senha_temporaria)
        except accounts.AccountError as error:
            raise _http(error) from error
