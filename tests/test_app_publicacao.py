"""Publicação com conexões escolhidas (SPEC-0026, US-003).

Fase RED: `POST /api/v1/bases` ainda não aceita conexões, parâmetros de divisão
nem `iniciar_execucao`, e a fachada ainda não tem `describe_collection`.
"""

from __future__ import annotations

from tests._conexoes import (
    ADMIN,
    MEMBER,
    OUTRA_EQUIPE,
    OWNER,
    capturar_agendamento,
    cliente,
    contar,
    criar_conexao_ok,
    criar_workspace,
    descrever_colecao,
    payload_embeddings,
    payload_qdrant,
    publicar,
    storage_temporario,
)
from tests._pessoas import sessao_do_banco


def _par_de_conexoes(client, dimensoes: int = 1536) -> tuple[dict, dict]:
    embeddings = criar_conexao_ok(
        client,
        payload_embeddings(
            configuracao={"modelo": "text-embedding-3-small", "dimensoes": dimensoes}
        ),
    )
    qdrant = criar_conexao_ok(client, payload_qdrant())
    return embeddings, qdrant


def test_publicar_base_com_conexoes_ativas_cria_base_e_execucao(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-003 FR-007 FR-008 FR-009 FR-010 FR-011 NFR-005 AC-010"""
    client = cliente()
    storage_temporario(tmp_path, monkeypatch)
    descrever_colecao(monkeypatch, existe=False)
    agendamentos = capturar_agendamento(monkeypatch)
    embeddings, qdrant = _par_de_conexoes(client)
    workspace_id = criar_workspace(client)

    resposta = publicar(client, workspace_id, embeddings["id"], qdrant["id"])

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["base_id"]
    assert corpo["execution_id"]
    from src.app.models import Base

    with sessao_do_banco() as sessao:
        base = sessao.get(Base, corpo["base_id"])
        assert base.conexao_embeddings_id == embeddings["id"]
        assert base.conexao_vector_store_id == qdrant["id"]
        assert base.chunking == {"splitter": "header", "chunk_size": 800, "chunk_overlap": 100}
        assert base.collection_name == "produtos"
    assert len(agendamentos) == 1
    execucao = client.get(f"/api/v1/executions/{corpo['execution_id']}", headers=OWNER)
    assert execucao.status_code == 200
    assert {"previstos", "inseridos", "mantidos", "removidos"} <= set(execucao.json())


def test_dimensao_divergente_bloqueia_sem_gravar_nada(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-003 FR-008 FR-009 NFR-002 AC-011"""
    client = cliente()
    pasta = storage_temporario(tmp_path, monkeypatch)
    descrever_colecao(monkeypatch, existe=True, dimensoes=3072)
    agendamentos = capturar_agendamento(monkeypatch)
    embeddings, qdrant = _par_de_conexoes(client, dimensoes=1536)
    workspace_id = criar_workspace(client)
    bases_antes, execucoes_antes = contar("Base"), contar("Execution")

    resposta = publicar(client, workspace_id, embeddings["id"], qdrant["id"])

    assert resposta.status_code == 409, resposta.text
    assert "3072" in resposta.text
    assert "1536" in resposta.text
    assert contar("Base") == bases_antes
    assert contar("Execution") == execucoes_antes
    assert agendamentos == []
    assert not pasta.exists() or list(pasta.iterdir()) == []


def test_colecao_inexistente_e_aceita_com_a_dimensao_declarada(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-003 FR-008 FR-009 NFR-002 AC-011"""
    client = cliente()
    storage_temporario(tmp_path, monkeypatch)
    descrever_colecao(monkeypatch, existe=False)
    capturar_agendamento(monkeypatch)
    embeddings, qdrant = _par_de_conexoes(client)

    resposta = publicar(client, criar_workspace(client), embeddings["id"], qdrant["id"])

    assert resposta.status_code == 201, resposta.text


def test_conexao_desativada_de_outra_equipe_ou_de_tipo_trocado_e_recusada(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0026 US-003 FR-003 FR-008 FR-009 FR-011 NFR-002 AC-012"""
    client = cliente()
    storage_temporario(tmp_path, monkeypatch)
    descrever_colecao(monkeypatch, existe=False)
    capturar_agendamento(monkeypatch)
    embeddings, qdrant = _par_de_conexoes(client)
    workspace_id = criar_workspace(client)
    de_outra_equipe = criar_conexao_ok(client, payload_qdrant(), OUTRA_EQUIPE)
    bases_antes = contar("Base")

    client.post(f"/api/v1/conexoes/{embeddings['id']}/desativar", headers=OWNER)
    desativada = publicar(client, workspace_id, embeddings["id"], qdrant["id"], headers=ADMIN)
    client.post(f"/api/v1/conexoes/{embeddings['id']}/reativar", headers=OWNER)
    outra_equipe = publicar(client, workspace_id, embeddings["id"], de_outra_equipe["id"])
    tipo_trocado = publicar(client, workspace_id, qdrant["id"], embeddings["id"])

    assert desativada.status_code == 409, desativada.text
    assert outra_equipe.status_code == 404, outra_equipe.text
    assert tipo_trocado.status_code == 404, tipo_trocado.text
    assert contar("Base") == bases_antes


def test_verificar_dimensao_antes_de_publicar_sem_criar_nada(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-003 FR-008 FR-009 NFR-002 AC-011"""
    client = cliente()
    storage_temporario(tmp_path, monkeypatch)
    embeddings, qdrant = _par_de_conexoes(client, dimensoes=1536)
    consulta = {
        "conexao_embeddings_id": embeddings["id"],
        "conexao_vector_store_id": qdrant["id"],
        "collection_name": "produtos",
    }
    bases_antes = contar("Base")

    descrever_colecao(monkeypatch, existe=True, dimensoes=3072)
    divergente = client.get("/api/v1/ingestao/dimensao", params=consulta, headers=OWNER)
    descrever_colecao(monkeypatch, existe=False)
    inexistente = client.get("/api/v1/ingestao/dimensao", params=consulta, headers=OWNER)
    negada = client.get("/api/v1/ingestao/dimensao", params=consulta, headers=MEMBER)

    assert divergente.status_code == 200, divergente.text
    assert divergente.json() == {"embeddings": 1536, "colecao": 3072, "compativel": False}
    assert inexistente.json() == {"embeddings": 1536, "colecao": None, "compativel": True}
    assert negada.status_code == 403
    assert contar("Base") == bases_antes
