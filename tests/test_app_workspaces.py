"""Testes TDD dos Workspaces da SPEC-0019."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _criar_workspace(client: TestClient, nome: str = "Workspace de teste") -> dict:
    response = client.post(
        "/api/v1/workspaces",
        json={"nome": nome},
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert response.status_code == 201
    return response.json()


def test_owner_cria_workspace() -> None:
    """SPECSFY: SPEC-0019 US-001 FR-001 FR-008 AC-001"""
    from src.app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/workspaces",
        json={"nome": "Banda Larga PF — Vivo — Gold"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 201
    workspace = response.json()
    assert workspace["nome"] == "Banda Larga PF — Vivo — Gold"

    listing = client.get(
        "/api/v1/workspaces",
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert listing.status_code == 200
    assert workspace["id"] in {item["id"] for item in listing.json()}


def test_owner_edita_workspace_sem_trocar_identidade() -> None:
    """SPECSFY: SPEC-0019 US-001 FR-002 FR-008 AC-002"""
    from src.app.main import app

    client = TestClient(app)
    workspace = _criar_workspace(client)
    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}",
        json={"nome": "Vivo — Banda Larga PF"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": workspace["id"],
        "nome": "Vivo — Banda Larga PF",
    }


def test_member_nao_cria_nem_apaga_workspace() -> None:
    """SPECSFY: SPEC-0019 US-001 US-004 FR-001 FR-003 FR-008 AC-003"""
    from src.app.main import app

    client = TestClient(app)
    headers = {"Authorization": "Bearer token-demo-member"}
    create = client.post("/api/v1/workspaces", json={"nome": "Negado"}, headers=headers)
    delete = client.delete("/api/v1/workspaces/workspace-vazio", headers=headers)

    assert create.status_code == 403
    assert delete.status_code == 403


def test_criar_workspace_sem_nome_e_rejeitado() -> None:
    """SPECSFY: SPEC-0019 US-001 FR-001 AC-004"""
    from src.app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/workspaces",
        json={"nome": "   "},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 400


def test_owner_apaga_workspace_vazio() -> None:
    """SPECSFY: SPEC-0019 US-001 FR-003 AC-005"""
    from src.app.main import app

    client = TestClient(app)
    workspace = _criar_workspace(client)
    response = client.delete(
        f"/api/v1/workspaces/{workspace['id']}",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 204
    listing = client.get(
        "/api/v1/workspaces",
        headers={"Authorization": "Bearer token-demo-owner"},
    )
    assert workspace["id"] not in {item["id"] for item in listing.json()}


def test_apagar_workspace_com_bases_e_bloqueado() -> None:
    """SPECSFY: SPEC-0019 US-001 FR-003 NFR-002 AC-006"""
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import Base

    client = TestClient(app)
    workspace = _criar_workspace(client)
    with SessionLocal() as session:
        session.add(
            Base(
                tenant_id="tenant-1",
                project_id="projeto-1",
                workspace_id=workspace["id"],
                nome="base-ativa",
                origem="upload",
                collection_name="base-ativa",
                metadados_chunk=[],
            )
        )
        session.commit()
    response = client.delete(
        f"/api/v1/workspaces/{workspace['id']}",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 409
    assert "base" in response.json()["detail"].lower()


def test_editar_workspace_com_nome_vazio_e_rejeitado() -> None:
    """SPECSFY: SPEC-0019 FR-002 NFR-002 AC-022"""
    from src.app.main import app

    client = TestClient(app)
    workspace = _criar_workspace(client)
    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}",
        json={"nome": ""},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 400


def test_member_nao_edita_workspace() -> None:
    """SPECSFY: SPEC-0019 FR-002 FR-008 NFR-002 AC-023"""
    from src.app.main import app

    client = TestClient(app)
    response = client.patch(
        "/api/v1/workspaces/workspace-existente",
        json={"nome": "Tentativa negada"},
        headers={"Authorization": "Bearer token-demo-member"},
    )

    assert response.status_code == 403


def test_suites_nao_usam_token_estatico() -> None:
    """SPECSFY: SPEC-0020 US-007 FR-010 NFR-003 AC-027"""
    from pathlib import Path

    raiz = Path(__file__).resolve().parent.parent
    # O texto é montado em duas partes para que este arquivo não se encontre.
    procurado = "token-" + "demo"
    ocorrencias: list[str] = []
    for pasta in ("src", "tests", "frontend/src"):
        for caminho in (raiz / pasta).rglob("*"):
            if not caminho.is_file() or caminho.suffix not in {".py", ".ts", ".tsx"}:
                continue
            if "__pycache__" in caminho.parts or "node_modules" in caminho.parts:
                continue
            if procurado in caminho.read_text(encoding="utf-8", errors="ignore"):
                ocorrencias.append(str(caminho.relative_to(raiz)))

    assert ocorrencias == []
