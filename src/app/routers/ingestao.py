"""Padrões, prévia descartável e verificação de dimensão da ingestão (SPEC-0026)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile

from src.app import conexoes, ingestao, publicacao
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal

router = APIRouter(prefix="/api/v1/ingestao", tags=["ingestao"])

TAMANHO_PAGINA_MAXIMO = 100
logger = logging.getLogger(__name__)


@router.get("/padroes")
def padroes(identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    require_write_role(identity)
    return {
        **ingestao.PADROES,
        "splitters": list(ingestao.SPLITTERS),
        "limites": ingestao.limites(),
    }


@router.post("/previa")
async def previa(
    arquivos: list[UploadFile] | None = None,
    usar_base_preparada: bool = Form(False),
    splitter: str = Form(ingestao.PADROES["splitter"]),
    chunk_size: int = Form(ingestao.PADROES["chunk_size"]),
    chunk_overlap: int = Form(ingestao.PADROES["chunk_overlap"]),
    pagina: int = Form(1),
    tamanho_pagina: int = Form(20),
    documento: str | None = Form(None),
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    """Calcula os chunks sem persistir nada: nem storage, nem banco, nem vetores."""
    require_write_role(identity)
    ingestao.validar_parametros_divisao(splitter, chunk_size, chunk_overlap)
    if pagina < 1 or not 1 <= tamanho_pagina <= TAMANHO_PAGINA_MAXIMO:
        raise HTTPException(status_code=422, detail="Paginação inválida.")
    if usar_base_preparada:
        conteudos = ingestao.ler_base_preparada()
    else:
        conteudos = await ingestao.ler_arquivos_markdown(arquivos or [])
    try:
        return ingestao.calcular_previa(
            conteudos,
            ingestao.montar_chunking(splitter, chunk_size, chunk_overlap),
            pagina=pagina,
            tamanho_pagina=tamanho_pagina,
            documento=documento or None,
        )
    except Exception as erro:
        logger.warning("falha ao calcular a prévia: %s", type(erro).__name__)
        raise HTTPException(
            status_code=422, detail="Não foi possível dividir os arquivos com estes parâmetros."
        ) from erro


@router.get("/dimensao")
def dimensao(
    conexao_embeddings_id: str = Query(...),
    conexao_vector_store_id: str = Query(...),
    collection_name: str = Query(..., min_length=1),
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    """Somente leitura: mostra as dimensões antes de publicar."""
    require_write_role(identity)
    with SessionLocal() as session:
        resolvidas = publicacao.resolver_conexoes(
            session, identity, conexao_embeddings_id, conexao_vector_store_id
        )
        try:
            return publicacao.verificar_dimensao(resolvidas, collection_name.strip())
        except conexoes.ErroDeConexao as erro:
            raise HTTPException(status_code=erro.status_code, detail=erro.detalhe) from erro
