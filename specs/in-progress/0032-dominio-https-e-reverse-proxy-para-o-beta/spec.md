# Especificação integrada: Domínio, HTTPS e reverse proxy para o Beta

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0032 |
| Slug | 0032-dominio-https-e-reverse-proxy-para-o-beta |
| Status | Implementing |
| Effort | 4 |
| Effort updated at | 2026-10-13 |
| Effort rationale | Labels de Traefik em um stack já existente, mais um teste e um script de conferência; sem schema nem interface. O risco está na verificação real, que só ocorre na VPS (perfil `standard`). |
| ClickUp Task | |
| Milestones | M03 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | In Progress |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-10-13 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O sistema só é acessível localmente. A VPS já tem um Traefik compartilhado na rede `network_swarm_public`, com HTTPS automático por labels, e o stack de produção (SPEC-0022) já se conecta a essa rede. Falta dizer ao Traefik qual domínio aponta para o frontend, redirecionar HTTP para HTTPS, ativar HSTS e limitar tentativas de login, e falta uma forma de conferir o resultado depois do deploy.

#### Resultado desejado

A equipe de consultoria abre o sistema por um endereço próprio, com cadeado válido e sem aviso de certificado, e quem faz o deploy confere o resultado com um único comando.

#### Métricas de sucesso

- 100% dos acessos HTTP ao domínio são redirecionados para HTTPS.
- O script de conferência termina com código 0 em um deploy correto e com código diferente de 0 em cada falha que ele cobre (DNS, certificado, redirecionamento, HSTS).
- Zero nome de domínio, credencial ou segredo versionado.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: o stack de produção já se conecta a `network_swarm_public` e não cria proxy próprio → o item só acrescenta labels ao frontend (`specs/completed/0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm/spec.md`, AC-008).

#### Fontes e contexto consultados

- `specs/backlog/0029-dominio-https-e-reverse-proxy-para-o-beta.md` (refinado em 2026-10-13, oito perguntas respondidas).
- `deploy/stack.prod.yml`, `deploy/build_and_deploy.sh`, `deploy/frontend/Dockerfile` (porta 3000), `frontend/next.config.ts` (reescrita de `/api/*` para o backend) e `src/app/routers/auth.py` (login em `POST /api/v1/auth/login`).
- `tests/test_deploy_stack.py`: padrão dos testes do stack.

#### Documentação consultada

- Documentação oficial Traefik Proxy v2.11 consultada em 2026-10-13: Swarm, `redirectscheme`, `headers`, `ratelimit` e prioridade. Resumo e URLs arquivados em `research/traefik-labels-swarm.md`.

#### Artefatos de pesquisa armazenados

- `specs/planned/0032-dominio-https-e-reverse-proxy-para-o-beta/research/traefik-labels-swarm.md`: resumo próprio das cinco fontes oficiais, versão v2.11, acesso em 2026-10-13.

#### Dúvidas respondidas

- **Q**: qual domínio? → **A**: um subdomínio de um domínio que a pessoa já tem, informado por variável no deploy (backlog 0029, Perguntas 1 e 2).
- **Q**: o que fica exposto? → **A**: só o frontend; `/api/*` passa por ele (Pergunta 3).
- **Q**: HTTP e HSTS? → **A**: HTTP redireciona para HTTPS e o HSTS começa com validade curta (Pergunta 4).
- **Q**: como provar? → **A**: teste automático das labels e script de conferência pós-deploy (Pergunta 5).
- **Q**: nomes do resolvedor e do ponto de entrada? → **A**: variáveis, com padrões (Pergunta 6); os nomes reais foram confirmados em 2026-10-13 pelas labels do n8n que já roda na mesma VPS: resolvedor `letsencryptresolver` e ponto de entrada HTTPS `websecure`.
- **Q**: quem acessa a tela de login? → **A**: qualquer pessoa na internet, com login por pessoa e limite de tentativas por endereço (Pergunta 7).

#### Dúvidas abertas

- Nenhuma bloqueante.
- Não bloqueante: nome do ponto de entrada HTTP no Traefik da VPS. A spec assume `web`; as labels do n8n fornecidas só mostram o ponto de entrada HTTPS, e o script de conferência acusa o erro se o nome for outro.
- Não bloqueante: valor final do limite de tentativas de login e da validade do HSTS. A spec assume valores iniciais reversíveis (ver Suposições), ajustáveis por variável.

### 3. Escopo e atores

#### Incluído

- Labels do Traefik no serviço do frontend: roteador por domínio, redirecionamento de HTTP para HTTPS, HSTS e limite de tentativas no login.
- Variáveis de ambiente do domínio, do resolvedor e do ponto de entrada, repassadas por `deploy/build_and_deploy.sh`.
- Teste automático das labels em `tests/test_deploy_stack.py`.
- Script de conferência pós-deploy `deploy/conferir_dominio.sh`.
- Trecho no `deploy/SECRETS.md` ou documento equivalente apontando as novas variáveis, sem valores.

#### Fora de escopo

- Instalar ou configurar o Traefik da VPS (ele já existe).
- Registrar o domínio e criar o registro DNS (feito pela pessoa responsável).
- Mais de um domínio ou o endereço com `www`.
- Firewall de aplicação, CDN e proteção contra ataques de grande volume.
- Página de manutenção.
- Restrição por IP ou VPN.

#### Atores

- **Pessoa responsável pelo deploy (Marcio)**: informa o domínio, roda o deploy e o script de conferência.
- **Equipe de consultoria**: acessa o sistema pelo domínio.
- **Traefik compartilhado**: lê as labels, emite o certificado e roteia o tráfego.

### 4. Princípios e restrições do projeto

- **PR-001**: nenhum segredo, credencial ou nome de domínio é versionado; valores entram por variável de ambiente no deploy (SPEC-0027).
- **PR-002**: o stack não cria reverse proxy próprio; só se conecta à rede compartilhada (SPEC-0022).
- **PR-003**: o deploy é manual nesta fase; não há CI/CD (decisão do M03).
- **PR-004**: nenhum teste usa o banco de desenvolvimento; os testes desta spec leem apenas arquivos.

### 5. Histórias de usuário

#### US-001 — Acessar o sistema por um domínio com HTTPS válido (P1)

Como pessoa da equipe de consultoria, quero abrir o sistema por um endereço próprio com HTTPS, para usá-lo sem aviso de certificado e sem decorar IP e porta.

**Por que P1**: sem domínio com HTTPS o Beta não pode ser usado por mais ninguém.
**Teste independente**: com o stack publicado, o domínio abre a tela de login com certificado válido.
**Requisitos**: FR-001, FR-003, NFR-001, NFR-002

#### US-002 — Ser levado ao HTTPS e ter o navegador lembrando disso (P1)

Como pessoa da equipe, quero que um acesso por `http://` me leve ao `https://`, para que minha senha e minha sessão nunca trafeguem sem cifra.

**Por que P1**: o sistema tem login por pessoa e cookie de sessão.
**Teste independente**: uma requisição HTTP ao domínio recebe redirecionamento para HTTPS, e a resposta HTTPS traz o cabeçalho HSTS.
**Requisitos**: FR-002

#### US-003 — Ter o login protegido contra tentativas repetidas (P2)

Como responsável pelo sistema, quero que tentativas repetidas de login de um mesmo endereço sejam limitadas, para dificultar o palpite de senhas numa tela pública.

**Por que P2**: a tela de login fica na internet; o limite reduz o risco sem restringir a equipe.
**Teste independente**: o stack declara o limite apenas na rota de login, e acima do limite o Traefik recusa novas tentativas.
**Requisitos**: FR-004

#### US-004 — Conferir o domínio depois do deploy com um comando (P2)

Como pessoa responsável pelo deploy, quero um script que confira o domínio, o certificado e os redirecionamentos, para saber em segundos se o deploy ficou certo.

**Por que P2**: a verificação real só acontece na VPS; o script a torna repetível e o runbook (SPEC do backlog 0032) aponta para ele.
**Teste independente**: o script termina com código 0 num domínio correto e com código diferente de 0 quando falta DNS, certificado ou redirecionamento.
**Requisitos**: FR-005, FR-006, NFR-003

### 6. Cenários BDD de aceite

#### AC-001 — Frontend exposto por domínio informado em variável

**Cobre**: US-001, FR-001, NFR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-001 @NFR-002 @AC-001
Feature: Exposição do frontend por domínio

  Scenario: o domínio vem de variável e só o frontend é exposto
    Given o stack de produção com a variável do domínio definida
    When as labels de Swarm do stack são lidas
    Then o frontend declara a regra de roteamento pelo domínio da variável
    And nenhum outro serviço declara `traefik.enable=true`
    And o texto do stack não contém nenhum nome de domínio literal
```

#### AC-002 — Resolvedor e ponto de entrada por variável com padrão

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-002
Feature: Nomes do Traefik configuráveis

  Scenario: resolvedor e ponto de entrada usam padrões e aceitam variável
    Given o stack sem as variáveis do resolvedor e do ponto de entrada
    When as labels do frontend são lidas
    Then o resolvedor é `letsencryptresolver` e o ponto de entrada é `websecure`
    And ao definir as variáveis, os nomes definidos substituem os padrões
```

#### AC-003 — Deploy recusado sem domínio

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-003
Feature: Variável de domínio obrigatória

  Scenario: deploy sem a variável do domínio é recusado
    Given a variável do domínio ausente no ambiente do deploy
    When `deploy/build_and_deploy.sh` é executado
    Then o script termina com erro e mensagem pedindo a variável
    And nenhuma imagem é construída e nenhum `docker stack deploy` roda
```

#### AC-004 — Redirecionamento de HTTP para HTTPS

**Cobre**: US-002, FR-002, FR-003

```gherkin
@US-002 @FR-002 @FR-003 @AC-004
Feature: Redirecionamento para HTTPS

  Scenario: acesso HTTP é redirecionado
    Given o frontend com as labels de domínio
    When as labels do roteador HTTP são lidas
    Then existe um roteador no ponto de entrada HTTP com o mesmo domínio
    And ele aplica o middleware de redirecionamento permanente para HTTPS
```

#### AC-005 — HSTS com validade curta e configurável

**Cobre**: US-002, FR-002, FR-003

```gherkin
@US-002 @FR-002 @FR-003 @AC-005
Feature: HSTS

  Scenario: HSTS começa curto e aceita ajuste
    Given o stack sem variável de validade do HSTS
    When as labels do middleware de cabeçalhos são lidas
    Then a validade do HSTS é de um dia (86400 segundos)
    And ao definir a variável de validade, o valor definido a substitui
```

#### AC-006 — HSTS sem subdomínios por padrão

**Cobre**: US-002, FR-002

```gherkin
@US-002 @FR-002 @AC-006
Feature: HSTS restrito ao domínio

  Scenario: HSTS não se estende a outros subdomínios nem entra em listas de pré-carga
    Given o middleware de cabeçalhos do frontend
    When suas labels são lidas
    Then `includeSubdomains` e `preload` não estão ativos
```

#### AC-007 — Limite de tentativas apenas no login

**Cobre**: US-003, FR-004, NFR-002

```gherkin
@US-003 @FR-004 @NFR-002 @AC-007
Feature: Limite de tentativas no login

  Scenario: o limite vale só para a rota de login
    Given o frontend com as labels de domínio
    When os roteadores são lidos
    Then existe um roteador próprio para `POST /api/v1/auth/login` com o middleware de limite
    And esse roteador tem prioridade explícita maior que a do roteador geral
    And o roteador geral do domínio não aplica o limite
```

#### AC-008 — Limite configurável por endereço

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-008
Feature: Valores do limite

  Scenario: limite por endereço com média e rajada configuráveis
    Given o middleware de limite do login
    When suas labels são lidas
    Then o critério é o endereço de origem
    And a média e a rajada têm valores iniciais e aceitam variáveis de ambiente
```

#### AC-009 — Limite acima do valor recusa a tentativa

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-009
Feature: Efeito do limite

  Scenario: ao exceder o limite a tentativa é recusada
    Given o limite de tentativas no login ativo na VPS
    When um mesmo endereço excede a rajada configurada em `POST /api/v1/auth/login`
    Then o Traefik responde 429 sem chegar ao backend
```

#### AC-010 — Conferência bem-sucedida

**Cobre**: US-004, FR-005, NFR-003

```gherkin
@US-004 @FR-005 @NFR-003 @AC-010
Feature: Script de conferência

  Scenario: domínio correto termina com sucesso
    Given um domínio com DNS, certificado válido, redirecionamento e HSTS corretos
    When `deploy/conferir_dominio.sh` roda com o domínio informado
    Then o script lista cada verificação como aprovada e termina com código 0
```

#### AC-011 — Conferência acusa cada falha

**Cobre**: US-004, FR-005, NFR-003, FR-003

```gherkin
@US-004 @FR-005 @NFR-003 @FR-003 @AC-011
Feature: Falhas do script de conferência

  Scenario: cada falha é nomeada e o código é diferente de zero
    Given um domínio sem DNS, ou com certificado inválido, sem redirecionamento ou sem HSTS
    When o script de conferência roda
    Then cada verificação reprovada aparece nomeada na saída
    And o script termina com código diferente de 0
```

#### AC-012 — Conferência sem domínio informado

**Cobre**: US-004, FR-005, NFR-001

```gherkin
@US-004 @FR-005 @NFR-001 @AC-012
Feature: Entrada do script

  Scenario: sem domínio o script recusa rodar
    Given nenhuma variável de domínio nem argumento
    When o script de conferência roda
    Then ele termina com erro e mensagem de uso, sem consultar nenhum endereço
```

#### AC-013 — Teste automático lê o stack sem rede

**Cobre**: US-004, FR-006, NFR-001

```gherkin
@US-004 @FR-006 @NFR-001 @AC-013
Feature: Teste das labels

  Scenario: o teste verifica o stack apenas por leitura de arquivo
    Given a suíte de testes do stack
    When os testes de domínio rodam
    Then eles leem `deploy/stack.prod.yml` e não consultam rede, DNS, Traefik nem banco
```

#### AC-014 — Teste reprova stack fora do contrato

**Cobre**: US-004, FR-006, NFR-002, FR-001

```gherkin
@US-004 @FR-006 @NFR-002 @FR-001 @AC-014
Feature: Teste reprova desvio

  Scenario: stack que expõe outro serviço é reprovado
    Given um stack em que o backend declara `traefik.enable=true`
    When os testes de domínio rodam
    Then o teste de exposição só do frontend falha
```

#### AC-015 — Teste reprova domínio literal

**Cobre**: US-004, FR-006, NFR-001

```gherkin
@US-004 @FR-006 @NFR-001 @FR-001 @AC-015
Feature: Teste reprova segredo ou domínio no texto

  Scenario: domínio literal nas labels é reprovado
    Given um stack com a regra de roteamento contendo um nome de domínio literal
    When os testes de domínio rodam
    Then o teste de ausência de domínio literal falha
```

#### AC-016 — Tempo da conferência

**Cobre**: US-004, NFR-003

```gherkin
@US-004 @NFR-003 @AC-016
Feature: Tempo do script

  Scenario: o script não trava
    Given um domínio que não responde
    When o script de conferência roda
    Then cada consulta tem tempo limite e o script termina em até 60 segundos com código diferente de 0
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O stack de produção deve declarar, no serviço do frontend, as labels de Swarm que o expõem pelo domínio recebido da variável `DOMINIO_RAGPIPELINE`, e `deploy/build_and_deploy.sh` deve recusar o deploy quando a variável estiver ausente. Nenhum outro serviço recebe labels de exposição.
- **FR-002**: O frontend deve ter um roteador HTTP que redireciona de forma permanente para HTTPS e um middleware de cabeçalhos com HSTS de validade inicial de 86400 segundos, ajustável por variável, sem `includeSubdomains` nem `preload`.
- **FR-003**: O resolvedor de certificado e o ponto de entrada HTTPS devem vir de variáveis de ambiente, com os padrões `letsencryptresolver` e `websecure`.
- **FR-004**: O login (`POST /api/v1/auth/login`) deve ter um roteador próprio com middleware de limite de tentativas por endereço de origem, com média e rajada configuráveis por variável; o restante do domínio não aplica esse limite. O roteador do login deve ter prioridade explícita maior que a do roteador geral do domínio, para que o limite se aplique de fato.
- **FR-005**: O script `deploy/conferir_dominio.sh` deve verificar DNS, certificado válido, redirecionamento de HTTP para HTTPS e cabeçalho HSTS, listar cada verificação e terminar com código 0 só quando todas passarem.
- **FR-006**: A suíte `tests/test_deploy_stack.py` deve verificar, por leitura do arquivo, as labels de domínio, redirecionamento, HSTS, limite de tentativas, os nomes por variável e a exposição só do frontend.

#### Não funcionais

- **NFR-001**: Segurança e confidencialidade: nenhum nome de domínio, credencial ou segredo aparece em texto no repositório. **Verificação**: teste de varredura do stack e dos scripts (AC-001, AC-013, AC-015).
- **NFR-002**: Superfície exposta mínima: somente o frontend é exposto por labels; backend, worker, Postgres e Qdrant não o são. **Verificação**: teste de labels por serviço (AC-001, AC-014).
- **NFR-003**: Operabilidade: o script de conferência termina em até 60 segundos, com tempo limite de 10 segundos por consulta. **Verificação**: teste do script contra um endereço que não responde (AC-016) e conferência manual na VPS.

#### Erros e casos-limite

- Variável de domínio ausente no deploy → o deploy recusa seguir, com mensagem clara.
- DNS ainda não aponta para a VPS ou o certificado não foi emitido → o script de conferência acusa a verificação reprovada; o deploy não é desfeito.
- Nomes do resolvedor ou do ponto de entrada errados → o Traefik não emite o certificado; o script acusa certificado inválido.
- HSTS ativo com a configuração quebrada → a validade curta limita o tempo que o navegador permanece preso em HTTPS.
- Limite de tentativas baixo demais para a equipe → os valores são variáveis e podem ser elevados sem editar o stack.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- `deploy/stack.prod.yml` (Compose 3.7 do Swarm) declara cinco serviços na rede externa `network_swarm_public`, sem labels. O frontend escuta na porta 3000 (`deploy/frontend/Dockerfile`).
- `deploy/build_and_deploy.sh` confere os secrets, constrói as imagens e roda `docker stack deploy`.
- `tests/test_deploy_stack.py` valida o stack lendo o YAML (padrão de `SPECSFY:`).
- O login é `POST /api/v1/auth/login` (`src/app/routers/auth.py`); `frontend/next.config.ts` reescreve `/api/*` para o backend.

#### Arquitetura e módulos

- Labels em `deploy.labels` do serviço `frontend_ragpipeline`: roteador HTTPS por domínio, roteador HTTP com redirecionamento, roteador de login com limite, middleware de cabeçalhos (HSTS) e o serviço de balanceamento na porta 3000.
- `deploy/build_and_deploy.sh` exige `DOMINIO_RAGPIPELINE` e exporta as demais variáveis com padrão.
- `deploy/conferir_dominio.sh` consulta o domínio por `curl` e `openssl`, sem tocar no stack.

#### Ajuste da estratégia de verificação — 2026-10-13

Pedido preservado: “não entendi.... não quero fazer o deploy agora na VPS> quero primeiro testar tudo local com docker e depois que estiover tudo OK faço o deploy”.

Classificação: mudança somente de plano/testes, sem alterar FR, NFR, AC ou código de produto. Antes de T027, executar T028: construir as imagens atuais pelos Dockerfiles existentes, iniciar frontend, backend, worker, PostgreSQL e Qdrant em um ambiente Docker local isolado, com dados de teste e armazenamento compartilhado entre API e worker. Conferir acesso pelo navegador, autenticação, navegação, conexões, prévia, processamento e conversão dentro dos limites das integrações disponíveis. Providers externos podem ser simulados somente no ensaio, com a limitação registrada. Evidência e procedimentos ficam nesta spec; configuração temporária do ensaio pode ficar em `/tmp`. Não modificar contêineres, banco ou volumes do stack local anterior. T027 continua exigindo a conferência real na VPS e só será executada quando a pessoa decidir publicar após testar localmente.

As evidências T001–T026 permanecem válidas para os mesmos comportamentos. O Plan Gate é reaberto somente para incorporar a tarefa operacional e sua dependência; nenhum predecessor TDD ou caso BDD existente é invalidado.

#### Migrations

- Não aplicável: nenhuma tabela, campo ou migração.

#### Models

- Não aplicável.

#### Controllers e casos de uso

- Não aplicável: não há rota nova; o roteamento é do Traefik.

#### Views e experiência

- Não aplicável: não há interface para pessoas além do certificado e do redirecionamento visíveis no navegador.

#### Queries e repositórios

- Não aplicável.

#### Jobs e processamento assíncrono

- Não aplicável.

#### Estrutura de arquivos

```text
specs/draft/0032-dominio-https-e-reverse-proxy-para-o-beta/
  spec.md
  research/
deploy/
  stack.prod.yml
  build_and_deploy.sh
  conferir_dominio.sh
tests/
  test_deploy_stack.py
  test_deploy_conferir_dominio_script.py
```

### 9. Modelo de dados

#### Entidades

- Não aplicável: nenhuma entidade de domínio nova ou alterada.

#### Estados e transições

- Não aplicável.

#### Migração e retenção

- Não aplicável.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega é configuração de infraestrutura (labels) e scripts de operação; a pessoa só vê o domínio e o cadeado no navegador, já servidos pelo frontend existente.

#### Stack e convenções de interface

- Não aplicável.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável.

#### Menus e navegação principal

- Não aplicável: nenhuma tela nova; a pessoa chega ao sistema pelo domínio.

#### Formulários e ações

- Não aplicável.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável: nenhum bloco React é criado ou alterado.

#### Estados e acessibilidade

- Não aplicável.

#### Contrato CRUD

- Não aplicável: a entrega não inclui CRUD.

#### Revisão visual durante o desenvolvimento

- Não aplicável: nenhuma tarefa altera interface; cada tarefa registra `Não aplicável` com esse motivo.

#### APIs expostas

- Nenhuma rota nova. O Traefik passa a expor o frontend pelo domínio; `/api/*` continua atrás do frontend.

#### APIs externas utilizadas

- Emissão automática de certificado pelo Traefik compartilhado da VPS (configurado fora deste repositório). O script de conferência consulta o domínio público do próprio sistema por HTTPS, com tempo limite por consulta.

#### Documentação das APIs consultadas

- A documentação do Traefik (labels de Swarm, `redirectscheme`, `headers`, `ratelimit` e prioridade) está arquivada em `research/traefik-labels-swarm.md`.

#### Eventos e outros contratos

- Variáveis de ambiente do deploy: `DOMINIO_RAGPIPELINE` (obrigatória), `TRAEFIK_CERT_RESOLVER` (padrão `letsencryptresolver`), `TRAEFIK_ENTRYPOINT_HTTPS` (padrão `websecure`), `TRAEFIK_ENTRYPOINT_HTTP` (padrão `web`), `HSTS_MAX_AGE_SEGUNDOS` (padrão 86400), `LOGIN_RATE_LIMIT_MEDIA` e `LOGIN_RATE_LIMIT_RAJADA` (valores iniciais na seção 16).

### 11. Estratégia TDD

- **Unidade**: leitura do stack e verificação das labels em `tests/test_deploy_stack.py`.
- **Integração/contrato**: `deploy/build_and_deploy.sh` e `deploy/conferir_dominio.sh` executados com comandos simulados em `tests/`, no padrão de `tests/test_deploy_build_and_deploy_script.py`.
- **BDD/aceite**: o Gherkin da seção 6 orienta os casos.
- **Runner TDD**: Pytest, runner já usado no projeto.
- **E2E**: Não aplicável.
- **Verificação manual**: certificado real, DNS real e limite de tentativas só existem na VPS; a pessoa responsável roda o script de conferência e a lista de verificação do runbook.

Os casos TDD e as tarefas estão nas seções 12 e 14; o RED é observado por `$specsfy-06-tdd-bdd`.

GREEN observado em 2026-10-13: T019 (AC-001/002/013/014/015), T020
(AC-003), T021 (AC-004/005/006), T022 (AC-007/008 e contrato estático de
AC-009), T023 (AC-010/011/012/016 com rede simulada). A prova pública de
AC-009 e AC-010 continua dependente de T027; testes locais não provam emissão
de certificado nem resposta 429 na VPS.

### 12. Plano de testes e rastreabilidade

Um caso por AC, cada um com seu marcador `SPECSFY: SPEC-0032 …`. O AC-009 é verificado por tela estática das labels (rajada positiva) e, no efeito real (429), na VPS por T027.

| AC | Teste (Pytest) | Arquivo | Tarefa |
| --- | --- | --- | --- |
| AC-001 | `test_frontend_e_exposto_por_dominio_de_variavel_e_so_ele` | `tests/test_deploy_stack.py` | T002 |
| AC-002 | `test_resolvedor_e_entrypoint_tem_padrao_e_aceitam_variavel` | `tests/test_deploy_stack.py` | T003 |
| AC-003 | `test_deploy_sem_dominio_e_recusado_antes_de_build_e_stack_deploy` | `tests/test_deploy_build_and_deploy_script.py` | T004 |
| AC-004 | `test_roteador_http_redireciona_permanentemente_para_https` | `tests/test_deploy_stack.py` | T005 |
| AC-005 | `test_hsts_tem_validade_curta_e_aceita_variavel` | `tests/test_deploy_stack.py` | T006 |
| AC-006 | `test_hsts_sem_includesubdomains_nem_preload` | `tests/test_deploy_stack.py` | T007 |
| AC-007 | `test_login_tem_roteador_proprio_com_prioridade_e_limite` | `tests/test_deploy_stack.py` | T008 |
| AC-008 | `test_limite_do_login_por_endereco_com_media_e_rajada_configuraveis` | `tests/test_deploy_stack.py` | T009 |
| AC-009 | `test_limite_do_login_declara_rajada_que_recusa_o_excesso` | `tests/test_deploy_stack.py` | T010 |
| AC-010 | `test_conferencia_aprova_dominio_correto` | `tests/test_deploy_conferir_dominio_script.py` | T015 |
| AC-011 | `test_conferencia_nomeia_cada_falha_e_sai_com_erro` | `tests/test_deploy_conferir_dominio_script.py` | T016 |
| AC-012 | `test_conferencia_sem_dominio_recusa_sem_consultar_rede` | `tests/test_deploy_conferir_dominio_script.py` | T017 |
| AC-013 | `test_testes_de_dominio_leem_o_stack_sem_rede` | `tests/test_deploy_stack.py` | T011 |
| AC-014 | `test_stack_com_backend_exposto_e_detectado` | `tests/test_deploy_stack.py` | T012 |
| AC-015 | `test_dominio_literal_na_regra_e_detectado` | `tests/test_deploy_stack.py` | T013 |
| AC-016 | `test_conferencia_tem_tempo_limite_e_termina_em_60s` | `tests/test_deploy_conferir_dominio_script.py` | T018 |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed em 2026-10-13 (`READY`).
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0032-dominio-https-e-reverse-proxy-para-o-beta/spec.md`
- **Achados**: contagens: 4 US, 6 FR, 3 NFR e 16 AC; cada US, FR e NFR com pelo menos 3 AC. Nenhum BLOCKER. WARNING-1 (resolvido): o roteador do login precisava de prioridade explícita sobre o geral; incluído em FR-004 e AC-007. WARNING-2 (resolvido): faltava o tempo limite por consulta do script; fixado em 10 segundos em NFR-003. WARNING-3 (aceito): a documentação do Traefik sobre labels de Swarm, `redirectscheme`, `headers` e `ratelimit` ainda não está arquivada em `research/`; deve ser arquivada antes da implementação (primeira tarefa do plano). NOTE: nome do ponto de entrada HTTP e valores do limite e do HSTS são suposições reversíveis, listadas como não bloqueantes.

#### Gate do Ato II — Plano

- Replanejamento de 2026-10-13: Passed após incluir T028 `[OPS]` e a dependência T027 → T028. Validador: 28 tarefas, 26 concluídas, 29/29 IDs cobertos; rastreabilidade OK. Não há tarefa CODE nova nem mudança de FR/NFR/AC; os predecessores RED e GREEN existentes foram preservados. `analyze_change --base HEAD` não comparou o arquivo porque sua pasta mudou de planned para in-progress no worktree; a classificação semântica acima considera somente este pedido, sem atribuir a ele as alterações anteriores.

- **Resultado**: Passed em 2026-10-13.
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0032-dominio-https-e-reverse-proxy-para-o-beta/spec.md`
- **Achados**: 27 tarefas (1 `[DOC]` de pesquisa, 16 `[TEST] [TDD]`, 1 `[TEST]` de apoio, 5 `[CODE]`, 2 `[DOC]`, 1 `[TEST]` de regressão e 1 `[OPS]`); 29 de 29 IDs (US, FR, NFR, AC) cobertos. RED válido observado nos 16 casos, cada um por asserção de comportamento ausente (stack sem labels, script de conferência inexistente, deploy que ainda segue sem domínio). Os 12 casos do stack foram escritos antes do código, e os existentes (SPEC-0022 e SPEC-0027) seguem verdes (16 passam). T001 (arquivar a documentação do Traefik) segue aberta e é a primeira tarefa da implementação. T027 (conferência real na VPS) só se fecha com a pessoa responsável. O teste do AC-016 leva cerca de 30 s por simular uma consulta lenta.

#### Gate do Ato III — Entrega

- **Resultado**: In Progress; implementação e verificação local aprovadas, conferência real T027 aberta.
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0032-dominio-https-e-reverse-proxy-para-o-beta/spec.md .`
- **Achados**: 29/29 IDs cobertos; 581 testes Python e 225 testes frontend aprovados, Ruff/lint/tipos/build aprovados. AC-009 (429 real), AC-010 (domínio público) e demais verificações de T027 exigem a observação no ambiente publicado. Delivery Gate não foi aprovado com evidência apenas local.

#### Linha de base da implementação — 2026-10-13

- Proteção do banco: SAFE antes de cada execução. Suíte de deploy: `.venv/bin/python -m pytest tests/test_deploy_stack.py tests/test_deploy_build_and_deploy_script.py tests/test_deploy_secrets_script.py tests/test_deploy_conferir_dominio_script.py -q`: 16 failed e 30 passed em 7,19 s; as 16 falhas são o RED esperado desta spec, sem falha legada nessa suíte. A execução ampla inicial foi interrompida para priorizar a base focal: 39 passed, 1 skipped em 148,46 s; não comprova regressão completa.

#### Verificação local da implementação — 2026-10-13

| Verificação | Comando | Resultado |
| --- | --- | --- |
| Stack e labels: AC-001/002/004/005/006/007/008/009/013/014/015 | `.venv/bin/python -m pytest tests/test_deploy_stack.py -q` | 23 passed em 1,55 s |
| Deploy e secrets: AC-003 e contratos anteriores | `.venv/bin/python -m pytest tests/test_deploy_build_and_deploy_script.py tests/test_deploy_secrets_script.py -q` | 19 passed em 7,32 s após reforçar a guarda do build falho |
| Conferência: AC-010/011/012/016 simulados | `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py -q` | 4 passed em 31,54 s; caso lento menor que 60 s |
| Marcadores de specs | `.venv/bin/python -m pytest tests/test_spec_markers.py -q` | 1 passed em 2,20 s |
| Lint Python | `.venv/bin/ruff check .` | All checks passed |
| Rastreabilidade | `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0032-dominio-https-e-reverse-proxy-para-o-beta/spec.md .` | 29/29 IDs; OK |
| Testes frontend | `npm --prefix frontend run test:tdd` | 225 passed, 56 arquivos, 236,14 s |
| Lint frontend | `npm --prefix frontend run lint` | exit 0 |
| Tipos frontend | `npm --prefix frontend run typecheck` | exit 0 |
| Build frontend | `npm --prefix frontend run build` | exit 0, rotas geradas |
| Sintaxe Bash | `bash -n deploy/conferir_dominio.sh deploy/build_and_deploy.sh` | exit 0 |
| Interpolação Swarm | `env DOMINIO_RAGPIPELINE=app-teste.invalid APPLICATION_NODE_HOSTNAME=no-de-aplicacao DATABASE_NODE_HOSTNAME=no-de-dados docker stack config --compose-file deploy/stack.prod.yml` | exit 0; sem publicação |
| Evidências | `node .agents/skills/specsfy-07-implement/scripts/verify_evidence.mjs specs/in-progress/0032-dominio-https-e-reverse-proxy-para-o-beta/spec.md .` | PASSED (strict) |

- Revisão visual: não aplicável em T001/T019–T026; somente infraestrutura, scripts e documentação, sem alteração de componentes, rotas de interface ou estilos.
- Contexto: monitor CURRENT; STACK.md registra o Traefik de forma aditiva. PROJECT.md e RULES.md sem mudança material: capacidades, regras de negócio e fluxo existentes preservados. Nenhum schema ou dependência mudou.
- Documentação: `build_documentation.mjs --project /home/marcioh/projects/rag-pipeline` executado após cada alteração de produção, seguido de `--check` aprovado; conteúdo humano preservado.
- Correções internas de testes: AC-015 passou a preservar a referência da variável antes de conferir parametrização; o teste legado de build falho recebe domínio fictício e exige tentativa de build, evitando sucesso por recusa anterior.
- Skip preexistente: `tests/spec0014/test_resumo_secao.py::test_comparacao_real_reproduzivel` exige opt-in `RUN_SPEC0014_REAL=1` para uma comparação paga externa; não pertence a esta entrega. Não há skip nos 16 casos da SPEC-0032.
- Primeira regressão Python completa: `.venv/bin/python -m pytest -q` retornou 3 failed, 578 passed e 1 skipped em 753,31 s. Os três casos são da SPEC-0023: dois em `tests/test_conversion_image_ocr.py` e o fluxo PDF/XLSX/JPG em `tests/test_router_conversao.py`; todos falharam por ausência de `tesseract`, sem mudança nesses módulos de aplicação. `deploy/backend/Dockerfile` já instala Tesseract e português. O sudo local exigiu senha, portanto pacotes oficiais Ubuntu foram baixados e extraídos somente em `/tmp/spec0032-ocr/runtime`, sem instalação global, versão Tesseract 5.3.4 com idiomas por/eng/osd. Regressão completa repetida com PATH, LD_LIBRARY_PATH e TESSDATA_PREFIX apontando para esse runtime; T026 segue aberta até o resultado.
- Segunda regressão completa: 578 passed, 3 failed e 1 skipped em 708,84 s. O OCR passou; os três erros vieram de `tests/test_ci_gates.py`, porque a configuração temporária substituiu o PATH e omitiu `uv`. Corrigida a execução para acrescentar o diretório de OCR ao PATH original, sem substituir os demais diretórios; nenhum código de aplicação ou teste foi alterado para essa correção. Repetição focal: 17 passed nos arquivos de OCR/conversão em 51,05 s e 22 passed em `tests/test_ci_gates.py` em 1,41 s. Execução integral reiniciada com `env PATH="/tmp/spec0032-ocr/runtime/usr/bin:$PATH" LD_LIBRARY_PATH=/tmp/spec0032-ocr/runtime/usr/lib/aarch64-linux-gnu TESSDATA_PREFIX=/tmp/spec0032-ocr/runtime/usr/share/tesseract-ocr/5/tessdata .venv/bin/python -m pytest -q`.
- Regressão integral final com o comando acima: **exit 0, 581 passed, 1 skipped, 2 warnings em 890,56 s**. O skip é o opt-in pago da SPEC-0014; nenhum caso da SPEC-0032 foi pulado. Sem falha remanescente. Avisos preexistentes de Starlette/httpx e LangGraph permanecem, sem alteração de dependências nesta entrega. T026 concluída; T027 permanece aguardando domínio/DNS, janela do deploy e evidência da pessoa responsável. Nenhum deploy, commit, push ou publicação foi executado nesta implementação.

#### Ensaio Docker local — T028, 2026-10-13/14

- Autorização: testar localmente primeiro, sem publicação na VPS. Docker confirmado no socket local; stack anterior na porta 3000 preservado. Projeto Compose `rag-ensaio-0032`, frontend `http://localhost:3300`, banco `rag_pipeline_ensaio_0032_testing`, APP_ENV=testing e volumes privados de PostgreSQL, Qdrant e uploads. Migrations existentes e schema da fila aplicados somente no banco novo, com guarda explícita e avaliação SAFE. Nenhuma migration, dependência ou interface de produto alterada.
- Builds aprovados, exit 0: `docker build -f deploy/backend/Dockerfile -t rag-pipeline-backend:ensaio-0032 .` e `docker build --build-arg API_PROXY_TARGET=http://backend_ragpipeline:8000 -f deploy/frontend/Dockerfile -t rag-pipeline-frontend:ensaio-0032 frontend/`. Backend contém Tesseract e LibreOffice; frontend gerou as rotas e passou tipos.
- Inicialização: `docker compose --env-file /tmp/rag-0032-ensaio/empty.env -f /tmp/rag-0032-ensaio/compose.yml up -d`; cinco serviços de aplicação ativos, PostgreSQL saudável e init concluído com exit 0. Auxiliares separados: embeddings simulados e Traefik v2.11. Banco e arquivos do stack anterior preservados.
- `.venv/bin/python /tmp/rag-0032-smoke.py`: exit 0, 42 verificações HTTP pelo proxy Next real; login, sessão, permissões owner/member, workspaces, conexões, prévia, publicação pelo worker/Qdrant, consulta e conversão. Primeiro envio: 3 chunks inseridos; repetição: 3 mantidos e nenhum inserido; substituição: 3 inseridos e 3 removidos, preservando um documento. Cinco arquivos convertidos com saída Markdown não vazia.
- `.venv/bin/python /tmp/rag-0032-formatos-smoke.py`: exit 0, seis conversões adicionais aprovadas. Total: 11 documentos nos 10 formatos suportados (PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, JPG, JPEG, PNG); conversão e OCR executados dentro da imagem atual.
- `node /tmp/rag-0032-browser.cjs` e `node /tmp/rag-0032-flow-browser.cjs`: exit 0, 39 capturas em 1280x900 e 375x900, claro/escuro. Aplicação real: erro de login, sessão válida, navegação por teclado, formulário longo, permissões e fluxo Arquivos → Divisão → Prévia → Publicação, com envio concluído nos dois tamanhos. Nenhum erro JavaScript nem overflow global. Bordas, espaçamento, margem, padding, tipografia e foco inspecionados; nenhuma correção visual necessária.
- `.venv/bin/python /tmp/rag-0032-proxy-smoke.py`: exit 0. Traefik local recebeu regras derivadas das labels de produção; HTTP 301 para HTTPS, certificado local validado com `--cacert`, HSTS `max-age=86400`; 25 POST de login deram 20 respostas 401 e 5 respostas 429 com HSTS. Outras 25 requisições continuaram 401, sem aplicar o limite fora do login.
- Evidências e fixtures permanecem fora do repositório em `/tmp/rag-0032-ensaio/`: `smoke-results.json`, `formatos-results.json`, `browser-results.json`, `flow-browser-results.json`, `proxy-results.json` e capturas PNG. Credenciais fictícias não registradas nesta spec.
- Limites: embeddings determinísticos simulam a API externa; não comprovaram qualidade semântica nem respostas reais do assistente/LLM. TLS usa certificado local, sem DNS público ou ACME; não comprova T027. O proxy usa file provider derivado das labels, não a descoberta Swarm da VPS. T027 continua aberta e adiada por decisão da pessoa.
- Procedimento seguro: mesmos argumentos Compose com `ps`, `stop` e `start`, descritos em `deploy/SECRETS.md`; não remover volumes. Configuração temporária deve ser preparada novamente se `/tmp` for apagado. Melhoria incorporada: ensaio isolado e init com guarda de banco de teste antes de migrations; nenhum ajuste adicional no produto necessário.

### 14. Tarefas

Formato:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Runner TDD: Pytest (`.venv/bin/python -m pytest`), já usado no projeto. Todas as tarefas abaixo registram `VISUAL` como `Não aplicável`, porque a entrega é configuração de infraestrutura e scripts, sem interface para pessoas.

#### Fase 0 — Pesquisa

- [x] T001 [DOC] Arquivar a documentação do Traefik (labels de Swarm, `redirectscheme`, `headers`, `ratelimit`, prioridade de roteadores) em specs/defined/0032-dominio-https-e-reverse-proxy-para-o-beta/research/traefik-labels-swarm.md e indexá-la na seção 2 — Refs: FR-002, FR-003, FR-004 — Depends: none
  - [x] **PREP**: Seções 2 e 10 lidas; consultar Docker/Swarm, RedirectScheme, Headers, RateLimit e Routers da documentação oficial v2.11.
  - [x] **EXECUTE**: Resumo próprio das cinco fontes oficiais v2.11 arquivado e indexado com URLs e data de acesso.
  - [x] **VERIFY**: Rodar `node .agents/skills/specsfy-03-specify/scripts/load_research.mjs` sobre a spec e confirmar que o arquivo é lido sem erro.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Registrar o caminho, a versão consultada e o resultado do `load_research`.
  - [x] **IMPROVE**: Anotar no arquivo qualquer divergência entre a documentação e as suposições da spec (nome do ponto de entrada HTTP, `priority`, `sourceCriterion`).

  - Registro VERIFY/VISUAL/EVIDENCE/IMPROVE: load_research: PASSED, 2369 bytes; cinco URLs oficiais v2.11 indexadas. Sem interface. Média exige period=1m; prioridade explícita e origem remota confirmadas. Versão e entrypoint HTTP reais reservados a T027.

#### Fase 1 — RED TDD informado pelo BDD

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-001 o caso `test_frontend_e_exposto_por_dominio_de_variavel_e_so_ele` em tests/test_deploy_stack.py — Refs: US-001, FR-001, NFR-001, NFR-002, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_frontend_e_exposto_por_dominio_de_variavel_e_so_ele` com o marcador `SPECSFY: SPEC-0032 US-001 FR-001 NFR-001 NFR-002 AC-001`: o frontend declara `traefik.enable=true` e a regra `Host(\`${DOMINIO_RAGPIPELINE}\`)`, nenhum outro serviço é exposto e o texto do stack não contém domínio literal.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_frontend_e_exposto_por_dominio_de_variavel_e_so_ele -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_frontend_e_exposto_por_dominio_de_variavel_e_so_ele -q`: falhou por asserção `None == 'true'`: o frontend não tem `traefik.enable`.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-002 o caso `test_resolvedor_e_entrypoint_tem_padrao_e_aceitam_variavel` em tests/test_deploy_stack.py — Refs: US-001, FR-003, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_resolvedor_e_entrypoint_tem_padrao_e_aceitam_variavel` com o marcador `SPECSFY: SPEC-0032 US-001 FR-003 NFR-001 AC-002`: sem variáveis o resolvedor é `letsencryptresolver` e o ponto de entrada `websecure`; com `TRAEFIK_CERT_RESOLVER` e `TRAEFIK_ENTRYPOINT_HTTPS` definidas, os valores definidos vencem (interpolação `${VAR:-padrão}` feita pelo próprio teste).
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_resolvedor_e_entrypoint_tem_padrao_e_aceitam_variavel -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_resolvedor_e_entrypoint_tem_padrao_e_aceitam_variavel -q`: falhou por asserção: nenhum roteador HTTPS geral nas labels.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T004 [P] [TEST] [TDD] [US-001] Derivar do AC-003 o caso `test_deploy_sem_dominio_e_recusado_antes_de_build_e_stack_deploy` em tests/test_deploy_build_and_deploy_script.py — Refs: US-001, FR-001, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_deploy_sem_dominio_e_recusado_antes_de_build_e_stack_deploy` com o marcador `SPECSFY: SPEC-0032 US-001 FR-001 NFR-001 AC-003`: sem `DOMINIO_RAGPIPELINE` o script termina com erro, a mensagem cita a variável e o log do `docker` falso não tem `build` nem `stack deploy`.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_build_and_deploy_script.py::test_deploy_sem_dominio_e_recusado_antes_de_build_e_stack_deploy -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_build_and_deploy_script.py::test_deploy_sem_dominio_e_recusado_antes_de_build_e_stack_deploy -q`: falhou por asserção `0 != 0`: o script ainda segue sem `DOMINIO_RAGPIPELINE`.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-004 o caso `test_roteador_http_redireciona_permanentemente_para_https` em tests/test_deploy_stack.py — Refs: US-002, FR-002, FR-003, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_roteador_http_redireciona_permanentemente_para_https` com o marcador `SPECSFY: SPEC-0032 US-002 FR-002 FR-003 AC-004`: existe roteador no ponto de entrada HTTP (`TRAEFIK_ENTRYPOINT_HTTP`, padrão `web`) com o mesmo domínio e o middleware `redirectscheme` com `scheme=https` e `permanent=true`.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_roteador_http_redireciona_permanentemente_para_https -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_roteador_http_redireciona_permanentemente_para_https -q`: falhou por asserção: nenhum roteador no ponto de entrada `web`.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-005 o caso `test_hsts_tem_validade_curta_e_aceita_variavel` em tests/test_deploy_stack.py — Refs: US-002, FR-002, FR-003, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_hsts_tem_validade_curta_e_aceita_variavel` com o marcador `SPECSFY: SPEC-0032 US-002 FR-002 FR-003 AC-005`: o middleware `headers` declara `stsSeconds` igual a `${HSTS_MAX_AGE_SEGUNDOS:-86400}`; sem variável vale 86400 e com variável o valor definido a substitui.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_hsts_tem_validade_curta_e_aceita_variavel -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_hsts_tem_validade_curta_e_aceita_variavel -q`: falhou por asserção: nenhum middleware de cabeçalhos com HSTS.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-006 o caso `test_hsts_sem_includesubdomains_nem_preload` em tests/test_deploy_stack.py — Refs: US-002, FR-002, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_hsts_sem_includesubdomains_nem_preload` com o marcador `SPECSFY: SPEC-0032 US-002 FR-002 AC-006`: o middleware de cabeçalhos existe e `stsIncludeSubdomains` e `stsPreload` não estão ativos.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_hsts_sem_includesubdomains_nem_preload -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_hsts_sem_includesubdomains_nem_preload -q`: falhou por asserção: nenhum middleware de cabeçalhos com HSTS.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T008 [TEST] [TDD] [US-003] Derivar do AC-007 o caso `test_login_tem_roteador_proprio_com_prioridade_e_limite` em tests/test_deploy_stack.py — Refs: US-003, FR-004, NFR-002, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_login_tem_roteador_proprio_com_prioridade_e_limite` com o marcador `SPECSFY: SPEC-0032 US-003 FR-004 NFR-002 AC-007`: há roteador para `POST /api/v1/auth/login` (`Method` e `Path` na regra) com o middleware `ratelimit`, `priority` numérica maior que a do roteador geral, e o roteador geral não aplica o limite.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_login_tem_roteador_proprio_com_prioridade_e_limite -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_login_tem_roteador_proprio_com_prioridade_e_limite -q`: falhou por asserção: nenhum roteador próprio para o login.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-008 o caso `test_limite_do_login_por_endereco_com_media_e_rajada_configuraveis` em tests/test_deploy_stack.py — Refs: US-003, FR-004, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_limite_do_login_por_endereco_com_media_e_rajada_configuraveis` com o marcador `SPECSFY: SPEC-0032 US-003 FR-004 AC-008`: o `ratelimit` usa o endereço de origem como critério; média e rajada vêm de `LOGIN_RATE_LIMIT_MEDIA` e `LOGIN_RATE_LIMIT_RAJADA` com padrões 10 e 20.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_limite_do_login_por_endereco_com_media_e_rajada_configuraveis -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_limite_do_login_por_endereco_com_media_e_rajada_configuraveis -q`: falhou por asserção: nenhum middleware de limite de tentativas.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-009 o caso `test_limite_do_login_declara_rajada_que_recusa_o_excesso` em tests/test_deploy_stack.py — Refs: US-003, FR-004, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_limite_do_login_declara_rajada_que_recusa_o_excesso` com o marcador `SPECSFY: SPEC-0032 US-003 FR-004 AC-009`: o limite do login declara `burst` positivo e `average` positivo, condição estática para o Traefik responder 429 acima da rajada; a resposta 429 real é conferida na VPS (T027).
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_limite_do_login_declara_rajada_que_recusa_o_excesso -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_limite_do_login_declara_rajada_que_recusa_o_excesso -q`: falhou por asserção: nenhum middleware de limite de tentativas.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T011 [TEST] [TDD] [US-004] Derivar do AC-013 o caso `test_testes_de_dominio_leem_o_stack_sem_rede` em tests/test_deploy_stack.py — Refs: US-004, FR-006, NFR-001, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-013 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_testes_de_dominio_leem_o_stack_sem_rede` com o marcador `SPECSFY: SPEC-0032 US-004 FR-006 NFR-001 AC-013`: com `socket.socket` bloqueado e sem variável de banco, a leitura das labels do frontend funciona só por arquivo e devolve labels não vazias.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_testes_de_dominio_leem_o_stack_sem_rede -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_testes_de_dominio_leem_o_stack_sem_rede -q`: falhou por asserção: o frontend não declara labels.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T012 [TEST] [TDD] [US-004] Derivar do AC-014 o caso `test_stack_com_backend_exposto_e_detectado` em tests/test_deploy_stack.py — Refs: US-004, FR-006, NFR-002, FR-001, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-014 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_stack_com_backend_exposto_e_detectado` com o marcador `SPECSFY: SPEC-0032 US-004 FR-006 NFR-002 FR-001 AC-014`: um stack copiado em memória com `traefik.enable=true` no backend faz a verificação de exposição acusar o backend, enquanto o stack real expõe só o frontend.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_stack_com_backend_exposto_e_detectado -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_stack_com_backend_exposto_e_detectado -q`: falhou por asserção `set() == {'frontend_ragpipeline'}`: nenhum serviço exposto.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T013 [TEST] [TDD] [US-004] Derivar do AC-015 o caso `test_dominio_literal_na_regra_e_detectado` em tests/test_deploy_stack.py — Refs: US-004, FR-006, NFR-001, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-015 na seção 6 e confirmar regra e IDs.
  - [x] **EXECUTE**: Escrever `test_dominio_literal_na_regra_e_detectado` com o marcador `SPECSFY: SPEC-0032 US-004 FR-006 NFR-001 AC-015`: uma regra com domínio literal (` Host(\`exemplo.com\`) `) é detectada pela varredura, e a regra real do stack só usa `${DOMINIO_RAGPIPELINE}`.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_dominio_literal_na_regra_e_detectado -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_stack.py::test_dominio_literal_na_regra_e_detectado -q`: falhou por asserção: o frontend não declara regras de roteamento.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de sintaxe ou de importação.

- [x] T014 [P] [TEST] [US-004] Criar o apoio tests/_rede_falsa.py com `curl`, `openssl` e `getent` falsos que registram as chamadas e simulam DNS, certificado, redirecionamento, HSTS e lentidão — Refs: US-004, FR-005, NFR-003, AC-010, AC-011, AC-016 — Depends: none
  - [x] **PREP**: Ler `tests/_docker_falso.py` e reaproveitar o padrão de `Ambiente` e de lista de ferramentas.
  - [x] **EXECUTE**: Escrever o módulo com cada falha ligada por variável (`FAKE_SEM_DNS`, `FAKE_CERT_INVALIDO`, `FAKE_SEM_REDIRECT`, `FAKE_SEM_HSTS`, `FAKE_LENTO`) e um log de chamadas.
  - [x] **VERIFY**: Importar o módulo em uma sessão Pytest e confirmar que os executáveis falsos são criados e executáveis.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Executado em 2026-10-13: sanidade das ferramentas falsas (`curl` HTTP/HTTPS, cabeçalhos, `-w`, `--max-time` com saída 28, `getent`, `openssl s_client`) com o resultado esperado em cada falha ligada por `FAKE_*`; variáveis: `FAKE_SEM_DNS`, `FAKE_CERT_INVALIDO`, `FAKE_SEM_REDIRECT`, `FAKE_SEM_HSTS`, `FAKE_LENTO`.
  - [x] **IMPROVE**: Manter o apoio independente de rede e de `docker`, para os testes do script rodarem em qualquer máquina.

- [x] T015 [TEST] [TDD] [US-004] Derivar do AC-010 o caso `test_conferencia_aprova_dominio_correto` em tests/test_deploy_conferir_dominio_script.py — Refs: US-004, FR-005, NFR-003, AC-010 — Depends: T014
  - [x] **PREP**: Ler o Gherkin do AC-010 na seção 6 e o apoio de `tests/_rede_falsa.py`.
  - [x] **EXECUTE**: Escrever `test_conferencia_aprova_dominio_correto` com o marcador `SPECSFY: SPEC-0032 US-004 FR-005 NFR-003 AC-010`: com `curl`, `openssl` e `getent` falsos que simulam DNS, certificado, redirecionamento e HSTS corretos, o script lista cada verificação como aprovada e sai com 0.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py::test_conferencia_aprova_dominio_correto -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py::test_conferencia_aprova_dominio_correto -q`: falhou por asserção: `deploy/conferir_dominio.sh` não existe.
  - [x] **IMPROVE**: Confirmar que o caso não depende de rede real nem do `docker`.

- [x] T016 [TEST] [TDD] [US-004] Derivar do AC-011 o caso `test_conferencia_nomeia_cada_falha_e_sai_com_erro` em tests/test_deploy_conferir_dominio_script.py — Refs: US-004, FR-005, NFR-003, FR-003, AC-011 — Depends: T014
  - [x] **PREP**: Ler o Gherkin do AC-011 na seção 6 e o apoio de `tests/_rede_falsa.py`.
  - [x] **EXECUTE**: Escrever `test_conferencia_nomeia_cada_falha_e_sai_com_erro` com o marcador `SPECSFY: SPEC-0032 US-004 FR-005 NFR-003 FR-003 AC-011`: para cada falha simulada (sem DNS, certificado inválido, sem redirecionamento, sem HSTS) a saída nomeia a verificação reprovada e o código é diferente de 0.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py::test_conferencia_nomeia_cada_falha_e_sai_com_erro -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py::test_conferencia_nomeia_cada_falha_e_sai_com_erro -q`: falhou por asserção: `deploy/conferir_dominio.sh` não existe.
  - [x] **IMPROVE**: Confirmar que o caso não depende de rede real nem do `docker`.

- [x] T017 [TEST] [TDD] [US-004] Derivar do AC-012 o caso `test_conferencia_sem_dominio_recusa_sem_consultar_rede` em tests/test_deploy_conferir_dominio_script.py — Refs: US-004, FR-005, NFR-001, AC-012 — Depends: T014
  - [x] **PREP**: Ler o Gherkin do AC-012 na seção 6 e o apoio de `tests/_rede_falsa.py`.
  - [x] **EXECUTE**: Escrever `test_conferencia_sem_dominio_recusa_sem_consultar_rede` com o marcador `SPECSFY: SPEC-0032 US-004 FR-005 NFR-001 AC-012`: sem argumento nem `DOMINIO_RAGPIPELINE` o script sai com erro e mensagem de uso, e o log das ferramentas falsas fica vazio.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py::test_conferencia_sem_dominio_recusa_sem_consultar_rede -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py::test_conferencia_sem_dominio_recusa_sem_consultar_rede -q`: falhou por asserção: `deploy/conferir_dominio.sh` não existe.
  - [x] **IMPROVE**: Confirmar que o caso não depende de rede real nem do `docker`.

- [x] T018 [TEST] [TDD] [US-004] Derivar do AC-016 o caso `test_conferencia_tem_tempo_limite_e_termina_em_60s` em tests/test_deploy_conferir_dominio_script.py — Refs: US-004, NFR-003, AC-016 — Depends: T014
  - [x] **PREP**: Ler o Gherkin do AC-016 na seção 6 e o apoio de `tests/_rede_falsa.py`.
  - [x] **EXECUTE**: Escrever `test_conferencia_tem_tempo_limite_e_termina_em_60s` com o marcador `SPECSFY: SPEC-0032 US-004 NFR-003 AC-016`: com um `curl` falso que dorme além do limite, o script passa `--max-time 10` a cada consulta, termina em até 60 s e sai com código diferente de 0.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py::test_conferencia_tem_tempo_limite_e_termina_em_60s -q` e observar RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: RED observado em 2026-10-13 com `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py::test_conferencia_tem_tempo_limite_e_termina_em_60s -q`: falhou por asserção: `deploy/conferir_dominio.sh` não existe.
  - [x] **IMPROVE**: Confirmar que o caso não depende de rede real nem do `docker`.

#### Fase 2 — US-001 Acessar o sistema por um domínio com HTTPS válido (P1)

**Objetivo**: o frontend é exposto pelo domínio da variável, só ele, com resolvedor e ponto de entrada configuráveis, e o deploy recusa seguir sem domínio.
**Teste independente**: `.venv/bin/python -m pytest tests/test_deploy_stack.py tests/test_deploy_build_and_deploy_script.py -q` passa; na VPS, o domínio abre a tela de login com certificado válido.

- [x] T019 [CODE] [US-001] Declarar em deploy/stack.prod.yml as labels de exposição do frontend (`traefik.enable`, roteador HTTPS por `Host`, resolvedor, ponto de entrada, serviço na porta 3000 com `passHostHeader=true`) — Refs: US-001, FR-001, FR-003, NFR-001, NFR-002, AC-001, AC-002, AC-013, AC-014, AC-015 — Depends: T001, T002, T003, T011, T012, T013
  - [x] **PREP**: Confirmar o RED de T002, T003, T011, T012 e T013 e a documentação arquivada em T001. Reconstruir `docs/` com `$specsfy-documentator` antes de implementar e rodar o monitor de contexto.
  - [x] **EXECUTE**: Acrescentar `deploy.labels` ao `frontend_ragpipeline` com `${DOMINIO_RAGPIPELINE}`, `${TRAEFIK_CERT_RESOLVER:-letsencryptresolver}` e `${TRAEFIK_ENTRYPOINT_HTTPS:-websecure}`, sem labels nos outros serviços.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py -q` e a regressão dos testes de stack já existentes.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Registrar o GREEN e o arquivo alterado.
  - [x] **IMPROVE**: Verificar que nenhum domínio literal entrou no arquivo e registrar a conferência.
  <!-- specsfy:evidence {"task": "T019", "refs": ["US-001", "FR-001", "FR-003", "NFR-001", "NFR-002", "AC-001", "AC-002", "AC-013", "AC-014", "AC-015"], "files": ["deploy/stack.prod.yml", "tests/test_deploy_stack.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_deploy_stack.py -k 'not http and not hsts and not login' -q", "exit": 0}]} -->

  - Registro PREP: RED confirmado em T002/T003/T011/T012/T013; pesquisa T001 validada; documentação reconstruída; monitor CURRENT.

  - Registro EXECUTE: Labels HTTPS declaradas apenas em deploy.labels do frontend; porta 3000 e passHostHeader explícitos. PROJECT.md: sem alteração de finalidade ou capacidade; implementação do acesso já especificado. Documentação reconstruída e check aprovado.

  - Registro VERIFY/VISUAL: 17 passed, 6 deselected no teste focal: not http and not hsts and not login. Correção interna de AC-015 preserva variável antes da verificação. Sem interface; nenhum serviço adicional exposto.

  - Registro EVIDENCE/IMPROVE: GREEN registrado para AC-001/002/013/014/015. Melhoria aplicada: guarda AC-015 corrigida para conferir parametrização sem remover a variável. Labels só no serviço Swarm; domínio real ausente.

- [x] T020 [P] [CODE] [US-001] Exigir `DOMINIO_RAGPIPELINE` e exportar as demais variáveis do Traefik em deploy/build_and_deploy.sh, e dar domínio padrão ao `Ambiente.deploy` em tests/_docker_falso.py — Refs: US-001, FR-001, FR-003, NFR-001, AC-001, AC-002, AC-003 — Depends: T001, T002, T003, T004
  - [x] **PREP**: Confirmar o RED de T002, T003 e T004 e listar os testes existentes que chamam `Ambiente.deploy`. Reconstruir `docs/` com `$specsfy-documentator` antes de implementar e rodar o monitor de contexto.
  - [x] **EXECUTE**: Acrescentar `: "${DOMINIO_RAGPIPELINE:?...}"` antes de qualquer `docker build`, exportar `DOMINIO_RAGPIPELINE` e as variáveis com padrão, e fazer `Ambiente.deploy` definir um domínio de teste por `setdefault`.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_build_and_deploy_script.py tests/test_deploy_secrets_script.py -q` e confirmar que os testes das SPEC-0022 e SPEC-0027 continuam verdes.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Registrar o GREEN e os arquivos alterados.
  - [x] **IMPROVE**: Conferir que a mensagem de erro cita a variável e o comando para defini-la.
  <!-- specsfy:evidence {"task": "T020", "refs": ["US-001", "FR-001", "FR-003", "NFR-001", "AC-002", "AC-003"], "files": ["deploy/build_and_deploy.sh", "tests/_docker_falso.py", "tests/test_deploy_build_and_deploy_script.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_deploy_build_and_deploy_script.py tests/test_deploy_secrets_script.py -q", "exit": 0}]} -->

  - Registro PREP: T004 observado RED antes do código; helper Ambiente já lido; variáveis da seção 10 confirmadas.

  - Registro EXECUTE: Domínio exigido antes dos secrets/builds; sete variáveis exportadas com padrões. Helper de sucesso informa domínio fictício; caso negativo continua sem domínio. Monitor CURRENT; documentação reconstruída e check aprovado.

  - Registro VERIFY/VISUAL: 19 passed em 4,28 s nos scripts de deploy e secrets; SAFE. Sem interface; mensagem cita DOMINIO_RAGPIPELINE, export e o script.

  - Registro EVIDENCE/IMPROVE: GREEN de AC-003 e regressão dos secrets: 19 passed. Mensagem de ausência informa export e o comando. Nenhuma melhoria adicional necessária: validação ocorre antes de acessar o Swarm.

#### Fase 3 — US-002 Ser levado ao HTTPS e ter o navegador lembrando disso (P1)

**Objetivo**: HTTP redireciona de forma permanente para HTTPS e o HSTS começa curto.
**Teste independente**: `.venv/bin/python -m pytest tests/test_deploy_stack.py -k "http or hsts" -q` passa; na VPS, `curl -I http://<domínio>` devolve redirecionamento.

- [x] T021 [CODE] [US-002] Acrescentar em deploy/stack.prod.yml o roteador HTTP com `redirectscheme` permanente e o middleware `headers` de HSTS (86400 s por padrão, sem `includeSubdomains` nem `preload`) — Refs: US-002, FR-002, FR-003, AC-004, AC-005, AC-006 — Depends: T001, T005, T006, T007, T019
  - [x] **PREP**: Confirmar o RED de T005, T006 e T007 e o GREEN de T019. Reconstruir `docs/` com `$specsfy-documentator` antes de implementar e rodar o monitor de contexto.
  - [x] **EXECUTE**: Declarar o roteador no ponto de entrada `${TRAEFIK_ENTRYPOINT_HTTP:-web}` e os dois middlewares, e ligar o middleware de cabeçalhos ao roteador HTTPS.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py -q`.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Registrar o GREEN e o arquivo alterado.
  - [x] **IMPROVE**: Conferir que `stsSeconds` vem de `${HSTS_MAX_AGE_SEGUNDOS:-86400}` e que o redirecionamento não cria laço com o roteador HTTPS.
  <!-- specsfy:evidence {"task": "T021", "refs": ["US-002", "FR-002", "FR-003", "AC-004", "AC-005", "AC-006"], "files": ["deploy/stack.prod.yml"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_deploy_stack.py -k 'not login' -q", "exit": 0}]} -->

  - Registro PREP: RED de T005/T006/T007 confirmado; T019 GREEN. Pesquisa dos middlewares lida; documentação atual.

  - Registro EXECUTE: Roteador HTTP com redirecionamento permanente; HSTS configurável só em HTTPS, sem subdomínios/preload. Monitor CURRENT; docs reconstruídas e check aprovado; PROJECT.md sem impacto material.

  - Registro VERIFY/VISUAL: 20 passed, 3 deselected em 2,21 s. Os casos de login seguem RED até T022. Sem interface; HTTP redireciona, HTTPS usa HSTS sem redirect.

  - Registro EVIDENCE/IMPROVE: AC-004/005/006 GREEN. HSTS usa variável com 86400 s; nenhum laço, pois redirect fica só no HTTP. Nenhuma melhoria adicional necessária.

#### Fase 4 — US-003 Ter o login protegido contra tentativas repetidas (P2)

**Objetivo**: só `POST /api/v1/auth/login` sofre o limite por endereço, com prioridade sobre o roteador geral.
**Teste independente**: `.venv/bin/python -m pytest tests/test_deploy_stack.py -k login -q` passa; na VPS, exceder a rajada devolve 429.

- [x] T022 [CODE] [US-003] Acrescentar em deploy/stack.prod.yml o roteador do login com `priority` explícita e o middleware `ratelimit` por endereço de origem (média e rajada por variável) — Refs: US-003, FR-004, NFR-002, AC-007, AC-008, AC-009 — Depends: T001, T008, T009, T010, T021
  - [x] **PREP**: Confirmar o RED de T008, T009 e T010 e o GREEN de T021. Reconstruir `docs/` com `$specsfy-documentator` antes de implementar e rodar o monitor de contexto.
  - [x] **EXECUTE**: Declarar o roteador com `Method(`POST`) && Path(`/api/v1/auth/login`)` e prioridade maior que a do geral, e o `ratelimit` com `${LOGIN_RATE_LIMIT_MEDIA:-10}` e `${LOGIN_RATE_LIMIT_RAJADA:-20}`.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_stack.py -q`.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Registrar o GREEN e o arquivo alterado.
  - [x] **IMPROVE**: Comparar o `sourceCriterion` e a unidade da média com a documentação arquivada em T001 e corrigir se divergirem.
  <!-- specsfy:evidence {"task": "T022", "refs": ["US-003", "FR-004", "NFR-002", "AC-007", "AC-008", "AC-009"], "files": ["deploy/stack.prod.yml"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_deploy_stack.py -q", "exit": 0}]} -->

  - Registro PREP: T008-T010 RED registrado; T021 GREEN. RateLimit oficial v2.11 lido; média por minuto, origem remota e prioridades confirmadas. Documentação atual.

  - Registro EXECUTE: Roteador exato de POST login com prioridade 100 acima de 10, HSTS antes de RateLimit; média 10/min e rajada 20 configuráveis, depth zero. Monitor CURRENT; docs check aprovado. PROJECT.md sem impacto material.

  - Registro VERIFY/VISUAL: 23 testes do stack GREEN; certificado e middleware HSTS também no login. Sem interface. A prova real de 429 continua pendente em T027.

  - Registro EVIDENCE/IMPROVE: AC-007/008/009 (contrato estático) GREEN; efeito real de AC-009 reservado a T027. Melhoria: HSTS precede limite, cobrindo respostas 429. period=1m e depth=0 comparados à pesquisa oficial.

#### Fase 5 — US-004 Conferir o domínio depois do deploy com um comando (P2)

**Objetivo**: um script confere DNS, certificado, redirecionamento e HSTS, com tempo limite.
**Teste independente**: `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py -q` passa; na VPS, `deploy/conferir_dominio.sh <domínio>` termina com 0.

- [x] T023 [P] [CODE] [US-004] Criar deploy/conferir_dominio.sh com as verificações de DNS, certificado, redirecionamento e HSTS, `--max-time 10` por consulta e saída com código diferente de 0 ao reprovar — Refs: US-004, FR-005, FR-003, NFR-001, NFR-003, AC-010, AC-011, AC-012, AC-016 — Depends: T001, T014, T015, T016, T017, T018
  - [x] **PREP**: Confirmar o RED de T015 a T018 e o apoio de T014. Reconstruir `docs/` com `$specsfy-documentator` antes de implementar e rodar o monitor de contexto.
  - [x] **EXECUTE**: Escrever o script em `bash` com `set -euo pipefail`, domínio por argumento ou `DOMINIO_RAGPIPELINE`, lista de verificações aprovadas e reprovadas e código de saída agregado.
  - [x] **VERIFY**: Rodar `.venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py -q` e `bash -n deploy/conferir_dominio.sh`.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Registrar o GREEN e o arquivo alterado.
  - [x] **IMPROVE**: Conferir que o script não imprime nada além do domínio informado e que o tempo total fica abaixo de 60 s no caso lento.
  <!-- specsfy:evidence {"task": "T023", "refs": ["US-004", "FR-005", "FR-003", "NFR-001", "NFR-003", "AC-010", "AC-011", "AC-012", "AC-016"], "files": ["deploy/conferir_dominio.sh"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_deploy_conferir_dominio_script.py -q", "exit": 0}]} -->

  - Registro PREP: RED de T015-T018 confirmado; RedeFalsa de T014 lida. Script terá getent/openssl/curl com limites de 10 segundos, sem persistência nem interface; docs atuais.

  - Registro EXECUTE: Script Bash executável com quatro verificações, certificado e hostname sem insecure, limites de 10 s em DNS/TLS/HTTP/HTTPS; monitor CURRENT e docs check aprovado. Sem impacto material em PROJECT.md.

  - Registro VERIFY/VISUAL: 4 passed em 31,54 s com rede simulada; bash -n aprovado. Caso lento abaixo de 60 s; certificado inválido, DNS, redirect e HSTS ausentes reprovados. Sem interface.

  - Registro EVIDENCE/IMPROVE: AC-010/011/012/016 GREEN. Melhoria aplicada: entrada restrita a hostname, verificação de nome TLS e redirect permanente para o mesmo hostname; respostas TLS não aparecem na saída.

#### Fase de documentação

- [x] T024 [DOC] [US-001] Documentar em deploy/SECRETS.md as variáveis `DOMINIO_RAGPIPELINE`, `TRAEFIK_CERT_RESOLVER`, `TRAEFIK_ENTRYPOINT_HTTPS`, `TRAEFIK_ENTRYPOINT_HTTP`, `HSTS_MAX_AGE_SEGUNDOS`, `LOGIN_RATE_LIMIT_MEDIA` e `LOGIN_RATE_LIMIT_RAJADA`, sem valores reais, e o uso de `deploy/conferir_dominio.sh` — Refs: FR-001, FR-003, NFR-001 — Depends: T020, T022, T023
  - [x] **PREP**: Ler `deploy/SECRETS.md` e as variáveis efetivamente usadas em `deploy/stack.prod.yml` e `deploy/build_and_deploy.sh`.
  - [x] **EXECUTE**: Acrescentar a seção das variáveis com o padrão de cada uma e o comando de conferência, sem nenhum domínio, credencial ou segredo.
  - [x] **VERIFY**: Conferir por busca que o documento não contém domínio literal e que cada variável citada existe no stack.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Registrar o comando de busca e o resultado.
  - [x] **IMPROVE**: Apontar no texto que a verificação real do certificado só acontece na VPS.

  - Registro PREP: SECRETS.md e sete variáveis efetivamente usadas nos scripts e stack lidos; sem valores reais.

  - Registro EXECUTE: Seção operacional acrescentada em deploy/SECRETS.md: sete variáveis, padrões, dependências do checker, códigos de saída e limites da prova local/VPS.

  - Registro VERIFY/VISUAL: Busca rg confirmou sete variáveis no documento, script e labels, sem domínio real. Sem interface; exemplos recebem hostname interativamente e a conferência real na VPS está explícita.

  - Registro EVIDENCE/IMPROVE: deploy/SECRETS.md conferido por rg; ressalva de certificado e 429 reais documentada. Nenhuma melhoria adicional necessária.

- [x] T025 [DOC] [US-001] Revisar `.specsfy/STACK.md` e `PROJECT.md` quanto ao Traefik compartilhado e ao domínio, e registrar a justificativa quando não houver impacto — Refs: FR-001, NFR-002 — Depends: T022
  - [x] **PREP**: Rodar `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` e ler as menções a proxy e rede em `STACK.md` e `PROJECT.md`.
  - [x] **EXECUTE**: Atualizar `STACK.md` com o uso do Traefik compartilhado por labels, se ainda não constar; manter `PROJECT.md` sem texto artificial quando não houver impacto material.
  - [x] **VERIFY**: Rodar o monitor de novo e obter `CURRENT`.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Registrar o resultado do monitor e a justificativa de `PROJECT.md` e `RULES.md`.
  - [x] **IMPROVE**: Registrar a ausência de regra nova ou a regra confirmada com a pessoa responsável.

  - Registro PREP: Monitor CURRENT; STACK.md e PROJECT.md lidos. Rede compartilhada já existe; acrescentar fato implementado de roteamento HTTPS por labels, sem alterar finalidade do produto.

  - Registro EXECUTE: STACK.md atualizado de forma aditiva com fontes executáveis. PROJECT.md preservado: acesso público materializa infraestrutura para capacidades existentes; sem mudança de finalidade, dados ou fluxo. RULES.md: nenhuma regra nova.

  - Registro VERIFY/VISUAL: Monitor Context: CURRENT após atualização aditiva da stack. Sem interface; revisão de PROJECT.md e RULES.md sem alteração material.

  - Registro EVIDENCE/IMPROVE: STACK.md registra fontes das labels e limites da prova local. Nenhuma regra nova; nenhuma melhoria adicional necessária.

#### Fase final — Qualidade

- [x] T026 [TEST] Executar a regressão completa e a rastreabilidade da SPEC-0032 em tests/test_deploy_stack.py — Refs: US-001, US-002, US-003, US-004, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016 — Depends: T019, T020, T021, T022, T023, T024, T025
  - [x] **PREP**: Listar os testes e checks do projeto (Pytest completo, Ruff, `check_traceability.mjs`, `test_spec_markers.py`).
  - [x] **EXECUTE**: Rodar a suíte completa, o lint e a rastreabilidade.
  - [x] **VERIFY**: Confirmar zero falhas e zero lacunas de rastreabilidade.
  - [x] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [x] **EVIDENCE**: Registrar contagens e comandos finais.
  - [x] **IMPROVE**: Registrar a retrospectiva do processo e o que ajustar nos próximos itens do M03.

  - Registro PREP: Checks: Pytest completo, Ruff, traceability, test_spec_markers, frontend Vitest/lint/typecheck/build e sintaxe Bash. Proteção do banco será conferida antes das suítes.

  - Registro EXECUTE: Primeira suíte completa executada: 578 passed, 3 failed por Tesseract ausente, 1 skipped opt-in preexistente. Runtime OCR temporário corrigido: regressão focal 17 passed em 51,05 s. Ruff, rastreabilidade, lint/tipos/build e 225 testes frontend aprovados; repetição completa em andamento para VERIFY.

  - Registro VERIFY/VISUAL: Regressão integral final: exit 0, 581 passed, 1 skipped preexistente e 2 warnings em 890,56 s. Frontend 225 passed; Ruff/lint/tipos/build e rastreabilidade 29/29 aprovados. Sem interface nesta entrega; VISUAL não aplicável por alterar apenas infraestrutura, scripts e documentação.

  - Registro EVIDENCE/IMPROVE: Resultados e comando exato registrados na seção 13. Retrospectiva: conferir binários de sistema e preservar PATH antes da próxima regressão ampla; runtime OCR temporário validado sem alteração global. Nenhuma mudança adicional de produção necessária.

- [ ] T027 [OPS] Conferir o resultado real na VPS: rodar o deploy com `DOMINIO_RAGPIPELINE`, executar `deploy/conferir_dominio.sh`, abrir o domínio no navegador e exceder a rajada do login — Refs: FR-001, FR-002, FR-004, FR-005, AC-009, AC-010 — Depends: T026, T028
  - [ ] **PREP**: Combinar com a pessoa responsável o domínio, o DNS apontado e a janela do deploy; nenhum valor é gravado no repositório.
  - [ ] **EXECUTE**: A pessoa responsável executa o deploy e o script na VPS e informa a saída; excedendo a rajada, o login deve responder 429.
  - [ ] **VERIFY**: Confirmar código 0 do script, cadeado válido, redirecionamento de HTTP para HTTPS, cabeçalho HSTS e 429 acima da rajada.
  - [ ] **VISUAL**: Não aplicável: a tarefa não toca interface para pessoas (spec, seção 10).
  - [ ] **EVIDENCE**: Registrar na seção 13 o que foi observado, sem domínio nem credencial.
  - [ ] **IMPROVE**: Ajustar variáveis (ponto de entrada HTTP, limite, HSTS) se a VPS divergir das suposições e registrar a decisão.

- [x] T028 [OPS] Ensaiar localmente as imagens Docker atuais e os fluxos da aplicação, com configuração temporária em /tmp/rag-0032-ensaio/compose.yml e evidência na seção 13, antes da VPS — Refs: US-004, FR-001, FR-005, NFR-001, NFR-002, AC-001, AC-010, AC-013 — Depends: T026
  - [x] **PREP**: Confirmar socket Docker local, imagens, portas disponíveis, contratos de inicialização e isolamento dos volumes; preservar o stack local anterior.
  - [x] **EXECUTE**: Construir imagens pelos Dockerfiles existentes, subir os cinco serviços em ambiente separado, preparar somente o banco de ensaio e criar uma pessoa de teste.
  - [x] **VERIFY**: Conferir frontend e proxy, login, menus, permissões, conexões, prévia, fila/worker, indexação Qdrant e conversão; registrar explicitamente integrações simuladas ou dependentes de credencial externa.
  - [x] **VISUAL**: Inspecionar a aplicação real nos viewports desktop e mobile, verificando bordas, espaçamentos, margens, padding, tipografia, navegação, formulários, foco, overflow e estados percorridos; não criar nem alterar interface.
  - [x] **EVIDENCE**: Registrar comandos, resultados, URL local, arquivos de evidência e limites; manter dados e chaves de teste fora do repositório.
  - [x] **IMPROVE**: Registrar um procedimento repetível de retomar ou parar o ensaio sem apagar volumes e a melhoria segura encontrada, ou justificar a ausência de ajuste.

  - Registro PREP: Socket unix local confirmado; stack anterior na porta 3000 preservado. Imagens novas construídas com tags ensaio-0032; porta 3300 livre. Ensaio usará rede e volumes Compose próprios e banco rag_pipeline_ensaio_0032_testing, com APP_ENV=testing; credenciais fictícias fora do repositório.

  - Registro EXECUTE: Imagens atuais construídas; cinco serviços e init de migrations/fila em rede e volumes Compose isolados. APP_ENV=testing e banco próprio confirmados. Frontend disponível em http://localhost:3300; owner/member fictícios preparados. Serviço auxiliar de embeddings simula somente a API externa, sem alterar o código de produto.

  - Registro VERIFY/VISUAL/EVIDENCE/IMPROVE: Ensaio aprovado: 42 verificações HTTP, 11 conversões nos 10 formatos, 39 capturas desktop/mobile e proxy local com 301/HSTS/429. Resultados, comandos, limitações de IA/TLS e stop/start registrados na seção 13 e no runbook. Sem alteração de produto nem publicação VPS.

### 15. Ordem de execução

- Caminho crítico: T001 → T002/T003/T011/T012/T013 → T019 → T021 → T022 → T024/T025 → T026 → T028 (Docker local) → aceite local da pessoa → T027 (VPS, posteriormente).
- Tarefas paralelas: T004, T014, T020 e T023 usam arquivos distintos das demais e não dependem delas; T015 a T018 compartilham um arquivo e correm em sequência; as tarefas que editam `deploy/stack.prod.yml` (T019, T021, T022) correm em sequência.
- Estratégia de MVP: T001, T002, T003, T011, T012, T013, T019, T004 e T020 entregam o domínio com HTTPS (US-001); US-002, US-003 e US-004 acrescentam redirecionamento, limite e conferência. T027 só se fecha na VPS.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0022 (stack de produção) e SPEC-0027 (secrets), ambas `Complete`.
- Traefik compartilhado já instalado na VPS, com resolvedor de certificado configurado.
- Domínio e DNS apontando para a VPS, a cargo da pessoa responsável.
- Backlog 0032 (runbook de deploy), que aponta para o script de conferência.

#### Riscos

- HSTS errado prende o navegador em HTTPS com configuração quebrada → validade inicial de um dia.
- Nome do ponto de entrada HTTP diferente de `web`, ou outro ambiente com nomes diferentes → o script de conferência acusa certificado inválido; as variáveis permitem corrigir sem editar o stack.
- Limite de tentativas afeta a equipe atrás de um mesmo endereço (NAT do escritório) → valores configuráveis por variável.
- A verificação real do certificado só acontece na VPS (mesmo limite da SPEC-0022).

#### Suposições

- Valores iniciais do limite de tentativas: média de 10 por minuto e rajada de 20 por endereço (reversíveis; pendentes de confirmação).
- Validade inicial do HSTS de 86400 segundos, a subir quando a configuração estiver estável.
- Os nomes `letsencryptresolver` e `websecure` foram confirmados pelas labels do n8n na mesma VPS. O ponto de entrada HTTP `web` segue como suposição; o n8n não o mostra.
- O serviço do frontend declara `loadbalancer.server.port=3000` e `passHostHeader=true`, como o n8n faz para a porta dele.
- O Traefik enxerga o endereço real de origem, sem CDN na frente.

### 17. Decisões

- **DEC-001**: domínio por variável de ambiente — o repositório e o stack guardam só a regra, e o mesmo stack serve a outro ambiente (backlog 0029, Pergunta 2).
- **DEC-002**: só o frontend é exposto; `/api/*` passa por ele — menor superfície, e já é como o stack funciona (Pergunta 3).
- **DEC-003**: HSTS com validade curta, sem `includeSubdomains` nem `preload` — reduz o risco de prender o navegador (Pergunta 4).
- **DEC-004**: limite de tentativas por endereço só no login, aplicado pelo Traefik — barato e sem mudar o backend (Pergunta 7).
- **DEC-005**: prova por teste das labels e script de conferência — a emissão real do certificado só existe na VPS (Pergunta 5).

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam (execução integral final e checks da seção 13; opt-in pago preexistente registrado).
