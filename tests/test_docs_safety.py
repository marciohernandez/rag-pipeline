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
    "config.example.yaml",
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


# --- SPEC-0008: contrato da fronteira interna publicado em docs/architecture.md ---

CONTRATO = "docs/architecture.md"
DIVIDAS_BLOQUEANTES = ("BACKLOG-0012", "BACKLOG-0013")
OPERACOES_DA_FACHADA = (
    "run_pipeline",
    "sync_vector_store",
    "validate_retrieval",
    "query_base",
)


def test_contrato_da_fronteira_documenta_fachada_entrypoints_config_e_limites() -> None:
    # SPECSFY: US-003 FR-007 NFR-003 AC-009
    contrato = _texto(CONTRATO).lower()
    assert "src/pipeline/service.py" in contrato
    assert "src/app/" in contrato
    entrypoints = ("pipeline.py", "search.py", "chat.py", "validate.py", "upsert_from_chunks.py")
    for entrypoint in entrypoints:
        assert entrypoint in contrato, f"contrato não cita o entrypoint {entrypoint}"
    assert "configuração" in contrato and "parâmetro" in contrato
    assert "síncrona" in contrato, "o limite de execução síncrona precisa estar declarado"


def test_contrato_declara_as_dividas_bloqueantes_com_identificador() -> None:
    # SPECSFY: US-003 FR-002 FR-007 NFR-002 AC-010
    contrato = _texto(CONTRATO)
    faltando = [d for d in DIVIDAS_BLOQUEANTES if d not in contrato]
    assert faltando == [], f"dívidas bloqueantes ausentes no contrato: {faltando}"
    baixo = contrato.lower()
    assert "bloqueante" in baixo or "impedimento" in baixo
    assert "reabrir" in baixo and "spec-0008" in baixo


def test_toda_operacao_publica_da_fachada_aparece_no_contrato() -> None:
    # SPECSFY: US-003 FR-003 FR-007 NFR-003 AC-013
    import importlib

    servico = importlib.import_module("src.pipeline.service")
    publicas = {
        nome
        for nome in dir(servico)
        if not nome.startswith("_") and callable(getattr(servico, nome))
        and getattr(getattr(servico, nome), "__module__", "") == servico.__name__
    }
    contrato = _texto(CONTRATO)
    nao_documentadas = sorted(nome for nome in publicas if nome not in contrato)
    assert nao_documentadas == [], f"operações da fachada fora do contrato: {nao_documentadas}"
    assert publicas, "a fachada precisa expor operações públicas"
    documentadas_inexistentes = [
        nome for nome in OPERACOES_DA_FACHADA if nome in contrato and nome not in publicas
    ]
    assert documentadas_inexistentes == [], (
        f"contrato cita operações que a fachada não expõe: {documentadas_inexistentes}"
    )
