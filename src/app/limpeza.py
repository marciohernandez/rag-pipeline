"""Orquestração da limpeza de conteúdo de domínio da Fase 1 (SPEC-0037).

Fluxo: conversão do documento → ``preparar_limpeza_do_lote`` (exige o resumo do domínio
confirmado) → ``limpar_documento`` (regras fixas e, se permitido, IA) →
``finalizar_limpeza_lote`` (duplicidade entre documentos e relatório).
"""

from __future__ import annotations

import json
import logging
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira
from src.app.db import SessionLocal
from src.app.models import (
    Conexao,
    DocumentoConversao,
    DominioWorkspace,
    ExclusaoLimpeza,
    LoteConversao,
    RelatorioLote,
    Workspace,
)
from src.app.settings import get_settings
from src.app.storage import get_storage

__all__ = [
    "RETENCAO_RELATORIO_DIAS",
    "RETENCAO_TEXTO_REMOVIDO_DIAS",
    "confirmar_dominio_do_lote",
    "criar_modelo_ia",
    "dominio_vigente",
    "enfileirar_limpeza",
    "finalizar_limpeza_lote",
    "limpar_documento",
    "preparar_limpeza_do_lote",
    "propor_dominio_do_lote",
    "purgar_retencao",
    "salvar_dominio",
]

logger = logging.getLogger(__name__)

RETENCAO_TEXTO_REMOVIDO_DIAS = 30
RETENCAO_RELATORIO_DIAS = 90
TAMANHO_MAXIMO_DOMINIO = 4000
_TERMINAIS = ("limpo", "limpo_com_duvidas", "falhou")


def _agora() -> datetime:
    return datetime.now(UTC)


def _nome_md(documento: DocumentoConversao) -> str:
    return f"{Path(documento.nome_arquivo).stem}.md"


def _opcoes() -> dict[str, Any]:
    return dict(get_settings().conversao or {})


# --- domínio ---------------------------------------------------------------------------


def dominio_vigente(session, workspace_id: str) -> DominioWorkspace | None:
    return (
        session.query(DominioWorkspace)
        .filter_by(workspace_id=workspace_id, vigente=True)
        .order_by(DominioWorkspace.versao.desc())
        .first()
    )


def salvar_dominio(
    session, workspace_id: str, texto: str, pessoa_id: str | None
) -> DominioWorkspace:
    """Cria a próxima versão do resumo e a torna vigente; as anteriores permanecem."""
    texto = (texto or "").strip()
    if not texto or len(texto) > TAMANHO_MAXIMO_DOMINIO:
        raise ValueError(
            f"O resumo do domínio deve ter de 1 a {TAMANHO_MAXIMO_DOMINIO} caracteres."
        )
    session.get(Workspace, workspace_id, with_for_update=True)
    ultima = (
        session.query(DominioWorkspace.versao)
        .filter_by(workspace_id=workspace_id)
        .order_by(DominioWorkspace.versao.desc())
        .first()
    )
    session.query(DominioWorkspace).filter_by(workspace_id=workspace_id, vigente=True).update(
        {"vigente": False}
    )
    nova = DominioWorkspace(
        workspace_id=workspace_id,
        versao=(ultima[0] if ultima else 0) + 1,
        texto=texto,
        vigente=True,
        aprovado_por=pessoa_id,
    )
    session.add(nova)
    session.flush()
    return nova


# --- IA ----------------------------------------------------------------------------------


def criar_modelo_ia(session, workspace: Workspace):
    """Adapter de chat da conexão de IA do Workspace; a chave só existe em memória."""
    from src.app import conexoes

    conexao = session.get(Conexao, workspace.conexao_ia_id) if workspace.conexao_ia_id else None
    if conexao is None or conexao.situacao != "ativa" or conexao.tipo != conexoes.TIPO_IA:
        raise conexoes.ErroDeConexao("Conexão de IA indisponível para o Workspace.", 409)
    configuracoes = get_settings()
    segredo = (
        conexoes.decifrar_segredo(configuracoes.conexoes_chave, conexao.segredo_cifrado)
        if conexao.segredo_cifrado
        else None
    )
    return service.criar_modelo_chat(
        conexoes.configuracao_para_pipeline(
            conexoes.TIPO_IA,
            conexao.configuracao,
            segredo,
            permitir_locais=configuracoes.conexoes_permitir_locais,
        )
    )


def _provedor(session, workspace: Workspace) -> str | None:
    conexao = session.get(Conexao, workspace.conexao_ia_id) if workspace.conexao_ia_id else None
    if conexao is None:
        return None
    host = urlparse((conexao.configuracao or {}).get("url_base") or "").hostname
    return host or "openrouter"


# --- armazenamento -----------------------------------------------------------------------


def _ler_md(documento: DocumentoConversao) -> str:
    with tempfile.TemporaryDirectory(prefix="limpeza-") as pasta:
        get_storage().materialize(documento.id, pasta)
        return (Path(pasta) / _nome_md(documento)).read_text(encoding="utf-8")


def _lateral(documento: DocumentoConversao) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="limpeza-") as pasta:
        get_storage().materialize(documento.id, pasta)
        caminho = Path(pasta) / f"{Path(documento.nome_arquivo).stem}.limpeza.json"
        return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else {}


def _gravar_lateral(documento: DocumentoConversao, dados: dict[str, Any]) -> None:
    get_storage().save(
        documento.id,
        f"{Path(documento.nome_arquivo).stem}.limpeza.json",
        json.dumps(dados, ensure_ascii=False).encode("utf-8"),
    )


# --- fluxo -------------------------------------------------------------------------------


def enfileirar_limpeza(documento_id: str) -> None:
    from src.app import tasks

    tasks.limpar_documento_task.defer(documento_id=documento_id)


def _documentos_convertidos(session, lote_id: str) -> list[DocumentoConversao]:
    return (
        session.query(DocumentoConversao)
        .filter(
            DocumentoConversao.lote_id == lote_id,
            DocumentoConversao.situacao == "concluido",
            DocumentoConversao.apagado_em.is_(None),
        )
        .order_by(DocumentoConversao.criado_em, DocumentoConversao.id)
        .all()
    )


def _iniciar(session, lote: LoteConversao, dominio: DominioWorkspace) -> list[str]:
    lote.dominio_versao_id = dominio.id
    lote.situacao = "limpando"
    return [
        d.id
        for d in _documentos_convertidos(session, lote.id)
        if d.limpeza_situacao == "aguardando_limpeza"
    ]


def preparar_limpeza_do_lote(lote_id: str) -> None:
    """Chamada quando a conversão do lote termina: pausa no domínio ou inicia a limpeza."""
    with SessionLocal() as session:
        lote = session.get(LoteConversao, lote_id, with_for_update=True)
        if lote is None:
            return
        todos = session.query(DocumentoConversao).filter_by(lote_id=lote_id).all()
        if any(d.situacao in ("fila", "processando", "aguardando_abas") for d in todos):
            return
        convertidos = _documentos_convertidos(session, lote_id)
        if not convertidos:
            return
        for documento in convertidos:
            if documento.limpeza_situacao is None:
                documento.limpeza_situacao = "aguardando_limpeza"
        dominio = dominio_vigente(session, lote.workspace_id)
        if dominio is None:
            lote.situacao = "aguardando_dominio"
            session.commit()
            return
        ids = _iniciar(session, lote, dominio)
        session.commit()
    for documento_id in ids:
        enfileirar_limpeza(documento_id)


def propor_dominio_do_lote(lote_id: str) -> str:
    """Resumo proposto pela IA a partir de uma amostra do lote; vazio sem IA permitida."""
    with SessionLocal() as session:
        lote = session.get(LoteConversao, lote_id)
        workspace = session.get(Workspace, lote.workspace_id)
        if not workspace.ia_externa_permitida:
            return ""
        amostra = []
        for documento in _documentos_convertidos(session, lote_id)[:5]:
            try:
                amostra.append(_ler_md(documento))
            except OSError:
                continue
        if not amostra:
            return ""
        try:
            return service.propor_dominio_ia(amostra, criar_modelo_ia(session, workspace))
        except Exception:  # noqa: BLE001 — a pessoa pode escrever o resumo à mão
            logger.warning("proposta de domínio indisponível para o lote %s", lote_id)
            return ""


def confirmar_dominio_do_lote(lote_id: str, texto: str, pessoa_id: str | None) -> None:
    with SessionLocal() as session:
        lote = session.get(LoteConversao, lote_id, with_for_update=True)
        dominio = salvar_dominio(session, lote.workspace_id, texto, pessoa_id)
        ids = _iniciar(session, lote, dominio)
        session.commit()
    for documento_id in ids:
        enfileirar_limpeza(documento_id)


def limpar_documento(documento_id: str) -> None:
    opcoes = _opcoes()
    with SessionLocal() as session:
        documento = session.get(DocumentoConversao, documento_id, with_for_update=True)
        if documento is None or documento.limpeza_situacao not in ("aguardando_limpeza", "falhou"):
            return
        lote = session.get(LoteConversao, documento.lote_id)
        if lote.situacao == "aguardando_dominio" or not lote.dominio_versao_id:
            return
        workspace = session.get(Workspace, lote.workspace_id)
        dominio = session.get(DominioWorkspace, lote.dominio_versao_id)
        documento.limpeza_situacao = "limpando"
        documento.limpeza_erro = None
        session.commit()
        nome_md = _nome_md(documento)
        try:
            texto = _ler_md(documento)
            regras = service.aplicar_regras_limpeza(texto, nome_md)
            texto = regras.markdown
            exclusoes = list(regras.exclusoes)
            duvidas: list[str] = []
            motivo_ia: str | None = None
            if workspace.ia_externa_permitida:
                try:
                    modelo = criar_modelo_ia(session, workspace)
                    texto, por_ia, duvidas = service.limpar_secoes_ia(
                        texto, nome_md, modelo, dominio.texto, opcoes
                    )
                    exclusoes += por_ia
                except Exception:  # noqa: BLE001 — a IA nunca derruba a limpeza por regras
                    logger.warning("IA de análise indisponível para o documento %s", documento_id)
                    motivo_ia = "IA indisponível"
            else:
                motivo_ia = "IA externa desligada para o Workspace"
            get_storage().save(documento.id, nome_md, texto.encode("utf-8"))
            for e in exclusoes:
                session.add(
                    ExclusaoLimpeza(
                        lote_id=lote.id,
                        documento_id=documento.id,
                        arquivo=e.arquivo,
                        posicao=e.posicao,
                        motivo=e.motivo,
                        camada=e.camada,
                        confianca=e.confianca,
                        trecho=e.trecho,
                    )
                )
            _gravar_lateral(documento, {"duvidas": duvidas, "motivo_ia": motivo_ia})
            documento.exclusoes = len(exclusoes)
            documento.duvidas = len(duvidas)
            documento.limpeza_erro = motivo_ia
            documento.limpeza_situacao = "limpo_com_duvidas" if duvidas else "limpo"
        except Exception:
            logger.exception("falha na limpeza do documento %s", documento_id)
            documento.limpeza_situacao = "falhou"
            documento.limpeza_erro = "Não foi possível ler o Markdown do documento; tente de novo."
        session.commit()


def limpeza_pendente(lote_id: str) -> bool:
    with SessionLocal() as session:
        return any(
            d.limpeza_situacao in ("aguardando_limpeza", "limpando")
            for d in _documentos_convertidos(session, lote_id)
        )


def solicitar_nova_tentativa(lote_id: str, documento_id: str) -> bool:
    """Recoloca um documento que falhou na fila, sem tocar nos já limpos."""
    with SessionLocal() as session:
        documento = session.get(DocumentoConversao, documento_id, with_for_update=True)
        if (
            documento is None
            or documento.lote_id != lote_id
            or documento.limpeza_situacao != "falhou"
        ):
            return False
        documento.limpeza_situacao = "aguardando_limpeza"
        documento.limpeza_erro = None
        session.get(LoteConversao, lote_id).situacao = "limpando"
        session.commit()
    enfileirar_limpeza(documento_id)
    return True


def finalizar_limpeza_lote(lote_id: str) -> None:
    """Duplicidade entre documentos, relatório do lote e situação final."""
    opcoes = _opcoes()
    with SessionLocal() as session:
        lote = session.get(LoteConversao, lote_id, with_for_update=True)
        workspace = session.get(Workspace, lote.workspace_id)
        documentos = _documentos_convertidos(session, lote_id)
        limpos = [d for d in documentos if d.limpeza_situacao in ("limpo", "limpo_com_duvidas")]
        textos = []
        for documento in limpos:
            try:
                textos.append((_nome_md(documento), _ler_md(documento)))
            except OSError:
                continue
        resultado = service.deduplicar_documentos_limpeza(textos, opcoes)
        por_nome = {_nome_md(d): d for d in limpos}
        for e in resultado.exclusoes:
            documento = por_nome[e.arquivo]
            session.add(
                ExclusaoLimpeza(
                    lote_id=lote.id,
                    documento_id=documento.id,
                    arquivo=e.arquivo,
                    posicao=e.posicao,
                    motivo=e.motivo,
                    camada=e.camada,
                    trecho=e.trecho,
                    mantido_em=e.mantido_em,
                )
            )
            documento.exclusoes += 1
        for nome, novo in resultado.documentos.items():
            antigo = dict(textos).get(nome)
            if antigo is not None and novo != antigo:
                get_storage().save(por_nome[nome].id, nome, novo.encode("utf-8"))
        itens, motivos_sem_ia = [], set()
        for documento in documentos:
            lateral = _lateral(documento) if documento.limpeza_situacao != "falhou" else {}
            if lateral.get("motivo_ia"):
                motivos_sem_ia.add(lateral["motivo_ia"])
            linhas = (
                session.query(ExclusaoLimpeza)
                .filter_by(lote_id=lote_id, documento_id=documento.id)
                .order_by(ExclusaoLimpeza.posicao)
                .all()
            )
            itens.append(
                {
                    "arquivo": _nome_md(documento),
                    "exclusoes": [
                        {
                            "arquivo": x.arquivo,
                            "posicao": x.posicao,
                            "motivo": x.motivo,
                            "camada": x.camada,
                            "confianca": x.confianca,
                            "mantido_em": x.mantido_em,
                        }
                        for x in linhas
                    ],
                    "duvidas": lateral.get("duvidas", []),
                    "revisar": [a.get("mensagem", "") for a in (documento.avisos or [])],
                    "falha": documento.limpeza_erro
                    if documento.limpeza_situacao == "falhou"
                    else None,
                }
            )
        ia_usada = bool(workspace.ia_externa_permitida) and not motivos_sem_ia
        dominio = (
            session.get(DominioWorkspace, lote.dominio_versao_id)
            if lote.dominio_versao_id
            else None
        )
        conteudo = service.montar_relatorio_limpeza(
            itens,
            resultado.provaveis,
            ia_usada=ia_usada,
            provedor=_provedor(session, workspace) if ia_usada else None,
            dominio_versao=dominio.versao if dominio else None,
            motivo_sem_ia=", ".join(sorted(motivos_sem_ia)) or None,
        )
        session.query(RelatorioLote).filter_by(lote_id=lote_id).delete()
        agora = _agora()
        session.add(
            RelatorioLote(
                lote_id=lote_id,
                conteudo=conteudo,
                ia_usada=ia_usada,
                provedor=_provedor(session, workspace) if ia_usada else None,
                dominio_versao_id=lote.dominio_versao_id,
                contagens={
                    "documentos": len(documentos),
                    "exclusoes": sum(d.exclusoes for d in documentos),
                    "duvidas": sum(d.duvidas for d in documentos),
                },
                criado_em=agora,
                expira_em=agora + timedelta(days=RETENCAO_RELATORIO_DIAS),
            )
        )
        falhou = any(d.limpeza_situacao == "falhou" for d in documentos)
        lote.situacao = "concluido_com_falhas" if falhou else "concluido"
        session.commit()


def purgar_retencao(agora: datetime | None = None) -> None:
    """Zera o texto removido após 30 dias e apaga relatórios vencidos (90 dias)."""
    agora = agora or _agora()
    with SessionLocal() as session:
        session.query(ExclusaoLimpeza).filter(
            ExclusaoLimpeza.criado_em < agora - timedelta(days=RETENCAO_TEXTO_REMOVIDO_DIAS),
            ExclusaoLimpeza.trecho.is_not(None),
        ).update({"trecho": None}, synchronize_session=False)
        session.query(RelatorioLote).filter(RelatorioLote.expira_em < agora).delete(
            synchronize_session=False
        )
        session.commit()
