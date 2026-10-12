"""Conversor de XLSX para Markdown via openpyxl (SPEC-0023)."""

from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from src.pipeline.conversion.contracts import ConversionError, ConversionResult


def _celula_para_texto(valor: object) -> str:
    return "" if valor is None else str(valor)


def _planilha_para_tabela(linhas: list[tuple]) -> str | None:
    if not linhas:
        return None
    cabecalho, *dados = ([_celula_para_texto(v) for v in linha] for linha in linhas)
    partes = [
        f"| {' | '.join(cabecalho)} |",
        f"| {' | '.join('---' for _ in cabecalho)} |",
    ]
    partes.extend(f"| {' | '.join(linha)} |" for linha in dados)
    return "\n".join(partes)


class XlsxConverter:
    """Transforma cada planilha em uma seção Markdown com tabela."""

    def converter(self, caminho: Path) -> ConversionResult:
        try:
            pasta_de_trabalho = load_workbook(str(caminho), read_only=True, data_only=True)
        except Exception as erro:
            raise ConversionError(f"Falha ao converter XLSX: {caminho.name}") from erro

        secoes: list[str] = []
        for planilha in pasta_de_trabalho.worksheets:
            cabecalho = f"## {planilha.title}"
            tabela = _planilha_para_tabela(list(planilha.iter_rows(values_only=True)))
            secoes.append("\n\n".join([cabecalho, tabela] if tabela else [cabecalho]))

        return ConversionResult(markdown="\n\n".join(secoes))
