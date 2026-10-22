"""Migration do schema da fila Procrastinate (SPEC-0042, US-001 e US-004).

Fase RED: ``alembic upgrade head`` ainda não cria as tabelas ``procrastinate_*``; a
cadeia termina em ``0040_grupos_e_tabelas``. Os casos rodam em schemas de scratch.
"""

from __future__ import annotations

from tests._banco_scratch import (
    REVISAO_ANTERIOR,
    alembic,
    aplicar_fila_a_mao,
    cabeca,
    criar_como_o_create_all,
    novo_banco,
    tabelas,
    tabelas_da_fila,
    versao,
)


def test_banco_vazio_recebe_app_fila_e_versao_no_head() -> None:
    """SPECSFY: SPEC-0042 US-001 FR-001 AC-001"""
    url = novo_banco()

    resultado = alembic(url, "upgrade", "head")

    assert resultado.returncode == 0, resultado.stderr
    assert versao(url) == cabeca()
    assert "workspaces" in tabelas(url)
    assert "procrastinate_jobs" in tabelas_da_fila(url), "a fila não foi criada pelo Alembic"


def test_segundo_upgrade_nao_altera_o_schema_da_fila() -> None:
    """SPECSFY: SPEC-0042 US-001 FR-001 NFR-002 AC-002"""
    url = novo_banco()
    assert alembic(url, "upgrade", "head").returncode == 0
    assert "procrastinate_jobs" in tabelas_da_fila(url), "a fila não foi criada pelo Alembic"
    antes = (tabelas(url), versao(url))

    resultado = alembic(url, "upgrade", "head")

    assert resultado.returncode == 0, resultado.stderr
    assert (tabelas(url), versao(url)) == antes


def test_fila_aplicada_a_mao_nao_quebra_a_migration() -> None:
    """SPECSFY: SPEC-0042 US-001 FR-001 AC-003"""
    url = novo_banco()
    aplicar_fila_a_mao(url)
    fila_antes = tabelas_da_fila(url)
    assert "procrastinate_jobs" in fila_antes

    resultado = alembic(url, "upgrade", "head")

    assert resultado.returncode == 0, resultado.stderr
    assert versao(url) == cabeca()
    assert cabeca() != REVISAO_ANTERIOR, "a cadeia ainda não tem a migration da fila"
    assert tabelas_da_fila(url) == fila_antes


def test_banco_do_create_all_e_adotado_com_stamp_head() -> None:
    """SPECSFY: SPEC-0042 US-004 FR-005 AC-011"""
    url = novo_banco()
    criar_como_o_create_all(url)
    aplicar_fila_a_mao(url)
    assert versao(url) is None

    adocao = alembic(url, "stamp", "head")
    resultado = alembic(url, "upgrade", "head")

    assert adocao.returncode == 0, adocao.stderr
    assert resultado.returncode == 0, resultado.stderr
    assert versao(url) == cabeca()
    assert cabeca() != REVISAO_ANTERIOR, "a cadeia ainda não tem a migration da fila"
    assert "procrastinate_jobs" in tabelas_da_fila(url)
