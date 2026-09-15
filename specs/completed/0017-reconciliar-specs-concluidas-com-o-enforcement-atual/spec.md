# Especificação integrada: Reconciliar specs concluídas com o enforcement atual

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0017 |
| Slug | 0017-reconciliar-specs-concluidas-com-o-enforcement-atual |
| Status | Complete |
| Effort | 2 |
| Effort updated at | 2026-09-15 |
| Effort rationale | Três correções localizadas em validadores Node.js, com fixtures Git temporárias, compatibilidade retroativa e regressão global. Sem aplicação, banco ou interface. |
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

O gate global aplica contratos recentes a specs históricas e reprova entregas
concluídas por três incompatibilidades: arquivos de evidence posteriormente
movidos, ausência legítima de research externo e falta de vínculo de evidence
por ID em marcadores legados. Corrigir os documentos históricos fabricaria uma
rastreabilidade que não existia no momento da entrega.

#### Resultado desejado

O enforcement reconhece, de forma explícita e auditável, os limites do contrato
histórico sem relaxar specs ativas ou namespaced. O `verify_repo.mjs` volta a
ser um gate confiável para o repositório inteiro e a SPEC-0016 pode concluir.

#### Métricas de sucesso

- 100% das specs `Complete` com caminhos movidos passam somente quando o Git
  comprova o caminho na ancestralidade da branch atual.
- 100% das specs ativas continuam exigindo arquivos presentes no checkout.
- Specs sem claim formal nem artefato indexado passam com zero researchs.
- O modo namespaced mantém a cadeia estrita por ID; o legado não falha somente
  pela ausência de evidence por ID.
- `verify_repo.mjs` termina com código zero no repositório atual em até 300 s.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: Por que `verify_evidence.mjs` reprova as specs 0001–0007? → Os
  caminhos citados existiam antes da reorganização de `src/` para
  `src/pipeline/`; os arquivos atuais equivalentes existem e o Git preserva os
  caminhos originais.
- **R-002**: Por que `load_research.mjs` reprova specs sem pesquisa externa? → O
  loader exige ao menos um artefato indexado mesmo sem claim formal; também não
  acompanha a mudança de pasta de estado da própria spec.
- **R-003**: Por que o full-chain reprova specs legadas? → O vínculo de evidence
  por ID foi introduzido depois dessas specs. `verify_evidence.mjs` já valida a
  materialidade, enquanto specs namespaced podem e devem usar o contrato novo.

#### Fontes e contexto consultados

- `specs/backlog/0021-reconciliar-specs-concluidas-com-o-enforcement-atual.md`.
- `specs/inbox/2026-09-15-163521-reconciliar-specs-concluidas-com-o-enforcement-atual.md`.
- Specs concluídas 0001–0014 e suas evidências versionadas.
- `.agents/skills/specsfy-07-implement/scripts/verify_evidence.mjs`.
- `.agents/skills/specsfy-03-specify/scripts/load_research.mjs`.
- `.agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs`.
- `.agents/skills/specsfy-04-validate/scripts/verify_repo.mjs`.

#### Documentação consultada

- Somente código, histórico Git e documentação local do repositório; nenhuma
  fonte externa foi necessária.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo; as fontes locais consultadas já são versionadas.

#### Dúvidas respondidas

- **Q**: Devemos reescrever evidence histórica? → **A**: Não. A existência do
  caminho será comprovada na ancestralidade Git da branch atual.
- **Q**: Ausência de research é sempre erro? → **A**: Não quando não há claim
  formal nem caminho indexado.
- **Q**: Qual é o corte para a cadeia estrita por ID? → **A**: O modo
  `namespaced`, que torna inequívoca a pertença da evidência à spec.

#### Dúvidas abertas

- Nenhuma lacuna bloqueante.

### 3. Escopo e atores

#### Incluído

- Compatibilidade histórica de arquivos de evidence para specs `Complete`.
- Relato separado dos arquivos aceitos pelo histórico Git.
- Research vazio quando não houver claim formal nem índice.
- Resolução de caminho de research sob estado antigo da mesma spec.
- Regra full-chain distinta para modo legado e namespaced.
- Testes de contrato e execução do gate global real.

#### Fora de escopo

- Alterar evidence inline das specs concluídas ou fabricar atestações.
- Relaxar arquivos ausentes em specs ativas.
- Aceitar histórico de outras branches via `--all` ou caminhos externos.
- Alterar aplicação, banco, API, frontend ou a implementação da SPEC-0015.

#### Atores

- **Pessoa mantenedora**: precisa confiar que o gate distingue legado legítimo
  de entrega ativa incompleta.
- **Automação Specsfy/CI**: consome códigos de saída e relatórios JSON.

### 4. Princípios e restrições do projeto

- **PR-001**: Compatibilidade histórica é exceção explícita somente para
  `Status: Complete`.
- **PR-002**: Paths continuam confinados à raiz, sem traversal ou symlink.
- **PR-003**: Git deve ser invocado com argumentos estruturados, sem shell e
  limitado à ancestralidade da branch atual.
- **PR-004**: Campos JSON existentes e códigos de saída permanecem compatíveis;
  novos dados são aditivos.
- **PR-005**: Nenhum documento histórico é alterado para satisfazer o gate.

### 5. Histórias de usuário

#### US-001 — Auditar legado sem enfraquecer entregas atuais (P1)

Como pessoa mantenedora, quero que o enforcement reconheça evidência histórica
comprovável e ausência legítima de research, para validar o repositório inteiro
sem mascarar falhas em specs ativas ou namespaced.

**Por que P1**: o gate global bloqueia a conclusão da SPEC-0016 e não distingue
incompatibilidade evolutiva de uma entrega realmente incompleta.
**Teste independente**: executar a suíte Node com fixtures temporárias e depois
`verify_repo.mjs`; as exceções legítimas passam e os controles estritos falham.
**Requisitos**: FR-001, FR-002, FR-003, NFR-001, NFR-002

### 6. Cenários BDD de aceite

#### AC-001 — Arquivo histórico comprovado em spec concluída

**Cobre**: US-001, FR-001, FR-003, NFR-001, NFR-002

```gherkin
@US-001 @FR-001 @FR-003 @NFR-001 @NFR-002 @AC-001
Feature: Compatibilidade auditável de evidências

  Scenario: Caminho movido permanece uma evidência histórica válida
    Given uma spec Complete cita um arquivo ausente no checkout atual
    And o caminho existe na ancestralidade Git da branch atual
    When o verificador de evidence é executado
    Then a tarefa é aceita
    And o relatório identifica o caminho como histórico
```

#### AC-002 — Spec ativa permanece estrita

**Cobre**: US-001, FR-001, FR-003, NFR-001

```gherkin
@US-001 @FR-001 @FR-003 @NFR-001 @AC-002
Feature: Fronteira da compatibilidade histórica

  Scenario: História Git não mascara arquivo ausente em entrega ativa
    Given uma spec ativa cita um arquivo ausente no checkout atual
    And o caminho existiu na ancestralidade Git
    When o verificador de evidence é executado
    Then a tarefa é reprovada por arquivo ausente
```

#### AC-003 — Research legitimamente vazio

**Cobre**: US-001, FR-002, FR-003, NFR-002

```gherkin
@US-001 @FR-002 @FR-003 @NFR-002 @AC-003
Feature: Research proporcional à investigação

  Scenario: Spec sem claim nem índice não fabrica artefato
    Given uma spec sem ResearchClaim formal e sem caminho de research indexado
    When o loader de research é executado
    Then o comando termina com sucesso
    And retorna zero artefatos
```

#### AC-004 — Caminho acompanha a mudança de estado da mesma spec

**Cobre**: US-001, FR-002, NFR-001, NFR-002

```gherkin
@US-001 @FR-002 @NFR-001 @NFR-002 @AC-004
Feature: Research preservado entre estados

  Scenario: Índice antigo resolve para o pacote atual
    Given a spec indexa research sob um estado anterior do mesmo slug
    And o artefato existe no diretório research do estado atual
    When o loader de research é executado
    Then o artefato atual é carregado sem aceitar referência a outra spec
```

#### AC-005 — Corte explícito entre cadeia legada e namespaced

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-001 @NFR-002 @AC-005
Feature: Enforcement evolutivo por modo de marcador

  Scenario: Evidence por ID é obrigatória somente no modo namespaced
    Given uma spec legada e uma spec namespaced têm teste e tarefa por ID
    And nenhuma tem marcador de evidence por ID
    When full-chain é executado para ambas
    Then a spec legada não falha somente por essa ausência
    And a spec namespaced permanece reprovada
    And o gate global do repositório passa após as reconciliações
```

### 7. Requisitos

#### Funcionais

- **FR-001**: `verify_evidence.mjs` deve aceitar arquivo ausente somente quando
  a spec tiver `Status: Complete`, o caminho for seguro e `git log -- <path>`
  comprovar sua existência na ancestralidade da branch atual; o JSON deve
  distinguir arquivos atuais de históricos.
- **FR-002**: `load_research.mjs` deve aceitar zero artefatos quando não houver
  `ResearchClaim` formal nem caminho indexado e deve remapear um índice sob
  outro estado do mesmo slug para o diretório atual, preservando o sufixo em
  `research/` e rejeitando outra spec.
- **FR-003**: `check_traceability.mjs --full-chain` deve exigir teste e tarefa
  por ID nos dois modos, exigir evidence por ID no modo `namespaced` e delegar
  a materialidade ao `verify_evidence.mjs` no modo `legacy`.

#### Não funcionais

- **NFR-001**: Paths devem permanecer confinados à raiz; symlinks e traversal
  continuam recusados; Git deve ser chamado sem shell, sem `--all` e sem
  executar conteúdo. **Verificação**: AC-001, AC-002, AC-004 e inspeção.
- **NFR-002**: As mudanças devem preservar interfaces CLI, campos JSON
  existentes e códigos de saída, adicionando somente informação compatível; o
  gate global deve terminar em até 300 s. **Verificação**: AC-001, AC-003,
  AC-004, AC-005 e regressão global.

#### Erros e casos-limite

- Git indisponível, repositório raso sem o caminho ou saída vazia → evidence
  histórica não é aceita.
- Spec ativa com arquivo ausente → falha mesmo que o Git conheça o caminho.
- Caminho absoluto, traversal, symlink ou fora da raiz → falha.
- Claim formal sem evidence local ou índice inseguro → research falha.
- Índice sob slug de outra spec → não é remapeado e falha como inseguro.
- Spec namespaced sem evidence por ID → full-chain permanece bloqueante.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Os três validadores são scripts ESM Node.js sem dependências externas.
- `verify_repo.mjs` os orquestra por processo filho e preserva cada resultado.
- Os documentos históricos usam Evidence Contract 1 e marcadores legados.

#### Arquitetura e módulos

- Em `verify_evidence.mjs`, ler o status da spec e consultar Git apenas quando
  um caminho seguro estiver ausente em uma spec concluída. Expor
  `historical_files` de modo aditivo.
- Em `load_research.mjs`, separar a ausência legítima de índice da referência
  inválida e normalizar somente o prefixo de estado da própria spec.
- Em `check_traceability.mjs`, condicionar apenas a lacuna `evidence` do
  full-chain ao `marker_mode`; cobertura de teste e tarefa permanece comum.
- Cobrir os contratos por fixtures temporárias, incluindo um repositório Git
  descartável para provar ancestralidade sem depender do histórico real.

#### Migrations

- Não aplicável; nenhuma persistência ou schema é alterado.

#### Models

- Não há model persistente. O resultado de evidence ganha uma coleção aditiva
  de paths históricos aceitos.

#### Controllers e casos de uso

- Não aplicável; as entradas permanecem CLIs locais.

#### Views e experiência

- Não aplicável; não há interface para pessoas.

#### Queries e repositórios

- Não aplicável; a única consulta nova é `git log` sobre caminho literal e
  seguro, executada no repositório da spec.

#### Jobs e processamento assíncrono

- Não aplicável.

#### Estrutura de arquivos

```text
.agents/skills/specsfy-03-specify/scripts/
  load_research.mjs
.agents/skills/specsfy-06-tdd-bdd/scripts/
  check_traceability.mjs
.agents/skills/specsfy-07-implement/scripts/
  verify_evidence.mjs
specs/<estado>/0017-reconciliar-specs-concluidas-com-o-enforcement-atual/
  spec.md
tests/
  specsfy_legacy_enforcement.test.mjs
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Spec auditada | `SPEC-NNNN` | status e modo de marcador | governa a política aplicável |
| Evidence de arquivo | path relativo | atual ou histórico comprovado | pertence a uma tarefa |
| Research indexado | path relativo | opcional sem claim; confinado ao pacote | pertence à spec |
| Lacuna full-chain | ID + classe | teste, tarefa ou evidence | evidence depende do modo |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Evidence ausente | spec `Complete` | Git comprova path | histórico aceito | path seguro na branch atual |
| Evidence ausente | spec ativa | verificação | rejeitado | Git não altera o resultado |
| Research | sem claim e sem índice | carregamento | vazio válido | nenhum artefato fabricado |
| Full-chain | modo legacy | evidence por ID ausente | materialidade delegada | teste e tarefa seguem obrigatórios |

#### Migração e retenção

- Não há migração de dados. Specs históricas e commits permanecem imutáveis.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega afeta somente comandos de
  governança consumidos por mantenedores e automação.

#### Stack e convenções de interface

- Não aplicável; nenhum frontend é alterado.

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

- Não aplicável; não há React nesta entrega.

#### Estados e acessibilidade

- Não aplicável; não há superfície visual.

#### Contrato CRUD

- Não aplicável; nenhum registro é administrado.

#### Revisão visual durante o desenvolvimento

- Não aplicável; cada tarefa deve registrar que não existe interface afetada.

#### APIs expostas

- As três CLIs preservam argumentos, flags, saída humana e campos JSON atuais.
- `verify_evidence.mjs --json` adiciona `historical_files` sem remover chaves.

#### APIs externas utilizadas

- Git CLI local: `git log --format=%H -- <path>`, sem shell e sem rede.

#### Documentação das APIs consultadas

- Contratos inferidos dos scripts locais e validados por testes de processo.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: decisões de compatibilidade exercitadas pelas CLIs em fixtures.
- **Integração/contrato**: processos Node e Git temporário com saídas e exit
  codes reais.
- **BDD/aceite**: AC-001 a AC-005 orientam casos TDD sem arquivos `.feature`.
- **Runner TDD**: `node --test tests/specsfy_legacy_enforcement.test.mjs`.
- **E2E**: `node .agents/skills/specsfy-04-validate/scripts/verify_repo.mjs`.
- **Verificação manual**: não aplicável.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-003, NFR-001, NFR-002, AC-001, AC-002 | AC-001 e AC-002 | `tests/specsfy_legacy_enforcement.test.mjs` — evidence histórica e fronteira ativa | RED: Complete falha no path histórico; controle ativo passa | GREEN: histórico aceito e ativo rejeitado | traversal rejeitado; regressão focal verde |
| US-001, FR-002, FR-003, NFR-001, NFR-002, AC-003, AC-004 | AC-003 e AC-004 | `tests/specsfy_legacy_enforcement.test.mjs` — research vazio e relocação | RED: ambos falham pelo contrato antigo | GREEN: vazio e relocação passam | outra spec rejeitada; regressão focal verde |
| US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-005 | AC-005 | `tests/specsfy_legacy_enforcement.test.mjs` — full-chain legado/namespaced | RED: legado falha; controle namespaced bloqueia como esperado | GREEN: legado passa e namespaced segue bloqueante | checker anterior 6/6; gate global verde |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001, FR-003, NFR-001, NFR-002 | AC-001 | Contrato | `node --test tests/specsfy_legacy_enforcement.test.mjs` | Passed; histórico e traversal exercitados |
| FR-001, FR-003, NFR-001 | AC-002 | Contrato negativo | mesmo comando focal | Passed; spec ativa rejeitada |
| FR-002, FR-003, NFR-002 | AC-003 | Contrato | mesmo comando focal | Passed; zero artefatos |
| FR-002, NFR-001, NFR-002 | AC-004 | Contrato de path | mesmo comando focal | Passed; mesma spec aceita e outra rejeitada |
| FR-001, FR-002, FR-003, NFR-001, NFR-002 | AC-005 | Integração/regressão | comando focal e `verify_repo.mjs .` | Passed; 12/12 focais e gate global verde |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/in-progress/0017-reconciliar-specs-concluidas-com-o-enforcement-atual/spec.md`
- **Achados**: Specsfy/2.0 válida em Draft; problema, fronteiras, requisitos,
  segurança e cinco cenários de aceite estão completos e sem lacunas.

#### Gate do Ato II — Plano

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0017-reconciliar-specs-concluidas-com-o-enforcement-atual/spec.md`
- **Achados**: 6 casos executados; 4 REDs válidos nas três lacunas e 2 controles
  negativos verdes. Sete tarefas cobrem os 11 IDs com dependências explícitas.

#### Gate do Ato III — Entrega

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0017-reconciliar-specs-concluidas-com-o-enforcement-atual/spec.md . --full-chain`
- **Achados**: 12/12 testes Node passaram; 313 testes Python passaram, 1
  pulado e 4 REDs intencionais da SPEC-0015 foram desmarcados; Ruff, docs,
  monitor, diff-check e `verify_repo.mjs .` passaram.

### 14. Tarefas

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Provar compatibilidade Git e fronteira de status em tests/specsfy_legacy_enforcement.test.mjs — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-001, AC-002 — Depends: none
  - [x] **PREP**: Confirmar escopo, IDs, dependências e baseline dos AC-001 e AC-002.
  - [x] **EXECUTE**: Criar fixtures Git descartáveis e casos namespaced com marcador próprio `SPECSFY: SPEC-0017`.
  - [x] **VERIFY**: RED observado na spec Complete; o controle de spec ativa passou.
  - [x] **VISUAL**: Não aplicável; a tarefa altera somente testes de CLI sem interface.
  - [x] **EVIDENCE**: `node --test tests/specsfy_legacy_enforcement.test.mjs` → exit 1; falha no AC-001.
  - [x] **IMPROVE**: Controle ativo confirma a fronteira; Git insuficiente permanece falha segura por desenho.

- [x] T002 [TEST] [TDD] [US-001] Provar research vazio e relocação segura em tests/specsfy_legacy_enforcement.test.mjs — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-003, AC-004 — Depends: none
  - [x] **PREP**: Confirmar escopo, IDs, dependências e baseline dos AC-003 e AC-004.
  - [x] **EXECUTE**: Criar fixtures sem claim/índice e com índice sob estado anterior da mesma spec.
  - [x] **VERIFY**: RED observado nos dois contratos ainda ausentes.
  - [x] **VISUAL**: Não aplicável; a tarefa altera somente testes de CLI sem interface.
  - [x] **EVIDENCE**: Comando focal → exit 1; falhas em AC-003 e AC-004.
  - [x] **IMPROVE**: O plano mantém referências a outra spec fora do remapeamento seguro.

- [x] T003 [TEST] [TDD] [US-001] Provar o corte legacy/namespaced do full-chain em tests/specsfy_legacy_enforcement.test.mjs — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-005 — Depends: none
  - [x] **PREP**: Confirmar escopo, IDs, dependências e baseline do AC-005.
  - [x] **EXECUTE**: Criar fixtures equivalentes nos modos legacy e namespaced sem evidence por ID.
  - [x] **VERIFY**: RED observado apenas no legado; namespaced continua bloqueante.
  - [x] **VISUAL**: Não aplicável; a tarefa altera somente testes de CLI sem interface.
  - [x] **EVIDENCE**: Comando focal → exit 1; falha legacy e controle namespaced verde.
  - [x] **IMPROVE**: Fixtures preservam teste e tarefa por ID nos dois modos.

#### Fase 2 — US-001 Auditar legado sem enfraquecer entregas atuais (P1)

**Objetivo**: tornar o gate global compatível com provas históricas auditáveis,
mantendo specs ativas e namespaced sob os contratos estritos.
**Teste independente**: `node --test tests/specsfy_legacy_enforcement.test.mjs`.

- [x] T004 [CODE] [US-001] Implementar evidence histórica em .agents/skills/specsfy-07-implement/scripts/verify_evidence.mjs — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-001, AC-002, AC-005 — Depends: T001, T002, T003
  - [x] **PREP**: REDs, status e política de path seguro confirmados.
  - [x] **EXECUTE**: Ancestralidade consultada sem shell e `historical_files` adicionado ao relatório.
  - [x] **VERIFY**: Casos históricos, ativos e traversal passaram.
  - [x] **VISUAL**: Não aplicável; o arquivo é um validador CLI sem interface.
  - [x] **EVIDENCE**: Suíte Node focal → 12/12 no conjunto com regressão da SPEC-0016.
  - [x] **IMPROVE**: `--literal-pathspecs` impede interpretação de pathspec e Git só roda para ausente elegível.
  <!-- specsfy:evidence {"task":"T004","refs":["US-001","FR-001","FR-002","FR-003","NFR-001","NFR-002","AC-001","AC-002","AC-005"],"files":[".agents/skills/specsfy-07-implement/scripts/verify_evidence.mjs"],"commands":[{"run":"node --test tests/specsfy_legacy_enforcement.test.mjs tests/check_traceability.test.mjs","exit":0}]} -->

- [x] T005 [CODE] [US-001] Implementar ausência e relocação de research em .agents/skills/specsfy-03-specify/scripts/load_research.mjs — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-003, AC-004, AC-005 — Depends: T001, T002, T003
  - [x] **PREP**: REDs e diferença entre ausência legítima e índice inválido confirmados.
  - [x] **EXECUTE**: Conjunto vazio elegível e remapeamento do mesmo slug implementados.
  - [x] **VERIFY**: Vazio, relocação e referência a outra spec passaram.
  - [x] **VISUAL**: Não aplicável; o arquivo é um loader CLI sem interface.
  - [x] **EVIDENCE**: Suíte Node focal → 12/12 no conjunto com regressão da SPEC-0016.
  - [x] **IMPROVE**: Claims formais, budgets e confinamento existente foram preservados.
  <!-- specsfy:evidence {"task":"T005","refs":["US-001","FR-001","FR-002","FR-003","NFR-001","NFR-002","AC-003","AC-004","AC-005"],"files":[".agents/skills/specsfy-03-specify/scripts/load_research.mjs"],"commands":[{"run":"node --test tests/specsfy_legacy_enforcement.test.mjs tests/check_traceability.test.mjs","exit":0}]} -->

- [x] T006 [CODE] [US-001] Implementar cadeia compatível em .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-001, AC-002, AC-003, AC-004, AC-005 — Depends: T001, T002, T003
  - [x] **PREP**: RED e contratos da SPEC-0016 confirmados.
  - [x] **EXECUTE**: Somente a lacuna evidence foi condicionada ao modo namespaced.
  - [x] **VERIFY**: Casos legacy/namespaced e 6/6 testes anteriores passaram.
  - [x] **VISUAL**: Não aplicável; o arquivo é um auditor CLI sem interface.
  - [x] **EVIDENCE**: Suíte Node conjunta → 12/12.
  - [x] **IMPROVE**: Teste e tarefa por ID permanecem obrigatórios nos dois modos.
  <!-- specsfy:evidence {"task":"T006","refs":["US-001","FR-001","FR-002","FR-003","NFR-001","NFR-002","AC-001","AC-002","AC-003","AC-004","AC-005"],"files":[".agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs"],"commands":[{"run":"node --test tests/specsfy_legacy_enforcement.test.mjs tests/check_traceability.test.mjs","exit":0}]} -->

**Checkpoint**: a suíte focal passa e cada controle negativo preserva o bloqueio
esperado antes da regressão global.

#### Fase final — Qualidade

- [x] T007 [TEST] [US-001] Executar regressão e gate global em tests/specsfy_legacy_enforcement.test.mjs — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-002, AC-001, AC-002, AC-003, AC-004, AC-005 — Depends: T004, T005, T006
  - [x] **PREP**: Suítes, checks, gates e quatro REDs intencionais da SPEC-0015 identificados.
  - [x] **EXECUTE**: Suítes focais, regressão Python, Ruff, docs, monitor, diff-check e gate global executados.
  - [x] **VERIFY**: `verify_repo.mjs .` passou em 18,7 s, abaixo do limite de 300 s.
  - [x] **VISUAL**: Não aplicável; a entrega não possui interface.
  - [x] **EVIDENCE**: Node 12/12; Python 313 passed, 1 skipped, 4 deselected; gate global PASSED.
  - [x] **IMPROVE**: Nenhuma evidence histórica foi reescrita; controles negativos documentam as fronteiras.
  <!-- specsfy:evidence {"task":"T007","refs":["US-001","FR-001","FR-002","FR-003","NFR-001","NFR-002","AC-001","AC-002","AC-003","AC-004","AC-005"],"files":["tests/specsfy_legacy_enforcement.test.mjs"],"commands":[{"run":"node .agents/skills/specsfy-04-validate/scripts/verify_repo.mjs .","exit":0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001/T002/T003 → T004/T005/T006 → T007 → retomada da
  SPEC-0016.
- Tarefas paralelas: T001–T003 e T004–T006 são independentes dentro de suas
  fases; a execução pode ser serial para preservar evidência clara.
- Estratégia de MVP: entregar os três contratos juntos, pois apenas o conjunto
  torna o gate global verde sem relaxamento indevido.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Git disponível e checkout com histórico local suficiente.
- SPEC-0016 aguarda esta reconciliação para concluir seu Delivery Gate.

#### Riscos

- Checkout raso não contém o path antigo → manter falha segura, sem fallback.
- Arquivo histórico pode anteceder a tarefa → reconhecer a limitação do
  Evidence Contract 1; não equiparar a atestação schema 2.
- Compatibilidade ampla demais enfraquece gates atuais → limitar por status,
  modo de marcador e testes negativos.

#### Suposições

- `Status: Complete` representa entrega encerrada e é o único estado elegível.
- A branch atual é a única fonte legítima de ancestralidade para o gate.

### 17. Decisões

- **DEC-001**: Usar ancestralidade Git do path como prova histórica mínima —
  preserva documentos e rejeita paths nunca versionados; não resolve vínculo
  temporal da tarefa, limitação documentada do contrato antigo.
- **DEC-002**: Permitir research vazio sem claim nem índice — evita artefato
  fictício e mantém claims formais estritos.
- **DEC-003**: Usar `marker_mode` como corte da cadeia por ID — o namespace
  fornece a atribuição inequívoca inexistente nas specs legadas.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes focais, rastreabilidade e `verify_repo.mjs` passam.
- [x] SPEC-0016 pode concluir sem alteração retroativa de suas predecessoras.
