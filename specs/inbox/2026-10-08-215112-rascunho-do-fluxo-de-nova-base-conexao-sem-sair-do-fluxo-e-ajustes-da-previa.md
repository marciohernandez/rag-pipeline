# Inbox: Rascunho do fluxo de Nova Base, conexão sem sair do fluxo e ajustes da Prévia

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-08T21:51:12Z |
| Slug | rascunho-do-fluxo-de-nova-base-conexao-sem-sair-do-fluxo-e-ajustes-da-previa |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `b692b15ff232f9d121e294379d0d245477ad3b5f4b5bd7c743d2bd43cf2a81d9` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

eu quero poder salvar parte do processo se não concluir por alguma razao o que vc acha? exatamente a melhoria possivel sugerida. outr ponto, quando estiver na previsa o botçao de seguir deve ficar na parte de cima e não no final da previa para não ter que rolar a pagina até o final.e outr ponto, na previa quando haver muitos chunks tem a opção de ler 10, depois 20, 50 75 e 100. sabe como é?

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Salvar o fluxo de Nova Base incompleto para retomar depois, cadastrar conexões sem perder o progresso, botão de seguir no topo da Prévia e seletor de chunks por página (10, 20, 50, 75, 100).

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Sair do fluxo antes de publicar descarta arquivos e configurações; sem conexões cadastradas a pessoa precisa sair do fluxo; na Prévia o botão de seguir fica no fim da lista e a página mostra sempre 10 chunks.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Owner/admin que cria Bases pelo fluxo de Nova Base.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Retomar uma Base não concluída, cadastrar conexões sem perder o trabalho e revisar muitos chunks com menos rolagem.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: salvar parte do processo quando não concluir; concorda com a melhoria sugerida de cadastrar conexão dentro da Publicação. Declaração: botão de seguir no topo da Prévia. Declaração: escolher 10, 20, 50, 75 ou 100 chunks por página. Evidência: a página da Prévia usa TAMANHO_PAGINA = 10 fixo (frontend/src/features/ingestao/useFluxoIngestao.ts:40) e o backend já aceita até 100 por página (src/app/routers/ingestao.py:15); Voltar e Próxima ficam no rodapé do FluxoIngestao; a SPEC-0026 deixou rascunho, retomada e persistência de arquivos antes de publicar fora de escopo.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Rascunho exigiria guardar arquivos enviados e parâmetros antes de publicar: onde, por quanto tempo, quem vê e quando apagar.

### Riscos e dependências

**Análise preliminar:** Arquivos de rascunho ocupando storage sem limpeza; rascunhos órfãos; conflito com a regra da SPEC-0026 de nada gravar antes de publicar; BACKLOG-0036 também altera Divisão e Prévia.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Backlog próprio para rascunho e retomada, com descoberta de dados; cadastro de conexão em painel lateral na Publicação; ajustes da Prévia (ações no topo ou fixas e seletor de tamanho de página) junto do BACKLOG-0036.

## Pontos a revisar no futuro

**A revisar:** Prazo de retenção do rascunho; um ou vários rascunhos por pessoa ou por Workspace; quem pode ver e retomar; o que acontece com a Prévia salva; se a barra de ações fica fixa ao rolar.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
