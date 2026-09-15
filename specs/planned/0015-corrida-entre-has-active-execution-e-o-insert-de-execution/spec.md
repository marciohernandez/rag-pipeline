# Especificação integrada: Corrida entre has_active_execution e o insert de Execution

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0015 |
| Slug | 0015-corrida-entre-has-active-execution-e-o-insert-de-execution |
| Status | Planned |
| Effort | 4 |
| Effort updated at | 2026-09-15 |
| Effort rationale | Correção localizada em `src/app/` (repo, router, models) com uma migration Alembic simples (índice único parcial) e conversão de erro de integridade em HTTP 409; a parte não trivial é provar a corrida de forma determinística (via monkeypatch em `has_active_execution`, não threads reais), não o código de produção. Perfil `standard`. — 2026-09-15: durante a materialização de T001 (`$specsfy-06-tdd-bdd`, modo prepare), a técnica de "duas sessões Postgres reais não commitadas" desenhada na definição se mostrou impraticável através do endpoint HTTP real (cada chamada abre e fecha sua própria sessão internamente, sem ponto de injeção). Substituída por monkeypatch determinístico em `repo.has_active_execution`, que força a janela de corrida sem depender de threads/timing — tecnica padrão para testar condições de corrida. RED observado com sucesso na primeira tentativa; Effort mantido em 4, sem mudança de escopo. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
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
- Teste que força deterministicamente a janela de corrida (via monkeypatch
  em `repo.has_active_execution`, contra o banco real `rag_pipeline_test`),
  substituindo/complementando `test_impede_execucao_concorrente`.

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
**Teste independente**: contra o banco real (`rag_pipeline_test`), commitar
uma execução ativa para uma base e forçar deterministicamente a janela de
corrida — via monkeypatch em `repo.has_active_execution` retornando `False`
mesmo havendo execução ativa, simulando o que uma segunda requisição veria
se tivesse checado antes do commit da primeira — e chamar o endpoint real:
o insert deve falhar por violação do índice único parcial e ser convertido
em 409 com o `id`/`situacao` da execução realmente ativa.
**Requisitos**: FR-001, FR-002, FR-003

### 6. Cenários BDD de aceite

#### AC-001 — Corrida real entre duas chamadas iniciar_execucao

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-001 @AC-001
Feature: Impedir execuções ativas concorrentes na mesma base

  Scenario: Segunda chamada iniciar_execucao perde a corrida
    Given uma base com uma execução em situação "pending" já commitada
    And uma segunda chamada a iniciar_execucao chega numa janela em que seu
      check otimista de has_active_execution não vê essa execução ativa —
      corrida real: a checagem ocorreu antes do commit da primeira
    When essa segunda chamada tenta inserir uma nova Execution para a mesma
      base
    Then o insert é rejeitado pelo índice único parcial do banco
    And a chamada recebe HTTP 409 com "execution_id" e "situacao" da
      execução realmente ativa no corpo da resposta
```

#### AC-002 — Corrida real entre iniciar_execucao e repetir_execucao

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-001 @AC-002
Feature: Impedir execuções ativas concorrentes na mesma base

  Scenario: repetir_execucao perde a corrida contra uma execução já ativa
    Given uma base com uma execução em situação "pending" já commitada e
      outra execução em situação "failed" na mesma base
    And uma chamada a repetir_execucao para a execução "failed" chega numa
      janela em que seu check otimista de has_active_execution não vê a
      execução "pending" ativa — corrida real com o endpoint iniciar_execucao
    When essa chamada tenta inserir uma nova Execution para a mesma base
    Then o insert é rejeitado pelo índice único parcial do banco,
      independentemente de qual endpoint (iniciar ou repetir) chamou primeiro
    And a chamada recebe HTTP 409 com "execution_id" e "situacao" da
      execução realmente ativa no corpo da resposta
```

#### AC-003 — Corrida real entre duas chamadas repetir_execucao

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-001 @AC-003
Feature: Impedir execuções ativas concorrentes na mesma base

  Scenario: repetir_execucao perde a corrida contra outra repetir_execucao
    Given uma base com uma execução em situação "pending" já commitada e
      duas outras execuções em situação "failed" na mesma base
    And uma chamada a repetir_execucao para uma das execuções "failed" chega
      numa janela em que seu check otimista de has_active_execution não vê a
      execução "pending" ativa
    When essa chamada tenta inserir uma nova Execution para a mesma base
    Then o insert é rejeitado pelo índice único parcial do banco
    And a chamada recebe HTTP 409 com "execution_id" e "situacao" da
      execução realmente ativa no corpo da resposta
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
  automatizado contra `rag_pipeline_test`, forçando deterministicamente a
  janela de corrida via monkeypatch em `has_active_execution` (não checagem
  otimista após o fato), provando que o índice único do banco — não o
  check da aplicação — garante o invariante (AC-001, AC-002, AC-003).

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
mock —, o que permite provar o índice único parcial contra o dialeto real,
mesmo com a janela de corrida forçada por monkeypatch em vez de threads.

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
specs/defined/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/
  spec.md
  research/
alembic/versions/<revisao>_indice_unico_execucao_ativa_por_base.py
src/app/models.py
src/app/repo.py
src/app/routers/executions.py
tests/test_app_executions.py
tests/test_app_migrations.py
.specsfy/DATABASE.md
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
  estruturado (`src/app/repo.py`/`src/app/routers/executions.py`).
- **Integração/contrato**: índice único parcial provado via `TestClient` HTTP
  contra `rag_pipeline_test`, com a janela de corrida forçada
  deterministicamente por monkeypatch em `has_active_execution` (AC-001,
  AC-002, AC-003); regressão sequencial, sem monkeypatch, via `TestClient`
  HTTP (AC-004).
- **BDD/aceite**: cenários da seção 6 (AC-001 a AC-004) orientam o desenho
  dos quatro casos TDD abaixo.
- **Runner TDD**: Pytest (projeto Python, `.specsfy/RULES.md`).
- **E2E**: não aplicável — os testes de AC-001–AC-003 já exercitam o
  endpoint HTTP real ponta a ponta contra banco real, sem mock.
- **Verificação manual**: nenhuma prevista; o comportamento inteiro é
  verificável por teste automatizado contra `rag_pipeline_test`.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, FR-003, NFR-001, AC-001 | AC-001 na seção 6 | `tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_iniciar` com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 AC-001` | `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_iniciar -v` → `assert 202 == 409` (2026-09-15) | Pending | Pending |
| US-001, FR-001, FR-002, FR-003, NFR-001, AC-002 | AC-002 na seção 6 | `tests/test_app_executions.py::test_corrida_real_entre_iniciar_e_repetir` com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 AC-002` | `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_iniciar_e_repetir -v` → `assert 202 == 409` (2026-09-15) | Pending | Pending |
| US-001, FR-001, FR-002, FR-003, NFR-001, AC-003 | AC-003 na seção 6 | `tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_repetir` com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 AC-003` | `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_repetir -v` → `assert 202 == 409` (2026-09-15) | Pending | Pending |
| US-001, FR-001, FR-002, AC-004 | AC-004 na seção 6 | `tests/test_app_executions.py::test_execucao_ativa_commitada_rejeita_sequencial` com marcador `SPECSFY: US-001 FR-001 FR-002 AC-004` | `uv run pytest tests/test_app_executions.py::test_execucao_ativa_commitada_rejeita_sequencial -v` → `AssertionError` (detail ainda é string) (2026-09-15) | Pending | Pending |

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

- **Resultado**: READY
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md` → `VALID DRAFT` (9 tarefas, 4 concluídas, 9/9 IDs cobertos).
- **Predecessores TDD**: T001–T004 concluídos com RED observado e registrado (tabela da seção 11), cobrindo os quatro AC e os predecessores mínimos de US-001/FR-001/FR-002/FR-003/NFR-001. T005 (`[CODE]`, migration) depende dos quatro.
- **Achados**: Nenhum bloqueio. Correção de plano registrada em `Effort rationale` (cabeçalho): a técnica de teste evoluiu de "duas sessões Postgres não commitadas" (impraticável via HTTP real) para monkeypatch determinístico em `has_active_execution`, sem mudança de FR/AC/escopo.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md .`
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

Nota local (`.specsfy/RULES.md`): migration não usa a tag `[MIGRATION]`
(rejeitada por `validate_tasks.mjs`); é uma tarefa `[CODE]` comum apontando
para `alembic/versions/<revisao>_<slug>.py`, com dois comandos aprovados no
item `VERIFY` (aplicar no banco de teste + `alembic current`).

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pytest falhando em tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_iniciar — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Lidos o Gherkin do AC-001 (seção 6), `tests/conftest.py` (banco real `rag_pipeline_test`, porta 55432) e `src/app/routers/executions.py` (`iniciar_execucao` chama `repo.has_active_execution(session, base.id)` por atributo de módulo). Confirmado: a técnica original de "duas sessões não commitadas" não é praticável através do endpoint HTTP real (cada chamada abre/fecha sua própria sessão internamente); adotado monkeypatch determinístico em `repo.has_active_execution`, que a técnica de `monkeypatch.setattr` alcança porque o router acessa `repo.has_active_execution` por atributo do módulo em tempo de chamada.
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 AC-001` em `tests/test_app_executions.py`: commita uma base com uma `Execution(situacao="pending")` já ativa; `monkeypatch.setattr(repo, "has_active_execution", lambda session, base_id: False)` força a janela de corrida; chama `POST /api/v1/bases/{base_id}/executions` via `TestClient` real; assere HTTP 409 com `{"execution_id": ..., "situacao": "pending"}`. Sem `.feature`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_iniciar -v` → RED confirmado: `assert 202 == 409` — sem o índice único, o insert da segunda chamada é aceito silenciosamente (falha por comportamento ausente, não por sintaxe/fixture/ambiente).
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: Comando e resultado acima registrados na tabela da seção 11 (Evidência RED-GREEN-REFACTOR).
  - [x] **IMPROVE**: Correção de plano aplicada e registrada em `Effort rationale` (cabeçalho) — a técnica de teste mudou de "duas sessões" para "monkeypatch determinístico"; nenhuma mudança de FR/AC/escopo.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pytest falhando em tests/test_app_executions.py::test_corrida_real_entre_iniciar_e_repetir — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-002 (seção 6) e o teste de T001 (mesma técnica de monkeypatch, já validada). Fixture: base com uma execução `pending` já ativa e outra `failed` (alvo do `repetir_execucao`).
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 AC-002` em `tests/test_app_executions.py`, mesma técnica de T001, chamando `POST /api/v1/executions/{execution_id}/retry` para a execução `failed`. Sem `.feature`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_iniciar_e_repetir -v` → RED confirmado: `assert 202 == 409`.
  - [x] **VISUAL**: Não aplicável — sem superfície visual.
  - [x] **EVIDENCE**: Comando e resultado acima registrados na tabela da seção 11.
  - [x] **IMPROVE**: Cobertura cruzada entre endpoints confirmada — mesmo mecanismo (`has_active_execution`) usado pelos dois, prova direta de FR-003.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pytest falhando em tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_repetir — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-003 (seção 6). Fixture: base com uma execução `pending` já ativa e duas `failed`.
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 AC-003` em `tests/test_app_executions.py`, mesma técnica de T001/T002, chamando `POST /api/v1/executions/{execution_id}/retry` para uma das execuções `failed`. Sem `.feature`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_repetir -v` → RED confirmado: `assert 202 == 409`.
  - [x] **VISUAL**: Não aplicável — sem superfície visual.
  - [x] **EVIDENCE**: Comando e resultado acima registrados na tabela da seção 11.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária — mesma técnica de T001/T002, já validada.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso Pytest falhando em tests/test_app_executions.py::test_execucao_ativa_commitada_rejeita_sequencial — Refs: US-001, FR-001, FR-002, AC-004 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-004 e o teste existente `test_impede_execucao_concorrente` (regressão sequencial já coberta hoje só pela mensagem genérica).
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: US-001 FR-001 FR-002 AC-004` em `tests/test_app_executions.py`: via `TestClient` real (sem monkeypatch), base com execução `running` já commitada, chama `iniciar_execucao` e assere HTTP 409 com corpo `{"execution_id": "<id>", "situacao": "running"}`. Sem `.feature`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_execucao_ativa_commitada_rejeita_sequencial -v` → RED confirmado: `AssertionError: assert 'Já existe uma execução ativa para esta base.' == {'execution_id': ..., 'situacao': 'running'}` — formato do `detail` ainda é string simples, não estruturado.
  - [x] **VISUAL**: Não aplicável — sem superfície visual.
  - [x] **EVIDENCE**: Comando e resultado acima registrados na tabela da seção 11.
  - [x] **IMPROVE**: `test_impede_execucao_concorrente` original mantido como caso adicional (não removido) — continua GREEN sem alteração, cobrindo o mesmo caminho sequencial com uma asserção mais simples (`status_code == 409`, sem checar o corpo).

#### Fase 2 — US-001 [Nunca ter duas execuções ativas concorrentes na mesma base] (P1)

**Objetivo**: garantir atomicamente, via índice único parcial no banco, que
nunca existam duas execuções ativas simultâneas para a mesma base, com HTTP
409 estruturado informando qual execução já está ativa.
**Teste independente**: os quatro testes de T001–T004 passam (GREEN) e
`test_impede_execucao_concorrente` original continua passando.

- [ ] T005 [CODE] [US-001] Criar migration Alembic com índice único parcial em executions.base_id (situacao IN pending/running) em alembic/versions/<revisao>_indice_unico_execucao_ativa_por_base.py e atualizar tests/test_app_migrations.py para asserir o índice — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-003 — Depends: T001, T002, T003, T004
  - [ ] **PREP**: RED de T001–T004 reconfirmado. `$specsfy-documentator` (`build_documentation.mjs --project . --check`) confirma `docs/` atual antes de alterar schema. Ler `alembic/versions/074d455d6f67_*.py` e `f3b60ce4f7f4_*.py` (convenção de nome, `down_revision`, estilo de docstring) e `tests/test_app_migrations.py` (padrão de asserção via `sqlalchemy.inspect`).
  - [ ] **EXECUTE**: Adicionar `Index(..., unique=True, postgresql_where=sa.text("situacao IN ('pending', 'running')"))` sobre `base_id` em `src/app/models.py::Execution`. Criar a revisão Alembic (`op.create_index(..., unique=True, postgresql_where=...)` em `upgrade`; `op.drop_index(...)` em `downgrade`), no estilo das revisões existentes. Atualizar `tests/test_app_migrations.py` para asserir, via `inspetor.get_indexes("executions")`, que o índice único parcial existe.
  - [ ] **VERIFY**: `APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test uv run alembic upgrade head` → exit 0; `APP_DATABASE_URL=... uv run alembic current` → revisão nova aplicada; `uv run pytest tests/test_app_migrations.py -q` → GREEN.
  - [ ] **VISUAL**: Não aplicável — migration de schema, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar os três comandos acima e arquivos alterados nas seções 11–13.
  - [ ] **IMPROVE**: Registrar melhoria aplicada ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T005","refs":["US-001","FR-001","NFR-001","AC-001","AC-002","AC-003"],"files":["src/app/models.py","alembic/versions/<revisao>_indice_unico_execucao_ativa_por_base.py","tests/test_app_migrations.py"],"commands":[{"run":"alembic upgrade head","exit":0},{"run":"alembic current","exit":0},{"run":"uv run pytest tests/test_app_migrations.py -q","exit":0}]} -->

- [ ] T006 [CODE] [US-001] Adicionar função compartilhada de insert com conversão de IntegrityError em 409 estruturado em src/app/repo.py — Refs: US-001, FR-001, FR-002, FR-003, AC-001, AC-002, AC-003, AC-004 — Depends: T005
  - [ ] **PREP**: RED de T001–T004 reconfirmado com o índice já aplicado (T005) — agora a violação de integridade acontece, mas ainda não é convertida em 409 estruturado. `$specsfy-documentator` (`--check`) confirma `docs/` atual. Ler `src/app/repo.py` (padrão de funções existentes) e `src/app/routers/executions.py` (uso atual de `has_active_execution`).
  - [ ] **EXECUTE**: Adicionar `repo.inserir_execucao_ativa(session, base_id) -> Execution`, que insere e commita a `Execution`, captura `sqlalchemy.exc.IntegrityError` na violação do índice único, faz `session.rollback()`, relê a execução ativa da base e levanta `HTTPException(409, detail={"execution_id": ..., "situacao": ...})`. Função única usada pelos dois endpoints (FR-003).
  - [ ] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_iniciar tests/test_app_executions.py::test_corrida_real_entre_iniciar_e_repetir tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_repetir -v` → GREEN.
  - [ ] **VISUAL**: Não aplicável — sem superfície visual.
  - [ ] **EVIDENCE**: Registrar comando, resultado e arquivos alterados.
  - [ ] **IMPROVE**: Registrar melhoria aplicada ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T006","refs":["US-001","FR-001","FR-002","FR-003","AC-001","AC-002","AC-003","AC-004"],"files":["src/app/repo.py"],"commands":[{"run":"uv run pytest tests/test_app_executions.py -k corrida_real -v","exit":0}]} -->

- [ ] T007 [CODE] [US-001] Usar repo.inserir_execucao_ativa nos dois endpoints e estruturar o 409 otimista em src/app/routers/executions.py — Refs: US-001, FR-001, FR-002, FR-003, AC-004 — Depends: T006
  - [ ] **PREP**: RED de T004 reconfirmado (formato do `detail` ainda é string). `$specsfy-documentator` (`--check`) confirma `docs/` atual. Ler `iniciar_execucao` e `repetir_execucao` (`src/app/routers/executions.py`) para trocar o insert direto por `repo.inserir_execucao_ativa` e estruturar também o 409 do check otimista (`has_active_execution`) no mesmo formato `{"execution_id": ..., "situacao": ...}`.
  - [ ] **EXECUTE**: Substituir o insert direto de `Execution` pela chamada a `repo.inserir_execucao_ativa` em `iniciar_execucao` e `repetir_execucao`; estruturar o `detail` do 409 otimista existente no mesmo formato.
  - [ ] **VERIFY**: `uv run pytest tests/test_app_executions.py -v` → GREEN (todas as quatro tarefas T001–T004, mais `test_impede_execucao_concorrente` original).
  - [ ] **VISUAL**: Não aplicável — resposta HTTP de erro, sem tela associada; frontend não muda (decisão confirmada, seção 2).
  - [ ] **EVIDENCE**: Registrar comando, resultado e arquivos alterados.
  - [ ] **IMPROVE**: Registrar melhoria aplicada ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T007","refs":["US-001","FR-001","FR-002","FR-003","AC-004"],"files":["src/app/routers/executions.py"],"commands":[{"run":"uv run pytest tests/test_app_executions.py -v","exit":0}]} -->

- [ ] T008 [DOC] Atualizar .specsfy/DATABASE.md com o índice único parcial de executions — Refs: FR-001 — Depends: T005
  - [ ] **PREP**: Ler `.specsfy/DATABASE.md` (curado manualmente neste projeto, `.specsfy/RULES.md`) e a migration de T005.
  - [ ] **EXECUTE**: Registrar manualmente o índice único parcial `(base_id)` filtrado por `situacao IN ('pending','running')` na tabela `executions` de `.specsfy/DATABASE.md`.
  - [ ] **VERIFY**: Revisão visual do arquivo confirmando a entrada nova, consistente com `src/app/models.py::Execution` e a migration de T005.
  - [ ] **VISUAL**: Não aplicável — documentação, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar o trecho adicionado.
  - [ ] **IMPROVE**: Registrar melhoria aplicada ou justificar nenhuma.

**Checkpoint**: rodar os quatro testes de T001–T004 mais
`test_impede_execucao_concorrente` original — todos GREEN demonstram a
história isoladamente, sem depender de outra fatia.

#### Fase final — Qualidade

- [ ] T009 [TEST] Executar regressão completa e rastreabilidade em tests/test_app_executions.py e tests/test_app_migrations.py — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-001, AC-002, AC-003, AC-004 — Depends: T007, T008
  - [ ] **PREP**: Identificar suítes, checks e gates aplicáveis (Ruff, Pytest completo, `check_traceability.mjs`).
  - [ ] **EXECUTE**: `uv run ruff check .`; `uv run pytest -q`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md .`.
  - [ ] **VERIFY**: Confirmar ausência de regressão nos testes pré-existentes e rastreabilidade completa dos IDs desta spec.
  - [ ] **VISUAL**: Não aplicável — item de regressão/rastreabilidade, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar contagens e comandos finais nas seções 11–13.
  - [ ] **IMPROVE**: Registrar retrospectiva do processo — por exemplo, se `test_impede_execucao_concorrente` original foi mantido, removido ou absorvido pelos novos casos.

### 15. Ordem de execução

- Caminho crítico: T001/T002/T003/T004 (RED) → T005 (migration) → T006 (repo)
  → T007 (routers) → T008 (DATABASE.md) → T009 (regressão/rastreabilidade).
- Tarefas paralelas: nenhuma marcada `[P]` — T001–T004 compartilham
  `tests/test_app_executions.py` (mesmo arquivo, funções distintas); T008
  depende só de T005, mas edita `.specsfy/DATABASE.md`, arquivo não
  compartilhado com T006/T007, e poderia rodar em paralelo a elas se
  houvesse mais de uma pessoa implementando — não marcada `[P]` porque a
  sequência única é suficiente para o tamanho da fatia.
- Estratégia de MVP: a spec inteira é o menor conjunto entregável; não há
  fatiamento adicional — é uma correção de bug única e pequena.

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
- ~~Teste de concorrência real (duas sessões) pode ser mais lento ou
  sensível a timing~~ — mitigado na prática: a técnica final (monkeypatch em
  `has_active_execution`, T001) é determinística e não depende de threads
  reais nem de sleep; RED observado de forma estável na primeira execução.

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
