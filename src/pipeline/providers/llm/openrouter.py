"""Adapter de chat via OpenRouter (SPEC-0021, FR-012).

Confina o SDK ``ChatOpenAI`` (API compatível com OpenAI). Recebe a configuração
já resolvida pelo entrypoint — provedor, modelo, chave e tempo limite — e nunca
lê o ambiente. O cliente é criado sob demanda, sem repetição automática nem
fallback: falha do provedor, da rede ou do tempo limite vira
``ChatProviderError`` genérico, sem detalhe interno nem credencial.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from src.pipeline.providers.contracts import ChatMessage
from src.pipeline.providers.errors import (
    ChatProviderError,
    InvalidProviderConfigError,
    MissingCredentialError,
)

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_TIMEOUT = 30.0
_PAPEIS = {"sistema": "system", "pessoa": "user", "assistente": "assistant"}


class OpenRouterChatAdapter:
    provider = "openrouter"

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
        base_url: str | None = None,
        **_ignored: object,
    ) -> None:
        if not isinstance(model, str) or not model.strip():
            raise InvalidProviderConfigError(
                "Configuração de chat incompleta: informe 'model' (LLM_MODEL)."
            )
        if not isinstance(api_key, str) or not api_key.strip():
            raise MissingCredentialError(
                "Configuração de chat incompleta: informe 'api_key' (OPENROUTER_API_KEY)."
            )
        tempo = _DEFAULT_TIMEOUT if timeout is None else timeout
        if isinstance(tempo, bool) or not isinstance(tempo, (int, float)) or tempo <= 0:
            raise InvalidProviderConfigError("'timeout' deve ser um número positivo de segundos.")
        self._model = model.strip()
        self._api_key = api_key
        self._timeout = float(tempo)
        self._base_url = (base_url or _DEFAULT_BASE_URL).strip()

    def responder(self, mensagens: Sequence[ChatMessage], timeout: float | None = None) -> str:
        """Devolve o texto da resposta; qualquer falha sobe como ``ChatProviderError``."""
        try:
            from langchain_openai import ChatOpenAI

            modelo = ChatOpenAI(
                model=self._model,
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=timeout or self._timeout,
                max_retries=0,
            )
            resposta = modelo.invoke([(_PAPEIS[m.papel], m.conteudo) for m in mensagens])
            conteudo = resposta.content
            texto = conteudo if isinstance(conteudo, str) else str(conteudo)
        except Exception as erro:  # noqa: BLE001 — qualquer falha do SDK vira erro genérico
            # Só o tipo entra no log: mensagem e cabeçalhos podem ecoar a chave.
            logger.warning("Falha na chamada ao modelo de chat (%s).", type(erro).__name__)
            raise ChatProviderError(
                "Não foi possível obter a resposta do modelo de linguagem."
            ) from None
        if not texto.strip():
            raise ChatProviderError("O modelo de linguagem devolveu uma resposta vazia.")
        return texto
