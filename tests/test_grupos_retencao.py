"""Retenção de 7 dias das imagens e propostas de lotes aguardando grupos (SPEC-0040)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests._fase1_conversao import armazenamento_temporario
from tests._fase1_grupos import exigir_modelo


def _lote_aguardando(session, storage, workspace_id, dias_de_idade: int, expira_em):
    from src.app.models import DocumentoConversao, LoteConversao

    GrupoImagem = exigir_modelo("GrupoImagem")
    agora = datetime.now(UTC)
    lote = LoteConversao(
        tenant_id="tenant-1",
        project_id="projeto-1",
        workspace_id=workspace_id,
        situacao="aguardando_grupos",
        criado_em=agora - timedelta(days=dias_de_idade),
    )
    session.add(lote)
    session.flush()
    grupo = GrupoImagem(lote_id=lote.id, ordem=1, certeza="incerta", aprovado=False)
    session.add(grupo)
    session.flush()
    ids = []
    for posicao in (1, 2):
        documento = DocumentoConversao(
            lote_id=lote.id,
            nome_arquivo=f"print-{posicao}.png",
            formato="png",
            tamanho_bytes=8,
            situacao="aguardando_grupos",
            grupo_id=grupo.id,
            posicao_no_grupo=posicao,
            expira_em=expira_em,
        )
        session.add(documento)
        session.flush()
        storage.save(documento.id, documento.nome_arquivo, b"\x89PNG....")
        ids.append(documento.id)
    return lote.id, ids


def test_spec_0040_ac_020_imagens_e_propostas_expiram_em_sete_dias(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0040 FR-008 NFR-001 AC-020"""
    from src.app import tasks
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao, Workspace

    GrupoImagem = exigir_modelo("GrupoImagem")
    storage = armazenamento_temporario(tmp_path, monkeypatch)
    agora = datetime.now(UTC)
    with SessionLocal() as session:
        workspace = Workspace(tenant_id="tenant-1", project_id="projeto-1", nome="Retenção")
        session.add(workspace)
        session.flush()
        antigo, ids_antigos = _lote_aguardando(
            session, storage, workspace.id, 8, agora - timedelta(days=1)
        )
        recente, ids_recentes = _lote_aguardando(
            session, storage, workspace.id, 2, agora + timedelta(days=5)
        )
        session.commit()

    tasks.purgar_documentos_conversao_task.func(0)

    with SessionLocal() as session:
        assert session.query(GrupoImagem).filter_by(lote_id=antigo).count() == 0
        assert session.query(GrupoImagem).filter_by(lote_id=recente).count() == 1
        for documento_id in ids_antigos:
            assert session.get(DocumentoConversao, documento_id).apagado_em is not None
            assert storage.list_files(documento_id) == []
        for documento_id in ids_recentes:
            assert session.get(DocumentoConversao, documento_id).apagado_em is None
            assert storage.list_files(documento_id) != []
