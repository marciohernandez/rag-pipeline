"""Inicialização do backend e do worker sem criar tabelas (SPEC-0042, US-002).

Fase RED: ``src.app.main`` ainda chama ``db.create_tables()`` na importação, o backend não
verifica a versão do banco ao subir e ``src.app.worker`` não tem ``main()``.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from tests._banco_scratch import RAIZ, novo_banco, tabelas


class _Parou(Exception):
    """Sinal de que a verificação de versão foi chamada na inicialização."""


def _verificacao_que_para(monkeypatch) -> None:
    from src.app import db

    def verificar(*_args, **_kwargs) -> None:
        raise _Parou

    monkeypatch.setattr(db, "verificar_banco_migrado", verificar, raising=False)


def test_importar_o_main_nao_cria_tabelas_nem_exige_banco_migrado() -> None:
    """SPECSFY: SPEC-0042 US-002 FR-002 NFR-002 AC-014"""
    url = novo_banco()
    ambiente = dict(os.environ)
    ambiente["APP_DATABASE_URL"] = url

    resultado = subprocess.run(
        [sys.executable, "-c", "import src.app.main"],
        cwd=str(RAIZ),
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert tabelas(url) == [], "importar o módulo não pode criar tabelas"


def test_backend_verifica_a_versao_do_banco_na_inicializacao(monkeypatch) -> None:
    """SPECSFY: SPEC-0042 US-002 FR-003 NFR-001 AC-005"""
    from fastapi.testclient import TestClient

    from src.app.main import app

    _verificacao_que_para(monkeypatch)

    with pytest.raises(_Parou), TestClient(app):
        pass


def test_worker_verifica_a_versao_do_banco_antes_de_rodar(monkeypatch) -> None:
    """SPECSFY: SPEC-0042 US-002 FR-003 NFR-003 AC-016"""
    from src.app import tasks, worker

    chamadas: list[dict] = []
    _verificacao_que_para(monkeypatch)
    monkeypatch.setattr(tasks.app, "run_worker", lambda **kwargs: chamadas.append(kwargs))
    principal = getattr(worker, "main", None)
    assert principal is not None, "src.app.worker.main ainda não existe"

    with pytest.raises(_Parou):
        principal()

    assert chamadas == [], "o worker não pode rodar com o banco não verificado"
