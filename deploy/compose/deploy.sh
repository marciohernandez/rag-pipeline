#!/usr/bin/env bash
# Deploy em Compose (SPEC-0045): publica exatamente o commit HEAD na VPS, por SSH.
#
#   deploy/compose/deploy.sh                    # publica o HEAD (já enviado ao remoto)
#   deploy/compose/deploy.sh --versao <sha>     # volta a uma versão já construída
#
# A configuração do servidor vem de um arquivo shell FORA do repositório, apontado por
# DEPLOY_CONFIG (permissão 600): DEPLOY_HOST, DEPLOY_USER (deploy), DEPLOY_KEY,
# DEPLOY_PATH e, opcionais, DEPLOY_PORT e DEPLOY_REPOSITORY (padrão: origin).
# Nunca usa down, nem remove volume: o banco vive em ragpipeline_postgres_data.

set -euo pipefail

falha() {
  echo "$*" >&2
  exit 1
}

versao_pedida=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --versao)
      versao_pedida="${2:?Informe a etiqueta depois de --versao}"
      shift 2
      ;;
    *) falha "Uso: deploy/compose/deploy.sh [--versao <etiqueta>]" ;;
  esac
done
etiqueta_valida='^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$'
if [ -n "$versao_pedida" ] && [[ ! "$versao_pedida" =~ $etiqueta_valida ]]; then
  falha "Etiqueta de versão inválida."
fi

: "${DEPLOY_CONFIG:?Defina DEPLOY_CONFIG com o arquivo de configuração do servidor (fora do repositório)}"
[ -f "$DEPLOY_CONFIG" ] || falha "DEPLOY_CONFIG não é um arquivo: $DEPLOY_CONFIG"
[ "$(stat -c %a "$DEPLOY_CONFIG")" = 600 ] || falha "O arquivo de DEPLOY_CONFIG precisa ter permissão 600."
# shellcheck disable=SC1090
. "$DEPLOY_CONFIG"
for variavel in DEPLOY_HOST DEPLOY_USER DEPLOY_KEY DEPLOY_PATH; do
  [ -n "${!variavel:-}" ] || falha "Defina $variavel em DEPLOY_CONFIG."
done
[ "$DEPLOY_USER" = deploy ] || falha "DEPLOY_USER precisa ser deploy; nunca root."
[ -r "$DEPLOY_KEY" ] || falha "DEPLOY_KEY não é legível."
deploy_repositorio="${DEPLOY_REPOSITORY:-origin}"
[[ "$DEPLOY_PATH" =~ ^/[A-Za-z0-9_./-]+$ ]] || falha "DEPLOY_PATH precisa ser um caminho absoluto simples."
[[ "$deploy_repositorio" =~ ^[A-Za-z0-9_.-]+$ ]] || falha "DEPLOY_REPOSITORY inválido."
[[ "$DEPLOY_HOST" =~ ^[A-Za-z0-9_.-]+$ ]] || falha "DEPLOY_HOST inválido."

sha=""
versao="$versao_pedida"
if [ -z "$versao_pedida" ]; then
  if [ -n "$(git status --porcelain)" ]; then
    falha "Há alterações não commitadas: elas não vão para o servidor. Faça o commit antes do deploy."
  fi
  sha="$(git rev-parse HEAD)"
  [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || falha "Não foi possível identificar o commit HEAD."
  [ -n "$(git branch -r --contains "$sha")" ] || falha "O commit HEAD ainda não está no remoto. Faça o push antes do deploy."
  versao="$(git rev-parse --short HEAD)"
  [[ "$versao" =~ $etiqueta_valida ]] || falha "Não foi possível identificar a versão pelo commit atual."
fi

opcoes_ssh=(-i "$DEPLOY_KEY" -o BatchMode=yes -o StrictHostKeyChecking=yes -o ForwardAgent=no)
[ -z "${DEPLOY_PORT:-}" ] || opcoes_ssh+=(-p "$DEPLOY_PORT")

echo "Versão das imagens: $versao"
ssh "${opcoes_ssh[@]}" "$DEPLOY_USER@$DEPLOY_HOST" \
  bash -s -- "${sha:-sem-commit}" "$versao" "$DEPLOY_PATH" "$deploy_repositorio" \
  "$([ -n "$versao_pedida" ] && echo retorno || echo publicacao)" <<'REMOTO'
set -euo pipefail
sha=$1 versao=$2 caminho=$3 repositorio=$4 modo=$5

falha() {
  echo "$*" >&2
  exit 1
}

cd "$caminho"
for ferramenta in git docker; do
  command -v "$ferramenta" > /dev/null || falha "Falta $ferramenta no servidor."
done
docker compose version > /dev/null || falha "Falta o Docker Compose v2 no servidor."
docker network inspect n8n-dev-stack_traefik_net > /dev/null 2>&1 \
  || falha "A rede n8n-dev-stack_traefik_net não existe; ela pertence ao Traefik e não é criada aqui."
[ -r .env ] || falha "Falta o .env do servidor em $caminho/.env."
[ "$(stat -c %a .env)" = 600 ] || falha "O .env do servidor precisa ter permissão 600."

segredos="$(sed -n 's/^SEGREDOS_DIR=//p' .env | tail -n 1)"
[ -d "$segredos" ] || falha "SEGREDOS_DIR do .env não é uma pasta."
for nome in openrouter_api_key r2_credentials conexoes_chave postgres_password qdrant_api_key \
  backup_chave backup_r2_credentials backup_avisos; do
  [ -f "$segredos/$nome" ] || falha "Segredo ausente: $nome (esperado em SEGREDOS_DIR)."
  [ "$(stat -c %a "$segredos/$nome")" = 600 ] || falha "O segredo $nome precisa ter permissão 600."
done

dc() {
  VERSAO_IMAGEM="$versao" docker compose -p ragpipeline --env-file .env \
    -f deploy/compose/compose.yml -f deploy/compose/compose.homolog.yml "$@"
}

if [ "$modo" = publicacao ]; then
  git fetch "$repositorio" "$sha"
  git checkout --detach "$sha"
  [ -z "$(git status --porcelain)" ] || falha "A árvore do servidor não está limpa."
fi
dc config -q

if [ "$modo" = retorno ]; then
  for imagem in backend frontend backup; do
    docker image inspect "rag-pipeline-$imagem:$versao" > /dev/null 2>&1 \
      || falha "A imagem rag-pipeline-$imagem:$versao não existe neste servidor."
  done
else
  dc build
fi

banco_existia=nao
docker volume inspect ragpipeline_postgres_data > /dev/null 2>&1 && banco_existia=sim
dc up -d --no-build --wait postgres_ragpipeline

if [ "$modo" = publicacao ]; then
  if [ "$banco_existia" = sim ]; then
    echo "Backup antes da migração..."
    dc exec -T backup_ragpipeline bash /backup/backup.sh \
      || falha "O backup falhou; a migração e o deploy foram interrompidos."
  else
    echo "Primeira instalação: sem dados para copiar; o backup foi dispensado."
  fi
  echo "Aplicando as migrations..."
  dc run --rm --no-deps -T backend_ragpipeline /bin/sh -ec \
    'export APP_DATABASE_URL="$(python -c "import os; from pathlib import Path; from urllib.parse import quote; e = os.environ; print(\"postgresql+psycopg://{}:{}@{}:{}/{}?sslmode={}\".format(quote(e[\"DATABASE_USER\"], safe=\"\"), quote(Path(\"/run/secrets/postgres_password\").read_text().strip(), safe=\"\"), e[\"DATABASE_HOST\"], e[\"DATABASE_PORT\"], e[\"DATABASE_NAME\"], e[\"DATABASE_SSLMODE\"]))")"; exec alembic upgrade head' \
    || falha "A migração falhou; a versão nova não foi iniciada. Veja deploy/BACKUP.md para restaurar."
fi

if ! dc up -d --no-build --wait; then
  dc ps || true
  dc logs --tail=50 || true
  falha "Algum serviço não ficou saudável. Veja o retorno em deploy/RUNBOOK_COMPOSE.md."
fi
dc ps
echo "Versão implantada: $versao"
REMOTO
