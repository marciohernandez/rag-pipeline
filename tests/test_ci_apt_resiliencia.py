"""SPEC-0044: limite de tempo e nova tentativa no passo do apt do CI.

Casos estáticos leem `.github/workflows/ci.yml` e o script de instalação; os
casos de comportamento executam `.github/scripts/instalar_pacotes_apt.sh` com
`sudo`, `apt-get` e `dpkg` falsos num diretório temporário, sem tocar no sistema.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "ci.yml"
SCRIPT_PATH = ROOT / ".github" / "scripts" / "instalar_pacotes_apt.sh"
CHAMADA_DO_SCRIPT = "bash .github/scripts/instalar_pacotes_apt.sh"
DONOS_DE_ACTIONS_PERMITIDOS = {"actions", "astral-sh"}

# `apt-get update` é a primeira chamada de cada tentativa; cada linha do contador é uma tentativa.
APT_SEMPRE_FALHA = """#!/usr/bin/env bash
case "$*" in
  *update*) echo update >> "$CONTADOR"; exit 1 ;;
esac
exit 0
"""
APT_FALHA_ATE = """#!/usr/bin/env bash
case "$*" in
  *update*)
    echo update >> "$CONTADOR"
    [ "$(wc -l < "$CONTADOR")" -lt "$FALHAR_ATE" ] && exit 1
    exit 0 ;;
esac
exit 0
"""
APT_LENTO = """#!/usr/bin/env bash
case "$*" in
  *update*) echo update >> "$CONTADOR"; exec sleep 4 >/dev/null 2>&1 ;;
esac
exit 0
"""


def _workflow() -> dict:
    return yaml.load(WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def _passos(job: str) -> list[dict]:
    return _workflow()["jobs"][job]["steps"]


def _texto_do_script() -> str:
    assert SCRIPT_PATH.is_file(), ".github/scripts/instalar_pacotes_apt.sh ainda não existe"
    return SCRIPT_PATH.read_text(encoding="utf-8")


def _executar_script(
    tmp_path: Path, apt: str, **ambiente: str
) -> tuple[subprocess.CompletedProcess[str], int, float]:
    assert SCRIPT_PATH.is_file(), ".github/scripts/instalar_pacotes_apt.sh ainda não existe"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    contador = tmp_path / "chamadas_apt.txt"
    contador.write_text("", encoding="utf-8")
    falsos = {
        "sudo": '#!/usr/bin/env bash\nexec "$@"\n',
        "dpkg": "#!/usr/bin/env bash\nexit 0\n",
        "apt-get": apt,
    }
    for nome, conteudo in falsos.items():
        arquivo = bin_dir / nome
        arquivo.write_text(conteudo, encoding="utf-8")
        arquivo.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "CONTADOR": str(contador),
        **ambiente,
    }
    inicio = time.monotonic()
    resultado = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    decorrido = time.monotonic() - inicio
    linhas = contador.read_text(encoding="utf-8").splitlines()
    tentativas = len([linha for linha in linhas if linha])
    return resultado, tentativas, decorrido


def test_tentativa_lenta_e_cancelada_pelo_limite(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0044 US-001 FR-001 NFR-001 AC-001"""
    assert "APT_LIMITE_SEGUNDOS:-300" in _texto_do_script()
    resultado, tentativas, decorrido = _executar_script(
        tmp_path, APT_LENTO, APT_LIMITE_SEGUNDOS="1", APT_TENTATIVAS="1"
    )
    assert tentativas == 1
    assert decorrido < 3.5, "a tentativa lenta não foi cancelada pelo limite"
    assert resultado.returncode != 0


def test_apt_que_sempre_falha_roda_tres_tentativas(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0044 US-001 FR-001 NFR-001 AC-002"""
    assert "APT_TENTATIVAS:-3" in _texto_do_script()
    _, tentativas, _ = _executar_script(tmp_path, APT_SEMPRE_FALHA)
    assert tentativas == 3


def test_tres_falhas_terminam_com_erro_e_mensagem(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0044 US-001 FR-002 AC-003"""
    resultado, _, _ = _executar_script(tmp_path, APT_SEMPRE_FALHA)
    saida = resultado.stdout + resultado.stderr
    assert resultado.returncode != 0
    assert "falhou após 3 tentativas" in saida.splitlines()[-1]


def test_sucesso_na_segunda_tentativa_para_o_laco(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0044 US-001 FR-001 FR-002 AC-004"""
    resultado, tentativas, _ = _executar_script(tmp_path, APT_FALHA_ATE, FALHAR_ATE="2")
    assert resultado.returncode == 0
    assert tentativas == 2


def test_job_quality_declara_teto_de_25_minutos() -> None:
    """SPECSFY: SPEC-0044 US-002 FR-003 NFR-001 AC-005"""
    assert _workflow()["jobs"]["quality"].get("timeout-minutes") == "25"


def test_gatilhos_e_comandos_preservados_e_apt_chama_o_script() -> None:
    """SPECSFY: SPEC-0044 US-002 FR-004 AC-006"""
    workflow = _workflow()
    assert {"push", "pull_request"} <= set(workflow["on"])
    comandos = [passo["run"] for passo in _passos("quality") if "run" in passo]
    assert "uv run ruff check" in comandos
    assert "uv run pytest" in comandos
    assert any(CHAMADA_DO_SCRIPT in comando for comando in comandos)


def test_ruff_e_pytest_sem_nova_tentativa() -> None:
    """SPECSFY: SPEC-0044 US-002 FR-004 NFR-002 AC-007"""
    passos = _passos("quality")
    for comando in ("uv run ruff check", "uv run pytest"):
        passo = next(p for p in passos if p.get("run") == comando)
        assert "continue-on-error" not in passo
        assert not re.search(r"\b(for|while|until)\b", passo["run"])
    com_script = [p for p in passos if CHAMADA_DO_SCRIPT in p.get("run", "")]
    assert len(com_script) == 1, "só o passo do apt deve chamar o script de nova tentativa"
    donos = {
        p["uses"].split("/")[0]
        for job in _workflow()["jobs"].values()
        for p in job["steps"]
        if "uses" in p
    }
    assert donos <= DONOS_DE_ACTIONS_PERMITIDOS


def test_teto_do_job_comporta_o_pior_caso_do_apt() -> None:
    """SPECSFY: SPEC-0044 US-002 FR-003 NFR-001 AC-008"""
    texto = _texto_do_script()
    limite = int(re.search(r"APT_LIMITE_SEGUNDOS:-(\d+)", texto).group(1))
    tentativas = int(re.search(r"APT_TENTATIVAS:-(\d+)", texto).group(1))
    pior_caso = limite * tentativas / 60
    quality = _workflow()["jobs"]["quality"]
    teto = int(quality["timeout-minutes"])
    passo_apt = next(p for p in quality["steps"] if CHAMADA_DO_SCRIPT in p.get("run", ""))
    assert teto > pior_caso + 5
    assert pior_caso <= int(passo_apt["timeout-minutes"]) < teto


def test_cada_tentativa_anuncia_seu_numero(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0044 US-001 FR-002 AC-009"""
    resultado, _, _ = _executar_script(tmp_path, APT_FALHA_ATE, FALHAR_ATE="3")
    saida = resultado.stdout + resultado.stderr
    for numero in (1, 2, 3):
        assert f"Tentativa {numero} de 3" in saida


def test_so_o_job_quality_recebe_teto() -> None:
    """SPECSFY: SPEC-0044 US-002 FR-003 AC-010"""
    jobs = _workflow()["jobs"]
    assert "timeout-minutes" in jobs["quality"]
    assert "timeout-minutes" not in jobs["frontend"]
    assert jobs["frontend"]["name"] == "Frontend (lint, types, tests, build)"


def test_workflow_e_script_sem_segredo() -> None:
    """SPECSFY: SPEC-0044 US-002 FR-004 NFR-002 AC-011"""
    textos = [WORKFLOW_PATH.read_text(encoding="utf-8"), _texto_do_script()]
    for texto in textos:
        assert "secrets." not in texto
        assert "${{ secrets" not in texto


def test_actions_continuam_fixadas_por_sha() -> None:
    """SPECSFY: SPEC-0044 US-002 FR-004 NFR-002 AC-012"""
    usos = [p["uses"] for job in _workflow()["jobs"].values() for p in job["steps"] if "uses" in p]
    assert usos
    for uso in usos:
        assert re.search(r"@[0-9a-f]{40}$", uso), f"action sem SHA fixo: {uso}"
