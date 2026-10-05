# Backlog: Backup automático do Postgres de produção

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0031 |
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

Configurar snapshot diário automático (ex.: pg_dump agendado) do Postgres de produção, com retenção definida, cobrindo Pessoas, Bases, execuções e conversas do assistente.

## Problema percebido

O Postgres de produção guardará dados reais de pessoas e conversas desde o primeiro dia do Beta, sem nenhuma rotina de backup hoje.

## Pessoa afetada ou beneficiada

Marcio, responsável por não perder dados reais das pessoas usuárias durante o Beta.

## Resultado ou valor esperado

Existe um snapshot diário do banco de produção com retenção definida, permitindo restaurar dados em caso de falha ou perda.

## Contexto

Item candidato do marco M03 (Deploy em Beta, Docker Swarm), decidido por Marcio em 2026-09-28: backup automático já deste o Beta, não adiado para um marco futuro. Depende do Postgres de produção (item de dockerização) já estar de pé.

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

- `specs/backlog/0028-dockerizar-aplicacao-e-stack-de-producao-docker-swarm.md` — bloqueante. O backup precisa do Postgres de produção já definido como serviço do Swarm.

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
