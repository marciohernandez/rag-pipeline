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
- Tratar operações remotas destrutivas fora do fluxo normal; o trabalho para
  bloquear `--recreate` está refinado no BACKLOG-0001.
