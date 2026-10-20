"""Stack de produção com Qdrant e Postgres externos (SPEC-0041).

Fase RED: o stack ainda declara `postgres_ragpipeline` e `qdrant_ragpipeline`, com
host e URL fixos. Os casos leem `deploy/stack.prod.yml` sem rede.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

STACK_PATH = Path(__file__).resolve().parent.parent / "deploy" / "stack.prod.yml"
SERVICOS_INTERNOS = ("postgres_ragpipeline", "qdrant_ragpipeline")
VOLUMES_INTERNOS = ("postgres_data_ragpipeline", "qdrant_data_ragpipeline")


def _stack() -> dict:
    return yaml.safe_load(STACK_PATH.read_text())


def _comando(servico: str) -> str:
    return "\n".join(str(item) for item in _stack()["services"][servico]["command"])


def test_stack_nao_declara_servicos_nem_volumes_internos() -> None:
    """SPECSFY: SPEC-0041 US-001 US-002 US-003 FR-001 FR-002 FR-004 NFR-003 AC-001"""
    stack = _stack()
    for nome in SERVICOS_INTERNOS:
        assert nome not in stack["services"]
    for nome in VOLUMES_INTERNOS:
        assert nome not in stack.get("volumes", {})
    texto = STACK_PATH.read_text()
    for nome in SERVICOS_INTERNOS:
        assert nome not in texto, f"{nome} ainda é referenciado no stack"


def test_url_do_postgres_vem_de_variaveis_e_exige_ssl(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0041 US-001 FR-001 NFR-001 AC-002"""
    senha = tmp_path / "senha"
    senha.write_text("segredo-simples\n")
    saida = _url_do_backend(senha)

    assert "db.exemplo.invalid" in saida
    assert "sslmode=require" in saida
    assert "postgres_ragpipeline" not in saida
    texto = STACK_PATH.read_text()
    assert "db.exemplo.invalid" not in texto and "DATABASE_HOST" in texto


def test_senha_com_caracteres_especiais_e_codificada_na_url(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0041 US-001 FR-001 NFR-001 AC-003"""
    senha = tmp_path / "senha"
    senha.write_text("a@b:c/d%e\n")

    saida = _url_do_backend(senha)

    assert "a%40b%3Ac%2Fd%25e" in saida
    assert "a@b:c/d%e" not in saida
    assert "usuario.ref@" not in saida and "usuario.ref:" in saida


def test_qdrant_externo_recebe_url_e_chave_por_secret() -> None:
    """SPECSFY: SPEC-0041 US-002 FR-002 NFR-001 AC-004"""
    stack = _stack()
    for nome in ("backend_ragpipeline", "worker_ragpipeline"):
        servico = stack["services"][nome]
        assert "${QDRANT_URL" in str(servico["environment"]["QDRANT_URL"])
        assert "qdrant_api_key" in servico["secrets"]
        assert "/run/secrets/qdrant_api_key" in _comando(nome)
        assert "QDRANT_API_KEY" in _comando(nome)
    assert stack["secrets"]["qdrant_api_key"]["external"] is True
    assert "qdrant_api_key_v1" in stack["secrets"]["qdrant_api_key"]["name"]
    assert "qdrant_ragpipeline" not in STACK_PATH.read_text()


def _url_do_backend(senha: Path) -> str:
    """Executa a linha que monta `APP_DATABASE_URL` no comando do backend, com a senha de teste."""
    comando = _comando("backend_ragpipeline").replace("$$", "$")
    linha = next(
        trecho
        for trecho in re.split(r"\n(?=export |exec )", comando)
        if trecho.startswith("export APP_DATABASE_URL")
    )
    linha = linha.replace("/run/secrets/postgres_password", str(senha)).replace(
        "python -c", f"{sys.executable} -c"
    )
    resultado = subprocess.run(
        ["bash", "-c", linha + '\nprintf %s "$APP_DATABASE_URL"'],
        env={
            "PATH": "/usr/bin:/bin",
            "DATABASE_HOST": "db.exemplo.invalid",
            "DATABASE_PORT": "5432",
            "DATABASE_NAME": "postgres",
            "DATABASE_USER": "usuario.ref",
            "DATABASE_SSLMODE": "require",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert resultado.returncode == 0, resultado.stderr
    return resultado.stdout
