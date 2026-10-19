"""Decisão da empresa: interpretação da resposta, correção com histórico e liberação (SPEC-0039).

Fluxo: resposta colada → ``registrar_resposta`` → ``interpretar`` (worker) → propostas →
confirmação humana (``aplicar_lote`` ou ``decidir``) → nova versão do documento →
publicação por novo envio à coleção → ``revisar``. Nenhum documento muda sem confirmação
registrada, e a correção troca somente o trecho alvo (verificado por hash do documento).
"""

from __future__ import annotations

import hashlib
import logging
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira
from src.app import limpeza, publicacao, repo
from src.app.db import SessionLocal
from src.app.models import (
    AnaliseContradicao,
    Colecao,
    DecisaoEmpresa,
    DocumentoColecao,
    Envio,
    OcorrenciaContradicao,
    PropostaCorrecao,
    RegistroExclusaoDecisoes,
    RespostaEmpresa,
    VersaoDocumento,
    Workspace,
)
from src.app.storage import get_storage

__all__ = [
    "RETENCAO_DIAS",
    "ErroDeDecisao",
    "apagar_da_colecao",
    "aplicar_lote",
    "criar_modelo_ia",
    "decidir",
    "interpretar",
    "purgar_retencao",
    "registrar_resposta",
    "restaurar_versao",
    "revisar",
]

RETENCAO_DIAS = 90
MAXIMO_RESPOSTA = 20_000
PENDENTES = ("clara", "incerta", "sem_decisao")
MOTIVO_FALHA = "A IA não respondeu. Tente interpretar de novo."
MSG_MANUAL = "Decida à mão: indique o arquivo, o trecho e o texto corrigido."
logger = logging.getLogger(__name__)


class ErroDeDecisao(Exception):
    """Falha de regra de negócio com o status HTTP que a rota deve devolver."""

    def __init__(self, mensagem: str, status: int = 409, **extra: Any):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
        self.extra = extra


def _agora() -> datetime:
    return datetime.now(UTC)


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def criar_modelo_ia(session, workspace: Workspace):
    """Adapter de chat da conexão de IA do Workspace; a chave só existe em memória."""
    return limpeza.criar_modelo_ia(session, workspace)


# --- leitura -----------------------------------------------------------------


def _ler_texto(documento: DocumentoColecao) -> str | None:
    if not documento.ultimo_envio_id:
        return None
    try:
        with tempfile.TemporaryDirectory(prefix="decisoes-") as pasta:
            get_storage().materialize(documento.ultimo_envio_id, pasta)
            return (Path(pasta) / documento.nome_arquivo).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None


def _documentos(session, colecao_id: str) -> dict[str, DocumentoColecao]:
    linhas = session.query(DocumentoColecao).filter_by(colecao_id=colecao_id).all()
    return {d.nome_arquivo: d for d in linhas}


def _analises(session, colecao_id: str) -> list[AnaliseContradicao]:
    return (
        session.query(AnaliseContradicao)
        .filter_by(colecao_id=colecao_id)
        .order_by(AnaliseContradicao.criado_em.desc())
        .all()
    )


def _ocorrencias(session, analise_id: str) -> list[OcorrenciaContradicao]:
    itens = session.query(OcorrenciaContradicao).filter_by(analise_id=analise_id).all()
    return sorted(itens, key=lambda o: (o.impacto != "alto", o.assunto.casefold(), o.id))


def _decididas(session, colecao_id: str) -> set[str]:
    linhas = (
        session.query(DecisaoEmpresa.ocorrencia_id)
        .filter(DecisaoEmpresa.colecao_id == colecao_id, DecisaoEmpresa.ocorrencia_id.isnot(None))
        .all()
    )
    return {i for (i,) in linhas}


def ocorrencias_abertas(session, colecao_id: str) -> list[OcorrenciaContradicao]:
    """Ocorrências da análise mais recente que ainda não receberam uma correção aplicada."""
    analises = _analises(session, colecao_id)
    if not analises:
        return []
    decididas = _decididas(session, colecao_id)
    return [o for o in _ocorrencias(session, analises[0].id) if o.id not in decididas]


def resumo_da_rodada(session, colecao_id: str) -> dict[str, int]:
    """Resolvidas, novas e abertas da análise mais recente em relação à anterior."""
    analises = [a for a in _analises(session, colecao_id) if a.situacao != "em_andamento"]
    abertas = len(ocorrencias_abertas(session, colecao_id))
    if len(analises) < 2:
        return {"resolvidas": 0, "novas": 0, "abertas": abertas}
    atuais = {o.assunto_normalizado for o in _ocorrencias(session, analises[0].id)}
    anteriores = {o.assunto_normalizado for o in _ocorrencias(session, analises[1].id)}
    return {
        "resolvidas": len(anteriores - atuais),
        "novas": len(atuais - anteriores),
        "abertas": abertas,
    }


def resposta_atual(session, colecao_id: str) -> RespostaEmpresa | None:
    return (
        session.query(RespostaEmpresa)
        .filter_by(colecao_id=colecao_id)
        .order_by(RespostaEmpresa.criado_em.desc())
        .first()
    )


def propostas_da_resposta(session, resposta_id: str) -> list[PropostaCorrecao]:
    return (
        session.query(PropostaCorrecao)
        .filter_by(resposta_id=resposta_id)
        .order_by(PropostaCorrecao.id)
        .all()
    )


# --- resposta e interpretação -------------------------------------------------


def registrar_resposta(
    session, colecao: Colecao, pessoa_id: str, texto: str, confirmado: bool, manual: bool
) -> RespostaEmpresa:
    texto = (texto or "").strip()
    if not texto:
        raise ErroDeDecisao("Cole a resposta da empresa.", 422)
    if len(texto) > MAXIMO_RESPOSTA:
        raise ErroDeDecisao(f"A resposta passa de {MAXIMO_RESPOSTA} caracteres.", 422)
    analises = _analises(session, colecao.id)
    abertas = ocorrencias_abertas(session, colecao.id)
    if not analises or not abertas:
        raise ErroDeDecisao("Não há contradições abertas para decidir nesta coleção.", 422)
    workspace = session.get(Workspace, colecao.workspace_id)
    if not manual:
        if not workspace.ia_externa_permitida:
            raise ErroDeDecisao(
                "Ative a análise por IA externa no Workspace para interpretar a resposta.", 409
            )
        if not workspace.conexao_ia_id:
            raise ErroDeDecisao("Escolha uma conexão de IA para análise no Workspace.", 409)
        if not confirmado:
            raise ErroDeDecisao("Confirme o aviso: o texto será enviado à IA configurada.", 422)
    ativa = (
        session.query(RespostaEmpresa).filter_by(colecao_id=colecao.id, situacao="em_andamento")
    ).first()
    if ativa is not None:
        raise ErroDeDecisao("Já existe uma interpretação em andamento nesta coleção.", 409)
    resposta = RespostaEmpresa(
        colecao_id=colecao.id,
        analise_id=analises[0].id,
        texto=texto,
        situacao="concluida" if manual else "em_andamento",
        criado_por=pessoa_id,
    )
    session.add(resposta)
    session.flush()
    if manual:
        for ocorrencia in abertas:
            session.add(
                PropostaCorrecao(
                    resposta_id=resposta.id,
                    ocorrencia_id=ocorrencia.id,
                    situacao="sem_decisao",
                    motivo=MSG_MANUAL,
                )
            )
    session.commit()
    return resposta


def interpretar(resposta_id: str) -> None:
    """Worker: interpreta a resposta; em falha nada é gravado nos documentos nem nas propostas."""
    with SessionLocal() as session:
        resposta = session.get(RespostaEmpresa, resposta_id)
        if resposta is None or resposta.situacao != "em_andamento":
            return
        colecao = session.get(Colecao, resposta.colecao_id)
        workspace = session.get(Workspace, colecao.workspace_id)
        abertas = ocorrencias_abertas(session, colecao.id)
        docs = _documentos(session, colecao.id)
        textos = {nome: t for nome, d in docs.items() if (t := _ler_texto(d)) is not None}
        try:
            modelo = criar_modelo_ia(session, workspace)
            dados = [{"id": o.id, "assunto": o.assunto, "trechos": o.trechos} for o in abertas]
            resultado = service.interpretar_resposta(modelo, resposta.texto, dados, textos)
        except Exception as erro:  # noqa: BLE001 — qualquer falha vira interpretação incompleta
            logger.warning("Interpretação da resposta falhou: %s", type(erro).__name__)
            resposta.situacao = "incompleta"
            resposta.motivo = MOTIVO_FALHA
            session.commit()
            return
        for item in resultado:
            arquivo = item.get("arquivo")
            session.add(
                PropostaCorrecao(
                    resposta_id=resposta.id,
                    ocorrencia_id=item["ocorrencia_id"],
                    situacao=item["situacao"],
                    arquivo=arquivo,
                    documento_id=docs[arquivo].id if arquivo in docs else None,
                    trecho_alvo=item["trecho_alvo"],
                    texto_corrigido=item["texto_corrigido"],
                    hash_documento=_hash(textos[arquivo]) if arquivo in textos else None,
                    motivo=item.get("motivo"),
                )
            )
        resposta.situacao = "concluida"
        session.commit()


# --- confirmação e aplicação --------------------------------------------------


def _guardar_versao(session, documento: DocumentoColecao, numero: int, texto: str, expira):
    chave = f"versao-{uuid.uuid4()}"
    get_storage().save(chave, documento.nome_arquivo, texto.encode("utf-8"))
    session.add(
        VersaoDocumento(
            documento_id=documento.id,
            numero=numero,
            chave_armazenamento=chave,
            hash=_hash(texto),
            criado_em=_agora(),
            expira_em=expira,
        )
    )


def _nova_versao(session, documento: DocumentoColecao, anterior: str, novo: str) -> int:
    """Guarda o texto anterior (1ª correção) e registra o novo como versão atual."""
    vencimento = _agora() + timedelta(days=RETENCAO_DIAS)
    versoes = (
        session.query(VersaoDocumento)
        .filter_by(documento_id=documento.id)
        .order_by(VersaoDocumento.numero)
        .all()
    )
    if not versoes:
        _guardar_versao(session, documento, 1, anterior, vencimento)
        numero = 2
    else:
        for versao in versoes:
            if versao.expira_em is None:
                versao.expira_em = vencimento
        numero = versoes[-1].numero + 1
    _guardar_versao(session, documento, numero, novo, None)
    session.flush()
    return numero


def _criar_envio(session, colecao: Colecao, documento: DocumentoColecao, texto: str, pessoa_id):
    base = documento.ultimo_envio
    envio_id = str(uuid.uuid4())
    get_storage().save(envio_id, documento.nome_arquivo, texto.encode("utf-8"))
    session.add(
        Envio(
            id=envio_id,
            colecao_id=colecao.id,
            arquivos=[documento.nome_arquivo],
            processamento=dict(base.processamento) if base else {},
            metadados_chunk=list(base.metadados_chunk) if base else [],
            situacao="queued",
            criado_por=pessoa_id,
        )
    )
    return envio_id


def _exigir_livre(session, colecao: Colecao) -> None:
    session.query(Colecao).filter_by(id=colecao.id).with_for_update().one()
    if repo.has_envio_ativo(session, colecao.id):
        raise ErroDeDecisao("Aguarde a publicação em andamento antes de decidir de novo.", 409)


def _aplicar(session, colecao: Colecao, pessoa_id: str, itens: list[dict[str, Any]]) -> int:
    """Aplica as correções confirmadas; valida tudo antes de gravar qualquer coisa."""
    _exigir_livre(session, colecao)
    docs = _documentos(session, colecao.id)
    originais: dict[str, str] = {}
    atuais: dict[str, str] = {}
    for item in itens:
        arquivo = item["arquivo"]
        documento = docs.get(arquivo)
        if documento is None:
            raise ErroDeDecisao(f"O documento {arquivo} não existe mais na coleção.", 409)
        if arquivo not in originais:
            texto = _ler_texto(documento)
            if texto is None:
                raise ErroDeDecisao(f"Não foi possível ler o documento {arquivo}.", 409)
            originais[arquivo] = atuais[arquivo] = texto
        esperado = item["proposta"].hash_documento
        if esperado and _hash(originais[arquivo]) != esperado:
            raise ErroDeDecisao(
                f"O documento {arquivo} mudou depois da análise; refaça a análise.", 409
            )
        try:
            atuais[arquivo] = service.aplicar_correcao(
                atuais[arquivo], item["trecho_alvo"], item["texto_corrigido"]
            )
        except ValueError:
            raise ErroDeDecisao(
                "Não foi possível localizar o trecho; indique qual corrigir", 422
            ) from None
    versoes: dict[str, int] = {}
    envios: list[str] = []
    try:
        for arquivo, texto in atuais.items():
            documento = docs[arquivo]
            versoes[arquivo] = _nova_versao(session, documento, originais[arquivo], texto)
            envios.append(_criar_envio(session, colecao, documento, texto, pessoa_id))
        for item in itens:
            proposta = item["proposta"]
            resposta = session.get(RespostaEmpresa, proposta.resposta_id)
            proposta.situacao = "editada" if item["editada"] else "aceita"
            session.add(
                DecisaoEmpresa(
                    proposta_id=proposta.id,
                    colecao_id=colecao.id,
                    ocorrencia_id=proposta.ocorrencia_id,
                    arquivo=item["arquivo"],
                    confirmado_por=pessoa_id,
                    confirmado_em=_agora(),
                    editada=item["editada"],
                    versao_resultante=versoes[item["arquivo"]],
                    resposta_trecho=resposta.texto[:2000] if resposta else "",
                    texto_proposto=proposta.texto_corrigido,
                    texto_aplicado=item["texto_corrigido"],
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        for envio_id in envios:
            get_storage().delete_base(envio_id)
        raise
    for envio_id in envios:
        publicacao.agendar_envio(envio_id, colecao.id)
    return len(itens)


def _proposta(session, colecao: Colecao, proposta_id: str) -> PropostaCorrecao:
    proposta = session.get(PropostaCorrecao, proposta_id)
    resposta = session.get(RespostaEmpresa, proposta.resposta_id) if proposta else None
    if proposta is None or resposta is None or resposta.colecao_id != colecao.id:
        raise ErroDeDecisao("Proposta não encontrada.", 404)
    if proposta.situacao not in PENDENTES:
        raise ErroDeDecisao("Esta proposta já foi decidida.", 409)
    return proposta


def aplicar_lote(session, colecao: Colecao, pessoa_id: str, confirmado: bool) -> int:
    """Confirma o bloco das propostas claras da resposta mais recente."""
    if not confirmado:
        raise ErroDeDecisao("Confirme as correções para aplicá-las.", 422)
    resposta = resposta_atual(session, colecao.id)
    if resposta is None:
        return 0
    itens = [
        {
            "proposta": p,
            "arquivo": p.arquivo,
            "trecho_alvo": p.trecho_alvo,
            "texto_corrigido": p.texto_corrigido,
            "editada": False,
        }
        for p in propostas_da_resposta(session, resposta.id)
        if p.situacao == "clara"
    ]
    return _aplicar(session, colecao, pessoa_id, itens) if itens else 0


def decidir(
    session, colecao: Colecao, pessoa_id: str, proposta_id: str, acao: str, dados: dict[str, Any]
) -> PropostaCorrecao:
    proposta = _proposta(session, colecao, proposta_id)
    if acao == "manter":
        proposta.situacao = "mantida"
        session.commit()
        return proposta
    if acao not in {"aceitar", "editar"}:
        raise ErroDeDecisao("Ação inválida: use aceitar, editar ou manter.", 422)
    arquivo = (dados.get("arquivo") or proposta.arquivo) if acao == "editar" else proposta.arquivo
    trecho = (
        (dados.get("trecho_alvo") or proposta.trecho_alvo)
        if acao == "editar"
        else proposta.trecho_alvo
    )
    corrigido = (
        (dados.get("texto_corrigido") or proposta.texto_corrigido)
        if acao == "editar"
        else proposta.texto_corrigido
    )
    if not arquivo or not trecho.strip() or not corrigido.strip():
        raise ErroDeDecisao("Informe o arquivo, o trecho e o texto corrigido.", 422)
    editada = acao == "editar" and (
        corrigido != proposta.texto_corrigido
        or not proposta.trecho_alvo
        or arquivo != proposta.arquivo
    )
    item = {
        "proposta": proposta,
        "arquivo": arquivo,
        "trecho_alvo": trecho,
        "texto_corrigido": corrigido,
        "editada": editada,
    }
    _aplicar(session, colecao, pessoa_id, [item])
    return proposta


# --- versões ------------------------------------------------------------------


def versoes_do_documento(session, colecao: Colecao, documento_id: str) -> list[VersaoDocumento]:
    documento = session.get(DocumentoColecao, documento_id)
    if documento is None or documento.colecao_id != colecao.id:
        raise ErroDeDecisao("Documento não encontrado.", 404)
    return (
        session.query(VersaoDocumento)
        .filter_by(documento_id=documento_id)
        .order_by(VersaoDocumento.numero)
        .all()
    )


def restaurar_versao(
    session, colecao: Colecao, pessoa_id: str, documento_id: str, numero: int, confirmado: bool
) -> int:
    """A versão escolhida vira a atual como uma versão nova; a volta fica no registro."""
    if not confirmado:
        raise ErroDeDecisao("Confirme para voltar a esta versão.", 422)
    versoes = versoes_do_documento(session, colecao, documento_id)
    escolhida = next((v for v in versoes if v.numero == numero), None)
    if escolhida is None:
        raise ErroDeDecisao("Versão não encontrada.", 404)
    _exigir_livre(session, colecao)
    documento = session.get(DocumentoColecao, documento_id)
    atual = _ler_texto(documento)
    with tempfile.TemporaryDirectory(prefix="decisoes-") as pasta:
        get_storage().materialize(escolhida.chave_armazenamento, pasta)
        arquivo = Path(pasta) / documento.nome_arquivo
        if atual is None or not arquivo.exists():
            raise ErroDeDecisao("Não foi possível ler a versão escolhida.", 409)
        texto = arquivo.read_text(encoding="utf-8")
    envio_id = None
    try:
        nova = _nova_versao(session, documento, atual, texto)
        envio_id = _criar_envio(session, colecao, documento, texto, pessoa_id)
        session.add(
            DecisaoEmpresa(
                colecao_id=colecao.id,
                arquivo=documento.nome_arquivo,
                confirmado_por=pessoa_id,
                confirmado_em=_agora(),
                versao_resultante=nova,
                restaurada_de=numero,
                texto_aplicado="",
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        if envio_id:
            get_storage().delete_base(envio_id)
        raise
    publicacao.agendar_envio(envio_id, colecao.id)
    return nova


# --- liberação ----------------------------------------------------------------


def revisar(session, colecao: Colecao, pessoa_id: str, confirmado: bool) -> dict[str, Any]:
    abertas = len(ocorrencias_abertas(session, colecao.id))
    if abertas and not confirmado:
        raise ErroDeDecisao(
            f"Há {abertas} {'contradição aberta' if abertas == 1 else 'contradições abertas'}; "
            "confirme para liberar mesmo assim.",
            409,
            abertas=abertas,
        )
    colecao.revisada_em = _agora()
    colecao.revisada_por = pessoa_id
    session.commit()
    return {
        "revisada_em": colecao.revisada_em.isoformat(),
        "revisada_por": pessoa_id,
        "abertas": abertas,
    }


# --- retenção -----------------------------------------------------------------


def apagar_da_colecao(session, colecao_id: str, apagado_por: str | None = None) -> None:
    """Apaga versões, decisões e texto da empresa; resta só um registro mínimo."""
    documentos = [
        i for (i,) in session.query(DocumentoColecao.id).filter_by(colecao_id=colecao_id).all()
    ]
    versoes = (
        session.query(VersaoDocumento).filter(VersaoDocumento.documento_id.in_(documentos)).all()
        if documentos
        else []
    )
    respostas = [
        i for (i,) in session.query(RespostaEmpresa.id).filter_by(colecao_id=colecao_id).all()
    ]
    decisoes = session.query(DecisaoEmpresa).filter_by(colecao_id=colecao_id).count()
    if not (decisoes or versoes or respostas):
        return
    for versao in versoes:
        get_storage().delete_base(versao.chave_armazenamento)
        session.delete(versao)
    session.query(DecisaoEmpresa).filter_by(colecao_id=colecao_id).delete(synchronize_session=False)
    if respostas:
        session.query(PropostaCorrecao).filter(PropostaCorrecao.resposta_id.in_(respostas)).delete(
            synchronize_session=False
        )
        session.query(RespostaEmpresa).filter(RespostaEmpresa.id.in_(respostas)).delete(
            synchronize_session=False
        )
    session.add(
        RegistroExclusaoDecisoes(
            colecao_id=colecao_id, apagado_por=apagado_por, apagado_em=_agora(), decisoes=decisoes
        )
    )


def purgar_retencao(agora: datetime | None = None) -> None:
    """Apaga as versões não atuais com mais de 90 dias; os registros ficam com a coleção."""
    agora = agora or _agora()
    with SessionLocal() as session:
        vencidas = (
            session.query(VersaoDocumento)
            .filter(VersaoDocumento.expira_em.isnot(None), VersaoDocumento.expira_em < agora)
            .all()
        )
        for versao in vencidas:
            get_storage().delete_base(versao.chave_armazenamento)
            session.delete(versao)
        session.commit()
