"""Bancos de scratch por schema para os testes da SPEC-0042.

Cada chamada cria um schema novo no banco de testes e devolve a URL que o aponta
por ``search_path``. Nada é apagado: os schemas ficam preservados para diagnóstico
e a cadeia Alembic só avança (``upgrade``) ou marca a versão (``stamp``), em linha
com a regra do projeto contra ``DROP``, ``TRUNCATE`` e rollback.
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from psycopg import connect, sql
from psycopg.conninfo import make_conninfo
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from tests._database_safety import configure_testing_environment

RAIZ = Path(__file__).resolve().parents[1]
REVISAO_ANTERIOR = "0040_grupos_e_tabelas"
COMANDOS_PERMITIDOS = {"upgrade", "stamp"}


def novo_banco() -> str:
    """Cria um schema exclusivo no banco de testes e devolve a URL que o usa."""
    base = make_url(configure_testing_environment())
    schema = f"fila_test_{uuid.uuid4().hex}"
    conninfo = base.set(drivername="postgresql").render_as_string(hide_password=False)
    with connect(conninfo, autocommit=True) as conexao:
        conexao.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    url = base.update_query_dict(
        {"options": f"-csearch_path={schema} -cmax_parallel_workers_per_gather=0"}
    )
    return url.render_as_string(hide_password=False)


def alembic(url: str, *argumentos: str) -> subprocess.CompletedProcess[str]:
    """Roda o Alembic como a pessoa operadora faria, apontado para o schema de scratch."""
    assert argumentos[0] in COMANDOS_PERMITIDOS, "Somente upgrade e stamp são permitidos"
    ambiente = dict(os.environ)
    ambiente["APP_DATABASE_URL"] = url
    ambiente["APP_VECTOR_STORE_COLLECTION"] = "rag-pipeline-app"
    return subprocess.run(
        [sys.executable, "-m", "alembic", *argumentos],
        cwd=str(RAIZ),
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def cabeca() -> str:
    """Revisão head dos scripts de ``alembic/versions``."""
    configuracao = Config(str(RAIZ / "alembic.ini"))
    configuracao.set_main_option("script_location", str(RAIZ / "alembic"))
    return ScriptDirectory.from_config(configuracao).get_current_head()


def tabelas(url: str) -> list[str]:
    engine = create_engine(url)
    try:
        return sorted(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def tabelas_da_fila(url: str) -> list[str]:
    return [nome for nome in tabelas(url) if nome.startswith("procrastinate_")]


def versao(url: str) -> str | None:
    engine = create_engine(url)
    try:
        if "alembic_version" not in inspect(engine).get_table_names():
            return None
        with engine.connect() as conexao:
            return conexao.execute(text("SELECT version_num FROM alembic_version")).scalar()
    finally:
        engine.dispose()


def aplicar_fila_a_mao(url: str) -> None:
    """Reproduz o ``procrastinate schema --apply`` manual que o ensaio local exigiu."""
    import procrastinate
    from procrastinate.schema import SchemaManager

    destino = make_url(url)
    conninfo = make_conninfo(
        host=destino.host,
        port=destino.port,
        dbname=destino.database,
        user=destino.username,
        password=destino.password,
        options=destino.query["options"],
    )
    conector = procrastinate.PsycopgConnector(conninfo=conninfo)
    sincrono = conector.get_sync_connector()
    sincrono.open()
    try:
        SchemaManager(conector).apply_schema()
    finally:
        sincrono.close()


def criar_como_o_create_all(url: str) -> None:
    """Estado legado: tabelas do app criadas por ``create_all`` e sem ``alembic_version``."""
    from src.app import models  # noqa: F401 — registra os modelos
    from src.app.db import ORMBase

    engine = create_engine(url)
    try:
        ORMBase.metadata.create_all(engine)
    finally:
        engine.dispose()
