# Stack do sistema

Documente tecnologias estruturais e a evidência executável que confirma cada
uma. Preserve decisões humanas nas seções livres deste arquivo.

## Inventário detectado

<!-- specsfy:stack:start -->
| Camada | Tecnologia | Evidência |
| --- | --- | --- |
| Linguagem e runtime | Python 3.12+ | `pyproject.toml` (`requires-python = ">=3.12"`) |
| Gerenciamento de ambiente | uv | `uv.lock`, comandos documentados em `README.md` e `GUIA_DE_USO.md` |
| Pipeline RAG | LangChain 1.2+ | `pyproject.toml`, imports em `src/` e scripts da aplicação |
| Embeddings | OpenAI, OpenRouter e Hugging Face | `config.yaml`, `src/providers/embeddings/` e `pyproject.toml` |
| Banco vetorial principal | Qdrant Client 1.10.1 | `pyproject.toml`, `config.yaml` e `src/providers/vectorstores/qdrant.py` |
| Bancos vetoriais alternativos | ChromaDB e Pinecone | `pyproject.toml`, `config.yaml` e `src/providers/vectorstores/` |
| Integração dedicada de embeddings HF | `langchain-huggingface` 1.2.2 | `pyproject.toml` (`langchain-huggingface>=1.2.2`), `uv.lock` |
| Configuração | YAML + python-dotenv | `config.yaml`, `src/config.py` e `pyproject.toml` |
| Interface operacional | CLI Python | `pipeline.py`, `search.py`, `chat.py` e `README.md` |
| Testes | Pytest 8.3+ | `pyproject.toml` (`dependency-groups.dev` e `tool.pytest.ini_options`) e `tests/` |
<!-- specsfy:stack:end -->

## Decisões e observações do projeto

- A stack acima representa somente o que está implementado neste repositório.
- SPEC-0003 (2026-09-01) eliminou os imports legados
  `langchain_community.vectorstores.Qdrant` e
  `langchain_community.embeddings.HuggingFaceEmbeddings`. A substituição do
  lado Hugging Face usa a integração dedicada `langchain-huggingface==1.2.2`.
  Do lado Qdrant, a DEC-011 manteve o SDK `qdrant-client==1.10.1` como única
  via de acesso: a assinatura de `QdrantVectorStore` permaneceu não comprovada
  (R-002) e a API que o pipeline já usava em produção é a única confirmada para
  essa versão. `langchain-qdrant` chegou a ser instalado e foi removido por não
  ter uso.
- Desde a SPEC-0003, imports de SDK de banco vetorial e de classes de
  embeddings ficam confinados a `src/providers/`, com `ChatOpenAI` em `chat.py`
  como única exceção temporária (BACKLOG-0010). A regra está em
  `.specsfy/RULES.md` e é verificada por `tests/test_provider_boundaries.py`.
- O projeto-mãe `rag-pipeline` prevê FastAPI, PostgreSQL, Procrastinate,
  Cloudflare R2, LangGraph, Next.js, shadcn/ui, Tailwind e Docker Compose. Essas
  tecnologias são direção futura de integração, não dependências atuais deste
  componente.
- A constituição 1.2.1 do projeto-mãe exige LangGraph/LangChain-first para
  orquestrações de IA. O pipeline atual usa LangChain, mas não contém ainda a
  aplicação agentic completa descrita para o projeto-mãe.
- Especialista `specsfy-specialist-langchain` disponível em `.agents/skills/`.
  Carregar sempre que a tarefa tocar cadeias, agentes, grafos, prompts, tools,
  retrievers, vector stores ou embeddings sobre LangChain/LangGraph, ou a
  migração de imports da era v0. Ele documenta os servidores MCP oficiais
  `docs-langchain` e `reference-langchain` para confirmar a API v1.
