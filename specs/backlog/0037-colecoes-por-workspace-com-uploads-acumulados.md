# Backlog: Coleções por workspace com uploads acumulados e identidade estável de documento

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0037 |
| Status | Promoted |
| Produto | rag-pipeline |
| Épico | Bases e coleções |
| Funcionalidade | Coleções por Workspace |
| Tipo | Melhoria (mudança de modelo) com correção de bug |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-08 |
| Spec promovida | specs/draft/0030-colecoes-por-workspace-com-envios-acumulados/spec.md (SPEC-0030, Draft) |

## Ideia original

Usuário: "o nome da coleção deve ser definido quando for subir o primeiro documento, assim todos os documentos que subir nesse mesmo nome seguem para a mesma coleção. assim temos o workspace e no workspace podemos ter mais de uma coleção e nele vamos subindo os arquivos. faz sentido?" Sobre chunking: "o chunks não acho que deve ser fixo porque posso usar documentos completamente diferentes por isso eu escolho como quero fazer o processamento se é por markdown, caracteres etc." Sobre o conjunto (coleções por workspace, embedding e conexão fixos por coleção, chunking por upload, remoção individual de documento, correção do identificador): "isso que eu quero...." (Fonte: specs/inbox/2026-10-08-235030-colecoes-por-workspace-com-uploads-acumulados-e-identidade-estavel-de-documento.md)

## Problema percebido

Cada upload cria uma Base isolada com escopo próprio (tenant::project::base_id), então documentos enviados para a mesma coleção não se acumulam: o mesmo arquivo enviado duas vezes duplica chunks, o mirror não remove versões de uploads anteriores e não há como apagar um documento específico. Além disso, o document_id muda a cada envio porque deriva da pasta temporária aleatória do upload.

## Pessoa afetada ou beneficiada

Owner e admin que publicam documentos nos Workspaces; indiretamente, quem consulta as bases RAG (respostas com trechos duplicados ou desatualizados).

## Resultado ou valor esperado

Workspace com várias coleções nomeadas; cada upload adiciona arquivos a uma coleção existente ou cria uma nova; mesmo arquivo sem mudança não duplica nem regera embedding; mesmo nome com conteúdo novo substitui a versão anterior; documento pode ser apagado individualmente.

## Contexto

Revê a decisão da SPEC-0019 (coleção escolhida por Base, várias Bases podendo dividir a coleção) e o fluxo de Nova Base da SPEC-0026/0029. Projeto ainda em teste, sem dados de produção a preservar (declaração do usuário em 2026-10-08).

## Referências relacionadas

- `specs/inbox/2026-10-08-235030-colecoes-por-workspace-com-uploads-acumulados-e-identidade-estavel-de-documento.md` (origem: captura da Inbox).
- `specs/completed/0019-agrupar-bases-em-workspaces-com-controle-de-colecao-e-metadados/spec.md` (spec relacionada: decidiu coleção escolhida por Base, com várias Bases podendo dividir a coleção; este item revê essa decisão).
- `specs/backlog/0026-agrupar-bases-em-projetos-com-controle-de-colecao-e-metadados.md` (backlog relacionado: origem da decisão de coleção por Base).
- `specs/completed/0028-apagar-base-usa-colecao-e-conexoes-da-base/spec.md` (spec relacionada: apagar Base usa coleção e conexões da própria Base).
- `specs/in-progress/0029-expor-configuracoes-do-processamento-no-front/spec.md` (spec relacionada, em andamento: estratégias de divisão, `sync_mode` e destino escolhidos por Base no fluxo de Nova Base).
- `specs/backlog/0036-expor-configuracoes-restantes-do-config-yaml-no-front.md` (backlog relacionado: configurações restantes no front).

## Comportamento esperado

- O Workspace lista suas Coleções em `DataGrid` (coluna ID visível, linha leva ao detalhe), com ações Renomear e Apagar por linha e o botão Enviar documentos.
- Enviar documentos usa o fluxo Arquivos → Divisão → Prévia → Publicação. Na Publicação, a pessoa escolhe Coleção existente (conexões herdadas e travadas) ou Nova coleção (nome + conexão de embeddings + conexão Qdrant). Não há escolha de `sync_mode`.
- A divisão (estratégia, tamanho, overlap e opções da SPEC-0029) é escolhida a cada envio.
- Regra de sincronização por coleção: arquivo novo é somado; arquivo com o mesmo nome e conteúdo diferente substitui todos os chunks da versão anterior; arquivo idêntico é mantido sem novo embedding.
- Identidade do documento: derivada da coleção e do nome do arquivo; `document_id` do frontmatter tem precedência. Nunca depende de pasta temporária.
- Detalhe da coleção em abas Documentos | Envios | Consulta. Documentos: tabela com nome, chunks, divisão usada, último envio e ações Substituir e Apagar; a linha abre `Sheet` somente leitura com os chunks.
- Apagar documento remove somente os chunks daquele documento, após confirmação com a quantidade de chunks.
- Apagar coleção remove a coleção física no Qdrant e os registros associados, após confirmação por digitação do nome.
- Renomear altera só o nome exibido; o nome físico no Qdrant é fixo.
- As Bases atuais são descartadas, sem migração.

## Interface (fechada com `specsfy-specialist-interface-experience`, `ux-design` e `ui-design`)

- Stack observada: Next.js + React + Tailwind + shadcn/ui + ReUI; `PageHeader` compartilhado; `DataGrid` nas listagens; `Sheet` para painéis; diálogos de exclusão como `ExcluirBaseDialog`.
- Telas: (1) `/workspaces/[id]` passa a listar Coleções (`DataGridColecoes`: ID, nome, documentos, chunks, último envio; ações Renomear e Apagar; linha → detalhe); (2) detalhe da coleção com abas Documentos | Envios | Consulta; (3) fluxo de envio (`FluxoIngestao`) com seleção ou criação de coleção na Publicação; (4) `Sheet` somente leitura com os chunks do documento; (5) renomear em `Sheet` de formulário; (6) diálogos de apagar documento (com quantidade de chunks) e coleção (digitar o nome).
- Navegação: menu principal inalterado (Workspaces); `Breadcrumb` Workspace → Coleção; a tela do envio volta para a coleção ao publicar.
- Estados por tela: carregando, vazio (Workspace sem coleções com CTA Enviar documentos; coleção sem documentos com CTA Adicionar documentos), erro com Tentar novamente, sucesso com feedback, permissão de member sem ações de escrita, teclado nas linhas e abas.
- Direção visual: defaults de `DESIGNSYSTEM.MD` e componentes registrados em `INTERFACE.md`.

## Regras de negócio

- RN-01: nome exibido da coleção é único dentro do Workspace (inferência a confirmar).
- RN-02: modelo de embedding e conexão Qdrant são definidos na criação da coleção e não mudam; envio com dimensão incompatível é bloqueado antes de gravar.
- RN-03: o mesmo nome de arquivo dentro da coleção representa o mesmo documento.
- RN-04: nenhum envio remove documentos não enviados; remoção só por ação explícita de apagar documento ou coleção.
- RN-05: descarte das Bases atuais sem `DROP TABLE`, `TRUNCATE` ou comandos equivalentes.

## Critérios de aceitação

- Dado uma coleção com `a.md`, quando envio `a.md` idêntico, então a coleção continua com os mesmos chunks e nenhum embedding novo é gerado.
- Dado uma coleção com `a.md`, quando envio `a.md` com conteúdo alterado, então só os chunks da nova versão permanecem para `a.md`.
- Dado uma coleção com `a.md`, quando envio `b.md`, então a coleção passa a ter `a.md` e `b.md`.
- Dado uma coleção com `a.md` e `b.md`, quando apago `a.md` e confirmo, então só os chunks de `a.md` saem do Qdrant.
- Dado uma coleção existente, quando escolho Coleção existente na Publicação, então as conexões aparecem travadas com as da coleção.
- Dado uma coleção, quando a apago e digito o nome, então a coleção física deixa de existir no Qdrant e some do Workspace.
- Dado um member, quando abre o Workspace, então não vê Enviar documentos, Renomear nem Apagar.

## Qualidades e operação

- Segurança: escrita restrita a owner/admin; apagar coleção é operação remota destrutiva com confirmação forte; chaves das conexões nunca aparecem em respostas ou logs (regra da SPEC-0026/0029).
- Privacidade: sem dado pessoal novo; isolamento por tenant/projeto/Workspace mantido.
- Desempenho e volume: arquivo idêntico não gera embedding novo; substituir documento reindexa só aquele documento.
- Auditoria e observabilidade: histórico de envios preservado após apagar ou substituir documento; contagens previstos/inseridos/mantidos/removidos por envio.

## Dependências

- SPEC-0029 (em andamento) precisa ser concluída antes: ela altera o mesmo fluxo e os mesmos arquivos (`bases.py`, `tasks.py`, `ingestao.py`, `qdrant.py`, `FluxoIngestao`).

## Situações de erro

- Dimensão do modelo diferente da coleção: publicação bloqueada antes de gravar.
- Falha no Qdrant ao apagar documento ou coleção: nada é removido do registro local e a mensagem é segura, sem credencial.
- Nome de coleção repetido no Workspace: criação bloqueada com mensagem.
- Envio falha no meio: o histórico de envios mostra o erro e permite repetir.

## Escopo

- Dentro: entidade Coleção por Workspace; inventário de documentos e envios; fluxo de envio com seleção/criação de coleção; identidade estável de documento; sincronização por coleção; remover documento; renomear e apagar coleção; descarte das Bases atuais; remoção de `sync_mode` da interface; consulta por coleção.
- Fora: migração das Bases atuais; mover documento entre coleções; trocar modelo de embedding ou conexão de uma coleção existente; renomear o nome físico no Qdrant; histórico de versões de documento.

## Dúvidas, decisões e riscos

- **Pergunta 1 (2026-10-08) — O que acontece com o conceito de "Base"?** Resposta original: `1`. Opção escolhida: "A Coleção substitui a Base: o Workspace lista as coleções; cada coleção mostra seus documentos e o histórico de envios; a consulta é feita na coleção." **Decisão:** a Coleção substitui a Base como unidade do Workspace; a hierarquia passa a ser Workspace → Coleção → documentos, com histórico de envios na coleção; consulta por coleção.
- **Decisões já declaradas na conversa (2026-10-08):** nome da coleção definido no primeiro upload; uploads seguintes escolhem coleção existente; modelo de embedding e conexão do vector store fixos por coleção; chunking/processamento escolhido a cada upload; remoção individual de documento; identidade do documento estável pelo nome do arquivo (preservando `document_id` do frontmatter).
- **Inferência a confirmar:** nome físico no Qdrant prefixado pelo Workspace; escopo de sincronização passa a ser a coleção.
- **Pergunta 2 (2026-10-08) — O que fazer com as Bases que já existem hoje (dados de teste)?** Resposta original: `1`. Opção escolhida: "Descartar tudo e começar do zero: as Bases atuais, seus registros e seus vetores no Qdrant são apagados, e as coleções novas nascem vazias." **Decisão:** sem migração de dados; as Bases atuais são descartadas. **Restrição do framework:** o descarte não pode usar comandos que apagam ou recriam banco/schema (`DROP TABLE`, `TRUNCATE`, `migrate:reset` e equivalentes); deve ocorrer pelo caminho de exclusão da aplicação ou por ação operacional explícita definida na spec.
- **Pergunta 3 (2026-10-08) — O que fazer com a opção `append` / `mirror` no upload?** Resposta original: `1`. Opção escolhida: "Remover a escolha: todo upload segue a mesma regra — arquivo novo é somado, arquivo de mesmo nome substitui a versão anterior, arquivo igual é mantido sem novo embedding; para tirar um documento, usa-se o botão de apagar." **Decisão:** o upload deixa de oferecer `sync_mode`. **Conflito a tratar:** a SPEC-0029, em andamento, expõe `sync_mode` no fluxo de Nova Base; esta entrega remove essa escolha da interface.
- **Pergunta 4 (2026-10-09) — Depois de criada, a coleção pode ter o nome alterado?** Resposta original: `1`. Opção escolhida: "Sim, só o nome exibido: renomeia na tela, mas o nome físico no Qdrant, definido na criação, não muda." **Decisão:** a Coleção tem nome exibido editável e nome físico imutável; os vetores não são movidos.
- **Pergunta 5 (2026-10-09, área Interface) — Por onde a pessoa sobe documentos para uma coleção?** Resposta original: `1`. Opção escolhida: "Um fluxo único com dois atalhos: no Workspace, o botão Enviar documentos abre o fluxo atual; na etapa Publicação, escolhe Coleção existente (conexões herdadas e travadas) ou Nova coleção (nome + conexões, cria a coleção). Na tela da coleção, Adicionar documentos abre o mesmo fluxo com a coleção pré-selecionada." **Decisão:** reaproveitar `FluxoIngestao` (Arquivos → Divisão → Prévia → Publicação) com seleção ou criação de coleção na Publicação; dois pontos de entrada. Interface atual observada: `/workspaces/[id]` com `DataGridBases` e botão Nova Base → `/workspaces/[id]/bases/nova`; `EtapaPublicacao` com campo livre de coleção e escolha de conexões; stack Next.js + shadcn/ui + ReUI, `PageHeader` compartilhado.
- **Pergunta 6 (2026-10-09, área Interface) — Como organizar a tela de detalhe da coleção?** Resposta original: `1`. Opção escolhida: "Em abas: Documentos | Envios | Consulta. Abre em Documentos, uma tabela com nome do arquivo, quantidade de chunks, divisão usada, data do último envio e ações." **Decisão:** detalhe da coleção com três abas; aba padrão Documentos.
- **Pergunta 7 (2026-10-09, área Interface) — O que acontece ao clicar num documento da tabela, e quais ações ele tem?** Resposta original: `1`. Opção escolhida: "A linha abre um painel lateral com os chunks do documento, só para leitura. Ações da linha: Substituir (abre o fluxo de envio com a coleção pré-selecionada) e Apagar (com confirmação dizendo quantos chunks saem)." **Decisão:** linha → `Sheet` somente leitura com os chunks; ações Substituir e Apagar com confirmação.
- **Pergunta 8 (2026-10-09) — Ao apagar uma coleção pela tela, o que acontece no Qdrant?** Resposta original: `1`. Opção escolhida: "Apaga a coleção física inteira no Qdrant; a confirmação mostra nome, quantidade de documentos e chunks e exige digitar o nome." **Decisão:** apagar coleção remove a coleção física no Qdrant, com confirmação forte por digitação do nome. Esta é a decisão explícita de operação remota destrutiva exigida por `PROJECT.md` (Limites).
- **Descoberta de dados (2026-10-09, `$specsfy-data-discovery`) — Quando um documento é apagado ou substituído, o que acontece com o histórico de envios?** Resposta original: `1`. Opção escolhida: "O histórico continua intacto: a aba Envios segue mostrando que o arquivo foi enviado naquela data, com as contagens da época; só os trechos e o documento atual somem." **Registro:** `.specsfy/DATABASE.md`, seção `Informações a guardar confirmadas` — Coleção de documentos do Workspace, Documento da coleção, Envio de documentos para a coleção.
- **Inferências a confirmar na spec:** permissões seguem a regra atual (owner/admin criam, enviam, renomeiam e apagam; member só consulta); nome físico no Qdrant prefixado pelo Workspace e único; escopo de sincronização por coleção; menu principal inalterado (entrada continua em Workspaces).
- **Abertos (não perguntados):** regra de apagar Workspace com coleções dentro (hoje bloqueado com Bases dentro). apagar e renomear coleção; permissões; telas e navegação.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
