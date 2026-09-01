# Padrões e referências de LangChain / LangGraph v1+

## Fontes oficiais

- LangChain docs (conceitos, guias, how-tos v1): https://docs.langchain.com/
- API reference canônica (classes, métodos, parâmetros):
  https://reference.langchain.com/
- LangGraph docs: https://langchain-ai.github.io/langgraph/
- LangChain Python (referência complementar): https://python.langchain.com/
- Guia de migração v0 → v1 e release notes: seção "Versions / Migration" em
  https://docs.langchain.com/

Regra: confirmar cada símbolo e assinatura na API reference **antes** de
escrever código. Exemplos públicos e respostas de LLM frequentemente descrevem
a API v0.

## Servidores MCP oficiais

Forma preferida de consultar documentação e referência canônica durante a
tarefa, sem depender da memória do modelo.

| Server | Endpoint | Transport | Conteúdo |
| --- | --- | --- | --- |
| `docs-langchain` | `https://docs.langchain.com/mcp` | http (streamable) | guias conceituais, tutoriais, how-tos |
| `reference-langchain` | `https://reference.langchain.com/mcp` | http (streamable) | referência de API: classes, métodos, parâmetros |

Configuração genérica (formato `mcpServers`, aceito por Claude Code via
`.mcp.json`, por Cursor e por Deep Agents em `~/.deepagents/.mcp.json`):

```json
{
  "mcpServers": {
    "docs-langchain":      { "type": "http", "url": "https://docs.langchain.com/mcp" },
    "reference-langchain": { "type": "http", "url": "https://reference.langchain.com/mcp" }
  }
}
```

Claude Code, via CLI:

```bash
claude mcp add --transport http docs-langchain https://docs.langchain.com/mcp
claude mcp add --transport http reference-langchain https://reference.langchain.com/mcp
```

Se este projeto tiver um `.mcp.json` versionado na raiz com esses dois
servers, o cliente pede aprovação na primeira utilização em cada máquina.

## Superfície v1 — checklist mínimo

- **Seleção de modelo**: `init_chat_model("<provider>:<modelo>", ...)`.
- **Mensagens**: `HumanMessage`, `AIMessage`, `SystemMessage`, `ToolMessage`
  de `langchain_core.messages`; conteúdo multimodal como content blocks.
- **Ferramentas**: decorador `@tool`; `model.bind_tools([...])`; a resposta
  traz `tool_calls`; retorno vai em `ToolMessage`.
- **Saída estruturada**: `model.with_structured_output(Schema)` com Pydantic
  ou `TypedDict`.
- **Streaming**: `.stream(...)` / `.astream(...)` com modo explícito
  (`values`, `updates`, `messages`, `custom`).
- **Prompts**: `ChatPromptTemplate.from_messages([...])`.
- **Composição linear**: `Runnable` / LCEL (`prompt | model | parser`) segue
  válido para pipelines simples sem estado nem ciclo.
- **Recuperação (RAG)**:
  - `VectorStore.as_retriever(search_kwargs={"k": ..., "filter": ...})`.
  - Embeddings via pacote dedicado do provider.
  - Text splitting via `langchain_text_splitters`
    (`RecursiveCharacterTextSplitter`, `MarkdownHeaderTextSplitter`).
  - `Document` de `langchain_core.documents`.

## Conferência mínima

- Comparar os imports do projeto com a API reference atual; anotar cada
  símbolo deprecado encontrado.
- Nunca introduzir import de `langchain_community.*` quando existir pacote de
  integração dedicado (ver `references/langgraph-v1.md` para a tabela).
- Rodar os testes Pytest ligados à mudança e o CLI afetado antes de declarar
  pronto.
