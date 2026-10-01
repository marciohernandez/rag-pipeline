"""Testes do conversor de imagens por OCR (SPEC-0023)."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "spec0023"


def test_spec_0023_ac_012_ocr_reconhece_texto_em_portugues() -> None:
    """SPECSFY: SPEC-0023 US-001 FR-003 NFR-001 AC-012"""
    from src.pipeline.conversion.converters.image import ImageConverter

    resultado = ImageConverter(idioma="por").converter(FIXTURES / "imagem.jpg")

    assert "documento de teste em português" in resultado.markdown.lower()


def test_spec_0023_ac_012_imagem_sem_texto_retorna_markdown_minimo(tmp_path) -> None:
    """SPECSFY: SPEC-0023 US-001 FR-003 NFR-001 AC-012"""
    from src.pipeline.conversion.converters.image import ImageConverter

    imagem_sem_texto = tmp_path / "sem-texto.pgm"
    imagem_sem_texto.write_bytes(b"P5\n16 16\n255\n" + bytes([255]) * 256)

    resultado = ImageConverter(idioma="por").converter(imagem_sem_texto)

    assert resultado.markdown.strip()
