# Integrações

<!-- specsfy:documentator:start -->
## Configuração

Valores de ambiente e integrações são documentados apenas pelos nomes declarados localmente, sem segredos.
<!-- specsfy:documentator:end -->

## Integrações verificadas

| Integração | Uso | Configuração sem valores |
| --- | --- | --- |
| OpenAI | embeddings | `OPENAI_API_KEY` e parâmetros em `config.yaml` |
| OpenRouter | embeddings e demonstração de chat | `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `LLM_MODEL` |
| Hugging Face | embeddings locais | modelo e device em `config.yaml` |
| Qdrant | destino vetorial principal e busca | `QDRANT_URL`, `QDRANT_API_KEY`, collection em `config.yaml` |
| ChromaDB | destino vetorial local alternativo | diretório e collection em `config.yaml` |
| Pinecone | destino vetorial remoto alternativo | `PINECONE_API_KEY`, `PINECONE_INDEX` e namespace configurado |

Credenciais são lidas do ambiente e não devem ser versionadas. Os nomes acima
são o contrato de configuração; nenhum valor sensível é publicado aqui.
