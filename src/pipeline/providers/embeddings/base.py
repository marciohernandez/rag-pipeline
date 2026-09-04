"""Base comum dos adapters de embeddings (SPEC-0003).

Concentra o comportamento compartilhado: ``embed_query`` deriva de
``embed_documents`` quando o adapter não tiver um caminho próprio, garantindo
que consulta e documento usem exatamente a mesma representação.
"""

from __future__ import annotations

from collections.abc import Sequence


class BaseEmbeddingAdapter:
    """Contrato mínimo; subclasses implementam ``_embed``."""

    provider: str = "base"

    def _embed(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(list(texts))

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]
