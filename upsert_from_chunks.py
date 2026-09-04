"""
Reupsert de chunks já exportados para o vector store, sem reprocessar documentos.

Uso:
    uv run python upsert_from_chunks.py --provider qdrant --recreate
"""

import argparse
import json
import logging
from pathlib import Path

from langchain_core.documents import Document

from src.bootstrap import load_env
from src.pipeline import service
from src.pipeline.config import load_config, setup_logging
from src.pipeline.manifest import validate_manifest
from src.pipeline.safety import SyncSafetyError, SyncSafetyPolicy

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reindexa a partir de chunks.json existente"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Caminho para o arquivo de configuracao (padrao: config.yaml)",
    )
    parser.add_argument(
        "--provider",
        default="qdrant",
        choices=["qdrant", "chroma", "pinecone"],
        help="Vector store alvo para o reupsert (padrao: qdrant)",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Apaga/recria a collection/namespace antes do upsert para evitar duplicacao",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help=(
            "Manifesto que valida o chunks.json antes do upsert "
            "(padrão: manifest.json ao lado dos chunks)"
        ),
    )
    args = parser.parse_args()
    try:
        SyncSafetyPolicy().reject_destructive_option(args.recreate)
    except SyncSafetyError as error:
        parser.error(str(error))
    return args


def load_chunks_from_json(chunks_file: str) -> list[Document]:
    path = Path(chunks_file)
    if not path.exists():
        raise FileNotFoundError(f"chunks_file nao encontrado: {path}")

    items = json.loads(path.read_text(encoding="utf-8"))
    return [
        Document(
            page_content=item.get("content", ""),
            metadata=item.get("metadata", {}),
        )
        for item in items
    ]


def validate_chunks_against_manifest(chunks: list[Document], manifest_path: str) -> None:
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Manifesto não encontrado: {path}. Gere e valide os chunks antes do upsert."
        )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    chunk_ids = [chunk.metadata.get("chunk_id", "") for chunk in chunks]
    if len(chunks) != manifest["chunk_count"] or set(chunk_ids) != set(manifest["chunk_ids"]):
        raise ValueError(
            "chunks.json não corresponde ao manifesto validado; upsert cancelado."
        )


def main() -> None:
    load_env()
    args = parse_args()

    cfg = load_config(args.config)
    log_cfg = cfg.get("log", {})
    setup_logging(level=log_cfg.get("level", "INFO"), log_file=log_cfg.get("arquivo"))

    chunks_file = cfg["caminhos"]["chunks_file"]
    vector_cfg = dict(cfg.get("vector_store", {}))
    vector_cfg["provider"] = args.provider

    chunks = load_chunks_from_json(chunks_file)
    manifest_file = args.manifest or str(Path(chunks_file).with_name("manifest.json"))
    validate_chunks_against_manifest(chunks, manifest_file)
    logger.info("Chunks carregados de %s: %d", chunks_file, len(chunks))

    counts = service.sync_vector_store(
        config={**cfg, "vector_store": vector_cfg},
        chunks=chunks,
    )

    logger.info(
        "Reupsert concluido: previstos=%d inseridos=%d mantidos=%d removidos=%d",
        counts.previstos,
        counts.inseridos,
        counts.mantidos,
        counts.removidos,
    )


if __name__ == "__main__":
    main()
