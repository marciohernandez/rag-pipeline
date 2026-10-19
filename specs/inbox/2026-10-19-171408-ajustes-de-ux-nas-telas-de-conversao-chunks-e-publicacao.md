# Inbox: Ajustes de UX nas telas de conversão, chunks e publicação

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-19T17:14:08Z |
| Slug | ajustes-de-ux-nas-telas-de-conversao-chunks-e-publicacao |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `0da913324cfc9b8a5735b59ee73f835d1dc3b8416f9d85c144a0cfbe18b91aeb` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Observações do usuário sobre as telas (print anotado): (1) Para que serve o Resumo do domínio? O que ele faz? O que faz o check 'permitir análise por IA externa'? Inverter a posição entre Coleções e Conversão de Documentos. (2) Não consigo voltar (tela com erro em vermelho). (3) Em converter documentos há o botão relatório do lote. É muito importante ter, no local onde estão todos os documentos convertidos, um botão para gerar relatório que inclua todos esses documentos convertidos, não apenas por lote, porque haverá momentos em que vamos converter documentos em momentos separados e preciso que seja possível fazer esse relatório. E também preciso saber onde coloco a resposta quando houver dúvidas, duplicidades, contradições para que esses documentos já convertidos sejam atualizados. (4) A divisão dos chunks deve estar um pouco mais aparente; fica difícil saber onde termina um chunk e onde começa o outro. Também saber [anotação cortada no print]. (5) Me explique o que são os embeddings falsos. Quando clicar em uma das opções de conexões deve ser possível entrar na tela da conexão para confirmar o que está lá e se precisar editar. Não consigo publicar, por quê?

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Lista de observações de usabilidade sobre conversão, relatórios, divisão de chunks, conexões e publicação.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Relatório só por lote; respostas a dúvidas/duplicidades/contradições sem local claro; chunks sem separação visível; conexões não editáveis a partir do select; mensagens e placeholders confusos na publicação.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoa que converte e publica documentos no Workspace.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Fluxo de conversão e publicação mais claro e controlável.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Relatório de todos os documentos convertidos; local para responder dúvidas e atualizar documentos convertidos; separador visual de chunks; abrir/editar conexão a partir do select; ordem do menu Coleções/Conversão; botão voltar; placeholder do nome da coleção.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Relatório consolidado e respostas a dúvidas associadas a documentos convertidos podem precisar ser guardados.

### Riscos e dependências

**Análise preliminar:** Atualizar documentos já convertidos a partir de respostas pode exigir reprocessamento; depende do fluxo de decisões existente.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Itens 3, 4 e 5 (conexão editável) como features; itens de menu, voltar e placeholder como correções pequenas.

## Pontos a revisar no futuro

**A revisar:** Em qual tela o 'Não consigo voltar' ocorre; conclusão da anotação cortada do item 4; escopo do relatório (filtros por período/documento).

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
