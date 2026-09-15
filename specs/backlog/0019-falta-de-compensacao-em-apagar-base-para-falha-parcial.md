# Backlog: Falta de compensação em apagar_base para falha parcial

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0019 |
| Status | Refining |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-09-15 |
| Spec promovida | Nenhuma |

## Ideia original

apagar_base não tem compensação se delete_scope ou o storage falharem após o soft-delete no Postgres já commitado: a base fica invisível (get_base_or_404 a exclui) e sem endpoint de retry, deixando storage/vetores órfãos permanentemente nesse cenário de falha parcial.

## Problema percebido

Se delete_scope ou o storage falharem depois do soft-delete já commitado em apagar_base, a base fica invisível (get_base_or_404 a exclui) e não existe endpoint de retry, deixando storage/vetores órfãos permanentemente.

## Pessoa afetada ou beneficiada

Não identificado no texto original.

## Resultado ou valor esperado

Não identificado no texto original.

## Contexto

Achado registrado em specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md, seção 16, como 'Não corrigido, registrado para spec/backlog futuro'; citado em specs/milestones/M02.md como item de dívida técnica sem milestone atribuída.

## Referências relacionadas

- `specs/inbox/2026-09-15-133813-falta-de-compensacao-em-apagar-base-para-falha-parcial.md` — captura de origem (proveniência).
- `specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md:1233` — spec relacionada: achado original "Não corrigido, registrado para spec/backlog futuro".
- `specs/milestones/M02.md` — documentação relacionada: item listado em "Fora de escopo" como dívida técnica sem milestone.
- `src/app/routers/bases.py:162-189` (`apagar_base`) — código relacionado: soft-delete commitado antes de `get_storage().delete_base` e `service.delete_scope`, sem bloco de compensação.
- `src/pipeline/service.py:175` (`delete_scope`) — operação que pode falhar depois do commit do soft-delete.

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
