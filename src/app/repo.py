"""Leituras com isolamento por tenant/projeto (SPEC-0012, FR-006/FR-007/AC-009)."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.auth import Identity
from src.app.models import Base, Execution

__all__ = [
    "get_base_or_404",
    "get_execution_or_404",
    "has_active_execution",
    "list_bases_for_identity",
    "list_executions_for_base",
]

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


def list_executions_for_base(session: Session, base_id: str) -> list[Execution]:
    """Execuções de uma base, da mais recente para a mais antiga (AC-005)."""
    stmt = (
        select(Execution).where(Execution.base_id == base_id).order_by(Execution.iniciado_em.desc())
    )
    return list(session.execute(stmt).scalars().all())


def list_bases_for_identity(
    session: Session, identity: Identity
) -> list[tuple[Base, Execution | None]]:
    """Bases ativas do tenant/projeto e a execução mais recente de cada uma.

    Ordena pela data da execução mais recente (desc); bases sem execução
    usam ``criado_em`` como chave de ordenação e desempate (AC-004).

    A leitura mais recente por base é resolvida em Python (uma consulta por
    base): o backend é um ambiente de demonstração com poucas bases por
    projeto; um ``JOIN`` com subconsulta de ``MAX(iniciado_em)`` é a
    otimização registrada para quando o volume justificar.
    """
    bases = (
        session.execute(
            select(Base).where(
                Base.tenant_id == identity.tenant_id,
                Base.project_id == identity.project_id,
                Base.apagada_em.is_(None),
            )
        )
        .scalars()
        .all()
    )
    pares: list[tuple[Base, Execution | None]] = []
    for base in bases:
        ultima = (
            session.execute(
                select(Execution)
                .where(Execution.base_id == base.id)
                .order_by(Execution.iniciado_em.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )
        pares.append((base, ultima))
    pares.sort(
        key=lambda par: par[1].iniciado_em if par[1] is not None else par[0].criado_em,
        reverse=True,
    )
    return pares
