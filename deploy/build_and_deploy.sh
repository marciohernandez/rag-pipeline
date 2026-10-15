#!/usr/bin/env bash

set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

# Exigir o domínio antes de consultar o Swarm ou construir imagens.
: "${DOMINIO_RAGPIPELINE:?Defina DOMINIO_RAGPIPELINE com export antes de executar deploy/build_and_deploy.sh}"
export DOMINIO_RAGPIPELINE
export TRAEFIK_CERT_RESOLVER="${TRAEFIK_CERT_RESOLVER:-letsencryptresolver}"
export TRAEFIK_ENTRYPOINT_HTTPS="${TRAEFIK_ENTRYPOINT_HTTPS:-websecure}"
export TRAEFIK_ENTRYPOINT_HTTP="${TRAEFIK_ENTRYPOINT_HTTP:-web}"
export HSTS_MAX_AGE_SEGUNDOS="${HSTS_MAX_AGE_SEGUNDOS:-86400}"
export LOGIN_RATE_LIMIT_MEDIA="${LOGIN_RATE_LIMIT_MEDIA:-10}"
export LOGIN_RATE_LIMIT_RAJADA="${LOGIN_RATE_LIMIT_RAJADA:-20}"

# SPEC-0027: confere os secrets antes de qualquer build e exporta a versão vigente
# de cada um. `resolver` só emite nomes que casam com o contrato, então o `eval` é seguro.
./deploy/secrets.sh verificar
eval "$(./deploy/secrets.sh resolver)"
export OPENROUTER_API_KEY_SECRET R2_CREDENTIALS_SECRET CONEXOES_CHAVE_SECRET POSTGRES_PASSWORD_SECRET
export BACKUP_CHAVE_SECRET BACKUP_R2_CREDENTIALS_SECRET BACKUP_AVISOS_SECRET

api_proxy_target="${API_PROXY_TARGET:-http://backend_ragpipeline:8000}"
application_node_hostname="${APPLICATION_NODE_HOSTNAME:-$(hostname)}"

docker build \
  -f deploy/backend/Dockerfile \
  -t rag-pipeline-backend:local \
  .

docker build \
  --build-arg "API_PROXY_TARGET=${api_proxy_target}" \
  -f deploy/frontend/Dockerfile \
  -t rag-pipeline-frontend:local \
  frontend/

: "${DATABASE_NODE_HOSTNAME:?Defina DATABASE_NODE_HOSTNAME com o node dedicado a dados}"

export API_PROXY_TARGET="$api_proxy_target"
export APPLICATION_NODE_HOSTNAME="$application_node_hostname"
export DATABASE_NODE_HOSTNAME

# A imagem precisa existir no nó de dados; as imagens locais não são distribuídas
# pelo Swarm. Nunca promover se o build do backup no nó de dados falhar.
if [ "$application_node_hostname" = "$DATABASE_NODE_HOSTNAME" ]; then
  docker build -f deploy/backup/Dockerfile -t rag-pipeline-backup:local deploy/backup
else
  : "${BACKUP_DOCKER_CONTEXT:?Defina BACKUP_DOCKER_CONTEXT para o Docker do nó de dados}"
  backup_node_hostname="$(docker --context "$BACKUP_DOCKER_CONTEXT" info --format '{{.Name}}')"
  [ "$backup_node_hostname" = "$DATABASE_NODE_HOSTNAME" ] || {
    echo 'O contexto do backup não aponta para o nó de dados.' >&2
    exit 1
  }
  docker --context "$BACKUP_DOCKER_CONTEXT" build -f deploy/backup/Dockerfile -t rag-pipeline-backup:local deploy/backup
fi

docker stack deploy \
  --resolve-image never \
  -c deploy/stack.prod.yml \
  rag-pipeline
