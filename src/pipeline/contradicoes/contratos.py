"""Contratos neutros da análise de contradições (SPEC-0038)."""

from __future__ import annotations

from dataclasses import dataclass, field

ETIQUETAS = ("conflito", "versao_desatualizada", "duplicado")
ROTULOS = {
    "conflito": "conflito",
    "versao_desatualizada": "versão desatualizada",
    "duplicado": "duplicado",
}


@dataclass(frozen=True)
class Afirmacao:
    """Um fato extraído de um documento, ligado a um assunto."""

    arquivo: str
    assunto: str
    texto: str
    impacto: str = "baixo"
    imagem: str | None = None


@dataclass(frozen=True)
class Trecho:
    arquivo: str
    texto: str
    imagem: str | None = None


@dataclass(frozen=True)
class Ocorrencia:
    assunto: str
    etiqueta: str
    impacto: str
    trechos: list[Trecho]
    explicacao: str
    arquivo_mais_antigo: str | None = None


@dataclass(frozen=True)
class Julgamento:
    """Um pedido à IA: somente as afirmações de um assunto."""

    assunto: str
    afirmacoes: list[Afirmacao] = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoExtracao:
    afirmacoes: list[Afirmacao]
    nao_classificadas: int = 0
