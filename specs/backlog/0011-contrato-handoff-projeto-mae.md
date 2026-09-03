# Backlog: Definir o contrato de handoff para o projeto-mãe

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0011 |
| Status | Captured |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Prontidão de integração |
| Tipo | Técnico |
| Prioridade | P2 — média |
| Milestones | M01 |
| Criado em | 2026-09-03 |
| Spec promovida | Nenhuma |

## Ideia original

Consolidar um contrato de handoff para incorporar este componente ao rag-pipeline, separado dos gates de qualidade pela decisão de 2026-09-03.

## Problema percebido

O componente será incorporado ao backend do rag-pipeline como módulo interno, mas não existe documento que declare a interface Python estável, os pontos de entrada, a configuração exigida, os limites e as dívidas conhecidas que a equipe do projeto-mãe herdará.

## Pessoa afetada ou beneficiada

Mantenedores do rag-ingestion-pipeline e a equipe que fará a incorporação no rag-pipeline.

## Resultado ou valor esperado

A equipe do projeto-mãe recebe um contrato explícito do que consumir, como configurar e o que não esperar, sem precisar ler o código para descobrir.

## Contexto

Fatia (b) do desmembramento do BACKLOG-0007, decidido em 2026-09-03. A fatia (a), com Ruff e integração contínua, permanece no 0007. O BACKLOG-0008 já registra que a incorporação acontece no repositório rag-pipeline, depois que este componente estiver estável.

## Referências relacionadas

- `specs/backlog/0007-gates-entrega-handoff.md`: item de origem. Este backlog é a fatia (b) do desmembramento decidido em 2026-09-03; o 0007 ficou com Ruff e integração contínua. Tipo: backlog relacionado.
- `specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md`: épico que declara a incorporação ao backend do `rag-pipeline` como fatia 2, no repositório irmão, com interface Python estável chamada por FastAPI. Tipo: backlog relacionado.
- `docs/application.md`: inventário das superfícies atuais, incluindo as cinco CLIs e os módulos de `src/`. Tipo: documentação relacionada.
- `.specsfy/STACK.md` e `PROJECT.md`: capacidades, limites e tecnologias que o contrato precisa declarar. Tipo: documentação relacionada.
- `specs/inbox/2026-09-02-195708-carregar-o-env-nos-entrypoints-em-vez-do-import-de-config.md` e `specs/inbox/2026-09-02-195646-cobrir-o-comportamento-dos-backends-reais-de-vector-store.md`: dívidas conhecidas que o contrato deve declarar em vez de esconder. Tipo: captura relacionada.

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

- Decisão confirmada em 2026-09-03: o BACKLOG-0007 foi desmembrado em duas fatias porque Ruff e integração contínua são infraestrutura de qualidade mensurável, enquanto o contrato de handoff é um documento de interface entre repositórios que depende de decisões do projeto-mãe. Mantê-los juntos atrasaria a primeira.
- Aberto: o refinamento desta fatia ainda não foi feito. Falta esclarecer o formato do contrato, quais dívidas conhecidas ele declara, se ele fixa a assinatura da interface Python e se a raiz do `rag-pipeline` precisa estar confirmada antes de escrevê-lo.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
