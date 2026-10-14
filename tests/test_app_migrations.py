"""Teste de integração da migração Alembic inicial (SPEC-0012, T037/T038).

Roda somente avanços Alembic em schemas exclusivos no banco de testes
(nunca apagado — este projeto proíbe DROP DATABASE/DROP TABLE/TRUNCATE mesmo
sobre bancos descartáveis, ver `.specsfy/Spec.md`), e confere via
`sqlalchemy.inspect` que as tabelas e colunas esperadas existem.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import uuid
from pathlib import Path

import psycopg
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from tests._database_safety import configure_testing_environment

BANCO_DE_SCRATCH = ""


@pytest.fixture(autouse=True)
def _schema_de_migracoes(monkeypatch):
    """Schema novo por caso, preservado; a cadeia só avança, nunca recua."""
    base = make_url(configure_testing_environment())
    schema = f"migration_test_{uuid.uuid4().hex}"
    with psycopg.connect(
        base.set(drivername="postgresql").render_as_string(hide_password=False),
        autocommit=True,
    ) as connection:
        connection.execute(
            psycopg.sql.SQL("CREATE SCHEMA {}").format(psycopg.sql.Identifier(schema))
        )
    # Schemas preservados acumulam catálogo; paralelismo na inspeção pode
    # esgotar /dev/shm de um PostgreSQL em Docker. Só esta sessão de teste usa
    # consultas sequenciais, sem alterar o servidor ou apagar diagnósticos.
    url = base.update_query_dict({
        "options": f"-csearch_path={schema} -cmax_parallel_workers_per_gather=0"
    })
    monkeypatch.setattr(
        sys.modules[__name__], "BANCO_DE_SCRATCH", url.render_as_string(hide_password=False)
    )


def _downgrade_ast(arquivo: str) -> ast.FunctionDef:
    """Inspeção de contrato sem executar SQL de remoção."""
    source = Path(__file__).resolve().parents[1] / "alembic" / "versions" / arquivo
    module = ast.parse(source.read_text())
    return next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "downgrade"
    )


def _tabelas_removidas(function: ast.FunctionDef) -> set[str]:
    return {
        call.args[0].value
        for call in ast.walk(function)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "drop_table"
        and isinstance(call.args[0], ast.Constant)
    }


REVISAO_ANTERIOR_SPEC_0019 = "4d0fd0aa498e"


def _executar_alembic(comando: str, revisao: str) -> None:
    assert comando == "upgrade", "Somente avanços não destrutivos são permitidos"
    ambiente = dict(os.environ)
    ambiente["APP_DATABASE_URL"] = BANCO_DE_SCRATCH
    ambiente["APP_VECTOR_STORE_COLLECTION"] = "rag-pipeline-app"
    resultado = subprocess.run(
        [sys.executable, "-m", "alembic", comando, revisao],
        cwd=str(__file__.rsplit("/tests/", 1)[0]),
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stderr


def _alembic_spec_0019(revisao: str) -> None:
    _executar_alembic("upgrade", revisao)


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
            base_migrada = connection.execute(
                text(
                    "SELECT workspace_id, collection_name, metadados_chunk "
                    "FROM bases WHERE id = :id"
                ),
                {"id": base_id},
            ).one()
            workspace_id = base_migrada.workspace_id
            workspace = connection.execute(
                text("SELECT tenant_id, project_id, nome FROM workspaces WHERE id = :id"),
                {"id": workspace_id},
            ).one()
        assert workspace == (tenant_id, project_id, "Workspace padrão")
        assert base_migrada.collection_name == "rag-pipeline-app"
        assert base_migrada.metadados_chunk == []
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


def test_spec_0019_contrato_de_downgrade_preserva_tabelas_legadas() -> None:
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
                    "(id, base_id, situacao, etapa, previstos, inseridos, mantidos, removidos, "
                    "iniciado_em) "
                    "VALUES (:id, :base_id, 'succeeded', 'concluido', 1, 1, 0, 0, now())"
                ),
                {"id": execution_id, "base_id": base_id},
            )
            connection.execute(
                text(
                    "INSERT INTO queries "
                    "(id, base_id, tenant_id, project_id, pergunta, resultado, chunks_fontes, "
                    "criado_em) "
                    "VALUES (:id, :base_id, 'tenant', 'project', 'pergunta', 'resultado', "
                    "'[]', now())"
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
    contrato = _downgrade_ast("0019_workspaces.py")
    assert _tabelas_removidas(contrato) == {"workspaces"}
    # A preservação dos registros é provada pelo upgrade real; a remoção
    # de estruturas do downgrade é apenas inspecionada, jamais executada.

    engine = create_engine(BANCO_DE_SCRATCH)
    try:
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT count(*) FROM bases WHERE id = :id"), {"id": base_id}
                ).scalar_one()
                == 1
            )
            assert (
                connection.execute(
                    text("SELECT count(*) FROM executions WHERE id = :id"), {"id": execution_id}
                ).scalar_one()
                == 1
            )
            assert (
                connection.execute(
                    text("SELECT count(*) FROM queries WHERE id = :id"), {"id": query_id}
                ).scalar_one()
                == 1
            )
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
        assert {"workspaces", "bases", "executions", "queries", "alembic_version"} <= tabelas
        assert {"conexoes", "eventos_conexao"} <= tabelas  # SPEC-0026
        colunas_documento = {
            coluna["name"]: coluna for coluna in inspetor.get_columns("documentos_conversao")
        }
        assert colunas_documento["avisos"]["nullable"] is False
        assert "[]" in colunas_documento["avisos"]["default"]

        colunas_workspaces = {coluna["name"] for coluna in inspetor.get_columns("workspaces")}
        assert colunas_workspaces == {
            "id",
            "tenant_id",
            "project_id",
            "nome",
            "criado_em",
            "apagada_em",
            "criado_por",
        }

        colunas_bases = {coluna["name"] for coluna in inspetor.get_columns("bases")}
        assert colunas_bases == {
            "id",
            "tenant_id",
            "project_id",
            "workspace_id",
            "nome",
            "origem",
            "collection_name",
            "metadados_chunk",
            "documentos",
            "conexao_embeddings_id",
            "conexao_vector_store_id",
            "chunking",
            "criado_em",
            "apagada_em",
            "criado_por",
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
            "criado_por",
        }

        colunas_queries = {coluna["name"] for coluna in inspetor.get_columns("queries")}
        assert colunas_queries == {
            "id",
            "base_id",
            "colecao_id",
            "tenant_id",
            "project_id",
            "pergunta",
            "resultado",
            "chunks_fontes",
            "criado_em",
            "criado_por",
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


# --------------------------------------------------------------------------
# SPEC-0020 — pessoas, sessões, tentativas, eventos e autoria (fase RED).
# --------------------------------------------------------------------------

REVISAO_ANTERIOR_SPEC_0020 = "0019_workspaces"
REVISAO_SPEC_0020 = "0020_pessoas"
TABELAS_SPEC_0020 = {
    "pessoas",
    "vinculos_pessoa",
    "sessoes",
    "tentativas_login",
    "eventos_acesso",
}
TABELAS_COM_AUTORIA_SPEC_0020 = ("workspaces", "bases", "executions", "queries")


def _alembic_spec_0020(revisao: str) -> None:
    """Avança a cadeia no schema exclusivo do caso."""
    _executar_alembic("upgrade", revisao)


def _inserir_dados_da_spec_0019(*, tenant_id: str, project_id: str) -> dict[str, str]:
    """Grava um Workspace, uma Base, uma Execução e uma Consulta no esquema da SPEC-0019."""
    ids = {chave: str(uuid.uuid4()) for chave in ("workspace", "base", "execucao", "consulta")}
    engine = create_engine(BANCO_DE_SCRATCH)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO workspaces (id, tenant_id, project_id, nome, criado_em) "
                    "VALUES (:id, :t, :p, 'Anterior', now())"
                ),
                {"id": ids["workspace"], "t": tenant_id, "p": project_id},
            )
            connection.execute(
                text(
                    "INSERT INTO bases (id, tenant_id, project_id, workspace_id, nome, origem, "
                    "collection_name, documentos, criado_em) "
                    "VALUES (:id, :t, :p, :w, 'base', 'upload', 'colecao', 1, now())"
                ),
                {"id": ids["base"], "t": tenant_id, "p": project_id, "w": ids["workspace"]},
            )
            connection.execute(
                text(
                    "INSERT INTO executions (id, base_id, situacao, etapa, previstos, inseridos, "
                    "mantidos, removidos, iniciado_em) "
                    "VALUES (:id, :b, 'succeeded', 'concluido', 1, 1, 0, 0, now())"
                ),
                {"id": ids["execucao"], "b": ids["base"]},
            )
            connection.execute(
                text(
                    "INSERT INTO queries (id, base_id, tenant_id, project_id, pergunta, "
                    "resultado, chunks_fontes, criado_em) "
                    "VALUES (:id, :b, :t, :p, 'pergunta', 'resultado', '[]', now())"
                ),
                {"id": ids["consulta"], "b": ids["base"], "t": tenant_id, "p": project_id},
            )
    finally:
        engine.dispose()
    return ids


def test_upgrade_preserva_linhas_e_deixa_autoria_vazia() -> None:
    """SPECSFY: SPEC-0020 US-005 US-007 FR-011 FR-013 NFR-006 AC-020"""
    _alembic_spec_0020(REVISAO_ANTERIOR_SPEC_0020)
    tenant_id = f"tenant-{uuid.uuid4()}"
    ids = _inserir_dados_da_spec_0019(tenant_id=tenant_id, project_id="projeto-1")

    _executar_alembic("upgrade", REVISAO_SPEC_0020)

    engine = create_engine(BANCO_DE_SCRATCH)
    try:
        inspetor = inspect(engine)
        assert set(inspetor.get_table_names()) >= TABELAS_SPEC_0020
        with engine.connect() as connection:
            for tabela, chave in zip(
                TABELAS_COM_AUTORIA_SPEC_0020,
                ("workspace", "base", "execucao", "consulta"),
                strict=True,
            ):
                colunas = {coluna["name"] for coluna in inspetor.get_columns(tabela)}
                assert "criado_por" in colunas, f"{tabela} sem criado_por"
                linha = connection.execute(
                    text(f"SELECT id, criado_por FROM {tabela} WHERE id = :id"),
                    {"id": ids[chave]},
                ).one()
                assert linha.id == ids[chave]
                assert linha.criado_por is None
    finally:
        engine.dispose()


def test_contrato_de_downgrade_remove_somente_estruturas_da_revisao() -> None:
    """SPECSFY: SPEC-0020 US-007 FR-013 NFR-006 AC-029

    Inspeção AST do contrato de reversão; nenhuma reversão SQL é executada.
    O upgrade e a preservação dos registros continuam provas de integração.
    """
    contrato = _downgrade_ast("0020_pessoas_e_autoria.py")
    assert _tabelas_removidas(contrato) == TABELAS_SPEC_0020
    loops = [node for node in ast.walk(contrato) if isinstance(node, ast.For)]
    assert len(loops) == 1
    alvo = loops[0]
    assert isinstance(alvo.iter, ast.Call) and alvo.iter.func.id == "reversed"
    assert set(ast.literal_eval(alvo.iter.args[0])) == set(TABELAS_COM_AUTORIA_SPEC_0020)
    colunas = [
        node
        for node in ast.walk(contrato)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "drop_column"
    ]
    assert len(colunas) == 1 and ast.literal_eval(colunas[0].args[1]) == "criado_por"
    # Nenhuma exclusão de dados nem SQL arbitrário pode ser introduzido.
    chamadas = {
        node.func.attr
        for node in ast.walk(contrato)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert chamadas == {"drop_index", "drop_constraint", "drop_column", "drop_table"}
