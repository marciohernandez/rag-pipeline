"""Apoio dos testes da SPEC-0043 (fase RED): indexar os `.md` de um lote sem download e upload.

Contratos assumidos pelos testes (seções 8 a 10 da SPEC-0043):

- ``POST /api/v1/envios`` e ``POST /api/v1/ingestao/previa`` aceitam os campos de formulário
  ``lote_id`` e ``documento_ids`` (campo repetido) como terceira origem, exclusiva com
  ``arquivos`` e ``usar_base_preparada`` (422). Lote fora do escopo responde 404, documento
  indisponível 409 e member 403.
- ``GET /api/v1/conversoes/{lote}`` devolve, em cada documento indexado, ``indexado`` com
  ``colecao_id``, ``colecao_nome`` e ``situacao_origem`` (``em_dia``, ``alterado`` ou ``expirado``).
- ``GET /api/v1/colecoes/{id}/documentos`` devolve ``origem`` com ``lote_id``,
  ``documento_conversao_id`` e ``situacao_origem`` nos documentos que vieram de um lote.
- Model ``OrigemDocumento`` (``documento_colecao_id``, ``lote_id``, ``documento_conversao_id``,
  ``envio_id``, ``hash_md``, ``criado_em``, ``atualizado_em``), sem coluna de texto.
- A reindexação é um ``POST /api/v1/envios`` com ``colecao_id`` e os mesmos ``documento_ids``.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests._colecoes import (
    ADMIN,
    MEMBER,
    OUTRA_EQUIPE,
    OWNER,
    Ambiente,
    documentos,
    executar_envio,
    md,
    preparar,
    texto_com_secoes,
)

__all__ = [
    "ADMIN",
    "MEMBER",
    "OUTRA_EQUIPE",
    "OWNER",
    "Ambiente",
    "alterar_markdown",
    "apagar_arquivos",
    "criar_lote_concluido",
    "documentos",
    "enviar_do_lote",
    "hash_do",
    "lote_da_api",
    "md",
    "origem_do_banco",
    "preparar",
    "previa_do_lote",
    "texto_com_secoes",
]


def hash_do(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def criar_lote_concluido(
    ambiente: Ambiente,
    conteudos: dict[str, str],
    *,
    tenant: str | None = None,
    projeto: str | None = None,
) -> tuple[str, dict[str, str]]:
    """Cria um lote concluído com um `.md` por documento; devolve (lote_id, {nome.md: id})."""
    from src.app import storage as storage_module
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao, LoteConversao, Workspace

    storage = storage_module.get_storage()
    agora = datetime.now(UTC)
    ids: dict[str, str] = {}
    with SessionLocal() as session:
        if tenant is None:
            workspace = session.get(Workspace, ambiente.workspace_id)
        else:
            workspace = Workspace(tenant_id=tenant, project_id=projeto or "p", nome="Outra equipe")
            session.add(workspace)
            session.flush()
        lote = LoteConversao(
            tenant_id=workspace.tenant_id,
            project_id=workspace.project_id,
            workspace_id=workspace.id,
            situacao="concluido",
        )
        session.add(lote)
        session.flush()
        for nome_md, texto in conteudos.items():
            stem = Path(nome_md).stem
            documento = DocumentoConversao(
                lote_id=lote.id,
                nome_arquivo=f"{stem}.pdf",
                formato="pdf",
                tamanho_bytes=len(texto),
                situacao="concluido",
                concluido_em=agora,
                expira_em=agora + timedelta(days=7),
            )
            session.add(documento)
            session.flush()
            storage.save(documento.id, nome_md, texto.encode("utf-8"))
            ids[nome_md] = documento.id
        session.commit()
        return lote.id, ids


def alterar_markdown(documento_id: str, nome_md: str, texto: str) -> None:
    from src.app import storage as storage_module

    storage_module.get_storage().save(documento_id, nome_md, texto.encode("utf-8"))


def apagar_arquivos(documento_id: str) -> None:
    """Simula a retenção de 7 dias: apaga os arquivos e grava ``apagado_em``."""
    from src.app import storage as storage_module
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao

    storage_module.get_storage().delete_base(documento_id)
    with SessionLocal() as session:
        documento = session.get(DocumentoConversao, documento_id)
        documento.apagado_em = datetime.now(UTC)
        session.commit()


def enviar_do_lote(
    ambiente: Ambiente,
    lote_id: str,
    documento_ids: list[str],
    *,
    nova: str | None = None,
    colecao_id: str | None = None,
    headers: dict[str, str] = OWNER,
    executar: bool = True,
    **extra: Any,
):
    campos: dict[str, Any] = {
        "workspace_id": ambiente.workspace_id,
        "splitter": "header",
        "chunk_size": "800",
        "chunk_overlap": "100",
        "lote_id": lote_id,
        "documento_ids": documento_ids,
    }
    if colecao_id is not None:
        campos["colecao_id"] = colecao_id
    if nova is not None:
        campos.update(
            nova_colecao=nova,
            conexao_embeddings_id=ambiente.embeddings_id,
            conexao_vector_store_id=ambiente.qdrant_id,
        )
    campos.update({chave: str(valor) for chave, valor in extra.items()})
    resposta = ambiente.client.post("/api/v1/envios", data=campos, headers=headers)
    if executar and resposta.status_code == 201:
        executar_envio(resposta.json()["envio_id"])
    return resposta


def previa_do_lote(client, lote_id: str, documento_ids: list[str], *, headers=OWNER, **extra: Any):
    campos: dict[str, Any] = {
        "lote_id": lote_id,
        "documento_ids": documento_ids,
        "splitter": "header",
        "chunk_size": "800",
        "chunk_overlap": "100",
    }
    campos.update({chave: str(valor) for chave, valor in extra.items()})
    return client.post("/api/v1/ingestao/previa", data=campos, headers=headers)


def lote_da_api(ambiente: Ambiente, lote_id: str, headers=OWNER) -> dict:
    resposta = ambiente.client.get(f"/api/v1/conversoes/{lote_id}", headers=headers)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def origem_do_banco(colecao_id: str, nome_arquivo: str):
    """Lê a ``OrigemDocumento`` do documento; reprova por comportamento ausente se o model falta."""
    from src.app import models
    from src.app.db import SessionLocal
    from src.app.models import DocumentoColecao

    modelo = getattr(models, "OrigemDocumento", None)
    if modelo is None:
        pytest.fail("OrigemDocumento ainda não existe (comportamento ainda ausente)")
    with SessionLocal() as session:
        documento = (
            session.query(DocumentoColecao)
            .filter_by(colecao_id=colecao_id, nome_arquivo=nome_arquivo)
            .one()
        )
        origem = session.query(modelo).filter_by(documento_colecao_id=documento.id).one()
        session.expunge(origem)
        return origem
