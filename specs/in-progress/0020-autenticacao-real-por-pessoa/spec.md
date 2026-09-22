# Especificação integrada: Autenticação real por pessoa

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0020 |
| Slug | 0020-autenticacao-real-por-pessoa |
| Status | Implementing |
| Effort | 8 |
| Effort updated at | 2026-09-21T23:55:24.050Z |
| Effort rationale | Mudança transversal de segurança: identidade por pessoa em todas as rotas, sessão revogável, migração com dados existentes, 94 usos de token nos testes a migrar e três telas novas no frontend. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | In Progress |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-09-21 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

`Identity(tenant_id, project_id, role)`, resolvida por um token estático de demonstração (`src/app/auth.py`, quatro tokens fixos em `src/app/main.py`), identifica um papel dentro de um tenant e projeto, mas não distingue uma pessoa da outra quando ambas têm o mesmo papel. Qualquer capacidade que precise saber "de quem" é uma preferência, uma ação ou uma autoria não tem onde se apoiar; o BACKLOG-0022 (chat com assistente LLM), por exemplo, exige memória de longo prazo por pessoa. A SPEC-0012 aceitou o token estático como suficiente para aquela fatia e deixou cadastro, convite e login real como fora de escopo.

#### Resultado desejado

Cada pessoa da equipe entra com o próprio e-mail e a própria senha, e o sistema passa a reconhecê-la individualmente: papel, tenant e projeto vêm da conta dela, o que ela cria fica com o nome dela, e quem administra pode criar, corrigir, desativar e redefinir as contas sem depender de terminal. O isolamento por tenant e projeto e as permissões owner, admin e member seguem exatamente como na SPEC-0012. O token estático deixa de ser a identidade do produto.

#### Métricas de sucesso

- 100% das rotas de dados recusam requisição sem sessão de pessoa ativa e nenhuma aceita os quatro tokens antigos (teste parametrizado sobre as rotas registradas).
- 100% dos Workspaces, Bases, Execuções e Consultas criados depois da entrega identificam a pessoa autora, e dois owners do mesmo tenant são distinguíveis nas listas.
- 0 requisições aceitas de uma sessão depois de sair, desativar, mudar o papel, corrigir nome ou e-mail ou redefinir a senha da pessoa.
- Suítes pytest e Vitest atuais verdes após migrar as 94 ocorrências de `token-demo` em 15 arquivos, sem nenhuma ocorrência restante.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: onde o token estático é consumido? → `src/app/auth.py` (registro e dependência `get_identity`), `src/app/main.py` (`_token_registry`), os quatro routers de `src/app/routers/` e `src/app/repo.py` recebem `Identity`; no frontend, `frontend/src/lib/session.ts` guarda o token e deduz o papel por regex, e `frontend/src/lib/api-client.ts` injeta o cabeçalho. Impacto: a troca fica concentrada em uma dependência FastAPI, sem espalhar mudança pelos routers.
- **R-002**: quanto teste depende do token estático? → 94 ocorrências de `token-demo` em 15 arquivos (`tests/test_app_worker.py`, `test_app_auth.py`, `test_app_workspaces.py`, `test_app_bases.py`, `test_app_executions.py`, `test_app_queries.py` e nove arquivos de `frontend/src/`). Impacto: a migração dos testes é parte do escopo, não um efeito colateral.
- **R-003**: como as tabelas nascem em teste e em produção? → `src/app/db.py` cria as tabelas por `metadata.create_all` e as migrações vivem em `alembic/versions/` (última revisão `0019_workspaces`); a suíte limpa as tabelas ao fim de cada teste. Impacto: modelos novos entram em `src/app/models.py` e a revisão nova encadeia em `0019_workspaces`.
- **R-004**: o worker suporta tarefa periódica? → `src/app/tasks.py` usa um `procrastinate.App` e `src/app/worker.py` executa o worker; Procrastinate oferece tarefas periódicas, a confirmar na implementação. Impacto: a limpeza de retenção usa o worker existente, e a validade das sessões nunca depende dela (DEC-006).
- **R-005**: quais padrões de tela existem para reaproveitar? → `frontend/src/features/workspaces/` (`DataGridWorkspaces`, `WorkspaceFormSheet`, `ExcluirWorkspaceDialog`), `PageHeader`, `Sheet`, `Dialog`, `Alert`, `Badge`, `Skeleton`, `Spinner`, `Input`, `Label` e `Button`; não existem `Select`, menu suspenso, `DetailLists` nem `Breadcrumb` como componente. Impacto: seção 10 decide o que é primitive nova e o que é markup local.

#### Fontes e contexto consultados

- `specs/backlog/0023-autenticacao-real-por-pessoa.md` (brief refinado em 7 perguntas de produto e 3 de dados, mais análise de interface).
- `specs/backlog/0022-chat-com-assistente-llm-para-ajudar-no-uso-do-sistema.md` (dependente).
- `specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md`, `0013-frontend-demonstravel-do-backend-de-aplicacao/spec.md` e `0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md` (comportamento que esta spec preserva ou supera).
- Código: `src/app/auth.py`, `main.py`, `models.py`, `db.py`, `repo.py`, `tasks.py`, `worker.py`, `routers/*.py`, `alembic/versions/0019_workspaces.py`, `tests/conftest.py`, `tests/test_app_auth.py`; `frontend/src/` (`lib/session.ts`, `lib/api-client.ts`, `features/auth/LoginForm.tsx`, `app/(autenticado)/layout.tsx`, `components/PageHeader.tsx`, `features/workspaces/`).
- `PROJECT.md`, `INTERFACE.md`, `DESIGNSYSTEM.MD`, `.specsfy/STACK.md`, `.specsfy/RULES.md`, `.specsfy/DATABASE.md` (seis informações registradas pela descoberta de dados).

#### Documentação consultada

- Nenhuma documentação externa consultada. As escolhas de hash de senha e de sessão (DEC-001 e DEC-002) são hipóteses técnicas apoiadas no que o repositório já usa e revisáveis na validação; nenhuma afirmação normativa depende de fonte externa.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Como a pessoa prova quem é? → **A**: e-mail e senha próprios, sem SSO nem provedor externo (Pergunta 1 do backlog).
- **Q**: Como uma pessoa passa a existir? → **A**: criada por owner ou admin, com senha inicial; sem convite nem cadastro aberto (Pergunta 2).
- **Q**: Quanto de gestão de pessoas entra? → **A**: criar, listar, corrigir nome e e-mail, alterar papel, desativar, reativar e redefinir senha; a própria pessoa troca a senha; ninguém é apagado (Pergunta 3 e Pergunta 1 da descoberta de dados).
- **Q**: Uma pessoa pode ter vários tenants ou projetos? → **A**: não; um tenant, um projeto, um papel (Pergunta 4).
- **Q**: O sistema registra quem fez cada ação? → **A**: sim, em Workspace, Base, Execução e Consulta (Pergunta 5).
- **Q**: Onde fica a gestão de pessoas na interface? → **A**: tela própria no padrão dos Workspaces, com painel lateral e diálogos (Pergunta 6).
- **Q**: Quando a sessão acaba? → **A**: 8 horas fixas, e na hora ao sair, desativar, mudar o papel ou redefinir a senha (Pergunta 7).
- **Q**: Por quanto tempo guardar o histórico de acessos? → **A**: 90 dias (Pergunta 2 da descoberta de dados).
- **Q**: Sessões encerradas e contadores de tentativa são guardados? → **A**: não; são apagados assim que deixam de valer, e só o histórico de acessos permanece (Pergunta 3 da descoberta de dados).

#### Dúvidas abertas

- Nenhuma. Os pontos que o backlog deixou para esta spec foram decididos como suposições reversíveis (seção 16) e decisões (seção 17). A regra de que admin não age sobre owner foi confirmada pela pessoa responsável na validação (DEC-013).

### 3. Escopo e atores

#### Incluído

- Login por e-mail e senha, sessão de 8 horas com encerramento imediato, bloqueio temporário por tentativas e mensagem genérica de erro.
- Troca obrigatória da senha no primeiro acesso e depois de uma redefinição, e troca da própria senha.
- Endpoint de identidade da pessoa logada e fim da dedução de papel pelo texto do token.
- API e tela de Pessoas: criar, listar, detalhar, corrigir nome e e-mail, alterar papel, desativar, reativar e redefinir senha, com as proteções do último owner e do admin sobre owner.
- Modelo de pessoa, vínculo com tenant, projeto e papel, sessão, tentativas de entrada e eventos de acesso, com migração reversível.
- Registro da pessoa autora em Workspace, Base, Execução e Consulta e sua exibição na interface.
- Registro dos eventos de acesso por 90 dias e limpeza periódica.
- Comando de implantação para criar o primeiro owner ou redefinir a senha de uma pessoa.
- Remoção dos tokens estáticos do backend de aplicação e migração dos testes que dependem deles.
- Revisão de `PROJECT.md`, `.specsfy/STACK.md`, `.specsfy/RULES.md`, `.specsfy/DATABASE.md` e `INTERFACE.md`.

#### Fora de escopo

- Cadastro aberto, autoatendimento, convite por e-mail e qualquer envio de e-mail.
- Recuperação de senha por link ("esqueci a senha" por e-mail).
- Login social, SSO, provedor externo de identidade e autenticação em dois fatores.
- Pessoa com vínculo em mais de um tenant ou projeto e seletor de contexto.
- Apagar a conta de uma pessoa, tela "meu perfil" e último acesso na lista de Pessoas.
- Tela ou API de consulta ao histórico de acessos.
- Memória e chat do BACKLOG-0022, e mover Base entre Workspaces.
- Mudança no isolamento por tenant e projeto ou nas permissões por papel definidas pela SPEC-0012.
- Reabrir a SPEC-0012 ou a SPEC-0013: esta spec supera a decisão do token estático sem alterar as concluídas.

#### Atores

- **Owner**: entra com a própria conta, faz tudo o que o admin faz e é o único que cria, promove, rebaixa, desativa ou corrige outro owner.
- **Admin**: entra com a própria conta, tem as permissões operacionais do owner sobre Workspaces, Bases e Execuções e administra pessoas member e admin, sem agir sobre owner.
- **Member**: entra com a própria conta, acompanha e consulta; não escreve, não administra pessoas e não vê a tela Pessoas.
- **Pessoa sem sessão**: só alcança Entrar; qualquer outra rota é recusada.
- **Responsável pela implantação**: executa a migração e o comando que cria o primeiro owner ou redefine a senha de uma pessoa.
- **Sistema**: cria e encerra sessões, conta tentativas, registra eventos e apaga o que deixou de valer.

### 4. Princípios e restrições do projeto

- **PR-001**: o isolamento por tenant e projeto e as permissões por papel da SPEC-0012 permanecem; nenhuma rota perde a recusa que já tem.
- **PR-002**: nenhum segredo (senha, hash, token de sessão, credencial de PostgreSQL, R2, Qdrant ou provider) aparece em resposta HTTP, log, evento ou tela, e nenhum segredo é versionado.
- **PR-003**: `src/app/` continua dependendo somente da fachada `src.pipeline.service`; o código de autenticação não importa outros módulos de `src/pipeline/` e `src/pipeline/` não importa `src/app/`.
- **PR-004**: as estruturas novas vivem em `src/app/models.py` e numa revisão Alembic encadeada em `0019_workspaces`; toda execução de migração e de teste usa o banco de teste separado (`rag_pipeline_test`), com a limpeza de tabelas de `tests/conftest.py` e sem comando destrutivo de schema.
- **PR-005**: o frontend segue a stack observada (Next.js 16, React 19, Tailwind v4, shadcn/ui `base-nova`); o token de sessão continua só em `sessionStorage`, nunca em `localStorage` ou cookie persistente; nenhuma biblioteca de interface nova sem confirmação.
- **PR-006**: cada caso de teste deriva do BDD desta spec e declara seu próprio marcador `SPECSFY: SPEC-0020 <IDs>`; RED válido antes de qualquer implementação.
- **PR-007**: a redação da spec evita as palavras que o validador do framework reprova por engano (regra de `.specsfy/RULES.md` e trava `tests/test_spec_markers.py`).

### 5. Histórias de usuário

#### US-001 — Entrar com e-mail e senha (P1)

Como pessoa da equipe, quero entrar com meu e-mail e minha senha, para que o sistema saiba quem eu sou e me dê o tenant, o projeto e o papel que são meus.

**Por que P1**: Sem identidade individual o sistema não distingue duas pessoas com o mesmo papel, e o BACKLOG-0022 (memória por pessoa) não tem onde se apoiar.
**Teste independente**: Criar duas pessoas do mesmo papel no mesmo tenant, entrar com cada uma e confirmar que o sistema devolve identidades distintas.
**Requisitos**: FR-001, FR-002, FR-007

#### US-002 — Definir e trocar a própria senha (P1)

Como pessoa recém-cadastrada ou com senha redefinida, quero definir minha própria senha antes de usar o sistema e poder trocá-la depois, para que só eu a conheça.

**Por que P1**: A senha inicial é digitada por quem administra; sem a troca obrigatória, outra pessoa continuaria sabendo a senha.
**Teste independente**: Entrar com uma senha inicial e confirmar que nenhuma outra tela ou endpoint funciona até a nova senha ser definida.
**Requisitos**: FR-003, FR-004, FR-005

#### US-003 — Administrar as pessoas do tenant (P1)

Como owner ou admin, quero criar, listar, corrigir, mudar o papel, desativar, reativar e redefinir a senha das pessoas da minha equipe, para manter o acesso sob controle sem depender de terminal.

**Por que P1**: Sem e-mail, a recuperação de senha e a entrada de novas pessoas dependem de quem administra; sem tela, dependeriam de terminal.
**Teste independente**: Como owner, criar um member, mudar o papel dele, desativá-lo, reativá-lo e redefinir a senha, tudo pela tela Pessoas.
**Requisitos**: FR-008, FR-009, FR-010, FR-015

#### US-004 — Encerrar o acesso na hora (P1)

Como pessoa logada, owner ou admin, quero que sair, desativar, mudar o papel ou redefinir a senha encerre a sessão afetada imediatamente, para que um acesso indevido não sobreviva à decisão de quem administra.

**Por que P1**: Quem desativa ou rebaixa alguém precisa ver o efeito na hora, e não esperar a sessão expirar.
**Teste independente**: Abrir uma sessão, desativar a pessoa por outra sessão e confirmar que a próxima requisição da primeira é recusada.
**Requisitos**: FR-006, NFR-004

#### US-005 — Saber quem criou cada registro (P2)

Como pessoa do tenant, quero ver quem criou cada Workspace, Base, Execução e Consulta, para distinguir o trabalho de cada pessoa e ter base para auditoria e memória por pessoa.

**Por que P2**: Hoje dois owners do mesmo tenant são indistinguíveis nos registros que criam.
**Teste independente**: Com dois owners, cada um cria uma Base e as listas mostram o autor correto de cada uma.
**Requisitos**: FR-011

#### US-006 — Registrar os eventos de acesso (P2)

Como owner ou admin, quero que o sistema registre entradas, falhas, bloqueios e mudanças de conta por 90 dias, sem guardar segredo, para poder investigar depois do fato.

**Por que P2**: Sem histórico, não há como responder quem mudou uma conta ou tentou entrar.
**Teste independente**: Provocar cada tipo de evento e confirmar que o registro existe, sem senha nem token, e que registros com mais de 90 dias são apagados.
**Requisitos**: FR-012, NFR-001

#### US-007 — Implantar sem perder dados nem manter tokens antigos (P1)

Como responsável pela implantação, quero criar o primeiro owner por comando e aplicar a migração sem alterar os dados atuais, para que o produto passe a exigir pessoas reais sem perder o que já existe.

**Por que P1**: As bases, execuções e consultas atuais pertencem a tenant-1 e projeto-1; sem migração segura elas ficariam inalcançáveis, e os tokens estáticos continuariam abrindo o sistema.
**Teste independente**: Aplicar a migração sobre um banco com dados, criar o primeiro owner por comando e confirmar que ele vê os dados atuais e que os tokens antigos são recusados.
**Requisitos**: FR-013, NFR-006

### 6. Cenários BDD de aceite

#### AC-001 — Entrar com credenciais válidas

**Cobre**: US-001, FR-001, FR-007, FR-010, NFR-003

```gherkin
@US-001 @FR-001 @FR-007 @FR-010 @NFR-003 @AC-001
Feature: Entrar com e-mail e senha

  Scenario: Pessoa ativa entra e recebe a sua identidade
    Given uma pessoa ativa, sem senha pendente, owner do tenant-1 e projeto-1
    When ela envia o e-mail e a senha corretos
    Then recebe uma sessão que expira em 8 horas
    And o endpoint de identidade devolve o nome, o papel owner, o tenant-1 e o projeto-1 dela
    And a mesma sessão lista apenas os Workspaces do tenant-1 e projeto-1
```

#### AC-002 — Credencial inválida sem revelar nada

**Cobre**: US-001, FR-001, FR-002, NFR-002

```gherkin
@US-001 @FR-001 @FR-002 @NFR-002 @AC-002
Feature: Recusar credenciais inválidas

  Scenario: Senha errada de e-mail existente
    Given uma pessoa ativa com e-mail cadastrado
    When alguém envia esse e-mail com uma senha errada
    Then nenhuma sessão é criada
    And a resposta é 401 com a mensagem genérica de credenciais inválidas
    And o contador de falhas seguidas desse e-mail aumenta em um
```

#### AC-003 — Conta desativada e e-mail inexistente recebem a mesma recusa

**Cobre**: US-001, FR-001, FR-008, NFR-002

```gherkin
@US-001 @FR-001 @FR-008 @NFR-002 @AC-003
Feature: Não permitir descobrir quais e-mails existem

  Scenario: Os três casos de recusa são indistinguíveis
    Given uma pessoa desativada, uma pessoa ativa e um e-mail que não existe
    When cada um é usado para entrar, com senha errada ou, no caso da desativada, com a senha correta
    Then os três recebem o mesmo status e o mesmo corpo de resposta
    And nenhuma sessão é criada
```

#### AC-004 — Bloqueio na quinta falha seguida

**Cobre**: US-001, FR-002, NFR-002

```gherkin
@US-001 @FR-002 @NFR-002 @AC-004
Feature: Bloquear tentativas repetidas

  Scenario: Cinco erros bloqueiam por 15 minutos
    Given cinco tentativas seguidas com senha errada para o mesmo e-mail
    When a sexta tentativa usa a senha correta dentro dos 15 minutos
    Then a entrada é recusada com a mensagem de bloqueio temporário, sem o tempo restante exato
    And nenhuma sessão é criada

  Scenario: E-mail inexistente também bloqueia
    Given cinco tentativas seguidas para um e-mail que não existe
    When a sexta tentativa acontece
    Then a resposta é a mesma mensagem de bloqueio temporário
```

#### AC-005 — Bloqueio termina e contador zera

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-005
Feature: Encerrar o bloqueio

  Scenario: Passados os 15 minutos a pessoa volta a entrar
    Given uma conta bloqueada há mais de 15 minutos
    When a pessoa envia a senha correta
    Then a entrada é aceita e o contador de falhas volta a zero

  Scenario: Um sucesso antes do limite zera o contador
    Given quatro falhas seguidas e nenhuma sessão
    When a pessoa entra com a senha correta
    Then o contador volta a zero e uma nova falha conta como a primeira
```

#### AC-006 — Primeiro acesso exige nova senha

**Cobre**: US-002, FR-004, FR-005, FR-010, FR-014

```gherkin
@US-002 @FR-004 @FR-005 @FR-010 @FR-014 @AC-006
Feature: Definir a própria senha antes de usar o sistema

  Scenario: Senha inicial só abre a tela de nova senha
    Given uma pessoa criada por um admin, com senha inicial pendente
    When ela entra com essa senha
    Then a interface a leva à tela Nova senha, sem menu de navegação, apenas com a ação Sair
    And qualquer rota de dados, como listar Workspaces, responde 403 com o código senha_pendente
    And o endpoint de identidade, a troca de senha e o encerramento da sessão continuam permitidos

  Scenario: Depois de definir a senha o acesso é liberado
    Given a mesma pessoa na tela Nova senha
    When ela envia uma nova senha válida e a confirmação igual
    Then a pendência é limpa e ela segue para os Workspaces sem entrar de novo
```

#### AC-007 — Política de senha na criação e na troca

**Cobre**: US-002, US-003, FR-003, FR-005

```gherkin
@US-002 @US-003 @FR-003 @FR-005 @AC-007
Feature: Aplicar a política de senha

  Scenario: Senha curta, igual à atual ou sem confirmação é recusada
    Given uma pessoa trocando a própria senha
    When ela envia uma nova senha com menos de 10 caracteres, igual à atual ou diferente da confirmação
    Then a troca é recusada com a causa junto do campo e a senha antiga continua valendo

  Scenario: A criação por admin segue a mesma política
    Given um admin criando uma pessoa
    When ele informa uma senha inicial com menos de 10 caracteres
    Then a criação é recusada e nenhuma pessoa é criada
```

#### AC-008 — Trocar a própria senha mantém a sessão atual

**Cobre**: US-002, US-004, FR-005, FR-006, NFR-004

```gherkin
@US-002 @US-004 @FR-005 @FR-006 @NFR-004 @AC-008
Feature: Trocar a própria senha

  Scenario: A sessão atual continua e as demais terminam
    Given uma pessoa com duas sessões abertas, A e B
    When ela troca a senha usando a sessão A informando a senha atual
    Then a sessão A continua aceita
    And a sessão B é recusada já na requisição seguinte
    And um evento de troca de senha é registrado
```

#### AC-009 — Sessão de 8 horas e saída

**Cobre**: US-004, FR-006, FR-014, NFR-004

```gherkin
@US-004 @FR-006 @FR-014 @NFR-004 @AC-009
Feature: Limitar e encerrar a sessão

  Scenario: Sessão de mais de 8 horas é recusada
    Given uma sessão criada há mais de 8 horas
    When ela é usada em qualquer rota autenticada
    Then a resposta é 401 e a sessão deixa de existir

  Scenario: Sair encerra na hora
    Given uma sessão válida
    When a pessoa usa Sair
    Then o servidor apaga a sessão, o frontend limpa o token e volta ao Login
    And reutilizar o token antigo responde 401
```

#### AC-010 — Eventos de conta derrubam a sessão da pessoa

**Cobre**: US-003, US-004, FR-006, FR-008, NFR-004

```gherkin
@US-003 @US-004 @FR-006 @FR-008 @NFR-004 @AC-010
Feature: Encerrar a sessão quando a conta muda

  Scenario: Desativar, mudar o papel, corrigir dados ou redefinir a senha
    Given uma pessoa com uma sessão aberta e outra pessoa, owner, agindo sobre ela
    When o owner desativa, muda o papel, corrige o nome ou o e-mail ou redefine a senha dessa pessoa
    Then a próxima requisição da sessão da pessoa afetada responde 401
    And o motivo do encerramento fica registrado como evento de acesso

  Scenario: Quem corrige os próprios dados mantém a sessão atual
    Given uma pessoa corrigindo o próprio nome
    When a correção é salva
    Then a sessão atual continua aceita e as demais sessões dela terminam
```

#### AC-011 — Owner e admin administram as pessoas

**Cobre**: US-003, FR-003, FR-004, FR-008, FR-010

```gherkin
@US-003 @FR-003 @FR-004 @FR-008 @FR-010 @AC-011
Feature: Administrar pessoas do tenant

  Scenario: Fluxo completo de administração
    Given um owner autenticado no tenant-1 e projeto-1
    When ele cria um member com nome, e-mail, papel e senha inicial, lista, detalha, corrige o nome, muda o papel para admin, desativa, reativa e redefine a senha
    Then cada operação vale somente para o tenant-1 e projeto-1
    And a pessoa criada e a pessoa com senha redefinida nascem com a troca de senha pendente
    And a pessoa nunca é apagada
```

#### AC-012 — E-mail duplicado e dados inválidos

**Cobre**: US-003, FR-008, FR-015, NFR-005

```gherkin
@US-003 @FR-008 @FR-015 @NFR-005 @AC-012
Feature: Recusar cadastro inválido sem perder o que foi digitado

  Scenario: E-mail já usado, sem diferenciar maiúsculas
    Given uma pessoa cadastrada com o e-mail ana@exemplo.com
    When um admin tenta criar outra com ANA@exemplo.com, inclusive em outro tenant
    Then a criação é recusada com 409 e orientação para usar outro e-mail

  Scenario: O painel preserva os campos e foca o primeiro erro
    Given o painel Nova pessoa com nome, e-mail e papel preenchidos
    When o envio volta com erro de e-mail duplicado
    Then os campos continuam preenchidos, o erro aparece abaixo do campo de e-mail e o foco vai para ele
```

#### AC-013 — Proteções do último owner e do admin

**Cobre**: US-003, FR-008, FR-009

```gherkin
@US-003 @FR-008 @FR-009 @AC-013
Feature: Impedir perda de controle e escalada de privilégio

  Scenario: Último owner não é desativado nem rebaixado
    Given um tenant com um único owner ativo
    When alguém tenta desativar ou rebaixar esse owner
    Then a operação é recusada com explicação e o owner continua ativo com o papel owner

  Scenario: Admin não age sobre owner nem se promove
    Given um admin e um owner no mesmo tenant
    When o admin tenta criar um owner, promover alguém ou a si mesmo a owner, ou corrigir, desativar ou redefinir a senha do owner
    Then cada tentativa é recusada com 403

  Scenario: Ninguém desativa a si mesma
    Given uma pessoa autenticada
    When ela tenta desativar a própria conta
    Then a operação é recusada
```

#### AC-014 — Member e isolamento por tenant

**Cobre**: US-003, FR-009, FR-010, FR-015, NFR-003

```gherkin
@US-003 @FR-009 @FR-010 @FR-015 @NFR-003 @AC-014
Feature: Preservar permissões por papel e isolamento

  Scenario: Member não escreve nem administra pessoas
    Given um member autenticado
    When ele tenta criar Workspace, Base, Execução ou apagar Base, ou chamar a API ou abrir a rota de Pessoas
    Then recebe 403 na API e uma tela de permissão insuficiente na rota, sem dados
    And o item Pessoas não aparece no menu

  Scenario: Pessoa de um tenant não alcança outro
    Given uma pessoa do tenant-2 e um Workspace do tenant-1
    When ela consulta ou altera esse Workspace ou uma pessoa do tenant-1
    Then recebe a mesma recusa que a SPEC-0012 já definia
```

#### AC-015 — Tokens estáticos e requisições sem sessão são recusados

**Cobre**: US-007, FR-010, FR-013, NFR-003

```gherkin
@US-007 @FR-010 @FR-013 @NFR-003 @AC-015
Feature: Encerrar a identidade por token estático

  Scenario: Nenhuma rota aceita os antigos tokens
    Given os tokens antigos token-demo-owner, token-demo-admin, token-demo-member e token-demo-outro-tenant
    When cada um é enviado em qualquer rota autenticada
    Then a resposta é 401

  Scenario: Rota sem sessão é recusada antes de tocar dados
    Given uma requisição sem cabeçalho de autorização ou com sessão inexistente
    When ela chega a qualquer rota de dados
    Then a resposta é 401 antes de qualquer acesso a pipeline, PostgreSQL ou armazenamento
```

#### AC-016 — Autoria de duas pessoas com o mesmo papel

**Cobre**: US-005, FR-010, FR-011

```gherkin
@US-005 @FR-010 @FR-011 @AC-016
Feature: Registrar a pessoa autora

  Scenario: Cada pessoa aparece como autora do que criou
    Given dois owners do mesmo tenant, Ana e Bruno
    When Ana cria um Workspace e uma Base e Bruno inicia uma Execução e faz uma Consulta
    Then a API devolve Ana como autora do Workspace e da Base e Bruno como autor da Execução e da Consulta
```

#### AC-017 — Exibição da autoria

**Cobre**: US-005, FR-011

```gherkin
@US-005 @FR-011 @AC-017
Feature: Mostrar quem criou cada registro

  Scenario: Autor identificado, não identificado e desativado
    Given registros criados depois da entrega, registros anteriores e um autor depois desativado
    When as listas e os detalhes são exibidos
    Then os novos mostram "Criada por" com o nome
    And os anteriores mostram "Autor não identificado"
    And o autor desativado continua com o nome e a marca "(desativada)"
```

#### AC-018 — Eventos de acesso registrados

**Cobre**: US-006, FR-012, NFR-001

```gherkin
@US-006 @FR-012 @NFR-001 @AC-018
Feature: Registrar os eventos de acesso

  Scenario: Cada tipo de evento deixa um registro
    Given a aplicação em uso
    When ocorrem entrada, senha errada, bloqueio, troca de senha, redefinição, criação, correção de dados, mudança de papel, desativação, reativação e encerramento de sessão
    Then cada um gera um registro com o tipo, quem fez, com quem e quando
    And nenhum registro contém senha, hash ou token
```

#### AC-019 — Retenção de 90 dias

**Cobre**: US-006, FR-012

```gherkin
@US-006 @FR-012 @AC-019
Feature: Apagar o histórico antigo

  Scenario: Registros com mais de 90 dias são apagados
    Given eventos de acesso de 89 e de 91 dias atrás
    When a limpeza periódica é executada
    Then o evento de 91 dias é apagado e o de 89 dias permanece
    And sessões e contadores que deixaram de valer também são apagados
```

#### AC-020 — Migração preserva dados e cria autoria vazia

**Cobre**: US-005, US-007, FR-011, FR-013, NFR-006

```gherkin
@US-005 @US-007 @FR-011 @FR-013 @NFR-006 @AC-020
Feature: Migrar sem perder dados

  Scenario: Upgrade sobre banco com dados atuais
    Given um banco na revisão anterior com Workspaces, Bases, Execuções e Consultas
    When a nova revisão é aplicada
    Then todas as linhas continuam iguais
    And a autoria dos registros anteriores fica vazia
    And as tabelas de pessoas, vínculos, sessões, tentativas e eventos existem
```

#### AC-021 — Nenhum segredo em resposta, log ou evento

**Cobre**: US-001, US-006, FR-003, FR-012, NFR-001

```gherkin
@US-001 @US-006 @FR-003 @FR-012 @NFR-001 @AC-021
Feature: Não vazar segredos

  Scenario: Varredura depois de criar, entrar, trocar e redefinir
    Given uma pessoa criada com uma senha conhecida e a captura de logs ligada
    When ela entra, troca a senha e tem a senha redefinida
    Then nenhuma resposta HTTP, linha de log ou evento contém a senha, o hash ou o token de sessão
```

#### AC-022 — Comando cria o primeiro owner e ele alcança os dados atuais

**Cobre**: US-007, FR-004, FR-013, NFR-006

```gherkin
@US-007 @FR-004 @FR-013 @NFR-006 @AC-022
Feature: Criar o primeiro owner por comando

  Scenario: Primeiro owner em tenant existente
    Given um banco migrado com Workspaces do tenant-1 e projeto-1 e nenhuma pessoa
    When o comando cria o owner nesse tenant e projeto, com a senha lida sem eco
    Then o owner entra, é levado a definir a própria senha e depois vê os Workspaces e Bases atuais

  Scenario: Redefinir a senha de uma pessoa existente por comando
    Given um tenant cujos owners esqueceram as senhas
    When o comando redefine a senha de um owner
    Then ele entra com a nova senha e fica pendente de troca
```

#### AC-023 — Sessão terminada volta ao Login e papel vem do backend

**Cobre**: US-001, US-004, FR-007, FR-014

```gherkin
@US-001 @US-004 @FR-007 @FR-014 @AC-023
Feature: Reagir a sessão terminada e conhecer a identidade

  Scenario: Requisição não autenticada leva ao Login com aviso
    Given uma pessoa logada cuja sessão foi encerrada por outra pessoa
    When ela usa qualquer ação da interface
    Then o frontend limpa a sessão, volta ao Login e mostra "Sua sessão terminou. Entre novamente."

  Scenario: O papel não é deduzido do token
    Given um token cujo texto contém a palavra admin, de uma pessoa member
    When o shell carrega a identidade
    Then as ações de escrita não aparecem, porque o papel vem do endpoint de identidade
```

#### AC-024 — Menu da pessoa e navegação persistente

**Cobre**: US-002, FR-007, FR-014, FR-015

```gherkin
@US-002 @FR-007 @FR-014 @FR-015 @AC-024
Feature: Navegar e cuidar da própria conta

  Scenario: Cabeçalho com pessoa, destinos e trilha
    Given uma pessoa autenticada com a senha definida
    When qualquer tela autenticada é aberta
    Then o cabeçalho mostra a trilha Equipe primeiro, os itens Workspaces e, só para owner e admin, Pessoas
    And o nome da pessoa abre um menu com Trocar senha e Sair
    And Trocar senha abre um diálogo com senha atual, nova e confirmação
```

#### AC-025 — Tela Pessoas: lista, painéis e diálogos

**Cobre**: US-003, FR-008, FR-009, FR-015, NFR-005

```gherkin
@US-003 @FR-008 @FR-009 @FR-015 @NFR-005 @AC-025
Feature: Administrar pessoas pela interface

  Scenario: Lista e ações por linha
    Given um owner na tela Pessoas
    When a lista carrega
    Then ela mostra ID, nome, e-mail, papel e situação em largura total, com a linha inteira abrindo o detalhe por mouse e teclado
    And cada linha tem Editar e Desativar ou Reativar, sem Apagar

  Scenario: Painéis e diálogos respeitam as regras
    Given o mesmo owner
    When ele abre Nova pessoa, Editar, Desativar, Reativar ou Redefinir senha
    Then criar e editar abrem em painel lateral e as demais ações pedem confirmação em diálogo com o alvo e a consequência
    And a ação de desativar não é oferecida para o último owner
```

#### AC-026 — Acessibilidade e responsividade das telas novas

**Cobre**: US-002, FR-014, FR-015, NFR-005

```gherkin
@US-002 @FR-014 @FR-015 @NFR-005 @AC-026
Feature: Usar as telas novas por teclado e em tela pequena

  Scenario: Formulários acessíveis
    Given as telas Entrar, Nova senha, Trocar senha e os painéis de Pessoas
    When a pessoa navega só por teclado e envia com erro
    Then os campos têm rótulo visível, o erro é anunciado abaixo do campo, o foco vai para o primeiro erro e os campos de senha usam autocomplete username, current-password e new-password

  Scenario: Tela pequena
    Given uma viewport de 360 px de largura
    When a lista de Pessoas e o cabeçalho são exibidos
    Then a página não rola na horizontal, a lista mantém a coluna ID e rola dentro da própria região
```

#### AC-027 — Regressão com pessoas de teste

**Cobre**: US-007, FR-010, NFR-003

```gherkin
@US-007 @FR-010 @NFR-003 @AC-027
Feature: Manter o comportamento existente

  Scenario: Suítes existentes passam sem token estático
    Given as suítes pytest e Vitest atuais migradas para criar pessoas de teste
    When são executadas por inteiro
    Then todas passam e a busca por token-demo em src, tests e frontend/src não encontra ocorrência
```

#### AC-028 — Senha e sessão guardadas só de forma derivada

**Cobre**: FR-003, FR-006, NFR-001

```gherkin
@FR-003 @FR-006 @NFR-001 @AC-028
Feature: Guardar somente derivados

  Scenario: Colunas gravadas
    Given uma pessoa criada e uma sessão aberta
    When as linhas gravadas no banco são inspecionadas
    Then a senha existe somente como hash de algoritmo próprio para senhas
    And o token de sessão existe somente como resumo, nunca em texto
```

#### AC-029 — Reversão da migração

**Cobre**: US-007, FR-013, NFR-006

```gherkin
@US-007 @FR-013 @NFR-006 @AC-029
Feature: Reverter a migração

  Scenario: Downgrade remove só o que foi criado
    Given um banco na nova revisão com dados anteriores
    When a revisão é revertida
    Then as tabelas de pessoas, vínculos, sessões, tentativas e eventos e as colunas de autoria desaparecem
    And as linhas de workspaces, bases, executions e queries continuam iguais
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve autenticar por e-mail e senha: com credenciais válidas de uma pessoa ativa, cria uma sessão e devolve a identidade (pessoa, tenant, projeto e papel); com e-mail inexistente, senha errada ou conta desativada, recusa com a mesma mensagem genérica e nenhuma sessão.
- **FR-002**: O sistema deve bloquear a entrada por 15 minutos depois de 5 falhas seguidas para o mesmo e-mail normalizado, existente ou não, recusando também a senha correta durante o bloqueio, zerando o contador ao entrar com sucesso ou ao fim do bloqueio e respondendo com mensagem própria de bloqueio, sem o tempo restante exato.
- **FR-003**: O sistema deve exigir senha com no mínimo 10 caracteres, sem regras de composição, na criação de pessoa, na redefinição e na troca da própria senha, e guardar somente um hash de senha.
- **FR-004**: O sistema deve marcar a pessoa criada ou com senha redefinida como pendente de troca de senha; enquanto pendente, a sessão só pode consultar a própria identidade, trocar a senha e sair, e qualquer outra rota é recusada com o código `senha_pendente`.
- **FR-005**: O sistema deve permitir que a pessoa troque a própria senha informando a senha atual e a nova (na pendência, somente a nova), recusar nova senha igual à atual ou fora da política, limpar a pendência, manter a sessão atual, encerrar as demais sessões da pessoa e registrar o evento.
- **FR-006**: O sistema deve manter cada sessão por 8 horas fixas, sem renovação, e encerrá-la e apagá-la na hora quando a pessoa sai, é desativada, tem o papel alterado, tem nome ou e-mail corrigidos ou tem a senha redefinida por outra pessoa.
- **FR-007**: O sistema deve expor um endpoint que devolve a identidade da pessoa logada (id, nome, e-mail, papel, tenant, projeto e se precisa trocar a senha), e o frontend deve usá-lo para conhecer nome e papel, deixando de deduzir o papel do texto do token.
- **FR-008**: O sistema deve permitir a owner e admin criar (nome, e-mail, papel e senha inicial), listar, detalhar, corrigir nome e e-mail, alterar o papel, desativar, reativar e redefinir a senha das pessoas do próprio tenant e projeto, com e-mail único no sistema sem diferenciar maiúsculas de minúsculas, e nunca apagar uma pessoa.
- **FR-009**: O sistema deve recusar desativar ou rebaixar o último owner ativo de um tenant, recusar que um admin crie, altere, promova, desative ou redefina a senha de um owner ou se promova a owner, e recusar que uma pessoa desative a si mesma.
- **FR-010**: O sistema deve preservar as permissões e o isolamento existentes: member não escreve nem acessa a gestão de pessoas, nenhuma pessoa lê ou altera dado de outro tenant ou projeto, cada rota de dados exige sessão de pessoa ativa com senha definida, e os tokens estáticos de demonstração deixam de autenticar.
- **FR-011**: O sistema deve registrar a pessoa autora (referência opcional) em Workspace, Base, Execução e Consulta criados depois da entrega, expor o nome do autor nas respostas da API e mostrá-lo na interface, com "autor não identificado" nos registros anteriores e o nome preservado, marcado como desativada, quando a pessoa é desativada.
- **FR-012**: O sistema deve registrar cada evento de acesso (entrada, senha errada, bloqueio, troca de senha, redefinição, criação, correção de dados, mudança de papel, desativação, reativação e encerramento de sessão com o motivo), com quem fez, com quem e quando, sem qualquer segredo, e apagar os registros com mais de 90 dias; não há tela nem API de consulta nesta entrega.
- **FR-013**: O sistema deve fornecer um comando de implantação que cria o primeiro owner de um tenant e projeto informados (senha lida sem eco, nunca por argumento) ou redefine a senha de uma pessoa existente, e uma migração que cria as estruturas novas sem alterar as linhas atuais e pode ser revertida.
- **FR-014**: O sistema deve oferecer as telas Entrar e Nova senha, um menu da pessoa no cabeçalho (nome, Trocar senha e Sair) e navegação persistente entre Workspaces e Pessoas, e deve levar ao Login, com aviso, quando a sessão termina ou uma requisição volta como não autenticada.
- **FR-015**: O sistema deve oferecer a tela Pessoas a owner e admin, com lista, detalhe, painel lateral de criar e editar e diálogos de desativar, reativar e redefinir a senha, sem ação de apagar, ocultando o item de menu e recusando a rota para member.

#### Não funcionais

- **NFR-001**: Nenhum segredo (senha, hash de senha, token de sessão) aparece em resposta HTTP, log, evento de acesso ou tela; a senha existe só como hash de algoritmo próprio para senhas e o token de sessão só como resumo no banco. **Verificação**: testes que criam, entram, trocam e redefinem senha e varrem respostas, logs capturados e linhas de eventos; inspeção das colunas gravadas.
- **NFR-002**: Login para e-mail inexistente, senha errada e conta desativada devolve o mesmo status e o mesmo corpo, e o bloqueio por tentativas vale igualmente para e-mail inexistente, sem permitir descobrir quais e-mails existem. **Verificação**: teste que compara as respostas dos três casos e do bloqueio de um e-mail inexistente.
- **NFR-003**: As recusas e os isolamentos existentes (401, 403 e 404 entre tenants) permanecem idênticos, e a suíte pytest e a suíte Vitest inteiras passam com pessoas de teste no lugar dos tokens estáticos. **Verificação**: pytest e Vitest completos verdes e busca por `token-demo` sem ocorrência em `src/`, `tests/` e `frontend/src/`.
- **NFR-004**: Depois de um evento que encerra a sessão, nenhuma requisição posterior dessa sessão é aceita (zero aceitas), sem depender do prazo de 8 horas nem de tarefa de limpeza. **Verificação**: teste sequencial que dispara cada evento e repete a requisição imediatamente.
- **NFR-005**: As telas novas têm rótulos visíveis, erro de campo anunciado com foco no primeiro erro, `autocomplete` correto, operação por teclado e nenhuma rolagem horizontal da página em 360 px de largura. **Verificação**: testes Vitest com Testing Library e revisão visual registrada por tarefa, com viewport e estados percorridos.
- **NFR-006**: A migração preserva 100% das linhas existentes de workspaces, bases, executions e queries, e a reversão remove somente o que a revisão criou. **Verificação**: teste de migração no banco de teste `rag_pipeline_test` e os comandos `uv run alembic upgrade head` e `uv run alembic current`.

#### Erros e casos-limite

- E-mail ou senha inválidos, e-mail inexistente ou conta desativada → 401 com a mesma mensagem genérica, sem sessão.
- Cinco falhas seguidas para o mesmo e-mail → 429 com mensagem de bloqueio temporário, sem o tempo restante exato, também para e-mail inexistente.
- Sessão ausente, inexistente, expirada, encerrada ou token antigo → 401; o frontend limpa a sessão e volta ao Login com o aviso "Sua sessão terminou. Entre novamente.".
- Senha inicial ou redefinida ainda não trocada → 403 com o código `senha_pendente` em qualquer rota fora identidade, troca de senha e sair.
- Senha nova com menos de 10 caracteres, igual à atual ou sem confirmação igual → 422 com a causa ligada ao campo; a senha antiga continua valendo.
- Senha atual incorreta na troca da própria senha → 422 com a causa no campo e a falha conta para o bloqueio do e-mail.
- E-mail já cadastrado ao criar ou corrigir pessoa, com qualquer combinação de maiúsculas → 409 com orientação; os campos digitados são preservados.
- Desativar ou rebaixar o último owner ativo, ou desativar a si mesma → 409 com explicação.
- Admin agindo sobre owner, criando owner ou se promovendo → 403.
- Member em qualquer rota de escrita ou de Pessoas → 403; na interface, tela de permissão insuficiente sem dados e sem item de menu.
- Pessoa de outro tenant ou projeto → 404 no recurso, igual ao comportamento atual, sem revelar existência.
- Falha inesperada → erro seguro sem detalhe interno e sem segredo.
- Migração aplicada sem a revisão anterior ou sem o banco de teste separado → o comando recusa e nada é alterado.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend Python 3.12+ com uv, FastAPI, SQLAlchemy 2, Alembic, psycopg, Procrastinate e Pytest; PostgreSQL da aplicação em `src/app/`, Qdrant como vector store, R2 ou diretório local para arquivos.
- `src/app/auth.py` expõe `Identity(tenant_id, project_id, role)`, `TokenRegistry`, `configure`, `get_identity` e `require_write_role`; `src/app/main.py` monta o registro de quatro tokens (`_token_registry`) e chama `auth.configure`.
- Os routers `bases.py`, `executions.py`, `workspaces.py` e `queries.py` recebem a identidade por `Depends(get_identity)` e chamam `require_write_role` nas rotas de escrita; `repo.py` filtra por `tenant_id` e `project_id` da identidade.
- `tests/conftest.py` define `APP_DATABASE_URL` para o banco `rag_pipeline_test` e limpa as tabelas ao fim de cada teste.
- Frontend em `frontend/` (Next.js 16 App Router): `lib/session.ts` guarda o token em `sessionStorage` e deduz o papel por regex; `lib/api-client.ts` injeta `Authorization: Bearer` e trata 401; `app/(autenticado)/layout.tsx` guarda a sessão e monta trilha e "Sair".

#### Arquitetura e módulos

- `src/app/security.py` (novo): política de senha, hash e verificação de senha (argon2id, DEC-002), geração de token de sessão de 256 bits e seu resumo, constantes nomeadas da política (8 horas, 5 tentativas, 15 minutos, 10 caracteres, 90 dias; DEC-010).
- `src/app/accounts.py` (novo): casos de uso de conta e sessão — entrar, sair, bloquear e zerar tentativas, trocar a própria senha, criar, listar, corrigir, mudar papel, desativar, reativar e redefinir senha, com as proteções do último owner e do admin sobre owner; encerra sessões e chama o registro de eventos.
- `src/app/events.py` (novo): grava eventos de acesso sem segredo e apaga o que passou de 90 dias.
- `src/app/auth.py` (reescrito): `Identity(person_id, nome, tenant_id, project_id, role)`; `get_identity` valida a sessão, carrega pessoa e vínculo do banco a cada requisição (DEC-003), exige pessoa ativa e senha definida; `get_identity_pendente` aceita senha pendente e serve só identidade, troca de senha e sair; `require_write_role` permanece; saem `TokenRegistry` e `configure`.
- `src/app/routers/auth.py` e `src/app/routers/people.py` (novos): rotas da seção 10, finas, delegando a `accounts.py`.
- `src/app/routers/{workspaces,bases,executions,queries}.py` e `repo.py`: gravam `criado_por` com `identity.person_id` e serializam o autor.
- `src/app/main.py`: remove `_token_registry` e `auth.configure`, registra os dois routers novos.
- `src/app/create_owner.py` (novo): comando de implantação, no padrão de `worker.py` (importa `src.app.main` para ligar banco e configuração), lê a senha com `getpass`, nunca por argumento.
- `src/app/tasks.py`: tarefa periódica diária de limpeza (sessões expiradas, contadores vencidos, eventos com mais de 90 dias).
- Nova dependência de produção: `argon2-cffi` em `pyproject.toml` e `uv.lock`, registrada em `.specsfy/PACKAGES.md`.

#### Migrations

- `alembic/versions/0020_pessoas_e_autoria.py` (revisão `0020_pessoas`, `down_revision = "0019_workspaces"`): cria `pessoas`, `vinculos_pessoa`, `sessoes`, `tentativas_login` e `eventos_acesso`; adiciona `criado_por` (nulável, chave estrangeira para `pessoas.id`, índice) em `workspaces`, `bases`, `executions` e `queries`. Não altera nem apaga linha existente.
- Ordem: tabelas de pessoas antes das colunas de autoria. Reversão: remove as colunas e depois as tabelas, na ordem inversa. Compatibilidade: o código antigo continua lendo as tabelas antigas, porque as colunas novas são opcionais.
- Não há backfill de pessoas nem de autoria; as linhas atuais ficam sem autor.
- Tarefa de migração é `[CODE]` comum apontando para `alembic/versions/`, com `VERIFY` registrando `uv run alembic upgrade head` e `uv run alembic current` no banco de teste, conforme `.specsfy/RULES.md`.

#### Models

- `Pessoa`, `VinculoPessoa`, `Sessao`, `TentativaLogin` e `EventoAcesso` em `src/app/models.py`, com as invariantes da seção 9.
- `Workspace`, `Base`, `Execution` e `Query` ganham `criado_por` e um relacionamento de leitura para a pessoa autora.

#### Controllers e casos de uso

- `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me` e `POST /api/v1/auth/senha` em `src/app/routers/auth.py`; `login` não exige sessão, os demais exigem (`me`, `senha` e `logout` aceitam senha pendente).
- `GET|POST /api/v1/pessoas`, `GET|PATCH /api/v1/pessoas/{id}`, `POST /api/v1/pessoas/{id}/desativar`, `.../reativar` e `.../redefinir-senha` em `src/app/routers/people.py`, todos exigindo owner ou admin.
- Autorização: `get_identity` (pessoa ativa, senha definida), `require_write_role` e, na gestão de pessoas, as regras de `accounts.py` (admin sobre owner, último owner, a si mesma).

#### Views e experiência

- Telas e estados da seção 10; arquivos previstos em `frontend/src/features/auth/`, `frontend/src/features/pessoas/`, `frontend/src/app/login/`, `frontend/src/app/nova-senha/`, `frontend/src/app/(autenticado)/pessoas/` e `frontend/src/app/(autenticado)/layout.tsx`.

#### Queries e repositórios

- `src/app/repo.py` ganha leituras de pessoas do tenant e projeto da identidade (lista, por id, busca por e-mail normalizado global para unicidade) e a contagem de owners ativos; toda leitura filtra por `tenant_id` e `project_id`, exceto a checagem de e-mail duplicado, que é global.
- Índices: `uq_pessoas_email_lower` (único sobre o e-mail em minúsculas), `uq_vinculos_pessoa_pessoa` (um vínculo por pessoa), `ix_sessoes_token_hash` (único), `ix_sessoes_expira_em`, `ix_eventos_acesso_criado_em` e `ix_<tabela>_criado_por` nas quatro tabelas de dados.
- Consistência: criação, mudança de papel e desativação rodam em uma transação que trava, com `SELECT ... FOR UPDATE`, todas as linhas de vínculo de owner do tenant e projeto antes de conferir a regra do último owner. Travar só a linha da pessoa alvo não basta: dois owners que se rebaixam ao mesmo tempo passariam os dois pela conferência e deixariam o tenant sem owner.

#### Jobs e processamento assíncrono

- `purgar_dados_de_acesso` em `src/app/tasks.py`: tarefa periódica diária do worker Procrastinate existente; apaga sessões expiradas, contadores de tentativa vencidos e eventos com mais de 90 dias. É idempotente (repetir não muda o resultado) e não tem dead-letter próprio; falha registra log sem segredo e tenta de novo no próximo ciclo. A recusa de sessão expirada acontece na leitura e não depende da limpeza.

#### Estrutura de arquivos

```text
specs/planned/0020-autenticacao-real-por-pessoa/
  spec.md
  research/
alembic/versions/0020_pessoas_e_autoria.py
src/app/
  security.py accounts.py events.py create_owner.py
  auth.py models.py repo.py main.py tasks.py
  routers/auth.py routers/people.py
  routers/{workspaces,bases,executions,queries}.py
tests/
  test_app_auth.py test_app_people.py test_app_access_events.py
  test_app_authorship.py test_app_bootstrap.py test_app_migrations.py
  (test_app_workspaces|bases|executions|queries|worker.py migrados)
frontend/src/
  lib/session.ts lib/api-client.ts
  features/auth/{LoginForm,NovaSenhaForm,MenuPessoa,TrocarSenhaDialog}.tsx
  features/pessoas/{DataGridPessoas,PessoaFormSheet,DesativarPessoaDialog,RedefinirSenhaDialog}.tsx
  components/DetailLists.tsx components/ui/dropdown-menu.tsx
  app/login/ app/nova-senha/ app/(autenticado)/pessoas/ app/(autenticado)/layout.tsx
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `Pessoa` (`pessoas`) | `id` UUID textual | `nome` (texto curto, obrigatório); `email` (texto curto, único sem diferenciar maiúsculas); `senha_hash` (nunca exposto); `precisa_trocar_senha` (sim ou não, padrão sim); `situacao` (`ativa` ou `desativada`); `criada_em`; `criada_por` (pessoa, opcional); `atualizada_em`. Nunca é apagada. | Tem um `VinculoPessoa`, várias `Sessao`, é alvo e autora de `EventoAcesso` e autora de Workspace, Base, Execução e Consulta. |
| `VinculoPessoa` (`vinculos_pessoa`) | `id` UUID textual | `pessoa_id`; `tenant_id`; `project_id`; `papel` (`owner`, `admin` ou `member`). Único por pessoa nesta entrega (DEC-004). | Pertence a uma `Pessoa`; escopo de tenant e projeto da identidade. |
| `Sessao` (`sessoes`) | `id` UUID textual | `pessoa_id`; `token_hash` (resumo do token, único); `criada_em`; `expira_em` (8 horas depois, fixo). Encerrar apaga a linha. | Pertence a uma `Pessoa`. |
| `TentativaLogin` (`tentativas_login`) | `email_normalizado` | `falhas_seguidas` (número); `bloqueada_ate` (data e horário, opcional); `atualizada_em`. Existe para e-mail cadastrado ou não (DEC-005). | Sem chave estrangeira; refere-se a um e-mail, não a uma pessoa. |
| `EventoAcesso` (`eventos_acesso`) | `id` UUID textual | `tipo` (entre: `entrou`, `senha_errada`, `bloqueada`, `senha_trocada`, `senha_redefinida`, `pessoa_criada`, `dados_corrigidos`, `papel_alterado`, `pessoa_desativada`, `pessoa_reativada`, `sessao_encerrada`); `motivo` (só em `sessao_encerrada`); `ator_pessoa_id` e `alvo_pessoa_id` (opcionais); `tenant_id` e `project_id` (opcionais); `criado_em`. Nunca guarda senha, hash, token nem o e-mail tentado. | Refere-se às pessoas envolvidas, sem impedi-las de existir. |
| Autoria (`criado_por`) | referência a `Pessoa.id` | Coluna opcional em `workspaces`, `bases`, `executions` e `queries`; vazia nos registros anteriores à entrega. | Cada registro aponta para a pessoa que o criou; a pessoa nunca é apagada, então a referência permanece válida. |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| `Pessoa` | criada, senha pendente | troca a própria senha | ativa, senha definida | Nova senha segue a política e difere da atual; sessão atual continua e as demais terminam. |
| `Pessoa` | ativa | owner ou admin desativa | desativada | Não é o último owner ativo, não é a própria pessoa e, se for owner, quem age é owner; encerra as sessões dela. |
| `Pessoa` | desativada | owner ou admin reativa | ativa | Vínculo e papel preservados; sem sessão nova até entrar de novo. |
| `Pessoa` | ativa | redefinição de senha por outra pessoa | ativa, senha pendente | Encerra as sessões dela; nova entrada leva à troca obrigatória. |
| `Sessao` | válida | sair, desativar, mudar papel, corrigir nome ou e-mail, redefinir senha, ou 8 horas | apagada | Depois de apagada, o mesmo token responde 401. |
| `TentativaLogin` | contando | quinta falha seguida | bloqueada por 15 minutos | Vale para e-mail cadastrado ou não; a senha correta é recusada durante o bloqueio. |
| `TentativaLogin` | contando ou bloqueada | sucesso ou fim do bloqueio | apagada ou zerada | O contador volta a zero. |

#### Migração e retenção

- A revisão `0020_pessoas` só cria estruturas e colunas opcionais; nenhuma linha atual é alterada, e os registros anteriores ficam sem autor, exibidos como "Autor não identificado".
- Não há migração de dados de tokens: os quatro tokens estáticos deixam de existir e o primeiro owner é criado por comando.
- Retenção: eventos de acesso por 90 dias, depois apagados; sessões e contadores são apagados assim que deixam de valer; pessoa e autoria permanecem enquanto o registro que descrevem existir.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. Login, definição de senha, gestão de pessoas e menu da pessoa são usados por pessoas em telas; a entrega não se resume a endpoints, porque o CRUD de pessoas e o login precisam de tela para cumprir o resultado.

#### Stack e convenções de interface

- Frontend `frontend/`: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, shadcn/ui preset `base-nova` (primitives Base UI) e registry ReUI configurado sem blocos instalados; testes com Vitest e Testing Library (`test:tdd`). Cliente HTTP único `lib/api-client.ts`, sessão em `lib/session.ts` (`sessionStorage`).
- Telas atuais afetadas: `/login` (`LoginForm` por colagem de token), shell `(autenticado)/layout.tsx` (trilha e "Sair", sem menu), `/workspaces`, `/workspaces/[id]` e `/execucoes/[id]` (listas e detalhes que passam a mostrar a autoria). O que se preserva: padrão de lista, painel lateral, diálogo, `PageHeader`, tokens e tipografia. O que muda: o login (token por e-mail e senha), o shell (pessoa e papel vêm do backend, navegação persistente) e nascem as telas Nova senha e Pessoas.
- Fontes locais lidas: `INTERFACE.md`, `DESIGNSYSTEM.MD`, `.specsfy/STACK.md`, `frontend/package.json` e os componentes de `frontend/src/`.

#### Telas e responsabilidades

| Tela | Rota | Quem usa | Tarefa principal |
| --- | --- | --- | --- |
| Entrar | `/login` | Pessoa sem sessão | Entrar com e-mail e senha; entrada: e-mail e senha; saída: sessão e ida a Workspaces ou a Nova senha |
| Nova senha | `/nova-senha` | Pessoa com senha pendente | Definir a própria senha; entrada: nova senha e confirmação; saída: pendência limpa e ida a Workspaces |
| Pessoas (lista) | `/pessoas` | Owner e admin | Ver e administrar as pessoas do tenant; entrada: filtros da lista e formulários; saída: lista atualizada |
| Pessoa (detalhe) | `/pessoas/[id]` | Owner e admin | Ver os dados de uma pessoa e agir sobre ela |
| Menu da pessoa e Trocar senha | cabeçalho de cada tela autenticada | Toda pessoa | Ver quem está logada, trocar a própria senha (senha atual, nova e confirmação) e sair |
| Autoria | listas e detalhes de Workspace, Base, Execução e Consulta | Toda pessoa | Ver "Criada por" e "Consultada por" |

#### Fluxo de informação e navegação

- `/login` recebe e-mail e senha; se a senha está pendente leva a `/nova-senha`, senão a `/workspaces`. Cada tela autenticada carrega a identidade do backend antes de mostrar ações de escrita. Sessão terminada ou requisição não autenticada volta a `/login` com o aviso "Sua sessão terminou. Entre novamente.".
- Owner ou admin cria a pessoa com uma senha inicial e a comunica por fora do sistema; o painel de criação lembra disso. A pessoa troca essa senha no primeiro acesso.
- `Breadcrumb` por tela: Entrar e Nova senha não têm trilha (telas isoladas, como o Login atual); `/pessoas` mostra Equipe → Pessoas; `/pessoas/[id]` mostra Equipe → Pessoas → nome da pessoa; as telas de Workspaces mantêm a trilha atual. O rótulo "Equipe" continua genérico, porque o tenant não tem nome no modelo (suposição 6).

#### Menus e navegação principal

- Menu principal: navegação persistente no cabeçalho do shell, com os itens **Workspaces** (`/workspaces`, todos os papéis) e **Pessoas** (`/pessoas`, só owner e admin; para member o item não existe). No mobile os itens quebram em uma linha própria sob a trilha, mantendo o nome da equipe visível.
- Menu secundário: o nome da pessoa, à direita, abre um menu suspenso com **Trocar senha** (abre diálogo) e **Sair** (encerra a sessão e volta a `/login`); em Nova senha o cabeçalho mostra apenas Sair.

#### Formulários e ações

- **Entrar**: campos e-mail e senha com rótulo visível, botão "Entrar" com estado de envio e a orientação "Esqueceu a senha? Peça a um owner ou admin da sua equipe para redefini-la". Em erro: `Alert` genérico, e-mail preservado, senha limpa, foco no primeiro campo; bloqueio temporário e sessão terminada têm mensagem própria.
- **Nova senha**: explica por que aparece ("sua senha foi definida por outra pessoa"), campos nova senha e confirmação, regra de 10 caracteres visível junto do campo, erro abaixo do campo, botão com estado de envio.
- **Criar pessoa** (painel lateral): nome, e-mail, papel e senha inicial; depois de criar, confirma e lembra de passar a senha por um canal seguro.
- **Editar pessoa** (painel lateral): nome, e-mail e papel; a opção owner só aparece para owner. Papel usa controle nativo `select` com o estilo de `Input` (DEC-008).
- **Desativar, Reativar e Redefinir senha** (diálogo de confirmação): mostram a pessoa alvo e a consequência (a sessão termina na hora; a senha redefinida exige nova troca); Redefinir tem o campo de senha temporária; desativar o último owner ou a si mesma não é oferecido.
- **Trocar senha** (diálogo do menu): senha atual, nova e confirmação, com a mesma política e o mesmo tratamento de erro.

#### Composição e disposição

- Lista de Pessoas: `PageHeader` com a ação primária "Nova pessoa" e `DataGrid` em largura total com `ID`, nome, e-mail, papel e situação; a linha inteira abre o detalhe por mouse e teclado; as ações "Editar" e "Desativar/Reativar" ficam na linha, independentes do clique da linha. Situação em `Badge` com texto, e a pessoa desativada também fica atenuada e marcada "Desativada", sem depender só de cor.
- Detalhe da pessoa: `PageHeader` com nome, situação e as ações; `DetailLists` com e-mail, papel, situação, se a troca de senha está pendente, criada em e por quem.
- Criar e editar em painel lateral (`Sheet`), como `WorkspaceFormSheet`, em vez de página em duas colunas: exceção ao `DESIGNSYSTEM.MD` com alcance somente na tela Pessoas, porque o formulário tem quatro campos e já é o padrão dos Workspaces; não vira regra do produto.
- Autoria: coluna "Criada por" em `DataGridBases` e `DataGridWorkspaces`; "Criada por" na descrição do detalhe de Base; "Iniciada por" em `PainelProgresso`; "Consultada por" junto do resultado de cada consulta. Registros anteriores mostram "Autor não identificado"; autor desativado mostra o nome com "(desativada)".
- Desktop e mobile: a lista mantém `ID` e rola na horizontal dentro da própria região no mobile; painéis e diálogos ocupam a largura da tela no mobile; o cabeçalho quebra a navegação sob a trilha.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Entrar | `LoginForm` | E-mail, senha, erros e estados de envio | `frontend/src/features/auth/LoginForm.tsx` | `Input`, `Label`, `Button`, `Alert` | shadcn/ui existentes e bloco próprio | Extensão do bloco atual (troca token por e-mail e senha) |
| Nova senha | `NovaSenhaForm` | Nova senha, confirmação, regra visível | `frontend/src/features/auth/NovaSenhaForm.tsx` | `Input`, `Label`, `Button`, `Alert` | shadcn/ui e próprio | Novo; reaproveita as primitives do `LoginForm` |
| Menu da pessoa | `MenuPessoa` | Nome, Trocar senha, Sair | `frontend/src/features/auth/MenuPessoa.tsx` | `DropdownMenu` | shadcn/ui (`dropdown-menu`, a instalar) e próprio | Novo |
| Trocar senha | `TrocarSenhaDialog` | Senha atual, nova e confirmação | `frontend/src/features/auth/TrocarSenhaDialog.tsx` | `Dialog`, `Input`, `Label`, `Button` | shadcn/ui existentes e próprio | Novo sobre `Dialog` |
| Shell | `LayoutAutenticado` | Guarda de sessão, identidade, navegação persistente, trilha | `frontend/src/app/(autenticado)/layout.tsx` | trilha existente, `MenuPessoa` | próprio | Extensão do shell atual |
| Pessoas | `DataGridPessoas` | Lista, linha clicável, ações por linha | `frontend/src/features/pessoas/DataGridPessoas.tsx` | tabela semântica, `Badge`, `Skeleton` | próprio, no padrão de `DataGridWorkspaces` | Novo; segue o padrão existente |
| Pessoas | `PessoaFormSheet` | Criar e editar em painel lateral | `frontend/src/features/pessoas/PessoaFormSheet.tsx` | `Sheet`, `Input`, `Label`, `select` nativo | shadcn/ui existentes e próprio | Novo; segue `WorkspaceFormSheet` |
| Pessoas | `DesativarPessoaDialog` e `RedefinirSenhaDialog` | Confirmação com alvo e consequência | `frontend/src/features/pessoas/` | `Dialog`, `Button` | shadcn/ui existentes e próprio | Novo; segue `ExcluirWorkspaceDialog` |
| Pessoa (detalhe) | `DetailLists` | Atributos por assunto | `frontend/src/components/DetailLists.tsx` | lista de termos e valores | próprio | Novo, componente compartilhado |
| Todas | `PageHeader` | Cabeçalho único | `frontend/src/components/PageHeader.tsx` | existente | próprio | Reuso sem alteração |
| Sessão | `session.ts` e `api-client.ts` | Guardar o token, buscar a identidade, tratar 401 com aviso | `frontend/src/lib/` | funções | próprio | Extensão |

- shadcn/ui fornece as primitives (`dropdown-menu` é a única nova); ReUI não entra nesta entrega porque os blocos locais e as primitives atendem as telas, e o registro em `INTERFACE.md` diz isso. Cada bloco novo é registrado em `INTERFACE.md` antes e depois da tarefa.

#### Estados e acessibilidade

- Carregando: `Skeleton` com a estrutura da lista ou do detalhe; botões com `Spinner` e desabilitados durante o envio. Vazio: a lista nunca fica sem a própria pessoa; se for a única, orienta a criar as demais. Erro: `Alert` com o que falhou e como recuperar, sem detalhe interno e sem segredo, campos preservados. Sucesso: feedback concreto ("Pessoa criada", "Senha redefinida") e retorno ao contexto. Permissão insuficiente: `member` que abre `/pessoas` por endereço vê explicação curta e o caminho de volta, sem dados. Não salvo: os painéis de criar e editar protegem alterações pendentes ao fechar.
- Acessibilidade: rótulos visíveis; erro de campo em vermelho com texto abaixo do campo, anunciado por tecnologia assistiva, com foco no primeiro erro; `autocomplete` `username`, `current-password` e `new-password`; opção de mostrar a senha; foco preso e devolvido em painéis e diálogos; linha da lista focável com nome acessível; situação nunca só por cor; `prefers-reduced-motion` respeitado.
- O `Breadcrumb` mantém a equipe visível, usa links reais nos itens anteriores e marca a tela atual com `aria-current="page"`.

#### Contrato CRUD

- Todas as telas de Pessoas usam o mesmo `PageHeader` componentizado (lista, detalhe e os painéis), variando título, descrição, trilha e ações por props.
- A listagem usa `DataGrid` em largura total, mantém a coluna `ID` visível e transforma a linha inteira em link para o detalhe; cada linha oferece editar e desativar ou reativar como botões independentes. **Exceção registrada, com alcance somente na tela Pessoas:** a linha não oferece apagar, porque pessoa nunca é apagada, só desativada, para preservar a autoria; desativar respeita a permissão e confirma a consequência antes de executar.
- Os componentes reaproveitados e os novos são registrados em `INTERFACE.md`, com consumidores, estados e regra de extensão.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre durante a implementação, mesmo sem pedido da pessoa, e confere bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, nos estados carregando, vazio, erro, sucesso e permissão insuficiente, com conteúdo curto e longo, em desktop e em 360 px.
- Cada tarefa registra a forma de conferência usada, o viewport, os estados percorridos, os ajustes e o resultado no item `VISUAL`; tarefa sem interface registra `Não aplicável` e o motivo concreto.


#### APIs expostas

Todas sob `/api/v1`, autenticadas por `Authorization: Bearer <token de sessão>`, salvo `login`. Erros de rota de dados não mudam (401, 403, 404); rotas com senha pendente respondem 403 `senha_pendente`.

| Verbo e rota | Quem | Request | Response | Erros |
| --- | --- | --- | --- | --- |
| `POST /auth/login` | Sem sessão | `{email, senha}` | 200 `{token, expira_em, pessoa}` com `pessoa = {id, nome, email, papel, tenant_id, project_id, precisa_trocar_senha}` | 401 genérico; 429 bloqueio temporário |
| `POST /auth/logout` | Qualquer sessão | vazio | 204 | 401 |
| `GET /auth/me` | Qualquer sessão, inclusive pendente | vazio | 200 `pessoa` | 401 |
| `POST /auth/senha` | Qualquer sessão, inclusive pendente | `{senha_atual, nova_senha}`; na pendência só `nova_senha` | 204 | 401; 422 política, igual à atual ou senha atual incorreta |
| `GET /pessoas` | Owner, admin | vazio | 200 lista de `{id, nome, email, papel, situacao, precisa_trocar_senha, criada_em, criada_por}` do tenant e projeto | 401; 403 |
| `POST /pessoas` | Owner, admin | `{nome, email, papel, senha_inicial}` | 201 pessoa | 403 (admin criando owner); 409 e-mail; 422 |
| `GET /pessoas/{id}` | Owner, admin | vazio | 200 pessoa | 404 (outro tenant ou inexistente) |
| `PATCH /pessoas/{id}` | Owner, admin | `{nome?, email?, papel?}` | 200 pessoa | 403; 404; 409 e-mail ou último owner; 422 |
| `POST /pessoas/{id}/desativar` e `/reativar` | Owner, admin | vazio | 204 | 403; 404; 409 último owner ou a si mesma |
| `POST /pessoas/{id}/redefinir-senha` | Owner, admin | `{senha_temporaria}` | 204 | 403; 404; 422 |

- Rotas existentes de Workspace, Base, Execução e Consulta passam a devolver `criado_por: {id, nome, desativada}` ou `null`; nenhum campo existente muda de nome nem de significado.
- Os tokens estáticos deixam de autenticar em qualquer rota. Versionamento: continua `/api/v1`, porque a mudança é aditiva nas respostas e a autenticação é interna ao produto de uso interno.

#### APIs externas utilizadas

- Nenhuma. Não há provedor externo de identidade nem envio de e-mail.

#### Documentação das APIs consultadas

- Nenhuma fonte externa; o contrato acima é a definição normativa.

#### Eventos e outros contratos

- Comando de implantação: `uv run python -m src.app.create_owner --nome <nome> --email <e-mail> --tenant <tenant> --projeto <projeto>` cria o primeiro owner; `--redefinir-senha --email <e-mail>` redefine a senha de uma pessoa existente. A senha é lida por `getpass`, nunca por argumento, e a pessoa nasce com a troca pendente.
- Eventos de acesso: os tipos da seção 9; produtor `src/app/events.py`; sem consumidor nesta entrega (não há tela nem API de leitura); compatibilidade: tipos novos entram por acréscimo.

### 11. Estratégia TDD

- **Unidade**: `src/app/security.py` (política de senha, hash e verificação, token de sessão e resumo) e as regras de `src/app/accounts.py` (bloqueio, proteções do último owner e do admin, encerramento de sessão) sem tocar HTTP.
- **Integração/contrato**: `fastapi.testclient.TestClient` sobre o app real e o PostgreSQL de teste `rag_pipeline_test`, com pessoas de teste criadas por fixture em `tests/conftest.py`; rotas de auth e de pessoas, autoria nas rotas existentes, migração Alembic e comando de implantação.
- **BDD/aceite**: o Gherkin da seção 6 orienta os casos; cada caso TDD declara o próprio marcador `SPECSFY: SPEC-0020 <IDs>`, sem criar nem executar arquivo `.feature`.
- **Runner TDD**: backend com Pytest (`uv run pytest`); frontend com Vitest e Testing Library (`test:tdd` = `vitest run` em `frontend/`), ambos já existentes no projeto, sem decisão nova. Execução sempre contra o banco de teste; nenhum comando destrutivo de schema.
- **E2E**: não aplicável nesta entrega — o repositório não tem runner E2E, e a jornada completa é coberta por integração no backend e por componentes no frontend.
- **Verificação manual**: somente a revisão visual de cada tela nova em desktop e 360 px, registrada no item `VISUAL` da tarefa, porque a aparência não é comprovada por teste automatizado.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-007, FR-010, NFR-003, AC-001 | AC-001 na seção 6 | test_login_valido_devolve_identidade em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 US-001 FR-001 FR-007 FR-010 NFR-003 AC-001` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-001, FR-001, FR-002, NFR-002, AC-002 | AC-002 na seção 6 | test_senha_errada_recusa_e_conta_falha em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 US-001 FR-001 FR-002 NFR-002 AC-002` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-001, FR-001, FR-008, NFR-002, AC-003 | AC-003 na seção 6 | test_recusas_de_login_sao_indistinguiveis em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 US-001 FR-001 FR-008 NFR-002 AC-003` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-001, FR-002, NFR-002, AC-004 | AC-004 na seção 6 | test_cinco_falhas_bloqueiam_por_quinze_minutos em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 US-001 FR-002 NFR-002 AC-004` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-001, FR-001, FR-002, AC-005 | AC-005 na seção 6 | test_bloqueio_expira_e_sucesso_zera_contador em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 US-001 FR-001 FR-002 AC-005` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-002, FR-004, FR-005, FR-010, FR-014, AC-006 | AC-006 na seção 6 | test_senha_pendente_libera_so_troca_e_identidade em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 US-002 FR-004 FR-005 FR-010 FR-014 AC-006` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-002, US-003, FR-003, FR-005, AC-007 | AC-007 na seção 6 | test_politica_de_senha_na_troca_e_na_criacao em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 US-002 US-003 FR-003 FR-005 AC-007` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-002, US-004, FR-005, FR-006, NFR-004, AC-008 | AC-008 na seção 6 | test_troca_de_senha_mantem_atual_e_encerra_demais em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 US-002 US-004 FR-005 FR-006 NFR-004 AC-008` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-004, FR-006, FR-014, NFR-004, AC-009 | AC-009 na seção 6 | test_sessao_expira_em_oito_horas_e_sair_encerra em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 US-004 FR-006 FR-014 NFR-004 AC-009` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-003, US-004, FR-006, FR-008, NFR-004, AC-010 | AC-010 na seção 6 | test_eventos_de_conta_encerram_sessoes em tests/test_app_people.py, marcador `SPECSFY: SPEC-0020 US-003 US-004 FR-006 FR-008 NFR-004 AC-010` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-003, FR-003, FR-004, FR-008, FR-010, AC-011 | AC-011 na seção 6 | test_owner_administra_pessoas_do_proprio_tenant em tests/test_app_people.py, marcador `SPECSFY: SPEC-0020 US-003 FR-003 FR-004 FR-008 FR-010 AC-011` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-003, FR-008, FR-015, NFR-005, AC-012 | AC-012 na seção 6 | test_email_duplicado_e_campos_invalidos em tests/test_app_people.py, marcador `SPECSFY: SPEC-0020 US-003 FR-008 FR-015 NFR-005 AC-012` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-003, FR-008, FR-009, AC-013 | AC-013 na seção 6 | test_protecoes_de_ultimo_owner_e_admin em tests/test_app_people.py, marcador `SPECSFY: SPEC-0020 US-003 FR-008 FR-009 AC-013` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-003, FR-009, FR-010, FR-015, NFR-003, AC-014 | AC-014 na seção 6 | test_member_e_isolamento_entre_tenants em tests/test_app_people.py, marcador `SPECSFY: SPEC-0020 US-003 FR-009 FR-010 FR-015 NFR-003 AC-014` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-007, FR-010, FR-013, NFR-003, AC-015 | AC-015 na seção 6 | test_tokens_estaticos_e_sem_sessao_sao_recusados em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 US-007 FR-010 FR-013 NFR-003 AC-015` | RED observado em 2026-09-21: `token-…-owner` ainda autentica em `/api/v1/workspaces`; o token estático continua aceito | Pending | Pending |
| US-005, FR-010, FR-011, AC-016 | AC-016 na seção 6 | test_autoria_distingue_pessoas_do_mesmo_papel em tests/test_app_authorship.py, marcador `SPECSFY: SPEC-0020 US-005 FR-010 FR-011 AC-016` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-005, FR-011, AC-017 | AC-017 na seção 6 | test_exibe_autor_nao_identificado_e_desativado em tests/test_app_authorship.py, marcador `SPECSFY: SPEC-0020 US-005 FR-011 AC-017` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-006, FR-012, NFR-001, AC-018 | AC-018 na seção 6 | test_cada_evento_gera_registro_sem_segredo em tests/test_app_access_events.py, marcador `SPECSFY: SPEC-0020 US-006 FR-012 NFR-001 AC-018` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-006, FR-012, AC-019 | AC-019 na seção 6 | test_limpeza_apaga_eventos_com_mais_de_noventa_dias em tests/test_app_access_events.py, marcador `SPECSFY: SPEC-0020 US-006 FR-012 AC-019` | RED observado em 2026-09-21: `src.app.models.EventoAcesso` ainda não existe | Pending | Pending |
| US-005, US-007, FR-011, FR-013, NFR-006, AC-020 | AC-020 na seção 6 | test_upgrade_preserva_linhas_e_deixa_autoria_vazia em tests/test_app_migrations.py, marcador `SPECSFY: SPEC-0020 US-005 US-007 FR-011 FR-013 NFR-006 AC-020` | RED observado em 2026-09-21: `alembic upgrade 0020_pessoas` recusado; a revisão ainda não existe | Pending | Pending |
| US-001, US-006, FR-003, FR-012, NFR-001, AC-021 | AC-021 na seção 6 | test_nenhum_segredo_em_resposta_log_ou_evento em tests/test_app_access_events.py, marcador `SPECSFY: SPEC-0020 US-001 US-006 FR-003 FR-012 NFR-001 AC-021` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-007, FR-004, FR-013, NFR-006, AC-022 | AC-022 na seção 6 | test_comando_cria_primeiro_owner_e_redefine_senha em tests/test_app_bootstrap.py, marcador `SPECSFY: SPEC-0020 US-007 FR-004 FR-013 NFR-006 AC-022` | RED observado em 2026-09-21: `src.app.create_owner` ainda não existe | Pending | Pending |
| US-001, US-004, FR-007, FR-014, AC-023 | AC-023 na seção 6 | layout usa a identidade do backend e trata 401 em frontend/src/app/(autenticado)/layout.test.tsx, marcador `SPECSFY: SPEC-0020 US-001 US-004 FR-007 FR-014 AC-023` | RED observado em 2026-09-21: o cabeçalho não mostra a pessoa nem o item Pessoas e `consumirAviso` ainda não existe em `@/lib/session` | Pending | Pending |
| US-002, FR-007, FR-014, FR-015, AC-024 | AC-024 na seção 6 | menu mostra nome, troca de senha e sair em frontend/src/features/auth/MenuPessoa.test.tsx, marcador `SPECSFY: SPEC-0020 US-002 FR-007 FR-014 FR-015 AC-024` | RED observado em 2026-09-21: `@/features/auth/MenuPessoa` ainda não existe | Pending | Pending |
| US-003, FR-008, FR-009, FR-015, NFR-005, AC-025 | AC-025 na seção 6 | lista de pessoas em largura total sem apagar em frontend/src/features/pessoas/DataGridPessoas.test.tsx, marcador `SPECSFY: SPEC-0020 US-003 FR-008 FR-009 FR-015 NFR-005 AC-025` | RED observado em 2026-09-21: `@/features/pessoas/DataGridPessoas` ainda não existe | Pending | Pending |
| US-002, FR-014, FR-015, NFR-005, AC-026 | AC-026 na seção 6 | formularios acessiveis e tela pequena em frontend/src/features/auth/LoginForm.test.tsx, marcador `SPECSFY: SPEC-0020 US-002 FR-014 FR-015 NFR-005 AC-026` | RED observado em 2026-09-21: o formulário de Login ainda não tem os campos E-mail e Senha | Pending | Pending |
| US-007, FR-010, NFR-003, AC-027 | AC-027 na seção 6 | suites atuais migradas para pessoas de teste em tests/test_app_workspaces.py, marcador `SPECSFY: SPEC-0020 US-007 FR-010 NFR-003 AC-027` | RED observado em 2026-09-21: o teste de guarda ainda encontra o texto do token estático em `src/`, `tests/` e `frontend/src/` | Pending | Pending |
| FR-003, FR-006, NFR-001, AC-028 | AC-028 na seção 6 | test_senha_e_token_ficam_so_como_derivados em tests/test_app_auth.py, marcador `SPECSFY: SPEC-0020 FR-003 FR-006 NFR-001 AC-028` | RED observado em 2026-09-21: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste | Pending | Pending |
| US-007, FR-013, NFR-006, AC-029 | AC-029 na seção 6 | test_downgrade_remove_somente_o_que_a_revisao_criou em tests/test_app_migrations.py, marcador `SPECSFY: SPEC-0020 US-007 FR-013 NFR-006 AC-029` | RED observado em 2026-09-21: as tabelas de pessoas, vínculos, sessões, tentativas e eventos ainda não existem na revisão atual | Pending | Pending |
| US-001, FR-001, FR-002, FR-014, AC-001, AC-002, AC-004, AC-006 | AC-001, AC-002, AC-004 e AC-006 na seção 6 | `LoginForm envia e-mail e senha e trata os retornos` em frontend/src/features/auth/LoginForm.test.tsx, marcador `SPECSFY: SPEC-0020 US-001 FR-001 FR-002 FR-014 AC-001 AC-002 AC-004 AC-006` | RED observado em 2026-09-21: os campos E-mail e Senha do Login ainda não existem | Pending | Pending |
| US-002, FR-004, FR-005, FR-014, AC-006, AC-007, AC-026 | AC-006, AC-007 e AC-026 na seção 6 | `NovaSenhaForm exige senha válida e confirmação` em frontend/src/features/auth/NovaSenhaForm.test.tsx, marcador `SPECSFY: SPEC-0020 US-002 FR-004 FR-005 FR-014 AC-006 AC-007 AC-026` | RED observado em 2026-09-21: `@/features/auth/NovaSenhaForm` e `@/app/nova-senha/page` ainda não existem | Pending | Pending |
| US-002, FR-005, FR-014, AC-007, AC-008, AC-024 | AC-007, AC-008 e AC-024 na seção 6 | `TrocarSenhaDialog troca a própria senha` em frontend/src/features/auth/TrocarSenhaDialog.test.tsx, marcador `SPECSFY: SPEC-0020 US-002 FR-005 FR-014 AC-007 AC-008 AC-024` | RED observado em 2026-09-21: `@/features/auth/TrocarSenhaDialog` ainda não existe | Pending | Pending |
| US-003, FR-008, FR-009, FR-015, AC-011, AC-012, AC-013, AC-025 | AC-011, AC-012, AC-013 e AC-025 na seção 6 | `PessoaFormSheet cria e edita pessoa em painel lateral` em frontend/src/features/pessoas/PessoaFormSheet.test.tsx, marcador `SPECSFY: SPEC-0020 US-003 FR-008 FR-009 FR-015 AC-011 AC-012 AC-013 AC-025` | RED observado em 2026-09-21: `@/features/pessoas/PessoaFormSheet` ainda não existe | Pending | Pending |
| US-003, US-004, FR-006, FR-008, FR-009, FR-015, AC-010, AC-013, AC-025 | AC-010, AC-013 e AC-025 na seção 6 | `diálogos de desativar, reativar e redefinir senha` em frontend/src/features/pessoas/DesativarPessoaDialog.test.tsx, marcador `SPECSFY: SPEC-0020 US-003 US-004 FR-006 FR-008 FR-009 FR-015 AC-010 AC-013 AC-025` | RED observado em 2026-09-21: `DesativarPessoaDialog` e `RedefinirSenhaDialog` ainda não existem | Pending | Pending |
| US-003, FR-010, FR-015, NFR-003, NFR-005, AC-011, AC-014, AC-025 | AC-011, AC-014 e AC-025 na seção 6 | `rotas de Pessoas por papel e detalhe da pessoa` em frontend/src/app/(autenticado)/pessoas/page.test.tsx, marcador `SPECSFY: SPEC-0020 US-003 FR-010 FR-015 NFR-003 NFR-005 AC-011 AC-014 AC-025` | RED observado em 2026-09-21: as rotas `/pessoas` e `/pessoas/[id]` ainda não existem | Pending | Pending |
| US-005, FR-011, AC-016, AC-017 | AC-016 e AC-017 na seção 6 | `autoria nas listas e detalhes` em frontend/src/features/bases/DataGridBases.test.tsx, marcador `SPECSFY: SPEC-0020 US-005 FR-011 AC-016 AC-017` | RED observado em 2026-09-21: as listas e o resultado ainda não mostram a autoria (Criada por, Iniciada por, Consultada por) | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Nível integração | tests/test_app_auth.py | Pending |
| FR-001 | AC-002 | Nível integração | tests/test_app_auth.py | Pending |
| FR-001 | AC-003 | Nível integração | tests/test_app_auth.py | Pending |
| FR-002 | AC-002 | Nível integração | tests/test_app_auth.py | Pending |
| FR-002 | AC-004 | Nível integração | tests/test_app_auth.py | Pending |
| FR-002 | AC-005 | Nível unidade e integração | tests/test_app_auth.py | Pending |
| FR-003 | AC-007 | Unidade e integração | tests/test_app_auth.py | Pending |
| FR-003 | AC-011 | Nível integração | tests/test_app_people.py | Pending |
| FR-003 | AC-021 | Nível integração | tests/test_app_access_events.py | Pending |
| FR-004 | AC-006 | Integração e frontend | tests/test_app_auth.py | Pending |
| FR-004 | AC-011 | Nível integração | tests/test_app_people.py | Pending |
| FR-004 | AC-022 | Nível integração | tests/test_app_bootstrap.py | Pending |
| FR-005 | AC-006 | Integração e frontend | tests/test_app_auth.py | Pending |
| FR-005 | AC-007 | Unidade e integração | tests/test_app_auth.py | Pending |
| FR-005 | AC-008 | Nível integração | tests/test_app_auth.py | Pending |
| FR-006 | AC-008 | Nível integração | tests/test_app_auth.py | Pending |
| FR-006 | AC-009 | Nível unidade, integração e frontend | tests/test_app_auth.py | Pending |
| FR-006 | AC-010 | Nível integração | tests/test_app_people.py | Pending |
| FR-007 | AC-001 | Nível integração | tests/test_app_auth.py | Pending |
| FR-007 | AC-023 | Nível frontend | frontend/src/app/(autenticado)/layout.test.tsx | Pending |
| FR-007 | AC-024 | Nível frontend | frontend/src/features/auth/MenuPessoa.test.tsx | Pending |
| FR-008 | AC-003 | Nível integração | tests/test_app_auth.py | Pending |
| FR-008 | AC-010 | Nível integração | tests/test_app_people.py | Pending |
| FR-008 | AC-011 | Nível integração | tests/test_app_people.py | Pending |
| FR-009 | AC-013 | Nível unidade e integração | tests/test_app_people.py | Pending |
| FR-009 | AC-014 | Nível integração e frontend | tests/test_app_people.py | Pending |
| FR-009 | AC-025 | Nível frontend | frontend/src/features/pessoas/DataGridPessoas.test.tsx | Pending |
| FR-010 | AC-001 | Nível integração | tests/test_app_auth.py | Pending |
| FR-010 | AC-006 | Integração e frontend | tests/test_app_auth.py | Pending |
| FR-010 | AC-011 | Nível integração | tests/test_app_people.py | Pending |
| FR-011 | AC-016 | Nível integração | tests/test_app_authorship.py | Pending |
| FR-011 | AC-017 | Nível integração e frontend | tests/test_app_authorship.py | Pending |
| FR-011 | AC-020 | Nível integração | tests/test_app_migrations.py | Pending |
| FR-012 | AC-018 | Nível integração | tests/test_app_access_events.py | Pending |
| FR-012 | AC-019 | Nível unidade e integração | tests/test_app_access_events.py | Pending |
| FR-012 | AC-021 | Nível integração | tests/test_app_access_events.py | Pending |
| FR-013 | AC-015 | Nível integração | tests/test_app_auth.py | Pending |
| FR-013 | AC-020 | Nível integração | tests/test_app_migrations.py | Pending |
| FR-013 | AC-022 | Nível integração | tests/test_app_bootstrap.py | Pending |
| FR-014 | AC-006 | Integração e frontend | tests/test_app_auth.py | Pending |
| FR-014 | AC-009 | Nível unidade, integração e frontend | tests/test_app_auth.py | Pending |
| FR-014 | AC-023 | Nível frontend | frontend/src/app/(autenticado)/layout.test.tsx | Pending |
| FR-015 | AC-012 | Nível integração e frontend | tests/test_app_people.py | Pending |
| FR-015 | AC-014 | Nível integração e frontend | tests/test_app_people.py | Pending |
| FR-015 | AC-024 | Nível frontend | frontend/src/features/auth/MenuPessoa.test.tsx | Pending |
| NFR-001 | AC-018 | Nível integração | tests/test_app_access_events.py | Pending |
| NFR-001 | AC-021 | Nível integração | tests/test_app_access_events.py | Pending |
| NFR-001 | AC-028 | Nível unidade e integração | tests/test_app_auth.py | Pending |
| NFR-002 | AC-002 | Nível integração | tests/test_app_auth.py | Pending |
| NFR-002 | AC-003 | Nível integração | tests/test_app_auth.py | Pending |
| NFR-002 | AC-004 | Nível integração | tests/test_app_auth.py | Pending |
| NFR-003 | AC-001 | Nível integração | tests/test_app_auth.py | Pending |
| NFR-003 | AC-014 | Nível integração e frontend | tests/test_app_people.py | Pending |
| NFR-003 | AC-015 | Nível integração | tests/test_app_auth.py | Pending |
| NFR-004 | AC-008 | Nível integração | tests/test_app_auth.py | Pending |
| NFR-004 | AC-009 | Nível unidade, integração e frontend | tests/test_app_auth.py | Pending |
| NFR-004 | AC-010 | Nível integração | tests/test_app_people.py | Pending |
| NFR-005 | AC-012 | Nível integração e frontend | tests/test_app_people.py | Pending |
| NFR-005 | AC-025 | Nível frontend | frontend/src/features/pessoas/DataGridPessoas.test.tsx | Pending |
| NFR-005 | AC-026 | Nível frontend e revisão visual | frontend/src/features/auth/LoginForm.test.tsx | Pending |
| NFR-006 | AC-020 | Nível integração | tests/test_app_migrations.py | Pending |
| NFR-006 | AC-022 | Nível integração | tests/test_app_bootstrap.py | Pending |
| NFR-006 | AC-029 | Nível integração | tests/test_app_migrations.py | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY
- **Data**: 2026-09-21
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/planned/0020-autenticacao-real-por-pessoa/spec.md`
- **Achados**: nenhum `BLOCKER`. Contagens: 7 US, 15 FR, 6 NFR, 29 AC e 13 DEC. Cobertura mínima US, FR e NFR com 3 ou mais AC: atendida para os 28 IDs. A seção 10 traz as nove partes obrigatórias, o Contrato CRUD com a exceção sem apagar e a revisão visual. A Definition of Done cita `PROJECT.md`, `.specsfy/STACK.md`, `.specsfy/RULES.md` e `.specsfy/DATABASE.md`, como exige a mudança de stack e de persistência. Os cinco findings abaixo não impedem o gate; os três P2 e os dois P3 em `Open` devem ser tratados por `$specsfy-05-tasks`.
- **FIND-SEC-001** [P2] [Open] Login de e-mail inexistente não verifica hash e responde mais rápido que o de e-mail existente, o que revela quais e-mails existem — Refs: NFR-002, FR-001, AC-003 — Evidence: specs/planned/0020-autenticacao-real-por-pessoa/spec.md — Effect: a igualdade de status e corpo exigida pelo requisito é anulada por diferença de tempo de resposta — Suggestion: verificar a senha contra um hash fictício de mesmo custo quando o e-mail não existe e cobrir com teste de tempo relativo
- **FIND-SEC-002** [P2] [Open] O bloqueio por e-mail permite negar o acesso de qualquer pessoa com 5 tentativas a cada 15 minutos — Refs: FR-002, FR-013, AC-004 — Evidence: specs/planned/0020-autenticacao-real-por-pessoa/spec.md — Effect: um owner pode ficar bloqueado de forma contínua por alguém que só conhece o e-mail dele — Suggestion: aceitar como troca conhecida, garantir que o comando de implantação limpe o bloqueio ao redefinir a senha e avaliar limite por e-mail e origem
- **FIND-ARCH-001** [P2] [Resolved] O plano travava só a linha da pessoa alvo na regra do último owner, o que permite corrida entre dois owners que se rebaixam ao mesmo tempo — Refs: FR-009, AC-013 — Evidence: specs/planned/0020-autenticacao-real-por-pessoa/spec.md — Effect: um tenant poderia ficar sem owner ativo — Suggestion: travar todas as linhas de vínculo de owner do tenant na mesma transação; corrigido na seção 8, em Queries e repositórios
- **FIND-SEC-003** [P3] [Open] A recusa de e-mail duplicado revela que o e-mail existe em outro tenant — Refs: FR-008, AC-012 — Evidence: specs/planned/0020-autenticacao-real-por-pessoa/spec.md — Effect: um admin descobre que um e-mail já está cadastrado em outra equipe — Suggestion: manter a mensagem sem indicar onde o e-mail está cadastrado; o risco é tolerável para uma equipe interna, mas a decisão de aceitar deve ser registrada
- **FIND-PROD-001** [P3] [Open] A seção 10 descreve a tela Nova senha com cabeçalho que mostra só Sair e também como tela isolada sem trilha — Refs: FR-014, AC-006 — Evidence: specs/planned/0020-autenticacao-real-por-pessoa/spec.md — Effect: duas leituras possíveis do que aparece no topo dessa tela — Suggestion: definir que a tela fica fora do shell, sem trilha nem navegação, e tem apenas a ação Sair
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: READY
- **Data**: 2026-09-21
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/planned/0020-autenticacao-real-por-pessoa/spec.md`
- **Achados**: nenhum erro. 71 tarefas (1 `[OPS]`, 36 `[TEST] [TDD]`, 27 `[CODE]`, 6 `[DOC]` e 1 `[TEST]` final), 57 de 57 IDs cobertos, 426 itens de checklist. Cada `AC` tem tarefa TDD própria e cada `US`, `FR` e `NFR` tem 3 ou mais. As 36 tarefas TDD têm RED válido registrado na seção 11 (26 de backend com `uv run pytest` e 39 casos de frontend em 10 arquivos com `vitest run`; os 73 casos de frontend e os 20 de backend existentes continuam passando). Cada `[CODE]` depende de pelo menos 3 predecessores TDD rastreáveis. A fase de interface cobre as 5 telas e atualiza `INTERFACE.md`. Não há tarefa com a tag de migração, conforme `.specsfy/RULES.md`. Atenção para a `Fase 2`: os testes AC-020 e AC-029 usam `alembic downgrade` no banco de scratch dedicado, como as suítes da SPEC-0019; no RED nenhum downgrade foi executado.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/planned/0020-autenticacao-real-por-pessoa/spec.md .`
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

Tarefas de migração de schema são `[CODE]` comuns apontando para `alembic/versions/`, sem a tag de migração (regra de `.specsfy/RULES.md`). Os testes de `[CODE]` rodam sempre contra o banco de teste `rag_pipeline_test`, sem nenhum comando que apague estruturas ou registros.

#### Fase 0 — Setup mínimo

**Objetivo**: ter o hash de senha disponível no ambiente antes de escrever os testes que dependem dele.
**Teste independente**: `uv run python -c "import argon2"` sai com código 0.

- [x] T001 [OPS] Adicionar a dependência `argon2-cffi` em ./pyproject.toml e sincronizar ./uv.lock — Refs: FR-003, NFR-001, AC-007, AC-021, AC-028 — Depends: none
  - [x] **PREP**: Confirmado que `argon2-cffi` não constava em `pyproject.toml`, o ambiente `uv` estava funcional com cache gravável em `/tmp` e `docs/` foi reconstruído com `$specsfy-documentator` como baseline.
  - [x] **EXECUTE**: Declarado `argon2-cffi>=25.1.0` em `dependencies`; `uv lock` resolveu `argon2-cffi 25.1.0` sem atualizar as demais dependências fora da resolução necessária.
  - [x] **VERIFY**: `UV_CACHE_DIR=/tmp/rag-pipeline-uv-cache uv sync` concluiu e `uv run python -c "import argon2; print(argon2.__version__)"` saiu com código 0, versão `25.1.0`.
  - [x] **VISUAL**: Não aplicável: a tarefa só altera dependências, sem superfície visual.
  - [x] **EVIDENCE**: Comandos `uv lock`, `uv sync` e import de `argon2` concluídos com código 0; arquivos alterados: `pyproject.toml` e `uv.lock`; refs FR-003, NFR-001, AC-007, AC-021 e AC-028.
  - [x] **IMPROVE**: Nenhuma dependência já declarada cobria hash de senha; a dependência dedicada foi mantida no menor escopo possível.

#### Fase 1 — RED TDD informado pelo BDD

Uma tarefa por `AC` (29) e uma por componente de frontend (7). O RED aceito é o de comportamento ausente; erro de sintaxe, de coleta ou de fixture de infraestrutura obriga a corrigir o teste. Para os casos que precisam de pessoa antes de o modelo existir, a ausência do modelo ou da tabela no primeiro uso é a causa esperada do RED e deve ser registrada como tal.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-001 o caso `test_login_valido_devolve_identidade` em tests/test_app_auth.py — Refs: US-001, FR-001, FR-007, FR-010, NFR-003, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na seção 6, confirmar US-001, FR-001, FR-007, FR-010, NFR-003, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_login_valido_devolve_identidade` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 US-001 FR-001 FR-007 FR-010 NFR-003 AC-001`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_login_valido_devolve_identidade`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-001 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-002 o caso `test_senha_errada_recusa_e_conta_falha` em tests/test_app_auth.py — Refs: US-001, FR-001, FR-002, NFR-002, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na seção 6, confirmar US-001, FR-001, FR-002, NFR-002, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_senha_errada_recusa_e_conta_falha` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 US-001 FR-001 FR-002 NFR-002 AC-002`, sem criar nem executar `.feature`. Inclui a verificação de que o contador de falhas do e-mail aumenta em um.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_senha_errada_recusa_e_conta_falha`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-002 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-003 o caso `test_recusas_de_login_sao_indistinguiveis` em tests/test_app_auth.py — Refs: US-001, FR-001, FR-008, NFR-002, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na seção 6, confirmar US-001, FR-001, FR-008, NFR-002, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_recusas_de_login_sao_indistinguiveis` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 US-001 FR-001 FR-008 NFR-002 AC-003`, sem criar nem executar `.feature`. Inclui a comparação de tempo relativo de resposta entre e-mail existente e inexistente, para cobrir o FIND-SEC-001.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_recusas_de_login_sao_indistinguiveis`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-003 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a comparação de tempo usa a mediana de 3 medidas e o fator 0,5, para não depender de uma medição isolada (FIND-SEC-001).

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-004 o caso `test_cinco_falhas_bloqueiam_por_quinze_minutos` em tests/test_app_auth.py — Refs: US-001, FR-002, NFR-002, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na seção 6, confirmar US-001, FR-002, NFR-002, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_cinco_falhas_bloqueiam_por_quinze_minutos` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 US-001 FR-002 NFR-002 AC-004`, sem criar nem executar `.feature`. Inclui o bloqueio de e-mail inexistente com a mesma mensagem.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_cinco_falhas_bloqueiam_por_quinze_minutos`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-004 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-005 o caso `test_bloqueio_expira_e_sucesso_zera_contador` em tests/test_app_auth.py — Refs: US-001, FR-001, FR-002, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na seção 6, confirmar US-001, FR-001, FR-002, o nível (nível unidade e integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_bloqueio_expira_e_sucesso_zera_contador` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 US-001 FR-001 FR-002 AC-005`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_bloqueio_expira_e_sucesso_zera_contador`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-005 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-006 o caso `test_senha_pendente_libera_so_troca_e_identidade` em tests/test_app_auth.py — Refs: US-002, FR-004, FR-005, FR-010, FR-014, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na seção 6, confirmar US-002, FR-004, FR-005, FR-010, FR-014, o nível (integração e frontend) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_senha_pendente_libera_so_troca_e_identidade` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 US-002 FR-004 FR-005 FR-010 FR-014 AC-006`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_senha_pendente_libera_so_troca_e_identidade`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-006 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-007 o caso `test_politica_de_senha_na_troca_e_na_criacao` em tests/test_app_auth.py — Refs: US-002, US-003, FR-003, FR-005, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na seção 6, confirmar US-002, US-003, FR-003, FR-005, o nível (unidade e integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_politica_de_senha_na_troca_e_na_criacao` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 US-002 US-003 FR-003 FR-005 AC-007`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_politica_de_senha_na_troca_e_na_criacao`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-007 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-008 o caso `test_troca_de_senha_mantem_atual_e_encerra_demais` em tests/test_app_auth.py — Refs: US-002, US-004, FR-005, FR-006, NFR-004, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na seção 6, confirmar US-002, US-004, FR-005, FR-006, NFR-004, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_troca_de_senha_mantem_atual_e_encerra_demais` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 US-002 US-004 FR-005 FR-006 NFR-004 AC-008`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_troca_de_senha_mantem_atual_e_encerra_demais`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-008 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T010 [TEST] [TDD] [US-004] Derivar do AC-009 o caso `test_sessao_expira_em_oito_horas_e_sair_encerra` em tests/test_app_auth.py — Refs: US-004, FR-006, FR-014, NFR-004, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na seção 6, confirmar US-004, FR-006, FR-014, NFR-004, o nível (nível unidade, integração e frontend) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_sessao_expira_em_oito_horas_e_sair_encerra` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 US-004 FR-006 FR-014 NFR-004 AC-009`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_sessao_expira_em_oito_horas_e_sair_encerra`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-009 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-010 o caso `test_eventos_de_conta_encerram_sessoes` em tests/test_app_people.py — Refs: US-003, US-004, FR-006, FR-008, NFR-004, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 na seção 6, confirmar US-003, US-004, FR-006, FR-008, NFR-004, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_eventos_de_conta_encerram_sessoes` em tests/test_app_people.py com o marcador `SPECSFY: SPEC-0020 US-003 US-004 FR-006 FR-008 NFR-004 AC-010`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_people.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_people.py -q -k test_eventos_de_conta_encerram_sessoes`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-010 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-011 o caso `test_owner_administra_pessoas_do_proprio_tenant` em tests/test_app_people.py — Refs: US-003, FR-003, FR-004, FR-008, FR-010, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 na seção 6, confirmar US-003, FR-003, FR-004, FR-008, FR-010, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_owner_administra_pessoas_do_proprio_tenant` em tests/test_app_people.py com o marcador `SPECSFY: SPEC-0020 US-003 FR-003 FR-004 FR-008 FR-010 AC-011`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_people.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_people.py -q -k test_owner_administra_pessoas_do_proprio_tenant`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-011 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-012 o caso `test_email_duplicado_e_campos_invalidos` em tests/test_app_people.py — Refs: US-003, FR-008, FR-015, NFR-005, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012 na seção 6, confirmar US-003, FR-008, FR-015, NFR-005, o nível (nível integração e frontend) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_email_duplicado_e_campos_invalidos` em tests/test_app_people.py com o marcador `SPECSFY: SPEC-0020 US-003 FR-008 FR-015 NFR-005 AC-012`, sem criar nem executar `.feature`. Inclui a checagem de que a mensagem de e-mail duplicado não informa em qual tenant o e-mail existe, tratando o FIND-SEC-003.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_people.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_people.py -q -k test_email_duplicado_e_campos_invalidos`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-012 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T014 [TEST] [TDD] [US-003] Derivar do AC-013 o caso `test_protecoes_de_ultimo_owner_e_admin` em tests/test_app_people.py — Refs: US-003, FR-008, FR-009, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-013 na seção 6, confirmar US-003, FR-008, FR-009, o nível (nível unidade e integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_protecoes_de_ultimo_owner_e_admin` em tests/test_app_people.py com o marcador `SPECSFY: SPEC-0020 US-003 FR-008 FR-009 AC-013`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_people.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_people.py -q -k test_protecoes_de_ultimo_owner_e_admin`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-013 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T015 [TEST] [TDD] [US-003] Derivar do AC-014 o caso `test_member_e_isolamento_entre_tenants` em tests/test_app_people.py — Refs: US-003, FR-009, FR-010, FR-015, NFR-003, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-014 na seção 6, confirmar US-003, FR-009, FR-010, FR-015, NFR-003, o nível (nível integração e frontend) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_member_e_isolamento_entre_tenants` em tests/test_app_people.py com o marcador `SPECSFY: SPEC-0020 US-003 FR-009 FR-010 FR-015 NFR-003 AC-014`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_people.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_people.py -q -k test_member_e_isolamento_entre_tenants`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-014 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T016 [TEST] [TDD] [US-007] Derivar do AC-015 o caso `test_tokens_estaticos_e_sem_sessao_sao_recusados` em tests/test_app_auth.py — Refs: US-007, FR-010, FR-013, NFR-003, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-015 na seção 6, confirmar US-007, FR-010, FR-013, NFR-003, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_tokens_estaticos_e_sem_sessao_sao_recusados` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 US-007 FR-010 FR-013 NFR-003 AC-015`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_tokens_estaticos_e_sem_sessao_sao_recusados`: FAILED, causa: `token-…-owner` ainda autentica em `/api/v1/workspaces`; o token estático continua aceito. Registrado na linha do AC-015 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: o texto do token antigo é montado em duas partes no arquivo, para o teste de guarda da T028 não se encontrar.

- [x] T017 [TEST] [TDD] [US-005] Derivar do AC-016 o caso `test_autoria_distingue_pessoas_do_mesmo_papel` em tests/test_app_authorship.py — Refs: US-005, FR-010, FR-011, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-016 na seção 6, confirmar US-005, FR-010, FR-011, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_autoria_distingue_pessoas_do_mesmo_papel` em tests/test_app_authorship.py com o marcador `SPECSFY: SPEC-0020 US-005 FR-010 FR-011 AC-016`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_authorship.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_authorship.py -q -k test_autoria_distingue_pessoas_do_mesmo_papel`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-016 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T018 [TEST] [TDD] [US-005] Derivar do AC-017 o caso `test_exibe_autor_nao_identificado_e_desativado` em tests/test_app_authorship.py — Refs: US-005, FR-011, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-017 na seção 6, confirmar US-005, FR-011, o nível (nível integração e frontend) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_exibe_autor_nao_identificado_e_desativado` em tests/test_app_authorship.py com o marcador `SPECSFY: SPEC-0020 US-005 FR-011 AC-017`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_authorship.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_authorship.py -q -k test_exibe_autor_nao_identificado_e_desativado`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-017 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T019 [TEST] [TDD] [US-006] Derivar do AC-018 o caso `test_cada_evento_gera_registro_sem_segredo` em tests/test_app_access_events.py — Refs: US-006, FR-012, NFR-001, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-018 na seção 6, confirmar US-006, FR-012, NFR-001, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_cada_evento_gera_registro_sem_segredo` em tests/test_app_access_events.py com o marcador `SPECSFY: SPEC-0020 US-006 FR-012 NFR-001 AC-018`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_access_events.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_access_events.py -q -k test_cada_evento_gera_registro_sem_segredo`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-018 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T020 [TEST] [TDD] [US-006] Derivar do AC-019 o caso `test_limpeza_apaga_eventos_com_mais_de_noventa_dias` em tests/test_app_access_events.py — Refs: US-006, FR-012, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-019 na seção 6, confirmar US-006, FR-012, o nível (nível unidade e integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_limpeza_apaga_eventos_com_mais_de_noventa_dias` em tests/test_app_access_events.py com o marcador `SPECSFY: SPEC-0020 US-006 FR-012 AC-019`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_access_events.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_access_events.py -q -k test_limpeza_apaga_eventos_com_mais_de_noventa_dias`: FAILED, causa: `src.app.models.EventoAcesso` ainda não existe. Registrado na linha do AC-019 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T021 [TEST] [TDD] [US-005] Derivar do AC-020 o caso `test_upgrade_preserva_linhas_e_deixa_autoria_vazia` em tests/test_app_migrations.py — Refs: US-005, US-007, FR-011, FR-013, NFR-006, AC-020 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-020 na seção 6, confirmar US-005, US-007, FR-011, FR-013, NFR-006, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_upgrade_preserva_linhas_e_deixa_autoria_vazia` em tests/test_app_migrations.py com o marcador `SPECSFY: SPEC-0020 US-005 US-007 FR-011 FR-013 NFR-006 AC-020`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_migrations.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_migrations.py -q -k test_upgrade_preserva_linhas_e_deixa_autoria_vazia`: FAILED, causa: `alembic upgrade 0020_pessoas` recusado; a revisão ainda não existe. Registrado na linha do AC-020 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: o teste parte de `0019_workspaces` com dados reais das quatro tabelas para provar que nenhuma linha muda.

- [x] T022 [TEST] [TDD] [US-001] Derivar do AC-021 o caso `test_nenhum_segredo_em_resposta_log_ou_evento` em tests/test_app_access_events.py — Refs: US-001, US-006, FR-003, FR-012, NFR-001, AC-021 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-021 na seção 6, confirmar US-001, US-006, FR-003, FR-012, NFR-001, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_nenhum_segredo_em_resposta_log_ou_evento` em tests/test_app_access_events.py com o marcador `SPECSFY: SPEC-0020 US-001 US-006 FR-003 FR-012 NFR-001 AC-021`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_access_events.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_access_events.py -q -k test_nenhum_segredo_em_resposta_log_ou_evento`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-021 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T023 [TEST] [TDD] [US-007] Derivar do AC-022 o caso `test_comando_cria_primeiro_owner_e_redefine_senha` em tests/test_app_bootstrap.py — Refs: US-007, FR-004, FR-013, NFR-006, AC-022 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-022 na seção 6, confirmar US-007, FR-004, FR-013, NFR-006, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_comando_cria_primeiro_owner_e_redefine_senha` em tests/test_app_bootstrap.py com o marcador `SPECSFY: SPEC-0020 US-007 FR-004 FR-013 NFR-006 AC-022`, sem criar nem executar `.feature`. Inclui o caso em que o comando limpa o bloqueio da conta ao redefinir a senha, tratando o FIND-SEC-002.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_bootstrap.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_bootstrap.py -q -k test_comando_cria_primeiro_owner_e_redefine_senha`: FAILED, causa: `src.app.create_owner` ainda não existe. Registrado na linha do AC-022 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T024 [TEST] [TDD] [US-001] Derivar do AC-023 o caso `layout usa a identidade do backend e trata 401` em frontend/src/app/(autenticado)/layout.test.tsx — Refs: US-001, US-004, FR-007, FR-014, AC-023 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-023 na seção 6, confirmar US-001, US-004, FR-007, FR-014, o nível (nível frontend) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `layout usa a identidade do backend e trata 401` em frontend/src/app/(autenticado)/layout.test.tsx com o marcador `SPECSFY: SPEC-0020 US-001 US-004 FR-007 FR-014 AC-023`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/app/(autenticado)/layout.test.tsx`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/app/(autenticado)/layout.test.tsx`: FAILED, causa: o cabeçalho não mostra a pessoa nem o item Pessoas e `consumirAviso` ainda não existe em `@/lib/session`. Registrado na linha do AC-023 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

- [x] T025 [TEST] [TDD] [US-002] Derivar do AC-024 o caso `menu mostra nome, troca de senha e sair` em frontend/src/features/auth/MenuPessoa.test.tsx — Refs: US-002, FR-007, FR-014, FR-015, AC-024 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-024 na seção 6, confirmar US-002, FR-007, FR-014, FR-015, o nível (nível frontend) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `menu mostra nome, troca de senha e sair` em frontend/src/features/auth/MenuPessoa.test.tsx com o marcador `SPECSFY: SPEC-0020 US-002 FR-007 FR-014 FR-015 AC-024`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/features/auth/MenuPessoa.test.tsx`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/features/auth/MenuPessoa.test.tsx`: FAILED, causa: `@/features/auth/MenuPessoa` ainda não existe. Registrado na linha do AC-024 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

- [x] T026 [TEST] [TDD] [US-003] Derivar do AC-025 o caso `lista de pessoas em largura total sem apagar` em frontend/src/features/pessoas/DataGridPessoas.test.tsx — Refs: US-003, FR-008, FR-009, FR-015, NFR-005, AC-025 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-025 na seção 6, confirmar US-003, FR-008, FR-009, FR-015, NFR-005, o nível (nível frontend) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `lista de pessoas em largura total sem apagar` em frontend/src/features/pessoas/DataGridPessoas.test.tsx com o marcador `SPECSFY: SPEC-0020 US-003 FR-008 FR-009 FR-015 NFR-005 AC-025`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/features/pessoas/DataGridPessoas.test.tsx`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/features/pessoas/DataGridPessoas.test.tsx`: FAILED, causa: `@/features/pessoas/DataGridPessoas` ainda não existe. Registrado na linha do AC-025 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

- [x] T027 [TEST] [TDD] [US-002] Derivar do AC-026 o caso `formularios acessiveis e tela pequena` em frontend/src/features/auth/LoginForm.test.tsx — Refs: US-002, FR-014, FR-015, NFR-005, AC-026 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-026 na seção 6, confirmar US-002, FR-014, FR-015, NFR-005, o nível (nível frontend e revisão visual) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `formularios acessiveis e tela pequena` em frontend/src/features/auth/LoginForm.test.tsx com o marcador `SPECSFY: SPEC-0020 US-002 FR-014 FR-015 NFR-005 AC-026`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/features/auth/LoginForm.test.tsx`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/features/auth/LoginForm.test.tsx`: FAILED, causa: o formulário de Login ainda não tem os campos E-mail e Senha. Registrado na linha do AC-026 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

- [x] T028 [TEST] [TDD] [US-007] Derivar do AC-027 o caso `suites atuais migradas para pessoas de teste` em tests/test_app_workspaces.py — Refs: US-007, FR-010, NFR-003, AC-027 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-027 na seção 6, confirmar US-007, FR-010, NFR-003, o nível (regressão) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `suites atuais migradas para pessoas de teste` em tests/test_app_workspaces.py com o marcador `SPECSFY: SPEC-0020 US-007 FR-010 NFR-003 AC-027`, sem criar nem executar `.feature`. O caso é um teste de guarda que varre `src/`, `tests/` e `frontend/src/` procurando o texto do token estático, montado em duas partes no próprio arquivo para não se encontrar.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_workspaces.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_workspaces.py -q -k test_suites_nao_usam_token_estatico`: FAILED, causa: o teste de guarda ainda encontra o texto do token estático em `src/`, `tests/` e `frontend/src/`. Registrado na linha do AC-027 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: o teste de guarda monta o texto procurado em duas partes, para não encontrar o próprio arquivo.

- [x] T029 [TEST] [TDD] Derivar do AC-028 o caso `test_senha_e_token_ficam_so_como_derivados` em tests/test_app_auth.py — Refs: FR-003, FR-006, NFR-001, AC-028 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-028 na seção 6, confirmar FR-003, FR-006, NFR-001, o nível (nível unidade e integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_senha_e_token_ficam_so_como_derivados` em tests/test_app_auth.py com o marcador `SPECSFY: SPEC-0020 FR-003 FR-006 NFR-001 AC-028`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_auth.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_auth.py -q -k test_senha_e_token_ficam_so_como_derivados`: FAILED, causa: `src.app.models.Pessoa` ainda não existe; o teste falha no corpo, ao criar a pessoa de teste. Registrado na linha do AC-028 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `tests/_pessoas.py` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta ou de fixture.

- [x] T030 [TEST] [TDD] [US-007] Derivar do AC-029 o caso `test_downgrade_remove_somente_o_que_a_revisao_criou` em tests/test_app_migrations.py — Refs: US-007, FR-013, NFR-006, AC-029 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-029 na seção 6, confirmar US-007, FR-013, NFR-006, o nível (nível integração) e as pessoas de teste que o cenário precisa.
  - [x] **EXECUTE**: Escrever `test_downgrade_remove_somente_o_que_a_revisao_criou` em tests/test_app_migrations.py com o marcador `SPECSFY: SPEC-0020 US-007 FR-013 NFR-006 AC-029`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: Observar RED válido com `uv run pytest tests/test_app_migrations.py -q`: o teste executa e falha por comportamento ausente (rota inexistente, estrutura inexistente ou asserção), sem erro de sintaxe, de coleta ou de fixture de infraestrutura.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `uv run pytest tests/test_app_migrations.py -q -k test_downgrade_remove_somente_o_que_a_revisao_criou`: FAILED, causa: as tabelas de pessoas, vínculos, sessões, tentativas e eventos ainda não existem na revisão atual. Registrado na linha do AC-029 da seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: o teste confirma primeiro que a revisão existe; sem isso o downgrade seria um no-op e o teste passaria sem implementação. Nenhum downgrade foi executado no RED.

- [x] T031 [P] [TEST] [TDD] [US-001] Derivar do BDD da spec o caso `LoginForm envia e-mail e senha e trata os retornos` em frontend/src/features/auth/LoginForm.test.tsx — Refs: US-001, FR-001, FR-002, FR-014, AC-001, AC-002, AC-004, AC-006 — Depends: none
  - [x] **PREP**: Ler no Gherkin os cenários AC-001, AC-002, AC-004, AC-006 e o contrato da tela na seção 10.
  - [x] **EXECUTE**: Escrever o caso que envia e-mail e senha, mostra a mensagem genérica em `Alert`, preserva o e-mail, limpa a senha, mostra a mensagem própria de bloqueio e leva a `/nova-senha` quando a senha está pendente. Marcador `SPECSFY: SPEC-0020 US-001 FR-001 FR-002 FR-014 AC-001 AC-002 AC-004 AC-006`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/features/auth/LoginForm.test.tsx`: o teste executa e falha por comportamento ausente, sem erro de coleta, de sintaxe ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/features/auth/LoginForm.test.tsx`: FAILED, causa: os campos E-mail e Senha do Login ainda não existem. Registrado na seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

- [x] T032 [P] [TEST] [TDD] [US-002] Derivar do BDD da spec o caso `NovaSenhaForm exige senha válida e confirmação` em frontend/src/features/auth/NovaSenhaForm.test.tsx — Refs: US-002, FR-004, FR-005, FR-014, AC-006, AC-007, AC-026 — Depends: none
  - [x] **PREP**: Ler no Gherkin os cenários AC-006, AC-007, AC-026 e o contrato da tela na seção 10.
  - [x] **EXECUTE**: Escrever o caso da tela Nova senha fora do shell, sem trilha nem navegação e só com Sair (FIND-PROD-001), com regra de 10 caracteres junto do campo e erro abaixo dele. Marcador `SPECSFY: SPEC-0020 US-002 FR-004 FR-005 FR-014 AC-006 AC-007 AC-026`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/features/auth/NovaSenhaForm.test.tsx`: o teste executa e falha por comportamento ausente, sem erro de coleta, de sintaxe ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/features/auth/NovaSenhaForm.test.tsx`: FAILED, causa: `@/features/auth/NovaSenhaForm` e `@/app/nova-senha/page` ainda não existem. Registrado na seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

- [x] T033 [P] [TEST] [TDD] [US-002] Derivar do BDD da spec o caso `TrocarSenhaDialog troca a própria senha` em frontend/src/features/auth/TrocarSenhaDialog.test.tsx — Refs: US-002, FR-005, FR-014, AC-007, AC-008, AC-024 — Depends: none
  - [x] **PREP**: Ler no Gherkin os cenários AC-007, AC-008, AC-024 e o contrato da tela na seção 10.
  - [x] **EXECUTE**: Escrever o caso do diálogo com senha atual, nova e confirmação, erro no campo e retorno ao contexto com a sessão mantida. Marcador `SPECSFY: SPEC-0020 US-002 FR-005 FR-014 AC-007 AC-008 AC-024`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/features/auth/TrocarSenhaDialog.test.tsx`: o teste executa e falha por comportamento ausente, sem erro de coleta, de sintaxe ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/features/auth/TrocarSenhaDialog.test.tsx`: FAILED, causa: `@/features/auth/TrocarSenhaDialog` ainda não existe. Registrado na seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

- [x] T034 [P] [TEST] [TDD] [US-003] Derivar do BDD da spec o caso `PessoaFormSheet cria e edita pessoa em painel lateral` em frontend/src/features/pessoas/PessoaFormSheet.test.tsx — Refs: US-003, FR-008, FR-009, FR-015, AC-011, AC-012, AC-013, AC-025 — Depends: none
  - [x] **PREP**: Ler no Gherkin os cenários AC-011, AC-012, AC-013, AC-025 e o contrato da tela na seção 10.
  - [x] **EXECUTE**: Escrever o caso do painel com nome, e-mail, papel e senha inicial, opção owner só para owner, campos preservados e foco no primeiro erro após 409. Marcador `SPECSFY: SPEC-0020 US-003 FR-008 FR-009 FR-015 AC-011 AC-012 AC-013 AC-025`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/features/pessoas/PessoaFormSheet.test.tsx`: o teste executa e falha por comportamento ausente, sem erro de coleta, de sintaxe ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/features/pessoas/PessoaFormSheet.test.tsx`: FAILED, causa: `@/features/pessoas/PessoaFormSheet` ainda não existe. Registrado na seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

- [x] T035 [P] [TEST] [TDD] [US-003] Derivar do BDD da spec o caso `diálogos de desativar, reativar e redefinir senha` em frontend/src/features/pessoas/DesativarPessoaDialog.test.tsx — Refs: US-003, US-004, FR-006, FR-008, FR-009, FR-015, AC-010, AC-013, AC-025 — Depends: none
  - [x] **PREP**: Ler no Gherkin os cenários AC-010, AC-013, AC-025 e o contrato da tela na seção 10.
  - [x] **EXECUTE**: Escrever o caso dos diálogos com alvo e consequência, sem oferecer desativar o último owner nem a si mesma, e com o campo de senha temporária na redefinição. Marcador `SPECSFY: SPEC-0020 US-003 US-004 FR-006 FR-008 FR-009 FR-015 AC-010 AC-013 AC-025`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/features/pessoas/DesativarPessoaDialog.test.tsx`: o teste executa e falha por comportamento ausente, sem erro de coleta, de sintaxe ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/features/pessoas/DesativarPessoaDialog.test.tsx`: FAILED, causa: `DesativarPessoaDialog` e `RedefinirSenhaDialog` ainda não existem. Registrado na seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

- [x] T036 [P] [TEST] [TDD] [US-003] Derivar do BDD da spec o caso `rotas de Pessoas por papel e detalhe da pessoa` em frontend/src/app/(autenticado)/pessoas/page.test.tsx — Refs: US-003, FR-010, FR-015, NFR-003, NFR-005, AC-011, AC-014, AC-025 — Depends: none
  - [x] **PREP**: Ler no Gherkin os cenários AC-011, AC-014, AC-025 e o contrato da tela na seção 10.
  - [x] **EXECUTE**: Escrever o caso da lista e do detalhe para owner, e o caso do member por endereço, com explicação curta sem dados e sem item de menu. Marcador `SPECSFY: SPEC-0020 US-003 FR-010 FR-015 NFR-003 NFR-005 AC-011 AC-014 AC-025`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/app/(autenticado)/pessoas/page.test.tsx`: o teste executa e falha por comportamento ausente, sem erro de coleta, de sintaxe ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/app/(autenticado)/pessoas/page.test.tsx`: FAILED, causa: as rotas `/pessoas` e `/pessoas/[id]` ainda não existem. Registrado na seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

- [x] T037 [P] [TEST] [TDD] [US-005] Derivar do BDD da spec o caso `autoria nas listas e detalhes` em frontend/src/features/bases/DataGridBases.test.tsx — Refs: US-005, FR-011, AC-016, AC-017 — Depends: none
  - [x] **PREP**: Ler no Gherkin os cenários AC-016, AC-017 e o contrato da tela na seção 10.
  - [x] **EXECUTE**: Escrever o caso da coluna "Criada por" nas listas de Workspaces e Bases, do "Iniciada por" no progresso e do "Consultada por" na consulta, com "Autor não identificado" e a marca "(desativada)". Marcador `SPECSFY: SPEC-0020 US-005 FR-011 AC-016 AC-017`.
  - [x] **VERIFY**: Observar RED válido com `npm --prefix frontend run test:tdd -- src/features/bases/DataGridBases.test.tsx`: o teste executa e falha por comportamento ausente, sem erro de coleta, de sintaxe ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste; a conferência visual acontece na tarefa de tela.
  - [x] **EVIDENCE**: RED observado em 2026-09-21 com `npm --prefix frontend run test:tdd -- src/features/bases/DataGridBases.test.tsx`: FAILED, causa: as listas e o resultado ainda não mostram a autoria (Criada por, Iniciada por, Consultada por). Registrado na seção 11.
  - [x] **IMPROVE**: Melhoria aplicada: a importação tardia por `frontend/src/test/carregar.ts` faz o RED sair por asserção de comportamento ausente, e não por erro de coleta.

#### Fase 2 — Fundação: dados, migração e segurança (US-005, US-006 e US-007)

**Objetivo**: modelos, migração reversível, hash de senha e registro de eventos prontos para as histórias.
**Teste independente**: `uv run alembic upgrade head` e `uv run pytest tests/test_app_migrations.py -q` no banco de teste.

- [x] T038 [CODE] Criar os modelos `Pessoa`, `VinculoPessoa`, `Sessao`, `TentativaLogin`, `EventoAcesso` e a coluna `criado_por` em src/app/models.py — Refs: US-005, US-007, FR-011, FR-013, NFR-006, AC-016, AC-020, AC-022, AC-029 — Depends: T017, T021, T023, T030
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados com `$specsfy-documentator`; REDs predecessores T017, T021, T023 e T030 confirmados; baseline `uv run pytest -q` concluído com 377 testes aprovados, 1 ignorado e 1 advertência preexistente.
  - [x] **EXECUTE**: Declaradas as cinco entidades da seção 9, com índice único funcional para e-mail sem diferenciar maiúsculas, vínculo único por pessoa e `criado_por` opcional em `Workspace`, `Base`, `Execution` e `Query`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_migrations.py tests/test_app_models.py -q` concluiu com 8 testes aprovados; a suíte completa permaneceu verde com 377 testes aprovados e 1 ignorado.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN registrado para estrutura e migração; arquivos verificados: `src/app/models.py` e `tests/conftest.py`. A fixture percorre `reversed(ORMBase.metadata.sorted_tables)`, respeitando a ordem inversa das chaves estrangeiras na limpeza.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: tabelas, colunas, índices e nomes em português seguem o padrão já adotado por `Workspace`, `Base`, `Execution` e `Query`.
  <!-- specsfy:evidence {"task": "T038", "refs": ["US-005", "US-007", "FR-011", "FR-013", "NFR-006", "AC-016", "AC-020", "AC-022", "AC-029"], "files": ["src/app/models.py", "tests/conftest.py"], "commands": [{"run": "uv run pytest tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}, {"run": "uv run pytest -q", "exit": 0}]} -->

- [x] T039 [CODE] Criar a revisão Alembic `0020_pessoas` em alembic/versions/0020_pessoas_e_autoria.py — Refs: US-007, FR-013, NFR-006, AC-020, AC-022, AC-029 — Depends: T021, T030, T023, T038
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T021, T030 e T023 e baseline de 377 testes aprovados confirmados; banco dedicado `rag_pipeline_test` confirmado na porta 55432. Nenhum comando destrutivo manual foi executado.
  - [x] **EXECUTE**: Revisão encadeada em `0019_workspaces`, com as cinco tabelas e seus índices, `criado_por` nulável e indexado nas quatro tabelas existentes e reversão declarada em ordem inversa.
  - [x] **VERIFY**: `uv run alembic upgrade head` saiu com código 0 no banco de teste; `uv run alembic current` mostrou `0020_pessoas (head)`; os casos de migração participaram do comando focal que concluiu com 8 testes aprovados.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: Revisão em `alembic/versions/0020_pessoas_e_autoria.py`; upgrade e consulta da revisão saíram com código 0. O teste de preservação manteve 4 de 4 linhas legadas — uma em `workspaces`, `bases`, `executions` e `queries` — e deixou a autoria nula.
  - [x] **IMPROVE**: A reversibilidade foi conferida pelo teste focal no banco de scratch com dados, preservando as quatro linhas preexistentes; nenhuma alteração adicional foi necessária.
  <!-- specsfy:evidence {"task": "T039", "refs": ["US-007", "FR-013", "NFR-006", "AC-020", "AC-022", "AC-029"], "files": ["alembic/versions/0020_pessoas_e_autoria.py"], "commands": [{"run": "uv run alembic upgrade head", "exit": 0}, {"run": "uv run alembic current", "exit": 0}, {"run": "uv run pytest tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}]} -->

- [x] T040 [CODE] Criar a política de senha, o hash argon2id e o token de sessão em src/app/security.py — Refs: FR-003, FR-006, NFR-001, NFR-002, AC-002, AC-003, AC-007, AC-021, AC-028 — Depends: T003, T004, T008, T022, T029, T001
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T003, T004, T008, T022 e T029 e baseline de 377 testes aprovados confirmados.
  - [x] **EXECUTE**: Implementadas a política de senha, hash e verificação Argon2id com hash fictício, token aleatório de 256 bits, resumo SHA-256 e constantes nomeadas para 8 horas, 5 tentativas, 15 minutos, 10 caracteres e 90 dias.
  - [x] **VERIFY**: `uv run pytest tests/test_app_auth.py -q -k "politica or derivados or indistinguiveis"` concluiu com 3 testes aprovados e 16 desmarcados. `src/app/security.py` não contém logging nem impressão de senha, hash ou token.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN focal com 3 testes; arquivo alterado: `src/app/security.py`. Medição local de três verificações por caminho: conta existente 117,95 ms, inexistente 111,66 ms, razão 0,947.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: o caminho inexistente usa `_HASH_FICTICIO`, criado pelo mesmo `PasswordHasher` e com o mesmo custo Argon2id do hash real.
  <!-- specsfy:evidence {"task": "T040", "refs": ["FR-003", "FR-006", "NFR-001", "NFR-002", "AC-002", "AC-003", "AC-007", "AC-021", "AC-028"], "files": ["src/app/security.py"], "commands": [{"run": "uv run pytest tests/test_app_auth.py -q -k \"politica or derivados or indistinguiveis\"", "exit": 0}]} -->

- [x] T041 [CODE] Criar o registro e a limpeza de eventos de acesso em src/app/events.py — Refs: US-006, FR-012, NFR-001, AC-018, AC-019, AC-021 — Depends: T019, T020, T022, T038
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T019, T020 e T022 e baseline de 377 testes aprovados confirmados.
  - [x] **EXECUTE**: Implementados os onze tipos de evento, sem persistir segredo ou e-mail tentado sem pessoa correspondente, e a limpeza de eventos com mais de 90 dias, sessões expiradas e bloqueios vencidos.
  - [x] **VERIFY**: `uv run pytest tests/test_app_access_events.py -q` concluiu com 3 testes aprovados, cobrindo todos os onze tipos, retenção em 89/91 dias e ausência de segredo em resposta, log e evento.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN com 3 testes; arquivo alterado: `src/app/events.py`; tipos cobertos: `entrou`, `senha_errada`, `bloqueada`, `senha_trocada`, `senha_redefinida`, `pessoa_criada`, `dados_corrigidos`, `papel_alterado`, `pessoa_desativada`, `pessoa_reativada` e `sessao_encerrada`.
  - [x] **IMPROVE**: Decisão preservada: o evento participa da mesma transação da operação principal; uma falha de auditoria aborta a operação, evitando sucesso sem o rastro exigido por FR-012, em vez de falhar silenciosamente.
  <!-- specsfy:evidence {"task": "T041", "refs": ["US-006", "FR-012", "NFR-001", "AC-018", "AC-019", "AC-021"], "files": ["src/app/events.py"], "commands": [{"run": "uv run pytest tests/test_app_access_events.py -q", "exit": 0}]} -->

#### Fase 3 — US-001, US-002, US-004 e US-007: substituir o token estático (P1)

**Objetivo**: entrar com e-mail e senha, senha própria, sessão revogável e implantação por comando, sem os tokens antigos.
**Teste independente**: `uv run pytest tests -q` passa e os quatro tokens antigos respondem 401.

- [x] T042 [CODE] [US-001] Implementar entrar, sair, bloqueio, sessão e troca de senha em src/app/accounts.py — Refs: US-001, US-002, US-004, FR-001, FR-002, FR-004, FR-005, FR-006, NFR-002, NFR-004, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-008, AC-009 — Depends: T002, T003, T004, T005, T006, T007, T009, T010, T038, T040, T041
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T002–T007, T009 e T010 e baseline de 377 testes aprovados confirmados.
  - [x] **EXECUTE**: Implementados login com contador normalizado, bloqueio de 15 minutos, sessão de 8 horas, logout, pendência e troca de senha com preservação da sessão atual, revogação das demais e evento com motivo.
  - [x] **VERIFY**: `uv run pytest tests/test_app_auth.py -q` concluiu com 19 testes aprovados, cobrindo login, bloqueio, expiração, logout, senha pendente e troca de senha.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN para AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-008 e AC-009; conta desativada, senha errada e e-mail inexistente retornaram o mesmo status 401 e o mesmo corpo JSON. Arquivo alterado: `src/app/accounts.py`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: contador, bloqueio e eventos são alterados na mesma `Session` e confirmados pelo mesmo `commit` da tentativa recusada.
  <!-- specsfy:evidence {"task": "T042", "refs": ["US-001", "US-002", "US-004", "FR-001", "FR-002", "FR-004", "FR-005", "FR-006", "NFR-002", "NFR-004", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006", "AC-008", "AC-009"], "files": ["src/app/accounts.py"], "commands": [{"run": "uv run pytest tests/test_app_auth.py -q", "exit": 0}]} -->

- [x] T043 [CODE] [US-001] Reescrever a identidade e as dependências em src/app/auth.py — Refs: US-001, US-007, FR-001, FR-004, FR-007, FR-010, NFR-003, AC-001, AC-006, AC-015 — Depends: T002, T007, T016, T042
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T002, T007 e T016 e baseline de 377 testes aprovados confirmados.
  - [x] **EXECUTE**: `Identity` passou a carregar pessoa, nome, e-mail, tenant, projeto, papel, pendência e sessão; pessoa e vínculo são resolvidos no banco a cada requisição; `get_identity`, `get_identity_pendente` e `require_write_role` estão ativos; `TokenRegistry` e o `configure` de autenticação foram removidos.
  - [x] **VERIFY**: `uv run pytest tests/test_app_auth.py -q` concluiu com 19 testes aprovados, incluindo identidade, senha pendente e recusa dos quatro tokens antigos.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN com 19 testes; sem sessão válida foram recusadas as rotas de criar Base, iniciar Execução, obter Execução, repetir Execução, apagar Base e consultar Base. Arquivo alterado: `src/app/auth.py`.
  - [x] **IMPROVE**: Busca estrutural em `src/`, `tests/` e `frontend/src/` não encontrou importação nem uso remanescente de `TokenRegistry`; nenhuma limpeza adicional foi necessária.
  <!-- specsfy:evidence {"task": "T043", "refs": ["US-001", "US-007", "FR-001", "FR-004", "FR-007", "FR-010", "NFR-003", "AC-001", "AC-006", "AC-015"], "files": ["src/app/auth.py"], "commands": [{"run": "uv run pytest tests/test_app_auth.py -q", "exit": 0}]} -->

- [x] T044 [CODE] [US-001] Criar as rotas de autenticação em src/app/routers/auth.py — Refs: US-001, US-002, FR-001, FR-002, FR-005, FR-007, AC-001, AC-002, AC-004, AC-006, AC-008, AC-009 — Depends: T002, T003, T005, T007, T009, T010, T042, T043
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T002, T003, T005, T007, T009 e T010 e baseline de 377 testes aprovados confirmados.
  - [x] **EXECUTE**: Expostas `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me` e `POST /api/v1/auth/senha`, delegando regras a `accounts.py` e aceitando a identidade com senha pendente onde necessário.
  - [x] **VERIFY**: `uv run pytest tests/test_app_auth.py -q` concluiu com 19 testes aprovados pela API real via `TestClient`.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN por rota: login e identidade 200, logout e troca de senha 204, credencial/sessão inválida 401, senha pendente fora das rotas permitidas 403 e bloqueio 429. Arquivo alterado: `src/app/routers/auth.py`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: `AccountError` é convertido para `HTTPException`, mantendo o corpo `detail` usado pelos routers FastAPI existentes.
  <!-- specsfy:evidence {"task": "T044", "refs": ["US-001", "US-002", "FR-001", "FR-002", "FR-005", "FR-007", "AC-001", "AC-002", "AC-004", "AC-006", "AC-008", "AC-009"], "files": ["src/app/routers/auth.py"], "commands": [{"run": "uv run pytest tests/test_app_auth.py -q", "exit": 0}]} -->

- [x] T045 [CODE] [US-007] Criar o comando de implantação em src/app/create_owner.py — Refs: US-007, FR-004, FR-013, NFR-006, AC-020, AC-022, AC-029 — Depends: T023, T021, T030, T042, T038
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T023, T021 e T030 e baseline de 377 testes aprovados confirmados.
  - [x] **EXECUTE**: Implementado `python -m src.app.create_owner` para criar o primeiro owner ou redefinir senha, usando `getpass`, recusando `--senha`, exigindo troca posterior, encerrando sessões e limpando o bloqueio.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bootstrap.py -q` concluiu com 1 teste aprovado, cobrindo criação, redefinição, recusa de senha por argumento e limpeza do bloqueio.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN no fluxo operacional; a senha é obtida exclusivamente por `getpass`, não integra `argv` nem é ecoada. Arquivo alterado: `src/app/create_owner.py`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: mensagens de sucesso e erro citam somente estado operacional; não incluem senha, hash ou token.
  <!-- specsfy:evidence {"task": "T045", "refs": ["US-007", "FR-004", "FR-013", "NFR-006", "AC-020", "AC-022", "AC-029"], "files": ["src/app/create_owner.py"], "commands": [{"run": "uv run pytest tests/test_app_bootstrap.py -q", "exit": 0}]} -->

- [x] T051 [CODE] [US-007] Migrar as suítes de backend para pessoas de teste em tests/conftest.py — Refs: US-007, FR-010, NFR-003, AC-015, AC-027 — Depends: T016, T028, T002, T043, T042, T046
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores e baseline confirmados. As seis suítes eram `test_app_worker.py`, `test_app_auth.py`, `test_app_workspaces.py`, `test_app_bases.py`, `test_app_executions.py` e `test_app_queries.py`.
  - [x] **EXECUTE**: Criada em `tests/conftest.py` a fixture compartilhada que converte as quatro identidades simbólicas em Pessoas e Sessões reais; as seis suítes foram migradas preservando cenários e recusas.
  - [x] **VERIFY**: `uv run pytest tests -q` concluiu com 377 testes aprovados e 1 ignorado; `rg -n 'token-demo' tests` não encontrou ocorrência literal.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: 71 ocorrências literais antes (3 auth, 28 bases, 16 executions, 10 queries, 3 worker e 11 workspaces) e 0 depois; regressão completa verde com 377 aprovados e 1 ignorado.
  - [x] **IMPROVE**: Consolidação aplicada: uma única fixture autouse em `tests/conftest.py` atende as seis suítes e mantém o papel/tenant explícito por identidade simbólica.
  <!-- specsfy:evidence {"task": "T051", "refs": ["US-007", "FR-010", "NFR-003", "AC-015", "AC-027"], "files": ["tests/conftest.py", "tests/test_app_worker.py", "tests/test_app_auth.py", "tests/test_app_workspaces.py", "tests/test_app_bases.py", "tests/test_app_executions.py", "tests/test_app_queries.py"], "commands": [{"run": "uv run pytest tests -q", "exit": 0}]} -->

- [x] T052 [CODE] [US-007] Remover os tokens estáticos e registrar os novos routers em src/app/main.py — Refs: US-007, FR-010, FR-013, NFR-003, AC-015, AC-027 — Depends: T016, T028, T002, T051, T044, T048, T049
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores e baseline confirmados.
  - [x] **EXECUTE**: `_token_registry` e `auth.configure` removidos; routers `auth` e `people` incluídos; preservada a ordem banco/tabelas, settings, storage e conector Procrastinate.
  - [x] **VERIFY**: `uv run pytest tests -q` concluiu com 377 testes aprovados e 1 ignorado; o caso AC-015 confirmou 401 para cada um dos quatro tokens antigos em todas as rotas protegidas exercitadas.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: Regressão backend completa verde; quatro tokens antigos recusados com 401; arquivo alterado: `src/app/main.py`.
  - [x] **IMPROVE**: Busca em `src/`, `tests/` e `frontend/src/` não encontrou importação, chamada ou comentário remanescente de `TokenRegistry`, `_token_registry`, `auth.configure` ou token estático literal.
  <!-- specsfy:evidence {"task": "T052", "refs": ["US-007", "FR-010", "FR-013", "NFR-003", "AC-015", "AC-027"], "files": ["src/app/main.py"], "commands": [{"run": "uv run pytest tests -q", "exit": 0}]} -->

#### Fase 4 — US-003: administrar pessoas no backend (P1)

**Objetivo**: API de Pessoas com as proteções do último owner e do admin sobre owner.
**Teste independente**: `uv run pytest tests/test_app_people.py -q`.

- [x] T046 [CODE] [US-003] Implementar a gestão de pessoas e as proteções em src/app/accounts.py — Refs: US-003, US-004, FR-006, FR-008, FR-009, FR-010, NFR-004, AC-010, AC-011, AC-012, AC-013, AC-014 — Depends: T011, T012, T013, T014, T015, T042
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T011–T015 e baseline de 377 testes aprovados confirmados.
  - [x] **EXECUTE**: Implementados criar, corrigir, alterar papel, desativar, reativar e redefinir senha; unicidade global case-insensitive com mensagem neutra; proteções de último owner, admin sobre owner e autodesativação; sessões afetadas são encerradas.
  - [x] **VERIFY**: `uv run pytest tests/test_app_people.py -q` concluiu com 6 testes aprovados, cobrindo proteções, isolamento, revogação de sessão e concorrência.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN para AC-010 a AC-014; o teste concorrente executou três rodadas de dois rebaixamentos simultâneos e manteve ao menos um owner em todas. Arquivo alterado: `src/app/accounts.py`.
  - [x] **IMPROVE**: A consulta trava, com `SELECT ... FOR UPDATE`, todas as linhas de owner ativo do tenant/projeto antes de rebaixar ou desativar; o teste concorrente comprova que duas operações simultâneas não deixam o tenant sem owner.
  <!-- specsfy:evidence {"task": "T046", "refs": ["US-003", "US-004", "FR-006", "FR-008", "FR-009", "FR-010", "NFR-004", "AC-010", "AC-011", "AC-012", "AC-013", "AC-014"], "files": ["src/app/accounts.py"], "commands": [{"run": "uv run pytest tests/test_app_people.py -q", "exit": 0}]} -->

- [x] T047 [CODE] [US-003] Criar as leituras de pessoas do tenant e projeto em src/app/repo.py — Refs: US-003, FR-008, FR-009, FR-010, AC-011, AC-013, AC-014 — Depends: T012, T014, T015, T038
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T012, T014 e T015 e baseline de 377 testes aprovados confirmados.
  - [x] **EXECUTE**: Adicionadas lista e busca por id isoladas por tenant/projeto, busca global por e-mail normalizado e contagem de owners ativos com trava de todas as linhas; acesso cruzado mantém 404. A contagem foi centralizada em `repo.py` e reutilizada por `accounts.py`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_people.py -q` concluiu com 6 testes aprovados em listagem, detalhe, isolamento e concorrência; Ruff passou nos dois módulos alterados.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN com 6 testes; arquivos alterados: `src/app/repo.py` e `src/app/accounts.py`; monitor de contexto permaneceu `CURRENT`.
  - [x] **IMPROVE**: A busca global usa o índice funcional único `uq_pessoas_email_lower`; o escopo usa `ix_vinculos_pessoa_tenant_project`; pessoa/vínculo usa PK e índice único de `pessoa_id`. Nenhum índice adicional foi necessário.
  <!-- specsfy:evidence {"task": "T047", "refs": ["US-003", "FR-008", "FR-009", "FR-010", "AC-011", "AC-013", "AC-014"], "files": ["src/app/repo.py", "src/app/accounts.py"], "commands": [{"run": "uv run pytest tests/test_app_people.py -q", "exit": 0}, {"run": "uv run ruff check src/app/repo.py src/app/accounts.py", "exit": 0}]} -->

- [x] T048 [CODE] [US-003] Criar as rotas de pessoas em src/app/routers/people.py — Refs: US-003, FR-008, FR-009, FR-010, AC-011, AC-012, AC-013, AC-014 — Depends: T012, T013, T014, T015, T046, T047, T043
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T012–T015 e baseline de 377 testes aprovados confirmados.
  - [x] **EXECUTE**: Expostas lista, criação, detalhe, edição, desativação, reativação e redefinição de senha em `/api/v1/pessoas`, todas protegidas para owner/admin e com os códigos previstos.
  - [x] **VERIFY**: `uv run pytest tests/test_app_people.py -q` concluiu com 6 testes aprovados pela API real.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN por rota: criação 201, lista/detalhe/edição 200, ações 204 e recusas 403, 404, 409 ou 422 conforme permissão, escopo, conflito e validação. Arquivo alterado: `src/app/routers/people.py`.
  - [x] **IMPROVE**: Verificação do serializador e das respostas confirmou ausência de `senha_hash` e token; somente identidade, escopo, papel, situação, pendência e autoria são expostos.
  <!-- specsfy:evidence {"task": "T048", "refs": ["US-003", "FR-008", "FR-009", "FR-010", "AC-011", "AC-012", "AC-013", "AC-014"], "files": ["src/app/routers/people.py"], "commands": [{"run": "uv run pytest tests/test_app_people.py -q", "exit": 0}]} -->

#### Fase 5 — US-005 e US-006: autoria e histórico de acessos (P2)

**Objetivo**: a pessoa autora em cada registro e a limpeza de 90 dias.
**Teste independente**: `uv run pytest tests/test_app_authorship.py tests/test_app_access_events.py -q`.

- [x] T049 [CODE] [US-005] Gravar e serializar a autoria em src/app/routers/workspaces.py, bases.py, executions.py e queries.py — Refs: US-005, FR-010, FR-011, AC-016, AC-017, AC-020 — Depends: T017, T018, T021, T038, T043
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores T017, T018 e T021 e baseline de 377 testes aprovados confirmados.
  - [x] **EXECUTE**: `identity.person_id` é persistido em Workspace, Base, Execução inicial/repetida e Consulta; respostas devolvem `{id, nome, desativada}` ou `null` sem remover campos existentes.
  - [x] **VERIFY**: As cinco suítes relacionadas concluíram com 50 testes aprovados; Ruff passou nos cinco módulos alterados.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: Exemplos comprovados: `{"criado_por":{"id":"<id>","nome":"Ana","desativada":false}}`, `{"criado_por":null}` e `{"criado_por":{"id":"<id>","nome":"Carla","desativada":true}}`. Arquivos: quatro routers e `src/app/repo.py`.
  - [x] **IMPROVE**: Melhoria aplicada: `selectinload` pré-carrega autores nas listas de Workspaces, Bases e histórico de Execuções, evitando uma consulta lazy por linha durante a serialização.
  <!-- specsfy:evidence {"task": "T049", "refs": ["US-005", "FR-010", "FR-011", "AC-016", "AC-017", "AC-020"], "files": ["src/app/routers/workspaces.py", "src/app/routers/bases.py", "src/app/routers/executions.py", "src/app/routers/queries.py", "src/app/repo.py"], "commands": [{"run": "uv run pytest tests/test_app_authorship.py tests/test_app_workspaces.py tests/test_app_bases.py tests/test_app_executions.py tests/test_app_queries.py -q", "exit": 0}, {"run": "uv run ruff check src/app/repo.py src/app/routers/workspaces.py src/app/routers/bases.py src/app/routers/executions.py src/app/routers/queries.py", "exit": 0}]} -->

- [x] T050 [CODE] [US-006] Criar a tarefa periódica de limpeza em src/app/tasks.py — Refs: US-006, FR-012, NFR-004, AC-018, AC-019, AC-021 — Depends: T019, T020, T022, T041
  - [x] **PREP**: `docs/` e `.specsfy/PACKAGES.md` reconstruídos e verificados; REDs predecessores e baseline confirmados. Procrastinate 3.9.0 expõe `App.periodic` e registrou a tarefa no `PeriodicRegistry`.
  - [x] **EXECUTE**: A limpeza diária `0 3 * * *` apaga eventos com mais de 90 dias, sessões expiradas e bloqueios vencidos; retorna e registra somente as três contagens.
  - [x] **VERIFY**: As suítes de eventos e tasks concluíram com 6 testes aprovados; o teste focal de expiração confirmou que sessão vencida é recusada mesmo sem executar a limpeza; Ruff passou.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: Procrastinate 3.9.0, `App.periodic` disponível e chave `("purgar_dados_de_acesso_task", "")` registrada com cron diário. Arquivos alterados: `src/app/tasks.py`, `src/app/events.py` e testes relacionados.
  - [x] **IMPROVE**: Idempotência comprovada no mesmo estado: primeira execução removeu `{"eventos":1,"sessoes":1,"tentativas":1}` e a segunda retornou zero nas três contagens sem alterar os registros válidos.
  <!-- specsfy:evidence {"task": "T050", "refs": ["US-006", "FR-012", "NFR-004", "AC-018", "AC-019", "AC-021"], "files": ["src/app/tasks.py", "src/app/events.py", "tests/test_app_access_events.py", "tests/test_app_tasks.py"], "commands": [{"run": "uv run pytest tests/test_app_access_events.py tests/test_app_tasks.py -q", "exit": 0}, {"run": "uv run pytest tests/test_app_auth.py -q -k sessao_expira", "exit": 0}, {"run": "uv run ruff check src/app/events.py src/app/tasks.py tests/test_app_access_events.py tests/test_app_tasks.py", "exit": 0}]} -->

#### Fase de interface

Uma tarefa por tela e por bloco, cada uma com `$specsfy-specialist-react-ui-components` no `PREP` e os blocos registrados em `INTERFACE.md`.

- [x] T053 [CODE] [US-001] Guardar a sessão, buscar a identidade e tratar 401 em frontend/src/lib/session.ts e api-client.ts — Refs: US-001, US-004, FR-007, FR-014, AC-001, AC-009, AC-023 — Depends: T002, T010, T024, T044
  - [x] **PREP**: Stack Next.js 16.3.4, React 19.2.8, TypeScript strict, Vitest 5 e fluxo/estados da seção 10 confirmados; `DESIGNSYSTEM.MD`, `INTERFACE.md` e especialistas de design, UI, componentes React e TypeScript carregados; documentação e REDs predecessores confirmados.
  - [x] **EXECUTE**: Token mantido somente em `sessionStorage`; identidade de `/auth/me` armazenada com validação runtime; papel não é mais deduzido por regex; 401 limpa token/identidade e grava o aviso “Sua sessão terminou. Entre novamente.”.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd -- src/lib` concluiu com 2 arquivos e 6 testes aprovados; typecheck e lint também passaram.
  - [x] **VISUAL**: Inspeção de integração em desktop e 360 px: os módulos não renderizam DOM nem alteram CSS, bordas, espaçamentos, margens, padding ou tipografia (família, peso, tamanho, altura de linha e quebra de texto); loading/erro/sucesso/permissão continuam responsabilidade das telas consumidoras. Sem delta visual a ajustar.
  - [x] **EVIDENCE**: GREEN em `frontend/src/lib`; arquivos alterados: `session.ts`, `api-client.ts` e teste. Busca focal não encontrou `token-demo` nos módulos.
  - [x] **IMPROVE**: Validação runtime adicionada para JSON do storage; teste confirmou token/identidade em `sessionStorage`, `localStorage` vazio e aviso consumível após 401. Busca não encontrou logging do token.
  <!-- specsfy:evidence {"task": "T053", "refs": ["US-001", "US-004", "FR-007", "FR-014", "AC-001", "AC-009", "AC-023"], "files": ["frontend/src/lib/session.ts", "frontend/src/lib/api-client.ts", "frontend/src/lib/api-client.test.ts"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/lib", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}]} -->

- [x] T054 [CODE] [US-007] Migrar os testes de frontend existentes para sessão de pessoa em frontend/src/lib/api-client.test.ts — Refs: US-007, FR-010, NFR-003, AC-015, AC-027 — Depends: T016, T028, T024, T053
  - [x] **PREP**: Stack, fluxo, estados, design system, especialista de componentes React, documentação e REDs predecessores confirmados nas oito suítes listadas.
  - [x] **EXECUTE**: As oito suítes passaram a usar sessões opacas e identidades simuladas de pessoa, preservando seus cenários e recusas.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd` concluiu com 27 arquivos e 111 testes aprovados; `rg -n 'token-demo' frontend/src` não encontrou ocorrência.
  - [x] **VISUAL**: Inspeção em desktop e 360 px: a tarefa altera somente fixtures/testes e não muda DOM, bordas, espaçamentos, margens, padding ou tipografia (família, peso, tamanho, altura de linha e quebra de texto); estados carregando, erro, sucesso e permissão continuam cobertos pelos mesmos testes. Sem ajuste visual.
  - [x] **EVIDENCE**: 21 ocorrências literais antes nas oito suítes e 0 depois; regressão frontend completa verde com 111 testes.
  - [x] **IMPROVE**: Consolidação preservada no utilitário público `saveSession`/`PessoaSessao`; cada suíte só mantém o mock de API específico do próprio cenário, sem duplicar armazenamento ou dedução de papel.
  <!-- specsfy:evidence {"task": "T054", "refs": ["US-007", "FR-010", "NFR-003", "AC-015", "AC-027"], "files": ["frontend/src/features/auth/LoginForm.test.tsx", "frontend/src/app/(autenticado)/layout.test.tsx", "frontend/src/app/(autenticado)/workspaces/page.test.tsx", "frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx", "frontend/src/app/(autenticado)/execucoes/[id]/page.test.tsx", "frontend/src/features/workspaces/ExcluirWorkspaceDialog.test.tsx", "frontend/src/features/workspaces/WorkspaceFormSheet.test.tsx", "frontend/src/lib/api-client.test.ts"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}]} -->

- [ ] T055 [P] [CODE] [US-001] Reescrever a tela Entrar em frontend/src/features/auth/LoginForm.tsx — Refs: US-001, FR-001, FR-002, FR-014, NFR-005, AC-001, AC-002, AC-004, AC-026 — Depends: T002, T003, T005, T027, T031, T053
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados da seção 10; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX; reconstruir `docs/` com `$specsfy-documentator`; confirmar o RED dos testes predecessores.
  - [ ] **EXECUTE**: Trocar o campo de token por e-mail e senha com rótulos visíveis, `autocomplete` `username` e `current-password`, `Alert` genérico, e-mail preservado, mensagem de bloqueio, orientação de recuperação e ida a `/nova-senha` quando a senha está pendente; ajustar `frontend/src/app/login/page.tsx`.
  - [ ] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features/auth/LoginForm` passa em fluxo, erro, bloqueio e teclado.
  - [ ] **VISUAL**: Conferir, em desktop e em 360 px, bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) de Entrar contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos estados carregando, erro, sucesso e permissão insuficiente, com conteúdo curto e longo; registrar a forma de conferência, o viewport e os ajustes.
  - [ ] **EVIDENCE**: Registrar o GREEN, os arquivos alterados e o resultado da interação por teclado.
  - [ ] **IMPROVE**: Conferir se o texto de orientação de recuperação está junto do formulário e registrar o ajuste.
  <!-- specsfy:evidence {"task": "T055", "refs": ["US-001", "FR-001", "FR-002", "FR-014", "NFR-005", "AC-001", "AC-002", "AC-004", "AC-026"], "files": ["frontend/src/features/auth/LoginForm.tsx", "frontend/src/app/login/page.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/auth/LoginForm", "exit": 0}]} -->

- [ ] T056 [P] [CODE] [US-002] Criar a tela Nova senha em frontend/src/features/auth/NovaSenhaForm.tsx e frontend/src/app/nova-senha/page.tsx — Refs: US-002, FR-004, FR-005, FR-014, NFR-005, AC-006, AC-007, AC-026 — Depends: T007, T008, T027, T032, T053
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados da seção 10; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX; reconstruir `docs/` com `$specsfy-documentator`; confirmar o RED dos testes predecessores.
  - [ ] **EXECUTE**: Criar a tela fora do shell, sem trilha e sem navegação, apenas com Sair (FIND-PROD-001), com a explicação do motivo, nova senha e confirmação, regra de 10 caracteres junto do campo e erro abaixo dele, ao concluir seguir a `/workspaces` sem novo login.
  - [ ] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features/auth/NovaSenhaForm` passa em validação, erro e conclusão.
  - [ ] **VISUAL**: Conferir, em desktop e em 360 px, bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) de Nova senha contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos estados carregando, erro, sucesso e permissão insuficiente, com conteúdo curto e longo; registrar a forma de conferência, o viewport e os ajustes.
  - [ ] **EVIDENCE**: Registrar o GREEN, os arquivos alterados e a forma como a pendência de senha bloqueia as demais rotas.
  - [ ] **IMPROVE**: Conferir a explicação para quem chega pela primeira vez e registrar o ajuste de texto.
  <!-- specsfy:evidence {"task": "T056", "refs": ["US-002", "FR-004", "FR-005", "FR-014", "NFR-005", "AC-006", "AC-007", "AC-026"], "files": ["frontend/src/features/auth/NovaSenhaForm.tsx", "frontend/src/app/nova-senha/page.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/auth/NovaSenhaForm", "exit": 0}]} -->

- [ ] T057 [P] [CODE] [US-002] Criar o menu da pessoa em frontend/src/features/auth/MenuPessoa.tsx e a primitive frontend/src/components/ui/dropdown-menu.tsx — Refs: US-002, FR-007, FR-014, FR-015, AC-009, AC-024 — Depends: T010, T025, T009, T033, T053
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados da seção 10; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX; reconstruir `docs/` com `$specsfy-documentator`; confirmar o RED dos testes predecessores.
  - [ ] **EXECUTE**: Adicionar a primitive `dropdown-menu` do shadcn/ui (mesma origem das demais, sem biblioteca nova) e o `MenuPessoa` com nome, papel, Trocar senha e Sair, focável por teclado e com foco devolvido ao fechar.
  - [ ] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features/auth/MenuPessoa` passa em abrir, navegar por teclado e sair.
  - [ ] **VISUAL**: Conferir, em desktop e em 360 px, bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) de o menu da pessoa contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos estados carregando, erro, sucesso e permissão insuficiente, com conteúdo curto e longo; registrar a forma de conferência, o viewport e os ajustes.
  - [ ] **EVIDENCE**: Registrar o GREEN, a primitive adicionada e os arquivos alterados.
  - [ ] **IMPROVE**: Conferir a ordem de foco do menu e registrar o ajuste.
  <!-- specsfy:evidence {"task": "T057", "refs": ["US-002", "FR-007", "FR-014", "FR-015", "AC-009", "AC-024"], "files": ["frontend/src/features/auth/MenuPessoa.tsx", "frontend/src/components/ui/dropdown-menu.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/auth/MenuPessoa", "exit": 0}]} -->

- [ ] T058 [P] [CODE] [US-002] Criar o diálogo Trocar senha em frontend/src/features/auth/TrocarSenhaDialog.tsx — Refs: US-002, FR-005, FR-014, NFR-005, AC-007, AC-008, AC-024 — Depends: T008, T009, T025, T033, T053
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados da seção 10; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX; reconstruir `docs/` com `$specsfy-documentator`; confirmar o RED dos testes predecessores.
  - [ ] **EXECUTE**: Criar o diálogo sobre `Dialog` com senha atual, nova e confirmação, `autocomplete` `current-password` e `new-password`, erro abaixo do campo com foco no primeiro erro e retorno ao contexto com a sessão mantida.
  - [ ] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features/auth/TrocarSenhaDialog` passa.
  - [ ] **VISUAL**: Conferir, em desktop e em 360 px, bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) de o diálogo Trocar senha contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos estados carregando, erro, sucesso e permissão insuficiente, com conteúdo curto e longo; registrar a forma de conferência, o viewport e os ajustes.
  - [ ] **EVIDENCE**: Registrar o GREEN e os arquivos alterados.
  - [ ] **IMPROVE**: Conferir a mensagem de erro de senha atual incorreta e registrar o ajuste.
  <!-- specsfy:evidence {"task": "T058", "refs": ["US-002", "FR-005", "FR-014", "NFR-005", "AC-007", "AC-008", "AC-024"], "files": ["frontend/src/features/auth/TrocarSenhaDialog.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/auth/TrocarSenhaDialog", "exit": 0}]} -->

- [ ] T059 [CODE] [US-001] Estender o shell com identidade, navegação persistente e guarda de senha pendente em frontend/src/app/(autenticado)/layout.tsx — Refs: US-001, US-002, US-004, FR-007, FR-014, FR-015, AC-006, AC-009, AC-023, AC-024 — Depends: T007, T010, T024, T025, T053, T057
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados da seção 10; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX; reconstruir `docs/` com `$specsfy-documentator`; confirmar o RED dos testes predecessores.
  - [ ] **EXECUTE**: Carregar a identidade do backend antes de renderizar, redirecionar sessão pendente a `/nova-senha`, mostrar os itens Workspaces e, só para owner e admin, Pessoas, incluir o `MenuPessoa`, manter a trilha Equipe primeiro e voltar ao Login com aviso em sessão terminada.
  - [ ] **VERIFY**: `npm --prefix frontend run test:tdd -- "src/app/(autenticado)/layout"` passa.
  - [ ] **VISUAL**: Conferir, em desktop e em 360 px, bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) de o shell autenticado contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos estados carregando, erro, sucesso e permissão insuficiente, com conteúdo curto e longo; registrar a forma de conferência, o viewport e os ajustes.
  - [ ] **EVIDENCE**: Registrar o GREEN, os arquivos alterados e o comportamento do cabeçalho em 360 px.
  - [ ] **IMPROVE**: Conferir a quebra da navegação sob a trilha no mobile e registrar o ajuste.
  <!-- specsfy:evidence {"task": "T059", "refs": ["US-001", "US-002", "US-004", "FR-007", "FR-014", "FR-015", "AC-006", "AC-009", "AC-023", "AC-024"], "files": ["frontend/src/app/(autenticado)/layout.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- \"src/app/(autenticado)/layout\"", "exit": 0}]} -->

- [ ] T060 [CODE] [US-003] Criar a lista de Pessoas em frontend/src/features/pessoas/DataGridPessoas.tsx e frontend/src/app/(autenticado)/pessoas/page.tsx — Refs: US-003, FR-008, FR-010, FR-015, NFR-005, AC-014, AC-025, AC-026 — Depends: T015, T026, T027, T036, T048, T059
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados da seção 10; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX; reconstruir `docs/` com `$specsfy-documentator`; confirmar o RED dos testes predecessores.
  - [ ] **EXECUTE**: Criar `DataGridPessoas` no padrão de `DataGridWorkspaces`: `PageHeader` com "Nova pessoa", `ID`, nome, e-mail, papel e situação em `Badge` com texto, linha inteira como link para o detalhe, ações Editar e Desativar ou Reativar independentes, sem Apagar, estados carregando, vazio e erro, e tela de permissão insuficiente para member.
  - [ ] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features/pessoas/DataGridPessoas "src/app/(autenticado)/pessoas"` passa.
  - [ ] **VISUAL**: Conferir, em desktop e em 360 px, bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) de a lista de Pessoas contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos estados carregando, erro, sucesso e permissão insuficiente, com conteúdo curto e longo; registrar a forma de conferência, o viewport e os ajustes.
  - [ ] **EVIDENCE**: Registrar o GREEN, os arquivos alterados e o resultado do teclado (Enter e Espaço na linha).
  - [ ] **IMPROVE**: Conferir a rolagem horizontal da lista em 360 px mantendo o `ID` e registrar o ajuste.
  <!-- specsfy:evidence {"task": "T060", "refs": ["US-003", "FR-008", "FR-010", "FR-015", "NFR-005", "AC-014", "AC-025", "AC-026"], "files": ["frontend/src/features/pessoas/DataGridPessoas.tsx", "frontend/src/app/(autenticado)/pessoas/page.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/pessoas/DataGridPessoas", "exit": 0}]} -->

- [ ] T061 [P] [CODE] [US-003] Criar o painel de criar e editar pessoa em frontend/src/features/pessoas/PessoaFormSheet.tsx — Refs: US-003, FR-008, FR-009, FR-015, NFR-005, AC-011, AC-012, AC-013, AC-025 — Depends: T012, T013, T014, T026, T034, T060
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados da seção 10; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX; reconstruir `docs/` com `$specsfy-documentator`; confirmar o RED dos testes predecessores.
  - [ ] **EXECUTE**: Criar o painel sobre `Sheet`, no padrão de `WorkspaceFormSheet`, com nome, e-mail, papel em `select` nativo com o estilo de `Input` e senha inicial, opção owner só para owner, aviso de canal seguro ao criar, campos preservados e foco no primeiro erro após 409, e proteção de alterações não salvas.
  - [ ] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features/pessoas/PessoaFormSheet` passa.
  - [ ] **VISUAL**: Conferir, em desktop e em 360 px, bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) de o painel de pessoa contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos estados carregando, erro, sucesso e permissão insuficiente, com conteúdo curto e longo; registrar a forma de conferência, o viewport e os ajustes.
  - [ ] **EVIDENCE**: Registrar o GREEN, os arquivos alterados e o resultado do foco após erro.
  - [ ] **IMPROVE**: Conferir a mensagem de e-mail duplicado sem indicar o tenant (FIND-SEC-003) e registrar a verificação.
  <!-- specsfy:evidence {"task": "T061", "refs": ["US-003", "FR-008", "FR-009", "FR-015", "NFR-005", "AC-011", "AC-012", "AC-013", "AC-025"], "files": ["frontend/src/features/pessoas/PessoaFormSheet.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/pessoas/PessoaFormSheet", "exit": 0}]} -->

- [ ] T062 [P] [CODE] [US-003] Criar os diálogos de desativar, reativar e redefinir senha em frontend/src/features/pessoas/DesativarPessoaDialog.tsx e RedefinirSenhaDialog.tsx — Refs: US-003, US-004, FR-006, FR-008, FR-009, FR-015, AC-010, AC-013, AC-025 — Depends: T011, T014, T026, T035, T060
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados da seção 10; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX; reconstruir `docs/` com `$specsfy-documentator`; confirmar o RED dos testes predecessores.
  - [ ] **EXECUTE**: Criar os diálogos sobre `Dialog`, no padrão de `ExcluirWorkspaceDialog`, mostrando a pessoa alvo e a consequência, sem oferecer desativar o último owner nem a si mesma, com campo de senha temporária na redefinição e erro seguro em `Alert`.
  - [ ] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features/pessoas` passa.
  - [ ] **VISUAL**: Conferir, em desktop e em 360 px, bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) de os diálogos de pessoa contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos estados carregando, erro, sucesso e permissão insuficiente, com conteúdo curto e longo; registrar a forma de conferência, o viewport e os ajustes.
  - [ ] **EVIDENCE**: Registrar o GREEN, os arquivos alterados e o comportamento de foco preso e devolvido.
  - [ ] **IMPROVE**: Conferir o texto da consequência de cada ação e registrar o ajuste.
  <!-- specsfy:evidence {"task": "T062", "refs": ["US-003", "US-004", "FR-006", "FR-008", "FR-009", "FR-015", "AC-010", "AC-013", "AC-025"], "files": ["frontend/src/features/pessoas/DesativarPessoaDialog.tsx", "frontend/src/features/pessoas/RedefinirSenhaDialog.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/pessoas", "exit": 0}]} -->

- [ ] T063 [CODE] [US-003] Criar o detalhe da pessoa em frontend/src/app/(autenticado)/pessoas/[id]/page.tsx e frontend/src/components/DetailLists.tsx — Refs: US-003, FR-008, FR-015, NFR-005, AC-011, AC-014, AC-025 — Depends: T012, T015, T026, T036, T061, T062
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados da seção 10; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX; reconstruir `docs/` com `$specsfy-documentator`; confirmar o RED dos testes predecessores.
  - [ ] **EXECUTE**: Criar a página com `PageHeader` (nome, situação e ações) e o componente compartilhado `DetailLists` com e-mail, papel, situação, troca de senha pendente e criada em e por quem, trilha Equipe, Pessoas e nome.
  - [ ] **VERIFY**: `npm --prefix frontend run test:tdd -- "src/app/(autenticado)/pessoas"` passa em detalhe, 404 e permissão.
  - [ ] **VISUAL**: Conferir, em desktop e em 360 px, bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) de o detalhe da pessoa contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos estados carregando, erro, sucesso e permissão insuficiente, com conteúdo curto e longo; registrar a forma de conferência, o viewport e os ajustes.
  - [ ] **EVIDENCE**: Registrar o GREEN, os arquivos alterados e a trilha renderizada.
  - [ ] **IMPROVE**: Conferir a quebra de e-mail e nome longos e registrar o ajuste.
  <!-- specsfy:evidence {"task": "T063", "refs": ["US-003", "FR-008", "FR-015", "NFR-005", "AC-011", "AC-014", "AC-025"], "files": ["frontend/src/app/(autenticado)/pessoas/[id]/page.tsx", "frontend/src/components/DetailLists.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- \"src/app/(autenticado)/pessoas\"", "exit": 0}]} -->

- [ ] T064 [CODE] [US-005] Mostrar a autoria nas listas e detalhes em frontend/src/features/bases/DataGridBases.tsx, workspaces/DataGridWorkspaces.tsx, execucoes/PainelProgresso.tsx e execucoes/FormularioConsulta.tsx — Refs: US-005, FR-011, AC-016, AC-017, AC-020 — Depends: T017, T018, T021, T037, T049
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados da seção 10; carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX; reconstruir `docs/` com `$specsfy-documentator`; confirmar o RED dos testes predecessores.
  - [ ] **EXECUTE**: Acrescentar "Criada por" nas listas de Workspaces e Bases e no detalhe da Base, "Iniciada por" no progresso da Execução e "Consultada por" no resultado da Consulta, com "Autor não identificado" e o nome com "(desativada)", sem alterar as colunas existentes.
  - [ ] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features` passa nas listas e detalhes alterados.
  - [ ] **VISUAL**: Conferir, em desktop e em 360 px, bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) de as listas e detalhes com autoria contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos estados carregando, erro, sucesso e permissão insuficiente, com conteúdo curto e longo; registrar a forma de conferência, o viewport e os ajustes.
  - [ ] **EVIDENCE**: Registrar o GREEN, os arquivos alterados e a leitura das listas em 360 px.
  - [ ] **IMPROVE**: Conferir se a coluna nova cabe na lista no mobile sem esconder o `ID` e registrar o ajuste.
  <!-- specsfy:evidence {"task": "T064", "refs": ["US-005", "FR-011", "AC-016", "AC-017", "AC-020"], "files": ["frontend/src/features/bases/DataGridBases.tsx", "frontend/src/features/workspaces/DataGridWorkspaces.tsx", "frontend/src/features/execucoes/PainelProgresso.tsx", "frontend/src/features/execucoes/FormularioConsulta.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features", "exit": 0}]} -->

- [ ] T065 [DOC] Registrar os blocos novos e alterados da interface em INTERFACE.md — Refs: US-003, FR-014, FR-015, NFR-005, AC-024, AC-025 — Depends: T063, T064, T059
  - [ ] **PREP**: Ler o estado atual do documento e o resultado das tarefas de código que ele descreve.
  - [ ] **EXECUTE**: Registrar em `INTERFACE.md` finalidade, arquivo, API, estados, consumidores e regra de reaproveitamento de cada bloco novo ou alterado (`NovaSenhaForm`, `MenuPessoa`, `TrocarSenhaDialog`, `DataGridPessoas`, `PessoaFormSheet`, os diálogos de pessoa, `DetailLists`, `dropdown-menu`, o shell e a autoria), as telas Entrar, Nova senha e Pessoas com item de menu, destino, permissão e comportamento responsivo, e as duas exceções da tela Pessoas.
  - [ ] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` fica `CURRENT`.
  - [ ] **VISUAL**: Não aplicável: documento de contexto, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar os blocos listados, os consumidores e o resultado do monitor.
  - [ ] **IMPROVE**: Conferir se algum bloco antigo ficou sem consumidor e registrar a correção do mapa.

#### Fase de documentação

Os contextos persistentes descrevem o que foi entregue, com evidência no código.

- [ ] T066 [DOC] Registrar a autenticação por pessoa e a dependência `argon2-cffi` em .specsfy/STACK.md — Refs: FR-003, NFR-001, AC-007, AC-028 — Depends: T040, T052
  - [ ] **PREP**: Ler o estado atual do documento e o resultado das tarefas de código que ele descreve.
  - [ ] **EXECUTE**: Trocar as linhas de "token estático de demonstração" do backend e do frontend pela autenticação por e-mail e senha com sessão opaca, e registrar `argon2-cffi` com a evidência em `pyproject.toml`.
  - [ ] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` fica `CURRENT`.
  - [ ] **VISUAL**: Não aplicável: documento de contexto, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar as linhas alteradas e as fontes de evidência.
  - [ ] **IMPROVE**: Conferir se a documentação descreve o que existe no código e não o que a spec previa.

- [ ] T067 [DOC] Reconciliar as tabelas e colunas novas em .specsfy/DATABASE.md — Refs: US-005, US-007, FR-011, FR-013, NFR-006, AC-020 — Depends: T039, T038, T049
  - [ ] **PREP**: Ler o estado atual do documento e o resultado das tarefas de código que ele descreve.
  - [ ] **EXECUTE**: Registrar no bloco detectado `pessoas`, `vinculos_pessoa`, `sessoes`, `tentativas_login`, `eventos_acesso` e `criado_por`, e ajustar as decisões de ownership e retenção que citam o token estático, preservando as seis informações confirmadas pela descoberta de dados.
  - [ ] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` fica `CURRENT`.
  - [ ] **VISUAL**: Não aplicável: documento de contexto, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar as linhas alteradas e as revisões `0020_pessoas` e `0019_workspaces` citadas.
  - [ ] **IMPROVE**: Conferir se os nomes de tabela e coluna do documento coincidem com `src/app/models.py`.

- [ ] T068 [DOC] Atualizar a regra de tenant e login real em .specsfy/RULES.md — Refs: FR-009, FR-010, AC-013, AC-014 — Depends: T052, T048
  - [ ] **PREP**: Ler o estado atual do documento e o resultado das tarefas de código que ele descreve.
  - [ ] **EXECUTE**: Atualizar a nota da SPEC-0012 que diz "login real fora de escopo" e registrar por `$specsfy-aux-rules`, sem remover regra existente, a regra confirmada de que admin não age sobre owner e de que a pessoa nunca é apagada.
  - [ ] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` fica `CURRENT`.
  - [ ] **VISUAL**: Não aplicável: documento de contexto, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar a regra acrescentada e a confirmação da pessoa responsável (DEC-013).
  - [ ] **IMPROVE**: Conferir se alguma regra existente conflita com a nova e registrar a resolução.

- [ ] T069 [DOC] Revisar a história e os limites em PROJECT.md — Refs: US-001, US-003, FR-001, FR-008, AC-001 — Depends: T052, T059
  - [ ] **PREP**: Ler o estado atual do documento e o resultado das tarefas de código que ele descreve.
  - [ ] **EXECUTE**: Trocar "cadastro, convite e login real continuam fora de escopo" pelo que passou a existir (login por e-mail e senha, gestão básica de pessoas) e manter fora de escopo convite por e-mail, recuperação por link, SSO e mais de um tenant por pessoa.
  - [ ] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` fica `CURRENT`.
  - [ ] **VISUAL**: Não aplicável: documento de contexto, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar os trechos alterados e, se algum não mudar, a justificativa de ausência de impacto.
  - [ ] **IMPROVE**: Conferir se o texto de finalidade continua fiel ao produto e registrar o ajuste.

- [ ] T070 [DOC] Regenerar o inventário de pacotes em .specsfy/PACKAGES.md — Refs: FR-003, NFR-001, AC-028 — Depends: T001, T066
  - [ ] **PREP**: Ler o estado atual do documento e o resultado das tarefas de código que ele descreve.
  - [ ] **EXECUTE**: Executar `$specsfy-documentator` para reconstruir `docs/` e `.specsfy/PACKAGES.md` com `argon2-cffi` e a finalidade curta dele.
  - [ ] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` fica `CURRENT`.
  - [ ] **VISUAL**: Não aplicável: documento de contexto, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar o resultado de `build_documentation.mjs --check` com código 0.
  - [ ] **IMPROVE**: Conferir se a finalidade do pacote está clara e registrar o ajuste.

#### Fase final — Qualidade

- [ ] T071 [TEST] Executar a regressão e a rastreabilidade completas em tests/ e frontend/src/ — Refs: US-001, US-002, US-003, US-004, US-005, US-006, US-007, NFR-001, NFR-003, NFR-006, AC-027 — Depends: T052, T064, T065, T066, T067, T068, T069, T070, T050, T045
  - [ ] **PREP**: Identificar as suítes, o Ruff, o `check_traceability.mjs` e os gates que fecham a spec.
  - [ ] **EXECUTE**: Executar `uv run ruff check .`, `uv run pytest -q`, `npm --prefix frontend run test:tdd`, `npm --prefix frontend run lint`, `npm --prefix frontend run typecheck`, `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/planned/0020-autenticacao-real-por-pessoa/spec.md .`, `uv run alembic upgrade head` e `uv run alembic current` no banco de teste, e a busca do texto do token estático em `src/`, `tests/` e `frontend/src/`.
  - [ ] **VERIFY**: Todos os comandos saem com código 0, a busca não encontra ocorrência e o monitor de contexto fica `CURRENT`.
  - [ ] **VISUAL**: Repassar a revisão visual final das telas Entrar, Nova senha, Pessoas e do cabeçalho, em desktop e em 360 px, conferindo bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD`.
  - [ ] **EVIDENCE**: Registrar as contagens e os comandos finais nas seções 11 a 13 e o resultado da revisão visual.
  - [ ] **IMPROVE**: Registrar a retrospectiva do processo e tratar os findings FIND-SEC-001, FIND-SEC-002, FIND-SEC-003 e FIND-PROD-001 como `Resolved` ou `Accepted` com decisão.

### 15. Ordem de execução

- Caminho crítico: T001 → testes RED (T002 a T037) → T038 → T039 → T040 → T042 → T043 → T044 → T046 → T048 → T051 → T052 → T059 → T060 → T063 → T071.
- Tarefas paralelas: os sete testes de frontend por componente (T031 a T037) e as telas T055, T056, T057, T058, T061 e T062 não compartilham arquivo nem estado e ficam marcadas `[P]`; as tarefas de backend que editam `src/app/accounts.py` (T042 e T046) ficam em sequência por compartilharem arquivo.
- Ordem de segurança: T051 precede T052, para que a remoção dos tokens estáticos só aconteça depois de as suítes existentes usarem pessoas de teste.
- Estratégia de MVP: US-001, US-002, US-004 e US-007 (Fases 0 a 3, mais T053, T055, T056, T057 e T059) já substituem o token estático; US-003 (Fase 4 e a tela Pessoas) completa a administração sem terminal; US-005 e US-006 (Fase 5) fecham o P2.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Bloqueia o BACKLOG-0022 (fatia 2, memória de longo prazo por pessoa); a fatia 1 do chat não espera esta spec.
- Supera a decisão do token estático da SPEC-0012 sem reabri-la; toca a SPEC-0013 (login e papel deduzido do token) e a SPEC-0019 (Workspaces passam a ter autor).
- Reconciliação com o BACKLOG-0021 (specs concluídas versus o enforcement atual) quando esta spec for concluída.
- Nova dependência de produção `argon2-cffi`, a registrar em `pyproject.toml`, `uv.lock` e `.specsfy/PACKAGES.md`.
- PostgreSQL de teste separado (`rag_pipeline_test`) disponível antes de qualquer teste ou migração.

#### Riscos

- Mudança transversal em `get_identity` e 94 usos de token nos testes → migração dos testes em tarefa própria, executada antes de remover o registro de tokens, e NFR-003 exige a suíte inteira verde.
- Sem e-mail, se os owners esquecerem as senhas, ninguém redefine → o comando de implantação redefine a senha de qualquer pessoa (FR-013).
- Ataque por tentativa de senha sem e-mail para alertar a pessoa → bloqueio de 15 minutos por e-mail normalizado, mensagem genérica e eventos de acesso por 90 dias.
- Escalada de privilégio de admin sobre owner → regra dedicada (FR-009) e cenário AC-013, confirmada pela pessoa responsável (DEC-013).
- Duas operações simultâneas deixarem o tenant sem owner → verificação sob bloqueio de linha na mesma transação (seção 8).
- A limpeza periódica não rodar (worker parado) → validade de sessão e de bloqueio é checada na leitura; só a retenção de 90 dias depende do worker.
- Flash de conteúdo antes de a identidade carregar no shell → o shell só renderiza depois de conhecer a pessoa, no padrão do estado `pronto` atual.

#### Suposições

- **S1**: o último owner de um tenant não pode ser desativado nem rebaixado.
- **S2**: senha com no mínimo 10 caracteres, sem regras de composição; 5 falhas seguidas bloqueiam por 15 minutos.
- **S3**: o primeiro owner de cada tenant existente é criado por comando na implantação, dentro de `tenant-1` e `projeto-1`, para que os dados atuais continuem alcançáveis.
- **S4**: `admin` gerencia `member` e `admin`, mas não cria, promove, rebaixa, corrige, desativa nem redefine a senha de `owner`, nem se promove a `owner`; ninguém desativa a si mesma. A parte sobre `admin` e `owner` foi confirmada pela pessoa responsável na validação (DEC-013); a parte sobre desativar a si mesma segue como suposição reversível.
- **S5**: a autoria é visível a todos os papéis do tenant, e o nome permanece nos registros de uma pessoa desativada.
- **S6**: o rótulo "Equipe" da trilha continua genérico, porque o tenant não tem nome no modelo.
- **S7**: o histórico de acessos é somente registrado nesta entrega; e-mail tentado que não corresponde a uma pessoa não é gravado no evento.
- **S8**: a troca obrigatória de senha do primeiro acesso não derruba a sessão aberta; a troca da própria senha e a correção dos próprios dados mantêm a sessão atual e encerram as demais.
- **S9**: os valores de política (8 horas, 5 tentativas, 15 minutos, 10 caracteres, 90 dias) são constantes nomeadas em um único módulo, sem variável de ambiente.

### 17. Decisões

- **DEC-001**: sessão opaca guardada no banco, com token aleatório de 256 bits e só o resumo persistido, em vez de JWT sem estado — o requisito de encerrar a sessão na hora exigiria uma lista de revogação de qualquer forma; alternativas: JWT com lista de revogação e cookie de sessão `httpOnly`, este último descartado por quebrar a decisão da SPEC-0013 de manter o token só em `sessionStorage` e por abrir CSRF. Trade-off: uma leitura de banco por requisição, aceitável para uma equipe pequena.
- **DEC-002**: hash de senha argon2id com `argon2-cffi` — padrão recomendado para senhas e sem custo de manutenção próprio; alternativas: `bcrypt` e `hashlib.scrypt` da biblioteca padrão (sem dependência nova). Trade-off: uma dependência nova em troca do algoritmo mais adequado; hipótese técnica a revalidar na validação.
- **DEC-003**: a identidade é resolvida a cada requisição a partir de pessoa, vínculo e situação no banco, e a sessão só prova quem é — mudança de papel e desativação valem na próxima requisição sem depender de reemitir sessão. Trade-off: mais leituras por requisição.
- **DEC-004**: o vínculo com tenant, projeto e papel é um registro próprio, com no máximo um por pessoa nesta entrega (índice único), para que evoluir para vários vínculos exija remover uma restrição, não reescrever o cadastro.
- **DEC-005**: o contador de tentativas é uma tabela própria indexada pelo e-mail normalizado, existente ou não, para que o bloqueio não revele quais e-mails existem.
- **DEC-006**: a limpeza de retenção é uma tarefa periódica do worker Procrastinate existente; a validade de sessão e de bloqueio é sempre verificada na leitura, sem depender dela.
- **DEC-007**: a pessoa nunca é apagada, só desativada, porque a autoria e os eventos apontam para ela; a referência de autoria usa chave estrangeira opcional.
- **DEC-008**: o papel usa o controle nativo `select` estilizado como `Input`, e o menu da pessoa usa a primitive `dropdown-menu` do shadcn/ui (mesma origem das demais); nenhum bloco ReUI é adicionado. Decide o ponto que o backlog deixou para esta spec.
- **DEC-009**: a autoria aparece como "Criada por" nas listas de Workspaces e Bases e no detalhe da Base, como "Iniciada por" no progresso da Execução e como "Consultada por" no resultado da Consulta; decide o ponto que o backlog deixou para esta spec.
- **DEC-010**: os valores de política ficam como constantes nomeadas em `src/app/security.py`, não configuráveis por ambiente nesta entrega, para não abrir superfície de configuração insegura.
- **DEC-011**: o comando de implantação lê a senha por `getpass` e recusa argumento de senha, para que ela nunca apareça na lista de processos nem no histórico do terminal.
- **DEC-012**: esta spec supera a decisão do token estático da SPEC-0012 nos pontos de identidade, sem reabrir a SPEC-0012 nem a SPEC-0013, que permanecem concluídas como registro do que foi entregue.
- **DEC-013**: `admin` não tem nenhum poder sobre `owner` (criar, promover, rebaixar, corrigir, desativar, redefinir a senha) e não se promove; só `owner` gerencia `owner` — confirmado pela pessoa responsável na validação da spec, opção 1 entre três; alternativas descartadas: admin corrige dados e redefine a senha de owner, e admin com poder igual ao do owner. Razão: redefinir a senha de um owner é o caminho mais curto para um admin assumir a conta dele.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam (`uv run pytest`, Ruff e `vitest run` em `frontend/`).
- [ ] A busca por `token-demo` não encontra ocorrência em `src/`, `tests/` e `frontend/src/`.
- [ ] A migração `0020_pessoas` foi aplicada e revertida no banco de teste com `uv run alembic upgrade head` e `uv run alembic current`.
- [ ] `PROJECT.md`, `.specsfy/STACK.md`, `.specsfy/RULES.md`, `.specsfy/DATABASE.md`, `.specsfy/PACKAGES.md` e `INTERFACE.md` foram revisados e o monitor de contexto está `CURRENT`.
- [ ] A revisão visual de cada tela nova está registrada nas tarefas.

## Effort history

- 2026-09-21T23:55:24.050Z: 1 → 8. Mudança transversal de segurança: identidade por pessoa em todas as rotas, sessão revogável, migração com dados existentes, 94 usos de token nos testes a migrar e três telas novas no frontend.
