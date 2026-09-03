# Especificação integrada: Instalar o Ruff e criar a esteira de integração contínua

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0007 |
| Slug | 0007-ruff-e-esteira-de-integracao-continua |
| Status | Defined |
| Effort | 4 |
| Effort updated at | 2026-09-03 |
| Effort rationale | Recalibrado de 1 para 4 na promoção. O volume é pequeno e conhecido: uma dependência, um bloco de configuração, dezenove correções já localizadas e um arquivo de workflow. O que sustenta a nota não é o volume, e sim três pontos de risco. As correções tocam arquivos pré-existentes, incluindo uma guarda estática de neutralidade cujo texto não pode perder alcance ao ser quebrado em linhas. O bloqueio de merge é configuração fora do repositório, não versionada e não revisável em código. E uma configuração de linter mal formulada pode desativar silenciosamente a família de regras que hoje protege o repositório, como a própria descoberta demonstrou. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Pending |
| Delivery Gate | Pending |
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
| US-001, FR-001, NFR-003, AC-001 | AC-001 na seção 6 | caso de Ruff declarado no grupo de desenvolvimento em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| US-001, FR-001, AC-002 | AC-002 na seção 6 | caso de `extend-select` com ausência de `select` em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| US-001, FR-002, AC-003 | AC-003 na seção 6 | caso de execução real sem achado em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| US-001, FR-002, AC-004 | AC-004 na seção 6 | caso de ausência dos três achados semânticos em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| FR-001, FR-002, AC-005 | AC-005 na seção 6 | caso de preservação do alcance da guarda estática em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| US-002, FR-003, AC-006 | AC-006 na seção 6 | caso de gatilho de push no workflow em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| US-002, FR-003, AC-007 | AC-007 na seção 6 | caso de gatilho de pull request no workflow em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| US-002, FR-003, NFR-001, NFR-002, AC-008 | AC-008 na seção 6 | caso de equivalência entre comandos locais e da esteira em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| US-002, FR-003, NFR-002, AC-009 | AC-009 na seção 6 | caso de ausência de segredo no workflow em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| US-003, FR-004, AC-010 | AC-010 na seção 6 | verificação manual registrada, com procedimento, responsável e evidência | Pending | Pending | Pending |
| US-003, FR-004, AC-011 | AC-011 na seção 6 | verificação manual registrada, com procedimento, responsável e evidência | Pending | Pending | Pending |
| US-003, FR-004, NFR-001, AC-012 | AC-012 na seção 6 | caso de existência do passo declarado de conferência da barreira em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| FR-001, NFR-003, AC-013 | AC-013 na seção 6 | caso de versão fixada do Ruff em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| FR-003, NFR-002, AC-014 | AC-014 na seção 6 | caso de ausência de valor sensível nos passos do workflow em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| US-001, FR-005, AC-015 | AC-015 na seção 6 | caso de registro do item cumprido na spec anterior em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| FR-005, NFR-001, AC-016 | AC-016 na seção 6 | caso de documentação de testes atualizada em `tests/test_ci_gates.py` | Pending | Pending | Pending |
| FR-005, NFR-003, AC-017 | AC-017 na seção 6 | caso de fontes de contexto atualizadas em `tests/test_ci_gates.py` | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

Regressão completa da fatia: `uv run pytest`. Verificação estática: `uv run ruff check`.

| Requisito | Cenário BDD | Nível | Arquivo e comando focal | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-001 | AC-002 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-001 | AC-005 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-001 | AC-013 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-002 | AC-003 | Integração | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-002 | AC-004 | Integração | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-002 | AC-005 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-003 | AC-006 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-003 | AC-007 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-003 | AC-008 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-003 | AC-009 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-003 | AC-014 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-004 | AC-010 | Manual | verificação no repositório do GitHub, com evidência registrada | Pending |
| FR-004 | AC-011 | Manual | verificação no repositório do GitHub, com evidência registrada | Pending |
| FR-004 | AC-012 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-005 | AC-015 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-005 | AC-016 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| FR-005 | AC-017 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| NFR-001 | AC-008 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| NFR-001 | AC-012 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| NFR-001 | AC-016 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| NFR-002 | AC-008 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| NFR-002 | AC-009 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| NFR-002 | AC-014 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| NFR-003 | AC-001 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| NFR-003 | AC-013 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |
| NFR-003 | AC-017 | Unidade | `tests/test_ci_gates.py` — `uv run pytest tests/test_ci_gates.py` | Pending |

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

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0007-ruff-e-esteira-de-integracao-continua/spec.md`
- **Achados**: Pending.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0007-ruff-e-esteira-de-integracao-continua/spec.md .`
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

#### Fase 1 — Decomposição pendente

A decomposição em tarefas pertence a `$specsfy-05-tasks` e será registrada nesta mesma seção depois que o `Definition Gate` estiver `Passed`. Nenhuma tarefa foi planejada ainda; a seção permanece aberta e nenhuma entrega pode começar por ela neste estado.

### 15. Ordem de execução

- Caminho crítico previsto: RED das conferências de configuração → dependência e configuração do Ruff → correção dos dezenove achados → RED das conferências do workflow → arquivo de workflow → configuração da barreira de merge → documentação e fechamento da pendência da SPEC-0006. A ordem final é responsabilidade de `$specsfy-05-tasks`.
- Tarefas paralelas: a definir no planejamento. As correções de largura de linha tocam arquivos distintos entre si e admitem paralelismo; as correções semânticas em `src/quality.py` compartilham arquivo e não.
- Estratégia de MVP: US-001 isolada já entrega valor — a verificação passa a existir e o código fica limpo — mesmo antes da esteira. Um corte de escopo preserva US-001 e US-002 e adia US-003, que é a única que depende de acesso administrativo.

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
