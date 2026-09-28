"""adiciona pessoas, sessões, eventos de acesso e autoria

Revision ID: 0020_pessoas
Revises: 0019_workspaces
Create Date: 2026-09-21 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0020_pessoas"
down_revision: str | Sequence[str] | None = "0019_workspaces"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pessoas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("senha_hash", sa.Text(), nullable=False),
        sa.Column("precisa_trocar_senha", sa.Boolean(), nullable=False),
        sa.Column("situacao", sa.String(length=20), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("criada_por", sa.String(length=36), nullable=True),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["criada_por"], ["pessoas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_pessoas_email_lower", "pessoas", [sa.text("lower(email)")], unique=True
    )

    op.create_table(
        "vinculos_pessoa",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pessoa_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=200), nullable=False),
        sa.Column("project_id", sa.String(length=200), nullable=False),
        sa.Column("papel", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["pessoa_id"], ["pessoas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pessoa_id"),
    )
    op.create_index("ix_vinculos_pessoa_pessoa_id", "vinculos_pessoa", ["pessoa_id"])
    op.create_index(
        "ix_vinculos_pessoa_tenant_project",
        "vinculos_pessoa",
        ["tenant_id", "project_id"],
    )

    op.create_table(
        "sessoes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pessoa_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pessoa_id"], ["pessoas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_sessoes_pessoa_id", "sessoes", ["pessoa_id"])
    op.create_index("ix_sessoes_token_hash", "sessoes", ["token_hash"], unique=True)
    op.create_index("ix_sessoes_expira_em", "sessoes", ["expira_em"])

    op.create_table(
        "tentativas_login",
        sa.Column("email_normalizado", sa.String(length=320), nullable=False),
        sa.Column("falhas_seguidas", sa.Integer(), nullable=False),
        sa.Column("bloqueada_ate", sa.DateTime(timezone=True), nullable=True),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("email_normalizado"),
    )
    op.create_index("ix_tentativas_login_bloqueada_ate", "tentativas_login", ["bloqueada_ate"])

    op.create_table(
        "eventos_acesso",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("motivo", sa.String(length=100), nullable=True),
        sa.Column("ator_pessoa_id", sa.String(length=36), nullable=True),
        sa.Column("alvo_pessoa_id", sa.String(length=36), nullable=True),
        sa.Column("tenant_id", sa.String(length=200), nullable=True),
        sa.Column("project_id", sa.String(length=200), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ator_pessoa_id"], ["pessoas.id"]),
        sa.ForeignKeyConstraint(["alvo_pessoa_id"], ["pessoas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eventos_acesso_tipo", "eventos_acesso", ["tipo"])
    op.create_index("ix_eventos_acesso_criado_em", "eventos_acesso", ["criado_em"])

    for tabela in ("workspaces", "bases", "executions", "queries"):
        op.add_column(tabela, sa.Column("criado_por", sa.String(length=36), nullable=True))
        op.create_foreign_key(
            f"fk_{tabela}_criado_por_pessoas",
            tabela,
            "pessoas",
            ["criado_por"],
            ["id"],
        )
        op.create_index(f"ix_{tabela}_criado_por", tabela, ["criado_por"])


def downgrade() -> None:
    for tabela in reversed(("workspaces", "bases", "executions", "queries")):
        op.drop_index(f"ix_{tabela}_criado_por", table_name=tabela)
        op.drop_constraint(f"fk_{tabela}_criado_por_pessoas", tabela, type_="foreignkey")
        op.drop_column(tabela, "criado_por")

    op.drop_index("ix_eventos_acesso_criado_em", table_name="eventos_acesso")
    op.drop_index("ix_eventos_acesso_tipo", table_name="eventos_acesso")
    op.drop_table("eventos_acesso")
    op.drop_index("ix_tentativas_login_bloqueada_ate", table_name="tentativas_login")
    op.drop_table("tentativas_login")
    op.drop_index("ix_sessoes_expira_em", table_name="sessoes")
    op.drop_index("ix_sessoes_token_hash", table_name="sessoes")
    op.drop_index("ix_sessoes_pessoa_id", table_name="sessoes")
    op.drop_table("sessoes")
    op.drop_index("ix_vinculos_pessoa_tenant_project", table_name="vinculos_pessoa")
    op.drop_index("ix_vinculos_pessoa_pessoa_id", table_name="vinculos_pessoa")
    op.drop_table("vinculos_pessoa")
    op.drop_index("uq_pessoas_email_lower", table_name="pessoas")
    op.drop_table("pessoas")
