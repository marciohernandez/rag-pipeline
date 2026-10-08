# Backlog: Apagar Base usa a coleção e as conexões da própria Base

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0035 |
| Status | Promoted |
| Produto | rag-pipeline |
| Épico | Bases e coleções |
| Funcionalidade | Apagar Base |
| Tipo | Correção (bug) |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-08 |
| Spec promovida | specs/completed/0028-apagar-base-usa-colecao-e-conexoes-da-base/spec.md (SPEC-0028, Complete) |

## Ideia original

Ao tentar apagar uma Base pela interface (botão Apagar base na tela da Base), a exclusão falha com 'Não foi possível apagar a base. Tente novamente.' O backend registra UnreliableScopeReadError causado por 404 do Qdrant: coleção rag-pipeline-app não existe. A Base foi criada com a coleção 'vivo test' e os 23 chunks estão nela. Indexação e consulta usam base.collection_name; apagar_base monta a configuração com a coleção padrão do sistema e ignora a coleção da Base. (Fonte: specs/inbox/2026-10-05-165154-apagar-base-ignora-a-colecao-da-base-e-falha-com-404-no-qdrant.md)

## Problema percebido

Apagar qualquer Base com coleção própria falha com 404 no Qdrant; se a coleção padrão existisse, a exclusão deixaria vetores órfãos na coleção real.

## Pessoa afetada ou beneficiada

Owner/admin e demais pessoas com papel de escrita que apagam Bases.

## Resultado ou valor esperado

Apagar uma Base remove seus vetores da coleção e das conexões corretas, e a Base some da listagem, sem resíduos; verificável pelo front.

## Contexto

Divergência entre apagar_base (settings.vector_store) e executions/queries/publicacao (base.collection_name e conexões por Base da SPEC-0026). Relacionado a SPEC-0018 (compensação) e SPEC-0019 (coleção por Base).

## Referências relacionadas

- `specs/inbox/2026-10-05-165154-apagar-base-ignora-a-colecao-da-base-e-falha-com-404-no-qdrant.md` — captura de origem (preservada).
- `specs/completed/0018-falta-de-compensacao-em-apagar-base-para-falha-parcial/spec.md` — spec relacionada: ordem e idempotência da exclusão.
- `specs/completed/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md` — spec relacionada: coleção por Base.
- `specs/completed/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md` — spec relacionada: conexões por Base.
- Código lido (evidência): `src/app/routers/bases.py:281-316`, `src/app/publicacao.py:80-115`, `src/app/routers/queries.py:44-46`.

## Comportamento esperado

Ao clicar em **Apagar base** na tela da Base, a exclusão remove os vetores da Base na coleção e nas conexões (embeddings e vector store) que a própria Base usa, apaga os dados no storage e no Postgres e a Base some da listagem. Nenhuma tela nova: o botão, a confirmação e a mensagem de erro existentes são preservados.

## Regras de negócio

- A configuração da exclusão é montada pelo mesmo caminho da indexação e da consulta (coleção e conexões da Base), inclusive para Bases anteriores à SPEC-0026 (configuração global com `collection_name` da Base).
- Coleção ausente no Qdrant equivale a já apagada: não há vetores a remover, a exclusão segue e a Base some da listagem (decisão da Pergunta 2).
- Falhas diferentes de coleção ausente (Qdrant fora do ar, leitura de escopo não confiável) continuam bloqueando a exclusão antes de qualquer escrita no Postgres, e a pessoa pode repetir o DELETE (SPEC-0018).
- Permissão inalterada: exige papel de escrita.

## Critérios de aceitação

- **Dado** uma Base com coleção própria (ex.: `vivo test`) já indexada, **quando** a pessoa com papel de escrita clica em Apagar base e confirma, **então** os vetores saem da coleção da Base, a Base some da listagem e nenhuma mensagem de erro aparece.
- **Dado** uma Base com conexões próprias de embeddings e vector store, **quando** é apagada, **então** a remoção ocorre no vector store dessa conexão, não no padrão do sistema.
- **Dado** uma Base cuja coleção não existe mais no Qdrant, **quando** é apagada, **então** a exclusão conclui e a Base some da listagem.
- **Dado** uma falha do Qdrant que não seja coleção ausente, **quando** a pessoa tenta apagar, **então** a Base continua visível, nada é apagado no Postgres e repetir a ação funciona depois que o Qdrant volta.
- **Dado** a coleção padrão do sistema com dados de outra Base, **quando** uma Base com coleção própria é apagada, **então** a coleção padrão não é alterada.

## Qualidades e operação

- Segurança: a exclusão nunca deve atingir coleção de outra Base ou do padrão; isolamento por tenant/projeto/base preservado (`scope_project_id`).
- Privacidade: a exclusão não deixa vetores órfãos com conteúdo da Base.
- Desempenho e volume: sem exigência nova; ordem de operações da SPEC-0018 preservada.
- Auditoria e observabilidade: registrar em log a coleção e a conexão alvo da exclusão e o caso de coleção ausente.

## Dependências

- SPEC-0018, SPEC-0019 e SPEC-0026 (concluídas) — comportamento a preservar.

## Situações de erro

- Coleção ausente: tratada como já apagada (sem erro).
- Qdrant indisponível ou escopo não confiável: exclusão bloqueada, mensagem existente "Não foi possível apagar a base. Tente novamente.", sem escrita no Postgres.

## Escopo

- Dentro: usar coleção e conexões da Base na exclusão; coleção ausente = já apagada; teste de regressão cobrindo coleção própria e conexão própria; verificação pelo front.
- Fora: telas novas ou mudança de texto da interface; limpeza automática de Bases vazias por upload falho; mudança de outros caminhos além de `apagar_base` (pode ser registrada em novo item se a revisão do código achar divergência); investigar se o espaço em `vivo test` interfere (verificar durante o teste).

## Dúvidas, decisões e riscos

- **Decisão (Pergunta 1, 2026-10-08):** a exclusão usa a mesma configuração da indexação e da consulta — coleção e conexões da Base — inclusive para Bases com conexão própria. Resposta original: `1`. Efeito: não basta trocar a coleção; a montagem da configuração de exclusão deve seguir o mesmo caminho da indexação (`publicacao.py`).
- **Evidência (código, não declaração):** Bases anteriores à SPEC-0026 mantêm a configuração global com `collection_name` da Base.
- **Decisão (Pergunta 2, 2026-10-08):** coleção ausente no Qdrant é tratada como já apagada. Resposta original: `1`.
- **Risco:** distinguir 404 de coleção ausente de outras falhas sem engolir erros reais.
- **Aberto (a verificar no teste):** nome da coleção com espaço (`vivo test`).
- **Verificação:** o resultado precisa ser comprovável pelo front (criar Base com coleção própria, indexar, apagar).

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promover com `$specsfy-03-specify` (branch `fix/` ou `spec/` conforme `.specsfy/RULES.md`).
