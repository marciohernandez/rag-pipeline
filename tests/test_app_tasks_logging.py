"""Log diagnosticável de falha no worker (SPEC-0012, Fase 11, FR-010).

`process_base_task` captura qualquer exceção do pipeline e grava um `erro`
genérico em `Execution`, por NFR-002. Até esta fase ele não registrava nada
em log, então a própria mensagem exibida — "ver logs do worker para detalhes"
— apontava para um log que não existia. Estes casos provam que o registro
passa a existir (AC-014), que ele não carrega credencial (AC-015) e que o
campo devolvido pela API continua genérico (AC-016).
"""

from __future__ import annotations

import logging

import pytest

import src.app.main  # noqa: F401 — efeito colateral: liga o engine e cria as tabelas
from src.app import settings
from src.app.db import SessionLocal
from src.app.models import Base, Execution
from src.app.settings import AppSettings
from src.app.tasks import process_base_task

SENHA_FALSA = "senha-falsa-do-teste-4f2b"
DSN_FALSO = f"postgresql://postgres:{SENHA_FALSA}@db.invalido:5432/rag"


@pytest.fixture
def execucao_que_falha(monkeypatch) -> str:
    """Uma `Execution` pendente cujo pipeline quebra ao materializar a base.

    O erro é injetado em `get_storage` — antes de qualquer rede — para que o
    caso não dependa de Qdrant, embeddings ou disco.
    """
    monkeypatch.setattr(
        settings,
        "_SETTINGS",
        AppSettings(
            embedding={"provider": "fake", "dimensions": 16},
            vector_store={"provider": "qdrant", "collection_name": "logging-test"},
        ),
    )

    def explodir_com_credencial_na_mensagem(*args, **kwargs):
        raise ConnectionError(f"não foi possível conectar usando {DSN_FALSO}")

    monkeypatch.setattr(
        "src.app.storage.get_storage", explodir_com_credencial_na_mensagem
    )

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-que-falha.md",
            origem="upload",
            documentos=1,
        )
        session.add(base)
        session.commit()
        execution = Execution(base_id=base.id, situacao="pending", etapa="")
        session.add(execution)
        session.commit()
        return execution.id


def _processar(execution_id: str) -> None:
    with SessionLocal() as session:
        execution = session.get(Execution, execution_id)
        base_id = execution.base_id
    process_base_task.func(
        execution_id,
        base_id=base_id,
        tenant_id="tenant-1",
        project_id="projeto-1",
        embedding={"provider": "fake", "dimensions": 16},
        vector_store={"provider": "qdrant", "collection_name": "logging-test"},
    )


def test_falha_registra_causa_diagnosticavel_no_log(
    execucao_que_falha, caplog
) -> None:
    """SPECSFY: US-001 US-002 FR-010 AC-014

    Uma execução que falha deixa no log do worker o tipo da exceção e a etapa
    alcançada — o bastante para diagnosticar sem reproduzir o problema.
    """
    with caplog.at_level(logging.ERROR):
        _processar(execucao_que_falha)

    registros = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert registros, (
        "nenhum registro de nível ERROR — a falha foi engolida pelo except e "
        'a mensagem "ver logs do worker para detalhes" continua sendo falsa'
    )
    texto = "\n".join(r.getMessage() for r in registros)
    assert "ConnectionError" in texto, f"tipo da exceção ausente no log: {texto!r}"
    assert "carregando" in texto or "chunking" in texto, (
        f"etapa alcançada ausente no log: {texto!r}"
    )


def test_log_de_falha_nao_expoe_credencial(execucao_que_falha, caplog) -> None:
    """SPECSFY: US-001 FR-010 NFR-002 AC-015

    A exceção injetada traz uma string de conexão com senha na própria
    mensagem — o caso real que FIND-SEC-004 descreve. O log precisa identificar
    a falha sem repassar esse conteúdo.
    """
    with caplog.at_level(logging.ERROR):
        _processar(execucao_que_falha)

    texto = "\n".join(r.getMessage() for r in caplog.records)
    assert texto.strip(), "nenhum log registrado — AC-015 não pode ser provado"
    assert SENHA_FALSA not in texto, f"credencial vazou no log: {texto!r}"
    assert DSN_FALSO not in texto, f"string de conexão vazou no log: {texto!r}"
    assert "ConnectionError" in texto, (
        f"o log sanitizou demais e não identifica a falha: {texto!r}"
    )


def test_erro_devolvido_pela_api_continua_generico(
    execucao_que_falha, caplog
) -> None:
    """SPECSFY: US-001 FR-010 NFR-002 AC-016

    O detalhe técnico fica no log; o campo `erro` persistido — que a API e o
    frontend expõem — continua com a mensagem segura de sempre.
    """
    with caplog.at_level(logging.ERROR):
        _processar(execucao_que_falha)

    # O Given do AC-016 é uma falha *já registrada no log*: sem isso não há
    # separação entre detalhe e mensagem segura para provar.
    texto = "\n".join(r.getMessage() for r in caplog.records)
    assert "ConnectionError" in texto, (
        "o detalhe técnico não chegou ao log, então o cenário do AC-016 não "
        f"chega a existir: {texto!r}"
    )

    with SessionLocal() as session:
        execution = session.get(Execution, execucao_que_falha)
        assert execution.situacao == "failed"
        assert execution.erro == (
            "Falha ao processar a base; ver logs do worker para detalhes."
        )
        assert SENHA_FALSA not in (execution.erro or "")
        assert "ConnectionError" not in (execution.erro or "")
