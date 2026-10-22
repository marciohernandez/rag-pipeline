"""Conversão local de HTML: conteúdo é dado, sem recursos externos ou scripts."""

from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify

from src.pipeline.conversion.contracts import ConversionResult, ConversionUserError


class HtmlConverter:
    def converter(self, caminho: Path) -> ConversionResult:
        soup = BeautifulSoup(caminho.read_bytes(), "html.parser")
        for node in soup(
            ["script", "style", "noscript", "template", "iframe", "object", "embed", "svg", "img"]
        ):
            node.decompose()
        corpo = soup.body or soup
        if not corpo.get_text(" ", strip=True):
            raise ConversionUserError(
                "não consegui extrair o conteúdo; "
                "salve a página completa como .html pelo navegador e envie-a."
            )
        titulo = soup.title.get_text(" ", strip=True) if soup.title else ""
        texto = markdownify(str(corpo), heading_style="ATX").strip()
        if titulo and not corpo.find(["h1", "h2"]):
            texto = f"# {titulo}\n\n{texto}"
        return ConversionResult(markdown=texto)
