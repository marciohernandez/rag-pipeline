"""Origem do documento indexado a partir de um lote de conversão (SPEC-0043)."""

import sqlalchemy as sa

from alembic import op

revision = "0043_origem_documento_lote"
down_revision = "0042_schema_da_fila"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "origens_documento",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "documento_colecao_id",
            sa.String(36),
            sa.ForeignKey("documentos_colecao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("lote_id", sa.String(36), sa.ForeignKey("lotes_conversao.id"), nullable=False),
        sa.Column(
            "documento_conversao_id",
            sa.String(36),
            sa.ForeignKey("documentos_conversao.id"),
            nullable=False,
        ),
        sa.Column("envio_id", sa.String(36), sa.ForeignKey("envios.id"), nullable=False),
        sa.Column("hash_md", sa.String(64), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "uq_origens_documento_documento", "origens_documento", ["documento_colecao_id"], unique=True
    )
    op.create_index("ix_origens_documento_lote", "origens_documento", ["lote_id"])


def downgrade() -> None:
    op.drop_index("ix_origens_documento_lote", table_name="origens_documento")
    op.drop_index("uq_origens_documento_documento", table_name="origens_documento")
    op.drop_table("origens_documento")
