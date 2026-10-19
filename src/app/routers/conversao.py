"""Endpoints de conversão de documentos para Markdown (SPEC-0023, US-001/002/003/004)."""

from __future__ import annotations

import io
import tempfile
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel

from src.app import conversao_grupos, limpeza, repo
from src.app.auth import Identity, get_identity, require_write_role
from src.app.db import SessionLocal
from src.app.models import DocumentoConversao, ExclusaoLimpeza, LoteConversao, RelatorioLote
from src.app.repo import recalcular_situacao_lote
from src.app.storage import get_storage
from src.app.tasks import process_conversion_document_task

router = APIRouter(prefix="/api/v1", tags=["conversao"])

EXTENSOES_ACEITAS = {
    "html",
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


def _config_conversao():
    from types import SimpleNamespace

    from src.app.settings import get_settings
    from src.pipeline.service import validar_config_conversao

    return SimpleNamespace(**validar_config_conversao({"conversao": get_settings().conversao}))


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
        "avisos": documento.avisos or [],
        "origem_url": documento.origem_url,
        "reprocessando_ia": documento.situacao == "processando"
        and documento.concluido_em is not None,
        "abas": documento.abas_disponiveis,
        "abas_selecionadas": documento.abas_selecionadas,
        "reprocessado_ia_em": documento.reprocessado_ia_em.isoformat()
        if documento.reprocessado_ia_em
        else None,
        "limpeza_situacao": documento.limpeza_situacao,
        "exclusoes": documento.exclusoes or 0,
        "duvidas": documento.duvidas or 0,
        "limpeza_motivo": documento.limpeza_erro,
        "criado_em": documento.criado_em.isoformat(),
        "concluido_em": (
            documento.concluido_em.isoformat() if documento.concluido_em is not None else None
        ),
    }


def _resumo_limpeza(documentos: list[DocumentoConversao]) -> dict:
    com_limpeza = [d for d in documentos if d.limpeza_situacao is not None]
    return {
        "total": len(com_limpeza),
        "concluidos": sum(
            d.limpeza_situacao in ("limpo", "limpo_com_duvidas") for d in com_limpeza
        ),
        "falhas": sum(d.limpeza_situacao == "falhou" for d in com_limpeza),
    }


def _serializar_lote(lote: LoteConversao, documentos: list[DocumentoConversao]) -> dict:
    return {
        "id": lote.id,
        "workspace_id": lote.workspace_id,
        "situacao": lote.situacao,
        "criado_em": lote.criado_em.isoformat(),
        "criado_por": _autor(lote),
        "limpeza": _resumo_limpeza(documentos),
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
    urls: Annotated[list[str] | None, Form()] = None,
    metadados: Annotated[str | None, Form()] = None,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    arquivos = arquivos or []
    urls = urls or []

    with SessionLocal() as session:
        workspace = _workspace_do_envio(session, workspace_id, identity)
        workspace_id_validado = workspace.id

    if not arquivos and not urls:
        raise HTTPException(status_code=400, detail="Envie ao menos um arquivo.")
    config = _config_conversao()
    if len(arquivos) + len(urls) > config.max_arquivos:
        raise HTTPException(
            status_code=400, detail=f"Limite de {config.max_arquivos} arquivos por lote excedido."
        )

    conteudos: list[tuple[str, str, bytes]] = []
    recusados: list[dict[str, str]] = []
    total = 0
    for arquivo in arquivos:
        nome = Path(arquivo.filename or "").name
        extensao = Path(nome).suffix.lstrip(".").lower()
        dados = await arquivo.read(config.max_bytes_arquivo + 1)
        motivo = None
        if not nome or extensao not in EXTENSOES_ACEITAS:
            motivo = f"Extensão não suportada: {nome or '(sem nome)'}."
        elif len(dados) > config.max_bytes_arquivo:
            motivo = (
                f"Arquivo {nome} excede o limite de {config.max_bytes_arquivo} bytes "
                f"({config.max_bytes_arquivo / (1024 * 1024):g} MB) por arquivo."
            )
        elif total + len(dados) > config.max_bytes_lote:
            motivo = f"Arquivo {nome} excede o limite de {config.max_bytes_lote} bytes por lote."
        if motivo:
            recusados.append({"nome_arquivo": nome, "motivo": motivo})
            continue
        total += len(dados)
        conteudos.append((nome, extensao, dados))
    import src.pipeline.service as service  # noqa: PLR0402 — fachada exigida pela arquitetura

    origens = {}
    for indice, url in enumerate(urls, 1):
        try:
            origem = service.validar_url_conversao(url)
        except service.ConversionUserError as erro:
            recusados.append({"nome_arquivo": f"Endereço {indice}", "motivo": str(erro)})
            continue
        nome = f"pagina-{indice}.url"
        origens[nome] = origem
        conteudos.append((nome, "url", url.encode("utf-8")))
    if not conteudos:
        raise HTTPException(status_code=400, detail=" ".join(item["motivo"] for item in recusados))

    pistas = conversao_grupos.ler_metadados(metadados)
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
                tamanho_bytes=0 if extensao == "url" else len(dados),
                origem_url=origens.get(nome),
                situacao="fila",
            )
            session.add(documento)
            session.flush()
            storage.save(documento.id, nome, dados)
            if extensao in {"xls", "xlsx"}:
                try:
                    with tempfile.TemporaryDirectory(prefix="abas-") as pasta:
                        caminho = Path(pasta) / nome
                        caminho.write_bytes(dados)
                        abas = service.listar_abas_conversao(caminho, extensao)
                    if len(abas) > 1:
                        documento.abas_disponiveis = abas
                        documento.situacao = "aguardando_abas"
                        documento.expira_em = datetime.now(UTC) + timedelta(days=7)
                except service.ConversionUserError as erro:
                    documento.situacao = "falhou"
                    documento.erro = str(erro)
                    documento.concluido_em = datetime.now(UTC)
                    documento.expira_em = documento.concluido_em + timedelta(days=7)
            informacao = pistas.get(nome)
            if informacao:
                documento.modificado_em = informacao["modificado_em"]
                documento.pasta_origem = informacao["pasta"]
            documentos.append(documento)
        imagens = [d for d in documentos if d.formato in conversao_grupos.FORMATOS_IMAGEM]
        if len(imagens) >= 2:
            conversao_grupos.propor(session, lote, imagens, {"conversao": config.__dict__})
        session.commit()
        resposta = _serializar_lote(lote, documentos)

    for documento in documentos:
        if documento.situacao == "fila":
            process_conversion_document_task.defer(documento_id=documento.id)

    resposta["recusados"] = recusados
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


@router.get("/conversoes/limites")
def limites_conversao(identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    config = _config_conversao()
    return {
        campo: getattr(config, campo)
        for campo in ("max_arquivos", "max_bytes_arquivo", "max_bytes_lote")
    }


@router.get("/conversoes/{lote_id}")
def obter_conversao(lote_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    with SessionLocal() as session:
        lote = repo.get_lote_or_404(session, lote_id, identity)
        return _serializar_lote(lote, list(lote.documentos))


class AjusteGruposInput(BaseModel):
    class Grupo(BaseModel):
        imagens: list[str]

    grupos: list[Grupo]


def _erro_grupos(erro: conversao_grupos.ErroDeGrupos) -> HTTPException:
    return HTTPException(status_code=erro.status, detail=erro.mensagem)


@router.get("/conversoes/{lote_id}/grupos")
def listar_grupos(lote_id: str, identity: Identity = Depends(get_identity)) -> dict:  # noqa: B008
    with SessionLocal() as session:
        repo.get_lote_or_404(session, lote_id, identity)
        return conversao_grupos.listar(session, lote_id)


@router.put("/conversoes/{lote_id}/grupos")
def ajustar_grupos(
    lote_id: str,
    corpo: AjusteGruposInput,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        lote = repo.get_lote_or_404(session, lote_id, identity)
        try:
            resposta = conversao_grupos.ajustar(session, lote, [g.imagens for g in corpo.grupos])
        except conversao_grupos.ErroDeGrupos as erro:
            session.rollback()
            raise _erro_grupos(erro) from erro
        session.commit()
        return resposta


@router.post("/conversoes/{lote_id}/grupos/confirmar", status_code=202)
def confirmar_grupos(
    lote_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        lote = repo.get_lote_or_404(session, lote_id, identity)
        try:
            criados = conversao_grupos.confirmar(session, lote)
        except conversao_grupos.ErroDeGrupos as erro:
            session.rollback()
            raise _erro_grupos(erro) from erro
        session.commit()
        resposta = {"documentos": [_serializar_documento(d) for d in criados]}
        ids = [d.id for d in criados]
    for documento_id in ids:
        process_conversion_document_task.defer(documento_id=documento_id)
    return resposta


@router.get("/conversoes/{lote_id}/documentos/{documento_id}/miniatura")
def baixar_miniatura(
    lote_id: str,
    documento_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> Response:
    with SessionLocal() as session:
        documento = repo.get_documento_or_404(session, lote_id, documento_id, identity)
        if documento.formato not in conversao_grupos.FORMATOS_IMAGEM or documento.apagado_em:
            raise HTTPException(status_code=404, detail="Miniatura indisponível.")
        nome = documento.nome_arquivo
        formato = documento.formato
    with tempfile.TemporaryDirectory(prefix=f"miniatura-{documento_id}-") as pasta:
        get_storage().materialize(documento_id, pasta)
        caminho = Path(pasta) / nome
        if not caminho.exists():
            raise HTTPException(status_code=404, detail="Miniatura indisponível.")
        conteudo = caminho.read_bytes()
    tipo = "image/png" if formato == "png" else "image/jpeg"
    return Response(content=conteudo, media_type=tipo, headers={"Cache-Control": "private"})


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


@router.delete("/conversoes/{lote_id}/documentos/{documento_id}", status_code=204)
def apagar_documento(
    lote_id: str,
    documento_id: str,
    identity: Identity = Depends(get_identity),  # noqa: B008
) -> Response:
    """Apaga um documento convertido ou que falhou: arquivos, registro e, se vazio, o lote.

    Diferente da retenção automática (FR-007), que preserva o registro, esta é a
    exclusão pedida pela pessoa (FR-010, DEC-009). Documento em fila ou
    processando é recusado: cancelar um job em andamento está fora desta entrega.
    """
    require_write_role(identity)
    with SessionLocal() as session:
        documento = repo.get_documento_or_404(session, lote_id, documento_id, identity)
        if documento.situacao in ("fila", "processando"):
            raise HTTPException(
                status_code=409,
                detail="Documento em processamento; aguarde o fim para apagar.",
            )
        get_storage().delete_base(documento.id)
        lote = documento.lote
        session.delete(documento)
        session.flush()
        if session.query(DocumentoConversao).filter_by(lote_id=lote_id).count() == 0:
            session.delete(lote)
        else:
            recalcular_situacao_lote(session, lote_id)
        session.commit()
    return Response(status_code=204)


@router.post("/conversoes/{lote_id}/documentos/{documento_id}/abas")
def confirmar_abas(
    lote_id: str,
    documento_id: str,
    payload: dict,
    identity: Annotated[Identity, Depends(get_identity)],
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        documento = repo.confirmar_abas_documento(
            session, lote_id, documento_id, identity, payload.get("abas")
        )
        resposta = _serializar_documento(documento)
        session.commit()
    process_conversion_document_task.defer(documento_id=documento_id)
    return resposta


@router.post("/conversoes/{lote_id}/documentos/{documento_id}/reprocessar-ia", status_code=202)
def reprocessar_ia(
    lote_id: str, documento_id: str, identity: Annotated[Identity, Depends(get_identity)]
) -> dict:
    from src.app.tasks import reprocessar_documento_ia_task

    require_write_role(identity)
    with SessionLocal() as session:
        documento = repo.get_documento_or_404(session, lote_id, documento_id, identity)
        session.refresh(documento, with_for_update=True)
        if (
            documento.situacao != "concluido"
            or documento.apagado_em
            or (documento.expira_em and documento.expira_em <= datetime.now(UTC))
        ):
            raise HTTPException(
                status_code=409, detail="Documento indisponível; aguarde ou reenvie o original."
            )
        documento.situacao = "processando"
        documento.erro = None
        recalcular_situacao_lote(session, lote_id)
        resposta = _serializar_documento(documento)
        session.commit()
    reprocessar_documento_ia_task.defer(documento_id=documento_id)
    return resposta


class DominioConfirmacao(BaseModel):
    texto: str


@router.get("/conversoes/{lote_id}/dominio-proposto")
def dominio_proposto(lote_id: str, identity: Annotated[Identity, Depends(get_identity)]) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        repo.get_lote_or_404(session, lote_id, identity)
    return {"texto": limpeza.propor_dominio_do_lote(lote_id)}


@router.post("/conversoes/{lote_id}/dominio/confirmar")
def confirmar_dominio(
    lote_id: str,
    payload: DominioConfirmacao,
    identity: Annotated[Identity, Depends(get_identity)],
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        lote = repo.get_lote_or_404(session, lote_id, identity)
        if lote.situacao != "aguardando_dominio":
            raise HTTPException(status_code=409, detail="O lote não está aguardando o domínio.")
    try:
        limpeza.confirmar_dominio_do_lote(lote_id, payload.texto, identity.person_id)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from None
    with SessionLocal() as session:
        lote = repo.get_lote_or_404(session, lote_id, identity)
        return _serializar_lote(lote, list(lote.documentos))


@router.post("/conversoes/{lote_id}/documentos/{documento_id}/limpar", status_code=202)
def limpar_de_novo(
    lote_id: str, documento_id: str, identity: Annotated[Identity, Depends(get_identity)]
) -> dict:
    require_write_role(identity)
    with SessionLocal() as session:
        repo.get_documento_or_404(session, lote_id, documento_id, identity)
    if not limpeza.solicitar_nova_tentativa(lote_id, documento_id):
        raise HTTPException(
            status_code=409, detail="Só um documento que falhou pode ser limpo de novo."
        )
    return {"id": documento_id, "limpeza_situacao": "aguardando_limpeza"}


@router.get("/conversoes/{lote_id}/relatorio")
def baixar_relatorio(
    lote_id: str, identity: Annotated[Identity, Depends(get_identity)]
) -> Response:
    require_write_role(identity)
    with SessionLocal() as session:
        repo.get_lote_or_404(session, lote_id, identity)
        relatorio = session.query(RelatorioLote).filter_by(lote_id=lote_id).one_or_none()
        if relatorio is None:
            raise HTTPException(status_code=404, detail="O relatório do lote ainda não existe.")
        conteudo = relatorio.conteudo
    return Response(
        content=conteudo.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="relatorio-do-lote.md"'},
    )


@router.get("/conversoes/{lote_id}/exclusoes")
def listar_exclusoes(
    lote_id: str, identity: Annotated[Identity, Depends(get_identity)]
) -> list[dict]:
    require_write_role(identity)
    with SessionLocal() as session:
        repo.get_lote_or_404(session, lote_id, identity)
        linhas = (
            session.query(ExclusaoLimpeza)
            .filter_by(lote_id=lote_id)
            .order_by(ExclusaoLimpeza.arquivo, ExclusaoLimpeza.posicao)
            .all()
        )
        return [
            {
                "id": x.id,
                "arquivo": x.arquivo,
                "posicao": x.posicao,
                "motivo": x.motivo,
                "camada": x.camada,
                "confianca": x.confianca,
                "trecho": x.trecho,
                "mantido_em": x.mantido_em,
            }
            for x in linhas
        ]
