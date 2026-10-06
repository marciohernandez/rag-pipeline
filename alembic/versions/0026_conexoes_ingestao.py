"""adiciona conexões de ingestão, seus eventos e os vínculos das bases

Revision ID: 0026_conexoes_ingestao
Revises: 0021_assistente
Create Date: 2026-10-06 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0026_conexoes_ingestao"
down_revision: str | Sequence[str] | None = "0021_assistente"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conexoes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=200), nullable=False),
        sa.Column("project_id", sa.String(length=200), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("situacao", sa.String(length=20), nullable=False),
        sa.Column("configuracao", sa.JSON(), server_default=sa.text("'{}'::json"), nullable=False),
        sa.Column("segredo_cifrado", sa.Text(), nullable=True),
        sa.Column("criado_por", sa.String(length=36), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["criado_por"], ["pessoas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conexoes_criado_por", "conexoes", ["criado_por"])
    op.create_index(
        "ix_conexoes_escopo_situacao", "conexoes", ["tenant_id", "project_id", "situacao"]
    )
    op.create_table(
        "eventos_conexao",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=200), nullable=False),
        sa.Column("project_id", sa.String(length=200), nullable=False),
        sa.Column("conexao_id", sa.String(length=36), nullable=False),
        sa.Column("acao", sa.String(length=30), nullable=False),
        sa.Column("ator_pessoa_id", sa.String(length=36), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ator_pessoa_id"], ["pessoas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eventos_conexao_conexao_id", "eventos_conexao", ["conexao_id"])
    op.create_index("ix_eventos_conexao_criado_em", "eventos_conexao", ["criado_em"])
    op.add_column("bases", sa.Column("conexao_embeddings_id", sa.String(length=36), nullable=True))
    op.add_column(
        "bases", sa.Column("conexao_vector_store_id", sa.String(length=36), nullable=True)
    )
    op.add_column("bases", sa.Column("chunking", sa.JSON(), nullable=True))
    op.create_foreign_key(
        "fk_bases_conexao_embeddings",
        "bases",
        "conexoes",
        ["conexao_embeddings_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_bases_conexao_vector_store",
        "bases",
        "conexoes",
        ["conexao_vector_store_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_bases_conexao_vector_store", "bases", type_="foreignkey")
    op.drop_constraint("fk_bases_conexao_embeddings", "bases", type_="foreignkey")
    op.drop_column("bases", "chunking")
    op.drop_column("bases", "conexao_vector_store_id")
    op.drop_column("bases", "conexao_embeddings_id")
    op.drop_index("ix_eventos_conexao_criado_em", table_name="eventos_conexao")
    op.drop_index("ix_eventos_conexao_conexao_id", table_name="eventos_conexao")
    op.drop_table("eventos_conexao")
    op.drop_index("ix_conexoes_escopo_situacao", table_name="conexoes")
    op.drop_index("ix_conexoes_criado_por", table_name="conexoes")
    op.drop_table("conexoes")
