# Inbox: Fluxo de ingestão inspirado nos Document Stores do Flowise

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-05T17:06:32Z |
| Slug | fluxo-de-ingestao-inspirado-nos-document-stores-do-flowise |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `e79ef03ec7f41939558aaa31cca58de8be99182633940eb84cef4df520431bd8` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

- como deve ser o processo:

1. criar workspace com nome e descrição
2. um botão para selecionar o tipo de Document Loader ( Select Document loader) exemplo na imagem. Se tivermos documentos diferenentes como fazer essa parte?. Essa fase devera ser na faze 1 onde enviamos os documentos para ser extraído as informações da domínio.
3. como inicialmente vamos ter apenas documentos .md que vão vir da fase 1 então agora para fazer o upload dos documentos sempre vamos ter o "Text File Loader ", que vem do langchain certo?
4. quando subir o arquivo definir se vai ter additionl metadata e Omit Metadate Keys. e depois selecionar qual o Select text Splitter. Se tivermos diferentes .md como markdonw e Q7A como podemos fazer? subir em momentos diferentes? veja imagens como ideia de modelo.

5. upsert. veja os prints de configuração

eu quero nesse inicio utilizar o Document Stores do Flowise como modelo e futuramente ir melhorando, mas nesse inicio seguir como ele trabalha.

https://github.com/FlowiseAI/Flowise

(Anexo: 10 capturas de tela do Flowise Document Stores enviadas na conversa de 2026-10-05, não versionadas: modal Select Document Loader; Text File loader com Upload File, Additional Metadata, Omit Metadata Keys e Markdown Text Splitter com Chunk Size 1000, Chunk Overlap 200 e Split by Headers H3; prévia de chunks (20 de 31); lista do store com o loader e o menu Options (Preview & Process, View & Edit Chunks, Upsert Chunks, View API, Delete); assistente de upsert em 3 etapas Embeddings, Vector Store e Record Manager, com OpenAI Custom Embedding e Qdrant.)

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** Reorganizar o envio de documentos para seguir o modelo do Flowise Document Stores: workspace com nome e descrição, escolha de Document Loader, upload, metadados, splitter, prévia de chunks e upsert configurável.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** O fluxo atual de upload cria uma Base direto; a pessoa quer escolher loader, metadados e splitter e configurar o upsert (embeddings, vector store, record manager) como no Flowise, no início seguindo o modelo dele e melhorando depois.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Marcio e a equipe de consultoria que sobem documentos e configuram a ingestão.

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Controle explícito sobre como os documentos .md vindos da fase 1 são carregados, divididos e indexados, com prévia antes de processar.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Workspace com nome e descrição; botão Select Document Loader; Text File Loader para .md (pergunta se vem do LangChain); Additional Metadata e Omit Metadata Keys; Text Splitter (Markdown Text Splitter, chunk size 1000, overlap 200, split por H3); prévia de chunks; ações Preview and Process, View and Edit Chunks, Upsert Chunks, View API, Delete; upsert em 3 etapas (Embeddings, Vector Store, Record Manager); Qdrant com coleção, dimensão 1536 e similaridade Cosine; seleção de loader pertence à fase 1.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Configuração por loader (tipo, splitter, metadados, chaves omitidas), configuração de embeddings, vector store e record manager por workspace ou loader, descrição do workspace.

### Riscos e dependências

**Análise preliminar:** Escopo grande, provavelmente mais de uma spec. Hoje a configuração de chunking é única (config.yaml) e não por loader. Uma das capturas do Flowise exibe o aviso: We are sunsetting Flowise, o que pesa na escolha dele como modelo de longo prazo.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Dividir em fatias: workspace com descrição; loader Text File e metadados; splitter por loader com prévia de chunks; configuração de upsert; ações de gestão dos chunks. Perguntas da pessoa a responder no refinamento: como tratar documentos de tipos diferentes (ex.: markdown e Q&A) e se sobem em momentos distintos.

## Pontos a revisar no futuro

**A revisar:** Confirmar se Text File Loader do Flowise vem do LangChain e qual o equivalente em Python aqui; vários loaders por workspace com splitter diferente; limite do que copiar do Flowise; relação com SPEC-0019 (workspaces) e a decisão de chunking de M02; imagens de referência não estão versionadas.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
