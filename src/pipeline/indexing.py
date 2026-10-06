"""Serviço de aplicação que liga `config.yaml` aos providers plugáveis.

Este módulo é a única fronteira que conhece o formato de `config.yaml` e o
formato de chunk do pipeline. Ele traduz configuração em adapters pela
`ProviderFactory`, converte `Document` em `VectorRecord`, monta o
`LogicalScope` e delega a sincronização ao serviço neutro `synchronize`.

Nenhum SDK de provider é importado aqui: a camada de plugins vive somente em
`src/pipeline/providers/`.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from langchain_core.documents import Document

from src.pipeline.providers import (
    LogicalScope,
    ProviderFactory,
    SyncCounts,
    VectorRecord,
    synchronize,
)
from src.pipeline.safety import SyncSafetyPolicy

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 50
DESCRICAO_NEUTRA = "base de conhecimento configurada para esta execução"
PERGUNTA_NEUTRA = "Quais informações estão disponíveis nesta base?"

# Dimensões conhecidas por modelo, usadas quando a configuração não declara.
_MODEL_DIMENSIONS = {
    "openai/text-embedding-3-small": 1536,
    "openai/text-embedding-3-large": 3072,
    "openai/text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


@dataclass(frozen=True)
class BaseIdentity:
    """Identidade textual da base, resolvida sem acoplamento a um cliente."""

    nome: str
    descricao: str
    descricao_derivada: bool


def resolve_identity(config: dict) -> BaseIdentity:
    """Resolve a identidade da base a partir da configuração operacional."""
    projeto = config.get("projeto") or {}
    nome = projeto.get("nome")
    if not isinstance(nome, str) or not nome.strip():
        raise ValueError("Configuração sem projeto.nome.")

    descricao = projeto.get("descricao")
    if not isinstance(descricao, str) or not descricao.strip():
        logger.warning(
            "Configuração sem projeto.descricao; usando descrição neutra."
        )
        return BaseIdentity(nome.strip(), DESCRICAO_NEUTRA, False)

    return BaseIdentity(nome.strip(), descricao.strip(), True)


def resolve_default_question(config: dict) -> tuple[str, bool]:
    """Resolve a primeira pergunta do gabarito, com degradação somente leitura."""
    caminhos = config.get("caminhos") or {}
    caminho = caminhos.get("consultas_referencia")
    if isinstance(caminho, str) and caminho.strip():
        try:
            from src.pipeline.validation import load_query_cases

            casos = load_query_cases(caminho.strip())
            if casos:
                return casos[0].pergunta, True
        except (OSError, ValueError, TypeError):
            pass

    logger.warning(
        "Pergunta padrão não pôde ser obtida do gabarito; usando pergunta neutra."
    )
    return PERGUNTA_NEUTRA, False


def resolve_dimensions(embedding_cfg: dict) -> int:
    """Resolve a dimensão do vetor pela configuração ou pelo modelo."""
    model = embedding_cfg.get("model", "openai/text-embedding-3-small")
    return int(embedding_cfg.get("dimensions") or _MODEL_DIMENSIONS.get(model, 1536))


def build_embeddings(embedding_cfg: dict):
    """Cria o adapter de embeddings declarado na configuração."""
    settings = {
        key: value
        for key, value in {
            "model": embedding_cfg.get("model"),
            "dimensions": embedding_cfg.get("dimensions"),
            # Credenciais e endpoint de uma conexão (SPEC-0026); ausentes, o
            # adapter continua lendo o ambiente como antes.
            "api_key": embedding_cfg.get("api_key"),
            "base_url": embedding_cfg.get("base_url"),
        }.items()
        if value is not None
    }
    return ProviderFactory.create_embedding(
        embedding_cfg.get("provider", "openrouter"), settings
    )


def build_vector_store(vector_cfg: dict, persist_dir: str | None = None):
    """Cria o adapter de vector store declarado na configuração."""
    settings = {
        "collection_name": vector_cfg.get("collection_name", "rag_docs"),
        "persist_directory": persist_dir,
        "index_name": vector_cfg.get("index_name"),
        "namespace": vector_cfg.get("namespace"),
    }
    # Destino de uma conexão (SPEC-0026); ausentes, o adapter lê o ambiente.
    for chave in ("url", "api_key"):
        if vector_cfg.get(chave):
            settings[chave] = vector_cfg[chave]
    return ProviderFactory.create_vector_store(
        vector_cfg.get("provider", "qdrant"), settings
    )


def build_scope(project_id: str | None, tenant_id: str | None = None) -> LogicalScope:
    """Monta o escopo lógico explícito usado por sincronização e recuperação."""
    return LogicalScope(project_id=project_id, tenant_id=tenant_id)


def scope_from_chunks(chunks: Sequence[Document]) -> LogicalScope:
    """Deriva o escopo lógico do lote pela política central da SPEC-0001.

    `SyncSafetyPolicy.assert_valid_scope` já é a fonte única das guardas de
    escopo (lote vazio, `project_id`/`chunk_id` ausente, `chunk_id` duplicado e
    tenants divergentes ou misturados). Reaproveitá-la aqui mantém a validação
    completa antes de qualquer provider ser composto, sem duplicar regra.
    """
    project_id, tenant_id = SyncSafetyPolicy().assert_valid_scope(chunks)
    return LogicalScope(project_id=project_id, tenant_id=tenant_id)


def to_records(chunks: Sequence[Document]) -> list[VectorRecord]:
    """Converte chunks em registros neutros, sem gerar embeddings ainda."""
    return [
        VectorRecord(
            id=str(chunk.metadata.get("chunk_id", "")),
            content=chunk.page_content,
            vector=(),
            metadata=dict(chunk.metadata),
        )
        for chunk in chunks
    ]


def _embed_in_batches(embeddings, texts: list[str], batch_size: int):
    """Gera embeddings em lotes, preservando o `batch_size` configurado."""
    vectors: list[Sequence[float]] = []
    total = len(texts)
    for start in range(0, total, batch_size):
        batch = texts[start : start + batch_size]
        vectors.extend(embeddings.embed_documents(batch))
        logger.info(
            "  [%d/%d] batch de embeddings gerado", min(start + batch_size, total), total
        )
    return vectors


def index_chunks(
    chunks: Sequence[Document],
    embedding_cfg: dict,
    vector_cfg: dict,
    persist_dir: str | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> SyncCounts:
    """Sincroniza os chunks no vector store configurado e devolve as contagens.

    Embeddings são gerados apenas para os registros ausentes no destino.
    """
    provider = vector_cfg.get("provider", "qdrant")
    mode = vector_cfg.get("sync_mode", "append")
    batch_size = int(embedding_cfg.get("batch_size", batch_size))
    dimensions = resolve_dimensions(embedding_cfg)

    # Fail-closed antes de compor qualquer provider: escopo lógico primeiro,
    # depois modo de sincronização. Nenhum adapter é criado até aqui.
    scope = scope_from_chunks(chunks)
    SyncSafetyPolicy().assert_sync_mode_supported(provider, mode)

    adapter = build_vector_store(vector_cfg, persist_dir)
    embeddings = build_embeddings(embedding_cfg)

    logger.info(
        "Iniciando indexacao: %d chunks -> %s [%s]",
        len(chunks),
        provider,
        vector_cfg.get("collection_name", "rag_docs"),
    )

    return synchronize(
        adapter,
        scope,
        to_records(chunks),
        mode=mode,
        dimensions=dimensions,
        embed=lambda texts: _embed_in_batches(embeddings, texts, batch_size),
    )


def retrieve(
    query: str,
    embedding_cfg: dict,
    vector_cfg: dict,
    *,
    project_id: str,
    tenant_id: str | None = None,
    k: int = 4,
    persist_dir: str | None = None,
):
    """Recupera resultados escopados por projeto e tenant explícitos."""
    scope = build_scope(project_id, tenant_id)
    embeddings = build_embeddings(embedding_cfg)
    adapter = build_vector_store(vector_cfg, persist_dir)
    return adapter.query(scope, embeddings.embed_query(query), k)
