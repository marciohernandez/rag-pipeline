#!/usr/bin/env bash
# Funções compartilhadas; secrets são dados, nunca código executável.
set +x
umask 077

ler_config() {
  local linha nome valor
  while IFS= read -r linha || [ -n "$linha" ]; do
    [[ "$linha" == *=* ]] || continue
    nome=${linha%%=*}; valor=${linha#*=}
    case "$nome" in
      AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|R2_ENDPOINT|BACKUP_BUCKET|SMTP_URL|SMTP_USER|SMTP_PASSWORD|SMTP_FROM|SMTP_TO|WEBHOOK_URL)
        # O provisionador escreve KEY=valor literal, inclusive aspas e cifrões.
        printf -v "$nome" '%s' "$valor"
        ;;
    esac
  done < "$1"
}

configurar_s3() {
  ler_config "$1"
  : "${AWS_ACCESS_KEY_ID:?}" "${AWS_SECRET_ACCESS_KEY:?}" "${R2_ENDPOINT:?}" "${BACKUP_BUCKET:?}"
  [[ "$R2_ENDPOINT" =~ ^https?://[^[:space:]@]+$ ]] || return 1
  [[ "$BACKUP_BUCKET" =~ ^[a-z0-9][a-z0-9.-]+$ ]] || return 1
  export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
  export AWS_DEFAULT_REGION=auto AWS_EC2_METADATA_DISABLED=true AWS_PAGER=""
}

s3() { local grupo=$1 acao=$2; shift 2; aws "$grupo" "$acao" --endpoint-url "$R2_ENDPOINT" "$@" 2>/dev/null; }

configurar_pg() {
  export PGHOST="${PGHOST:-postgres_ragpipeline}" PGPORT="${PGPORT:-5432}"
  export PGUSER="${PGUSER:-rag_pipeline}" PGDATABASE="${PGDATABASE:-rag_pipeline}"
  export PGCONNECT_TIMEOUT=15
  export PGPASSWORD
  PGPASSWORD=$(cat "${BACKUP_SECRETS_DIR:-/run/secrets}/postgres_password")
}

decifrar() {
  openssl enc -d -aes-256-cbc -pbkdf2 -pass "file:$1" -in "$2" -out "$3" 2>/dev/null
}

# curl lê URLs e autenticação pela entrada padrão, sem valores no argv.
campo_curl() {
  local valor=$2
  [[ "$valor" != *$'\n'* && "$valor" != *$'\r'* ]] || return 1
  valor=${valor//\\/\\\\}; valor=${valor//\"/\\\"}
  printf '%s = "%s"\n' "$1" "$valor"
}

avisar() {
  local mensagem="Backup falhou: etapa=$etapa" cfg
  local tls=(--ssl-reqd)
  [ "${BACKUP_SMTP_TLS:-1}" != 0 ] || tls=()
  [ -r "$secrets/backup_avisos" ] || { echo 'Avisos indisponíveis: secret ausente.'; return; }
  ler_config "$secrets/backup_avisos"
  printf 'From: %s\nTo: %s\nSubject: Falha no backup PostgreSQL\n\n%s\n' \
    "${SMTP_FROM:-}" "${SMTP_TO:-}" "$mensagem" > "$tmp/email"
  if cfg=$(campo_curl url "${SMTP_URL:-}" && campo_curl user "${SMTP_USER:-}:${SMTP_PASSWORD:-}"); then
    if ! printf '%s\n' "$cfg" | curl --config - --silent --show-error --fail --max-time 30 \
      "${tls[@]}" --mail-from "${SMTP_FROM:-}" --mail-rcpt "${SMTP_TO:-}" --upload-file "$tmp/email" >/dev/null 2>&1; then
      echo 'Aviso por e-mail falhou.'
    fi
  else echo 'Aviso por e-mail falhou: configuração inválida.'; fi
  printf '{"text":"%s"}\n' "$mensagem" > "$tmp/chat.json"
  if cfg=$(campo_curl url "${WEBHOOK_URL:-}"); then
    if ! printf '%s\n' "$cfg" | curl --config - --silent --show-error --fail --max-time 30 \
      --header 'Content-Type: application/json' --data-binary "@$tmp/chat.json" >/dev/null 2>&1; then
      echo 'Aviso por webhook falhou.'
    fi
  else echo 'Aviso por webhook falhou: configuração inválida.'; fi
}
