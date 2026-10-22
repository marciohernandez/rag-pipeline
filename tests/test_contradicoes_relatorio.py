"""Relatório em Markdown e PDF (SPEC-0038, FR-007, FR-008)."""

from __future__ import annotations

from types import SimpleNamespace

from tests._fase1_contradicoes import exigir


def _dados():
    trecho = lambda arquivo, texto: SimpleNamespace(arquivo=arquivo, texto=texto, imagem=None)
    analise = SimpleNamespace(
        provedor="openrouter",
        dominio_versao_id="dom-3",
        documentos_analisados=2,
        situacao="concluida",
        motivo=None,
        total_assuntos=2,
        concluidos=2,
    )
    ocorrencias = [
        SimpleNamespace(
            assunto="cancelamento",
            etiqueta="conflito",
            impacto="alto",
            trechos=[
                trecho("comercial.md", "Cancelamento em 7 dias."),
                trecho("marketing.md", "Cancelamento em 15 dias."),
            ],
            explicacao="Os prazos de cancelamento divergem.",
            arquivo_mais_antigo=None,
        ),
        SimpleNamespace(
            assunto="horário",
            etiqueta="duplicado",
            impacto="baixo",
            trechos=[
                trecho("a.md", "Atendimento até 18h."),
                trecho("b.md", "Atendemos até as 18h."),
            ],
            explicacao="Mesmo fato repetido.",
            arquivo_mais_antigo=None,
        ),
    ]
    return analise, ocorrencias


def test_spec_0038_ac_017_markdown_agrupa_por_assunto_com_origem_e_explicacao() -> None:
    """SPECSFY: SPEC-0038 US-004 FR-008 AC-017"""
    relatorio = exigir("src.pipeline.contradicoes.relatorio")
    analise, ocorrencias = _dados()

    texto = relatorio.montar_markdown(analise, ocorrencias)

    for esperado in (
        "cancelamento",
        "conflito",
        "comercial.md",
        "marketing.md",
        "Cancelamento em 7 dias.",
        "Os prazos de cancelamento divergem.",
        "openrouter",
        "dom-3",
    ):
        assert esperado in texto
    assert texto.index("cancelamento") < texto.index("horário")
    assert texto.index("comercial.md") < texto.index("marketing.md")


def test_spec_0038_ac_018_pdf_legivel_com_o_mesmo_conteudo_do_markdown() -> None:
    """SPECSFY: SPEC-0038 US-004 FR-008 AC-018"""
    import pymupdf

    relatorio = exigir("src.pipeline.contradicoes.relatorio")
    analise, ocorrencias = _dados()

    pdf = relatorio.montar_pdf(analise, ocorrencias)

    assert pdf.startswith(b"%PDF")
    with pymupdf.open(stream=pdf, filetype="pdf") as documento:
        texto = "".join(pagina.get_text() for pagina in documento)
    for esperado in ("cancelamento", "comercial.md", "marketing.md", "Os prazos de cancelamento"):
        assert esperado in texto


def test_spec_0038_ac_016_markdown_sem_ocorrencias_informa_documentos_analisados() -> None:
    """SPECSFY: SPEC-0038 US-004 FR-008 AC-017"""
    relatorio = exigir("src.pipeline.contradicoes.relatorio")
    analise, _ = _dados()
    analise.documentos_analisados = 8

    texto = relatorio.montar_markdown(analise, [])

    assert "Nenhuma contradição encontrada" in texto
    assert "8" in texto
