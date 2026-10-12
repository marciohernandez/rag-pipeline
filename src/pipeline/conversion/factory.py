"""Factory de conversores por extensão (SPEC-0023).

Segue o mesmo padrão de despacho de `src/pipeline/providers/factory.py`,
trocando o nome de provider pela extensão normalizada do arquivo. Formatos
legados são normalizados via `legacy_office` antes do despacho ao conversor
OOXML equivalente.
"""

from __future__ import annotations

from pathlib import Path

from src.pipeline.conversion.contracts import (
    ConversionResult,
    DocumentConverter,
    UnsupportedFormatError,
)
from src.pipeline.conversion.converters.docx import DocxConverter
from src.pipeline.conversion.converters.image import ImageConverter
from src.pipeline.conversion.converters.pdf import PdfConverter
from src.pipeline.conversion.converters.pptx import PptxConverter
from src.pipeline.conversion.converters.xlsx import XlsxConverter
from src.pipeline.conversion.legacy_office import normalizar_formato_legado

_CONVERSORES: dict[str, DocumentConverter] = {
    "pdf": PdfConverter(),
    "docx": DocxConverter(),
    "pptx": PptxConverter(),
    "xlsx": XlsxConverter(),
    "jpg": ImageConverter(),
    "jpeg": ImageConverter(),
    "png": ImageConverter(),
}

_LEGADOS = {"doc", "ppt", "xls"}


class ConverterFactory:
    """Despacha um arquivo local para o conversor correspondente à sua extensão."""

    @staticmethod
    def for_extension(extensao: str) -> DocumentConverter:
        chave = (extensao or "").strip().lower().lstrip(".")
        if chave not in _CONVERSORES and chave not in _LEGADOS:
            raise UnsupportedFormatError(
                f"Formato de conversão desconhecido: {extensao!r}. "
                f"Opções: {', '.join(sorted(_CONVERSORES) | _LEGADOS)}."
            )
        return _ExtensaoConverter(chave)


class _ExtensaoConverter:
    """Adapter interno: normaliza formato legado antes de delegar ao conversor OOXML."""

    def __init__(self, extensao: str) -> None:
        self._extensao = extensao

    def converter(self, caminho: Path) -> ConversionResult:
        extensao = self._extensao
        caminho_efetivo = caminho
        if extensao in _LEGADOS:
            caminho_efetivo = normalizar_formato_legado(caminho, extensao)
            extensao = caminho_efetivo.suffix.lstrip(".")
        return _CONVERSORES[extensao].converter(caminho_efetivo)
