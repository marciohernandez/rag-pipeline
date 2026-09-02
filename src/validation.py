"""Validação somente leitura de uma base indexada (SPEC-0004).

Este módulo começa pela fronteira local: a configuração e o gabarito são
validados integralmente antes de qualquer adapter ou provider ser consultado.
"""

from __future__ import annotations

import json

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from src.providers.contracts import LogicalScope


_CATEGORIAS = {"ampla", "especifica", "sem_resposta"}


@dataclass(frozen=True)
class QueryCase:
    pergunta: str
    categoria: str
    deve_conter: tuple[str, ...] = ()
    documento_esperado: str | None = None


@dataclass(frozen=True)
class ScopeComparison:
    previstos: int = 0
    observados: int = 0
    faltantes: frozenset[str] = frozenset()
    orfaos: frozenset[str] = frozenset()


@dataclass(frozen=True)
class QueryOutcome:
    pergunta: str
    categoria: str
    aprovada: bool
    criterios_ausentes: tuple[str, ...] = ()
    melhor_score: float | None = None


@dataclass(frozen=True)
class ValidationReport:
    outcome: str
    impediment: str | None = None
    comparison: ScopeComparison = field(default_factory=ScopeComparison)
    queries: tuple[QueryOutcome, ...] = ()
    report_path: str | None = None

    def to_dict(self) -> dict:
        """Representação segura para a camada de saída futura."""
        return {
            "desfecho": self.outcome,
            "impedimento": self.impediment,
            "preflight": {},
            "conferencia": {
                "previstos": self.comparison.previstos,
                "observados": self.comparison.observados,
                "faltantes": sorted(self.comparison.faltantes),
                "orfaos": sorted(self.comparison.orfaos),
            },
            "consultas": [],
        }

    def render(self) -> str:
        return f"Validação: {self.outcome}" + (
            f" — {self.impediment}" if self.impediment else ""
        )


def _non_empty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Gabarito inválido: {field_name} é obrigatório.")
    return value.strip()


def load_query_cases(path: str) -> list[QueryCase]:
    """Carrega e valida localmente o gabarito versionado da base."""
    query_path = Path(path)
    if not query_path.is_file():
        raise ValueError("Gabarito de consultas não encontrado.")

    try:
        loaded = yaml.safe_load(query_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError("Gabarito de consultas inválido.") from error

    if not isinstance(loaded, list) or not loaded:
        raise ValueError("Gabarito de consultas deve conter ao menos uma entrada.")

    cases: list[QueryCase] = []
    for entry in loaded:
        if not isinstance(entry, dict):
            raise ValueError("Cada entrada do gabarito deve ser um objeto.")
        pergunta = _non_empty_text(entry.get("pergunta"), "pergunta")
        categoria = _non_empty_text(entry.get("categoria"), "categoria")
        if categoria not in _CATEGORIAS:
            raise ValueError("Categoria de consulta inválida.")

        raw_terms = entry.get("deve_conter", [])
        if not isinstance(raw_terms, list) or any(
            not isinstance(term, str) or not term.strip() for term in raw_terms
        ):
            raise ValueError("deve_conter deve ser uma lista de textos não vazios.")
        terms = tuple(term.strip() for term in raw_terms)

        document = entry.get("documento_esperado")
        if document is not None:
            document = _non_empty_text(document, "documento_esperado")
        if categoria != "sem_resposta" and not (terms or document):
            raise ValueError(
                "Consultas amplas e específicas exigem deve_conter ou documento_esperado."
            )
        cases.append(QueryCase(pergunta, categoria, terms, document))
    return cases


class _Impedimento(RuntimeError):
    """Motivo pelo qual não foi possível validar; nunca é uma reprovação."""


def _scope_from_config(config: dict, tenant_id: str | None) -> LogicalScope:
    """Deriva o escopo lógico de `projeto.nome`, como o resto do pipeline."""
    project_id = (config.get("projeto") or {}).get("nome")
    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("Configuração sem projeto.nome.")
    return LogicalScope(project_id=project_id.strip(), tenant_id=tenant_id)


def _configured_dimensions(config: dict) -> int:
    from src.indexing import resolve_dimensions

    return resolve_dimensions(config.get("embedding") or {})


def preflight(adapter, scope: LogicalScope, *, dimensions: int) -> dict:
    """Confere existência e dimensão do escopo por leitura pura.

    Não usa `ensure_ready`: naquele caminho o adapter Qdrant cria a coleção
    ausente, o que transformaria um escopo inexistente em base vazia aprovada.
    A mensagem de impedimento nunca cita credencial, token ou URL de destino.
    """
    metadados = adapter.describe_scope(scope)
    if not metadados:
        raise _Impedimento(
            "Escopo inexistente ou inacessível no destino configurado."
        )
    declarada = metadados.get("dimensions")
    if declarada is not None and int(declarada) != int(dimensions):
        raise _Impedimento(
            f"Dimensão declarada pelo destino ({declarada}) difere da dimensão "
            f"configurada para embeddings ({dimensions})."
        )
    return dict(metadados)


def _manifest_path(config: dict) -> Path:
    """Resolve o manifesto como `pipeline.py`, para conferir a mesma base."""
    caminhos = config.get("caminhos") or {}
    declarado = caminhos.get("manifest_file")
    if isinstance(declarado, str) and declarado.strip():
        return Path(declarado.strip())
    chunks_file = caminhos.get("chunks_file")
    if not isinstance(chunks_file, str) or not chunks_file.strip():
        raise ValueError(
            "Configuração sem caminhos.manifest_file nem caminhos.chunks_file."
        )
    return Path(chunks_file.strip()).with_name("manifest.json")


def load_manifest(config: dict) -> dict:
    """Carrega o manifesto e confirma que ele descreve a base configurada."""
    caminho = _manifest_path(config)
    if not caminho.is_file():
        raise _Impedimento("Manifesto da base não encontrado.")
    try:
        manifesto = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise _Impedimento("Manifesto da base inválido.") from error
    if not isinstance(manifesto, dict):
        raise _Impedimento("Manifesto da base inválido.")

    projeto = (config.get("projeto") or {}).get("nome")
    colecao = (config.get("vector_store") or {}).get("collection_name")
    if manifesto.get("project_id") != projeto:
        raise _Impedimento(
            "Manifesto pertence a outro projeto: "
            f"{manifesto.get('project_id')!r} em vez de {projeto!r}."
        )
    if colecao is not None and manifesto.get("collection_name") != colecao:
        raise _Impedimento(
            "Manifesto pertence a outra coleção: "
            f"{manifesto.get('collection_name')!r} em vez de {colecao!r}."
        )
    return manifesto


def compare_scope(adapter, scope: LogicalScope, expected_ids) -> ScopeComparison:
    """Compara identidades por igualdade estrita, sem escrever no destino."""
    previstos = {str(item) for item in expected_ids}
    observados = {str(item) for item in adapter.list_ids(scope)}
    return ScopeComparison(
        previstos=len(previstos),
        observados=len(observados),
        faltantes=frozenset(previstos - observados),
        orfaos=frozenset(observados - previstos),
    )


def validate_base(config: dict, *, adapter=None, embeddings=None, tenant_id=None) -> ValidationReport:
    """Valida toda entrada local e o ambiente antes de conferir identidades."""
    del embeddings
    try:
        paths = config.get("caminhos", {})
        reference_path = paths.get("consultas_referencia")
        if not isinstance(reference_path, str) or not reference_path.strip():
            raise ValueError("Configuração sem caminhos.consultas_referencia.")
        load_query_cases(reference_path)
        scope = _scope_from_config(config, tenant_id)
        dimensions = _configured_dimensions(config)
    except (AttributeError, TypeError, ValueError) as error:
        return ValidationReport(outcome="impedido", impediment=str(error))

    if adapter is None:
        from src.indexing import build_vector_store

        adapter = build_vector_store(
            config.get("vector_store") or {},
            (config.get("caminhos") or {}).get("vector_store_dir"),
        )

    try:
        preflight(adapter, scope, dimensions=dimensions)
        manifesto = load_manifest(config)
        comparacao = compare_scope(adapter, scope, manifesto.get("chunk_ids") or [])
    except _Impedimento as error:
        return ValidationReport(outcome="impedido", impediment=str(error))

    if comparacao.faltantes or comparacao.orfaos:
        return ValidationReport(outcome="reprovado", comparison=comparacao)

    return ValidationReport(
        outcome="impedido",
        impediment="Roteiro de consultas ainda não executado.",
        comparison=comparacao,
    )


def exit_code(report: ValidationReport) -> int:
    """Traduz o desfecho sem acoplar o caso de uso à linha de comando."""
    return {"aprovado": 0, "reprovado": 1}.get(report.outcome, 2)
