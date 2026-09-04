"""Testes dos endpoints de bases do backend de aplicação (SPEC-0012)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_rejeita_envio_fora_dos_limites() -> None:
    """SPECSFY: US-001 FR-003 NFR-001 AC-003"""
    from src.app.main import app

    client = TestClient(app)
    arquivos_demais = [
        ("arquivos", (f"doc{i}.md", b"# titulo\nconteudo", "text/markdown")) for i in range(51)
    ]

    response = client.post(
        "/api/v1/bases",
        files=arquivos_demais,
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 400
    assert "limite" in response.json()["detail"].lower()


def test_apagar_base_remove_conteudo() -> None:
    """SPECSFY: US-002 FR-005 FR-007 NFR-002 NFR-004 AC-006"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution, Query

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-exemplo",
            origem="upload",
        )
        session.add(base)
        session.flush()
        session.add(
            Execution(
                base_id=base.id,
                situacao="succeeded",
                etapa="concluido",
                previstos=5,
                inseridos=5,
                mantidos=0,
                removidos=0,
            )
        )
        session.add(
            Query(
                base_id=base.id,
                tenant_id="tenant-1",
                project_id="projeto-1",
                pergunta="pergunta de teste",
                resultado="resposta de teste",
                chunks_fontes=[],
            )
        )
        session.commit()
        base_id = base.id

    client = TestClient(app)
    response = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 204

    with SessionLocal() as session:
        base_apagada = session.get(Base, base_id)
        assert base_apagada is not None
        assert base_apagada.apagada_em is not None
        assert session.query(Execution).filter_by(base_id=base_id).count() == 0
        assert session.query(Query).filter_by(base_id=base_id).count() == 0
