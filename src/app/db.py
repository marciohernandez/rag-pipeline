"""Persistência PostgreSQL do backend de aplicação (SPEC-0012).

Este módulo nunca lê ``config.yaml`` nem variável de ambiente diretamente
(PR-002). O entrypoint (``src/app/main.py``, ou o fixture de teste) resolve a
URL de conexão e chama :func:`configure` uma única vez.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

__all__ = ["ORMBase", "SessionLocal", "configure", "create_tables", "get_engine"]


class ORMBase(DeclarativeBase):
    """Base declarativa dos modelos de ``src/app``."""


SessionLocal: sessionmaker[Session] = sessionmaker(expire_on_commit=False)
_engine: Engine | None = None


def configure(database_url: str) -> Engine:
    """Cria o engine PostgreSQL e vincula ``SessionLocal`` a ele."""
    global _engine
    _engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal.configure(bind=_engine)
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError(
            "Banco de dados não configurado. Chame src.app.db.configure(url) no entrypoint."
        )
    return _engine


def create_tables() -> None:
    """Cria as tabelas declaradas em ``src/app/models.py`` se não existirem."""
    from src.app import models  # noqa: F401 — garante que os modelos sejam registrados

    ORMBase.metadata.create_all(get_engine())
