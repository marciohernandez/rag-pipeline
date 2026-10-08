# Especificação integrada: Provisionamento e conferência dos secrets de produção do Swarm

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0027 |
| Slug | 0027-provisionamento-de-secrets-do-swarm |
| Status | Defined |
| Effort | 5 |
| Effort updated at | 2026-10-08 |
| Effort rationale | Script de operação com segredos, versionamento por nome, bloqueios para trocas com efeito colateral, mudança no stack e no deploy e testes com `docker` simulado; sem interface, banco ou mudança de pipeline. |
| ClickUp Task | |
| Milestones | M03 |
| Definition Gate | Passed |
| Plan Gate | Pending |
| Delivery Gate | Pending |
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

- `deploy/secrets.sh` (bash, `set -euo pipefail`): despacha os subcomandos; consulta o Swarm por `docker secret ls --format '{{.Name}}'`; cria por `printf '%s' "$valor" | docker secret create "$nome" -`; lê entradas com `read -r -s`; gera a senha com `tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32` e a chave Fernet com `openssl rand -base64 32 | tr '+/' '-_'`.
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
specs/defined/0027-provisionamento-de-secrets-do-swarm/
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

- Nenhuma documentação externa foi consultada; os comandos do Docker acima são os já usados em `deploy/build_and_deploy.sh` e na SPEC-0022. A semântica de `name:` com interpolação em secrets externos é hipótese a provar no ensaio local.

#### Eventos e outros contratos

- Contrato de nomes: `^(openrouter_api_key|r2_credentials|postgres_password|conexoes_chave)(_local)?_v[0-9]+$`; contrato de variáveis: `OPENROUTER_API_KEY_SECRET`, `R2_CREDENTIALS_SECRET`, `POSTGRES_PASSWORD_SECRET`, `CONEXOES_CHAVE_SECRET`.

### 11. Estratégia TDD

- **Unidade**: Não aplicável como unidade isolada; as regras de nome, versão e validação são exercitadas pelo script inteiro.
- **Integração/contrato**: o script e o `build_and_deploy.sh` rodam com um `docker` falso no `PATH` que registra argumentos e entrada padrão e simula um Swarm em memória (lista de secrets); o YAML do stack e do override é inspecionado em testes de contrato.
- **BDD/aceite**: o Gherkin da seção 6 orienta o desenho dos testes; não há arquivos `.feature`.
- **Runner TDD**: Pytest (`uv run pytest`) e Ruff, como no restante do projeto.
- **E2E**: validação manual única do ensaio local no Swarm real (secrets `_local`, `docker stack deploy` e serviços subindo), porque o Swarm não existe na suíte.
- **Verificação manual**: a prova de `name:` com variável no Compose 3.7 e o primeiro uso no servidor real, pelo operador, pelo mesmo motivo.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, NFR-001, NFR-003, NFR-004, AC-001 | AC-001 na seção 6 | Criar os secrets pela primeira vez em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 FR-001 FR-002 NFR-001 NFR-003 NFR-004 AC-001` | Pending | Pending | Pending |
| US-001, FR-002, NFR-003, AC-002 | AC-002 na seção 6 | Gerar e exibir uma única vez os secrets internos em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 FR-002 NFR-003 AC-002` | Pending | Pending | Pending |
| US-001, FR-001, FR-003, NFR-002, AC-003 | AC-003 na seção 6 | Recusar a criação explícita de um secret que já existe em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 FR-001 FR-003 NFR-002 AC-003` | Pending | Pending | Pending |
| US-001, FR-002, FR-003, NFR-002, AC-004 | AC-004 na seção 6 | Completar somente os secrets ausentes em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 FR-002 FR-003 NFR-002 AC-004` | Pending | Pending | Pending |
| US-001, FR-002, FR-003, FR-009, NFR-004, AC-005 | AC-005 na seção 6 | Recusar entrada vazia ou inválida sem criar nada em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 FR-002 FR-003 FR-009 NFR-004 AC-005` | Pending | Pending | Pending |
| US-002, US-004, FR-005, FR-008, AC-006 | AC-006 na seção 6 | Resolver a versão mais alta de cada secret por ambiente em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-002 US-004 FR-005 FR-008 AC-006` | Pending | Pending | Pending |
| US-002, FR-005, FR-006, NFR-004, AC-007 | AC-007 na seção 6 | Bloquear o deploy quando falta um secret em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-002 FR-005 FR-006 NFR-004 AC-007` | Pending | Pending | Pending |
| US-002, FR-005, FR-006, FR-007, AC-008 | AC-008 na seção 6 | Entregar a versão resolvida ao stack no deploy em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-002 FR-005 FR-006 FR-007 AC-008` | Pending | Pending | Pending |
| US-002, FR-007, AC-009 | AC-009 na seção 6 | Declarar o stack só com secrets externos versionados e sem `session_secret` em `tests/test_deploy_stack.py` com marcador próprio `SPECSFY: SPEC-0027 US-002 FR-007 AC-009` | Pending | Pending | Pending |
| US-003, FR-004, FR-005, NFR-002, AC-010 | AC-010 na seção 6 | Trocar um secret criando a próxima versão em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-003 FR-004 FR-005 NFR-002 AC-010` | Pending | Pending | Pending |
| US-003, FR-004, NFR-004, FR-010, AC-011 | AC-011 na seção 6 | Bloquear a troca de secret com efeito colateral por padrão em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-003 FR-004 NFR-004 FR-010 AC-011` | Pending | Pending | Pending |
| US-003, FR-004, FR-010, NFR-001, AC-012 | AC-012 na seção 6 | Permitir a troca perigosa só com parâmetro e confirmação digitada em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-003 FR-004 FR-010 NFR-001 AC-012` | Pending | Pending | Pending |
| US-003, FR-004, NFR-002, AC-013 | AC-013 na seção 6 | Manter a versão anterior quando a troca é interrompida em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-003 FR-004 NFR-002 AC-013` | Pending | Pending | Pending |
| US-004, FR-008, NFR-003, AC-014 | AC-014 na seção 6 | Preparar o ensaio local com valores fictícios em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-004 FR-008 NFR-003 AC-014` | Pending | Pending | Pending |
| US-004, FR-007, FR-008, AC-015 | AC-015 na seção 6 | Subir o ensaio local pelo mesmo mecanismo de versão em `tests/test_deploy_stack.py` com marcador próprio `SPECSFY: SPEC-0027 US-004 FR-007 FR-008 AC-015` | Pending | Pending | Pending |
| US-001, US-003, FR-009, NFR-001, AC-016 | AC-016 na seção 6 | Nunca expor o valor de um secret em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-001 US-003 FR-009 NFR-001 AC-016` | Pending | Pending | Pending |
| FR-001, FR-009, NFR-004, AC-017 | AC-017 na seção 6 | Falhar com mensagem clara sem Docker ou fora do manager em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 FR-001 FR-009 NFR-004 AC-017` | Pending | Pending | Pending |
| FR-010, FR-001, NFR-004, AC-018 | AC-018 na seção 6 | Documentar o uso, a guarda dos valores e as consequências em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0027 FR-010 FR-001 NFR-004 AC-018` | Pending | Pending | Pending |
| US-002, FR-005, FR-006, NFR-002, AC-019 | AC-019 na seção 6 | Verificar os secrets antes dos builds e só então fazer o deploy em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0027 US-002 FR-005 FR-006 NFR-002 AC-019` | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-001 | AC-003 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-001 | AC-017 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-001 | AC-018 | Contrato | `tests/test_deploy_secrets_script.py` | Pending |
| FR-002 | AC-001 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-002 | AC-002 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-002 | AC-004 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-002 | AC-005 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-003 | AC-003 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-003 | AC-004 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-003 | AC-005 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-004 | AC-010 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-004 | AC-011 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-004 | AC-012 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-004 | AC-013 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-005 | AC-006 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-005 | AC-007 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Pending |
| FR-005 | AC-008 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Pending |
| FR-005 | AC-010 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-005 | AC-019 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Pending |
| FR-006 | AC-007 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Pending |
| FR-006 | AC-008 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Pending |
| FR-006 | AC-019 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Pending |
| FR-007 | AC-008 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Pending |
| FR-007 | AC-009 | Contrato | `tests/test_deploy_stack.py` | Pending |
| FR-007 | AC-015 | Contrato | `tests/test_deploy_stack.py` | Pending |
| FR-008 | AC-006 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-008 | AC-014 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-008 | AC-015 | Contrato | `tests/test_deploy_stack.py` | Pending |
| FR-009 | AC-005 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-009 | AC-016 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-009 | AC-017 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-010 | AC-011 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-010 | AC-012 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| FR-010 | AC-018 | Contrato | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-001 | AC-001 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-001 | AC-012 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-001 | AC-016 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-002 | AC-003 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-002 | AC-004 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-002 | AC-010 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-002 | AC-013 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-002 | AC-019 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Pending |
| NFR-003 | AC-001 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-003 | AC-002 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-003 | AC-014 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-004 | AC-001 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-004 | AC-005 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-004 | AC-007 | Integração | `tests/test_deploy_build_and_deploy_script.py` | Pending |
| NFR-004 | AC-011 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-004 | AC-017 | Integração | `tests/test_deploy_secrets_script.py` | Pending |
| NFR-004 | AC-018 | Contrato | `tests/test_deploy_secrets_script.py` | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed em 2026-10-08
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0027-provisionamento-de-secrets-do-swarm/spec.md`
- **Achados**: 4 US, 10 FR, 4 NFR e 19 AC; cada US, FR e NFR coberto por no mínimo 3 AC; nenhum BLOCKER e nenhum P1. A DoD não precisa citar `.specsfy/STACK.md` nem `.specsfy/DATABASE.md` porque a entrega não muda stack nem persistência, e a evidência registra essa avaliação; `PROJECT.md` e `.specsfy/RULES.md` estão na DoD.
- **FIND-ARCH-001** [P2] [Accepted] A hipótese de que um secret externo aceita `name:` com variável e padrão no Compose 3.7 não foi provada por documentação nem por execução — Refs: FR-007, AC-008, AC-009 — Evidence: deploy/stack.prod.yml:1 — Effect: se falhar, o stack não receberia a versão resolvida — Suggestion: DEC-009 prova no ensaio local e define a resolução por substituição de texto como contorno; aceito.
- **FIND-SEC-001** [P3] [Accepted] O deploy aplica `eval` à saída de `resolver` — Refs: FR-005, AC-006, AC-008 — Evidence: deploy/build_and_deploy.sh:1 — Effect: um nome de secret malicioso poderia injetar comando — Suggestion: `resolver` só emite nomes validados pelo contrato (FR-005, DEC-010); aceito.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0027-provisionamento-de-secrets-do-swarm/spec.md`
- **Achados**: Pending.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0027-provisionamento-de-secrets-do-swarm/spec.md .`
- **Achados**: Pending.

### 14. Tarefas

Pendente: a decomposição em tarefas é produzida por `$specsfy-05-tasks` depois que o Definition Gate for `Passed`. Formato esperado:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Cada tarefa terá o checklist `PREP`, `EXECUTE`, `VERIFY`, `VISUAL`, `EVIDENCE` e `IMPROVE`, nessa ordem.

### 15. Ordem de execução

- Pendente: definida por `$specsfy-05-tasks`. Sequência prevista: provar `name:` com variável no ensaio local, script (`criar`, `resolver`, `verificar`, `trocar`), stack e override, verificação no deploy, documentação e regras.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0022 (stack de produção) e SPEC-0026 (`conexoes_chave`), já concluídas.
- CLI do Docker, `openssl` e um nó manager do Swarm no momento do uso.
- BACKLOG-0032 (runbook) depende desta spec e a referenciará.

#### Riscos

- **Hipótese não provada**: um secret externo aceitar `name:` com variável e padrão no Compose 3.7 → provar no ensaio local do Swarm na primeira tarefa; se falhar, resolver os nomes por `sed` no arquivo antes do deploy e atualizar esta spec.
- Trocar `postgres_password` só no Swarm derruba backend e worker, porque o Postgres não relê o secret depois de criado → bloqueio por padrão e procedimento exibido.
- Perda de um valor gerado e exibido uma vez → instrução de guarda no gerenciador de senhas; `conexoes_chave` perdida obriga recadastrar as conexões.
- Atualização de uma réplica única interrompe o serviço por alguns segundos durante o rolling update → aceito no Beta; `update_config` com `start-first` fica para um item futuro.
- Valores digitados podem ficar no buffer do terminal ou em gravação de tela → fora do alcance do script; documentado no guia.

#### Suposições

- Não existe produção implantada com nomes de secret sem versão; por isso o padrão do stack é `<nome>_v1` e nenhuma migração de nomes é necessária. Default reversível.
- O `r2_credentials` é um arquivo de atribuições `VARIAVEL=valor` lido por `. /run/secrets/r2_credentials`, como o stack atual faz; o script monta esse conteúdo a partir dos quatro campos pedidos.
- No ensaio local, o `r2_credentials` sem variáveis ativas faz o backend gravar uploads em disco, como já documenta `deploy/stack.local.yml`.
- A chave Fernet gerada por `openssl rand -base64 32` com `+/` trocado por `-_` é aceita por `cryptography.fernet.Fernet`; o teste de NFR-003 comprova.

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
- **DEC-008**: A versão vigente é a de maior `N` no nome, sem arquivo de estado nem labels — evita um segundo registro que possa divergir do Swarm.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
- [ ] `.specsfy/RULES.md` registra as regras confirmadas de secrets (nome versionado, sem valor em argumento, troca bloqueada) e `PROJECT.md` é revisado, com justificativa quando não houver impacto material; `.specsfy/STACK.md` e `.specsfy/DATABASE.md` não mudam e a evidência registra essa avaliação.
- [ ] `deploy/SECRETS.md` existe e o ensaio local do Swarm comprovou a hipótese de `name:` com variável.
