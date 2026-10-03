#!/usr/bin/env bash

set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

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

docker stack deploy \
  --resolve-image never \
  -c deploy/stack.prod.yml \
  rag-pipeline
