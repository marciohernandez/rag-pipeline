"""Validação somente leitura de uma base indexada (SPEC-0004).

Este módulo começa pela fronteira local: a configuração e o gabarito são
validados integralmente antes de qualquer adapter ou provider ser consultado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


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


def validate_base(config: dict, *, adapter=None, embeddings=None, tenant_id=None) -> ValidationReport:
    """Valida primeiro toda entrada local, sem acessar o destino nesta fase."""
    del adapter, embeddings, tenant_id
    try:
        paths = config.get("caminhos", {})
        reference_path = paths.get("consultas_referencia")
        if not isinstance(reference_path, str) or not reference_path.strip():
            raise ValueError("Configuração sem caminhos.consultas_referencia.")
        load_query_cases(reference_path)
    except (AttributeError, TypeError, ValueError) as error:
        return ValidationReport(outcome="impedido", impediment=str(error))
    return ValidationReport(
        outcome="impedido",
        impediment="Preflight remoto ainda não executado.",
    )


def exit_code(report: ValidationReport) -> int:
    """Traduz o desfecho sem acoplar o caso de uso à linha de comando."""
    return {"aprovado": 0, "reprovado": 1}.get(report.outcome, 2)
