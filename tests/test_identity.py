"""Identidade estável de documento por coleção (SPEC-0030, AC-006).

Fase RED: ``loader`` grava ``caminho_relativo`` com a pasta temporária do worker e
``assign_document_identity`` deriva o ``document_id`` dele.
"""

from __future__ import annotations

from pathlib import Path

from src.pipeline.identity import assign_document_identity
from src.pipeline.loader import load_markdown_documents


def _documento(pasta: Path, texto: str = "# Título\n\nCorpo do documento.\n"):
    pasta.mkdir(parents=True)
    (pasta / "a.md").write_text(texto, encoding="utf-8")
    return load_markdown_documents(str(pasta))[0]


def _id(pasta: Path, colecao: str, texto: str = "# Título\n\nCorpo do documento.\n") -> str:
    documento = _documento(pasta, texto)
    assign_document_identity(documento, colecao)
    return documento.metadata["document_id"]


def test_document_id_estavel_por_colecao_e_nome(tmp_path) -> None:
    """SPECSFY: SPEC-0030 US-002 FR-004 FR-005 NFR-002 AC-006"""
    primeiro = _id(tmp_path / "base-7-k3j2h1", "col-manuais")
    segundo = _id(tmp_path / "base-9-zz91xa", "col-manuais")
    assert primeiro == segundo, "a pasta temporária não pode entrar na identidade"

    assert _id(tmp_path / "base-11-aaaaaa", "col-politicas") != primeiro

    com_frontmatter = "---\ndocument_id: doc-42\n---\n# Título\n\nCorpo.\n"
    assert _id(tmp_path / "base-12-bbbbbb", "col-manuais", com_frontmatter) == "doc-42"
