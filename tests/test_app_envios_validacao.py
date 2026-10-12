"""Validações de entrada do envio (SPEC-0030): arquivos, papel e conexões.

Absorve os casos de upload da antiga ``POST /api/v1/bases`` (limites, travessia de
diretório, member) e da publicação (conexão desativada, outra equipe, tipo trocado).
"""

from __future__ import annotations

from tests._colecoes import MEMBER, OUTRA_EQUIPE, OWNER, enviar, md, preparar, texto_com_secoes
from tests._conexoes import criar_conexao_ok, payload_embeddings, payload_qdrant


def test_rejeita_envio_fora_dos_limites(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-002 NFR-001 AC-003"""
    ambiente = preparar(tmp_path, monkeypatch)
    demais = [md(f"doc{i}.md", "# titulo\nconteudo") for i in range(51)]

    resposta = enviar(ambiente, demais, nova="manuais", executar=False)

    assert resposta.status_code == 400
    assert "limite" in resposta.json()["detail"].lower()


def test_nome_de_arquivo_com_travessia_fica_dentro_do_storage(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-002 NFR-001 AC-003"""
    ambiente = preparar(tmp_path, monkeypatch)

    resposta = enviar(
        ambiente, [md("../../evil.md", "# conteudo malicioso")], nova="manuais", executar=False
    )

    assert resposta.status_code == 201, resposta.text
    assert not (tmp_path / "evil.md").exists(), "escreveu fora do storage (path traversal)"
    assert all(ambiente.pasta in arquivo.parents for arquivo in ambiente.pasta.rglob("*.md"))


def test_member_nao_envia_e_nada_e_guardado(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-015 NFR-001 AC-012"""
    ambiente = preparar(tmp_path, monkeypatch)

    resposta = enviar(
        ambiente, [md("a.md", texto_com_secoes(2))], nova="manuais", headers=MEMBER, executar=False
    )

    assert resposta.status_code == 403
    assert not list(ambiente.pasta.rglob("*.md"))


def test_arquivos_com_o_mesmo_nome_no_envio_sao_recusados(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-002 FR-004 AC-003"""
    ambiente = preparar(tmp_path, monkeypatch)

    resposta = enviar(
        ambiente,
        [md("a.md", texto_com_secoes(1)), md("a.md", texto_com_secoes(2))],
        nova="manuais",
        executar=False,
    )

    assert resposta.status_code == 422
    assert "Há arquivos com o mesmo nome neste envio." in resposta.text


def test_nome_de_colecao_invalido_e_recusado(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-001 AC-003"""
    ambiente = preparar(tmp_path, monkeypatch)

    for nome in ("   ", "x" * 81):
        resposta = enviar(ambiente, [md("a.md", texto_com_secoes(1))], nova=nome, executar=False)
        assert resposta.status_code in {422}, resposta.text


def test_conexao_desativada_de_outra_equipe_ou_de_tipo_trocado_e_recusada(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-003 NFR-001 AC-003"""
    ambiente = preparar(tmp_path, monkeypatch)
    client = ambiente.client
    arquivos = [md("a.md", texto_com_secoes(1))]

    de_outra_equipe = criar_conexao_ok(client, payload_qdrant(), headers=OUTRA_EQUIPE)
    resposta = client.post(
        "/api/v1/envios",
        data={
            "workspace_id": ambiente.workspace_id,
            "nova_colecao": "a",
            "conexao_embeddings_id": ambiente.embeddings_id,
            "conexao_vector_store_id": de_outra_equipe["id"],
        },
        files=arquivos,
        headers=OWNER,
    )
    assert resposta.status_code == 404

    tipo_trocado = client.post(
        "/api/v1/envios",
        data={
            "workspace_id": ambiente.workspace_id,
            "nova_colecao": "b",
            "conexao_embeddings_id": ambiente.qdrant_id,
            "conexao_vector_store_id": ambiente.embeddings_id,
        },
        files=arquivos,
        headers=OWNER,
    )
    assert tipo_trocado.status_code == 404

    desativada = criar_conexao_ok(client, payload_embeddings())
    client.post(f"/api/v1/conexoes/{desativada['id']}/desativar", headers=OWNER)
    resposta = client.post(
        "/api/v1/envios",
        data={
            "workspace_id": ambiente.workspace_id,
            "nova_colecao": "c",
            "conexao_embeddings_id": desativada["id"],
            "conexao_vector_store_id": ambiente.qdrant_id,
        },
        files=arquivos,
        headers=OWNER,
    )
    assert resposta.status_code == 409
    assert "desativada" in resposta.text


def test_envio_para_colecao_apagada_responde_404(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0030 US-001 FR-002 FR-011 AC-003"""
    ambiente = preparar(tmp_path, monkeypatch)
    resposta = enviar(ambiente, [md("a.md", texto_com_secoes(1))], nova="manuais")
    colecao_id = resposta.json()["colecao_id"]
    monkeypatch.setattr("src.pipeline.service.drop_collection", lambda *a, **k: None, raising=False)
    apagada = ambiente.client.request(
        "DELETE",
        f"/api/v1/colecoes/{colecao_id}",
        json={"confirmacao_nome": "manuais"},
        headers=OWNER,
    )
    assert apagada.status_code == 204

    novo = enviar(
        ambiente, [md("b.md", texto_com_secoes(1))], colecao_id=colecao_id, executar=False
    )

    assert novo.status_code == 404
    assert "A coleção não existe mais." in novo.text
