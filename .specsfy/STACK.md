# Stack do sistema

Documente tecnologias estruturais e a evidência executável que confirma cada
uma. Preserve decisões humanas nas seções livres deste arquivo.

## Inventário detectado

<!-- specsfy:stack:start -->
| Camada | Tecnologia | Evidência |
| --- | --- | --- |
| Infraestrutura de desenvolvimento e testes | Docker Compose | `docker-compose.yml` (PostgreSQL de teste) |
| Empacotamento do backend e worker | Docker (`python:3.12-slim`, uv 0.12.15, usuário não-root) | `deploy/backend/Dockerfile` e `.dockerignore` (SPEC-0022) |
| Empacotamento do frontend | Docker multi-stage (`node:24-slim`, Next.js standalone, usuário `node`) | `deploy/frontend/Dockerfile`, `frontend/.dockerignore` e `frontend/next.config.ts` (SPEC-0022) |
| Orquestração de produção | Docker Swarm/Compose 3.7, cinco serviços, secrets/volumes/rede externos e placement por hostname | `deploy/stack.prod.yml` (SPEC-0022) |
| Entrega da stack de produção | Builds locais fail-fast e `docker stack deploy --resolve-image never`, com serviços fixados ao respectivo node de build/dados | `deploy/build_and_deploy.sh`, `deploy/backend/Dockerfile`, `deploy/frontend/Dockerfile` e `deploy/stack.prod.yml` (SPEC-0022) |
| Linguagem e runtime | Python 3.12+ | `pyproject.toml` (`requires-python = ">=3.12"`) |
| Gerenciamento de ambiente | uv | `uv.lock`, comandos documentados em `README.md` e `GUIA_DE_USO.md` |
| Pipeline RAG | LangChain 1.2+ | `pyproject.toml`, imports em `src/` e scripts da aplicação |
| Embeddings | OpenAI, OpenRouter e Hugging Face | `config.example.yaml` versionado, `config.yaml` local, `src/pipeline/providers/embeddings/` e `pyproject.toml` |
| Banco vetorial | Qdrant Client 1.10.1 (único provider concreto) | `pyproject.toml`, `config.example.yaml` versionado, `config.yaml` local e `src/pipeline/providers/vectorstores/qdrant.py` |
| Abstração de vector store | Contrato neutro + `ProviderFactory` extensível + `InMemoryVectorStoreAdapter` (oráculo) | `src/pipeline/providers/contracts.py`, `src/pipeline/providers/factory.py`, `src/pipeline/providers/vectorstores/{base,in_memory}.py` e `tests/test_vectorstore_conformance.py`. ChromaDB e Pinecone removidos pela SPEC-0010 |
| Integração dedicada de embeddings HF | `langchain-huggingface` 1.2.2 | `pyproject.toml` (`langchain-huggingface>=1.2.2`), `uv.lock` |
| Configuração | YAML + python-dotenv | `config.example.yaml` neutro e versionado, `config.yaml` local ignorado pelo Git, `src/pipeline/config.py` (lê o YAML, sem carregar `.env`) e `pyproject.toml` |
| Carga do `.env` | `src/bootstrap.py` (`load_env()`) | Ponto único de carga do `.env`, chamado por cada entrypoint `.py` da raiz no início de `main()`; `src/pipeline/` não importa `python-dotenv`. Verificado por `tests/test_env_bootstrap.py` (SPEC-0009) |
| Fronteira interna | Fachada Python síncrona | `src/pipeline/service.py`, `src/app/__init__.py` e `tests/test_application_boundaries.py` |
| Backend de aplicação | FastAPI 0.141+ sobre servidor ASGI Uvicorn | `pyproject.toml` (`fastapi>=0.141.1`, `python-multipart>=0.0.32`, `uvicorn>=0.34.0`), `src/app/main.py`, `src/app/routers/` e o comando `uv run uvicorn src.app.main:app` documentado no `README.md` (SPEC-0012; `uvicorn` declarado na Fase 9) |
| Persistência do backend de aplicação | PostgreSQL via SQLAlchemy 2 + psycopg 3 | `pyproject.toml` (`psycopg[binary]>=3.3.5`), `src/app/db.py`, `src/app/models.py` (tabelas `bases`, `executions`, `queries`) (SPEC-0012) |
| Migrações do backend de aplicação | Alembic | `pyproject.toml` (`alembic>=1.19.2`) (SPEC-0012) |
| Hash de senhas | Argon2id via argon2-cffi 25.1.0 | `pyproject.toml` (`argon2-cffi>=25.1.0`), `uv.lock` (`argon2-cffi` 25.1.0) e `src/app/security.py` (`PasswordHasher`, hash e verificação) (SPEC-0020) |
| Cifra de segredos das conexões de ingestão | `cryptography` 50.0.2 (Fernet), chave única fornecida por `APP_CONEXOES_CHAVE` ou `APP_CONEXOES_CHAVE_FILE` (secret do Swarm), sem rotação automática | `pyproject.toml` (`cryptography>=50.0.2`), `uv.lock`, `src/app/settings.py` (`conexoes_chave`, fora do `repr`), `src/app/main.py` e `src/app/conexoes.py` (cifra e validação, SPEC-0026) |
| Orquestração do assistente | LangGraph 1.1+ (dependência direta) | `pyproject.toml` (`langgraph>=1`), `uv.lock` e, a partir da SPEC-0021, `src/pipeline/assistant.py` |
| Contrato de chat com LLM | `ChatModelAdapter`/`ChatMessage` neutros, adapter OpenRouter por `ChatOpenAI` confinado a `src/pipeline/providers/llm/` (SPEC-0021) | `src/pipeline/providers/contracts.py`, `factory.py` e `llm/openrouter.py`; `chat.py` segue como exceção rastreada |
| Execução assíncrona do backend de aplicação | Procrastinate sobre o mesmo PostgreSQL | `pyproject.toml` (`procrastinate>=3.9.0`), `src/app/tasks.py` (SPEC-0012) |
| Armazenamento de arquivos enviados | Cloudflare R2 (S3-compatível) via boto3, com fallback em disco local fora de produção | `pyproject.toml` (`boto3>=1.43.88`), `src/app/storage.py` (`S3CompatibleStorage`, `LocalDirectoryStorage`) (SPEC-0012) |
| Autenticação do backend de aplicação | Pessoa, vínculo e sessão revogável com token opaco e senha Argon2id | `src/app/auth.py`, `src/app/accounts.py`, `src/app/security.py`, `src/app/routers/auth.py`, `src/app/models.py` e revisão Alembic `0020_pessoas` (SPEC-0020) |
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
- SPEC-0010 (2026-09-04) removeu as implementações concretas de vector store
  ainda não escolhidas — ChromaDB e Pinecone — junto com as dependências
  `chromadb`, `langchain-chroma` e `langchain-pinecone`. A abstração
  multi-provider foi preservada: o contrato neutro, o backend port, a
  `ProviderFactory` e o `InMemoryVectorStoreAdapter` continuam extensíveis.
  Adicionar um provider volta a ser: novo módulo em
  `src/pipeline/providers/vectorstores/`, entrada em `_VECTOR_STORES` e
  parametrização da suíte de conformidade.
- A SPEC-0012 (2026-09-04) adotou, para o backend de aplicação deste
  componente, quatro das tecnologias antes listadas como direção futura do
  projeto-mãe: FastAPI, PostgreSQL, Procrastinate e Cloudflare R2. Elas deixam
  de ser "direção futura" e passam a ser dependências implementadas em
  `src/app/` (ver linhas do inventário acima). Docker Compose também deixa de
  ser direção futura — `docker-compose.yml` (raiz) provisiona o Postgres de
  teste reproduzível (ver nota abaixo).
- A SPEC-0013 (2026-09-05) adotou a stack de frontend antes listada como
  direção futura: **Next.js, React, TypeScript, Tailwind CSS, shadcn/ui e
  Vitest** deixam de ser "direção futura" e passam a ser dependências
  implementadas em `frontend/` (projeto Node autocontido, DEC-001 —
  `package.json`/`tsconfig.json`/`components.json` próprios, sem misturar com o
  tooling `uv`). Apenas LangGraph e as integrações de IA agentic seguem como
  direção futura. Detalhamento na seção "Stack de frontend (`frontend/`)"
  abaixo; o scanner de `update_stack.mjs` só lê manifests da raiz e não
  inventaria `frontend/package.json` — a tabela abaixo é curada manualmente,
  como já ocorre com `.specsfy/DATABASE.md` (ver `.specsfy/RULES.md`).
- A constituição 1.2.1 do projeto-mãe exige LangGraph/LangChain-first para
  orquestrações de IA. O pipeline atual usa LangChain, mas não contém ainda a
  aplicação agentic completa descrita para o projeto-mãe.
- Especialista `specsfy-specialist-langchain` disponível em `.agents/skills/`.
  Carregar sempre que a tarefa tocar cadeias, agentes, grafos, prompts, tools,
  retrievers, vector stores ou embeddings sobre LangChain/LangGraph, ou a
  migração de imports da era v0. Ele documenta os servidores MCP oficiais
  `docs-langchain` e `reference-langchain` para confirmar a API v1.
- Os testes de `src/app/` (SPEC-0012) exigem um PostgreSQL acessível via
  `APP_DATABASE_URL` (padrão de teste:
  `postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test`).
  `docker-compose.yml` (raiz, serviço `postgres-test`) provisiona esse
  Postgres de forma reproduzível (`docker compose up -d postgres-test`),
  documentado em `README.md`. Nesta máquina de desenvolvimento, o contêiner
  `rag-pipeline-test-postgres` já estava no ar (criado manualmente antes do
  compose existir) com estado acumulado da sessão de trabalho (tabelas da
  aplicação, migração Alembic e schema do Procrastinate já aplicados); o
  compose não foi executado contra ele para não recriar o contêiner e perder
  esse estado — a definição foi validada com `docker compose config`.

## Stack de frontend (`frontend/`)

Projeto Node autocontido criado pela SPEC-0013 (fatia 3, frontend
demonstrável). Curado manualmente — o scanner só lê a raiz.

| Camada | Tecnologia | Evidência |
| --- | --- | --- |
| Framework e roteamento | Next.js 16.3.4 (App Router) | `frontend/package.json` (`next`), `frontend/src/app/` (rotas `/login`, `/projeto`, `/execucoes/[id]`, grupo `(autenticado)`), `next.config.ts` |
| UI | React 19.2.8 | `frontend/package.json` (`react`, `react-dom`) |
| Linguagem | TypeScript 5 | `frontend/tsconfig.json` (`strict`), script `typecheck` (`tsc --noEmit`) |
| Typecheck do build | API TypeScript do Next (sem CLI experimental) | `frontend/next.config.ts` (`experimental.useTypeScriptCli: false`); mantém a checagem de tipos sem depender da captura de `tsc --showConfig` no Node 24 |
| Estilo | Tailwind CSS v4 | `frontend/package.json` (`tailwindcss@^4`, `@tailwindcss/postcss`), `frontend/src/app/globals.css` |
| Primitives de UI | shadcn/ui (preset `base-nova`, sobre Base UI `@base-ui/react`) | `frontend/components.json`, `frontend/src/components/ui/` (`button`, `input`, `label`, `alert`, `sheet`, `dialog`, `badge`, `skeleton`, `spinner`) |
| Registry de composições | ReUI (`@reui`, itens gratuitos `@reui/c-*`) | `frontend/components.json` (`registries["@reui"]`); avaliado `@reui/data-grid` e preterido por uma tabela semântica (ver `INTERFACE.md`) |
| Ícones | lucide-react | `frontend/package.json`, `frontend/components.json` (`iconLibrary: "lucide"`) |
| Cliente HTTP | `fetch` nativo encapsulado | `frontend/src/lib/api-client.ts` (`apiFetch`/`apiJson`, injeta `Authorization`, trata 401), `frontend/src/lib/session.ts` (`sessionStorage`) |
| Testes | Vitest 5 + Testing Library (jsdom) | `frontend/package.json` (`vitest`, `@testing-library/*`, `jsdom`), `frontend/vitest.config.mts`, script `test:tdd` (`vitest run`); 25 arquivos `*.test.tsx` em `frontend/src/**` |
| Qualidade estática | ESLint 9 (`eslint-config-next`) | `frontend/package.json`, script `lint` (`eslint`) |
| CSP | Cabeçalho básico sem nonce | `frontend/next.config.ts` (`script-src 'self' 'unsafe-inline'`, DEC-004). Sem `connect-src`: `fetch` herda `default-src 'self'`, o que torna o proxy abaixo obrigatório |
| Integração com a API | Proxy de mesma origem no servidor do Next | `frontend/next.config.ts` (`rewrites()` de `/api/:path*` para `API_PROXY_TARGET`, padrão `http://127.0.0.1:8000`), `frontend/.env.example`, guard `frontend/src/lib/api-proxy.test.ts` (SPEC-0013, Fase 11). O backend não instala `CORSMiddleware`: chamada cross-origin morre no preflight `OPTIONS` (405) |

- Autenticação do frontend: login por e-mail e senha; somente o token opaco de
  sessão fica em `sessionStorage`. A identidade e o papel vêm de
  `GET /api/v1/auth/me`, são armazenados como cache separado e nunca são
  inferidos do texto do token. Respostas 401 limpam a sessão e levam ao Login.
- CI do frontend: job dedicado em `.github/workflows/ci.yml`, separado do job
  Python (FIND-ARCH-001, SPEC-0013).

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

## Isolamento da regressão (SPEC-0022, T017)

- `tests/_database_safety.py` exige `.env.testing` com `APP_ENV=testing` e
  destino PostgreSQL explícito distinto do desenvolvimento, normalizando
  driver e aliases locais e recusando herança divergente.
- `tests/conftest.py` usa schemas exclusivos e rollback transacional; testes
  de concorrência/worker preservam commits em schemas próprios, sem limpeza
  global. Migrations só avançam, com inspeção AST dos contratos de reversão.
- `.env.testing.example` permite reproduzir a configuração local no CI;
  `.env.testing` é ignorado pelo Git e por `.dockerignore`.
