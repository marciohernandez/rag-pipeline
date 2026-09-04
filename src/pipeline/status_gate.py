"""Gate de bloqueio de indexação por status configurável."""

from __future__ import annotations

import logging

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def filter_by_status(
    documents: list[Document], blocked_statuses: list[str] | None
) -> tuple[list[Document], list[dict]]:
    """Separa documentos cujo status está na lista bloqueante configurada.

    Documento com status ausente ou fora da lista é mantido (fail-open). Uma
    lista bloqueante vazia ou ausente não exclui nenhum documento, o que
    preserva o comportamento atual da base sem frontmatter.
    """
    bloqueados = {str(status).strip() for status in blocked_statuses or []}
    mantidos: list[Document] = []
    excluidos: list[dict] = []

    for document in documents:
        status = document.metadata.get("status")
        if isinstance(status, str) and status.strip() in bloqueados:
            identificador = (
                document.metadata.get("document_id")
                or document.metadata.get("caminho_relativo")
                or document.metadata.get("nome_arquivo", "desconhecido")
            )
            registro = {
                "documento": identificador,
                "nome_arquivo": document.metadata.get("nome_arquivo", ""),
                "status": status,
                "motivo": "status presente na lista bloqueante configurada",
            }
            excluidos.append(registro)
            logger.info(
                "Documento excluído da indexação por status bloqueante: %s (status=%s)",
                identificador,
                status,
            )
            continue
        mantidos.append(document)

    return mantidos, excluidos
