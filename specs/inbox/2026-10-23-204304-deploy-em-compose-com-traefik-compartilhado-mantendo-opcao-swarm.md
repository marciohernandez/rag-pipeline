# Inbox: Deploy em Compose com Traefik compartilhado, mantendo opção Swarm

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-23T20:43:04Z |
| Slug | deploy-em-compose-com-traefik-compartilhado-mantendo-opcao-swarm |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `b29d0496d78370ecff2b57a1c1f0ec248be577a6b5c059f098032ac6de2cd143` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Pedido inicial: "analise a instrução de como fazer o deploy na vpos. essa instrução devi de outro projeto." (instrução colada do projeto "factory", resumida abaixo sem perda de regra)

Padrão colado: publicar na VPS onde já roda o projeto factory. Traefik já existe (outro stack); rede externa compartilhada n8n-dev-stack_traefik_net (external: true, nunca criar/remover); certresolver mytlschallenge, entrypoint websecure; usuário SSH deploy (nunca root); Docker Compose v2 e Git no servidor; VPS ARM ou x86_64, build no servidor. Dois arquivos: compose.yml (base: sem labels de proxy, sem portas no host, restart unless-stopped, mem_limit/cpus, healthcheck em todo serviço; app com read_only, cap_drop ALL, no-new-privileges, init: true, usuário não-root) e compose.homolog.yml (conecta web à rede externa e define labels Traefik; nomes de router/service únicos prefixados pelo projeto; API e front no mesmo domínio separados por PathPrefix(/api) com priority maior na API). Comando sempre com projeto Compose estável: docker compose -p <proj> -f compose.yml -f compose.homolog.yml. Segredos: .env só no servidor, permissão 600, criado pela pessoa, nunca no Git, .env.example só com nomes, variáveis obrigatórias com ${VAR:?mensagem}. Banco em container próprio com volume nomeado <proj>_postgres_data, sem porta publicada; nunca down -v, migrate:fresh, DROP, TRUNCATE. scripts/deploy.sh (chamado por make deploy): lê config shell fora do repo (DEPLOY_CONFIG, perm 600) com DEPLOY_HOST, DEPLOY_USER=deploy, DEPLOY_KEY, DEPLOY_PATH, DEPLOY_PORT, DEPLOY_REPOSITORY; publica exatamente o commit HEAD (já no remoto); via SSH (BatchMode=yes, StrictHostKeyChecking=yes, sem agent forwarding): valida pré-requisitos, git fetch + checkout --detach, árvore limpa, compose config -q; build (falha aborta e mantém os serviços); up -d --no-build --wait; sem down, sem remover volumes; repositório privado com deploy key somente leitura. Backup: scripts/backup.sh faz pg_dump | gzip via docker compose exec -T db para pasta do host (BACKUP_DIR), valida com gzip -t, retém 7, agenda no cron e documenta restauração. Pedido ao assistente: ler o projeto e descrever serviços, portas, bancos/volumes, variáveis e diferenças; propor compose.yml + compose.homolog.yml, deploy.sh, backup.sh, Makefile e .env.example; listar o que a pessoa faz na VPS antes do primeiro deploy; confirmar host, usuário, pasta, domínio e nome do projeto Compose antes de qualquer ação na VPS; validar depois do deploy (containers healthy, curl -I https://<dominio>, certificado, logs); parar e perguntar se algo exigir mexer no Traefik, na rede compartilhada ou em outro projeto.

Esclarecimento da pessoa: "a idei é ter a opção de swarm quando precisar...na vps que vamos fazer o deploy não tem swarm....penso que quando o projeto crescer e precisar seja facil fazer o swarm para aumentar, mas não é necessario no inicio. entendeu?"

Respostas da pessoa: "1 - vamos usar um postgree em um container, sai do supabase / 2 - sim [Qdrant publicado continua] / 3 - mantem [backup atual] / 4 - sim é esse [rede n8n-dev-stack_traefik_net e certresolver mytlschallenge] / 5 - ok [host, usuário, pasta, domínio e nome do projeto Compose ainda não informados]"

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Publicar o projeto na VPS sem Swarm usando Compose + Traefik no padrão do factory, com Postgres em container, preservando os arquivos de Swarm como caminho de crescimento.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** O deploy atual é Swarm (stack.prod.yml, Postgres Supabase externo), mas a VPS de destino só tem Compose.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Marcio (responsável pelo deploy); equipe de consultoria que usa o Beta.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Primeiro deploy viável na VPS de destino, com migração futura para Swarm sem reescrita.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: Compose agora, Swarm depois; Postgres em container (sai do Supabase); Qdrant publicado com prefixo beta-; backup atual mantido; rede n8n-dev-stack_traefik_net e certresolver mytlschallenge; padrão compose.yml + compose.homolog.yml, deploy.sh via SSH, backup.sh, Makefile, .env.example. Inferência: os mesmos Dockerfiles servem aos dois modos; secrets podem ser arquivos montados em /run/secrets para o comando do backend ficar igual.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Postgres passa a ser container com volume nomeado próprio, sem porta publicada; dados hoje no Supabase precisarão de migração/backup e restauração; backup cifrado ao R2 continua.

### Riscos e dependências

**Análise preliminar:** Troca de Supabase para Postgres em container exige migrar dados e adaptar o serviço de backup; Traefik e rede são de outro stack (não mexer); segredos como arquivos no servidor; hardening read_only pode conflitar com LibreOffice gravando em /app/.config; superposição com SPEC-0041 e T020.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Uma spec de deploy em Compose (compose.yml, compose.homolog.yml, scripts/deploy.sh, backup, Makefile, .env.example, runbook) preservando stack.prod.yml; possível spec separada para migrar dados do Supabase.

## Pontos a revisar no futuro

**A revisar:** Host, usuário, pasta, domínio e nome do projeto Compose não informados; destino do backup com Postgres em container; como migrar dados do Supabase; segredos em arquivo vs .env; healthchecks e limites de memória por serviço; confirmar que a VPS de destino é a mesma do desenvolvimento ou outra.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
