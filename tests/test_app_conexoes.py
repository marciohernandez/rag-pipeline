"""Conexões reutilizáveis de ingestão (SPEC-0026, US-001).

Fase RED: a API `/api/v1/conexoes`, os models `Conexao` e `EventoConexao` e a
cifra de segredos ainda não existem; cada caso afirma o Then do cenário.
"""

from __future__ import annotations

import pytest

from tests._conexoes import (
    ADMIN,
    CHAVE_EMBEDDINGS,
    CHAVE_NOVA,
    CHAVE_QDRANT,
    MASCARA,
    MEMBER,
    OUTRA_EQUIPE,
    OWNER,
    cliente,
    criar_base_vinculada,
    criar_conexao,
    criar_conexao_ok,
    criar_workspace,
    descrever_colecao,
    eventos_da_conexao,
    linha_da_conexao,
    payload_embeddings,
    payload_qdrant,
    publicar,
    storage_temporario,
)


def test_cadastrar_conexao_de_embeddings_openai_sem_devolver_a_chave() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 FR-002 FR-004 NFR-001 NFR-002 AC-001"""
    client = cliente()

    resposta = criar_conexao(client, payload_embeddings(nome="OpenAI principal"))

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["situacao"] == "ativa"
    assert corpo["tipo"] == "embeddings_openai"
    assert corpo["segredo_definido"] is True
    assert corpo["segredo_mascara"] == MASCARA
    assert CHAVE_EMBEDDINGS not in resposta.text
    linha = linha_da_conexao(corpo["id"])
    assert linha.segredo_cifrado
    assert CHAVE_EMBEDDINGS not in linha.segredo_cifrado
    assert eventos_da_conexao(corpo["id"]) == ["criada"]


def test_editar_conexao_preserva_ou_troca_a_chave_e_registra_eventos() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 FR-002 FR-004 NFR-001 AC-002"""
    client = cliente()
    conexao = criar_conexao_ok(client, payload_qdrant(nome="Qdrant produção"))
    cifrado_inicial = linha_da_conexao(conexao["id"]).segredo_cifrado

    renomeada = client.patch(
        f"/api/v1/conexoes/{conexao['id']}", json={"nome": "Qdrant renomeado"}, headers=ADMIN
    )
    cifrado_apos_nome = linha_da_conexao(conexao["id"]).segredo_cifrado
    trocada = client.patch(
        f"/api/v1/conexoes/{conexao['id']}", json={"segredo": CHAVE_NOVA}, headers=ADMIN
    )
    cifrado_apos_troca = linha_da_conexao(conexao["id"]).segredo_cifrado

    assert renomeada.status_code == 200, renomeada.text
    assert trocada.status_code == 200, trocada.text
    assert cifrado_apos_nome == cifrado_inicial
    assert cifrado_apos_troca != cifrado_inicial
    for texto in (renomeada.text, trocada.text):
        assert CHAVE_QDRANT not in texto
        assert CHAVE_NOVA not in texto
    assert eventos_da_conexao(conexao["id"]) == ["chave_trocada", "criada", "editada"]


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"configuracao": {"url": "ftp://qdrant.exemplo.com"}},
        {"configuracao": {"url": "https://usuario:senha@qdrant.exemplo.com"}},
        {"configuracao": {"url": "http://localhost:6333"}},
        {"configuracao": {"url": "http://169.254.169.254/latest"}},
        {"tipo": "pinecone"},
        {"nome": ""},
    ],
)
def test_recusar_conexao_invalida_sem_gravar_nada(alteracoes) -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 FR-002 NFR-002 AC-003"""
    client = cliente()

    resposta = criar_conexao(client, payload_qdrant(**alteracoes), ADMIN)

    assert resposta.status_code == 422, resposta.text
    assert CHAVE_QDRANT not in resposta.text
    listagem = client.get("/api/v1/conexoes", headers=ADMIN)
    assert listagem.status_code == 200
    assert listagem.json() == []


def test_dimensoes_invalidas_sao_recusadas() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-001 FR-002 NFR-002 AC-003"""
    client = cliente()

    resposta = criar_conexao(
        client,
        payload_embeddings(configuracao={"modelo": "text-embedding-3-small", "dimensoes": 0}),
    )

    assert resposta.status_code == 422, resposta.text
    assert client.get("/api/v1/conexoes", headers=OWNER).json() == []


def test_desativar_e_reativar_preserva_vinculos_e_bloqueia_a_publicacao(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0026 US-001 FR-003 FR-004 FR-008 NFR-002 AC-004"""
    client = cliente()
    storage_temporario(tmp_path, monkeypatch)
    descrever_colecao(monkeypatch, existe=False)
    embeddings = criar_conexao_ok(client, payload_embeddings())
    qdrant = criar_conexao_ok(client, payload_qdrant())
    base_id = criar_base_vinculada(embeddings["id"], qdrant["id"])

    desativada = client.post(f"/api/v1/conexoes/{embeddings['id']}/desativar", headers=OWNER)
    bloqueada = publicar(client, criar_workspace(client), embeddings["id"], qdrant["id"])
    reativada = client.post(f"/api/v1/conexoes/{embeddings['id']}/reativar", headers=OWNER)

    assert desativada.status_code == 200, desativada.text
    assert desativada.json()["situacao"] == "desativada"
    assert bloqueada.status_code == 409, bloqueada.text
    assert reativada.status_code == 200
    assert reativada.json()["situacao"] == "ativa"
    base = client.get(f"/api/v1/bases/{base_id}", headers=OWNER)
    assert base.status_code == 200
    assert eventos_da_conexao(embeddings["id"]) == ["criada", "desativada", "reativada"]


def test_excluir_somente_conexao_sem_uso() -> None:
    """SPECSFY: SPEC-0026 US-001 FR-003 FR-004 NFR-002 AC-005"""
    client = cliente()
    livre = criar_conexao_ok(client, payload_qdrant(nome="Livre"))
    embeddings = criar_conexao_ok(client, payload_embeddings())
    em_uso = criar_conexao_ok(client, payload_qdrant(nome="Em uso"))
    criar_base_vinculada(embeddings["id"], em_uso["id"])

    excluida = client.delete(f"/api/v1/conexoes/{livre['id']}", headers=OWNER)
    recusada = client.delete(f"/api/v1/conexoes/{em_uso['id']}", headers=OWNER)

    assert excluida.status_code == 204, excluida.text
    assert recusada.status_code == 409, recusada.text
    assert "1" in recusada.text
    assert client.get(f"/api/v1/conexoes/{em_uso['id']}", headers=OWNER).status_code == 200
    assert client.get(f"/api/v1/conexoes/{livre['id']}", headers=OWNER).status_code == 404
    assert eventos_da_conexao(livre["id"]) == ["criada", "excluida"]
    assert "excluida" not in eventos_da_conexao(em_uso["id"])


def test_member_e_outra_equipe_nao_alcancam_as_conexoes() -> None:
    """SPECSFY: SPEC-0026 US-001 US-004 FR-004 FR-012 NFR-002 AC-006"""
    client = cliente()
    conexao = criar_conexao_ok(client, payload_qdrant())
    caminho = f"/api/v1/conexoes/{conexao['id']}"

    respostas_member = [
        client.get("/api/v1/conexoes", headers=MEMBER),
        client.get(caminho, headers=MEMBER),
        criar_conexao(client, payload_qdrant(), MEMBER),
        client.patch(caminho, json={"nome": "x"}, headers=MEMBER),
        client.post(f"{caminho}/desativar", headers=MEMBER),
        client.delete(caminho, headers=MEMBER),
    ]
    respostas_outra = [
        client.get(caminho, headers=OUTRA_EQUIPE),
        client.patch(caminho, json={"nome": "x"}, headers=OUTRA_EQUIPE),
        client.post(f"{caminho}/desativar", headers=OUTRA_EQUIPE),
        client.delete(caminho, headers=OUTRA_EQUIPE),
    ]

    assert [r.status_code for r in respostas_member] == [403] * 6
    assert [r.status_code for r in respostas_outra] == [404] * 4
    assert client.get("/api/v1/conexoes", headers=OUTRA_EQUIPE).json() == []
