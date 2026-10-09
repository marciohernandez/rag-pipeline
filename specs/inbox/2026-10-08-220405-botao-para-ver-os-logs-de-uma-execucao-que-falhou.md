# Inbox: Botão para ver os logs de uma execução que falhou

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-08T22:04:05Z |
| Slug | botao-para-ver-os-logs-de-uma-execucao-que-falhou |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `2c7828c12adcd11144554966d685cd966338ca45304da27d53200f66a8fa99c4` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

acho importante ter um botçao para ver os logs

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Na tela da execução, oferecer um botão para ver os logs ou o motivo detalhado da falha, em vez de só 'ver logs do worker para detalhes'.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Quando a execução falha, a tela diz apenas 'Falha ao processar a base; ver logs do worker para detalhes', e a pessoa não tem acesso a esses logs pela interface.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Owner/admin que publica Bases e acompanha execuções.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Entender e corrigir a falha sem acesso ao servidor.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: botão para ver os logs. Contexto (2026-10-08): execução falhou na etapa indexando com UnexpectedResponse do Qdrant; o log do worker registra só o tipo do erro; a causa real era 401 'Must provide an API key' de um Qdrant externo cadastrado sem chave. A SPEC-0026 deixou 'Testar conexão' fora de escopo.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Possível guardar por execução um motivo de falha legível e sem segredos.

### Riscos e dependências

**Análise preliminar:** Logs podem conter URLs, chaves ou conteúdo de documentos; exibir só mensagens sanitizadas e para papéis de escrita.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Motivo de falha legível na execução (ex.: 'o Qdrant recusou a gravação: falta a chave de API'); painel de logs da execução; botão 'Testar conexão' no cadastro de conexões.

## Pontos a revisar no futuro

**A revisar:** Quais logs mostrar (só da execução ou do worker); retenção; quem pode ver; formato do motivo de falha; incluir Testar conexão no mesmo item.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
