"""PDFs sintéticos da SPEC-0033: gerados no teste, sem dados reais (PR-004)."""

from __future__ import annotations

import io
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

TEXTO_NATIVO = "Relatorio mensal com texto nativo suficiente para dispensar o reconhecimento por OCR"
FRASE_IMAGEM = "Cláusula segunda: ação e rescisão"
_FONTE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def imagem_com_texto(frase: str = FRASE_IMAGEM) -> bytes:
    """PNG branco com a frase em letras grandes; frase vazia gera uma imagem sem texto."""
    # DejaVu renderiza os acentos de forma legível; a fonte padrão do Pillow distorce "ç" e "ã".
    fonte = (
        ImageFont.truetype(str(_FONTE), 72) if _FONTE.exists() else ImageFont.load_default(size=72)
    )
    imagem = Image.new("RGB", (1700, 260), "white")
    if frase:
        ImageDraw.Draw(imagem).text((30, 80), frase, fill="black", font=fonte)
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    return buffer.getvalue()


def criar_pdf(caminho: Path, paginas: list[str]) -> Path:
    """Cria um PDF. Cada item descreve uma página:

    - ``"texto"``: só camada de texto;
    - ``"imagem:FRASE"``: só a imagem da frase (``"imagem:"`` = imagem sem texto);
    - ``"misto:FRASE"``: parágrafo de texto no topo e a imagem da frase embaixo.
    """
    documento = pymupdf.open()
    for descricao in paginas:
        tipo, _, frase = descricao.partition(":")
        pagina = documento.new_page(width=595, height=842)
        if tipo in ("texto", "misto"):
            pagina.insert_textbox(pymupdf.Rect(72, 72, 520, 140), TEXTO_NATIVO, fontsize=12)
        if tipo in ("imagem", "misto"):
            pagina.insert_image(pymupdf.Rect(30, 200, 565, 335), stream=imagem_com_texto(frase))
    documento.save(str(caminho))
    documento.close()
    return caminho
