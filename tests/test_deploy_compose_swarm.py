"""Convivência do deploy em Compose com o Swarm (SPEC-0045).

Os arquivos de Swarm não mudam de comportamento e Compose e Swarm compartilham as imagens.
"""

from __future__ import annotations

import hashlib
import re

from tests._compose_deploy import COMPOSE, RAIZ, RUNBOOK, STACK, texto_de, yaml_de

# SHA-256 dos arquivos de Swarm antes da SPEC-0045; mudar um deles exige spec própria e a
# atualização consciente deste instantâneo. O RUNBOOK.md fica de fora: ganha só um aviso.
SWARM = {
    "deploy/stack.prod.yml": ("00c68766599a4619e431e6fb469e51337d197431a80a682943a982ea352cf601"),
    "deploy/stack.local.yml": ("a923566eb96e21f59770ec803f299bac0e211440800b31ecfa8e19484b2a1e27"),
    "deploy/secrets.sh": ("92061be983bcbf228a118262aca0f400f514f0cd6fc479f6a70b74f5397bb4d7"),
    "deploy/build_and_deploy.sh": (
        "bd40c7013ca387ed9481f114865634cce714cb40a207c5b3329712922bc6fd3f"
    ),
}
AVISO = "RUNBOOK_COMPOSE.md"


def _sha(relativo: str) -> str:
    return hashlib.sha256((RAIZ / relativo).read_bytes()).hexdigest()


def test_arquivos_de_swarm_intactos_e_runbook_aponta_para_o_compose() -> None:
    """SPECSFY: SPEC-0045 US-003 FR-007 NFR-002 AC-010"""
    for relativo, esperado in SWARM.items():
        assert _sha(relativo) == esperado, f"{relativo} mudou"
    assert AVISO in texto_de(RAIZ / "deploy" / "RUNBOOK.md"), "RUNBOOK.md sem aviso do Compose"
    assert RUNBOOK.is_file()


def test_compose_e_swarm_usam_os_mesmos_dockerfiles_e_etiquetas() -> None:
    """SPECSFY: SPEC-0045 US-003 FR-001 FR-007 NFR-002 AC-011"""
    compose = yaml_de(COMPOSE)["services"]
    swarm = yaml_de(STACK)["services"]
    for nome in (
        "backend_ragpipeline",
        "worker_ragpipeline",
        "frontend_ragpipeline",
        "backup_ragpipeline",
    ):
        assert compose[nome]["image"] == swarm[nome]["image"], nome
    esperados = {
        "backend_ragpipeline": "deploy/backend/Dockerfile",
        "frontend_ragpipeline": "deploy/frontend/Dockerfile",
        "backup_ragpipeline": "deploy/backup/Dockerfile",
    }
    for nome, relativo in esperados.items():
        build = compose[nome]["build"]
        resolvido = (COMPOSE.parent / build["context"] / build["dockerfile"]).resolve()
        assert resolvido == RAIZ / relativo, nome
    for relativo in esperados.values():
        assert not re.search(r"--platform=", (RAIZ / relativo).read_text()), relativo


def test_compose_nao_usa_recursos_exclusivos_do_swarm() -> None:
    """SPECSFY: SPEC-0045 US-003 FR-007 NFR-002 AC-013"""
    arquivo = yaml_de(COMPOSE)
    for nome, servico in arquivo["services"].items():
        assert "deploy" not in servico, nome
    segredos = arquivo["secrets"]
    assert all(
        "file" in definicao and "external" not in definicao for definicao in segredos.values()
    )
    assert set(segredos) == {
        "openrouter_api_key",
        "r2_credentials",
        "conexoes_chave",
        "postgres_password",
        "qdrant_api_key",
        "backup_chave",
        "backup_r2_credentials",
        "backup_avisos",
    }
