# Integrações

<!-- specsfy:documentator:start -->
## Configuração

Valores de ambiente e integrações são documentados apenas pelos nomes declarados localmente, sem segredos.
<!-- specsfy:documentator:end -->

## Integrações verificadas

| Integração | Uso | Configuração sem valores |
| --- | --- | --- |
| OpenAI | embeddings | `OPENAI_API_KEY` e parâmetros em `config.yaml` |
| OpenRouter | embeddings e demonstração de chat | `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `LLM_MODEL` |
| Hugging Face | embeddings locais | modelo e device em `config.yaml` |
| Qdrant | destino vetorial e busca; único provider concreto desde a SPEC-0010 | `QDRANT_URL`, `QDRANT_API_KEY`, collection em `config.yaml` |
| R2 de backup | dump PostgreSQL cifrado diário; bucket separado do sistema | secrets `backup_r2_credentials` e `backup_chave` no serviço `backup_ragpipeline` |
| SMTP e webhook | avisos independentes de falha no backup | secret `backup_avisos`; configuração e resposta a falhas em `deploy/BACKUP.md` |

Em produção o Postgres e o Qdrant são externos (SPEC-0041): `DATABASE_HOST`,
`DATABASE_USER`, `DATABASE_NAME`, `DATABASE_PORT`, `DATABASE_SSLMODE`, `QDRANT_URL`, o secret
`qdrant_api_key` e o prefixo opcional `APP_COLECAO_PREFIXO`; detalhes em
[deploy/SECRETS.md](../deploy/SECRETS.md).

Credenciais são lidas do ambiente e não devem ser versionadas. Os nomes acima
são o contrato de configuração; nenhum valor sensível é publicado aqui.

O [manual de backup](../deploy/BACKUP.md) descreve retenção, restauração e
verificação na VPS. `bash deploy/backup/ensaio.sh` executa a prova local com
Postgres temporário e Moto simulando S3, sem portas publicadas. As credenciais
do ensaio são fictícias; o script verifica dump, cifragem, publicação,
idempotência, restauração e os dois canais de aviso, e remove seus recursos.

O [runbook de deploy](../deploy/RUNBOOK.md) descreve a atualização, a primeira
instalação e as emergências. Cada imagem é etiquetada pelo commit curto, as três
últimas versões ficam no nó e `deploy/build_and_deploy.sh --versao <etiqueta>`
reimplanta uma versão guardada sem construir.
