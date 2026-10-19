"""Proposta de grupos e ordem de imagens por metadados (SPEC-0040).

Contrato assumido: ``src.pipeline.conversion.agrupamento`` expõe
``ArquivoImagem(nome, modificado_em=None, pasta=None)`` e
``propor_grupos(arquivos, intervalo_max=timedelta(minutes=10)) -> PropostaGrupos`` com
``certeza`` (``total`` ou ``incerta``) e ``grupos``; cada grupo tem ``arquivos`` (nomes na ordem
sugerida) e ``certeza``. A proposta usa só nome, data e hora e pasta: nunca lê o conteúdo.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

from tests._fase1_conversao import exigir

BASE = datetime(2026, 10, 16, 10, 0, tzinfo=UTC)


def _arquivo(modulo, nome, minutos, pasta):
    return modulo.ArquivoImagem(nome, BASE + timedelta(minutes=minutos), pasta)


def _nomes(proposta) -> list[list[str]]:
    return [list(g.arquivos) for g in proposta.grupos]


def test_spec_0040_ac_001_tres_conversas_misturadas_viram_tres_grupos() -> None:
    """SPECSFY: SPEC-0040 US-001 FR-001 NFR-002 AC-001"""
    modulo = exigir("src.pipeline.conversion.agrupamento")
    ana = [_arquivo(modulo, f"ana-{i:02d}.png", i, "whatsapp-ana") for i in range(1, 5)]
    bia = [_arquivo(modulo, f"bia-{i}.png", i, "whatsapp-bia") for i in range(1, 5)]
    passos = [_arquivo(modulo, f"passo-{i}.png", 300 + i, "tutorial") for i in range(1, 5)]
    misturadas = [ana[2], passos[1], bia[0], ana[0], passos[3], bia[3], ana[3], bia[1], passos[0]]
    misturadas += [ana[1], bia[2], passos[2]]

    proposta = modulo.propor_grupos(misturadas)

    esperados = [
        [a.nome for a in ana],
        [a.nome for a in bia],
        [a.nome for a in passos],
    ]
    assert sorted(_nomes(proposta)) == sorted(esperados)
    assert proposta.certeza == "total"


def test_spec_0040_ac_001_a_proposta_nao_precisa_do_conteudo_das_imagens() -> None:
    """SPECSFY: SPEC-0040 US-001 FR-001 NFR-002 AC-001"""
    modulo = exigir("src.pipeline.conversion.agrupamento")
    arquivos = [_arquivo(modulo, f"nao-existe-{i}.png", i, "pasta") for i in range(1, 4)]

    proposta = modulo.propor_grupos(arquivos)  # os arquivos não existem no disco

    assert _nomes(proposta) == [[a.nome for a in arquivos]]


def test_spec_0040_ac_002_numeracao_continua_agrupa_e_salto_de_tempo_separa() -> None:
    """SPECSFY: SPEC-0040 US-001 FR-001 NFR-002 AC-002"""
    modulo = exigir("src.pipeline.conversion.agrupamento")
    arquivos = [
        _arquivo(modulo, "print-03.png", 4, "prints"),
        _arquivo(modulo, "print-01.png", 0, "prints"),
        _arquivo(modulo, "print-04.png", 240, "prints"),
        _arquivo(modulo, "print-02.png", 2, "prints"),
    ]

    proposta = modulo.propor_grupos(arquivos)

    assert _nomes(proposta) == [
        ["print-01.png", "print-02.png", "print-03.png"],
        ["print-04.png"],
    ]


def test_spec_0040_ac_002_o_intervalo_maximo_e_configuravel() -> None:
    """SPECSFY: SPEC-0040 US-001 FR-001 NFR-002 AC-002"""
    modulo = exigir("src.pipeline.conversion.agrupamento")
    arquivos = [
        _arquivo(modulo, "tela-01.png", 0, "prints"),
        _arquivo(modulo, "tela-02.png", 30, "prints"),
    ]

    assert len(modulo.propor_grupos(arquivos, intervalo_max=timedelta(minutes=10)).grupos) == 2
    assert len(modulo.propor_grupos(arquivos, intervalo_max=timedelta(minutes=45)).grupos) == 1


def test_spec_0040_ac_003_pistas_ambiguas_geram_proposta_incerta() -> None:
    """SPECSFY: SPEC-0040 US-001 FR-001 FR-002 AC-003"""
    modulo = exigir("src.pipeline.conversion.agrupamento")
    arquivos = [
        modulo.ArquivoImagem(nome, BASE, "mesma-pasta")
        for nome in ("foto.png", "imagem.png", "captura.png", "tela.png")
    ]

    proposta = modulo.propor_grupos(arquivos)

    assert proposta.certeza == "incerta"
    assert proposta.grupos
    assert all(g.certeza == "incerta" for g in proposta.grupos)


def test_spec_0040_ac_003_sem_data_e_sem_pasta_usa_as_pistas_restantes_e_fica_incerta() -> None:
    """SPECSFY: SPEC-0040 US-001 FR-001 FR-002 AC-003"""
    modulo = exigir("src.pipeline.conversion.agrupamento")
    arquivos = [modulo.ArquivoImagem(f"print-{i:02d}.png") for i in (2, 1, 3)]

    proposta = modulo.propor_grupos(arquivos)

    assert _nomes(proposta) == [["print-01.png", "print-02.png", "print-03.png"]]
    assert proposta.certeza == "incerta"


def test_spec_0040_ac_022_cinquenta_imagens_sem_ocr_e_em_ate_dois_segundos(monkeypatch) -> None:
    """SPECSFY: SPEC-0040 FR-001 NFR-003 AC-022"""
    import pytesseract
    from PIL import Image

    modulo = exigir("src.pipeline.conversion.agrupamento")

    def proibido(*args, **kwargs):
        raise AssertionError("a proposta não pode ler o conteúdo da imagem")

    monkeypatch.setattr(pytesseract, "image_to_string", proibido)
    monkeypatch.setattr(Image, "open", proibido)
    arquivos = [_arquivo(modulo, f"img-{i:02d}.png", i // 5, f"pasta-{i % 3}") for i in range(50)]

    inicio = time.perf_counter()
    proposta = modulo.propor_grupos(arquivos)
    duracao = time.perf_counter() - inicio

    assert duracao < 2
    assert sum(len(g.arquivos) for g in proposta.grupos) == 50
