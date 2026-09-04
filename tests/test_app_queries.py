"""Testes do endpoint de consulta do backend de aplicação (SPEC-0012)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from langchain_core.documents import Document


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


def test_consulta_nao_mistura_bases_do_mesmo_projeto(monkeypatch) -> None:
    """SPECSFY: US-004 FR-008 AC-010"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution
    from src.app.tasks import build_pipeline_config
    from src.pipeline import service
    from src.pipeline.providers.vectorstores.in_memory import InMemoryVectorStoreAdapter

    # Mesmo dublê de backend usado em test_apagar_base_remove_pontos_vector_store:
    # persiste entre a indexação de setup e a consulta feita pelo endpoint,
    # sem depender de rede ou de um Qdrant real.
    backend_compartilhado = InMemoryVectorStoreAdapter()
    monkeypatch.setattr(
        "src.pipeline.indexing.build_vector_store",
        lambda *args, **kwargs: backend_compartilhado,
    )

    with SessionLocal() as session:
        base_a = Base(
            tenant_id="tenant-1", project_id="projeto-1", nome="base-a", origem="preparada"
        )
        base_b = Base(
            tenant_id="tenant-1", project_id="projeto-1", nome="base-b", origem="preparada"
        )
        session.add_all([base_a, base_b])
        session.flush()
        session.add_all(
            [
                Execution(
                    base_id=base_a.id,
                    situacao="succeeded",
                    etapa="concluido",
                    previstos=1,
                    inseridos=1,
                    mantidos=0,
                    removidos=0,
                ),
                Execution(
                    base_id=base_b.id,
                    situacao="succeeded",
                    etapa="concluido",
                    previstos=1,
                    inseridos=1,
                    mantidos=0,
                    removidos=0,
                ),
            ]
        )
        session.commit()
        base_a_id = base_a.id

    config = build_pipeline_config(
        base_project_id="projeto-1",
        embedding={"provider": "fake", "dimensions": 16},
        vector_store={"provider": "qdrant", "collection_name": "app-test"},
        input_dir=".",
    )
    chunk_a = Document(
        page_content="Conteudo exclusivo da base A: plano essencial 100 Mbps.",
        metadata={"project_id": "projeto-1", "tenant_id": "tenant-1", "chunk_id": "chunk-a"},
    )
    chunk_b = Document(
        page_content="Conteudo exclusivo da base B: instalacao em ate 5 dias uteis.",
        metadata={"project_id": "projeto-1", "tenant_id": "tenant-1", "chunk_id": "chunk-b"},
    )
    service.sync_vector_store(config, [chunk_a])
    service.sync_vector_store(config, [chunk_b])

    client = TestClient(app)
    resposta = client.post(
        f"/api/v1/bases/{base_a_id}/query",
        json={"pergunta": "O que a base A oferece?"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert resposta.status_code == 200
    trechos = " ".join(item["trecho"] for item in resposta.json()["chunks_fontes"])
    assert "base B" not in trechos
