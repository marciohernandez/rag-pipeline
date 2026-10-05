# Backlog: Runbook de deploy manual em produção

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0032 |
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

Documentar o processo de deploy manual do sistema em produção (docker stack deploy), incluindo pré-requisitos, ordem dos passos e como verificar que o deploy funcionou.

## Problema percebido

O deploy será manual nesta fase (decisão confirmada), mas não existe hoje nenhum processo documentado de como atualizar o sistema em produção sem quebrar o Beta.

## Pessoa afetada ou beneficiada

Marcio, ao atualizar o sistema em produção sempre que uma nova versão precisar ir ao ar.

## Resultado ou valor esperado

Existe um passo a passo documentado e repetível para atualizar o ambiente de produção via Docker Swarm, reduzindo o risco de erro humano no deploy.

## Contexto

Item candidato do marco M03 (Deploy em Beta, Docker Swarm), decorrente da decisão de Marcio em 2026-09-28 de manter o deploy manual (sem CI/CD automatizado) nesta entrega. Depende dos demais itens do marco (stack de produção, domínio/TLS, secrets) já estarem definidos.

## Referências relacionadas

- Nenhuma referência relevante encontrada.

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

- `specs/backlog/0028-dockerizar-aplicacao-e-stack-de-producao-docker-swarm.md`, `0029-dominio-https-e-reverse-proxy-para-o-beta.md`, `0030-gestao-de-secrets-de-producao-via-docker-swarm.md` — bloqueantes. O runbook documenta o processo depois que stack, domínio/TLS e secrets já existirem.

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: a esclarecer.
- Fora: a esclarecer.

## Dúvidas, decisões e riscos

- Nenhum registrado.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
