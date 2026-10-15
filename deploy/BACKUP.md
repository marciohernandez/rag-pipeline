# Backup do PostgreSQL

O serviço `backup_ragpipeline` executa às **03:00 UTC**, com a aplicação no ar.
O destino é um bucket Cloudflare R2 exclusivo para backup, com credencial
própria. Não cobre os vetores do Qdrant nem os arquivos já guardados no R2.
A retenção guarda **7 diários** e **4 semanais** (cópia aos domingos).

## Guardar a chave

Crie uma chave longa e aleatória no gerenciador de senhas da pessoa responsável,
**fora da VPS**. Guarde a identificação da chave e as datas em que foi usada.
Forneça uma cópia ao secret `backup_chave`; o provisionador não a exibe.
**Sem a chave, o backup não pode ser restaurado.** Preserve chaves anteriores
enquanto houver objetos cifrados com elas. A troca não recifra os objetos.

## Configurar

Execute `deploy/secrets.sh criar` em um manager para completar os ausentes.
Veja [SECRETS.md](SECRETS.md). Os três secrets de backup são versionados:

| Secret | Campos pedidos, na ordem | Uso |
| --- | --- | --- |
| `backup_chave` | Chave fornecida pela pessoa | AES-256-CBC, salt aleatório, PBKDF2 do OpenSSL |
| `backup_r2_credentials` | `BACKUP_BUCKET`, `R2_ENDPOINT`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Bucket separado, endpoint HTTPS sem autenticação na URL; permissão de listar, ler, gravar e excluir só nesse bucket |
| `backup_avisos` | `SMTP_URL`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TO`, `WEBHOOK_URL` | SMTP com STARTTLS ou SMTPS e webhook HTTPS que aceite JSON `{"text":"mensagem"}` |

Os arquivos de configuração são pares `KEY=valor` literais, um por linha,
sem aspas shell, expansão nem execução. Não coloque secrets em argumentos,
arquivos versionados ou variáveis do stack. SMTP e webhook entram no curl
pela entrada padrão. O log omite stderr dos clientes para evitar repetir
credenciais retornadas por serviços externos.

`deploy/build_and_deploy.sh` verifica e resolve as versões antes dos builds.
A imagem é construída no nó de dados. Quando ele difere do nó de aplicação,
configure um Docker context para esse servidor e exporte
`BACKUP_DOCKER_CONTEXT`; o script confere o hostname antes de construir.
Construir a imagem não distribui imagens aos outros nós do Swarm.

| Variável | Padrão | Efeito |
| --- | --- | --- |
| `BACKUP_HORA` | `03:00` | Janela diária em UTC, formato HH:MM |
| `BACKUP_TIMEOUT_SEGUNDOS` | `3600` | Limite do ciclo inteiro; TERM, seguido de KILL após 90 s para limpeza e avisos |
| `BACKUP_MIN_BYTES` | `1024` | Dump deve superar esse tamanho |
| `BACKUP_TENTATIVAS` | `3` | Tentativas de envio ao armazenamento |
| `BACKUP_ESPERA_SEGUNDOS` | `5` | Espera entre tentativas, multiplicada pelo número da tentativa |

O serviço roda sem root, sem porta publicada e sem volume de dump. Secrets
somente nos serviços que precisam deles. O diretório temporário tem permissão
privada e é removido no encerramento, inclusive em falha tratável. KILL ou perda
do host não executam traps; o diretório é efêmero no contêiner, sem volume.

## Ciclo manual e logs

No nó de dados, localize o contêiner e execute um ciclo manual:

```bash
docker ps --filter name=backup_ragpipeline --format '{{.ID}}'
docker exec <id-do-container> bash /backup/backup.sh
docker service logs --since 24h rag-pipeline_backup_ragpipeline
```

Cada etapa registra início, fim e resultado; a última linha é `RESUMO`.
Sucesso informa data, objetos, bytes e retenção, sem enviar avisos.
Objetos diários: `diarios/AAAA-MM-DD.dump.enc`; semanais:
`semanais/AAAA-SWW.dump.enc` (ano e semana ISO).

O dump custom é cifrado e validado localmente, enviado a uma chave provisória
`pendentes/`, baixado e conferido por tamanho, SHA-256, decifragem e
`pg_restore --list`. Só depois é publicado e aplicada a retenção. A chave
provisória é removida ao encerrar. Uma interrupção abrupta pode deixar um
objeto provisório cifrado; ele não entra na retenção de backups. Repetir no
mesmo dia substitui o objeto diário e não aumenta a contagem.

## Avisos e resposta a falhas

Uma falha retorna código não zero e tenta e-mail e chat independentemente.
Os avisos contêm a etapa, sem chave, senha, token ou URL autenticada.

| Etapa | Conferir e corrigir |
| --- | --- |
| `configurar` | Secrets presentes e não vazios; endpoint e bucket válidos |
| `dump` | Conectividade e credencial do Postgres, espaço temporário e tempo do job |
| `cifrar` | Arquivo da chave, OpenSSL e espaço temporário |
| `enviar` | Rede, endpoint, bucket, permissões e limites do armazenamento |
| `verificar` | Tamanho mínimo, integridade do dump, chave e objeto baixado; não aplicar retenção manualmente |
| `reter` | Permissões de listar e excluir no bucket; confira quais objetos continuam disponíveis |
| aviso por e-mail | SMTP, STARTTLS/SMTPS, autenticação e destinatário |
| aviso por webhook | URL, autenticação embutida na URL do webhook e resposta HTTP do chat |

Após corrigir, execute o ciclo manual e confira `RESUMO resultado=sucesso`.
O agendador continua para a próxima janela mesmo depois de um ciclo falho.

## Restaurar e conferir

Use um servidor **temporário e separado**. Nunca aponte a restauração para o
servidor de desenvolvimento ou de teste usado pelas suítes. Nunca restaure
sobre um banco existente. O script cria um **banco temporário novo**; não usa
opções de limpeza nem apaga estruturas. Ele recusa nomes já existentes.

1. Escolha o objeto e a chave correspondente guardada fora da VPS.
2. Monte a chave, o arquivo de credenciais do bucket e o arquivo de senha do
   Postgres como arquivos privados no contêiner. `BACKUP_SECRETS_DIR` aponta
   para a pasta com `postgres_password`. `PGUSER` define o usuário do destino
   (padrão `rag_pipeline`), que precisa poder criar bancos. Não forneça a senha
   em argumento. `--destino` aceita somente `host:porta`, sem usuário ou senha.
3. Execute na imagem de backup com acesso ao servidor temporário:

```bash
bash /backup/restaurar.sh diarios/AAAA-MM-DD.dump.enc \
  --destino postgres-temporario:5432 \
  --chave-arquivo /run/secrets/backup_chave \
  --credenciais-arquivo /run/secrets/backup_r2_credentials
```

O nome padrão é `restauracao_AAAAMMDDHHMMSS` UTC. Opcionalmente, `--banco`
aceita identificador simples novo (letras minúsculas, números e underscore,
iniciando por letra, até 63 caracteres). Colisão de nomes retorna falha.
Objeto ausente ou chave errada é recusado antes de criar banco.

4. Confira tabelas e registros no banco informado usando `psql` com a senha
   via arquivo/ambiente privado. Compare contagens e registros conhecidos.
   `pg_restore --list` valida o catálogo, mas não substitui esta conferência.
5. Só após conferir o conteúdo, planeje separadamente a troca da aplicação
   para o banco recuperado. Este script não promove bancos. Se a restauração
   falhar depois da criação, o banco novo parcial permanece para diagnóstico;
   repita com outro nome novo.

## Ensaio local

```bash
bash deploy/backup/ensaio.sh
```

O ensaio cria uma rede isolada, Postgres temporário, S3 simulado com Moto 5.1.15 e coletor de
SMTP/webhook sem portas publicadas. Usa apenas valores fictícios, valida o
ciclo, restaura e confere um registro conhecido, injeta uma falha e confirma
os dois avisos. Remove somente os próprios contêineres, rede e arquivos
temporários ao encerrar, sem usar o banco de desenvolvimento.

Para ensaiar o stack inteiro já existente, o override `stack.local.yml`
acrescenta `s3_local_ragpipeline` e `avisos_local_ragpipeline`. Provisione
os secrets locais com `deploy/secrets.sh criar --ambiente local`, resolva
suas versões e crie o bucket `rag-backup-local` usando a CLI da imagem
e as credenciais fictícias do secret. O override não deve ser usado na VPS.
`BACKUP_SMTP_TLS=0` existe somente para SMTP do coletor isolado; produção
mantém TLS obrigatório. O S3 local não tem volume persistente: é descartável.

## Verificação real na VPS, após o deploy

A pessoa responsável executa esta conferência depois de aceitar o ensaio
local. Ela fica fora do Delivery Gate desta spec:

1. Provisione bucket separado no R2, credencial limitada a ele e os secrets.
2. Execute um ciclo manual e confira log, objeto, tamanho e horário.
3. Baixe o objeto e ensaie a restauração em servidor temporário próprio.
4. Provoque uma falha controlada somente no serviço de backup e confira a
   chegada real do e-mail e do chat; restaure sua configuração em seguida.
5. Confira a execução automática às 03:00 UTC e o crescimento da retenção
   até 7 diários e 4 semanais. Guarde a chave fora da VPS.

A ordem do deploy, a volta atrás e a restauração em emergência estão em [RUNBOOK.md](RUNBOOK.md).
