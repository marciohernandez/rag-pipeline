"""Análise de contradições entre documentos da coleção (SPEC-0038)."""

import sqlalchemy as sa

from alembic import op

revision = "0038_contradicoes"
down_revision = "0037_limpeza_dominio"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analises_contradicao",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("colecao_id", sa.String(36), sa.ForeignKey("colecoes.id"), nullable=False),
        sa.Column("situacao", sa.String(20), nullable=False),
        sa.Column("motivo", sa.String(200), nullable=True),
        sa.Column("iniciada_por", sa.String(36), sa.ForeignKey("pessoas.id"), nullable=True),
        sa.Column("provedor", sa.String(100), nullable=True),
        sa.Column(
            "dominio_versao_id",
            sa.String(36),
            sa.ForeignKey("dominios_workspace.id"),
            nullable=True,
        ),
        sa.Column("total_assuntos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("concluidos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documentos_analisados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progresso", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_analises_contradicao_colecao", "analises_contradicao", ["colecao_id", "criado_em"]
    )
    op.create_table(
        "ocorrencias_contradicao",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "analise_id", sa.String(36), sa.ForeignKey("analises_contradicao.id"), nullable=False
        ),
        sa.Column("assunto", sa.String(200), nullable=False),
        sa.Column("assunto_normalizado", sa.String(200), nullable=False),
        sa.Column("etiqueta", sa.String(30), nullable=False),
        sa.Column("impacto", sa.String(10), nullable=False),
        sa.Column("chave_trechos", sa.String(64), nullable=False),
        sa.Column("trechos", sa.JSON(), nullable=False),
        sa.Column("explicacao", sa.Text(), nullable=False),
        sa.Column("arquivo_mais_antigo", sa.String(255), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "analise_id",
            "assunto_normalizado",
            "chave_trechos",
            name="uq_ocorrencias_contradicao_idempotencia",
        ),
    )
    op.create_index(
        "ix_ocorrencias_contradicao_analise", "ocorrencias_contradicao", ["analise_id"]
    )


def downgrade():
    op.drop_index("ix_ocorrencias_contradicao_analise", table_name="ocorrencias_contradicao")
    op.drop_table("ocorrencias_contradicao")
    op.drop_index("ix_analises_contradicao_colecao", table_name="analises_contradicao")
    op.drop_table("analises_contradicao")
