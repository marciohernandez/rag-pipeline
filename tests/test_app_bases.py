"""Testes dos endpoints de bases do backend de aplicação (SPEC-0012)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from langchain_core.documents import Document
from sqlalchemy.orm import Session


def _client_com_storage_temporario(tmp_path, monkeypatch) -> TestClient:
    from src.app import storage as storage_module
    from src.app.main import app
    from src.app.storage import LocalDirectoryStorage

    monkeypatch.setattr(
        storage_module,
        "_STORAGE",
        LocalDirectoryStorage(str(tmp_path / "uploads-spec-0019")),
    )
    return TestClient(app)


def _criar_workspace_spec_0019(client: TestClient, nome: str = "Workspace de teste") -> str:
    response = client.post(
        "/api/v1/workspaces",
        json={"nome": nome},
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _arquivo_markdown_spec_0019() -> list[tuple[str, tuple[str, bytes, str]]]:
    return [("arquivos", ("base.md", b"# Base\n\nConteudo de teste.", "text/markdown"))]


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


def test_spec_0019_upload_associa_base_ao_workspace(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 US-002 FR-004 FR-008 AC-007"""
    client = _client_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace_spec_0019(client)

    response = client.post(
        "/api/v1/bases",
        data={"workspace_id": workspace_id},
        files=_arquivo_markdown_spec_0019(),
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 201
    assert response.json()["workspace_id"] == workspace_id
    listing = client.get(
        "/api/v1/bases",
        params={"workspace_id": workspace_id},
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [response.json()["base_id"]]


def test_spec_0019_upload_sem_workspace_e_rejeitado(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 US-002 FR-004 AC-008"""
    client = _client_com_storage_temporario(tmp_path, monkeypatch)

    response = client.post(
        "/api/v1/bases",
        files=_arquivo_markdown_spec_0019(),
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 400
    assert not any((tmp_path / "uploads-spec-0019").rglob("*.md"))


def test_spec_0019_upload_persiste_colecao_customizada(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 US-002 FR-005 AC-009"""
    client = _client_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace_spec_0019(client)

    response = client.post(
        "/api/v1/bases",
        data={"workspace_id": workspace_id, "collection_name": "politicas"},
        files=_arquivo_markdown_spec_0019(),
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 201
    assert response.json()["collection_name"] == "politicas"
    from src.app.db import SessionLocal
    from src.app.models import Base

    with SessionLocal() as session:
        assert session.get(Base, response.json()["base_id"]).collection_name == "politicas"


def test_spec_0019_upload_deriva_colecao_do_workspace(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 US-002 FR-005 AC-010"""
    client = _client_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace_spec_0019(client)

    response = client.post(
        "/api/v1/bases",
        data={"workspace_id": workspace_id},
        files=_arquivo_markdown_spec_0019(),
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 201
    assert response.json()["collection_name"] == f"ws-{workspace_id}"


def test_spec_0019_upload_persiste_metadados_customizados(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 US-003 FR-007 AC-014"""
    client = _client_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace_spec_0019(client)

    response = client.post(
        "/api/v1/bases",
        data={
            "workspace_id": workspace_id,
            "metadados_chunk": '[{"rotulo":"canal","valor":"fibra"}]',
        },
        files=_arquivo_markdown_spec_0019(),
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 201
    assert response.json()["metadados_chunk"] == [{"rotulo": "canal", "valor": "fibra"}]
    from src.app.db import SessionLocal
    from src.app.models import Base

    with SessionLocal() as session:
        assert session.get(Base, response.json()["base_id"]).metadados_chunk == [
            {"rotulo": "canal", "valor": "fibra"}
        ]


def test_spec_0019_upload_sem_metadados_usa_lista_vazia(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 US-003 FR-007 AC-015"""
    client = _client_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace_spec_0019(client)

    response = client.post(
        "/api/v1/bases",
        data={"workspace_id": workspace_id},
        files=_arquivo_markdown_spec_0019(),
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 201
    assert response.json()["metadados_chunk"] == []


def test_spec_0019_upload_rejeita_rotulo_duplicado(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 US-003 FR-007 AC-016"""
    client = _client_com_storage_temporario(tmp_path, monkeypatch)
    workspace_id = _criar_workspace_spec_0019(client)

    response = client.post(
        "/api/v1/bases",
        data={
            "workspace_id": workspace_id,
            "metadados_chunk": (
                '[{"rotulo":"canal","valor":"fibra"},'
                '{"rotulo":"canal","valor":"loja"}]'
            ),
        },
        files=_arquivo_markdown_spec_0019(),
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 400
    assert not any((tmp_path / "uploads-spec-0019").rglob("*.md"))
    from src.app.db import SessionLocal
    from src.app.models import Base

    with SessionLocal() as session:
        assert session.query(Base).filter_by(workspace_id=workspace_id).count() == 0


def test_spec_0019_member_nao_envia_base(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 US-002 US-004 FR-004 FR-008 AC-018"""
    client = _client_com_storage_temporario(tmp_path, monkeypatch)

    response = client.post(
        "/api/v1/bases",
        data={"workspace_id": "workspace-visivel"},
        files=_arquivo_markdown_spec_0019(),
        headers={"Authorization": "Bearer pessoa-teste-member"},
    )

    assert response.status_code == 403
    assert not any((tmp_path / "uploads-spec-0019").rglob("*.md"))


def test_rejeita_envio_fora_dos_limites() -> None:
    """SPECSFY: US-001 FR-003 NFR-001 AC-003"""
    from src.app.main import app

    client = TestClient(app)
    workspace_id = _criar_workspace_spec_0019(client)
    arquivos_demais = [
        ("arquivos", (f"doc{i}.md", b"# titulo\nconteudo", "text/markdown")) for i in range(51)
    ]

    response = client.post(
        "/api/v1/bases",
        data={"workspace_id": workspace_id},
        files=arquivos_demais,
        headers={"Authorization": "Bearer pessoa-teste-owner"},
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
    workspace_id = _criar_workspace_spec_0019(client)
    response = client.post(
        "/api/v1/bases",
        data={"workspace_id": workspace_id},
        files=[
            (
                "arquivos",
                ("../../evil.md", b"# conteudo malicioso", "text/markdown"),
            )
        ],
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 201
    assert not alvo_fora_do_root.exists(), "escreveu fora do diretório da base (path traversal)"


def test_apagar_base_remove_conteudo(vector_store_em_memoria) -> None:
    """SPECSFY: US-002 FR-005 FR-007 NFR-002 NFR-004 AC-006

    SPECSFY: SPEC-0018 US-001 FR-001 AC-001 — regressão do caminho feliz após
    a reordenação de apagar_base (storage e vector store antes do commit).
    """
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution, Query

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
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
        headers={"Authorization": "Bearer pessoa-teste-owner"},
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
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert response.status_code == 204

    assert backend_compartilhado.list_ids(escopo) == set()


def test_apagar_base_falha_no_storage_nao_altera_postgres(monkeypatch) -> None:
    """SPECSFY: SPEC-0018 US-001 FR-001 FR-002 AC-002"""
    from src.app import storage as storage_module
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution, Query

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
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

    def falha_no_storage(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("falha simulada de storage")

    monkeypatch.setattr(storage_module.get_storage(), "delete_base", falha_no_storage)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 500

    with SessionLocal() as session:
        base_ainda_ativa = session.get(Base, base_id)
        assert base_ainda_ativa is not None
        assert base_ainda_ativa.apagada_em is None
        assert session.query(Execution).filter_by(base_id=base_id).count() == 1
        assert session.query(Query).filter_by(base_id=base_id).count() == 1


def test_apagar_base_falha_no_vector_store_nao_altera_postgres(
    vector_store_em_memoria, monkeypatch
) -> None:
    """SPECSFY: SPEC-0018 US-001 FR-001 FR-002 AC-003"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution, Query

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
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

    def falha_no_vector_store(*_args: object, **_kwargs: object) -> int:
        raise RuntimeError("falha simulada de vector store")

    # storage.delete_base roda de verdade (diretório da base não existe em
    # disco neste teste — LocalDirectoryStorage.delete_base é um no-op sobre
    # pasta inexistente); só service.delete_scope é forçado a falhar.
    monkeypatch.setattr("src.pipeline.service.delete_scope", falha_no_vector_store)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 500

    with SessionLocal() as session:
        base_ainda_ativa = session.get(Base, base_id)
        assert base_ainda_ativa is not None
        assert base_ainda_ativa.apagada_em is None
        assert session.query(Execution).filter_by(base_id=base_id).count() == 1
        assert session.query(Query).filter_by(base_id=base_id).count() == 1


def test_apagar_base_repete_apos_falha_no_storage_completa(
    vector_store_em_memoria, monkeypatch
) -> None:
    """SPECSFY: SPEC-0018 US-001 FR-002 FR-003 NFR-001 AC-004"""
    from src.app import storage as storage_module
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution, Query

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
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

    # Falha só na primeira chamada; a partir da segunda, delega ao
    # delete_base real — prova a idempotência real do storage, não uma
    # simulação de sucesso.
    storage_instance = storage_module.get_storage()
    delete_base_original = storage_instance.delete_base
    chamadas = {"n": 0}

    def falha_na_primeira_chamada(base_id_arg: str) -> None:
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            raise RuntimeError("falha simulada de storage")
        delete_base_original(base_id_arg)

    monkeypatch.setattr(storage_instance, "delete_base", falha_na_primeira_chamada)

    client = TestClient(app, raise_server_exceptions=False)

    primeira = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert primeira.status_code == 500
    with SessionLocal() as session:
        assert session.get(Base, base_id).apagada_em is None

    segunda = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert segunda.status_code == 204

    with SessionLocal() as session:
        base_apagada = session.get(Base, base_id)
        assert base_apagada is not None
        assert base_apagada.apagada_em is not None
        assert session.query(Execution).filter_by(base_id=base_id).count() == 0
        assert session.query(Query).filter_by(base_id=base_id).count() == 0


def test_apagar_base_repete_apos_falha_no_vector_store_completa(
    vector_store_em_memoria, monkeypatch
) -> None:
    """SPECSFY: SPEC-0018 US-001 FR-002 FR-003 NFR-001 AC-005"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution, Query
    from src.pipeline import service as pipeline_service

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
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

    # Falha só na primeira vez em que delete_scope é de fato chamado; nas
    # demais, delega ao comportamento real (idempotência real, não mockada).
    delete_scope_original = pipeline_service.delete_scope
    chamadas = {"n": 0}

    def falha_na_primeira_chamada(config: dict, **kwargs: object) -> int:
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            raise RuntimeError("falha simulada de vector store")
        return delete_scope_original(config, **kwargs)

    monkeypatch.setattr(pipeline_service, "delete_scope", falha_na_primeira_chamada)

    client = TestClient(app, raise_server_exceptions=False)

    primeira = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert primeira.status_code == 500
    with SessionLocal() as session:
        assert session.get(Base, base_id).apagada_em is None

    segunda = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert segunda.status_code == 204

    with SessionLocal() as session:
        base_apagada = session.get(Base, base_id)
        assert base_apagada is not None
        assert base_apagada.apagada_em is not None
        assert session.query(Execution).filter_by(base_id=base_id).count() == 0
        assert session.query(Query).filter_by(base_id=base_id).count() == 0


def test_apagar_base_repete_apos_falhas_sucessivas_completa(
    vector_store_em_memoria, monkeypatch
) -> None:
    """SPECSFY: SPEC-0018 US-001 FR-002 FR-003 NFR-001 AC-006"""
    from src.app import storage as storage_module
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution, Query
    from src.pipeline import service as pipeline_service

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
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

    # 1ª chamada: storage falha (delete_scope nunca é alcançado).
    # 2ª chamada: storage sucede de verdade; delete_scope falha na sua
    # primeira invocação real. 3ª chamada: os dois sucedem de verdade.
    storage_instance = storage_module.get_storage()
    delete_base_original = storage_instance.delete_base
    chamadas_storage = {"n": 0}

    def storage_falha_na_primeira_chamada(base_id_arg: str) -> None:
        chamadas_storage["n"] += 1
        if chamadas_storage["n"] == 1:
            raise RuntimeError("falha simulada de storage")
        delete_base_original(base_id_arg)

    monkeypatch.setattr(storage_instance, "delete_base", storage_falha_na_primeira_chamada)

    delete_scope_original = pipeline_service.delete_scope
    chamadas_vector_store = {"n": 0}

    def vector_store_falha_na_primeira_invocacao(config: dict, **kwargs: object) -> int:
        chamadas_vector_store["n"] += 1
        if chamadas_vector_store["n"] == 1:
            raise RuntimeError("falha simulada de vector store")
        return delete_scope_original(config, **kwargs)

    monkeypatch.setattr(
        pipeline_service, "delete_scope", vector_store_falha_na_primeira_invocacao
    )

    client = TestClient(app, raise_server_exceptions=False)

    primeira = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert primeira.status_code == 500
    with SessionLocal() as session:
        assert session.get(Base, base_id).apagada_em is None

    segunda = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert segunda.status_code == 500
    with SessionLocal() as session:
        assert session.get(Base, base_id).apagada_em is None

    terceira = client.delete(
        f"/api/v1/bases/{base_id}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert terceira.status_code == 204

    with SessionLocal() as session:
        base_apagada = session.get(Base, base_id)
        assert base_apagada is not None
        assert base_apagada.apagada_em is not None
        assert session.query(Execution).filter_by(base_id=base_id).count() == 0
        assert session.query(Query).filter_by(base_id=base_id).count() == 0


def test_lista_bases_por_tenant_ordenada() -> None:
    """SPECSFY: US-002 FR-002 NFR-001 AC-004 (SPEC-0013)"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution

    with SessionLocal() as session:
        base_antiga = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
            nome="base-antiga",
            origem="upload",
            documentos=2,
        )
        base_recente = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
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
        headers={"Authorization": "Bearer pessoa-teste-owner"},
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
            **_campos_base_spec_0019(session),
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
        headers={"Authorization": "Bearer pessoa-teste-owner"},
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
            **_campos_base_spec_0019(session),
            nome="base-tenant-1",
            origem="upload",
            documentos=1,
        )
        base_tenant_2 = Base(
            tenant_id="tenant-2",
            project_id="projeto-2",
            **_campos_base_spec_0019(
                session, tenant_id="tenant-2", project_id="projeto-2"
            ),
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
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert resposta_listagem.status_code == 200
    ids_retornados = {item["id"] for item in resposta_listagem.json()}
    assert id_tenant_1 in ids_retornados
    assert id_tenant_2 not in ids_retornados

    resposta_detalhe_cruzado = client.get(
        f"/api/v1/bases/{id_tenant_2}",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert resposta_detalhe_cruzado.status_code == 404


def test_seleciona_base_preparada() -> None:
    """SPECSFY: US-001 FR-003"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base

    client = TestClient(app)
    workspace_id = _criar_workspace_spec_0019(client)
    response = client.post(
        "/api/v1/bases",
        data={"usar_base_preparada": "true", "workspace_id": workspace_id},
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )

    assert response.status_code == 201
    base_id = response.json()["base_id"]

    with SessionLocal() as session:
        base = session.get(Base, base_id)
        assert base is not None
        assert base.origem == "preparada"
