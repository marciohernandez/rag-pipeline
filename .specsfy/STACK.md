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
| Embeddings | OpenAI, OpenRouter e Hugging Face | `config.yaml`, `src/embedder.py` e `pyproject.toml` |
| Banco vetorial principal | Qdrant Client 1.10.1 | `pyproject.toml`, `config.yaml` e `src/embedder.py` |
| Bancos vetoriais alternativos | ChromaDB e Pinecone | `pyproject.toml`, `config.yaml` e `src/embedder.py` |
| Configuração | YAML + python-dotenv | `config.yaml`, `src/config.py` e `pyproject.toml` |
| Interface operacional | CLI Python | `pipeline.py`, `search.py`, `chat.py` e `README.md` |
| Testes | Pytest 8.3+ | `pyproject.toml` e `tests/` |
<!-- specsfy:stack:end -->

## Decisões e observações do projeto

- A stack acima representa somente o que está implementado neste repositório.
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
