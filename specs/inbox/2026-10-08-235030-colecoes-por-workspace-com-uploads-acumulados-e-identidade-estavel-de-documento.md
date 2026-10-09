# Inbox: Coleções por workspace com uploads acumulados e identidade estável de documento

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-08T23:50:30Z |
| Slug | colecoes-por-workspace-com-uploads-acumulados-e-identidade-estavel-de-documento |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `c467886a8e5b6a63d1c09574fabf07126b82a9b354688154492be730b6fd47b6` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Pergunta inicial: "se eu colocar um novo documento e colocar o mesmo nome de uma coleção que ja tem no Qdrant o que acontece? substitui o anterior ou complementa?"

Depois: "se eu subir o mesmo arquivo ( duplicado) o que acontece?" e "mas o que funciona melhor quando o projeto estiver em produção? posso usar as 2 alternativas? hoje não me preocupo com as informações porque estou em teste".

Proposta do usuário: "um ponto que percebi, o nome da coleção deve ser definido quando for subir o primeiro documento, assim todos os documentos que subir nesse mesmo nome seguem para a mesma coleção. assim temos o workspace e no workspace podemos ter mais de uma coleção e nele vamos subindo os arquivos. faz sentido?"

Sobre fixar o chunking por coleção: "o chunks não acho que deve ser fixo porque posso usar documentos completamente diferentes por isso eu escolho como quero fazer o processamento se é por markdown, caracteres etc."

Sobre a remoção individual de documentos (apresentada como lista de documentos da coleção com ação de apagar em cada um) e o conjunto consolidado: "isso que eu quero...."

Conjunto confirmado pelo usuário: modelo workspace → coleções → arquivos; modelo de embedding e conexão fixos por coleção; chunking escolhido por upload; remoção individual de documento; correção do bug do identificador de documento.

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Trocar o modelo atual (cada upload vira uma Base isolada) por coleções nomeadas dentro do workspace, que acumulam arquivos em uploads sucessivos sem duplicar, com remoção individual de documentos.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Declaração (diagnóstico conferido no código em 2026-10-08): cada upload cria uma Base nova (src/app/routers/bases.py) e o escopo de sincronização é tenant::project::base_id (src/app/tasks.py, scope_project_id). Subir várias vezes na mesma coleção gera escopos separados; o modo mirror só limpa o próprio upload e não remove documentos de uploads anteriores; o mesmo arquivo enviado duas vezes duplica chunks em qualquer modo. Bug adicional: document_id deriva de caminho_relativo, que inclui a pasta temporária aleatória do upload (src/pipeline/loader.py:88 + src/pipeline/identity.py); teste confirmou document_id diferente para o mesmo doc.md em dois envios (base-7-HaYB/doc.md → 0093c04e-…; base-7-sMpE/doc.md → 9282e935-…).

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Usuário responsável pelo projeto, que publica documentos nos workspaces. Inferência: consumidores das buscas RAG, afetados por trechos duplicados ou desatualizados.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Coleção estável por workspace: mesmo arquivo com mesmo conteúdo não duplica nem regera embedding; mesmo nome com conteúdo novo substitui a versão anterior; documento novo é somado; documento obsoleto pode ser apagado individualmente. Inferência: menor custo de embeddings e respostas sem informação velha.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: workspace contém várias coleções; o nome da coleção é definido no primeiro upload e uploads seguintes com o mesmo nome vão para a mesma coleção. Declaração: chunking/processamento NÃO é fixo da coleção — escolhido a cada upload (markdown, caracteres etc.). Declaração (confirmada com 'isso que eu quero'): modelo de embedding e conexão do vector store fixos por coleção, definidos no primeiro upload; tela da coleção lista documentos com ação de apagar por documento; identidade do documento derivada do nome do arquivo, preservando document_id do frontmatter quando presente. Inferência: nome único por workspace e nome físico no Qdrant prefixado pelo workspace para evitar colisão entre workspaces no mesmo servidor. Inferência: escopo de sincronização passa a ser a coleção, não o upload. Recomendação discutida: em produção, append para acréscimos + remoção individual; mirror deixa de ser necessário no dia a dia.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Nova entidade Coleção no workspace (nome, nome físico no Qdrant, conexão de embeddings, conexão de vector store, dimensão); vínculo upload/Base → Coleção; inventário de documentos por coleção (nome do arquivo, document_id, source_hash, chunking usado, data) para listar e apagar; possível revisão do modelo Base atual (src/app/models.py) e de .specsfy/DATABASE.md.

### Riscos e dependências

**Análise preliminar:** Bases de teste existentes ficam incompatíveis com a nova identidade (usuário declarou que os dados atuais são de teste e podem ser descartados). Dependência: SPEC-0029 em andamento mexe em ingestão, bases e qdrant.py. Risco: mirror sobre a coleção inteira com lote parcial apagaria documentos; precisa de aviso claro ou deixar de ser padrão. Risco: mudar o modelo de embedding de uma coleção existente quebraria a busca — deve ser bloqueado.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Backlog/spec para: (1) entidade Coleção por workspace e fluxo de upload com seleção ou criação de coleção; (2) escopo de sincronização por coleção; (3) identidade estável de documento por nome do arquivo; (4) lista de documentos da coleção com remoção individual; (5) revisão do padrão append/mirror com aviso antes de remover. Possível fatiar o item 3 como correção isolada.

## Pontos a revisar no futuro

**A revisar:** Como migrar ou descartar as Bases atuais; se o conceito Base continua existindo (como registro de upload/execução) ou é substituído; se o mirror continua disponível e com qual aviso; regra de nome físico da coleção no Qdrant; o que acontece ao apagar uma coleção inteira; renomear coleção é permitido?; permissões para apagar documento; telas e navegação da coleção (contrato de interface e CRUD).

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
