"""Persistência PostgreSQL do backend de aplicação (SPEC-0012).

Este módulo nunca lê ``config.yaml`` nem variável de ambiente diretamente
(PR-002). O entrypoint (``src/app/main.py``, ou o fixture de teste) resolve a
URL de conexão e chama :func:`configure` uma única vez.
"""

from __future__ import annotations

from pathlib import Path

from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

__all__ = [
    "BancoNaoMigrado",
    "ORMBase",
    "SessionLocal",
    "configure",
    "get_engine",
    "verificar_banco_migrado",
]


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


class BancoNaoMigrado(RuntimeError):
    """O banco ainda não recebeu todas as migrations desta versão."""


def verificar_banco_migrado(engine: Engine | None = None) -> None:
    """Confere apenas a revisão do banco, sem executar migrations ou DDL."""
    scripts = ScriptDirectory(str(Path(__file__).resolve().parents[2] / "alembic"))
    with (engine if engine is not None else get_engine()).connect() as conexao:
        revisoes = MigrationContext.configure(conexao).get_current_heads()
    if set(revisoes) != set(scripts.get_heads()):
        raise BancoNaoMigrado("Banco não migrado. Execute alembic upgrade head antes de iniciar.")
