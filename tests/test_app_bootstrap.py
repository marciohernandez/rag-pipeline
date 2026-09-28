"""Testes do comando de implantação do primeiro owner (SPEC-0020, fase RED)."""

from __future__ import annotations

import getpass
from datetime import UTC, datetime, timedelta

import pytest

from tests._pessoas import (
    NOVA_SENHA,
    SENHA,
    atualizar,
    cliente,
    consultar,
    criar_pessoa,
    email_unico,
    login,
    recurso,
)


def test_comando_cria_primeiro_owner_e_redefine_senha(monkeypatch) -> None:
    """SPECSFY: SPEC-0020 US-007 FR-004 FR-013 NFR-006 AC-022"""
    from src.app.db import SessionLocal
    from src.app.models import Workspace

    criar_owner = recurso("src.app.create_owner")
    senhas = iter([SENHA, NOVA_SENHA])
    monkeypatch.setattr(getpass, "getpass", lambda *_a, **_k: next(senhas))
    cli = cliente()
    with SessionLocal() as sessao:
        sessao.add(Workspace(tenant_id="tenant-1", project_id="projeto-1", nome="Anterior"))
        sessao.commit()

    email = email_unico("owner")
    codigo = criar_owner.main(
        ["--nome", "Marcio", "--email", email, "--tenant", "tenant-1", "--projeto", "projeto-1"]
    )
    assert codigo == 0
    resposta = login(cli, email, SENHA)
    assert resposta.status_code == 200
    assert resposta.json()["pessoa"]["precisa_trocar_senha"] is True
    assert resposta.json()["pessoa"]["papel"] == "owner"
    cabecalho = {"Authorization": f"Bearer {resposta.json()['token']}"}
    assert (
        cli.post(
            "/api/v1/auth/senha", json={"nova_senha": "senha-definida-por-mim-1"}, headers=cabecalho
        ).status_code
        == 204
    )
    nomes = {w["nome"] for w in cli.get("/api/v1/workspaces", headers=cabecalho).json()}
    assert "Anterior" in nomes

    with pytest.raises(SystemExit) as saida:
        criar_owner.main(
            [
                "--nome",
                "X",
                "--email",
                email_unico(),
                "--tenant",
                "t",
                "--projeto",
                "p",
                "--senha",
                "nao-deve-aceitar",
            ]
        )
    assert saida.value.code != 0

    # Segundo caso: owners esqueceram a senha e a conta está bloqueada (FIND-SEC-002).
    esquecida = criar_pessoa(papel="owner")
    for _ in range(5):
        login(cli, esquecida["email"], "senha-errada-123")
    assert login(cli, esquecida["email"], esquecida["senha"]).status_code == 429
    atualizar(
        "TentativaLogin",
        lambda m: m.email_normalizado == esquecida["email"].lower(),
        bloqueada_ate=datetime.now(UTC) + timedelta(minutes=14),
    )
    assert criar_owner.main(["--redefinir-senha", "--email", esquecida["email"]]) == 0
    reentrada = login(cli, esquecida["email"], NOVA_SENHA)
    assert reentrada.status_code == 200
    assert reentrada.json()["pessoa"]["precisa_trocar_senha"] is True
    assert consultar("Pessoa", lambda m: m.email == esquecida["email"])
