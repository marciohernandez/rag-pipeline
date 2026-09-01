# Banco de dados

Mapa de persistência do pipeline Python. Não inclui schemas internos de
dependências instaladas em `.venv`, pois eles pertencem aos fornecedores e não
ao domínio deste repositório.

## Fontes de dados

<!-- specsfy:database:start -->
| Fonte | Tecnologia/forma | Evidência |
| --- | --- | --- |
| Documentos de entrada | Arquivos Markdown com frontmatter YAML | `config.yaml`, `src/loader.py` |
| Auditoria de chunks | Arquivo JSON local | `config.yaml`, `src/exporter.py` |
| Manifesto de sincronização | Arquivo JSON local | `pipeline.py`, `src/manifest.py` |
| Banco vetorial principal | Collection Qdrant remota, configurada sem credenciais no código | `config.yaml`, `src/embedder.py` |
| Banco vetorial alternativo | Collection ChromaDB local | `config.yaml`, `src/embedder.py` |
| Banco vetorial alternativo | Índice e namespace Pinecone remotos | `config.yaml`, `src/embedder.py` |

## Estruturas detectadas

| Estrutura | Tipo | Campos | Relações | Fonte |
| --- | --- | --- | --- | --- |
| Documento Markdown | Arquivo de origem | `page_content`, frontmatter, `nome_arquivo`, `caminho_relativo`, `source_hash` | Origina um `document_id` e vários chunks | `src/loader.py`, `src/identity.py` |
| Chunk auditável | Item de `chunks.json` | `chunk_index`, `nome_arquivo`, `total_chunks`, `metadata`, `content`, `content_length` | Pertence a um documento; usa `chunk_id`, `document_id` e `project_id` | `src/exporter.py`, `src/identity.py` |
| Manifesto de execução | Objeto JSON | `run_id`, `generated_at`, `project_id`, `collection_name`, embedding, contagens, documentos, `chunk_ids` | Consolida documentos e chunks esperados antes da indexação | `src/manifest.py` |
| Ponto Qdrant | Vetor + payload | ID=`chunk_id`, vetor configurado, `page_content`, `metadata` | Escopo lógico por `metadata.project_id`; documento por `metadata.document_id` | `src/embedder.py` |
| Collection ChromaDB | Collection gerenciada pelo provider | Documento, embedding e metadados compatíveis com LangChain | Nome configurado; persistência no diretório local | `src/embedder.py`, `config.yaml` |
| Vetor Pinecone | Vetor + metadados | ID estável derivado de namespace, caminho e posição; conteúdo e metadados LangChain | Isolado por índice e namespace | `src/embedder.py`, `config.yaml` |
<!-- specsfy:database:end -->

## Decisões, ownership e retenção

- A pasta Markdown configurada é a fonte de verdade da execução local.
- No Qdrant, `sync_mode: mirror` remove somente IDs obsoletos do mesmo
  `project_id`, depois do upsert bem-sucedido dos pontos novos ou alterados.
- Identidades de documentos e chunks são determinísticas; `run_id` identifica
  apenas a execução do manifesto.
- O código atual não implementa tenant persistente. A exigência multi-tenant do
  projeto-mãe é uma restrição futura de integração, não um schema já existente.
- Ownership, classificação dos documentos de clientes e prazos de retenção não
  estão definidos nas fontes atuais e permanecem pendentes para a descoberta
  do produto completo.
