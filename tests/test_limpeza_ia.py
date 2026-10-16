"""Avaliação por IA das seções restantes (SPEC-0037, US-003, FR-004, FR-005)."""

from __future__ import annotations

from tests._fase1_limpeza import (
    AUTH_OWNER,
    EspiaoIa,
    definir_dominio,
    exigir,
    ler_md,
    modelo_orm,
    preparar_lote,
)

REDES = "Siga-nos nas redes sociais e compartilhe esta página com os amigos."
TROCA = "A política de troca permite devolver o produto em até trinta dias."
NEGOCIO = "O plano básico custa 49 reais por mês, com suporte por e-mail."
RODAPE = "Empresa XPTO — Documento confidencial"


def _ligar(monkeypatch, limpeza, modelo):
    monkeypatch.setattr(limpeza, "criar_modelo_ia", lambda session, workspace: modelo)
    monkeypatch.setattr(limpeza, "enfileirar_limpeza", lambda documento_id: None)


def _limpar(tmp_path, monkeypatch, markdown, modelo, *, ia=True):
    limpeza = exigir("src.app.limpeza")
    _ligar(monkeypatch, limpeza, modelo)
    ctx = preparar_lote(tmp_path, monkeypatch, {"a.md": markdown}, ia=ia)
    assert definir_dominio(ctx).status_code == 200
    limpeza.preparar_limpeza_do_lote(ctx.lote_id)
    limpeza.limpar_documento(ctx.docs["a.md"])
    limpeza.finalizar_limpeza_lote(ctx.lote_id)
    lote = ctx.c.get(f"/api/v1/conversoes/{ctx.lote_id}", headers=AUTH_OWNER).json()
    return ctx, lote["documentos"][0]


def test_spec_0037_ac_008_chave_desligada_nao_envia_texto_a_ia(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0037 US-003 FR-004 FR-005 NFR-001 AC-008"""
    modelo = EspiaoIa()

    ctx, documento = _limpar(tmp_path, monkeypatch, f"# A\n\n{NEGOCIO}\n", modelo, ia=False)

    assert modelo.chamadas == 0
    assert documento["limpeza_situacao"] in {"limpo", "limpo_com_duvidas"}
    relatorio = ctx.c.get(f"/api/v1/conversoes/{ctx.lote_id}/relatorio", headers=AUTH_OWNER)
    assert "etapa de IA não rodou" in relatorio.text


def test_spec_0037_ac_009_baixa_confianca_e_mantida_e_marcada(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0037 US-003 FR-002 FR-005 NFR-002 AC-009"""
    from src.app.db import SessionLocal

    modelo = EspiaoIa({"Siga-nos": ("ruido", 0.95), "política de troca": ("ruido", 0.55)})
    markdown = f"# A\n\n{NEGOCIO}\n\n{REDES}\n\n{TROCA}\n"

    ctx, documento = _limpar(tmp_path, monkeypatch, markdown, modelo)

    limpo = ler_md(ctx.docs["a.md"], "a.md", tmp_path)
    assert "Siga-nos" not in limpo
    assert TROCA in limpo and NEGOCIO in limpo
    Exclusao = modelo_orm("ExclusaoLimpeza")
    with SessionLocal() as session:
        [exclusao] = session.query(Exclusao).filter_by(camada="ia").all()
    assert exclusao.confianca == 0.95 and "Siga-nos" in exclusao.trecho
    assert documento["limpeza_situacao"] == "limpo_com_duvidas" and documento["duvidas"] == 1
    relatorio = ctx.c.get(f"/api/v1/conversoes/{ctx.lote_id}/relatorio", headers=AUTH_OWNER).text
    assert "política de troca" in relatorio.lower()


def test_spec_0037_ac_010_ia_indisponivel_mantem_o_conteudo(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0037 US-003 FR-005 FR-008 NFR-003 AC-010"""
    from src.pipeline.providers.errors import ChatProviderError

    modelo = EspiaoIa(erro=ChatProviderError("indisponível"))
    markdown = f"# A\n\n{NEGOCIO}\n\n{REDES}\n"

    ctx, documento = _limpar(tmp_path, monkeypatch, markdown, modelo)

    assert modelo.chamadas >= 1
    limpo = ler_md(ctx.docs["a.md"], "a.md", tmp_path)
    assert REDES in limpo and NEGOCIO in limpo
    assert documento["limpeza_situacao"] == "limpo"
    assert "IA indisponível" in documento["limpeza_motivo"]
    relatorio = ctx.c.get(f"/api/v1/conversoes/{ctx.lote_id}/relatorio", headers=AUTH_OWNER).text
    assert "etapa de IA não rodou" in relatorio


def test_spec_0037_ac_020_ia_so_recebe_o_que_as_regras_deixaram(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0037 US-003 FR-005 NFR-003 AC-020"""
    modelo = EspiaoIa()
    markdown = f"# A\n\n{NEGOCIO}\n\n{RODAPE}\n\n1\n\n{TROCA}\n\n{RODAPE}\n\n2\n\n{RODAPE}\n"

    _limpar(tmp_path, monkeypatch, markdown, modelo)

    enviado = "\n".join(modelo.mensagens)
    assert NEGOCIO in enviado and TROCA in enviado
    assert RODAPE not in enviado

    avaliacao = exigir("src.pipeline.limpeza.avaliacao_ia")
    limitado = EspiaoIa()
    secoes = [f"Seção {i}: " + "texto de negócio " * 6 for i in range(6)]
    avaliacao.AvaliadorIa(limitado, max_chars_por_requisicao=250).avaliar(secoes, "domínio")
    assert limitado.chamadas >= 3
    assert all(
        sum(len(s) for s in secoes if s in mensagem) <= 250 for mensagem in limitado.mensagens
    )
    assert all(any(s in m for m in limitado.mensagens) for s in secoes)
