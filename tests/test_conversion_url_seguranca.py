"""Segurança da busca de URL e do HTML (SPEC-0036, FR-002, NFR-001, NFR-002)."""

from __future__ import annotations

import logging
import socket
import tempfile
from pathlib import Path

from tests._fase1_conversao import (
    HTML_COM_TEXTO,
    RespostaFalsa,
    Transporte,
    armazenamento_temporario,
    criar_lote,
    executar,
    exigir,
    instalar_rede_falsa,
    ler_documento,
    pagina,
)

INTERNOS = [
    "http://localhost/",
    "http://127.0.0.1/",
    "http://10.0.0.5/",
    "http://192.168.0.1/",
    "http://169.254.169.254/latest/meta-data",
    "http://[::1]/",
]


def _buscador(transporte, resolver=None):
    modulo = exigir("src.pipeline.conversion.url_fetcher")
    return modulo, modulo.UrlFetcher(
        config=None, resolver=resolver or (lambda host: ["93.184.216.34"]), transporte=transporte
    )


def test_spec_0036_ac_004_enderecos_internos_sao_recusados() -> None:
    """SPECSFY: SPEC-0036 US-001 FR-002 NFR-001 AC-004"""
    modulo = exigir("src.pipeline.conversion.url_fetcher")
    transporte = Transporte(pagina())
    for endereco in INTERNOS:
        buscador = modulo.UrlFetcher(
            config=None, resolver=lambda host: ["127.0.0.1"], transporte=transporte
        )
        try:
            buscador.buscar(endereco)
        except modulo.UrlBloqueadaError:
            continue
        raise AssertionError(f"{endereco} deveria ser recusado")
    assert transporte.chamadas == []


def test_spec_0036_ac_005_redirecionamento_para_rede_interna_e_bloqueado() -> None:
    """SPECSFY: SPEC-0036 US-001 FR-002 NFR-001 AC-005"""
    transporte = Transporte(
        RespostaFalsa(302, {"location": "http://10.0.0.5/admin", "content-type": "text/html"})
    )
    modulo, buscador = _buscador(transporte)

    try:
        buscador.buscar("https://exemplo.com/")
    except (modulo.UrlBloqueadaError, modulo.BuscaFalhouError):
        pass
    else:
        raise AssertionError("redirecionamento interno deveria ser bloqueado")
    assert [url for url, _ in transporte.chamadas] == ["https://exemplo.com/"]


def test_spec_0036_ac_006_dns_que_resolve_para_interno_e_bloqueado() -> None:
    """SPECSFY: SPEC-0036 US-001 FR-002 NFR-001 AC-006"""
    transporte = Transporte(pagina())
    modulo, buscador = _buscador(transporte, resolver=lambda host: ["93.184.216.34", "10.0.0.5"])
    try:
        buscador.buscar("https://intranet.exemplo.com/")
    except modulo.UrlBloqueadaError:
        pass
    else:
        raise AssertionError("nome com algum endereço interno deveria ser recusado")
    assert transporte.chamadas == []

    consultas: list[str] = []
    ok = Transporte(pagina())
    _, bom = _buscador(ok, resolver=lambda host: (consultas.append(host), ["93.184.216.34"])[1])
    bom.buscar("https://exemplo.com/")
    assert consultas == ["exemplo.com"]
    assert ok.chamadas == [("https://exemplo.com/", "93.184.216.34")]


def test_spec_0036_ac_012_scripts_do_html_nunca_sao_executados(monkeypatch) -> None:
    """SPECSFY: SPEC-0036 US-002 FR-004 NFR-001 AC-012"""
    modulo = exigir("src.pipeline.conversion.converters.html")
    conexoes: list[object] = []
    monkeypatch.setattr(socket.socket, "connect", lambda self, *a: conexoes.append(a))
    html = HTML_COM_TEXTO.replace(
        "window.segredo", "fetch('http://evil.example/x'); window.segredo"
    )
    with tempfile.TemporaryDirectory() as pasta:
        arquivo = Path(pasta) / "pagina.html"
        arquivo.write_text(html, encoding="utf-8")
        resultado = modulo.HtmlConverter().converter(arquivo)

    assert conexoes == []
    assert "fetch(" not in resultado.markdown and "evil.example" not in resultado.markdown


def test_spec_0036_ac_026_logs_e_mensagens_nao_expoem_credenciais(
    tmp_path, monkeypatch, caplog
) -> None:
    """SPECSFY: SPEC-0036 NFR-002 NFR-001 US-001 AC-026"""
    armazenamento_temporario(tmp_path, monkeypatch)

    def quebrar(url):
        raise OSError("conexão recusada")

    instalar_rede_falsa(monkeypatch, quebrar)
    segredo = "https://usuario:senha-secreta@exemplo.com/p?token=token-secreto"
    _, ids = criar_lote([{"nome": "p.url", "formato": "url", "url": segredo}])

    with caplog.at_level(logging.DEBUG):
        executar(ids["p.url"])

    doc = ler_documento(ids["p.url"])
    assert doc.situacao == "falhou"
    texto = caplog.text + (doc.erro or "")
    assert "senha-secreta" not in texto and "token-secreto" not in texto
