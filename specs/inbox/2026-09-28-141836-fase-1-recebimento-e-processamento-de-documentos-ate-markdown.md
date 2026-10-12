# Inbox: Fase 1: recebimento e processamento de documentos até Markdown

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-09-28T17:18:36Z |
| Slug | fase-1-recebimento-e-processamento-de-documentos-ate-markdown |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `435ee33f4725d83d5354a56bdb8a9875fda8bc6073cc13003ff39713881bb73f` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

vamos trabalhar na fase um do sistema, recebimento dos documentos e todo o processamento, extração das informações até o momento de colocar em arquivo .md para estarem prontos para seguir a fase 2

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Construir a Fase 1 do sistema: receber documentos, processá-los e extrair suas informações, entregando um arquivo .md pronto para alimentar a Fase 2 (chunking/embeddings/Qdrant) já existente.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Não identificado explicitamente no texto original. Inferência: hoje o sistema (Fase 2) só processa arquivos .md já prontos, colocados manualmente na pasta configurada; não existe nenhuma etapa que receba documentos originais (outros formatos) e os transforme em Markdown.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Não identificado no texto original. Inferência: as mesmas pessoas que hoje preparam e enviam Bases (Marcio e equipe de consultoria), que passariam a poder enviar documentos originais em vez de já ter um .md pronto.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Uma pessoa consegue enviar documentos originais e obter automaticamente um Markdown estruturado, pronto para a Fase 2, sem converter manualmente para .md antes.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Escopo mencionado: 'recebimento dos documentos', 'todo o processamento', 'extração das informações', saída em 'arquivo .md'. Não especifica formatos de entrada aceitos, fontes de recebimento (upload? pasta? integração?), nem regras de extração.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original. Inferência: documentos originais recebidos (formato, origem) e os .md gerados precisarão de algum rastro/identidade para conectar com a Fase 2 (já existe conceito de Base/execução na Fase 2).

### Riscos e dependências

**Análise preliminar:** Decisão já tomada nesta conversa: construir dentro do repositório rag-pipeline atual, expandindo o escopo hoje documentado em PROJECT.md (que hoje declara explicitamente que ingestão multi-formato é 'prevista para o projeto-mãe' e está fora de escopo deste componente). Nenhum repositório relacionado (rag-ingestion-pipeline, rag-pipeline-old) tem essa capacidade implementada — é trabalho novo. Risco: PROJECT.md precisará ser revisado para refletir a mudança de escopo.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Aprofundar no backlog: formatos de documento aceitos, forma de recebimento (upload via frontend? pasta? API?), o que conta como 'processamento' e 'extração de informações', se há detecção de contradições/validação humana (mencionada em registros anteriores do projeto-mãe), e como o .md gerado se conecta à Base/execução da Fase 2 já existente.

## Pontos a revisar no futuro

**A revisar:** Formatos de entrada não especificados. Definição de 'processamento' e 'extração' não especificada. Relação entre esta nova etapa e o conceito de Base/Workspace/execução já existente na Fase 2 não especificada.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
