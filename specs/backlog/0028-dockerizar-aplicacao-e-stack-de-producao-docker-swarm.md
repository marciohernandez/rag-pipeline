# Backlog: Dockerizar a aplicação e criar o stack de produção (Docker Swarm)

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0028 |
| Status | Promoted |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | M03 |
| Criado em | 2026-09-28 |
| Spec promovida | specs/draft/0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm/spec.md (SPEC-0022) |

## Ideia original

Criar Dockerfiles de produção para backend FastAPI, frontend Next.js e worker Procrastinate, e um stack file de Docker Swarm cobrindo todos os serviços (backend, frontend, worker, Postgres de produção, Qdrant de produção), distintos dos recursos de teste já existentes.

## Problema percebido

O sistema hoje só roda localmente (next dev + backend FastAPI local + Postgres de teste via Docker Compose); não existe nenhum Dockerfile de produção nem definição de como os serviços rodam juntos fora do ambiente de desenvolvimento.

## Pessoa afetada ou beneficiada

Marcio, ao colocar o sistema no ar para uso interno da equipe de consultoria (M03 — Deploy em Beta).

## Resultado ou valor esperado

A aplicação inteira sobe em produção com um comando (docker stack deploy) em um VPS via Docker Swarm, com Postgres e Qdrant de produção isolados dos recursos de teste.

## Contexto

Item candidato do marco M03 (Deploy em Beta, Docker Swarm), aberto por decisão de Marcio em 2026-09-28 na entrevista de roadmap pós-M02. Pré-requisito para os demais itens do marco (domínio/TLS, secrets, backup, runbook de deploy).

## Referências relacionadas

- `specs/milestones/M03.md` — marco de origem (Deploy em Beta, Docker Swarm). Tipo: milestone relacionada.
- `specs/backlog/0029-dominio-https-e-reverse-proxy-para-o-beta.md`, `0030-gestao-de-secrets-de-producao-via-docker-swarm.md`, `0031-backup-automatico-do-postgres-de-producao.md`, `0032-runbook-de-deploy-manual-em-producao.md` — itens irmãos do mesmo marco, dependentes deste. Tipo: backlog relacionado.
- `docker-compose.yml` (raiz) — hoje só provisiona o Postgres de teste (`rag-pipeline-test-postgres`); o Postgres de produção precisa ser um serviço/volume distinto. Tipo: superfície técnica afetada.

## Comportamento esperado

- Dockerfile de produção para backend FastAPI, frontend Next.js e worker Procrastinate, buildados diretamente no VPS (sem registry nesta fase).
- Stack file de Docker Swarm cobrindo todos os serviços: backend, frontend, worker, Postgres de produção e Qdrant de produção.
- Postgres e Qdrant de produção como serviços do próprio stack, com dados em volumes Docker nomeados e externos (criados manualmente antes, referenciados como `external: true`), distintos dos recursos de teste (`rag-pipeline-test-postgres`).
- Postgres e Qdrant de produção fixados por `placement.constraints` no mesmo node dedicado a banco de dados já usado por outras aplicações da VPS (ex.: `bancodedados01`); backend, frontend e worker sem constraint de node.
- O stack conecta-se à rede overlay externa `network_swarm_public`, já compartilhada com as demais aplicações da VPS e já servida por um reverse proxy (Traefik ou similar) com HTTPS automático por labels.
- Credenciais de produção (senha do Postgres, chave OpenRouter, credenciais Cloudflare R2, segredo de sessão) são lidas via `docker secrets`, referenciadas pelos serviços que precisam delas — a criação e o conteúdo dos secrets são escopo do BACKLOG-0030, mas o stack file já os referencia.

## Regras de negócio

- Nenhum dado de produção pode ser gravado nos recursos de teste (`rag-pipeline-test-postgres` ou coleção de teste do Qdrant), nem vice-versa — isolamento total entre ambientes.
- Nenhuma credencial de produção pode aparecer em texto puro no stack file nem em log — apenas via `docker secret`.

## Critérios de aceitação

- **Dado** o código atualizado no VPS, **quando** Marcio builda as imagens localmente e roda `docker stack deploy`, **então** backend, frontend, worker, Postgres e Qdrant de produção sobem como serviços do Swarm, todos em estado `Running`.
- **Dado** o stack no ar, **quando** o Postgres ou o Qdrant de produção recebem dados, **então** esses dados persistem em volumes externos nomeados, distintos e isolados dos recursos de teste.
- **Dado** o stack no ar, **quando** backend ou worker precisam de uma credencial (OpenRouter, R2, sessão, senha do banco), **então** ela é lida via `docker secret`, nunca em texto puro no stack file nem em log.
- **Dado** o stack conectado à rede `network_swarm_public`, **quando** o reverse proxy existente (Traefik) é configurado com as labels certas (BACKLOG-0029), **então** o serviço fica acessível por HTTPS sem exigir configuração adicional de rede neste item.

## Qualidades e operação

- Segurança: nenhuma credencial em texto puro versionado; isolamento de rede/volume entre produção e teste.
- Privacidade: dados de produção (Pessoas, Bases, conversas do assistente) ficam apenas nos volumes de produção, nunca nos de teste.
- Desempenho e volume: a avaliar durante a implementação — dimensionamento de CPU/memória de cada serviço, considerando que o node de banco de dados já hospeda outras aplicações.
- Auditoria e observabilidade: fora de escopo deste item (ver `specs/milestones/M03.md`, seção "Fora de escopo" — observabilidade avançada não faz parte do M03).

## Dependências

- Nenhuma bloqueante. Toda a camada de aplicação (backend, frontend, worker) já está implementada e mesclada em `main`.

## Situações de erro

- Se o build de uma imagem falhar no VPS, o `docker stack deploy` deve preservar os serviços anteriores em execução (Swarm não substitui um serviço por uma imagem que falhou o build).
- Se um `docker secret` referenciado não existir, o serviço correspondente falha ao subir de forma visível (não deve subir "silenciosamente" sem a credencial).

## Escopo

- Dentro: Dockerfile de produção para backend, frontend e worker; stack file do Swarm com todos os serviços; Postgres e Qdrant de produção com volumes externos nomeados; placement constraint no node de banco de dados; conexão com a rede `network_swarm_public` existente; leitura de credenciais via `docker secrets` no stack file.
- Fora: domínio, TLS e labels do Traefik (`BACKLOG-0029`); criação dos secrets e seu conteúdo (`BACKLOG-0030`); backup do Postgres de produção (`BACKLOG-0031`); runbook de deploy (`BACKLOG-0032`); registry de imagens; CI/CD automatizado; múltiplos nós para alta disponibilidade da aplicação em si.

## Dúvidas, decisões e riscos

- **Decisão** (entrevista de roadmap, 2026-09-28): hospedagem via Docker Swarm, não PaaS gerenciado nem serviços cloud separados.
- **Decisão**: já existe um VPS disponível para isso, com Docker Swarm já instalado e outras aplicações já em produção nele; provisionar servidor novo não faz parte deste item.
- **Decisão**: Postgres e Qdrant de produção rodam como serviços do próprio Swarm (containers), não como serviços gerenciados externos.
- **Decisão** (aprofundamento, 2026-09-28): build das imagens direto no VPS, sem registry nesta fase.
- **Decisão**: o Swarm é multi-node; Postgres e Qdrant deste projeto são fixados no node dedicado a banco de dados (mesmo padrão já usado por outras aplicações, ex.: `bancodedados01`); os demais serviços não têm constraint de node.
- **Decisão**: credenciais de produção via `docker secrets`, não como variável de ambiente em texto puro no stack file (diferente do padrão mais simples usado em outras stacks da VPS, escolhido aqui por lidar com chave de LLM e storage).
- **Decisão**: volumes de dados como volumes Docker nomeados e externos, criados manualmente antes do deploy — mesmo padrão do exemplo de stack já usado na VPS (`postgres_data: external: true`).
- **Decisão**: a rede `network_swarm_public` já existe e já tem reverse proxy (Traefik) com HTTPS automático por labels — este item só conecta a ela, sem criar proxy próprio.
- **Aberto**: nome exato do node de banco de dados a usar e limites de CPU/memória de cada serviço — não bloqueiam a especificação, ficam para a implementação.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Pronto para `$specsfy-03-specify`.
