# Pipeline RAG com LangChain

Pipeline de processamento de documentos Markdown para RAG (Retrieval-Augmented Generation).

> Consulte o [Guia de uso](GUIA_DE_USO.md) para o procedimento completo no WSL, organizacao por projeto, metadados, indexacao no Qdrant e atualizacoes sem duplicidade.

## Estrutura

```
rag-pipeline/
├── documentos/               ← fontes de entrada em Markdown e materiais do projeto
├── src/
│   ├── config.py             ← carrega config.yaml e .env
│   ├── loader.py             ← lê .md e extrai frontmatter YAML
│   ├── chunker.py            ← divide docs em chunks (respeita frontmatter)
│   ├── indexing.py           ← gera embeddings e sincroniza o vector store
│   ├── quality.py            ← avalia sinais de qualidade dos chunks
│   └── validation.py         ← valida a recuperação e a consistência do índice
├── output/
│   ├── chunks.json           ← chunks gerados (para inspeção)
│   └── manifest.json         ← metadados e auditoria da execução
├── pipeline.py               ← script principal (orquestrador da etapa 2)
├── search.py                 ← busca RAG simples no terminal
├── chat.py                   ← 🤖 chatbot interativo RAG com LLM
├── config.example.yaml       ← exemplo neutro versionado
├── config.yaml               ← configuração central local (não versionada)
├── .env.example              ← template de variáveis de ambiente
├── PROJECT.md                ← visão de arquitetura e visão do projeto-mãe
├── README.md                 ← visão geral do pipeline e uso
└── pyproject.toml            ← dependências gerenciadas pelo uv
```

## Setup

```powershell
# 1. Criar/ativar o ambiente virtual
uv venv
.venv\Scripts\activate

# 2. Instalar dependências (já feito pelo uv add)
uv sync

# 3. Criar a configuração local a partir do exemplo neutro
copy config.example.yaml config.yaml
# Edite o config.yaml com a identidade, os caminhos e o destino da sua base

# 4. Configurar variáveis de ambiente
copy .env.example .env
# Edite o .env com as credenciais reais
```

O `config.yaml` local concentra os parâmetros do projeto, como `projeto.nome`, `projeto.descricao`, `embedding.provider`, `embedding.model`, `vector_store.provider` e `vector_store.collection_name`. As ferramentas operacionais derivam dessa identidade suas mensagens e instruções ao modelo.
O `.env` deve ficar apenas com credenciais, como `OPENAI_API_KEY`, `OPENROUTER_API_KEY` e `QDRANT_API_KEY`.

## Resumos e sincronização

O pipeline gera `section_summary` automaticamente para seções Markdown com várias subseções. Esses chunks resumem os títulos de uma seção e melhoram a recuperação de perguntas amplas no Flowise, sem alterar os arquivos `.md` de origem.

Cada execução valida `chunks.json` e `manifest.json` antes de qualquer upsert. No modo Qdrant `mirror`, pontos obsoletos só são removidos após o envio bem-sucedido dos pontos novos ou alterados.

## Uso

### Executar o pipeline completo

```powershell
# Gera chunks + indexa no vector store configurado
uv run python pipeline.py

# Apenas gera chunks.json (sem indexar — útil para inspecionar)
uv run python pipeline.py --only-chunks
```

Para atualizar ou recuperar uma base inconsistente, gere e revise
`chunks.json` e `manifest.json`, confirme o destino em `config.yaml` e execute
o pipeline normalmente. A reexecução é idempotente no Qdrant: primeiro confirma
os pontos esperados e somente depois remove obsoletos do mesmo `project_id`.

### Buscar na base vetorial (Chunks puros)

Para testar apenas o "Retriever" e ver quais chunks estão sendo retornados pelo banco vetorial:

```powershell
uv run python search.py "quais informações estão disponíveis?"
uv run python search.py --k 6 "qual documento explica este assunto?"
```

### Interagir com o Chatbot RAG (LLM + Contexto)

Para testar o fluxo completo usando o LLM configurado no projeto para gerar as respostas com base no contexto indexado. 
Ele lê o histórico, recupera os `chunks` mais próximos, repassa a origem `[Capítulo > Subcapítulo]` (breadcrumbs) e pede para o LLM responder:

```powershell
uv run python chat.py
```
*Irá abrir um prompt interativo no terminal. Digite sua pergunta e veja o assistente formatar a resposta baseada nos manuais.*

## Configuração

Toda a configuração fica em `config.yaml`:

| Parâmetro | Descrição |
|---|---|
| `projeto.nome` | Nome lógico do projeto |
| `caminhos.*` | Caminhos de entrada, saída, chunks e persistência |
| `chunking.default_chunk_size` | Tamanho padrão dos chunks |
| `chunking.default_chunk_overlap` | Overlap padrão |
| `chunking.default_splitter` | `header` ou `recursive` |
| `embedding.provider` | `openrouter`, `openai` ou `huggingface` |
| `embedding.model` | Modelo de embeddings |
| `vector_store.provider` | `chroma`, `qdrant` ou `pinecone` |
| `vector_store.collection_name` | Nome da collection do projeto |

### Regra de configuração

- Use o `config.yaml` para parâmetros do projeto.
- Use o `.env` apenas para credenciais.
- Se mudar o provider ou o modelo, reindexe a collection no Qdrant.

### Frontmatter por arquivo

Cada `.md` pode sobrescrever as configurações globais via frontmatter:

```yaml
---
chunk_size_recommended: 1200
chunk_overlap_recommended: 200
splitter: "MarkdownHeaderTextSplitter"
---
```

## Provedores suportados

### Embeddings & LLM
- **OpenAI** (`text-embedding-3-small` / `text-embedding-3-large`) → requer `OPENAI_API_KEY`
- **OpenRouter** (`openai/text-embedding-3-small` / modelos LLM) → requer `OPENROUTER_API_KEY`
- **HuggingFace** (`paraphrase-multilingual-MiniLM-L12-v2`) → local, sem custo de API

### Vector Stores
- **ChromaDB** → local, zero configuração
- **Qdrant** → requer `QDRANT_URL` + `QDRANT_API_KEY`
- **Pinecone** → requer `PINECONE_API_KEY`

## Integração com Flowise

Ao usar a collection configurada para a sua base no Flowise, configure o nó Qdrant com:

- `Qdrant Collection Name`: o valor de `vector_store.collection_name`
- `Vector Dimension`: `1536` para `text-embedding-3-small`
- `Content Key`: `page_content`
- `Metadata Key`: `metadata`

Se o `Content Key` estiver como `content`, o Flowise pode mostrar `pageContent` vazio mesmo com os pontos indexados corretamente.

## Trocar para HuggingFace (sem custo)

No `config.yaml`:
```yaml
embedding:
  provider: huggingface
  model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

No `.env`:
```
EMBEDDING_PROVIDER=huggingface
```

## Backend de aplicação (FastAPI, SPEC-0012)

Além dos CLIs acima, `src/app/` expõe um backend FastAPI multi-tenant sobre o
mesmo pipeline (upload/base preparada, iniciar/repetir/apagar execução,
consultar). O processamento roda em segundo plano via
[Procrastinate](https://procrastinate.readthedocs.io/) sobre o mesmo
PostgreSQL da aplicação — a API só agenda a tarefa; um **worker separado**
precisa estar rodando para ela ser processada de fato.

### Variáveis de ambiente

- `APP_DATABASE_URL` — string de conexão PostgreSQL (SQLAlchemy), usada tanto
  pelas tabelas da aplicação quanto pela fila do Procrastinate.
- `APP_EMBEDDING_PROVIDER` / `APP_EMBEDDING_DIMENSIONS` — provider de
  embeddings (padrão `fake`, sem custo; use `openai`/`openrouter`/`huggingface`
  em produção).
- `APP_VECTOR_STORE_PROVIDER` / `APP_VECTOR_STORE_COLLECTION` — provider de
  vector store (**apenas `qdrant` é aceito para escrita**; o padrão
  `in_memory` só serve para leitura/demonstração local, nunca sincroniza).
- `APP_R2_BUCKET`, `APP_R2_ENDPOINT_URL`, `APP_R2_ACCESS_KEY_ID`,
  `APP_R2_SECRET_ACCESS_KEY` — credenciais do Cloudflare R2; sem elas, os
  arquivos enviados ficam em `APP_LOCAL_STORAGE_DIR` (padrão
  `output/uploads`), útil para desenvolvimento local.

### Postgres de teste local

```bash
docker compose up -d postgres-test
```

Sobe um Postgres 16 em `localhost:55432` (usuário `postgres`, senha `postgres`,
banco `rag_pipeline_test`), o mesmo destino esperado por `tests/conftest.py`.

### Preparar o banco (uma vez por ambiente novo)

```bash
# Schema da aplicação (tabelas bases/executions/queries)
uv run alembic upgrade head

# Schema interno do Procrastinate (fila de jobs) — só na primeira vez;
# rodar de novo contra um banco já preparado falha (schema já existe)
uv run python -m procrastinate --app src.app.tasks.app schema --apply
```

### Rodar a API

```bash
uv run uvicorn src.app.main:app --reload
```

### Rodar o worker

A tarefa `process_base_task` só é executada por um worker Procrastinate
rodando **fora** do processo da API:

```bash
uv run python -m procrastinate --app src.app.tasks.app worker
```

Sem esse processo, toda execução fica presa em `pending` indefinidamente.
