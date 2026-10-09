# Inbox: Stack local divergente dos arquivos de deploy e banco sem histórico de migrations

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-08T22:00:19Z |
| Slug | stack-local-divergente-dos-arquivos-de-deploy-e-banco-sem-historico-de-migrations |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `d49bb6a42128d21d068e12929b464d8bc453bed38fc5caadaf58299a144a45f2` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Pendência operacional registrada pelo agente em 2026-10-08, com autorização da pessoa: o stack local foi ajustado manualmente fora dos arquivos de stack. (1) imagens rag-pipeline-backend:local e rag-pipeline-frontend:local reconstruídas e serviços atualizados com docker service update, sem docker stack deploy; (2) banco local sem alembic_version, criado por create_all: colunas da migration 0026 aplicadas à mão pela pessoa e revisão 0026_conexoes_ingestao registrada; (3) secret conexoes_chave_local_v1 criado por deploy/secrets.sh e adicionado a backend e worker com APP_CONEXOES_CHAVE_FILE. O stack em execução usa os secrets de nome de produção sem sufixo de versão (postgres_password, openrouter_api_key, session_secret, r2_credentials).

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** O stack local recebeu ajustes manuais (imagens, migration 0026 e secret da chave de cifra) que um próximo docker stack deploy pode desfazer, e o banco local não era gerido pelo Alembic.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Um docker stack deploy com os arquivos atuais e os secrets _local recriaria senha do Postgres e chave do OpenRouter, derrubando o acesso ao banco e o Assistente; sem alembic upgrade no deploy, colunas novas quebram o backend como ocorreu com a 0026.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoa que opera o ambiente local e o deploy.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Deploy local e de produção reproduzível, com migrations aplicadas e secrets consistentes.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Evidência: o backend inicia sem rodar migrations (comando do serviço só chama uvicorn); src/app/db.py:45 usa create_all; deploy/SECRETS.md, seção Ensaio local, cria os quatro secrets _local de uma vez; o próximo deploy precisa de CONEXOES_CHAVE_SECRET=conexoes_chave_local_v1 para manter as conexões legíveis.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Chave de cifra das conexões: perder ou trocar torna ilegíveis as chaves já cadastradas.

### Riscos e dependências

**Análise preliminar:** Perda das conexões cadastradas ao trocar a chave de cifra; banco inacessível ao trocar a senha; migrations futuras não aplicadas.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Incluir no BACKLOG-0032 (runbook de deploy manual): passo de alembic upgrade head no deploy, reconciliação dos nomes de secrets do ensaio local e uso do secret conexoes_chave existente.

## Pontos a revisar no futuro

**A revisar:** Decidir se o backend roda migrations ao iniciar ou por tarefa separada; decidir se o ensaio local passa a usar os secrets _local ou os de nome de produção.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
