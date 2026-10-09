"""adiciona coleções por Workspace, documentos, envios e a coleção das consultas

Revision ID: 0030_colecoes
Revises: 0026_conexoes_ingestao
Create Date: 2026-10-09 00:00:00.000000

Sem ``DROP`` nem ``TRUNCATE``: ``bases`` e ``executions`` permanecem como tabelas
legadas (SPEC-0030, PR-002).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0030_colecoes"
down_revision: str | Sequence[str] | None = "0026_conexoes_ingestao"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "colecoes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=200), nullable=False),
        sa.Column("project_id", sa.String(length=200), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("nome_normalizado", sa.String(length=80), nullable=False),
        sa.Column("nome_fisico", sa.String(length=255), nullable=False),
        sa.Column("conexao_embeddings_id", sa.String(length=36), nullable=False),
        sa.Column("conexao_vector_store_id", sa.String(length=36), nullable=False),
        sa.Column("dimensao", sa.Integer(), nullable=False),
        sa.Column("criado_por", sa.String(length=36), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("apagada_em", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["conexao_embeddings_id"], ["conexoes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["conexao_vector_store_id"], ["conexoes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["criado_por"], ["pessoas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome_fisico"),
    )
    op.create_index("ix_colecoes_workspace_id", "colecoes", ["workspace_id"])
    op.create_index("ix_colecoes_criado_por", "colecoes", ["criado_por"])
    op.create_index(
        "uq_colecoes_nome_ativo",
        "colecoes",
        ["workspace_id", "nome_normalizado"],
        unique=True,
        postgresql_where=sa.text("apagada_em IS NULL"),
    )
    op.create_table(
        "envios",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("colecao_id", sa.String(length=36), nullable=False),
        sa.Column("arquivos", sa.JSON(), nullable=False),
        sa.Column("processamento", sa.JSON(), nullable=False),
        sa.Column(
            "metadados_chunk", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False
        ),
        sa.Column("situacao", sa.String(length=20), nullable=False),
        sa.Column("etapa", sa.String(length=50), nullable=False),
        sa.Column("previstos", sa.Integer(), nullable=False),
        sa.Column("inseridos", sa.Integer(), nullable=False),
        sa.Column("mantidos", sa.Integer(), nullable=False),
        sa.Column("removidos", sa.Integer(), nullable=False),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("iniciado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_por", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["colecao_id"], ["colecoes.id"]),
        sa.ForeignKeyConstraint(["criado_por"], ["pessoas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_envios_colecao_id", "envios", ["colecao_id"])
    op.create_index("ix_envios_criado_por", "envios", ["criado_por"])
    op.create_table(
        "documentos_colecao",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("colecao_id", sa.String(length=36), nullable=False),
        sa.Column("nome_arquivo", sa.String(length=255), nullable=False),
        sa.Column("document_id", sa.String(length=200), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("chunks", sa.Integer(), nullable=False),
        sa.Column("chunking", sa.JSON(), nullable=False),
        sa.Column("ultimo_envio_id", sa.String(length=36), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["colecao_id"], ["colecoes.id"]),
        sa.ForeignKeyConstraint(["ultimo_envio_id"], ["envios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documentos_colecao_colecao_id", "documentos_colecao", ["colecao_id"])
    op.create_index(
        "uq_documentos_colecao_nome",
        "documentos_colecao",
        ["colecao_id", "nome_arquivo"],
        unique=True,
    )
    op.add_column("queries", sa.Column("colecao_id", sa.String(length=36), nullable=True))
    op.create_foreign_key("fk_queries_colecao_id", "queries", "colecoes", ["colecao_id"], ["id"])
    op.create_index("ix_queries_colecao_id", "queries", ["colecao_id"])
    op.alter_column("queries", "base_id", existing_type=sa.String(length=36), nullable=True)


def downgrade() -> None:
    """Remove somente o que esta revisão criou.

    ``queries.base_id`` volta a ser obrigatório apenas se nenhuma consulta de
    coleção existir; do contrário o downgrade precisa de revisão humana.
    """
    op.alter_column("queries", "base_id", existing_type=sa.String(length=36), nullable=False)
    op.drop_index("ix_queries_colecao_id", table_name="queries")
    op.drop_constraint("fk_queries_colecao_id", "queries", type_="foreignkey")
    op.drop_column("queries", "colecao_id")
    op.drop_index("uq_documentos_colecao_nome", table_name="documentos_colecao")
    op.drop_index("ix_documentos_colecao_colecao_id", table_name="documentos_colecao")
    op.drop_table("documentos_colecao")
    op.drop_index("ix_envios_criado_por", table_name="envios")
    op.drop_index("ix_envios_colecao_id", table_name="envios")
    op.drop_table("envios")
    op.drop_index("uq_colecoes_nome_ativo", table_name="colecoes")
    op.drop_index("ix_colecoes_criado_por", table_name="colecoes")
    op.drop_index("ix_colecoes_workspace_id", table_name="colecoes")
    op.drop_table("colecoes")
