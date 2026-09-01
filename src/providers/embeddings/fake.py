"""Adapter de embeddings determinístico para conformidade (SPEC-0003).

Sem SDK e sem rede. O vetor de um texto é derivado de SHA-256, então a mesma
entrada sempre produz o mesmo vetor e entradas diferentes produzem vetores
diferentes. Usado como oráculo estável pela suíte de conformidade.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from src.providers.embeddings.base import BaseEmbeddingAdapter
from src.providers.errors import InvalidProviderConfigError

_DEFAULT_DIMENSIONS = 16


def _deterministic_vector(text: str, dimensions: int) -> list[float]:
    values: list[float] = []
    counter = 0
    while len(values) < dimensions:
        block = hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest()
        for offset in range(0, len(block), 2):
            values.append(int.from_bytes(block[offset : offset + 2], "big") / 65535.0)
            if len(values) >= dimensions:
                break
        counter += 1
    return values[:dimensions]


class FakeEmbeddingAdapter(BaseEmbeddingAdapter):
    provider = "fake"

    def __init__(self, *, dimensions: int | None = None, **_ignored: object) -> None:
        dims = _DEFAULT_DIMENSIONS if dimensions is None else int(dimensions)
        if dims <= 0:
            raise InvalidProviderConfigError("dimensions deve ser um inteiro positivo.")
        self._dimensions = dims

    def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [_deterministic_vector(text, self._dimensions) for text in texts]
