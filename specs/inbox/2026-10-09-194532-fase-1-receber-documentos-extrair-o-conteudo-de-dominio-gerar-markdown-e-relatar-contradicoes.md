# Inbox: Fase 1: receber documentos, extrair o conteúdo de domínio, gerar Markdown e relatar contradições

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-09T19:45:32Z |
| Slug | fase-1-receber-documentos-extrair-o-conteudo-de-dominio-gerar-markdown-e-relatar-contradicoes |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `c71ab32494dd9ecda52554ef3206999869f562c0e10f751e938e82d2c7bc1fde` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

vc entendeu o processo? nós fizemos a segunda parte que é pegar os arquivos .md, quebrar em chunks e subir no bd vetorial. agora falta a primeira parte que é receber os arquivos com as informaçoes que podem vir em docs, html, pdf ppt , url, extrair as informações dominio, isso é as informações dos documentos e não as informações acessorios como numero de pagina etc. depois dessa extração, criar os .md e analisar todos para ver se não existe informações que são contraditorias, se existir gerar um relatorio com essas informaçoes contraditorias e de quais arquivos sairam para conferir com a empresa que forneceu as informações para verificar o que esta valendo. atualizar os arquivos .md e deixar prontos para a segunda parte. entendeu? isso esta nos documentos do projeto?

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Implementar a primeira parte do pipeline: receber documentos (doc, html, pdf, ppt, url), extrair só a informação de domínio, gerar os .md, detectar informações contraditórias entre eles, gerar relatório com os arquivos de origem para conferir com a empresa fornecedora e atualizar os .md para a segunda parte (chunks e base vetorial).

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** A segunda parte (md, chunks, base vetorial) está pronta; falta a primeira. Hoje o envio só aceita .md e src/pipeline/conversion/converters está vazio. PROJECT.md cita a Fase 1 e lista como limite a ausência de ingestão multi-formato, curadoria cruzada e detecção de contradições.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Pessoa que prepara a base de conhecimento a partir de documentos de uma empresa cliente; a empresa fornecedora das informações confere o relatório (declarado).

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Chegar à segunda parte com .md só com informação de domínio, sem contradições não resolvidas, com origem rastreável.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Formatos de entrada declarados: docs, html, pdf, ppt e url. Extrair apenas informação de domínio, excluindo acessórios como número de página. Análise conjunta de todos os .md para achar contradições. Relatório com a informação contraditória e os arquivos de origem. Atualização dos .md após a conferência com a empresa. Saída: .md prontos para a segunda parte.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Possível necessidade de guardar o documento original, o .md gerado, as contradições encontradas com seus arquivos de origem, a decisão da empresa sobre qual informação vale e a versão atualizada do .md. Não confirmado.

### Riscos e dependências

**Análise preliminar:** Definição detalhada da Fase 1 está na constituição, briefing e tech stack do projeto-mãe, que não estão no repositório; o M01 está fechado, então o marco é a decidir; sobreposição possível com a skill doc-rag-analyzer e com o contrato Markdown (SPEC-0002); a conferência com a empresa é um passo humano fora do sistema.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Backlogs separados por capacidade: (1) conversão multi-formato e url para .md; (2) extração só do conteúdo de domínio; (3) detecção de contradições e relatório com origem; (4) ciclo de conferência e atualização dos .md. Marco de roadmap a decidir.

## Pontos a revisar no futuro

**A revisar:** Obter o briefing e a constituição da Fase 1; formatos e limites de tamanho; o que conta como informação acessória; critério de contradição; formato do relatório; como a decisão da empresa volta ao sistema; se roda antes do envio ou no worker; relação com a captura de 2026-10-09-192547 e com os envios por coleção da SPEC-0030.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
