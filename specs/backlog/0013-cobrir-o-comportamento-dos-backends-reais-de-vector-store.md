# Backlog: Cobrir o comportamento dos backends reais de vector store

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0013 |
| Status | Captured |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Prontidão de integração |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-09-03 |
| Spec promovida | Nenhuma |

## Ideia original

Nenhum teste do repositório exercita as classes reais de backend: _QdrantBackend, _ChromaBackend e _PineconeBackend. Toda a suíte de providers injeta FakeVectorBackend como cliente, então _create_backend() nunca roda e o código que fala com cada SDK só é executado em produção. A SPEC-0004 cobriu a superfície das cinco operações do port e o comportamento de describe, mas ensure, write, search e scope_ids continuam sem prova de comportamento. Cada backend tem um _conn() que permite injetar um cliente-dublê do SDK, então dá para cobrir sem rede.

## Problema percebido

A suíte prova a delegação do adapter base sobre um fake; a tradução de cada operação para o SDK real de Qdrant, ChromaDB e Pinecone nunca é executada por teste, então erro de integração só aparece durante uma sincronização real.

## Pessoa afetada ou beneficiada

Quem opera o pipeline e quem trocar de provider de banco vetorial.

## Resultado ou valor esperado

Erro de integração com o SDK passa a falhar no teste, sem exigir rede, usando o _conn() de cada backend para injetar um cliente-dublê.

## Contexto

Dívida declarada como bloqueante no BACKLOG-0011 (Pergunta 5, 2026-09-03): precisa ser resolvida antes de src/app/ receber implementação, porque incorporar o pipeline a um backend assíncrono move erro de tradução de SDK para dentro de execuções de produção.

## Referências relacionadas

- `specs/inbox/2026-09-02-195646-cobrir-o-comportamento-dos-backends-reais-de-vector-store.md`: captura de origem, preservada integralmente. Tipo: captura relacionada.
- `specs/backlog/0011-contrato-handoff-projeto-mae.md`: declara este item como dívida bloqueante da fronteira interna entre pipeline e backend de aplicação. Tipo: backlog relacionado.

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
