"""Apoio dos testes da SPEC-0027: um `docker` falso que simula secrets do Swarm.

O falso guarda cada secret como arquivo em ``estado/secrets/<nome>``, registra
os argumentos de cada chamada em ``estado/chamadas.log`` (nunca a entrada
padrão) e responde só aos subcomandos que o script de deploy usa:
``info``, ``secret ls``, ``secret create <nome> -``, ``build`` e ``stack deploy``.

SPEC-0035: o falso também guarda as imagens (``estado/imagens.txt``, da mais antiga
para a mais nova) e responde a ``build -t``, ``image ls <repo> --format``,
``image inspect``, ``image rm`` e ``service inspect``. Um ``git`` falso responde a
``git rev-parse --short HEAD`` (``FAKE_GIT_VERSAO``) e a ``git status --porcelain``
(``FAKE_GIT_SUJO``). Estes são os comandos que ``deploy/build_and_deploy.sh`` usa
para etiquetar por versão, podar e voltar atrás.
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
    "tac",
    "touch",
    "mv",
]

DOCKER_FALSO = r"""#!/usr/bin/env bash
estado="${FAKE_DOCKER_ESTADO:?}"
mkdir -p "$estado/secrets"
echo "$*" >> "$estado/chamadas.log"
if [ "$1" = --context ]; then shift 2; fi
case "$1" in
  info)
    if [[ "$*" == *".Name"* ]]; then echo "${FAKE_NODE_NAME:-no-de-dados}"; exit 0; fi
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
    argumentos=("$@")
    for ((i = 0; i < ${#argumentos[@]}; i++)); do
      if [ "${argumentos[i]}" = "-t" ]; then
        imagem="${argumentos[i+1]}"
        touch "$estado/imagens.txt"
        grep -vxF "$imagem" "$estado/imagens.txt" > "$estado/imagens.tmp" || true
        echo "$imagem" >> "$estado/imagens.tmp"
        mv "$estado/imagens.tmp" "$estado/imagens.txt"
      fi
    done
    exit 0 ;;
  image)
    touch "$estado/imagens.txt"
    case "$2" in
      ls)
        repo=""
        [[ "${3:-}" != -* ]] && repo="${3:-}"
        formato="{{.Repository}}:{{.Tag}}"
        for ((i = 1; i <= $#; i++)); do
          if [ "${!i}" = "--format" ]; then j=$((i + 1)); formato="${!j}"; fi
        done
        tac "$estado/imagens.txt" | while read -r imagem; do
          if [ -z "$repo" ] || [ "${imagem%%:*}" = "$repo" ]; then
            if [ "$formato" = "{{.Tag}}" ]; then echo "${imagem#*:}"; else echo "$imagem"; fi
          fi
        done
        exit 0 ;;
      inspect)
        grep -qxF "$3" "$estado/imagens.txt" && exit 0
        echo "Error: No such image: $3" >&2
        exit 1 ;;
      rm)
        echo "$3" >> "$estado/removidas.log"
        grep -vxF "$3" "$estado/imagens.txt" > "$estado/imagens.tmp" || true
        mv "$estado/imagens.tmp" "$estado/imagens.txt"
        echo "Untagged: $3"
        exit 0 ;;
    esac
    exit 0 ;;
  service)
    if [ "$2" = inspect ] && [ -e "$estado/servico_em_uso" ]; then
      cat "$estado/servico_em_uso"
      exit 0
    fi
    exit 1 ;;
  stack)
    env | grep '_SECRET=' >> "$estado/ambiente_deploy.log"
    if [ "${FAKE_FALHAR_DEPLOY:-}" = "1" ]; then exit 1; fi
    echo "VERSAO_IMAGEM=${VERSAO_IMAGEM:-}" >> "$estado/versao_deploy.log"
    echo "rag-pipeline-backend:${VERSAO_IMAGEM:-local}" > "$estado/servico_em_uso"
    exit 0 ;;
esac
exit 0
"""

GIT_FALSO = r"""#!/usr/bin/env bash
case "$1 $2" in
  "rev-parse --short") echo "${FAKE_GIT_VERSAO:-abc1234}" ;;
  "status --porcelain") [ -z "${FAKE_GIT_SUJO:-}" ] || echo " M deploy/exemplo.sh" ;;
esac
exit 0
"""

REPOSITORIOS = ("rag-pipeline-backend", "rag-pipeline-frontend", "rag-pipeline-backup")


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
            git = pasta / "git"
            git.write_text(GIT_FALSO)
            git.chmod(git.stat().st_mode | stat.S_IEXEC)
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

    def deploy(self, *args: str, **env_extra: str):
        env_extra.setdefault("DOMINIO_RAGPIPELINE", "app-teste.invalid")
        env_extra.setdefault("DATABASE_NODE_HOSTNAME", "no-de-dados")
        env_extra.setdefault("BACKUP_DOCKER_CONTEXT", "dados-teste")
        env_extra.setdefault("APPLICATION_NODE_HOSTNAME", "no-de-aplicacao")
        # SPEC-0041: Postgres e Qdrant são externos e vêm de variáveis.
        env_extra.setdefault("DATABASE_HOST", "db.exemplo.invalid")
        env_extra.setdefault("DATABASE_USER", "usuario.ref")
        env_extra.setdefault("QDRANT_URL", "https://qdrant.exemplo.invalid")
        return subprocess.run(
            ["bash", str(DEPLOY_SH), *args],
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

    # imagens e versões (SPEC-0035) --------------------------------------
    def semear_imagens(
        self,
        versoes: list[str],
        *,
        repositorios: tuple[str, ...] = REPOSITORIOS,
        em_uso: str | None = None,
        extras: list[str] | None = None,
    ) -> None:
        """Cria as imagens ``<repo>:<versao>`` (a primeira é a mais antiga)."""
        linhas = [f"{repo}:{versao}" for versao in versoes for repo in repositorios]
        linhas += extras or []
        (self.estado / "imagens.txt").write_text("\n".join(linhas) + "\n")
        if em_uso:
            (self.estado / "servico_em_uso").write_text(f"rag-pipeline-backend:{em_uso}\n")

    def etiquetas(self, repositorio: str) -> list[str]:
        """Etiquetas do repositório, da mais nova para a mais antiga."""
        arquivo = self.estado / "imagens.txt"
        linhas = arquivo.read_text().splitlines() if arquivo.exists() else []
        return [i.split(":", 1)[1] for i in reversed(linhas) if i.split(":", 1)[0] == repositorio]

    def removidas(self) -> list[str]:
        log = self.estado / "removidas.log"
        return log.read_text().splitlines() if log.exists() else []

    def versoes_implantadas(self) -> list[str]:
        log = self.estado / "versao_deploy.log"
        return log.read_text().splitlines() if log.exists() else []

    def ambiente_do_deploy(self) -> list[str]:
        log = self.estado / "ambiente_deploy.log"
        return log.read_text().splitlines() if log.exists() else []


def todos_os_secrets(versoes: dict[str, int] | None = None) -> dict[str, str]:
    """Os sete secrets de produção, cada um na versão pedida (padrão v1)."""
    padrao = {
        "openrouter_api_key": 1,
        "r2_credentials": 1,
        "postgres_password": 1,
        "qdrant_api_key": 1,
        "conexoes_chave": 1,
        "backup_chave": 1,
        "backup_r2_credentials": 1,
        "backup_avisos": 1,
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
    senha_postgres: str = "senha-postgres-sentinela-0041",
    chave_qdrant: str = "qdrant-sentinela-0041",
) -> str:
    return (
        f"{chave}\n{bucket}\n{endpoint}\n{acesso}\n{segredo}\n"
        f"{senha_postgres}\n{chave_qdrant}\n" + entrada_backup()
    )


def entrada_backup() -> str:
    return (
        "chave-ficticia-backup\nbackup-teste\nhttps://backup.invalid\nacesso-backup\n"
        "segredo-backup\nsmtp://smtp.invalid:587\naviso@teste.invalid\nsenha-ficticia\n"
        "aviso@teste.invalid\npessoa@teste.invalid\nhttps://chat.invalid/hook\n"
    )
