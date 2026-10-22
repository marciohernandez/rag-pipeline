# Especificação integrada: Serviços externos de Qdrant e Postgres no stack de produção

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0041 |
| Slug | 0041-servicos-externos-qdrant-postgres-producao |
| Status | Implementing |
| Effort | 5 |
| Effort updated at | 2026-10-19 |
| Effort rationale | Edição de um stack Swarm, de scripts de shell de backup e deploy e de uma regra de nome de coleção, sem schema nem interface. O risco está em segredos, na conexão TLS com o Postgres e no isolamento das coleções já existentes no Qdrant; a prova real fica com a pessoa na VPS (perfil `standard`). |
| ClickUp Task | |
| Milestones | M03 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | In Progress |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-10-19 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O stack de produção (`deploy/stack.prod.yml`) sobe o próprio Qdrant e o próprio Postgres em contêineres, com host e URL fixos (`qdrant_ragpipeline`, `postgres_ragpipeline`). A pessoa responsável já tem um Qdrant publicado (com coleções em uso) e quer um Postgres gerenciado, e não quer subir esses dois serviços na VPS. Hoje não há como apontar o stack para eles por configuração: o `QDRANT_URL` está fixo, a chave de API do Qdrant não é entregue, o host do Postgres está fixo e o backup depende do Postgres interno. Além disso, o sistema cria e apaga coleções no Qdrant a partir de nomes escolhidos na tela, o que pode colidir com as coleções que já existem no servidor compartilhado.

#### Resultado desejado

Um stack de produção que se conecta a um Qdrant e a um Postgres externos apenas por variáveis e secrets, mantém o backup diário cifrado no R2 contra o banco externo e dá às coleções novas um prefixo configurável, sem tocar nas coleções já existentes.

#### Métricas de sucesso

- Zero serviços de Qdrant ou Postgres e zero volumes dos dois no stack de produção.
- Zero valores de host, usuário, senha, chave ou domínio reais no repositório.
- Zero comandos que apaguem ou recriem banco ou coleção existente nesta entrega.
- Backup diário concluído com `resultado=sucesso` contra o Postgres externo na primeira verificação real na VPS (T020).

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: como o código monta a conexão e os nomes de coleção → `src/app/main.py` lê `APP_DATABASE_URL` e `QDRANT_URL`; `src/pipeline/providers/vectorstores/qdrant.py` já lê `QDRANT_API_KEY`; `src/app/colecoes.py` gera `nome_fisico` a partir do nome escolhido, imutável. Impacto: a chave do Qdrant só precisa ser entregue pelo stack, e o prefixo entra na geração do nome físico.
- **R-002**: como o backup acessa o banco → `deploy/backup/comum.sh` usa `PGHOST`, `PGPORT`, `PGUSER` e `PGDATABASE` com padrões internos e lê `postgres_password`. Impacto: basta tornar os valores configuráveis pelo stack e acrescentar `PGSSLMODE`.

#### Fontes e contexto consultados

- `deploy/stack.prod.yml`, `deploy/backup/comum.sh`, `deploy/SECRETS.md`, `deploy/RUNBOOK.md`, `.env.testing` (somente o formato, sem valores), `src/app/colecoes.py`, `src/app/main.py`, `src/app/models.py`.
- Backlog `specs/backlog/0046-servicos-externos-de-qdrant-e-postgres-no-stack-de-producao.md` e as respostas confirmadas na conversa de 2026-10-19.

#### Documentação consultada

- Nenhuma documentação externa nova: o formato da conexão do Supabase (pooler em modo sessão, porta 5432, `sslmode=require`) já está documentado em `.env.testing.example` no repositório.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Qual Postgres externo? → **A**: Supabase, em projeto novo e separado do de teste, pelo pooler em modo sessão, porta 5432, com `sslmode=require`.
- **Q**: Qual Qdrant? → **A**: o servidor já publicado (`qdrant.smartsystem.ia.br`), com URL e chave de API do beta; ele já tem coleções em produção.
- **Q**: O que fazer com o backup? → **A**: manter `backup_ragpipeline` no Swarm, apontando para o Postgres externo, com o mesmo dump cifrado no R2.
- **Q**: Como proteger as coleções existentes? → **A**: prefixo configurável nas coleções criadas pelo sistema (`beta-` no beta), que a pessoa poderá esvaziar mais tarde.

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Remoção de `postgres_ragpipeline`, `qdrant_ragpipeline` e dos volumes `postgres_data_ragpipeline` e `qdrant_data_ragpipeline` do stack de produção.
- Conexão do backend e do worker ao Postgres externo por variáveis (host, porta, banco, usuário, modo SSL) e pelo secret de senha existente.
- Entrega de `QDRANT_URL` e da chave de API por secret `qdrant_api_key`.
- Prefixo configurável aplicado ao nome físico das coleções novas.
- Backup apontando para o Postgres externo.
- Verificação de variáveis e secrets no deploy e atualização do runbook, dos secrets e do backup.

#### Fora de escopo

- Criar o projeto Supabase ou instalar qualquer serviço externo (feito pela pessoa).
- Renomear ou migrar coleções já existentes no Qdrant, ou levar as coleções `beta-` para a produção sem prefixo.
- Trocar o provedor de embeddings ou de LLM, o R2 de uploads e o Traefik.
- Qualquer comando que apague, recrie ou zere banco ou coleção.
- O deploy em si, que continua sendo a SPEC-0032/T027, agora precedida pelas tarefas desta spec.

#### Atores

- **Pessoa responsável pelo deploy**: configura variáveis e secrets, aplica a migração e executa o deploy manual na VPS.
- **Pessoa usuária do sistema**: cria coleções pela tela e não vê mudança de fluxo.
- **Serviço de backup**: gera e envia o dump cifrado ao bucket separado.

### 4. Princípios e restrições do projeto

- **PR-001**: Nenhum segredo, host, usuário, chave ou domínio real entra no repositório; valores vêm de variáveis e de secrets do Swarm.
- **PR-002**: Nenhuma etapa executa comando destrutivo de banco ou de coleção, nem testes contra o banco de desenvolvimento.
- **PR-003**: O deploy continua manual e feito somente pela pessoa responsável.
- **PR-004**: O Postgres externo é acessado só com TLS (`sslmode=require` no mínimo).

### 5. Histórias de usuário

#### US-001 — Implantar o beta usando um Postgres externo (P1)

Como pessoa responsável pelo deploy, quero que backend e worker se conectem a um Postgres externo por configuração, para não subir banco na VPS.

**Por que P1**: sem isso o beta não sobe com o Supabase.
**Teste independente**: ler o stack e executar o teste que monta a URL a partir de variáveis e do secret.
**Requisitos**: FR-001, FR-005

#### US-002 — Usar o Qdrant publicado sem colidir com as coleções existentes (P1)

Como pessoa responsável pelo deploy, quero que o sistema use o Qdrant já publicado, com chave de API e um prefixo nas coleções novas, para não afetar o que já está em produção.

**Por que P1**: o servidor é compartilhado e tem coleções em uso.
**Teste independente**: criar uma coleção com prefixo e conferir o nome físico, e ler o stack para a URL e a chave.
**Requisitos**: FR-002, FR-003

#### US-003 — Manter o backup diário contra o banco externo (P2)

Como pessoa responsável pelo deploy, quero que o backup cifrado continue rodando contra o Postgres externo, para não perder a proteção entregue na SPEC-0034.

**Por que P2**: o backup só é possível depois de o banco existir, mas é exigência da operação.
**Teste independente**: rodar o script de backup com binários falsos apontando para um host externo.
**Requisitos**: FR-004

### 6. Cenários BDD de aceite

#### AC-001 — Stack de produção sem Qdrant e Postgres internos

**Cobre**: US-001, US-002, US-003, FR-001, FR-002, FR-004, NFR-003

```gherkin
@US-001 @US-002 @US-003 @FR-001 @FR-002 @FR-004 @NFR-003 @AC-001
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Stack de produção sem Qdrant e Postgres internos
    Given o stack de produção do Swarm
    When a pessoa lê `deploy/stack.prod.yml`
    Then não há serviço `postgres_ragpipeline` nem `qdrant_ragpipeline`, nem volumes `postgres_data_ragpipeline` e `qdrant_data_ragpipeline`, e o serviço `backup_ragpipeline` e a API não dependem de nenhum deles
```

#### AC-002 — Backend e worker montam a conexão com o Postgres externo

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-002
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Backend e worker montam a conexão com o Postgres externo
    Given o host, a porta, o banco, o usuário e o modo SSL informados por variáveis e a senha vinda do secret `postgres_password`
    When backend e worker montam `APP_DATABASE_URL`
    Then a URL aponta para o host externo, exige `sslmode=require` por padrão e não contém host nem senha literais no stack
```

#### AC-003 — Senha com caracteres especiais continua válida na URL

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-003
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Senha com caracteres especiais continua válida na URL
    Given uma senha de Postgres com `@`, `:`, `/` e `%`
    When a URL de conexão é montada a partir do secret
    Then a senha é codificada na URL e a conexão usa o usuário e o host informados, sem expor a senha em argumento de processo
```

#### AC-004 — Qdrant externo recebe URL e chave de API

**Cobre**: US-002, FR-002, NFR-001

```gherkin
@US-002 @FR-002 @NFR-001 @AC-004
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Qdrant externo recebe URL e chave de API
    Given `QDRANT_URL` informado e o secret `qdrant_api_key` criado
    When backend e worker iniciam
    Then `QDRANT_URL` aponta para o servidor externo e `QDRANT_API_KEY` é lida do secret em `/run/secrets`, nunca de valor literal no stack
```

#### AC-005 — Prefixo aplicado ao nome físico de coleção nova

**Cobre**: US-002, FR-003, NFR-003

```gherkin
@US-002 @FR-003 @NFR-003 @AC-005
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Prefixo aplicado ao nome físico de coleção nova
    Given o prefixo `beta-` configurado e uma coleção chamada `Manuais`
    When a coleção é criada
    Then o nome físico no Qdrant é `beta-Manuais`, o nome exibido continua `Manuais` e o nome físico permanece imutável
```

#### AC-006 — Prefixo vazio preserva o comportamento atual

**Cobre**: US-002, FR-003, NFR-002

```gherkin
@US-002 @FR-003 @NFR-002 @AC-006
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Prefixo vazio preserva o comportamento atual
    Given nenhum prefixo configurado
    When uma coleção é criada
    Then o nome físico é igual ao slug atual, e as coleções criadas antes continuam com o mesmo nome
```

#### AC-007 — Prefixo respeita o limite do nome e as reservas

**Cobre**: US-002, FR-003, NFR-003

```gherkin
@US-002 @FR-003 @NFR-003 @AC-007
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Prefixo respeita o limite do nome e as reservas
    Given o prefixo `beta-` e um nome cujo slug, somado ao prefixo, ultrapassa o limite do nome físico, ou coincide com um nome reservado
    When a coleção é criada
    Then o limite considera o prefixo, o sistema nunca gera um nome maior que o limite, e a verificação de nomes reservados e em uso vale para o nome com prefixo
```

#### AC-008 — Backup usa o Postgres externo

**Cobre**: US-003, FR-004, NFR-001

```gherkin
@US-003 @FR-004 @NFR-001 @AC-008
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Backup usa o Postgres externo
    Given host, porta, banco, usuário e modo SSL do Postgres externo e a senha no secret
    When o ciclo de backup roda
    Then o `pg_dump` usa esses valores, o arquivo cifrado vai ao bucket de backup e a senha não aparece em log nem em argumento
```

#### AC-009 — Backup acusa Postgres externo inacessível sem apagar o anterior

**Cobre**: US-003, FR-004, NFR-002

```gherkin
@US-003 @FR-004 @NFR-002 @AC-009
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Backup acusa Postgres externo inacessível sem apagar o anterior
    Given o Postgres externo inacessível ou recusando a senha
    When o ciclo de backup roda
    Then o ciclo termina com `resultado=falha`, o aviso de falha é enviado e o backup anterior no bucket permanece intacto
```

#### AC-010 — Deploy recusado sem a configuração externa

**Cobre**: US-001, FR-002, FR-005, NFR-001

```gherkin
@US-001 @FR-002 @FR-005 @NFR-001 @AC-010
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Deploy recusado sem a configuração externa
    Given as variáveis `DATABASE_HOST` ou `QDRANT_URL` ausentes
    When a pessoa executa `deploy/build_and_deploy.sh`
    Then o script recusa antes de qualquer build, nomeia cada variável ausente e não imprime valores
```

#### AC-011 — Documentação sem valores reais e com a migração no banco externo

**Cobre**: US-001, FR-005, NFR-001

```gherkin
@US-001 @FR-005 @NFR-001 @AC-011
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Documentação sem valores reais e com a migração no banco externo
    Given `deploy/RUNBOOK.md`, `deploy/SECRETS.md` e `deploy/BACKUP.md`
    When a pessoa os lê
    Then descrevem as variáveis do Postgres e do Qdrant externos, o secret `qdrant_api_key`, o prefixo de coleção e a migração do Alembic contra o banco externo, sem host, usuário, senha, chave ou domínio reais
```

#### AC-012 — Ensaio local e testes existentes seguem válidos

**Cobre**: US-003, FR-001, FR-002, NFR-002

```gherkin
@US-003 @FR-001 @FR-002 @NFR-002 @AC-012
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Ensaio local e testes existentes seguem válidos
    Given o stack local de ensaio (`deploy/stack.local.yml`) e os testes de SPEC-0022, SPEC-0027, SPEC-0032, SPEC-0034 e SPEC-0035
    When a suíte de regressão roda
    Then nenhum teste preexistente falha, exceto os que afirmavam os serviços internos de produção, que são atualizados para o novo contrato, e o ensaio local continua com seus serviços próprios
```

#### AC-013 — Deploy confere o secret da chave do Qdrant

**Cobre**: US-001, FR-002, FR-005, NFR-001

```gherkin
@US-001 @FR-002 @FR-005 @NFR-001 @AC-013
Feature: Serviços externos de Qdrant e Postgres em produção

  Scenario: Deploy confere o secret da chave do Qdrant
    Given o secret `qdrant_api_key` ausente no Swarm
    When a pessoa executa `deploy/build_and_deploy.sh`
    Then o script para antes de qualquer build, lista o secret ausente e o comando de criação, e não imprime valores
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O stack de produção deve conectar backend e worker ao Postgres externo por `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER` e `DATABASE_SSLMODE` (padrão `require`) e pelo secret `postgres_password`, e não deve declarar `postgres_ragpipeline` nem seu volume.
- **FR-002**: O stack de produção deve usar `QDRANT_URL` informado por variável e a chave de API lida do secret `qdrant_api_key`, e não deve declarar `qdrant_ragpipeline` nem seu volume.
- **FR-003**: O sistema deve aplicar o prefixo configurado em `APP_COLECAO_PREFIXO` ao nome físico das coleções criadas depois da configuração, sem alterar coleções existentes, sem exceder o limite do nome físico e com valor vazio como padrão; o stack deve aplicar o mesmo prefixo às coleções fixas do sistema (`APP_VECTOR_STORE_COLLECTION` e `APP_ASSISTANT_KNOWLEDGE_COLLECTION`).
- **FR-004**: O serviço de backup deve usar `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE` e `PGSSLMODE` vindos do stack, manter o dump cifrado no bucket de backup e preservar o backup anterior quando o banco estiver inacessível.
- **FR-005**: O deploy deve recusar a execução, antes de qualquer build, quando `DATABASE_HOST`, `QDRANT_URL` ou um secret exigido (incluindo `qdrant_api_key`) estiver ausente, e a documentação deve descrever as variáveis, os secrets, o prefixo e a migração no banco externo.

#### Não funcionais

- **NFR-001**: Segurança: nenhum valor sensível literal no repositório, no stack, em argumentos de processo ou em logs. **Verificação**: testes que varrem o stack e os scripts, e conferência de `deploy/*.md` sem valores reais.
- **NFR-002**: Compatibilidade: o ensaio local e os testes existentes continuam passando, e prefixo vazio mantém o comportamento atual. **Verificação**: regressão completa com Pytest, Ruff e testes do stack.
- **NFR-003**: Proteção de dados: nada nesta entrega apaga ou recria banco ou coleção, e nomes com prefixo nunca ultrapassam o limite nem colidem com reservados. **Verificação**: testes de nome físico e revisão do diff por comandos destrutivos.

#### Erros e casos-limite

- Host, usuário ou banco ausentes → deploy recusado com a lista do que falta (AC-010).
- Secret `qdrant_api_key` ausente → deploy recusado antes do build (AC-013).
- Senha com caracteres especiais → codificada na URL (AC-003).
- Postgres externo inacessível durante o backup → falha registrada e aviso, backup anterior preservado (AC-009).
- Prefixo mais nome acima do limite → o sistema respeita o limite (AC-007).
- Trocar o prefixo depois: coleções criadas com o prefixo antigo mantêm o nome físico e deixam de ser encontradas por um nome novo; não há migração automática (fora de escopo).

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Python 3 com FastAPI, SQLAlchemy e Alembic; stack Swarm com Traefik; testes com Pytest; scripts de deploy e backup em Bash.
- `backend_ragpipeline` e `worker_ragpipeline` montam `APP_DATABASE_URL` por um `python -c` que codifica a senha do secret; o host interno está fixo.
- O Qdrant externo é lido por `QDRANT_URL` e `QDRANT_API_KEY` em `src/pipeline/providers/vectorstores/qdrant.py`.
- O nome físico da coleção é gerado em `src/app/colecoes.py` (`nome_fisico=slug`) e validado por `_exigir_nome_fisico_livre`.

#### Arquitetura e módulos

- `deploy/stack.prod.yml`: sai o Postgres e o Qdrant internos; entram as variáveis `DATABASE_*`, `QDRANT_URL`, `APP_COLECAO_PREFIXO` e o secret `qdrant_api_key` nos serviços que precisam deles.
- `deploy/backup/comum.sh`: `configurar_pg` passa a aceitar `PGSSLMODE` e não assume mais o host interno como padrão obrigatório.
- `src/app/settings.py` e `src/app/colecoes.py`: leitura de `APP_COLECAO_PREFIXO` e aplicação ao nome físico.
- `deploy/stack.prod.yml` também compõe `APP_VECTOR_STORE_COLLECTION` e `APP_ASSISTANT_KNOWLEDGE_COLLECTION` com `${APP_COLECAO_PREFIXO}` na frente do nome padrão.
- `deploy/build_and_deploy.sh` e `deploy/secrets.sh`: exigem as variáveis e o novo secret.

#### Migrations

- Não aplicável: não há mudança de schema. A migração do Alembic existente é aplicada ao banco externo, como passo manual do runbook, antes do deploy.

#### Models

- Sem mudança. `Colecao.nome_fisico` continua imutável; apenas a regra que o gera recebe o prefixo.

#### Controllers e casos de uso

- Criação de coleção em `src/app/colecoes.py`: aplica o prefixo antes das verificações de limite, reserva e uso.

#### Views e experiência

- Não aplicável: a entrega não altera telas. O nome exibido da coleção não muda.

#### Queries e repositórios

- Sem mudança de consulta; a verificação de nome em uso e reservado passa a considerar o nome com prefixo.

#### Jobs e processamento assíncrono

- O worker recebe as mesmas variáveis e secrets do backend. Sem mudança de retry ou idempotência.

#### Estrutura de arquivos

```text
specs/draft/0041-servicos-externos-qdrant-postgres-producao/
  spec.md
  research/
deploy/stack.prod.yml
deploy/backup/comum.sh
deploy/build_and_deploy.sh
deploy/secrets.sh
deploy/RUNBOOK.md
deploy/SECRETS.md
deploy/BACKUP.md
src/app/settings.py
src/app/colecoes.py
tests/test_deploy_stack_externo.py
tests/test_deploy_backup_externo.py
tests/test_colecoes_prefixo.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Colecao | id | `nome_fisico` com prefixo configurado na criação, imutável depois | pertence a um Workspace |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Colecao | inexistente | criar com prefixo `beta-` | ativa com `nome_fisico` prefixado | nome físico único e dentro do limite |

#### Migração e retenção

- Não aplicável: nenhuma coluna ou tabela muda. Coleções antigas mantêm o nome físico; coleções criadas com prefixo mantêm o prefixo.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega muda configuração de deploy, scripts e uma regra interna de nome; as telas não mudam.

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

- Não aplicável: nenhum bloco React é criado ou alterado.

#### Estados e acessibilidade

- Não aplicável.

#### Contrato CRUD

- Não aplicável: nenhuma tela de CRUD é criada ou alterada.

#### Revisão visual durante o desenvolvimento

- Não aplicável: a entrega não tem superfície visual. Cada tarefa registra `Não aplicável` com esse motivo.

#### APIs expostas

- Nenhuma API nova. As rotas existentes de coleção passam a gerar o nome físico com o prefixo.

#### APIs externas utilizadas

- Qdrant publicado: URL e chave de API por configuração, TLS, sem fallback.
- Postgres do Supabase: pooler em modo sessão, porta 5432, `sslmode=require`.

#### Documentação das APIs consultadas

- `.env.testing.example` do repositório (formato da conexão do Supabase).

#### Eventos e outros contratos

- Variáveis: `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_SSLMODE`, `QDRANT_URL`, `APP_COLECAO_PREFIXO`. Secrets: `postgres_password`, `qdrant_api_key`.

### 11. Estratégia TDD

- **Unidade**: leitura do stack e dos scripts de deploy e backup sem rede; geração do nome físico com prefixo.
- **Integração/contrato**: criação de coleção pela API com prefixo configurado, usando o banco de teste já isolado.
- **BDD/aceite**: o Gherkin da seção 6 orienta os casos TDD; não há arquivos `.feature`.
- **Runner TDD**: projeto Python, runner existente: Pytest (`.venv/bin/python -m pytest`).
- **E2E**: não aplicável.
- **Verificação manual**: conexão real ao Supabase e ao Qdrant publicado, e backup real, que dependem de serviços e credenciais que não ficam no repositório (T020).

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, US-002, US-003, FR-001, FR-002, FR-004, NFR-003, AC-001 | AC-001 na seção 6 | caso 1 em tests/test_deploy_stack_externo.py com marcador próprio `SPECSFY: SPEC-0041 US-001 US-002 US-003 FR-001 FR-002 FR-004 NFR-003 AC-001` | RED 2026-10-19: o stack ainda declara `postgres_ragpipeline`, `qdrant_ragpipeline` e seus volumes | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-001, FR-001, NFR-001, AC-002 | AC-002 na seção 6 | caso 2 em tests/test_deploy_stack_externo.py com marcador próprio `SPECSFY: SPEC-0041 US-001 FR-001 NFR-001 AC-002` | RED 2026-10-19: a URL usa o host interno fixo e não lê `DATABASE_HOST` | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-001, FR-001, NFR-001, AC-003 | AC-003 na seção 6 | caso 3 em tests/test_deploy_stack_externo.py com marcador próprio `SPECSFY: SPEC-0041 US-001 FR-001 NFR-001 AC-003` | RED 2026-10-19: a URL usa o host interno fixo (a codificação da senha já existe) | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-002, FR-002, NFR-001, AC-004 | AC-004 na seção 6 | caso 4 em tests/test_deploy_stack_externo.py com marcador próprio `SPECSFY: SPEC-0041 US-002 FR-002 NFR-001 AC-004` | RED 2026-10-19: `QDRANT_URL` é fixo e não há secret `qdrant_api_key` | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-002, FR-003, NFR-003, AC-005 | AC-005 na seção 6 | caso 5 em tests/test_colecoes_prefixo.py com marcador próprio `SPECSFY: SPEC-0041 US-002 FR-003 NFR-003 AC-005` | RED 2026-10-19: `colecoes.nome_fisico_com_prefixo` não existe | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-002, FR-003, NFR-002, AC-006 | AC-006 na seção 6 | caso 6 em tests/test_colecoes_prefixo.py com marcador próprio `SPECSFY: SPEC-0041 US-002 FR-003 NFR-002 AC-006` | RED 2026-10-19: `AppSettings.colecao_prefixo` e a função de prefixo não existem | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-002, FR-003, NFR-003, AC-007 | AC-007 na seção 6 | caso 7 em tests/test_colecoes_prefixo.py com marcador próprio `SPECSFY: SPEC-0041 US-002 FR-003 NFR-003 AC-007` | RED 2026-10-19: o limite e a reserva ainda não consideram prefixo | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-003, FR-004, NFR-001, AC-008 | AC-008 na seção 6 | caso 8 em tests/test_deploy_backup_externo.py com marcador próprio `SPECSFY: SPEC-0041 US-003 FR-004 NFR-001 AC-008` | RED 2026-10-19: o serviço de backup não recebe `PGHOST` e demais variáveis de `DATABASE_*` | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-003, FR-004, NFR-002, AC-009 | AC-009 na seção 6 | caso 9 em tests/test_deploy_backup_externo.py com marcador próprio `SPECSFY: SPEC-0041 US-003 FR-004 NFR-002 AC-009` | RED 2026-10-19: sem `PGHOST` o backup assume o host interno e não falha | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-001, FR-002, FR-005, NFR-001, AC-010 | AC-010 na seção 6 | caso 10 em tests/test_deploy_build_and_deploy_script.py com marcador próprio `SPECSFY: SPEC-0041 US-001 FR-002 FR-005 NFR-001 AC-010` | RED 2026-10-19: o deploy não exige `DATABASE_HOST` nem `QDRANT_URL` | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-001, FR-005, NFR-001, AC-011 | AC-011 na seção 6 | caso 11 em tests/test_deploy_runbook_docs.py com marcador próprio `SPECSFY: SPEC-0041 US-001 FR-005 NFR-001 AC-011` | RED 2026-10-19: os documentos não citam as variáveis, o secret e o prefixo | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-003, FR-001, FR-002, NFR-002, AC-012 | AC-012 na seção 6 | caso 12 em tests/test_deploy_stack.py com marcador próprio `SPECSFY: SPEC-0041 US-003 FR-001 FR-002 NFR-002 AC-012` | RED 2026-10-19: o contrato de SPEC-0022 ainda exige os serviços internos de produção | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |
| US-001, FR-002, FR-005, NFR-001, AC-013 | AC-013 na seção 6 | caso 13 em tests/test_deploy_secrets_script.py com marcador próprio `SPECSFY: SPEC-0041 US-001 FR-002 FR-005 NFR-001 AC-013` | RED 2026-10-19: o deploy não exige o secret `qdrant_api_key` | GREEN 2026-10-19 | Regressão sem banco: 503 passed, 0 failed |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | tests/test_deploy_stack_externo.py | Passed |
| FR-001 | AC-002 | Unidade | tests/test_deploy_stack_externo.py | Passed |
| FR-001 | AC-003 | Unidade | tests/test_deploy_stack_externo.py | Passed |
| FR-001 | AC-012 | Regressão | tests/test_deploy_stack.py | Passed |
| FR-002 | AC-001 | Unidade | tests/test_deploy_stack_externo.py | Passed |
| FR-002 | AC-004 | Unidade | tests/test_deploy_stack_externo.py | Passed |
| FR-002 | AC-010 | Unidade | tests/test_deploy_build_and_deploy_script.py | Passed |
| FR-002 | AC-012 | Regressão | tests/test_deploy_stack.py | Passed |
| FR-002 | AC-013 | Unidade | tests/test_deploy_secrets_script.py | Passed |
| FR-003 | AC-005 | Integração | tests/test_colecoes_prefixo.py | Passed |
| FR-003 | AC-006 | Integração | tests/test_colecoes_prefixo.py | Passed |
| FR-003 | AC-007 | Integração | tests/test_colecoes_prefixo.py | Passed |
| FR-004 | AC-001 | Unidade | tests/test_deploy_stack_externo.py | Passed |
| FR-004 | AC-008 | Unidade | tests/test_deploy_backup_externo.py | Passed |
| FR-004 | AC-009 | Unidade | tests/test_deploy_backup_externo.py | Passed |
| FR-005 | AC-010 | Unidade | tests/test_deploy_build_and_deploy_script.py | Passed |
| FR-005 | AC-011 | Unidade | tests/test_deploy_runbook_docs.py | Passed |
| FR-005 | AC-013 | Unidade | tests/test_deploy_secrets_script.py | Passed |
| NFR-001 | AC-002 | Unidade | tests/test_deploy_stack_externo.py | Passed |
| NFR-001 | AC-003 | Unidade | tests/test_deploy_stack_externo.py | Passed |
| NFR-001 | AC-004 | Unidade | tests/test_deploy_stack_externo.py | Passed |
| NFR-001 | AC-008 | Unidade | tests/test_deploy_backup_externo.py | Passed |
| NFR-001 | AC-010 | Unidade | tests/test_deploy_build_and_deploy_script.py | Passed |
| NFR-001 | AC-011 | Unidade | tests/test_deploy_runbook_docs.py | Passed |
| NFR-001 | AC-013 | Unidade | tests/test_deploy_secrets_script.py | Passed |
| NFR-002 | AC-006 | Integração | tests/test_colecoes_prefixo.py | Passed |
| NFR-002 | AC-009 | Unidade | tests/test_deploy_backup_externo.py | Passed |
| NFR-002 | AC-012 | Regressão | tests/test_deploy_stack.py | Passed |
| NFR-003 | AC-001 | Unidade | tests/test_deploy_stack_externo.py | Passed |
| NFR-003 | AC-005 | Integração | tests/test_colecoes_prefixo.py | Passed |
| NFR-003 | AC-007 | Integração | tests/test_colecoes_prefixo.py | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed (2026-10-19)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0041-servicos-externos-qdrant-postgres-producao/spec.md`
- **Achados**: 3 US, 5 FR, 3 NFR e 13 AC; cada US, FR e NFR tem ao menos três AC em `**Cobre**`. Sem BLOCKER. WARNING resolvido: o prefixo também cobre as coleções fixas do sistema (FR-003). WARNING resolvido: a Definition of Done passou a citar STACK, PROJECT, RULES e DATABASE. Nota: as conexões de Qdrant cadastradas pela pessoa na interface têm URL própria e ficam fora desta spec.

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-19)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/planned/0041-servicos-externos-qdrant-postgres-producao/spec.md`
- **Achados**: 21 tarefas (13 `[TEST] [TDD]`, 4 `[CODE]`, 2 `[DOC]`, 1 `[TEST]` de regressão e 1 `[OPS]`); 24 de 24 IDs cobertos. RED válido observado nos 13 casos, cada um por comportamento ausente. Os testes de coleção rodam sem banco, porque o `.env.testing` ainda aponta para um Supabase com placeholder; a regressão das suítes com banco (T019) depende de a pessoa preencher esse arquivo. Caminho crítico: T001–T013 → T014–T018 → T021 → T019 → T020.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0041-servicos-externos-qdrant-postgres-producao/spec.md .`
- **Achados**: Pending.

#### Evidência complementar — ensaio local em Docker (2026-10-22)

- **Aceite**: a pessoa responsável deu o ensaio local por aceito em 2026-10-22, condição que ela mesma impôs antes de qualquer deploy na VPS. Este registro **não** conclui a T020 nem passa o Delivery Gate: o deploy real continua pendente.
- **Ambiente**: Swarm local, imagens do commit `5713fc8` construídas pelos Dockerfiles de produção, `deploy/stack.prod.yml` + `deploy/stack.local.yml`, secrets fictícios `_local_v1`, Postgres e S3 próprios, `APP_COLECAO_PREFIXO=beta-`, acesso por encaminhamento de porta. O stack, as imagens, os volumes e os secrets do ensaio foram removidos ao final.
- **Observado**: 8 serviços em 1/1; cadeia do Alembic aplicada em banco vazio até `0040_grupos_e_tabelas` (31 tabelas); login, workspace, conexões, divisão em chunks e publicação concluídos (envio com 10 previstos e 10 inseridos, worker e fila funcionando).
- **Qdrant**: a conexão cadastrada na aplicação apontava para o Qdrant publicado, e o Qdrant local do stack ficou sem coleções. O ensaio valida o prefixo e a conexão externa pela aplicação, não o `QDRANT_URL` e o `qdrant_api_key` do próprio stack.
- **Achado**: o runbook não aplica o schema da fila (Procrastinate) e o app cria tabelas com `create_all` na subida. Num banco novo a publicação falhou (`type "procrastinate_job_to_defer_v1[]" does not exist`) e o registro da coleção ficou órfão. O ensaio aplicou `procrastinate schema --apply` manualmente. Capturado em `specs/inbox/2026-10-22-191007-aplicar-o-schema-da-fila-procrastinate-no-deploy-e-evitar-corrida-do-create-all.md`; a T020 só deve rodar depois de esse passo constar no runbook.
- **Fora do ensaio**: Supabase externo, HTTPS, HSTS, 429 do login e respostas reais de IA, cobertos pela T020 e pela T027 da SPEC-0032.
- **Limpeza pendente (por conta da pessoa)**: coleções `beta-teste` e `beta-teste1` provavelmente vazias no Qdrant publicado.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso falhando em tests/test_deploy_stack_externo.py — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-004, NFR-003, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-001 porque o stack ainda declara `postgres_ragpipeline`, `qdrant_ragpipeline` e seus volumes.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: o stack ainda declara `postgres_ragpipeline`, `qdrant_ragpipeline` e seus volumes; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso falhando em tests/test_deploy_stack_externo.py — Refs: US-001, FR-001, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-002 porque a URL usa o host interno fixo e não lê `DATABASE_HOST`.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: a URL usa o host interno fixo e não lê `DATABASE_HOST`; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso falhando em tests/test_deploy_stack_externo.py — Refs: US-001, FR-001, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-003 porque a URL usa o host interno fixo (a codificação da senha já existe).
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: a URL usa o host interno fixo (a codificação da senha já existe); falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T004 [TEST] [TDD] [US-002] Derivar do AC-004 um caso falhando em tests/test_deploy_stack_externo.py — Refs: US-002, FR-002, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-004 porque `QDRANT_URL` é fixo e não há secret `qdrant_api_key`.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: `QDRANT_URL` é fixo e não há secret `qdrant_api_key`; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-005 um caso falhando em tests/test_colecoes_prefixo.py — Refs: US-002, FR-003, NFR-003, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-005 porque `colecoes.nome_fisico_com_prefixo` não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: `colecoes.nome_fisico_com_prefixo` não existe; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 um caso falhando em tests/test_colecoes_prefixo.py — Refs: US-002, FR-003, NFR-002, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-006 porque `AppSettings.colecao_prefixo` e a função de prefixo não existem.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: `AppSettings.colecao_prefixo` e a função de prefixo não existem; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso falhando em tests/test_colecoes_prefixo.py — Refs: US-002, FR-003, NFR-003, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-007 porque o limite e a reserva ainda não consideram prefixo.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: o limite e a reserva ainda não consideram prefixo; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T008 [TEST] [TDD] [US-003] Derivar do AC-008 um caso falhando em tests/test_deploy_backup_externo.py — Refs: US-003, FR-004, NFR-001, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-008 porque o serviço de backup não recebe `PGHOST` e demais variáveis de `DATABASE_*`.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: o serviço de backup não recebe `PGHOST` e demais variáveis de `DATABASE_*`; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-009 um caso falhando em tests/test_deploy_backup_externo.py — Refs: US-003, FR-004, NFR-002, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-009 porque sem `PGHOST` o backup assume o host interno e não falha.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: sem `PGHOST` o backup assume o host interno e não falha; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T010 [TEST] [TDD] [US-001] Derivar do AC-010 um caso falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-001, FR-002, FR-005, NFR-001, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-010 porque o deploy não exige `DATABASE_HOST` nem `QDRANT_URL`.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: o deploy não exige `DATABASE_HOST` nem `QDRANT_URL`; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T011 [TEST] [TDD] [US-001] Derivar do AC-011 um caso falhando em tests/test_deploy_runbook_docs.py — Refs: US-001, FR-005, NFR-001, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-011 porque os documentos não citam as variáveis, o secret e o prefixo.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: os documentos não citam as variáveis, o secret e o prefixo; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso falhando em tests/test_deploy_stack.py — Refs: US-003, FR-001, FR-002, NFR-002, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-012 porque o contrato de SPEC-0022 ainda exige os serviços internos de produção.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: o contrato de SPEC-0022 ainda exige os serviços internos de produção; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T013 [TEST] [TDD] [US-001] Derivar do AC-013 um caso falhando em tests/test_deploy_secrets_script.py — Refs: US-001, FR-002, FR-005, NFR-001, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido. Resultado: RED em AC-013 porque o deploy não exige o secret `qdrant_api_key`.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste e não tem superfície visual.
  - [x] **EVIDENCE**: Comando `.venv/bin/python -m pytest -q <arquivo da tarefa>`; causa do RED: o deploy não exige o secret `qdrant_api_key`; falha de comportamento, não de sintaxe.
  - [x] **IMPROVE**: Cobertura revisada; testes de coleção rodam sem banco para não depender do `.env.testing` ainda sem URL real.

- [x] T014 [CODE] [US-001] Remover `postgres_ragpipeline`, `qdrant_ragpipeline` e seus volumes de deploy/stack.prod.yml; montar `APP_DATABASE_URL` e `QDRANT_*` por variáveis e secrets — Refs: US-001, US-002, FR-001, FR-002, NFR-001, NFR-003, AC-001, AC-002, AC-003, AC-004 — Depends: T001, T002, T003, T004
  - [x] **PREP**: Confirmar RED TDD e dependências.
  - [x] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar arquivos; depois implementar a menor mudança. Stack sem Postgres e Qdrant internos, `DATABASE_*`, `QDRANT_URL`, chave por secret e prefixo nas coleções fixas; `stack.local.yml` passou a trazer Postgres e Qdrant próprios do ensaio.
  - [x] **VERIFY**: Executar testes focais e regressão. `.venv/bin/python -m pytest -q tests/test_deploy_stack_externo.py tests/test_deploy_stack.py`: GREEN.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual. Sem interface alterada.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados. Arquivos alterados conforme a tarefa; regressão sem banco: 503 passed, 1 skipped, 0 failed.
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. Nenhuma melhoria adicional: o escopo ficou no mínimo que torna os testes verdes.
  <!-- specsfy:evidence {"task": "T014", "refs": ["US-001", "US-002", "FR-001", "FR-002", "NFR-001", "NFR-003", "AC-001", "AC-002", "AC-003", "AC-004"], "files": ["deploy/stack.prod.yml"], "commands": [{"run": ".venv/bin/python -m pytest -q tests/test_deploy_stack_externo.py tests/test_deploy_stack.py", "exit": 0}]} -->

- [x] T015 [CODE] [US-002] Aplicar o prefixo configurável `APP_COLECAO_PREFIXO` ao nome físico em src/app/colecoes.py e src/app/settings.py — Refs: US-002, FR-003, NFR-002, NFR-003, AC-005, AC-006, AC-007 — Depends: T005, T006, T007
  - [x] **PREP**: Confirmar RED TDD e dependências.
  - [x] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar arquivos; depois implementar a menor mudança. `colecoes.nome_fisico_com_prefixo`, `AppSettings.colecao_prefixo` e leitura de `APP_COLECAO_PREFIXO` em `main.py`.
  - [x] **VERIFY**: Executar testes focais e regressão. `.venv/bin/python -m pytest -q tests/test_colecoes_prefixo.py`: GREEN.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual. Sem interface alterada.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados. Arquivos alterados conforme a tarefa; regressão sem banco: 503 passed, 1 skipped, 0 failed.
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. Nenhuma melhoria adicional: o escopo ficou no mínimo que torna os testes verdes.
  <!-- specsfy:evidence {"task": "T015", "refs": ["US-002", "FR-003", "NFR-002", "NFR-003", "AC-005", "AC-006", "AC-007"], "files": ["src/app/colecoes.py", "src/app/settings.py"], "commands": [{"run": ".venv/bin/python -m pytest -q tests/test_colecoes_prefixo.py", "exit": 0}]} -->

- [x] T016 [CODE] [US-003] Parametrizar `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE` e `PGSSLMODE` em deploy/backup/comum.sh e no serviço `backup_ragpipeline` — Refs: US-003, FR-004, NFR-001, NFR-002, AC-008, AC-009 — Depends: T008, T009, T012
  - [x] **PREP**: Confirmar RED TDD e dependências.
  - [x] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar arquivos; depois implementar a menor mudança. `configurar_pg` exige `PGHOST`, `PGUSER` e `PGDATABASE` e repassa `PGSSLMODE`; backup do stack recebe `PG*` de `DATABASE_*`.
  - [x] **VERIFY**: Executar testes focais e regressão. `.venv/bin/python -m pytest -q tests/test_deploy_backup_externo.py tests/test_deploy_backup_script.py tests/test_deploy_restore_script.py`: GREEN.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual. Sem interface alterada.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados. Arquivos alterados conforme a tarefa; regressão sem banco: 503 passed, 1 skipped, 0 failed.
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. Nenhuma melhoria adicional: o escopo ficou no mínimo que torna os testes verdes.
  <!-- specsfy:evidence {"task": "T016", "refs": ["US-003", "FR-004", "NFR-001", "NFR-002", "AC-008", "AC-009"], "files": ["deploy/backup/comum.sh"], "commands": [{"run": ".venv/bin/python -m pytest -q tests/test_deploy_backup_externo.py tests/test_deploy_backup_script.py tests/test_deploy_restore_script.py", "exit": 0}]} -->

- [x] T017 [CODE] [US-001] Exigir `DATABASE_HOST` e `QDRANT_URL` em deploy/build_and_deploy.sh e incluir o secret `qdrant_api_key` em deploy/secrets.sh — Refs: US-001, FR-002, FR-005, NFR-001, AC-010, AC-013 — Depends: T010, T011, T013
  - [x] **PREP**: Confirmar RED TDD e dependências.
  - [x] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar arquivos; depois implementar a menor mudança. `build_and_deploy.sh` exige `DATABASE_HOST`, `DATABASE_USER` e `QDRANT_URL`; `secrets.sh` cria `qdrant_api_key` e passa a pedir a senha do Postgres externo em vez de gerá-la (DEC-004).
  - [x] **VERIFY**: Executar testes focais e regressão. `.venv/bin/python -m pytest -q tests/test_deploy_build_and_deploy_script.py tests/test_deploy_secrets_script.py`: GREEN.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual. Sem interface alterada.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados. Arquivos alterados conforme a tarefa; regressão sem banco: 503 passed, 1 skipped, 0 failed.
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. Nenhuma melhoria adicional: o escopo ficou no mínimo que torna os testes verdes.
  <!-- specsfy:evidence {"task": "T017", "refs": ["US-001", "FR-002", "FR-005", "NFR-001", "AC-010", "AC-013"], "files": ["deploy/build_and_deploy.sh", "deploy/secrets.sh"], "commands": [{"run": ".venv/bin/python -m pytest -q tests/test_deploy_build_and_deploy_script.py tests/test_deploy_secrets_script.py", "exit": 0}]} -->

- [x] T018 [DOC] [US-001] Atualizar deploy/RUNBOOK.md, deploy/SECRETS.md, deploy/BACKUP.md, docs/integrations.md e .env.example com as variáveis externas, o prefixo e a migração — Refs: US-001, FR-005, NFR-001, AC-011 — Depends: T011
  - [x] **PREP**: Confirmar RED TDD e dependências.
  - [x] **EXECUTE**: Implementar a menor mudança. RUNBOOK, SECRETS, BACKUP, docs/integrations.md e .env.example descrevem as variáveis, os secrets, o prefixo e a migração no banco externo.
  - [x] **VERIFY**: Executar testes focais e regressão. `.venv/bin/python -m pytest -q tests/test_deploy_runbook_docs.py`: GREEN.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual. Não aplicável: só documentação.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados. Comandos e resultados acima.
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. Nenhuma melhoria adicional necessária.

- [x] T019 [TEST] Executar a regressão completa, Ruff e a rastreabilidade em tests/test_deploy_stack.py — Refs: NFR-002, AC-012, FR-001, FR-002, US-003 — Depends: T014, T015, T016, T017, T018, T021, T012
  - [x] **PREP**: Dependências T014–T018, T021 e T012 concluídas; destino de teste separado validado por `check_database_safety.mjs --project . --command '.venv/bin/python -m pytest -q'`: SAFE. Retomada em 2026-10-19 na branch da SPEC-0041.
  - [x] **EXECUTE**: Em 2026-10-22, executados regressão completa, Ruff e auditoria dos marcadores, sem alteração de produção. Antes de cada tentativa de Pytest: `node .agents/skills/specsfy-setup/scripts/check_database_safety.mjs --project . --command '.venv/bin/python -m pytest -q'` → SAFE, exit 0. A primeira tentativa, `.venv/bin/python -m pytest -q`, usou o destino remoto de testes e foi interrompida por lentidão (exit 130, sem resumo final). A execução completa usou o PostgreSQL local de testes já ativo, conforme `docker-compose.yml` e o exemplo da CI: `TESTING_ENV_FILE=.env.testing.example .venv/bin/python tests/_database_safety.py` → isolamento SAFE, exit 0; `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q` → exit 1. Nenhum banco de desenvolvimento ou comando destrutivo utilizado.
  - [x] **VERIFY**: Regressão completa com **813 passed, 3 failed, 1 skipped, 2 warnings em 615.51s**, exit 1, executada pelo Codex no sandbox. Reexecução em 2026-10-22 fora do sandbox: `check_database_safety.mjs --project . --command '.venv/bin/python -m pytest -q tests/test_ci_gates.py'` → SAFE; `TESTING_ENV_FILE=.env.testing.example .venv/bin/python -m pytest -q tests/test_ci_gates.py` → **22 passed, 2 warnings em 1.96s**, exit 0, incluindo os três testes que falharam no sandbox. Logo, as 813 aprovações mais os 3 testes reexecutados cobrem a regressão sem falha remanescente. As três falhas do sandbox são de `tests/test_ci_gates.py` (SPEC-0007): `test_ruff_check_runs_cleanly_over_the_repository`, `test_ruff_reports_no_known_semantic_findings` e `test_ruff_line_length_passes_without_reducing_guard_scope`. Seus subprocessos `uv run ruff check ...` retornaram exit 2: `Could not acquire lock` / `Could not create temporary file` / `Read-only file system (os error 30)` em `/home/marcioh/.cache/uv/`. Blocker de ambiente fora da SPEC-0041; nenhuma correção ou nova tentativa após o diagnóstico, conforme o limite solicitado. Ruff direto: `.venv/bin/ruff check .` → `All checks passed!`, exit 0. `.github/workflows/ci.yml` usa `uv run ruff check`, sem `format --check`; checagem de formato não executada.
  - [x] **VISUAL**: Não aplicável: somente execução de testes, análise estática e registro documental, sem alteração de interface.
  - [x] **EVIDENCE**: Auditoria AST via `.venv/bin/python -` em `tests/test_deploy_stack.py` → exit 0: **27 casos, 27 com marcador próprio `SPECSFY:`, 0 sem marcador**. Distribuição: SPEC-0022=9, SPEC-0026=1, SPEC-0027=2, SPEC-0032=11, SPEC-0034=2, SPEC-0035=1, SPEC-0041=1. O caso `test_ensaio_local_mantem_servicos_proprios_e_o_contrato_da_producao_e_externo` (linha 543) declara `SPECSFY: SPEC-0041 US-003 FR-001 FR-002 NFR-002 AC-012`, cobrindo todas as referências da T019. Logs desta execução em `/tmp/spec0041-t019-pytest.log` (tentativa interrompida) e `/tmp/spec0041-t019-pytest-local.log` (regressão completa). `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → CURRENT, exit 0, no início e após a regressão. Único arquivo versionado alterado: esta `spec.md`, somente no checklist de T019. T019 concluída após a reexecução dos três testes fora do sandbox; não houve ação na VPS, deploy, commit/push ou alteração da SPEC-0032/T027.
  - [x] **IMPROVE**: Nenhuma melhoria aplicada no repositório: a falha foi só do sandbox do Codex, cujo cache do `uv` é somente leitura. Para futuras delegações, liberar escrita em `~/.cache/uv` ou definir `UV_CACHE_DIR` dentro do projeto.

- [x] T021 [DOC] Registrar a mudança em .specsfy/STACK.md, .specsfy/DATABASE.md, .specsfy/RULES.md e PROJECT.md (ou a avaliação sem impacto material) — Refs: US-001, US-002, FR-001, FR-002, FR-003, NFR-001, AC-001, AC-004, AC-005 — Depends: T014, T015
  - [x] **PREP**: Rodar `monitor_context.mjs --check` e ler os quatro documentos.
  - [x] **EXECUTE**: Atualizar STACK (Qdrant e Postgres externos), DATABASE (Postgres do Supabase), RULES (prefixo e TLS) e revisar PROJECT. STACK, DATABASE e RULES atualizados; `monitor_context.mjs --check --acknowledge-project-no-change` retornou CURRENT (PROJECT.md: a finalidade e as capacidades não mudam, só a topologia de produção, já refletida em STACK e DATABASE).
  - [x] **VERIFY**: Rodar `monitor_context.mjs --check` e obter CURRENT. Monitor CURRENT.
  - [x] **VISUAL**: Não aplicável: a tarefa só altera documentação. Não aplicável: só documentação.
  - [x] **EVIDENCE**: Registrar o comando, o resultado e as avaliações sem impacto. Comandos e resultados acima.
  - [x] **IMPROVE**: Registrar melhoria aplicada ou ausência justificada. Nenhuma melhoria adicional necessária.

- [ ] T020 [OPS] Deploy do beta com serviços externos: criar o projeto Supabase novo, `qdrant_api_key`, aplicar a migração do Alembic no banco externo e rodar a conferência (SPEC-0032 T027) seguindo deploy/RUNBOOK.md — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-004, AC-001, AC-004, AC-008 — Depends: T019
  - [ ] **PREP**: Confirmar dependências e o ambiente.
  - [ ] **EXECUTE**: Executar o procedimento.
  - [ ] **VERIFY**: Executar testes focais e regressão.
  - [ ] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.

### 15. Ordem de execução

- Caminho crítico: T001–T013 → T014/T015/T016/T017/T018 → T019 → T020.
- Tarefas paralelas: T014, T015, T016, T017 e T018 não compartilham arquivo, mas T014 e T016 tocam o mesmo stack e seguem em ordem.
- Estratégia de MVP: T014 e T017 entregam o stack externo e o deploy seguro; T015 protege as coleções; T016 mantém o backup.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Projeto Supabase novo e chave de API do Qdrant, criados pela pessoa responsável.
- SPEC-0032 (T027) passa a depender desta entrega; SPEC-0034 e SPEC-0035 são alteradas só em seus scripts e textos operacionais.

#### Riscos

- O Postgres externo recusa a conexão ou o `pg_dump` pelo pooler → mitigação: pooler em modo sessão, `sslmode=require` e verificação real em T020.
- O prefixo faz o sistema parar de enxergar coleções ao ser removido → mitigação: limite documentado, sem migração automática.
- Colisão com coleções existentes no Qdrant compartilhado → mitigação: prefixo `beta-` e nenhum comando destrutivo.

#### Suposições

- O limite atual do nome físico (`_NOME_MAXIMO`) é mantido e passa a incluir o prefixo.
- `DATABASE_SSLMODE` tem padrão `require`.
- O nome do banco no Supabase é `postgres`, informado em `DATABASE_NAME`.

### 17. Decisões

- **DEC-001**: Postgres externo é o Supabase em projeto novo, pelo pooler em modo sessão — confirmada pela pessoa responsável em 2026-10-19; isola os dados do beta dos de teste.
- **DEC-002**: Qdrant externo é o servidor publicado, com chave de API em secret e prefixo configurável nas coleções — confirmada em 2026-10-19; protege as coleções em produção.
- **DEC-003**: `backup_ragpipeline` permanece no Swarm contra o Postgres externo — confirmada em 2026-10-19; preserva a SPEC-0034 e não depende do plano do provedor.

- **DEC-004**: `postgres_password` em produção é informada (sem eco), não gerada — a senha pertence ao provedor do Postgres externo; trocar o secret exige trocar antes a senha no provedor. Efeito: `deploy/secrets.sh` e seus testes (SPEC-0027) foram ajustados; `stack.local.yml` ganhou Postgres e Qdrant próprios para o ensaio.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
- [ ] `.specsfy/STACK.md` revisado: Qdrant e Postgres passam a ser externos em produção.
- [ ] `PROJECT.md` revisado, ou a avaliação sem impacto material registrada na evidência da tarefa.
- [ ] `.specsfy/RULES.md` revisado para a regra do prefixo de coleção e da conexão TLS.
- [ ] `.specsfy/DATABASE.md` revisado: o Postgres de produção passa a ser o Supabase.
