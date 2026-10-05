"""Pré-condição do Pytest: destino explícito, separado e sem herança ambígua."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_DEFAULT = "postgresql+psycopg://postgres:postgres@localhost:5432/rag_pipeline"


def database_identity(url: str) -> tuple[str, int, str]:
    """Compara destino sem considerar senha, usuário ou qualificador do driver."""
    try:
        parsed = make_url(url)
        if parsed.get_backend_name() != "postgresql" or not parsed.host or not parsed.database:
            raise ValueError
        host = parsed.host.lower()
        if host in {"localhost", "127.0.0.1", "::1"}:
            host = "loopback"
        return host, parsed.port or 5432, parsed.database
    except (TypeError, ValueError) as error:
        raise RuntimeError("Destino PostgreSQL inválido; conexão não autorizada") from error


def configure_testing_environment(root: Path = ROOT) -> str:
    testing_path = root / ".env.testing"
    example_path = root / ".env.testing.example"
    # O runner do GitHub Actions já sobe o Postgres de teste e exporta o mesmo
    # destino do exemplo versionado; nele, o exemplo substitui o arquivo local.
    if (
        not testing_path.is_file()
        and os.environ.get("GITHUB_ACTIONS") == "true"
        and example_path.is_file()
    ):
        testing_path = example_path
    if not testing_path.is_file():
        raise RuntimeError("Crie .env.testing a partir de .env.testing.example antes dos testes")
    testing = dotenv_values(testing_path, interpolate=False)
    url = testing.get("APP_DATABASE_URL")
    if testing.get("APP_ENV") != "testing" or not url:
        raise RuntimeError(".env.testing exige APP_ENV=testing e APP_DATABASE_URL explícita")
    target = database_identity(url)
    development = dotenv_values(root / ".env", interpolate=False)
    if target == database_identity(development.get("APP_DATABASE_URL") or DEVELOPMENT_DEFAULT):
        raise RuntimeError("Banco de testes coincide com o banco de desenvolvimento")
    inherited = os.environ.get("APP_DATABASE_URL")
    if inherited and database_identity(inherited) != target:
        raise RuntimeError("APP_DATABASE_URL herdada diverge do destino de .env.testing")
    if os.environ.get("APP_ENV") not in {None, "testing"}:
        raise RuntimeError("APP_ENV herdado não é testing")
    os.environ["APP_ENV"] = "testing"
    os.environ["APP_DATABASE_URL"] = url
    return url


if __name__ == "__main__":
    configure_testing_environment()
    print("Isolamento PostgreSQL: SAFE (.env.testing explícito, destino separado)")
