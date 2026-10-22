"""Apoio dos testes da SPEC-0034: binários falsos para o ciclo de backup e a restauração.

Cada binário falso fica em ``bin/`` e registra os argumentos de cada chamada em
``logs/<binário>.log`` (nunca a entrada padrão, exceto ``curl``, cujo arquivo de
configuração lido da entrada padrão vai para ``logs/curl_stdin.log``). O bucket
de backup é um diretório; ``aws s3 ls`` imita a saída real (nomes relativos ao
prefixo). ``openssl`` é o real: a cifragem é verificada de ponta a ponta.
"""

# ruff: noqa: E501

from __future__ import annotations

import shutil
import stat
import subprocess
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BACKUP_SH = RAIZ / "deploy" / "backup" / "backup.sh"
AGENDAR_SH = RAIZ / "deploy" / "backup" / "agendar.sh"
RESTAURAR_SH = RAIZ / "deploy" / "backup" / "restaurar.sh"

CHAVE = "chave-sentinela-0034"
R2_SEGREDO = "segredo-r2-sentinela-0034"
R2_ACESSO = "AKIASENTINELA0034"
SMTP_SENHA = "senha-smtp-sentinela-0034"
WEBHOOK_TOKEN = "token-webhook-sentinela-0034"
PG_SENHA = "senha-pg-sentinela-0034"
DUMP_EM_CLARO = "SENTINELA-DUMP-EM-CLARO-0034"
SEGREDOS = [CHAVE, R2_SEGREDO, SMTP_SENHA, WEBHOOK_TOKEN, PG_SENHA]
BUCKET = "bucket-backup-sentinela"

FERRAMENTAS = [
    "bash", "env", "cat", "tr", "head", "tail", "sort", "uniq", "sed", "awk", "grep",
    "cut", "wc", "mkdir", "rm", "date", "openssl", "ls", "basename", "dirname", "tee",
    "xargs", "mktemp", "sleep", "printf", "test", "cp", "mv", "stat", "find", "touch",
    "dd", "od", "base64", "seq", "expr", "true", "false",
]  # fmt: skip

AWS_FALSO = r"""#!/usr/bin/env bash
dir="${FAKE_BUCKET_DIR:?}"
echo "$*" >> "${FAKE_LOG_DIR:?}/aws.log"
args=()
while [ $# -gt 0 ]; do
  case "$1" in
    --endpoint-url) shift 2 ;;
    *) args+=("$1"); shift ;;
  esac
done
set -- "${args[@]}"
[ "$1" = "s3" ] || exit 1
cmd="$2"
chave_de() { local u="${1#s3://}"; echo "${u#*/}"; }
case "$cmd" in
  cp)
    src="$3"; dst="$4"
    if [[ "$src" == s3://* ]]; then
      k="$(chave_de "$src")"
      [ -f "$dir/$k" ] || { echo "NoSuchKey: $k" >&2; exit 1; }
      if [[ "$dst" == s3://* ]]; then
        d="$(chave_de "$dst")"; mkdir -p "$(dirname "$dir/$d")"; cp "$dir/$k" "$dir/$d"
      else
        cp "$dir/$k" "$dst"
      fi
    else
      if [ "${FAKE_AWS_FALHA_ENVIO:-}" = "1" ]; then echo "falha simulada no envio" >&2; exit 1; fi
      k="$(chave_de "$dst")"; mkdir -p "$(dirname "$dir/$k")"; cp "$src" "$dir/$k"
    fi ;;
  ls)
    prefixo="$(chave_de "$3")"
    # A CLI real retorna 1 quando a consulta de um objeto exato não o encontra.
    if [[ "$prefixo" == *.enc ]] && [ ! -f "$dir/$prefixo" ]; then exit 1; fi
    if [[ "$prefixo" == */ ]] && [ ! -d "$dir/$prefixo" ]; then exit 1; fi
    base="${prefixo%"${prefixo##*/}"}"
    if [ -d "$dir" ]; then
      (cd "$dir" && find . -type f | sed 's|^\./||' | sort) | while read -r f; do
        case "$f" in
          "$prefixo"*) echo "2026-10-14 03:00:00 $(stat -c %s "$dir/$f") ${f#"$base"}" ;;
        esac
      done
    fi ;;
  rm)
    k="$(chave_de "$3")"; rm -f "$dir/$k" ;;
  *) exit 1 ;;
esac
exit 0
"""

PG_DUMP_FALSO = r"""#!/usr/bin/env bash
echo "$*" >> "${FAKE_LOG_DIR:?}/pg_dump.log"
if [ "${FAKE_PG_DUMP_FALHA:-}" = "1" ]; then echo "pg_dump: falha simulada" >&2; exit 1; fi
out=""
while [ $# -gt 0 ]; do
  case "$1" in -f|--file) out="$2"; shift 2 ;; *) shift ;; esac
done
bytes="${FAKE_DUMP_BYTES:-4096}"
if [ "$bytes" = "0" ]; then : > "$out"; exit 0; fi
cabecalho="PGDMP"
[ "${FAKE_DUMP_INVALIDO:-}" = "1" ] && cabecalho="XXXXX"
{ printf '%s' "$cabecalho"; printf '%s' "SENTINELA-DUMP-EM-CLARO-0034"; head -c "$bytes" /dev/zero | tr '\0' 'a'; } > "$out"
exit 0
"""

PG_RESTORE_FALSO = r"""#!/usr/bin/env bash
echo "$*" >> "${FAKE_LOG_DIR:?}/pg_restore.log"
arquivo="${@: -1}"
case " $* " in
  *" --list "*|*" -l "*)
    [ "$(head -c 5 "$arquivo")" = "PGDMP" ] || { echo "pg_restore: formato inválido" >&2; exit 1; }
    echo "; tabela_fake" ;;
esac
exit 0
"""

PSQL_FALSO = r"""#!/usr/bin/env bash
echo "$*" >> "${FAKE_LOG_DIR:?}/psql.log"
bancos="${FAKE_DBS_FILE:?}"
todo="$*"
if [[ "$todo" == *"FROM pg_database"* ]]; then
  nome="${todo#*datname=\'}"; nome="${nome%%\'*}"
  grep -qx "$nome" "$bancos" && echo 1
  exit 0
fi
if [[ "$todo" == *"CREATE DATABASE"* ]]; then
  nome="${todo#*CREATE DATABASE }"; nome="${nome//\"/}"; nome="${nome%%;*}"; nome="${nome%% *}"
  echo "$nome" >> "$bancos"
  exit 0
fi
exit 0
"""

CURL_FALSO = r"""#!/usr/bin/env bash
logs="${FAKE_LOG_DIR:?}"
echo "$*" >> "$logs/curl_args.log"
cfg="$(cat)"
printf '%s\n' "$cfg" >> "$logs/curl_stdin.log"
if [[ "$cfg" == *smtp* ]]; then tipo=smtp; else tipo=webhook; fi
echo "$tipo" >> "$logs/curl_tipos.log"
corpo=""
while [ $# -gt 0 ]; do
  case "$1" in
    -T|--upload-file) corpo="$2"; shift 2 ;;
    --data-binary) corpo="${2#@}"; shift 2 ;;
    *) shift ;;
  esac
done
n="$(wc -l < "$logs/curl_tipos.log")"
[ -n "$corpo" ] && [ -f "$corpo" ] && cp "$corpo" "$logs/corpo_${tipo}_${n}.txt"
if [ "$tipo" = "smtp" ] && [ "${FAKE_CURL_FALHA_SMTP:-}" = "1" ]; then echo "smtp indisponível" >&2; exit 22; fi
if [ "$tipo" = "webhook" ] && [ "${FAKE_CURL_FALHA_WEBHOOK:-}" = "1" ]; then echo "webhook indisponível" >&2; exit 22; fi
exit 0
"""

DOCKER_FALSO = r"""#!/usr/bin/env bash
echo "$*" >> "${FAKE_LOG_DIR:?}/docker.log"
exit 0
"""


def semana(dia: str) -> str:
    iso = date.fromisoformat(dia).isocalendar()
    return f"{iso.year}-S{iso.week:02d}"


class AmbienteBackup:
    """Diretório de trabalho de um teste: binários falsos, segredos, bucket e logs."""

    def __init__(self, tmp_path: Path, *, avisos: bool = True) -> None:
        self.raiz = tmp_path
        self.bin = tmp_path / "bin"
        self.bucket = tmp_path / "bucket"
        self.segredos = tmp_path / "segredos"
        self.tmp = tmp_path / "tmp"
        self.logs = tmp_path / "logs"
        for pasta in (self.bin, self.bucket, self.segredos, self.tmp, self.logs):
            pasta.mkdir(parents=True, exist_ok=True)
        for nome, script in {
            "aws": AWS_FALSO,
            "pg_dump": PG_DUMP_FALSO,
            "pg_restore": PG_RESTORE_FALSO,
            "psql": PSQL_FALSO,
            "curl": CURL_FALSO,
            "docker": DOCKER_FALSO,
        }.items():
            falso = self.bin / nome
            falso.write_text(script)
            falso.chmod(falso.stat().st_mode | stat.S_IEXEC)
        for nome in FERRAMENTAS:
            destino = shutil.which(nome)
            if destino and not (self.bin / nome).exists():
                (self.bin / nome).symlink_to(destino)
        (self.segredos / "backup_chave").write_text(CHAVE)
        (self.segredos / "postgres_password").write_text(PG_SENHA)
        (self.segredos / "backup_r2_credentials").write_text(
            f"AWS_ACCESS_KEY_ID={R2_ACESSO}\n"
            f"AWS_SECRET_ACCESS_KEY={R2_SEGREDO}\n"
            "R2_ENDPOINT=https://r2.exemplo.invalid\n"
            f"BACKUP_BUCKET={BUCKET}\n"
        )
        if avisos:
            (self.segredos / "backup_avisos").write_text(
                "SMTP_URL=smtp://smtp.exemplo.invalid:587\n"
                "SMTP_USER=aviso@exemplo.invalid\n"
                f"SMTP_PASSWORD={SMTP_SENHA}\n"
                "SMTP_FROM=aviso@exemplo.invalid\n"
                "SMTP_TO=marcio@exemplo.invalid\n"
                f"WEBHOOK_URL=https://chat.exemplo.invalid/hook/{WEBHOOK_TOKEN}\n"
            )
        self.bancos = tmp_path / "bancos.txt"
        self.bancos.write_text("postgres\nrag_pipeline\n")

    # execução --------------------------------------------------------------
    def env(self, **extra: str) -> dict[str, str]:
        ambiente = {
            "PATH": str(self.bin),
            "HOME": str(self.raiz),
            "BACKUP_SECRETS_DIR": str(self.segredos),
            "BACKUP_TMPDIR": str(self.tmp),
            "BACKUP_DATA": "2026-10-14",
            "BACKUP_MIN_BYTES": "1024",
            "BACKUP_TENTATIVAS": "3",
            "BACKUP_ESPERA_SEGUNDOS": "0",
            "FAKE_BUCKET_DIR": str(self.bucket),
            "FAKE_LOG_DIR": str(self.logs),
            "FAKE_DBS_FILE": str(self.bancos),
            # SPEC-0041: o Postgres é externo e o ciclo exige o destino explícito.
            "PGHOST": "db.exemplo.invalid",
            "PGPORT": "5432",
            "PGUSER": "usuario.ref",
            "PGDATABASE": "postgres",
            "PGSSLMODE": "require",
        }
        ambiente.update(extra)
        return ambiente

    def _rodar(self, comando: list[str], entrada: str = "", **env: str):
        return subprocess.run(
            comando,
            input=entrada,
            env=self.env(**env),
            cwd=RAIZ,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

    def trocar_pg_dump_para_registrar_ambiente(self) -> None:
        """Faz o `pg_dump` falso registrar as variáveis PG* que recebeu (SPEC-0041)."""
        destino = self.bin / "pg_dump"
        corpo = destino.read_text().replace(
            'echo "$*" >> "${FAKE_LOG_DIR:?}/pg_dump.log"',
            'echo "$*" >> "${FAKE_LOG_DIR:?}/pg_dump.log"\n'
            'env | grep -E "^PG(HOST|PORT|USER|DATABASE|SSLMODE)=" '
            '>> "${FAKE_LOG_DIR:?}/pg_dump_env.log"',
            1,
        )
        destino.write_text(corpo)

    def backup(self, **env: str):
        return self._rodar(["bash", str(BACKUP_SH)], **env)

    def agendar(self, *args: str, **env: str):
        return self._rodar(["bash", str(AGENDAR_SH), *args], **env)

    def restaurar(self, *args: str, **env: str):
        return self._rodar(["bash", str(RESTAURAR_SH), *args], **env)

    # leitura do estado -----------------------------------------------------
    def semear(self, chave: str, conteudo: bytes = b"semente" * 300) -> None:
        destino = self.bucket / chave
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)

    def objetos(self, prefixo: str = "") -> list[str]:
        return sorted(
            str(arquivo.relative_to(self.bucket))
            for arquivo in self.bucket.rglob("*")
            if arquivo.is_file() and str(arquivo.relative_to(self.bucket)).startswith(prefixo)
        )

    def log(self, nome: str) -> list[str]:
        arquivo = self.logs / f"{nome}.log"
        return arquivo.read_text().splitlines() if arquivo.exists() else []

    def envios(self) -> list[str]:
        """Chamadas `aws s3 cp` cujo destino é o bucket (envios e cópias)."""
        return [
            c
            for c in self.log("aws")
            if c.startswith("s3 cp ") and c.split()[-1].startswith("s3://")
        ]

    def corpos(self) -> str:
        return "\n".join(p.read_text() for p in sorted(self.logs.glob("corpo_*.txt")))

    def tudo_que_vaza(self, *resultados) -> str:
        """Saída dos processos mais os argumentos registrados pelos falsos."""
        partes = [r.stdout + r.stderr for r in resultados]
        for nome in ("aws", "pg_dump", "pg_restore", "psql", "curl_args", "docker"):
            partes.append("\n".join(self.log(nome)))
        partes.append(self.corpos())
        return "\n".join(partes)

    def descriptografar(self, chave_do_objeto: str) -> bytes:
        resultado = subprocess.run(
            [
                "openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
                "-pass", f"file:{self.segredos / 'backup_chave'}",
                "-in", str(self.bucket / chave_do_objeto),
            ],
            capture_output=True,
            check=False,
        )  # fmt: skip
        assert resultado.returncode == 0, resultado.stderr
        return resultado.stdout
