"""Decisão da empresa, versões de documento e liberação da coleção (SPEC-0039)."""

import sqlalchemy as sa

from alembic import op

revision = "0039_decisoes_empresa"
down_revision = "0038_contradicoes"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("colecoes", sa.Column("revisada_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "colecoes",
        sa.Column("revisada_por", sa.String(36), sa.ForeignKey("pessoas.id"), nullable=True),
    )
    op.create_table(
        "respostas_empresa",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("colecao_id", sa.String(36), sa.ForeignKey("colecoes.id"), nullable=False),
        sa.Column(
            "analise_id",
            sa.String(36),
            sa.ForeignKey("analises_contradicao.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("situacao", sa.String(20), nullable=False),
        sa.Column("motivo", sa.String(200), nullable=True),
        sa.Column("criado_por", sa.String(36), sa.ForeignKey("pessoas.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_respostas_empresa_colecao", "respostas_empresa", ["colecao_id", "criado_em"]
    )
    op.create_table(
        "propostas_correcao",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "resposta_id", sa.String(36), sa.ForeignKey("respostas_empresa.id"), nullable=False
        ),
        sa.Column(
            "ocorrencia_id",
            sa.String(36),
            sa.ForeignKey("ocorrencias_contradicao.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("situacao", sa.String(20), nullable=False),
        sa.Column("arquivo", sa.String(255), nullable=True),
        sa.Column("documento_id", sa.String(36), nullable=True),
        sa.Column("trecho_alvo", sa.Text(), nullable=False),
        sa.Column("texto_corrigido", sa.Text(), nullable=False),
        sa.Column("hash_documento", sa.String(64), nullable=True),
        sa.Column("motivo", sa.String(200), nullable=True),
    )
    op.create_index("ix_propostas_correcao_resposta", "propostas_correcao", ["resposta_id"])
    op.create_table(
        "decisoes_empresa",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "proposta_id", sa.String(36), sa.ForeignKey("propostas_correcao.id"), nullable=True
        ),
        sa.Column("colecao_id", sa.String(36), sa.ForeignKey("colecoes.id"), nullable=False),
        sa.Column("ocorrencia_id", sa.String(36), nullable=True),
        sa.Column("arquivo", sa.String(255), nullable=True),
        sa.Column("confirmado_por", sa.String(36), sa.ForeignKey("pessoas.id"), nullable=True),
        sa.Column("confirmado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("editada", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("versao_resultante", sa.Integer(), nullable=True),
        sa.Column("restaurada_de", sa.Integer(), nullable=True),
        sa.Column("resposta_trecho", sa.Text(), nullable=False),
        sa.Column("texto_proposto", sa.Text(), nullable=False),
        sa.Column("texto_aplicado", sa.Text(), nullable=False),
    )
    op.create_index(
        "ix_decisoes_empresa_colecao", "decisoes_empresa", ["colecao_id", "confirmado_em"]
    )
    op.create_table(
        "versoes_documento",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "documento_id",
            sa.String(36),
            sa.ForeignKey("documentos_colecao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("chave_armazenamento", sa.String(255), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "uq_versoes_documento_numero", "versoes_documento", ["documento_id", "numero"], unique=True
    )
    op.create_table(
        "registros_exclusao_decisoes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("colecao_id", sa.String(36), nullable=False),
        sa.Column("apagado_por", sa.String(36), nullable=True),
        sa.Column("apagado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decisoes", sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_table("registros_exclusao_decisoes")
    op.drop_index("uq_versoes_documento_numero", table_name="versoes_documento")
    op.drop_table("versoes_documento")
    op.drop_index("ix_decisoes_empresa_colecao", table_name="decisoes_empresa")
    op.drop_table("decisoes_empresa")
    op.drop_index("ix_propostas_correcao_resposta", table_name="propostas_correcao")
    op.drop_table("propostas_correcao")
    op.drop_index("ix_respostas_empresa_colecao", table_name="respostas_empresa")
    op.drop_table("respostas_empresa")
    op.drop_column("colecoes", "revisada_por")
    op.drop_column("colecoes", "revisada_em")
