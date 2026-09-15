# Especificação integrada: Namespacear marcadores SPECSFY por especificação

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0016 |
| Slug | 0016-namespacear-marcadores-specsfy-por-spec |
| Status | Complete |
| Effort | 2 |
| Effort updated at | 2026-09-15 |
| Effort rationale | Mudança localizada em um verificador Node.js, com compatibilidade legada, testes de contrato e migração piloto da SPEC-0015. Sem aplicação, banco ou interface. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-15 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

`check_traceability.mjs` trata IDs locais como `US-001`, `FR-001` e `AC-001`
como identificadores globais. Ao varrer a raiz do repositório, evidências de
outras specs contam como cobertura e como marcadores órfãos da spec atual. Isso
produz falsos positivos e falsos bloqueios nos gates, inclusive na SPEC-0015.

#### Resultado desejado

Cada marcador novo declara inequivocamente sua spec. O auditor isola cobertura
e órfãos pelo namespace alvo, mantém leitura compatível das specs históricas e
permite migrar uma spec inteira sem exigir migração em massa do repositório.

#### Métricas de sucesso

- 100% dos marcadores namespaced da spec alvo são avaliados sem interferência
  de marcadores estrangeiros ou legados.
- 100% das invocações históricas sem namespace alvo continuam aceitando
  marcadores legados como cobertura.
- A SPEC-0015 pode ser validada na raiz do repositório sem órfãos provenientes
  de outras specs.
- A suíte focal do verificador cobre ao menos cinco cenários e termina sem
  falhas após a implementação.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: O auditor atual conhece a spec de cada marcador? → Não. Ele extrai
  somente IDs locais de todas as linhas e agrega por ID, sem namespace.
- **R-002**: É possível migrar todas as specs agora sem ampliar o escopo? → Não
  é necessário. Um modo namespaced ativado pela presença do namespace alvo e
  um fallback legado permitem migração gradual.
- **R-003**: O consumidor exige compatibilidade de argumentos e saída? → Sim.
  `verify_repo.mjs` invoca o script posicionalmente e usa o código de saída;
  esses contratos devem ser preservados.

#### Fontes e contexto consultados

- `specs/backlog/0020-namespacear-marcadores-specsfy-por-spec.md` — brief e
  decisão confirmada.
- `.agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs` — parser,
  cálculo e relatório atuais.
- `.agents/skills/specsfy-04-validate/scripts/verify_repo.mjs` — consumidor do
  checker.
- `specs/defined/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/spec.md`
  e `tests/test_app_executions.py` — migração piloto.
- Specs concluídas 0006 e 0007 — evidência da limitação e das mitigações
  históricas.

#### Documentação consultada

- Somente fontes locais do repositório; nenhuma documentação externa foi
  necessária.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo; as fontes consultadas são versionadas no próprio
  repositório.

#### Dúvidas respondidas

- **Q**: Qual estratégia de compatibilidade adotar? → **A**: evolução local
  compatível, namespace explícito e migração gradual, confirmada pelo usuário
  em 2026-09-15.
- **Q**: O que torna um órfão bloqueante? → **A**: somente um ID inexistente
  declarado no namespace da spec alvo; IDs legados ambíguos são aviso.

#### Dúvidas abertas

- Nenhuma lacuna aplicável.

### 3. Escopo e atores

#### Incluído

- Reconhecer `SPECSFY: SPEC-NNNN <IDs locais>`.
- Extrair o namespace alvo do campo `ID` de `spec.md`.
- Selecionar modo `namespaced` quando houver marcador da spec alvo e modo
  `legacy` quando não houver.
- Isolar cobertura, contagens e órfãos no modo namespaced.
- Preservar cobertura legada e rebaixar órfãos ambíguos a aviso no modo
  legacy.
- Expor namespace e modo no relatório humano e JSON.
- Migrar todos os marcadores vinculados à SPEC-0015 no arquivo de teste e nas
  referências normativas da própria spec.

#### Fora de escopo

- Migrar em massa specs concluídas e seus testes.
- Renumerar histórias, requisitos ou critérios.
- Alterar Gherkin, evidências de tarefas ou aceite fora da seleção de testes.
- Alterar aplicação, API, banco, pipeline ou frontend.
- Publicar a mudança no repositório upstream do Specsfy.

#### Atores

- **Pessoa mantenedora**: executa gates e precisa confiar que a cobertura
  pertence à spec validada.
- **Automação de CI/Specsfy**: consome código de saída e JSON sem interação.

### 4. Princípios e restrições do projeto

- **PR-001**: `spec.md` permanece a fonte normativa e fornece o namespace por
  seu campo `ID`.
- **PR-002**: argumentos posicionais, flags, campos JSON existentes e códigos
  de saída devem permanecer compatíveis.
- **PR-003**: o parser não executa conteúdo dos arquivos e mantém a mesma
  fronteira de leitura local.
- **PR-004**: uma spec migrada deve migrar todos os seus marcadores de uma vez;
  marcadores legados são ignorados no modo namespaced.
- **PR-005**: os testes de contrato ficam em `tests/` para serem rastreáveis;
  seus marcadores namespaced não podem contaminar outras specs.

### 5. Histórias de usuário

#### US-001 — Validar evidências no namespace correto (P1)

Como pessoa mantenedora, quero que cada evidência de teste seja atribuída à sua
spec, para confiar nos gates mesmo quando diferentes specs reutilizam IDs
locais.

**Por que P1**: a colisão já bloqueia o planejamento da SPEC-0015 e invalida a
confiabilidade do verificador global.
**Teste independente**: executar a suíte Node focal com fixtures temporárias
contendo duas specs e IDs locais repetidos; cada invocação deve produzir
cobertura e órfãos apenas do escopo aplicável.
**Requisitos**: FR-001, FR-002, FR-003, NFR-001, NFR-002

### 6. Cenários BDD de aceite

#### AC-001 — Isolamento entre namespaces

**Cobre**: US-001, FR-001, FR-003, NFR-001, NFR-002

```gherkin
@US-001 @FR-001 @FR-003 @NFR-001 @NFR-002 @AC-001
Feature: Rastreabilidade por especificação

  Scenario: IDs repetidos pertencem somente ao namespace alvo
    Given duas specs reutilizam US-001 e AC-001 em marcadores namespaced
    When o auditor valida uma das specs
    Then somente os marcadores com o ID dessa spec contam como cobertura
    And os marcadores da outra spec não são reportados como órfãos
```

#### AC-002 — Compatibilidade com spec legada

**Cobre**: US-001, FR-002, NFR-001

```gherkin
@US-001 @FR-002 @NFR-001 @AC-002
Feature: Compatibilidade durante migração gradual

  Scenario: Spec sem namespace alvo usa marcadores legados
    Given uma spec sem qualquer marcador com seu namespace
    And existem marcadores SPECSFY sem namespace
    When o auditor valida essa spec
    Then os IDs legados continuam contando como cobertura
    And IDs legados estranhos são avisos não bloqueantes
```

#### AC-003 — Órfão da spec alvo continua bloqueante

**Cobre**: US-001, FR-001, FR-003, NFR-002

```gherkin
@US-001 @FR-001 @FR-003 @NFR-002 @AC-003
Feature: Integridade do namespace alvo

  Scenario: Marcador namespaced referencia ID inexistente
    Given um marcador do namespace alvo contém um ID local sintaticamente válido que a spec não define
    When o auditor valida essa spec
    Then o ID não definido é reportado como marcador órfão
    And o comando termina com código diferente de zero
```

#### AC-004 — Marcador legado não cria falsa cobertura em spec migrada

**Cobre**: US-001, FR-001, FR-002, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @AC-004
Feature: Migração sem mistura de modos

  Scenario: Spec namespaced ainda convive com testes legados
    Given existe ao menos um marcador do namespace alvo
    And um marcador legado contém outro requisito da mesma spec
    When o auditor valida a spec
    Then o auditor usa somente o modo namespaced
    And o requisito presente apenas no marcador legado permanece descoberto
```

#### AC-005 — Contrato de relatório e spec inválida

**Cobre**: US-001, FR-002, FR-003, NFR-002

```gherkin
@US-001 @FR-002 @FR-003 @NFR-002 @AC-005
Feature: Contrato operacional do auditor

  Scenario: Relatório identifica modo e exige ID de spec válido
    Given uma invocação válida e outra spec sem campo ID válido
    When o auditor é executado em formato humano e JSON
    Then a invocação válida informa namespace e modo preservando os campos existentes
    And a spec inválida termina com erro de uso sem varrer os testes
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O auditor deve reconhecer exclusivamente como marcador
  namespaced a forma `SPECSFY: SPEC-NNNN <IDs>` e, quando encontrar ao menos
  um marcador da spec alvo, considerar apenas os IDs desses marcadores para
  cobertura, contagens e órfãos.
- **FR-002**: Na ausência de marcador do namespace alvo, o auditor deve manter
  marcadores `SPECSFY:` sem namespace e tags `@US|FR|NFR|AC-NNN` como cobertura
  legada, reportando IDs não definidos como aviso não bloqueante.
- **FR-003**: O auditor deve extrair `SPEC-NNNN` da tabela de metadados,
  rejeitar spec sem ID válido antes da varredura e informar `spec_id` e
  `marker_mode` no JSON e no relatório humano sem remover campos existentes.

#### Não funcionais

- **NFR-001**: A mudança deve preservar argumentos, flags, campos JSON
  existentes e códigos de saída para invocações legadas válidas.
  **Verificação**: testes de contrato AC-001, AC-002 e AC-004, mais execução de
  `verify_repo.mjs`.
- **NFR-002**: O resultado deve ser determinístico e obtido em uma única
  varredura da raiz, sem executar o conteúdo lido nem ampliar os diretórios
  aceitos.
  **Verificação**: inspeção do algoritmo e testes AC-001, AC-003 e AC-005.

#### Erros e casos-limite

- Spec sem `| ID | SPEC-NNNN |` válido → mensagem de erro e exit code 2.
- Namespace estrangeiro → ignorado no modo namespaced da spec alvo.
- Marcador legado durante modo namespaced → ignorado para impedir falsa
  cobertura.
- ID inválido dentro do namespace alvo → órfão bloqueante e exit code 1.
- Nenhum namespace alvo e IDs legados ambíguos → aviso, sem falha por órfão.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- `check_traceability.mjs` é um script ESM Node.js sem dependências externas.
- O script coleta arquivos, extrai marcadores linha a linha e agrega
  `locations` antes de calcular cobertura, mínimos, órfãos e cadeia completa.
- `verify_repo.mjs` chama o script com `node`, caminhos posicionais e flags.

#### Arquitetura e módulos

- Separar a análise de cada linha em registros com `specId`, `ids` e
  `location`.
- Extrair `targetSpecId` da tabela Markdown da spec antes de caminhar a raiz.
- Realizar uma única coleta de registros; depois selecionar:
  - `namespaced`: registros cujo `specId === targetSpecId`;
  - `legacy`: somente registros sem `specId`, quando não existir registro do
    namespace alvo.
- Calcular `locations`, `records`, cobertura e órfãos sobre a seleção.
- Manter órfãos selecionados bloqueantes somente no modo namespaced; no modo
  legacy expô-los também como `legacy_orphan_warnings` e não incluí-los na
  condição de falha.

#### Migrations

- Não aplicável; nenhuma persistência ou schema.

#### Models

- Registro efêmero interno: `{ specId: string | null, ids: Set<string>,
  location: string }`. Não há model persistente.

#### Controllers e casos de uso

- Não aplicável; a entrada permanece CLI e o caso de uso está no próprio
  `check_traceability.mjs`.

#### Views e experiência

- Não aplicável; não existe interface para pessoas.

#### Queries e repositórios

- Não aplicável; apenas leitura local dos arquivos já aceitos pelo walker.

#### Jobs e processamento assíncrono

- Não aplicável.

#### Estrutura de arquivos

```text
.agents/skills/specsfy-06-tdd-bdd/scripts/
  check_traceability.mjs
specs/defined/0015-corrida-entre-has-active-execution-e-o-insert-de-execution/
  spec.md
specs/<estado>/0016-namespacear-marcadores-specsfy-por-spec/
  spec.md
tests/
  check_traceability.test.mjs
  test_app_executions.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Spec alvo | `SPEC-NNNN` | extraída do metadado `ID`; obrigatória | seleciona zero ou mais marcadores |
| Marcador | arquivo + linha | namespace opcional e conjunto de IDs locais | pertence a uma spec explícita ou ao legado |
| Resultado | invocação | modo, cobertura, órfãos, avisos e código de saída | deriva da spec e dos marcadores selecionados |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Auditor | sem registros alvo | fim da coleta | `legacy` | somente registros sem namespace são usados |
| Auditor | ao menos um registro alvo | fim da coleta | `namespaced` | somente registros da spec alvo são usados |

#### Migração e retenção

- Não há retenção. A migração é textual e gradual; a SPEC-0015 é o piloto e
  as specs legadas permanecem válidas.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega altera somente um comando de
  verificação consumido por mantenedores e automação.

#### Stack e convenções de interface

- Não aplicável; nenhum frontend, rota ou componente visual é afetado.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável.

#### Menus e navegação principal

- Não aplicável.

#### Formulários e ações

- Não aplicável.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável; não existem blocos React nesta entrega.

#### Estados e acessibilidade

- Não aplicável; não há superfície visual ou interação por teclado.

#### Contrato CRUD

- Não aplicável; a entrega não administra registros.

#### Revisão visual durante o desenvolvimento

- Não aplicável; não há interface para revisar.

#### APIs expostas

- CLI preservada: `node check_traceability.mjs <spec> <root> [--kinds ...]
  [--minimum-tests N] [--json] [--full-chain]`.
- JSON adiciona `spec_id`, `marker_mode` e `legacy_orphan_warnings`, mantendo
  todas as chaves existentes.
- Saída humana adiciona uma linha de modo/namespace e mantém os rótulos atuais.

#### APIs externas utilizadas

- Nenhuma.

#### Documentação das APIs consultadas

- Nenhuma documentação externa.

#### Eventos e outros contratos

- Formato novo: `SPECSFY: SPEC-NNNN US-NNN FR-NNN NFR-NNN AC-NNN`.
- Formato legado: `SPECSFY: US-NNN ...` e tags `@US-NNN` continuam aceitos
  apenas quando a spec alvo ainda não possui marcador namespaced.

### 11. Estratégia TDD

- **Unidade**: `node:test` carrega a CLI real em processo e usa diretórios
  temporários, sem mock do parser ou do filesystem. O carregamento em processo
  evita o `EPERM` imposto pelo sandbox a subprocessos Node.
- **Integração/contrato**: validar stdout, JSON, código de saída e
  compatibilidade da chamada real usada por `verify_repo.mjs`.
- **BDD/aceite**: os cinco cenários da seção 6 orientam casos TDD; arquivos
  `.feature` não serão executados.
- **Runner TDD**: `node --test`, já disponível no runtime Node.js do projeto e
  sem nova dependência.
- **E2E**: executar o checker real contra a SPEC-0015 e `verify_repo.mjs`.
- **Verificação manual**: não aplicável.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-003, NFR-001, NFR-002, AC-001 | AC-001 na seção 6 | caso namespaced isola duas specs em `tests/check_traceability.test.mjs` com marcador da SPEC-0016 | RED em 2026-09-15: checker retornou 1 ao agregar órfãos do namespace estrangeiro | GREEN: namespace estrangeiro ignorado; 6/6 casos focais passaram | SPEC-0016 11/11 e SPEC-0015 9/9 em modo namespaced |
| US-001, FR-002, NFR-001, AC-002 | AC-002 na seção 6 | caso fallback legado não falha por órfão ambíguo no mesmo arquivo | RED em 2026-09-15: checker retornou 1 porque o órfão legado ainda é bloqueante | GREEN: fallback legado retorna 0 e separa aviso de órfão bloqueante | Compatibilidade coberta sem remover campos existentes |
| US-001, FR-001, FR-003, NFR-002, AC-003 | AC-003 na seção 6 | caso órfão do namespace alvo é bloqueante no mesmo arquivo | RED em 2026-09-15: saída não fornece `marker_mode` nem JSON namespaced consumível | GREEN: órfão do alvo retorna 1 e aparece no JSON namespaced | Parser de linha e agregação separados em funções pequenas |
| US-001, FR-001, FR-002, NFR-001, AC-004 | AC-004 na seção 6 | caso marcador legado não cobre spec migrada no mesmo arquivo | RED em 2026-09-15: checker retornou 0 porque misturou o marcador legado na cobertura | GREEN: requisito apenas legado permanece descoberto no modo namespaced | Migração piloto completa dos quatro marcadores da SPEC-0015 |
| US-001, FR-002, FR-003, NFR-002, AC-005 | AC-005 na seção 6 | casos contrato JSON/humano e ID ausente no mesmo arquivo | RED em 2026-09-15: saída não informa modo e spec sem ID retorna 1 em vez do erro de uso 2 | GREEN: saída humana/JSON informa modo e spec sem ID retorna 2 | `.mjs` incluído no walker após RED focal adicional de 5 casos |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001, FR-003, NFR-001, NFR-002 | AC-001 | Unidade/contrato | `node tests/check_traceability.test.mjs` | Passed: 6/6 |
| FR-002, NFR-001 | AC-002 | Unidade/compatibilidade | mesmo comando | Passed: 6/6 |
| FR-001, FR-003, NFR-002 | AC-003 | Unidade/falha | mesmo comando | Passed: 6/6 |
| FR-001, FR-002, NFR-001 | AC-004 | Unidade/migração | mesmo comando | Passed: 6/6; SPEC-0015 9/9 |
| FR-002, FR-003, NFR-002 | AC-005 | Contrato/CLI | mesmo comando | Passed: 6/6; ID ausente retorna 2 |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (2026-09-15)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0016-namespacear-marcadores-specsfy-por-spec/spec.md`
- **Achados**: formato Specsfy/2.0 válido; 1 US, 3 FR, 2 NFR e 5 AC, com ao menos três cenários para cada US/FR/NFR; contrato de compatibilidade, seleção por namespace, fallback, falhas e prova real na SPEC-0015 estão definidos. Nenhum BLOCKER aberto.

#### Gate do Ato II — Plano

- **Resultado**: READY (2026-09-15)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/draft/0016-namespacear-marcadores-specsfy-por-spec/spec.md`
- **Achados**: 6 tarefas ordenadas; T001–T003 materializaram 6 casos TDD antes de T004. `node tests/check_traceability.test.mjs` → 0 passed, 6 failed por ausência das capacidades planejadas antes da implementação. RED válido, sem falha de ambiente; o arquivo foi depois movido para `tests/` para ser descoberto pela rastreabilidade.

#### Gate do Ato III — Entrega

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0016-namespacear-marcadores-specsfy-por-spec/spec.md . --full-chain`
- **Achados**: checker conjunto 12/12, SPEC-0016 11/11 e SPEC-0015 9/9;
  Ruff verde; baseline Python 313 passed, 1 skipped e 4 REDs intencionais da
  SPEC-0015 desmarcados. A SPEC-0017 reconciliou os contratos históricos e
  `verify_repo.mjs .` passou para todas as specs 0001–0017.

### 14. Tarefas

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Provar isolamento namespaced e ausência de mistura com legado em `tests/check_traceability.test.mjs` — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-001, AC-004 — Depends: none
  - [x] **PREP**: Confirmada sintaxe, seleção de modo e campos do contrato nas seções 6–10.
  - [x] **EXECUTE**: Criadas fixtures temporárias para namespaces concorrentes e marcador legado, usando o checker real como subprocesso.
  - [x] **VERIFY**: RED observado: o checker misturou IDs estrangeiros e aceitou falsa cobertura legada.
  - [x] **VISUAL**: Não aplicável; a tarefa testa uma CLI sem interface visual.
  - [x] **EVIDENCE**: Comando e causas do RED registrados nas seções 11–13.
  - [x] **IMPROVE**: Fixtures usam `mkdtemp` e `finally` com remoção, sem contaminar a raiz.

- [x] T002 [TEST] [TDD] [US-001] Provar fallback legado compatível e contrato aditivo em `tests/check_traceability.test.mjs` — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-002, AC-005 — Depends: none
  - [x] **PREP**: Confirmado que a fixture não contém marcador do namespace alvo.
  - [x] **EXECUTE**: Criado caso com cobertura legada suficiente e ID estranho ambíguo.
  - [x] **VERIFY**: RED observado: órfão legado ainda bloqueia e o modo não é declarado.
  - [x] **VISUAL**: Não aplicável; a tarefa testa uma CLI sem interface visual.
  - [x] **EVIDENCE**: stdout/JSON, código de saída e causa do RED registrados.
  - [x] **IMPROVE**: O caso distingue `legacy_orphan_warnings` de `orphan_markers`.

- [x] T003 [TEST] [TDD] [US-001] Provar órfão alvo, rejeição de spec sem ID e determinismo em `tests/check_traceability.test.mjs` — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-003, AC-005 — Depends: none
  - [x] **PREP**: Confirmados códigos de saída 1 para gap e 2 para uso/spec inválida.
  - [x] **EXECUTE**: Criados casos para órfão namespaced, JSON/humano e metadado ID ausente.
  - [x] **VERIFY**: RED observado: namespace e validação do ID ainda não existem.
  - [x] **VISUAL**: Não aplicável; a tarefa testa uma CLI sem interface visual.
  - [x] **EVIDENCE**: Resultados individuais e vínculos AC-003/AC-005 registrados.
  - [x] **IMPROVE**: Assertivas usam conjuntos/arrays ordenados do contrato, não ordem de leitura dos arquivos.

#### Fase 2 — US-001 Validar evidências no namespace correto (P1)

**Objetivo**: tornar cobertura e órfãos confiáveis por spec sem quebrar o acervo legado.
**Teste independente**: `node tests/check_traceability.test.mjs` termina com todos os casos aprovados.

- [x] T004 [CODE] [US-001] Implementar parser, seleção de modo e relatório em `.agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs` — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-001, AC-002, AC-003, AC-004, AC-005 — Depends: T001, T002, T003
  - [x] **PREP**: REDs T001–T003 confirmados; assinatura, flags e campos existentes preservados.
  - [x] **EXECUTE**: ID alvo, coleta única, seleção de modo, órfãos bloqueantes e avisos legados implementados.
  - [x] **VERIFY**: `node tests/check_traceability.test.mjs` → 6 passed; saída humana e JSON conferidas pelos casos.
  - [x] **VISUAL**: Não aplicável; a mudança não possui interface.
  - [x] **EVIDENCE**: GREEN, arquivos e documentação reconstruída registrados.
  - [x] **IMPROVE**: Parser foi decomposto em funções pequenas e permanece sem dependências externas; harness carrega a CLI no mesmo processo porque subprocessos Node são bloqueados pelo sandbox com `EPERM`.
  <!-- specsfy:evidence {"task":"T004","refs":["US-001","FR-001","FR-002","FR-003","NFR-001","NFR-002","AC-001","AC-002","AC-003","AC-004","AC-005"],"files":[".agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs","tests/check_traceability.test.mjs","docs/testing.md"],"commands":[{"run":"node tests/check_traceability.test.mjs","exit":0},{"run":"node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check","exit":0}]} -->

- [x] T005 [CODE] [US-001] Validar a migração piloto do namespace contra a SPEC-0015, em andamento numa branch própria (spec/0015-corrida-entre-has-active-execution-e-o-insert-de-execution) — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-004 — Depends: T004
  - [x] **PREP**: Mapeados somente os quatro testes e as cinco referências normativas pertencentes à SPEC-0015, então em `specs/defined/0015-.../spec.md` e `tests/test_app_executions.py` no checkout local daquela branch.
  - [x] **EXECUTE**: `SPEC-0015` inserido nos quatro marcadores da fatia e nas referências normativas correspondentes, no checkout local da branch `spec/0015-...`. Nota de proveniência: por `.specsfy/RULES.md` ("uma branch nunca carrega duas specs"), essa edição pertence à SPEC-0015 e é commitada e mantida pela própria branch dela, não por esta — este item registra apenas a validação piloto do mecanismo de namespace desta spec contra um caso real em andamento.
  - [x] **VERIFY**: Checker real, rodado naquele checkout → modo namespaced, 9/9 IDs cobertos em 47 arquivos, `RESULTADO: OK`.
  - [x] **VISUAL**: Não aplicável; migração textual de testes e spec.
  - [x] **EVIDENCE**: Resultado isolado do checker registrado abaixo; os arquivos de teste/spec da SPEC-0015 não fazem parte do pacote desta spec (vivem em `spec/0015-...`).
  - [x] **IMPROVE**: Busca focal confirmou que todos os quatro marcadores da SPEC-0015 possuem namespace; marcadores de outras fatias no mesmo arquivo foram preservados.
  <!-- specsfy:evidence {"task":"T005","refs":["US-001","FR-001","FR-002","NFR-001","AC-001","AC-004"],"files":[".agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs"],"commands":[{"run":"node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs <checkout-local-de-spec/0015-...>/spec.md . (validação piloto fora do pacote desta spec)","exit":0}]} -->

#### Fase final — Qualidade

- [x] T006 [TEST] Executar regressão e enforcement a partir de `tests/check_traceability.test.mjs` — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-001, AC-002, AC-003, AC-004, AC-005 — Depends: T004, T005
  - [x] **PREP**: Suíte focal, checkers das SPEC-0015/0016, regressão Python, Ruff, `verify_repo.mjs`, documentador e monitor identificados.
  - [x] **EXECUTE**: Todos os comandos previstos foram executados sem mudar aplicação ou banco.
  - [x] **VERIFY**: Checks focais, baseline e `verify_repo.mjs .` passam após a reconciliação formal da SPEC-0017.
  - [x] **VISUAL**: Não aplicável; a entrega não possui interface visual.
  - [x] **EVIDENCE**: Registrados 6/6 testes Node, 11/11 e 9/9 IDs, Ruff verde, 313 testes Python verdes e o diagnóstico do enforcement global.
  - [x] **IMPROVE**: Teste movido para `tests/`, extensão `.mjs` coberta por RED/GREEN e dívida histórica capturada separadamente sem fabricar evidência retroativa.

### 15. Ordem de execução

- Caminho crítico: T001/T002/T003 → T004 → T005 → T006.
- Tarefas paralelas: T001, T002 e T003 podem ser escritas em paralelo, mas o
  RED focal é registrado num único comando antes de T004.
- Estratégia de MVP: entregar isolamento e compatibilidade numa única fatia,
  usando a SPEC-0015 como prova real.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Node.js disponível, checker atual e consumidor `verify_repo.mjs`.
- A SPEC-0015 depende desta entrega antes de recuperar seu Plan Gate.

#### Riscos

- Migração parcial de uma spec reduz sua cobertura aparente → migrar todos os
  marcadores daquela spec numa única tarefa e verificar IDs descobertos.
- Consumidor externo depende da saída textual → preservar rótulos existentes e
  apenas acrescentar identificação de modo.
- Legado continua semanticamente ambíguo → avisar sem bloquear e exigir
  namespace para specs novas/migradas.

#### Suposições

- `SPEC-NNNN` permanece único no projeto e presente na tabela inicial de cada
  spec válida.
- `node:test` é suficiente e não requer dependência adicional.
- Marcadores `@ID` sem `SPEC-NNNN` permanecem exclusivamente legados.

### 17. Decisões

- **DEC-001**: Adotar `SPECSFY: SPEC-NNNN <IDs>` — torna a posse explícita sem
  alterar os IDs locais.
- **DEC-002**: Ativar modo namespaced pela presença de marcador da spec alvo —
  evita misturar evidência nova e legada numa migração incompleta.
- **DEC-003**: No fallback legado, órfãos são avisos não bloqueantes — não há
  informação suficiente para atribuí-los corretamente.
- **DEC-004**: Manter o teste em `tests/` e namespacear todos os seus casos —
  o walker encontra a evidência da SPEC-0016 e ignora esses marcadores ao
  validar qualquer outra spec namespaced.
- **DEC-005**: Migrar apenas a SPEC-0015 nesta fatia — prova o contrato real e
  mantém a migração histórica fora do escopo.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
