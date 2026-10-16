"""Retenção do log de exclusões e do relatório do lote (SPEC-0037, FR-002, FR-007, NFR-001)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests._fase1_limpeza import AUTH_MEMBER, AUTH_OWNER, exigir, modelo_orm, preparar_lote

AGORA = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)


def test_spec_0037_ac_004_texto_removido_30_dias_e_acesso_restrito(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0037 US-001 FR-002 FR-009 NFR-001 AC-004"""
    from src.app.db import SessionLocal

    ctx = preparar_lote(tmp_path, monkeypatch, {"a.md": "# A\n"})
    Exclusao = modelo_orm("ExclusaoLimpeza")
    with SessionLocal() as session:
        for dias, motivo in ((31, "rodape"), (5, "numero de pagina")):
            session.add(
                Exclusao(
                    lote_id=ctx.lote_id,
                    documento_id=ctx.docs["a.md"],
                    arquivo="a.md",
                    posicao=1,
                    motivo=motivo,
                    camada="regra",
                    trecho=f"texto-{dias}",
                    criado_em=AGORA - timedelta(days=dias),
                )
            )
        session.commit()

    exigir("src.app.limpeza").purgar_retencao(agora=AGORA)

    with SessionLocal() as session:
        por_motivo = {e.motivo: e for e in session.query(Exclusao).all()}
    assert por_motivo["rodape"].trecho is None
    assert por_motivo["rodape"].arquivo == "a.md" and por_motivo["rodape"].posicao == 1
    assert por_motivo["numero de pagina"].trecho == "texto-5"
    url = f"/api/v1/conversoes/{ctx.lote_id}/exclusoes"
    assert ctx.c.get(url, headers=AUTH_MEMBER).status_code == 403
    dono = ctx.c.get(url, headers=AUTH_OWNER)
    assert dono.status_code == 200
    assert "texto-5" in dono.text


def test_spec_0037_ac_017_relatorio_vence_em_90_dias(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0037 US-005 FR-007 NFR-001 AC-017"""
    from src.app.db import SessionLocal
    from src.app.models import LoteConversao

    antigo = preparar_lote(tmp_path, monkeypatch, {"a.md": "# A\n"})
    recente = preparar_lote(tmp_path, monkeypatch, {"b.md": "# B\n"})
    Relatorio = modelo_orm("RelatorioLote")
    with SessionLocal() as session:
        for lote_id, dias in ((antigo.lote_id, 91), (recente.lote_id, 10)):
            criado = AGORA - timedelta(days=dias)
            session.add(
                Relatorio(
                    lote_id=lote_id,
                    conteudo="# Relatório",
                    ia_usada=False,
                    provedor=None,
                    contagens={},
                    criado_em=criado,
                    expira_em=criado + timedelta(days=90),
                )
            )
        session.commit()

    exigir("src.app.limpeza").purgar_retencao(agora=AGORA)

    with SessionLocal() as session:
        ids = {r.lote_id for r in session.query(Relatorio).all()}
        assert ids == {recente.lote_id}
        assert session.get(LoteConversao, antigo.lote_id) is not None
