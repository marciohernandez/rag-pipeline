"""Fixtures do backend de aplicação (SPEC-0012) para a suíte pytest.

Configura a URL do PostgreSQL de teste antes de qualquer import de
``src.app.main`` e limpa as tabelas entre os testes que efetivamente usam o
backend de aplicação, sem afetar a suíte do pipeline (``src/pipeline``), que
não importa ``src.app``.
"""

from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault(
    "APP_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test",
)


@pytest.fixture(autouse=True)
def _limpar_tabelas_do_backend_de_aplicacao():
    yield
    if "src.app.main" not in sys.modules:
        return
    from src.app import db
    from src.app.db import ORMBase

    with db.SessionLocal() as session:
        for table in reversed(ORMBase.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
