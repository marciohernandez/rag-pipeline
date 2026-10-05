# Backlog: Domínio, HTTPS e reverse proxy para o Beta

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0029 |
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

Apontar um domínio próprio para o sistema em produção e servir a aplicação com HTTPS válido desde o início do Beta, via reverse proxy (ex.: Traefik ou Caddy) na frente dos serviços do Docker Swarm.

## Problema percebido

O sistema hoje só é acessível localmente; não há domínio, certificado nem reverse proxy configurados para expor a aplicação de forma segura.

## Pessoa afetada ou beneficiada

Marcio e a equipe de consultoria, ao acessar o sistema em produção durante o Beta.

## Resultado ou valor esperado

A aplicação é acessível por um domínio próprio com HTTPS válido, sem aviso de certificado inválido nem acesso só por IP/porta.

## Contexto

Item candidato do marco M03 (Deploy em Beta, Docker Swarm), decidido por Marcio em 2026-09-28: domínio próprio com HTTPS desde o início (não IP/porta). Depende do stack de produção (item de dockerização) já estar de pé.

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

- `specs/backlog/0028-dockerizar-aplicacao-e-stack-de-producao-docker-swarm.md` — bloqueante. O reverse proxy e o HTTPS precisam do stack de produção já rodando no Swarm.

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
