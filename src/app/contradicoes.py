"""Orquestração da análise de contradições de uma coleção (SPEC-0038).

Fluxo: pedido confirmado → ``iniciar_analise`` → ``processar_parte`` (uma parte por
execução: extração em partes e depois julgamentos por assunto) → ``concluida`` ou
``incompleta``. O estado fica em ``AnaliseContradicao.progresso`` para a retomada.
A análise só lê documentos: nunca escreve em documento, vetor ou coleção.
"""

from __future__ import annotations

import hashlib
import logging
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.orm.attributes import flag_modified

import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira
from src.app import limpeza
from src.app.db import SessionLocal
from src.app.models import (
    AnaliseContradicao,
    Colecao,
    DocumentoColecao,
    OcorrenciaContradicao,
    Workspace,
)
from src.app.storage import get_storage

__all__ = [
    "RETENCAO_DIAS",
    "apagar_da_colecao",
    "continuar_analise",
    "criar_modelo_ia",
    "iniciar_analise",
    "processar_parte",
    "purgar_retencao",
]

RETENCAO_DIAS = 90
TAMANHO_PARTE = 40_000
MAXIMO_POR_JULGAMENTO = 20
JULGAMENTOS_POR_EXECUCAO = 10
logger = logging.getLogger(__name__)


class ErroDeAnalise(Exception):
    """Falha de regra de negócio com o status HTTP que a rota deve devolver."""

    def __init__(self, mensagem: str, status: int = 409):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def _agora() -> datetime:
    return datetime.now(UTC)


def criar_modelo_ia(session, workspace: Workspace):
    """Adapter de chat da conexão de IA do Workspace; a chave só existe em memória."""
    return limpeza.criar_modelo_ia(session, workspace)


def _documentos_da_colecao(session, colecao_id: str) -> list[DocumentoColecao]:
    return (
        session.query(DocumentoColecao)
        .filter_by(colecao_id=colecao_id)
        .order_by(DocumentoColecao.nome_arquivo)
        .all()
    )


def _validar_pedido(session, colecao: Colecao, confirmado: bool) -> Workspace:
    workspace = session.get(Workspace, colecao.workspace_id)
    if not workspace.ia_externa_permitida:
        raise ErroDeAnalise(
            "Ative a análise por IA externa no Workspace para analisar contradições.", 409
        )
    if not workspace.conexao_ia_id:
        raise ErroDeAnalise("Escolha uma conexão de IA para análise no Workspace.", 409)
    if not confirmado:
        raise ErroDeAnalise("Confirme o aviso: o conteúdo será enviado à IA configurada.", 422)
    if not _documentos_da_colecao(session, colecao.id):
        raise ErroDeAnalise("Não há documentos para analisar nesta coleção.", 422)
    ativa = (
        session.query(AnaliseContradicao)
        .filter_by(colecao_id=colecao.id, situacao="em_andamento")
        .first()
    )
    if ativa is not None:
        raise ErroDeAnalise("Já existe uma análise em andamento nesta coleção.", 409)
    return workspace


def iniciar_analise(session, colecao: Colecao, pessoa_id: str, confirmado: bool):
    workspace = _validar_pedido(session, colecao, confirmado)
    dominio = limpeza.dominio_vigente(session, workspace.id)
    agora = _agora()
    analise = AnaliseContradicao(
        colecao_id=colecao.id,
        situacao="em_andamento",
        iniciada_por=pessoa_id,
        provedor=limpeza.provedor_da_ia(session, workspace),
        dominio_versao_id=dominio.id if dominio else None,
        progresso={},
        criado_em=agora,
        expira_em=agora + timedelta(days=RETENCAO_DIAS),
    )
    session.add(analise)
    session.commit()
    return analise


def continuar_analise(session, colecao: Colecao, analise_id: str):
    analise = session.get(AnaliseContradicao, analise_id)
    if analise is None or analise.colecao_id != colecao.id:
        raise ErroDeAnalise("Análise não encontrada.", 404)
    if analise.situacao != "incompleta":
        raise ErroDeAnalise("Só uma análise incompleta pode ser continuada.", 409)
    _validar_pedido(session, colecao, confirmado=True)
    analise.situacao = "em_andamento"
    analise.motivo = None
    session.commit()
    return analise


def _ler_documentos(documentos: list[DocumentoColecao]) -> tuple[dict[str, str], list[str]]:
    textos: dict[str, str] = {}
    ignorados: list[str] = []
    for documento in documentos:
        if not documento.ultimo_envio_id:
            ignorados.append(documento.nome_arquivo)
            continue
        try:
            with tempfile.TemporaryDirectory(prefix="contradicoes-") as pasta:
                get_storage().materialize(documento.ultimo_envio_id, pasta)
                textos[documento.nome_arquivo] = (Path(pasta) / documento.nome_arquivo).read_text(
                    encoding="utf-8"
                )
        except (OSError, ValueError):
            ignorados.append(documento.nome_arquivo)
    return textos, ignorados


def _chave_julgamento(julgamento: dict[str, Any]) -> str:
    textos = sorted(a["texto"] for a in julgamento["afirmacoes"])
    base = julgamento["assunto"] + "\0" + "\0".join(textos)
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def _chave_trechos(ocorrencia: dict[str, Any]) -> str:
    trechos = sorted(f"{t['arquivo']}\0{t['texto']}" for t in ocorrencia["trechos"])
    base = ocorrencia["etiqueta"] + "\0" + "\0".join(trechos)
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def _falhar(session, analise: AnaliseContradicao, erro: Exception) -> None:
    motivo = "Resposta da IA inválida" if isinstance(erro, ValueError) else "IA indisponível"
    logger.warning("análise %s interrompida: %s (%s)", analise.id, motivo, type(erro).__name__)
    analise.situacao = "incompleta"
    analise.motivo = motivo
    session.commit()


def processar_parte(analise_id: str) -> bool:
    """Processa uma parte da análise; devolve ``True`` quando ainda há o que fazer."""
    with SessionLocal() as session:
        analise = session.get(AnaliseContradicao, analise_id)
        if analise is None or analise.situacao != "em_andamento":
            return False
        colecao = session.get(Colecao, analise.colecao_id)
        workspace = session.get(Workspace, colecao.workspace_id)
        try:
            modelo = criar_modelo_ia(session, workspace)
        except Exception as erro:  # noqa: BLE001 — conexão indisponível vira análise incompleta
            _falhar(session, analise, erro)
            return False
        documentos, ignorados = _ler_documentos(_documentos_da_colecao(session, colecao.id))
        progresso = dict(analise.progresso or {})
        progresso.setdefault("proxima_parte", 0)
        progresso.setdefault("afirmacoes", [])
        progresso.setdefault("nao_classificadas", 0)
        progresso.setdefault("julgados", [])
        progresso["avisos"] = [f"Documento ignorado (ilegível): {n}" for n in ignorados]
        analise.documentos_analisados = len(documentos)
        partes = service.dividir_documentos_em_partes(documentos, TAMANHO_PARTE)
        if progresso["proxima_parte"] < len(partes):
            return _extrair_proxima_parte(session, analise, modelo, partes, progresso)
        return _julgar_pendentes(session, analise, modelo, progresso)


def _salvar(session, analise: AnaliseContradicao, progresso: dict[str, Any]) -> None:
    analise.progresso = progresso
    flag_modified(analise, "progresso")  # o dict é alterado no lugar
    session.commit()


def _extrair_proxima_parte(session, analise, modelo, partes, progresso) -> bool:
    indice = progresso["proxima_parte"]
    try:
        resultado = service.extrair_afirmacoes(partes[indice], modelo)
    except Exception as erro:  # noqa: BLE001 — qualquer falha da IA interrompe a análise
        _salvar(session, analise, progresso)
        _falhar(session, analise, erro)
        return False
    progresso["afirmacoes"] += resultado["afirmacoes"]
    progresso["nao_classificadas"] += resultado["nao_classificadas"]
    progresso["proxima_parte"] = indice + 1
    if progresso["proxima_parte"] >= len(partes):
        julgamentos = service.agrupar_assuntos(progresso["afirmacoes"], MAXIMO_POR_JULGAMENTO)
        analise.total_assuntos = len(julgamentos)
    _salvar(session, analise, progresso)
    return True


def _julgar_pendentes(session, analise, modelo, progresso) -> bool:
    julgamentos = service.agrupar_assuntos(progresso["afirmacoes"], MAXIMO_POR_JULGAMENTO)
    analise.total_assuntos = len(julgamentos)
    julgados = set(progresso["julgados"])
    pendentes = [j for j in julgamentos if _chave_julgamento(j) not in julgados]
    for julgamento in pendentes[:JULGAMENTOS_POR_EXECUCAO]:
        try:
            ocorrencias = service.julgar_assunto(
                modelo, julgamento["assunto"], julgamento["afirmacoes"]
            )
        except Exception as erro:  # noqa: BLE001 — qualquer falha da IA interrompe a análise
            _salvar(session, analise, progresso)
            _falhar(session, analise, erro)
            return False
        for ocorrencia in ocorrencias:
            chave = _chave_trechos(ocorrencia)
            existe = (
                session.query(OcorrenciaContradicao)
                .filter_by(
                    analise_id=analise.id,
                    assunto_normalizado=julgamento["assunto"],
                    chave_trechos=chave,
                )
                .first()
            )
            if existe is None:
                session.add(
                    OcorrenciaContradicao(
                        analise_id=analise.id,
                        assunto=ocorrencia["assunto"][:200],
                        assunto_normalizado=julgamento["assunto"][:200],
                        etiqueta=ocorrencia["etiqueta"],
                        impacto=ocorrencia["impacto"],
                        chave_trechos=chave,
                        trechos=ocorrencia["trechos"],
                        explicacao=ocorrencia["explicacao"],
                        arquivo_mais_antigo=ocorrencia["arquivo_mais_antigo"],
                    )
                )
        progresso["julgados"] = [*progresso["julgados"], _chave_julgamento(julgamento)]
        analise.concluidos = len(progresso["julgados"])
        _salvar(session, analise, progresso)
    restantes = len(pendentes) - JULGAMENTOS_POR_EXECUCAO
    if restantes > 0:
        return True
    analise.situacao = "concluida"
    analise.concluido_em = _agora()
    session.commit()
    return False


def apagar_da_colecao(session, colecao_id: str) -> None:
    """Remove análises e ocorrências da coleção, sem deixar texto de cliente."""
    ids = [
        i for (i,) in session.query(AnaliseContradicao.id).filter_by(colecao_id=colecao_id).all()
    ]
    if ids:
        session.query(OcorrenciaContradicao).filter(
            OcorrenciaContradicao.analise_id.in_(ids)
        ).delete(synchronize_session=False)
        session.query(AnaliseContradicao).filter(AnaliseContradicao.id.in_(ids)).delete(
            synchronize_session=False
        )


def purgar_retencao(agora: datetime | None = None) -> None:
    """Apaga análises vencidas (90 dias) e suas ocorrências."""
    agora = agora or _agora()
    with SessionLocal() as session:
        vencidas = [
            i
            for (i,) in session.query(AnaliseContradicao.id)
            .filter(AnaliseContradicao.expira_em < agora)
            .all()
        ]
        if vencidas:
            session.query(OcorrenciaContradicao).filter(
                OcorrenciaContradicao.analise_id.in_(vencidas)
            ).delete(synchronize_session=False)
            session.query(AnaliseContradicao).filter(AnaliseContradicao.id.in_(vencidas)).delete(
                synchronize_session=False
            )
        session.commit()
