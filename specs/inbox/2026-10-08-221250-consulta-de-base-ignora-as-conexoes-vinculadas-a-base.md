# Inbox: Consulta de Base ignora as conexões vinculadas à Base

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-08T22:12:50Z |
| Slug | consulta-de-base-ignora-as-conexoes-vinculadas-a-base |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `41e63057efbf73a3311ca50c7fead2bda3df3584b2765992b179425cfd2a1049` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Registro do agente ao concluir a SPEC-0028 (DEC-004), em 2026-10-08: a consulta de uma Base (src/app/routers/queries.py) usa a configuração global de embeddings e vector store com o collection_name da Base, mas ignora as conexões vinculadas à Base desde a SPEC-0026.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Consultar uma Base indexada em um Qdrant de conexão própria usa o Qdrant e os embeddings globais, e não os da conexão.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Bases publicadas com conexão própria (ex.: Qdrant externo) são consultadas no destino errado e podem devolver vazio ou erro.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoa que consulta Bases pela tela da Base.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Consultar cada Base no mesmo destino e com o mesmo modelo de embeddings usados na indexação.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Evidência: src/app/routers/queries.py monta embedding e vector_store a partir de settings; a SPEC-0028 criou configuracao_vector_store_da_base em src/app/tasks.py, reutilizável para o vector store; a consulta também precisa da conexão de embeddings da Base para gerar o vetor da pergunta.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Decifrar a chave de embeddings na consulta; manter o segredo fora de logs e respostas; Bases legadas sem conexões devem manter o comportamento.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Spec pequena reaproveitando configuracao_vector_store_da_base e uma função equivalente para embeddings.

## Pontos a revisar no futuro

**A revisar:** Confirmar o comportamento atual consultando a Base 'teste vivo', publicada no Qdrant externo.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
