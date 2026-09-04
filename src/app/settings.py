"""Configuração de embeddings/vector store injetada pelo entrypoint (PR-002)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["AppSettings", "configure", "get_settings"]


@dataclass(frozen=True)
class AppSettings:
    embedding: dict[str, Any]
    vector_store: dict[str, Any]


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
