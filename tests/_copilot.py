"""Apoio dos testes da SPEC-0031 (copilot com acesso ao sistema e ao conteúdo processado).

O código de produção da SPEC-0031 ainda não existe quando estes testes são
escritos (fase RED). Contratos fixados pelos testes (a implementação os segue):

* O nó ``classificar`` do grafo chama o modelo uma vez, antes da resposta, com
  uma mensagem ``sistema`` que começa com :data:`CLASSIFICAR` e espera de volta
  as recuperações necessárias, separadas por espaço: ``colecoes``, ``estado``,
  ``processado`` ou ``nenhuma``. :class:`ModeloCopilot` responde por esse
  contrato e separa essa chamada das de resposta (``chamadas``/``contexto``).
* ``src.app.assistente_contexto.LIMITE_DE_TRECHOS`` é o teto de trechos
  recuperados por turno.
* ``AppSettings.conteudo_max_caracteres`` é o limite do texto convertido
  guardado por documento (padrão 2000000).
* ``ConteudoDocumento`` (``conteudos_documento``): ``documento_id`` único,
  ``texto``, ``trechos`` (lista de ``{"ordem", "texto", "etiquetas"}`` com
  ``ordem`` a partir de 1 e ``etiquetas`` como dicionário rótulo → valor),
  ``envio_id``, ``truncado`` e ``atualizado_em``.
* Fonte de resposta: ``{"tipo", "rotulo", "colecao_id", "documento",
  "envio_id", "rota"}``; ``rotulo`` de documento é "documento — coleção";
  ``rota`` é ``/workspaces/{workspace_id}/colecoes/{colecao_id}`` para
  coleção e documento e ``/envios/{envio_id}`` para envio.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

from tests._assistente import (
    ModeloDeTeste,
    cliente,
    enviar,
    exigir,
    instalar_busca,
    instalar_modelo,
    nova_conversa,
)
from tests._pessoas import sessao_do_banco

CLASSIFICAR = "[CLASSIFICAR]"
TUDO = "colecoes estado processado"


def exigir_copilot(modulo: str, nome: str | None = None) -> Any:
    """Importa ``modulo`` (e ``nome``) ou reprova por comportamento ausente."""
    try:
        carregado = importlib.import_module(modulo)
    except ImportError:
        pytest.fail(f"{modulo} ainda não existe (comportamento da SPEC-0031 ausente)")
    if nome is None:
        return carregado
    if not hasattr(carregado, nome):
        pytest.fail(f"{modulo}.{nome} ainda não existe (comportamento da SPEC-0031 ausente)")
    return getattr(carregado, nome)


class ModeloCopilot(ModeloDeTeste):
    """Modelo de teste que responde a classificação e registra só os turnos de resposta."""

    def __init__(
        self,
        resposta: str = "Resposta fixa do copilot de teste.",
        *,
        classificacao: str = TUDO,
        erro: Exception | None = None,
    ):
        super().__init__(resposta, erro)
        self.classificacao = classificacao
        self.classificacoes: list[list[Any]] = []
        self.timeouts: list[Any] = []

    def responder(self, mensagens, timeout=None) -> str:
        if mensagens and mensagens[0].conteudo.lstrip().startswith(CLASSIFICAR):
            self.classificacoes.append(list(mensagens))
            return self.classificacao
        self.timeouts.append(timeout)
        return super().responder(mensagens, timeout)

    def tudo(self) -> str:
        """Todo texto enviado ao modelo, inclusive nas chamadas de classificação."""
        mensagens = [m for lote in (*self.classificacoes, *self.chamadas) for m in lote]
        return "\n".join(m.conteudo for m in mensagens)


def preparar_copilot(monkeypatch, *, modelo: ModeloCopilot | None = None, busca=None):
    exigir("src.app.routers.assistente")
    modelo = instalar_modelo(monkeypatch, modelo or ModeloCopilot())
    chamadas = instalar_busca(monkeypatch, busca or {})
    return modelo, chamadas


def perguntar(cli, cabecalho, texto: str, **extra: object):
    conversa = nova_conversa(cli, cabecalho)
    return enviar(cli, cabecalho, conversa, texto, **extra)


def consultadas(chamadas: list[dict]) -> set[str]:
    """Nomes físicos das coleções que receberam busca vetorial."""
    return {c["vector_store"]["collection_name"] for c in chamadas}


def documento_do_banco(colecao_id: str, nome_arquivo: str) -> Any:
    from sqlalchemy import select

    from src.app.models import DocumentoColecao

    with sessao_do_banco() as sessao:
        linha = sessao.execute(
            select(DocumentoColecao).where(
                DocumentoColecao.colecao_id == colecao_id,
                DocumentoColecao.nome_arquivo == nome_arquivo,
            )
        ).scalar_one()
        sessao.expunge(linha)
        return linha


def workspace_da_colecao(colecao_id: str) -> str:
    from src.app.models import Colecao

    with sessao_do_banco() as sessao:
        return sessao.get(Colecao, colecao_id).workspace_id


def criar_envio_no_banco(colecao_id: str, **campos: Any) -> str:
    from src.app.models import Envio

    valores: dict[str, Any] = {
        "arquivos": ["contrato.md"],
        "processamento": {},
        "situacao": "succeeded",
        "etapa": "concluido",
    }
    valores.update(campos)
    with sessao_do_banco() as sessao:
        envio = Envio(colecao_id=colecao_id, **valores)
        sessao.add(envio)
        sessao.commit()
        return envio.id


def conteudos_do_banco(colecao_id: str) -> list[Any]:
    """Linhas de ``ConteudoDocumento`` da coleção, reprovando se o modelo não existe."""
    from sqlalchemy import select

    from src.app.models import DocumentoColecao

    modelo = exigir_copilot("src.app.models", "ConteudoDocumento")
    with sessao_do_banco() as sessao:
        consulta = (
            select(modelo)
            .join(DocumentoColecao, DocumentoColecao.id == modelo.documento_id)
            .where(DocumentoColecao.colecao_id == colecao_id)
        )
        linhas = list(sessao.execute(consulta).scalars().all())
        for linha in linhas:
            sessao.expunge(linha)
        return linhas


def gravar_conteudo(
    colecao_id: str,
    nome_arquivo: str,
    *,
    texto: str,
    trechos: list[dict[str, Any]],
    envio_id: str | None = None,
) -> None:
    """Grava ``ConteudoDocumento`` direto no banco para o documento já registrado."""
    modelo = exigir_copilot("src.app.models", "ConteudoDocumento")
    documento = documento_do_banco(colecao_id, nome_arquivo)
    envio_id = envio_id or criar_envio_no_banco(colecao_id)
    with sessao_do_banco() as sessao:
        sessao.add(
            modelo(
                documento_id=documento.id,
                texto=texto,
                trechos=trechos,
                envio_id=envio_id,
                truncado=False,
            )
        )
        sessao.commit()


__all__ = [
    "CLASSIFICAR",
    "TUDO",
    "ModeloCopilot",
    "cliente",
    "consultadas",
    "conteudos_do_banco",
    "criar_envio_no_banco",
    "documento_do_banco",
    "exigir_copilot",
    "gravar_conteudo",
    "perguntar",
    "preparar_copilot",
    "workspace_da_colecao",
]
