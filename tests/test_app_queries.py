"""Testes do endpoint de consulta do backend de aplicação (SPEC-0012)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from langchain_core.documents import Document
from sqlalchemy.orm import Session

from src.pipeline.providers.contracts import SearchResult


def _campos_base_spec_0019(
    session: Session,
    *,
    tenant_id: str = "tenant-1",
    project_id: str = "projeto-1",
) -> dict[str, object]:
    from src.app.models import Workspace

    workspace = Workspace(
        tenant_id=tenant_id,
        project_id=project_id,
        nome="Workspace de fixture",
    )
    session.add(workspace)
    session.flush()
    return {
        "workspace_id": workspace.id,
        "collection_name": f"ws-{workspace.id}",
        "metadados_chunk": [],
    }


def _criar_base_spec_0019(
    client: TestClient,
    *,
    workspace_id: str,
    collection_name: str,
    nome: str,
) -> str:
    response = client.post(
        "/api/v1/bases",
        data={"workspace_id": workspace_id, "collection_name": collection_name},
        files=[("arquivos", (f"{nome}.md", f"# {nome}\n\nConteudo.".encode(), "text/markdown"))],
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert response.status_code == 201
    return response.json()["base_id"]


def _marcar_base_processada_spec_0019(base_id: str) -> None:
    from src.app.db import SessionLocal
    from src.app.models import Execution

    with SessionLocal() as session:
        session.add(
            Execution(
                base_id=base_id,
                situacao="succeeded",
                etapa="concluido",
                previstos=1,
                inseridos=1,
                mantidos=0,
                removidos=0,
            )
        )
        session.commit()


def test_spec_0019_consulta_usa_colecao_da_base(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 US-002 FR-006 NFR-003 AC-012"""
    from src.app import storage as storage_module
    from src.app.main import app
    from src.app.storage import LocalDirectoryStorage
    from src.pipeline import service

    monkeypatch.setattr(
        storage_module,
        "_STORAGE",
        LocalDirectoryStorage(str(tmp_path / "uploads-spec-0019")),
    )
    configuracoes: list[dict] = []

    def consultar(config: dict, _pergunta: str):
        configuracoes.append(config)
        colecao = config["vector_store"]["collection_name"]
        return [
            SearchResult(
                content=f"resultado-{colecao}", metadata={"document_id": colecao}, score=1.0
            )
        ]

    monkeypatch.setattr(service, "query_base", consultar)
    client = TestClient(app)
    workspace = client.post(
        "/api/v1/workspaces",
        json={"nome": "Coleções"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert workspace.status_code == 201
    workspace_id = workspace.json()["id"]
    _criar_base_spec_0019(
        client, workspace_id=workspace_id, collection_name="produtos", nome="produtos"
    )
    politicas_id = _criar_base_spec_0019(
        client, workspace_id=workspace_id, collection_name="politicas", nome="politicas"
    )
    _marcar_base_processada_spec_0019(politicas_id)

    response = client.post(
        f"/api/v1/bases/{politicas_id}/query",
        json={"pergunta": "Qual política se aplica?"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 200
    assert configuracoes[-1]["vector_store"]["collection_name"] == "politicas"
    assert response.json()["resultado"] == "resultado-politicas"


def test_spec_0019_colecao_repetida_preserva_escopo_logico(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 FR-005 FR-006 NFR-003 AC-013"""
    from src.app import storage as storage_module
    from src.app.main import app
    from src.app.storage import LocalDirectoryStorage
    from src.pipeline import service

    monkeypatch.setattr(
        storage_module,
        "_STORAGE",
        LocalDirectoryStorage(str(tmp_path / "uploads-spec-0019")),
    )
    escopos: list[str] = []

    def consultar(config: dict, _pergunta: str):
        escopos.append(config["projeto"]["nome"])
        return [SearchResult(content=config["projeto"]["nome"], metadata={}, score=1.0)]

    monkeypatch.setattr(service, "query_base", consultar)
    client = TestClient(app)
    workspace_ids = []
    for nome in ("A", "B"):
        response = client.post(
            "/api/v1/workspaces",
            json={"nome": nome},
            headers={"Authorization": "Bearer token-demo-owner"},
        )
        assert response.status_code == 201
        workspace_ids.append(response.json()["id"])

    base_ids = [
        _criar_base_spec_0019(
            client, workspace_id=workspace_id, collection_name="geral", nome=f"base-{indice}"
        )
        for indice, workspace_id in enumerate(workspace_ids)
    ]
    for base_id in base_ids:
        _marcar_base_processada_spec_0019(base_id)
        response = client.post(
            f"/api/v1/bases/{base_id}/query",
            json={"pergunta": "Consulta"},
            headers={"Authorization": "Bearer token-demo-owner"},
        )
        assert response.status_code == 200

    assert len(set(escopos)) == 2
    assert all("tenant-1::projeto-1::" in escopo for escopo in escopos)


def test_consulta_base_indexada(vector_store_em_memoria) -> None:
    """SPECSFY: US-004 FR-008 AC-010"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
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
            **_campos_base_spec_0019(session),
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
            **_campos_base_spec_0019(session),
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


def test_consulta_isola_por_tenant() -> None:
    """SPECSFY: US-004 FR-008 NFR-001 AC-015 (SPEC-0013)"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution

    with SessionLocal() as session:
        base_tenant_2 = Base(
            tenant_id="tenant-2",
            project_id="projeto-2",
            **_campos_base_spec_0019(
                session, tenant_id="tenant-2", project_id="projeto-2"
            ),
            nome="base-tenant-2",
            origem="preparada",
        )
        session.add(base_tenant_2)
        session.flush()
        session.add(
            Execution(
                base_id=base_tenant_2.id,
                situacao="succeeded",
                etapa="concluido",
                previstos=1,
                inseridos=1,
                mantidos=0,
                removidos=0,
            )
        )
        session.commit()
        base_id = base_tenant_2.id

    client = TestClient(app)
    resposta = client.post(
        f"/api/v1/bases/{base_id}/query",
        json={"pergunta": "pergunta de outro tenant"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert resposta.status_code == 404


def test_consulta_nao_mistura_bases_do_mesmo_projeto(monkeypatch) -> None:
    """SPECSFY: US-004 FR-008 AC-010"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution
    from src.app.tasks import build_pipeline_config, scope_project_id
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
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
            nome="base-a",
            origem="preparada",
        )
        base_b = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
            nome="base-b",
            origem="preparada",
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
        base_b_id = base_b.id

    # Cada base indexada no seu próprio escopo composto (o mesmo que
    # process_base_task/consultar_base usam de verdade), sem "tenant_id" no
    # metadata do chunk — o pipeline real (src/pipeline/identity.py) nunca
    # grava esse campo, só "project_id".
    escopo_a = scope_project_id("tenant-1", "projeto-1", base_a_id)
    escopo_b = scope_project_id("tenant-1", "projeto-1", base_b_id)
    config_a = build_pipeline_config(
        base_project_id=escopo_a,
        embedding={"provider": "fake", "dimensions": 16},
        vector_store={"provider": "qdrant", "collection_name": "app-test"},
        input_dir=".",
    )
    config_b = build_pipeline_config(
        base_project_id=escopo_b,
        embedding={"provider": "fake", "dimensions": 16},
        vector_store={"provider": "qdrant", "collection_name": "app-test"},
        input_dir=".",
    )
    chunk_a = Document(
        page_content="Conteudo exclusivo da base A: plano essencial 100 Mbps.",
        metadata={"project_id": escopo_a, "chunk_id": "chunk-a"},
    )
    chunk_b = Document(
        page_content="Conteudo exclusivo da base B: instalacao em ate 5 dias uteis.",
        metadata={"project_id": escopo_b, "chunk_id": "chunk-b"},
    )
    service.sync_vector_store(config_a, [chunk_a])
    service.sync_vector_store(config_b, [chunk_b])

    client = TestClient(app)
    resposta = client.post(
        f"/api/v1/bases/{base_a_id}/query",
        json={"pergunta": "O que a base A oferece?"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert resposta.status_code == 200
    trechos = " ".join(item["trecho"] for item in resposta.json()["chunks_fontes"])
    assert "base B" not in trechos
