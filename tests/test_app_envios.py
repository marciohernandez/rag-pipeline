"""Envio de documentos para coleções (SPEC-0030, AC-001 e AC-003).

Fase RED: ``POST /api/v1/envios`` e as coleções por Workspace ainda não existem.
"""

from __future__ import annotations

import json

import pytest

from tests._colecoes import (
    OWNER,
    colecao_do_banco,
    criar_colecao,
    documentos,
    enviar,
    md,
    preparar,
    texto_com_secoes,
)
from tests._conexoes import criar_conexao_ok, payload_embeddings
from tests._pessoas import sessao_do_banco


def test_primeiro_envio_cria_colecao_com_conexoes_e_sem_sync_mode(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-001 FR-002 FR-003 FR-006 FR-007 FR-015 AC-001"""
    ambiente = preparar(tmp_path, monkeypatch)

    resposta = enviar(ambiente, [md("a.md", texto_com_secoes(2))], nova="manuais")

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert {"envio_id", "colecao_id"} <= set(corpo)
    listagem = ambiente.client.get(
        f"/api/v1/workspaces/{ambiente.workspace_id}/colecoes", headers=OWNER
    )
    assert listagem.status_code == 200, listagem.text
    assert [(c["nome"], c["documentos"]) for c in listagem.json()] == [("manuais", 1)]
    colecao = colecao_do_banco(corpo["colecao_id"])
    assert colecao.conexao_embeddings_id == ambiente.embeddings_id
    assert colecao.conexao_vector_store_id == ambiente.qdrant_id
    assert colecao.nome_fisico.startswith("col-")
    envio = ambiente.client.get(f"/api/v1/envios/{corpo['envio_id']}", headers=OWNER).json()
    assert "header" in json.dumps(envio["processamento"])
    assert "sync_mode" not in json.dumps(envio)
    assert [d["nome_arquivo"] for d in documentos(ambiente, corpo["colecao_id"])] == ["a.md"]


NOME_DUPLICADO = "Já existe uma coleção com esse nome neste Workspace."
CONEXOES_FIXAS = "A coleção usa conexões fixas; envie sem trocar as conexões."
DIMENSOES = "Dimensões incompatíveis: modelo 3072, coleção 1536."
SYNC_MODE = "Modo de sincronização não é aceito no envio."


@pytest.mark.parametrize(
    ("situacao", "status", "mensagem"),
    [
        ("nome_duplicado", 409, NOME_DUPLICADO),
        ("outra_conexao", 422, CONEXOES_FIXAS),
        ("outra_dimensao", 422, DIMENSOES),
        ("sync_mode", 422, SYNC_MODE),
    ],
)
def test_envio_invalido_e_recusado_antes_de_gravar(
    situacao, status, mensagem, tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-001 FR-003 FR-007 NFR-004 AC-003"""
    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "manuais")
    registros_antes = len(ambiente.armazem.todos())
    agendamentos_antes = len(ambiente.agendamentos)
    arquivos = [md("novo.md", texto_com_secoes(2, "v9"))]

    if situacao == "nome_duplicado":
        resposta = enviar(ambiente, arquivos, nova="Manuais", executar=False)
    elif situacao == "outra_conexao":
        outra = criar_conexao_ok(ambiente.client, payload_embeddings())["id"]
        resposta = enviar(
            ambiente,
            arquivos,
            colecao_id=colecao_id,
            conexao_embeddings_id=outra,
            executar=False,
        )
    elif situacao == "outra_dimensao":
        from src.app.models import Conexao

        with sessao_do_banco() as sessao:
            conexao = sessao.get(Conexao, ambiente.embeddings_id)
            conexao.configuracao = {"modelo": "text-embedding-3-large", "dimensoes": 3072}
            sessao.commit()
        resposta = enviar(ambiente, arquivos, colecao_id=colecao_id, executar=False)
    else:
        resposta = enviar(
            ambiente, arquivos, colecao_id=colecao_id, sync_mode="mirror", executar=False
        )

    assert resposta.status_code == status, resposta.text
    assert mensagem in resposta.text
    assert [d["nome_arquivo"] for d in documentos(ambiente, colecao_id)] == ["a.md"]
    assert len(ambiente.armazem.todos()) == registros_antes
    assert len(ambiente.agendamentos) == agendamentos_antes
