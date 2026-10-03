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

    resultado = subprocess.run(
        [str(SCRIPT_PATH)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert resultado.returncode != 0
    chamadas = log.read_text() if log.exists() else ""
    assert "stack deploy" not in chamadas
