# Inbox: Duplicidade ignora documentos com o mesmo nome no mesmo lote

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-23T13:44:39Z |
| Slug | duplicidade-ignora-documentos-com-o-mesmo-nome-no-mesmo-lote |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `47c6f32199919f1852bc2a6065b46a2dabe7443a3d79ec17665638a4cc260476` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Verificação feita a pedido da pessoa ("coloquei 2 documentos iguais mas no relatorio diz duplicidades nenhuma"): num teste offline com o .md real, dois documentos iguais com nomes diferentes geram 170 exclusões por duplicidade, mas dois documentos iguais com o mesmo nome geram 0.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** A camada de duplicidade trata documentos de mesmo nome como o mesmo arquivo e pula a comparação, então duas cópias do mesmo arquivo no mesmo lote não são detectadas.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Em src/pipeline/limpeza/duplicidade.py, o laço de comparação tem if origem == arquivo: continue, e em src/app/limpeza.py os documentos são indexados por _nome_md (por_nome e dict(textos)). Dois documentos com o mesmo nome no mesmo lote colidem. Duas cópias do mesmo arquivo têm exatamente o mesmo nome, o caso mais comum de duplicidade.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoa da consultoria (owner/admin) que envia vários arquivos num único lote.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Dois arquivos iguais num mesmo lote são apontados como duplicados mesmo com nomes iguais.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: resultado do teste offline (nomes diferentes: 170 exclusões e 1 provável; mesmo nome: 0 e 0). Não confirmado: se o envio de conversão aceita dois arquivos com o mesmo nome no mesmo lote, o que depende da validação da rota de conversão. Inferência: pode ser um defeito latente da SPEC-0037, sem ocorrência confirmada em uso real.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Corrigir exige identificar o documento por id e não pelo nome em limpeza.py e em duplicidade.py; mexe na SPEC-0037 já concluída. Outros pontos que usam o nome como chave podem ter o mesmo problema.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Possível spec de correção da SPEC-0037, com teste para dois documentos de mesmo nome. Nada promovido.

## Pontos a revisar no futuro

**A revisar:** A rota de conversão aceita dois arquivos com o mesmo nome no mesmo lote? Se aceita, como o sistema os distingue hoje? A correção deve usar o id do documento?

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
