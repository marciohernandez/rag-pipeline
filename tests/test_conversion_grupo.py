"""Conversor do grupo de imagens: seções na ordem aprovada, origem e imagem ilegível (SPEC-0040).

Contrato assumido: ``src.pipeline.conversion.converters.grupo.GrupoImagensConverter(
conversor_imagem=None).converter(caminhos) -> ConversionResult`` converte cada imagem com o
conversor de imagem (injetável), na ordem recebida, e monta uma seção por imagem com a linha
``Origem: <arquivo>``. Imagem sem texto reconhecido vira ``imagem não legível: <arquivo>`` e gera o
aviso ``imagem_nao_legivel``.
"""

from __future__ import annotations

from pathlib import Path

from src.pipeline.conversion.contracts import AvisoConversao, ConversionResult
from tests._fase1_conversao import exigir


class ImagemFalsa:
    def __init__(self, textos: dict[str, str]):
        self.textos = textos
        self.lidos: list[str] = []

    def converter(self, caminho: Path) -> ConversionResult:
        self.lidos.append(caminho.name)
        texto = self.textos.get(caminho.name, "")
        if not texto:
            return ConversionResult(
                markdown=f"_Nenhum texto reconhecido em {caminho.name}._",
                avisos=[
                    AvisoConversao(
                        "ocr_sem_texto_reconhecido", None, "Nenhum texto foi reconhecido."
                    )
                ],
            )
        return ConversionResult(markdown=texto)


def _converter(textos, ordem):
    modulo = exigir("src.pipeline.conversion.converters.grupo")
    falsa = ImagemFalsa(textos)
    conversor = modulo.GrupoImagensConverter(conversor_imagem=falsa)
    return conversor.converter([Path(nome) for nome in ordem]), falsa


def test_spec_0040_ac_007_uma_secao_por_imagem_na_ordem_aprovada_com_origem() -> None:
    """SPECSFY: SPEC-0040 US-002 FR-003 NFR-001 AC-007"""
    resultado, falsa = _converter(
        {"A.png": "texto A", "B.png": "texto B", "C.png": "texto C"}, ["B.png", "A.png", "C.png"]
    )

    md = resultado.markdown
    assert md.count("Origem:") == 3
    assert md.index("Origem: B.png") < md.index("Origem: A.png") < md.index("Origem: C.png")
    assert md.index("texto B") < md.index("texto A") < md.index("texto C")
    assert md.index("Origem: B.png") < md.index("texto B") < md.index("Origem: A.png")
    assert falsa.lidos == ["B.png", "A.png", "C.png"]
    assert resultado.avisos == []


def test_spec_0040_ac_007_o_markdown_do_grupo_respeita_o_contrato_sem_frontmatter() -> None:
    """SPECSFY: SPEC-0040 US-002 FR-003 NFR-001 AC-007"""
    resultado, _ = _converter({"A.png": "texto A"}, ["A.png"])

    assert not resultado.markdown.lstrip().startswith("---")
    assert "Origem: A.png" in resultado.markdown


def test_spec_0040_ac_009_imagem_ilegivel_e_sinalizada_e_marca_revisar() -> None:
    """SPECSFY: SPEC-0040 US-003 FR-004 AC-009"""
    resultado, _ = _converter({"A.png": "texto A", "C.png": "texto C"}, ["A.png", "B.png", "C.png"])

    md = resultado.markdown
    assert "imagem não legível: B.png" in md
    assert md.index("texto A") < md.index("imagem não legível: B.png") < md.index("texto C")
    codigos = [a.codigo for a in resultado.avisos]
    assert codigos == ["imagem_nao_legivel"]
    assert "imagem não legível: B.png" in resultado.avisos[0].mensagem


def test_spec_0040_ac_011_relatorio_do_lote_lista_imagem_ilegivel_e_tabela_complexa() -> None:
    """SPECSFY: SPEC-0040 US-003 FR-004 AC-011"""
    import src.pipeline.service as service  # noqa: PLR0402

    tabelas = exigir("src.pipeline.conversion.tabelas")
    grupo, _ = _converter({}, ["B.png"])
    complexa = tabelas.normalizar_tabelas(
        [[tabelas.Tabela([["a", "b"], ["c", "d"]], mesclada=True)]]
    )

    relatorio = service.montar_relatorio_limpeza(
        [
            {"arquivo": "grupo-1.md", "revisar": [a.mensagem for a in grupo.avisos]},
            {"arquivo": "planos.docx", "revisar": [a.mensagem for a in complexa.avisos]},
        ],
        [],
        ia_usada=False,
        provedor=None,
        dominio_versao=None,
    )

    assert "grupo-1.md: imagem não legível: B.png" in relatorio
    assert "planos.docx: tabela complexa virou texto" in relatorio


def test_spec_0040_ac_024_a_ordem_aprovada_nao_e_reordenada_ao_refazer() -> None:
    """SPECSFY: SPEC-0040 FR-003 NFR-001 AC-024"""
    textos = {"a.png": "A", "b.png": "B", "c.png": "C"}
    primeira, _ = _converter(textos, ["c.png", "a.png", "b.png"])
    segunda, _ = _converter(textos, ["c.png", "a.png", "b.png"])

    assert primeira.markdown == segunda.markdown
    assert primeira.markdown.index("Origem: c.png") < primeira.markdown.index("Origem: a.png")
