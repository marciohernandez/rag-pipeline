"""Fachada estável dos casos de uso do pipeline.

As operações recebem a configuração não sensível já resolvida. Leitura de
arquivo e preparação do ambiente pertencem aos entrypoints da raiz; resolução
de credenciais continua encapsulada nos adapters de provider.
"""

from __future__ import annotations

from collections.abc import Mapping as _Mapping
from collections.abc import Sequence as _Sequence
from dataclasses import dataclass as _dataclass
from pathlib import Path as _Path
from typing import Any as _Any

from langchain_core.documents import Document as _Document

from src.pipeline import indexing as _indexing
from src.pipeline.chunker import chunk_documents as _chunk_documents
from src.pipeline.exporter import export_chunks_to_json as _export_chunks_to_json
from src.pipeline.indexing import build_scope as _build_scope
from src.pipeline.indexing import index_chunks as _index_chunks
from src.pipeline.indexing import retrieve as _retrieve
from src.pipeline.loader import load_markdown_documents as _load_markdown_documents
from src.pipeline.manifest import build_manifest as _build_manifest
from src.pipeline.manifest import export_manifest as _export_manifest
from src.pipeline.providers.contracts import SyncCounts as _SyncCounts
from src.pipeline.quality import evaluate_quality as _evaluate_quality
from src.pipeline.status_gate import filter_by_status as _filter_by_status
from src.pipeline.validation import validate_base as _validate_base

__all__ = [
    "delete_scope",
    "query_base",
    "run_pipeline",
    "sync_vector_store",
    "validate_retrieval",
]


@_dataclass(frozen=True)
class _PipelineRunResult:
    """Resultado estruturado da preparação e sincronização de uma base."""

    documents: tuple[_Document, ...]
    chunks: tuple[_Document, ...]
    manifest: dict[str, _Any]
    manifest_path: str
    excluded_documents: tuple[dict[str, _Any], ...]
    quality_report: _Any
    sync_counts: _SyncCounts | None


def _required_mapping(config: _Mapping[str, _Any], key: str) -> dict[str, _Any]:
    value = config.get(key)
    if value is None:
        raise ValueError(f"Configuração sem {key}.")
    if not isinstance(value, _Mapping):
        raise TypeError(f"Configuração {key} deve ser um objeto.")
    return dict(value)


def _optional_mapping(config: _Mapping[str, _Any], key: str) -> dict[str, _Any]:
    value = config.get(key) or {}
    if not isinstance(value, _Mapping):
        raise TypeError(f"Configuração {key} deve ser um objeto.")
    return dict(value)


def _project_id(config: _Mapping[str, _Any]) -> str:
    project = _required_mapping(config, "projeto")
    value = project.get("nome")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Configuração sem projeto.nome.")
    return value.strip()


def _runtime_sections(
    config: _Mapping[str, _Any],
) -> tuple[str, dict[str, _Any], dict[str, _Any]]:
    if not isinstance(config, _Mapping):
        raise TypeError("Configuração resolvida deve ser um objeto.")
    return (
        _project_id(config),
        _required_mapping(config, "embedding"),
        _required_mapping(config, "vector_store"),
    )


def _required_path(paths: _Mapping[str, _Any], key: str) -> str:
    value = paths.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Configuração sem caminhos.{key}.")
    return value.strip()


def run_pipeline(
    config: _Mapping[str, _Any],
    *,
    input_dir: str | None = None,
    only_chunks: bool = False,
) -> _PipelineRunResult:
    """Prepara uma base e, quando solicitado, sincroniza seus chunks."""
    project_id, embedding_config, vector_config = _runtime_sections(config)
    paths = _required_mapping(config, "caminhos")
    source_dir = input_dir or _required_path(paths, "input_dir")
    chunks_path = _required_path(paths, "chunks_file")
    manifest_path = str(
        paths.get("manifest_file") or _Path(chunks_path).with_name("manifest.json")
    )

    documents = _load_markdown_documents(source_dir)
    markdown_contract = _optional_mapping(config, "contrato_markdown")
    selected, excluded = _filter_by_status(
        documents,
        markdown_contract.get("status_bloqueado", []),
    )
    chunking_config = _optional_mapping(config, "chunking")
    chunks = _chunk_documents(
        selected,
        dict(chunking_config),
        project_id=project_id,
    )

    _export_chunks_to_json(chunks, chunks_path)
    manifest = _build_manifest(
        chunks,
        project_id=project_id,
        collection_name=vector_config.get("collection_name", "rag_docs"),
        embedding_cfg=embedding_config,
        excluded_documents=excluded,
    )
    _export_manifest(manifest, manifest_path)

    quality_config = _optional_mapping(config, "qualidade")
    quality_report = _evaluate_quality(
        chunks,
        dict(chunking_config),
        dict(quality_config),
        manifest=manifest,
        output_dir=_Path(chunks_path).parent,
    )
    counts = None
    if not only_chunks:
        counts = sync_vector_store(config=config, chunks=chunks)

    return _PipelineRunResult(
        documents=tuple(selected),
        chunks=tuple(chunks),
        manifest=manifest,
        manifest_path=manifest_path,
        excluded_documents=tuple(excluded),
        quality_report=quality_report,
        sync_counts=counts,
    )


def sync_vector_store(
    config: _Mapping[str, _Any],
    chunks: _Sequence[_Document],
) -> _SyncCounts:
    """Sincroniza chunks e devolve as quatro contagens ao chamador."""
    _project, embedding_config, vector_config = _runtime_sections(config)
    if not chunks:
        return _SyncCounts(previstos=0, inseridos=0, mantidos=0, removidos=0)
    paths = _optional_mapping(config, "caminhos")
    return _index_chunks(
        chunks=chunks,
        embedding_cfg=embedding_config,
        vector_cfg=vector_config,
        persist_dir=paths.get("vector_store_dir"),
    )


def delete_scope(
    config: _Mapping[str, _Any],
    *,
    tenant_id: str | None = None,
) -> int:
    """Remove todos os pontos indexados no escopo lógico configurado.

    Usado pela exclusão de bases (`src/app/`): cada base tem seu próprio
    `projeto.nome` (isolamento por base resolvido pelo chamador), então
    esvaziar o escopo aqui não afeta outras bases.
    """
    project_id, _embedding_config, vector_config = _runtime_sections(config)
    adapter = _indexing.build_vector_store(vector_config)
    scope = _build_scope(project_id, tenant_id)
    ids = adapter.list_ids(scope)
    if ids:
        adapter.delete_ids(scope, ids)
    return len(ids)


def validate_retrieval(
    config: _Mapping[str, _Any],
    *,
    tenant_id: str | None = None,
):
    """Valida uma base indexada sem alterar o destino."""
    _runtime_sections(config)
    _required_mapping(config, "caminhos")
    return _validate_base(dict(config), tenant_id=tenant_id)


def query_base(
    config: _Mapping[str, _Any],
    query: str,
    *,
    top_k: int = 4,
    tenant_id: str | None = None,
):
    """Consulta a base indexada sob o escopo lógico configurado."""
    project_id, embedding_config, vector_config = _runtime_sections(config)
    if not isinstance(query, str) or not query.strip():
        raise ValueError("A consulta não pode ser vazia.")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k deve ser um inteiro positivo.")
    paths = _optional_mapping(config, "caminhos")
    return _retrieve(
        query.strip(),
        embedding_config,
        vector_config,
        project_id=project_id,
        tenant_id=tenant_id,
        k=top_k,
        persist_dir=paths.get("vector_store_dir"),
    )
