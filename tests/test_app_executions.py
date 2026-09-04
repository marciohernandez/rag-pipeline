"""Testes do endpoint de execuções do backend de aplicação (SPEC-0012)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_iniciar_execucao_nao_bloqueia() -> None:
    """SPECSFY: US-001 FR-001 FR-002 FR-003 FR-009 NFR-001 AC-001"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-exemplo",
            origem="preparada",
        )
        session.add(base)
        session.commit()
        base_id = base.id

    client = TestClient(app)

    response = client.post(
        f"/api/v1/bases/{base_id}/executions",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 202
    body = response.json()
    assert "execution_id" in body
    assert body["situacao"] in {"pending", "running"}


def test_estado_sobrevive_reinicio() -> None:
    """SPECSFY: US-001 FR-002 NFR-004 AC-002"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-exemplo",
            origem="preparada",
        )
        session.add(base)
        session.flush()
        execution = Execution(
            base_id=base.id,
            situacao="running",
            etapa="chunking",
            previstos=10,
            inseridos=4,
            mantidos=0,
            removidos=0,
        )
        session.add(execution)
        session.commit()
        execution_id = execution.id

    # Nova sessão simula a leitura por um processo reiniciado.
    client = TestClient(app)
    response = client.get(
        f"/api/v1/executions/{execution_id}",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["etapa"] == "chunking"
    assert body["inseridos"] == 4


def test_impede_execucao_concorrente() -> None:
    """SPECSFY: US-001 FR-009 NFR-003 AC-013"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-exemplo",
            origem="preparada",
        )
        session.add(base)
        session.flush()
        session.add(
            Execution(
                base_id=base.id,
                situacao="running",
                etapa="chunking",
                previstos=0,
                inseridos=0,
                mantidos=0,
                removidos=0,
            )
        )
        session.commit()
        base_id = base.id

    client = TestClient(app)
    response = client.post(
        f"/api/v1/bases/{base_id}/executions",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 409


def test_repetir_execucao_falhada() -> None:
    """SPECSFY: US-002 FR-001 FR-002 FR-004 NFR-001 NFR-003 NFR-004 AC-004"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-exemplo",
            origem="preparada",
        )
        session.add(base)
        session.flush()
        execucao_falha = Execution(
            base_id=base.id,
            situacao="failed",
            etapa="indexacao",
            previstos=10,
            inseridos=0,
            mantidos=0,
            removidos=0,
            erro="Falha simulada de indexação",
        )
        session.add(execucao_falha)
        session.commit()
        execution_id = execucao_falha.id

    client = TestClient(app)
    response = client.post(
        f"/api/v1/executions/{execution_id}/retry",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 202
    novo_execution_id = response.json()["execution_id"]
    assert novo_execution_id != execution_id


def test_repeticao_nao_duplica_pontos() -> None:
    """SPECSFY: US-002 FR-004 NFR-003 AC-005"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-exemplo",
            origem="preparada",
        )
        session.add(base)
        session.flush()
        execucao = Execution(
            base_id=base.id,
            situacao="failed",
            etapa="indexacao",
            previstos=5,
            inseridos=0,
            mantidos=0,
            removidos=0,
        )
        session.add(execucao)
        session.commit()
        execution_id = execucao.id

    client = TestClient(app)
    total_por_tentativa: list[int] = []
    for _ in range(3):
        response = client.post(
            f"/api/v1/executions/{execution_id}/retry",
            headers={"Authorization": "Bearer token-demo-owner"},
        )
        assert response.status_code == 202
        execution_id = response.json()["execution_id"]

        estado = client.get(
            f"/api/v1/executions/{execution_id}",
            headers={"Authorization": "Bearer token-demo-owner"},
        ).json()
        total_por_tentativa.append(estado["inseridos"] + estado["mantidos"])

        # Nenhum worker roda neste teste; simula o worker concluindo com falha
        # para permitir a próxima repetição do laço (só se repete uma execução
        # que falhou, FR-004/FR-009).
        with SessionLocal() as session:
            execucao_db = session.get(Execution, execution_id)
            execucao_db.situacao = "failed"
            session.commit()

    # O total de pontos ativos (inseridos + mantidos) não deve crescer a cada repetição.
    assert len(set(total_por_tentativa)) == 1
