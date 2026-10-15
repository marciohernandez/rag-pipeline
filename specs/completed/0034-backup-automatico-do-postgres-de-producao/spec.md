# Especificação integrada: Backup automático do Postgres de produção

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0034 |
| Slug | 0034-backup-automatico-do-postgres-de-producao |
| Status | Complete |
| Effort | 5 |
| Effort updated at | 2026-10-15 |
| Effort rationale | Um serviço agendado em shell (dump, cifragem, envio S3, verificação, retenção, aviso), um script de restauração, secrets e stack; sem schema nem interface. O risco está em falhas parciais e em segredos, cobertos com binários falsos e um ensaio local no Docker; a verificação real no R2 fica com a pessoa na VPS (perfil `standard`). |
| ClickUp Task | |
| Milestones | M03 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-10-15 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O Postgres de produção do Beta guardará dados reais de pessoas, bases, execuções e conversas do assistente desde o primeiro dia e não existe nenhuma rotina de backup. A perda do disco ou da VPS apagaria tudo. Origem: `specs/backlog/0031-backup-automatico-do-postgres-de-producao.md` (BACKLOG-0031), com as oito decisões de 2026-10-13.

#### Resultado desejado

A cada dia, de madrugada, um dump cifrado do Postgres sai da VPS para um bucket separado do Cloudflare R2, é verificado, entra numa retenção de 7 diários e 4 semanais e, se algo falhar, Marcio recebe um aviso por e-mail e por chat. Existe um script de restauração e um documento que explica a operação. Tudo é provado no Docker local antes do deploy na VPS.

#### Métricas de sucesso

- O ciclo completo (dump, cifragem, envio, verificação, retenção) passa no ensaio local com armazenamento S3 local e Postgres temporário.
- Uma restauração de teste num banco temporário lista as tabelas do dump.
- 100% das etapas com falha injetada deixam os backups anteriores intactos e disparam o aviso.
- Nenhum valor de segredo aparece em log, argumento ou mensagem nos testes.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: o stack de produção (`deploy/stack.prod.yml`) roda o Postgres como serviço do Swarm com volume externo e já usa secrets externos versionados (SPEC-0027) → o serviço de backup segue o mesmo padrão e é preso ao nó de dados.
- **R-002**: backend e worker usam o secret `r2_credentials` para uploads e `.md` → os arquivos de origem e os `.md` já ficam no R2, fora da VPS; o backup cobre somente o Postgres (os vetores do Qdrant são refeitos pela Fase 2).

#### Fontes e contexto consultados

- `specs/backlog/0031-backup-automatico-do-postgres-de-producao.md`, `specs/backlog/0032-runbook-de-deploy-manual-em-producao.md`, `specs/milestones/M03.md`.
- `deploy/stack.prod.yml`, `deploy/stack.local.yml`, `deploy/secrets.sh`, `deploy/build_and_deploy.sh`, `deploy/SECRETS.md`.
- `tests/test_deploy_stack.py`, `tests/test_deploy_secrets_script.py`, `tests/_docker_falso.py` (padrão dos binários falsos).

#### Documentação consultada

- Documentação oficial MinIO e Moto para localizar uma imagem acessível do S3 local; consulta e resultados em `research/2026-10-15-s3-local.md`. PostgreSQL, OpenSSL e CLI S3 exercitados no ensaio Docker.

#### Artefatos de pesquisa armazenados

- `specs/completed/0034-backup-automatico-do-postgres-de-producao/research/2026-10-15-s3-local.md`: fontes primárias e resultado dos pulls do armazenamento de ensaio.

#### Dúvidas respondidas

- **Q**: Para onde vai o dump? → **A**: bucket do Cloudflare R2 separado do bucket do sistema, com credencial própria (Pergunta 1 do backlog).
- **Q**: Qual a retenção? → **A**: 7 diários e 4 semanais (Pergunta 2).
- **Q**: O dump é protegido? → **A**: cifrado antes de sair; a chave fica com a pessoa responsável, fora da VPS, e o job recebe uma cópia como secret do Swarm (Pergunta 3).
- **Q**: O que o backup cobre? → **A**: só o Postgres (Pergunta 4, opção 3).
- **Q**: Como se verifica? → **A**: a cada backup, sem teste semanal automático de restauração (Pergunta 5, opção 3).
- **Q**: Como se avisa? → **A**: falha por e-mail e por webhook de chat; sucesso só no log (Pergunta 6, opção 4).
- **Q**: Horário? → **A**: madrugada, por exemplo 3h, com o sistema no ar (Pergunta 7).
- **Q**: Restauração? → **A**: script de restauração, passo a passo no runbook e uma restauração de teste na entrega (Pergunta 8, opção 3).
- **Q**: Onde a entrega é provada? → **A**: no Docker local, com a verificação real no R2 e no e-mail feita depois pela pessoa na VPS (decisão de Marcio em 2026-10-15).

#### Dúvidas abertas

- Nenhuma bloqueante. Quatro pontos que o backlog deixou em aberto foram resolvidos por padrão reversível em Suposições (provedor de e-mail e chat, nome e escopo do bucket, ferramenta de cifragem, onde o job roda).

### 3. Escopo e atores

#### Incluído

- Serviço `backup_ragpipeline` no Swarm com agendador diário, dump, cifragem, envio, verificação, retenção e aviso de falha.
- Script `deploy/backup/restaurar.sh` e documento `deploy/BACKUP.md`.
- Três secrets novos no `deploy/secrets.sh`, no stack de produção e no override local.
- Ensaio local no Docker com armazenamento S3 local e uma restauração de teste.

#### Fora de escopo

- Backup do Qdrant.
- Recuperação até um ponto no tempo (PITR) e réplica.
- Teste automático periódico de restauração.
- Frequência maior que a diária.
- A verificação real contra o R2, o SMTP e o chat de produção (fica com a pessoa, na VPS, depois do deploy).
- O runbook de deploy em si (BACKLOG-0032), que apenas referencia o `deploy/BACKUP.md`.

#### Atores

- **Marcio**: responsável pelos dados do Beta; guarda a chave fora da VPS, recebe os avisos e executa a restauração.
- **Serviço de backup**: contêiner no nó de dados que executa o ciclo diário.

### 4. Princípios e restrições do projeto

- **PR-001**: Nunca versionar ou expor credenciais; segredos ficam fora do repositório e do stack file (`.specsfy/RULES.md`).
- **PR-002**: Segredos só entram nos serviços por secret externo versionado do Swarm (SPEC-0027).
- **PR-003**: Nenhum teste, ensaio ou restauração usa o banco de desenvolvimento; a restauração de teste usa um banco temporário próprio.
- **PR-004**: Nenhum comando que apaga, recria ou zera banco ou schema é usado ou sugerido; a restauração só cria bancos novos.
- **PR-005**: O corpo desta spec evita a palavra proibida pela regra de marcadores do projeto (`tests/test_spec_markers.py`).
- **PR-006**: Branch `spec/0034-backup-automatico-do-postgres-de-producao` para a implementação; uma branch nunca carrega duas specs.

### 5. Histórias de usuário

#### US-001 — Ter um backup diário cifrado fora da VPS (P1)

Como Marcio, responsável pelos dados do Beta, quero que o Postgres de produção seja copiado diariamente, cifrado, para um bucket separado, para não perder pessoas, bases, execuções e conversas se a VPS ou o disco falharem.

**Por que P1**: O Beta guarda dados reais desde o primeiro dia e hoje não há nenhuma rotina de cópia.
**Teste independente**: Rodar um ciclo contra um Postgres e um armazenamento S3 de teste e conferir o objeto cifrado no bucket.
**Requisitos**: FR-001, FR-002, FR-003, FR-004, FR-005

#### US-002 — Ser avisado quando o backup falha (P1)

Como Marcio, responsável pelos dados do Beta, quero receber um aviso por e-mail e por chat quando o backup ou a verificação falhar, para agir antes que a janela de perda cresça.

**Por que P1**: Um backup que falha em silêncio é pior que nenhum: dá falsa segurança.
**Teste independente**: Forçar uma falha no ciclo e conferir a mensagem SMTP e o POST do webhook.
**Requisitos**: FR-006, FR-009

#### US-003 — Restaurar um backup com segurança (P1)

Como Marcio, responsável pelos dados do Beta, quero restaurar um backup escolhido num banco temporário e conferir o conteúdo, para recuperar dados sem arriscar o banco em uso nem o de desenvolvimento.

**Por que P1**: Um backup só vale se alguém consegue restaurá-lo; o procedimento precisa estar escrito e testado.
**Teste independente**: Restaurar um dump de teste num Postgres temporário e listar as tabelas.
**Requisitos**: FR-007, FR-010

#### US-004 — Ensaiar o backup no Docker local (P2)

Como Marcio, que valida a entrega antes de fazer o deploy na VPS, quero ensaiar o ciclo completo no Docker local, sem credenciais reais, para chegar à VPS com o mecanismo já provado.

**Por que P2**: O deploy na VPS acontece depois; a prova local reduz o risco do primeiro uso real.
**Teste independente**: Subir o armazenamento S3 local, rodar o ciclo e restaurar.
**Requisitos**: FR-001, FR-008

### 6. Cenários BDD de aceite

#### AC-001 — Gerar, cifrar e enviar o backup diário

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-003

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-001 @NFR-003 @AC-001
Feature: Backup automático do Postgres

  Scenario: Gerar, cifrar e enviar o backup diário
    Given o Postgres responde e o bucket de backup está acessível
    And a chave de cifragem e as credenciais do bucket estão nos secrets
    When o ciclo de backup roda
    Then o dump em formato custom é gerado com `pg_dump` sem parar nenhum serviço da aplicação
    And o arquivo é cifrado antes de sair do contêiner
    And o objeto `diarios/AAAA-MM-DD.dump.enc` existe no bucket de backup
```

#### AC-002 — Nunca deixar o dump em claro fora do diretório temporário

**Cobre**: US-001, FR-002, NFR-001

```gherkin
@US-001 @FR-002 @NFR-001 @AC-002
Feature: Backup automático do Postgres

  Scenario: Nunca deixar o dump em claro fora do diretório temporário
    Given um ciclo de backup em andamento
    When o ciclo termina com sucesso ou com falha
    Then o dump em claro só existiu no diretório temporário do job
    And o diretório temporário é removido ao final, inclusive em falha
    And nenhum caminho do bucket recebe um arquivo sem a extensão `.enc`
```

#### AC-003 — Copiar o backup de domingo para a retenção semanal

**Cobre**: US-001, FR-003, FR-005, NFR-004

```gherkin
@US-001 @FR-003 @FR-005 @NFR-004 @AC-003
Feature: Backup automático do Postgres

  Scenario: Copiar o backup de domingo para a retenção semanal
    Given a data da execução é um domingo
    When o ciclo de backup conclui com sucesso, uma ou duas vezes no mesmo dia
    Then o bucket recebe `diarios/AAAA-MM-DD.dump.enc` e `semanais/AAAA-SWW.dump.enc`
    And em outros dias da semana nenhum objeto semanal é criado
    And a segunda execução do dia sobrescreve os mesmos objetos, sem duplicar
```

#### AC-004 — Manter 7 backups diários e 4 semanais

**Cobre**: US-001, FR-004, FR-005, NFR-002

```gherkin
@US-001 @FR-004 @FR-005 @NFR-002 @AC-004
Feature: Backup automático do Postgres

  Scenario: Manter 7 backups diários e 4 semanais
    Given o bucket já tem 7 diários e 4 semanais anteriores
    And o novo backup foi enviado e verificado
    When a poda de retenção roda
    Then o diário mais antigo e o semanal mais antigo são removidos
    And restam 7 diários e 4 semanais, incluindo o novo
    And objetos fora dos prefixos `diarios/` e `semanais/` nunca são removidos
```

#### AC-005 — Aprovar a verificação do backup

**Cobre**: US-001, FR-002, FR-004

```gherkin
@US-001 @FR-002 @FR-004 @AC-005
Feature: Backup automático do Postgres

  Scenario: Aprovar a verificação do backup
    Given o objeto cifrado foi enviado ao bucket
    When a verificação roda
    Then o objeto existe e o tamanho enviado coincide com o tamanho local
    And o tamanho é maior que o mínimo configurado
    And a cifragem abre com a chave e `pg_restore --list` lê o conteúdo
    And o resultado fica registrado no log como sucesso
```

#### AC-006 — Reprovar a verificação sem apagar o backup anterior

**Cobre**: US-001, US-002, FR-004, FR-005, NFR-002

```gherkin
@US-001 @US-002 @FR-004 @FR-005 @NFR-002 @AC-006
Feature: Backup automático do Postgres

  Scenario: Reprovar a verificação sem apagar o backup anterior
    Given o dump gerado está vazio, truncado ou não abre com a chave
    When a verificação roda
    Then o ciclo termina com falha e código diferente de zero
    And a poda de retenção não roda
    And os backups anteriores permanecem no bucket
    And o aviso de falha é disparado
```

#### AC-007 — Tentar de novo quando o bucket está indisponível

**Cobre**: US-001, US-002, FR-003, FR-006, NFR-002

```gherkin
@US-001 @US-002 @FR-003 @FR-006 @NFR-002 @AC-007
Feature: Backup automático do Postgres

  Scenario: Tentar de novo quando o bucket está indisponível
    Given o bucket de backup recusa o envio
    When o ciclo de backup tenta enviar o objeto
    Then o envio é repetido até o limite de tentativas, com espera entre elas
    And esgotadas as tentativas, o ciclo termina com falha e dispara o aviso
    And os backups anteriores permanecem e a execução seguinte tenta de novo
```

#### AC-008 — Avisar a falha por e-mail e por chat

**Cobre**: US-002, FR-006, NFR-001

```gherkin
@US-002 @FR-006 @NFR-001 @AC-008
Feature: Backup automático do Postgres

  Scenario: Avisar a falha por e-mail e por chat
    Given um ciclo de backup terminou com falha
    And o e-mail e o webhook de chat estão configurados
    When o aviso é enviado
    Then uma mensagem SMTP é enviada ao destinatário configurado
    And uma requisição POST com a mensagem é enviada ao webhook
    And as mensagens dizem a etapa que falhou e não contêm chave, senha nem URL com credencial
```

#### AC-009 — Entregar o aviso pelo canal que funciona

**Cobre**: US-002, FR-006, FR-009

```gherkin
@US-002 @FR-006 @FR-009 @AC-009
Feature: Backup automático do Postgres

  Scenario: Entregar o aviso pelo canal que funciona
    Given um ciclo de backup terminou com falha
    And o envio do e-mail falha
    When o aviso é enviado
    Then o webhook de chat ainda recebe a mensagem
    And a falha do e-mail fica registrada no log
    And o código de saída continua indicando a falha do backup
```

#### AC-010 — Registrar o sucesso só no log

**Cobre**: US-002, FR-006, FR-009

```gherkin
@US-002 @FR-006 @FR-009 @AC-010
Feature: Backup automático do Postgres

  Scenario: Registrar o sucesso só no log
    Given um ciclo de backup terminou com sucesso
    When o ciclo encerra
    Then nenhum e-mail nem webhook é disparado
    And o log registra data, objetos enviados, tamanho e a retenção aplicada
    And o código de saída é zero
```

#### AC-011 — Restaurar um backup num banco temporário

**Cobre**: US-003, FR-007, NFR-001

```gherkin
@US-003 @FR-007 @NFR-001 @AC-011
Feature: Backup automático do Postgres

  Scenario: Restaurar um backup num banco temporário
    Given existe um backup cifrado no bucket
    And a pessoa tem a chave e o endereço de um servidor Postgres de destino
    When a pessoa executa o script de restauração informando o objeto
    Then o script baixa o objeto e decifra com a chave
    And cria um banco novo `restauracao_AAAAMMDDHHMMSS` no servidor de destino e restaura nele
    And informa o nome do banco criado e não imprime a chave
```

#### AC-012 — Recusar objeto inexistente ou chave errada

**Cobre**: US-003, FR-007, NFR-002

```gherkin
@US-003 @FR-007 @NFR-002 @AC-012
Feature: Backup automático do Postgres

  Scenario: Recusar objeto inexistente ou chave errada
    Given o objeto informado não existe ou a chave não abre o arquivo
    When a pessoa executa o script de restauração
    Then o script termina com código diferente de zero e mensagem clara
    And nenhum banco é criado no servidor de destino
    And o diretório temporário é removido
```

#### AC-013 — Nunca restaurar sobre um banco existente

**Cobre**: US-003, FR-007, NFR-002

```gherkin
@US-003 @FR-007 @NFR-002 @AC-013
Feature: Backup automático do Postgres

  Scenario: Nunca restaurar sobre um banco existente
    Given o servidor de destino já tem bancos, inclusive o `rag_pipeline`
    When a pessoa executa o script de restauração, inclusive pedindo um nome de banco já existente
    Then o script só cria bancos novos e recusa um nome que já existe
    And não usa opções que apagam objetos (`--clean`, `DROP`)
    And os bancos existentes permanecem intactos
```

#### AC-014 — Provisionar os secrets do backup

**Cobre**: US-004, FR-008, NFR-001

```gherkin
@US-004 @FR-008 @NFR-001 @AC-014
Feature: Backup automático do Postgres

  Scenario: Provisionar os secrets do backup
    Given o gerenciador de secrets de produção
    When a pessoa cria, verifica e resolve os secrets
    Then `backup_chave`, `backup_r2_credentials` e `backup_avisos` são aceitos como nomes, com versão `_v<N>`
    And os valores entram só pela entrada padrão e nunca aparecem na saída
    And no ambiente local os três recebem valores fictícios sem perguntas
```

#### AC-015 — Declarar o serviço de backup no stack de produção

**Cobre**: US-004, FR-008, NFR-003

```gherkin
@US-004 @FR-008 @NFR-003 @AC-015
Feature: Backup automático do Postgres

  Scenario: Declarar o serviço de backup no stack de produção
    Given o arquivo `deploy/stack.prod.yml`
    When o stack é inspecionado
    Then existe o serviço `backup_ragpipeline`, preso ao nó de dados, sem portas publicadas
    And ele recebe só os três secrets de backup e a senha do Postgres
    And o serviço declara limite de tempo do job e não declara volume com o dump
```

#### AC-016 — Ensaiar o backup no Docker local

**Cobre**: US-004, FR-001, FR-008

```gherkin
@US-004 @FR-001 @FR-008 @AC-016
Feature: Backup automático do Postgres

  Scenario: Ensaiar o backup no Docker local
    Given o override `deploy/stack.local.yml` e os secrets `_local`
    When o ensaio local é preparado
    Then o override acrescenta um armazenamento compatível com S3 local no lugar do R2
    And os secrets de backup `_local` apontam para ele com valores fictícios
    And nenhuma credencial real nem endereço de produção é necessário
```

#### AC-017 — Reexecutar o ciclo no mesmo dia sem duplicar

**Cobre**: FR-001, FR-003, NFR-004

```gherkin
@FR-001 @FR-003 @NFR-004 @AC-017
Feature: Backup automático do Postgres

  Scenario: Reexecutar o ciclo no mesmo dia sem duplicar
    Given um backup do dia já existe no bucket
    When o ciclo de backup roda de novo no mesmo dia
    Then o objeto do dia é substituído, não duplicado
    And a contagem de diários na retenção não aumenta
    And o log registra a substituição
```

#### AC-018 — Agendar o ciclo para a madrugada

**Cobre**: FR-001, NFR-003, NFR-004

```gherkin
@FR-001 @NFR-003 @NFR-004 @AC-018
Feature: Backup automático do Postgres

  Scenario: Agendar o ciclo para a madrugada
    Given a hora configurada é 03:00 e o relógio marca outro horário
    When o agendador calcula a próxima execução
    Then a espera vai até a próxima 03:00, hoje ou amanhã
    And o ciclo não roda duas vezes na mesma janela
    And uma falha do ciclo não derruba o agendador, que espera a janela seguinte
```

#### AC-019 — Documentar onde a chave fica guardada

**Cobre**: US-003, FR-010, NFR-001

```gherkin
@US-003 @FR-010 @NFR-001 @AC-019
Feature: Backup automático do Postgres

  Scenario: Documentar onde a chave fica guardada
    Given o arquivo `deploy/BACKUP.md`
    When a pessoa lê a seção de chave de cifragem
    Then o documento diz que a chave fica fora da VPS, no gerenciador de senhas da pessoa responsável
    And explica que sem a chave o backup não pode ser restaurado
    And não contém nenhum valor de chave, senha ou credencial
```

#### AC-020 — Manter o log sem segredos

**Cobre**: US-002, FR-009, NFR-001

```gherkin
@US-002 @FR-009 @NFR-001 @AC-020
Feature: Backup automático do Postgres

  Scenario: Manter o log sem segredos
    Given um ciclo de backup com sucesso e outro com falha, com valores de segredo conhecidos
    When os logs e as mensagens de aviso são inspecionados
    Then nenhum valor de chave, senha, token ou credencial aparece
    And cada etapa registra início, fim e resultado
    And o log termina com uma linha de resumo do ciclo
```

#### AC-021 — Documentar a restauração e a conferência

**Cobre**: US-003, FR-007, FR-010

```gherkin
@US-003 @FR-007 @FR-010 @AC-021
Feature: Backup automático do Postgres

  Scenario: Documentar a restauração e a conferência
    Given o arquivo `deploy/BACKUP.md`
    When a pessoa procura como restaurar um backup
    Then há o passo a passo do script de restauração com o banco temporário
    And há a conferência do conteúdo restaurado antes de qualquer troca
    And há o aviso de que nunca se restaura sobre o banco de desenvolvimento ou de teste
```

#### AC-022 — Documentar avisos, falhas e operação

**Cobre**: US-002, FR-006, FR-010

```gherkin
@US-002 @FR-006 @FR-010 @AC-022
Feature: Backup automático do Postgres

  Scenario: Documentar avisos, falhas e operação
    Given o arquivo `deploy/BACKUP.md`
    When a pessoa procura o que fazer quando chega um aviso de falha
    Then há as causas prováveis por etapa e a ação para cada uma
    And há a retenção, o horário e como rodar um ciclo manual
    And há a verificação real com o R2 e o e-mail, feita pela pessoa na VPS fora do Delivery Gate
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O serviço de backup deve executar o ciclo de backup uma vez por dia, na hora configurada em `BACKUP_HORA` (padrão 03:00), gerando um dump `pg_dump` em formato custom do banco `rag_pipeline` sem parar nenhum serviço da aplicação e sem tomar bloqueios exclusivos.
- **FR-002**: O ciclo deve cifrar o dump com AES-256 e derivação PBKDF2 usando a chave do secret `backup_chave` antes de qualquer envio, manter o dump em claro somente num diretório temporário do job e removê-lo ao final, mesmo em falha.
- **FR-003**: O ciclo deve enviar o dump cifrado ao bucket de backup (distinto do bucket do sistema, com credencial própria) como `diarios/AAAA-MM-DD.dump.enc`, copiar para `semanais/AAAA-SWW.dump.enc` aos domingos, repetir o envio com espera entre tentativas e terminar com falha ao esgotá-las.
- **FR-004**: O ciclo deve verificar cada backup antes de aplicar a retenção: o objeto existe no bucket com o tamanho enviado, o tamanho supera o mínimo configurado, a cifragem abre com a chave e `pg_restore --list` lê o conteúdo.
- **FR-005**: O ciclo deve manter 7 backups diários e 4 semanais, removendo os mais antigos somente depois de o novo backup ser enviado e verificado, e nunca tocar em objetos fora dos prefixos `diarios/` e `semanais/`.
- **FR-006**: O ciclo deve avisar a falha de qualquer etapa por e-mail (SMTP) e por webhook de chat, tentando os dois canais de forma independente; o sucesso é registrado só no log.
- **FR-007**: O script `deploy/backup/restaurar.sh` deve baixar o objeto indicado, decifrar com a chave informada e restaurar num banco novo do servidor de destino indicado, nomeado `restauracao_AAAAMMDDHHMMSS` por padrão ou com o nome pedido em `--banco`, recusando nomes de banco já existentes e nunca apagando nem sobrescrevendo objetos.
- **FR-008**: O stack de produção deve declarar o serviço `backup_ragpipeline` preso ao nó de dados, com os secrets externos versionados `backup_chave`, `backup_r2_credentials` e `backup_avisos` provisionados por `deploy/secrets.sh`, e o override local deve permitir o ensaio com armazenamento S3 local e valores fictícios.
- **FR-009**: Cada ciclo deve registrar no log, sem segredos, o início, o fim e o resultado de cada etapa, o tamanho e os objetos enviados, a retenção aplicada e uma linha final de resumo.
- **FR-010**: A entrega deve incluir `deploy/BACKUP.md` com a guarda da chave fora da VPS, a restauração passo a passo, a retenção, o horário, o ciclo manual, o significado dos avisos e a verificação real na VPS, de modo que o runbook (BACKLOG-0032) possa referenciá-lo.

#### Não funcionais

- **NFR-001**: Nenhuma chave, senha, token, credencial ou dump em claro aparece em log, argumento de comando, mensagem de aviso, imagem ou repositório. **Verificação**: testes que injetam valores conhecidos e inspecionam logs, argumentos registrados pelos binários falsos, mensagens e arquivos versionados.
- **NFR-002**: Uma falha em qualquer etapa nunca remove nem altera backups anteriores; a retenção só roda depois de verificação aprovada. **Verificação**: testes com falha injetada em cada etapa conferindo o conteúdo do bucket falso.
- **NFR-003**: O ciclo não interrompe a aplicação e termina dentro do limite de tempo do job configurado (padrão 1 hora); o agendador sobrevive a falhas de um ciclo. **Verificação**: inspeção do stack (sem parada de serviços, limite de tempo) e teste do agendador com ciclo falho.
- **NFR-004**: O ciclo é idempotente no dia: reexecutá-lo substitui os mesmos objetos e não aumenta a contagem de backups. **Verificação**: teste que roda o ciclo duas vezes no mesmo dia e conta os objetos.

#### Erros e casos-limite

- Dump vazio, truncado ou que não abre com a chave → falha na verificação, sem retenção, backups anteriores intactos e aviso.
- Bucket indisponível → novas tentativas com espera; esgotadas, falha com aviso; a execução seguinte tenta de novo.
- Falha do e-mail ou do webhook → o outro canal ainda é tentado; a falha do canal é registrada no log.
- Chave ausente ou vazia no secret → o ciclo falha antes de gerar o dump e avisa.
- Restauração com objeto inexistente, chave errada ou nome de banco existente → recusa sem criar nada.
- Postgres inacessível → falha no dump, com aviso; nenhum objeto é enviado.
- Execução em domingo → cria também a cópia semanal; o mesmo dia reexecutado substitui os objetos.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- O stack `deploy/stack.prod.yml` define backend, frontend, worker, Postgres e Qdrant com secrets externos versionados; `deploy/secrets.sh` provisiona os secrets e `deploy/build_and_deploy.sh` constrói as imagens e faz o deploy.
- O override `deploy/stack.local.yml` ensaia o stack de produção na máquina com secrets `_local` e valores fictícios.
- Os testes de deploy usam binários falsos no `PATH` (`tests/_docker_falso.py`) e inspecionam o YAML; o runner é Pytest com Ruff.
- Os testes existentes `test_deploy_stack.py` e `test_deploy_secrets_script.py` fixam a lista de serviços e de secrets; eles são atualizados na entrega para incluir o serviço e os secrets de backup.

#### Arquitetura e módulos

- `deploy/backup/backup.sh`: um ciclo (dump, cifragem, envio, verificação, retenção, aviso).
- `deploy/backup/agendar.sh`: laço que calcula a próxima janela e chama o ciclo; sobrevive a falhas.
- `deploy/backup/restaurar.sh`: restauração em banco temporário novo.
- `deploy/backup/Dockerfile`: imagem enxuta (Postgres client, `openssl`, CLI S3, `curl`) usada pelo serviço.
- Os secrets são arquivos em `/run/secrets`: `backup_chave` (texto), `backup_r2_credentials` (variáveis de ambiente: chave de acesso, segredo, endpoint e bucket) e `backup_avisos` (variáveis: servidor e credenciais SMTP, remetente, destinatário e URL do webhook).
- O Swarm não tem agendador próprio; o serviço fica no ar com o laço do `agendar.sh`.

#### Migrations

- Não aplicável: nenhuma mudança de schema.

#### Models

- Não aplicável: nenhuma entidade persistente nova no banco.

#### Controllers e casos de uso

- Caso de uso "ciclo de backup" em `deploy/backup/backup.sh` com as etapas `dump`, `cifrar`, `enviar`, `verificar`, `reter`, `avisar`; cada etapa registra no log e a primeira falha encerra o ciclo e chama o aviso.
- Caso de uso "restaurar" em `deploy/backup/restaurar.sh`.

#### Views e experiência

- Não aplicável: sem interface para pessoas.

#### Queries e repositórios

- Não aplicável. O bucket de backup é a única fonte de verdade da retenção: a listagem dos prefixos `diarios/` e `semanais/` define o que é podado.

#### Jobs e processamento assíncrono

- O agendador executa o ciclo uma vez por janela; a idempotência vem de nomes de objeto determinados pela data. Falha do ciclo não derruba o agendador. Não há fila nem dead-letter: o aviso e a próxima janela são o mecanismo de recuperação.

#### Estrutura de arquivos

```text
specs/draft/0034-backup-automatico-do-postgres-de-producao/
  spec.md
  research/
deploy/
  BACKUP.md
  SECRETS.md
  secrets.sh
  stack.prod.yml
  stack.local.yml
  build_and_deploy.sh
  backup/
    Dockerfile
    backup.sh
    agendar.sh
    restaurar.sh
tests/
  _backup_falso.py
  test_deploy_backup_script.py
  test_deploy_backup_agendador_script.py
  test_deploy_restore_script.py
  test_deploy_backup_docs.py
  test_deploy_stack.py
  test_deploy_secrets_script.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Backup diário | `diarios/AAAA-MM-DD.dump.enc` no bucket de backup | Dump custom cifrado; no máximo 7; um por dia | Origem do backup semanal |
| Backup semanal | `semanais/AAAA-SWW.dump.enc` no bucket de backup | Cópia do backup de domingo; no máximo 4 | Copiado de um diário |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Backup do dia | Ausente | Ciclo conclui e verificação aprova | Presente e verificado | Só então a retenção roda |
| Backup do dia | Ausente | Falha em qualquer etapa | Ausente | Backups anteriores intactos; aviso disparado |
| Backup do dia | Presente | Ciclo reexecutado no mesmo dia | Substituído | Contagem de diários não aumenta |

#### Migração e retenção

- Sem migração. Retenção: 7 diários e 4 semanais, aplicada somente após verificação aprovada; objetos fora dos dois prefixos nunca são removidos.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega é um serviço agendado e scripts de operação; a pessoa interage por terminal (restauração), e-mail e chat (avisos).

#### Stack e convenções de interface

- Não aplicável.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável.

#### Menus e navegação principal

- Não aplicável: não há telas nem menus.

#### Formulários e ações

- Não aplicável.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Não aplicável | Não aplicável | Sem interface | Não aplicável | Não aplicável | Não aplicável | Não aplicável |

#### Estados e acessibilidade

- Não aplicável. As mensagens de aviso são texto simples, legíveis por leitor de tela e sem dependência de imagem.

#### Contrato CRUD

- Não aplicável: a entrega não administra registros por tela.

#### Revisão visual durante o desenvolvimento

- Não aplicável: a entrega não altera interface. Cada tarefa registra `Não aplicável` com esse motivo.

#### APIs expostas

- Nenhuma API HTTP. Contratos de linha de comando: `deploy/backup/backup.sh` (sem argumentos; configuração por variáveis e secrets; saída 0 sucesso, diferente de zero falha), `deploy/backup/agendar.sh` e `deploy/backup/restaurar.sh <objeto> --destino <endereço do servidor Postgres> [--banco <nome novo>]` (saída 0 sucesso, 1 uso ou validação, 2 falha de operação).

#### APIs externas utilizadas

- Bucket S3 compatível do Cloudflare R2 (listar, enviar, consultar tamanho, copiar, remover) com credencial própria do secret `backup_r2_credentials`, tentativas com espera e falha ao esgotar.
- Servidor SMTP e webhook HTTP de chat para os avisos, cada um com tempo limite e falha registrada sem derrubar o outro.

#### Documentação das APIs consultadas

- Nenhuma fonte externa consultada nesta etapa; o uso será conferido nos testes e no ensaio local.

#### Eventos e outros contratos

- Mensagem de aviso: assunto e texto com a etapa que falhou, a data e o código de saída, sem segredos. O webhook recebe JSON com os campos `text` e `content` para compatibilidade com canais comuns de chat.

### 11. Estratégia TDD

- **Unidade**: o cálculo da próxima janela do agendador.
- **Integração/contrato**: `backup.sh` e `restaurar.sh` rodam com `pg_dump`, `pg_restore`, `psql`, a CLI S3, `curl` e `date` simulados no `PATH`, com um bucket em memória que registra argumentos e entradas; o YAML do stack e do override e o `BACKUP.md` são inspecionados em testes de contrato.
- **BDD/aceite**: o Gherkin da seção 6 orienta o desenho dos testes; não há arquivos `.feature`.
- **Runner TDD**: Pytest (`uv run pytest`) e Ruff, como no restante do projeto.
- **E2E**: o ensaio local no Docker (tarefa de operação local) roda o ciclo real contra um armazenamento S3 local e um Postgres temporário e faz uma restauração de teste; fica como evidência manual dentro do Delivery Gate.
- **Verificação manual**: o uso real contra o R2, o SMTP e o chat de produção fica com a pessoa na VPS, fora do Delivery Gate (DEC-007).

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, FR-003, NFR-001, NFR-003, AC-001 | AC-001 na seção 6 | Gerar, cifrar e enviar o backup diário em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-001 FR-001 FR-002 FR-003 NFR-001 NFR-003 AC-001` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-001, FR-002, NFR-001, AC-002 | AC-002 na seção 6 | Nunca deixar o dump em claro fora do diretório temporário em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-001 FR-002 NFR-001 AC-002` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-001, FR-003, FR-005, NFR-004, AC-003 | AC-003 na seção 6 | Copiar o backup de domingo para a retenção semanal em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-001 FR-003 FR-005 NFR-004 AC-003` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-001, FR-004, FR-005, NFR-002, AC-004 | AC-004 na seção 6 | Manter 7 backups diários e 4 semanais em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-001 FR-004 FR-005 NFR-002 AC-004` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-001, FR-002, FR-004, AC-005 | AC-005 na seção 6 | Aprovar a verificação do backup em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-001 FR-002 FR-004 AC-005` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-001, US-002, FR-004, FR-005, NFR-002, AC-006 | AC-006 na seção 6 | Reprovar a verificação sem apagar o backup anterior em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-001 US-002 FR-004 FR-005 NFR-002 AC-006` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-001, US-002, FR-003, FR-006, NFR-002, AC-007 | AC-007 na seção 6 | Tentar de novo quando o bucket está indisponível em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-001 US-002 FR-003 FR-006 NFR-002 AC-007` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-002, FR-006, NFR-001, AC-008 | AC-008 na seção 6 | Avisar a falha por e-mail e por chat em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-002 FR-006 NFR-001 AC-008` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-002, FR-006, FR-009, AC-009 | AC-009 na seção 6 | Entregar o aviso pelo canal que funciona em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-002 FR-006 FR-009 AC-009` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-002, FR-006, FR-009, AC-010 | AC-010 na seção 6 | Registrar o sucesso só no log em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-002 FR-006 FR-009 AC-010` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-003, FR-007, NFR-001, AC-011 | AC-011 na seção 6 | Restaurar um backup num banco temporário em `tests/test_deploy_restore_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-003 FR-007 NFR-001 AC-011` | Observado em 2026-10-15: saída 127: `deploy/backup/restaurar.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-003, FR-007, NFR-002, AC-012 | AC-012 na seção 6 | Recusar objeto inexistente ou chave errada em `tests/test_deploy_restore_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-003 FR-007 NFR-002 AC-012` | Observado em 2026-10-15: saída 127: `deploy/backup/restaurar.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-003, FR-007, NFR-002, AC-013 | AC-013 na seção 6 | Nunca restaurar sobre um banco existente em `tests/test_deploy_restore_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-003 FR-007 NFR-002 AC-013` | Observado em 2026-10-15: saída 127: `deploy/backup/restaurar.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-004, FR-008, NFR-001, AC-014 | AC-014 na seção 6 | Provisionar os secrets do backup em `tests/test_deploy_secrets_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-004 FR-008 NFR-001 AC-014` | Observado em 2026-10-15: `deploy/secrets.sh` responde `Secret desconhecido: backup_chave` | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-004, FR-008, NFR-003, AC-015 | AC-015 na seção 6 | Declarar o serviço de backup no stack de produção em `tests/test_deploy_stack.py` com marcador próprio `SPECSFY: SPEC-0034 US-004 FR-008 NFR-003 AC-015` | Observado em 2026-10-15: o serviço `backup_ragpipeline` e o armazenamento S3 local ainda não existem em `deploy/stack.prod.yml` e `deploy/stack.local.yml` | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-004, FR-001, FR-008, AC-016 | AC-016 na seção 6 | Ensaiar o backup no Docker local em `tests/test_deploy_stack.py` com marcador próprio `SPECSFY: SPEC-0034 US-004 FR-001 FR-008 AC-016` | Observado em 2026-10-15: o serviço `backup_ragpipeline` e o armazenamento S3 local ainda não existem em `deploy/stack.prod.yml` e `deploy/stack.local.yml` | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| FR-001, FR-003, NFR-004, AC-017 | AC-017 na seção 6 | Reexecutar o ciclo no mesmo dia sem duplicar em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 FR-001 FR-003 NFR-004 AC-017` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| FR-001, NFR-003, NFR-004, AC-018 | AC-018 na seção 6 | Agendar o ciclo para a madrugada em `tests/test_deploy_backup_agendador_script.py` com marcador próprio `SPECSFY: SPEC-0034 FR-001 NFR-003 NFR-004 AC-018` | Observado em 2026-10-15: saída 127: `deploy/backup/agendar.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-003, FR-010, NFR-001, AC-019 | AC-019 na seção 6 | Documentar onde a chave fica guardada em `tests/test_deploy_backup_docs.py` com marcador próprio `SPECSFY: SPEC-0034 US-003 FR-010 NFR-001 AC-019` | Observado em 2026-10-15: `deploy/BACKUP.md` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-002, FR-009, NFR-001, AC-020 | AC-020 na seção 6 | Manter o log sem segredos em `tests/test_deploy_backup_script.py` com marcador próprio `SPECSFY: SPEC-0034 US-002 FR-009 NFR-001 AC-020` | Observado em 2026-10-15: saída 127: `deploy/backup/backup.sh` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-003, FR-007, FR-010, AC-021 | AC-021 na seção 6 | Documentar a restauração e a conferência em `tests/test_deploy_backup_docs.py` com marcador próprio `SPECSFY: SPEC-0034 US-003 FR-007 FR-010 AC-021` | Observado em 2026-10-15: `deploy/BACKUP.md` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |
| US-002, FR-006, FR-010, AC-022 | AC-022 na seção 6 | Documentar avisos, falhas e operação em `tests/test_deploy_backup_docs.py` com marcador próprio `SPECSFY: SPEC-0034 US-002 FR-006 FR-010 AC-022` | Observado em 2026-10-15: `deploy/BACKUP.md` ainda não existe | GREEN: suíte focal 68 passed em 2026-10-15 | Regressão focal passou; ensaio Docker aprovado |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-001 | AC-016 | Contrato | `tests/test_deploy_stack.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-001 | AC-017 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-001 | AC-018 | Unidade | `tests/test_deploy_backup_agendador_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-002 | AC-001 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-002 | AC-002 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-002 | AC-005 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-003 | AC-001 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-003 | AC-003 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-003 | AC-007 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-003 | AC-017 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-004 | AC-004 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-004 | AC-005 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-004 | AC-006 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-005 | AC-003 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-005 | AC-004 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-005 | AC-006 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-006 | AC-007 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-006 | AC-008 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-006 | AC-009 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-006 | AC-010 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-006 | AC-022 | Contrato | `tests/test_deploy_backup_docs.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-007 | AC-011 | Integração | `tests/test_deploy_restore_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-007 | AC-012 | Integração | `tests/test_deploy_restore_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-007 | AC-013 | Integração | `tests/test_deploy_restore_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-007 | AC-021 | Contrato | `tests/test_deploy_backup_docs.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-008 | AC-014 | Integração | `tests/test_deploy_secrets_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-008 | AC-015 | Contrato | `tests/test_deploy_stack.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-008 | AC-016 | Contrato | `tests/test_deploy_stack.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-009 | AC-009 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-009 | AC-010 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-009 | AC-020 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-010 | AC-019 | Contrato | `tests/test_deploy_backup_docs.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-010 | AC-021 | Contrato | `tests/test_deploy_backup_docs.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| FR-010 | AC-022 | Contrato | `tests/test_deploy_backup_docs.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-001 | AC-001 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-001 | AC-002 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-001 | AC-008 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-001 | AC-011 | Integração | `tests/test_deploy_restore_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-001 | AC-014 | Integração | `tests/test_deploy_secrets_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-001 | AC-019 | Contrato | `tests/test_deploy_backup_docs.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-001 | AC-020 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-002 | AC-004 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-002 | AC-006 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-002 | AC-007 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-002 | AC-012 | Integração | `tests/test_deploy_restore_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-002 | AC-013 | Integração | `tests/test_deploy_restore_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-003 | AC-001 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-003 | AC-015 | Contrato | `tests/test_deploy_stack.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-003 | AC-018 | Unidade | `tests/test_deploy_backup_agendador_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-004 | AC-003 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-004 | AC-017 | Integração | `tests/test_deploy_backup_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |
| NFR-004 | AC-018 | Unidade | `tests/test_deploy_backup_agendador_script.py` | Passed: suíte focal 68 passed em 2026-10-15 |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed em 2026-10-15
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0034-backup-automatico-do-postgres-de-producao/spec.md`
- **Achados**: 4 US, 10 FR, 4 NFR e 22 AC; cada US, FR e NFR tem pelo menos 3 AC em `**Cobre**`. Sem BLOCKER. WARNING resolvido: o AC-013 pressupunha `--banco`, agora declarado no FR-007 e no contrato da seção 10. WARNING resolvido: a Definition of Done passou a citar `STACK.md`, `PROJECT.md` e `DATABASE.md`. NOTE aceita: US-004 (P2) carrega o FR-008, mas o serviço no stack também é necessário à US-001; a ordem de tarefas já entrega o stack antes do ensaio.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`, severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed em 2026-10-15
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/planned/0034-backup-automatico-do-postgres-de-producao/spec.md`
- **Achados**: 32 tarefas (24 `[TEST]`, incluindo a regressão final, 5 `[CODE]`, 2 `[DOC]` e 1 `[OPS]`); 40 de 40 IDs cobertos; os 22 casos TDD (um por AC, cada um com marcador próprio) foram materializados em `tests/` e observaram RED válido em 2026-10-15, todos por comportamento ausente. Caminho crítico: T001–T022 → T023 → T024 → T025 → T028 → T029 → T030 → T032 → T031. Paralelo: T026 (restauração) e T027 (secrets).

#### Gate do Ato III — Entrega

- **Resultado**: Passed em 2026-10-15, para a SPEC-0034.
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0034-backup-automatico-do-postgres-de-producao/spec.md . --kinds US,FR,NFR,AC --full-chain`
- **Achados**: 32 tarefas concluídas, 40/40 IDs cobertos; 22 AC com QA Passed; evidência estrita e pesquisa aprovadas. Ensaio Docker, restauração e avisos aprovados. Regressão Python encerrada com reexecução bem-sucedida da única falha após a troca de imagem local; quatro casos novos também passaram na suíte focal. Checks do frontend e Ruff passaram. O benchmark pago da SPEC-0014 continua condicionado à execução explícita; falhas históricas da política global estão discriminadas abaixo e não pertencem à SPEC-0034.

#### Evidências locais da entrega — 2026-10-15

- `bash deploy/backup/ensaio.sh`: exit 0, ENSAIO APROVADO. PostgreSQL 16.10 real, OpenSSL real, CLI S3 real contra Moto 5.1.15 em rede Docker interna. Um objeto cifrado de 1728 bytes; repetição sem duplicata; banco novo `restauracao_ensaio` contém tabela `prova_backup` e registro esperado. Falha do dump preserva objeto anterior e chega por SMTP e webhook. Nenhum segredo real usado; ambiente próprio removido.
- `./deploy/secrets.sh criar backup_chave backup_r2_credentials backup_avisos --ambiente local`: exit 0; três secrets `_local_v1` conferidos e removidos ao encerrar o ensaio de provisionamento, sem alterar secrets preexistentes.
- `uv run pytest tests/test_deploy_backup_script.py tests/test_deploy_backup_agendador_script.py tests/test_deploy_restore_script.py tests/test_deploy_backup_docs.py tests/test_deploy_stack.py tests/test_deploy_secrets_script.py tests/test_deploy_build_and_deploy_script.py -q`: 68 passed, 2 avisos de depreciação, 38,13 s.
- RED adicional do AC-014: teste novo de aspas e metacaracteres falhou antes da correção de `ler_config`; o parser agora preserva o valor literal do secret e não executa seu conteúdo. GREEN na suíte focal de 68 casos.
- RED adicional do AC-001: binário falso corrigido para retornar 1 quando objeto exato não existe; teste falhou antes da correção de `publicar` e ficou GREEN na suíte focal. Retenção lista a raiz recursivamente, distingue prefixos gerenciados e mantém erros de rede fatais.
- `uv run pytest -q`: 623 passed, 1 skipped, 1 failed em 1160,39 s. A única falha foi o AC-016, cujo detector MinIO estava carregado antes da troca para Moto durante a execução. `uv run pytest --lf -q`: exit 0, 1 passed e 23 deselected em 1,60 s. A suíte focal final de 68 casos também passou e cobre os quatro novos testes ausentes na coleta inicial. O único skip pertence ao benchmark pago da SPEC-0014, não a esta entrega.
- `npm --prefix frontend run test:tdd`: exit 0, 58 arquivos e 236 testes passaram (337,89 s).
- `uv run ruff check`: exit 0. `npm --prefix frontend run lint`, `typecheck` e `build`: exit 0.
- A política global `verify_repo.mjs` retornou exit 1 por pendências em specs anteriores: rastreabilidade nas SPEC-0012, 0013, 0019, 0023 e 0026; índices relativos de pesquisa nas SPEC-0023 e 0030; validação estrita da SPEC-0031 ainda Draft. Nenhum desses arquivos foi alterado nesta entrega. Os checks próprios da SPEC-0034 (formato, tarefas, cadeia completa de rastreabilidade, aceite, evidência e pesquisa) passaram.
- Monitor CURRENT; documentador executado e `--check` passou. Sem interface visual ou mudança no schema da aplicação. A validação real do R2/SMTP/chat permanece com a pessoa após deploy na VPS, conforme DEC-007.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-003, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na seção 6 (Gerar, cifrar e enviar o backup diário), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-001 FR-001 FR-002 FR-003 NFR-001 NFR-003 AC-001`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-001, FR-002, FR-003, NFR-001, NFR-003, AC-001 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-001, FR-002, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na seção 6 (Nunca deixar o dump em claro fora do diretório temporário), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-001 FR-002 NFR-001 AC-002`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-002, NFR-001, AC-002 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-001, FR-003, FR-005, NFR-004, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na seção 6 (Copiar o backup de domingo para a retenção semanal), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-001 FR-003 FR-005 NFR-004 AC-003`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-003, FR-005, NFR-004, AC-003 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-001, FR-004, FR-005, NFR-002, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na seção 6 (Manter 7 backups diários e 4 semanais), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-001 FR-004 FR-005 NFR-002 AC-004`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-004, FR-005, NFR-002, AC-004 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-001, FR-002, FR-004, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na seção 6 (Aprovar a verificação do backup), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-001 FR-002 FR-004 AC-005`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-002, FR-004, AC-005 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-006 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-001, US-002, FR-004, FR-005, NFR-002, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na seção 6 (Reprovar a verificação sem apagar o backup anterior), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-001 US-002 FR-004 FR-005 NFR-002 AC-006`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, US-002, FR-004, FR-005, NFR-002, AC-006 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T007 [TEST] [TDD] [US-001] Derivar do AC-007 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-001, US-002, FR-003, FR-006, NFR-002, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na seção 6 (Tentar de novo quando o bucket está indisponível), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-001 US-002 FR-003 FR-006 NFR-002 AC-007`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, US-002, FR-003, FR-006, NFR-002, AC-007 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-002, FR-006, NFR-001, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na seção 6 (Avisar a falha por e-mail e por chat), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-002 FR-006 NFR-001 AC-008`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-006, NFR-001, AC-008 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-002, FR-006, FR-009, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na seção 6 (Entregar o aviso pelo canal que funciona), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-002 FR-006 FR-009 AC-009`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-006, FR-009, AC-009 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T010 [TEST] [TDD] [US-002] Derivar do AC-010 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-002, FR-006, FR-009, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 na seção 6 (Registrar o sucesso só no log), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-002 FR-006 FR-009 AC-010`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-006, FR-009, AC-010 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 um caso TDD falhando em tests/test_deploy_restore_script.py — Refs: US-003, FR-007, NFR-001, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 na seção 6 (Restaurar um backup num banco temporário), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_restore_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-003 FR-007 NFR-001 AC-011`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_restore_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/restaurar.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-007, NFR-001, AC-011 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso TDD falhando em tests/test_deploy_restore_script.py — Refs: US-003, FR-007, NFR-002, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012 na seção 6 (Recusar objeto inexistente ou chave errada), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_restore_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-003 FR-007 NFR-002 AC-012`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_restore_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/restaurar.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-007, NFR-002, AC-012 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-013 um caso TDD falhando em tests/test_deploy_restore_script.py — Refs: US-003, FR-007, NFR-002, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-013 na seção 6 (Nunca restaurar sobre um banco existente), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_restore_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-003 FR-007 NFR-002 AC-013`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_restore_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/restaurar.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-007, NFR-002, AC-013 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T014 [TEST] [TDD] [US-004] Derivar do AC-014 um caso TDD falhando em tests/test_deploy_secrets_script.py — Refs: US-004, FR-008, NFR-001, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-014 na seção 6 (Provisionar os secrets do backup), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_secrets_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-004 FR-008 NFR-001 AC-014`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_secrets_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, `deploy/secrets.sh` responde `Secret desconhecido: backup_chave`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-004, FR-008, NFR-001, AC-014 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T015 [TEST] [TDD] [US-004] Derivar do AC-015 um caso TDD falhando em tests/test_deploy_stack.py — Refs: US-004, FR-008, NFR-003, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-015 na seção 6 (Declarar o serviço de backup no stack de produção), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_stack.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-004 FR-008 NFR-003 AC-015`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_stack.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, o serviço `backup_ragpipeline` e o armazenamento S3 local ainda não existem em `deploy/stack.prod.yml` e `deploy/stack.local.yml`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-004, FR-008, NFR-003, AC-015 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T016 [TEST] [TDD] [US-004] Derivar do AC-016 um caso TDD falhando em tests/test_deploy_stack.py — Refs: US-004, FR-001, FR-008, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-016 na seção 6 (Ensaiar o backup no Docker local), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_stack.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-004 FR-001 FR-008 AC-016`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_stack.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, o serviço `backup_ragpipeline` e o armazenamento S3 local ainda não existem em `deploy/stack.prod.yml` e `deploy/stack.local.yml`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-004, FR-001, FR-008, AC-016 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T017 [TEST] [TDD] Derivar do AC-017 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: FR-001, FR-003, NFR-004, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-017 na seção 6 (Reexecutar o ciclo no mesmo dia sem duplicar), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 FR-001 FR-003 NFR-004 AC-017`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs FR-001, FR-003, NFR-004, AC-017 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T018 [TEST] [TDD] Derivar do AC-018 um caso TDD falhando em tests/test_deploy_backup_agendador_script.py — Refs: FR-001, NFR-003, NFR-004, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-018 na seção 6 (Agendar o ciclo para a madrugada), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_agendador_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 FR-001 NFR-003 NFR-004 AC-018`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_agendador_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/agendar.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs FR-001, NFR-003, NFR-004, AC-018 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T019 [TEST] [TDD] [US-003] Derivar do AC-019 um caso TDD falhando em tests/test_deploy_backup_docs.py — Refs: US-003, FR-010, NFR-001, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-019 na seção 6 (Documentar onde a chave fica guardada), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-003 FR-010 NFR-001 AC-019`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_docs.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, `deploy/BACKUP.md` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-010, NFR-001, AC-019 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T020 [TEST] [TDD] [US-002] Derivar do AC-020 um caso TDD falhando em tests/test_deploy_backup_script.py — Refs: US-002, FR-009, NFR-001, AC-020 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-020 na seção 6 (Manter o log sem segredos), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-002 FR-009 NFR-001 AC-020`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_script.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, saída 127: `deploy/backup/backup.sh` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-009, NFR-001, AC-020 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T021 [TEST] [TDD] [US-003] Derivar do AC-021 um caso TDD falhando em tests/test_deploy_backup_docs.py — Refs: US-003, FR-007, FR-010, AC-021 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-021 na seção 6 (Documentar a restauração e a conferência), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-003 FR-007 FR-010 AC-021`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_docs.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, `deploy/BACKUP.md` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-007, FR-010, AC-021 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T022 [TEST] [TDD] [US-002] Derivar do AC-022 um caso TDD falhando em tests/test_deploy_backup_docs.py — Refs: US-002, FR-006, FR-010, AC-022 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-022 na seção 6 (Documentar avisos, falhas e operação), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs`, porque o `conftest.py` da suíte exige `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_backup_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0034 US-002 FR-006 FR-010 AC-022`, usando os binários falsos de `tests/_backup_falso.py` quando o caso é de integração e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_backup_docs.py -q` e observar RED válido: falha por script, serviço, secret ou documento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-15: RED válido, `deploy/BACKUP.md` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-006, FR-010, AC-022 nas seções 11–13.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

#### Fase 2 — US-001, US-002 e FR-001 a FR-006, FR-009 (P1) — ciclo de backup

**Objetivo**: o ciclo gera, cifra, envia, verifica, poda e avisa.
**Teste independente**: `uv run pytest tests/test_deploy_backup_script.py tests/test_deploy_backup_agendador_script.py -q`.

- [x] T023 [TEST] Criar os binários falsos e o bucket em diretório usados pelos testes de backup em tests/_backup_falso.py — Refs: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-001 — Depends: none
  - [x] **PREP**: Confirmar os RED de backup e ler `tests/_docker_falso.py` para reaproveitar o padrão. Antes do `EXECUTE`, reconstruir `docs/` de forma independente com `$specsfy-documentator`.
  - [x] **EXECUTE**: Implementar `pg_dump`, `pg_restore`, `psql`, CLI S3, `curl` e `date` falsos, com bucket em memória em diretório temporário e registro de argumentos e entradas.
  - [x] **VERIFY**: Rodar `uv run pytest tests/test_deploy_backup_script.py -q` e conferir que a causa dos RED passou de infraestrutura de teste para comportamento ausente. Resultado em 2026-10-15: os casos de backup, restauração, stack, secrets e documentação falham por comportamento ausente, não por infraestrutura de teste; `uv run ruff check tests` passou.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar arquivos e comando; nenhum teste de comportamento passa ainda.
  - [x] **IMPROVE**: Manter os falsos pequenos e sem lógica de produção; justificar qualquer exceção.

- [x] T024 [CODE] Implementar o ciclo de backup em deploy/backup/backup.sh — Refs: AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-017, AC-020, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-009, NFR-001, NFR-002, NFR-003, NFR-004, US-001, US-002 — Depends: T023, T001, T002, T003, T004, T005, T006, T007, T008, T009, T010, T017, T020
  - [x] **PREP**: Confirmados os RED, contratos dos falsos e documentação reconstruída em 2026-10-15.  Confirmar os RED de `tests/test_deploy_backup_script.py` e os binários falsos. Antes do `EXECUTE`, reconstruir `docs/` de forma independente com `$specsfy-documentator`.
  - [x] **EXECUTE**: Implementados backup.sh e comum.sh; documentação reconstruída e check exit 0.  Implementar dump custom, cifragem AES-256 com PBKDF2, diretório temporário com limpeza por `trap`, envio com tentativas, cópia semanal aos domingos, verificação, retenção 7/4, aviso por SMTP e webhook e log sem segredos.
  - [x] **VERIFY**: GREEN: 12 testes do ciclo passaram (14,17 s).  Rodar `uv run pytest tests/test_deploy_backup_script.py -q` e a regressão focal de deploy.
  - [x] **VISUAL**: Não aplicável: apenas scripts operacionais, sem tela ou DOM.  `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: GREEN do ciclo; sem comandos destrutivos de banco; monitor CURRENT; docs check exit 0. PROJECT.md sem mudança nesta tarefa: capacidade será registrada na integração T032.  Registrar GREEN, arquivos alterados e a conferência de que o script não usa comandos destrutivos de banco.
  - [x] **IMPROVE**: Melhoria: funções comuns isoladas, sem executar o conteúdo dos secrets.  Extrair funções por etapa se o script passar de uma tela e meia; justificar a ausência de melhoria.

<!-- specsfy:evidence {"task": "T024", "refs": ["AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006", "AC-007", "AC-008", "AC-009", "AC-010", "AC-017", "AC-020", "FR-001", "FR-002", "FR-003", "FR-004", "FR-005", "FR-006", "FR-009", "NFR-001", "NFR-002", "NFR-003", "NFR-004", "US-001", "US-002"], "files": ["deploy/backup/backup.sh", "deploy/backup/comum.sh"], "commands": [{"run": "uv run pytest tests/test_deploy_backup_script.py -q", "exit": 0}]} -->


- [x] T025 [CODE] Implementar o agendador e a imagem do serviço em deploy/backup/agendar.sh — Refs: FR-001, NFR-003, NFR-004, AC-018 — Depends: T024, T018
  - [x] **PREP**: Confirmado RED do AC-018; Postgres 16; documentação atual.  Confirmar o RED do AC-018 e a imagem base do Postgres de produção (`postgres:16-alpine`). Antes do `EXECUTE`, reconstruir `docs/` de forma independente com `$specsfy-documentator`.
  - [x] **EXECUTE**: Agendador UTC e Dockerfile não root implementados; monitor CURRENT; docs check exit 0.  Implementar o cálculo da próxima janela com `BACKUP_HORA`, o laço que sobrevive a falhas e `deploy/backup/Dockerfile` com cliente Postgres, `openssl`, CLI S3 e `curl`.
  - [x] **VERIFY**: GREEN: 1 teste do agendador passou.  Rodar `uv run pytest tests/test_deploy_backup_agendador_script.py -q`.
  - [x] **VISUAL**: Não aplicável: agendador e imagem sem interface.  `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Janela UTC e sobrevivência a falhas verificadas; build e tamanho real serão registrados no ensaio T030. Base fixada em 16.10-alpine3.22; pacotes resolvidos pelo repositório Alpine 3.22.  Registrar GREEN, arquivos alterados e o tamanho esperado da imagem.
  - [x] **IMPROVE**: Melhoria: funções comuns isoladas, sem executar o conteúdo dos secrets.  Fixar versões da imagem base e dos pacotes; justificar a ausência de melhoria.

#### Fase 3 — US-003 e FR-007 (P1) — restauração

**Objetivo**: restaurar um backup num banco temporário novo, sem tocar em bancos existentes.
**Teste independente**: `uv run pytest tests/test_deploy_restore_script.py -q`.

<!-- specsfy:evidence {"task": "T025", "refs": ["FR-001", "NFR-003", "NFR-004", "AC-018"], "files": ["deploy/backup/agendar.sh", "deploy/backup/Dockerfile"], "commands": [{"run": "uv run pytest tests/test_deploy_backup_agendador_script.py -q", "exit": 0}]} -->


- [x] T026 [CODE] Implementar a restauração em banco temporário em deploy/backup/restaurar.sh — Refs: FR-007, NFR-001, NFR-002, US-003, AC-011, AC-012, AC-013 — Depends: T023, T011, T012, T013
  - [x] **PREP**: Confirmados AC-011 a AC-013 e RED prévio; documentação reconstruída.  Confirmar os RED de `tests/test_deploy_restore_script.py`. Antes do `EXECUTE`, reconstruir `docs/` de forma independente com `$specsfy-documentator`.
  - [x] **EXECUTE**: Restauração com validação prévia, identificadores restritos, banco novo e erro seguro; docs check exit 0.  Implementar download, decifragem, criação do banco `restauracao_AAAAMMDDHHMMSS`, recusa de nome existente, restauração sem opções que apagam objetos e limpeza do diretório temporário.
  - [x] **VERIFY**: GREEN: casos AC-011 a AC-013 verificados pelo runner.  Rodar `uv run pytest tests/test_deploy_restore_script.py -q`.
  - [x] **VISUAL**: Não aplicável: script de terminal sem interface gráfica.  `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: GREEN: 3 casos, 14,60 s; nenhum banco existente alterado; sem mudança na finalidade do PROJECT.md nem no schema.  Registrar GREEN e a conferência de que nenhum banco existente é tocado.
  - [x] **IMPROVE**: Melhoria: funções comuns isoladas, sem executar o conteúdo dos secrets.  Revisar as mensagens de erro para orientar a pessoa; justificar a ausência de melhoria.

#### Fase 4 — US-004 e FR-008 (P2) — secrets, stack e ensaio local

**Objetivo**: provisionar os secrets, declarar o serviço e ensaiar no Docker local.
**Teste independente**: `uv run pytest tests/test_deploy_stack.py tests/test_deploy_secrets_script.py -q`.

<!-- specsfy:evidence {"task": "T026", "refs": ["FR-007", "NFR-001", "NFR-002", "US-003", "AC-011", "AC-012", "AC-013"], "files": ["deploy/backup/restaurar.sh"], "commands": [{"run": "uv run pytest tests/test_deploy_restore_script.py -q", "exit": 0}]} -->


- [x] T027 [CODE] Aceitar os três secrets de backup no gerenciador de secrets em deploy/secrets.sh — Refs: US-004, FR-008, NFR-001, AC-014 — Depends: T014, T015, T016
  - [x] **PREP**: Confirmados contrato e RED do AC-014; docs atual.  Confirmar o RED do AC-014 e o contrato atual de `deploy/secrets.sh`. Antes do `EXECUTE`, reconstruir `docs/` de forma independente com `$specsfy-documentator`.
  - [x] **EXECUTE**: Secrets literais provisionados sem eco, valores locais fictícios e SECRETS.md atualizados; docs check exit 0; monitor CURRENT.  Acrescentar `backup_chave`, `backup_r2_credentials` e `backup_avisos` a `NOMES`, ao mapa de variáveis e à geração de valores fictícios do ambiente local, e atualizar `deploy/SECRETS.md`.
  - [x] **VERIFY**: GREEN: 15 testes do provisionador passaram (15,08 s).  Rodar `uv run pytest tests/test_deploy_secrets_script.py -q` e conferir que os testes existentes foram ajustados à nova lista.
  - [x] **VISUAL**: Não aplicável: gerenciador CLI sem tela.  `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Lista ampliada para sete secrets; helpers de regressão atualizados; sem impacto na finalidade de PROJECT.md; sem schema novo.  Registrar GREEN e arquivos alterados.
  - [x] **IMPROVE**: Melhoria: funções comuns isoladas, sem executar o conteúdo dos secrets.  Manter a ajuda e o documento com os mesmos nomes; justificar a ausência de melhoria.

<!-- specsfy:evidence {"task": "T027", "refs": ["US-004", "FR-008", "NFR-001", "AC-014"], "files": ["deploy/secrets.sh", "deploy/SECRETS.md", "tests/_docker_falso.py", "tests/test_deploy_secrets_script.py"], "commands": [{"run": "uv run pytest tests/test_deploy_secrets_script.py -q", "exit": 0}]} -->


- [x] T028 [CODE] Declarar o serviço de backup no stack e no override local em deploy/stack.prod.yml — Refs: US-004, FR-001, FR-008, NFR-001, NFR-003, AC-014, AC-015, AC-016 — Depends: T027, T025, T015, T016
  - [x] **PREP**: Confirmados contrato de placement, REDs de stack e imagem construída localmente.  Confirmar os RED de `tests/test_deploy_stack.py` e o stack atual. Antes do `EXECUTE`, reconstruir `docs/` de forma independente com `$specsfy-documentator`.
  - [x] **EXECUTE**: Declarar o serviço `backup_ragpipeline` no nó de dados, sem portas, com os secrets de backup e a senha do Postgres e limite de tempo; acrescentar o armazenamento S3 local e os secrets `_local` em `deploy/stack.local.yml`; construir a imagem em `deploy/build_and_deploy.sh`; ajustar a lista de serviços de `tests/test_deploy_stack.py`.
  - [x] **VERIFY**: GREEN em 2026-10-15: suíte conjunta de stack/build/documentação, 33 passed (3,40 s). Rodar `uv run pytest tests/test_deploy_stack.py tests/test_deploy_build_and_deploy_script.py -q`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Documentação reconstruída e check exit 0; monitor CURRENT. Registrar GREEN e arquivos alterados.
  - [x] **IMPROVE**: Override mantém S3 e SMTP fictícios restritos ao ambiente local; manual agora tem ensaio reproduzível. Conferir que o override local não é necessário em produção; justificar a ausência de melhoria.

<!-- specsfy:evidence {"task": "T028", "refs": ["US-004", "FR-001", "FR-008", "NFR-001", "NFR-003", "AC-014", "AC-015", "AC-016"], "files": ["deploy/stack.prod.yml", "deploy/stack.local.yml", "deploy/build_and_deploy.sh", "tests/test_deploy_stack.py", "tests/test_deploy_build_and_deploy_script.py"], "commands": [{"run": "uv run pytest tests/test_deploy_stack.py tests/test_deploy_build_and_deploy_script.py tests/test_deploy_backup_docs.py -q", "exit": 0}]} -->

#### Fase 5 — FR-010 — documentação

**Objetivo**: documentar a operação do backup para o runbook.
**Teste independente**: `uv run pytest tests/test_deploy_backup_docs.py -q`.

- [x] T029 [DOC] Escrever o documento de operação do backup em deploy/BACKUP.md — Refs: US-002, US-003, FR-006, FR-007, FR-010, NFR-001, AC-019, AC-021, AC-022 — Depends: T024, T026, T019, T021, T022
  - [x] **PREP**: Lidos AC-019, AC-021, AC-022 e contratos implementados.  Confirmar os RED de `tests/test_deploy_backup_docs.py` e o comportamento já implementado.
  - [x] **EXECUTE**: Documentar guarda da chave fora da VPS, restauração passo a passo, retenção, horário, ciclo manual, avisos e a verificação real na VPS, sem nenhum valor de segredo.
  - [x] **VERIFY**: GREEN em 2026-10-15: suíte conjunta de stack/build/documentação, 33 passed (3,40 s). Rodar `uv run pytest tests/test_deploy_backup_docs.py -q`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Documentação reconstruída e check exit 0; monitor CURRENT. Registrar GREEN e arquivo criado.
  - [x] **IMPROVE**: Override mantém S3 e SMTP fictícios restritos ao ambiente local; manual agora tem ensaio reproduzível. Conferir que o texto serve de referência para o runbook (BACKLOG-0032); justificar a ausência de melhoria.

<!-- specsfy:evidence {"task": "T029", "refs": ["US-002", "US-003", "FR-006", "FR-007", "FR-010", "NFR-001", "AC-019", "AC-021", "AC-022"], "files": ["deploy/BACKUP.md"], "commands": [{"run": "uv run pytest tests/test_deploy_backup_script.py tests/test_deploy_backup_agendador_script.py tests/test_deploy_restore_script.py tests/test_deploy_backup_docs.py tests/test_deploy_stack.py tests/test_deploy_secrets_script.py tests/test_deploy_build_and_deploy_script.py -q", "exit": 0}]} -->

#### Fase 6 — Ensaio local e qualidade

- [x] T030 [OPS] Ensaiar o ciclo e a restauração no Docker local em deploy/stack.local.yml — Refs: US-001, US-003, US-004, FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, FR-008, NFR-001, NFR-002, AC-001, AC-005, AC-011, AC-016 — Depends: T028, T029
  - [x] **PREP**: Proteção SAFE; Docker unix local confirmado; Postgres 16.10 temporário, Moto 5.1.15 e coletor em rede interna própria, sem portas. Secrets backup_*_local_v1 também criados pelo provisionador real e removidos após conferência, preservando os preexistentes.
  - [x] **EXECUTE**: Criado e executado `bash deploy/backup/ensaio.sh`: ciclo real, repetição no dia, restauração de `prova_backup` com registro conhecido e falha por banco inexistente com os dois avisos.
  - [x] **VERIFY**: ENSAIO APROVADO (exit 0): objeto cifrado de 1728 bytes; um diário após repetição; tabela e conteúdo restaurados; bucket preservado após falha; SMTP e webhook recebidos. Contêineres, volume anônimo e rede próprios removidos pelo trap.
  - [x] **VISUAL**: Não aplicável: ferramentas de operação sem alteração da interface da aplicação.
  - [x] **EVIDENCE**: Ensaio Docker em 2026-10-15; imagem 633730214 bytes, usuário postgres. Ver seção 13 para comandos, resultados e limites. Nenhum valor real de segredo utilizado.
  - [x] **IMPROVE**: Ensaio descobriu retorno 1 da CLI ao listar objeto/prefixo vazio: publicação e retenção corrigidas; binário falso alinhado e AC-001 reproduziu RED antes da correção. Coletor agora completa AUTH PLAIN. Moto substitui imagem MinIO inacessível; o ensaio recusa Docker remoto.

<!-- specsfy:evidence {"task": "T030", "refs": ["US-001", "US-003", "US-004", "FR-001", "FR-002", "FR-003", "FR-004", "FR-005", "FR-007", "FR-008", "NFR-001", "NFR-002", "AC-001", "AC-005", "AC-011", "AC-016"], "files": ["deploy/backup/ensaio.sh", "deploy/backup/coletor_local.py"], "commands": [{"run": "bash deploy/backup/ensaio.sh", "exit": 0}]} -->

- [x] T032 [DOC] Atualizar o contexto persistente do projeto em .specsfy/STACK.md — Refs: US-001, US-004, FR-008, NFR-001, AC-014, AC-015 — Depends: T028, T029
  - [x] **PREP**: Lidos STACK.md e PROJECT.md; persistência da aplicação preservada: sem tabela, campo, relação ou migration nova.
  - [x] **EXECUTE**: Stack registra cliente Postgres, Bash, OpenSSL, AWS CLI, curl, tini e Moto local; PROJECT.md registra backup diário cifrado fora da VPS.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check`: CURRENT. Documentação reconstruída e check exit 0.
  - [x] **VISUAL**: Não aplicável: somente contexto técnico sem interface.
  - [x] **EVIDENCE**: Atualizados `.specsfy/STACK.md` e `PROJECT.md`; `.specsfy/DATABASE.md` sem mudança, pois o schema da aplicação não muda; tabela do ensaio é descartável.
  - [x] **IMPROVE**: Distinguido S3 simulado por Moto do destino R2 de produção; sem dependência nova na aplicação.

<!-- specsfy:evidence {"task": "T032", "refs": ["US-001", "US-004", "FR-008", "NFR-001", "AC-014", "AC-015"], "files": [".specsfy/STACK.md", "PROJECT.md"], "commands": [{"run": "node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check", "exit": 0}]} -->

- [x] T031 [TEST] Executar regressão e rastreabilidade em tests/test_deploy_backup_script.py — Refs: US-001, US-002, US-003, US-004, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018, AC-019, AC-020, AC-021, AC-022 — Depends: T030, T032
  - [x] **PREP**: Identificados Pytest, Ruff, checks do frontend e validadores Specsfy; banco de teste separado confirmado SAFE.
  - [x] **EXECUTE**: Executados Pytest completo, reexecução da única falha, suíte focal final de 68 casos, Ruff, testes/tipos/lint/build do frontend e rastreabilidade completa.
  - [x] **VERIFY**: Regressão: 623 passed, 1 skipped, 1 falha na execução inicial; o único caso falho passou na reexecução (1 passed, 23 deselected). A execução longa carregara o detector antigo de MinIO antes da troca para Moto. Versão final coberta pelos 68 testes focais, inclusive os quatro adicionados após a coleta inicial. Único skip: benchmark pago da SPEC-0014, condicionado a RUN_SPEC0014_REAL; nenhum skip nesta spec.
  - [x] **VISUAL**: Não aplicável: scripts de backup, stack e documentação; nenhuma interface da aplicação alterada.
  - [x] **EVIDENCE**: Seção 13 registra comandos e resultados exatos; 236 testes frontend passaram; Ruff, lint, tipos e build passaram; 40/40 IDs e aceite passaram. Pendências da política global em specs anteriores registradas separadamente.
  - [x] **IMPROVE**: Ensaio real revelou diferenças da CLI S3 e do SMTP que os falsos não reproduziam; helpers corrigidos. Para próximas execuções longas, congelar a configuração de infraestrutura antes da coleta para evitar condição antiga em memória.

<!-- specsfy:evidence {"task": "T031", "refs": ["US-001", "US-002", "US-003", "US-004", "FR-001", "FR-002", "FR-003", "FR-004", "FR-005", "FR-006", "FR-007", "FR-008", "FR-009", "FR-010", "NFR-001", "NFR-002", "NFR-003", "NFR-004", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006", "AC-007", "AC-008", "AC-009", "AC-010", "AC-011", "AC-012", "AC-013", "AC-014", "AC-015", "AC-016", "AC-017", "AC-018", "AC-019", "AC-020", "AC-021", "AC-022"], "files": ["tests/test_deploy_backup_script.py", "tests/_backup_falso.py", "tests/test_deploy_build_and_deploy_script.py"], "commands": [{"run": "uv run pytest --lf -q", "exit": 0}, {"run": "uv run ruff check", "exit": 0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001–T022 (RED) → T023 → T024 → T025 → T028 → T029 → T030 → T032 → T031.
- Tarefas paralelas: `T026` (restauração) pode andar em paralelo com `T024` e `T025` depois dos binários falsos, porque usa arquivos distintos; `T027` (secrets) é independente do ciclo.
- Estratégia de MVP: US-001 e US-002 (ciclo com aviso) entregam o valor mínimo; US-003 fecha a recuperação; US-004 prova o conjunto no Docker local antes do deploy.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- `specs/completed/0027-provisionamento-de-secrets-do-swarm/` e `deploy/stack.prod.yml` (SPEC-0022): secrets externos versionados e Postgres como serviço do Swarm.
- BACKLOG-0032 (runbook) referencia o `deploy/BACKUP.md` desta entrega; não bloqueia.

#### Riscos

- Chave de cifragem perdida inutiliza todos os backups → mitigado por guardá-la fora da VPS e documentar onde (AC-019).
- Perda de até 24 horas de dados por causa da frequência diária → aceito no Beta; a frequência pode subir depois.
- Backup bom no ensaio e falho na VPS (R2, SMTP ou chat reais) → mitigado pela verificação real documentada para a pessoa fazer após o deploy e pelo aviso de falha.
- Dump grande estourar o limite de tempo do job → limite configurável e aviso de falha.

#### Suposições

- **Cifragem**: `openssl` com AES-256 e PBKDF2 e uma chave simétrica no secret `backup_chave`; sem dependência extra na imagem. Reversível por outra ferramenta sem mudar o contrato do bucket.
- **Job**: serviço do Swarm com laço agendador (o Swarm não tem cron), preso ao nó de dados.
- **Avisos**: SMTP genérico e webhook JSON genérico; o provedor concreto é configuração do secret `backup_avisos`.
- **Bucket**: nome e escopo ficam no secret `backup_r2_credentials`, com chave de acesso limitada a esse bucket.
- **Tamanho mínimo e tentativas**: mínimo de 1 KiB, 3 tentativas de envio com espera crescente, limite de tempo do job de 1 hora; todos configuráveis por variável.
- **Armazenamento local**: o ensaio usa um armazenamento compatível com S3 em contêiner, só no override local.

### 17. Decisões

- **DEC-001**: O destino é um bucket R2 separado do bucket do sistema, com credencial própria — o backup precisa sobreviver à perda da VPS e à troca da credencial do sistema (backlog, Pergunta 1).
- **DEC-002**: Retenção de 7 diários e 4 semanais, podada só após verificação — limita o custo e evita apagar o último backup bom (Pergunta 2).
- **DEC-003**: Dump cifrado antes de sair; chave fora da VPS e cópia no secret do job — o job precisa da chave para verificar; o risco de perda da chave é documentado (Pergunta 3).
- **DEC-004**: Cobertura só do Postgres — os vetores são derivados e os arquivos já estão no R2 (Pergunta 4).
- **DEC-005**: Avisos de falha por e-mail e webhook, tentados de forma independente; sucesso só no log (Pergunta 6).
- **DEC-006**: Restauração só em banco novo, sem opções destrutivas — protege o banco em uso e cumpre a proteção do banco de desenvolvimento (Pergunta 8 e PR-003, PR-004).
- **DEC-007**: A prova da entrega é o ensaio local no Docker; a verificação real no R2, no e-mail e no chat fica com a pessoa na VPS, fora do Delivery Gate — decisão de Marcio em 2026-10-15 de trabalhar local e fazer o deploy depois, mesmo padrão da SPEC-0027.
- **DEC-008**: Agendador em laço dentro de um serviço do Swarm, porque o Swarm não tem cron; alternativa descartada: tarefa do worker da aplicação, que acoplaria o backup à aplicação que ele protege.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/STACK.md` revisado: novo serviço `backup_ragpipeline`, imagem de backup (cliente Postgres, `openssl`, CLI S3) e ensaio com armazenamento S3 local.
- [x] `PROJECT.md` revisado: o Beta passa a ter backup diário cifrado fora da VPS (ou justificativa de ausência de impacto registrada na evidência).
- [x] `.specsfy/DATABASE.md` confirmado sem mudança: nenhuma tabela, campo, relação ou migration nova.
