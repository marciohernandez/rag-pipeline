"""Prefixo configurável no nome físico das coleções (SPEC-0041).

Fase RED: ``colecoes`` ainda não tem ``nome_fisico_com_prefixo`` e ``AppSettings`` não
tem ``colecao_prefixo``. Os casos provam a regra sem banco; a criação pela API fica
coberta pelos testes de coleção existentes na regressão.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.app import colecoes
from src.app.settings import AppSettings

LIMITE = 80


def _funcao():
    funcao = getattr(colecoes, "nome_fisico_com_prefixo", None)
    assert funcao is not None, "falta colecoes.nome_fisico_com_prefixo(slug, prefixo)"
    return funcao


class _SessaoVazia:
    """Sessão mínima: nenhuma coleção ou base registrada."""

    def execute(self, *_args, **_kwargs):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=list), first=lambda: None)


def test_prefixo_vira_parte_do_nome_fisico_da_colecao_nova() -> None:
    """SPECSFY: SPEC-0041 US-002 FR-003 NFR-003 AC-005"""
    assert _funcao()("Manuais", "beta-") == "beta-Manuais"
    assert _funcao()("politica-RH-v2", "beta-") == "beta-politica-RH-v2"


def test_sem_prefixo_o_nome_fisico_segue_o_comportamento_atual() -> None:
    """SPECSFY: SPEC-0041 US-002 FR-003 NFR-002 AC-006"""
    assert _funcao()("Manuais", "") == "Manuais"
    configuracao = AppSettings(embedding={}, vector_store={})
    assert getattr(configuracao, "colecao_prefixo", None) == ""


def test_prefixo_respeita_o_limite_e_as_reservas(monkeypatch) -> None:
    """SPECSFY: SPEC-0041 US-002 FR-003 NFR-003 AC-007"""
    fisico = _funcao()("a" * 200, "beta-")
    assert fisico.startswith("beta-") and len(fisico) <= LIMITE

    configuracao = AppSettings(
        embedding={},
        vector_store={"collection_name": "beta-sistema"},
        colecao_prefixo="beta-",
    )
    monkeypatch.setattr("src.app.settings.get_settings", lambda: configuracao)
    with pytest.raises(HTTPException) as erro:
        colecoes._exigir_nome_fisico_livre(_SessaoVazia(), _funcao()("sistema", "beta-"), "x")
    assert erro.value.status_code == 409
