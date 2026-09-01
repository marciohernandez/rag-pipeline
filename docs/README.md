# Documentação técnica

<!-- specsfy:documentator:start -->
## Visão geral

- Frameworks detectados: não identificados.
- Arquivos de código: 0.
- Arquivos de teste: 0.

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

- Runtime: Python 3.12+.
- Aplicação: oito módulos em `src/` e seis CLIs/scripts na raiz ou em `scripts/`.
- Testes próprios: quatro arquivos em `tests/`, executados com Pytest.
- Stack principal: LangChain, Qdrant, ChromaDB, Pinecone e providers de embeddings.
- Não existe frontend, API web ou autenticação neste componente.

Leia também [Fluxos](flows.md), [Integrações](integrations.md) e
[Decisões](decisions.md).
