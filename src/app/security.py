"""Primitivas de segurança para senhas e sessões da aplicação."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

DURACAO_SESSAO = timedelta(hours=8)
MAX_FALHAS_LOGIN = 5
DURACAO_BLOQUEIO = timedelta(minutes=15)
TAMANHO_MINIMO_SENHA = 10
RETENCAO_EVENTOS = timedelta(days=90)

_hasher = PasswordHasher()
_HASH_FICTICIO = _hasher.hash("senha-ficticia-para-custo-constante")


class SenhaInvalida(ValueError):
    """A senha não atende à política explícita do produto."""


def validar_politica_senha(senha: str, *, senha_atual: str | None = None) -> None:
    if len(senha) < TAMANHO_MINIMO_SENHA:
        raise SenhaInvalida(f"A senha deve ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres.")
    if senha_atual is not None and senha == senha_atual:
        raise SenhaInvalida("A nova senha deve ser diferente da senha atual.")


def hash_senha(senha: str) -> str:
    validar_politica_senha(senha)
    return _hasher.hash(senha)


def verificar_senha(senha_hash: str | None, senha: str) -> bool:
    """Verifica a senha pagando o mesmo custo quando a conta não existe."""
    try:
        return _hasher.verify(senha_hash or _HASH_FICTICIO, senha)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def gerar_token_sessao() -> str:
    """Gera 256 bits aleatórios em codificação URL-safe."""
    return secrets.token_urlsafe(32)


def resumir_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verificar_senha_ficticia(senha: str) -> None:
    """Executa a verificação Argon2 mesmo quando não existe pessoa para o e-mail."""
    verificar_senha(None, senha)
