"""Prepara a fila Procrastinate junto do schema da aplicação."""

from procrastinate.schema import SchemaManager
from sqlalchemy import text

from alembic import op

revision = "0042_schema_da_fila"
down_revision = "0040_grupos_e_tabelas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conexao = op.get_bind()
    if conexao.execute(text("SELECT to_regclass('procrastinate_jobs')")).scalar() is None:
        conexao.execute(text(SchemaManager.get_schema()))


def downgrade() -> None:
    # Preserva o schema da fila para não apagar tarefas pendentes.
    pass
