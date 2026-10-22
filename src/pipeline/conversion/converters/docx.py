"""Conversor de DOCX para Markdown via python-docx (SPEC-0023)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from src.pipeline.conversion.contracts import ConversionError, ConversionResult
from src.pipeline.conversion.tabelas import Tabela, Texto, normalizar_tabelas

_HEADING_PREFIX = "Heading "


def _iter_block_items(document: Document) -> Iterator[Paragraph | Table]:
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def _paragraph_to_markdown(paragraph: Paragraph) -> str | None:
    texto = paragraph.text.strip()
    if not texto:
        return None
    if paragraph.style.name.startswith(_HEADING_PREFIX):
        nivel = paragraph.style.name.removeprefix(_HEADING_PREFIX).strip()
        nivel_numero = int(nivel) if nivel.isdigit() else 1
        return f"{'#' * nivel_numero} {texto}"
    return texto


def _table_to_block(table: Table) -> Tabela:
    linhas = [[celula.text.strip() for celula in linha.cells] for linha in table.rows]
    mesclada = bool(table._tbl.xpath(".//w:gridSpan | .//w:vMerge")) or any(
        len({id(celula._tc) for celula in linha.cells}) < len(linha.cells) for linha in table.rows
    )
    return Tabela(linhas, mesclada=mesclada)


class DocxConverter:
    """Extrai Markdown de um DOCX preservando cabeçalhos e tabelas."""

    def converter(self, caminho: Path) -> ConversionResult:
        try:
            documento = Document(str(caminho))
        except Exception as erro:
            raise ConversionError(f"Falha ao converter DOCX: {caminho.name}") from erro

        blocos: list[Texto | Tabela] = []
        for item in _iter_block_items(documento):
            if isinstance(item, Paragraph):
                texto = _paragraph_to_markdown(item)
                if texto is not None:
                    blocos.append(Texto(texto))
            elif item.rows:
                blocos.append(_table_to_block(item))
        resultado = normalizar_tabelas([blocos])
        return ConversionResult(markdown=resultado.markdown, avisos=resultado.avisos)
