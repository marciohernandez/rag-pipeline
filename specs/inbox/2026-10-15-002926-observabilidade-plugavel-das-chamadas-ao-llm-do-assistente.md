# Inbox: Observabilidade plugável das chamadas ao LLM do assistente

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-15T00:29:26Z |
| Slug | observabilidade-plugavel-das-chamadas-ao-llm-do-assistente |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `ccc6685756ba2d4d9f97bacca0099b805cba756f9525e8b880e034170dbe6334` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Observabilidade plugável das chamadas ao LLM do assistente. Resgatado da SPEC-0020 (branch spec/0020-chat-com-assistente-especialista-em-rag-fatia-1-memoria-de-projeto, FR-008), que foi descartada porque o chat foi entregue pela SPEC-0021, mas sem este item. Ideia: registrar cada chamada ao provider de LLM (grounding e geração de resposta) por um mecanismo de observabilidade plugável, com contrato neutro (ex.: src/app/assistant/observability.py, ObservabilityProvider.record(trace)), no mesmo padrão contrato + factory + adapter já usado para embeddings, vector store e provider de LLM. Primeira implementação real: adapter Langfuse. Só liga por configuração explícita; o padrão é um adapter nulo (opt-in). Quando ligado envia prompt e resposta completos, latência e erro, escopado por tenant_id/project_id e pela conversa de origem. Hospedagem e retenção ficam com quem configura o serviço, e a documentação deve listar o que é enviado. Origem das decisões: respostas de 2026-09-21 na spec 0020 (opção 1). Nada disso existe na main hoje.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Registrar prompt, resposta, latência e erro de cada chamada ao LLM do assistente por um contrato de observabilidade plugável, desligado por padrão.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** O assistente de chat (SPEC-0021) já está em produção sem forma de observar as chamadas ao LLM; o item FR-008 da SPEC-0020 descartada previa isso e não foi entregue.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Não identificado no texto original.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Poder diagnosticar qualidade, custo e falhas das respostas do assistente, sem acoplar o código a um serviço específico.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Contrato neutro ObservabilityProvider.record(trace) com factory e adapters; adapter nulo como padrão (opt-in por configuração); primeiro adapter real Langfuse; escopo por tenant_id, project_id e conversa; documentação lista o que é enviado.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Possível registro de prompt e resposta completos, latência e erro por chamada, escopado por tenant, projeto e conversa; retenção fica com o serviço externo configurado.

### Riscos e dependências

**Análise preliminar:** Envio de prompt e resposta completos a um serviço externo (privacidade, dados de clientes); dependência de serviço externo; relação com BACKLOG-0010 (provider de LLM plugável) e BACKLOG-0003 (padrão contrato + adapter).

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Refinar como item de backlog ligado ao assistente (SPEC-0021) e ao provider de LLM plugável; avaliar a conversa de dados antes de gravar qualquer traço.

## Pontos a revisar no futuro

**A revisar:** Quem são as pessoas afetadas; se o envio de prompt e resposta completos é aceitável por padrão ou só com anonimização; se há outros adapters além do Langfuse; relação exata com o backlog 0027 (memória de longo prazo).

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
