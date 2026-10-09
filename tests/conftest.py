"""Fixtures do backend de aplicação (SPEC-0012) para a suíte pytest.

Valida .env.testing antes de importar a aplicação. Usa rollback transacional
nos casos comuns e schemas exclusivos nos casos com conexões concorrentes.
Não apaga tabelas nem registros existentes.
"""

from __future__ import annotations

import os
import uuid

import procrastinate
import psycopg
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from procrastinate.schema import SchemaManager
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from tests._database_safety import configure_testing_environment

TEST_DATABASE_URL = configure_testing_environment()

# SPEC-0026: chave de cifra das conexões só para a suíte; nunca um valor real.
os.environ.setdefault("APP_CONEXOES_CHAVE", Fernet.generate_key().decode())


@pytest.fixture
def vector_store_em_memoria(monkeypatch):
    """Fixa o vector store do backend de aplicação em ``in_memory``.

    Alguns casos exercitam consulta/exclusão sem dublar o provider e só não
    tocavam a rede porque o padrão de ``APP_VECTOR_STORE_PROVIDER`` era
    ``in_memory``. Desde 2026-09-07 o padrão é ``qdrant`` — o único provider que
    `SyncSafetyPolicy` aceita para escrita, e portanto o único padrão capaz de
    concluir uma execução real. Depender de um padrão de produção para não abrir
    conexão era acoplamento indevido: quem precisa de ``in_memory`` declara.
    """
    import src.app.main  # noqa: F401 — efeito colateral: settings.configure(...)
    from src.app import settings
    from src.app.settings import AppSettings

    atual = settings.get_settings()
    monkeypatch.setattr(
        settings,
        "_SETTINGS",
        AppSettings(
            embedding=dict(atual.embedding),
            vector_store={**atual.vector_store, "provider": "in_memory"},
        ),
    )


@pytest.fixture(autouse=True)
def _sessoes_reais_para_suites_legadas(monkeypatch):
    """Converte identidades simbólicas dos testes em sessões reais no banco.

    As suítes anteriores à SPEC-0020 continuam legíveis quanto ao papel que
    exercitam, mas cada requisição autentica uma Pessoa real e uma Sessão
    revogável, exatamente como a aplicação em produção.
    """
    original_request = TestClient.request
    tokens: dict[str, str] = {}
    identidades = {
        "pessoa-teste-owner": {"papel": "owner"},
        "pessoa-teste-admin": {"papel": "admin"},
        "pessoa-teste-member": {"papel": "member"},
        "pessoa-teste-outro-tenant": {
            "papel": "owner",
            "tenant": "tenant-2",
            "projeto": "projeto-2",
        },
    }

    def request_com_sessao_real(self, method, url, **kwargs):
        headers = dict(kwargs.get("headers") or {})
        authorization = headers.get("Authorization") or headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            identidade = authorization.removeprefix("Bearer ")
            campos = identidades.get(identidade)
            if campos is not None:
                if identidade not in tokens:
                    from tests._pessoas import criar_pessoa

                    pessoa = criar_pessoa(**campos)
                    resposta = original_request(
                        self,
                        "POST",
                        "/api/v1/auth/login",
                        json={"email": pessoa["email"], "senha": pessoa["senha"]},
                    )
                    assert resposta.status_code == 200
                    tokens[identidade] = resposta.json()["token"]
                headers["Authorization"] = f"Bearer {tokens[identidade]}"
                kwargs["headers"] = headers
        return original_request(self, method, url, **kwargs)

    monkeypatch.setattr(TestClient, "request", request_com_sessao_real)


@pytest.fixture(autouse=True)
def _isolar_backend(request, monkeypatch, _sessoes_reais_para_suites_legadas):
    if (
        not request.node.path.name.startswith("test_app_")
        or request.node.path.name == "test_app_migrations.py"
    ):
        yield
        return
    import src.app.main  # noqa: F401 — configuração inicial já validada
    from src.app import db, tasks

    # Schema novo, sem fallback para public. Fica preservado para diagnóstico;
    # testes concorrentes precisam de commits visíveis entre conexões reais.
    schema = f"test_{uuid.uuid4().hex}"
    url = make_url(TEST_DATABASE_URL)
    conninfo = url.set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(conninfo, autocommit=True) as connection:
        connection.execute(
            psycopg.sql.SQL("CREATE SCHEMA {}").format(psycopg.sql.Identifier(schema))
        )
    isolated_url = url.update_query_dict({"options": f"-csearch_path={schema}"})
    engine = create_engine(isolated_url)
    db.ORMBase.metadata.create_all(engine)
    isolated_conninfo = isolated_url.set(drivername="postgresql").render_as_string(
        hide_password=False
    )
    connector = procrastinate.PsycopgConnector(conninfo=isolated_conninfo)
    sync_connector = connector.get_sync_connector()
    sync_connector.open()
    SchemaManager(connector).apply_schema()
    previous_connector = tasks.app.connector
    tasks.app.connector = connector
    tasks.app.job_manager.connector = connector
    monkeypatch.setenv("APP_DATABASE_URL", isolated_url.render_as_string(hide_password=False))
    monkeypatch.setattr(db, "_engine", engine)

    concurrent = request.node.path.name in {
        "test_app_people.py",
        "test_app_executions.py",
        "test_app_worker.py",
    }
    connection = engine.connect()
    transaction = None if concurrent else connection.begin()
    db.SessionLocal.configure(
        bind=engine if concurrent else connection,
        join_transaction_mode="conditional_savepoint" if concurrent else "create_savepoint",
    )
    try:
        yield
    finally:
        if transaction is not None and transaction.is_active:
            transaction.rollback()
        connection.close()
        db.SessionLocal.configure(bind=None, join_transaction_mode="conditional_savepoint")
        tasks.app.connector = previous_connector
        tasks.app.job_manager.connector = previous_connector
        sync_connector.close()
        engine.dispose()


@pytest.fixture(autouse=True)
def _teste_de_conexao_sem_rede(request, monkeypatch):
    """Substitui o teste de conexão ao salvar (SPEC-0029) para que nenhum caso faça rede.

    `tests/test_app_conexoes_teste.py` exercita o teste real com o cliente do
    Qdrant e o adapter de embeddings dublados, então fica de fora.
    """
    if request.node.path.name == "test_app_conexoes_teste.py":
        return
    from src.pipeline import service

    monkeypatch.setattr(
        service,
        "testar_conexao",
        lambda configuracao: {"sucesso": True, "mensagem": "Conexão testada com sucesso."},
    )
