"""Entrypoint FastAPI do backend de aplicação (SPEC-0012).

Como os CLIs da raiz, este módulo é o único ponto que resolve variáveis de
ambiente e monta a configuração injetada nos demais módulos de ``src/app`` e
na fachada de ``src/pipeline`` (PR-002). Nenhum outro módulo de ``src/app``
lê ``os.environ`` diretamente.
"""

from __future__ import annotations

import os
from pathlib import Path

import procrastinate
import yaml
from fastapi import FastAPI

import src.pipeline.service as service  # noqa: PLR0402 — fronteira AST exige fachada explícita
from src.app import db, settings, storage, tasks
from src.app.routers import (
    assistente,
    auth,
    colecoes,
    conexoes,
    contradicoes,
    conversao,
    envios,
    ingestao,
    people,
    workspaces,
)
from src.app.settings import AppSettings

__all__ = ["app"]


def _database_url() -> str:
    return os.environ.get(
        "APP_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/rag_pipeline",
    )


def _procrastinate_conninfo() -> str:
    """psycopg (usado pelo conector Procrastinate) exige libpq puro, sem o
    qualificador de dialeto ``+psycopg`` que o SQLAlchemy aceita."""
    return _database_url().replace("postgresql+psycopg://", "postgresql://")


def _chave_de_cifra_das_conexoes() -> str:
    """Lê a chave de cifra de um arquivo de secret (Swarm) ou da variável."""
    arquivo = os.environ.get("APP_CONEXOES_CHAVE_FILE")
    if arquivo:
        try:
            with open(arquivo, encoding="utf-8") as conteudo:
                return conteudo.read().strip()
        except OSError:
            return ""
    return os.environ.get("APP_CONEXOES_CHAVE", "").strip()


def _app_settings() -> AppSettings:
    caminho = Path(__file__).resolve().parents[2] / "config.yaml"
    config = yaml.safe_load(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}
    conversao = service.validar_config_conversao(config or {})
    return AppSettings(
        conversao=conversao,
        embedding={
            "provider": os.environ.get("APP_EMBEDDING_PROVIDER", "fake"),
            "dimensions": int(os.environ.get("APP_EMBEDDING_DIMENSIONS", "16")),
        },
        vector_store={
            # `qdrant` é o único provider que `SyncSafetyPolicy` aceita para
            # escrita. Com o antigo padrão `in_memory`, uma instalação sem a
            # variável definida subia normalmente e só falhava lá dentro da
            # tarefa em segundo plano, com o erro genérico de
            # `process_base_task` — nenhuma execução real conseguia concluir.
            "provider": os.environ.get("APP_VECTOR_STORE_PROVIDER", "qdrant"),
            "collection_name": os.environ.get("APP_VECTOR_STORE_COLLECTION", "rag-pipeline-app"),
        },
        # Assistente (SPEC-0021): a chave só vive aqui, no entrypoint.
        llm={
            "provider": os.environ.get("APP_LLM_PROVIDER", "openrouter"),
            "model": os.environ.get("LLM_MODEL", ""),
            "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
            "timeout": float(os.environ.get("APP_LLM_TIMEOUT", "30")),
        },
        conhecimento_collection=os.environ.get(
            "APP_ASSISTANT_KNOWLEDGE_COLLECTION", "assistente_conhecimento"
        ),
        conexoes_chave=_chave_de_cifra_das_conexoes(),
        conteudo_max_caracteres=int(os.environ.get("APP_CONTEUDO_MAX_CARACTERES", "2000000")),
        conexoes_permitir_locais=os.environ.get("APP_CONEXOES_PERMITIR_HOSTS_LOCAIS", "").lower()
        in {"1", "true", "sim"},
    )


def _storage() -> storage.Storage:
    bucket = os.environ.get("APP_R2_BUCKET")
    endpoint = os.environ.get("APP_R2_ENDPOINT_URL")
    access_key = os.environ.get("APP_R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("APP_R2_SECRET_ACCESS_KEY")
    if bucket and endpoint and access_key and secret_key:
        return storage.S3CompatibleStorage(
            bucket=bucket, endpoint_url=endpoint, access_key=access_key, secret_key=secret_key
        )
    return storage.LocalDirectoryStorage(os.environ.get("APP_LOCAL_STORAGE_DIR", "output/uploads"))


db.configure(_database_url())
db.create_tables()
settings.configure(_app_settings())
storage.configure(_storage())
tasks.configure_connector(procrastinate.PsycopgConnector(conninfo=_procrastinate_conninfo()))

app = FastAPI(title="RAG Pipeline — Backend de aplicação")
app.include_router(assistente.router)
app.include_router(auth.router)
app.include_router(colecoes.router)
app.include_router(conexoes.router)
app.include_router(contradicoes.router)
app.include_router(conversao.router)
app.include_router(envios.router)
app.include_router(ingestao.router)
app.include_router(people.router)
app.include_router(workspaces.router)
