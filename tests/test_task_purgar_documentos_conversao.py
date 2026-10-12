"""Testes da retenção dos documentos convertidos (SPEC-0023)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

AUTH_OWNER = {"Authorization": "Bearer pessoa-teste-owner"}


def _preparar_documento_expirado(tmp_path, monkeypatch):
    from src.app import storage as storage_module
    from src.app.db import SessionLocal
    from src.app.main import app
    from src.app.models import DocumentoConversao, LoteConversao, Workspace
    from src.app.storage import LocalDirectoryStorage

    storage = LocalDirectoryStorage(tmp_path / "uploads-spec-0023")
    monkeypatch.setattr(storage_module, "_STORAGE", storage)
    agora = datetime.now(UTC)
    with SessionLocal() as session:
        workspace = Workspace(
            tenant_id="tenant-1",
            project_id="projeto-1",
            nome="Retenção de conversões",
        )
        session.add(workspace)
        session.flush()
        lote = LoteConversao(
            tenant_id="tenant-1",
            project_id="projeto-1",
            workspace_id=workspace.id,
            situacao="concluido",
        )
        session.add(lote)
        session.flush()
        documento = DocumentoConversao(
            lote_id=lote.id,
            nome_arquivo="historico.pdf",
            formato="pdf",
            tamanho_bytes=20,
            situacao="concluido",
            concluido_em=agora - timedelta(days=8),
            expira_em=agora - timedelta(days=1),
        )
        session.add(documento)
        session.flush()
        workspace_id = workspace.id
        lote_id = lote.id
        documento_id = documento.id
        storage.save(documento_id, "historico.pdf", b"%PDF-1.7")
        storage.save(documento_id, "historico.md", "# Histórico\n".encode())
        session.commit()
    return TestClient(app), storage, workspace_id, lote_id, documento_id


def test_spec_0023_ac_013_purga_arquivos_mas_preserva_registros(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 FR-007 NFR-002 AC-013"""
    from src.app import tasks as tasks_module
    from src.app.db import SessionLocal
    purgar_documentos_conversao_task = tasks_module.purgar_documentos_conversao_task

    from src.app.models import DocumentoConversao, LoteConversao

    _, storage, _, lote_id, documento_id = _preparar_documento_expirado(
        tmp_path,
        monkeypatch,
    )

    purgar_documentos_conversao_task.func(_timestamp=0)

    assert not storage.list_files(documento_id)
    with SessionLocal() as session:
        assert session.get(LoteConversao, lote_id) is not None
        documento = session.get(DocumentoConversao, documento_id)
        assert documento is not None
        assert documento.apagado_em is not None
        assert documento.nome_arquivo == "historico.pdf"
        assert documento.situacao == "concluido"


def test_spec_0023_ac_014_historico_continua_consultavel_apos_purga(
    tmp_path,
    monkeypatch,
) -> None:
    """SPECSFY: SPEC-0023 FR-007 AC-014"""
    from src.app.tasks import purgar_documentos_conversao_task

    client, _, _, lote_id, documento_id = _preparar_documento_expirado(
        tmp_path,
        monkeypatch,
    )
    purgar_documentos_conversao_task.func(_timestamp=0)

    detalhe = client.get(
        f"/api/v1/conversoes/{lote_id}",
        headers=AUTH_OWNER,
    )
    download = client.get(
        f"/api/v1/conversoes/{lote_id}/documentos/{documento_id}/markdown",
        headers=AUTH_OWNER,
    )

    assert detalhe.status_code == 200
    assert detalhe.json()["documentos"] == [
        {
            **detalhe.json()["documentos"][0],
            "nome_arquivo": "historico.pdf",
            "formato": "pdf",
            "situacao": "concluido",
        }
    ]
    assert download.status_code == 404
