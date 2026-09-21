"""Modelos ORM da aplicação (SPEC-0012 e SPEC-0019)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from src.app.db import ORMBase

__all__ = ["Base", "Execution", "Query", "Workspace"]


def _novo_id() -> str:
    return str(uuid.uuid4())


def _agora() -> datetime:
    return datetime.now(UTC)


class Workspace(ORMBase):
    """Agrupador de bases dentro de um tenant e projeto."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    nome: Mapped[str] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    apagada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    bases: Mapped[list[Base]] = relationship(back_populates="workspace")


class Base(ORMBase):
    """Uma base Markdown de um projeto/tenant (upload ou preparada)."""

    __tablename__ = "bases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id"))
    nome: Mapped[str] = mapped_column(String(255))
    origem: Mapped[str] = mapped_column(String(20))
    collection_name: Mapped[str] = mapped_column(String(255))
    metadados_chunk: Mapped[list[dict[str, str]]] = mapped_column(
        JSON, default=list, server_default=text("'[]'::json")
    )
    documentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    apagada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    workspace: Mapped[Workspace] = relationship(back_populates="bases")


class Execution(ORMBase):
    """Uma execução do pipeline sobre uma base (situação, etapa, contagens).

    ``uq_executions_base_active`` garante no máximo uma execução
    ``pending``/``running`` por ``base_id`` (SPEC-0015, FR-001) — corrige a
    corrida entre ``has_active_execution`` e este insert, atomicamente, no
    banco.
    """

    __tablename__ = "executions"
    __table_args__ = (
        Index(
            "uq_executions_base_active",
            "base_id",
            unique=True,
            postgresql_where=text("situacao IN ('pending', 'running')"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    base_id: Mapped[str] = mapped_column(String(36), ForeignKey("bases.id"))
    situacao: Mapped[str] = mapped_column(String(20))
    etapa: Mapped[str] = mapped_column(String(50), default="")
    previstos: Mapped[int] = mapped_column(Integer, default=0)
    inseridos: Mapped[int] = mapped_column(Integer, default=0)
    mantidos: Mapped[int] = mapped_column(Integer, default=0)
    removidos: Mapped[int] = mapped_column(Integer, default=0)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    iniciado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    concluido_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )


class Query(ORMBase):
    """Uma consulta de validação realizada sobre uma base indexada."""

    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    base_id: Mapped[str] = mapped_column(String(36), ForeignKey("bases.id"))
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    pergunta: Mapped[str] = mapped_column(Text)
    resultado: Mapped[str] = mapped_column(Text, default="")
    chunks_fontes: Mapped[Any] = mapped_column(JSON, default=list)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
