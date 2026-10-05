# Especificação integrada: Tema escuro (dark mode) no frontend

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0024 |
| Slug | 0024-tema-escuro-dark-mode-no-frontend |
| Status | Planned |
| Effort | 3 |
| Effort updated at | 2026-10-05 |
| Effort rationale | Entrega somente de frontend, sem backend, banco ou dependência nova: mecanismo de tema com script antes da primeira pintura, extensão de uma primitive, um seletor novo no menu da pessoa e revisão visual das telas existentes nos dois temas. O raciocínio mais delicado é evitar o piscar na hidratação e provar contraste, o que mantém o perfil `standard`. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-05 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O frontend só funciona no tema claro. O `frontend/src/app/globals.css` já define as variáveis do tema escuro (bloco `.dark` e `@custom-variant dark`), mas nada aplica a classe `dark` ao documento, não existe controle para a pessoa escolher o tema e nenhuma preferência é lembrada. Hoje o tema escuro não pode ser ligado nem testado pela interface.

#### Resultado desejado

A pessoa autenticada escolhe entre Claro, Escuro e Sistema no menu da pessoa, vê a escolha aplicada na hora e a encontra lembrada ao voltar ao sistema no mesmo navegador. Cada página, inclusive `/login`, `/nova-senha` e a tela de erro global, já nasce no tema certo, sem piscar no tema trocado. As telas atuais ficam legíveis e acessíveis nos dois temas.

#### Métricas de sucesso

- Nenhuma ocorrência de página exibida no tema trocado antes da primeira pintura em recarregamento (AC-006, AC-007 e AC-016).
- Texto com contraste mínimo de 4,5:1 e elementos de interface com contraste mínimo de 3:1 nos dois temas (AC-010).
- A preferência é lembrada em cada recarregamento quando o armazenamento do navegador está disponível (AC-001 e AC-004).
- Nenhuma cor fixa fora dos tokens do tema nas fontes do frontend, salvo as exceções declaradas (AC-017).

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001** [high] O script em linha no head do layout raiz, com suppressHydrationWarning no elemento html, aplica uma preferência de tema guardada no navegador antes da primeira pintura — Verdict: verified — Confidence: high — Evidence: research/nextjs-prevenir-flash/nota.md#técnica — Budget: 1/3

#### Fontes e contexto consultados

- `specs/backlog/0033-tema-escuro-dark-mode-no-frontend.md` (BACKLOG-0033, refinado em 2026-10-05) e as cinco respostas confirmadas na descoberta de Interface.
- `INTERFACE.md`, `DESIGNSYSTEM.MD` e `.specsfy/RULES.md` do projeto.
- `frontend/src/app/globals.css`, `frontend/src/app/layout.tsx`, `frontend/src/app/global-error.tsx`, `frontend/src/app/(autenticado)/layout.tsx`, `frontend/src/features/auth/MenuPessoa.tsx`, `frontend/src/components/ui/dropdown-menu.tsx`, `dialog.tsx`, `sheet.tsx`, `frontend/next.config.ts` e `frontend/vitest.config.mts`.
- Varredura de cores fixas nas fontes do frontend (2026-10-05): fora de testes e de `globals.css`, só a página-modelo `frontend/src/app/page.tsx` e os fundos `bg-black/10` de `dialog.tsx` e `sheet.tsx` usam cor fixa; o restante usa tokens (`bg-background`, `text-muted-foreground`, `border`).
- `frontend/AGENTS.md`, que manda consultar a documentação local do Next 16 antes de escrever código.

#### Documentação consultada

- Next.js 16.3.4, guia local "How to prevent flash before hydration" em `frontend/node_modules/next/dist/docs/01-app/02-guides/preventing-flash-before-hydration.md` (consultado em 2026-10-05): técnica do script em linha para temas e preferências guardadas no navegador.
- Tailwind CSS v4 (variante `dark` declarada em `globals.css`) e shadcn/ui (preset `base-nova`, Base UI), conforme `INTERFACE.md`.

#### Artefatos de pesquisa armazenados

- `specs/defined/0024-tema-escuro-dark-mode-no-frontend/research/nextjs-prevenir-flash/`: nota de proveniência própria sobre o guia local do Next 16.3.4 (licença MIT, consultado em 2026-10-05), sem cópia do conteúdo do guia; registra a técnica e o impacto nesta spec.

#### Dúvidas respondidas

- **Q**: Como a pessoa escolhe o tema? → **A**: Claro, Escuro e Sistema, com Sistema como padrão inicial.
- **Q**: Onde fica o controle? → **A**: No menu da pessoa (`MenuPessoa`), nas telas autenticadas; `/login` e `/nova-senha` seguem o tema do sistema, sem controle.
- **Q**: Onde a escolha é guardada? → **A**: Somente no navegador; a preferência por conta da pessoa fica como evolução futura, fora do escopo.
- **Q**: Qual a cobertura nas telas existentes? → **A**: Todas as telas atuais corretas nos dois temas, com ajuste de cor onde um componente ficar ilegível.
- **Q**: Quais critérios de qualidade? → **A**: Sem piscar no carregamento, contraste WCAG AA e controle operável por teclado e identificado para leitores de tela.

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Seletor com as opções Claro, Escuro e Sistema no menu da pessoa, indicando a opção ativa.
- Aplicação imediata do tema, persistência no navegador e reação às mudanças do tema do computador quando Sistema está ativo.
- Script antes da primeira pintura no layout raiz e na tela de erro global; `/login` e `/nova-senha` herdam o tema pelo layout raiz.
- Ajuste dos tokens e dos componentes das telas atuais onde o contraste ou a separação visual falharem no tema escuro, incluindo o fundo de Dialog e Sheet.
- Testes automatizados de lógica, componentes, contraste, cores fixas e CSP; revisão visual das telas nos dois temas.

#### Fora de escopo

- Preferência de tema por conta da pessoa, guardada no backend (evolução futura).
- Temas além de Claro e Escuro, e personalização de cores.
- Controle de tema em `/login` e `/nova-senha`.
- Redesenho de telas, mudança de conteúdo, de rotas ou de permissões.
- A rota `/`, que ainda mostra a página-modelo do Next.js; tratar em item próprio.
- Sincronização da preferência entre abas abertas ao mesmo tempo.

#### Atores

- **Pessoa autenticada (owner, admin ou member)**: escolhe o tema pelo menu da pessoa e o vê aplicado nas telas autenticadas.
- **Pessoa sem sessão**: vê `/login` e `/nova-senha` no tema salvo ou, sem preferência, no tema do computador, sem controle.

### 4. Princípios e restrições do projeto

- **PR-001**: Reaproveitar tokens, primitives e blocos existentes antes de criar valores locais; o tema muda aparência por tokens, nunca por cor fixa em componente (`DESIGNSYSTEM.MD`, seção de tokens).
- **PR-002**: Registrar em `INTERFACE.md`, na mesma tarefa, cada bloco criado ou estendido, com origem, consumidores e regra de reuso.
- **PR-003**: A página ou a rota apenas compõe blocos; a lógica de tema vive em módulo e hook próprios.
- **PR-004**: Consultar a documentação local do Next 16 antes de escrever código de layout (`frontend/AGENTS.md`).
- **PR-005**: Cada entrega usa uma branch própria, `spec/0024-tema-escuro-dark-mode-no-frontend`, e o PR só abre depois de `Complete`, com os dois jobs do CI verdes (`.specsfy/RULES.md`).
- **PR-006**: A revisão visual é obrigatória e confere bordas, espaçamentos, margens, padding e tipografia nos dois temas.

### 5. Histórias de usuário

#### US-001 — Escolher o tema e ter a escolha lembrada (P1)

Como pessoa autenticada, quero escolher entre Claro, Escuro e Sistema no menu da pessoa e ter a escolha lembrada neste navegador, para trabalhar no tema mais confortável sem repetir a escolha.

**Por que P1**: é o pedido central e destrava o uso do tema escuro, que já tem os tokens prontos.
**Teste independente**: abrir o menu da pessoa, escolher Escuro, recarregar a página e confirmar que o tema escuro continua ativo.
**Requisitos**: FR-001, FR-002, FR-003, FR-004

#### US-002 — Ver cada página já no tema certo (P1)

Como pessoa usuária, quero que cada página, inclusive o login e a tela de erro, já apareça no tema certo ao carregar, para não ver um clarão do tema trocado.

**Por que P1**: sem isso o tema escuro piora a experiência em cada recarregamento e em cada primeira visita.
**Teste independente**: com Escuro salvo, recarregar `/workspaces` e `/login` com o cache desabilitado e confirmar que nenhuma pintura ocorre em tema claro.
**Requisitos**: FR-005, FR-006

#### US-003 — Usar as telas atuais com conforto nos dois temas (P2)

Como pessoa usuária, quero que as telas atuais fiquem legíveis e acessíveis no tema claro e no escuro, para ler e operar o sistema sem esforço, inclusive por teclado e leitor de tela.

**Por que P2**: depende do mecanismo de P1 e valida a cobertura das telas e a acessibilidade.
**Teste independente**: percorrer workspaces, execuções, pessoas, diálogos e o painel do Assistente nos dois temas e conferir contraste, foco e legibilidade.
**Requisitos**: FR-007, FR-008

### 6. Cenários BDD de aceite

#### AC-001 — Escolher Escuro aplica o tema e grava a preferência

**Cobre**: US-001, FR-001, FR-002, NFR-003

```gherkin
@US-001 @FR-001 @FR-002 @NFR-003 @AC-001
Feature: Tema escuro do frontend

  Scenario: Escolher Escuro aplica o tema e grava a preferência
    Given uma pessoa autenticada sem preferência de tema salva
    When ela abre o menu da pessoa e escolhe "Escuro"
    Then o tema escuro é aplicado na hora, sem recarregar a página
    And a preferência "escuro" fica gravada no navegador
```

#### AC-002 — O menu mostra as três opções e marca a ativa

**Cobre**: US-001, FR-001, FR-008, NFR-003

```gherkin
@US-001 @FR-001 @FR-008 @NFR-003 @AC-002
Feature: Tema escuro do frontend

  Scenario: O menu mostra as três opções e marca a ativa
    Given uma pessoa autenticada com a opção Sistema ativa
    When ela abre o menu da pessoa
    Then vê o grupo "Tema" com as opções Claro, Escuro e Sistema
    And somente "Sistema" aparece marcada como ativa
```

#### AC-003 — Sistema acompanha o computador em tempo real

**Cobre**: US-001, FR-002, FR-003

```gherkin
@US-001 @FR-002 @FR-003 @AC-003
Feature: Tema escuro do frontend

  Scenario: Sistema acompanha o computador em tempo real
    Given a opção Sistema ativa e o computador no tema claro
    When o computador passa para o tema escuro com o sistema aberto
    Then o tema escuro é aplicado sem recarregar a página
    And ao voltar para o claro, o tema claro é aplicado
```

#### AC-004 — Sem preferência ou com valor inválido, vale Sistema

**Cobre**: US-001, FR-002, FR-004

```gherkin
@US-001 @FR-002 @FR-004 @AC-004
Feature: Tema escuro do frontend

  Scenario: Sem preferência ou com valor inválido, vale Sistema
    Given um navegador sem preferência salva, ou com um valor salvo desconhecido
    When a pessoa abre qualquer tela
    Then a opção ativa é Sistema
    And o tema acompanha o do computador
```

#### AC-005 — Armazenamento indisponível não gera erro

**Cobre**: US-001, FR-002, FR-004, NFR-004

```gherkin
@US-001 @FR-002 @FR-004 @NFR-004 @AC-005
Feature: Tema escuro do frontend

  Scenario: Armazenamento indisponível não gera erro
    Given um navegador que bloqueia o armazenamento local
    When a pessoa escolhe "Escuro" no menu
    Then o tema escuro é aplicado na sessão atual, sem mensagem de erro
    And ao recarregar, o sistema volta a seguir o tema do computador
```

#### AC-006 — Sem piscar quando Escuro está salvo

**Cobre**: US-002, FR-005, NFR-001

```gherkin
@US-002 @FR-005 @NFR-001 @AC-006
Feature: Tema escuro do frontend

  Scenario: Sem piscar quando Escuro está salvo
    Given a preferência "escuro" salva no navegador
    When a pessoa recarrega uma tela autenticada
    Then o tema escuro já está aplicado ao documento antes da primeira pintura
    And a página nunca aparece no tema claro
```

#### AC-007 — Sem piscar na primeira visita com o computador escuro

**Cobre**: US-002, FR-003, FR-004, FR-005, NFR-001

```gherkin
@US-002 @FR-003 @FR-004 @FR-005 @NFR-001 @AC-007
Feature: Tema escuro do frontend

  Scenario: Sem piscar na primeira visita com o computador escuro
    Given nenhuma preferência salva e o computador no tema escuro
    When a pessoa abre o sistema pela primeira vez
    Then o tema escuro é aplicado antes da primeira pintura
    And a página não passa pelo tema claro
```

#### AC-008 — Login e nova senha seguem o tema, sem controle

**Cobre**: US-002, FR-003, FR-006

```gherkin
@US-002 @FR-003 @FR-006 @AC-008
Feature: Tema escuro do frontend

  Scenario: Login e nova senha seguem o tema, sem controle
    Given o computador no tema escuro e nenhuma sessão ativa
    When a pessoa abre /login ou /nova-senha
    Then a tela aparece no tema escuro
    And não existe controle de tema nela
```

#### AC-009 — A tela de erro global respeita o tema

**Cobre**: US-002, FR-005, FR-006

```gherkin
@US-002 @FR-005 @FR-006 @AC-009
Feature: Tema escuro do frontend

  Scenario: A tela de erro global respeita o tema
    Given a preferência "escuro" salva e uma falha que aciona a tela de erro global
    When a tela de erro global é exibida
    Then ela aparece no tema escuro
    And o botão "Tentar novamente" continua visível e utilizável
```

#### AC-010 — Contraste dos tokens nos dois temas

**Cobre**: US-003, FR-007, NFR-002

```gherkin
@US-003 @FR-007 @NFR-002 @AC-010
Feature: Tema escuro do frontend

  Scenario: Contraste dos tokens nos dois temas
    Given os tokens de cor do tema claro e do tema escuro
    When se calcula o contraste dos pares de texto e dos elementos de interface
    Then os pares de texto têm razão mínima de 4,5:1
    And o anel de foco e a borda de campo têm razão mínima de 3:1 sobre o fundo da página
```

#### AC-011 — Fundo de diálogo e painel separa o conteúdo no tema escuro

**Cobre**: US-003, FR-007, NFR-002

```gherkin
@US-003 @FR-007 @NFR-002 @AC-011
Feature: Tema escuro do frontend

  Scenario: Fundo de diálogo e painel separa o conteúdo no tema escuro
    Given o tema escuro ativo e um diálogo ou painel lateral aberto
    When a pessoa olha a tela
    Then o fundo atrás do diálogo ou painel usa preto com opacidade de pelo menos 50%
    And o conteúdo do diálogo ou painel permanece legível
```

#### AC-012 — O seletor opera somente pelo teclado

**Cobre**: US-003, FR-001, FR-008, NFR-003

```gherkin
@US-003 @FR-001 @FR-008 @NFR-003 @AC-012
Feature: Tema escuro do frontend

  Scenario: O seletor opera somente pelo teclado
    Given o menu da pessoa focado e uma pessoa usando somente o teclado
    When ela abre o menu, navega até o grupo "Tema" e escolhe "Escuro" com Enter
    Then o tema escuro é aplicado
    And o foco volta ao gatilho do menu
```

#### AC-013 — As opções são anunciadas com nome e estado

**Cobre**: US-003, FR-008, NFR-003

```gherkin
@US-003 @FR-008 @NFR-003 @AC-013
Feature: Tema escuro do frontend

  Scenario: As opções são anunciadas com nome e estado
    Given uma tecnologia assistiva e o menu da pessoa aberto
    When ela percorre as opções do grupo "Tema"
    Then cada opção é anunciada com o seu nome
    And a opção ativa é anunciada como marcada
```

#### AC-014 — Sem nova dependência, sem mudança de CSP, backend ou banco

**Cobre**: FR-002, FR-005, NFR-004

```gherkin
@FR-002 @FR-005 @NFR-004 @AC-014
Feature: Tema escuro do frontend

  Scenario: Sem nova dependência, sem mudança de CSP, backend ou banco
    Given o mecanismo de tema implementado
    When se inspecionam o pacote do frontend, a configuração do Next e o diff da entrega
    Then a CSP continua permitindo script em linha da própria origem
    And não há nova dependência de tema nem alteração em backend ou banco
```

#### AC-015 — Trocar o tema não altera conteúdo, rotas nem permissões

**Cobre**: US-001, FR-002, NFR-004

```gherkin
@US-001 @FR-002 @NFR-004 @AC-015
Feature: Tema escuro do frontend

  Scenario: Trocar o tema não altera conteúdo, rotas nem permissões
    Given uma pessoa com papel member autenticada
    When ela troca o tema pelo menu da pessoa
    Then os itens do menu e as rotas continuam os mesmos
    And a pessoa continua sem acesso a Pessoas, mudando somente a aparência
```

#### AC-016 — O layout raiz emite o script de tema no head

**Cobre**: US-002, FR-005, FR-006, NFR-001

```gherkin
@US-002 @FR-005 @FR-006 @NFR-001 @AC-016
Feature: Tema escuro do frontend

  Scenario: O layout raiz emite o script de tema no head
    Given a renderização do layout raiz
    When o HTML é gerado
    Then o script de tema está no head, antes do conteúdo da página
    And o texto do script tem menos de 1 KB
    And o elemento html aceita a mudança de classe sem erro de hidratação
```

#### AC-017 — Nenhuma fonte usa cor fixa fora dos tokens do tema

**Cobre**: US-003, FR-007, NFR-002

```gherkin
@US-003 @FR-007 @NFR-002 @AC-017
Feature: Tema escuro do frontend

  Scenario: Nenhuma fonte usa cor fixa fora dos tokens do tema
    Given as fontes dos componentes e das telas do frontend
    When elas são varridas em busca de cores fixas
    Then nenhuma usa cor fora dos tokens do tema
    And as únicas exceções são os fundos de Dialog e Sheet e a página-modelo da rota raiz
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O menu da pessoa (`MenuPessoa`) deve oferecer, no grupo "Tema", as opções Claro, Escuro e Sistema como itens de escolha única, marcando a opção ativa.
- **FR-002**: Ao escolher uma opção, o sistema deve aplicar o tema na hora, sem recarregar a página, e gravar a preferência no navegador na chave `rag-pipeline-tema`, com os valores `claro`, `escuro` ou `sistema`.
- **FR-003**: Com Sistema ativo, o sistema deve seguir a preferência de tema do computador (`prefers-color-scheme`) e reagir às mudanças dela em tempo real, sem recarregar a página.
- **FR-004**: Sem preferência salva, ou com valor salvo desconhecido, o sistema deve usar Sistema; se o armazenamento do navegador estiver indisponível, deve aplicar a escolha na sessão atual, sem mensagem de erro, e voltar a Sistema ao recarregar.
- **FR-005**: O sistema deve aplicar o tema resolvido ao elemento `html` por um script em linha no `head`, antes da primeira pintura, no layout raiz e na tela de erro global.
- **FR-006**: `/login`, `/nova-senha` e a tela de erro global devem aparecer no tema salvo ou, sem preferência, no tema do computador, sem exibir controle de tema.
- **FR-007**: As telas e os componentes atuais devem usar os tokens do tema, sem cor fixa que prejudique a leitura; o fundo de Dialog e Sheet deve usar preto com opacidade mínima de 50% no tema escuro, mantendo os 10% atuais no tema claro.
- **FR-008**: O controle de tema deve ser operável somente por teclado e comunicar nome e estado às tecnologias assistivas, como itens de escolha única marcados.

#### Não funcionais

- **NFR-001**: Desempenho percebido. O tema é aplicado antes da primeira pintura, por script síncrono menor que 1 KB e sem requisição de rede. **Verificação**: teste do script e do layout raiz; verificação manual com cache desabilitado e CPU reduzida nas ferramentas do navegador.
- **NFR-002**: Contraste e legibilidade. Texto com razão mínima de 4,5:1 e anel de foco e borda de campo com razão mínima de 3:1 sobre o fundo, nos dois temas. **Verificação**: teste Vitest que calcula a razão a partir dos tokens de `globals.css`, varredura de cores fixas e revisão visual das telas.
- **NFR-003**: Acessibilidade. O controle é alcançável e operável por teclado, mantém o foco visível e expõe papel e estado às tecnologias assistivas. **Verificação**: testes de componente com Testing Library e `user-event`, e revisão manual com teclado.
- **NFR-004**: Compatibilidade e contenção. Nenhuma dependência nova, nenhuma mudança na CSP, no backend ou no banco, e nenhum erro quando o armazenamento está indisponível. **Verificação**: teste da CSP, inspeção do diff de `package.json`, `package-lock.json` e `src/` do backend, e teste de armazenamento bloqueado.

#### Erros e casos-limite

- Valor salvo desconhecido → tratado como Sistema, sem regravar até nova escolha.
- Armazenamento bloqueado ou cheio → a escolha vale só na sessão atual e o sistema volta a Sistema ao recarregar, sem erro visível.
- `matchMedia` indisponível → o sistema usa o tema claro.
- JavaScript desativado → a página aparece no tema claro padrão e o controle não está disponível.
- Troca de tema com diálogo ou painel aberto → o diálogo ou painel muda junto, sem fechar.
- Saída da conta (logout) → a preferência permanece, porque pertence ao navegador e não à pessoa.
- Mudança do tema do computador com Claro ou Escuro fixados → ignorada.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Frontend em `frontend/`: Next.js 16.3.4 (App Router), React 19.2.8, TypeScript, Tailwind CSS v4, shadcn/ui no preset `base-nova` (Base UI) e Vitest 5 com jsdom e Testing Library (`test:tdd` = `vitest run`).
- `frontend/src/app/globals.css` declara `@custom-variant dark (&:is(.dark *))` e o bloco `.dark` com os tokens do tema escuro; `@layer base` aplica `bg-background text-foreground` ao `body`.
- `frontend/src/app/layout.tsx` é o layout raiz (fontes Geist, `<html lang="pt-BR">`) e não tem script nem preferência de tema.
- `frontend/src/app/global-error.tsx` renderiza o próprio `<html>` e `<body>` e importa `globals.css`.
- `frontend/src/app/(autenticado)/layout.tsx` é o shell das telas autenticadas; hospeda `MenuPessoa` (sobre `dropdown-menu`) e o `AssistenteLauncher`. `/login` e `/nova-senha` ficam fora desse shell.
- `frontend/src/components/ui/dropdown-menu.tsx` expõe `DropdownMenu`, `Trigger`, `Content`, `Item`, `Group`, `Label` e `Separator` sobre Base UI, sem itens de escolha única.
- `frontend/src/components/ui/dialog.tsx` e `sheet.tsx` usam o fundo `bg-black/10`.
- `frontend/next.config.ts` aplica uma CSP com `script-src 'self' 'unsafe-inline'`, o que permite o script em linha da própria origem.
- A sessão usa `sessionStorage` (`frontend/src/lib/session.ts`); a preferência de tema usa `localStorage`, que sobrevive ao fim da sessão e ao logout.

#### Arquitetura e módulos

- **Módulo `frontend/src/lib/tema.ts`**: tipo `PreferenciaTema` (`claro`, `escuro`, `sistema`), constante `CHAVE_TEMA` (`rag-pipeline-tema`), funções puras `normalizarPreferencia`, `resolverTema` e `aplicarTema`, leitura e gravação com tratamento de falha do armazenamento, e a função `scriptTema()` que devolve o texto do script em linha a partir da mesma constante.
- **Hook `frontend/src/features/tema/useTema.ts`**: expõe `preferencia` e `escolher`, aplica o tema, grava a preferência e, com Sistema ativo, acompanha `prefers-color-scheme`; o valor inicial no servidor é `sistema` e a leitura do armazenamento ocorre só no cliente, sem divergência de hidratação.
- **Bloco `frontend/src/features/tema/ScriptTema.tsx`**: renderiza o script em linha com o padrão do guia do Next (tipo `text/javascript` no servidor e `text/plain` no cliente, com `suppressHydrationWarning`), para não gerar aviso do React.
- **Bloco `frontend/src/features/tema/SeletorTema.tsx`**: grupo "Tema" com três itens de escolha única, usando o hook.
- **Primitive `frontend/src/components/ui/dropdown-menu.tsx`**: estendida com `DropdownMenuRadioGroup` e `DropdownMenuRadioItem` sobre `Menu.RadioGroup` e `Menu.RadioItem` do Base UI.
- **`frontend/src/features/auth/MenuPessoa.tsx`**: inclui o `SeletorTema` entre o rótulo da pessoa e "Trocar senha".
- **`frontend/src/app/layout.tsx`** e **`frontend/src/app/global-error.tsx`**: `suppressHydrationWarning` no `html` e `ScriptTema` no `head`.
- **`frontend/src/app/globals.css`**: `color-scheme` por tema e, se o teste de contraste exigir, ajuste dos tokens.
- **`frontend/src/components/ui/dialog.tsx`** e **`sheet.tsx`**: fundo com preto a 50% no tema escuro (`dark:bg-black/50`), mantendo `bg-black/10` no claro.

#### Migrations

- Não aplicável: nenhuma persistência no servidor.

#### Models

- Não aplicável: nenhum model; a preferência é um valor do navegador.

#### Controllers e casos de uso

- Não aplicável: nenhum endpoint ou caso de uso no backend.

#### Views e experiência

- Menu da pessoa com o grupo "Tema" (três itens de escolha única) entre o rótulo e as ações da conta.
- Estados: ativa/inativa por item; sem estado de carregamento, vazio ou erro, porque a ação é local e imediata.
- Acessibilidade: itens com papel de escolha única e estado marcado, teclado e foco do `DropdownMenu` do Base UI.
- Arquivos: `frontend/src/features/tema/SeletorTema.tsx` e `frontend/src/features/auth/MenuPessoa.tsx`.

#### Queries e repositórios

- Não aplicável.

#### Jobs e processamento assíncrono

- Não aplicável.

#### Estrutura de arquivos

```text
specs/defined/0024-tema-escuro-dark-mode-no-frontend/
  spec.md
  research/
    nextjs-prevenir-flash/
      nota.md
frontend/
  src/
    app/
      layout.tsx                       (alterado)
      global-error.tsx                 (alterado)
      globals.css                      (alterado)
      globals.contraste.test.ts        (novo)
      cores-fixas.test.ts              (novo)
      layout.test.tsx                  (novo)
      telas-de-acesso.test.tsx         (novo)
      global-error.test.tsx            (alterado)
    components/ui/
      dropdown-menu.tsx                (alterado)
      dialog.tsx                       (alterado)
      sheet.tsx                        (alterado)
      backdrops.test.tsx               (novo)
    features/
      tema/
        ScriptTema.tsx                 (novo)
        SeletorTema.tsx                (novo)
        useTema.ts                     (novo)
        ScriptTema.test.tsx            (novo)
        SeletorTema.test.tsx           (novo)
        SeletorTema.a11y.test.tsx      (novo)
        useTema.test.tsx               (novo)
      auth/
        MenuPessoa.tsx                 (alterado)
        MenuPessoa.test.tsx            (alterado)
    lib/
      tema.ts                          (novo)
      tema.test.ts                     (novo)
      api-proxy.test.ts                (alterado)
INTERFACE.md                           (alterado)
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Preferência de tema (local do navegador) | Chave `rag-pipeline-tema` em `localStorage` | Valor em `claro`, `escuro` ou `sistema`; ausente ou desconhecido equivale a `sistema` | Nenhuma: não se liga a Pessoa, Sessão nem a qualquer registro do backend |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Preferência de tema | sistema (padrão) | Pessoa escolhe Escuro | escuro | Grava `escuro`; aplica o tema na hora |
| Preferência de tema | escuro | Pessoa escolhe Claro | claro | Grava `claro`; aplica o tema na hora |
| Preferência de tema | claro ou escuro | Pessoa escolhe Sistema | sistema | Grava `sistema`; passa a seguir o computador |
| Preferência de tema | qualquer | Valor lido é desconhecido | sistema | Não regrava até nova escolha |
| Preferência de tema | qualquer | Armazenamento indisponível | sistema ao recarregar | A escolha vale só na sessão atual |

#### Migração e retenção

- Não aplicável: nenhuma migração. A preferência não expira; limpar os dados do navegador a remove e devolve o padrão Sistema. Duas pessoas que usam o mesmo navegador compartilham a preferência, porque ela pertence ao navegador.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. A entrega é um controle no menu da pessoa e o comportamento visual de todas as telas atuais nos dois temas.

#### Stack e convenções de interface

- Next.js 16.3.4 (App Router), React 19.2.8, TypeScript, Tailwind CSS v4 com `@custom-variant dark`, shadcn/ui no preset `base-nova` sobre Base UI, ícones `lucide-react`, testes com Vitest, jsdom e Testing Library.
- Fontes locais observadas: `INTERFACE.md`, `DESIGNSYSTEM.MD`, `.specsfy/STACK.md`, `frontend/components.json`, `frontend/src/app/globals.css` e as telas listadas abaixo.
- O sistema atual é preservado: conteúdo, rotas, permissões, shell autenticado, `PageHeader`, `DataGrid*`, formulários, diálogos e o painel do Assistente não mudam. Muda a aparência, por tokens, e o menu da pessoa ganha o grupo "Tema".
- ReUI está configurado mas sem blocos instalados; esta entrega não precisa de composição ReUI.

#### Telas e responsabilidades

- **Telas autenticadas** (`/workspaces`, `/workspaces/[id]`, `/execucoes/[id]`, `/pessoas`, `/pessoas/[id]`): continuam com a mesma tarefa; passam a aparecer no tema escolhido.
- **Menu da pessoa** (cabeçalho do shell autenticado): ganha o grupo "Tema" para escolher Claro, Escuro ou Sistema.
- **`/login` e `/nova-senha`**: continuam com a mesma tarefa; aparecem no tema salvo ou no do computador, sem controle.
- **Tela de erro global** (`global-error.tsx`): continua como última recuperação; aparece no tema salvo ou no do computador.
- **Diálogos e painéis** (`Dialog`, `Sheet`, painel do Assistente): continuam iguais, com o fundo em preto a 50% no tema escuro.
- **`/projeto`** continua sendo só um redirecionamento permanente para `/workspaces`, sem aparência própria. A rota `/` fica fora de escopo.

#### Fluxo de informação e navegação

- A pessoa autentica, abre o menu da pessoa no cabeçalho e escolhe o tema; o tema muda na hora e é gravado no navegador. Ao recarregar ou voltar depois, o script do `head` reaplica o tema antes da primeira pintura.
- Sem sessão, a pessoa chega a `/login` ou `/nova-senha` e vê o tema salvo ou o do computador.
- Não há troca de rota nem confirmação ao escolher o tema; escolher fecha o menu e devolve o foco ao gatilho.
- Breadcrumb: o shell autenticado mantém a trilha existente (Equipe, módulo e tela atual) sem alteração; `/login` e `/nova-senha` continuam sem trilha.

#### Menus e navegação principal

- A navegação principal do shell (Workspaces para todas as pessoas, Pessoas só para owner e admin) não muda.
- O menu da pessoa ganha o grupo "Tema" entre o rótulo da pessoa (nome e papel) e as ações da conta: ordem final rótulo, separador, "Tema" com Claro, Escuro e Sistema, separador, "Trocar senha" e "Sair".
- Permissão: o controle aparece para qualquer papel autenticado. Responsivo: o menu mantém o comportamento atual, ancorado ao gatilho, com o nome da pessoa contido por `truncate`.

#### Formulários e ações

- Não há formulário. A ação é a escolha de um entre três itens de escolha única, sem campos, validação ou envio; a ação ocorre dentro do menu ancorado, sem página, painel lateral ou modal próprio.
- Falha de gravação no navegador não gera mensagem: o tema vale na sessão atual.

#### Composição e disposição

- O grupo "Tema" ocupa a largura do menu e usa o mesmo espaçamento, tipografia e raio dos itens atuais do `DropdownMenu`; o indicador de seleção fica à esquerda ou à direita conforme o padrão do item de escolha única do Base UI.
- Mobile e desktop: sem diferença de composição; o menu continua contido na largura da tela.
- Componentes existentes reaproveitados: `DropdownMenu`, `Group`, `Label`, `Separator` e `Item`.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Menu da pessoa | `SeletorTema` | Grupo "Tema" com três itens de escolha única | `frontend/src/features/tema/SeletorTema.tsx` | `DropdownMenuGroup`, `DropdownMenuLabel`, `DropdownMenuRadioGroup`, `DropdownMenuRadioItem` | Próprio, sobre `dropdown-menu` (shadcn/ui, Base UI) | Novo; reaproveita o menu da pessoa existente |
| Menu da pessoa | `DropdownMenuRadioGroup` e `DropdownMenuRadioItem` | Itens de escolha única do menu | `frontend/src/components/ui/dropdown-menu.tsx` | `Menu.RadioGroup`, `Menu.RadioItem` e `Menu.RadioItemIndicator` do Base UI | shadcn/ui (Base UI) | Estende a primitive existente; sem menu paralelo |
| Menu da pessoa | `MenuPessoa` | Hospeda o `SeletorTema` | `frontend/src/features/auth/MenuPessoa.tsx` | `DropdownMenu` | Próprio | Extensão do bloco existente |
| Todas as telas | `useTema` | Estado da preferência, gravação, aplicação e reação ao computador | `frontend/src/features/tema/useTema.ts` | Hook React | Próprio | Novo; ponto único de acesso ao tema |
| Todas as telas | módulo de tema | Regras puras e texto do script | `frontend/src/lib/tema.ts` | Funções e constantes | Próprio | Novo; fonte única da chave e dos valores |
| Todas as telas | `ScriptTema` | Aplica o tema antes da primeira pintura | `frontend/src/features/tema/ScriptTema.tsx` | Script em linha | Próprio, padrão do guia do Next 16 | Novo; usado no layout raiz e no erro global |
| Todas as telas | `RootLayout` | Hospeda o script e aceita a mudança de classe no `html` | `frontend/src/app/layout.tsx` | Layout raiz | Próprio | Extensão do bloco existente |
| Erro global | `GlobalError` | Aplica o tema na última recuperação | `frontend/src/app/global-error.tsx` | Documento completo | Próprio | Extensão do bloco existente |
| Diálogos e painéis | `Dialog` e `Sheet` | Fundo com opacidade mínima de 50% no tema escuro | `frontend/src/components/ui/dialog.tsx`, `frontend/src/components/ui/sheet.tsx` | `DialogOverlay`, `SheetOverlay` | shadcn/ui (Base UI) | Ajuste de classe do fundo; claro inalterado |

- Cada bloco novo ou estendido é registrado em `INTERFACE.md` na mesma tarefa, com arquivo, origem, API, estados e consumidores.
- Esta entrega não usa composição ReUI; usa primitives shadcn/ui e blocos próprios.

#### Estados e acessibilidade

- Cada item tem estado ativo ou inativo, anunciado como marcado ou não; não há loading, vazio, erro ou permissão insuficiente, porque a ação é local e o controle aparece para qualquer papel autenticado.
- Teclado: o gatilho do menu abre com Enter ou Espaço, as setas percorrem os itens, Enter escolhe, Esc fecha, e o foco volta ao gatilho. O foco visível usa o anel do tema.
- Tecnologia assistiva: itens com papel de escolha única e `aria-checked`, agrupados sob o rótulo "Tema".
- Contraste: texto mínimo de 4,5:1 e anel de foco e borda de campo mínimos de 3:1 nos dois temas.
- O `Breadcrumb` do shell mantém a equipe visível, links válidos nos itens anteriores e a tela atual com semântica de página, sem alteração.

#### Contrato CRUD

- Não há CRUD novo nem alterado. Os CRUDs existentes preservam o `PageHeader` único e reutilizável, o `DataGrid` em largura total com a coluna `ID` visível, a linha inteira como link para o detalhe e as ações independentes de editar e apagar; esses blocos só ganham a aparência do tema, sem mudar markup, props ou comportamento.
- Os blocos recorrentes de cabeçalho, tabela, linha, ações, formulário, estados e feedback continuam registrados em `INTERFACE.md` e são reaproveitados sem duplicação.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre durante a implementação, mesmo sem pedido da pessoa, e confere bordas, espaçamentos, margens, padding e tipografia do sistema, nos dois temas, em 360 px e 1280 px de largura.
- Telas e estados a percorrer em cada tema: `/login` (inclusive erro), `/nova-senha`, `/workspaces` (loading, vazio e lista), `/workspaces/[id]`, `/execucoes/[id]` (execução ativa, falha e sucesso com consulta), `/pessoas` e `/pessoas/[id]`, diálogos de confirmação, `Sheet` de formulário, painel do Assistente aberto, menu da pessoa aberto, tela de erro global, conteúdo curto e longo, e foco por teclado.
- Registrar em cada tarefa o método (stack local no Swarm com túnel de porta ou `next dev`), o viewport, os estados percorridos, os achados e os ajustes. Em tarefa sem interface, registrar `Não aplicável` e o motivo.

#### APIs expostas

- Nenhuma: não há endpoint novo nem alteração de endpoint.

#### APIs externas utilizadas

- Nenhuma. A única API do navegador usada é `localStorage` e `matchMedia`, sem rede.

#### Documentação das APIs consultadas

- Guia local do Next.js 16.3.4 "How to prevent flash before hydration" (consultado em 2026-10-05): decisão de usar script em linha no `head` com `suppressHydrationWarning` no `html` (DEC-001).

#### Eventos e outros contratos

- Contrato de armazenamento do navegador: chave `rag-pipeline-tema`, valores `claro`, `escuro` ou `sistema`, ausência equivale a `sistema`. Classe `dark` no `html` para o tema escuro, e `color-scheme` coerente no mesmo elemento.

### 11. Estratégia TDD

- **Unidade**: lógica pura de tema (`frontend/src/lib/tema.test.ts`), hook (`frontend/src/features/tema/useTema.test.tsx`), contraste dos tokens (`frontend/src/app/globals.contraste.test.ts`) e varredura de cores fixas (`frontend/src/app/cores-fixas.test.ts`).
- **Integração/contrato**: seletor no menu da pessoa (`SeletorTema.test.tsx`, `MenuPessoa.test.tsx`), script, layout raiz e erro global (`ScriptTema.test.tsx`, `layout.test.tsx`, `global-error.test.tsx`), telas de acesso (`telas-de-acesso.test.tsx`, que cobre `/login` e `/nova-senha`), fundos de Dialog e Sheet (`backdrops.test.tsx`) e CSP (`api-proxy.test.ts`).
- **BDD/aceite**: o Gherkin da seção 6 orienta os casos; cada caso TDD declara o próprio marcador `SPECSFY: SPEC-0024 <IDs>`, sem criar nem executar arquivo `.feature`.
- **Runner TDD**: Vitest no frontend (`test:tdd` = `vitest run`, já materializado na SPEC-0013 e confirmado como runner de Node do projeto). O backend Python não muda e a suíte Pytest segue como regressão.
- **E2E**: não aplicável nesta entrega; o projeto não tem runner E2E e a jornada é coberta por testes de componente em jsdom.
- **Verificação manual**: revisão visual das telas nos dois temas, em 360 px e 1280 px, e conferência de que a página não pisca com cache desabilitado e CPU reduzida, porque o jsdom não calcula layout nem pintura e porque o contraste real depende do que o navegador renderiza.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, NFR-003, AC-001 | AC-001 na seção 6 | test_escolher_escuro_aplica_o_tema_e_grava_a_preferencia em frontend/src/features/tema/SeletorTema.test.tsx, marcador `SPECSFY: SPEC-0024 US-001 FR-001 FR-002 NFR-003 AC-001` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/features/tema/SeletorTema.test.tsx`: módulo SeletorTema inexistente (asserção do import) | Pending | Pending |
| US-001, FR-001, FR-008, NFR-003, AC-002 | AC-002 na seção 6 | test_menu_mostra_tres_opcoes_com_a_ativa_marcada em frontend/src/features/auth/MenuPessoa.test.tsx, marcador `SPECSFY: SPEC-0024 US-001 FR-001 FR-008 NFR-003 AC-002` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/features/auth/MenuPessoa.test.tsx`: grupo Tema ausente no menu: role group Tema não encontrado | Pending | Pending |
| US-001, FR-002, FR-003, AC-003 | AC-003 na seção 6 | test_sistema_acompanha_o_computador_e_reage_a_mudanca em frontend/src/features/tema/useTema.test.tsx, marcador `SPECSFY: SPEC-0024 US-001 FR-002 FR-003 AC-003` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/features/tema/useTema.test.tsx`: hook useTema inexistente (asserção do import) | Pending | Pending |
| US-001, FR-002, FR-004, AC-004 | AC-004 na seção 6 | test_sem_preferencia_ou_valor_invalido_resolve_para_sistema em frontend/src/lib/tema.test.ts, marcador `SPECSFY: SPEC-0024 US-001 FR-002 FR-004 AC-004` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/lib/tema.test.ts`: módulo lib/tema inexistente (asserção do import) | Pending | Pending |
| US-001, FR-002, FR-004, NFR-004, AC-005 | AC-005 na seção 6 | test_armazenamento_indisponivel_aplica_na_sessao_sem_erro em frontend/src/features/tema/useTema.test.tsx, marcador `SPECSFY: SPEC-0024 US-001 FR-002 FR-004 NFR-004 AC-005` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/features/tema/useTema.test.tsx`: hook useTema inexistente (asserção do import) | Pending | Pending |
| US-002, FR-005, NFR-001, AC-006 | AC-006 na seção 6 | test_script_aplica_escuro_salvo_antes_da_hidratacao em frontend/src/features/tema/ScriptTema.test.tsx, marcador `SPECSFY: SPEC-0024 US-002 FR-005 NFR-001 AC-006` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/features/tema/ScriptTema.test.tsx`: ScriptTema inexistente (asserção do import) | Pending | Pending |
| US-002, FR-003, FR-004, FR-005, NFR-001, AC-007 | AC-007 na seção 6 | test_script_com_sistema_escuro_aplica_a_classe_sem_preferencia_salva em frontend/src/features/tema/ScriptTema.test.tsx, marcador `SPECSFY: SPEC-0024 US-002 FR-003 FR-004 FR-005 NFR-001 AC-007` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/features/tema/ScriptTema.test.tsx`: ScriptTema inexistente (asserção do import) | Pending | Pending |
| US-002, FR-003, FR-006, AC-008 | AC-008 na seção 6 | test_login_e_nova_senha_seguem_o_tema_sem_controle em frontend/src/app/telas-de-acesso.test.tsx, marcador `SPECSFY: SPEC-0024 US-002 FR-003 FR-006 AC-008` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/app/telas-de-acesso.test.tsx`: layout raiz renderizado com /login e /nova-senha sem script de tema | Pending | Pending |
| US-002, FR-005, FR-006, AC-009 | AC-009 na seção 6 | test_erro_global_inclui_o_script_de_tema em frontend/src/app/global-error.test.tsx, marcador `SPECSFY: SPEC-0024 US-002 FR-005 FR-006 AC-009` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/app/global-error.test.tsx`: tela de erro global com head vazio, sem script de tema | Pending | Pending |
| US-003, FR-007, NFR-002, AC-010 | AC-010 na seção 6 | test_pares_de_texto_dos_tokens_atendem_contraste_aa_nos_dois_temas em frontend/src/app/globals.contraste.test.ts, marcador `SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-010` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/app/globals.contraste.test.ts`: claro: muted-foreground/muted 4,34:1, ring 2,59:1, input 1,26:1; escuro: input 1,47:1 | Pending | Pending |
| US-003, FR-007, NFR-002, AC-011 | AC-011 na seção 6 | test_backdrops_de_dialog_e_sheet_usam_opacidade_minima_no_escuro em frontend/src/components/ui/backdrops.test.tsx, marcador `SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-011` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/components/ui/backdrops.test.tsx`: overlays de Dialog e Sheet sem a classe dark:bg-black/50 | Pending | Pending |
| US-003, FR-001, FR-008, NFR-003, AC-012 | AC-012 na seção 6 | test_seletor_opera_so_pelo_teclado em frontend/src/features/tema/SeletorTema.test.tsx, marcador `SPECSFY: SPEC-0024 US-003 FR-001 FR-008 NFR-003 AC-012` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/features/tema/SeletorTema.test.tsx`: módulo SeletorTema inexistente (asserção do import) | Pending | Pending |
| US-003, FR-008, NFR-003, AC-013 | AC-013 na seção 6 | test_opcoes_sao_anunciadas_com_nome_e_estado em frontend/src/features/tema/SeletorTema.a11y.test.tsx, marcador `SPECSFY: SPEC-0024 US-003 FR-008 NFR-003 AC-013` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/features/tema/SeletorTema.a11y.test.tsx`: módulo SeletorTema inexistente (asserção do import) | Pending | Pending |
| FR-002, FR-005, NFR-004, AC-014 | AC-014 na seção 6 | test_csp_continua_permitindo_script_em_linha_e_nada_muda_fora_do_frontend em frontend/src/lib/api-proxy.test.ts, marcador `SPECSFY: SPEC-0024 FR-002 FR-005 NFR-004 AC-014` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/lib/api-proxy.test.ts`: ScriptTema inexistente (asserção do import) | Pending | Pending |
| US-001, FR-002, NFR-004, AC-015 | AC-015 na seção 6 | test_trocar_tema_nao_altera_navegacao_nem_permissoes_do_menu em frontend/src/features/auth/MenuPessoa.test.tsx, marcador `SPECSFY: SPEC-0024 US-001 FR-002 NFR-004 AC-015` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/features/auth/MenuPessoa.test.tsx`: menu sem grupo Tema: menuitemradio Escuro não encontrado | Pending | Pending |
| US-002, FR-005, FR-006, NFR-001, AC-016 | AC-016 na seção 6 | test_layout_raiz_renderiza_o_script_no_head_e_aceita_a_mudanca_de_classe em frontend/src/app/layout.test.tsx, marcador `SPECSFY: SPEC-0024 US-002 FR-005 FR-006 NFR-001 AC-016` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/app/layout.test.tsx`: layout raiz com head vazio, sem script e sem suppressHydrationWarning | Pending | Pending |
| US-003, FR-007, NFR-002, AC-017 | AC-017 na seção 6 | test_fontes_do_frontend_nao_usam_cores_fixas_fora_dos_tokens em frontend/src/app/cores-fixas.test.ts, marcador `SPECSFY: SPEC-0024 US-003 FR-007 NFR-002 AC-017` | RED observado 2026-10-05 com `npm --prefix frontend run test:tdd -- src/app/cores-fixas.test.ts`: dialog.tsx e sheet.tsx sem a variante dark:bg-black/50 | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| US-001 | AC-001 | Componente | frontend/src/features/tema/SeletorTema.test.tsx | Pending |
| US-001 | AC-002 | Componente | frontend/src/features/auth/MenuPessoa.test.tsx | Pending |
| US-001 | AC-003 | Unidade | frontend/src/features/tema/useTema.test.tsx | Pending |
| US-001 | AC-004 | Unidade | frontend/src/lib/tema.test.ts | Pending |
| US-001 | AC-005 | Unidade | frontend/src/features/tema/useTema.test.tsx | Pending |
| US-001 | AC-015 | Componente | frontend/src/features/auth/MenuPessoa.test.tsx | Pending |
| US-002 | AC-006 | Componente | frontend/src/features/tema/ScriptTema.test.tsx | Pending |
| US-002 | AC-007 | Componente | frontend/src/features/tema/ScriptTema.test.tsx | Pending |
| US-002 | AC-008 | Componente | frontend/src/app/telas-de-acesso.test.tsx | Pending |
| US-002 | AC-009 | Componente | frontend/src/app/global-error.test.tsx | Pending |
| US-002 | AC-016 | Componente | frontend/src/app/layout.test.tsx | Pending |
| US-003 | AC-010 | Unidade | frontend/src/app/globals.contraste.test.ts | Pending |
| US-003 | AC-011 | Componente | frontend/src/components/ui/backdrops.test.tsx | Pending |
| US-003 | AC-012 | Componente | frontend/src/features/tema/SeletorTema.test.tsx | Pending |
| US-003 | AC-013 | Componente | frontend/src/features/tema/SeletorTema.a11y.test.tsx | Pending |
| US-003 | AC-017 | Unidade | frontend/src/app/cores-fixas.test.ts | Pending |
| FR-001 | AC-001 | Componente | frontend/src/features/tema/SeletorTema.test.tsx | Pending |
| FR-001 | AC-002 | Componente | frontend/src/features/auth/MenuPessoa.test.tsx | Pending |
| FR-001 | AC-012 | Componente | frontend/src/features/tema/SeletorTema.test.tsx | Pending |
| FR-002 | AC-001 | Componente | frontend/src/features/tema/SeletorTema.test.tsx | Pending |
| FR-002 | AC-003 | Unidade | frontend/src/features/tema/useTema.test.tsx | Pending |
| FR-002 | AC-004 | Unidade | frontend/src/lib/tema.test.ts | Pending |
| FR-002 | AC-005 | Unidade | frontend/src/features/tema/useTema.test.tsx | Pending |
| FR-002 | AC-014 | Integração | frontend/src/lib/api-proxy.test.ts | Pending |
| FR-002 | AC-015 | Componente | frontend/src/features/auth/MenuPessoa.test.tsx | Pending |
| FR-003 | AC-003 | Unidade | frontend/src/features/tema/useTema.test.tsx | Pending |
| FR-003 | AC-007 | Componente | frontend/src/features/tema/ScriptTema.test.tsx | Pending |
| FR-003 | AC-008 | Componente | frontend/src/app/telas-de-acesso.test.tsx | Pending |
| FR-004 | AC-004 | Unidade | frontend/src/lib/tema.test.ts | Pending |
| FR-004 | AC-005 | Unidade | frontend/src/features/tema/useTema.test.tsx | Pending |
| FR-004 | AC-007 | Componente | frontend/src/features/tema/ScriptTema.test.tsx | Pending |
| FR-005 | AC-006 | Componente | frontend/src/features/tema/ScriptTema.test.tsx | Pending |
| FR-005 | AC-007 | Componente | frontend/src/features/tema/ScriptTema.test.tsx | Pending |
| FR-005 | AC-009 | Componente | frontend/src/app/global-error.test.tsx | Pending |
| FR-005 | AC-014 | Integração | frontend/src/lib/api-proxy.test.ts | Pending |
| FR-005 | AC-016 | Componente | frontend/src/app/layout.test.tsx | Pending |
| FR-006 | AC-008 | Componente | frontend/src/app/telas-de-acesso.test.tsx | Pending |
| FR-006 | AC-009 | Componente | frontend/src/app/global-error.test.tsx | Pending |
| FR-006 | AC-016 | Componente | frontend/src/app/layout.test.tsx | Pending |
| FR-007 | AC-010 | Unidade | frontend/src/app/globals.contraste.test.ts | Pending |
| FR-007 | AC-011 | Componente | frontend/src/components/ui/backdrops.test.tsx | Pending |
| FR-007 | AC-017 | Unidade | frontend/src/app/cores-fixas.test.ts | Pending |
| FR-008 | AC-002 | Componente | frontend/src/features/auth/MenuPessoa.test.tsx | Pending |
| FR-008 | AC-012 | Componente | frontend/src/features/tema/SeletorTema.test.tsx | Pending |
| FR-008 | AC-013 | Componente | frontend/src/features/tema/SeletorTema.a11y.test.tsx | Pending |
| NFR-001 | AC-006 | Componente | frontend/src/features/tema/ScriptTema.test.tsx | Pending |
| NFR-001 | AC-007 | Componente | frontend/src/features/tema/ScriptTema.test.tsx | Pending |
| NFR-001 | AC-016 | Componente | frontend/src/app/layout.test.tsx | Pending |
| NFR-002 | AC-010 | Unidade | frontend/src/app/globals.contraste.test.ts | Pending |
| NFR-002 | AC-011 | Componente | frontend/src/components/ui/backdrops.test.tsx | Pending |
| NFR-002 | AC-017 | Unidade | frontend/src/app/cores-fixas.test.ts | Pending |
| NFR-003 | AC-001 | Componente | frontend/src/features/tema/SeletorTema.test.tsx | Pending |
| NFR-003 | AC-002 | Componente | frontend/src/features/auth/MenuPessoa.test.tsx | Pending |
| NFR-003 | AC-012 | Componente | frontend/src/features/tema/SeletorTema.test.tsx | Pending |
| NFR-003 | AC-013 | Componente | frontend/src/features/tema/SeletorTema.a11y.test.tsx | Pending |
| NFR-004 | AC-005 | Unidade | frontend/src/features/tema/useTema.test.tsx | Pending |
| NFR-004 | AC-014 | Integração | frontend/src/lib/api-proxy.test.ts | Pending |
| NFR-004 | AC-015 | Componente | frontend/src/features/auth/MenuPessoa.test.tsx | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0024-tema-escuro-dark-mode-no-frontend/spec.md`
- **Achados**: READY em 2026-10-05. Contagens: 3 US, 8 FR, 4 NFR e 17 AC; cada US, FR e NFR tem no mínimo três AC declarados em `**Cobre**`, e a feature inteira tem 17. Nenhum BLOCKER. A revisão semântica encontrou quatro WARNING, todos resolvidos na mesma etapa, e um finding de segurança aceito.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.
- **FIND-PROD-001** [P3] [Resolved] FR-007 e AC-011 usavam a palavra perceptível sem medida — Refs: FR-007, AC-011 — Evidence: frontend/src/components/ui/dialog.tsx — Effect: o requisito não era verificável por teste — Suggestion: fixar o fundo de Dialog e Sheet em preto com opacidade mínima de 50% no tema escuro, aplicado na redação de FR-007 e AC-011
- **FIND-PROD-002** [P3] [Resolved] AC-008 cobria /login e /nova-senha, mas o teste planejado ficava só em login/page.test.tsx — Refs: AC-008, FR-006 — Evidence: frontend/src/app/login/page.tsx — Effect: a tela nova-senha ficaria sem teste correspondente — Suggestion: usar frontend/src/app/telas-de-acesso.test.tsx, que cobre as duas telas, aplicado nas seções 8, 11 e 12
- **FIND-PROD-003** [P3] [Resolved] O limite de 1 KB do script em NFR-001 não estava ligado a nenhum teste — Refs: NFR-001, AC-016 — Evidence: frontend/src/app/layout.tsx — Effect: o limite poderia ser excedido sem que algum teste falhasse — Suggestion: incluir a checagem do tamanho do script no cenário AC-016, aplicado na seção 6
- **FIND-PROD-004** [P3] [Resolved] A Definition of Done não cobria INTERFACE.md, PROJECT.md, STACK.md, DATABASE.md nem a documentação técnica — Refs: FR-001, NFR-004 — Evidence: INTERFACE.md — Effect: blocos novos poderiam deixar de ser registrados e a documentação ficar desatualizada — Suggestion: acrescentar os itens correspondentes à seção 18, aplicado
- **FIND-SEC-001** [P3] [Accepted] O script em linha do tema depende de unsafe-inline em script-src, já presente na CSP — Refs: NFR-004, AC-014 — Evidence: frontend/next.config.ts — Effect: nenhuma superfície nova, porque o texto do script é constante e não recebe entrada externa — Suggestion: manter a CSP atual e proteger a premissa com o teste de AC-014; decisão registrada em DEC-007

#### Gate do Ato II — Plano

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0024-tema-escuro-dark-mode-no-frontend/spec.md`
- **Achados**: Passed em 2026-10-05. 28 tarefas (17 `[TEST] [TDD]`, 9 `[CODE]`, 1 `[DOC]`, 1 `[TEST]` de regressão), 32 de 32 IDs cobertos. As 17 tarefas TDD (T001 a T017) têm RED válido registrado na seção 11: 40 casos Vitest novos falham pelo comportamento ausente e os 139 existentes seguem verdes. `check_traceability.mjs` reporta 32/32 IDs cobertos. Achado da fase RED: o tema claro também reprova o contraste (muted-foreground sobre muted 4,34:1, ring 2,59:1, input 1,26:1), além do input escuro (1,47:1); T026 ajusta os tokens dos dois temas.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0024-tema-escuro-dark-mode-no-frontend/spec.md .`
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

Runner de testes: Vitest, por `npm --prefix frontend run test:tdd` (já materializado na SPEC-0013). Os testes não usam o banco: esta entrega só toca o frontend, e a suíte Pytest do backend não precisa rodar.

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Vitest falhando em frontend/src/features/tema/SeletorTema.test.tsx — Refs: US-001, FR-001, FR-002, NFR-003, AC-001 — Depends: none
  - [x] **PREP**: Ler o AC-001 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/features/tema/SeletorTema.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_escolher_escuro_aplica_o_tema_e_grava_a_preferencia` em `frontend/src/features/tema/SeletorTema.test.tsx` com marcador próprio `SPECSFY:` do AC-001, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/SeletorTema.test.tsx` e observar RED válido: o módulo `SeletorTema` ainda não existe, e o import falha.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Vitest falhando em frontend/src/features/auth/MenuPessoa.test.tsx — Refs: US-001, FR-001, FR-008, NFR-003, AC-002 — Depends: none
  - [x] **PREP**: Ler o AC-002 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/features/auth/MenuPessoa.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_menu_mostra_tres_opcoes_com_a_ativa_marcada` em `frontend/src/features/auth/MenuPessoa.test.tsx` com marcador próprio `SPECSFY:` do AC-002, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/auth/MenuPessoa.test.tsx` e observar RED válido: o menu ainda não tem o grupo Tema e a consulta pelo papel `menuitemradio` não encontra as três opções.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Vitest falhando em frontend/src/features/tema/useTema.test.tsx — Refs: US-001, FR-002, FR-003, AC-003 — Depends: none
  - [x] **PREP**: Ler o AC-003 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/features/tema/useTema.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_sistema_acompanha_o_computador_e_reage_a_mudanca` em `frontend/src/features/tema/useTema.test.tsx` com marcador próprio `SPECSFY:` do AC-003, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/useTema.test.tsx` e observar RED válido: o hook `useTema` ainda não existe, e o import falha.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T004 [P] [TEST] [TDD] [US-001] Derivar do AC-004 um caso Vitest falhando em frontend/src/lib/tema.test.ts — Refs: US-001, FR-002, FR-004, AC-004 — Depends: none
  - [x] **PREP**: Ler o AC-004 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/lib/tema.test.ts` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_sem_preferencia_ou_valor_invalido_resolve_para_sistema` em `frontend/src/lib/tema.test.ts` com marcador próprio `SPECSFY:` do AC-004, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/lib/tema.test.ts` e observar RED válido: o módulo `tema` ainda não existe, e o import falha.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 um caso Vitest falhando em frontend/src/features/tema/useTema.test.tsx — Refs: US-001, FR-002, FR-004, NFR-004, AC-005 — Depends: none
  - [x] **PREP**: Ler o AC-005 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/features/tema/useTema.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_armazenamento_indisponivel_aplica_na_sessao_sem_erro` em `frontend/src/features/tema/useTema.test.tsx` com marcador próprio `SPECSFY:` do AC-005, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/useTema.test.tsx` e observar RED válido: o hook `useTema` ainda não existe, e o import falha.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 um caso Vitest falhando em frontend/src/features/tema/ScriptTema.test.tsx — Refs: US-002, FR-005, NFR-001, AC-006 — Depends: none
  - [x] **PREP**: Ler o AC-006 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/features/tema/ScriptTema.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_script_aplica_escuro_salvo_antes_da_hidratacao` em `frontend/src/features/tema/ScriptTema.test.tsx` com marcador próprio `SPECSFY:` do AC-006, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/ScriptTema.test.tsx` e observar RED válido: o módulo `ScriptTema` ainda não existe, e o import falha.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso Vitest falhando em frontend/src/features/tema/ScriptTema.test.tsx — Refs: US-002, FR-003, FR-004, FR-005, NFR-001, AC-007 — Depends: none
  - [x] **PREP**: Ler o AC-007 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/features/tema/ScriptTema.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_script_com_sistema_escuro_aplica_a_classe_sem_preferencia_salva` em `frontend/src/features/tema/ScriptTema.test.tsx` com marcador próprio `SPECSFY:` do AC-007, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/ScriptTema.test.tsx` e observar RED válido: o módulo `ScriptTema` ainda não existe, e o import falha.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T008 [P] [TEST] [TDD] [US-002] Derivar do AC-008 um caso Vitest falhando em frontend/src/app/telas-de-acesso.test.tsx — Refs: US-002, FR-003, FR-006, AC-008 — Depends: none
  - [x] **PREP**: Ler o AC-008 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/app/telas-de-acesso.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_login_e_nova_senha_seguem_o_tema_sem_controle` em `frontend/src/app/telas-de-acesso.test.tsx` com marcador próprio `SPECSFY:` do AC-008, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/app/telas-de-acesso.test.tsx` e observar RED válido: o layout raiz renderizado com as telas de acesso ainda não contém o script de tema.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T009 [P] [TEST] [TDD] [US-002] Derivar do AC-009 um caso Vitest falhando em frontend/src/app/global-error.test.tsx — Refs: US-002, FR-005, FR-006, AC-009 — Depends: none
  - [x] **PREP**: Ler o AC-009 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/app/global-error.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_erro_global_inclui_o_script_de_tema` em `frontend/src/app/global-error.test.tsx` com marcador próprio `SPECSFY:` do AC-009, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/app/global-error.test.tsx` e observar RED válido: a tela de erro global ainda não renderiza o script de tema no head.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T010 [P] [TEST] [TDD] [US-003] Derivar do AC-010 um caso Vitest falhando em frontend/src/app/globals.contraste.test.ts — Refs: US-003, FR-007, NFR-002, AC-010 — Depends: none
  - [x] **PREP**: Ler o AC-010 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/app/globals.contraste.test.ts` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_pares_de_texto_dos_tokens_atendem_contraste_aa_nos_dois_temas` em `frontend/src/app/globals.contraste.test.ts` com marcador próprio `SPECSFY:` do AC-010, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/app/globals.contraste.test.ts` e observar RED válido: a borda de campo `--input` do tema escuro (branco a 15%) não alcança 3:1 sobre o fundo; se o caso passar de primeira, endurecer o par `--input` sobre `--background` até falhar.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T011 [P] [TEST] [TDD] [US-003] Derivar do AC-011 um caso Vitest falhando em frontend/src/components/ui/backdrops.test.tsx — Refs: US-003, FR-007, NFR-002, AC-011 — Depends: none
  - [x] **PREP**: Ler o AC-011 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/components/ui/backdrops.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_backdrops_de_dialog_e_sheet_usam_opacidade_minima_no_escuro` em `frontend/src/components/ui/backdrops.test.tsx` com marcador próprio `SPECSFY:` do AC-011, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/components/ui/backdrops.test.tsx` e observar RED válido: os fundos de Dialog e Sheet ainda usam só `bg-black/10`, sem a variante `dark:bg-black/50`.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso Vitest falhando em frontend/src/features/tema/SeletorTema.test.tsx — Refs: US-003, FR-001, FR-008, NFR-003, AC-012 — Depends: none
  - [x] **PREP**: Ler o AC-012 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/features/tema/SeletorTema.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_seletor_opera_so_pelo_teclado` em `frontend/src/features/tema/SeletorTema.test.tsx` com marcador próprio `SPECSFY:` do AC-012, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/SeletorTema.test.tsx` e observar RED válido: o módulo `SeletorTema` ainda não existe, e o import falha.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T013 [P] [TEST] [TDD] [US-003] Derivar do AC-013 um caso Vitest falhando em frontend/src/features/tema/SeletorTema.a11y.test.tsx — Refs: US-003, FR-008, NFR-003, AC-013 — Depends: none
  - [x] **PREP**: Ler o AC-013 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/features/tema/SeletorTema.a11y.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_opcoes_sao_anunciadas_com_nome_e_estado` em `frontend/src/features/tema/SeletorTema.a11y.test.tsx` com marcador próprio `SPECSFY:` do AC-013, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/SeletorTema.a11y.test.tsx` e observar RED válido: o módulo `SeletorTema` ainda não existe, e o import falha.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T014 [TEST] [TDD] Derivar do AC-014 um caso Vitest falhando em frontend/src/lib/api-proxy.test.ts — Refs: FR-002, FR-005, NFR-004, AC-014 — Depends: none
  - [x] **PREP**: Ler o AC-014 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/lib/api-proxy.test.ts` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_csp_continua_permitindo_script_em_linha_e_nada_muda_fora_do_frontend` em `frontend/src/lib/api-proxy.test.ts` com marcador próprio `SPECSFY:` do AC-014, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/lib/api-proxy.test.ts` e observar RED válido: o caso renderiza o `ScriptTema` para confirmar que a CSP o permite, e o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T015 [TEST] [TDD] [US-001] Derivar do AC-015 um caso Vitest falhando em frontend/src/features/auth/MenuPessoa.test.tsx — Refs: US-001, FR-002, NFR-004, AC-015 — Depends: none
  - [x] **PREP**: Ler o AC-015 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/features/auth/MenuPessoa.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_trocar_tema_nao_altera_navegacao_nem_permissoes_do_menu` em `frontend/src/features/auth/MenuPessoa.test.tsx` com marcador próprio `SPECSFY:` do AC-015, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/auth/MenuPessoa.test.tsx` e observar RED válido: o menu ainda não tem o grupo Tema para a pessoa trocar o tema.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T016 [P] [TEST] [TDD] [US-002] Derivar do AC-016 um caso Vitest falhando em frontend/src/app/layout.test.tsx — Refs: US-002, FR-005, FR-006, NFR-001, AC-016 — Depends: none
  - [x] **PREP**: Ler o AC-016 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/app/layout.test.tsx` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_layout_raiz_renderiza_o_script_no_head_e_aceita_a_mudanca_de_classe` em `frontend/src/app/layout.test.tsx` com marcador próprio `SPECSFY:` do AC-016, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/app/layout.test.tsx` e observar RED válido: o layout raiz ainda não renderiza o script de tema nem `suppressHydrationWarning` no `html`.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

- [x] T017 [P] [TEST] [TDD] [US-003] Derivar do AC-017 um caso Vitest falhando em frontend/src/app/cores-fixas.test.ts — Refs: US-003, FR-007, NFR-002, AC-017 — Depends: none
  - [x] **PREP**: Ler o AC-017 na seção 6 e confirmar os IDs cobertos, o arquivo `frontend/src/app/cores-fixas.test.ts` e o nível do teste.
  - [x] **EXECUTE**: Escrever o caso `test_fontes_do_frontend_nao_usam_cores_fixas_fora_dos_tokens` em `frontend/src/app/cores-fixas.test.ts` com marcador próprio `SPECSFY:` do AC-017, sem criar nem executar arquivo `.feature`; mockar `matchMedia` e o armazenamento no próprio teste, porque o jsdom não os fornece.
  - [x] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/app/cores-fixas.test.ts` e observar RED válido: os arquivos permitidos (`dialog.tsx` e `sheet.tsx`) ainda não usam a variante `dark:` do fundo exigida pelo caso.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste automatizado, sem alterar superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs na seção 11.
  - [x] **IMPROVE**: Revisar se o caso falha pelo motivo certo e não por erro de montagem do teste, e registrar o ajuste ou a ausência dele.

#### Fase 2 — Fundação do tema (US-001 e US-002, P1)

**Objetivo**: ter a lógica do tema, o hook e o script de pré-pintura funcionando e testados, ainda sem controle na interface.
**Teste independente**: `npm --prefix frontend run test:tdd -- src/lib/tema.test.ts src/features/tema/useTema.test.tsx src/features/tema/ScriptTema.test.tsx` termina com sucesso.

- [ ] T018 [CODE] [US-001] Implementar a lógica pura do tema em frontend/src/lib/tema.ts — Refs: US-001, US-002, FR-002, FR-003, FR-004, FR-005, NFR-001, NFR-004, AC-003, AC-004, AC-005, AC-006, AC-007 — Depends: T003, T004, T005, T006, T007
  - [ ] **PREP**: Confirmar o RED das dependências, reconstruir `docs/` com `$specsfy-documentator` antes de escrever código.
  - [ ] **EXECUTE**: Criar `frontend/src/lib/tema.ts` com o tipo `PreferenciaTema`, a constante `CHAVE_TEMA` (`rag-pipeline-tema`), `normalizarPreferencia`, `resolverTema`, `aplicarTema` (classe `dark` e `color-scheme` no `html`), leitura e gravação com `try/catch` e `scriptTema()`, que monta o texto do script a partir da mesma constante e fica abaixo de 1 KB.
  - [ ] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/lib/tema.test.ts` e confirmar GREEN para AC-004, mais o regresso dos casos do script (AC-006 e AC-007) quando o `ScriptTema` existir.
  - [ ] **VISUAL**: Não aplicável: a tarefa produz lógica ou script sem superfície visual própria; o efeito visual é conferido nas tarefas de interface.
  - [ ] **EVIDENCE**: Registrar GREEN, os arquivos alterados e o tamanho em bytes do texto do script.
  - [ ] **IMPROVE**: Verificar que o texto do script e as funções puras produzem o mesmo resultado para a mesma entrada, e registrar o ajuste ou a ausência dele.
  <!-- specsfy:evidence {"task":"T018","refs":["US-001","US-002","FR-002","FR-003","FR-004","FR-005","NFR-001","NFR-004","AC-003","AC-004","AC-005","AC-006","AC-007"],"files":["frontend/src/lib/tema.ts"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/lib/tema.test.ts","exit":0}]} -->

- [ ] T019 [CODE] [US-001] Implementar o hook de tema em frontend/src/features/tema/useTema.ts — Refs: US-001, FR-002, FR-003, FR-004, NFR-003, AC-003, AC-005 — Depends: T018, T003, T005
  - [ ] **PREP**: Confirmar o RED das dependências, reconstruir `docs/` com `$specsfy-documentator` antes de escrever código.
  - [ ] **EXECUTE**: Criar `frontend/src/features/tema/useTema.ts`: devolve `preferencia` e `escolher`, inicia em `sistema` no servidor, lê o armazenamento só no cliente, aplica e grava a escolha, acompanha `prefers-color-scheme` quando a preferência é `sistema` e remove o ouvinte ao desmontar.
  - [ ] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/useTema.test.tsx` e confirmar GREEN para AC-003 e AC-005.
  - [ ] **VISUAL**: Não aplicável: a tarefa produz lógica ou script sem superfície visual própria; o efeito visual é conferido nas tarefas de interface.
  - [ ] **EVIDENCE**: Registrar GREEN, os arquivos alterados e a confirmação de que não há aviso de hidratação nem de `act` na saída.
  - [ ] **IMPROVE**: Conferir que o hook não regrava a preferência ao ler um valor inválido, e registrar o ajuste ou a ausência dele.
  <!-- specsfy:evidence {"task":"T019","refs":["US-001","FR-002","FR-003","FR-004","NFR-003","AC-003","AC-005"],"files":["frontend/src/features/tema/useTema.ts"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/features/tema/useTema.test.tsx","exit":0}]} -->

- [ ] T020 [CODE] [US-002] Implementar o script de pré-pintura em frontend/src/features/tema/ScriptTema.tsx — Refs: US-002, FR-005, NFR-001, AC-006, AC-007, AC-016 — Depends: T018, T006, T007, T016
  - [ ] **PREP**: Confirmar o RED das dependências, reconstruir `docs/` com `$specsfy-documentator` antes de escrever código.
  - [ ] **EXECUTE**: Criar `frontend/src/features/tema/ScriptTema.tsx`: renderiza o `<script>` com o texto de `scriptTema()`, usando o padrão do guia do Next 16 (tipo `text/javascript` no servidor, `text/plain` no cliente e `suppressHydrationWarning`) para não gerar aviso do React.
  - [ ] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/ScriptTema.test.tsx` e confirmar GREEN para AC-006 e AC-007.
  - [ ] **VISUAL**: Não aplicável: a tarefa produz lógica ou script sem superfície visual própria; o efeito visual é conferido nas tarefas de interface.
  - [ ] **EVIDENCE**: Registrar GREEN, os arquivos alterados e o comportamento do script com Escuro salvo, com Sistema escuro e com armazenamento bloqueado.
  - [ ] **IMPROVE**: Reler o guia local do Next 16 e conferir que o padrão aplicado é o documentado, e registrar o ajuste ou a ausência dele.
  <!-- specsfy:evidence {"task":"T020","refs":["US-002","FR-005","NFR-001","AC-006","AC-007","AC-016"],"files":["frontend/src/features/tema/ScriptTema.tsx"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/features/tema/ScriptTema.test.tsx","exit":0}]} -->

#### Fase de interface

**Objetivo**: ligar o tema ao layout raiz e à tela de erro, expor o seletor no menu da pessoa e deixar as telas atuais legíveis nos dois temas.
**Teste independente**: com o stack local aberto, escolher Escuro no menu da pessoa, recarregar `/workspaces` e `/login` e confirmar o tema escuro sem passar pelo claro.

- [ ] T021 [CODE] [US-002] Aplicar o script de tema no layout raiz e na tela de erro global em frontend/src/app/layout.tsx e frontend/src/app/global-error.tsx — Refs: US-002, FR-005, FR-006, NFR-001, NFR-004, AC-008, AC-009, AC-014, AC-016 — Depends: T020, T008, T009, T014, T016
  - [ ] **PREP**: Confirmar o RED das dependências, reconstruir `docs/` com `$specsfy-documentator` antes de escrever código, e carregar `$specsfy-specialist-react-ui-components` e `$specsfy-specialist-shadcn-ui` antes de escrever JSX ou TSX.
  - [ ] **EXECUTE**: Em `layout.tsx` e `global-error.tsx`, adicionar `suppressHydrationWarning` ao `<html>` e o `ScriptTema` dentro de `<head>`; `/login` e `/nova-senha` herdam o tema pelo layout raiz e não recebem controle.
  - [ ] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/app/layout.test.tsx src/app/telas-de-acesso.test.tsx src/app/global-error.test.tsx src/lib/api-proxy.test.ts` e confirmar GREEN para AC-008, AC-009, AC-014 e AC-016.
  - [ ] **VISUAL**: Conferir, nos temas claro e escuro, em 360 px e 1280 px, bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, percorrendo `/login` com e sem erro, `/nova-senha`, `/workspaces` e a tela de erro global, recarregando com cache desabilitado e CPU reduzida para confirmar que a página não pisca, e registrar método, viewport, estados, ajustes e resultado.
  - [ ] **EVIDENCE**: Registrar GREEN, os arquivos alterados e o resultado da conferência visual do recarregamento.
  - [ ] **IMPROVE**: Conferir que nenhum aviso de hidratação aparece no console em `next dev`, e registrar o ajuste ou a ausência dele.
  <!-- specsfy:evidence {"task":"T021","refs":["US-002","FR-005","FR-006","NFR-001","NFR-004","AC-008","AC-009","AC-014","AC-016"],"files":["frontend/src/app/layout.tsx","frontend/src/app/global-error.tsx"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/app/layout.test.tsx","exit":0}]} -->

- [ ] T022 [CODE] [US-003] Estender o menu com itens de escolha única em frontend/src/components/ui/dropdown-menu.tsx — Refs: US-003, FR-001, FR-008, NFR-003, AC-012, AC-013 — Depends: T001, T002, T012, T013
  - [ ] **PREP**: Confirmar o RED das dependências, reconstruir `docs/` com `$specsfy-documentator` antes de escrever código, e carregar `$specsfy-specialist-react-ui-components` e `$specsfy-specialist-shadcn-ui` antes de escrever JSX ou TSX.
  - [ ] **EXECUTE**: Acrescentar `DropdownMenuRadioGroup` e `DropdownMenuRadioItem` (sobre `Menu.RadioGroup`, `Menu.RadioItem` e `Menu.RadioItemIndicator` do Base UI) ao arquivo, com o mesmo espaçamento, tipografia e raio dos itens atuais, e exportá-los.
  - [ ] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/SeletorTema.a11y.test.tsx` e confirmar o papel `menuitemradio` com `aria-checked`.
  - [ ] **VISUAL**: Conferir, nos temas claro e escuro, em 360 px e 1280 px, bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, percorrendo o menu da pessoa aberto, com o item ativo, o item em foco por teclado e o item desabilitado se existir, e registrar método, viewport, estados, ajustes e resultado.
  - [ ] **EVIDENCE**: Registrar GREEN, os arquivos alterados e o resultado da conferência visual do menu.
  - [ ] **IMPROVE**: Conferir que os itens existentes (`Item`, `Label`, `Separator`) continuam idênticos, e registrar o ajuste ou a ausência dele.
  <!-- specsfy:evidence {"task":"T022","refs":["US-003","FR-001","FR-008","NFR-003","AC-012","AC-013"],"files":["frontend/src/components/ui/dropdown-menu.tsx"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/features/tema/SeletorTema.a11y.test.tsx","exit":0}]} -->

- [ ] T023 [CODE] [US-001] Criar o seletor de tema em frontend/src/features/tema/SeletorTema.tsx — Refs: US-001, FR-001, FR-002, FR-008, NFR-003, AC-001, AC-012, AC-013 — Depends: T019, T022, T001, T012, T013
  - [ ] **PREP**: Confirmar o RED das dependências, reconstruir `docs/` com `$specsfy-documentator` antes de escrever código, e carregar `$specsfy-specialist-react-ui-components` e `$specsfy-specialist-shadcn-ui` antes de escrever JSX ou TSX.
  - [ ] **EXECUTE**: Criar `frontend/src/features/tema/SeletorTema.tsx`: grupo com o rótulo "Tema" e três itens (Claro, Escuro e Sistema) de escolha única, ligado ao `useTema`, marcando a preferência ativa.
  - [ ] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/tema/SeletorTema.test.tsx src/features/tema/SeletorTema.a11y.test.tsx` e confirmar GREEN para AC-001, AC-012 e AC-013.
  - [ ] **VISUAL**: Conferir, nos temas claro e escuro, em 360 px e 1280 px, bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, percorrendo o grupo "Tema" com cada uma das três opções ativa, o foco por teclado e o menu com nome de pessoa longo, e registrar método, viewport, estados, ajustes e resultado.
  - [ ] **EVIDENCE**: Registrar GREEN, os arquivos alterados e o resultado da conferência visual do grupo.
  - [ ] **IMPROVE**: Conferir que a escolha fecha o menu e devolve o foco ao gatilho, e registrar o ajuste ou a ausência dele.
  <!-- specsfy:evidence {"task":"T023","refs":["US-001","FR-001","FR-002","FR-008","NFR-003","AC-001","AC-012","AC-013"],"files":["frontend/src/features/tema/SeletorTema.tsx"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/features/tema/SeletorTema.test.tsx","exit":0}]} -->

- [ ] T024 [CODE] [US-001] Incluir o seletor no menu da pessoa em frontend/src/features/auth/MenuPessoa.tsx — Refs: US-001, FR-001, FR-008, NFR-003, NFR-004, AC-002, AC-015 — Depends: T023, T002, T015
  - [ ] **PREP**: Confirmar o RED das dependências, reconstruir `docs/` com `$specsfy-documentator` antes de escrever código, e carregar `$specsfy-specialist-react-ui-components` e `$specsfy-specialist-shadcn-ui` antes de escrever JSX ou TSX.
  - [ ] **EXECUTE**: Em `MenuPessoa.tsx`, incluir o `SeletorTema` entre o rótulo da pessoa e "Trocar senha", com separadores, na ordem rótulo, separador, Tema, separador, Trocar senha, Sair.
  - [ ] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/features/auth/MenuPessoa.test.tsx` e confirmar GREEN para AC-002 e AC-015, sem quebrar os casos atuais do menu.
  - [ ] **VISUAL**: Conferir, nos temas claro e escuro, em 360 px e 1280 px, bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, percorrendo o menu aberto para owner, admin e member, com nome longo e papel, e o diálogo de troca de senha aberto a partir do menu, e registrar método, viewport, estados, ajustes e resultado.
  - [ ] **EVIDENCE**: Registrar GREEN, os arquivos alterados e o resultado da conferência visual do menu completo.
  - [ ] **IMPROVE**: Conferir que os itens Trocar senha e Sair continuam funcionando e na mesma posição relativa, e registrar o ajuste ou a ausência dele.
  <!-- specsfy:evidence {"task":"T024","refs":["US-001","FR-001","FR-008","NFR-003","NFR-004","AC-002","AC-015"],"files":["frontend/src/features/auth/MenuPessoa.tsx"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/features/auth/MenuPessoa.test.tsx","exit":0}]} -->

- [ ] T025 [CODE] [US-003] Reforçar o fundo de Dialog e Sheet no tema escuro em frontend/src/components/ui/dialog.tsx e frontend/src/components/ui/sheet.tsx — Refs: US-003, FR-007, NFR-002, AC-011, AC-017 — Depends: T010, T011, T017
  - [ ] **PREP**: Confirmar o RED das dependências, reconstruir `docs/` com `$specsfy-documentator` antes de escrever código, e carregar `$specsfy-specialist-react-ui-components` e `$specsfy-specialist-shadcn-ui` antes de escrever JSX ou TSX.
  - [ ] **EXECUTE**: Em `dialog.tsx` e `sheet.tsx`, manter `bg-black/10` no tema claro e acrescentar `dark:bg-black/50` ao fundo, sem alterar mais nada nos dois arquivos.
  - [ ] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/components/ui/backdrops.test.tsx src/app/cores-fixas.test.ts` e confirmar GREEN para AC-011 e AC-017.
  - [ ] **VISUAL**: Conferir, nos temas claro e escuro, em 360 px e 1280 px, bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, percorrendo um diálogo de confirmação, o painel de formulário (`Sheet`) e o painel do Assistente abertos, sobre uma lista com conteúdo, e registrar método, viewport, estados, ajustes e resultado.
  - [ ] **EVIDENCE**: Registrar GREEN, os arquivos alterados e o resultado da conferência visual dos fundos.
  - [ ] **IMPROVE**: Conferir se a separação visual entre painel e página é suficiente a 50%, e registrar o ajuste ou a ausência dele.
  <!-- specsfy:evidence {"task":"T025","refs":["US-003","FR-007","NFR-002","AC-011","AC-017"],"files":["frontend/src/components/ui/dialog.tsx","frontend/src/components/ui/sheet.tsx"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/components/ui/backdrops.test.tsx","exit":0}]} -->

- [ ] T026 [CODE] [US-003] Ajustar os tokens de cor e o color-scheme em frontend/src/app/globals.css — Refs: US-003, FR-007, NFR-002, AC-010, AC-017 — Depends: T010, T011, T017
  - [ ] **PREP**: Confirmar o RED das dependências, reconstruir `docs/` com `$specsfy-documentator` antes de escrever código, e carregar `$specsfy-specialist-react-ui-components` e `$specsfy-specialist-shadcn-ui` antes de escrever JSX ou TSX.
  - [ ] **EXECUTE**: Em `globals.css`, declarar `color-scheme` por tema (`light` em `:root` e `dark` em `.dark`) e ajustar somente os tokens do `.dark` que o teste de contraste reprovar, como `--input` e `--border`, sem trocar a paleta nem criar cor fora dos tokens.
  - [ ] **VERIFY**: Rodar `npm --prefix frontend run test:tdd -- src/app/globals.contraste.test.ts` e confirmar GREEN para AC-010, com texto em 4,5:1 e foco e borda de campo em 3:1.
  - [ ] **VISUAL**: Conferir, nos temas claro e escuro, em 360 px e 1280 px, bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, percorrendo `/login`, `/workspaces` (loading, vazio e lista), `/workspaces/[id]`, `/execucoes/[id]` (execução ativa, falha e sucesso com consulta), `/pessoas`, `/pessoas/[id]`, formulários com erro e foco, `Badge`, `Alert` e conteúdo curto e longo, e registrar método, viewport, estados, ajustes e resultado.
  - [ ] **EVIDENCE**: Registrar GREEN, os tokens alterados com os valores antes e depois, e o resultado da conferência visual de cada tela.
  - [ ] **IMPROVE**: Registrar cada tela em que um token alterado mudou a aparência do tema claro, que deve permanecer igual, e o ajuste ou a ausência dele.
  <!-- specsfy:evidence {"task":"T026","refs":["US-003","FR-007","NFR-002","AC-010","AC-017"],"files":["frontend/src/app/globals.css"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/app/globals.contraste.test.ts","exit":0}]} -->

- [ ] T027 [DOC] [US-003] Registrar os blocos de tema em INTERFACE.md — Refs: US-001, US-002, US-003, FR-001, FR-005, FR-007, FR-008, AC-002, AC-006, AC-011 — Depends: T021, T022, T023, T024, T025, T026
  - [ ] **PREP**: Reler `INTERFACE.md` e listar os blocos criados ou estendidos por T019 a T026, com arquivo, origem e consumidores reais.
  - [ ] **EXECUTE**: Acrescentar a `INTERFACE.md` as linhas de `SeletorTema`, `useTema`, `ScriptTema`, do módulo `tema` e das extensões de `DropdownMenu`, `MenuPessoa`, `Dialog`, `Sheet`, `RootLayout` e `GlobalError`, com finalidade, API, estados, acessibilidade e regra de reuso, e atualizar as linhas de tela afetadas.
  - [ ] **VERIFY**: Conferir que cada arquivo citado existe, que cada bloco listado tem consumidor e que `INTERFACE.md` não cita bloco inexistente.
  - [ ] **VISUAL**: Não aplicável: a tarefa só atualiza o mapa de interface em texto; a conferência visual foi feita nas tarefas T021 a T026.
  - [ ] **EVIDENCE**: Registrar os blocos incluídos e a saída de `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check`.
  - [ ] **IMPROVE**: Registrar a regra de reuso nova (tema só por tokens, sem cor fixa) ou declarar que `INTERFACE.md` já a cobria.

**Checkpoint**: com o stack local, escolher Claro, Escuro e Sistema no menu da pessoa, recarregar cada tela autenticada e `/login` com o cache desabilitado, e confirmar que o tema fica lembrado e nenhuma página pisca.

#### Fase final — Qualidade

- [ ] T028 [TEST] Executar a regressão do frontend e a revisão visual final com frontend/package.json — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017 — Depends: T021, T024, T025, T026, T027
  - [ ] **PREP**: Identificar os checks do frontend (`lint`, `typecheck`, `test:tdd`, `build`) e confirmar que o diff não toca `package.json`, `package-lock.json`, `next.config.ts`, `src/` do backend nem o banco.
  - [ ] **EXECUTE**: Rodar `npm --prefix frontend run lint`, `npm --prefix frontend run typecheck`, `npm --prefix frontend run test:tdd` e `npm --prefix frontend run build`, e `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs` sobre a spec.
  - [ ] **VERIFY**: Confirmar zero falhas nos quatro checks e nenhuma lacuna na rastreabilidade de US, FR, NFR e AC.
  - [ ] **VISUAL**: Repassar nos dois temas, em 360 px e 1280 px, bordas, espaçamentos, margens, padding e tipografia de todas as telas e estados listados na seção 10, com cache desabilitado e CPU reduzida no recarregamento, e registrar método, achados e resultado.
  - [ ] **EVIDENCE**: Registrar contagens de testes, comandos, resultado da rastreabilidade, a revisão de `PROJECT.md` (sem impacto material, com justificativa) e a reconstrução final de `docs/` por `$specsfy-documentator`.
  - [ ] **IMPROVE**: Registrar a retrospectiva do processo, incluindo qualquer ajuste de token feito na revisão visual.

### 15. Ordem de execução

- Caminho crítico: T001 a T017 (RED) → T018 → T019 e T020 → T021 → T022 → T023 → T024 → T027 → T028.
- Tarefas paralelas: as tarefas de RED marcadas `[P]` usam arquivos de teste distintos e não compartilham estado; os casos que dividem o mesmo arquivo (AC-001 e AC-012, AC-002 e AC-015, AC-003 e AC-005, AC-006 e AC-007) não são paralelos. T025 e T026 não dependem do seletor e podem ocorrer em paralelo com T022 a T024, mas ficam sem `[P]` porque alteram a aparência das mesmas telas e a revisão visual deve ser sequencial.
- Estratégia de MVP: T001 a T017, depois T018 a T024 entregam US-001 e US-002 (tema escolhido, lembrado e sem piscar); T025 e T026 entregam US-003; T027 e T028 fecham registro e qualidade.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Nenhuma dependência externa nova. Depende do `frontend/` existente, de `globals.css` com os tokens `.dark` e do `DropdownMenu` do Base UI.
- Para a revisão visual, depende de um ambiente que sirva o frontend (stack local no Swarm com túnel de porta, ou `next dev`).

#### Riscos

- Componente com cor fixa ou token insuficiente fica ilegível no tema escuro → varredura de cores fixas, teste de contraste e revisão visual das telas.
- O teste de contraste pode falhar para algum token do `.dark` (por exemplo, a borda de campo com transparência) → ajustar o token em `globals.css` dentro desta entrega, com registro na tarefa.
- `suppressHydrationWarning` no `html` pode esconder uma divergência legítima → limitar a supressão ao elemento `html` e cobrir a classe com teste.
- O script em linha depende de a CSP continuar permitindo `'unsafe-inline'` em `script-src` → o teste da CSP (AC-014) falha se isso mudar, e a mudança deve reabrir esta spec.
- Quem compartilha o navegador compartilha a preferência → aceito, por decisão de guardar só no navegador; a preferência por conta fica como evolução futura.
- A primeira pintura do `global-error` depende do mesmo script → coberto por AC-009.

#### Suposições

- A preferência é por navegador e não por pessoa; sair da conta não a apaga.
- Sistema é o padrão inicial.
- A rota `/`, hoje a página-modelo do Next.js, fica fora desta entrega.
- Não há runner E2E; a revisão visual é manual e registrada em cada tarefa.
- O número 0024 foi usado porque a SPEC-0023 já existe na branch remota `spec/0023-fase-1-recebimento-e-processamento-de-documentos-ate-markdown`, ainda não integrada à `main`.

### 17. Decisões

- **DEC-001**: Implementar o tema com código próprio, sem biblioteca de tema — o guia oficial do Next 16 descreve a técnica (script em linha no `head` e `suppressHydrationWarning`), a CSP atual a permite e a lógica é pequena e testável; evita uma dependência nova (NFR-004). Alternativa: `next-themes`, mais rápida, mas adiciona dependência e comportamento externo. Trade-off: manter e testar o código próprio.
- **DEC-002**: Aplicar o tema pela classe `dark` no `html`, e não por `data-theme` — o `globals.css` já define `@custom-variant dark (&:is(.dark *))` e o bloco `.dark`, então nenhum token precisa mudar de seletor.
- **DEC-003**: Oferecer o controle como itens de escolha única dentro do `DropdownMenu` existente, e não como botão alternador de dois estados — são três opções, o estado ativo precisa ser anunciado e o menu da pessoa já é o lugar de preferências da conta.
- **DEC-004**: Guardar a preferência em `localStorage` na chave `rag-pipeline-tema`, com os valores `claro`, `escuro` e `sistema` — escolha confirmada de guardar só no navegador; o valor ausente equivale a `sistema` e `sistema` é gravado de forma explícita quando escolhido.
- **DEC-005**: Provar o contraste por teste que calcula a razão a partir dos tokens de `globals.css`, somado à revisão visual — o jsdom não renderiza o CSS final, e o cálculo sobre os tokens é determinístico e barato.
- **DEC-007**: Manter a CSP atual (`script-src 'self' 'unsafe-inline'`) e usar um script em linha constante para o tema — migrar a CSP para nonce ou hash é uma mudança de segurança própria, fora de escopo; o script não recebe entrada de pessoa nem de rede, e o teste de AC-014 detecta se a CSP deixar de permitir o script em linha.
- **DEC-006**: Numerar esta spec como 0024 — a SPEC-0023 já existe na branch remota `spec/0023-fase-1-recebimento-e-processamento-de-documentos-ate-markdown`; reaproveitar o 0023 geraria duas specs com o mesmo ID quando aquela branch for integrada.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Cada cenário `AC` aplicável passa.
- [ ] Cada requisito possui evidência de verificação.
- [ ] Cada tarefa na seção 14 está concluída.
- [ ] Testes e checks estáticos disponíveis passam.
- [ ] `INTERFACE.md` registra cada bloco criado ou estendido, com origem, consumidores e regra de reuso.
- [ ] `PROJECT.md` foi revisado; sem impacto material, a justificativa está na evidência da tarefa.
- [ ] `.specsfy/STACK.md` permanece válido, porque não há tecnologia estrutural nova, e `.specsfy/DATABASE.md` não muda, porque não há persistência no servidor.
- [ ] `$specsfy-documentator` reconstruiu `docs/` e `.specsfy/PACKAGES.md` depois da última tarefa de implementação.
