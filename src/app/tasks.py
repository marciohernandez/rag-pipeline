"""Tarefas assíncronas do backend: envios de documentos (SPEC-0030) e limpeza de acesso.

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
from datetime import UTC, datetime, timedelta
from pathlib import Path
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


def scope_colecao(tenant_id: str, project_id: str, colecao_id: str) -> str:
    """Escopo lógico (``metadata.project_id``) de uma coleção, isolado por tenant e projeto."""
    return f"{tenant_id}::{project_id}::{colecao_id}"


def build_pipeline_config(
    *,
    base_project_id: str,
    embedding: dict[str, Any],
    vector_store: dict[str, Any],
    input_dir: str,
    chunking: dict[str, Any] | None = None,
    secoes: dict[str, Any] | None = None,
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
    configuracao.update(secoes or {})
    return configuracao


def _config_da_conexao(session, conexao_id: str, tipo: str, **extra: Any) -> dict[str, Any]:
    """Seção ``embedding`` ou ``vector_store`` de uma conexão ativa; a chave só existe em memória.

    Caminho único de decifra e revalidação de URL, usado pela execução e pela
    exclusão da Base para que as duas alcancem o mesmo destino (SPEC-0028).
    """
    from src.app import conexoes
    from src.app.models import Conexao
    from src.app.settings import get_settings

    configuracoes = get_settings()
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


def configuracao_vector_store_da_base(session, base) -> dict[str, Any]:
    """Seção ``vector_store`` da Base: conexão Qdrant vinculada ou configuração global.

    Em ambos os casos a coleção é a da própria Base. Uma conexão desativada
    bloqueia com 409 e orienta a reativá-la (SPEC-0028, DEC-003). O log traz a
    coleção e o nome da conexão, nunca a chave.
    """
    from src.app import conexoes
    from src.app.models import Conexao
    from src.app.settings import get_settings

    if not (base.conexao_embeddings_id and base.conexao_vector_store_id):
        logging.getLogger(__name__).info(
            "vector store da Base %s: coleção=%s conexão=configuração global",
            base.id,
            base.collection_name,
        )
        return {**get_settings().vector_store, "collection_name": base.collection_name}

    conexao = session.get(Conexao, base.conexao_vector_store_id)
    if conexao is not None and conexao.tipo == conexoes.TIPO_QDRANT and conexao.situacao != "ativa":
        raise conexoes.ErroDeConexao(
            f"A conexão {conexao.nome} está desativada. Reative-a para apagar a Base.", 409
        )
    configuracao = _config_da_conexao(
        session,
        base.conexao_vector_store_id,
        conexoes.TIPO_QDRANT,
        collection_name=base.collection_name,
    )
    logging.getLogger(__name__).info(
        "vector store da Base %s: coleção=%s conexão=%s",
        base.id,
        base.collection_name,
        conexao.nome if conexao is not None else "desconhecida",
    )
    return configuracao


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


_ERRO_ENVIO = "Falha ao processar o envio; ver logs do worker para detalhes."


def _registrar_documento(session, envio, colecao_id: str, contagens, chunks) -> None:
    """Grava a nova versão do documento depois que o destino confirmou a sincronização."""
    from sqlalchemy import select

    from src.app.models import DocumentoColecao

    primeiro = chunks[0].metadata
    nome = str(primeiro.get("nome_arquivo", ""))
    documento = session.execute(
        select(DocumentoColecao).where(
            DocumentoColecao.colecao_id == colecao_id, DocumentoColecao.nome_arquivo == nome
        )
    ).scalar_one_or_none()
    if documento is None:
        documento = DocumentoColecao(colecao_id=colecao_id, nome_arquivo=nome)
        session.add(documento)
    elif contagens.inseridos == 0 and contagens.removidos == 0:
        return
    documento.document_id = str(primeiro.get("document_id", ""))
    documento.source_hash = str(primeiro.get("source_hash", ""))
    documento.chunks = len(chunks)
    documento.chunking = dict(envio.processamento or {})
    documento.ultimo_envio_id = envio.id
    documento.atualizado_em = _agora()
    session.commit()


@app.task(name="process_envio_task")
def process_envio_task(envio_id: str) -> None:
    """Processa um envio: divide, sincroniza documento a documento e registra a versão.

    Só ``envio_id`` vai pela fila; conexões, divisão e arquivos são lidos aqui, e a
    chave existe apenas em memória. Cada documento só muda de versão depois que o
    destino confirma a sincronização dele (NFR-004).
    """
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira
    from src.app import conexoes, ingestao
    from src.app.db import SessionLocal
    from src.app.models import Colecao, Envio

    with SessionLocal() as session:
        envio = session.get(Envio, envio_id)
        if envio is None or envio.situacao not in ("queued", "failed"):
            return
        colecao = session.get(Colecao, envio.colecao_id)
        if colecao is None or colecao.apagada_em is not None:
            return
        colecao_id = colecao.id
        envio.situacao = "running"
        envio.etapa = "carregando"
        envio.erro = None
        session.commit()

        try:
            divisao = dict(envio.processamento or {})
            embedding = _config_da_conexao(
                session, colecao.conexao_embeddings_id, conexoes.TIPO_EMBEDDINGS
            )
            destino = divisao.get("destino") or {}
            if "batch_size" in destino:
                embedding["batch_size"] = int(destino["batch_size"])
            vector_store = _config_da_conexao(
                session,
                colecao.conexao_vector_store_id,
                conexoes.TIPO_QDRANT,
                collection_name=colecao.nome_fisico,
            )
            vector_store.pop("sync_mode", None)
            with tempfile.TemporaryDirectory(prefix=f"envio-{envio_id}-") as pasta:
                from src.app.storage import get_storage

                storage: Storage = get_storage()
                storage.materialize(envio_id, pasta)
                config = build_pipeline_config(
                    base_project_id=scope_colecao(
                        colecao.tenant_id, colecao.project_id, colecao_id
                    ),
                    embedding=embedding,
                    vector_store=vector_store,
                    input_dir=pasta,
                    chunking=ingestao.montar_chunking(
                        divisao.get("splitter", ingestao.PADROES["splitter"]),
                        int(divisao.get("chunk_size", ingestao.PADROES["chunk_size"])),
                        int(divisao.get("chunk_overlap", ingestao.PADROES["chunk_overlap"])),
                        divisao,
                    ),
                    secoes=ingestao.secoes_de_processamento(divisao),
                )
                envio.etapa = "chunking"
                session.commit()
                resultado = service.run_pipeline(config, only_chunks=True)
                chunks = _mesclar_metadados_chunk(
                    resultado.chunks, list(envio.metadados_chunk or [])
                )
                envio.etapa = "indexando"
                envio.previstos = len(chunks)
                session.commit()
                contagens = service.sync_documents(
                    config,
                    chunks,
                    on_document=lambda _doc, cont, grupo: _registrar_documento(
                        session, envio, colecao_id, cont, grupo
                    ),
                )
                envio.inseridos = contagens.inseridos
                envio.mantidos = contagens.mantidos
                envio.removidos = contagens.removidos
                envio.situacao = "succeeded"
                envio.etapa = "concluido"
        except Exception as erro:  # noqa: BLE001 — erro seguro, sem detalhe interno do provedor
            session.rollback()
            envio = session.get(Envio, envio_id)
            _registrar_falha(envio_id, envio.etapa, erro)
            envio.situacao = "failed"
            envio.erro = _ERRO_ENVIO
            envio.etapa = envio.etapa or "falha"
        finally:
            envio.concluido_em = _agora()
            session.commit()


_RETENCAO_CONVERSAO_DIAS = 7


def _registrar_falha_documento(documento_id: str, erro: BaseException) -> None:
    """Registra a causa técnica de uma conversão que falhou (NFR-003, AC-018).

    Mesmo padrão de ``_registrar_falha``: tipo da exceção e origem no código
    vão para o log; a mensagem da exceção fica de fora — pode carregar DSN,
    chave ou outro segredo do conversor ou de sua dependência.
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
        "conversão do documento %s falhou: %s em %s",
        documento_id,
        type(erro).__name__,
        origem,
    )


@app.task(name="process_conversion_document_task")
def process_conversion_document_task(*, documento_id: str) -> None:
    """Converte um documento para Markdown e recalcula a situação do lote (SPEC-0023)."""
    from dataclasses import asdict

    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira
    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao
    from src.app.repo import recalcular_situacao_lote
    from src.app.settings import get_settings
    from src.app.storage import get_storage

    with SessionLocal() as session:
        documento = session.get(DocumentoConversao, documento_id)
        if documento is None:
            return
        documento.situacao = "processando"
        session.commit()

        try:
            with tempfile.TemporaryDirectory(prefix=f"conversao-{documento_id}-") as pasta:
                storage: Storage = get_storage()
                storage.materialize(documento_id, pasta)
                caminho = Path(pasta) / documento.nome_arquivo
                resultado = service.convert_document(
                    caminho, documento.formato, config={"conversao": get_settings().conversao}
                )
                nome_markdown = f"{Path(documento.nome_arquivo).stem}.md"
                storage.save(documento_id, nome_markdown, resultado.markdown.encode("utf-8"))
                documento.situacao = "concluido"
                documento.erro = None
                documento.avisos = [asdict(aviso) for aviso in resultado.avisos]
        except Exception as erro:  # noqa: BLE001 — erro seguro, sem detalhe interno do conversor
            _registrar_falha_documento(documento_id, erro)
            documento.situacao = "falhou"
            documento.erro = "Não foi possível converter o documento; tente reenviar."
            documento.avisos = []
        finally:
            documento.concluido_em = _agora()
            documento.expira_em = documento.concluido_em + timedelta(days=_RETENCAO_CONVERSAO_DIAS)
            recalcular_situacao_lote(session, documento.lote_id)
            session.commit()


@app.periodic(cron="0 3 * * *")
@app.task(name="purgar_documentos_conversao_task")
def purgar_documentos_conversao_task(_timestamp: int) -> None:
    """Remove diariamente os arquivos de documentos convertidos expirados (FR-007).

    Só apaga original e ``.md`` do Storage; a linha em ``documentos_conversao``
    nunca é removida, preservando o histórico do lote (AC-013, AC-014).
    """
    from sqlalchemy import select

    from src.app.db import SessionLocal
    from src.app.models import DocumentoConversao
    from src.app.storage import get_storage

    storage = get_storage()
    with SessionLocal() as session:
        expirados = (
            session.execute(
                select(DocumentoConversao).where(
                    DocumentoConversao.expira_em <= _agora(),
                    DocumentoConversao.apagado_em.is_(None),
                )
            )
            .scalars()
            .all()
        )
        for documento in expirados:
            storage.delete_base(documento.id)
            documento.apagado_em = _agora()
        session.commit()
    logging.getLogger(__name__).info(
        "purga de documentos de conversão concluída: %d documento(s)", len(expirados)
    )
