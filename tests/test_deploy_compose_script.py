"""Publicação por `deploy/compose/deploy.sh` e alvos do Makefile (SPEC-0045).

Fase RED: o script e o Makefile ainda não existem. O servidor é simulado.
"""

from __future__ import annotations

import subprocess

from tests._compose_deploy import MAKEFILE, RAIZ, SHA, Servidor, texto_de


def _indice(chamadas: list[str], trecho: str) -> int:
    for posicao, chamada in enumerate(chamadas):
        if trecho in chamada:
            return posicao
    raise AssertionError(f"chamada ausente: {trecho!r} em {chamadas}")


def test_publica_exatamente_o_head_com_ssh_seguro(tmp_path) -> None:
    """SPECSFY: SPEC-0045 US-002 FR-004 FR-005 NFR-002 AC-006"""
    servidor = Servidor(tmp_path)
    resultado = servidor.executar()
    assert resultado.returncode == 0, resultado.stderr
    chamadas = servidor.chamadas()
    assert _indice(chamadas, f"checkout --detach {SHA}") < _indice(chamadas, " build")
    assert any("-p ragpipeline" in c and "-f" in c for c in chamadas)
    ssh = servidor.ssh_log.read_text()
    assert "BatchMode=yes" in ssh and "StrictHostKeyChecking=yes" in ssh
    assert "ForwardAgent=yes" not in ssh and " -A" not in ssh
    assert f"VERSAO_IMAGEM={SHA[:7]}]" in "\n".join(chamadas), "versão diferente do commit curto"


def test_recusa_arvore_suja_ou_head_fora_do_remoto(tmp_path) -> None:
    """SPECSFY: SPEC-0045 US-002 FR-004 FR-005 NFR-003 AC-007"""
    for nome, opcoes in (("suja", {"git_sujo": True}), ("fora", {"no_remoto": False})):
        base = tmp_path / nome
        base.mkdir()
        servidor = Servidor(base, **opcoes)
        resultado = servidor.executar()
        assert resultado.returncode != 0, nome
        assert servidor.ssh_log.read_text() == "", f"{nome}: tocou no servidor"
        assert resultado.stderr.strip(), "sem orientação"


def test_build_com_erro_nao_derruba_nem_substitui_servicos(tmp_path) -> None:
    """SPECSFY: SPEC-0045 US-002 FR-004 NFR-002 NFR-003 AC-008"""
    servidor = Servidor(tmp_path, docker_falha=" build")
    resultado = servidor.executar()
    assert resultado.returncode != 0
    texto = "\n".join(servidor.chamadas())
    for proibido in (" up ", " down", "volume rm", " -v"):
        assert proibido not in texto, f"executou {proibido!r} depois do build com erro"


def test_migra_depois_do_postgres_e_antes_do_conjunto(tmp_path) -> None:
    """SPECSFY: SPEC-0045 US-002 FR-004 FR-006 AC-009"""
    servidor = Servidor(tmp_path)
    assert servidor.executar().returncode == 0
    chamadas = servidor.chamadas()
    postgres = _indice(chamadas, "up -d --no-build --wait postgres_ragpipeline")
    migracao = _indice(chamadas, "alembic upgrade head")
    conjunto = max(i for i, c in enumerate(chamadas) if "up -d --no-build --wait" in c)
    assert _indice(chamadas, " build") < postgres < migracao < conjunto
    falha = tmp_path / "falha"
    falha.mkdir()
    com_erro = Servidor(falha, docker_falha="alembic upgrade head")
    assert com_erro.executar().returncode != 0
    depois = [c for c in com_erro.chamadas() if "up -d --no-build --wait" in c]
    assert all("postgres_ragpipeline" in c for c in depois), "subiu o conjunto com migration falha"


def test_makefile_expoe_os_alvos_sem_comando_destrutivo() -> None:
    """SPECSFY: SPEC-0045 US-002 FR-005 NFR-003 AC-019"""
    texto = texto_de(MAKEFILE)
    for alvo in ("deploy:", "deploy-config:", "deploy-logs:"):
        assert alvo in texto, alvo
    assert "down -v" not in texto and "volume rm" not in texto
    seco = subprocess.run(
        ["make", "-n", "deploy-config"], cwd=RAIZ, capture_output=True, text=True, check=False
    ).stdout
    assert "-p ragpipeline" in seco and "deploy/compose/compose.yml" in seco
    assert "deploy/compose/compose.homolog.yml" in seco
