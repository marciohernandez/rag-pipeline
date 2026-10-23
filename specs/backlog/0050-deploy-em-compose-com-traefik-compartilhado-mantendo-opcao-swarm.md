# Backlog: Deploy em Compose com Traefik compartilhado, mantendo opção Swarm

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0050 |
| Status | Promoted |
| Produto | RAG Pipeline |
| Épico | Entrega e operação do Beta |
| Funcionalidade | Deploy em Compose |
| Tipo | técnico |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-23 |
| Spec promovida | specs/draft/0045-deploy-em-compose-com-traefik/spec.md |

## Ideia original

Publicar o projeto na VPS de destino, que não tem Swarm, usando Compose + Traefik no padrão do projeto factory; o Swarm continua como opção para quando o projeto crescer, sem ser necessário no início. Postgres passa a container (sai do Supabase, que só tem dados de teste); Qdrant publicado continua; backup atual é mantido. Texto integral em specs/inbox/2026-10-23-204304-deploy-em-compose-com-traefik-compartilhado-mantendo-opcao-swarm.md

## Problema percebido

O deploy atual (stack.prod.yml) exige Docker Swarm e Postgres externo (SPEC-0041), mas a VPS de destino só tem Docker Compose.

## Pessoa afetada ou beneficiada

Marcio, responsável por operar o deploy do Beta.

## Resultado ou valor esperado

Primeiro deploy do Beta na VPS com Compose, HTTPS pelo Traefik compartilhado, com caminho de crescimento para Swarm sem reescrever imagens.

## Contexto

Traefik e a rede n8n-dev-stack_traefik_net pertencem a outro stack e não podem ser alterados; certresolver mytlschallenge; usuário SSH deploy; build no servidor; Postgres em container com volume próprio; Qdrant publicado com prefixo beta-. Relacionado a SPEC-0041 (in-progress), SPEC-0032 (in-progress), SPEC-0027, SPEC-0034 e SPEC-0035.

## Referências relacionadas

- specs/inbox/2026-10-23-204304-deploy-em-compose-com-traefik-compartilhado-mantendo-opcao-swarm.md — origem (Inbox)
- specs/in-progress/0041-servicos-externos-qdrant-postgres-producao/spec.md — spec relacionada: Postgres externo no Swarm; a parte do Postgres é substituída no caminho Compose
- specs/in-progress/0032-dominio-https-e-reverse-proxy-para-o-beta/spec.md — spec relacionada: domínio, HTTPS e proxy
- specs/completed/0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm/spec.md — spec relacionada: imagens reaproveitadas
- specs/completed/0027-provisionamento-de-secrets-do-swarm/spec.md — spec relacionada: contrato dos secrets
- specs/completed/0034-backup-automatico-do-postgres-de-producao/spec.md — spec relacionada: serviço de backup mantido
- specs/completed/0035-runbook-de-deploy-manual-em-producao/spec.md — spec relacionada: runbook do Swarm, preservado

## Comportamento esperado

`make deploy` publica o commit `HEAD` na VPS por SSH (usuário `deploy`, `BatchMode`, host conhecido). No servidor: valida pré-requisitos, faz checkout do commit, exige árvore limpa, valida o Compose, constrói as imagens, faz backup e aplica as migrations (`alembic upgrade head` em container descartável) e só então sobe os serviços com `up -d --no-build --wait`. Frontend, backend, worker, Postgres em container e backup rodam em Compose; só o frontend é exposto pelo Traefik compartilhado, com HTTPS, e `/api/*` passa pelo proxy do Next. Os arquivos de Swarm continuam no repositório.

## Regras de negócio

- Nunca criar, alterar ou remover o Traefik, a rede `n8n-dev-stack_traefik_net` nem outro projeto da VPS; parar e perguntar se algo exigir isso.
- Nunca `down -v`, `migrate:fresh`, `DROP`, `TRUNCATE` ou qualquer comando que apague volume ou banco.
- Nomes de router, service e middleware do Traefik prefixados por `ragpipeline-`; projeto Compose próprio e estável.
- Segredos em arquivos de permissão 600 no servidor, fora do Git; variáveis obrigatórias falham cedo com `${VAR:?mensagem}`.
- Postgres sem porta publicada, volume nomeado próprio.

## Critérios de aceitação

- Dado o commit HEAD no remoto, quando o deploy roda, então as imagens são construídas no servidor, as migrations aplicadas e os serviços ficam `healthy`.
- Dado um build com erro, quando o deploy roda, então aborta e os serviços atuais continuam no ar.
- Dado o domínio apontando para a VPS, quando se faz `curl -I https://<domínio>`, então responde por HTTPS com certificado emitido e redirecionamento de HTTP.
- Dado o backend sob `read_only`, quando um DOC/PPT/XLS ou imagem é enviado, então a conversão e o OCR funcionam.
- Dado um deploy novo sobre dados existentes, então o volume do Postgres é preservado.
- Dado o `docker-compose` do Swarm, então `stack.prod.yml` e seus scripts seguem intactos e usam as mesmas imagens.

## Qualidades e operação

- Segurança: hardening completo dos containers; segredos em arquivo 600; SSH sem agent forwarding e com host verificado.
- Privacidade: a avaliar.
- Desempenho e volume: `mem_limit` e `cpus` por serviço, a calibrar; healthcheck em cada serviço.
- Auditoria e observabilidade: a avaliar.

## Dependências

- Traefik compartilhado e rede externa já existentes na VPS de destino; DNS do domínio apontando para a VPS; acesso de leitura do servidor ao Git; Qdrant publicado e R2 disponíveis.

## Situações de erro

- Build falha: aborta sem tocar nos serviços atuais.
- Migration falha: não sobe a nova versão; a restauração segue `deploy/BACKUP.md`.
- `--wait` expira: reporta serviço não saudável e logs.

## Escopo

- Dentro: `compose.yml`, `compose.homolog.yml`, `scripts/deploy.sh`, entradas no `Makefile`, `.env.example`, Postgres em container, migração via container descartável, backup apontando para o `db`, runbook de primeira instalação e verificação pós-deploy.
- Fora: executar o deploy na VPS (só com autorização), mexer em Traefik ou rede, mudar a lógica do backup, migrar dados do Supabase, qualquer mudança funcional da aplicação.

## Dúvidas, decisões e riscos

- Decisão (2026-10-23, pessoa): Postgres em container, sai do Supabase; os dados do Supabase são só de teste e não precisam ser migrados.
- Decisão: Qdrant publicado continua, com prefixo `beta-`; backup atual é mantido; rede `n8n-dev-stack_traefik_net` e certresolver `mytlschallenge` confirmados.
- Decisão: o Swarm é opção futura, não necessário no início; os arquivos de Swarm são preservados.
- Pergunta 1 — segredos no servidor. Resposta: "1" → arquivos em pasta fora do Git, permissão 600, montados como secrets do Compose em /run/secrets/*, mantendo o comando do backend e do worker idêntico ao do Swarm.
- Pergunta 2 — migrations. Resposta: "1" → passo no `deploy.sh`, depois do backup e antes do `up`, rodando `alembic upgrade head` num container descartável; a subida dos serviços não migra sozinha (mantém a regra do runbook atual).
- Pergunta 3 — hardening. Resposta: "1" → padrão completo (`read_only`, `cap_drop: [ALL]`, `no-new-privileges`, `init: true`) com `tmpfs` em `/tmp`, `/app/.config` e `/app/.cache`; exige teste real do LibreOffice/OCR sob `read_only`.
- Pergunta 4 — uploads. Resposta: "1" → Cloudflare R2 com as credenciais no secret `r2_credentials`, sem volume de uploads, como no Swarm.
- Pergunta 5 — backup. Resposta: "1" → manter o serviço `backup_ragpipeline` (cifrado, enviado ao R2, retenção e aviso), apontando para o container `db` na rede interna do Compose com `sslmode=disable`; o `scripts/backup.sh` simples do padrão do factory não é criado.
- Pergunta 6 — SPEC-0041 e SPEC-0032. Resposta: "1" → ficam como estão; o Compose é caminho paralelo, a SPEC-0041 continua valendo para o Swarm, e as tarefas de deploy real (T020 e T027) passam a ser cumpridas e fechadas pelo deploy em Compose.
- Aberto: host, usuário, pasta, domínio e nome do projeto Compose (necessários só no deploy real).

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
