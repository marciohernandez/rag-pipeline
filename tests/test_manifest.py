import pytest
from langchain_core.documents import Document

from src.manifest import ManifestValidationError, build_manifest, validate_manifest


def test_manifest_counts_chunk_types_and_documents() -> None:
    chunks = [
        Document(
            page_content="conteúdo",
            metadata={
                "chunk_id": "a",
                "chunk_type": "detail",
                "document_id": "doc-1",
                "nome_arquivo": "a.md",
                "caminho_relativo": "base/a.md",
                "source_hash": "hash",
            },
        ),
        Document(
            page_content="resumo",
            metadata={
                "chunk_id": "b",
                "chunk_type": "section_summary",
                "document_id": "doc-1",
                "nome_arquivo": "a.md",
                "caminho_relativo": "base/a.md",
                "source_hash": "hash",
            },
        ),
    ]

    manifest = build_manifest(
        chunks,
        project_id="base",
        collection_name="collection",
        embedding_cfg={"provider": "openai", "model": "model", "dimensions": 3},
    )

    assert manifest["chunk_count"] == 2
    assert manifest["chunk_type_counts"] == {"detail": 1, "section_summary": 1}
    assert manifest["documents"][0]["chunk_count"] == 2


def test_manifest_rejects_duplicate_ids() -> None:
    with pytest.raises(ManifestValidationError, match="duplicados"):
        validate_manifest({"chunk_count": 2, "chunk_ids": ["same", "same"]})
