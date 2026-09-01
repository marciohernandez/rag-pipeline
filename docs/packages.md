# Pacotes e bibliotecas

<!-- specsfy:documentator:start -->
## Inventário

| Categoria | Escopo | Pacote | Versão | Finalidade | Fonte | GitHub |
| --- | --- | --- | --- | --- | --- | --- |
<!-- specsfy:documentator:end -->

## Dependências Python diretas

| Categoria | Pacote | Restrição | Finalidade | Fonte |
| --- | --- | --- | --- | --- |
| Vetores | `qdrant-client` | `==1.10.1` | Cliente Qdrant; única via de acesso ao destino desde a DEC-011 da SPEC-0003 | `pyproject.toml` |
| Vetores | `chromadb`, `langchain-chroma` | `>=1.5.9`, `>=1.1.0` | Persistência ChromaDB | `pyproject.toml` |
| Vetores | `langchain-pinecone` | `>=0.2.13` | Integração Pinecone | `pyproject.toml` |
| Embeddings | `langchain-huggingface` | `>=1.2.2` | Integração dedicada de embeddings Hugging Face locais (SPEC-0003) | `pyproject.toml` |
| RAG | `langchain`, `langchain-community`, `langchain-openai` | conforme `pyproject.toml` | Documentos, splitters, embeddings e vector stores | `pyproject.toml` |
| Providers | `openai`, `tiktoken` | conforme `pyproject.toml` | API e tokenização | `pyproject.toml` |
| Configuração | `python-dotenv`, `pyyaml` | conforme `pyproject.toml` | Ambiente e YAML | `pyproject.toml` |
| Desenvolvimento | `pytest` | `>=8.3.0` | Testes automatizados | `pyproject.toml` |

As versões resolvidas, inclusive transitivas, permanecem em `uv.lock`.
`.specsfy/PACKAGES.md` fica vazio por desenho do gerador, pois inventaria
somente pacotes npm e Composer.
