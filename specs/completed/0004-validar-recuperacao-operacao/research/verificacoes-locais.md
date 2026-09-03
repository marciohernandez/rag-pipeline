# Verificacoes locais da SPEC-0004

Notas de proveniencia das inspecoes feitas no proprio repositorio em 2026-09-01,
durante o refinamento do BACKLOG-0006 e a redacao desta spec. Nenhuma fonte
externa foi consultada nesta fatia; este arquivo registra apenas o que foi
observado localmente, com o comando usado e o resultado obtido.

## Contrato nucleo dos adapters

Comando: `grep -nE "def |class |Protocol" src/providers/contracts.py`

Resultado relevante, em `src/providers/contracts.py`:

- linha 103: `def list_ids(self, scope: LogicalScope) -> set[str]: ...`
- linha 107: `def query(self, scope, embedding, k)` no mesmo `VectorStoreAdapter`
- linha 118: `def delete_ids(...)` isolado em `MirrorCapableVectorStore`

Consequencia para a spec: a conferencia de identidade e o roteiro de consultas
usam apenas metodos do contrato nucleo, presentes em todos os backends, sem
depender da extensao destrutiva e sem importar SDK.

## Score nativo por provider

Comando: `grep -rn "score" src/providers/vectorstores/*.py`

Resultado: `SearchResult.score` e preenchido com o valor devolvido por cada
integracao — `similarity_search_by_vector_with_relevance_scores` em
`chroma.py:89`, `hit.score` em `qdrant.py:151` e `match["score"]` em
`pinecone.py:111`.

Consequencia para a spec: um limiar numerico unico nao e comparavel entre
backends. A DEC-008 declara o limiar por base, valido para o provider
configurado naquela base, e a secao 16 registra o limite conhecido.

## Volume observado na base ativa

Comando: leitura de `output/vivo_gold_banda_larga_pf/manifest.json`

Resultado: `chunk_count` 208, 7 documentos, `chunk_type_counts` com 191
`detail` e 17 `section_summary`, `excluded_by_status_count` zero.

Consequencia para a spec: `list_ids` sobre o escopo e barato no volume atual;
paginacao fica registrada como risco de escala futura, nao como requisito.

## Formato de consultas ja esbocado no projeto

Fonte local: `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md`, secao 13, linhas 383 a 401.

Resultado: o documento propoe perguntas de referencia por base em YAML, com as
chaves `pergunta`, `deve_conter` e `documento_esperado`.

Consequencia para a spec: a DEC-003 adota esse formato e acrescenta a categoria
declarada por consulta. O documento e roteiro historico do projeto, nao fonte
normativa.

## Estado do versionamento

Comando: `cat .gitignore` e `git ls-files documentos`

Resultado: `output/` esta ignorado; os cinco arquivos Markdown de
`documentos/vivo_gold_banda_larga_pf/` estao rastreados.

Consequencia para a spec: o gabarito ao lado dos documentos segue a pratica
atual e nao cria exposicao nova; o JSON de resultado em `output/` e historico
local, nao versionado.
