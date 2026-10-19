"""Grupos de imagens do lote de conversão (SPEC-0040)."""

import sqlalchemy as sa

from alembic import op

revision = "0040_grupos_e_tabelas"
down_revision = "0039_decisoes_empresa"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "grupos_imagem",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("lote_id", sa.String(36), sa.ForeignKey("lotes_conversao.id"), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("certeza", sa.String(10), nullable=False),
        sa.Column("aprovado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("documento_id", sa.String(36), nullable=True),
    )
    op.create_index("ix_grupos_imagem_lote", "grupos_imagem", ["lote_id"])
    op.add_column(
        "documentos_conversao",
        sa.Column("grupo_id", sa.String(36), sa.ForeignKey("grupos_imagem.id"), nullable=True),
    )
    op.add_column(
        "documentos_conversao", sa.Column("posicao_no_grupo", sa.Integer(), nullable=True)
    )
    op.add_column(
        "documentos_conversao",
        sa.Column("modificado_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("documentos_conversao", sa.Column("pasta_origem", sa.String(255), nullable=True))
    op.create_index("ix_documentos_conversao_grupo_id", "documentos_conversao", ["grupo_id"])


def downgrade():
    op.drop_index("ix_documentos_conversao_grupo_id", table_name="documentos_conversao")
    op.drop_column("documentos_conversao", "pasta_origem")
    op.drop_column("documentos_conversao", "modificado_em")
    op.drop_column("documentos_conversao", "posicao_no_grupo")
    op.drop_column("documentos_conversao", "grupo_id")
    op.drop_index("ix_grupos_imagem_lote", table_name="grupos_imagem")
    op.drop_table("grupos_imagem")
