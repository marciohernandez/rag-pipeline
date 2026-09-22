"""Testes da gestão de pessoas do backend de aplicação (SPEC-0020, fase RED)."""

from __future__ import annotations

import threading

from tests._pessoas import (
    NOVA_SENHA,
    atualizar,
    cliente,
    consultar,
    criar_pessoa,
    email_unico,
    entrar,
    eventos,
    login,
    pessoa_com_sessao,
)


def _criar_via_api(cli, cabecalho, *, papel: str = "member", email: str | None = None):
    return cli.post(
        "/api/v1/pessoas",
        json={
            "nome": "Pessoa criada pela API",
            "email": email or email_unico("api"),
            "papel": papel,
            "senha_inicial": "senha-inicial-123",
        },
        headers=cabecalho,
    )


def test_eventos_de_conta_encerram_sessoes() -> None:
    """SPECSFY: SPEC-0020 US-003 US-004 FR-006 FR-008 NFR-004 AC-010"""
    cli = cliente()
    _, dono = pessoa_com_sessao(cli, papel="owner")

    alteracoes = [
        ("POST", "desativar", None),
        ("PATCH", "", {"papel": "admin"}),
        ("PATCH", "", {"nome": "Nome corrigido"}),
        ("PATCH", "", {"email": email_unico("corrigido")}),
        ("POST", "redefinir-senha", {"senha_temporaria": "senha-temporaria-123"}),
    ]
    for verbo, caminho, corpo in alteracoes:
        alvo = criar_pessoa()
        sessao_do_alvo = entrar(cli, alvo["email"], alvo["senha"])
        url = f"/api/v1/pessoas/{alvo['id']}" + (f"/{caminho}" if caminho else "")
        resposta = cli.request(verbo, url, json=corpo, headers=dono)
        assert resposta.status_code in {200, 204}, f"{verbo} {url}: {resposta.status_code}"
        assert cli.get("/api/v1/auth/me", headers=sessao_do_alvo).status_code == 401
        motivos = eventos("sessao_encerrada", alvo_pessoa_id=alvo["id"])
        assert motivos and all(evento.motivo for evento in motivos)

    propria = criar_pessoa(papel="admin")
    atual = entrar(cli, propria["email"], propria["senha"])
    outra_sessao = entrar(cli, propria["email"], propria["senha"])
    correcao = cli.patch(
        f"/api/v1/pessoas/{propria['id']}", json={"nome": "Meu nome novo"}, headers=atual
    )
    assert correcao.status_code == 200
    assert cli.get("/api/v1/auth/me", headers=atual).status_code == 200
    assert cli.get("/api/v1/auth/me", headers=outra_sessao).status_code == 401


def test_owner_administra_pessoas_do_proprio_tenant() -> None:
    """SPECSFY: SPEC-0020 US-003 FR-003 FR-004 FR-008 FR-010 AC-011"""
    cli = cliente()
    _, dono = pessoa_com_sessao(cli, papel="owner")
    _, de_fora = pessoa_com_sessao(cli, papel="owner", tenant="tenant-2", projeto="projeto-2")

    criada = _criar_via_api(cli, dono)
    assert criada.status_code == 201
    pessoa_id = criada.json()["id"]
    assert criada.json()["precisa_trocar_senha"] is True
    assert "senha_hash" not in criada.text

    assert pessoa_id in {p["id"] for p in cli.get("/api/v1/pessoas", headers=dono).json()}
    assert pessoa_id not in {p["id"] for p in cli.get("/api/v1/pessoas", headers=de_fora).json()}
    assert cli.get(f"/api/v1/pessoas/{pessoa_id}", headers=dono).status_code == 200

    base = f"/api/v1/pessoas/{pessoa_id}"
    assert cli.patch(base, json={"nome": "Nome novo"}, headers=dono).status_code == 200
    assert cli.patch(base, json={"papel": "admin"}, headers=dono).status_code == 200
    assert cli.post(f"{base}/desativar", headers=dono).status_code == 204
    assert cli.post(f"{base}/reativar", headers=dono).status_code == 204

    atualizar("Pessoa", lambda m: m.id == pessoa_id, precisa_trocar_senha=False)
    redefinicao = cli.post(
        f"{base}/redefinir-senha", json={"senha_temporaria": NOVA_SENHA}, headers=dono
    )
    assert redefinicao.status_code == 204
    assert consultar("Pessoa", lambda m: m.id == pessoa_id)[0].precisa_trocar_senha is True

    assert cli.delete(base, headers=dono).status_code in {404, 405}
    assert cli.get(base, headers=dono).status_code == 200


def test_email_duplicado_e_campos_invalidos() -> None:
    """SPECSFY: SPEC-0020 US-003 FR-008 FR-015 NFR-005 AC-012"""
    cli = cliente()
    _, admin = pessoa_com_sessao(cli, papel="admin")
    _, de_fora = pessoa_com_sessao(cli, papel="admin", tenant="tenant-2", projeto="projeto-2")
    email = email_unico("ana")
    assert _criar_via_api(cli, admin, email=email).status_code == 201

    repetido = _criar_via_api(cli, admin, email=email.upper())
    assert repetido.status_code == 409
    entre_tenants = _criar_via_api(cli, de_fora, email=email)
    assert entre_tenants.status_code == 409
    # FIND-SEC-003: a recusa não revela em qual tenant o e-mail já existe.
    for resposta in (repetido, entre_tenants):
        assert "tenant" not in resposta.text.lower()

    sem_nome = cli.post(
        "/api/v1/pessoas",
        json={
            "nome": "",
            "email": email_unico(),
            "papel": "member",
            "senha_inicial": "senha-inicial-123",
        },
        headers=admin,
    )
    assert sem_nome.status_code == 422


def test_protecoes_de_ultimo_owner_e_admin() -> None:
    """SPECSFY: SPEC-0020 US-003 FR-008 FR-009 AC-013"""
    cli = cliente()
    unico, dono = pessoa_com_sessao(cli, papel="owner", tenant="tenant-5", projeto="projeto-5")

    rebaixar = cli.patch(f"/api/v1/pessoas/{unico['id']}", json={"papel": "admin"}, headers=dono)
    assert rebaixar.status_code == 409
    desativar = cli.post(f"/api/v1/pessoas/{unico['id']}/desativar", headers=dono)
    assert desativar.status_code == 409
    assert consultar("VinculoPessoa", lambda m: m.pessoa_id == unico["id"])[0].papel == "owner"

    segundo = criar_pessoa(papel="owner", tenant="tenant-5", projeto="projeto-5")
    rebaixado = cli.patch(
        f"/api/v1/pessoas/{segundo['id']}", json={"papel": "member"}, headers=dono
    )
    assert rebaixado.status_code == 200

    admin, sessao_admin = pessoa_com_sessao(cli, papel="admin")
    dono_alvo = criar_pessoa(papel="owner")
    membro = criar_pessoa(papel="member")
    base = "/api/v1/pessoas"
    tentativas = [
        cli.post(
            base,
            json={
                "nome": "Novo owner",
                "email": email_unico(),
                "papel": "owner",
                "senha_inicial": "senha-inicial-123",
            },
            headers=sessao_admin,
        ),
        cli.patch(f"{base}/{admin['id']}", json={"papel": "owner"}, headers=sessao_admin),
        cli.patch(f"{base}/{membro['id']}", json={"papel": "owner"}, headers=sessao_admin),
        cli.patch(f"{base}/{dono_alvo['id']}", json={"nome": "X"}, headers=sessao_admin),
        cli.post(f"{base}/{dono_alvo['id']}/desativar", headers=sessao_admin),
        cli.post(
            f"{base}/{dono_alvo['id']}/redefinir-senha",
            json={"senha_temporaria": NOVA_SENHA},
            headers=sessao_admin,
        ),
    ]
    assert [t.status_code for t in tentativas] == [403] * 6

    propria = cli.post(f"{base}/{admin['id']}/desativar", headers=sessao_admin)
    assert propria.status_code == 409
    assert login(cli, admin["email"], admin["senha"]).status_code == 200


def test_rebaixamentos_simultaneos_nao_deixam_tenant_sem_owner() -> None:
    """SPECSFY: SPEC-0020 US-003 FR-009 AC-013"""
    for rodada in range(3):
        tenant = f"tenant-corrida-{rodada}"
        a, sessao_a = pessoa_com_sessao(
            cliente(), papel="owner", tenant=tenant, projeto="projeto-corrida"
        )
        b, sessao_b = pessoa_com_sessao(
            cliente(), papel="owner", tenant=tenant, projeto="projeto-corrida"
        )
        largada = threading.Barrier(2)
        respostas: list[int] = []

        def rebaixar(alvo, cabecalho, largada=largada, respostas=respostas):
            largada.wait()
            resposta = cliente().patch(
                f"/api/v1/pessoas/{alvo['id']}", json={"papel": "admin"}, headers=cabecalho
            )
            respostas.append(resposta.status_code)

        fios = [
            threading.Thread(target=rebaixar, args=(b, sessao_a)),
            threading.Thread(target=rebaixar, args=(a, sessao_b)),
        ]
        for fio in fios:
            fio.start()
        for fio in fios:
            fio.join()

        vinculos = consultar("VinculoPessoa", lambda m, t=tenant: m.tenant_id == t)
        assert [v.papel for v in vinculos].count("owner") >= 1, f"rodada {rodada}: {respostas}"


def test_member_e_isolamento_entre_tenants() -> None:
    """SPECSFY: SPEC-0020 US-003 FR-009 FR-010 FR-015 NFR-003 AC-014"""
    cli = cliente()
    _, membro = pessoa_com_sessao(cli, papel="member")
    _, dono = pessoa_com_sessao(cli, papel="owner")
    _, de_fora = pessoa_com_sessao(cli, papel="owner", tenant="tenant-2", projeto="projeto-2")

    escritas = [
        cli.post("/api/v1/workspaces", json={"nome": "Nao pode"}, headers=membro),
        cli.post("/api/v1/bases", data={"workspace_id": "x"}, headers=membro),
        cli.delete("/api/v1/bases/base-exemplo", headers=membro),
        cli.get("/api/v1/pessoas", headers=membro),
        _criar_via_api(cli, membro),
    ]
    assert [r.status_code for r in escritas] == [403] * 5

    workspace = cli.post("/api/v1/workspaces", json={"nome": "Do tenant 1"}, headers=dono)
    assert workspace.status_code == 201
    id_workspace = workspace.json()["id"]
    assert cli.get(f"/api/v1/workspaces/{id_workspace}", headers=de_fora).status_code == 404
    assert (
        cli.patch(
            f"/api/v1/workspaces/{id_workspace}", json={"nome": "Invasor"}, headers=de_fora
        ).status_code
        == 404
    )
    pessoa_do_tenant_1 = criar_pessoa(papel="member")
    assert (
        cli.get(f"/api/v1/pessoas/{pessoa_do_tenant_1['id']}", headers=de_fora).status_code == 404
    )
