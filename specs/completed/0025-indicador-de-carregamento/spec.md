# Especificação integrada: Indicador de carregamento junto da ação ou área em processamento

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0025 |
| Slug | 0025-indicador-de-carregamento |
| Status | Complete |
| Effort | 4 |
| Effort updated at | 2026-10-05 |
| Effort rationale | Feedback transversal em componentes existentes, sem backend ou persistência novos. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-05 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema
Esperas de ações e dados exibem texto ou skeleton sem círculo de processamento consistente.

#### Resultado desejado
A pessoa percebe a espera junto da ação ou área, mantendo o restante da tela disponível.

#### Métricas de sucesso
Cada espera mapeada mostra círculo enquanto pendente e o remove ao terminar; zero overlays globais novos.

### 2. Research e esclarecimentos

#### Researchs executados
Inspeção local: Spinner existe; estados locais já controlam a maioria das esperas. Abrir conversa, Bases opcionais e sair precisam explicitar a espera existente.

#### Fontes e contexto consultados
- specs/inbox/2026-10-05-170632-indicador-de-carregamento-circulo-girando-durante-qualquer-processamento.md
- specs/backlog/0034-indicador-de-carregamento.md
- PROJECT.md, DESIGNSYSTEM.MD, INTERFACE.md e contexto .specsfy.
- frontend/src/components/ui/ e features auth/workspaces/bases/pessoas/execucoes/assistente.

#### Documentação consultada
Código e manifests locais: React 19, Next 16.3.4, Tailwind 4 e Vitest. Nenhuma API externa consultada.

#### Artefatos de pesquisa armazenados
Evidência local de Chromium em research/revisao-visual/: 72 screenshots, resultados.json e formularios.json; requests simulados, sem dados reais. Logs RED/GREEN, suíte, checks e enforcement preservados em research/verificacao/.

#### Dúvidas respondidas
- **Q**: Onde mostrar? → **A**: Junto da ação ou área, mantendo o restante disponível. Resposta literal “1” normalizada para a opção apresentada na conversa.
- **Q**: Quando mostrar? → **A**: Pedido original: “sempre que estiver executando algo”; inclui esperas visíveis e indexação ativa.

#### Dúvidas abertas
Nenhuma lacuna aplicável.

### 3. Escopo e atores

#### Incluído
Esperas de autenticação/sessão/sair, listas, formulários e exclusões de Workspaces/Bases/Pessoas, consulta, indexação e assistente.

#### Fora de escopo
Novas operações de negócio, percentuais fictícios, cancelamento de jobs, bloqueio global e alterações de API.

#### Atores
- **Pessoa sem sessão**: entrar/definir senha.
- **Owner, admin e member**: operações já permitidas pelo papel.

### 4. Princípios e restrições do projeto

- **PR-001**: Reutilizar primitives, tokens e componentes locais; sem dependência nova.
- **PR-002**: Preservar autorização, confirmação, dados digitados, navegação e erros.
- **PR-003**: Vitest via test:tdd; Gherkin é somente referência.
- **PR-004**: Branch por spec, documentação após implementação e revisão visual.

### 5. Histórias de usuário

#### US-001 — Perceber processamento local (P1)

Como pessoa usuária, quero um círculo junto da operação em andamento para saber que o sistema está trabalhando sem perder acesso ao restante da tela.

**Por que P1**: pedido central.
**Teste independente**: atrasar resposta e observar círculo local até sucesso/falha.
**Requisitos**: FR-001, FR-002, NFR-001

### 6. Cenários BDD de aceite

#### AC-001 — Espera no botão da ação

**Cobre**: US-001, FR-001, FR-002, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @AC-001
Feature: Feedback local de processamento

  Scenario: Espera no botão da ação
    Given um botão com operação em andamento
    When o botão é renderizado
    Then o círculo fica junto do texto e apenas essa ação fica ocupada e indisponível
```

#### AC-002 — Envio e falha do formulário

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-002
Feature: Feedback local de processamento

  Scenario: Envio e falha do formulário
    Given uma pessoa envia um formulário válido
    When a resposta demora e depois falha
    Then o círculo aparece durante a espera e desaparece na falha, com erro e nova tentativa disponíveis
```

#### AC-003 — Carregamento local de dados

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-003
Feature: Feedback local de processamento

  Scenario: Carregamento local de dados
    Given uma listagem ou detalhe está carregando
    When a região de espera é apresentada
    Then o círculo e texto identificam a área sem bloquear outras ações
```

#### AC-004 — Execução assíncrona ativa

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-004
Feature: Feedback local de processamento

  Scenario: Execução assíncrona ativa
    Given uma execução está pending ou running
    When a situação muda para succeeded ou failed
    Then o círculo sai somente ao término, preservando contagens e erros
```

#### AC-005 — Término e independência das ações

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-005
Feature: Feedback local de processamento

  Scenario: Término e independência das ações
    Given uma operação local está pendente
    When ela termina com sucesso ou erro
    Then seu círculo desaparece e controles independentes continuam utilizáveis
```

#### AC-006 — Acessibilidade e preferência visual

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-006
Feature: Feedback local de processamento

  Scenario: Acessibilidade e preferência visual
    Given a pessoa usa tema claro ou escuro com movimento reduzido
    When um indicador aparece
    Then texto está em português, ícone herda cor, não recebe foco e respeita movimento reduzido
```

### 7. Requisitos

#### Funcionais
- **FR-001**: Cada espera mapeada deve mostrar círculo junto da ação/área, preservando texto, skeleton e controles independentes. Cobertura: AC-001 a AC-006.
- **FR-002**: Círculo deve acompanhar ciclo real até sucesso/erro, ou pending/running até término; controles da ação continuam prevenindo repetição. Cobertura: AC-001, AC-002, AC-004, AC-005.

#### Não funcionais
- **NFR-001**: Português, ícone decorativo junto de texto, sem foco, cores herdadas dos temas e rotação desativada com prefers-reduced-motion. **Verificação**: AC-001/AC-003/AC-006 em componentes, CSS e Chromium.

#### Erros e casos-limite
Falha remove espera e mantém recuperação existente. Polling mantém círculo durante execução ativa. Cliques síncronos e requisições auxiliares silenciosas não criam espera global.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente
React 19/Next App Router/Tailwind 4/shadcn Base UI; estados locais e apiFetch/apiJson existentes.

#### Arquitetura e módulos
Spinner ganha português/reduced motion; Button recebe loading opcional com ícone, aria-busy e disabled. IndicadorProcessamento compõe ícone/texto. Features mantêm ownership.

#### Migrations
Não aplicável; nenhum schema novo.

#### Models
Somente booleanos transitórios, sem modelo persistente novo.

#### Controllers e casos de uso
Chamadas existentes; expor carregandoMensagens em useAssistente e espera no SeletorBase/MenuPessoa.

#### Views e experiência
Superfícies na seção 10; preservar loading/empty/error/success existentes.

#### Queries e repositórios
Nenhuma alteração no backend.

#### Jobs e processamento assíncrono
PainelProgresso usa situação recebida no polling; nenhum job novo.

#### Estrutura de arquivos
```text
frontend/src/components/ui/{button,spinner}.tsx
frontend/src/components/IndicadorProcessamento.tsx
frontend/src/features/{auth,workspaces,bases,pessoas,execucoes,assistente}/
frontend/src/app/(autenticado)/
frontend/src/test/processamento.test.tsx
```

### 9. Modelo de dados

#### Entidades
| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Espera local | Componente da ação | Booleano transitório | Tela atual |

#### Estados e transições
| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Espera | Livre | Pedido | Ocupada | Círculo local |
| Espera | Ocupada | Sucesso/erro | Livre | Recuperação preservada |
| Execução | pending/running | Término | succeeded/failed | Círculo só enquanto ativa |

#### Migração e retenção
Não aplicável; sem persistência.

### 10. Interfaces e contratos

#### Interface para pessoas
- **Há interface para pessoas**: Sim.

#### Stack e convenções de interface
Next 16.3.4 App Router, React 19, Tailwind v4, shadcn Base UI, ReUI registry e Vitest/Testing Library. Componentes existentes atendem; não copiar layout novo do catálogo.

#### Telas e responsabilidades
| Tela | Responsabilidade |
| --- | --- |
| /login | Envio de credenciais |
| /nova-senha | Envio de senha e Sair |
| Shell autenticado | Sessão, trocar senha e sair |
| /workspaces | Lista, formulário e exclusão |
| /workspaces/[id] | Bases, upload e exclusão |
| /pessoas | Lista e formulário |
| /pessoas/[id] | Detalhe, situação e senha |
| /execucoes/[id] | Detalhe, execução, repetir e consulta |
| Assistente | Histórico, conversa, Bases, envio e exclusão |

#### Fluxo de informação e navegação
Manter rotas, redirects e Breadcrumb Equipe/módulo/tela. Mesma ação com feedback local até resposta; conteúdo independente continua utilizável.

#### Menus e navegação principal
Workspaces, Pessoas conforme papel, menu da pessoa e launcher do assistente preservados. Claro/Escuro/Sistema continuam. Sair usa spinner no item; responsividade existente.

#### Formulários e ações
Manter campos, labels e validações; sheets de Workspace/upload/Pessoa, diálogos de confirmação e senha, login/nova senha/consulta/composer. Círculo só no botão confirmador, não em Cancelar.

#### Composição e disposição
Ícone 16px com gap existente no botão ou gap-2 no texto de região. Sem overlay ou mudança de grid, margens/padding. Skeleton mantido; defaults de DESIGNSYSTEM.MD.

#### Blocos React e componentes selecionados
| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Cada tela | Button | Espera de ação | frontend/src/components/ui/button.tsx | Button + Spinner | shadcn/ui | loading opcional |
| Cada tela | Spinner | Ícone | frontend/src/components/ui/spinner.tsx | Loader2Icon | shadcn/ui | Português/motion |
| Dados | IndicadorProcessamento | Ícone/texto | frontend/src/components/IndicadorProcessamento.tsx | Spinner | Próprio | Novo compartilhado |
| Auth | Formulários/MenuPessoa | Submit/sair | frontend/src/features/auth/ | Button/DropdownMenu | Próprio | Extensão |
| Workspaces/Bases | DataGrids/sheets/dialogs | Lista/envio/exclusão | frontend/src/features/workspaces/ e frontend/src/features/bases/ | Button/Skeleton/IndicadorProcessamento | Próprio | Extensão |
| Pessoas | DataGrid/formulários | Lista/envio | frontend/src/features/pessoas/ | Button/Skeleton | Próprio | Extensão |
| Execução | PainelProgresso/FormularioConsulta | Job e consulta | frontend/src/features/execucoes/ | Badge/Button/IndicadorProcessamento | Próprio | Extensão |
| Assistente | Listas/Composer/SeletorBase/useAssistente | Esperas do painel | frontend/src/features/assistente/ | Button/Skeleton/IndicadorProcessamento | Próprio | Extensão |

#### Estados e acessibilidade
Ícone decorativo aria-hidden junto de texto; região com status, botão aria-busy/disabled. Nenhum foco no ícone; preservar vazio/erro/sucesso/permissão. Respeitar reduced motion e tema.

#### Contrato CRUD
Nenhum CRUD novo. Preservar PageHeader, Breadcrumb, DataGrid largura disponível, coluna ID, link da linha e ações independentes de editar e apagar. INTERFACE.md registra extensões.

#### Revisão visual durante o desenvolvimento
Chromium em 360/1280px, claro/escuro, livre/ocupado/erro/terminal e reduced motion; bordas, espaçamentos, margens, padding, tipografia, foco e overflow. Prova em cada tarefa.

#### APIs expostas
Nenhuma API nova; contratos v1 e Sessão preservados.

#### APIs externas utilizadas
Nenhuma operação externa nova.

#### Documentação das APIs consultadas
Código local api-client.ts e contratos existentes.

#### Eventos e outros contratos
Button loading?: boolean; IndicadorProcessamento children/className. useAssistente expõe carregandoMensagens e encerra espera em finally.

### 11. Estratégia TDD

- **Unidade**: Button/Spinner e painéis.
- **Integração/contrato**: Promises adiadas com formulários/componentes reais.
- **BDD/aceite**: seis ACs da seção 6, sem executar Gherkin.
- **Runner TDD**: Vitest, npm --prefix frontend run test:tdd.
- **E2E**: Chromium com respostas controladas e componentes reais.
- **Verificação manual**: layout/motion no browser, pois jsdom não renderiza.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, NFR-001, AC-001 | AC-001 seção 6 | frontend/src/test/processamento.test.tsx (AC-001) | RED: ausência de feedback local; Vitest focal exit 1, 12 falhas | GREEN: 12/12 casos focais; exit 0 | Regressão: 192/192 testes; primitives compartilhadas |
| US-001, FR-001, FR-002, AC-002 | AC-002 seção 6 | frontend/src/test/processamento.test.tsx (AC-002) | RED: ausência de feedback local; Vitest focal exit 1, 12 falhas | GREEN: 12/12 casos focais; exit 0 | Regressão: 192/192 testes; primitives compartilhadas |
| US-001, FR-001, NFR-001, AC-003 | AC-003 seção 6 | frontend/src/test/processamento.test.tsx (AC-003) | RED: ausência de feedback local; Vitest focal exit 1, 12 falhas | GREEN: 12/12 casos focais; exit 0 | Regressão: 192/192 testes; primitives compartilhadas |
| US-001, FR-001, FR-002, AC-004 | AC-004 seção 6 | frontend/src/test/processamento.test.tsx (AC-004) | RED: ausência de feedback local; Vitest focal exit 1, 12 falhas | GREEN: 12/12 casos focais; exit 0 | Regressão: 192/192 testes; primitives compartilhadas |
| US-001, FR-001, FR-002, AC-005 | AC-005 seção 6 | frontend/src/test/processamento.test.tsx (AC-005) | RED: ausência de feedback local; Vitest focal exit 1, 12 falhas | GREEN: 12/12 casos focais; exit 0 | Regressão: 192/192 testes; primitives compartilhadas |
| US-001, FR-001, NFR-001, AC-006 | AC-006 seção 6 | frontend/src/test/processamento.test.tsx (AC-006) | RED: ausência de feedback local; Vitest focal exit 1, 12 falhas | GREEN: 12/12 casos focais; exit 0 | Regressão: 192/192 testes; primitives compartilhadas |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, NFR-001 | AC-001 | Componente/contrato | npm --prefix frontend run test:tdd -- src/test/processamento.test.tsx | Passed: Vitest focal 12/12; suíte 192/192, sem skips |
| US-001, FR-001, FR-002 | AC-002 | Componente/contrato | npm --prefix frontend run test:tdd -- src/test/processamento.test.tsx | Passed: Vitest focal 12/12; suíte 192/192, sem skips |
| US-001, FR-001, NFR-001 | AC-003 | Componente/contrato | npm --prefix frontend run test:tdd -- src/test/processamento.test.tsx | Passed: Vitest focal 12/12; suíte 192/192, sem skips |
| US-001, FR-001, FR-002 | AC-004 | Componente/contrato | npm --prefix frontend run test:tdd -- src/test/processamento.test.tsx | Passed: Vitest focal 12/12; suíte 192/192, sem skips |
| US-001, FR-001, FR-002 | AC-005 | Componente/contrato | npm --prefix frontend run test:tdd -- src/test/processamento.test.tsx | Passed: Vitest focal 12/12; suíte 192/192, sem skips |
| US-001, FR-001, NFR-001 | AC-006 | Componente/contrato | npm --prefix frontend run test:tdd -- src/test/processamento.test.tsx | Passed: Vitest focal 12/12; suíte 192/192, sem skips |

### 13. Validações

#### Gate do Ato I — Definição
- **Resultado**: Passed
- **Comando**: validate_spec.mjs nesta spec.
- **Achados**: READY em 2026-10-05; cobertura US/FR/NFR de no mínimo três ACs, posição confirmada e nenhuma decisão material aberta. Validador estrutural VALID DRAFT; revisão semântica de estados, recuperação, autoria e escopo aprovada.

#### Gate do Ato II — Plano
- **Resultado**: Passed
- **Comando**: validate_tasks.mjs nesta spec.
- **Achados**: READY; 18 tarefas, seis predecessores TDD concluídos com RED válido (12 casos), cobertura 10/10 IDs e fase de interface validada. Sem nova decisão de arquitetura.

#### Gate do Ato III — Entrega
- **Resultado**: Passed
- **Comando**: check_traceability.mjs, verify_acceptance.mjs, lint, typecheck, Vitest e build.
- **Achados**: READY em 2026-10-05. 18/18 tarefas; 12 casos focais GREEN, 192/192 testes em 42 arquivos (zero skips), lint/typecheck/build aprovados. Rastreabilidade 10/10 IDs, QA Passed, evidência strict Passed e enforcement local Passed. Chromium: 72 capturas em 360/1280 px e claro/escuro, região/botão, livre/ocupado/erro/terminal; sem overflow. Reduced motion sem animação, sem foco nos ícones; padding, bordas, margens, espaçamento e tipografia preservados. Respostas simuladas no browser, sem operações em dados reais. Frontend Docker local reconstruído e serviço convergente na porta 3000. Nenhum schema/pacote novo; documentação CURRENT.

### 14. Tarefas

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Provar AC-001 em frontend/src/test/processamento.test.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Ler AC-001 e escolher componente/contrato que prova a espera local.
  - [x] **EXECUTE**: Materializar caso Vitest de AC-001 com marcador próprio.
  - [x] **VERIFY**: Observar RED por comportamento ausente ou documentar caracterização já existente.
  - [x] **VISUAL**: Não aplicável; teste de componente não altera interface de produção.
  - [x] **EVIDENCE**: Registrar comando, causa e IDs na seção 11.
  - [x] **IMPROVE**: Evitar oráculo que substitui o estado real de espera.

Evidência T001: Vitest focal em 2026-10-05; 12 casos falharam pela ausência de Spinner local, aria-busy, estado de leitura ou rótulo/motion. Saída: /tmp/rag-spinner-red.log. Nenhuma produção alterada. Oráculo usa DOM e requests reais com resposta adiada.

- [x] T002 [TEST] [TDD] [US-001] Provar AC-002 em frontend/src/test/processamento.test.tsx — Refs: US-001, FR-001, FR-002, AC-002 — Depends: none
  - [x] **PREP**: Ler AC-002 e escolher componente/contrato que prova a espera local.
  - [x] **EXECUTE**: Materializar caso Vitest de AC-002 com marcador próprio.
  - [x] **VERIFY**: Observar RED por comportamento ausente ou documentar caracterização já existente.
  - [x] **VISUAL**: Não aplicável; teste de componente não altera interface de produção.
  - [x] **EVIDENCE**: Registrar comando, causa e IDs na seção 11.
  - [x] **IMPROVE**: Evitar oráculo que substitui o estado real de espera.

Evidência T002: Vitest focal em 2026-10-05; 12 casos falharam pela ausência de Spinner local, aria-busy, estado de leitura ou rótulo/motion. Saída: /tmp/rag-spinner-red.log. Nenhuma produção alterada. Oráculo usa DOM e requests reais com resposta adiada.

- [x] T003 [TEST] [TDD] [US-001] Provar AC-003 em frontend/src/test/processamento.test.tsx — Refs: US-001, FR-001, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Ler AC-003 e escolher componente/contrato que prova a espera local.
  - [x] **EXECUTE**: Materializar caso Vitest de AC-003 com marcador próprio.
  - [x] **VERIFY**: Observar RED por comportamento ausente ou documentar caracterização já existente.
  - [x] **VISUAL**: Não aplicável; teste de componente não altera interface de produção.
  - [x] **EVIDENCE**: Registrar comando, causa e IDs na seção 11.
  - [x] **IMPROVE**: Evitar oráculo que substitui o estado real de espera.

Evidência T003: Vitest focal em 2026-10-05; 12 casos falharam pela ausência de Spinner local, aria-busy, estado de leitura ou rótulo/motion. Saída: /tmp/rag-spinner-red.log. Nenhuma produção alterada. Oráculo usa DOM e requests reais com resposta adiada.

- [x] T004 [TEST] [TDD] [US-001] Provar AC-004 em frontend/src/test/processamento.test.tsx — Refs: US-001, FR-001, FR-002, AC-004 — Depends: none
  - [x] **PREP**: Ler AC-004 e escolher componente/contrato que prova a espera local.
  - [x] **EXECUTE**: Materializar caso Vitest de AC-004 com marcador próprio.
  - [x] **VERIFY**: Observar RED por comportamento ausente ou documentar caracterização já existente.
  - [x] **VISUAL**: Não aplicável; teste de componente não altera interface de produção.
  - [x] **EVIDENCE**: Registrar comando, causa e IDs na seção 11.
  - [x] **IMPROVE**: Evitar oráculo que substitui o estado real de espera.

Evidência T004: Vitest focal em 2026-10-05; 12 casos falharam pela ausência de Spinner local, aria-busy, estado de leitura ou rótulo/motion. Saída: /tmp/rag-spinner-red.log. Nenhuma produção alterada. Oráculo usa DOM e requests reais com resposta adiada.

- [x] T005 [TEST] [TDD] [US-001] Provar AC-005 em frontend/src/test/processamento.test.tsx — Refs: US-001, FR-001, FR-002, AC-005 — Depends: none
  - [x] **PREP**: Ler AC-005 e escolher componente/contrato que prova a espera local.
  - [x] **EXECUTE**: Materializar caso Vitest de AC-005 com marcador próprio.
  - [x] **VERIFY**: Observar RED por comportamento ausente ou documentar caracterização já existente.
  - [x] **VISUAL**: Não aplicável; teste de componente não altera interface de produção.
  - [x] **EVIDENCE**: Registrar comando, causa e IDs na seção 11.
  - [x] **IMPROVE**: Evitar oráculo que substitui o estado real de espera.

Evidência T005: Vitest focal em 2026-10-05; 12 casos falharam pela ausência de Spinner local, aria-busy, estado de leitura ou rótulo/motion. Saída: /tmp/rag-spinner-red.log. Nenhuma produção alterada. Oráculo usa DOM e requests reais com resposta adiada.

- [x] T006 [TEST] [TDD] [US-001] Provar AC-006 em frontend/src/test/processamento.test.tsx — Refs: US-001, FR-001, NFR-001, AC-006 — Depends: none
  - [x] **PREP**: Ler AC-006 e escolher componente/contrato que prova a espera local.
  - [x] **EXECUTE**: Materializar caso Vitest de AC-006 com marcador próprio.
  - [x] **VERIFY**: Observar RED por comportamento ausente ou documentar caracterização já existente.
  - [x] **VISUAL**: Não aplicável; teste de componente não altera interface de produção.
  - [x] **EVIDENCE**: Registrar comando, causa e IDs na seção 11.
  - [x] **IMPROVE**: Evitar oráculo que substitui o estado real de espera.

Evidência T006: Vitest focal em 2026-10-05; 12 casos falharam pela ausência de Spinner local, aria-busy, estado de leitura ou rótulo/motion. Saída: /tmp/rag-spinner-red.log. Nenhuma produção alterada. Oráculo usa DOM e requests reais com resposta adiada.

#### Fase de interface

- [x] T007 [CODE] [US-001] Estender primitives de espera em frontend/src/components/ui/button.tsx, frontend/src/components/ui/spinner.tsx, frontend/src/components/IndicadorProcessamento.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006
  - [x] **PREP**: Confirmar RED e carregar specsfy-specialist-react-ui-components; ler blocos existentes e INTERFACE.md.
  - [x] **EXECUTE**: Implementar feedback local em frontend/src/components/ui/button.tsx, preservar fluxo/temas e reconstruir docs/ por specsfy-documentator.
  - [x] **VERIFY**: Executar testes focais e conferir estados livre/ocupado/erro com controls independentes.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia em 360/1280px, claro/escuro, espera/erro.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos e revisão visual na própria tarefa.
  - [x] **IMPROVE**: Reutilizar estado e primitive, removendo spinner duplicado quando necessário.


Evidência T007: Vitest focal 12/12 e regressão 192/192 aprovados; lint, typecheck e build exit 0. Revisão Chromium 360/1280 px, claro/escuro: loading de regiões, botão de login, erro e execução ativa/terminal; zero overflow/erros JS e reduced motion sem animação. Inspeção dos consumidores confirma bordas, margens, padding e tipografia preservados; botão compartilha ícone 16 px e espaçamento existente. Screenshots em research/revisao-visual/. Refactor: primitive compartilhada e estado local existente, sem nova dependência.

<!-- specsfy:evidence {"task": "T007", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["frontend/src/components/ui/button.tsx", "frontend/src/components/ui/spinner.tsx", "frontend/src/components/IndicadorProcessamento.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

- [x] T008 [CODE] [US-001] Mostrar espera em /login em frontend/src/features/auth/LoginForm.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006, T007
  - [x] **PREP**: Confirmar RED e carregar specsfy-specialist-react-ui-components; ler blocos existentes e INTERFACE.md.
  - [x] **EXECUTE**: Implementar feedback local em frontend/src/features/auth/LoginForm.tsx, preservar fluxo/temas e reconstruir docs/ por specsfy-documentator.
  - [x] **VERIFY**: Executar testes focais e conferir estados livre/ocupado/erro com controls independentes.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia em 360/1280px, claro/escuro, espera/erro.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos e revisão visual na própria tarefa.
  - [x] **IMPROVE**: Reutilizar estado e primitive, removendo spinner duplicado quando necessário.


Evidência T008: Vitest focal 12/12 e regressão 192/192 aprovados; lint, typecheck e build exit 0. Revisão Chromium 360/1280 px, claro/escuro: loading de regiões, botão de login, erro e execução ativa/terminal; zero overflow/erros JS e reduced motion sem animação. Inspeção dos consumidores confirma bordas, margens, padding e tipografia preservados; botão compartilha ícone 16 px e espaçamento existente. Screenshots em research/revisao-visual/. Refactor: primitive compartilhada e estado local existente, sem nova dependência.

<!-- specsfy:evidence {"task": "T008", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["frontend/src/features/auth/LoginForm.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

- [x] T009 [CODE] [US-001] Mostrar espera em /nova-senha em frontend/src/features/auth/NovaSenhaForm.tsx, frontend/src/app/nova-senha/page.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006, T007
  - [x] **PREP**: Confirmar RED e carregar specsfy-specialist-react-ui-components; ler blocos existentes e INTERFACE.md.
  - [x] **EXECUTE**: Implementar feedback local em frontend/src/features/auth/NovaSenhaForm.tsx, preservar fluxo/temas e reconstruir docs/ por specsfy-documentator.
  - [x] **VERIFY**: Executar testes focais e conferir estados livre/ocupado/erro com controls independentes.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia em 360/1280px, claro/escuro, espera/erro.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos e revisão visual na própria tarefa.
  - [x] **IMPROVE**: Reutilizar estado e primitive, removendo spinner duplicado quando necessário.


Evidência T009: Vitest focal 12/12 e regressão 192/192 aprovados; lint, typecheck e build exit 0. Revisão Chromium 360/1280 px, claro/escuro: loading de regiões, botão de login, erro e execução ativa/terminal; zero overflow/erros JS e reduced motion sem animação. Inspeção dos consumidores confirma bordas, margens, padding e tipografia preservados; botão compartilha ícone 16 px e espaçamento existente. Screenshots em research/revisao-visual/. Refactor: primitive compartilhada e estado local existente, sem nova dependência.

<!-- specsfy:evidence {"task": "T009", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["frontend/src/features/auth/NovaSenhaForm.tsx", "frontend/src/app/nova-senha/page.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

- [x] T010 [CODE] [US-001] Mostrar espera de sessão, senha e sair no shell em frontend/src/app/(autenticado)/layout.tsx, frontend/src/features/auth/MenuPessoa.tsx, frontend/src/features/auth/TrocarSenhaDialog.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006, T007
  - [x] **PREP**: Confirmar RED e carregar specsfy-specialist-react-ui-components; ler blocos existentes e INTERFACE.md.
  - [x] **EXECUTE**: Implementar feedback local em frontend/src/app/(autenticado)/layout.tsx, preservar fluxo/temas e reconstruir docs/ por specsfy-documentator.
  - [x] **VERIFY**: Executar testes focais e conferir estados livre/ocupado/erro com controls independentes.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia em 360/1280px, claro/escuro, espera/erro.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos e revisão visual na própria tarefa.
  - [x] **IMPROVE**: Reutilizar estado e primitive, removendo spinner duplicado quando necessário.


Evidência T010: Vitest focal 12/12 e regressão 192/192 aprovados; lint, typecheck e build exit 0. Revisão Chromium 360/1280 px, claro/escuro: loading de regiões, botão de login, erro e execução ativa/terminal; zero overflow/erros JS e reduced motion sem animação. Inspeção dos consumidores confirma bordas, margens, padding e tipografia preservados; botão compartilha ícone 16 px e espaçamento existente. Screenshots em research/revisao-visual/. Refactor: primitive compartilhada e estado local existente, sem nova dependência.

<!-- specsfy:evidence {"task": "T010", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["frontend/src/app/(autenticado)/layout.tsx", "frontend/src/features/auth/MenuPessoa.tsx", "frontend/src/features/auth/TrocarSenhaDialog.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

- [x] T011 [CODE] [US-001] Mostrar espera em /workspaces e ações de Workspace em frontend/src/features/workspaces/DataGridWorkspaces.tsx, frontend/src/features/workspaces/WorkspaceFormSheet.tsx, frontend/src/features/workspaces/ExcluirWorkspaceDialog.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006, T007
  - [x] **PREP**: Confirmar RED e carregar specsfy-specialist-react-ui-components; ler blocos existentes e INTERFACE.md.
  - [x] **EXECUTE**: Implementar feedback local em frontend/src/features/workspaces/DataGridWorkspaces.tsx, preservar fluxo/temas e reconstruir docs/ por specsfy-documentator.
  - [x] **VERIFY**: Executar testes focais e conferir estados livre/ocupado/erro com controls independentes.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia em 360/1280px, claro/escuro, espera/erro.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos e revisão visual na própria tarefa.
  - [x] **IMPROVE**: Reutilizar estado e primitive, removendo spinner duplicado quando necessário.


Evidência T011: Vitest focal 12/12 e regressão 192/192 aprovados; lint, typecheck e build exit 0. Revisão Chromium 360/1280 px, claro/escuro: loading de regiões, botão de login, erro e execução ativa/terminal; zero overflow/erros JS e reduced motion sem animação. Inspeção dos consumidores confirma bordas, margens, padding e tipografia preservados; botão compartilha ícone 16 px e espaçamento existente. Screenshots em research/revisao-visual/. Refactor: primitive compartilhada e estado local existente, sem nova dependência.

<!-- specsfy:evidence {"task": "T011", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["frontend/src/features/workspaces/DataGridWorkspaces.tsx", "frontend/src/features/workspaces/WorkspaceFormSheet.tsx", "frontend/src/features/workspaces/ExcluirWorkspaceDialog.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

- [x] T012 [CODE] [US-001] Mostrar espera em /workspaces/[id] e ações de Base em frontend/src/features/bases/DataGridBases.tsx, frontend/src/features/bases/UploadBaseSheet.tsx, frontend/src/features/bases/ExcluirBaseDialog.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006, T007
  - [x] **PREP**: Confirmar RED e carregar specsfy-specialist-react-ui-components; ler blocos existentes e INTERFACE.md.
  - [x] **EXECUTE**: Implementar feedback local em frontend/src/features/bases/DataGridBases.tsx, preservar fluxo/temas e reconstruir docs/ por specsfy-documentator.
  - [x] **VERIFY**: Executar testes focais e conferir estados livre/ocupado/erro com controls independentes.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia em 360/1280px, claro/escuro, espera/erro.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos e revisão visual na própria tarefa.
  - [x] **IMPROVE**: Reutilizar estado e primitive, removendo spinner duplicado quando necessário.


Evidência T012: Vitest focal 12/12 e regressão 192/192 aprovados; lint, typecheck e build exit 0. Revisão Chromium 360/1280 px, claro/escuro: loading de regiões, botão de login, erro e execução ativa/terminal; zero overflow/erros JS e reduced motion sem animação. Inspeção dos consumidores confirma bordas, margens, padding e tipografia preservados; botão compartilha ícone 16 px e espaçamento existente. Screenshots em research/revisao-visual/. Refactor: primitive compartilhada e estado local existente, sem nova dependência.

<!-- specsfy:evidence {"task": "T012", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["frontend/src/features/bases/DataGridBases.tsx", "frontend/src/features/bases/UploadBaseSheet.tsx", "frontend/src/features/bases/ExcluirBaseDialog.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

- [x] T013 [CODE] [US-001] Mostrar espera em /pessoas e formulários em frontend/src/features/pessoas/DataGridPessoas.tsx, frontend/src/features/pessoas/PessoaFormSheet.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006, T007
  - [x] **PREP**: Confirmar RED e carregar specsfy-specialist-react-ui-components; ler blocos existentes e INTERFACE.md.
  - [x] **EXECUTE**: Implementar feedback local em frontend/src/features/pessoas/DataGridPessoas.tsx, preservar fluxo/temas e reconstruir docs/ por specsfy-documentator.
  - [x] **VERIFY**: Executar testes focais e conferir estados livre/ocupado/erro com controls independentes.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia em 360/1280px, claro/escuro, espera/erro.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos e revisão visual na própria tarefa.
  - [x] **IMPROVE**: Reutilizar estado e primitive, removendo spinner duplicado quando necessário.


Evidência T013: Vitest focal 12/12 e regressão 192/192 aprovados; lint, typecheck e build exit 0. Revisão Chromium 360/1280 px, claro/escuro: loading de regiões, botão de login, erro e execução ativa/terminal; zero overflow/erros JS e reduced motion sem animação. Inspeção dos consumidores confirma bordas, margens, padding e tipografia preservados; botão compartilha ícone 16 px e espaçamento existente. Screenshots em research/revisao-visual/. Refactor: primitive compartilhada e estado local existente, sem nova dependência.

<!-- specsfy:evidence {"task": "T013", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["frontend/src/features/pessoas/DataGridPessoas.tsx", "frontend/src/features/pessoas/PessoaFormSheet.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

- [x] T014 [CODE] [US-001] Mostrar espera em /pessoas/[id] e ações de situação/senha em frontend/src/app/(autenticado)/pessoas/[id]/page.tsx, frontend/src/features/pessoas/DesativarPessoaDialog.tsx, frontend/src/features/pessoas/RedefinirSenhaDialog.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006, T007
  - [x] **PREP**: Confirmar RED e carregar specsfy-specialist-react-ui-components; ler blocos existentes e INTERFACE.md.
  - [x] **EXECUTE**: Implementar feedback local em frontend/src/app/(autenticado)/pessoas/[id]/page.tsx, preservar fluxo/temas e reconstruir docs/ por specsfy-documentator.
  - [x] **VERIFY**: Executar testes focais e conferir estados livre/ocupado/erro com controls independentes.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia em 360/1280px, claro/escuro, espera/erro.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos e revisão visual na própria tarefa.
  - [x] **IMPROVE**: Reutilizar estado e primitive, removendo spinner duplicado quando necessário.


Evidência T014: Vitest focal 12/12 e regressão 192/192 aprovados; lint, typecheck e build exit 0. Revisão Chromium 360/1280 px, claro/escuro: loading de regiões, botão de login, erro e execução ativa/terminal; zero overflow/erros JS e reduced motion sem animação. Inspeção dos consumidores confirma bordas, margens, padding e tipografia preservados; botão compartilha ícone 16 px e espaçamento existente. Screenshots em research/revisao-visual/. Refactor: primitive compartilhada e estado local existente, sem nova dependência.

<!-- specsfy:evidence {"task": "T014", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["frontend/src/app/(autenticado)/pessoas/[id]/page.tsx", "frontend/src/features/pessoas/DesativarPessoaDialog.tsx", "frontend/src/features/pessoas/RedefinirSenhaDialog.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

- [x] T015 [CODE] [US-001] Mostrar espera em /execucoes/[id], consulta e indexação em frontend/src/app/(autenticado)/execucoes/[id]/page.tsx, frontend/src/features/execucoes/PainelProgresso.tsx, frontend/src/features/execucoes/FormularioConsulta.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006, T007
  - [x] **PREP**: Confirmar RED e carregar specsfy-specialist-react-ui-components; ler blocos existentes e INTERFACE.md.
  - [x] **EXECUTE**: Implementar feedback local em frontend/src/app/(autenticado)/execucoes/[id]/page.tsx, preservar fluxo/temas e reconstruir docs/ por specsfy-documentator.
  - [x] **VERIFY**: Executar testes focais e conferir estados livre/ocupado/erro com controls independentes.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia em 360/1280px, claro/escuro, espera/erro.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos e revisão visual na própria tarefa.
  - [x] **IMPROVE**: Reutilizar estado e primitive, removendo spinner duplicado quando necessário.


Evidência T015: Vitest focal 12/12 e regressão 192/192 aprovados; lint, typecheck e build exit 0. Revisão Chromium 360/1280 px, claro/escuro: loading de regiões, botão de login, erro e execução ativa/terminal; zero overflow/erros JS e reduced motion sem animação. Inspeção dos consumidores confirma bordas, margens, padding e tipografia preservados; botão compartilha ícone 16 px e espaçamento existente. Screenshots em research/revisao-visual/. Refactor: primitive compartilhada e estado local existente, sem nova dependência.

<!-- specsfy:evidence {"task": "T015", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["frontend/src/app/(autenticado)/execucoes/[id]/page.tsx", "frontend/src/features/execucoes/PainelProgresso.tsx", "frontend/src/features/execucoes/FormularioConsulta.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

- [x] T016 [CODE] [US-001] Mostrar espera no painel do assistente em frontend/src/features/assistente/ComposerMensagem.tsx, frontend/src/features/assistente/ListaConversas.tsx, frontend/src/features/assistente/ListaMensagens.tsx, frontend/src/features/assistente/SeletorBase.tsx, frontend/src/features/assistente/ApagarConversaDialog.tsx, frontend/src/features/assistente/useAssistente.ts, frontend/src/features/assistente/AssistentePainel.tsx — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006, T007
  - [x] **PREP**: Confirmar RED e carregar specsfy-specialist-react-ui-components; ler blocos existentes e INTERFACE.md.
  - [x] **EXECUTE**: Implementar feedback local em frontend/src/features/assistente/ComposerMensagem.tsx, preservar fluxo/temas e reconstruir docs/ por specsfy-documentator.
  - [x] **VERIFY**: Executar testes focais e conferir estados livre/ocupado/erro com controls independentes.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia em 360/1280px, claro/escuro, espera/erro.
  - [x] **EVIDENCE**: Registrar GREEN, arquivos e revisão visual na própria tarefa.
  - [x] **IMPROVE**: Reutilizar estado e primitive, removendo spinner duplicado quando necessário.


Evidência T016: Vitest focal 12/12 e regressão 192/192 aprovados; lint, typecheck e build exit 0. Revisão Chromium 360/1280 px, claro/escuro: loading de regiões, botão de login, erro e execução ativa/terminal; zero overflow/erros JS e reduced motion sem animação. Inspeção dos consumidores confirma bordas, margens, padding e tipografia preservados; botão compartilha ícone 16 px e espaçamento existente. Screenshots em research/revisao-visual/. Refactor: primitive compartilhada e estado local existente, sem nova dependência.

<!-- specsfy:evidence {"task": "T016", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["frontend/src/features/assistente/ComposerMensagem.tsx", "frontend/src/features/assistente/ListaConversas.tsx", "frontend/src/features/assistente/ListaMensagens.tsx", "frontend/src/features/assistente/SeletorBase.tsx", "frontend/src/features/assistente/ApagarConversaDialog.tsx", "frontend/src/features/assistente/useAssistente.ts", "frontend/src/features/assistente/AssistentePainel.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

#### Fase final — Qualidade

- [x] T017 [DOC] [US-001] Registrar componentes e capacidade em INTERFACE.md, PROJECT.md e docs/ — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T007, T008, T009, T010, T011, T012, T013, T014, T015, T016
  - [x] **PREP**: Conferir cada componente e consumidor efetivamente alterado.
  - [x] **EXECUTE**: Registrar loading/IndicadorProcessamento e reconstruir documentação e PACKAGES.md.
  - [x] **VERIFY**: Exigir documentador --check e monitor CURRENT.
  - [x] **VISUAL**: Não aplicável; inventário textual, revisão visual nas tarefas de interface.
  - [x] **EVIDENCE**: Registrar os caminhos e comandos aprovados.
  - [x] **IMPROVE**: Documentar regra de reuso para próxima tela.


Evidência T017: INTERFACE.md registra Button/Spinner/IndicadorProcessamento e consumidores; PROJECT.md registra capacidade. specsfy-documentator reconstruiu docs/ e conferiu PACKAGES.md; build_documentation.mjs --check e monitor_context.mjs --check exit 0, CURRENT. Nenhuma dependência alterada. VISUAL não aplicável: inventário textual.

- [x] T018 [TEST] [US-001] Executar regressão de frontend/package.json e rastreabilidade desta spec.md — Refs: US-001, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T017
  - [x] **PREP**: Validar segurança dos comandos e identificar lint/typecheck/test:tdd/build.
  - [x] **EXECUTE**: Executar checks e auditores de evidência, QA e rastreabilidade.
  - [x] **VERIFY**: Exigir zero falhas e cobertura de cada ID.
  - [x] **VISUAL**: Repassar bordas, espaçamentos, margens, padding, tipografia, foco, overflow e reduced motion em 360/1280px e dois temas.
  - [x] **EVIDENCE**: Registrar contagens e limitações concretas na seção 13.
  - [x] **IMPROVE**: Registrar retrospectiva e ausência de nova dependência.


Evidência T018: segurança SAFE; lint/typecheck/build exit 0, Vitest 192/192 e 12/12 focal; rastreabilidade 10/10, QA Passed, evidence strict Passed e verify_repo local Passed. Revisão final Chromium 72 capturas, 360/1280 px, claro/escuro: regiões, login/senha, criação de Workspace/Pessoa, upload, consulta, assistente/histórico/seleção de Base e Sair. Zero overflow; reduced motion sem animação. Inspeção visual de screenshots confirma ícone/texto alinhados e tokens existentes. Primitives compartilhadas evitam duplicação; nenhuma dependência nova. Docker build e serviço frontend local convergentes.

### 15. Ordem de execução

T001–T006 RED → T007 primitives → T008–T016 telas → T017 documentação → T018 regressão. Nenhuma tarefa marcada P, pois compartilham primitive/testes. Cada tela preserva uma entrega independente.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências
SPEC-0024 tema e componentes existentes; nenhum pacote novo.

#### Riscos
Duplicar Spinner existente: retirar ícone manual ao usar loading. Movimento excessivo: reduced motion. Respostas concorrentes no assistente: manter seleção/espera coerentes.

#### Suposições
Espera significa operação perceptível; digitar e escolher tema são síncronos e não recebem loading. Requisições auxiliares silenciosas não criam bloqueio.

### 17. Decisões
- **DEC-001**: Junto da ação/área e restante disponível, opção 1 confirmada.
- **DEC-002**: Reutilizar Spinner e estender Button; componente de região compartilhado.
- **DEC-003**: Indexação ativa mantém círculo até situação terminal.

### 18. Definition of Done
- [x] Definition Gate Passed.
- [x] Plan Gate Passed.
- [x] Delivery Gate Passed.
- [x] Cenários e requisitos com evidência automatizada/visual.
- [x] Tarefas da seção 14 concluídas.
- [x] Lint/typecheck/Vitest/build aprovados.
- [x] INTERFACE.md, PROJECT.md, docs/ e PACKAGES.md atuais; monitor CURRENT.
