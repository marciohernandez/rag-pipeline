# Testes

<!-- specsfy:documentator:start -->
## Resumo

- Arquivos de teste: 0.
- Runner: não identificado.
- Scripts: não declarados.

| Arquivo |
| --- |
| Nenhum teste identificado |
<!-- specsfy:documentator:end -->

## Testes Python verificados

- Runner: Pytest, grupo `dev` de `pyproject.toml`.
- Arquivos próprios: 17.
- Casos observados: 180 casos executados, 180 aprovados.

| Arquivo | Casos | Cobertura principal |
| --- | --- | --- |
| `tests/test_vectorstore_conformance.py` | 26 | núcleo do contrato de vector store (`ensure_ready`, `list_ids`, `upsert`, `query`) em todos os adapters, com extensão `mirror` restrita a Qdrant e in-memory |
| `tests/test_safety.py` | 23 | guardas de opção destrutiva, modo, escopo e remoção nos entrypoints |
| `tests/test_provider_factory.py` | 17 | criação de cada provider pela mesma factory e erro local antes de qualquer cliente remoto |
| `tests/test_describe_scope_conformance.py` | 16 | `describe_scope` nos quatro backends, incluindo escopo ausente e dimensão declarada |
| `tests/test_validation.py` | 15 | validação de recuperação: preflight, conferência de identidade, roteiro de consultas, relatório, JSON e desfechos |
| `tests/test_safety_policy.py` | 14 | contrato unitário de `SyncSafetyPolicy` |
| `tests/test_chunker.py` | 14 | resumos de seção, limiar mínimo e IDs determinísticos |
| `tests/test_characterization_providers.py` | 13 | comportamento observável da camada de providers, congelado durante o corte de `src/embedder.py` |
| `tests/test_qdrant_sync.py` | 12 | upsert antes da limpeza e preservação dos dados remotos em falha |
| `tests/test_describe_scope_backends.py` | 6 | caracterização de `describe` nos backends reais, com SDK substituído por dublê e sem rede |
| `tests/test_status_gate.py` | 5 | bloqueio de indexação por status configurável |
| `tests/test_docs_safety.py` | 5 | material operacional publicado sem caminho destrutivo |
| `tests/test_provider_boundaries.py` | 4 | fronteira estática de imports: SDK de vector store e classes de embeddings somente em `src/providers/` |
| `tests/test_loader.py` | 3 | hash de origem e falha rápida de documento inválido |
| `tests/test_embedding_conformance.py` | 3 | determinismo e dimensão do adapter fake de embeddings |
| `tests/test_validation_boundaries.py` | 2 | ausência dos protótipos de diagnóstico e de SDK de provider no código de validação |
| `tests/test_manifest.py` | 2 | contagens e rejeição de IDs duplicados |

`tests/_fakes_vectorstore.py` não é arquivo de casos: reúne os dublês
compartilhados pelas suítes de conformidade.

Nenhuma suíte exige rede. Destinos remotos e SDKs são substituídos por dublês
observáveis, o que permite provar garantias de somente leitura sem tocar em
Qdrant, ChromaDB, Pinecone ou provedores de embeddings.

Comando reproduzível: `uv run pytest`. Ruff é gate confirmado do projeto, mas
ainda não está instalado no ambiente atual; a lacuna pertence ao BACKLOG-0007.
