"""Tetos configuráveis por arquivo e por lote (SPEC-0036, US-004, FR-006)."""

from __future__ import annotations

from tests._fase1_conversao import (
    AUTH_OWNER,
    armazenamento_temporario,
    cliente,
    config_worker,
    criar_lote,
    executar,
    exigir,
    instalar_rede_falsa,
    ler_documento,
    pagina,
    sem_enfileirar,
)


def _arquivo(nome: str, tamanho: int):
    return ("arquivos", (nome, b"x" * tamanho, "image/png"))


def _definir_tetos(monkeypatch, **valores):
    """O roteador resolve os tetos por `_config_conversao()` (contrato da SPEC-0036)."""
    from src.app.routers import conversao as roteador
    from src.pipeline.conversion.config import ConversaoConfig

    monkeypatch.setattr(roteador, "_config_conversao", lambda: ConversaoConfig(**valores))


def _enviar(c, workspace_id, *arquivos):
    return c.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=list(arquivos),
        headers=AUTH_OWNER,
    )


def _preparar(tmp_path, monkeypatch):
    from tests.test_router_conversao import _criar_workspace

    c = cliente(tmp_path, monkeypatch)
    enfileirados = sem_enfileirar(monkeypatch)
    return c, _criar_workspace(c), enfileirados


def test_spec_0036_ac_009_resposta_acima_do_teto_recusa_so_aquela_url(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0036 US-001 US-004 FR-006 NFR-001 AC-009"""
    armazenamento_temporario(tmp_path, monkeypatch)
    config_worker(monkeypatch, max_bytes_url=1000)
    instalar_rede_falsa(
        monkeypatch,
        lambda url: (
            pagina("<html><body><p>" + "texto " * 2000 + "</p></body></html>")
            if "grande" in url
            else pagina()
        ),
    )
    _, ids = criar_lote(
        [
            {"nome": "grande.url", "formato": "url", "url": "https://exemplo.com/grande"},
            {"nome": "pequena.url", "formato": "url", "url": "https://exemplo.com/pequena"},
        ]
    )

    executar(ids["grande.url"])
    executar(ids["pequena.url"])

    grande = ler_documento(ids["grande.url"])
    assert grande.situacao == "falhou" and "tamanho" in (grande.erro or "")
    assert ler_documento(ids["pequena.url"]).situacao == "concluido"


def test_spec_0036_ac_016_arquivo_acima_do_teto_e_recusado_e_o_outro_segue(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0036 US-004 FR-006 AC-016"""
    c, workspace_id, enfileirados = _preparar(tmp_path, monkeypatch)
    _definir_tetos(monkeypatch, max_bytes_arquivo=500, max_bytes_lote=5000)

    resposta = _enviar(c, workspace_id, _arquivo("grande.png", 800), _arquivo("ok.png", 300))

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert [d["nome_arquivo"] for d in corpo["documentos"]] == ["ok.png"]
    assert [r["nome_arquivo"] for r in corpo["recusados"]] == ["grande.png"]
    assert "500" in corpo["recusados"][0]["motivo"]
    assert len(enfileirados) == 1


def test_spec_0036_ac_017_lote_acima_do_teto_recusa_o_excedente(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-004 FR-006 AC-017

    Usa PDFs: desde a SPEC-0040, duas ou mais imagens do mesmo envio aguardam a aprovação dos
    grupos e não são enfileiradas.
    """
    c, workspace_id, enfileirados = _preparar(tmp_path, monkeypatch)
    _definir_tetos(monkeypatch, max_bytes_arquivo=800, max_bytes_lote=1000)

    resposta = _enviar(
        c, workspace_id, _arquivo("a.pdf", 600), _arquivo("b.pdf", 600), _arquivo("c.pdf", 300)
    )

    corpo = resposta.json()
    assert [d["nome_arquivo"] for d in corpo["documentos"]] == ["a.pdf", "c.pdf"]
    assert [r["nome_arquivo"] for r in corpo["recusados"]] == ["b.pdf"]
    assert len(enfileirados) == 2


def test_spec_0036_ac_018_tetos_vem_da_configuracao(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-004 FR-006 NFR-005 AC-018"""
    config = exigir("src.pipeline.conversion.config")
    padrao = config.ConversaoConfig()
    assert padrao.max_bytes_arquivo == 40 * 1024 * 1024
    assert padrao.max_bytes_lote == 50 * 1024 * 1024
    assert (
        config.carregar_config_conversao(
            {"conversao": {"max_bytes_arquivo": 700, "max_bytes_lote": 900}}
        ).max_bytes_arquivo
        == 700
    )

    c, workspace_id, _ = _preparar(tmp_path, monkeypatch)
    _definir_tetos(monkeypatch, max_bytes_arquivo=500, max_bytes_lote=5000)
    assert _enviar(c, workspace_id, _arquivo("a.png", 600)).status_code == 400
    _definir_tetos(monkeypatch, max_bytes_arquivo=700, max_bytes_lote=5000)
    assert _enviar(c, workspace_id, _arquivo("a.png", 600)).status_code == 201


def test_spec_0036_url_tambem_respeita_teto_do_lote(tmp_path, monkeypatch):
    """SPECSFY: SPEC-0036 US-004 FR-006 NFR-001 AC-017 AC-009"""
    armazenamento_temporario(tmp_path, monkeypatch)
    config_worker(monkeypatch, max_bytes_url=900, max_bytes_lote=1000)
    instalar_rede_falsa(monkeypatch, pagina("<html><body>" + "texto " * 100 + "</body></html>"))
    _, ids = criar_lote(
        [
            {"nome": "a.url", "formato": "url", "url": "https://exemplo.com/a"},
            {"nome": "b.url", "formato": "url", "url": "https://exemplo.com/b"},
        ]
    )
    for id in ids.values():
        executar(id)
    assert ler_documento(ids["a.url"]).situacao == "concluido"
    assert ler_documento(ids["b.url"]).situacao == "falhou"
    assert "tamanho" in ler_documento(ids["b.url"]).erro
