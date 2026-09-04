"""Leituras com isolamento por tenant/projeto (SPEC-0012, FR-006/FR-007/AC-009)."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.auth import Identity
from src.app.models import Base, Execution

__all__ = ["get_base_or_404", "get_execution_or_404", "has_active_execution"]

_SITUACOES_ATIVAS = ("pending", "running")


def get_base_or_404(session: Session, base_id: str, identity: Identity) -> Base:
    base = session.get(Base, base_id)
    if (
        base is None
        or base.apagada_em is not None
        or base.tenant_id != identity.tenant_id
        or base.project_id != identity.project_id
    ):
        raise HTTPException(status_code=404, detail="Base não encontrada.")
    return base


def get_execution_or_404(session: Session, execution_id: str, identity: Identity) -> Execution:
    execution = session.get(Execution, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execução não encontrada.")
    base = session.get(Base, execution.base_id)
    if (
        base is None
        or base.tenant_id != identity.tenant_id
        or base.project_id != identity.project_id
    ):
        raise HTTPException(status_code=404, detail="Execução não encontrada.")
    return execution


def has_active_execution(session: Session, base_id: str) -> bool:
    stmt = select(Execution.id).where(
        Execution.base_id == base_id, Execution.situacao.in_(_SITUACOES_ATIVAS)
    )
    return session.execute(stmt).first() is not None
