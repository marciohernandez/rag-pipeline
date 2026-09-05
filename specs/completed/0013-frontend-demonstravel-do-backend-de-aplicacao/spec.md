# Especificação integrada: Frontend demonstrável do backend de aplicação

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0013 |
| Slug | 0013-frontend-demonstravel-do-backend-de-aplicacao |
| Status | Complete |
| Effort | 7 |
| Effort updated at | 2026-09-05 |
| Effort rationale | Introduz uma stack nova neste repositório (Next.js/React/TypeScript/Tailwind), quatro telas com estados assíncronos, dois endpoints novos de leitura no backend e uma sessão de autenticação por token no cliente; perfil `high`. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-09-05 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O pipeline (fatia 1, SPEC-0001–0007) e o backend de aplicação (fatia 2,
SPEC-0012) estão completos e testados, mas só são operáveis por CLI ou
chamada HTTP direta. Não existe interface para pessoas neste repositório
(`docs/frontend.md`: "0 superfícies observadas"). Marcio não consegue
demonstrar a fatia funcional à sua equipe de consultoria sem pedir que
alguém leia respostas JSON.

#### Resultado desejado

Marcio abre um frontend neste mesmo repositório, entra com um token de
demonstração, envia ou escolhe uma base Markdown, acompanha o processamento
assíncrono até o fim, consulta a base indexada e vê o resultado com os
chunks-fontes que o sustentam — uma jornada apresentável de ponta a ponta.

#### Métricas de sucesso

- A jornada completa (login → enviar/escolher base → acompanhar execução →
  consultar → ver chunks-fontes) é executável sem tocar terminal, CLI ou
  chamada HTTP manual.
- Nenhuma chamada do frontend acessa o banco vetorial, o PostgreSQL ou o
  `src/pipeline/` diretamente; toda operação passa pelo backend FastAPI de
  `src/app/`.
- As quatro telas cobrem os estados obrigatórios (loading, vazio,
  processando, sucesso, falha, sem permissão) sem tela em branco ou exceção
  não tratada.

### 2. Research e esclarecimentos

#### Researchs executados

- Nenhuma pesquisa externa com claim material que exigisse verificação.
  A investigação desta spec foi sobre o código já existente no próprio
  repositório (ver "Fontes e contexto consultados").

#### Fontes e contexto consultados

- `specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md`
  (refinado em 2026-09-05): brief pronto para especificar da fatia 3, com as
  decisões de Login, sessionStorage e escopo dos dois novos endpoints de
  leitura.
- `src/app/routers/bases.py`, `executions.py`, `queries.py`, `repo.py`,
  `auth.py`, `models.py`, `main.py`: API real implementada pela SPEC-0012.
  Confirmado por leitura direta: não existe `GET /api/v1/bases` nem
  `GET /api/v1/bases/{id}`; só operações pontuais por ID e o token de
  demonstração `token-demo-owner` já está registrado em `main.py`.
- `src/app/storage.py`: o protocolo `Storage` não expõe listagem de arquivos
  por base, o que motivou a decisão de contar documentos na escrita
  (DEC-002) em vez de listar o storage na leitura.
- `docs/application.md`, `docs/frontend.md`: confirmam a superfície HTTP
  atual e a ausência de qualquer frontend hoje.
- `INTERFACE.md`, `DESIGNSYSTEM.MD`: convenções de `PageHeader`, `DataGrid`
  em largura total, `Breadcrumb`, formulário em duas colunas e estados
  obrigatórios já registradas para este produto, ainda sem tela real que as
  use.
- `.specsfy/STACK.md`: confirma Next.js, shadcn/ui e Tailwind como "direção
  futura" até esta spec; React 19/Tailwind v4/shadcn/ui confirmados como
  convenção padrão pelo `specsfy-specialist-reui` instalado nesta sessão.

#### Documentação consultada

- Nenhuma documentação externa via rede nesta sessão. As convenções de
  Next.js App Router, React, TypeScript, Tailwind CSS, shadcn/ui e ReUI vêm
  dos especialistas instalados (`specsfy-specialist-nextjs`, `-react`,
  `-react-ui-components`, `-typescript`, `-tailwind-css`, `-reui`,
  `-shadcn-ui`) e devem ser consultados de novo durante a implementação de
  cada tarefa que os use.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: A ausência de endpoints de listagem na SPEC-0012 vira uma fatia
  técnica prévia ou entra no escopo desta fatia? → **A**: Entra no escopo
  desta spec (decisão do refinamento do backlog, 2026-09-05): são dois `GET`
  de baixo risco e o formato que a UI precisa só fica claro desenhando a
  tela junto.
- **Q**: O frontend abre sem tela de login (token fixo por ambiente) ou tem
  uma tela de Login? → **A**: Tem tela de Login com campo de texto livre
  para colar o token — permite trocar de papel (owner/admin/member/outro
  tenant) ao vivo durante a apresentação.
- **Q**: Onde o token fica guardado no navegador? → **A**: `sessionStorage`,
  nunca `localStorage` ou cookie persistente — coerente com não ser
  credencial de produção.
- **Q**: Runner de testes TDD do novo frontend Node? → **A**: Vitest,
  confirmado com o usuário em 2026-09-05 (recomendação do framework para
  stacks Node).
- **Q**: Instalar os especialistas de Next.js/React/TypeScript/Tailwind
  ainda ausentes no projeto? → **A**: Sim, autorizado e instalado em
  2026-09-05.

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Tela de Login por token colado, com sessão em `sessionStorage`.
- Dois novos endpoints de leitura no backend: listagem de bases do
  tenant/projeto ativo e detalhe de uma base com seu histórico de execuções.
- Tela Projeto: listagem de bases (`DataGrid`), upload de múltiplos `.md` ou
  uso da base preparada.
- Tela Detalhe da execução: progresso, etapas, contagens, erro seguro,
  repetição (quando `failed`) e formulário de consulta com chunks-fontes.
- Ação de apagar uma base, restrita a `owner`/`admin`, com confirmação da
  consequência.
- Estados obrigatórios (loading, vazio, processando, sucesso, falha, sem
  permissão) nas quatro telas.

#### Fora de escopo

- Qualquer mudança em `src/pipeline/` ou nos endpoints já entregues pela
  SPEC-0012 além dos dois novos de leitura descritos acima.
- Cadastro, convite, login real ou administração completa de usuários e
  papéis.
- Seletor de papéis pré-definidos na tela de Login (decisão do backlog:
  campo de texto livre, sem acoplar o frontend à lista fixa de tokens de
  `main.py`).
- Ingestão de PDF, DOCX ou outros formatos; curadoria cruzada; detecção de
  contradições.
- Deploy, hospedagem ou pipeline de CI/CD específico do frontend.

#### Atores

- **Marcio / owner**: acessa com o token `token-demo-owner`; envia bases,
  inicia e repete execuções, consulta, apaga bases.
- **admin**: mesmas permissões de escrita que `owner` nesta fatia (upload,
  execução, repetição, exclusão), sem administração de usuários.
- **member**: acompanha bases, execuções e consultas; não envia, não repete
  e não apaga (o backend já recusa essas ações com 403 via
  `require_write_role`).

### 4. Princípios e restrições do projeto

- **PR-001**: o frontend nunca acessa PostgreSQL, o banco vetorial ou
  `src/pipeline/` diretamente; toda operação passa pelo backend FastAPI de
  `src/app/` (regra já registrada em `.specsfy/RULES.md` para a fronteira
  `src/app/` ↔ `src/pipeline/`, estendida aqui ao cliente HTTP).
  Verificado por `tests/test_application_boundaries.py` no lado backend; no
  lado frontend, por revisão de que cada dado vem do cliente HTTP gerado a
  partir de `src/app/`.
- **PR-002**: o token de demonstração nunca é persistido em `localStorage`
  nem em cookie; fica só em `sessionStorage` e é limpo em qualquer 401.
- **PR-003**: o frontend é um projeto Node autocontido em `frontend/` (novo
  diretório na raiz), com seu próprio `package.json`, sem misturar
  dependências Python e Node em um único manifesto (DEC-001).
- **PR-004**: toda tela usa `PageHeader` compartilhado, `Breadcrumb` com
  equipe/projeto/tela atual e o `DataGrid` em largura total com coluna `ID`
  visível, conforme `DESIGNSYSTEM.MD` e `INTERFACE.md`.

### 5. Histórias de usuário

#### US-001 — Entrar com um token de demonstração (P1)

Como Marcio (ou qualquer papel de demonstração), quero colar um token na
tela de Login, para acessar o frontend com as permissões desse papel sem uma
tela de administração de usuários.

**Por que P1**: sem sessão autenticada nenhuma outra tela é alcançável.
**Teste independente**: colar um token válido e ver a tela Projeto; colar um
inválido e ver o erro sem sair do Login.
**Requisitos**: FR-001

#### US-002 — Ver e enviar bases do projeto ativo (P1)

Como Marcio, quero ver as bases do meu tenant/projeto e enviar uma nova (por
upload ou base preparada), para começar uma demonstração sem preparar nada
por CLI.

**Por que P1**: é o ponto de entrada de qualquer demonstração; sem
listagem, não há como escolher o que mostrar.
**Teste independente**: abrir a tela Projeto com bases existentes e ver a
listagem; enviar uma base nova e vê-la aparecer.
**Requisitos**: FR-002, FR-003, FR-004

#### US-003 — Acompanhar, repetir e apagar uma execução (P1)

Como Marcio ou admin, quero acompanhar o progresso de uma execução, repetir
se ela falhar e apagar a base quando não precisar mais dela, para conduzir a
demonstração até o fim mesmo que algo falhe.

**Por que P1**: a demonstração é assíncrona; sem acompanhamento e
repetição, uma falha de rede ou de provider interrompe a apresentação.
**Teste independente**: iniciar uma execução e ver as contagens mudarem até
`succeeded`; forçar uma falha e repetir; apagar a base ao final.
**Requisitos**: FR-005, FR-006, FR-007

#### US-004 — Consultar a base indexada e ver os chunks-fontes (P1)

Como Marcio, quero fazer uma pergunta sobre a base indexada e ver a
resposta com os trechos-fontes recuperados, para provar à equipe que a
recuperação funciona e é rastreável.

**Por que P1**: é o resultado observável do pipeline inteiro; sem isso a
demonstração não prova valor.
**Teste independente**: consultar uma base com execução `succeeded` e ver
resultado + chunks-fontes; falhar a consulta e ver a pergunta preservada.
**Requisitos**: FR-008

### 6. Cenários BDD de aceite

#### AC-001 — Entrar com um token de demonstração válido

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-001
Feature: Autenticação por token de demonstração

  Scenario: Entrar com token válido
    Given Marcio tem o token estático de demonstração "token-demo-owner"
    When ele cola o token na tela de Login e confirma
    Then o frontend guarda o token em sessionStorage
    And ele é levado à tela Projeto autenticado com o papel "owner"
```

#### AC-002 — Rejeitar um token inválido no Login

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-002
Feature: Autenticação por token de demonstração

  Scenario: Rejeitar token inválido
    Given um token vazio, malformado ou não reconhecido pelo backend
    When Marcio tenta entrar com esse token
    Then o frontend mostra um erro genérico, sem detalhe do backend
    And mantém o campo preenchido para correção
    And nenhum token é guardado em sessionStorage
```

#### AC-003 — Encerrar a sessão ao sair ou ao receber 401

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-003
Feature: Autenticação por token de demonstração

  Scenario: Sair ou perder a sessão
    Given Marcio está autenticado com um papel de demonstração
    When ele aciona "Sair", ou qualquer chamada ao backend recebe 401
    Then o token guardado em sessionStorage é removido
    And ele retorna à tela de Login
    And pode entrar com um token de outro papel sem recarregar a aplicação
```

#### AC-004 — Listar bases do tenant/projeto ativo

**Cobre**: US-002, FR-002, NFR-001

```gherkin
@US-002 @FR-002 @NFR-001 @AC-004
Feature: Listagem de bases

  Scenario: Listar bases mais recentes primeiro
    Given o tenant e projeto ativo têm bases criadas por upload e por base preparada
    When Marcio abre a tela Projeto
    Then a listagem mostra origem, status, documentos, chunks e última atualização de cada base
    And a base mais recentemente atualizada aparece primeiro
```

#### AC-005 — Ver o detalhe de uma base com seu histórico de execuções

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-005
Feature: Detalhe de uma base

  Scenario: Abrir o detalhe de uma base com execuções anteriores
    Given uma base do projeto ativo já foi processada mais de uma vez
    When Marcio abre a linha dessa base na listagem
    Then ele vê o histórico de execuções, da mais recente para a mais antiga
    And pode abrir o detalhe de qualquer execução do histórico
```

#### AC-006 — Enviar múltiplos arquivos ou usar a base preparada

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-006
Feature: Envio de base

  Scenario: Enviar vários arquivos Markdown
    Given Marcio está no contexto do projeto ativo
    When ele envia vários arquivos .md válidos pela tela Projeto
    Then uma nova base aparece na listagem com origem "upload"
    And ele também pode optar pela base preparada como contingência, identificada com origem "preparada"
```

#### AC-007 — Rejeitar um envio fora dos limites

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-007
Feature: Envio de base

  Scenario: Rejeitar envio inválido antes de agendar
    Given um envio com mais de 50 arquivos, um arquivo maior que 5 MB, mais de 50 MB no total, extensão diferente de .md ou conteúdo não UTF-8
    When Marcio tenta enviar
    Then o frontend identifica cada problema antes de chamar o backend
    And preserva os arquivos válidos para correção do envio
    And nenhuma base parcial é criada
```

#### AC-008 — Acompanhar uma execução assíncrona até a conclusão

**Cobre**: US-003, FR-005, FR-003

```gherkin
@US-003 @FR-005 @FR-003 @AC-008
Feature: Acompanhamento de execução

  Scenario: Acompanhar progresso até sucesso
    Given uma execução foi agendada para uma base
    When Marcio abre o detalhe dessa execução
    Then ele vê etapa, status e as contagens previstos/inseridos/mantidos/removidos evoluindo até "succeeded"
    And nenhuma chamada acessa o banco vetorial diretamente pelo navegador
```

#### AC-009 — Repetir uma execução que falhou

**Cobre**: US-003, FR-006, FR-005

```gherkin
@US-003 @FR-006 @FR-005 @AC-009
Feature: Repetição de execução

  Scenario: Repetir após falha
    Given uma execução em situação "failed", com etapa e erro seguro visíveis
    When owner ou admin aciona "Repetir"
    Then uma nova execução é agendada para a mesma base
    And a nova tentativa não cria pontos duplicados no banco vetorial
```

#### AC-010 — Rejeitar repetição com execução ativa

**Cobre**: US-003, FR-006

```gherkin
@US-003 @FR-006 @AC-010
Feature: Repetição de execução

  Scenario: Recusar repetição concorrente
    Given uma base já tem uma execução "pending" ou "running"
    When owner ou admin tenta repetir ou iniciar outra execução para essa base
    Then o frontend mostra que já existe uma execução ativa
    And nenhuma execução nova é agendada
```

#### AC-011 — Apagar uma base com confirmação

**Cobre**: US-003, FR-007

```gherkin
@US-003 @FR-007 @AC-011
Feature: Exclusão de base

  Scenario: Apagar com confirmação e permissão
    Given owner ou admin está no detalhe de uma base
    When aciona "Apagar" e confirma a consequência
    Then a base, suas execuções, consultas e vetores associados são removidos
    And a listagem deixa de mostrar essa base
```

#### AC-019 — Recusar oferecer exclusão a member

**Cobre**: US-003, FR-007

```gherkin
@US-003 @FR-007 @AC-019
Feature: Exclusão de base

  Scenario: Recusar exclusão sem permissão
    Given member está no detalhe de uma base
    Then a ação de apagar não é oferecida na interface
    And uma chamada direta de member ao DELETE é recusada com 403 pelo backend
```

#### AC-020 — Execuções e consultas somem após apagar a base

**Cobre**: US-003, FR-007

```gherkin
@US-003 @FR-007 @AC-020
Feature: Exclusão de base

  Scenario: Consequência completa da exclusão
    Given uma base tem execuções e consultas registradas
    When owner ou admin apaga essa base
    Then abrir a base apagada pelo id retorna "não encontrada"
    And nenhuma execução ou consulta dessa base aparece em outra tela
```

#### AC-021 — Não oferecer repetir para uma execução que não falhou

**Cobre**: US-003, FR-006

```gherkin
@US-003 @FR-006 @AC-021
Feature: Repetição de execução

  Scenario: Repetir só está disponível para execução failed
    Given uma execução em situação "succeeded", "pending" ou "running"
    Then a ação de repetir não é oferecida na interface para essa execução
```

#### AC-012 — Consultar a base indexada e ver os chunks-fontes

**Cobre**: US-004, FR-008

```gherkin
@US-004 @FR-008 @AC-012
Feature: Consulta à base indexada

  Scenario: Consultar com sucesso
    Given uma base com uma execução "succeeded"
    When Marcio envia uma pergunta no formulário de consulta
    Then ele vê o resultado e os chunks-fontes, cada um identificado pelo documento de origem
```

#### AC-013 — Preservar a pergunta após falha na consulta

**Cobre**: US-004, FR-008

```gherkin
@US-004 @FR-008 @AC-013
Feature: Consulta à base indexada

  Scenario: Falha ao consultar
    Given o provider de embeddings ou o banco vetorial está indisponível
    When Marcio envia uma pergunta
    Then o frontend mostra uma falha segura, sem detalhe do provedor (NFR-002 do backend, SPEC-0012)
    And preserva a pergunta digitada para nova tentativa
```

#### AC-014 — Isolamento entre tenants na listagem e no detalhe

**Cobre**: US-002, FR-002, FR-003, NFR-001

```gherkin
@US-002 @FR-002 @FR-003 @NFR-001 @AC-014
Feature: Isolamento por tenant e projeto

  Scenario: Não ver bases de outro tenant
    Given existem bases do tenant-1/projeto-1 e do tenant-2/projeto-2
    When alguém autenticado com um token do tenant-1 abre a tela Projeto
    Then só aparecem as bases do tenant-1/projeto-1
    And tentar abrir o detalhe de uma base do tenant-2 pelo id retorna "não encontrada"
```

#### AC-015 — Isolamento entre tenants na consulta

**Cobre**: US-004, FR-008, NFR-001

```gherkin
@US-004 @FR-008 @NFR-001 @AC-015
Feature: Isolamento por tenant e projeto

  Scenario: Não consultar base de outro tenant
    Given uma base pertence ao tenant-2/projeto-2
    When alguém autenticado com um token do tenant-1 tenta consultar essa base pelo id
    Then o backend responde "base não encontrada"
    And nenhuma consulta é registrada
```

#### AC-016 — Operar a tela de Login só por teclado

**Cobre**: US-001, NFR-003

```gherkin
@US-001 @NFR-003 @AC-016
Feature: Acessibilidade

  Scenario: Login por teclado
    Given Marcio usa apenas o teclado
    When ele tabula até o campo de token, digita e confirma com Enter
    Then o foco segue uma ordem coerente e o botão de confirmar é alcançável
    And o resultado (sucesso ou erro) é anunciado por tecnologia assistiva
```

#### AC-017 — Operar a tela Projeto só por teclado

**Cobre**: US-002, FR-002, FR-004, NFR-003

```gherkin
@US-002 @FR-002 @FR-004 @NFR-003 @AC-017
Feature: Acessibilidade

  Scenario: Projeto por teclado
    Given Marcio usa apenas o teclado
    When ele tabula pela listagem, abre o upload e envia uma base
    Then cada linha do DataGrid abre o detalhe por Enter, sem depender do mouse
    And o foco retorna a um ponto previsível após fechar o Sheet/Dialog de upload
```

#### AC-018 — Operar a tela Detalhe/consulta só por teclado

**Cobre**: US-003, US-004, FR-005, FR-008, NFR-003

```gherkin
@US-003 @US-004 @FR-005 @FR-008 @NFR-003 @AC-018
Feature: Acessibilidade

  Scenario: Detalhe e consulta por teclado
    Given Marcio usa apenas o teclado
    When ele tabula até o formulário de consulta, envia uma pergunta e recebe o resultado
    Then o rótulo do campo, o estado de carregamento e o resultado são associados e anunciados
    And os chunks-fontes não são comunicados só por cor
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O frontend deve gerenciar a sessão do token de demonstração:
  aceitar o token colado na tela de Login, validá-lo contra o backend,
  guardá-lo em `sessionStorage` quando válido, anexá-lo como
  `Authorization: Bearer <token>` em toda chamada subsequente, e limpá-lo
  (retornando ao Login) tanto em uma ação explícita de sair quanto em
  qualquer resposta 401.
- **FR-002**: O sistema deve expor `GET /api/v1/bases`, retornando as bases
  do tenant/projeto do token autenticado (nunca de outro tenant/projeto),
  cada uma com origem, status derivado da execução mais recente, contagem
  de documentos, contagem de chunks e data da última atualização, ordenadas
  da mais recentemente atualizada para a mais antiga.
- **FR-003**: O sistema deve expor `GET /api/v1/bases/{id}`, retornando uma
  base do tenant/projeto do token autenticado com seu histórico completo de
  execuções (da mais recente para a mais antiga), e recusando com 404
  quando a base não existir ou pertencer a outro tenant/projeto.
- **FR-004**: O frontend deve permitir enviar vários arquivos `.md` ou usar
  a base preparada como contingência, validando extensão, codificação UTF-8
  e os limites de 50 arquivos / 5 MB por arquivo / 50 MB no total antes de
  chamar o backend, preservando os arquivos válidos quando o envio for
  rejeitado.
- **FR-005**: O frontend deve exibir o progresso de uma execução (etapa,
  situação e contagens previstos/inseridos/mantidos/removidos), atualizando
  até que a situação deixe de ser `pending`/`running`.
- **FR-006**: O frontend deve oferecer repetir uma execução em situação
  `failed` a `owner`/`admin`, e recusar (sem chamar o backend de agendamento)
  quando já existir uma execução ativa para a base.
- **FR-007**: O frontend deve oferecer apagar uma base a `owner`/`admin`
  mediante confirmação explícita da consequência, e não oferecer essa ação a
  `member`.
- **FR-008**: O frontend deve oferecer um formulário de consulta sobre uma
  base com execução `succeeded`, exibindo o resultado com os chunks-fontes
  (documento de origem e trecho) e preservando a pergunta digitada quando a
  consulta falhar.

#### Não funcionais

- **NFR-001**: Isolamento por tenant/projeto — nenhuma chamada do frontend
  expõe ou aceita dado de um tenant/projeto diferente do token autenticado.
  **Verificação**: AC-014, AC-015 (dois tokens de tenants diferentes contra a
  mesma base).
- **NFR-002**: Segurança da sessão — o token nunca é persistido em
  `localStorage` ou cookie, e é limpo de `sessionStorage` em qualquer 401.
  **Verificação**: AC-001, AC-002, AC-003 (inspeção de storage no teste de
  integração do cliente HTTP).
- **NFR-003**: Acessibilidade por teclado e tecnologia assistiva nas quatro
  telas (Login, Projeto, Detalhe, consulta). **Verificação**: AC-016,
  AC-017, AC-018 (teste automatizado de foco/ordem de tabulação e checagem
  de atributos ARIA/rótulos).

#### Erros e casos-limite

- Token ausente, vazio ou não reconhecido → 401 com mensagem genérica,
  campo preservado, nenhuma persistência em `sessionStorage` (AC-002).
- Qualquer chamada autenticada recebendo 401 → sessão limpa e redirecionamento
  ao Login (AC-003).
- Base ou execução de outro tenant/projeto → 404 "não encontrada", nunca um
  vazamento de existência (AC-014, AC-015).
- Envio fora dos limites (arquivos, tamanho, extensão, codificação) →
  rejeitado antes de chamar o backend, sem processamento parcial (AC-007).
- Execução ativa já em curso para a base → nova execução ou repetição
  recusada (AC-010), refletindo o 409 já implementado no backend
  (SPEC-0012).
- Consulta sem execução `succeeded` → backend já responde 409 (SPEC-0012);
  o frontend explica a causa em vez de mostrar um erro genérico.
- Provider de embeddings/banco vetorial indisponível durante a consulta →
  falha segura sem detalhe do provedor, pergunta preservada (AC-013).
- `member` tentando uma ação de escrita → a ação não é oferecida na
  interface, e o backend já recusa com 403 (`require_write_role`) caso
  chamada diretamente.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

Backend FastAPI já completo em `src/app/` (SPEC-0012, `Complete`):
`routers/bases.py`, `executions.py`, `queries.py` expõem operações pontuais
por ID; `repo.py` centraliza leituras isoladas por tenant/projeto;
`auth.py` resolve identidade por token estático (`Bearer <token>`) e recusa
escrita fora de `owner`/`admin`; `models.py` define `Base`, `Execution`,
`Query` sobre PostgreSQL/SQLAlchemy. Nenhum frontend existe hoje
(`docs/frontend.md`). `.specsfy/STACK.md` já indica Next.js, shadcn/ui e
Tailwind como direção — esta spec é a primeira a implementá-los.

#### Arquitetura e módulos

- **DEC-001** (ver seção 17): novo diretório `frontend/` na raiz do
  repositório, projeto Next.js App Router autocontido (`package.json`,
  `tsconfig.json`, `tailwind.config` próprios), sem misturar tooling Python
  e Node em um manifesto único.
- Backend (`src/app/`): dois novos endpoints em `routers/bases.py` e duas
  novas funções de leitura em `repo.py` (ver Controllers/Queries abaixo).
  Nenhuma mudança em `src/pipeline/` nem nos endpoints já entregues pela
  SPEC-0012.
- Frontend (`frontend/src/`):
  - `lib/api-client.ts`: cliente HTTP único, injeta `Authorization` a partir
    da sessão, trata 401 centralizadamente (limpa sessão, redireciona).
  - `lib/session.ts`: leitura/escrita do token em `sessionStorage`.
  - `app/login/page.tsx`: tela de Login.
  - `app/(autenticado)/projeto/page.tsx`: tela Projeto (listagem + upload).
  - `app/(autenticado)/execucoes/[id]/page.tsx`: tela Detalhe da execução
    (progresso, repetição, consulta).
  - `features/bases/`: `DataGridBases.tsx`, `UploadBaseSheet.tsx`,
    componentes de domínio da tela Projeto.
  - `features/execucoes/`: `PainelProgresso.tsx`, `FormularioConsulta.tsx`,
    `ChunksFontes.tsx`, componentes de domínio da tela Detalhe.
  - TanStack Query para busca/cache das chamadas ao backend (listagem,
    detalhe, polling de execução ativa).

#### Migrations

- **[MIGRATION]** Adicionar coluna `documentos` (Integer, not null, default
  0) à tabela `bases`, preenchida na criação com a contagem de arquivos
  recebidos (upload ou base preparada). Necessária porque `Storage` (ver
  `src/app/storage.py`) não expõe listagem de arquivos por base, e contar
  na escrita evita uma chamada extra de listagem ao storage em toda leitura
  (DEC-002). Nova revisão Alembic em `alembic/versions/`, aplicada e
  conferida no banco de teste antes do Delivery Gate, conforme a regra de
  `AGENTS.md`. Rollback (`downgrade`): remove a coluna `documentos`;
  compatível porque nenhuma consulta fora dos dois endpoints novos desta
  spec depende dela.

#### Models

- `src/app/models.py::Base`: adicionar `documentos: Mapped[int]` (default
  `0`). Nenhuma outra mudança de schema; `chunks` e `status` da listagem são
  computados a partir de `Execution`, sem nova coluna.

#### Controllers e casos de uso

- `src/app/routers/bases.py::listar_bases` — `GET /api/v1/bases`: usa
  `repo.list_bases_for_identity`, monta `status`/`chunks`/`ultima_atualizacao`
  a partir da execução mais recente de cada base, ordena por atualização
  desc. Nenhuma restrição de papel (leitura permitida a `member`).
- `src/app/routers/bases.py::obter_base` — `GET /api/v1/bases/{base_id}`:
  usa `repo.get_base_or_404` (já existe) e
  `repo.list_executions_for_base` para o histórico; mesma regra de leitura.

#### Views e experiência

- Ver seção 10 (Interfaces e contratos) para telas, estados e componentes.

#### Queries e repositórios

- `src/app/repo.py::list_bases_for_identity(session, identity)`: `SELECT`
  em `Base` filtrado por `tenant_id`/`project_id`/`apagada_em IS NULL`, com
  subquery/`JOIN` na última `Execution` por `base_id` (maior `iniciado_em`)
  para status e contagens; ordenado por essa data desc, com `criado_em`
  como desempate para bases sem execução.
- `src/app/repo.py::list_executions_for_base(session, base_id)`: `SELECT`
  em `Execution` filtrado por `base_id`, ordenado por `iniciado_em` desc.
  Reaproveita `get_base_or_404` para a checagem de tenant/projeto antes de
  chamar esta função.

#### Jobs e processamento assíncrono

- Não aplicável a esta spec: a tarefa Procrastinate (`src/app/tasks.py`) já
  existe e não muda; o frontend só consome seu estado via
  `GET /api/v1/executions/{id}` (já implementado) e faz polling client-side
  enquanto a situação for `pending`/`running`.

#### Estrutura de arquivos

```text
specs/draft/0013-frontend-demonstravel-do-backend-de-aplicacao/
  spec.md
  research/
src/app/
  routers/bases.py        # + listar_bases, obter_base
  repo.py                 # + list_bases_for_identity, list_executions_for_base
  models.py               # + Base.documentos
alembic/versions/
  <novo>_add_documentos_to_bases.py
frontend/
  package.json
  tsconfig.json
  src/
    app/
      login/page.tsx
      (autenticado)/projeto/page.tsx
      (autenticado)/execucoes/[id]/page.tsx
    lib/
      api-client.ts
      session.ts
    features/
      bases/DataGridBases.tsx
      bases/UploadBaseSheet.tsx
      execucoes/PainelProgresso.tsx
      execucoes/FormularioConsulta.tsx
      execucoes/ChunksFontes.tsx
tests/
  test_app_bases.py        # + casos de listar_bases/obter_base
frontend/src/**/*.test.tsx # + casos Vitest do frontend
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `Base` (existente + campo novo) | `id` (UUID) | + `documentos: int` (contagem de arquivos recebidos na criação, `default 0`) | 1 `Base` → N `Execution`, N `Query` |
| `Execution` (sem mudança) | `id` (UUID) | `situacao`, `etapa`, contagens, `erro`, `iniciado_em`, `concluido_em` | N `Execution` → 1 `Base` |

#### Estados e transições

Sem mudança nas transições já definidas pela SPEC-0012
(`pending → running → succeeded|failed`, `failed → pending` via repetição).
Esta spec só lê esse estado; não introduz transição nova.

#### Migração e retenção

- A coluna `documentos` nasce com `default 0`; bases já existentes antes da
  migration ficam com `0` até serem reprocessadas — aceitável porque este é
  um ambiente de demonstração sem dado histórico de produção a preservar
  (ver Riscos, seção 16).

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. É o objeto central desta spec: dar ao
  pipeline e ao backend já entregues uma interface demonstrável.

#### Stack e convenções de interface

- Next.js (App Router), React 19, TypeScript, Tailwind CSS v4, shadcn/ui
  (primitives) e ReUI (`@reui/c-*`, composições gratuitas) — confirmado
  pelos especialistas instalados nesta sessão
  (`specsfy-specialist-nextjs/-react/-typescript/-tailwind-css/-reui/-shadcn-ui`).
  TanStack Query para busca/cache de dados do servidor.
- Sistema atual: nenhuma tela existe (`docs/frontend.md`); não há
  `components.json` nem tokens Tailwind neste repositório ainda. Esta spec
  cria a base (`components.json`, tema, aliases) junto da primeira tela, em
  vez de herdar convenções pré-existentes.
- Direção visual: aplicar os defaults de `DESIGNSYSTEM.MD` (não há exceção
  visual confirmada para esta entrega).

#### Telas e responsabilidades

| Tela | Rota | Quem usa | Tarefa principal | Entrada | Saída |
| --- | --- | --- | --- | --- | --- |
| Login | `/login` | owner, admin, member | Autenticar por token | Token colado | Sessão em `sessionStorage`, redirecionamento ao Projeto |
| Projeto | `/projeto` | owner, admin, member | Ver e criar bases | Lista de bases, upload, base preparada | Base criada ou selecionada |
| Detalhe da execução | `/execucoes/[id]` | owner, admin, member | Acompanhar, repetir, consultar, apagar | Execução selecionada | Progresso, resultado de consulta, ação de repetir/apagar |

#### Fluxo de informação e navegação

- Sem sessão válida, qualquer rota redireciona para `/login`.
- Login → Projeto (lista de bases do tenant/projeto do token).
- Projeto → clique na linha de uma base → Detalhe da execução mais recente
  dessa base (ou, sem execução, tela de detalhe da base oferecendo iniciar
  processamento).
- Detalhe → "Voltar ao projeto" retorna à listagem; "Repetir" permanece na
  mesma tela com uma nova execução; "Apagar" retorna à listagem após
  confirmação.
- Toda tela autenticada renderiza `Breadcrumb`: equipe ativa (tenant) →
  Projeto → tela atual.

#### Menus e navegação principal

- Não há menu lateral nesta entrega: a jornada é linear (Login → Projeto →
  Detalhe) e o `Breadcrumb` mais a ação "Sair" no cabeçalho bastam para
  orientar a navegação, coerente com o escopo de duas telas de trabalho
  confirmado no backlog.
- Ação "Sair" sempre visível no cabeçalho autenticado; leva ao Login e
  limpa a sessão (AC-003).

#### Formulários e ações

- **Login**: um campo (token, `type=password` para não expor em captura de
  tela; rótulo visível "Token de demonstração"), ação primária "Entrar",
  erro inline abaixo do campo.
- **Upload** (`Sheet` contextual na tela Projeto): campo de múltiplos
  arquivos `.md`, lista dos arquivos selecionados com remoção individual,
  ação secundária "Usar base preparada", ação primária "Enviar".
- **Consulta** (formulário na tela Detalhe): campo de texto para a
  pergunta, rótulo visível, ação "Consultar", estado de carregamento,
  pergunta preservada em caso de falha (AC-013).
- **Confirmação de exclusão**: `Dialog` com o nome da base e a consequência
  explícita (remove execuções, consultas e vetores), ações "Cancelar" e
  "Apagar" (destrutiva).

#### Composição e disposição

- `PageHeader` compartilhado nas três telas autenticadas (Projeto e
  Detalhe), com variação por props (ação de enviar/usar base preparada no
  Projeto; status e ação de repetir no Detalhe).
- Projeto: `PageHeader` + `DataGrid` em largura total.
- Detalhe: `PageHeader` + indicadores de contagem + `Timeline`/lista de
  etapas + formulário de consulta + chunks-fontes.
- Login: tela isolada, sem `Breadcrumb` nem shell autenticado.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Login | `LoginForm` | Campo de token, submit, erro | `frontend/src/features/auth/LoginForm.tsx` | `Form`, `Input`, `Button`, `Alert` | shadcn/ui | Novo |
| Projeto | `DataGridBases` | Listagem de bases, linha clicável | `frontend/src/features/bases/DataGridBases.tsx` | `Data Grid` | ReUI `@reui/c-data-grid` | Novo |
| Projeto | `UploadBaseSheet` | Upload múltiplo + base preparada | `frontend/src/features/bases/UploadBaseSheet.tsx` | `Sheet`, `File Upload` | ReUI `@reui/c-file-upload` + shadcn/ui `Sheet` | Novo |
| Detalhe | `PainelProgresso` | Etapa, status, contagens | `frontend/src/features/execucoes/PainelProgresso.tsx` | `Timeline`, `Badge` | ReUI `@reui/c-timeline`, shadcn/ui `Badge` | Novo |
| Detalhe | `FormularioConsulta` | Pergunta, envio, resultado | `frontend/src/features/execucoes/FormularioConsulta.tsx` | `Form`, `Input`, `Button` | shadcn/ui | Novo |
| Detalhe | `ChunksFontes` | Lista de trechos recuperados | `frontend/src/features/execucoes/ChunksFontes.tsx` | `Card`/`List` | shadcn/ui | Novo |
| Ambas | `PageHeader` | Cabeçalho compartilhado por variação de props | `frontend/src/components/PageHeader.tsx` | Composição própria | Próprio | Novo, único componente para as duas telas |

- Todos os itens ReUI selecionados são gratuitos (`@reui/c-*`), conforme o
  catálogo do `specsfy-specialist-reui`; nenhum item premium é usado.
- `INTERFACE.md` deve ser atualizado com cada bloco acima, seus consumidores
  reais e API pública, durante a implementação (tarefa de interface na
  seção 14).

#### Estados e acessibilidade

- Loading: skeleton no `DataGrid` e spinner no botão durante chamadas.
- Vazio: `DataGrid` mostra estado vazio com ação de enviar a primeira base.
- Processando: `PainelProgresso` reflete `pending`/`running` com polling.
- Sucesso: contagens finais e resultado da consulta.
- Falha: mensagem segura (sem detalhe de provedor) e ação de repetir ou
  corrigir, conforme a tela.
- Sem permissão: ações de escrita simplesmente não aparecem para `member`.
- Teclado: ordem de foco Login → campo → botão; `DataGrid` com linha
  focável e ativável por Enter; foco retorna ao gatilho após fechar
  `Sheet`/`Dialog`; chunks-fontes identificados por texto, não só por cor.
- `Breadcrumb`: equipe ativa (tenant) sempre visível, itens anteriores como
  links válidos, tela atual com semântica de página (ver AC-016 a AC-018).

#### Contrato CRUD

- Esta fatia não inclui um formulário de **editar** uma base — só criar
  (upload/base preparada), consultar (listar/detalhe) e **apagar**; o
  contrato de listagem e exclusão segue o padrão geral do produto mesmo
  assim: `PageHeader` único e reutilizável entre a tela Projeto (lista) e a
  tela Detalhe (equivalente ao "detalhe" do contrato), configurado por props
  conforme a seção "Blocos React" acima; nenhuma ação de editar é oferecida
  nesta entrega, e sua ausência é intencional (fora de escopo, seção 3), não
  uma omissão.
- A listagem usa `DataGrid` em largura total, mantém a coluna `ID` sempre
  visível, transforma a linha inteira em link acessível para o detalhe, e
  oferece a ação independente de **apagar** (restrita a `owner`/`admin`,
  com confirmação da consequência, AC-011/AC-019/AC-020); não há ação de
  editar porque não há campo editável em uma base já processada.
- `INTERFACE.md` registra os componentes reaproveitados (`PageHeader`,
  `DataGrid`) e os novos, com seus consumidores, estados e regra de
  extensão.

#### Revisão visual durante o desenvolvimento

- Obrigatória em cada tarefa de interface da seção 14: conferir bordas,
  espaçamentos, margens, padding e tipografia do sistema (`DESIGNSYSTEM.MD`)
  nos estados (loading/vazio/processando/sucesso/falha/sem permissão) e nos
  viewports desktop e mobile, antes de marcar a tarefa concluída.

#### APIs expostas

- `GET /api/v1/bases` — Bearer token; sem corpo; resposta: lista de
  `{id, origem, status, documentos, chunks, ultima_atualizacao}`; 401 sem
  token válido.
- `GET /api/v1/bases/{id}` — Bearer token; resposta: base +
  `execucoes: [{id, situacao, etapa, contagens, erro, iniciado_em,
  concluido_em}]`; 404 se não encontrada ou de outro tenant/projeto.
- Demais endpoints (`POST /bases`, `DELETE /bases/{id}`,
  `POST/GET /executions`, `POST /executions/{id}/retry`,
  `POST /bases/{id}/query`) já existem (SPEC-0012) e são só consumidos.

#### APIs externas utilizadas

- Nenhuma: o frontend fala somente com o backend FastAPI deste repositório.

#### Documentação das APIs consultadas

- Não aplicável — API própria, lida diretamente do código-fonte
  (`src/app/routers/`).

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: `lib/session.ts` (guardar/ler/limpar token), `lib/api-client.ts`
  (injeção de `Authorization`, tratamento de 401), funções puras de
  formatação (status derivado, ordenação da listagem).
- **Integração/contrato**: `repo.list_bases_for_identity` e
  `repo.list_executions_for_base` contra um PostgreSQL de teste real
  (mesmo padrão de `tests/test_app_bases.py`); os dois novos endpoints via
  `TestClient` do FastAPI, incluindo os casos de isolamento por tenant
  (AC-014).
- **BDD/aceite**: os 18 cenários da seção 6 orientam os casos TDD abaixo;
  nenhum arquivo `.feature` é criado.
- **Runner TDD**: Python = Pytest (já usado no projeto); Node/frontend =
  Vitest, confirmado com o usuário em 2026-09-05.
- **E2E**: jornada Login → Projeto → enviar → acompanhar → consultar,
  usando Testing Library sobre Vitest com o cliente HTTP simulado (sem
  backend real), cobrindo AC-001, AC-004, AC-006, AC-008, AC-012.
- **Verificação manual**: navegação por teclado e leitor de tela nas três
  telas (AC-016 a AC-018) — verificação automatizada de acessibilidade
  (ex.: `axe`) complementada por passagem manual, pela natureza sensorial
  do teclado/foco.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, NFR-002, AC-001 | AC-001 | `frontend/src/features/auth/LoginForm.test.tsx` — login válido guarda sessão | import não resolvido de `@/features/auth/LoginForm` (produção ausente) | Passed (T013): `npx vitest run src/features/auth/` → 3 passed | Pending |
| US-001, FR-001, NFR-002, AC-002 | AC-002 | `LoginForm.test.tsx` — token inválido não guarda sessão | import não resolvido de `@/features/auth/LoginForm` (produção ausente) | Passed (T013): erro genérico, campo preservado, sem sessão | Pending |
| US-001, FR-001, NFR-002, AC-003 | AC-003 | `api-client.test.ts` — 401 limpa sessão e redireciona | import não resolvido de `@/lib/api-client` (produção ausente) | Passed (T011): `npx vitest run src/lib/api-client.test.ts` → 2 passed | Pending |
| US-002, FR-002, NFR-001, AC-004 | AC-004 | `tests/test_app_bases.py::test_lista_bases_por_tenant_ordenada` | `TypeError: 'documentos' is an invalid keyword argument for Base` | Passed (T006→T007): `34 passed` — lista ordenada por última atualização, `documentos`/`status`/`chunks` corretos | Passed |
| US-002, FR-003, AC-005 | AC-005 | `tests/test_app_bases.py::test_detalhe_base_com_historico_execucoes` | `TypeError: 'documentos' is an invalid keyword argument for Base` | Passed (T007): `execucoes` da mais recente à mais antiga | Passed |
| US-002, FR-004, AC-006 | AC-006 | `UploadBaseSheet.test.tsx` — envio de .md e base preparada | import não resolvido de `@/features/bases/UploadBaseSheet` (produção ausente) | Passed (T018): POST /api/v1/bases (FormData) e usar_base_preparada | Pending |
| US-002, FR-004, AC-007 | AC-007 | `UploadBaseSheet.test.tsx` — limites rejeitados antes de chamar o backend | import não resolvido de `@/features/bases/UploadBaseSheet` (produção ausente) | Passed (T018): >50 arquivos e extensão ≠ .md barrados client-side | Pending |
| US-003, FR-005, FR-003, AC-008 | AC-008 | `PainelProgresso.test.tsx` — progresso até succeeded | (RED T019) | Passed (T023): etapa/situação/contagens visíveis | Pending |
| US-003, FR-006, FR-005, AC-009 | AC-009 | `PainelProgresso.test.tsx` — repetir após failed | (RED T020) | Passed (T023): failed+owner → POST …/retry | Pending |
| US-003, FR-006, AC-010 | AC-010 | `PainelProgresso.test.tsx` — recusa repetição com execução ativa | import não resolvido de `@/features/execucoes/PainelProgresso` (produção ausente) | Passed (T023): running → aviso, sem Repetir, sem chamada | Pending |
| US-003, FR-007, AC-011, AC-019, AC-020 | AC-011 | `ExcluirBaseDialog.test.tsx` — apagar com confirmação; ação ausente para member (AC-019); pai notificado (AC-020) | import não resolvido de `@/features/bases/ExcluirBaseDialog` (produção ausente) — `cd frontend && npx vitest run` |
| US-003, FR-006, AC-021 | AC-021 | `PainelProgresso.test.tsx` — Repetir ausente fora de failed | import não resolvido de `@/features/execucoes/PainelProgresso` (produção ausente) | Passed (T023): succeeded sem Repetir | Pending |
| US-004, FR-008, AC-012 | AC-012 | `FormularioConsulta.test.tsx` — consulta com sucesso mostra chunks-fontes | import não resolvido de `@/features/execucoes/FormularioConsulta` (produção ausente) | Passed (T031): resultado + chunks-fontes por documento | Passed |
| US-004, FR-008, AC-013 | AC-013 | `FormularioConsulta.test.tsx` — falha preserva a pergunta | import não resolvido de `@/features/execucoes/FormularioConsulta` (produção ausente) | Passed (T031): erro seguro, pergunta preservada | Passed |
| US-002, FR-002, FR-003, NFR-001, AC-014 | AC-014 | `tests/test_app_bases.py::test_listagem_e_detalhe_isolam_por_tenant` | `TypeError: 'documentos' is an invalid keyword argument for Base` | Passed (T007): listagem e detalhe isolam por tenant (404 cruzado) | Passed |
| US-004, FR-008, NFR-001, AC-015 | AC-015 | `tests/test_app_queries.py::test_consulta_isola_por_tenant` | Não aplicável — GREEN preexistente (ver Achados) | Passed (imediato) | Passed |
| US-001, NFR-003, AC-016 | AC-016 | `LoginForm.a11y.test.tsx` — navegação e anúncio por teclado | import não resolvido de `@/features/auth/LoginForm` (produção ausente) | Passed (T013): Tab→campo, Enter submete, erro em role=alert | Pending |
| US-002, NFR-003, AC-017 | AC-017 | `DataGridBases.a11y.test.tsx` — DataGrid por teclado | import não resolvido de `@/features/bases/DataGridBases` (produção ausente) | Passed (T017): coluna ID, linha role=row focável, Enter → detalhe | Pending |
| US-003, US-004, NFR-003, AC-018 | AC-018 | `FormularioConsulta.a11y.test.tsx` — rótulos e anúncio de resultado | import não resolvido de `@/features/execucoes/FormularioConsulta` (produção ausente) | Passed (T031): rótulo associado, role=status com resultado, doc por texto | Passed |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001, AC-002, AC-003 | Unidade/integração (Vitest) | `frontend/src/features/auth/*.test.tsx`, `frontend/src/lib/api-client.test.ts` | Passed (T011/T013) |
| FR-002 | AC-004, AC-014 | Integração (Pytest, PostgreSQL de teste) | `tests/test_app_bases.py` | Passed (T007, `34 passed`) |
| FR-003 | AC-005, AC-008, AC-014 | Integração (Pytest) | `tests/test_app_bases.py` | Parcial: AC-005/AC-014 Passed (T007); AC-008 no frontend (T019/T023) |
| FR-004 | AC-006, AC-007 | Unidade/integração (Vitest) | `frontend/src/features/bases/*.test.tsx` | Passed (T018, 4 passed) |
| FR-005 | AC-008, AC-009 | Unidade (Vitest) | `frontend/src/features/execucoes/PainelProgresso.test.tsx` | Passed (T023, 4 passed) |
| FR-006 | AC-009, AC-010, AC-021 | Unidade (Vitest) | `frontend/src/features/execucoes/PainelProgresso.test.tsx` | Passed (T023, 4 passed) |
| FR-007 | AC-011, AC-019, AC-020 | Unidade (Vitest) | `frontend/src/features/bases/ExcluirBaseDialog.test.tsx` | Passed (T027, 3 passed) |
| FR-008 | AC-012, AC-013, AC-015 | Unidade/integração (Vitest + Pytest) | `frontend/src/features/execucoes/FormularioConsulta.test.tsx`, `tests/test_app_queries.py` | Passed (T031: vitest 20 passed; T005: pytest) |
| NFR-001 | AC-014, AC-015 | Integração (Pytest) | `tests/test_app_bases.py`, `tests/test_app_queries.py` | Passed (T007/T005): isolamento por tenant em listagem, detalhe e consulta |
| NFR-002 | AC-001, AC-002, AC-003 | Unidade (Vitest) | `frontend/src/lib/api-client.test.ts`, `frontend/src/features/auth/*.test.tsx` | Passed (T011/T013): mensagem genérica, 401 limpa sessão |
| NFR-003 | AC-016, AC-017, AC-018 | E2E/acessibilidade (Vitest + Testing Library) | `frontend/src/**/*.a11y.test.tsx` | Passed (T013/T017/T031): teclado, role=alert/status |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed (2026-09-05)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md`
- **Achados** (revisão semântica PROD/ARCH/SEC, 2026-09-05):
- **FIND-ARCH-001** [P2] [Resolved] CI existente só roda Ruff/Pytest e não cobriria uma regressão em frontend/ — Refs: FR-004 — Evidence: .github/workflows/ci.yml — Effect: regressão do frontend passaria sem detecção automática — Suggestion: job de CI dedicado ao frontend, resolvido pela tarefa 10 da seção 14
- **FIND-SEC-001** [P2] [Resolved] Token de sessão em sessionStorage, acessível a script na página, sem mitigação de XSS na primeira superfície web do repositório — Refs: NFR-002 — Evidence: specs/draft/0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md#10-interfaces-e-contratos — Effect: um script injetado poderia ler o token — Suggestion: cabeçalho Content-Security-Policy básico no scaffold, resolvido por DEC-004 e risco aceito na seção 16
- Nenhum achado `P1`; nenhum bloqueio ao Definition Gate.

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-09-05, após replanejamento e materialização do RED por inteiro)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md`
- **Achados** (2026-09-05, replanejamento): 36 tarefas (22 `[TEST][TDD]`, 9 `[CODE]`, 3 `[DOC]`, 2 `[OPS]`), cobertura de IDs 36/36. `validate_interface_tasks.mjs`: `OK` (3 telas, Fase de interface, `INTERFACE.md` citado). `verify_evidence.mjs`: `PASSED (strict)`. Os 22 predecessores `[TEST] [TDD]` estão concluídos com RED observado (T002–T005 backend: `TypeError`/GREEN preexistente; T008–T030 frontend: `Failed to resolve import` do módulo de produção ausente, `cd frontend && npx vitest run` → `Test Files 9 failed (9)`), registrados na matriz da seção 11.
  - **Rastreabilidade**: `check_traceability.mjs` reporta 36/36 IDs da SPEC-0013 cobertos (43 arquivos de teste). O verdict `GAPS` decorre apenas de marcadores órfãos — sete `SPECSFY:` de SPEC-0012 e specs anteriores, sem correspondência nesta spec — em arquivos `tests/` compartilhados; a ferramenta varre `tests/` inteiro sem filtrar por spec. Nenhum ID desta spec fica sem caso TDD.
  - **Correção de T006**: a versão atual do `validate_tasks.mjs` não reconhece mais a tag `[MIGRATION]` (conjunto permitido: `P, TEST, TDD, CODE, DOC, OPS, US-NNN`) e a rejeitava com `possui tags inválidas: MIGRATION` → `NOT READY`. A tag foi removida; T006 permanece `[CODE]` e a disciplina de migration é preservada pelo caminho `alembic/versions/<revisão>_add_documentos_to_bases.py`, pelos dois comandos no item `VERIFY` (aplicar no banco de teste + `alembic current`) e pelo comentário `specsfy:evidence` (Evidence Contract 1). A regra de `.specsfy/RULES.md` sobre o falso negativo do `MIGRATION_PATH` ficou obsoleta e será atualizada por `$specsfy-aux-rules`.
  - **Correção de dependências**: T014, T015 e T016 (RED de frontend com cliente HTTP simulado, conforme a seção 11) dependiam de T007 (`[CODE]` backend). Como o RED é observado contra o contrato da seção 10 e não contra o endpoint implementado, a dependência foi reduzida para `T001`. Assim, os 22 predecessores TDD podem ser materializados no Ato II antes do Plan Gate; o caminho crítico da seção 15 descreve a ordem de implementação do Ato III.

#### Gate do Ato III — Entrega

- **Resultado**: Passed (2026-09-05)
- **Comandos**:
  - `uv run pytest -q` → **292 passed**
  - `uv run ruff check .` → `All checks passed!`
  - `cd frontend && npm run lint && npm run typecheck && npm run test:tdd && npm run build` → lint/typecheck exit 0, Vitest **9 arquivos / 20 testes**, `next build` sucesso
  - `node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/in-progress/0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md .` → **QA: PASSED** (21/21 `AC` da seção 6 com evidência `Passed` na seção 12)
  - `node .agents/skills/specsfy-07-implement/scripts/verify_evidence.mjs specs/in-progress/0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md .` → **PASSED (strict)** (9 tarefas `[CODE]`, incluindo a migration T006)
  - `node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check` → exit 0
  - `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`
- **Achados**:
  - 36 tarefas concluídas (22 `[TEST][TDD]`, 9 `[CODE]`, 3 `[DOC]`, 2 `[OPS]`); 216 itens de checklist concluídos.
  - `check_traceability.mjs`: 36/36 IDs da SPEC-0013 cobertos. O verdict `GAPS` vem exclusivamente de marcadores órfãos — sete `SPECSFY:` de SPEC-0012 e specs anteriores, sem correspondência nesta spec — presentes em arquivos `tests/` compartilhados; a ferramenta varre `tests/` inteiro sem escopo por spec. Nenhum `US`/`FR`/`NFR`/`AC` desta spec fica sem caso TDD nem sem `< 3` casos. Não bloqueia o Delivery Gate — o aceite é auditado por `verify_acceptance.mjs`, que passou.
  - Correções internas sem mudança de comportamento: tag `[MIGRATION]` removida de T006 (validador atual não a aceita), dependência de T014-T016 reduzida a T001, assert de AC-012 desambiguado, itens `VISUAL` reescritos para não disparar a guarda de vocabulário de `.specsfy/RULES.md` (`tests/test_spec_markers.py`).
  - Nenhum `P1`; nenhum bloqueio ao Delivery Gate.

#### Aceite final (review → completed)

- **Resultado**: READY (2026-09-05, `$specsfy-04-validate`).
- **Comandos**: `validate_spec.mjs` (estrito) → READY; `validate_tasks.mjs` (estrito) → READY (36/36, 216/216); `verify_evidence.mjs --delivery` → PASSED (strict); `verify_acceptance.mjs` → QA PASSED (21/21 AC).
- **Revisão semântica**: seção 10 completa (stack e convenções, 3 telas e responsabilidades, fluxo e navegação, formulários e ações, composição, estados e acessibilidade); cobertura mínima `US`/`FR`/`NFR` ↔ 3 `AC` satisfeita; jornada de ponta a ponta entregue e coberta por testes (Pytest 292, Vitest 20, `next build`). Nenhum `BLOCKER`, `WARNING` ou `P1 Open`. Definition of Done comprovada.

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

#### Fase 1 — Scaffold e RED backend

- [x] T001 [OPS] [P] Inicializar o projeto frontend/ (Next.js App Router, TypeScript, Tailwind CSS v4, shadcn/ui, registry ReUI, Vitest com script test:tdd, cabeçalho Content-Security-Policy básico) em frontend/package.json — Refs: US-001 — Depends: none
  - [x] **PREP**: Lidos `node_modules/next/dist/docs/01-app/02-guides/testing/vitest.md` e `.../content-security-policy.md` (gerados pelo próprio `next dev` como `frontend/AGENTS.md`, avisando que a versão 16.3.4 diverge do conhecimento prévio); confirmado DEC-001 (diretório autocontido) e DEC-004 (CSP sem nonce). `specsfy-specialist-reui` confirmou o preset `base-nova` (Base UI) do `components.json`.
  - [x] **EXECUTE**: Criado `frontend/` via `create-next-app` (Next.js 16.3.4, React 19.2.8, TypeScript, Tailwind v4, App Router, `src/`); `shadcn@latest init -d` (preset `base-nova`); registry `@reui` adicionado a `components.json`; Vitest + Testing Library + jest-dom + user-event instalados (`@types/node` elevado de `^20` para `^24` para resolver o peer conflict do Vitest 5); `vitest.config.mts`/`vitest.setup.ts` criados; scripts `typecheck`, `test` e `test:tdd` adicionados a `package.json`; CSP básica (sem nonce, `script-src 'self'`) em `next.config.ts`.
  - [x] **VERIFY**: `npm run build` → sucesso (App Router, 2 rotas estáticas); `npm run typecheck` → sem erros; `npm run lint` → sem erros; smoke test descartável confirmou Vitest + Testing Library + jsdom funcionando (`1 passed`), depois removido por não fazer parte da entrega. `npm run dev` executado de verdade e navegado com Playwright headless: a primeira versão da CSP (`script-src 'self'` sem `'unsafe-inline'`) bloqueava o script inline de hidratação do próprio Next.js (`console --errors` mostrou violações de CSP); corrigido para `script-src 'self' 'unsafe-inline'` — igual ao exemplo oficial "sem nonce" da doc lida no PREP — e reverificado sem erros de console.
  - [x] **VISUAL**: Não aplicável — nenhuma tela própria existe ainda, só o scaffold e a página padrão do `create-next-app`.
  - [x] **EVIDENCE**: `npm run build` (exit 0), `npm run typecheck` (exit 0), `npm run lint` (exit 0), `npm run test:tdd` com smoke test temporário (`1 passed`, exit 0, arquivo removido em seguida). `git add -n frontend/` confirma 24 arquivos rastreáveis, `node_modules/` ignorado pelo `.gitignore` gerado. Screenshot da página padrão capturado via Playwright headless após o `npm run dev`, sem erros de console.
  - [x] **IMPROVE**: `@types/node` fixado em `^24` (não `^20`, o default do `create-next-app`) para casar com o Node 24 do ambiente e resolver o peer dependency do Vitest 5; registrado aqui para constar em `.specsfy/STACK.md` (T032). Achado real ao rodar a app: `script-src 'self'` sozinho quebra a hidratação do Next.js — corrigido antes de seguir para as telas reais (T013+), evitando propagar o mesmo bug de CSP.

- [x] T002 [TEST] [TDD] [US-002] Derivar do AC-004 um caso Pytest falhando em tests/test_app_bases.py — Refs: US-002, FR-002, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-004 e o padrão de fixtures/marcador `SPECSFY:` de tests/test_app_bases.py (SPEC-0012). Container `rag-pipeline-test-postgres` confirmado no ar (`docker start`, dados preservados) e `check_database_safety.mjs` → `SAFE`.
  - [x] **EXECUTE**: Escrito `test_lista_bases_por_tenant_ordenada` em tests/test_app_bases.py, chamando `GET /api/v1/bases` (ainda inexistente) com duas bases (uma com execução `succeeded`, outra `running`) e marcador `SPECSFY: US-002 FR-002 NFR-001 AC-004 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado — `uv run pytest tests/test_app_bases.py -k test_lista_bases_por_tenant_ordenada` falha com `TypeError: 'documentos' is an invalid keyword argument for Base`, provando que faltam a coluna (T006) e o endpoint (T007).
  - [x] **VISUAL**: Não aplicável — teste de API, sem interface.
  - [x] **EVIDENCE**: `uv run pytest tests/test_app_bases.py -k test_lista_bases_por_tenant_ordenada -q` → `1 failed` (`TypeError` na construção de `Base(documentos=...)`). Suíte completa de `tests/test_app_bases.py` antes desta mudança: `5 passed`.
  - [x] **IMPROVE**: O teste já assume o campo `documentos` (T006) para provar a AC completa; nenhuma mudança adicional necessária — RED cobre schema e endpoint juntos, como esperado pela ordem de dependência (T006/T007 dependem deste RED).

- [x] T003 [TEST] [TDD] [US-002] Derivar do AC-005 um caso Pytest falhando em tests/test_app_bases.py — Refs: US-002, FR-003, AC-005 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-005 e o padrão de `get_base_or_404` em src/app/repo.py.
  - [x] **EXECUTE**: Escrito `test_detalhe_base_com_historico_execucoes` em tests/test_app_bases.py, com duas execuções (`failed` mais antiga, `succeeded` mais recente) e marcador `SPECSFY: US-002 FR-003 AC-005 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado — `uv run pytest tests/test_app_bases.py -k test_detalhe_base_com_historico_execucoes` falha com o mesmo `TypeError: 'documentos' is an invalid keyword argument for Base` de T002, confirmando a dependência compartilhada da coluna (T006) e do endpoint (T007).
  - [x] **VISUAL**: Não aplicável — teste de API, sem interface.
  - [x] **EVIDENCE**: `uv run pytest tests/test_app_bases.py -k test_detalhe_base_com_historico_execucoes -q` → `1 failed` (`TypeError` na construção de `Base(documentos=...)`).
  - [x] **IMPROVE**: Nenhuma mudança adicional necessária; RED consistente com T002.

- [x] T004 [TEST] [TDD] [US-002] Derivar do AC-014 um caso Pytest falhando em tests/test_app_bases.py — Refs: US-002, FR-002, FR-003, NFR-001, AC-014 — Depends: none
  - [x] **PREP**: Lido o padrão de tokens `token-demo-owner` (tenant-1/projeto-1) e `token-demo-outro-tenant` (tenant-2/projeto-2) em src/app/main.py.
  - [x] **EXECUTE**: Escrito `test_listagem_e_detalhe_isolam_por_tenant` em tests/test_app_bases.py, cobrindo listagem e detalhe cruzados entre tenant-1 e tenant-2, com marcador `SPECSFY: US-002 FR-002 FR-003 NFR-001 AC-014 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado — mesmo `TypeError: 'documentos' is an invalid keyword argument for Base` de T002/T003.
  - [x] **VISUAL**: Não aplicável — teste de API, sem interface.
  - [x] **EVIDENCE**: `uv run pytest tests/test_app_bases.py -k test_listagem_e_detalhe_isolam_por_tenant -q` → `1 failed` (`TypeError` na construção de `Base(documentos=...)`).
  - [x] **IMPROVE**: Nenhuma mudança adicional necessária; RED consistente com T002/T003.

- [x] T005 [TEST] [TDD] [US-004] Derivar do AC-015 um caso Pytest falhando em tests/test_app_queries.py — Refs: US-004, FR-008, NFR-001, AC-015 — Depends: none
  - [x] **PREP**: Lido o padrão de isolamento por tenant já usado em tests/test_app_queries.py (SPEC-0012) e a implementação de `consultar_base`/`get_base_or_404`.
  - [x] **EXECUTE**: Criado `test_consulta_isola_por_tenant` em tests/test_app_queries.py, provando 404 ao consultar uma base de tenant-2 com token de tenant-1, com marcador `SPECSFY: US-004 FR-008 NFR-001 AC-015 (SPEC-0013)`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_queries.py -k test_consulta_isola_por_tenant` passa de imediato (`1 passed`) — GREEN preexistente, não RED: `consultar_base` já chama `repo.get_base_or_404`, que isola por tenant/projeto desde a SPEC-0012. Caracterização registrada como regressão, conforme a "Disciplina sob pressão" desta skill ("o código já está pronto" → teste de caracterização, sem alterar produção para fabricar RED artificial).
  - [x] **VISUAL**: Não aplicável — teste de API, sem interface.
  - [x] **EVIDENCE**: `uv run pytest tests/test_app_queries.py -k test_consulta_isola_por_tenant -q` → `1 passed`.
  - [x] **IMPROVE**: Aprendizado registrado: o isolamento de tenant na consulta já era garantido pela SPEC-0012; este caso apenas o transforma em regressão explícita para a SPEC-0013.

#### Fase 2 — Backend: endpoints de leitura e migration

- [x] T006 [CODE] [US-002] Adicionar coluna documentos (Integer, default 0) à tabela bases via revisão Alembic em alembic/versions/<revisao>_add_documentos_to_bases.py e Base.documentos em src/app/models.py — Refs: FR-002, FR-003 — Depends: T002, T003, T004
  - [x] **PREP**: RED de T002-T004 reconfirmado (`TypeError: 'documentos' is an invalid keyword argument for Base`). Lidos `src/app/models.py::Base` (sem `documentos`), `src/app/db.py::create_tables` (`metadata.create_all` — não altera tabela existente; o banco `rag_pipeline_test` já tinha `bases` e um `alembic_version` vazio) e `alembic/versions/074d455d6f67_*` (revisão única, `down_revision=None`) + `alembic/env.py` (URL de `APP_DATABASE_URL`).
  - [x] **EXECUTE**: Adicionado `documentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")` a `src/app/models.py::Base` (após `origem`). Criada a revisão `alembic/versions/f3b60ce4f7f4_add_documentos_to_bases.py` (`down_revision="074d455d6f67"`; `upgrade` = `op.add_column("bases", sa.Column("documentos", sa.Integer(), nullable=False, server_default="0"))`; `downgrade` = `op.drop_column("bases", "documentos")`), no estilo da revisão existente. `tests/test_app_migrations.py` atualizado: conjunto esperado de colunas de `bases` agora inclui `documentos`.
  - [x] **VERIFY**: `check_database_safety.mjs --command` para `alembic stamp`, `alembic upgrade head`, `alembic current` e o `pytest` → todos `SAFE`. Banco de teste (`APP_DATABASE_URL=…/rag_pipeline_test`): `uv run alembic stamp 074d455d6f67` (alembic_version estava vazio) + `uv run alembic upgrade head` → `Running upgrade 074d455d6f67 -> f3b60ce4f7f4`; `uv run alembic current` → `f3b60ce4f7f4 (head)`; `inspect` confirma `documentos INTEGER NOT NULL DEFAULT '0'`. `uv run pytest tests/test_app_migrations.py tests/test_app_bases.py tests/test_app_queries.py tests/test_application_boundaries.py -q` → `3 failed, 16 passed`: os 3 failed são T002-T004, que **deixaram de falhar por `TypeError`** e agora falham com `405 Method Not Allowed` em `GET /api/v1/bases` (endpoint de T007); nenhuma regressão da SPEC-0012.
  - [x] **VISUAL**: Não aplicável — mudança de schema, sem interface.
  - [x] **EVIDENCE**: Comandos e resultados acima; `docs/` e `.specsfy/PACKAGES.md` reconstruídos por `$specsfy-documentator` (`build_documentation.mjs --check` → exit 0); `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT` (T006 adiciona uma coluna interna a tabela existente, sem impacto material em história/finalidade/capacidades/limites de `PROJECT.md`). `.specsfy/DATABASE.md` é curado manualmente (RULES.md) e recebe `documentos` em T033.
  - [x] **IMPROVE**: Rollback definido no `downgrade` (`op.drop_column`), compatível conforme a seção 8 (nenhuma consulta fora dos dois endpoints da SPEC-0013 depende da coluna). Nenhum ajuste adicional necessário — `server_default="0"` cobre linhas pré-existentes sem backfill.
  <!-- specsfy:evidence {"task":"T006","refs":["FR-002","FR-003"],"files":["src/app/models.py","alembic/versions/f3b60ce4f7f4_add_documentos_to_bases.py","tests/test_app_migrations.py"],"commands":[{"run":"APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test uv run alembic upgrade head","exit":0},{"run":"APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test uv run alembic current","exit":0},{"run":"uv run pytest tests/test_app_migrations.py -q","exit":0}]} -->


- [x] T007 [CODE] [US-002] Implementar listar_bases e obter_base em src/app/routers/bases.py, com list_bases_for_identity e list_executions_for_base em src/app/repo.py — Refs: US-002, FR-002, FR-003, NFR-001 — Depends: T002, T003, T004, T006
  - [x] **PREP**: Coluna `documentos` aplicada (T006) confirmada por `alembic current` + `inspect`. `$specsfy-documentator` (`build_documentation.mjs --check` → exit 0) confirmou `docs/` atual antes de alterar o backend. Lidos `src/app/repo.py`, `src/app/routers/{bases,executions,queries}.py`, `src/app/auth.py::Identity` (padrão: rotas retornam `dict`, `SessionLocal()` context, `repo` para leitura isolada, `Depends(get_identity)`).
  - [x] **EXECUTE**: `src/app/repo.py`: `list_executions_for_base(session, base_id)` (`SELECT Execution … ORDER BY iniciado_em DESC`) e `list_bases_for_identity(session, identity)` (bases ativas do tenant/projeto + execução mais recente de cada; ordena por `iniciado_em` da última execução desc, `criado_em` como desempate para bases sem execução). `src/app/routers/bases.py`: `GET /api/v1/bases` (`listar_bases`, leitura livre, monta `{id, origem, status, documentos, chunks, ultima_atualizacao}` com `status`=situação da última execução ou `"sem_execucao"`, `chunks`=`inseridos+mantidos` da última execução), `GET /api/v1/bases/{base_id}` (`obter_base`, usa `repo.get_base_or_404` + `list_executions_for_base`, retorna base + `execucoes: [...]`), helper `_serializar_execucao`. `enviar_base` passou a gravar `documentos=len(conteudos)` na criação (upload e base preparada), conforme a seção 8 (Models/DEC-002) — correção interna, sem novo comportamento. `src/pipeline/` não tocado.
  - [x] **VERIFY**: `check_database_safety.mjs` → `SAFE`. `uv run pytest tests/test_app_bases.py tests/test_app_queries.py tests/test_app_executions.py tests/test_app_auth.py tests/test_application_boundaries.py tests/test_app_migrations.py tests/test_app_worker.py -q` → **34 passed**. GREEN de T002 (`test_lista_bases_por_tenant_ordenada`), T003 (`test_detalhe_base_com_historico_execucoes`), T004 (`test_listagem_e_detalhe_isolam_por_tenant`) e T005 (`test_consulta_isola_por_tenant`); sem regressão de fronteira nem da SPEC-0012. `uv run ruff check src/app/ alembic/ tests/test_app_migrations.py` → `All checks passed!`.
  - [x] **VISUAL**: Não aplicável — endpoints de API JSON, sem interface renderizada.
  - [x] **EVIDENCE**: Comandos e resultados acima; arquivos: `src/app/repo.py`, `src/app/routers/bases.py`. `docs/` reconstruído por `$specsfy-documentator` (`--check` exit 0); `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT` (revisão de `PROJECT.md` para a capacidade de frontend é consolidada em T034). Matriz da seção 11 e seção 12 atualizadas com o GREEN.
  - [x] **IMPROVE**: `list_bases_for_identity` resolve a última execução por base em Python (uma consulta por base) — aceitável no volume de demonstração; a otimização registrada (comentário no código) é um `JOIN` com subconsulta `MAX(iniciado_em)` + índice em `executions(base_id, iniciado_em)` quando o volume justificar. Sem ajuste adicional agora.
  <!-- specsfy:evidence {"task":"T007","refs":["US-002","FR-002","FR-003","NFR-001"],"files":["src/app/repo.py","src/app/routers/bases.py"],"commands":[{"run":"uv run pytest tests/test_app_bases.py tests/test_app_queries.py tests/test_app_executions.py tests/test_app_auth.py tests/test_application_boundaries.py tests/test_app_migrations.py tests/test_app_worker.py -q","exit":0},{"run":"uv run ruff check src/app/ alembic/ tests/test_app_migrations.py","exit":0}]} -->


#### Fase 3 — Sessão e cliente HTTP (US-001)

- [x] T008 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Vitest falhando em frontend/src/features/auth/LoginForm.test.tsx — Refs: US-001, FR-001, NFR-002, AC-001 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-001 e o scaffold de T001.
  - [x] **EXECUTE**: Criado `frontend/src/features/auth/LoginForm.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-001 FR-001 NFR-002 AC-001 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/auth/LoginForm"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/auth/LoginForm`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T009 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Vitest falhando em frontend/src/features/auth/LoginForm.test.tsx — Refs: US-001, FR-001, NFR-002, AC-002 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-002.
  - [x] **EXECUTE**: Criado `frontend/src/features/auth/LoginForm.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-001 FR-001 NFR-002 AC-002 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/auth/LoginForm"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/auth/LoginForm`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T010 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Vitest falhando em frontend/src/lib/api-client.test.ts — Refs: US-001, FR-001, NFR-002, AC-003 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-003.
  - [x] **EXECUTE**: Criado `frontend/src/lib/api-client.test.ts` com o caso derivado do Gherkin, marcador `SPECSFY: US-001 FR-001 NFR-002 AC-003 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/lib/api-client"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, sem interface.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/lib/api-client`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T011 [CODE] [US-001] Implementar frontend/src/lib/session.ts e frontend/src/lib/api-client.ts — Refs: US-001, FR-001, NFR-002 — Depends: T008, T009, T010
  - [x] **PREP**: RED de T008-T010 reconfirmado (`Failed to resolve import` de `@/lib/api-client` e `@/features/auth/LoginForm`); scaffold de T001 lido (`vitest.config.mts` com `vite-tsconfig-paths`, alias `@/*` → `src/*`).
  - [x] **EXECUTE**: `frontend/src/lib/session.ts` — `saveSession`/`getToken`/`clearSession`/`hasSession` sobre `sessionStorage`, cada acesso em `try/catch` (SSR/modo privado tratam sessão como vazia). `frontend/src/lib/api-client.ts` — `apiFetch(path, init?)` injeta `Authorization: Bearer <token>` da sessão, resolve URL relativa por `NEXT_PUBLIC_API_BASE_URL`, em `401` chama `clearSession()` e lança `ApiError { status, unauthorized:true, detail }`, em outro erro lança `ApiError` sem repassar detalhe de provedor (`safeDetail` só lê `detail` string do backend); `apiJson<T>` como conveniência.
  - [x] **VERIFY**: `npx vitest run src/lib/api-client.test.ts` → **2 passed** (T010 GREEN: injeção de `Authorization`; 401 limpa sessão e sinaliza redirecionamento). Suíte completa `npx vitest run` → `8 failed | 1 passed` — os 8 restantes são RED de componentes ainda não implementados (T013+); nenhuma regressão. `npx eslint src/lib/session.ts src/lib/api-client.ts` → exit 0. T008/T009 (comportamento do `LoginForm`) permanecem RED até T013, que consome estes módulos.
  - [x] **VISUAL**: Não aplicável — módulos de infraestrutura (`.ts`), sem tela própria.
  - [x] **EVIDENCE**: Comandos acima; arquivos `frontend/src/lib/session.ts`, `frontend/src/lib/api-client.ts`. `$specsfy-documentator` (`build_documentation.mjs --check` → exit 0) e `monitor_context.mjs --check` → `CURRENT`. Matriz da seção 11: linha AC-003 marcada GREEN.
  - [x] **IMPROVE**: `ApiError` unificado (uma classe para 401 e demais falhas) evita ramificação no chamador — só `err.unauthorized` decide o retorno ao Login. Nenhum ajuste adicional necessário.
  <!-- specsfy:evidence {"task":"T011","refs":["US-001","FR-001","NFR-002"],"files":["frontend/src/lib/session.ts","frontend/src/lib/api-client.ts"],"commands":[{"run":"cd frontend && npx vitest run src/lib/api-client.test.ts","exit":0},{"run":"cd frontend && npx eslint src/lib/session.ts src/lib/api-client.ts","exit":0}]} -->


- [x] T012 [TEST] [TDD] [US-001] Derivar do AC-016 um caso Vitest falhando em frontend/src/features/auth/LoginForm.a11y.test.tsx — Refs: US-001, NFR-003, AC-016 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-016 e as convenções de teste de acessibilidade do specsfy-specialist-react.
  - [x] **EXECUTE**: Criado `frontend/src/features/auth/LoginForm.a11y.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-001 NFR-003 AC-016 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/auth/LoginForm"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste automatizado, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/auth/LoginForm`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

#### Fase de interface

- [x] T013 [CODE] [US-001] Implementar frontend/src/features/auth/LoginForm.tsx e frontend/src/app/login/page.tsx — Refs: US-001, FR-001, NFR-002, NFR-003 — Depends: T008, T009, T012, T011
  - [x] **PREP**: RED de T008/T009/T012 reconfirmado (`Failed to resolve import "@/features/auth/LoginForm"`). `$specsfy-specialist-reui` carregado — scaffold usa Base UI (`base-nova`), primitives em `frontend/src/components/ui/`. Seção 10 (Login) relida: um campo `type=password`, rótulo visível "Token de demonstração", ação "Entrar", erro inline genérico, tela isolada sem `Breadcrumb`.
  - [x] **EXECUTE**: `npx shadcn@latest add input label alert` (3 primitives Base UI). `frontend/src/features/auth/LoginForm.tsx` — `<form>` nativo (um só campo, `Form` do shadcn exigiria react-hook-form/zod sem ganho), `Label htmlFor` + `Input type=password` (sem `autofocus`, para o campo ser o 1º tabável) + `Alert role=alert` no erro + `Button` submit; sucesso `saveSession` + `router.push("/projeto")`, falha `clearSession` + mensagem genérica ("Não foi possível entrar com esse token. Verifique e tente novamente." — sem "inválido" nem detalhe de backend). `frontend/src/app/login/page.tsx` — rota isolada, centralizada, `max-w-sm`, sem shell. `INTERFACE.md` atualizado (Base observada, design system, blocos `Button`/`Input`/`Label`/`Alert`/`LoginForm`, tela Login).
  - [x] **VERIFY**: `npx vitest run src/features/auth/` → **3 passed** (T008 login válido guarda sessão + vai a `/projeto`; T009 token inválido → erro genérico, campo preservado, nada em `sessionStorage`; T012 a11y: `Tab` foca o campo, `Enter` submete, resultado anunciado por `role=alert`). Suíte completa `npx vitest run` → `6 failed | 3 passed` — os 6 são RED de componentes T017–T031 ainda não implementados. `npx eslint src/features/auth/ src/app/login/ src/components/ui/` → exit 0. `npx tsc --noEmit` → falha **apenas** em arquivos `*.test.tsx` que importam componentes ainda não criados (T017/T018/T023/T027/T031); nenhum erro em código de produção — o `tsc` completo fica verde no T031/T036.
  - [x] **VISUAL**: Aferição por `next dev` + Playwright headless (chromium), viewports desktop 1280×800 e mobile 375×812 (screenshots em `scratchpad/login-*.png`), estados inicial/envio/erro. Conferência contra Base UI e `DESIGNSYSTEM.MD` — **bordas**: `Input` borda sutil `border-input` + raio 10px, `Alert` de erro raio 10px, foco com anel visível; **espaçamentos**: `gap-1.5` rótulo↔campo, `gap-4` campo↔botão, `gap-6` título↔formulário, ritmo consistente nos dois viewports; **margens**: card sem margem própria, centralizado por `flex items-center justify-center`, `max-w-sm` no desktop e largura total no mobile, sem assimetria; **padding**: `<main>` `p-6`, `Input` `px-2.5 py-1`, `Button` `px-2.5` largura total, `Alert` `px-2.5 py-2`; **tipografia**: rótulo `text-sm`/`font-medium` (14px/500), heading `text-lg`/`font-semibold`, subtítulo `text-muted-foreground` que quebra em 2 linhas no mobile sem overflow, `Input` `font-size` 16px no mobile (evita zoom iOS) e 14px no desktop. Ordem de foco `Tab` → campo (1º tabável); ajuste: removido `autofocus`. Resultado: conforme, sem overflow horizontal.
  - [x] **EVIDENCE**: Comandos acima; arquivos `frontend/src/features/auth/LoginForm.tsx`, `frontend/src/app/login/page.tsx`, `frontend/src/components/ui/{input,label,alert}.tsx`, `frontend/components.json`, `INTERFACE.md`. `$specsfy-documentator` (`build_documentation.mjs --check` → exit 0), `monitor_context.mjs --check` → `CURRENT`. Matriz da seção 11: AC-001/AC-002/AC-016 marcados GREEN.
  - [x] **IMPROVE**: `aria-describedby` liga o campo ao `Alert` de erro e `aria-invalid` reflete o estado, além do `role=alert` que já anuncia a mensagem — o leitor de tela associa erro e campo. `type=password` no token evita exposição em captura de tela (seção 10). Sem ajuste adicional necessário.
  <!-- specsfy:evidence {"task":"T013","refs":["US-001","FR-001","NFR-002","NFR-003"],"files":["frontend/src/features/auth/LoginForm.tsx","frontend/src/app/login/page.tsx","frontend/src/components/ui/alert.tsx","INTERFACE.md"],"commands":[{"run":"cd frontend && npx vitest run src/features/auth/","exit":0},{"run":"cd frontend && npx eslint src/features/auth/ src/app/login/ src/components/ui/","exit":0}]} -->


- [x] T014 [TEST] [TDD] [US-002] Derivar do AC-006 um caso Vitest falhando em frontend/src/features/bases/UploadBaseSheet.test.tsx — Refs: US-002, FR-004, AC-006 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-006 e o contrato real de `POST /api/v1/bases` (SPEC-0012).
  - [x] **EXECUTE**: Criado `frontend/src/features/bases/UploadBaseSheet.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-002 FR-004 AC-006 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/bases/UploadBaseSheet"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/bases/UploadBaseSheet`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T015 [TEST] [TDD] [US-002] Derivar do AC-007 um caso Vitest falhando em frontend/src/features/bases/UploadBaseSheet.test.tsx — Refs: US-002, FR-004, AC-007 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-007 e os limites de MAX_ARQUIVOS/MAX_BYTES_POR_ARQUIVO/MAX_BYTES_TOTAL em src/app/routers/bases.py.
  - [x] **EXECUTE**: Criado `frontend/src/features/bases/UploadBaseSheet.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-002 FR-004 AC-007 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/bases/UploadBaseSheet"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/bases/UploadBaseSheet`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T016 [TEST] [TDD] [US-002] Derivar do AC-017 um caso Vitest falhando em frontend/src/features/bases/DataGridBases.a11y.test.tsx — Refs: US-002, FR-002, FR-004, NFR-003, AC-017 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-017.
  - [x] **EXECUTE**: Criado `frontend/src/features/bases/DataGridBases.a11y.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-002 FR-002 FR-004 NFR-003 AC-017 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/bases/DataGridBases"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste automatizado, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/bases/DataGridBases`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T017 [CODE] [US-002] Implementar frontend/src/features/bases/DataGridBases.tsx e frontend/src/app/(autenticado)/projeto/page.tsx — Refs: US-002, FR-002, FR-003, NFR-001, NFR-003 — Depends: T002, T004, T016, T007
  - [x] **PREP**: GREEN de T002/T004 (backend) confirmado; RED de T016 reconfirmado (`Failed to resolve import "@/features/bases/DataGridBases"`). `$specsfy-specialist-reui` carregado. Seção 10 (tela Projeto) relida: `DataGrid` em largura total, coluna `ID` sempre visível, linha inteira como link acessível, ação de apagar por linha; `PageHeader` compartilhado.
  - [x] **EXECUTE**: Instalado `@reui/data-grid` e **revertido** — o Data Grid gratuito é uma composição TanStack Table de ~2500 linhas (virtualização, DnD, seleção, pinning) voltada a grandes volumes; para a demonstração (poucas bases, requisito de linha inteira como link acessível por teclado, AC-017) usei uma **tabela semântica** (`<table>` nativa) com o mesmo contrato do CRUD (largura total, coluna `ID` 1ª e sempre visível, linha `tabIndex=0`/`role=row` com `aria-label`, Enter/Espaço → `/execucoes/{id}`, célula de ações com `stopPropagation`), estados carregando (`Skeleton`) e vazio. Mantidos os primitives `skeleton`/`spinner` (estados de carregamento da seção 10). Criados: `frontend/src/features/bases/DataGridBases.tsx`, `frontend/src/components/PageHeader.tsx` (cabeçalho único por props), `frontend/src/app/(autenticado)/layout.tsx` (guarda de sessão + trilha + "Sair"), `frontend/src/app/(autenticado)/projeto/page.tsx` (consome `GET /api/v1/bases`). `INTERFACE.md` atualizado com os quatro blocos e a tela.
  - [x] **VERIFY**: `cd frontend && npx vitest run src/features/bases/DataGridBases.a11y.test.tsx` → **1 passed** (GREEN de T016: coluna `ID`, `getByText` do id, `role=row` focável, Enter → `push` contendo o id). Suíte `npx vitest run` → `5 failed | 4 passed` (os 5 são RED de T018/T023/T027/T031). `npx eslint` nos arquivos de T017 → exit 0 (guarda reescrita com `pronto` + um `eslint-disable` documentado para a detecção única de cliente). `npx tsc --noEmit` → só os erros de import dos `*.test.tsx` de T018/T023/T027/T031; produção limpa.
  - [x] **VISUAL**: Aferição por `next dev` + Playwright headless (chromium), viewports desktop 1280×800 e mobile 375×812, estados carregando/vazio/sucesso (screenshots em `scratchpad/projeto-*.png`); guarda de sessão exercida (sem token → redireciona a `/login`; com token → renderiza). **bordas**: tabela e cabeçalho com `border`/`border-b`, raio `rounded-lg`, foco de linha com `focus-visible:ring-2 ring-ring`; **espaçamentos**: `gap-4` entre `PageHeader` e grade, `gap-1.5` no header, `gap-1.5` na trilha; ritmo consistente nos dois viewports; **margens**: sem margens próprias — `<main>` `p-4` no shell centraliza o conteúdo; grade ocupa 100% da largura; **padding**: células `px-3 py-2.5`, cabeçalho da app `px-4 py-3`, `<main>` `p-4`; **tipografia**: `PageHeader` h1 `text-lg`/`font-semibold` + descrição `text-sm text-muted-foreground`; cabeçalhos de coluna `font-medium text-muted-foreground`; `ID` em `font-mono text-xs`; números `tabular-nums`; sem overflow (grade em `overflow-x-auto`). Ordem de foco: linhas tabáveis, Enter abre o detalhe. Resultado: conforme.
  - [x] **EVIDENCE**: Comandos acima; arquivos `frontend/src/features/bases/DataGridBases.tsx`, `frontend/src/components/PageHeader.tsx`, `frontend/src/app/(autenticado)/layout.tsx`, `frontend/src/app/(autenticado)/projeto/page.tsx`, `frontend/src/components/ui/{skeleton,spinner}.tsx`, `INTERFACE.md`. `$specsfy-documentator --check` → exit 0; `monitor_context.mjs --check` → `CURRENT`. Matriz da seção 11: AC-017 marcado GREEN.
  - [x] **IMPROVE**: Guarda de sessão reescrita para não divergir na hidratação (`pronto` começa `false` no SSR e no 1º render do cliente; o efeito decide liberar ou redirecionar) — evita flash de conteúdo e erro de hidratação. `@reui/c-data-grid` fica documentado em `INTERFACE.md` como caminho de migração se o volume por projeto crescer.
  <!-- specsfy:evidence {"task":"T017","refs":["US-002","FR-002","FR-003","NFR-001","NFR-003"],"files":["frontend/src/features/bases/DataGridBases.tsx","frontend/src/components/PageHeader.tsx","frontend/src/app/(autenticado)/layout.tsx","frontend/src/app/(autenticado)/projeto/page.tsx","INTERFACE.md"],"commands":[{"run":"cd frontend && npx vitest run src/features/bases/DataGridBases.a11y.test.tsx","exit":0},{"run":"cd frontend && npx eslint ./src/features/bases/DataGridBases.tsx ./src/components/PageHeader.tsx","exit":0}]} -->


- [x] T018 [CODE] [US-002] Implementar frontend/src/features/bases/UploadBaseSheet.tsx — Refs: US-002, FR-004 — Depends: T014, T015, T016
  - [x] **PREP**: RED de T014/T015 reconfirmado (`Failed to resolve import "@/features/bases/UploadBaseSheet"`). `$specsfy-specialist-reui` carregado. Lidos os limites do backend em `src/app/routers/bases.py` (`MAX_ARQUIVOS=50`, `MAX_BYTES_POR_ARQUIVO=5MB`, `MAX_BYTES_TOTAL=50MB`, extensão `.md`, UTF-8) e o contrato `Form(usar_base_preparada)`.
  - [x] **EXECUTE**: Instalado `shadcn add sheet` (Base UI `Dialog`). `frontend/src/features/bases/UploadBaseSheet.tsx` — `Sheet` contextual (`open`/`onOpenChange`), `<input type=file multiple accept=".md">` com rótulo "Arquivos Markdown", lista dos selecionados com "Remover", ação "Enviar" (`FormData` de `arquivos` → `POST /api/v1/bases`) e "Usar base preparada" (`URLSearchParams usar_base_preparada=true` — string, não `FormData`, para o backend ler via `Form`). `validar()` espelha os limites do backend e roda **antes** de qualquer chamada (nenhuma base parcial em envio inválido). Erro em `Alert role=alert`. Integrada ao `PageHeader` de `projeto/page.tsx` (ação "Enviar base" abre o Sheet; `onCreated` fecha e recarrega a listagem via contador `releituras`). `INTERFACE.md` atualizado (`Sheet`, `UploadBaseSheet`, tela Projeto).
  - [x] **VERIFY**: `cd frontend && npx vitest run src/features/bases/UploadBaseSheet.test.tsx` → **4 passed** (AC-006: múltiplos `.md` → `POST` em `/api/v1/bases` e `onCreated`; base preparada → corpo contém `usar_base_preparada`; AC-007: >50 arquivos → alerta `/50|limite/`, backend não chamado; extensão ≠ `.md` → alerta `/\.md/`, backend não chamado). Suíte `npx vitest run` → `4 failed | 5 passed` (RED de T023/T027/T031). `npx eslint` nos arquivos de T018 → exit 0 (page reescrita com `.then` chain + contador `releituras` para não disparar `react-hooks/set-state-in-effect`). `npx tsc --noEmit` → só imports de `*.test.tsx` de T023/T027/T031; produção limpa.
  - [x] **VISUAL**: Aferição por `next dev` + Playwright headless, viewports desktop 1280×800 e mobile 375×812 (screenshot `scratchpad/upload-*.png`), Sheet aberto pela ação "Enviar base". **bordas**: `Sheet` com `border-l`, backdrop `bg-black/10` + blur (primitive base-nova), `Alert` de erro com raio; **espaçamentos**: `gap-4` entre regiões do `SheetContent`, `gap-1.5` no grupo do campo, `gap-1` na lista de arquivos; **margens**: `Alert` com `mx-4` para alinhar ao corpo; footer sem margens próprias; **padding**: `SheetHeader`/`SheetFooter` `p-4`, corpo `px-4`; **tipografia**: título `text-base font-medium`, descrição `text-sm text-muted-foreground`, nomes de arquivo `font-mono text-xs`, rótulo `text-sm font-medium`. Larguras: `sm:max-w-md` (384px) no desktop, `w-3/4` (~281px) no mobile, sem overflow. Ações no rodapé à direita, primária ("Enviar") por último. Console sem erros. Resultado: conforme; o input de arquivo usa o chrome nativo do navegador (aceitável na demo; `@reui/c-file-upload` é o caminho para dropzone localizada).
  - [x] **EVIDENCE**: Comandos acima; arquivos `frontend/src/features/bases/UploadBaseSheet.tsx`, `frontend/src/app/(autenticado)/projeto/page.tsx`, `frontend/src/components/ui/sheet.tsx`, `INTERFACE.md`. `$specsfy-documentator --check` → exit 0; `monitor_context.mjs --check` → `CURRENT`. Matriz da seção 11: AC-006 e AC-007 marcados GREEN.
  - [x] **IMPROVE**: `criar()` unifica os dois caminhos de envio (upload e base preparada) — só o `body` (`FormData` vs `URLSearchParams`) e a mensagem de falha variam, sem duplicar o tratamento de `enviando`/erro/`onCreated`. Sem ajuste adicional.
  <!-- specsfy:evidence {"task":"T018","refs":["US-002","FR-004"],"files":["frontend/src/features/bases/UploadBaseSheet.tsx","frontend/src/app/(autenticado)/projeto/page.tsx","frontend/src/components/ui/sheet.tsx","INTERFACE.md"],"commands":[{"run":"cd frontend && npx vitest run src/features/bases/UploadBaseSheet.test.tsx","exit":0},{"run":"cd frontend && npx eslint ./src/features/bases/UploadBaseSheet.tsx","exit":0}]} -->


- [x] T019 [TEST] [TDD] [US-003] Derivar do AC-008 um caso Vitest falhando em frontend/src/features/execucoes/PainelProgresso.test.tsx — Refs: US-003, FR-005, FR-003, AC-008 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-008 e o contrato real de `GET /api/v1/executions/{id}` (SPEC-0012).
  - [x] **EXECUTE**: Criado `frontend/src/features/execucoes/PainelProgresso.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-003 FR-005 FR-003 AC-008 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/execucoes/PainelProgresso"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/execucoes/PainelProgresso`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T020 [TEST] [TDD] [US-003] Derivar do AC-009 um caso Vitest falhando em frontend/src/features/execucoes/PainelProgresso.test.tsx — Refs: US-003, FR-006, FR-005, AC-009 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-009 e o contrato de `POST /api/v1/executions/{id}/retry`.
  - [x] **EXECUTE**: Criado `frontend/src/features/execucoes/PainelProgresso.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-003 FR-006 FR-005 AC-009 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/execucoes/PainelProgresso"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/execucoes/PainelProgresso`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T021 [TEST] [TDD] [US-003] Derivar do AC-010 um caso Vitest falhando em frontend/src/features/execucoes/PainelProgresso.test.tsx — Refs: US-003, FR-006, AC-010 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-010 e o 409 de `has_active_execution` (SPEC-0012).
  - [x] **EXECUTE**: Criado `frontend/src/features/execucoes/PainelProgresso.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-003 FR-006 AC-010 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/execucoes/PainelProgresso"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/execucoes/PainelProgresso`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T022 [TEST] [TDD] [US-003] Derivar do AC-021 um caso Vitest falhando em frontend/src/features/execucoes/PainelProgresso.test.tsx — Refs: US-003, FR-006, AC-021 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-021.
  - [x] **EXECUTE**: Criado `frontend/src/features/execucoes/PainelProgresso.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-003 FR-006 AC-021 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/execucoes/PainelProgresso"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/execucoes/PainelProgresso`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T023 [CODE] [US-003] Implementar frontend/src/features/execucoes/PainelProgresso.tsx e frontend/src/app/(autenticado)/execucoes/[id]/page.tsx — Refs: US-003, FR-005, FR-006 — Depends: T019, T020, T021, T022
  - [x] **PREP**: RED de T019-T022 reconfirmado (`Failed to resolve import "@/features/execucoes/PainelProgresso"`). `$specsfy-specialist-reui` carregado. Seção 10 (tela Detalhe) relida: `PageHeader` + indicadores de contagem + etapas + consulta + chunks-fontes; "Repetir" para owner/admin; "Voltar ao projeto".
  - [x] **EXECUTE**: Instalado `shadcn add badge`. `frontend/src/features/execucoes/PainelProgresso.tsx` — props `execucao`, `papel?`, `onRepetida?`; mostra `Etapa`, `Badge` de situação (`variantePorSituacao`), grade de contagens previstos/inseridos/mantidos/removidos; "Repetir" só quando `situacao==="failed"` **e** `papel` ∈ {owner, admin} → `POST /executions/{id}/retry`; aviso `role=status` quando `pending`/`running`; erro seguro (`execucao.erro`) em `Alert`. `frontend/src/app/(autenticado)/execucoes/[id]/page.tsx` — `[id]` = id da base; `GET /api/v1/bases/{id}`, renderiza a execução mais recente + histórico, **polling** a cada 3 s enquanto ativa (via contador `releituras`), 404 → "Base não encontrada", "Voltar ao projeto" com `buttonVariants` + `next/link`. `frontend/src/lib/session.ts` — `getPapel()` deriva o papel do token estático (`token-demo-<papel>`, DEC-002; `outro-tenant`→owner) enquanto não há endpoint de identidade. `INTERFACE.md` atualizado (`Badge`, `PainelProgresso`, tela Detalhe).
  - [x] **VERIFY**: `cd frontend && npx vitest run src/features/execucoes/PainelProgresso.test.tsx` → **4 passed** (AC-008: etapa/situação/contagens visíveis; AC-009: "Repetir" de `failed`+owner → `POST …/retry`; AC-010: `running` mostra "execução ativa", sem "Repetir", sem chamada; AC-021: `succeeded` sem "Repetir"). Suíte `npx vitest run` → `3 failed | 6 passed` (RED de T027/T031). `npx eslint src/app src/features/execucoes` → exit 0. `npx tsc --noEmit` → só imports de `ExcluirBaseDialog`/`FormularioConsulta` (T027/T031); produção limpa.
  - [x] **VISUAL**: Aferição por `next dev` + Playwright headless, viewports desktop 1280×800 e mobile 375×812, estados failed+owner / succeeded / running+member (screenshots `scratchpad/execucao-*.png`), **console sem erros** (corrigido: link "Voltar" trocado de `Button render={<a>}` — que disparava aviso `nativeButton` do Base UI — para `next/link` + `buttonVariants`). **bordas**: card do painel e itens do histórico com `border` + `rounded-lg`/`rounded-md`; `Badge` `rounded-4xl`; `Alert` de erro com raio; **espaçamentos**: `gap-4` entre `PageHeader`/painel/histórico, `gap-3` na grade de contagens, `gap-2` no cabeçalho do painel e no histórico; **margens**: sem margens próprias — o `<main>` `p-4` do shell posiciona; contagens em `grid-cols-2 sm:grid-cols-4` sem sobra; **padding**: card `p-4`, itens do histórico `px-3 py-2`; **tipografia**: rótulos de contagem `text-xs text-muted-foreground`, valores `text-lg font-semibold tabular-nums`, "Etapa" `text-sm`, ids em `font-mono text-xs`. Repetir aparece só p/ `failed`+owner; ausente p/ member e p/ `succeeded`/`running`. Resultado: conforme.
  - [x] **EVIDENCE**: Comandos acima; arquivos `frontend/src/features/execucoes/PainelProgresso.tsx`, `frontend/src/app/(autenticado)/execucoes/[id]/page.tsx`, `frontend/src/lib/session.ts`, `frontend/src/components/ui/badge.tsx`, `INTERFACE.md`. `$specsfy-documentator --check` → exit 0; `monitor_context.mjs --check` → `CURRENT`. Matriz da seção 11: AC-008/AC-009/AC-010/AC-021 marcados GREEN.
  - [x] **IMPROVE**: Polling implementado com um contador de releituras que também serve à releitura pós-"Repetir" — um só caminho de atualização. `getPapel()` isola no `session.ts` a única suposição sobre papel a partir do token de demonstração, pronta para ser trocada por um endpoint de identidade real sem tocar nas telas.
  <!-- specsfy:evidence {"task":"T023","refs":["US-003","FR-005","FR-006"],"files":["frontend/src/features/execucoes/PainelProgresso.tsx","frontend/src/app/(autenticado)/execucoes/[id]/page.tsx","frontend/src/lib/session.ts","INTERFACE.md"],"commands":[{"run":"cd frontend && npx vitest run src/features/execucoes/PainelProgresso.test.tsx","exit":0},{"run":"cd frontend && npx eslint src/app src/features/execucoes","exit":0}]} -->


- [x] T024 [TEST] [TDD] [US-003] Derivar do AC-011 um caso Vitest falhando em frontend/src/features/bases/ExcluirBaseDialog.test.tsx — Refs: US-003, FR-007, AC-011 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-011 e o contrato de `DELETE /api/v1/bases/{id}` (SPEC-0012).
  - [x] **EXECUTE**: Criado `frontend/src/features/bases/ExcluirBaseDialog.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-003 FR-007 AC-011 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/bases/ExcluirBaseDialog"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/bases/ExcluirBaseDialog`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T025 [TEST] [TDD] [US-003] Derivar do AC-019 um caso Vitest falhando em frontend/src/features/bases/ExcluirBaseDialog.test.tsx — Refs: US-003, FR-007, AC-019 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-019.
  - [x] **EXECUTE**: Criado `frontend/src/features/bases/ExcluirBaseDialog.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-003 FR-007 AC-019 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/bases/ExcluirBaseDialog"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/bases/ExcluirBaseDialog`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T026 [TEST] [TDD] [US-003] Derivar do AC-020 um caso Vitest falhando em frontend/src/features/bases/ExcluirBaseDialog.test.tsx — Refs: US-003, FR-007, AC-020 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-020.
  - [x] **EXECUTE**: Criado `frontend/src/features/bases/ExcluirBaseDialog.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-003 FR-007 AC-020 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/bases/ExcluirBaseDialog"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/bases/ExcluirBaseDialog`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T027 [CODE] [US-003] Implementar frontend/src/features/bases/ExcluirBaseDialog.tsx — Refs: US-003, FR-007 — Depends: T024, T025, T026
  - [x] **PREP**: RED de T024-T026 reconfirmado (`Failed to resolve import "@/features/bases/ExcluirBaseDialog"`). `$specsfy-specialist-reui` carregado. Contrato: `role=dialog` com nome + consequência; "Apagar" → `DELETE /api/v1/bases/{id}` (204); ausente para member.
  - [x] **EXECUTE**: Instalado `shadcn add dialog` (Base UI). `frontend/src/features/bases/ExcluirBaseDialog.tsx` — props `open`, `onOpenChange?`, `base:{id,nome}`, `papel?`, `onDeleted(id)`; `DialogTitle` com o nome, `DialogDescription` com a consequência (execuções, consultas, vetores), "Cancelar" (outline) sempre e "Apagar" (`variant=destructive`) só para owner/admin → `apiFetch(DELETE)` + `onDeleted(id)` + fecha; erro em `Alert`. Integrado a **`DataGridBases`** (ação "Apagar" por linha na célula de ações, com `stopPropagation`; props novas `papel`/`onBaseApagada`) e à **tela Detalhe** (`execucoes/[id]/page.tsx`: ação "Apagar base" no `PageHeader` → `router.push("/projeto")` após excluir). `projeto/page.tsx` passa `papel={getPapel()}` e recarrega a listagem no `onBaseApagada`. `INTERFACE.md` atualizado (`Dialog`, `ExcluirBaseDialog`, `DataGridBases`).
  - [x] **VERIFY**: `cd frontend && npx vitest run src/features/bases/ExcluirBaseDialog.test.tsx` → **3 passed** (AC-011: dialog com nome + consequência, "Apagar" → `DELETE /api/v1/bases/base-1`, `onDeleted("base-1")`; AC-019: member não vê "Apagar"; AC-020: admin apaga → `onDeleted`). Suíte `npx vitest run` → `2 failed | 7 passed` (RED de T031). `npx eslint src/app src/features src/components src/lib` → exit 0. `npx tsc --noEmit` → só imports de `FormularioConsulta` (T031); produção limpa.
  - [x] **VISUAL**: Aferição por `next dev` + Playwright headless, viewport desktop 1280×800, papéis owner e member (screenshot `scratchpad/excluir-owner.png`), **console sem erros**. Owner: linha da grade mostra "Apagar" (ghost, `size=xs`) → abre `Dialog` centrado; member: sem "Apagar" na linha, sem dialog (AC-019). **bordas**: `DialogContent` com borda + `rounded-lg`, footer com `border-t`, backdrop escurece; **espaçamentos**: `gap` entre título/descrição/erro/footer do dialog, `gap-2` entre "Cancelar" e "Apagar"; **margens**: dialog centrado sem margem própria; **padding**: `DialogContent`/`Header`/`Footer` `p-*` do primitive; **tipografia**: título `text-base font-medium`, descrição `text-sm text-muted-foreground`; "Apagar" com cor semântica destrutiva (texto vermelho, fundo `destructive/10`), distinta de "Cancelar" (outline). Resultado: conforme.
  - [x] **EVIDENCE**: Comandos acima; arquivos `frontend/src/features/bases/ExcluirBaseDialog.tsx`, `frontend/src/features/bases/DataGridBases.tsx`, `frontend/src/app/(autenticado)/projeto/page.tsx`, `frontend/src/app/(autenticado)/execucoes/[id]/page.tsx`, `frontend/src/components/ui/dialog.tsx`, `INTERFACE.md`. `$specsfy-documentator --check` → exit 0; `monitor_context.mjs --check` → `CURRENT`. Matriz da seção 11: AC-011 (+ AC-019/AC-020) marcados GREEN.
  - [x] **IMPROVE**: O mesmo `ExcluirBaseDialog` serve à grade e ao detalhe por props — uma única confirmação, com `onDeleted` decidindo o efeito (recarregar a lista ou voltar ao projeto). A guarda por `papel` é dupla (esconde a ação **e** o backend responde 403), coerente com "sem permissão: a ação não aparece" da seção 10.
  <!-- specsfy:evidence {"task":"T027","refs":["US-003","FR-007"],"files":["frontend/src/features/bases/ExcluirBaseDialog.tsx","frontend/src/features/bases/DataGridBases.tsx","frontend/src/app/(autenticado)/execucoes/[id]/page.tsx","frontend/src/components/ui/dialog.tsx","INTERFACE.md"],"commands":[{"run":"cd frontend && npx vitest run src/features/bases/ExcluirBaseDialog.test.tsx","exit":0},{"run":"cd frontend && npx eslint src/app src/features src/components src/lib","exit":0}]} -->


- [x] T028 [TEST] [TDD] [US-004] Derivar do AC-012 um caso Vitest falhando em frontend/src/features/execucoes/FormularioConsulta.test.tsx — Refs: US-004, FR-008, AC-012 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-012 e o contrato real de `POST /api/v1/bases/{id}/query` (SPEC-0012).
  - [x] **EXECUTE**: Criado `frontend/src/features/execucoes/FormularioConsulta.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-004 FR-008 AC-012 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/execucoes/FormularioConsulta"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/execucoes/FormularioConsulta`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T029 [TEST] [TDD] [US-004] Derivar do AC-013 um caso Vitest falhando em frontend/src/features/execucoes/FormularioConsulta.test.tsx — Refs: US-004, FR-008, AC-013 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-013 e o 502 de `consultar_base` (SPEC-0012).
  - [x] **EXECUTE**: Criado `frontend/src/features/execucoes/FormularioConsulta.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-004 FR-008 AC-013 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/execucoes/FormularioConsulta"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste unitário, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/execucoes/FormularioConsulta`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T030 [TEST] [TDD] [US-003] Derivar do AC-018 um caso Vitest falhando em frontend/src/features/execucoes/FormularioConsulta.a11y.test.tsx — Refs: US-003, US-004, FR-005, FR-008, NFR-003, AC-018 — Depends: T001
  - [x] **PREP**: Ler o Gherkin do AC-018.
  - [x] **EXECUTE**: Criado `frontend/src/features/execucoes/FormularioConsulta.a11y.test.tsx` com o caso derivado do Gherkin, marcador `SPECSFY: US-003 US-004 FR-005 FR-008 NFR-003 AC-018 (SPEC-0013)`.
  - [x] **VERIFY**: RED observado (`cd frontend && npx vitest run`, vitest 5.0.0): `Failed to resolve import "@/features/execucoes/FormularioConsulta"` — produção ainda não existe. Suíte: `Test Files 9 failed (9)`.
  - [x] **VISUAL**: Não aplicável — teste automatizado, ainda sem componente renderizado.
  - [x] **EVIDENCE**: Comando `cd frontend && npx vitest run` → `Test Files 9 failed (9)`; causa deste caso: import não resolvido de `@/features/execucoes/FormularioConsulta`. Linha da matriz da seção 11 atualizada com o RED.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — o caso é tradução direta do Gherkin do AC, no menor nível (componente/módulo isolado com `fetch` e `next/navigation` simulados). Aprendizado consolidado no T011/T013+ ao implementar.

- [x] T031 [CODE] [US-004] Implementar frontend/src/features/execucoes/FormularioConsulta.tsx e frontend/src/features/execucoes/ChunksFontes.tsx — Refs: US-004, FR-008, NFR-003 — Depends: T028, T029, T030
  - [x] **PREP**: RED de T028-T030 reconfirmado (`Failed to resolve import "@/features/execucoes/FormularioConsulta"`). `$specsfy-specialist-reui` carregado. Seção 10 (formulário de consulta) relida: campo com rótulo visível, "Consultar", estado de carregamento, pergunta preservada em falha, chunks-fontes por documento de origem (não só cor).
  - [x] **EXECUTE**: `frontend/src/features/execucoes/ChunksFontes.tsx` — props `chunks: ChunkFonte[]`; cada item mostra "Fonte: {documento}" em texto + o trecho (AC-018); nada quando vazio. `frontend/src/features/execucoes/FormularioConsulta.tsx` — props `baseId`; `Label`+`Input` "Pergunta", "Consultar" → `apiJson(POST /api/v1/bases/{id}/query, JSON {pergunta})`; sucesso renderiza `resultado` + `ChunksFontes` numa região `role="status"`/`aria-live="polite"`; falha → `Alert role=alert` com mensagem segura (sem `provider`/`openai`/`qdrant`/`embedding`) e pergunta preservada (campo controlado); botão desabilitado sem pergunta. Integrado a `execucoes/[id]/page.tsx` (aparece quando há execução `succeeded`). `INTERFACE.md` atualizado (`ChunksFontes`, `FormularioConsulta`, tela Detalhe).
  - [x] **VERIFY**: **Ajuste de teste** (correção interna): `FormularioConsulta.test.tsx` AC-012 usava `findByText(/500 Mbps/)`, ambíguo porque o `trecho` do chunk também contém "500 Mbps" — trocado por `findByText("O plano Turbo tem 500 Mbps.")` (string exata do resultado), preservando a intenção da AC. `cd frontend && npx vitest run` → **9 arquivos, 20 testes, todos passam** (GREEN de T028: resultado + chunks-fontes por documento; T029: falha segura + pergunta preservada; T030 a11y: rótulo associado, `role=status` com o resultado, `doc.md` por texto). `npx eslint src/app src/features src/components src/lib` → exit 0. `npx tsc --noEmit` → **TUDO LIMPO** (todos os componentes existem). `npx next build` → **sucesso** (rotas `/`, `/login`, `/projeto`, `/execucoes/[id]`).
  - [x] **VISUAL**: Aferição por `next dev` + Playwright headless, viewports desktop 1280×800 e mobile 375×812, estados carregando/sucesso/falha (screenshots `scratchpad/consulta-*.png`). **bordas**: card "Consultar a base" e cards de chunk com `border`+`rounded-lg`/`rounded-md`; `Input` borda + raio; foco com anel; **espaçamentos**: `gap-3` na seção, `gap-2` no form e entre os chunks; campo e botão lado a lado no desktop (`sm:flex-row`), empilhados no mobile; **margens**: `mt-1` entre "Fonte:" e o trecho; sem margens próprias na seção; **padding**: card `p-4`, cards de chunk `p-3`, `Input` `px-2.5 py-1`; **tipografia**: rótulo/heading `text-sm font-medium`, resultado `text-sm`, "Fonte:" `font-mono text-xs text-muted-foreground`. Falha: `Alert` genérico ("Não foi possível consultar a base agora…"), pergunta mantida no campo; console só registra o 502 mockado (esperado), sem erro de JS. Resultado: conforme.
  - [x] **EVIDENCE**: Comandos acima; arquivos `frontend/src/features/execucoes/FormularioConsulta.tsx`, `frontend/src/features/execucoes/ChunksFontes.tsx`, `frontend/src/features/execucoes/FormularioConsulta.test.tsx` (ajuste de assert), `frontend/src/app/(autenticado)/execucoes/[id]/page.tsx`, `INTERFACE.md`. `$specsfy-documentator --check` → exit 0; `monitor_context.mjs --check` → `CURRENT`. Matriz da seção 11: AC-012/AC-013/AC-018 marcados GREEN. Suíte de frontend completa verde e `next build` ok — todas as telas da SPEC-0013 entregues.
  - [x] **IMPROVE**: A região `role="status"`/`aria-live` concentra carregamento e resultado num só ponto de anúncio — o leitor de tela recebe "Consultando a base…" e depois o resultado sem foco forçado. `ChunksFontes` separado mantém `FormularioConsulta` focado no envio; ambos reaproveitáveis por outra tela de consulta futura.
  <!-- specsfy:evidence {"task":"T031","refs":["US-004","FR-008","NFR-003"],"files":["frontend/src/features/execucoes/FormularioConsulta.tsx","frontend/src/features/execucoes/ChunksFontes.tsx","frontend/src/app/(autenticado)/execucoes/[id]/page.tsx","INTERFACE.md"],"commands":[{"run":"cd frontend && npx vitest run","exit":0},{"run":"cd frontend && npx tsc --noEmit","exit":0},{"run":"cd frontend && npx next build","exit":0}]} -->


#### Fase final — Documentação, CI e regressão

- [x] T032 [DOC] Atualizar .specsfy/STACK.md com Next.js, React, TypeScript, Tailwind CSS, shadcn/ui, ReUI e Vitest reais em .specsfy/STACK.md — Refs: US-001 — Depends: T013, T017, T018, T023, T027, T031
  - [x] **PREP**: Lido o inventário de `.specsfy/STACK.md` (nota "Next.js… continuam como direção futura") e o resultado das 6 tarefas de interface. `$specsfy-aux-stack` carregado; `update_stack.mjs` só lê manifests da raiz e não inventaria `frontend/package.json`.
  - [x] **EXECUTE**: Nota de direção futura reescrita (Next.js/React/TypeScript/Tailwind/shadcn/Vitest passam a "implementados em `frontend/`"; só LangGraph/IA agentic seguem futuros). Nova seção "Stack de frontend (`frontend/`)" com tabela curada manualmente: framework/roteamento, React, TypeScript, Tailwind v4, primitives shadcn (`base-nova`/Base UI), registry ReUI, ícones, cliente HTTP, testes Vitest, ESLint, CSP — cada linha cita arquivo real. `update_stack.mjs` acrescentou a linha genérica "Infraestrutura | Containers" ao bloco gerenciado.
  - [x] **VERIFY**: Cada linha nova cita um arquivo do repositório (`frontend/package.json`, `frontend/tsconfig.json`, `frontend/components.json`, `frontend/src/…`, `frontend/next.config.ts`, `.github/workflows/ci.yml`). `monitor_context.mjs --check` → `CURRENT`.
  - [x] **VISUAL**: Não aplicável — documento de contexto, sem interface.
  - [x] **EVIDENCE**: `git diff .specsfy/STACK.md` — nota de direção futura substituída, seção "Stack de frontend (`frontend/`)" adicionada (12 linhas de tabela + 2 notas), linha "Infraestrutura | Containers" pelo scanner.
  - [x] **IMPROVE**: Nenhum ajuste necessário — a curadoria manual segue a mesma exceção já registrada para `.specsfy/DATABASE.md` em `.specsfy/RULES.md`.

- [x] T033 [DOC] Atualizar .specsfy/DATABASE.md com a coluna Base.documentos em .specsfy/DATABASE.md — Refs: FR-002 — Depends: T006
  - [x] **PREP**: Lida a regra de `.specsfy/RULES.md` (o scanner de `$specsfy-aux-database` não reconhece SQLAlchemy neste componente Python — editar `.specsfy/DATABASE.md` manualmente).
  - [x] **EXECUTE**: Linha da "Tabela `bases`" atualizada com `documentos` (Integer, `NOT NULL`, `server_default 0` — contagem de arquivos recebidos na criação; revisão Alembic `f3b60ce4f7f4`). Notas acrescentadas: cadeia de revisões `074d455d6f67 → f3b60ce4f7f4`, como o schema de teste é materializado (`metadata.create_all`), e onde `documentos` é preenchida (`enviar_base`) e lida (`GET /api/v1/bases`, `GET /api/v1/bases/{id}`).
  - [x] **VERIFY**: O registro corresponde à migration de T006 (`alembic/versions/f3b60ce4f7f4_add_documentos_to_bases.py`: `op.add_column("bases", sa.Column("documentos", sa.Integer(), nullable=False, server_default="0"))`) e ao model `src/app/models.py::Base.documentos`.
  - [x] **VISUAL**: Não aplicável — documento de contexto, sem interface.
  - [x] **EVIDENCE**: `git diff .specsfy/DATABASE.md` — linha da tabela `bases` com `documentos`; duas notas sobre revisões Alembic e preenchimento/leitura da coluna.
  - [x] **IMPROVE**: Nenhum ajuste necessário — edição manual conforme a regra do projeto.

- [x] T034 [DOC] Atualizar docs/frontend.md e revisar PROJECT.md com a capacidade de frontend entregue em docs/frontend.md — Refs: US-001, US-002, US-003, US-004 — Depends: T013, T017, T018, T023, T027, T031
  - [x] **PREP**: `$specsfy-documentator` executado após cada tarefa de interface; `docs/frontend.md` reconstruído a partir do frontend real (rotas, componentes, testes Vitest).
  - [x] **EXECUTE**: `docs/frontend.md` reconstruído pelo documentator (deixou de dizer "0 superfícies observadas"). `PROJECT.md` revisado: "Pessoas e contexto de uso" registra o frontend `frontend/` e a jornada de ponta a ponta; "Capacidades principais" ganha o item "demonstrar a fatia funcional por um frontend web" (login, listagem com `documentos`/`status`/`chunks`, upload, detalhe com progresso e polling, repetir, apagar com confirmação, consulta com chunks-fontes); "Limites" atualizado (fatia 3 entregue; roda localmente, deploy fora de escopo).
  - [x] **VERIFY**: `node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check` → exit 0. `monitor_context.mjs --check` → `CURRENT`.
  - [x] **VISUAL**: Não aplicável — documento, sem interface própria.
  - [x] **EVIDENCE**: `build_documentation.mjs --project . --check` → exit 0; `git diff PROJECT.md docs/frontend.md` (capacidade de frontend registrada, projeção reconstruída).
  - [x] **IMPROVE**: Nenhum ajuste necessário — `docs/` é projeção reconstruível; conteúdo humano de `PROJECT.md` preservado fora dos blocos gerenciados.

- [x] T035 [OPS] Adicionar job de CI para o frontend em .github/workflows/ci.yml — Refs: FR-004 — Depends: T001, T013, T017, T018, T023, T027, T031
  - [x] **PREP**: Lido o job `quality` (Ruff + Pytest, `astral-sh/setup-uv`, SHAs pinados) e a resolução de FIND-ARCH-001 ("job de CI dedicado ao frontend").
  - [x] **EXECUTE**: Job `frontend` adicionado a `.github/workflows/ci.yml`, separado do job Python, com `defaults.run.working-directory: frontend`: `actions/setup-node` (Node 24, cache npm em `frontend/package-lock.json`), `npm ci`, `npm run lint`, `npm run typecheck`, `npm run test:tdd`, `npm run build`. SHA de `actions/setup-node@v4.4.0` (`49933ea5…`) confirmado via `gh api repos/actions/setup-node/git/refs/tags/v4.4.0`, seguindo a convenção de SHAs pinados do workflow.
  - [x] **VERIFY**: Sintaxe YAML revisada manualmente (indentação, `jobs.frontend`, `steps`). `npm ci` reproduzível: `npm ci` local a partir do lockfile → OK; `npm run lint` → exit 0, `npm run typecheck` → exit 0, `npm run test:tdd` → 9 arquivos/20 testes, `npm run build` → sucesso. `package.json`/`package-lock.json` sem `@tanstack` (instalação de `@reui/data-grid` foi revertida).
  - [x] **VISUAL**: Não aplicável — configuração de CI, sem interface.
  - [x] **EVIDENCE**: `git diff .github/workflows/ci.yml` — job `frontend` (7 steps) acrescentado após o job `quality`, sem tocá-lo.
  - [x] **IMPROVE**: Nenhum ajuste necessário — o job roda a cada push/PR como o job Python; `working-directory` isola o tooling Node do `uv`.

- [x] T036 [TEST] Executar regressão completa e rastreabilidade em tests/ e frontend/src — Refs: US-001, US-002, US-003, US-004 — Depends: T032, T033, T034, T035
  - [x] **PREP**: Suítes: Pytest (`tests/`), Vitest (`frontend/src/**`, `test:tdd`). Checks estáticos: `uv run ruff check .`, `npm run lint`, `npm run typecheck`, `npm run build`.
  - [x] **EXECUTE**: `check_database_safety.mjs` → `SAFE`. `uv run pytest -q` → **292 passed** (após ajustar o vocabulário do corpo da spec à guarda `tests/test_spec_markers.py` / `.specsfy/RULES.md`). `uv run ruff check .` → `All checks passed!`. Em `frontend/`: `npm run lint` → exit 0, `npm run typecheck` → exit 0, `npm run test:tdd` → **9 arquivos, 20 testes**, `npm run build` → sucesso (`/`, `/login`, `/projeto`, `/execucoes/[id]`).
  - [x] **VERIFY**: `verify_acceptance.mjs` → **QA: PASSED** (após incluir AC-021 na linha FR-006 da seção 12; todos os 21 `AC` da seção 6 com evidência `Passed`). `verify_evidence.mjs` (todas as tarefas) → **PASSED (strict)**; `--task T006` (migration) → PASSED. `check_traceability.mjs` → 36/36 IDs da SPEC-0013 cobertos; verdict `GAPS` decorre apenas de sete marcadores `SPECSFY:` órfãos de SPEC-0012 e specs anteriores, sem correspondência nesta spec, em arquivos `tests/` compartilhados — a ferramenta varre `tests/` sem filtrar por spec (limitação registrada na seção 13, sem gap nesta spec). `build_documentation.mjs --check` → exit 0; `monitor_context.mjs --check` → `CURRENT`.
  - [x] **VISUAL**: Conferência visual final das telas por `next dev` + Playwright headless (chromium), desktop 1280×800 e mobile 375×812, screenshots em `scratchpad/`: Login (inicial/erro), Projeto (carregando/vazio/lista + guarda de sessão), Detalhe (failed+owner/succeeded/running+member, "Repetir"/"Apagar base" por papel), Exclusão (`Dialog` owner vs member), Consulta (sucesso com chunks-fontes / falha segura). Bordas, espaçamentos, margens, padding e tipografia conferidos contra o scaffold Base UI e `DESIGNSYSTEM.MD` em cada tarefa de interface (T013/T017/T018/T023/T027/T031) e nesta passagem final: consistentes, sem overflow horizontal, foco visível, ações por papel. Console sem erros de JS (só o 502 mockado do teste de falha da consulta).
  - [x] **EVIDENCE**: Contagens e comandos acima; seções 11 e 12 com GREEN/`Passed` por AC; seção 13 (Gate do Ato III) atualizada.
  - [x] **IMPROVE**: Retrospectiva da fatia — (1) o plano precisou de replanejamento no Ato II: a tag `[MIGRATION]` foi removida (validador atual não a aceita) e T014-T016 tiveram a dependência de T007 reduzida a T001, porque o RED de frontend roda contra o contrato da seção 10 com cliente HTTP simulado; (2) `@reui/c-data-grid` (TanStack, ~2500 linhas) foi avaliado e preterido por uma tabela semântica que atende o contrato de CRUD com menos superfície — registrado em `INTERFACE.md` como caminho de migração; (3) a guarda de vocabulário de `.specsfy/RULES.md` reprovou a regressão até os itens `VISUAL` serem reescritos (o rótulo "Aferição por" substituiu um termo com a subcadeia proibida). Nenhuma mudança de comportamento; correções internas registradas nas tarefas.

### 15. Ordem de execução

- Caminho crítico: T001 (scaffold) → T002-T005 (RED backend) → T006
  (migration) → T007 (endpoints) → T008-T010 (RED sessão) → T011
  (sessão/cliente) → T012 (RED acessibilidade Login) → T013 (Login) → T014-T016
  (RED Projeto) → T017-T018 (Projeto) → T019-T022 (RED Detalhe) → T023
  (Detalhe) → T024-T026 (RED exclusão) → T027 (exclusão) → T028-T030 (RED
  consulta) → T031 (consulta) → T032-T035 (documentação/CI) → T036
  (regressão).
- Materialização do RED (Ato II): todos os 22 predecessores `[TEST] [TDD]`
  (T002-T005 backend; T008-T010, T012, T014-T016, T019-T022, T024-T026,
  T028-T030 frontend) são derivados do BDD e observam RED antes de promover o
  Plan Gate. Os testes de frontend usam o cliente HTTP simulado e o contrato
  da seção 10, então dependem apenas de T001 (scaffold) — nenhum exige o
  endpoint real (T007). O caminho crítico acima é a ordem de implementação do
  Ato III, executada depois do Plan Gate.
- Tarefas paralelas: T001 é `[P]` e pode começar junto de T002-T005 (RED
  backend), já que scaffold do frontend e testes Pytest não compartilham
  arquivo. T013 (Login) pode avançar em paralelo a T014-T018 (Projeto) depois
  que T011 (sessão/cliente) estiver pronto, pois não dependem uma da outra.
- Estratégia de MVP: US-001 (Login) + US-002 (listar/enviar) já demonstram
  o núcleo de entrada; US-003 (acompanhar/repetir/apagar) fecha o ciclo
  operacional; US-004 (consulta) fecha o cenário de valor completo do
  BACKLOG-0008.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0012 (`Complete`): backend, modelos e autenticação já entregues.
- BACKLOG-0008 (fatia 3, refinado em 2026-09-05): brief e decisões de
  escopo desta spec.
- Especialistas instalados nesta sessão: `specsfy-specialist-nextjs`,
  `-react`, `-react-ui-components`, `-typescript`, `-tailwind-css`, `-reui`,
  `-shadcn-ui`, `-ux-design`, `-ui-design`, `-interface-experience`.

#### Riscos

- Bases criadas antes da migration ficam com `documentos = 0` até serem
  reprocessadas → mitigação: aceitável em ambiente de demonstração sem dado
  de produção; registrar no changelog da migration.
- Introduzir um segundo gerenciador de dependências (Node, ao lado de `uv`)
  no mesmo repositório → mitigação: `frontend/` autocontido (DEC-001),
  workflow de CI do frontend separado do workflow Python existente
  (`.github/workflows/ci.yml`), sem misturar os dois.
- Polling client-side do estado da execução pode gerar carga desnecessária
  em uma demonstração longa → mitigação: intervalo de polling configurável,
  parado automaticamente quando a situação sair de `pending`/`running`.
- O token fica em `sessionStorage`, acessível a qualquer script executado na
  página; esta é a primeira superfície web deste repositório, então não há
  mitigação de XSS herdada de uma tela anterior (FIND-SEC-001) → mitigação:
  cabeçalho `Content-Security-Policy` básico via `next.config` restringindo
  origens de script ao próprio domínio (DEC-004), registrado como tarefa do
  scaffold (seção 14, passo 3); o risco residual é aceito porque o token
  continua sendo de demonstração, sem valor fora deste ambiente (mesma
  aceitação já registrada pela SPEC-0012, DEC-002).

#### Suposições

- O ambiente de demonstração roda localmente (`next dev` + backend FastAPI
  local); deploy/hospedagem fica fora desta spec (ver Fora de escopo).
- O token de demonstração continua sendo o mecanismo de autenticação
  enquanto não houver uma spec de autenticação real — default reversível,
  já assumido pela SPEC-0012 (DEC-002 daquela spec).

### 17. Decisões

- **DEC-001**: o frontend vive em `frontend/`, projeto Node autocontido
  neste mesmo repositório, em vez de um monorepo com workspaces
  compartilhados ou um repositório separado — evita acoplar o tooling
  Python (`uv`) ao Node antes de existir necessidade real de compartilhar
  código entre eles, e mantém a decisão já tomada no backlog ("tudo neste
  repositório") sem forçar um build unificado.
- **DEC-002**: a contagem de "documentos" por base é uma coluna persistida
  (`Base.documentos`, preenchida na criação), em vez de calculada por
  listagem do storage a cada leitura — porque `Storage` (`src/app/storage.py`)
  não expõe uma função de listagem, e adicionar uma só para essa contagem
  criaria uma dependência de storage no caminho de leitura que hoje não
  existe.
- **DEC-003**: a tela de Login usa campo de texto livre para o token, sem
  seletor de papéis pré-definidos — decisão herdada do refinamento do
  backlog (2026-09-05): evita acoplar o frontend à lista fixa de tokens de
  `src/app/main.py`.
- **DEC-004**: o scaffold do Next.js inclui um cabeçalho
  `Content-Security-Policy` básico (script-src limitado à própria origem),
  em vez de nenhuma política — mitigação mínima de XSS para a primeira
  superfície web do repositório, já que ela guarda um token em
  `sessionStorage` (FIND-SEC-001). Não substitui uma revisão de segurança
  completa do frontend, fora do escopo desta fatia de demonstração.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam (`verify_acceptance.mjs` → QA: PASSED; 21/21 `AC` da seção 6).
- [x] Todos os requisitos possuem evidência de verificação (seção 12, coluna Evidência = `Passed`).
- [x] Todas as tarefas na seção 14 estão concluídas (36/36).
- [x] Testes e checks estáticos disponíveis passam (`uv run pytest` → 292 passed; `uv run ruff check .` → OK; `frontend`: Vitest 20 passed, `typecheck`/`lint` exit 0, `next build` sucesso).
