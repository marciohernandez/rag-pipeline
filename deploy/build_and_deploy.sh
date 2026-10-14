#!/usr/bin/env bash

set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

# SPEC-0032: o domínio público é obrigatório; recusa antes de qualquer build ou deploy.
: "${DOMINIO_RAGPIPELINE:?Defina DOMINIO_RAGPIPELINE com o domínio público do frontend}"

# SPEC-0027: confere os secrets antes de qualquer build e exporta a versão vigente
# de cada um. `resolver` só emite nomes que casam com o contrato, então o `eval` é seguro.
./deploy/secrets.sh verificar
eval "$(./deploy/secrets.sh resolver)"
export OPENROUTER_API_KEY_SECRET R2_CREDENTIALS_SECRET CONEXOES_CHAVE_SECRET POSTGRES_PASSWORD_SECRET

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
export DOMINIO_RAGPIPELINE
# Opcionais: só exportadas quando definidas; o stack tem o padrão em `${VAR:-padrão}`.
export TRAEFIK_CERT_RESOLVER="${TRAEFIK_CERT_RESOLVER:-letsencryptresolver}"
export TRAEFIK_ENTRYPOINT_HTTPS="${TRAEFIK_ENTRYPOINT_HTTPS:-websecure}"
export TRAEFIK_ENTRYPOINT_HTTP="${TRAEFIK_ENTRYPOINT_HTTP:-web}"
export HSTS_MAX_AGE_SEGUNDOS="${HSTS_MAX_AGE_SEGUNDOS:-86400}"
export LOGIN_RATE_LIMIT_MEDIA="${LOGIN_RATE_LIMIT_MEDIA:-10}"
export LOGIN_RATE_LIMIT_RAJADA="${LOGIN_RATE_LIMIT_RAJADA:-20}"

docker stack deploy \
  --resolve-image never \
  -c deploy/stack.prod.yml \
  rag-pipeline
