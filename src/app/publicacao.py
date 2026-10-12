"""Resolução das conexões e verificação de dimensão da publicação (SPEC-0026)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.app import conexoes, repo
from src.app.auth import Identity
from src.app.models import Conexao
from src.app.settings import get_settings

__all__ = [
    "ConexoesResolvidas",
    "agendar_envio",
    "resolver_conexoes",
    "verificar_dimensao",
]


@dataclass(frozen=True)
class ConexoesResolvidas:
    embeddings: Conexao
    vector_store: Conexao


def _conexao_do_tipo(session: Session, identity: Identity, conexao_id: str, tipo: str) -> Conexao:
    """404 para outra equipe ou tipo trocado; 409 para conexão desativada."""
    conexao = repo.get_conexao_or_404(session, conexao_id, identity)
    if conexao.tipo != tipo:
        raise HTTPException(status_code=404, detail="Conexão não encontrada.")
    if conexao.situacao != "ativa":
        raise HTTPException(
            status_code=409,
            detail=f"A conexão {conexao.nome} está desativada. Reative-a ou escolha outra.",
        )
    return conexao


def resolver_conexoes(
    session: Session, identity: Identity, conexao_embeddings_id: str, conexao_vector_store_id: str
) -> ConexoesResolvidas:
    return ConexoesResolvidas(
        embeddings=_conexao_do_tipo(
            session, identity, conexao_embeddings_id, conexoes.TIPO_EMBEDDINGS
        ),
        vector_store=_conexao_do_tipo(
            session, identity, conexao_vector_store_id, conexoes.TIPO_QDRANT
        ),
    )


def verificar_dimensao(resolvidas: ConexoesResolvidas, colecao: str) -> dict[str, Any]:
    """Compara a dimensão declarada com a da coleção, sem criar nada (FR-009)."""
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira

    configuracoes = get_settings()
    segredo = (
        conexoes.decifrar_segredo(
            configuracoes.conexoes_chave, resolvidas.vector_store.segredo_cifrado
        )
        if resolvidas.vector_store.segredo_cifrado
        else None
    )
    destino = conexoes.configuracao_para_pipeline(
        conexoes.TIPO_QDRANT,
        resolvidas.vector_store.configuracao,
        segredo,
        collection_name=colecao,
        permitir_locais=configuracoes.conexoes_permitir_locais,
    )
    descricao = service.describe_collection(destino)
    declarada = int(resolvidas.embeddings.configuracao.get("dimensoes", 0))
    existente = descricao.get("dimensions") if descricao.get("exists") else None
    return {
        "embeddings": declarada,
        "colecao": existente,
        "compativel": existente is None or int(existente) == declarada,
    }


def agendar_envio(envio_id: str, colecao_id: str) -> None:
    """Enfileira `process_envio_task`; o ``lock`` serializa os envios da mesma coleção.

    Só o identificador do envio vai para a fila; ``queueing_lock`` não serve aqui
    porque recusaria o segundo envio em vez de enfileirá-lo (SPEC-0030).
    """
    from src.app.tasks import process_envio_task

    process_envio_task.configure(lock=f"colecao:{colecao_id}").defer(envio_id=envio_id)
