"""Rotas da decisão da empresa: resposta, propostas, versões e liberação (SPEC-0039)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.app import decisoes, repo, tasks
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import DecisaoEmpresa, PropostaCorrecao, RespostaEmpresa, VersaoDocumento

router = APIRouter(prefix="/api/v1", tags=["decisoes"])


class RespostaInput(BaseModel):
    texto: str = ""
    confirmado: bool = False
    manual: bool = False


class ConfirmacaoInput(BaseModel):
    confirmado: bool = False


class DecisaoInput(BaseModel):
    acao: str
    arquivo: str | None = None
    trecho_alvo: str | None = None
    texto_corrigido: str | None = None


def _iso(valor) -> str | None:
    return valor.isoformat() if valor else None


def _erro(erro: decisoes.ErroDeDecisao) -> HTTPException:
    return HTTPException(status_code=erro.status, detail=erro.mensagem)


def _resposta(resposta: RespostaEmpresa) -> dict[str, Any]:
    return {
        "id": resposta.id,
        "situacao": resposta.situacao,
        "motivo": resposta.motivo,
        "criado_em": _iso(resposta.criado_em),
    }


def _proposta(proposta: PropostaCorrecao) -> dict[str, Any]:
    return {
        "id": proposta.id,
        "ocorrencia_id": proposta.ocorrencia_id,
        "situacao": proposta.situacao,
        "arquivo": proposta.arquivo,
        "documento_id": proposta.documento_id,
        "trecho_alvo": proposta.trecho_alvo,
        "texto_corrigido": proposta.texto_corrigido,
        "motivo": proposta.motivo,
    }


def _versao(versao: VersaoDocumento) -> dict[str, Any]:
    return {
        "numero": versao.numero,
        "hash": versao.hash,
        "criado_em": _iso(versao.criado_em),
        "expira_em": _iso(versao.expira_em),
        "atual": versao.expira_em is None,
    }


def _registro(item: DecisaoEmpresa) -> dict[str, Any]:
    return {
        "id": item.id,
        "confirmado_por": item.confirmado_por,
        "confirmado_em": _iso(item.confirmado_em),
        "ocorrencia_id": item.ocorrencia_id,
        "arquivo": item.arquivo,
        "resposta_trecho": item.resposta_trecho,
        "proposta": item.texto_proposto,
        "texto_aplicado": item.texto_aplicado,
        "editada": item.editada,
        "versao": item.versao_resultante,
        "restaurada_de": item.restaurada_de,
    }


@router.post("/colecoes/{colecao_id}/decisoes/respostas")
def colar_resposta(
    colecao_id: str,
    payload: RespostaInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
):
    require_write_role(identity)
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        try:
            resposta = decisoes.registrar_resposta(
                session,
                colecao,
                identity.person_id,
                payload.texto,
                payload.confirmado,
                payload.manual,
            )
        except decisoes.ErroDeDecisao as erro:
            raise _erro(erro) from erro
        corpo = _resposta(resposta)
    if payload.manual:
        return JSONResponse(corpo, status_code=201)
    tasks.interpretar_resposta_task.defer(resposta_id=corpo["id"])
    return JSONResponse(corpo, status_code=202)


@router.get("/colecoes/{colecao_id}/decisoes/propostas")
def listar_propostas(
    colecao_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        resposta = decisoes.resposta_atual(session, colecao.id)
        if resposta is None:
            return {"resposta": None, "propostas": []}
        return {
            "resposta": _resposta(resposta),
            "propostas": [
                _proposta(p) for p in decisoes.propostas_da_resposta(session, resposta.id)
            ],
        }


@router.post("/colecoes/{colecao_id}/decisoes/propostas/confirmar")
def confirmar_claras(
    colecao_id: str,
    payload: ConfirmacaoInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        try:
            aplicadas = decisoes.aplicar_lote(
                session, colecao, identity.person_id, payload.confirmado
            )
        except decisoes.ErroDeDecisao as erro:
            raise _erro(erro) from erro
    return {"aplicadas": aplicadas}


@router.post("/colecoes/{colecao_id}/decisoes/propostas/{proposta_id}/decisao")
def decidir_proposta(
    colecao_id: str,
    proposta_id: str,
    payload: DecisaoInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        try:
            proposta = decisoes.decidir(
                session,
                colecao,
                identity.person_id,
                proposta_id,
                payload.acao,
                payload.model_dump(exclude={"acao"}),
            )
        except decisoes.ErroDeDecisao as erro:
            raise _erro(erro) from erro
        return _proposta(proposta)


@router.get("/colecoes/{colecao_id}/decisoes/registro")
def registro(
    colecao_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        itens = (
            session.query(DecisaoEmpresa)
            .filter_by(colecao_id=colecao.id)
            .order_by(DecisaoEmpresa.confirmado_em)
            .all()
        )
        return [_registro(i) for i in itens]


@router.get("/colecoes/{colecao_id}/decisoes/rodada")
def rodada(
    colecao_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        return {
            **decisoes.resumo_da_rodada(session, colecao.id),
            "revisada_em": _iso(colecao.revisada_em),
        }


@router.get("/colecoes/{colecao_id}/documentos/{documento_id}/versoes")
def listar_versoes(
    colecao_id: str,
    documento_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        try:
            return [
                _versao(v) for v in decisoes.versoes_do_documento(session, colecao, documento_id)
            ]
        except decisoes.ErroDeDecisao as erro:
            raise _erro(erro) from erro


@router.post("/colecoes/{colecao_id}/documentos/{documento_id}/versoes/{numero}/restaurar")
def restaurar(
    colecao_id: str,
    documento_id: str,
    numero: int,
    payload: ConfirmacaoInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        try:
            nova = decisoes.restaurar_versao(
                session, colecao, identity.person_id, documento_id, numero, payload.confirmado
            )
        except decisoes.ErroDeDecisao as erro:
            raise _erro(erro) from erro
    return {"versao": nova}


@router.post("/colecoes/{colecao_id}/revisar")
def revisar(
    colecao_id: str,
    payload: ConfirmacaoInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
):
    require_write_role(identity)
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        try:
            return decisoes.revisar(session, colecao, identity.person_id, payload.confirmado)
        except decisoes.ErroDeDecisao as erro:
            corpo = {"detail": erro.mensagem, **erro.extra}
            return JSONResponse(corpo, status_code=erro.status)
