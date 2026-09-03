"""Identidade estável de documentos e chunks para sincronização vetorial."""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document


def content_hash(content: str) -> str:
    """Retorna o SHA-256 do conteúdo em UTF-8."""
    return sha256(content.encode("utf-8")).hexdigest()


def stable_uuid(*parts: object) -> str:
    """Gera um UUID compatível com Qdrant a partir de dados estáveis."""
    return str(uuid5(NAMESPACE_URL, "|".join(str(part) for part in parts)))


def assign_document_identity(document: Document, project_id: str) -> None:
    """Inclui identidade e fingerprint da fonte no metadata do documento.

    Um ``document_id`` já presente e não vazio, recebido do projeto-mãe via
    frontmatter, tem precedência sobre a geração determinística local.
    """
    source_path = document.metadata.get("caminho_relativo") or document.metadata.get(
        "nome_arquivo", "desconhecido"
    )
    document.metadata["project_id"] = project_id
    document_id = document.metadata.get("document_id")
    if not isinstance(document_id, str) or not document_id.strip():
        document.metadata["document_id"] = stable_uuid(
            "document", project_id, source_path
        )
    document.metadata.setdefault("source_hash", content_hash(document.page_content))


def assign_chunk_identities(chunks: list[Document], project_id: str) -> None:
    """Atribui IDs determinísticos e únicos a todos os chunks de uma execução."""
    occurrences: dict[str, int] = defaultdict(int)

    for chunk in chunks:
        metadata = chunk.metadata
        source_path = metadata.get("caminho_relativo") or metadata.get(
            "nome_arquivo", "desconhecido"
        )
        document_id = metadata.get("document_id") or stable_uuid(
            "document", project_id, source_path
        )
        source_hash = metadata.get("source_hash") or content_hash(chunk.page_content)
        chunk_type = metadata.get("chunk_type", "detail")
        logical_path = "|".join(
            str(metadata.get(key, ""))
            for key in ("titulo", "secao", "subsecao", "summary_key")
        )
        digest = content_hash(chunk.page_content)
        base_key = "|".join(  # noqa: FLY002 - campos variáveis formam a chave canônica
            (project_id, document_id, source_hash, chunk_type, logical_path, digest)
        )
        occurrence = occurrences[base_key]
        occurrences[base_key] += 1

        metadata.update(
            {
                "project_id": project_id,
                "document_id": document_id,
                "source_hash": source_hash,
                "chunk_hash": digest,
                "chunk_id": stable_uuid("chunk", base_key, occurrence),
            }
        )
