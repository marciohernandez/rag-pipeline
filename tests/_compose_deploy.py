"""Apoio dos testes do deploy em Compose (SPEC-0045).

Os arquivos de ``deploy/compose/`` são lidos sem rede e sem tocar na VPS. O servidor é
simulado: ``ssh`` falso executa localmente o script enviado pela entrada padrão, e
``git`` e ``docker`` falsos registram as chamadas em ``chamadas.log``.
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "deploy" / "compose"
COMPOSE = PASTA / "compose.yml"
HOMOLOG = PASTA / "compose.homolog.yml"
ENV_EXAMPLE = PASTA / ".env.example"
DEPLOY_SH = PASTA / "deploy.sh"
RUNBOOK = RAIZ / "deploy" / "RUNBOOK_COMPOSE.md"
MAKEFILE = RAIZ / "Makefile"
STACK = RAIZ / "deploy" / "stack.prod.yml"

SERVICOS = (
    "postgres_ragpipeline",
    "backend_ragpipeline",
    "worker_ragpipeline",
    "frontend_ragpipeline",
    "backup_ragpipeline",
)
SEGREDOS = (
    "openrouter_api_key",
    "r2_credentials",
    "conexoes_chave",
    "postgres_password",
    "qdrant_api_key",
    "backup_chave",
    "backup_r2_credentials",
    "backup_avisos",
)
SHA = "abc1234def5678abc1234def5678abc1234def56"


def existente(caminho: Path) -> Path:
    assert caminho.is_file(), f"{caminho.relative_to(RAIZ)} ainda não existe"
    return caminho


def yaml_de(caminho: Path) -> dict:
    return yaml.safe_load(existente(caminho).read_text())


def texto_de(caminho: Path) -> str:
    return existente(caminho).read_text()


def variaveis_minimas(segredos: Path) -> dict[str, str]:
    return {
        "DOMINIO_RAGPIPELINE": "app-teste.invalid",
        "QDRANT_URL": "https://qdrant.exemplo.invalid",
        "VERSAO_IMAGEM": "abc1234",
        "SEGREDOS_DIR": str(segredos),
    }


def compose_config(env_extra: dict[str, str], *arquivos: Path, remover: tuple[str, ...] = ()):
    """Roda `docker compose config -q` (operação local, não toca o Docker em execução)."""
    env = {k: v for k, v in os.environ.items() if k not in remover}
    env.update(env_extra)
    comando = ["docker", "compose", "-p", "ragpipeline"]
    for arquivo in arquivos:
        comando += ["-f", str(arquivo)]
    return subprocess.run(
        comando + ["config", "-q"], env=env, capture_output=True, text=True, check=False
    )


def criar_segredos(pasta: Path, modo: int = 0o600) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    for nome in SEGREDOS:
        arquivo = pasta / nome
        arquivo.write_text("valor-de-teste\n")
        arquivo.chmod(modo)
    return pasta


def _executavel(arquivo: Path, conteudo: str) -> None:
    arquivo.write_text(conteudo)
    arquivo.chmod(arquivo.stat().st_mode | stat.S_IEXEC)


class Servidor:
    """Ambiente simulado: config de deploy, ssh/git/docker falsos e pasta do projeto."""

    def __init__(
        self,
        base: Path,
        *,
        git_sujo: bool = False,
        no_remoto: bool = True,
        docker_falha: str = "",
        modo_segredos: int = 0o600,
        sem_segredo: str = "",
    ) -> None:
        self.base = base
        self.log = base / "chamadas.log"
        self.ssh_log = base / "ssh.log"
        self.log.write_text("")
        self.ssh_log.write_text("")
        bin_ = base / "bin"
        bin_.mkdir()
        self.projeto = base / "servidor" / "ragpipeline"
        self.projeto.mkdir(parents=True)
        segredos = criar_segredos(base / "servidor" / "segredos", modo_segredos)
        if sem_segredo:
            (segredos / sem_segredo).unlink()
        (self.projeto / ".env").write_text(
            f"DOMINIO_RAGPIPELINE=app-teste.invalid\nQDRANT_URL=https://q.invalid\n"
            f"SEGREDOS_DIR={segredos}\nDATABASE_HOST=postgres_ragpipeline\n"
        )
        (self.projeto / ".env").chmod(0o600)
        chave = base / "chave"
        chave.write_text("chave-falsa\n")
        chave.chmod(0o600)
        self.config = base / "deploy.conf"
        self.config.write_text(
            f"DEPLOY_HOST=vps.invalid\nDEPLOY_USER=deploy\nDEPLOY_KEY={chave}\n"
            f"DEPLOY_PATH={self.projeto}\n"
        )
        self.config.chmod(0o600)
        _executavel(
            bin_ / "ssh",
            f'#!/usr/bin/env bash\necho "$@" >> "{self.ssh_log}"\n'
            # Como o ssh real: descarta as opções, executa o comando remoto com a entrada
            # padrão e devolve o código de saída.
            'while [ "$#" -gt 0 ]; do case "$1" in *@*) shift; break;; esac; shift; done\n'
            'exec bash -c "$*"\n',
        )
        status = 'echo " M arquivo"' if git_sujo else "true"
        remoto = "echo origin/main" if no_remoto else "true"
        _executavel(
            bin_ / "git",
            f'#!/usr/bin/env bash\necho "git $@" >> "{self.log}"\n'
            f'if [ "$1" = rev-parse ] && [ "$2" = --short ]; then echo {SHA[:7]}; exit 0; fi\n'
            f'if [ "$1" = rev-parse ]; then echo {SHA}; exit 0; fi\n'
            f'if [ "$1" = status ]; then {status}; exit 0; fi\n'
            f'if [ "$1" = branch ]; then {remoto}; exit 0; fi\n'
            "exit 0\n",
        )
        _executavel(
            bin_ / "docker",
            "#!/usr/bin/env bash\n"
            f'echo "docker $@ [VERSAO_IMAGEM=$VERSAO_IMAGEM]" >> "{self.log}"\n'
            f'case "$*" in *network*inspect*) exit 0;; esac\n'
            + (f'case "$*" in *{docker_falha}*) exit 1;; esac\n' if docker_falha else "")
            + "exit 0\n",
        )
        self.env = os.environ.copy()
        self.env["PATH"] = f"{bin_}:{self.env['PATH']}"
        self.env["DEPLOY_CONFIG"] = str(self.config)

    def executar(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(existente(DEPLOY_SH)), *args],
            cwd=RAIZ,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def chamadas(self) -> list[str]:
        return self.log.read_text().splitlines()
