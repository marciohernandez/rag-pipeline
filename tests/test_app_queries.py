"""Testes do endpoint de consulta do backend de aplicação (SPEC-0012)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_consulta_base_indexada() -> None:
    """SPECSFY: US-004 FR-008 AC-010"""
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
                situacao="succeeded",
                etapa="concluido",
                previstos=3,
                inseridos=3,
                mantidos=0,
                removidos=0,
            )
        )
        session.commit()
        base_id = base.id

    client = TestClient(app)
    resposta = client.post(
        f"/api/v1/bases/{base_id}/query",
        json={"pergunta": "Qual o objetivo do projeto?"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert "resultado" in corpo
    assert "chunks_fontes" in corpo


def test_consulta_base_nao_processada() -> None:
    """SPECSFY: US-004 FR-008 NFR-002 AC-011"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-sem-execucao",
            origem="upload",
        )
        session.add(base)
        session.commit()
        base_id = base.id

    client = TestClient(app)
    resposta = client.post(
        f"/api/v1/bases/{base_id}/query",
        json={"pergunta": "Qualquer pergunta"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert resposta.status_code == 409


def test_consulta_com_integracao_indisponivel(monkeypatch) -> None:
    """SPECSFY: US-004 FR-008 NFR-002 AC-012"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution
    from src.pipeline import service

    def _falha(*args: object, **kwargs: object) -> None:
        raise RuntimeError(
            "conexao recusada pelo Qdrant em wss://minha-instancia:6333 com api-key=segredo-fake"
        )

    monkeypatch.setattr(service, "query_base", _falha)

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
                situacao="succeeded",
                etapa="concluido",
                previstos=1,
                inseridos=1,
                mantidos=0,
                removidos=0,
            )
        )
        session.commit()
        base_id = base.id

    client = TestClient(app)
    resposta = client.post(
        f"/api/v1/bases/{base_id}/query",
        json={"pergunta": "teste"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert resposta.status_code == 502
    corpo_texto = resposta.text.lower()
    assert "segredo-fake" not in corpo_texto
    assert "api-key" not in corpo_texto
