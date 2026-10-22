"""Publicação atômica quando o enfileiramento falha (SPEC-0042, US-003).

Fase RED: ``POST /api/v1/envios`` grava coleção e envio antes de enfileirar; se o
enfileiramento falha, a resposta é um 500 genérico e os registros ficam órfãos.
"""

from __future__ import annotations

import logging

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from tests._colecoes import (
    OWNER,
    criar_colecao,
    enviar,
    md,
    preparar,
    texto_com_secoes,
)
from tests._pessoas import sessao_do_banco

SEGREDO = "SENHA-SECRETA-9f3"
HOST_INTERNO = "host-interno-db"
FALHA_DA_FILA = f"postgresql://usuario:{SEGREDO}@{HOST_INTERNO}:5432/db recusou o envio"


def _fila_que_falha(ambiente, monkeypatch) -> dict[str, bool]:
    """Faz ``agendar_envio`` falhar enquanto ``estado['falhar']`` for verdadeiro."""
    from src.app import publicacao

    original = publicacao.agendar_envio
    estado = {"falhar": True}

    def agendar(envio_id: str, colecao_id: str) -> None:
        if estado["falhar"]:
            raise RuntimeError(FALHA_DA_FILA)
        original(envio_id, colecao_id)

    monkeypatch.setattr(publicacao, "agendar_envio", agendar)
    from src.app.main import app

    ambiente.client = TestClient(app, raise_server_exceptions=False)
    return estado


def _contagens(workspace_id: str) -> tuple[int, int]:
    from src.app.models import Colecao, Envio

    with sessao_do_banco() as sessao:
        colecoes = sessao.scalar(
            select(func.count()).select_from(Colecao).where(Colecao.workspace_id == workspace_id)
        )
        envios = sessao.scalar(select(func.count()).select_from(Envio))
    return colecoes, envios


def _arquivos_guardados(ambiente) -> list[str]:
    if not ambiente.pasta.exists():
        return []
    return sorted(str(p) for p in ambiente.pasta.rglob("*") if p.is_file())


def test_falha_na_fila_com_colecao_nova_nao_deixa_registro_e_permite_repetir(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0042 US-003 FR-004 AC-008"""
    ambiente = preparar(tmp_path, monkeypatch)
    estado = _fila_que_falha(ambiente, monkeypatch)

    resposta = enviar(ambiente, [md("a.md", texto_com_secoes(2))], nova="X", executar=False)

    assert resposta.status_code == 503, resposta.text
    assert _contagens(ambiente.workspace_id) == (0, 0)
    assert _arquivos_guardados(ambiente) == []
    estado["falhar"] = False
    de_novo = enviar(ambiente, [md("a.md", texto_com_secoes(2))], nova="X", executar=False)
    assert de_novo.status_code == 201, de_novo.text


def test_falha_na_fila_em_colecao_existente_remove_so_o_envio_do_pedido(
    tmp_path, monkeypatch, caplog
) -> None:
    """SPECSFY: SPEC-0042 US-003 FR-004 NFR-001 AC-009"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "X", [md("a.md", texto_com_secoes(2))])
    antes = _contagens(ambiente.workspace_id)
    arquivos_antes = _arquivos_guardados(ambiente)
    estado = _fila_que_falha(ambiente, monkeypatch)
    assert estado["falhar"]

    with caplog.at_level(logging.WARNING):
        resposta = enviar(
            ambiente, [md("b.md", texto_com_secoes(2, "v2"))], colecao_id=colecao_id, executar=False
        )

    assert resposta.status_code == 503, resposta.text
    assert _contagens(ambiente.workspace_id) == antes
    assert _arquivos_guardados(ambiente) == arquivos_antes
    listagem = ambiente.client.get(
        f"/api/v1/workspaces/{ambiente.workspace_id}/colecoes", headers=OWNER
    ).json()
    assert [c["nome"] for c in listagem] == ["X"]
    assert any("enfileirar" in r.getMessage().lower() for r in caplog.records)
    assert SEGREDO not in caplog.text and HOST_INTERNO not in caplog.text


def test_nova_tentativa_depois_da_falha_grava_uma_vez_e_enfileira(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0042 US-003 FR-004 AC-010"""
    ambiente = preparar(tmp_path, monkeypatch)
    estado = _fila_que_falha(ambiente, monkeypatch)
    primeira = enviar(ambiente, [md("a.md", texto_com_secoes(2))], nova="X", executar=False)
    assert primeira.status_code == 503, primeira.text
    estado["falhar"] = False

    segunda = enviar(ambiente, [md("a.md", texto_com_secoes(2))], nova="X", executar=False)

    assert segunda.status_code == 201, segunda.text
    assert _contagens(ambiente.workspace_id) == (1, 1)
    assert [a["envio_id"] for a in ambiente.agendamentos] == [segunda.json()["envio_id"]]


def test_resposta_da_falha_nao_traz_detalhes_internos(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0042 US-003 FR-004 NFR-001 AC-017"""
    ambiente = preparar(tmp_path, monkeypatch)
    _fila_que_falha(ambiente, monkeypatch)

    resposta = enviar(ambiente, [md("a.md", texto_com_secoes(2))], nova="X", executar=False)

    assert resposta.status_code == 503, resposta.text
    corpo = resposta.text
    assert "não foi possível iniciar o envio" in corpo.lower()
    for proibido in (SEGREDO, HOST_INTERNO, "postgresql://", "Traceback", "RuntimeError"):
        assert proibido not in corpo
