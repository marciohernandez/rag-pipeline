# Especificação integrada: Domínio, HTTPS e reverse proxy para o Beta

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0032 |
| Slug | 0032-dominio-https-e-reverse-proxy-para-o-beta |
| Status | Draft |
| Effort | 4 |
| Effort updated at | 2026-10-13 |
| Effort rationale | Labels de Traefik em um stack já existente, mais um teste e um script de conferência; sem schema nem interface. O risco está na verificação real, que só ocorre na VPS (perfil `standard`). |
| ClickUp Task | |
| Milestones | M03 |
| Definition Gate | Pending |
| Plan Gate | Pending |
| Delivery Gate | Pending |
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

- Nenhuma fonte externa consultada nesta definição. A documentação do Traefik sobre labels de Swarm, middlewares `redirectscheme`, `headers` e `ratelimit` deve ser consultada e arquivada em `research/` antes da implementação.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: qual domínio? → **A**: um subdomínio de um domínio que a pessoa já tem, informado por variável no deploy (backlog 0029, Perguntas 1 e 2).
- **Q**: o que fica exposto? → **A**: só o frontend; `/api/*` passa por ele (Pergunta 3).
- **Q**: HTTP e HSTS? → **A**: HTTP redireciona para HTTPS e o HSTS começa com validade curta (Pergunta 4).
- **Q**: como provar? → **A**: teste automático das labels e script de conferência pós-deploy (Pergunta 5).
- **Q**: nomes do resolvedor e do ponto de entrada? → **A**: variáveis, com padrões (Pergunta 6); os nomes reais foram confirmados em 2026-10-13 pelas labels do n8n que já roda na mesma VPS: resolvedor `letsencryptresolver` e ponto de entrada HTTPS `websecure`.
- **Q**: quem acessa a tela de login? → **A**: qualquer pessoa na internet, com login por pessoa e limite de tentativas por endereço (Pergunta 7).

#### Dúvidas abertas

- **Pendente**: nome do ponto de entrada HTTP (sem HTTPS) no Traefik da VPS. A spec assume `web`; as labels do n8n fornecidas só mostram o ponto de entrada HTTPS.
- **Pendente**: valor final do limite de tentativas de login e da validade final do HSTS. A spec assume valores iniciais reversíveis (ver Suposições).

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
- **FR-004**: O login (`POST /api/v1/auth/login`) deve ter um roteador próprio com middleware de limite de tentativas por endereço de origem, com média e rajada configuráveis por variável; o restante do domínio não aplica esse limite.
- **FR-005**: O script `deploy/conferir_dominio.sh` deve verificar DNS, certificado válido, redirecionamento de HTTP para HTTPS e cabeçalho HSTS, listar cada verificação e terminar com código 0 só quando todas passarem.
- **FR-006**: A suíte `tests/test_deploy_stack.py` deve verificar, por leitura do arquivo, as labels de domínio, redirecionamento, HSTS, limite de tentativas, os nomes por variável e a exposição só do frontend.

#### Não funcionais

- **NFR-001**: Segurança e confidencialidade: nenhum nome de domínio, credencial ou segredo aparece em texto no repositório. **Verificação**: teste de varredura do stack e dos scripts (AC-001, AC-013, AC-015).
- **NFR-002**: Superfície exposta mínima: somente o frontend é exposto por labels; backend, worker, Postgres e Qdrant não o são. **Verificação**: teste de labels por serviço (AC-001, AC-014).
- **NFR-003**: Operabilidade: o script de conferência termina em até 60 segundos, com tempo limite por consulta. **Verificação**: teste do script contra um endereço que não responde (AC-016) e conferência manual na VPS.

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

- A documentação do Traefik (labels de Swarm, `redirectscheme`, `headers`, `ratelimit`) deve ser arquivada em `research/` antes da implementação.

#### Eventos e outros contratos

- Variáveis de ambiente do deploy: `DOMINIO_RAGPIPELINE` (obrigatória), `TRAEFIK_CERT_RESOLVER` (padrão `letsencryptresolver`), `TRAEFIK_ENTRYPOINT_HTTPS` (padrão `websecure`), `TRAEFIK_ENTRYPOINT_HTTP` (padrão `web`), `HSTS_MAX_AGE_SEGUNDOS` (padrão 86400), `LOGIN_RATE_LIMIT_MEDIA` e `LOGIN_RATE_LIMIT_RAJADA` (valores iniciais na seção 16).

### 11. Estratégia TDD

- **Unidade**: leitura do stack e verificação das labels em `tests/test_deploy_stack.py`.
- **Integração/contrato**: `deploy/build_and_deploy.sh` e `deploy/conferir_dominio.sh` executados com comandos simulados em `tests/`, no padrão de `tests/test_deploy_build_and_deploy_script.py`.
- **BDD/aceite**: o Gherkin da seção 6 orienta os casos.
- **Runner TDD**: Pytest, runner já usado no projeto.
- **E2E**: Não aplicável.
- **Verificação manual**: certificado real, DNS real e limite de tentativas só existem na VPS; a pessoa responsável roda o script de conferência e a lista de verificação do runbook.

Os casos TDD, o RED observado e as tarefas serão derivados por `$specsfy-05-tasks` e `$specsfy-06-tdd-bdd` depois do Definition Gate.

### 12. Plano de testes e rastreabilidade

Será preenchido por `$specsfy-05-tasks` com um caso por AC.

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0032-dominio-https-e-reverse-proxy-para-o-beta/spec.md`
- **Achados**: Pending.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/draft/0032-dominio-https-e-reverse-proxy-para-o-beta/spec.md`
- **Achados**: Pending.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0032-dominio-https-e-reverse-proxy-para-o-beta/spec.md .`
- **Achados**: Pending.

### 14. Tarefas

Serão geradas por `$specsfy-05-tasks` depois do Definition Gate.

### 15. Ordem de execução

Será definida por `$specsfy-05-tasks`.

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

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
