# Inbox: Limpeza por regras não remove aviso repetido que começa com asteriscos

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-23T12:48:49Z |
| Slug | limpeza-por-regras-nao-remove-aviso-repetido-que-comeca-com-asteriscos |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `2bedc8ab50581d178de1d0c1746cccff813762471bcf4ba3efc294aa7c2588e5` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Primeiro ciclo do gabarito M04 (doc-01, regulamento_regras_das_categorias_de_clientes_vivo_beneficios_v6_20241213.pdf): os avisos de classificação "***Este documento está clasificado como PUBLICO por TELEFÓNICA." e "***This document is classified as PUBLIC by TELEFÓNICA." continuam no .md depois da limpeza por regras (IA externa desligada), repetidos 13 vezes cada (corrigido em 2026-10-23; o texto anterior dizia 5 por leitura parcial do arquivo, e o resultado se repetiu num segundo envio do mesmo PDF). O parágrafo de negócio dos Vivinhos foi preservado.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** A regra de linha repetida da limpeza ignora linhas iniciadas por *, -, #, | ou >, então um aviso de classificação que começa com *** nunca é removido, mesmo repetido várias vezes.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** No primeiro documento real do gabarito do M04, 0 de 2 trechos de ruído foram removidos (meta provisória: 80%), embora o negócio tenha sido preservado (0 removidos, alvo 0). Causa observada em src/pipeline/limpeza/regras.py: candidatas a rodapé excluem linhas que começam com *, -, #, |, > ou crase tripla, para proteger listas e negrito.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoa da consultoria (owner/admin) que converte e revisa documentos de uma empresa.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Avisos e rodapés repetidos que começam com marcação Markdown também saem na limpeza por regras, sem apagar listas nem negrito de negócio.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: amostra de 1 documento; os dois avisos ficaram; 36 exclusões foram feitas, todas pela regra de linha repetida (blocos de picture text, Confira o regulamento completo, Regras de uso, links de loja e eventos). Inferência: algumas dessas 36 podem ser conteúdo útil; a pessoa não confirmou. A amostra é pequena e não prova a taxa geral.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Relaxar a exclusão por prefixo pode apagar itens de lista ou texto em negrito de negócio; precisa de teste com documentos reais. Relacionado a SPEC-0037 (limpeza) e ao gabarito do M04.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Possível ajuste da regra de linha repetida ou nova regra para avisos de classificação; possível spec de correção da SPEC-0037. Nada promovido.

## Pontos a revisar no futuro

**A revisar:** Quais das 36 exclusões foram indevidas? Repetir com mais documentos antes de decidir? Tratar só linhas repetidas que começam com ***, ou qualquer prefixo? Religar a IA melhora o resultado?

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
