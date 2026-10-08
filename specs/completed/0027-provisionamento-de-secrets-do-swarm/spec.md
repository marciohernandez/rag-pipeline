# Especificação integrada: Provisionamento e conferência dos secrets de produção do Swarm

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0027 |
| Slug | 0027-provisionamento-de-secrets-do-swarm |
| Status | Complete |
| Effort | 5 |
| Effort updated at | 2026-10-08 |
| Effort rationale | Script de operação com segredos, versionamento por nome, bloqueios para trocas com efeito colateral, mudança no stack e no deploy e testes com `docker` simulado; sem interface, banco ou mudança de pipeline. |
| ClickUp Task | |
| Milestones | M03 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-10-08 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

A stack de produção (SPEC-0022) já consome secrets externos do Swarm e a SPEC-0026 acrescentou o `conexoes_chave`, mas nada cria, confere ou troca esses secrets no servidor. A própria SPEC-0022 deixou para este item a "criação dos docker secrets em si e seu conteúdo real". Sem um processo, o operador cria os secrets à mão, com o risco de deixar credenciais no histórico do shell ou em arquivo, de esquecer um secret e só descobrir depois do deploy, e de trocar `postgres_password` ou `conexoes_chave` sem saber que isso quebra a aplicação. Pedido original (BACKLOG-0030): gerir as credenciais de produção por docker secrets do Swarm, em vez de arquivo `.env` em texto puro no servidor.

#### Resultado desejado

Marcio cria, confere e troca os secrets da aplicação por um script que lê as credenciais sem eco e gera as internas, o deploy recusa seguir quando falta um secret e usa sempre a versão mais recente, as trocas perigosas são bloqueadas por padrão, e o ensaio local usa o mesmo mecanismo com valores fictícios.

#### Métricas de sucesso

- Zero valores de secret em argumentos, histórico, arquivos, logs, erros e stack, medido pelos testes de NFR-001.
- 100% dos deploys por `build_and_deploy.sh` falham antes do build quando falta um secret, medido pelo teste de AC-007.
- Zero criações que sobrescrevem um secret existente, medido pelos testes de AC-003 e AC-004.
- Trocas de `postgres_password` e `conexoes_chave` só com parâmetro e confirmação, medido pelos testes de AC-011 e AC-012.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: O que a stack atual já faz com secrets? → `deploy/stack.prod.yml` declara `openrouter_api_key`, `r2_credentials`, `session_secret`, `postgres_password` e `conexoes_chave` como secrets externos e os serviços os leem em `/run/secrets/*`; a criação dos secrets ficou fora da SPEC-0022 (impacto: esta spec cobre só provisionamento, conferência e troca).
- **R-002**: `session_secret` ainda é usado? → O `deploy/stack.prod.yml` exporta `APP_SESSION_SECRET`, mas nenhum arquivo de `src/` o lê desde a SPEC-0020, quando as sessões passaram a token opaco com hash (impacto: o secret é removido, FR-007).
- **R-003**: Como testar scripts que chamam o `docker`? → `tests/test_deploy_build_and_deploy_script.py` usa um `docker` falso no `PATH` que registra as chamadas (impacto: a estratégia de testes reaproveita esse padrão).

#### Fontes e contexto consultados

- `specs/backlog/0030-gestao-de-secrets-de-producao-via-docker-swarm.md`, origem das decisões (seis perguntas respondidas em 2026-10-08).
- `deploy/stack.prod.yml`, `deploy/stack.local.yml`, `deploy/build_and_deploy.sh`, `tests/test_deploy_stack.py` e `tests/test_deploy_build_and_deploy_script.py`.
- `specs/completed/0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm/spec.md` e `specs/completed/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md` (DEC-012).
- `.specsfy/RULES.md`, `.specsfy/STACK.md` e `.specsfy/DATABASE.md`.

#### Documentação consultada

- Nenhuma documentação externa foi consultada nesta etapa. A hipótese de que um secret externo aceita `name:` com interpolação de variável em arquivo Compose 3.7 está registrada em Riscos e será provada no ensaio local do Swarm antes de a spec ser considerada entregue.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Qual a entrega principal? → **A** (2026-10-08): script em `deploy/` que cria e troca os secrets lendo valores sem eco, mais verificação prévia no deploy; inventário com datas e lembrete de troca ficam fora.
- **Q**: Como trocar um secret sem derrubar a aplicação? → **A**: nome versionado (`<nome>_v<N>`), stack aponta para a versão atual por variável definida no deploy, atualização controlada pelo Swarm e versão anterior preservada.
- **Q**: Como tratar os secrets internos? → **A**: `session_secret`, `postgres_password` e `conexoes_chave` seriam gerados e exibidos uma única vez; pedem-se sem eco só `openrouter_api_key` e `r2_credentials`.
- **Q**: E a troca de `postgres_password` e `conexoes_chave`? → **A**: bloqueada por padrão; só com parâmetro explícito, confirmação digitada e consequência exibida.
- **Q**: E o `session_secret`? → **A**: removido da stack, do teste e do script, porque nada o usa.
- **Q**: O ensaio local entra? → **A**: sim, com `--ambiente local`, sufixo `_local` e valores fictícios, sem pedir chave real.

#### Dúvidas abertas

- Nenhuma dúvida bloqueante. A hipótese técnica sobre `name:` com variável é um risco com verificação planejada, não uma decisão pendente da pessoa.

### 3. Escopo e atores

#### Incluído

- Script `deploy/secrets.sh` com `criar`, `trocar`, `verificar`, `resolver`, `--ambiente` e `--ajuda`.
- Verificação prévia e exportação das variáveis resolvidas em `deploy/build_and_deploy.sh`.
- Nomes versionados nos secrets do `deploy/stack.prod.yml`, remoção do `session_secret` e simplificação do `deploy/stack.local.yml`.
- Ensaio local com valores fictícios.
- Testes com `docker` simulado, `deploy/SECRETS.md` e regras em `.specsfy/RULES.md`.

#### Fora de escopo

- Gerenciadores externos de segredo (Vault, KMS).
- Inventário com datas de criação e lembrete de troca periódica.
- Rotação automática ou agendada.
- Credenciais de backup do Postgres (BACKLOG-0031).
- Automação por CI/CD e o runbook completo de deploy (BACKLOG-0032), que apenas referenciará o script.
- Execução do procedimento de `ALTER USER` no banco: o script só o exibe.
- Remoção de versões antigas de secrets.

#### Atores

- **Marcio, operador**: executa o script no manager do Swarm, guarda os valores exibidos no gerenciador de senhas e decide quando trocar um secret.
- **Serviços da aplicação** (backend, worker e Postgres): leem os secrets em `/run/secrets/*`; não participam do script.

### 4. Princípios e restrições do projeto

- **PR-001**: Nunca versionar ou expor credenciais; segredos ficam fora do repositório e do stack file (`.specsfy/RULES.md`).
- **PR-002**: A chave da OpenRouter, as credenciais do R2 e a chave de cifra das conexões só entram nos serviços por secret do Swarm (SPEC-0022 e SPEC-0026, DEC-012).
- **PR-003**: Trocar a chave de cifra das conexões exige recadastrar as chaves das conexões; não há rotação automática.
- **PR-004**: Nenhum comando destrutivo de banco ou schema é usado ou sugerido pelo script; o procedimento de senha do Postgres é apenas exibido.
- **PR-005**: O corpo desta spec evita as palavras proibidas pela regra de marcadores do projeto (`tests/test_spec_markers.py`).
- **PR-006**: Branch `spec/0027-provisionamento-de-secrets-do-swarm` para a implementação; uma branch nunca carrega duas specs.

### 5. Histórias de usuário

#### US-001 — Criar os secrets de produção pela primeira vez (P1)

Como Marcio, operador do Beta, quero criar os secrets da aplicação no Swarm por um comando que lê as credenciais sem eco e gera as internas, para que nenhuma credencial passe por histórico de shell, arquivo ou stack.

**Por que P1**: Sem os secrets a aplicação não sobe em produção, e hoje não existe forma segura de criá-los.
**Teste independente**: Rodar `deploy/secrets.sh criar` num Swarm de teste e conferir os quatro secrets e a ausência de valores em argumentos e arquivos.
**Requisitos**: FR-001, FR-002, FR-003, FR-009

#### US-002 — Conferir os secrets antes de cada deploy (P1)

Como Marcio, quero que o deploy confira se todos os secrets existem e use a versão mais recente de cada um, para não descobrir um secret ausente só depois de a aplicação falhar em produção.

**Por que P1**: Evita um deploy parcial e mostra o comando exato de correção.
**Teste independente**: Executar `deploy/build_and_deploy.sh` com um secret faltando e confirmar a falha antes do build, e depois com tudo presente e confirmar as variáveis resolvidas.
**Requisitos**: FR-005, FR-006, FR-007

#### US-003 — Trocar um secret sem derrubar a aplicação (P1)

Como Marcio, quero trocar um secret criando uma nova versão e aplicando-a no deploy seguinte, e ser bloqueado nas trocas que têm efeito colateral, para renovar credenciais sem perder o serviço nem as conexões cadastradas.

**Por que P1**: Credenciais precisam ser renovadas, e duas delas (`postgres_password` e `conexoes_chave`) quebram o sistema se trocadas sem o procedimento.
**Teste independente**: Trocar `openrouter_api_key` e conferir a v2 com a v1 preservada; tentar trocar `postgres_password` sem parâmetro e conferir o bloqueio.
**Requisitos**: FR-004, FR-005, FR-010

#### US-004 — Ensaiar o Swarm localmente sem credenciais reais (P2)

Como Marcio, quero preparar o ensaio local do Swarm com secrets fictícios gerados pelo mesmo script, para validar a stack sem expor chaves reais.

**Por que P2**: Mantém o ensaio repetível e evita copiar credenciais de produção para uma máquina de desenvolvimento.
**Teste independente**: Rodar `deploy/secrets.sh criar --ambiente local` e subir a stack com o override local.
**Requisitos**: FR-008, FR-007

### 6. Cenários BDD de aceite

#### AC-001 — Criar os secrets pela primeira vez

**Cobre**: US-001, FR-001, FR-002, NFR-001, NFR-003, NFR-004

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @NFR-003 @NFR-004 @AC-001
Feature: Secrets de produção do Swarm

  Scenario: Criar os secrets pela primeira vez
    Given um Swarm sem nenhum secret da aplicação e um `PATH` restrito a bash, utilitários padrão, `openssl` e o `docker` simulado
    When o operador executa `deploy/secrets.sh criar` e informa a chave da OpenRouter e os quatro campos do R2 sem eco
    Then são criados `openrouter_api_key_v1`, `r2_credentials_v1`, `postgres_password_v1` e `conexoes_chave_v1`, cada valor entra no `docker secret create` somente pela entrada padrão, e o resumo lista nome e versão de cada secret criado com saída 0
```

#### AC-002 — Gerar e exibir uma única vez os secrets internos

**Cobre**: US-001, FR-002, NFR-003

```gherkin
@US-001 @FR-002 @NFR-003 @AC-002
Feature: Secrets de produção do Swarm

  Scenario: Gerar e exibir uma única vez os secrets internos
    Given a criação inicial dos secrets
    When o script gera `postgres_password` e `conexoes_chave`
    Then cada valor gerado aparece uma única vez na saída, a `conexoes_chave` é uma chave Fernet válida de 44 caracteres, a senha do Postgres tem 32 caracteres alfanuméricos, e uma nova execução não reexibe nenhum valor
```

#### AC-003 — Recusar a criação explícita de um secret que já existe

**Cobre**: US-001, FR-001, FR-003, NFR-002

```gherkin
@US-001 @FR-001 @FR-003 @NFR-002 @AC-003
Feature: Secrets de produção do Swarm

  Scenario: Recusar a criação explícita de um secret que já existe
    Given `openrouter_api_key_v1` já existe no Swarm
    When o operador executa `deploy/secrets.sh criar openrouter_api_key`
    Then o script recusa com saída 1 e mensagem que cita o nome, pede troca em vez de criação, não chama `docker secret create` e não pergunta nenhum valor
```

#### AC-004 — Completar somente os secrets ausentes

**Cobre**: US-001, FR-002, FR-003, NFR-002

```gherkin
@US-001 @FR-002 @FR-003 @NFR-002 @AC-004
Feature: Secrets de produção do Swarm

  Scenario: Completar somente os secrets ausentes
    Given `openrouter_api_key_v1` e `postgres_password_v1` já existem e os outros dois não
    When o operador executa `deploy/secrets.sh criar` sem nomes
    Then o script informa os dois existentes como preservados, cria apenas `r2_credentials_v1` e `conexoes_chave_v1`, pede somente os valores dos que vai criar e termina com saída 0
```

#### AC-005 — Recusar entrada vazia ou inválida sem criar nada

**Cobre**: US-001, FR-002, FR-003, FR-009, NFR-004

```gherkin
@US-001 @FR-002 @FR-003 @FR-009 @NFR-004 @AC-005
Feature: Secrets de produção do Swarm

  Scenario: Recusar entrada vazia ou inválida sem criar nada
    Given o operador informa uma chave vazia, ou um endpoint do R2 sem `http` ou `https`
    When o script valida a entrada
    Then ele recusa com saída 1 e mensagem que cita o campo sem repetir o valor digitado, sem chamar `docker secret create` para o secret em questão e sem gravar nada em disco
```

#### AC-006 — Resolver a versão mais alta de cada secret por ambiente

**Cobre**: US-002, US-004, FR-005, FR-008

```gherkin
@US-002 @US-004 @FR-005 @FR-008 @AC-006
Feature: Secrets de produção do Swarm

  Scenario: Resolver a versão mais alta de cada secret por ambiente
    Given o Swarm tem `openrouter_api_key_v1`, `openrouter_api_key_v2` e `openrouter_api_key_local_v1`
    When o operador executa `deploy/secrets.sh resolver` e depois `deploy/secrets.sh resolver --ambiente local`
    Then o primeiro imprime `OPENROUTER_API_KEY_SECRET=openrouter_api_key_v2` e o segundo imprime `OPENROUTER_API_KEY_SECRET=openrouter_api_key_local_v1`, sem nenhum valor de secret
```

#### AC-007 — Bloquear o deploy quando falta um secret

**Cobre**: US-002, FR-005, FR-006, NFR-004

```gherkin
@US-002 @FR-005 @FR-006 @NFR-004 @AC-007
Feature: Secrets de produção do Swarm

  Scenario: Bloquear o deploy quando falta um secret
    Given `conexoes_chave` não existe no Swarm
    When o operador executa `deploy/build_and_deploy.sh`
    Then a verificação falha antes de qualquer `docker build` e de `docker stack deploy`, lista `conexoes_chave`, mostra o comando `deploy/secrets.sh criar conexoes_chave` e termina com saída diferente de 0
```

#### AC-008 — Entregar a versão resolvida ao stack no deploy

**Cobre**: US-002, FR-005, FR-006, FR-007

```gherkin
@US-002 @FR-005 @FR-006 @FR-007 @AC-008
Feature: Secrets de produção do Swarm

  Scenario: Entregar a versão resolvida ao stack no deploy
    Given todos os secrets existem e `openrouter_api_key_v2` é a versão mais alta
    When o deploy chega ao `docker stack deploy`
    Then o ambiente do comando contém `OPENROUTER_API_KEY_SECRET=openrouter_api_key_v2` e as demais variáveis resolvidas, e o deploy segue sem pedir nenhum valor
```

#### AC-009 — Declarar o stack só com secrets externos versionados e sem `session_secret`

**Cobre**: US-002, FR-007

```gherkin
@US-002 @FR-007 @AC-009
Feature: Secrets de produção do Swarm

  Scenario: Declarar o stack só com secrets externos versionados e sem `session_secret`
    Given o arquivo `deploy/stack.prod.yml`
    When os testes do stack o inspecionam
    Then cada secret externo usa `name:` com variável e padrão `_v1`, nenhum serviço referencia nem exporta `session_secret`, o Postgres usa `postgres_password` pelo mesmo mecanismo e nenhum valor sensível está em texto puro
```

#### AC-010 — Trocar um secret criando a próxima versão

**Cobre**: US-003, FR-004, FR-005, NFR-002

```gherkin
@US-003 @FR-004 @FR-005 @NFR-002 @AC-010
Feature: Secrets de produção do Swarm

  Scenario: Trocar um secret criando a próxima versão
    Given `openrouter_api_key_v1` está em uso
    When o operador executa `deploy/secrets.sh trocar openrouter_api_key` e informa a nova chave sem eco
    Then nasce `openrouter_api_key_v2`, a v1 não é removida nem alterada, e a saída explica que o próximo deploy aplica a nova versão em atualização controlada pelo Swarm
```

#### AC-011 — Bloquear a troca de secret com efeito colateral por padrão

**Cobre**: US-003, FR-004, NFR-004, FR-010

```gherkin
@US-003 @FR-004 @NFR-004 @FR-010 @AC-011
Feature: Secrets de produção do Swarm

  Scenario: Bloquear a troca de secret com efeito colateral por padrão
    Given `postgres_password_v1` e `conexoes_chave_v1` existem
    When o operador executa `deploy/secrets.sh trocar postgres_password` e `deploy/secrets.sh trocar conexoes_chave` sem o parâmetro explícito
    Then o script recusa os dois com saída 1, mostra a consequência de cada um (Postgres: alterar a senha dentro do banco antes; conexões: recadastrar todas as chaves) e não cria nenhum secret
```

#### AC-012 — Permitir a troca perigosa só com parâmetro e confirmação digitada

**Cobre**: US-003, FR-004, FR-010, NFR-001

```gherkin
@US-003 @FR-004 @FR-010 @NFR-001 @AC-012
Feature: Secrets de produção do Swarm

  Scenario: Permitir a troca perigosa só com parâmetro e confirmação digitada
    Given `postgres_password_v1` existe
    When o operador executa `deploy/secrets.sh trocar postgres_password --confirmar-consequencia`, digita a confirmação pedida e depois repete sem a confirmação correta
    Then com a confirmação correta o script mostra o procedimento manual, cria `postgres_password_v2` e exibe o novo valor uma única vez; com confirmação errada não cria nada e termina com saída 1
```

#### AC-013 — Manter a versão anterior quando a troca é interrompida

**Cobre**: US-003, FR-004, NFR-002

```gherkin
@US-003 @FR-004 @NFR-002 @AC-013
Feature: Secrets de produção do Swarm

  Scenario: Manter a versão anterior quando a troca é interrompida
    Given `r2_credentials_v1` está em uso e o `docker secret create` da v2 falha
    When o operador executa `deploy/secrets.sh trocar r2_credentials`
    Then o script termina com saída diferente de 0, informa que a v1 continua valendo, não remove nada e a resolução seguinte continua apontando para `r2_credentials_v1`
```

#### AC-014 — Preparar o ensaio local com valores fictícios

**Cobre**: US-004, FR-008, NFR-003

```gherkin
@US-004 @FR-008 @NFR-003 @AC-014
Feature: Secrets de produção do Swarm

  Scenario: Preparar o ensaio local com valores fictícios
    Given um Swarm local sem secrets
    When o operador executa `deploy/secrets.sh criar --ambiente local`
    Then são criados os quatro secrets com sufixo `_local_v1` sem nenhuma pergunta, a chave da OpenRouter é fictícia, o `r2_credentials` não ativa o R2 e a senha e a chave Fernet são geradas
```

#### AC-015 — Subir o ensaio local pelo mesmo mecanismo de versão

**Cobre**: US-004, FR-007, FR-008

```gherkin
@US-004 @FR-007 @FR-008 @AC-015
Feature: Secrets de produção do Swarm

  Scenario: Subir o ensaio local pelo mesmo mecanismo de versão
    Given os secrets `_local_v1` existem e `deploy/stack.local.yml` é combinado ao stack de produção
    When os testes do stack inspecionam o override
    Then o override não mapeia secrets por nome fixo, mantém só o volume de uploads, e as variáveis `*_SECRET` resolvidas para o ambiente local selecionam os secrets `_local`
```

#### AC-016 — Nunca expor o valor de um secret

**Cobre**: US-001, US-003, FR-009, NFR-001

```gherkin
@US-001 @US-003 @FR-009 @NFR-001 @AC-016
Feature: Secrets de produção do Swarm

  Scenario: Nunca expor o valor de um secret
    Given valores sentinela informados e gerados durante criação e troca
    When o teste percorre argumentos de cada chamada ao `docker`, saída padrão, saída de erro e arquivos temporários
    Then nenhum valor sentinela aparece fora da entrada padrão do `docker secret create` e da exibição única dos valores gerados, e mensagens de erro citam só nomes e versões
```

#### AC-017 — Falhar com mensagem clara sem Docker ou fora do manager

**Cobre**: FR-001, FR-009, NFR-004

```gherkin
@FR-001 @FR-009 @NFR-004 @AC-017
Feature: Secrets de produção do Swarm

  Scenario: Falhar com mensagem clara sem Docker ou fora do manager
    Given o `docker` ausente do `PATH`, ou um nó que não é manager do Swarm
    When o operador executa qualquer subcomando
    Then o script termina com saída 2 e mensagem que diz o que falta (Docker ou manager), sem pedir valores e sem imprimir nada sensível
```

#### AC-018 — Documentar o uso, a guarda dos valores e as consequências

**Cobre**: FR-010, FR-001, NFR-004

```gherkin
@FR-010 @FR-001 @NFR-004 @AC-018
Feature: Secrets de produção do Swarm

  Scenario: Documentar o uso, a guarda dos valores e as consequências
    Given o repositório depois da entrega
    When os testes de documentação inspecionam `deploy/SECRETS.md`, `.specsfy/RULES.md` e a ajuda do script
    Then o guia cita cada subcomando, a guarda no gerenciador de senhas, a consequência da troca de `postgres_password` e de `conexoes_chave` e a convenção de nomes, e `deploy/secrets.sh --ajuda` lista os mesmos subcomandos
```

#### AC-019 — Verificar os secrets antes dos builds e só então fazer o deploy

**Cobre**: US-002, FR-005, FR-006, NFR-002

```gherkin
@US-002 @FR-005 @FR-006 @NFR-002 @AC-019
Feature: Secrets de produção do Swarm

  Scenario: Verificar os secrets antes dos builds e só então fazer o deploy
    Given todos os secrets existem no Swarm
    When o operador executa `deploy/build_and_deploy.sh` com um `docker` simulado que registra a ordem das chamadas
    Then a verificação ocorre antes dos dois `docker build`, o `docker stack deploy` vem por último, nada é criado nem alterado nos secrets, e um build que falha ainda impede o deploy
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve oferecer o script `deploy/secrets.sh` com os subcomandos `criar`, `trocar`, `verificar` e `resolver`, o parâmetro `--ambiente producao|local` (padrão produção) e `--ajuda`, e deve falhar com saída 2 e mensagem clara quando o `docker` não existir ou o nó não for manager do Swarm.
- **FR-002**: O subcomando `criar` deve pedir sem eco a chave da OpenRouter e os campos do `r2_credentials` (bucket, endpoint, access key e secret key), gerar `postgres_password` (32 caracteres alfanuméricos) e `conexoes_chave` (chave Fernet válida), exibir cada valor gerado uma única vez, e criar cada secret como `<nome>_v1` passando o valor somente pela entrada padrão do `docker secret create`.
- **FR-003**: O sistema deve nunca sobrescrever um secret: `criar` com nome explícito deve recusar um secret que já existe sem pedir valores, e `criar` sem nomes deve preservar os existentes e criar apenas os ausentes; entrada vazia ou inválida (por exemplo, endpoint sem `http` ou `https`) deve ser recusada antes de qualquer criação.
- **FR-004**: O subcomando `trocar <nome>` deve criar a versão seguinte (`_v<N+1>`) sem alterar nem remover a anterior; para `postgres_password` e `conexoes_chave` deve recusar a troca por padrão, mostrar a consequência e só prosseguir com `--confirmar-consequencia` e uma confirmação digitada, exibindo o procedimento manual antes de criar a nova versão; uma falha na criação deve deixar a versão anterior intacta e vigente.
- **FR-005**: O sistema deve resolver a versão mais alta de cada secret do ambiente escolhido: `resolver` imprime atribuições `VARIAVEL=nome_do_secret` (`OPENROUTER_API_KEY_SECRET`, `R2_CREDENTIALS_SECRET`, `POSTGRES_PASSWORD_SECRET`, `CONEXOES_CHAVE_SECRET`) e `verificar` falha listando os secrets ausentes e o comando de criação de cada um; nenhum dos dois imprime valores, e `resolver` só emite nomes que casam com o contrato de nomes, de modo que sua saída é segura para `eval`.
- **FR-006**: O `deploy/build_and_deploy.sh` deve executar a verificação antes de qualquer build e de `docker stack deploy`, abortar com saída diferente de 0 se algum secret faltar, e exportar as variáveis resolvidas ao ambiente do `docker stack deploy`.
- **FR-007**: O `deploy/stack.prod.yml` deve declarar cada secret como externo com `name:` vindo da variável resolvida e padrão `<nome>_v1`, remover `session_secret` (lista de secrets, comandos de serviço e bloco de secrets), manter o Postgres e a aplicação no mesmo mecanismo, e o `deploy/stack.local.yml` deve deixar de mapear secrets por nome fixo e manter apenas o volume de uploads do ensaio.
- **FR-008**: Com `--ambiente local`, o sistema deve criar e resolver os secrets com a convenção `<nome>_local_v<N>`, sem fazer nenhuma pergunta, usando chave da OpenRouter fictícia, um `r2_credentials` que não ativa o R2 (o backend grava uploads em disco) e valores gerados para a senha do Postgres e a chave Fernet.
- **FR-009**: O sistema deve nunca expor o valor de um secret em argumento de comando, histórico do shell, arquivo em disco, log, saída de erro ou stack file, citando em mensagens apenas nomes e versões; a única exceção é a exibição única, na criação ou troca, dos valores gerados.
- **FR-010**: O repositório deve documentar o uso, a convenção de nomes, a guarda dos valores no gerenciador de senhas e as consequências e o procedimento de troca de `postgres_password` e `conexoes_chave` em `deploy/SECRETS.md`, registrar as regras confirmadas em `.specsfy/RULES.md` e manter `deploy/secrets.sh --ajuda` consistente com o guia.

#### Não funcionais

- **NFR-001**: Nenhum valor de secret pode aparecer em argumentos de processo, histórico, arquivos, logs, saída de erro ou no stack, exceto na exibição única dos valores gerados. **Verificação**: Testes com `docker` simulado que registra argumentos e entrada padrão; busca de valores sentinela em argumentos, saídas e arquivos temporários.
- **NFR-002**: A criação é idempotente e segura: nunca sobrescreve, e uma falha ou interrupção não deixa a versão vigente alterada nem um secret parcial. **Verificação**: Testes que repetem `criar`, falham a criação da versão seguinte e confirmam que a anterior permanece e continua sendo a resolvida.
- **NFR-003**: O script depende apenas de bash, da CLI do Docker e de utilitários padrão do sistema (`openssl`, `tr`, `head`), e a chave gerada é aceita por Fernet. **Verificação**: Teste que valida a chave gerada com `cryptography.fernet.Fernet` e execução do script com `PATH` restrito a esses utilitários e ao `docker` simulado.
- **NFR-004**: As mensagens são acionáveis, em português do Brasil, e os códigos de saída são estáveis: 0 sucesso, 1 uso ou validação, 2 ambiente sem Docker ou sem manager, e diferente de 0 quando falta secret na verificação. **Verificação**: Testes que conferem o código de saída e o trecho da mensagem em cada falha prevista.

#### Erros e casos-limite

- Docker ausente ou nó que não é manager → saída 2, mensagem do que falta, sem perguntas e sem dados sensíveis.
- Secret explícito já existente em `criar` → recusa com saída 1 e orientação para usar `trocar`; nada é criado.
- Entrada vazia, chave Fernet malformada ou endpoint do R2 sem `http` ou `https` → recusa na validação, antes de criar o secret.
- Secret referenciado ausente na verificação do deploy → falha antes do build e do `stack deploy`, com a lista e o comando de criação.
- Falha ao criar a versão seguinte numa troca → saída diferente de 0; a versão anterior continua vigente e nada é removido.
- Troca de `postgres_password` ou `conexoes_chave` sem `--confirmar-consequencia`, ou com confirmação digitada errada → recusa sem criar nada.
- Terminal sem suporte a leitura sem eco (entrada não interativa) em produção → recusa pedindo execução interativa, sem aceitar valores por argumento.
- Versão mais alta ilegível no nome (nome fora do padrão `_v<N>`) → ignorada na resolução e apontada como aviso, sem aborto.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- `deploy/stack.prod.yml` (Compose 3.7) lista os secrets em uma âncora `x-application-secrets`, exporta cada um nos comandos de backend e worker e declara o bloco `secrets:` com `external: true`; o Postgres usa `postgres_password` por `POSTGRES_PASSWORD_FILE`.
- `deploy/build_and_deploy.sh` constrói as duas imagens e roda `docker stack deploy`; `deploy/stack.local.yml` sobrepõe o volume de uploads e o nome do secret da OpenRouter para o ensaio local.
- Os testes de deploy usam um `docker` falso no `PATH` (`tests/test_deploy_build_and_deploy_script.py`) e inspeção de YAML (`tests/test_deploy_stack.py`).

#### Arquitetura e módulos

- `deploy/secrets.sh` (bash, `set -euo pipefail`): despacha os subcomandos; consulta o Swarm por `docker secret ls --format '{{.Name}}'`; cria por `printf '%s' "$valor" | docker secret create "$nome" -`; lê entradas com `read -r -s`; gera a senha com `openssl rand -base64 64 | LC_ALL=C tr -dc 'A-Za-z0-9' | head -c 32` e a chave Fernet com `openssl rand -base64 32 | tr '+/' '-_'`.
- Convenção: produção `<nome>_v<N>`; local `<nome>_local_v<N>`. A versão vigente é a de maior `N` entre os nomes que seguem o padrão.
- `deploy/build_and_deploy.sh` chama `deploy/secrets.sh verificar` antes dos builds e `eval "$(deploy/secrets.sh resolver)"` para exportar as quatro variáveis ao `docker stack deploy`.
- Ponto de extensão: um novo secret entra numa lista única no script (nome, tipo de origem: pedido, gerado ou composto) e numa linha do stack.

#### Migrations

- Não aplicável: nenhuma mudança de banco ou schema.

#### Models

- Não aplicável: sem modelo persistente.

#### Controllers e casos de uso

- Não aplicável como HTTP. Os "casos de uso" são os subcomandos de `deploy/secrets.sh`: `criar [nome...] [--ambiente]`, `trocar <nome> [--confirmar-consequencia] [--ambiente]`, `verificar [--ambiente]`, `resolver [--ambiente]` e `--ajuda`.

#### Views e experiência

- Não aplicável: sem interface para pessoas. A experiência é a saída do terminal em português, com nomes e versões, perguntas sem eco e a exibição única dos valores gerados.

#### Queries e repositórios

- Não aplicável. A única consulta é a lista de nomes de secrets do Swarm.

#### Jobs e processamento assíncrono

- Não aplicável: execução manual e síncrona.

#### Estrutura de arquivos

```text
specs/in-progress/0027-provisionamento-de-secrets-do-swarm/
  spec.md
  research/
deploy/secrets.sh
deploy/build_and_deploy.sh
deploy/stack.prod.yml
deploy/stack.local.yml
deploy/SECRETS.md
tests/test_deploy_secrets_script.py
tests/test_deploy_build_and_deploy_script.py
tests/test_deploy_stack.py
.specsfy/RULES.md
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Secret do Swarm | Nome `<nome>_v<N>` ou `<nome>_local_v<N>` | Conteúdo imutável; `<nome>` em {`openrouter_api_key`, `r2_credentials`, `postgres_password`, `conexoes_chave`}; versão inteira crescente | Referenciado por serviços via `name:` resolvido por variável; nunca persistido no repositório |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Secret (nome lógico) | ausente | `criar` | `v1` vigente | Nunca sobrescreve; valor só pela entrada padrão |
| Secret (nome lógico) | `vN` vigente | `trocar` | `vN+1` vigente, `vN` preservada | Falha na criação mantém `vN` vigente |
| Secret (nome lógico) | `vN` vigente | `trocar` de `postgres_password` ou `conexoes_chave` sem confirmação | `vN` vigente | Recusa com consequência exibida |

#### Migração e retenção

- Não aplicável: nenhum dado do produto muda. As versões antigas de secrets permanecem no Swarm até remoção manual (fora de escopo). Não há produção implantada, então não há migração de nomes sem versão; o padrão `_v1` do stack cobre a primeira instalação.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega é uma ferramenta de linha de comando operada por Marcio no servidor, sem tela, rota ou componente; a experiência é o terminal.

#### Stack e convenções de interface

- Não aplicável.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável.

#### Menus e navegação principal

- Não aplicável: não há menu nem rota; a pessoa chega ao comportamento por `deploy/secrets.sh` e por `deploy/build_and_deploy.sh`.

#### Formulários e ações

- Não aplicável como formulário. As perguntas do terminal são: chave da OpenRouter, bucket, endpoint, access key e secret key do R2 (sem eco nos valores secretos) e a confirmação digitada nas trocas perigosas.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável: nenhum componente React é criado ou alterado.

#### Estados e acessibilidade

- Não aplicável a telas. No terminal: mensagens em português, códigos de saída estáveis e nenhuma dependência de cor para transmitir erro.

#### APIs expostas

- Interface de linha de comando de `deploy/secrets.sh`: `criar [nome...]`, `trocar <nome> [--confirmar-consequencia]`, `verificar`, `resolver`, `--ambiente producao|local`, `--ajuda`; saída 0 sucesso, 1 uso ou validação, 2 ambiente sem Docker ou sem manager, diferente de 0 quando `verificar` encontra ausência.
- `resolver` imprime `VARIAVEL=nome_do_secret` uma por linha, adequado a `eval`.

#### APIs externas utilizadas

- CLI do Docker Swarm: `docker secret ls`, `docker secret create <nome> -` e `docker info` (para confirmar manager). Autenticação é a do usuário local; sem timeout, retry ou fallback próprios: a falha do Docker interrompe o script com saída diferente de 0.

#### Documentação das APIs consultadas

- Nenhuma documentação externa foi consultada; os comandos do Docker acima são os já usados em `deploy/build_and_deploy.sh` e na SPEC-0022. A semântica de `name:` com interpolação em secrets externos foi comprovada na stack isolada da T020 (Docker 29.8.2).

#### Eventos e outros contratos

- Contrato de nomes: `^(openrouter_api_key|r2_credentials|postgres_password|conexoes_chave)(_local)?_v[0-9]+$`; contrato de variáveis: `OPENROUTER_API_KEY_SECRET`, `R2_CREDENTIALS_SECRET`, `POSTGRES_PASSWORD_SECRET`, `CONEXOES_CHAVE_SECRET`.

### 11. Estratégia TDD

- **Unidade**: Não aplicável como unidade isolada; as regras de nome, versão e validação são exercitadas pelo script inteiro.
- **Integração/contrato**: o script e o `build_and_deploy.sh` rodam com um `docker` falso no `PATH` que registra argumentos e entrada padrão e simula um Swarm em memória (lista de secrets); o YAML do stack e do override é inspecionado em testes de contrato.
- **BDD/aceite**: o Gherkin da seção 6 orienta o desenho dos testes; não há arquivos `.feature`.
- **Runner TDD**: Pytest (`uv run pytest`) e Ruff, como no restante do projeto.
- **E2E**: Não aplicável na suíte, porque o Swarm não existe nela. O ensaio local completo no Swarm real (secrets `_local`, `docker stack deploy` e serviços subindo) fica como validação manual do operador, fora do Delivery Gate (DEC-011).
- **Verificação manual**: a prova de `name:` com variável foi feita na T020 em uma stack isolada; o ensaio local completo e o primeiro uso no servidor real ficam com o operador, pelo mesmo motivo.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, NFR-001, NFR-003, NFR-004, AC-001 | AC-001 na seção 6 | Criar os secrets pela primeira vez em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 FR-001 FR-002 NFR-001 NFR-003 NFR-004 AC-001` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-001, FR-002, NFR-003, AC-002 | AC-002 na seção 6 | Gerar e exibir uma única vez os secrets internos em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 FR-002 NFR-003 AC-002` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-001, FR-001, FR-003, NFR-002, AC-003 | AC-003 na seção 6 | Recusar a criação explícita de um secret que já existe em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 FR-001 FR-003 NFR-002 AC-003` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-001, FR-002, FR-003, NFR-002, AC-004 | AC-004 na seção 6 | Completar somente os secrets ausentes em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 FR-002 FR-003 NFR-002 AC-004` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-001, FR-002, FR-003, FR-009, NFR-004, AC-005 | AC-005 na seção 6 | Recusar entrada vazia ou inválida sem criar nada em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 FR-002 FR-003 FR-009 NFR-004 AC-005` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-002, US-004, FR-005, FR-008, AC-006 | AC-006 na seção 6 | Resolver a versão mais alta de cada secret por ambiente em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-002 US-004 FR-005 FR-008 AC-006` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-002, FR-005, FR-006, NFR-004, AC-007 | AC-007 na seção 6 | Bloquear o deploy quando falta um secret em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-002 FR-005 FR-006 NFR-004 AC-007` | Observado em 2026-10-08: o deploy segue com saída 0 mesmo sem `conexoes_chave`: `build_and_deploy.sh` não verifica secrets | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-002, FR-005, FR-006, FR-007, AC-008 | AC-008 na seção 6 | Entregar a versão resolvida ao stack no deploy em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-002 FR-005 FR-006 FR-007 AC-008` | Observado em 2026-10-08: `docker stack deploy` não recebe `OPENROUTER_API_KEY_SECRET` nem as demais variáveis resolvidas | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-002, FR-007, AC-009 | AC-009 na seção 6 | Declarar o stack só com secrets externos versionados e sem `session_secret` em `tests/test_deploy_stack.py` com marcador próprio `SPECSFY: SPEC-0027 US-002 FR-007 AC-009` | Observado em 2026-10-08: `session_secret` ainda está no stack e os secrets externos não usam `name:` por variável | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-003, FR-004, FR-005, NFR-002, AC-010 | AC-010 na seção 6 | Trocar um secret criando a próxima versão em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-003 FR-004 FR-005 NFR-002 AC-010` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-003, FR-004, NFR-004, FR-010, AC-011 | AC-011 na seção 6 | Bloquear a troca de secret com efeito colateral por padrão em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-003 FR-004 NFR-004 FR-010 AC-011` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-003, FR-004, FR-010, NFR-001, AC-012 | AC-012 na seção 6 | Permitir a troca perigosa só com parâmetro e confirmação digitada em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-003 FR-004 FR-010 NFR-001 AC-012` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-003, FR-004, NFR-002, AC-013 | AC-013 na seção 6 | Manter a versão anterior quando a troca é interrompida em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-003 FR-004 NFR-002 AC-013` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-004, FR-008, NFR-003, AC-014 | AC-014 na seção 6 | Preparar o ensaio local com valores fictícios em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-004 FR-008 NFR-003 AC-014` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-004, FR-007, FR-008, AC-015 | AC-015 na seção 6 | Subir o ensaio local pelo mesmo mecanismo de versão em `tests/test_deploy_stack.py` com marcador próprio `SPECSFY: SPEC-0027 US-004 FR-007 FR-008 AC-015` | Observado em 2026-10-08: `deploy/stack.local.yml` ainda mapeia `openrouter_api_key_local` por nome fixo | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-001, US-003, FR-009, NFR-001, AC-016 | AC-016 na seção 6 | Nunca expor o valor de um secret em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 US-003 FR-009 NFR-001 AC-016` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| FR-001, FR-009, NFR-004, AC-017 | AC-017 na seção 6 | Falhar com mensagem clara sem Docker ou fora do manager em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 FR-001 FR-009 NFR-004 AC-017` | Observado em 2026-10-08: saída 127: `deploy/secrets.sh` ainda não existe | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| FR-010, FR-001, NFR-004, AC-018 | AC-018 na seção 6 | Documentar o uso, a guarda dos valores e as consequências em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 FR-010 FR-001 NFR-004 AC-018` | Observado em 2026-10-08: `deploy/SECRETS.md ainda não existe` (e `deploy/secrets.sh` ausente) | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |
| US-002, FR-005, FR-006, NFR-002, AC-019 | AC-019 na seção 6 | Verificar os secrets antes dos builds e só então fazer o deploy em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-002 FR-005 FR-006 NFR-002 AC-019` | Observado em 2026-10-08: a verificação não consulta o Swarm (nenhuma chamada `secret ls` antes dos builds) | GREEN em 2026-10-08: `uv run pytest -q`, 494 passed, 1 skipped (comparação paga da SPEC-0014 desabilitada: RUN_SPEC0014_REAL != 1) | Regressão completa Passed; casos desta spec sem skip |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-001 | AC-003 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-001 | AC-017 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-001 | AC-018 | Contrato | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-002 | AC-001 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-002 | AC-002 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-002 | AC-004 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-002 | AC-005 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-003 | AC-003 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-003 | AC-004 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-003 | AC-005 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-004 | AC-010 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-004 | AC-011 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-004 | AC-012 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-004 | AC-013 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-005 | AC-006 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-005 | AC-007 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-005 | AC-008 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-005 | AC-010 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-005 | AC-019 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-006 | AC-007 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-006 | AC-008 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-006 | AC-019 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-007 | AC-008 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-007 | AC-009 | Contrato | `tests/test_deploy_stack.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-007 | AC-015 | Contrato | `tests/test_deploy_stack.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-008 | AC-006 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-008 | AC-014 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-008 | AC-015 | Contrato | `tests/test_deploy_stack.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-009 | AC-005 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-009 | AC-016 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-009 | AC-017 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-010 | AC-011 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-010 | AC-012 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| FR-010 | AC-018 | Contrato | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-001 | AC-001 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-001 | AC-012 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-001 | AC-016 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-002 | AC-003 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-002 | AC-004 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-002 | AC-010 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-002 | AC-013 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-002 | AC-019 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-003 | AC-001 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-003 | AC-002 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-003 | AC-014 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-004 | AC-001 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-004 | AC-005 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-004 | AC-007 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-004 | AC-011 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-004 | AC-017 | Integração | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |
| NFR-004 | AC-018 | Contrato | `tests/test_deploy_secrets_script.py` | Passed em 2026-10-08: `uv run pytest -q` (494 passed); cenário e marcadores conferidos |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed em 2026-10-08
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/in-progress/0027-provisionamento-de-secrets-do-swarm/spec.md`
- **Achados**: 4 US, 10 FR, 4 NFR e 19 AC; cada US, FR e NFR coberto por no mínimo 3 AC; nenhum BLOCKER e nenhum P1. A DoD não precisa citar `.specsfy/STACK.md` nem `.specsfy/DATABASE.md` porque a entrega não muda stack nem persistência, e a evidência registra essa avaliação; `PROJECT.md` e `.specsfy/RULES.md` estão na DoD.
- **FIND-ARCH-001** [P2] [Resolved] A hipótese de `name:` com variável e padrão foi comprovada na T020 com Docker 29.8.2 e stack isolada — Refs: FR-007, AC-008, AC-009 — Evidence: deploy/stack.prod.yml:1 — Effect: o stack recebe a versão resolvida sem perder o destino lógico do secret — Suggestion: manter `name:`; o contorno de DEC-009 não foi necessário.
- **FIND-SEC-001** [P3] [Accepted] O deploy aplica `eval` à saída de `resolver` — Refs: FR-005, AC-006, AC-008 — Evidence: deploy/build_and_deploy.sh:1 — Effect: um nome de secret malicioso poderia injetar comando — Suggestion: `resolver` só emite nomes validados pelo contrato (FR-005, DEC-010); aceito.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed em 2026-10-08
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0027-provisionamento-de-secrets-do-swarm/spec.md`
- **Achados**: 30 tarefas (19 RED TDD, 6 de código, 3 de operação, 2 de documentação e 1 de fechamento), 180 itens de checklist e 37 de 37 IDs cobertos. As 19 tarefas RED (T001–T019) estão concluídas com RED válido observado e cada tarefa `[CODE]` depende de no mínimo 3 predecessores TDD. Não há fase de interface porque a entrega não tem interface para pessoas. A prova da hipótese de `name:` com variável (T020) precede o código que depende dela. Replanejado em 2026-10-08: a tarefa T029 (ensaio local completo no Swarm real) foi removida do plano por decisão do operador (DEC-011), sem alterar requisitos nem cenários; o plano passou a ter 29 tarefas.

#### Gate do Ato III — Entrega

- **Resultado**: Passed em 2026-10-08.
- **Comandos**: `uv run ruff check`; `uv run pytest -q`; `npm --prefix frontend run test:tdd`, `lint`, `typecheck` e `build`; `check_traceability.mjs <spec> . --kinds US,FR,NFR,AC --full-chain`; `verify_acceptance.mjs <spec> .`; `verify_evidence.mjs <spec> .`; `review_findings.mjs <spec> --root .`; `verify_repo.mjs . --boundary local --timeout-seconds 300 --max-output-bytes 65536`; `build_documentation.mjs --project .` e `--check`; `monitor_context.mjs --project . --check`. `<spec>` é esta fonte normativa no estado em que cada verificação ocorreu; caminhos completos constam nos comentários de evidência das tarefas.
- **Achados**: Ruff Passed; Python 494 passed, 1 skipped (comparação paga opt-in da SPEC-0014, `RUN_SPEC0014_REAL != 1`), 2 avisos preexistentes de depreciação; nenhum caso desta spec pulado. Frontend 219 passed em 53 arquivos, lint/tipos/build Passed. 37/37 IDs rastreados, cada US/FR/NFR com ao menos 3 casos TDD e todos os 19 AC com Passed na matriz. 29/29 tarefas e 174/174 itens concluídos. Evidências strict Passed; findings sem P1 Open. T020 comprovou `name:` com variável no Docker 29.8.2. Documentação reconstruída e check Passed, monitor CURRENT. Sem mudança de produção nesta tarefa; sem impacto adicional em stack, persistência ou regras. Ensaio local completo e primeiro uso em produção seguem com o operador (DEC-011), fora do Delivery Gate.

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

Um caso por `AC`, cada um com marcador `SPECSFY:` próprio. Os casos de um mesmo arquivo de teste não usam `[P]`.

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-001, FR-001, FR-002, NFR-001, NFR-003, NFR-004, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na seção 6 (Criar os secrets pela primeira vez), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-001 FR-001 FR-002 NFR-001 NFR-003 NFR-004 AC-001`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-001, FR-002, NFR-001, NFR-003, NFR-004, AC-001 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-001 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-001, FR-002, NFR-003, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na seção 6 (Gerar e exibir uma única vez os secrets internos), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-001 FR-002 NFR-003 AC-002`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-002, NFR-003, AC-002 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-002 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-001, FR-001, FR-003, NFR-002, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na seção 6 (Recusar a criação explícita de um secret que já existe), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-001 FR-001 FR-003 NFR-002 AC-003`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-001, FR-003, NFR-002, AC-003 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-003 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-001, FR-002, FR-003, NFR-002, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na seção 6 (Completar somente os secrets ausentes), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-001 FR-002 FR-003 NFR-002 AC-004`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-002, FR-003, NFR-002, AC-004 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-004 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-001, FR-002, FR-003, FR-009, NFR-004, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na seção 6 (Recusar entrada vazia ou inválida sem criar nada), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-001 FR-002 FR-003 FR-009 NFR-004 AC-005`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-002, FR-003, FR-009, NFR-004, AC-005 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-005 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-002, US-004, FR-005, FR-008, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na seção 6 (Resolver a versão mais alta de cada secret por ambiente), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-002 US-004 FR-005 FR-008 AC-006`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, US-004, FR-005, FR-008, AC-006 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-006 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-002, FR-005, FR-006, NFR-004, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na seção 6 (Bloquear o deploy quando falta um secret), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-002 FR-005 FR-006 NFR-004 AC-007`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q`, causa: o deploy segue com saída 0 mesmo sem `conexoes_chave`: `build_and_deploy.sh` não verifica secrets.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-005, FR-006, NFR-004, AC-007 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falhou por comportamento ausente; linha AC-007 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-002, FR-005, FR-006, FR-007, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na seção 6 (Entregar a versão resolvida ao stack no deploy), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-002 FR-005 FR-006 FR-007 AC-008`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q`, causa: `docker stack deploy` não recebe `OPENROUTER_API_KEY_SECRET` nem as demais variáveis resolvidas.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-005, FR-006, FR-007, AC-008 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falhou por comportamento ausente; linha AC-008 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 um caso TDD falhando em tests/test_deploy_stack.py — Refs: US-002, FR-007, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na seção 6 (Declarar o stack só com secrets externos versionados e sem `session_secret`), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de contrato do YAML em tests/test_deploy_stack.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-002 FR-007 AC-009`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_stack.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_stack.py -q`, causa: `session_secret` ainda está no stack e os secrets externos não usam `name:` por variável.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-007, AC-009 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_stack.py -q` falhou por comportamento ausente; linha AC-009 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-010 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-003, FR-004, FR-005, NFR-002, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 na seção 6 (Trocar um secret criando a próxima versão), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-003 FR-004 FR-005 NFR-002 AC-010`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-004, FR-005, NFR-002, AC-010 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-010 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-003, FR-004, NFR-004, FR-010, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 na seção 6 (Bloquear a troca de secret com efeito colateral por padrão), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-003 FR-004 NFR-004 FR-010 AC-011`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-004, NFR-004, FR-010, AC-011 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-011 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-003, FR-004, FR-010, NFR-001, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012 na seção 6 (Permitir a troca perigosa só com parâmetro e confirmação digitada), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-003 FR-004 FR-010 NFR-001 AC-012`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-004, FR-010, NFR-001, AC-012 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-012 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-013 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-003, FR-004, NFR-002, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-013 na seção 6 (Manter a versão anterior quando a troca é interrompida), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-003 FR-004 NFR-002 AC-013`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-004, NFR-002, AC-013 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-013 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T014 [TEST] [TDD] [US-004] Derivar do AC-014 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-004, FR-008, NFR-003, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-014 na seção 6 (Preparar o ensaio local com valores fictícios), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-004 FR-008 NFR-003 AC-014`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-004, FR-008, NFR-003, AC-014 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-014 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T015 [TEST] [TDD] [US-004] Derivar do AC-015 um caso TDD falhando em tests/test_deploy_stack.py — Refs: US-004, FR-007, FR-008, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-015 na seção 6 (Subir o ensaio local pelo mesmo mecanismo de versão), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de contrato do YAML em tests/test_deploy_stack.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-004 FR-007 FR-008 AC-015`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_stack.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_stack.py -q`, causa: `deploy/stack.local.yml` ainda mapeia `openrouter_api_key_local` por nome fixo.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-004, FR-007, FR-008, AC-015 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_stack.py -q` falhou por comportamento ausente; linha AC-015 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T016 [TEST] [TDD] [US-001] Derivar do AC-016 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-001, US-003, FR-009, NFR-001, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-016 na seção 6 (Nunca expor o valor de um secret), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-001 US-003 FR-009 NFR-001 AC-016`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, US-003, FR-009, NFR-001, AC-016 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-016 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T017 [TEST] [TDD] Derivar do AC-017 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: FR-001, FR-009, NFR-004, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-017 na seção 6 (Falhar com mensagem clara sem Docker ou fora do manager), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 FR-001 FR-009 NFR-004 AC-017`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: saída 127: `deploy/secrets.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs FR-001, FR-009, NFR-004, AC-017 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-017 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T018 [TEST] [TDD] Derivar do AC-018 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: FR-010, FR-001, NFR-004, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-018 na seção 6 (Documentar o uso, a guarda dos valores e as consequências), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 FR-010 FR-001 NFR-004 AC-018`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_secrets_script.py -q`, causa: `deploy/SECRETS.md ainda não existe` (e `deploy/secrets.sh` ausente).
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs FR-010, FR-001, NFR-004, AC-018 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_secrets_script.py -q` falhou por comportamento ausente; linha AC-018 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T019 [TEST] [TDD] [US-002] Derivar do AC-019 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-002, FR-005, FR-006, NFR-002, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-019 na seção 6 (Verificar os secrets antes dos builds e só então fazer o deploy), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing` mesmo nos testes de deploy.
  - [x] **EXECUTE**: Escrever o teste de integração com `docker` simulado no `PATH` em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0027 US-002 FR-005 FR-006 NFR-002 AC-019`, reaproveitando o `docker` falso de `tests/test_deploy_build_and_deploy_script.py` e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, variável ou subcomando ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-08: RED válido com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q`, causa: a verificação não consulta o Swarm (nenhuma chamada `secret ls` antes dos builds).
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-005, FR-006, NFR-002, AC-019 nas seções 11–13. Registrado: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falhou por comportamento ausente; linha AC-019 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

#### Fase 2 — Prova da hipótese do stack

**Objetivo**: confirmar `name:` com variável e padrão em secrets externos antes de escrever código que dependa disso.
**Teste independente**: ensaio no Swarm local com e sem a variável, referenciando `prova_v1` e `prova_v2`.

- [x] T020 [OPS] Provar no ensaio local do Swarm que um secret externo aceita `name:` com variável e padrão em `deploy/stack.prod.yml` — Refs: FR-007, AC-008, AC-009 — Depends: none
  - [x] **PREP**: Ler DEC-009 e o risco da hipótese na seção 16; confirmar se `docker` com Swarm local está disponível e registrar a versão do Docker. Resultado: Docker 29.8.2 com Swarm ativo de um nó (`developer-oracle`), com a stack `rag-pipeline` e secrets do ensaio da SPEC-0022 em uso; esses recursos não foram tocados.
  - [x] **EXECUTE**: Montar um arquivo Compose mínimo em diretório temporário com um secret externo `name: ${PROVA_SECRET:-prova_v1}`, criar `prova_v2` no Swarm local e rodar `docker stack deploy` com e sem a variável; registrar o resultado e remover os recursos de prova. Resultado em 2026-10-08: stack própria `prova0027` (1 serviço `postgres:16-alpine` com `sleep 600`), secrets fictícios `prova0027_v1` e `prova0027_v2` e `docker stack deploy --resolve-image never` com e sem `PROVA_SECRET`.
  - [x] **VERIFY**: Confirmar que, sem a variável, o serviço referencia `prova_v1` e, com `PROVA_SECRET=prova_v2`, referencia `prova_v2` (via `docker service inspect`). Se falhar, registrar a falha e aplicar o contorno de DEC-009 (substituição de texto no arquivo do stack) antes das tarefas de código. Resultado em 2026-10-08: sem a variável o serviço referencia `prova0027_v1`; com `PROVA_SECRET=prova0027_v2` referencia `prova0027_v2`; o arquivo montado mantém o nome lógico `chave` (`/run/secrets/chave`). O contorno de DEC-009 não é necessário.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera script, arquivo de deploy ou documentação de terminal, sem superfície visual. Verificado: tarefa de operação sem superfície visual.
  - [x] **EVIDENCE**: Docker 29.8.2. A execução já registrada em PREP/EXECUTE/VERIFY usou `docker stack deploy --resolve-image never` na stack isolada `prova0027`, sem e com `PROVA_SECRET=prova0027_v2`, e `docker service inspect` confirmou respectivamente `prova0027_v1` e `prova0027_v2`, preservando o destino lógico `/run/secrets/chave`. FR-007, AC-008 e AC-009 comprovados; mecanismo `name:` confirmado, sem contorno de DEC-009. Versão reconferida em 2026-10-08 com `docker version --format` (somente versão).
  - [x] **IMPROVE**: Resultado consolidado na seção 16; nenhuma melhoria adicional necessária: a prova isolada confirmou o mecanismo e evitou tocar a stack da aplicação. DEC-009 permanece sem contorno.

#### Fase 3 — Script de secrets (US-001, US-003 e US-004)

**Objetivo**: `deploy/secrets.sh` com `verificar`, `resolver`, `criar` e `trocar` e o ambiente local.
**Teste independente**: `uv run pytest tests/test_deploy_secrets_script.py -q` verde com o `docker` simulado.

- [x] T021 [CODE] [US-002] Criar o esqueleto de `deploy/secrets.sh` com despacho de subcomandos, `--ajuda`, checagem de Docker e manager, ambiente e os subcomandos `verificar` e `resolver` — Refs: US-002, US-004, FR-001, FR-005, NFR-004, AC-006, AC-017 — Depends: T006, T007, T017
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Confirmar o contrato de nomes `^(openrouter_api_key|r2_credentials|postgres_password|conexoes_chave)(_local)?_v[0-9]+$` e a convenção de saídas 0, 1 e 2. Resultado: docs/ reconstruídos; contrato de nomes e saídas 0, 1 e 2 confirmados; T021 deixou de depender da T020 porque a hipótese já está provada (registrado no plano).
  - [x] **EXECUTE**: Criar `deploy/secrets.sh` (bash, `set -euo pipefail`, executável) que lista os secrets por `docker secret ls`, confirma manager por `docker info`, resolve a maior versão por nome e ambiente, imprime `VARIAVEL=nome` só para nomes que casam com o contrato (`resolver`) e falha listando os ausentes com o comando de criação (`verificar`). Resultado: Criado `deploy/secrets.sh` (bash, `set -euo pipefail`, executável): despacho de `criar`, `trocar`, `verificar` e `resolver`, `--ajuda`, `--ambiente`, checagem de Docker e manager por `docker info`, listagem por `docker secret ls`, versão mais alta por nome e ambiente; `resolver` só emite nomes montados da lista fixa e de números; `verificar` lista os ausentes com o comando de criação.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_deploy_secrets_script.py tests/test_deploy_build_and_deploy_script.py tests/test_deploy_stack.py -q` nos casos de AC-006, AC-007 (parte da verificação) e AC-017 e `uv run ruff check`; confirmar saída 2 sem Docker ou fora do manager. Resultado: `uv run pytest tests/test_deploy_secrets_script.py -q` (sem o caso do guia, da T027) → 13 passed, incluindo AC-006 e AC-017; `bash -n` e `uv run ruff check` sem erros; `shellcheck` não está instalado neste ambiente.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera script, arquivo de deploy ou documentação de terminal, sem superfície visual. Resultado: `Não aplicável`: a tarefa só altera um script de terminal, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN dos casos de resolução e de ambiente, e que nenhuma saída contém valor de secret. Resultado: GREEN de AC-006 (resolução por ambiente) e AC-017 (sem Docker e fora do manager, saída 2) e da parte do deploy que o script serve (FR-001, FR-005, NFR-004, US-002, US-004). Monitor `CURRENT` com `--acknowledge-project-no-change`: o `PROJECT.md` é revisado na T028.
  - [x] **IMPROVE**: Aplicar a melhoria de uma única lista de secrets (nome, origem e variável) reutilizada por todos os subcomandos ou justificar nenhuma. Resultado: Melhoria aplicada: uma lista fixa de secrets e uma função de variável reutilizadas por todos os subcomandos, para a resolução nunca emitir nome fora do contrato (DEC-010).
  <!-- specsfy:evidence {"task": "T021", "refs": ["US-002", "US-004", "FR-001", "FR-005", "NFR-004", "AC-006", "AC-017"], "files": ["deploy/secrets.sh", "tests/test_deploy_secrets_script.py", "tests/_docker_falso.py"], "commands": [{"run": "uv run pytest tests/test_deploy_secrets_script.py -q --deselect tests/test_deploy_secrets_script.py::test_documentacao_e_ajuda_listam_os_mesmos_subcomandos", "exit": 0}, {"run": "uv run ruff check", "exit": 0}]} -->

- [x] T022 [CODE] [US-001] Implementar o subcomando `criar` em `deploy/secrets.sh` com leitura sem eco, geração de `postgres_password` e `conexoes_chave`, validação e recusa de sobrescrita — Refs: US-001, FR-002, FR-003, FR-009, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-016 — Depends: T001, T002, T003, T004, T005, T016, T021
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Confirmar que `openssl` e `tr` estão disponíveis e como o `docker secret create <nome> -` recebe o valor pela entrada padrão. Resultado: docs/ reconstruídos; `openssl` e `tr` confirmados; `docker secret create <nome> -` recebe o valor pela entrada padrão; decisão registrada na spec: `--entrada-padrao` aceita os valores por linhas para automação e testes.
  - [x] **EXECUTE**: Implementar `criar [nome...]`: `read -r -s` para a chave da OpenRouter e para o `r2_credentials` (monta as atribuições a partir de bucket, endpoint, access key e secret key), geração da senha de 32 caracteres alfanuméricos e da chave Fernet (`openssl rand -base64 32` com `+/` trocado por `-_`), exibição única dos valores gerados, validação de entrada vazia e de endpoint sem `http` ou `https`, criação como `<nome>_v1` por entrada padrão, recusa de nome explícito existente e preservação dos existentes quando sem nomes. Resultado: `criar [nome...]` em `deploy/secrets.sh`: leitura sem eco (`read -r -s`) da chave da OpenRouter e dos quatro campos do R2, montagem do arquivo de atribuições com citação segura, geração da senha de 32 caracteres alfanuméricos e da chave Fernet, exibição única dos valores gerados, validação de tudo antes de criar qualquer secret, criação como `<nome>_v1` pela entrada padrão, recusa de nome explícito existente e preservação dos existentes quando sem nomes.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_deploy_secrets_script.py tests/test_deploy_build_and_deploy_script.py tests/test_deploy_stack.py -q` nos casos de AC-001 a AC-005 e AC-016, validar a chave gerada com `cryptography.fernet.Fernet` e rodar `uv run ruff check`. Resultado: `uv run pytest tests/test_deploy_secrets_script.py -q` (sem o caso do guia) → 13 passed, incluindo AC-001 a AC-005 e AC-016; a chave gerada é aceita por `cryptography.fernet.Fernet` e a varredura de valores sentinela em argumentos, saídas e arquivos temporários não encontra nada; `uv run ruff check` sem erros. Uma mensagem foi ajustada ("preservado") porque o teste a exige.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera script, arquivo de deploy ou documentação de terminal, sem superfície visual. Resultado: `Não aplicável`: a tarefa só altera um script de terminal, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN dos seis cenários e a varredura de valores sentinela em argumentos, saídas e arquivos temporários. Resultado: GREEN dos seis cenários de criação e de ausência de valor fora da exibição única (US-001, FR-002, FR-003, FR-009, NFR-001, NFR-002, NFR-003).
  - [x] **IMPROVE**: Aplicar a melhoria de validar todas as entradas antes da primeira criação ou justificar nenhuma. Resultado: Melhoria aplicada: todas as entradas são lidas e validadas antes da primeira criação, então uma entrada inválida nunca deixa secret parcial.
  <!-- specsfy:evidence {"task": "T022", "refs": ["US-001", "FR-002", "FR-003", "FR-009", "NFR-001", "NFR-002", "NFR-003", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-016"], "files": ["deploy/secrets.sh"], "commands": [{"run": "uv run pytest tests/test_deploy_secrets_script.py -q --deselect tests/test_deploy_secrets_script.py::test_documentacao_e_ajuda_listam_os_mesmos_subcomandos", "exit": 0}, {"run": "uv run ruff check", "exit": 0}]} -->

- [x] T023 [CODE] [US-003] Implementar o subcomando `trocar` em `deploy/secrets.sh` com nova versão, bloqueio de `postgres_password` e `conexoes_chave` e confirmação digitada — Refs: US-003, FR-004, FR-009, FR-010, NFR-001, NFR-002, NFR-004, AC-010, AC-011, AC-012, AC-013, AC-016 — Depends: T010, T011, T012, T013, T016, T022
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Reler DEC-004 e o texto de consequência de cada secret (Postgres: alterar a senha no banco antes; conexões: recadastrar as chaves). Resultado: docs/ reconstruídos; DEC-004 e os textos de consequência de `postgres_password` (alterar a senha no banco) e `conexoes_chave` (recadastrar as conexões) relidos.
  - [x] **EXECUTE**: Implementar `trocar <nome>`: cria `_v<N+1>` sem alterar a anterior; para `postgres_password` e `conexoes_chave` recusa sem `--confirmar-consequencia`, mostra a consequência, exige a confirmação digitada, exibe o procedimento manual e só então cria e exibe o novo valor uma única vez; falha na criação preserva a versão vigente e não remove nada. Resultado: `trocar <nome>` em `deploy/secrets.sh`: cria a versão seguinte sem alterar nem remover a anterior; `postgres_password` e `conexoes_chave` são recusados sem `--confirmar-consequencia` (a consequência é exibida), com o parâmetro exigem digitar o nome do secret, exibem o procedimento e só então criam e mostram o novo valor uma única vez; falha na criação informa que a versão anterior continua vigente, sai com erro e não remove nada.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_deploy_secrets_script.py tests/test_deploy_build_and_deploy_script.py tests/test_deploy_stack.py -q` nos casos de AC-010 a AC-013 e AC-016 e `uv run ruff check`; confirmar que a resolução seguinte a uma falha continua apontando para a versão anterior. Resultado: `uv run pytest tests/test_deploy_secrets_script.py -q` (sem o caso do guia) → 13 passed, incluindo AC-010 a AC-013; a resolução seguinte a uma falha continua apontando para a versão anterior; `uv run ruff check` sem erros.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera script, arquivo de deploy ou documentação de terminal, sem superfície visual. Resultado: `Não aplicável`: a tarefa só altera um script de terminal, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN dos cinco cenários de troca e de ausência de valores fora da exibição única. Resultado: GREEN dos quatro cenários de troca (US-003, FR-004, FR-009, FR-010, NFR-001, NFR-002, NFR-004).
  - [x] **IMPROVE**: Aplicar a melhoria de centralizar os textos de consequência para a ajuda, o bloqueio e o guia usarem a mesma redação ou justificar nenhuma. Resultado: Melhoria aplicada: a consequência é uma função única, usada tanto no bloqueio quanto na confirmação, e o guia da T027 reutiliza a mesma redação.
  <!-- specsfy:evidence {"task": "T023", "refs": ["US-003", "FR-004", "FR-009", "FR-010", "NFR-001", "NFR-002", "NFR-004", "AC-010", "AC-011", "AC-012", "AC-013", "AC-016"], "files": ["deploy/secrets.sh"], "commands": [{"run": "uv run pytest tests/test_deploy_secrets_script.py -q --deselect tests/test_deploy_secrets_script.py::test_documentacao_e_ajuda_listam_os_mesmos_subcomandos", "exit": 0}, {"run": "uv run ruff check", "exit": 0}]} -->

- [x] T024 [CODE] [US-004] Implementar `--ambiente local` em `deploy/secrets.sh` para criar e resolver os secrets `<nome>_local_v<N>` sem perguntas e com valores fictícios — Refs: US-004, FR-008, NFR-003, AC-006, AC-014, AC-015 — Depends: T006, T014, T015, T022
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Confirmar que o `r2_credentials` local não pode ativar o R2 (o backend grava uploads em disco) e o formato de atribuições lido por `. /run/secrets/r2_credentials`. Resultado: docs/ reconstruídos; confirmado que o `r2_credentials` local não pode ativar o R2 (o backend grava uploads em disco) e que o arquivo é lido por `. /run/secrets/r2_credentials`.
  - [x] **EXECUTE**: Acrescentar o ambiente local a `criar` e `resolver`: sufixo `_local`, chave da OpenRouter fictícia, `r2_credentials` sem variáveis ativas, senha e chave Fernet geradas, nenhuma pergunta e nenhuma exibição de valor desnecessária. Resultado: `--ambiente local` em `criar`, `trocar`, `verificar` e `resolver`: sufixo `_local`, chave da OpenRouter fictícia, `r2_credentials` só com comentário (nenhuma variável ativa), senha e chave Fernet geradas, nenhuma pergunta e nenhuma exibição dos valores gerados.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_deploy_secrets_script.py tests/test_deploy_build_and_deploy_script.py tests/test_deploy_stack.py -q` nos casos de AC-006 e AC-014 e `uv run ruff check`. Resultado: `uv run pytest tests/test_deploy_secrets_script.py -q` (sem o caso do guia) → 13 passed, incluindo AC-006 e AC-014; `resolver --ambiente local` nunca devolve nomes de produção; `uv run ruff check` sem erros.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera script, arquivo de deploy ou documentação de terminal, sem superfície visual. Resultado: `Não aplicável`: a tarefa só altera um script de terminal, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN e que `resolver --ambiente local` nunca devolve nomes de produção. Resultado: GREEN de AC-014 e da resolução local de AC-006 (US-004, FR-008, NFR-003). O ensaio completo no Swarm real fica com o operador antes do primeiro deploy em produção (DEC-011); T029 foi removida do plano.
  - [x] **IMPROVE**: Aplicar a melhoria de reaproveitar a mesma rotina de criação para os dois ambientes ou justificar nenhuma. Resultado: Melhoria aplicada: a mesma rotina de criação serve aos dois ambientes; só a obtenção dos valores muda.
  <!-- specsfy:evidence {"task": "T024", "refs": ["US-004", "FR-008", "NFR-003", "AC-006", "AC-014", "AC-015"], "files": ["deploy/secrets.sh"], "commands": [{"run": "uv run pytest tests/test_deploy_secrets_script.py -q --deselect tests/test_deploy_secrets_script.py::test_documentacao_e_ajuda_listam_os_mesmos_subcomandos", "exit": 0}, {"run": "uv run ruff check", "exit": 0}]} -->

**Checkpoint**: criar, trocar, verificar e resolver funcionam com o `docker` simulado e nenhum valor aparece fora da exibição única.

#### Fase 4 — Stack e deploy (US-002)

**Objetivo**: stack com secrets versionados por variável, sem `session_secret`, e deploy que verifica antes de construir.
**Teste independente**: `uv run pytest tests/test_deploy_stack.py tests/test_deploy_build_and_deploy_script.py -q` verde.

- [x] T025 [P] [CODE] [US-002] Declarar os secrets com `name:` por variável e padrão `_v1` e remover `session_secret` em `deploy/stack.prod.yml`, simplificar `deploy/stack.local.yml` e atualizar `tests/test_deploy_stack.py` — Refs: US-002, US-004, FR-007, AC-008, AC-009, AC-015 — Depends: T008, T009, T015
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Reler o resultado de T020 (mecanismo `name:` ou contorno de DEC-009) e os testes atuais de `tests/test_deploy_stack.py`. Resultado: docs/ reconstruídos; resultado da T020 relido (o mecanismo `name:` com variável e padrão funciona no Docker 29.8.2, sem contorno de DEC-009).
  - [x] **EXECUTE**: Em `deploy/stack.prod.yml`: cada secret externo com `name: ${VARIAVEL:-<nome>_v1}`, remoção de `session_secret` da âncora, dos comandos de backend e worker e do bloco de secrets; em `deploy/stack.local.yml`: remover o mapeamento fixo do secret da OpenRouter e manter o volume de uploads; em `tests/test_deploy_stack.py`: ajustar `SECRETS_DE_PRODUCAO` e acrescentar as asserções de nome por variável e de ausência de `session_secret`. Resultado: `deploy/stack.prod.yml`: os quatro secrets externos usam `name: ${VARIAVEL_SECRET:-<nome>_v1}`, `session_secret` saiu da âncora de secrets, dos comandos de backend e worker e do bloco de secrets, com comentário da convenção; `deploy/stack.local.yml`: removido o mapeamento fixo `openrouter_api_key_local`, mantido o volume de uploads e um comentário sobre o mecanismo; `tests/test_deploy_stack.py`: `session_secret` saiu de `SECRETS_DE_PRODUCAO`.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_deploy_stack.py -q`, `uv run ruff check` e o `docker stack config` (ou equivalente) para confirmar que o YAML resolve com e sem as variáveis. Resultado: `uv run pytest tests/test_deploy_stack.py -q` → verde, incluindo AC-009 e AC-015 e os testes antigos do stack; `docker stack config` resolve `*_v1` por padrão e `*_local_v1` com as variáveis e o override local, e não contém `session_secret`; `uv run ruff check` sem erros.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera script, arquivo de deploy ou documentação de terminal, sem superfície visual. Resultado: `Não aplicável`: a tarefa só altera arquivos de stack e teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN de AC-009 e AC-015 e o diff dos dois arquivos de stack sem valores de secrets. Resultado: GREEN de AC-009 e AC-015 (US-002, US-004, FR-007). Os 3 casos do `build_and_deploy.sh` continuam RED até a T026. Monitor `CURRENT` com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: Aplicar a melhoria de um comentário no stack explicando a convenção de nomes ou justificar nenhuma. Resultado: Melhoria aplicada: comentário no stack explicando a convenção `<nome>_v<N>` e as variáveis `*_SECRET`, para quem ler o arquivo entender de onde vem o nome.
  <!-- specsfy:evidence {"task": "T025", "refs": ["US-002", "US-004", "FR-007", "AC-008", "AC-009", "AC-015"], "files": ["deploy/stack.prod.yml", "deploy/stack.local.yml", "tests/test_deploy_stack.py"], "commands": [{"run": "uv run pytest tests/test_deploy_stack.py -q", "exit": 0}, {"run": "uv run ruff check", "exit": 0}]} -->

- [x] T026 [CODE] [US-002] Fazer `deploy/build_and_deploy.sh` executar `verificar` antes dos builds e exportar as variáveis de `resolver` ao `docker stack deploy` — Refs: US-002, FR-005, FR-006, NFR-002, NFR-004, AC-007, AC-008, AC-019 — Depends: T007, T008, T019, T021
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Reler `tests/test_deploy_build_and_deploy_script.py` e a regra de que um build que falha impede o deploy. Resultado: docs/ reconstruídos; `tests/test_deploy_build_and_deploy_script.py` e a regra de que um build que falha impede o deploy relidos.
  - [x] **EXECUTE**: Inserir a verificação antes do primeiro `docker build`, abortar com a lista de ausentes e o comando de criação, consumir `resolver` por `eval` (seguro por DEC-010) e exportar as quatro variáveis antes do `docker stack deploy`; aceitar o ambiente local sem alterar o fluxo de produção. Resultado: `deploy/build_and_deploy.sh`: antes do primeiro `docker build` chama `deploy/secrets.sh verificar` (aborta com a lista de ausentes e o comando de criação), consome `deploy/secrets.sh resolver` por `eval` (seguro por DEC-010) e exporta `OPENROUTER_API_KEY_SECRET`, `R2_CREDENTIALS_SECRET`, `CONEXOES_CHAVE_SECRET` e `POSTGRES_PASSWORD_SECRET` ao `docker stack deploy`. O teste antigo do build que falha passou a simular os quatro secrets presentes, senão ele passaria a falhar na verificação e deixaria de provar que o build falho impede o deploy.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_deploy_secrets_script.py tests/test_deploy_build_and_deploy_script.py tests/test_deploy_stack.py -q` nos casos de AC-007, AC-008 e AC-019, incluindo o teste existente de build falho, e `uv run ruff check`. Resultado: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` → 4 passed, incluindo AC-007, AC-008 e AC-019 e o teste de build falho; `bash -n` e `uv run ruff check` sem erros.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera script, arquivo de deploy ou documentação de terminal, sem superfície visual. Resultado: `Não aplicável`: a tarefa só altera um script de deploy, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN e a ordem das chamadas registrada pelo `docker` falso (verificação, builds, deploy). Resultado: GREEN de AC-007, AC-008 e AC-019 e a ordem das chamadas registrada pelo `docker` falso (verificação, builds, deploy; nenhum `secret create`) (US-002, FR-005, FR-006, NFR-002, NFR-004). Monitor `CURRENT` com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: Aplicar a melhoria de uma mensagem única que lista todos os ausentes de uma vez ou justificar nenhuma. Resultado: Melhoria aplicada: comentário curto no script explicando por que o `eval` é seguro, para quem o revisar não precisar reconstituir a DEC-010.
  <!-- specsfy:evidence {"task": "T026", "refs": ["US-002", "FR-005", "FR-006", "NFR-002", "NFR-004", "AC-007", "AC-008", "AC-019"], "files": ["deploy/build_and_deploy.sh", "tests/test_deploy_build_and_deploy_script.py"], "commands": [{"run": "uv run pytest tests/test_deploy_build_and_deploy_script.py -q", "exit": 0}, {"run": "uv run ruff check", "exit": 0}]} -->

**Checkpoint**: o deploy recusa um secret ausente antes dos builds e entrega as variáveis resolvidas ao stack.

#### Fase 5 — Documentação e regras

- [x] T027 [DOC] Escrever `deploy/SECRETS.md` com uso, convenção de nomes, guarda dos valores e procedimentos de troca, e alinhar `deploy/secrets.sh --ajuda` — Refs: US-003, FR-001, FR-010, NFR-004, AC-011, AC-018 — Depends: T018, T023
  - [x] **PREP**: Reler as decisões DEC-001 a DEC-010 e o texto de consequência já usado pelo script. Resultado: Decisões DEC-001 a DEC-010 relidas e os textos de consequência já usados pelo script reaproveitados.
  - [x] **EXECUTE**: Criar `deploy/SECRETS.md` com cada subcomando e parâmetro, a convenção `<nome>_v<N>` e `<nome>_local_v<N>`, a guarda dos valores no gerenciador de senhas, as consequências e o procedimento manual de `postgres_password` e `conexoes_chave`, o ensaio local e os limites (sem inventário, sem rotação automática); conferir que `--ajuda` lista os mesmos subcomandos. Resultado: Criado `deploy/SECRETS.md`: tabela dos quatro secrets, convenção `<nome>_v<N>` e `<nome>_local_v<N>`, primeira instalação, conferência (`verificar` e `resolver`), troca versionada, trocas com efeito colateral com o procedimento de `ALTER USER` do Postgres e o recadastro das conexões, ensaio local, `--entrada-padrao`, códigos de saída e limites; `--ajuda` já lista os mesmos subcomandos.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_deploy_secrets_script.py tests/test_deploy_build_and_deploy_script.py tests/test_deploy_stack.py -q` no caso de AC-018 e conferir cada comando do guia contra a saída de `deploy/secrets.sh --ajuda`. Resultado: `uv run pytest tests/test_deploy_secrets_script.py -q` → 14 passed, incluindo o caso de AC-018 (cada subcomando citado como `deploy/secrets.sh <subcomando>`, os temas ALTER USER, recadastrar, gerenciador de senhas, `_v1` e `_local_v1`, e a ajuda do script).
  - [x] **VISUAL**: `Não aplicável`: documentação de texto sem superfície visual. Resultado: `Não aplicável`: documentação de texto sem superfície visual.
  - [x] **EVIDENCE**: Registrar o diff de `deploy/SECRETS.md` e o resultado do caso de AC-018. Resultado: Diff de `deploy/SECRETS.md` e GREEN de AC-018 (FR-001, FR-010, NFR-004, US-003, AC-011).
  - [x] **IMPROVE**: Aplicar a melhoria de um exemplo completo de primeira instalação e de troca ou justificar nenhuma. Resultado: Melhoria aplicada: o procedimento do Postgres avisa da janela curta entre alterar a senha no banco e fazer o deploy, que o texto de consequência do script não detalha.

  <!-- specsfy:evidence {"task": "T027", "refs": ["FR-010", "FR-001", "NFR-004", "AC-018", "US-003", "AC-011"], "files": ["deploy/SECRETS.md", "deploy/secrets.sh", ".specsfy/RULES.md", "tests/test_deploy_secrets_script.py"], "commands": [{"run": "uv run pytest -q", "exit": 0}, {"run": "uv run ruff check", "exit": 0}]} -->

- [x] T028 [DOC] Registrar em `.specsfy/RULES.md` as regras confirmadas de secrets (nome versionado, valor só por entrada padrão, troca perigosa bloqueada) e revisar `PROJECT.md` — Refs: FR-009, FR-010, NFR-001, AC-016, AC-018 — Depends: T022, T023, T026, T027
  - [x] **PREP**: Reler `.specsfy/RULES.md` e `PROJECT.md`; usar `$specsfy-aux-rules` e preservar as regras existentes. Resultado: `.specsfy/RULES.md` e `PROJECT.md` relidos; regras existentes preservadas, no padrão da skill `$specsfy-aux-rules`.
  - [x] **EXECUTE**: Acrescentar as regras confirmadas (DEC-002, DEC-003, DEC-004 e DEC-007) em Segurança e privacidade e atualizar `PROJECT.md` com a capacidade de operar os secrets, ou registrar a justificativa de ausência de impacto material; registrar que `.specsfy/STACK.md` e `.specsfy/DATABASE.md` não mudam. Resultado: `.specsfy/RULES.md` ganhou duas regras em Segurança e privacidade: secrets só por `deploy/secrets.sh`, versionados e nunca sobrescritos, e a troca bloqueada de `postgres_password` e `conexoes_chave`. `PROJECT.md` ganhou a capacidade de operar os secrets de produção. `.specsfy/STACK.md` e `.specsfy/DATABASE.md` não mudam: a entrega não altera tecnologia estrutural, manifests nem persistência.
  - [x] **VERIFY**: Executar `monitor_context.mjs --check`. Resultado: `monitor_context.mjs --check` → `CURRENT` sem `--acknowledge-project-no-change`, porque o `PROJECT.md` foi de fato atualizado.
  - [x] **VISUAL**: `Não aplicável`: documentação sem superfície visual. Resultado: `Não aplicável`: documentação sem superfície visual.
  - [x] **EVIDENCE**: Registrar o diff e a saída do monitor. Resultado: Diff de `.specsfy/RULES.md` e `PROJECT.md`, saída do monitor e a avaliação de ausência de impacto em STACK e DATABASE (FR-009, FR-010, NFR-001, AC-016, AC-018).
  - [x] **IMPROVE**: Nenhuma melhoria necessária: as regras apenas formalizam decisões já confirmadas. Resultado: Nenhuma melhoria necessária: as regras apenas formalizam decisões já confirmadas (DEC-001, DEC-002, DEC-004 e DEC-007).

#### Fase final — Qualidade

- [x] T030 [TEST] Executar regressão e rastreabilidade com `.agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs` sobre `specs/in-progress/0027-provisionamento-de-secrets-do-swarm/spec.md` e fechar o Delivery Gate — Refs: US-001, US-002, US-003, US-004, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018, AC-019 — Depends: T020, T022, T023, T024, T025, T026, T027, T028
  - [x] **PREP**: `check_database_safety.mjs --project . --command "uv run pytest"` → SAFE; fixtures conferidas: banco de teste explícito, isolamento transacional ou schemas exclusivos, sem apagar recursos existentes. Definition e Plan Gate READY; dependências concluídas. Regressão: Ruff, Pytest, Vitest, lint, tipos, build, rastreabilidade, aceite e política do repositório.
  - [x] **EXECUTE**: Executar `uv run ruff check`, `uv run pytest`, `check_traceability.mjs --full-chain`, `verify_acceptance.mjs` e `verify_repo.mjs`; o frontend não é tocado, mas `npm run test:tdd` roda como regressão. Resultado: Ruff Passed; Pytest 494 passed, 1 skipped; Vitest 219 passed/53 arquivos; lint, typecheck e build do frontend Passed; rastreabilidade 37/37; QA 19/19; verify_repo Passed (execução completa, sem self-test).
  - [x] **VERIFY**: Nenhuma falha; 37/37 IDs com cadeia completa, nenhum marcador órfão; `verify_acceptance.mjs` Passed para os 19 AC; `verify_evidence.mjs` Passed (strict). Findings Passed com `--root .` (contorno do problema de raiz conhecido). O único skip é a comparação paga opt-in da SPEC-0014 (`RUN_SPEC0014_REAL != 1`), fora desta entrega; warnings de depreciação FastAPI/LangGraph preexistentes não bloqueiam. Nenhum caso da SPEC-0027 foi pulado.
  - [x] **VISUAL**: `Não aplicável`: apenas fechamento de evidência de scripts de terminal e deploy; nenhuma interface foi alterada nesta tarefa.
  - [x] **EVIDENCE**: Seções 11–12 atualizadas com GREEN e Passed por cenário; seção 13 registra 37/37 IDs, 19/19 AC, 29/29 tarefas e 174/174 itens. Comentário JSON abaixo liga todos os IDs a arquivos existentes e comandos executados com saída 0. Documentação reconstruída e --check aprovado; monitor CURRENT. Sem alteração de stack, banco, regras ou capacidade além do já registrado na T028.
  - [x] **IMPROVE**: Melhorias aplicadas no registro: completar evidência da T020 e do guia AC-018, remover a referência obsoleta à T029 e atualizar a hipótese comprovada; chamadas de findings usam --root . para evitar o problema conhecido do validador. Nenhuma alteração de produção necessária; regressão verde.

  <!-- specsfy:evidence {"task": "T030", "refs": ["US-001", "US-002", "US-003", "US-004", "FR-001", "FR-002", "FR-003", "FR-004", "FR-005", "FR-006", "FR-007", "FR-008", "FR-009", "FR-010", "NFR-001", "NFR-002", "NFR-003", "NFR-004", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006", "AC-007", "AC-008", "AC-009", "AC-010", "AC-011", "AC-012", "AC-013", "AC-014", "AC-015", "AC-016", "AC-017", "AC-018", "AC-019"], "files": ["deploy/secrets.sh", "deploy/build_and_deploy.sh", "deploy/stack.prod.yml", "deploy/stack.local.yml", "deploy/SECRETS.md", "tests/test_deploy_secrets_script.py", "tests/test_deploy_build_and_deploy_script.py", "tests/test_deploy_stack.py", ".specsfy/RULES.md", "PROJECT.md"], "commands": [{"run": "uv run ruff check", "exit": 0}, {"run": "uv run pytest -q", "exit": 0}, {"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}, {"run": "node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0027-provisionamento-de-secrets-do-swarm/spec.md . --kinds US,FR,NFR,AC --full-chain", "exit": 0}, {"run": "node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/in-progress/0027-provisionamento-de-secrets-do-swarm/spec.md .", "exit": 0}, {"run": "node .agents/skills/specsfy-04-validate/scripts/verify_repo.mjs . --boundary local --timeout-seconds 300 --max-output-bytes 65536", "exit": 0}, {"run": "node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check", "exit": 0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001–T019 (RED) → T020 (prova de `name:`) → T021 → T022 → T023 → T024 → T026 → T027 → T028 → T030.
- Tarefas paralelas: T025 (arquivos de stack e `tests/test_deploy_stack.py`) pode andar junto das tarefas do script (T021 a T024), porque não compartilha arquivo nem estado com elas. As demais compartilham `deploy/secrets.sh`, dependência ou documentação.
- Estratégia de MVP: `verificar` e `resolver` (T021) com o deploy e o stack (T025, T026) formam o primeiro marco, porque já impedem um deploy com secret ausente; `criar` (T022) e `trocar` (T023) completam o provisionamento, e o ambiente local (T024) fecha a validação automatizada. O ensaio completo no Swarm real, antes planejado como T029, ficou fora do Delivery Gate (DEC-011).

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0022 (stack de produção) e SPEC-0026 (`conexoes_chave`), já concluídas.
- CLI do Docker, `openssl` e um nó manager do Swarm no momento do uso.
- BACKLOG-0032 (runbook) depende desta spec e a referenciará.

#### Riscos

- **Hipótese comprovada (T020)**: Docker 29.8.2 confirmou `name:` com variável e padrão no Compose 3.7 na stack isolada `prova0027`: sem variável usa `prova0027_v1`, com `PROVA_SECRET=prova0027_v2` usa `prova0027_v2`; `docker service inspect` confirmou ambos com destino lógico `/run/secrets/chave`. O contorno de DEC-009 não foi necessário.
- Trocar `postgres_password` só no Swarm derruba backend e worker, porque o Postgres não relê o secret depois de criado → bloqueio por padrão e procedimento exibido.
- Perda de um valor gerado e exibido uma vez → instrução de guarda no gerenciador de senhas; `conexoes_chave` perdida obriga recadastrar as conexões.
- Atualização de uma réplica única interrompe o serviço por alguns segundos durante o rolling update → aceito no Beta; `update_config` com `start-first` fica para um item futuro.
- O ensaio local completo no Swarm real não foi executado nesta entrega, porque a stack em execução na máquina de desenvolvimento compartilha volumes e rede externos com ele → a validação automatizada, o `docker stack config` e a prova da T020 cobrem o mecanismo, e o ensaio fica como validação manual do operador antes do primeiro deploy em produção.
- Valores digitados podem ficar no buffer do terminal ou em gravação de tela → fora do alcance do script; documentado no guia.

#### Suposições

- Não existe produção implantada com nomes de secret sem versão; por isso o padrão do stack é `<nome>_v1` e nenhuma migração de nomes é necessária. Default reversível.
- O `r2_credentials` é um arquivo de atribuições `VARIAVEL=valor` lido por `. /run/secrets/r2_credentials`, como o stack atual faz; o script monta esse conteúdo a partir dos quatro campos pedidos.
- No ensaio local, o `r2_credentials` sem variáveis ativas faz o backend gravar uploads em disco, como já documenta `deploy/stack.local.yml`.
- A chave Fernet gerada por `openssl rand -base64 32` com `+/` trocado por `-_` é aceita por `cryptography.fernet.Fernet`; o teste de NFR-003 comprova.
- Para automação e testes, o parâmetro explícito `--entrada-padrao` aceita os valores pedidos como linhas da entrada padrão, na ordem das perguntas (chave da OpenRouter; bucket, endpoint, access key e secret key do R2; e, nas trocas perigosas, o nome do secret como confirmação); sem ele, entrada não interativa é recusada. Os valores continuam fora de argumentos de comando. Default reversível.

### 17. Decisões

- **DEC-001**: Entrega principal é um script de provisionamento mais verificação prévia no deploy — alternativas descartadas: apenas documentar comandos, e acrescentar inventário com lembrete de troca.
- **DEC-002**: Troca por nome versionado resolvido por variável no deploy — alternativas descartadas: recriar o secret com o mesmo nome (indisponibilidade) e `docker service update` direto (divergência entre stack e serviço).
- **DEC-003**: Os secrets internos são gerados e exibidos uma única vez; só `openrouter_api_key` e `r2_credentials` são pedidos — alternativas descartadas: pedir todos e gerar sem nunca exibir.
- **DEC-004**: Troca de `postgres_password` e `conexoes_chave` é bloqueada por padrão, com parâmetro explícito, confirmação digitada e consequência exibida — alternativas descartadas: automatizar a troca no banco e proibir a troca.
- **DEC-005**: `session_secret` é removido: nada em `src/` o usa desde a SPEC-0020.
- **DEC-006**: O script também prepara o ensaio local, com sufixo `_local` e valores fictícios.
- **DEC-007**: `criar` sem nomes completa só os secrets ausentes e `criar` com nome explícito recusa o existente — permite retomar uma criação interrompida sem sobrescrever nada.
- **DEC-009**: A primeira tarefa prova, no ensaio local do Swarm, que um secret externo aceita `name:` com variável e padrão; se a hipótese falhar, os nomes são resolvidos por substituição de texto no arquivo do stack antes do deploy, sem mudar o contrato de variáveis nem o comportamento do script.
- **DEC-010**: `build_and_deploy.sh` consome a saída de `resolver` com `eval`, aceitável porque `resolver` emite apenas atribuições cujos nomes passam pela expressão regular do contrato de nomes.
- **DEC-011**: O ensaio local completo no Swarm real sai do Delivery Gate: a stack `rag-pipeline` em execução na máquina de desenvolvimento usa os mesmos volumes e rede externos, e um deploy de ensaio a atualizaria; a validação ficou a cargo do operador, e o mecanismo está coberto por testes, por `docker stack config` e pela prova isolada da T020 (decisão do operador em 2026-10-08).
- **DEC-008**: A versão vigente é a de maior `N` no nome, sem arquivo de estado nem labels — evita um segundo registro que possa divergir do Swarm.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/RULES.md` registra as regras confirmadas de secrets (nome versionado, sem valor em argumento, troca bloqueada) e `PROJECT.md` é revisado, com justificativa quando não houver impacto material; `.specsfy/STACK.md` e `.specsfy/DATABASE.md` não mudam e a evidência registra essa avaliação.
- [x] `deploy/SECRETS.md` existe e a prova da T020 comprovou a hipótese de `name:` com variável; o ensaio local completo no Swarm real fica como validação manual do operador (DEC-011).
