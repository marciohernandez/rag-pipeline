# Arquitetura

<!-- specsfy:documentator:start -->
## Componentes

| Tipo | Quantidade |
| --- | --- |
| Código | 0 |
| Testes | 0 |

## Diagramas

```mermaid
flowchart TD
  Application[Aplicação]
```

```mermaid
classDiagram
  class Application
```
<!-- specsfy:documentator:end -->

## Arquitetura Python verificada

```mermaid
flowchart LR
  Markdown[Markdown + frontmatter] --> Loader[src.loader]
  Loader --> StatusGate[src.status_gate]
  StatusGate --> Chunker[src.chunker]
  Chunker --> Identity[src.identity]
  Identity --> Manifest[src.manifest]
  Identity --> Exporter[chunks.json]
  Manifest --> Indexer[src.embedder]
  Safety[src.safety] --> Indexer
  Indexer --> Qdrant[(Qdrant)]
  Indexer --> Chroma[(ChromaDB)]
  Indexer --> Pinecone[(Pinecone)]
  Qdrant --> Search[search.py / chat.py]
```

O pipeline é uma aplicação CLI modular em Python. `pipeline.py` compõe os
módulos; desde a SPEC-0003 a criação de providers e o acesso à persistência
vivem em `src/providers/`, atrás de contratos neutros e de uma factory, e
`src/indexing.py` traduz `config.yaml` e chunks para esses contratos. O antigo
`src/embedder.py`, lacuna registrada no BACKLOG-0003, foi removido.
Identidades determinísticas e manifesto sustentam idempotência e auditoria. O Qdrant implementa upsert antes da remoção
de obsoletos no mesmo `project_id`.

`src/safety.py` concentra a política fail-closed exigida antes de qualquer
mutação remota. `SyncSafetyPolicy` rejeita a opção `--recreate`, valida provider
e modo de sincronização, exige um único `project_id` sem `chunk_id` duplicado e
libera a remoção somente quando o destino confirma todos os pontos esperados.
Os entrypoints `pipeline.py` e `upsert_from_chunks.py` aplicam a guarda antes de
criar qualquer cliente.

`src/validation.py` estabelece a fronteira local da validação de recuperação:
ele lê e valida o gabarito versionado antes de compor ou consultar um adapter e,
só então, executa o preflight de ambiente — existência do escopo e dimensão
declarada pelo destino — por leitura pura, sem preparar a coleção.

Para conferir o destino sem alterá-lo, o contrato neutro expõe
`VectorStoreAdapter.describe_scope(scope)`, acrescentado pela SPEC-0004. A
operação é leitura pura: devolve existência e dimensão declaradas pelo destino,
ou um mapa vazio quando o escopo não existe. Ela existe porque `ensure_ready`
prepara o destino e cria a coleção ausente, o que uma validação somente leitura
não pode fazer. Cada backend a implementa com a leitura própria do seu SDK —
`get_collection` no Qdrant, cliente direto do ChromaDB em vez do construtor que
faz get-or-create, `describe_index` no Pinecone — e o backend em memória serve
de referência.

O contrato de recepção de Markdown do projeto-mãe (SPEC-0002) estende esse
desenho em quatro pontos: `document_id` do frontmatter tem precedência sobre a
identidade determinística (`src/identity.py`); `SyncSafetyPolicy.assert_valid_scope`
passou a validar e retornar também `tenant_id`, estendendo o escopo lógico
fail-closed para `project_id + tenant_id`; `src/status_gate.py` exclui, antes
do chunking, documentos com `status` presente em uma lista bloqueante
configurável (`contrato_markdown.status_bloqueado` em `config.yaml`); e
`src/chunker.py` ganhou o splitter `qa`, que divide o corpo por `++++` em um
chunk por bloco quando o documento declara `splitter: qa` no frontmatter.
`type` e `version` do frontmatter são propagados a cada chunk pelo mecanismo
de mesclagem de metadata já existente, sem efeito no processamento.
