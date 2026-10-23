# Inbox: Detectar duplicidade entre lotes de conversão do mesmo Workspace

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-23T13:44:39Z |
| Slug | detectar-duplicidade-entre-lotes-de-conversao-do-mesmo-workspace |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `f8f606872b3a1c7882a394190aabfb9255ce71301739d74bcedc53fdb9045c52` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

coloquei 2 documentos iguais mas no relatorio diz duplicidades nenhuma (o mesmo PDF foi enviado em dois envios separados, cada um virou um lote com 1 documento)

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** A pessoa enviou o mesmo PDF duas vezes em envios separados e o relatório de cada lote disse que não há duplicidades; a camada de duplicidade só compara documentos dentro do mesmo lote.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Cada envio de conversão cria um lote, e finalizar_limpeza_lote compara só os documentos do próprio lote (src/app/limpeza.py, src/pipeline/limpeza/duplicidade.py, SPEC-0037 FR-006). Um documento igual a outro já convertido em lote anterior do Workspace não é apontado. O relatório diz duplicidades nenhuma, o que a pessoa leu como falha grave.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoa da consultoria (owner/admin) que envia documentos de uma empresa em vários lotes.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Saber, no relatório ou na coleção, quando um documento já foi enviado antes no mesmo Workspace, sem depender de ele estar no mesmo lote.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: dois documentos iguais, relatório com duplicidades nenhuma. Observado no banco de desenvolvimento: dois lotes distintos (12:43 e 13:25 de 2026-10-23), cada um com 1 documento; os .md convertidos são byte a byte idênticos. Inferência: o comportamento está de acordo com a SPEC-0037, e o que a pessoa esperava (comparar entre lotes) é uma funcionalidade nova. Possível mensagem mais clara no relatório quando o lote tem só um documento.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Provável necessidade de lembrar uma impressão do conteúdo de cada documento já convertido por Workspace (a confirmar em conversa futura).

### Riscos e dependências

**Análise preliminar:** Arquivos do lote expiram em 7 dias, então a comparação com lotes antigos precisa de uma impressão guardada, não do arquivo. Comparar entre lotes toca privacidade e retenção. Relacionado a SPEC-0037, SPEC-0043 (origem do documento indexado) e a coleção, que também poderia acusar duplicidade na indexação.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Possível spec para duplicidade entre lotes e/ou aviso na indexação; possível texto do relatório explicando que a comparação é só dentro do lote. Nada promovido.

## Pontos a revisar no futuro

**A revisar:** Comparar com lotes anteriores do Workspace, com documentos já indexados na coleção, ou ambos? O que fazer ao achar: só avisar ou excluir? Por quanto tempo guardar a impressão do documento? O relatório de lote de 1 documento deve dizer que não há com quem comparar?

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
