# Evidência: contrato de VectorStore do LangChain

## Metadados

- Origem: LangChain Python API Reference, consultada por Context7.
- URL: https://reference.langchain.com/python/langchain-core/vectorstores
- Acesso: 2026-09-01.
- Licença/cópia: nenhum conteúdo externo reproduzido; somente notas próprias.
- Finalidade: conferir suporte conceitual a IDs fornecidos pelo chamador e testes de conformidade de vector stores.

## Achados

### ids-fornecidos

- A referência de testes de integração de `VectorStore` verifica que `add_documents` preserva IDs fornecidos pelo argumento `ids` e que `delete(ids=[...])` remove os IDs indicados.
- Isso sustenta o uso de identidade explícita no adapter ChromaDB novo e a suíte de conformidade, sem obrigar o contrato do projeto a expor classes específicas do SDK.
- Conferência local em `langchain-chroma==1.1.0`: `add_texts` aceita `ids`, `get` aceita `where`, `limit` e `offset`, e `delete` aceita `ids`. A inspeção foi feita com `inspect.signature` no ambiente `.venv`, sem acesso remoto.

### integracoes-dedicadas

- A referência diferencia integrações legadas de `langchain_community` das integrações dedicadas.
- A migração de Qdrant e Hugging Face deve usar `langchain-qdrant` e `langchain-huggingface`, com símbolos e assinaturas reconfirmados durante a implementação.
- Versões locais observadas: `langchain==1.2.18`, `langchain-openai==1.2.1`, `langchain-chroma==1.1.0`, `langchain-pinecone==0.2.13` e `qdrant-client==1.10.1`.

### limite-da-consulta

- A consulta específica de `QdrantVectorStore` não retornou documentação suficiente no índice usado.
- A spec não fixa assinatura de construtor do pacote. A implementação deve confirmar a API instalada/canônica antes de escrever o adapter e preservar os contornos do `qdrant-client==1.10.1` observados no código atual.
