"""Apoio dos testes da SPEC-0021 (assistente especialista em RAG).

O código de produção da SPEC-0021 ainda não existe quando estes testes são
escritos (fase RED). Cada função importa o recurso só ao ser chamada e usa
:func:`exigir`, que reprova o teste com mensagem clara quando o módulo ou o
atributo ainda não existe; a falha acontece no corpo do teste, nunca na coleta.

Contratos fixados pelos testes (a implementação os segue):

* ``ProviderFactory.create_chat_model(nome, settings)`` devolve um adapter com
  ``responder(mensagens, timeout) -> str``; os testes de API o substituem por
  :class:`ModeloDeTeste`.
* ``src.pipeline.service.query_base`` é a única porta de recuperação vetorial
  do assistente; os testes a substituem por :func:`instalar_busca`.
* Papéis das mensagens enviadas ao modelo: ``sistema``, ``pessoa`` e
  ``assistente``; a fonte de um trecho vem de ``metadata["caminho_origem"]``.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest
from fastapi.testclient import TestClient

BASE_URL = "/api/v1/assistente"


def exigir(modulo: str, nome: str | None = None) -> Any:
    """Importa ``modulo`` (e ``nome``) ou reprova por comportamento ausente."""
    try:
        carregado = importlib.import_module(modulo)
    except ImportError:
        pytest.fail(f"{modulo} ainda não existe (comportamento da SPEC-0021 ausente)")
    if nome is None:
        return carregado
    if not hasattr(carregado, nome):
        pytest.fail(f"{modulo}.{nome} ainda não existe (comportamento da SPEC-0021 ausente)")
    return getattr(carregado, nome)


class ModeloDeTeste:
    """Modelo de linguagem de teste: responde texto fixo e registra o contexto."""

    def __init__(
        self, resposta: str = "Resposta fixa do assistente de teste.", erro: Exception | None = None
    ):
        self.resposta = resposta
        self.erro = erro
        self.chamadas: list[list[Any]] = []

    def responder(self, mensagens, timeout=None) -> str:
        self.chamadas.append(list(mensagens))
        if self.erro is not None:
            raise self.erro
        return self.resposta

    def contexto(self, indice: int = -1) -> str:
        return "\n".join(m.conteudo for m in self.chamadas[indice])

    def papeis(self, indice: int = -1) -> list[str]:
        return [m.papel for m in self.chamadas[indice]]


def instalar_modelo(monkeypatch, modelo: ModeloDeTeste) -> ModeloDeTeste:
    """Registra ``modelo`` como o adapter de chat devolvido pela factory."""
    fabrica = exigir("src.pipeline.providers.factory", "ProviderFactory")
    if not hasattr(fabrica, "create_chat_model"):
        pytest.fail("ProviderFactory.create_chat_model ainda não existe (SPEC-0021 ausente)")
    monkeypatch.setattr(
        fabrica, "create_chat_model", staticmethod(lambda nome=None, settings=None, **_: modelo)
    )
    return modelo


def instalar_busca(
    monkeypatch, por_colecao: dict[str, list] | None = None, *, falhar: bool = False
):
    """Substitui ``service.query_base``; ``por_colecao['*']`` vale para as demais."""
    from src.pipeline import service

    chamadas: list[dict] = []
    por_colecao = por_colecao or {}

    def falsa(config, query, *, top_k=4, tenant_id=None):
        chamadas.append(config)
        if falhar:
            raise RuntimeError("qdrant indisponivel em 10.0.0.7 com senha-interna")
        colecao = config["vector_store"]["collection_name"]
        return list(por_colecao.get(colecao, por_colecao.get("*", [])))

    monkeypatch.setattr(service, "query_base", falsa)
    return chamadas


def resultado(conteudo: str, origem: str, **extra: object):
    from src.pipeline.providers.contracts import SearchResult

    return SearchResult(content=conteudo, metadata={"caminho_origem": origem, **extra}, score=1.0)


def cliente() -> TestClient:
    from src.app.main import app

    return TestClient(app)


def criar_base(
    *,
    tenant: str = "tenant-1",
    projeto: str = "projeto-1",
    nome: str = "Manuais de produto",
    execucao: str | None = "succeeded",
    apagada: bool = False,
) -> dict[str, str]:
    """Grava Workspace, Base e (opcional) Execução diretamente no banco de teste."""
    from datetime import UTC, datetime

    from src.app import db
    from src.app.models import Base, Execution, Workspace

    with db.SessionLocal() as sessao:
        workspace = Workspace(tenant_id=tenant, project_id=projeto, nome=f"WS {nome}")
        sessao.add(workspace)
        sessao.flush()
        base = Base(
            tenant_id=tenant,
            project_id=projeto,
            workspace_id=workspace.id,
            nome=nome,
            origem="upload",
            collection_name=f"col-{workspace.id}",
            documentos=2,
            apagada_em=datetime.now(UTC) if apagada else None,
        )
        sessao.add(base)
        sessao.flush()
        if execucao is not None:
            sessao.add(
                Execution(
                    base_id=base.id,
                    situacao=execucao,
                    etapa="concluido",
                    previstos=1,
                    inseridos=1,
                    mantidos=0,
                    removidos=0,
                )
            )
        sessao.commit()
        return {"id": base.id, "nome": nome, "colecao": base.collection_name}


def nova_conversa(cli: TestClient, cabecalho: dict[str, str]) -> str:
    resposta = cli.post(f"{BASE_URL}/conversas", headers=cabecalho)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


def enviar(
    cli: TestClient, cabecalho: dict[str, str], conversa_id: str, texto: str, **extra: object
):
    return cli.post(
        f"{BASE_URL}/conversas/{conversa_id}/mensagens",
        json={"texto": texto, **extra},
        headers=cabecalho,
    )


def contar(nome_modelo: str) -> int:
    from tests._pessoas import consultar

    return len(consultar(nome_modelo))
