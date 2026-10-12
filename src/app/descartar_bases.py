"""Descarte operacional das Bases antigas (SPEC-0030, FR-014).

``python -m src.app.descartar_bases`` percorre as Bases ativas e aplica a rotina de
exclusão que existia na API: apaga os arquivos guardados, os pontos do escopo da
Base no Qdrant, as execuções e as consultas, e marca a Base como apagada. Nenhuma
tabela é apagada ou truncada (PR-002); uma Base que falha é relatada e as demais
seguem.
"""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select

from src.app import conexoes
from src.app.db import SessionLocal
from src.app.models import Base, Execution, Query
from src.app.settings import get_settings
from src.app.storage import get_storage
from src.app.tasks import configuracao_vector_store_da_base, scope_project_id

__all__ = ["descartar_bases", "main"]

logger = logging.getLogger(__name__)


def _descartar(base_id: str) -> None:
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira

    with SessionLocal() as session:
        base = session.get(Base, base_id)
        if base is None or base.apagada_em is not None:
            return
        tenant_id, project_id = base.tenant_id, base.project_id
        # O destino é resolvido antes de qualquer remoção: conexão desativada bloqueia
        # aqui, sem apagar arquivos nem tocar o Postgres.
        vector_store = configuracao_vector_store_da_base(session, base)
    get_storage().delete_base(base_id)
    config = {
        "projeto": {"nome": scope_project_id(tenant_id, project_id, base_id)},
        "embedding": dict(get_settings().embedding),
        "vector_store": vector_store,
    }
    service.delete_scope(config)
    with SessionLocal() as session:
        base = session.get(Base, base_id)
        session.execute(delete(Execution).where(Execution.base_id == base_id))
        session.execute(delete(Query).where(Query.base_id == base_id))
        base.apagada_em = datetime.now(UTC)
        base.nome = ""
        session.commit()


def descartar_bases() -> dict[str, Any]:
    """Descarta cada Base ativa e devolve ``{"descartadas": n, "falhas": [ids]}``."""
    with SessionLocal() as session:
        ids = list(
            session.execute(select(Base.id).where(Base.apagada_em.is_(None)).order_by(Base.id))
            .scalars()
            .all()
        )
    descartadas = 0
    falhas: list[str] = []
    for base_id in ids:
        try:
            _descartar(base_id)
            descartadas += 1
        except conexoes.ErroDeConexao as erro:
            logger.error("Base %s não descartada: %s", base_id, erro.detalhe)
            falhas.append(base_id)
        except Exception as erro:  # noqa: BLE001 — só o tipo vai ao log; o detalhe pode ter chave
            logger.error("Base %s não descartada: %s", base_id, type(erro).__name__)
            falhas.append(base_id)
    return {"descartadas": descartadas, "falhas": falhas}


def main() -> int:
    import src.app.main  # noqa: F401 — efeito colateral: configura banco, storage e settings

    resultado = descartar_bases()
    print(f"Bases descartadas: {resultado['descartadas']}")
    for base_id in resultado["falhas"]:
        print(f"Falhou (repita o comando): {base_id}")
    return 1 if resultado["falhas"] else 0


if __name__ == "__main__":
    sys.exit(main())
