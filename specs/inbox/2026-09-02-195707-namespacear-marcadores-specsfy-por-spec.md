# Inbox: Namespacear marcadores SPECSFY por spec

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-09-02T22:57:07Z |
| Slug | namespacear-marcadores-specsfy-por-spec |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `281bdef00a603571a51cc17c752d590f44db7141b8395e4a5608e3a1df349726` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Os marcadores SPECSFY nos testes não dizem a qual spec pertencem. Como cada spec numera seus IDs do zero, US-001, FR-001 e AC-003 existem em várias specs ao mesmo tempo. O check_traceability varre todos os arquivos de teste, então marcadores da SPEC-0003 são contados como cobertura da SPEC-0004 e vice-versa. Hoje a mitigação é isolar cada fatia em arquivo de teste próprio, o que funciona mas depende de disciplina. A correção real seria namespacear o marcador, algo como SPECSFY: SPEC-0004 AC-003, e ajustar o auditor.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** IDs repetidos entre specs fazem o auditor contar cobertura de uma fatia como se fosse de outra.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** US-001, FR-001 e AC-003 existem em várias specs; o auditor não distingue a origem do marcador.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Quem valida gates e confia na contagem de cobertura.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** A contagem de cobertura passa a refletir apenas os casos da fatia auditada.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: check_traceability varre todos os arquivos de teste. Declaração: a mitigação atual é isolar cada fatia em arquivo próprio. Inferência: a correção pertence ao framework Specsfy, não a este repositório de produto.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Dependência: mudar o formato do marcador exige ajustar o auditor e os testes já marcados das specs 0001 a 0004.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Proposta ao framework Specsfy; enquanto isso, manter a convenção de arquivo por fatia.

## Pontos a revisar no futuro

**A revisar:** Confirmar se o repositório de produto pode mudar a convenção sozinho ou se depende de release do framework.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
