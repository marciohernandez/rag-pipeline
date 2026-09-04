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
    string tenant_id
    string chunk_type
    string type
    string version
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
JSON e o destino vetorial Qdrant (único provider concreto desde a SPEC-0010).
O contrato completo e suas evidências permanecem em `.specsfy/DATABASE.md`.

Desde o SPEC-0002, `document_id` recebido no frontmatter prevalece sobre a
identidade determinística, e `tenant_id` (opcional) estende o escopo lógico de
sincronização junto com `project_id`. `status` bloqueia a indexação por lista
configurável; `type` e `version` são metadado de auditoria sem efeito no
processamento.

## Persistência do backend de aplicação (SPEC-0012)

```mermaid
erDiagram
  BASE ||--o{ EXECUTION : tem
  BASE ||--o{ QUERY : tem

  BASE {
    string id
    string tenant_id
    string project_id
    string nome
    string origem
    datetime criado_em
    datetime apagada_em
  }
  EXECUTION {
    string id
    string base_id
    string situacao
    string etapa
    int previstos
    int inseridos
    int mantidos
    int removidos
    string erro
    datetime iniciado_em
    datetime concluido_em
  }
  QUERY {
    string id
    string base_id
    string tenant_id
    string project_id
    string pergunta
    string resultado
    json chunks_fontes
    datetime criado_em
  }
```

PostgreSQL, via SQLAlchemy (`src/app/models.py`) e Alembic para migrações.
Apagar uma `BASE` remove suas `EXECUTION` e `QUERY`, os arquivos no storage
(R2 ou disco local) e os vetores associados no vector store, preservando
apenas `apagada_em` preenchido e `nome` esvaziado como registro mínimo da
exclusão. Detalhes e evidências em `.specsfy/DATABASE.md`.
