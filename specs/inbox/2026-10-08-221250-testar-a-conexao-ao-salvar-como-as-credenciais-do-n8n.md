# Inbox: Testar a conexão ao salvar, como as credenciais do n8n

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-08T22:12:50Z |
| Slug | testar-a-conexao-ao-salvar-como-as-credenciais-do-n8n |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `6d1dfc3dd364b1ad31ab11d0f1bdcffd2e55f39d52bfe93b00c45f2be4632d6a` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

deu certo. aproveitar e podemos no momento que é criado uma conexçaoi ela ser testada. se falhar já indicar que falhou, como é feito com as credenciais no n8n, vc sabe?

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Ao criar ou editar uma conexão, o sistema testa o acesso e mostra se funcionou ou qual foi a falha, como o n8n faz com credenciais.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Uma conexão Qdrant sem chave foi salva sem aviso e só falhou na indexação, com mensagem genérica.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Owner/admin que cadastra conexões de embeddings e Qdrant.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Descobrir conexões inválidas no cadastro, antes de publicar uma Base.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: testar no momento da criação e indicar a falha, como no n8n. Contexto: Qdrant externo respondeu 401 'Must provide an API key' na indexação; a SPEC-0026 deixou 'Testar conexão' fora de escopo. Relacionado à captura 2026-10-08-220405 (botão de logs).

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Possível guardar o resultado e a data do último teste da conexão.

### Riscos e dependências

**Análise preliminar:** O teste de embeddings gera uma chamada paga ao provedor; o teste não pode expor a chave em logs ou respostas; o teste não pode criar coleção no Qdrant.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Teste automático ao salvar, com resultado no painel (sucesso ou motivo da falha) e opção de salvar mesmo assim; botão Testar conexão também na lista e no detalhe; Qdrant: GET /collections com a chave; embeddings: um embedding curto conferindo a dimensão declarada.

## Pontos a revisar no futuro

**A revisar:** Se a falha impede salvar ou só avisa; se a conexão guarda o status do último teste; custo do teste de embeddings.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
