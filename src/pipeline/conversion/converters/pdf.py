"""Conversor de PDF para Markdown via pymupdf4llm (SPEC-0023)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf
import pymupdf4llm

from src.pipeline.conversion.config import ConversaoConfig
from src.pipeline.conversion.contracts import AvisoConversao, ConversionError, ConversionResult


@dataclass
class PdfConverter:
    """Extrai Markdown de um PDF preservando cabeçalhos e tabelas por heurística."""

    config: ConversaoConfig = field(default_factory=ConversaoConfig)

    def converter(self, caminho: Path) -> ConversionResult:
        try:
            with pymupdf.open(caminho) as documento:
                if documento.needs_pass:
                    raise ValueError("PDF protegido")
                return self._converter_paginas(documento)
        except Exception as erro:
            raise ConversionError(f"Falha ao converter PDF: {caminho.name}") from erro

    def _converter_paginas(self, documento: pymupdf.Document) -> ConversionResult:
        partes: list[str] = []
        avisos: list[AvisoConversao] = []
        tentativas = 0
        omitidas: list[int] = []
        tesseract = shutil.which("tesseract") is not None
        for indice, pagina in enumerate(documento):
            candidata = len(
                "".join(pagina.get_text().split())
            ) < self.config.minimo_texto_util or bool(pagina.get_images())
            ocr = candidata
            if candidata and tentativas >= self.config.limite_paginas_ocr:
                omitidas.append(indice + 1)
                ocr = False
            elif candidata and not tesseract:
                avisos.append(AvisoConversao("ocr_falhou", indice + 1, "Tesseract indisponível."))
                ocr = False
            elif candidata:
                tentativas += 1
            try:
                markdown = pymupdf4llm.to_markdown(
                    documento, pages=[indice], use_ocr=ocr, ocr_language=self.config.idioma
                )
            except Exception:
                if not ocr:
                    raise
                avisos.append(
                    AvisoConversao(
                        "ocr_falhou",
                        indice + 1,
                        "Não foi possível reconhecer o texto da página com o idioma configurado.",
                    )
                )
                markdown = pymupdf4llm.to_markdown(
                    documento, pages=[indice], use_ocr=False, ocr_language=self.config.idioma
                )
            else:
                if ocr and len("".join(markdown.split())) < self.config.minimo_texto_util:
                    avisos.append(
                        AvisoConversao(
                            "ocr_pouco_texto",
                            indice + 1,
                            "Pouco texto foi reconhecido na página; confira o documento original.",
                        )
                    )
            partes.append(markdown)
        if omitidas:
            avisos.append(
                AvisoConversao(
                    "ocr_limite_de_paginas",
                    omitidas[0],
                    f"{len(omitidas)} páginas não foram lidas por OCR porque o limite foi atingido "
                    f"(páginas {', '.join(map(str, omitidas))}).",
                )
            )
        return ConversionResult(markdown="".join(partes), avisos=avisos)
