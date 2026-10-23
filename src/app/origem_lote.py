"""Origem "lote de conversão" para a prévia e o envio (SPEC-0043).

Lê os `.md` que a Fase 1 já guarda, com as mesmas validações do upload manual, e mantém a
origem dos documentos indexados: quem veio de qual lote, com qual versão do `.md`. A marca
"alterado desde a indexação" é calculada na leitura e nunca persistida; o registro guarda só
identificadores e o hash do `.md`, nunca o texto do cliente.
"""

from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app import ingestao, repo
from src.app.auth import Identity
from src.app.models import Colecao, DocumentoColecao, DocumentoConversao, OrigemDocumento
from src.app.storage import get_storage

CHAVE_ORIGEM = "origem_lote"
EM_DIA = "em_dia"
ALTERADO = "alterado"
EXPIRADO = "expirado"


@dataclass(frozen=True)
class MarkdownDoLote:
    """Um `.md` lido do lote: nome, bytes, documento de origem e hash do conteúdo lido."""

    nome: str
    dados: bytes
    documento_id: str
    hash_md: str


def exigir_uma_origem(tem_arquivos: bool, usar_base_preparada: bool, lote_id: str | None) -> None:
    """Upload, base preparada e lote são origens exclusivas (422 ao combinar)."""
    if sum((tem_arquivos, usar_base_preparada, bool(lote_id))) > 1:
        raise HTTPException(
            status_code=422,
            detail="Use somente uma origem: arquivos enviados, base preparada ou lote.",
        )


def nome_markdown(documento: DocumentoConversao) -> str:
    return f"{Path(documento.nome_arquivo).stem}.md"


def hash_do_conteudo(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def _ler_markdown(documento: DocumentoConversao) -> bytes | None:
    """Bytes do `.md` guardado para o documento, ou ``None`` se o arquivo não existe mais."""
    if documento.apagado_em is not None:
        return None
    with tempfile.TemporaryDirectory(prefix=f"origem-{documento.id}-") as pasta:
        get_storage().materialize(documento.id, pasta)
        caminho = Path(pasta) / nome_markdown(documento)
        return caminho.read_bytes() if caminho.exists() else None


def _indisponivel(documento: DocumentoConversao) -> HTTPException:
    return HTTPException(
        status_code=409,
        detail=(
            f"O documento {nome_markdown(documento)} não está mais disponível no lote "
            "(ainda em processamento, com falha ou já apagado). Ajuste a seleção."
        ),
    )


def ler_documentos_lote(
    session: Session,
    identity: Identity,
    lote_id: str,
    documento_ids: list[str],
    *,
    workspace_id: str | None = None,
) -> list[MarkdownDoLote]:
    """Lê uma única vez os `.md` marcados do lote, validando escopo, aptidão e limites.

    Lote fora do tenant, do projeto ou do Workspace informado responde 404 sem revelar que
    existe; documento que não está mais apto responde 409 com o nome do `.md`.
    """
    lote = repo.get_lote_or_404(session, lote_id, identity)
    if workspace_id is not None and lote.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Lote de conversão não encontrado.")
    ids = list(dict.fromkeys(documento_ids))
    if not ids:
        raise HTTPException(status_code=400, detail="Marque ao menos um documento do lote.")
    if len(ids) > ingestao.MAX_ARQUIVOS:
        raise HTTPException(
            status_code=400, detail=f"Limite de {ingestao.MAX_ARQUIVOS} arquivos excedido."
        )
    lidos: list[MarkdownDoLote] = []
    total = 0
    for documento_id in ids:
        documento = session.get(DocumentoConversao, documento_id)
        if documento is None or documento.lote_id != lote.id:
            raise HTTPException(status_code=404, detail="Documento do lote não encontrado.")
        if documento.situacao != "concluido":
            raise _indisponivel(documento)
        dados = _ler_markdown(documento)
        if dados is None:
            raise _indisponivel(documento)
        ingestao.validar_conteudo_markdown(nome_markdown(documento), dados)
        total += len(dados)
        if total > ingestao.MAX_BYTES_TOTAL:
            raise HTTPException(status_code=400, detail="Limite de 50 MB por envio excedido.")
        lidos.append(
            MarkdownDoLote(nome_markdown(documento), dados, documento.id, hash_do_conteudo(dados))
        )
    return lidos


def mapa_de_origem(lote_id: str, lidos: list[MarkdownDoLote]) -> dict:
    """O que o envio guarda para o worker registrar a origem: ids e hashes, sem texto."""
    return {
        "lote_id": lote_id,
        "documentos": {
            item.nome: {"documento_id": item.documento_id, "hash_md": item.hash_md}
            for item in lidos
        },
    }


def registrar_origem(session: Session, envio, documento: DocumentoColecao) -> None:
    """Grava ou atualiza a origem do documento a partir do mapa guardado no envio."""
    mapa = (envio.processamento or {}).get(CHAVE_ORIGEM)
    if not mapa:
        return
    item = (mapa.get("documentos") or {}).get(documento.nome_arquivo)
    if item is None:
        return
    origem = session.execute(
        select(OrigemDocumento).where(OrigemDocumento.documento_colecao_id == documento.id)
    ).scalar_one_or_none()
    if origem is None:
        origem = OrigemDocumento(documento_colecao_id=documento.id)
        session.add(origem)
    origem.lote_id = mapa["lote_id"]
    origem.documento_conversao_id = item["documento_id"]
    origem.envio_id = envio.id
    origem.hash_md = item["hash_md"]
    origem.atualizado_em = datetime.now(UTC)


def situacao_da_origem(origem: OrigemDocumento, documento: DocumentoConversao | None) -> str:
    """``em_dia``, ``alterado`` ou ``expirado``; só lê o armazenamento se o arquivo existe."""
    if documento is None:
        return EXPIRADO
    dados = _ler_markdown(documento)
    if dados is None:
        return EXPIRADO
    return EM_DIA if hash_do_conteudo(dados) == origem.hash_md else ALTERADO


def indexado_por_documento(session: Session, lote_ids: list[str]) -> dict[str, dict]:
    """Por documento de lote já indexado: coleção e ``situacao_origem`` (a mais recente vence)."""
    if not lote_ids:
        return {}
    linhas = session.execute(
        select(OrigemDocumento, DocumentoColecao.colecao_id, Colecao.nome)
        .join(DocumentoColecao, DocumentoColecao.id == OrigemDocumento.documento_colecao_id)
        .join(Colecao, Colecao.id == DocumentoColecao.colecao_id)
        .where(OrigemDocumento.lote_id.in_(lote_ids))
        .order_by(OrigemDocumento.atualizado_em)
    ).all()
    resultado: dict[str, dict] = {}
    for origem, colecao_id, colecao_nome in linhas:
        documento = session.get(DocumentoConversao, origem.documento_conversao_id)
        resultado[origem.documento_conversao_id] = {
            "colecao_id": colecao_id,
            "colecao_nome": colecao_nome,
            "situacao_origem": situacao_da_origem(origem, documento),
        }
    return resultado


def origem_por_documento_da_colecao(session: Session, colecao_id: str) -> dict[str, dict]:
    """Por documento da coleção que veio de um lote: lote, documento e ``situacao_origem``."""
    linhas = session.execute(
        select(OrigemDocumento)
        .join(DocumentoColecao, DocumentoColecao.id == OrigemDocumento.documento_colecao_id)
        .where(DocumentoColecao.colecao_id == colecao_id)
    ).scalars()
    resultado: dict[str, dict] = {}
    for origem in linhas:
        documento = session.get(DocumentoConversao, origem.documento_conversao_id)
        resultado[origem.documento_colecao_id] = {
            "lote_id": origem.lote_id,
            "documento_conversao_id": origem.documento_conversao_id,
            "situacao_origem": situacao_da_origem(origem, documento),
        }
    return resultado
