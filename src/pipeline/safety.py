"""Política fail-closed para sincronizações em destinos vetoriais."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


class SyncSafetyError(ValueError):
    """Erro base para violações da política de sincronização."""


class DestructiveOptionError(SyncSafetyError):
    """Uma opção destrutiva obsoleta foi solicitada."""


class UnsupportedSyncModeError(SyncSafetyError):
    """O provider não oferece as garantias exigidas pelo modo solicitado."""


class InvalidSyncScopeError(SyncSafetyError):
    """Os chunks não formam um escopo lógico seguro e inequívoco."""


class UnsafeRemovalError(SyncSafetyError):
    """O destino não comprovou que uma remoção pode prosseguir."""


class SyncSafetyPolicy:
    """Centraliza as guardas obrigatórias antes de mutações remotas."""

    _SUPPORTED_PROVIDERS = frozenset({"qdrant"})
    _SUPPORTED_MODES = frozenset({"append", "mirror"})
    _MIRROR_PROVIDERS = frozenset({"qdrant"})

    def reject_destructive_option(self, requested: bool) -> None:
        """Rejeita a opção antiga e orienta o fluxo seguro de recuperação."""
        if requested:
            raise DestructiveOptionError(
                "A opção --recreate foi desativada. Use a sincronização "
                "idempotente para atualizar ou recuperar a base."
            )

    def assert_sync_mode_supported(self, provider: str, sync_mode: str) -> None:
        """Valida provider e modo antes da criação de qualquer cliente."""
        normalized_provider = self._normalized_token(provider)
        normalized_mode = self._normalized_token(sync_mode)

        if normalized_provider not in self._SUPPORTED_PROVIDERS:
            raise UnsupportedSyncModeError(
                f"Provider não suportado para sincronização: {provider!r}."
            )
        if normalized_mode not in self._SUPPORTED_MODES:
            raise UnsupportedSyncModeError(
                f"Modo de sincronização não suportado: {sync_mode!r}."
            )
        if (
            normalized_mode == "mirror"
            and normalized_provider not in self._MIRROR_PROVIDERS
        ):
            raise UnsupportedSyncModeError(
                "O modo espelho exige garantia de escopo e está disponível "
                "somente para o provider qdrant; use o modo append."
            )

    def assert_valid_scope(self, chunks: Sequence[Any]) -> tuple[str, str | None]:
        """Valida IDs obrigatórios e retorna ``(project_id, tenant_id)`` do lote.

        ``tenant_id`` é opcional, mas estrito quando presente: a totalidade do
        lote precisa declarar o mesmo valor, ou nenhum chunk declara. Um
        ``tenant_id`` vazio ou apenas espaços é tratado como ausente, pela
        mesma normalização usada em ``project_id`` e ``chunk_id``.
        """
        if not chunks:
            raise InvalidSyncScopeError(
                "O conjunto esperado de chunks está vazio; sincronização bloqueada."
            )

        project_ids: set[str] = set()
        tenant_ids: set[str] = set()
        lote_sem_tenant = False
        chunk_ids: list[str] = []
        for chunk in chunks:
            metadata = getattr(chunk, "metadata", None)
            if not isinstance(metadata, Mapping):
                raise InvalidSyncScopeError("Chunk sem metadata válida.")

            project_id = self._clean_identifier(metadata.get("project_id"))
            chunk_id = self._clean_identifier(metadata.get("chunk_id"))
            tenant_id = self._clean_identifier(metadata.get("tenant_id"))
            if not project_id:
                raise InvalidSyncScopeError("Chunk com project_id ausente ou vazio.")
            if not chunk_id:
                raise InvalidSyncScopeError("Chunk com chunk_id ausente ou vazio.")

            project_ids.add(project_id)
            chunk_ids.append(chunk_id)
            if tenant_id:
                tenant_ids.add(tenant_id)
            else:
                lote_sem_tenant = True

        if len(project_ids) != 1:
            raise InvalidSyncScopeError(
                "Os chunks possuem project_id divergentes; sincronização bloqueada."
            )
        if len(chunk_ids) != len(set(chunk_ids)):
            raise InvalidSyncScopeError(
                "O escopo contém chunk_id duplicado; sincronização bloqueada."
            )
        if tenant_ids and lote_sem_tenant:
            raise InvalidSyncScopeError(
                "O lote mistura chunks com e sem tenant_id; sincronização "
                "bloqueada."
            )
        if len(tenant_ids) > 1:
            raise InvalidSyncScopeError(
                "Os chunks possuem tenant_id divergentes; sincronização "
                "bloqueada."
            )

        tenant_id_resolvido = next(iter(tenant_ids)) if tenant_ids else None
        return next(iter(project_ids)), tenant_id_resolvido

    def assert_removal_allowed(
        self, expected_ids: Iterable[str], confirmed_ids: Iterable[str]
    ) -> None:
        """Libera remoção somente após confirmar todos os pontos esperados."""
        expected = {self._clean_identifier(item) for item in expected_ids}
        expected.discard("")
        if not expected:
            raise UnsafeRemovalError(
                "O conjunto esperado está vazio; nenhuma remoção é permitida."
            )

        confirmed = {self._clean_identifier(item) for item in confirmed_ids}
        confirmed.discard("")
        missing = expected - confirmed
        if missing:
            raise UnsafeRemovalError(
                "A remoção foi bloqueada porque o destino não confirmou todos "
                f"os pontos esperados (esperados={len(expected)}, "
                f"confirmados={len(expected - missing)})."
            )

    @staticmethod
    def _normalized_token(value: object) -> str:
        return value.strip().lower() if isinstance(value, str) else ""

    @staticmethod
    def _clean_identifier(value: object) -> str:
        return value.strip() if isinstance(value, str) else ""
