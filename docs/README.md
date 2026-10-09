# Documentação técnica

<!-- specsfy:documentator:start -->
## Visão geral

- Frameworks detectados: não identificados.
- Arquivos de código: 833.
- Arquivos de teste: 43.

## Roteiro

- [Arquitetura](architecture.md)
- [Aplicação](application.md)
- [Banco de dados](database.md)
- [Testes](testing.md)
- [Pacotes](packages.md)
<!-- specsfy:documentator:end -->

## Complemento verificado do projeto

O detector automático acima não identifica os frameworks deste repositório
porque o backend Python e o projeto Node autocontido em `frontend/` não estão
no alcance do seu reconhecimento de manifests. As seções complementares dos
documentos detalham o que o código comprova:

- Pipeline e CLIs: Python 3.12+ com `uv`, LangChain, Qdrant e providers de
  embeddings OpenAI, OpenRouter e Hugging Face; a abstração de vector store
  permanece aberta a outros destinos.
- Aplicação web: FastAPI em `src/app/`, PostgreSQL para Workspaces, Bases,
  Execuções e Consultas, Procrastinate para processamento assíncrono e
  autenticação por token estático de demonstração.
- Interface: Next.js/React em `frontend/`, com jornada Login → Workspaces →
  Bases → detalhe/consulta; `/projeto` permanece como redirect de
  compatibilidade.
- Testes: Pytest em `tests/` e Vitest/Testing Library em `frontend/src/`.
  Os números de casos devem vir da execução de cada suíte, não deste texto.

Leia também [Frontend](frontend.md), [Fluxos](flows.md),
[Integrações](integrations.md) e [Decisões](decisions.md).
