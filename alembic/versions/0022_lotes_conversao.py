"""adiciona lotes e documentos de conversão

Revision ID: 0022_lotes_conversao
Revises: 0021_assistente
Create Date: 2026-09-28 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0022_lotes_conversao"
down_revision: str | Sequence[str] | None = "0021_assistente"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lotes_conversao",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=200), nullable=False),
        sa.Column("project_id", sa.String(length=200), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("criado_por", sa.String(length=36), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("situacao", sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["criado_por"], ["pessoas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_lotes_conversao_workspace_criado",
        "lotes_conversao",
        ["workspace_id", "criado_em"],
    )
    op.create_table(
        "documentos_conversao",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("lote_id", sa.String(length=36), nullable=False),
        sa.Column("nome_arquivo", sa.String(length=255), nullable=False),
        sa.Column("formato", sa.String(length=20), nullable=False),
        sa.Column("tamanho_bytes", sa.Integer(), nullable=False),
        sa.Column("situacao", sa.String(length=20), nullable=False),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("apagado_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["lote_id"], ["lotes_conversao.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_documentos_conversao_lote",
        "documentos_conversao",
        ["lote_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_documentos_conversao_lote", table_name="documentos_conversao")
    op.drop_table("documentos_conversao")
    op.drop_index("ix_lotes_conversao_workspace_criado", table_name="lotes_conversao")
    op.drop_table("lotes_conversao")
