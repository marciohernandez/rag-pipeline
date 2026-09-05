# Especificação integrada: Frontend demonstrável do backend de aplicação

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0013 |
| Slug | 0013-frontend-demonstravel-do-backend-de-aplicacao |
| Status | Implementing |
| Effort | 7 |
| Effort updated at | 2026-09-05 |
| Effort rationale | Introduz uma stack nova neste repositório (Next.js/React/TypeScript/Tailwind), quatro telas com estados assíncronos, dois endpoints novos de leitura no backend e uma sessão de autenticação por token no cliente; perfil `high`. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | In Progress |
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
| US-001, FR-001, NFR-002, AC-001 | AC-001 | `frontend/src/features/auth/LoginForm.test.tsx` — login válido guarda sessão | import não resolvido de `@/features/auth/LoginForm` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-001, FR-001, NFR-002, AC-002 | AC-002 | `LoginForm.test.tsx` — token inválido não guarda sessão | import não resolvido de `@/features/auth/LoginForm` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-001, FR-001, NFR-002, AC-003 | AC-003 | `api-client.test.ts` — 401 limpa sessão e redireciona | import não resolvido de `@/lib/api-client` (produção ausente) | Passed (T011): `npx vitest run src/lib/api-client.test.ts` → 2 passed | Pending |
| US-002, FR-002, NFR-001, AC-004 | AC-004 | `tests/test_app_bases.py::test_lista_bases_por_tenant_ordenada` | `TypeError: 'documentos' is an invalid keyword argument for Base` | Passed (T006→T007): `34 passed` — lista ordenada por última atualização, `documentos`/`status`/`chunks` corretos | Passed |
| US-002, FR-003, AC-005 | AC-005 | `tests/test_app_bases.py::test_detalhe_base_com_historico_execucoes` | `TypeError: 'documentos' is an invalid keyword argument for Base` | Passed (T007): `execucoes` da mais recente à mais antiga | Passed |
| US-002, FR-004, AC-006 | AC-006 | `UploadBaseSheet.test.tsx` — envio de .md e base preparada | import não resolvido de `@/features/bases/UploadBaseSheet` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-002, FR-004, AC-007 | AC-007 | `UploadBaseSheet.test.tsx` — limites rejeitados antes de chamar o backend | import não resolvido de `@/features/bases/UploadBaseSheet` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-003, FR-005, FR-003, AC-008 | AC-008 | `PainelProgresso.test.tsx` — progresso até succeeded | import não resolvido de `@/features/execucoes/PainelProgresso` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-003, FR-006, FR-005, AC-009 | AC-009 | `PainelProgresso.test.tsx` — repetir após failed | import não resolvido de `@/features/execucoes/PainelProgresso` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-003, FR-006, AC-010 | AC-010 | `PainelProgresso.test.tsx` — recusa repetição com execução ativa | import não resolvido de `@/features/execucoes/PainelProgresso` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-003, FR-007, AC-011, AC-019, AC-020 | AC-011 | `ExcluirBaseDialog.test.tsx` — apagar com confirmação; ação ausente para member (AC-019); pai notificado (AC-020) | import não resolvido de `@/features/bases/ExcluirBaseDialog` (produção ausente) — `cd frontend && npx vitest run` |
| US-003, FR-006, AC-021 | AC-021 | `PainelProgresso.test.tsx` — Repetir ausente fora de failed | import não resolvido de `@/features/execucoes/PainelProgresso` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-004, FR-008, AC-012 | AC-012 | `FormularioConsulta.test.tsx` — consulta com sucesso mostra chunks-fontes | import não resolvido de `@/features/execucoes/FormularioConsulta` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-004, FR-008, AC-013 | AC-013 | `FormularioConsulta.test.tsx` — falha preserva a pergunta | import não resolvido de `@/features/execucoes/FormularioConsulta` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-002, FR-002, FR-003, NFR-001, AC-014 | AC-014 | `tests/test_app_bases.py::test_listagem_e_detalhe_isolam_por_tenant` | `TypeError: 'documentos' is an invalid keyword argument for Base` | Passed (T007): listagem e detalhe isolam por tenant (404 cruzado) | Passed |
| US-004, FR-008, NFR-001, AC-015 | AC-015 | `tests/test_app_queries.py::test_consulta_isola_por_tenant` | Não aplicável — GREEN preexistente (ver Achados) | Passed (imediato) | Passed |
| US-001, NFR-003, AC-016 | AC-016 | `LoginForm.a11y.test.tsx` — navegação e anúncio por teclado | import não resolvido de `@/features/auth/LoginForm` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-002, NFR-003, AC-017 | AC-017 | `DataGridBases.a11y.test.tsx` — DataGrid e Sheet por teclado | import não resolvido de `@/features/bases/DataGridBases` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |
| US-003, US-004, NFR-003, AC-018 | AC-018 | `FormularioConsulta.a11y.test.tsx` — rótulos e anúncio de resultado | import não resolvido de `@/features/execucoes/FormularioConsulta` (produção ausente) — `cd frontend && npx vitest run` | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001, AC-002, AC-003 | Unidade/integração (Vitest) | `frontend/src/features/auth/*.test.tsx`, `frontend/src/lib/api-client.test.ts` | Pending |
| FR-002 | AC-004, AC-014 | Integração (Pytest, PostgreSQL de teste) | `tests/test_app_bases.py` | Passed (T007, `34 passed`) |
| FR-003 | AC-005, AC-008, AC-014 | Integração (Pytest) | `tests/test_app_bases.py` | Parcial: AC-005/AC-014 Passed (T007); AC-008 no frontend (T019/T023) |
| FR-004 | AC-006, AC-007 | Unidade/integração (Vitest) | `frontend/src/features/bases/*.test.tsx` | Pending |
| FR-005 | AC-008, AC-009 | Unidade (Vitest) | `frontend/src/features/execucoes/PainelProgresso.test.tsx` | Pending |
| FR-006 | AC-009, AC-010 | Unidade (Vitest) | `frontend/src/features/execucoes/PainelProgresso.test.tsx` | Pending |
| FR-007 | AC-011 | Unidade (Vitest) | `frontend/src/features/execucoes/PainelProgresso.test.tsx` | Pending |
| FR-008 | AC-012, AC-013, AC-015 | Unidade/integração (Vitest + Pytest) | `frontend/src/features/execucoes/FormularioConsulta.test.tsx`, `tests/test_app_queries.py` | Pending |
| NFR-001 | AC-014, AC-015 | Integração (Pytest) | `tests/test_app_bases.py`, `tests/test_app_queries.py` | Passed (T007/T005): isolamento por tenant em listagem, detalhe e consulta |
| NFR-002 | AC-001, AC-002, AC-003 | Unidade (Vitest) | `frontend/src/lib/session.test.ts` | Pending |
| NFR-003 | AC-016, AC-017, AC-018 | E2E/acessibilidade (Vitest + Testing Library + axe) | `frontend/src/**/*.a11y.test.tsx` | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed (2026-09-05)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md`
- **Achados** (revisão semântica PROD/ARCH/SEC, 2026-09-05):
- **FIND-ARCH-001** [P2] [Resolved] CI existente só roda Ruff/Pytest e não cobriria uma regressão em frontend/ — Refs: FR-004 — Evidence: .github/workflows/ci.yml — Effect: regressão do frontend passaria sem detecção automática — Suggestion: job de CI dedicado ao frontend, resolvido pela tarefa 10 da seção 14
- **FIND-SEC-001** [P2] [Resolved] Token de sessão em sessionStorage, acessível a script na página, sem mitigação de XSS na primeira superfície web do repositório — Refs: NFR-002 — Evidence: specs/draft/0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md#10-interfaces-e-contratos — Effect: um script injetado poderia ler o token — Suggestion: cabeçalho Content-Security-Policy básico no scaffold, resolvido por DEC-004 e risco aceito na seção 16
- Nenhum achado `P1`; nenhum bloqueio ao Definition Gate.

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-09-05, após replanejamento e materialização de todo o RED)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md`
- **Achados** (2026-09-05, replanejamento): 36 tarefas (22 `[TEST][TDD]`, 9 `[CODE]`, 3 `[DOC]`, 2 `[OPS]`), cobertura de IDs 36/36. `validate_interface_tasks.mjs`: `OK` (3 telas, Fase de interface, `INTERFACE.md` citado). `verify_evidence.mjs`: `PASSED (strict)`. Os 22 predecessores `[TEST] [TDD]` estão concluídos com RED observado (T002–T005 backend: `TypeError`/GREEN preexistente; T008–T030 frontend: `Failed to resolve import` do módulo de produção ausente, `cd frontend && npx vitest run` → `Test Files 9 failed (9)`), registrados na matriz da seção 11.
  - **Rastreabilidade**: `check_traceability.mjs` reporta 36/36 IDs da SPEC-0013 cobertos (43 arquivos de teste). O verdict `GAPS` decorre apenas de marcadores órfãos (`AC-022`–`AC-025`, `FR-009`, `NFR-004`, `US-005`) de SPEC-0012 e anteriores em arquivos `tests/` compartilhados; a ferramenta varre `tests/` inteiro sem filtrar por spec. Nenhum ID desta spec fica sem caso TDD.
  - **Correção de T006**: a versão atual do `validate_tasks.mjs` não reconhece mais a tag `[MIGRATION]` (conjunto permitido: `P, TEST, TDD, CODE, DOC, OPS, US-NNN`) e a rejeitava com `possui tags inválidas: MIGRATION` → `NOT READY`. A tag foi removida; T006 permanece `[CODE]` e a disciplina de migration é preservada pelo caminho `alembic/versions/<revisão>_add_documentos_to_bases.py`, pelos dois comandos no item `VERIFY` (aplicar no banco de teste + `alembic current`) e pelo comentário `specsfy:evidence` (Evidence Contract 1). A regra de `.specsfy/RULES.md` sobre o falso negativo do `MIGRATION_PATH` ficou obsoleta e será atualizada por `$specsfy-aux-rules`.
  - **Correção de dependências**: T014, T015 e T016 (RED de frontend com cliente HTTP simulado, conforme a seção 11) dependiam de T007 (`[CODE]` backend). Como o RED é observado contra o contrato da seção 10 e não contra o endpoint implementado, a dependência foi reduzida para `T001`. Assim, os 22 predecessores TDD podem ser materializados no Ato II antes do Plan Gate; o caminho crítico da seção 15 descreve a ordem de implementação do Ato III.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md .`
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

- [ ] T013 [CODE] [US-001] Implementar frontend/src/features/auth/LoginForm.tsx e frontend/src/app/login/page.tsx — Refs: US-001, FR-001, NFR-002, NFR-003 — Depends: T008, T009, T012, T011
  - [ ] **PREP**: Confirmar RED de T008, T009, T012; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX/TSX; reler a seção 10 (Login).
  - [ ] **EXECUTE**: Implementar `LoginForm` (shadcn/ui `Form`, `Input` tipo password, `Button`, `Alert`) e a rota `/login`; registrar o bloco em `INTERFACE.md`.
  - [ ] **VERIFY**: Rodar `npm run test:tdd` e confirmar GREEN de T008, T009, T012; navegar manualmente por teclado.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do campo, botão e alerta de erro conforme `DESIGNSYSTEM.MD`, nos estados vazio/erro/carregando, em desktop e mobile.
  - [ ] **EVIDENCE**: Registrar comando, GREEN e arquivos alterados; registrar o bloco em `INTERFACE.md`.
  - [ ] **IMPROVE**: Registrar ajuste de acessibilidade aplicado ou ausência justificada.

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

- [ ] T017 [CODE] [US-002] Implementar frontend/src/features/bases/DataGridBases.tsx e frontend/src/app/(autenticado)/projeto/page.tsx — Refs: US-002, FR-002, FR-003, NFR-001, NFR-003 — Depends: T002, T004, T016, T007
  - [ ] **PREP**: Confirmar GREEN de T002, T004 (backend) e RED de T016; carregar `$specsfy-specialist-react-ui-components`; reler a seção 10 (tela Projeto).
  - [ ] **EXECUTE**: Implementar `DataGridBases` (ReUI `Data Grid`, coluna ID, linha clicável, `TableRowAction`), `PageHeader` e a rota `/projeto`, consumindo `GET /api/v1/bases`; registrar em `INTERFACE.md`.
  - [ ] **VERIFY**: Rodar `npm run test:tdd` e confirmar GREEN de T016; navegar manualmente por teclado.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do DataGrid, PageHeader e Badge de status, nos estados vazio/carregando/sucesso, em desktop e mobile.
  - [ ] **EVIDENCE**: Registrar comando, GREEN e arquivos alterados; registrar o bloco em `INTERFACE.md`.
  - [ ] **IMPROVE**: Registrar ajuste aplicado ou ausência justificada.

- [ ] T018 [CODE] [US-002] Implementar frontend/src/features/bases/UploadBaseSheet.tsx — Refs: US-002, FR-004 — Depends: T014, T015, T016
  - [ ] **PREP**: Confirmar RED de T014, T015; carregar `$specsfy-specialist-react-ui-components`.
  - [ ] **EXECUTE**: Implementar `UploadBaseSheet` (ReUI `File Upload` em `Sheet`), integrada ao `DataGridBases` de T017; registrar em `INTERFACE.md`.
  - [ ] **VERIFY**: Rodar `npm run test:tdd` e confirmar GREEN de T014, T015.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do Sheet e da lista de arquivos, nos estados vazio/erro/sucesso, em desktop e mobile.
  - [ ] **EVIDENCE**: Registrar comando, GREEN e arquivos alterados; registrar o bloco em `INTERFACE.md`.
  - [ ] **IMPROVE**: Registrar ajuste aplicado ou ausência justificada.

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

- [ ] T023 [CODE] [US-003] Implementar frontend/src/features/execucoes/PainelProgresso.tsx e frontend/src/app/(autenticado)/execucoes/[id]/page.tsx — Refs: US-003, FR-005, FR-006 — Depends: T019, T020, T021, T022
  - [ ] **PREP**: Confirmar RED de T019-T022; carregar `$specsfy-specialist-react-ui-components`; reler a seção 10 (tela Detalhe).
  - [ ] **EXECUTE**: Implementar `PainelProgresso` (ReUI `Timeline`, `Badge`), `PageHeader` reconfigurado e a rota `/execucoes/[id]`, com polling enquanto pending/running; registrar em `INTERFACE.md`.
  - [ ] **VERIFY**: Rodar `npm run test:tdd` e confirmar GREEN de T019-T022.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do Timeline, Badge e indicadores de contagem, nos estados processando/sucesso/falha, em desktop e mobile.
  - [ ] **EVIDENCE**: Registrar comando, GREEN e arquivos alterados; registrar o bloco em `INTERFACE.md`.
  - [ ] **IMPROVE**: Registrar ajuste aplicado ou ausência justificada.

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

- [ ] T027 [CODE] [US-003] Implementar frontend/src/features/bases/ExcluirBaseDialog.tsx — Refs: US-003, FR-007 — Depends: T024, T025, T026
  - [ ] **PREP**: Confirmar RED de T024-T026; carregar `$specsfy-specialist-react-ui-components`.
  - [ ] **EXECUTE**: Implementar `ExcluirBaseDialog` (shadcn/ui `Dialog`), integrado à tela Detalhe (T023), restrito a owner/admin; registrar em `INTERFACE.md`.
  - [ ] **VERIFY**: Rodar `npm run test:tdd` e confirmar GREEN de T024-T026.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do Dialog de confirmação, nos estados padrão e sem permissão, em desktop e mobile.
  - [ ] **EVIDENCE**: Registrar comando, GREEN e arquivos alterados; registrar o bloco em `INTERFACE.md`.
  - [ ] **IMPROVE**: Registrar ajuste aplicado ou ausência justificada.

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

- [ ] T031 [CODE] [US-004] Implementar frontend/src/features/execucoes/FormularioConsulta.tsx e frontend/src/features/execucoes/ChunksFontes.tsx — Refs: US-004, FR-008, NFR-003 — Depends: T028, T029, T030
  - [ ] **PREP**: Confirmar RED de T028-T030; carregar `$specsfy-specialist-react-ui-components`; reler a seção 10 (formulário de consulta).
  - [ ] **EXECUTE**: Implementar `FormularioConsulta` e `ChunksFontes`, integrados à tela Detalhe (T023); registrar em `INTERFACE.md`.
  - [ ] **VERIFY**: Rodar `npm run test:tdd` e confirmar GREEN de T028-T030; navegar manualmente por teclado e leitor de tela.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do formulário e da lista de chunks-fontes, nos estados carregando/sucesso/falha, em desktop e mobile.
  - [ ] **EVIDENCE**: Registrar comando, GREEN e arquivos alterados; registrar o bloco em `INTERFACE.md`.
  - [ ] **IMPROVE**: Registrar ajuste aplicado ou ausência justificada.

#### Fase final — Documentação, CI e regressão

- [ ] T032 [DOC] Atualizar .specsfy/STACK.md com Next.js, React, TypeScript, Tailwind CSS, shadcn/ui, ReUI e Vitest reais em .specsfy/STACK.md — Refs: US-001 — Depends: T013, T017, T018, T023, T027, T031
  - [ ] **PREP**: Ler o inventário atual de `.specsfy/STACK.md` e o resultado das tarefas de interface concluídas.
  - [ ] **EXECUTE**: Registrar a stack do frontend com evidência (arquivos reais) no bloco gerenciado.
  - [ ] **VERIFY**: Conferir que cada linha nova cita um arquivo real do repositório.
  - [ ] **VISUAL**: Não aplicável — atualização de documento de contexto, sem interface própria.
  - [ ] **EVIDENCE**: Registrar o diff aplicado.
  - [ ] **IMPROVE**: Registrar ausência de ajuste necessário.

- [ ] T033 [DOC] Atualizar .specsfy/DATABASE.md com a coluna Base.documentos em .specsfy/DATABASE.md — Refs: FR-002 — Depends: T006
  - [ ] **PREP**: Ler a regra local de `.specsfy/RULES.md` sobre edição manual de `.specsfy/DATABASE.md` neste componente Python.
  - [ ] **EXECUTE**: Registrar manualmente a coluna `documentos` na tabela `bases`.
  - [ ] **VERIFY**: Conferir que o registro corresponde exatamente à migration de T006.
  - [ ] **VISUAL**: Não aplicável — atualização de documento de contexto, sem interface própria.
  - [ ] **EVIDENCE**: Registrar o diff aplicado.
  - [ ] **IMPROVE**: Registrar ausência de ajuste necessário.

- [ ] T034 [DOC] Atualizar docs/frontend.md e revisar PROJECT.md com a capacidade de frontend entregue em docs/frontend.md — Refs: US-001, US-002, US-003, US-004 — Depends: T013, T017, T018, T023, T027, T031
  - [ ] **PREP**: Rodar `$specsfy-documentator` para reconstruir `docs/` a partir do frontend real.
  - [ ] **EXECUTE**: Conferir `docs/frontend.md` reconstruído e atualizar `PROJECT.md` (Capacidades principais) registrando a demonstração de ponta a ponta.
  - [ ] **VERIFY**: Rodar `node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check`.
  - [ ] **VISUAL**: Não aplicável — atualização de documento, sem interface própria.
  - [ ] **EVIDENCE**: Registrar o comando e o resultado do `--check`.
  - [ ] **IMPROVE**: Registrar ausência de ajuste necessário.

- [ ] T035 [OPS] Adicionar job de CI para o frontend em .github/workflows/ci.yml — Refs: FR-004 — Depends: T001, T013, T017, T018, T023, T027, T031
  - [ ] **PREP**: Ler o job Python existente em `.github/workflows/ci.yml` (FIND-ARCH-001).
  - [ ] **EXECUTE**: Adicionar um job separado rodando `npm ci`, typecheck, lint e `npm run test:tdd` dentro de `frontend/`, sem alterar o job Python.
  - [ ] **VERIFY**: Validar o workflow com `docker compose config`-equivalente do GitHub Actions (`act` local, se disponível) ou revisão manual da sintaxe YAML.
  - [ ] **VISUAL**: Não aplicável — configuração de CI, sem interface.
  - [ ] **EVIDENCE**: Registrar o diff do workflow.
  - [ ] **IMPROVE**: Registrar ausência de ajuste necessário.

- [ ] T036 [TEST] Executar regressão completa e rastreabilidade em tests/ e frontend/src — Refs: US-001, US-002, US-003, US-004 — Depends: T032, T033, T034, T035
  - [ ] **PREP**: Identificar as suítes Pytest e Vitest e os checks estáticos (Ruff, typecheck, lint) do projeto.
  - [ ] **EXECUTE**: Rodar `uv run pytest`, `uv run ruff check .`, `npm run test:tdd`, typecheck e lint em `frontend/`.
  - [ ] **VERIFY**: Confirmar ausência de gaps e todos os `AC` da seção 6 GREEN.
  - [ ] **VISUAL**: Repassar a conferência visual final das quatro telas (bordas, espaçamentos, margens, padding, tipografia) em desktop e mobile.
  - [ ] **EVIDENCE**: Registrar contagens e comandos finais nas seções 11–13.
  - [ ] **IMPROVE**: Registrar retrospectiva do processo desta fatia.

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
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam (Pytest + Ruff no
      backend; Vitest + typecheck + lint no frontend).
