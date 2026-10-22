"""Contratos neutros da limpeza (SPEC-0037).

Nada aqui depende de HTTP, banco ou biblioteca de IA.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Exclusao:
    """Uma remoção feita pela limpeza, com origem e motivo auditáveis."""

    arquivo: str
    posicao: int
    motivo: str
    camada: str
    trecho: str
    confianca: float | None = None
    mantido_em: str | None = None


@dataclass(frozen=True)
class ResultadoLimpeza:
    markdown: str
    exclusoes: list[Exclusao] = field(default_factory=list)


@dataclass(frozen=True)
class SecaoAvaliada:
    """Decisão da IA para uma seção: ``remover``, ``manter`` ou ``duvida``."""

    texto: str
    decisao: str
    confianca: float


@dataclass(frozen=True)
class ParDuplicado:
    arquivo_a: str
    arquivo_b: str
    trecho_a: str
    trecho_b: str
    semelhanca: float


@dataclass(frozen=True)
class ResultadoDuplicidade:
    documentos: dict[str, str]
    exclusoes: list[Exclusao] = field(default_factory=list)
    provaveis: list[ParDuplicado] = field(default_factory=list)
