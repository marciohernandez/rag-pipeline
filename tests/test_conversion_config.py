"""Testes da configuração da conversão e do idioma do OCR (SPEC-0033)."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pymupdf4llm
import pytest

from tests._pdfs_spec0033 import criar_pdf

FIXTURES = Path(__file__).parent / "fixtures" / "spec0023"


def _modulo():
    try:
        return import_module("src.pipeline.conversion.config")
    except ModuleNotFoundError:
        pytest.fail("src/pipeline/conversion/config.py ainda não existe (FR-005)")


def test_spec_0033_ac_007_idioma_vale_para_pdf_e_imagem(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-003 FR-004 FR-005 AC-007"""
    import pytesseract

    from src.pipeline.conversion.converters.image import ImageConverter
    from src.pipeline.conversion.converters.pdf import PdfConverter

    config = _modulo().carregar_config_conversao({"conversao": {"idioma": "eng"}})
    idiomas_pdf: list[str] = []
    idiomas_imagem: list[str] = []
    original = pymupdf4llm.to_markdown
    monkeypatch.setattr(
        pymupdf4llm,
        "to_markdown",
        lambda *a, **k: (idiomas_pdf.append(k.get("ocr_language")), original(*a, **k))[1],
    )
    original_ocr = pytesseract.image_to_string
    monkeypatch.setattr(
        pytesseract,
        "image_to_string",
        lambda *a, **k: (idiomas_imagem.append(k.get("lang")), original_ocr(*a, **k))[1],
    )

    PdfConverter(config=config).converter(criar_pdf(tmp_path / "i.pdf", ["imagem:Texto simples"]))
    ImageConverter(config=config).converter(FIXTURES / "imagem.jpg")

    assert idiomas_pdf and set(idiomas_pdf) == {"eng"}
    assert idiomas_imagem == ["eng"]


def test_spec_0033_ac_008_padroes_sem_a_secao() -> None:
    """SPECSFY: SPEC-0033 US-003 FR-004 FR-005 AC-008"""
    config = _modulo().carregar_config_conversao({})

    assert config.idioma == "por+eng"
    assert config.limite_paginas_ocr == 50
    assert config.minimo_texto_util == 40


@pytest.mark.parametrize(
    ("secao", "campo"),
    [
        ({"limite_paginas_ocr": 0}, "limite_paginas_ocr"),
        ({"limite_paginas_ocr": -3}, "limite_paginas_ocr"),
        ({"idioma": ""}, "idioma"),
        ({"minimo_texto_util": -1}, "minimo_texto_util"),
    ],
)
def test_spec_0033_ac_009_rejeita_valor_invalido(secao, campo) -> None:
    """SPECSFY: SPEC-0033 US-003 FR-004 FR-005 AC-009"""
    with pytest.raises(ValueError, match=campo):
        _modulo().carregar_config_conversao({"conversao": secao})
