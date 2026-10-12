"""Testes de autenticação e autorização do backend de aplicação (SPEC-0012)."""

from __future__ import annotations

import re
import statistics
import time
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from tests._pessoas import (
    NOVA_SENHA,
    SENHA,
    atualizar,
    cliente,
    consultar,
    criar_pessoa,
    email_unico,
    entrar,
    eventos,
    falhas_seguidas,
    login,
    pessoa_com_sessao,
)


def test_owner_executa_fluxo_completo(tmp_path, monkeypatch) -> None:
    """SPECSFY: US-003 FR-001 FR-003 FR-004 FR-005 FR-006 FR-007 FR-009 NFR-003 AC-007"""
    from tests._colecoes import OWNER, enviar, md, preparar

    ambiente = preparar(tmp_path, monkeypatch)
    monkeypatch.setattr("src.pipeline.service.drop_collection", lambda *a, **k: None, raising=False)
    client = ambiente.client

    envio = enviar(ambiente, [md("doc.md", "# Titulo\n\n## Parte\n\nConteudo")], nova="fluxo")
    assert envio.status_code == 201
    envio_id, colecao_id = envio.json()["envio_id"], envio.json()["colecao_id"]
    assert client.get(f"/api/v1/envios/{envio_id}", headers=OWNER).json()["situacao"] == "succeeded"

    # A repetição só é aceita se o envio já tiver falhado; aqui apenas comprovamos
    # que o owner tem permissão para tentar (não é um 401/403).
    repeticao = client.post(f"/api/v1/envios/{envio_id}/retry", headers=OWNER)
    assert repeticao.status_code in {202, 409}

    exclusao = client.request(
        "DELETE",
        f"/api/v1/colecoes/{colecao_id}",
        json={"confirmacao_nome": "fluxo"},
        headers=OWNER,
    )
    assert exclusao.status_code == 204


@pytest.mark.parametrize(
    ("metodo", "rota"),
    [
        ("post", "/api/v1/envios"),
        ("get", "/api/v1/envios/envio-exemplo"),
        ("post", "/api/v1/envios/envio-exemplo/retry"),
        ("delete", "/api/v1/colecoes/colecao-exemplo"),
        ("post", "/api/v1/colecoes/colecao-exemplo/query"),
        ("get", "/api/v1/colecoes/colecao-exemplo/documentos"),
    ],
)
def test_rejeita_sem_token_valido(metodo: str, rota: str) -> None:
    """SPECSFY: US-003 FR-006 NFR-002 AC-008"""
    from src.app.main import app

    client = TestClient(app)

    sem_token = getattr(client, metodo)(rota)
    assert sem_token.status_code in {401, 403}

    com_token_invalido = getattr(client, metodo)(
        rota, headers={"Authorization": "Bearer token-invalido"}
    )
    assert com_token_invalido.status_code in {401, 403}


def test_isola_por_papel_e_tenant(tmp_path, monkeypatch) -> None:
    """SPECSFY: US-003 FR-005 FR-006 FR-007 NFR-002 AC-009"""
    from tests._colecoes import MEMBER, OUTRA_EQUIPE, criar_colecao, preparar

    ambiente = preparar(tmp_path, monkeypatch)
    colecao_id = criar_colecao(ambiente, "autorizacao")
    envio_id = ambiente.client.get(
        f"/api/v1/colecoes/{colecao_id}/envios",
        headers={"Authorization": "Bearer pessoa-teste-owner"},
    ).json()[0]["id"]

    apagar_como_member = ambiente.client.request(
        "DELETE",
        f"/api/v1/colecoes/{colecao_id}",
        json={"confirmacao_nome": "autorizacao"},
        headers=MEMBER,
    )
    assert apagar_como_member.status_code == 403

    acessar_de_outro_tenant = ambiente.client.get(
        f"/api/v1/envios/{envio_id}", headers=OUTRA_EQUIPE
    )
    assert acessar_de_outro_tenant.status_code == 404


# --------------------------------------------------------------------------
# SPEC-0020 — autenticação real por pessoa (fase RED).
# --------------------------------------------------------------------------

MENSAGEM_TIPO_BLOQUEIO = re.compile(r"\d")


def test_login_valido_devolve_identidade() -> None:
    """SPECSFY: SPEC-0020 US-001 FR-001 FR-007 FR-010 NFR-003 AC-001"""
    cli = cliente()
    pessoa = criar_pessoa(papel="owner", nome="Ana Souza")
    outra = criar_pessoa(papel="owner", tenant="tenant-2", projeto="projeto-2")

    resposta = login(cli, pessoa["email"], pessoa["senha"])

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert isinstance(corpo["token"], str) and corpo["token"]
    validade = datetime.fromisoformat(corpo["expira_em"]) - datetime.now(UTC)
    assert timedelta(hours=7, minutes=50) < validade <= timedelta(hours=8, minutes=1)

    cabecalho = {"Authorization": f"Bearer {corpo['token']}"}
    identidade = cli.get("/api/v1/auth/me", headers=cabecalho)
    assert identidade.status_code == 200
    assert identidade.json()["nome"] == "Ana Souza"
    assert identidade.json()["papel"] == "owner"
    assert identidade.json()["tenant_id"] == "tenant-1"
    assert identidade.json()["project_id"] == "projeto-1"

    do_outro = cli.post(
        "/api/v1/workspaces",
        json={"nome": "Workspace do tenant 2"},
        headers=entrar(cli, outra["email"], outra["senha"]),
    )
    assert do_outro.status_code == 201
    listagem = cli.get("/api/v1/workspaces", headers=cabecalho)
    assert listagem.status_code == 200
    assert do_outro.json()["id"] not in {item["id"] for item in listagem.json()}


def test_senha_errada_recusa_e_conta_falha() -> None:
    """SPECSFY: SPEC-0020 US-001 FR-001 FR-002 NFR-002 AC-002"""
    cli = cliente()
    pessoa = criar_pessoa()

    resposta = login(cli, pessoa["email"], "senha-errada-123")

    assert resposta.status_code == 401
    assert "credenciais" in resposta.text.lower()
    assert falhas_seguidas(pessoa["email"]) == 1
    assert consultar("Sessao", lambda m: m.pessoa_id == pessoa["id"]) == []


def test_recusas_de_login_sao_indistinguiveis() -> None:
    """SPECSFY: SPEC-0020 US-001 FR-001 FR-008 NFR-002 AC-003"""
    cli = cliente()
    desativada = criar_pessoa(situacao="desativada")
    ativa = criar_pessoa()
    inexistente = email_unico("nao-existe")

    a = login(cli, desativada["email"], desativada["senha"])
    b = login(cli, ativa["email"], "senha-errada-123")
    c = login(cli, inexistente, "senha-errada-123")

    assert a.status_code == b.status_code == c.status_code == 401
    assert a.json() == b.json() == c.json()

    def tempo(email: str) -> float:
        medidas = []
        for _ in range(3):
            inicio = time.perf_counter()
            login(cli, email, "senha-errada-123")
            medidas.append(time.perf_counter() - inicio)
        return statistics.median(medidas)

    # FIND-SEC-001: e-mail inexistente também paga o custo da verificação de hash.
    assert tempo(inexistente) >= 0.5 * tempo(ativa["email"])


def test_cinco_falhas_bloqueiam_por_quinze_minutos() -> None:
    """SPECSFY: SPEC-0020 US-001 FR-002 NFR-002 AC-004"""
    cli = cliente()
    pessoa = criar_pessoa()
    for _ in range(5):
        assert login(cli, pessoa["email"], "senha-errada-123").status_code == 401

    bloqueada = login(cli, pessoa["email"], pessoa["senha"])

    assert bloqueada.status_code == 429
    assert not MENSAGEM_TIPO_BLOQUEIO.search(bloqueada.json()["detail"])
    assert consultar("Sessao", lambda m: m.pessoa_id == pessoa["id"]) == []

    inexistente = email_unico("nao-existe")
    for _ in range(5):
        assert login(cli, inexistente, "senha-errada-123").status_code == 401
    sexta = login(cli, inexistente, "senha-errada-123")
    assert sexta.status_code == 429
    assert sexta.json() == bloqueada.json()


def test_bloqueio_expira_e_sucesso_zera_contador() -> None:
    """SPECSFY: SPEC-0020 US-001 FR-001 FR-002 AC-005"""
    cli = cliente()
    pessoa = criar_pessoa()
    for _ in range(5):
        login(cli, pessoa["email"], "senha-errada-123")
    assert login(cli, pessoa["email"], pessoa["senha"]).status_code == 429
    atualizar(
        "TentativaLogin",
        lambda m: m.email_normalizado == pessoa["email"].lower(),
        bloqueada_ate=datetime.now(UTC) - timedelta(minutes=1),
    )

    assert login(cli, pessoa["email"], pessoa["senha"]).status_code == 200
    assert falhas_seguidas(pessoa["email"]) == 0

    outra = criar_pessoa()
    for _ in range(4):
        login(cli, outra["email"], "senha-errada-123")
    assert login(cli, outra["email"], outra["senha"]).status_code == 200
    assert login(cli, outra["email"], "senha-errada-123").status_code == 401
    assert falhas_seguidas(outra["email"]) == 1


def test_senha_pendente_libera_so_troca_e_identidade() -> None:
    """SPECSFY: SPEC-0020 US-002 FR-004 FR-005 FR-010 FR-014 AC-006"""
    cli = cliente()
    pessoa = criar_pessoa(pendente=True)
    resposta = login(cli, pessoa["email"], pessoa["senha"])
    assert resposta.status_code == 200
    assert resposta.json()["pessoa"]["precisa_trocar_senha"] is True
    cabecalho = {"Authorization": f"Bearer {resposta.json()['token']}"}

    assert cli.get("/api/v1/auth/me", headers=cabecalho).status_code == 200
    bloqueada = cli.get("/api/v1/workspaces", headers=cabecalho)
    assert bloqueada.status_code == 403
    assert "senha_pendente" in bloqueada.text
    assert cli.post("/api/v1/auth/logout", headers=cabecalho).status_code == 204

    cabecalho = entrar(cli, pessoa["email"], pessoa["senha"])
    troca = cli.post("/api/v1/auth/senha", json={"nova_senha": NOVA_SENHA}, headers=cabecalho)
    assert troca.status_code == 204
    assert cli.get("/api/v1/workspaces", headers=cabecalho).status_code == 200


def test_politica_de_senha_na_troca_e_na_criacao() -> None:
    """SPECSFY: SPEC-0020 US-002 US-003 FR-003 FR-005 AC-007"""
    cli = cliente()
    pessoa, cabecalho = pessoa_com_sessao(cli)

    curta = cli.post(
        "/api/v1/auth/senha",
        json={"senha_atual": SENHA, "nova_senha": "curta"},
        headers=cabecalho,
    )
    igual = cli.post(
        "/api/v1/auth/senha",
        json={"senha_atual": SENHA, "nova_senha": SENHA},
        headers=cabecalho,
    )
    assert curta.status_code == 422
    assert igual.status_code == 422
    assert login(cli, pessoa["email"], SENHA).status_code == 200

    _, sessao_admin = pessoa_com_sessao(cli, papel="admin")
    email_novo = email_unico("nova")
    criacao = cli.post(
        "/api/v1/pessoas",
        json={"nome": "Nova", "email": email_novo, "papel": "member", "senha_inicial": "curta"},
        headers=sessao_admin,
    )
    assert criacao.status_code == 422
    assert consultar("Pessoa", lambda m: m.email == email_novo) == []


def test_troca_de_senha_mantem_atual_e_encerra_demais() -> None:
    """SPECSFY: SPEC-0020 US-002 US-004 FR-005 FR-006 NFR-004 AC-008"""
    cli = cliente()
    pessoa = criar_pessoa()
    sessao_a = entrar(cli, pessoa["email"], pessoa["senha"])
    sessao_b = entrar(cli, pessoa["email"], pessoa["senha"])

    troca = cli.post(
        "/api/v1/auth/senha",
        json={"senha_atual": SENHA, "nova_senha": NOVA_SENHA},
        headers=sessao_a,
    )

    assert troca.status_code == 204
    assert cli.get("/api/v1/auth/me", headers=sessao_a).status_code == 200
    assert cli.get("/api/v1/auth/me", headers=sessao_b).status_code == 401
    assert len(eventos("senha_trocada", ator_pessoa_id=pessoa["id"])) >= 1


def test_sessao_expira_em_oito_horas_e_sair_encerra() -> None:
    """SPECSFY: SPEC-0020 US-004 FR-006 FR-014 NFR-004 AC-009"""
    cli = cliente()
    pessoa = criar_pessoa()
    cabecalho = entrar(cli, pessoa["email"], pessoa["senha"])
    atualizar(
        "Sessao",
        lambda m: m.pessoa_id == pessoa["id"],
        expira_em=datetime.now(UTC) - timedelta(seconds=1),
    )

    assert cli.get("/api/v1/auth/me", headers=cabecalho).status_code == 401
    assert consultar("Sessao", lambda m: m.pessoa_id == pessoa["id"]) == []

    novo = entrar(cli, pessoa["email"], pessoa["senha"])
    assert cli.post("/api/v1/auth/logout", headers=novo).status_code == 204
    assert cli.get("/api/v1/auth/me", headers=novo).status_code == 401
    assert consultar("Sessao", lambda m: m.pessoa_id == pessoa["id"]) == []


def test_tokens_estaticos_e_sem_sessao_sao_recusados() -> None:
    """SPECSFY: SPEC-0020 US-007 FR-010 FR-013 NFR-003 AC-015"""
    cli = cliente()
    antigos = [
        "token-" + "demo-owner",
        "token-" + "demo-admin",
        "token-" + "demo-member",
        "token-" + "demo-outro-tenant",
    ]
    rotas = [
        ("get", "/api/v1/workspaces"),
        ("get", "/api/v1/colecoes/colecao-exemplo/documentos"),
        ("get", "/api/v1/envios/envio-exemplo"),
        ("post", "/api/v1/colecoes/colecao-exemplo/query"),
    ]
    for token in antigos:
        for metodo, rota in rotas:
            resposta = getattr(cli, metodo)(rota, headers={"Authorization": f"Bearer {token}"})
            assert resposta.status_code == 401, f"{token} ainda autentica em {rota}"

    for metodo, rota in rotas:
        assert getattr(cli, metodo)(rota).status_code == 401
        inexistente = {"Authorization": "Bearer sessao-que-nao-existe"}
        assert getattr(cli, metodo)(rota, headers=inexistente).status_code == 401


def test_senha_e_token_ficam_so_como_derivados() -> None:
    """SPECSFY: SPEC-0020 FR-003 FR-006 NFR-001 AC-028"""
    cli = cliente()
    pessoa = criar_pessoa()
    resposta = login(cli, pessoa["email"], pessoa["senha"])
    token = resposta.json()["token"]

    gravada = consultar("Pessoa", lambda m: m.id == pessoa["id"])[0]
    assert gravada.senha_hash.startswith("$argon2")
    assert pessoa["senha"] not in gravada.senha_hash

    sessoes = consultar("Sessao", lambda m: m.pessoa_id == pessoa["id"])
    assert len(sessoes) == 1
    assert sessoes[0].token_hash != token
    texto_da_linha = " ".join(str(valor) for valor in vars(sessoes[0]).values())
    assert token not in texto_da_linha
