"""Testes de preservação estrutural dos conversores (SPEC-0023)."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "spec0023"


def test_spec_0023_ac_003_docx_preserva_titulos_e_tabela() -> None:
    """SPECSFY: SPEC-0023 US-001 FR-003 AC-003"""
    from src.pipeline.conversion.converters.docx import DocxConverter

    resultado = DocxConverter().converter(FIXTURES / "estrutura.docx")

    assert "# Relatório de atendimento" in resultado.markdown
    assert "## Indicadores" in resultado.markdown
    assert "| Canal | Total |" in resultado.markdown
    assert "| Telefone | 12 |" in resultado.markdown


def test_spec_0023_ac_003_xlsx_cria_secao_para_cada_planilha() -> None:
    """SPECSFY: SPEC-0023 US-001 FR-003 AC-003"""
    from src.pipeline.conversion.converters.xlsx import XlsxConverter

    resultado = XlsxConverter().converter(FIXTURES / "duas-planilhas.xlsx")

    assert "## Resumo" in resultado.markdown
    assert "| Indicador | Valor |" in resultado.markdown
    assert "| Documentos | 3 |" in resultado.markdown
    assert "## Detalhes" in resultado.markdown
    assert "| Arquivo | Situação |" in resultado.markdown
    assert "| relatorio.pdf | Concluído |" in resultado.markdown
