# Backlog: Elevar capacidade de sincronização de ChromaDB e Pinecone

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0009 |
| Status | Descartado — superado pela SPEC-0010 |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Arquitetura de providers |
| Tipo | Técnico |
| Prioridade | P3 — baixa |
| Milestones | M01 |
| Criado em | 2026-09-01 |
| Spec promovida | Nenhuma |

## Ideia original

Depois que BACKLOG-0003 entregar o contrato neutro de vector store, os adapters de ChromaDB e Pinecone, e a suíte de conformidade, elevar esses dois backends para a superfície completa do contrato: `mirror` idempotente com releitura de escopo lógico, remoção de obsoletos guardada pela `SyncSafetyPolicy` e log com as contagens estruturadas `previstos/inseridos/mantidos/removidos`.

## Problema percebido

Hoje só o Qdrant faz sincronização idempotente completa. ChromaDB opera em `append` não idempotente (reexecução acumula) e Pinecone em `append` com IDs estáveis, sem remover pontos obsoletos. BACKLOG-0003 preserva essas diferenças de propósito, declarando-as por capability flags, para não inflar o risco da modularização. Enquanto ChromaDB e Pinecone não subirem ao contrato completo, trocar o Qdrant por um deles significa perder a garantia de espelho.

## Pessoa afetada ou beneficiada

Mantenedores do componente e quem, no futuro, quiser operar ChromaDB ou Pinecone como banco principal em vez do Qdrant.

## Resultado ou valor esperado

Os três bancos suportados passam a oferecer a mesma superfície de sincronização; a escolha de backend deixa de ter impacto na semântica de espelho e auditoria.

## Contexto

- Depende do contrato, do adapter de referência in-memory e da suíte de conformidade entregues por BACKLOG-0003; não começa antes disso.
- Não bloqueia o objetivo declarado pela pessoa responsável ("começar com Qdrant e poder trocar facilmente depois"): esse objetivo é atendido pelo contrato neutro do 0003. Este item só fecha a lacuna de capacidade dos adapters que já existem.
- Prioridade baixa e possivelmente nunca priorizado: um backend novo (ex.: Postgres/pgvector) nasceria já completo contra o contrato, sem precisar deste trabalho.

## Referências relacionadas

- `specs/backlog/0003-modularizar-providers-factory-adapter.md` — entrega o contrato neutro, os capability flags, o adapter de referência in-memory e a suíte de conformidade sobre os quais este item se apoia. Tipo: pré-requisito.
- `src/safety.py` — `SyncSafetyPolicy`; `_MIRROR_PROVIDERS` precisaria incluir os backends elevados. Tipo: dependência de comportamento.
- `specs/completed/0001-bloquear-recriacao-destrutiva/spec.md` — garantias fail-closed que a elevação precisa preservar. Tipo: spec relacionada (precedente).
- `specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md` — épico pai M0. Tipo: backlog relacionado (pai).

## Comportamento esperado

A esclarecer no refinamento. Direção inicial: cada backend elevado implementa a extensão `MirrorCapableVectorStore` do contrato de BACKLOG-0003 (`list_ids(scope)` e `delete_ids(ids)` eficientes o suficiente para o `mirror` guardado), declara a capacidade `mirror`, e passa nas asserções da extensão na suíte de conformidade — as mesmas que hoje só Qdrant e o adapter de referência in-memory passam.

## Regras de negócio

- A esclarecer conforme risco e complexidade. A elevação não pode enfraquecer a `SyncSafetyPolicy` nem alterar `config.yaml`/metadados.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: preservar integralmente a política fail-closed da SPEC-0001 nos novos caminhos de remoção.
- Privacidade: sem mudança prevista.
- Desempenho e volume: a releitura de escopo em ChromaDB e Pinecone precisa ser avaliada (paginação, limites de filtro do Pinecone por plano).
- Auditoria e observabilidade: log com contagens estruturadas uniforme entre os três bancos.

## Dependências

- BACKLOG-0003 concluído (contrato, adapter de referência, suíte de conformidade).

## Situações de erro

- A esclarecer. Incluir o caso de um backend cujo filtro por escopo não seja confiável para autorizar remoção.

## Escopo

- Dentro: elevar os adapters ChromaDB e Pinecone à superfície completa do contrato; ajustar `SyncSafetyPolicy._MIRROR_PROVIDERS`; uniformizar o log de contagens.
- Fora: novos backends (ex.: adapter real de Postgres/pgvector); mudanças no contrato; qualquer coisa do projeto-mãe.

## Dúvidas, decisões e riscos

- Decisão herdada de BACKLOG-0003 (Pergunta 10): esta lacuna foi deliberadamente adiada para manter a modularização de baixo risco.
- **Supersessão parcial da SPEC-0001:** a SPEC-0001 (fora de escopo e NFR-003) encaminhou a "identidade estável / idempotência do ChromaDB" ao BACKLOG-0003. O BACKLOG-0003 cumpre a parte de identidade estável (upsert por `chunk_id`, sem duplicar) e o log de contagens uniforme. A semântica de espelho (`mirror` com releitura de escopo e remoção guardada de obsoletos) para os backends `append` foi realocada para este BACKLOG-0009. Registro explícito da mudança de roteamento.
- Risco: o delete por filtro de metadados do Pinecone tem limites por plano; a viabilidade do `mirror` guardado precisa ser confirmada.
- Risco: pode ser fechado como "não será feito" se nenhum uso real de ChromaDB/Pinecone como banco principal surgir.
- **Descartado em 2026-09-05:** a SPEC-0010 (2026-09-04) removeu as implementações concretas de ChromaDB e Pinecone do projeto (`chromadb`, `langchain-chroma`, `langchain-pinecone` e os adapters correspondentes), preservando apenas o contrato multi-provider aberto. Não existe mais adapter de ChromaDB ou Pinecone para elevar à superfície completa de `mirror`. Este item deixa de ser aplicável; um provider futuro nasceria diretamente contra o contrato do BACKLOG-0003, sem esta dívida.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Nenhum. Item descartado em 2026-09-05: a SPEC-0010 removeu ChromaDB e Pinecone
do projeto, então não há mais adapter para elevar. Reabrir só se um desses
bancos voltar a ser considerado como provider concreto no futuro.
