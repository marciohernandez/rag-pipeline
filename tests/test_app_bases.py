"""Testes dos endpoints de bases do backend de aplicação (SPEC-0012)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from langchain_core.documents import Document


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


def test_apagar_base_remove_pontos_vector_store(monkeypatch) -> None:
    """SPECSFY: US-002 FR-005 AC-006"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution
    from src.app.tasks import build_pipeline_config, scope_project_id
    from src.pipeline import service
    from src.pipeline.providers.vectorstores.in_memory import InMemoryVectorStoreAdapter

    # O config declara provider "qdrant" (único aceito por
    # SyncSafetyPolicy); o adapter real é substituído por um backend
    # em memória fixo, para que a indexação de setup e a remoção feita
    # pelo DELETE enxerguem o mesmo estado dentro deste teste — equivalente
    # a um Qdrant real permanecer no ar entre as duas chamadas, sem rede.
    backend_compartilhado = InMemoryVectorStoreAdapter()
    monkeypatch.setattr(
        "src.pipeline.indexing.build_vector_store",
        lambda *args, **kwargs: backend_compartilhado,
    )

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

    escopo_da_base = scope_project_id("projeto-1", base_id)
    config = build_pipeline_config(
        base_project_id=escopo_da_base,
        embedding={"provider": "fake", "dimensions": 16},
        vector_store={"provider": "qdrant", "collection_name": "app-test"},
        input_dir=".",
    )
    chunk = Document(
        page_content="Plano Turbo: 500 Mbps para uso simultâneo intenso.",
        metadata={"project_id": escopo_da_base, "tenant_id": "tenant-1", "chunk_id": "chunk-1"},
    )
    service.sync_vector_store(config, [chunk])

    from src.pipeline.providers.contracts import LogicalScope

    escopo = LogicalScope(project_id=escopo_da_base, tenant_id="tenant-1")
    assert backend_compartilhado.list_ids(escopo) == {"chunk-1"}

    client = TestClient(app)
    response = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert response.status_code == 204

    assert backend_compartilhado.list_ids(escopo) == set()


def test_seleciona_base_preparada() -> None:
    """SPECSFY: US-001 FR-003"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base

    client = TestClient(app)
    response = client.post(
        "/api/v1/bases",
        data={"usar_base_preparada": "true"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 201
    base_id = response.json()["base_id"]

    with SessionLocal() as session:
        base = session.get(Base, base_id)
        assert base is not None
        assert base.origem == "preparada"
