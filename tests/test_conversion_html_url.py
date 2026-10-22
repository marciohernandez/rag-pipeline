"""Conversão de URL e de arquivo .html para Markdown (SPEC-0036, US-001/US-002)."""

from __future__ import annotations

from pathlib import Path

from tests._fase1_conversao import (
    AUTH_OWNER,
    HTML_COM_TEXTO,
    HTML_SEM_TEXTO,
    RespostaFalsa,
    armazenamento_temporario,
    cliente,
    criar_lote,
    executar,
    exigir,
    instalar_rede_falsa,
    ler_documento,
    ler_markdown,
    pagina,
    sem_enfileirar,
)

URL = "https://exemplo.com/politica"


def test_spec_0036_ac_001_url_publica_gera_markdown_rastreavel(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-001 FR-001 FR-009 NFR-003 AC-001"""
    from tests.test_router_conversao import _criar_workspace

    c = cliente(tmp_path, monkeypatch)
    instalar_rede_falsa(monkeypatch, pagina())
    enfileirados = sem_enfileirar(monkeypatch)
    workspace_id = _criar_workspace(c)

    resposta = c.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id, "urls": [URL]},
        headers=AUTH_OWNER,
    )

    assert resposta.status_code == 201
    documento = resposta.json()["documentos"][0]
    assert documento["situacao"] == "fila"
    assert documento["formato"] == "url"
    executar(enfileirados[0])
    assert ler_documento(enfileirados[0]).situacao == "concluido"
    from src.app.storage import get_storage

    md = ler_markdown(
        get_storage(), enfileirados[0], f"{Path(documento['nome_arquivo']).stem}.md", tmp_path
    )
    assert "Política de reembolso" in md
    assert "dez dias úteis" in md
    assert URL in md


def test_spec_0036_ac_002_uma_url_um_documento_sem_seguir_links(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-001 FR-001 AC-002"""
    armazenamento_temporario(tmp_path, monkeypatch)
    transporte = instalar_rede_falsa(monkeypatch, pagina())
    _, ids = criar_lote([{"nome": "politica.url", "formato": "url", "url": URL}])

    executar(ids["politica.url"])

    assert ler_documento(ids["politica.url"]).situacao == "concluido"
    assert [url for url, _ in transporte.chamadas] == [URL]


def test_spec_0036_ac_003_falha_de_rede_marca_so_o_documento(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-001 FR-001 NFR-001 AC-003"""
    armazenamento_temporario(tmp_path, monkeypatch)
    instalar_rede_falsa(
        monkeypatch,
        lambda url: (
            RespostaFalsa(500, corpo=b"erro interno do servidor 10.1.2.3")
            if "quebrada" in url
            else pagina()
        ),
    )
    _, ids = criar_lote(
        [
            {"nome": "quebrada.url", "formato": "url", "url": "https://exemplo.com/quebrada"},
            {"nome": "boa.url", "formato": "url", "url": URL},
        ]
    )

    executar(ids["quebrada.url"])
    executar(ids["boa.url"])

    falhou = ler_documento(ids["quebrada.url"])
    assert falhou.situacao == "falhou"
    assert falhou.erro and "10.1.2.3" not in falhou.erro and "500" not in falhou.erro
    assert ler_documento(ids["boa.url"]).situacao == "concluido"


def test_spec_0036_ac_007_pagina_sem_texto_orienta_salvar_html(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-001 FR-003 AC-007"""
    armazenamento_temporario(tmp_path, monkeypatch)
    instalar_rede_falsa(monkeypatch, pagina(HTML_SEM_TEXTO))
    _, ids = criar_lote([{"nome": "vazia.url", "formato": "url", "url": URL}])

    executar(ids["vazia.url"])

    doc = ler_documento(ids["vazia.url"])
    assert doc.situacao == "falhou"
    assert "não consegui extrair o conteúdo" in (doc.erro or "")
    assert ".html" in (doc.erro or "")


def test_spec_0036_ac_008_resposta_que_nao_e_html_e_recusada() -> None:
    """SPECSFY: SPEC-0036 US-001 FR-003 FR-001 AC-008"""
    modulo = exigir("src.pipeline.conversion.url_fetcher")
    pdf = RespostaFalsa(200, {"content-type": "application/pdf"}, b"%PDF-1.7 ...")
    buscador = modulo.UrlFetcher(
        config=None, resolver=lambda host: ["93.184.216.34"], transporte=lambda *a: pdf
    )

    try:
        buscador.buscar(URL)
    except modulo.BuscaFalhouError as erro:
        assert "página" in str(erro)
        assert "não consegui extrair o conteúdo" in str(erro)
    else:
        raise AssertionError("resposta que não é HTML deveria ser recusada")


def test_spec_0036_ac_010_arquivo_html_gera_markdown_sem_scripts(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-002 FR-004 FR-009 AC-010"""
    storage = armazenamento_temporario(tmp_path, monkeypatch)
    _, ids = criar_lote(
        [{"nome": "politica.html", "formato": "html", "conteudo": HTML_COM_TEXTO.encode()}]
    )

    executar(ids["politica.html"])

    assert ler_documento(ids["politica.html"]).situacao == "concluido"
    md = ler_markdown(storage, ids["politica.html"], "politica.md", tmp_path)
    assert "dez dias úteis" in md
    assert "codigo-do-script" not in md and "color:red" not in md


def test_spec_0036_ac_011_html_sem_texto_util_orienta_a_pessoa() -> None:
    """SPECSFY: SPEC-0036 US-002 FR-003 FR-004 AC-011"""
    modulo = exigir("src.pipeline.conversion.converters.html")
    contratos = exigir("src.pipeline.conversion.contracts")
    import tempfile

    with tempfile.TemporaryDirectory() as pasta:
        arquivo = Path(pasta) / "vazio.html"
        arquivo.write_text(HTML_SEM_TEXTO, encoding="utf-8")
        try:
            modulo.HtmlConverter().converter(arquivo)
        except contratos.ConversionUserError as erro:
            assert "não consegui extrair o conteúdo" in str(erro)
        else:
            raise AssertionError("HTML sem texto deveria falhar com orientação")
