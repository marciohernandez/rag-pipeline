"""add documentos to bases

Revision ID: f3b60ce4f7f4
Revises: 074d455d6f67
Create Date: 2026-09-05 15:12:38.069833

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3b60ce4f7f4"
down_revision: str | Sequence[str] | None = "074d455d6f67"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adiciona ``bases.documentos`` (contagem de arquivos recebidos na criação)."""
    op.add_column(
        "bases",
        sa.Column(
            "documentos",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    """Remove ``bases.documentos``.

    Compatível porque nenhuma consulta fora dos dois endpoints de leitura da
    SPEC-0013 depende dela (ver spec.md, seção 8).
    """
    op.drop_column("bases", "documentos")
