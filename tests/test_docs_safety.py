"""Testes TDD derivados dos cenários BDD documentais da SPEC-0001.

A varredura cobre apenas o material operacional publicado. `specs/` e
`research/` ficam de fora de propósito: eles preservam o estado auditado e
precisam continuar citando o comando removido.
"""

from __future__ import annotations

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

PUBLICADOS = (
    "README.md",
    "GUIA_DE_USO.md",
    "CONTEXTO_MELHORIA_RECUPERACAO_RAG.md",
    "config.yaml",
)

TERMOS_DESTRUTIVOS = ("--recreate", "delete_all", "delete_collection")


def _texto(nome: str) -> str:
    return (RAIZ / nome).read_text(encoding="utf-8")


@pytest.mark.parametrize("nome", PUBLICADOS)
def test_documento_publicado_nao_apresenta_caminho_destrutivo(nome: str) -> None:
    # SPECSFY: US-003 FR-005 FR-006 NFR-002 AC-011
    conteudo = _texto(nome)
    encontrados = [termo for termo in TERMOS_DESTRUTIVOS if termo in conteudo]
    assert encontrados == [], (
        f"{nome} ainda apresenta {encontrados} como procedimento operacional"
    )


def test_guia_publica_recuperacao_idempotente_apoiada_pelo_manifesto() -> None:
    # SPECSFY: US-003 FR-001 FR-006 NFR-002 NFR-003 AC-012
    guia = _texto("GUIA_DE_USO.md").lower()
    assert "manifesto" in guia
    assert "idempotente" in guia
    for termo in TERMOS_DESTRUTIVOS:
        assert termo not in guia
