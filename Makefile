# Deploy em Compose (SPEC-0045). Nada aqui apaga volume, banco ou schema.
#
#   make deploy         publica o commit HEAD (já no remoto) na VPS
#   make deploy-config  valida os arquivos Compose localmente (exporta as variáveis antes)
#   make deploy-logs    mostra os logs recentes dos serviços na VPS
#
# DEPLOY_CONFIG aponta para o arquivo de configuração do servidor, fora do repositório.

COMPOSE := docker compose -p ragpipeline -f deploy/compose/compose.yml -f deploy/compose/compose.homolog.yml

.PHONY: deploy deploy-config deploy-logs

deploy:
	bash deploy/compose/deploy.sh

deploy-config:
	$(COMPOSE) config -q

deploy-logs:
	@test -n "$$DEPLOY_CONFIG" || { echo "Defina DEPLOY_CONFIG." >&2; exit 1; }
	@. "$$DEPLOY_CONFIG" && ssh -i "$$DEPLOY_KEY" -o BatchMode=yes -o StrictHostKeyChecking=yes \
		-o ForwardAgent=no $${DEPLOY_PORT:+-p $$DEPLOY_PORT} "$$DEPLOY_USER@$$DEPLOY_HOST" \
		"cd $$DEPLOY_PATH && $(COMPOSE) --env-file .env logs --tail=100"
