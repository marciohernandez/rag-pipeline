"""Retenção do histórico de versões e registros de decisão (SPEC-0039)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests._fase1_decisoes import exigir, hash_de, modelo_orm, montar_ciclo

AGORA = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)


def test_spec_0039_ac_014_versoes_vencem_em_90_dias_e_registros_ficam_com_a_colecao(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0039 US-003 FR-005 NFR-001 AC-014"""
    from src.app.db import SessionLocal
    from src.app.models import DocumentoColecao

    decisoes = exigir("src.app.decisoes")
    Versao, Decisao = modelo_orm("VersaoDocumento"), modelo_orm("DecisaoEmpresa")
    Proposta, Resposta = modelo_orm("PropostaCorrecao"), modelo_orm("RespostaEmpresa")
    ctx = montar_ciclo(tmp_path, monkeypatch, {})
    with SessionLocal() as session:
        doc = session.query(DocumentoColecao).filter_by(colecao_id=ctx.colecao_id).first()
        for numero, dias in ((1, 91), (2, 10)):
            criado = AGORA - timedelta(days=dias)
            session.add(
                Versao(
                    documento_id=doc.id,
                    numero=numero,
                    chave_armazenamento=f"v{numero}",
                    hash=hash_de(f"v{numero}"),
                    criado_em=criado,
                    expira_em=criado + timedelta(days=90),
                )
            )
        analise = (
            session.query(modelo_orm("AnaliseContradicao"))
            .filter_by(colecao_id=ctx.colecao_id)
            .one()
        )
        resposta = Resposta(colecao_id=ctx.colecao_id, analise_id=analise.id, texto="Vale 7 dias.")
        session.add(resposta)
        session.flush()
        proposta = Proposta(resposta_id=resposta.id, situacao="aceita", trecho_alvo="a")
        session.add(proposta)
        session.flush()
        session.add(
            Decisao(
                proposta_id=proposta.id, colecao_id=ctx.colecao_id, resposta_trecho="Vale 7 dias."
            )
        )
        session.commit()

    decisoes.purgar_retencao(AGORA)

    with SessionLocal() as session:
        assert [v.numero for v in session.query(Versao).all()] == [2]
        assert session.query(Decisao).filter_by(colecao_id=ctx.colecao_id).count() == 1

        decisoes.apagar_da_colecao(session, ctx.colecao_id, apagado_por="pessoa-1")
        session.commit()

    with SessionLocal() as session:
        assert session.query(Versao).count() == 0
        assert session.query(Decisao).count() == 0
        assert session.query(Proposta).count() == 0
        assert session.query(Resposta).count() == 0
        minimo = modelo_orm("RegistroExclusaoDecisoes")
        registros = session.query(minimo).filter_by(colecao_id=ctx.colecao_id).all()
        assert len(registros) == 1
        assert registros[0].apagado_por == "pessoa-1" and registros[0].decisoes == 1
        assert not hasattr(registros[0], "texto")
