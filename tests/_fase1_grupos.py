"""Apoio dos testes da SPEC-0040 (fase RED): grupos de imagens do lote de conversão.

Contratos assumidos pelos testes (seções 8 a 10 da SPEC-0040):

- ``POST /api/v1/conversoes`` aceita o campo de formulário ``metadados`` (JSON: lista de
  ``{"nome", "modificado_em", "pasta"}``). Com duas ou mais imagens o lote volta em
  ``aguardando_grupos`` e as imagens ficam com a situação ``aguardando_grupos`` (nada é
  enfileirado).
- ``GET /api/v1/conversoes/{lote}/grupos`` → ``{"certeza", "grupos": [{"id", "ordem", "certeza",
  "aprovado", "imagens": [{"documento_id", "nome_arquivo", "posicao"}]}]}`` (qualquer papel).
- ``PUT /api/v1/conversoes/{lote}/grupos`` → corpo ``{"grupos": [{"imagens": [documento_id]}]}``
  (owner/admin); 422 para imagem em dois grupos ou grupo vazio.
- ``POST /api/v1/conversoes/{lote}/grupos/confirmar`` (owner/admin) cria um documento de formato
  ``grupo`` por grupo (``grupo-<ordem>.grupo``) e um documento próprio por imagem isolada, e
  enfileira cada um; o ``.md`` do grupo traz uma seção por imagem na ordem aprovada.
- Models: ``GrupoImagem`` (``lote_id``, ``ordem``, ``certeza``, ``aprovado``) e as colunas
  ``grupo_id``, ``posicao_no_grupo``, ``modificado_em`` e ``pasta_origem`` em
  ``DocumentoConversao``.
"""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from tests._fase1_conversao import (
    AUTH_MEMBER,
    AUTH_OWNER,
    cliente,
    executar,
    exigir,
    sem_enfileirar,
)

__all__ = [
    "AUTH_MEMBER",
    "AUTH_OWNER",
    "BASE",
    "Img",
    "confirmar",
    "dados_do_lote",
    "documentos_do_grupo",
    "enviar",
    "executar_todos",
    "exigir",
    "grupos",
    "markdown_de",
    "preparar",
]

BASE = datetime(2026, 10, 16, 10, 0, tzinfo=UTC)


class Img(SimpleNamespace):
    """Imagem do envio: ``nome``, ``largura`` (chave do OCR falso), ``minutos`` e ``pasta``."""

    def __init__(self, nome: str, largura: int, minutos: int = 0, pasta: str | None = None):
        super().__init__(nome=nome, largura=largura, minutos=minutos, pasta=pasta)


def _png(largura: int) -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (largura, 12), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def preparar(tmp_path, monkeypatch, ocr: dict[int, str | Exception]):
    """Cliente, fila capturada e OCR falso (texto ou erro por largura da imagem)."""
    import pytesseract

    from tests.test_router_conversao import _criar_workspace

    c = cliente(tmp_path, monkeypatch)
    enfileirados = sem_enfileirar(monkeypatch)
    estado = SimpleNamespace(ocr=dict(ocr))

    def ocr_falso(imagem, lang=None, **kwargs):
        resultado = estado.ocr.get(imagem.width, "")
        if isinstance(resultado, Exception):
            raise resultado
        return resultado

    monkeypatch.setattr(pytesseract, "image_to_string", ocr_falso)
    return SimpleNamespace(
        c=c, enfileirados=enfileirados, workspace_id=_criar_workspace(c), estado=estado
    )


def enviar(ctx, imagens: list[Img], extras=None, headers=AUTH_OWNER):
    metadados = [
        {
            "nome": i.nome,
            "modificado_em": (BASE + timedelta(minutes=i.minutos)).isoformat(),
            "pasta": i.pasta,
        }
        for i in imagens
    ]
    arquivos = [("arquivos", (i.nome, _png(i.largura), "image/png")) for i in imagens]
    arquivos += list(extras or [])
    resposta = ctx.c.post(
        "/api/v1/conversoes",
        data={"workspace_id": ctx.workspace_id, "metadados": json.dumps(metadados)},
        files=arquivos,
        headers=headers,
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def grupos(ctx, lote_id: str, headers=AUTH_OWNER) -> dict:
    resposta = ctx.c.get(f"/api/v1/conversoes/{lote_id}/grupos", headers=headers)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def confirmar(ctx, lote_id: str, headers=AUTH_OWNER):
    return ctx.c.post(f"/api/v1/conversoes/{lote_id}/grupos/confirmar", json={}, headers=headers)


def dados_do_lote(ctx, lote_id: str, headers=AUTH_OWNER) -> dict:
    resposta = ctx.c.get(f"/api/v1/conversoes/{lote_id}", headers=headers)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def documentos_do_grupo(ctx, lote_id: str) -> list[dict]:
    """Documentos de formato ``grupo`` do lote, na ordem do nome (``grupo-1``, ``grupo-2``...)."""
    docs = [d for d in dados_do_lote(ctx, lote_id)["documentos"] if d["formato"] == "grupo"]
    return sorted(docs, key=lambda d: d["nome_arquivo"])


def executar_todos(ctx) -> int:
    rodados = 0
    while ctx.enfileirados:
        executar(ctx.enfileirados.pop(0))
        rodados += 1
    return rodados


def markdown_de(ctx, lote_id: str, documento_id: str) -> str:
    resposta = ctx.c.get(
        f"/api/v1/conversoes/{lote_id}/documentos/{documento_id}/markdown", headers=AUTH_OWNER
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.text


def exigir_modelo(nome: str):
    modulo = exigir("src.app.models")
    classe = getattr(modulo, nome, None)
    if classe is None:
        pytest.fail(f"src.app.models.{nome} ainda não existe (comportamento ainda ausente)")
    return classe
