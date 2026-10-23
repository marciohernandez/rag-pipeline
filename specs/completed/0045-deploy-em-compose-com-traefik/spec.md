# Especificação integrada: Deploy em Compose com Traefik compartilhado, mantendo opção Swarm

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0045 |
| Slug | 0045-deploy-em-compose-com-traefik |
| Status | Complete |
| Effort | 5 |
| Effort updated at | 2026-10-23 |
| Effort rationale | Infraestrutura nova (Compose, Traefik, SSH, migrations) com muitas peças pequenas e risco operacional; sem lógica de domínio. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-10-23 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O deploy do Beta existe só para Docker Swarm ([deploy/stack.prod.yml](deploy/stack.prod.yml)), com Postgres externo (SPEC-0041). A VPS de destino não tem Swarm; tem Docker Compose, o Traefik compartilhado (outro stack) e a rede `n8n-dev-stack_traefik_net`, no padrão do projeto factory. Sem outro caminho, não há como fazer o primeiro deploy.

#### Resultado desejado

O Beta publicado na VPS com Compose + Traefik compartilhado por `make deploy`, com Postgres em container, backup mantido e verificação real de DNS e HTTPS. Os arquivos e as imagens do Swarm continuam utilizáveis, para a mudança futura exigir só a troca do orquestrador.

#### Métricas de sucesso

- Um comando (`make deploy`) leva do commit `HEAD` aos cinco serviços `healthy`.
- `curl -I https://<domínio>` responde por HTTPS com certificado emitido e o HTTP redireciona.
- Zero comandos que apaguem volume, banco ou schema nos scripts novos.
- 100% dos arquivos de Swarm sem alteração de comportamento.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: o padrão do factory pode ser reaproveitado sem mudar o Dockerfile? → sim para backend e backup; o frontend embute `API_PROXY_TARGET` no build, então os nomes de serviço do Swarm são mantidos para a imagem servir aos dois modos.
- **R-002**: o nome `compose.yml` na raiz colide com o `docker-compose.yml` do Postgres de teste? → sim, o Compose escolhe `compose.yml` antes de `docker-compose.yml`; por isso os arquivos ficam em `deploy/compose/`.

#### Fontes e contexto consultados

- [deploy/stack.prod.yml](deploy/stack.prod.yml), [deploy/stack.local.yml](deploy/stack.local.yml), [deploy/RUNBOOK.md](deploy/RUNBOOK.md), [deploy/SECRETS.md](deploy/SECRETS.md), [deploy/BACKUP.md](deploy/BACKUP.md), [deploy/build_and_deploy.sh](deploy/build_and_deploy.sh) e os três Dockerfiles em `deploy/`.
- Instrução de deploy do projeto factory, colada pela pessoa (preservada na Inbox).
- [specs/backlog/0050-deploy-em-compose-com-traefik-compartilhado-mantendo-opcao-swarm.md](specs/backlog/0050-deploy-em-compose-com-traefik-compartilhado-mantendo-opcao-swarm.md) e [specs/inbox/2026-10-23-204304-deploy-em-compose-com-traefik-compartilhado-mantendo-opcao-swarm.md](specs/inbox/2026-10-23-204304-deploy-em-compose-com-traefik-compartilhado-mantendo-opcao-swarm.md).

#### Documentação consultada

- Arquivos locais acima, em 2026-10-23. Nenhuma documentação externa.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: o Swarm ainda será usado? → **A**: só quando o projeto crescer; não é necessário no início.
- **Q**: Postgres? → **A**: em container, sai do Supabase (dados de teste, sem migração).
- **Q**: Qdrant? → **A**: o publicado continua, com prefixo `beta-`.
- **Q**: backup? → **A**: o serviço atual é mantido e passa a apontar para o container (Pergunta 5).
- **Q**: rede e resolver do Traefik? → **A**: `n8n-dev-stack_traefik_net` e `mytlschallenge`.
- **Q**: segredos? → **A**: arquivos 600 montados como secrets do Compose (Pergunta 1).
- **Q**: migrations? → **A**: no `deploy.sh`, depois do backup e antes do `up`, em container descartável (Pergunta 2).
- **Q**: hardening? → **A**: completo, com `tmpfs` (Pergunta 3).
- **Q**: uploads? → **A**: Cloudflare R2 (Pergunta 4).
- **Q**: SPEC-0041 e SPEC-0032? → **A**: ficam como estão; T020 e T027 serão fechadas pelo deploy em Compose (Pergunta 6).

#### Dúvidas abertas

- Host, usuário, pasta, domínio e nome do projeto Compose: `Pendente`, necessários só no deploy real (`ragpipeline` é a sugestão).
- Valores de `mem_limit` e `cpus` por serviço: `Pendente`, a calibrar no Ato II.

### 3. Escopo e atores

#### Incluído

- `compose.yml` e `compose.homolog.yml`, `deploy.sh`, `Makefile`, `.env.example`, Postgres em container, migração no deploy, backup apontando para o container, runbook de Compose e verificação pós-deploy.

#### Fora de escopo

- Executar o deploy na VPS (exige autorização específica da pessoa).
- Criar ou alterar Traefik, a rede compartilhada ou outro projeto da VPS.
- Migrar dados do Supabase.
- Mudar a lógica do backup ou qualquer comportamento da aplicação.
- Remover ou reescrever os arquivos de Swarm.

#### Atores

- **Marcio (responsável pelo deploy)**: opera o `make deploy`, cria segredos e a configuração de deploy no servidor e autoriza qualquer ação na VPS.

### 4. Princípios e restrições do projeto

- **PR-001**: nenhum teste usa o banco de desenvolvimento; os testes desta spec não precisam de banco (verificação estática e servidor simulado).
- **PR-002**: nada executa na VPS sem a pessoa ver o plano e autorizar.
- **PR-003**: nunca apagar volume, banco ou schema como rotina.
- **PR-004**: pare e pergunte se algo exigir mexer no Traefik, na rede compartilhada ou em outro projeto.
- **PR-005**: branch `spec/0045-deploy-em-compose-com-traefik`; PR só depois de `Complete`.

### 5. Histórias de usuário

#### US-001 — Subir o Beta em Compose atrás do Traefik compartilhado (P1)

Como Marcio, quero subir frontend, backend, worker, Postgres e backup em Compose na VPS sem Swarm, com HTTPS pelo Traefik compartilhado, para ter o Beta no ar sem montar um cluster.

**Por que P1**: sem isso não há primeiro deploy.
**Teste independente**: `docker compose config -q` e subida local com `--wait`, sem DNS real.
**Requisitos**: FR-001, FR-002, FR-003, FR-006

#### US-002 — Publicar uma versão com um comando e verificar de verdade (P1)

Como Marcio, quero publicar o commit HEAD com `make deploy`, com backup, migration e verificação pós-deploy, para atualizar o Beta com segurança e saber que DNS e HTTPS funcionam.

**Por que P1**: sem isso não há primeiro deploy.
**Teste independente**: `deploy.sh` contra um servidor simulado (SSH e Docker substituídos).
**Requisitos**: FR-004, FR-005, FR-008

#### US-003 — Manter o Swarm como opção de crescimento (P2)

Como Marcio, quero manter os arquivos e as imagens do Swarm funcionando ao lado do Compose, para migrar para o Swarm quando o projeto crescer sem reescrever imagens nem scripts.

**Por que P2**: não é necessário no início, mas barato de preservar agora e caro de refazer depois.
**Teste independente**: comparar os arquivos de Swarm e validar que o `compose.yml` e o stack usam as mesmas imagens.
**Requisitos**: FR-007

### 6. Cenários BDD de aceite

#### AC-001 — Conjunto sobe saudável

**Cobre**: US-001, FR-001, FR-006, NFR-001

```gherkin
@US-001 @FR-001 @FR-006 @NFR-001 @AC-001
Feature: Conjunto sobe saudável

  Scenario: Conjunto sobe saudável
    Given um servidor com Docker Compose, segredos em arquivo e as imagens construídas
    When o conjunto sobe com `docker compose -p ragpipeline up -d --wait`
    Then postgres_ragpipeline, backend_ragpipeline, worker_ragpipeline, frontend_ragpipeline e backup_ragpipeline ficam `healthy` e nenhum publica porta no host
```

#### AC-002 — Só o frontend é exposto por HTTPS

**Cobre**: US-001, FR-001, FR-002, NFR-003

```gherkin
@US-001 @FR-001 @FR-002 @NFR-003 @AC-002
Feature: Só o frontend é exposto por HTTPS

  Scenario: Só o frontend é exposto por HTTPS
    Given o domínio apontando para a VPS e o Traefik compartilhado em execução
    When se pede `https://<domínio>` e `/api/v1/...`
    Then o frontend responde por HTTPS com certificado emitido pelo `mytlschallenge`, a API responde pelo proxy do Next na mesma origem e backend, worker e Postgres não têm rota no Traefik
```

#### AC-003 — Dependência indisponível não passa como saudável

**Cobre**: US-001, FR-001, FR-006, NFR-003

```gherkin
@US-001 @FR-001 @FR-006 @NFR-003 @AC-003
Feature: Dependência indisponível não passa como saudável

  Scenario: Dependência indisponível não passa como saudável
    Given o Postgres não ficou saudável
    When o conjunto sobe com `--wait`
    Then o comando falha, indica o serviço não saudável e o deploy relata o erro com os logs, sem declarar sucesso
```

#### AC-004 — Login com limite, HSTS e redirecionamento

**Cobre**: US-001, FR-002, NFR-001

```gherkin
@US-001 @FR-002 @NFR-001 @AC-004
Feature: Login com limite, HSTS e redirecionamento

  Scenario: Login com limite, HSTS e redirecionamento
    Given o roteamento do frontend configurado
    When se faz `POST /api/v1/auth/login` repetidas vezes e se acessa por HTTP
    Then o login é limitado pelo rate limit configurado, as respostas HTTPS trazem HSTS e o HTTP redireciona permanentemente para HTTPS
```

#### AC-005 — Segredo ausente falha cedo

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-005
Feature: Segredo ausente falha cedo

  Scenario: Segredo ausente falha cedo
    Given um arquivo de segredo ausente ou com permissão diferente de 600
    When o deploy valida os pré-requisitos
    Then o deploy para antes do build, nomeia o segredo e a permissão esperada e não imprime valores
```

#### AC-006 — Deploy publica exatamente o HEAD

**Cobre**: US-002, FR-004, FR-005, NFR-002

```gherkin
@US-002 @FR-004 @FR-005 @NFR-002 @AC-006
Feature: Deploy publica exatamente o HEAD

  Scenario: Deploy publica exatamente o HEAD
    Given o commit HEAD local já está no remoto e a configuração de deploy está fora do repositório
    When se executa `make deploy`
    Then o servidor faz checkout desse commit, constrói, migra e sobe os serviços, e a versão das imagens é o commit curto
```

#### AC-007 — Deploy recusa árvore suja ou commit fora do remoto

**Cobre**: US-002, FR-004, FR-005, NFR-003

```gherkin
@US-002 @FR-004 @FR-005 @NFR-003 @AC-007
Feature: Deploy recusa árvore suja ou commit fora do remoto

  Scenario: Deploy recusa árvore suja ou commit fora do remoto
    Given alterações não commitadas ou um HEAD que não está no remoto
    When se executa `make deploy`
    Then o script recusa antes de qualquer comando no servidor e diz o que fazer
```

#### AC-008 — Build com erro mantém os serviços atuais

**Cobre**: US-002, FR-004, NFR-002, NFR-003

```gherkin
@US-002 @FR-004 @NFR-002 @NFR-003 @AC-008
Feature: Build com erro mantém os serviços atuais

  Scenario: Build com erro mantém os serviços atuais
    Given uma versão em execução e um build novo que falha
    When o deploy roda
    Then o script aborta sem executar `up`, `down` ou remover volume, e os serviços atuais continuam em execução
```

#### AC-009 — Migration aplicada antes da subida

**Cobre**: US-002, FR-004, FR-006

```gherkin
@US-002 @FR-004 @FR-006 @AC-009
Feature: Migration aplicada antes da subida

  Scenario: Migration aplicada antes da subida
    Given um Postgres de pé e saudável, com banco novo ou com uma versão que traz migration nova
    When o deploy chega ao passo de migração
    Then o backup foi feito antes quando já havia dados, `alembic upgrade head` roda em container descartável e só então backend, worker, frontend e backup sobem; se a migration falhar, a versão nova não sobe
```

#### AC-010 — Arquivos de Swarm preservados

**Cobre**: US-003, FR-007, NFR-002

```gherkin
@US-003 @FR-007 @NFR-002 @AC-010
Feature: Arquivos de Swarm preservados

  Scenario: Arquivos de Swarm preservados
    Given o repositório com o novo caminho Compose
    When se comparam `deploy/stack.prod.yml`, `secrets.sh`, `build_and_deploy.sh` e `RUNBOOK.md` com a versão anterior
    Then nenhum desses arquivos foi alterado em comportamento e o stack continua válido
```

#### AC-011 — Mesmas imagens nos dois modos

**Cobre**: US-003, FR-001, FR-007, NFR-002

```gherkin
@US-003 @FR-001 @FR-007 @NFR-002 @AC-011
Feature: Mesmas imagens nos dois modos

  Scenario: Mesmas imagens nos dois modos
    Given os Dockerfiles de backend, frontend e backup
    When o Compose e o Swarm constroem as imagens
    Then os dois usam os mesmos Dockerfiles, a mesma etiqueta `rag-pipeline-<serviço>:<commit>` e os mesmos nomes de serviço, e as bases têm manifest para ARM e x86_64
```

#### AC-012 — Traefik e rede compartilhada não são alterados

**Cobre**: US-003, FR-002, NFR-003

```gherkin
@US-003 @FR-002 @NFR-003 @AC-012
Feature: Traefik e rede compartilhada não são alterados

  Scenario: Traefik e rede compartilhada não são alterados
    Given a rede `n8n-dev-stack_traefik_net` já existe
    When o Compose é validado e implantado
    Then a rede é referenciada com `external: true`, router, service e middleware têm o prefixo `ragpipeline-`, e nenhum recurso do Traefik ou de outro projeto é criado, alterado ou removido
```

#### AC-013 — Compose não depende de recursos exclusivos do Swarm

**Cobre**: US-003, FR-007, NFR-002

```gherkin
@US-003 @FR-007 @NFR-002 @AC-013
Feature: Compose não depende de recursos exclusivos do Swarm

  Scenario: Compose não depende de recursos exclusivos do Swarm
    Given o `compose.yml` do caminho Compose
    When ele é validado com `docker compose config -q`
    Then o arquivo não usa `deploy:` de Swarm nem secrets externos, e os nomes dos secrets lógicos coincidem com os do Swarm, para a troca ser só de origem
```

#### AC-014 — Primeira instalação documentada e executável

**Cobre**: US-002, FR-008, NFR-003

```gherkin
@US-002 @FR-008 @NFR-003 @AC-014
Feature: Primeira instalação documentada e executável

  Scenario: Primeira instalação documentada e executável
    Given uma VPS sem o projeto
    When se segue a seção de primeira instalação do runbook
    Then pasta, segredos 600, `known_hosts`, acesso de leitura ao Git, DNS e configuração de deploy são criados na ordem, com comandos exatos e sem segredos no texto
```

#### AC-015 — Verificação pós-deploy comprova DNS e HTTPS

**Cobre**: US-002, FR-008, NFR-003

```gherkin
@US-002 @FR-008 @NFR-003 @AC-015
Feature: Verificação pós-deploy comprova DNS e HTTPS

  Scenario: Verificação pós-deploy comprova DNS e HTTPS
    Given um deploy concluído
    When se executa a verificação do runbook
    Then ela confere containers `healthy`, `curl -I https://<domínio>`, certificado emitido e logs sem erro; container saudável sozinho não basta
```

#### AC-016 — Verificação reprovada leva ao retorno

**Cobre**: US-002, FR-008, NFR-003

```gherkin
@US-002 @FR-008 @NFR-003 @AC-016
Feature: Verificação reprovada leva ao retorno

  Scenario: Verificação reprovada leva ao retorno
    Given uma verificação reprovada
    When se aplica o retorno do runbook
    Then o deploy volta à etiqueta anterior sem construir nada e sem apagar volume ou banco
```

#### AC-017 — Variáveis e exemplo sem segredos

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-017
Feature: Variáveis e exemplo sem segredos

  Scenario: Variáveis e exemplo sem segredos
    Given o `.env.example` e o repositório
    When se inspecionam os arquivos versionados
    Then o exemplo contém só nomes de variáveis, `.env`, a pasta de segredos e a configuração de deploy não são versionados, e o `.gitignore` os cobre
```

#### AC-018 — Variável obrigatória ausente falha cedo

**Cobre**: US-001, FR-003, NFR-003

```gherkin
@US-001 @FR-003 @NFR-003 @AC-018
Feature: Variável obrigatória ausente falha cedo

  Scenario: Variável obrigatória ausente falha cedo
    Given `DOMINIO_RAGPIPELINE` ou `QDRANT_URL` ausente
    When `docker compose config` roda
    Then falha com a mensagem `${VAR:?mensagem}` da variável, sem subir nada
```

#### AC-019 — Alvos do Makefile

**Cobre**: US-002, FR-005, NFR-003

```gherkin
@US-002 @FR-005 @NFR-003 @AC-019
Feature: Alvos do Makefile

  Scenario: Alvos do Makefile
    Given o Makefile na raiz
    When se executam `make deploy`, `make deploy-config` e `make deploy-logs`
    Then cada alvo chama o script com o projeto Compose `ragpipeline` e os dois arquivos, e nenhum alvo contém `down -v`
```

#### AC-020 — Backup aponta para o Postgres em container

**Cobre**: US-001, FR-006, NFR-001

```gherkin
@US-001 @FR-006 @NFR-001 @AC-020
Feature: Backup aponta para o Postgres em container

  Scenario: Backup aponta para o Postgres em container
    Given o serviço de backup do Compose
    When o ciclo de backup roda
    Then ele alcança `postgres_ragpipeline` pela rede interna com `sslmode=disable`, cifra o dump, envia ao R2 e registra `resultado=sucesso`
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O `compose.yml` define frontend, backend, worker, Postgres e backup com os mesmos nomes de serviço do Swarm, sem labels de proxy e sem portas publicadas no host, com `restart: unless-stopped`, `mem_limit`, `cpus` e healthcheck em cada serviço; os containers da aplicação usam `read_only`, `cap_drop: [ALL]`, `no-new-privileges`, `init: true` e `tmpfs` em `/tmp`, `/app/.config` e `/app/.cache`.
- **FR-002**: O `compose.homolog.yml` conecta o frontend à rede externa `n8n-dev-stack_traefik_net` e define as labels do Traefik com prefixo `ragpipeline-`: HTTPS pelo `mytlschallenge` no `websecure`, redirect de HTTP, HSTS e rate limit do login; só o frontend é roteado.
- **FR-003**: Os segredos são arquivos de permissão 600 em uma pasta do servidor fora do repositório, montados como secrets do Compose em `/run/secrets/<nome>` com os mesmos nomes lógicos do Swarm; as variáveis não secretas ficam num `.env` do servidor; variáveis obrigatórias usam `${VAR:?mensagem}`; o `.env.example` só traz nomes.
- **FR-004**: O `deploy.sh` lê a configuração de `DEPLOY_CONFIG`, publica exatamente o `HEAD` já no remoto por SSH (`BatchMode=yes`, `StrictHostKeyChecking=yes`, sem agent forwarding) e, no servidor, valida pré-requisitos, faz `git fetch` e `checkout --detach`, exige árvore limpa e `compose config -q`, constrói as imagens, sobe só o Postgres (`up -d --no-build --wait postgres_ragpipeline`), faz um ciclo de backup quando já existe banco com dados, aplica as migrations e só então executa `up -d --no-build --wait` para o conjunto, sem `down` e sem remover volumes.
- **FR-005**: O `Makefile` oferece `make deploy`, `make deploy-config` e `make deploy-logs`, que chamam o script com o projeto Compose `ragpipeline` e os dois arquivos.
- **FR-006**: O Postgres roda em container próprio com o volume nomeado `ragpipeline_postgres_data`, sem porta publicada e com healthcheck; backend, worker, migração e backup o alcançam pela rede interna com `sslmode=disable`, e o backup atual (cifrado, enviado ao R2) é mantido.
- **FR-007**: Os arquivos do Swarm (`deploy/stack.prod.yml`, `stack.local.yml`, `secrets.sh`, `build_and_deploy.sh`, `RUNBOOK.md`) permanecem funcionais, e o Compose reaproveita os mesmos Dockerfiles, etiquetas de imagem e nomes de serviço.
- **FR-008**: O runbook de Compose documenta a primeira instalação (pasta, segredos 600, `known_hosts`, acesso ao Git, DNS, configuração de deploy), a verificação pós-deploy (containers `healthy`, `curl -I https://<domínio>`, certificado, logs), o retorno à versão anterior e a restauração do backup.

#### Não funcionais

- **NFR-001**: Segurança: nenhum segredo no Git, em imagem, em log ou em argumento de comando; arquivos de segredo 600; containers sem privilégios extras; SSH sem agent forwarding e com host verificado. **Verificação**: inspeção dos arquivos versionados e dos scripts, busca por segredos nos logs e `docker inspect` dos containers.
- **NFR-002**: Portabilidade e reprodutibilidade: as imagens constroem em ARM e x86_64 a partir de `uv.lock` e `package-lock.json`, com a mesma etiqueta e os mesmos Dockerfiles do Swarm. **Verificação**: `docker buildx build --platform linux/amd64,linux/arm64` e comparação dos Dockerfiles.
- **NFR-003**: Segurança operacional: nenhum comando do caminho Compose apaga volume, banco ou schema, e nenhum recurso do Traefik, da rede compartilhada ou de outro projeto da VPS é criado, alterado ou removido. **Verificação**: busca estática por `down -v`, `DROP`, `TRUNCATE`, `migrate:fresh`, `volume rm` e `docker network` nos scripts, e `docker compose config` mostrando a rede como `external`.

#### Erros e casos-limite

- Primeira instalação (volume do Postgres novo, sem dados) → o ciclo de backup é dispensado e a migração cria o schema inteiro, inclusive a fila Procrastinate.
- Segredo ausente, com permissão errada ou variável obrigatória ausente → o deploy para antes do build, sem imprimir valores.
- HEAD fora do remoto ou árvore suja → recusa antes de tocar no servidor.
- Rede `n8n-dev-stack_traefik_net` inexistente → recusa e pergunta; não a cria.
- Build, migration ou `--wait` falhando → não substitui os serviços atuais; relata e orienta o retorno.
- Domínio sem DNS → o certificado não é emitido; a verificação pós-deploy acusa.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Python 3.12 (uv, `uv.lock`), FastAPI + worker Procrastinate, frontend Next.js 24, Dockerfiles multi-stage não-root em `deploy/`, scripts Bash em `deploy/`, testes com Pytest em `tests/`.
- O frontend embute `API_PROXY_TARGET` no build; o backend e o worker leem `/run/secrets/*` e montam `APP_DATABASE_URL` a partir de `DATABASE_*`.
- Já existe `docker-compose.yml` na raiz (Postgres de teste, contêiner `rag-pipeline-test-postgres`); não deve ser afetado.

#### Arquitetura e módulos

- `deploy/compose/compose.yml`: serviços `postgres_ragpipeline`, `backend_ragpipeline`, `worker_ragpipeline`, `frontend_ragpipeline`, `backup_ragpipeline`, builds a partir dos Dockerfiles existentes, secrets por `file:`.
- `deploy/compose/compose.homolog.yml`: rede externa e labels do Traefik só no frontend.
- `deploy/compose/deploy.sh`: orquestra local e remoto por SSH; `deploy/compose/.env.example`.
- `Makefile` na raiz com `deploy`, `deploy-config` e `deploy-logs`.
- `deploy/RUNBOOK_COMPOSE.md`: primeira instalação, atualização, verificação, retorno e restauração.
- O comando é sempre `docker compose -p ragpipeline -f deploy/compose/compose.yml -f deploy/compose/compose.homolog.yml`.

#### Migrations

- O schema é aplicado por `alembic upgrade head` em container descartável (imagem do backend) depois do backup e antes do `up`; um banco novo recebe tudo, inclusive a fila Procrastinate. Nenhuma migration nova.

#### Models

- Não aplicável.

#### Controllers e casos de uso

- Não aplicável.

#### Views e experiência

- Não aplicável: sem interface para pessoas.

#### Queries e repositórios

- Não aplicável.

#### Jobs e processamento assíncrono

- O worker Procrastinate sobe como serviço próprio com a mesma imagem do backend; sem mudança de comportamento.

#### Estrutura de arquivos

```text
specs/draft/0045-deploy-em-compose-com-traefik/
  spec.md
  research/
deploy/compose/
  compose.yml
  compose.homolog.yml
  deploy.sh
  .env.example
deploy/RUNBOOK_COMPOSE.md
Makefile
tests/test_deploy_compose_*.py
tests/_compose_deploy.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Volume `ragpipeline_postgres_data` | nome do volume | dados do Postgres; nunca removido | usado por `postgres_ragpipeline` |
| Pasta de segredos | caminho no servidor | arquivos 600 fora do repositório | montados como secrets |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Versão implantada | etiqueta anterior | deploy bem-sucedido | etiqueta nova | a anterior permanece disponível para retorno |

#### Migração e retenção

- Sem migração de dados do Supabase (somente teste). O backup atual mantém a retenção e a cifragem definidas na SPEC-0034.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega é infraestrutura e scripts de operação; nenhuma tela é criada ou alterada.

#### Stack e convenções de interface

- Não aplicável.

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

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável |

#### Estados e acessibilidade

- Não aplicável.

#### Contrato CRUD

- Não aplicável.

#### Revisão visual durante o desenvolvimento

- Não aplicável: nenhuma tarefa tem superfície visual.

#### APIs expostas

- Nenhuma nova. A API existente continua em `/api/*` pelo proxy do Next.

#### APIs externas utilizadas

- Qdrant publicado (`QDRANT_URL`, chave em secret), Cloudflare R2, OpenRouter, Let's Encrypt pelo Traefik. Sem mudança de contrato.

#### Documentação das APIs consultadas

- Nenhuma externa.

#### Eventos e outros contratos

- Contrato de configuração de deploy: `DEPLOY_HOST`, `DEPLOY_USER=deploy`, `DEPLOY_KEY`, `DEPLOY_PATH`, `DEPLOY_PORT` (opcional) e `DEPLOY_REPOSITORY` (opcional), em arquivo shell 600 fora do repositório apontado por `DEPLOY_CONFIG`.

### 11. Estratégia TDD

- **Unidade**: regras do `deploy.sh` (recusas, ordem dos passos, ausência de comandos destrutivos).
- **Integração/contrato**: `docker compose config` dos dois arquivos; comparação dos arquivos de Swarm; `deploy.sh` com `ssh`, `git` e `docker` simulados.
- **BDD/aceite**: o Gherkin da seção 6 orienta os testes.
- **Runner TDD**: Pytest, já adotado no projeto.
- **E2E**: não automatizado; o deploy real e a verificação de HTTPS são feitos pela pessoa depois de autorizar.
- **Verificação manual**: HTTPS e certificado na VPS e conversão de DOC/PPT/XLS sob `read_only` (exige Docker e o domínio reais).

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-006, NFR-001, AC-001 | AC-001 na seção 6 | `tests/test_deploy_compose_base.py::test_conjunto_tem_cinco_servicos_enxutos_e_seguros` (marcador `SPECSFY: SPEC-0045 … AC-001`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-001, FR-001, FR-002, NFR-003, AC-002 | AC-002 na seção 6 | `tests/test_deploy_compose_traefik.py::test_so_o_frontend_e_roteado_por_https` (marcador `SPECSFY: SPEC-0045 … AC-002`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-001, FR-001, FR-006, NFR-003, AC-003 | AC-003 na seção 6 | `tests/test_deploy_compose_base.py::test_aplicacao_espera_o_postgres_ficar_saudavel` (marcador `SPECSFY: SPEC-0045 … AC-003`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-001, FR-002, NFR-001, AC-004 | AC-004 na seção 6 | `tests/test_deploy_compose_traefik.py::test_login_tem_limite_hsts_e_redirecionamento` (marcador `SPECSFY: SPEC-0045 … AC-004`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-001, FR-003, NFR-001, AC-005 | AC-005 na seção 6 | `tests/test_deploy_compose_segredos.py::test_deploy_recusa_segredo_ausente_ou_com_permissao_errada` (marcador `SPECSFY: SPEC-0045 … AC-005`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-002, FR-004, FR-005, NFR-002, AC-006 | AC-006 na seção 6 | `tests/test_deploy_compose_script.py::test_publica_exatamente_o_head_com_ssh_seguro` (marcador `SPECSFY: SPEC-0045 … AC-006`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-002, FR-004, FR-005, NFR-003, AC-007 | AC-007 na seção 6 | `tests/test_deploy_compose_script.py::test_recusa_arvore_suja_ou_head_fora_do_remoto` (marcador `SPECSFY: SPEC-0045 … AC-007`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-002, FR-004, NFR-002, NFR-003, AC-008 | AC-008 na seção 6 | `tests/test_deploy_compose_script.py::test_build_com_erro_nao_derruba_nem_substitui_servicos` (marcador `SPECSFY: SPEC-0045 … AC-008`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-002, FR-004, FR-006, AC-009 | AC-009 na seção 6 | `tests/test_deploy_compose_script.py::test_migra_depois_do_postgres_e_antes_do_conjunto` (marcador `SPECSFY: SPEC-0045 … AC-009`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-003, FR-007, NFR-002, AC-010 | AC-010 na seção 6 | `tests/test_deploy_compose_swarm.py::test_arquivos_de_swarm_intactos_e_runbook_aponta_para_o_compose` (marcador `SPECSFY: SPEC-0045 … AC-010`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-003, FR-001, FR-007, NFR-002, AC-011 | AC-011 na seção 6 | `tests/test_deploy_compose_swarm.py::test_compose_e_swarm_usam_os_mesmos_dockerfiles_e_etiquetas` (marcador `SPECSFY: SPEC-0045 … AC-011`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-003, FR-002, NFR-003, AC-012 | AC-012 na seção 6 | `tests/test_deploy_compose_traefik.py::test_rede_externa_e_nomes_com_prefixo_do_projeto` (marcador `SPECSFY: SPEC-0045 … AC-012`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-003, FR-007, NFR-002, AC-013 | AC-013 na seção 6 | `tests/test_deploy_compose_swarm.py::test_compose_nao_usa_recursos_exclusivos_do_swarm` (marcador `SPECSFY: SPEC-0045 … AC-013`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-002, FR-008, NFR-003, AC-014 | AC-014 na seção 6 | `tests/test_deploy_compose_runbook.py::test_primeira_instalacao_na_ordem_e_sem_segredos` (marcador `SPECSFY: SPEC-0045 … AC-014`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-002, FR-008, NFR-003, AC-015 | AC-015 na seção 6 | `tests/test_deploy_compose_runbook.py::test_verificacao_pos_deploy_prova_dns_e_https` (marcador `SPECSFY: SPEC-0045 … AC-015`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-002, FR-008, NFR-003, AC-016 | AC-016 na seção 6 | `tests/test_deploy_compose_runbook.py::test_retorno_a_versao_anterior_sem_construir_nem_apagar` (marcador `SPECSFY: SPEC-0045 … AC-016`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-001, FR-003, NFR-001, AC-017 | AC-017 na seção 6 | `tests/test_deploy_compose_segredos.py::test_exemplo_so_tem_nomes_e_segredos_nao_sao_versionados` (marcador `SPECSFY: SPEC-0045 … AC-017`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-001, FR-003, NFR-003, AC-018 | AC-018 na seção 6 | `tests/test_deploy_compose_segredos.py::test_variavel_obrigatoria_ausente_falha_cedo` (marcador `SPECSFY: SPEC-0045 … AC-018`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-002, FR-005, NFR-003, AC-019 | AC-019 na seção 6 | `tests/test_deploy_compose_script.py::test_makefile_expoe_os_alvos_sem_comando_destrutivo` (marcador `SPECSFY: SPEC-0045 … AC-019`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |
| US-001, FR-006, NFR-001, AC-020 | AC-020 na seção 6 | `tests/test_deploy_compose_base.py::test_backup_alcanca_o_postgres_em_container_sem_tls` (marcador `SPECSFY: SPEC-0045 … AC-020`) | Observado em 2026-10-23: falha porque o artefato esperado de `deploy/compose/` ainda não existe | Observado em 2026-10-23: passa | Regressão: suíte completa (875 passed) |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Contrato | tests/test_deploy_compose_base.py | Passed |
| FR-001 | AC-002 | Contrato | tests/test_deploy_compose_traefik.py | Passed |
| FR-001 | AC-003 | Contrato | tests/test_deploy_compose_base.py | Passed |
| FR-001 | AC-011 | Contrato | tests/test_deploy_compose_swarm.py | Passed |
| FR-002 | AC-002 | Contrato | tests/test_deploy_compose_traefik.py | Passed |
| FR-002 | AC-004 | Contrato | tests/test_deploy_compose_traefik.py | Passed |
| FR-002 | AC-012 | Contrato | tests/test_deploy_compose_traefik.py | Passed |
| FR-003 | AC-005 | Integração | tests/test_deploy_compose_segredos.py | Passed |
| FR-003 | AC-017 | Integração | tests/test_deploy_compose_segredos.py | Passed |
| FR-003 | AC-018 | Integração | tests/test_deploy_compose_segredos.py | Passed |
| FR-004 | AC-006 | Integração | tests/test_deploy_compose_script.py | Passed |
| FR-004 | AC-007 | Integração | tests/test_deploy_compose_script.py | Passed |
| FR-004 | AC-008 | Integração | tests/test_deploy_compose_script.py | Passed |
| FR-004 | AC-009 | Integração | tests/test_deploy_compose_script.py | Passed |
| FR-005 | AC-006 | Integração | tests/test_deploy_compose_script.py | Passed |
| FR-005 | AC-007 | Integração | tests/test_deploy_compose_script.py | Passed |
| FR-005 | AC-019 | Integração | tests/test_deploy_compose_script.py | Passed |
| FR-006 | AC-001 | Contrato | tests/test_deploy_compose_base.py | Passed |
| FR-006 | AC-003 | Contrato | tests/test_deploy_compose_base.py | Passed |
| FR-006 | AC-009 | Integração | tests/test_deploy_compose_script.py | Passed |
| FR-006 | AC-020 | Contrato | tests/test_deploy_compose_base.py | Passed |
| FR-007 | AC-010 | Contrato | tests/test_deploy_compose_swarm.py | Passed |
| FR-007 | AC-011 | Contrato | tests/test_deploy_compose_swarm.py | Passed |
| FR-007 | AC-013 | Contrato | tests/test_deploy_compose_swarm.py | Passed |
| FR-008 | AC-014 | Contrato | tests/test_deploy_compose_runbook.py | Passed |
| FR-008 | AC-015 | Contrato | tests/test_deploy_compose_runbook.py | Passed |
| FR-008 | AC-016 | Contrato | tests/test_deploy_compose_runbook.py | Passed |
| NFR-001 | AC-001 | Contrato | tests/test_deploy_compose_base.py | Passed |
| NFR-001 | AC-004 | Contrato | tests/test_deploy_compose_traefik.py | Passed |
| NFR-001 | AC-005 | Integração | tests/test_deploy_compose_segredos.py | Passed |
| NFR-001 | AC-017 | Integração | tests/test_deploy_compose_segredos.py | Passed |
| NFR-001 | AC-020 | Contrato | tests/test_deploy_compose_base.py | Passed |
| NFR-002 | AC-006 | Integração | tests/test_deploy_compose_script.py | Passed |
| NFR-002 | AC-008 | Integração | tests/test_deploy_compose_script.py | Passed |
| NFR-002 | AC-010 | Contrato | tests/test_deploy_compose_swarm.py | Passed |
| NFR-002 | AC-011 | Contrato | tests/test_deploy_compose_swarm.py | Passed |
| NFR-002 | AC-013 | Contrato | tests/test_deploy_compose_swarm.py | Passed |
| NFR-003 | AC-002 | Contrato | tests/test_deploy_compose_traefik.py | Passed |
| NFR-003 | AC-003 | Contrato | tests/test_deploy_compose_base.py | Passed |
| NFR-003 | AC-007 | Integração | tests/test_deploy_compose_script.py | Passed |
| NFR-003 | AC-008 | Integração | tests/test_deploy_compose_script.py | Passed |
| NFR-003 | AC-012 | Contrato | tests/test_deploy_compose_traefik.py | Passed |
| NFR-003 | AC-014 | Contrato | tests/test_deploy_compose_runbook.py | Passed |
| NFR-003 | AC-015 | Contrato | tests/test_deploy_compose_runbook.py | Passed |
| NFR-003 | AC-016 | Contrato | tests/test_deploy_compose_runbook.py | Passed |
| NFR-003 | AC-018 | Integração | tests/test_deploy_compose_segredos.py | Passed |
| NFR-003 | AC-019 | Integração | tests/test_deploy_compose_script.py | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed (READY, 2026-10-23)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0045-deploy-em-compose-com-traefik/spec.md`
- **Achados**: 3 US, 8 FR, 3 NFR e 20 AC, com cobertura mínima de 3 AC por US, FR e NFR. Corrigidos na revisão: (1) WARNING→BLOCKER de teste no FR-004, porque o backup e a migração exigem o Postgres de pé, e a ordem agora sobe só o Postgres antes; (2) primeira instalação sem dados, em que o backup é dispensado (caso-limite); (3) a Definition of Done passou a citar STACK, DATABASE, PROJECT, RULES e INTERFACE. Aberto sem bloquear: host, usuário, pasta, domínio e nome do projeto Compose, e `mem_limit` e `cpus`.

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-23)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0045-deploy-em-compose-com-traefik/spec.md`
- **Achados**: 31 tarefas (20 TDD em RED válido, 7 de código, 3 de documentação e 1 de regressão), 34 de 34 IDs cobertos. Todos os predecessores TDD de tarefas `[CODE]` estão concluídos. Os testes ficam em `tests/test_deploy_compose_*.py` e usam o servidor simulado de `tests/_compose_deploy.py`.

#### Gate do Ato III — Entrega

- **Resultado**: Passed (2026-10-23)
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0045-deploy-em-compose-com-traefik/spec.md .`
- **Achados**: 31 de 31 tarefas concluídas; 34 de 34 IDs rastreados; 20 testes novos verdes; suíte completa verde exceto um teste de timeout sensível a carga, que passa isolado. O deploy real na VPS fica fora desta spec.

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

Nenhuma tarefa executa comando na VPS, usa o banco de desenvolvimento ou apaga volume, banco ou schema. Os testes usam arquivos, `docker compose config` e um servidor simulado (`ssh`, `git` e `docker` substituídos no `PATH`).

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 (conjunto sobe saudável) um caso Pytest falhando em tests/test_deploy_compose_base.py — Refs: US-001, FR-001, FR-006, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-001` em tests/test_deploy_compose_base.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_base.py::test_conjunto_tem_cinco_servicos_enxutos_e_seguros` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 (só o frontend é exposto por https) um caso Pytest falhando em tests/test_deploy_compose_traefik.py — Refs: US-001, FR-001, FR-002, NFR-003, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-002` em tests/test_deploy_compose_traefik.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_traefik.py::test_so_o_frontend_e_roteado_por_https` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 (dependência indisponível não passa como saudável) um caso Pytest falhando em tests/test_deploy_compose_base.py — Refs: US-001, FR-001, FR-006, NFR-003, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-003` em tests/test_deploy_compose_base.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_base.py::test_aplicacao_espera_o_postgres_ficar_saudavel` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 (login com limite, hsts e redirecionamento) um caso Pytest falhando em tests/test_deploy_compose_traefik.py — Refs: US-001, FR-002, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-004` em tests/test_deploy_compose_traefik.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_traefik.py::test_login_tem_limite_hsts_e_redirecionamento` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 (segredo ausente falha cedo) um caso Pytest falhando em tests/test_deploy_compose_segredos.py — Refs: US-001, FR-003, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-005` em tests/test_deploy_compose_segredos.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_segredos.py::test_deploy_recusa_segredo_ausente_ou_com_permissao_errada` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 (deploy publica exatamente o head) um caso Pytest falhando em tests/test_deploy_compose_script.py — Refs: US-002, FR-004, FR-005, NFR-002, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-006` em tests/test_deploy_compose_script.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_script.py::test_publica_exatamente_o_head_com_ssh_seguro` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 (deploy recusa árvore suja ou commit fora do remoto) um caso Pytest falhando em tests/test_deploy_compose_script.py — Refs: US-002, FR-004, FR-005, NFR-003, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-007` em tests/test_deploy_compose_script.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_script.py::test_recusa_arvore_suja_ou_head_fora_do_remoto` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 (build com erro mantém os serviços atuais) um caso Pytest falhando em tests/test_deploy_compose_script.py — Refs: US-002, FR-004, NFR-002, NFR-003, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-008` em tests/test_deploy_compose_script.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_script.py::test_build_com_erro_nao_derruba_nem_substitui_servicos` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 (migration aplicada antes da subida) um caso Pytest falhando em tests/test_deploy_compose_script.py — Refs: US-002, FR-004, FR-006, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-009` em tests/test_deploy_compose_script.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_script.py::test_migra_depois_do_postgres_e_antes_do_conjunto` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-010 (arquivos de swarm preservados) um caso Pytest falhando em tests/test_deploy_compose_swarm.py — Refs: US-003, FR-007, NFR-002, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-010` em tests/test_deploy_compose_swarm.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_swarm.py::test_arquivos_de_swarm_intactos_e_runbook_aponta_para_o_compose` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 (mesmas imagens nos dois modos) um caso Pytest falhando em tests/test_deploy_compose_swarm.py — Refs: US-003, FR-001, FR-007, NFR-002, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-011` em tests/test_deploy_compose_swarm.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_swarm.py::test_compose_e_swarm_usam_os_mesmos_dockerfiles_e_etiquetas` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 (traefik e rede compartilhada não são alterados) um caso Pytest falhando em tests/test_deploy_compose_traefik.py — Refs: US-003, FR-002, NFR-003, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-012` em tests/test_deploy_compose_traefik.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_traefik.py::test_rede_externa_e_nomes_com_prefixo_do_projeto` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-013 (compose não depende de recursos exclusivos do swarm) um caso Pytest falhando em tests/test_deploy_compose_swarm.py — Refs: US-003, FR-007, NFR-002, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-013 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-013` em tests/test_deploy_compose_swarm.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_swarm.py::test_compose_nao_usa_recursos_exclusivos_do_swarm` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T014 [TEST] [TDD] [US-002] Derivar do AC-014 (primeira instalação documentada e executável) um caso Pytest falhando em tests/test_deploy_compose_runbook.py — Refs: US-002, FR-008, NFR-003, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-014 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-014` em tests/test_deploy_compose_runbook.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_runbook.py::test_primeira_instalacao_na_ordem_e_sem_segredos` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T015 [TEST] [TDD] [US-002] Derivar do AC-015 (verificação pós-deploy comprova dns e https) um caso Pytest falhando em tests/test_deploy_compose_runbook.py — Refs: US-002, FR-008, NFR-003, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-015 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-015` em tests/test_deploy_compose_runbook.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_runbook.py::test_verificacao_pos_deploy_prova_dns_e_https` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T016 [TEST] [TDD] [US-002] Derivar do AC-016 (verificação reprovada leva ao retorno) um caso Pytest falhando em tests/test_deploy_compose_runbook.py — Refs: US-002, FR-008, NFR-003, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-016 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-016` em tests/test_deploy_compose_runbook.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_runbook.py::test_retorno_a_versao_anterior_sem_construir_nem_apagar` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T017 [TEST] [TDD] [US-001] Derivar do AC-017 (variáveis e exemplo sem segredos) um caso Pytest falhando em tests/test_deploy_compose_segredos.py — Refs: US-001, FR-003, NFR-001, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-017 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-017` em tests/test_deploy_compose_segredos.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_segredos.py::test_exemplo_so_tem_nomes_e_segredos_nao_sao_versionados` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T018 [TEST] [TDD] [US-001] Derivar do AC-018 (variável obrigatória ausente falha cedo) um caso Pytest falhando em tests/test_deploy_compose_segredos.py — Refs: US-001, FR-003, NFR-003, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-018 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-018` em tests/test_deploy_compose_segredos.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_segredos.py::test_variavel_obrigatoria_ausente_falha_cedo` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T019 [TEST] [TDD] [US-002] Derivar do AC-019 (alvos do makefile) um caso Pytest falhando em tests/test_deploy_compose_script.py — Refs: US-002, FR-005, NFR-003, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-019 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-019` em tests/test_deploy_compose_script.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_script.py::test_makefile_expoe_os_alvos_sem_comando_destrutivo` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

- [x] T020 [TEST] [TDD] [US-001] Derivar do AC-020 (backup aponta para o postgres em container) um caso Pytest falhando em tests/test_deploy_compose_base.py — Refs: US-001, FR-006, NFR-001, AC-020 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-020 na spec e confirmar regra, IDs e nível (contrato estático ou servidor simulado).
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:AC-020` em tests/test_deploy_compose_base.py, sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido: falha por asserção sobre comportamento ausente, não por sintaxe ou importação.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual, só materializa teste.
  - [x] **EVIDENCE**: RED observado: `uv run pytest tests/test_deploy_compose_base.py::test_backup_alcanca_o_postgres_em_container_sem_tls` falha com o artefato de `deploy/compose/` ausente.
  - [x] **IMPROVE**: Caso reutiliza `tests/_compose_deploy.py` (servidor simulado), sem duplicar apoio.

#### Fase 2 — US-001 Subir o Beta em Compose atrás do Traefik compartilhado (P1)

**Objetivo**: ter o conjunto Compose completo, seguro e roteado pelo Traefik compartilhado.
**Teste independente**: `uv run pytest tests/test_deploy_compose_base.py tests/test_deploy_compose_traefik.py tests/test_deploy_compose_segredos.py -q` passa e `docker compose config -q` valida os dois arquivos.

- [x] T021 [P] [CODE] [US-001] Criar o conjunto base em deploy/compose/compose.yml (Postgres, backend, worker, frontend e backup, hardening, healthchecks, limites, secrets por arquivo) — Refs: US-001, FR-001, FR-006, NFR-001, NFR-002, NFR-003, AC-001, AC-003, AC-011, AC-013, AC-020 — Depends: T001, T003, T011, T013, T020
  - [x] **PREP**: Confirmar o RED TDD dos AC listados, reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE` e conferir que os nomes de serviço, Dockerfiles e etiquetas coincidem com `deploy/stack.prod.yml`. Documentação reconstruída por `build_documentation.mjs` e RED confirmado nos predecessores.
  - [x] **EXECUTE**: `deploy/compose/compose.yml` criado: 5 serviços com os nomes do Swarm, secrets `file:`, hardening, healthchecks, limites e volume nomeado.
  - [x] **VERIFY**: `docker compose config -q` válido; testes de AC-001, AC-003, AC-011, AC-013 e AC-020 passam.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (infraestrutura e scripts).
  - [x] **EVIDENCE**: GREEN: `uv run pytest tests/test_deploy_compose_*.py -q` verde (20 passed); `uv run ruff check` sem achados.
  - [x] **IMPROVE**: Healthchecks de worker e backup montados para não casarem com o próprio processo; `tmpfs` em `/app/output` acrescentado porque o backend grava ali com `read_only`.
  <!-- specsfy:evidence {"task": "T021", "refs": ["US-001", "FR-001", "FR-006", "NFR-001", "NFR-002", "NFR-003", "AC-001", "AC-003", "AC-011", "AC-013", "AC-020"], "files": ["deploy/compose/compose.yml"], "commands": [{"run": "uv run pytest tests/test_deploy_compose_*.py -q", "exit": 0}]} -->

- [x] T022 [P] [CODE] [US-001] Criar o roteamento do Traefik em deploy/compose/compose.homolog.yml (rede externa e labels `ragpipeline-` só no frontend) — Refs: US-001, FR-002, NFR-001, NFR-003, AC-002, AC-004, AC-012 — Depends: T002, T004, T012
  - [x] **PREP**: Confirmar o RED TDD dos AC listados, reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE` e confirmar com a pessoa o nome da rede e do resolver, já respondidos como `n8n-dev-stack_traefik_net` e `mytlschallenge`. Documentação reconstruída por `build_documentation.mjs` e RED confirmado nos predecessores.
  - [x] **EXECUTE**: `deploy/compose/compose.homolog.yml` criado: rede externa `n8n-dev-stack_traefik_net`, labels `ragpipeline-*` só no frontend e `traefik.enable=false` nos demais.
  - [x] **VERIFY**: Testes de AC-002, AC-004 e AC-012 passam e `config -q` com os dois arquivos é válido.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (infraestrutura e scripts).
  - [x] **EVIDENCE**: GREEN: `uv run pytest tests/test_deploy_compose_*.py -q` verde (20 passed); `uv run ruff check` sem achados.
  - [x] **IMPROVE**: Resolver `mytlschallenge` e entrypoint `websecure` fixos, como no padrão confirmado; o `web` do redirect fica a conferir na VPS.
  <!-- specsfy:evidence {"task": "T022", "refs": ["US-001", "FR-002", "NFR-001", "NFR-003", "AC-002", "AC-004", "AC-012"], "files": ["deploy/compose/compose.homolog.yml"], "commands": [{"run": "uv run pytest tests/test_deploy_compose_*.py -q", "exit": 0}]} -->

- [x] T023 [CODE] [US-001] Criar o contrato de variáveis e segredos em deploy/compose/.env.example e .gitignore (nomes sem valores, `${VAR:?mensagem}`) — Refs: US-001, FR-003, NFR-001, NFR-003, AC-017, AC-018 — Depends: T017, T018, T021, T022
  - [x] **PREP**: Confirmar o RED TDD dos AC listados, reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE` e listar as variáveis obrigatórias do Swarm (`DOMINIO_RAGPIPELINE`, `QDRANT_URL`, `APP_COLECAO_PREFIXO`, `DATABASE_*`). Documentação reconstruída por `build_documentation.mjs` e RED confirmado nos predecessores.
  - [x] **EXECUTE**: `deploy/compose/.env.example` (só nomes) e `.gitignore` (`deploy/compose/segredos/`) criados; variáveis obrigatórias com `${VAR:?mensagem}`.
  - [x] **VERIFY**: Testes de AC-017 e AC-018 passam.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (infraestrutura e scripts).
  - [x] **EVIDENCE**: GREEN: `uv run pytest tests/test_deploy_compose_*.py -q` verde (20 passed); `uv run ruff check` sem achados.
  - [x] **IMPROVE**: O AC-005 passou para a T024, porque quem valida os segredos é o `deploy.sh`; plano corrigido.
  <!-- specsfy:evidence {"task": "T023", "refs": ["US-001", "FR-003", "NFR-001", "NFR-003", "AC-005", "AC-017", "AC-018"], "files": ["deploy/compose/.env.example", ".gitignore", "deploy/compose/compose.yml"], "commands": [{"run": "uv run pytest tests/test_deploy_compose_*.py -q", "exit": 0}]} -->

**Checkpoint**: os dois arquivos Compose validam com `docker compose config -q` e os testes de contrato passam sem tocar na VPS.

#### Fase 3 — US-002 Publicar uma versão com um comando e verificar de verdade (P1)

**Objetivo**: `make deploy` publica o `HEAD` com build, backup, migration e verificação.
**Teste independente**: `uv run pytest tests/test_deploy_compose_script.py tests/test_deploy_compose_runbook.py -q` com `ssh`, `git` e `docker` simulados.

- [x] T024 [CODE] [US-002] Implementar a publicação em deploy/compose/deploy.sh (config, SSH seguro, pré-requisitos, build, Postgres, backup, migração, `up --wait`) — Refs: US-002, FR-003, FR-004, FR-006, NFR-001, NFR-002, NFR-003, AC-005, AC-006, AC-007, AC-008, AC-009 — Depends: T005, T006, T007, T008, T009, T021, T022, T023
  - [x] **PREP**: Confirmar o RED TDD dos AC listados, reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE` e definir a ordem: validar, build, subir só o Postgres, backup quando houver dados, migrar, subir o conjunto. Documentação reconstruída por `build_documentation.mjs` e RED confirmado nos predecessores.
  - [x] **EXECUTE**: `deploy/compose/deploy.sh` criado: config 600, SSH seguro, pré-requisitos, build, Postgres, backup condicional, migração em container descartável e `up --wait`; `--versao` para o retorno.
  - [x] **VERIFY**: Testes de AC-005 a AC-009 passam com `ssh`, `git` e `docker` simulados.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (infraestrutura e scripts).
  - [x] **EVIDENCE**: GREEN: `uv run pytest tests/test_deploy_compose_*.py -q` verde (20 passed); `uv run ruff check` sem achados.
  - [x] **IMPROVE**: O `ssh` falso passou a executar o comando remoto como o real, e o log do `docker` registra `VERSAO_IMAGEM`, o que torna a asserção da versão mais forte.
  <!-- specsfy:evidence {"task": "T024", "refs": ["US-002", "FR-004", "FR-006", "NFR-002", "NFR-003", "AC-006", "AC-007", "AC-008", "AC-009"], "files": ["deploy/compose/deploy.sh"], "commands": [{"run": "uv run pytest tests/test_deploy_compose_*.py -q", "exit": 0}]} -->

- [x] T025 [CODE] [US-002] Criar os alvos de deploy em "./Makefile" na raiz (`deploy`, `deploy-config`, `deploy-logs`) — Refs: US-002, FR-005, NFR-003, AC-006, AC-007, AC-019 — Depends: T006, T007, T019, T024
  - [x] **PREP**: Confirmar o RED TDD dos AC listados, reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE` e conferir que não existe Makefile prévio na raiz. Documentação reconstruída por `build_documentation.mjs` e RED confirmado nos predecessores.
  - [x] **EXECUTE**: `./Makefile` criado com `deploy`, `deploy-config` e `deploy-logs`, sem comando destrutivo.
  - [x] **VERIFY**: Teste de AC-019 passa e `make -n deploy-logs` expande corretamente.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (infraestrutura e scripts).
  - [x] **EVIDENCE**: GREEN: `uv run pytest tests/test_deploy_compose_*.py -q` verde (20 passed); `uv run ruff check` sem achados.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: o Makefile só delega ao script e ao Compose.
  <!-- specsfy:evidence {"task": "T025", "refs": ["US-002", "FR-005", "NFR-003", "AC-006", "AC-007", "AC-019"], "files": ["Makefile"], "commands": [{"run": "uv run pytest tests/test_deploy_compose_*.py -q", "exit": 0}]} -->

- [x] T026 [P] [CODE] [US-002] Escrever o runbook de Compose em deploy/RUNBOOK_COMPOSE.md (primeira instalação, atualização, verificação, retorno e restauração) — Refs: US-002, FR-008, NFR-003, AC-014, AC-015, AC-016 — Depends: T014, T015, T016, T024
  - [x] **PREP**: Confirmar o RED TDD dos AC listados, reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE` e reunir os comandos exatos e os pontos que dependem de host, usuário, pasta e domínio, que ficam `Pendente`. Documentação reconstruída por `build_documentation.mjs` e RED confirmado nos predecessores.
  - [x] **EXECUTE**: `deploy/RUNBOOK_COMPOSE.md` criado: primeira instalação, atualização, verificação, retorno e restauração, sem segredos.
  - [x] **VERIFY**: Testes de AC-014, AC-015 e AC-016 passam.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (infraestrutura e scripts).
  - [x] **EVIDENCE**: GREEN: `uv run pytest tests/test_deploy_compose_*.py -q` verde (20 passed); `uv run ruff check` sem achados.
  - [x] **IMPROVE**: Valores de host, usuário, pasta, domínio e projeto permanecem `Pendente`, explícitos no texto.
  <!-- specsfy:evidence {"task": "T026", "refs": ["US-002", "FR-008", "NFR-003", "AC-014", "AC-015", "AC-016"], "files": ["deploy/RUNBOOK_COMPOSE.md"], "commands": [{"run": "uv run pytest tests/test_deploy_compose_*.py -q", "exit": 0}]} -->

**Checkpoint**: o `deploy.sh` simulado cobre o caminho feliz e as recusas, e o runbook leva da VPS vazia à verificação real.

#### Fase 4 — US-003 Manter o Swarm como opção de crescimento (P2)

**Objetivo**: o Swarm continua íntegro e compartilha imagens com o Compose.
**Teste independente**: `uv run pytest tests/test_deploy_compose_swarm.py -q`.

- [x] T027 [P] [CODE] [US-003] Registrar a convivência em deploy/RUNBOOK.md com um aviso para o caminho Compose, sem alterar nenhum passo do Swarm — Refs: US-003, FR-007, NFR-002, AC-010, AC-011, AC-013 — Depends: T010, T011, T013, T021
  - [x] **PREP**: Confirmar o RED TDD dos AC listados, reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE` e confirmar que `stack.prod.yml`, `secrets.sh` e `build_and_deploy.sh` ficam intactos. Documentação reconstruída por `build_documentation.mjs` e RED confirmado nos predecessores.
  - [x] **EXECUTE**: Aviso para `RUNBOOK_COMPOSE.md` acrescentado ao início de `deploy/RUNBOOK.md`, sem alterar passo do Swarm.
  - [x] **VERIFY**: Testes de AC-010, AC-011 e AC-013 passam; os hashes dos arquivos de Swarm não mudaram.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (infraestrutura e scripts).
  - [x] **EVIDENCE**: GREEN: `uv run pytest tests/test_deploy_compose_*.py -q` verde (20 passed); `uv run ruff check` sem achados.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: a mudança é uma nota.
  <!-- specsfy:evidence {"task": "T027", "refs": ["US-003", "FR-007", "NFR-002", "AC-010", "AC-011", "AC-013"], "files": ["deploy/RUNBOOK.md"], "commands": [{"run": "uv run pytest tests/test_deploy_compose_*.py -q", "exit": 0}]} -->

**Checkpoint**: nenhum arquivo de Swarm mudou de comportamento e os dois modos usam as mesmas imagens.

#### Fase final — Qualidade e contexto

- [x] T028 [P] [DOC] Registrar Docker Compose e Traefik como caminho de deploy em .specsfy/STACK.md — Refs: US-001, FR-001, FR-002 — Depends: T021, T022
  - [x] **PREP**: Ler o arquivo atual e preservar o conteúdo humano.
  - [x] **EXECUTE**: `.specsfy/STACK.md` recebeu três linhas: orquestração sem Swarm, acesso no caminho Compose e entrega no caminho Compose.
  - [x] **VERIFY**: Monitor de contexto `CURRENT`.
  - [x] **VISUAL**: Não aplicável: documento de contexto, sem superfície visual.
  - [x] **EVIDENCE**: Monitor `CURRENT` após a edição; trecho alterado conferido.
  - [x] **IMPROVE**: Nenhuma melhoria necessária.

- [x] T029 [P] [DOC] Registrar o Postgres em container e o volume `ragpipeline_postgres_data` em .specsfy/DATABASE.md — Refs: US-001, FR-006 — Depends: T021
  - [x] **PREP**: Ler o arquivo atual e preservar o conteúdo humano.
  - [x] **EXECUTE**: `.specsfy/DATABASE.md` recebeu a linha do Postgres em container com o volume `ragpipeline_postgres_data`.
  - [x] **VERIFY**: Monitor de contexto `CURRENT`.
  - [x] **VISUAL**: Não aplicável: documento de contexto, sem superfície visual.
  - [x] **EVIDENCE**: Monitor `CURRENT` após a edição; trecho alterado conferido.
  - [x] **IMPROVE**: Nenhuma melhoria necessária.

- [x] T030 [P] [DOC] Revisar PROJECT.md quanto ao deploy em Compose e registrar a conclusão — Refs: US-001, US-002, FR-004 — Depends: T024
  - [x] **PREP**: Ler o arquivo atual e preservar o conteúdo humano.
  - [x] **EXECUTE**: `PROJECT.md` recebeu um parágrafo sobre o deploy em Compose (SPEC-0045).
  - [x] **VERIFY**: Monitor de contexto `CURRENT`.
  - [x] **VISUAL**: Não aplicável: documento de contexto, sem superfície visual.
  - [x] **EVIDENCE**: Monitor `CURRENT` após a edição; trecho alterado conferido.
  - [x] **IMPROVE**: Nenhuma melhoria necessária.

- [x] T031 [TEST] Executar regressão e rastreabilidade em tests/test_deploy_compose_*.py e no repositório — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018, AC-019, AC-020 — Depends: T021, T022, T023, T024, T025, T026, T027, T028, T029, T030
  - [x] **PREP**: Identificar suites, `ruff` e a rastreabilidade.
  - [x] **EXECUTE**: Rodar `uv run pytest tests/test_deploy_compose_*.py -q`, `uv run ruff check .` e `check_traceability.mjs`.
  - [x] **VERIFY**: Suíte completa: 875 passed, 1 skipped, 2 failed; as duas falhas foram analisadas (ver EVIDENCE) e passam isoladas depois da correção.
  - [x] **VISUAL**: Não aplicável: nenhuma superfície visual.
  - [x] **EVIDENCE**: `uv run pytest` (2891 s): 875 passed. `test_spec_markers` reprovou por \"todo\" no texto da spec e foi corrigido; `test_llm_provider::test_chamada_ao_modelo_respeita_timeout_configurado` estourou 10,7 s contra 10 s sob carga e passa isolado (não toca nesta mudança). `ruff check` limpo; `check_traceability.mjs --full-chain` 34/34; `build_documentation.mjs --check` exit 0.
  - [x] **IMPROVE**: Evitar \"todo\" em português nas specs, por causa do falso positivo do validador; teste de timeout sensível a carga fica registrado como risco conhecido.

### 15. Ordem de execução

- Caminho crítico: T001–T020 (RED) → T021/T022 → T023 → T024 → T025 e T026 → T031.
- Tarefas paralelas: T021 e T022 (arquivos distintos), T026 e T027 (documentos distintos) e T028, T029 e T030 (documentos de contexto distintos). Os testes de arquivos diferentes podem ser escritos em paralelo, mas não levam `[P]` por compartilharem o arquivo do grupo.
- Estratégia de MVP: US-001 (Fase 2) e US-002 (Fase 3) formam o primeiro deploy; US-003 preserva o Swarm e entra em seguida.
- O deploy real na VPS, que fecha a T020 da SPEC-0041 e a T027 da SPEC-0032, fica fora desta spec e exige autorização específica.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Traefik compartilhado e rede `n8n-dev-stack_traefik_net` na VPS de destino; DNS do domínio apontando para a VPS; acesso de leitura do servidor ao Git (deploy key); Qdrant publicado, R2 e OpenRouter disponíveis.

#### Riscos

- `read_only` pode quebrar o LibreOffice ou o OCR → `tmpfs` em `/app/.config` e `/app/.cache` e teste real de conversão antes de aceitar.
- `cap_drop: [ALL]` impede a inicialização do Postgres → `cap_add` mínimo (`CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `SETGID`, `SETUID`) só nele.
- Nome `compose.yml` na raiz sobrescreveria o `docker-compose.yml` de teste → arquivos em `deploy/compose/`.
- Frontend embute `API_PROXY_TARGET` → mesmos nomes de serviço do Swarm.
- Migration falha depois do backup → a versão nova não sobe; restauração por `deploy/BACKUP.md`.
- `mem_limit` mal calibrado causa OOM → valores medidos no ensaio.

#### Suposições

- A VPS de destino tem Docker Compose v2, Git e o usuário `deploy` com acesso ao Docker.
- O mesmo `.env` com nomes de variáveis do Swarm (`DOMINIO_RAGPIPELINE`, `QDRANT_URL`, `APP_COLECAO_PREFIXO`) vale no Compose.
- O Postgres em container é a imagem `postgres:16.10-alpine3.22`, igual à usada pelo backup.

### 17. Decisões

- **DEC-001**: Compose agora, Swarm como opção futura — a VPS de destino não tem Swarm; a manutenção dos arquivos custa pouco.
- **DEC-002**: arquivos em `deploy/compose/`, não na raiz — evita colidir com o `docker-compose.yml` de teste; trade-off: o comando leva `-f` explícito.
- **DEC-003**: mesmos nomes de serviço, Dockerfiles e etiquetas do Swarm — a imagem do frontend embute o destino da API.
- **DEC-004**: segredos como arquivos montados em `/run/secrets` — o comando do backend fica idêntico nos dois modos.
- **DEC-005**: migrations pelo `deploy.sh`, depois do backup — mantém a regra do runbook atual.
- **DEC-006**: hardening completo com `tmpfs` — padrão do factory; exceção documentada para o Postgres.
- **DEC-007**: uploads no R2 e backup atual mantido — reaproveita o que o Swarm já usa.
- **DEC-008**: SPEC-0041 e SPEC-0032 ficam como estão; T020 e T027 serão fechadas pelo deploy em Compose.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/STACK.md` revisado para registrar Docker Compose e Traefik como caminho de deploy.
- [x] `.specsfy/DATABASE.md` revisado: o Postgres passa a rodar em container com o volume `ragpipeline_postgres_data`.
- [x] `PROJECT.md` revisado (deploy em Compose) ou justificativa de ausência de impacto registrada.
- [x] `.specsfy/RULES.md` revisado se alguma regra nova for confirmada pela pessoa.
- [x] `INTERFACE.md`: sem impacto, a entrega não tem interface.
