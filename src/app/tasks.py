"""Tarefa assíncrona de processamento de uma base (SPEC-0012, seção 8).

Usa Procrastinate sobre o mesmo PostgreSQL da aplicação. O app nasce com
``InMemoryConnector`` (nenhuma fila real antes de configurado); o entrypoint
(``src/app/main.py``) chama ``configure_connector`` com um
``procrastinate.PsycopgConnector`` real assim que a aplicação sobe — inclusive
em teste, contra o Postgres de teste isolado, para que um worker fora do
processo consuma a mesma fila que a API agenda.

``configure_connector`` precisa reatribuir **os dois** ponteiros de connector
do ``App``: ``app.connector`` e ``app.job_manager.connector``. ``task.defer()``
roteia pelo ``job_manager``; trocar só ``app.connector`` faz todo agendamento
cair no ``InMemoryConnector`` de placeholder — o job nunca chega ao Postgres e
nenhum worker externo o consome (SPEC-0012, Fase 9, T044–T048).
"""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import procrastinate
from langchain_core.documents import Document
from procrastinate import testing as procrastinate_testing
from procrastinate.connector import BaseConnector

from src.app.storage import Storage

app = procrastinate.App(connector=procrastinate_testing.InMemoryConnector())


def configure_connector(connector: BaseConnector) -> None:
    """Troca o conector do app Procrastinate e o abre (chamado uma vez no entrypoint).

    Reatribui ``app.connector`` **e** ``app.job_manager.connector`` — este último
    é o que ``task.defer()`` usa. É o que o próprio ``App.replace_connector`` do
    procrastinate faz; aqui a troca é permanente, não escopada a um ``with``.
    """
    app.connector = connector
    app.job_manager.connector = connector
    app.open()


def _agora() -> datetime:
    return datetime.now(UTC)


@app.periodic(cron="0 3 * * *")
@app.task(name="purgar_dados_de_acesso_task")
def purgar_dados_de_acesso_task(_timestamp: int) -> None:
    """Remove diariamente somente sessões, bloqueios e eventos expirados."""
    from src.app.db import SessionLocal
    from src.app.events import purgar_dados_de_acesso, purgar_eventos_conexao

    with SessionLocal() as session:
        contagens = purgar_dados_de_acesso(session)
        eventos_conexao = purgar_eventos_conexao(session)
    logging.getLogger(__name__).info(
        "limpeza de acesso concluída: eventos=%d sessões=%d tentativas=%d eventos_conexao=%d",
        contagens["eventos"],
        contagens["sessoes"],
        contagens["tentativas"],
        eventos_conexao,
    )


def _registrar_falha(execution_id: str, etapa: str, erro: BaseException) -> None:
    """Registra a causa técnica de uma execução que falhou (FR-010).

    A mensagem da exceção fica de fora de propósito: psycopg, boto3 e o cliente
    Qdrant costumam embutir DSN, endpoint ou chave nela, e NFR-002 proíbe
    credencial em log. O que vai para o log é o que diagnostica sem identificar
    segredo — tipo da exceção, etapa alcançada e origem no código — enquanto o
    ``erro`` persistido continua genérico para a API (AC-014 a AC-016).
    """
    traceback = erro.__traceback__
    while traceback is not None and traceback.tb_next is not None:
        traceback = traceback.tb_next
    origem = (
        f"{traceback.tb_frame.f_code.co_filename}:{traceback.tb_lineno}"
        if traceback is not None
        else "origem indisponível"
    )
    logging.getLogger(__name__).error(
        "execução %s falhou na etapa %s: %s em %s",
        execution_id,
        etapa or "desconhecida",
        type(erro).__name__,
        origem,
    )


def scope_project_id(tenant_id: str, project_id: str, base_id: str) -> str:
    """Compõe o identificador de escopo lógico isolado por base e por tenant.

    ``LogicalScope`` (src/pipeline/) só distingue project_id/tenant_id; sem
    incorporar ``base_id`` aqui, todas as bases do mesmo tenant/projeto
    compartilhariam o mesmo escopo no vector store — o DELETE de uma base
    removeria (ou deixaria de remover) pontos de outra, e uma consulta
    misturaria conteúdo de bases distintas (achado registrado na reabertura
    do Ato II desta spec, T029–T031).

    ``tenant_id`` também entra na string, e não é mais passado como
    ``LogicalScope.tenant_id`` separado (ver ``query_base``/``delete_scope``
    em ``src/app/routers/``): o caminho de escrita (``run_pipeline`` →
    ``chunk_documents`` → ``assign_document_identity``, em ``src/pipeline/``)
    nunca grava ``tenant_id`` no metadata do chunk — só ``project_id``. Se o
    caminho de leitura/exclusão continuasse passando
    ``tenant_id=identity.tenant_id`` explícito para ``LogicalScope``, o
    escopo da escrita (sempre ``tenant_id=None``) nunca bateria com o da
    leitura/exclusão, e toda consulta real voltaria vazia e todo DELETE
    deixaria os pontos reais órfãos. Achado durante o `/code-review` desta
    reabertura (T031 original só isolava por base, não fechava esse
    descompasso). Corrigir isso dentro de `src/pipeline/` está fora de
    escopo desta spec (seção 3); dobrar o tenant na mesma string de
    `project_id`, já sob controle total de `src/app/` nos dois lados, evita
    tocar `src/pipeline/`.
    """
    return f"{tenant_id}::{project_id}::{base_id}"


def build_pipeline_config(
    *,
    base_project_id: str,
    embedding: dict[str, Any],
    vector_store: dict[str, Any],
    input_dir: str,
    chunking: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Monta a configuração injetada na fachada para uma base específica."""
    configuracao = {
        "projeto": {"nome": base_project_id},
        "caminhos": {
            "input_dir": input_dir,
            "chunks_file": f"{input_dir}/chunks.json",
        },
        "embedding": dict(embedding),
        "vector_store": dict(vector_store),
    }
    if chunking:
        configuracao["chunking"] = dict(chunking)
    return configuracao


def _configuracao_da_base(
    session,
    base,
    *,
    embedding: dict[str, Any] | None,
    vector_store: dict[str, Any] | None,
    conexao_embeddings_id: str | None,
    conexao_vector_store_id: str | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    """Resolve embeddings, destino e divisão da Base; a chave só existe em memória.

    Com conexões, decifra as chaves aqui (nunca vieram pela fila) e revalida as
    URLs. Sem elas, usa os argumentos antigos do job ou a configuração global.
    """
    from src.app import conexoes, ingestao
    from src.app.models import Conexao
    from src.app.settings import get_settings

    configuracoes = get_settings()
    if not (conexao_embeddings_id and conexao_vector_store_id):
        return (
            dict(embedding) if embedding is not None else dict(configuracoes.embedding),
            dict(vector_store)
            if vector_store is not None
            else {**configuracoes.vector_store, "collection_name": base.collection_name},
            None,
        )

    def _pipeline(conexao_id: str, tipo: str, **extra: Any) -> dict[str, Any]:
        conexao = session.get(Conexao, conexao_id)
        if conexao is None or conexao.situacao != "ativa" or conexao.tipo != tipo:
            raise conexoes.ErroDeConexao("Conexão indisponível para esta execução.", 409)
        segredo = (
            conexoes.decifrar_segredo(configuracoes.conexoes_chave, conexao.segredo_cifrado)
            if conexao.segredo_cifrado
            else None
        )
        return conexoes.configuracao_para_pipeline(
            tipo,
            conexao.configuracao,
            segredo,
            permitir_locais=configuracoes.conexoes_permitir_locais,
            **extra,
        )

    divisao = base.chunking or {}
    return (
        _pipeline(conexao_embeddings_id, conexoes.TIPO_EMBEDDINGS),
        _pipeline(
            conexao_vector_store_id, conexoes.TIPO_QDRANT, collection_name=base.collection_name
        ),
        ingestao.montar_chunking(
            divisao.get("splitter", ingestao.PADROES["splitter"]),
            int(divisao.get("chunk_size", ingestao.PADROES["chunk_size"])),
            int(divisao.get("chunk_overlap", ingestao.PADROES["chunk_overlap"])),
        ),
    )


def _mesclar_metadados_chunk(
    chunks: Sequence[Document], pares: Sequence[dict[str, str]]
) -> list[Document]:
    """Aplica metadata da Base sem substituir chaves estruturais do pipeline."""
    customizados = {
        item["rotulo"]: item["valor"]
        for item in pares
        if isinstance(item, dict)
        and isinstance(item.get("rotulo"), str)
        and isinstance(item.get("valor"), str)
    }
    resultado = list(chunks)
    for chunk in resultado:
        chunk.metadata = {**customizados, **chunk.metadata}
    return resultado


@app.task(name="process_base_task")
def process_base_task(
    execution_id: str,
    *,
    base_id: str,
    tenant_id: str,
    project_id: str,
    embedding: dict[str, Any] | None = None,
    vector_store: dict[str, Any] | None = None,
    conexao_embeddings_id: str | None = None,
    conexao_vector_store_id: str | None = None,
) -> None:
    """Processa uma execução: carrega, faz chunk, gera embeddings e sincroniza.

    Jobs com conexões trazem só identificadores; jobs de Bases anteriores à
    SPEC-0026 ainda podem trazer `embedding` e `vector_store`, e sem nenhum dos
    dois vale a configuração global injetada no entrypoint.
    """
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira
    from src.app.db import SessionLocal
    from src.app.models import Base, Execution

    with SessionLocal() as session:
        execution = session.get(Execution, execution_id)
        if execution is None:
            return
        base = session.get(Base, base_id)
        if base is None:
            return
        metadados_chunk = list(base.metadados_chunk or [])
        execution.situacao = "running"
        execution.etapa = "carregando"
        session.commit()

        try:
            embedding_cfg, vector_store_cfg, chunking = _configuracao_da_base(
                session,
                base,
                embedding=embedding,
                vector_store=vector_store,
                conexao_embeddings_id=conexao_embeddings_id,
                conexao_vector_store_id=conexao_vector_store_id,
            )
            with tempfile.TemporaryDirectory(prefix=f"base-{base_id}-") as pasta:
                from src.app.storage import get_storage

                storage: Storage = get_storage()
                storage.materialize(base_id, pasta)
                config = build_pipeline_config(
                    base_project_id=scope_project_id(tenant_id, project_id, base_id),
                    embedding=embedding_cfg,
                    vector_store=vector_store_cfg,
                    input_dir=pasta,
                    chunking=chunking,
                )
                execution.etapa = "chunking"
                session.commit()
                resultado = service.run_pipeline(config, only_chunks=True)
                chunks = _mesclar_metadados_chunk(resultado.chunks, metadados_chunk)
                execution.etapa = "indexando"
                execution.previstos = len(chunks)
                session.commit()
                contagens = service.sync_vector_store(config, chunks)
                execution.inseridos = contagens.inseridos
                execution.mantidos = contagens.mantidos
                execution.removidos = contagens.removidos
                execution.situacao = "succeeded"
                execution.etapa = "concluido"
        except Exception as erro:  # noqa: BLE001 — erro seguro, sem detalhe interno do provedor
            _registrar_falha(execution_id, execution.etapa, erro)
            execution.situacao = "failed"
            execution.erro = "Falha ao processar a base; ver logs do worker para detalhes."
            execution.etapa = execution.etapa or "falha"
        finally:
            execution.concluido_em = _agora()
            session.commit()
