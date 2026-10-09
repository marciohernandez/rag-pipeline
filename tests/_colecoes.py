"""Apoio dos testes da SPEC-0030: coleções por Workspace e envios acumulados.

Fase RED: o código de produção ainda não existe. Os casos exercitam a API HTTP da
seção 10 da spec e o worker ``process_envio_task`` (importado só ao ser usado por
:func:`recurso`, que reprova o teste por comportamento ausente). Nenhum caso toca
rede: embeddings e vector store são dublados na fronteira de
``src.pipeline.indexing`` e o storage é um diretório temporário.

Contrato de ``POST /api/v1/envios`` assumido pelos testes (multipart):
``workspace_id``; ``colecao_id`` (coleção existente) ou ``nova_colecao`` (nome) com
``conexao_embeddings_id`` e ``conexao_vector_store_id``; ``arquivos``; e a divisão
(``splitter``, ``chunk_size``, ``chunk_overlap``, ``processamento``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.pipeline.providers.contracts import SearchResult, VectorRecord
from src.pipeline.providers.vectorstores.base import BaseVectorStoreAdapter, MirrorMixin
from tests._conexoes import (
    ADMIN,
    CHAVE_EMBEDDINGS,
    CHAVE_QDRANT,
    MEMBER,
    OUTRA_EQUIPE,
    OWNER,
    cliente,
    criar_conexao_ok,
    criar_workspace,
    payload_embeddings,
    payload_qdrant,
    storage_temporario,
)
from tests._pessoas import recurso, sessao_do_banco

__all__ = [
    "ADMIN",
    "CHAVE_EMBEDDINGS",
    "CHAVE_QDRANT",
    "MEMBER",
    "OUTRA_EQUIPE",
    "OWNER",
    "Ambiente",
    "colecao_do_banco",
    "criar_colecao",
    "criar_conexoes_e_colecao",
    "documentos",
    "enviar",
    "executar_envio",
    "md",
    "preparar",
    "texto_com_secoes",
]


class ArmazemFalso:
    """Vector store em memória que respeita o escopo de coleção e de documento."""

    def __init__(self) -> None:
        self.registros: dict[str, dict[str, VectorRecord]] = {}
        self.falhar_escrita = False

    @staticmethod
    def _projeto(escopo) -> str:
        return escopo.project_id

    def _do_escopo(self, escopo) -> dict[str, VectorRecord]:
        doc = getattr(escopo, "document_id", None)
        todos = self.registros.get(self._projeto(escopo), {})
        if doc is None:
            return todos
        return {k: v for k, v in todos.items() if v.metadata.get("document_id") == doc}

    # backend port ----------------------------------------------------------
    def ensure(self, escopo, dimensions: int) -> None:
        self.registros.setdefault(self._projeto(escopo), {})

    def describe(self, escopo) -> dict:
        if self._projeto(escopo) not in self.registros:
            return {}
        return {"exists": True, "dimensions": 8}

    def scope_ids(self, escopo) -> set[str]:
        return set(self._do_escopo(escopo))

    def write(self, escopo, registros: Sequence[VectorRecord]) -> None:
        if registros and self.falhar_escrita:
            raise RuntimeError(f"qdrant recusou a gravação ({CHAVE_QDRANT})")
        balde = self.registros.setdefault(self._projeto(escopo), {})
        for registro in registros:
            balde[registro.id] = registro

    def remove(self, escopo, ids: Iterable[str]) -> None:
        balde = self.registros.get(self._projeto(escopo), {})
        for identificador in ids:
            balde.pop(identificador, None)

    def search(self, escopo, embedding, k: int) -> list[SearchResult]:
        return [
            SearchResult(content=r.content, metadata=r.metadata, score=1.0)
            for r in list(self._do_escopo(escopo).values())[: max(k, 0)]
        ]

    def scope_records(self, escopo, limite: int) -> list[SearchResult]:
        return self.search(escopo, [], limite)

    # observação ------------------------------------------------------------
    def todos(self) -> list[VectorRecord]:
        return [r for balde in self.registros.values() for r in balde.values()]

    def do_arquivo(self, nome_arquivo: str) -> list[VectorRecord]:
        return [r for r in self.todos() if r.metadata.get("nome_arquivo") == nome_arquivo]


class AdaptadorFalso(MirrorMixin, BaseVectorStoreAdapter):
    provider = "qdrant"


class EmbeddingsFalso:
    def __init__(self) -> None:
        self.textos: list[str] = []

    def embed_documents(self, textos: list[str]) -> list[list[float]]:
        self.textos.extend(textos)
        return [[1.0] * 8 for _ in textos]

    def embed_query(self, texto: str) -> list[float]:
        return [1.0] * 8


@dataclass
class Ambiente:
    client: TestClient
    workspace_id: str
    embeddings_id: str
    qdrant_id: str
    armazem: ArmazemFalso
    embeddings: EmbeddingsFalso
    pasta: Path
    agendamentos: list[dict[str, Any]] = field(default_factory=list)
    locks: list[str | None] = field(default_factory=list)
    colecoes_fisicas: set[str] = field(default_factory=set)


def preparar(tmp_path, monkeypatch) -> Ambiente:
    """Workspace, conexões ativas, storage temporário e dublês de embeddings e Qdrant."""
    pasta = storage_temporario(tmp_path, monkeypatch)
    client = cliente()
    armazem = ArmazemFalso()
    embeddings = EmbeddingsFalso()
    adaptador = AdaptadorFalso(client=armazem)
    monkeypatch.setattr("src.pipeline.indexing.build_embeddings", lambda cfg: embeddings)
    colecoes_fisicas: set[str] = set()

    def construir_destino(cfg, persist_dir=None):
        colecoes_fisicas.add(str(cfg.get("collection_name", "")))
        return adaptador

    monkeypatch.setattr("src.pipeline.indexing.build_vector_store", construir_destino)
    monkeypatch.setattr(
        "src.pipeline.service.describe_collection",
        lambda *args, **kwargs: {"exists": False, "dimensions": None},
        raising=False,
    )
    ambiente = Ambiente(
        client=client,
        workspace_id=criar_workspace(client),
        embeddings_id=criar_conexao_ok(client, payload_embeddings())["id"],
        qdrant_id=criar_conexao_ok(client, payload_qdrant())["id"],
        armazem=armazem,
        embeddings=embeddings,
        pasta=pasta,
        colecoes_fisicas=colecoes_fisicas,
    )
    from src.app import tasks

    tarefa = getattr(tasks, "process_envio_task", None)
    if tarefa is not None:

        class _Agendador:
            def __init__(self, **opcoes: Any) -> None:
                self.opcoes = opcoes

            def defer(self, **kwargs: Any) -> None:
                ambiente.agendamentos.append(kwargs)
                ambiente.locks.append(self.opcoes.get("lock"))

        monkeypatch.setattr(tarefa, "configure", lambda **opcoes: _Agendador(**opcoes))
    return ambiente


def md(nome: str, texto: str) -> tuple[str, tuple[str, bytes, str]]:
    return ("arquivos", (nome, texto.encode(), "text/markdown"))


def texto_com_secoes(quantidade: int, marca: str = "v1") -> str:
    """Markdown com uma seção `##` por chunk esperado na divisão por cabeçalho."""
    corpo = "".join(
        f"## Seção {i}\n\nTexto {marca} da seção {i} do documento.\n\n"
        for i in range(1, quantidade + 1)
    )
    return f"# Documento\n\n{corpo}"


def enviar(
    ambiente: Ambiente,
    arquivos: list,
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
    resposta = ambiente.client.post("/api/v1/envios", data=campos, files=arquivos, headers=headers)
    if executar and resposta.status_code == 201:
        executar_envio(resposta.json()["envio_id"])
    return resposta


def executar_envio(envio_id: str) -> None:
    """Roda o worker do envio, como o Procrastinate faria."""
    tarefa = recurso("src.app.tasks", "process_envio_task")
    tarefa.func(envio_id)


def criar_colecao(ambiente: Ambiente, nome: str = "manuais", arquivos: list | None = None) -> str:
    """Cria a coleção pelo primeiro envio e devolve o `colecao_id`."""
    resposta = enviar(
        ambiente, arquivos if arquivos is not None else [md("a.md", texto_com_secoes(3))], nova=nome
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["colecao_id"]


def documentos(ambiente: Ambiente, colecao_id: str, headers=OWNER) -> list[dict]:
    resposta = ambiente.client.get(f"/api/v1/colecoes/{colecao_id}/documentos", headers=headers)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def colecao_do_banco(colecao_id: str) -> Any:
    modelo = recurso("src.app.models", "Colecao")
    with sessao_do_banco() as sessao:
        linha = sessao.get(modelo, colecao_id)
        assert linha is not None
        sessao.expunge(linha)
        return linha


def sem_chave(*textos: str) -> Callable[[], bool]:
    return lambda: (
        not any(chave in texto for texto in textos for chave in (CHAVE_QDRANT, CHAVE_EMBEDDINGS))
    )


def criar_conexoes_e_colecao(nome: str = "manuais") -> str:
    """Grava conexões, coleção e um envio na fila direto no banco; devolve o `envio_id`."""
    from src.app.models import Colecao, Envio, Workspace

    client = cliente()
    embeddings = criar_conexao_ok(client, payload_embeddings())
    qdrant = criar_conexao_ok(client, payload_qdrant())
    with sessao_do_banco() as sessao:
        workspace = Workspace(tenant_id="tenant-1", project_id="projeto-1", nome="WS envio")
        sessao.add(workspace)
        sessao.flush()
        colecao = Colecao(
            tenant_id="tenant-1",
            project_id="projeto-1",
            workspace_id=workspace.id,
            nome=nome,
            nome_normalizado=nome.casefold(),
            nome_fisico="col-teste-0001",
            conexao_embeddings_id=embeddings["id"],
            conexao_vector_store_id=qdrant["id"],
            dimensao=1536,
        )
        sessao.add(colecao)
        sessao.flush()
        envio = Envio(colecao_id=colecao.id, arquivos=["a.md"], processamento={}, situacao="queued")
        sessao.add(envio)
        sessao.commit()
        return envio.id
