"""Limpeza de conteúdo, domínio por Workspace e relatório do lote (SPEC-0037)."""

import sqlalchemy as sa

from alembic import op

revision = "0037_limpeza_dominio"
down_revision = "0036_conversao_formatos"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dominios_workspace",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("versao", sa.Integer(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("vigente", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("aprovado_por", sa.String(36), sa.ForeignKey("pessoas.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "versao", name="uq_dominios_workspace_versao"),
    )
    op.create_index(
        "ix_dominios_workspace_vigente", "dominios_workspace", ["workspace_id", "vigente"]
    )
    op.create_table(
        "exclusoes_limpeza",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("lote_id", sa.String(36), sa.ForeignKey("lotes_conversao.id"), nullable=False),
        sa.Column(
            "documento_id", sa.String(36), sa.ForeignKey("documentos_conversao.id"), nullable=True
        ),
        sa.Column("arquivo", sa.String(255), nullable=False),
        sa.Column("posicao", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(200), nullable=False),
        sa.Column("camada", sa.String(20), nullable=False),
        sa.Column("confianca", sa.Float(), nullable=True),
        sa.Column("trecho", sa.Text(), nullable=True),
        sa.Column("mantido_em", sa.String(255), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_exclusoes_limpeza_lote", "exclusoes_limpeza", ["lote_id"])
    op.create_table(
        "relatorios_lote",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "lote_id",
            sa.String(36),
            sa.ForeignKey("lotes_conversao.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("conteudo", sa.Text(), nullable=False),
        sa.Column("ia_usada", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("provedor", sa.String(100), nullable=True),
        sa.Column(
            "dominio_versao_id",
            sa.String(36),
            sa.ForeignKey("dominios_workspace.id"),
            nullable=True,
        ),
        sa.Column("contagens", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column(
        "workspaces",
        sa.Column("ia_externa_permitida", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "workspaces",
        sa.Column("conexao_ia_id", sa.String(36), sa.ForeignKey("conexoes.id"), nullable=True),
    )
    op.add_column(
        "documentos_conversao", sa.Column("limpeza_situacao", sa.String(30), nullable=True)
    )
    op.add_column(
        "documentos_conversao",
        sa.Column("duvidas", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "documentos_conversao",
        sa.Column("exclusoes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("documentos_conversao", sa.Column("limpeza_erro", sa.Text(), nullable=True))
    op.add_column(
        "lotes_conversao",
        sa.Column(
            "dominio_versao_id",
            sa.String(36),
            sa.ForeignKey("dominios_workspace.id"),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("lotes_conversao", "dominio_versao_id")
    for nome in ("limpeza_erro", "exclusoes", "duvidas", "limpeza_situacao"):
        op.drop_column("documentos_conversao", nome)
    op.drop_column("workspaces", "conexao_ia_id")
    op.drop_column("workspaces", "ia_externa_permitida")
    op.drop_table("relatorios_lote")
    op.drop_index("ix_exclusoes_limpeza_lote", table_name="exclusoes_limpeza")
    op.drop_table("exclusoes_limpeza")
    op.drop_index("ix_dominios_workspace_vigente", table_name="dominios_workspace")
    op.drop_table("dominios_workspace")
