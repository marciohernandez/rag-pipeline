"""Rotas da análise de contradições: permissões, avisos e erros (SPEC-0038)."""

from __future__ import annotations

from tests._fase1_contradicoes import (
    ADMIN_HEADERS,
    MEMBER,
    OWNER,
    IaContradicoes,
    analisar,
    modelo_orm,
    montar,
    montar_vazia,
    relatorio,
    rodar_fila,
)

COMERCIAL = "# Comercial\n\nO cancelamento pode ser feito em até 7 dias.\n"
MARKETING = "# Marketing\n\nO cancelamento pode ser feito em até 15 dias.\n"


def _modelo():
    return IaContradicoes(
        extracao={
            "comercial.md": [("cancelamento prazo", "Cancelamento em até 7 dias.", "alto")],
            "marketing.md": [("prazo de cancelamento", "Cancelamento em até 15 dias.", "alto")],
        },
        veredito={"cancelamento": ("conflito", "Os prazos divergem.")},
    )


def _nenhuma_analise() -> int:
    from src.app.db import SessionLocal

    with SessionLocal() as session:
        return session.query(modelo_orm("AnaliseContradicao")).count()


def test_spec_0038_ac_004_sem_ia_externa_permitida_avisa_e_nao_chama_o_modelo(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0038 US-001 FR-001 FR-006 NFR-001 AC-004"""
    modelo = _modelo()
    ctx = montar(
        tmp_path,
        monkeypatch,
        {"comercial.md": COMERCIAL, "marketing.md": MARKETING},
        modelo,
        ia_externa=False,
    )

    resposta = analisar(ctx)

    assert resposta.status_code == 409
    assert "IA externa" in resposta.json()["detail"]
    assert modelo.chamadas == 0
    assert _nenhuma_analise() == 0


def test_spec_0038_ac_005_member_nao_inicia_nem_continua(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0038 US-001 FR-001 FR-009 AC-005"""
    ctx = montar(
        tmp_path, monkeypatch, {"comercial.md": COMERCIAL, "marketing.md": MARKETING}, _modelo()
    )

    iniciar = analisar(ctx, headers=MEMBER)
    continuar = ctx.c.post(
        f"/api/v1/colecoes/{ctx.colecao_id}/contradicoes/analises/qualquer/continuar",
        headers=MEMBER,
    )
    admin = analisar(ctx, headers=ADMIN_HEADERS)

    assert iniciar.status_code == 403
    assert continuar.status_code == 403
    assert admin.status_code == 202
    assert _nenhuma_analise() == 1


def test_spec_0038_ac_005_sem_confirmacao_do_aviso_a_analise_nao_comeca(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0038 US-001 FR-001 FR-009 AC-005"""
    modelo = _modelo()
    ctx = montar(
        tmp_path, monkeypatch, {"comercial.md": COMERCIAL, "marketing.md": MARKETING}, modelo
    )

    resposta = analisar(ctx, confirmado=False)

    assert resposta.status_code == 422
    assert modelo.chamadas == 0
    assert _nenhuma_analise() == 0


def test_spec_0038_ac_014_colecao_vazia_avisa_e_nao_chama_a_ia(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0038 US-001 FR-006 AC-014"""
    modelo = _modelo()
    ctx = montar_vazia(tmp_path, monkeypatch, modelo)

    resposta = analisar(ctx)

    assert resposta.status_code == 422
    assert "não há" in resposta.json()["detail"].lower()
    assert modelo.chamadas == 0
    assert _nenhuma_analise() == 0


def test_spec_0038_ac_019_member_consulta_mas_nao_baixa(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0038 US-004 US-005 FR-008 FR-009 AC-019"""
    ctx = montar(
        tmp_path, monkeypatch, {"comercial.md": COMERCIAL, "marketing.md": MARKETING}, _modelo()
    )
    assert analisar(ctx).status_code == 202
    rodar_fila(ctx)
    base = f"/api/v1/colecoes/{ctx.colecao_id}/contradicoes"

    consulta = relatorio(ctx, headers=MEMBER)
    md = ctx.c.get(f"{base}/relatorio?formato=md", headers=MEMBER)
    pdf = ctx.c.get(f"{base}/relatorio?formato=pdf", headers=MEMBER)
    dono_md = ctx.c.get(f"{base}/relatorio?formato=md", headers=OWNER)
    dono_pdf = ctx.c.get(f"{base}/relatorio?formato=pdf", headers=OWNER)

    assert len(consulta["ocorrencias"]) == 1
    assert md.status_code == 403 and pdf.status_code == 403
    assert dono_md.status_code == 200 and "comercial.md" in dono_md.text
    assert dono_pdf.status_code == 200 and dono_pdf.content.startswith(b"%PDF")


def test_spec_0038_ac_005_segunda_analise_enquanto_a_primeira_esta_ativa_e_recusada(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0038 US-001 FR-001 FR-009 AC-005"""
    ctx = montar(
        tmp_path, monkeypatch, {"comercial.md": COMERCIAL, "marketing.md": MARKETING}, _modelo()
    )

    primeira = analisar(ctx)
    segunda = analisar(ctx)

    assert primeira.status_code == 202
    assert segunda.status_code == 409
    assert _nenhuma_analise() == 1
