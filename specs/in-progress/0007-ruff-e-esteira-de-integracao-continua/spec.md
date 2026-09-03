# Especificação integrada: Instalar o Ruff e criar a esteira de integração contínua

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0007 |
| Slug | 0007-ruff-e-esteira-de-integracao-continua |
| Status | Implementing |
| Effort | 4 |
| Effort updated at | 2026-09-03 |
| Effort rationale | Recalibrado de 1 para 4 na promoção. O volume é pequeno e conhecido: uma dependência, um bloco de configuração, dezenove correções já localizadas e um arquivo de workflow. O que sustenta a nota não é o volume, e sim três pontos de risco. As correções tocam arquivos pré-existentes, incluindo uma guarda estática de neutralidade cujo texto não pode perder alcance ao ser quebrado em linhas. O bloqueio de merge é configuração fora do repositório, não versionada e não revisável em código. E uma configuração de linter mal formulada pode desativar silenciosamente a família de regras que hoje protege o repositório, como a própria descoberta demonstrou. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | In Progress |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-03 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O repositório declara `[tool.ruff]` no `pyproject.toml`, com `extend-exclude = [".agents"]`, mas o Ruff **não está entre as dependências**. Existe configuração sem ferramenta: `uv run ruff check` responde `error: Failed to spawn: ruff`.

`.github/workflows/` não existe. Nenhuma verificação roda sozinha. Hoje, se alguém publicar sem executar `uv run pytest`, nada sinaliza.

Isso contradiz uma regra confirmada do projeto. Em 2026-08-31, durante o setup, ficou registrado em `.specsfy/RULES.md`, seção Testes: manter um workflow de integração contínua que execute Ruff e a suíte Pytest a cada push de branch de fase, com a conclusão do marco exigindo esse workflow verde, sem depender de execução manual.

A consequência já é concreta. A SPEC-0006 foi concluída em 2026-09-03 com um item da Definition of Done **aberto**, porque `uv run ruff check` não executa. A pendência foi aceita explicitamente e sua responsabilidade atribuída a esta fatia.

A medição feita durante o refinamento mostra que o custo é pequeno e que o benefício é imediato. Executando o Ruff de forma efêmera com `uvx`, sem instalar nada no projeto, a configuração escolhida acusa dezenove achados. Dezesseis são `E501`, largura de linha, em código pré-existente. **Três são defeitos semânticos, e os três foram introduzidos pela SPEC-0006 horas antes**, em `quality.py:70`, `src/quality.py:292` e `src/quality.py:608`. O código anterior a essa entrega não tem nenhum achado semântico.

Ou seja: no primeiro dia em que o linter poderia ter rodado, ele teria pego três defeitos que entraram sem qualquer sinal.

#### Resultado desejado

O mantenedor executa `uv run ruff check` e a verificação roda. Toda publicação em branch de fase e cada pull request disparam Ruff e Pytest automaticamente, sem intervenção. Uma reprovação impede o merge, em vez de apenas informá-lo. O item da Definition of Done que a SPEC-0006 deixou aberto passa a poder ser fechado.

#### Métricas de sucesso

- `uv run ruff check` executa e devolve zero achado, comprovado por execução local reproduzível.
- Os três defeitos semânticos identificados em `quality.py` e `src/quality.py` deixam de existir.
- A configuração declarada preserva o conjunto padrão do Ruff, comprovado por caso que verifica a presença das regras `TRY004`, `PIE810` e `ISC004` no conjunto efetivo.
- Um push em branch de fase produz uma execução automática de Ruff e Pytest visível no commit.
- Um pull request com verificação reprovada não pode ser concluído.
- A esteira executa sem receber credencial, token ou variável de ambiente do projeto.
- `uv run pytest` permanece verde, com os 221 casos atuais.
- Nenhuma dependência de execução é acrescentada; o Ruff entra apenas no grupo de desenvolvimento.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: o diagnóstico registrado no backlog em 2026-08-31 ainda vale? → Não, em dois terços. A suíte passou de nove para 221 casos e os comandos destrutivos na documentação foram removidos pela SPEC-0001, com guarda de regressão em `tests/test_docs_safety.py`. Só a ausência do Ruff permanece.
- **R-002**: quantos achados o Ruff produz sobre o código atual? → Depende inteiramente da configuração. Padrão do Ruff 0.16.5: três. `select = E,F,I,UP,B,SIM` com largura 88: cento e vinte e quatro, sendo cento e vinte e dois `E501`. Mesmo conjunto com largura 100: dezoito. `extend-select = E501,I,UP,B,SIM` com largura 100: dezenove.
- **R-003**: `select` e `extend-select` são equivalentes? → Não, e a diferença é material. `select` **substitui** o conjunto padrão; `extend-select` **soma** a ele. O padrão do Ruff 0.16 cobre `E4`, `E7`, `E9` e `F`, mas não `E5`, onde vive o `E501`. Por isso `select = E,F,I,UP,B,SIM` e o padrão são conjuntos parcialmente disjuntos: o primeiro passa a ver largura de linha e deixa de ver `TRY004`, `PIE810` e `ISC004`; o segundo faz o inverso. Só `extend-select` cobre os dois.
- **R-004**: existe dívida de lint acumulada neste repositório? → Não. Dos dezenove achados da configuração escolhida, dezesseis são largura de linha em código pré-existente, dos quais onze em `tests/test_client_neutrality.py`, que mantém listas longas de identificadores. Os três achados semânticos foram introduzidos pela SPEC-0006.
- **R-005**: qual plataforma de integração contínua o repositório usa? → Nenhuma, hoje. O remoto é `github.com/marciohernandez/rag-ingestion-pipeline`, o que sustenta GitHub Actions como escolha, registrada como suposição em `S-001`.
- **R-006**: a suíte exige rede, credencial ou serviço externo? → Não. `docs/testing.md` registra que nenhuma suíte exige rede: destinos remotos e SDKs são substituídos por dublês observáveis. A esteira, portanto, não precisa de segredo.
- **R-007**: o bloqueio de merge é configuração do repositório ou do workflow? → Do repositório, no GitHub, fora do controle de versão. O workflow apenas publica um resultado; transformar esse resultado em barreira é ajuste administrativo separado, o que exige tratá-lo como passo próprio e verificável.

#### Fontes e contexto consultados

- `pyproject.toml`: declara `[tool.ruff]` sem o Ruff nas dependências; `requires-python = ">=3.12"`; grupo `dev` com Pytest.
- `.python-version`: declara `3.12`.
- `.specsfy/RULES.md`, seções Código e qualidade e Testes: regras confirmadas sobre Ruff, Pytest, branch por fase e workflow de integração contínua.
- `specs/completed/0006-gate-qualidade-chunks-metadados/spec.md`, seções 13 e 18: pendência externa aceita e sua atribuição a esta fatia.
- `docs/testing.md`: inventário das suítes, ausência de exigência de rede e registro da lacuna do Ruff.
- `tests/test_docs_safety.py` e `tests/test_client_neutrality.py`: guardas estáticas afetadas pelas correções de largura de linha.
- `specs/backlog/0007-gates-entrega-handoff.md`: item de origem, refinado em 2026-09-03.
- Saída de `uvx ruff check` em suas cinco configurações, produzida durante o refinamento.

#### Documentação consultada

- Ruff 0.16.5, comportamento observado localmente por execução efêmera com `uvx`. Tópicos relevantes: composição do conjunto padrão de regras, diferença entre `select` e `extend-select`, e o fato de `E501` pertencer a `E5`, fora do padrão.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo. Toda a evidência desta fatia foi produzida por execução local sobre o próprio repositório, e os números estão registrados nas seções 1 e 2 e no item de backlog de origem.

#### Dúvidas respondidas

- **Q**: este item continua sendo uma fatia só? → **A**: não. Foi desmembrado em 2026-09-03. Esta fatia cobre Ruff e integração contínua; o contrato de handoff para o projeto-mãe passou ao `BACKLOG-0011`.
- **Q**: como escolher o conjunto de regras sem saber o volume de violações? → **A**: medindo antes, com execução efêmera que não altera o projeto.
- **Q**: qual configuração vira o gate? → **A**: `extend-select = ["E501", "I", "UP", "B", "SIM"]` com `line-length = 100`, dezenove correções. A alternativa com `select` foi descartada por deixar de fora os três defeitos semânticos do código recém-entregue.
- **Q**: o que acontece quando a verificação reprova? → **A**: o merge fica bloqueado. Um resultado ignorável não cumpre a regra confirmada.

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Ruff como dependência do grupo de desenvolvimento, com versão fixada.
- Configuração `extend-select = ["E501", "I", "UP", "B", "SIM"]` e `line-length = 100` no `pyproject.toml`, preservando o `extend-exclude` existente.
- Correção dos dezenove achados: três defeitos semânticos e dezesseis linhas longas.
- Workflow do GitHub Actions executando `uv run ruff check` e `uv run pytest` a cada push de branch de fase e em pull request, com Python 3.12 e `uv`.
- Configuração do resultado da esteira como verificação obrigatória para merge, tratada como passo explícito e verificável.
- Atualização de `docs/testing.md`, que hoje declara o Ruff como ausente.
- Fechamento do item pendente da Definition of Done da SPEC-0006.

#### Fora de escopo

- Contrato de handoff para o projeto-mãe, que passou ao `BACKLOG-0011`.
- Formatação automática por `ruff format`: não foi decidida e mudaria arquivos muito além dos dezenove achados.
- Matriz de versões de Python, ambientes gerenciados, pipeline de deploy e publicação de pacote.
- APM, tracing distribuído e métricas em serviço externo.
- Correção de qualquer achado que apareça fora da configuração declarada, como as noventa e sete ocorrências que a família `TRY` completa produziria.
- Alteração de comportamento de qualquer módulo: as correções são de forma, não de função.

#### Atores

- **Mantenedor do componente**: hoje único responsável por lembrar de executar as verificações antes de publicar. Precisa que a verificação exista localmente e que a esteira a repita sem depender da sua memória.
- **Equipe futura do projeto-mãe**: consumirá este componente e depende de que a barreira exista antes da incorporação, para não herdar código sem verificação.

### 4. Princípios e restrições do projeto

- **PR-001**: a esteira executa exatamente os comandos disponíveis localmente. Um comando que só existe na integração contínua não é reproduzível pelo mantenedor e transforma a esteira em caixa-preta.
- **PR-002**: a configuração do linter usa `extend-select`, nunca `select`. Substituir o conjunto padrão desativaria silenciosamente as regras que hoje protegem o repositório, como `R-003` demonstrou.
- **PR-003**: a reprovação bloqueia o merge. Origem: `.specsfy/RULES.md`, seção Testes, que exige o workflow verde como condição de conclusão do marco.
- **PR-004**: a esteira não recebe credencial, token nem variável de ambiente do projeto, e seu registro de execução não expõe valor sensível. Origem: `.specsfy/RULES.md`, seções Segurança e privacidade e Operação.
- **PR-005**: as correções preservam o comportamento e o alcance do código corrigido. Em particular, quebrar uma linha longa de uma guarda estática não pode reduzir o conjunto que ela varre.
- **PR-006**: a versão do Ruff é fixada. Uma atualização que introduza regra nova não pode reprovar um push sem mudança de código.
- **PR-007**: o Ruff entra somente no grupo de desenvolvimento. Ele não é dependência de execução do pipeline.

### 5. Histórias de usuário

#### US-001 — Verificar o código antes de publicar (P1)

Como mantenedor do componente, quero executar o Ruff localmente e obter zero achado, para corrigir problemas antes que eles entrem no repositório.

**Por que P1**: é a base de tudo o mais. Sem a ferramenta instalada e o código limpo, a esteira nasceria vermelha e a barreira seria inútil.
**Teste independente**: executar `uv run ruff check` e observar a verificação rodar sem achado.
**Requisitos**: FR-001, FR-002, FR-005, NFR-003

#### US-002 — Ter a verificação executada a cada publicação (P1)

Como mantenedor do componente, quero que Ruff e Pytest rodem sozinhos a cada push e pull request, para não depender da minha memória.

**Por que P1**: a regra confirmada em `.specsfy/RULES.md` exige a esteira verde para concluir o marco, e é essa automação que a SPEC-0006 esperava.
**Teste independente**: publicar um push em branch de fase e observar a execução automática no commit.
**Requisitos**: FR-003, NFR-001, NFR-002

#### US-003 — Impedir que código reprovado entre na base (P2)

Como mantenedor do componente, quero que o merge fique bloqueado enquanto a verificação estiver reprovada, para que a esteira seja barreira e não aviso.

**Por que P2**: depende de US-001 e US-002 existirem, mas sem ela o resultado da esteira permanece opcional.
**Teste independente**: abrir um pull request com verificação reprovada e observar o merge impedido.
**Requisitos**: FR-004, NFR-001

### 6. Cenários BDD de aceite

#### AC-001 — Ruff executável localmente

**Cobre**: US-001, FR-001, NFR-003

```gherkin
@US-001 @FR-001 @NFR-003 @AC-001
Feature: Verificação local

  Scenario: Executar o Ruff pelo gerenciador do projeto
    Given o Ruff declarado como dependência do grupo de desenvolvimento
    When o mantenedor executa a verificação pelo gerenciador do projeto
    Then a verificação roda em vez de falhar por ferramenta ausente
    And a versão utilizada é a fixada nas dependências
```

#### AC-002 — Configuração preserva o conjunto padrão

**Cobre**: US-001, FR-001

```gherkin
@US-001 @FR-001 @AC-002
Feature: Configuração do linter

  Scenario: Somar famílias ao padrão em vez de substituí-lo
    Given a configuração declarada no arquivo de projeto
    When o conjunto efetivo de regras é resolvido
    Then as regras do conjunto padrão continuam ativas
    And as famílias acrescentadas também estão ativas
    And a exclusão de diretórios já declarada é preservada
```

#### AC-003 — Verificação local sem achado

**Cobre**: US-001, FR-002

```gherkin
@US-001 @FR-002 @AC-003
Feature: Verificação local

  Scenario: Obter zero achado depois das correções
    Given os dezenove achados corrigidos
    When o mantenedor executa a verificação local
    Then nenhum achado é reportado
    And a suíte de testes permanece verde
```

#### AC-004 — Defeitos semânticos corrigidos

**Cobre**: US-001, FR-002

```gherkin
@US-001 @FR-002 @AC-004
Feature: Correção dos achados

  Scenario: Eliminar os três defeitos semânticos herdados da entrega anterior
    Given os três achados semânticos localizados na entrega anterior
    When a verificação percorre os arquivos correspondentes
    Then nenhum deles é reportado
    And o comportamento provado pelos testes daqueles módulos permanece idêntico
```

#### AC-005 — Largura de linha respeitada sem perda de alcance

**Cobre**: FR-001, FR-002

```gherkin
@FR-001 @FR-002 @AC-005
Feature: Correção dos achados

  Scenario: Quebrar linhas longas preservando o alcance da guarda estática
    Given uma guarda estática cujas listas de identificadores excedem a largura configurada
    When as linhas são quebradas para respeitar o limite
    Then nenhum identificador é removido do conjunto varrido
    And a guarda continua reprovando o conteúdo que reprovava antes
```

#### AC-006 — Push em branch de fase dispara a esteira

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-006
Feature: Execução automática

  Scenario: Verificar um push sem intervenção
    Given a esteira de integração contínua configurada
    When o mantenedor publica um push em uma branch de fase
    Then a verificação e a suíte são executadas automaticamente
    And o resultado fica visível no commit
```

#### AC-007 — Pull request dispara a esteira

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-007
Feature: Execução automática

  Scenario: Verificar um pull request
    Given um pull request aberto para a branch principal
    When a esteira é acionada
    Then a verificação e a suíte são executadas sobre o conteúdo proposto
    And o resultado fica associado ao pull request
```

#### AC-008 — A esteira roda os comandos locais

**Cobre**: US-002, FR-003, NFR-001, NFR-002

```gherkin
@US-002 @FR-003 @NFR-001 @NFR-002 @AC-008
Feature: Reprodutibilidade

  Scenario: Executar exatamente o que o mantenedor executa
    Given a definição da esteira
    When seus passos de verificação são inspecionados
    Then eles usam os mesmos comandos disponíveis localmente
    And nenhum passo exige credencial, token ou variável de ambiente do projeto
```

#### AC-009 — A esteira não recebe segredo

**Cobre**: US-002, FR-003, NFR-002

```gherkin
@US-002 @FR-003 @NFR-002 @AC-009
Feature: Segurança da esteira

  Scenario: Executar a suíte completa sem segredo
    Given a esteira sem nenhum segredo configurado
    When ela executa a suíte completa
    Then todos os casos passam
    And nenhuma etapa falha por credencial ausente
```

#### AC-010 — Merge bloqueado com verificação reprovada

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-010
Feature: Barreira de merge

  Scenario: Impedir a conclusão diante de reprovação
    Given um pull request cuja verificação automática reprovou
    When alguém tenta concluir o merge
    Then o merge é impedido
    And o motivo do impedimento identifica a verificação reprovada
```

#### AC-011 — Merge liberado com verificação aprovada

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-011
Feature: Barreira de merge

  Scenario: Permitir a conclusão com a verificação aprovada
    Given um pull request cuja verificação automática passou
    When alguém conclui o merge
    Then o merge acontece sem impedimento adicional da verificação
```

#### AC-012 — O bloqueio é um passo verificável

**Cobre**: US-003, FR-004, NFR-001

```gherkin
@US-003 @FR-004 @NFR-001 @AC-012
Feature: Barreira de merge

  Scenario: Registrar a configuração que não vive no repositório
    Given que a barreira de merge é ajuste administrativo fora do controle de versão
    When a entrega é conferida
    Then existe um passo próprio que descreve como configurá-la
    And existe uma forma declarada de verificar que ela está ativa
```

#### AC-013 — Versão do Ruff fixada

**Cobre**: FR-001, NFR-003

```gherkin
@FR-001 @NFR-003 @AC-013
Feature: Determinismo

  Scenario: Impedir que uma atualização reprove um push sem mudança de código
    Given a versão do Ruff fixada nas dependências
    When uma versão mais nova do Ruff é publicada
    Then a verificação continua usando a versão fixada
    And atualizá-la exige uma alteração deliberada das dependências
```

#### AC-014 — Registro de execução sem valor sensível

**Cobre**: FR-003, NFR-002

```gherkin
@FR-003 @NFR-002 @AC-014
Feature: Segurança da esteira

  Scenario: Não expor valor sensível no registro
    Given uma execução concluída da esteira
    When seu registro é inspecionado
    Then nenhuma credencial, token ou URL de destino aparece
```

#### AC-015 — Pendência da entrega anterior fechada

**Cobre**: US-001, FR-005

```gherkin
@US-001 @FR-005 @AC-015
Feature: Fechamento da pendência

  Scenario: Cumprir o item que ficou aberto na entrega anterior
    Given a verificação local disponível e sem achado
    When a Definition of Done da entrega anterior é revisada
    Then o item que exigia a verificação de lint pode ser marcado como cumprido
    And a revisão fica registrada na fonte normativa daquela entrega
```

#### AC-016 — Documentação de testes atualizada

**Cobre**: FR-005, NFR-001

```gherkin
@FR-005 @NFR-001 @AC-016
Feature: Documentação

  Scenario: Deixar de declarar a ferramenta como ausente
    Given a documentação de testes que hoje declara a ferramenta indisponível
    When a entrega é concluída
    Then a documentação descreve a verificação como disponível e reproduzível
    And publica o comando exato que o mantenedor executa
```

#### AC-017 — Registro do gate reflete a esteira ativa

**Cobre**: FR-005, NFR-003

```gherkin
@FR-005 @NFR-003 @AC-017
Feature: Documentação

  Scenario: Refletir a esteira nas fontes de contexto do projeto
    Given a esteira ativa e a verificação disponível
    When as fontes de contexto do projeto são revisadas
    Then elas registram a esteira como existente em vez de planejada
    And registram a versão fixada da ferramenta
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O projeto deve declarar o Ruff como dependência do grupo de desenvolvimento, com versão fixada, e configurar no `pyproject.toml` `extend-select = ["E501", "I", "UP", "B", "SIM"]` e `line-length = 100`, preservando o `extend-exclude` já declarado. A configuração usa `extend-select`, não `select`, de modo que o conjunto padrão do Ruff permaneça ativo.
- **FR-002**: O repositório deve ficar sem nenhum achado sob a configuração declarada. Isso exige corrigir os três achados semânticos em `quality.py:70`, `src/quality.py:292` e `src/quality.py:608`, e as dezesseis linhas longas distribuídas em `chat.py`, `search.py`, `src/validation.py`, `upsert_from_chunks.py` e `tests/test_client_neutrality.py`, sem alterar o comportamento nem o alcance do código corrigido.
- **FR-003**: O repositório deve conter um workflow de integração contínua que execute `uv run ruff check` e `uv run pytest` a cada push de branch de fase e em pull request, usando Python 3.12 e `uv`, sem receber credencial, token ou variável de ambiente do projeto, e publicando o resultado no commit e no pull request.
- **FR-004**: O resultado da esteira deve ser configurado como verificação obrigatória para merge, de modo que um pull request com verificação reprovada não possa ser concluído. Por ser ajuste administrativo fora do controle de versão, a entrega deve incluir um passo próprio que descreva como configurá-lo e uma forma declarada de verificar que está ativo.
- **FR-005**: A entrega deve atualizar `docs/testing.md` e as fontes de contexto que hoje declaram a ferramenta ausente, e registrar na fonte normativa da SPEC-0006 que o item pendente da sua Definition of Done pode ser marcado como cumprido.

#### Não funcionais

- **NFR-001**: A esteira executa exatamente os comandos disponíveis localmente, e a barreira de merge é verificável por alguém que não a configurou. **Verificação**: inspeção do workflow confirmando que seus passos de verificação usam os mesmos comandos publicados na documentação, somada ao passo declarado de conferência da barreira.
- **NFR-002**: Nem a esteira nem seu registro de execução recebem ou expõem credencial, token, URL de destino ou variável de ambiente do projeto. **Verificação**: execução da suíte completa na esteira sem nenhum segredo configurado, e inspeção do registro produzido.
- **NFR-003**: A verificação é determinística ao longo do tempo: a versão da ferramenta é fixada, e uma atualização não pode reprovar um push sem mudança de código. **Verificação**: inspeção das dependências confirmando versão fixada, e conferência de que a versão registrada na documentação corresponde à declarada.

#### Erros e casos-limite

- Ruff acusa achado novo em um push → a esteira reprova e o merge fica bloqueado até a correção; a verificação não é desligada para destravar.
- Caso de teste instável reprova a esteira → o caso é corrigido ou isolado; a suíte não é desativada.
- Plataforma de integração contínua indisponível → o mantenedor pode reexecutar; a verificação local permanece como caminho reproduzível, o que é a razão de `PR-001`.
- Quebra de linha em guarda estática reduz o conjunto varrido → violação de `PR-005`; a correção precisa preservar o alcance, o que `AC-005` verifica.
- Configuração declarada com `select` em vez de `extend-select` → o conjunto padrão é substituído e os três defeitos semânticos deixam de ser vistos; `AC-002` existe para impedir essa regressão.
- Ausência de acesso administrativo ao repositório → o workflow pode ser entregue, mas a barreira de merge não; a entrega precisa declarar essa dependência em vez de assumi-la cumprida.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Python 3.12 com `uv`, declarado em `.python-version` e em `requires-python = ">=3.12"`.
- `pyproject.toml` já tem `[dependency-groups] dev = ["pytest>=8.3.0"]`, `[tool.pytest.ini_options]` com `pythonpath` e `testpaths`, e `[tool.ruff] extend-exclude = [".agents"]`.
- 221 casos em vinte arquivos de teste, nenhum exigindo rede, conforme `docs/testing.md`.
- `.github/` não existe no repositório.
- `tests/test_client_neutrality.py` e `tests/test_docs_safety.py` são guardas estáticas que varrem listas de termos; onze das dezesseis linhas longas estão na primeira delas.

#### Arquitetura e módulos

- **`pyproject.toml`** — acrescenta `ruff` ao grupo `dev` com versão fixada e completa o bloco `[tool.ruff]` com `line-length` e `extend-select`, preservando `extend-exclude`.
- **`.github/workflows/ci.yml`** — arquivo novo. Aciona-se em `push` e `pull_request`, prepara Python 3.12 e `uv`, instala as dependências do projeto e executa, em passos separados e nomeados, `uv run ruff check` e `uv run pytest`. Passos separados tornam a causa da reprovação legível sem abrir o registro completo.
- **Correções de forma** — `quality.py`, `src/quality.py`, `chat.py`, `search.py`, `src/validation.py`, `upsert_from_chunks.py` e `tests/test_client_neutrality.py`. Nenhuma altera comportamento.
- **`docs/testing.md`** — deixa de declarar o Ruff ausente e passa a publicar o comando e a versão fixada.
- **`.specsfy/STACK.md`** — registra a esteira e a ferramenta de lint como estruturais.
- **`specs/completed/0006-gate-qualidade-chunks-metadados/spec.md`** — recebe o registro de que o item pendente foi cumprido, sem reabrir seus gates.

#### Migrations

- Não aplicável. Nenhuma persistência é tocada.

#### Models

- Não aplicável. A fatia não introduz estrutura de dados.

#### Controllers e casos de uso

- Não aplicável no sentido de aplicação. Os pontos de entrada desta fatia são comandos: `uv run ruff check` e `uv run pytest`, executados localmente e pela esteira.

#### Views e experiência

- Não aplicável. A superfície é linha de comando e a interface do próprio GitHub, que não é construída por esta entrega.

#### Queries e repositórios

- Não aplicável.

#### Jobs e processamento assíncrono

- A execução da esteira é assíncrona em relação ao push, por natureza da plataforma. Não há retry automático nem fila própria: a reexecução é acionada manualmente pelo mantenedor.

#### Estrutura de arquivos

```text
specs/draft/0007-ruff-e-esteira-de-integracao-continua/
  spec.md
  research/
.github/
  workflows/
    ci.yml
pyproject.toml
docs/testing.md
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Configuração do linter | bloco `[tool.ruff]` do `pyproject.toml` | `line-length` igual a 100; `extend-select` com as cinco famílias; `extend-exclude` preservado | consumida pelo comando local e pela esteira |
| Definição da esteira | `.github/workflows/ci.yml` | gatilhos de push e pull request; versão de Python; passos de verificação nomeados; nenhum segredo | produz o resultado consumido pela barreira de merge |
| Barreira de merge | configuração do repositório no GitHub | nome da verificação exigida; escopo da branch protegida | consome o resultado da esteira; não vive no repositório |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Execução da esteira | pendente | verificação e suíte passam | aprovada | merge liberado pela barreira |
| Execução da esteira | pendente | verificação ou suíte reprova | reprovada | merge impedido; causa identificada no passo que falhou |
| Execução da esteira | reprovada | correção publicada | pendente | nova execução substitui a anterior no mesmo pull request |
| Item pendente da SPEC-0006 | aberto | verificação local disponível e sem achado | cumprido | registro feito na fonte normativa daquela entrega, sem reabrir seus gates |

#### Migração e retenção

- Não aplicável. O histórico de execuções pertence à plataforma e não é gerenciado por esta entrega.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega é consumida por comando de terminal e pela interface do próprio GitHub, que já existe e não é construída aqui. Este repositório não possui frontend, conforme `docs/frontend.md` e `INTERFACE.md`.

#### Stack e convenções de interface

- Não aplicável. Nenhum framework de interface consta de `pyproject.toml` ou do código.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável. O fluxo é comando, execução e resultado publicado no commit e no pull request.

#### Menus e navegação principal

- Não aplicável.

#### Formulários e ações

- Não aplicável. A entrada é o próprio push ou pull request.

#### Composição e disposição

- Não aplicável. A apresentação do resultado pertence ao GitHub.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável |

- Não aplicável: o repositório não usa React, Tailwind, shadcn/ui nem ReUI, e esta fatia não introduz nenhum deles.

#### Estados e acessibilidade

- Os estados observáveis são aprovado, reprovado e pendente, cada um distinguível por texto e por código de saída dos comandos, não apenas por cor na interface da plataforma.
- A causa de uma reprovação é legível pelo nome do passo que falhou, sem exigir a leitura do registro completo.

#### Contrato CRUD

- Não aplicável. A fatia não administra registros.

#### Revisão visual durante o desenvolvimento

- O item `VISUAL` de cada tarefa é registrado como `Não aplicável`, com o motivo concreto: a entrega não possui superfície visual construída por este repositório. A conferência equivalente é a legibilidade do nome dos passos da esteira e do texto publicado em `docs/testing.md`.

#### APIs expostas

- **Comando**: `uv run ruff check`. Sem autenticação. Saída: lista de achados e código de saída zero quando não há nenhum.
- **Comando**: `uv run pytest`. Sem autenticação. Saída: resultado da suíte e código de saída correspondente.
- Nenhuma API de rede é exposta por esta fatia.

#### APIs externas utilizadas

- GitHub Actions como plataforma de execução, e as ações públicas de preparação de ambiente que o workflow declarar. Nenhuma credencial do projeto é fornecida a elas. As versões das ações são fixadas, pela mesma razão de `PR-006`.

#### Documentação das APIs consultadas

- Não aplicável. Nenhuma API foi consultada; o comportamento do Ruff foi observado por execução local.

#### Eventos e outros contratos

- **Contrato implícito com a barreira de merge**: o nome da verificação publicada pela esteira é o identificador que a configuração do repositório exige. Renomear o passo ou o workflow quebra a barreira sem quebrar o workflow, o que torna o nome parte do contrato e não detalhe de implementação.

### 11. Estratégia TDD

- **Unidade**: conferência da configuração declarada no `pyproject.toml` — presença de `extend-select` e ausência de `select`, valor de `line-length`, preservação de `extend-exclude`, e versão fixada do Ruff.
- **Integração/contrato**: execução real de `uv run ruff check` sobre o repositório, esperando zero achado; conferência do arquivo de workflow quanto aos gatilhos, aos comandos e à ausência de segredo.
- **BDD/aceite**: os dezessete cenários da seção 6 são o contrato de referência. Nenhum arquivo `.feature` é criado ou executado.
- **Runner TDD**: Pytest, já adotado. `uv run pytest`.
- **E2E**: não aplicável.
- **Verificação manual**: os cenários `AC-010` e `AC-011`, sobre o bloqueio de merge, dependem de configuração administrativa no GitHub e não podem ser automatizados a partir do repositório. Serão verificados manualmente, com procedimento, responsável e evidência registrados, conforme `FR-004`. Os demais cenários são automatizáveis.

Os casos desta fatia ficam concentrados em `tests/test_ci_gates.py`, isolando a fatia conforme a mitigação já adotada pelas anteriores para a contagem de cobertura.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, NFR-003, AC-001 | AC-001 na seção 6 | caso de Ruff declarado no grupo de desenvolvimento em `tests/test_ci_gates.py` | RED em 2026-09-03: `ruff==0.16.5` ausente do grupo `dev` | GREEN em 2026-09-03: Ruff 0.16.5 declarado e executável | 3 casos focais verdes; regressão pendente |
| US-001, FR-001, AC-002 | AC-002 na seção 6 | caso de `extend-select` com ausência de `select` em `tests/test_ci_gates.py` | RED em 2026-09-03: `line-length` e `extend-select` ausentes | GREEN em 2026-09-03: configuração aditiva e largura 100 | 3 casos focais verdes; regressão pendente |
| US-001, FR-002, AC-003 | AC-003 na seção 6 | caso de execução real sem achado em `tests/test_ci_gates.py` | RED em 2026-09-03: `uv run ruff check` encerrou com código 2 porque Ruff não está instalado | GREEN em 2026-09-03: verificação completa sem achados | Ruff e regressões focais verdes; suíte total pendente |
| US-001, FR-002, AC-004 | AC-004 na seção 6 | caso de ausência dos três achados semânticos em `tests/test_ci_gates.py` | RED em 2026-09-03: medição isolada encontrou `TRY004`, `PIE810` e `ISC004` | GREEN em 2026-09-03: três códigos ausentes e 27 testes de qualidade verdes | Regressão focal concluída; suíte total pendente |
| FR-001, FR-002, AC-005 | AC-005 na seção 6 | caso de preservação do alcance da guarda estática em `tests/test_ci_gates.py` | RED em 2026-09-03: alcance preservado, mas Ruff 0.16.5 encontrou 16 `E501` com largura 100 | GREEN em 2026-09-03: E501 zerado e conjunto protegido preservado | 14 casos de neutralidade verdes; suíte total pendente |
| US-002, FR-003, AC-006 | AC-006 na seção 6 | caso de gatilho de push no workflow em `tests/test_ci_gates.py` | RED em 2026-09-03: `.github/workflows/ci.yml` ausente | GREEN em 2026-09-03: gatilho `push` declarado | Contrato local verde; execução remota pendente |
| US-002, FR-003, AC-007 | AC-007 na seção 6 | caso de gatilho de pull request no workflow em `tests/test_ci_gates.py` | RED em 2026-09-03: `.github/workflows/ci.yml` ausente | GREEN em 2026-09-03: gatilho `pull_request` declarado | Contrato local verde; execução remota pendente |
| US-002, FR-003, NFR-001, NFR-002, AC-008 | AC-008 na seção 6 | caso de equivalência entre comandos locais e da esteira em `tests/test_ci_gates.py` | RED em 2026-09-03: workflow e passos locais ausentes | GREEN em 2026-09-03: comandos locais em passos separados e nomeados | Contrato local verde; execução remota pendente |
| US-002, FR-003, NFR-002, AC-009 | AC-009 na seção 6 | caso de ausência de segredo no workflow em `tests/test_ci_gates.py` | RED em 2026-09-03: workflow auditável ausente | GREEN em 2026-09-03: nenhum segredo ou credencial declarado | Contrato local verde; execução remota pendente |
| US-003, FR-004, AC-010 | AC-010 na seção 6 | verificação manual registrada, com procedimento, responsável e evidência | RED em 2026-09-03: linha manual ainda está `Pending` | GREEN em 2026-09-03: PR #2 com `_ci_barrier_probe.py` (import não usado) reprovou o check `Ruff and Pytest` (runs 33789500214/33789504941); `mergeStateStatus=BLOCKED` e `gh pr merge` recusado pelo GitHub | Arquivo de prova removido no commit de liberação; responsável marciohernandez |
| US-003, FR-004, AC-011 | AC-011 na seção 6 | verificação manual registrada, com procedimento, responsável e evidência | RED em 2026-09-03: linha manual ainda está `Pending` | GREEN em 2026-09-03: commit de remoção do arquivo de prova no PR #2, com evidência de AC-010 registrada e regressão completa executada nesta mesma tarefa T024/T027 | Regressão completa verde (seção 12); responsável marciohernandez |
| US-003, FR-004, NFR-001, AC-012 | AC-012 na seção 6 | caso de existência do passo declarado de conferência da barreira em `tests/test_ci_gates.py` | RED em 2026-09-03: procedimento de proteção ausente em `docs/testing.md` | GREEN em 2026-09-03: configuração e ensaio publicados | Caso focal verde; comprovação remota pendente |
| FR-001, NFR-003, AC-013 | AC-013 na seção 6 | caso de versão fixada do Ruff em `tests/test_ci_gates.py` | RED em 2026-09-03: pin ausente de `pyproject.toml` e `uv.lock` | GREEN em 2026-09-03: manifest e lockfile fixam 0.16.5 | `uv run ruff --version` → `ruff 0.16.5`; regressão pendente |
| FR-003, NFR-002, AC-014 | AC-014 na seção 6 | caso de ausência de valor sensível nos passos do workflow em `tests/test_ci_gates.py` | RED em 2026-09-03: workflow auditável ausente | GREEN em 2026-09-03: comandos não imprimem configuração sensível | Contrato local verde; log remoto pendente |
| US-001, FR-005, AC-015 | AC-015 na seção 6 | caso de registro do item cumprido na spec anterior em `tests/test_ci_gates.py` | RED em 2026-09-03: item da SPEC-0006 permanece aberto | GREEN em 2026-09-03: pendência marcada como cumprida pela SPEC-0007 | SPEC-0006 permanece `Complete` com três gates `Passed` |
| FR-005, NFR-001, AC-016 | AC-016 na seção 6 | caso de documentação de testes atualizada em `tests/test_ci_gates.py` | RED em 2026-09-03: documento ainda declara Ruff ausente | GREEN em 2026-09-03: comando e versão publicados | Documentador e monitor verdes |
| FR-005, NFR-003, AC-017 | AC-017 na seção 6 | caso de fontes de contexto atualizadas em `tests/test_ci_gates.py` | RED em 2026-09-03: stack registra Ruff efêmero e não GitHub Actions | GREEN em 2026-09-03: stack registra Ruff 0.16.5 e GitHub Actions | `PROJECT.md` revisado; monitor `CURRENT` |

### 12. Plano de testes e rastreabilidade

Regressão completa da fatia: `uv run pytest`. Verificação estática: `uv run ruff check`.

| Requisito | Cenário BDD | Nível | Arquivo e comando focal | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T018 |
| FR-001 | AC-002 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T018 |
| FR-001 | AC-005 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T021 |
| FR-001 | AC-013 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T018 |
| FR-002 | AC-003 | Integração | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T021 |
| FR-002 | AC-004 | Integração | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T019 |
| FR-002 | AC-005 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T021 |
| FR-003 | AC-006 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed localmente em T022; remoto pendente |
| FR-003 | AC-007 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed localmente em T022; remoto pendente |
| FR-003 | AC-008 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T022 |
| FR-003 | AC-009 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed localmente em T022; remoto pendente |
| FR-003 | AC-014 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed localmente em T022; log remoto pendente |
| FR-004 | AC-010 | Manual | verificação no repositório do GitHub, com evidência registrada | Bloqueado — PR #2, commit 4f9be0e, data 2026-09-03, responsável: marciohernandez, evidência: runs 33789500214/33789504941 reprovados por `Ruff and Pytest`; `mergeStateStatus=BLOCKED`; `gh pr merge` recusado ("the base branch policy prohibits the merge") |
| FR-004 | AC-011 | Manual | verificação no repositório do GitHub, com evidência registrada | Liberado — PR #2, commit deste registro, data 2026-09-03, responsável: marciohernandez, evidência: arquivo de prova removido, `Ruff and Pytest` aprovado e `mergeStateStatus` sem o impedimento do check (ver seção 12 para a regressão completa) |
| FR-004 | AC-012 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T023 |
| FR-005 | AC-015 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T025 |
| FR-005 | AC-016 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T026 |
| FR-005 | AC-017 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T026 |
| NFR-001 | AC-008 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T022 |
| NFR-001 | AC-012 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T023 |
| NFR-001 | AC-016 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T026 |
| NFR-002 | AC-008 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T022 |
| NFR-002 | AC-009 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed localmente em T022; remoto pendente |
| NFR-002 | AC-014 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed localmente em T022; log remoto pendente |
| NFR-003 | AC-001 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T018 |
| NFR-003 | AC-013 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T018 |
| NFR-003 | AC-017 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Passed em T026 |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY — 2026-09-03
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0007-ruff-e-esteira-de-integracao-continua/spec.md --allow-draft` → `VALID DRAFT`. Formato `Specsfy/2.0`, três atos na ordem, slug igual ao diretório, pacote restrito a `spec.md` e nenhum `research/`, coerente com a declaração de que não houve fonte externa.
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/review_findings.mjs --spec specs/defined/0007-ruff-e-esteira-de-integracao-continua/spec.md --root .`
- **Cobertura**: 3 `US`, 5 `FR`, 3 `NFR`, 17 `AC`, 6 `DEC`, 7 `PR`. Todos os onze requisitos alcançam ao menos três cenários; nenhum `AC` referencia identificador inexistente. A tabela RED-GREEN-REFACTOR prevê dezessete casos e repete a mesma cobertura.
- **Conferência de contexto**: a Definition of Done cita `.specsfy/STACK.md`, porque a fatia acrescenta ferramenta estrutural e esteira, e exige revisão de `PROJECT.md`. `.specsfy/DATABASE.md` não é exigido: nenhuma persistência é tocada. `git check-ignore` confirma que `.github/workflows/ci.yml` não seria ignorado pelo repositório.
- **Achados**: dois registrados, nenhum bloqueante.

- **FIND-ARCH-001** [P2] [Open] O cenário `AC-003` verifica a ausência de achados executando o linter, o que faz a suíte de testes depender da ferramenta instalada e reportar a mesma reprovação duas vezes na esteira, uma no passo de lint e outra no passo de testes — Refs: FR-002, AC-003, NFR-001 — Evidence: tests/test_client_neutrality.py:115 — Effect: o acoplamento em si tem precedente no repositório, que já executa `git ls-files` por subprocesso e falha explicitamente quando o diretório de controle de versão está ausente, em vez de passar por vacuidade; o risco não é o subprocesso e sim passar por vacuidade quando o linter não estiver instalado, exatamente a situação que esta fatia existe para corrigir — Suggestion: o caso derivado de `AC-003` deve falhar de forma explícita quando o executável do linter não for encontrado, seguindo o padrão de `_git_ls_files`, e o planejamento deve declarar que `uv run pytest` passa a depender da ferramenta de desenvolvimento instalada

- **FIND-PROD-001** [P3] [Open] O requisito `FR-005` manda registrar na fonte normativa da SPEC-0006, já `Complete`, que o item pendente da sua Definition of Done foi cumprido — Refs: FR-005, AC-015 — Evidence: specs/completed/0006-gate-qualidade-chunks-metadados/spec.md — Effect: editar uma spec concluída é exceção ao ciclo normal, e uma alteração descuidada poderia sugerir que seus gates foram recalculados quando não foram — Suggestion: a tarefa correspondente deve limitar a alteração à marcação daquele item e a uma nota datada que cite esta fatia, preservando o texto dos três gates e o registro da pendência externa como histórico
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`, severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: READY — 2026-09-03
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0007-ruff-e-esteira-de-integracao-continua/spec.md --allow-draft` → `total=27 complete=17 tdd=18 code=5 checklist_items=162 checklist_complete=102 covered_spec_ids=28 required_spec_ids=28`, `VALID DRAFT`.
- **Comando RED**: `uv run pytest tests/test_ci_gates.py --tb=short` → 17 failed, todos por comportamento ausente ou incorreto: dependência/configuração do Ruff, três achados semânticos, dezesseis linhas acima de 100 colunas, workflow ausente, evidência administrativa pendente e documentação/contexto desatualizados.
- **Medição isolada**: `uvx ruff@0.16.5 check --select TRY004,PIE810,ISC004 quality.py src/quality.py` → três achados; `uvx ruff@0.16.5 check --select E501 --line-length 100 chat.py search.py src/validation.py upsert_from_chunks.py tests/test_client_neutrality.py` → dezesseis achados.
- **Rastreabilidade**: `check_traceability.mjs` → 28/28 IDs cobertos. O auditor também reporta os marcadores órfãos históricos de outras specs, limitação já registrada em `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md`; a mitigação vigente é o arquivo próprio `tests/test_ci_gates.py`.
- **Achados**: nenhum bloqueio. T001–T017 concluídas com marcador próprio, RED registrado e produção intacta.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0007-ruff-e-esteira-de-integracao-continua/spec.md .`
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

Runner: Pytest, já adotado pelo repositório. Comando focal das tarefas TDD:
`uv run pytest tests/test_ci_gates.py`. Regressão: `uv run pytest`. O Gherkin
permanece somente na seção 6; cada caso executável recebe marcador próprio
`SPECSFY:` em `tests/test_ci_gates.py`.

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 o caso de dependência e versão do Ruff em tests/test_ci_gates.py — Refs: US-001, FR-001, NFR-003, AC-001 — Depends: none
  - [x] **PREP**: AC-001 e o baseline foram conferidos; o grupo `dev` contém somente `pytest>=8.3.0`.
  - [x] **EXECUTE**: Criado o caso `test_ruff_is_a_pinned_development_dependency` com marcador próprio em `tests/test_ci_gates.py`.
  - [x] **VERIFY**: RED válido: o caso falha porque `ruff==0.16.5` não pertence às dependências de desenvolvimento.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa somente um teste de configuração, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_ci_gates.py -k test_ruff_is_a_pinned_development_dependency` → 1 failed por `AssertionError`, após proteção do banco `SAFE`.
  - [x] **IMPROVE**: A asserção exige igualdade do pin completo, distinguindo-o de intervalos de versão abertos.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 o caso do conjunto efetivo de regras em tests/test_ci_gates.py — Refs: US-001, FR-001, AC-002 — Depends: none
  - [x] **PREP**: AC-002 e o bloco atual foram conferidos; somente `extend-exclude = [".agents"]` estava declarado.
  - [x] **EXECUTE**: Criado o caso `test_ruff_extends_the_default_rule_set` com marcador próprio, cobrindo `line-length`, `extend-select`, ausência de `select` e exclusão preservada.
  - [x] **VERIFY**: RED válido: `line-length` retornou `None` em vez de 100 antes da implementação.
  - [x] **VISUAL**: Não aplicável — a tarefa verifica configuração textual, sem interface construída.
  - [x] **EVIDENCE**: `uv run pytest tests/test_ci_gates.py -k test_ruff_extends_the_default_rule_set` → 1 failed, 1 deselected, após proteção do banco `SAFE`.
  - [x] **IMPROVE**: O caso cobre largura e extensão do conjunto sem duplicar a verificação de pin da T001/T013.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 o caso de execução real do Ruff em tests/test_ci_gates.py — Refs: US-001, FR-002, AC-003 — Depends: none
  - [x] **PREP**: AC-003 e o padrão `_git_ls_files` foram lidos; a prova não pode passar por vacuidade.
  - [x] **EXECUTE**: Criado `test_ruff_check_runs_cleanly_over_the_repository` com subprocesso real e marcador próprio.
  - [x] **VERIFY**: RED válido: `uv run ruff check` encerrou com código 2 por executável ausente.
  - [x] **VISUAL**: Não aplicável — a tarefa exercita um comando CLI, sem elementos visuais do produto.
  - [x] **EVIDENCE**: `uv run pytest tests/test_ci_gates.py --tb=short` → AC-003 falhou explicitamente por `Failed to spawn: ruff`, após proteção `SAFE`.
  - [x] **IMPROVE**: O teste propaga stdout e stderr do subprocesso, tornando a causa diagnóstica.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 o caso dos três achados semânticos em tests/test_ci_gates.py — Refs: US-001, FR-002, AC-004 — Depends: none
  - [x] **PREP**: AC-004 e os arquivos afetados foram conferidos sem fixar números de linha no teste.
  - [x] **EXECUTE**: Criado `test_ruff_reports_no_known_semantic_findings` com marcador próprio e seleção dos três códigos.
  - [x] **VERIFY**: RED válido confirmado por `uvx ruff@0.16.5`: `TRY004`, `PIE810` e `ISC004` permanecem presentes.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste estático sem superfície visual.
  - [x] **EVIDENCE**: O arquivo focal falhou e a medição efêmera isolada reportou exatamente três achados semânticos.
  - [x] **IMPROVE**: O oráculo seleciona códigos e caminhos, não posições frágeis.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 o caso de largura e alcance da guarda em tests/test_ci_gates.py — Refs: US-001, FR-001, FR-002, AC-005 — Depends: none
  - [x] **PREP**: AC-005, três ferramentas e oito identificadores da guarda foram inventariados.
  - [x] **EXECUTE**: Criado `test_ruff_line_length_passes_without_reducing_guard_scope`, cobrindo E501 e o conjunto protegido.
  - [x] **VERIFY**: RED válido: alcance preservado e Ruff 0.16.5 encontrou 16 linhas acima de 100 colunas.
  - [x] **VISUAL**: Não aplicável — a tarefa cobre código de teste e configuração, sem interface.
  - [x] **EVIDENCE**: `uvx ruff@0.16.5 check --select E501 --line-length 100 ...` → 16 errors; arquivo focal também vermelho após proteção `SAFE`.
  - [x] **IMPROVE**: A prova usa pertinência em conjuntos e independe da disposição das quebras.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 o caso do gatilho de push em tests/test_ci_gates.py — Refs: US-002, FR-003, AC-006 — Depends: none
  - [x] **PREP**: AC-006 foi lido e a ausência de `.github/workflows/ci.yml` confirmada.
  - [x] **EXECUTE**: Criado `test_ci_runs_on_push_for_phase_branches` com marcador próprio e leitura estrutural do YAML.
  - [x] **VERIFY**: RED válido pela ausência do workflow, antes de qualquer configuração de CI.
  - [x] **VISUAL**: Não aplicável — a tarefa inspeciona YAML de automação, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_ci_gates.py --tb=short` reportou `.github/workflows/ci.yml ainda não existe`.
  - [x] **IMPROVE**: O teste exige `push` sem restringir padrões de nome das branches.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 o caso do gatilho de pull request em tests/test_ci_gates.py — Refs: US-002, FR-003, AC-007 — Depends: none
  - [x] **PREP**: AC-007 foi lido e o contrato estrutural de `pull_request` definido.
  - [x] **EXECUTE**: Criado `test_ci_runs_on_pull_requests` com marcador próprio.
  - [x] **VERIFY**: RED válido pela ausência do workflow e, portanto, do gatilho esperado.
  - [x] **VISUAL**: Não aplicável — a tarefa verifica contrato de CI em arquivo, sem interface do projeto.
  - [x] **EVIDENCE**: O arquivo focal falhou com mensagem explícita de workflow ausente.
  - [x] **IMPROVE**: A leitura por YAML não depende da ordem das chaves.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 o caso dos comandos reproduzíveis em tests/test_ci_gates.py — Refs: US-002, FR-003, NFR-001, NFR-002, AC-008 — Depends: none
  - [x] **PREP**: AC-008 e os comandos locais `uv run ruff check` e `uv run pytest` foram confirmados.
  - [x] **EXECUTE**: Criado `test_ci_uses_the_same_named_local_commands` com marcador próprio e extração dos passos `run`.
  - [x] **VERIFY**: RED válido porque o arquivo que deveria declarar os dois passos ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa cobre comandos e YAML, sem tela mantida pelo repositório.
  - [x] **EVIDENCE**: O arquivo focal falhou antes de encontrar qualquer comando de CI.
  - [x] **IMPROVE**: A prova compara comandos completos e não depende do nome decorativo de cada passo.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 o caso de execução sem segredos em tests/test_ci_gates.py — Refs: US-002, FR-003, NFR-002, AC-009 — Depends: none
  - [x] **PREP**: AC-009 e os nomes de credenciais dos providers foram mapeados sem abrir `.env`.
  - [x] **EXECUTE**: Criado `test_ci_does_not_receive_project_secrets` com marcador próprio e lista de padrões proibidos.
  - [x] **VERIFY**: RED válido: não há workflow auditável para comprovar ausência de segredos.
  - [x] **VISUAL**: Não aplicável — a tarefa é uma guarda estática de segurança sem interface.
  - [x] **EVIDENCE**: O arquivo focal falhou pela ausência de `.github/workflows/ci.yml` após proteção `SAFE`.
  - [x] **IMPROVE**: A guarda lê apenas o workflow e nunca carrega valores de ambiente.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-010 o contrato de evidência de merge bloqueado em tests/test_ci_gates.py — Refs: US-003, FR-004, AC-010 — Depends: none
  - [x] **PREP**: AC-010 foi lido e o limite automatizável foi fixado em procedimento e evidência manual registrada.
  - [x] **EXECUTE**: Criado `test_failed_required_check_has_manual_blocking_evidence` com marcador próprio.
  - [x] **VERIFY**: RED válido porque a linha manual de AC-010 ainda termina em `Pending`.
  - [x] **VISUAL**: Não aplicável — a interface do GitHub não é construída nem alterada por esta tarefa.
  - [x] **EVIDENCE**: O arquivo focal falhou sobre a linha de rastreabilidade manual ainda pendente.
  - [x] **IMPROVE**: O teste não acessa rede nem API e exige responsável e evidência na fonte normativa.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 o contrato de evidência de merge liberado em tests/test_ci_gates.py — Refs: US-003, FR-004, AC-011 — Depends: none
  - [x] **PREP**: AC-011 foi lido e os campos mínimos do registro manual foram definidos.
  - [x] **EXECUTE**: Criado `test_successful_required_check_has_manual_release_evidence` com marcador próprio.
  - [x] **VERIFY**: RED válido porque a linha manual de AC-011 ainda termina em `Pending`.
  - [x] **VISUAL**: Não aplicável — a tarefa valida texto e evidência externa, sem interface do produto.
  - [x] **EVIDENCE**: O arquivo focal registrou a pendência específica do cenário de liberação.
  - [x] **IMPROVE**: O caso exige evidência do estado liberado sem afirmar que o merge precisa ser consumado.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 o caso do procedimento verificável em tests/test_ci_gates.py — Refs: US-003, FR-004, NFR-001, AC-012 — Depends: none
  - [x] **PREP**: AC-012 foi lido e `docs/testing.md` definido como destino do procedimento.
  - [x] **EXECUTE**: Criado `test_branch_protection_procedure_is_reproducible` com marcador próprio e quatro elementos essenciais.
  - [x] **VERIFY**: RED válido porque a documentação ainda não contém o procedimento de proteção.
  - [x] **VISUAL**: Não aplicável — a tarefa verifica documentação técnica, sem superfície visual.
  - [x] **EVIDENCE**: O arquivo focal falhou na conjunção dos termos obrigatórios após proteção `SAFE`.
  - [x] **IMPROVE**: A guarda aceita mudanças editoriais e conserva os estados bloqueado e liberado.

- [x] T013 [TEST] [TDD] [US-001] Derivar do AC-013 o caso de pin determinístico em tests/test_ci_gates.py — Refs: US-001, FR-001, NFR-003, AC-013 — Depends: none
  - [x] **PREP**: AC-013 e a versão medida 0.16.5 foram confirmados nas fontes da spec.
  - [x] **EXECUTE**: Criado `test_ruff_pin_is_locked_at_the_measured_version`, cobrindo manifest e lockfile.
  - [x] **VERIFY**: RED válido: o grupo `dev` contém zero ocorrência de `ruff==0.16.5`.
  - [x] **VISUAL**: Não aplicável — a tarefa cobre determinismo de dependência, sem interface.
  - [x] **EVIDENCE**: O arquivo focal falhou antes da inspeção do lockfile, após proteção `SAFE`.
  - [x] **IMPROVE**: `tomllib` substitui regex permissiva na leitura do manifest.

- [x] T014 [TEST] [TDD] [US-002] Derivar do AC-014 o caso de logs sem valores sensíveis em tests/test_ci_gates.py — Refs: US-002, FR-003, NFR-002, AC-014 — Depends: none
  - [x] **PREP**: AC-014 foi lido e nomes sensíveis foram separados de metadados permitidos.
  - [x] **EXECUTE**: Criado `test_ci_commands_do_not_log_sensitive_configuration` sem abrir `.env`.
  - [x] **VERIFY**: RED válido porque não há workflow auditável para provar o contrato de log.
  - [x] **VISUAL**: Não aplicável — a tarefa cobre segurança de logs, sem interface visual.
  - [x] **EVIDENCE**: O arquivo focal falhou pela ausência da definição da esteira.
  - [x] **IMPROVE**: A lista evita nomes genéricos que confundiriam ações públicas versionadas com segredos.

- [x] T015 [TEST] [TDD] [US-001] Derivar do AC-015 o caso de fechamento da SPEC-0006 em tests/test_ci_gates.py — Refs: US-001, FR-005, AC-015 — Depends: none
  - [x] **PREP**: AC-015 e o único item aberto na Definition of Done da SPEC-0006 foram localizados.
  - [x] **EXECUTE**: Criado `test_previous_spec_records_the_ruff_gap_as_closed` com marcador próprio.
  - [x] **VERIFY**: RED válido: a seção 18 anterior ainda possui um item aberto que cita `uv run ruff check`.
  - [x] **VISUAL**: Não aplicável — a tarefa verifica uma fonte normativa Markdown, sem interface.
  - [x] **EVIDENCE**: O arquivo focal exibiu exatamente o item aberto da entrega anterior.
  - [x] **IMPROVE**: A prova limita sua leitura à Definition of Done e exige vínculo explícito com a SPEC-0007.

- [x] T016 [TEST] [TDD] [US-001] Derivar do AC-016 o caso da documentação reproduzível em tests/test_ci_gates.py — Refs: US-001, FR-005, NFR-001, AC-016 — Depends: none
  - [x] **PREP**: AC-016 e a declaração de Ruff ausente em `docs/testing.md` foram confirmados.
  - [x] **EXECUTE**: Criado `test_testing_documentation_publishes_the_available_ruff_command` com marcador próprio.
  - [x] **VERIFY**: RED válido: a documentação não publica `uv run ruff check` e mantém a lacuna antiga.
  - [x] **VISUAL**: Não aplicável — a tarefa cobre documentação textual, sem tela do sistema.
  - [x] **EVIDENCE**: O arquivo focal falhou na primeira asserção sobre o comando reproduzível.
  - [x] **IMPROVE**: O teste verifica fatos essenciais sem exigir redação idêntica.

- [x] T017 [TEST] [TDD] [US-001] Derivar do AC-017 o caso das fontes de contexto em tests/test_ci_gates.py — Refs: US-001, FR-005, NFR-003, AC-017 — Depends: none
  - [x] **PREP**: AC-017 e a linha `Ruff efêmero por uvx` da stack foram conferidos.
  - [x] **EXECUTE**: Criado `test_stack_records_pinned_ruff_and_github_actions` com marcador próprio.
  - [x] **VERIFY**: RED válido: `Ruff 0.16.5` e `GitHub Actions` não aparecem no contexto atual.
  - [x] **VISUAL**: Não aplicável — a tarefa inspeciona documentação estrutural, sem interface.
  - [x] **EVIDENCE**: O arquivo focal falhou ao exigir a versão fixada na stack.
  - [x] **IMPROVE**: A prova exige fatos estruturais e deixa detalhes operacionais para `docs/testing.md`.

#### Fase 2 — US-001 Verificação local reproduzível (P1)

**Objetivo**: disponibilizar o Ruff fixado, preservar seu conjunto padrão e
eliminar os dezenove achados sem mudar comportamento.
**Teste independente**: `uv run ruff check` retorna código zero e
`uv run pytest tests/test_ci_gates.py -k 'AC_001 or AC_002 or AC_003 or AC_004 or AC_005 or AC_013'` passa.

- [x] T018 [CODE] [US-001] Declarar Ruff 0.16.5 e sua configuração em ./pyproject.toml e ./uv.lock — Refs: US-001, FR-001, NFR-003, AC-001, AC-002, AC-013 — Depends: T001, T002, T013
  - [x] **PREP**: REDs T001, T002 e T013 confirmados; documentação reconstruída e `extend-exclude = [".agents"]` preservado.
  - [x] **EXECUTE**: `ruff==0.16.5` foi adicionado apenas ao grupo `dev`; `line-length = 100` e `extend-select` foram declarados e `uv.lock` atualizado.
  - [x] **VERIFY**: Três casos focais passaram e `uv run ruff --version` confirmou `ruff 0.16.5`.
  - [x] **VISUAL**: Não aplicável — a mudança afeta manifest e configuração CLI, sem superfície visual.
  - [x] **EVIDENCE**: GREEN registrado nas seções 11–12; `.specsfy/STACK.md` atualizado, monitor `CURRENT` e `PROJECT.md` revisado sem impacto material na finalidade ou nas capacidades do produto.
  - [x] **IMPROVE**: Confirmado que o Ruff não entrou em `[project].dependencies`; nenhuma dependência de runtime foi acrescentada.
  <!-- specsfy:evidence {"task":"T018","refs":["US-001","FR-001","NFR-003","AC-001","AC-002","AC-013"],"files":["pyproject.toml","uv.lock",".specsfy/STACK.md"],"commands":[{"run":"uv run pytest tests/test_ci_gates.py -k 'pinned_development or extends_the_default or pin_is_locked'","exit":0},{"run":"uv run ruff --version","exit":0}]} -->

- [x] T019 [CODE] [US-001] Corrigir os achados semânticos em quality.py e src/quality.py — Refs: US-001, FR-002, AC-003, AC-004, AC-005 — Depends: T003, T004, T005, T018
  - [x] **PREP**: REDs T003–T005 confirmados; `docs/` reconstruído e testes de qualidade revisados, incluindo o tratamento da exceção na fronteira CLI.
  - [x] **EXECUTE**: `TRY004` usa `TypeError` capturado pela CLI, `PIE810` usa tupla em `endswith` e `ISC004` foi removido com mensagem intermediária idêntica.
  - [x] **VERIFY**: Ruff passou para os três códigos; `tests/test_quality_gate.py` teve 27 passed e o caso semântico da SPEC-0007 passou.
  - [x] **VISUAL**: Não aplicável — a alteração é interna a CLI e avaliação de qualidade, sem interface visual.
  - [x] **EVIDENCE**: GREEN registrado; monitor `CURRENT`, documentação reconstruída e `PROJECT.md` sem impacto material porque finalidade, capacidades, limites e mensagens observáveis foram preservados.
  - [x] **IMPROVE**: A mensagem de erro passou a ter nome próprio antes de compor a tupla, eliminando concatenação ambígua; a migração para `[tool.ruff.lint]` não foi aplicada porque FR-001 exige a chave no bloco atual.
  <!-- specsfy:evidence {"task":"T019","refs":["US-001","FR-002","AC-003","AC-004","AC-005"],"files":["quality.py","src/quality.py","docs/testing.md"],"commands":[{"run":"uv run ruff check --select TRY004,PIE810,ISC004 quality.py src/quality.py","exit":0},{"run":"uv run pytest tests/test_quality_gate.py","exit":0},{"run":"uv run pytest tests/test_ci_gates.py -k semantic_findings","exit":0}]} -->

- [x] T020 [CODE] [US-001] Corrigir linhas longas em chat.py, search.py, src/validation.py e upsert_from_chunks.py — Refs: US-001, FR-001, FR-002, AC-003, AC-004, AC-005 — Depends: T003, T004, T005, T018
  - [x] **PREP**: Baseline E501 confirmado, `docs/` reconstruído e mensagens, assinatura e argumentos afetados registrados para comparação literal.
  - [x] **EXECUTE**: Cinco linhas foram quebradas nos quatro módulos; strings e chamadas preservam o mesmo conteúdo e a assinatura longa foi distribuída por parâmetros.
  - [x] **VERIFY**: E501 passou nos quatro arquivos e 31 testes de neutralidade e validação passaram.
  - [x] **VISUAL**: Não aplicável — são ajustes de forma em comandos de terminal, sem tela mantida pelo projeto.
  - [x] **EVIDENCE**: Monitor `CURRENT`, documentação reconstruída e revisão de `PROJECT.md` sem impacto material: mensagens, argumentos, finalidade e capacidades foram preservados.
  - [x] **IMPROVE**: Quebras estruturais foram preferidas; a única string longa do prompt usa continuação explícita para preservar o texto sem concatenação ambígua.
  <!-- specsfy:evidence {"task":"T020","refs":["US-001","FR-001","FR-002","AC-003","AC-004","AC-005"],"files":["chat.py","search.py","src/validation.py","upsert_from_chunks.py"],"commands":[{"run":"uv run ruff check --select E501 chat.py search.py src/validation.py upsert_from_chunks.py","exit":0},{"run":"uv run pytest tests/test_client_neutrality.py tests/test_validation.py tests/test_validation_boundaries.py","exit":0}]} -->

- [x] T021 [CODE] [US-001] Preservar o alcance da guarda em tests/test_client_neutrality.py e organizar imports de tests/test_ci_gates.py — Refs: US-001, FR-001, FR-002, AC-002, AC-003, AC-005 — Depends: T002, T003, T005, T018
  - [x] **PREP**: Três ferramentas e oito identificadores foram salvos como baseline; `docs/` foi reconstruído e o novo arquivo TDD mostrou somente um `I001` próprio.
  - [x] **EXECUTE**: As onze linhas foram reformatadas sem remover os três caminhos nem os oito termos, e o Ruff organizou mecanicamente os imports do teste novo.
  - [x] **VERIFY**: `uv run ruff check` passou no repositório inteiro; T005 passou e os 14 casos de neutralidade permaneceram verdes.
  - [x] **VISUAL**: Não aplicável — a tarefa altera guardas estáticas Pytest, sem interface.
  - [x] **EVIDENCE**: GREEN registrado; documentação reconstruída, monitor `CURRENT` e `PROJECT.md` revisado sem impacto material porque somente testes e forma foram alterados.
  - [x] **IMPROVE**: Listas e chamadas extensas ficaram estruturadas em blocos legíveis, preservando exatamente o conjunto protegido.
  <!-- specsfy:evidence {"task":"T021","refs":["US-001","FR-001","FR-002","AC-002","AC-003","AC-005"],"files":["tests/test_client_neutrality.py","tests/test_ci_gates.py"],"commands":[{"run":"uv run ruff check","exit":0},{"run":"uv run pytest tests/test_client_neutrality.py","exit":0},{"run":"uv run pytest tests/test_ci_gates.py -k line_length","exit":0}]} -->

**Checkpoint**: US-001 é demonstrável com `uv run ruff check` sem achados e
a regressão dos módulos afetados verde.

#### Fase 3 — US-002 Esteira automática (P1)

**Objetivo**: executar os mesmos comandos locais em push e pull request, sem
segredos e com resultados legíveis.
**Teste independente**: os casos AC-006–AC-009 e AC-014 passam por inspeção de
`.github/workflows/ci.yml`.

- [x] T022 [CODE] [US-002] Criar o workflow de integração contínua em .github/workflows/ci.yml — Refs: US-002, FR-003, NFR-001, NFR-002, AC-006, AC-007, AC-008, AC-009, AC-014 — Depends: T006, T007, T008, T009, T014, T018, T019, T020, T021
  - [x] **PREP**: Cinco REDs confirmados, `docs/` reconstruído, Python 3.12 e uv 0.11.16 conferidos; ações oficiais e SHAs atuais verificados na documentação do GitHub e da Astral.
  - [x] **EXECUTE**: Workflow criado com `push`, `pull_request`, Python 3.12, uv 0.11.16, dependências travadas e passos separados de Ruff e Pytest; ações fixadas por SHA.
  - [x] **VERIFY**: Cinco casos focais passaram e o YAML foi carregado com gatilhos e `permissions.contents = read`.
  - [x] **VISUAL**: Não aplicável — o arquivo configura automação externa; a legibilidade foi conferida pelos nomes textuais dos passos.
  - [x] **EVIDENCE**: GREEN local registrado; documentação reconstruída, monitor `CURRENT` e `PROJECT.md` revisado sem impacto na finalidade do produto; execução remota segue para T024.
  - [x] **IMPROVE**: Aplicadas permissões mínimas, `persist-credentials: false` e cancelamento de runs obsoletos por concorrência.
  <!-- specsfy:evidence {"task":"T022","refs":["US-002","FR-003","NFR-001","NFR-002","AC-006","AC-007","AC-008","AC-009","AC-014"],"files":[".github/workflows/ci.yml"],"commands":[{"run":"uv run pytest tests/test_ci_gates.py -k 'runs_on_push or runs_on_pull or same_named or receive_project_secrets or log_sensitive'","exit":0},{"run":".venv/bin/python -c 'from pathlib import Path; import yaml; data=yaml.load(Path(\".github/workflows/ci.yml\").read_text(), Loader=yaml.BaseLoader); assert \"push\" in data[\"on\"] and \"pull_request\" in data[\"on\"] and data[\"permissions\"][\"contents\"] == \"read\"'","exit":0}]} -->

**Checkpoint**: US-002 é demonstrável localmente pelos testes de contrato e,
após publicação autorizada, por uma execução verde associada ao commit e ao PR.

#### Fase 4 — US-003 Barreira de merge verificável (P2)

**Objetivo**: transformar o resultado da esteira em requisito de merge e deixar
o procedimento auditável sem introduzir credenciais na suíte.
**Teste independente**: um PR reprovado fica bloqueado e um PR aprovado fica
liberado, com procedimento, responsável e evidências registrados na spec.

- [x] T023 [DOC] [US-003] Publicar o procedimento da verificação obrigatória em docs/testing.md — Refs: US-003, FR-004, NFR-001, AC-010, AC-011, AC-012 — Depends: T010, T011, T012, T022
  - [x] **PREP**: REDs T010–T012 confirmados; `Ruff and Pytest` foi fixado como nome estável do job e da verificação obrigatória.
  - [x] **EXECUTE**: Publicado o procedimento para configurar a regra em `main`, provocar reprovação controlada, confirmar bloqueio e reconfirmar liberação após GREEN.
  - [x] **VERIFY**: O caso de AC-012 passou; o roteiro identifica menu, branch, nome do check, ensaio vermelho/verde e evidência esperada.
  - [x] **VISUAL**: Não aplicável — a entrega é documentação Markdown; hierarquia, sequência e legibilidade textual foram revisadas.
  - [x] **EVIDENCE**: `uv run pytest tests/test_ci_gates.py -k branch_protection_procedure` → 1 passed, 16 deselected; seção 12 atualizada.
  - [x] **IMPROVE**: O procedimento elimina dependência de memória, não conclui o merge e não deixa o arquivo temporário de prova na árvore final.

- [x] T024 [OPS] [US-003] Configurar e comprovar a barreira no GitHub, registrando o resultado em specs/in-progress/0007-ruff-e-esteira-de-integracao-continua/spec.md — Refs: US-003, FR-004, NFR-001, AC-010, AC-011, AC-012 — Depends: T023
  - [x] **PREP**: Acesso administrativo confirmado via `gh auth status` (owner `marciohernandez`), autorização recebida do responsável pelo projeto e nome exato do check confirmado em `.github/workflows/ci.yml`: `Ruff and Pytest`.
  - [x] **EXECUTE**: Branch `feat/finalizar-rag-ingestion-pipeline` publicada e PR #2 aberto para `main`; ruleset `Require CI on main` (id 22214769) criado via API exigindo `Ruff and Pytest`, sem bypass (`current_user_can_bypass: never`). Ensaio reprovado com `_ci_barrier_probe.py` (import não usado, commit 4f9be0e) e ensaio aprovado removendo o arquivo. Nenhum segredo foi adicionado ao repositório ou ao workflow.
  - [x] **VERIFY**: `gh pr view 2` retornou `mergeStateStatus=BLOCKED` com o check `Ruff and Pytest` em `FAILURE` (runs 33789500214 e 33789504941); `gh pr merge 2 --squash` foi recusado pelo GitHub com "the base branch policy prohibits the merge". Após remover o arquivo de prova, `uv run ruff check` e `uv run pytest` ficaram verdes (238 casos) e o check `Ruff and Pytest` do PR passou a `SUCCESS`, liberando o `mergeStateStatus`.
  - [x] **VISUAL**: Não aplicável — a interface observada pertence ao GitHub (Settings → Rules → Rulesets e o PR #2); os estados textuais do check e do `mergeStateStatus` foram conferidos via `gh api`/`gh pr view`, sem tela própria deste repositório.
  - [x] **EVIDENCE**: AC-010 e AC-011 registrados nas linhas `Manual` da seção 12 e na tabela RED-GREEN-REFACTOR da seção 11, com PR, commits, runs, data (2026-09-03) e responsável (`marciohernandez`). Detalhe do ensaio no Gate do Ato III (seção 13).
  - [x] **IMPROVE**: Ambiguidade encontrada — o runner do GitHub não possui `config.yaml` (gitignorado), quebrando `test_ac_007`/`test_ac_008` em toda execução remota. Corrigida no workflow (`.github/workflows/ci.yml`, passo "Prepare local configuration") e documentada em `docs/testing.md`.

**Checkpoint**: US-003 é demonstrável por uma regra de proteção ativa e pelas
duas evidências manuais registradas.

#### Fase final — Contexto, pendência anterior e qualidade

- [x] T025 [DOC] [US-001] Registrar o fechamento da pendência em specs/completed/0006-gate-qualidade-chunks-metadados/spec.md — Refs: US-001, FR-005, AC-015 — Depends: T015, T018, T019, T020, T021
  - [x] **PREP**: `uv run ruff check` verde confirmado e o único item aberto da seção 18 da SPEC-0006 localizado.
  - [x] **EXECUTE**: O item foi marcado como cumprido em 2026-09-03 pela SPEC-0007; o histórico da pendência foi preservado e nenhum status ou gate anterior foi alterado.
  - [x] **VERIFY**: AC-015 passou e o validador da SPEC-0006 retornou `READY`, mantendo `Status: Complete` e os três gates `Passed`.
  - [x] **VISUAL**: Não aplicável — a tarefa atualiza fonte normativa Markdown, sem interface.
  - [x] **EVIDENCE**: `uv run pytest tests/test_ci_gates.py -k previous_spec` → 1 passed; `validate_spec.mjs` da SPEC-0006 → `READY`; seção 12 atualizada.
  - [x] **IMPROVE**: O item conserva o resultado parcial original como histórico e separa dele a resolução posterior, datada e vinculada.

- [x] T026 [DOC] [US-001] Atualizar contexto e documentação em .specsfy/STACK.md, PROJECT.md e docs/testing.md — Refs: US-001, FR-005, NFR-001, NFR-003, AC-016, AC-017 — Depends: T016, T017, T018, T022, T023, T025
  - [x] **PREP**: Monitor executado; `$specsfy-aux-stack` carregada e declarações de Ruff, CI, comandos e versões comparadas com `pyproject.toml`, `uv.lock` e o workflow.
  - [x] **EXECUTE**: `.specsfy/STACK.md` registra Ruff e Actions; `PROJECT.md` registra os gates reproduzíveis e `docs/testing.md` publica comandos e procedimento; documentação reconstruída.
  - [x] **VERIFY**: AC-016 e AC-017 passaram; monitor `CURRENT` e check do documentador concluíram sem pendência.
  - [x] **VISUAL**: Não aplicável — a tarefa atualiza documentação técnica sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_ci_gates.py -k 'testing_documentation or stack_records'` → 2 passed; comandos de contexto registrados nesta tarefa e nas seções 11–12.
  - [x] **IMPROVE**: Declarações obsoletas de Ruff efêmero e CI inexistente foram removidas; detalhes operacionais permanecem somente em `docs/testing.md`.

- [ ] T027 [TEST] Executar regressão, rastreabilidade e aceite em tests/test_ci_gates.py — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017 — Depends: T022, T024, T025, T026
  - [ ] **PREP**: Confirmar todas as dependências, inventariar os casos e executar o monitor antes do fechamento.
  - [ ] **EXECUTE**: Executar `uv run ruff check`, o arquivo focal, a suíte Pytest completa, rastreabilidade e verificadores de aceite e evidência.
  - [ ] **VERIFY**: Confirmar zero achado, regressão verde, 17 AC com resultado e todos os IDs cobertos.
  - [ ] **VISUAL**: Não aplicável — a fatia não possui interface construída; conferir a legibilidade textual dos passos e da documentação.
  - [ ] **EVIDENCE**: Registrar contagens, comandos, códigos de saída, checks remotos e resultado dos gates nas seções 11–13.
  - [ ] **IMPROVE**: Fazer revisão final dos riscos e registrar melhoria concreta ou ausência justificada.

### 15. Ordem de execução

- Caminho crítico: T001–T017 → T018 → T019/T020/T021 → T022 → T023 → T024 → T025/T026 → T027.
- Tarefas paralelas: os desenhos T001–T017 são conceitualmente independentes, mas compartilham `tests/test_ci_gates.py` e serão materializados em sequência. Depois de T018, T019, T020 e T021 não compartilham arquivos entre si e podem ser executadas em paralelo; T025 pode avançar após o lint local verde, sem aguardar a configuração remota T024.
- Estratégia de MVP: T001–T021 concluem US-001 como incremento isolado e reproduzível. T022 acrescenta US-002 sem depender de acesso administrativo. T023–T024 completam US-003 e o gate remoto; T025–T027 fecham a rastreabilidade e a documentação da entrega inteira.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Acesso administrativo ao repositório no GitHub, necessário para configurar a barreira de merge de `FR-004`. Sem ele, o workflow pode ser entregue e a barreira não.
- SPEC-0006, concluída: é a fonte normativa onde o item pendente será registrado como cumprido.
- Nenhuma dependência funcional pendente: as seis fatias que o item de origem aguardava foram entregues.

#### Riscos

- As correções de largura de linha tocam `tests/test_client_neutrality.py`, uma guarda estática cujas listas definem o que ela varre → quebrar uma linha não pode remover identificador do conjunto; `AC-005` e `PR-005` existem para verificar isso.
- Uma configuração declarada com `select` em vez de `extend-select` desativaria silenciosamente o conjunto padrão e deixaria de ver os três defeitos semânticos → `AC-002` transforma essa distinção em verificação executável.
- A barreira de merge não vive no repositório, não aparece em revisão de código e pode ser desfeita sem deixar rastro no histórico → `FR-004` exige passo próprio e forma declarada de conferência.
- Uma atualização do Ruff pode introduzir regra nova e reprovar um push sem mudança de código → a versão é fixada por `PR-006` e `AC-013`.
- O nome da verificação publicada pela esteira é o identificador que a barreira exige; renomear o passo quebraria a barreira sem quebrar o workflow → registrado como contrato na seção 10.
- Os três achados semânticos estão em código entregue pela SPEC-0006, cujos gates já passaram → as correções são de forma e não podem alterar o comportamento provado por `tests/test_quality_gate.py`.

#### Suposições

- **S-001**: a plataforma é o GitHub Actions. Sustentada por evidência, não por declaração verbal: o remoto do repositório é `github.com/marciohernandez/rag-ingestion-pipeline`. Default reversível: outra plataforma exigiria trocar apenas o arquivo de workflow, preservando comandos, configuração e correções.
- **S-002**: a esteira usa Python 3.12 e `uv`, em versão única e sem matriz, coerentes com `.python-version`, `requires-python` e os comandos publicados na documentação.
- **S-003**: "branch de fase" significa qualquer branch que não seja a principal, conforme a regra de branch por fase registrada em `.specsfy/RULES.md`. A esteira aciona-se em push para qualquer branch e em pull request.
- **S-004**: a versão do Ruff a fixar é a 0.16.5, observada durante o refinamento e base de toda a medição registrada na seção 2. Fixar outra versão exigiria repetir a medição, porque o conjunto padrão de regras varia entre versões.
- **S-005**: as ações públicas usadas pelo workflow também têm versão fixada, pela mesma razão de `PR-006`.

### 17. Decisões

- **DEC-001**: o item de origem foi desmembrado em duas fatias. Alternativa considerada: manter Ruff, esteira e contrato de handoff juntos. Trade-off: o contrato de handoff é documento de interface entre repositórios e depende de decisões do projeto-mãe; mantê-lo junto atrasaria a barreira de qualidade, que já tem uma entrega esperando por ela. A fatia restante virou o `BACKLOG-0011`.
- **DEC-002**: medir o volume de violações antes de escolher o conjunto de regras, por execução efêmera que não altera o projeto. Alternativa: escolher pelo hábito e corrigir o que aparecesse. Trade-off: a medição mostrou que a diferença entre configurações plausíveis ia de três a cento e vinte e quatro achados, o que teria transformado uma escolha casual em uma semana de mutirão.
- **DEC-003**: adotar `extend-select = ["E501", "I", "UP", "B", "SIM"]` com `line-length = 100`. Alternativas: manter só o padrão, com três achados e sem controle de largura nem bugbear; usar `select` com as mesmas famílias, com dezoito achados mas perdendo o conjunto padrão; usar largura 110, com oito achados. Trade-off: `extend-select` é a única forma de cobrir os dois conjuntos, e dezenove correções em código já testado é trabalho de uma sessão. A recomendação inicial usava `select` e foi corrigida quando a medição expôs que os conjuntos eram parcialmente disjuntos.
- **DEC-004**: a reprovação bloqueia o merge, e a esteira aciona-se tanto em push quanto em pull request. Alternativas: apenas informar; bloquear só na branch principal; adiar a decisão de bloqueio. Trade-off: a regra confirmada em `.specsfy/RULES.md` exige a esteira verde como condição de conclusão do marco, e um resultado ignorável não cumpre isso.
- **DEC-005**: a versão do Ruff e das ações do workflow é fixada. Alternativa: acompanhar a versão mais recente. Trade-off: acompanhar traria regras novas sem aviso e reprovaria pushes sem mudança de código; fixar exige atualização deliberada, que é o comportamento desejado para um gate.
- **DEC-006**: os cenários de bloqueio de merge são verificados manualmente, com procedimento, responsável e evidência registrados. Alternativa: tentar automatizar a conferência da configuração pela API do GitHub. Trade-off: automatizar exigiria credencial na suíte, contradizendo `NFR-002` e a garantia de que nenhum teste depende de rede.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Os dezessete cenários `AC` têm resultado registrado, incluindo os dois verificados manualmente com procedimento, responsável e evidência.
- [ ] Cada história, requisito funcional e requisito não funcional possui pelo menos três cenários e evidência.
- [ ] O Ruff está declarado no grupo de desenvolvimento com versão fixada e `uv run ruff check` executa.
- [ ] A configuração usa `extend-select` e não `select`, comprovado por caso que verifica a ausência da chave substitutiva.
- [ ] `uv run ruff check` devolve zero achado sobre o repositório inteiro.
- [ ] Os três achados semânticos em `quality.py` e `src/quality.py` foram corrigidos sem alterar o comportamento provado por `tests/test_quality_gate.py`.
- [ ] As dezesseis linhas longas foram quebradas sem reduzir o alcance de nenhuma guarda estática.
- [ ] `.github/workflows/ci.yml` existe, aciona-se em push e pull request e executa os mesmos comandos publicados na documentação.
- [ ] A esteira executa sem nenhum segredo configurado e seu registro não expõe valor sensível.
- [ ] A verificação está configurada como obrigatória para merge, com a conferência registrada.
- [ ] `uv run pytest` está verde, sem regressão nos casos existentes.
- [ ] Nenhuma dependência de execução foi acrescentada; o Ruff está apenas no grupo de desenvolvimento.
- [ ] `docs/testing.md` deixou de declarar o Ruff ausente e publica o comando e a versão fixada.
- [ ] `.specsfy/STACK.md` registra a esteira e a ferramenta de lint.
- [ ] A fonte normativa da SPEC-0006 registra que o item pendente da sua Definition of Done foi cumprido.
- [ ] `PROJECT.md` foi revisto; se a revisão concluir que não há impacto material sobre finalidade ou capacidades do produto, a justificativa fica registrada na evidência da tarefa.
- [ ] A documentação foi reconstruída com o monitor de contexto em `CURRENT`.

## Effort history

- 2026-09-03: 1 → 4. Promoção do BACKLOG-0007, já desmembrado. O volume é pequeno e conhecido, mas a fatia toca uma guarda estática cujo alcance não pode ser reduzido, depende de uma configuração administrativa fora do controle de versão e envolve uma escolha de configuração capaz de desativar silenciosamente regras hoje ativas.
