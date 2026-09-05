# Backlog: Cobrir o comportamento dos backends reais de vector store

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0013 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Prontidão de integração |
| Tipo | Técnico |
| Prioridade | P1 — alta |
| Milestones | M01 |
| Criado em | 2026-09-03 |
| Spec promovida | `specs/completed/0011-cobrir-comportamento-backend-real-qdrant/spec.md` (SPEC-0011, Complete) |

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

- Cada teste constrói o `_QdrantBackend` real e substitui apenas `_conn()` por
  um cliente-dublê; nenhuma outra parte do backend é mockada.
- O dublê imita somente o subconjunto de métodos do `qdrant-client`
  efetivamente chamado por cada operação (`get_collections`,
  `create_collection`, `scroll`, `upsert`, `delete`, `search`), registrando as
  chamadas recebidas — mesmo padrão de `_ClienteQdrant` em
  `tests/test_describe_scope_backends.py`. Não criar um fake genérico e
  reutilizável do SDK inteiro.
- Cada teste prova dois lados da tradução: os argumentos exatos que o backend
  envia ao SDK (filtro de escopo, `PointStruct`, `PointIdsList`, `wait=True`
  etc.) e a tradução da resposta do SDK de volta ao contrato neutro
  (`SearchResult`, `set[str]`, `None`).
- `ensure` é idempotente: só chama `create_collection` quando a coleção não
  existir na resposta de `get_collections`.
- `write` e `remove` não chamam o SDK (`upsert` / `delete`) quando a lista de
  registros ou ids recebida estiver vazia — replica a guarda já existente no
  código de produção.
- `scope_ids` agrega os ids de todas as páginas do `scroll` até `offset` ser
  `None`; uma falha do SDK durante a paginação deve levantar
  `UnreliableScopeReadError` encadeada (`from error`), sem propagar a exceção
  original ao chamador.
- Não alterar o comportamento de produção do adapter nem do `MirrorMixin`;
  esta fatia é caracterização por teste, não mudança de comportamento.

## Critérios de aceitação

- **AC-01 (ensure cria quando ausente):** Dado que `get_collections` não lista
  a coleção configurada, quando `ensure(scope, dimensions=N)` é chamado, então
  `create_collection` é chamado com `VectorParams(size=N, distance=COSINE)`.
- **AC-02 (ensure idempotente):** Dado que `get_collections` já lista a
  coleção configurada, quando `ensure` é chamado, então `create_collection`
  não é chamado.
- **AC-03 (write traduz e é no-op vazio):** Dado uma lista de `VectorRecord`,
  quando `write` é chamado, então `upsert` recebe `PointStruct` com `id`,
  `vector` e `payload` (`page_content` + `metadata`) corretos e `wait=True`;
  dado uma lista vazia, `upsert` não é chamado.
- **AC-04 (search traduz filtro e resposta):** Dado um embedding, `k` e um
  escopo com `tenant_id`, quando `search` é chamado, então o filtro enviado ao
  SDK contém as condições de `project_id` e `tenant_id`, e cada hit retornado
  pelo SDK é traduzido para `SearchResult(content, metadata, score)`.
- **AC-05 (scope_ids pagina até o fim):** Dado que `scroll` devolve múltiplas
  páginas com `offset` não nulo até a última, quando `scope_ids` é chamado,
  então o conjunto retornado agrega os ids de todas as páginas.
- **AC-06 (scope_ids traduz erro do SDK):** Dado que `scroll` levanta uma
  exceção do SDK durante a paginação, quando `scope_ids` é chamado, então
  `UnreliableScopeReadError` é levantada encadeada a partir da exceção
  original.
- **AC-07 (remove traduz e é no-op vazio):** Dado uma lista de ids, quando
  `remove` é chamado, então `delete` recebe `PointIdsList` com os ids e
  `wait=True`; dado uma lista vazia, `delete` não é chamado.

## Qualidades e operação

- Segurança: nenhuma superfície nova; os testes não tocam rede nem
  credenciais reais, só o cliente-dublê injetado via `_conn()`.
- Privacidade: sem dado real; os dublês usam identificadores e payloads
  sintéticos.
- Desempenho e volume: fora de escopo — não há teste de carga ou latência
  contra o Qdrant real, só tradução de argumentos e respostas sem rede.
- Auditoria e observabilidade: sem mudança; a fatia não altera os logs de
  `synchronize` nem as contagens de `SyncCounts`.

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
  BACKLOG-0014. BACKLOG-0014 foi entregue como SPEC-0010 (`Complete`); esta
  fatia está desbloqueada.
- **Decisão (2026-09-04):** o dublê do SDK imita somente o subconjunto
  explícito de métodos usados por operação (`get_collections`,
  `create_collection`, `scroll`, `upsert`, `delete`, `search`), seguindo o
  padrão de `_ClienteQdrant` em `tests/test_describe_scope_backends.py`; não
  criar um fake genérico e reutilizável do SDK inteiro.
- **Decisão (2026-09-04):** cada teste prova tanto os argumentos exatos
  enviados ao SDK quanto a tradução da resposta de volta ao contrato neutro,
  não só o valor de retorno.
- Nenhuma lacuna aplicável restante nesta rodada.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Item pronto para `$specsfy-03-specify`.
