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

**Redução de escopo confirmada em 2026-09-04:** o usuário só vai trabalhar com
Qdrant. ChromaDB e Pinecone deixam de fazer parte do projeto (BACKLOG-0014, que
enxuga os concretos mantendo o contrato multi-provider aberto). Esta fatia passa
a cobrir **apenas** o `_QdrantBackend` real e depende do BACKLOG-0014 ser
especificado e entregue antes, para não escrever teste para código removido.

## Referências relacionadas

- `specs/inbox/2026-09-02-195646-cobrir-o-comportamento-dos-backends-reais-de-vector-store.md`: captura de origem, preservada integralmente. Tipo: captura relacionada.
- `specs/backlog/0011-contrato-handoff-projeto-mae.md`: declara este item como dívida bloqueante da fronteira interna entre pipeline e backend de aplicação. Tipo: backlog relacionado.
- `specs/backlog/0014-enxugar-providers-concretos-qdrant.md`: remove Chroma e
  Pinecone do projeto; bloqueia esta fatia e reduz seu escopo a Qdrant-only.
  Tipo: backlog relacionado (dependência).

## Comportamento esperado

Cobrir o `_QdrantBackend` real (`src/pipeline/providers/vectorstores/qdrant.py`)
para as operações do port ainda sem prova de comportamento — `ensure`, `write`,
`search`, `scope_ids` e `remove` (esta via `MirrorMixin`; `describe` já foi
coberto pela SPEC-0004). Cada teste constrói o backend real e substitui o SDK do
Qdrant por um cliente-dublê (padrão de `tests/test_describe_scope_backends.py`),
sem rede: prova a tradução dos argumentos enviados ao SDK e a tradução da
resposta do SDK de volta ao contrato neutro, incluindo os caminhos de erro
conhecidos (`UnreliableScopeReadError` na releitura paginada que falha).
ChromaDB e Pinecone estão fora — não existirão mais no projeto após o
BACKLOG-0014.

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

- **BACKLOG-0014** (enxugar providers concretos para Qdrant): deve ser
  especificado e entregue antes, para que o escopo real seja só Qdrant.
- Contrato, backend port e adapter Qdrant entregues pela SPEC-0003.

## Situações de erro

- Releitura paginada do escopo no Qdrant que falha: `scope_ids` levanta
  `UnreliableScopeReadError` e a sincronização é bloqueada — precisa de prova de
  comportamento com dublê que força a exceção do SDK.

## Escopo

- Dentro: testes de comportamento do `_QdrantBackend` real para `ensure`,
  `write`, `search`, `scope_ids` e `remove`, com dublê de SDK, sem rede;
  registro da nova baseline de regressão.
- Fora: ChromaDB e Pinecone (removidos no BACKLOG-0014); `describe` (já coberto
  pela SPEC-0004); teste de integração contra um Qdrant real com rede;
  mudança de comportamento de produção do adapter.

## Dúvidas, decisões e riscos

- **Decisão (2026-09-04):** escopo reduzido a Qdrant-only; depende do
  BACKLOG-0014.
- **A decidir na spec:** se o dublê imita o SDK do Qdrant (`qdrant-client`) por
  subconjunto explícito de métodos usados (`get_collections`, `create_collection`,
  `scroll`, `upsert`, `delete`, `search`) ou por um fake mais completo.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
