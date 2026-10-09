"""Nome físico da coleção igual ao nome digitado (SPEC-0030, atualização de 2026-10-09).

Fase RED: hoje o nome físico é ``col-<código>``, não há recusa de nome em uso ou
reservado e a exclusão física só confere o prefixo ``col-``.
"""

from __future__ import annotations

import pytest

from tests._colecoes import (
    OWNER,
    colecao_do_banco,
    criar_colecao,
    enviar,
    md,
    preparar,
    texto_com_secoes,
)
from tests._conexoes import criar_base_vinculada, criar_workspace


@pytest.mark.parametrize(
    ("digitado", "fisico"),
    [
        ("Teste-Vivo", "Teste-Vivo"),
        ("Manuais Técnicos 2026", "Manuais-Tecnicos-2026"),
        ("política/RH (v2)", "politica-RH-v2"),
    ],
)
def test_nome_fisico_e_o_slug_do_nome_digitado(digitado, fisico, tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-001 FR-010 FR-002 AC-023"""
    ambiente = preparar(tmp_path, monkeypatch)

    colecao_id = criar_colecao(ambiente, digitado)

    assert colecao_do_banco(colecao_id).nome_fisico == fisico
    assert ambiente.colecoes_fisicas == {fisico}
    renomeada = ambiente.client.patch(
        f"/api/v1/colecoes/{colecao_id}", json={"nome": "Outro nome"}, headers=OWNER
    )
    assert renomeada.status_code == 200, renomeada.text
    assert colecao_do_banco(colecao_id).nome_fisico == fisico


MENSAGEM_VAZIO = "O nome da coleção precisa ter ao menos uma letra ou número."
MENSAGEM_EM_USO = "Já existe uma coleção com esse nome no Qdrant desta conexão. Escolha outro nome."
MENSAGEM_RESERVADO = "Esse nome é reservado pelo sistema. Escolha outro nome."


@pytest.mark.parametrize(
    ("situacao", "status", "mensagem"),
    [
        ("slug_vazio", 422, MENSAGEM_VAZIO),
        ("em_uso_em_outro_workspace", 409, MENSAGEM_EM_USO),
        ("reservada_do_assistente", 409, MENSAGEM_RESERVADO),
        ("colecao_de_base_legada", 409, MENSAGEM_RESERVADO),
    ],
)
def test_nome_fisico_invalido_em_uso_ou_reservado_e_recusado(
    situacao, status, mensagem, tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-001 FR-003 NFR-004 AC-024"""
    from src.app.settings import get_settings

    ambiente = preparar(tmp_path, monkeypatch)
    criar_colecao(ambiente, "manuais")
    gravados_antes = len(ambiente.armazem.todos())
    outro_workspace = criar_workspace(ambiente.client)
    nome, workspace = {
        "slug_vazio": ("!!!", ambiente.workspace_id),
        "em_uso_em_outro_workspace": ("Manuais", outro_workspace),
        "reservada_do_assistente": (get_settings().conhecimento_collection, ambiente.workspace_id),
        "colecao_de_base_legada": ("produtos", ambiente.workspace_id),
    }[situacao]
    if situacao == "colecao_de_base_legada":
        criar_base_vinculada(ambiente.embeddings_id, ambiente.qdrant_id)
    ambiente.workspace_id = workspace

    resposta = enviar(ambiente, [md("b.md", texto_com_secoes(2))], nova=nome, executar=False)

    assert resposta.status_code == status, resposta.text
    assert mensagem in resposta.text
    assert len(ambiente.armazem.todos()) == gravados_antes
    listagem = ambiente.client.get(f"/api/v1/workspaces/{workspace}/colecoes", headers=OWNER)
    assert nome not in [c["nome"] for c in listagem.json()]


def test_exclusao_fisica_so_de_colecao_registrada(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-005 FR-011 NFR-001 NFR-004 AC-025"""
    from src.pipeline import indexing, service
    from src.pipeline.safety import SyncSafetyPolicy, UnsafeRemovalError

    politica = SyncSafetyPolicy()
    politica.assert_collection_drop_allowed("Teste-Vivo", ["Teste-Vivo"])
    for fora in ("rag_docs", "", "teste-vivo"):
        with pytest.raises(UnsafeRemovalError):
            politica.assert_collection_drop_allowed(fora, ["Teste-Vivo"])

    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "Teste-Vivo")
    chamadas: list[str] = []

    def construiria_cliente(*args, **kwargs):
        chamadas.append("cliente")
        raise AssertionError("o Qdrant não pode ser tocado para coleção não registrada")

    monkeypatch.setattr(indexing, "build_vector_store", construiria_cliente)
    config = {
        "projeto": {"nome": "x"},
        "embedding": {},
        "vector_store": {"collection_name": "rag_docs"},
    }
    with pytest.raises(UnsafeRemovalError):
        service.drop_collection(config, registradas=["Teste-Vivo"])
    assert chamadas == []

    apagadas: list[str] = []
    monkeypatch.setattr(
        service,
        "drop_collection",
        lambda cfg, **kw: apagadas.append(cfg["vector_store"]["collection_name"]),
    )
    resposta = ambiente.client.request(
        "DELETE",
        f"/api/v1/colecoes/{colecao_id}",
        json={"confirmacao_nome": "Teste-Vivo"},
        headers=OWNER,
    )
    assert resposta.status_code == 204, resposta.text
    assert apagadas == ["Teste-Vivo"]
    de_novo = enviar(ambiente, [md("a.md", texto_com_secoes(2))], nova="Teste-Vivo", executar=False)
    assert de_novo.status_code == 201, de_novo.text
