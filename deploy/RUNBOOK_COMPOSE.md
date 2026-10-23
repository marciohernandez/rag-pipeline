# Runbook de deploy em Compose

Passo a passo para publicar o Beta numa VPS **sem Swarm**, com Docker Compose e o Traefik
compartilhado (SPEC-0045). O caminho do Swarm continua em [RUNBOOK.md](RUNBOOK.md); as
imagens, os nomes de serviço e os nomes dos secrets são os mesmos, então a troca futura
muda só o orquestrador.

Nada aqui contém segredo, chave, domínio ou endereço real. Quem decide quando publicar é a
pessoa responsável; o deploy só roda com a autorização dela. Compose, Traefik, a rede
`n8n-dev-stack_traefik_net` e os outros projetos da VPS pertencem a outros stacks: **nunca**
os crie, altere ou remova daqui. Se algo exigir isso, pare e pergunte.

Valores ainda `Pendente`, a informar antes do primeiro deploy: host, usuário, pasta, domínio
e nome do projeto Compose (a sugestão é `ragpipeline`).

## Como funciona

| Peça | Onde fica |
| --- | --- |
| Compose base e roteamento | `deploy/compose/compose.yml` e `deploy/compose/compose.homolog.yml` |
| Script de publicação | `deploy/compose/deploy.sh`, chamado por `make deploy` |
| Variáveis não secretas | `.env` na pasta do projeto no servidor (permissão 600) |
| Segredos | arquivos 600 numa pasta do servidor fora do Git (`SEGREDOS_DIR`) |
| Banco | container `postgres_ragpipeline`, volume `ragpipeline_postgres_data`, sem porta publicada |
| Qdrant e uploads | Qdrant publicado (prefixo `beta-`) e Cloudflare R2 |

O comando Compose é sempre o mesmo, com projeto próprio e os dois arquivos:

```bash
docker compose -p ragpipeline --env-file .env \
  -f deploy/compose/compose.yml -f deploy/compose/compose.homolog.yml <subcomando>
```

## Primeira instalação

Faça cada passo como o usuário `deploy` (nunca root). Troque os valores `<...>`.

1. **Acesso do servidor ao Git.** Em repositório privado, gere uma *deploy key* somente
   leitura no servidor, cadastre a chave pública no repositório e confira:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/ragpipeline_deploy_key -N '' -C ragpipeline-deploy-key
cat ~/.ssh/ragpipeline_deploy_key.pub     # cadastre como deploy key somente leitura
git ls-remote <url-do-repositorio>         # precisa listar as referências sem pedir senha
```

2. **Pastas, repositório e `.env`.**

```bash
mkdir -p ~/ragpipeline/segredos && chmod 700 ~/ragpipeline/segredos
git clone <url-do-repositorio> ~/ragpipeline/app
cd ~/ragpipeline/app
cp deploy/compose/.env.example .env && chmod 600 .env
nano .env     # preencha DOMINIO_RAGPIPELINE, QDRANT_URL, SEGREDOS_DIR e APP_COLECAO_PREFIXO
```

3. **Segredos.** Um arquivo por nome, com `chmod 600`, lendo cada valor sem eco. Os
   formatos são os dos secrets do Swarm (ver [SECRETS.md](SECRETS.md) e
   `deploy/secrets.sh`): `openrouter_api_key`, `qdrant_api_key`, `postgres_password` e
   `backup_chave` guardam um valor puro; `conexoes_chave` é uma chave Fernet;
   `r2_credentials`, `backup_r2_credentials` e `backup_avisos` guardam linhas `CAMPO=valor`.

```bash
cd ~/ragpipeline/segredos
read -rs V && printf '%s' "$V" > openrouter_api_key && unset V && chmod 600 openrouter_api_key
# repita para os demais; a senha do Postgres nasce aqui e só vale na primeira subida
python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' \
  > conexoes_chave && chmod 600 conexoes_chave
ls -l ~/ragpipeline/segredos    # todos precisam aparecer como -rw-------
```

   Guarde `backup_chave` num gerenciador de senhas **fora da VPS**: sem ela o backup não
   pode ser restaurado. A senha do Postgres é aplicada na criação do volume; trocá-la depois
   exige alterar a senha dentro do banco.

4. **`known_hosts` na máquina de quem publica.** O deploy usa
   `StrictHostKeyChecking=yes`: registre o servidor uma única vez, conferindo a impressão
   digital por outro canal.

```bash
ssh-keyscan -H <host> >> ~/.ssh/known_hosts
ssh-keygen -lf <(ssh-keyscan <host> 2>/dev/null)    # compare com a impressão digital do servidor
```

5. **DNS.** Aponte o registro do domínio para o IP da VPS e confirme antes do deploy; o
   certificado só é emitido se o DNS já resolver:

```bash
dig +short <dominio>     # precisa devolver o IP da VPS
```

6. **Configuração de deploy (`DEPLOY_CONFIG`).** Um arquivo shell **fora do repositório**,
   com permissão 600, na máquina de quem publica:

```bash
cat > ~/.config/ragpipeline-deploy.conf <<'CONF'
DEPLOY_HOST=<host>
DEPLOY_USER=deploy
DEPLOY_KEY=<caminho-da-chave-ssh-privada>
DEPLOY_PATH=/home/deploy/ragpipeline/app
# DEPLOY_PORT=22
# DEPLOY_REPOSITORY=origin
CONF
chmod 600 ~/.config/ragpipeline-deploy.conf
export DEPLOY_CONFIG=~/.config/ragpipeline-deploy.conf
```

7. **Traefik e rede.** Confirme que a rede existe (somente leitura) e que o resolver
   `mytlschallenge` e os pontos de entrada `web` e `websecure` existem no Traefik:

```bash
docker network inspect n8n-dev-stack_traefik_net > /dev/null && echo rede-ok
```

8. **Publicar.** O commit `HEAD` precisa estar no remoto:

```bash
git push
make deploy
```

   Na primeira vez o banco ainda não existe: o backup é dispensado e a migração cria todo o
   schema, inclusive a fila Procrastinate.

## Atualizar

1. `git push` do commit a publicar (o script recusa árvore suja e commit fora do remoto).
2. Confirme que nenhum lote está em andamento (conversão, ingestão ou análise).
3. `make deploy`. O script, no servidor, valida os pré-requisitos, faz o checkout do commit,
   constrói as imagens, sobe o Postgres, faz um backup quando já há dados, aplica as
   migrations em container descartável e só então sobe o conjunto com `--wait`.
4. Se o build ou a migração falhar, a versão nova não sobe e os serviços atuais continuam.
5. Confirme com a seção Verificação.

## Verificação

Container saudável não prova DNS nem HTTPS. Confira tudo:

```bash
docker compose -p ragpipeline --env-file .env \
  -f deploy/compose/compose.yml -f deploy/compose/compose.homolog.yml ps   # todos healthy
curl -I https://<dominio>        # HTTP 200 por HTTPS, com HSTS
curl -I http://<dominio>         # 301 ou 308 redirecionando para https
echo | openssl s_client -connect <dominio>:443 -servername <dominio> 2>/dev/null \
  | openssl x509 -noout -issuer -dates      # certificado emitido e dentro da validade
make deploy-logs                 # sem erro nos logs recentes
```

Depois, no navegador: entre com uma conta de teste e envie uma pergunta ao assistente. Na
primeira instalação, percorra a lista completa: login, criar uma Pessoa, subir uma Base e
conversar com o assistente. Envie também um DOC, PPT ou XLS e uma imagem para confirmar que
a conversão e o OCR funcionam com o sistema de arquivos somente leitura.

Se a verificação reprovar, siga o Retorno.

## Retorno

Volte à versão anterior sem construir nada. As imagens anteriores continuam no servidor,
etiquetadas pelo commit curto:

```bash
docker image ls rag-pipeline-backend      # etiquetas disponíveis
bash deploy/compose/deploy.sh --versao <etiqueta-anterior>
```

O retorno sem construir só reimplanta as imagens existentes: não aplica migration, não apaga
o volume `ragpipeline_postgres_data` e nunca `down -v`. Se a migração da versão nova afetou
os dados, restaure o backup (próxima seção) antes de decidir.

## Restauração do backup

O backup cifrado e enviado ao R2 é o mesmo da SPEC-0034 e roda no serviço
`backup_ragpipeline`, agora apontando para o container `postgres_ragpipeline`. A
restauração **cria um banco novo e nunca restaura sobre um existente**; siga
[BACKUP.md](BACKUP.md) e confira o conteúdo antes de trocar a aplicação para o banco
recuperado. Para um ciclo manual:

```bash
docker compose -p ragpipeline --env-file .env \
  -f deploy/compose/compose.yml -f deploy/compose/compose.homolog.yml \
  exec -T backup_ragpipeline bash /backup/backup.sh
```

## Migrar para o Swarm depois

Quando o projeto crescer, use [RUNBOOK.md](RUNBOOK.md): os mesmos Dockerfiles, etiquetas e
nomes de serviço valem, e os secrets mantêm os nomes lógicos. A decisão de Postgres externo
ou em container no Swarm é uma spec própria.
