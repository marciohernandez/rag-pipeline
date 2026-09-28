"""Testes de API do assistente com sessão real por Pessoa (SPEC-0021)."""

from __future__ import annotations

import json
import logging
import uuid

from tests._assistente import (
    BASE_URL,
    ModeloDeTeste,
    cliente,
    contar,
    criar_base,
    enviar,
    exigir,
    instalar_busca,
    instalar_modelo,
    nova_conversa,
    resultado,
)
from tests._pessoas import consultar, pessoa_com_sessao


def _preparar(monkeypatch, *, modelo=None, busca=None, falhar_busca=False):
    exigir("src.app.routers.assistente")
    modelo = instalar_modelo(monkeypatch, modelo or ModeloDeTeste())
    chamadas = instalar_busca(monkeypatch, busca or {}, falhar=falhar_busca)
    return modelo, chamadas


def test_enviar_mensagem_devolve_resposta_e_persiste_o_par(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 US-001 FR-003 FR-009 AC-002"""
    modelo, _ = _preparar(monkeypatch)
    cli = cliente()
    _, cab = pessoa_com_sessao(cli, papel="member")
    conversa = nova_conversa(cli, cab)

    resposta = enviar(cli, cab, conversa, "qual splitter usar para manuais em Markdown?")

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["mensagem_assistente"]["conteudo"] == modelo.resposta
    detalhe = cli.get(f"{BASE_URL}/conversas/{conversa}", headers=cab).json()
    assert [m["papel"] for m in detalhe["mensagens"]] == ["pessoa", "assistente"]
    assert detalhe["mensagens"][0]["conteudo"] == "qual splitter usar para manuais em Markdown?"
    assert detalhe["mensagens"][1]["conteudo"] == modelo.resposta


def test_falha_do_provedor_devolve_502_generico_sem_gravar(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 US-001 FR-003 FR-010 NFR-002 AC-003"""
    _preparar(
        monkeypatch, modelo=ModeloDeTeste(erro=RuntimeError("detalhe-interno-do-provedor-xyz"))
    )
    cli = cliente()
    _, cab = pessoa_com_sessao(cli)
    conversa = nova_conversa(cli, cab)

    resposta = enviar(cli, cab, conversa, "olá")

    assert resposta.status_code == 502
    assert "detalhe-interno-do-provedor-xyz" not in resposta.text
    detalhe = cli.get(f"{BASE_URL}/conversas/{conversa}", headers=cab).json()
    assert detalhe["mensagens"] == []


def test_endpoints_do_assistente_exigem_sessao_valida(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 US-001 FR-001 FR-009 NFR-001 AC-004"""
    _preparar(monkeypatch)
    cli = cliente()
    _, cab = pessoa_com_sessao(cli)
    conversa = nova_conversa(cli, cab)
    invalido = {"Authorization": "Bearer sessao-inexistente"}

    for cabecalho in ({}, invalido):
        chamadas = [
            cli.get(f"{BASE_URL}/conversas", headers=cabecalho),
            cli.post(f"{BASE_URL}/conversas", headers=cabecalho),
            cli.get(f"{BASE_URL}/conversas/{conversa}", headers=cabecalho),
            cli.post(
                f"{BASE_URL}/conversas/{conversa}/mensagens",
                json={"texto": "oi"},
                headers=cabecalho,
            ),
            cli.delete(f"{BASE_URL}/conversas/{conversa}", headers=cabecalho),
        ]
        assert [c.status_code for c in chamadas] == [401] * 5
        assert all(conversa not in c.text for c in chamadas)


def test_listar_conversas_devolve_so_as_da_pessoa_mais_recentes_primeiro(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 US-002 FR-002 NFR-001 AC-005"""
    _preparar(monkeypatch)
    cli = cliente()
    _, cab_a = pessoa_com_sessao(cli)
    _, cab_b = pessoa_com_sessao(cli)
    a1, a2 = nova_conversa(cli, cab_a), nova_conversa(cli, cab_a)
    b1 = nova_conversa(cli, cab_b)

    lista = cli.get(f"{BASE_URL}/conversas", headers=cab_a)
    assert lista.status_code == 200
    assert [c["id"] for c in lista.json()] == [a2, a1]
    assert all({"id", "titulo", "atualizada_em"} <= set(c) for c in lista.json())

    assert enviar(cli, cab_a, a1, "atualiza a mais antiga").status_code == 201
    assert [c["id"] for c in cli.get(f"{BASE_URL}/conversas", headers=cab_a).json()] == [a1, a2]
    assert [c["id"] for c in cli.get(f"{BASE_URL}/conversas", headers=cab_b).json()] == [b1]


def test_apagar_conversa_so_pela_autora_e_outra_pessoa_recebe_404(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 US-002 FR-002 NFR-001 AC-007"""
    _preparar(monkeypatch)
    cli = cliente()
    _, cab_autora = pessoa_com_sessao(cli, papel="member")
    _, cab_owner = pessoa_com_sessao(cli, papel="owner")
    conversa = nova_conversa(cli, cab_autora)
    assert enviar(cli, cab_autora, conversa, "pergunta").status_code == 201

    inexistente = cli.get(f"{BASE_URL}/conversas/{uuid.uuid4()}", headers=cab_owner)
    abrir = cli.get(f"{BASE_URL}/conversas/{conversa}", headers=cab_owner)
    apagar = cli.delete(f"{BASE_URL}/conversas/{conversa}", headers=cab_owner)
    assert (abrir.status_code, apagar.status_code, inexistente.status_code) == (404, 404, 404)
    assert abrir.json() == inexistente.json()
    assert cli.get(f"{BASE_URL}/conversas/{conversa}", headers=cab_autora).status_code == 200

    assert cli.delete(f"{BASE_URL}/conversas/{conversa}", headers=cab_autora).status_code == 204
    assert cli.get(f"{BASE_URL}/conversas/{conversa}", headers=cab_autora).status_code == 404
    assert consultar("MensagemAssistente", lambda m: m.conversa_id == conversa) == []


def test_base_apontada_inclui_chunks_reais_no_contexto_sem_escrever(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 US-004 FR-007 FR-008 NFR-001 AC-011"""
    base = criar_base(nome="Manuais de produto")
    trecho = "Cláusula 7: a garantia cobre defeitos de fabricação por doze meses."
    modelo, chamadas = _preparar(
        monkeypatch, busca={base["colecao"]: [resultado(trecho, "x", nome_arquivo="contrato.md")]}
    )
    cli = cliente()
    _, cab = pessoa_com_sessao(cli)
    conversa = nova_conversa(cli, cab)
    antes = {n: contar(n) for n in ("Workspace", "Base", "Execution", "Query")}

    resposta = enviar(cli, cab, conversa, "qual chunking convém?", base_id=base["id"])

    assert resposta.status_code == 201, resposta.text
    contexto = modelo.contexto()
    assert "Manuais de produto" in contexto and "contrato.md" in contexto and trecho in contexto
    assert any(c["vector_store"]["collection_name"] == base["colecao"] for c in chamadas)
    assert {n: contar(n) for n in antes} == antes


def test_base_de_outro_escopo_devolve_404_sem_vazar(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 US-004 FR-007 NFR-001 AC-012"""
    de_outro_tenant = criar_base(
        tenant="tenant-2", projeto="projeto-2", nome="Segredo do outro tenant"
    )
    apagada = criar_base(nome="Base apagada", apagada=True)
    modelo, _ = _preparar(
        monkeypatch, busca={"*": [resultado("trecho-secreto-do-outro-tenant", "x")]}
    )
    cli = cliente()
    _, cab = pessoa_com_sessao(cli)
    conversa = nova_conversa(cli, cab)

    inexistente = enviar(cli, cab, conversa, "analise", base_id=str(uuid.uuid4()))
    for base in (de_outro_tenant, apagada):
        resposta = enviar(cli, cab, conversa, "analise", base_id=base["id"])
        assert resposta.status_code == 404
        assert resposta.json() == inexistente.json()
    assert inexistente.status_code == 404
    assert modelo.chamadas == []


def test_base_sem_execucao_concluida_devolve_409(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 US-004 FR-007 NFR-002 AC-013"""
    sem_execucao = criar_base(nome="Sem execução", execucao=None)
    falhou = criar_base(nome="Execução falhou", execucao="failed")
    modelo, _ = _preparar(monkeypatch)
    cli = cliente()
    _, cab = pessoa_com_sessao(cli)
    conversa = nova_conversa(cli, cab)

    for base in (sem_execucao, falhou):
        resposta = enviar(cli, cab, conversa, "analise", base_id=base["id"])
        assert resposta.status_code == 409
        assert "indexad" in resposta.text.lower()
    assert modelo.chamadas == []


def test_turno_nao_altera_bases_workspaces_execucoes_nem_configuracao(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 FR-008 NFR-001 NFR-004 AC-017"""
    base = criar_base(nome="Base intocável")
    modelo, _ = _preparar(monkeypatch, busca={base["colecao"]: [resultado("trecho", "x")]})
    cli = cliente()
    _, cab = pessoa_com_sessao(cli)
    conversa = nova_conversa(cli, cab)

    def fotografia():
        linhas = {}
        for nome in ("Workspace", "Base", "Execution", "Query"):
            linhas[nome] = sorted(
                json.dumps(
                    {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}, sort_keys=True
                )
                for r in consultar(nome)
            )
        return linhas

    antes = fotografia()
    resposta = enviar(cli, cab, conversa, "apague a Base Base intocável agora", base_id=base["id"])

    assert resposta.status_code == 201, resposta.text
    assert fotografia() == antes
    assert contar("ConversaAssistente") == 1 and contar("MensagemAssistente") == 2
    assert modelo.chamadas


def test_falha_da_recuperacao_devolve_502_generico(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 FR-010 FR-005 NFR-002 AC-019"""
    _preparar(monkeypatch, falhar_busca=True)
    cli = cliente()
    _, cab = pessoa_com_sessao(cli)
    conversa = nova_conversa(cli, cab)

    resposta = enviar(cli, cab, conversa, "como indexar?")

    assert resposta.status_code == 502
    assert "senha-interna" not in resposta.text and "10.0.0.7" not in resposta.text
    assert cli.get(f"{BASE_URL}/conversas/{conversa}", headers=cab).json()["mensagens"] == []


def test_mensagem_vazia_ou_acima_do_limite_devolve_422(monkeypatch) -> None:
    """SPECSFY: SPEC-0021 FR-003 NFR-002 AC-028"""
    modelo, _ = _preparar(monkeypatch)
    cli = cliente()
    _, cab = pessoa_com_sessao(cli)
    conversa = nova_conversa(cli, cab)

    for texto in ("", "x" * 4001):
        resposta = enviar(cli, cab, conversa, texto)
        assert resposta.status_code == 422, resposta.text
    assert modelo.chamadas == []
    assert cli.get(f"{BASE_URL}/conversas/{conversa}", headers=cab).json()["mensagens"] == []
    assert enviar(cli, cab, conversa, "x" * 4000).status_code == 201


def test_log_de_turno_registra_metadados_sem_conteudo(monkeypatch, caplog) -> None:
    """SPECSFY: SPEC-0021 FR-009 NFR-004 AC-029"""
    base = criar_base(nome="Base do log")
    trecho = "TRECHO-SIGILOSO-DA-BASE-777"
    _preparar(
        monkeypatch,
        modelo=ModeloDeTeste("RESPOSTA-CONFIDENCIAL-888"),
        busca={base["colecao"]: [resultado(trecho, "x")]},
    )
    cli = cliente()
    pessoa, cab = pessoa_com_sessao(cli)
    conversa = nova_conversa(cli, cab)
    caplog.set_level(logging.DEBUG)
    caplog.clear()

    resposta = enviar(cli, cab, conversa, "PERGUNTA-PRIVADA-999", base_id=base["id"])

    assert resposta.status_code == 201, resposta.text
    registros = [
        r
        for r in caplog.records
        if "assistente" in r.name.lower() or "assistente" in r.getMessage().lower()
    ]
    assert registros, "nenhum registro estruturado de turno do assistente"
    texto = "\n".join(
        f"{r.getMessage()} {json.dumps(r.__dict__, default=str)}" for r in registros
    ).lower()
    for esperado in (pessoa["id"], conversa, "duracao", "resultado", "base"):
        assert str(esperado).lower() in texto, f"o log do turno não contém {esperado!r}"
    todos = "\n".join(
        f"{r.getMessage()} {json.dumps(r.__dict__, default=str)}" for r in caplog.records
    )
    token = cab["Authorization"].removeprefix("Bearer ")
    for proibido in (
        "PERGUNTA-PRIVADA-999",
        "RESPOSTA-CONFIDENCIAL-888",
        trecho,
        token,
        pessoa["senha"],
    ):
        assert proibido not in todos, f"o log contém conteúdo ou segredo: {proibido!r}"
