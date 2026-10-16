"""Apoio dos testes da SPEC-0038 (fase RED).

Os módulos novos ainda não existem quando os testes são escritos. ``exigir`` (de
``tests/_fase1_conversao.py``) importa o módulo só no corpo do teste e reprova por
asserção quando ele falta, para que o RED seja pelo comportamento ausente.

Contratos assumidos pelos testes (seção 8 da SPEC-0038):

- ``src.pipeline.contradicoes.contratos``: ``Afirmacao(arquivo, assunto, texto,
  impacto="baixo", imagem=None)`` e ``Ocorrencia(assunto, etiqueta, impacto, trechos,
  explicacao, arquivo_mais_antigo=None)``; ``trechos`` é lista de objetos com ``arquivo``,
  ``texto`` e ``imagem``. Etiquetas: ``conflito``, ``versao_desatualizada``, ``duplicado``.
- ``src.pipeline.contradicoes.assuntos``: ``normalizar_assunto(texto) -> str`` (caixa,
  acentos, pontuação, palavras de ligação e ordem) e ``planejar_julgamentos(afirmacoes,
  maximo_por_julgamento=20) -> list`` com ``assunto`` e ``afirmacoes`` por item; assunto
  com uma única afirmação não gera julgamento.
- ``src.pipeline.contradicoes.julgamento.julgar_assunto(modelo, assunto, afirmacoes) ->
  list[Ocorrencia]``. O modelo (``ChatModelAdapter``) recebe ``### ASSUNTO <assunto>`` e
  ``### AFIRMACAO <i> (<arquivo>)`` seguido do texto, e responde um JSON
  ``[{"etiqueta", "indices", "explicacao", "mais_antigo"}]``.
- A extração envia ``### DOCUMENTO <arquivo>`` seguido do texto e recebe
  ``[{"assunto", "texto", "impacto"}]``.
- ``src.pipeline.contradicoes.relatorio``: ``montar_markdown(analise, ocorrencias)`` e
  ``montar_pdf(analise, ocorrencias) -> bytes``.
- ``src.app.contradicoes``: ``criar_modelo_ia(session, workspace)`` e
  ``purgar_retencao(agora)``; tarefa ``src.app.tasks.analisar_contradicoes_task``.
- ``src.app.models``: ``AnaliseContradicao`` e ``OcorrenciaContradicao``.
- Rotas: ``POST /api/v1/colecoes/{id}/contradicoes/analises`` (corpo ``{"confirmado":
  true}``, 202), ``POST .../analises/{aid}/continuar`` (202), ``GET
  /api/v1/colecoes/{id}/contradicoes`` (``?etiqueta=``) e ``GET
  .../contradicoes/relatorio?formato=md|pdf``.
- ``GET .../contradicoes`` devolve ``{"analise": {...}|null, "ocorrencias": [...],
  "nao_classificadas": n}`` com ``analise`` contendo ``id``, ``situacao``, ``motivo``,
  ``provedor``, ``dominio_versao_id``, ``total_assuntos``, ``concluidos`` e
  ``documentos_analisados``.
"""

from __future__ import annotations

import json
import re
from types import SimpleNamespace

import pytest

from tests._colecoes import MEMBER, OWNER, criar_colecao, md, preparar
from tests._conexoes import criar_conexao_ok
from tests._fase1_conversao import exigir

__all__ = [
    "ADMIN_HEADERS",
    "MEMBER",
    "OWNER",
    "IaContradicoes",
    "analisar",
    "exigir",
    "modelo_orm",
    "montar",
    "montar_vazia",
    "relatorio",
    "rodar_fila",
]

ADMIN_HEADERS = {"Authorization": "Bearer pessoa-teste-admin"}
CHAVE_IA = "sk-spec0038-chave-da-ia-7c1e"


def modelo_orm(nome: str):
    modulo = exigir("src.app.models")
    classe = getattr(modulo, nome, None)
    if classe is None:
        pytest.fail(f"src.app.models.{nome} ainda não existe (comportamento ainda ausente)")
    return classe


class IaContradicoes:
    """``ChatModelAdapter`` falso que extrai e julga conforme um roteiro.

    ``extracao``: arquivo -> lista de ``(assunto, texto)`` (ou ``(assunto, texto, impacto)``).
    ``veredito``: trecho do assunto normalizado -> ``(etiqueta, explicacao)``.
    ``cair_apos``: número de julgamentos que funcionam antes de a IA ficar indisponível.
    """

    def __init__(self, extracao=None, veredito=None, cair_apos=None, indisponivel=False):
        self.extracao = extracao or {}
        self.veredito = veredito or {}
        self.cair_apos = cair_apos
        self.indisponivel = indisponivel
        self.prompts_extracao: list[str] = []
        self.julgados: list[str] = []
        self.prompts_julgamento: list[str] = []

    @property
    def chamadas(self) -> int:
        return len(self.prompts_extracao) + len(self.prompts_julgamento)

    def responder(self, mensagens, timeout=None) -> str:
        conteudo = "\n".join(getattr(m, "conteudo", str(m)) for m in mensagens)
        if self.indisponivel:
            raise ConnectionError("provedor de IA indisponível")
        if "### ASSUNTO" in conteudo:
            return self._julgar(conteudo)
        return self._extrair(conteudo)

    def _extrair(self, conteudo: str) -> str:
        self.prompts_extracao.append(conteudo)
        itens = []
        for arquivo in re.findall(r"### DOCUMENTO (\S+)", conteudo):
            for item in self.extracao.get(arquivo, []):
                assunto, texto, *resto = item
                itens.append(
                    {
                        "arquivo": arquivo,
                        "assunto": assunto,
                        "texto": texto,
                        "impacto": resto[0] if resto else "baixo",
                    }
                )
        return json.dumps(itens)

    def _julgar(self, conteudo: str) -> str:
        self.prompts_julgamento.append(conteudo)
        if self.cair_apos is not None and len(self.julgados) >= self.cair_apos:
            raise ConnectionError("provedor de IA indisponível")
        assunto = re.search(r"### ASSUNTO (.+)", conteudo).group(1).strip()
        indices = [int(i) for i in re.findall(r"### AFIRMACAO (\d+)", conteudo)]
        self.julgados.append(assunto)
        for trecho, (etiqueta, explicacao) in self.veredito.items():
            if trecho in assunto:
                return json.dumps(
                    [
                        {
                            "etiqueta": etiqueta,
                            "indices": indices,
                            "explicacao": explicacao,
                            "mais_antigo": indices[0]
                            if etiqueta == "versao_desatualizada"
                            else None,
                        }
                    ]
                )
        return "[]"


def _ligar_ia(amb, monkeypatch, modelo, *, ia_externa=True):
    contradicoes = exigir("src.app.contradicoes")
    monkeypatch.setattr(contradicoes, "criar_modelo_ia", lambda session, workspace: modelo)
    conexao = criar_conexao_ok(
        amb.client,
        {
            "nome": "IA de análise",
            "tipo": "ia_analise",
            "configuracao": {
                "modelo": "modelo-de-analise",
                "url_base": "https://api.exemplo.com/v1",
            },
            "segredo": CHAVE_IA,
        },
    )
    resposta = amb.client.patch(
        f"/api/v1/workspaces/{amb.workspace_id}/analise-ia",
        json={"ia_externa_permitida": ia_externa, "conexao_ia_id": conexao["id"]},
        headers=OWNER,
    )
    assert resposta.status_code == 200, resposta.text


def montar(tmp_path, monkeypatch, arquivos: dict[str, str], modelo, *, ia_externa=True):
    """Coleção com os ``arquivos`` enviados, IA simulada e fila de análise capturada."""
    amb = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(amb, "politicas", [md(n, t) for n, t in arquivos.items()])
    _ligar_ia(amb, monkeypatch, modelo, ia_externa=ia_externa)
    fila: list[dict] = []
    tasks = exigir("src.app.tasks")
    tarefa = getattr(tasks, "analisar_contradicoes_task", None)
    if tarefa is None:
        pytest.fail("src.app.tasks.analisar_contradicoes_task ainda não existe")
    monkeypatch.setattr(tarefa, "defer", lambda **kw: fila.append(kw))
    return SimpleNamespace(
        amb=amb,
        c=amb.client,
        colecao_id=colecao_id,
        workspace_id=amb.workspace_id,
        modelo=modelo,
        fila=fila,
        tarefa=tarefa,
    )


def montar_vazia(tmp_path, monkeypatch, modelo):
    """Coleção cujos documentos foram removidos (sem nada a analisar)."""
    from src.app.db import SessionLocal
    from src.app.models import ConteudoDocumento, DocumentoColecao

    ctx = montar(tmp_path, monkeypatch, {"a.md": "# A\n\nTexto.\n"}, modelo)
    with SessionLocal() as session:
        docs = session.query(DocumentoColecao).filter_by(colecao_id=ctx.colecao_id).all()
        for doc in docs:
            session.query(ConteudoDocumento).filter_by(documento_id=doc.id).delete()
            session.delete(doc)
        session.commit()
    return ctx


def analisar(ctx, headers=OWNER, confirmado=True):
    return ctx.c.post(
        f"/api/v1/colecoes/{ctx.colecao_id}/contradicoes/analises",
        json={"confirmado": confirmado},
        headers=headers,
    )


def rodar_fila(ctx, maximo: int = 200) -> int:
    """Executa os jobs enfileirados, como o worker faria, e devolve quantos rodaram."""
    rodados = 0
    while ctx.fila and rodados < maximo:
        ctx.tarefa.func(**ctx.fila.pop(0))
        rodados += 1
    return rodados


def relatorio(ctx, headers=OWNER, etiqueta: str | None = None) -> dict:
    sufixo = f"?etiqueta={etiqueta}" if etiqueta else ""
    resposta = ctx.c.get(f"/api/v1/colecoes/{ctx.colecao_id}/contradicoes{sufixo}", headers=headers)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()
