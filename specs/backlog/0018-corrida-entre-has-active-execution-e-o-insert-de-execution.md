# Backlog: Corrida entre has_active_execution e o insert de Execution

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0018 |
| Status | Promoted |
| Produto | rag-pipeline — backend de aplicação (SPEC-0012) |
| Épico | Confiabilidade e integridade de dados |
| Funcionalidade | Controle de execuções por base |
| Tipo | Técnico (correção de bug de concorrência) |
| Prioridade | Alta |
| Milestones | |
| Criado em | 2026-09-15 |
| Spec promovida | `specs/draft/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md` (SPEC-0015) em 2026-09-15 |

## Ideia original

iniciar_execucao/repetir_execucao fazem has_active_execution e o insert da nova Execution sem lock nem constraint no banco ((base_id, situacao) sem índice único) — duas requisições concorrentes podem passar pelo check antes de qualquer commit e criar duas execuções ativas para a mesma base, violando FR-009 sob concorrência real (dois agentes independentes do /code-review encontraram o mesmo problema). test_impede_execucao_concorrente só testa chamadas sequenciais, não concorrência real.

## Problema percebido

Duas requisições concorrentes podem passar pelo check has_active_execution antes de qualquer commit e criar duas execuções ativas simultâneas para a mesma base, violando FR-009 (SPEC-0012) sob concorrência real.

## Pessoa afetada ou beneficiada

Qualquer chamador de `iniciar_execucao`/`repetir_execucao` — pessoa usuária no
frontend de demonstração (SPEC-0013, duplo clique ou duas abas) ou integração
que chame a API diretamente. Decisão confirmada em 2026-09-15: a correção não
assume uma origem específica; cobre qualquer chamador, pois vive no nível
comum de `has_active_execution`/insert em `src/app/repo.py`.

## Resultado ou valor esperado

Nunca existem duas execuções ativas (`pending`/`running`) simultâneas para a
mesma base, garantido pelo banco (índice único parcial), não apenas por um
check otimista na aplicação. Decisão confirmada em 2026-09-15.

## Situações de erro

- Violação do índice único parcial durante o insert (corrida real) é
  capturada e convertida em HTTP 409 com `id`/`situacao` da execução ativa —
  não deve vazar como erro 500 de integridade do banco.
- Inferência (a confirmar na especificação): o teste automatizado precisa
  provar concorrência real (duas conexões/threads/sessões distintas
  disputando o mesmo insert), não apenas chamadas sequenciais — o texto
  original já registra que `test_impede_execucao_concorrente` cobre somente
  o caso sequencial.

## Contexto

Achado registrado em specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md, seção 16, como 'Não corrigido, registrado para spec/backlog futuro'; citado em specs/milestones/M02.md como item de dívida técnica sem milestone atribuída.

## Referências relacionadas

- `specs/inbox/2026-09-15-133804-corrida-entre-has-active-execution-e-o-insert-de-execution.md` — captura de origem (proveniência).
- `specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md:1232` — spec relacionada: achado original "Não corrigido, registrado para spec/backlog futuro" (FR-009).
- `specs/milestones/M02.md` — documentação relacionada: item listado em "Fora de escopo" como dívida técnica sem milestone.
- `src/app/repo.py:49-53` (`has_active_execution`) e `src/app/models.py` (`Execution`, sem `UniqueConstraint`/`Index` em `(base_id, situacao)`) — código relacionado, confirma a ausência de lock/constraint.
- `src/app/routers/executions.py` — consumidor de `has_active_execution` em `iniciar_execucao`/`repetir_execucao`.

## Comportamento esperado

Quando duas requisições concorrentes tentam iniciar (ou repetir) execução para
a mesma base, o sistema garante atomicamente que apenas uma seja aceita; a
segunda é rejeitada com erro de conflito (409). Decisão confirmada em
2026-09-15: mantém o invariante "uma execução ativa por base" já pretendido
por FR-009 (SPEC-0012), agora garantido de forma atômica (constraint/lock no
banco) em vez do check otimista atual em `has_active_execution`.

## Regras de negócio

- A esclarecer conforme risco e complexidade.

## Critérios de aceitação

- Dado que uma base já tem uma execução em `pending` ou `running`, quando uma
  segunda requisição concorrente tenta iniciar ou repetir execução para a
  mesma base, então o sistema rejeita a segunda com HTTP 409, informando `id`
  e `situacao` da execução já ativa no corpo do erro. Decisão confirmada em
  2026-09-15.
- A esclarecer critérios adicionais (situações de erro, teste de concorrência
  real) nas próximas rodadas.

## Qualidades e operação

- Segurança: sem exposição nova — o 409 devolve apenas `id`/`situacao` da
  execução, dados já acessíveis a quem tem permissão sobre a base.
- Privacidade: não aplicável; nenhum dado pessoal envolvido.
- Desempenho e volume: overhead desprezível (um índice parcial pequeno; volume
  de execuções por base é baixo, ambiente de demonstração).
- Auditoria e observabilidade: não avaliado como requisito — a esclarecer se
  necessário durante a especificação.

## Dependências

- Migration Alembic (`alembic/versions/`) no banco de teste
  (`rag_pipeline_test`), seguindo a regra local de `.specsfy/RULES.md` sobre
  tarefas `[CODE]` de schema (não usar a tag `[MIGRATION]`).
- Nenhuma dependência bloqueante de outra spec ou backlog.

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: índice único parcial em `Execution` (`base_id`, filtrado por
  `situacao IN ('pending','running')`), migration Alembic correspondente,
  conversão da violação de integridade em HTTP 409 com `id`/`situacao` da
  execução ativa em `iniciar_execucao` e `repetir_execucao`
  (`src/app/routers/executions.py`), e teste de concorrência real (duas
  sessões/conexões distintas disputando o mesmo insert) substituindo ou
  complementando `test_impede_execucao_concorrente`.
- Fora: qualquer mudança no frontend (SPEC-0013) — decisão confirmada em
  2026-09-15, catch genérico existente é suficiente; fila de execuções
  (opção 2 rejeitada na Pergunta 1); lock distribuído externo (opção 3
  rejeitada na Pergunta 4); BACKLOG-0019 (compensação em `apagar_base`), que é
  item separado.

## Dúvidas, decisões e riscos

- Decisão (2026-09-15): rejeitar a segunda requisição concorrente com 409,
  mantendo o invariante de FR-009 (SPEC-0012), em vez de enfileirar ou
  permitir-e-cancelar.
- Decisão (2026-09-15): a correção não assume uma origem específica de
  requisição (frontend ou API direta); cobre qualquer chamador de
  `iniciar_execucao`/`repetir_execucao`.
- Decisão (2026-09-15): o corpo do 409 informa `id` e `situacao` da execução
  já ativa.
- Decisão (2026-09-15): mecanismo é índice único parcial no banco
  (`(base_id)` filtrado por `situacao IN ('pending','running')`), não lock de
  aplicação nem lock distribuído externo.
- Decisão (2026-09-15): prioridade Alta — bug de integridade de dados real,
  já encontrado por dois agentes independentes de `/code-review`.
- Decisão (2026-09-15): sem mudança de frontend; o catch genérico de
  `PainelProgresso.tsx` já é suficiente para o cenário raro (duas abas/duplo
  clique).
- Risco herdado do texto original: `test_impede_execucao_concorrente` só
  cobre chamadas sequenciais; a especificação precisa derivar um teste de
  concorrência real (duas sessões/conexões distintas) para provar a correção.
- Decisão (2026-09-15): spec separada do BACKLOG-0019 (falta de compensação em
  `apagar_base`), apesar de descoberta junto e no mesmo módulo `src/app` —
  correções independentes, uma exige migration e a outra não.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Pronto para `$specsfy-03-specify`.
