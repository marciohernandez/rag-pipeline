"""Apoio dos testes da SPEC-0036 (fase RED).

Os módulos novos ainda não existem quando os testes são escritos. `exigir` importa
o módulo só no corpo do teste e reprova por asserção quando ele falta, para que o
RED seja pelo comportamento ausente e não por erro de coleta.

Contratos assumidos pelos testes (seção 8 da SPEC-0036):

- ``src.pipeline.conversion.url_fetcher``: ``UrlFetcher(config, resolver=None,
  transporte=None).buscar(url) -> ResultadoBusca(html, url_final)``, as exceções
  ``UrlBloqueadaError`` e ``BuscaFalhouError`` (ambas ``ConversionError``), a
  validação pura ``validar_url_publica(url, resolver=None)`` e as funções padrão
  ``resolver_padrao(host) -> list[str]`` e
  ``transporte_padrao(url, ip, timeout, max_bytes) -> RespostaHttp``.
- ``src.pipeline.conversion.contracts.ConversionUserError``: ``ConversionError``
  cuja mensagem é segura para exibir à pessoa.
- ``src.pipeline.conversion.converters.html.HtmlConverter``.
- ``src.pipeline.conversion.qualidade.avaliar_qualidade(markdown, config)``.
- ``src.pipeline.conversion.reprocessar_ia.ReprocessadorIa.reprocessar(caminho,
  formato) -> str`` e ``src.app.tasks.reprocessar_documento_ia_task``.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

AUTH_OWNER = {"Authorization": "Bearer pessoa-teste-owner"}
AUTH_MEMBER = {"Authorization": "Bearer pessoa-teste-member"}
HTML_COM_TEXTO = (
    "<html><head><title>Política de reembolso</title><style>.x{color:red}</style></head>"
    "<body><h1>Política de reembolso</h1><p>O reembolso é feito em até dez dias úteis.</p>"
    "<script>window.segredo = 'codigo-do-script'</script>"
    '<a href="https://exemplo.com/outra">Outra página</a></body></html>'
)
HTML_SEM_TEXTO = (
    '<html><body><div id="app"></div><script>carregar()</script></body></html>'
)


def exigir(modulo: str):
    try:
        return importlib.import_module(modulo)
    except ImportError:
        pytest.fail(f"{modulo} ainda não existe (comportamento ainda ausente)")


class RespostaFalsa:
    def __init__(self, status=200, cabecalhos=None, corpo=b""):
        self.status = status
        self.cabecalhos = cabecalhos or {"content-type": "text/html; charset=utf-8"}
        self.corpo = corpo


def pagina(html: str = HTML_COM_TEXTO, **extra) -> RespostaFalsa:
    return RespostaFalsa(200, corpo=html.encode("utf-8"), **extra)


class Transporte:
    """Transporte HTTP falso que registra cada conexão (url, ip)."""

    def __init__(self, respostas):
        self.respostas = respostas if callable(respostas) else (lambda url: respostas)
        self.chamadas: list[tuple[str, str]] = []

    def __call__(self, url, ip, timeout, max_bytes):
        self.chamadas.append((url, ip))
        return self.respostas(url)


def resolver_para(mapa: dict[str, list[str]]):
    return lambda host: mapa.get(host, ["93.184.216.34"])


def instalar_rede_falsa(monkeypatch, respostas, mapa_dns=None):
    """Substitui resolver e transporte padrão do `UrlFetcher` usado pelo worker."""
    modulo = exigir("src.pipeline.conversion.url_fetcher")
    transporte = Transporte(respostas)
    monkeypatch.setattr(modulo, "resolver_padrao", resolver_para(mapa_dns or {}))
    monkeypatch.setattr(modulo, "transporte_padrao", transporte)
    return transporte


def config_worker(monkeypatch, **conversao):
    from src.app import settings as settings_module

    monkeypatch.setattr(
        settings_module, "get_settings", lambda: SimpleNamespace(conversao=conversao)
    )


def criar_lote(documentos: list[dict], *, tenant="tenant-1", projeto="projeto-1"):
    """Cria workspace, lote e documentos; devolve (lote_id, {nome: documento_id})."""
    from src.app import storage as storage_module
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao, LoteConversao, Workspace

    storage = storage_module.get_storage()
    ids: dict[str, str] = {}
    with SessionLocal() as session:
        workspace = Workspace(tenant_id=tenant, project_id=projeto, nome="Fase 1 conversão")
        session.add(workspace)
        session.flush()
        lote = LoteConversao(
            tenant_id=tenant,
            project_id=projeto,
            workspace_id=workspace.id,
            situacao="processando",
        )
        session.add(lote)
        session.flush()
        for item in documentos:
            conteudo = item.get("conteudo", b"")
            documento = DocumentoConversao(
                lote_id=lote.id,
                nome_arquivo=item["nome"],
                formato=item["formato"],
                tamanho_bytes=len(conteudo),
                situacao=item.get("situacao", "fila"),
            )
            if "url" in item:
                documento.origem_url = item["url"]
            session.add(documento)
            session.flush()
            if conteudo:
                storage.save(documento.id, item["nome"], conteudo)
            ids[item["nome"]] = documento.id
        session.commit()
        return lote.id, ids


def armazenamento_temporario(tmp_path, monkeypatch):
    from src.app import storage as storage_module
    from src.app.main import app as _app  # noqa: F401 — configura banco e storage
    from src.app.storage import LocalDirectoryStorage

    storage = LocalDirectoryStorage(str(tmp_path / "uploads-spec-0036"))
    monkeypatch.setattr(storage_module, "_STORAGE", storage)
    return storage


def executar(documento_id: str) -> None:
    from src.app import tasks

    tasks.process_conversion_document_task.func(documento_id=documento_id)


def ler_documento(documento_id: str):
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao

    with SessionLocal() as session:
        d = session.get(DocumentoConversao, documento_id)
        return SimpleNamespace(
            situacao=d.situacao, erro=d.erro, avisos=list(d.avisos or []), nome=d.nome_arquivo
        )


def ler_markdown(storage, documento_id: str, nome_md: str, tmp: Path) -> str:
    pasta = tmp / f"md-{documento_id}"
    storage.materialize(documento_id, pasta)
    return (pasta / nome_md).read_text(encoding="utf-8")


def cliente(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from src.app.main import app
    from tests.test_router_conversao import _cliente_com_storage_temporario

    _cliente_com_storage_temporario(tmp_path, monkeypatch)
    return TestClient(app)


def sem_enfileirar(monkeypatch):
    """Evita o job real e devolve a lista de ids enfileirados."""
    from src.app import tasks

    enfileirados: list[str] = []
    monkeypatch.setattr(
        tasks.process_conversion_document_task,
        "defer",
        lambda **kw: enfileirados.append(kw["documento_id"]),
    )
    return enfileirados
