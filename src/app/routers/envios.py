"""Envios de documentos para coleções (SPEC-0030, US-001 e US-002)."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from src.app import colecoes, ingestao, origem_lote, publicacao, repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import Envio
from src.app.routers.comum import autor_json, metadados_do_upload, workspace_do_upload
from src.app.storage import get_storage

router = APIRouter(prefix="/api/v1", tags=["envios"])
logger = logging.getLogger(__name__)


def _agora() -> datetime:
    return datetime.now(UTC)


def serializar_envio(envio: Envio) -> dict:
    return {
        "id": envio.id,
        "colecao_id": envio.colecao_id,
        "arquivos": list(envio.arquivos or []),
        "processamento": envio.processamento,
        "situacao": envio.situacao,
        "etapa": envio.etapa,
        "previstos": envio.previstos,
        "inseridos": envio.inseridos,
        "mantidos": envio.mantidos,
        "removidos": envio.removidos,
        "erro": envio.erro,
        "iniciado_em": envio.iniciado_em.isoformat(),
        "concluido_em": envio.concluido_em.isoformat() if envio.concluido_em else None,
        "criado_por": autor_json(envio),
    }


def _processamento_do_envio(
    splitter: str, chunk_size: int, chunk_overlap: int, bruto: str | None
) -> dict:
    """Valida a divisão e devolve o que o envio guarda, sem `sync_mode` (FR-006, FR-007)."""
    processamento = ingestao.ler_processamento(bruto)
    if "sync_mode" in (processamento.get("destino") or {}):
        raise HTTPException(status_code=422, detail=colecoes.MSG_SYNC_MODE)
    escolhas = ingestao.validar_parametros_divisao(
        splitter, chunk_size, chunk_overlap, processamento
    )
    escolhas["destino"].pop("sync_mode", None)
    return {
        "splitter": splitter,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        **escolhas,
    }


@router.post("/envios", status_code=201)
async def criar_envio(
    arquivos: list[UploadFile] | None = None,
    workspace_id: str | None = Form(None),
    colecao_id: str | None = Form(None),
    nova_colecao: str | None = Form(None),
    usar_base_preparada: bool = Form(False),
    lote_id: str | None = Form(None),
    documento_ids: list[str] | None = Form(None),  # noqa: B008
    conexao_embeddings_id: str | None = Form(None),
    conexao_vector_store_id: str | None = Form(None),
    metadados_chunk: str | None = Form(None),
    splitter: str = Form(ingestao.PADROES["splitter"]),
    chunk_size: int = Form(ingestao.PADROES["chunk_size"]),
    chunk_overlap: int = Form(ingestao.PADROES["chunk_overlap"]),
    processamento: str | None = Form(None),
    sync_mode: str | None = Form(None),
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    if sync_mode is not None:
        raise HTTPException(status_code=422, detail=colecoes.MSG_SYNC_MODE)
    if bool(colecao_id) == bool(nova_colecao):
        raise HTTPException(
            status_code=422, detail="Informe uma coleção existente ou o nome de uma nova coleção."
        )
    with SessionLocal() as session:
        workspace = workspace_do_upload(session, workspace_id, identity)
        workspace_id_validado = workspace.id
    origem_lote.exigir_uma_origem(bool(arquivos), usar_base_preparada, lote_id)
    mapa_origem: dict | None = None
    if lote_id:
        with SessionLocal() as session:
            lidos = origem_lote.ler_documentos_lote(
                session, identity, lote_id, documento_ids or [], workspace_id=workspace_id_validado
            )
        conteudos = [(item.nome, item.dados) for item in lidos]
        mapa_origem = origem_lote.mapa_de_origem(lote_id, lidos)
    elif usar_base_preparada:
        conteudos = ingestao.ler_base_preparada()
    else:
        conteudos = await ingestao.ler_arquivos_markdown(arquivos or [])
    nomes = [nome for nome, _ in conteudos]
    if len(nomes) != len(set(nomes)):
        raise HTTPException(status_code=422, detail="Há arquivos com o mesmo nome neste envio.")
    metadados = metadados_do_upload(metadados_chunk)
    guardado = _processamento_do_envio(splitter, chunk_size, chunk_overlap, processamento)
    if mapa_origem is not None:
        guardado[origem_lote.CHAVE_ORIGEM] = mapa_origem

    envio_id = str(uuid.uuid4())
    storage = get_storage()
    with SessionLocal() as session:
        try:
            if colecao_id:
                try:
                    colecao = repo.get_colecao_or_404(session, colecao_id, identity)
                except HTTPException:
                    raise HTTPException(
                        status_code=404, detail="A coleção não existe mais."
                    ) from None
                if colecao.workspace_id != workspace_id_validado:
                    raise HTTPException(status_code=404, detail="A coleção não existe mais.")
                colecoes.exigir_envio_possivel(
                    session, identity, colecao, conexao_embeddings_id, conexao_vector_store_id
                )
            else:
                colecao = colecoes.criar_colecao(
                    session,
                    identity,
                    workspace,
                    nova_colecao or "",
                    conexao_embeddings_id,
                    conexao_vector_store_id,
                )
                colecoes.exigir_envio_possivel(session, identity, colecao, None, None)
            for nome, dados in conteudos:
                storage.save(envio_id, nome, dados)
            session.add(
                Envio(
                    id=envio_id,
                    colecao_id=colecao.id,
                    arquivos=nomes,
                    processamento=guardado,
                    metadados_chunk=metadados,
                    situacao="queued",
                    criado_por=identity.person_id,
                )
            )
            session.commit()
            colecao_id_final = colecao.id
        except Exception:
            session.rollback()
            storage.delete_base(envio_id)
            raise
    try:
        publicacao.agendar_envio(envio_id, colecao_id_final)
    except Exception as exc:  # noqa: BLE001 — qualquer falha da fila exige compensação segura
        logger.warning("Falha ao enfileirar envio (%s).", type(exc).__name__)
        try:
            publicacao.compensar_envio(envio_id, colecao_id_final, colecao_nova=not colecao_id)
        except Exception as erro_compensacao:  # noqa: BLE001 — mantém o erro público sem segredos
            logger.warning(
                "Falha ao compensar envio após enfileirar (%s).",
                type(erro_compensacao).__name__,
            )
        raise HTTPException(
            status_code=503, detail="Não foi possível iniciar o envio. Tente novamente."
        ) from None
    return {"envio_id": envio_id, "colecao_id": colecao_id_final}


@router.get("/envios/{envio_id}")
def obter_envio(envio_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    with SessionLocal() as session:
        envio = repo.get_envio_or_404(session, envio_id, identity)
        colecao = repo.get_colecao_or_404(session, envio.colecao_id, identity)
        return {
            **serializar_envio(envio),
            "colecao": {
                "id": colecao.id,
                "nome": colecao.nome,
                "workspace_id": colecao.workspace_id,
            },
        }


@router.post("/envios/{envio_id}/retry", status_code=202)
def repetir_envio(envio_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    require_write_role(identity)
    with SessionLocal() as session:
        envio = repo.get_envio_or_404(session, envio_id, identity)
        if envio.situacao != "failed":
            raise HTTPException(
                status_code=409, detail="Só é possível repetir um envio que falhou."
            )
        colecao = repo.get_colecao_or_404(session, envio.colecao_id, identity)
        colecoes.exigir_envio_possivel(session, identity, colecao, None, None)
        envio.situacao = "queued"
        envio.etapa = ""
        envio.erro = None
        envio.concluido_em = None
        envio.iniciado_em = _agora()
        colecao_id = colecao.id
        session.commit()
    publicacao.agendar_envio(envio_id, colecao_id)
    return {"envio_id": envio_id, "situacao": "queued"}
