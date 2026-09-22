"""Comando de implantação para criar o primeiro owner ou redefinir uma senha."""

from __future__ import annotations

import argparse
import getpass
from collections.abc import Sequence

from sqlalchemy import delete, select

import src.app.main  # noqa: F401 — configura o banco como o entrypoint HTTP
from src.app.accounts import normalizar_email
from src.app.db import SessionLocal
from src.app.events import registrar_evento
from src.app.models import Pessoa, TentativaLogin, VinculoPessoa
from src.app.security import SenhaInvalida, hash_senha


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cria o primeiro owner ou redefine uma senha.")
    parser.add_argument("--nome")
    parser.add_argument("--email", required=True)
    parser.add_argument("--tenant")
    parser.add_argument("--projeto")
    parser.add_argument("--redefinir-senha", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    senha = getpass.getpass("Senha temporária: ")
    try:
        senha_hash = hash_senha(senha)
    except SenhaInvalida as erro:
        print(f"Erro: {erro}")
        return 2

    email = normalizar_email(args.email)
    with SessionLocal() as session:
        pessoa = session.execute(
            select(Pessoa).where(Pessoa.email == email)
        ).scalar_one_or_none()
        if args.redefinir_senha:
            if pessoa is None:
                print("Erro: pessoa não encontrada.")
                return 1
            vinculo = session.execute(
                select(VinculoPessoa).where(VinculoPessoa.pessoa_id == pessoa.id)
            ).scalar_one()
            pessoa.senha_hash = senha_hash
            pessoa.precisa_trocar_senha = True
            session.execute(
                delete(TentativaLogin).where(TentativaLogin.email_normalizado == email)
            )
            from src.app.accounts import encerrar_sessoes

            encerrar_sessoes(session, pessoa.id, motivo="senha_redefinida")
            registrar_evento(
                session,
                "senha_redefinida",
                alvo_pessoa_id=pessoa.id,
                tenant_id=vinculo.tenant_id,
                project_id=vinculo.project_id,
            )
            session.commit()
            print("Senha redefinida; a troca será exigida no próximo acesso.")
            return 0

        if not args.nome or not args.tenant or not args.projeto:
            print("Erro: nome, tenant e projeto são obrigatórios para criar o owner.")
            return 2
        if pessoa is not None:
            print("Erro: e-mail já cadastrado.")
            return 1
        pessoa = Pessoa(
            nome=args.nome.strip(),
            email=email,
            senha_hash=senha_hash,
            precisa_trocar_senha=True,
            situacao="ativa",
        )
        session.add(pessoa)
        session.flush()
        session.add(
            VinculoPessoa(
                pessoa_id=pessoa.id,
                tenant_id=args.tenant,
                project_id=args.projeto,
                papel="owner",
            )
        )
        registrar_evento(
            session,
            "pessoa_criada",
            alvo_pessoa_id=pessoa.id,
            tenant_id=args.tenant,
            project_id=args.projeto,
        )
        session.commit()
    print("Owner criado; a troca de senha será exigida no primeiro acesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
