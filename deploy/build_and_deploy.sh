#!/usr/bin/env bash

set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

# SPEC-0035: `--versao <etiqueta>` reimplanta uma versão já guardada, sem construir.
versao_pedida=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --versao)
      versao_pedida="${2:?Informe a etiqueta depois de --versao}"
      shift 2
      ;;
    *)
      echo "Uso: deploy/build_and_deploy.sh [--versao <etiqueta>]" >&2
      exit 2
      ;;
  esac
done
etiqueta_valida='^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$'
if [ -n "$versao_pedida" ] && [[ ! "$versao_pedida" =~ $etiqueta_valida ]]; then
  echo "Etiqueta de versão inválida." >&2
  exit 2
fi

# Exigir o domínio antes de consultar o Swarm ou construir imagens.
: "${DOMINIO_RAGPIPELINE:?Defina DOMINIO_RAGPIPELINE com export antes de executar deploy/build_and_deploy.sh}"
export DOMINIO_RAGPIPELINE
# SPEC-0041: Postgres e Qdrant são externos; sem host, usuário e URL não há deploy.
ausentes=()
for variavel in DATABASE_HOST DATABASE_USER QDRANT_URL; do
  [ -n "${!variavel:-}" ] || ausentes+=("$variavel")
done
if [ "${#ausentes[@]}" -gt 0 ]; then
  echo "Defina com export antes do deploy: ${ausentes[*]} (ver deploy/SECRETS.md)." >&2
  exit 1
fi
export DATABASE_HOST DATABASE_USER QDRANT_URL
export DATABASE_PORT="${DATABASE_PORT:-5432}" DATABASE_NAME="${DATABASE_NAME:-postgres}"
export DATABASE_SSLMODE="${DATABASE_SSLMODE:-require}" APP_COLECAO_PREFIXO="${APP_COLECAO_PREFIXO:-}"
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
export QDRANT_API_KEY_SECRET
export BACKUP_CHAVE_SECRET BACKUP_R2_CREDENTIALS_SECRET BACKUP_AVISOS_SECRET

repositorios=(rag-pipeline-backend rag-pipeline-frontend rag-pipeline-backup)
copias_guardadas=3

# SPEC-0035: a etiqueta é o commit curto; só vale se identificar o código implantado.
if [ -n "$versao_pedida" ]; then
  VERSAO_IMAGEM="$versao_pedida"
else
  if [ -n "$(git status --porcelain)" ]; then
    echo "Há alterações não commitadas: a versão não identificaria o código. Faça o commit antes do deploy." >&2
    exit 1
  fi
  VERSAO_IMAGEM="$(git rev-parse --short HEAD)"
  if [[ ! "$VERSAO_IMAGEM" =~ $etiqueta_valida ]]; then
    echo "Não foi possível identificar a versão pelo commit atual." >&2
    exit 1
  fi
fi
export VERSAO_IMAGEM
echo "Versão das imagens: $VERSAO_IMAGEM"

# A versão em uso antes deste deploy é a de retorno e nunca é podada.
versao_de_retorno=""
imagem_em_uso="$(docker service inspect \
  --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' \
  rag-pipeline_backend_ragpipeline 2>/dev/null || true)"
if [ -n "$imagem_em_uso" ]; then
  versao_de_retorno="${imagem_em_uso#*:}"
  versao_de_retorno="${versao_de_retorno%%@*}"
fi

api_proxy_target="${API_PROXY_TARGET:-http://backend_ragpipeline:8000}"
application_node_hostname="${APPLICATION_NODE_HOSTNAME:-$(hostname)}"

if [ -z "$versao_pedida" ]; then
  docker build \
    -f deploy/backend/Dockerfile \
    -t "rag-pipeline-backend:${VERSAO_IMAGEM}" \
    .

  docker build \
    --build-arg "API_PROXY_TARGET=${api_proxy_target}" \
    -f deploy/frontend/Dockerfile \
    -t "rag-pipeline-frontend:${VERSAO_IMAGEM}" \
    frontend/
fi

: "${DATABASE_NODE_HOSTNAME:?Defina DATABASE_NODE_HOSTNAME com o node dedicado a dados}"

# A imagem precisa existir no nó de dados; as imagens locais não são distribuídas
# pelo Swarm. Nunca promover se o build do backup no nó de dados falhar.
docker_dados=(docker)
if [ "$application_node_hostname" != "$DATABASE_NODE_HOSTNAME" ]; then
  : "${BACKUP_DOCKER_CONTEXT:?Defina BACKUP_DOCKER_CONTEXT para o Docker do nó de dados}"
  backup_node_hostname="$(docker --context "$BACKUP_DOCKER_CONTEXT" info --format '{{.Name}}')"
  [ "$backup_node_hostname" = "$DATABASE_NODE_HOSTNAME" ] || {
    echo 'O contexto do backup não aponta para o nó de dados.' >&2
    exit 1
  }
  docker_dados=(docker --context "$BACKUP_DOCKER_CONTEXT")
fi

if [ -z "$versao_pedida" ]; then
  "${docker_dados[@]}" build -f deploy/backup/Dockerfile \
    -t "rag-pipeline-backup:${VERSAO_IMAGEM}" deploy/backup
else
  # Voltar atrás: a etiqueta precisa existir nas três imagens antes de implantar.
  faltando=0
  for repositorio in "${repositorios[@]}"; do
    docker_do_repositorio=(docker)
    [ "$repositorio" = rag-pipeline-backup ] && docker_do_repositorio=("${docker_dados[@]}")
    "${docker_do_repositorio[@]}" image inspect "${repositorio}:${VERSAO_IMAGEM}" >/dev/null 2>&1 || faltando=1
  done
  if [ "$faltando" = 1 ]; then
    disponiveis="$(
      for repositorio in "${repositorios[@]}"; do
        docker_do_repositorio=(docker)
        [ "$repositorio" = rag-pipeline-backup ] && docker_do_repositorio=("${docker_dados[@]}")
        "${docker_do_repositorio[@]}" image ls "$repositorio" --format '{{.Tag}}' 2>/dev/null |
          awk -v r="$repositorio" '$0 != "local" && $0 != "<none>" { print $0 }'
      done | sort | uniq -c | awk -v n="${#repositorios[@]}" '$1 == n { print $2 }' | tr '\n' ' '
    )"
    echo "A versão ${VERSAO_IMAGEM} não existe nas três imagens." >&2
    echo "Versões disponíveis: ${disponiveis:-nenhuma}" >&2
    exit 1
  fi
fi

export API_PROXY_TARGET="$api_proxy_target"
export APPLICATION_NODE_HOSTNAME="$application_node_hostname"
export DATABASE_NODE_HOSTNAME

docker stack deploy \
  --resolve-image never \
  -c deploy/stack.prod.yml \
  rag-pipeline

# SPEC-0035: poda só depois de um deploy bem-sucedido (o `set -e` já parou antes).
# Fica o mais recente (`copias_guardadas`), a versão implantada e a de retorno.
# Só `docker image rm` das etiquetas antigas das três imagens do projeto.
for repositorio in "${repositorios[@]}"; do
  docker_do_repositorio=(docker)
  [ "$repositorio" = rag-pipeline-backup ] && docker_do_repositorio=("${docker_dados[@]}")
  mantidas=0
  while IFS= read -r etiqueta; do
    [ -n "$etiqueta" ] || continue
    mantidas=$((mantidas + 1))
    if [ "$mantidas" -le "$copias_guardadas" ] ||
       [ "$etiqueta" = "$VERSAO_IMAGEM" ] || [ "$etiqueta" = "$versao_de_retorno" ]; then
      continue
    fi
    "${docker_do_repositorio[@]}" image rm "${repositorio}:${etiqueta}" >/dev/null ||
      echo "Aviso: não foi possível remover ${repositorio}:${etiqueta}." >&2
  done < <("${docker_do_repositorio[@]}" image ls "$repositorio" --format '{{.Tag}}')
done
