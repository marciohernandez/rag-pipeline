"""Segredos, variáveis e exemplo do deploy em Compose (SPEC-0045).

Fase RED: `deploy/compose/` ainda não existe.
"""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest

from tests._compose_deploy import (
    COMPOSE,
    ENV_EXAMPLE,
    HOMOLOG,
    RAIZ,
    Servidor,
    compose_config,
    criar_segredos,
    texto_de,
    variaveis_minimas,
)


def test_deploy_recusa_segredo_ausente_ou_com_permissao_errada(tmp_path) -> None:
    """SPECSFY: SPEC-0045 US-001 FR-003 NFR-001 AC-005"""
    for opcoes, esperado in (
        ({"sem_segredo": "qdrant_api_key"}, "qdrant_api_key"),
        ({"modo_segredos": 0o644}, "600"),
    ):
        base = tmp_path / esperado
        base.mkdir()
        servidor = Servidor(base, **opcoes)
        resultado = servidor.executar()
        assert resultado.returncode != 0
        assert esperado in resultado.stderr
        assert "valor-de-teste" not in resultado.stdout + resultado.stderr
        assert not any(" build" in c for c in servidor.chamadas()), "buildou com segredo inválido"


def test_exemplo_so_tem_nomes_e_segredos_nao_sao_versionados() -> None:
    """SPECSFY: SPEC-0045 US-001 FR-003 NFR-001 AC-017"""
    for linha in texto_de(ENV_EXAMPLE).splitlines():
        if linha.strip() and not linha.startswith("#"):
            assert re.fullmatch(r"[A-Z][A-Z0-9_]*=", linha), f"valor no exemplo: {linha!r}"
    for caminho in ("deploy/compose/.env", "deploy/compose/segredos/openrouter_api_key"):
        ignorado = subprocess.run(["git", "check-ignore", "-q", caminho], cwd=RAIZ, check=False)
        assert ignorado.returncode == 0, f"{caminho} não está no .gitignore"


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker ausente")
def test_variavel_obrigatoria_ausente_falha_cedo(tmp_path) -> None:
    """SPECSFY: SPEC-0045 US-001 FR-003 NFR-003 AC-018"""
    segredos = criar_segredos(tmp_path / "segredos")
    base = variaveis_minimas(segredos)
    for variavel in ("DOMINIO_RAGPIPELINE", "QDRANT_URL"):
        sem = {k: v for k, v in base.items() if k != variavel}
        resultado = compose_config(sem, COMPOSE, HOMOLOG, remover=(variavel,))
        assert resultado.returncode != 0, variavel
        assert variavel in resultado.stderr
