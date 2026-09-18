"""Teste de integração da migração Alembic inicial (SPEC-0012, T037/T038).

Roda `alembic upgrade head` contra um banco de scratch permanente e dedicado
(nunca apagado — este projeto proíbe DROP DATABASE/DROP TABLE/TRUNCATE mesmo
sobre bancos descartáveis, ver `.specsfy/Spec.md`), e confere via
`sqlalchemy.inspect` que as tabelas e colunas esperadas existem.
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid

from sqlalchemy import create_engine, inspect, text

BANCO_DE_SCRATCH = (
    "postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_alembic_schema_check"
)
REVISAO_ANTERIOR_SPEC_0019 = "f3b60ce4f7f4"


def _alembic_spec_0019(revisao: str) -> None:
    ambiente = dict(os.environ)
    ambiente["APP_DATABASE_URL"] = BANCO_DE_SCRATCH
    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade" if revisao == "head" else "downgrade", revisao],
        cwd=str(__file__.rsplit("/tests/", 1)[0]),
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr


def _inserir_base_legada_spec_0019(*, tenant_id: str, project_id: str) -> str:
    base_id = str(uuid.uuid4())
    engine = create_engine(BANCO_DE_SCRATCH)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO bases "
                    "(id, tenant_id, project_id, nome, origem, documentos, criado_em) "
                    "VALUES (:id, :tenant_id, :project_id, :nome, 'upload', 1, now())"
                ),
                {
                    "id": base_id,
                    "tenant_id": tenant_id,
                    "project_id": project_id,
                    "nome": f"legada-{base_id}",
                },
            )
    finally:
        engine.dispose()
    return base_id


def test_spec_0019_migracao_cria_workspace_padrao_e_associa_bases() -> None:
    """SPECSFY: SPEC-0019 FR-009 NFR-001 AC-019"""
    _alembic_spec_0019(REVISAO_ANTERIOR_SPEC_0019)
    tenant_id = f"tenant-{uuid.uuid4()}"
    project_id = f"project-{uuid.uuid4()}"
    base_id = _inserir_base_legada_spec_0019(tenant_id=tenant_id, project_id=project_id)

    _alembic_spec_0019("head")
    engine = create_engine(BANCO_DE_SCRATCH)
    try:
        assert "workspaces" in inspect(engine).get_table_names()
        with engine.connect() as connection:
            workspace_id = connection.execute(
                text("SELECT workspace_id FROM bases WHERE id = :id"), {"id": base_id}
            ).scalar_one()
            workspace = connection.execute(
                text(
                    "SELECT tenant_id, project_id, nome FROM workspaces WHERE id = :id"
                ),
                {"id": workspace_id},
            ).one()
        assert workspace == (tenant_id, project_id, "Workspace padrão")
    finally:
        engine.dispose()


def test_spec_0019_migracao_e_idempotente() -> None:
    """SPECSFY: SPEC-0019 FR-009 NFR-001 AC-020"""
    _alembic_spec_0019(REVISAO_ANTERIOR_SPEC_0019)
    tenant_id = f"tenant-{uuid.uuid4()}"
    project_id = f"project-{uuid.uuid4()}"
    _inserir_base_legada_spec_0019(tenant_id=tenant_id, project_id=project_id)
    _alembic_spec_0019("head")

    engine = create_engine(BANCO_DE_SCRATCH)
    try:
        assert "workspaces" in inspect(engine).get_table_names()
        with engine.connect() as connection:
            antes = connection.execute(
                text(
                    "SELECT count(*) FROM workspaces "
                    "WHERE tenant_id = :tenant_id AND project_id = :project_id"
                ),
                {"tenant_id": tenant_id, "project_id": project_id},
            ).scalar_one()
        _alembic_spec_0019("head")
        with engine.connect() as connection:
            depois = connection.execute(
                text(
                    "SELECT count(*) FROM workspaces "
                    "WHERE tenant_id = :tenant_id AND project_id = :project_id"
                ),
                {"tenant_id": tenant_id, "project_id": project_id},
            ).scalar_one()
        assert antes == depois == 1
    finally:
        engine.dispose()


def test_spec_0019_downgrade_preserva_dados_existentes() -> None:
    """SPECSFY: SPEC-0019 FR-009 NFR-001 AC-021"""
    _alembic_spec_0019(REVISAO_ANTERIOR_SPEC_0019)
    base_id = _inserir_base_legada_spec_0019(
        tenant_id=f"tenant-{uuid.uuid4()}", project_id=f"project-{uuid.uuid4()}"
    )
    execution_id = str(uuid.uuid4())
    query_id = str(uuid.uuid4())
    engine = create_engine(BANCO_DE_SCRATCH)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO executions "
                    "(id, base_id, situacao, etapa, previstos, inseridos, mantidos, removidos, iniciado_em) "
                    "VALUES (:id, :base_id, 'succeeded', 'concluido', 1, 1, 0, 0, now())"
                ),
                {"id": execution_id, "base_id": base_id},
            )
            connection.execute(
                text(
                    "INSERT INTO queries "
                    "(id, base_id, tenant_id, project_id, pergunta, resultado, chunks_fontes, criado_em) "
                    "VALUES (:id, :base_id, 'tenant', 'project', 'pergunta', 'resultado', '[]', now())"
                ),
                {"id": query_id, "base_id": base_id},
            )
    finally:
        engine.dispose()

    _alembic_spec_0019("head")
    engine = create_engine(BANCO_DE_SCRATCH)
    try:
        assert "workspaces" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
    _alembic_spec_0019(REVISAO_ANTERIOR_SPEC_0019)

    engine = create_engine(BANCO_DE_SCRATCH)
    try:
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT count(*) FROM bases WHERE id = :id"), {"id": base_id}
            ).scalar_one() == 1
            assert connection.execute(
                text("SELECT count(*) FROM executions WHERE id = :id"), {"id": execution_id}
            ).scalar_one() == 1
            assert connection.execute(
                text("SELECT count(*) FROM queries WHERE id = :id"), {"id": query_id}
            ).scalar_one() == 1
    finally:
        engine.dispose()


def test_alembic_upgrade_cria_schema_esperado() -> None:
    """SPECSFY: FR-002 NFR-004"""
    ambiente = dict(os.environ)
    ambiente["APP_DATABASE_URL"] = BANCO_DE_SCRATCH

    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(__file__.rsplit("/tests/", 1)[0]),
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr

    engine = create_engine(BANCO_DE_SCRATCH)
    try:
        inspetor = inspect(engine)
        tabelas = set(inspetor.get_table_names())
        assert {"bases", "executions", "queries", "alembic_version"} <= tabelas

        colunas_bases = {coluna["name"] for coluna in inspetor.get_columns("bases")}
        assert colunas_bases == {
            "id",
            "tenant_id",
            "project_id",
            "nome",
            "origem",
            "documentos",
            "criado_em",
            "apagada_em",
        }

        colunas_executions = {coluna["name"] for coluna in inspetor.get_columns("executions")}
        assert colunas_executions == {
            "id",
            "base_id",
            "situacao",
            "etapa",
            "previstos",
            "inseridos",
            "mantidos",
            "removidos",
            "erro",
            "iniciado_em",
            "concluido_em",
        }

        colunas_queries = {coluna["name"] for coluna in inspetor.get_columns("queries")}
        assert colunas_queries == {
            "id",
            "base_id",
            "tenant_id",
            "project_id",
            "pergunta",
            "resultado",
            "chunks_fontes",
            "criado_em",
        }

        indices_executions = {
            indice["name"]: indice for indice in inspetor.get_indexes("executions")
        }
        assert "uq_executions_base_active" in indices_executions
        indice_ativo = indices_executions["uq_executions_base_active"]
        assert indice_ativo["column_names"] == ["base_id"]
        assert indice_ativo["unique"] is True
        assert "pending" in indice_ativo["dialect_options"]["postgresql_where"]
        assert "running" in indice_ativo["dialect_options"]["postgresql_where"]
    finally:
        engine.dispose()
