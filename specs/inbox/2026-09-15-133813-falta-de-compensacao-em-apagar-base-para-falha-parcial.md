# Inbox: Falta de compensação em apagar_base para falha parcial

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-09-15T16:38:13Z |
| Slug | falta-de-compensacao-em-apagar-base-para-falha-parcial |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `0f6b37d1ec9d80a43f47df94df2e2555b8b491f1820dce1ef4e976db451f6204` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

apagar_base não tem compensação se delete_scope ou o storage falharem após o soft-delete no Postgres já commitado: a base fica invisível (get_base_or_404 a exclui) e sem endpoint de retry, deixando storage/vetores órfãos permanentemente nesse cenário de falha parcial.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** apagar_base não tem compensação quando delete_scope ou o storage falham após o soft-delete no Postgres já ter sido commitado, deixando storage e vetores órfãos permanentemente.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Se delete_scope ou o storage falharem depois do soft-delete já commitado, a base fica invisível (get_base_or_404 a exclui) e não existe endpoint de retry, deixando storage/vetores órfãos permanentemente nesse cenário de falha parcial.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Não identificado no texto original.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Não identificado no texto original.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** apagar_base (src/app). delete_scope. get_base_or_404 exclui bases com soft-delete. Ausência de endpoint de retry para o cenário de falha parcial.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Estado de soft-delete de uma base pode ficar commitado no Postgres enquanto storage/vetores associados permanecem órfãos.

### Riscos e dependências

**Análise preliminar:** Órfãos permanentes de storage/vetores após falha parcial; achado registrado em SPEC-0012 seção 16 como 'Não corrigido, registrado para spec/backlog futuro' e listado em specs/milestones/M02.md como item sem milestone atribuída.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Backlog/spec futura para desenhar compensação (saga/retry) ou endpoint de retry para completar a exclusão de storage/vetores após falha parcial.

## Pontos a revisar no futuro

**A revisar:** Confirmar com a pessoa responsável a estratégia de compensação preferida (retry manual, job de reconciliação, transação distribuída) — nenhuma solução foi decidida no texto original.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
