#!/usr/bin/env bash
# SPEC-0032: confere DNS, certificado, redirecionamento HTTP e HSTS do domínio público.
# Uso: deploy/conferir_dominio.sh <dominio>   (o mesmo valor de DOMINIO_RAGPIPELINE)
# Cada verificação imprime uma linha `OK` ou `FALHA`; sai com código diferente de 0
# se alguma reprovar. Cada consulta tem limite de 10 s (o total fica abaixo de 60 s).

set -uo pipefail

dominio="${1:-}"
if [ -z "$dominio" ]; then
  echo "Uso: deploy/conferir_dominio.sh <dominio>  (o valor de DOMINIO_RAGPIPELINE)" >&2
  exit 2
fi

falhas=0

registrar() {
  if [ "$1" = ok ]; then
    echo "OK     $2: $3"
  else
    echo "FALHA  $2: $3"
    falhas=$((falhas + 1))
  fi
}

# DNS
if timeout 10 getent hosts "$dominio" > /dev/null 2>&1; then
  registrar ok DNS "$dominio resolve"
else
  registrar falha DNS "$dominio não resolve"
fi

# Certificado: verificação padrão do curl contra a cadeia confiável.
if curl --silent --output /dev/null --max-time 10 "https://$dominio/" > /dev/null 2>&1; then
  registrar ok Certificado "certificado válido em https://$dominio/"
else
  registrar falha Certificado "https://$dominio/ não foi aceito (certificado inválido, ausente ou sem resposta)"
fi

# Redirecionamento HTTP -> HTTPS
destino="$(curl --silent --output /dev/null --max-time 10 \
  --write-out '%{http_code} %{redirect_url}' "http://$dominio/" 2> /dev/null || true)"
codigo="${destino%% *}"
local_redirect="${destino#* }"
case "$codigo" in
  301 | 308)
    if [ "${local_redirect#https://}" != "$local_redirect" ]; then
      registrar ok Redirecionamento "HTTP responde $codigo para $local_redirect"
    else
      registrar falha Redirecionamento "HTTP responde $codigo, mas não para HTTPS"
    fi
    ;;
  *)
    registrar falha Redirecionamento "HTTP não redireciona permanentemente (resposta: ${codigo:-sem resposta})"
    ;;
esac

# HSTS
cabecalhos="$(curl --silent --head --max-time 10 "https://$dominio/" 2> /dev/null || true)"
if printf '%s' "$cabecalhos" | grep -qi '^strict-transport-security:'; then
  registrar ok HSTS "cabeçalho strict-transport-security presente"
else
  registrar falha HSTS "cabeçalho strict-transport-security ausente em https://$dominio/"
fi

[ "$falhas" -eq 0 ]
