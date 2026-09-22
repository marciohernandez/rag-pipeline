"""Apoio dos testes da SPEC-0020: pessoas, sessões e leitura direta do banco.

O código de produção da SPEC-0020 ainda não existe quando estes testes são
escritos (fase RED). Por isso cada função importa o recurso só ao ser chamada e
usa :func:`recurso`, que reprova o teste com uma mensagem clara quando o
módulo, o modelo ou a função ainda não existe. A falha acontece dentro do corpo
do teste, nunca na coleta nem em fixture de infraestrutura.

As pessoas de teste são gravadas pelos modelos de ``src.app.models`` (seção 9
da spec) e as senhas passam por ``src.app.security.hash_senha``; todo o resto
do comportamento é exercitado pela API HTTP da seção 10.
"""

from __future__ import annotations

import importlib
import uuid
from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

SENHA = "senha-de-teste-123"
NOVA_SENHA = "outra-senha-de-teste-456"


def recurso(modulo: str, nome: str | None = None) -> Any:
    """Importa ``modulo`` (e ``nome``) ou reprova o teste por comportamento ausente."""
    try:
        carregado = importlib.import_module(modulo)
    except ImportError:
        pytest.fail(f"{modulo} ainda não existe (comportamento da SPEC-0020 ausente)")
    if nome is None:
        return carregado
    if not hasattr(carregado, nome):
        pytest.fail(f"{modulo}.{nome} ainda não existe (comportamento da SPEC-0020 ausente)")
    return getattr(carregado, nome)


def cliente() -> TestClient:
    from src.app.main import app

    return TestClient(app)


def email_unico(prefixo: str = "pessoa") -> str:
    return f"{prefixo}-{uuid.uuid4().hex[:10]}@exemplo.com"


def sessao_do_banco():
    import src.app.main  # noqa: F401 — liga banco e configuração
    from src.app import db

    return db.SessionLocal()


def criar_pessoa(
    *,
    email: str | None = None,
    senha: str = SENHA,
    papel: str = "member",
    tenant: str = "tenant-1",
    projeto: str = "projeto-1",
    nome: str = "Pessoa de teste",
    pendente: bool = False,
    situacao: str = "ativa",
) -> dict[str, str]:
    """Grava uma pessoa e seu vínculo diretamente no banco de teste."""
    pessoa_modelo = recurso("src.app.models", "Pessoa")
    vinculo_modelo = recurso("src.app.models", "VinculoPessoa")
    hash_senha = recurso("src.app.security", "hash_senha")
    email = email or email_unico()
    with sessao_do_banco() as sessao:
        pessoa = pessoa_modelo(
            nome=nome,
            email=email,
            senha_hash=hash_senha(senha),
            precisa_trocar_senha=pendente,
            situacao=situacao,
        )
        sessao.add(pessoa)
        sessao.flush()
        sessao.add(
            vinculo_modelo(pessoa_id=pessoa.id, tenant_id=tenant, project_id=projeto, papel=papel)
        )
        sessao.commit()
        return {"id": pessoa.id, "email": email, "senha": senha, "nome": nome, "papel": papel}


def login(cli: TestClient, email: str, senha: str = SENHA):
    return cli.post("/api/v1/auth/login", json={"email": email, "senha": senha})


def entrar(cli: TestClient, email: str, senha: str = SENHA) -> dict[str, str]:
    """Entra e devolve o cabeçalho de autorização; reprova o teste se o login falhar."""
    resposta = login(cli, email, senha)
    assert resposta.status_code == 200, f"login de {email} falhou: {resposta.status_code}"
    return {"Authorization": f"Bearer {resposta.json()['token']}"}


def pessoa_com_sessao(cli: TestClient, **campos: Any) -> tuple[dict[str, str], dict[str, str]]:
    """Cria uma pessoa ativa e devolve ``(pessoa, cabeçalho de autorização)``."""
    pessoa = criar_pessoa(**campos)
    return pessoa, entrar(cli, pessoa["email"], pessoa["senha"])


def consultar(nome_modelo: str, criterio: Callable[[Any], Any] | None = None) -> list[Any]:
    """Lê linhas de um modelo; ``criterio`` recebe a classe e devolve a cláusula."""
    from sqlalchemy import select

    modelo = recurso("src.app.models", nome_modelo)
    with sessao_do_banco() as sessao:
        consulta = select(modelo)
        if criterio is not None:
            consulta = consulta.where(criterio(modelo))
        return list(sessao.execute(consulta).scalars().all())


def atualizar(nome_modelo: str, criterio: Callable[[Any], Any], **campos: Any) -> None:
    modelo = recurso("src.app.models", nome_modelo)
    from sqlalchemy import update

    with sessao_do_banco() as sessao:
        sessao.execute(update(modelo).where(criterio(modelo)).values(**campos))
        sessao.commit()


def falhas_seguidas(email: str) -> int:
    linhas = consultar("TentativaLogin", lambda m: m.email_normalizado == email.strip().lower())
    return linhas[0].falhas_seguidas if linhas else 0


def eventos(tipo: str, **filtros: Any) -> list[Any]:
    def criterio(modelo):
        clausula = modelo.tipo == tipo
        for campo, valor in filtros.items():
            clausula = clausula & (getattr(modelo, campo) == valor)
        return clausula

    return consultar("EventoAcesso", criterio)
