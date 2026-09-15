"""indice unico parcial: uma execucao ativa por base

Revision ID: 4d0fd0aa498e
Revises: f3b60ce4f7f4
Create Date: 2026-09-16 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d0fd0aa498e"
down_revision: str | Sequence[str] | None = "f3b60ce4f7f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adiciona índice único parcial que garante no máximo uma execução
    ``pending``/``running`` por base (SPEC-0015, FR-001).

    Corrige a corrida entre ``has_active_execution`` e o insert de
    ``Execution`` (SPEC-0012 seção 16): o check otimista da aplicação não
    garantia atomicidade sob concorrência real. O índice parcial faz o
    banco recusar a segunda inserção concorrente com uma violação de
    integridade (SQLSTATE 23505), convertida em HTTP 409 pela aplicação
    (``src/app/repo.py::inserir_execucao_ativa``).
    """
    op.create_index(
        "uq_executions_base_active",
        "executions",
        ["base_id"],
        unique=True,
        postgresql_where=sa.text("situacao IN ('pending', 'running')"),
    )


def downgrade() -> None:
    """Remove o índice único parcial ``uq_executions_base_active``."""
    op.drop_index("uq_executions_base_active", table_name="executions")
