"""Rotas de login, identidade, senha e encerramento da sessão."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.app import accounts
from src.app.auth import Identity, get_identity_pendente
from src.app.db import SessionLocal

router = APIRouter(prefix="/api/v1/auth", tags=["autenticacao"])


class LoginInput(BaseModel):
    email: str
    senha: str


class SenhaInput(BaseModel):
    nova_senha: str
    senha_atual: str | None = None


def _http(error: accounts.AccountError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


def _identidade(identity: Identity) -> dict:
    return {
        "id": identity.person_id,
        "nome": identity.nome,
        "email": identity.email,
        "papel": identity.role,
        "tenant_id": identity.tenant_id,
        "project_id": identity.project_id,
        "precisa_trocar_senha": identity.precisa_trocar_senha,
    }


@router.post("/login")
def login(payload: LoginInput) -> dict:
    with SessionLocal() as session:
        try:
            token, sessao, pessoa, vinculo = accounts.entrar(session, payload.email, payload.senha)
        except accounts.AccountError as error:
            raise _http(error) from error
        return {
            "token": token,
            "expira_em": sessao.expira_em.isoformat(),
            "pessoa": accounts.serializar_pessoa(session, pessoa, vinculo),
        }


@router.get("/me")
def me(identity: Identity = Depends(get_identity_pendente)) -> dict:  # noqa: B008
    return _identidade(identity)


@router.post("/logout", status_code=204)
def logout(identity: Identity = Depends(get_identity_pendente)) -> None:  # noqa: B008
    with SessionLocal() as session:
        accounts.sair(session, identity)


@router.post("/senha", status_code=204)
def alterar_senha(
    payload: SenhaInput,
    identity: Identity = Depends(get_identity_pendente),  # noqa: B008
) -> None:
    with SessionLocal() as session:
        try:
            accounts.trocar_senha(
                session,
                identity,
                nova_senha=payload.nova_senha,
                senha_atual=payload.senha_atual,
            )
        except accounts.AccountError as error:
            raise _http(error) from error
