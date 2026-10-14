import os
import stat
import subprocess
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "deploy" / "build_and_deploy.sh"


def _docker_fake_que_falha_no_build(tmp_path: Path) -> tuple[Path, Path]:
    log = tmp_path / "chamadas.log"
    fake = tmp_path / "docker"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$@" >> "{log}"\n'
        'if [ "$1" = "info" ]; then echo true; exit 0; fi\n'
        'if [ "$1 $2" = "secret ls" ]; then\n'
        "  printf '%s\\n' openrouter_api_key_v1 r2_credentials_v1 \\\n"
        "    postgres_password_v1 conexoes_chave_v1\n"
        "  exit 0\n"
        "fi\n"
        'if [ "$1" = "build" ]; then exit 1; fi\n'
        "exit 0\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return fake, log


def test_build_falho_impede_execucao_do_deploy(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0022 US-001 FR-001 FR-002 NFR-001 AC-003"""
    _, log = _docker_fake_que_falha_no_build(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["DOMINIO_RAGPIPELINE"] = "app-teste.invalid"

    resultado = subprocess.run(
        [str(SCRIPT_PATH)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert resultado.returncode != 0
    chamadas = log.read_text() if log.exists() else ""
    assert any(linha.startswith("build ") for linha in chamadas.splitlines())
    assert "stack deploy" not in chamadas


# --- SPEC-0027: verificação dos secrets antes dos builds -----------------------

from tests._docker_falso import Ambiente, todos_os_secrets


def test_secret_ausente_bloqueia_o_deploy_antes_dos_builds(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-002 FR-005 FR-006 NFR-004 AC-007"""
    secrets = todos_os_secrets()
    del secrets["conexoes_chave_v1"]
    amb = Ambiente(tmp_path, secrets)

    resultado = amb.deploy()

    assert resultado.returncode != 0
    texto = resultado.stdout + resultado.stderr
    assert "conexoes_chave" in texto
    assert "deploy/secrets.sh criar conexoes_chave" in texto
    chamadas = "\n".join(amb.chamadas())
    assert "build" not in chamadas
    assert "stack deploy" not in chamadas


def test_deploy_entrega_a_versao_resolvida_ao_stack(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-002 FR-005 FR-006 FR-007 AC-008"""
    secrets = todos_os_secrets({"openrouter_api_key": 2})
    secrets["openrouter_api_key_v1"] = "valor-antigo"
    amb = Ambiente(tmp_path, secrets)

    resultado = amb.deploy()

    assert resultado.returncode == 0, resultado.stderr
    ambiente_do_deploy = amb.ambiente_do_deploy()
    assert "OPENROUTER_API_KEY_SECRET=openrouter_api_key_v2" in ambiente_do_deploy
    assert "R2_CREDENTIALS_SECRET=r2_credentials_v1" in ambiente_do_deploy
    assert "POSTGRES_PASSWORD_SECRET=postgres_password_v1" in ambiente_do_deploy
    assert "CONEXOES_CHAVE_SECRET=conexoes_chave_v1" in ambiente_do_deploy
    assert amb.criacoes() == []


def test_verificacao_vem_antes_dos_builds_e_o_deploy_por_ultimo(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-002 FR-005 FR-006 NFR-002 AC-019"""
    amb = Ambiente(tmp_path, todos_os_secrets())

    resultado = amb.deploy()
    chamadas = amb.chamadas()

    assert resultado.returncode == 0, resultado.stderr

    def posicao(prefixo: str) -> int:
        return next((i for i, c in enumerate(chamadas) if c.startswith(prefixo)), -1)

    primeira_listagem, primeiro_build, deploy = (
        posicao("secret ls"),
        posicao("build"),
        posicao("stack deploy"),
    )
    assert primeira_listagem >= 0, "a verificação dos secrets não consultou o Swarm"
    assert primeira_listagem < primeiro_build < deploy
    assert deploy == len(chamadas) - 1
    assert amb.criacoes() == []

    falho = Ambiente(tmp_path / "falho", todos_os_secrets()).deploy(FAKE_FALHAR_BUILD="1")
    assert falho.returncode != 0


# --- SPEC-0032: domínio obrigatório no deploy -------------------------------------


from tests._docker_falso import RAIZ


def test_deploy_sem_dominio_e_recusado_antes_de_build_e_stack_deploy(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0032 US-001 FR-001 NFR-001 AC-003"""
    amb = Ambiente(tmp_path, todos_os_secrets())
    env = amb.env(DATABASE_NODE_HOSTNAME="no-de-dados", APPLICATION_NODE_HOSTNAME="no-de-aplicacao")
    assert "DOMINIO_RAGPIPELINE" not in env

    resultado = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        env=env,
        cwd=RAIZ,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert resultado.returncode != 0
    assert "DOMINIO_RAGPIPELINE" in resultado.stdout + resultado.stderr
    chamadas = "\n".join(amb.chamadas())
    assert "build" not in chamadas
    assert "stack deploy" not in chamadas
