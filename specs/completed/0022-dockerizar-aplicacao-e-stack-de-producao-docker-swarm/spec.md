# Especificação integrada: Dockerizar a aplicação e criar o stack de produção (Docker Swarm)

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0022 |
| Slug | 0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm |
| Status | Complete |
| Effort | 5 |
| Effort updated at | 2026-09-28 |
| Effort rationale | Dockerização multi-serviço (backend, worker, frontend) com especificidades reais de produção (placement por node, secrets, integração com rede overlay e reverse proxy já existentes na VPS compartilhada) — perfil `standard`. Não introduz schema, domínio ou comportamento novo para pessoa usuária, o que reduz a carga em relação a uma feature de produto. |
| ClickUp Task | |
| Milestones | M03 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-10-03 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O sistema (`rag-pipeline`) hoje só roda localmente: frontend por `next dev`,
backend FastAPI local, Postgres de teste via `docker-compose.yml` na raiz.
Não existe nenhum Dockerfile de produção, nenhuma definição de como os
serviços (backend, frontend, worker Procrastinate, Postgres, Qdrant) rodam
juntos fora do ambiente de desenvolvimento, e nenhuma forma de subir a
aplicação num servidor real.

#### Resultado desejado

Marcio consegue subir toda a aplicação em produção com um único comando
(`docker stack deploy`) no VPS que já opera via Docker Swarm, com Postgres e
Qdrant de produção isolados dos recursos de teste, credenciais geridas por
`docker secrets` e integração com a rede overlay e o reverse proxy já
existentes na mesma VPS — sem afetar as demais aplicações já em produção
nela.

#### Métricas de sucesso

- `docker stack deploy` sobe os cinco serviços (backend, frontend, worker,
  Postgres de produção, Qdrant de produção) e todos alcançam o estado
  `Running`, verificável por `docker service ls`.
- Nenhuma credencial de produção aparece em texto puro no stack file
  versionado nem em log de container.

### 2. Research e esclarecimentos

#### Researchs executados

- Nenhuma pesquisa externa foi necessária: Docker Swarm, `docker stack
  deploy`, `docker secret` e `deploy.placement.constraints` são
  funcionalidades nativas e estáveis do Docker Engine, já em uso real pela
  pessoa responsável em outras aplicações da mesma VPS.

#### Fontes e contexto consultados

- `specs/backlog/0028-dockerizar-aplicacao-e-stack-de-producao-docker-swarm.md` — brief completo, origem desta spec.
- `specs/milestones/M03.md` — marco de origem (Deploy em Beta, Docker Swarm).
- `PROJECT.md`, `.specsfy/STACK.md` — stack atual: Python 3.12+/`uv`, FastAPI, SQLAlchemy/Alembic, Procrastinate, Next.js 16, Qdrant.
- `docker-compose.yml` (raiz) — hoje só provisiona `rag-pipeline-test-postgres` (porta 55432); não deve ser confundido nem reaproveitado para produção.
- `README.md` (seções "Rodar o worker") — confirma que o worker Procrastinate roda pelo mesmo código-base do backend, via `uv run python -m src.app.worker` (que importa `src.app.main`), sem entrypoint próprio distinto.
- `frontend/next.config.ts` — confirma `rewrites()` de `/api/*` para `API_PROXY_TARGET` (default `http://127.0.0.1:8000`), sem `output: "standalone"` configurado ainda; e uma CSP restrita a `'self'`.
- `.github/workflows/ci.yml` — versões usadas em CI: Python 3.12, Node 24.
- Exemplo real de stack file de produção compartilhado por Marcio durante o
  aprofundamento do backlog (Postgres do n8n): convenção de nome de serviço
  `<tecnologia>_<app>`, rede overlay externa `network_swarm_public`, volume
  nomeado `external: true`, `deploy.placement.constraints` por
  `node.hostname`, limites de `cpus`/`memory` por serviço.

#### Documentação consultada

- Nenhuma documentação externa nova; Docker Swarm/Compose v3.7 já documentado
  no exemplo real fornecido e no conhecimento consolidado da stack.

#### Artefatos de pesquisa armazenados

- Evidência local de execução: `specs/completed/0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm/research/t017-swarm-local.json` (2026-10-03, Codex; resultados por AC, recursos locais e hashes SHA-256; sem valores de secrets).
- Nenhum artefato externo armazenado. O exemplo de stack file citado acima
  foi colado na conversa (dado operacional da pessoa responsável, não
  documentação de terceiro), e suas convenções já estão registradas nesta
  spec e no BACKLOG-0028; não há licença ou termo de terceiro a preservar.

#### Dúvidas respondidas

- **Q**: onde as imagens Docker são construídas? → **A**: build direto no VPS, sem registry nesta fase (decisão do aprofundamento do backlog).
- **Q**: o Swarm é single-node ou multi-node? → **A**: multi-node; Postgres/Qdrant de produção deste projeto são fixados no node dedicado a banco de dados já usado por outras aplicações.
- **Q**: como gerir credenciais de produção? → **A**: `docker secrets`, não variável de ambiente em texto puro (diferente do padrão mais simples usado em outras stacks da VPS, escolhido aqui por lidar com chave de LLM e storage).
- **Q**: já existe reverse proxy/TLS compartilhado na VPS? → **A**: sim, Traefik (ou similar) já roda na rede `network_swarm_public` com HTTPS automático por labels; este item só conecta a essa rede, sem criar proxy próprio (o `BACKLOG-0029` cuida das labels específicas de domínio).
- **Q**: o worker Procrastinate precisa de imagem própria? → **A**: não — reaproveita a mesma imagem do backend (mesmo código-base Python), mudando apenas o comando do serviço (`uvicorn` vs `python -m src.app.worker`), decisão registrada como `DEC-001`.

#### Dúvidas abertas

- Nenhuma bloqueante para a definição. Nome exato do node de banco de dados e
  limites de CPU/memória por serviço ficam para a implementação (`Ato II`),
  sem impedir `Definition Gate`.

### 3. Escopo e atores

#### Incluído

- Dockerfile de produção para o backend FastAPI (reaproveitado também pelo
  worker Procrastinate, mudando só o comando do container).
- Dockerfile de produção para o frontend Next.js.
- Stack file de Docker Swarm (`deploy/stack.prod.yml`) cobrindo os cinco
  serviços: backend, frontend, worker, Postgres de produção e Qdrant de
  produção.
- Postgres e Qdrant de produção como serviços do próprio stack, com dados em
  volumes Docker nomeados e externos (criados manualmente antes do primeiro
  deploy), distintos dos recursos de teste.
- `deploy.placement.constraints` fixando Postgres e Qdrant de produção no
  node dedicado a banco de dados já usado por outras aplicações da VPS.
- `deploy.placement.constraints` fixando backend, frontend e worker no node
  que executou o build local, pois esta fase não possui registry para
  distribuir as imagens aos demais nodes do Swarm.
- Conexão do stack à rede overlay externa `network_swarm_public` já existente
  e já servida por reverse proxy com HTTPS automático.
- Leitura de credenciais de produção (senha do Postgres, chave OpenRouter,
  credenciais Cloudflare R2, segredo de sessão) via `docker secret`,
  referenciadas pelos serviços que precisam delas.
- Ajuste mínimo do frontend para produção: `output: "standalone"` em
  `next.config.ts` (build enxuto para container) e `API_PROXY_TARGET`
  apontando para o serviço `backend` pelo nome DNS interno do Swarm, não
  `127.0.0.1`.

#### Fora de escopo

- Domínio, TLS e labels específicas do Traefik para este projeto (`BACKLOG-0029`).
- Criação dos `docker secrets` em si e seu conteúdo real (`BACKLOG-0030`).
- Backup automático do Postgres de produção (`BACKLOG-0031`).
- Runbook documentado do processo de deploy manual (`BACKLOG-0032`).
- Registry de imagens Docker e qualquer pipeline de CI/CD automatizado para deploy.
- Provisionamento de servidor novo — o VPS já existe e já roda Docker Swarm.
- Qualquer mudança de comportamento do backend, frontend ou worker que não
  seja estritamente necessária para rodar em container (não é uma feature de
  produto).

#### Atores

- **Marcio**: opera o build das imagens e o `docker stack deploy` no VPS; único ator desta entrega.

### 4. Princípios e restrições do projeto

- **PR-001**: Nenhum dado de produção pode ser gravado nos recursos de teste
  (`rag-pipeline-test-postgres` ou coleção de teste do Qdrant), nem
  vice-versa — isolamento total entre ambientes (herdado do BACKLOG-0028).
- **PR-002**: Nenhuma credencial de produção pode aparecer em texto puro no
  stack file versionado nem em log de container — apenas via `docker
  secret`.
- **PR-003**: Esta entrega não pode alterar nem interromper as demais
  aplicações já em produção na mesma VPS (mesma rede overlay, mesmo Swarm,
  possivelmente mesmo node de banco de dados).

### 5. Histórias de usuário

#### US-001 — Subir toda a stack de produção com um comando (P1)

Como Marcio, quero subir backend, frontend, worker, Postgres e Qdrant de
produção com um único `docker stack deploy`, para colocar o sistema no ar sem
um processo manual de várias etapas desconexas.

**Por que P1**: é o resultado central do item; sem isso não há Beta.
**Teste independente**: rodar `docker stack deploy -c deploy/stack.prod.yml rag-pipeline` num Swarm local de teste e observar os cinco serviços em `Running` via `docker service ls`.
**Requisitos**: FR-001, FR-002

#### US-002 — Proteger credenciais de produção (P1)

Como Marcio, quero que nenhuma credencial de produção apareça em texto puro
no stack file, para reduzir o risco de vazamento ao versionar ou compartilhar
o arquivo.

**Por que P1**: decisão explícita de segurança para esta entrega (BACKLOG-0030 depende deste item existir primeiro).
**Teste independente**: inspecionar `deploy/stack.prod.yml` e confirmar que cada valor sensível é uma referência `secrets:`, nunca um valor literal.
**Requisitos**: FR-003

#### US-003 — Coexistir com as outras aplicações da VPS sem conflito (P2)

Como Marcio, quero que os serviços de produção deste projeto sigam o mesmo
padrão de node e rede já usado pelas outras aplicações da VPS, para não
quebrar nem competir por recursos com o que já está em produção.

**Por que P2**: importante para estabilidade operacional, mas não bloqueia o primeiro deploy funcional (US-001) se ainda não estiver perfeitamente ajustado.
**Teste independente**: inspecionar `deploy/stack.prod.yml` e confirmar `placement.constraints` no node de banco de dados e a rede externa `network_swarm_public` declarada.
**Requisitos**: FR-004

### 6. Cenários BDD de aceite

#### AC-001 — Deploy inicial sobe todos os serviços com os volumes de produção

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-001
Feature: Subir o stack de produção

  Scenario: Deploy inicial sobe todos os serviços
    Given os volumes externos "postgres_data_ragpipeline" e "qdrant_data_ragpipeline" já criados no VPS
    When Marcio executa "docker stack deploy -c deploy/stack.prod.yml rag-pipeline"
    Then os serviços backend, frontend, worker, postgres e qdrant de produção alcançam o estado "Running"
```

#### AC-002 — Dados de produção persistem isolados dos recursos de teste

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-002
Feature: Subir o stack de produção

  Scenario: Isolamento entre volumes de produção e de teste
    Given o stack de produção e o docker-compose de teste ("rag-pipeline-test-postgres") rodando na mesma VPS
    When uma Base é criada através do backend de produção
    Then o registro aparece somente no volume "postgres_data_ragpipeline", nunca em "rag-pipeline-test-postgres"
```

#### AC-003 — Falha de build preserva os serviços já em execução

**Cobre**: US-001, FR-001, FR-002, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @AC-003
Feature: Subir o stack de produção

  Scenario: Build de uma nova imagem falha
    Given o stack de produção já rodando com uma versão anterior das imagens
    When Marcio tenta buildar uma nova imagem do backend e o build falha
    Then os serviços já em execução continuam "Running" com a imagem anterior, sem interrupção nem perda dos dados nos volumes
```

#### AC-004 — Serviço lê credencial sensível via docker secret

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-004
Feature: Proteger credenciais de produção

  Scenario: Backend lê a chave da OpenRouter por secret
    Given o secret "openrouter_api_key" criado no Swarm e referenciado pelo serviço backend
    When o serviço backend inicia
    Then ele lê a credencial do arquivo montado pelo secret, e o stack file não contém o valor em texto puro
```

#### AC-005 — Secret ausente impede o serviço de subir de forma visível

**Cobre**: US-002, FR-003, NFR-001

```gherkin
@US-002 @FR-003 @NFR-001 @AC-005
Feature: Proteger credenciais de produção

  Scenario: Secret referenciado não existe no Swarm
    Given o stack file referencia o secret "openrouter_api_key" mas ele não foi criado no Swarm
    When Marcio executa "docker stack deploy -c deploy/stack.prod.yml rag-pipeline"
    Then o serviço backend falha ao subir de forma visível ("docker service ps" mostra o erro), em vez de subir sem a credencial
```

#### AC-006 — Atualização de um secret não expõe seu valor

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-006
Feature: Proteger credenciais de produção

  Scenario: Rotação de uma credencial
    Given um novo valor para o secret "openrouter_api_key" criado com um novo nome de versão
    When o serviço backend é atualizado para referenciar a nova versão do secret
    Then o valor anterior e o novo nunca aparecem em texto puro no stack file nem em "docker service logs"
```

#### AC-007 — Serviços sobem nos nodes compatíveis com seus artefatos e dados

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-007
Feature: Coexistir com as demais aplicações da VPS

  Scenario: Placement dos serviços de aplicação e dados
    Given o node que buildou as imagens locais e o node dedicado a banco de dados
    When o stack de produção é implantado
    Then backend, frontend e worker sobem exclusivamente no node de build
    And postgres e qdrant de produção sobem exclusivamente no node de banco de dados
```

#### AC-008 — Stack conecta-se à rede compartilhada sem criar proxy próprio

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-008
Feature: Coexistir com as demais aplicações da VPS

  Scenario: Integração com a rede existente
    Given a rede overlay externa "network_swarm_public" já servida por um reverse proxy com HTTPS automático
    When o stack de produção é implantado
    Then o serviço frontend está conectado a essa rede, e nenhum reverse proxy próprio é criado por este stack
```

#### AC-009 — Constraint para node inexistente falha visivelmente sem afetar os demais serviços

**Cobre**: US-003, FR-004, NFR-001

```gherkin
@US-003 @FR-004 @NFR-001 @AC-009
Feature: Coexistir com as demais aplicações da VPS

  Scenario: Node de destino não existe ou está indisponível
    Given uma constraint de placement apontando para um node que não existe no cluster
    When o Swarm tenta agendar o serviço postgres de produção
    Then a tarefa fica visivelmente pendente de agendamento ("docker service ps" mostra "Pending"), sem derrubar os demais serviços do stack
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O stack de produção deve subir os serviços backend, frontend,
  worker, Postgres de produção e Qdrant de produção com um único comando
  `docker stack deploy`, todos alcançando o estado `Running`.
- **FR-002**: Postgres e Qdrant de produção devem persistir dados em volumes
  Docker nomeados e externos, distintos e isolados dos recursos de teste
  (`rag-pipeline-test-postgres`).
- **FR-003**: Toda credencial sensível usada pelos serviços (senha do
  Postgres, chave OpenRouter, credenciais Cloudflare R2, segredo de sessão)
  deve ser lida via `docker secret`, nunca declarada em texto puro no stack
  file.
- **FR-004**: Postgres e Qdrant de produção devem ser fixados por
  `deploy.placement.constraints` no node dedicado a banco de dados; backend,
  frontend e worker devem ser fixados no node que executou o build local,
  evitando agendamento num node sem as imagens enquanto não há registry; o
  stack deve conectar-se à rede overlay externa `network_swarm_public` já
  existente, sem criar reverse proxy próprio.

#### Não funcionais

- **NFR-001**: O deploy deve ser resiliente a falhas parciais — build
  malsucedido não deve derrubar serviços já em execução, secret ausente não
  deve permitir subida silenciosa sem a credencial, e uma constraint de
  placement não satisfeita não deve afetar os demais serviços do stack.
  **Verificação**: teste estrutural do stack file (`tests/test_deploy_stack.py`) mais verificação manual em Swarm de teste.

#### Erros e casos-limite

- Build de imagem falha → serviços já em execução permanecem `Running` com a
  imagem anterior (AC-003).
- Secret referenciado ausente no Swarm → serviço correspondente falha ao
  subir de forma visível (AC-005).
- Node de destino da constraint de placement inexistente ou indisponível →
  tarefa fica `Pending` de agendamento, sem afetar os demais serviços
  (AC-009).

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend: Python 3.12+ gerenciado por `uv`, FastAPI (`src/app/main.py`),
  SQLAlchemy 2 + psycopg 3 sobre PostgreSQL, migrations por Alembic, fila
  assíncrona Procrastinate sobre o mesmo Postgres. O worker roda o mesmo
  código-base (`uv run python -m src.app.worker`, que importa
  `src.app.main`), sem Dockerfile nem entrypoint distintos hoje.
- Frontend: Next.js 16.3.4 (`frontend/`), Node 24 em CI, projeto Node
  autocontido (`package.json`/`tsconfig.json`/`components.json` próprios).
  `next.config.ts` já reencaminha `/api/*` para `API_PROXY_TARGET` (hoje
  `http://127.0.0.1:8000`, correto só em desenvolvimento) e não usa
  `output: "standalone"` ainda.
- Só existe hoje `docker-compose.yml` na raiz, exclusivamente para o Postgres
  de teste (`rag-pipeline-test-postgres`, porta 55432) — não é reaproveitado
  para produção; um stack file de produção separado é necessário.
- CI (`(.github/workflows/ci.yml)`) roda lint/test/build em push e PR, sem
  nenhum passo de deploy.
- VPS de destino: Docker Swarm já instalado, multi-node, já com outras
  aplicações em produção. Rede overlay externa `network_swarm_public` já
  existente, com reverse proxy (Traefik ou similar) provendo HTTPS automático
  por labels. Convenções já em uso (evidenciadas por um stack file real
  compartilhado por Marcio): nome de serviço `<tecnologia>_<app>`, volumes
  Docker nomeados com `external: true` (criados manualmente antes do stack),
  `deploy.placement.constraints` por `node.hostname` para fixar serviços de
  banco de dados num node dedicado, limites de `cpus`/`memory` por serviço.

#### Arquitetura e módulos

- `deploy/backend/Dockerfile`: imagem Python 3.12-slim com `uv`, instala
  dependências de `pyproject.toml`/`uv.lock` (`uv sync --frozen --no-dev`),
  copia `src/`, `alembic/` e `alembic.ini`. Reaproveitada por dois serviços
  do stack (backend e worker), cada um com `command:` próprio — decisão
  `DEC-001`.
- `deploy/frontend/Dockerfile`: build multi-stage Node 24 — estágio de
  dependências (`npm ci`), estágio de build (`npm run build`, já com
  `output: "standalone"` em `next.config.ts`), estágio de execução rodando o
  servidor standalone gerado pelo Next. Como o Next.js 16 serializa os
  rewrites no build standalone, o estágio de build recebe
  `API_PROXY_TARGET` por `ARG` não sensível e o aplica somente ao comando de
  build. `deploy/build_and_deploy.sh` resolve o valor uma vez (default
  `http://backend_ragpipeline:8000`), passa-o ao build e o stack publica o
  mesmo valor no ambiente do serviço para manter o contrato operacional
  explícito — decisão `DEC-002`.
- `deploy/stack.prod.yml`: stack file Compose 3.7 para `docker stack deploy`,
  com cinco serviços (`backend_ragpipeline`, `frontend_ragpipeline`,
  `worker_ragpipeline`, `postgres_ragpipeline`, `qdrant_ragpipeline`),
  seguindo a convenção de nome `<tecnologia>_<app>` já usada na VPS —
  decisão `DEC-003`. `postgres_ragpipeline` e `qdrant_ragpipeline` recebem
  `deploy.placement.constraints` para o node de banco de dados; todos os
  cinco serviços conectam-se à rede externa `network_swarm_public`; volumes
  `postgres_data_ragpipeline` e `qdrant_data_ragpipeline` como `external:
  true`; secrets (`openrouter_api_key`, `r2_credentials`, `session_secret`,
  `postgres_password`) referenciados via bloco `secrets:` de cada serviço que
  precisa deles (criação do conteúdo real é escopo do `BACKLOG-0030`).
- `deploy/build_and_deploy.sh`: script que builda as duas imagens
  (`deploy/backend/Dockerfile`, `deploy/frontend/Dockerfile`) e só executa
  `docker stack deploy` se ambos os builds tiverem sucesso (`set -euo
  pipefail`), tornando FR-001/NFR-001 (falha de build não derruba serviço em
  execução) verificável de forma automatizada, sem depender do VPS real. O
  script também passa `API_PROXY_TARGET` como build arg do frontend porque o
  rewrite do standalone é fixado durante `next build` — decisão `DEC-005`.

#### Migrations

- Não aplicável. Esta entrega não altera schema; Alembic continua a mesma
  fonte de migrations, aplicada manualmente contra o Postgres de produção
  (fora do escopo desta spec, que só entrega a definição do container e do
  stack).

#### Models

- Não aplicável — nenhum model novo ou alterado.

#### Controllers e casos de uso

- Não aplicável — nenhum endpoint novo ou alterado; o backend em produção
  expõe exatamente os mesmos routers já existentes em `src/app/routers/`.

#### Views e experiência

- Não aplicável — ver seção 10 (Interface para pessoas: Não).

#### Queries e repositórios

- Não aplicável — nenhuma mudança em `src/app/repo.py` ou equivalentes.

#### Jobs e processamento assíncrono

- O worker Procrastinate (`src.app.worker`) passa a rodar como serviço
  próprio do stack de produção (`worker_ragpipeline`), na mesma imagem do
  backend, apontando para o mesmo Postgres de produção. Sem mudança de
  comportamento do worker em si, apenas o ambiente de execução.

#### Estrutura de arquivos

```text
specs/defined/0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm/
  spec.md
deploy/
  backend/
    Dockerfile
  frontend/
    Dockerfile
  stack.prod.yml
  build_and_deploy.sh
frontend/
  next.config.ts        (ajuste: output "standalone")
tests/
  test_deploy_stack.py
```

### 9. Modelo de dados

#### Entidades

- Não aplicável — nenhuma entidade de domínio nova ou alterada; o schema do
  Postgres de produção é idêntico ao já existente, só passa a rodar num
  container de produção em vez de local/teste.

#### Estados e transições

- Não aplicável.

#### Migração e retenção

- Não aplicável a esta spec (backup e retenção do Postgres de produção são
  escopo do `BACKLOG-0031`).

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. Esta entrega é infraestrutura de
  deploy (Dockerfiles e stack Swarm); não cria, altera nem remove nenhuma
  tela, fluxo, formulário ou interação de pessoa usuária com o sistema. O
  ajuste em `next.config.ts` (`output: "standalone"`, `API_PROXY_TARGET`) é
  puramente operacional e não muda nenhuma experiência visível.

#### APIs expostas

- Não aplicável — nenhum endpoint novo; os mesmos routers HTTP já existentes
  passam a rodar em produção sem alteração de contrato.

#### APIs externas utilizadas

- Nenhuma nova. As mesmas integrações já existentes (OpenRouter, Cloudflare
  R2, Qdrant) continuam sendo usadas, agora com credenciais de produção via
  `docker secret` em vez de `.env` local.

#### Documentação das APIs consultadas

- Não aplicável.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: estrutura do stack file (`deploy/stack.prod.yml`) validada
  por parsing YAML — presença dos cinco serviços, `external: true` nos
  volumes de dados, `deploy.placement.constraints` em `postgres_ragpipeline`
  e `qdrant_ragpipeline`, rede externa `network_swarm_public` declarada, e
  nenhum valor sensível em texto puro (toda credencial via bloco `secrets:`).
- **Integração/contrato**: `docker build` real dos dois Dockerfiles
  (backend e frontend) contra o código atual, executável neste ambiente de
  desenvolvimento (Docker disponível), sem depender do VPS de produção. No
  frontend, a inspeção de `.next/routes-manifest.json` precisa provar
  que o rewrite foi serializado para `http://backend_ragpipeline:8000`, não
  para o fallback local.
- **BDD/aceite**: cenários da seção 6 (AC-001 a AC-009) orientam os casos
  TDD abaixo.
- **Runner TDD**: Pytest (já usado pelo restante do projeto Python; não há
  Laravel nem decisão de runner Node pendente para esta spec, que não altera
  `frontend/`de forma testável por Vitest além do build).
- **E2E**: subida real do stack completo (`docker stack deploy`) validada
  num Swarm local de single-node neste ambiente de desenvolvimento
  (`docker swarm init` local), como prova estrutural — os aspectos exclusivos
  da VPS real (node de banco de dados específico, rede `network_swarm_public`
  real, Traefik real) exigem **verificação manual** no VPS de produção, feita
  por Marcio, por não haver acesso a essa infraestrutura neste ambiente.
- **Verificação manual**: deploy real no VPS de produção (placement no node
  de banco de dados real, integração com a rede/Traefik reais) — inevitável,
  pois esta sessão não tem acesso às credenciais nem ao Swarm de produção de
  Marcio.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, AC-001 | AC-001 na seção 6 | `tests/test_deploy_stack.py::test_stack_declara_os_cinco_servicos_esperados` | `FileNotFoundError: deploy/stack.prod.yml` (2026-09-28) | Passed — T017, 2026-10-03 | Passed — regressão integral 419 casos |
| US-001, FR-001, FR-002, AC-002 | AC-002 na seção 6 | `tests/test_deploy_stack.py::test_volumes_de_producao_sao_externos_e_distintos_dos_de_teste` | `FileNotFoundError: deploy/stack.prod.yml` (2026-09-28) | Passed — T017, 2026-10-03 | Passed — regressão integral 419 casos |
| US-001, FR-001, FR-002, NFR-001, AC-003 | AC-003 na seção 6 | `tests/test_deploy_build_and_deploy_script.py::test_build_falho_impede_execucao_do_deploy` | `FileNotFoundError: deploy/build_and_deploy.sh` (2026-09-28) | Passed — T017, 2026-10-03 | Passed — regressão integral 419 casos |
| US-002, FR-003, AC-004 | AC-004 na seção 6 | `tests/test_deploy_stack.py::test_credenciais_sensiveis_sao_referencias_a_secrets` | `FileNotFoundError: deploy/stack.prod.yml` (2026-09-28) | Passed — T017, 2026-10-03 | Passed — regressão integral 419 casos |
| US-002, FR-003, NFR-001, AC-005 | AC-005 na seção 6 | `tests/test_deploy_stack.py::test_cada_secret_referenciado_esta_declarado_no_stack` | `FileNotFoundError: deploy/stack.prod.yml` (2026-09-28) | Passed — T017, 2026-10-03 | Passed — regressão integral 419 casos |
| US-002, FR-003, AC-006 | AC-006 na seção 6 | `tests/test_deploy_stack.py::test_nenhum_valor_de_secret_aparece_em_texto_puro` | `FileNotFoundError: deploy/stack.prod.yml` (2026-09-28) | Passed — T017, 2026-10-03 | Passed — regressão integral 419 casos |
| US-003, FR-004, AC-007 | AC-007 na seção 6 | `tests/test_deploy_stack.py::test_servicos_tem_placement_compativel_com_imagens_locais` | `FileNotFoundError: deploy/stack.prod.yml` (2026-09-28) | Passed — T017, 2026-10-03 | Passed — regressão integral 419 casos |
| US-003, FR-004, AC-008 | AC-008 na seção 6 | `tests/test_deploy_stack.py::test_stack_conecta_rede_externa_network_swarm_public` | `FileNotFoundError: deploy/stack.prod.yml` (2026-09-28) | Passed — T017, 2026-10-03 | Passed — regressão integral 419 casos |
| US-003, FR-004, NFR-001, AC-009 | AC-009 na seção 6 | `tests/test_deploy_stack.py::test_constraints_de_placement_sao_bem_formadas_e_escopadas_por_servico` | `FileNotFoundError: deploy/stack.prod.yml` (2026-09-28) | Passed — T017, 2026-10-03 | Passed — regressão integral 419 casos |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade + Integração | `tests/test_deploy_stack.py`; `docker build -f deploy/backend/Dockerfile .`; `docker build -f deploy/frontend/Dockerfile frontend/` | Passed — T017, 2026-10-03; research/t017-swarm-local.json |
| FR-001 | AC-002 | Unidade | `tests/test_deploy_stack.py` | Passed — T017, 2026-10-03; research/t017-swarm-local.json |
| FR-001 | AC-003 | Unidade | `tests/test_deploy_build_and_deploy_script.py` | Passed — T017, 2026-10-03; research/t017-swarm-local.json |
| FR-002 | AC-001 | Unidade | `tests/test_deploy_stack.py` | Passed — T017, 2026-10-03; research/t017-swarm-local.json |
| FR-002 | AC-002 | Unidade | `tests/test_deploy_stack.py` | Passed — T017, 2026-10-03; research/t017-swarm-local.json |
| FR-003 | AC-004 | Unidade | `tests/test_deploy_stack.py` | Passed — T017, 2026-10-03; research/t017-swarm-local.json |
| FR-003 | AC-005 | Unidade | `tests/test_deploy_stack.py` | Passed — T017, 2026-10-03; research/t017-swarm-local.json |
| FR-003 | AC-006 | Unidade | `tests/test_deploy_stack.py` | Passed — T017, 2026-10-03; research/t017-swarm-local.json |
| FR-004 | AC-007 | Unidade | `tests/test_deploy_stack.py` | Passed — T017, 2026-10-03; research/t017-swarm-local.json |
| FR-004 | AC-008 | Unidade | `tests/test_deploy_stack.py` | Passed — T017, 2026-10-03; research/t017-swarm-local.json |
| NFR-001 | AC-003, AC-005, AC-009 | Unidade + Verificação manual | `tests/test_deploy_stack.py`; Swarm local de teste | Passed — T017, 2026-10-03; research/t017-swarm-local.json |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (revalidado em 2026-10-01)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm/spec.md --allow-draft` → `VALID DRAFT`.
- **Achados**:

- **FIND-PROD-001** [P2] [Resolved] Definition of Done não citava a atualização de `.specsfy/STACK.md` mesmo introduzindo Docker Swarm como tecnologia de deploy de produção — Refs: FR-001 — Evidence: .specsfy/STACK.md — Effect: STACK.md poderia ficar desatualizado mesmo com a spec Complete — Suggestion: adicionar item de DoD exigindo o registro em STACK.md, aplicado nesta revisão.

Nenhum achado `P1` pendente. Revisão `SEC` (segredos, isolamento, rotação) e
`ARCH` (princípios da seção 4 refletidos nas seções 8–10) sem achado
bloqueante — profundidade proporcional ao risco: uso interno, sem superfície
externa nova, sem dado sensível de terceiros.
- **FIND-ARCH-002** [P1] [Resolved] Imagens locais não são distribuídas entre nodes sem registry — Refs: FR-001, FR-004, AC-007 — Evidence: deploy/stack.prod.yml — Effect: agendamento poderia escolher node sem imagem — Suggestion: fixar serviços de aplicação no node de build, conforme DEC-006, T007 e T015; confirmado pela pessoa em 2026-10-01.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: READY (revalidado em 2026-10-01)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0022-dockerizar-aplicacao-e-stack-de-producao-docker-swarm/spec.md` → `READY` (17 tarefas, 10 concluídas; predecessores TDD T001–T009 preservados com RED observado).
- **Achados**: Nenhum bloqueante. T011 e T013 foram reconciliadas para passar `API_PROXY_TARGET` também ao build standalone, pois Next.js 16 serializa rewrites durante `next build`; requisitos, ACs, dependências e tarefas TDD permanecem válidos.
- **Revalidação de 2026-10-01**: T007 e T015 foram reconciliadas com a
  constraint do node de build confirmada em DEC-006; o novo RED foi observado
  e a validação de tarefas permaneceu `READY` sem alterar a contagem de 17
  tarefas.

#### Gate do Ato III — Entrega

- **Resultado**: Passed — execução integral e verificação global aprovadas em 2026-10-03; 419 testes Python sem skips, 135 testes frontend, nove cenários de aceite e 17/17 tarefas comprovados.
- **Comprovação do banco**: `check_database_safety.mjs` aprovado antes de cada execução; `uv run python -m tests._database_safety` → SAFE. `.env.testing` local declara `APP_ENV=testing` e destino PostgreSQL explícito distinto do `.env` ou do fallback de desenvolvimento. Driver, senha e aliases locais não mascaram a identidade do banco; herança divergente é recusada antes de importar a aplicação. Seis testes focais de segurança passaram. Valores de conexão não foram registrados.
- **Correções e evidências**: URLs codificadas do Alembic falhavam por interpolação de `%` (RED real no teste de upgrade); escape `%%` em `alembic/env.py` levou a GREEN. A imagem não-root falhava ao criar `output/uploads` (RED: `docker run --rm --entrypoint /bin/sh rag-pipeline-backend:local -c 'test -w /app/output/uploads'` → exit 1); criação e ownership do diretório levaram ao mesmo comando com exit 0 e ao backend/worker estáveis no Swarm. O teste de build falho também detectou a ausência do bit executável do script, corrigida e registrada no índice Git.
- **Checks já aprovados**: Pytest focal (19 passed); regressão integral com `RUN_SPEC0014_REAL=1 uv run pytest -q` (419 passed, zero skips, 147,76 s; dois avisos de depreciação sem falha); Ruff; lint, typecheck e Vitest do frontend (31 arquivos, 135 testes); build standalone limpo com rewrite para `http://backend_ragpipeline:8000`; builds reais das duas imagens; `deploy/build_and_deploy.sh` no Swarm local; documentação reconstruída e monitor CURRENT. As dependências nativas ARM locais foram reparadas sem alterar manifests ou lockfiles, e o cache de build com falha foi preservado em `/tmp`.
- **Aceite local**: nove ACs aprovados em `research/t017-swarm-local.json`, com hashes dos quatro artefatos de deploy. Cinco serviços 1/1; login, troca de senha, criação de Workspace e upload pelo proxy do frontend; Base com uma linha somente no PostgreSQL do Swarm e zero no banco de testes; build Docker realmente falho preserva os serviços; secret externo ausente recusa deploy; node inexistente mantém apenas o probe Pending; rotação sintética preserva o nome montado, sem valor em stack/logs. Responsável: Codex nesta sessão; ambiente: single-node local, secrets sintéticos, sem operação no VPS de produção. O backend do ensaio materializou o schema ORM; a fila foi preparada por avanço, e o upgrade Alembic foi comprovado separadamente nos schemas de regressão.
- **Revisão visual**: Não aplicável — alterações em infraestrutura, migrations/configuração de testes e documentação, sem mudança de interface para pessoas.
- **Avaliação de contexto**: nenhuma mudança material de capacidades, história ou finalidade em `PROJECT.md`; stack, persistência de testes, README e documentação foram atualizados para refletir o isolamento. Nenhuma regra de produto nova; monitor CURRENT.
- **Achados resolvidos**:
- **FIND-SEC-003** [P1] [Resolved] A suíte podia herdar banco de desenvolvimento sem validação — Refs: FR-002, AC-002 — Evidence: tests/_database_safety.py — Effect: risco de executar a regressão sobre destino incorreto — Suggestion: configuração explícita em .env.testing, comparação normalizada e recusa de herança divergente, aplicadas antes da importação do backend e cobertas por tests/test_database_safety.py.
- **FIND-SEC-004** [P1] [Resolved] A regressão executava downgrades e limpeza global — Refs: FR-002, NFR-001, AC-002 — Evidence: tests/test_app_migrations.py — Effect: remoção indevida de estruturas ou registros — Suggestion: avanços em schemas novos, inspeção AST do contrato de reversão, rollback transacional e fila por schema, implementados em tests/conftest.py e tests/test_app_worker.py; nenhum downgrade SQL ou limpeza global executado.
- **Limites de DEC-004**: node dedicado, rede/Traefik e secrets reais permanecem validação operacional no VPS por Marcio. Esta entrega comprova artefatos e Swarm local, sem implantar produção.

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

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pytest falhando em tests/test_deploy_stack.py — Refs: US-001, FR-001, FR-002, AC-001 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-001 na seção 6; confirmado que `deploy/stack.prod.yml` ainda não existe.
  - [x] **EXECUTE**: Escrito `test_stack_declara_os_cinco_servicos_esperados` em `tests/test_deploy_stack.py`, com marcador `SPECSFY: SPEC-0022 US-001 FR-001 FR-002 AC-001`, carregando `deploy/stack.prod.yml` via `yaml.safe_load` e checando as chaves `backend_ragpipeline`, `frontend_ragpipeline`, `worker_ragpipeline`, `postgres_ragpipeline`, `qdrant_ragpipeline` em `services`.
  - [x] **VERIFY**: RED válido observado — `FileNotFoundError: deploy/stack.prod.yml` (arquivo ainda não criado).
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste de infraestrutura, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_deploy_stack.py::test_stack_declara_os_cinco_servicos_esperados -v` → 1 failed (`FileNotFoundError`), 2026-09-28.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária nesta tarefa de teste único.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pytest falhando em tests/test_deploy_stack.py — Refs: US-001, FR-001, FR-002, AC-002 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-002 na seção 6.
  - [x] **EXECUTE**: Escrito `test_volumes_de_producao_sao_externos_e_distintos_dos_de_teste`, com marcador `SPECSFY: SPEC-0022 US-001 FR-001 FR-002 AC-002`, checando que `postgres_data_ragpipeline` e `qdrant_data_ragpipeline` existem em `volumes`, cada um com `external: true`, e que nenhum nome coincide com `rag-pipeline-test-postgres`.
  - [x] **VERIFY**: RED válido — `FileNotFoundError: deploy/stack.prod.yml`.
  - [x] **VISUAL**: Não aplicável — mesma justificativa de T001.
  - [x] **EVIDENCE**: `uv run pytest tests/test_deploy_stack.py -q` → falha por `FileNotFoundError`, 2026-09-28.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pytest falhando em tests/test_deploy_build_and_deploy_script.py — Refs: US-001, FR-001, FR-002, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-003 na seção 6; confirmado que `deploy/build_and_deploy.sh` ainda não existe.
  - [x] **EXECUTE**: Escrito `test_build_falho_impede_execucao_do_deploy` em `tests/test_deploy_build_and_deploy_script.py`, com marcador `SPECSFY: SPEC-0022 US-001 FR-001 FR-002 NFR-001 AC-003`, usando um `docker` falso no `PATH` que loga cada subcomando e falha em `build`, verificando que `stack deploy` nunca é chamado e o script sai com código diferente de zero.
  - [x] **VERIFY**: RED válido — `FileNotFoundError: deploy/build_and_deploy.sh` (script ainda não existe).
  - [x] **VISUAL**: Não aplicável — mesma justificativa de T001.
  - [x] **EVIDENCE**: `uv run pytest tests/test_deploy_build_and_deploy_script.py -q` → falha por `FileNotFoundError`, 2026-09-28.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

- [x] T004 [TEST] [TDD] [US-002] Derivar do AC-004 um caso Pytest falhando em tests/test_deploy_stack.py — Refs: US-002, FR-003, AC-004 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-004 na seção 6.
  - [x] **EXECUTE**: Escrito `test_credenciais_sensiveis_sao_referencias_a_secrets`, com marcador `SPECSFY: SPEC-0022 US-002 FR-003 AC-004`, checando que os serviços `backend_ragpipeline`/`worker_ragpipeline` referenciam `openrouter_api_key`, `r2_credentials`, `session_secret` e `postgres_password` via `secrets:`, e que nenhuma variável de ambiente do serviço contém esses valores diretamente.
  - [x] **VERIFY**: RED válido — `FileNotFoundError: deploy/stack.prod.yml`.
  - [x] **VISUAL**: Não aplicável — mesma justificativa de T001.
  - [x] **EVIDENCE**: `uv run pytest tests/test_deploy_stack.py -q` → falha por `FileNotFoundError`, 2026-09-28.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-005 um caso Pytest falhando em tests/test_deploy_stack.py — Refs: US-002, FR-003, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-005 na seção 6.
  - [x] **EXECUTE**: Escrito `test_cada_secret_referenciado_esta_declarado_no_stack`, com marcador `SPECSFY: SPEC-0022 US-002 FR-003 NFR-001 AC-005`, checando que cada nome citado em algum `secrets:` de serviço tem uma entrada correspondente no bloco `secrets:` de nível superior, com `external: true`.
  - [x] **VERIFY**: RED válido — `FileNotFoundError: deploy/stack.prod.yml`.
  - [x] **VISUAL**: Não aplicável — mesma justificativa de T001.
  - [x] **EVIDENCE**: `uv run pytest tests/test_deploy_stack.py -q` → falha por `FileNotFoundError`, 2026-09-28.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 um caso Pytest falhando em tests/test_deploy_stack.py — Refs: US-002, FR-003, AC-006 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-006 na seção 6.
  - [x] **EXECUTE**: Escrito `test_nenhum_valor_de_secret_aparece_em_texto_puro`, com marcador `SPECSFY: SPEC-0022 US-002 FR-003 AC-006`, checando que nenhuma entrada do bloco `secrets:` de nível superior tem chave `file:`/valor inline — todas usam `external: true`.
  - [x] **VERIFY**: RED válido — `FileNotFoundError: deploy/stack.prod.yml`.
  - [x] **VISUAL**: Não aplicável — mesma justificativa de T001.
  - [x] **EVIDENCE**: `uv run pytest tests/test_deploy_stack.py -q` → falha por `FileNotFoundError`, 2026-09-28.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

- [x] T007 [TEST] [TDD] [US-003] Derivar do AC-007 um caso Pytest falhando em tests/test_deploy_stack.py — Refs: US-003, FR-004, AC-007 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-007 na seção 6.
  - [x] **EXECUTE**: Revisado em 2026-10-01 como `test_servicos_tem_placement_compativel_com_imagens_locais`, com marcador `SPECSFY: SPEC-0022 US-003 FR-004 AC-007`, checando `APPLICATION_NODE_HOSTNAME` em backend/frontend/worker e `DATABASE_NODE_HOSTNAME` em Postgres/Qdrant.
  - [x] **VERIFY**: RED válido — `FileNotFoundError: deploy/stack.prod.yml`.
  - [x] **VISUAL**: Não aplicável — mesma justificativa de T001.
  - [x] **EVIDENCE**: RED original preservado (`FileNotFoundError`, 2026-09-28); teste revisado após a decisão de 2026-10-01 e RED reconfirmado antes de T015.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

- [x] T008 [TEST] [TDD] [US-003] Derivar do AC-008 um caso Pytest falhando em tests/test_deploy_stack.py — Refs: US-003, FR-004, AC-008 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-008 na seção 6.
  - [x] **EXECUTE**: Escrito `test_stack_conecta_rede_externa_network_swarm_public`, com marcador `SPECSFY: SPEC-0022 US-003 FR-004 AC-008`, checando que `networks.network_swarm_public.external` é `true`, que todos os cinco serviços listam essa rede, e que nenhum serviço de reverse proxy é declarado neste stack.
  - [x] **VERIFY**: RED válido — `FileNotFoundError: deploy/stack.prod.yml`.
  - [x] **VISUAL**: Não aplicável — mesma justificativa de T001.
  - [x] **EVIDENCE**: `uv run pytest tests/test_deploy_stack.py -q` → falha por `FileNotFoundError`, 2026-09-28.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-009 um caso Pytest falhando em tests/test_deploy_stack.py — Refs: US-003, FR-004, NFR-001, AC-009 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-009 na seção 6.
  - [x] **EXECUTE**: Escrito `test_constraints_de_placement_sao_bem_formadas_e_escopadas_por_servico`, com marcador `SPECSFY: SPEC-0022 US-003 FR-004 NFR-001 AC-009`, checando que cada `deploy.placement.constraints` é uma lista de strings não vazia e válida, aninhada exclusivamente sob o `deploy:` do próprio serviço, nunca em nível de stack.
  - [x] **VERIFY**: RED válido — `FileNotFoundError: deploy/stack.prod.yml`.
  - [x] **VISUAL**: Não aplicável — mesma justificativa de T001.
  - [x] **EVIDENCE**: `uv run pytest tests/test_deploy_stack.py -q` → falha por `FileNotFoundError`, 2026-09-28.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.

#### Fase 2 — US-001 Subir toda a stack de produção com um comando (P1)

**Objetivo**: backend, frontend, worker, Postgres e Qdrant de produção sobem com `docker stack deploy`, com dados isolados dos recursos de teste, sem que uma falha de build derrube o que já está `Running`.
**Teste independente**: `docker swarm init` local, `deploy/build_and_deploy.sh`, `docker service ls` mostrando os cinco serviços `Running`.

- [x] T010 [CODE] [US-001] Criar deploy/backend/Dockerfile (Python 3.12-slim + uv, reaproveitado pelo worker) — Refs: US-001, FR-001, FR-002, AC-001, AC-002, AC-003 — Depends: T001, T002, T003
  - [x] **PREP**: RED reconfirmado em T001/T002/T003 (`3 failed`: `deploy/stack.prod.yml` e `deploy/build_and_deploy.sh` ausentes); `$specsfy-documentator` executado e `build_documentation.mjs --check` aprovado antes de `EXECUTE` (2026-10-01).
  - [x] **EXECUTE**: Criado `deploy/backend/Dockerfile` sobre `python:3.12-slim`, com uv 0.12.15, `uv sync --frozen --no-dev --no-install-project`, cópia de `src/`, `alembic/` e `alembic.ini`, execução não-root e sem `CMD` fixo; `.dockerignore` protege credenciais e artefatos locais do contexto de build.
  - [x] **VERIFY**: `docker build -f deploy/backend/Dockerfile -t rag-pipeline-backend:local .` concluiu com exit 0; inspeção confirmou `User=app`, `Cmd=null` e porta `8000/tcp` (2026-10-01).
  - [x] **VISUAL**: Não aplicável — Dockerfile não tem superfície visual.
  - [x] **EVIDENCE**: Imagem `rag-pipeline-backend:local` construída; T001/T002/T003 permanecem RED de forma esperada até `stack.prod.yml` e `build_and_deploy.sh` nascerem em T012/T013. Arquivos: `deploy/backend/Dockerfile`, `.dockerignore`, `.specsfy/STACK.md` e documentação reconstruída em `docs/`.
  - [x] **IMPROVE**: Adicionado `.dockerignore` para excluir segredos/configuração local e artefatos do contexto; removido `chown -R` da virtualenv e limpo o `CMD` herdado da imagem base, mantendo filesystem root-owned e processo não-root.
  <!-- specsfy:evidence {"task":"T010","refs":["US-001","FR-001","FR-002","AC-001","AC-002","AC-003"],"files":["deploy/backend/Dockerfile",".dockerignore",".specsfy/STACK.md","docs/architecture.md"],"commands":[{"run":"docker build -f deploy/backend/Dockerfile -t rag-pipeline-backend:local .","exit":0},{"run":"docker image inspect rag-pipeline-backend:local --format '{{json .Config.User}} {{json .Config.Cmd}} {{json .Config.ExposedPorts}}'","exit":0},{"run":"node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project /media/marcio/AKT/Projects/rag-pipeline --check","exit":0}]} -->

- [x] T011 [CODE] [US-001] Criar deploy/frontend/Dockerfile e ajustar frontend/next.config.ts (output standalone, API_PROXY_TARGET) — Refs: US-001, FR-001, FR-002, AC-001, AC-002, AC-003 — Depends: T001, T002, T003
  - [x] **PREP**: RED reconfirmado em T001/T002/T003 (`3 failed` pelos artefatos ainda ausentes); documentação reconstruída e `build_documentation.mjs --check` aprovado antes de `EXECUTE` (2026-10-01). Confirmados Next.js 16.3.4, App Router, runtime Node 24 e orientação local de `output: "standalone"`.
  - [x] **EXECUTE**: Mantido `output: "standalone"` em `frontend/next.config.ts`; criado `deploy/frontend/Dockerfile` multi-stage em Node 24 (dependências → build → runtime standalone), com assets públicos/estáticos, usuário `node` e comando `node server.js`; `API_PROXY_TARGET` é obrigatório como build arg não sensível e aplicado somente a `npm run build`; criado `frontend/.dockerignore`. T012 publicará o mesmo valor no serviço `frontend_ragpipeline`.
  - [x] **VERIFY**: Typecheck e `npm --prefix frontend run build -- --webpack` concluíram com exit 0; build Docker com `API_PROXY_TARGET=http://backend_ragpipeline:8000` concluiu com exit 0; inspeção dentro da imagem confirmou esse destino em `/app/server.js`, `User=node`, `Cmd=["node","server.js"]` e porta `3000/tcp` (2026-10-01). O build Turbopack no host falhou por restrição de bind do ambiente, mas passou dentro do Docker.
  - [x] **VISUAL**: Não aplicável — ajuste de build/infraestrutura, sem mudança de tela, DOM, estilo ou componente.
  - [x] **EVIDENCE**: Arquivos: `frontend/next.config.ts`, `frontend/.dockerignore`, `deploy/frontend/Dockerfile` e documentação reconstruída em `docs/`.
  - [x] **IMPROVE**: O build arg tornou-se obrigatório e fail-closed, impedindo que uma imagem de produção seja criada silenciosamente com o fallback local; o contexto do frontend exclui `.env*`, `.next` e `node_modules`.
  <!-- specsfy:evidence {"task":"T011","refs":["US-001","FR-001","FR-002","AC-001","AC-002","AC-003"],"files":["frontend/next.config.ts","frontend/.dockerignore","deploy/frontend/Dockerfile","docs/frontend.md"],"commands":[{"run":"npm --prefix frontend run typecheck","exit":0},{"run":"npm --prefix frontend run build -- --webpack","exit":0},{"run":"docker build --build-arg API_PROXY_TARGET=http://backend_ragpipeline:8000 -f deploy/frontend/Dockerfile -t rag-pipeline-frontend:local frontend/","exit":0},{"run":"docker run --rm --entrypoint node rag-pipeline-frontend:local -e \"const fs=require('fs');const s=fs.readFileSync('/app/server.js','utf8');const target='http://backend_ragpipeline:8000/api/:path*';if(!s.includes(target))process.exit(1);console.log(target)\"","exit":0},{"run":"node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project /media/marcio/AKT/Projects/rag-pipeline --check","exit":0}]} -->

- [x] T012 [CODE] [US-001] Criar deploy/stack.prod.yml com os cinco serviços e volumes externos nomeados — Refs: US-001, FR-001, FR-002, AC-001, AC-002 — Depends: T001, T002, T010, T011
  - [x] **PREP**: Confirmado RED de T001/T002 por ausência de `deploy/stack.prod.yml` (o plano dizia GREEN, impossível antes da execução desta tarefa); `$specsfy-documentator` executado e `--check` aprovado antes de `EXECUTE` (2026-10-01).
  - [x] **EXECUTE**: Criado `deploy/stack.prod.yml` (Compose 3.7) com `backend_ragpipeline`, `frontend_ragpipeline`, `worker_ragpipeline` (mesma imagem do backend, comando `uv run python -m src.app.worker`), `postgres_ragpipeline` 16 e `qdrant_ragpipeline` 1.10.1; volumes `postgres_data_ragpipeline` e `qdrant_data_ragpipeline` declarados como externos.
  - [x] **VERIFY**: Testes focais T001/T002 com `2 passed`; `docker stack config -c deploy/stack.prod.yml` aceitou e normalizou a definição (2026-10-01).
  - [x] **VISUAL**: Não aplicável — arquivo de infraestrutura sem superfície visual.
  - [x] **EVIDENCE**: GREEN de AC-001/AC-002 e arquivo `deploy/stack.prod.yml`; documentação reconstruída e verificada.
  - [x] **IMPROVE**: Variáveis não sensíveis receberam defaults explícitos e o ambiente compartilhado entre backend/worker usa anchor YAML, reduzindo divergência operacional sem duplicar segredo.
  <!-- specsfy:evidence {"task":"T012","refs":["US-001","FR-001","FR-002","AC-001","AC-002"],"files":["deploy/stack.prod.yml","docs/architecture.md"],"commands":[{"run":"uv run pytest tests/test_deploy_stack.py::test_stack_declara_os_cinco_servicos_esperados tests/test_deploy_stack.py::test_volumes_de_producao_sao_externos_e_distintos_dos_de_teste -q","exit":0},{"run":"docker stack config -c deploy/stack.prod.yml","exit":0},{"run":"node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project /media/marcio/AKT/Projects/rag-pipeline --check","exit":0}]} -->

- [x] T013 [CODE] [US-001] Criar deploy/build_and_deploy.sh — Refs: US-001, FR-001, NFR-001, AC-003 — Depends: T003, T010, T011, T012
  - [x] **PREP**: RED de T003 confirmado por ausência de `deploy/build_and_deploy.sh`; `$specsfy-documentator` executado e `--check` aprovado antes de `EXECUTE` (2026-10-01).
  - [x] **EXECUTE**: Criado `deploy/build_and_deploy.sh` executável com `set -euo pipefail`: resolve `API_PROXY_TARGET`, builda backend e frontend (passando o build arg), exige `DATABASE_NODE_HOSTNAME`, exporta os hostnames e só então executa `docker stack deploy --resolve-image never`.
  - [x] **VERIFY**: Teste focal T003 com `1 passed`; `bash -n deploy/build_and_deploy.sh` aprovado (2026-10-01).
  - [x] **VISUAL**: Não aplicável — script de infraestrutura sem superfície visual.
  - [x] **EVIDENCE**: GREEN de AC-003; arquivo executável `deploy/build_and_deploy.sh`; documentação reconstruída e verificada.
  - [x] **IMPROVE**: Adicionado `--resolve-image never` para evitar consulta a registry inexistente e validação fail-closed de `DATABASE_NODE_HOSTNAME` somente depois dos builds, preservando a garantia de não implantar quando o build falha.
  <!-- specsfy:evidence {"task":"T013","refs":["US-001","FR-001","NFR-001","AC-003"],"files":["deploy/build_and_deploy.sh","docs/architecture.md"],"commands":[{"run":"uv run pytest tests/test_deploy_build_and_deploy_script.py::test_build_falho_impede_execucao_do_deploy -q","exit":0},{"run":"bash -n deploy/build_and_deploy.sh","exit":0},{"run":"node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project /media/marcio/AKT/Projects/rag-pipeline --check","exit":0}]} -->

**Checkpoint**: `docker swarm init` local + `deploy/build_and_deploy.sh` sobem backend/frontend/worker/postgres/qdrant de produção, todos `Running` em `docker service ls`, isolados dos recursos de teste.

#### Fase 3 — US-002 Proteger credenciais de produção (P1)

**Objetivo**: nenhuma credencial de produção em texto puro no stack file; secret ausente falha visivelmente.
**Teste independente**: inspecionar `deploy/stack.prod.yml` — cada valor sensível é uma referência `secrets:`.

- [x] T014 [CODE] [US-002] Adicionar blocos secrets (external) e referências nos serviços de deploy/stack.prod.yml — Refs: US-002, FR-003, AC-004, AC-005, AC-006 — Depends: T004, T005, T006, T012
  - [x] **PREP**: RED reconfirmado em T004 (`secrets` ausentes); T005/T006 passaram de forma vacuamente estrutural antes de existirem referências. `$specsfy-documentator` executado e `--check` aprovado antes de `EXECUTE` (2026-10-01).
  - [x] **EXECUTE**: Declarados `openrouter_api_key`, `r2_credentials`, `session_secret` e `postgres_password` como secrets externos. Backend/worker leem os quatro arquivos antes de executar, constroem `APP_DATABASE_URL` com senha codificada para URL e carregam o arquivo R2 compatível com shell; Postgres usa `POSTGRES_PASSWORD_FILE`.
  - [x] **VERIFY**: Três testes focais com `3 passed`; `docker stack config -c deploy/stack.prod.yml` aprovou a interpolação e mostrou apenas referências externas, sem valores sensíveis (2026-10-01).
  - [x] **VISUAL**: Não aplicável — arquivo de infraestrutura sem superfície visual.
  - [x] **EVIDENCE**: GREEN de AC-004/AC-005/AC-006; `deploy/stack.prod.yml`; documentação reconstruída e verificada.
  - [x] **IMPROVE**: Adicionada prova de leitura efetiva em `/run/secrets/*`, URL-encoding da senha do Postgres e escape `$$` exigido pelo Compose; o stack falha visivelmente se arquivo secreto estiver ausente ou inválido.
  <!-- specsfy:evidence {"task":"T014","refs":["US-002","FR-003","AC-004","AC-005","AC-006"],"files":["deploy/stack.prod.yml","tests/test_deploy_stack.py","docs/architecture.md"],"commands":[{"run":"uv run pytest tests/test_deploy_stack.py::test_credenciais_sensiveis_sao_referencias_a_secrets tests/test_deploy_stack.py::test_cada_secret_referenciado_esta_declarado_no_stack tests/test_deploy_stack.py::test_nenhum_valor_de_secret_aparece_em_texto_puro -q","exit":0},{"run":"docker stack config -c deploy/stack.prod.yml","exit":0},{"run":"node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project /media/marcio/AKT/Projects/rag-pipeline --check","exit":0}]} -->

**Checkpoint**: `grep` por qualquer segredo real em `deploy/stack.prod.yml` não retorna nada; a spec do `BACKLOG-0030` pode criar os secrets reais sem exigir mudança neste stack file.

#### Fase 4 — US-003 Coexistir com as outras aplicações da VPS sem conflito (P2)

**Objetivo**: Postgres/Qdrant de produção fixados no node de banco de dados; stack integrado à rede compartilhada existente, sem proxy próprio.
**Teste independente**: inspecionar `deploy/stack.prod.yml` — `placement.constraints` e rede `network_swarm_public` presentes e corretamente escopados.

- [x] T015 [CODE] [US-003] Adicionar placement.constraints por node de build/dados e rede externa network_swarm_public em deploy/stack.prod.yml — Refs: US-003, FR-004, AC-007, AC-008, AC-009 — Depends: T007, T008, T009, T012
  - [x] **PREP**: RED reconfirmado em T007/T008/T009 (`3 failed`: ausência de `deploy.placement` e do bloco `networks`); `$specsfy-documentator` executado e `build_documentation.mjs --check` aprovado antes de `EXECUTE` (2026-10-01).
  - [x] **EXECUTE**: Adicionados `deploy.placement.constraints` por `APPLICATION_NODE_HOSTNAME` em backend/frontend/worker e por `DATABASE_NODE_HOSTNAME` em Postgres/Qdrant; declarada `networks.network_swarm_public.external: true` e conectados os cinco serviços a ela.
  - [x] **VERIFY**: Os três testes focais passaram (`3 passed`); `APPLICATION_NODE_HOSTNAME=app-node DATABASE_NODE_HOSTNAME=db-node docker stack config -c deploy/stack.prod.yml` também concluiu com exit 0 e materializou os placements esperados (2026-10-01).
  - [x] **VISUAL**: Não aplicável — arquivo de infraestrutura sem interface visual.
  - [x] **EVIDENCE**: GREEN de AC-007/AC-008/AC-009 registrado; arquivos: `deploy/stack.prod.yml`, `tests/test_deploy_stack.py` e documentação reconstruída em `docs/`.
  - [x] **IMPROVE**: A validação passou a interpolar hostnames distintos (`app-node`/`db-node`), provando que as duas classes de placement não colapsam acidentalmente; nenhuma refatoração adicional foi necessária com os testes verdes.
  <!-- specsfy:evidence {"task":"T015","refs":["US-003","FR-004","AC-007","AC-008","AC-009"],"files":["deploy/stack.prod.yml","tests/test_deploy_stack.py","docs/architecture.md"],"commands":[{"run":"uv run pytest tests/test_deploy_stack.py::test_servicos_tem_placement_compativel_com_imagens_locais tests/test_deploy_stack.py::test_stack_conecta_rede_externa_network_swarm_public tests/test_deploy_stack.py::test_constraints_de_placement_sao_bem_formadas_e_escopadas_por_servico -q","exit":0},{"run":"APPLICATION_NODE_HOSTNAME=app-node DATABASE_NODE_HOSTNAME=db-node docker stack config -c deploy/stack.prod.yml","exit":0},{"run":"node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check","exit":0}]} -->

**Checkpoint**: `deploy/stack.prod.yml` pronto para receber, no VPS real, o nome exato do node de banco de dados e o secret real (BACKLOG-0030), sem mudança estrutural adicional.

#### Fase final — Qualidade

- [x] T016 [DOC] Atualizar .specsfy/STACK.md com Docker Swarm de produção e os arquivos deploy/* — Refs: FR-001, FR-004 — Depends: T012, T013, T014, T015
  - [x] **PREP**: T012–T015 confirmadas como concluídas; `specsfy doctor`, `setup_context.mjs` e `update_stack.mjs` executados novamente antes da atualização manual aditiva (2026-10-01).
  - [x] **EXECUTE**: Inventário de `.specsfy/STACK.md` atualizado de forma aditiva com empacotamento backend/worker, frontend standalone, orquestração Docker Swarm e entrega fail-fast; as evidências apontam para os quatro artefatos `deploy/*` previstos.
  - [x] **VERIFY**: `monitor_context.mjs --project . --check` retornou `Context monitor: CURRENT`, sem pendência em `STACK.md`; documentação reconstruída e `build_documentation.mjs --check` aprovado (2026-10-01).
  - [x] **VISUAL**: Não aplicável — documentação técnica sem interface visual.
  - [x] **EVIDENCE**: `.specsfy/STACK.md` registra os quatro artefatos de deploy; monitor de contexto `CURRENT` e documentação automática em estado consistente.
  - [x] **IMPROVE**: A linha genérica de “Containers” foi tornada verificável e separada entre Compose de teste e Swarm de produção, evitando que agentes futuros confundam os dois ambientes.

- [x] T017 [TEST] Executar regressão completa em tests/ e verificação manual de deploy/build_and_deploy.sh em Swarm local — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009 — Depends: T013, T014, T015, T016
  - [x] **PREP**: Identificados os checks de encerramento: `uv run pytest`, `uv run ruff check .`, rastreabilidade Specsfy, lint/typecheck/Vitest/build do frontend, builds Docker e inspeção Swarm; setup/documentação foram revalidados antes da execução (2026-10-01). Preflight repetido em 2026-10-03: isolamento inicialmente não comprovado e operações destrutivas detectadas; ambos corrigidos na retomada, com prova SAFE, fixtures não destrutivas e CLI oficial 0.23.0 (`doctor` aprovado); evidências na seção 13.
  - [x] **EXECUTE**: Em 2026-10-03, isolamento de .env.testing comprovado, testes destrutivos substituídos, regressão integral com RUN_SPEC0014_REAL=1 (419 passed, zero skips), frontend (135 testes) e builds reais executados. Swarm local inicializado, script real implantado e cinco serviços estáveis 1/1; HTTP autenticado, isolamento de Base, falhas AC-003/AC-005/AC-009 e rotação AC-006 observados. Evidência bruta: research/t017-swarm-local.json. Correções internas: escape da URL Alembic, diretório de uploads gravável pelo usuário não-root e bit executável do script.
  - [x] **VERIFY**: RUN_SPEC0014_REAL=1 uv run pytest -q → 419 passed, zero skips; 19 testes focais de segurança/migrations/worker e 16 focais de deploy/segurança aprovados. Ruff, ESLint, typecheck, 135 testes Vitest, build standalone, builds Docker e nove ACs do Swarm local aprovados. Rastreabilidade full-chain 17/17 IDs; documentação CURRENT e diff sem erro. Nenhuma falha preexistente permanece aberta.
  - [x] **VISUAL**: Não aplicável — Dockerfile, script, ambiente e fixtures de testes, escape de URL Alembic e documentação técnica não alteram telas, componentes, layout, bordas, espaçamentos ou tipografia. O proxy foi exercitado por HTTP autenticado, sem mudança de interface.
  - [x] **EVIDENCE**: Seções 11–13 atualizadas com GREEN, regressão integral (419 passed), matriz de nove ACs e comandos; comentário specsfy:evidence abaixo e research/t017-swarm-local.json registram os arquivos, hashes de deploy e provas locais por AC. Rastreabilidade full-chain 17/17; QA, findings e evidências aprovados na conferência final.
  - [x] **IMPROVE**: Melhorias aplicadas: pré-condição fail-closed para banco Python, fixtures sem limpeza global, isolamento de migrations por avanço, smoke test real como não-root e bit executável preservado pelo Git. A validação estrutural isolada não detectava a permissão de uploads; o ensaio de runtime agora registra essa prova. Permanecem fora da sessão somente node dedicado, rede/Traefik e credenciais reais no VPS, conforme DEC-004; nenhum bloqueio local pendente.
  <!-- specsfy:evidence {"task":"T017","refs":["US-001","US-002","US-003","FR-001","FR-002","FR-003","FR-004","NFR-001","AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-007","AC-008","AC-009"],"files":["deploy/backend/Dockerfile","deploy/frontend/Dockerfile","deploy/stack.prod.yml","deploy/build_and_deploy.sh","alembic/env.py","tests/conftest.py","tests/_database_safety.py","tests/test_database_safety.py","tests/test_app_migrations.py","tests/test_app_worker.py",".env.testing.example",".github/workflows/ci.yml",".gitignore",".specsfy/STACK.md",".specsfy/DATABASE.md","README.md","docs/testing.md"],"commands":[{"run":"uv run python -m tests._database_safety","exit":0},{"run":"RUN_SPEC0014_REAL=1 uv run pytest -q","exit":0},{"run":"uv run ruff check .","exit":0},{"run":"npm run lint","cwd":"frontend","exit":0},{"run":"npm run typecheck","cwd":"frontend","exit":0},{"run":"npm run test:tdd","cwd":"frontend","exit":0},{"run":"API_PROXY_TARGET=http://backend_ragpipeline:8000 NEXT_TELEMETRY_DISABLED=1 npm run build","cwd":"frontend","exit":0},{"run":"APPLICATION_NODE_HOSTNAME=developer-oracle DATABASE_NODE_HOSTNAME=developer-oracle deploy/build_and_deploy.sh","exit":0},{"run":"uv run python /tmp/t017-swarm-proof.py","exit":0},{"run":"uv run python /tmp/t017-secret-rotation.py","exit":0},{"run":"node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check","exit":0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001/T002/T003 → T010/T011 → T012 → T013 → T004/T005/T006 → T014 → T007/T008/T009 → T015 → T016 → T017.
- Tarefas paralelas: nenhuma marcada `[P]` — T001–T009 compartilham os mesmos
  arquivos de teste (`tests/test_deploy_stack.py`,
  `tests/test_deploy_build_and_deploy_script.py`), e as tarefas `[CODE]`
  seguintes dependem de RED observado nos respectivos predecessores.
- Estratégia de MVP: Fase 2 (US-001) sozinha já entrega valor demonstrável —
  a stack sobe e persiste dados isolados dos de teste, mesmo antes dos
  secrets (Fase 3) e do placement/rede (Fase 4) estarem prontos, permitindo
  verificação incremental em Swarm local a cada fase.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Nenhuma bloqueante. Toda a camada de aplicação (backend, frontend, worker)
  já está implementada e mesclada em `main`.

#### Riscos

- Node de banco de dados da VPS pode não ter capacidade (CPU/memória/disco)
  para mais este Postgres e Qdrant, além das cargas já existentes → mitigação:
  confirmar recursos disponíveis antes do primeiro deploy real; ajustar
  `limits` do stack file conforme necessário.
- `output: "standalone"` no Next.js pode exigir ajuste em imports ou assets
  não previstos → mitigação: build local (`npm run build`) validado antes de
  buildar a imagem Docker.

#### Suposições

- O node de banco de dados dedicado já usado por outras aplicações da VPS é
  o destino correto para `postgres_ragpipeline` e `qdrant_ragpipeline`; o
  nome exato do node é confirmado na implementação, sem impacto de escopo.
- Build direto no VPS (sem registry) é aceitável nesta fase, dado o volume de
  deploys esperado (uso interno, deploy manual); as imagens locais ficam
  restritas ao node que executou o build — default reversível, registrado no
  BACKLOG-0028 e confirmado pela pessoa responsável em 2026-10-01.

### 17. Decisões

- **DEC-001**: reaproveitar a mesma imagem Docker para os serviços `backend`
  e `worker` (ambos rodam o mesmo código-base Python), variando apenas o
  `command:` de cada serviço no stack file — alternativa descartada: duas
  imagens quase idênticas, sem benefício dado que o worker não tem
  dependências extras.
- **DEC-002**: adicionar `output: "standalone"` a `frontend/next.config.ts` e
  apontar `API_PROXY_TARGET` para o nome DNS interno do serviço `backend`
  (`http://backend_ragpipeline:8000`). A implementação detectou em 2026-10-01
  que Next.js 16 serializa rewrites no artefato standalone durante o build;
  por isso o valor não sensível é resolvido por `build_and_deploy.sh`, passado
  como build arg e repetido no ambiente do serviço do stack. Alternativas
  descartadas: manter `127.0.0.1`, que não resolve entre containers, ou
  confiar apenas no ambiente de runtime, que não altera o rewrite já
  serializado.
- **DEC-003**: nomear os serviços do stack como `<tecnologia>_ragpipeline`
  (`backend_ragpipeline`, `frontend_ragpipeline`, `worker_ragpipeline`,
  `postgres_ragpipeline`, `qdrant_ragpipeline`), seguindo a convenção
  `<tecnologia>_<app>` já usada pelas outras aplicações da VPS (evidenciada
  pelo exemplo real `postgres_n8n`) — alternativa descartada: nomes livres,
  que quebrariam a consistência operacional já estabelecida por Marcio.
- **DEC-004**: validar o stack file e os Dockerfiles neste ambiente de
  desenvolvimento via parsing estrutural, `docker build` real e um Swarm
  local de single-node (`docker swarm init` local) — não no VPS de produção,
  ao qual esta sessão não tem acesso — alternativa descartada: assumir
  correção sem qualquer prova executável; a verificação final contra o VPS
  real permanece manual, feita por Marcio (seção 11).
- **DEC-005**: criar `deploy/build_and_deploy.sh` para tornar AC-003
  (falha de build não derruba serviço em execução) verificável por teste
  automatizado, em vez de depender só de inspeção manual do comportamento do
  Swarm — alternativa descartada: documentar a ordem "buildar antes de
  implantar" apenas em prosa, sem prova executável.
- **DEC-006**: sem registry, fixar backend, frontend e worker no node que
  executa o build local; fixar Postgres e Qdrant no node dedicado a dados.
  A pessoa responsável confirmou esta opção em 2026-10-01. Alternativas
  descartadas nesta fase: construir manualmente em cada node ou introduzir
  registry privado.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/STACK.md` registra Docker Swarm como tecnologia de deploy de
      produção, os Dockerfiles em `deploy/` e o stack file
      `deploy/stack.prod.yml`, com a evidência apontando para esses arquivos.
