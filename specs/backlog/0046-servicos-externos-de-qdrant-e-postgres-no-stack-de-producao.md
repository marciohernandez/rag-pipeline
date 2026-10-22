# Backlog: Serviços externos de Qdrant e Postgres no stack de produção

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0046 |
| Status | Promoted |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-19 |
| Spec promovida | Nenhuma |

## Ideia original

Qdrant externo (URL e chave de API) e Postgres externo (host, banco, usuário e senha)

## Problema percebido

O stack de produção sobe Qdrant e Postgres em contêineres, com host e URL fixos. O beta deve usar o Qdrant já publicado e um Postgres gerenciado, sem subir esses serviços na VPS.

## Pessoa afetada ou beneficiada

Pessoa responsável pelo deploy do beta

## Resultado ou valor esperado

Stack de produção que se conecta a Qdrant e Postgres externos por configuração e secrets, mantém o backup cifrado no R2 e protege as coleções já existentes no Qdrant.

## Contexto

Decisões: Supabase em projeto novo, pooler em modo sessão, sslmode=require; Qdrant qdrant.smartsystem.ia.br com chave de API em secret e prefixo configurável de coleção (beta-); backup_ragpipeline mantido apontando para o Postgres externo; remover postgres_ragpipeline, qdrant_ragpipeline e seus volumes. Pré-requisito da T027 da SPEC-0032. Relacionados: specs/backlog/0028-dockerizar-aplicacao-e-stack-de-producao-docker-swarm.md, SPEC-0034 e SPEC-0035.

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

- Nenhuma registrada.

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

## Spec derivada

- `specs/draft/0041-servicos-externos-qdrant-postgres-producao/spec.md`
