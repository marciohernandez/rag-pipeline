"""Apoio dos testes da SPEC-0039 (fase RED).

Os módulos novos ainda não existem quando os testes são escritos; ``exigir`` importa o módulo
só no corpo do teste e reprova por asserção quando ele falta.

Contratos assumidos pelos testes (seções 8 a 10 da SPEC-0039):

- ``src.pipeline.decisoes.interpretacao.interpretar_resposta(modelo, resposta, ocorrencias,
  documentos) -> list[Proposta]``. ``ocorrencias`` é uma lista de dicionários com ``id``,
  ``assunto`` e ``trechos`` (``arquivo`` e ``texto``); ``documentos`` mapeia arquivo →
  Markdown. O modelo (``ChatModelAdapter``) recebe ``### RESPOSTA`` seguido do texto e
  ``### OCORRENCIA <i>`` (``i`` a partir de 1, na ordem da lista) com os trechos, e responde
  um JSON ``[{"ocorrencia": i, "arquivo", "trecho_alvo", "texto_corrigido", "confianca":
  "clara"|"incerta"}]``; cada bloco ``### OCORRENCIA <i>`` traz o assunto em uma linha própria
  seguido dos trechos. A saída tem uma ``Proposta`` por ocorrência, com ``ocorrencia_id``,
  ``situacao`` (``clara``, ``incerta`` ou ``sem_decisao``), ``arquivo``, ``trecho_alvo``,
  ``texto_corrigido`` e ``motivo``.
- ``src.pipeline.decisoes.localizacao.localizar_trecho(markdown, trecho, limiar=0.9)`` devolve
  ``None`` (ausente ou ambíguo) ou um objeto com ``inicio``, ``fim`` e ``exata``.
- ``src.pipeline.decisoes.aplicacao.aplicar_correcao(markdown, trecho_alvo, texto_corrigido)
  -> str`` troca só o trecho alvo; ``ValueError`` quando ele não é localizado.
- ``src.app.decisoes``: ``criar_modelo_ia(session, workspace)``, ``purgar_retencao(agora)`` e
  ``apagar_da_colecao(session, colecao_id, apagado_por=None)``; tarefa
  ``src.app.tasks.interpretar_resposta_task``.
- ``src.app.models``: ``RespostaEmpresa``, ``PropostaCorrecao``, ``DecisaoEmpresa``,
  ``VersaoDocumento`` e ``RegistroExclusaoDecisoes`` (``colecao_id``, ``apagado_por``,
  ``apagado_em``, ``decisoes``); ``Colecao.revisada_em`` e ``Colecao.revisada_por``.
- Rotas (sob ``/api/v1/colecoes/{id}``): ``POST /decisoes/respostas`` (``{"texto",
  "confirmado"}``, 202), ``GET /decisoes/propostas`` (``{"resposta", "propostas"}``),
  ``POST /decisoes/propostas/confirmar`` (``{"confirmado": true}`` → ``{"aplicadas": n}``),
  ``POST /decisoes/propostas/{pid}/decisao`` (``{"acao": "aceitar"|"editar"|"manter",
  "texto_corrigido"?}``), ``GET /decisoes/registro``, ``GET /decisoes/rodada`` (``resolvidas``,
  ``novas``, ``abertas``), ``GET /documentos/{documento_id}/versoes``, ``POST
  /documentos/{documento_id}/versoes/{numero}/restaurar`` (``{"confirmado": true}``) e
  ``POST /revisar`` (``{"confirmado"}`` → ``{"revisada_em", "revisada_por", "abertas"}``;
  409 com ``abertas`` quando há contradições abertas e não houve confirmação).
"""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path

import pytest

from tests._colecoes import colecao_do_banco, executar_envio
from tests._fase1_contradicoes import (
    ADMIN_HEADERS,
    MEMBER,
    OWNER,
    IaContradicoes,
    analisar,
    exigir,
    modelo_orm,
    montar,
    rodar_fila,
)

__all__ = [
    "ADMIN_HEADERS",
    "COMERCIAL",
    "CORRECAO",
    "MARKETING",
    "MEMBER",
    "OWNER",
    "RESPOSTA",
    "TRECHO_MARKETING",
    "IaDecisoes",
    "colar",
    "colecao_do_banco",
    "exigir",
    "hash_de",
    "interpretar",
    "ler_md",
    "modelo_orm",
    "montar_ciclo",
    "proposta_clara",
    "propostas",
    "publicar",
    "rodar_interpretacao",
    "url",
]

COMERCIAL = "# Comercial\n\nO cancelamento pode ser feito em até 7 dias.\n"
MARKETING = "# Marketing\n\nO cancelamento pode ser feito em até 15 dias.\n"
RESPOSTA = "Vale o prazo de 7 dias para cancelar; o material de marketing está errado."
TRECHO_MARKETING = "O cancelamento pode ser feito em até 15 dias."
CORRECAO = "O cancelamento pode ser feito em até 7 dias."


class IaDecisoes:
    """``ChatModelAdapter`` falso da interpretação da resposta.

    ``roteiro``: trecho que identifica a ocorrência (no bloco ``### OCORRENCIA``) → proposta
    ``{"arquivo", "trecho_alvo", "texto_corrigido", "confianca"}`` ou ``None`` (não coberta).
    """

    def __init__(self, roteiro=None, indisponivel=False):
        self.roteiro = roteiro or {}
        self.indisponivel = indisponivel
        self.prompts: list[str] = []

    @property
    def chamadas(self) -> int:
        return len(self.prompts)

    def responder(self, mensagens, timeout=None) -> str:
        conteudo = "\n".join(getattr(m, "conteudo", str(m)) for m in mensagens)
        self.prompts.append(conteudo)
        if self.indisponivel:
            raise ConnectionError("provedor de IA indisponível")
        itens = []
        for indice, corpo in re.findall(
            r"### OCORRENCIA (\d+)\n(.*?)(?=\n### OCORRENCIA |\Z)", conteudo, re.DOTALL
        ):
            for chave, proposta in self.roteiro.items():
                if chave in corpo and proposta is not None:
                    itens.append({"ocorrencia": int(indice), **proposta})
        return json.dumps(itens)


def proposta_clara(arquivo="marketing.md", trecho=TRECHO_MARKETING, corrigido=CORRECAO):
    return {
        "arquivo": arquivo,
        "trecho_alvo": trecho,
        "texto_corrigido": corrigido,
        "confianca": "clara",
    }


def hash_de(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def ler_md(ctx, nome: str) -> str:
    """Texto atual do documento na coleção, como o worker de envio o guardou."""
    from src.app.db import SessionLocal
    from src.app.models import DocumentoColecao
    from src.app.storage import get_storage

    with SessionLocal() as session:
        doc = (
            session.query(DocumentoColecao)
            .filter_by(colecao_id=ctx.colecao_id, nome_arquivo=nome)
            .one()
        )
        envio_id = doc.ultimo_envio_id
    with tempfile.TemporaryDirectory(prefix="decisoes-teste-") as pasta:
        get_storage().materialize(envio_id, pasta)
        return (Path(pasta) / nome).read_text(encoding="utf-8")


def montar_ciclo(
    tmp_path,
    monkeypatch,
    roteiro,
    *,
    arquivos=None,
    extracao=None,
    veredito=None,
    indisponivel=False,
):
    """Coleção já analisada (com contradições) e a IA de interpretação simulada."""
    arquivos = arquivos or {"comercial.md": COMERCIAL, "marketing.md": MARKETING}
    contradicoes = IaContradicoes(
        extracao=extracao
        or {
            "comercial.md": [("cancelamento prazo", "Cancelamento em até 7 dias.", "alto")],
            "marketing.md": [("prazo de cancelamento", "Cancelamento em até 15 dias.", "alto")],
        },
        veredito=veredito or {"cancelamento": ("conflito", "Os prazos divergem.")},
    )
    ctx = montar(tmp_path, monkeypatch, arquivos, contradicoes)
    assert analisar(ctx).status_code == 202
    rodar_fila(ctx)

    decisoes = exigir("src.app.decisoes")
    modelo = IaDecisoes(roteiro, indisponivel=indisponivel)
    monkeypatch.setattr(decisoes, "criar_modelo_ia", lambda session, workspace: modelo)
    tasks = exigir("src.app.tasks")
    tarefa = getattr(tasks, "interpretar_resposta_task", None)
    if tarefa is None:
        pytest.fail("src.app.tasks.interpretar_resposta_task ainda não existe")
    fila: list[dict] = []
    monkeypatch.setattr(tarefa, "defer", lambda **kw: fila.append(kw))
    ctx.modelo_decisoes = modelo
    ctx.fila_decisoes = fila
    ctx.tarefa_decisoes = tarefa
    ctx.contradicoes = contradicoes
    ctx.envios_consumidos = len(ctx.amb.agendamentos)
    return ctx


def url(ctx, caminho: str) -> str:
    return f"/api/v1/colecoes/{ctx.colecao_id}{caminho}"


def colar(ctx, texto=RESPOSTA, confirmado=True, headers=OWNER):
    return ctx.c.post(
        url(ctx, "/decisoes/respostas"),
        json={"texto": texto, "confirmado": confirmado},
        headers=headers,
    )


def rodar_interpretacao(ctx) -> int:
    rodados = 0
    while ctx.fila_decisoes:
        ctx.tarefa_decisoes.func(**ctx.fila_decisoes.pop(0))
        rodados += 1
    return rodados


def propostas(ctx, headers=OWNER) -> dict:
    resposta = ctx.c.get(url(ctx, "/decisoes/propostas"), headers=headers)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def interpretar(ctx, texto=RESPOSTA, headers=OWNER) -> list[dict]:
    """Cola a resposta, roda a fila e devolve as propostas."""
    resposta = colar(ctx, texto, headers=headers)
    assert resposta.status_code == 202, resposta.text
    rodar_interpretacao(ctx)
    return propostas(ctx, headers)["propostas"]


def publicar(ctx) -> int:
    """Executa os envios agendados pelas correções, como o worker faria."""
    pendentes = ctx.amb.agendamentos[ctx.envios_consumidos :]
    for agendamento in pendentes:
        executar_envio(agendamento["envio_id"])
    ctx.envios_consumidos = len(ctx.amb.agendamentos)
    return len(pendentes)
