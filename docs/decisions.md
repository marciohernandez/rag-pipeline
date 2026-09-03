# Decisões técnicas

<!-- specsfy:documentator:start -->
## Política

Decisões explícitas em `PROJECT.md` e `.specsfy/` prevalecem sobre inferências deste documento.
<!-- specsfy:documentator:end -->

## Decisões explícitas vigentes

- Finalizar este componente antes de montar o projeto-mãe `rag-pipeline`.
- Usar Specsfy como fonte normativa e Linear apenas para tracking.
- Trabalhar em uma branch própria por fase, nunca diretamente na principal.
- Manter Qdrant como destino principal e ChromaDB/Pinecone como alternativas
  atualmente expostas.
- Preservar identidades determinísticas, manifesto e sincronização idempotente.
- Não antecipar neste componente a ingestão multi-formato, curadoria,
  autenticação, dashboard ou demais capacidades V1 do projeto-mãe.
- Tratar operações remotas destrutivas fora do fluxo normal. A SPEC-0001 está
  concluída: `--recreate` é rejeitado com orientação de recuperação idempotente
  e as guardas de modo, escopo e remoção vivem em `src/pipeline/safety.py`.
- Manter o modo espelho restrito ao Qdrant; ChromaDB e Pinecone operam apenas
  em modo append, por não comprovarem a garantia de escopo exigida.
- SPEC-0002 concluída: `document_id`, `tenant_id`, `status`, `type` e `version`
  do frontmatter do projeto-mãe passam a ser respeitados. `document_id`
  recebido tem precedência sobre a identidade determinística; `tenant_id`
  estende o escopo lógico fail-closed quando declarado; `status` bloqueia
  indexação por lista configurável (vazia por padrão); `type`/`version` são
  metadado auditável sem efeito de processamento.
- Separador de blocos Q&A é `++++`, não `---`, para eliminar a colisão com o
  delimitador de frontmatter YAML.
- SPEC-0003 concluída: providers viraram plugins atrás de contratos neutros.
  `src/pipeline/providers/` concentra contratos, factory e adapters, e é o único lugar do
  repositório onde SDK de banco vetorial ou classe de embeddings pode ser
  importado; `ChatOpenAI` em `chat.py` é a única exceção temporária, rastreada
  pelo BACKLOG-0010. A regra é verificada por teste estático de AST em
  `tests/test_provider_boundaries.py`. `src/pipeline/embedder.py` foi removido sem shim.
- DEC-011: o acesso ao Qdrant permanece pelo SDK `qdrant-client==1.10.1`, e não
  por `langchain-qdrant`. A assinatura de `QdrantVectorStore` não foi comprovada
  para essa versão (R-002), e a API que o pipeline já usava em produção é a
  única confirmada. `langchain-qdrant` chegou a ser instalado e foi removido por
  não ter uso.
- SPEC-0004 concluída: a validação de recuperação é somente leitura e vive em
  `src/pipeline/validation.py`, com `validate.py` apenas como camada de linha de comando.
  O módulo é chamável sem a CLI e devolve resultado equivalente, para que o
  backend do BACKLOG-0008 consuma o mesmo caso de uso.
- O preflight da validação usa `describe_scope`, operação de leitura
  acrescentada ao contrato neutro, e nunca `ensure_ready`: naquele caminho o
  adapter Qdrant cria a coleção ausente, o que faria um escopo inexistente ser
  aprovado como base vazia.
- O veredito da validação distingue três desfechos, e não dois: `0` aprova, `1`
  reprova depois de validar e `2` declara que não foi possível validar.
  Ambiente indisponível não é tratado como base divergente.
- O gabarito de consultas é versionado junto da base, em
  `caminhos.consultas_referencia`, e não embutido no código. Os protótipos
  `scripts/check_qdrant_connection.py` e `scripts/check_qdrant_search.py`, que
  falavam REST cru e carregavam nome de cliente e pergunta de negócio fixos,
  foram removidos.
