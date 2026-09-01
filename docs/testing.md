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
- Arquivos próprios: sete.
- Casos observados: 37 casos executados.

| Arquivo | Cobertura principal |
| --- | --- |
| `tests/test_loader.py` | hash de origem e falha rápida de documento inválido |
| `tests/test_chunker.py` | resumos, limiar mínimo e IDs determinísticos |
| `tests/test_manifest.py` | contagens e rejeição de IDs duplicados |
| `tests/test_qdrant_sync.py` | upsert antes da limpeza e preservação em falha |
| `tests/test_safety.py` | guardas de opção destrutiva, modo, escopo e remoção nos entrypoints |
| `tests/test_safety_policy.py` | contrato unitário de `SyncSafetyPolicy` |
| `tests/test_docs_safety.py` | material publicado sem caminho destrutivo |

Comando reproduzível: `uv run pytest`. Ruff é gate confirmado do projeto, mas
ainda não está instalado no ambiente atual; a lacuna pertence ao BACKLOG-0007.
