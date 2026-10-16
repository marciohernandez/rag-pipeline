# Contratos multimodais e execução da IA

Consultado em 2026-10-15; evidência informativa da SPEC-0036, DEC-007.

- Referência LangChain, testes oficiais multimodais: https://reference.langchain.com/python/langchain-tests/integration_tests/chat_models/ChatModelIntegrationTests — blocos `text` e `image_url` com data URI base64 são aceitos pelo contrato de mensagens da integração OpenAI. Conteúdo de imagem permanece em memória; nenhuma URL externa de imagem é entregue ao modelo.
- LangGraph v1, Graph API: https://docs.langchain.com/oss/python/langgraph/graph-api — StateGraph com estado tipado, nós e edges explícitos, compilado antes de invoke. O fluxo de reprocessamento é finito e sem ferramentas de escrita; não utiliza checkpointer nem tracing externo, pois não há conversa ou retomada.
- Dependências locais: langchain-core e langgraph resolvidos em uv.lock. Renderer PDF/imagens: PyMuPDF. Documentos Office: LibreOffice já presente na imagem deploy/backend/Dockerfile; ausência local causa falha segura e preserva o Markdown anterior.

Nenhuma chamada a provedor pago foi executada durante os testes.
