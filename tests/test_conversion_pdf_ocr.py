"""Testes do OCR por página no conversor de PDF (SPEC-0033)."""

from __future__ import annotations

import re
import socket
from importlib import import_module

import pymupdf4llm
import pytest

from tests._pdfs_spec0033 import TEXTO_NATIVO, criar_pdf


def _normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def _config(**campos):
    try:
        modulo = import_module("src.pipeline.conversion.config")
    except ModuleNotFoundError:
        pytest.fail("src/pipeline/conversion/config.py ainda não existe (FR-005)")
    return modulo.ConversaoConfig(**campos)


def _conversor(**campos):
    from src.pipeline.conversion.converters.pdf import PdfConverter

    return PdfConverter(config=_config(**campos)) if campos else PdfConverter()


def _espiar(monkeypatch, falhar_em_pagina: int | None = None) -> list[dict]:
    """Registra os argumentos de cada chamada a `pymupdf4llm.to_markdown`."""
    original = pymupdf4llm.to_markdown
    chamadas: list[dict] = []

    def espiao(*args, **kwargs):
        chamadas.append(kwargs)
        if (
            falhar_em_pagina is not None
            and kwargs.get("use_ocr")
            and kwargs.get("pages") == [falhar_em_pagina]
        ):
            raise RuntimeError("falha simulada de OCR")
        return original(*args, **kwargs)

    monkeypatch.setattr(pymupdf4llm, "to_markdown", espiao)
    return chamadas


def _bloquear_rede(monkeypatch) -> None:
    def proibido(*_args, **_kwargs):
        raise AssertionError("chamada de rede durante a conversão (NFR-001)")

    monkeypatch.setattr(socket.socket, "connect", proibido)


def _codigos(resultado) -> list[tuple[str, int]]:
    return [(aviso.codigo, aviso.pagina) for aviso in resultado.avisos]


def test_spec_0033_ac_001_pdf_misto_le_pagina_em_imagem(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-001 FR-001 FR-002 NFR-001 NFR-002 AC-001"""
    pdf = criar_pdf(tmp_path / "misto.pdf", ["misto:Cláusula segunda: ação e rescisão", "texto"])
    _bloquear_rede(monkeypatch)

    resultado = _conversor().converter(pdf)

    markdown = _normalizar(resultado.markdown)
    assert "Relatorio mensal com texto nativo" in markdown
    assert "Cláusula segunda: ação e rescisão" in markdown
    assert markdown.index("Cláusula segunda") < markdown.rindex("Relatorio mensal")


def test_spec_0033_ac_002_pdf_de_texto_nao_passa_por_ocr(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-001 FR-001 NFR-002 AC-002"""
    pdf = criar_pdf(tmp_path / "texto.pdf", ["texto", "texto"])
    esperado = pymupdf4llm.to_markdown(str(pdf), use_ocr=False)
    chamadas = _espiar(monkeypatch)

    resultado = _conversor().converter(pdf)

    assert chamadas, "o conversor deve chamar o pymupdf4llm"
    assert all(chamada.get("use_ocr") is False for chamada in chamadas)
    assert resultado.markdown == esperado
    assert resultado.avisos == []


def test_spec_0033_ac_003_pdf_inteiro_em_imagem_na_ordem(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-001 FR-001 FR-002 NFR-001 NFR-003 AC-003"""
    pdf = criar_pdf(
        tmp_path / "imagens.pdf",
        [
            "imagem:Primeira cláusula: ação com informações suficientes para leitura",
            "imagem:Segunda cláusula: rescisão com informações suficientes para leitura",
            "imagem:Terceira cláusula: previsão com informações suficientes para leitura",
        ],
    )
    _bloquear_rede(monkeypatch)

    resultado = _conversor().converter(pdf)

    markdown = _normalizar(resultado.markdown)
    posicoes = [
        markdown.find("Primeira cláusula: ação"),
        markdown.find("Segunda cláusula: rescisão"),
        markdown.find("Terceira cláusula: previsão"),
    ]
    assert all(posicao >= 0 for posicao in posicoes), markdown
    assert posicoes == sorted(posicoes)
    assert resultado.avisos == []


def test_spec_0033_ac_004_ocr_sem_texto_gera_aviso(tmp_path) -> None:
    """SPECSFY: SPEC-0033 US-002 FR-003 FR-006 FR-008 AC-004"""
    pdf = criar_pdf(tmp_path / "vazia.pdf", ["texto", "imagem:"])

    resultado = _conversor().converter(pdf)

    assert _codigos(resultado) == [("ocr_pouco_texto", 2)]
    assert resultado.avisos[0].mensagem
    assert "Relatorio mensal" in resultado.markdown


def test_spec_0033_ac_005_limite_de_paginas_com_ocr(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-002 FR-003 FR-004 NFR-003 AC-005"""
    pdf = criar_pdf(tmp_path / "cinco.pdf", ["imagem:Página número um"] * 5)
    chamadas = _espiar(monkeypatch)

    resultado = _conversor(limite_paginas_ocr=2).converter(pdf)

    assert sum(1 for chamada in chamadas if chamada.get("use_ocr")) == 2
    limite = [aviso for aviso in resultado.avisos if aviso.codigo == "ocr_limite_de_paginas"]
    assert len(limite) == 1
    assert "3" in limite[0].mensagem


def test_spec_0033_ac_006_falha_de_ocr_em_pagina(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-002 FR-002 FR-003 FR-007 FR-008 AC-006"""
    pdf = criar_pdf(
        tmp_path / "tres.pdf",
        [
            "imagem:Primeira cláusula: ação",
            "imagem:Segunda cláusula: rescisão",
            "imagem:Terceira cláusula: previsão",
        ],
    )
    _espiar(monkeypatch, falhar_em_pagina=1)

    resultado = _conversor().converter(pdf)

    markdown = _normalizar(resultado.markdown)
    assert "Primeira cláusula: ação" in markdown
    assert "Terceira cláusula: previsão" in markdown
    assert markdown.index("Primeira") < markdown.index("Terceira")
    assert ("ocr_falhou", 2) in _codigos(resultado)


def test_spec_0033_ac_010_tesseract_ausente(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0033 US-002 FR-006 FR-007 NFR-001 AC-010"""
    pdf = criar_pdf(tmp_path / "sem-tesseract.pdf", ["texto", "imagem:Cláusula segunda"])
    monkeypatch.setattr("shutil.which", lambda *_args, **_kwargs: None)

    resultado = _conversor().converter(pdf)

    assert _normalizar(TEXTO_NATIVO)[:30] in _normalizar(resultado.markdown)
    falhas = [aviso for aviso in resultado.avisos if aviso.codigo == "ocr_falhou"]
    assert [aviso.pagina for aviso in falhas] == [2]
    assert "Tesseract indisponível" in falhas[0].mensagem
