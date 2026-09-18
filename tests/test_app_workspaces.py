"""Testes TDD dos Workspaces da SPEC-0019."""

from __future__ import annotations

from fastapi.testclient import TestClient


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
    response = client.patch(
        "/api/v1/workspaces/workspace-existente",
        json={"nome": "Vivo — Banda Larga PF"},
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "workspace-existente",
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
    response = client.delete(
        "/api/v1/workspaces/workspace-vazio",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 204


def test_apagar_workspace_com_bases_e_bloqueado() -> None:
    """SPECSFY: SPEC-0019 US-001 FR-003 NFR-002 AC-006"""
    from src.app.main import app

    client = TestClient(app)
    response = client.delete(
        "/api/v1/workspaces/workspace-com-bases",
        headers={"Authorization": "Bearer token-demo-owner"},
    )

    assert response.status_code == 409
    assert "base" in response.json()["detail"].lower()


def test_editar_workspace_com_nome_vazio_e_rejeitado() -> None:
    """SPECSFY: SPEC-0019 FR-002 NFR-002 AC-022"""
    from src.app.main import app

    client = TestClient(app)
    response = client.patch(
        "/api/v1/workspaces/workspace-existente",
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
