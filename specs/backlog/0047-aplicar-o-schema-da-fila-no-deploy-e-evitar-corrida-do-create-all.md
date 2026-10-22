# Backlog: Aplicar o schema da fila no deploy e evitar corrida do create_all

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0047 |
| Status | Promoted |
| Produto | RAG Pipeline |
| Épico | Deploy do beta (M03) |
| Funcionalidade | Preparação do banco no deploy |
| Tipo | Técnico |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-22 |
| Spec promovida | specs/draft/0042-aplicar-o-schema-da-fila-no-deploy-e-evitar-corrida-do-create-all/spec.md |

## Ideia original

Achado do ensaio local em Docker (2026-10-22): o deploy/RUNBOOK.md roda alembic upgrade head e o deploy, mas nenhum passo aplica o schema da fila Procrastinate; num banco novo a publicação de coleção falha, o worker cai em loop e o registro da coleção fica órfão. O app também cria tabelas com create_all na subida, e backend e worker disputaram a criação num banco vazio.

## Problema percebido

A primeira instalação em banco novo (T020 da SPEC-0041, Supabase externo) não consegue publicar coleções sem um passo manual não documentado, e uma falha ao enfileirar deixa a coleção registrada sem envio, bloqueando o nome.

## Pessoa afetada ou beneficiada

Quem opera o deploy do beta e quem publica coleções no Workspace.

## Resultado ou valor esperado

Primeira instalação e atualizações que deixam a fila pronta antes de o app atender, sem registro órfão quando o enfileiramento falha.

## Contexto

Distinto da captura de 2026-10-08 (stack local divergente e migrations): aqui o foco é o schema da fila Procrastinate, a corrida do create_all na subida e a compensação da coleção órfã. Bloqueia a T020 da SPEC-0041.

## Referências relacionadas

- `specs/inbox/2026-10-22-191007-aplicar-o-schema-da-fila-procrastinate-no-deploy-e-evitar-corrida-do-create-all.md` — origem (captura).
- `specs/inbox/2026-10-08-220019-stack-local-divergente-dos-arquivos-de-deploy-e-banco-sem-historico-de-migrations.md` — backlog relacionado: `create_all` versus migrations no deploy; não trata da fila.
- `specs/in-progress/0041-servicos-externos-qdrant-postgres-producao/spec.md` — spec relacionada: a T020 (deploy com Supabase novo) depende deste item; evidência do ensaio na seção 13.
- `specs/completed/0035-runbook-de-deploy-manual-em-producao/spec.md` — spec relacionada: definiu o runbook com `alembic upgrade head` sem o schema da fila.
- `specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md` — spec relacionada: introduziu o worker Procrastinate e a CLI `schema --apply`.
- `src/app/main.py:113` e `src/app/db.py:41` — `create_tables()` com `create_all` na subida do backend e do worker.
- `docs/application.md` — documentação relacionada: entrypoint do worker e `schema --apply`.

## Comportamento esperado

- Uma migration do Alembic cria o schema da fila Procrastinate somente se ele ainda não existir; `alembic upgrade head` em banco vazio deixa tabelas do app e da fila prontas.
- Backend e worker não criam tabelas na subida; verificam se o banco está na versão esperada do Alembic e, se não estiver, param com mensagem clara que indica o passo de migração.
- Se o enfileiramento do envio falhar durante a publicação, nada fica gravado: a coleção não persiste, a pessoa vê o erro e pode tentar de novo com o mesmo nome.
- O runbook documenta o passo único `alembic stamp head` para bancos já criados pelo `create_all`, após conferir o schema.

## Regras de negócio

- O Alembic é a única fonte do schema do banco da aplicação e da fila.
- A migration da fila é idempotente: não falha nem recria quando o schema já existe.
- Publicação é atômica em relação ao enfileiramento: ou a coleção e o envio existem, ou nenhum.

## Critérios de aceitação

- Dado um banco Postgres vazio, quando `alembic upgrade head` é executado, então as tabelas do app e as `procrastinate_*` existem e `alembic_version` está no head.
- Dado um banco já no head, quando `alembic upgrade head` é executado de novo, então termina sem erro e sem alterar o schema.
- Dado um banco sem a migração aplicada, quando o backend ou o worker sobe, então encerra com mensagem clara indicando `alembic upgrade head`, sem criar tabelas.
- Dado que o enfileiramento do envio falha na publicação, quando a pessoa publica a coleção `X`, então vê o erro, nenhuma coleção `X` fica gravada e uma nova tentativa com o nome `X` é aceita.
- Dado um banco criado pelo `create_all` e sem `alembic_version`, quando o runbook de adoção é seguido (`alembic stamp head`), então o `alembic upgrade head` seguinte não tenta recriar tabelas.
- Dado um banco novo migrado, quando backend e worker sobem juntos, então não há disputa nem `UniqueViolation` na criação de tabelas.

## Qualidades e operação

- Segurança: a migration não grava credenciais; a verificação de versão não expõe a URL do banco na mensagem.
- Privacidade: não aplicável, sem dado pessoal novo.
- Desempenho e volume: a verificação de versão roda uma vez na subida, com custo desprezível.
- Auditoria e observabilidade: a mensagem de banco não migrado e a falha de enfileiramento são registradas no log do serviço.

## Dependências

- Bloqueia a T020 da SPEC-0041 (deploy do beta no Supabase novo).
- Relaciona-se ao runbook da SPEC-0035 e ao worker da SPEC-0012.

## Situações de erro

- Banco não migrado na subida: o serviço para com mensagem clara.
- Falha ao enfileirar: publicação desfeita com erro visível, sem registro órfão.
- Banco antigo sem `alembic_version`: segue o passo de adoção do runbook.

## Escopo

- Dentro: migration idempotente do schema da fila; remoção do `create_all` da subida com verificação de versão; atomicidade da publicação na falha do enfileiramento; passo de adoção no runbook; ajuste dos testes que dependiam do `create_all`.
- Fora: limpeza das coleções órfãs já existentes em bancos ou no Qdrant publicado; execução do deploy real na VPS (T020 e T027); outras divergências do stack local (captura de 2026-10-08).

## Dúvidas, decisões e riscos

- **Decisão (2026-10-22, Pergunta 1, resposta "1")**: o schema da fila Procrastinate é aplicado por uma migration do Alembic que o cria somente se ainda não existir. O `alembic upgrade head` do runbook passa a preparar tudo, sem passo manual novo; o mesmo caminho serve para banco novo e existente.
- **Decisão (2026-10-22, Pergunta 2, resposta "1")**: remover o `create_all` da subida. O Alembic é a única fonte do schema; na subida, backend e worker verificam se o banco está na versão esperada e param com mensagem clara se não estiver.
- **Decisão (2026-10-22, Pergunta 3, resposta "1")**: se o enfileiramento do envio falhar, a publicação inteira é desfeita: a coleção não fica gravada, a pessoa vê o erro e pode tentar de novo com o mesmo nome.
- **Decisão (2026-10-22, Pergunta 4, resposta "1")**: bancos já criados pelo `create_all` (tabelas sem `alembic_version`) são adotados por um passo único documentado no runbook, `alembic stamp head`, depois de conferir que o schema está completo. O beta novo não precisa desse passo.
- **Risco (inferência)**: testes que hoje dependem de `create_tables()` (por exemplo, `tests/conftest.py`) precisarão preparar o banco pelo Alembic; avaliar na spec.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Spec criada: SPEC-0042. O comportamento passa a ser governado pela spec.
