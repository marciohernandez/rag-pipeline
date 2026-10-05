# Backlog: Gestão de secrets de produção via Docker Swarm

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0030 |
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

Gerir as credenciais de produção (OpenRouter, Cloudflare R2, senha do Postgres, segredo de sessão, etc.) por docker secrets do Swarm, em vez de arquivo .env em texto puro no servidor.

## Problema percebido

Hoje as credenciais ficam em arquivos .env locais, adequado para desenvolvimento mas não para um servidor de produção compartilhado pela equipe.

## Pessoa afetada ou beneficiada

Marcio, ao operar e atualizar o ambiente de produção durante o Beta.

## Resultado ou valor esperado

Nenhuma credencial de produção fica em texto puro no stack file nem versionada; segredos são injetados nos serviços via docker secrets.

## Contexto

Item candidato do marco M03 (Deploy em Beta, Docker Swarm), decorrente da escolha de hospedagem (Docker Swarm) feita por Marcio em 2026-09-28. Depende do stack de produção (item de dockerização) já estar definido.

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

- `specs/backlog/0028-dockerizar-aplicacao-e-stack-de-producao-docker-swarm.md` — bloqueante. Os secrets são injetados nos serviços definidos pelo stack de produção.

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
