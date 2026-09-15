# Inbox: Reconciliar specs concluídas com o enforcement atual

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-09-15T19:35:21Z |
| Slug | reconciliar-specs-concluidas-com-o-enforcement-atual |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `820a2c27fe5957c164b9804ae2a1ca7790593c57384f9763fb9171d0af91d0eb` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

O enforcement global verify_repo continua falhando depois que a colisão de namespaces foi corrigida. A rastreabilidade simples das specs históricas passa, mas specs concluídas antigas ainda não satisfazem os contratos atuais de tarefas, evidências, research e, em três casos, da cadeia full-chain por evidência ausente. Isso deve ser reconciliado separadamente sem reescrever retroativamente evidências que não possam ser provadas.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Separar e corrigir incompatibilidades históricas que mantêm verify_repo vermelho após a correção de namespace.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** O gate global não pode ficar verde porque specs concluídas sob versões anteriores do framework falham nos validadores atuais de tarefas, evidências, research e full-chain.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoas mantenedoras e automações que dependem de verify_repo como gate confiável.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Definir uma política auditável de migração ou compatibilidade para que o enforcement global fique verde sem fabricar evidência retroativa.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Falhas observadas em tasks/evidence/research de specs antigas; trace simples agora passa; full-chain ainda aponta evidência ausente em SPEC-0005, SPEC-0011 e SPEC-0013.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não há persistência de produto; apenas specs e evidências versionadas no repositório.

### Riscos e dependências

**Análise preliminar:** Reescrever histórico pode fabricar evidência; relaxar o gate global indiscriminadamente pode esconder regressões reais.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Inventariar falhas por spec, distinguir incompatibilidade de schema de evidência realmente ausente e definir migração ou grandfathering explícito.

## Pontos a revisar no futuro

**A revisar:** Escolher política para specs concluídas antes do Evidence Contract atual e critérios para aceitar ou reconstruir evidência histórica.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
