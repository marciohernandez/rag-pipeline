#!/usr/bin/env bash
set +x
set -euo pipefail
export TZ=UTC
hora=${BACKUP_HORA:-03:00}
[[ "$hora" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]$ ]] || { echo 'BACKUP_HORA inválida (HH:MM UTC).' >&2; exit 1; }
espera() {
  local agora=$1 h m s alvo atual
  [[ "$agora" =~ ^([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$ ]] || return 1
  IFS=: read -r h m s <<< "$agora"
  atual=$((10#$h * 3600 + 10#$m * 60 + 10#$s))
  alvo=$((10#${hora%:*} * 3600 + 10#${hora#*:} * 60))
  echo "$(( (alvo - atual + 86399) % 86400 + 1 ))"
}
if [ "${1:-}" = --espera ]; then espera "${2:?}"; exit; fi
limite=0
if [ "${1:-}" = --iteracoes ]; then limite=${2:?}; [[ "$limite" =~ ^[1-9][0-9]*$ ]]; fi
quantidade=0
filho=""
trap '[ -z "$filho" ] || kill -TERM "$filho" 2>/dev/null || true; wait 2>/dev/null || true; exit 0' TERM INT
while :; do
  if [ "${BACKUP_SEM_ESPERA:-0}" != 1 ]; then
    sleep "$(espera "$(date +%H:%M:%S)")" & filho=$!
    wait "$filho" || true
  fi
  bash "${BACKUP_CICLO:-$(dirname -- "${BASH_SOURCE[0]}")/backup.sh}" & filho=$!
  if ! wait "$filho"; then echo 'Ciclo falhou; próxima janela mantida.'; fi
  filho=""
  quantidade=$((quantidade + 1))
  if [ "$limite" -gt 0 ] && [ "$quantidade" -ge "$limite" ]; then break; fi
done
