"""Campos aditivos da conversão Fase 1 (SPEC-0036)."""

import sqlalchemy as sa

from alembic import op

revision = "0036_conversao_formatos"
down_revision = "0031_conteudo_documento"
branch_labels = None
depends_on = None


def upgrade():
    for nome, tipo in (
        ("origem_url", sa.Text()),
        ("abas_disponiveis", sa.JSON()),
        ("abas_selecionadas", sa.JSON()),
        ("reprocessado_ia_em", sa.DateTime(timezone=True)),
    ):
        op.add_column("documentos_conversao", sa.Column(nome, tipo, nullable=True))


def downgrade():
    for nome in ("reprocessado_ia_em", "abas_selecionadas", "abas_disponiveis", "origem_url"):
        op.drop_column("documentos_conversao", nome)
