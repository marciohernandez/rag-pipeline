# LangGraph v1 e migração v0 → v1

Confirmar cada assinatura na API reference (`reference-langchain` /
https://langchain-ai.github.io/langgraph/) antes de aplicar. Este arquivo é um
mapa de decisão, não um substituto da referência.

## Quando usar LangGraph

| Necessidade | Ferramenta |
| --- | --- |
| Sequência linear de passos, sem estado | `Runnable` / LCEL (`a | b | c`) |
| Laço "modelo chama ferramentas até terminar" | `create_agent` (prebuilt) |
| Ramificação, ciclo, múltiplos atores, estado compartilhado, human-in-the-loop | `StateGraph` explícito |

## StateGraph — essencial

- **Estado**: `TypedDict` (ou dataclass / Pydantic) com os campos do fluxo.
  Campos acumuladores usam reducer (ex.: `Annotated[list, add_messages]`).
- **Nós**: função `state -> dict parcial de estado`. Nomear pela
  responsabilidade.
- **Arestas**: `add_edge(START, "no")`, `add_edge("no", END)`; ramificação com
  `add_conditional_edges("no", roteador)`.
- **Compilação**: `graph = builder.compile(checkpointer=...)`.

## Persistência (checkpointer)

- Habilita retomada, memória multi-turn e human-in-the-loop.
- Implementações: em memória (dev/teste), SQLite, Postgres.
- Execução carrega `config={"configurable": {"thread_id": "..."}}`.
- Dar checkpointer sempre que houver conversa contínua, aprovação humana ou
  necessidade de retomar após falha.

## Streaming

Modos de `.stream()` / `.astream()`:

- `values` — estado completo a cada passo.
- `updates` — só o delta de cada nó.
- `messages` — tokens do LLM conforme são gerados.
- `custom` — eventos emitidos pelo próprio código do nó.

## Human-in-the-loop

- `interrupt(payload)` dentro de um nó pausa o grafo e devolve o payload ao
  chamador.
- O chamador inspeciona / edita e retoma com `Command(resume=...)`.
- Requer checkpointer.

## Composição

- **Subgraphs**: um grafo compilado vira nó de outro; alinhar o schema de
  estado na fronteira.
- **`create_agent`** (em `langchain.agents`) é o agente prebuilt do v1 —
  laço ReAct com ferramentas, saída estruturada opcional e checkpointer.
  Substitui `langgraph.prebuilt.create_react_agent` da era anterior.

## Tabela de migração v0 → v1 (casos deste repositório)

| Padrão v0 no repo | Alvo v1 | Local |
| --- | --- | --- |
| `from langchain_community.vectorstores import Qdrant` | `from langchain_qdrant import QdrantVectorStore` (dep. `langchain-qdrant`) | `src/embedder.py:170` |
| `from langchain_community.embeddings import HuggingFaceEmbeddings` | `from langchain_huggingface import HuggingFaceEmbeddings` (dep. `langchain-huggingface`) | `src/embedder.py:132` |
| `from langchain_openai import OpenAIEmbeddings` | mantém — pacote dedicado já é o alvo v1 | `src/embedder.py:93`, `src/embedder.py:118` |
| `from langchain_chroma import Chroma` | mantém | `src/embedder.py:162`, `src/embedder.py:228` |
| `from langchain_pinecone import PineconeVectorStore` | mantém | `src/embedder.py:180`, `src/embedder.py:374` |
| LCEL puro: `ChatPromptTemplate | RunnablePassthrough | ChatOpenAI | StrOutputParser` | permanece válido para cadeia linear; migrar para `create_agent` só se a feature exigir ferramentas, estado ou HITL | `chat.py:20-23` |
| `from langchain_text_splitters import ...` | mantém — pacote dedicado é o alvo v1 | `src/chunker.py:13-14` |
| `from langchain_core.documents import Document` | mantém | vários arquivos em `src/` e `tests/` |

Observações:

- As versões exatas de assinatura mudam entre minors do v1; reconfirmar cada
  símbolo em `reference-langchain` antes de aplicar a migração.
- Migrar imports é uma tarefa/spec separada — esta skill documenta o caminho,
  não altera `src/` nem `pyproject.toml` por conta própria.
- Adicionar `langchain-qdrant` / `langchain-huggingface` ao `pyproject.toml`
  faz parte da spec de migração, não desta skill.
