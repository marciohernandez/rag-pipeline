"""
Pipeline RAG — Exportador de Chunks
Salva chunks em JSON para inspeção e auditoria antes da indexação.
"""

import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def export_chunks_to_json(chunks: list[Document], output_path: str) -> None:
    """
    Exporta todos os chunks em formato JSON para inspeção.
    Útil para validar antes de indexar no vector store.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    data = [
        {
            "chunk_index": chunk.metadata.get("chunk_index", i),
            "nome_arquivo": chunk.metadata.get("nome_arquivo", ""),
            "total_chunks": chunk.metadata.get("total_chunks", ""),
            "metadata": chunk.metadata,
            "content": chunk.page_content,
            "content_length": len(chunk.page_content),
        }
        for i, chunk in enumerate(chunks)
    ]

    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=Path(output_path).parent,
        delete=False,
        suffix=".tmp",
    ) as temp_file:
        json.dump(data, temp_file, ensure_ascii=False, indent=2)
        temp_path = Path(temp_file.name)
    temp_path.replace(output_path)

    logger.info("✅ Chunks exportados para: %s (%d chunks)", output_path, len(data))


def print_chunks_summary(chunks: list[Document]) -> None:
    """Imprime resumo dos chunks por arquivo."""
    from collections import defaultdict

    by_file: dict[str, list] = defaultdict(list)
    for chunk in chunks:
        nome = chunk.metadata.get("nome_arquivo", "desconhecido")
        by_file[nome].append(len(chunk.page_content))

    print("\n" + "=" * 60)
    print(f"  RESUMO DOS CHUNKS ({len(chunks)} total)")
    print("=" * 60)
    for nome, sizes in sorted(by_file.items()):
        avg = sum(sizes) // len(sizes)
        print(f"  {nome:<45} {len(sizes):>4} chunks  avg={avg} chars")
    print("=" * 60 + "\n")
