"""guarda o conteúdo processado de cada documento da coleção

Revision ID: 0031_conteudo_documento
Revises: 0033_avisos_conversao
Create Date: 2026-10-15 00:00:00.000000

Migração aditiva (SPEC-0031, PR-004): cria somente ``conteudos_documento``, sem
backfill e sem alterar tabelas existentes. ``downgrade`` remove só a tabela nova.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0031_conteudo_documento"
down_revision: str | Sequence[str] | None = "0033_avisos_conversao"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conteudos_documento",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("documento_id", sa.String(length=36), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("trechos", sa.JSON(), nullable=False),
        sa.Column("envio_id", sa.String(length=36), nullable=False),
        sa.Column("truncado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["documento_id"], ["documentos_colecao.id"]),
        sa.ForeignKeyConstraint(["envio_id"], ["envios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_conteudos_documento_documento", "conteudos_documento", ["documento_id"], unique=True
    )
    op.create_index("ix_conteudos_documento_envio_id", "conteudos_documento", ["envio_id"])


def downgrade() -> None:
    op.drop_index("ix_conteudos_documento_envio_id", table_name="conteudos_documento")
    op.drop_index("uq_conteudos_documento_documento", table_name="conteudos_documento")
    op.drop_table("conteudos_documento")
