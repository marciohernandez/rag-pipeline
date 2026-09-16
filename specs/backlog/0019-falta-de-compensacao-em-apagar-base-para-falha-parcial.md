# Backlog: Falta de compensação em apagar_base para falha parcial

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0019 |
| Status | Promoted |
| Produto | rag-pipeline — backend de aplicação (SPEC-0012) |
| Épico | Confiabilidade e integridade de dados |
| Funcionalidade | Exclusão de base |
| Tipo | Técnico (correção de bug de consistência) |
| Prioridade | Alta |
| Milestones | |
| Criado em | 2026-09-15 |
| Spec promovida | specs/draft/0018-falta-de-compensacao-em-apagar-base-para-falha-parcial/spec.md |

## Ideia original

apagar_base não tem compensação se delete_scope ou o storage falharem após o soft-delete no Postgres já commitado: a base fica invisível (get_base_or_404 a exclui) e sem endpoint de retry, deixando storage/vetores órfãos permanentemente nesse cenário de falha parcial.

## Problema percebido

Se delete_scope ou o storage falharem depois do soft-delete já commitado em apagar_base, a base fica invisível (get_base_or_404 a exclui) e não existe endpoint de retry, deixando storage/vetores órfãos permanentemente.

## Pessoa afetada ou beneficiada

Pessoa com papel `owner` ou `admin` (única com permissão de apagar base, ver
`ExcluirBaseDialog.tsx`/`require_write_role`), que hoje pode ficar com storage
e vetores órfãos permanentemente sem forma de corrigir, mesmo tentando "apagar
de novo" pela mesma tela.

## Resultado ou valor esperado

Nenhum recurso (storage ou vetores) fica órfão permanentemente após uma falha
parcial; uma falha em `apagar_base` é sempre recuperável repetindo a mesma
chamada `DELETE`, sem endpoint ou fluxo adicional.

## Situações de erro

- `storage.delete_base` ou `service.delete_scope` falham: a exceção propaga
  (HTTP 500, comportamento inalterado hoje), mas a base permanece ativa no
  Postgres — `Execution`/`Query` não são removidos e `apagada_em` não é
  preenchido. Repetir o `DELETE` reexecuta os dois passos.
- Ambos os deletes externos já são naturalmente idempotentes (confirmado no
  código: `LocalDirectoryStorage.delete_base` checa `pasta.exists()`;
  `S3CompatibleStorage.delete_base` itera objetos existentes por prefixo;
  `service.delete_scope` lista IDs e só chama `delete_ids` se houver algum) —
  repetir a chamada após falha parcial (ex.: storage apagado, vector store
  falhou) não gera erro nem efeito colateral no que já foi apagado.

## Contexto

Achado registrado em specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md, seção 16, como 'Não corrigido, registrado para spec/backlog futuro'; citado em specs/milestones/M02.md como item de dívida técnica sem milestone atribuída.

## Referências relacionadas

- `specs/inbox/2026-09-15-133813-falta-de-compensacao-em-apagar-base-para-falha-parcial.md` — captura de origem (proveniência).
- `specs/completed/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md:1233` — spec relacionada: achado original "Não corrigido, registrado para spec/backlog futuro".
- `specs/milestones/M02.md` — documentação relacionada: item listado em "Fora de escopo" como dívida técnica sem milestone.
- `src/app/routers/bases.py:162-189` (`apagar_base`) — código relacionado: soft-delete commitado antes de `get_storage().delete_base` e `service.delete_scope`, sem bloco de compensação.
- `src/pipeline/service.py:175` (`delete_scope`) — operação que pode falhar depois do commit do soft-delete.

## Comportamento esperado

`apagar_base` apaga storage e vector store primeiro; o soft-delete no
Postgres (`apagada_em`, remoção de `Execution`/`Query`) só é commitado depois
que os dois externos tiverem sucesso. Se qualquer um falhar, a base continua
visível/ativa e a pessoa pode repetir o mesmo `DELETE` — sem endpoint novo,
sem job em segundo plano. Decisão confirmada em 2026-09-15.

## Regras de negócio

- A esclarecer conforme risco e complexidade.

## Critérios de aceitação

- Dado que uma base existe e tem execuções indexadas, quando `apagar_base` é
  chamada e `storage.delete_base` ou `service.delete_scope` falham, então o
  Postgres não muda de estado — a base continua visível e ativa (sem
  `apagada_em`, sem remover `Execution`/`Query`) — e a pessoa pode repetir o
  mesmo `DELETE` para concluir a exclusão.
- Dado que uma base existe, quando `apagar_base` é chamada e storage e vector
  store são apagados com sucesso, então o Postgres commita o soft-delete
  (`apagada_em`, remoção de `Execution`/`Query`) e a base passa a ser
  invisível (`get_base_or_404` a exclui), preservando o comportamento atual
  para o caminho feliz.
- Decisão confirmada em 2026-09-15.

## Qualidades e operação

- Segurança: sem mudança de superfície — só reordena chamadas já existentes.
- Privacidade: não aplicável; nenhum dado pessoal envolvido.
- Desempenho e volume: sem impacto — mesmas duas chamadas externas, só em
  ordem diferente; nenhuma chamada adicional no caminho feliz.
- Auditoria e observabilidade: não avaliado como requisito — a esclarecer se
  necessário durante a especificação.

## Dependências

- Nenhuma dependência bloqueante de outra spec ou backlog. Sem migration de
  banco (mudança é só de ordem de chamadas, sem alterar schema).
- Relacionado a BACKLOG-0018 (mesma origem — fechamento do M02, mesmo módulo
  `src/app`), mas decidido como spec separada.

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: reordenar `apagar_base` (`src/app/routers/bases.py`) para apagar
  storage e vector store antes de commitar o soft-delete no Postgres; testes
  cobrindo falha em cada um dos dois passos externos, confirmando que o
  Postgres não muda de estado e que repetir o `DELETE` completa a exclusão.
- Fora: qualquer mudança no frontend (decisão confirmada); endpoint de retry
  dedicado (decisão confirmada — retry é simplesmente repetir o `DELETE`);
  job de reconciliação em segundo plano (decisão confirmada); spec conjunta
  com BACKLOG-0018 (decisão confirmada — specs separadas).

## Dúvidas, decisões e riscos

- Decisão (2026-09-15): reordenar `apagar_base` — apagar storage e vector
  store antes de commitar o soft-delete no Postgres — em vez de job de
  reconciliação ou rollback automático do soft-delete.
- Decisão (2026-09-15): sem mudança de frontend; `ExcluirBaseDialog.tsx` já
  orienta "tente novamente", que passa a funcionar de verdade com a correção.
- Decisão (2026-09-15): prioridade Alta — mesmo nível do BACKLOG-0018.
- Decisão (2026-09-15): spec separada do BACKLOG-0018, apesar de descoberta
  junto e no mesmo módulo — correções independentes, uma exige migration e a
  outra não.
- Confirmado por leitura de código: `storage.delete_base` e
  `service.delete_scope` já são idempotentes, então repetir o `DELETE` após
  falha parcial é seguro sem tratamento especial adicional.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promovido para `specs/draft/0018-falta-de-compensacao-em-apagar-base-para-falha-parcial/spec.md` (SPEC-0018) em 2026-09-15. Próximo passo: `$specsfy-04-validate`.
