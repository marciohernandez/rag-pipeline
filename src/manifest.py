"""Manifesto local para validar uma carga antes de escrever no vector store."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
import json
from uuid import uuid4

from langchain_core.documents import Document


class ManifestValidationError(ValueError):
    """Indica que o conjunto local não está seguro para indexação."""


def build_manifest(
    chunks: list[Document],
    *,
    project_id: str,
    collection_name: str,
    embedding_cfg: dict,
) -> dict:
    documents: dict[str, dict] = {}
    type_counts = Counter()

    for chunk in chunks:
        metadata = chunk.metadata
        document_id = metadata.get("document_id", "")
        documents.setdefault(
            document_id,
            {
                "document_id": document_id,
                "nome_arquivo": metadata.get("nome_arquivo", ""),
                "caminho_relativo": metadata.get("caminho_relativo", ""),
                "source_hash": metadata.get("source_hash", ""),
                "chunk_count": 0,
            },
        )["chunk_count"] += 1
        type_counts[metadata.get("chunk_type", "detail")] += 1

    manifest = {
        "run_id": str(uuid4()),
        "generated_at": datetime.now(UTC).isoformat(),
        "project_id": project_id,
        "collection_name": collection_name,
        "embedding": {
            "provider": embedding_cfg.get("provider"),
            "model": embedding_cfg.get("model"),
            "dimensions": embedding_cfg.get("dimensions"),
        },
        "chunk_count": len(chunks),
        "chunk_type_counts": dict(sorted(type_counts.items())),
        "documents": list(
            sorted(documents.values(), key=lambda item: item["caminho_relativo"])
        ),
        "chunk_ids": [chunk.metadata.get("chunk_id", "") for chunk in chunks],
    }
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict) -> None:
    chunk_ids = manifest.get("chunk_ids", [])
    if not chunk_ids:
        raise ManifestValidationError("Nenhum chunk foi gerado; indexação cancelada.")
    if any(not chunk_id for chunk_id in chunk_ids):
        raise ManifestValidationError("Há chunks sem chunk_id; indexação cancelada.")
    if len(chunk_ids) != len(set(chunk_ids)):
        raise ManifestValidationError("Há chunk_ids duplicados; indexação cancelada.")
    if manifest.get("chunk_count") != len(chunk_ids):
        raise ManifestValidationError("Contagem do manifesto é inconsistente.")


def export_manifest(manifest: dict, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as temp_file:
        json.dump(manifest, temp_file, ensure_ascii=False, indent=2)
        temp_path = Path(temp_file.name)
    temp_path.replace(path)
