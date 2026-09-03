"""Testes TDD do gate de bloqueio de indexação por status (SPEC-0002)."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module, util
from typing import Any

from langchain_core.documents import Document


def _filter_by_status() -> Callable[..., Any]:
    """Carrega o gate com uma falha TDD legível enquanto ele não existir."""
    module_spec = util.find_spec("src.status_gate")
    assert module_spec is not None, "src.status_gate ainda não foi implementado"
    module = import_module("src.status_gate")
    func = getattr(module, "filter_by_status", None)
    assert func is not None, "src.status_gate deve expor filter_by_status"
    return func


def _document(nome: str, *, status: str | None = None) -> Document:
    metadata: dict[str, Any] = {
        "nome_arquivo": nome,
        "caminho_relativo": f"base/{nome}",
    }
    if status is not None:
        metadata["status"] = status
    return Document(page_content="Conteúdo.", metadata=metadata)


def test_documento_com_status_bloqueante_e_excluido() -> None:
    # SPECSFY: US-003 FR-005 NFR-003 AC-009
    filter_by_status = _filter_by_status()
    documentos = [_document("reprovado.md", status="reprovado")]

    mantidos, excluidos = filter_by_status(documentos, ["reprovado"])

    assert mantidos == []
    assert len(excluidos) == 1
    assert excluidos[0]["status"] == "reprovado"


def test_documento_com_status_fora_da_lista_e_mantido() -> None:
    # SPECSFY: US-003 FR-005 NFR-002 AC-010
    filter_by_status = _filter_by_status()
    documentos = [_document("aprovado.md", status="aprovado")]

    mantidos, excluidos = filter_by_status(documentos, ["reprovado"])

    assert mantidos == documentos
    assert excluidos == []


def test_documento_sem_status_e_mantido_fail_open() -> None:
    # SPECSFY: US-003 FR-005 NFR-002 AC-011
    filter_by_status = _filter_by_status()
    documentos = [_document("sem-status.md")]

    mantidos, excluidos = filter_by_status(documentos, ["reprovado"])

    assert mantidos == documentos
    assert excluidos == []


def test_registro_de_exclusao_nao_expoe_segredos() -> None:
    # SPECSFY: US-003 FR-005 NFR-003 AC-022
    filter_by_status = _filter_by_status()
    documentos = [_document("reprovado.md", status="reprovado")]

    _, excluidos = filter_by_status(documentos, ["reprovado"])

    registro = str(excluidos[0])
    assert "reprovado.md" in registro or "base/reprovado.md" in registro
    assert "reprovado" in registro
    for termo_sensivel in ("api_key", "senha", "token", "secret"):
        assert termo_sensivel not in registro.lower()


def test_manifesto_conta_documentos_excluidos_por_status() -> None:
    # SPECSFY: US-003 FR-005 NFR-003 AC-023
    filter_by_status = _filter_by_status()
    documentos = [
        _document("aprovado.md", status="aprovado"),
        _document("reprovado.md", status="reprovado"),
    ]

    mantidos, excluidos = filter_by_status(documentos, ["reprovado"])

    assert len(mantidos) == 1
    assert len(excluidos) == 1
