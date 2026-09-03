# Especificação integrada: Fronteira interna entre o pipeline e o backend de aplicação

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0008 |
| Slug | 0008-fronteira-interna-pipeline-aplicacao |
| Status | Complete |
| Effort | 7 |
| Effort updated at | 2026-09-03 |
| Effort rationale | Move o pacote `src/` inteiro de uma vez, reescreve os imports de nove entrypoints e de 21 arquivos de teste, desenha uma fachada nova e cria um teste estático de fronteira. A execução precisa ser atômica: a suíte de 238 testes é a única prova de que a migração não quebrou comportamento. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-03 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O repositório será estendido com um backend de aplicação — FastAPI, execução
assíncrona e persistência — que chamará o pipeline existente. Hoje não há
fronteira alguma entre as duas camadas: qualquer módulo novo pode importar
`src/chunker.py`, `src/indexing.py`, `src/providers/factory.py` ou
`src/config.py` diretamente. Sem contrato declarado, o backend nasceria
acoplado ao interior do pipeline, e cada mudança interna passaria a quebrar a
camada de aplicação.

O problema já foi resolvido uma vez, um nível abaixo: a SPEC-0003 isolou os
SDKs de banco vetorial em `src/providers/` e provou a fronteira com um teste
estático de AST. A camada de aplicação não tem equivalente.

Há ainda três lacunas concretas que impedem o backend de consumir o pipeline
com segurança:

1. não existe um alvo de import estável — quem chamar o pipeline hoje precisa
   conhecer qual módulo interno faz o quê;
2. a configuração é global: `src/config.py` lê `config.yaml` do disco e chama
   `load_dotenv()` no import do módulo, o que impede um backend multi-tenant de
   executar dois projetos com configurações diferentes no mesmo processo;
3. as contagens de `previstos`, `inseridos`, `mantidos` e `removidos` são
   publicadas para o operador, mas não há garantia de que cheguem ao chamador
   como valor de retorno — o backend precisa persisti-las e exibi-las.

#### Resultado desejado

O backend de aplicação é escrito contra uma fachada explícita e estável, com
configuração recebida por parâmetro, dentro de uma fronteira física de
diretórios que uma violação de import faz falhar no CI. Quem for implementar
`src/app/` encontra em documentação a fachada, os entrypoints, a configuração
exigida, os limites e as dívidas bloqueantes, sem precisar ler o interior de
`src/pipeline/`.

Os comandos de operação existentes continuam funcionando exatamente como antes.

#### Métricas de sucesso

- A suíte completa permanece verde após a migração, sem redução do número de
  testes que passam (baseline: 238 aprovados).
- `uv run ruff check .` permanece sem aviso.
- Zero imports de módulo interno de `src/pipeline/` a partir de `src/app/`,
  verificado por teste estático a cada push.
- Os cinco comandos de operação da raiz executam com a mesma invocação de
  antes da migração.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: qual padrão de fronteira já é usado e provado neste repositório? →
  `tests/test_provider_boundaries.py` percorre a AST de cada módulo Python fora
  de `tests/` e de `src/providers/` e falha quando encontra import de SDK de
  vector store ou classe de embeddings, com exceções nomeadas explicitamente.
  Esta spec replica o mesmo mecanismo um nível acima, na fronteira
  `src/app/` → `src/pipeline/`.
- **R-002**: onde a configuração vira estado global? → `src/config.py:13` chama
  `load_dotenv()` no corpo do módulo, fora de qualquer função. Qualquer import
  de `src.config` injeta o `.env` da máquina no processo inteiro. Esse
  comportamento é a dívida BACKLOG-0012 e é o motivo de a regra de configuração
  injetada precisar de prova própria nesta spec.
- **R-003**: quais entrypoints existem hoje na raiz? → `pipeline.py`,
  `search.py`, `chat.py`, `validate.py`, `upsert_from_chunks.py`, além de
  `main.py`, `demo_rag.py`, `inspect_chunks.py` e `quality.py`. Os cinco
  primeiros são os comandos de operação declarados em `docs/application.md`.

#### Fontes e contexto consultados

- `specs/backlog/0011-contrato-handoff-projeto-mae.md`: brief refinado que
  originou esta spec, com as oito decisões confirmadas.
- `specs/completed/0003-modularizar-providers-factory-adapter/spec.md`:
  precedente do padrão de contrato neutro, factory e teste estático de AST.
- `tests/test_provider_boundaries.py`: implementação de referência da varredura
  de AST.
- `src/config.py`, `src/indexing.py`, `src/validation.py`, `src/safety.py`:
  superfícies que a fachada precisa cobrir.
- `docs/application.md` e `docs/architecture.md`: inventário das superfícies e
  fronteiras atuais.
- `PROJECT.md` e `.specsfy/STACK.md`: capacidades, limites e stack confirmados.

#### Documentação consultada

- Nenhuma documentação externa. Todas as conclusões vêm do código e das specs
  locais.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo. Nenhuma fonte fora do repositório foi consultada,
  portanto não há cópia a preservar em `research/`.

#### Dúvidas respondidas

- **Q**: o contrato ainda é um handoff entre repositórios? → **A**: não. Os
  commits `e2d8b1b` e `0fe7b1b` consolidaram `rag-ingestion-pipeline` e
  `rag-pipeline` em um único repositório. O contrato passa a ser a fronteira
  interna entre pipeline e backend de aplicação.
- **Q**: onde o backend vai morar? → **A**: em `src/app/`, com o código atual
  movido para `src/pipeline/`, mantendo um único pacote Python e uma única
  configuração de projeto.
- **Q**: os CLIs mudam? → **A**: não. Continuam na raiz, com a mesma invocação,
  passando a importar de `src/pipeline/`.
- **Q**: qual a forma da interface estável? → **A**: uma fachada nova de casos
  de uso, não a reexportação dos módulos existentes.
- **Q**: como a configuração chega à fachada? → **A**: por parâmetro, já
  resolvida. Ler `config.yaml` fica restrito aos entrypoints da raiz.
- **Q**: as dívidas conhecidas bloqueiam esta spec? → **A**: elas bloqueiam a
  implementação de `src/app/`, não esta fronteira. BACKLOG-0012 e BACKLOG-0013
  podem ser entregues em paralelo.

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Mover o conteúdo atual de `src/` para `src/pipeline/`, preservando os módulos
  existentes e o histórico do Git.
- Criar `src/app/` como destino declarado do backend de aplicação, sem
  implementar API, tarefas ou persistência.
- Criar a fachada de casos de uso do pipeline, com operações de alto nível.
- Fazer a fachada receber a configuração já resolvida por parâmetro.
- Ajustar os entrypoints da raiz para importar de `src/pipeline/`, resolver a
  configuração e chamar a fachada, sem mudar sua invocação.
- Criar o teste estático de fronteira que reprova import de módulo interno de
  `src/pipeline/` a partir de `src/app/`.
- Registrar o contrato em documentação: fachada, entrypoints, configuração
  exigida, limites e dívidas bloqueantes.

#### Fora de escopo

- Implementar FastAPI, rotas HTTP, execução assíncrona, persistência,
  autenticação, tenant, projeto ou papéis — fatia 2 do BACKLOG-0008.
- Qualquer tela ou frontend — fatia 3 do BACKLOG-0008.
- Reescrever a lógica interna do pipeline: chunking, embeddings, indexação,
  qualidade, validação e política de segurança permanecem como estão.
- Mudar o contrato de `config.yaml` percebido pelo operador.
- Resolver as duas dívidas bloqueantes: BACKLOG-0012 e BACKLOG-0013 têm specs
  próprias.
- Remover ou renomear comandos de operação existentes.

#### Atores

- **Implementador do backend de aplicação**: escreve `src/app/`; precisa de um
  alvo de import estável, configuração injetável e limites declarados.
- **Operador do pipeline**: Marcio, hoje; executa os comandos da raiz e não
  pode ser interrompido pela reorganização.
- **Mantenedor do repositório**: revisa mudanças; precisa que uma violação de
  fronteira falhe automaticamente, não em leitura manual de diff.

### 4. Princípios e restrições do projeto

- **PR-001**: a fronteira é verificada por teste estático executado na esteira
  de integração contínua, no mesmo padrão já estabelecido pela SPEC-0003; a
  disciplina não depende de revisão humana.
- **PR-002**: a migração de diretórios preserva o histórico do Git e não
  reescreve lógica; mover e reescrever são mudanças distintas e não podem ser
  misturadas na mesma entrega.
- **PR-003**: a política fail-closed de `src/safety.py` permanece intacta e
  continua sendo aplicada antes de qualquer mutação remota.
- **PR-004**: nenhum segredo transita por assinatura de caso de uso; a
  resolução de credencial permanece onde está hoje.
- **PR-005**: os comandos de operação existentes são contrato com o operador;
  esta entrega não pode alterar sua invocação.
- **PR-006**: uma dívida declarada bloqueante não pode ser contornada por
  decisão local durante a implementação do backend.

### 5. Histórias de usuário

#### US-001 — Consumir o pipeline por uma fachada estável (P1)

Como implementador do backend de aplicação, quero uma fachada de casos de uso
com configuração injetada, para escrever `src/app/` sem depender do interior do
pipeline nem de estado global.

**Por que P1**: sem ela, a fatia 2 do BACKLOG-0008 começa acoplada e o
retrabalho cresce a cada arquivo novo.
**Teste independente**: chamar a fachada com uma configuração montada em
memória, sem `config.yaml` no disco, e obter a execução e suas contagens.
**Requisitos**: FR-003, FR-004

#### US-002 — Reorganizar sem interromper a operação (P1)

Como operador do pipeline, quero que os comandos da raiz continuem funcionando
exatamente como hoje, para que a reorganização de diretórios não interrompa meu
trabalho.

**Por que P1**: a operação é o único uso real do repositório hoje; quebrá-la
troca um problema futuro por um problema presente.
**Teste independente**: executar cada comando de operação antes e depois da
migração e comparar invocação e resultado.
**Requisitos**: FR-001, FR-005

#### US-003 — Impedir a erosão da fronteira (P1)

Como mantenedor do repositório, quero que uma violação de fronteira falhe
automaticamente e que o contrato esteja documentado, para que a separação
sobreviva às próximas entregas sem depender de revisão manual.

**Por que P1**: uma fronteira sem verificação automática degrada em semanas; o
repositório já provou o padrão contrário na SPEC-0003.
**Teste independente**: introduzir um import proibido em um arquivo de
`src/app/` e observar a suíte reprovar identificando arquivo e módulo.
**Requisitos**: FR-002, FR-006, FR-007

### 6. Cenários BDD de aceite

#### AC-001 — Migração de diretórios preserva a suíte

**Cobre**: US-002, FR-001, FR-002, NFR-001

```gherkin
@US-002 @FR-001 @FR-002 @NFR-001 @AC-001
Feature: Reorganização do pacote sem perda de comportamento

  Scenario: A suíte continua verde após mover o pacote
    Given o pacote atual em src/ com a suíte completa aprovada
    When o conteúdo de src/ é movido para src/pipeline/ e src/app/ é criado
    Then a suíte completa continua aprovada com a mesma contagem de testes
    And o ruff check continua sem aviso
```

#### AC-002 — Comandos de operação inalterados

**Cobre**: US-002, FR-001, FR-005, NFR-001

```gherkin
@US-002 @FR-001 @FR-005 @NFR-001 @AC-002
Feature: Preservação dos comandos do operador

  Scenario: Cada entrypoint da raiz executa como antes
    Given os comandos pipeline.py, search.py, chat.py, validate.py e upsert_from_chunks.py
    When o operador executa cada um deles após a migração
    Then a invocação é idêntica à de antes da migração
    And cada comando resolve a configuração e delega ao pipeline sem erro de import
```

#### AC-003 — Fachada executa com configuração injetada

**Cobre**: US-001, FR-003, FR-004, NFR-004

```gherkin
@US-001 @FR-003 @FR-004 @NFR-004 @AC-003
Feature: Execução do pipeline pela fachada

  Scenario: Executar o pipeline sem config.yaml no disco
    Given uma configuração válida montada em memória
    And nenhum arquivo config.yaml acessível ao processo
    When a fachada é chamada para executar o pipeline sobre uma base
    Then a execução acontece usando somente a configuração recebida
    And o retorno da chamada expõe as contagens da execução
```

#### AC-004 — Fachada recusa configuração inválida

**Cobre**: US-001, FR-003, FR-004, NFR-002

```gherkin
@US-001 @FR-003 @FR-004 @NFR-002 @AC-004
Feature: Falha explícita antes de efeito remoto

  Scenario: Chamada com configuração ausente ou incompleta
    Given uma configuração ausente ou sem as chaves exigidas
    When a fachada é chamada
    Then a chamada falha imediatamente com mensagem que identifica a chave faltante
    And nenhum acesso ao banco vetorial ou ao provider de embeddings é realizado
    And nenhum valor de credencial aparece na mensagem de erro
```

#### AC-005 — Fronteira reprova import interno

**Cobre**: US-003, FR-002, FR-006, NFR-001

```gherkin
@US-003 @FR-002 @FR-006 @NFR-001 @AC-005
Feature: Verificação estática da fronteira

  Scenario: Um módulo de src/app/ importa módulo interno do pipeline
    Given um arquivo em src/app/ que importa src.pipeline.chunker
    When a suíte é executada
    Then o teste de fronteira reprova
    And a mensagem identifica o arquivo e o módulo importado

  Scenario: Um módulo de src/pipeline/ importa a camada de aplicação
    Given um arquivo em src/pipeline/ que importa src.app
    When a suíte é executada
    Then o teste de fronteira reprova por inversão de dependência
    And a mensagem identifica o arquivo e o módulo importado
```

#### AC-006 — Fronteira aceita import da fachada

**Cobre**: US-003, FR-003, FR-006

```gherkin
@US-003 @FR-003 @FR-006 @AC-006
Feature: Caminho autorizado da fronteira

  Scenario: Um módulo de src/app/ importa apenas a fachada
    Given um arquivo em src/app/ que importa somente a fachada de src/pipeline/
    When a suíte é executada
    Then o teste de fronteira aprova
    And nenhum outro alvo de import dentro de src/pipeline/ é considerado autorizado
```

#### AC-007 — Fachada não depende de estado global

**Cobre**: US-001, FR-004, NFR-002, NFR-003

```gherkin
@US-001 @FR-004 @NFR-002 @NFR-003 @AC-007
Feature: Ausência de estado global na fachada

  Scenario: Execução isolada do disco e de configuração global
    Given nenhum config.yaml acessível ao processo
    When a fachada recebe a configuração não sensível completa por parâmetro
    Then a execução não lê arquivo de configuração
    And a fachada não consulta variável de ambiente para configuração não sensível
    And duas chamadas com configurações não sensíveis distintas não interferem uma na outra
    And a resolução de credencial permanece nos providers, fora da assinatura da fachada
```

#### AC-008 — Contagens disponíveis no retorno

**Cobre**: US-001, FR-003, NFR-004

```gherkin
@US-001 @FR-003 @NFR-004 @AC-008
Feature: Contagens consumíveis pelo chamador

  Scenario: Obter previstos, inseridos, mantidos e removidos
    Given uma sincronização concluída pela fachada
    When o chamador inspeciona o retorno da operação
    Then encontra as contagens de previstos, inseridos, mantidos e removidos
    And não precisa ler log ou saída de terminal para obtê-las
```

#### AC-009 — Contrato documentado e completo

**Cobre**: US-003, FR-007, NFR-003

```gherkin
@US-003 @FR-007 @NFR-003 @AC-009
Feature: Contrato legível para quem implementa o backend

  Scenario: Consultar o contrato antes de escrever src/app/
    Given a documentação do contrato publicada no repositório
    When alguém precisa escrever um módulo em src/app/
    Then encontra a fachada, os entrypoints, a configuração exigida e os limites
    And encontra as dívidas bloqueantes declaradas com seus identificadores
```

#### AC-010 — Dívida bloqueante impede a incorporação

**Cobre**: US-003, FR-002, FR-007, NFR-002

```gherkin
@US-003 @FR-002 @FR-007 @NFR-002 @AC-010
Feature: Bloqueio explícito da fatia seguinte

  Scenario: Iniciar src/app/ com dívida bloqueante aberta
    Given BACKLOG-0012 ou BACKLOG-0013 ainda não entregue
    When alguém consulta o contrato para iniciar a implementação de src/app/
    Then o contrato declara a dívida como impedimento com seu identificador
    And registra que prosseguir exige reabrir esta especificação
```

#### AC-011 — Entrypoint resolve e repassa a configuração

**Cobre**: US-002, FR-004, FR-005, NFR-004

```gherkin
@US-002 @FR-004 @FR-005 @NFR-004 @AC-011
Feature: Responsabilidade de configuração no entrypoint

  Scenario: O comando da raiz monta a configuração e chama a fachada
    Given um config.yaml válido no diretório de trabalho
    When o operador executa um comando da raiz
    Then o entrypoint resolve a configuração a partir do arquivo
    And repassa a configuração resolvida para a fachada
    And apresenta ao operador o mesmo resultado de antes da migração
```

#### AC-012 — Regressão completa após a migração

**Cobre**: US-002, FR-001, FR-005, FR-006, NFR-001, NFR-003

```gherkin
@US-002 @FR-001 @FR-005 @FR-006 @NFR-001 @NFR-003 @AC-012
Feature: Prova de que a migração não regrediu

  Scenario: Executar suíte, lint e fronteira em conjunto
    Given a migração concluída e a fachada implementada
    When a suíte completa, o ruff check e o teste de fronteira são executados
    Then todos aprovam
    And o número de testes aprovados não é menor que a baseline registrada
```

#### AC-013 — Documentação acompanha a implementação

**Cobre**: US-003, FR-003, FR-007, NFR-003

```gherkin
@US-003 @FR-003 @FR-007 @NFR-003 @AC-013
Feature: Contrato alinhado ao código entregue

  Scenario: Operação da fachada ausente da documentação
    Given a fachada implementada com suas operações de caso de uso
    When o contrato documentado é comparado com a fachada
    Then toda operação pública da fachada aparece documentada
    And nenhuma operação documentada existe apenas no texto
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve manter o código de pipeline hoje existente em `src/`
  dentro de `src/pipeline/`, preservando os módulos existentes — loader,
  chunker, identity, manifest, quality, validation, safety, indexing,
  providers, exporter, status_gate e config — sem alteração de lógica.
- **FR-002**: O sistema deve possuir o pacote `src/app/` como destino único do
  backend de aplicação, reconhecido pela verificação de fronteira mesmo antes
  de conter implementação.
- **FR-003**: O sistema deve expor, em um módulo único de `src/pipeline/`, uma
  fachada com as operações de caso de uso do pipeline: executar o pipeline
  sobre uma base, sincronizar com o banco vetorial, validar a recuperação e
  consultar a base indexada. Cada operação deve devolver seu resultado ao
  chamador, incluindo as contagens quando aplicável.
- **FR-004**: O sistema deve fazer cada operação da fachada receber a
  **configuração não sensível** já resolvida como parâmetro, sem que a própria
  fachada leia arquivo de configuração, leia variável de ambiente ou dependa de
  estado global do processo. A **resolução de credencial** permanece delegada
  aos providers, como PR-004 declara: ela não transita pela assinatura da
  fachada e não é objeto deste requisito.
- **FR-005**: O sistema deve manter os entrypoints `pipeline.py`, `search.py`,
  `chat.py`, `validate.py` e `upsert_from_chunks.py` na raiz, com a mesma
  invocação de hoje, responsáveis por resolver `config.yaml` e chamar a
  fachada.
- **FR-006**: O sistema deve reprovar, por teste estático de AST executado na
  suíte, a violação da fronteira nos dois sentidos, identificando arquivo e
  módulo: qualquer import feito a partir de `src/app/` para um módulo de
  `src/pipeline/` que não seja a fachada, e qualquer import de `src.app` feito a
  partir de `src/pipeline/`, que inverteria a dependência entre as camadas.
- **FR-007**: O sistema deve publicar o contrato em documentação versionada,
  declarando a fachada e suas operações, os entrypoints, a configuração
  exigida, os limites conhecidos e as dívidas bloqueantes com seus
  identificadores de backlog.

#### Não funcionais

- **NFR-001**: A migração não reduz a cobertura existente: a suíte completa
  permanece aprovada com contagem igual ou maior que a baseline e o
  `ruff check` permanece sem aviso. **Verificação**: `uv run pytest` e
  `uv run ruff check .` antes e depois, com as contagens registradas na
  evidência da tarefa.
- **NFR-002**: Nenhum segredo transita pela assinatura das operações da fachada
  nem aparece em mensagem de erro. **Verificação**: inspeção da assinatura
  pública somada a teste que provoca falha de configuração e confere a ausência
  de valor de credencial na mensagem.
- **NFR-003**: Os limites do contrato são declarados explicitamente: a fachada
  é síncrona e bloqueia a thread chamadora, e a documentação corresponde às
  operações realmente expostas. **Verificação**: inspeção do contrato publicado
  comparada à superfície pública da fachada.
- **NFR-004**: As contagens de `previstos`, `inseridos`, `mantidos` e
  `removidos` são alcançáveis pelo valor de retorno da fachada, não apenas por
  log. **Verificação**: teste que executa uma sincronização com backend dublê e
  lê as quatro contagens no retorno.

#### Erros e casos-limite

- Configuração ausente, incompleta ou inválida na chamada da fachada → falha
  imediata, antes de qualquer acesso remoto, com a chave faltante identificada
  e sem expor valor de credencial.
- Import proibido de `src/app/` para módulo interno de `src/pipeline/` → teste
  de fronteira reprova, nomeando arquivo e módulo; o merge é bloqueado pela
  esteira já existente.
- Entrypoint da raiz quebrado pela migração → a suíte reprova; a entrega não é
  considerada concluída enquanto os cinco comandos não executarem como antes.
- Duas chamadas concorrentes da fachada com configurações distintas → cada uma
  usa apenas a configuração recebida; não há vazamento de uma para a outra.
- `src/app/` vazio no momento da entrega → a verificação de fronteira precisa
  aprovar mesmo sem nenhum arquivo a inspecionar, sem falso positivo.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Aplicação Python 3.12+ gerenciada por `uv`, sem framework web. Testes em
  Pytest (`pyproject.toml` define `testpaths = ["tests"]` e
  `pythonpath = ["."]`), lint com Ruff 0.16.5, esteira GitHub Actions criada
  pela SPEC-0007.
- `src/` contém hoje 12 módulos e o pacote `src/providers/`. A SPEC-0003
  estabeleceu que `src/providers/` é o único lugar onde SDK de banco vetorial
  ou classe de embeddings pode ser importado, com o teste estático
  `tests/test_provider_boundaries.py` provando a regra sobre a AST.
- Nove arquivos `.py` na raiz funcionam como entrypoints; cinco deles são os
  comandos de operação documentados em `docs/application.md`.
- `src/config.py` chama `load_dotenv()` no corpo do módulo (linha 13) e carrega
  `config.yaml`. Esse acoplamento é a dívida BACKLOG-0012 e limita, nesta
  entrega, o que pode ser provado sobre isolamento de ambiente.
- `src/indexing.py` é o serviço de aplicação atual; `src/validation.py`
  concentra a validação somente leitura e já é chamável sem a camada de linha
  de comando; `src/safety.py` mantém a política fail-closed.

#### Arquitetura e módulos

- `src/pipeline/`: o conteúdo atual de `src/` na íntegra, sem alteração de lógica.
  Continua sendo a implementação do pipeline e mantém internamente a fronteira
  de providers já provada pela SPEC-0003.
- `src/pipeline/service.py`: fachada nova. Único alvo de import autorizado a
  partir de `src/app/`. Concentra as operações de caso de uso, cada uma
  recebendo a configuração resolvida e devolvendo um resultado estruturado.
  A fachada compõe os módulos internos; não reexporta seus símbolos.
- `src/app/`: pacote do backend de aplicação. Nesta entrega recebe apenas
  `__init__.py` e a documentação de que é o destino da fatia 2. API, tarefas e
  persistência não pertencem a esta spec.
- `tests/test_application_boundaries.py`: teste estático novo, modelado sobre
  `tests/test_provider_boundaries.py`, com varredura nos dois sentidos. Percorre
  a AST de cada módulo sob `src/app/` e reprova import de `src.pipeline.*` que
  não seja a fachada; percorre a AST de cada módulo sob `src/pipeline/` e
  reprova qualquer import de `src.app`.
- Entrypoints da raiz: mantêm nome, local e invocação; passam a importar de
  `src/pipeline/`, resolvem a configuração e chamam a fachada.

#### Migrations

- Não aplicável. Esta entrega não altera schema, coleção, índice ou qualquer
  estrutura persistida. O banco vetorial não é tocado.

#### Models

- Não aplicável no sentido de ORM. As estruturas de dados relevantes são os
  resultados devolvidos pela fachada, descritos na seção 9.

#### Controllers e casos de uso

| Caso de uso | Entrada | Saída | Arquivo |
| --- | --- | --- | --- |
| Executar o pipeline sobre uma base | configuração resolvida | resultado com documentos, chunks e caminho do manifesto | `src/pipeline/service.py` |
| Sincronizar com o banco vetorial | configuração resolvida, chunks ou caminho do manifesto | resultado com previstos, inseridos, mantidos e removidos | `src/pipeline/service.py` |
| Validar a recuperação | configuração resolvida | veredito e resultado por consulta do gabarito | `src/pipeline/service.py` |
| Consultar a base indexada | configuração resolvida, pergunta, top_k | resultados com conteúdo e metadados de origem | `src/pipeline/service.py` |

- Autorização não se aplica nesta camada: a fachada é uma biblioteca interna.
  Tenant, projeto e papéis pertencem à fatia 2, em `src/app/`.

#### Views e experiência

- Não aplicável. Esta entrega não possui interface para pessoas. Os comandos de
  linha de comando existentes preservam sua saída atual, sem redesenho.

#### Queries e repositórios

- Não aplicável. O acesso ao banco vetorial continua encapsulado em
  `src/pipeline/providers/`, sem mudança de contrato, filtro ou paginação.

#### Jobs e processamento assíncrono

- Não aplicável nesta entrega. A fachada é síncrona e bloqueia a thread
  chamadora; isso é um limite declarado do contrato, não uma omissão. A
  execução assíncrona pertence à fatia 2 do BACKLOG-0008.

#### Estrutura de arquivos

```text
specs/planned/0008-fronteira-interna-pipeline-aplicacao/
  spec.md
src/
  pipeline/
    __init__.py
    service.py
    chunker.py
    config.py
    exporter.py
    identity.py
    indexing.py
    loader.py
    manifest.py
    quality.py
    safety.py
    status_gate.py
    validation.py
    providers/
  app/
    __init__.py
tests/
  test_application_boundaries.py
  test_pipeline_service.py
pipeline.py
search.py
chat.py
validate.py
upsert_from_chunks.py
docs/architecture.md
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Configuração não sensível resolvida | nenhuma; valor passado por parâmetro | conjunto completo de chaves não sensíveis exigidas por operação; imutável durante a chamada; não carrega credencial em nenhum campo | consumida por toda operação da fachada; credencial permanece resolvida nos providers |
| Resultado de execução | nenhuma; valor de retorno | documentos processados, chunks gerados, caminho do manifesto | produzido pela operação de executar o pipeline |
| Resultado de sincronização | nenhuma; valor de retorno | previstos, inseridos, mantidos, removidos | produzido pela operação de sincronizar |
| Resultado de validação | nenhuma; valor de retorno | veredito da base e resultado por consulta do gabarito | produzido pela operação de validar |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Chamada da fachada | não iniciada | recebe configuração completa | em execução | a configuração não muda durante a chamada |
| Chamada da fachada | não iniciada | recebe configuração ausente ou incompleta | recusada | nenhum acesso remoto ocorre; a chave faltante é identificada |
| Chamada da fachada | em execução | conclui | concluída | o retorno carrega o resultado; contagens presentes quando aplicável |

#### Migração e retenção

- Não aplicável. Nenhum dado é persistido, migrado ou descartado por esta
  entrega. Manifesto, `chunks.json` e coleções vetoriais mantêm formato e
  local atuais.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega é uma fronteira interna de
  código consumida por outro código. As únicas superfícies usadas por pessoas
  são os comandos de linha de comando já existentes, cuja invocação e saída
  esta spec preserva sem redesenho. Nenhuma tela, formulário, navegação ou
  estado visual é criado ou alterado.

#### Stack e convenções de interface

- Não aplicável. O repositório não possui camada de interface: `INTERFACE.md` e
  `docs/frontend.md` registram que nenhuma interface para pessoas está
  implementada. Esta entrega não introduz framework de interface, e a stack
  futura prevista para a fatia 3 não é decidida aqui.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável.

#### Menus e navegação principal

- Não aplicável. O operador chega às capacidades pelos comandos de linha de
  comando na raiz do repositório, documentados em `docs/application.md` e
  `GUIA_DE_USO.md`.

#### Formulários e ações

- Não aplicável.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável. O projeto não usa React, Tailwind, shadcn/ui ou ReUI, e esta
  entrega não os introduz.

#### Estados e acessibilidade

- Não aplicável. Sem superfície visual, não há loading, vazio, erro visual,
  foco ou navegação por teclado a definir. As mensagens de erro do pipeline
  continuam sendo texto de terminal, sem alteração.

#### Contrato CRUD

- Não aplicável. A entrega não cria administração de registros.

#### Revisão visual durante o desenvolvimento

- `Não aplicável`. Nenhuma tarefa desta spec altera superfície visual: a
  entrega move módulos, cria uma fachada Python, um teste estático e
  documentação. Cada tarefa registrará esse motivo concreto no item `VISUAL`.

#### APIs expostas

- Nenhuma API HTTP. A superfície pública desta entrega é a fachada Python de
  `src/pipeline/service.py`, com quatro operações de caso de uso, cada uma
  recebendo a configuração resolvida por parâmetro e devolvendo um resultado
  estruturado. A assinatura exata é decidida na implementação e registrada na
  documentação do contrato.

#### APIs externas utilizadas

- Nenhuma nova. Os SDKs de Qdrant, ChromaDB, Pinecone e dos providers de
  embeddings continuam acessados exclusivamente por `src/pipeline/providers/`,
  como a SPEC-0003 estabeleceu.

#### Documentação das APIs consultadas

- Nenhuma. Nenhuma documentação externa foi consultada para esta definição.

#### Eventos e outros contratos

- Contrato de fronteira: `src/app/` importa somente
  `src/pipeline/service.py`. Qualquer outro alvo dentro de `src/pipeline/` é
  proibido e verificado por AST.
- Contrato de configuração: a fachada recebe a configuração não sensível
  resolvida por parâmetro; resolver `config.yaml` é responsabilidade dos
  entrypoints. Credencial não entra por esse caminho: continua resolvida dentro
  de `src/pipeline/providers/`, a partir do ambiente, como hoje.
- Contrato de limites: a fachada é síncrona; o chamador é responsável por
  executá-la fora da thread de requisição quando precisar de assincronia.

### 11. Estratégia TDD

- **Unidade**: operações da fachada com configuração injetada; recusa de
  configuração ausente ou incompleta; presença das contagens no retorno;
  ausência de leitura de arquivo e de ambiente durante a chamada.
- **Integração/contrato**: teste estático de AST da fronteira `src/app/` →
  `src/pipeline/`, incluindo o caso autorizado, o caso proibido e o caso de
  pacote vazio.
- **BDD/aceite**: os cenários AC-001 a AC-013 da seção 6 são o contrato de
  referência que orienta o desenho dos casos TDD. Nenhum arquivo `.feature` é
  criado ou executado.
- **Runner TDD**: Pytest, runner já estabelecido do projeto
  (`pyproject.toml`, `[tool.pytest.ini_options]`). O projeto não tem PHP nem
  Node; nenhuma decisão nova de runner é necessária.
- **E2E**: Não aplicável no sentido de navegador. A prova de ponta a ponta é a
  execução dos cinco comandos de operação da raiz após a migração.
- **Verificação manual**: execução dos cinco comandos de operação, por serem
  entrypoints de processo cujo comportamento de invocação não é coberto pela
  suíte. O motivo é registrado na evidência da tarefa correspondente.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-002, FR-001, FR-002, NFR-001, AC-001 | AC-001 na seção 6 | caso de importabilidade do pacote movido em `tests/test_pipeline_service.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_pacote_migrado_para_src_pipeline_e_importavel: ModuleNotFoundError src.pipeline | GREEN 2026-09-03 — os 12 módulos existentes migrados são importáveis em `src.pipeline` e `src/app/__init__.py` existe | Regressão T014: 239 testes preexistentes aprovados; Ruff sem achados |
| US-002, FR-001, FR-005, NFR-001, AC-002 | AC-002 na seção 6 | caso de resolução dos entrypoints em `tests/test_pipeline_service.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_entrypoints_da_raiz_importam_de_src_pipeline: 5 entrypoints importam de src.<módulo> | GREEN 2026-09-03 — os cinco entrypoints operacionais importam de `src.pipeline` | Regressão T014: 239 testes preexistentes aprovados; Ruff sem achados |
| US-001, FR-003, FR-004, NFR-004, AC-003 | AC-003 na seção 6 | caso de execução com configuração injetada em `tests/test_pipeline_service.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_fachada_executa_com_configuracao_em_memoria: sem src.pipeline.service | GREEN 2026-09-03 — `sync_vector_store` executa sem arquivo de configuração e devolve `SyncCounts` | Refactor T015: fachada separa validação, composição e casos de uso; 239 testes preexistentes aprovados |
| US-001, FR-003, FR-004, NFR-002, AC-004 | AC-004 na seção 6 | caso de recusa por configuração incompleta em `tests/test_pipeline_service.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_fachada_recusa_configuracao_incompleta_sem_expor_credencial: sem src.pipeline.service | GREEN 2026-09-03 — configuração vazia falha em `projeto` antes de provider e sem expor credencial | Refactor T015: ausência e tipo inválido possuem erros separados; Ruff aprovado |
| US-003, FR-002, FR-006, NFR-001, AC-005 | AC-005 na seção 6 | caso de import proibido em `tests/test_application_boundaries.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_estrutura_da_fronteira_existe + 2 varreduras: src/app/ e src/pipeline/ inexistentes | GREEN 2026-09-03 — estrutura presente e zero violações nos dois sentidos | Refactor T016: scanner usa alvo autorizado único e mensagens com caminho/módulo |
| US-003, FR-003, FR-006, AC-006 | AC-006 na seção 6 | caso de import autorizado em `tests/test_application_boundaries.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_import_autorizado_da_fachada_e_aceito + test_pacote_app_vazio: src/app/ inexistente | GREEN 2026-09-03 — import da fachada aceito e pacote app vazio sem falso positivo | Refactor T016: varredura determinística e sem fixtura temporária |
| US-001, FR-004, NFR-002, NFR-003, AC-007 | AC-007 na seção 6 | caso de ausência de leitura de disco e ambiente em `tests/test_pipeline_service.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_fachada_nao_le_disco_nem_ambiente_para_configuracao: sem src.pipeline.service | GREEN 2026-09-03 — fonte da fachada não lê arquivo nem consulta ambiente | Refactor T015: dependências internas recebem aliases privados e superfície pública fica limitada às quatro operações |
| US-001, FR-003, NFR-004, AC-008 | AC-008 na seção 6 | caso das quatro contagens no retorno em `tests/test_pipeline_service.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_sincronizacao_devolve_as_quatro_contagens_no_retorno: sem src.pipeline.service | GREEN 2026-09-03 — retorno expõe previstos, inseridos, mantidos e removidos | Refactor T015: lote vazio devolve contagens zero sem compor provider |
| US-003, FR-007, NFR-003, AC-009 | AC-009 na seção 6 | caso de completude do contrato documentado em `tests/test_docs_safety.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_contrato_da_fronteira_documenta_fachada_entrypoints_config_e_limites: docs/architecture.md sem a fachada | GREEN 2026-09-03 — contrato publica fachada, entrypoints, configuração e limite síncrono | Refactor T018: contrato tabular confrontado com superfície pública real |
| US-003, FR-002, FR-007, NFR-002, AC-010 | AC-010 na seção 6 | caso de declaração das dívidas bloqueantes em `tests/test_docs_safety.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_contrato_declara_as_dividas_bloqueantes_com_identificador: BACKLOG-0012/0013 ausentes | GREEN 2026-09-03 — dívidas e regra de reabrir SPEC-0008 publicadas | Refactor T018: limites e bloqueios ganharam seção própria |
| US-002, FR-004, FR-005, NFR-004, AC-011 | AC-011 na seção 6 | caso de repasse de configuração pelo entrypoint em `tests/test_pipeline_service.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_entrypoint_resolve_config_yaml_e_repassa_para_a_fachada: entrypoints não delegam à fachada | GREEN 2026-09-03 — cinco entrypoints resolvem configuração e chamam uma operação da fachada | Refactor T017: delegação mudou no menor ponto possível e os cinco `--help` permaneceram aprovados |
| US-002, FR-001, FR-005, FR-006, NFR-001, NFR-003, AC-012 | AC-012 na seção 6 | caso de baseline e módulos coletáveis em `tests/test_ci_gates.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_migration_baseline_and_boundary_modules_are_recorded: baseline 238 não declarada em doc versionada | GREEN 2026-09-03 — baseline publicada, módulos coletáveis e suíte completa com 255 passed | Refactor T018: caracterizações antigas atualizadas para a fachada; zero regressão |
| US-003, FR-003, FR-007, NFR-003, AC-013 | AC-013 na seção 6 | caso de correspondência entre fachada e contrato em `tests/test_docs_safety.py`, marcador `SPECSFY:` próprio | RED 2026-09-03 — test_toda_operacao_publica_da_fachada_aparece_no_contrato: sem src.pipeline.service | GREEN 2026-09-03 — quatro operações públicas correspondem exatamente ao contrato | Refactor T018: aliases privados evitam símbolos públicos incidentais |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | `tests/test_pipeline_service.py` | Passed — T014, teste focal de importabilidade |
| FR-001 | AC-002 | Integração | `tests/test_pipeline_service.py` | Passed — T014, teste focal dos entrypoints |
| FR-001 | AC-012 | Regressão | `uv run pytest` | Passed — T020, `uv run pytest` → 255 passed (≥ baseline 238) |
| FR-002 | AC-001 | Integração | `tests/test_pipeline_service.py` | Passed — T014, pacote `src/app/` e módulos migrados presentes |
| FR-002 | AC-005 | Contrato | `tests/test_application_boundaries.py` | Passed — T016, 5 passed nas varreduras de AST nos dois sentidos |
| FR-002 | AC-010 | Inspeção | `tests/test_docs_safety.py` | Passed — T018, 8 passed; contrato declara BACKLOG-0012/0013 |
| FR-003 | AC-003 | Unidade | `tests/test_pipeline_service.py` | Passed — T015, fachada executa com configuração injetada |
| FR-003 | AC-006 | Contrato | `tests/test_application_boundaries.py` | Passed — T016, 5 passed; import autorizado da fachada aceito |
| FR-003 | AC-008 | Unidade | `tests/test_pipeline_service.py` | Passed — T015, retorno expõe as quatro contagens |
| FR-003 | AC-013 | Inspeção | `tests/test_docs_safety.py` | Passed — T018, 8 passed; quatro operações públicas no contrato |
| FR-004 | AC-003 | Unidade | `tests/test_pipeline_service.py` | Passed — T015, configuração em memória sem `config.yaml` no disco |
| FR-004 | AC-004 | Unidade | `tests/test_pipeline_service.py` | Passed — T015, configuração incompleta recusada sem expor credencial |
| FR-004 | AC-007 | Unidade | `tests/test_pipeline_service.py` | Passed — T015, fachada não lê arquivo nem consulta ambiente |
| FR-004 | AC-011 | Integração | `tests/test_pipeline_service.py` | Passed — T017, cinco entrypoints resolvem config e delegam à fachada |
| FR-005 | AC-002 | Integração | `tests/test_pipeline_service.py` | Passed — T014, cinco entrypoints importam da nova topologia |
| FR-005 | AC-011 | Integração | `tests/test_pipeline_service.py` | Passed — T017, delegação no menor ponto possível; cinco `--help` código 0 |
| FR-005 | AC-012 | Regressão | `uv run pytest` | Passed — T020, `uv run pytest` → 255 passed |
| FR-006 | AC-005 | Contrato | `tests/test_application_boundaries.py` | Passed — T016, 5 passed; violação nomeia arquivo e módulo |
| FR-006 | AC-006 | Contrato | `tests/test_application_boundaries.py` | Passed — T016, 5 passed; pacote `src/app/` vazio sem falso positivo |
| FR-006 | AC-012 | Regressão | `uv run pytest` | Passed — T020, `uv run pytest` → 255 passed |
| FR-007 | AC-009 | Inspeção | `tests/test_docs_safety.py` | Passed — T018, 8 passed; fachada, entrypoints, config e limite síncrono |
| FR-007 | AC-010 | Inspeção | `tests/test_docs_safety.py` | Passed — T018, 8 passed; dívidas bloqueantes com identificador |
| FR-007 | AC-013 | Inspeção | `tests/test_docs_safety.py` | Passed — T018, 8 passed; contrato corresponde à superfície pública |
| NFR-001 | AC-001 | Regressão | `uv run pytest` | Passed — T014, 239 testes preexistentes aprovados e Ruff aprovado |
| NFR-001 | AC-002 | Regressão | `uv run pytest` | Passed — T014, casos focais 2 passed e regressão preexistente 239 passed |
| NFR-001 | AC-005 | Contrato | `tests/test_application_boundaries.py` | Passed — T016, 5 passed na suíte de fronteira |
| NFR-001 | AC-012 | Regressão | `uv run pytest` e `uv run ruff check .` | Passed — T020, 255 passed e `ruff check .` → `All checks passed!` |
| NFR-002 | AC-004 | Unidade | `tests/test_pipeline_service.py` | Passed — T015, mensagem de erro sem valor de credencial |
| NFR-002 | AC-007 | Unidade | `tests/test_pipeline_service.py` | Passed — T015, credenciais permanecem nos providers |
| NFR-002 | AC-010 | Inspeção | `tests/test_docs_safety.py` | Passed — T018, 8 passed; nenhum segredo na assinatura da fachada |
| NFR-003 | AC-007 | Unidade | `tests/test_pipeline_service.py` | Passed — T015, superfície pública limitada a quatro operações |
| NFR-003 | AC-009 | Inspeção | `tests/test_docs_safety.py` | Passed — T018, 8 passed; limite síncrono declarado no contrato |
| NFR-003 | AC-012 | Regressão | `uv run pytest` | Passed — T020, `uv run pytest` → 255 passed |
| NFR-003 | AC-013 | Inspeção | `tests/test_docs_safety.py` | Passed — T018, 8 passed; nenhuma operação documentada apenas no texto |
| NFR-004 | AC-003 | Unidade | `tests/test_pipeline_service.py` | Passed — T015, retorno estruturado da execução |
| NFR-004 | AC-008 | Unidade | `tests/test_pipeline_service.py` | Passed — T015, previstos, inseridos, mantidos e removidos no retorno |
| NFR-004 | AC-011 | Integração | `tests/test_pipeline_service.py` | Passed — T017, entrypoint repassa a configuração resolvida |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY — 2026-09-03 (primeira execução NOT READY na mesma data; reexecutado após as correções)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0008-fronteira-interna-pipeline-aplicacao/spec.md --allow-draft`
- **Estrutural**: `VALID DRAFT`. Formato `Specsfy/2.0`, três atos na ordem
  canônica, slug igual ao diretório, pacote restrito a `spec.md`. Cobertura
  conferida: 13 `AC` para 3 `US`, 7 `FR` e 4 `NFR`; cada ID tem no mínimo três
  `AC` distintos em `**Cobre**`, nenhuma tag Gherkin diverge do `**Cobre**` e
  nenhum ID citado está indeclarado.
- **Achados**: dois `BLOCKER`, um `WARNING` e uma `NOTE`, todos `Resolved` na
  correção de 2026-09-03. A reprovação foi semântica, não estrutural. As
  correções aplicadas: FR-004 e AC-007 passaram a separar configuração não
  sensível de resolução de credencial; FR-006 e AC-005 passaram a cobrir a
  fronteira nos dois sentidos; a seção 18 ganhou quatro itens de contexto e a
  seção 14 ganhou a tarefa T010; a palavra `provável` virou `comprovável`.

- **FIND-ARCH-001** [P1] [Resolved] FR-004 proíbe leitura de variável de ambiente, mas PR-004 preserva a resolução de credencial nos providers, que usam os.getenv — Refs: FR-004, NFR-002, AC-003, AC-004, AC-007, AC-011 — Evidence: src/pipeline/providers/embeddings/openai.py — Effect: o requisito contradiz um princípio da própria spec; o mesmo padrão aparece em src/pipeline/providers/vectorstores/qdrant.py e em src/pipeline/providers/vectorstores/pinecone.py, de modo que qualquer execução real lê ambiente e o AC-007 só passa com providers dublês, tornando a prova vazia — Suggestion: FR-004 passa a exigir que apenas a configuração não sensível chegue por parâmetro, sem leitura de config.yaml nem de ambiente pela fachada, e declara a resolução de credencial delegada aos providers; AC-007 afirma o que é verificável, ou seja, a chamada não lê arquivo de configuração e duas chamadas com configurações distintas não interferem uma na outra

- **FIND-PROD-002** [P1] [Resolved] A Definition of Done não exige atualizar os documentos de contexto cujos caminhos esta entrega move — Refs: FR-001, FR-002, FR-006, AC-001, AC-012 — Evidence: .specsfy/STACK.md — Effect: STACK.md linhas 14-16, 38 e 64-66 e a seção Contexto técnico de PROJECT.md citam src/providers/, src/indexing.py, src/safety.py e src/validation.py, e .specsfy/RULES.md registra a regra de fronteira equivalente para src/providers/; sem exigência na seção 18 a spec pode ser concluída deixando os três documentos apontando para caminhos inexistentes — Suggestion: acrescentar à seção 18 itens exigindo a atualização de .specsfy/STACK.md e PROJECT.md para os novos caminhos e o registro da regra de fronteira de src/app/ para a fachada em .specsfy/RULES.md por specsfy-aux-rules, incluindo a regra existente que cita src/providers/

- **FIND-ARCH-003** [P2] [Resolved] A verificação de fronteira cobre apenas o sentido de src/app/ para src/pipeline/ — Refs: FR-006, AC-005, AC-006 — Evidence: tests/test_provider_boundaries.py — Effect: o teste modelo varre em um único sentido; replicado assim, o import de src.app a partir de src/pipeline/ inverteria a dependência e permaneceria indetectado — Suggestion: estender FR-006 para reprovar também import de src.app a partir de src/pipeline/ e cobrir esse sentido em AC-005 ou em cenário próprio

- **FIND-PROD-004** [P3] [Resolved] Erro de palavra na mitigação de risco inverte o sentido da frase — Refs: FR-004, AC-007 — Evidence: specs/in-progress/0008-fronteira-interna-pipeline-aplicacao/spec.md — Effect: na seção 16, o risco do load_dotenv usa provável onde o sentido é comprovável, trocando o significado da mitigação — Suggestion: substituir provável por comprovável

- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed — 2026-09-03
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/planned/0008-fronteira-interna-pipeline-aplicacao/spec.md` → `VALID DRAFT` e, após promover o gate, `VALID`.
- **Contagens**: total=20 · tdd=13 (T001–T013) · code=5 (T014–T018) · doc=1 (T019) · test=1 (T020); 27/27 IDs cobertos; 13 tarefas TDD concluídas com RED registrado na seção 11.
- **RED observado**: `uv run pytest` → 239 passed, 16 failed (os 16 casos novos da SPEC-0008), zero regressão na suíte existente; `uv run ruff check .` → `All checks passed!`.
- **Predecessores TDD**: cada tarefa `[CODE]` depende de ao menos três casos TDD com RED; caminho crítico T001..T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020.
- **Achados**: nenhum bloqueio. `check_traceability.mjs` reporta marcadores
  órfãos de specs anteriores, limitação global já registrada na SPEC-0007 e
  mitigada pelos arquivos próprios desta fatia. Os identificadores externos
  foram omitidos desta nota porque o validador os interpreta como requisitos
  declarados pela própria SPEC-0008.
- **Replanejamento durante T014**: Passed — 2026-09-03. Corrigida uma
  dependência circular: T001 deixou de exigir `service.py`, pertencente a
  T015, e T014 passou a provar separadamente os dois casos focais da migração,
  os 239 testes preexistentes e o Ruff. Os testes das tarefas posteriores
  permanecem em RED até seus respectivos códigos. `validate_tasks.mjs
  --allow-draft` retornou `VALID DRAFT` com 20 tarefas, 13 TDD concluídas e
  cobertura de 27/27 IDs; os dois casos focais corrigidos retornaram `2
  passed` após a migração.
- **Replanejamento durante T015**: Passed — 2026-09-03. T015–T017 passaram a
  usar verificações focais e cumulativas compatíveis com a ordem das tarefas;
  a suíte completa ficou em T018/T020, depois que os casos documentais saem do
  RED. Nenhum teste, requisito, AC ou dependência de produção foi removido.
  `validate_tasks.mjs --allow-draft` retornou `VALID DRAFT`, com 20 tarefas,
  14 concluídas e cobertura de 27/27 IDs.

#### Gate do Ato III — Entrega

- **Resultado**: Passed — 2026-09-03
- **Aceite final (review → completed)**: READY em 2026-09-03. Comandos reexecutados na pasta `review`: `validate_spec.mjs` → `RESULTADO: READY`; `validate_tasks.mjs` → `RESULTADO: READY` (20/20 tarefas, 120/120 itens de checklist, 27/27 IDs); `verify_acceptance.mjs` → `QA: PASSED`; `verify_evidence.mjs` → `Evidência: PASSED (strict)`; `check_traceability.mjs` → 27/27 IDs cobertos, `GAPS` apenas por marcadores de SPEC-0001 a SPEC-0007; `uv run pytest` → 255 passed; `uv run ruff check .` → `All checks passed!`; `monitor_context.mjs --project . --check` → `CURRENT`. Nenhum `BLOCKER` remanescente.
- **Comando**: `uv run pytest` → 255 passed em 15,00s; `uv run ruff check .` → `All checks passed!`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0008-fronteira-interna-pipeline-aplicacao/spec.md .` → 27/27 IDs cobertos em 24 arquivos, `RESULTADO: GAPS` por marcadores de specs anteriores; `node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs <spec> .` → `QA: PASSED`; `node .agents/skills/specsfy-07-implement/scripts/verify_evidence.mjs <spec> .` → `Evidência: PASSED (strict)`; `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `Context monitor: CURRENT`.
- **Achados**: entrega sem bloqueio. Regressão completa com 255 testes aprovados, acima da baseline mínima de 238 registrada em `docs/architecture.md` e da baseline preexistente de 239. Ruff sem aviso. Rastreabilidade com 27/27 IDs cobertos, `uncovered: []`, `insufficient_cases: {}` e 182 casos de feature. O `RESULTADO: GAPS` decorre exclusivamente de `MARCADORES ÓRFÃOS` — nove critérios de aceite numerados de 014 em diante, um requisito funcional de número 008 e duas histórias de números 004 e 005, aqui citados sem a forma `TIPO-NNN` para não serem lidos como declaração desta spec — todos pertencentes às SPEC-0001 a SPEC-0007, materializados em arquivos de teste que compartilham a pasta `tests/`. Nenhum órfão vem dos arquivos próprios desta fatia: `tests/test_pipeline_service.py`, `tests/test_application_boundaries.py` e `tests/test_spec_markers.py`. A dívida de namespacear marcadores por spec está capturada em `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md` e pertence ao framework, não a esta entrega. `verify_acceptance.mjs` aprova com os 13 AC da seção 12 marcados `Passed`; `verify_evidence.mjs` aprova em modo estrito as cinco tarefas `[CODE]`; o monitor de contexto retorna `CURRENT`.
- **T020 — regressão, lint e rastreabilidade**: GREEN em 2026-09-03. `uv run pytest` → 255 passed; `uv run ruff check .` → `All checks passed!`; `check_traceability.mjs` → 27/27 IDs cobertos, sem `uncovered` nem `insufficient_cases`, `GAPS` apenas por marcadores de specs anteriores; `verify_acceptance.mjs` → `QA: PASSED`; `verify_evidence.mjs` → `PASSED (strict)`; `monitor_context.mjs --check` → `CURRENT`. Cobertura: todos os US, FR, NFR e AC da spec.
- **T014 — migração atômica**: GREEN em 2026-09-03. Comandos:
  `uv run pytest tests/test_pipeline_service.py -k 'pacote_migrado or
  entrypoints_da_raiz_importam'` → 2 passed; regressão isolada dos casos
  preexistentes → 239 passed e 4 casos posteriores da SPEC-0008 deselected;
  `uv run ruff check .` → `All checks passed!`. Foram movidos 12 módulos e o
  pacote de providers para `src/pipeline/`, criados os pacotes `src/app/` e
  `src/pipeline/`, e reescritos imports, alvos dinâmicos e guardas de caminho.
  `PROJECT.md` foi revisado, `docs/` reconstruído e o monitor retornou
  `CURRENT`. Cobertura: US-002, FR-001, FR-002, FR-005, NFR-001, AC-001 e
  AC-002.
- **T015 — fachada de casos de uso**: GREEN em 2026-09-03. `uv run pytest
  tests/test_pipeline_service.py -k 'configuracao_em_memoria or
  recusa_configuracao or nao_le_disco or quatro_contagens'` → 4 passed;
  regressão preexistente → 239 passed, 4 deselected; `uv run ruff check .` →
  `All checks passed!`. A superfície pública resultante é `run_pipeline`,
  `sync_vector_store`, `validate_retrieval` e `query_base`; helpers e o tipo de
  retorno da execução são privados. A fachada recebe configuração resolvida,
  não lê arquivo ou ambiente, mantém credenciais nos providers e devolve
  `SyncCounts` ao chamador. Cobertura: US-001, FR-003, FR-004, NFR-002,
  NFR-003, NFR-004, AC-003, AC-004, AC-007 e AC-008.
- **T016 — fronteira estática**: GREEN em 2026-09-03. `uv run pytest
  tests/test_application_boundaries.py` → 5 passed. O scanner percorre
  `src/app/` e `src/pipeline/`, aceita somente `src.pipeline.service` no
  sentido aplicação→pipeline, proíbe `src.app` no sentido inverso e trata o
  pacote de aplicação vazio sem aprovação enganosa. Cobertura: US-003,
  FR-002, FR-006, NFR-001, AC-005, AC-006 e parcela estrutural de AC-012.
- **T017 — entrypoints adaptados**: GREEN em 2026-09-03. Os casos focais de
  import e delegação retornaram `2 passed`; `uv run python <entrypoint>
  --help` retornou código 0 para `pipeline.py`, `search.py`, `chat.py`,
  `validate.py` e `upsert_from_chunks.py`; Ruff retornou `All checks passed!`.
  A mudança preservou argumentos e apresentação e substituiu somente o ponto
  de chamada por `sync_vector_store`, `query_base` ou `validate_retrieval`.
  Cobertura: US-002, FR-004, FR-005, NFR-004, AC-002 e AC-011.
- **Correção regressiva de T017 durante T018**: três caracterizações antigas
  ainda exigiam composição direta por `indexing`. Elas foram atualizadas para
  verificar `service.sync_vector_store`, `service.query_base` e o repasse de
  escopo à fachada. O teste focal retornou `3 passed`; a suíte completa passou
  depois da correção com 255 testes.
- **T018 — contrato publicado**: GREEN em 2026-09-03. `uv run pytest
  tests/test_docs_safety.py` → 8 passed; `uv run pytest` → 255 passed. O
  contrato versionado corresponde às quatro operações públicas, registra
  configuração por parâmetro, limite síncrono, cinco entrypoints, baseline e
  dívidas bloqueantes. Cobertura: US-003, FR-003, FR-007, NFR-002, NFR-003,
  AC-009, AC-010 e AC-013; AC-012 também ficou verde pela baseline publicada.
- **T019 — contexto persistente**: concluída em 2026-09-03. As auxiliares
  `$specsfy-aux-stack` e `$specsfy-aux-rules` atualizaram a topologia e a regra
  arquitetural; `PROJECT.md` registra a fachada e o destino `src/app/`.
  Varredura por caminhos antigos retornou zero ocorrência e `monitor_context.mjs
  --project . --check` retornou `CURRENT`. Cobertura: US-003, FR-001, FR-002,
  FR-006, FR-007, NFR-003, AC-009 e AC-012.

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

O detalhamento abaixo foi confirmado, ordenado e completado por
`$specsfy-05-tasks` a partir da seção 8. Há uma tarefa `[TEST] [TDD]` por
cenário de aceite (AC-001 a AC-013), seguida das tarefas `[CODE]` e `[DOC]`
que as tornam GREEN. O Gherkin permanece só na seção 6; cada caso executável
recebe marcador próprio `SPECSFY:` no arquivo indicado. Runner: Pytest, já
adotado pelo repositório. Regressão: `uv run pytest`. Lint: `uv run ruff check .`.

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-002] Derivar do AC-001 o caso de importabilidade do pacote movido em tests/test_pipeline_service.py — Refs: US-002, FR-001, FR-002, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: AC-001 lido; baseline conferida em `uv run pytest` → 239 passed antes da mudança (≥ 238 registrado na spec).
  - [x] **EXECUTE**: Criado `tests/test_pipeline_service.py::test_pacote_migrado_para_src_pipeline_e_importavel`, marcador `# SPECSFY: US-002 FR-001 FR-002 NFR-001 AC-001`, que importa os 12 módulos existentes migrados para `src.pipeline.*` e exige `src/app/__init__.py`; `service.py` permanece coberto separadamente por T003/T015.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError: No module named 'src.pipeline'`.
  - [x] **VISUAL**: `Não aplicável` — teste de biblioteca Python, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_pipeline_service.py -k pacote_migrado` → 1 failed; RED registrado na seção 11.
  - [x] **IMPROVE**: A asserção lista o conjunto completo de módulos faltando em vez de parar no primeiro, dando um diagnóstico único para T014.

- [x] T002 [TEST] [TDD] [US-002] Derivar do AC-002 o caso de resolução dos entrypoints da raiz em tests/test_pipeline_service.py — Refs: US-002, FR-001, FR-005, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Levantada a invocação atual dos cinco comandos; todos importam hoje `from src.<módulo>`.
  - [x] **EXECUTE**: Criado `test_entrypoints_da_raiz_importam_de_src_pipeline`, marcador próprio, que faz varredura de texto por `from src.<não-pipeline>` e exige referência a `src.pipeline`.
  - [x] **VERIFY**: RED válido — os cinco entrypoints acusados por importarem `chunker`, `config`, `indexing`, `loader`, `manifest`, `quality`, `safety`, `status_gate`, `validation`, `exporter`.
  - [x] **VISUAL**: `Não aplicável` — verificação de texto de módulo, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_pipeline_service.py -k entrypoints` → 1 failed; RED na seção 11.
  - [x] **IMPROVE**: A varredura é estática (lê o texto), evitando efeitos colaterais de importar `chat.py`/`search.py`, que carregam `src.providers`.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 o caso de execução da fachada com configuração injetada em tests/test_pipeline_service.py — Refs: US-001, FR-003, FR-004, NFR-004, AC-003 — Depends: none
  - [x] **PREP**: Confirmadas as quatro operações da seção 8 e as chaves não sensíveis `projeto.nome`, `embedding`, `vector_store`.
  - [x] **EXECUTE**: Criado `test_fachada_executa_com_configuracao_em_memoria`, marcador próprio, que faz `monkeypatch.chdir(tmp_path)` (sem `config.yaml`) e chama `service.sync_vector_store(config=..., chunks=[])`.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError: No module named 'src.pipeline'` ao importar a fachada.
  - [x] **VISUAL**: `Não aplicável` — teste de biblioteca Python, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_pipeline_service.py -k config_em_memoria` → 1 failed; RED na seção 11.
  - [x] **IMPROVE**: O nome da operação (`sync_vector_store`) é um default reversível; o RED é dominado pela ausência do módulo, não pela assinatura.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 o caso de recusa de configuração ausente ou incompleta em tests/test_pipeline_service.py — Refs: US-001, FR-003, FR-004, NFR-002, AC-004 — Depends: none
  - [x] **PREP**: Definida a expectativa: falha imediata com a chave faltante e sem valor de credencial (`sk-`, `api_key`) na mensagem.
  - [x] **EXECUTE**: Criado `test_fachada_recusa_configuracao_incompleta_sem_expor_credencial`, marcador próprio, com `pytest.raises((KeyError, ValueError))` sobre `config={}`.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError` antes de qualquer asserção sobre a mensagem.
  - [x] **VISUAL**: `Não aplicável` — teste de biblioteca Python, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_pipeline_service.py -k recusa_configuracao` → 1 failed; RED na seção 11.
  - [x] **IMPROVE**: A asserção sobre ausência de credencial na mensagem já está escrita, guiando a implementação da fachada em T015.

- [x] T005 [TEST] [TDD] [US-003] Derivar do AC-005 o caso de import proibido nos dois sentidos em tests/test_application_boundaries.py — Refs: US-003, FR-002, FR-006, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Lido `tests/test_provider_boundaries.py` como modelo de varredura por AST.
  - [x] **EXECUTE**: Criado `tests/test_application_boundaries.py` com `test_estrutura_da_fronteira_existe`, `test_src_app_so_importa_a_fachada_de_src_pipeline` e `test_src_pipeline_nao_importa_a_camada_de_aplicacao`, marcador `# SPECSFY: US-003 FR-002 FR-006 NFR-001 AC-005`, cobrindo os dois sentidos e nomeando arquivo e módulo na violação.
  - [x] **VERIFY**: RED válido — os três casos falham por `src/app/` e `src/pipeline/` inexistentes (`assert APP_DIR.is_dir()` / `assert PIPELINE_DIR.is_dir()`).
  - [x] **VISUAL**: `Não aplicável` — teste estático de AST, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_application_boundaries.py` → 5 failed; RED na seção 11.
  - [x] **IMPROVE**: Cada caso de varredura tem uma guarda `is_dir()` explícita, impedindo aprovação vazia enquanto a estrutura não existir.

- [x] T006 [TEST] [TDD] [US-003] Derivar do AC-006 o caso de import autorizado da fachada e de pacote vazio em tests/test_application_boundaries.py — Refs: US-003, FR-003, FR-006, AC-006 — Depends: none
  - [x] **PREP**: Confirmado que o único alvo autorizado é `src.pipeline.service` e que `src/app/` pode entregar vazio.
  - [x] **EXECUTE**: Criados `test_import_autorizado_da_fachada_e_aceito` e `test_pacote_app_vazio_nao_produz_falso_positivo`, marcador `# SPECSFY: US-003 FR-003 FR-006 AC-006`.
  - [x] **VERIFY**: RED válido — ambos falham por `src/app/` inexistente.
  - [x] **VISUAL**: `Não aplicável` — teste estático de AST, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_application_boundaries.py -k "autorizado or vazio"` → 2 failed; RED na seção 11.
  - [x] **IMPROVE**: O caso de pacote vazio aceita tanto ausência de arquivos quanto apenas `__init__.py`, cobrindo a entrega mínima de T014.

- [x] T007 [TEST] [TDD] [US-001] Derivar do AC-007 o caso de ausência de estado global e de leitura de disco e ambiente em tests/test_pipeline_service.py — Refs: US-001, FR-004, NFR-002, NFR-003, AC-007 — Depends: none
  - [x] **PREP**: Definido observar o texto-fonte da fachada por `load_config(`, `os.getenv`, `os.environ` e `load_dotenv`, dado o limite do `load_dotenv()` de `src/config.py` (BACKLOG-0012).
  - [x] **EXECUTE**: Criado `test_fachada_nao_le_disco_nem_ambiente_para_configuracao`, marcador próprio, que inspeciona `Path(service.__file__).read_text()`.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError` ao importar a fachada.
  - [x] **VISUAL**: `Não aplicável` — teste de biblioteca Python, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_pipeline_service.py -k nao_le_disco` → 1 failed; RED na seção 11.
  - [x] **IMPROVE**: A verificação por texto-fonte é o que se pode comprovar sem BACKLOG-0012 resolvido; o limite está declarado na seção 16.

- [x] T008 [TEST] [TDD] [US-001] Derivar do AC-008 o caso das quatro contagens no retorno da sincronização em tests/test_pipeline_service.py — Refs: US-001, FR-003, NFR-004, AC-008 — Depends: none
  - [x] **PREP**: Confirmados os nomes `previstos`, `inseridos`, `mantidos`, `removidos` na saída de `src/indexing.py` (`SyncCounts`).
  - [x] **EXECUTE**: Criado `test_sincronizacao_devolve_as_quatro_contagens_no_retorno`, marcador próprio, que lê as quatro contagens no valor de retorno (atributo ou chave).
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError` ao importar a fachada.
  - [x] **VISUAL**: `Não aplicável` — teste de biblioteca Python, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_pipeline_service.py -k quatro_contagens` → 1 failed; RED na seção 11.
  - [x] **IMPROVE**: A asserção aceita `hasattr` ou chave de dicionário, não travando a forma do resultado estruturado antes de T015.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-009 o caso de contrato documentado e completo em tests/test_docs_safety.py — Refs: US-003, FR-007, NFR-003, AC-009 — Depends: none
  - [x] **PREP**: Confirmado `docs/architecture.md` como destino do contrato e os itens verificáveis por texto.
  - [x] **EXECUTE**: Acrescentado `test_contrato_da_fronteira_documenta_fachada_entrypoints_config_e_limites`, marcador `# SPECSFY: US-003 FR-007 NFR-003 AC-009`, conferindo fachada, `src/app/`, os cinco entrypoints, configuração por parâmetro e o limite síncrono.
  - [x] **VERIFY**: RED válido — `docs/architecture.md` atual não cita `src/pipeline/service.py` nem os entrypoints.
  - [x] **VISUAL**: `Não aplicável` — verificação de documentação em texto, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_docs_safety.py -k contrato_da_fronteira` → 1 failed; RED na seção 11.
  - [x] **IMPROVE**: A lista de itens conferidos está explícita no teste, servindo de checklist para T018.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-010 o caso de declaração das dívidas bloqueantes em tests/test_docs_safety.py — Refs: US-003, FR-002, FR-007, NFR-002, AC-010 — Depends: none
  - [x] **PREP**: Confirmados os identificadores BACKLOG-0012 e BACKLOG-0013 e o texto de bloqueio esperado (`bloqueante`/`impedimento`, `reabrir`, `spec-0008`).
  - [x] **EXECUTE**: Acrescentado `test_contrato_declara_as_dividas_bloqueantes_com_identificador`, marcador próprio.
  - [x] **VERIFY**: RED válido — nenhum dos identificadores aparece em `docs/architecture.md`.
  - [x] **VISUAL**: `Não aplicável` — verificação de documentação em texto, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_docs_safety.py -k dividas_bloqueantes` → 1 failed; RED na seção 11.
  - [x] **IMPROVE**: O teste exige simultaneamente identificador, linguagem de impedimento e a regra de reabrir a SPEC-0008, cobrindo o AC inteiro num caso.

- [x] T011 [TEST] [TDD] [US-002] Derivar do AC-011 o caso de repasse de configuração pelo entrypoint em tests/test_pipeline_service.py — Refs: US-002, FR-004, FR-005, NFR-004, AC-011 — Depends: none
  - [x] **PREP**: Confirmado que cada entrypoint deve resolver `config.yaml` (`load_config(`) e chamar a fachada (`src.pipeline.service` ou `service.<operação>`).
  - [x] **EXECUTE**: Criado `test_entrypoint_resolve_config_yaml_e_repassa_para_a_fachada`, marcador `# SPECSFY: US-002 FR-004 FR-005 NFR-004 AC-011`, varredura de texto dos cinco comandos.
  - [x] **VERIFY**: RED válido — os cinco entrypoints resolvem `config.yaml` hoje, mas nenhum delega à fachada.
  - [x] **VISUAL**: `Não aplicável` — verificação de texto de módulo, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_pipeline_service.py -k repassa_para_a_fachada` → 1 failed; RED na seção 11.
  - [x] **IMPROVE**: O teste separa as duas obrigações (resolver e delegar), o que localiza a falha por entrypoint em T017.

- [x] T012 [TEST] [TDD] [US-002] Derivar do AC-012 o caso de baseline de regressão registrada e módulos de fronteira e fachada coletáveis em tests/test_ci_gates.py — Refs: US-002, FR-001, FR-005, FR-006, NFR-001, NFR-003, AC-012 — Depends: none
  - [x] **PREP**: Registrada a baseline `_BASELINE_MINIMA = 238`; destino de declaração: `docs/architecture.md` ou `docs/testing.md`.
  - [x] **EXECUTE**: Acrescentado `test_migration_baseline_and_boundary_modules_are_recorded`, marcador `# SPECSFY: US-002 FR-001 FR-005 FR-006 NFR-001 NFR-003 AC-012`, conferindo os dois módulos de regressão e a baseline em documentação versionada.
  - [x] **VERIFY**: RED válido — os módulos já existem, mas nenhuma documentação declara a baseline de 238 (`assert baseline_declarada` falha).
  - [x] **VISUAL**: `Não aplicável` — verificação de coleta e documentação, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_ci_gates.py -k migration_baseline` → 1 failed; RED na seção 11.
  - [x] **IMPROVE**: A parte de módulos coletáveis já passa, isolando o RED na declaração da baseline — exatamente o que T018/T019 precisam publicar.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-013 o caso de correspondência entre operações da fachada e contrato em tests/test_docs_safety.py — Refs: US-003, FR-003, FR-007, NFR-003, AC-013 — Depends: none
  - [x] **PREP**: Definido enumerar a superfície pública de `src.pipeline.service` por `dir()` filtrando `__module__ == service.__name__`.
  - [x] **EXECUTE**: Acrescentado `test_toda_operacao_publica_da_fachada_aparece_no_contrato`, marcador `# SPECSFY: US-003 FR-003 FR-007 NFR-003 AC-013`, com dupla checagem: operação pública sem contrato e operação documentada inexistente.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError` ao importar `src.pipeline.service`.
  - [x] **VISUAL**: `Não aplicável` — verificação de documentação em texto, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_docs_safety.py -k operacao_publica_da_fachada` → 1 failed; RED na seção 11.
  - [x] **IMPROVE**: O caso cobre os dois sentidos da divergência (código→doc e doc→código), tornando AC-013 verificável por teste e não por leitura.

#### Fase 2 — US-002 Reorganizar sem interromper a operação (P1)

**Objetivo**: mover o pacote e preservar os comandos do operador.
**Teste independente**: executar os cinco comandos da raiz e a suíte completa após a migração.

- [x] T014 [CODE] [US-002] Mover src/ para src/pipeline/, criar src/app/__init__.py e reescrever todos os imports em src/pipeline/, nos nove entrypoints da raiz e nos arquivos de teste — Refs: US-002, FR-001, FR-002, FR-005, NFR-001, AC-001, AC-002 — Depends: T001, T002, T012
  - [x] **PREP**: RED confirmado em `uv run pytest` → 239 passed e 16 failed exclusivamente nos casos novos da SPEC-0008; T001, T002 e T012 permanecem vermelhos. Baseline mínima 238 confirmada, imports `src.*` inventariados por `rg` em módulos, nove entrypoints e testes, e `docs/` reconstruído e aprovado pelo `$specsfy-documentator` antes da mudança.
  - [x] **EXECUTE**: Os 12 módulos e `src/providers/` foram movidos com `git mv` para `src/pipeline/`; `src/app/__init__.py` e `src/pipeline/__init__.py` foram criados, e imports, alvos dinâmicos e guardas de caminho dos nove entrypoints e da suíte foram reescritos sem alterar a lógica interna. `PROJECT.md` e `docs/` já refletem os caminhos movidos; monitor `CURRENT`.
  - [x] **VERIFY**: Casos focais `2 passed`; regressão dos 239 testes preexistentes `239 passed, 4 deselected`; `uv run ruff check .` → `All checks passed!`.
  - [x] **VISUAL**: `Não aplicável` — a tarefa move módulos Python e não altera superfície visual, portanto não há bordas, espaçamentos, margens, padding ou tipografia a inspecionar.
  - [x] **EVIDENCE**: GREEN de T001/T002, parcela estrutural de T012, comandos, contagens e caminhos foram registrados nas seções 11–13; `verify_evidence.mjs ... --task T014` → `Evidência: PASSED (strict)`.
  - [x] **IMPROVE**: A varredura pós-migração foi ampliada para imports dinâmicos e caminhos compostos com `Path`, evitando que testes antigos continuassem apontando silenciosamente para módulos removidos.
  <!-- specsfy:evidence {"task":"T014","refs":["US-002","FR-001","FR-002","FR-005","NFR-001","AC-001","AC-002"],"files":["src/pipeline/","src/app/__init__.py"],"commands":[{"run":"uv run pytest tests/test_pipeline_service.py -k 'pacote_migrado or entrypoints_da_raiz_importam'","exit":0},{"run":"uv run pytest --ignore=tests/test_pipeline_service.py --ignore=tests/test_application_boundaries.py -k 'not migration_baseline_and_boundary_modules_are_recorded and not contrato_da_fronteira_documenta_fachada_entrypoints_config_e_limites and not contrato_declara_as_dividas_bloqueantes_com_identificador and not toda_operacao_publica_da_fachada_aparece_no_contrato'","exit":0},{"run":"uv run ruff check .","exit":0}]} -->

**Checkpoint**: casos focais da migração, 239 testes preexistentes e Ruff verdes;
os testes da fachada, do contrato e da fronteira final permanecem em RED até
as tarefas responsáveis.

#### Fase 3 — US-001 Consumir o pipeline por uma fachada estável (P1)

**Objetivo**: expor as operações de caso de uso com configuração injetada.
**Teste independente**: chamar a fachada com configuração em memória e obter as contagens no retorno.

- [x] T015 [CODE] [US-001] Implementar a fachada de casos de uso em src/pipeline/service.py — Refs: US-001, FR-003, FR-004, NFR-002, NFR-003, NFR-004, AC-003, AC-004, AC-007, AC-008 — Depends: T003, T004, T007, T008, T014
  - [x] **PREP**: RED de T003, T004, T007 e T008 reproduzido por quatro casos focais, todos por ausência de `src.pipeline.service`. Confirmadas as operações `run_pipeline`, `sync_vector_store`, `validate_retrieval` e `query_base`, suas entradas por configuração resolvida e retornos estruturados; documentação reconstruída e referências atuais de LangChain v1 consultadas antes de `EXECUTE`.
  - [x] **EXECUTE**: Implementado `src/pipeline/service.py` com quatro operações públicas, helpers e tipos privados, configuração não sensível recebida por parâmetro, zero leitura de arquivo/ambiente, retorno estruturado da execução e `SyncCounts` explícito na sincronização. Nenhum símbolo interno é reexportado; documentação reconstruída e monitor `CURRENT`.
  - [x] **VERIFY**: Quatro casos focais da fachada `4 passed`; regressão preexistente `239 passed, 4 deselected`; Ruff aprovado. Os casos de entrypoint e documentação permanecem reservados para T017/T018.
  - [x] **VISUAL**: `Não aplicável` — a tarefa entrega um módulo Python de biblioteca, sem superfície visual, portanto não há bordas, espaçamentos, margens, padding ou tipografia a inspecionar.
  - [x] **EVIDENCE**: GREEN de T003, T004, T007 e T008, comandos, regressão e assinatura pública registrados nas seções 11 e 13; `verify_evidence.mjs ... --task T015` → `Evidência: PASSED (strict)`.
  - [x] **IMPROVE**: Imports e tipos auxiliares receberam aliases privados, fazendo a inspeção da superfície pública encontrar somente as quatro operações da fachada e impedindo reexportação acidental.
  <!-- specsfy:evidence {"task":"T015","refs":["US-001","FR-003","FR-004","NFR-002","NFR-003","NFR-004","AC-003","AC-004","AC-007","AC-008"],"files":["src/pipeline/service.py"],"commands":[{"run":"uv run pytest tests/test_pipeline_service.py -k 'configuracao_em_memoria or recusa_configuracao or nao_le_disco or quatro_contagens'","exit":0},{"run":"uv run pytest --ignore=tests/test_pipeline_service.py --ignore=tests/test_application_boundaries.py -k 'not migration_baseline_and_boundary_modules_are_recorded and not contrato_da_fronteira_documenta_fachada_entrypoints_config_e_limites and not contrato_declara_as_dividas_bloqueantes_com_identificador and not toda_operacao_publica_da_fachada_aparece_no_contrato'","exit":0}]} -->

- [x] T016 [CODE] [US-003] Consolidar o scanner de fronteira nos dois sentidos em tests/test_application_boundaries.py e o pacote src/app/__init__.py — Refs: US-003, FR-002, FR-006, NFR-001, AC-005, AC-006, AC-012 — Depends: T005, T006, T012, T014
  - [x] **PREP**: RED de T005/T006 e parcela estrutural de T012 confirmados na seção 11; único alvo autorizado confirmado como `src.pipeline.service`. `docs/` foi reconstruído e uma varredura não encontrou fixtura de violação nem import interno em `src/app/`.
  - [x] **EXECUTE**: O scanner AST de `tests/test_application_boundaries.py` está consolidado nos dois sentidos, nomeia arquivo e módulo nas violações, aceita somente `src.pipeline.service`, e `src/app/__init__.py` vazio não produz falso positivo. Monitor `CURRENT`.
  - [x] **VERIFY**: `uv run pytest tests/test_application_boundaries.py` → 5 passed; a regressão integral permanece em T018/T020, depois de os casos documentais saírem do RED.
  - [x] **VISUAL**: `Não aplicável` — a tarefa entrega teste estático de AST, sem superfície visual, portanto não há bordas, espaçamentos, margens, padding ou tipografia a inspecionar.
  - [x] **EVIDENCE**: GREEN de T005/T006 e parcela estrutural de T012 registrados nas seções 11 e 13; `verify_evidence.mjs ... --task T016` → `Evidência: PASSED (strict)`.
  - [x] **IMPROVE**: A exceção deixou de ser uma lista aberta e ficou reduzida a um único módulo nomeado (`src.pipeline.service`), tornando a expansão futura deliberada e revisável.
  <!-- specsfy:evidence {"task":"T016","refs":["US-003","FR-002","FR-006","NFR-001","AC-005","AC-006","AC-012"],"files":["tests/test_application_boundaries.py","src/app/__init__.py"],"commands":[{"run":"uv run pytest tests/test_application_boundaries.py","exit":0}]} -->

- [x] T017 [CODE] [US-002] Fazer pipeline.py, search.py, chat.py, validate.py e upsert_from_chunks.py resolverem config.yaml e chamarem a fachada — Refs: US-002, FR-004, FR-005, NFR-004, AC-002, AC-011 — Depends: T002, T011, T012, T015
  - [x] **PREP**: T002 permanece GREEN após a migração e T011 foi reproduzido em RED, nomeando os cinco entrypoints sem delegação. Invocações `--help`, argumentos atuais e saída operacional foram lidos; `docs/` reconstruído antes de `EXECUTE`.
  - [x] **EXECUTE**: Os cinco entrypoints continuam resolvendo `config.yaml` e agora delegam à fachada: `pipeline.py` e `upsert_from_chunks.py` usam `sync_vector_store`, `search.py` e `chat.py` usam `query_base`, e `validate.py` usa `validate_retrieval`. Argumentos, nomes de comandos e apresentação no terminal foram preservados; documentação reconstruída e monitor `CURRENT`.
  - [x] **VERIFY**: Casos focais de import e delegação `2 passed`; os cinco comandos responderam a `--help` com código 0 e as mesmas opções; Ruff aprovado. A regressão integral permanece em T018/T020.
  - [x] **VISUAL**: `Não aplicável` — a saída textual de terminal existente é preservada sem redesenho, portanto não há bordas, espaçamentos, margens, padding ou tipografia visual a inspecionar.
  - [x] **EVIDENCE**: GREEN de T002/T011, comandos focais e os cinco `--help` registrados nas seções 11 e 13; `verify_evidence.mjs ... --task T017` → `Evidência: PASSED (strict)`.
  - [x] **IMPROVE**: A delegação foi feita no ponto mais estreito de cada CLI, removendo composição duplicada de embeddings/vector store em busca e chat sem alterar a responsabilidade de carregar `config.yaml`.
  <!-- specsfy:evidence {"task":"T017","refs":["US-002","FR-004","FR-005","NFR-004","AC-002","AC-011"],"files":["pipeline.py","search.py","chat.py","validate.py","upsert_from_chunks.py"],"commands":[{"run":"uv run pytest tests/test_pipeline_service.py -k 'entrypoints_da_raiz_importam or repassa_para_a_fachada'","exit":0},{"run":"uv run python pipeline.py --help","exit":0},{"run":"uv run python search.py --help","exit":0},{"run":"uv run python chat.py --help","exit":0},{"run":"uv run python validate.py --help","exit":0},{"run":"uv run python upsert_from_chunks.py --help","exit":0}]} -->

**Checkpoint**: fachada chamável sem `config.yaml` e comandos preservados.

#### Fase 4 — US-003 Impedir a erosão da fronteira (P1)

**Objetivo**: tornar a fronteira verificável e o contrato legível.
**Teste independente**: introduzir um import proibido e observar a suíte reprovar.

- [x] T018 [CODE] [US-003] Publicar o contrato da fronteira em docs/architecture.md — Refs: US-003, FR-003, FR-007, NFR-002, NFR-003, AC-009, AC-010, AC-013 — Depends: T009, T010, T013, T015
  - [x] **PREP**: RED de T009/T010/T013 reproduzido (`3 failed`), superfície pública inspecionada como `query_base`, `run_pipeline`, `sync_vector_store` e `validate_retrieval`, e dívidas `BACKLOG-0012/0013` confirmadas. `docs/` reconstruído antes de `EXECUTE`.
  - [x] **EXECUTE**: `docs/architecture.md` publica a fronteira bidirecional, as quatro operações reais, entradas/saídas, os cinco entrypoints, configuração por parâmetro, limite síncrono, baseline e `BACKLOG-0012/0013` com a regra de reabrir a SPEC-0008. Documentação reconstruída e monitor `CURRENT`.
  - [x] **VERIFY**: `uv run pytest tests/test_docs_safety.py` → 8 passed; após alinhar três caracterizações antigas à fachada, `uv run pytest` → 255 passed.
  - [x] **VISUAL**: `Não aplicável` — a entrega é documentação Markdown e testes de contrato, sem superfície visual, portanto não há bordas, espaçamentos, margens, padding ou tipografia de aplicação a inspecionar.
  - [x] **EVIDENCE**: GREEN de T009/T010/T013, caminho, comandos e regressão registrados nas seções 11 e 13; `verify_evidence.mjs ... --task T018` → `Evidência: PASSED (strict)`.
  - [x] **IMPROVE**: A documentação passou a enumerar a superfície pública em tabela e o teste confronta código↔texto nos dois sentidos, reduzindo deriva futura.
  <!-- specsfy:evidence {"task":"T018","refs":["US-003","FR-003","FR-007","NFR-002","NFR-003","AC-009","AC-010","AC-013"],"files":["docs/architecture.md"],"commands":[{"run":"uv run pytest tests/test_docs_safety.py","exit":0},{"run":"uv run pytest","exit":0}]} -->

- [x] T019 [DOC] [US-003] Atualizar .specsfy/STACK.md, PROJECT.md e .specsfy/RULES.md para os novos caminhos e registrar a regra de fronteira — Refs: US-003, FR-001, FR-002, FR-006, FR-007, NFR-003, AC-009, AC-012 — Depends: T012, T014, T015, T018
  - [x] **PREP**: Varredura identificou oito menções antigas em `.specsfy/STACK.md`, uma em `.specsfy/RULES.md` e nenhuma restante em `PROJECT.md`; o projeto ainda precisava declarar `src/app/` e `src/pipeline/service.py` explicitamente.
  - [x] **EXECUTE**: `.specsfy/STACK.md` e `PROJECT.md` registram `src/pipeline/`, `src/app/` e a fachada; `$specsfy-aux-rules` acrescentou a fronteira e a regra existente passou a citar `src/pipeline/providers/`.
  - [x] **VERIFY**: `monitor_context.mjs --project . --check` → `CURRENT`; `rg` retornou zero menção aos caminhos antigos nos três documentos.
  - [x] **VISUAL**: `Não aplicável` — a tarefa altera documentação Markdown sem superfície visual, portanto não há bordas, espaçamentos, margens, padding ou tipografia de aplicação a inspecionar.
  - [x] **EVIDENCE**: Comando, resultado, cobertura e arquivos atualizados registrados na seção 13; os documentos são a própria evidência versionada.
  - [x] **IMPROVE**: A stack ganhou uma linha explícita para a fronteira interna, evitando que a topologia precise ser inferida apenas pelas notas históricas.
  <!-- specsfy:evidence {"task":"T019","refs":["US-003","FR-001","FR-002","FR-006","FR-007","NFR-003","AC-009","AC-012"],"files":["PROJECT.md",".specsfy/STACK.md",".specsfy/RULES.md"],"commands":[{"run":"node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check","exit":0}]} -->

**Checkpoint**: fronteira verificável, contrato publicado e contexto do projeto coerente com os novos caminhos.

#### Fase final — Qualidade

- [x] T020 [TEST] Executar regressão, lint e rastreabilidade e registrar o resultado nas seções 11–13 de specs/in-progress/0008-fronteira-interna-pipeline-aplicacao/spec.md — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013 — Depends: T014, T015, T016, T017, T018, T019
  - [x] **PREP**: Suíte Pytest, Ruff, validadores de spec/tarefas, achados especializados, monitor, documentador e rastreabilidade identificados. Baseline mínima 238, baseline preexistente 239 e última regressão completa 255 passed confirmadas em T001/T012/T018.
  - [x] **EXECUTE**: `uv run pytest` → 255 passed em 15,00s; `uv run ruff check .` → `All checks passed!`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0008-fronteira-interna-pipeline-aplicacao/spec.md .` → 27/27 IDs cobertos em 24 arquivos; `verify_acceptance.mjs` → `QA: PASSED`; `verify_evidence.mjs` → `Evidência: PASSED (strict)`; `monitor_context.mjs --project . --check` → `CURRENT`.
  - [x] **VERIFY**: Zero `uncovered` e zero `insufficient_cases` na rastreabilidade; 255 testes aprovados ≥ baseline mínima 238. O `RESULTADO: GAPS` é apenas de marcadores órfãos das SPEC-0001 a SPEC-0007 que compartilham `tests/`; nenhum vem de `tests/test_pipeline_service.py`, `tests/test_application_boundaries.py` ou `tests/test_spec_markers.py`. A seção 12 passou a registrar `Passed` em todos os 13 AC e a seção 13 fechou o Gate do Ato III.
  - [x] **VISUAL**: `Não aplicável` — nenhuma tarefa desta spec altera superfície visual.
  - [x] **EVIDENCE**: Contagens, comandos finais e veredito de rastreabilidade registrados nas seções 12 e 13; atestação abaixo.
  - [x] **IMPROVE**: Retrospectiva — a migração atômica de `src/` para `src/pipeline/` funcionou porque cada import foi inventariado por `rg` antes do `git mv`, a suíte preexistente de 239 testes serviu de rede de segurança imediata e os casos novos ficaram em RED até seu código. O `check_traceability.mjs` varrer toda a pasta `tests/` continua produzindo `GAPS` por marcadores de outras specs; a mitigação recorrente é confinar a auditoria aos arquivos da fatia. Recomendação para a fatia 2: priorizar BACKLOG-0012 (remover `load_dotenv()` do import de `src/pipeline/config.py`) antes de escrever `src/app/`, para que AC-007 possa ser provado sem provider dublê.
  <!-- specsfy:evidence {"task":"T020","refs":["US-001","US-002","US-003","FR-001","FR-002","FR-003","FR-004","FR-005","FR-006","FR-007","NFR-001","NFR-002","NFR-003","NFR-004","AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-007","AC-008","AC-009","AC-010","AC-011","AC-012","AC-013"],"files":["specs/in-progress/0008-fronteira-interna-pipeline-aplicacao/spec.md"],"commands":[{"run":"uv run pytest","exit":0},{"run":"uv run ruff check .","exit":0},{"run":"node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0008-fronteira-interna-pipeline-aplicacao/spec.md .","exit":1},{"run":"node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/in-progress/0008-fronteira-interna-pipeline-aplicacao/spec.md .","exit":0},{"run":"node .agents/skills/specsfy-07-implement/scripts/verify_evidence.mjs specs/in-progress/0008-fronteira-interna-pipeline-aplicacao/spec.md .","exit":0},{"run":"node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check","exit":0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001..T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020.
- Tarefas paralelas: T001 a T013 podem ser escritas em paralelo por
  materializarem RED em arquivos distintos (`tests/test_pipeline_service.py`,
  `tests/test_application_boundaries.py`, `tests/test_docs_safety.py` e
  `tests/test_ci_gates.py`) e não dependerem umas das outras. Depois do GREEN de
  T015, T016 e T018 podem avançar em paralelo a T017; T019 depende de T018 por
  atualizar os mesmos caminhos que o contrato publica.
- Estratégia de MVP: T014 sozinho já entrega valor verificável — o pacote
  reorganizado com a suíte verde e os cinco comandos preservados. A fronteira só
  passa a ser útil com T015 e T016 concluídos; o contrato documentado em T018 e
  o contexto atualizado em T019 fecham a entrega para quem vai implementar
  `src/app/`.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0003, concluída: fornece o padrão de contrato neutro, factory e teste
  estático de AST que esta spec replica um nível acima.
- SPEC-0007, concluída: fornece a esteira de integração contínua que executa o
  teste de fronteira a cada push e bloqueia o merge.
- BACKLOG-0012 e BACKLOG-0013: bloqueiam a implementação de `src/app/` na fatia
  2 do BACKLOG-0008. Não bloqueiam esta spec e podem ser entregues em paralelo.

#### Riscos

- Mover `src/` toca todos os imports do repositório e os 21 arquivos de teste →
  executar a migração como mudança atômica em T005, com a suíte completa como
  prova; não fatiar por módulo.
- A fachada pode degenerar em repasse fino que apenas reexporta funções
  internas, mantendo o acoplamento com outro nome → desenhar as operações pelo
  caso de uso, não pelo módulo de origem, e proibir reexportação de símbolos
  interno na revisão de T006.
- O `load_dotenv()` no import de `src/config.py` permite contornar a regra de
  configuração injetada enquanto BACKLOG-0012 não for entregue → declarar o
  limite no contrato de T008 e cobrir com o caso de AC-007 o que for
  comprovável sem a dívida resolvida.
- `src/app/` vazio pode produzir falso positivo no teste de fronteira, que
  passaria por não ter nada a inspecionar → cobrir explicitamente o caso de
  pacote vazio em T001.
- A documentação do contrato pode divergir da fachada com o tempo → AC-013
  torna a correspondência verificável por teste, não por leitura.

#### Suposições

- O runner de testes permanece Pytest, já estabelecido no `pyproject.toml`;
  nenhuma decisão nova de runner é necessária por não haver PHP nem Node.
- A fachada vive em `src/pipeline/service.py`. O nome é um default reversível:
  qualquer módulo único de `src/pipeline/` satisfaz o contrato, desde que seja
  o único alvo autorizado e esteja declarado no teste de fronteira.
- Os quatro casos de uso da seção 8 cobrem o que a fatia 2 precisa consumir.
  Uma operação adicional descoberta na fatia 2 reabre esta spec por
  `$specsfy-update-spec`, em vez de ser adicionada por decisão local.
- `docs/architecture.md` é o destino do contrato publicado. Se o documentador
  reorganizar a topologia de `docs/`, o destino acompanha, mantendo o conteúdo.
- Os arquivos `main.py`, `demo_rag.py`, `inspect_chunks.py` e `quality.py` na
  raiz não são comandos de operação declarados e recebem apenas o ajuste de
  import necessário para a suíte continuar verde.

### 17. Decisões

- **DEC-001**: reformular o item de origem de contrato de handoff entre
  repositórios para fronteira interna — a consolidação em `e2d8b1b` e `0fe7b1b`
  tornou a premissa de dois repositórios falsa. Alternativa descartada: manter
  o handoff supondo um repositório futuro separado, o que documentaria uma
  arquitetura que não existe.
- **DEC-002**: adotar `src/pipeline/` e `src/app/` dentro do mesmo pacote, em
  vez de um diretório `app/` na raiz ao lado de `src/`. Trade-off: exige mover
  todos os imports de uma vez, mas evita dois pacotes Python paralelos na raiz
  e mantém uma única configuração de projeto.
- **DEC-003**: manter os entrypoints na raiz como adaptadores finos, em vez de
  movê-los para dentro do pacote. Razão: a invocação dos comandos é contrato
  com o operador; mudá-la trocaria um problema futuro por um presente.
  Trade-off: a raiz do repositório continua com arquivos `.py` soltos.
- **DEC-004**: expor uma fachada nova de casos de uso em vez de tratar os
  módulos existentes como interface. Razão: reexportar `indexing` e
  `validation` congelaria a estrutura interna atual como contrato público.
  Trade-off: exige desenhar e manter uma camada adicional.
- **DEC-005**: injetar a configuração por parâmetro em vez de manter a leitura
  de `config.yaml` na fachada. Razão: um backend com vários projetos no mesmo
  processo não pode depender de um arquivo global. Trade-off: os entrypoints
  ganham a responsabilidade de resolver a configuração.
- **DEC-006**: declarar BACKLOG-0012 e BACKLOG-0013 como bloqueantes da fatia
  2, e não desta spec. Razão: a fronteira pode ser desenhada e provada antes
  das dívidas; começar `src/app/` antes delas é que seria arriscado.
  Trade-off: a regra de configuração injetada fica parcialmente contornável até
  BACKLOG-0012 ser entregue, limite que o contrato declara.
- **DEC-007**: verificar a fronteira por AST, replicando
  `tests/test_provider_boundaries.py`. Razão: o padrão já é conhecido, roda sem
  rede e já está integrado à esteira. Alternativa descartada: revisão manual em
  pull request, que a SPEC-0003 já demonstrou ser insuficiente.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/STACK.md` reflete `src/pipeline/` e `src/app/`, sem citar
      caminho inexistente sob o antigo `src/`.
- [x] `PROJECT.md` tem o `Contexto técnico` revisado para a nova topologia de
      módulos e para a existência da fachada.
- [x] `.specsfy/RULES.md` registra, por `$specsfy-aux-rules`, a regra de
      fronteira `src/app/` → fachada, e a regra existente sobre imports
      confinados passa a citar `src/pipeline/providers/`.
- [x] O monitor de contexto retorna `CURRENT`.
