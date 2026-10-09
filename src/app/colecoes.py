"""Regras de Coleção por Workspace (SPEC-0030): nome, conexões fixas e dimensão."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.app import conexoes, publicacao
from src.app.auth import Identity
from src.app.models import Base, Colecao, Workspace

__all__ = [
    "MSG_CONEXOES_FIXAS",
    "MSG_NOME_DUPLICADO",
    "MSG_NOME_FISICO_EM_USO",
    "MSG_NOME_FISICO_RESERVADO",
    "MSG_SLUG_VAZIO",
    "MSG_SYNC_MODE",
    "configuracao_da_colecao",
    "criar_colecao",
    "exigir_envio_possivel",
    "normalizar_nome",
    "slug_fisico",
]

MSG_NOME_DUPLICADO = "Já existe uma coleção com esse nome neste Workspace."
MSG_CONEXOES_FIXAS = "A coleção usa conexões fixas; envie sem trocar as conexões."
MSG_SYNC_MODE = "Modo de sincronização não é aceito no envio."
MSG_SLUG_VAZIO = "O nome da coleção precisa ter ao menos uma letra ou número."
MSG_NOME_FISICO_EM_USO = (
    "Já existe uma coleção com esse nome no Qdrant desta conexão. Escolha outro nome."
)
MSG_NOME_FISICO_RESERVADO = "Esse nome é reservado pelo sistema. Escolha outro nome."
_NOME_MAXIMO = 80


def normalizar_nome(nome: object) -> tuple[str, str]:
    """Valida o nome exibido (1–80 caracteres) e devolve ``(nome, normalizado)``."""
    texto = nome.strip() if isinstance(nome, str) else ""
    if not texto or len(texto) > _NOME_MAXIMO:
        raise HTTPException(
            status_code=422, detail="O nome da coleção deve ter de 1 a 80 caracteres."
        )
    return texto, texto.casefold()


def slug_fisico(nome: str) -> str:
    """Nome da coleção no Qdrant: o nome digitado sem acentos e sem caracteres inválidos.

    Qualquer sequência fora de letras, números, ``_``, ``.`` e ``-`` vira um único
    ``-``; ``-`` e ``.`` nas pontas saem; no máximo 80 caracteres.
    """
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", sem_acento)
    slug = re.sub(r"-{2,}", "-", slug).strip("-.")
    return slug[:_NOME_MAXIMO].strip("-.")


def _exigir_nome_fisico_livre(session: Session, slug: str, conexao_vector_store_id: str) -> None:
    """Recusa nome sem letra ou número, reservado pelo sistema ou já em uso na conexão."""
    from sqlalchemy import func, select

    from src.app.settings import get_settings

    if not re.search(r"[A-Za-z0-9]", slug):
        raise HTTPException(status_code=422, detail=MSG_SLUG_VAZIO)
    configuracoes = get_settings()
    reservados = {
        str(configuracoes.conhecimento_collection or ""),
        str(configuracoes.vector_store.get("collection_name") or ""),
    }
    reservados |= set(
        session.execute(select(Base.collection_name).where(Base.apagada_em.is_(None)))
        .scalars()
        .all()
    )
    if slug.casefold() in {nome.casefold() for nome in reservados if nome}:
        raise HTTPException(status_code=409, detail=MSG_NOME_FISICO_RESERVADO)
    em_uso = session.execute(
        select(Colecao.id).where(
            Colecao.apagada_em.is_(None),
            Colecao.conexao_vector_store_id == conexao_vector_store_id,
            func.lower(Colecao.nome_fisico) == slug.casefold(),
        )
    ).first()
    if em_uso is not None:
        raise HTTPException(status_code=409, detail=MSG_NOME_FISICO_EM_USO)


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
    slug = slug_fisico(exibido)
    resolvidas = publicacao.resolver_conexoes(
        session, identity, conexao_embeddings_id, conexao_vector_store_id
    )
    _exigir_nome_fisico_livre(session, slug, conexao_vector_store_id)
    colecao = Colecao(
        tenant_id=identity.tenant_id,
        project_id=identity.project_id,
        workspace_id=workspace.id,
        nome=exibido,
        nome_normalizado=normalizado,
        nome_fisico=slug,
        conexao_embeddings_id=conexao_embeddings_id,
        conexao_vector_store_id=conexao_vector_store_id,
        dimensao=int(resolvidas.embeddings.configuracao.get("dimensoes", 0)),
        criado_por=identity.person_id,
    )
    session.add(colecao)
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
