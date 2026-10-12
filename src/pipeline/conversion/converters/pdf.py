"""Conversor de PDF para Markdown via pymupdf4llm (SPEC-0023)."""

from __future__ import annotations

from pathlib import Path

import pymupdf4llm

from src.pipeline.conversion.contracts import ConversionError, ConversionResult


class PdfConverter:
    """Extrai Markdown de um PDF preservando cabeçalhos e tabelas por heurística."""

    def converter(self, caminho: Path) -> ConversionResult:
        try:
            markdown = pymupdf4llm.to_markdown(str(caminho))
        except Exception as erro:
            raise ConversionError(f"Falha ao converter PDF: {caminho.name}") from erro
        return ConversionResult(markdown=markdown)
