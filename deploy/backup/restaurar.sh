#!/usr/bin/env bash
set +x
set -Eeuo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/comum.sh"
objeto=${1:?Informe o objeto diarios/AAAA-MM-DD.dump.enc}; shift
destino=""; chave=""; credenciais=""; banco="restauracao_$(date -u +%Y%m%d%H%M%S)"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --destino) destino=${2:?}; shift 2 ;;
    --chave-arquivo) chave=${2:?}; shift 2 ;;
    --credenciais-arquivo) credenciais=${2:?}; shift 2 ;;
    --banco) banco=${2:?}; shift 2 ;;
    *) echo 'Parâmetro desconhecido.' >&2; exit 1 ;;
  esac
done
[[ "$objeto" =~ ^(diarios/[0-9]{4}-[0-9]{2}-[0-9]{2}|semanais/[0-9]{4}-S[0-9]{2})\.dump\.enc$ ]]
[[ "$destino" =~ ^[a-zA-Z0-9._-]+:[0-9]+$ ]]
[[ "$banco" =~ ^[a-z][a-z0-9_]{0,62}$ ]]
tmp=$(mktemp -d "${BACKUP_TMPDIR:-/tmp}/restauracao.XXXXXXXX")
finalizar() {
  local codigo=$?
  trap - EXIT
  rm -rf -- "$tmp"
  if [ "$codigo" != 0 ]; then echo 'Restauração recusada ou falhou. Confira objeto, chave, conexão e banco de destino.' >&3; fi
  exit "$codigo"
}
trap finalizar EXIT
trap 'exit 124' TERM INT
# Diagnóstico seguro: nunca repetir URL autenticada nem stderr dos clientes.
exec 3>&2
exec 2>/dev/null
configurar_s3 "$credenciais"
[ -s "$chave" ]
s3 s3 cp "s3://$BACKUP_BUCKET/$objeto" "$tmp/backup.enc" >/dev/null
decifrar "$chave" "$tmp/backup.enc" "$tmp/backup.dump"
pg_restore --list "$tmp/backup.dump" >/dev/null
configurar_pg
export PGHOST=${destino%:*} PGPORT=${destino##*:} PGDATABASE=postgres
existe=$(psql --no-password -X -At -v ON_ERROR_STOP=1 -c "SELECT 1 FROM pg_database WHERE datname='$banco'")
[ -z "$existe" ]
# CREATE falha atomicamente se outra execução criar o mesmo nome neste intervalo.
psql --no-password -X -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"$banco\"" >/dev/null
PGDATABASE="$banco" pg_restore --no-password --exit-on-error --no-owner --no-privileges \
  --dbname "$banco" "$tmp/backup.dump" >/dev/null
echo "Restaurado no banco novo: $banco. Confira as tabelas antes de usar."
