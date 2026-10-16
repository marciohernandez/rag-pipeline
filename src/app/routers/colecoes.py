"""Coleções por Workspace: leitura, documentos e envios (SPEC-0030)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, select

from src.app import colecoes, contradicoes, repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import Conexao, DocumentoColecao, Envio
from src.app.models import Query as ConsultaSalva
from src.app.routers.comum import autor_json
from src.app.routers.envios import serializar_envio
from src.app.storage import get_storage

router = APIRouter(prefix="/api/v1", tags=["colecoes"])


def _iso(valor) -> str | None:
    return valor.isoformat() if valor is not None else None


@router.get("/colecoes")
def listar_colecoes_do_projeto(
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    """Coleções de todos os Workspaces do projeto, para a escolha do assistente."""
    with SessionLocal() as session:
        itens = []
        for workspace in repo.list_workspaces_for_identity(session, identity):
            for item in repo.list_colecoes_for_workspace(session, identity, workspace.id):
                itens.append(
                    {
                        "id": item["colecao"].id,
                        "nome": item["colecao"].nome,
                        "workspace_id": workspace.id,
                        "workspace_nome": workspace.nome,
                        "documentos": item["documentos"],
                    }
                )
        return itens


@router.get("/workspaces/{workspace_id}/colecoes")
def listar_colecoes(
    workspace_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    with SessionLocal() as session:
        repo.get_workspace_or_404(session, workspace_id, identity)
        return [
            {
                "id": item["colecao"].id,
                "nome": item["colecao"].nome,
                "documentos": item["documentos"],
                "chunks": item["chunks"],
                "ultimo_envio_em": _iso(item["ultimo_envio_em"]),
            }
            for item in repo.list_colecoes_for_workspace(session, identity, workspace_id)
        ]


@router.get("/colecoes/{colecao_id}")
def obter_colecao(colecao_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        documentos = repo.list_documentos_da_colecao(session, colecao.id)
        embeddings = session.get(Conexao, colecao.conexao_embeddings_id)
        vector_store = session.get(Conexao, colecao.conexao_vector_store_id)
        return {
            "id": colecao.id,
            "nome": colecao.nome,
            "workspace_id": colecao.workspace_id,
            "workspace_nome": colecao.workspace.nome,
            "dimensao": colecao.dimensao,
            "conexao_embeddings": {
                "id": colecao.conexao_embeddings_id,
                "nome": embeddings.nome if embeddings else "",
            },
            "conexao_vector_store": {
                "id": colecao.conexao_vector_store_id,
                "nome": vector_store.nome if vector_store else "",
            },
            "documentos": len(documentos),
            "chunks": sum(documento.chunks for documento in documentos),
            "criado_em": colecao.criado_em.isoformat(),
            "criado_por": autor_json(colecao),
        }


@router.get("/colecoes/{colecao_id}/documentos")
def listar_documentos(
    colecao_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        return [
            {
                "id": documento.id,
                "nome_arquivo": documento.nome_arquivo,
                "chunks": documento.chunks,
                "chunking": documento.chunking,
                "ultimo_envio_em": _iso(documento.atualizado_em),
            }
            for documento in repo.list_documentos_da_colecao(session, colecao.id)
        ]


@router.get("/colecoes/{colecao_id}/envios")
def listar_envios(
    colecao_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        return [
            serializar_envio(envio) for envio in repo.list_envios_da_colecao(session, colecao.id)
        ]


MSG_ENVIO_ATIVO = "Há um envio em processamento nesta coleção. Aguarde a conclusão para apagar."


class RenomearRequest(BaseModel):
    nome: str


class ApagarColecaoRequest(BaseModel):
    confirmacao_nome: str = ""


class ConsultaColecaoRequest(BaseModel):
    pergunta: str
    top_k: int = Field(4, ge=1, le=50)


def _registrar_recusa(operacao: str, erro: Exception) -> None:
    """Loga só o tipo da exceção: o detalhe do provedor pode conter endpoint ou chave."""
    logging.getLogger(__name__).error("%s recusada pelo destino: %s", operacao, type(erro).__name__)


@router.patch("/colecoes/{colecao_id}")
def renomear_colecao(
    colecao_id: str,
    corpo: RenomearRequest,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        exibido, normalizado = colecoes.normalizar_nome(corpo.nome)
        colecoes.exigir_nome_livre(session, colecao.workspace_id, normalizado, colecao.id)
        colecao.nome = exibido
        colecao.nome_normalizado = normalizado
        session.commit()
        return {"id": colecao.id, "nome": colecao.nome}


@router.get("/colecoes/{colecao_id}/documentos/{documento_id}/chunks")
def listar_chunks_do_documento(
    colecao_id: str,
    documento_id: str,
    limite: int = Query(200, ge=1, le=200),
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira

    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        documento = session.get(DocumentoColecao, documento_id)
        if documento is None or documento.colecao_id != colecao.id:
            raise HTTPException(status_code=404, detail="Documento não encontrado.")
        config = colecoes.configuracao_da_colecao(session, identity, colecao)
        document_id = documento.document_id
    try:
        return service.list_document_chunks(config, document_id, limite)
    except Exception as erro:
        _registrar_recusa("leitura dos chunks", erro)
        raise HTTPException(
            status_code=502, detail="Não foi possível ler os chunks do documento no momento."
        ) from erro


@router.delete("/colecoes/{colecao_id}/documentos/{documento_id}", status_code=204)
def apagar_documento(
    colecao_id: str,
    documento_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> None:
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira

    require_write_role(identity)
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        documento = session.get(DocumentoColecao, documento_id)
        if documento is None or documento.colecao_id != colecao.id:
            raise HTTPException(status_code=404, detail="Documento não encontrado.")
        if repo.has_envio_ativo(session, colecao.id):
            raise HTTPException(status_code=409, detail=MSG_ENVIO_ATIVO)
        config = colecoes.configuracao_da_colecao(session, identity, colecao)
        document_id = documento.document_id
    try:
        service.delete_scope(config, document_id=document_id)
    except Exception as erro:
        _registrar_recusa("exclusão do documento", erro)
        raise HTTPException(
            status_code=502, detail="Não foi possível apagar o documento. Tente novamente."
        ) from erro
    with SessionLocal() as session:
        documento = session.get(DocumentoColecao, documento_id)
        if documento is not None:
            repo.apagar_conteudo_do_documento(session, documento.id)
            session.delete(documento)
            session.commit()


@router.delete("/colecoes/{colecao_id}", status_code=204)
def apagar_colecao(
    colecao_id: str,
    corpo: ApagarColecaoRequest | None = None,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> None:
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira

    require_write_role(identity)
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        if (corpo.confirmacao_nome if corpo else "").strip() != colecao.nome:
            raise HTTPException(
                status_code=422, detail="Digite o nome da coleção para confirmar a exclusão."
            )
        if repo.has_envio_ativo(session, colecao.id):
            raise HTTPException(status_code=409, detail=MSG_ENVIO_ATIVO)
        config = colecoes.configuracao_da_colecao(session, identity, colecao)
        nome_fisico = colecao.nome_fisico
    # O Qdrant confirma primeiro: só então os registros locais saem (NFR-004).
    try:
        service.drop_collection(config, registradas=[nome_fisico])
    except Exception as erro:
        _registrar_recusa("exclusão da coleção", erro)
        raise HTTPException(
            status_code=502, detail="Não foi possível apagar a coleção. Tente novamente."
        ) from erro
    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        envios = session.execute(select(Envio.id).where(Envio.colecao_id == colecao.id)).scalars()
        envio_ids = list(envios)
        storage = get_storage()
        for envio_id in envio_ids:
            storage.delete_base(envio_id)
        session.execute(delete(ConsultaSalva).where(ConsultaSalva.colecao_id == colecao.id))
        repo.apagar_conteudos_da_colecao(session, colecao.id)
        contradicoes.apagar_da_colecao(session, colecao.id)
        session.execute(delete(DocumentoColecao).where(DocumentoColecao.colecao_id == colecao.id))
        session.execute(delete(Envio).where(Envio.colecao_id == colecao.id))
        colecao.apagada_em = datetime.now(UTC)
        session.commit()


@router.post("/colecoes/{colecao_id}/query")
def consultar_colecao(
    colecao_id: str,
    corpo: ConsultaColecaoRequest,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira

    with SessionLocal() as session:
        colecao = repo.get_colecao_or_404(session, colecao_id, identity)
        if not repo.list_documentos_da_colecao(session, colecao.id):
            raise HTTPException(
                status_code=409, detail="Esta coleção ainda não tem documentos indexados."
            )
        config = colecoes.configuracao_da_colecao(session, identity, colecao)
        colecao_id_validado = colecao.id
    try:
        resultados = list(service.query_base(config, corpo.pergunta, top_k=corpo.top_k) or [])
    except Exception as erro:
        # Nunca repassar o detalhe do provedor ao cliente (NFR-001).
        _registrar_recusa("consulta", erro)
        raise HTTPException(
            status_code=502, detail="Não foi possível consultar a coleção no momento."
        ) from erro
    chunks_fontes = [
        {
            "documento": resultado.metadata.get("nome_arquivo")
            or resultado.metadata.get("document_id"),
            "trecho": resultado.content,
        }
        for resultado in resultados
    ]
    resposta = {
        "resultado": resultados[0].content if resultados else "",
        "chunks_fontes": chunks_fontes,
        "criado_por": {"id": identity.person_id, "nome": identity.nome, "desativada": False},
    }
    with SessionLocal() as session:
        session.add(
            ConsultaSalva(
                colecao_id=colecao_id_validado,
                tenant_id=identity.tenant_id,
                project_id=identity.project_id,
                pergunta=corpo.pergunta,
                resultado=resposta["resultado"],
                chunks_fontes=chunks_fontes,
                criado_por=identity.person_id,
            )
        )
        session.commit()
    return resposta
