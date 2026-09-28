"""Leituras com isolamento por tenant/projeto (SPEC-0012, FR-006/FR-007/AC-009)."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from src.app.auth import Identity
from src.app.models import (
    Base,
    ConversaAssistente,
    Execution,
    MensagemAssistente,
    Pessoa,
    VinculoPessoa,
    Workspace,
)

__all__ = [
    "count_active_owners_for_update",
    "get_base_or_404",
    "get_conversa_or_404",
    "get_execution_or_404",
    "get_pessoa_by_email",
    "get_pessoa_or_404",
    "get_workspace_or_404",
    "has_active_bases_for_workspace",
    "has_active_execution",
    "inserir_execucao_ativa",
    "list_bases_for_identity",
    "list_conversas_da_pessoa",
    "list_executions_for_base",
    "list_mensagens_recentes",
    "list_pessoas_for_identity",
    "list_workspaces_for_identity",
]

_SITUACOES_ATIVAS = ("pending", "running")
_CONSTRAINT_EXECUCAO_ATIVA = "uq_executions_base_active"
_SQLSTATE_VIOLACAO_UNICIDADE = "23505"


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


def get_workspace_or_404(
    session: Session, workspace_id: str, identity: Identity
) -> Workspace:
    workspace = session.get(Workspace, workspace_id)
    if (
        workspace is None
        or workspace.apagada_em is not None
        or workspace.tenant_id != identity.tenant_id
        or workspace.project_id != identity.project_id
    ):
        raise HTTPException(status_code=404, detail="Workspace não encontrado.")
    return workspace


def get_pessoa_by_email(session: Session, email_normalizado: str) -> Pessoa | None:
    return session.execute(
        select(Pessoa).where(func.lower(Pessoa.email) == email_normalizado)
    ).scalar_one_or_none()


def get_pessoa_or_404(
    session: Session, pessoa_id: str, identity: Identity, *, for_update: bool = False
) -> tuple[Pessoa, VinculoPessoa]:
    stmt = (
        select(Pessoa, VinculoPessoa)
        .join(VinculoPessoa, VinculoPessoa.pessoa_id == Pessoa.id)
        .where(
            Pessoa.id == pessoa_id,
            VinculoPessoa.tenant_id == identity.tenant_id,
            VinculoPessoa.project_id == identity.project_id,
        )
    )
    if for_update:
        stmt = stmt.with_for_update()
    linha = session.execute(stmt).one_or_none()
    if linha is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada.")
    return linha[0], linha[1]


def list_pessoas_for_identity(
    session: Session, identity: Identity
) -> list[tuple[Pessoa, VinculoPessoa]]:
    stmt = (
        select(Pessoa, VinculoPessoa)
        .join(VinculoPessoa, VinculoPessoa.pessoa_id == Pessoa.id)
        .where(
            VinculoPessoa.tenant_id == identity.tenant_id,
            VinculoPessoa.project_id == identity.project_id,
        )
        .order_by(Pessoa.nome, Pessoa.id)
    )
    return [(linha[0], linha[1]) for linha in session.execute(stmt).all()]


def count_active_owners_for_update(
    session: Session, tenant_id: str, project_id: str
) -> int:
    """Conta owners ativos depois de travar todas as linhas correspondentes."""
    stmt = (
        select(VinculoPessoa.id)
        .join(Pessoa, Pessoa.id == VinculoPessoa.pessoa_id)
        .where(
            VinculoPessoa.tenant_id == tenant_id,
            VinculoPessoa.project_id == project_id,
            VinculoPessoa.papel == "owner",
            Pessoa.situacao == "ativa",
        )
        .order_by(VinculoPessoa.id)
        .with_for_update()
    )
    return len(session.execute(stmt).scalars().all())


def list_workspaces_for_identity(session: Session, identity: Identity) -> list[Workspace]:
    stmt = (
        select(Workspace)
        .options(selectinload(Workspace.autor))
        .where(
            Workspace.tenant_id == identity.tenant_id,
            Workspace.project_id == identity.project_id,
            Workspace.apagada_em.is_(None),
        )
        .order_by(Workspace.criado_em.desc(), Workspace.id.desc())
    )
    return list(session.execute(stmt).scalars().all())


def has_active_bases_for_workspace(session: Session, workspace_id: str) -> bool:
    stmt = (
        select(Base.id)
        .where(Base.workspace_id == workspace_id, Base.apagada_em.is_(None))
        .limit(1)
    )
    return session.execute(stmt).first() is not None


def has_active_execution(session: Session, base_id: str) -> bool:
    stmt = select(Execution.id).where(
        Execution.base_id == base_id, Execution.situacao.in_(_SITUACOES_ATIVAS)
    )
    return session.execute(stmt).first() is not None


def inserir_execucao_ativa(
    session: Session,
    base_id: str,
    *,
    situacao: str = "pending",
    etapa: str = "agendado",
    criado_por: str | None = None,
) -> Execution:
    """Insere uma nova ``Execution`` ativa, convertendo a corrida perdida em 409.

    Usada por ``iniciar_execucao`` e ``repetir_execucao`` (SPEC-0015, FR-003):
    o índice único parcial ``uq_executions_base_active`` garante atomicamente
    que nunca existem duas execuções ``pending``/``running`` para a mesma
    base, mesmo sob concorrência real — o check otimista de
    ``has_active_execution`` sozinho não garantia isso.

    Só converte em conflito a violação exata dessa constraint; qualquer outro
    ``IntegrityError`` (ou a ausência inesperada da execução ativa na
    releitura) propaga sem modificação, para não mascarar um erro diferente.
    """
    execution = Execution(
        base_id=base_id, situacao=situacao, etapa=etapa, criado_por=criado_por
    )
    session.add(execution)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        sqlstate = getattr(error.orig, "sqlstate", None)
        constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        if sqlstate != _SQLSTATE_VIOLACAO_UNICIDADE or constraint != _CONSTRAINT_EXECUCAO_ATIVA:
            raise
        stmt = select(Execution).where(
            Execution.base_id == base_id, Execution.situacao.in_(_SITUACOES_ATIVAS)
        )
        ativa = session.execute(stmt).scalars().first()
        if ativa is None:
            raise
        raise HTTPException(
            status_code=409,
            detail={"execution_id": ativa.id, "situacao": ativa.situacao},
        ) from None
    return execution


def list_executions_for_base(session: Session, base_id: str) -> list[Execution]:
    """Execuções de uma base, da mais recente para a mais antiga (AC-005)."""
    stmt = (
        select(Execution)
        .options(selectinload(Execution.autor))
        .where(Execution.base_id == base_id)
        .order_by(Execution.iniciado_em.desc())
    )
    return list(session.execute(stmt).scalars().all())


def list_bases_for_identity(
    session: Session, identity: Identity, workspace_id: str | None = None
) -> list[tuple[Base, Execution | None]]:
    """Bases ativas do tenant/projeto e a execução mais recente de cada uma.

    Ordena pela data da execução mais recente (desc); bases sem execução
    usam ``criado_em`` como chave de ordenação e desempate (AC-004).

    A leitura mais recente por base é resolvida em Python (uma consulta por
    base): o backend é um ambiente de demonstração com poucas bases por
    projeto; um ``JOIN`` com subconsulta de ``MAX(iniciado_em)`` é a
    otimização registrada para quando o volume justificar.
    """
    filtros = [
        Base.tenant_id == identity.tenant_id,
        Base.project_id == identity.project_id,
        Base.apagada_em.is_(None),
    ]
    if workspace_id is not None:
        filtros.append(Base.workspace_id == workspace_id)
    bases = session.execute(
        select(Base).options(selectinload(Base.autor)).where(*filtros)
    ).scalars().all()
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


_LIMITE_HISTORICO = 50
_JANELA_DE_MENSAGENS = 20


def list_conversas_da_pessoa(
    session: Session, identity: Identity, limite: int = _LIMITE_HISTORICO
) -> list[ConversaAssistente]:
    """Conversas da própria pessoa, da mais recente para a mais antiga (SPEC-0021, FR-002)."""
    return list(
        session.scalars(
            select(ConversaAssistente)
            .where(
                ConversaAssistente.pessoa_id == identity.person_id,
                ConversaAssistente.tenant_id == identity.tenant_id,
                ConversaAssistente.project_id == identity.project_id,
            )
            .order_by(ConversaAssistente.atualizada_em.desc(), ConversaAssistente.criada_em.desc())
            .limit(limite)
        )
    )


def get_conversa_or_404(
    session: Session, conversa_id: str, identity: Identity
) -> ConversaAssistente:
    """Só a autora enxerga a conversa; qualquer outra pessoa recebe o mesmo 404."""
    conversa = session.get(ConversaAssistente, conversa_id)
    if (
        conversa is None
        or conversa.pessoa_id != identity.person_id
        or conversa.tenant_id != identity.tenant_id
        or conversa.project_id != identity.project_id
    ):
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    return conversa


def list_mensagens_recentes(
    session: Session, conversa_id: str, limite: int = _JANELA_DE_MENSAGENS
) -> list[MensagemAssistente]:
    """As ``limite`` mensagens mais recentes da conversa, em ordem cronológica."""
    recentes = session.scalars(
        select(MensagemAssistente)
        .where(MensagemAssistente.conversa_id == conversa_id)
        .order_by(MensagemAssistente.criada_em.desc())
        .limit(limite)
    )
    return list(reversed(list(recentes)))
