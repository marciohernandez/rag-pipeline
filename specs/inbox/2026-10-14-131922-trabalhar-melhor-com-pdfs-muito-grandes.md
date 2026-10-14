# Inbox: Trabalhar melhor com PDFs muito grandes

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-14T13:19:22Z |
| Slug | trabalhar-melhor-com-pdfs-muito-grandes |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `213d0b5de917526cfd716e87d4b445bef980bd43819260fed0814fb29192f9c9` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

depois precisamos encontrar um forma melhor de trabalhar com documentos  muito grandes de PDF. deixa no inbox.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Documentos PDF muito grandes precisam de uma forma melhor de tratamento do que o limite simples de páginas com OCR decidido para o item 0045.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** PDFs muito grandes, como contratos de centenas de páginas, ocupam o worker por muito tempo no OCR e na extração; o item 0045 só os limita (as páginas além do limite saem sem OCR, com aviso), o que deixa conteúdo de fora. A pessoa quer uma forma melhor de lidar com eles, ainda não definida.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Marcio e a equipe de consultoria, que recebem documentos grandes (declaração indireta: o tema surgiu ao discutir o limite de páginas do OCR).

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Documento grande convertido por inteiro, sem travar o processamento dos demais documentos do lote.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: é preciso achar uma forma melhor de trabalhar com PDFs muito grandes, para depois. Inferência: pode envolver dividir o PDF em partes processadas em paralelo, processar por página em fila, mostrar o progresso por página ou aceitar a continuação do OCR de onde parou; nada disso foi confirmado.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Possível necessidade de guardar o progresso por página ou por parte do documento; não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Tempo de worker e memória em PDFs grandes; risco de atrasar os demais documentos do lote; custo de reprocessar do zero em caso de falha no meio; depende do limite de páginas decidido no backlog 0045.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Processamento por partes ou por página com progresso visível; continuar de onde parou; limite configurável; dividir o documento antes do envio como alternativa de contorno.

## Pontos a revisar no futuro

**A revisar:** Qual o tamanho típico dos documentos grandes que a equipe recebe; se o limite de páginas do item 0045 é suficiente no começo; se o progresso por página precisa aparecer na lista; se o reprocessamento parcial importa.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
