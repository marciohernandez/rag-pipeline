# Secrets de produção do Swarm

Guia de uso de `deploy/secrets.sh` (SPEC-0027). O script cria, confere e troca os
secrets que a stack de produção lê em `/run/secrets/*`. Ele roda **no nó manager do
Swarm**, com a CLI do Docker, e é operado manualmente.

## O que existe

| Secret | Origem do valor | Para que serve |
| --- | --- | --- |
| `openrouter_api_key` | você informa, sem eco | chave da OpenRouter (embeddings e assistente) |
| `r2_credentials` | você informa bucket, endpoint, access key e secret key, sem eco | armazenamento Cloudflare R2 dos uploads |
| `postgres_password` | gerado pelo script | senha do usuário `rag_pipeline` do Postgres |
| `conexoes_chave` | gerado pelo script (chave Fernet) | cifra as chaves das conexões de ingestão |

O `session_secret` deixou de existir: nada no código o usa desde a autenticação por
pessoa e sessão (SPEC-0020).

## Convenção de nomes

Um secret do Swarm não pode ser editado. Por isso cada valor vive em uma versão:

- produção: `<nome>_v<N>`, por exemplo `openrouter_api_key_v1` e `openrouter_api_key_v2`;
- ensaio local: `<nome>_local_v<N>`, por exemplo `openrouter_api_key_local_v1`.

A versão vigente é a de maior `N`. `deploy/build_and_deploy.sh` descobre essas versões e
as entrega ao stack pelas variáveis `OPENROUTER_API_KEY_SECRET`, `R2_CREDENTIALS_SECRET`,
`POSTGRES_PASSWORD_SECRET` e `CONEXOES_CHAVE_SECRET`. Sem a variável, o stack usa `_v1`.

## Primeira instalação

```bash
deploy/secrets.sh criar
```

- Pede, sem eco, a chave da OpenRouter e os campos do R2.
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

## Domínio, HTTPS e proxy reverso (SPEC-0032)

O frontend é exposto pelo Traefik compartilhado da VPS, por labels em
`deploy/stack.prod.yml`. As variáveis abaixo são lidas por `deploy/build_and_deploy.sh`;
nenhuma guarda valor real no repositório.

| Variável | Obrigatória | Padrão | Uso |
| --- | --- | --- | --- |
| `DOMINIO_RAGPIPELINE` | Sim | — | Domínio público do frontend. Sem ela o deploy é recusado antes de qualquer build. |
| `TRAEFIK_CERT_RESOLVER` | Não | `letsencryptresolver` | Resolvedor de certificados do Traefik. |
| `TRAEFIK_ENTRYPOINT_HTTPS` | Não | `websecure` | Ponto de entrada HTTPS. |
| `TRAEFIK_ENTRYPOINT_HTTP` | Não | `web` | Ponto de entrada HTTP, que redireciona de forma permanente para HTTPS. |
| `HSTS_MAX_AGE_SEGUNDOS` | Não | `86400` | Validade do HSTS (sem `includeSubdomains` nem `preload`). |
| `LOGIN_RATE_LIMIT_MEDIA` | Não | `10` | Média de tentativas de login por minuto, por endereço de origem. |
| `LOGIN_RATE_LIMIT_RAJADA` | Não | `20` | Rajada máxima; acima dela o Traefik responde 429. |

Depois do deploy, confira o domínio no nó manager ou em qualquer máquina com acesso à internet:

```bash
deploy/conferir_dominio.sh "$DOMINIO_RAGPIPELINE"
```

O script verifica DNS, certificado, redirecionamento HTTP e HSTS, com limite de 10 s por
consulta. Cada verificação aparece como `OK` ou `FALHA`, e qualquer falha encerra com código
diferente de 0.
