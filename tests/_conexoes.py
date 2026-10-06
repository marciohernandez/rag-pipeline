"""Apoio dos testes da SPEC-0026: conexões, publicação e arquivos de ingestão.

O código de produção da SPEC-0026 ainda não existe quando estes testes são
escritos (fase RED). Os casos exercitam a API HTTP da seção 10 da spec e só
importam o que for preciso ler do banco por :func:`recurso`, que reprova o
teste com mensagem clara quando o modelo ainda não existe.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from tests._pessoas import recurso, sessao_do_banco

OWNER = {"Authorization": "Bearer pessoa-teste-owner"}
ADMIN = {"Authorization": "Bearer pessoa-teste-admin"}
MEMBER = {"Authorization": "Bearer pessoa-teste-member"}
OUTRA_EQUIPE = {"Authorization": "Bearer pessoa-teste-outro-tenant"}

CHAVE_EMBEDDINGS = "sk-spec0026-chave-de-embeddings-9f3a"
CHAVE_QDRANT = "qd-spec0026-chave-do-qdrant-7c1e"
CHAVE_NOVA = "qd-spec0026-chave-nova-5b2d"
MASCARA = "••••••••"


def cliente() -> TestClient:
    from src.app.main import app

    return TestClient(app)


def storage_temporario(tmp_path: Path, monkeypatch) -> Path:
    """Aponta o storage da aplicação para um diretório descartável."""
    from src.app import storage as storage_module
    from src.app.storage import LocalDirectoryStorage

    pasta = tmp_path / "uploads-spec-0026"
    monkeypatch.setattr(storage_module, "_STORAGE", LocalDirectoryStorage(str(pasta)))
    return pasta


def payload_embeddings(**alteracoes: Any) -> dict[str, Any]:
    dados: dict[str, Any] = {
        "nome": f"OpenAI {uuid.uuid4().hex[:6]}",
        "tipo": "embeddings_openai",
        "configuracao": {"modelo": "text-embedding-3-small", "dimensoes": 1536},
        "segredo": CHAVE_EMBEDDINGS,
    }
    dados.update(alteracoes)
    return dados


def payload_qdrant(**alteracoes: Any) -> dict[str, Any]:
    dados: dict[str, Any] = {
        "nome": f"Qdrant {uuid.uuid4().hex[:6]}",
        "tipo": "qdrant",
        "configuracao": {"url": "https://qdrant.exemplo.com"},
        "segredo": CHAVE_QDRANT,
    }
    dados.update(alteracoes)
    return dados


def criar_conexao(client: TestClient, payload: dict[str, Any], headers=OWNER):
    return client.post("/api/v1/conexoes", json=payload, headers=headers)


def criar_conexao_ok(client: TestClient, payload: dict[str, Any], headers=OWNER) -> dict:
    resposta = criar_conexao(client, payload, headers)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_workspace(client: TestClient, headers=OWNER) -> str:
    resposta = client.post(
        "/api/v1/workspaces", json={"nome": f"WS {uuid.uuid4().hex[:6]}"}, headers=headers
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


def arquivos_md(quantidade: int = 1) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [
        (
            "arquivos",
            (
                f"doc-{indice}.md",
                f"# Documento {indice}\n\n## Seção A\n\nTexto da seção A {indice}.\n\n"
                f"## Seção B\n\nTexto da seção B {indice}.".encode(),
                "text/markdown",
            ),
        )
        for indice in range(quantidade)
    ]


def publicar(
    client: TestClient,
    workspace_id: str,
    conexao_embeddings_id: str,
    conexao_vector_store_id: str,
    *,
    headers=OWNER,
    colecao: str = "produtos",
    arquivos=None,
    **extra: Any,
):
    campos: dict[str, Any] = {
        "workspace_id": workspace_id,
        "collection_name": colecao,
        "splitter": "header",
        "chunk_size": "800",
        "chunk_overlap": "100",
        "conexao_embeddings_id": conexao_embeddings_id,
        "conexao_vector_store_id": conexao_vector_store_id,
        "iniciar_execucao": "true",
    }
    campos.update(extra)
    return client.post(
        "/api/v1/bases",
        data=campos,
        files=arquivos if arquivos is not None else arquivos_md(2),
        headers=headers,
    )


def descrever_colecao(monkeypatch, *, existe: bool, dimensoes: int | None = None) -> None:
    """Fixa o que a fachada devolve ao consultar a coleção, sem rede."""
    resposta = {"exists": existe, "dimensions": dimensoes} if existe else {}
    monkeypatch.setattr(
        "src.pipeline.service.describe_collection",
        lambda *args, **kwargs: resposta,
        raising=False,
    )


def capturar_agendamento(monkeypatch) -> list[dict[str, Any]]:
    """Captura os argumentos de ``process_base_task.defer`` sem enfileirar."""
    from src.app.tasks import process_base_task

    capturados: list[dict[str, Any]] = []
    monkeypatch.setattr(process_base_task, "defer", lambda **kwargs: capturados.append(kwargs))
    return capturados


def eventos_da_conexao(conexao_id: str) -> list[str]:
    modelo = recurso("src.app.models", "EventoConexao")
    with sessao_do_banco() as sessao:
        linhas = sessao.query(modelo).filter(modelo.conexao_id == conexao_id).all()
        return sorted(linha.acao for linha in linhas)


def linha_da_conexao(conexao_id: str) -> Any:
    modelo = recurso("src.app.models", "Conexao")
    with sessao_do_banco() as sessao:
        linha = sessao.get(modelo, conexao_id)
        sessao.expunge(linha)
        return linha


def criar_base_vinculada(conexao_embeddings_id: str, conexao_vector_store_id: str) -> str:
    """Grava uma Base já ligada às duas conexões, direto pelo modelo."""
    from src.app.models import Base, Workspace

    with sessao_do_banco() as sessao:
        workspace = Workspace(tenant_id="tenant-1", project_id="projeto-1", nome="WS vínculo")
        sessao.add(workspace)
        sessao.flush()
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            workspace_id=workspace.id,
            nome="base-vinculada.md",
            origem="upload",
            collection_name="produtos",
            documentos=1,
            conexao_embeddings_id=conexao_embeddings_id,
            conexao_vector_store_id=conexao_vector_store_id,
        )
        sessao.add(base)
        sessao.commit()
        return base.id


def contar(modelo_nome: str) -> int:
    from src.app import models

    modelo = getattr(models, modelo_nome)
    with sessao_do_banco() as sessao:
        return sessao.query(modelo).count()
