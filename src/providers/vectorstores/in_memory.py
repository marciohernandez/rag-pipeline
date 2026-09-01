"""Adapter de vector store in-memory (SPEC-0003).

Referência completa do núcleo e da extensão ``mirror``, sem SDK. Serve de
oráculo estável para a suíte de conformidade e para os CLIs em testes.
"""

from __future__ import annotations

from src.providers.vectorstores.base import (
    BaseVectorStoreAdapter,
    DictVectorBackend,
    MirrorMixin,
)


class InMemoryVectorStoreAdapter(MirrorMixin, BaseVectorStoreAdapter):
    provider = "in_memory"

    def __init__(self, **_ignored: object) -> None:
        # O adapter in-memory nunca usa cliente externo: ele é a própria
        # referência do contrato.
        super().__init__(client=DictVectorBackend())
