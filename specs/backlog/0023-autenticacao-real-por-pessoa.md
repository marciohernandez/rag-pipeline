# Backlog: Autenticação real por pessoa

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0023 |
| Status | Promoted |
| Produto | rag-pipeline |
| Épico | Identidade e acesso por pessoa |
| Funcionalidade | Autenticação e gestão de pessoas |
| Tipo | História transversal (regra de acesso, dados e interface) |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-09-18 |
| Spec promovida | specs/planned/0020-autenticacao-real-por-pessoa/spec.md |

## Ideia original

Sem citação literal própria: item derivado da descoberta de BACKLOG-0022 (chat com assistente LLM), que exige memória de longo prazo por identidade individual de pessoa. Hoje a autenticação (src/app/auth.py) é um token estático de demonstração (SPEC-0012, DEC-002) com Identity(tenant_id, project_id, role); não existe conceito de pessoa individual dentro de um tenant/projeto.

## Problema percebido

Identity(tenant_id, project_id, role) identifica um papel dentro de um tenant/projeto, mas não distingue uma pessoa da outra quando ambas têm o mesmo papel no mesmo tenant/projeto. Qualquer capacidade que precise saber 'de quem' é uma preferência, uma memória, uma ação ou uma autoria — como a memória de longo prazo pedida em BACKLOG-0022 — não tem hoje onde se apoiar.

## Pessoa afetada ou beneficiada

Pessoas usuárias que compartilham tenant/projeto/papel e precisam ser distinguidas entre si; indiretamente, qualquer fatia futura que dependa de identidade individual (auditoria por pessoa, preferências, memória, autoria de ações).

## Resultado ou valor esperado

Um modelo de identidade que reconhece pessoas individuais (cadastro e/ou login real), preservando o isolamento por tenant/projeto e os papéis (owner/admin/member) já estabelecidos, e substituindo o token estático de demonstração como identidade primária do produto.

## Contexto

Nasce como pré-requisito bloqueante de BACKLOG-0022 (chat com assistente LLM especializado em RAG), que decidiu que a memória de longo prazo do assistente deve ser por pessoa, não por tenant/projeto. Reabre uma decisão que SPEC-0012 (DEC-002) havia deixado explicitamente fora de escopo ('token estático de demonstração' como aceitável para aquela fatia). Afeta o produto inteiro, não só o chat: qualquer spec que hoje usa Identity(tenant_id, project_id, role) precisa ser revisitada para saber se e como incorpora a pessoa individual.

## Referências relacionadas

- `specs/backlog/0022-chat-com-assistente-llm-para-ajudar-no-uso-do-sistema.md` — item que originou esta dependência; sua memória de longo prazo por pessoa só pode ser implementada depois deste. Tipo: dependente (bloqueado por este item).
- `src/app/auth.py` — implementação atual do token estático de demonstração e de `Identity(tenant_id, project_id, role)`. Tipo: superfície técnica afetada.
- `specs/defined/` e specs concluídas que usam `Identity`/`require_write_role` (SPEC-0012 em diante) — todas assumem hoje que papel identifica a parte que age; precisam ser revisitadas quanto à compatibilidade com pessoa individual. Tipo: superfície de produto afetada.

- `specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md` — DEC-002, FR-006, FR-007, US-003 e AC-008/AC-009: origem do token estático e dos papéis owner/admin/member; declara cadastro, convite e login real como fora de escopo sem decidir o mecanismo. Tipo: spec relacionada (limita o item).
- `specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md` — jornada e papéis herdados (owner/admin escrevem, member só consulta); reafirma cadastro/convite fora de escopo. Tipo: backlog relacionado.
- `specs/completed/0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md` e `frontend/src/lib/session.ts` — login por colagem de token e papel deduzido por regex no texto do token; não há endpoint de identidade. Tipo: superfície de produto afetada.
- `src/app/main.py` (`_token_registry`), `src/app/routers/*.py`, `src/app/repo.py` — quatro tokens fixos; todos os routers dependem de `get_identity`, e os de escrita também de `require_write_role`. Tipo: superfície técnica afetada.
- `PROJECT.md`, `.specsfy/STACK.md`, `.specsfy/RULES.md` (nota da SPEC-0012), `.specsfy/DATABASE.md` — registram o token estático e "login real fora de escopo"; precisam ser revisados quando a spec sair. Tipo: documentação relacionada.

**Nota de numeração (resolvida)**: a SPEC-0019 já corrigiu a referência que apontava para "0023" e hoje cita o BACKLOG-0026. O item de chunking na interface é o BACKLOG-0025. Ainda restam referências velhas a "0023" em BACKLOG-0022 e BACKLOG-0026, e a `0024-agrupar-bases-…` em `.specsfy/DATABASE.md` (linhas 106 e 107); estão fora do escopo deste item e ficam sinalizadas para correção separada.

## Comportamento esperado

- Toda pessoa ativa entra com **e-mail e senha** na tela de Login; a sessão carrega tenant, projeto e papel da pessoa e dura 8 horas.
- No primeiro acesso, e depois de uma redefinição feita por owner ou admin, a pessoa define uma nova senha antes de usar qualquer outra tela.
- Owner e admin acessam a tela **Pessoas**: criam pessoas (nome, e-mail, papel, senha inicial), listam, corrigem nome e e-mail, alteram o papel, desativam, reativam e redefinem a senha de outra pessoa. `member` não vê a tela nem chama essa API.
- Toda pessoa troca a própria senha e sai pelo menu do cabeçalho, que mostra o nome dela.
- Workspace, Base, Execução e Consulta registram a pessoa autora, visível nas listas e no detalhe; registros anteriores mostram "autor não identificado".
- O isolamento por tenant e projeto e as permissões por papel (owner/admin escrevem, member só consulta) continuam exatamente como na SPEC-0012.
- O token estático de demonstração deixa de ser a identidade do produto.

## Regras de negócio

- Cada pessoa pertence a exatamente um tenant e projeto, com um único papel; o e-mail é único no sistema.
- Contas nascem só por criação de owner ou admin; não há cadastro aberto nem convite por e-mail.
- Owner e admin gerenciam `member`; só `owner` cria, promove, rebaixa ou desativa `owner`; ninguém se promove (suposição, a confirmar na especificação).
- O último owner ativo de um tenant não pode ser desativado nem rebaixado.
- Pessoa não é apagada, só desativada, para preservar a autoria. Pessoa desativada não entra e perde a sessão na hora.
- Owner ou admin corrige o nome e o e-mail de uma pessoa que possa gerenciar; a pessoa continua a mesma e mantém a autoria. `admin` não altera dados de `owner`.
- Sessão de 8 horas fixas; termina na hora ao sair, desativar, alterar o papel, corrigir nome ou e-mail, ou redefinir a senha.
- Senha com no mínimo 10 caracteres; 5 tentativas erradas seguidas bloqueiam a conta por 15 minutos; a mensagem de erro de login é genérica.
- A senha e seu hash nunca aparecem em resposta HTTP, log ou registro exibido.

## Critérios de aceitação

- **AC-1 Login**: **Dado** uma pessoa ativa com e-mail e senha corretos, **quando** ela entra, **então** recebe uma sessão com o seu tenant, projeto e papel e vê apenas os Workspaces do seu tenant.
- **AC-2 Credencial inválida**: **Dado** e-mail inexistente ou senha errada, **quando** a pessoa tenta entrar, **então** nenhuma sessão é criada e a mensagem é a mesma nos dois casos; **e** na quinta falha seguida a conta fica bloqueada por 15 minutos, mesmo com a senha certa.
- **AC-3 Primeiro acesso**: **Dado** uma pessoa com senha inicial ou redefinida, **quando** ela entra, **então** só consegue definir nova senha; qualquer outra rota ou endpoint é recusado até a troca.
- **AC-4 Distinguir pessoas do mesmo papel**: **Dado** dois owners do mesmo tenant, **quando** cada um cria uma Base, **então** a lista e o detalhe mostram a pessoa autora correta em cada uma.
- **AC-5 Isolamento**: **Dado** uma pessoa do tenant A, **quando** ela consulta ou altera dado do tenant B, **então** recebe a mesma recusa já definida na SPEC-0012.
- **AC-6 Permissão por papel**: **Dado** um `member`, **quando** ele tenta criar, iniciar, repetir ou apagar, ou abrir a tela ou a API de Pessoas, **então** recebe recusa por permissão insuficiente e não vê o item de menu.
- **AC-7 Gestão de pessoas**: **Dado** um owner ou admin, **quando** cria uma pessoa, lista, corrige nome ou e-mail, altera o papel, desativa, reativa ou redefine a senha de outra, **então** cada operação vale para o tenant e projeto dele, a pessoa continua sendo a mesma com o histórico de autoria, e e-mail já usado é recusado com orientação.
- **AC-8 Invalidação imediata**: **Dado** uma pessoa com sessão aberta, **quando** ela é desativada, tem o papel alterado ou a senha redefinida, **então** a próxima requisição dessa sessão é recusada como não autenticada.
- **AC-9 Último owner**: **Dado** um tenant com um único owner ativo, **quando** alguém tenta desativá-lo ou rebaixá-lo, **então** a operação é recusada com explicação.
- **AC-10 Escalada de privilégio** (suposição): **Dado** um `admin`, **quando** tenta criar, promover, rebaixar ou desativar um `owner`, ou se promover, **então** é recusado.
- **AC-11 Autoria**: **Dado** uma Base, Workspace, Execução ou Consulta criada depois da entrega, **quando** alguém a consulta, **então** vê quem a criou; **e** os registros anteriores mostram "autor não identificado".
- **AC-12 Sessão e tokens antigos**: **Dado** uma sessão de mais de 8 horas ou um dos antigos tokens de demonstração, **quando** usados, **então** são recusados como não autenticados.
- **AC-13 Segredos**: **Dado** qualquer resposta HTTP, log ou tela, **quando** inspecionados após criar, entrar, trocar ou redefinir senha, **então** não contêm a senha nem o hash.

## Qualidades e operação

- Segurança: senha guardada só como hash com algoritmo próprio para senhas, nunca em texto (hipótese técnica, a decidir na especificação); mensagem de login genérica; limite de tentativas e bloqueio temporário; invalidação imediata de sessão; escalada de privilégio contida; toda requisição continua sendo recusada antes de tocar pipeline, PostgreSQL ou armazenamento.
- Privacidade: e-mail e nome são dado pessoal e ficam só no banco da aplicação; a autoria é visível a todos os papéis do tenant; pessoa desativada mantém o nome nos registros que criou; nenhum segredo em log ou resposta.
- Desempenho e volume: equipe pequena de consultoria (dezenas de pessoas por tenant); verificação de senha e sessão não devem degradar as listagens atuais; não há meta numérica de latência a fixar.
- Auditoria e observabilidade: registrar, sem segredo, entrada, falha, bloqueio, troca e redefinição de senha, alteração de papel, desativação e reativação, com pessoa autora e horário. Retenção de 90 dias.

## Dependências

- Bloqueia `specs/backlog/0022-chat-com-assistente-llm-para-ajudar-no-uso-do-sistema.md` (fatia 2, memória de longo prazo por pessoa). A fatia 1 do chat não espera este item.
- Substitui a decisão DEC-002 e o comportamento de US-003, FR-006 e AC-008 da SPEC-0012, que falam em token estático: a spec derivada deve dizer o que passa a valer, e a SPEC-0012 concluída não é reaberta por este item.
- Toca a SPEC-0013 (login por token e papel deduzido do texto do token) e a SPEC-0019 (Workspaces: autoria e escopo por pessoa); ambas concluídas.
- Reconciliação com o BACKLOG-0021 (specs concluídas versus o enforcement atual) quando a spec sair.
- Documentação a revisar: `PROJECT.md`, `.specsfy/STACK.md`, `.specsfy/RULES.md` (nota da SPEC-0012 sobre tenant sem tabela própria e "login real fora de escopo"), `.specsfy/DATABASE.md` e `INTERFACE.md`.
- Superfície de testes: 94 ocorrências de `token-demo` em 15 arquivos (`tests/` e `frontend/src/`) precisam migrar para pessoas de teste.

## Situações de erro

- E-mail ou senha inválidos: mensagem genérica, sem revelar se o e-mail existe.
- Conta bloqueada por tentativas: mensagem informa o bloqueio temporário sem expor o tempo restante exato.
- Conta desativada: mesma mensagem genérica do login inválido.
- Sessão expirada, revogada ou token antigo: 401, e o frontend limpa a sessão e volta ao Login.
- Senha inicial ou redefinida ainda não trocada: recusa de qualquer rota, com direcionamento à tela de nova senha.
- Senha nova fraca (menos de 10 caracteres) ou igual à atual: recusa com orientação no campo.
- E-mail já cadastrado ao criar pessoa: recusa com orientação.
- Tentativa de desativar ou rebaixar o último owner, ou de `admin` agir sobre `owner`: recusa por regra, com explicação.
- `member` em rota ou API de Pessoas: 403.
- Falha inesperada do backend: erro seguro, sem detalhe interno, sem segredo.

## Escopo

- Dentro: login por e-mail e senha; sessão de 8 horas com invalidação imediata; troca obrigatória de senha no primeiro acesso e após redefinição; troca da própria senha; tela e API de Pessoas (criar, listar, corrigir nome e e-mail, alterar papel, desativar, reativar, redefinir senha); modelo de pessoa e vínculo com tenant, projeto e papel; registro de autoria em Workspace, Base, Execução e Consulta; endpoint de identidade da pessoa logada e fim da dedução de papel por regex no frontend; remoção dos tokens estáticos do backend de aplicação; criação do primeiro owner por comando; migração dos dados existentes; trilha de auditoria de eventos de acesso.
- Fora: cadastro aberto e autoatendimento; convite por e-mail e envio de e-mail; recuperação de senha por link; login social, SSO e provedor externo de identidade; MFA; várias pessoas com vínculo em mais de um tenant ou projeto e seletor de contexto; apagar a conta de uma pessoa; mover Base entre Workspaces; memória e chat do BACKLOG-0022; mudança no isolamento por tenant e projeto ou nas permissões por papel da SPEC-0012.

## Interface

Especialistas aplicados: `interface-experience` (sistema atual e composição), `ux-design` (jornada e recuperação) e `ui-design` (estados e responsividade), sobre `DESIGNSYSTEM.MD` e `INTERFACE.md`. Stack observada: Next.js 16 (App Router), React 19, TypeScript, Tailwind v4, shadcn/ui `base-nova` (Base UI), sem blocos ReUI instalados, Vitest e Testing Library. Base reaproveitável: `PageHeader`, `DataGridWorkspaces`, `WorkspaceFormSheet`, `ExcluirWorkspaceDialog`, `Sheet`, `Dialog`, `Alert`, `Badge`, `Skeleton`, `Spinner`, `Input`, `Label`, `Button`. Ainda não existem `Select`, menu suspenso, `DetailLists` nem `Breadcrumb` como componente (a trilha está escrita direto no `layout.tsx`); a especificação decide se são primitives shadcn novas ou markup local.

**Telas e destinos**

| Tela | Rota | Quem acessa | Tarefa principal |
| --- | --- | --- | --- |
| Entrar | `/login` | Qualquer pessoa sem sessão | Entrar com e-mail e senha |
| Nova senha | `/nova-senha` (nome provisório) | Pessoa com senha inicial ou redefinida | Definir a própria senha antes de usar o sistema |
| Pessoas (lista) | `/pessoas` | Owner e admin | Ver, criar e administrar as pessoas do tenant |
| Pessoa (detalhe) | `/pessoas/[id]` | Owner e admin | Ver os dados e agir sobre uma pessoa |
| Menu da pessoa | cabeçalho de toda tela autenticada | Toda pessoa | Ver quem está logada, trocar a própria senha e sair |

**Fluxo de informação.** `/login` recebe e-mail e senha; se a senha ainda é inicial ou redefinida, leva a `/nova-senha`; caso contrário, aos Workspaces. Toda tela autenticada pergunta ao backend quem é a pessoa (nome e papel), em vez de deduzir o papel do texto do token. Owner ou admin cria a pessoa com uma senha inicial e a comunica por fora do sistema; a pessoa troca essa senha no primeiro acesso.

**Menus e navegação.** O shell passa a ter navegação persistente no cabeçalho com "Workspaces" e, só para owner e admin, "Pessoas" (hoje a jornada é linear e não há menu). No mobile os itens quebram em uma linha própria sob a trilha, sem perder o nome da equipe. A trilha continua sempre visível: Equipe → Pessoas → nome da pessoa. À direita, o nome da pessoa abre um menu com "Trocar senha" e "Sair".

**Formulários e ações**

- **Entrar**: e-mail e senha, rótulos visíveis, botão "Entrar" com estado de envio, texto explicando a recuperação ("Esqueceu a senha? Peça a um owner ou admin da sua equipe para redefini-la"). Em erro, mensagem genérica em `Alert`, e-mail preservado, senha limpa, foco no primeiro campo. Bloqueio temporário e sessão terminada têm mensagem própria, sem revelar se o e-mail existe.
- **Nova senha**: explica por que aparece ("sua senha foi definida por outra pessoa"), nova senha e confirmação, regra de 10 caracteres visível junto do campo, erro abaixo do campo, botão de envio com estado. Sem menu de navegação até concluir, apenas "Sair".
- **Criar pessoa** (painel lateral, como `WorkspaceFormSheet`): nome, e-mail, papel, senha inicial. Depois de criar, o painel confirma e lembra que a senha inicial deve ser passada à pessoa por um canal seguro.
- **Editar pessoa** (painel lateral): nome, e-mail e papel. Papel `owner` só aparece como opção para owner.
- **Redefinir senha**, **Desativar** e **Reativar** (diálogo de confirmação): mostram a pessoa alvo e a consequência (sessão termina na hora; senha redefinida exige nova troca). Desativar o último owner é recusado com explicação e o botão nem é oferecido a quem não pode.
- **Trocar senha** (diálogo a partir do menu): senha atual, nova e confirmação.

**Composição e responsividade**

- **Lista de Pessoas**: `PageHeader` com ação primária "Nova pessoa", `DataGrid` em largura total com `ID`, nome, e-mail, papel, situação e uma linha inteira que abre o detalhe por mouse e teclado. As ações da linha são "Editar" e "Desativar/Reativar", independentes do clique da linha. **Não há "Apagar"**: pessoa nunca é apagada, e isso é uma exceção registrada ao contrato CRUD, com alcance só nesta tela. Situação aparece em `Badge` com texto, e a pessoa desativada também fica atenuada e com o texto "Desativada", sem depender só de cor.
- **Detalhe da pessoa**: `PageHeader` com nome, situação e as ações (editar, redefinir senha, desativar ou reativar) e `DetailLists` com e-mail, papel, situação, se ainda precisa trocar a senha, e criada em e por quem.
- **Criar e editar em painel lateral** (`Sheet`) em vez de página em duas colunas: exceção registrada ao `DESIGNSYSTEM.MD`, com alcance só na tela Pessoas, porque o formulário tem quatro campos e já é o padrão dos Workspaces (SPEC-0019). Não vira regra do produto.
- **Autoria**: as listas e detalhes de Workspace, Base e Execução ganham "Criada por", e o resultado de uma Consulta mostra quem a fez. Registros anteriores mostram "Autor não identificado". Pessoa desativada continua aparecendo pelo nome, com a marca "(desativada)".
- **Desktop e mobile**: a lista mantém `ID` e rola na horizontal no mobile, como as demais; painel lateral e diálogos ocupam a largura da tela no mobile; o cabeçalho quebra a navegação sob a trilha.

**Estados**

| Estado | Comportamento |
| --- | --- |
| Carregando | `Skeleton` com a estrutura da lista ou do detalhe; botões com `Spinner` e desabilitados durante o envio |
| Vazio | A lista nunca fica sem a própria pessoa; se for a única, orienta a criar as demais |
| Erro | `Alert` com o que falhou e como recuperar, sem detalhe interno e sem segredo; campos preservados |
| Sucesso | Feedback concreto ("Pessoa criada", "Senha redefinida") e retorno ao contexto |
| Sem permissão | `member` que abre `/pessoas` ou `/pessoas/[id]` por endereço vê explicação curta e o caminho de volta, sem dados; o item de menu nem aparece |
| Sessão terminada | O frontend limpa a sessão, volta ao Login e avisa "Sua sessão terminou. Entre novamente." |
| Conta bloqueada | Aviso de bloqueio temporário no Login |
| Não salvo | Painel de criar ou editar protege alterações pendentes ao fechar |

**Acessibilidade.** Rótulos visíveis; erro de campo em vermelho com texto abaixo do campo, anunciado por tecnologia assistiva e foco no primeiro erro; `autocomplete` correto (`username`, `current-password`, `new-password`) para gerenciadores de senha; opção de mostrar a senha; foco preso e devolvido em painéis e diálogos; linha da lista focável com nome acessível; situação nunca só por cor; `aria-current="page"` no último item da trilha; respeito a `prefers-reduced-motion`.

## Dúvidas, decisões e riscos

- **Decisão (Pergunta 1, opção 1)**: mecanismo de entrada é **e-mail e senha próprios**. O backend FastAPI cadastra a pessoa, guarda somente o hash da senha e emite a sessão; sem provedor externo de identidade nem SSO. Alternativas descartadas: login com conta Google (OIDC) e provedor gerenciado (Supabase Auth, Clerk, Auth0). Efeito: a tabela de pessoas e o vínculo com tenant e papel vivem no banco da aplicação, e passam a ser responsabilidade do projeto hash de senha, expiração de sessão, limite de tentativas e recuperação de senha. Recuperação de senha e convite normalmente pedem envio de e-mail; se não houver e-mail, o convite pode gerar um link copiável (a confirmar).
- **Decisão (Pergunta 2, opção 2)**: contas são **criadas por quem administra, sem convite**. Owner ou admin cadastra a pessoa já com e-mail, senha inicial e papel, e ela troca a senha no primeiro acesso. Não há cadastro aberto nem autoatendimento, e o cadastro não depende de envio de e-mail. Alternativas descartadas: convite por e-mail (1) e cadastro aberto com tenant próprio (3). Efeito: o produto segue de uso interno da consultoria, e o fluxo de convite, reenvio e expiração fica para uma evolução posterior. Isto cria a primeira gestão de usuários do produto, fora de escopo desde a SPEC-0012; o alcance dela é a Pergunta 3.
- **Decisão (Pergunta 3, opção 2)**: gestão de pessoas **básica**. Owner ou admin cria a pessoa, lista as pessoas do tenant e projeto, altera o papel, desativa e reativa a conta e redefine a senha de outra pessoa; toda pessoa troca a própria senha. Apagar a conta fica de fora, para preservar a autoria. Alternativas descartadas: mínimo, sem alterar papel nem redefinir senha (1); sem tela de administração, com contas por comando ou seed (3). Efeito: sem envio de e-mail, a recuperação de senha depende de owner ou admin redefinir; há tela de gestão de pessoas no frontend.
- **Decisão (Pergunta 4, opção 1)**: cada pessoa pertence a **exatamente um tenant e projeto, com um único papel**; o e-mail é único no sistema e o login já entra no contexto certo. `Identity` continua com um único `tenant_id`, `project_id` e `role`, e nenhuma rota perde o isolamento atual. Não há seletor de contexto. Alternativas descartadas: vários vínculos com escolha de contexto (2) e um tenant com vários projetos (3). Organização por cliente segue com os Workspaces (SPEC-0019), dentro do mesmo tenant e projeto.
- **Suposição (reversível)**: o vínculo da pessoa com tenant, projeto e papel é modelado como registro próprio, separado do cadastro da pessoa, para que uma evolução futura para vários vínculos não exija reescrever o cadastro.
- **Decisão (Pergunta 5, opção 1)**: o sistema **registra a pessoa autora em tudo que ela cria ou dispara** — Workspace, Base, Execução e Consulta —, e a autoria aparece nas listas e no detalhe. Registros anteriores à entrega ficam como "autor não identificado". Alternativas descartadas: só ações de escrita (2) e nenhuma autoria nesta entrega (3). Efeito: coluna opcional de autoria em quatro tabelas e migração que não altera as linhas existentes; dois owners no mesmo tenant passam a ser distinguíveis na tela e nos testes.
- **Suposição (reversível)**: a autoria é visível para todos os papéis do tenant, inclusive `member`.
- **Suposição (reversível)**: se a pessoa for desativada, o nome dela continua nos registros que criou.
- **Análise da interface atual (para a área Interface)**: o frontend (`frontend/`, Next.js 16 App Router, React 19, Tailwind v4, shadcn/ui `base-nova`, registry ReUI configurado sem blocos instalados) tem Login por colagem de token (`LoginForm`), shell autenticado com trilha e "Sair" (`(autenticado)/layout.tsx`), listas em `DataGrid` com coluna ID e linha clicável, painel lateral para criar e editar (`WorkspaceFormSheet` sobre `Sheet`), diálogo de confirmação (`Dialog`) e `PageHeader` único. O papel é deduzido por regex no texto do token (`session.ts`) porque não há endpoint de identidade. Preservar esses padrões, sem biblioteca nova; mudam o login (token → e-mail e senha), o shell (mostrar a pessoa e obter o papel do backend) e nasce a tela de gestão de pessoas.
- **Decisão (Pergunta 6, opção 1)**: a gestão de pessoas é uma **tela "Pessoas" própria, no padrão dos Workspaces**: lista em largura total com ID, nome, e-mail, papel e situação; linha inteira abre o detalhe da pessoa por mouse e teclado; criar e alterar papel abrem em painel lateral (como `WorkspaceFormSheet`); desativar, reativar e redefinir senha pedem confirmação em diálogo. Visível só para owner e admin; `member` não vê o item de menu. Alternativas descartadas: criar e editar em página própria (2) e gestão dentro do menu da conta (3). Efeito: reaproveita `DataGridWorkspaces`, `WorkspaceFormSheet`, `ExcluirWorkspaceDialog` e `PageHeader`, sem componente novo de estrutura.
- **Suposição (reversível)**: o item "Pessoas" aparece na trilha e no cabeçalho do shell; no mobile a lista mantém a coluna ID e rola na horizontal, como nas demais listas.
- **Suposição (reversível)**: no primeiro acesso, e depois de uma redefinição feita por owner ou admin, a pessoa é levada a uma tela de nova senha antes de qualquer outra tela. O cabeçalho do shell passa a mostrar o nome da pessoa com um menu de "Trocar senha" e "Sair". Erros de login usam mensagem genérica, sem revelar se o e-mail existe.
- **Decisão (Pergunta 7, opção 1)**: a sessão dura **8 horas fixas depois do login**, sem renovação, e **termina na hora** quando a pessoa sai, é desativada, tem o papel alterado ou a senha redefinida. Fechar a aba também encerra a sessão, porque o token permanece só em `sessionStorage` (decisão da SPEC-0013). Alternativas descartadas: expiração por inatividade de 30 minutos (2) e sessão longa de 30 dias com "manter conectado" (3), que quebraria a decisão de guardar o token só em `sessionStorage`. Efeito: a invalidação imediata é o requisito que mais pesa, porque quem desativa ou rebaixa alguém precisa ver o efeito na hora.
- **Suposição (reversível)**: senha com no mínimo 10 caracteres, sem regras de composição; 5 tentativas erradas seguidas bloqueiam a conta por 15 minutos.
- **Suposição (reversível)**: o primeiro owner de cada tenant existente é criado por comando na implantação, dentro de `tenant-1`/`projeto-1`, para que os dados atuais continuem alcançáveis. Os quatro tokens estáticos de demonstração deixam de autenticar no backend de aplicação; os testes passam a criar pessoas por fixture.
- **Suposição (reversível, a confirmar na especificação)**: `admin` gerencia `member` e `admin`, mas não cria, promove, rebaixa nem desativa `owner`, nem se promove a `owner`. Evita escalada de privilégio. Só `owner` gerencia `owner`.
- **Decisão (data-discovery, Pergunta 1, opção 1)**: **owner ou admin corrige o nome e o e-mail** de qualquer pessoa que possa gerenciar, na mesma tela de edição do papel. A pessoa continua sendo a mesma, com o histórico de autoria, e a sessão dela termina na hora, como nas outras mudanças de conta. Alternativas descartadas: a própria pessoa corrige o nome e só owner ou admin o e-mail (2); nada se corrige, desativa-se e recria-se a conta (3), o que perderia a autoria. O "meu perfil" da própria pessoa fica fora desta entrega. Preenche a lacuna deixada pela Pergunta 3, cuja gestão básica não listava a correção desses dois campos.
- **Decisão (data-discovery, Pergunta 2, opção 1)**: o **histórico de acessos** (entrada, senha errada, bloqueio, troca e redefinição de senha, criação, correção, mudança de papel, desativação e reativação) é guardado por **90 dias** e depois apagado. Alternativas descartadas: enquanto a conta existir mais 12 meses (2) e sem prazo (3). A autoria em Workspace, Base, Execução e Consulta não entra nesse prazo: acompanha o registro que descreve.
- **Registrado em `.specsfy/DATABASE.md` (data-discovery, Pergunta 3, opção 1)**: formatos confirmados para Pessoa, Vínculo da pessoa, Sessão, Tentativas de entrada, Histórico de acessos e Autoria. Sessões encerradas e o contador de tentativas são apagados assim que deixam de valer; só o histórico de acessos permanece pelos 90 dias. Alternativas descartadas: mostrar o último acesso na lista de Pessoas (2) e guardar sessões encerradas por 90 dias (3).
- **Suposição (reversível, a confirmar na especificação)**: o histórico de acessos é **somente registrado** nesta entrega, sem tela nem API de consulta; ninguém o lê pela interface.
- **Registrado (área Interface, especialistas `interface-experience`, `ux-design` e `ui-design`)**: telas, fluxo, navegação, formulários, composição e estados na seção `Interface`; respostas textuais das Perguntas 6 e 7 e das suposições do primeiro acesso e do menu da pessoa preservadas.
- **Exceção ao contrato CRUD (alcance: só a tela Pessoas)**: sem "Apagar", porque pessoa só é desativada.
- **Exceção ao `DESIGNSYSTEM.MD` (alcance: só a tela Pessoas)**: criar e editar em painel lateral em vez de página em duas colunas, seguindo o precedente dos Workspaces.
- **Suposição (reversível)**: a navegação persistente do cabeçalho ("Workspaces" e, para owner e admin, "Pessoas") substitui a jornada linear atual, que só tinha a trilha e "Sair".
- **Suposição (reversível)**: quando a própria pessoa troca a senha, a sessão atual continua e as demais terminam; a troca obrigatória do primeiro acesso não a obriga a entrar de novo.
- **Suposição (reversível)**: o rótulo "Equipe" da trilha continua genérico, porque o tenant não tem nome no modelo; dar nome ao tenant é uma evolução, não parte deste item.
- **Aberto (P3, a decidir na especificação)**: o que acontece com a sessão de quem corrige o próprio nome ou e-mail; onde exatamente a autoria aparece em cada lista; se o papel usa `Select` novo ou controle nativo.
- **Suposição (reversível)**: o último owner de um tenant não pode ser desativado nem rebaixado, para não deixar o tenant sem dono.
- **Inferência**: o mecanismo escolhido não muda o modelo de pessoa, vínculo e papel; só muda quem prova a identidade.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras (com a suposição sobre `admin` e `owner` a confirmar na especificação).
- [x] O resultado pode ser verificado objetivamente (AC-1 a AC-13).
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promovido para `specs/planned/0020-autenticacao-real-por-pessoa/spec.md` (SPEC-0020), que passa a governar o comportamento; este backlog preserva a proveniência. A spec decidiu os pontos P3 que este item deixava abertos (`select` nativo para o papel, `dropdown-menu` para o menu da pessoa, posição da autoria em cada lista, sessão de quem corrige os próprios dados) e manteve como suposição a ser confirmada na validação a regra de que `admin` não age sobre `owner`. Próxima etapa: `$specsfy-04-validate`.
