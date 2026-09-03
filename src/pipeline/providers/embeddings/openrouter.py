"""Adapter de embeddings via OpenRouter (SPEC-0003).

Compartilha o SDK ``OpenAIEmbeddings`` da OpenAI, mudando somente credencial e
``base_url``. Corpo dos métodos implementado por T020.
"""

from __future__ import annotations

from src.pipeline.providers.embeddings.openai import OpenAIEmbeddingAdapter


class OpenRouterEmbeddingAdapter(OpenAIEmbeddingAdapter):
    provider = "openrouter"
    _env_var = "OPENROUTER_API_KEY"
    _default_base_url = "https://openrouter.ai/api/v1"
