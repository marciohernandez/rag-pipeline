"""Avisos de revisão dos documentos convertidos (SPEC-0033)."""

import sqlalchemy as sa

from alembic import op

revision = "0033_avisos_conversao"
down_revision = "0022_lotes_conversao"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documentos_conversao",
        sa.Column("avisos", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    op.drop_column("documentos_conversao", "avisos")
