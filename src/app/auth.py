"""Autenticação por token estático de demonstração (SPEC-0012, DEC-002).

Não é o modelo final de autenticação do produto: existe só para aplicar
tenant, projeto e papel nesta fatia, sem cadastro nem login real.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException

__all__ = ["Identity", "TokenRegistry", "configure", "get_identity", "require_write_role"]

PAPEIS_DE_ESCRITA = frozenset({"owner", "admin"})


@dataclass(frozen=True)
class Identity:
    tenant_id: str
    project_id: str
    role: str


class TokenRegistry:
    """Mapa de token estático de demonstração para identidade."""

    def __init__(self, tokens: dict[str, Identity]) -> None:
        self._tokens = dict(tokens)

    def resolve(self, token: str) -> Identity | None:
        return self._tokens.get(token)


_REGISTRY: TokenRegistry | None = None


def configure(registry: TokenRegistry) -> None:
    """Define o registro de tokens usado por :func:`get_identity`."""
    global _REGISTRY
    _REGISTRY = registry


def get_identity(authorization: str | None = Header(default=None)) -> Identity:
    """Dependência FastAPI: resolve a identidade do token do cabeçalho.

    Rejeita a requisição (401) antes de qualquer acesso a pipeline,
    PostgreSQL ou armazenamento de arquivo (FR-006).
    """
    if _REGISTRY is None:
        raise HTTPException(status_code=401, detail="Autenticação não configurada.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente.")
    token = authorization.removeprefix("Bearer ").strip()
    identity = _REGISTRY.resolve(token)
    if identity is None:
        raise HTTPException(status_code=401, detail="Token inválido.")
    return identity


def require_write_role(identity: Identity) -> None:
    """Recusa a operação quando o papel não tem permissão de escrita (FR-007)."""
    if identity.role not in PAPEIS_DE_ESCRITA:
        raise HTTPException(status_code=403, detail="Permissão insuficiente para esta operação.")
