"""Contrato unitário da política de segurança da sincronização."""

from __future__ import annotations

from importlib import import_module, util
from typing import Any

import pytest
from langchain_core.documents import Document


def _policy_class() -> type[Any]:
    """Carrega a política com uma falha TDD legível enquanto ela não existir."""
    module_spec = util.find_spec("src.safety")
    assert module_spec is not None, "SyncSafetyPolicy ainda não foi implementada"
    module = import_module("src.safety")
    policy_class = getattr(module, "SyncSafetyPolicy", None)
    assert policy_class is not None, "src.safety deve expor SyncSafetyPolicy"
    return policy_class


def _chunk(chunk_id: str, project_id: str = "projeto") -> Document:
    return Document(
        page_content="conteúdo",
        metadata={"project_id": project_id, "chunk_id": chunk_id},
    )


def test_rejeita_opcao_destrutiva_com_mensagem_de_migracao() -> None:
    # SPECSFY: US-002 US-003 FR-001 FR-002 NFR-001 AC-001 AC-002 AC-003
    policy = _policy_class()()

    policy.reject_destructive_option(False)
    with pytest.raises(ValueError, match=r"(?i)(?=.*--recreate)(?=.*idempotente)"):
        policy.reject_destructive_option(True)


def test_restringe_modo_espelho_e_preserva_incremental() -> None:
    # SPECSFY: US-001 US-003 FR-002 FR-005 NFR-001 AC-008 AC-009
    policy = _policy_class()()

    policy.assert_sync_mode_supported("qdrant", "mirror")
    policy.assert_sync_mode_supported("chroma", "append")
    policy.assert_sync_mode_supported("pinecone", "append")

    with pytest.raises(ValueError, match=r"(?i)espelho"):
        policy.assert_sync_mode_supported("chroma", "mirror")
    with pytest.raises(ValueError, match=r"(?i)modo"):
        policy.assert_sync_mode_supported("qdrant", "desconhecido")


@pytest.mark.parametrize(
    "chunks",
    [
        [],
        [_chunk("chunk-1", "")],
        [_chunk("chunk-1", "projeto"), _chunk("chunk-2", "outro")],
        [_chunk("", "projeto")],
        [_chunk("repetido", "projeto"), _chunk("repetido", "projeto")],
    ],
)
def test_valida_escopo_logico_antes_de_mutacoes(chunks: list[Document]) -> None:
    # SPECSFY: US-001 US-003 FR-004 FR-007 NFR-001 AC-007 AC-013
    policy = _policy_class()()

    with pytest.raises(ValueError):
        policy.assert_valid_scope(chunks)


def test_retorna_project_id_do_escopo_valido() -> None:
    # SPECSFY: US-001 FR-004 NFR-001 AC-007
    policy = _policy_class()()

    assert policy.assert_valid_scope(
        [_chunk("chunk-1"), _chunk("chunk-2")]
    ) == "projeto"


def test_bloqueia_remocao_sem_confirmacao_completa() -> None:
    # SPECSFY: US-001 FR-003 FR-007 NFR-001 AC-013 AC-014
    policy = _policy_class()()

    with pytest.raises(ValueError, match=r"(?i)vazio"):
        policy.assert_removal_allowed(set(), set())
    with pytest.raises(ValueError, match=r"(?i)confirm"):
        policy.assert_removal_allowed({"novo-1", "novo-2"}, {"novo-1"})


def test_permite_substituicao_total_quando_esperado_esta_confirmado() -> None:
    # SPECSFY: US-001 FR-003 FR-007 NFR-003 AC-015
    policy = _policy_class()()

    policy.assert_removal_allowed({"novo-1", "novo-2"}, {"novo-1", "novo-2"})
