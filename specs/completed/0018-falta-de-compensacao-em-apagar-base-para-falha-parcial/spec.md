# Especificação integrada: Falta de compensação em apagar_base para falha parcial

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0018 |
| Slug | 0018-falta-de-compensacao-em-apagar-base-para-falha-parcial |
| Status | Complete |
| Effort | 3 |
| Effort updated at | 2026-09-15 |
| Effort rationale | Correção localizada em um único endpoint (`src/app/routers/bases.py`), sem migration, sem mudança de schema ou de frontend. Exige reordenar chamadas já existentes e cobrir cinco cenários de falha/retentativa com monkeypatch de storage e vector store contra o banco de teste real. Perfil `standard`. |
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

`apagar_base` (`src/app/routers/bases.py`) commita o soft-delete no Postgres
(`apagada_em`, remoção de `Execution`/`Query`) **antes** de chamar
`storage.delete_base` e `service.delete_scope`. Se qualquer um dos dois
externos falhar depois desse commit, a exceção propaga (HTTP 500,
comportamento inalterado hoje), mas a base já ficou invisível —
`repo.get_base_or_404` a exclui de qualquer listagem, detalhe ou nova
tentativa de exclusão pelo mesmo `base_id` — enquanto o storage e/ou os
vetores no vector store continuam existindo, órfãos, sem qualquer forma de
retomar a limpeza. Achado original registrado em
`specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md`, seção
16, como "Não corrigido, registrado para spec/backlog futuro".

#### Resultado desejado

Nenhum recurso (storage ou vetores) fica órfão permanentemente após uma
falha parcial em `apagar_base`. Uma falha em `storage.delete_base` ou
`service.delete_scope` é sempre recuperável repetindo a mesma chamada
`DELETE /api/v1/bases/{base_id}`, sem endpoint, job ou fluxo adicional — o
Postgres só muda de estado depois que os dois externos tiverem sucesso.

#### Métricas de sucesso

- 0 execuções de `apagar_base` deixam a base soft-deletada no Postgres
  quando `storage.delete_base` ou `service.delete_scope` falha.
- 100% das falhas parciais simuladas (storage, vector store, ou falhas
  sucessivas nos dois em tentativas diferentes) são recuperáveis repetindo o
  mesmo `DELETE`, sem efeito colateral adicional no que já foi apagado.

### 2. Research e esclarecimentos

#### Researchs executados

- Nenhuma claim técnica externa. Este research confirmou apenas
  comportamento do código local: `LocalDirectoryStorage.delete_base` checa
  `pasta.exists()` antes de `shutil.rmtree` (`src/app/storage.py:51-54`);
  `S3CompatibleStorage.delete_base` itera objetos existentes por prefixo e só
  apaga os encontrados (`src/app/storage.py:84-88`); `service.delete_scope`
  lista IDs do escopo e só chama `delete_ids` se houver algum
  (`src/pipeline/service.py:175-192`). Os três já são idempotentes: repetir a
  chamada depois de uma falha parcial não gera erro nem duplica efeito sobre
  o que já foi apagado.

#### Fontes e contexto consultados

- `specs/backlog/0019-falta-de-compensacao-em-apagar-base-para-falha-parcial.md`: brief de origem, com todas as decisões já confirmadas pelo usuário.
- `specs/inbox/2026-09-15-133813-falta-de-compensacao-em-apagar-base-para-falha-parcial.md`: captura original.
- `specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md:1233`: achado original, "Não corrigido, registrado para spec/backlog futuro".
- `specs/milestones/M02.md`: item listado em "Fora de escopo" como dívida técnica sem milestone.
- `specs/completed/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md`: spec irmã (mesma origem, mesmo módulo `src/app`), decidida como spec separada por não exigir migration.
- Código atual: `src/app/routers/bases.py` (`apagar_base`, ordem atual: commit do soft-delete antes dos dois externos), `src/app/storage.py` (`LocalDirectoryStorage.delete_base`, `S3CompatibleStorage.delete_base`), `src/pipeline/service.py` (`delete_scope`), `src/app/repo.py` (`get_base_or_404`, exclui bases com `apagada_em` não nulo), `src/app/models.py` (`Base.apagada_em`), `tests/test_app_bases.py` (`test_apagar_base_remove_conteudo`, `test_apagar_base_remove_pontos_vector_store` — cobrem hoje só o caminho feliz), `tests/conftest.py` (banco de teste real `rag_pipeline_test`, fixture `vector_store_em_memoria`).
- `frontend/`: `ExcluirBaseDialog.tsx` já orienta a pessoa a "tentar novamente" em caso de erro — texto que hoje não resolve o problema (base já invisível) e passa a funcionar de verdade com esta correção, sem qualquer mudança de frontend.
- `.specsfy/RULES.md`: proteção do banco de desenvolvimento (testes usam `rag_pipeline_test`, nunca o banco de desenvolvimento).

#### Documentação consultada

- Nenhuma documentação externa consultada.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Reordenar as chamadas, criar endpoint de retry dedicado, ou job de
  reconciliação em segundo plano? → **A**: Reordenar `apagar_base` — apagar
  storage e vector store antes de commitar o soft-delete — porque os dois
  externos já são idempotentes e não exige infraestrutura nova. Decisão
  confirmada no refinamento do BACKLOG-0019.
- **Q**: O frontend precisa de um endpoint ou fluxo de retry novo? → **A**:
  Não; `ExcluirBaseDialog.tsx` já orienta "tente novamente", que passa a
  funcionar de verdade repetindo o mesmo `DELETE` — decisão confirmada.
- **Q**: Esta correção deve ficar na mesma spec do BACKLOG-0018 (corrida em
  `has_active_execution`)? → **A**: Não; specs separadas — BACKLOG-0018 exige
  migration (índice único), esta não. Decisão confirmada no refinamento
  cruzado dos dois backlogs (ver SPEC-0015, DEC-004).
- **Q**: Qual a prioridade? → **A**: Alta — mesmo nível do BACKLOG-0018,
  ambos originados do fechamento do M02 como dívida técnica sem milestone.

#### Dúvidas abertas

- Nenhuma bloqueante para a definição.

### 3. Escopo e atores

#### Incluído

- Reordenar `apagar_base` (`src/app/routers/bases.py`): apagar storage
  (`storage.delete_base`) e vector store (`service.delete_scope`) antes de
  abrir a sessão que commita o soft-delete no Postgres (`apagada_em`, remoção
  de `Execution`/`Query`).
- Testes cobrindo falha em `storage.delete_base` isolada, falha em
  `service.delete_scope` isolada, e falhas sucessivas nos dois em tentativas
  diferentes, e a retentativa (repetir o mesmo `DELETE`) completando a
  exclusão em cada um desses três cenários, sempre confirmando que o
  Postgres não muda de estado enquanto a falha persistir.

#### Fora de escopo

- Qualquer mudança no frontend — decisão confirmada; `ExcluirBaseDialog.tsx`
  já orienta "tente novamente".
- Endpoint de retry dedicado — decisão confirmada; retry é simplesmente
  repetir o mesmo `DELETE`.
- Job de reconciliação em segundo plano — decisão confirmada.
- Spec conjunta com BACKLOG-0018/SPEC-0015 — decisão confirmada; specs
  separadas, uma exige migration e a outra não.
- Qualquer mudança em `storage.py`, `service.py` ou `repo.py` — os três
  comportamentos usados (idempotência dos deletes externos,
  `get_base_or_404`) já são adequados e permanecem inalterados.

#### Atores

- **Pessoa operadora** (papel `owner` ou `admin`, única com permissão de
  apagar base via `require_write_role`, ver `ExcluirBaseDialog.tsx`): chama
  `DELETE /api/v1/bases/{base_id}`; hoje pode ficar com storage e vetores
  órfãos permanentemente se um dos dois externos falhar depois do commit.
- **Integração técnica**: chama o mesmo endpoint diretamente, sem passar
  pelo frontend; sujeita ao mesmo comportamento.

### 4. Princípios e restrições do projeto

- **PR-001**: `src/app/` importa somente `src/pipeline/service.py`; esta
  correção não toca `src/pipeline/` nem amplia a fronteira (SPEC-0008,
  `tests/test_application_boundaries.py`).
- **PR-002**: testes executam exclusivamente contra o banco de teste
  `rag_pipeline_test` (`tests/conftest.py`); nenhum teste desta spec usa o
  banco de desenvolvimento (`.specsfy/RULES.md`, proteção do banco).
- **PR-003**: nenhuma mudança de superfície de autorização — `require_write_role`
  permanece a única verificação de permissão do endpoint.
- **PR-004**: nenhum segredo é exposto em resposta HTTP ou log — a correção
  só reordena chamadas já existentes, sem novo campo de resposta.

### 5. Histórias de usuário

#### US-001 — Recuperar uma exclusão de base que falhou parcialmente repetindo o mesmo DELETE (P1)

Como pessoa operadora (owner/admin) ou integração técnica, quero que uma
falha em `storage.delete_base` ou `service.delete_scope` durante
`apagar_base` nunca deixe a base invisível com storage/vetores órfãos, para
que eu sempre consiga concluir a exclusão simplesmente repetindo a mesma
chamada `DELETE`, sem precisar de suporte ou de um fluxo adicional.

**Por que P1**: bug de integridade de dados real — hoje uma falha parcial
deixa recursos órfãos permanentemente, sem forma de correção, mesmo que a
pessoa tente "apagar de novo" pela mesma tela.
**Teste independente**: contra o banco de teste real (`rag_pipeline_test`),
forçar `storage.delete_base` e/ou `service.delete_scope` a lançar exceção na
primeira chamada e confirmar que o Postgres não muda de estado; repetir a
mesma chamada `DELETE` sem a falha forçada e confirmar que a exclusão
completa com sucesso.
**Requisitos**: FR-001, FR-002, FR-003

### 6. Cenários BDD de aceite

#### AC-001 — Caminho feliz preservado (regressão)

**Cobre**: US-001, FR-001

```gherkin
@US-001 @FR-001 @AC-001
Feature: Exclusão de base sem falha parcial

  Scenario: Storage e vector store apagados com sucesso
    Given uma base existente com execuções e consultas indexadas
    When DELETE /api/v1/bases/{base_id} é chamado e storage.delete_base e
      service.delete_scope têm sucesso
    Then o Postgres commita o soft-delete (apagada_em preenchido, Execution
      e Query removidos) e a base passa a ser invisível
    And a resposta é HTTP 204, igual ao comportamento atual
```

#### AC-002 — Falha isolada em storage.delete_base não altera o Postgres

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-002
Feature: Falha parcial em apagar_base

  Scenario: storage.delete_base falha antes de qualquer escrita no Postgres
    Given uma base existente com execuções e consultas indexadas
    When DELETE /api/v1/bases/{base_id} é chamado e storage.delete_base
      lança uma exceção
    Then a chamada responde HTTP 500 e a exceção original é propagada
    And o Postgres não muda de estado: apagada_em continua nulo e Execution
      e Query da base continuam presentes
```

#### AC-003 — Falha isolada em service.delete_scope não altera o Postgres

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-003
Feature: Falha parcial em apagar_base

  Scenario: service.delete_scope falha depois do storage já ter sido apagado
    Given uma base existente com execuções e consultas indexadas
    When DELETE /api/v1/bases/{base_id} é chamado, storage.delete_base tem
      sucesso e service.delete_scope lança uma exceção
    Then a chamada responde HTTP 500 e a exceção original é propagada
    And o Postgres não muda de estado: apagada_em continua nulo e Execution
      e Query da base continuam presentes
```

#### AC-004 — Repetir o DELETE após falha no storage completa a exclusão

**Cobre**: US-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-002 @FR-003 @NFR-001 @AC-004
Feature: Retentativa de apagar_base após falha parcial

  Scenario: Segunda chamada sem a falha forçada conclui a exclusão
    Given uma primeira chamada a DELETE /api/v1/bases/{base_id} que falhou
      porque storage.delete_base lançou uma exceção, sem alterar o Postgres
    When a mesma chamada DELETE /api/v1/bases/{base_id} é repetida e
      storage.delete_base e service.delete_scope têm sucesso desta vez
    Then a resposta é HTTP 204 e o Postgres commita o soft-delete, sem erro
      nem efeito colateral adicional causado pela primeira tentativa
```

#### AC-005 — Repetir o DELETE após falha no vector store completa a exclusão

**Cobre**: US-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-002 @FR-003 @NFR-001 @AC-005
Feature: Retentativa de apagar_base após falha parcial

  Scenario: Segunda chamada sem a falha forçada conclui a exclusão
    Given uma primeira chamada a DELETE /api/v1/bases/{base_id} que falhou
      porque service.delete_scope lançou uma exceção depois do storage já
      apagado, sem alterar o Postgres
    When a mesma chamada DELETE /api/v1/bases/{base_id} é repetida e
      service.delete_scope tem sucesso desta vez
    Then a resposta é HTTP 204 e o Postgres commita o soft-delete, sem erro
      causado por storage.delete_base rodar de novo sobre um diretório já
      removido (idempotência confirmada em research)
```

#### AC-006 — Falhas sucessivas em chamadas diferentes continuam recuperáveis até a exclusão completar

**Cobre**: US-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-002 @FR-003 @NFR-001 @AC-006
Feature: Retentativa de apagar_base após falhas parciais sucessivas

  Scenario: Três chamadas seguidas, cada uma resolvendo a falha da anterior, concluem a exclusão
    Given uma primeira chamada a DELETE /api/v1/bases/{base_id} em que
      storage.delete_base lança exceção, sem alterar o Postgres
    And uma segunda chamada, sem a falha do storage, em que
      service.delete_scope lança exceção, também sem alterar o Postgres
    When a mesma chamada DELETE /api/v1/bases/{base_id} é repetida uma
      terceira vez e os dois externos têm sucesso
    Then a terceira resposta é HTTP 204 e o Postgres commita o soft-delete,
      sem erro nem duplicação de efeito sobre o que já foi apagado pelas
      tentativas anteriores
```

### 7. Requisitos

#### Funcionais

- **FR-001**: `apagar_base` deve chamar `storage.delete_base` e
  `service.delete_scope` antes de abrir a sessão que commita o soft-delete
  no Postgres (`apagada_em`, remoção de `Execution`/`Query`).
- **FR-002**: Se `storage.delete_base` ou `service.delete_scope` lançar uma
  exceção, o Postgres não deve mudar de estado — a base continua visível e
  ativa (sem `apagada_em`, sem remover `Execution`/`Query`) e a exceção
  original propaga (HTTP 500).
- **FR-003**: Repetir a mesma chamada `DELETE /api/v1/bases/{base_id}` após
  uma falha parcial deve completar a exclusão com sucesso quando os externos
  não falharem na nova tentativa, sem endpoint, parâmetro ou fluxo adicional.

#### Não funcionais

- **NFR-001**: Idempotência da retentativa — repetir `DELETE` qualquer
  número de vezes após uma falha parcial não gera erro adicional nem duplica
  efeito sobre o que já foi apagado, apoiada na idempotência já existente de
  `LocalDirectoryStorage.delete_base`, `S3CompatibleStorage.delete_base` e
  `service.delete_scope`. **Verificação**: testes automatizados que chamam
  `DELETE` duas vezes seguidas para a mesma base após cada tipo de falha
  parcial (AC-004, AC-005, AC-006).

#### Erros e casos-limite

- `storage.delete_base` falha → HTTP 500, Postgres inalterado, repetir o
  `DELETE` reexecuta os dois passos (AC-002, AC-004).
- `service.delete_scope` falha (storage já removido) → HTTP 500, Postgres
  inalterado; repetir o `DELETE` chama `storage.delete_base` de novo sobre um
  diretório/prefixo já vazio (no-op idempotente) e conclui com sucesso
  (AC-003, AC-005).
- Falhas sucessivas em chamadas diferentes (storage na primeira tentativa,
  vector store na segunda) → cada tentativa recebe HTTP 500 sem alterar o
  Postgres; a terceira chamada, sem falha forçada, conclui a exclusão com
  sucesso (AC-006).
- Base já apagada (`apagada_em` preenchido) → `get_base_or_404` continua
  respondendo 404, sem mudança nesta spec (comportamento existente,
  inalterado, fora do escopo desta correção).

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

FastAPI + SQLAlchemy + PostgreSQL (`src/app/`). `apagar_base`
(`src/app/routers/bases.py:161-189`) hoje abre uma sessão, apaga
`Execution`/`Query`, marca `apagada_em` e faz `commit()` antes de chamar
`get_storage().delete_base(base_id)` e `service.delete_scope(config)` — os
dois externos rodam depois do commit, sem qualquer bloco de compensação.
`get_base_or_404` (`src/app/repo.py:27-36`) já exclui bases com `apagada_em`
não nulo de qualquer leitura, inclusive uma nova chamada `DELETE` para o
mesmo `base_id`. `LocalDirectoryStorage.delete_base` e
`S3CompatibleStorage.delete_base` (`src/app/storage.py`) e
`service.delete_scope` (`src/pipeline/service.py:175-192`) já são
idempotentes (confirmado em research).

#### Arquitetura e módulos

- `src/app/routers/bases.py`: `apagar_base` reordenado em três passos —
  (1) uma primeira sessão somente-leitura confirma a base via
  `repo.get_base_or_404` (autorização e existência, sem escrita); (2) fora de
  qualquer sessão, chama `get_storage().delete_base(base_id)` e depois monta
  o `config` e chama `service.delete_scope(config)`, exatamente como hoje;
  (3) só depois dos dois externos terem sucesso, uma segunda sessão relê a
  base (`repo.get_base_or_404`), remove `Execution`/`Query`, marca
  `apagada_em`/`nome=""` e commita. Se o passo (2) lançar exceção, nenhuma
  sessão de escrita é aberta e a exceção propaga sem tocar o Postgres.
- Nenhuma mudança em `src/app/storage.py`, `src/pipeline/service.py` ou
  `src/app/repo.py` — os três comportamentos usados já são adequados.

#### Migrations

- Não aplicável — nenhuma mudança de schema.

#### Models

- Não aplicável — `Base`, `Execution` e `Query` permanecem inalterados.

#### Controllers e casos de uso

- `apagar_base` (`src/app/routers/bases.py`): única função alterada;
  autorização inalterada (`require_write_role`).

#### Views e experiência

- Não aplicável — sem interface para pessoas (ver seção 10).

#### Queries e repositórios

- `repo.get_base_or_404` reaproveitado sem alteração, chamado duas vezes
  (leitura inicial e releitura antes do commit final) — nenhuma query nova.

#### Jobs e processamento assíncrono

- Não aplicável — `process_base_task` (`src/app/tasks.py`) não é tocado por
  esta correção.

#### Estrutura de arquivos

```text
specs/draft/0018-falta-de-compensacao-em-apagar-base-para-falha-parcial/
  spec.md
  research/
src/app/routers/bases.py
tests/test_app_bases.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `Base` | `id` (UUID) | `apagada_em` só é preenchido depois que `storage.delete_base` e `service.delete_scope` tiverem sucesso (invariante novo; schema inalterado) | 1:N com `Execution`, `Query` |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| `Base` | ativa (`apagada_em` nulo) | `DELETE`, storage e vector store com sucesso | apagada (`apagada_em` preenchido, `Execution`/`Query` removidos) | Postgres só muda depois dos dois externos terem sucesso |
| `Base` | ativa (`apagada_em` nulo) | `DELETE`, storage ou vector store falha | ativa (sem mudança) | exceção propaga; Postgres permanece exatamente como estava |

#### Migração e retenção

- Não aplicável — sem migração de dados existentes, sem mudança de schema.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A correção é inteiramente de backend
  (reordenar duas chamadas já existentes dentro de um endpoint já existente).
  `ExcluirBaseDialog.tsx` (frontend, SPEC-0013) já orienta "tente novamente"
  em caso de erro — esse texto passa a funcionar de verdade com esta
  correção, sem qualquer mudança de tela, componente ou fluxo visual
  (decisão confirmada no refinamento do BACKLOG-0019).

#### APIs expostas

- `DELETE /api/v1/bases/{base_id}` (já existente,
  `src/app/routers/bases.py`): contrato inalterado — HTTP 204 no sucesso,
  exceção propagada (HTTP 500) na falha parcial, sem novo campo de request
  ou response. A diferença observável está apenas no estado resultante do
  Postgres e na possibilidade real de recuperação por retentativa.

#### APIs externas utilizadas

- Nenhuma nova; `storage.delete_base` e `service.delete_scope` já eram
  chamados por este endpoint.

#### Documentação das APIs consultadas

- Nenhuma.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: não aplicável isoladamente — o comportamento só é observável
  pela combinação sessão HTTP + Postgres real + storage + vector store, por
  isso todos os casos são de integração.
- **Integração/contrato**: `apagar_base` exercitado via `TestClient` HTTP
  contra `rag_pipeline_test`, com `storage.delete_base`
  (`src/app/storage.py`, instância retornada por `get_storage()`) e
  `service.delete_scope` (`src/pipeline/service.py`) substituídos por
  `unittest.mock.Mock(side_effect=...)` para forçar cada combinação de
  falha/sucesso descrita nos AC-002 a AC-006. `TestClient(app,
  raise_server_exceptions=False)` permite observar o HTTP 500 real em vez de
  deixar a exceção propagar para o teste.
- **BDD/aceite**: cenários da seção 6 (AC-001 a AC-006) orientam o desenho
  dos casos TDD abaixo.
- **Runner TDD**: Pytest (projeto Python, `.specsfy/RULES.md`).
- **E2E**: não aplicável — os testes já exercitam o endpoint HTTP real
  contra o banco real; não há jornada de múltiplas telas envolvida.
- **Verificação manual**: nenhuma prevista; o comportamento inteiro é
  verificável por teste automatizado contra `rag_pipeline_test`.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, AC-001 | AC-001 na seção 6 | `tests/test_app_bases.py::test_apagar_base_remove_conteudo` e `test_apagar_base_remove_pontos_vector_store` (já existentes) | Não aplicável — comportamento de caminho feliz inalterado; testes já GREEN antes desta spec, usados como regressão da nova ordem | `uv run pytest tests/test_app_bases.py -k 'remove_conteudo or remove_pontos_vector_store' -v` → 2 passed, GREEN (2026-09-15) | `uv run pytest -q` (suíte completa) → sem regressão |
| US-001, FR-001, FR-002, AC-002 | AC-002 na seção 6 | `tests/test_app_bases.py::test_apagar_base_falha_no_storage_nao_altera_postgres` com marcador `SPECSFY: SPEC-0018 US-001 FR-001 FR-002 AC-002` | `uv run pytest tests/test_app_bases.py::test_apagar_base_falha_no_storage_nao_altera_postgres -v` → `AssertionError: assert datetime.datetime(...) is None` (soft-delete já commitado); RED válido em 2026-09-15 | `uv run pytest tests/test_app_bases.py -v` → 13 passed, GREEN (2026-09-15) | `uv run pytest -q` (suíte completa) → sem regressão |
| US-001, FR-001, FR-002, AC-003 | AC-003 na seção 6 | `tests/test_app_bases.py::test_apagar_base_falha_no_vector_store_nao_altera_postgres` com marcador `SPECSFY: SPEC-0018 US-001 FR-001 FR-002 AC-003` | Mesmo comando → mesma causa: `apagada_em` já preenchido antes de `service.delete_scope` ser chamado; RED válido em 2026-09-15 | `uv run pytest tests/test_app_bases.py -v` → 13 passed, GREEN (2026-09-15) | `uv run pytest -q` (suíte completa) → sem regressão |
| US-001, FR-002, FR-003, NFR-001, AC-004 | AC-004 na seção 6 | `tests/test_app_bases.py::test_apagar_base_repete_apos_falha_no_storage_completa` com marcador `SPECSFY: SPEC-0018 US-001 FR-002 FR-003 NFR-001 AC-004` | Mesmo comando → 2ª chamada retornou 404 (base já invisível pela 1ª), diferente do 204 esperado; RED válido em 2026-09-15 | `uv run pytest tests/test_app_bases.py -v` → 13 passed, GREEN (2026-09-15) | `uv run pytest -q` (suíte completa) → sem regressão |
| US-001, FR-002, FR-003, NFR-001, AC-005 | AC-005 na seção 6 | `tests/test_app_bases.py::test_apagar_base_repete_apos_falha_no_vector_store_completa` com marcador `SPECSFY: SPEC-0018 US-001 FR-002 FR-003 NFR-001 AC-005` | Mesmo comando → 2ª chamada retornou 404, mesma causa de AC-004; RED válido em 2026-09-15 | `uv run pytest tests/test_app_bases.py -v` → 13 passed, GREEN (2026-09-15) | `uv run pytest -q` (suíte completa) → sem regressão |
| US-001, FR-002, FR-003, NFR-001, AC-006 | AC-006 na seção 6 | `tests/test_app_bases.py::test_apagar_base_repete_apos_falhas_sucessivas_completa` com marcador `SPECSFY: SPEC-0018 US-001 FR-002 FR-003 NFR-001 AC-006` | Mesmo comando → 2ª chamada retornou 404, mesma causa de AC-004/AC-005 (teste nem chega à 3ª chamada); RED válido em 2026-09-15 | `uv run pytest tests/test_app_bases.py -v` → 13 passed, GREEN (2026-09-15) | `uv run pytest -q` (suíte completa) → sem regressão |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração (banco real, regressão) | `uv run pytest tests/test_app_bases.py -k 'remove_conteudo or remove_pontos_vector_store' -v` | Passed (2026-09-15) |
| FR-001, FR-002 | AC-002 | Integração (banco real) | `uv run pytest tests/test_app_bases.py::test_apagar_base_falha_no_storage_nao_altera_postgres -v` | Passed (2026-09-15) |
| FR-001, FR-002 | AC-003 | Integração (banco real) | `uv run pytest tests/test_app_bases.py::test_apagar_base_falha_no_vector_store_nao_altera_postgres -v` | Passed (2026-09-15) |
| FR-002, FR-003, NFR-001 | AC-004 | Integração (banco real) | `uv run pytest tests/test_app_bases.py::test_apagar_base_repete_apos_falha_no_storage_completa -v` | Passed (2026-09-15) |
| FR-002, FR-003, NFR-001 | AC-005 | Integração (banco real) | `uv run pytest tests/test_app_bases.py::test_apagar_base_repete_apos_falha_no_vector_store_completa -v` | Passed (2026-09-15) |
| FR-002, FR-003, NFR-001 | AC-006 | Integração (banco real) | `uv run pytest tests/test_app_bases.py::test_apagar_base_repete_apos_falhas_sucessivas_completa -v` | Passed (2026-09-15) |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0018-falta-de-compensacao-em-apagar-base-para-falha-parcial/spec.md --allow-draft` → `VALID DRAFT`.
- **Cobertura mínima**: US-001 (6 AC), FR-001 (3 AC), FR-002 (5 AC), FR-003 (3 AC), NFR-001 (3 AC) — todos ≥ 3, conforme MCR-10.
- **Revisão semântica (2026-09-15)**: aplicadas as lentes `PROD` e `ARCH`
  (`references/review-lenses.md`), materiais por tratar de integridade
  transacional entre Postgres e dois serviços externos idempotentes; `SEC`
  avaliada e considerada não material — sem mudança de autenticação,
  autorização ou exposição de dado novo (`require_write_role` inalterado,
  corpo de resposta do 500 não muda). Nenhum achado `P1 Open`: os princípios
  PR-001–PR-004 aparecem no desenho das seções 8–10, os caminhos citados
  existem no repositório (`src/app/routers/bases.py`, `src/app/storage.py`,
  `src/pipeline/service.py`, `tests/test_app_bases.py`), e a ausência de
  migration/rollback está justificada (seção 8, "Migrations"). `node
  .agents/skills/specsfy-04-validate/scripts/review_findings.mjs
  specs/draft/0018-falta-de-compensacao-em-apagar-base-para-falha-parcial/spec.md`
  → `Reviews: PASSED` (nenhum achado registrado, nenhum bloqueio).
- **Achados**: Nenhum `BLOCKER`. Nenhum achado `P1/P2/P3` registrado.

#### Gate do Ato II — Plano

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0018-falta-de-compensacao-em-apagar-base-para-falha-parcial/spec.md` → `VALID DRAFT` (7 tarefas, 6 TDD, 1 CODE, 11/11 IDs cobertos, 30/42 itens de checklist concluídos — T001–T005).
- **Predecessores TDD**: T001–T005 provam RED válido para AC-002–AC-006 contra `rag_pipeline_test` (evidência na seção 11). T006 ([CODE], reordenar `apagar_base`) e T007 (regressão/rastreabilidade) permanecem abertos, aguardando implementação.
- **Achados**: Nenhum bloqueio. O plano está pronto para iniciar T006 sem código de produção.

#### Gate do Ato III — Entrega

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0018-falta-de-compensacao-em-apagar-base-para-falha-parcial/spec.md .` → `Namespace: SPEC-0018; modo: namespaced. Rastreabilidade: 11/11 IDs cobertos em 49 arquivos de teste. RESULTADO: OK`.
- **Tarefas**: 7/7 concluídas (`validate_tasks.mjs` → `READY`, 42/42 itens de checklist).
- **QA**: `verify_acceptance.mjs` → `QA: PASSED` (AC-001–AC-006 todos `Passed`, seção 12).
- **Regressão**: `uv run ruff check .` → limpo. `uv run pytest -q` → 322 passed, 1 skipped (skip pré-existente de SPEC-0014, não relacionado a esta fatia). Sem regressão nos 317 testes anteriores.
- **Documentação**: `docs/` reconstruído por `$specsfy-documentator` (`build_documentation.mjs --project . --check` → exit 0, sem diff — o contrato externo do endpoint não muda com esta correção interna). `monitor_context.mjs --check --acknowledge-project-no-change` ainda reporta `docs/` como pendente pela heurística de diff de git (exige `docs/` entre os caminhos alterados; não existe reconhecimento equivalente ao de `PROJECT.md` para esse caso) — `build_documentation.mjs --check` prova que a documentação já está correta, então nenhuma edição artificial foi feita só para satisfazer a heurística (registrado também em T006/T007).
- **Migration**: Não aplicável — sem mudança de schema nesta spec.
- **Aceite final (`$specsfy-04-validate`, 2026-09-15)**: `validate_spec.mjs` → `READY`; `review_findings.mjs` → `Reviews: PASSED`; `node .agents/skills/specsfy-04-validate/scripts/verify_repo.mjs . --boundary local --timeout-seconds 300 --max-output-bytes 65536` → exit 0, sem `FAIL` em nenhuma spec do repositório. `Delivery Gate: Passed` confirmado; `Status: Complete`.
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

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pytest falhando em tests/test_app_bases.py::test_apagar_base_falha_no_storage_nao_altera_postgres — Refs: US-001, FR-001, FR-002, AC-002 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-002 e o `apagar_base` atual (`src/app/routers/bases.py:161-189`, ordem hoje: commit antes dos externos).
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: SPEC-0018 US-001 FR-001 FR-002 AC-002`, usando `TestClient(app, raise_server_exceptions=False)` e `monkeypatch.setattr(storage_module.get_storage(), "delete_base", falha_no_storage)`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_apagar_base_falha_no_storage_nao_altera_postgres -v` → RED confirmado: `AssertionError: assert datetime.datetime(...) is None` — o Postgres já commitou o soft-delete antes de `storage.delete_base` ser chamado.
  - [x] **VISUAL**: Não aplicável — teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária — teste mínimo, sem mock além do necessário para isolar a falha do storage.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pytest falhando em tests/test_app_bases.py::test_apagar_base_falha_no_vector_store_nao_altera_postgres — Refs: US-001, FR-001, FR-002, AC-003 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-003 e confirmado que `service.delete_scope` é chamado em `apagar_base` via `import src.pipeline.service as service`.
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: SPEC-0018 US-001 FR-001 FR-002 AC-003`, usando a fixture `vector_store_em_memoria` e `monkeypatch.setattr("src.pipeline.service.delete_scope", falha_no_vector_store)`; `storage.delete_base` roda real (no-op sobre diretório inexistente), sem criar ou executar `.feature`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_apagar_base_falha_no_vector_store_nao_altera_postgres -v` → RED confirmado: mesma causa de T001 — o commit já aconteceu antes de `service.delete_scope` ser chamado.
  - [x] **VISUAL**: Não aplicável — teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-004 um caso Pytest falhando em tests/test_app_bases.py::test_apagar_base_repete_apos_falha_no_storage_completa — Refs: US-001, FR-002, FR-003, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-004; confirmado que uma segunda chamada `DELETE` para o mesmo `base_id` hoje recebe 404 assim que o soft-delete da primeira chamada foi commitado (`repo.get_base_or_404` exclui base com `apagada_em` preenchido).
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: SPEC-0018 US-001 FR-002 FR-003 NFR-001 AC-004`, com um wrapper que faz `storage.delete_base` lançar exceção só na 1ª chamada e delegar ao `delete_base` real (não um mock de sucesso) a partir da 2ª — duas chamadas `DELETE` sucessivas, sem criar ou executar `.feature`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_apagar_base_repete_apos_falha_no_storage_completa -v` → RED confirmado: a segunda chamada recebe 404 (base já invisível pela primeira), não 204.
  - [x] **VISUAL**: Não aplicável — teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-005 um caso Pytest falhando em tests/test_app_bases.py::test_apagar_base_repete_apos_falha_no_vector_store_completa — Refs: US-001, FR-002, FR-003, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-005; mesma premissa de T003 aplicada a `service.delete_scope`.
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: SPEC-0018 US-001 FR-002 FR-003 NFR-001 AC-005`, com um wrapper que faz `service.delete_scope` lançar exceção só na 1ª invocação real e delegar ao `delete_scope` real a partir da 2ª — duas chamadas `DELETE` sucessivas, sem criar ou executar `.feature`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_apagar_base_repete_apos_falha_no_vector_store_completa -v` → RED confirmado: a segunda chamada recebe 404 pelo mesmo motivo de T003.
  - [x] **VISUAL**: Não aplicável — teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-006 um caso Pytest falhando em tests/test_app_bases.py::test_apagar_base_repete_apos_falhas_sucessivas_completa — Refs: US-001, FR-002, FR-003, NFR-001, AC-006 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-006; encadeia a falha de storage (T003) na 1ª chamada e a falha de vector store (T004) na 2ª, já sem a primeira falha.
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: SPEC-0018 US-001 FR-002 FR-003 NFR-001 AC-006`, combinando os dois wrappers de T003/T004 (`storage.delete_base` falha só na 1ª chamada; `service.delete_scope` falha só na 1ª vez em que é de fato invocado, ou seja, na 2ª chamada `DELETE`) — três chamadas `DELETE` sucessivas, sem criar ou executar `.feature`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_apagar_base_repete_apos_falhas_sucessivas_completa -v` → RED confirmado: a 2ª chamada recebe 404 pelo mesmo motivo de T003/T004 (o teste nem chega a exercitar a 3ª).
  - [x] **VISUAL**: Não aplicável — teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

#### Fase 2 — US-001 Recuperar uma exclusão de base que falhou parcialmente repetindo o mesmo DELETE (P1)

**Objetivo**: `apagar_base` nunca deixa a base soft-deletada no Postgres
quando `storage.delete_base` ou `service.delete_scope` falha; repetir o
`DELETE` sempre completa a exclusão quando os externos não falharem de novo.
**Teste independente**: T001–T005 e as duas regressões de AC-001 passam
(GREEN) sem depender de outra fatia.

- [x] T006 [CODE] [US-001] Reordenar apagar_base para chamar storage e vector store antes do commit do soft-delete em src/app/routers/bases.py — Refs: US-001, FR-001, FR-002, FR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005
  - [x] **PREP**: RED de T001–T005 reconfirmado (5 falhas ativas). Lido `apagar_base` atual (`src/app/routers/bases.py:161-189`) e a montagem do `config` usado por `service.delete_scope`.
  - [x] **EXECUTE**: Dividida `apagar_base` em: (1) sessão somente-leitura com `repo.get_base_or_404` para autorização/existência; (2) fora de sessão, `get_storage().delete_base(base_id)` seguido da montagem do `config` (inalterada) e `service.delete_scope(config)`; (3) segunda sessão que relê a base, remove `Execution`/`Query`, marca `apagada_em`/`nome=""` e commita — só executada se (2) não lançou exceção.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py -v` → 13 passed (T001–T005 GREEN, `test_apagar_base_remove_conteudo`/`test_apagar_base_remove_pontos_vector_store` continuam GREEN, sem regressão). `uv run pytest tests/test_application_boundaries.py -v` → 5 passed (PR-001, fronteira `src/app/` → `src/pipeline/service.py` preservada). `uv run ruff check src/app/routers/bases.py tests/test_app_bases.py` → limpo.
  - [x] **VISUAL**: Não aplicável — resposta HTTP de erro/sucesso, sem tela associada; frontend não muda (decisão confirmada, seção 2).
  - [x] **EVIDENCE**: Comandos e resultados acima; arquivo alterado: `src/app/routers/bases.py`. `docs/` reconstruído por `$specsfy-documentator` (`build_documentation.mjs --project . --check` → exit 0, sem diff — o contrato externo do endpoint, já documentado em `docs/architecture.md`, não muda com esta correção interna). `monitor_context.mjs --check --acknowledge-project-no-change` → ainda reporta `docs/` pendente pela heurística de diff de git (o script exige que `docs/` apareça entre os caminhos alterados para considerar a documentação atual, e não existe flag de reconhecimento equivalente a `--acknowledge-project-no-change` para esse caso); `build_documentation.mjs --check` confirma que a documentação já está correta sem gerar diff, então nenhuma edição artificial foi feita em `docs/` só para satisfazer a heurística.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária — mudança mínima, sem duplicar a leitura de `get_base_or_404` além do necessário para separar a fase de verificação da fase de escrita.
  <!-- specsfy:evidence {"task":"T006","refs":["US-001","FR-001","FR-002","FR-003","AC-001","AC-002","AC-003","AC-004","AC-005","AC-006"],"files":["src/app/routers/bases.py"],"commands":[{"run":"uv run pytest tests/test_app_bases.py -v","exit":0},{"run":"uv run pytest tests/test_application_boundaries.py -v","exit":0},{"run":"uv run ruff check src/app/routers/bases.py tests/test_app_bases.py","exit":0},{"run":"node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check","exit":0}]} -->

**Checkpoint**: rodar T001–T005 mais `test_apagar_base_remove_conteudo` e
`test_apagar_base_remove_pontos_vector_store` — todos GREEN demonstram a
história isoladamente, sem depender de outra fatia.

#### Fase final — Qualidade

- [x] T007 [TEST] Executar regressão completa e rastreabilidade em tests/test_app_bases.py — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T006
  - [x] **PREP**: Suítes identificadas (Ruff, Pytest completo, rastreabilidade namespaced por spec desde SPEC-0016/SPEC-0017). Auditoria inicial de rastreabilidade apontou 10/11 IDs cobertos: `AC-001` sem teste próprio e `FR-001` com só 2/3 casos, porque os dois testes de regressão do caminho feliz (`test_apagar_base_remove_conteudo`, `test_apagar_base_remove_pontos_vector_store`) só carregavam marcadores do namespace legado (SPEC-0012/SPEC-0013).
  - [x] **EXECUTE**: Adicionado um segundo marcador `SPECSFY: SPEC-0018 US-001 FR-001 AC-001` ao docstring de `test_apagar_base_remove_conteudo` (preservando o marcador legado na mesma docstring), fechando a lacuna de AC-001 e elevando FR-001 para 3/3. Em seguida `uv run ruff check .`; `uv run pytest -q`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0018-falta-de-compensacao-em-apagar-base-para-falha-parcial/spec.md .`.
  - [x] **VERIFY**: Ruff limpo. `322 passed, 1 skipped` (1 skip pré-existente de SPEC-0014, não relacionado a esta fatia; 317 pré-existentes + 5 novos testes de T001–T005, sem regressão — a correção de rastreabilidade só adicionou um marcador a um teste já existente, sem criar teste novo). `check_traceability.mjs` → `Namespace: SPEC-0018; modo: namespaced. Rastreabilidade: 11/11 IDs cobertos em 49 arquivos de teste. RESULTADO: OK`.
  - [x] **VISUAL**: Não aplicável — item de regressão/rastreabilidade, sem superfície visual.
  - [x] **EVIDENCE**: Comandos e resultados acima registrados nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária — a lacuna de rastreabilidade encontrada nesta própria tarefa já foi corrigida dentro dela, sem deixar dívida para trás.
  <!-- specsfy:evidence {"task":"T007","refs":["US-001","FR-001","FR-002","FR-003","NFR-001","AC-001","AC-002","AC-003","AC-004","AC-005","AC-006"],"files":["tests/test_app_bases.py"],"commands":[{"run":"uv run ruff check .","exit":0},{"run":"uv run pytest -q","exit":0},{"run":"node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0018-falta-de-compensacao-em-apagar-base-para-falha-parcial/spec.md .","exit":0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001/T002/T003/T004/T005 (RED) → T006 (reordenar o
  endpoint) → T007 (regressão/rastreabilidade).
- Tarefas paralelas: nenhuma marcada `[P]` — T001–T005 compartilham
  `tests/test_app_bases.py` (mesmo arquivo, funções distintas); a sequência
  única é suficiente para o tamanho da fatia.
- Estratégia de MVP: a spec inteira é o menor conjunto entregável — é uma
  correção de bug única e pequena, sem fatiamento adicional.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Nenhuma dependência bloqueante de outra spec ou backlog. Sem migration de
  banco.

#### Riscos

- Um teste de retentativa pode mascarar um bug se o mock não refletir
  exatamente o comportamento idempotente real → mitigação: os testes de
  AC-004/005/006 usam o storage e o vector store reais (apenas com um
  `side_effect` que falha uma vez) em vez de dublar toda a idempotência,
  provando o comportamento real de `LocalDirectoryStorage.delete_base` e do
  adapter em memória.
- Reordenar `apagar_base` pode introduzir uma janela onde a base já teve
  storage/vetores apagados mas ainda aparece ativa no Postgres até a segunda
  sessão commitar → mitigação: essa janela é curta (sem I/O adicional entre
  os dois externos e o commit) e é estritamente melhor que o estado atual
  (base invisível com recursos órfãos permanentes); aceito como trade-off
  desta correção, sem introduzir lock adicional (decisão confirmada, fora de
  escopo um mecanismo de lock distribuído para este caso).

#### Suposições

- `LocalDirectoryStorage.delete_base`, `S3CompatibleStorage.delete_base` e
  `service.delete_scope` permanecem idempotentes (confirmado por leitura de
  código nesta spec); qualquer mudança futura nesses três pontos deve
  preservar essa propriedade ou esta correção deixa de ser suficiente.

### 17. Decisões

- **DEC-001**: Reordenar `apagar_base` — apagar storage e vector store antes
  de commitar o soft-delete no Postgres — em vez de endpoint de retry
  dedicado ou job de reconciliação em segundo plano. Confirmada no
  refinamento do BACKLOG-0019.
- **DEC-002**: Sem mudança de frontend — `ExcluirBaseDialog.tsx` já orienta
  "tente novamente", que passa a funcionar de verdade com a correção.
  Confirmada no refinamento do BACKLOG-0019.
- **DEC-003**: Spec separada de BACKLOG-0018/SPEC-0015 (corrida em
  `has_active_execution`), apesar de descoberta junto e no mesmo módulo —
  correções independentes, uma exige migration e a outra não. Confirmada no
  refinamento cruzado dos dois backlogs.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
