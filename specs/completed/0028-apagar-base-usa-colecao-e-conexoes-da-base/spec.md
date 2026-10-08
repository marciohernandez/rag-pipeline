# Especificação integrada: Apagar Base usa a coleção e as conexões da própria Base

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0028 |
| Slug | 0028-apagar-base-usa-colecao-e-conexoes-da-base |
| Status | Complete |
| Effort | 4 |
| Effort updated at | 2026-10-08 |
| Effort rationale | Correção localizada em três módulos (rota de exclusão, resolução de conexões do worker e fachada do pipeline), com segredo cifrado e distinção entre coleção ausente e falha real; sem migration nem tela. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-10-08 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

Ao apagar uma Base pela interface, a exclusão falha com "Não foi possível apagar a base. Tente novamente." quando a Base foi criada com coleção própria. O backend registra `UnreliableScopeReadError` causado por um 404 do Qdrant: a coleção `rag-pipeline-app` não existe. `apagar_base` (`src/app/routers/bases.py`) monta a configuração do vector store com a coleção padrão do sistema, enquanto a indexação (`src/app/publicacao.py` e `src/app/tasks.py`) usa `base.collection_name` e, desde a SPEC-0026, as conexões vinculadas à Base. Efeito: apagar qualquer Base com coleção própria falha e, se a coleção padrão existisse, a exclusão deixaria vetores órfãos na coleção real. Para Bases com conexão Qdrant própria, a exclusão ainda miraria o Qdrant global. Fonte: `specs/inbox/2026-10-05-165154-apagar-base-ignora-a-colecao-da-base-e-falha-com-404-no-qdrant.md`.

#### Resultado desejado

Apagar uma Base remove os vetores dela da coleção e do Qdrant que a própria Base usa, a Base some da listagem e não sobram resíduos. Uma coleção que já não existe no Qdrant não impede a exclusão, enquanto qualquer outra falha continua bloqueando-a sem alterar o Postgres. O resultado é verificável pelo front, em `/workspaces/[id]`.

#### Métricas de sucesso

- 100% das exclusões de Base com coleção própria concluem com 204 nos testes de AC-001, AC-003 e AC-004.
- Zero pontos removidos fora do escopo da Base apagada, medido por AC-002.
- Zero ocorrência da chave da conexão em respostas, logs e mensagens de erro, medido por AC-005.
- Zero exclusão concluída diante de falha que não seja coleção ausente, medido por AC-008.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: Por que a exclusão falha com 404? → `apagar_base` monta `vector_store` com `dict(settings.vector_store)` sem `collection_name` (`src/app/routers/bases.py`), e a coleção padrão não existe; a releitura paginada em `scope_ids` converte o 404 em `UnreliableScopeReadError` (`src/pipeline/providers/vectorstores/qdrant.py`). Impacto: FR-001.
- **R-002**: Como a indexação resolve o vector store de uma Base? → `_configuracao_da_base` (`src/app/tasks.py`) usa a conexão Qdrant vinculada, decifra a chave em memória e acrescenta `collection_name=base.collection_name`; sem conexões usa `settings.vector_store` com a coleção da Base. Impacto: FR-001, FR-002 e a regra de caminho único.
- **R-003**: `describe_collection` serve para decidir "coleção ausente"? → Não: `QdrantAdapter.describe` devolve mapa vazio tanto para coleção ausente quanto para destino inacessível (`src/pipeline/providers/vectorstores/qdrant.py`, DEC-015 da SPEC-0026). Usá-lo trataria uma queda do Qdrant como coleção ausente e deixaria vetores órfãos. Impacto: DEC-002 e FR-003.
- **R-004**: A consulta (`queries.py`) também diverge? → Sim, em parte: `src/app/routers/queries.py` usa `settings.vector_store` com `collection_name=base.collection_name`, mas ignora as conexões vinculadas. Impacto: fora de escopo desta spec e registrado em DEC-004.

#### Fontes e contexto consultados

- `specs/backlog/0035-apagar-base-usa-colecao-e-conexoes-da-base.md`, brief refinado com duas decisões confirmadas em 2026-10-08 (escopo da correção e coleção ausente).
- `specs/inbox/2026-10-05-165154-apagar-base-ignora-a-colecao-da-base-e-falha-com-404-no-qdrant.md`, captura de origem.
- `src/app/routers/bases.py`, `src/app/tasks.py`, `src/app/publicacao.py`, `src/app/routers/queries.py`, `src/app/conexoes.py`, `src/pipeline/service.py` e `src/pipeline/providers/vectorstores/qdrant.py`, evidência do comportamento atual.
- `tests/test_app_bases.py` e `tests/_fakes_vectorstore.py`, padrão dos testes de exclusão existentes.
- Specs concluídas relacionadas: SPEC-0018 (ordem e idempotência da exclusão), SPEC-0019 (coleção por Base) e SPEC-0026 (conexões por Base).
- `.specsfy/RULES.md`, `.specsfy/STACK.md`, `.specsfy/DATABASE.md` e `INTERFACE.md`.

#### Documentação consultada

- Nenhuma documentação externa: o comportamento é definido pelo código local e pelas specs citadas.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q** (2026-10-08): Qual o escopo da correção? → **A**: a exclusão usa a mesma configuração da indexação (coleção e conexões da Base), inclusive para Bases com conexão própria.
- **Q** (2026-10-08): O que fazer quando a coleção não existe mais no Qdrant? → **A**: tratar como já apagada; a exclusão segue e a Base some da listagem.

#### Dúvidas abertas

- Nenhuma. Os defaults assumidos estão em Suposições e nas decisões DEC-001 a DEC-004.

### 3. Escopo e atores

#### Incluído

- Montar a configuração do vector store da exclusão pelo mesmo caminho da indexação: coleção da Base e, quando vinculada, a conexão Qdrant da Base.
- Manter o caminho das Bases anteriores à SPEC-0026 (Qdrant global com a coleção da Base).
- Tratar a coleção ausente (404 do Qdrant) como já apagada.
- Manter o bloqueio, sem escrita no Postgres, para qualquer outra falha, e a repetição segura da SPEC-0018.
- Registrar em log a coleção e a conexão alvo, sem segredo.
- Teste de regressão cobrindo coleção própria, conexão própria, coleção ausente e falha real, e conferência pelo front.

#### Fora de escopo

- Telas novas ou mudança de texto da interface.
- A divergência da consulta, que ignora as conexões da Base (DEC-004).
- Limpeza automática de Bases vazias por upload que falhou.
- Mudar a política de segurança de sincronização, a ordem das operações da SPEC-0018 ou o soft-delete.
- Apagar a própria coleção do Qdrant: a exclusão remove somente os pontos do escopo da Base.
- Outros providers de vector store.

#### Atores

- **Pessoa com papel de escrita (owner, admin e equivalentes)**: apaga Bases pelo front e espera que os vetores saiam do lugar certo.
- **Backend (rota `DELETE /bases/{base_id}`)**: resolve o destino correto, remove os pontos e só então grava o soft-delete no Postgres.
- **Qdrant**: guarda as coleções; pode estar com a coleção ausente ou indisponível.

### 4. Princípios e restrições do projeto

- **PR-001**: `src/app/` depende somente da fachada `src.pipeline.service`; nenhum import de módulos internos de `src/pipeline/` nem do SDK `qdrant_client` a partir de `src/app/` (`.specsfy/RULES.md`, `tests/test_application_boundaries.py`).
- **PR-002**: Segredos de conexão existem apenas cifrados no Postgres e decifrados em memória; nunca em respostas, logs, argumentos de job ou mensagens de erro (SPEC-0026).
- **PR-003**: Storage e vector store são apagados antes de qualquer escrita no Postgres, e cada passo é idempotente (SPEC-0018).
- **PR-004**: Testes usam o Postgres de teste com rollback transacional e nunca o banco de desenvolvimento; comandos que apagam banco ou schema são ignorados.
- **PR-005**: Uma branch por unidade de integração: `spec/0028-apagar-base-usa-colecao-e-conexoes-da-base`, sem carregar outra spec.

### 5. Histórias de usuário

#### US-001 — Apagar Base com coleção própria (P1)

Como pessoa com papel de escrita, quero apagar uma Base criada com coleção própria, para que os vetores dela saiam da coleção correta e a Base desapareça da listagem.

**Por que P1**: hoje a exclusão de qualquer Base com coleção própria falha, o que impede limpar o ambiente de teste e deixa vetores órfãos em risco.
**Teste independente**: criar uma Base com coleção própria, indexar e apagar pelo front; a Base some e os pontos saem da coleção.
**Requisitos**: FR-001, NFR-002

#### US-002 — Apagar Base com conexões próprias (P1)

Como pessoa com papel de escrita, quero que a exclusão use o Qdrant da conexão vinculada à Base, para não apagar no destino errado nem expor a chave da conexão.

**Por que P1**: desde a SPEC-0026 a Base indexa em um Qdrant escolhido pela pessoa; a exclusão no Qdrant global seria incorreta e insegura.
**Teste independente**: apagar uma Base vinculada a uma conexão Qdrant e conferir que a remoção ocorreu nesse Qdrant e que a chave não aparece em log nem resposta.
**Requisitos**: FR-002, FR-005, NFR-001

#### US-003 — Concluir a exclusão quando a coleção não existe e bloquear em falhas reais (P2)

Como pessoa com papel de escrita, quero que uma coleção que já não existe não me impeça de apagar a Base, mas que uma falha real do Qdrant me avise, para não ficar com Bases impossíveis de apagar nem com vetores órfãos.

**Por que P2**: a coleção ausente é um caso de borda frequente em ambientes de teste; o valor é recuperar o fluxo sem enfraquecer a segurança da exclusão.
**Teste independente**: apagar uma Base cuja coleção foi removida do Qdrant (conclui) e outra com o Qdrant indisponível (bloqueia e permite repetir).
**Requisitos**: FR-003, FR-004, FR-005, NFR-002

### 6. Cenários BDD de aceite

#### AC-001 — Base com coleção própria é apagada nessa coleção

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-001
Feature: Apagar Base usa a coleção e as conexões da própria Base

  Scenario: Exclusão usa a coleção da Base
    Given uma Base indexada na coleção própria "vivo test" e a coleção padrão "rag-pipeline-app" inexistente
    When uma pessoa com papel de escrita apaga a Base
    Then os pontos do escopo da Base saem de "vivo test", a resposta é 204 e a Base some da listagem
```

#### AC-002 — Coleção padrão e outras Bases permanecem intactas

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-002
Feature: Apagar Base usa a coleção e as conexões da própria Base

  Scenario: Isolamento durante a exclusão
    Given a coleção padrão com pontos de outra Base e uma segunda Base na mesma coleção própria
    When a primeira Base é apagada
    Then apenas os pontos do escopo da primeira Base são removidos e os demais pontos permanecem
```

#### AC-003 — Base anterior à SPEC-0026 mantém o caminho com a configuração global

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-003
Feature: Apagar Base usa a coleção e as conexões da própria Base

  Scenario: Base sem conexões vinculadas
    Given uma Base sem conexões vinculadas e com coleção própria
    When ela é apagada
    Then o Qdrant global é usado com o collection_name da Base e a exclusão conclui sem erro
```

#### AC-004 — Base com conexões é apagada no Qdrant da conexão

**Cobre**: US-002, FR-002, FR-005, NFR-001

```gherkin
@US-002 @FR-002 @FR-005 @NFR-001 @AC-004
Feature: Apagar Base usa a coleção e as conexões da própria Base

  Scenario: Exclusão pelo Qdrant da conexão vinculada
    Given uma Base vinculada a uma conexão Qdrant ativa com chave cifrada e coleção própria
    When ela é apagada
    Then a remoção ocorre na URL e na coleção da conexão com a chave decifrada em memória e o log registra a coleção e o nome da conexão sem a chave
```

#### AC-005 — A chave da conexão não vaza

**Cobre**: US-002, FR-002, FR-005, NFR-001

```gherkin
@US-002 @FR-002 @FR-005 @NFR-001 @AC-005
Feature: Apagar Base usa a coleção e as conexões da própria Base

  Scenario: Segredo fora de logs, respostas e erros
    Given uma Base vinculada a uma conexão Qdrant cuja chave é um valor conhecido
    When a exclusão conclui e quando ela falha no vector store
    Then a chave não aparece no corpo da resposta, nos logs capturados nem na mensagem de erro
```

#### AC-006 — Conexão desativada ou ilegível bloqueia a exclusão

**Cobre**: US-002, FR-002, FR-004, NFR-001

```gherkin
@US-002 @FR-002 @FR-004 @NFR-001 @AC-006
Feature: Apagar Base usa a coleção e as conexões da própria Base

  Scenario: Conexão indisponível
    Given uma Base vinculada a uma conexão Qdrant desativada
    When a pessoa tenta apagar a Base
    Then a resposta é 409 com a mensagem pedindo para reativar a conexão, a Base continua visível e nada é gravado no Postgres
```

#### AC-007 — Coleção ausente no Qdrant conta como já apagada

**Cobre**: US-003, FR-003, FR-005

```gherkin
@US-003 @FR-003 @FR-005 @AC-007
Feature: Apagar Base usa a coleção e as conexões da própria Base

  Scenario: Coleção inexistente
    Given uma Base cuja coleção não existe mais no Qdrant (resposta 404)
    When a pessoa apaga a Base
    Then a exclusão conclui com 204, o log registra a coleção ausente e a Base some da listagem
```

#### AC-008 — Falha que não é coleção ausente continua bloqueando

**Cobre**: US-003, FR-003, FR-004, NFR-002

```gherkin
@US-003 @FR-003 @FR-004 @NFR-002 @AC-008
Feature: Apagar Base usa a coleção e as conexões da própria Base

  Scenario: Qdrant indisponível
    Given um Qdrant que responde erro de conexão ou 500 na releitura do escopo
    When a pessoa tenta apagar a Base
    Then a resposta é de erro, a Base continua visível, nada é gravado no Postgres e a falha não é tratada como coleção ausente
```

#### AC-009 — Repetir a exclusão depois da falha conclui

**Cobre**: US-003, FR-003, FR-004, NFR-002

```gherkin
@US-003 @FR-003 @FR-004 @NFR-002 @AC-009
Feature: Apagar Base usa a coleção e as conexões da própria Base

  Scenario: Repetição após falha
    Given uma exclusão que falhou porque o Qdrant estava indisponível
    When o Qdrant volta e a pessoa repete a exclusão
    Then a exclusão conclui, os pontos saem da coleção da Base e a Base some da listagem
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve montar a configuração do vector store da exclusão de uma Base com o `collection_name` da própria Base, pelo mesmo caminho usado na indexação, de modo que os pontos removidos sejam os do escopo da Base nessa coleção e a coleção padrão do sistema nunca seja consultada nem alterada por uma Base com coleção própria.
- **FR-002**: O sistema deve, quando a Base tiver conexão Qdrant vinculada, usar a URL e a chave dessa conexão na exclusão, decifrando a chave em memória e revalidando a URL; deve recusar com 409 e mensagem clara uma conexão desativada ou indisponível, sem escrever no Postgres.
- **FR-003**: O sistema deve tratar como coleção ausente apenas a releitura do escopo que falhar com resposta 404 do Qdrant, concluindo a exclusão com zero pontos removidos; qualquer outra falha deve manter o comportamento atual de erro.
- **FR-004**: O sistema deve manter, para qualquer falha que não seja coleção ausente, a Base visível, nenhuma escrita no Postgres e a possibilidade de repetir a exclusão (SPEC-0018).
- **FR-005**: O sistema deve registrar em log, a cada exclusão, a coleção alvo, o nome da conexão usada (quando houver) e o caso de coleção ausente, sem incluir a chave nem a URL com credenciais.

#### Não funcionais

- **NFR-001**: Segurança dos segredos: a chave da conexão não aparece em respostas HTTP, logs, mensagens de exceção nem argumentos de job, e somente a chave da conexão Qdrant é decifrada na exclusão. **Verificação**: AC-004, AC-005 e AC-006 com chave conhecida e captura de logs.
- **NFR-002**: Compatibilidade e idempotência: Bases anteriores à SPEC-0026 mantêm o comportamento, a ordem storage → vector store → Postgres da SPEC-0018 é preservada, e repetir a exclusão após uma falha conclui. **Verificação**: AC-001, AC-002, AC-003, AC-008 e AC-009 mais a regressão de `tests/test_app_bases.py`.

#### Erros e casos-limite

- Coleção própria com espaço no nome (por exemplo "vivo test") → o nome é passado como está; o teste de AC-001 usa esse nome.
- Coleção ausente (404) → exclusão conclui, log registra o caso.
- Qdrant indisponível, erro 500 ou timeout → erro, Base visível, sem escrita no Postgres.
- Conexão desativada → 409 com mensagem para reativar a conexão.
- Chave que não pode ser decifrada → erro 503 genérico da SPEC-0026, sem vazar valor.
- Base já apagada → 404 existente de `get_base_or_404`.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI com SQLAlchemy e Postgres, worker procrastinate, pipeline em `src/pipeline/` acessado por `src/app/` somente pela fachada `src.pipeline.service` (`.specsfy/STACK.md`).
- `apagar_base` em `src/app/routers/bases.py` monta `{"projeto", "embedding", "vector_store"}` com a configuração global e chama `service.delete_scope(config)`.
- `_configuracao_da_base` em `src/app/tasks.py` já resolve embeddings, vector store e divisão da Base para a execução, decifrando a chave só em memória.
- Testes de exclusão existentes em `tests/test_app_bases.py` usam o fixture `vector_store_em_memoria` de `tests/_fakes_vectorstore.py`.

#### Arquitetura e módulos

- `src/app/tasks.py`: extrair de `_configuracao_da_base` a função pública `configuracao_vector_store_da_base(session, base)`, que devolve a seção `vector_store` da Base (conexão Qdrant vinculada com a coleção da Base, ou configuração global com a coleção da Base). `_configuracao_da_base` passa a chamá-la, garantindo um único caminho para indexação e exclusão.
- `src/app/routers/bases.py`: `apagar_base` obtém a seção `vector_store` por essa função (dentro de uma sessão curta), mantém `embedding` global sem decifrar chave de embeddings, e converte `ErroDeConexao` em resposta HTTP como a rota de execuções já faz.
- `src/pipeline/service.py`: `delete_scope` captura `UnreliableScopeReadError`, verifica se a causa tem `status_code == 404` e, nesse caso, registra log e devolve 0; qualquer outra causa relança a exceção original.
- Sem mudança em `src/pipeline/providers/`, no contrato do adaptador, no banco ou no front.

#### Migrations

- Não aplicável: nenhuma tabela, coluna ou índice muda.

#### Models

- Sem mudança. Usa `Base` (`collection_name`, `conexao_embeddings_id`, `conexao_vector_store_id`, `chunking`) e `Conexao` (`tipo`, `situacao`, `configuracao`, `segredo_cifrado`) em `src/app/models.py`.

#### Controllers e casos de uso

- `DELETE /bases/{base_id}` em `src/app/routers/bases.py`: mantém `require_write_role`, `get_base_or_404`, `get_storage().delete_base`, soft-delete e a ordem da SPEC-0018; muda apenas a origem da seção `vector_store` e o tratamento de coleção ausente (via fachada).

#### Views e experiência

- Não aplicável: nenhuma tela muda. O botão Apagar base, a confirmação e a mensagem de erro existentes são preservados.

#### Queries e repositórios

- Sem mudança em `src/app/repo.py`. A leitura da conexão usa `session.get(Conexao, id)` como `_configuracao_da_base`.

#### Jobs e processamento assíncrono

- Não aplicável: a exclusão é síncrona e nenhum job novo é criado.

#### Estrutura de arquivos

```text
specs/draft/0028-apagar-base-usa-colecao-e-conexoes-da-base/
  spec.md
  research/
src/
  app/
    tasks.py
    routers/bases.py
  pipeline/
    service.py
tests/
  test_app_bases_exclusao_colecao.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Base | `id` | `collection_name`, `conexao_embeddings_id`, `conexao_vector_store_id`, `apagada_em`; sem mudança de schema | pertence a um Workspace; referencia até duas Conexões |
| Conexão | `id` | `tipo`, `situacao`, `configuracao`, `segredo_cifrado`; somente leitura nesta spec | usada por uma ou mais Bases |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Base | ativa | exclusão concluída (pontos removidos ou coleção ausente) | apagada (`apagada_em` preenchido, nome vazio) | o soft-delete só é gravado depois de storage e vector store |
| Base | ativa | exclusão falha por erro real do Qdrant ou do storage | ativa | nenhuma escrita no Postgres; a pessoa pode repetir |
| Base | ativa | exclusão recusada por conexão desativada | ativa | resposta 409; nenhuma escrita no Postgres |

#### Migração e retenção

- Não aplicável: sem mudança de dados. Bases anteriores à SPEC-0026 não têm conexões vinculadas e seguem pelo caminho global com a coleção da Base.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega corrige o comportamento do backend da rota `DELETE /bases/{base_id}`. O botão Apagar base, a confirmação e a mensagem de erro existentes ficam como estão; o front apenas exibe o resultado.

#### Stack e convenções de interface

- Não aplicável: nenhuma camada de interface muda. Telas observadas e preservadas: detalhe do Workspace (`/workspaces/[id]`) e a tela da Base, que contêm a ação Apagar base (`INTERFACE.md`).

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Inalterado: a pessoa abre o Workspace, entra na Base e aciona Apagar base; o front chama o backend e mostra sucesso ou o erro existente.

#### Menus e navegação principal

- Não aplicável: nenhuma tela nova.

#### Formulários e ações

- Não aplicável: nenhum campo novo.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável: nenhum bloco React é criado ou alterado, e `INTERFACE.md` não muda.

#### Estados e acessibilidade

- Inalterados. O estado de erro existente cobre a falha real; o sucesso remove a Base da listagem.

#### Contrato CRUD

- Não aplicável: nenhuma tela CRUD é criada ou alterada.

#### Revisão visual durante o desenvolvimento

- Não aplicável nas tarefas de código: a mudança não tem superfície visual. A conferência final pelo front confirma apenas o resultado funcional da exclusão (T013).

#### APIs expostas

- `DELETE /bases/{base_id}` (autenticação por sessão, papel de escrita): resposta 204 em sucesso; 404 para Base inexistente ou de outra equipe; 409 para conexão vinculada desativada (novo, mensagem pedindo para reativá-la); 503 genérico para chave não decifrável; erro de servidor existente para falhas reais do Qdrant ou do storage. Sem mudança de versionamento.

#### APIs externas utilizadas

- Qdrant, operações de leitura paginada do escopo e remoção por identificadores, na URL da conexão vinculada ou da configuração global; autenticação por chave de API quando houver; timeout e retry do cliente existente; sem fallback: falha real bloqueia a exclusão.

#### Documentação das APIs consultadas

- Nenhuma documentação externa: o status 404 como sinal de coleção ausente foi confirmado no código do adaptador e deve ser provado pelos testes AC-007 e AC-008 com o falso do Qdrant.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: tratamento de 404 em `delete_scope` e montagem da seção `vector_store` por `configuracao_vector_store_da_base`.
- **Integração/contrato**: rota `DELETE /bases/{base_id}` com Postgres de teste (rollback transacional) e o falso de vector store de `tests/_fakes_vectorstore.py`, estendido para simular coleção ausente (404) e indisponibilidade.
- **BDD/aceite**: o Gherkin da seção 6 orienta o desenho dos testes; não há arquivos `.feature`.
- **Runner TDD**: Pytest existente (`uv run pytest`) e Ruff, conforme `.specsfy/RULES.md`.
- **E2E**: Não aplicável como automação; a jornada pelo front é conferida manualmente em T013.
- **Verificação manual**: apagar pelo front uma Base com coleção própria no stack local reconstruído e conferir no Qdrant que a coleção deixou de ter os pontos da Base; necessária porque o stack roda a imagem anterior à correção.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, NFR-002, AC-001 | AC-001 na seção 6 | `test_apagar_base_usa_colecao_da_base` em tests/test_app_bases_exclusao_colecao.py com marcador próprio `SPECSFY: SPEC-0028 US-001 FR-001 NFR-002 AC-001` | RED 2026-10-08: a exclusão alcançou só `rag-pipeline-app`, nunca `vivo test` | GREEN 2026-10-08: `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 passed) | Regressão 2026-10-08: `uv run pytest -q` (503 passed, 1 skipped) e `ruff check .` limpo |
| US-001, FR-001, NFR-002, AC-002 | AC-002 na seção 6 | `test_apagar_base_nao_toca_colecao_padrao_nem_outras_bases` em tests/test_app_bases_exclusao_colecao.py com marcador próprio `SPECSFY: SPEC-0028 US-001 FR-001 NFR-002 AC-002` | RED 2026-10-08: a exclusão alcançou a coleção padrão `rag-pipeline-app` | GREEN 2026-10-08: `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 passed) | Regressão 2026-10-08: `uv run pytest -q` (503 passed, 1 skipped) e `ruff check .` limpo |
| US-001, FR-001, NFR-002, AC-003 | AC-003 na seção 6 | `test_apagar_base_sem_conexoes_usa_qdrant_global_com_colecao_da_base` em tests/test_app_bases_exclusao_colecao.py com marcador próprio `SPECSFY: SPEC-0028 US-001 FR-001 NFR-002 AC-003` | RED 2026-10-08: a configuração usada não trouxe o `collection_name` da Base (`rag-pipeline-app`) | GREEN 2026-10-08: `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 passed) | Regressão 2026-10-08: `uv run pytest -q` (503 passed, 1 skipped) e `ruff check .` limpo |
| US-002, FR-002, FR-005, NFR-001, AC-004 | AC-004 na seção 6 | `test_apagar_base_com_conexoes_usa_qdrant_da_conexao` em tests/test_app_bases_exclusao_colecao.py com marcador próprio `SPECSFY: SPEC-0028 US-002 FR-002 FR-005 NFR-001 AC-004` | RED 2026-10-08: o Qdrant da conexão não foi usado; só a configuração global foi alcançada | GREEN 2026-10-08: `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 passed) | Regressão 2026-10-08: `uv run pytest -q` (503 passed, 1 skipped) e `ruff check .` limpo |
| US-002, FR-002, FR-005, NFR-001, AC-005 | AC-005 na seção 6 | `test_apagar_base_nao_vaza_chave_da_conexao` em tests/test_app_bases_exclusao_colecao.py com marcador próprio `SPECSFY: SPEC-0028 US-002 FR-002 FR-005 NFR-001 AC-005` | RED 2026-10-08: o Qdrant da conexão não foi alcançado na falha (configuração global usada) | GREEN 2026-10-08: `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 passed) | Regressão 2026-10-08: `uv run pytest -q` (503 passed, 1 skipped) e `ruff check .` limpo |
| US-002, FR-002, FR-004, NFR-001, AC-006 | AC-006 na seção 6 | `test_apagar_base_com_conexao_desativada_bloqueia_sem_alterar_postgres` em tests/test_app_bases_exclusao_colecao.py com marcador próprio `SPECSFY: SPEC-0028 US-002 FR-002 FR-004 NFR-001 AC-006` | RED 2026-10-08: a resposta foi 204 em vez de 409 para conexão desativada | GREEN 2026-10-08: `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 passed) | Regressão 2026-10-08: `uv run pytest -q` (503 passed, 1 skipped) e `ruff check .` limpo |
| US-003, FR-003, FR-005, AC-007 | AC-007 na seção 6 | `test_apagar_base_com_colecao_ausente_conclui` em tests/test_app_bases_exclusao_colecao.py com marcador próprio `SPECSFY: SPEC-0028 US-003 FR-003 FR-005 AC-007` | RED 2026-10-08: a resposta foi 500 em vez de 204 (404 de coleção ausente tratado como falha) | GREEN 2026-10-08: `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 passed) | Regressão 2026-10-08: `uv run pytest -q` (503 passed, 1 skipped) e `ruff check .` limpo |
| US-003, FR-003, FR-004, NFR-002, AC-008 | AC-008 na seção 6 | `test_apagar_base_com_qdrant_indisponivel_bloqueia` em tests/test_app_bases_exclusao_colecao.py com marcador próprio `SPECSFY: SPEC-0028 US-003 FR-003 FR-004 NFR-002 AC-008` | RED 2026-10-08: a coleção da Base não foi alcançada (só `rag-pipeline-app`) | GREEN 2026-10-08: `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 passed) | Regressão 2026-10-08: `uv run pytest -q` (503 passed, 1 skipped) e `ruff check .` limpo |
| US-003, FR-003, FR-004, NFR-002, AC-009 | AC-009 na seção 6 | `test_apagar_base_repete_apos_falha_do_qdrant_conclui` em tests/test_app_bases_exclusao_colecao.py com marcador próprio `SPECSFY: SPEC-0028 US-003 FR-003 FR-004 NFR-002 AC-009` | RED 2026-10-08: a coleção da Base não foi alcançada na repetição (só `rag-pipeline-app`) | GREEN 2026-10-08: `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 passed) | Regressão 2026-10-08: `uv run pytest -q` (503 passed, 1 skipped) e `ruff check .` limpo |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_usa_colecao_da_base -v` | Passed (2026-10-08) |
| FR-001 | AC-002 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_nao_toca_colecao_padrao_nem_outras_bases -v` | Passed (2026-10-08) |
| FR-001 | AC-003 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_sem_conexoes_usa_qdrant_global_com_colecao_da_base -v` | Passed (2026-10-08) |
| FR-002 | AC-004 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_com_conexoes_usa_qdrant_da_conexao -v` | Passed (2026-10-08) |
| FR-002 | AC-005 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_nao_vaza_chave_da_conexao -v` | Passed (2026-10-08) |
| FR-002 | AC-006 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_com_conexao_desativada_bloqueia_sem_alterar_postgres -v` | Passed (2026-10-08) |
| FR-003 | AC-007 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_com_colecao_ausente_conclui -v` | Passed (2026-10-08) |
| FR-003 | AC-008 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_com_qdrant_indisponivel_bloqueia -v` | Passed (2026-10-08) |
| FR-003 | AC-009 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_repete_apos_falha_do_qdrant_conclui -v` | Passed (2026-10-08) |
| FR-004 | AC-006 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_com_conexao_desativada_bloqueia_sem_alterar_postgres -v` | Passed (2026-10-08) |
| FR-004 | AC-008 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_com_qdrant_indisponivel_bloqueia -v` | Passed (2026-10-08) |
| FR-004 | AC-009 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_repete_apos_falha_do_qdrant_conclui -v` | Passed (2026-10-08) |
| FR-005 | AC-004 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_com_conexoes_usa_qdrant_da_conexao -v` | Passed (2026-10-08) |
| FR-005 | AC-005 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_nao_vaza_chave_da_conexao -v` | Passed (2026-10-08) |
| FR-005 | AC-007 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_com_colecao_ausente_conclui -v` | Passed (2026-10-08) |
| NFR-001 | AC-004 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_com_conexoes_usa_qdrant_da_conexao -v` | Passed (2026-10-08) |
| NFR-001 | AC-005 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_nao_vaza_chave_da_conexao -v` | Passed (2026-10-08) |
| NFR-001 | AC-006 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_com_conexao_desativada_bloqueia_sem_alterar_postgres -v` | Passed (2026-10-08) |
| NFR-002 | AC-001 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_usa_colecao_da_base -v` | Passed (2026-10-08) |
| NFR-002 | AC-002 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_nao_toca_colecao_padrao_nem_outras_bases -v` | Passed (2026-10-08) |
| NFR-002 | AC-003 | Integração (Postgres de teste, Qdrant falso) | `uv run pytest tests/test_app_bases_exclusao_colecao.py::test_apagar_base_sem_conexoes_usa_qdrant_global_com_colecao_da_base -v` | Passed (2026-10-08) |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (2026-10-08)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0028-apagar-base-usa-colecao-e-conexoes-da-base/spec.md`
- **Achados**: 0 BLOCKER, 0 WARNING, 1 NOTE resolvida (seção 15: T012 edita `src/pipeline/service.py`, não os arquivos de `src/app/`). Cobertura mínima atendida: 3 US, 5 FR, 2 NFR, cada um com 3 ou mais AC (9 AC no total); matriz da seção 12 com 21 linhas; 9 casos TDD com marcador próprio. DoD sem exigência de STACK.md, DATABASE.md ou PROJECT.md porque não há mudança de stack, persistência ou finalidade.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-08)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0028-apagar-base-usa-colecao-e-conexoes-da-base/spec.md`
- **Achados**: 13 tarefas (9 de teste TDD com RED válido, 3 de código, 1 de regressão); 19 de 19 IDs cobertos; nenhum predecessor TDD aberto. RED observado com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 failed, cada um pelo comportamento ausente). Banco de teste confirmado como `SAFE` por `check_database_safety.mjs`.

#### Gate do Ato III — Entrega

- **Resultado**: Passed (2026-10-08)
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0028-apagar-base-usa-colecao-e-conexoes-da-base/spec.md . --full-chain`
- **Achados**: 13/13 tarefas concluídas; 19/19 IDs com teste, tarefa e evidência; 9 casos TDD verdes; suíte completa 503 passed e 1 skipped; `verify_acceptance.mjs` PASSED; conferência pelo front confirmada pelo Postgres e pelo log do Qdrant.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 o caso `test_apagar_base_usa_colecao_da_base` falhando em tests/test_app_bases_exclusao_colecao.py — Refs: US-001, FR-001, NFR-002, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 failed): a exclusão alcançou só `rag-pipeline-app`, nunca `vivo test`.
  - [x] **IMPROVE**: O fixture `vector_store_em_memoria` foi descartado porque recria as configurações sem a chave de cifra das conexões; o destino falso já isola o vector store.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 o caso `test_apagar_base_nao_toca_colecao_padrao_nem_outras_bases` falhando em tests/test_app_bases_exclusao_colecao.py — Refs: US-001, FR-001, NFR-002, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 failed): a exclusão alcançou a coleção padrão `rag-pipeline-app`.
  - [x] **IMPROVE**: O fixture `vector_store_em_memoria` foi descartado porque recria as configurações sem a chave de cifra das conexões; o destino falso já isola o vector store.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 o caso `test_apagar_base_sem_conexoes_usa_qdrant_global_com_colecao_da_base` falhando em tests/test_app_bases_exclusao_colecao.py — Refs: US-001, FR-001, NFR-002, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 failed): a configuração usada não trouxe o `collection_name` da Base (`rag-pipeline-app`).
  - [x] **IMPROVE**: O fixture `vector_store_em_memoria` foi descartado porque recria as configurações sem a chave de cifra das conexões; o destino falso já isola o vector store.

- [x] T004 [TEST] [TDD] [US-002] Derivar do AC-004 o caso `test_apagar_base_com_conexoes_usa_qdrant_da_conexao` falhando em tests/test_app_bases_exclusao_colecao.py — Refs: US-002, FR-002, FR-005, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 failed): o Qdrant da conexão não foi usado; só a configuração global foi alcançada.
  - [x] **IMPROVE**: O fixture `vector_store_em_memoria` foi descartado porque recria as configurações sem a chave de cifra das conexões; o destino falso já isola o vector store.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-005 o caso `test_apagar_base_nao_vaza_chave_da_conexao` falhando em tests/test_app_bases_exclusao_colecao.py — Refs: US-002, FR-002, FR-005, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 failed): o Qdrant da conexão não foi alcançado na falha (configuração global usada).
  - [x] **IMPROVE**: O fixture `vector_store_em_memoria` foi descartado porque recria as configurações sem a chave de cifra das conexões; o destino falso já isola o vector store.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 o caso `test_apagar_base_com_conexao_desativada_bloqueia_sem_alterar_postgres` falhando em tests/test_app_bases_exclusao_colecao.py — Refs: US-002, FR-002, FR-004, NFR-001, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 failed): a resposta foi 204 em vez de 409 para conexão desativada.
  - [x] **IMPROVE**: O fixture `vector_store_em_memoria` foi descartado porque recria as configurações sem a chave de cifra das conexões; o destino falso já isola o vector store.

- [x] T007 [TEST] [TDD] [US-003] Derivar do AC-007 o caso `test_apagar_base_com_colecao_ausente_conclui` falhando em tests/test_app_bases_exclusao_colecao.py — Refs: US-003, FR-003, FR-005, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 failed): a resposta foi 500 em vez de 204 (404 de coleção ausente tratado como falha).
  - [x] **IMPROVE**: O fixture `vector_store_em_memoria` foi descartado porque recria as configurações sem a chave de cifra das conexões; o destino falso já isola o vector store.

- [x] T008 [TEST] [TDD] [US-003] Derivar do AC-008 o caso `test_apagar_base_com_qdrant_indisponivel_bloqueia` falhando em tests/test_app_bases_exclusao_colecao.py — Refs: US-003, FR-003, FR-004, NFR-002, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 failed): a coleção da Base não foi alcançada (só `rag-pipeline-app`).
  - [x] **IMPROVE**: O fixture `vector_store_em_memoria` foi descartado porque recria as configurações sem a chave de cifra das conexões; o destino falso já isola o vector store.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-009 o caso `test_apagar_base_repete_apos_falha_do_qdrant_conclui` falhando em tests/test_app_bases_exclusao_colecao.py — Refs: US-003, FR-003, FR-004, NFR-002, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q` (9 failed): a coleção da Base não foi alcançada na repetição (só `rag-pipeline-app`).
  - [x] **IMPROVE**: O fixture `vector_store_em_memoria` foi descartado porque recria as configurações sem a chave de cifra das conexões; o destino falso já isola o vector store.

#### Fase 2 — US-001 Apagar Base com coleção própria (P1)

**Objetivo**: a exclusão usa a coleção da Base, inclusive para Bases sem conexões vinculadas.
**Teste independente**: `uv run pytest tests/test_app_bases_exclusao_colecao.py -k "colecao_da_base or nao_toca or sem_conexoes" -v` passa.

- [x] T010 [CODE] [US-001] Extrair de `_configuracao_da_base` a montagem do vector_store em `configuracao_vector_store_da_base(session, base)` e usá-la em `apagar_base`, em src/app/tasks.py e src/app/routers/bases.py — Refs: US-001, FR-001, NFR-002, AC-001, AC-002, AC-003 — Depends: T001, T002, T003
  - [x] **PREP**: RED confirmado nas tarefas T001–T009; `build_documentation.mjs --check` executado antes de editar.
  - [x] **EXECUTE**: Mudança implementada; `docs/architecture.md` e `docs/database.md` atualizados e `build_documentation.mjs --check` passou.
  - [x] **VERIFY**: Testes focais e regressão executados com resultado esperado.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera nenhuma tela; o botão, a confirmação e a mensagem de erro existentes são preservados.
  - [x] **EVIDENCE**: GREEN dos AC-001, AC-002 e AC-003 com `uv run pytest tests/test_app_bases_exclusao_colecao.py -q`; regressão `tests/test_app_bases.py` (21 passed); arquivos: `src/app/tasks.py` (`_config_da_conexao`, `configuracao_vector_store_da_base`), `src/app/routers/bases.py`.
  - [x] **IMPROVE**: A decifra e a revalidação da conexão ficaram em `_config_da_conexao`, usada pela execução e pela exclusão (caminho único, DEC-001).
  <!-- specsfy:evidence {"task":"T010","refs":["US-001", "FR-001", "NFR-002", "AC-001", "AC-002", "AC-003"],"files":["src/app/tasks.py", "src/app/routers/bases.py"],"commands":[{"run":"uv run pytest tests/test_app_bases_exclusao_colecao.py -v","exit":0}]} -->

**Checkpoint**: apagar uma Base com coleção própria e sem conexões conclui e remove os pontos da coleção da Base.

#### Fase 3 — US-002 Apagar Base com conexões próprias (P1)

**Objetivo**: a exclusão alcança o Qdrant da conexão vinculada sem expor a chave.
**Teste independente**: `uv run pytest tests/test_app_bases_exclusao_colecao.py -k "conexao or conexoes or chave" -v` passa.

- [x] T011 [CODE] [US-002] Resolver a conexão Qdrant da Base na exclusão (decifrar só a chave do Qdrant, revalidar a URL, 409 para conexão desativada) e registrar log sem segredo, em src/app/tasks.py e src/app/routers/bases.py — Refs: US-002, FR-002, FR-005, NFR-001, AC-004, AC-005, AC-006 — Depends: T004, T005, T006, T010
  - [x] **PREP**: RED confirmado nas tarefas T001–T009; `build_documentation.mjs --check` executado antes de editar.
  - [x] **EXECUTE**: Mudança implementada; `docs/architecture.md` e `docs/database.md` atualizados e `build_documentation.mjs --check` passou.
  - [x] **VERIFY**: Testes focais e regressão executados com resultado esperado.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera nenhuma tela; o botão, a confirmação e a mensagem de erro existentes são preservados.
  - [x] **EVIDENCE**: GREEN dos AC-004, AC-005 e AC-006; conexão desativada responde 409 antes de apagar storage ou tocar o Postgres; log traz coleção e nome da conexão sem a chave; arquivos: `src/app/tasks.py`, `src/app/routers/bases.py`.
  - [x] **IMPROVE**: O destino é resolvido antes de `get_storage().delete_base`, para o bloqueio por conexão desativada não apagar arquivos.
  <!-- specsfy:evidence {"task":"T011","refs":["US-002", "FR-002", "FR-005", "NFR-001", "AC-004", "AC-005", "AC-006"],"files":["src/app/tasks.py", "src/app/routers/bases.py"],"commands":[{"run":"uv run pytest tests/test_app_bases_exclusao_colecao.py -v","exit":0}]} -->

**Checkpoint**: apagar uma Base vinculada a conexões usa a URL e a chave da conexão, e a chave não aparece em log, resposta nem erro.

#### Fase 4 — US-003 Coleção ausente e falhas (P2)

**Objetivo**: coleção ausente conclui a exclusão e qualquer outra falha continua bloqueando.
**Teste independente**: `uv run pytest tests/test_app_bases_exclusao_colecao.py -k "ausente or indisponivel or repete" -v` passa.

- [x] T012 [CODE] [US-003] Tratar 404 na releitura do escopo como coleção ausente em `delete_scope` (retorna 0 e registra log) mantendo UnreliableScopeReadError para as demais falhas, em src/pipeline/service.py — Refs: US-003, FR-003, FR-004, FR-005, NFR-002, AC-007, AC-008, AC-009 — Depends: T007, T008, T009, T011
  - [x] **PREP**: RED confirmado nas tarefas T001–T009; `build_documentation.mjs --check` executado antes de editar.
  - [x] **EXECUTE**: Mudança implementada; `docs/architecture.md` e `docs/database.md` atualizados e `build_documentation.mjs --check` passou.
  - [x] **VERIFY**: Testes focais e regressão executados com resultado esperado.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera nenhuma tela; o botão, a confirmação e a mensagem de erro existentes são preservados.
  - [x] **EVIDENCE**: GREEN dos AC-007, AC-008 e AC-009; 404 na causa de `UnreliableScopeReadError` devolve 0 e registra a coleção ausente, outras falhas propagam; suíte inteira `uv run pytest -q` com 503 passed e 1 skipped; arquivo: `src/pipeline/service.py`.
  - [x] **IMPROVE**: A detecção usa só `status_code == 404` da causa, sem importar o SDK do Qdrant em `src/app/`.
  <!-- specsfy:evidence {"task":"T012","refs":["US-003", "FR-003", "FR-004", "FR-005", "NFR-002", "AC-007", "AC-008", "AC-009"],"files":["src/pipeline/service.py"],"commands":[{"run":"uv run pytest tests/test_app_bases_exclusao_colecao.py -v","exit":0}]} -->

**Checkpoint**: coleção ausente conclui com 204, e Qdrant indisponível mantém a Base visível e permite repetir.

#### Fase final — Qualidade

- [x] T013 [TEST] Executar regressão, Ruff e rastreabilidade e conferir o teste real pelo front (apagar a Base com coleção própria) em tests/test_app_bases_exclusao_colecao.py — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, NFR-002, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009 — Depends: T010, T011, T012
  - [x] **PREP**: Identificar suites, checks e gates; confirmar o stack local de teste (Postgres de teste, nunca o de desenvolvimento).
  - [x] **EXECUTE**: Executar `uv run ruff check`, `uv run pytest` e `check_traceability.mjs`; reconstruir o stack local com autorização da pessoa e apagar pelo front uma Base com coleção própria.
  - [x] **VERIFY**: Pelo front, Bases com coleção própria foram apagadas sem erro (`vivo test` às 20:12, 21:36 e 21:40 UTC e `plano pf teste` às 20:19 UTC, `apagada_em` preenchido no Postgres); o log do Qdrant local mostra `scroll` e `delete` em `vivo%20test` com 200 e nenhum 404; o Workspace `teste_01` foi apagado às 21:34 UTC depois de esvaziado.
  - [x] **VISUAL**: Não aplicável: nenhuma tela foi criada ou alterada; a conferência pelo front só confirmou o resultado da exclusão.
  - [x] **EVIDENCE**: `ruff check .` limpo; `uv run pytest -q` 503 passed e 1 skipped; `check_traceability.mjs --full-chain` 19/19; `verify_acceptance.mjs` PASSED; conferência pelo front registrada em VERIFY. `PROJECT.md` revisado sem impacto material: a finalidade e as capacidades do projeto não mudam (monitor executado com `--acknowledge-project-no-change`).
  - [x] **IMPROVE**: A atualização do stack local revelou banco sem histórico do Alembic e serviço sem a chave de cifra das conexões; ambos foram corrigidos com autorização e registrados em `specs/inbox/2026-10-08-220019-stack-local-divergente-dos-arquivos-de-deploy-e-banco-sem-historico-de-migrations.md`. A divergência da consulta (DEC-004) segue para captura.

### 15. Ordem de execução

- Caminho crítico: T001–T009 (RED) → T010 → T011 → T012 → T013.
- Tarefas paralelas: T001–T009 podem ser escritas em paralelo, pois só criam casos independentes no mesmo arquivo de teste; T010 e T011 são sequenciais porque editam `src/app/tasks.py` e `src/app/routers/bases.py` em cadeia; T012 edita só `src/pipeline/service.py` e fica depois de T011 apenas para validar a exclusão completa.
- Estratégia de MVP: US-001 (T010) já destrava a exclusão de Bases com coleção própria; US-002 e US-003 completam a correção.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0018 (ordem e idempotência da exclusão), SPEC-0019 (coleção por Base) e SPEC-0026 (conexões por Base), todas concluídas.
- Postgres de teste local (`rag-pipeline-test-postgres`, porta 55432) e o falso de vector store em `tests/_fakes_vectorstore.py`.
- Reconstrução do stack local com `deploy/build_and_deploy.sh` para a conferência final pelo front, que exige autorização da pessoa.

#### Riscos

- Distinguir 404 de coleção ausente de outras falhas sem engolir erros reais → a decisão usa somente `status_code == 404` na causa da falha e os testes AC-007 e AC-008 cobrem os dois lados.
- 404 por motivo diferente de coleção ausente (por exemplo URL errada atrás de proxy) → seria tratado como ausente; mitigação: log explícito do caso e a conexão revalidada antes (URL válida).
- Conexão desativada impede apagar a Base → mensagem orienta reativar a conexão; alternativa de forçar a exclusão fica fora de escopo.
- A consulta continua ignorando as conexões da Base → registrado em DEC-004 para decisão posterior.

#### Suposições

- Só pessoas com papel de escrita apagam Bases, como hoje.
- O nome da coleção com espaço (por exemplo "vivo test") é aceito pelo Qdrant e passado sem alteração; AC-001 confirma.
- O falso de vector store pode simular 404 com um erro que carregue `status_code`; caso contrário T001–T009 o estendem.
- A branch de integração é `spec/0028-apagar-base-usa-colecao-e-conexoes-da-base`.

### 17. Decisões

- **DEC-001**: A exclusão usa a seção `vector_store` produzida por uma função compartilhada com a indexação — razão: um único caminho evita nova divergência; alternativa rejeitada: duplicar a lógica de conexões em `apagar_base`.
- **DEC-002**: Coleção ausente é detectada pelo `status_code == 404` da causa de `UnreliableScopeReadError` dentro de `delete_scope` — razão: `describe_collection` não distingue ausência de indisponibilidade e trataria uma queda como exclusão bem-sucedida; alternativa rejeitada: consultar `describe_collection` antes.
- **DEC-003**: Conexão vinculada desativada bloqueia a exclusão com 409 — razão: coerente com a publicação e evita apagar no destino errado; trade-off: Base presa até a conexão ser reativada.
- **DEC-004**: A divergência da consulta (`queries.py` ignora as conexões da Base) fica fora desta spec — razão: mudança de comportamento de leitura com outro risco; será registrada como captura no inbox ao concluir.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Os cenários `AC` aplicáveis passam.
- [x] Os requisitos possuem evidência de verificação.
- [x] As tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
