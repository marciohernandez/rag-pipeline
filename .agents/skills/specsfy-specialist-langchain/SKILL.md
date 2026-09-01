---
name: specsfy-specialist-langchain
description: Orientar arquitetura e implementação com LangChain e LangGraph v1+ (agents, mensagens, tools, structured output, streaming, StateGraph, checkpointers, RAG e retrievers) e migração de padrões da era v0. Use ao criar ou evoluir orquestração de IA, cadeias, agentes ou recuperação; não use para ajustes que não tocam a camada LangChain.
---

# LangChain e LangGraph v1+

Use esta skill para entender e evoluir orquestração de IA sobre LangChain e
LangGraph, sem escolher biblioteca, provider ou padrão por suposição. Leia a
stack, `pyproject.toml`, os imports em `src/` e os scripts de aplicação antes de
propor alteração. Confirme a superfície de API contra fonte canônica (servidores
MCP oficiais ou `docs.langchain.com`) antes de escrever código: as assinaturas
mudam entre minors do v1 e muitos exemplos públicos ainda são v0.

## Quando usar

- Use ao adicionar ou alterar cadeias, agentes, grafos, prompts, tools,
  retrievers, vector stores ou embeddings sobre LangChain.
- Use ao migrar imports e APIs da era v0 (`langchain.*` monolítico,
  `langchain_community.*`) para os pacotes v1.
- Use ao decidir entre uma cadeia linear (LCEL/`Runnable`), um agente prebuilt
  (`create_agent`) e um grafo explícito (`StateGraph`).
- Não use para escolher outra biblioteca de orquestração sem evidência do
  projeto, nem para mudanças que não tocam a camada LangChain.

## Fluxo

1. Ler stack, `pyproject.toml`, imports em `src/` e scripts (`pipeline.py`,
   `search.py`, `chat.py`, `upsert_from_chunks.py`).
2. Confirmar cada símbolo e assinatura contra a fonte canônica (MCP
   `reference-langchain` / `docs-langchain` ou `reference.langchain.com`) antes
   de escrever. Não hardcodar de memória.
3. Escolher o menor building block que resolve: `Runnable`/LCEL para composição
   linear, `create_agent` para laço de ferramentas prebuilt, `StateGraph` só
   quando há ramificação, ciclo ou estado que a cadeia linear não expressa.
4. Definir estado, persistência (checkpointer), modo de streaming e tratamento
   de erro de forma explícita.
5. Derivar cenários de teste Pytest para o comportamento novo, incluindo
   entrada inválida e falha de ferramenta.
6. Registrar a decisão e a migração de qualquer padrão v0 que a mudança tocar.

## Padrões

- Selecionar modelo com `init_chat_model`; não instanciar classe de provider
  direto quando a seleção puder ser parametrizada.
- Usar mensagens e content blocks de `langchain_core.messages`; tratar conteúdo
  multimodal como blocos, não string.
- Declarar ferramentas com `@tool` e ligar via `bind_tools`; validar entrada
  com o schema da ferramenta.
- Obter saída tipada com `with_structured_output` em vez de parsing manual.
- Fazer streaming com `.stream()` / `.astream()` e modo explícito
  (`values`, `updates`, `messages`, `custom`).
- Construir retriever a partir do vector store (`VectorStore.as_retriever`);
  manter parâmetros de busca (`k`, filtro, score threshold) na configuração.
- Preferir pacotes de integração dedicados — `langchain-openai`,
  `langchain-qdrant`, `langchain-chroma`, `langchain-pinecone`,
  `langchain-huggingface` — em vez de `langchain_community.*` quando houver
  equivalente.
- Usar `StateGraph` apenas com estado tipado e reducers; nomear nós pela
  responsabilidade.
- Dar checkpointer ao agente ou grafo sempre que houver multi-turn, retomada ou
  human-in-the-loop.

## Antipadrões

- Importar de `langchain.*` monolítico o que migrou para `langchain_core` ou
  para um pacote de integração.
- Manter `from langchain_community.vectorstores import Qdrant` quando
  `langchain-qdrant` cobre o caso.
- Criar `StateGraph` para um fluxo que é uma sequência linear de passos.
- Rodar agente com estado conversacional sem checkpointer.
- Copiar exemplos de tutoriais v0 sem checar deprecações na API reference
  atual.
- Inventar campos de estado, nós ou ferramentas sem uso observado.

## Validação

- Rodar os testes Pytest ligados à mudança e observar RED antes de GREEN.
- Executar de ponta a ponta o script ou CLI afetado (`pipeline.py`,
  `search.py`, `chat.py`).
- Conferir que nenhum import deprecado novo foi introduzido
  (`grep -rn "langchain_community" src/`).
- Validar a superfície usada contra a API reference canônica; não declarar
  pronto sem uma saída verificável do projeto.

## Skills relacionadas

- `$specsfy-specialist-data-modeling` para contratos de documento, chunk e
  embedding.
- `$specsfy-specialist-software-architecture` para boundaries e dependências da
  camada de orquestração.
- `$specsfy-aux-stack` para registrar mudança estrutural de tecnologia.
- `$specsfy-specialist-postgres` quando a persistência do checkpointer ou do
  vector store for Postgres.

Leia [references/standards.md](references/standards.md) para fontes oficiais,
servidores MCP e a superfície v1; e
[references/langgraph-v1.md](references/langgraph-v1.md) para LangGraph e
migração v0 → v1.
