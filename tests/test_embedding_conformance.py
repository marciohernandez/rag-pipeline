"""Suíte de conformidade de embeddings — TDD informado pelo BDD da SPEC-0003.

AC-004 (parte de embeddings): o adapter fake é determinístico e respeita a
dimensão configurada, servindo de oráculo estável para o núcleo de conformidade
sem acesso remoto. Enquanto ``src/providers/`` não existir, cada caso falha por
comportamento ausente.
"""

from __future__ import annotations

DIMENSIONS = 8


def _fake_embeddings():
    from src.providers.factory import ProviderFactory

    return ProviderFactory.create_embedding("fake", {"dimensions": DIMENSIONS})


def test_fake_respeita_a_dimensao_configurada() -> None:
    # SPECSFY: US-001 US-002 FR-001 FR-003 FR-008 NFR-004 AC-004
    adapter = _fake_embeddings()

    documentos = adapter.embed_documents(["alpha", "beta"])
    assert [len(vetor) for vetor in documentos] == [DIMENSIONS, DIMENSIONS]
    assert len(adapter.embed_query("alpha")) == DIMENSIONS


def test_fake_e_deterministico_para_a_mesma_entrada() -> None:
    # SPECSFY: US-001 US-002 FR-001 FR-003 FR-008 NFR-004 AC-004
    adapter = _fake_embeddings()

    assert adapter.embed_documents(["alpha"]) == adapter.embed_documents(["alpha"])
    assert adapter.embed_query("alpha") == adapter.embed_documents(["alpha"])[0]


def test_fake_separa_entradas_diferentes() -> None:
    # SPECSFY: US-001 US-002 FR-001 FR-003 FR-008 NFR-004 AC-004
    adapter = _fake_embeddings()

    alpha, beta = adapter.embed_documents(["alpha", "beta"])
    assert alpha != beta
