"""Hierarquia de erros da camada de providers (SPEC-0003).

Todos os erros locais herdam de :class:`ProviderError`, o que permite aos
consumidores tratarem a fronteira inteira sem conhecer o SDK concreto. Nenhum
destes erros implica acesso remoto: eles são levantados durante a validação
local, antes de qualquer cliente ser criado.
"""

from __future__ import annotations

# Reexportados da política central da SPEC-0001: a camada de providers oferece
# uma fachada única de erros sem duplicar a definição em `src/pipeline/safety.py`.
from src.pipeline.safety import (  # noqa: F401
    SyncSafetyError,
    UnsafeRemovalError,
    UnsupportedSyncModeError,
)


class ProviderError(Exception):
    """Erro base de qualquer provider de embeddings ou vector store."""


# As bases adicionais preservam o contrato observável do `src/pipeline/embedder.py`
# anterior (NFR-004): nome, configuração e escopo inválidos continuam sendo
# `ValueError`, e credencial ausente continua sendo `EnvironmentError`.


class UnknownProviderError(ProviderError, ValueError):
    """A factory recebeu um nome que não corresponde a nenhum adapter."""


class InvalidProviderConfigError(ProviderError, ValueError):
    """A configuração local do adapter está incompleta ou malformada."""


class MissingCredentialError(ProviderError, EnvironmentError):
    """Uma credencial obrigatória não foi encontrada na configuração/ambiente."""


class ChatProviderError(ProviderError):
    """O modelo de linguagem falhou ou excedeu o tempo limite.

    A mensagem é sempre genérica: nunca carrega detalhe do provedor nem
    credencial (SPEC-0021, FR-010).
    """


class InvalidScopeError(ProviderError, ValueError):
    """O escopo lógico de recuperação é inválido (ex.: ``project_id`` ausente)."""


class LegacyDestinationError(ProviderError):
    """O destino contém identidades incompatíveis; use um destino novo."""


class UnreliableScopeReadError(ProviderError):
    """A releitura de IDs do escopo não pôde ser concluída de forma confiável."""
