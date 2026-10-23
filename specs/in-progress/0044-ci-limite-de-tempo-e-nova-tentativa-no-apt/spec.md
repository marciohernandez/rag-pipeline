# Especificação integrada: CI: limite de tempo e nova tentativa no passo de instalação do apt

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0044 |
| Slug | 0044-ci-limite-de-tempo-e-nova-tentativa-no-apt |
| Status | Implementing |
| Effort | 3 |
| Effort updated at | 2026-10-23 |
| Effort rationale | Uma mudança pequena em um workflow e em um script de shell, com testes que simulam o apt; o risco está em não esconder falhas reais e em não quebrar a esteira que protege a main. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-10-23 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O job "Ruff and Pytest" do CI fica pendente por 15 a 30 minutos quando o passo "Install system packages for document conversion" é lento. Esse passo roda `apt-get update` e `apt-get install` de tesseract e libreoffice, leva cerca de 1 minuto quando tudo corre bem e não tem limite de tempo nem nova tentativa. Foi observado nos PRs #77, #78 e #81: no #78 o passo durou cerca de 16 minutos (12:49 a 13:05 UTC) e no #81 ficou 15 minutos nele (13:45 a 14:00 UTC). O Ruff e o Pytest não foram a causa. Depois da entrega do limite com nova tentativa, o PR #83 mostrou que a lentidão é do download dos pacotes: o `apt-get update` baixa 12,6 MB em 1 segundo, mas o `apt-get install` precisa de 121 MB (71 pacotes, quase todos do LibreOffice) e o espelho os entrega a cerca de 40 KB/s, então nenhuma tentativa de 5 minutos termina. A `main` exige o check "Ruff and Pytest", então o merge fica bloqueado até a pessoa cancelar a execução e reexecutá-la à mão, o que resolveu nas três vezes (a segunda tentativa passou em cerca de 6 minutos).

#### Resultado desejado

O passo do apt é cancelado depois de 5 minutos e tentado de novo, até 3 tentativas. Se as 3 falharem, o job falha com uma mensagem legível. O job "Ruff and Pytest" tem um teto de 25 minutos. O CI instala só os pacotes que a suíte usa de verdade, `tesseract-ocr` e `tesseract-ocr-por`, e deixa de baixar o LibreOffice, que os testes simulam. Os gatilhos de push e de pull request, os comandos de Ruff e Pytest, o job do frontend e a imagem de produção ficam como estão.

#### Métricas de sucesso

- Pior caso do passo do apt: 15 minutos (3 tentativas de 300 segundos), contra os 16 a 30 minutos observados. **Observação**: teste estático dos valores padrão do script e execução simulada com limite curto.
- 0 reexecuções manuais por lentidão do apt nos PRs seguintes. **Observação**: acompanhamento dos próximos PRs e do histórico de execuções do GitHub.
- Download do passo do apt cai de 121 MB para cerca de 10 MB. **Observação**: linha "Need to get" no registro do passo no CI do PR que entregar a mudança.
- 0 mudanças nos comandos de Ruff e Pytest e nos gatilhos do CI. **Observação**: testes existentes de `tests/test_ci_gates.py` e os novos casos desta spec.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: Em que passo o job trava? → no passo "Install system packages for document conversion" de `.github/workflows/ci.yml`: na primeira tentativa do PR #78 ele levou de 12:49:59 a 13:05:53 UTC e o Pytest só começou depois. Impacto: a correção fica nesse passo (FR-001, FR-002).
- **R-002**: O que o CI já tem de resiliência? → nada no passo do apt; o job inteiro não declara `timeout-minutes` (o padrão do GitHub é 360 minutos). Impacto: o teto do job é novo (FR-003).
- **R-003**: Quais regras e testes tocam o workflow? → a regra confirmada de `.specsfy/RULES.md` (Ruff e Pytest a cada push de branch de fase) e `tests/test_ci_gates.py`, que confere gatilhos, comandos, ausência de segredo e o serviço de Postgres. Impacto: gatilhos e comandos ficam intactos (FR-004).
- **R-004**: Dá para ter nova tentativa sem action de terceiros? → sim, com um laço de shell e o comando `timeout`, em um script versionado no repositório. Impacto: sem nova dependência na cadeia de suprimentos (NFR-002, DEC-004).
- **R-005**: Por que o limite com nova tentativa não destravou o PR #83? → nas execuções 40022178239 e 40022165408 as 3 tentativas estouraram 300 s; o `apt-get update` levou 1 s (12,6 MB a 9,4 MB/s), mas o `install` precisava de 121 MB e avançou cerca de 12 MB por tentativa (121, depois 109, depois 99 MB faltando), a cerca de 40 KB/s. Quase todo o volume é do LibreOffice. A VPS de desenvolvimento não tem `soffice` instalado e a suíte completa passou nela (857 passed, 1 skipped, 2026-10-23); os testes de `tests/test_conversion_legacy_office.py` simulam o `soffice`. O Tesseract existe na VPS e é usado pelos testes de OCR. Impacto: o CI deixa de instalar o LibreOffice (FR-005, DEC-006).

#### Fontes e contexto consultados

- `specs/backlog/0049-ci-limite-de-tempo-e-nova-tentativa-no-passo-de-instalacao-do-apt.md` e a captura `specs/inbox/2026-10-23-130907-ci-trava-no-passo-de-instalacao-de-pacotes-do-sistema-apt.md`.
- `.github/workflows/ci.yml` e `tests/test_ci_gates.py`.
- `specs/completed/0007-ruff-e-esteira-de-integracao-continua/spec.md` (define o workflow e afirma que não há retry automático).
- `.specsfy/RULES.md`, seção Testes.
- Logs das execuções 39947575814 (PR #78), 39963832034 (PR #81), 40022178239 e 40022165408 (PR #83) do GitHub Actions, `deploy/backend/Dockerfile` e `tests/test_conversion_legacy_office.py`, e a proteção da `main` (checks exigidos: "Ruff and Pytest" e "Frontend (lint, types, tests, build)").

#### Documentação consultada

- Sintaxe de workflow do GitHub Actions: `timeout-minutes` em job e em passo, e `run` com script; consultada de memória do uso no próprio repositório. Nenhuma fonte externa foi copiada.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo; as evidências são locais e estão nos arquivos e nas execuções citados.

#### Dúvidas respondidas

- **Q**: qual o alcance da correção? → **A**: só limite de tempo e nova tentativa no passo do apt, mantendo os gatilhos de push e de pull request (decisão da pessoa responsável, 2026-10-23, DEC-001).
- **Q**: qual o limite do passo? → **A**: 5 minutos por tentativa, com até 3 tentativas (DEC-002).
- **Q**: haverá um teto para o job inteiro? → **A**: sim, 25 minutos para o job "Ruff and Pytest" (DEC-003).
- **Q**: como resolver a lentidão que o limite com nova tentativa não resolveu? → **A**: "Tirar o LibreOffice do CI e instalar só o Tesseract (de ~121 MB para ~10 MB); mudança mínima, sem dependência nova" (resposta 1 da pessoa responsável, 2026-10-23, DEC-006).

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Script `.github/scripts/instalar_pacotes_apt.sh` com limite de 300 segundos por tentativa e até 3 tentativas.
- Passo do `ci.yml` chamando o script, com limite de segurança do próprio passo.
- Teto de 25 minutos no job "Ruff and Pytest".
- Lista de pacotes do CI restrita a `tesseract-ocr` e `tesseract-ocr-por`.
- Testes em `tests/test_ci_apt_resiliencia.py` que simulam o apt com comandos falsos e conferem o workflow.

#### Fora de escopo

- Mudar os gatilhos de push e de pull request.
- Cache dos pacotes do apt e troca do espelho.
- Os pacotes da imagem de produção em `deploy/backend/Dockerfile`, que continua instalando o LibreOffice.
- O job do frontend e qualquer código da aplicação.
- Nova tentativa para Ruff ou Pytest.
- Reabrir ou editar a SPEC-0007.

#### Atores

- **Pessoa que abre PRs**: espera o CI liberar o merge e hoje precisa cancelar e reexecutar à mão.
- **GitHub Actions**: executa o workflow, aplica os limites e publica o resultado no commit e no PR.

### 4. Princípios e restrições do projeto

- **PR-001**: o CI roda Ruff e Pytest a cada push de branch de fase e em pull request (`.specsfy/RULES.md` e o requisito do workflow da SPEC-0007); os gatilhos não mudam.
- **PR-002**: o workflow não recebe segredo, credencial nem variável de ambiente do projeto além do banco de teste já declarado (requisito do workflow da SPEC-0007).
- **PR-003**: as actions ficam fixadas por SHA de 40 caracteres (princípios e requisito de versão fixada da SPEC-0007); nenhuma action nova é adicionada.
- **PR-004**: a verificação não é desligada para destravar o merge; a nova tentativa vale só para a instalação dos pacotes do sistema.

### 5. Histórias de usuário

#### US-001 — Instalar os pacotes do sistema com limite de tempo e nova tentativa (P1)

Como pessoa que abre PRs, quero que o passo do apt seja cancelado depois de 5 minutos e tentado de novo, para não esperar 15 a 30 minutos nem reexecutar à mão.

**Por que P1**: o problema ocorreu em três PRs seguidos e bloqueia o merge.
**Teste independente**: executar o script com um apt falso que falha, e outro que demora mais que o limite, e observar as tentativas e o código de saída.
**Requisitos**: FR-001, FR-002, FR-005, NFR-001

#### US-002 — Limitar o job e preservar o resto da esteira (P2)

Como pessoa que abre PRs, quero um teto para o job "Ruff and Pytest" e a garantia de que gatilhos, comandos e o job do frontend não mudam, para que o CI fique previsível sem perder o que ele já verifica.

**Por que P2**: protege contra um travamento em outro passo e evita regressão da esteira.
**Teste independente**: ler o workflow e conferir o teto, os gatilhos, os comandos, as actions fixadas e o job do frontend.
**Requisitos**: FR-003, FR-004, NFR-002

### 6. Cenários BDD de aceite

#### AC-001 — Cada tentativa tem limite de 300 segundos

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-001
Feature: Limite de tempo por tentativa

  Scenario: Uma tentativa lenta é cancelada pelo limite
    Given o script de instalação com limite padrão de 300 segundos
    And um apt falso que demora mais que o limite configurado para o teste
    When o script roda
    Then a tentativa é cancelada pelo limite e não bloqueia o script
```

#### AC-002 — Até 3 tentativas

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-002
Feature: Nova tentativa do apt

  Scenario: O apt falha em todas as tentativas
    Given um apt falso que sempre falha
    When o script roda com o padrão de 3 tentativas
    Then o apt é chamado em exatamente 3 tentativas
```

#### AC-003 — Falha final legível

**Cobre**: US-001, FR-002

```gherkin
@US-001 @FR-002 @AC-003
Feature: Falha final do passo

  Scenario: As 3 tentativas falham
    Given um apt falso que sempre falha
    When o script termina
    Then o código de saída é diferente de zero
    And a última mensagem diz que a instalação falhou após 3 tentativas
```

#### AC-004 — Sucesso na segunda tentativa

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-004
Feature: Recuperação na nova tentativa

  Scenario: A primeira tentativa falha e a segunda passa
    Given um apt falso que falha uma vez e depois funciona
    When o script roda
    Then o código de saída é zero
    And o apt não é chamado uma terceira vez
```

#### AC-005 — Teto de 25 minutos no job

**Cobre**: US-002, FR-003, NFR-001

```gherkin
@US-002 @FR-003 @NFR-001 @AC-005
Feature: Teto do job Ruff and Pytest

  Scenario: O job declara o teto
    Given o workflow .github/workflows/ci.yml
    When o job "Ruff and Pytest" é lido
    Then ele declara timeout-minutes igual a 25
```

#### AC-006 — Gatilhos e comandos preservados

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-006
Feature: Esteira preservada

  Scenario: Gatilhos e comandos continuam os mesmos
    Given o workflow depois da mudança
    When os gatilhos e os comandos são lidos
    Then o workflow roda em push e em pull_request
    And continua executando uv run ruff check e uv run pytest
```

#### AC-007 — Sem nova tentativa para Pytest e sem action de terceiros

**Cobre**: US-002, FR-004, NFR-002

```gherkin
@US-002 @FR-004 @NFR-002 @AC-007
Feature: Verificação não escondida

  Scenario: Ruff e Pytest não têm nova tentativa
    Given o workflow depois da mudança
    When os passos de Ruff e Pytest são lidos
    Then nenhum deles usa laço de repetição nem continue-on-error
    And nenhuma action de terceiros de nova tentativa é usada
```

#### AC-008 — O teto cobre o pior caso do passo

**Cobre**: US-002, FR-003, NFR-001

```gherkin
@US-002 @FR-003 @NFR-001 @AC-008
Feature: Teto coerente com o passo

  Scenario: O teto do job comporta o pior caso do apt
    Given o limite padrão e o número de tentativas do script
    When o pior caso do passo é calculado
    Then o teto do job é maior que o pior caso mais 5 minutos de margem
```

#### AC-009 — Mensagem por tentativa

**Cobre**: US-001, FR-002

```gherkin
@US-001 @FR-002 @AC-009
Feature: Log legível

  Scenario: Cada tentativa anuncia seu número
    Given um apt falso que falha duas vezes e depois funciona
    When o script roda
    Then o registro mostra "Tentativa 1 de 3", "Tentativa 2 de 3" e "Tentativa 3 de 3"
```

#### AC-010 — Job do frontend inalterado

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-010
Feature: Escopo do teto

  Scenario: Só o job Ruff and Pytest recebe o teto
    Given o workflow depois da mudança
    When o job do frontend é lido
    Then ele não declara timeout-minutes
    And mantém o nome "Frontend (lint, types, tests, build)"
```

#### AC-011 — Sem segredo no workflow

**Cobre**: US-002, FR-004, NFR-002

```gherkin
@US-002 @FR-004 @NFR-002 @AC-011
Feature: Workflow sem segredo

  Scenario: O workflow e o script não referenciam segredo
    Given o workflow e o script de instalação
    When o texto deles é lido
    Then nenhum deles referencia secrets
```

#### AC-012 — Actions fixadas por SHA

**Cobre**: US-002, FR-004, NFR-002

```gherkin
@US-002 @FR-004 @NFR-002 @AC-012
Feature: Cadeia de suprimentos

  Scenario: Cada action usada continua fixada por SHA
    Given o workflow depois da mudança
    When os passos com uses são lidos
    Then cada action usa um SHA de 40 caracteres
```

#### AC-013 — O CI não pede o LibreOffice ao apt

**Cobre**: US-001, FR-005

```gherkin
@US-001 @FR-005 @AC-013
Feature: Pacotes do CI sem LibreOffice

  Scenario: O script instala sem LibreOffice
    Given um apt falso que registra os argumentos do install
    When o script roda
    Then nenhum pacote cujo nome começa com libreoffice é pedido ao apt
```

#### AC-014 — O CI instala exatamente o Tesseract

**Cobre**: US-001, FR-005

```gherkin
@US-001 @FR-005 @AC-014
Feature: Pacotes do CI restritos ao que a suíte usa

  Scenario: A lista de pacotes é a do Tesseract
    Given um apt falso que registra os argumentos do install
    When o script roda
    Then os pacotes pedidos são exatamente tesseract-ocr e tesseract-ocr-por
```

#### AC-015 — A imagem de produção mantém o LibreOffice

**Cobre**: US-001, FR-005

```gherkin
@US-001 @FR-005 @AC-015
Feature: Produção preservada

  Scenario: O Dockerfile do backend continua com o LibreOffice
    Given o arquivo deploy/backend/Dockerfile
    When a instalação de pacotes do sistema é lida
    Then ela inclui libreoffice-core, tesseract-ocr e tesseract-ocr-por
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O passo de instalação dos pacotes do sistema deve executar `apt-get update` e `apt-get install` dentro de um limite de 300 segundos por tentativa, com até 3 tentativas, em `.github/scripts/instalar_pacotes_apt.sh`.
- **FR-002**: Quando as 3 tentativas falharem, o script deve terminar com código diferente de zero e uma mensagem final legível; quando uma tentativa passar, deve terminar com zero sem chamar o apt de novo; cada tentativa anuncia seu número.
- **FR-003**: O job "Ruff and Pytest" deve declarar `timeout-minutes: 25`; o job do frontend não recebe teto nesta entrega.
- **FR-005**: O script de instalação do CI deve pedir ao apt somente `tesseract-ocr` e `tesseract-ocr-por`, sem nenhum pacote do LibreOffice; a imagem de produção em `deploy/backend/Dockerfile` continua instalando o LibreOffice e o Tesseract.
- **FR-004**: O workflow deve manter os gatilhos de push e de pull request, os comandos `uv run ruff check` e `uv run pytest` sem nova tentativa, sem segredo e com cada action fixada por SHA.

#### Não funcionais

- **NFR-001**: O pior caso do passo do apt é de 15 minutos (3 x 300 segundos) e o teto do job é maior que esse valor mais 5 minutos de margem. **Verificação**: teste que calcula o pior caso a partir dos padrões do script e compara com o `timeout-minutes` do job.
- **NFR-002**: Nenhuma action nova de terceiros é adicionada e as existentes continuam fixadas por SHA; o workflow e o script não usam segredo. **Verificação**: testes estáticos sobre o workflow e o script.

#### Erros e casos-limite

- Uma tentativa passa do limite → é cancelada, o script limpa o estado do dpkg e tenta de novo.
- As 3 tentativas falham → o passo e o job falham, o merge fica bloqueado e a reexecução manual continua possível.
- O job passa de 25 minutos por outro passo → o GitHub o cancela.
- Um teste novo passa a precisar do LibreOffice real → ele falha no CI por falta do `soffice`; a correção é simular o `soffice` no teste ou reabrir FR-005.
- O apt falha por pacote inexistente → falha nas 3 tentativas com a mensagem final; o custo é de, no máximo, 3 tentativas curtas.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- O CI é `.github/workflows/ci.yml`, com os jobs `quality` ("Ruff and Pytest") e `frontend`, ambos em `ubuntu-latest`; roda em `push` e `pull_request`, com `concurrency` que cancela execuções antigas do mesmo ref.
- O passo "Install system packages for document conversion" faz `sudo apt-get update` e `sudo apt-get install -y --no-install-recommends` de `tesseract-ocr`, `tesseract-ocr-por`, `libreoffice-core`, `libreoffice-writer`, `libreoffice-calc` e `libreoffice-impress`.
- `tests/test_ci_gates.py` lê o workflow com PyYAML e confere gatilhos, comandos, ausência de segredo e o serviço de Postgres; a SPEC-0007 é a fonte desses testes.
- A `main` exige os checks "Ruff and Pytest" e "Frontend (lint, types, tests, build)".

#### Arquitetura e módulos

- `.github/scripts/instalar_pacotes_apt.sh` (novo): laço de até 3 tentativas; cada uma roda `sudo timeout --kill-after=10 300 bash -c '<apt-get update e install>'`; entre tentativas roda `sudo dpkg --configure -a`; usa `-o Acquire::Retries=3`. Os padrões vêm de `APT_LIMITE_SEGUNDOS` (300) e `APT_TENTATIVAS` (3), que os testes sobrescrevem.
- `.github/workflows/ci.yml` (alterado): o passo passa a chamar `bash .github/scripts/instalar_pacotes_apt.sh`, com `timeout-minutes: 17` como limite de segurança do passo, e o job `quality` ganha `timeout-minutes: 25`.
- Lista `PACOTES` do script (alterada por FR-005): só `tesseract-ocr tesseract-ocr-por`; o LibreOffice sai do CI e fica só em `deploy/backend/Dockerfile`.
- `tests/test_ci_apt_resiliencia.py` (novo): casos estáticos sobre o workflow e o script e casos de execução do script com `sudo` e `apt-get` falsos num diretório temporário.

#### Migrations

- Não aplicável.

#### Models

- Não aplicável.

#### Controllers e casos de uso

- Não aplicável.

#### Views e experiência

- Não aplicável: não há interface para pessoas.

#### Queries e repositórios

- Não aplicável.

#### Jobs e processamento assíncrono

- Não aplicável à aplicação. No CI, a nova tentativa é do passo do apt e não se estende a Ruff, Pytest nem ao job do frontend.

#### Estrutura de arquivos

```text
specs/0044-ci-limite-de-tempo-e-nova-tentativa-no-apt/
  spec.md
  research/
.github/
  scripts/instalar_pacotes_apt.sh
  workflows/ci.yml
tests/test_ci_apt_resiliencia.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Não aplicável | Não aplicável | Nenhum dado persistido é criado ou alterado | Nenhuma |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Passo do apt | Tentativa N em curso | Passa dentro do limite | Concluído com sucesso | O apt não é chamado de novo |
| Passo do apt | Tentativa N em curso | Falha ou passa do limite e N < 3 | Tentativa N+1 | O dpkg é reconfigurado antes |
| Passo do apt | Tentativa 3 em curso | Falha ou passa do limite | Falhou | Código de saída diferente de zero e mensagem final |

#### Migração e retenção

- Não aplicável.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega muda um workflow de CI e um script de shell; a pessoa vê o resultado nos checks do GitHub, que não são uma tela do sistema.

#### Stack e convenções de interface

- Não aplicável.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável.

#### Menus e navegação principal

- Não aplicável: não há menu nem tela nova.

#### Formulários e ações

- Não aplicável.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável: nenhuma tela é criada ou alterada, então nenhum bloco React, componente shadcn/ui ou ReUI é usado.

#### Estados e acessibilidade

- Não aplicável. A mensagem do script no registro do job é texto simples e legível, com o número de cada tentativa.

#### Contrato CRUD

- Não aplicável.

#### Revisão visual durante o desenvolvimento

- Não aplicável: a entrega não tem superfície visual. Cada tarefa registra `Não aplicável` com esse motivo concreto.

#### APIs expostas

- Nenhuma.

#### APIs externas utilizadas

- GitHub Actions e os espelhos de pacotes do Ubuntu, usados pelo `apt-get`. Limite de 300 segundos por tentativa e até 3 tentativas; sem fallback além da falha do passo.

#### Documentação das APIs consultadas

- Nenhuma fonte externa copiada; decisões extraídas dos logs das execuções citadas na seção 2.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: leitura do workflow e do script com PyYAML e texto, para limites, teto, gatilhos e ausência de segredo.
- **Integração/contrato**: execução do script com `sudo`, `apt-get` e `dpkg` falsos em um diretório temporário, contando chamadas e conferindo o código de saída e as mensagens.
- **BDD/aceite**: os Gherkin da seção 6 orientam o desenho dos casos; cada AC tem pelo menos um caso.
- **Runner TDD**: Pytest, runner já usado pelo repositório (`tests/test_ci_gates.py`); marcador `SPECSFY: SPEC-0044 ...` em cada caso.
- **E2E**: a execução real do CI no PR que entregar a spec; não há como forçar o atraso do apt no GitHub.
- **Verificação manual**: acompanhar nos PRs seguintes se a reexecução manual deixou de ser necessária, pois o atraso do espelho é intermitente.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, NFR-001, AC-001 | AC-001 na seção 6 | caso de limite por tentativa em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe | GREEN 2026-10-23: caso passa com o script criado em T013 (5 passed) | Ruff limpo e `bash -n` sem erro; regressão completa em T016 |
| US-001, FR-001, NFR-001, AC-002 | AC-002 na seção 6 | caso de 3 tentativas em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe | GREEN 2026-10-23: caso passa com o script criado em T013 (5 passed) | Ruff limpo e `bash -n` sem erro; regressão completa em T016 |
| US-001, FR-002, AC-003 | AC-003 na seção 6 | caso de falha final em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe | GREEN 2026-10-23: caso passa com o script criado em T013 (5 passed) | Ruff limpo e `bash -n` sem erro; regressão completa em T016 |
| US-001, FR-001, FR-002, AC-004 | AC-004 na seção 6 | caso de sucesso na segunda tentativa em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe | GREEN 2026-10-23: caso passa com o script criado em T013 (5 passed) | Ruff limpo e `bash -n` sem erro; regressão completa em T016 |
| US-002, FR-003, NFR-001, AC-005 | AC-005 na seção 6 | caso do teto do job em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: `timeout-minutes` ausente no job `quality` (valor `None` em vez de `'25'`) | GREEN 2026-10-23: o job `quality` declara `timeout-minutes: 25` (T015) | 34 casos (12 da spec e 22 de `tests/test_ci_gates.py`) verdes |
| US-002, FR-004, AC-006 | AC-006 na seção 6 | caso de gatilhos e comandos em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: nenhum passo do workflow chama o script (`bash .github/scripts/instalar_pacotes_apt.sh` ausente) | GREEN 2026-10-23: caso passa com o passo do apt chamando o script (T014) | 22 casos de `tests/test_ci_gates.py` seguem verdes |
| US-002, FR-004, NFR-002, AC-007 | AC-007 na seção 6 | caso de Ruff e Pytest sem nova tentativa em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: nenhum passo do workflow chama o script (0 passos em vez de 1) | GREEN 2026-10-23: Ruff e Pytest sem nova tentativa e só o passo do apt chama o script (T014 e T015) | 34 casos (12 da spec e 22 de `tests/test_ci_gates.py`) verdes |
| US-002, FR-003, NFR-001, AC-008 | AC-008 na seção 6 | caso do teto contra o pior caso em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe | GREEN 2026-10-23: o teto de 25 minutos supera o pior caso de 15 mais 5 e o limite do passo (17) fica entre os dois (T015) | 34 casos (12 da spec e 22 de `tests/test_ci_gates.py`) verdes |
| US-001, FR-002, AC-009 | AC-009 na seção 6 | caso de mensagem por tentativa em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe | GREEN 2026-10-23: caso passa com o script criado em T013 (5 passed) | Ruff limpo e `bash -n` sem erro; regressão completa em T016 |
| US-002, FR-003, AC-010 | AC-010 na seção 6 | caso do job do frontend em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: `timeout-minutes` ausente no job `quality` | GREEN 2026-10-23: só o job `quality` tem teto e o frontend segue igual (T015) | 34 casos (12 da spec e 22 de `tests/test_ci_gates.py`) verdes |
| US-002, FR-004, NFR-002, AC-011 | AC-011 na seção 6 | caso de ausência de segredo em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe | GREEN 2026-10-23: workflow e script sem referência a segredo (T013 e T015) | 34 casos (12 da spec e 22 de `tests/test_ci_gates.py`) verdes |
| US-001, FR-005, AC-013 | AC-013 na seção 6 | caso sem LibreOffice no install em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: o script pede `libreoffice-core`, `libreoffice-writer`, `libreoffice-calc` e `libreoffice-impress` | Pending | Pending |
| US-001, FR-005, AC-014 | AC-014 na seção 6 | caso da lista exata do Tesseract em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | RED 2026-10-23: 6 pacotes pedidos em vez de `tesseract-ocr` e `tesseract-ocr-por` | Pending | Pending |
| US-001, FR-005, AC-015 | AC-015 na seção 6 | caso do Dockerfile de produção em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | Caracterização: passou antes da mudança (comportamento a preservar) | Pending | Pending |
| US-002, FR-004, NFR-002, AC-012 | AC-012 na seção 6 | caso de actions fixadas por SHA em tests/test_ci_apt_resiliencia.py com marcador próprio `SPECSFY:` | Caracterização: passou antes da mudança (comportamento a preservar) | GREEN 2026-10-23: actions seguem fixadas por SHA (caracterização, preservada) | 34 casos (12 da spec e 22 de `tests/test_ci_gates.py`) verdes |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | tests/test_ci_apt_resiliencia.py | Pending |
| FR-001 | AC-002 | Integração | tests/test_ci_apt_resiliencia.py | Pending |
| FR-001 | AC-004 | Integração | tests/test_ci_apt_resiliencia.py | Pending |
| FR-002 | AC-003 | Integração | tests/test_ci_apt_resiliencia.py | Pending |
| FR-002 | AC-004 | Integração | tests/test_ci_apt_resiliencia.py | Pending |
| FR-002 | AC-009 | Integração | tests/test_ci_apt_resiliencia.py | Pending |
| FR-003 | AC-005 | Unidade | tests/test_ci_apt_resiliencia.py | Pending |
| FR-003 | AC-008 | Unidade | tests/test_ci_apt_resiliencia.py | Pending |
| FR-003 | AC-010 | Unidade | tests/test_ci_apt_resiliencia.py | Pending |
| FR-004 | AC-006 | Unidade | tests/test_ci_apt_resiliencia.py | Pending |
| FR-004 | AC-007 | Unidade | tests/test_ci_apt_resiliencia.py | Pending |
| FR-004 | AC-011 | Unidade | tests/test_ci_apt_resiliencia.py | Pending |
| FR-004 | AC-012 | Unidade | tests/test_ci_apt_resiliencia.py | Pending |
| FR-005 | AC-013 | Integração | tests/test_ci_apt_resiliencia.py | Pending |
| FR-005 | AC-014 | Integração | tests/test_ci_apt_resiliencia.py | Pending |
| FR-005 | AC-015 | Unidade | tests/test_ci_apt_resiliencia.py | Pending |
| NFR-001 | AC-001 | Integração | uv run pytest tests/test_ci_apt_resiliencia.py | Pending |
| NFR-001 | AC-002 | Integração | uv run pytest tests/test_ci_apt_resiliencia.py | Pending |
| NFR-001 | AC-005 | Unidade | uv run pytest tests/test_ci_apt_resiliencia.py | Pending |
| NFR-001 | AC-008 | Unidade | uv run pytest tests/test_ci_apt_resiliencia.py | Pending |
| NFR-002 | AC-007 | Unidade | uv run pytest tests/test_ci_apt_resiliencia.py | Pending |
| NFR-002 | AC-011 | Unidade | uv run pytest tests/test_ci_apt_resiliencia.py | Pending |
| NFR-002 | AC-012 | Unidade | uv run pytest tests/test_ci_apt_resiliencia.py | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY em 2026-10-23 (revalidação após FR-005/DEC-006). Validação anterior, de 2026-10-23, também READY; seus achados seguem abaixo como histórico.
- **Revalidação de 2026-10-23**: 0 BLOCKER, 2 WARNING, 1 NOTE. Cobertura mínima: a feature tem 15 AC; US-001: 8, US-002: 7, FR-001: 3, FR-002: 3, FR-003: 3, FR-004: 4, FR-005: 3, NFR-001: 4, NFR-002: 3.
  - **WARNING (FR-005, R-005)**: só o Tesseract soma cerca de 10 MB; no ritmo medido de 40 KB/s, uma tentativa pode não terminar em 300 s. O apt reaproveita o que já baixou entre tentativas (121, depois 109, depois 99 MB), então 2 tentativas bastam nesse ritmo. Ação: conferir a linha "Need to get" e o tempo do passo no CI do PR da entrega.
  - **WARNING (FR-005)**: um teste futuro que precise do LibreOffice real falha no CI. Ação: registrado em erros e casos-limite e em DEC-006; a correção é simular o `soffice` ou reabrir FR-005.
  - **NOTE (AC-013, AC-014)**: AC-014, a lista exata, implica AC-013, sem LibreOffice. Os dois ficam porque o AC-013 dá a mensagem de falha específica quando o LibreOffice volta à lista.
- Sem impacto em `.specsfy/STACK.md`, que já registra GitHub Actions e Pytest, nem em `.specsfy/DATABASE.md`, porque não há persistência. `PROJECT.md` não muda de finalidade nem de capacidade.
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0044-ci-limite-de-tempo-e-nova-tentativa-no-apt/spec.md`
- **Achados**: 0 BLOCKER, 2 WARNING, 1 NOTE. Cobertura mínima atendida: cada US, FR e NFR tem pelo menos 3 AC (US-001: 5, US-002: 7, FR-001: 3, FR-002: 3, FR-003: 3, FR-004: 4, NFR-001: 4, NFR-002: 3) e a feature tem 12 AC.
  - **WARNING (seção 14)**: as tarefas ainda são o modelo do template; `$specsfy-05-tasks` as substitui e preserva os IDs. Ação: planejar a seção 14.
  - **WARNING (seção 8, FR-001)**: o limite de segurança de 17 minutos do passo existe no plano mas não tem FR nem AC próprios. Ação: cobrir na tarefa do `ci.yml` e num caso de teste, sem criar requisito novo; o teto de 25 minutos do job e o limite de 300 segundos já têm AC.
  - **NOTE (AC-007)**: "nenhuma action de terceiros de nova tentativa" é verificável por uma lista de donos permitidos em `uses` (hoje `actions` e `astral-sh`); o teste deve usar essa lista.
- Findings especializados: nenhum aplicável; sem superfície de produto, dado ou segurança além da cadeia de suprimentos já coberta por NFR-002.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed em 2026-10-23 (replanejamento por FR-005). 21 tarefas, 24 de 24 IDs cobertos; RED válido em AC-013 e AC-014 e caracterização em AC-015. Resultado anterior: Passed em 2026-10-23.
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0044-ci-limite-de-tempo-e-nova-tentativa-no-apt/spec.md`
- **Achados**: 16 tarefas (12 `[TEST] [TDD]`, 3 `[CODE]` e 1 `[TEST]` de regressão); 20 de 20 IDs cobertos. RED válido observado em 11 casos, cada um por comportamento ausente (o script `.github/scripts/instalar_pacotes_apt.sh` não existe, o job `quality` não declara `timeout-minutes` e nenhum passo chama o script). O caso de AC-012 é de caracterização e passa antes da mudança, registrado como trava contra regressão. Ruff limpo no arquivo de teste. O banco de testes foi confirmado como separado por `check_database_safety.mjs` (SAFE); os casos não usam banco.

#### Gate do Ato III — Entrega

- **Resultado**: Pending — reaberto em 2026-10-23 por FR-005 (DEC-006). Resultado anterior: Passed
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0044-ci-limite-de-tempo-e-nova-tentativa-no-apt/spec.md .`
- **Achados**: 16 de 16 tarefas concluídas; 20 de 20 IDs cobertos (`--full-chain`: OK); 857 testes passam (1 ignorado) e o Ruff está limpo; `docs/` conferido com `--check`. O PR #82 passou no CI sem reexecução manual: na execução de pull request o apt ficou lento, as tentativas 1 e 2 foram cortadas em 300 s e a 3ª instalou os pacotes (20:25:55 a 20:40:46 UTC), e o job terminou com sucesso dentro do teto de 25 minutos. Merge feito na `main` (commit f08f712).

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: uma tentativa lenta é cancelada pelo limite configurado — Refs: US-001, FR-001, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_tentativa_lenta_e_cancelada_pelo_limite` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: o apt que sempre falha é chamado em exatamente 3 tentativas — Refs: US-001, FR-001, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_apt_que_sempre_falha_roda_tres_tentativas` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: as 3 falhas terminam com código diferente de zero e mensagem final — Refs: US-001, FR-002, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_tres_falhas_terminam_com_erro_e_mensagem` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: sucesso na segunda tentativa termina com zero sem terceira chamada — Refs: US-001, FR-001, FR-002, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_sucesso_na_segunda_tentativa_para_o_laco` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-005 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: o job Ruff and Pytest declara timeout-minutes 25 — Refs: US-002, FR-003, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_job_quality_declara_teto_de_25_minutos` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: `timeout-minutes` ausente no job `quality` (valor `None` em vez de `'25'`).
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: gatilhos e comandos preservados e o passo do apt chama o script — Refs: US-002, FR-004, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_gatilhos_e_comandos_preservados_e_apt_chama_o_script` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: nenhum passo do workflow chama o script (`bash .github/scripts/instalar_pacotes_apt.sh` ausente).
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: Ruff e Pytest sem nova tentativa e só o passo do apt usa o script — Refs: US-002, FR-004, NFR-002, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_ruff_e_pytest_sem_nova_tentativa` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: nenhum passo do workflow chama o script (0 passos em vez de 1).
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: o teto do job supera o pior caso do passo mais 5 minutos — Refs: US-002, FR-003, NFR-001, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_teto_do_job_comporta_o_pior_caso_do_apt` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T009 [TEST] [TDD] [US-001] Derivar do AC-009 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: cada tentativa anuncia seu número no registro — Refs: US-001, FR-002, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_cada_tentativa_anuncia_seu_numero` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T010 [TEST] [TDD] [US-002] Derivar do AC-010 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: só o job Ruff and Pytest recebe teto e o frontend fica igual — Refs: US-002, FR-003, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_so_o_job_quality_recebe_teto` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: `timeout-minutes` ausente no job `quality`.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T011 [TEST] [TDD] [US-002] Derivar do AC-011 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: o workflow e o script não referenciam secrets — Refs: US-002, FR-004, NFR-002, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_workflow_e_script_sem_segredo` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. RED observado em 2026-10-23: `.github/scripts/instalar_pacotes_apt.sh` ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

- [x] T012 [TEST] [TDD] [US-002] Derivar do AC-012 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: cada action usada continua fixada por SHA de 40 caracteres — Refs: US-002, FR-004, NFR-002, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012 na spec e confirmar regra, IDs e nível de teste; rodar `check_database_safety.mjs` antes de qualquer teste. Banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Escrever o caso `test_actions_continuam_fixadas_por_sha` em `tests/test_ci_apt_resiliencia.py` com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`. Caso criado em `tests/test_ci_apt_resiliencia.py`.
  - [x] **VERIFY**: Observar RED válido, por comportamento ausente e não por erro de sintaxe ou de import. Caso de caracterização: passou antes da mudança em 2026-10-23, por preservar um comportamento já existente; fica como trava contra regressão.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar o comando `uv run pytest tests/test_ci_apt_resiliencia.py` e a causa do RED. Execução focal em 2026-10-23: 11 casos falharam e 1 passou (AC-012, caracterização); a causa do RED é comportamento ausente, não erro de sintaxe, fixture ou ambiente.
  - [x] **IMPROVE**: Revisar a cobertura do caso e registrar aprendizado ou ausência justificada. Nenhuma melhoria adicional: o caso é o menor que prova o AC.

#### Fase 2 — US-001 Instalar os pacotes do sistema com limite de tempo e nova tentativa (P1)

**Objetivo**: o passo do apt é cancelado após 300 segundos e tentado de novo, até 3 vezes, e falha com mensagem legível.
**Teste independente**: `uv run pytest tests/test_ci_apt_resiliencia.py -k "tentativa or apt or falhas"` com resultado verde.

- [x] T013 [CODE] [US-001] Criar o script de instalação com limite e nova tentativa em .github/scripts/instalar_pacotes_apt.sh — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-009 — Depends: T001, T002, T003, T004, T009
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências; rodar `check_database_safety.mjs` antes de qualquer teste. RED dos predecessores T001, T002, T003, T004 e T009 confirmado na seção 11; banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar arquivos; depois implementar a menor mudança. O script lê `APT_LIMITE_SEGUNDOS` (padrão 300) e `APT_TENTATIVAS` (padrão 3), roda `sudo timeout --kill-after=10` sobre `apt-get update` e `apt-get install` com `-o Acquire::Retries=3`, anuncia "Tentativa N de 3", roda `sudo dpkg --configure -a` entre as tentativas e termina com erro e mensagem final após a última. `docs/` reconstruído com `$specsfy-documentator` antes (`--check` exit 0); criado `.github/scripts/instalar_pacotes_apt.sh` com laço de até 3 tentativas, `sudo timeout --kill-after=10` de 300 segundos por tentativa, `dpkg --configure -a` entre elas e mensagem final de erro; os padrões vêm de `APT_LIMITE_SEGUNDOS` e `APT_TENTATIVAS`. Monitor de contexto: CURRENT; `PROJECT.md` sem impacto material (a entrega é um script de CI, sem mudar capacidades do produto).
  - [x] **VERIFY**: Executar `tests/test_ci_apt_resiliencia.py` nos casos de AC-001, AC-002, AC-003, AC-004 e AC-009; cada um GREEN, e `uv run ruff check` limpo. Os 5 casos de AC-001, AC-002, AC-003, AC-004 e AC-009 passam (5 passed); `uv run ruff check .` limpo e `bash -n` sem erro. Os 5 casos restantes do arquivo são de T014 e T015 e continuam em RED.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar GREEN, comando, contagens e arquivos alterados. GREEN registrado na seção 11; arquivo alterado: `.github/scripts/instalar_pacotes_apt.sh` (e `tests/test_ci_apt_resiliencia.py`, só no apt falso lento: `exec sleep` para que o processo não segure o canal de saída depois do cancelamento).
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. O apt falso lento passou a usar `exec`, o que torna o teste do limite determinístico (cerca de 1 segundo em vez de esperar o processo órfão).
  <!-- specsfy:evidence {"task": "T013", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-009"], "files": [".github/scripts/instalar_pacotes_apt.sh", "tests/test_ci_apt_resiliencia.py"], "commands": [{"run": "uv run pytest tests/test_ci_apt_resiliencia.py::test_tentativa_lenta_e_cancelada_pelo_limite tests/test_ci_apt_resiliencia.py::test_apt_que_sempre_falha_roda_tres_tentativas tests/test_ci_apt_resiliencia.py::test_tres_falhas_terminam_com_erro_e_mensagem tests/test_ci_apt_resiliencia.py::test_sucesso_na_segunda_tentativa_para_o_laco tests/test_ci_apt_resiliencia.py::test_cada_tentativa_anuncia_seu_numero", "exit": 0}]} -->

**Checkpoint**: o script, rodado com um apt falso, tenta no máximo 3 vezes, cancela a tentativa lenta e sai com o código certo.

- [x] T014 [CODE] [US-001] Trocar o passo do apt do ci.yml pela chamada ao script, com timeout-minutes 17, em .github/workflows/ci.yml — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-006 — Depends: T001, T002, T006, T013
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências; rodar `check_database_safety.mjs` antes de qualquer teste. RED dos predecessores T001, T002 e T006 confirmado na seção 11 e T013 concluída; banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar arquivos; depois implementar a menor mudança. O passo "Install system packages for document conversion" passa a rodar `bash .github/scripts/instalar_pacotes_apt.sh` e declara `timeout-minutes: 17` como limite de segurança, acima do pior caso de 15 minutos; o restante do passo e do workflow não muda. `docs/` reconstruído com `$specsfy-documentator` antes (`--check` exit 0); o passo "Install system packages for document conversion" de `.github/workflows/ci.yml` agora roda `bash .github/scripts/instalar_pacotes_apt.sh` com `timeout-minutes: 17`, e um comentário aponta a SPEC-0044. Monitor de contexto: CURRENT; `PROJECT.md` sem impacto material.
  - [x] **VERIFY**: Executar `tests/test_ci_apt_resiliencia.py` e `tests/test_ci_gates.py`; AC-006 GREEN e sem regressão nos casos existentes do workflow. 26 passed: os 4 casos de AC-001, AC-002, AC-006 e AC-007 (esta, parcial) mais os 22 de `tests/test_ci_gates.py`, sem regressão nos casos existentes do workflow.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar GREEN, comando, contagens e arquivos alterados. GREEN de AC-006 registrado na seção 11; arquivo alterado: `.github/workflows/ci.yml`.
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. Nenhuma melhoria adicional: a mudança é só a troca do corpo do passo, e o comentário explica por que o limite do passo (17) fica acima do pior caso (15).
  <!-- specsfy:evidence {"task": "T014", "refs": ["US-001", "FR-001", "NFR-001", "AC-001", "AC-002", "AC-006"], "files": [".github/workflows/ci.yml"], "commands": [{"run": "uv run pytest tests/test_ci_apt_resiliencia.py::test_gatilhos_e_comandos_preservados_e_apt_chama_o_script tests/test_ci_apt_resiliencia.py::test_ruff_e_pytest_sem_nova_tentativa tests/test_ci_apt_resiliencia.py::test_tentativa_lenta_e_cancelada_pelo_limite tests/test_ci_apt_resiliencia.py::test_apt_que_sempre_falha_roda_tres_tentativas tests/test_ci_gates.py", "exit": 0}]} -->

#### Fase 3 — US-002 Limitar o job e preservar o resto da esteira (P2)

**Objetivo**: o job "Ruff and Pytest" tem teto de 25 minutos e gatilhos, comandos, actions e o job do frontend ficam como estão.
**Teste independente**: `uv run pytest tests/test_ci_apt_resiliencia.py tests/test_ci_gates.py` com resultado verde.

- [x] T015 [CODE] [US-002] Declarar timeout-minutes 25 no job quality e conferir que o restante do workflow não muda em .github/workflows/ci.yml — Refs: US-002, FR-003, FR-004, NFR-001, NFR-002, AC-005, AC-006, AC-007, AC-008, AC-010, AC-011, AC-012 — Depends: T005, T006, T007, T008, T010, T011, T012, T014
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências; rodar `check_database_safety.mjs` antes de qualquer teste. RED dos predecessores T005, T006, T007, T008, T010, T011 e T012 confirmado na seção 11 (T012 é de caracterização) e T014 concluída; banco de testes separado confirmado por `check_database_safety.mjs`: SAFE.
  - [x] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar arquivos; depois implementar a menor mudança. O job `quality` ganha `timeout-minutes: 25`; o job `frontend`, os gatilhos, os comandos de Ruff e Pytest, as actions fixadas por SHA e a ausência de segredo ficam intactos. `docs/` reconstruído com `$specsfy-documentator` antes (`--check` exit 0); o job `quality` de `.github/workflows/ci.yml` ganhou `timeout-minutes: 25`, com comentário apontando a SPEC-0044; o job `frontend`, os gatilhos, os comandos de Ruff e Pytest, as actions fixadas por SHA e a ausência de segredo ficaram intactos. Monitor de contexto: CURRENT; `PROJECT.md` sem impacto material.
  - [x] **VERIFY**: Executar `tests/test_ci_apt_resiliencia.py` e `tests/test_ci_gates.py`; AC-005, AC-006, AC-007, AC-008, AC-010, AC-011 e AC-012 GREEN. 34 passed (`uv run pytest tests/test_ci_apt_resiliencia.py tests/test_ci_gates.py`): os 12 casos da spec, incluindo AC-005, AC-007, AC-008, AC-010, AC-011 e AC-012, e os 22 de `tests/test_ci_gates.py`.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar GREEN, comando, contagens e arquivos alterados. GREEN de AC-005, AC-007, AC-008, AC-010, AC-011 e AC-012 registrado na seção 11; arquivo alterado: `.github/workflows/ci.yml`.
  - [x] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma. Nenhuma melhoria adicional: a mudança é uma linha com comentário, e os testes já travam o teto contra o pior caso do passo.
  <!-- specsfy:evidence {"task": "T015", "refs": ["US-002", "FR-003", "FR-004", "NFR-001", "NFR-002", "AC-005", "AC-006", "AC-007", "AC-008", "AC-010", "AC-011", "AC-012"], "files": [".github/workflows/ci.yml"], "commands": [{"run": "uv run pytest tests/test_ci_apt_resiliencia.py tests/test_ci_gates.py", "exit": 0}]} -->

**Checkpoint**: o workflow tem os dois limites novos e os testes de preservação continuam verdes.

#### Fase final — Qualidade

- [x] T016 [TEST] Executar regressão, rastreabilidade e a conferência de documentos em tests/test_ci_apt_resiliencia.py — Refs: US-001, US-002, FR-001, FR-002, FR-003, FR-004, NFR-001, NFR-002, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012 — Depends: T013, T014, T015
  - [x] **PREP**: Identificar suites, checks e gates; rodar `check_database_safety.mjs` antes da regressão. `check_database_safety.mjs`: SAFE. A suíte rodou contra o Postgres de teste da VPS (`rag-pipeline-test-postgres`, banco `rag_pipeline_test`, via `TESTING_ENV_FILE`), não contra o banco de desenvolvimento.
  - [x] **EXECUTE**: Executar a suíte completa, Ruff e a rastreabilidade; reconstruir `docs/` com `$specsfy-documentator` e conferir `--check`; revisar `PROJECT.md` e registrar a justificativa de que não há impacto material, e confirmar que `.specsfy/STACK.md` e `.specsfy/DATABASE.md` não mudam. Suíte completa, Ruff e rastreabilidade executados; `$specsfy-documentator` rodou e `--check` saiu com 0, sem mudança em `docs/`. `PROJECT.md` sem impacto material: a entrega só ajusta o CI (script de apt, limite de tempo) e não muda finalidade, capacidades nem limites do produto. `.specsfy/STACK.md` e `.specsfy/DATABASE.md` inalterados: GitHub Actions e Pytest já constam e não há persistência nova; monitor de contexto: CURRENT.
  - [x] **VERIFY**: Confirmar ausência de gaps de rastreabilidade (`--full-chain`) e a suíte verde. `check_traceability.mjs --full-chain`: 20/20 IDs cobertos, RESULTADO OK. `uv run pytest`: 857 passed, 1 skipped em 24min18s. Ruff: All checks passed. Os 12 casos de `tests/test_ci_apt_resiliencia.py` passam.
  - [x] **VISUAL**: Não aplicável: a entrega não tem superfície visual (workflow e script de CI).
  - [x] **EVIDENCE**: Registrar contagens e comandos finais; registrar se o CI do PR da entrega passou sem reexecução manual por lentidão do apt. Comandos e contagens acima. O CI do PR da entrega ainda não rodou: o item do Definition of Done sobre o CI do PR fica pendente até o merge. Duas rodadas anteriores da suíte contra o Supabase falharam por timeout de autenticação do pooler (ERROR transitório e 10 erros seguidos), sem relação com a spec; passaram ao usar o Postgres de teste local.
  - [x] **IMPROVE**: Registrar retrospectiva do processo. Suíte de testes dependente do Supabase publicado fica instável por timeout do pooler e leva mais de 6 minutos para falhar; o Postgres de teste da VPS resolve. Sugestão para a pessoa decidir: tornar `TESTING_ENV_FILE` apontando para ele o padrão local.
  <!-- specsfy:evidence {"task": "T016", "refs": ["US-001", "US-002", "FR-001", "FR-002", "FR-003", "FR-004", "NFR-001", "NFR-002"], "files": [], "commands": [{"run": "uv run pytest", "exit": 0}, {"run": "ruff check .", "exit": 0}, {"run": "check_traceability.mjs --full-chain", "exit": 0}]} -->

#### Fase 4 — FR-005 Pacotes do CI restritos ao Tesseract (P1, reabertura de 2026-10-23)

- [x] T017 [TEST] [TDD] [US-001] Derivar do AC-013 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: nenhum pacote libreoffice é pedido ao apt — Refs: US-001, FR-005, AC-013 — Depends: none
  - [x] **PREP**: Ler o AC-013 e o apt falso existente; rodar `check_database_safety.mjs` antes do teste.
  - [x] **EXECUTE**: Criar um apt falso que grava os argumentos do `install` e um caso com marcador `SPECSFY: SPEC-0044 US-001 FR-005 AC-013`.
  - [x] **VERIFY**: Observar RED porque o script ainda pede `libreoffice-core`.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (script de CI e testes).
  - [x] **EVIDENCE**: Registrar o comando e a falha observada na seção 11. Apt falso `APT_REGISTRA_INSTALL` e caso `test_ci_nao_pede_libreoffice_ao_apt`; RED: 4 pacotes do LibreOffice pedidos. Comando: `uv run pytest tests/test_ci_apt_resiliencia.py -k "libreoffice or tesseract"` → 2 failed, 1 passed.
  - [x] **IMPROVE**: Registrar melhoria aplicada ou justificar nenhuma. O apt falso de T017 serve a T018 por meio de `_pacotes_pedidos`, sem duplicar código.

- [x] T018 [TEST] [TDD] [US-001] Derivar do AC-014 um caso Pytest falhando em tests/test_ci_apt_resiliencia.py: os pacotes pedidos são exatamente tesseract-ocr e tesseract-ocr-por — Refs: US-001, FR-005, AC-014 — Depends: T017
  - [x] **PREP**: Reutilizar o apt falso que grava os argumentos (T017).
  - [x] **EXECUTE**: Criar o caso com marcador `SPECSFY: SPEC-0044 US-001 FR-005 AC-014` comparando o conjunto de pacotes pedidos.
  - [x] **VERIFY**: Observar RED porque a lista ainda tem 6 pacotes.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (script de CI e testes).
  - [x] **EVIDENCE**: Registrar o comando e a falha observada na seção 11. Caso `test_ci_instala_exatamente_o_tesseract`; RED: a lista tem 6 pacotes. Comando: `uv run pytest tests/test_ci_apt_resiliencia.py -k "libreoffice or tesseract"` → 2 failed, 1 passed.
  - [x] **IMPROVE**: Registrar melhoria aplicada ou justificar nenhuma. Nenhuma: o caso reaproveita o apoio de T017.

- [x] T019 [TEST] [TDD] [US-001] Derivar do AC-015 um caso Pytest de caracterização em tests/test_ci_apt_resiliencia.py: deploy/backend/Dockerfile mantém libreoffice-core e o Tesseract — Refs: US-001, FR-005, AC-015 — Depends: none
  - [x] **PREP**: Ler `deploy/backend/Dockerfile`.
  - [x] **EXECUTE**: Criar o caso com marcador `SPECSFY: SPEC-0044 US-001 FR-005 AC-015`.
  - [x] **VERIFY**: Confirmar que passa antes da mudança (comportamento a preservar).
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (script de CI e testes).
  - [x] **EVIDENCE**: Registrar como caracterização na seção 11. Caso `test_imagem_de_producao_mantem_libreoffice_e_tesseract`; passa antes da mudança (caracterização).
  - [x] **IMPROVE**: Registrar melhoria aplicada ou justificar nenhuma. Nenhuma: leitura estática simples.

- [ ] T020 [CODE] [US-001] Restringir a lista PACOTES a tesseract-ocr e tesseract-ocr-por em .github/scripts/instalar_pacotes_apt.sh — Refs: US-001, FR-005, AC-013, AC-014, AC-015 — Depends: T017, T018, T019
  - [ ] **PREP**: Confirmar o RED de T017 e T018 e a caracterização de T019.
  - [ ] **EXECUTE**: Reconstruir `docs/` com `$specsfy-documentator` antes de alterar; depois trocar só a lista `PACOTES` e o comentário do script.
  - [ ] **VERIFY**: Executar `tests/test_ci_apt_resiliencia.py` e `tests/test_ci_gates.py`; AC-013, AC-014 e AC-015 em GREEN.
  - [ ] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (script de CI e testes).
  - [ ] **EVIDENCE**: Registrar GREEN, comando, contagens e arquivos alterados.
  - [ ] **IMPROVE**: Registrar melhoria aplicada ou justificar nenhuma.

- [ ] T021 [TEST] Executar a regressão, a rastreabilidade e a conferência do CI real do PR em tests/test_ci_apt_resiliencia.py — Refs: US-001, FR-005, AC-013, AC-014, AC-015 — Depends: T020
  - [ ] **PREP**: Rodar `check_database_safety.mjs`; usar o Postgres de teste da VPS via `TESTING_ENV_FILE`.
  - [ ] **EXECUTE**: Executar a suíte completa, o Ruff, `check_traceability.mjs --full-chain` e `build_documentation.mjs --check`; revisar `PROJECT.md`.
  - [ ] **VERIFY**: Suíte verde e 0 gaps; no CI do PR, conferir a linha "Need to get" e o tempo do passo do apt.
  - [ ] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (script de CI e testes).
  - [ ] **EVIDENCE**: Registrar contagens, comandos e o resultado do CI do PR.
  - [ ] **IMPROVE**: Registrar a retrospectiva da reabertura.

### 15. Ordem de execução

- Caminho crítico: T001–T012 → T013 → T014 → T015 → T016; reabertura: T017 → T018 → T020 → T021, com T019 em paralelo lógico.
- Tarefas paralelas: nenhuma marcada `[P]`; T001–T012 escrevem o mesmo arquivo de teste e T014 e T015 alteram o mesmo `ci.yml`, então seguem em ordem.
- Estratégia de MVP: T001–T004, T009 e T013 entregam o script com limite e nova tentativa; T014 o liga ao CI; T015 acrescenta o teto do job.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0007 (esteira de CI), entregue; esta spec a referencia e não a reabre.
- A regra de `.specsfy/RULES.md` sobre o workflow de integração contínua.

#### Riscos

- A correção passa pelo próprio CI e pode travar no apt enquanto é entregue → usar o contorno manual já conhecido (cancelar e reexecutar a execução).
- O limite de 5 minutos pode cancelar uma instalação lenta que terminaria → aceito pela pessoa; a nova tentativa costuma recuperar.
- Matar o apt no meio pode deixar o dpkg interrompido e travar a tentativa seguinte → o script roda `dpkg --configure -a` entre as tentativas e o teste cobre a ordem.
- Nova tentativa pode esconder uma falha real e persistente → após 3 falhas o job falha com mensagem legível, e a nova tentativa não vale para Ruff nem Pytest.
- A SPEC-0007 afirma que não há retry automático → esta spec registra em DEC-005 que a nova tentativa vale só para a instalação dos pacotes.

#### Suposições

- A lentidão vem do espelho de pacotes do Ubuntu no runner, e não do conteúdo do passo; a nova tentativa recupera a maioria dos casos.
- O runner `ubuntu-latest` tem `sudo` e `timeout` (coreutils), como hoje.
- O pior caso de 15 minutos mais cerca de 6 minutos do restante do job cabe nos 25 minutos do teto.

### 17. Decisões

- **DEC-001**: alcance da correção — limite de tempo e nova tentativa no passo do apt, mantendo os gatilhos de push e de pull request; razão: a regra confirmada de `.specsfy/RULES.md` exige rodar a cada push de branch de fase; alternativas descartadas: cache dos pacotes e restringir o push à `main`.
- **DEC-002**: limite do passo — 300 segundos por tentativa e até 3 tentativas; razão: a execução normal leva cerca de 1 minuto, e 5 minutos separam lentidão de travamento; trade-off: pior caso de 15 minutos.
- **DEC-003**: teto do job — 25 minutos para o job "Ruff and Pytest"; razão: rede de segurança contra travamento em outro passo, acima de 15 minutos do apt mais cerca de 6 do resto.
- **DEC-004**: nova tentativa em script de shell versionado em `.github/scripts/`, e não em action de terceiros; razão: testável por execução simulada e sem nova dependência na cadeia de suprimentos; trade-off: um arquivo a mais para manter.
- **DEC-006** (2026-10-23, IDs: FR-005, AC-013, AC-014, AC-015, US-001): o CI instala só `tesseract-ocr` e `tesseract-ocr-por`; razão: o limite com nova tentativa não vence um download de 121 MB a cerca de 40 KB/s (R-005), e nenhum teste usa o LibreOffice real; alternativas descartadas: cache dos `.deb` com `actions/cache` e troca do espelho, que não foi medida; trade-off: um teste futuro que precise do LibreOffice real falha no CI até simular o `soffice`. DEC-001 continua valendo para os gatilhos; a exclusão do cache segue fora do escopo.
- **DEC-005**: spec nova que referencia a SPEC-0007, sem reabri-la; razão: a SPEC-0007 está concluída; a frase sobre ausência de retry automático continua valendo para Ruff e Pytest, e a nova tentativa vale só para a instalação dos pacotes do sistema.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
- [ ] `.specsfy/STACK.md` revisado: GitHub Actions e Pytest já constam, sem mudança estrutural; `.specsfy/DATABASE.md` não é afetado, pois não há persistência; `PROJECT.md` sem impacto material, justificado na evidência.
- [ ] `docs/` reconstruído por `$specsfy-documentator` e `build_documentation.mjs --check` passa.
- [ ] O PR da entrega passa no CI e o merge é feito sem reexecução manual por lentidão do apt, ou a ocorrência é registrada.
