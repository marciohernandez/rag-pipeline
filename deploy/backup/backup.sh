#!/usr/bin/env bash
set +x
set -Eeuo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/comum.sh"

# O limite envolve o ciclo inteiro; TERM permite avisar e limpar antes do KILL.
if [ "${1:-}" != --interno ] && command -v timeout >/dev/null; then
  exec timeout --signal=TERM --kill-after=90 "${BACKUP_TIMEOUT_SEGUNDOS:-3600}" bash "$0" --interno
fi
secrets=${BACKUP_SECRETS_DIR:-/run/secrets}
tmp=$(mktemp -d "${BACKUP_TMPDIR:-/tmp}/backup.XXXXXXXX")
etapa=configurar
pendente=""
finalizar() {
  local codigo=$?
  trap - EXIT TERM INT
  set +e
  if [ "$codigo" != 0 ]; then
    echo "etapa=$etapa fim resultado=falha"
    avisar
  fi
  [ -z "$pendente" ] || s3 s3 rm "$pendente" >/dev/null
  rm -rf -- "$tmp"
  echo "RESUMO resultado=$([ "$codigo" = 0 ] && echo sucesso || echo falha) etapa=$etapa"
  exit "$codigo"
}
trap finalizar EXIT
trap 'exit 124' TERM INT
# Não permitir mensagens de ferramentas que possam repetir credenciais.
exec 2>/dev/null
[ -s "$secrets/backup_chave" ]
configurar_s3 "$secrets/backup_r2_credentials"
configurar_pg
dia=$(date -d "${BACKUP_DATA:-$(date +%F)}" +%F)
diario="s3://$BACKUP_BUCKET/diarios/$dia.dump.enc"
semanal="s3://$BACKUP_BUCKET/semanais/$(date -d "$dia" +%G-S%V).dump.enc"
tentativas=${BACKUP_TENTATIVAS:-3}
[[ "$tentativas" =~ ^[1-9][0-9]*$ ]]

executar() {
  etapa=$1; shift
  echo "etapa=$etapa inicio"
  "$@"
  echo "etapa=$etapa fim resultado=sucesso"
}
dump() { pg_dump -Fc --no-password -f "$tmp/origem.dump"; }
cifrar() {
  openssl enc -aes-256-cbc -salt -pbkdf2 -pass "file:$secrets/backup_chave" \
    -in "$tmp/origem.dump" -out "$tmp/backup.enc"
}
validar_local() {
  [ "$(stat -c %s "$tmp/origem.dump")" -gt "${BACKUP_MIN_BYTES:-1024}" ]
  decifrar "$secrets/backup_chave" "$tmp/backup.enc" "$tmp/conferencia.dump"
  pg_restore --list "$tmp/conferencia.dump" >/dev/null
}
enviar() {
  local n
  # Um objeto provisório evita substituir o backup anterior com dados inválidos.
  pendente="s3://$BACKUP_BUCKET/pendentes/${tmp##*/}.enc"
  for ((n=1; n<=tentativas; n++)); do
    if s3 s3 cp "$tmp/backup.enc" "$pendente" >/dev/null; then return; fi
    [ "$n" = "$tentativas" ] || sleep "$(( ${BACKUP_ESPERA_SEGUNDOS:-5} * n ))"
  done
  return 1
}
verificar() {
  local tamanho remoto
  tamanho=$(stat -c %s "$tmp/backup.enc")
  remoto=$(s3 s3 ls "$pendente")
  [ "$(awk '{print $3}' <<< "$remoto")" = "$tamanho" ]
  s3 s3 cp "$pendente" "$tmp/remoto.enc" >/dev/null
  [ "$(openssl dgst -sha256 < "$tmp/remoto.enc")" = "$(openssl dgst -sha256 < "$tmp/backup.enc")" ]
  decifrar "$secrets/backup_chave" "$tmp/remoto.enc" "$tmp/conferencia.dump"
  pg_restore --list "$tmp/conferencia.dump" >/dev/null
  echo "data=$dia bytes=$tamanho verificar=sucesso"
}
publicar() {
  local anterior
  # A consulta de um objeto ainda ausente retorna 1 na CLI real.
  # Esta consulta só informa substituição; a cópia abaixo valida a publicação.
  if anterior=$(s3 s3 ls "$diario") && [ -n "$anterior" ]; then
    echo "data=$dia substituição do objeto diário"
  fi
  s3 s3 cp "$pendente" "$diario" >/dev/null
  echo "objeto=diarios/$dia.dump.enc"
  if [ "$(date -d "$dia" +%u)" = 7 ]; then
    s3 s3 cp "$pendente" "$semanal" >/dev/null
    echo "objeto=${semanal#s3://$BACKUP_BUCKET/}"
  fi
}
podar() {
  local prefixo=$1 manter=$2 lista nome quantidade
  # Listar a raiz retorna sucesso também num bucket sem cópia semanal.
  # A CLI retorna 1 para prefixos vazios; erros de rede continuam fatais aqui.
  lista=$(s3 s3 ls "s3://$BACKUP_BUCKET/" --recursive)
  # Só objetos de backup gerenciados, nunca subpastas ou nomes livres.
  lista=$(awk -v prefixo="$prefixo/" 'index($4,prefixo)==1 {print substr($4,length(prefixo)+1)}' \
    <<< "$lista" | grep -E "$3" | sort -r || true)
  quantidade=0
  while IFS= read -r nome; do
    [ -n "$nome" ] || continue
    quantidade=$((quantidade + 1))
    if [ "$quantidade" -gt "$manter" ]; then s3 s3 rm "s3://$BACKUP_BUCKET/$prefixo/$nome" >/dev/null; fi
  done <<< "$lista"
}
reter() {
  podar diarios 7 '^[0-9]{4}-[0-9]{2}-[0-9]{2}\.dump\.enc$'
  podar semanais 4 '^[0-9]{4}-S[0-9]{2}\.dump\.enc$'
  echo 'retenção=7_diários/4_semanais'
}
executar dump dump
executar cifrar cifrar
executar verificar validar_local
executar enviar enviar
executar verificar verificar
executar enviar publicar
executar reter reter
