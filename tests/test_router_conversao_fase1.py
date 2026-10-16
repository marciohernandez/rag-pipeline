"""Compatibilidade, migração e envio assíncrono da Fase 1 de conversão (SPEC-0036)."""

from __future__ import annotations

import uuid
from pathlib import Path

import psycopg
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from tests._database_safety import configure_testing_environment
from tests._fase1_conversao import (
    AUTH_MEMBER,
    AUTH_OWNER,
    cliente,
    instalar_rede_falsa,
    pagina,
    sem_enfileirar,
)

FIXTURES = Path(__file__).parent / "fixtures" / "spec0023"
REVISAO_ANTERIOR = "0031_conteudo_documento"
NOVAS_COLUNAS = {"origem_url", "abas_disponiveis", "abas_selecionadas", "reprocessado_ia_em"}


def test_spec_0036_ac_024_member_nao_envia_url(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-001 FR-008 NFR-002 AC-024 envio de URL exige escrita"""
    from tests.test_router_conversao import _criar_workspace

    c = cliente(tmp_path, monkeypatch)
    enfileirados = sem_enfileirar(monkeypatch)
    workspace_id = _criar_workspace(c)

    resposta = c.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id, "urls": ["https://exemplo.com/p"]},
        headers=AUTH_MEMBER,
    )

    assert resposta.status_code == 403
    assert enfileirados == []


def test_spec_0036_ac_025_formatos_existentes_continuam_convertendo(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 FR-009 FR-007 NFR-005 AC-025"""
    from tests._fase1_conversao import executar, ler_documento
    from tests.test_router_conversao import _criar_workspace

    c = cliente(tmp_path, monkeypatch)
    enfileirados = sem_enfileirar(monkeypatch)
    workspace_id = _criar_workspace(c)

    resposta = c.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[
            (
                "arquivos",
                ("relatorio.pdf", (FIXTURES / "relatorio.pdf").read_bytes(), "application/pdf"),
            ),
            (
                "arquivos",
                (
                    "planilha.xlsx",
                    (FIXTURES / "planilha.xlsx").read_bytes(),
                    "application/octet-stream",
                ),
            ),
        ],
        headers=AUTH_OWNER,
    )

    assert resposta.status_code == 201
    documentos = resposta.json()["documentos"]
    assert [d["situacao"] for d in documentos] == ["fila", "fila"]  # uma aba: sem seleção
    for documento_id in enfileirados:
        executar(documento_id)
        assert ler_documento(documento_id).situacao == "concluido"
        assert ler_documento(documento_id).avisos == []


def test_spec_0036_ac_028_envio_de_url_responde_sem_buscar(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 NFR-003 US-001 FR-001 AC-028"""
    from tests.test_router_conversao import _criar_workspace

    c = cliente(tmp_path, monkeypatch)
    transporte = instalar_rede_falsa(monkeypatch, pagina())
    enfileirados = sem_enfileirar(monkeypatch)
    workspace_id = _criar_workspace(c)

    resposta = c.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id, "urls": ["https://lento.exemplo.com/p"]},
        headers=AUTH_OWNER,
    )

    assert resposta.status_code == 201
    assert resposta.json()["documentos"][0]["situacao"] == "fila"
    assert transporte.chamadas == []
    assert len(enfileirados) == 1


def test_spec_0036_ac_004_envio_com_endereco_interno_nao_cria_documento(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0036 US-001 FR-002 NFR-001 AC-004 recusa já no envio"""
    from tests.test_router_conversao import _criar_workspace

    c = cliente(tmp_path, monkeypatch)
    transporte = instalar_rede_falsa(monkeypatch, pagina())
    sem_enfileirar(monkeypatch)
    workspace_id = _criar_workspace(c)

    resposta = c.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id, "urls": ["http://127.0.0.1:8000/admin"]},
        headers=AUTH_OWNER,
    )

    assert resposta.status_code == 400
    assert "endereço" in resposta.json()["detail"].lower()
    assert transporte.chamadas == []
    assert c.get(f"/api/v1/conversoes?workspace_id={workspace_id}", headers=AUTH_OWNER).json() == []


@pytest.fixture
def banco_de_scratch(monkeypatch):
    from tests import test_app_migrations as migracoes

    base = make_url(configure_testing_environment())
    schema = f"migration_test_{uuid.uuid4().hex}"
    with psycopg.connect(
        base.set(drivername="postgresql").render_as_string(hide_password=False), autocommit=True
    ) as conexao:
        conexao.execute(psycopg.sql.SQL("CREATE SCHEMA {}").format(psycopg.sql.Identifier(schema)))
    url = base.update_query_dict(
        {"options": f"-csearch_path={schema} -cmax_parallel_workers_per_gather=0"}
    )
    monkeypatch.setattr(migracoes, "BANCO_DE_SCRATCH", url.render_as_string(hide_password=False))
    return migracoes


def test_spec_0036_ac_027_migracao_preserva_lotes_e_documentos(banco_de_scratch) -> None:
    """SPECSFY: SPEC-0036 NFR-005 FR-009 US-003 AC-027"""
    migracoes = banco_de_scratch
    migracoes._executar_alembic("upgrade", REVISAO_ANTERIOR)
    engine = create_engine(migracoes.BANCO_DE_SCRATCH)
    try:
        with engine.begin() as conexao:
            conexao.execute(
                text(
                    "INSERT INTO workspaces (id, tenant_id, project_id, nome, criado_em) "
                    "VALUES ('w1', 't', 'p', 'ws', now())"
                )
            )
            conexao.execute(
                text(
                    "INSERT INTO lotes_conversao (id, tenant_id, project_id, "
                    "workspace_id, criado_em, situacao) "
                    "VALUES ('l1', 't', 'p', 'w1', now(), 'concluido')"
                )
            )
            conexao.execute(
                text(
                    "INSERT INTO documentos_conversao (id, lote_id, nome_arquivo, "
                    "formato, tamanho_bytes, "
                    "avisos, situacao, criado_em) VALUES "
                    "('d1', 'l1', 'a.pdf', 'pdf', 10, '[]', 'concluido', now())"
                )
            )
        migracoes._executar_alembic("upgrade", "head")
        colunas = {c["name"] for c in inspect(engine).get_columns("documentos_conversao")}
        assert colunas >= NOVAS_COLUNAS
        with engine.connect() as conexao:
            linha = conexao.execute(
                text(
                    "SELECT nome_arquivo, situacao, origem_url, abas_disponiveis, "
                    "abas_selecionadas, "
                    "reprocessado_ia_em FROM documentos_conversao WHERE id = 'd1'"
                )
            ).one()
        assert tuple(linha) == ("a.pdf", "concluido", None, None, None, None)
    finally:
        engine.dispose()
