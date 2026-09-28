# Backlog: Dockerizar a aplicação e criar o stack de produção (Docker Swarm)

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0028 |
| Status | Captured |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | M03 |
| Criado em | 2026-09-28 |
| Spec promovida | Nenhuma |

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

A esclarecer.

## Regras de negócio

- A esclarecer conforme risco e complexidade.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: a avaliar.
- Privacidade: a avaliar.
- Desempenho e volume: a avaliar.
- Auditoria e observabilidade: a avaliar.

## Dependências

- Nenhuma registrada.

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: a esclarecer.
- Fora: a esclarecer.

## Dúvidas, decisões e riscos

- **Decisão** (entrevista de roadmap, 2026-09-28): hospedagem via Docker Swarm, não PaaS gerenciado nem serviços cloud separados.
- **Decisão**: já existe um VPS disponível para isso; provisionar servidor novo não faz parte deste item.
- **Decisão**: Postgres e Qdrant de produção rodam como serviços do próprio Swarm (containers), não como serviços gerenciados externos.
- **Aberto**: dimensionamento de recursos do VPS existente (CPU/memória) para os serviços de produção — a confirmar durante a especificação.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
