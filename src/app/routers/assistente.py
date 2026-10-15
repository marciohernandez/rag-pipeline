"""Endpoints do assistente especialista em RAG (SPEC-0021).

Conversas pertencem à pessoa autenticada: qualquer outra pessoa, mesmo owner ou
admin, recebe o mesmo 404. O assistente apenas orienta; este módulo só escreve
nas tabelas do assistente. O par pergunta e resposta só é gravado quando a
resposta existe, e o log do turno nunca carrega conteúdo nem segredo.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator

import src.pipeline.service as service  # noqa: PLR0402 — forma exigida pelo teste de fronteira
from src.app import assistente_contexto, repo
from src.app.auth import Identity, get_identity
from src.app.db import SessionLocal
from src.app.models import ConversaAssistente, MensagemAssistente
from src.app.settings import get_settings

router = APIRouter(prefix="/api/v1/assistente", tags=["assistente"])
logger = logging.getLogger("src.app.assistente")

LIMITE_DA_MENSAGEM = 4000
_TITULO_PADRAO = "Nova conversa"
_TAMANHO_DO_TITULO = 60
_ERRO_GENERICO = "Não foi possível obter a resposta do assistente no momento."
_PROJETO_DO_CONHECIMENTO = "assistente-conhecimento"


class MensagemRequest(BaseModel):
    texto: str = Field(min_length=1, max_length=LIMITE_DA_MENSAGEM)
    colecao_id: str | None = None

    @field_validator("texto")
    @classmethod
    def _nao_vazio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("A mensagem não pode ser vazia.")
        return valor


def _mensagem(mensagem: MensagemAssistente) -> dict[str, Any]:
    return {
        "id": mensagem.id,
        "papel": mensagem.papel,
        "conteudo": mensagem.conteudo,
        "fontes": list(mensagem.fontes or []),
        # A coluna ainda se chama base_id (tabela anterior à SPEC-0030); guarda a coleção.
        "colecao_id": mensagem.base_id,
        "criada_em": mensagem.criada_em.isoformat(),
    }


@router.get("/conversas")
def listar_conversas(identity: Identity = Depends(get_identity)) -> list[dict]:  # noqa: B008
    with SessionLocal() as session:
        return [
            {
                "id": conversa.id,
                "titulo": conversa.titulo,
                "atualizada_em": conversa.atualizada_em.isoformat(),
            }
            for conversa in repo.list_conversas_da_pessoa(session, identity)
        ]


@router.post("/conversas", status_code=201)
def criar_conversa(identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    with SessionLocal() as session:
        conversa = ConversaAssistente(
            tenant_id=identity.tenant_id,
            project_id=identity.project_id,
            pessoa_id=identity.person_id,
            titulo=_TITULO_PADRAO,
        )
        session.add(conversa)
        session.commit()
        return {"id": conversa.id, "titulo": conversa.titulo}


@router.get("/conversas/{conversa_id}")
def obter_conversa(
    conversa_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    with SessionLocal() as session:
        conversa = repo.get_conversa_or_404(session, conversa_id, identity)
        return {
            "id": conversa.id,
            "titulo": conversa.titulo,
            "mensagens": [_mensagem(m) for m in conversa.mensagens],
        }


@router.delete("/conversas/{conversa_id}", status_code=204)
def apagar_conversa(
    conversa_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> Response:
    with SessionLocal() as session:
        conversa = repo.get_conversa_or_404(session, conversa_id, identity)
        session.delete(conversa)
        session.commit()
    return Response(status_code=204)


def _configuracao_da_colecao(colecao: str, projeto: str) -> dict[str, Any]:
    configuracao = get_settings()
    return {
        "projeto": {"nome": projeto},
        "caminhos": {},
        "embedding": dict(configuracao.embedding),
        "vector_store": {**configuracao.vector_store, "collection_name": colecao},
    }


def _colecao_apontada(session, colecao_id: str, identity: Identity) -> dict[str, Any]:
    colecao = repo.get_colecao_or_404(session, colecao_id, identity)
    documentos = repo.list_documentos_da_colecao(session, colecao.id)
    if not documentos:
        raise HTTPException(
            status_code=409, detail="Esta coleção ainda não tem documentos indexados."
        )
    return {"nome": colecao.nome, "documentos": [d.nome_arquivo for d in documentos]}


def _registrar_turno(identity: Identity, conversa_id: str, com_base: bool, inicio: float, ok: bool):
    logger.info(
        "assistente_turno pessoa_id=%s conversa_id=%s com_base=%s duracao_ms=%d resultado=%s",
        identity.person_id,
        conversa_id,
        "sim" if com_base else "nao",
        int((time.monotonic() - inicio) * 1000),
        "ok" if ok else "erro",
    )


@router.post("/conversas/{conversa_id}/mensagens", status_code=201)
def enviar_mensagem(
    conversa_id: str,
    corpo: MensagemRequest,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    with SessionLocal() as session:
        conversa = repo.get_conversa_or_404(session, conversa_id, identity)
        base = (
            _colecao_apontada(session, corpo.colecao_id, identity)
            if corpo.colecao_id is not None
            else None
        )
        primeira_mensagem = not conversa.mensagens
        # Cópias simples: a chamada ao modelo acontece fora da sessão do banco.
        historico = [
            SimpleNamespace(papel=m.papel, conteudo=m.conteudo)
            for m in repo.list_mensagens_recentes(session, conversa.id)
        ]

    configuracao = get_settings()
    contexto = assistente_contexto.criar_contexto(identity, corpo.colecao_id)
    inicio = time.monotonic()
    try:
        resposta = service.assistant_reply(
            llm_config=configuracao.llm,
            knowledge_config=_configuracao_da_colecao(
                configuracao.conhecimento_collection, _PROJETO_DO_CONHECIMENTO
            ),
            historico=historico,
            texto=corpo.texto,
            colecoes=contexto.colecoes,
            estado=contexto.estado,
            processado=contexto.processado,
        )
    except service.AssistantError as erro:
        _registrar_turno(identity, conversa_id, base is not None, inicio, ok=False)
        raise HTTPException(status_code=502, detail=_ERRO_GENERICO) from erro

    agora = datetime.now(UTC)
    with SessionLocal() as session:
        conversa = repo.get_conversa_or_404(session, conversa_id, identity)
        da_pessoa = MensagemAssistente(
            conversa_id=conversa.id,
            papel="pessoa",
            conteudo=corpo.texto,
            base_id=corpo.colecao_id,
            fontes=[],
            criada_em=agora,
        )
        do_assistente = MensagemAssistente(
            conversa_id=conversa.id,
            papel="assistente",
            conteudo=resposta.texto,
            base_id=None,
            fontes=list(resposta.fontes),
            criada_em=agora + timedelta(milliseconds=1),
        )
        session.add_all([da_pessoa, do_assistente])
        if primeira_mensagem:
            conversa.titulo = corpo.texto.strip()[:_TAMANHO_DO_TITULO]
        conversa.atualizada_em = do_assistente.criada_em
        session.commit()
        resultado = {
            "mensagem_pessoa": _mensagem(da_pessoa),
            "mensagem_assistente": _mensagem(do_assistente),
        }
    _registrar_turno(identity, conversa_id, base is not None, inicio, ok=True)
    return resultado
