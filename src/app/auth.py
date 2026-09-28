"""Dependências FastAPI para sessões revogáveis de pessoas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Header, HTTPException
from sqlalchemy import select

from src.app.db import SessionLocal
from src.app.models import Pessoa, Sessao, VinculoPessoa
from src.app.security import resumir_token

__all__ = ["Identity", "get_identity", "get_identity_pendente", "require_write_role"]

PAPEIS_DE_ESCRITA = frozenset({"owner", "admin"})


@dataclass(frozen=True)
class Identity:
    person_id: str
    nome: str
    email: str
    tenant_id: str
    project_id: str
    role: str
    precisa_trocar_senha: bool
    session_id: str


def _token_do_cabecalho(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sessão ausente.")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Sessão ausente.")
    return token


def get_identity_pendente(authorization: str | None = Header(default=None)) -> Identity:
    """Resolve a identidade atual, inclusive quando a senha ainda está pendente."""
    token = _token_do_cabecalho(authorization)
    with SessionLocal() as session:
        linha = session.execute(
            select(Sessao, Pessoa, VinculoPessoa)
            .join(Pessoa, Pessoa.id == Sessao.pessoa_id)
            .join(VinculoPessoa, VinculoPessoa.pessoa_id == Pessoa.id)
            .where(Sessao.token_hash == resumir_token(token))
        ).one_or_none()
        if linha is None:
            raise HTTPException(status_code=401, detail="Sessão inválida ou encerrada.")
        sessao, pessoa, vinculo = linha
        if sessao.expira_em <= datetime.now(UTC):
            session.delete(sessao)
            session.commit()
            raise HTTPException(status_code=401, detail="Sessão expirada.")
        if pessoa.situacao != "ativa":
            session.delete(sessao)
            session.commit()
            raise HTTPException(status_code=401, detail="Sessão inválida ou encerrada.")
        return Identity(
            person_id=pessoa.id,
            nome=pessoa.nome,
            email=pessoa.email,
            tenant_id=vinculo.tenant_id,
            project_id=vinculo.project_id,
            role=vinculo.papel,
            precisa_trocar_senha=pessoa.precisa_trocar_senha,
            session_id=sessao.id,
        )


def get_identity(authorization: str | None = Header(default=None)) -> Identity:
    identity = get_identity_pendente(authorization)
    if identity.precisa_trocar_senha:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "senha_pendente",
                "message": "Defina uma nova senha antes de continuar.",
            },
        )
    return identity


def require_write_role(identity: Identity) -> None:
    if identity.role not in PAPEIS_DE_ESCRITA:
        raise HTTPException(status_code=403, detail="Permissão insuficiente para esta operação.")
