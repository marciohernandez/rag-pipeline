# Runbook de deploy manual em produção

Passo a passo para atualizar o Beta, instalá-lo pela primeira vez e agir numa
emergência (SPEC-0035). O deploy é manual: **só a pessoa responsável** o faz, por
acesso remoto à VPS, em um nó manager do Swarm. Nenhum segredo, chave, endereço de
bucket nem domínio real entra neste documento; o domínio vem da variável
`DOMINIO_RAGPIPELINE` e os valores secretos vêm do gerenciador de senhas.

> Este runbook cobre o deploy em **Docker Swarm**. Numa VPS sem Swarm, com Compose e o
> Traefik compartilhado, use [RUNBOOK_COMPOSE.md](RUNBOOK_COMPOSE.md) (SPEC-0045); as imagens
> e os nomes de serviço são os mesmos.

Documentos ligados a este: [SECRETS.md](SECRETS.md) (secrets e domínio) e
[BACKUP.md](BACKUP.md) (backup, chave e restauração).

**Delegar o deploy** a outra pessoa exige antes: dar os acessos à VPS e ao Docker,
repassar as chaves guardadas fora da VPS e manter um registro de deploys. Nada disso
existe hoje; fica apenas marcado aqui.

## Atualizar a produção

Use esta área a cada versão nova. A ordem importa: não pule passos.

### Pré-condições

1. No repositório, no commit que será implantado, confirme **Ruff**, **Pytest** e o
   **build do frontend** verdes. O CI do pull request mergeado já os executa.
2. Confirme que o repositório na VPS está limpo e no commit certo (`git status`,
   `git log -1`). O script recusa árvore com alterações não commitadas.
3. Confirme que **nenhum lote está em andamento** (conversão, ingestão ou análise).
   Conte as execuções `pending` e `running` no Postgres externo; o resultado precisa ser
   zero. A consulta é somente de leitura e usa o `psql` com a senha digitada, sem eco:

```bash
read -rs PGPASSWORD && export PGPASSWORD
psql "host=$DATABASE_HOST port=${DATABASE_PORT:-5432} dbname=${DATABASE_NAME:-postgres} user=$DATABASE_USER sslmode=${DATABASE_SSLMODE:-require}" \
  -c "SELECT count(*) FROM executions WHERE situacao IN ('pending', 'running');"
```

4. Se o resultado não for zero, **espere** os lotes terminarem e repita a consulta. Não
   siga com lote em andamento.

### Backup recente

1. Confirme o último backup no log do serviço (veja [BACKUP.md](BACKUP.md)):

```bash
docker service logs --since 24h rag-pipeline_backup_ragpipeline
```

2. A última linha `RESUMO` precisa dizer `resultado=sucesso`. Sem backup das últimas
   24 horas, execute um ciclo manual no nó de dados e confira o resultado antes de
   seguir:

```bash
docker exec "$(docker ps -q --filter name=backup_ragpipeline)" bash /backup/backup.sh
```

### Migração do banco

Só há migração quando a versão traz um arquivo novo em `alembic/versions/`. O serviço
não migra sozinho: a migração é um passo manual, **depois do backup** e **antes do
deploy**.

O aviso "Banco não migrado" na subida do backend ou worker indica migração pendente:
execute `alembic upgrade head` pelo procedimento abaixo antes de reiniciar os serviços.
O Alembic prepara tanto as tabelas do app quanto o schema da fila Procrastinate;
os serviços apenas verificam a versão e nunca criam tabelas na subida.

**Adoção única de banco legado criado pelo `create_all`:** depois do backup,
confira que o schema do app **e o da fila Procrastinate estão completos** e
correspondem a todas as migrations desta versão. Somente depois dessa conferência,
execute `alembic stamp head` usando o mesmo serviço descartável e as mesmas
variáveis e secrets do passo 2, substituindo o comando final. O stamp apenas
registra a versão: não cria nem corrige estruturas ausentes, inclusive as da fila.
Depois siga o upgrade normal abaixo. Banco incompleto precisa ter suas divergências
resolvidas antes da adoção; não marque como migrado um schema incompleto.

1. Descubra o secret vigente da senha do banco e construa a imagem da versão nova sem
   implantar (o deploy reaproveita o cache):

```bash
deploy/secrets.sh resolver
docker build -f deploy/backend/Dockerfile -t "rag-pipeline-backend:$(git rev-parse --short HEAD)" .
```

2. Rode a migração (`alembic upgrade head`) contra o Postgres externo como um serviço
   descartável do Swarm. O host, o usuário e o banco entram como variáveis; a senha entra
   pelo secret (`source` é a versão vigente impressa por `deploy/secrets.sh resolver`),
   nunca pela linha de comando:

```bash
docker service create --name migracao-ragpipeline --restart-condition none \
  --network network_swarm_public --constraint "node.hostname==$APPLICATION_NODE_HOSTNAME" \
  --secret source=postgres_password_v1,target=postgres_password \
  --env DATABASE_HOST --env DATABASE_USER --env DATABASE_NAME="${DATABASE_NAME:-postgres}" \
  --env DATABASE_PORT="${DATABASE_PORT:-5432}" --env DATABASE_SSLMODE="${DATABASE_SSLMODE:-require}" \
  "rag-pipeline-backend:$(git rev-parse --short HEAD)" /bin/sh -ec \
  'export APP_DATABASE_URL="$(python -c "import os; from pathlib import Path; from urllib.parse import quote; e = os.environ; print(\"postgresql+psycopg://{}:{}@{}:{}/{}?sslmode={}\".format(quote(e[\"DATABASE_USER\"], safe=\"\"), quote(Path(\"/run/secrets/postgres_password\").read_text().strip(), safe=\"\"), e[\"DATABASE_HOST\"], e[\"DATABASE_PORT\"], e[\"DATABASE_NAME\"], e[\"DATABASE_SSLMODE\"]))")"; exec alembic upgrade head'
docker service logs migracao-ragpipeline
docker service rm migracao-ragpipeline
```

3. Troque `postgres_password_v1` pela versão que o `resolver` imprimiu. O log precisa
   terminar sem erro. **Se a migração falhar, não atualize o serviço**: a aplicação
   continua na versão anterior. Avalie o erro e, se o banco foi afetado, restaure o
   backup feito antes (área Emergências).

### Deploy

1. Exporte o domínio, o Postgres externo, o Qdrant externo e o nó onde o backup roda, e
   rode o script (veja [SECRETS.md](SECRETS.md)). O script recusa o deploy, antes de
   qualquer build, se faltar `DATABASE_HOST`, `DATABASE_USER` ou `QDRANT_URL`:

```bash
export DOMINIO_RAGPIPELINE
export DATABASE_HOST DATABASE_USER   # Postgres externo; DATABASE_PORT, DATABASE_NAME e
                                     # DATABASE_SSLMODE têm padrão (5432, postgres, require)
export QDRANT_URL                    # Qdrant externo
export APP_COLECAO_PREFIXO           # prefixo das coleções do sistema (por exemplo, beta-)
export DATABASE_NODE_HOSTNAME        # nó onde o serviço de backup roda
deploy/build_and_deploy.sh
```

2. O script confere os secrets antes de qualquer build, etiqueta as imagens pelo commit
   curto (informado na saída como `Versão das imagens`), implanta o stack e, só depois
   de um deploy bem-sucedido, guarda as três versões mais recentes de cada imagem e
   apaga as mais antigas. Anote a versão implantada.

### Verificação

1. Confira o domínio, o certificado, o redirecionamento e o HSTS:

```bash
deploy/conferir_dominio.sh
```

2. Faça a checagem rápida: entre com uma conta de teste (login) e envie uma pergunta ao
   assistente.
3. A **lista completa** (login, criar uma Pessoa, subir uma Base e conversar com o
   assistente) vale na **primeira instalação** e depois de **mudança grande**.
4. Se a verificação reprovar, vá para a área Emergências e volte à versão anterior.

## Primeira instalação

1. Crie os secrets, que o script pede sem eco. O valor entra pela entrada padrão do
   Docker e nunca por argumento:

```bash
deploy/secrets.sh criar
deploy/secrets.sh verificar
```

2. Aponte o domínio para a VPS e confirme que o Traefik compartilhado já existe
   (veja [SECRETS.md](SECRETS.md)). Exporte a variável `DOMINIO_RAGPIPELINE`; o DNS e o
   certificado são conferidos depois do deploy.
3. Guarde a chave do backup (`backup_chave`) no gerenciador de senhas, fora da VPS, e
   leia [BACKUP.md](BACKUP.md). Sem a chave, o backup não pode ser restaurado.
4. Faça a migração do banco externo novo com o serviço descartável descrito na área
   Atualizar a produção. O banco ainda não tem tabelas, então `alembic upgrade head`
   cria todas, incluindo a fila Procrastinate, em um único comando.
5. Rode o deploy e a verificação (com as variáveis exportadas como descrito em Deploy):

```bash
deploy/build_and_deploy.sh
deploy/conferir_dominio.sh
```

6. Percorra a **lista completa**: entre com o owner, crie uma Pessoa, suba uma Base e
   converse com o assistente. Essa lista é a condição de saída do M03.
7. Confira o primeiro ciclo do backup conforme a seção de verificação real em
   [BACKUP.md](BACKUP.md).

## Emergências

1. **Voltar à versão anterior** (verificação reprovada ou erro depois do deploy). As
   imagens das três últimas versões continuam no nó; reimplante a anterior sem
   construir nada:

```bash
deploy/build_and_deploy.sh --versao <etiqueta-anterior>
```

   Se a etiqueta não existir, o script recusa e lista as versões disponíveis.
2. **Comando de emergência do Swarm**, se o script não puder rodar: devolve um serviço
   à especificação anterior.

```bash
docker service rollback rag-pipeline_backend_ragpipeline
```

   Repita para `frontend_ragpipeline` e `worker_ragpipeline`.
3. **Restaurar o banco** quando a migração ou o deploy afetou os dados. Use o último
   backup e siga `deploy/BACKUP.md`: `restaurar.sh` cria um **banco novo** e nunca
   restaura sobre um existente. Confira o conteúdo antes de trocar a aplicação para o
   banco recuperado.
4. Nunca use comando que apague, recrie ou zere banco, schema ou volume como rotina.
5. Depois da emergência, registre o que aconteceu e só tente de novo com uma versão
   que passou na verificação.
