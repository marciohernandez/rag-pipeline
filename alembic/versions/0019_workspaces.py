"""adiciona workspaces e configurações persistentes das bases

Revision ID: 0019_workspaces
Revises: 4d0fd0aa498e
Create Date: 2026-09-18 00:00:00.000000

"""

from __future__ import annotations

import os
import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019_workspaces"
down_revision: str | Sequence[str] | None = "4d0fd0aa498e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOME_WORKSPACE_PADRAO = "Workspace padrão"
_COLECAO_LEGADA_PADRAO = "rag-pipeline-app"


def _collection_name_legada() -> str:
    """Preserva a coleção global usada pelo backend antes da SPEC-0019."""
    configurada = os.environ.get("APP_VECTOR_STORE_COLLECTION", "").strip()
    return configurada or _COLECAO_LEGADA_PADRAO


def _backfill_bases() -> None:
    conexao = op.get_bind()
    escopos = conexao.execute(
        sa.text(
            "SELECT DISTINCT tenant_id, project_id "
            "FROM bases WHERE workspace_id IS NULL "
            "ORDER BY tenant_id, project_id"
        )
    ).mappings()

    for escopo in escopos:
        workspace_id = conexao.execute(
            sa.text(
                "SELECT id FROM workspaces "
                "WHERE tenant_id = :tenant_id AND project_id = :project_id "
                "AND nome = :nome AND apagada_em IS NULL "
                "ORDER BY criado_em, id LIMIT 1"
            ),
            {
                "tenant_id": escopo["tenant_id"],
                "project_id": escopo["project_id"],
                "nome": _NOME_WORKSPACE_PADRAO,
            },
        ).scalar_one_or_none()
        if workspace_id is None:
            workspace_id = str(uuid.uuid4())
            conexao.execute(
                sa.text(
                    "INSERT INTO workspaces "
                    "(id, tenant_id, project_id, nome, criado_em) "
                    "VALUES (:id, :tenant_id, :project_id, :nome, now())"
                ),
                {
                    "id": workspace_id,
                    "tenant_id": escopo["tenant_id"],
                    "project_id": escopo["project_id"],
                    "nome": _NOME_WORKSPACE_PADRAO,
                },
            )

        conexao.execute(
            sa.text(
                "UPDATE bases SET workspace_id = :workspace_id "
                "WHERE workspace_id IS NULL "
                "AND tenant_id = :tenant_id AND project_id = :project_id"
            ),
            {
                "workspace_id": workspace_id,
                "tenant_id": escopo["tenant_id"],
                "project_id": escopo["project_id"],
            },
        )

    conexao.execute(
        sa.text(
            "UPDATE bases SET collection_name = :collection_name "
            "WHERE collection_name IS NULL"
        ),
        {"collection_name": _collection_name_legada()},
    )


def upgrade() -> None:
    """Cria Workspaces e associa todas as Bases legadas atomicamente."""
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=200), nullable=False),
        sa.Column("project_id", sa.String(length=200), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("apagada_em", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workspaces_tenant_project",
        "workspaces",
        ["tenant_id", "project_id"],
        unique=False,
    )

    op.add_column("bases", sa.Column("workspace_id", sa.String(length=36), nullable=True))
    op.add_column("bases", sa.Column("collection_name", sa.String(length=255), nullable=True))
    op.add_column(
        "bases",
        sa.Column(
            "metadados_chunk",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )

    _backfill_bases()

    op.alter_column("bases", "workspace_id", existing_type=sa.String(length=36), nullable=False)
    op.alter_column(
        "bases", "collection_name", existing_type=sa.String(length=255), nullable=False
    )
    op.create_foreign_key(
        "fk_bases_workspace_id_workspaces",
        "bases",
        "workspaces",
        ["workspace_id"],
        ["id"],
    )
    op.create_index("ix_bases_workspace_id", "bases", ["workspace_id"], unique=False)


def downgrade() -> None:
    """Remove o schema da SPEC-0019 sem apagar Bases, Execuções ou Queries."""
    op.drop_index("ix_bases_workspace_id", table_name="bases")
    op.drop_constraint("fk_bases_workspace_id_workspaces", "bases", type_="foreignkey")
    op.drop_column("bases", "metadados_chunk")
    op.drop_column("bases", "collection_name")
    op.drop_column("bases", "workspace_id")
    op.drop_index("ix_workspaces_tenant_project", table_name="workspaces")
    op.drop_table("workspaces")
