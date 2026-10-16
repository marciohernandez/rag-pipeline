"""Apoio dos testes da SPEC-0037 (fase RED).

Os módulos novos ainda não existem quando os testes são escritos. `exigir` (de
`tests/_fase1_conversao.py`) importa o módulo só no corpo do teste e reprova por
asserção quando ele falta, para que o RED seja pelo comportamento ausente e não
por erro de coleta.

Contratos assumidos pelos testes (seção 8 da SPEC-0037):

- ``src.pipeline.limpeza.contratos``: ``Exclusao(arquivo, posicao, motivo, camada,
  trecho, confianca=None, mantido_em=None)`` e ``ResultadoLimpeza(markdown, exclusoes)``.
- ``src.pipeline.limpeza.regras.aplicar_regras_fixas(markdown, arquivo) -> ResultadoLimpeza``.
- ``src.pipeline.limpeza.avaliacao_ia.AvaliadorIa(modelo, limiar=0.8,
  max_chars_por_requisicao=4000).avaliar(secoes, dominio) -> list[SecaoAvaliada]``
  com ``decisao`` em ``remover``, ``manter`` ou ``duvida`` e ``confianca``. O modelo
  (``ChatModelAdapter``) recebe as seções no prompt como ``### SECAO <i>`` seguido do
  texto, e responde um JSON ``[{"indice": i, "classe": "ruido"|"negocio",
  "confianca": 0..1}]``.
- ``src.pipeline.limpeza.duplicidade.deduplicar(documentos, minimo_caracteres=200,
  limiar=0.95, limiar_provavel=0.8) -> ResultadoDuplicidade`` com ``documentos``
  (arquivo -> markdown), ``exclusoes`` e ``provaveis`` (pares com ``arquivo_a``,
  ``arquivo_b``).
- ``src.app.limpeza``: ``preparar_limpeza_do_lote(lote_id)``, ``limpar_documento(
  documento_id)``, ``finalizar_limpeza_lote(lote_id)``, ``purgar_retencao(agora)``,
  ``criar_modelo_ia(session, workspace)`` e ``enfileirar_limpeza(documento_id)``.
- ``src.app.models``: ``DominioWorkspace``, ``ExclusaoLimpeza``, ``RelatorioLote``.
- Rotas: ``GET|PUT /api/v1/workspaces/{id}/dominio``, ``GET .../dominio/versoes``,
  ``PATCH .../analise-ia``, ``GET /conversoes/{lote}/dominio-proposto``,
  ``POST .../dominio/confirmar``, ``POST .../documentos/{doc}/limpar``,
  ``GET .../relatorio`` e ``GET .../exclusoes``.
"""

from __future__ import annotations

import json
import re
from types import SimpleNamespace

import pytest

from tests._fase1_conversao import (  # noqa: F401 — reexportados para os testes
    AUTH_MEMBER,
    AUTH_OWNER,
    armazenamento_temporario,
    cliente,
    exigir,
    sem_enfileirar,
)

DOMINIO = "A empresa vende planos de assinatura de software de gestão para pequenas empresas."
CHAVE_IA = "sk-spec0037-chave-da-ia-3d9f"


def modelo_orm(nome: str):
    modulo = exigir("src.app.models")
    classe = getattr(modulo, nome, None)
    if classe is None:
        pytest.fail(f"src.app.models.{nome} ainda não existe (comportamento ainda ausente)")
    return classe


class EspiaoIa:
    """``ChatModelAdapter`` falso: registra as chamadas e classifica seções por trecho."""

    def __init__(self, classificacao=None, texto=None, erro=None):
        self.classificacao = classificacao or {}
        self.texto = texto
        self.erro = erro
        self.mensagens: list[str] = []

    def responder(self, mensagens, timeout=None) -> str:
        conteudo = "\n".join(getattr(m, "conteudo", str(m)) for m in mensagens)
        self.mensagens.append(conteudo)
        if self.erro:
            raise self.erro
        if self.texto is not None:
            return self.texto
        itens = []
        for indice, corpo in re.findall(
            r"### SECAO (\d+)\n(.*?)(?=\n### SECAO |\Z)", conteudo, re.DOTALL
        ):
            classe, confianca = "negocio", 0.99
            for trecho, (c, f) in self.classificacao.items():
                if trecho in corpo:
                    classe, confianca = c, f
            itens.append({"indice": int(indice), "classe": classe, "confianca": confianca})
        return json.dumps(itens)

    @property
    def chamadas(self) -> int:
        return len(self.mensagens)


def criar_workspace(c) -> str:
    resposta = c.post(
        "/api/v1/workspaces", json={"nome": "Limpeza de documentos"}, headers=AUTH_OWNER
    )
    assert resposta.status_code == 201
    return resposta.json()["id"]


def preparar_lote(tmp_path, monkeypatch, markdowns: dict[str, str], *, ia=False):
    """Envia um lote pela API, marca os documentos como convertidos e grava os `.md`.

    Devolve ``SimpleNamespace(c, workspace_id, lote_id, docs)`` com ``docs`` mapeando o
    nome do `.md` (por exemplo ``a.md``) para o id do documento.
    """
    from src.app import storage as storage_module
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao, Workspace

    c = cliente(tmp_path, monkeypatch)
    sem_enfileirar(monkeypatch)
    workspace_id = criar_workspace(c)
    resposta = c.post(
        "/api/v1/conversoes",
        data={"workspace_id": workspace_id},
        files=[
            ("arquivos", (nome.replace(".md", ".pdf"), b"%PDF-1.4", "application/pdf"))
            for nome in markdowns
        ],
        headers=AUTH_OWNER,
    )
    assert resposta.status_code == 201, resposta.text
    lote = resposta.json()
    storage = storage_module.get_storage()
    docs: dict[str, str] = {}
    with SessionLocal() as session:
        for documento in lote["documentos"]:
            nome_md = documento["nome_arquivo"].replace(".pdf", ".md")
            registro = session.get(DocumentoConversao, documento["id"])
            registro.situacao = "concluido"
            storage.save(registro.id, nome_md, markdowns[nome_md].encode("utf-8"))
            docs[nome_md] = registro.id
        if ia:
            workspace = session.get(Workspace, workspace_id)
            workspace.ia_externa_permitida = True
        session.commit()
    return SimpleNamespace(c=c, workspace_id=workspace_id, lote_id=lote["id"], docs=docs)


def definir_dominio(ctx, texto: str = DOMINIO, headers=AUTH_OWNER):
    return ctx.c.put(
        f"/api/v1/workspaces/{ctx.workspace_id}/dominio", json={"texto": texto}, headers=headers
    )


def ler_md(documento_id: str, nome_md: str, tmp) -> str:
    from src.app import storage as storage_module

    pasta = tmp / f"limpo-{documento_id}"
    storage_module.get_storage().materialize(documento_id, pasta)
    return (pasta / nome_md).read_text(encoding="utf-8")


def linhas(markdown: str) -> list[str]:
    return [linha.strip() for linha in markdown.splitlines()]
