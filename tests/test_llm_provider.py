"""Testes do contrato neutro de chat, do adapter e da factory (SPEC-0021)."""

from __future__ import annotations

import socket
import threading
import time

import pytest

from tests._assistente import exigir


def _config(**alteracoes) -> dict:
    base = {
        "model": "modelo-de-teste",
        "api_key": "sk-chave-secreta-123",
        "timeout": 30,
        "base_url": "http://127.0.0.1:9/v1",
    }
    base.update(alteracoes)
    return base


def test_chamada_ao_modelo_respeita_timeout_configurado() -> None:
    """SPECSFY: SPEC-0021 FR-010 FR-012 NFR-002 AC-020"""
    fabrica = exigir("src.pipeline.providers.factory", "ProviderFactory")
    mensagem = exigir("src.pipeline.providers.contracts", "ChatMessage")
    erro_base = exigir("src.pipeline.providers.errors", "ProviderError")

    servidor = socket.socket()
    servidor.bind(("127.0.0.1", 0))
    servidor.listen(1)
    conexoes: list[socket.socket] = []

    def aceitar_e_calar() -> None:  # provedor que aceita a conexão e nunca responde
        try:
            conn, _ = servidor.accept()
            conexoes.append(conn)
        except OSError:
            pass

    threading.Thread(target=aceitar_e_calar, daemon=True).start()
    porta = servidor.getsockname()[1]
    try:
        adapter = fabrica.create_chat_model(
            "openrouter", _config(timeout=0.5, base_url=f"http://127.0.0.1:{porta}/v1")
        )
        inicio = time.monotonic()
        with pytest.raises(erro_base) as info:
            adapter.responder([mensagem("pessoa", "olá")], 0.5)
        assert time.monotonic() - inicio < 10, "a chamada não foi interrompida pelo limite de tempo"
        assert "sk-chave-secreta-123" not in str(info.value)
    finally:
        for conn in conexoes:
            conn.close()
        servidor.close()


def test_factory_resolve_adapter_neutro_e_valida_configuracao() -> None:
    """SPECSFY: SPEC-0021 FR-012 FR-005 NFR-002 AC-023"""
    fabrica = exigir("src.pipeline.providers.factory", "ProviderFactory")
    invalido = exigir("src.pipeline.providers.errors", "InvalidProviderConfigError")
    desconhecido = exigir("src.pipeline.providers.errors", "UnknownProviderError")

    adapter = fabrica.create_chat_model("openrouter", _config())
    assert callable(getattr(adapter, "responder", None))

    with pytest.raises(invalido) as sem_modelo:
        fabrica.create_chat_model("openrouter", _config(model=""))
    assert "model" in str(sem_modelo.value)
    assert "sk-chave-secreta-123" not in str(sem_modelo.value)

    with pytest.raises(Exception) as sem_chave:
        fabrica.create_chat_model("openrouter", _config(api_key=""))
    assert "api_key" in str(sem_chave.value).lower() or "chave" in str(sem_chave.value).lower()

    with pytest.raises(desconhecido):
        fabrica.create_chat_model("provedor-que-nao-existe", _config())
