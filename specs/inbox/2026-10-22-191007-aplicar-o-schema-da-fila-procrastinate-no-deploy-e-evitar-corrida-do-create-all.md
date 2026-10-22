# Inbox: Aplicar o schema da fila Procrastinate no deploy e evitar corrida do create_all

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-22T19:10:07Z |
| Slug | aplicar-o-schema-da-fila-procrastinate-no-deploy-e-evitar-corrida-do-create-all |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `34e8dd3ea3bfd2129642798121527b86ce7d8b2ce5b4b7db8b4eefe19320aaee` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Achado do ensaio local em Docker (2026-10-22, commit 5713fc8): o deploy/RUNBOOK.md manda rodar 'alembic upgrade head' e depois o deploy, mas nenhum passo aplica o schema da fila de tarefas do Procrastinate ('python -m procrastinate --app src.app.worker.app schema --apply'). Num banco novo, publicar uma coleção falha com 'type procrastinate_job_to_defer_v1[] does not exist', o worker cai em loop e o registro da coleção fica gravado sem envio, de modo que a nova tentativa responde 'Já existe uma coleção com esse nome neste Workspace'. Além disso, o app cria as tabelas sozinho na subida (create_all em src/app/db.py), e backend e worker, ao subirem juntos num banco vazio, disputaram a criação (UniqueViolation em pg_type_typname_nsp_index).

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Num banco novo o runbook não aplica o schema da fila e o create_all do app pode disputar a criação de tabelas; a publicação de coleção falha e deixa registro órfão.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** A primeira instalação em banco externo novo (T020 da SPEC-0041) reproduziria a falha da publicação, do worker e do registro órfão da coleção.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Quem opera o deploy do beta e quem publica coleções.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Primeira instalação que publica coleções sem passos manuais não documentados.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: o runbook roda alembic upgrade head antes do deploy e não aplica o schema da fila. Declaração: src/app/db.py cria tabelas com create_all na subida. Declaração: o registro da coleção persiste mesmo quando o envio falha.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Tabelas procrastinate_* da fila no Postgres; registro de coleção sem envio concluído.

### Riscos e dependências

**Análise preliminar:** Deploy da T020 falhar na primeira publicação; coleções órfãs bloqueiam o reuso do nome.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Inferência: passo do runbook ou verificação na subida para aplicar o schema da fila; avaliar compensação ao falhar o enfileiramento; avaliar remover ou serializar o create_all em favor do Alembic.

## Pontos a revisar no futuro

**A revisar:** Onde aplicar o schema (runbook manual, job de migração ou entrypoint); se o create_all deve continuar; limpeza de coleções órfãs já criadas.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
