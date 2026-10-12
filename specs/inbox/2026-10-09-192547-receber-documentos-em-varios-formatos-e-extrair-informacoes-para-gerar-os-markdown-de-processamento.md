# Inbox: Receber documentos em vários formatos e extrair informações para gerar os Markdown de processamento

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-09T19:25:47Z |
| Slug | receber-documentos-em-varios-formatos-e-extrair-informacoes-para-gerar-os-markdown-de-processamento |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `0ff9b4befa4f80ff5b8cbc676bec942b747da3e42b67632a8068a0a7488736f4` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

o que eu quero é: fazer implementação da parte inicial do sistema, a qual recebe os documentos em diversos formatos, extraia as informações ( dominio, acho que é assim que fala) para perar os .md para preocessamento.

(Mensagem anterior do mesmo pedido: "agora preciso de foco no M1 para desenvolver a parte de processamento de documentos, extração de informaçoes, relatorio comparativo se existe informações contraditorias até gerar os documentos .md prontos para fazer a quebra de chunks e p upsert na base vetorial.")

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Implementar a etapa inicial do sistema: receber documentos em diversos formatos, extrair as informações do domínio e gerar os .md que alimentam a quebra em chunks e o upsert na base vetorial.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Hoje o envio só aceita arquivos .md (src/app/ingestao.py) e src/pipeline/conversion/converters está vazio; a etapa de receber outros formatos e extrair informações não existe no código. Inferência.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoa que prepara documentos para a base vetorial (inferência: equipe de consultoria que usa o sistema).

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Gerar documentos .md prontos para o chunking e o upsert na base vetorial a partir de documentos em diversos formatos.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Entrada em diversos formatos; extração de informações do domínio; geração de .md; relatório comparativo de informações contraditórias (mencionado na mensagem anterior); etapa seguinte já existente: chunks e upsert.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Possível necessidade de guardar o documento original, o .md gerado, as informações extraídas e o relatório de contradições. Não confirmado.

### Riscos e dependências

**Análise preliminar:** Dependência da coleção e do envio (SPEC-0030); possível sobreposição com a skill doc-rag-analyzer e com o contrato Markdown do projeto-mãe (SPEC-0002); o M01 está fechado e não é reaberto.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Backlog de conversão multi-formato para .md; backlog de extração de informações do domínio; backlog do relatório de contradições; vínculo a um marco de roadmap a decidir.

## Pontos a revisar no futuro

**A revisar:** Quais formatos entram; o que significa extrair informações do domínio; se o relatório de contradições faz parte desta entrega; onde a etapa roda (antes do envio ou no worker); em qual marco entra, já que o M01 está fechado.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
