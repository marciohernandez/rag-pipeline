"""Contratos neutros de conversor para Markdown (SPEC-0023).

Nenhum tipo aqui depende de biblioteca de extração. A `ConverterFactory`
devolve adapters que satisfazem `DocumentConverter`; consumidores conhecem
apenas este módulo, seguindo o mesmo padrão de `src/pipeline/providers/contracts.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class AvisoConversao:
    """Motivo de revisão, com página numerada a partir de um."""

    codigo: str
    pagina: int | None
    mensagem: str


@dataclass(frozen=True)
class ConversionResult:
    """Resultado neutro da conversão de um documento para Markdown."""

    markdown: str
    avisos: list[AvisoConversao] = field(default_factory=list)


@runtime_checkable
class DocumentConverter(Protocol):
    """Converte um arquivo local em `ConversionResult`."""

    def converter(self, caminho: Path) -> ConversionResult: ...


class ConversionError(Exception):
    """Erro base de qualquer conversor de documento."""


class UnsupportedFormatError(ConversionError, ValueError):
    """A factory recebeu uma extensão sem conversor correspondente."""
