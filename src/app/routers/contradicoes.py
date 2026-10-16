"""Rotas da análise de contradições de uma coleção (SPEC-0038)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira
from src.app import contradicoes, repo, tasks
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import AnaliseContradicao, OcorrenciaContradicao

router = APIRouter(prefix="/api/v1", tags=["contradicoes"])


class IniciarAnaliseInput(BaseModel):
    confirmado: bool = False


def _iso(valor) -> str | None:
    return valor.isoformat() if valor else None


def _analise(analise: AnaliseContradicao) -> dict[str, Any]:
    progresso = analise.progresso or {}
    return {
        "id": analise.id,
        "situacao": analise.situacao,
        "motivo": analise.motivo,
        "provedor": analise.provedor,
        "dominio_versao_id": analise.dominio_versao_id,
        "total_assuntos": analise.total_assuntos,
        "concluidos": analise.concluidos,
        "documentos_analisados": analise.documentos_analisados,
        "avisos": progresso.get("avisos", []),
        "criado_em": _iso(analise.criado_em),
        "concluido_em": _iso(analise.concluido_em),
    }


def _ocorrencia(item: OcorrenciaContradicao) -> dict[str, Any]:
    return {
        "id": item.id,
        "assunto": item.assunto,
        "etiqueta": item.etiqueta,
        "impacto": item.impacto,
        "trechos": item.trechos,
        "explicacao": item.explicacao,
        "arquivo_mais_antigo": item.arquivo_mais_antigo,
    }


def _ultima(session, colecao_id: str) -> AnaliseContradicao | None:
    return (
        session.query(AnaliseContradicao)
        .filter_by(colecao_id=colecao_id)
        .order_by(AnaliseContradicao.criado_em.desc())
        .first()
    )


def _ocorrencias(session, analise_id: str, etiqueta: str | None = None):
    consulta = session.query(OcorrenciaContradicao).filter_by(analise_id=analise_id)
    if etiqueta:
        consulta = consulta.filter_by(etiqueta=etiqueta)
    itens = consulta.all()
    return sorted(itens, key=lambda o: (o.impacto != "alto", o.assunto.casefold()))


@router.post("/colecoes/{colecao_id}/contradicoes/analises", status_code=202)
def iniciar(
    colecao_id: str,
    payload: IniciarAnaliseInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        try:
            analise = contradicoes.iniciar_analise(
                session, colecao, identity.person_id, payload.confirmado
            )
        except contradicoes.ErroDeAnalise as erro:
            raise HTTPException(status_code=erro.status, detail=erro.mensagem) from erro
        resposta = _analise(analise)
    tasks.analisar_contradicoes_task.defer(analise_id=resposta["id"])
    return resposta


@router.post("/colecoes/{colecao_id}/contradicoes/analises/{analise_id}/continuar", status_code=202)
def continuar(
    colecao_id: str,
    analise_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        try:
            analise = contradicoes.continuar_analise(session, colecao, analise_id)
        except contradicoes.ErroDeAnalise as erro:
            raise HTTPException(status_code=erro.status, detail=erro.mensagem) from erro
        resposta = _analise(analise)
    tasks.analisar_contradicoes_task.defer(analise_id=analise_id)
    return resposta


@router.get("/colecoes/{colecao_id}/contradicoes")
def consultar(
    colecao_id: str,
    etiqueta: str | None = None,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        analise = _ultima(session, colecao.id)
        if analise is None:
            return {"analise": None, "ocorrencias": [], "nao_classificadas": 0}
        return {
            "analise": _analise(analise),
            "ocorrencias": [_ocorrencia(o) for o in _ocorrencias(session, analise.id, etiqueta)],
            "nao_classificadas": (analise.progresso or {}).get("nao_classificadas", 0),
        }


@router.get("/colecoes/{colecao_id}/contradicoes/relatorio")
def baixar(
    colecao_id: str,
    formato: str = "md",
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> Response:
    require_write_role(identity)
    if formato not in {"md", "pdf"}:
        raise HTTPException(status_code=422, detail="Formato inválido: use md ou pdf.")
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        analise = _ultima(session, colecao.id)
        if analise is None:
            raise HTTPException(status_code=404, detail="Nenhuma análise para baixar.")
        ocorrencias = [_ocorrencia(o) for o in _ocorrencias(session, analise.id)]
        resumo = _analise(analise)
        conteudo = service.montar_relatorio_contradicoes(resumo, ocorrencias, formato)
    if formato == "pdf":
        return Response(
            conteudo,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="contradicoes.pdf"'},
        )
    return Response(
        conteudo,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="contradicoes.md"'},
    )
