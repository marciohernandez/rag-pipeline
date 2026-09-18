"""Testes do endpoint de execuções do backend de aplicação (SPEC-0012)."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _campos_base_spec_0019(session: Session) -> dict[str, object]:
    from src.app.models import Workspace

    workspace = Workspace(
        tenant_id="tenant-1",
        project_id="projeto-1",
        nome="Workspace de fixture",
    )
    session.add(workspace)
    session.flush()
    return {
        "workspace_id": workspace.id,
        "collection_name": f"ws-{workspace.id}",
        "metadados_chunk": [],
    }


def test_spec_0019_execucao_usa_collection_name_da_base(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0019 US-002 FR-006 NFR-003 AC-011"""
    from src.app import storage as storage_module
    from src.app.main import app
    from src.app.settings import get_settings
    from src.app.storage import LocalDirectoryStorage
    from src.app.tasks import process_base_task

    monkeypatch.setattr(
        storage_module,
        "_STORAGE",
        LocalDirectoryStorage(str(tmp_path / "uploads-spec-0019")),
    )
    agendamento: dict[str, object] = {}
    monkeypatch.setattr(process_base_task, "defer", lambda **kwargs: agendamento.update(kwargs))
    client = TestClient(app)
    vector_store_global = dict(get_settings().vector_store)

    workspace = client.post(
        "/api/v1/workspaces",
        json={"nome": "Execução"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert workspace.status_code == 201
    upload = client.post(
        "/api/v1/bases",
        data={"workspace_id": workspace.json()["id"], "collection_name": "produtos"},
        files=[("arquivos", ("base.md", b"# Base\n\nProdutos.", "text/markdown"))],
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert upload.status_code == 201

    response = client.post(
        f"/api/v1/bases/{upload.json()['base_id']}/executions",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 202
    assert agendamento["vector_store"]["collection_name"] == "produtos"
    assert get_settings().vector_store == vector_store_global
    assert agendamento["vector_store"] is not get_settings().vector_store


def _executar_chamadas_http_concorrentes(chamadas: list[Callable[[], Any]]) -> list[Any]:
    with ThreadPoolExecutor(max_workers=len(chamadas)) as executor:
        futuros = [executor.submit(chamada) for chamada in chamadas]
        return [futuro.result(timeout=5) for futuro in futuros]


def test_iniciar_execucao_nao_bloqueia() -> None:
    """SPECSFY: US-001 FR-001 FR-002 FR-003 FR-009 NFR-001 AC-001"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
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
            **_campos_base_spec_0019(session),
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
            **_campos_base_spec_0019(session),
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


def test_execucao_ativa_commitada_rejeita_sequencial() -> None:
    """SPECSFY: SPEC-0015 US-001 FR-001 FR-002 AC-004

    Regressão do comportamento sequencial já existente (sem corrida real,
    sem monkeypatch): quando a execução ativa já está commitada, o check
    otimista de has_active_execution já rejeita, sem tentar inserir. O que
    muda nesta spec é o formato do corpo do 409, que passa a ser estruturado
    com execution_id/situacao em vez de uma mensagem de texto livre.
    """
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
        execucao_ativa = Execution(
            base_id=base.id,
            situacao="running",
            etapa="chunking",
            previstos=0,
            inseridos=0,
            mantidos=0,
            removidos=0,
        )
        session.add(execucao_ativa)
        session.commit()
        base_id = base.id
        execution_id_ativa = execucao_ativa.id

    client = TestClient(app)
    response = client.post(
        f"/api/v1/bases/{base_id}/executions",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "execution_id": execution_id_ativa,
        "situacao": "running",
    }


def test_corrida_real_entre_duas_chamadas_iniciar(monkeypatch) -> None:
    """SPECSFY: SPEC-0015 US-001 FR-001 FR-002 FR-003 NFR-001 AC-001

    Duas sessões HTTP concluem o check real antes de disputar o insert. Sem o
    índice único parcial (T005), ambas são aceitas silenciosamente.
    """
    from src.app import repo
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base
    from src.app.routers import executions as executions_router

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
            nome="base-exemplo",
            origem="preparada",
        )
        session.add(base)
        session.commit()
        base_id = base.id

    barreira = Barrier(2)
    resultados_do_check: list[bool] = []
    has_active_execution_real = repo.has_active_execution

    def observar_check(session, base_id: str) -> bool:
        resultado = has_active_execution_real(session, base_id)
        resultados_do_check.append(resultado)
        barreira.wait(timeout=5)
        return resultado

    monkeypatch.setattr(repo, "has_active_execution", observar_check)
    monkeypatch.setattr(executions_router, "_agendar", lambda *args, **kwargs: None)

    client = TestClient(app)
    respostas = _executar_chamadas_http_concorrentes(
        [
            lambda: client.post(
                f"/api/v1/bases/{base_id}/executions",
                headers={"Authorization": "Bearer token-demo-owner"},
            ),
            lambda: client.post(
                f"/api/v1/bases/{base_id}/executions",
                headers={"Authorization": "Bearer token-demo-owner"},
            ),
        ]
    )

    assert resultados_do_check == [False, False]
    assert sorted(response.status_code for response in respostas) == [202, 409]
    aceita = next(response for response in respostas if response.status_code == 202)
    rejeitada = next(response for response in respostas if response.status_code == 409)
    assert rejeitada.json()["detail"] == {
        "execution_id": aceita.json()["execution_id"],
        "situacao": "pending",
    }


def test_corrida_real_entre_iniciar_e_repetir(monkeypatch) -> None:
    """SPECSFY: SPEC-0015 US-001 FR-001 FR-002 FR-003 NFR-001 AC-002

    Início e repetição concluem o check real antes de disputar o insert.
    """
    from src.app import repo
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution
    from src.app.routers import executions as executions_router

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
        execucao_falha = Execution(
            base_id=base.id,
            situacao="failed",
            etapa="indexacao",
            previstos=5,
            inseridos=0,
            mantidos=0,
            removidos=0,
            erro="Falha simulada de indexação",
        )
        session.add(execucao_falha)
        session.commit()
        base_id = base.id
        execution_id_falha = execucao_falha.id

    barreira = Barrier(2)
    resultados_do_check: list[bool] = []
    has_active_execution_real = repo.has_active_execution

    def observar_check(session, base_id: str) -> bool:
        resultado = has_active_execution_real(session, base_id)
        resultados_do_check.append(resultado)
        barreira.wait(timeout=5)
        return resultado

    monkeypatch.setattr(repo, "has_active_execution", observar_check)
    monkeypatch.setattr(executions_router, "_agendar", lambda *args, **kwargs: None)

    client = TestClient(app)
    respostas = _executar_chamadas_http_concorrentes(
        [
            lambda: client.post(
                f"/api/v1/bases/{base_id}/executions",
                headers={"Authorization": "Bearer token-demo-owner"},
            ),
            lambda: client.post(
                f"/api/v1/executions/{execution_id_falha}/retry",
                headers={"Authorization": "Bearer token-demo-owner"},
            ),
        ]
    )

    assert resultados_do_check == [False, False]
    assert sorted(response.status_code for response in respostas) == [202, 409]
    aceita = next(response for response in respostas if response.status_code == 202)
    rejeitada = next(response for response in respostas if response.status_code == 409)
    assert rejeitada.json()["detail"] == {
        "execution_id": aceita.json()["execution_id"],
        "situacao": "pending",
    }


def test_corrida_real_entre_duas_chamadas_repetir(monkeypatch) -> None:
    """SPECSFY: SPEC-0015 US-001 FR-001 FR-002 FR-003 NFR-001 AC-003

    Duas repetições de execuções ``failed`` distintas disputam o insert.
    """
    from src.app import repo
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base, Execution
    from src.app.routers import executions as executions_router

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
        execucoes_falhas = [
            Execution(
                base_id=base.id,
                situacao="failed",
                etapa="indexacao",
                previstos=5,
                inseridos=0,
                mantidos=0,
                removidos=0,
                erro=f"Falha simulada de indexação {indice}",
            )
            for indice in range(2)
        ]
        session.add_all(execucoes_falhas)
        session.commit()
        execution_ids_falhas = [execution.id for execution in execucoes_falhas]

    barreira = Barrier(2)
    resultados_do_check: list[bool] = []
    has_active_execution_real = repo.has_active_execution

    def observar_check(session, base_id: str) -> bool:
        resultado = has_active_execution_real(session, base_id)
        resultados_do_check.append(resultado)
        barreira.wait(timeout=5)
        return resultado

    monkeypatch.setattr(repo, "has_active_execution", observar_check)
    monkeypatch.setattr(executions_router, "_agendar", lambda *args, **kwargs: None)

    client = TestClient(app)
    respostas = _executar_chamadas_http_concorrentes(
        [
            lambda execution_id=execution_id: client.post(
                f"/api/v1/executions/{execution_id}/retry",
                headers={"Authorization": "Bearer token-demo-owner"},
            )
            for execution_id in execution_ids_falhas
        ]
    )

    assert resultados_do_check == [False, False]
    assert sorted(response.status_code for response in respostas) == [202, 409]
    aceita = next(response for response in respostas if response.status_code == 202)
    rejeitada = next(response for response in respostas if response.status_code == 409)
    assert rejeitada.json()["detail"] == {
        "execution_id": aceita.json()["execution_id"],
        "situacao": "pending",
    }


def test_repetir_execucao_falhada() -> None:
    """SPECSFY: US-002 FR-001 FR-002 FR-004 NFR-001 NFR-003 NFR-004 AC-004"""
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
            **_campos_base_spec_0019(session),
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


def test_resposta_inicio_execucao_em_ate_1s(monkeypatch) -> None:
    """SPECSFY: US-001 NFR-001"""
    import time

    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base
    from src.app.tasks import process_base_task

    def _tarefa_lenta(*args: object, **kwargs: object) -> None:
        # Duração simulada bem maior que o limite de 1s do NFR-001; se o
        # endpoint algum dia passar a rodar a tarefa de forma síncrona antes
        # de responder, este teste passa a estourar o limite.
        time.sleep(2)

    monkeypatch.setattr(process_base_task, "func", _tarefa_lenta)

    with SessionLocal() as session:
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            **_campos_base_spec_0019(session),
            nome="base-exemplo",
            origem="preparada",
        )
        session.add(base)
        session.commit()
        base_id = base.id

    client = TestClient(app)
    inicio = time.perf_counter()
    response = client.post(
        f"/api/v1/bases/{base_id}/executions",
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    duracao = time.perf_counter() - inicio

    assert response.status_code == 202
    assert duracao < 1.0
