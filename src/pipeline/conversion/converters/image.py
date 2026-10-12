"""Conversor de imagem para Markdown via OCR (pytesseract) (SPEC-0023)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytesseract
from PIL import Image

from src.pipeline.conversion.contracts import ConversionError, ConversionResult


@dataclass
class ImageConverter:
    """Reconhece texto em uma imagem por OCR, melhor esforço, sem bloquear por baixa confiança."""

    idioma: str = "por"

    def converter(self, caminho: Path) -> ConversionResult:
        try:
            with Image.open(caminho) as imagem:
                texto = pytesseract.image_to_string(imagem, lang=self.idioma)
        except Exception as erro:
            raise ConversionError(f"Falha ao converter imagem: {caminho.name}") from erro

        texto = texto.strip()
        if not texto:
            return ConversionResult(
                markdown=f"_Nenhum texto reconhecido em {caminho.name}._",
                avisos=["ocr_sem_texto_reconhecido"],
            )
        return ConversionResult(markdown=texto)
