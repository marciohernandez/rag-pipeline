# Documentação técnica

<!-- specsfy:documentator:start -->
## Visão geral

- Frameworks detectados: não identificados.
- Arquivos de código: 271.
- Arquivos de teste: 10.

## Roteiro

- [Arquitetura](architecture.md)
- [Aplicação](application.md)
- [Banco de dados](database.md)
- [Testes](testing.md)
- [Pacotes](packages.md)
<!-- specsfy:documentator:end -->

## Complemento verificado para Python

O detector automático acima inventaria frameworks Node/Laravel e não reconhece
o código Python deste repositório. O mapeamento verificável do sistema está nas
seções complementares dos documentos abaixo.

- Runtime: Python 3.12+, ambiente gerenciado por `uv`.
- Aplicação: 10 módulos em `src/pipeline/` e 16 arquivos em `src/pipeline/providers/`, que
  concentram os contratos neutros, a factory e os adapters.
- Interface operacional: oito CLIs na raiz — `pipeline.py`, `validate.py`,
  `search.py`, `chat.py`, `upsert_from_chunks.py`, `inspect_chunks.py`,
  `demo_rag.py` e `main.py`. A pasta `scripts/` não existe mais: os protótipos
  de diagnóstico foram substituídos por `validate.py` na SPEC-0004.
- Testes próprios: 17 arquivos em `tests/`, 180 casos executados com Pytest,
  nenhum exigindo rede.
- Stack principal: LangChain, Qdrant (único provider concreto de vector store)
  e providers de embeddings OpenAI, OpenRouter e Hugging Face. A abstração
  multi-provider permanece aberta para novos destinos.
- Não existe frontend, API web ou autenticação neste componente.

Leia também [Fluxos](flows.md), [Integrações](integrations.md) e
[Decisões](decisions.md).
