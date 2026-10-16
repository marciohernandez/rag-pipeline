"""Relatório de contradições em Markdown e PDF com o mesmo conteúdo (SPEC-0038, FR-008)."""

from __future__ import annotations

import html
import io
from collections.abc import Sequence
from typing import Any

from src.pipeline.contradicoes.contratos import ROTULOS


def _ordenadas(ocorrencias: Sequence[Any]) -> list[Any]:
    return sorted(ocorrencias, key=lambda o: (o.impacto != "alto", str(o.assunto).casefold()))


def _linhas(analise: Any, ocorrencias: Sequence[Any]) -> list[tuple[str, str]]:
    """Representação neutra: (tipo, texto) com tipos titulo, subtitulo, item e texto."""
    linhas = [("titulo", "Relatório de contradições")]
    linhas.append(("texto", f"IA usada: {analise.provedor or 'não informada'}"))
    linhas.append(("texto", f"Versão do domínio: {analise.dominio_versao_id or 'não informada'}"))
    linhas.append(("texto", f"Documentos analisados: {analise.documentos_analisados}"))
    if analise.situacao == "incompleta":
        linhas.append(
            (
                "texto",
                f"Análise incompleta ({analise.concluidos} de {analise.total_assuntos} assuntos)"
                + (f": {analise.motivo}" if analise.motivo else ""),
            )
        )
    if not ocorrencias:
        linhas.append(
            (
                "texto",
                (
                    f"Nenhuma contradição encontrada. {analise.documentos_analisados} "
                    "documentos foram analisados."
                ),
            )
        )
    for ocorrencia in _ordenadas(ocorrencias):
        etiqueta = ROTULOS.get(ocorrencia.etiqueta, ocorrencia.etiqueta)
        linhas.append(("subtitulo", ocorrencia.assunto))
        linhas.append(("texto", f"Etiqueta: {etiqueta} · Impacto: {ocorrencia.impacto}"))
        for trecho in ocorrencia.trechos:
            marca = " (mais antigo)" if trecho.arquivo == ocorrencia.arquivo_mais_antigo else ""
            linhas.append(("item", f"{trecho.arquivo}{marca}: {trecho.texto}"))
        linhas.append(("texto", f"Explicação: {ocorrencia.explicacao}"))
    return linhas


def montar_markdown(analise: Any, ocorrencias: Sequence[Any]) -> str:
    prefixo = {"titulo": "# ", "subtitulo": "## ", "item": "- ", "texto": ""}
    return "\n\n".join(f"{prefixo[t]}{x}" for t, x in _linhas(analise, ocorrencias)) + "\n"


def montar_pdf(analise: Any, ocorrencias: Sequence[Any]) -> bytes:
    import pymupdf

    etiquetas = {"titulo": "h1", "subtitulo": "h2", "texto": "p", "item": "p"}
    corpo = "".join(
        f"<{etiquetas[t]}>{'• ' if t == 'item' else ''}{html.escape(x)}</{etiquetas[t]}>"
        for t, x in _linhas(analise, ocorrencias)
    )
    destino = io.BytesIO()
    historia = pymupdf.Story(html=f"<body>{corpo}</body>")
    escritor = pymupdf.DocumentWriter(destino)
    pagina = pymupdf.paper_rect("a4")
    area = pagina + (36, 36, -36, -36)
    mais = 1
    while mais:
        dispositivo = escritor.begin_page(pagina)
        mais, _ = historia.place(area)
        historia.draw(dispositivo)
        escritor.end_page()
    escritor.close()
    return destino.getvalue()
