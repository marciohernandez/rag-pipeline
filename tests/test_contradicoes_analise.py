"""Análise de contradições da coleção: fluxo, partes, retomada e retenção (SPEC-0038)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tests._fase1_contradicoes import (
    IaContradicoes,
    analisar,
    exigir,
    modelo_orm,
    montar,
    relatorio,
    rodar_fila,
)

AGORA = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)
COMERCIAL = "# Comercial\n\nO cancelamento pode ser feito em até 7 dias.\n"
MARKETING = "# Marketing\n\nO cancelamento pode ser feito em até 15 dias.\n"


def _estado_dos_documentos(ctx) -> list:
    from src.app.db import SessionLocal
    from src.app.models import ConteudoDocumento, DocumentoColecao

    with SessionLocal() as session:
        docs = session.query(DocumentoColecao).filter_by(colecao_id=ctx.colecao_id).all()
        return sorted(
            (
                d.nome_arquivo,
                d.source_hash,
                d.chunks,
                session.query(ConteudoDocumento).filter_by(documento_id=d.id).one().texto,
            )
            for d in docs
        )


def test_spec_0038_ac_001_conflito_entre_dois_arquivos_sem_alterar_documentos(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0038 US-001 US-002 FR-001 FR-003 FR-004 NFR-002 AC-001"""
    modelo = IaContradicoes(
        extracao={
            "comercial.md": [("cancelamento prazo", "Cancelamento em até 7 dias.", "alto")],
            "marketing.md": [("prazo de cancelamento", "Cancelamento em até 15 dias.", "alto")],
        },
        veredito={"cancelamento": ("conflito", "Os prazos de cancelamento divergem.")},
    )
    ctx = montar(
        tmp_path, monkeypatch, {"comercial.md": COMERCIAL, "marketing.md": MARKETING}, modelo
    )
    antes = _estado_dos_documentos(ctx)

    resposta = analisar(ctx)
    assert resposta.status_code == 202, resposta.text
    rodar_fila(ctx)
    dados = relatorio(ctx)

    assert dados["analise"]["situacao"] == "concluida"
    assert len(dados["ocorrencias"]) == 1
    ocorrencia = dados["ocorrencias"][0]
    assert ocorrencia["etiqueta"] == "conflito"
    assert "cancelamento" in ocorrencia["assunto"].lower()
    assert {t["arquivo"] for t in ocorrencia["trechos"]} == {"comercial.md", "marketing.md"}
    assert ocorrencia["explicacao"] == "Os prazos de cancelamento divergem."
    assert _estado_dos_documentos(ctx) == antes


def test_spec_0038_ac_010_retomada_julga_so_os_assuntos_que_faltam(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0038 US-003 FR-005 NFR-003 AC-010"""
    extracao = {
        "a.md": [(f"assunto {i}", f"Valor {i} é 10.") for i in range(10)],
        "b.md": [(f"assunto {i}", f"Valor {i} é 20.") for i in range(10)],
    }
    modelo = IaContradicoes(
        extracao=extracao, veredito={"assunto": ("conflito", "Valores diferentes.")}, cair_apos=6
    )
    ctx = montar(
        tmp_path, monkeypatch, {"a.md": "# A\n\nTexto.\n", "b.md": "# B\n\nTexto.\n"}, modelo
    )

    assert analisar(ctx).status_code == 202
    rodar_fila(ctx)
    parcial = relatorio(ctx)
    assert parcial["analise"]["situacao"] == "incompleta"
    assert parcial["analise"]["concluidos"] == 6
    assert len(parcial["ocorrencias"]) == 6

    modelo.cair_apos = None
    julgados_antes = list(modelo.julgados)
    continuar = ctx.c.post(
        f"/api/v1/colecoes/{ctx.colecao_id}/contradicoes/analises/{parcial['analise']['id']}/continuar",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    )
    assert continuar.status_code == 202, continuar.text
    rodar_fila(ctx)

    novos = modelo.julgados[len(julgados_antes) :]
    assert len(novos) == 4
    assert not set(novos) & set(julgados_antes)
    final = relatorio(ctx)
    assert final["analise"]["situacao"] == "concluida"
    assert len(final["ocorrencias"]) == 10
    assert len({o["assunto"] for o in final["ocorrencias"]}) == 10


def test_spec_0038_ac_012_cinquenta_documentos_em_partes_com_progresso(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0038 US-003 FR-005 NFR-003 AC-012"""
    corpo = "Texto de apoio do documento sobre a política da empresa. " * 70
    arquivos = {f"doc{i:02d}.md": f"# Doc {i}\n\n{corpo}\n" for i in range(50)}
    extracao = {
        nome: [("preço do plano", f"O plano custa {i} reais.", "alto")]
        for i, nome in enumerate(arquivos)
    }
    modelo = IaContradicoes(
        extracao=extracao, veredito={"plano": ("conflito", "Preços diferentes.")}
    )
    ctx = montar(tmp_path, monkeypatch, arquivos, modelo)

    assert analisar(ctx).status_code == 202
    rodar_fila(ctx, maximo=1)
    meio = relatorio(ctx)
    assert meio["analise"]["situacao"] == "em_andamento"
    assert ctx.fila, "a análise deveria reenfileirar a próxima parte"

    rodar_fila(ctx)
    final = relatorio(ctx)

    assert final["analise"]["situacao"] == "concluida"
    assert final["analise"]["documentos_analisados"] == 50
    assert len(modelo.prompts_extracao) > 1
    assert max(len(p) for p in modelo.prompts_extracao) <= 60_000
    assert 1 <= len(modelo.julgados) <= 3  # um assunto, em grupos de até 20 afirmações


def test_spec_0038_ac_013_ia_indisponivel_deixa_incompleta_sem_marcar_como_resolvido(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0038 US-003 FR-005 FR-006 AC-013"""
    modelo = IaContradicoes(indisponivel=True)
    ctx = montar(tmp_path, monkeypatch, {"a.md": COMERCIAL, "b.md": MARKETING}, modelo)

    assert analisar(ctx).status_code == 202
    rodar_fila(ctx)
    dados = relatorio(ctx)

    assert dados["analise"]["situacao"] == "incompleta"
    assert "IA indisponível" in dados["analise"]["motivo"]
    assert dados["ocorrencias"] == []
    assert dados["analise"]["situacao"] != "concluida"


def test_spec_0038_ac_020_retencao_de_90_dias_e_metadados_do_relatorio(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0038 US-004 FR-009 NFR-001 AC-020"""
    from src.app.db import SessionLocal

    Analise = modelo_orm("AnaliseContradicao")
    Ocorrencia = modelo_orm("OcorrenciaContradicao")
    ctx = montar(tmp_path, monkeypatch, {"a.md": COMERCIAL}, IaContradicoes())
    ids = {}
    with SessionLocal() as session:
        for rotulo, dias in (("antiga", 91), ("recente", 10)):
            criado = AGORA - timedelta(days=dias)
            analise = Analise(
                colecao_id=ctx.colecao_id,
                situacao="concluida",
                provedor="openrouter",
                total_assuntos=1,
                concluidos=1,
                documentos_analisados=2,
                criado_em=criado,
                concluido_em=criado,
                expira_em=criado + timedelta(days=90),
            )
            session.add(analise)
            session.flush()
            session.add(
                Ocorrencia(
                    analise_id=analise.id,
                    assunto="cancelamento",
                    assunto_normalizado="cancelamento",
                    etiqueta="conflito",
                    impacto="alto",
                    chave_trechos=f"k-{rotulo}",
                    trechos=[
                        {"arquivo": "a.md", "texto": "7 dias"},
                        {"arquivo": "b.md", "texto": "15 dias"},
                    ],
                    explicacao="Divergência.",
                )
            )
            ids[rotulo] = analise.id
        session.commit()

    exigir("src.app.contradicoes").purgar_retencao(agora=AGORA)

    with SessionLocal() as session:
        restantes = {a.id for a in session.query(Analise).all()}
        sobras = {o.analise_id for o in session.query(Ocorrencia).all()}
    assert restantes == {ids["recente"]}
    assert sobras == {ids["recente"]}
    analise = relatorio(ctx)["analise"]
    assert analise["provedor"] == "openrouter"
    assert "dominio_versao_id" in analise
