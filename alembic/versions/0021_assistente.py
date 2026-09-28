"""adiciona conversas e mensagens do assistente

Revision ID: 0021_assistente
Revises: 0020_pessoas
Create Date: 2026-09-24 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0021_assistente"
down_revision: str | Sequence[str] | None = "0020_pessoas"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversas_assistente",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=200), nullable=False),
        sa.Column("project_id", sa.String(length=200), nullable=False),
        sa.Column("pessoa_id", sa.String(length=36), nullable=False),
        sa.Column("titulo", sa.String(length=60), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pessoa_id"], ["pessoas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversas_assistente_pessoa_atualizada",
        "conversas_assistente",
        ["pessoa_id", "atualizada_em"],
    )
    op.create_table(
        "mensagens_assistente",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("conversa_id", sa.String(length=36), nullable=False),
        sa.Column("papel", sa.String(length=20), nullable=False),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("base_id", sa.String(length=36), nullable=True),
        sa.Column("fontes", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversa_id"], ["conversas_assistente.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mensagens_assistente_conversa_criada",
        "mensagens_assistente",
        ["conversa_id", "criada_em"],
    )


def downgrade() -> None:
    op.drop_index("ix_mensagens_assistente_conversa_criada", table_name="mensagens_assistente")
    op.drop_table("mensagens_assistente")
    op.drop_index("ix_conversas_assistente_pessoa_atualizada", table_name="conversas_assistente")
    op.drop_table("conversas_assistente")
