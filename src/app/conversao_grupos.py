"""Grupos de imagens do lote de conversão: proposta, ajuste e confirmação (SPEC-0040).

Fluxo: envio com duas ou mais imagens → ``propor`` (só metadados) → lote ``aguardando_grupos`` →
``ajustar`` (rascunho) → ``confirmar`` → um documento de formato ``grupo`` por grupo, convertido em
segundo plano. Nada é gerado antes da confirmação e a ordem aprovada é a do ``.md``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira
from src.app.models import DocumentoConversao, GrupoImagem, LoteConversao

FORMATOS_IMAGEM = {"png", "jpg", "jpeg"}
RETENCAO_DIAS = 7


class ErroDeGrupos(Exception):
    """Falha de regra de negócio com o status HTTP que a rota deve devolver."""

    def __init__(self, mensagem: str, status: int = 409):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def ler_metadados(texto: str | None) -> dict[str, dict[str, Any]]:
    """Metadados por nome de arquivo (``modificado_em`` ISO ou em milissegundos, e ``pasta``)."""
    if not texto:
        return {}
    try:
        itens = json.loads(texto)
    except ValueError:
        return {}
    saida: dict[str, dict[str, Any]] = {}
    for item in itens if isinstance(itens, list) else []:
        if not isinstance(item, dict) or not isinstance(item.get("nome"), str):
            continue
        quando = item.get("modificado_em")
        instante = None
        try:
            if isinstance(quando, (int, float)):
                instante = datetime.fromtimestamp(quando / 1000, UTC)
            elif isinstance(quando, str):
                instante = datetime.fromisoformat(quando)
                if instante.tzinfo is None:
                    instante = instante.replace(tzinfo=UTC)
        except (ValueError, OverflowError, OSError):
            instante = None
        pasta = item.get("pasta")
        saida[item["nome"]] = {
            "modificado_em": instante,
            "pasta": pasta if isinstance(pasta, str) and pasta else None,
        }
    return saida


def _chaves(imagens: list[DocumentoConversao]) -> dict[str, DocumentoConversao]:
    chaves: dict[str, DocumentoConversao] = {}
    for indice, imagem in enumerate(imagens):
        chave = imagem.nome_arquivo
        if chave in chaves:
            chave = f"{imagem.pasta_origem or indice}/{imagem.nome_arquivo}"
        chaves[chave] = imagem
    return chaves


def propor(session, lote: LoteConversao, imagens: list[DocumentoConversao], config) -> None:
    """Cria os grupos propostos e deixa as imagens e o lote aguardando a aprovação."""
    chaves = _chaves(imagens)
    proposta = service.propor_grupos_conversao(
        [
            {"nome": chave, "modificado_em": i.modificado_em, "pasta": i.pasta_origem}
            for chave, i in chaves.items()
        ],
        config,
    )
    vencimento = datetime.now(UTC) + timedelta(days=RETENCAO_DIAS)
    for ordem, grupo in enumerate(proposta["grupos"], 1):
        registro = GrupoImagem(
            lote_id=lote.id,
            ordem=ordem,
            certeza=grupo["certeza"],
            aprovado=grupo["certeza"] == "total",
        )
        session.add(registro)
        session.flush()
        for posicao, chave in enumerate(grupo["arquivos"], 1):
            imagem = chaves[chave]
            imagem.grupo_id = registro.id
            imagem.posicao_no_grupo = posicao
    for imagem in imagens:
        imagem.situacao = "aguardando_grupos"
        imagem.expira_em = vencimento
    lote.situacao = "aguardando_grupos"


def _grupos(session, lote_id: str) -> list[GrupoImagem]:
    return session.query(GrupoImagem).filter_by(lote_id=lote_id).order_by(GrupoImagem.ordem).all()


def _imagens(session, lote_id: str) -> list[DocumentoConversao]:
    return (
        session.query(DocumentoConversao)
        .filter(
            DocumentoConversao.lote_id == lote_id,
            DocumentoConversao.formato.in_(FORMATOS_IMAGEM),
            DocumentoConversao.grupo_id.isnot(None),
        )
        .order_by(DocumentoConversao.posicao_no_grupo)
        .all()
    )


def listar(session, lote_id: str) -> dict[str, Any]:
    grupos = _grupos(session, lote_id)
    por_grupo: dict[str, list[DocumentoConversao]] = {g.id: [] for g in grupos}
    for imagem in _imagens(session, lote_id):
        por_grupo.setdefault(imagem.grupo_id, []).append(imagem)
    return {
        "certeza": "total" if grupos and all(g.certeza == "total" for g in grupos) else "incerta",
        "grupos": [
            {
                "id": g.id,
                "ordem": g.ordem,
                "certeza": g.certeza,
                "aprovado": g.aprovado,
                "imagens": [
                    {
                        "documento_id": i.id,
                        "nome_arquivo": i.nome_arquivo,
                        "posicao": i.posicao_no_grupo,
                    }
                    for i in sorted(por_grupo[g.id], key=lambda x: x.posicao_no_grupo or 0)
                ],
            }
            for g in grupos
        ],
    }


def _exigir_aguardando(lote: LoteConversao) -> None:
    if lote.situacao != "aguardando_grupos":
        raise ErroDeGrupos("O lote não está aguardando a aprovação dos grupos.", 409)


def ajustar(session, lote: LoteConversao, grupos: list[list[str]]) -> dict[str, Any]:
    """Substitui o rascunho: cada imagem em exatamente um grupo, sem grupo vazio."""
    _exigir_aguardando(lote)
    imagens = {i.id: i for i in _imagens(session, lote.id)}
    enviados = [d for grupo in grupos for d in grupo]
    if any(not grupo for grupo in grupos):
        raise ErroDeGrupos("Não pode haver grupo vazio.", 422)
    if len(enviados) != len(set(enviados)):
        raise ErroDeGrupos("Cada imagem pode estar em um único grupo.", 422)
    if set(enviados) != set(imagens):
        raise ErroDeGrupos("Todas as imagens do lote precisam estar em algum grupo.", 422)
    existentes = _grupos(session, lote.id)
    for indice, ids in enumerate(grupos):
        if indice < len(existentes):
            registro = existentes[indice]
        else:
            registro = GrupoImagem(lote_id=lote.id, ordem=indice + 1, certeza="incerta")
            session.add(registro)
            session.flush()
        registro.ordem = indice + 1
        registro.aprovado = False
        for posicao, documento_id in enumerate(ids, 1):
            imagens[documento_id].grupo_id = registro.id
            imagens[documento_id].posicao_no_grupo = posicao
    session.flush()
    for sobra in existentes[len(grupos) :]:
        session.delete(sobra)
    session.flush()
    return listar(session, lote.id)


def confirmar(session, lote: LoteConversao) -> list[DocumentoConversao]:
    """Cria um documento ``grupo`` por grupo; o chamador enfileira a conversão de cada um."""
    _exigir_aguardando(lote)
    painel = listar(session, lote.id)
    imagens = {i.id: i for i in _imagens(session, lote.id)}
    criados: list[DocumentoConversao] = []
    for grupo in painel["grupos"]:
        tamanho = sum(imagens[i["documento_id"]].tamanho_bytes for i in grupo["imagens"])
        documento = DocumentoConversao(
            lote_id=lote.id,
            nome_arquivo=f"grupo-{grupo['ordem']}.grupo",
            formato="grupo",
            tamanho_bytes=tamanho,
            situacao="fila",
        )
        session.add(documento)
        session.flush()
        registro = session.get(GrupoImagem, grupo["id"])
        registro.documento_id = documento.id
        registro.aprovado = True
        criados.append(documento)
    for imagem in imagens.values():
        imagem.situacao = "agrupado"
    lote.situacao = "processando"
    return criados


def imagens_do_grupo(session, documento_id: str) -> list[DocumentoConversao]:
    grupo = session.query(GrupoImagem).filter_by(documento_id=documento_id).first()
    if grupo is None:
        return []
    return (
        session.query(DocumentoConversao)
        .filter_by(grupo_id=grupo.id)
        .order_by(DocumentoConversao.posicao_no_grupo)
        .all()
    )


def apagar_propostas_expiradas(session, lotes: set[str]) -> None:
    """Apaga as propostas dos lotes cujos documentos já expiraram por inteiro."""
    for lote_id in lotes:
        documentos = session.query(DocumentoConversao).filter_by(lote_id=lote_id).all()
        if not documentos or any(d.apagado_em is None for d in documentos):
            continue
        for documento in documentos:
            documento.grupo_id = None
        session.flush()
        session.query(GrupoImagem).filter_by(lote_id=lote_id).delete(synchronize_session=False)
