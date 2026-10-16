"""Rotas da limpeza: conexão de IA, retomada e andamento (SPEC-0037)."""

from __future__ import annotations

from tests._conexoes import CHAVE_EMBEDDINGS, criar_conexao, payload_embeddings
from tests._fase1_limpeza import (
    AUTH_MEMBER,
    AUTH_OWNER,
    CHAVE_IA,
    definir_dominio,
    exigir,
    preparar_lote,
)

HEADERS = {"owner": AUTH_OWNER, "member": AUTH_MEMBER}


def _payload_ia(**extra):
    dados = {
        "nome": "IA de análise",
        "tipo": "ia_analise",
        "configuracao": {"modelo": "modelo-de-analise", "url_base": "https://api.exemplo.com/v1"},
        "segredo": CHAVE_IA,
    }
    dados.update(extra)
    return dados


def test_spec_0037_ac_018_conexao_de_ia_por_workspace_e_sigilo_da_chave(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0037 US-003 FR-004 FR-009 NFR-001 AC-018"""
    ctx = preparar_lote(tmp_path, monkeypatch, {"a.md": "# A\n"})
    c = ctx.c
    criada = criar_conexao(c, _payload_ia())
    assert criada.status_code == 201, criada.text
    assert CHAVE_IA not in criada.text
    embeddings = criar_conexao(c, payload_embeddings())
    url = f"/api/v1/workspaces/{ctx.workspace_id}/analise-ia"

    ok = c.patch(
        url,
        json={"ia_externa_permitida": True, "conexao_ia_id": criada.json()["id"]},
        headers=AUTH_OWNER,
    )
    errada = c.patch(
        url,
        json={"ia_externa_permitida": True, "conexao_ia_id": embeddings.json()["id"]},
        headers=AUTH_OWNER,
    )
    negada = c.patch(url, json={"ia_externa_permitida": False}, headers=AUTH_MEMBER)

    assert ok.status_code == 200
    assert CHAVE_IA not in ok.text and CHAVE_EMBEDDINGS not in ok.text
    assert errada.status_code == 422
    assert negada.status_code == 403


def test_spec_0037_ac_013_cinquenta_documentos_e_retomada_so_dos_que_falharam(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0037 US-005 FR-008 NFR-003 AC-013"""
    from src.app import storage as storage_module

    limpeza = exigir("src.app.limpeza")
    regras = exigir("src.pipeline.limpeza.regras")
    monkeypatch.setattr(limpeza, "enfileirar_limpeza", lambda documento_id: None)
    markdowns = {f"d{i:02d}.md": f"# Doc {i}\n\nConteúdo de negócio {i}.\n" for i in range(50)}
    ctx = preparar_lote(tmp_path, monkeypatch, markdowns)
    assert definir_dominio(ctx).status_code == 200
    storage = storage_module.get_storage()
    ausentes = [ctx.docs["d03.md"], ctx.docs["d41.md"]]
    for documento_id in ausentes:
        storage.delete_base(documento_id)
    chamadas: list[str] = []
    original = regras.aplicar_regras_fixas
    monkeypatch.setattr(
        regras,
        "aplicar_regras_fixas",
        lambda markdown, arquivo: (chamadas.append(arquivo), original(markdown, arquivo))[1],
    )

    limpeza.preparar_limpeza_do_lote(ctx.lote_id)
    for documento_id in ctx.docs.values():
        limpeza.limpar_documento(documento_id)

    lote = ctx.c.get(f"/api/v1/conversoes/{ctx.lote_id}", headers=AUTH_OWNER).json()
    assert lote["limpeza"] == {"total": 50, "concluidos": 48, "falhas": 2}
    falharam = [d["id"] for d in lote["documentos"] if d["limpeza_situacao"] == "falhou"]
    assert sorted(falharam) == sorted(ausentes)
    assert all(d["limpeza_motivo"] for d in lote["documentos"] if d["id"] in falharam)

    for nome in ("d03.md", "d41.md"):
        storage.save(ctx.docs[nome], nome, markdowns[nome].encode("utf-8"))
    chamadas.clear()
    for documento_id in falharam:
        resposta = ctx.c.post(
            f"/api/v1/conversoes/{ctx.lote_id}/documentos/{documento_id}/limpar",
            headers=AUTH_OWNER,
        )
        assert resposta.status_code in {200, 202}
        limpeza.limpar_documento(documento_id)

    assert sorted(chamadas) == ["d03.md", "d41.md"]
    lote = ctx.c.get(f"/api/v1/conversoes/{ctx.lote_id}", headers=AUTH_OWNER).json()
    assert lote["limpeza"]["concluidos"] == 50 and lote["limpeza"]["falhas"] == 0
