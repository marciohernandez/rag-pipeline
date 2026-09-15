# Especificação integrada: Corrida entre has_active_execution e o insert de Execution

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0015 |
| Slug | 0015-corrida-entre-has-active-execution-e-o-insert-de-execution |
| Status | Complete |
| Effort | 4 |
| Effort updated at | 2026-09-15 |
| Effort rationale | Correção localizada em `src/app/` (repo, router, models) com migration Alembic, índice único parcial e conversão seletiva da violação esperada em HTTP 409. Perfil `standard`. — 2026-09-15: a auditoria pré-implementação invalidou a estratégia TDD baseada apenas em uma linha já commitada e monkeypatch do check, pois ela não satisfazia a métrica aprovada de duas transações PostgreSQL concorrentes. O plano passa a disparar dois endpoints HTTP em threads/sessões reais; um wrapper preserva a consulta de `has_active_execution` e usa `threading.Barrier` para liberar os dois inserts somente depois que ambos os checks retornarem `False`. Não há `sleep`, banco simulado ou resultado falsificado. Effort mantido em 4. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
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
- Testes HTTP com duas sessões PostgreSQL reais coordenadas por
  `threading.Barrier`, sem `sleep`: ambos os endpoints executam a consulta
  real, observam ausência de execução ativa e só então disputam os inserts e
  commits no banco.
- Teste sequencial existente e asserção do corpo estruturado do HTTP 409.

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
**Teste independente**: contra o banco real (`rag_pipeline_test`), disparar os
dois endpoints HTTP em threads/sessões distintas. Um `threading.Barrier`
preserva as duas consultas reais e libera os inserts somente depois que ambas
retornarem `False`. Exatamente um commit deve ser aceito; o concorrente deve
ser rejeitado pelo índice único parcial e convertido em 409 com o
`id`/`situacao` da execução vencedora.
**Requisitos**: FR-001, FR-002, FR-003

### 6. Cenários BDD de aceite

#### AC-001 — Corrida real entre duas chamadas iniciar_execucao

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-001 @AC-001
Feature: Impedir execuções ativas concorrentes na mesma base

  Scenario: Segunda chamada iniciar_execucao perde a corrida
    Given uma base commitada e duas chamadas a iniciar_execucao em sessões
      distintas
    And as duas chamadas concluem o check otimista sem execução ativa
    When ambas tentam inserir e commitar uma nova Execution para a mesma base
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
    Given uma base e uma execução "failed" commitadas
    And iniciar_execucao e repetir_execucao concluem o check otimista em
      sessões distintas sem execução ativa
    When ambas tentam inserir e commitar uma nova Execution para a mesma base
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
    Given uma base e duas execuções "failed" commitadas
    And duas chamadas a repetir_execucao concluem o check otimista em sessões
      distintas sem execução ativa
    When ambas tentam inserir e commitar uma nova Execution para a mesma base
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
  automatizado contra `rag_pipeline_test` com duas sessões/transações reais e
  coordenação por `threading.Barrier`, sem `sleep`. O wrapper do check preserva
  a consulta real e libera os inserts apenas quando ambas retornarem `False`,
  provando que o índice único do banco — não o check da aplicação — garante o
  invariante (AC-001, AC-002, AC-003).

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
mock. Os casos concorrentes disparam duas requisições em threads separadas;
`threading.Barrier` coordena a ordem sem depender de tempo de máquina.

#### Arquitetura e módulos

- `src/app/models.py`: `Execution` ganha um índice único parcial
  (`Index(..., unique=True, postgresql_where=...)`) sobre `base_id`, restrito
  a `situacao IN ('pending', 'running')`.
- `src/app/repo.py`: nenhuma mudança de assinatura; `has_active_execution`
  continua como check otimista (evita uma tentativa de insert desnecessária
  no caminho feliz sequencial, AC-003), mas deixa de ser a única garantia.
- `src/app/routers/executions.py`: `iniciar_execucao` e `repetir_execucao`
  usam a função comum de insert. A função captura
  `sqlalchemy.exc.IntegrityError` no `session.commit()` da nova `Execution` e
  só converte em conflito a violação `23505` do índice
  `uq_executions_base_active`; qualquer outra falha de integridade é
  propagada. Na violação esperada, faz `session.rollback()`, relê a execução
  ativa da base e levanta `HTTPException(409,
  detail={"execution_id": ..., "situacao": ...})`. Se a releitura não
  encontrar uma ativa, a falha original também é propagada.

#### Migrations

- Uma migration Alembic nova em `alembic/versions/`, no padrão das duas
  existentes (`074d455d6f67_schema_inicial...py`,
  `f3b60ce4f7f4_add_documentos_to_bases.py`): `op.create_index` com nome
  estável `uq_executions_base_active`,
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
  contra `rag_pipeline_test`, com duas sessões/transações reais coordenadas
  por `threading.Barrier` (AC-001, AC-002, AC-003). O wrapper temporário de
  `has_active_execution` preserva a consulta e sincroniza seu retorno. A regressão
  sequencial usa `TestClient` HTTP sem coordenação (AC-004).
- **BDD/aceite**: cenários da seção 6 (AC-001 a AC-004) orientam o desenho
  dos quatro casos TDD abaixo.
- **Runner TDD**: Pytest (projeto Python, `.specsfy/RULES.md`).
- **E2E**: não aplicável — os testes de AC-001–AC-003 exercitam o endpoint
  HTTP real contra banco real e dublam somente o agendamento posterior, já
  fora da disputa de persistência desta spec.
- **Verificação manual**: nenhuma prevista; o comportamento inteiro é
  verificável por teste automatizado contra `rag_pipeline_test`.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, FR-003, NFR-001, AC-001 | AC-001 na seção 6 | `tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_iniciar` com marcador `SPECSFY: SPEC-0015 US-001 FR-001 FR-002 FR-003 NFR-001 AC-001` | `uv run pytest tests/test_app_executions.py -k 'corrida_real' -v` → duas sessões HTTP retornaram `[202, 202]`, diferente de `[202, 409]`; RED válido em 2026-09-15 | `uv run pytest tests/test_app_executions.py -v` → 10 passed, GREEN (2026-09-15) | `uv run pytest -q` (suíte completa) → sem regressão |
| US-001, FR-001, FR-002, FR-003, NFR-001, AC-002 | AC-002 na seção 6 | `tests/test_app_executions.py::test_corrida_real_entre_iniciar_e_repetir` com marcador `SPECSFY: SPEC-0015 US-001 FR-001 FR-002 FR-003 NFR-001 AC-002` | Mesmo comando → início e repetição retornaram `[202, 202]`, diferente de `[202, 409]`; RED válido em 2026-09-15 | `uv run pytest tests/test_app_executions.py -v` → 10 passed, GREEN (2026-09-15) | `uv run pytest -q` (suíte completa) → sem regressão |
| US-001, FR-001, FR-002, FR-003, NFR-001, AC-003 | AC-003 na seção 6 | `tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_repetir` com marcador `SPECSFY: SPEC-0015 US-001 FR-001 FR-002 FR-003 NFR-001 AC-003` | Mesmo comando → duas repetições distintas retornaram `[202, 202]`, diferente de `[202, 409]`; RED válido em 2026-09-15 | `uv run pytest tests/test_app_executions.py -v` → 10 passed, GREEN (2026-09-15) | `uv run pytest -q` (suíte completa) → sem regressão |
| US-001, FR-001, FR-002, AC-004 | AC-004 na seção 6 | `tests/test_app_executions.py::test_execucao_ativa_commitada_rejeita_sequencial` com marcador `SPECSFY: SPEC-0015 US-001 FR-001 FR-002 AC-004` | `uv run pytest tests/test_app_executions.py::test_execucao_ativa_commitada_rejeita_sequencial -v` → `AssertionError` (detail ainda é string) (2026-09-15) | `uv run pytest tests/test_app_executions.py -v` → 10 passed, GREEN (2026-09-15) | `uv run pytest -q` (suíte completa) → sem regressão |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001, FR-002, FR-003 | AC-001 | Integração (banco real) | `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_iniciar -v` | Passed (2026-09-15) |
| FR-001, FR-002, FR-003 | AC-002 | Integração (banco real) | `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_iniciar_e_repetir -v` | Passed (2026-09-15) |
| FR-001, FR-002, FR-003 | AC-003 | Integração (banco real) | `uv run pytest tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_repetir -v` | Passed (2026-09-15) |
| FR-001, FR-002 | AC-004 | Integração HTTP | `uv run pytest tests/test_app_executions.py::test_execucao_ativa_commitada_rejeita_sequencial -v` | Passed (2026-09-15) |
| NFR-001 | AC-001, AC-002, AC-003 | Integração (banco real) | comandos acima | Passed (2026-09-15) |

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

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md`.
- **Predecessores TDD**: T001–T003 agora provam o RED com requisições HTTP
  concorrentes e sessões reais; T004 prova o caminho sequencial.
- **Achados**: os quatro REDs são válidos, a SPEC-0016 eliminou colisões de
  namespace e a SPEC-0017 restaurou o enforcement global. O plano está pronto
  sem iniciar migration ou código de produção.

#### Gate do Ato III — Entrega

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md .` → `Namespace: SPEC-0015; modo: namespaced. Rastreabilidade: 9/9 IDs cobertos em 49 arquivos de teste. RESULTADO: OK`.
- **Tarefas**: 9/9 concluídas (`validate_tasks.mjs` estrito → `READY`, 54/54 itens de checklist).
- **QA**: `verify_acceptance.mjs` → `QA: PASSED` (AC-001–AC-004 todos `Passed`, seção 12).
- **Regressão**: `uv run ruff check .` → limpo. `uv run pytest -q` → 317 passed, 1 skipped (skip pré-existente de SPEC-0014, não relacionado a esta fatia). Sem regressão nos 313 testes anteriores.
- **Documentação**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos por `$specsfy-documentator`; `.specsfy/DATABASE.md` atualizado manualmente com o índice `uq_executions_base_active` (T008). `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT` (correção de bug de concorrência interna; sem mudança de história, finalidade, capacidades ou limites do produto).
- **Migration**: `alembic/versions/4d0fd0aa498e_indice_unico_execucao_ativa_por_base.py` aplicada e verificada (T005) — arquivo, comando de aplicação e consulta de estado registrados no `specsfy:evidence` de T005.
- **Aceite final (`$specsfy-04-validate`, 2026-09-15)**: `validate_spec.mjs` → `READY`; `review_findings.mjs` → `Reviews: PASSED`; `node .agents/skills/specsfy-04-validate/scripts/verify_repo.mjs . --boundary local --timeout-seconds 300 --max-output-bytes 65536` → exit 0, sem `FAIL` em nenhuma spec do repositório, incluindo as 13 specs `Complete` do M01/M02 que a SPEC-0017 corrigiu (confirma o fix repo-wide) e as próprias SPEC-0016/SPEC-0017. `Delivery Gate: Passed` confirmado; `Status: Complete`.
- **Achados**: Nenhum bloqueio.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pytest falhando com duas sessões PostgreSQL reais em tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_iniciar — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Confirmados `rag_pipeline_test`, duas chamadas reais ao endpoint de início e a consulta real de `has_active_execution` em cada sessão.
  - [x] **EXECUTE**: As duas chamadas aguardam numa `threading.Barrier` depois do check `False` e antes do insert; o agendamento posterior foi dublado por estar fora da disputa de persistência.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py -k 'corrida_real' -v` → RED: status observados `[202, 202]`, diferentes dos `[202, 409]` esperados, sem falha ambiental.
  - [x] **VISUAL**: Não aplicável — teste de concorrência de backend, sem superfície visual.
  - [x] **EVIDENCE**: Ordem observada e causa do RED registradas na seção 11.
  - [x] **IMPROVE**: Removida a falsa simulação por linha commitada; não há `sleep`, e `Future.result(timeout=5)` limita travamento.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pytest falhando com iniciar/repetir em sessões reais em tests/test_app_executions.py::test_corrida_real_entre_iniciar_e_repetir — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Confirmadas base e execução `failed` commitadas antes das chamadas concorrentes de início e repetição.
  - [x] **EXECUTE**: As duas sessões HTTP executam o check real e aguardam na mesma barreira antes de disputar o insert.
  - [x] **VERIFY**: Mesmo comando focal → RED: `[202, 202]` em vez de `[202, 409]`, sem falha ambiental.
  - [x] **VISUAL**: Não aplicável — teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: Ordem transacional e causa do RED registradas na seção 11.
  - [x] **IMPROVE**: Helper de concorrência reaproveitado sem ocultar os endpoints distintos exercitados.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pytest falhando entre repetições em sessões reais em tests/test_app_executions.py::test_corrida_real_entre_duas_chamadas_repetir — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Confirmadas base e duas execuções `failed` distintas e commitadas antes das duas repetições concorrentes.
  - [x] **EXECUTE**: As duas sessões HTTP executam o check real e aguardam na barreira antes de disputar o insert.
  - [x] **VERIFY**: Mesmo comando focal → RED: `[202, 202]` em vez de `[202, 409]`, sem flutuação por timing.
  - [x] **VISUAL**: Não aplicável — teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: Ordem transacional e causa do RED registradas na seção 11.
  - [x] **IMPROVE**: Helper comum preservado e `ThreadPoolExecutor` garante teardown das duas chamadas.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso Pytest falhando em tests/test_app_executions.py::test_execucao_ativa_commitada_rejeita_sequencial — Refs: US-001, FR-001, FR-002, AC-004 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-004 e o teste existente `test_impede_execucao_concorrente` (regressão sequencial já coberta hoje só pela mensagem genérica).
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: SPEC-0015 US-001 FR-001 FR-002 AC-004` em `tests/test_app_executions.py`: via `TestClient` real (sem monkeypatch), base com execução `running` já commitada, chama `iniciar_execucao` e assere HTTP 409 com corpo `{"execution_id": "<id>", "situacao": "running"}`. Sem `.feature`.
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

- [x] T005 [CODE] [US-001] Criar migration Alembic com índice único parcial nomeado em executions.base_id em alembic/versions/4d0fd0aa498e_indice_unico_execucao_ativa_por_base.py e atualizar tests/test_app_migrations.py — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-003 — Depends: T001, T002, T003, T004
  - [x] **PREP**: RED de T001–T004 reconfirmado. `$specsfy-documentator` (`build_documentation.mjs --project . --check`) confirmou `docs/` atual antes de alterar schema. Preflight somente leitura em `rag_pipeline_test` (`SELECT base_id, count(*) ... GROUP BY base_id HAVING count(*) > 1`) → nenhuma base conflitante.
  - [x] **EXECUTE**: Adicionado `Index("uq_executions_base_active", "base_id", unique=True, postgresql_where=text("situacao IN ('pending', 'running')"))` em `Execution.__table_args__` (`src/app/models.py`); criada a revisão Alembic `4d0fd0aa498e` (`down_revision="f3b60ce4f7f4"`), no estilo das revisões existentes; `tests/test_app_migrations.py` ganhou asserção via `inspetor.get_indexes("executions")` (nome, coluna, unicidade, predicado parcial).
  - [x] **VERIFY**: `APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test uv run alembic upgrade head` → exit 0 (`f3b60ce4f7f4 -> 4d0fd0aa498e`); `alembic current` → `4d0fd0aa498e (head)`; `uv run pytest tests/test_app_migrations.py -v` → 1 passed.
  - [x] **VISUAL**: Não aplicável — migration de schema, sem superfície visual.
  - [x] **EVIDENCE**: Comandos e resultados acima; `docs/` reconstruído por `$specsfy-documentator` (`--check` → exit 0); `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT` (adicionar um índice a uma tabela existente não muda história/finalidade/capacidades/limites de `PROJECT.md`).
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária — migration mínima, no padrão já estabelecido pelas duas revisões anteriores.
  <!-- specsfy:evidence {"task":"T005","refs":["US-001","FR-001","NFR-001","AC-001","AC-002","AC-003"],"files":["src/app/models.py","alembic/versions/4d0fd0aa498e_indice_unico_execucao_ativa_por_base.py","tests/test_app_migrations.py"],"commands":[{"run":"APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test uv run alembic upgrade head","exit":0},{"run":"APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test uv run alembic current","exit":0},{"run":"uv run pytest tests/test_app_migrations.py -v","exit":0}]} -->

- [x] T006 [CODE] [US-001] Adicionar função compartilhada de insert com conversão seletiva da unique violation em 409 estruturado em src/app/repo.py — Refs: US-001, FR-001, FR-002, FR-003, AC-001, AC-002, AC-003, AC-004 — Depends: T005
  - [x] **PREP**: RED de T001–T004 reconfirmado com o índice já aplicado (T005) — agora a violação de integridade acontece (`IntegrityError`/SQLSTATE 23505), mas ainda propaga sem tratamento. Lidos `src/app/repo.py` (padrão de funções existentes) e `src/app/routers/executions.py` (uso atual de `has_active_execution`). Confirmado via script manual que `error.orig.sqlstate`/`error.orig.diag.constraint_name` (psycopg 3) expõem exatamente `"23505"`/`"uq_executions_base_active"`.
  - [x] **EXECUTE**: Adicionada `repo.inserir_execucao_ativa(session, base_id, *, situacao="pending", etapa="agendado") -> Execution`: insere e commita; em `IntegrityError`, faz `session.rollback()` e só converte em `HTTPException(409, detail={"execution_id", "situacao"})` quando SQLSTATE é `23505` **e** a constraint é `uq_executions_base_active` **e** a releitura encontra a execução ativa — qualquer outro caso propaga sem modificação. Função única, ainda não chamada pelos endpoints (isso é T007).
  - [x] **VERIFY**: Verificação unitária da função isolada (script manual, duas sessões reais): primeira chamada insere `pending`; segunda chamada para a mesma base levanta `HTTPException(409, detail={"execution_id": <id da primeira>, "situacao": "pending"})`. `uv run ruff check src/app/repo.py` → limpo. Os testes HTTP fim-a-fim (`test_corrida_real_*`) continuam RED nesta tarefa — esperado, porque os endpoints ainda fazem o insert direto (T007 os conecta à função nova); GREEN completo fica registrado em T007.
  - [x] **VISUAL**: Não aplicável — sem superfície visual.
  - [x] **EVIDENCE**: Verificação unitária e Ruff registrados acima; `docs/` confirmado atual (`build_documentation.mjs --check` → exit 0); `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT` (função nova em módulo interno, sem mudança de contrato público ainda).
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.
  <!-- specsfy:evidence {"task":"T006","refs":["US-001","FR-001","FR-002","FR-003","AC-001","AC-002","AC-003","AC-004"],"files":["src/app/repo.py"],"commands":[{"run":"uv run ruff check src/app/repo.py","exit":0}]} -->

- [x] T007 [CODE] [US-001] Usar repo.inserir_execucao_ativa nos dois endpoints e estruturar o 409 otimista em src/app/routers/executions.py — Refs: US-001, FR-001, FR-002, FR-003, AC-004 — Depends: T006
  - [x] **PREP**: RED de T004 reconfirmado (formato do `detail` ainda era string). Lidos `iniciar_execucao` e `repetir_execucao` (`src/app/routers/executions.py`).
  - [x] **EXECUTE**: Adicionado `_detail_execucao_ativa(session, base_id)` (reaproveita `repo.list_executions_for_base`) para estruturar o 409 do check otimista de `has_active_execution` no formato `{"execution_id", "situacao"}`. Substituído o insert direto de `Execution` por `repo.inserir_execucao_ativa(session, base_id)` em `iniciar_execucao` e `repetir_execucao`, cobrindo também a corrida real (FR-003).
  - [x] **VERIFY**: `uv run ruff check .` → limpo. `uv run pytest tests/test_app_executions.py -v` → 10 passed (T001–T004, `test_impede_execucao_concorrente` original e os 6 testes pré-existentes da fatia).
  - [x] **VISUAL**: Não aplicável — resposta HTTP de erro, sem tela associada; frontend não muda (decisão confirmada, seção 2).
  - [x] **EVIDENCE**: Comandos e resultados acima; `docs/` reconstruído (`build_documentation.mjs --check` → exit 0); `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT` (estruturar um corpo de erro não muda história/finalidade/capacidades/limites de `PROJECT.md`).
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.
  <!-- specsfy:evidence {"task":"T007","refs":["US-001","FR-001","FR-002","FR-003","AC-004"],"files":["src/app/routers/executions.py"],"commands":[{"run":"uv run pytest tests/test_app_executions.py -v","exit":0}]} -->

- [x] T008 [DOC] Atualizar .specsfy/DATABASE.md com o índice único parcial de executions — Refs: FR-001 — Depends: T005
  - [x] **PREP**: Lido `.specsfy/DATABASE.md` (curado manualmente neste projeto, `.specsfy/RULES.md`) e a migration de T005.
  - [x] **EXECUTE**: Registrado manualmente o índice único parcial `uq_executions_base_active` (`base_id`, filtrado por `situacao IN ('pending','running')`) na linha da tabela `executions` de `.specsfy/DATABASE.md`, com a origem (SPEC-0015, revisão `4d0fd0aa498e`).
  - [x] **VERIFY**: Revisão visual do arquivo confirmando a entrada nova, consistente com `src/app/models.py::Execution.__table_args__` e a migration `4d0fd0aa498e`.
  - [x] **VISUAL**: Não aplicável — documentação, sem superfície visual.
  - [x] **EVIDENCE**: Trecho adicionado registrado acima (linha da tabela `executions`).
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

**Checkpoint**: rodar os quatro testes de T001–T004 mais
`test_impede_execucao_concorrente` original — todos GREEN demonstram a
história isoladamente, sem depender de outra fatia.

#### Fase final — Qualidade

- [x] T009 [TEST] Executar regressão completa e rastreabilidade em tests/test_app_executions.py e tests/test_app_migrations.py — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-001, AC-002, AC-003, AC-004 — Depends: T007, T008
  - [x] **PREP**: Suítes identificadas (Ruff, Pytest completo, rastreabilidade). SPEC-0016/SPEC-0017 (BACKLOG-0020/0021) já mergeadas na `main` e sincronizadas nesta branch (PR #10) — `check_traceability.mjs` já namespaceia por spec, sem misturar marcadores de outras specs.
  - [x] **EXECUTE**: `uv run ruff check .`; `uv run pytest -q`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md .`.
  - [x] **VERIFY**: Ruff limpo. `317 passed, 1 skipped` (313 pré-existentes + 4 desta fatia, sem regressão). `check_traceability.mjs` → `Namespace: SPEC-0015; modo: namespaced. Rastreabilidade: 9/9 IDs cobertos em 49 arquivos de teste. RESULTADO: OK`.
  - [x] **VISUAL**: Não aplicável — item de regressão/rastreabilidade, sem superfície visual.
  - [x] **EVIDENCE**: Comandos e resultados acima registrados nas seções 11–13.
  - [x] **IMPROVE**: `test_impede_execucao_concorrente` original foi mantido como caso adicional (não removido) — continua GREEN, cobrindo o mesmo caminho sequencial com asserção mais simples que `test_execucao_ativa_commitada_rejeita_sequencial`.
  <!-- specsfy:evidence {"task":"T009","refs":["US-001","FR-001","FR-002","FR-003","NFR-001","AC-001","AC-002","AC-003","AC-004"],"files":["tests/test_app_executions.py","tests/test_app_migrations.py"],"commands":[{"run":"uv run ruff check .","exit":0},{"run":"uv run pytest -q","exit":0},{"run":"node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md .","exit":0}]} -->

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
- BACKLOG-0020 (`namespacear-marcadores-specsfy-por-spec`) entregue antes de
  T009 e do Delivery Gate, pois o auditor atual mistura IDs locais de specs
  diferentes e falha com marcadores órfãos.

#### Riscos

- Ambiente com dado já inconsistente faria a migration falhar ao criar o
  índice → mitigação: preflight somente leitura lista as bases conflitantes e
  interrompe a aplicação antes de DDL; nenhuma limpeza automática pertence a
  esta spec.
- Testes com threads podem oscilar ou deixar sessão aberta → mitigação:
  `threading.Barrier` e `Future.result()` com timeout explícito, sem `sleep`;
  o executor aguarda o encerramento das duas chamadas.
- O auditor de rastreabilidade atual mistura IDs de specs diferentes →
  mitigação: BACKLOG-0020 é dependência explícita de T009 e do Delivery Gate.

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

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
