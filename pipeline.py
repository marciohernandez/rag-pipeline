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

# Garante que o src/pipeline/ está no path
sys.path.insert(0, str(Path(__file__).parent))

from src.bootstrap import load_env
from src.pipeline import service
from src.pipeline.chunker import chunk_documents
from src.pipeline.config import load_config, setup_logging
from src.pipeline.exporter import export_chunks_to_json, print_chunks_summary
from src.pipeline.loader import load_markdown_documents
from src.pipeline.manifest import build_manifest, export_manifest
from src.pipeline.quality import QualityGateError, evaluate_quality
from src.pipeline.safety import SyncSafetyError, SyncSafetyPolicy
from src.pipeline.status_gate import filter_by_status

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
    args = parser.parse_args()
    try:
        SyncSafetyPolicy().reject_destructive_option(args.recreate)
    except SyncSafetyError as error:
        parser.error(str(error))
    return args


def main() -> None:
    load_env()
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
    chunks_file = caminhos["chunks_file"]
    manifest_file = caminhos.get("manifest_file") or str(
        Path(chunks_file).with_name("manifest.json")
    )
    vector_store_dir = caminhos.get("vector_store_dir", "./output/chroma_db")

    # ── 2. Carregamento ────────────────────────────────────────
    logger.info("[ETAPA 1/5] Carregando documentos Markdown...")
    documents = load_markdown_documents(input_dir)
    logger.info("Documentos carregados: %d", len(documents))

    contrato_cfg = cfg.get("contrato_markdown", {})
    documents, excluded_documents = filter_by_status(
        documents, contrato_cfg.get("status_bloqueado", [])
    )
    if excluded_documents:
        logger.info(
            "Documentos excluídos por status bloqueante: %d", len(excluded_documents)
        )

    # ── 3. Chunking ────────────────────────────────────────────
    logger.info("[ETAPA 2/5] Gerando chunks...")
    chunking_cfg = cfg.get("chunking", {})
    project_id = cfg["projeto"]["nome"]
    chunks = chunk_documents(documents, chunking_cfg, project_id=project_id)

    # ── 4. Exportação ──────────────────────────────────────────
    logger.info("[ETAPA 3/5] Exportando chunks para JSON...")
    export_chunks_to_json(chunks, chunks_file)
    manifest = build_manifest(
        chunks,
        project_id=project_id,
        collection_name=cfg["vector_store"].get("collection_name", "rag_docs"),
        embedding_cfg=cfg.get("embedding", {}),
        excluded_documents=excluded_documents,
    )
    export_manifest(manifest, manifest_file)
    logger.info("Manifesto validado e salvo em: %s", manifest_file)
    print_chunks_summary(chunks)

    # ── 4.1 Gate de qualidade ──────────────────────────────────
    # Roda antes do desvio de --only-chunks: esse é justamente o modo usado
    # para ajustar o chunking, e medir sem indexar é o ciclo que ele serve.
    logger.info("[ETAPA 4/5] Avaliando a qualidade da preparação...")
    try:
        quality_report = evaluate_quality(
            chunks,
            chunking_cfg,
            cfg.get("qualidade", {}),
            manifest=manifest,
            output_dir=Path(chunks_file).parent,
        )
    except QualityGateError as error:
        logger.error("Gate de qualidade reprovou a carga: %s", error)
        logger.error("Indexação cancelada; nada foi escrito no destino.")
        raise SystemExit(1) from error

    for nome, ocorrencias in quality_report.sinais.items():
        if nome == "distribuicao_de_tamanho" or not ocorrencias:
            continue
        logger.info(
            "Sinal de qualidade %s: %d chunk(s) em %d documento(s)",
            nome,
            sum(ocorrencias.values()),
            len(ocorrencias),
        )
    for aviso in quality_report.avisos:
        logger.info("Gate de qualidade: %s", aviso)
    if quality_report.report_path:
        logger.info("Relatório de qualidade: %s", quality_report.report_path)

    if args.only_chunks:
        logger.info("⚡ Modo --only-chunks: indexação ignorada.")
        logger.info("Chunks salvos em: %s", chunks_file)
        return

    # ── 5. Indexação ───────────────────────────────────────────
    logger.info("[ETAPA 5/5] Indexando no vector store...")
    vector_cfg = cfg.get("vector_store", {})

    counts = service.sync_vector_store(config=cfg, chunks=chunks)

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
    logger.info(
        "   Contagens: previstos=%d inseridos=%d mantidos=%d removidos=%d",
        counts.previstos,
        counts.inseridos,
        counts.mantidos,
        counts.removidos,
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
