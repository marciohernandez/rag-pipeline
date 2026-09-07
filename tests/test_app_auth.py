"""Testes de autenticação e autorização do backend de aplicação (SPEC-0012)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_owner_executa_fluxo_completo(vector_store_em_memoria) -> None:
    """SPECSFY: US-003 FR-001 FR-003 FR-004 FR-005 FR-006 FR-007 FR-009 NFR-003 AC-007"""
    from src.app.main import app

    client = TestClient(app)
    headers = {"Authorization": "Bearer token-demo-owner"}

    envio = client.post(
        "/api/v1/bases",
        files=[("arquivos", ("doc.md", b"# Titulo\nConteudo", "text/markdown"))],
        headers=headers,
    )
    assert envio.status_code == 201
    base_id = envio.json()["base_id"]

    inicio = client.post(f"/api/v1/bases/{base_id}/executions", headers=headers)
    assert inicio.status_code == 202
    execution_id = inicio.json()["execution_id"]

    # A repetição só é aceita se a execução já tiver falhado; aqui apenas
    # comprovamos que o owner tem permissão para tentar (não é um 401/403).
    repeticao = client.post(f"/api/v1/executions/{execution_id}/retry", headers=headers)
    assert repeticao.status_code in {202, 409}

    exclusao = client.delete(f"/api/v1/bases/{base_id}", headers=headers)
    assert exclusao.status_code == 204


@pytest.mark.parametrize(
    ("metodo", "rota"),
    [
        ("post", "/api/v1/bases"),
        ("post", "/api/v1/bases/base-exemplo/executions"),
        ("get", "/api/v1/executions/execucao-exemplo"),
        ("post", "/api/v1/executions/execucao-exemplo/retry"),
        ("delete", "/api/v1/bases/base-exemplo"),
        ("post", "/api/v1/bases/base-exemplo/query"),
    ],
)
def test_rejeita_sem_token_valido(metodo: str, rota: str) -> None:
    """SPECSFY: US-003 FR-006 NFR-002 AC-008"""
    from src.app.main import app

    client = TestClient(app)

    sem_token = getattr(client, metodo)(rota)
    assert sem_token.status_code in {401, 403}

    com_token_invalido = getattr(client, metodo)(
        rota, headers={"Authorization": "Bearer token-invalido"}
    )
    assert com_token_invalido.status_code in {401, 403}


def test_isola_por_papel_e_tenant() -> None:
    """SPECSFY: US-003 FR-005 FR-006 FR-007 NFR-002 AC-009"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution

    with SessionLocal() as session:
        base = Base(tenant_id="tenant-1", project_id="projeto-1", nome="base-1", origem="upload")
        session.add(base)
        session.flush()
        execucao = Execution(
            base_id=base.id,
            situacao="succeeded",
            etapa="concluido",
            previstos=1,
            inseridos=1,
            mantidos=0,
            removidos=0,
        )
        session.add(execucao)
        session.commit()
        base_id = base.id
        execution_id = execucao.id

    client = TestClient(app)

    apagar_como_member = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer token-demo-member"},
    )
    assert apagar_como_member.status_code == 403

    acessar_de_outro_tenant = client.get(
        f"/api/v1/executions/{execution_id}",
        headers={"Authorization": "Bearer token-demo-outro-tenant"},
    )
    assert acessar_de_outro_tenant.status_code == 404
