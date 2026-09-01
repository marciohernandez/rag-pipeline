# Aplicação e implementações

<!-- specsfy:documentator:start -->
## Superfícies

Categorias: Serviços, Rotas e APIs, Páginas, Componentes, Testes e Outras fontes.

Relação: relaciona cada arquivo observado à sua superfície.

| Categoria | Arquivo | Símbolos |
| --- | --- | --- |
| Outras fontes | — | Nenhum arquivo de código encontrado |
<!-- specsfy:documentator:end -->

## Inventário Python verificado

| Superfície | Arquivos | Responsabilidade |
| --- | --- | --- |
| Orquestração CLI | `pipeline.py` | Carregar, dividir, identificar, manifestar, exportar e indexar documentos. |
| Carga | `src/loader.py` | Ler Markdown, frontmatter e hash de origem com modo estrito. |
| Chunking | `src/chunker.py` | Dividir por títulos, caracteres ou blocos Q&A (`splitter: qa`) e gerar resumos de seção. |
| Identidade | `src/identity.py` | Produzir IDs e hashes determinísticos de documentos e chunks; preserva `document_id` recebido do frontmatter quando presente. |
| Manifesto | `src/manifest.py` | Construir, validar e exportar o manifesto da execução. |
| Exportação | `src/exporter.py` | Gerar auditoria JSON e resumo dos chunks. |
| Contratos de provider | `src/providers/contracts.py`, `errors.py`, `factory.py` | Definir tipos neutros, hierarquia de erros e o despacho de provider por nome. |
| Adapters de embeddings | `src/providers/embeddings/` | OpenAI, OpenRouter, Hugging Face e um fake determinístico, com cliente lazy. |
| Adapters de vector store | `src/providers/vectorstores/` | Qdrant, ChromaDB, Pinecone e in-memory; `base.py` orquestra a sincronização e emite as contagens. |
| Serviço de indexação | `src/indexing.py` | Traduzir `config.yaml` e chunks para os contratos, indexar e recuperar sob a política de segurança. |
| Segurança de sincronização | `src/safety.py` | Aplicar as guardas fail-closed de opção destrutiva, modo, escopo (project_id + tenant_id) e remoção. |
| Contrato de frontmatter | `src/status_gate.py` | Excluir documentos com status presente na lista bloqueante configurável, com registro auditável. |
| Configuração | `src/config.py`, `config.yaml` | Carregar configuração não sensível, ambiente e logging. |
| Consulta | `search.py`, `chat.py`, `demo_rag.py` | Busca e demonstrações RAG por linha de comando. |
| Importação auditada | `upsert_from_chunks.py` | Validar chunks contra manifesto e enviar ao destino vetorial. |
| Diagnóstico | `scripts/check_qdrant_connection.py`, `scripts/check_qdrant_search.py` | Conferir conexão e busca no Qdrant. |
