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
  Loader --> Chunker[src.chunker]
  Chunker --> Identity[src.identity]
  Identity --> Manifest[src.manifest]
  Identity --> Exporter[chunks.json]
  Manifest --> Indexer[src.embedder]
  Indexer --> Qdrant[(Qdrant)]
  Indexer --> Chroma[(ChromaDB)]
  Indexer --> Pinecone[(Pinecone)]
  Qdrant --> Search[search.py / chat.py]
```

O pipeline é uma aplicação CLI modular em Python. `pipeline.py` compõe os
módulos; `src/embedder.py` ainda concentra criação de providers e persistência,
lacuna registrada no BACKLOG-0003. Identidades determinísticas e manifesto
sustentam idempotência e auditoria. O Qdrant implementa upsert antes da remoção
de obsoletos no mesmo `project_id`.
