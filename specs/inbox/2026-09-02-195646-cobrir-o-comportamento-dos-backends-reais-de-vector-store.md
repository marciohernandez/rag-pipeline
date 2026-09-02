# Inbox: Cobrir o comportamento dos backends reais de vector store

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-09-02T22:56:46Z |
| Slug | cobrir-o-comportamento-dos-backends-reais-de-vector-store |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `c88ed5bdba547943ecdb12630c813baa2030a108698c1e7913e4609db47b7e51` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Nenhum teste do repositório exercita as classes reais de backend: _QdrantBackend, _ChromaBackend e _PineconeBackend. Toda a suíte de providers injeta FakeVectorBackend como cliente, então _create_backend() nunca roda e o código que fala com cada SDK só é executado em produção. A SPEC-0004 cobriu a superfície das cinco operações do port e o comportamento de describe, mas ensure, write, search e scope_ids continuam sem prova de comportamento. Cada backend tem um _conn() que permite injetar um cliente-dublê do SDK, então dá para cobrir sem rede.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Os backends que falam com Qdrant, ChromaDB e Pinecone nunca são executados por teste algum.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** A suíte prova a delegação do adapter base sobre um fake; erro na tradução para o SDK só aparece em produção.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Quem opera o pipeline e quem trocar de provider.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Erro de integração com SDK passa a falhar no teste, e não durante uma sincronização real.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: _create_backend() nunca roda com cliente injetado. Declaração: SPEC-0004 cobriu superfície das cinco operações e comportamento de describe. Inferência: o seam _conn() permite dublê de SDK sem rede.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Dependência: contratos e adapters entregues pela SPEC-0003. Relação: a SPEC-0004 abriu o precedente ao cobrir describe.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Fatia de robustez sobre src/providers/vectorstores, com dublês de SDK por backend.

## Pontos a revisar no futuro

**A revisar:** Definir se o dublê imita o SDK real ou um subconjunto; decidir se vale teste de integração opcional contra serviço real.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
