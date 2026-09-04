# Pacotes e bibliotecas

<!-- specsfy:documentator:start -->
## Inventário

| Categoria | Escopo | Pacote | Versão | Finalidade | Fonte | GitHub |
| --- | --- | --- | --- | --- | --- | --- |
<!-- specsfy:documentator:end -->

## Dependências Python diretas

| Categoria | Pacote | Restrição | Finalidade | Fonte |
| --- | --- | --- | --- | --- |
| Vetores | `qdrant-client` | `==1.10.1` | Cliente Qdrant; única via de acesso ao destino desde a DEC-011 da SPEC-0003. Único provider concreto de vector store desde a SPEC-0010 | `pyproject.toml` |
| Embeddings | `langchain-huggingface` | `>=1.2.2` | Integração dedicada de embeddings Hugging Face locais (SPEC-0003) | `pyproject.toml` |
| RAG | `langchain`, `langchain-community`, `langchain-openai` | conforme `pyproject.toml` | Documentos, splitters, embeddings e vector stores | `pyproject.toml` |
| Providers | `openai`, `tiktoken` | conforme `pyproject.toml` | API e tokenização | `pyproject.toml` |
| Configuração | `python-dotenv`, `pyyaml` | conforme `pyproject.toml` | Ambiente e YAML | `pyproject.toml` |
| Backend de aplicação | `fastapi`, `python-multipart` | `>=0.141.1`, `>=0.0.32` | API HTTP e upload multipart do backend em `src/app/` (SPEC-0012) | `pyproject.toml` |
| Backend de aplicação | `psycopg[binary]`, `alembic` | `>=3.3.5`, `>=1.19.2` | Driver PostgreSQL e migrações do backend em `src/app/` (SPEC-0012) | `pyproject.toml` |
| Backend de aplicação | `procrastinate` | `>=3.9.0` | Fila de tarefas assíncronas sobre PostgreSQL, usada por `src/app/tasks.py` (SPEC-0012) | `pyproject.toml` |
| Backend de aplicação | `boto3` | `>=1.43.88` | Cliente S3-compatível para o Cloudflare R2, usado por `src/app/storage.py` (SPEC-0012) | `pyproject.toml` |
| Desenvolvimento | `pytest` | `>=8.3.0` | Testes automatizados | `pyproject.toml` |

As versões resolvidas, inclusive transitivas, permanecem em `uv.lock`.
`.specsfy/PACKAGES.md` fica vazio por desenho do gerador, pois inventaria
somente pacotes npm e Composer.
