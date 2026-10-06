"""Configuração padrão do backend de aplicação (SPEC-0012).

Regressão registrada na seção 16 da SPEC-0012 e fechada em 2026-09-07: o padrão
de `APP_VECTOR_STORE_PROVIDER` era `in_memory`, provider que `SyncSafetyPolicy`
recusa para escrita. Uma instalação sem a variável definida subia normalmente e
só falhava dentro da tarefa em segundo plano, com o erro genérico de
`process_base_task` — nenhuma execução real conseguia concluir.
"""

from __future__ import annotations

import pytest


def _app_settings(monkeypatch, **ambiente: str):
    from src.app.main import _app_settings as construir

    for chave in (
        "APP_VECTOR_STORE_PROVIDER",
        "APP_VECTOR_STORE_COLLECTION",
        "APP_EMBEDDING_PROVIDER",
        "APP_EMBEDDING_DIMENSIONS",
    ):
        monkeypatch.delenv(chave, raising=False)
    for chave, valor in ambiente.items():
        monkeypatch.setenv(chave, valor)
    return construir()


def test_provider_padrao_do_vector_store_aceita_escrita(monkeypatch) -> None:
    """SPECSFY: US-001 FR-001

    O padrão precisa ser um provider que a política de segurança aceite
    sincronizar; caso contrário a configuração padrão nunca conclui uma
    execução.
    """
    from src.pipeline.safety import SyncSafetyPolicy

    settings = _app_settings(monkeypatch)
    provider = settings.vector_store["provider"]

    assert provider == "qdrant"
    # Não levanta: a política aceita este provider para sincronizar em mirror.
    SyncSafetyPolicy().assert_sync_mode_supported(provider, "mirror")


def test_provider_do_vector_store_continua_configuravel(monkeypatch) -> None:
    """SPECSFY: US-001 FR-001

    O padrão muda, mas a escolha explícita continua respeitada — inclusive
    `in_memory`, para leitura/demonstração local.
    """
    settings = _app_settings(monkeypatch, APP_VECTOR_STORE_PROVIDER="in_memory")

    assert settings.vector_store["provider"] == "in_memory"


def test_provider_in_memory_continua_recusado_para_escrita() -> None:
    """SPECSFY: US-001 FR-001

    Contraprova do primeiro caso: `in_memory` continua barrado pela política,
    e é por isso que ele não serve como padrão.
    """
    from src.pipeline.safety import SyncSafetyPolicy, UnsupportedSyncModeError

    with pytest.raises(UnsupportedSyncModeError):
        SyncSafetyPolicy().assert_sync_mode_supported("in_memory", "mirror")


def test_chave_de_cifra_das_conexoes_vem_do_arquivo_ou_da_variavel(monkeypatch, tmp_path) -> None:
    """SPECSFY: SPEC-0026 FR-002 NFR-001 NFR-005 AC-001 AC-013"""
    segredo = tmp_path / "conexoes_chave"
    segredo.write_text("chave-do-arquivo\n", encoding="utf-8")
    monkeypatch.delenv("APP_CONEXOES_CHAVE_FILE", raising=False)

    da_variavel = _app_settings(monkeypatch, APP_CONEXOES_CHAVE="chave-da-variavel")
    do_arquivo = _app_settings(
        monkeypatch, APP_CONEXOES_CHAVE="ignorada", APP_CONEXOES_CHAVE_FILE=str(segredo)
    )
    monkeypatch.delenv("APP_CONEXOES_CHAVE_FILE")
    ausente = _app_settings(monkeypatch, APP_CONEXOES_CHAVE="")

    assert da_variavel.conexoes_chave == "chave-da-variavel"
    assert do_arquivo.conexoes_chave == "chave-do-arquivo"
    assert ausente.conexoes_chave == ""
    assert "chave-do-arquivo" not in repr(do_arquivo)
