"""
Pipeline RAG — Embedder
Gera embeddings e indexa chunks no vector store configurado.
Suporta embeddings: openrouter | openai | huggingface
Suporta vector stores: ChromaDB | Qdrant | Pinecone
"""

import logging
import os
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def _pinecone_settings(vector_cfg: dict) -> tuple[str, str]:
    """Retorna indice e namespace obrigatorios da configuracao Pinecone."""
    index_name = vector_cfg.get("index_name") or os.getenv("PINECONE_INDEX", "")
    namespace = vector_cfg.get("namespace", "")

    if not index_name:
        raise ValueError("Defina vector_store.index_name no config.yaml")
    if not namespace:
        raise ValueError(
            "Defina vector_store.namespace no config.yaml para isolar esta base"
        )
    return index_name, namespace


def _pinecone_document_ids(chunks: list[Document], namespace: str) -> list[str]:
    """Gera IDs estaveis para que uma nova execucao nao duplique os chunks."""
    ids = []
    for chunk in chunks:
        source = chunk.metadata.get("caminho_relativo", "")
        position = chunk.metadata.get("chunk_index", "")
        identity = f"{namespace}|{source}|{position}"
        ids.append(sha256(identity.encode("utf-8")).hexdigest())
    return ids


def _get_qdrant_client():
    """Cria o cliente Qdrant respeitando a porta indicada pela URL.

    O qdrant-client 1.10.1 usa 6333 como porta padrao mesmo quando a URL
    informada e HTTPS. Para endpoints publicados por proxy sem porta explicita,
    usamos a porta padrao do protocolo (443 para HTTPS e 80 para HTTP).
    """
    from qdrant_client import QdrantClient

    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY") or None
    parsed_url = urlsplit(url)

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
        raise ValueError(
            "QDRANT_URL deve ser uma URL HTTP(S) valida, por exemplo: "
            "https://qdrant.example.com"
        )

    port = parsed_url.port
    if port is None:
        port = 443 if parsed_url.scheme == "https" else 80

    return QdrantClient(
        url=url,
        port=port,
        https=parsed_url.scheme == "https",
        api_key=api_key,
    )


# ─────────────────────────────────────────────
# Fabrica de Embeddings
# ─────────────────────────────────────────────

def get_embeddings(embedding_cfg: dict):
    """
    Retorna o objeto de embeddings configurado.
    Suporta: openrouter | openai | huggingface

    O provider, o modelo e o store devem vir do config.yaml.
    O .env fica apenas para credenciais.
    """
    provider = embedding_cfg.get("provider", "openrouter")
    model = embedding_cfg.get("model", "openai/text-embedding-3-small")
    dimensions = embedding_cfg.get("dimensions")
    dimension_kwargs = {"dimensions": int(dimensions)} if dimensions else {}

    if provider == "openrouter":
        from langchain_openai import OpenAIEmbeddings

        api_key = os.getenv("OPENROUTER_API_KEY", "")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

        if not api_key or api_key.startswith("sk-or-..."):
            raise EnvironmentError(
                "OPENROUTER_API_KEY nao configurada no .env\n"
                "Gere sua chave em: https://openrouter.ai/keys"
            )

        logger.info("Usando embeddings via OpenRouter: %s", model)
        return OpenAIEmbeddings(
            model=model,
            api_key=api_key,
            base_url=base_url,
            **dimension_kwargs,
            # Headers recomendados pelo OpenRouter para identificacao da app
            default_headers={
                "HTTP-Referer": "https://github.com/rag-pipeline",
                "X-Title": "RAG Pipeline",
            },
        )

    elif provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key.startswith("sk-..."):
            raise EnvironmentError("OPENAI_API_KEY nao configurada no .env")

        logger.info("Usando embeddings OpenAI (direto): %s", model)
        return OpenAIEmbeddings(
            model=model,
            api_key=api_key,
            **dimension_kwargs,
        )

    elif provider == "huggingface":
        from langchain_community.embeddings import HuggingFaceEmbeddings

        hf_model = embedding_cfg.get(
            "model",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        )
        logger.info("Usando embeddings HuggingFace (local): %s", hf_model)
        return HuggingFaceEmbeddings(model_name=hf_model)

    else:
        raise ValueError(
            f"Provedor de embeddings nao suportado: '{provider}'\n"
            "Opcoes validas: openrouter | openai | huggingface"
        )


# ─────────────────────────────────────────────
# Fabrica de Vector Store
# ─────────────────────────────────────────────

def get_vector_store(vector_cfg: dict, embeddings, persist_dir: str):
    """
    Retorna o vector store configurado (para leitura/busca).
    Para indexar use index_chunks().
    Suporta: chroma | qdrant | pinecone
    """
    provider = vector_cfg.get("provider", "chroma")
    collection = vector_cfg.get("collection_name", "rag_docs")

    if provider == "chroma":
        from langchain_chroma import Chroma
        return Chroma(
            collection_name=collection,
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )

    elif provider == "qdrant":
        from langchain_community.vectorstores import Qdrant

        client = _get_qdrant_client()
        return Qdrant(
            client=client,
            collection_name=collection,
            embeddings=embeddings,
        )

    elif provider == "pinecone":
        from langchain_pinecone import PineconeVectorStore

        index_name, namespace = _pinecone_settings(vector_cfg)
        return PineconeVectorStore(
            index_name=index_name,
            embedding=embeddings,
            namespace=namespace,
        )

    else:
        raise ValueError(f"Vector store nao suportado: {provider}")


# ─────────────────────────────────────────────
# Indexacao
# ─────────────────────────────────────────────

def index_chunks(
    chunks: list[Document],
    embedding_cfg: dict,
    vector_cfg: dict,
    persist_dir: str,
    batch_size: int = 50,
    recreate: bool = False,
) -> None:
    """
    Gera embeddings e indexa todos os chunks no vector store.
    Processa em batches para evitar timeout e exibir progresso.

    Args:
        recreate: Se True, apaga e recria a collection antes de indexar.
                  Use para re-indexar sem duplicar.
    """
    vs_provider = vector_cfg.get("provider", "chroma")
    collection = vector_cfg.get("collection_name", "rag_docs")
    batch_size = int(embedding_cfg.get("batch_size", batch_size))

    embeddings = get_embeddings(embedding_cfg)

    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    total = len(chunks)
    logger.info(
        "Iniciando indexacao: %d chunks -> %s [%s]",
        total, vs_provider, collection,
    )

    if vs_provider == "chroma":
        from langchain_chroma import Chroma

        for i in range(0, total, batch_size):
            batch = chunks[i : i + batch_size]
            Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                collection_name=collection,
                persist_directory=persist_dir,
            )
            logger.info(
                "  [%d/%d] batch indexado (%d chunks)",
                min(i + batch_size, total), total, len(batch),
            )

    elif vs_provider == "qdrant":
        from qdrant_client.http.models import (
            Distance,
            FieldCondition,
            Filter,
            MatchValue,
            PointIdsList,
            PointStruct,
            VectorParams,
        )

        # qdrant-client 1.10.1 nao possui parametro check_compatibility
        client = _get_qdrant_client()

        # Mapa de dimensoes por modelo
        DIMS = {
            "openai/text-embedding-3-small": 1536,
            "openai/text-embedding-3-large": 3072,
            "openai/text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        embed_model = embedding_cfg.get("model", "openai/text-embedding-3-small")
        vector_size = int(embedding_cfg.get("dimensions") or DIMS.get(embed_model, 1536))
        sync_mode = vector_cfg.get("sync_mode", "append")
        if sync_mode not in {"append", "mirror"}:
            raise ValueError("vector_store.sync_mode deve ser 'append' ou 'mirror'")

        project_ids = {chunk.metadata.get("project_id", "") for chunk in chunks}
        if len(project_ids) != 1 or not next(iter(project_ids), ""):
            raise ValueError(
                "Todos os chunks Qdrant devem ter o mesmo project_id não vazio"
            )
        project_id = next(iter(project_ids))
        chunk_ids = [chunk.metadata.get("chunk_id", "") for chunk in chunks]
        if any(not chunk_id for chunk_id in chunk_ids):
            raise ValueError("Há chunks sem chunk_id; indexação cancelada.")
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("Há chunk_ids duplicados; indexação cancelada.")

        existing = [c.name for c in client.get_collections().collections]

        if recreate and collection in existing:
            client.delete_collection(collection)
            existing.remove(collection)
            logger.info("Collection '%s' removida para re-indexacao", collection)

        if collection not in existing:
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info("Collection '%s' criada no Qdrant (%d dims)", collection, vector_size)
        else:
            count = client.count(collection).count
            logger.info(
                "Collection '%s' ja existe (%d pontos). Adicionando %d novos chunks.",
                collection, count, total,
            )

        project_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.project_id",
                    match=MatchValue(value=project_id),
                )
            ]
        )
        existing_ids: set[str] = set()
        offset = None
        while True:
            records, next_offset = client.scroll(
                collection_name=collection,
                scroll_filter=project_filter,
                limit=256,
                offset=offset,
                with_payload=False,
                with_vectors=False,
            )
            existing_ids.update(str(record.id) for record in records)
            if next_offset is None:
                break
            offset = next_offset

        to_upsert = [
            chunk for chunk in chunks if chunk.metadata["chunk_id"] not in existing_ids
        ]
        logger.info(
            "Qdrant: %d pontos existentes, %d novos/alterados, modo=%s",
            len(existing_ids), len(to_upsert), sync_mode,
        )

        for i in range(0, len(to_upsert), batch_size):
            batch = to_upsert[i : i + batch_size]
            vectors = embeddings.embed_documents([chunk.page_content for chunk in batch])
            points = [
                PointStruct(
                    id=chunk.metadata["chunk_id"],
                    vector=vector,
                    payload={
                        "page_content": chunk.page_content,
                        "metadata": chunk.metadata,
                    },
                )
                for chunk, vector in zip(batch, vectors, strict=True)
            ]
            client.upsert(collection_name=collection, points=points, wait=True)
            logger.info(
                "  [%d/%d] batch indexado",
                min(i + batch_size, len(to_upsert)),
                len(to_upsert),
            )

        if sync_mode == "mirror":
            stale_ids = existing_ids - set(chunk_ids)
            stale_ids_list = sorted(stale_ids)
            for i in range(0, len(stale_ids_list), batch_size):
                stale_batch = stale_ids_list[i : i + batch_size]
                client.delete(
                    collection_name=collection,
                    points_selector=PointIdsList(points=stale_batch),
                    wait=True,
                )
                logger.info(
                    "  [%d/%d] pontos obsoletos removidos",
                    min(i + batch_size, len(stale_ids_list)),
                    len(stale_ids_list),
                )

    elif vs_provider == "pinecone":
        from langchain_pinecone import PineconeVectorStore
        from pinecone import Pinecone

        api_key = os.getenv("PINECONE_API_KEY", "")
        if not api_key:
            raise EnvironmentError("PINECONE_API_KEY nao configurada no .env")

        index_name, namespace = _pinecone_settings(vector_cfg)
        expected_dimensions = int(embedding_cfg.get("dimensions", 1536))

        pinecone = Pinecone(api_key=api_key)
        index_description = pinecone.describe_index(index_name)
        if index_description.dimension != expected_dimensions:
            raise ValueError(
                f"Dimensao do indice Pinecone '{index_name}' "
                f"({index_description.dimension}) difere da dimensao configurada "
                f"para embeddings ({expected_dimensions})"
            )

        index = pinecone.Index(index_name)
        if recreate:
            index.delete(delete_all=True, namespace=namespace)
            logger.info(
                "Namespace Pinecone '%s' limpo no indice '%s'",
                namespace,
                index_name,
            )

        vector_store = PineconeVectorStore(
            index=index,
            embedding=embeddings,
            namespace=namespace,
        )

        for i in range(0, total, batch_size):
            batch = chunks[i : i + batch_size]
            vector_store.add_documents(
                documents=batch,
                ids=_pinecone_document_ids(batch, namespace),
            )
            logger.info("  [%d/%d] batch indexado", min(i + batch_size, total), total)

        collection = f"{index_name}/{namespace}"

    else:
        raise ValueError(f"Vector store nao suportado: {vs_provider}")

    logger.info("Indexacao concluida: %d chunks em '%s'", total, collection)
