# Inbox: Corrida entre has_active_execution e o insert de Execution

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-09-15T16:38:04Z |
| Slug | corrida-entre-has-active-execution-e-o-insert-de-execution |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `1084d18c274534efb37e6acb7eb8ecee399b3ad76d2266da3d759c3eea83a0b7` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

iniciar_execucao/repetir_execucao fazem has_active_execution e o insert da nova Execution sem lock nem constraint no banco ((base_id, situacao) sem índice único) — duas requisições concorrentes podem passar pelo check antes de qualquer commit e criar duas execuções ativas para a mesma base, violando FR-009 sob concorrência real (dois agentes independentes do /code-review encontraram o mesmo problema). test_impede_execucao_concorrente só testa chamadas sequenciais, não concorrência real.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** iniciar_execucao/repetir_execucao verificam has_active_execution e inserem a nova Execution sem lock nem constraint única, permitindo duas execuções ativas concorrentes para a mesma base.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Duas requisições concorrentes podem passar pelo check has_active_execution antes de qualquer commit e criar duas execuções ativas simultâneas para a mesma base, violando FR-009 sob concorrência real.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Não identificado no texto original.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Não identificado no texto original.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** FR-009 (SPEC-0012). Falta lock ou constraint única em (base_id, situacao) na tabela de Execution. test_impede_execucao_concorrente só cobre chamadas sequenciais, não concorrência real. Encontrado por dois agentes independentes do /code-review.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Tabela de Execution: par (base_id, situacao) sem índice único hoje.

### Riscos e dependências

**Análise preliminar:** Duas execuções ativas simultâneas para a mesma base sob concorrência real; achado registrado em SPEC-0012 seção 16 como 'Não corrigido, registrado para spec/backlog futuro' e listado em specs/milestones/M02.md como item sem milestone atribuída.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Backlog/spec futura para adicionar lock ou constraint única de banco em (base_id, situacao) e cobrir com teste de concorrência real.

## Pontos a revisar no futuro

**A revisar:** Confirmar com a pessoa responsável se a correção é lock otimista/pessimista na aplicação ou constraint única no banco; nenhuma solução foi decidida no texto original.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
