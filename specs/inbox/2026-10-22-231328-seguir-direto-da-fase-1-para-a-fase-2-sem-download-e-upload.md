# Inbox: Seguir direto da Fase 1 para a Fase 2 sem download e upload

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-22T23:13:28Z |
| Slug | seguir-direto-da-fase-1-para-a-fase-2-sem-download-e-upload |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `3b47ad4fb67465dd6718be641747e6f0e0997f16009cd93273d643495ff90f29` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

eu quero poder usar os documenteos em .md criados na primeira fase diretemamento ao inves de fazer download e upload novamente. ter a opção de seguir direto, mas como opção.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Permitir usar os .md gerados na Fase 1 diretamente na Fase 2, sem baixar e subir de novo, mantendo o fluxo atual como opção.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Hoje é preciso baixar os .md da Fase 1 e enviá-los novamente para indexar, um desvio manual sem valor agregado.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoa da consultoria que processa os documentos e indexa a coleção (Marcio e equipe).

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Menos passos manuais entre as fases e uso garantido da versão revisada dos .md.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: usar os .md da Fase 1 diretamente; seguir direto é uma opção, não substitui o caminho atual. Inferência: ponto natural pode ser a coleção liberada para a base (M04); a Fase 2 já existe (chunks e upsert).

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Os .md da Fase 1 já ficam no sistema; talvez seja preciso consultar quais documentos e qual coleção alimentam a indexação.

### Riscos e dependências

**Análise preliminar:** Indexar gera embeddings e tem custo; reindexar após alterar os .md; relação com SPEC-0039 (Liberar para a base) e SPEC-0030 (coleções).

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Ação opcional na coleção liberada para indexar os .md existentes, com confirmação, mantendo o upload manual.

## Pontos a revisar no futuro

**A revisar:** Coleção de destino: a mesma ou outra? Exigir coleção liberada? Comportamento ao alterar .md depois de indexar? Confirmação e exibição de custo?

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
