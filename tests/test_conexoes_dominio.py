"""Regras de domínio das conexões de ingestão (SPEC-0026, T022).

Unidade pura: sem banco e sem HTTP. Os cenários HTTP equivalentes ficam em
``tests/test_app_conexoes.py`` e ficam verdes na T024.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet

from src.app import conexoes
from src.app.conexoes import ErroDeConexao

CHAVE = Fernet.generate_key().decode()
SEGREDO = "sk-spec0026-unidade-1234"


@pytest.mark.parametrize(
    "url",
    [
        "ftp://qdrant.exemplo.com",
        "https://usuario:senha@qdrant.exemplo.com",
        "http://localhost:6333",
        "http://127.0.0.1:6333",
        "http://[::1]:6333",
        "http://169.254.169.254/latest/meta-data",
        "http://metadata.google.internal/",
        "http://0.0.0.0:6333",
        "qdrant.exemplo.com",
        "",
    ],
)
def test_url_invalida_ou_interna_e_recusada(url) -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 NFR-002 AC-003"""
    with pytest.raises(ErroDeConexao):
        conexoes.validar_url(url)


def test_url_publica_ou_de_rede_interna_do_swarm_e_aceita() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 NFR-002 AC-001"""
    assert (
        conexoes.validar_url("https://qdrant.exemplo.com:6333") == "https://qdrant.exemplo.com:6333"
    )
    assert conexoes.validar_url("http://qdrant:6333") == "http://qdrant:6333"
    assert conexoes.validar_url("http://10.0.0.5:6333") == "http://10.0.0.5:6333"
    assert conexoes.validar_url("http://localhost:6333", permitir_locais=True)


def test_configuracao_de_embeddings_aplica_padroes_e_recusa_dimensoes_invalidas() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 FR-002 NFR-002 AC-003"""
    padrao = conexoes.validar_configuracao("embeddings_openai", {})
    assert padrao == {"modelo": "text-embedding-3-small", "dimensoes": 1536}
    for dimensoes in (0, -1, True, "1536", 20001):
        with pytest.raises(ErroDeConexao):
            conexoes.validar_configuracao("embeddings_openai", {"dimensoes": dimensoes})
    with pytest.raises(ErroDeConexao):
        conexoes.validar_configuracao("qdrant", {"url": "https://q.exemplo.com", "extra": 1})
    with pytest.raises(ErroDeConexao):
        conexoes.validar_tipo("pinecone")


def test_nome_e_obrigatorio_e_limitado() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 FR-002 NFR-002 AC-003"""
    assert conexoes.validar_nome("  OpenAI  ") == "OpenAI"
    for nome in ("", "   ", None, "x" * 81):
        with pytest.raises(ErroDeConexao):
            conexoes.validar_nome(nome)


def test_cifra_nao_guarda_em_claro_e_decifra_somente_com_a_mesma_chave() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 FR-002 NFR-001 AC-001 AC-002"""
    texto = conexoes.cifrar_segredo(CHAVE, SEGREDO)

    assert SEGREDO not in texto
    assert conexoes.decifrar_segredo(CHAVE, texto) == SEGREDO
    with pytest.raises(ErroDeConexao) as erro:
        conexoes.decifrar_segredo(Fernet.generate_key().decode(), texto)
    assert erro.value.status_code == 503
    assert SEGREDO not in erro.value.detalhe
    with pytest.raises(ErroDeConexao):
        conexoes.cifrar_segredo("", SEGREDO)
    with pytest.raises(ErroDeConexao):
        conexoes.cifrar_segredo("nao-e-uma-chave", SEGREDO)


def test_serializacao_publica_nunca_devolve_a_chave() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 FR-002 NFR-001 AC-001 AC-002"""
    conexao = SimpleNamespace(
        id="c-1",
        nome="OpenAI",
        tipo="embeddings_openai",
        situacao="ativa",
        configuracao={"modelo": "m", "dimensoes": 8},
        criado_por=None,
        segredo_cifrado=conexoes.cifrar_segredo(CHAVE, SEGREDO),
        criado_em=None,
        atualizada_em=None,
    )
    sem_chave = SimpleNamespace(**{**vars(conexao), "segredo_cifrado": None})

    publica = conexoes.serializar_conexao(conexao, 2)

    assert publica["segredo_definido"] is True
    assert publica["segredo_mascara"] == conexoes.MASCARA
    assert publica["em_uso"] == 2
    assert SEGREDO not in str(publica) and "segredo_cifrado" not in publica
    assert conexoes.serializar_conexao(sem_chave, 0)["segredo_mascara"] == ""


def test_configuracao_do_pipeline_revalida_a_url_e_leva_a_chave_so_em_memoria() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 FR-002 NFR-001 NFR-002 AC-001 AC-003"""
    embeddings = conexoes.configuracao_para_pipeline(
        "embeddings_openai",
        {"modelo": "m", "dimensoes": 8, "url_base": "https://api.exemplo.com/v1"},
        SEGREDO,
    )
    qdrant = conexoes.configuracao_para_pipeline(
        "qdrant", {"url": "https://q.exemplo.com"}, None, collection_name="produtos"
    )

    assert embeddings == {
        "provider": "openai",
        "model": "m",
        "dimensions": 8,
        "base_url": "https://api.exemplo.com/v1",
        "api_key": SEGREDO,
    }
    assert qdrant == {
        "provider": "qdrant",
        "url": "https://q.exemplo.com",
        "collection_name": "produtos",
    }
    with pytest.raises(ErroDeConexao):
        conexoes.configuracao_para_pipeline("qdrant", {"url": "http://169.254.169.254"}, None)
