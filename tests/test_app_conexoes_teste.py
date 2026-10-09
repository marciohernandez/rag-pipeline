"""Teste da conexão ao salvar, como nas credenciais do n8n (SPEC-0029, US-005).

Fase RED: criar ou editar uma conexão não testa o acesso e a resposta não traz
``teste``. O cliente do Qdrant e o adapter de embeddings são substituídos: nenhum
caso faz rede.
"""

from __future__ import annotations

import logging

from tests._conexoes import (
    CHAVE_EMBEDDINGS,
    CHAVE_QDRANT,
    OWNER,
    cliente,
    criar_conexao,
    payload_embeddings,
    payload_qdrant,
)


def _qdrant_respondendo(monkeypatch, erro: Exception | None) -> None:
    def get_collections(self):
        if erro is not None:
            raise erro
        return type("Resposta", (), {"collections": []})()

    monkeypatch.setattr("qdrant_client.QdrantClient.get_collections", get_collections)


def _resposta_401() -> Exception:
    from qdrant_client.http.exceptions import UnexpectedResponse

    return UnexpectedResponse(
        status_code=401,
        reason_phrase="Unauthorized",
        content=b"Must provide an API key or an Authorization bearer token",
        headers={},
    )


def _embeddings_devolvendo(monkeypatch, dimensoes: int) -> None:
    class _Adapter:
        def embed_documents(self, textos):
            return [[0.1] * dimensoes for _ in textos]

        def embed_query(self, texto):
            return [0.1] * dimensoes

    monkeypatch.setattr("src.pipeline.indexing.build_embeddings", lambda *a, **k: _Adapter())


def test_qdrant_sem_chave_salva_com_teste_falho(monkeypatch, caplog) -> None:
    """SPECSFY: SPEC-0029 US-005 FR-009 NFR-001 AC-019"""
    client = cliente()
    _qdrant_respondendo(monkeypatch, _resposta_401())

    with caplog.at_level(logging.DEBUG):
        resposta = criar_conexao(client, payload_qdrant(segredo=None))

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["teste"]["sucesso"] is False
    assert corpo["teste"]["mensagem"] == "O servidor exige uma chave de API."
    assert client.get(f"/api/v1/conexoes/{corpo['id']}", headers=OWNER).status_code == 200
    assert CHAVE_QDRANT not in resposta.text and CHAVE_QDRANT not in caplog.text


def test_embeddings_testa_e_confere_dimensao(monkeypatch, caplog) -> None:
    """SPECSFY: SPEC-0029 US-005 FR-009 NFR-001 AC-020"""
    client = cliente()
    _embeddings_devolvendo(monkeypatch, 1536)

    with caplog.at_level(logging.DEBUG):
        criada = criar_conexao(client, payload_embeddings())
        assert criada.status_code == 201, criada.text
        editada = client.patch(
            f"/api/v1/conexoes/{criada.json()['id']}",
            json={"configuracao": {"modelo": "text-embedding-3-small", "dimensoes": 3072}},
            headers=OWNER,
        )

    assert criada.json()["teste"] == {
        "sucesso": True,
        "mensagem": "Conexão testada com sucesso.",
        "dimensoes": 1536,
    }
    assert editada.status_code == 200, editada.text
    assert editada.json()["teste"]["sucesso"] is False
    assert (
        editada.json()["teste"]["mensagem"]
        == "O modelo devolveu 1536 dimensões; a conexão declara 3072."
    )
    for texto in (criada.text, editada.text, caplog.text):
        assert CHAVE_EMBEDDINGS not in texto


def test_servidor_inalcancavel_falha_no_tempo_limite(monkeypatch, caplog) -> None:
    """SPECSFY: SPEC-0029 US-005 FR-009 NFR-001 AC-021"""
    import httpx

    client = cliente()
    _qdrant_respondendo(
        monkeypatch, httpx.ConnectError(f"falha ao conectar com chave {CHAVE_QDRANT}")
    )

    with caplog.at_level(logging.DEBUG):
        resposta = criar_conexao(client, payload_qdrant())

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["teste"]["sucesso"] is False
    assert resposta.json()["teste"]["mensagem"] == "Não foi possível alcançar o servidor."
    assert CHAVE_QDRANT not in resposta.text and CHAVE_QDRANT not in caplog.text
