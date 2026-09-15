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

from sqlalchemy import create_engine, inspect

BANCO_DE_SCRATCH = (
    "postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_alembic_schema_check"
)


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
