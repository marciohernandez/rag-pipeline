"""Apoio dos testes da SPEC-0032: `curl`, `openssl` e `getent` falsos para o script de conferência.

Os executáveis falsos substituem a rede: cada chamada é registrada em
``estado/chamadas.log`` e o resultado depende de variáveis de ambiente que ligam
uma falha por vez:

- ``FAKE_SEM_DNS``: o nome não resolve (``getent`` sai com 2, ``curl`` com 6);
- ``FAKE_CERT_INVALIDO``: o certificado é recusado (``curl`` HTTPS sai com 60, salvo
  com ``-k``/``--insecure``; ``openssl s_client`` informa ``Verify return code: 20``);
- ``FAKE_SEM_REDIRECT``: o acesso HTTP responde 200 em vez de redirecionar;
- ``FAKE_SEM_HSTS``: a resposta HTTPS não traz ``strict-transport-security``;
- ``FAKE_LENTO=<segundos>``: cada consulta demora esse tempo; o ``curl`` falso respeita
  ``--max-time``/``-m`` (dorme o limite e sai com 28), como o real.

Contrato de saída do script de conferência: uma linha por verificação, começando por
``OK`` ou ``FALHA`` e contendo o nome ``DNS``, ``Certificado``, ``Redirecionamento``
ou ``HSTS``.
"""

from __future__ import annotations

import shutil
import stat
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from tests._docker_falso import FERRAMENTAS

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "deploy" / "conferir_dominio.sh"

# Nome fictício em TLD reservado (RFC 2606); nenhum domínio real entra no repositório.
DOMINIO_DE_TESTE = "app-teste.invalid"

VERIFICACOES = ("DNS", "Certificado", "Redirecionamento", "HSTS")

_FERRAMENTAS_EXTRAS = ["timeout", "true", "false", "seq"]

CURL_FALSO = r"""#!/usr/bin/env bash
estado="${FAKE_REDE_ESTADO:?}"
echo "curl $*" >> "$estado/chamadas.log"
url=""; formato=""; limite=""; cabecalhos=0; inseguro=0
args=("$@")
for ((i = 0; i < ${#args[@]}; i++)); do
  a="${args[$i]}"
  case "$a" in
    http://*|https://*) url="$a" ;;
    -w|--write-out) formato="${args[$((i + 1))]}" ;;
    --max-time|-m) limite="${args[$((i + 1))]}" ;;
    --max-time=*) limite="${a#--max-time=}" ;;
    -D|--head|--include) cabecalhos=1 ;;
    -k|--insecure) inseguro=1 ;;
    --*) ;;
    -[!-]*I*|-[!-]*i*) cabecalhos=1 ;;
  esac
  case "$a" in
    -[!-]*k*) inseguro=1 ;;
  esac
done
esquema="${url%%://*}"
host="${url#*://}"; host="${host%%/*}"
if [ -n "${FAKE_LENTO:-}" ]; then
  if [ -n "$limite" ] && [ "$FAKE_LENTO" -gt "$limite" ]; then
    sleep "$limite"
    exit 28
  fi
  sleep "$FAKE_LENTO"
fi
if [ -n "${FAKE_SEM_DNS:-}" ]; then exit 6; fi
codigo=200; destino=""
if [ "$esquema" = "http" ] && [ -z "${FAKE_SEM_REDIRECT:-}" ]; then
  codigo=308; destino="https://$host/"
fi
if [ "$esquema" = "https" ] && [ -n "${FAKE_CERT_INVALIDO:-}" ] && [ "$inseguro" = 0 ]; then
  exit 60
fi
if [ "$cabecalhos" = 1 ]; then
  if [ "$codigo" = 308 ]; then
    printf 'HTTP/1.1 308 Permanent Redirect\r\nLocation: %s\r\n\r\n' "$destino"
  else
    printf 'HTTP/2 200\r\n'
    if [ "$esquema" = "https" ] && [ -z "${FAKE_SEM_HSTS:-}" ]; then
      printf 'strict-transport-security: max-age=86400\r\n'
    fi
    printf '\r\n'
  fi
fi
if [ -n "$formato" ]; then
  saida="${formato//%\{http_code\}/$codigo}"
  saida="${saida//%\{redirect_url\}/$destino}"
  saida="${saida//%\{url_effective\}/$url}"
  printf '%b' "$saida"
fi
exit 0
"""

OPENSSL_FALSO = r"""#!/usr/bin/env bash
estado="${FAKE_REDE_ESTADO:?}"
echo "openssl $*" >> "$estado/chamadas.log"
if [ -n "${FAKE_LENTO:-}" ]; then sleep "$FAKE_LENTO"; fi
case "$1" in
  s_client)
    cat > /dev/null
    if [ -n "${FAKE_SEM_DNS:-}" ]; then exit 1; fi
    printf -- '-----BEGIN CERTIFICATE-----\nFALSO\n-----END CERTIFICATE-----\n'
    if [ -n "${FAKE_CERT_INVALIDO:-}" ]; then
      echo "Verify return code: 20 (unable to get local issuer certificate)"
    else
      echo "Verify return code: 0 (ok)"
    fi
    exit 0 ;;
  x509)
    cat > /dev/null
    echo "notAfter=Dec 31 23:59:59 2099 GMT"
    echo "Certificate will not expire"
    exit 0 ;;
esac
exit 0
"""

GETENT_FALSO = r"""#!/usr/bin/env bash
estado="${FAKE_REDE_ESTADO:?}"
echo "getent $*" >> "$estado/chamadas.log"
[ "$1" = "hosts" ] || exit 2
if [ -n "${FAKE_SEM_DNS:-}" ]; then exit 2; fi
echo "203.0.113.10 $2"
exit 0
"""


@dataclass
class Execucao:
    codigo: int
    saida: str
    duracao: float


class RedeFalsa:
    """Diretório de trabalho de um teste: ferramentas de rede falsas e `PATH` isolado."""

    def __init__(self, tmp_path: Path) -> None:
        self.raiz = tmp_path
        self.estado = tmp_path / "estado"
        self.bin = tmp_path / "bin"
        for pasta in (self.estado, self.bin):
            pasta.mkdir(parents=True, exist_ok=True)
        for nome, corpo in (
            ("curl", CURL_FALSO),
            ("openssl", OPENSSL_FALSO),
            ("getent", GETENT_FALSO),
        ):
            arquivo = self.bin / nome
            arquivo.write_text(corpo)
            arquivo.chmod(arquivo.stat().st_mode | stat.S_IEXEC)
        for nome in [*FERRAMENTAS, *_FERRAMENTAS_EXTRAS]:
            destino = shutil.which(nome)
            if destino and not (self.bin / nome).exists():
                (self.bin / nome).symlink_to(destino)

    def env(self, **extra: str) -> dict[str, str]:
        ambiente = {
            "PATH": str(self.bin),
            "HOME": str(self.raiz),
            "FAKE_REDE_ESTADO": str(self.estado),
        }
        ambiente.update(extra)
        return ambiente

    def rodar(self, *args: str, **env_extra: str) -> Execucao:
        assert SCRIPT.exists(), "deploy/conferir_dominio.sh não existe"
        inicio = time.monotonic()
        resultado = subprocess.run(
            ["bash", str(SCRIPT), *args],
            env=self.env(**env_extra),
            cwd=RAIZ,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        return Execucao(
            codigo=resultado.returncode,
            saida=resultado.stdout + resultado.stderr,
            duracao=time.monotonic() - inicio,
        )

    def chamadas(self) -> list[str]:
        log = self.estado / "chamadas.log"
        return log.read_text().splitlines() if log.exists() else []
