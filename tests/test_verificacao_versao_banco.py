"""Verificação da versão do banco na subida dos serviços (SPEC-0042, US-002).

Fase RED: ``src.app.db.verificar_banco_migrado`` e ``BancoNaoMigrado`` ainda não existem.
A interface que estes casos fixam é ``verificar_banco_migrado(engine=None) -> None``, que
levanta ``BancoNaoMigrado`` (um ``RuntimeError``) quando ``alembic_version`` falta ou está
atrás do head, com uma mensagem que remete a ``alembic upgrade head`` e nunca traz host,
usuário nem senha.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url

from tests._banco_scratch import alembic, cabeca, novo_banco, tabelas, versao

DDL = re.compile(r"^\s*(CREATE|ALTER|DROP)\b", re.IGNORECASE)
REVISAO_ANTIGA = "0039_decisoes_empresa"


def _verificador():
    from src.app import db

    funcao = getattr(db, "verificar_banco_migrado", None)
    classe = getattr(db, "BancoNaoMigrado", None)
    assert funcao is not None, "src.app.db.verificar_banco_migrado ainda não existe"
    assert classe is not None, "src.app.db.BancoNaoMigrado ainda não existe"
    return funcao, classe


def _migrar(url: str, destino: str = "head") -> None:
    resultado = alembic(url, "upgrade", destino)
    assert resultado.returncode == 0, resultado.stderr


def _em_paralelo(url: str, quantidade: int = 2) -> list[Exception | None]:
    funcao, _ = _verificador()

    def rodar(_: int) -> Exception | None:
        engine = create_engine(url)
        try:
            funcao(engine)
            return None
        except Exception as erro:  # noqa: BLE001 — o caso inspeciona o erro
            return erro
        finally:
            engine.dispose()

    with ThreadPoolExecutor(quantidade) as pool:
        return list(pool.map(rodar, range(quantidade)))


def test_subida_em_banco_migrado_nao_emite_ddl() -> None:
    """SPECSFY: SPEC-0042 US-002 FR-002 NFR-003 AC-004"""
    funcao, _ = _verificador()
    url = novo_banco()
    _migrar(url)
    engine = create_engine(url)
    instrucoes: list[str] = []

    @event.listens_for(engine, "before_cursor_execute")
    def _registrar(conexao, cursor, statement, parametros, contexto, varias) -> None:
        instrucoes.append(statement)

    try:
        funcao(engine)
    finally:
        engine.dispose()

    assert instrucoes, "a verificação precisa consultar o banco"
    assert [i for i in instrucoes if DDL.match(i)] == []


def test_banco_sem_alembic_version_para_com_mensagem_sem_credenciais() -> None:
    """SPECSFY: SPEC-0042 US-002 FR-003 NFR-001 AC-005"""
    funcao, banco_nao_migrado = _verificador()
    url = novo_banco()
    engine = create_engine(url)
    destino = make_url(url)

    try:
        with pytest.raises(banco_nao_migrado) as capturado:
            funcao(engine)
    finally:
        engine.dispose()

    mensagem = str(capturado.value)
    assert "alembic upgrade head" in mensagem
    for segredo in (destino.host, destino.username, destino.password, str(destino.port)):
        assert segredo and segredo not in mensagem
    assert tabelas(url) == [], "a verificação não pode criar tabelas"


def test_banco_atras_do_head_para_com_a_mensagem_de_migracao_pendente() -> None:
    """SPECSFY: SPEC-0042 US-002 FR-003 AC-006"""
    funcao, banco_nao_migrado = _verificador()
    url = novo_banco()
    _migrar(url, REVISAO_ANTIGA)
    assert versao(url) == REVISAO_ANTIGA != cabeca()
    antes = tabelas(url)
    engine = create_engine(url)

    try:
        with pytest.raises(banco_nao_migrado) as capturado:
            funcao(engine)
    finally:
        engine.dispose()

    assert "alembic upgrade head" in str(capturado.value)
    assert tabelas(url) == antes


def test_tabela_ausente_com_versao_no_head_nao_e_recriada() -> None:
    """SPECSFY: SPEC-0042 US-002 FR-002 AC-007"""
    funcao, _ = _verificador()
    url = novo_banco()
    assert alembic(url, "stamp", "head").returncode == 0
    assert tabelas(url) == ["alembic_version"]
    engine = create_engine(url)

    try:
        funcao(engine)
    finally:
        engine.dispose()

    assert tabelas(url) == ["alembic_version"], "a subida não pode completar o schema"


def test_dois_servicos_em_banco_migrado_sobem_sem_disputa() -> None:
    """SPECSFY: SPEC-0042 US-002 NFR-003 AC-015"""
    _verificador()
    url = novo_banco()
    _migrar(url)
    antes = tabelas(url)

    resultados = _em_paralelo(url)

    assert resultados == [None, None]
    assert tabelas(url) == antes


def test_dois_servicos_em_banco_nao_migrado_encerram_sem_criar_tabela() -> None:
    """SPECSFY: SPEC-0042 US-002 FR-003 NFR-003 AC-016"""
    _, banco_nao_migrado = _verificador()
    url = novo_banco()

    resultados = _em_paralelo(url)

    assert [type(r) for r in resultados] == [banco_nao_migrado, banco_nao_migrado]
    assert all("alembic upgrade head" in str(r) for r in resultados)
    assert tabelas(url) == []
