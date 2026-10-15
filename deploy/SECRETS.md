# Secrets de produção do Swarm

Guia de uso de `deploy/secrets.sh` (SPEC-0027). O script cria, confere e troca os
secrets que a stack de produção lê em `/run/secrets/*`. Ele roda **no nó manager do
Swarm**, com a CLI do Docker, e é operado manualmente.

## Testar localmente antes da VPS

O ensaio da SPEC-0032 está disponível em `http://localhost:3300`, com imagens
construídas pelos Dockerfiles de produção e dados fictícios em volumes próprios.
O stack local anterior continua separado. Embeddings são simulados; respostas
reais de IA e certificado público continuam dependendo de validação posterior.
Credenciais de teste foram entregues na conversa e não são secrets de produção.

Para consultar, parar ou retomar o ambiente preparado:

```bash
docker compose --env-file /tmp/rag-0032-ensaio/empty.env -f /tmp/rag-0032-ensaio/compose.yml ps
docker compose --env-file /tmp/rag-0032-ensaio/empty.env -f /tmp/rag-0032-ensaio/compose.yml stop
docker compose --env-file /tmp/rag-0032-ensaio/empty.env -f /tmp/rag-0032-ensaio/compose.yml start
```

Esses comandos preservam os volumes. A configuração, certificados locais e
fixtures são temporários em `/tmp/rag-0032-ensaio/`; se removidos, será necessário
prepará-los novamente antes de usar os comandos. Os resultados e limites do ensaio
estão na seção 13 da SPEC-0032. A pessoa responsável decide quando publicar na VPS
após aceitar os testes locais.

## O que existe

| Secret | Origem do valor | Para que serve |
| --- | --- | --- |
| `openrouter_api_key` | você informa, sem eco | chave da OpenRouter (embeddings e assistente) |
| `r2_credentials` | você informa bucket, endpoint, access key e secret key, sem eco | armazenamento Cloudflare R2 dos uploads |
| `postgres_password` | gerado pelo script | senha do usuário `rag_pipeline` do Postgres |
| `conexoes_chave` | gerado pelo script (chave Fernet) | cifra as chaves das conexões de ingestão |
| `backup_chave` | você informa e guarda fora da VPS, sem eco | cifra os dumps PostgreSQL |
| `backup_r2_credentials` | você informa os campos do bucket separado, sem eco | armazenamento exclusivo dos backups |
| `backup_avisos` | você informa SMTP e webhook, sem eco | avisos de falha do backup |

O `session_secret` deixou de existir: nada no código o usa desde a autenticação por
pessoa e sessão (SPEC-0020).

## Convenção de nomes

Um secret do Swarm não pode ser editado. Por isso cada valor vive em uma versão:

- produção: `<nome>_v<N>`, por exemplo `openrouter_api_key_v1` e `openrouter_api_key_v2`;
- ensaio local: `<nome>_local_v<N>`, por exemplo `openrouter_api_key_local_v1`.

A versão vigente é a de maior `N`. `deploy/build_and_deploy.sh` descobre essas versões e
as entrega ao stack pelas variáveis `OPENROUTER_API_KEY_SECRET`, `R2_CREDENTIALS_SECRET`,
`POSTGRES_PASSWORD_SECRET`, `CONEXOES_CHAVE_SECRET`, `BACKUP_CHAVE_SECRET`,
`BACKUP_R2_CREDENTIALS_SECRET` e `BACKUP_AVISOS_SECRET`.
Sem a variável, o stack usa `_v1`.

## Primeira instalação

```bash
deploy/secrets.sh criar
```

- Pede, sem eco, a chave da OpenRouter e os campos do R2.
- Pede, sem eco, a chave do backup, os campos do bucket de backup e dos avisos.
- Gera `postgres_password` e `conexoes_chave` e **mostra cada valor uma única vez**, em
  uma linha `VALOR GERADO <secret>: <valor>`. **Guarde-o agora no gerenciador de senhas**:
  não há como lê-lo de novo no Swarm.
- Nunca sobrescreve: se algum secret já existir, ele é preservado e só os ausentes são
  criados. Uma criação interrompida pode ser retomada repetindo o mesmo comando.
- Com nome explícito, por exemplo `deploy/secrets.sh criar conexoes_chave`, cria só esse
  secret e **recusa** se ele já existir (use `trocar`).

## Conferir antes do deploy

```bash
deploy/secrets.sh verificar    # lista os ausentes e o comando para criá-los
deploy/secrets.sh resolver     # imprime VARIAVEL=nome_do_secret da versão vigente
```

`deploy/build_and_deploy.sh` já executa os dois: se faltar um secret, o deploy para
**antes de qualquer build**, com a lista e o comando de criação. Nenhum dos dois imprime
valores.

## Trocar um secret

```bash
deploy/secrets.sh trocar openrouter_api_key
deploy/secrets.sh trocar r2_credentials
```

Cria a versão seguinte (`_v2`, `_v3`...) e **preserva a anterior**. O próximo deploy
(`deploy/build_and_deploy.sh`) passa a apontar para a nova versão e o Swarm atualiza os
serviços. Se a criação falhar, a versão anterior continua vigente e nada é removido.
Versões antigas ficam no Swarm até você removê-las à mão, depois de confirmar a troca.

### Trocas com efeito colateral

`postgres_password` e `conexoes_chave` ficam **bloqueados por padrão**:

```bash
deploy/secrets.sh trocar postgres_password --confirmar-consequencia
deploy/secrets.sh trocar conexoes_chave --confirmar-consequencia
```

O script mostra a consequência, pede que você digite o nome do secret e só então cria a
nova versão, exibindo o novo valor uma única vez.

**`postgres_password`**: o Postgres só lê o secret quando cria o banco. Trocar o secret
sem alterar a senha dentro do banco derruba backend e worker. Procedimento:

1. Crie a nova versão com o comando acima e guarde o valor mostrado.
2. Altere a senha dentro do banco com o novo valor:
   `docker exec -it $(docker ps -q -f name=postgres_ragpipeline) psql -U rag_pipeline -d rag_pipeline -c "ALTER USER rag_pipeline PASSWORD '<novo valor>'"`.
3. Rode `deploy/build_and_deploy.sh` logo em seguida. Entre os passos 2 e 3 backend e
   worker ainda usam a senha antiga e perdem a conexão, então faça isso numa janela curta.

**`conexoes_chave`**: a chave de cifra é única e não há rotação automática. Trocá-la torna
ilegíveis as chaves de todas as conexões cadastradas. Depois do deploy, é preciso
recadastrar a chave de cada conexão em **Conexões**.

## Ensaio local

```bash
deploy/secrets.sh criar --ambiente local
eval "$(deploy/secrets.sh resolver --ambiente local)"
docker stack deploy --resolve-image never -c deploy/stack.prod.yml -c deploy/stack.local.yml rag-pipeline
```

Cria os quatro secrets `<nome>_local_v1` **sem perguntar nada**: chave da OpenRouter
fictícia, `r2_credentials` sem variáveis ativas (o backend grava uploads em disco) e
senha e chave Fernet geradas. Nenhuma credencial real é necessária.

## Domínio e HTTPS do Beta (SPEC-0032)

O Traefik compartilhado da VPS lê as labels do frontend na rede externa
`network_swarm_public`. Só o frontend recebe labels de exposição; `/api/*`
continua passando pelo proxy do Next.js para o backend. O stack não instala
Traefik nem cria o registro DNS.

Informe o subdomínio já apontado para a VPS no ambiente do deploy. Nenhum
domínio real deve ser gravado neste documento, no stack ou em um commit:

```bash
read -r -p 'Subdomínio do Beta: ' DOMINIO_RAGPIPELINE
export DOMINIO_RAGPIPELINE
deploy/build_and_deploy.sh
```

Sem domínio, o script para antes de consultar secrets ou construir imagens.
As variáveis abaixo são exportadas pelo script e interpoladas pelo Swarm:

| Variável | Padrão | Uso |
| --- | --- | --- |
| `DOMINIO_RAGPIPELINE` | obrigatório, sem padrão | hostname único, sem protocolo, caminho ou porta |
| `TRAEFIK_CERT_RESOLVER` | `letsencryptresolver` | resolvedor já configurado no Traefik |
| `TRAEFIK_ENTRYPOINT_HTTPS` | `websecure` | ponto de entrada HTTPS |
| `TRAEFIK_ENTRYPOINT_HTTP` | `web` | ponto de entrada HTTP, a conferir na VPS |
| `HSTS_MAX_AGE_SEGUNDOS` | `86400` | validade inicial de um dia, sem subdomínios nem preload |
| `LOGIN_RATE_LIMIT_MEDIA` | `10` | tentativas por minuto por endereço de origem |
| `LOGIN_RATE_LIMIT_RAJADA` | `20` | rajada máxima no login |

O limite só se aplica a `POST /api/v1/auth/login`; o roteador do login tem
prioridade maior que o geral. HSTS também se aplica às respostas do login.
Os valores de média, rajada e HSTS são iniciais e reversíveis. Pessoas atrás
do mesmo NAT compartilham o limite. Esta configuração pressupõe que o Traefik
receba diretamente o endereço de origem, sem CDN.

Depois do deploy, na VPS ou numa máquina com acesso público ao domínio:

```bash
deploy/conferir_dominio.sh "$DOMINIO_RAGPIPELINE"
# Também aceita apenas a variável exportada:
deploy/conferir_dominio.sh
```

O script precisa de Bash, `timeout`, `getent`, `openssl`, `curl` e `awk`.
Lista DNS, Certificado, Redirecionamento e HSTS como `OK` ou `FALHA`. Cada
consulta tem limite de dez segundos; o conjunto termina em até 60 segundos.
Código 0 significa quatro verificações aprovadas, 1 indica falha de conferência
e 2 indica entrada ou dependência inválida. A conferência não desfaz o deploy.

A emissão real do certificado e o efeito do limite só podem ser comprovados
no ambiente publicado. Abra o domínio no navegador, confira o cadeado e
confirme resposta 429 quando o mesmo endereço exceder a rajada do login.
Os testes locais verificam as labels e simulam as consultas; T027 permanece
aberta até receber essa evidência, sem registrar domínio nem credenciais.

## Automação

`--entrada-padrao` lê os valores pedidos como linhas da entrada padrão, na ordem das
perguntas. Existe para testes e automação; os valores continuam fora de argumentos.
Sem ele, uma entrada que não seja um terminal é recusada.

## Códigos de saída

| Código | Significado |
| --- | --- |
| 0 | sucesso |
| 1 | uso incorreto, validação recusada, secret ausente ou troca bloqueada |
| 2 | Docker ausente ou nó que não é manager do Swarm |

## Limites

- Os valores passam apenas pela entrada padrão do `docker secret create`; o que você
  digita pode ficar no buffer do terminal ou em gravação de tela, fora do alcance do script.
- Não há inventário com datas, lembrete de troca, rotação automática nem integração com
  gerenciadores externos (Vault, KMS).
- A atualização de um serviço com uma réplica pode interromper o serviço por alguns
  segundos durante o deploy.

## Secrets do backup (SPEC-0034)

`backup_chave`, `backup_r2_credentials` e `backup_avisos` seguem as mesmas
versões externas e o sufixo `_local`. Use `deploy/secrets.sh criar` para
completar os ausentes. A chave de backup é fornecida pela pessoa e nunca é
exibida; guarde-a antes no gerenciador de senhas fora da VPS.

O provisionador pede bucket separado, endpoint HTTPS, access key e secret key
para `backup_r2_credentials`; pede SMTP URL, usuário, senha, remetente,
destinatário e webhook HTTPS para `backup_avisos`. Os arquivos são pares
`KEY=valor` literais, sem execução nem expansão shell. A ordem é a da ajuda
operacional em [BACKUP.md](BACKUP.md). O modo local preenche valores fictícios
para `s3_local_ragpipeline` e `avisos_local_ragpipeline`, sem perguntas.

Trocar a chave de backup afeta somente os novos dumps. Preserve as chaves
anteriores fora da VPS enquanto existir backup cifrado com elas. O bucket de
backup exige credencial própria, limitada a ele; nunca reutilize
`r2_credentials` da aplicação. Os valores resolvidos são
`BACKUP_CHAVE_SECRET`, `BACKUP_R2_CREDENTIALS_SECRET` e `BACKUP_AVISOS_SECRET`.

O passo a passo completo de atualização, primeira instalação e emergências está em [RUNBOOK.md](RUNBOOK.md).
