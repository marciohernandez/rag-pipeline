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


def test_rejeita_nome_de_arquivo_com_travessia_de_diretorio(tmp_path, monkeypatch) -> None:
    """SPECSFY: US-001 FR-003"""
    from src.app import storage as storage_module
    from src.app.main import app
    from src.app.storage import LocalDirectoryStorage

    # Aponta o storage local para um diretório descartável desta execução,
    # para provar que nada é escrito fora dele mesmo que o filename tente;
    # monkeypatch restaura o storage original ao fim do teste.
    root = tmp_path / "uploads"
    monkeypatch.setattr(storage_module, "_STORAGE", LocalDirectoryStorage(str(root)))
    alvo_fora_do_root = tmp_path / "evil.md"

    client = TestClient(app)
    response = client.post(
        "/api/v1/bases",
        files=[
            (
                "arquivos",
                ("../../evil.md", b"# conteudo malicioso", "text/markdown"),
            )
        ],
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 201
    assert not alvo_fora_do_root.exists(), "escreveu fora do diretório da base (path traversal)"


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

    escopo_da_base = scope_project_id("tenant-1", "projeto-1", base_id)
    config = build_pipeline_config(
        base_project_id=escopo_da_base,
        embedding={"provider": "fake", "dimensions": 16},
        vector_store={"provider": "qdrant", "collection_name": "app-test"},
        input_dir=".",
    )
    # Sem "tenant_id" no metadata: o pipeline real (src/pipeline/identity.py)
    # nunca grava esse campo no chunk, só "project_id" — reproduzir isso é o
    # que expôs o descompasso de escopo entre escrita e leitura/exclusão.
    chunk = Document(
        page_content="Plano Turbo: 500 Mbps para uso simultâneo intenso.",
        metadata={"project_id": escopo_da_base, "chunk_id": "chunk-1"},
    )
    service.sync_vector_store(config, [chunk])

    from src.pipeline.providers.contracts import LogicalScope

    escopo = LogicalScope(project_id=escopo_da_base, tenant_id=None)
    assert backend_compartilhado.list_ids(escopo) == {"chunk-1"}

    client = TestClient(app)
    response = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert response.status_code == 204

    assert backend_compartilhado.list_ids(escopo) == set()


def test_lista_bases_por_tenant_ordenada() -> None:
    """SPECSFY: US-002 FR-002 NFR-001 AC-004 (SPEC-0013)"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution

    with SessionLocal() as session:
        base_antiga = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-antiga",
            origem="upload",
            documentos=2,
        )
        base_recente = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-recente",
            origem="preparada",
            documentos=1,
        )
        session.add_all([base_antiga, base_recente])
        session.flush()
        session.add(
            Execution(
                base_id=base_antiga.id,
                situacao="succeeded",
                etapa="concluido",
                previstos=3,
                inseridos=3,
                mantidos=0,
                removidos=0,
            )
        )
        session.add(
            Execution(
                base_id=base_recente.id,
                situacao="running",
                etapa="indexando",
                previstos=1,
                inseridos=0,
                mantidos=0,
                removidos=0,
            )
        )
        session.commit()
        id_antiga, id_recente = base_antiga.id, base_recente.id

    client = TestClient(app)
    response = client.get(
        "/api/v1/bases",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 200
    bases = response.json()
    ids_retornados = [item["id"] for item in bases]
    assert id_recente in ids_retornados
    assert id_antiga in ids_retornados
    assert ids_retornados.index(id_recente) < ids_retornados.index(id_antiga)

    item_recente = next(item for item in bases if item["id"] == id_recente)
    assert item_recente["origem"] == "preparada"
    assert item_recente["status"] == "running"
    assert item_recente["documentos"] == 1
    assert item_recente["chunks"] == 0


def test_detalhe_base_com_historico_execucoes() -> None:
    """SPECSFY: US-002 FR-003 AC-005 (SPEC-0013)"""
    from datetime import UTC, datetime, timedelta

    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution

    agora = datetime.now(UTC)

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-com-historico",
            origem="upload",
            documentos=1,
        )
        session.add(base)
        session.flush()
        execucao_antiga = Execution(
            base_id=base.id,
            situacao="failed",
            etapa="embeddings",
            previstos=1,
            inseridos=0,
            mantidos=0,
            removidos=0,
            erro="provider indisponível",
            iniciado_em=agora - timedelta(hours=1),
        )
        execucao_recente = Execution(
            base_id=base.id,
            situacao="succeeded",
            etapa="concluido",
            previstos=1,
            inseridos=1,
            mantidos=0,
            removidos=0,
            iniciado_em=agora,
        )
        session.add_all([execucao_antiga, execucao_recente])
        session.commit()
        base_id = base.id
        id_execucao_recente = execucao_recente.id
        id_execucao_antiga = execucao_antiga.id

    client = TestClient(app)
    response = client.get(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["id"] == base_id
    ids_execucoes = [execucao["id"] for execucao in corpo["execucoes"]]
    assert ids_execucoes == [id_execucao_recente, id_execucao_antiga]


def test_listagem_e_detalhe_isolam_por_tenant() -> None:
    """SPECSFY: US-002 FR-002 FR-003 NFR-001 AC-014 (SPEC-0013)"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base

    with SessionLocal() as session:
        base_tenant_1 = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="base-tenant-1",
            origem="upload",
            documentos=1,
        )
        base_tenant_2 = Base(
            tenant_id="tenant-2",
            project_id="projeto-2",
            nome="base-tenant-2",
            origem="upload",
            documentos=1,
        )
        session.add_all([base_tenant_1, base_tenant_2])
        session.commit()
        id_tenant_1, id_tenant_2 = base_tenant_1.id, base_tenant_2.id

    client = TestClient(app)

    resposta_listagem = client.get(
        "/api/v1/bases",
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert resposta_listagem.status_code == 200
    ids_retornados = {item["id"] for item in resposta_listagem.json()}
    assert id_tenant_1 in ids_retornados
    assert id_tenant_2 not in ids_retornados

    resposta_detalhe_cruzado = client.get(
        f"/api/v1/bases/{id_tenant_2}",
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert resposta_detalhe_cruzado.status_code == 404


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
