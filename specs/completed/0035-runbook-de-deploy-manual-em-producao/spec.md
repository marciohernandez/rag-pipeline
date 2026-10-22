# Especificação integrada: Runbook de deploy manual em produção

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0035 |
| Slug | 0035-runbook-de-deploy-manual-em-producao |
| Status | Complete |
| Effort | 4 |
| Effort updated at | 2026-10-15 |
| Effort rationale | Um runbook em Markdown, uma mudança no `build_and_deploy.sh` (etiqueta por versão, poda das três últimas, reimplantação por `--versao`) e testes por contrato e com `docker` simulado; sem schema nem interface. O risco está em não podar a versão em uso e em manter o runbook fiel aos scripts; a execução real do runbook na VPS fica com a pessoa (perfil `standard`). |
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

O deploy do Beta é manual (decisão de 2026-09-28), mas não existe um processo documentado de como atualizar o sistema em produção sem quebrá-lo. O script `deploy/build_and_deploy.sh` constrói as imagens com a etiqueta fixa `:local`, que a próxima construção sobrescreve; por isso não há como voltar a uma versão anterior. As migrações do banco (`alembic`) não têm passo documentado e nada confere se há lote em andamento antes de atualizar. Origem: `specs/backlog/0032-runbook-de-deploy-manual-em-producao.md` (BACKLOG-0032), com as oito decisões de 2026-10-13.

#### Resultado desejado

Existe `deploy/RUNBOOK.md`, com passo a passo repetível para atualizar, instalar pela primeira vez e agir em emergências, e o `build_and_deploy.sh` etiqueta cada imagem pela versão (o commit), guarda as três últimas e reimplanta uma versão anterior por `--versao`. Um teste automático impede o runbook de citar o que não existe, e a pessoa responsável executa o runbook inteiro uma vez na VPS.

#### Métricas de sucesso

- 100% dos arquivos, flags, subcomandos, serviços e secrets citados no runbook existem no repositório, conferido pelo teste automático.
- Voltar à versão anterior leva um único comando (`deploy/build_and_deploy.sh --versao <etiqueta>`) e não constrói imagem.
- Cada imagem do projeto mantém no máximo três versões etiquetadas no nó após um deploy bem-sucedido.
- Zero segredo ou domínio real no runbook e nas saídas do script.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: como o deploy é feito hoje → `deploy/build_and_deploy.sh` confere os secrets, constrói as imagens com `:local` e roda `docker stack deploy --resolve-image never`; o stack usa `image: rag-pipeline-*:local`. Impacto: a volta atrás exige etiqueta por versão e `stack.prod.yml` parametrizado.
- **R-002**: onde ficam as migrações → há `alembic/` e `alembic.ini` na imagem do backend e `alembic/env.py` lê `APP_DATABASE_URL`, mas o comando do serviço sobe o `uvicorn` sem migrar e nenhum documento descreve `alembic upgrade`. Impacto: a migração é um passo manual novo no runbook.
- **R-003**: como saber se há lote em andamento → a tabela `executions` tem a situação `pending`/`running` (índice parcial `uq_executions_base_active`, SPEC-0015). Impacto: o runbook usa uma consulta somente de leitura a essa tabela.

#### Fontes e contexto consultados

- `specs/backlog/0032-runbook-de-deploy-manual-em-producao.md` e `specs/milestones/M03.md`.
- `deploy/build_and_deploy.sh`, `deploy/stack.prod.yml`, `deploy/stack.local.yml`, `deploy/secrets.sh`, `deploy/conferir_dominio.sh`, `deploy/backup/restaurar.sh`.
- `deploy/SECRETS.md` e `deploy/BACKUP.md` (formato e tom a seguir) e os testes `tests/test_deploy_*.py`.
- `alembic/env.py` e `src/app/models.py` (`Execution`).
- Nenhuma fonte externa.

#### Documentação consultada

- Documentação local do repositório listada acima; sem documentação externa.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: onde fica o runbook? → **A**: `deploy/RUNBOOK.md`, ao lado do `SECRETS.md` (backlog, Pergunta 1).
- **Q**: o que o runbook cobre? → **A**: atualização, primeira instalação e emergências (volta atrás e restauração), apontando o script de conferência do domínio (Pergunta 2).
- **Q**: como se volta atrás? → **A**: imagens etiquetadas pela versão, últimas três guardadas, `docker service rollback` como emergência (Pergunta 3).
- **Q**: e as migrações? → **A**: passo manual separado, depois de um backup, antes do deploy (Pergunta 4).
- **Q**: como se verifica? → **A**: `conferir_dominio.sh` e checagem rápida a cada deploy; lista completa na primeira instalação e em mudança grande (Pergunta 5).
- **Q**: quando se faz o deploy? → **A**: só sem lote em andamento (Pergunta 6).
- **Q**: quem faz? → **A**: só a pessoa responsável por acesso remoto; o runbook marca o que mudaria para delegar (Pergunta 7).
- **Q**: como se prova? → **A**: teste automático das citações e uma execução única do runbook na VPS (Pergunta 8).

#### Dúvidas abertas

- Nenhuma. As três dúvidas operacionais do backlog foram resolvidas como suposições reversíveis (seção 16) e decisões (DEC-002, DEC-003, DEC-005).

### 3. Escopo e atores

#### Incluído

- `deploy/RUNBOOK.md` com as áreas de atualização, primeira instalação e emergências.
- Mudança de `deploy/build_and_deploy.sh` e de `deploy/stack.prod.yml` (e `deploy/stack.local.yml` quando consumir as mesmas variáveis) para etiquetar por versão, guardar as três últimas e reimplantar por `--versao`.
- Teste automático das citações do runbook e testes do script com `docker` simulado.
- Atualização de `deploy/SECRETS.md` e `deploy/BACKUP.md` com a ligação para o runbook, quando necessário.
- A execução única do runbook pela pessoa responsável na VPS, fora do Delivery Gate (DEC-004).

#### Fora de escopo

- Deploy automático (CI/CD).
- Delegação do deploy a outras pessoas: apenas marcada no runbook.
- Teste automático periódico de restauração.
- Mudança nos itens 0029 (domínio) e 0031/0034 (backup) além de serem apontados.
- Registro de deploys e aviso à equipe antes do deploy.
- Distribuição de imagens entre nós do Swarm (um único nó nesta fase).

#### Atores

- **Marcio (pessoa responsável)**: faz o deploy por acesso remoto à VPS, decide voltar atrás e restaura o banco.
- **Equipe de consultoria**: usa o Beta; é afetada por atualização mal feita, mas não opera o deploy.

### 4. Princípios e restrições do projeto

- **PR-001**: nenhum segredo é escrito em documento, argumento, log ou stack file; segredos entram só por `deploy/secrets.sh` (SPEC-0027).
- **PR-002**: nenhuma etapa usa comando que apague, recrie ou zere banco ou schema; a restauração só cria um banco novo (SPEC-0034).
- **PR-003**: o runbook cita somente arquivos, flags, serviços e secrets que existem, e o teste impede que isso se perca.
- **PR-004**: o deploy só acontece com o repositório limpo e em um commit identificável.
- **PR-005**: o workflow é Specsfy, com testes escritos antes (Pytest) e Ruff a cada integração.

### 5. Histórias de usuário

#### US-001 — Atualizar a produção seguindo um passo a passo (P1)

Como Marcio (pessoa responsável), quero atualizar o sistema em produção por um passo a passo conferido e repetível, para reduzir o risco de erro humano no deploy sem quebrar o Beta.

**Por que P1**: Atualizar o ambiente sem lote em andamento é o uso mais frequente e o que mais arrisca o Beta.
**Teste independente**: Seguir a área de atualização do runbook e ver o sistema responder pelo script de conferência.
**Requisitos**: FR-001, FR-002, FR-003, FR-007

#### US-002 — Voltar a uma versão anterior (P1)

Como Marcio (pessoa responsável), quero voltar a uma versão anterior das imagens quando o deploy der errado, para recuperar o Beta em minutos, sem reconstruir nada às pressas.

**Por que P1**: Sem versão etiquetada não há volta atrás confiável; a etiqueta fixa `:local` é sobrescrita a cada build.
**Teste independente**: Fazer dois deploys e reimplantar o primeiro com `--versao`.
**Requisitos**: FR-004, FR-005, FR-006, FR-009

#### US-003 — Instalar pela primeira vez (P2)

Como Marcio (pessoa responsável), quero seguir um roteiro de primeira instalação na VPS, para chegar a um Beta funcionando e verificado, na ordem certa.

**Por que P2**: A primeira instalação tem dependências entre secrets, domínio, chave do backup e migração; fora de ordem ela falha tarde.
**Teste independente**: Ler a área de primeira instalação e conferir que cada passo cita um arquivo ou script existente.
**Requisitos**: FR-001, FR-003, FR-007

#### US-004 — Agir numa emergência (P2)

Como Marcio (pessoa responsável), quero saber como agir quando o deploy ou a migração falha, para voltar à versão anterior e, se preciso, restaurar o backup sem improvisar.

**Por que P2**: Na hora do erro não há tempo de redescobrir o caminho; o backup só vale se a restauração estiver ao alcance.
**Teste independente**: Seguir a área de emergências após uma verificação reprovada simulada.
**Requisitos**: FR-006, FR-008

### 6. Cenários BDD de aceite

#### AC-001 — Documentar as três áreas do runbook

**Cobre**: US-001, US-003, US-004, FR-001, NFR-003

```gherkin
@US-001 @US-003 @US-004 @FR-001 @NFR-003 @AC-001
Feature: Documentar as três áreas do runbook

  Scenario: Documentar as três áreas do runbook
    Given o repositório com `deploy/SECRETS.md` e `deploy/BACKUP.md`
    When a pessoa responsável abre `deploy/RUNBOOK.md`
    Then o documento traz as áreas de atualização, primeira instalação e emergências, cada uma em passos numerados
```

#### AC-002 — Ordenar a atualização de produção

**Cobre**: US-001, FR-002, FR-003

```gherkin
@US-001 @FR-002 @FR-003 @AC-002
Feature: Ordenar a atualização de produção

  Scenario: Ordenar a atualização de produção
    Given a área de atualização do runbook
    When a pessoa lê os passos em ordem
    Then as pré-condições vêm antes do backup, do backup antes da migração, da migração antes do deploy e do deploy antes da verificação
```

#### AC-003 — Conferir que não há lote em andamento

**Cobre**: US-001, FR-002, NFR-002

```gherkin
@US-001 @FR-002 @NFR-002 @AC-003
Feature: Conferir que não há lote em andamento

  Scenario: Conferir que não há lote em andamento
    Given o passo de pré-condições do runbook
    When a pessoa o executa antes do deploy
    Then ele consulta, somente para leitura, as execuções `pending` e `running` na tabela `executions`; com lote em andamento o runbook manda esperar e não seguir
```

#### AC-004 — Fazer a migração como passo separado e protegido

**Cobre**: US-001, US-004, FR-002, FR-003, FR-008

```gherkin
@US-001 @US-004 @FR-002 @FR-003 @FR-008 @AC-004
Feature: Fazer a migração como passo separado e protegido

  Scenario: Fazer a migração como passo separado e protegido
    Given um deploy que inclui migração
    When a pessoa segue o runbook
    Then a migração é um passo manual antes do deploy, só depois de um backup recente; se ela falhar o serviço não é atualizado e o runbook aponta a restauração do backup feito antes
```

#### AC-005 — Etiquetar cada imagem pela versão

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-005
Feature: Etiquetar cada imagem pela versão

  Scenario: Etiquetar cada imagem pela versão
    Given o repositório sem alterações não commitadas e os binários `docker` simulados
    When `deploy/build_and_deploy.sh` roda
    Then as imagens de backend, frontend e backup são construídas com a etiqueta do commit curto e o stack é implantado com essa mesma etiqueta
```

#### AC-006 — Recusar o deploy com a árvore suja

**Cobre**: US-002, FR-004, NFR-003

```gherkin
@US-002 @FR-004 @NFR-003 @AC-006
Feature: Recusar o deploy com a árvore suja

  Scenario: Recusar o deploy com a árvore suja
    Given arquivos alterados e não commitados no repositório
    When `deploy/build_and_deploy.sh` roda
    Then ele recusa antes de qualquer build e de `docker stack deploy`, dizendo que a versão não identificaria o código
```

#### AC-007 — Guardar as três últimas versões de cada imagem

**Cobre**: US-002, FR-005

```gherkin
@US-002 @FR-005 @AC-007
Feature: Guardar as três últimas versões de cada imagem

  Scenario: Guardar as três últimas versões de cada imagem
    Given cinco versões antigas de cada imagem no nó e um deploy bem-sucedido
    When a poda roda ao final do script
    Then ficam as três mais recentes de cada imagem e as demais são removidas
```

#### AC-008 — Voltar atrás reimplantando uma versão guardada

**Cobre**: US-002, FR-006

```gherkin
@US-002 @FR-006 @AC-008
Feature: Voltar atrás reimplantando uma versão guardada

  Scenario: Voltar atrás reimplantando uma versão guardada
    Given uma versão anterior guardada no nó
    When `deploy/build_and_deploy.sh --versao <etiqueta>` roda
    Then ele não constrói nada, confere os secrets e implanta o stack com a etiqueta pedida
```

#### AC-009 — Recusar uma versão que não existe

**Cobre**: US-002, FR-006, NFR-003

```gherkin
@US-002 @FR-006 @NFR-003 @AC-009
Feature: Recusar uma versão que não existe

  Scenario: Recusar uma versão que não existe
    Given uma etiqueta que não existe para alguma das imagens
    When `deploy/build_and_deploy.sh --versao <etiqueta>` roda
    Then ele recusa antes de implantar e lista as versões disponíveis
```

#### AC-010 — Verificar o deploy com o script de domínio

**Cobre**: US-001, US-003, FR-007

```gherkin
@US-001 @US-003 @FR-007 @AC-010
Feature: Verificar o deploy com o script de domínio

  Scenario: Verificar o deploy com o script de domínio
    Given o passo de verificação do runbook
    When a pessoa o executa depois do deploy
    Then o runbook manda rodar `deploy/conferir_dominio.sh` e a checagem rápida de login e assistente; a lista completa fica para a primeira instalação e para mudança grande
```

#### AC-011 — Instalar pela primeira vez

**Cobre**: US-003, FR-001, FR-003, FR-007

```gherkin
@US-003 @FR-001 @FR-003 @FR-007 @AC-011
Feature: Instalar pela primeira vez

  Scenario: Instalar pela primeira vez
    Given a área de primeira instalação do runbook
    When a pessoa lê os passos em ordem
    Then vêm secrets, domínio e HTTPS, chave do backup, migração do banco novo, deploy e a lista completa de verificação (login, criar Pessoa, subir uma Base e conversar com o assistente)
```

#### AC-012 — Reagir a uma verificação reprovada

**Cobre**: US-001, US-004, FR-006, FR-007, FR-008

```gherkin
@US-001 @US-004 @FR-006 @FR-007 @FR-008 @AC-012
Feature: Reagir a uma verificação reprovada

  Scenario: Reagir a uma verificação reprovada
    Given uma verificação que reprova depois do deploy
    When a pessoa consulta a área de emergências
    Then o runbook manda voltar à versão anterior, cita `docker service rollback` como comando de emergência e, se o banco foi afetado, aponta `deploy/BACKUP.md` e `restaurar.sh`
```

#### AC-013 — Nunca usar comando destrutivo de banco como rotina

**Cobre**: US-004, FR-008, NFR-002

```gherkin
@US-004 @FR-008 @NFR-002 @AC-013
Feature: Nunca usar comando destrutivo de banco como rotina

  Scenario: Nunca usar comando destrutivo de banco como rotina
    Given o texto completo do runbook
    When um teste o varre
    Then nenhum comando que apaga, recria ou zera banco ou schema aparece como passo; a restauração só cria um banco novo
```

#### AC-014 — Manter segredos e domínio fora do runbook

**Cobre**: FR-001, FR-009, NFR-001

```gherkin
@FR-001 @FR-009 @NFR-001 @AC-014
Feature: Manter segredos e domínio fora do runbook

  Scenario: Manter segredos e domínio fora do runbook
    Given o texto completo do runbook
    When um teste o varre
    Then ele não contém segredo, chave, endereço de bucket nem o domínio real, só nomes de variável e de secret
```

#### AC-015 — Detectar referência quebrada

**Cobre**: US-001, FR-009, NFR-003

```gherkin
@US-001 @FR-009 @NFR-003 @AC-015
Feature: Detectar referência quebrada

  Scenario: Detectar referência quebrada
    Given um runbook que cita scripts, flags, stack e secrets
    When o teste confere cada citação contra o repositório
    Then uma citação de arquivo, flag ou secret que não existe reprova o teste
```

#### AC-016 — Conferir flags e comandos citados nos scripts

**Cobre**: US-002, FR-009

```gherkin
@US-002 @FR-009 @AC-016
Feature: Conferir flags e comandos citados nos scripts

  Scenario: Conferir flags e comandos citados nos scripts
    Given o runbook que cita `--versao` e os subcomandos de `deploy/secrets.sh`
    When o teste lê os scripts
    Then cada flag e subcomando citado existe no script correspondente
```

#### AC-017 — Manter as saídas do script sem segredo

**Cobre**: FR-004, NFR-001

```gherkin
@FR-004 @NFR-001 @AC-017
Feature: Manter as saídas do script sem segredo

  Scenario: Manter as saídas do script sem segredo
    Given valores sentinela nos secrets e nas variáveis de ambiente
    When `deploy/build_and_deploy.sh` roda, com sucesso e com falha
    Then nenhum valor sentinela aparece na saída nem nos argumentos dos comandos `docker`
```

#### AC-018 — Podar só depois de um deploy bem-sucedido

**Cobre**: US-002, FR-005, NFR-002

```gherkin
@US-002 @FR-005 @NFR-002 @AC-018
Feature: Podar só depois de um deploy bem-sucedido

  Scenario: Podar só depois de um deploy bem-sucedido
    Given um `docker stack deploy` que falha
    When o script termina
    Then nenhuma imagem é removida e as versões anteriores continuam disponíveis para voltar
```

#### AC-019 — Nunca podar a versão em uso nem a de retorno

**Cobre**: US-002, FR-005, FR-006

```gherkin
@US-002 @FR-005 @FR-006 @AC-019
Feature: Nunca podar a versão em uso nem a de retorno

  Scenario: Nunca podar a versão em uso nem a de retorno
    Given a versão implantada e a anterior entre as guardadas
    When a poda roda
    Then essas versões não são removidas, mesmo que as outras sobrem além de três
```

#### AC-020 — Citar nomes e comandos que existem

**Cobre**: FR-009, NFR-003

```gherkin
@FR-009 @NFR-003 @AC-020
Feature: Citar nomes e comandos que existem

  Scenario: Citar nomes e comandos que existem
    Given os serviços e secrets citados no runbook
    When o teste lê `deploy/stack.prod.yml`
    Then cada serviço e cada secret citado existe no stack
```

#### AC-021 — Não pedir segredo na linha de comando

**Cobre**: NFR-001

```gherkin
@NFR-001 @AC-021
Feature: Não pedir segredo na linha de comando

  Scenario: Não pedir segredo na linha de comando
    Given os passos do runbook que criam ou trocam secrets
    When a pessoa os executa
    Then eles usam `deploy/secrets.sh`, cujo valor entra pela entrada padrão, e nenhum comando recebe o valor como argumento
```

#### AC-022 — Limitar a poda às imagens do projeto

**Cobre**: NFR-002

```gherkin
@NFR-002 @AC-022
Feature: Limitar a poda às imagens do projeto

  Scenario: Limitar a poda às imagens do projeto
    Given outras imagens e volumes no nó, entre eles os dados
    When a poda roda
    Then só as etiquetas antigas das três imagens do projeto são removidas; nenhum volume, rede ou outra imagem é tocado
```

#### AC-023 — Sugerir a delegação sem implementá-la

**Cobre**: US-001, US-003, FR-001

```gherkin
@US-001 @US-003 @FR-001 @AC-023
Feature: Sugerir a delegação sem implementá-la

  Scenario: Sugerir a delegação sem implementá-la
    Given o runbook
    When a pessoa procura quem pode fazer o deploy
    Then o documento diz que só a pessoa responsável faz e marca o que mudaria para delegar (acessos, chaves e registro de deploys)
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve manter `deploy/RUNBOOK.md` com as áreas de atualização, primeira instalação e emergências, cada uma em passos numerados e com a delegação apenas marcada.
- **FR-002**: O runbook deve exigir, antes do deploy, as pré-condições: Ruff, Pytest e build do frontend verdes, backup recente e nenhum lote em andamento, conferido por consulta somente para leitura às execuções `pending` e `running`.
- **FR-003**: O runbook deve tratar a migração como passo manual separado, antes do deploy e depois de um backup recente, e só atualizar o serviço depois da conferência.
- **FR-004**: `deploy/build_and_deploy.sh` deve etiquetar as imagens de backend, frontend e backup com o commit curto, recusar árvore com alterações não commitadas antes de qualquer build e implantar o stack com essa etiqueta.
- **FR-005**: `deploy/build_and_deploy.sh` deve manter as três versões mais recentes de cada imagem, podar as mais antigas só depois de um deploy bem-sucedido e nunca podar a versão em uso nem a de retorno.
- **FR-006**: `deploy/build_and_deploy.sh --versao <etiqueta>` deve reimplantar uma versão guardada sem construir, conferindo os secrets, e recusar uma etiqueta inexistente listando as disponíveis; o runbook cita `docker service rollback` como comando de emergência.
- **FR-007**: O runbook deve mandar rodar `deploy/conferir_dominio.sh` e a checagem rápida de login e assistente a cada deploy, e a lista completa (login, criar Pessoa, subir uma Base e conversar com o assistente) na primeira instalação e depois de mudança grande.
- **FR-008**: O runbook deve apontar `deploy/BACKUP.md` e `restaurar.sh` para a restauração, sem comando que apague, recrie ou zere banco ou schema como passo de rotina.
- **FR-009**: O repositório deve ter um teste automático que confere que os arquivos, as flags, os subcomandos, os serviços e os secrets citados no runbook existem, e que o runbook não contém segredo nem o domínio real.

#### Não funcionais

- **NFR-001**: Segurança: nenhum segredo, chave, endereço de bucket ou domínio real em `deploy/RUNBOOK.md`, nas saídas nem nos argumentos de `deploy/build_and_deploy.sh`. **Verificação**: varredura por teste do texto do runbook e da saída e dos argumentos do script com valores sentinela.
- **NFR-002**: Proteção do banco: o runbook e o script não executam nem sugerem como rotina comando que apague, recrie ou zere banco, schema, volume ou rede; a poda alcança só etiquetas antigas das imagens do projeto. **Verificação**: varredura por teste do runbook e do script, e teste da poda com outras imagens e volumes presentes.
- **NFR-003**: Verificabilidade e falha segura: o runbook não envelhece sem o teste perceber, e o script recusa, antes de qualquer build ou deploy, árvore suja e etiqueta inexistente. **Verificação**: testes de referência cruzada com o repositório e testes do script com `docker` simulado.

#### Erros e casos-limite

- Lote `pending` ou `running` na hora do deploy → o runbook manda esperar e não seguir.
- Árvore com alterações não commitadas → o script recusa antes de qualquer build.
- Etiqueta pedida em `--versao` não existe para alguma das imagens → o script recusa e lista as disponíveis.
- `docker stack deploy` falha → nenhuma versão é podada e o runbook manda voltar à versão anterior.
- Migração falha → o serviço não é atualizado e o runbook aponta a restauração do backup feito antes.
- Primeira execução, com menos de três versões no nó → a poda não remove nada.
- Verificação reprovada depois do deploy → voltar à versão anterior; se o banco foi afetado, restaurar o último backup.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- `deploy/build_and_deploy.sh` (bash, `set -euo pipefail`) confere os secrets, constrói `rag-pipeline-backend:local`, `rag-pipeline-frontend:local` e `rag-pipeline-backup:local` (esta no nó de dados, por `BACKUP_DOCKER_CONTEXT` quando difere) e roda `docker stack deploy --resolve-image never -c deploy/stack.prod.yml rag-pipeline`.
- `deploy/stack.prod.yml` referencia as três imagens com `:local`; `postgres:16-alpine` e `qdrant/qdrant:v1.10.1` já têm versão fixa.
- Os testes de deploy usam `docker` simulado (`tests/_docker_falso.py`) e inspecionam o YAML (`tests/test_deploy_stack.py`); o formato de documentos de operação é `deploy/SECRETS.md` e `deploy/BACKUP.md`, com teste de contrato em `tests/test_deploy_backup_docs.py`.
- O banco de teste é separado do de desenvolvimento (`.env.testing`).

#### Arquitetura e módulos

- `deploy/RUNBOOK.md`: documento único, três áreas (atualização, primeira instalação, emergências), em passos numerados, citando scripts e arquivos por caminho.
- `deploy/build_and_deploy.sh`: calcula `VERSAO_IMAGEM` (commit curto), recusa árvore suja, constrói e etiqueta as três imagens com a versão, implanta o stack com `VERSAO_IMAGEM`, depois poda as etiquetas antigas das três imagens mantendo as três mais recentes, a em uso e a de retorno. A versão de retorno é a etiqueta da imagem do serviço no momento em que o script começa (lida de `docker service inspect` do stack, quando existir). Com `--versao <etiqueta>` pula o build, confere que a etiqueta existe para as três imagens e implanta.
- `deploy/stack.prod.yml` (e o override local, se consumir as mesmas imagens): `image: rag-pipeline-*:${VERSAO_IMAGEM}`.

#### Migrations

Não aplicável: nenhuma mudança de schema. O runbook documenta como rodar `alembic upgrade head` na imagem do backend contra o banco de produção, como passo manual antes do deploy.

#### Models

Não aplicável.

#### Controllers e casos de uso

Não aplicável. O script é um caso de uso operacional: entrada (variáveis de ambiente e `--versao`), saída (stack implantado com a etiqueta) e autorização dada pelo acesso à VPS.

#### Views e experiência

Não aplicável: sem interface para pessoas.

#### Queries e repositórios

- Consulta somente de leitura citada no runbook para a janela de deploy: contagem de linhas de `executions` com `situacao IN ('pending','running')`, executada com `psql` dentro do serviço do Postgres, sem credencial na linha de comando.

#### Jobs e processamento assíncrono

Não aplicável: nenhum job novo; o runbook só manda esperar os lotes do worker terminarem.

#### Estrutura de arquivos

```text
specs/completed/0035-runbook-de-deploy-manual-em-producao/
  spec.md
deploy/
  RUNBOOK.md                 (novo)
  build_and_deploy.sh        (versão, poda, --versao)
  stack.prod.yml             (imagens por ${VERSAO_IMAGEM})
tests/
  test_deploy_runbook_docs.py            (novo)
  test_deploy_build_and_deploy_script.py (estendido)
  test_deploy_stack.py                   (estendido)
```

### 9. Modelo de dados

#### Entidades

Não aplicável: nenhuma entidade persistente é criada ou alterada. A versão de imagem é uma etiqueta Docker (commit curto), não um dado do produto.

#### Estados e transições

Não aplicável.

#### Migração e retenção

Retenção de imagens: as três versões mais recentes de cada imagem do projeto ficam no nó; as demais são removidas após um deploy bem-sucedido.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega é um documento de operação e um script de linha de comando usados por quem opera a VPS; nenhuma tela é criada ou alterada.

#### Stack e convenções de interface

Não aplicável.

#### Telas e responsabilidades

Não aplicável.

#### Fluxo de informação e navegação

Não aplicável.

#### Menus e navegação principal

Não aplicável: sem telas, a pessoa chega ao runbook por `deploy/RUNBOOK.md`, ligado a partir de `deploy/SECRETS.md` e `deploy/BACKUP.md`.

#### Formulários e ações

Não aplicável.

#### Composição e disposição

Não aplicável.

#### Blocos React e componentes selecionados

Não aplicável: nenhuma interface React é criada.

#### Estados e acessibilidade

Não aplicável. O runbook usa títulos, listas numeradas e blocos de código para leitura linear.

#### Contrato CRUD

Não aplicável.

#### Revisão visual durante o desenvolvimento

Não aplicável: sem superfície visual; cada tarefa registra `Não aplicável` com o motivo.

#### APIs expostas

Contrato de linha de comando de `deploy/build_and_deploy.sh`:

| Uso | Efeito | Saída de erro |
| --- | --- | --- |
| `deploy/build_and_deploy.sh` | confere secrets, recusa árvore suja, constrói e etiqueta pela versão, implanta e poda | código diferente de zero antes de construir ou implantar |
| `deploy/build_and_deploy.sh --versao <etiqueta>` | confere secrets e etiquetas, não constrói, implanta a versão e poda | recusa e lista as versões disponíveis quando a etiqueta não existe |

#### APIs externas utilizadas

Nenhuma além do Docker local já usado (`docker build`, `docker image`, `docker stack deploy`).

#### Documentação das APIs consultadas

- Sem documentação externa; `docker image ls`, `docker image rm` e `docker stack deploy` seguem o uso já presente no script.

#### Eventos e outros contratos

Não aplicável.

### 11. Estratégia TDD

- **Unidade**: não há unidade isolada; a lógica de versão e poda é do script e é testada por integração com `docker` simulado.
- **Integração/contrato**: `build_and_deploy.sh` roda com `docker`, `git` e `deploy/secrets.sh` simulados no `PATH` (`tests/_docker_falso.py`); o runbook e o YAML do stack são inspecionados por testes de contrato.
- **BDD/aceite**: o Gherkin da seção 6 orienta o desenho dos testes; não há arquivos `.feature`.
- **Runner TDD**: Pytest (`uv run pytest`) e Ruff, como no restante do projeto.
- **E2E**: não aplicável fora da VPS; o ensaio local não substitui a execução real.
- **Verificação manual**: a execução única do runbook inteiro na VPS pela pessoa responsável, fora do Delivery Gate (DEC-004).

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, US-003, US-004, FR-001, NFR-003, AC-001 | AC-001 na seção 6 | Documentar as três áreas do runbook em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-001 US-003 US-004 FR-001 NFR-003 AC-001` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-001, FR-002, FR-003, AC-002 | AC-002 na seção 6 | Ordenar a atualização de produção em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-001 FR-002 FR-003 AC-002` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-001, FR-002, NFR-002, AC-003 | AC-003 na seção 6 | Conferir que não há lote em andamento em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-001 FR-002 NFR-002 AC-003` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-001, US-004, FR-002, FR-003, FR-008, AC-004 | AC-004 na seção 6 | Fazer a migração como passo separado e protegido em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-001 US-004 FR-002 FR-003 FR-008 AC-004` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-002, FR-004, AC-005 | AC-005 na seção 6 | Etiquetar cada imagem pela versão em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0035 US-002 FR-004 AC-005` | RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao` | GREEN 2026-10-15: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-002, FR-004, NFR-003, AC-006 | AC-006 na seção 6 | Recusar o deploy com a árvore suja em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0035 US-002 FR-004 NFR-003 AC-006` | RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao` | GREEN 2026-10-15: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-002, FR-005, AC-007 | AC-007 na seção 6 | Guardar as três últimas versões de cada imagem em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0035 US-002 FR-005 AC-007` | RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao` | GREEN 2026-10-15: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-002, FR-006, AC-008 | AC-008 na seção 6 | Voltar atrás reimplantando uma versão guardada em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0035 US-002 FR-006 AC-008` | RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao` | GREEN 2026-10-15: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-002, FR-006, NFR-003, AC-009 | AC-009 na seção 6 | Recusar uma versão que não existe em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0035 US-002 FR-006 NFR-003 AC-009` | RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao` | GREEN 2026-10-15: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-001, US-003, FR-007, AC-010 | AC-010 na seção 6 | Verificar o deploy com o script de domínio em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-001 US-003 FR-007 AC-010` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-003, FR-001, FR-003, FR-007, AC-011 | AC-011 na seção 6 | Instalar pela primeira vez em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-003 FR-001 FR-003 FR-007 AC-011` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-001, US-004, FR-006, FR-007, FR-008, AC-012 | AC-012 na seção 6 | Reagir a uma verificação reprovada em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-001 US-004 FR-006 FR-007 FR-008 AC-012` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-004, FR-008, NFR-002, AC-013 | AC-013 na seção 6 | Nunca usar comando destrutivo de banco como rotina em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-004 FR-008 NFR-002 AC-013` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| FR-001, FR-009, NFR-001, AC-014 | AC-014 na seção 6 | Manter segredos e domínio fora do runbook em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 FR-001 FR-009 NFR-001 AC-014` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-001, FR-009, NFR-003, AC-015 | AC-015 na seção 6 | Detectar referência quebrada em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-001 FR-009 NFR-003 AC-015` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-002, FR-009, AC-016 | AC-016 na seção 6 | Conferir flags e comandos citados nos scripts em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-002 FR-009 AC-016` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| FR-004, NFR-001, AC-017 | AC-017 na seção 6 | Manter as saídas do script sem segredo em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0035 FR-004 NFR-001 AC-017` | RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao` | GREEN 2026-10-15: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-002, FR-005, NFR-002, AC-018 | AC-018 na seção 6 | Podar só depois de um deploy bem-sucedido em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0035 US-002 FR-005 NFR-002 AC-018` | RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao` | GREEN 2026-10-15: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-002, FR-005, FR-006, AC-019 | AC-019 na seção 6 | Nunca podar a versão em uso nem a de retorno em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0035 US-002 FR-005 FR-006 AC-019` | RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao` | GREEN 2026-10-15: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| FR-009, NFR-003, AC-020 | AC-020 na seção 6 | Citar nomes e comandos que existem em `tests/test_deploy_stack.py` com marcador próprio `SPECSFY: SPEC-0035 FR-009 NFR-003 AC-020` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_stack.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| NFR-001, AC-021 | AC-021 na seção 6 | Não pedir segredo na linha de comando em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 NFR-001 AC-021` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| NFR-002, AC-022 | AC-022 na seção 6 | Limitar a poda às imagens do projeto em `tests/test_deploy_build_and_deploy_script.py` com marcador próprio `SPECSFY: SPEC-0035 NFR-002 AC-022` | RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao` | GREEN 2026-10-15: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |
| US-001, US-003, FR-001, AC-023 | AC-023 na seção 6 | Sugerir a delegação sem implementá-la em `tests/test_deploy_runbook_docs.py` com marcador próprio `SPECSFY: SPEC-0035 US-001 US-003 FR-001 AC-023` | RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe | GREEN 2026-10-15: `uv run pytest tests/test_deploy_runbook_docs.py -q` | Suíte completa 651 passed, 1 skipped; Ruff limpo |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| US-001 | AC-001 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-001 | AC-002 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-001 | AC-003 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-001 | AC-004 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-001 | AC-010 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-001 | AC-012 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-001 | AC-015 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-001 | AC-023 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-002 | AC-005 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| US-002 | AC-006 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| US-002 | AC-007 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| US-002 | AC-008 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| US-002 | AC-009 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| US-002 | AC-016 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-002 | AC-018 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| US-002 | AC-019 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| US-003 | AC-001 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-003 | AC-010 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-003 | AC-011 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-003 | AC-023 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-004 | AC-001 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-004 | AC-004 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-004 | AC-012 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| US-004 | AC-013 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-001 | AC-001 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-001 | AC-011 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-001 | AC-014 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-001 | AC-023 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-002 | AC-002 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-002 | AC-003 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-002 | AC-004 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-003 | AC-002 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-003 | AC-004 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-003 | AC-011 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-004 | AC-005 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| FR-004 | AC-006 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| FR-004 | AC-017 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| FR-005 | AC-007 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| FR-005 | AC-018 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| FR-005 | AC-019 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| FR-006 | AC-008 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| FR-006 | AC-009 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| FR-006 | AC-012 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-006 | AC-019 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| FR-007 | AC-010 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-007 | AC-011 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-007 | AC-012 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-008 | AC-004 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-008 | AC-012 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-008 | AC-013 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-009 | AC-014 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-009 | AC-015 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-009 | AC-016 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| FR-009 | AC-020 | Contrato | `uv run pytest tests/test_deploy_stack.py -q` | Passed |
| NFR-001 | AC-014 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| NFR-001 | AC-017 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| NFR-001 | AC-021 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| NFR-002 | AC-003 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| NFR-002 | AC-013 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| NFR-002 | AC-018 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| NFR-002 | AC-022 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| NFR-003 | AC-001 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| NFR-003 | AC-006 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| NFR-003 | AC-009 | Integração | `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` | Passed |
| NFR-003 | AC-015 | Contrato | `uv run pytest tests/test_deploy_runbook_docs.py -q` | Passed |
| NFR-003 | AC-020 | Contrato | `uv run pytest tests/test_deploy_stack.py -q` | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY em 2026-10-15
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/completed/0035-runbook-de-deploy-manual-em-producao/spec.md`
- **Achados**: 4 `US`, 9 `FR`, 3 `NFR` e 23 `AC`; cada `US`, `FR` e `NFR` tem pelo menos 3 `AC` em `**Cobre**`. Nenhum `BLOCKER`. `WARNING` resolvido: a "versão de retorno" não tinha definição e passou a ser a etiqueta em uso no início do script (seção 8). `NOTE`: a migração pode tornar a volta atrás insegura, risco já registrado na seção 16 com a restauração como saída. Sem mudança de stack, de persistência nem de regra, então `STACK.md`, `DATABASE.md` e `RULES.md` não são afetados.

#### Gate do Ato II — Plano

- **Resultado**: Passed em 2026-10-15
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/completed/0035-runbook-de-deploy-manual-em-producao/spec.md`
- **Achados**: 26 tarefas (24 `[TEST]`, 1 `[CODE]`, 1 `[DOC]`), 39 de 39 IDs cobertos. T001–T023 concluídas com RED válido: 14 casos falham por `deploy/RUNBOOK.md` ausente e 9 casos do script falham porque ele ainda etiqueta `:local`, sem versão, poda nem `--versao`; os 48 testes de deploy existentes continuam verdes e o Ruff passa. Apoio de teste estendido em `tests/_docker_falso.py` (imagens, `git` falso).

#### Gate do Ato III — Entrega

- **Resultado**: Passed em 2026-10-15
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/completed/0035-runbook-de-deploy-manual-em-producao/spec.md . --full-chain`
- **Achados**: 26 de 26 tarefas concluídas; 39 de 39 IDs cobertos, cadeia `US/FR/NFR/AC → teste → tarefa → evidência` completa; `verify_acceptance.mjs`: QA PASSED; `uv run pytest` completo: 651 passed, 1 skipped; `uv run ruff check .` limpo; `monitor_context.mjs --check` e `build_documentation.mjs --check` atuais. Fora do gate (DEC-004): a execução do runbook inteiro na VPS pela pessoa responsável, que prova a migração em serviço descartável, a volta atrás com `--versao` e a poda com imagens reais.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-001, US-003, US-004, FR-001, NFR-003, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na seção 6 (Documentar as três áreas do runbook), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-001 US-003 US-004 FR-001 NFR-003 AC-001`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, US-003, US-004, FR-001, NFR-003, AC-001 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-001, FR-002, FR-003, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na seção 6 (Ordenar a atualização de produção), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-001 FR-002 FR-003 AC-002`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-002, FR-003, AC-002 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-001, FR-002, NFR-002, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na seção 6 (Conferir que não há lote em andamento), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-001 FR-002 NFR-002 AC-003`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-002, NFR-002, AC-003 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-001, US-004, FR-002, FR-003, FR-008, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na seção 6 (Fazer a migração como passo separado e protegido), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-001 US-004 FR-002 FR-003 FR-008 AC-004`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, US-004, FR-002, FR-003, FR-008, AC-004 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-005 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-002, FR-004, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na seção 6 (Etiquetar cada imagem pela versão), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-002 FR-004 AC-005`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-004, AC-005 nas seções 11–13. Resultado: RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao`; `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-002, FR-004, NFR-003, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na seção 6 (Recusar o deploy com a árvore suja), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-002 FR-004 NFR-003 AC-006`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-004, NFR-003, AC-006 nas seções 11–13. Resultado: RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao`; `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-002, FR-005, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na seção 6 (Guardar as três últimas versões de cada imagem), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-002 FR-005 AC-007`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-005, AC-007 nas seções 11–13. Resultado: RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao`; `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-002, FR-006, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na seção 6 (Voltar atrás reimplantando uma versão guardada), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-002 FR-006 AC-008`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-006, AC-008 nas seções 11–13. Resultado: RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao`; `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-002, FR-006, NFR-003, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na seção 6 (Recusar uma versão que não existe), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-002 FR-006 NFR-003 AC-009`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-006, NFR-003, AC-009 nas seções 11–13. Resultado: RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao`; `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T010 [TEST] [TDD] [US-001] Derivar do AC-010 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-001, US-003, FR-007, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 na seção 6 (Verificar o deploy com o script de domínio), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-001 US-003 FR-007 AC-010`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, US-003, FR-007, AC-010 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-003, FR-001, FR-003, FR-007, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 na seção 6 (Instalar pela primeira vez), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-003 FR-001 FR-003 FR-007 AC-011`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-001, FR-003, FR-007, AC-011 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T012 [TEST] [TDD] [US-001] Derivar do AC-012 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-001, US-004, FR-006, FR-007, FR-008, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012 na seção 6 (Reagir a uma verificação reprovada), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-001 US-004 FR-006 FR-007 FR-008 AC-012`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, US-004, FR-006, FR-007, FR-008, AC-012 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T013 [TEST] [TDD] [US-004] Derivar do AC-013 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-004, FR-008, NFR-002, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-013 na seção 6 (Nunca usar comando destrutivo de banco como rotina), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-004 FR-008 NFR-002 AC-013`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-004, FR-008, NFR-002, AC-013 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T014 [TEST] [TDD] Derivar do AC-014 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: FR-001, FR-009, NFR-001, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-014 na seção 6 (Manter segredos e domínio fora do runbook), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 FR-001 FR-009 NFR-001 AC-014`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs FR-001, FR-009, NFR-001, AC-014 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T015 [TEST] [TDD] [US-001] Derivar do AC-015 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-001, FR-009, NFR-003, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-015 na seção 6 (Detectar referência quebrada), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-001 FR-009 NFR-003 AC-015`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-009, NFR-003, AC-015 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T016 [TEST] [TDD] [US-002] Derivar do AC-016 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-002, FR-009, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-016 na seção 6 (Conferir flags e comandos citados nos scripts), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-002 FR-009 AC-016`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-009, AC-016 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T017 [TEST] [TDD] Derivar do AC-017 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: FR-004, NFR-001, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-017 na seção 6 (Manter as saídas do script sem segredo), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 FR-004 NFR-001 AC-017`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs FR-004, NFR-001, AC-017 nas seções 11–13. Resultado: RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao`; `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T018 [TEST] [TDD] [US-002] Derivar do AC-018 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-002, FR-005, NFR-002, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-018 na seção 6 (Podar só depois de um deploy bem-sucedido), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-002 FR-005 NFR-002 AC-018`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-005, NFR-002, AC-018 nas seções 11–13. Resultado: RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao`; `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T019 [TEST] [TDD] [US-002] Derivar do AC-019 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-002, FR-005, FR-006, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-019 na seção 6 (Nunca podar a versão em uso nem a de retorno), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-002 FR-005 FR-006 AC-019`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-005, FR-006, AC-019 nas seções 11–13. Resultado: RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao`; `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T020 [TEST] [TDD] Derivar do AC-020 um caso TDD falhando em tests/test_deploy_stack.py — Refs: FR-009, NFR-003, AC-020 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-020 na seção 6 (Citar nomes e comandos que existem), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_stack.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 FR-009 NFR-003 AC-020`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_stack.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs FR-009, NFR-003, AC-020 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_stack.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T021 [TEST] [TDD] Derivar do AC-021 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: NFR-001, AC-021 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-021 na seção 6 (Não pedir segredo na linha de comando), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 NFR-001 AC-021`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs NFR-001, AC-021 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T022 [TEST] [TDD] Derivar do AC-022 um caso TDD falhando em tests/test_deploy_build_and_deploy_script.py — Refs: NFR-002, AC-022 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-022 na seção 6 (Limitar a poda às imagens do projeto), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_build_and_deploy_script.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 NFR-002 AC-022`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs NFR-002, AC-022 nas seções 11–13. Resultado: RED 2026-10-15: o script ainda etiqueta `:local`, sem versão, poda nem `--versao`; `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T023 [TEST] [TDD] [US-001] Derivar do AC-023 um caso TDD falhando em tests/test_deploy_runbook_docs.py — Refs: US-001, US-003, FR-001, AC-023 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-023 na seção 6 (Sugerir a delegação sem implementá-la), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` se o `conftest.py` da suíte exigir `.env.testing`.
  - [x] **EXECUTE**: Escrever o teste em tests/test_deploy_runbook_docs.py com marcador próprio (docstring) `SPECSFY: SPEC-0035 US-001 US-003 FR-001 AC-023`, usando `docker`, `git` e `secrets.sh` simulados de `tests/_docker_falso.py` nos casos de script e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com `uv run pytest tests/test_deploy_runbook_docs.py -q` e observar RED válido: falha por script, flag, documento ou etiqueta ausente, não por erro de sintaxe ou de ambiente. Observado.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa só materializa teste.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, US-003, FR-001, AC-023 nas seções 11–13. Resultado: RED 2026-10-15: `deploy/RUNBOOK.md` ainda não existe; `uv run pytest tests/test_deploy_runbook_docs.py -q` falha só nos casos novos, sem erro de sintaxe, importação ou ambiente.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.


#### Fase 2 — US-002 (P1) — versão, poda e volta atrás

**Objetivo**: cada imagem sai etiquetada pela versão, as três últimas ficam no nó e uma versão anterior volta com um comando.
**Teste independente**: `uv run pytest tests/test_deploy_build_and_deploy_script.py tests/test_deploy_stack.py -q`.

- [x] T024 [CODE] [US-002] Etiquetar as imagens pela versão e reimplantar por `--versao` em deploy/build_and_deploy.sh — Refs: US-002, FR-004, FR-005, FR-006, FR-009, NFR-001, NFR-002, NFR-003, AC-005, AC-006, AC-007, AC-008, AC-009, AC-017, AC-018, AC-019, AC-020, AC-022 — Depends: T005, T006, T007, T008, T009, T017, T018, T019, T022, T020
  - [x] **PREP**: Confirmar o RED dos casos de script e de stack, rodar `$specsfy-documentator` para reconstruir `docs/` e `.specsfy/PACKAGES.md` antes de editar e ler `deploy/build_and_deploy.sh`, `deploy/stack.prod.yml` e `deploy/stack.local.yml`. Feito: RED confirmado nos 9 casos do script; `build_documentation.mjs --check` saiu com 0 antes da edição.
  - [x] **EXECUTE**: Calcular `VERSAO_IMAGEM` (commit curto), recusar árvore suja antes de qualquer build, construir e etiquetar backend, frontend e backup, implantar com a etiqueta, aceitar `--versao <etiqueta>` sem build (recusando etiqueta inexistente com a lista), podar só depois do deploy bem-sucedido mantendo as três mais recentes, a em uso e a de retorno, sem tocar volumes, redes ou outras imagens; ajustar `test_build_falho_impede_execucao_do_deploy` (SPEC-0022), que usa o `git` real, para usar um `git` falso no `PATH`, porque a árvore suja passa a recusar o deploy antes do build; trocar `:local` por `${VERSAO_IMAGEM}` em `deploy/stack.prod.yml` e ajustar `deploy/stack.local.yml` se necessário. Feito: versão por commit curto, recusa de árvore suja, `--versao` sem build, conferência da etiqueta nas três imagens, poda das três mais recentes com a versão implantada e a de retorno protegidas e sem tocar volumes, redes nem outras imagens; `deploy/stack.prod.yml` e `deploy/stack.local.yml` usam `${VERSAO_IMAGEM}`; testes antigos de SPEC-0022 (`git` falso) e SPEC-0027 (a poda roda depois do deploy) ajustados. `monitor_context.mjs --check`: CURRENT; `PROJECT.md` sem impacto material (a finalidade do projeto não muda).
  - [x] **VERIFY**: Rodar `uv run pytest tests/test_deploy_build_and_deploy_script.py tests/test_deploy_stack.py -q` e a regressão `uv run pytest tests/test_deploy_*.py -q`. Feito: `uv run pytest tests/test_deploy_build_and_deploy_script.py tests/test_deploy_stack.py tests/test_deploy_secrets_script.py -q` → 57 passed, 1 failed (o teste de AC-020, que depende do runbook da T025).
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). Não aplicável: script de linha de comando e YAML, sem interface para pessoas.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos alterados e o resultado de `uv run ruff check`. Feito: GREEN dos AC-005 a AC-009, AC-017, AC-018, AC-019 e AC-022; arquivos `deploy/build_and_deploy.sh`, `deploy/stack.prod.yml`, `deploy/stack.local.yml`, `tests/_docker_falso.py`; `ruff check` limpo.
  - [x] **IMPROVE**: Concentrar o cálculo de versão e a poda em funções pequenas do script e justificar a ausência de outra melhoria. Feito: a conferência da etiqueta e a poda usam o `docker` do nó de dados para a imagem de backup; o AC-020 fecha com o runbook (T025).

  <!-- specsfy:evidence {"task":"T024","refs":["AC-005", "AC-006", "AC-007", "AC-008", "AC-009", "AC-017", "AC-018", "AC-019", "AC-020", "AC-022", "FR-004", "FR-005", "FR-006", "FR-009", "NFR-001", "NFR-002", "NFR-003", "US-002"],"files":["deploy/build_and_deploy.sh","deploy/stack.prod.yml","deploy/stack.local.yml","tests/_docker_falso.py"],"commands":[{"run":"uv run pytest tests/test_deploy_build_and_deploy_script.py -q","exit":0}]} -->

**Checkpoint**: dois deploys seguidos com `docker` simulado e a volta ao primeiro por `--versao`.

#### Fase 3 — US-001, US-003, US-004 (P1/P2) — runbook

**Objetivo**: o passo a passo de atualização, primeira instalação e emergências, fiel aos scripts.
**Teste independente**: `uv run pytest tests/test_deploy_runbook_docs.py -q`.

- [x] T025 [DOC] [US-001] Escrever o runbook de deploy em deploy/RUNBOOK.md — Refs: US-001, US-002, US-003, US-004, FR-001, FR-002, FR-003, FR-006, FR-007, FR-008, FR-009, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-021, AC-023 — Depends: T001, T002, T003, T004, T010, T011, T012, T013, T014, T015, T016, T021, T023, T024
  - [x] **PREP**: Confirmar o RED dos casos do runbook e reler `deploy/SECRETS.md`, `deploy/BACKUP.md`, `deploy/conferir_dominio.sh` e o `--versao` entregue. Feito: RED dos 14 casos do runbook e do stack confirmado; `--versao` entregue na T024 relido.
  - [x] **EXECUTE**: Escrever as áreas de atualização (pré-condições, backup, migração, deploy, verificação), primeira instalação e emergências (voltar atrás, `docker service rollback`, restauração por `deploy/BACKUP.md`), com a consulta somente de leitura a `executions`, a nota de delegação e sem segredo, domínio real ou comando destrutivo. Feito: `deploy/RUNBOOK.md` com as áreas Atualizar a produção (pré-condições, backup, migração, deploy, verificação), Primeira instalação e Emergências; migração como serviço descartável do Swarm, consulta de lote somente de leitura e delegação apenas marcada. Os testes ganharam o reconhecimento do prefixo `rag-pipeline_` dos serviços.
  - [x] **VERIFY**: Rodar `uv run pytest tests/test_deploy_runbook_docs.py tests/test_deploy_stack.py -q`. Feito: `uv run pytest tests/test_deploy_*.py -q` → 95 passed.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). A tarefa produz um documento Markdown. Não aplicável: a tarefa produz um documento Markdown, sem interface para pessoas.
  - [x] **EVIDENCE**: Registrar GREEN, o arquivo criado e o resultado da varredura de segredos. Feito: GREEN dos AC-001 a AC-004, AC-010 a AC-016, AC-020, AC-021 e AC-023; arquivo `deploy/RUNBOOK.md`; varredura sem segredo, domínio real nem comando destrutivo.
  - [x] **IMPROVE**: Ligar o runbook a partir de `deploy/SECRETS.md` e `deploy/BACKUP.md` e justificar qualquer outra melhoria ou a ausência dela. Feito: o runbook foi ligado a `deploy/SECRETS.md` e `deploy/BACKUP.md` (uma linha de ligação ao RUNBOOK.md em cada um); o passo de migração em serviço descartável fica para a execução real na VPS (DEC-004).
  <!-- specsfy:evidence {"task": "T025", "refs": ["US-001", "US-002", "US-003", "US-004", "FR-001", "FR-002", "FR-003", "FR-006", "FR-007", "FR-008", "FR-009", "NFR-001", "NFR-002", "NFR-003", "AC-001", "AC-002", "AC-003", "AC-004", "AC-010", "AC-011", "AC-012", "AC-013", "AC-014", "AC-015", "AC-016", "AC-021", "AC-023"], "files": ["deploy/RUNBOOK.md", "deploy/SECRETS.md", "deploy/BACKUP.md"], "commands": [{"run": "uv run pytest tests/test_deploy_runbook_docs.py tests/test_deploy_stack.py -q", "exit": 0}]} -->


#### Fase final — Qualidade

- [x] T026 [TEST] Executar regressão e rastreabilidade em tests/test_deploy_build_and_deploy_script.py — Refs: US-001, US-002, US-003, US-004, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018, AC-019, AC-020, AC-021, AC-022, AC-023 — Depends: T024, T025
  - [x] **PREP**: Identificar as suítes de deploy, o Ruff e os gates, e conferir o banco de teste. Feito: suítes de deploy, Ruff e gates identificados; o banco de teste é o de `.env.testing`, validado pelo `conftest.py`.
  - [x] **EXECUTE**: Rodar `uv run ruff check`, `uv run pytest` e `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs` sobre a spec; revisar `PROJECT.md` e registrar a justificativa quando não houver impacto material, sem mudança de stack, persistência ou regra. Feito: `uv run ruff check .` limpo; `uv run pytest` completo → 651 passed, 1 skipped; `check_traceability.mjs --full-chain` → 39/39 IDs, OK; `PROJECT.md`, `.specsfy/STACK.md` e `docs/integrations.md` atualizados (SPEC-0035 não muda persistência nem regras, então `DATABASE.md` e `RULES.md` ficam como estão).
  - [x] **VERIFY**: Confirmar ausência de gaps de rastreabilidade e a regressão verde. Feito: sem gaps de rastreabilidade; a primeira execução da suíte parou em `tests/test_spec_markers.py` por uma palavra proibida no texto da spec, corrigida, e a segunda passou inteira. O build do frontend não foi reexecutado porque nenhum arquivo de `frontend/` mudou.
  - [x] **VISUAL**: `Não aplicável`: a tarefa não toca interface para pessoas (spec, seção 10). Não aplicável: nenhuma interface para pessoas foi alterada.
  - [x] **EVIDENCE**: Registrar contagens e comandos finais nas seções 11–13. Feito: contagens e comandos finais registrados nas seções 11–13.
  - [x] **IMPROVE**: Registrar a retrospectiva do processo. Feito: o texto da spec não pode conter palavras que o teste de marcadores recusa como placeholder; a primeira suíte parou por isso e foi corrigida.


### 15. Ordem de execução

- Caminho crítico: T001–T023 (RED) → T024 → T025 → T026.
- Tarefas paralelas: Nenhuma; os casos de um mesmo arquivo de teste não usam `[P]` e o runbook depende do `--versao` entregue.
- Estratégia de MVP: US-002 (versão e volta atrás) entrega o maior valor de segurança; o runbook (US-001, US-003, US-004) fecha a entrega. A execução única do runbook na VPS fica com a pessoa responsável, fora do Delivery Gate (DEC-004).

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0027 (secrets), SPEC-0032 (domínio e `conferir_dominio.sh`) e SPEC-0034 (backup e `restaurar.sh`), já concluídas e citadas pelo runbook.
- `docker`, `git` e acesso remoto à VPS, que já existem.

#### Riscos

- Runbook desatualizado em relação aos scripts → o teste de referência cruzada reprova a citação quebrada (FR-009).
- Podar a versão em uso e derrubar a volta atrás → a poda protege a versão em uso e a de retorno e só roda após deploy bem-sucedido (FR-005).
- Versão sem identificar o código por árvore suja → o script recusa árvore com alterações (FR-004).
- Migração incompatível com a versão anterior, o que torna a volta atrás insegura → o runbook exige backup antes da migração e a restauração como caminho de emergência (FR-003, FR-008).
- Imagens locais não são distribuídas entre nós → fora de escopo; um único nó nesta fase.

#### Suposições

- A VPS tem um único nó de aplicação e o nó de dados já é tratado por `BACKUP_DOCKER_CONTEXT`.
- A versão da imagem é o commit curto do repositório na VPS; o código chega à VPS por `git pull` do commit que passou na integração.
- Tags `:local` antigas são substituídas pela etiqueta da versão; o stack local de ensaio continua funcionando com `VERSAO_IMAGEM` definida.
- A checagem rápida de login e assistente é manual, sem script novo.

### 17. Decisões

- **DEC-001**: Local e forma — `deploy/RUNBOOK.md`, ao lado de `SECRETS.md` e `BACKUP.md`; um documento com três áreas. Alternativa descartada: um arquivo por área, que espalharia a ordem dos passos.
- **DEC-002**: Versão da imagem = commit curto, com recusa de árvore suja — a etiqueta só vale se identificar o código; alternativa descartada: data/hora, que não liga a imagem ao código.
- **DEC-003**: Guardar as três últimas versões por imagem, podando só após deploy bem-sucedido e protegendo a em uso e a de retorno — equilibra disco e capacidade de voltar; resolve a dúvida aberta do backlog.
- **DEC-004**: A prova da entrega é o teste automático; a execução inteira do runbook na VPS fica com a pessoa responsável, fora do Delivery Gate, no mesmo padrão das SPEC-0027 e SPEC-0034 — decisão de trabalhar local e fazer o deploy depois.
- **DEC-005**: A janela de deploy é conferida por consulta somente de leitura a `executions` (`pending`/`running`) — resolve a dúvida aberta do backlog; alternativa descartada: olhar as telas, que não é repetível.
- **DEC-006**: O registro de deploys fica fora desta spec; o runbook só marca a delegação — resolve a dúvida aberta do backlog.
- **DEC-007**: Migração como passo manual separado, com backup antes — o serviço não migra sozinho para evitar migração concorrente e permitir a conferência.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
