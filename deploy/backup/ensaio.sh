#!/usr/bin/env bash
# Ensaio autocontido: apenas Docker local, dados e credenciais fictícios.
set +x
set -Eeuo pipefail
umask 077
cd "$(dirname -- "${BASH_SOURCE[0]}")/../.."

# Recusar contextos remotos: este comando nunca deve operar uma VPS.
if [ -n "${DOCKER_CONTEXT:-}" ]; then
  endpoint=$(docker context inspect "$DOCKER_CONTEXT" --format '{{.Endpoints.docker.Host}}')
else
  endpoint=${DOCKER_HOST:-$(docker context inspect --format '{{.Endpoints.docker.Host}}')}
fi
[[ "$endpoint" == unix://* ]] || { echo 'O ensaio exige um Docker local (unix://).' >&2; exit 1; }
# Fixar o endpoint conferido mesmo quando há DOCKER_CONTEXT no ambiente.
docker() { command docker --host "$endpoint" "$@"; }
tmp=$(mktemp -d)
nome="rag-backup-ensaio-$(date +%s)-$$"
rede="$nome-rede"
pg="$nome-pg"; s3="$nome-s3"; avisos="$nome-avisos"; job="$nome-job"
limpar() {
  local codigo=$?
  trap - EXIT
  docker rm -fv "$job" "$pg" "$s3" "$avisos" >/dev/null 2>&1 || true
  docker network rm "$rede" >/dev/null 2>&1 || true
  rm -rf -- "$tmp"
  exit "$codigo"
}
trap limpar EXIT
trap 'exit 130' INT TERM

docker build -f deploy/backup/Dockerfile -t rag-pipeline-backup:local deploy/backup
docker network create --internal "$rede" >/dev/null
mkdir "$tmp/secrets"
printf '%s\n' 'senha-ficticia-do-ensaio' > "$tmp/secrets/postgres_password"
printf '%s\n' 'chave-ficticia-do-ensaio' > "$tmp/secrets/backup_chave"
cat > "$tmp/secrets/backup_r2_credentials" <<'EOF'
AWS_ACCESS_KEY_ID=ensaio-local
AWS_SECRET_ACCESS_KEY=segredo-ficticio-do-ensaio
R2_ENDPOINT=http://s3:9000
BACKUP_BUCKET=rag-backup-local
EOF
cat > "$tmp/secrets/backup_avisos" <<'EOF'
SMTP_URL=smtp://avisos:1025
SMTP_USER=ensaio
SMTP_PASSWORD=senha-ficticia
SMTP_FROM=backup@ensaio.invalid
SMTP_TO=operador@ensaio.invalid
WEBHOOK_URL=http://avisos:8080
EOF
# Somente valores fictícios; leitura pelo mesmo usuário sem root da imagem.
chmod 755 "$tmp" "$tmp/secrets"
chmod 444 "$tmp/secrets/"*
montagem=(--mount "type=bind,src=$tmp/secrets,dst=/run/secrets,readonly")
docker run -d --name "$pg" --network "$rede" --network-alias postgres \
  "${montagem[@]}" -e POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password \
  -e POSTGRES_USER=rag_pipeline -e POSTGRES_DB=rag_pipeline \
  postgres:16.10-alpine3.22 >/dev/null
docker run -d --name "$s3" --network "$rede" --network-alias s3 \
  -e MOTO_PORT=9000 motoserver/moto:5.1.15 >/dev/null
docker run -d --name "$avisos" --network "$rede" --network-alias avisos \
  --entrypoint python3 rag-pipeline-backup:local /backup/coletor_local.py >/dev/null

rodar() {
  docker run --rm --name "$job" --network "$rede" "${montagem[@]}" \
    -e PGHOST=postgres -e BACKUP_SMTP_TLS=0 -e BACKUP_ESPERA_SEGUNDOS=0 \
    --entrypoint bash rag-pipeline-backup:local "$@"
}
pronto=0
for ((n=0; n<60; n++)); do
  if docker exec "$pg" pg_isready -U rag_pipeline >/dev/null 2>&1 && \
    rodar -c 'source /backup/comum.sh; configurar_s3 /run/secrets/backup_r2_credentials; s3 s3 mb s3://rag-backup-local' >/dev/null 2>&1; then
    pronto=1; break
  fi
  sleep 1
done
[ "$pronto" = 1 ] || { echo 'Postgres ou S3 local não ficou pronto.' >&2; exit 1; }
docker exec -i "$pg" psql -U rag_pipeline -d rag_pipeline -v ON_ERROR_STOP=1 <<'SQL'
CREATE TABLE prova_backup (id integer PRIMARY KEY, conteudo text NOT NULL);
INSERT INTO prova_backup VALUES (1, 'registro conhecido do ensaio');
SQL

rodar /backup/backup.sh | tee "$tmp/ciclo.log"
grep -q 'RESUMO resultado=sucesso' "$tmp/ciclo.log"
# Segunda execução prova que o objeto diário é substituído sem duplicar.
rodar /backup/backup.sh > "$tmp/repeticao.log"
rodar -c 'source /backup/comum.sh; configurar_s3 /run/secrets/backup_r2_credentials; s3 s3 ls s3://rag-backup-local/diarios/' > "$tmp/objetos"
[ "$(wc -l < "$tmp/objetos")" -eq 1 ]
objeto="diarios/$(date -u +%F).dump.enc"
rodar /backup/restaurar.sh "$objeto" --destino postgres:5432 \
  --chave-arquivo /run/secrets/backup_chave \
  --credenciais-arquivo /run/secrets/backup_r2_credentials --banco restauracao_ensaio
registro=$(docker exec "$pg" psql -U rag_pipeline -d restauracao_ensaio -At \
  -c 'SELECT conteudo FROM prova_backup WHERE id=1')
[ "$registro" = 'registro conhecido do ensaio' ]
docker exec "$pg" psql -U rag_pipeline -d restauracao_ensaio -c '\dt'

# O banco inexistente força falha no dump sem alterar o servidor nem o bucket.
if rodar -c 'export PGDATABASE=banco_inexistente_do_ensaio; bash /backup/backup.sh' > "$tmp/falha.log"; then
  echo 'A falha injetada deveria retornar código não zero.' >&2; exit 1
fi
grep -q 'RESUMO resultado=falha' "$tmp/falha.log"
docker logs "$avisos" > "$tmp/avisos.log" 2>&1
grep -q 'AVISO smtp recebido' "$tmp/avisos.log"
grep -q 'AVISO webhook recebido' "$tmp/avisos.log"
rodar -c 'source /backup/comum.sh; configurar_s3 /run/secrets/backup_r2_credentials; s3 s3 ls s3://rag-backup-local/diarios/' > "$tmp/depois"
cmp "$tmp/objetos" "$tmp/depois"
for valor in senha-ficticia-do-ensaio chave-ficticia-do-ensaio segredo-ficticio-do-ensaio; do
  if grep -Fq "$valor" "$tmp/"*.log; then echo 'Segredo fictício apareceu no log.' >&2; exit 1; fi
done
docker image inspect rag-pipeline-backup:local --format 'Imagem: {{.Size}} bytes; usuário: {{.Config.User}}'
echo 'ENSAIO APROVADO: ciclo cifrado, verificação, idempotência, restauração e avisos SMTP/webhook.'
