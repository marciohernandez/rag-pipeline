# Especificação integrada: Aplicar o schema da fila no deploy e evitar corrida do create_all

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0042 |
| Slug | 0042-aplicar-o-schema-da-fila-no-deploy-e-evitar-corrida-do-create-all |
| Status | Complete |
| Effort | 5 |
| Effort updated at | 2026-10-22 |
| Effort rationale | Migration idempotente do schema da fila, remoção do create_all com verificação de versão, compensação pós-commit na publicação e ajuste de runbook e testes, sem interface. O risco está na concorrência da subida e em bancos antigos. |
| ClickUp Task | |
| Milestones | M03 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-10-22 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O ensaio local em Docker (2026-10-22, commit `5713fc8`) mostrou que um banco novo não fica pronto só com o `alembic upgrade head` do `deploy/RUNBOOK.md`:

- o schema da fila Procrastinate não é criado por nenhum passo do runbook; sem ele a publicação de uma coleção falha com `type "procrastinate_job_to_defer_v1[]" does not exist` e o worker cai em loop;
- o backend e o worker criam tabelas na subida com `create_all` (`src/app/main.py:113`, `src/app/db.py:41`); em banco vazio os dois disputaram a criação (`UniqueViolation` em `pg_type_typname_nsp_index`) e o banco ficou sem `alembic_version`;
- a rota de publicação grava a coleção e o envio antes de enfileirar (`src/app/routers/envios.py:138-144`); quando o enfileiramento falhou, a coleção ficou gravada sem envio e a nova tentativa respondeu "Já existe uma coleção com esse nome neste Workspace".

A primeira instalação no Supabase novo (T020 da SPEC-0041) reproduziria as três falhas.

#### Resultado desejado

Um banco novo fica pronto com um único `alembic upgrade head`, que também prepara a fila; backend e worker não criam tabelas e avisam com clareza quando o banco não está migrado; e uma publicação que não consegue enfileirar não deixa coleção nem envio gravados, de modo que a pessoa tenta de novo com o mesmo nome.

#### Métricas de sucesso

- Em banco vazio, `alembic upgrade head` cria as tabelas do app, as `procrastinate_*` e deixa `alembic_version` no head, em 1 comando e 0 passos manuais adicionais. **Observação**: teste de migração em banco vazio e repetição no ensaio local.
- 0 ocorrências de `UniqueViolation` na criação de tabelas quando backend e worker sobem juntos. **Observação**: teste de subida simultânea e logs do ensaio local.
- 100% das falhas de enfileiramento deixam 0 coleções novas e 0 envios órfãos gravados. **Observação**: teste que força a falha do enfileiramento e consulta o banco.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: Onde o schema da fila é aplicado hoje? → só pela CLI `python -m procrastinate --app src.app.worker.app schema --apply`, documentada em `docs/application.md` e usada em `tests/conftest.py`; nenhum arquivo de `deploy/` a chama. Impacto: o runbook precisa passar a prepará-lo (FR-001).
- **R-002**: Quem cria tabelas na subida? → `db.create_tables()` em `src/app/main.py:113`, importado também pelo worker (`src/app/worker.py`). Impacto: remover e verificar a versão (FR-002, FR-003).
- **R-003**: O que a rota de publicação grava antes de enfileirar? → coleção e envio, com `session.commit()` em `src/app/routers/envios.py:138`, e só depois `publicacao.agendar_envio`. Impacto: a falha do enfileiramento exige compensação depois do commit (FR-004).

#### Fontes e contexto consultados

- `specs/backlog/0047-aplicar-o-schema-da-fila-no-deploy-e-evitar-corrida-do-create-all.md` e a captura `specs/inbox/2026-10-22-191007-aplicar-o-schema-da-fila-procrastinate-no-deploy-e-evitar-corrida-do-create-all.md`.
- `specs/inbox/2026-10-08-220019-stack-local-divergente-dos-arquivos-de-deploy-e-banco-sem-historico-de-migrations.md` (banco sem histórico de migrations).
- `specs/in-progress/0041-servicos-externos-qdrant-postgres-producao/spec.md`, seção 13 (evidência do ensaio local).
- `deploy/RUNBOOK.md`, `deploy/SECRETS.md`, `alembic/env.py`, `alembic/versions/0040_grupos_e_tabelas.py`, `tests/conftest.py`, `src/app/main.py`, `src/app/db.py`, `src/app/publicacao.py`.
- Ensaio local executado nesta conversa: logs do backend e do worker e consultas ao Postgres do ensaio.

#### Documentação consultada

- `docs/application.md` (entrypoint do worker e `schema --apply`) e `docs/database.md`.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo; as evidências são locais e estão nos arquivos citados.

#### Dúvidas respondidas

- **Q**: onde aplicar o schema da fila? → **A**: numa migration do Alembic que o cria somente se ainda não existir (decisão da pessoa responsável, 2026-10-22, DEC-001).
- **Q**: o que fazer com o `create_all` na subida? → **A**: remover; o Alembic é a única fonte do schema e a subida verifica a versão (DEC-002).
- **Q**: a coleção órfã entra neste item? → **A**: sim; a falha ao enfileirar desfaz a publicação (DEC-003).
- **Q**: e os bancos já criados pelo `create_all`? → **A**: passo único documentado, `alembic stamp head` depois de conferir o schema (DEC-004).

#### Dúvidas abertas

- Nenhuma bloqueante. Detalhes de implementação ficam para o plano técnico: como a migration detecta o schema existente da fila e como a verificação de versão obtém o head do código.

### 3. Escopo e atores

#### Incluído

- Migration do Alembic que cria o schema da fila Procrastinate somente se ausente, de forma idempotente.
- Remoção do `create_all` da subida do backend e do worker, com verificação da versão do banco e parada com mensagem clara.
- Atomicidade da publicação quando o enfileiramento falha: coleção nova, envio e arquivos desfeitos.
- `deploy/RUNBOOK.md` e `deploy/SECRETS.md` atualizados, com o passo único de adoção `alembic stamp head`.
- Ajuste dos testes que dependiam do `create_all` na subida.

#### Fora de escopo

- Limpeza das coleções órfãs já existentes em bancos ou no Qdrant publicado (`beta-teste` e `beta-teste1` do ensaio).
- Executar o deploy real na VPS (T020 da SPEC-0041 e T027 da SPEC-0032).
- Demais divergências do stack local descritas na captura de 2026-10-08 (secrets `_local`, imagens `local`).
- Migrar o worker para outro mecanismo de fila.

#### Atores

- **Operador do deploy**: executa o runbook, o `alembic upgrade head` e, quando for o caso, o passo de adoção.
- **Pessoa que publica**: envia documentos para uma coleção e precisa de um erro claro e de nova tentativa possível.
- **Backend e worker**: verificam a versão do banco na subida e não criam tabelas.

### 4. Princípios e restrições do projeto

- **PR-001**: Nenhum segredo, host, usuário, chave ou domínio real entra no repositório, nos logs nem nas mensagens de erro.
- **PR-002**: Nenhuma etapa executa comando destrutivo de banco ou de coleção, nem testes contra o banco de desenvolvimento; os testes usam o banco de testes isolado por schema.
- **PR-003**: O deploy continua manual e feito somente pela pessoa responsável.
- **PR-004**: O Alembic é a única fonte do schema do banco da aplicação e da fila.

### 5. Histórias de usuário

#### US-001 — Preparar um banco novo com um único comando (P1)

Como operador do deploy, quero que o `alembic upgrade head` deixe pronto também o schema da fila, para instalar o beta num banco novo sem passos manuais não documentados.

**Por que P1**: sem isso a primeira publicação do beta falha; bloqueia a T020 da SPEC-0041.
**Teste independente**: rodar `alembic upgrade head` em banco vazio e conferir tabelas do app, da fila e `alembic_version` no head.
**Requisitos**: FR-001

#### US-002 — Subir os serviços sem criar tabelas e saber quando falta migrar (P1)

Como operador do deploy, quero que backend e worker não criem tabelas e avisem com clareza quando o banco não está migrado, para evitar disputa na criação e bancos sem histórico.

**Por que P1**: a corrida do `create_all` derrubou a primeira tentativa do backend no ensaio.
**Teste independente**: subir backend e worker em banco vazio e em banco migrado e comparar o comportamento.
**Requisitos**: FR-002, FR-003

#### US-003 — Publicar sem deixar coleção órfã quando o envio não entra na fila (P1)

Como pessoa que publica documentos, quero que uma falha ao iniciar o envio não deixe a coleção gravada, para repetir a publicação com o mesmo nome.

**Por que P1**: no ensaio o nome ficou bloqueado por um registro sem envio.
**Teste independente**: forçar a falha do enfileiramento e publicar de novo com o mesmo nome.
**Requisitos**: FR-004

#### US-004 — Adotar bancos já criados pelo create_all e seguir o runbook (P2)

Como operador do deploy, quero um passo único e documentado para bancos criados pelo `create_all`, para adotar o Alembic sem recriar tabelas.

**Por que P2**: o beta é banco novo; bancos antigos, como o de desenvolvimento, são a exceção.
**Teste independente**: aplicar `alembic stamp head` num banco criado pelo `create_all` e rodar `alembic upgrade head` sem erro.
**Requisitos**: FR-005

### 6. Cenários BDD de aceite

#### AC-001 — Banco vazio fica pronto com um único comando

**Cobre**: US-001, FR-001

```gherkin
@US-001 @FR-001 @AC-001
Feature: Preparação do banco pelo Alembic

  Scenario: Banco novo recebe tabelas do app e da fila
    Given um banco Postgres vazio
    When `alembic upgrade head` é executado
    Then as tabelas do app, as tabelas `procrastinate_*` e `alembic_version` existem e a versão está no head
```

#### AC-002 — A migration da fila é idempotente

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-002
Feature: Preparação do banco pelo Alembic

  Scenario: Segunda execução não altera nada
    Given um banco já no head
    When `alembic upgrade head` é executado de novo
    Then termina sem erro e sem alterar o schema
```

#### AC-003 — Fila aplicada à mão não quebra a migration

**Cobre**: US-001, FR-001

```gherkin
@US-001 @FR-001 @AC-003
Feature: Preparação do banco pelo Alembic

  Scenario: Banco com o schema da fila já aplicado fora do Alembic
    Given um banco no qual `procrastinate schema --apply` já foi executado e que ainda não recebeu a migration da fila
    When `alembic upgrade head` é executado
    Then a migration detecta o schema existente, não o recria e o banco termina no head
```

#### AC-004 — Subida em banco migrado não emite DDL

**Cobre**: US-002, FR-002, NFR-003

```gherkin
@US-002 @FR-002 @NFR-003 @AC-004
Feature: Subida dos serviços sem criar tabelas

  Scenario: Backend sobe em banco no head
    Given um banco migrado até o head
    When o backend inicia
    Then ele sobe sem criar nem alterar tabelas
```

#### AC-005 — Banco não migrado para o serviço com mensagem clara

**Cobre**: US-002, FR-003, NFR-001

```gherkin
@US-002 @FR-003 @NFR-001 @AC-005
Feature: Verificação de versão na subida

  Scenario: Banco vazio sem migração
    Given um banco sem `alembic_version`
    When o backend ou o worker inicia
    Then o processo encerra com código diferente de zero e uma mensagem que manda executar `alembic upgrade head`, sem host, usuário nem senha
```

#### AC-006 — Banco em versão antiga também para o serviço

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-006
Feature: Verificação de versão na subida

  Scenario: Banco atrás do head
    Given um banco cuja `alembic_version` está antes do head do código
    When o backend ou o worker inicia
    Then o processo encerra com a mensagem de migração pendente e nenhuma tabela é criada
```

#### AC-007 — A subida não cria tabelas em nenhum caso

**Cobre**: US-002, FR-002

```gherkin
@US-002 @FR-002 @AC-007
Feature: Subida dos serviços sem criar tabelas

  Scenario: Banco incompleto não é completado pelo serviço
    Given um banco com `alembic_version` no head mas sem uma tabela do app
    When o backend inicia
    Then ele não recria a tabela ausente; a falha aparece na consulta que a usa
```

#### AC-008 — Falha ao enfileirar não deixa coleção nova

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-008
Feature: Publicação atômica

  Scenario: Enfileiramento falha na criação de uma coleção
    Given uma pessoa publica documentos em uma coleção nova `X` e a fila recusa o envio
    When a publicação termina
    Then ela vê o erro, nenhuma coleção `X` nem envio ficam gravados, os arquivos enviados são removidos e uma nova tentativa com o nome `X` é aceita
```

#### AC-009 — Falha ao enfileirar em coleção existente remove só o envio

**Cobre**: US-003, FR-004, NFR-001

```gherkin
@US-003 @FR-004 @NFR-001 @AC-009
Feature: Publicação atômica

  Scenario: Enfileiramento falha em uma coleção existente
    Given uma coleção `X` já existe e a fila recusa um novo envio
    When a pessoa publica documentos nela
    Then o envio e os arquivos desse pedido são removidos, a coleção `X` e seus envios anteriores permanecem e o log registra a falha sem segredos
```

#### AC-010 — Enfileiramento que funciona segue o fluxo atual

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-010
Feature: Publicação atômica

  Scenario: Caminho feliz da publicação
    Given a fila está disponível
    When a pessoa publica documentos em uma coleção nova
    Then a coleção e o envio ficam gravados e o envio entra na fila como hoje
```

#### AC-011 — Banco criado pelo create_all é adotado com o stamp

**Cobre**: US-004, FR-005

```gherkin
@US-004 @FR-005 @AC-011
Feature: Adoção de banco existente

  Scenario: Banco com tabelas e sem histórico
    Given um banco criado pelo `create_all`, com tabelas completas e sem `alembic_version`
    When o passo documentado `alembic stamp head` é executado e depois `alembic upgrade head`
    Then o upgrade termina sem tentar recriar tabelas
```

#### AC-012 — O runbook descreve o fluxo e a adoção

**Cobre**: US-004, FR-005

```gherkin
@US-004 @FR-005 @AC-012
Feature: Runbook de deploy

  Scenario: Documentação cobre primeira instalação e adoção
    Given o `deploy/RUNBOOK.md` atualizado
    When a pessoa operadora o consulta
    Then ele mostra a primeira instalação com um único `alembic upgrade head` e o passo único de adoção com o `stamp head` e a conferência prévia do schema
```

#### AC-013 — O runbook não pede mais o schema da fila à mão

**Cobre**: US-004, FR-005, NFR-002

```gherkin
@US-004 @FR-005 @NFR-002 @AC-013
Feature: Runbook de deploy

  Scenario: Sem passo manual de schema da fila
    Given o `deploy/RUNBOOK.md` e o `deploy/SECRETS.md` atualizados
    When a pessoa operadora segue a primeira instalação
    Then nenhum passo manda executar `procrastinate schema --apply` e o aviso de banco não migrado remete ao passo de migração
```

#### AC-014 — Os testes existentes seguem verdes

**Cobre**: US-002, FR-002, NFR-002

```gherkin
@US-002 @FR-002 @NFR-002 @AC-014
Feature: Regressão

  Scenario: Suítes existentes continuam válidas
    Given a regressão completa com Pytest e Ruff
    When ela é executada depois da mudança
    Then nenhum teste preexistente falha, exceto os que afirmavam o `create_all` na subida, que passam a afirmar o novo contrato
```

#### AC-015 — Backend e worker sobem juntos sem disputa

**Cobre**: US-002, NFR-003

```gherkin
@US-002 @NFR-003 @AC-015
Feature: Concorrência na subida

  Scenario: Subida simultânea em banco migrado
    Given um banco migrado até o head
    When backend e worker iniciam ao mesmo tempo
    Then ambos ficam saudáveis e nenhum registra `UniqueViolation`
```

#### AC-016 — Subida simultânea em banco não migrado para os dois

**Cobre**: US-002, FR-003, NFR-003

```gherkin
@US-002 @FR-003 @NFR-003 @AC-016
Feature: Concorrência na subida

  Scenario: Banco não migrado com dois serviços
    Given um banco sem migração
    When backend e worker iniciam ao mesmo tempo
    Then ambos encerram com a mensagem de migração pendente e nenhum cria tabela
```

#### AC-017 — O erro mostrado à pessoa não vaza detalhes internos

**Cobre**: US-003, FR-004, NFR-001

```gherkin
@US-003 @FR-004 @NFR-001 @AC-017
Feature: Publicação atômica

  Scenario: Mensagem de falha ao enfileirar
    Given o enfileiramento falha por erro de banco
    When a pessoa recebe a resposta da publicação
    Then a mensagem diz que não foi possível iniciar o envio e pede nova tentativa, sem DSN, host, usuário, senha nem rastreio interno
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve fornecer uma migration do Alembic que cria o schema da fila Procrastinate somente quando ele ainda não existir, de forma idempotente, de modo que `alembic upgrade head` em banco vazio deixe tabelas do app, da fila e `alembic_version` no head.
- **FR-002**: Backend e worker não devem criar nem alterar tabelas na subida.
- **FR-003**: Backend e worker devem, na subida, comparar a versão do banco com o head do Alembic e encerrar com código diferente de zero e uma mensagem que remete a `alembic upgrade head` quando o banco não estiver migrado ou estiver atrás do head.
- **FR-004**: Quando o enfileiramento do envio falhar na publicação, o sistema deve desfazer o que o pedido gravou (coleção nova, envio e arquivos enviados), preservar uma coleção que já existia com seus envios anteriores, informar o erro à pessoa e permitir nova tentativa com o mesmo nome.
- **FR-005**: O `deploy/RUNBOOK.md` e o `deploy/SECRETS.md` devem descrever a primeira instalação com um único `alembic upgrade head` e o passo único de adoção de bancos criados pelo `create_all` (`alembic stamp head` depois de conferir que o schema está completo).

#### Não funcionais

- **NFR-001**: Segurança e privacidade: mensagens de banco não migrado, erros devolvidos à pessoa e logs de falha de enfileiramento não contêm host, usuário, senha nem DSN. **Verificação**: testes que inspecionam a mensagem, a resposta e o log.
- **NFR-002**: Compatibilidade: os testes existentes continuam passando, exceto os que afirmavam o `create_all` na subida, e a migration é reaplicável sem efeito. **Verificação**: regressão completa com Pytest e Ruff e teste de dupla execução do `alembic upgrade head`.
- **NFR-003**: Concorrência: backend e worker iniciados ao mesmo tempo não produzem `UniqueViolation` na criação de tabelas. **Verificação**: teste de subida simultânea em banco migrado e não migrado e repetição do ensaio local.

#### Erros e casos-limite

- Banco sem `alembic_version` na subida → o serviço encerra com a mensagem de migração pendente.
- Banco atrás do head → o serviço encerra com a mensagem de migração pendente.
- Falha ao enfileirar com coleção nova → publicação desfeita por inteiro.
- Falha ao enfileirar com coleção existente → só o envio e os arquivos do pedido são desfeitos.
- Banco com o schema da fila aplicado à mão → a migration não recria nem falha.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Python 3.12 com FastAPI, SQLAlchemy 2, Alembic (`alembic/env.py` lê `APP_DATABASE_URL`) e Procrastinate com `PsycopgConnector` (`src/app/tasks.py`, `src/app/worker.py`).
- `src/app/main.py` executa `db.configure`, `db.create_tables()` e `tasks.configure_connector(...)` na importação; o worker importa `src.app.main` e herda tudo isso.
- A migration mais recente é `0040_grupos_e_tabelas`; as tabelas do app já são criadas pelas migrations, e o `create_all` é redundante.
- A rota `POST /api/v1/envios` grava coleção e envio com `session.commit()` e depois chama `publicacao.agendar_envio` (`src/app/routers/envios.py:138-144`, `src/app/publicacao.py:84`).
- `tests/conftest.py` isola cada teste em um schema próprio, aplica `ORMBase.metadata.create_all` e `SchemaManager(connector).apply_schema()` sem passar por `db.create_tables()`.

#### Arquitetura e módulos

- Nova migration em `alembic/versions/` que aplica o schema da fila condicionalmente, por exemplo consultando `to_regclass('procrastinate_jobs')` e usando o SQL do `SchemaManager` do Procrastinate (a escolha entre SQL embutido e chamada ao `SchemaManager` e o rollback ficam para as tarefas).
- `src/app/db.py` ganha uma verificação de versão (`verificar_banco_migrado`) que compara `alembic_version` com o head dos scripts em `alembic/versions/`; `create_tables()` deixa de ser chamado na subida.
- A verificação roda na **inicialização real** do serviço, e não na importação de `src/app/main.py`: no backend, no evento de startup do FastAPI; no worker, no `main()` de `src/app/worker.py`. A importação de `src.app.main` deixa de chamar `db.create_tables()` e não consulta o banco, porque `tests/conftest.py` e muitas suítes importam esse módulo contra um banco isolado por schema que não recebe o Alembic.
- `src/app/publicacao.py` e `src/app/routers/envios.py` passam a compensar a falha do enfileiramento: remover o envio, a coleção criada no pedido e os arquivos salvos, e propagar um erro de publicação sem detalhes internos.

#### Migrations

- Uma migration nova, filha de `0040_grupos_e_tabelas`, idempotente; o `downgrade` não remove o schema da fila para não apagar tarefas pendentes (a decisão final fica nas tarefas e no `DEC` correspondente).
- Ordem no deploy: `alembic upgrade head` antes de subir backend e worker, como já descreve o runbook.

#### Models

- Nenhum model novo. A tabela `alembic_version` é do Alembic e não entra em `src/app/models.py`.

#### Controllers e casos de uso

- `POST /api/v1/envios`: depois do commit, se `agendar_envio` falhar, executa a compensação e devolve erro de serviço indisponível com mensagem genérica; mantém o fluxo atual quando o enfileiramento funciona.

#### Views e experiência

- Não aplicável: sem mudança de tela. A mensagem de erro já é exibida pelo frontend atual no formulário de publicação.

#### Queries e repositórios

- Consulta de leitura a `alembic_version` na subida; remoção de `Envio` e, quando a coleção foi criada no pedido, de `Colecao`, em uma transação própria da compensação.

#### Jobs e processamento assíncrono

- O worker não muda de comportamento além de verificar a versão do banco na subida; a fila só funciona depois da migration.

#### Estrutura de arquivos

```text
specs/draft/0042-aplicar-o-schema-da-fila-no-deploy-e-evitar-corrida-do-create-all/
  spec.md
  research/
alembic/versions/
  <nova migration da fila>
src/app/
  db.py
  main.py
  publicacao.py
  routers/envios.py
deploy/
  RUNBOOK.md
  SECRETS.md
tests/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Schema da fila (`procrastinate_*`) | nomes das tabelas e tipos do Procrastinate | criado pela migration somente se ausente | usado por `Envio` via `process_envio_task` |
| `alembic_version` | `version_num` | head do código = versão esperada pela subida | consultada por backend e worker |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Envio | gravado (`queued`) | enfileiramento falha | removido | nenhuma coleção nova nem envio órfão permanecem |
| Envio | gravado (`queued`) | enfileiramento funciona | `queued` na fila | fluxo atual preservado |

#### Migração e retenção

- Banco novo: `alembic upgrade head`. Banco criado pelo `create_all`: `alembic stamp head` depois de conferir o schema, e então `alembic upgrade head` nas versões seguintes. Sem mudança de retenção.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega muda deploy, subida dos serviços e a regra de gravação da publicação; a tela de publicação existente apenas exibe o erro já tratado, sem alteração de composição.

#### Stack e convenções de interface

- Não aplicável.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável.

#### Menus e navegação principal

- Não aplicável.

#### Formulários e ações

- Não aplicável.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável.

#### Estados e acessibilidade

- Não aplicável.

#### Contrato CRUD

- Não aplicável.

#### Revisão visual durante o desenvolvimento

- Não aplicável: nenhuma tarefa toca interface para pessoas.

#### APIs expostas

- `POST /api/v1/envios`: contrato inalterado no sucesso; na falha de enfileiramento responde erro de serviço indisponível com mensagem genérica e sem alterar o formato dos demais erros. Autenticação e permissões inalteradas.

#### APIs externas utilizadas

- Nenhuma.

#### Documentação das APIs consultadas

- Procrastinate (CLI `schema --apply` e `SchemaManager`), conforme `docs/application.md` e o uso em `tests/conftest.py`.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: a verificação de versão (`db.verificar_banco_migrado`) e a compensação da publicação, no menor nível que prova cada regra.
- **Integração/contrato**: Alembic real em schemas de scratch do banco de testes (`tests/_banco_scratch.py`), a rota `POST /api/v1/envios` com o `TestClient` e a fila simulada, e o contrato de texto do runbook.
- **BDD/aceite**: o Gherkin da seção 6 orienta o desenho dos casos; nenhum `.feature` é criado ou executado.
- **Runner TDD**: Pytest (projeto Python); todos os casos usam o banco de testes isolado por schema e nunca o banco de desenvolvimento.
- **E2E**: a repetição do ensaio local em Docker (subir, migrar, publicar uma coleção) antes de o deploy da T020, feita pela pessoa responsável.
- **Verificação manual**: somente o ensaio local acima, porque envolve Docker Swarm e o Qdrant publicado.
- **Interface fixada pelos testes**: `src.app.db.verificar_banco_migrado(engine=None) -> None` e `src.app.db.BancoNaoMigrado(RuntimeError)`; `src.app.worker.main()`; resposta `503` com a mensagem "Não foi possível iniciar o envio" na falha de enfileiramento.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, AC-001 | AC-001 na seção 6 | `test_banco_vazio_recebe_app_fila_e_versao_no_head` em `tests/test_migracao_fila.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): `procrastinate_jobs` ausente depois de `alembic upgrade head`: a fila não é criada pelo Alembic | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py`: 10 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-001, FR-001, NFR-002, AC-002 | AC-002 na seção 6 | `test_segundo_upgrade_nao_altera_o_schema_da_fila` em `tests/test_migracao_fila.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): `procrastinate_jobs` ausente depois do primeiro upgrade: sem a migration da fila não há o que repetir | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py`: 10 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-001, FR-001, AC-003 | AC-003 na seção 6 | `test_fila_aplicada_a_mao_nao_quebra_a_migration` em `tests/test_migracao_fila.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): o head ainda é `0040_grupos_e_tabelas`: a cadeia não tem a migration da fila | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py`: 10 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-002, FR-002, NFR-003, AC-004 | AC-004 na seção 6 | `test_subida_em_banco_migrado_nao_emite_ddl` em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): `src.app.db.verificar_banco_migrado` ainda não existe | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-002, FR-003, NFR-001, AC-005 | AC-005 na seção 6 | `test_banco_sem_alembic_version_para_com_mensagem_sem_credenciais` em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): `src.app.db.verificar_banco_migrado` ainda não existe; o caso `test_backend_verifica_a_versao_do_banco_na_inicializacao` também falha com `DID NOT RAISE` | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-002, FR-003, AC-006 | AC-006 na seção 6 | `test_banco_atras_do_head_para_com_a_mensagem_de_migracao_pendente` em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): `src.app.db.verificar_banco_migrado` ainda não existe | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-002, FR-002, AC-007 | AC-007 na seção 6 | `test_tabela_ausente_com_versao_no_head_nao_e_recriada` em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): `src.app.db.verificar_banco_migrado` ainda não existe | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-003, FR-004, AC-008 | AC-008 na seção 6 | `test_falha_na_fila_com_colecao_nova_nao_deixa_registro_e_permite_repetir` em `tests/test_app_publicacao_atomica.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): a resposta é 500 em vez de 503 e a coleção fica gravada | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-003, FR-004, NFR-001, AC-009 | AC-009 na seção 6 | `test_falha_na_fila_em_colecao_existente_remove_so_o_envio_do_pedido` em `tests/test_app_publicacao_atomica.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): a resposta é 500 em vez de 503 e o envio do pedido fica gravado | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-003, FR-004, AC-010 | AC-010 na seção 6 | `test_nova_tentativa_depois_da_falha_grava_uma_vez_e_enfileira` em `tests/test_app_publicacao_atomica.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): a primeira tentativa responde 500 em vez de 503 e deixa a coleção que bloqueia o nome | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-004, FR-005, AC-011 | AC-011 na seção 6 | `test_banco_do_create_all_e_adotado_com_stamp_head` em `tests/test_migracao_fila.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): o head ainda é `0040_grupos_e_tabelas`: a cadeia não tem a migration da fila | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py`: 10 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-004, FR-005, AC-012 | AC-012 na seção 6 | `test_runbook_mostra_a_primeira_instalacao_e_o_passo_de_adocao_do_create_all` em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): o runbook não tem o passo de adoção `alembic stamp head` | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py`: 16 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-004, FR-005, NFR-002, AC-013 | AC-013 na seção 6 | `test_runbook_e_secrets_nao_mandam_aplicar_o_schema_da_fila_a_mao` em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): o runbook não explica o aviso de banco não migrado nem remete ao passo de migração | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py`: 16 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-002, FR-002, NFR-002, AC-014 | AC-014 na seção 6 | `test_importar_o_main_nao_cria_tabelas_nem_exige_banco_migrado` em `tests/test_app_inicializacao.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): importar `src.app.main` cria 31 tabelas no banco vazio (`create_all` na importação) | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-002, NFR-003, AC-015 | AC-015 na seção 6 | `test_dois_servicos_em_banco_migrado_sobem_sem_disputa` em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): `src.app.db.verificar_banco_migrado` ainda não existe | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-002, FR-003, NFR-003, AC-016 | AC-016 na seção 6 | `test_dois_servicos_em_banco_nao_migrado_encerram_sem_criar_tabela` em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): `src.app.db.verificar_banco_migrado` ainda não existe; `test_worker_verifica_a_versao_do_banco_antes_de_rodar` falha porque `src.app.worker.main` não existe | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |
| US-003, FR-004, NFR-001, AC-017 | AC-017 na seção 6 | `test_resposta_da_falha_nao_traz_detalhes_internos` em `tests/test_app_publicacao_atomica.py` com marcador próprio `SPECSFY:` | RED (2026-10-22): a resposta é 500 em vez de 503, sem a mensagem tratada de falha ao iniciar o envio | GREEN (2026-10-22): `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed | regressão completa `.venv/bin/python -m pytest -q`: 834 passed, 1 skipped; a única falha (`tests/test_spec_markers.py`, palavra na própria spec) foi corrigida e reexecutada: 1 passed. Ruff limpo; rastreabilidade 29/29 |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | `tests/test_migracao_fila.py::test_banco_vazio_recebe_app_fila_e_versao_no_head` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py`: 10 passed |
| FR-001 | AC-002 | Integração | `tests/test_migracao_fila.py::test_segundo_upgrade_nao_altera_o_schema_da_fila` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py`: 10 passed |
| NFR-002 | AC-002 | Integração | `tests/test_migracao_fila.py::test_segundo_upgrade_nao_altera_o_schema_da_fila` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py`: 10 passed |
| FR-001 | AC-003 | Integração | `tests/test_migracao_fila.py::test_fila_aplicada_a_mao_nao_quebra_a_migration` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py`: 10 passed |
| FR-002 | AC-004 | Integração | `tests/test_verificacao_versao_banco.py::test_subida_em_banco_migrado_nao_emite_ddl` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| NFR-003 | AC-004 | Integração | `tests/test_verificacao_versao_banco.py::test_subida_em_banco_migrado_nao_emite_ddl` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| FR-003 | AC-005 | Integração | `tests/test_verificacao_versao_banco.py::test_banco_sem_alembic_version_para_com_mensagem_sem_credenciais` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| NFR-001 | AC-005 | Integração | `tests/test_verificacao_versao_banco.py::test_banco_sem_alembic_version_para_com_mensagem_sem_credenciais` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| FR-003 | AC-006 | Integração | `tests/test_verificacao_versao_banco.py::test_banco_atras_do_head_para_com_a_mensagem_de_migracao_pendente` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| FR-002 | AC-007 | Integração | `tests/test_verificacao_versao_banco.py::test_tabela_ausente_com_versao_no_head_nao_e_recriada` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| FR-004 | AC-008 | Integração | `tests/test_app_publicacao_atomica.py::test_falha_na_fila_com_colecao_nova_nao_deixa_registro_e_permite_repetir` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed |
| FR-004 | AC-009 | Integração | `tests/test_app_publicacao_atomica.py::test_falha_na_fila_em_colecao_existente_remove_so_o_envio_do_pedido` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed |
| NFR-001 | AC-009 | Integração | `tests/test_app_publicacao_atomica.py::test_falha_na_fila_em_colecao_existente_remove_so_o_envio_do_pedido` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed |
| FR-004 | AC-010 | Integração | `tests/test_app_publicacao_atomica.py::test_nova_tentativa_depois_da_falha_grava_uma_vez_e_enfileira` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed |
| FR-005 | AC-011 | Integração | `tests/test_migracao_fila.py::test_banco_do_create_all_e_adotado_com_stamp_head` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py`: 10 passed |
| FR-005 | AC-012 | Contrato de documentação | `tests/test_deploy_runbook_docs.py::test_runbook_mostra_a_primeira_instalacao_e_o_passo_de_adocao_do_create_all` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py`: 16 passed |
| FR-005 | AC-013 | Contrato de documentação | `tests/test_deploy_runbook_docs.py::test_runbook_e_secrets_nao_mandam_aplicar_o_schema_da_fila_a_mao` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py`: 16 passed |
| NFR-002 | AC-013 | Contrato de documentação | `tests/test_deploy_runbook_docs.py::test_runbook_e_secrets_nao_mandam_aplicar_o_schema_da_fila_a_mao` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py`: 16 passed |
| FR-002 | AC-014 | Integração | `tests/test_app_inicializacao.py::test_importar_o_main_nao_cria_tabelas_nem_exige_banco_migrado` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| NFR-002 | AC-014 | Integração | `tests/test_app_inicializacao.py::test_importar_o_main_nao_cria_tabelas_nem_exige_banco_migrado` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| NFR-003 | AC-015 | Integração | `tests/test_verificacao_versao_banco.py::test_dois_servicos_em_banco_migrado_sobem_sem_disputa` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| FR-003 | AC-016 | Integração | `tests/test_verificacao_versao_banco.py::test_dois_servicos_em_banco_nao_migrado_encerram_sem_criar_tabela` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| NFR-003 | AC-016 | Integração | `tests/test_verificacao_versao_banco.py::test_dois_servicos_em_banco_nao_migrado_encerram_sem_criar_tabela` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed |
| FR-004 | AC-017 | Integração | `tests/test_app_publicacao_atomica.py::test_resposta_da_falha_nao_traz_detalhes_internos` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed |
| NFR-001 | AC-017 | Integração | `tests/test_app_publicacao_atomica.py::test_resposta_da_falha_nao_traz_detalhes_internos` | Passed — `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed (2026-10-22)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0042-aplicar-o-schema-da-fila-no-deploy-e-evitar-corrida-do-create-all/spec.md`
- **Achados**: 4 US, 5 FR, 3 NFR e 17 AC; a feature e cada US, FR e NFR têm ao menos três AC em `**Cobre**`. Sem BLOCKER. WARNING resolvido: a Definition of Done passou a citar `.specsfy/DATABASE.md`, `.specsfy/RULES.md` e `PROJECT.md`, porque a entrega altera persistência e cria uma regra nova (Alembic como única fonte do schema). NOTE resolvido: as métricas de sucesso ganharam a forma de observação.
- **FIND-ARCH-001** [P2] [Resolved] A verificação de versão na importação de `src/app/main.py` derrubaria as suítes que importam o módulo contra um banco isolado por schema sem Alembic — Refs: FR-003, NFR-002 — Evidence: tests/conftest.py:158 — Effect: regressão completa falharia antes de qualquer teste — Suggestion: executar a verificação no startup do backend e no `main()` do worker. Resolvido na seção 8.
- Inferência registrada para confirmação: em coleção que já existia, a compensação remove só o envio e os arquivos do pedido (seção 16, Suposições).

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-22)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/planned/0042-aplicar-o-schema-da-fila-no-deploy-e-evitar-corrida-do-create-all/spec.md`
- **Achados**: 24 tarefas (17 `[TEST] [TDD]`, 3 `[CODE]`, 2 `[DOC]` e 1 `[TEST]` de regressão); 29 de 29 IDs cobertos. RED válido observado nos 17 casos, cada um por comportamento ausente (fila não criada pelo Alembic, `verificar_banco_migrado` e `worker.main` inexistentes, `create_all` na importação, resposta 500 em vez de 503, runbook sem adoção): 19 falhas na execução focal (17 AC mais 2 casos de ligação do backend e do worker) e 14 testes preexistentes do runbook verdes. Ruff limpo e rastreabilidade 29/29. O banco de testes foi confirmado como separado por `check_database_safety.mjs` (SAFE) e os casos usam schemas de scratch, sem remoção.
- Inferência registrada: a adoção de um banco criado pelo `create_all` por `alembic stamp head` pressupõe que o schema da fila já esteja aplicado nesse banco; a conferência prévia do runbook precisa cobrir isso (T021).

#### Gate do Ato III — Entrega

- **Resultado**: Passed (2026-10-22)
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/completed/0042-aplicar-o-schema-da-fila-no-deploy-e-evitar-corrida-do-create-all/spec.md . --full-chain`
- **Achados**: rastreabilidade 29 de 29 IDs; 24 de 24 tarefas concluídas; `verify_acceptance.mjs` com 17 de 17 AC aprovados. Regressão completa com 834 passed, 1 skipped e 1 falha de texto da própria spec, corrigida e reexecutada (1 passed). Ruff limpo, documentação atual (`build_documentation.mjs --check` exit 0) e monitor CURRENT. `.specsfy/DATABASE.md` e `.specsfy/RULES.md` revisados; `PROJECT.md` revisado sem impacto material.
- **Limite do aceite**: a prova de ponta a ponta com Docker e o Qdrant/Postgres publicados continua sendo a repetição do ensaio local e a T020 da SPEC-0041, feita pela pessoa responsável; este gate não a substitui.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pytest falhando em tests/test_migracao_fila.py: banco vazio recebe tabelas do app, da fila e `alembic_version` no head — Refs: US-001, FR-001, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_migracao_fila.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_banco_vazio_recebe_app_fila_e_versao_no_head` criado em `tests/test_migracao_fila.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: `procrastinate_jobs` ausente depois de `alembic upgrade head`: a fila não é criada pelo Alembic.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_migracao_fila.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pytest falhando em tests/test_migracao_fila.py: segundo `alembic upgrade head` termina sem erro e sem alterar o schema — Refs: US-001, FR-001, NFR-002, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_migracao_fila.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_segundo_upgrade_nao_altera_o_schema_da_fila` criado em `tests/test_migracao_fila.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: `procrastinate_jobs` ausente depois do primeiro upgrade: sem a migration da fila não há o que repetir.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_migracao_fila.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pytest falhando em tests/test_migracao_fila.py: fila já aplicada por `procrastinate schema --apply` não quebra a migration — Refs: US-001, FR-001, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_migracao_fila.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_fila_aplicada_a_mao_nao_quebra_a_migration` criado em `tests/test_migracao_fila.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: o head ainda é `0040_grupos_e_tabelas`: a cadeia não tem a migration da fila.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_migracao_fila.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T004 [TEST] [TDD] [US-002] Derivar do AC-004 um caso Pytest falhando em tests/test_verificacao_versao_banco.py: subida em banco migrado não cria nem altera tabelas — Refs: US-002, FR-002, NFR-003, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_subida_em_banco_migrado_nao_emite_ddl` criado em `tests/test_verificacao_versao_banco.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: `src.app.db.verificar_banco_migrado` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-005 um caso Pytest falhando em tests/test_verificacao_versao_banco.py: banco sem `alembic_version` encerra com a mensagem de migração, sem host, usuário nem senha — Refs: US-002, FR-003, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_banco_sem_alembic_version_para_com_mensagem_sem_credenciais` criado em `tests/test_verificacao_versao_banco.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: `src.app.db.verificar_banco_migrado` ainda não existe; o caso `test_backend_verifica_a_versao_do_banco_na_inicializacao` também falha com `DID NOT RAISE`.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 um caso Pytest falhando em tests/test_verificacao_versao_banco.py: banco atrás do head encerra com a mensagem de migração pendente — Refs: US-002, FR-003, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_banco_atras_do_head_para_com_a_mensagem_de_migracao_pendente` criado em `tests/test_verificacao_versao_banco.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: `src.app.db.verificar_banco_migrado` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso Pytest falhando em tests/test_verificacao_versao_banco.py: tabela ausente com `alembic_version` no head não é recriada na subida — Refs: US-002, FR-002, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_tabela_ausente_com_versao_no_head_nao_e_recriada` criado em `tests/test_verificacao_versao_banco.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: `src.app.db.verificar_banco_migrado` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T008 [TEST] [TDD] [US-003] Derivar do AC-008 um caso Pytest falhando em tests/test_app_publicacao_atomica.py: falha ao enfileirar em coleção nova não deixa coleção, envio nem arquivos — Refs: US-003, FR-004, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_app_publicacao_atomica.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_falha_na_fila_com_colecao_nova_nao_deixa_registro_e_permite_repetir` criado em `tests/test_app_publicacao_atomica.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: a resposta é 500 em vez de 503 e a coleção fica gravada.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-009 um caso Pytest falhando em tests/test_app_publicacao_atomica.py: falha ao enfileirar em coleção existente remove só o envio e os arquivos do pedido — Refs: US-003, FR-004, NFR-001, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_app_publicacao_atomica.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_falha_na_fila_em_colecao_existente_remove_so_o_envio_do_pedido` criado em `tests/test_app_publicacao_atomica.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: a resposta é 500 em vez de 503 e o envio do pedido fica gravado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-010 um caso Pytest falhando em tests/test_app_publicacao_atomica.py: enfileiramento que funciona grava coleção e envio e enfileira como hoje — Refs: US-003, FR-004, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_app_publicacao_atomica.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_nova_tentativa_depois_da_falha_grava_uma_vez_e_enfileira` criado em `tests/test_app_publicacao_atomica.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: a primeira tentativa responde 500 em vez de 503 e deixa a coleção que bloqueia o nome.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T011 [TEST] [TDD] [US-004] Derivar do AC-011 um caso Pytest falhando em tests/test_migracao_fila.py: banco do `create_all` com `alembic stamp head` aceita o `upgrade head` sem recriar tabelas — Refs: US-004, FR-005, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_migracao_fila.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_banco_do_create_all_e_adotado_com_stamp_head` criado em `tests/test_migracao_fila.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: o head ainda é `0040_grupos_e_tabelas`: a cadeia não tem a migration da fila.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_migracao_fila.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T012 [TEST] [TDD] [US-004] Derivar do AC-012 um caso Pytest falhando em tests/test_deploy_runbook_docs.py: o runbook mostra a primeira instalação com um único `alembic upgrade head` e o passo de adoção com `stamp head` — Refs: US-004, FR-005, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_runbook_mostra_a_primeira_instalacao_e_o_passo_de_adocao_do_create_all` criado em `tests/test_deploy_runbook_docs.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: o runbook não tem o passo de adoção `alembic stamp head`.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T013 [TEST] [TDD] [US-004] Derivar do AC-013 um caso Pytest falhando em tests/test_deploy_runbook_docs.py: runbook e SECRETS não mandam rodar `procrastinate schema --apply` à mão — Refs: US-004, FR-005, NFR-002, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-013 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_runbook_e_secrets_nao_mandam_aplicar_o_schema_da_fila_a_mao` criado em `tests/test_deploy_runbook_docs.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: o runbook não explica o aviso de banco não migrado nem remete ao passo de migração.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T014 [TEST] [TDD] [US-002] Derivar do AC-014 um caso Pytest falhando em tests/test_app_inicializacao.py: importar `src.app.main` não cria tabelas nem exige banco migrado — Refs: US-002, FR-002, NFR-002, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-014 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_app_inicializacao.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_importar_o_main_nao_cria_tabelas_nem_exige_banco_migrado` criado em `tests/test_app_inicializacao.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: importar `src.app.main` cria 31 tabelas no banco vazio (`create_all` na importação).
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_app_inicializacao.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T015 [TEST] [TDD] [US-002] Derivar do AC-015 um caso Pytest falhando em tests/test_verificacao_versao_banco.py: backend e worker iniciados juntos em banco migrado não registram `UniqueViolation` — Refs: US-002, NFR-003, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-015 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_dois_servicos_em_banco_migrado_sobem_sem_disputa` criado em `tests/test_verificacao_versao_banco.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: `src.app.db.verificar_banco_migrado` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T016 [TEST] [TDD] [US-002] Derivar do AC-016 um caso Pytest falhando em tests/test_verificacao_versao_banco.py: backend e worker iniciados juntos em banco não migrado encerram sem criar tabela — Refs: US-002, FR-003, NFR-003, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-016 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_verificacao_versao_banco.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_dois_servicos_em_banco_nao_migrado_encerram_sem_criar_tabela` criado em `tests/test_verificacao_versao_banco.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: `src.app.db.verificar_banco_migrado` ainda não existe; `test_worker_verifica_a_versao_do_banco_antes_de_rodar` falha porque `src.app.worker.main` não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T017 [TEST] [TDD] [US-003] Derivar do AC-017 um caso Pytest falhando em tests/test_app_publicacao_atomica.py: a resposta de falha ao enfileirar não traz DSN, host, usuário, senha nem rastreio — Refs: US-003, FR-004, NFR-001, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-017 na spec e confirmar regra, IDs e nível de teste; confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento antes de rodar. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso TDD em `tests/test_app_publicacao_atomica.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso `test_resposta_da_falha_nao_traz_detalhes_internos` criado em `tests/test_app_publicacao_atomica.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-22: a resposta é 500 em vez de 503, sem a mensagem tratada de falha ao iniciar o envio.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando `.venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py` e a causa do RED. Executado com `TESTING_ENV_FILE=.env.testing.example`; a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

#### Fase 2 — US-001 Preparar um banco novo com um único comando (P1)

**Objetivo**: `alembic upgrade head` deixa tabelas do app, da fila e `alembic_version` prontas, de forma idempotente.
**Teste independente**: `.venv/bin/python -m pytest -q tests/test_migracao_fila.py`.

- [x] T018 [CODE] [US-001] Criar a migration idempotente do schema da fila em alembic/versions/0042_schema_da_fila.py, filha de `0040_grupos_e_tabelas` — Refs: US-001, FR-001, NFR-002, AC-001, AC-002, AC-003 — Depends: T001, T002, T003
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências; rodar `check_database_safety.mjs` antes de qualquer teste. RED dos predecessores T001, T002 e T003 confirmado na seção 11; banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar arquivos; depois implementar a menor mudança. A migration aplica o schema do Procrastinate somente quando `procrastinate_jobs` ainda não existe; o `downgrade` não remove o schema da fila. `docs/` reconstruído com `$specsfy-documentator` antes e depois (`--check` exit 0); criada `alembic/versions/0042_schema_da_fila.py` (revisão `0042_schema_da_fila`, filha de `0040_grupos_e_tabelas`), que aplica o schema do `SchemaManager` só quando `to_regclass('procrastinate_jobs')` é nulo; o `downgrade` não remove nada.
  - [x] **VERIFY**: Executar `tests/test_migracao_fila.py` (AC-001, AC-002, AC-003) e `tests/test_app_migrations.py`; todos GREEN. `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py`: 10 passed, GREEN em AC-001, AC-002, AC-003 e AC-011; `.venv/bin/ruff check .` limpo.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN, comando, contagens e arquivos alterados. GREEN registrado; arquivo alterado: `alembic/versions/0042_schema_da_fila.py`. Implementado pelo Codex a pedido da pessoa responsável; diff revisado e testes reexecutados pelo Claude.
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. Nenhuma melhoria adicional: a migration é a menor que torna os casos verdes e não introduz dependência nova.
  <!-- specsfy:evidence {"task": "T018", "refs": ["US-001", "FR-001", "NFR-002", "AC-001", "AC-002", "AC-003"], "files": ["alembic/versions/0042_schema_da_fila.py"], "commands": [{"run": ".venv/bin/python -m pytest -q tests/test_migracao_fila.py tests/test_app_migrations.py", "exit": 0}]} -->

**Checkpoint**: um banco vazio chega ao head com um único comando e o segundo `upgrade head` não muda nada.

#### Fase 3 — US-002 Subir os serviços sem criar tabelas e saber quando falta migrar (P1)

**Objetivo**: backend e worker verificam a versão do banco na inicialização, não criam tabelas e não disputam a criação.
**Teste independente**: `.venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py`.

- [x] T019 [CODE] [US-002] Trocar `db.create_tables()` por uma verificação de versão (`verificar_banco_migrado`) em src/app/db.py, chamada no startup do backend em src/app/main.py e no `main()` do worker em src/app/worker.py — Refs: US-002, FR-002, FR-003, NFR-003, NFR-001, NFR-002, AC-004, AC-005, AC-006, AC-007, AC-014, AC-015, AC-016 — Depends: T004, T005, T006, T007, T014, T015, T016, T018
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências; rodar `check_database_safety.mjs` antes de qualquer teste. RED dos predecessores T004–T007 e T014–T016 e a migration da T018 confirmados; banco de testes separado: SAFE.
  - [x] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar arquivos; depois implementar a menor mudança. A importação de `src.app.main` não cria tabelas nem consulta o banco; a verificação compara `alembic_version` com o head dos scripts e encerra com mensagem que remete a `alembic upgrade head`, sem host, usuário nem senha. `docs/` reconstruído antes e depois (`--check` exit 0); `db.create_tables()` removido (função e exportação), criados `BancoNaoMigrado` e `verificar_banco_migrado(engine=None)` em `src/app/db.py`, que compara a revisão do banco com o head dos scripts sem executar DDL; o backend verifica a versão no `lifespan` do FastAPI (`src/app/main.py`) e o worker na nova `main()` de `src/app/worker.py`. A importação de `src.app.main` não cria tabelas nem consulta o banco. A mensagem remete a `alembic upgrade head` sem host, usuário, senha nem URL.
  - [x] **VERIFY**: Executar `tests/test_verificacao_versao_banco.py`, `tests/test_app_inicializacao.py`, `tests/test_app_worker.py` e `tests/test_app_migrations.py`; todos GREEN. `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py`: 16 passed, GREEN em AC-004, AC-005, AC-006, AC-007, AC-014, AC-015 e AC-016.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN, comando, contagens e arquivos alterados. GREEN registrado; arquivos alterados: `src/app/db.py`, `src/app/main.py`, `src/app/worker.py`. Implementado pelo Codex a pedido da pessoa responsável; diff revisado e testes reexecutados pelo Claude.
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. Nenhuma melhoria adicional: a verificação compara conjuntos de revisões e não toca o schema.
  <!-- specsfy:evidence {"task": "T019", "refs": ["US-002", "FR-002", "FR-003", "NFR-003", "NFR-001", "NFR-002", "AC-004", "AC-005", "AC-006", "AC-007", "AC-014", "AC-015", "AC-016"], "files": ["src/app/db.py", "src/app/main.py", "src/app/worker.py"], "commands": [{"run": ".venv/bin/python -m pytest -q tests/test_verificacao_versao_banco.py tests/test_app_inicializacao.py tests/test_app_worker.py", "exit": 0}]} -->

**Checkpoint**: banco vazio faz os dois serviços encerrarem com a mensagem de migração; banco migrado os deixa subir juntos sem `UniqueViolation`.

#### Fase 4 — US-003 Publicar sem deixar coleção órfã quando o envio não entra na fila (P1)

**Objetivo**: falha ao enfileirar desfaz coleção nova, envio e arquivos do pedido e permite nova tentativa com o mesmo nome.
**Teste independente**: `.venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`.

- [x] T020 [CODE] [US-003] Compensar a falha do enfileiramento em src/app/publicacao.py e src/app/routers/envios.py: remover envio, coleção criada no pedido e arquivos, e responder erro genérico — Refs: US-003, FR-004, NFR-001, AC-008, AC-009, AC-010, AC-017 — Depends: T008, T009, T010, T017, T019
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências; rodar `check_database_safety.mjs` antes de qualquer teste. RED dos predecessores T008, T009, T010 e T017 e a verificação da T019 confirmados; banco de testes separado: SAFE.
  - [x] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar arquivos; depois implementar a menor mudança. Depois do `commit`, se `agendar_envio` falhar, a compensação roda em transação própria, preserva coleção e envios anteriores quando a coleção já existia, registra a falha no log sem segredos e devolve erro de serviço indisponível com mensagem genérica. `docs/` reconstruído antes e depois (`--check` exit 0); em `src/app/routers/envios.py`, a falha de `agendar_envio` depois do commit aciona `publicacao.compensar_envio` (`src/app/publicacao.py`), que remove o envio do pedido, a coleção só quando criada no pedido e os arquivos do pedido em transação própria, registra aviso com só o tipo da exceção e responde 503 "Não foi possível iniciar o envio. Tente novamente." sem detalhes internos.
  - [x] **VERIFY**: Executar `tests/test_app_publicacao_atomica.py` e as suítes existentes de envios e publicação; todos GREEN. `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py`: 4 passed, GREEN em AC-008, AC-009, AC-010 e AC-017. O Codex também passou as suítes relacionadas de envios, sync, tasks, bootstrap e falhas de coleção.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN, comando, contagens e arquivos alterados. GREEN registrado; arquivos alterados: `src/app/publicacao.py`, `src/app/routers/envios.py`. Implementado pelo Codex a pedido da pessoa responsável; diff revisado e testes reexecutados pelo Claude.
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. Nenhuma melhoria adicional: a compensação reaproveita `storage.delete_base` e a sessão existentes.
  <!-- specsfy:evidence {"task": "T020", "refs": ["US-003", "FR-004", "NFR-001", "AC-008", "AC-009", "AC-010", "AC-017"], "files": ["src/app/publicacao.py", "src/app/routers/envios.py"], "commands": [{"run": ".venv/bin/python -m pytest -q tests/test_app_publicacao_atomica.py", "exit": 0}]} -->

**Checkpoint**: com a fila indisponível, publicar `X` falha e publicar `X` de novo é aceito.

#### Fase 5 — US-004 Adotar bancos criados pelo create_all e seguir o runbook (P2)

**Objetivo**: runbook com a primeira instalação em um único `alembic upgrade head` e o passo único de adoção.
**Teste independente**: `.venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py`.

- [x] T021 [DOC] [US-004] Atualizar deploy/RUNBOOK.md e deploy/SECRETS.md: primeira instalação com um único `alembic upgrade head`, passo de adoção com `alembic stamp head` e aviso de banco não migrado — Refs: US-004, FR-005, NFR-002, AC-011, AC-012, AC-013 — Depends: T011, T012, T013, T018, T019
  - [x] **PREP**: Ler as seções de migração e de primeira instalação do runbook e confirmar que nenhum passo manda aplicar o schema da fila à mão. RED dos predecessores T011, T012 e T013 e as tarefas T018 e T019 confirmados.
  - [x] **EXECUTE**: Reescrever os passos de migração e instalação, acrescentar a adoção de bancos do `create_all` com a conferência prévia do schema, sem host, domínio ou segredo reais. `deploy/RUNBOOK.md` e `deploy/SECRETS.md` atualizados: primeira instalação com um único `alembic upgrade head` (já prepara a fila), passo único de adoção de bancos do `create_all` (conferir antes app e fila completos; depois `alembic stamp head`), aviso de banco não migrado remetendo ao `alembic upgrade head`; nenhum passo manda executar `procrastinate schema --apply`.
  - [x] **VERIFY**: Executar `.venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py`; GREEN em AC-012 e AC-013. `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py`: 16 passed, GREEN em AC-012 e AC-013 e nos 14 casos preexistentes.
  - [x] **VISUAL**: Não aplicável: a tarefa só altera documentação e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, o resultado e os arquivos alterados. GREEN registrado; arquivos alterados: `deploy/RUNBOOK.md`, `deploy/SECRETS.md`. Implementado pelo Codex a pedido da pessoa responsável; diff revisado e testes reexecutados pelo Claude.
  - [x] **IMPROVE**: Registrar melhoria aplicada ou ausência justificada. Nenhuma melhoria adicional; o texto avisa que o `stamp` não corrige um schema incompleto, inclusive o da fila.
  <!-- specsfy:evidence {"task": "T021", "refs": ["US-004", "FR-005", "NFR-002", "AC-011", "AC-012", "AC-013"], "files": ["deploy/RUNBOOK.md", "deploy/SECRETS.md"], "commands": [{"run": "TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py", "exit": 0}]} -->

**Checkpoint**: seguir só o runbook leva um banco novo ao head e um banco antigo à adoção.

#### Fase de documentação do projeto

- [x] T022 [DOC] [US-001] Registrar em .specsfy/DATABASE.md o schema da fila (`procrastinate_*`) e `alembic_version` como preparados pelo Alembic — Refs: US-001, FR-001, NFR-002, AC-001, AC-002, AC-003 — Depends: T018
  - [x] **PREP**: Rodar `monitor_context.mjs --check` e ler `.specsfy/DATABASE.md`. `monitor_context.mjs --check` e leitura de `.specsfy/DATABASE.md` feitos.
  - [x] **EXECUTE**: Acrescentar as tabelas da fila e `alembic_version`, a migration `0042_schema_da_fila` e a regra de idempotência, preservando o texto humano existente. `.specsfy/DATABASE.md` ganhou o inventário de `alembic_version` e das tabelas `procrastinate_*`, a migration `0042_schema_da_fila` e a idempotência, sem apagar conteúdo existente.
  - [x] **VERIFY**: Rodar `monitor_context.mjs --check` e obter `CURRENT`. `monitor_context.mjs --project . --check --acknowledge-project-no-change`: CURRENT.
  - [x] **VISUAL**: Não aplicável: a tarefa só altera documentação e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando e o resultado. Arquivo alterado: `.specsfy/DATABASE.md`. Implementado pelo Codex a pedido da pessoa responsável; diff revisado e testes reexecutados pelo Claude.
  - [x] **IMPROVE**: Registrar melhoria aplicada ou ausência justificada. Nenhuma melhoria adicional.

- [x] T023 [DOC] [US-002] Registrar em .specsfy/RULES.md que o Alembic é a única fonte do schema e que o app não cria tabelas na subida — Refs: US-002, FR-002, FR-003, NFR-003, NFR-001, AC-004, AC-005, AC-006 — Depends: T019
  - [x] **PREP**: Rodar `monitor_context.mjs --check` e ler `.specsfy/RULES.md`; confirmar que a regra já foi decidida (DEC-002 e PR-004). `monitor_context.mjs --check` e leitura de `.specsfy/RULES.md` feitos; regra já decidida em DEC-002 e PR-004.
  - [x] **EXECUTE**: Acrescentar a regra sem alterar nem remover regras existentes. `.specsfy/RULES.md` ganhou a regra de que o Alembic é a única fonte do schema e de que o app verifica a versão na subida em vez de criar tabelas, sem alterar regras existentes.
  - [x] **VERIFY**: Rodar `monitor_context.mjs --check` e obter `CURRENT`. `monitor_context.mjs --project . --check --acknowledge-project-no-change`: CURRENT.
  - [x] **VISUAL**: Não aplicável: a tarefa só altera documentação e não tem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando e o resultado. Arquivo alterado: `.specsfy/RULES.md`. Implementado pelo Codex a pedido da pessoa responsável; diff revisado e testes reexecutados pelo Claude.
  - [x] **IMPROVE**: Registrar melhoria aplicada ou ausência justificada. Nenhuma melhoria adicional.

#### Fase final — Qualidade

- [x] T024 [TEST] Executar a regressão completa, o Ruff e a rastreabilidade em tests/test_migracao_fila.py, tests/test_verificacao_versao_banco.py, tests/test_app_publicacao_atomica.py, tests/test_app_inicializacao.py e tests/test_deploy_runbook_docs.py — Refs: US-002, US-001, US-003, US-004, FR-002, FR-001, FR-003, FR-004, FR-005, NFR-002, NFR-001, NFR-003, AC-014 — Depends: T018, T019, T020, T021, T022, T023
  - [x] **PREP**: Confirmar com `check_database_safety.mjs` que o banco de testes é separado do de desenvolvimento; identificar suítes, checks e gates. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE; destino `.env.testing.example` (Postgres local de testes).
  - [x] **EXECUTE**: Executar `.venv/bin/python -m pytest -q`, `.venv/bin/ruff check .` e `check_traceability.mjs`; revisar `PROJECT.md` ou registrar a avaliação sem impacto material. Executados `.venv/bin/python -m pytest -q`, `.venv/bin/ruff check .`, `check_traceability.mjs --full-chain` e `verify_acceptance.mjs`. `PROJECT.md` revisado: não descreve `create_all` nem o preparo do banco no deploy; finalidade, capacidades e limites não mudam, então a avaliação é sem impacto material e `monitor_context.mjs --check --acknowledge-project-no-change` retornou CURRENT.
  - [x] **VERIFY**: Confirmar ausência de gaps: nenhum teste preexistente falha, exceto os que afirmavam o `create_all` na subida, já atualizados. Regressão completa: **834 passed, 1 skipped, 1 failed em 828 s**. A única falha, `tests/test_spec_markers.py::test_nenhuma_spec_dispara_o_falso_positivo_do_validador`, era um termo da própria spec, na seção 13, que o validador de marcadores rejeita e foi corrigida; reexecutada: 1 passed. Nenhum teste preexistente falhou por causa da mudança.
  - [x] **VISUAL**: Não aplicável: a tarefa só executa testes e análise estática, sem superfície visual.
  - [x] **EVIDENCE**: Registrar contagens e comandos finais e a avaliação de `PROJECT.md`. Ruff limpo; rastreabilidade 29/29 IDs com `--full-chain`: OK; `verify_acceptance.mjs`: QA PASSED (17 de 17 AC); `build_documentation.mjs --check`: exit 0; monitor CURRENT.
  - [x] **IMPROVE**: Registrar a retrospectiva do processo, incluindo o que o ensaio local revelou. A suíte `tests/test_spec_markers.py` já protege o texto das specs; a lição foi conferir o texto da spec com esse teste antes de fechar cada gate.

### 15. Ordem de execução

- Caminho crítico: T001–T017 → T018 → T019 → T020 → T021 → T024.
- Tarefas paralelas: nenhuma marcada `[P]`; T001–T017 compartilham poucos arquivos de teste e seguem em ordem para evitar conflito. T022 depende só de T018 e T023 só de T019, e podem andar em paralelo com T020 e T021 por não tocarem os mesmos arquivos.
- Estratégia de MVP: T001–T003 e T018 entregam o banco pronto com um comando e destravam a T020 da SPEC-0041; T019 elimina a corrida; T020 evita a coleção órfã; T021 documenta.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Bloqueia a T020 da SPEC-0041 (deploy do beta no Supabase novo).
- Altera o runbook entregue pela SPEC-0035 e a subida definida na SPEC-0012.

#### Riscos

- Remover o `create_all` quebra bancos que dependem dele, como o de desenvolvimento → passo documentado de adoção (`alembic stamp head`) e mensagem clara na subida.
- A verificação de versão pode bloquear a subida por engano em um banco migrado → comparar com o head dos scripts do Alembic e cobrir com testes de banco no head, atrasado e vazio.
- A compensação pós-commit pode falhar e deixar resíduo → executar em transação própria, registrar a falha no log sem segredos e cobrir com teste de falha na própria compensação.
- Testes que dependiam do `create_all` na subida → ajustar para o novo contrato; o `conftest` já usa schema isolado e aplica a fila por conta própria.

#### Suposições

- Em coleção que já existia, a compensação remove apenas o envio e os arquivos do pedido e mantém a coleção e os envios anteriores (inferência a partir de "a coleção não fica gravada" aplicada só à coleção nova).
- Bancos com schema criado pelo `create_all` têm o schema completo; a conferência é feita pela pessoa operadora antes do `stamp`.
- O beta usa um banco novo (Supabase), então não precisa do passo de adoção.

### 17. Decisões

- **DEC-001**: O schema da fila é aplicado por uma migration do Alembic, criada somente se ainda não existir — decisão da pessoa responsável em 2026-10-22. Alternativas descartadas: passo manual no runbook (depende de lembrar) e aplicação na subida do backend (mistura migração com inicialização).
- **DEC-002**: O `create_all` sai da subida e o app verifica a versão do banco, parando com mensagem clara — decisão da pessoa responsável em 2026-10-22. Alternativas descartadas: remover sem verificação (erro tardio) e manter com lock (duas fontes de schema).
- **DEC-003**: Falha ao enfileirar desfaz a publicação inteira, sem coleção nem envio órfãos — decisão da pessoa responsável em 2026-10-22. Alternativas descartadas: manter a coleção com situação "falhou" e deixar para outro item.
- **DEC-004**: Bancos criados pelo `create_all` são adotados por `alembic stamp head` documentado no runbook — decisão da pessoa responsável em 2026-10-22. Alternativas descartadas: migration inicial que pula tabelas existentes (esconde diferenças de schema) e recriar os bancos.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/DATABASE.md` revisado: schema da fila (`procrastinate_*`) e `alembic_version` passam a constar como preparados pelo Alembic.
- [x] `.specsfy/RULES.md` revisado para a regra de que o Alembic é a única fonte do schema e de que o app não cria tabelas na subida.
- [x] `PROJECT.md` revisado, ou a avaliação sem impacto material registrada na evidência da tarefa.
