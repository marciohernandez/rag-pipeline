# Banco de dados

<!-- specsfy:documentator:start -->
## Fontes de persistência

| Arquivo |
| --- |
| Nenhuma estrutura confirmada além das fontes listadas. |

```mermaid
erDiagram
  ENTITY { string id }
```
<!-- specsfy:documentator:end -->

## Persistência verificada do componente

```mermaid
erDiagram
  DOCUMENTO ||--o{ CHUNK : origina
  EXECUCAO ||--|| MANIFESTO : gera
  MANIFESTO ||--o{ CHUNK : relaciona
  CHUNK ||--|| PONTO_VETORIAL : indexa

  DOCUMENTO {
    string document_id
    string source_hash
    string caminho_relativo
  }
  CHUNK {
    string chunk_id
    string document_id
    string project_id
    string chunk_type
  }
  MANIFESTO {
    string run_id
    string project_id
    int total_chunks
  }
  PONTO_VETORIAL {
    string chunk_id
    vector embedding
    json metadata
  }
```

As fontes persistentes são os Markdown de entrada, `chunks.json`, o manifesto
JSON e os destinos vetoriais Qdrant, ChromaDB ou Pinecone. O contrato completo
e suas evidências permanecem em `.specsfy/DATABASE.md`.
