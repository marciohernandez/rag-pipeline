# Especificação integrada: Corrida entre has_active_execution e o insert de Execution

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0015 |
| Slug | 0015-corrida-entre-has-active-execution-e-o-insert-de-execution |
| Status | Defined |
| Effort | 4 |
| Effort updated at | 2026-09-15 |
| Effort rationale | Correção localizada em `src/app/` (repo, router, models) com uma migration Alembic simples (índice único parcial) e conversão de erro de integridade em HTTP 409; a parte não trivial é o teste de concorrência real (duas sessões Postgres distintas disputando o mesmo insert), não o código de produção. Perfil `standard`. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Pending |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-15 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

`iniciar_execucao` e `repetir_execucao` (`src/app/routers/executions.py`)
verificam `repo.has_active_execution` e só então inserem a nova `Execution`,
sem lock nem constraint no banco. A tabela `executions` não tem
`UniqueConstraint`/`Index` em `(base_id, situacao)`. Duas requisições
concorrentes podem passar pelo check antes de qualquer commit e criar duas
execuções ativas (`pending`/`running`) para a mesma base ao mesmo tempo,
violando o invariante de execução única por base que a SPEC-0012 (seção 7)
já pretendia garantir. O teste
existente, `test_impede_execucao_concorrente`, só cobre chamadas sequenciais
(uma execução já commitada antes da segunda chamada), não concorrência real.
Duas execuções ativas simultâneas disparam duas tarefas em segundo plano
(`process_base_task`) escrevendo/apagando o mesmo escopo lógico do vector
store ao mesmo tempo, além de duplicar custo de embeddings e chamadas ao
Qdrant.

#### Resultado desejado

Nunca existem duas execuções ativas (`pending`/`running`) simultâneas para a
mesma base, garantido atomicamente pelo banco — não apenas por um check
otimista na aplicação. Quando uma segunda requisição concorrente perde a
corrida, ela recebe HTTP 409 com o `id` e a `situacao` da execução que já
está ativa.

#### Métricas de sucesso

- Um teste que dispara duas inserções de `Execution` para a mesma base em
  sessões/transações Postgres distintas, sem que uma veja o commit da outra,
  produz exatamente uma execução ativa e uma rejeição HTTP 409.
- 0 execuções duplicadas ativas (`pending`/`running`) para a mesma base, sob
  inspeção do banco, em qualquer sequência de chamadas a `iniciar_execucao`
  e `repetir_execucao`, concorrentes ou não.

### 2. Research e esclarecimentos

#### Researchs executados

- Nenhuma claim técnica externa. Este research confirmou comportamento do
  código local (não de uma API externa): `LocalDirectoryStorage.delete_base`,
  `S3CompatibleStorage.delete_base` e `service.delete_scope` não são objeto
  desta spec (ver BACKLOG-0019, spec irmã); aqui a leitura de código
  confirmou apenas a ausência de `UniqueConstraint`/`Index` em
  `src/app/models.py::Execution` e o fluxo de `has_active_execution` em
  `src/app/repo.py:49-53`.

#### Fontes e contexto consultados

- `specs/backlog/0018-corrida-entre-has-active-execution-e-o-insert-de-execution.md`: brief de origem, com todas as decisões da Pergunta 1 à Pergunta 5 já confirmadas pelo usuário.
- `specs/inbox/2026-09-15-133804-corrida-entre-has-active-execution-e-o-insert-de-execution.md`: captura original, preservando a redação da SPEC-0012 seção 16.
- `specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md:1232`: achado original, "Não corrigido, registrado para spec/backlog futuro" (requisito de execução única por base, seção 7), incluindo a nota de que dois agentes independentes de `/code-review` encontraram o mesmo problema.
- `specs/milestones/M02.md`: item listado em "Fora de escopo" como dívida técnica sem milestone.
- Código atual: `src/app/repo.py` (`has_active_execution`), `src/app/routers/executions.py` (`iniciar_execucao`, `repetir_execucao`), `src/app/models.py` (`Execution`, sem constraint), `alembic/versions/` (duas migrations existentes, convenção de nomes e docstrings), `tests/test_app_executions.py::test_impede_execucao_concorrente` (teste sequencial existente), `tests/conftest.py` (banco de teste real `rag_pipeline_test` em `postgresql+psycopg://...:55432`).
- `.specsfy/RULES.md`: regra local sobre tarefas `[CODE]` de migration (não usar a tag `[MIGRATION]`) e proteção do banco de desenvolvimento (testes usam `rag_pipeline_test`, nunca o banco de desenvolvimento).

#### Documentação consultada

- Nenhuma documentação externa consultada.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Rejeitar a segunda requisição concorrente, enfileirar, ou permitir e cancelar depois? → **A**: Rejeitar com HTTP 409, mantendo o invariante de execução única por base já registrado na SPEC-0012 (seção 7) — decidido no refinamento do BACKLOG-0018, Pergunta 1.
- **Q**: A correção deve assumir uma origem específica da requisição (frontend ou API direta)? → **A**: Não; cobre qualquer chamador de `iniciar_execucao`/`repetir_execucao` — Pergunta 2.
- **Q**: O corpo do 409 deve informar qual execução já está ativa? → **A**: Sim, `id` e `situacao` — Pergunta 3.
- **Q**: Qual mecanismo garante a atomicidade — índice único no banco, lock de aplicação (`SELECT ... FOR UPDATE`) ou lock distribuído externo? → **A**: Índice único parcial no banco, porque garante o invariante independente de quantos processos da aplicação (incluindo workers `procrastinate`) tentem inserir ao mesmo tempo — Pergunta 4.
- **Q**: Qual a prioridade? → **A**: Alta — bug de integridade de dados real, já encontrado por dois agentes independentes de `/code-review` — Pergunta 5.
- **Q**: O frontend (SPEC-0013) precisa de tratamento específico para o novo 409? → **A**: Não; o catch genérico de `PainelProgresso.tsx` já é suficiente para esse cenário raro (duas abas/duplo clique) — Pergunta 6.
- **Q**: BACKLOG-0018 e BACKLOG-0019 (compensação em `apagar_base`) viram uma spec só ou duas? → **A**: Duas specs separadas — uma exige migration, a outra não; decisão confirmada no refinamento cruzado dos dois backlogs.

#### Dúvidas abertas

- Nenhuma bloqueante para a definição.

### 3. Escopo e atores

#### Incluído

- Migration Alembic adicionando índice único parcial em `executions` sobre
  `base_id`, filtrado por `situacao IN ('pending', 'running')`.
- Conversão da violação de integridade em HTTP 409 (com `id`/`situacao` da
  execução ativa no corpo) em `iniciar_execucao` e `repetir_execucao`.
- Teste de concorrência real (duas sessões Postgres distintas disputando o
  mesmo insert), substituindo/complementando `test_impede_execucao_concorrente`.

#### Fora de escopo

- Qualquer mudança no frontend (SPEC-0013) — decisão confirmada; o catch
  genérico existente já é suficiente.
- Fila de execuções em vez de rejeição imediata — decisão confirmada.
- Lock distribuído externo (ex.: Redis) — decisão confirmada.
- BACKLOG-0019 (falta de compensação em `apagar_base` para falha parcial) —
  spec irmã separada.
- Qualquer mudança em `src/pipeline/` ou na lógica de processamento da
  tarefa (`process_base_task`).

#### Atores

- **Pessoa operadora** (owner/admin, via frontend SPEC-0013): dispara
  "iniciar execução" ou "repetir execução"; pode fazê-lo duas vezes quase ao
  mesmo tempo (duplo clique, duas abas).
- **Integração técnica**: chama a API diretamente (`POST
  /bases/{id}/executions`, `POST /executions/{id}/retry`), sem passar pelo
  frontend; sujeita ao mesmo invariante.

### 4. Princípios e restrições do projeto

- **PR-001**: `src/app/` importa somente `src/pipeline/service.py`; esta
  correção não toca `src/pipeline/` (SPEC-0008, `tests/test_application_boundaries.py`).
- **PR-002**: migration segue a regra local de `.specsfy/RULES.md`: tarefa
  `[CODE]` apontando para `alembic/versions/<revisao>_<slug>.py`, nunca a
  tag `[MIGRATION]` (não suportada por `validate_tasks.mjs`).
- **PR-003**: testes executam exclusivamente contra o banco de teste
  `rag_pipeline_test` (`tests/conftest.py`); nenhum teste desta spec usa o
  banco de desenvolvimento (`.specsfy/RULES.md`, proteção do banco).
- **PR-004**: nenhum segredo é exposto em resposta HTTP ou log (SPEC-0012,
  PR-003); o corpo do 409 expõe apenas `id`/`situacao` da execução, dados já
  acessíveis a quem tem permissão sobre a base.

### 5. Histórias de usuário

#### US-001 — Nunca ter duas execuções ativas concorrentes na mesma base (P1)

Como pessoa operadora ou integração técnica, quero que o sistema impeça
atomicamente duas execuções ativas simultâneas para a mesma base, mesmo sob
chamadas concorrentes, para que o estado da base nunca fique inconsistente e
eu saiba exatamente qual execução já está em andamento quando minha
requisição for rejeitada.

**Por que P1**: é uma correção de bug de integridade de dados real, já
encontrado por dois agentes independentes de `/code-review` (SPEC-0012,
seção 16); duas execuções ativas simultâneas corrompem o escopo lógico do
vector store e duplicam custo de embeddings.
**Teste independente**: abrir duas sessões Postgres reais, fazer as duas
passarem pelo check de `has_active_execution` sem ver o commit uma da outra,
inserir em ambas e commitar em sequência — a segunda deve falhar por
violação de integridade e ser convertida em 409 com o `id`/`situacao` da
primeira.
**Requisitos**: FR-001, FR-002, FR-003

### 6. Cenários BDD de aceite

#### AC-001 — Corrida real entre duas chamadas iniciar_execucao

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-001 @AC-001
Feature: Impedir execuções ativas concorrentes na mesma base

  Scenario: Duas chamadas iniciar_execucao disputam o mesmo insert
    Given uma base sem execução ativa
    And duas sessões Postgres distintas, ambas simulando iniciar_execucao,
      checam has_active_execution e não veem execução ativa nenhuma, porque
      nenhuma commitou ainda
    When as duas sessões inserem uma nova Execution para a mesma base e
      commitam em sequência
    Then a primeira commit é aceita e cria a execução em situação "pending"
    And a segunda commit falha por violação do índice único parcial
    And a requisição da segunda sessão recebe HTTP 409 com "id" e "situacao"
      da execução criada pela primeira no corpo da resposta
```

#### AC-002 — Corrida real entre iniciar_execucao e repetir_execucao

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-001 @AC-002
Feature: Impedir execuções ativas concorrentes na mesma base

  Scenario: iniciar_execucao e repetir_execucao concorrem pela mesma base
    Given uma base com uma execução em situação "failed"
    And duas sessões Postgres distintas — uma simulando iniciar_execucao,
      outra simulando repetir_execucao para a execução falhada da mesma base
      — checam has_active_execution e não veem execução ativa nenhuma
    When as duas sessões inserem uma nova Execution para a mesma base e
      commitam em sequência
    Then apenas a primeira commit é aceita
    And a segunda recebe HTTP 409 com "id" e "situacao" da execução ativa
      criada pela primeira, independentemente de qual endpoint chamou
      primeiro
```

#### AC-003 — Corrida real entre duas chamadas repetir_execucao

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-001 @AC-003
Feature: Impedir execuções ativas concorrentes na mesma base

  Scenario: Duas chamadas repetir_execucao disputam o mesmo insert
    Given uma base com duas execuções em situação "failed"
    And duas sessões Postgres distintas, cada uma simulando repetir_execucao
      para uma das execuções falhadas da mesma base, checam
      has_active_execution e não veem execução ativa nenhuma
    When as duas sessões inserem uma nova Execution para a mesma base e
      commitam em sequência
    Then apenas a primeira commit é aceita
    And a segunda recebe HTTP 409 com "id" e "situacao" da execução ativa
      criada pela primeira
```

#### AC-004 — Chamada sequencial contra execução já ativa continua rejeitada imediatamente (regressão)

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-004
Feature: Impedir execuções ativas concorrentes na mesma base

  Scenario: Chamada sequencial contra base com execução já commitada
    Given uma base com uma execução em situação "running" já commitada
    When iniciar_execucao é chamado para a mesma base
    Then o sistema responde HTTP 409 com "id" e "situacao" da execução
      "running", sem tentar inserir uma nova Execution
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve impedir, de forma atômica garantida pelo banco
  (não apenas por um check otimista na aplicação), a existência de mais de
  uma `Execution` em situação `pending` ou `running` para a mesma `base_id`,
  mesmo sob chamadas concorrentes a `iniciar_execucao` e `repetir_execucao`.
- **FR-002**: Quando uma requisição violar esse invariante (perder a
  corrida ou encontrar execução já ativa), o sistema deve responder HTTP 409
  com um corpo contendo `id` e `situacao` da execução já ativa.
- **FR-003**: O invariante e o tratamento de erro do FR-001/FR-002 devem
  valer identicamente para `iniciar_execucao` e `repetir_execucao` — o
  mecanismo vive no nível comum de `has_active_execution`/insert, não em
  cada endpoint separadamente.

#### Não funcionais

- **NFR-001**: Atomicidade sob concorrência real. **Verificação**: teste
  automatizado com duas sessões/transações Postgres distintas contra
  `rag_pipeline_test`, nenhuma vendo o commit da outra antes de inserir
  (AC-001, AC-002, AC-003).

#### Erros e casos-limite

- Duas requisições concorrentes tentam iniciar execução para a mesma base →
  a segunda recebe 409 com `id`/`situacao` da execução ativa (AC-001).
- Uma requisição de repetição concorre com uma de início, ou com outra
  repetição, para a mesma base → mesmo tratamento, independentemente de qual
  endpoint (AC-002, AC-003).
- Uma segunda requisição sequencial encontra execução já commitada → 409
  imediato, sem tentar inserir (AC-004, comportamento já existente
  preservado, verificado por `test_impede_execucao_concorrente` original).
- Violação do índice único parcial por qualquer inserção de `Execution` fora
  dos dois endpoints cobertos (ex.: script direto, migration de dados) não é
  tratada por esta spec — os dois endpoints de `src/app/routers/executions.py`
  são os únicos pontos de inserção de `Execution` no sistema hoje.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

FastAPI + SQLAlchemy + PostgreSQL (`src/app/`), migrations via Alembic
(`alembic/versions/`, duas migrations existentes desde SPEC-0012/SPEC-0013).
`src/app/repo.py` concentra leituras com isolamento por tenant/projeto;
`src/app/routers/executions.py` expõe `iniciar_execucao` e
`repetir_execucao`, ambos chamando `repo.has_active_execution` antes de
inserir. Testes de API usam `tests/conftest.py`, que aponta para o banco
real `rag_pipeline_test` (Postgres em `localhost:55432`) — não SQLite nem
mock —, o que permite um teste de concorrência real com duas sessões.

#### Arquitetura e módulos

- `src/app/models.py`: `Execution` ganha um índice único parcial
  (`Index(..., unique=True, postgresql_where=...)`) sobre `base_id`, restrito
  a `situacao IN ('pending', 'running')`.
- `src/app/repo.py`: nenhuma mudança de assinatura; `has_active_execution`
  continua como check otimista (evita uma tentativa de insert desnecessária
  no caminho feliz sequencial, AC-003), mas deixa de ser a única garantia.
- `src/app/routers/executions.py`: `iniciar_execucao` e `repetir_execucao`
  capturam `sqlalchemy.exc.IntegrityError` no `session.commit()` do insert
  da nova `Execution`; em caso de violação do índice único, fazem
  `session.rollback()`, releem a execução ativa da base (`repo` já expõe o
  necessário via uma nova leitura simples) e levantam `HTTPException(409,
  detail={"execution_id": ..., "situacao": ...})` — mesmo formato de detail
  usado hoje, agora estruturado.

#### Migrations

- Uma migration Alembic nova em `alembic/versions/`, no padrão das duas
  existentes (`074d455d6f67_schema_inicial...py`,
  `f3b60ce4f7f4_add_documentos_to_bases.py`): `op.create_index` com
  `postgresql_where=sa.text("situacao IN ('pending', 'running')")`,
  `unique=True`, sobre `executions.base_id`. `downgrade()` remove o índice.
  Compatível para trás: nenhuma linha existente pode violar o índice, porque
  o invariante de "uma ativa por base" já era a intenção (só não era
  garantido) — na pior hipótese de dado já inconsistente em ambiente real, a
  migration falha de forma visível (não silenciosa) e exige limpeza manual
  antes de aplicar, o que é aceitável neste ambiente de demonstração.

#### Models

- `Execution` (`src/app/models.py`): adiciona o índice único parcial descrito
  acima. Nenhum campo novo, nenhuma migração de dados.

#### Controllers e casos de uso

- `iniciar_execucao` e `repetir_execucao`
  (`src/app/routers/executions.py`): passam a tratar `IntegrityError` do
  insert de `Execution` como 409 estruturado, além do 409 otimista já
  existente vindo de `has_active_execution`. Autorização inalterada
  (`require_write_role`).

#### Views e experiência

- Não aplicável — sem interface para pessoas nesta spec (decisão confirmada,
  Pergunta 6).

#### Queries e repositórios

- `src/app/repo.py::has_active_execution` permanece como está (check
  otimista, evita um insert desnecessário no caminho sequencial comum).

#### Jobs e processamento assíncrono

- Não aplicável — `process_base_task` (`src/app/tasks.py`) não muda; esta
  spec atua antes do agendamento da tarefa.

#### Estrutura de arquivos

```text
specs/draft/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/
  spec.md
  research/
alembic/versions/<revisao>_indice_unico_execucao_ativa_por_base.py
src/app/models.py
src/app/routers/executions.py
tests/test_app_executions.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `Execution` | `id` (UUID) | `base_id`, `situacao` — invariante novo: no máximo uma linha com `situacao IN ('pending','running')` por `base_id`, garantido por índice único parcial | N:1 com `Base` |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| `Execution` | (nenhuma ativa para a base) | insert com `situacao="pending"` | `pending` | índice único parcial garante unicidade por `base_id` entre `pending`/`running` |
| `Execution` | `pending`/`running` já ativa | tentativa de insert concorrente | (rejeitado) | violação de integridade convertida em HTTP 409 com `id`/`situacao` da ativa |

#### Migração e retenção

- Não aplicável — sem migração de dados existentes, só adição de índice.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A correção é inteiramente de backend
  (índice de banco + tratamento de erro); o frontend (SPEC-0013) já trata o
  409 de forma genérica e adequada para este cenário (decisão confirmada no
  refinamento do BACKLOG-0018, Pergunta 6) — nenhuma tela, componente ou
  fluxo visual muda.

#### APIs expostas

- `POST /api/v1/bases/{base_id}/executions` (já existente,
  `src/app/routers/executions.py`): resposta de erro 409 passa a incluir
  corpo estruturado `{"detail": {"execution_id": "<id>", "situacao":
  "<pending|running>"}}` tanto no caminho otimista (check prévio) quanto no
  caminho de corrida real (violação de integridade). Sem mudança de
  autenticação nem de versionamento.
- `POST /api/v1/executions/{execution_id}/retry` (já existente): mesmo
  tratamento de 409 estruturado.

#### APIs externas utilizadas

- Nenhuma.

#### Documentação das APIs consultadas

- Nenhuma.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: conversão de `IntegrityError` em `HTTPException(409, ...)`
  estruturado (`src/app/routers/executions.py`).
- **Integração/contrato**: índice único parcial provado por duas sessões
  Postgres reais contra `rag_pipeline_test` (AC-001, AC-002); regressão
  sequencial via `TestClient` HTTP (AC-003).
- **BDD/aceite**: cenários da seção 6 (AC-001 a AC-003) orientam o desenho
  dos três casos TDD abaixo.
- **Runner TDD**: Pytest (projeto Python, `.specsfy/RULES.md`).
- **E2E**: não aplicável — o teste de concorrência real com duas sessões já
  cobre o caminho ponta a ponta relevante (banco real, sem mock).
- **Verificação manual**: nenhuma prevista; o comportamento inteiro é
  verificável por teste automatizado contra `rag_pipeline_test`.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, FR-003, NFR-001, AC-001 | AC-001 na seção 6 | `tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_iniciar` com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 AC-001` | Pending | Pending | Pending |
| US-001, FR-001, FR-002, FR-003, NFR-001, AC-002 | AC-002 na seção 6 | `tests/test_app_executions.py::test_corrida_real_entre_iniciar_e_repetir` com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 AC-002` | Pending | Pending | Pending |
| US-001, FR-001, FR-002, FR-003, NFR-001, AC-003 | AC-003 na seção 6 | `tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_repetir` com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 AC-003` | Pending | Pending | Pending |
| US-001, FR-001, FR-002, AC-004 | AC-004 na seção 6 | `tests/test_app_executions.py::test_execucao_ativa_commitada_rejeita_sequencial` com marcador `SPECSFY: US-001 FR-001 FR-002 AC-004` | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001, FR-002, FR-003 | AC-001 | Integração (banco real) | `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_iniciar -v` | Pending |
| FR-001, FR-002, FR-003 | AC-002 | Integração (banco real) | `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_iniciar_e_repetir -v` | Pending |
| FR-001, FR-002, FR-003 | AC-003 | Integração (banco real) | `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_repetir -v` | Pending |
| FR-001, FR-002 | AC-004 | Integração HTTP | `uv run pytest tests/test_app_executions.py::test_execucao_ativa_commitada_rejeita_sequencial -v` | Pending |
| NFR-001 | AC-001, AC-002, AC-003 | Integração (banco real) | comandos acima | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md --allow-draft` → `VALID DRAFT`.
- **Cobertura mínima**: US-001 (4 AC), FR-001 (4 AC), FR-002 (4 AC), FR-003 (3 AC), NFR-001 (3 AC) — todos ≥ 3, conforme MCR-10.
- **Revisão semântica (2026-09-15)**: aplicadas as lentes `PROD` e `ARCH`
  (`references/review-lenses.md`), materiais por envolver migration e
  invariante de concorrência real; `SEC` avaliada e considerada não material
  — sem autenticação/autorização nova, sem dado sensível novo exposto (o
  409 só expõe `id`/`situacao`, já acessíveis a quem tem permissão sobre a
  base). Nenhum achado `P1 Open`: os princípios PR-001–PR-004 aparecem no
  desenho das seções 8–10, os caminhos citados existem no repositório
  (`src/app/models.py`, `src/app/routers/executions.py`,
  `alembic/versions/`), e rollback/compatibilidade da migration estão
  decididos (seção 8, "Migrations"). `node
  .agents/skills/specsfy-04-validate/scripts/review_findings.mjs
  specs/draft/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md`
  → `Reviews: PASSED` (nenhum achado registrado, nenhum bloqueio).
- **Achados**: Nenhum `BLOCKER`. Nenhum achado `P1/P2/P3` registrado.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/draft/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md`
- **Achados**: Pending.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md .`
- **Achados**: Pending.

### 14. Tarefas

Formato:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Cada tarefa possui exatamente este checklist, atualizado durante a execução:

```markdown
  - [ ] **PREP**: Confirmar escopo, IDs, dependências e baseline.
  - [ ] **EXECUTE**: Produzir a entrega no caminho declarado.
  - [ ] **VERIFY**: Executar a verificação focal adequada.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do sistema; se não houver interface, registrar `Não aplicável` e o motivo.
  - [ ] **EVIDENCE**: Registrar comando, resultado e IDs nas seções 11–13.
  - [ ] **IMPROVE**: Registrar melhoria aplicada ou ausência justificada.
```

Esta fatia não cria tarefas de tarefas ainda — a decomposição detalhada
(RED/GREEN/REFACTOR e migration) é responsabilidade de `$specsfy-05-tasks`.

### 15. Ordem de execução

- Caminho crítico: migration → RED (AC-001/AC-002/AC-003) → GREEN
  (conversão de erro + índice) → regressão.
- Tarefas paralelas: nenhuma — item pequeno, sequência única.
- Estratégia de MVP: a spec inteira é o menor conjunto entregável; não há
  fatiamento adicional.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Migration Alembic aplicada no banco de teste (`rag_pipeline_test`) antes
  dos testes de integração.

#### Riscos

- Ambiente com dado já inconsistente (mais de uma execução ativa para a
  mesma base) faria a migration falhar ao criar o índice → mitigação:
  ambiente de demonstração, sem dado de produção; migration falha de forma
  visível, não silenciosa.
- Teste de concorrência real (duas sessões) pode ser mais lento ou sensível
  a timing do que um teste unitário simples → mitigação: o cenário é
  determinístico (duas transações não commitadas disputando o mesmo insert,
  sem depender de threads reais ou sleep), não um teste de carga.

#### Suposições

- O índice único parcial é suportado pelo dialeto PostgreSQL usado em
  produção e teste (`postgresql_where`), consistente com o uso já existente
  de recursos específicos do Postgres no projeto.

### 17. Decisões

- **DEC-001**: Rejeitar a segunda requisição concorrente com HTTP 409 (em
  vez de enfileirar ou permitir-e-cancelar) — mantém o invariante de
  execução única por base que a SPEC-0012 (seção 7) já pretendia, sem
  infraestrutura nova. Confirmada no refinamento do BACKLOG-0018, Pergunta 1.
- **DEC-002**: Mecanismo de atomicidade é índice único parcial no banco (não
  lock de aplicação nem lock distribuído) — garante o invariante
  independente de quantos processos/workers tentem inserir ao mesmo tempo.
  Confirmada na Pergunta 4.
- **DEC-003**: Sem mudança de frontend — o catch genérico de
  `PainelProgresso.tsx` já é suficiente para o cenário raro. Confirmada na
  Pergunta 6.
- **DEC-004**: Spec separada de BACKLOG-0019 (compensação em `apagar_base`),
  apesar de descoberta junto e no mesmo módulo — correções independentes,
  uma exige migration e a outra não. Confirmada no refinamento cruzado dos
  dois backlogs.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
