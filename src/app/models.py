"""Modelos ORM de ``bases``, ``executions`` e ``queries`` (SPEC-0012, seção 9)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.app.db import ORMBase

__all__ = ["Base", "Execution", "Query"]


def _novo_id() -> str:
    return str(uuid.uuid4())


def _agora() -> datetime:
    return datetime.now(UTC)


class Base(ORMBase):
    """Uma base Markdown de um projeto/tenant (upload ou preparada)."""

    __tablename__ = "bases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_novo_id)
    tenant_id: Mapped[str] = mapped_column(String(200))
    project_id: Mapped[str] = mapped_column(String(200))
    nome: Mapped[str] = mapped_column(String(255))
    origem: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)
    apagada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )


class Execution(ORMBase):
    """Uma execução do pipeline sobre uma base (situação, etapa, contagens)."""

    __tablename__ = "executions"

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
