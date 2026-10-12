"""Endpoints de conversão de documentos para Markdown (SPEC-0023, US-001/002/003/004)."""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile

from src.app import repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import DocumentoConversao, LoteConversao
from src.app.repo import recalcular_situacao_lote
from src.app.storage import get_storage
from src.app.tasks import process_conversion_document_task

router = APIRouter(prefix="/api/v1", tags=["conversao"])

MAX_ARQUIVOS = 50
MAX_BYTES_POR_ARQUIVO = 40 * 1024 * 1024
MAX_BYTES_TOTAL = 50 * 1024 * 1024
EXTENSOES_ACEITAS = {
    "pdf",
    "ppt",
    "pptx",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "jpg",
    "jpeg",
    "png",
}


def _autor(registro) -> dict | None:
    if registro.autor is None:
        return None
    return {
        "id": registro.autor.id,
        "nome": registro.autor.nome,
        "desativada": registro.autor.situacao != "ativa",
    }


def _serializar_documento(documento: DocumentoConversao) -> dict:
    return {
        "id": documento.id,
        "nome_arquivo": documento.nome_arquivo,
        "formato": documento.formato,
        "tamanho_bytes": documento.tamanho_bytes,
        "situacao": documento.situacao,
        "erro": documento.erro,
        "criado_em": documento.criado_em.isoformat(),
        "concluido_em": (
            documento.concluido_em.isoformat() if documento.concluido_em is not None else None
        ),
    }


def _serializar_lote(lote: LoteConversao, documentos: list[DocumentoConversao]) -> dict:
    return {
        "id": lote.id,
        "workspace_id": lote.workspace_id,
        "situacao": lote.situacao,
        "criado_em": lote.criado_em.isoformat(),
        "criado_por": _autor(lote),
        "documentos": [_serializar_documento(documento) for documento in documentos],
    }


def _workspace_do_envio(session, workspace_id: str | None, identity: Identity):
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Informe o Workspace do envio.")
    try:
        return repo.get_workspace_or_404(session, workspace_id, identity)
    except HTTPException as erro:
        if erro.status_code != 404:
            raise
        raise HTTPException(
            status_code=400, detail="Workspace inválido para este projeto."
        ) from None


def _markdown_do_documento(documento: DocumentoConversao, pasta: Path) -> Path:
    storage = get_storage()
    storage.materialize(documento.id, pasta)
    return pasta / f"{Path(documento.nome_arquivo).stem}.md"


@router.post("/conversoes", status_code=201)
async def enviar_conversoes(
    arquivos: list[UploadFile] | None = None,
    workspace_id: str | None = Form(None),
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    arquivos = arquivos or []

    with SessionLocal() as session:
        workspace = _workspace_do_envio(session, workspace_id, identity)
        workspace_id_validado = workspace.id

    if not arquivos:
        raise HTTPException(status_code=400, detail="Envie ao menos um arquivo.")
    if len(arquivos) > MAX_ARQUIVOS:
        raise HTTPException(
            status_code=400, detail=f"Limite de {MAX_ARQUIVOS} arquivos por lote excedido."
        )

    conteudos: list[tuple[str, str, bytes]] = []
    total = 0
    for arquivo in arquivos:
        dados = await arquivo.read()
        nome = Path(arquivo.filename or "").name
        extensao = Path(nome).suffix.lstrip(".").lower()
        if not nome or extensao not in EXTENSOES_ACEITAS:
            raise HTTPException(
                status_code=400, detail=f"Extensão não suportada: {nome or '(sem nome)'}."
            )
        if len(dados) > MAX_BYTES_POR_ARQUIVO:
            raise HTTPException(
                status_code=400, detail=f"Arquivo {nome} excede o limite de 40 MB por arquivo."
            )
        total += len(dados)
        if total > MAX_BYTES_TOTAL:
            raise HTTPException(status_code=400, detail="Limite de 50 MB por envio excedido.")
        conteudos.append((nome, extensao, dados))

    storage = get_storage()
    with SessionLocal() as session:
        lote = LoteConversao(
            tenant_id=identity.tenant_id,
            project_id=identity.project_id,
            workspace_id=workspace_id_validado,
            criado_por=identity.person_id,
            situacao="processando",
        )
        session.add(lote)
        session.flush()

        documentos: list[DocumentoConversao] = []
        for nome, extensao, dados in conteudos:
            documento = DocumentoConversao(
                lote_id=lote.id,
                nome_arquivo=nome,
                formato=extensao,
                tamanho_bytes=len(dados),
                situacao="fila",
            )
            session.add(documento)
            session.flush()
            storage.save(documento.id, nome, dados)
            documentos.append(documento)
        session.commit()
        resposta = _serializar_lote(lote, documentos)

    for documento in documentos:
        process_conversion_document_task.defer(documento_id=documento.id)

    return resposta


@router.get("/conversoes")
def listar_conversoes(
    workspace_id: str | None = None,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> list[dict]:
    with SessionLocal() as session:
        if workspace_id is not None:
            repo.get_workspace_or_404(session, workspace_id, identity)
        lotes = repo.list_lotes_for_identity(session, identity, workspace_id)
        return [_serializar_lote(lote, list(lote.documentos)) for lote in lotes]


@router.get("/conversoes/{lote_id}")
def obter_conversao(lote_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    with SessionLocal() as session:
        lote = repo.get_lote_or_404(session, lote_id, identity)
        return _serializar_lote(lote, list(lote.documentos))


@router.get("/conversoes/{lote_id}/documentos/{documento_id}/markdown")
def baixar_markdown(
    lote_id: str,
    documento_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> Response:
    with SessionLocal() as session:
        documento = repo.get_documento_or_404(session, lote_id, documento_id, identity)
        if documento.situacao != "concluido" or documento.apagado_em is not None:
            raise HTTPException(
                status_code=404,
                detail="Markdown indisponível; reenvie o documento original.",
            )
        nome_arquivo = documento.nome_arquivo

    with tempfile.TemporaryDirectory(prefix=f"conversao-{documento_id}-") as pasta_raw:
        pasta = Path(pasta_raw)
        storage = get_storage()
        storage.materialize(documento_id, pasta)
        nome_markdown = f"{Path(nome_arquivo).stem}.md"
        caminho_markdown = pasta / nome_markdown
        if not caminho_markdown.exists():
            raise HTTPException(
                status_code=404,
                detail="Markdown indisponível; reenvie o documento original.",
            )
        conteudo = caminho_markdown.read_bytes()

    return Response(
        content=conteudo,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{nome_markdown}"'},
    )


@router.get("/conversoes/{lote_id}/pacote")
def baixar_pacote(lote_id: str, identity: Identity = Depends(get_identity)) -> Response:  # noqa: B008
    with SessionLocal() as session:
        lote = repo.get_lote_or_404(session, lote_id, identity)
        documentos_concluidos = [
            documento
            for documento in lote.documentos
            if documento.situacao == "concluido" and documento.apagado_em is None
        ]

    storage = get_storage()
    buffer = io.BytesIO()
    with tempfile.TemporaryDirectory(prefix=f"pacote-{lote_id}-") as pasta_raw:
        pasta = Path(pasta_raw)
        with zipfile.ZipFile(buffer, "w") as arquivo_zip:
            for indice, documento in enumerate(documentos_concluidos):
                subpasta = pasta / str(indice)
                storage.materialize(documento.id, subpasta)
                nome_markdown = f"{Path(documento.nome_arquivo).stem}.md"
                caminho_markdown = subpasta / nome_markdown
                if caminho_markdown.exists():
                    arquivo_zip.write(caminho_markdown, arcname=nome_markdown)

    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="lote-{lote_id}.zip"'},
    )


@router.post("/conversoes/{lote_id}/documentos/{documento_id}/reenviar")
def reenviar_documento(
    lote_id: str,
    documento_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        documento = repo.get_documento_or_404(session, lote_id, documento_id, identity)
        if documento.situacao != "falhou" or documento.apagado_em is not None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Documento não está com falha ou já expirou; "
                    "envie o arquivo original novamente."
                ),
            )
        documento.situacao = "fila"
        documento.erro = None
        documento.expira_em = None
        documento.concluido_em = None
        recalcular_situacao_lote(session, documento.lote_id)
        session.commit()
        resposta = _serializar_documento(documento)

    process_conversion_document_task.defer(documento_id=documento_id)
    return resposta
