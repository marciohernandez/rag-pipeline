"""Contratos neutros da decisão da empresa (SPEC-0039)."""

from __future__ import annotations

from dataclasses import dataclass

SITUACOES = ("clara", "incerta", "sem_decisao")
MSG_NAO_LOCALIZADO = "Não foi possível localizar o trecho; indique qual corrigir"
MSG_NAO_COBERTA = "A resposta da empresa não cobre esta contradição."


@dataclass(frozen=True)
class Localizacao:
    """Posição do trecho alvo no Markdown; ``exata`` é falso na correspondência aproximada."""

    inicio: int
    fim: int
    exata: bool


@dataclass(frozen=True)
class Proposta:
    """Proposta de correção para uma contradição; nada é gravado até a pessoa confirmar."""

    ocorrencia_id: str
    situacao: str
    arquivo: str | None = None
    trecho_alvo: str = ""
    texto_corrigido: str = ""
    motivo: str | None = None
