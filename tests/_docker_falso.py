"""Apoio dos testes da SPEC-0027: um `docker` falso que simula secrets do Swarm.

O falso guarda cada secret como arquivo em ``estado/secrets/<nome>``, registra
os argumentos de cada chamada em ``estado/chamadas.log`` (nunca a entrada
padrão) e responde só aos subcomandos que o script de deploy usa:
``info``, ``secret ls``, ``secret create <nome> -``, ``build`` e ``stack deploy``.
"""

from __future__ import annotations

import shutil
import stat
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SECRETS_SH = RAIZ / "deploy" / "secrets.sh"
DEPLOY_SH = RAIZ / "deploy" / "build_and_deploy.sh"

FERRAMENTAS = [
    "bash",
    "env",
    "cat",
    "tr",
    "head",
    "tail",
    "sort",
    "uniq",
    "sed",
    "awk",
    "grep",
    "cut",
    "wc",
    "mkdir",
    "rm",
    "date",
    "openssl",
    "ls",
    "basename",
    "dirname",
    "tee",
    "xargs",
    "od",
    "base64",
    "mktemp",
    "sleep",
    "stty",
    "tty",
    "dd",
    "printf",
    "test",
]

DOCKER_FALSO = r"""#!/usr/bin/env bash
estado="${FAKE_DOCKER_ESTADO:?}"
mkdir -p "$estado/secrets"
echo "$*" >> "$estado/chamadas.log"
case "$1" in
  info)
    if [ "${FAKE_MANAGER:-true}" = "true" ]; then echo "true"; else echo "false"; fi
    exit 0 ;;
  secret)
    case "$2" in
      ls)
        for arquivo in "$estado"/secrets/*; do
          [ -e "$arquivo" ] && basename "$arquivo"
        done
        exit 0 ;;
      create)
        nome="$3"
        if [ -e "$estado/secrets/$nome" ]; then
          cat > /dev/null
          echo "Error response from daemon: secret $nome already exists" >&2
          exit 1
        fi
        if [ "${FAKE_FALHAR_CRIAR:-}" = "$nome" ]; then
          cat > /dev/null
          echo "erro simulado ao criar o secret" >&2
          exit 1
        fi
        cat > "$estado/secrets/$nome"
        exit 0 ;;
    esac ;;
  build)
    if [ "${FAKE_FALHAR_BUILD:-}" = "1" ]; then exit 1; fi
    exit 0 ;;
  stack)
    env | grep '_SECRET=' >> "$estado/ambiente_deploy.log"
    exit 0 ;;
esac
exit 0
"""


class Ambiente:
    """Diretório de trabalho de um teste: `docker` falso, `PATH` e estado do Swarm."""

    def __init__(self, tmp_path: Path, secrets: dict[str, str] | None = None) -> None:
        self.raiz = tmp_path
        self.estado = tmp_path / "estado"
        self.bin = tmp_path / "bin"
        self.bin_sem_docker = tmp_path / "bin_sem_docker"
        for pasta in (self.estado / "secrets", self.bin, self.bin_sem_docker):
            pasta.mkdir(parents=True, exist_ok=True)
        falso = self.bin / "docker"
        falso.write_text(DOCKER_FALSO)
        falso.chmod(falso.stat().st_mode | stat.S_IEXEC)
        for pasta in (self.bin, self.bin_sem_docker):
            for nome in FERRAMENTAS:
                destino = shutil.which(nome)
                if destino and not (pasta / nome).exists():
                    (pasta / nome).symlink_to(destino)
        for nome, conteudo in (secrets or {}).items():
            (self.estado / "secrets" / nome).write_text(conteudo)

    def env(self, *, com_docker: bool = True, **extra: str) -> dict[str, str]:
        ambiente = {
            "PATH": str(self.bin if com_docker else self.bin_sem_docker),
            "HOME": str(self.raiz),
            "FAKE_DOCKER_ESTADO": str(self.estado),
        }
        ambiente.update(extra)
        return ambiente

    def secrets_script(
        self, *args: str, entrada: str = "", com_docker: bool = True, **env_extra: str
    ):
        return subprocess.run(
            ["bash", str(SECRETS_SH), *args],
            input=entrada,
            env=self.env(com_docker=com_docker, **env_extra),
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

    def deploy(self, **env_extra: str):
        env_extra.setdefault("DOMINIO_RAGPIPELINE", "app-teste.invalid")
        env_extra.setdefault("DATABASE_NODE_HOSTNAME", "no-de-dados")
        env_extra.setdefault("APPLICATION_NODE_HOSTNAME", "no-de-aplicacao")
        return subprocess.run(
            ["bash", str(DEPLOY_SH)],
            env=self.env(**env_extra),
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

    # leitura do estado ---------------------------------------------------
    def nomes(self) -> list[str]:
        return sorted(arquivo.name for arquivo in (self.estado / "secrets").iterdir())

    def valor(self, nome: str) -> str:
        return (self.estado / "secrets" / nome).read_text()

    def chamadas(self) -> list[str]:
        log = self.estado / "chamadas.log"
        return log.read_text().splitlines() if log.exists() else []

    def criacoes(self) -> list[str]:
        return [c for c in self.chamadas() if c.startswith("secret create")]

    def ambiente_do_deploy(self) -> list[str]:
        log = self.estado / "ambiente_deploy.log"
        return log.read_text().splitlines() if log.exists() else []


def todos_os_secrets(versoes: dict[str, int] | None = None) -> dict[str, str]:
    """Os quatro secrets de produção, cada um na versão pedida (padrão v1)."""
    padrao = {
        "openrouter_api_key": 1,
        "r2_credentials": 1,
        "postgres_password": 1,
        "conexoes_chave": 1,
    }
    padrao.update(versoes or {})
    return {f"{nome}_v{n}": f"valor-existente-{nome}-v{n}" for nome, n in padrao.items()}


def valores_gerados(saida: str) -> dict[str, str]:
    """Extrai as linhas `VALOR GERADO <secret>: <valor>` da saída do script."""
    gerados: dict[str, str] = {}
    for linha in saida.splitlines():
        if linha.startswith("VALOR GERADO "):
            rotulo, _, valor = linha.removeprefix("VALOR GERADO ").partition(": ")
            gerados[rotulo.strip()] = valor.strip()
    return gerados


def entrada_criar(
    chave: str = "sk-or-sentinela-0027",
    bucket: str = "bucket-sentinela",
    endpoint: str = "https://r2.exemplo.com",
    acesso: str = "AKIASENTINELA0027",
    segredo: str = "segredo-r2-sentinela-0027",
) -> str:
    return f"{chave}\n{bucket}\n{endpoint}\n{acesso}\n{segredo}\n"
