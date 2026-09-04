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
| Embeddings | OpenAI, OpenRouter e Hugging Face | `config.example.yaml` versionado, `config.yaml` local, `src/pipeline/providers/embeddings/` e `pyproject.toml` |
| Banco vetorial principal | Qdrant Client 1.10.1 | `pyproject.toml`, `config.example.yaml` versionado, `config.yaml` local e `src/pipeline/providers/vectorstores/qdrant.py` |
| Bancos vetoriais alternativos | ChromaDB e Pinecone | `pyproject.toml`, `config.example.yaml` versionado, `config.yaml` local e `src/pipeline/providers/vectorstores/` |
| Integração dedicada de embeddings HF | `langchain-huggingface` 1.2.2 | `pyproject.toml` (`langchain-huggingface>=1.2.2`), `uv.lock` |
| Configuração | YAML + python-dotenv | `config.example.yaml` neutro e versionado, `config.yaml` local ignorado pelo Git, `src/pipeline/config.py` (lê o YAML, sem carregar `.env`) e `pyproject.toml` |
| Carga do `.env` | `src/bootstrap.py` (`load_env()`) | Ponto único de carga do `.env`, chamado por cada entrypoint `.py` da raiz no início de `main()`; `src/pipeline/` não importa `python-dotenv`. Verificado por `tests/test_env_bootstrap.py` (SPEC-0009) |
| Fronteira interna | Fachada Python síncrona | `src/pipeline/service.py`, `src/app/__init__.py` e `tests/test_application_boundaries.py` |
| Interface operacional | CLI Python | `pipeline.py`, `search.py`, `chat.py`, `validate.py`, `quality.py` e `README.md` |
| Testes | Pytest 8.3+ | `pyproject.toml` (`dependency-groups.dev` e `tool.pytest.ini_options`) e `tests/` |
| Qualidade estática | Ruff 0.16.5 | `pyproject.toml` (`dependency-groups.dev`, `tool.ruff` com `line-length = 100`, `extend-select` e exclusão de `.agents`) e `uv.lock` |
| Integração contínua | GitHub Actions | `.github/workflows/ci.yml` (push, pull request, Python 3.12, uv 0.11.16, Ruff e Pytest) |
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
  embeddings ficam confinados a `src/pipeline/providers/`, com `ChatOpenAI` em `chat.py`
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

## Chaves de configuração da validação de recuperação

A SPEC-0004 acrescentou três chaves não sensíveis ao contrato exemplificado em
`config.example.yaml` e preenchido localmente em `config.yaml`. Elas
pertencem à configuração estrutural porque `validate.py` não aceita nenhuma
entrada fora do `config.yaml` da base: sem elas o comando não valida e encerra
com código `2`, antes de qualquer acesso remoto.

| Chave | Obrigatória | Valor padrão | Finalidade | Evidência |
| --- | --- | --- | --- | --- |
| `caminhos.consultas_referencia` | Sim | — | Caminho do gabarito versionado de consultas da base, lido localmente antes de tocar o destino | `config.yaml`, `src/pipeline/validation.py` (`load_query_cases`, ausência levanta `Configuração sem caminhos.consultas_referencia.`) |
| `validacao.limiar_minimo` | Sim | — | Score mínimo a partir do qual um resultado reprova uma consulta declarada como `sem_resposta`; calibrado por provider de embeddings | `config.yaml`, `src/pipeline/validation.py` (`_avaliar`, ausência levanta `Configuração sem validacao.limiar_minimo`) |
| `validacao.top_k` | Não | `4` | Número máximo de resultados avaliados por consulta do gabarito | `config.yaml`, `src/pipeline/validation.py` (`run_query_cases`) |

- O gabarito apontado por `caminhos.consultas_referencia` é um YAML de lista,
  com `pergunta` e `categoria` obrigatórias em cada entrada e `deve_conter` ou
  `documento_esperado` exigidos fora da categoria `sem_resposta`. Um gabarito
  malformado encerra a validação com código `2`.
- `deve_conter` é comparado por substring exata sobre o conteúdo dos resultados
  recuperados. Ao escrever um gabarito, copie os trechos do conteúdo real dos
  chunks em `output/<base>/chunks.json`, não do Markdown de origem: o chunking
  por cabeçalho e os resumos de seção mudam o texto que chega ao índice.
- `limiar_minimo` é específico da combinação de provider, modelo e banco
  vetorial. Trocar `embedding.provider` ou `embedding.model` exige recalibrar o
  valor antes de confiar em uma reprovação de `sem_resposta`.
