"""Regras de Coleção por Workspace (SPEC-0030): nome, conexões fixas e dimensão."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.app import conexoes, publicacao
from src.app.auth import Identity
from src.app.models import Colecao, Workspace

__all__ = [
    "MSG_CONEXOES_FIXAS",
    "MSG_NOME_DUPLICADO",
    "MSG_SYNC_MODE",
    "PREFIXO_FISICO",
    "configuracao_da_colecao",
    "criar_colecao",
    "exigir_envio_possivel",
    "nome_fisico",
    "normalizar_nome",
]

PREFIXO_FISICO = "col-"
MSG_NOME_DUPLICADO = "Já existe uma coleção com esse nome neste Workspace."
MSG_CONEXOES_FIXAS = "A coleção usa conexões fixas; envie sem trocar as conexões."
MSG_SYNC_MODE = "Modo de sincronização não é aceito no envio."
_NOME_MAXIMO = 80


def normalizar_nome(nome: object) -> tuple[str, str]:
    """Valida o nome exibido (1–80 caracteres) e devolve ``(nome, normalizado)``."""
    texto = nome.strip() if isinstance(nome, str) else ""
    if not texto or len(texto) > _NOME_MAXIMO:
        raise HTTPException(
            status_code=422, detail="O nome da coleção deve ter de 1 a 80 caracteres."
        )
    return texto, texto.casefold()


def nome_fisico(workspace_id: str, colecao_id: str) -> str:
    return f"{PREFIXO_FISICO}{workspace_id[:8]}-{colecao_id[:8]}"


def nome_livre(session: Session, workspace_id: str, normalizado: str, ignorar: str | None) -> bool:
    outras = session.query(Colecao.id).filter(
        Colecao.workspace_id == workspace_id,
        Colecao.nome_normalizado == normalizado,
        Colecao.apagada_em.is_(None),
    )
    if ignorar is not None:
        outras = outras.filter(Colecao.id != ignorar)
    return outras.first() is None


def exigir_nome_livre(
    session: Session, workspace_id: str, normalizado: str, ignorar: str | None = None
) -> None:
    if not nome_livre(session, workspace_id, normalizado, ignorar):
        raise HTTPException(status_code=409, detail=MSG_NOME_DUPLICADO)


def criar_colecao(
    session: Session,
    identity: Identity,
    workspace: Workspace,
    nome: str,
    conexao_embeddings_id: str | None,
    conexao_vector_store_id: str | None,
) -> Colecao:
    """Cria a coleção no primeiro envio, fixando conexões, dimensão e nome físico."""
    exibido, normalizado = normalizar_nome(nome)
    if not conexao_embeddings_id or not conexao_vector_store_id:
        raise HTTPException(
            status_code=422, detail="Informe a conexão de embeddings e a do Qdrant."
        )
    exigir_nome_livre(session, workspace.id, normalizado)
    resolvidas = publicacao.resolver_conexoes(
        session, identity, conexao_embeddings_id, conexao_vector_store_id
    )
    colecao = Colecao(
        tenant_id=identity.tenant_id,
        project_id=identity.project_id,
        workspace_id=workspace.id,
        nome=exibido,
        nome_normalizado=normalizado,
        nome_fisico="pendente",
        conexao_embeddings_id=conexao_embeddings_id,
        conexao_vector_store_id=conexao_vector_store_id,
        dimensao=int(resolvidas.embeddings.configuracao.get("dimensoes", 0)),
        criado_por=identity.person_id,
    )
    session.add(colecao)
    session.flush()
    colecao.nome_fisico = nome_fisico(workspace.id, colecao.id)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail=MSG_NOME_DUPLICADO) from None
    return colecao


def exigir_envio_possivel(
    session: Session,
    identity: Identity,
    colecao: Colecao,
    conexao_embeddings_id: str | None,
    conexao_vector_store_id: str | None,
) -> None:
    """Conexões fixas, ativas e com a dimensão da coleção (FR-003), antes de gravar."""
    if (conexao_embeddings_id and conexao_embeddings_id != colecao.conexao_embeddings_id) or (
        conexao_vector_store_id and conexao_vector_store_id != colecao.conexao_vector_store_id
    ):
        raise HTTPException(status_code=422, detail=MSG_CONEXOES_FIXAS)
    resolvidas = publicacao.resolver_conexoes(
        session, identity, colecao.conexao_embeddings_id, colecao.conexao_vector_store_id
    )
    modelo = int(resolvidas.embeddings.configuracao.get("dimensoes", 0))
    if modelo != colecao.dimensao:
        raise HTTPException(
            status_code=422,
            detail=f"Dimensões incompatíveis: modelo {modelo}, coleção {colecao.dimensao}.",
        )


def configuracao_da_colecao(
    session: Session, identity: Identity, colecao: Colecao
) -> dict[str, Any]:
    """Configuração do pipeline da coleção; as chaves existem só em memória.

    Conexão desativada bloqueia com a mensagem já existente (409), antes de qualquer
    chamada remota.
    """
    from src.app.tasks import _config_da_conexao, scope_colecao

    publicacao.resolver_conexoes(
        session, identity, colecao.conexao_embeddings_id, colecao.conexao_vector_store_id
    )
    try:
        embedding = _config_da_conexao(
            session, colecao.conexao_embeddings_id, conexoes.TIPO_EMBEDDINGS
        )
        vector_store = _config_da_conexao(
            session,
            colecao.conexao_vector_store_id,
            conexoes.TIPO_QDRANT,
            collection_name=colecao.nome_fisico,
        )
    except conexoes.ErroDeConexao as erro:
        raise HTTPException(status_code=erro.status_code, detail=erro.detalhe) from erro
    return {
        "projeto": {"nome": scope_colecao(colecao.tenant_id, colecao.project_id, colecao.id)},
        "caminhos": {},
        "embedding": embedding,
        "vector_store": vector_store,
    }
