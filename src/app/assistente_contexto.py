"""Contexto do copilot: o que o modelo pode ver, sempre filtrado pela identidade (SPEC-0031).

Fronteira da aplicação com o grafo do assistente. Cada recuperador nasce da identidade
(tenant, projeto e papel; DEC-013) e devolve evidências ``{"texto", "fonte"}`` já
filtradas, a ser entregues ao modelo como dado. Nada aqui recebe escopo do modelo ou do
texto da pergunta, e nenhuma credencial sai deste módulo: o estado e as configurações
passam por allowlist de campos (FR-011).
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select

import src.pipeline.service as service  # noqa: PLR0402 — forma exigida pelo teste de fronteira
from src.app import colecoes, repo
from src.app.auth import Identity
from src.app.db import SessionLocal
from src.app.models import Colecao, Conexao, Envio

__all__ = [
    "LIMITE_DE_COLECOES",
    "LIMITE_DE_TRECHOS",
    "ContextoDoTurno",
    "criar_contexto",
]

LIMITE_DE_TRECHOS = 12
LIMITE_DE_COLECOES = 10
_TRECHOS_POR_COLECAO = 3
_ENVIOS_POR_COLECAO = 3
_PAPEIS_DE_CONFIGURACAO = frozenset({"owner", "admin"})
_ETIQUETA = re.compile(r"([\w\-]+)=([\w\-.]+)")

Evidencia = dict[str, Any]


class ContextoDoTurno:
    """Os três recuperadores do turno, ligados à identidade e ao filtro opcional."""

    def __init__(self, identity: Identity, colecao_id: str | None) -> None:
        self._identity = identity
        self._colecao_id = colecao_id

    def colecoes(self, pergunta: str) -> list[Evidencia]:
        return _buscar_nas_colecoes(self._identity, self._colecao_id, pergunta)

    def estado(self, pergunta: str) -> list[Evidencia]:
        return _estado_operacional(self._identity, self._colecao_id)

    def processado(self, pergunta: str) -> list[Evidencia]:
        return _conteudo_processado(self._identity, self._colecao_id, pergunta)


def criar_contexto(identity: Identity, colecao_id: str | None = None) -> ContextoDoTurno:
    return ContextoDoTurno(identity, colecao_id)


# --------------------------------------------------------------------------- escopo


def _colecoes_do_escopo(session, identity: Identity, colecao_id: str | None) -> list[Colecao]:
    """Coleções ativas do tenant e projeto da identidade, ou só a do filtro."""
    if colecao_id is not None:
        return [repo.get_colecao_or_404(session, colecao_id, identity)]
    consulta = (
        select(Colecao)
        .where(
            Colecao.tenant_id == identity.tenant_id,
            Colecao.project_id == identity.project_id,
            Colecao.apagada_em.is_(None),
        )
        .order_by(Colecao.criado_em.desc(), Colecao.id.desc())
        .limit(LIMITE_DE_COLECOES)
    )
    return list(session.execute(consulta).scalars().all())


def _rota_da_colecao(colecao: Colecao) -> str:
    return f"/workspaces/{colecao.workspace_id}/colecoes/{colecao.id}"


def _fonte_de_documento(colecao: Colecao, documento: str) -> dict[str, Any]:
    return {
        "tipo": "documento",
        "rotulo": f"{documento} — {colecao.nome}",
        "colecao_id": colecao.id,
        "documento": documento,
        "envio_id": None,
        "rota": _rota_da_colecao(colecao),
    }


def _fonte_de_colecao(colecao: Colecao) -> dict[str, Any]:
    return {
        "tipo": "colecao",
        "rotulo": colecao.nome,
        "colecao_id": colecao.id,
        "documento": None,
        "envio_id": None,
        "rota": _rota_da_colecao(colecao),
    }


def _fonte_de_envio(colecao: Colecao, envio: Envio) -> dict[str, Any]:
    arquivos = ", ".join(envio.arquivos or []) or "arquivos"
    return {
        "tipo": "envio",
        "rotulo": f"Envio de {arquivos} — {colecao.nome}",
        "colecao_id": colecao.id,
        "documento": None,
        "envio_id": envio.id,
        "rota": f"/envios/{envio.id}",
    }


# --------------------------------------------------------------------------- coleções


def _buscar_nas_colecoes(
    identity: Identity, colecao_id: str | None, pergunta: str
) -> list[Evidencia]:
    """Busca vetorial em todas as coleções do escopo, com teto de trechos por turno."""
    alvos: list[tuple[Colecao, dict[str, Any]]] = []
    with SessionLocal() as session:
        for colecao in _colecoes_do_escopo(session, identity, colecao_id):
            if not repo.list_documentos_da_colecao(session, colecao.id):
                continue
            try:
                config = colecoes.configuracao_da_colecao(session, identity, colecao)
            except HTTPException:
                continue  # conexão desativada: a coleção sai da busca
            session.expunge(colecao)
            alvos.append((colecao, config))

    def buscar(alvo: tuple[Colecao, dict[str, Any]]):
        colecao, config = alvo
        return colecao, service.query_base(config, pergunta, top_k=_TRECHOS_POR_COLECAO)

    if not alvos:
        return []
    with ThreadPoolExecutor(max_workers=min(5, len(alvos))) as pool:
        encontrados = list(pool.map(buscar, alvos))

    candidatos = [
        (colecao, trecho) for colecao, trechos in encontrados for trecho in (trechos or [])
    ]
    candidatos.sort(key=lambda par: par[1].score or 0.0, reverse=True)
    evidencias: list[Evidencia] = []
    for colecao, trecho in candidatos[:LIMITE_DE_TRECHOS]:
        documento = str(trecho.metadata.get("nome_arquivo") or "desconhecido")
        evidencias.append(
            {
                "texto": f"[Fonte: {documento} — {colecao.nome}]\n{trecho.content}",
                "fonte": _fonte_de_documento(colecao, documento),
            }
        )
    return evidencias


# --------------------------------------------------------------------------- estado


def _modelo_de_embeddings(session, colecao: Colecao) -> str | None:
    conexao = session.get(Conexao, colecao.conexao_embeddings_id)
    modelo = (conexao.configuracao or {}).get("modelo") if conexao is not None else None
    return str(modelo) if modelo else None


def _divisao_do_envio(envio: Envio | None) -> str | None:
    processamento = dict(envio.processamento or {}) if envio is not None else {}
    campos = {
        "divisão": processamento.get("splitter"),
        "tamanho do trecho": processamento.get("chunk_size"),
        "sobreposição": processamento.get("chunk_overlap"),
    }
    partes = [f"{nome} {valor}" for nome, valor in campos.items() if valor is not None]
    return ", ".join(partes) if partes else None


def _descrever_envio(envio: Envio) -> str:
    texto = (
        f"envio de {', '.join(envio.arquivos or []) or 'arquivos'}: situação {envio.situacao}, "
        f"etapa {envio.etapa or 'não iniciada'}, previstos {envio.previstos}, "
        f"inseridos {envio.inseridos}, mantidos {envio.mantidos}, removidos {envio.removidos}"
    )
    if envio.erro:
        texto += f", erro: {envio.erro}"
    return texto


def _estado_operacional(identity: Identity, colecao_id: str | None) -> list[Evidencia]:
    """Coleções, documentos, envios e configurações por campos permitidos."""
    pode_ver_configuracao = identity.role in _PAPEIS_DE_CONFIGURACAO
    evidencias: list[Evidencia] = []
    with SessionLocal() as session:
        for colecao in _colecoes_do_escopo(session, identity, colecao_id):
            documentos = repo.list_documentos_da_colecao(session, colecao.id)
            envios = repo.list_envios_da_colecao(session, colecao.id)
            total_de_trechos = sum(d.chunks for d in documentos)
            linhas = [
                (
                    f"Coleção «{colecao.nome}»: {len(documentos)} documento(s), "
                    f"{total_de_trechos} trecho(s) indexados."
                ),
                f"Tela da coleção (documentos e envios): {_rota_da_colecao(colecao)}",
            ]
            if documentos:
                linhas.append("Documentos: " + ", ".join(d.nome_arquivo for d in documentos))
            for envio in envios[:_ENVIOS_POR_COLECAO]:
                linhas.append(_descrever_envio(envio))
                if envio.situacao == "failed":
                    linhas.append(
                        "Passo sugerido: use Repetir na tela de envios da coleção "
                        f"({_rota_da_colecao(colecao)})."
                    )
                    evidencias.append(
                        {"texto": "\n".join(linhas), "fonte": _fonte_de_envio(colecao, envio)}
                    )
                    linhas = []
            if pode_ver_configuracao:
                modelo = _modelo_de_embeddings(session, colecao)
                divisao = _divisao_do_envio(next((e for e in envios if e.processamento), None))
                if modelo or divisao:
                    linhas.append(
                        "Configuração: "
                        + "; ".join(
                            parte
                            for parte in (
                                f"modelo de embeddings {modelo}" if modelo else None,
                                divisao,
                            )
                            if parte
                        )
                    )
            if linhas:
                evidencias.append({"texto": "\n".join(linhas), "fonte": _fonte_de_colecao(colecao)})
    if not pode_ver_configuracao:
        evidencias.append(
            {
                "texto": (
                    "Dado restrito a admin: a conexão e a divisão das coleções não podem ser "
                    "mostradas ao papel desta pessoa; diga isso se perguntarem."
                ),
                "fonte": None,
            }
        )
    return evidencias


# --------------------------------------------------------------------------- processado


def _conteudo_processado(
    identity: Identity, colecao_id: str | None, pergunta: str
) -> list[Evidencia]:
    """Trechos guardados dos documentos citados na pergunta, filtrados por etiqueta."""
    etiquetas = dict(_ETIQUETA.findall(pergunta))
    pergunta_baixa = pergunta.casefold()
    evidencias: list[Evidencia] = []
    with SessionLocal() as session:
        for colecao in _colecoes_do_escopo(session, identity, colecao_id):
            documentos = repo.list_documentos_da_colecao(session, colecao.id)
            citados = [d for d in documentos if d.nome_arquivo.casefold() in pergunta_baixa]
            for documento in citados or documentos:
                conteudo = repo.obter_conteudo(session, documento.id)
                if conteudo is None:
                    if documento in citados:
                        evidencias.append(
                            {
                                "texto": (
                                    f"O documento {documento.nome_arquivo} não tem conteúdo "
                                    "processado guardado (foi enviado antes desta função); "
                                    "responda só pelo conteúdo indexado."
                                ),
                                "fonte": None,
                            }
                        )
                    continue
                for trecho in conteudo.trechos or []:
                    marcas = trecho.get("etiquetas") or {}
                    if any(marcas.get(rotulo) != valor for rotulo, valor in etiquetas.items()):
                        continue
                    descricao = ", ".join(f"{k}={v}" for k, v in marcas.items()) or "sem etiquetas"
                    aviso = " (texto do documento incompleto)" if conteudo.truncado else ""
                    evidencias.append(
                        {
                            "texto": (
                                f"[Documento: {documento.nome_arquivo} — {colecao.nome}, trecho "
                                f"{trecho.get('ordem')}, etiquetas: {descricao}]{aviso}\n"
                                f"{trecho.get('texto', '')}"
                            ),
                            "fonte": _fonte_de_documento(colecao, documento.nome_arquivo),
                        }
                    )
                    if len(evidencias) >= LIMITE_DE_TRECHOS:
                        return evidencias
    return evidencias
