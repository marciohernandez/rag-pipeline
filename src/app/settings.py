"""Configuração de embeddings/vector store injetada pelo entrypoint (PR-002)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = ["AppSettings", "configure", "get_settings"]


@dataclass(frozen=True)
class AppSettings:
    embedding: dict[str, Any]
    vector_store: dict[str, Any]
    # SPEC-0021: modelo de linguagem do assistente e coleção de conhecimento do
    # produto, ambos injetados pelo entrypoint (nunca lidos do ambiente aqui).
    llm: dict[str, Any] = field(default_factory=dict)
    conhecimento_collection: str = "assistente_conhecimento"
    # SPEC-0026: chave Fernet que cifra as chaves das conexões. Vazia quando o
    # entrypoint não a recebeu; conexões só funcionam com ela (nunca no repr).
    conexoes_chave: str = field(default="", repr=False)
    # Exceção explícita de desenvolvimento: aceita URLs de loopback nas conexões.
    conexoes_permitir_locais: bool = False


_SETTINGS: AppSettings | None = None


def configure(settings: AppSettings) -> None:
    global _SETTINGS
    _SETTINGS = settings


def get_settings() -> AppSettings:
    if _SETTINGS is None:
        raise RuntimeError(
            "AppSettings não configurado. Chame src.app.settings.configure(...) no entrypoint."
        )
    return _SETTINGS
