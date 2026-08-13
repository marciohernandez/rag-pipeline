"""
Pipeline RAG — Script Principal
Orquestra: Carregamento → Chunking → Exportação → Indexação

Uso:
    uv run python pipeline.py                  # executa tudo
    uv run python pipeline.py --only-chunks    # apenas gera chunks.json (sem indexar)
    uv run python pipeline.py --skip-index     # igual a --only-chunks
"""

import argparse
import logging
import sys
from pathlib import Path

# Garante que o src/ está no path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config, setup_logging
from src.loader import load_markdown_documents
from src.chunker import chunk_documents
from src.exporter import export_chunks_to_json, print_chunks_summary
from src.embedder import index_chunks

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline RAG: Markdown → Chunks → Vector Store"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Caminho para o arquivo de configuração (padrão: config.yaml)",
    )
    parser.add_argument(
        "--only-chunks",
        "--skip-index",
        action="store_true",
        dest="only_chunks",
        help="Gera apenas o arquivo chunks.json, sem indexar no vector store",
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Sobrescreve o diretório de entrada do config.yaml",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help=(
            "Substitui a base antes de indexar: recria a collection no Qdrant "
            "ou limpa somente o namespace no Pinecone"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ── 1. Configuração ────────────────────────────────────────
    cfg = load_config(args.config)
    log_cfg = cfg.get("log", {})
    setup_logging(
        level=log_cfg.get("level", "INFO"),
        log_file=log_cfg.get("arquivo"),
    )

    logger.info("=" * 60)
    logger.info("Pipeline RAG iniciado — projeto: %s", cfg["projeto"]["nome"])
    logger.info("=" * 60)

    caminhos = cfg["caminhos"]
    input_dir = args.input_dir or caminhos["input_dir"]
    output_dir = caminhos["output_dir"]
    chunks_file = caminhos["chunks_file"]
    vector_store_dir = caminhos.get("vector_store_dir", "./output/chroma_db")

    # ── 2. Carregamento ────────────────────────────────────────
    logger.info("[ETAPA 1/4] Carregando documentos Markdown...")
    documents = load_markdown_documents(input_dir)
    logger.info("Documentos carregados: %d", len(documents))

    # ── 3. Chunking ────────────────────────────────────────────
    logger.info("[ETAPA 2/4] Gerando chunks...")
    chunking_cfg = cfg.get("chunking", {})
    chunks = chunk_documents(documents, chunking_cfg)

    # ── 4. Exportação ──────────────────────────────────────────
    logger.info("[ETAPA 3/4] Exportando chunks para JSON...")
    export_chunks_to_json(chunks, chunks_file)
    print_chunks_summary(chunks)

    if args.only_chunks:
        logger.info("⚡ Modo --only-chunks: indexação ignorada.")
        logger.info("Chunks salvos em: %s", chunks_file)
        return

    # ── 5. Indexação ───────────────────────────────────────────
    logger.info("[ETAPA 4/4] Indexando no vector store...")
    embedding_cfg = cfg.get("embedding", {})
    vector_cfg = cfg.get("vector_store", {})

    index_chunks(
        chunks=chunks,
        embedding_cfg=embedding_cfg,
        vector_cfg=vector_cfg,
        persist_dir=vector_store_dir,
        recreate=args.recreate,
    )

    provider = vector_cfg.get("provider", "chroma")
    if provider == "pinecone":
        vector_store_location = (
            f"Pinecone: {vector_cfg.get('index_name')}"
            f"/{vector_cfg.get('namespace')}"
        )
    elif provider == "qdrant":
        vector_store_location = (
            f"Qdrant: {vector_cfg.get('collection_name', 'rag_docs')}"
        )
    else:
        vector_store_location = f"Chroma: {vector_store_dir}"

    logger.info("=" * 60)
    logger.info("✅ Pipeline concluído com sucesso!")
    logger.info("   Chunks: %s", chunks_file)
    logger.info("   Vector Store: %s", vector_store_location)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
