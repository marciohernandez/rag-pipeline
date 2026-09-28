"""Fixtures do backend de aplicação (SPEC-0012) para a suíte pytest.

Configura a URL do PostgreSQL de teste antes de qualquer import de
``src.app.main`` e limpa as tabelas entre os testes que efetivamente usam o
backend de aplicação, sem afetar a suíte do pipeline (``src/pipeline``), que
não importa ``src.app``.
"""

from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault(
    "APP_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test",
)


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
def _limpar_tabelas_do_backend_de_aplicacao(_sessoes_reais_para_suites_legadas):
    yield
    if "src.app.main" not in sys.modules:
        return
    from src.app import db
    from src.app.db import ORMBase

    with db.SessionLocal() as session:
        for table in reversed(ORMBase.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
