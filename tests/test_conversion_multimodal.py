"""Caracterização complementar dos contratos reais usados pela SPEC-0036."""

from types import SimpleNamespace

import pymupdf
import pytest

from src.pipeline.conversion.contracts import ConversionUserError
from src.pipeline.conversion.reprocessar_ia import ReprocessadorIa
from src.pipeline.providers.contracts import ChatImage, ChatMessage
from src.pipeline.providers.llm.openrouter import OpenRouterChatAdapter


def test_adapter_preserva_texto_e_traduz_imagens(monkeypatch):
    """SPECSFY: SPEC-0036 US-005 FR-008 FR-009 NFR-002 AC-021 AC-022"""
    import langchain_openai

    recebidas = []

    class Modelo:
        def __init__(self, **kwargs):
            pass

        def invoke(self, entrada):
            recebidas.extend(entrada)
            return SimpleNamespace(content="# Resultado")

    monkeypatch.setattr(langchain_openai, "ChatOpenAI", Modelo)
    modelo = OpenRouterChatAdapter(model="modelo-falso", api_key="chave-ficticia")
    modelo.responder(
        [ChatMessage("sistema", "Texto"), ChatMessage("pessoa", "Página", (ChatImage("YWJj"),))]
    )
    assert recebidas[0] == ("system", "Texto")
    assert recebidas[1][1][1] == {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64,YWJj"},
    }


def test_pdf_vira_imagens_do_documento_sem_rede(tmp_path):
    """SPECSFY: SPEC-0036 US-005 FR-008 NFR-002 AC-021"""
    caminho = tmp_path / "origem.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page().insert_text((40, 40), "Conteudo original")
        pdf.save(caminho)
    chamadas = []

    class Modelo:
        def responder(self, mensagens):
            chamadas.append(mensagens)
            return "# Conteúdo lido"

    assert ReprocessadorIa(Modelo()).reprocessar(caminho, "pdf") == "# Conteúdo lido"
    assert len(chamadas) == 1
    assert len(chamadas[0][1].imagens) == 1
    assert chamadas[0][1].imagens[0].base64.startswith("iVBOR")


def test_resposta_vazia_e_falha_segura(tmp_path):
    """SPECSFY: SPEC-0036 US-005 FR-008 NFR-002 AC-023"""
    caminho = tmp_path / "origem.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.save(caminho)

    class Modelo:
        def responder(self, mensagens):
            raise RuntimeError("segredo-ficticio")

    with pytest.raises(ConversionUserError) as erro:
        ReprocessadorIa(Modelo()).reprocessar(caminho, "pdf")
    assert "segredo-ficticio" not in str(erro.value)


def test_limite_de_ocr_nao_cria_limite_de_paginas_para_ia(tmp_path):
    """SPECSFY: SPEC-0036 US-005 FR-008 AC-021 DEC-005"""
    from src.pipeline.conversion.config import ConversaoConfig

    caminho = tmp_path / "duas-paginas.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.new_page()
        pdf.save(caminho)
    recebidas = []

    class Modelo:
        def responder(self, mensagens):
            recebidas.extend(mensagens[-1].imagens)
            return "# Documento"

    ReprocessadorIa(Modelo(), ConversaoConfig(limite_paginas_ocr=1)).reprocessar(caminho, "pdf")
    assert len(recebidas) == 2
