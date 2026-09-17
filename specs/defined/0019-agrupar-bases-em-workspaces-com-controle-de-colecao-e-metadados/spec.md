# Especificação integrada: Agrupar bases em Workspaces com controle de coleção e metadados

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0019 |
| Slug | 0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados |
| Status | Defined |
| Effort | 7 |
| Effort updated at | 2026-09-17 |
| Effort rationale | Mudança de modelo de dados (nova entidade + migração de dados existentes) que atravessa router de upload, agendamento de execução, consulta e telas novas de interface — perfil `high`, sem irreversibilidade financeira ou de autorização crítica que justifique `maximum`. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Pending |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-09-17 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

As "bases" hoje existem soltas, sem agrupamento por cliente ou engajamento de consultoria. Todas as bases de todos os tenants compartilham a mesma coleção do banco vetorial (`vector_store.collection_name` global em `config.yaml`/`AppSettings`, isoladas apenas por metadata lógico via `scope_project_id`), sem possibilidade de separar conteúdo por estratégia de RAG (ex.: uma coleção para "produtos e serviços", outra para "políticas"). Também não existe forma de anexar metadados customizados aos chunks de uma base para filtrar buscas depois.

#### Resultado desejado

Uma pessoa organiza bases de conhecimento por cliente/engajamento em um **Workspace** (ex.: "Banda Larga PF — Vivo — Gold"). Toda Base pertence a exatamente um Workspace. Ao enviar uma Base, a pessoa escolhe opcionalmente um nome de coleção do banco vetorial (com um default derivado do Workspace quando omitido) e pode anexar pares de rótulo/valor que passam a fazer parte do metadata de cada chunk gerado.

#### Métricas de sucesso

- 100% das Bases (novas e pré-existentes) possuem `workspace_id` preenchido após a migração; nenhuma base fica "órfã".
- Uma pessoa consegue enviar duas Bases do mesmo Workspace para coleções diferentes e confirmar, por consulta, que os resultados não se misturam entre coleções.
- Tentativa de apagar um Workspace com Bases dentro é sempre bloqueada (0% de exclusões acidentais em cascata).

### 2. Research e esclarecimentos

#### Researchs executados

- Nenhuma pesquisa externa foi necessária; toda a investigação foi sobre o próprio repositório (ver Fontes e contexto consultados).

#### Fontes e contexto consultados

- `specs/backlog/0024-agrupar-bases-em-projetos-com-controle-de-colecao-e-metadados.md` — brief refinado nesta mesma conversa, com decisões de obrigatoriedade, autorização e exclusão já tomadas.
- `specs/inbox/2026-09-17-152835-arrumar-a-qualidade-visual-do-frontend.md` — captura original que originou o backlog.
- `.specsfy/DATABASE.md` — confirma que "projeto" já nomeia o escopo técnico de isolamento multi-tenant (`Base.project_id`), motivando o nome "Workspace" para a nova entidade; registra também "Workspace de organização de bases" e "Metadados customizados por chunk" em `Informações a guardar confirmadas`.
- `src/app/models.py` — schema atual de `Base`, `Execution`, `Query` (SPEC-0012/0013/0015).
- `src/app/auth.py` — `Identity(tenant_id, project_id, role)`, `require_write_role` (papéis de escrita: `owner`, `admin`).
- `src/app/routers/bases.py`, `src/app/routers/executions.py`, `src/app/routers/queries.py` — fluxo de upload, agendamento (`_agendar` usa `settings.vector_store` fixo) e consulta (mesmo padrão fixo).
- `src/app/settings.py` — `AppSettings.vector_store` é um dicionário único, global, configurado uma vez no entrypoint.
- `src/app/tasks.py` — `scope_project_id` (isolamento lógico por `tenant_id::project_id::base_id`), `process_base_task` (orquestra chunking + indexação via `src/pipeline/service`).
- `src/pipeline/chunker.py`, `config.yaml` — splitters e parâmetros de chunk já configuráveis por config global/frontmatter, mas sem hook de metadata customizado por upload.
- `INTERFACE.md` — telas, blocos React e convenções de composição atuais (`PageHeader`, `DataGridBases`, `UploadBaseSheet`, `Sheet`, `Dialog`).
- `alembic/versions/` — três revisões existentes (`074d455d6f67`, `4d0fd0aa498e`, `f3b60ce4f7f4`); convenção de migração incremental sem `migrate:fresh`.

#### Documentação consultada

- Nenhuma documentação externa consultada.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: O "Projeto" que agrupa bases é o mesmo `project_id` técnico já existente? → **A**: Não; é uma entidade nova, acima das Bases atuais, sem mudar o `project_id` técnico de isolamento.
- **Q**: Que nome usar para não colidir com "projeto" (já usado no sentido técnico)? → **A**: "Workspace".
- **Q**: Toda Base pertence obrigatoriamente a um Workspace, ou é opcional? → **A**: Obrigatório; Bases pré-existentes migram para um Workspace padrão criado na migração.
- **Q**: O que acontece ao apagar um Workspace com Bases dentro? → **A**: Bloqueado; a pessoa precisa apagar ou mover as Bases antes.
- **Q**: Quem pode gerenciar Workspaces? → **A**: Owner e admin criam/editam/apagam e enviam arquivos; member só visualiza (corrigido nesta conversa para bater com `require_write_role`, já que a resposta inicial de que "member também envia" conflitava com o código atual).
- **Q**: O Workspace guarda mais campos além do nome? → **A**: Não; apenas um nome livre curto.
- **Q**: Como informar metadados customizados por chunk? → **A**: Pares livres de rótulo e valor, definidos a cada upload, sem lista fixa pré-definida.
- **Q**: A escolha de coleção e a estratégia de chunking (splitter/tamanho/overlap) são uma tela de configurações global? → **A**: Não; são valores por upload/Base (decisão do item de backlog 0023, dependência desta spec para o campo de coleção).

#### Dúvidas abertas

- Nenhuma bloqueante. Duas questões de baixo impacto ficaram com default reversível documentado em Suposições (seção 16): comportamento de Workspace vazio e ausência de ação para mover Base entre Workspaces nesta entrega.

### 3. Escopo e atores

#### Incluído

- Entidade **Workspace**: criar, listar, ver detalhe, editar nome, apagar (bloqueado com Bases dentro).
- Campo `workspace_id` obrigatório em `Base`; upload exige escolher o Workspace de destino.
- Campo `collection_name` em `Base`, informável no upload; quando omitido, recebe um default derivado do Workspace.
- Agendamento de execução (`POST /bases/{id}/executions`) e consulta (`POST /bases/{id}/query`) passam a usar o `collection_name` armazenado na Base em vez do valor fixo de `AppSettings.vector_store`.
- Campo de metadados customizados (`metadados_chunk`, pares rótulo/valor) em `Base`, informável no upload, propagado ao metadata de cada chunk gerado a partir dela.
- Migração idempotente que cria um Workspace padrão por combinação de `tenant_id`/`project_id` técnico e associa as Bases pré-existentes a ele.
- Telas: listagem de Workspaces (`/workspaces`), detalhe de um Workspace (`/workspaces/[id]`, que assume o papel da listagem plana de bases hoje em `/projeto`), formulário de criar/editar Workspace, diálogo de apagar Workspace, e `UploadBaseSheet` estendido com os campos de coleção e metadados.
- Conversão de `/projeto` em redirect permanente para `/workspaces`, preservando os cenários de navegação já aceitos pela SPEC-0013 (DEC-005).
- Autorização: `owner`/`admin` gerenciam Workspaces e enviam Bases; `member` só visualiza.

#### Fora de escopo

- Campos de estratégia de chunking (splitter, tamanho, overlap) na interface — item de backlog 0023, ainda não especificado.
- Escolha de backend de vector store (Qdrant/Chroma/Pinecone) — apenas Qdrant continua suportado (SPEC-0010).
- Provider de LLM plugável — backlog 0010, item próprio.
- Ação de mover uma Base entre Workspaces já existentes.
- Campos adicionais no Workspace (empresa/cliente separados, descrição longa) — só nome livre curto.
- Cadastro, login real ou administração completa de papéis — token estático de demonstração continua (SPEC-0012, DEC-002).
- Qualquer mudança em `src/pipeline/` além de receber metadata adicional já calculado por `src/app/` (o merge de pares customizados acontece em `src/app/tasks.py`, não dentro da fachada do pipeline).

#### Atores

- **Owner**: cria, edita e apaga Workspaces; envia e apaga Bases dentro deles; mesmas permissões de `admin` nesta fatia.
- **Admin**: mesmas permissões de `owner` para esta entrega (papel de escrita, `require_write_role`).
- **Member**: visualiza Workspaces e Bases dentro deles; não cria, edita, apaga Workspace nem envia arquivos.

### 4. Princípios e restrições do projeto

- **PR-001**: O isolamento técnico multi-tenant (`Identity.tenant_id`/`Identity.project_id`, `scope_project_id`) permanece intocado; o Workspace é uma camada de organização que opera **dentro** desse escopo, nunca o substitui.
- **PR-002**: `src/pipeline/` permanece neutro em relação a Workspace e a metadados customizados; qualquer regra nova é aplicada em `src/app/` antes ou depois de chamar a fachada (`service.run_pipeline`/`service.query_base`), na mesma convenção já usada por `scope_project_id`.
- **PR-003**: Nenhum teste desta spec usa o banco de desenvolvimento; migrações e testes rodam contra o banco de teste isolado (`APP_DATABASE_URL` de teste), sem `migrate:fresh`/`RefreshDatabase`/equivalentes destrutivos.
- **PR-004**: Migrações Alembic são incrementais e reversíveis (`upgrade`/`downgrade`), seguindo a convenção das três revisões existentes.

### 5. Histórias de usuário

#### US-001 — Criar e organizar Workspaces (P1)

Como owner ou admin, quero criar, nomear, editar e apagar Workspaces, para organizar minhas bases de conhecimento por cliente ou engajamento.

**Por que P1**: sem essa capacidade, não existe onde agrupar as Bases — é a fundação de toda a entrega.
**Teste independente**: criar um Workspace pela API/tela, confirmar que aparece na listagem, editar seu nome e apagá-lo (vazio).
**Requisitos**: FR-001, FR-002, FR-003, FR-008

#### US-002 — Escolher coleção por Base dentro do Workspace (P1)

Como owner ou admin, quero escolher a coleção do banco vetorial de cada Base que envio dentro de um Workspace, para decidir se compartilho índice com outras Bases do mesmo Workspace ou separo por tipo de conteúdo.

**Por que P1**: é o valor central pedido ("uma coleção só, ou coleções separadas por tipo de conteúdo") — sem isso o Workspace só organiza visualmente, sem afetar a estratégia de RAG.
**Teste independente**: enviar duas Bases do mesmo Workspace com nomes de coleção diferentes e confirmar, por consulta, que os resultados não se misturam.
**Requisitos**: FR-004, FR-005, FR-006

#### US-003 — Metadados customizados por chunk (P2)

Como owner ou admin, quero anexar pares de rótulo e valor aos chunks de uma Base no momento do upload, para taguear e depois filtrar resultados de busca por essas tags.

**Por que P2**: melhora a estratégia de RAG mas não bloqueia o valor central do Workspace (US-002); pode evoluir depois de US-001/US-002 estarem entregues.
**Teste independente**: enviar uma Base com pares de metadata customizados e confirmar que aparecem no payload indexado de cada chunk.
**Requisitos**: FR-007

#### US-004 — Visualização somente leitura para member (P1)

Como member, quero visualizar os Workspaces e as Bases dentro deles sem poder enviar, editar ou apagar nada, para acompanhar o trabalho sem risco de alterar dados.

**Por que P1**: autorização é uma categoria P1 (MCR-10) — sem essa garantia, a entrega expõe uma regressão de segurança em relação ao comportamento já implementado para Bases.
**Teste independente**: autenticar como member, confirmar que a listagem e o detalhe do Workspace aparecem, e que nenhuma ação de escrita fica disponível nem é aceita pela API.
**Requisitos**: FR-008

### 6. Cenários BDD de aceite

#### AC-001 — Owner cria um Workspace com sucesso

**Cobre**: US-001, FR-001, FR-008

```gherkin
@US-001 @FR-001 @FR-008 @AC-001
Feature: Criar Workspace

  Scenario: Owner cria um Workspace com nome válido
    Given uma pessoa autenticada com papel "owner"
    When ela cria um Workspace com o nome "Banda Larga PF — Vivo — Gold"
    Then o Workspace aparece na listagem de Workspaces do seu tenant/projeto
```

#### AC-002 — Owner edita o nome de um Workspace

**Cobre**: US-001, FR-002, FR-008

```gherkin
@US-001 @FR-002 @FR-008 @AC-002
Feature: Editar Workspace

  Scenario: Owner renomeia um Workspace existente
    Given um Workspace chamado "Vivo" pertencente ao tenant/projeto da pessoa
    When ela edita o nome para "Vivo — Banda Larga PF"
    Then o Workspace passa a aparecer com o novo nome
    And as Bases já associadas a ele continuam vinculadas ao mesmo Workspace
```

#### AC-003 — Member não pode criar nem apagar Workspace

**Cobre**: US-001, US-004, FR-001, FR-003, FR-008

```gherkin
@US-001 @US-004 @FR-001 @FR-003 @FR-008 @AC-003
Feature: Autorização de Workspace

  Scenario: Member tenta criar um Workspace
    Given uma pessoa autenticada com papel "member"
    When ela tenta criar um Workspace
    Then a operação é recusada com código 403
    And nenhum Workspace novo é criado

  Scenario: Member tenta apagar um Workspace
    Given um Workspace existente sem Bases dentro
    And uma pessoa autenticada com papel "member"
    When ela tenta apagar esse Workspace
    Then a operação é recusada com código 403
    And o Workspace continua existindo
```

#### AC-004 — Criar Workspace sem nome é rejeitado

**Cobre**: US-001, FR-001

```gherkin
@US-001 @FR-001 @AC-004
Feature: Validação de Workspace

  Scenario: Owner tenta criar um Workspace sem nome
    Given uma pessoa autenticada com papel "owner"
    When ela tenta criar um Workspace com nome vazio
    Then a operação é recusada com código 400
    And nenhum Workspace é criado
```

#### AC-005 — Owner apaga um Workspace vazio

**Cobre**: US-001, FR-003

```gherkin
@US-001 @FR-003 @AC-005
Feature: Apagar Workspace vazio

  Scenario: Owner apaga um Workspace sem Bases dentro
    Given um Workspace sem nenhuma Base ativa associada
    And uma pessoa autenticada com papel "owner"
    When ela apaga esse Workspace
    Then o Workspace deixa de aparecer na listagem
```

#### AC-006 — Apagar Workspace com Bases dentro é bloqueado

**Cobre**: US-001, FR-003, NFR-002

```gherkin
@US-001 @FR-003 @NFR-002 @AC-006
Feature: Bloqueio de exclusão de Workspace

  Scenario: Owner tenta apagar um Workspace que ainda tem Bases
    Given um Workspace com ao menos uma Base ativa associada
    And uma pessoa autenticada com papel "owner"
    When ela tenta apagar esse Workspace
    Then a operação é recusada com código 409
    And a mensagem de erro explica a consequência sem expor detalhe interno
    And o Workspace e suas Bases continuam existindo
```

#### AC-007 — Owner envia uma Base escolhendo o Workspace de destino

**Cobre**: US-002, FR-004, FR-008

```gherkin
@US-002 @FR-004 @FR-008 @AC-007
Feature: Upload de Base associado a um Workspace

  Scenario: Owner envia arquivos indicando o Workspace de destino
    Given um Workspace existente
    And uma pessoa autenticada com papel "owner"
    When ela envia arquivos Markdown indicando esse Workspace como destino
    Then a Base criada aparece na listagem desse Workspace
```

#### AC-008 — Upload sem Workspace de destino é rejeitado

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-008
Feature: Validação de upload

  Scenario: Owner tenta enviar arquivos sem indicar um Workspace
    Given uma pessoa autenticada com papel "owner"
    When ela tenta enviar arquivos Markdown sem indicar um Workspace de destino
    Then a operação é recusada com código 400
    And nenhuma Base é criada
```

#### AC-009 — Owner escolhe um nome de coleção customizado no upload

**Cobre**: US-002, FR-005

```gherkin
@US-002 @FR-005 @AC-009
Feature: Coleção customizada por Base

  Scenario: Owner informa um nome de coleção ao enviar uma Base
    Given um Workspace existente
    And uma pessoa autenticada com papel "owner"
    When ela envia uma Base informando o nome de coleção "politicas"
    Then a Base criada é registrada com `collection_name` igual a "politicas"
```

#### AC-010 — Upload sem nome de coleção usa o default do Workspace

**Cobre**: US-002, FR-005

```gherkin
@US-002 @FR-005 @AC-010
Feature: Default de coleção

  Scenario: Owner envia uma Base sem informar nome de coleção
    Given um Workspace existente
    And uma pessoa autenticada com papel "owner"
    When ela envia uma Base sem informar nome de coleção
    Then a Base criada recebe o nome de coleção padrão derivado do Workspace
```

#### AC-011 — Execução usa o `collection_name` da Base, não um valor fixo global

**Cobre**: US-002, FR-006, NFR-003

```gherkin
@US-002 @FR-006 @NFR-003 @AC-011
Feature: Agendamento de execução por coleção da Base

  Scenario: Iniciar execução de uma Base com coleção customizada
    Given uma Base com `collection_name` igual a "produtos"
    When a pessoa inicia a execução dessa Base
    Then o job agendado usa "produtos" como coleção de destino
    And não usa o valor fixo de `AppSettings.vector_store`
```

#### AC-012 — Duas Bases do mesmo Workspace em coleções diferentes não se misturam

**Cobre**: US-002, FR-006, NFR-003

```gherkin
@US-002 @FR-006 @NFR-003 @AC-012
Feature: Isolamento por coleção

  Scenario: Consultar uma Base cuja coleção é diferente de outra do mesmo Workspace
    Given duas Bases do mesmo Workspace, uma com `collection_name` "produtos" e outra "politicas", ambas indexadas com sucesso
    When a pessoa consulta a Base "politicas"
    Then os resultados retornados vêm somente da coleção "politicas"
    And nenhum chunk da coleção "produtos" aparece na resposta
```

#### AC-013 — Mesmo nome de coleção em Workspaces diferentes preserva isolamento

**Cobre**: FR-005, FR-006, NFR-003

```gherkin
@FR-005 @FR-006 @NFR-003 @AC-013
Feature: Isolamento por escopo lógico mesmo com nome de coleção repetido

  Scenario: Duas Bases de Workspaces diferentes usam o mesmo nome de coleção
    Given uma Base do Workspace "A" e uma Base do Workspace "B", ambas com `collection_name` igual a "geral"
    When cada uma é indexada e depois consultada separadamente
    Then cada consulta retorna somente os chunks da própria Base
    And o escopo lógico (`scope_project_id`) continua isolando por tenant/projeto/base dentro da mesma coleção
```

#### AC-014 — Owner anexa metadados customizados no upload

**Cobre**: US-003, FR-007

```gherkin
@US-003 @FR-007 @AC-014
Feature: Metadados customizados por chunk

  Scenario: Owner envia uma Base com pares de rótulo e valor
    Given um Workspace existente
    And uma pessoa autenticada com papel "owner"
    When ela envia uma Base informando o par "categoria" = "politica"
    And a execução dessa Base é concluída com sucesso
    Then cada chunk indexado a partir dessa Base carrega "categoria" = "politica" no seu metadata
```

#### AC-015 — Upload sem metadados customizados não gera erro

**Cobre**: US-003, FR-007

```gherkin
@US-003 @FR-007 @AC-015
Feature: Metadados customizados opcionais

  Scenario: Owner envia uma Base sem nenhum par customizado
    Given um Workspace existente
    And uma pessoa autenticada com papel "owner"
    When ela envia uma Base sem informar nenhum par de rótulo/valor
    Then a Base é criada normalmente
    And os chunks gerados não recebem pares extras além dos já existentes
```

#### AC-016 — Rótulo duplicado no upload é rejeitado

**Cobre**: US-003, FR-007

```gherkin
@US-003 @FR-007 @AC-016
Feature: Validação de metadados customizados

  Scenario: Owner envia dois pares com o mesmo rótulo
    Given um Workspace existente
    And uma pessoa autenticada com papel "owner"
    When ela tenta enviar uma Base com dois pares usando o rótulo "categoria"
    Then a operação é recusada com código 400
    And nenhuma Base é criada
```

#### AC-017 — Member visualiza Workspaces e Bases sem ações de escrita

**Cobre**: US-004, FR-008

```gherkin
@US-004 @FR-008 @AC-017
Feature: Visualização somente leitura

  Scenario: Member acessa a listagem e o detalhe de um Workspace
    Given uma pessoa autenticada com papel "member"
    And um Workspace com ao menos uma Base dentro
    When ela abre a listagem de Workspaces e o detalhe desse Workspace
    Then ela visualiza o Workspace e suas Bases
    And nenhuma ação de criar, editar, apagar Workspace ou enviar Base fica disponível na tela
```

#### AC-018 — Member não pode enviar Base mesmo chamando a API diretamente

**Cobre**: US-002, US-004, FR-004, FR-008

```gherkin
@US-002 @US-004 @FR-004 @FR-008 @AC-018
Feature: Autorização de upload

  Scenario: Member tenta enviar arquivos diretamente pela API
    Given um Workspace existente
    And uma pessoa autenticada com papel "member"
    When ela tenta enviar arquivos Markdown para esse Workspace pela API
    Then a operação é recusada com código 403
    And nenhuma Base é criada
```

#### AC-019 — Migração cria Workspace padrão e associa Bases pré-existentes

**Cobre**: FR-009, NFR-001

```gherkin
@FR-009 @NFR-001 @AC-019
Feature: Migração de Bases existentes

  Scenario: Rodar a migração sobre um banco com Bases sem Workspace
    Given um banco com Bases pré-existentes sem `workspace_id`, para um mesmo tenant/projeto técnico
    When a migração é executada (`alembic upgrade head`)
    Then um Workspace padrão é criado para esse tenant/projeto técnico
    And todas as Bases correspondentes passam a ter `workspace_id` preenchido com esse Workspace padrão
```

#### AC-020 — Migração é idempotente

**Cobre**: FR-009, NFR-001

```gherkin
@FR-009 @NFR-001 @AC-020
Feature: Idempotência da migração

  Scenario: Rodar a migração novamente sobre um banco já migrado
    Given um banco onde a migração de Workspace padrão já foi aplicada
    When a migração é executada novamente
    Then nenhum Workspace padrão duplicado é criado
    And nenhuma Base já associada tem seu `workspace_id` alterado
```

#### AC-021 — Reverter a migração preserva dados existentes

**Cobre**: FR-009, NFR-001

```gherkin
@FR-009 @NFR-001 @AC-021
Feature: Reversão da migração

  Scenario: Reverter a migração de Workspace
    Given um banco com Workspaces e Bases associadas criados por esta migração
    When a migração é revertida (`alembic downgrade`)
    Then a tabela de Workspaces e a coluna `workspace_id` de `bases` deixam de existir
    And nenhum dado de Bases, Execuções ou Queries é perdido
```

#### AC-022 — Editar Workspace com nome vazio é rejeitado

**Cobre**: FR-002, NFR-002

```gherkin
@FR-002 @NFR-002 @AC-022
Feature: Validação de edição de Workspace

  Scenario: Owner tenta apagar o nome de um Workspace
    Given um Workspace existente com nome "Vivo"
    And uma pessoa autenticada com papel "owner"
    When ela tenta editar o nome desse Workspace para um valor vazio
    Then a operação é recusada com código 400
    And o nome anterior "Vivo" é mantido
```

#### AC-023 — Member não pode editar Workspace

**Cobre**: FR-002, FR-008, NFR-002

```gherkin
@FR-002 @FR-008 @NFR-002 @AC-023
Feature: Autorização de edição

  Scenario: Member tenta editar o nome de um Workspace
    Given um Workspace existente
    And uma pessoa autenticada com papel "member"
    When ela tenta editar o nome desse Workspace
    Then a operação é recusada com código 403
    And o nome do Workspace permanece inalterado
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve permitir que `owner`/`admin` criem um Workspace informando um nome livre curto obrigatório.
- **FR-002**: O sistema deve permitir que `owner`/`admin` editem o nome de um Workspace existente, exigindo nome não vazio.
- **FR-003**: O sistema deve bloquear a exclusão de um Workspace enquanto existir ao menos uma Base ativa (não apagada) associada a ele.
- **FR-004**: O sistema deve exigir que toda Base pertença a exatamente um Workspace; o envio de arquivos exige indicar o Workspace de destino.
- **FR-005**: O sistema deve permitir que, ao enviar uma Base, a pessoa informe um nome de coleção do banco vetorial (`collection_name`); quando omitido, o sistema atribui um nome padrão derivado do Workspace de destino.
- **FR-006**: O sistema deve usar o `collection_name` armazenado na Base — não um valor fixo de `AppSettings.vector_store` — ao agendar a execução de indexação e ao consultar essa Base.
- **FR-007**: O sistema deve permitir que, ao enviar uma Base, a pessoa informe pares de rótulo/valor customizados (rótulos não repetidos no mesmo envio), anexados ao metadata de cada chunk gerado a partir dessa Base.
- **FR-008**: O sistema deve restringir criação, edição e exclusão de Workspace, e envio de Base, a `owner`/`admin`; `member` só visualiza Workspaces e Bases.
- **FR-009**: O sistema deve migrar, de forma idempotente, as Bases pré-existentes sem Workspace para um Workspace padrão criado automaticamente por combinação de `tenant_id`/`project_id` técnico.

#### Não funcionais

- **NFR-001**: A migração de dados (FR-009) deve ser reversível via `alembic downgrade` sem perda de dados de Bases, Execuções ou Queries existentes. **Verificação**: teste de migração cobrindo upgrade e downgrade (`tests/test_app_migrations.py`).
- **NFR-002**: Mensagens de erro para exclusão bloqueada, validação e negação de autorização não expõem detalhe interno de implementação, seguindo a mesma política já aplicada a Bases (SPEC-0012). **Verificação**: teste de contrato de erro por cenário (403/400/409).
- **NFR-003**: O isolamento lógico entre tenants/projetos técnicos (`scope_project_id`) continua garantido mesmo quando múltiplas Bases compartilham ou diferem no `collection_name`. **Verificação**: teste caracterizando escopo de leitura/escrita por coleção e por `scope_project_id`.

#### Erros e casos-limite

- Criar/editar Workspace com nome vazio → 400, nada é alterado (AC-004, AC-022).
- Apagar Workspace com Bases dentro → 409, nada é apagado (AC-006).
- Enviar Base sem Workspace de destino → 400, nenhuma Base criada (AC-008).
- Enviar Base com par de metadata de rótulo repetido → 400, nenhuma Base criada (AC-016).
- Qualquer ação de escrita tentada por `member` → 403, nenhum dado alterado (AC-003, AC-007 negativo implícito, AC-018, AC-023).

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

Backend Python 3.12+/FastAPI (`src/app/`) com PostgreSQL via SQLAlchemy + Alembic (`src/app/models.py`, `src/app/db.py`), fila Procrastinate (`src/app/tasks.py`) e fachada neutra `src/pipeline/service.py`. Autenticação por token estático de demonstração (`src/app/auth.py`, `Identity(tenant_id, project_id, role)`, `require_write_role` para `owner`/`admin`). Hoje `Base` já carrega `tenant_id`/`project_id` técnicos; `AppSettings.vector_store` é único e global, injetado no entrypoint e repassado sem alteração a cada execução (`executions.py::_agendar`) e a cada consulta (`queries.py::consultar_base`). Frontend Next.js 16 App Router (`frontend/`) com shadcn/ui + ReUI, telas `/login`, `/projeto` (listagem plana de bases) e `/execucoes/[id]` (detalhe), documentadas em `INTERFACE.md`.

#### Arquitetura e módulos

- Novo model `Workspace` em `src/app/models.py`, na mesma tabela/módulo de `Base`/`Execution`/`Query`.
- `Base` ganha três colunas novas: `workspace_id` (FK, `NOT NULL` após backfill), `collection_name` (String, `NOT NULL`), `metadados_chunk` (JSON, lista de `{rotulo, valor}`, default lista vazia).
- Novo router `src/app/routers/workspaces.py`: `POST /api/v1/workspaces`, `GET /api/v1/workspaces`, `GET /api/v1/workspaces/{id}`, `PATCH /api/v1/workspaces/{id}`, `DELETE /api/v1/workspaces/{id}`.
- `src/app/routers/bases.py::enviar_base` passa a exigir `workspace_id` (form field), aceitar `collection_name` opcional (default derivado do Workspace) e `metadados_chunk` opcional (JSON serializado em form field, validado sem rótulo repetido).
- `src/app/routers/executions.py::_agendar` e `src/app/routers/queries.py::consultar_base` passam a montar `vector_store` a partir de `dict(settings.vector_store) | {"collection_name": base.collection_name}` em vez do dicionário fixo.
- `src/app/tasks.py::process_base_task` recebe os pares de `metadados_chunk` da Base e, após `service.run_pipeline`, mescla cada par no `.metadata` de cada item em `resultado.chunks` antes de `sync_vector_store` — sem tocar `src/pipeline/`.
- `src/app/repo.py` ganha `list_workspaces_for_identity`, `get_workspace_or_404`, `count_active_bases_for_workspace`, seguindo o padrão já usado por `get_base_or_404`/`list_bases_for_identity`.

#### Migrations

Uma revisão Alembic nova (ou duas, se a equipe de implementação preferir separar schema de backfill):

1. `upgrade`: cria tabela `workspaces` (`id`, `tenant_id`, `project_id`, `nome`, `criado_em`, `apagada_em`); adiciona `bases.workspace_id` (nullable), `bases.collection_name` (nullable), `bases.metadados_chunk` (JSON, default `[]`).
2. Backfill idempotente: para cada combinação distinta de `(tenant_id, project_id)` em `bases` sem `workspace_id`, cria um `Workspace` com nome "Workspace padrão" e associa todas as Bases correspondentes; preenche `collection_name` das Bases existentes com o valor hoje fixo em `AppSettings.vector_store` (preservando o comportamento atual sem regressão).
3. Torna `bases.workspace_id` e `bases.collection_name` `NOT NULL` depois do backfill.
4. `downgrade`: remove as colunas de `bases` e a tabela `workspaces`, sem tocar `executions`/`queries`.

Segue a mesma convenção das revisões existentes (`074d455d6f67` → `4d0fd0aa498e` → `f3b60ce4f7f4`); a suíte de `src/app/` continua materializando o schema de teste por `metadata.create_all`, com a revisão também aplicada ao banco de scratch de `tests/test_app_migrations.py`.

#### Models

- **Workspace** (`src/app/models.py`): `id` (UUID), `tenant_id`, `project_id` (escopo técnico, mesma convenção de `Base`), `nome` (String, não vazio — validado no router, não como `CHECK` de banco), `criado_em`, `apagada_em` (exclusão lógica, mesmo padrão de `Base`).
- **Base** (atualizado): `+ workspace_id` (FK `workspaces.id`, `NOT NULL`), `+ collection_name` (String, `NOT NULL`), `+ metadados_chunk` (JSON, lista de pares, default `[]`).

#### Controllers e casos de uso

- `workspaces.py::criar_workspace` — `require_write_role`; valida nome não vazio; retorna 201.
- `workspaces.py::listar_workspaces` — leitura livre (owner/admin/member), escopado por `identity.tenant_id`/`identity.project_id`.
- `workspaces.py::obter_workspace` — leitura livre; 404 se não pertencer ao escopo do token.
- `workspaces.py::editar_workspace` — `require_write_role`; valida nome não vazio; 400 se vazio.
- `workspaces.py::apagar_workspace` — `require_write_role`; 409 se `count_active_bases_for_workspace > 0`; senão exclusão lógica (`apagada_em`).
- `bases.py::enviar_base` — `require_write_role` (já existente); novo parâmetro obrigatório `workspace_id` (400 se ausente ou não pertencer ao escopo); `collection_name` opcional (default = nome derivado do Workspace, ex. slug do `workspace_id`); `metadados_chunk` opcional (400 se rótulo repetido).
- `executions.py::_agendar` e `queries.py::consultar_base` — leem `base.collection_name` da linha já carregada, sobrescrevendo a chave `collection_name` do dicionário de `vector_store` antes de despachar/consultar.

#### Views e experiência

- Ver seção 10 (Interfaces e contratos) para o detalhamento completo de telas, componentes e estados.

#### Queries e repositórios

- `repo.list_workspaces_for_identity(session, identity)`: filtra por `tenant_id`/`project_id`, exclui `apagada_em` preenchido.
- `repo.get_workspace_or_404(session, workspace_id, identity)`: mesmo padrão de `get_base_or_404`.
- `repo.count_active_bases_for_workspace(session, workspace_id)`: `COUNT(*)` de `bases` com `workspace_id` igual e `apagada_em IS NULL`.

#### Jobs e processamento assíncrono

- `process_base_task` (Procrastinate) ganha o parâmetro `metadados_chunk: list[dict]`; após `service.run_pipeline`, itera `resultado.chunks` e faz `chunk.metadata.update({par["rotulo"]: par["valor"] for par in metadados_chunk})` antes de `sync_vector_store`.

#### Estrutura de arquivos

```text
specs/defined/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/
  spec.md
  research/            (vazio — nenhuma fonte externa)
src/app/
  models.py            (+ Workspace, + colunas em Base)
  repo.py              (+ funções de Workspace)
  routers/
    workspaces.py       (novo)
    bases.py            (+ workspace_id/collection_name/metadados_chunk no upload)
    executions.py        (+ collection_name da Base no agendamento)
    queries.py            (+ collection_name da Base na consulta)
  tasks.py              (+ merge de metadados_chunk nos chunks)
alembic/versions/
  <nova revisão>        (workspaces + colunas em bases + backfill)
frontend/src/
  app/(autenticado)/
    workspaces/page.tsx           (novo — lista de Workspaces)
    workspaces/[id]/page.tsx      (novo — detalhe: bases do Workspace)
  features/workspaces/
    DataGridWorkspaces.tsx        (novo)
    WorkspaceFormSheet.tsx        (novo — criar/editar)
    ExcluirWorkspaceDialog.tsx    (novo)
  features/bases/
    UploadBaseSheet.tsx           (+ campos de coleção e metadados)
tests/
  test_app_workspaces.py          (novo)
  test_app_bases.py               (+ casos de workspace_id/collection_name/metadados)
  test_app_migrations.py          (+ upgrade/downgrade/idempotência da nova revisão)
frontend/src/features/workspaces/__tests__/  (novo)
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `Workspace` | `id` (UUID) | `tenant_id`, `project_id` (escopo técnico); `nome` (texto curto, não vazio); `criado_em`; `apagada_em` (exclusão lógica) | Tem várias `Base`; exclusão bloqueada enquanto houver `Base` ativa associada |
| `Base` (atualizado) | `id` (UUID) | `+ workspace_id` (FK `workspaces.id`, `NOT NULL`); `+ collection_name` (texto, `NOT NULL`, default derivado do Workspace quando omitido no upload); `+ metadados_chunk` (JSON, lista de `{rotulo, valor}`, rótulos únicos por Base, default `[]`) | Pertence a exatamente um `Workspace`; continua tendo várias `Execution` e `Query` |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| `Workspace` | Ativo (sem Bases) | `apagar_workspace` | Apagado (`apagada_em` preenchido) | Só permitido quando `count_active_bases_for_workspace = 0` |
| `Workspace` | Ativo (com Bases) | tentativa de `apagar_workspace` | Permanece ativo | Operação recusada (409), nenhum dado alterado |
| `Base` | Sem execução | `enviar_base` | Associada a um `Workspace`, com `collection_name` definido | `workspace_id` sempre preenchido; `collection_name` sempre preenchido (informado ou default) |

#### Migração e retenção

- Backfill único, idempotente, executado pela migração Alembic (seção 8): cria um Workspace padrão por `(tenant_id, project_id)` técnico e associa as Bases pré-existentes; preenche `collection_name` das Bases existentes com o valor hoje fixo em `AppSettings.vector_store`, preservando o comportamento atual de indexação/consulta dessas Bases.
- Retenção do Workspace segue a mesma política de exclusão lógica já usada em `Base` (preserva `apagada_em`, sem apagar a linha).

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. A entrega troca a listagem plana de bases (`/projeto`) por uma navegação em dois níveis (Workspaces → Bases dentro de um Workspace) e estende o formulário de upload existente. `/projeto` permanece como redirect para `/workspaces` (DEC-005), sem invalidar os cenários da SPEC-0013.

#### Stack e convenções de interface

- Next.js 16 App Router, React 19, TypeScript, Tailwind CSS v4, shadcn/ui (preset `base-nova`) e ReUI (`@reui/c-*`), conforme `INTERFACE.md`. Testes com Vitest + Testing Library (`test:tdd` = `vitest run`). Cliente HTTP único `frontend/src/lib/api-client.ts`; sessão em `frontend/src/lib/session.ts`. Layout autenticado existente (`app/(autenticado)/layout.tsx`) é reaproveitado sem mudança de guarda de sessão.

#### Telas e responsabilidades

- **Listagem de Workspaces** (`/workspaces`, passa a ser a página inicial pós-login no lugar de `/projeto`): lista os Workspaces do tenant/projeto; ação "Criar Workspace" (owner/admin); cada linha leva ao detalhe.
- **Detalhe do Workspace** (`/workspaces/[id]`): reaproveita `DataGridBases` filtrado pelo `workspace_id`; ação "Enviar base" abre `UploadBaseSheet` já associado a esse Workspace; ações "Editar nome" e "Apagar Workspace" (owner/admin, a segunda bloqueada com Bases dentro).
- **Detalhe de execução** (`/execucoes/[id]`): sem mudança de responsabilidade; passa a exibir também o nome do Workspace e o `collection_name` da Base no `PageHeader` (contexto).

#### Fluxo de informação e navegação

- Login → `/workspaces` (lista) → clique/Enter na linha → `/workspaces/{id}` (detalhe, bases do Workspace) → clique/Enter na linha de uma Base → `/execucoes/{id}` (detalhe da base), como hoje. `Breadcrumb` de `/workspaces/{id}` mostra "Equipe → Workspaces → {nome do Workspace}"; `Breadcrumb` de `/execucoes/{id}` passa a incluir o Workspace: "Equipe → Workspaces → {Workspace} → {Base}".
- A rota `/projeto` deixa de renderizar a listagem plana e passa a redirecionar para `/workspaces` (DEC-005). O redirect preserva links salvos e mantém válidos os cenários de navegação aceitos pela SPEC-0013, que continuam observáveis: quem chega em `/projeto` autenticado termina numa listagem de bases — agora dentro do Workspace. O redirect de `LoginForm` (`frontend/src/features/auth/LoginForm.tsx:39`) passa a apontar para `/workspaces`, e seu teste (`LoginForm.test.tsx:40`) é atualizado junto, na mesma tarefa.

#### Menus e navegação principal

- Não há menu lateral hoje (`INTERFACE.md` não registra um); a navegação principal continua sendo o `Breadcrumb` e as linhas clicáveis dos `DataGrid`. Sem mudança estrutural de menu nesta entrega.

#### Formulários e ações

- **Criar/editar Workspace** (`WorkspaceFormSheet`, painel lateral — mesmo padrão de `Sheet` já usado por `UploadBaseSheet`): campo único "Nome", obrigatório, texto curto; ação "Salvar"; erro inline (`Alert role="alert"`) para nome vazio.
- **Apagar Workspace** (`ExcluirWorkspaceDialog`, modal — mesmo padrão de `ExcluirBaseDialog`): mostra nome do Workspace; se houver Bases dentro, o botão "Apagar" fica desabilitado com texto explicando a consequência ("Apague ou mova as bases deste Workspace antes de continuar"); se vazio, confirma a exclusão.
- **Upload de Base** (`UploadBaseSheet`, estendido): mantém o input de arquivos `.md` existente; adiciona um campo opcional "Nome da coleção" (texto curto, com hint "Deixe em branco para usar o padrão deste Workspace") e uma lista editável de pares "Rótulo"/"Valor" (adicionar/remover linha), com validação de rótulo não repetido antes de chamar o backend — mesma disciplina de validação client-side já aplicada aos limites de arquivo.

#### Composição e disposição

- `/workspaces`: `PageHeader` (título "Workspaces", ação "Criar Workspace") + `DataGridWorkspaces` em largura total, coluna `ID` visível, linha inteira como link para o detalhe.
- `/workspaces/[id]`: `PageHeader` (título = nome do Workspace, ações "Enviar base", "Editar nome", "Apagar Workspace") + `DataGridBases` (reaproveitado, sem mudança de props além do filtro por `workspace_id` já aplicado no `GET /api/v1/bases?workspace_id=`).
- Ambas as telas refluem para coluna única em mobile, mesma convenção das telas existentes.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| `/workspaces` | `DataGridWorkspaces` | Listagem de Workspaces, linha clicável | `frontend/src/features/workspaces/DataGridWorkspaces.tsx` | Tabela semântica | Próprio | Novo, espelha `DataGridBases` |
| `/workspaces` e `/workspaces/[id]` | `WorkspaceFormSheet` | Criar/editar nome do Workspace | `frontend/src/features/workspaces/WorkspaceFormSheet.tsx` | `Sheet` (shadcn/ui) | Próprio, reaproveita `Sheet` | Novo, mesmo padrão de `UploadBaseSheet` |
| `/workspaces/[id]` | `ExcluirWorkspaceDialog` | Confirmação/bloqueio de exclusão | `frontend/src/features/workspaces/ExcluirWorkspaceDialog.tsx` | `Dialog` (shadcn/ui) | Próprio, reaproveita `Dialog` | Novo, espelha `ExcluirBaseDialog` |
| `/workspaces/[id]` | `DataGridBases` | Listagem de Bases do Workspace | `frontend/src/features/bases/DataGridBases.tsx` | Tabela semântica | Existente (SPEC-0013) | Reuso direto, com filtro por `workspace_id` |
| `/workspaces/[id]` | `UploadBaseSheet` | Envio de Base + coleção + metadados | `frontend/src/features/bases/UploadBaseSheet.tsx` | `Sheet` (shadcn/ui) | Existente (SPEC-0013) | Estendido com dois campos novos |
| `/workspaces/[id]` | `Input`/`Label`/`Button` | Campos de coleção e pares de metadata | `frontend/src/components/ui/{input,label,button}.tsx` | Primitives shadcn/ui | Existente | Reuso direto |

#### Estados e acessibilidade

- Listagem de Workspaces: carregando (skeleton, mesmo padrão de `DataGridBases`), vazio ("Nenhum Workspace ainda" + convite a criar), erro de leitura (`Alert`), sucesso.
- Detalhe do Workspace: carregando, 404 ("Workspace não encontrado"), vazio (Workspace sem Bases, com convite a enviar), sucesso (lista de Bases), exclusão bloqueada (mensagem inline no diálogo, não apenas cor — mesma disciplina de `ChunksFontes`/AC-018 do SPEC-0013).
- `Breadcrumb` de ambas as telas mantém a equipe visível e marca a tela atual com semântica de página, mesma convenção das telas existentes.
- Formulário de upload: erro de rótulo repetido anunciado em `Alert role="alert"` antes de chamar o backend.

#### Contrato CRUD

- `PageHeader` único e reutilizável entre `/workspaces` (lista) e `/workspaces/[id]` (detalhe), variando por props (`title`, `actions`), sem duplicar markup — mesma regra já aplicada a Bases.
- `DataGridWorkspaces` ocupa toda a largura disponível, mantém a coluna `ID` visível, transforma a linha inteira em link para o detalhe por mouse e teclado, e não expõe "editar"/"apagar" na própria linha (essas ações ficam no `PageHeader` do detalhe, já que Workspace não tem tela de edição dedicada — o `WorkspaceFormSheet` abre sobre a tela atual).
- Registrar em `INTERFACE.md`, na tarefa de implementação, os blocos novos e os reaproveitados, seus consumidores e o componente shadcn/ui/ReUI de origem.

#### Revisão visual durante o desenvolvimento

- Ocorre durante a implementação das tarefas de interface (seção 14, fase de interface), cobrindo bordas, espaçamentos, margens, padding e tipografia nas duas telas novas e no `UploadBaseSheet` estendido, nos viewports desktop e mobile e nos estados listados acima.

#### APIs expostas

- `POST /api/v1/workspaces` — autenticado, `owner`/`admin`; body `{nome}`; 201 com `{id, nome}`; 400 se nome vazio.
- `GET /api/v1/workspaces` — autenticado, qualquer papel; retorna Workspaces do tenant/projeto do token.
- `GET /api/v1/workspaces/{id}` — autenticado, qualquer papel; 404 fora do escopo do token.
- `PATCH /api/v1/workspaces/{id}` — autenticado, `owner`/`admin`; body `{nome}`; 400 se vazio; 403 se `member`.
- `DELETE /api/v1/workspaces/{id}` — autenticado, `owner`/`admin`; 409 se houver Base ativa associada; 204 em sucesso.
- `POST /api/v1/bases` (atualizado) — novos campos de form: `workspace_id` (obrigatório), `collection_name` (opcional), `metadados_chunk` (opcional, JSON serializado); mesmas regras de autenticação/autorização já existentes.
- `GET /api/v1/bases?workspace_id=` (atualizado) — filtro adicional opcional por Workspace, usado pela tela de detalhe.

#### APIs externas utilizadas

- Nenhuma nova; continua usando Qdrant como único backend real de vector store (SPEC-0010), agora endereçado por `collection_name` variável em vez de fixo.

#### Documentação das APIs consultadas

- Nenhuma documentação externa consultada.

#### Eventos e outros contratos

- Não aplicável — sem filas ou eventos novos; `process_base_task` (Procrastinate) já existente ganha um parâmetro adicional (`metadados_chunk`), sem mudar seu contrato de fila.

### 11. Estratégia TDD

- **Unidade**: validação de nome de Workspace não vazio; validação de rótulo de metadata não repetido; derivação do `collection_name` default a partir do Workspace; merge de `metadados_chunk` no `.metadata` de cada chunk (`process_base_task`).
- **Integração/contrato**: endpoints de `workspaces.py` (autorização, 400/403/404/409); `bases.py::enviar_base` com `workspace_id`/`collection_name`/`metadados_chunk`; `executions.py::_agendar` e `queries.py::consultar_base` usando `collection_name` da Base.
- **BDD/aceite**: cenários `AC-001` a `AC-023` da seção 6.
- **Runner TDD**: Python/FastAPI → Pytest (já em uso, `tests/test_app_*.py`); Frontend Next.js → Vitest (`test:tdd` = `vitest run`, já configurado em `frontend/package.json`).
- **E2E**: fluxo "criar Workspace → enviar Base com coleção customizada → consultar" coberto por teste de integração Pytest (sem necessidade de E2E de navegador nesta fatia, mesma decisão de escopo do SPEC-0013).
- **Verificação manual**: revisão visual das duas telas novas e do `UploadBaseSheet` estendido (seção 14, item `VISUAL`), inevitável por não haver E2E de navegador automatizado no projeto.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-008, AC-001 | AC-001 na seção 6 | `test_app_workspaces.py::test_owner_cria_workspace` (marcador `SPECSFY:AC-001`) | Pending | Pending | Pending |
| US-001, FR-003, NFR-002, AC-006 | AC-006 na seção 6 | `test_app_workspaces.py::test_apagar_workspace_com_bases_bloqueado` (marcador `SPECSFY:AC-006`) | Pending | Pending | Pending |
| US-002, FR-005, AC-010 | AC-010 na seção 6 | `test_app_bases.py::test_upload_sem_colecao_usa_default_do_workspace` (marcador `SPECSFY:AC-010`) | Pending | Pending | Pending |
| US-002, FR-006, NFR-003, AC-012 | AC-012 na seção 6 | `test_app_queries.py::test_consulta_isola_por_colecao` (marcador `SPECSFY:AC-012`) | Pending | Pending | Pending |
| US-003, FR-007, AC-014 | AC-014 na seção 6 | `test_app_tasks.py::test_metadados_customizados_no_chunk` (marcador `SPECSFY:AC-014`) | Pending | Pending | Pending |
| US-004, FR-008, AC-017 | AC-017 na seção 6 | `frontend/src/features/workspaces/__tests__/DataGridWorkspaces.test.tsx::member_nao_ve_acoes_de_escrita` (marcador `SPECSFY:AC-017`) | Pending | Pending | Pending |
| FR-009, NFR-001, AC-019 | AC-019 na seção 6 | `test_app_migrations.py::test_migracao_cria_workspace_padrao_e_associa_bases` (marcador `SPECSFY:AC-019`) | Pending | Pending | Pending |

A tabela acima é representativa; a seção 14 (Tarefas) detalha a derivação de RED para todos os 23 `AC` na Fase 1.

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001, AC-003, AC-004 | Integração | `pytest tests/test_app_workspaces.py` | Pending |
| FR-002 | AC-002, AC-022, AC-023 | Integração | `pytest tests/test_app_workspaces.py` | Pending |
| FR-003 | AC-005, AC-006, AC-007 | Integração | `pytest tests/test_app_workspaces.py` | Pending |
| FR-004 | AC-007, AC-008, AC-018 | Integração | `pytest tests/test_app_bases.py` | Pending |
| FR-005 | AC-009, AC-010, AC-013 | Integração | `pytest tests/test_app_bases.py` | Pending |
| FR-006 | AC-011, AC-012, AC-013 | Integração | `pytest tests/test_app_executions.py tests/test_app_queries.py` | Pending |
| FR-007 | AC-014, AC-015, AC-016 | Unidade + Integração | `pytest tests/test_app_tasks.py tests/test_app_bases.py` | Pending |
| FR-008 | AC-001, AC-003, AC-017, AC-018 | Integração | `pytest tests/test_app_workspaces.py tests/test_app_bases.py` | Pending |
| FR-009 | AC-019, AC-020, AC-021 | Integração | `pytest tests/test_app_migrations.py` | Pending |
| NFR-001 | AC-019, AC-020, AC-021 | Integração | `pytest tests/test_app_migrations.py` | Pending |
| NFR-002 | AC-006, AC-022, AC-023 | Integração | `pytest tests/test_app_workspaces.py` | Pending |
| NFR-003 | AC-011, AC-012, AC-013 | Integração | `pytest tests/test_app_queries.py` | Pending |
| US-004 (interface) | AC-017 | Frontend/unidade | `vitest run frontend/src/features/workspaces` | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (2026-09-17)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md`
- **Achados**: validação estrutural `VALID`; cobertura verificada por contagem automática — 23 `AC`, com todos os 4 `US`, 9 `FR` e 3 `NFR` cobertos por pelo menos três `AC` distintos e nenhum `AC` citando ID inexistente. A revisão semântica abriu dois achados `P1`, ambos resolvidos antes da aprovação do gate:
- **FIND-ARCH-001** [P1] [Resolved] A spec removia a rota `/projeto` (seção 10; tarefa T010) sem declarar o impacto sobre a SPEC-0013, já concluída, que define essa rota e a cobre por teste — Refs: US-004, FR-008 — Evidence: frontend/src/features/auth/LoginForm.tsx:39 — Effect: implementar T010 quebraria `LoginForm.test.tsx:40` e invalidaria cenários aceitos de uma spec concluída, sem registro de que era intencional — Suggestion: manter `/projeto` como redirect compatível para `/workspaces`, preservando os cenários da SPEC-0013. Resolvido por DEC-005: a rota vira redirect permanente, T010 foi reescrita para converter em vez de remover e para atualizar o redirect do `LoginForm` junto com seu teste; nenhum cenário da SPEC-0013 é invalidado e `$specsfy-update-spec` não precisa ser acionado.
- **FIND-PROD-002** [P1] [Resolved] A Definition of Done (seção 18) não exigia revisão de `.specsfy/DATABASE.md` nem de `PROJECT.md`, embora a entrega crie a tabela `workspaces` e três colunas em `bases` (seção 9) e acrescente uma capacidade material ao produto — Refs: FR-009, NFR-001 — Evidence: .specsfy/DATABASE.md:27 — Effect: a entrega poderia ser fechada deixando o mapa de persistência e a descrição do produto desatualizados, com o monitor de contexto bloqueando a conclusão depois — Suggestion: acrescentar itens de DoD exigindo esses arquivos atualizados. Resolvido: a seção 18 passou a exigir `.specsfy/DATABASE.md`, `PROJECT.md`, `INTERFACE.md` e `monitor_context.mjs --check` retornando `CURRENT`.
- **Nota de ferramenta**: `review_findings.mjs` precisa ser executado com `--root .` neste repositório; sem esse argumento ele deriva a raiz como `dirname(spec)/../..`, que aponta para `specs/` no layout com pasta de estado e rejeita evidências válidas. Registrado em `specs/inbox/2026-09-17-181959-review-findings-mjs-calcula-a-raiz-errada-no-layout-com-pasta-de-estado.md`.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md`
- **Achados**: Pending.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md .`
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

*Nota de planejamento (`$specsfy-05-tasks` detalha isto no Ato II): esta seção nasce com o esqueleto mínimo de fases: RED TDD informado pelo BDD (todos os 23 `AC`), implementação de Workspace (US-001), upload com coleção e metadados (US-002/US-003), agendamento/consulta por coleção, migração, interface (US-004 e telas), e qualidade final. `specsfy-05-tasks` decompõe cada fase em tarefas `TNNN` completas com o checklist acima antes do `Plan Gate`.*

#### Fase 1 — RED TDD informado pelo BDD

- [ ] T001 [TEST] [TDD] Derivar de AC-001 a AC-023 os casos Pytest/Vitest falhando correspondentes — Refs: AC-001..AC-023 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da seção 6 e confirmar IDs e nível de teste por cenário.
  - [ ] **EXECUTE**: Escrever os casos TDD com marcador próprio `SPECSFY:AC-NNN`, sem criar ou executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido em cada caso.
  - [ ] **VISUAL**: Não aplicável nesta fase — tarefa só materializa teste.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED por caso.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

#### Fase 2 — US-001: Workspace (modelo, migração e API)

**Objetivo**: existir a entidade Workspace, com migração das Bases pré-existentes.
**Teste independente**: criar, editar e apagar um Workspace pela API; migração idempotente comprovada.

- [ ] T002 [CODE] [US-001] Criar model `Workspace` e colunas novas em `Base` em src/app/models.py — Refs: FR-001, FR-002, FR-004, FR-005, FR-007 — Depends: T001
- [ ] T003 [CODE] [US-001] Criar migração Alembic (schema + backfill idempotente + NOT NULL) em alembic/versions/ — Refs: FR-009, NFR-001, AC-019, AC-020, AC-021 — Depends: T002
- [ ] T004 [CODE] [US-001] Implementar `repo.py` (list/get/count de Workspace) e `routers/workspaces.py` (CRUD + autorização) — Refs: FR-001, FR-002, FR-003, FR-008 — Depends: T003

(cada tarefa acima recebe o checklist completo `PREP/EXECUTE/VERIFY/VISUAL/EVIDENCE/IMPROVE` na decomposição de `$specsfy-05-tasks`.)

**Checkpoint**: `pytest tests/test_app_workspaces.py tests/test_app_migrations.py` verde.

#### Fase 3 — US-002/US-003: upload com coleção e metadados

**Objetivo**: upload de Base associado a Workspace, com coleção e metadados customizados.
**Teste independente**: enviar duas Bases do mesmo Workspace em coleções diferentes e confirmar isolamento por consulta.

- [ ] T005 [CODE] [US-002] Estender `routers/bases.py::enviar_base` com `workspace_id`/`collection_name`/`metadados_chunk` — Refs: FR-004, FR-005, FR-007 — Depends: T004
- [ ] T006 [CODE] [US-002] Atualizar `executions.py::_agendar` e `queries.py::consultar_base` para usar `base.collection_name` — Refs: FR-006, NFR-003 — Depends: T005
- [ ] T007 [CODE] [US-003] Mesclar `metadados_chunk` nos chunks em `tasks.py::process_base_task` — Refs: FR-007 — Depends: T005

**Checkpoint**: `pytest tests/test_app_bases.py tests/test_app_executions.py tests/test_app_queries.py tests/test_app_tasks.py` verde.

#### Fase de interface — US-004 e telas

- [ ] T008 [CODE] [US-004] Implementar `/workspaces` e `/workspaces/[id]` com `DataGridWorkspaces`, `WorkspaceFormSheet`, `ExcluirWorkspaceDialog` — Refs: FR-001, FR-002, FR-003, FR-008, AC-017 — Depends: T004
- [ ] T009 [CODE] [US-002] [US-003] Estender `UploadBaseSheet` com campos de coleção e metadados — Refs: FR-005, FR-007 — Depends: T005, T008
- [ ] T010 [CODE] Converter `/projeto` em redirect para `/workspaces`, apontar o redirect de `LoginForm` para `/workspaces` (atualizando `LoginForm.test.tsx`) e ajustar o `Breadcrumb`/navegação para o fluxo Workspaces → Bases — Refs: US-004 — Depends: T008

(cada tarefa recebe o checklist completo, incluindo `VISUAL` com a conferência de bordas/espaçamento/tipografia nos viewports relevantes.)

#### Fase final — Qualidade

- [ ] T011 [TEST] Executar regressão completa e rastreabilidade (`check_traceability.mjs`) — Refs: todos os IDs desta spec — Depends: T002–T010

### 15. Ordem de execução

- Caminho crítico: T001 → T002 → T003 → T004 → T005 → T006/T007 → T008 → T009 → T010 → T011.
- Tarefas paralelas: T006 e T007 podem avançar em paralelo depois de T005 (tocam arquivos diferentes: `executions.py`/`queries.py` vs. `tasks.py`).
- Estratégia de MVP: Fase 2 (Workspace + migração) e Fase 3 (upload com coleção) já entregam o valor central de US-002 (isolamento por coleção); a interface (Fase de interface) e os metadados customizados (US-003) podem seguir em incremento separado se necessário priorizar.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Nenhuma dependência externa nova; usa a mesma infraestrutura (PostgreSQL, Qdrant, Procrastinate) já em produção nesta fatia.
- Backlog 0023 (splitter/chunk_size/chunk_overlap na UI) permanece como entrega separada; esta spec não depende dele para ser implementada, mas o formulário de upload que ele vai estender é o mesmo `UploadBaseSheet` tocado aqui.

#### Riscos

- Alterar o formulário de upload e o agendamento/consulta em três routers ao mesmo tempo → mitigação: backfill preserva o `collection_name` fixo atual para Bases existentes, então nenhuma base já indexada muda de coleção sem ação explícita da pessoa.
- Migração de dados sobre uma tabela `bases` já em uso → mitigação: backfill idempotente, testado por upgrade+downgrade+reexecução (AC-019/020/021), sem `migrate:fresh`.

#### Suposições

- **Suposição (reversível)**: um Workspace pode permanecer vazio (sem Bases) indefinidamente; não há exclusão automática. Se o uso real mostrar necessidade de limpeza, uma spec futura pode adicionar essa regra.
- **Suposição (reversível)**: não existe, nesta entrega, ação para mover uma Base entre Workspaces já existentes; reorganizar exige apagar e reenviar. Se isso se mostrar limitante, entra como spec futura.
- **Suposição (reversível)**: o nome padrão de coleção derivado do Workspace usa o próprio `workspace_id` (ex.: `ws-<uuid>`) como sufixo, por ser estável e não exigir normalização de texto livre; pode evoluir para um slug do nome do Workspace depois.

### 17. Decisões

- **DEC-001**: A nova entidade chama-se "Workspace", não "Projeto", para não colidir com o `project_id` técnico de isolamento multi-tenant já existente e documentado em `.specsfy/DATABASE.md`. Alternativas consideradas: "Cliente", "Pasta". Trade-off: "Workspace" é mais neutro e não amarra a um critério de agrupamento único (cliente), mantendo a entidade útil se um dia agrupar por outro critério.
- **DEC-002**: O merge de `metadados_chunk` acontece em `src/app/tasks.py`, depois de `service.run_pipeline` retornar os chunks, e não dentro de `src/pipeline/`. Razão: preserva `src/pipeline/` neutro em relação a conceitos de `src/app/` (mesma convenção já usada por `scope_project_id`), evitando acoplar a fachada compartilhada a um conceito exclusivo do backend de aplicação.
- **DEC-003**: `owner` e `admin` recebem exatamente as mesmas permissões nesta entrega (sem diferenciação adicional entre os dois papéis de escrita). Razão: `require_write_role` já trata os dois de forma idêntica hoje; diferenciar exigiria uma decisão de produto não solicitada nesta conversa.
- **DEC-004**: A migração usa backfill automático (Workspace padrão por tenant/projeto técnico) em vez de exigir migração manual. Razão: elimina o estado misto "algumas bases com Workspace, outras sem", que complicaria a UI e a autorização.
- **DEC-005**: `/projeto` é mantida como redirect permanente para `/workspaces`, em vez de removida. Razão: a rota é comportamento aceito da SPEC-0013, já concluída (FIND-ARCH-001); o redirect entrega a nova navegação sem invalidar cenários daquela spec nem exigir reabri-la via `$specsfy-update-spec`. Alternativa considerada: remover a rota e atualizar a SPEC-0013 — descartada por custo de reabertura maior que o de manter um redirect. Trade-off: fica uma rota de compatibilidade no código, a ser removida numa limpeza futura se deixar de ter uso.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis (AC-001 a AC-023) passam.
- [ ] Todos os requisitos (FR-001 a FR-009, NFR-001 a NFR-003) possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam (`pytest`, `vitest run`, `ruff`, `check_traceability.mjs`).
- [ ] `.specsfy/DATABASE.md` atualizado com a tabela `workspaces` e as colunas novas de `bases` (`workspace_id`, `collection_name`, `metadados_chunk`), incluindo a revisão Alembic correspondente.
- [ ] `PROJECT.md` revisado quanto à capacidade nova de organizar bases em Workspaces com controle de coleção, ou justificativa registrada de ausência de impacto material.
- [ ] `INTERFACE.md` atualizado com os blocos React novos (`DataGridWorkspaces`, `WorkspaceFormSheet`, `ExcluirWorkspaceDialog`), as telas novas e o `UploadBaseSheet` estendido.
- [ ] `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` retorna `CURRENT`.
