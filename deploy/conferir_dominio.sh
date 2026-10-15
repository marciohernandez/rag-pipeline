#!/usr/bin/env bash
set -euo pipefail

dominio="${1:-${DOMINIO_RAGPIPELINE:-}}"
if (( $# > 1 )) || [[ -z "$dominio" ]]; then
  echo "Uso: deploy/conferir_dominio.sh <domínio> ou defina DOMINIO_RAGPIPELINE" >&2
  exit 2
fi
# Somente hostname, sem protocolo, caminho, credencial ou opções de comando.
if [[ ! "$dominio" =~ ^[[:alnum:]]([[:alnum:].-]*[[:alnum:]])?$ ]] ||
   [[ "$dominio" != *.* || "$dominio" == *..* || ${#dominio} -gt 253 ]]; then
  echo "Uso: informe um hostname em DOMINIO_RAGPIPELINE ou no argumento" >&2
  exit 2
fi
for ferramenta in timeout getent openssl curl awk; do
  if ! command -v "$ferramenta" >/dev/null; then
    echo "FALHA Dependência: instale $ferramenta" >&2
    exit 2
  fi
done
dominio="${dominio,,}"
falhas=0
resultado() {
  if [[ "$2" == 0 ]]; then
    printf 'OK %s\n' "$1"
  else
    printf 'FALHA %s\n' "$1"
    falhas=1
  fi
}
printf 'Conferindo domínio: %s\n' "$dominio"

dns=1
if timeout 10 getent hosts "$dominio" >/dev/null 2>&1; then dns=0; fi
resultado DNS "$dns"

# A cadeia e o hostname são conferidos sem expor a resposta TLS nos logs.
certificado=1
tls=""
if tls="$(timeout 10 openssl s_client -connect "${dominio}:443" \
    -servername "$dominio" -verify_hostname "$dominio" -verify_return_error \
    </dev/null 2>&1)"; then
  if [[ "$tls" == *"Verify return code: 0 (ok)"* ]]; then certificado=0; fi
fi
https_ok=1
cabecalhos=""
if cabecalhos="$(curl --silent --show-error --head --max-time 10 --connect-timeout 5 \
    --proto '=https' "https://${dominio}/login" 2>/dev/null)"; then
  https_ok=0
fi
if [[ "$https_ok" != 0 ]]; then certificado=1; fi
resultado Certificado "$certificado"

redirecionamento=1
http=""
if http="$(curl --silent --show-error --head --max-time 10 --connect-timeout 5 \
    --proto '=http' "http://${dominio}/" 2>/dev/null)"; then
  if awk -v destino="https://${dominio}/" '
    { sub(/\r$/, "") }
    /^HTTP\/[^ ]+ (301|308)( |$)/ { permanente=1 }
    tolower($1)=="location:" && $2==destino { correto=1 }
    END { exit !(permanente && correto) }
  ' <<< "$http"; then redirecionamento=0; fi
fi
resultado Redirecionamento "$redirecionamento"

hsts=1
if [[ "$https_ok" == 0 ]] && awk '
    tolower($0) ~ /^strict-transport-security:[[:space:]]*max-age=[0-9]+/ {
      valor=tolower($0); sub(/.*max-age=/, "", valor)
      if (valor+0>0) presente=1
    }
    END { exit !presente }
  ' <<< "$cabecalhos"; then hsts=0; fi
resultado HSTS "$hsts"
exit "$falhas"
