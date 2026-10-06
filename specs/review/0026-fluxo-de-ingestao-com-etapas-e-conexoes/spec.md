# Especificação integrada: Fluxo de ingestão com etapas, conexões reutilizáveis e prévia de chunks

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0026 |
| Slug | 0026-fluxo-de-ingestao-com-etapas-e-conexoes |
| Status | Reviewing |
| Effort | 8 |
| Effort updated at | 2026-10-06 |
| Effort rationale | Nova tabela com segredo cifrado, mudança do worker para decifrar fora da fila, prévia sem estado, verificação de dimensão no vector store e quatro telas novas substituindo o envio atual; muitas decisões cruzam backend, pipeline e interface. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-06 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

Quem opera o pipeline pela interface só consegue enviar arquivos e disparar a execução completa de uma vez: o `UploadBaseSheet` cria a Base e agenda o processamento inteiro (`UploadBaseSheet.criar` → `agendarEAbrir`). Splitter, tamanho de chunk e overlap vivem em `config.yaml`, e os destinos de embeddings e Qdrant vêm de configuração global do servidor. Para testar uma divisão diferente, a pessoa precisa editar arquivo, reimplantar ou apagar e recriar a Base. Não existe como revisar os chunks antes de gastar embeddings nem como escolher o destino por Base. Pedido original (BACKLOG-0025): "todas as variáveis configuráveis devem estar aki e tambem ter uma forma mais organizada", ampliado em 2026-10-05 para o fluxo de ingestão inspirado nos Document Stores do Flowise.

#### Resultado desejado

Owner e admin conduzem o envio em quatro etapas (Arquivos, Divisão, Prévia, Publicação), escolhem splitter, tamanho e overlap, revisam os chunks sem persistir nada, selecionam conexões reutilizáveis de embeddings e Qdrant cadastradas pela interface, definem a coleção e publicam com proteção contra dimensões incompatíveis, acompanhando inseridos, mantidos e removidos.

#### Métricas de sucesso

- 100% dos envios novos passam pelas quatro etapas; nenhum envio cria Base ou execução antes de Publicar.
- Zero ocorrência da chave de uma conexão em respostas da API, logs, argumentos de job, manifesto e prévias, medida pelos testes de NFR-001.
- Zero vetores gravados quando a dimensão diverge, medido pelo teste de AC-011.
- Bases anteriores executam sem alteração de comportamento, medido pela regressão completa.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: Como o Flowise separa carregamento, divisão, prévia e upsert nos Document Stores? → A documentação oficial separa loader, splitter, prévia, processamento e configuração de upsert, com Record Manager opcional; a jornada serve de referência visual, não obriga a replicar o catálogo de providers (impacto: etapas e escopo reduzido a dois tipos de conexão).
- **R-002**: O código atual já aceita parâmetros de divisão por configuração injetada? → Sim: `service.run_pipeline` lê a seção opcional `chunking` e `_get_splitter_config` dá prioridade ao frontmatter sobre o padrão global (impacto: FR-007 preserva a precedência e a prévia pode reutilizar `run_pipeline(only_chunks=True)`).
- **R-003**: Como obter a dimensão de uma coleção sem criar nada? → `VectorStoreAdapter.describe_scope` é leitura pura e devolve existência e dimensão (`src/pipeline/providers/contracts.py`) (impacto: FR-009 não exige novo contrato).

#### Fontes e contexto consultados

- `specs/backlog/0025-expor-configuracoes-de-ingestao-na-interface.md`, origem normativa das decisões de Dados, Integrações e Interface (oito perguntas por área, todas respondidas em 2026-10-05 e 2026-10-06).
- `specs/inbox/2026-10-05-170632-fluxo-de-ingestao-inspirado-nos-document-stores-do-flowise.md`, captura integral do pedido ampliado.
- `src/app/routers/bases.py`, `src/app/routers/executions.py`, `src/app/tasks.py`, `src/app/settings.py`, `src/app/models.py`, `src/pipeline/service.py`, `src/pipeline/chunker.py` e `config.yaml`, evidência do comportamento atual.
- `INTERFACE.md`, `DESIGNSYSTEM.MD`, `.specsfy/DATABASE.md`, `.specsfy/RULES.md` e `.specsfy/STACK.md`.
- Specs concluídas relacionadas: SPEC-0002 (contrato Q&A e sincronização), SPEC-0019 (Workspace, coleção e metadados), SPEC-0020 (Pessoa e Sessão), SPEC-0025 (indicador de processamento).

#### Documentação consultada

- Flowise, Document Stores, https://docs.flowiseai.com/using-flowise/document-stores, acessada em 2026-10-05; tópicos: etapas de loader, splitter, prévia, processamento, upsert e Record Manager.
- Flowise, nó Text File, https://github.com/FlowiseAI/Flowise/blob/main/packages/components/nodes/documentloaders/Text/Text.ts, branch main acessada em 2026-10-05 (referência mutável); tópico: uso de `.md` com `TextLoader`.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo: as duas fontes do Flowise foram usadas como referência conceitual de jornada, sem copiar conteúdo, e as conclusões normativas estão neste arquivo.

#### Dúvidas respondidas

- **Q**: Onde vivem os parâmetros de divisão? → **A**: Por Base, no momento do envio, e não em uma tela global de configurações (decisão de setembro, mantida).
- **Q**: Como oferecer conexões de embeddings e Qdrant? → **A**: Cadastro e seleção de conexões reutilizáveis pela interface; owner e admin da mesma equipe e projeto as administram e usam em qualquer Workspace.
- **Q**: O que fazer ao retirar uma conexão usada? → **A**: Desativar preserva vínculos e histórico; novo upsert exige conexão ativa; exclusão definitiva somente sem uso.
- **Q**: Como tratar a chave? → **A**: Somente escrita, cifrada no servidor, mascarada na interface, troca exige nova chave.
- **Q**: Quais tipos na primeira entrega? → **A**: Embeddings OpenAI (modelo e URL base opcionais) e Qdrant; Chroma, Pinecone e outros providers ficam fora (BACKLOG-0009).
- **Q**: Dimensão divergente? → **A**: Bloquear antes de publicar, sem gravar vetor.
- **Q**: Record Manager? → **A**: Sem etapa nem conexão própria; reaproveitar a sincronização da SPEC-0002 e mostrar inseridos, mantidos e removidos.
- **Q**: Prévia e edição de chunks? → **A**: Prévia descartável sem persistência; sem edição ou exclusão de chunks individuais.
- **Q**: Como registrar alterações nas conexões? → **A** (2026-10-06): histórico próprio de eventos com pessoa, ação e horário, sem a chave, retido por 90 dias como o histórico de acessos.
- **Q**: Como guardar e trocar a chave de cifra em produção? → **A** (2026-10-06): chave única fornecida como secret do Docker Swarm ou variável de ambiente, sem rotação automática; trocar exige recadastrar as chaves das conexões.
- **Q**: Quais limites de divisão? → **A** (2026-10-06): tamanho de 200 a 4000 caracteres; overlap de 0 até a metade do tamanho e sempre menor que o tamanho; padrões header, 1000 e 200.
- **Q**: Interface do fluxo? → **A**: Página própria com etapas substituindo o `UploadBaseSheet`; menu Conexões para owner e admin com `DataGrid` e `Sheet`; Divisão com poucos campos e aviso Q&A; Prévia somente leitura e paginada; Publicação com conexões ativas, dimensões em linha e botão bloqueado com razão; nada guardado no servidor antes de publicar; estados e acessibilidade completos.

#### Dúvidas abertas

- Nenhuma dúvida bloqueante. As três pendências do primeiro rascunho (auditoria, chave de cifra e limites) foram respondidas em 2026-10-06 e estão em Dúvidas respondidas. Os demais padrões em Suposições são defaults reversíveis a conferir na validação.

### 3. Escopo e atores

#### Incluído

- Conexões reutilizáveis dos tipos `embeddings_openai` e `qdrant`: cadastro, listagem, detalhe, edição, desativação, reativação e exclusão sem uso, por API e interface.
- Cifra da chave em repouso, somente escrita, com máscara fixa, e histórico `eventos_conexao` das alterações com retenção de 90 dias.
- Prévia descartável dos chunks (`POST /api/v1/ingestao/previa`) e endpoint de padrões e limites (`GET /api/v1/ingestao/padroes`).
- Extensão de `POST /api/v1/bases` com parâmetros de divisão, vínculos de conexão e criação da execução na mesma requisição.
- Verificação de dimensão antes de publicar.
- Persistência, na Base, dos parâmetros e dos vínculos; execução e repetição com esses valores; compatibilidade com Bases anteriores.
- Página de nova Base com quatro etapas, tela Conexões (lista e detalhe), item de menu, remoção do `UploadBaseSheet` e opção de base preparada na etapa Arquivos.

#### Fora de escopo

- Chroma, Pinecone e outros providers de vector store ou de embeddings (BACKLOG-0009 e BACKLOG-0010).
- Record Manager como etapa ou conexão; "Testar conexão"; "View & Edit Chunks", edição ou exclusão de chunks individuais; "View API".
- Rascunho de Base no servidor, retomada de fluxo e persistência dos arquivos antes de publicar.
- Configuração por arquivo pela interface (o frontmatter continua sendo o meio de ajuste por arquivo).
- Adicionar envios a uma Base existente: cada publicação cria uma Base nova.
- Escolha de loaders para outros formatos, que pertence à fase 1 de ingestão.
- Rotação automática da chave de cifra, tela de consulta ao histórico de conexões e gestão geral de secrets de produção (BACKLOG-0030).
- Tela global de configurações.

#### Atores

- **Owner**: administra conexões, envia arquivos, calcula prévias e publica Bases em qualquer Workspace da equipe e projeto.
- **Admin**: mesmas permissões do owner nesta entrega.
- **Member**: consulta Workspaces e Bases como hoje; não vê Conexões, não vê o botão de nova Base e é recusado nas URLs e APIs novas.
- **Worker do pipeline**: decifra as chaves em memória, divide, gera embeddings e sincroniza; nunca recebe chave pela fila.

### 4. Princípios e restrições do projeto

- **PR-001**: `src/app` depende somente da fachada `src.pipeline.service`; SDKs de vector store e de embeddings ficam confinados a `src/pipeline/providers/` (verificado por `tests/test_application_boundaries.py` e `tests/test_provider_boundaries.py`).
- **PR-002**: Nunca versionar, logar ou expor credenciais; o acesso à configuração é centralizado e injetado pelo entrypoint, e `src/pipeline/` não carrega `.env`.
- **PR-003**: A sincronização registra modo, escopo lógico e contagens previstas, inseridas, mantidas e removidas, sem credenciais, tokens ou URLs de destino.
- **PR-004**: Proteção do banco: testes usam `DatabaseTransactions`-equivalente do projeto (rollback transacional) e o banco de teste explícito de `.env.testing`; comandos destrutivos de schema são recusados.
- **PR-005**: Em frontend, as telas compõem componentes React; `INTERFACE.md` é atualizado com cada bloco criado ou reaproveitado, seguindo `DESIGNSYSTEM.MD` (`PageHeader` único, `DataGrid` com coluna `ID`, `Breadcrumb`).
- **PR-006**: O corpo desta spec evita as palavras proibidas pela regra de marcadores do projeto (`tests/test_spec_markers.py`).
- **PR-007**: Branch `spec/0026-fluxo-de-ingestao-com-etapas-e-conexoes` para a implementação; uma branch nunca carrega duas specs.

### 5. Histórias de usuário

#### US-001 — Administrar conexões reutilizáveis (P1)

Como owner ou admin da equipe, quero cadastrar, editar, desativar e excluir conexões de embeddings OpenAI e de Qdrant, para reutilizá-las em qualquer Workspace sem editar arquivos de configuração nem reimplantar.

**Por que P1**: É a base de tudo: sem conexão ativa nenhuma Base nova pode ser publicada.
**Teste independente**: Cadastrar uma conexão pela tela Conexões e vê-la na lista com chave mascarada.
**Requisitos**: FR-001, FR-002, FR-003, FR-004, FR-012

#### US-002 — Dividir e revisar chunks antes de publicar (P1)

Como owner ou admin, quero escolher splitter, tamanho de chunk e overlap e ver uma prévia dos chunks antes de gerar embeddings, para ajustar a divisão sem publicar nada.

**Por que P1**: Hoje o envio cria a Base e executa tudo; errar a divisão obriga a apagar e repetir.
**Teste independente**: Enviar arquivos de exemplo, calcular a prévia e conferir contagens e chunks sem que nada exista no servidor depois.
**Requisitos**: FR-005, FR-006, FR-007, FR-013

#### US-003 — Publicar com as conexões escolhidas (P1)

Como owner ou admin, quero escolher a conexão de embeddings, a conexão Qdrant e a coleção e publicar a Base, para indexar os chunks aprovados com proteção contra dimensões incompatíveis.

**Por que P1**: Fecha a jornada: sem publicação a prévia não gera valor.
**Teste independente**: Publicar a partir da etapa Publicação e acompanhar inseridos, mantidos e removidos na Base.
**Requisitos**: FR-008, FR-009, FR-010, FR-011, FR-014

#### US-004 — Acesso restrito e substituição do envio atual (P2)

Como pessoa da equipe, quero que somente owner e admin vejam o fluxo e as conexões e que o envio antigo seja substituído pelo novo fluxo, para não existirem dois caminhos de envio com comportamentos diferentes.

**Por que P2**: Evita regressão de permissão e duplicidade de caminhos.
**Teste independente**: Abrir o Workspace como member e como owner e comparar as ações disponíveis.
**Requisitos**: FR-012, FR-013, FR-014

### 6. Cenários BDD de aceite

#### AC-001 — Cadastrar conexão de embeddings OpenAI

**Cobre**: US-001, FR-001, FR-002, FR-004, NFR-001, NFR-002

```gherkin
@US-001 @FR-001 @FR-002 @FR-004 @NFR-001 @NFR-002 @AC-001
Feature: Conexões reutilizáveis de ingestão

  Scenario: Cadastrar conexão de embeddings OpenAI
    Given uma pessoa owner autenticada na equipe e no projeto ativos
    When ela cadastra uma conexão do tipo embeddings OpenAI com nome, modelo, dimensões 1536 e uma chave
    Then a API responde 201 com a conexão ativa, sem a chave, com `segredo_definido` verdadeiro e a máscara fixa, o banco guarda somente o texto cifrado e `eventos_conexao` recebe o evento `criada` com a pessoa autora e sem a chave
```

#### AC-002 — Cadastrar conexão Qdrant e preservar a chave na edição

**Cobre**: US-001, FR-001, FR-002, FR-004, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @FR-004 @NFR-001 @AC-002
Feature: Conexões reutilizáveis de ingestão

  Scenario: Cadastrar conexão Qdrant e preservar a chave na edição
    Given uma conexão Qdrant ativa com chave definida
    When uma pessoa admin edita o nome sem informar chave e depois edita informando uma nova chave
    Then a primeira edição mantém o texto cifrado anterior e a segunda o substitui; nenhuma resposta devolve a chave antiga ou a nova, e `eventos_conexao` registra `editada` na primeira e `chave_trocada` na segunda, sem valores
```

#### AC-003 — Recusar conexão inválida

**Cobre**: US-001, FR-001, FR-002, NFR-002

```gherkin
@US-001 @FR-001 @FR-002 @NFR-002 @AC-003
Feature: Conexões reutilizáveis de ingestão

  Scenario: Recusar conexão inválida
    Given uma pessoa admin autenticada
    When ela envia uma conexão com URL de esquema não HTTP, URL com credenciais embutidas, host de loopback ou de metadados da nuvem, dimensões menores que 1, tipo desconhecido ou nome vazio
    Then a API responde 422 com a mensagem do campo e nada é gravado
```

#### AC-004 — Desativar e reativar uma conexão

**Cobre**: US-001, FR-003, FR-004, FR-008, NFR-002

```gherkin
@US-001 @FR-003 @FR-004 @FR-008 @NFR-002 @AC-004
Feature: Ciclo de vida das conexões

  Scenario: Desativar e reativar uma conexão
    Given uma conexão ativa vinculada a uma Base já publicada
    When uma pessoa owner a desativa e depois a reativa
    Then a conexão some das opções de publicação enquanto desativada, o vínculo e o histórico da Base permanecem, os vetores não são tocados a reativação a devolve às opções e `eventos_conexao` registra `desativada` e `reativada`
```

#### AC-005 — Excluir somente conexão sem uso

**Cobre**: US-001, FR-003, FR-004, NFR-002

```gherkin
@US-001 @FR-003 @FR-004 @NFR-002 @AC-005
Feature: Ciclo de vida das conexões

  Scenario: Excluir somente conexão sem uso
    Given uma conexão sem Base vinculada e outra vinculada a uma Base
    When uma pessoa owner tenta excluir as duas
    Then a primeira é removida com 204 e a segunda recebe 409 com a quantidade de Bases em uso e permanece intacta, com o evento `excluida` registrado somente na exclusão aceita
```

#### AC-006 — Recusar acesso de member e de outra equipe às conexões

**Cobre**: US-001, US-004, FR-004, FR-012, NFR-002

```gherkin
@US-001 @US-004 @FR-004 @FR-012 @NFR-002 @AC-006
Feature: Autorização das conexões

  Scenario: Recusar acesso de member e de outra equipe às conexões
    Given uma pessoa member na equipe A e uma pessoa admin na equipe B
    When elas tentam listar, ler, criar, editar, desativar e excluir uma conexão da equipe A
    Then o member recebe 403 em cada operação e a admin da equipe B recebe 404 por conexão específica e lista vazia, sem revelar a existência
```

#### AC-007 — Calcular a prévia com splitter por cabeçalhos

**Cobre**: US-002, FR-005, FR-006, FR-007, NFR-003

```gherkin
@US-002 @FR-005 @FR-006 @FR-007 @NFR-003 @AC-007
Feature: Prévia descartável dos chunks

  Scenario: Calcular a prévia com splitter por cabeçalhos
    Given três arquivos Markdown válidos enviados com splitter header, tamanho 1000 e overlap 200
    When uma pessoa owner solicita a prévia
    Then a resposta traz documentos, total de chunks, tamanho médio e a primeira página de chunks com documento de origem, posição, tamanho e texto, e nada é gravado no storage, no banco, no vector store nem no provedor de embeddings
```

#### AC-008 — Respeitar o frontmatter na prévia e avisar sobre os arquivos afetados

**Cobre**: US-002, FR-005, FR-007, NFR-003

```gherkin
@US-002 @FR-005 @FR-007 @NFR-003 @AC-008
Feature: Prévia descartável dos chunks

  Scenario: Respeitar o frontmatter na prévia e avisar sobre os arquivos afetados
    Given um arquivo com `splitter: qa` e outro com `chunk_size_recommended` no frontmatter, ao lado de um arquivo comum
    When a prévia é calculada com splitter recursive e tamanho 500
    Then o arquivo Q&A gera um chunk por par, o segundo usa o próprio tamanho, o comum usa o formulário e a resposta lista os dois primeiros em `arquivos_com_configuracao_propria`
```

#### AC-009 — Recusar parâmetros e arquivos inválidos na prévia

**Cobre**: US-002, FR-005, FR-006, NFR-003

```gherkin
@US-002 @FR-005 @FR-006 @NFR-003 @AC-009
Feature: Prévia descartável dos chunks

  Scenario: Recusar parâmetros e arquivos inválidos na prévia
    Given uma pessoa owner autenticada
    When ela solicita a prévia com overlap maior ou igual ao tamanho, tamanho fora dos limites, splitter desconhecido, arquivo que não é `.md`, arquivo acima de 5 MB ou mais de 50 arquivos
    Then a API responde 400 ou 422 com a mensagem do problema e nenhum arquivo é lido além da validação nem gravado
```

#### AC-010 — Publicar uma Base com conexões ativas

**Cobre**: US-003, FR-007, FR-008, FR-009, FR-010, FR-011, NFR-005

```gherkin
@US-003 @FR-007 @FR-008 @FR-009 @FR-010 @FR-011 @NFR-005 @AC-010
Feature: Publicação com conexões escolhidas

  Scenario: Publicar uma Base com conexões ativas
    Given arquivos válidos, uma conexão de embeddings ativa, uma conexão Qdrant ativa e a coleção `produtos` inexistente
    When uma pessoa owner publica com splitter, tamanho, overlap e `iniciar_execucao` verdadeiro
    Then a API responde 201 com `base_id` e `execution_id`, a Base guarda os parâmetros e os dois vínculos, a execução usa a mesma precedência da prévia e o resultado traz inseridos, mantidos e removidos
```

#### AC-011 — Bloquear a publicação quando a dimensão diverge

**Cobre**: US-003, FR-008, FR-009, NFR-002

```gherkin
@US-003 @FR-008 @FR-009 @NFR-002 @AC-011
Feature: Publicação com conexões escolhidas

  Scenario: Bloquear a publicação quando a dimensão diverge
    Given a coleção `produtos` existe no Qdrant com dimensão 3072 e a conexão de embeddings declara 1536
    When uma pessoa owner tenta publicar
    Then a API responde 409 com as duas dimensões na mensagem e nenhuma Base, nenhum arquivo, nenhuma execução e nenhum vetor são criados
```

#### AC-012 — Recusar conexão desativada ou de outra equipe na publicação

**Cobre**: US-003, FR-003, FR-008, FR-009, FR-011, NFR-002

```gherkin
@US-003 @FR-003 @FR-008 @FR-009 @FR-011 @NFR-002 @AC-012
Feature: Publicação com conexões escolhidas

  Scenario: Recusar conexão desativada ou de outra equipe na publicação
    Given uma conexão de embeddings desativada, uma conexão Qdrant de outra equipe e uma conexão do tipo trocado
    When uma pessoa admin tenta publicar com cada uma delas
    Then a API responde 409 para a desativada e 404 para a de outra equipe e para o tipo trocado, e nada é gravado
```

#### AC-013 — Decifrar a chave somente no worker e repetir com os mesmos parâmetros

**Cobre**: US-003, FR-010, FR-011, NFR-001, NFR-005

```gherkin
@US-003 @FR-010 @FR-011 @NFR-001 @NFR-005 @AC-013
Feature: Execução com conexões

  Scenario: Decifrar a chave somente no worker e repetir com os mesmos parâmetros
    Given uma Base vinculada a duas conexões ativas e uma execução que falhou
    When a execução é agendada e depois repetida por `retry`
    Then os argumentos do job contêm somente identificadores, o worker decifra as chaves em memória, os logs e o manifesto não contêm chaves, o worker revalida as URLs das conexões e marca a execução como `failed` diante de host proibido, e a repetição reaproveita splitter, tamanho, overlap, coleção e vínculos da Base
```

#### AC-014 — Executar Base legada com a configuração global

**Cobre**: US-003, FR-010, FR-011, NFR-005

```gherkin
@US-003 @FR-010 @FR-011 @NFR-005 @AC-014
Feature: Compatibilidade com Bases existentes

  Scenario: Executar Base legada com a configuração global
    Given uma Base criada antes desta entrega, sem vínculos de conexão nem parâmetros de divisão
    When uma pessoa owner inicia ou repete uma execução
    Then o worker usa a configuração global injetada no entrypoint e os padrões de `config.yaml`, e o comportamento observável permanece idêntico ao anterior
```

#### AC-015 — Percorrer as etapas preservando o preenchimento

**Cobre**: US-002, US-004, FR-006, FR-013, FR-014, NFR-004

```gherkin
@US-002 @US-004 @FR-006 @FR-013 @FR-014 @NFR-004 @AC-015
Feature: Fluxo de ingestão em etapas

  Scenario: Percorrer as etapas preservando o preenchimento
    Given a página de nova Base aberta por uma pessoa owner com dois arquivos selecionados
    When ela avança até Prévia, volta a Divisão, altera o tamanho e tenta sair com alterações pendentes
    Then os arquivos e os valores permanecem, o erro de campo aparece abaixo do campo com foco no primeiro erro, a etapa nova recebe o foco no título e a saída pede confirmação
```

#### AC-016 — Substituir o envio atual e oferecer a base preparada

**Cobre**: US-004, FR-012, FR-013, FR-014

```gherkin
@US-004 @FR-012 @FR-013 @FR-014 @AC-016
Feature: Fluxo de ingestão em etapas

  Scenario: Substituir o envio atual e oferecer a base preparada
    Given a página de um Workspace aberta por owner e por member
    When cada pessoa observa as ações disponíveis
    Then o owner vê o botão que leva à página de nova Base, o `UploadBaseSheet` não existe mais, a etapa Arquivos oferece a opção de base preparada e o member não vê o botão e recebe recusa ao abrir a URL direta
```

#### AC-017 — Mostrar loading, vazio e erro nas etapas

**Cobre**: US-002, US-003, FR-013, FR-014, NFR-004

```gherkin
@US-002 @US-003 @FR-013 @FR-014 @NFR-004 @AC-017
Feature: Estados do fluxo de ingestão

  Scenario: Mostrar loading, vazio e erro nas etapas
    Given a página de nova Base sem conexão ativa, e depois com falha simulada na prévia e na publicação
    When a pessoa chega à Publicação, calcula a prévia e publica
    Then a Publicação orienta para Conexões, a Próxima fica desabilitada sem arquivos, o carregamento usa `Button loading` e `IndicadorProcessamento`, a falha aparece em `Alert` com Tentar novamente e o preenchimento é mantido
```

#### AC-018 — Listar e administrar conexões na interface

**Cobre**: US-001, FR-012, FR-014, NFR-004

```gherkin
@US-001 @FR-012 @FR-014 @NFR-004 @AC-018
Feature: Tela de Conexões

  Scenario: Listar e administrar conexões na interface
    Given a tela Conexões aberta por uma pessoa admin com três conexões
    When ela percorre a lista por teclado, abre uma linha, edita em painel lateral e desativa
    Then a grade ocupa a largura inteira com a coluna ID, a linha inteira leva ao detalhe, as ações de editar, desativar e excluir são independentes, a chave aparece mascarada e vazia na edição e o resultado é anunciado em região `aria-live`
```

#### AC-019 — Acompanhar inseridos, mantidos e removidos depois de publicar

**Cobre**: US-003, FR-010, FR-014

```gherkin
@US-003 @FR-010 @FR-014 @AC-019
Feature: Publicação com conexões escolhidas

  Scenario: Acompanhar inseridos, mantidos e removidos depois de publicar
    Given uma publicação aceita pelo backend
    When a interface navega para a página da Base
    Then o `PainelProgresso` mostra a etapa e as contagens de inseridos, mantidos e removidos da execução criada, sem etapa nem conexão de Record Manager
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve permitir que owner e admin cadastrem conexões de dois tipos, `embeddings_openai` (nome, modelo, URL base opcional, dimensões inteiras maiores que 0 e chave) e `qdrant` (nome, URL e chave opcional), escopadas ao tenant e ao projeto da pessoa, validando esquema HTTP ou HTTPS, ausência de credenciais na URL e recusa de hosts de loopback, link-local e metadados da nuvem, repetindo essa validação no worker antes de conectar.
- **FR-002**: O sistema deve tratar a chave de cada conexão como somente escrita: cifrá-la antes de persistir com uma chave única fornecida ao entrypoint por secret do Docker Swarm ou variável de ambiente, sem rotação automática, nunca devolvê-la em resposta, log ou manifesto, expor apenas `segredo_definido` e uma máscara fixa sem caracteres da chave, preservar a chave quando a edição não informar outra e substituí-la quando informar.
- **FR-003**: O sistema deve permitir desativar e reativar uma conexão preservando vínculos, histórico e vetores já publicados, impedir que uma conexão desativada seja usada em nova publicação ou nova execução e permitir a exclusão definitiva somente de conexão sem Base vinculada, com 409 quando houver uso.
- **FR-004**: O sistema deve oferecer listagem, detalhe, edição, desativação, reativação e exclusão de conexões por `/api/v1/conexoes`, com `id`, `nome`, `tipo`, `situacao`, configuração não secreta, `segredo_definido`, quantidade de Bases em uso, autoria e datas, restritas a owner e admin da mesma equipe e projeto, e registrar em `eventos_conexao` cada criação, edição, troca de chave, desativação, reativação e exclusão com a pessoa autora, a ação e o horário, sem a chave e sem valores de campos secretos, retidos por 90 dias.
- **FR-005**: O sistema deve calcular a prévia dos chunks por `POST /api/v1/ingestao/previa` a partir de arquivos `.md` enviados ou da base preparada e dos parâmetros de divisão, devolvendo documentos, total de chunks, tamanho médio, avisos, arquivos com configuração própria e chunks paginados com documento de origem, posição, tamanho e texto, sem persistir nada.
- **FR-006**: O sistema deve validar os parâmetros de divisão: splitter `header` ou `recursive`, tamanho de chunk inteiro entre 200 e 4000 caracteres, overlap inteiro entre 0 e a metade do tamanho (sempre menor que o tamanho), com os limites expostos por `GET /api/v1/ingestao/padroes`, e pré-preencher os valores padrão de `config.yaml` (header, 1000 e 200).
- **FR-007**: O sistema deve manter a precedência atual do chunker: a configuração do frontmatter de cada arquivo (`splitter`, inclusive `qa`, `chunk_size_recommended` e `chunk_overlap_recommended`) prevalece sobre os parâmetros do formulário, e tanto a prévia quanto a execução aplicam exatamente a mesma regra.
- **FR-008**: O sistema deve estender `POST /api/v1/bases` para receber splitter, tamanho, overlap, `conexao_embeddings_id`, `conexao_vector_store_id`, coleção e `iniciar_execucao`, exigindo conexões ativas do tipo correto na mesma equipe e projeto, e quando `iniciar_execucao` for verdadeiro criar a execução na mesma requisição.
- **FR-009**: O sistema deve comparar, antes de criar qualquer registro, a dimensão declarada na conexão de embeddings com a dimensão da coleção obtida por `describe_scope` do vector store da conexão Qdrant, bloquear a publicação com 409 e mensagem clara quando divergirem e aceitar coleção inexistente, expondo a mesma verificação em `GET /api/v1/ingestao/dimensao` (somente leitura) para que a etapa Publicação mostre as dimensões e bloqueie o botão antes de publicar.
- **FR-010**: O sistema deve executar a publicação reaproveitando a sincronização por escopo lógico da SPEC-0002, sem etapa nem conexão de Record Manager, e expor na execução e na interface as contagens de pontos previstos, inseridos, mantidos e removidos.
- **FR-011**: O sistema deve guardar na Base o splitter, o tamanho, o overlap e os identificadores das duas conexões, usar esses valores em qualquer nova execução ou repetição da Base e manter Bases anteriores a esta entrega, sem vínculos, executando com a configuração global do entrypoint.
- **FR-012**: O sistema deve exibir o item de menu `Conexões` e as rotas `/conexoes` e `/conexoes/[id]` somente a owner e admin, recusar `member` na URL direta, e levar o botão de nova Base do Workspace, visível somente a owner e admin, à página `/workspaces/[id]/bases/nova`.
- **FR-013**: O sistema deve oferecer a página de nova Base com as etapas Arquivos, Divisão, Prévia e Publicação, manter arquivos e valores em memória do navegador ao voltar entre etapas, descartar tudo ao sair ou recarregar com aviso prévio de alterações pendentes, oferecer a base preparada na etapa Arquivos e remover o `UploadBaseSheet`.
- **FR-014**: O sistema deve cobrir loading, vazio, erro, permissão insuficiente, teclado e layout de uma coluna no mobile em todas as telas novas, com erro de campo abaixo do campo, `Alert` com Tentar novamente nas falhas de prévia e publicação, foco no título da etapa ao trocar e resultados anunciados por região `aria-live`.

#### Não funcionais

- **NFR-001**: A chave de conexão é cifrada em repouso com chave de cifra injetada pelo entrypoint, nunca trafega nos argumentos de job, em logs, no manifesto, na prévia, em mensagens de erro nem em respostas da API. **Verificação**: Testes que inspecionam o texto persistido, os argumentos do job, a captura de logs e todas as respostas; varredura de strings com a chave de teste.
- **NFR-002**: Cada operação de conexão, prévia e publicação respeita papel e escopo: member é recusado, outra equipe ou projeto recebe 404 sem revelar existência, e nenhuma conexão cruza o tenant. **Verificação**: Testes de integração por papel e por tenant em cada endpoint novo.
- **NFR-003**: A prévia não persiste nada e reaproveita os limites do envio atual (50 arquivos, 5 MB por arquivo, 50 MB por lote, UTF-8) sem criar retenção temporária nem chamar embeddings ou vector store. **Verificação**: Testes com storage, repositório, vector store e embeddings falsos que falham se forem tocados, mais testes de limite.
- **NFR-004**: As telas novas são operáveis por teclado, anunciam resultados a tecnologia assistiva, mantêm contraste dos tokens existentes em tema claro e escuro e usam uma coluna abaixo do breakpoint mobile. **Verificação**: Testes Vitest com Testing Library e verificação de acessibilidade como nos `*.a11y.test.tsx` existentes, mais conferência visual registrada por tarefa.
- **NFR-005**: A entrega não quebra o contrato atual: Bases anteriores continuam executáveis, a migração Alembic só adiciona schema, e as fronteiras de `src/app` com `src/pipeline` e de providers permanecem verdes. **Verificação**: `uv run pytest` completo com `tests/test_application_boundaries.py`, `tests/test_provider_boundaries.py` e `tests/test_app_migrations.py`, mais `uv run ruff check`.

#### Erros e casos-limite

- Conexão com URL inválida, dimensões inválidas ou tipo desconhecido → 422 com mensagem do campo e nada gravado.
- Edição de conexão sem chave → a chave anterior permanece; edição com chave vazia explícita em conexão que exige chave → 422.
- Exclusão de conexão em uso → 409 com a quantidade de Bases; desativação em uso → permitida e preserva vínculos.
- Prévia com parâmetros ou arquivos fora dos limites → 400 ou 422 com mensagem, sem leitura posterior nem gravação.
- Arquivo sem texto útil ou sem chunks após a divisão → a prévia informa zero chunks com aviso e a Publicação permanece bloqueada.
- Publicação com conexão desativada, de outro escopo ou de tipo trocado → 409 ou 404 e nada gravado.
- Dimensão da conexão diferente da coleção → 409 com as duas dimensões e nada gravado; coleção inexistente → permitida.
- Falha do worker ao decifrar a chave ou ao chamar o provedor → execução `failed` com mensagem genérica e detalhe somente nos logs do worker, sem segredo.
- Conexão desativada depois da publicação e repetição de execução → 409 pedindo reativar ou trocar a conexão.
- Qdrant inacessível ou sem permissão durante a verificação de dimensão → `describe_scope` devolve mapa vazio, a coleção é tratada como inexistente e a falha aparece na execução (`failed`, mensagem genérica); nenhum dado é gravado antes disso.
- Chave de cifra ausente no entrypoint → o backend recusa criar ou usar conexões com erro de configuração, sem expor valores.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI com SQLAlchemy 2, Alembic, PostgreSQL e Procrastinate (`src/app/`); pipeline em `src/pipeline/` acessado somente pela fachada `src/pipeline/service.py`.
- `POST /api/v1/bases` (`src/app/routers/bases.py`) valida arquivos, grava no storage e cria a Base; `POST /api/v1/bases/{id}/executions` (`src/app/routers/executions.py`) cria a execução e chama `process_base_task.defer` com `embedding` e `vector_store` copiados de `AppSettings` (configuração global injetada em `src/app/main.py`).
- `process_base_task` (`src/app/tasks.py`) materializa os arquivos, chama `service.run_pipeline(only_chunks=True)` e `service.sync_vector_store`. `build_pipeline_config` ainda não injeta a seção `chunking`, que a fachada já lê.
- `chunker._get_splitter_config` dá prioridade ao frontmatter; `config.yaml` define padrões `header`, 1000 e 200.
- Frontend Next.js 16, React 19, Tailwind v4, shadcn/ui `base-nova` e Vitest; `UploadBaseSheet`, `PainelProgresso`, `DataGridPessoas`, `PessoaFormSheet`, `PageHeader` e `IndicadorProcessamento` são os blocos de referência.

#### Arquitetura e módulos

- Novo módulo `src/app/conexoes.py`: regras de domínio das conexões (validação de URL, cifra e decifra com `cryptography.fernet`, máscara, resolução de configuração para o pipeline). A chave de cifra entra por `AppSettings` (novo campo), injetada pelo entrypoint.
- Novo router `src/app/routers/conexoes.py` para `/api/v1/conexoes`, e novo router `src/app/routers/ingestao.py` para `/api/v1/ingestao/padroes` e `/api/v1/ingestao/previa`, registrados em `src/app/main.py`.
- `src/app/repo.py` ganha o repositório de conexões (listar, obter, criar, atualizar, contar uso) com escopo de tenant e projeto.
- `src/pipeline/service.py` ganha duas funções finas: `preview_chunks(config, input_dir)` (reaproveita `run_pipeline(only_chunks=True)` sem sincronizar) e `describe_collection(vector_config)` (usa `describe_scope` e devolve existência e dimensão); nenhuma altera `contracts.py`.
- `process_base_task` passa a receber `conexao_embeddings_id` e `conexao_vector_store_id` em vez de `embedding` e `vector_store`; o worker lê as conexões, decifra e monta a configuração. Bases sem vínculos usam `AppSettings` como hoje.
- Ponto de extensão: novo tipo de conexão é uma entrada no registro de tipos de `src/app/conexoes.py` e na `ProviderFactory`, sem tocar nas rotas.

#### Migrations

- Nova revisão Alembic `alembic/versions/0026_conexoes_ingestao.py` (down_revision `0021_assistente` ou a cabeça atual na implementação): cria `conexoes` e `eventos_conexao` e adiciona em `bases` as colunas `conexao_embeddings_id`, `conexao_vector_store_id` (FKs anuláveis, `ON DELETE RESTRICT`) e `chunking` (JSON anulável). Compatível com Bases anteriores (colunas nulas) e reversível: o downgrade remove somente o schema novo.
- Segue a regra do projeto: tarefa `[CODE]` com o caminho da revisão, verificação por `uv run alembic upgrade head` no banco de teste e `uv run alembic current`.

#### Models

- `Conexao` em `src/app/models.py`: `id`, `tenant_id`, `project_id`, `nome`, `tipo`, `situacao`, `configuracao` (JSON não secreto), `segredo_cifrado` (Text anulável), `criado_por` (FK Pessoa opcional), `criado_em`, `atualizada_em`. Invariantes: `tipo` em {`embeddings_openai`, `qdrant`}; `situacao` em {`ativa`, `desativada`}; `nome` único por equipe e projeto entre conexões não excluídas.
- `EventoConexao` em `src/app/models.py`: `id`, `tenant_id`, `project_id`, `conexao_id` (sem FK, sobrevive à exclusão), `acao`, `ator_pessoa_id`, `criado_em`; sem campo de valor, para nunca guardar segredo. Purga em 90 dias junto de `purgar_dados_de_acesso_task`.
- `Base` ganha `conexao_embeddings_id`, `conexao_vector_store_id` e `chunking` (`{splitter, chunk_size, chunk_overlap}`).

#### Controllers e casos de uso

- `POST /api/v1/conexoes`, `GET /api/v1/conexoes`, `GET /api/v1/conexoes/{id}`, `PATCH /api/v1/conexoes/{id}`, `POST /api/v1/conexoes/{id}/desativar`, `POST /api/v1/conexoes/{id}/reativar`, `DELETE /api/v1/conexoes/{id}`: todos exigem `require_write_role`; `src/app/routers/conexoes.py`.
- `GET /api/v1/ingestao/padroes`, `GET /api/v1/ingestao/dimensao` e `POST /api/v1/ingestao/previa`: `src/app/routers/ingestao.py`; a prévia grava os arquivos recebidos somente em diretório temporário do processo, apagado ao fim da requisição, sem tocar storage, banco, embeddings ou vector store.
- `POST /api/v1/bases` estendido em `src/app/routers/bases.py`: valida conexões e dimensão antes de qualquer gravação; `iniciar_execucao` cria a execução com `repo.inserir_execucao_ativa` e agenda o job.
- `POST /api/v1/bases/{id}/executions` e `retry` passam a agendar por identificadores de conexão e recusam conexão desativada com 409.

#### Views e experiência

- Ver a seção 10: páginas `/workspaces/[id]/bases/nova`, `/conexoes` e `/conexoes/[id]`.

#### Queries e repositórios

- `repo.listar_conexoes(session, identity)` filtra por `tenant_id` e `project_id` e ordena por nome; `repo.contar_bases_da_conexao(session, conexao_id)` conta Bases não apagadas; índice em (`tenant_id`, `project_id`, `situacao`). A listagem é pequena e não pagina nesta entrega.

#### Jobs e processamento assíncrono

- `process_base_task` mantém o job único e idempotente por execução; o retry cria nova execução. A chave nunca entra nos argumentos do job: o worker consulta `Conexao` pelo identificador, decifra em memória e descarta. Falha ao decifrar marca a execução como `failed` com mensagem genérica.

#### Estrutura de arquivos

```text
specs/review/0026-fluxo-de-ingestao-com-etapas-e-conexoes/
  spec.md
  research/
alembic/versions/0026_conexoes_ingestao.py
src/app/conexoes.py
src/app/routers/conexoes.py
src/app/routers/ingestao.py
src/app/models.py            (Conexao, colunas em Base)
src/app/repo.py
src/app/tasks.py
src/app/settings.py          (chave de cifra)
src/app/main.py
src/pipeline/service.py      (preview_chunks, describe_collection)
tests/test_app_conexoes.py
tests/test_app_ingestao_previa.py
tests/test_app_publicacao.py
tests/test_app_tasks_conexoes.py
frontend/src/features/conexoes/
frontend/src/features/ingestao/
frontend/src/app/(autenticado)/conexoes/
frontend/src/app/(autenticado)/workspaces/[id]/bases/nova/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `conexoes` | `id` (UUID em texto) | `tenant_id`, `project_id`, `nome` (1 a 80 caracteres), `tipo`, `situacao`, `configuracao` (modelo, URL base opcional e dimensões para embeddings; URL para Qdrant), `segredo_cifrado` (nunca em claro), `criado_por`, `criado_em`, `atualizada_em` | Pertence a tenant e projeto; criada por Pessoa; referenciada por zero ou mais Bases |
| `eventos_conexao` | `id` | `tenant_id`, `project_id`, `conexao_id`, `acao` (criada, editada, chave_trocada, desativada, reativada, excluida), `ator_pessoa_id`, `criado_em`; nunca valores de campos | Referencia Pessoa autora; retida por 90 dias; sem tela de consulta nesta entrega |
| `bases` (estendida) | `id` existente | `conexao_embeddings_id`, `conexao_vector_store_id` anuláveis; `chunking` JSON anulável com `splitter`, `chunk_size` e `chunk_overlap`; Bases anteriores ficam nulas | Referencia duas conexões com `ON DELETE RESTRICT` |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Conexão | `ativa` | desativar | `desativada` | Vínculos, histórico e vetores permanecem; não é elegível para nova publicação nem nova execução |
| Conexão | `desativada` | reativar | `ativa` | Volta às opções de publicação |
| Conexão | qualquer | excluir sem uso | removida | Somente sem Base vinculada; com uso retorna 409 |
| Conexão | qualquer | editar | mesmo estado | Chave preservada quando não informada; edição não altera Bases já publicadas além de passar a valer em novas execuções |

#### Migração e retenção

- Migração apenas aditiva. Conexões permanecem até serem excluídas por owner ou admin sem uso; desativar não apaga. Não há retenção temporária: a prévia não persiste. Eventos de conexão são purgados após 90 dias pela tarefa periódica existente. Atualizar `.specsfy/DATABASE.md` manualmente após a migração, conforme a regra do projeto.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. Owner e admin conduzem envio, prévia e publicação e administram conexões em telas; member apenas consulta, como hoje.

#### Stack e convenções de interface

- Next.js 16 App Router, React 19, TypeScript, Tailwind v4, shadcn/ui `base-nova` (Base UI), registry ReUI configurado sem blocos instalados, Vitest com Testing Library, cliente `apiFetch`/`apiJson` e sessão em `sessionStorage` (fontes: `INTERFACE.md`, `frontend/package.json`, `frontend/components.json`). Preservar: navegação Workspaces para todos e Pessoas para owner e admin, `MenuPessoa`, `PageHeader` único, `DataGrid` com coluna `ID` e linha clicável, `Sheet` para formulários curtos, `Dialog` para confirmações, `Button loading`, `IndicadorProcessamento`, `PainelProgresso` e `Breadcrumb`. Mudar: o envio deixa de criar e executar de uma vez; surge uma superfície de Conexões; o `UploadBaseSheet` é removido, com atualização de `INTERFACE.md`, testes e consumidores (`workspaces/[id]/page.tsx`).

#### Telas e responsabilidades

- **Nova Base** (`/workspaces/[id]/bases/nova`): owner e admin; reúne Arquivos, Divisão, Prévia e Publicação e termina na página da Base.
- **Conexões** (`/conexoes`): owner e admin; lista, cria, edita, desativa, reativa e exclui conexões.
- **Conexão** (`/conexoes/[id]`): owner e admin; detalhe com configuração não secreta, chave mascarada, situação, uso e autoria.
- **Workspace** (`/workspaces/[id]`): ganha o botão "Nova Base" que leva à página de etapas.
- **Base** (`/execucoes/[id]`): recebe o usuário após publicar, com `PainelProgresso`.

#### Fluxo de informação e navegação

- A pessoa abre o Workspace, aciona "Nova Base", percorre as etapas e, ao publicar, vai à página da Base. Voltar entre etapas preserva arquivos e valores em memória; sair ou recarregar descarta tudo, com aviso antes de sair. Breadcrumbs: Equipe → Workspaces → Workspace → Nova Base; Equipe → Conexões; Equipe → Conexões → Conexão.

#### Menus e navegação principal

- Menu principal: Workspaces (todos), Pessoas (owner e admin) e o novo item Conexões (owner e admin), com destino `/conexoes`, mesma regra de visibilidade de Pessoas em `frontend/src/app/(autenticado)/layout.tsx`, colapsando junto dos demais no mobile. A rota `/workspaces/[id]/bases/nova` não tem item de menu: é alcançada pelo botão do Workspace, que a própria jornada comprova. `member` não vê Conexões e a URL direta é recusada.

#### Formulários e ações

- **Arquivos**: seletor de múltiplos `.md` com os limites do backend (50 arquivos, 5 MB por arquivo, 50 MB por lote), lista dos selecionados com remoção, opção "Usar base preparada" e ação Próxima desabilitada sem arquivos.
- **Divisão**: `Select` de splitter (Markdown por cabeçalhos ou recursivo por caracteres), tamanho e overlap pré-preenchidos pelos padrões de `GET /api/v1/ingestao/padroes`, ajuda curta, validação em linha (overlap menor que o tamanho, mínimo e máximo), erro abaixo do campo e aviso listando arquivos com `splitter: qa` ou configuração própria que ficam fora desses parâmetros; sem seção avançada.
- **Prévia**: contagens no topo, avisos e lista paginada somente leitura de chunks com documento, posição, tamanho e texto truncado com "ver mais", com filtro por documento; ajustar significa voltar a Divisão.
- **Publicação**: `Select` de conexão de embeddings e de conexão Qdrant (somente ativas), comparação de dimensões em linha, campo de coleção, resumo final (arquivos, chunks, modelo, coleção, destino) e botão "Publicar" desabilitado com a razão visível enquanto houver divergência de dimensão, conexão desativada ou ausência de conexão ativa.
- **Conexões**: criação e edição em `Sheet` (nome, tipo, campos do tipo, chave com campo vazio e máscara na edição); desativar e reativar por botão; excluir por `Dialog` que confirma a consequência. Padrão: página para o fluxo e painel lateral para os formulários curtos.

#### Composição e disposição

- Páginas com `PageHeader` e `Breadcrumb`, conteúdo em duas colunas responsivas (formulário e contexto) e uma coluna no mobile; as etapas formam uma barra de progresso navegável acima do conteúdo. A lista de Conexões usa `DataGrid` em largura inteira. Densidade igual à de Pessoas e Workspaces.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Nova Base | `FluxoIngestao` | Estado em memória e navegação entre etapas | `frontend/src/features/ingestao/FluxoIngestao.tsx` | Composição de etapas | Próprio | Novo; substitui `UploadBaseSheet` |
| Nova Base | `EtapaArquivos` | Seleção de arquivos e base preparada | `frontend/src/features/ingestao/EtapaArquivos.tsx` | `Input`, `Button`, `Alert` | Próprio sobre shadcn/ui | Novo; reaproveita limites e validação do sheet atual |
| Nova Base | `EtapaDivisao` | Formulário de splitter, tamanho e overlap | `frontend/src/features/ingestao/EtapaDivisao.tsx` | `Select`, `Input`, `Label`, `Alert` | Próprio sobre shadcn/ui | Novo |
| Nova Base | `EtapaPrevia` | Resumo e lista paginada de chunks | `frontend/src/features/ingestao/EtapaPrevia.tsx` | `Badge`, `Select`, `Button`, `Skeleton` | Próprio sobre shadcn/ui | Novo; texto truncado reaproveita padrão de `ChunksFontes` |
| Nova Base | `EtapaPublicacao` | Conexões, coleção, resumo e Publicar | `frontend/src/features/ingestao/EtapaPublicacao.tsx` | `Select`, `Input`, `Button`, `Alert` | Próprio sobre shadcn/ui | Novo |
| Nova Base | `BarraEtapas` | Indicador navegável das quatro etapas | `frontend/src/features/ingestao/BarraEtapas.tsx` | Lista ordenada com `aria-current` | Próprio | Novo |
| Nova Base | `useFluxoIngestao` | Chamadas à prévia e à publicação, estado e saída protegida | `frontend/src/features/ingestao/useFluxoIngestao.ts` | Hook | Próprio | Novo; segue `useAssistente` |
| Conexões | `DataGridConexoes` | Listagem com coluna ID, linha clicável e ações | `frontend/src/features/conexoes/DataGridConexoes.tsx` | Tabela semântica | Próprio | Estende o padrão de `DataGridPessoas` |
| Conexões | `ConexaoFormSheet` | Criação e edição em painel lateral | `frontend/src/features/conexoes/ConexaoFormSheet.tsx` | `Sheet`, `Input`, `Select`, `Label` | Próprio sobre shadcn/ui | Estende o padrão de `PessoaFormSheet` |
| Conexões | `ExcluirConexaoDialog` | Confirmação de exclusão e desativação | `frontend/src/features/conexoes/ExcluirConexaoDialog.tsx` | `Dialog` | Próprio sobre shadcn/ui | Estende `ExcluirBaseDialog` |
| Conexão | `DetalheConexao` | Detalhe com configuração não secreta | `frontend/src/features/conexoes/DetalheConexao.tsx` | `DetailLists` | Próprio | Reusa `DetailLists` |
| Todas | `PageHeader`, `Breadcrumb` do shell, `PainelProgresso`, `IndicadorProcessamento` | Cabeçalho, contexto e feedback | arquivos existentes | `PageHeader`, `PainelProgresso` | Próprio | Reuso sem mudança de API |

- shadcn/ui fornece as primitives já instaladas (`Button`, `Input`, `Label`, `Select`, `Sheet`, `Dialog`, `Alert`, `Badge`, `Skeleton`); nenhum bloco ReUI `@reui/c-*` é usado nesta entrega (DEC-014): as composições acima são próprias sobre as primitives, como as telas já entregues.
- A lista acima deve ser espelhada em `INTERFACE.md` a cada tarefa; a página apenas compõe esses blocos.

#### Estados e acessibilidade

- Loading: prévia e publicação com `Button loading` e `IndicadorProcessamento`. Vazio: sem conexão ativa a Publicação orienta para Conexões; sem arquivos, Próxima fica desabilitada; sem chunks, aviso e Publicar bloqueado. Erro: erro de campo abaixo do campo em vermelho com foco no primeiro erro; falha de prévia ou publicação em `Alert` com Tentar novamente, sem perder o preenchimento. Sucesso: navegação para a Base e anúncio por `aria-live`. Permissão insuficiente: member não vê Conexões nem o botão e a URL direta é recusada. Teclado e foco: etapas navegáveis, foco no título da etapa ao trocar, lista de chunks acessível, linha de `DataGrid` operável por teclado. Responsivo: uma coluna no mobile.
- O `Breadcrumb` mantém a equipe visível, usa links válidos nos itens anteriores e marca a tela atual com semântica de página.

#### Contrato CRUD

- A tela Conexões é um CRUD e usa o mesmo `PageHeader` componentizado de Pessoas e Workspaces em lista, detalhe, criação e edição, com variações por props.
- A listagem usa `DataGrid` em largura total, mantém a coluna `ID` visível junto de nome, tipo e situação, transforma a linha inteira em link para o detalhe por mouse e teclado e oferece botões independentes de editar e apagar, além de desativar e reativar; apagar respeita a permissão e confirma a consequência.
- Os componentes recorrentes são registrados em `INTERFACE.md` e reaproveitados antes de qualquer implementação nova.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre durante a implementação, mesmo sem pedido da pessoa, e confere bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, nos viewports desktop e mobile, em tema claro e escuro, com conteúdo curto e longo, foco e overflow.
- Cada tarefa registra a forma de conferência, viewport, estados percorridos, achados e ajustes; tarefa sem superfície visual registra `Não aplicável` com motivo concreto.

#### APIs expostas

- `GET /api/v1/ingestao/padroes` → `{splitter, chunk_size, chunk_overlap, limites}`; autenticação por sessão; owner e admin.
- `GET /api/v1/ingestao/dimensao?conexao_embeddings_id=&conexao_vector_store_id=&collection_name=` → `{embeddings, colecao, compativel}` (`colecao` nulo quando a coleção não existe e `compativel` verdadeiro nesse caso); somente leitura, owner e admin; erros 403, 404 e 409 para conexão desativada.
- `POST /api/v1/ingestao/previa` (multipart: `arquivos`, `usar_base_preparada`, `splitter`, `chunk_size`, `chunk_overlap`, `pagina`, `tamanho_pagina`, `documento` opcional) → `{resumo, avisos, arquivos_com_configuracao_propria, chunks, pagina, total}`; erros 400, 403, 422.
- `POST /api/v1/conexoes` e `PATCH /api/v1/conexoes/{id}` (JSON com `segredo` somente de entrada); respostas sem o segredo; erros 403, 404, 409, 422.
- `POST /api/v1/bases` (multipart existente mais `splitter`, `chunk_size`, `chunk_overlap`, `conexao_embeddings_id`, `conexao_vector_store_id`, `iniciar_execucao`) → `{base_id, workspace_id, collection_name, metadados_chunk, execution_id?}`; compatível: sem os campos novos o comportamento anterior permanece.
- Versionamento: prefixo `/api/v1` mantido; campos novos são opcionais.

#### APIs externas utilizadas

- OpenAI Embeddings (ou endpoint compatível pela URL base da conexão) e Qdrant, ambos acessados somente por `src/pipeline/providers/`, com as chaves das conexões. Timeout, retry e fallback seguem os adapters existentes; nenhuma chamada externa ocorre na prévia.

#### Documentação das APIs consultadas

- Flowise Document Stores (referência de jornada, ver seção 2). Contratos de OpenAI e Qdrant não foram consultados nesta etapa: a primeira entrega reaproveita os adapters existentes sem mudar chamadas.

#### Eventos e outros contratos

- Argumentos de `process_base_task`: `execution_id`, `base_id`, `tenant_id`, `project_id`, `conexao_embeddings_id`, `conexao_vector_store_id` (sem chaves); Bases legadas continuam podendo enfileirar o formato anterior durante a transição de jobs já enfileirados.

### 11. Estratégia TDD

- **Unidade**: validação de URL e parâmetros, cifra e máscara de `src/app/conexoes.py`, precedência de configuração e componentes de etapa.
- **Integração/contrato**: endpoints novos e estendidos com PostgreSQL de teste (rollback transacional), vector store e embeddings falsos de `tests/_fakes_vectorstore.py`, worker com `process_base_task` e fronteiras de módulos.
- **BDD/aceite**: o Gherkin da seção 6 orienta o desenho dos testes; não há arquivos `.feature`.
- **Runner TDD**: backend com Pytest (`uv run pytest`) e Ruff; frontend com Vitest (`npm run test:tdd` em `frontend/`, já materializado).
- **E2E**: Não aplicável nesta entrega; a jornada é coberta por testes de integração e de componente.
- **Verificação manual**: conferência visual por tarefa nos viewports e temas, porque a revisão visual é inevitável para bordas, espaçamentos e tipografia.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, FR-004, NFR-001, NFR-002, AC-001 | AC-001 na seção 6 | Cadastrar conexão de embeddings OpenAI em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-001 FR-002 FR-004 NFR-001 NFR-002 AC-001` | Observado em 2026-10-06: `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe | Verde em 2026-10-06: `uv run pytest tests/test_app_conexoes.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-001, FR-001, FR-002, FR-004, NFR-001, AC-002 | AC-002 na seção 6 | Cadastrar conexão Qdrant e preservar a chave na edição em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-001 FR-002 FR-004 NFR-001 AC-002` | Observado em 2026-10-06: `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe | Verde em 2026-10-06: `uv run pytest tests/test_app_conexoes.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-001, FR-001, FR-002, NFR-002, AC-003 | AC-003 na seção 6 | Recusar conexão inválida em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-001 FR-002 NFR-002 AC-003` | Observado em 2026-10-06: `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe | Verde em 2026-10-06: `uv run pytest tests/test_app_conexoes.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-001, FR-003, FR-004, FR-008, NFR-002, AC-004 | AC-004 na seção 6 | Desativar e reativar uma conexão em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-003 FR-004 FR-008 NFR-002 AC-004` | Observado em 2026-10-06: `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe | Verde em 2026-10-06: `uv run pytest tests/test_app_conexoes.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-001, FR-003, FR-004, NFR-002, AC-005 | AC-005 na seção 6 | Excluir somente conexão sem uso em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-003 FR-004 NFR-002 AC-005` | Observado em 2026-10-06: `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe | Verde em 2026-10-06: `uv run pytest tests/test_app_conexoes.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-001, US-004, FR-004, FR-012, NFR-002, AC-006 | AC-006 na seção 6 | Recusar acesso de member e de outra equipe às conexões em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 US-004 FR-004 FR-012 NFR-002 AC-006` | Observado em 2026-10-06: `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe | Verde em 2026-10-06: `uv run pytest tests/test_app_conexoes.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-002, FR-005, FR-006, FR-007, NFR-003, AC-007 | AC-007 na seção 6 | Calcular a prévia com splitter por cabeçalhos em `tests/test_app_ingestao_previa.py` com marcador próprio `SPECSFY: SPEC-0026 US-002 FR-005 FR-006 FR-007 NFR-003 AC-007` | Observado em 2026-10-06: `404 Not Found`: a rota `/api/v1/ingestao/previa` ainda não existe | Verde em 2026-10-06: `uv run pytest tests/test_app_ingestao_previa.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-002, FR-005, FR-007, NFR-003, AC-008 | AC-008 na seção 6 | Respeitar o frontmatter na prévia e avisar sobre os arquivos afetados em `tests/test_app_ingestao_previa.py` com marcador próprio `SPECSFY: SPEC-0026 US-002 FR-005 FR-007 NFR-003 AC-008` | Observado em 2026-10-06: `404 Not Found`: a rota `/api/v1/ingestao/previa` ainda não existe | Verde em 2026-10-06: `uv run pytest tests/test_app_ingestao_previa.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-002, FR-005, FR-006, NFR-003, AC-009 | AC-009 na seção 6 | Recusar parâmetros e arquivos inválidos na prévia em `tests/test_app_ingestao_previa.py` com marcador próprio `SPECSFY: SPEC-0026 US-002 FR-005 FR-006 NFR-003 AC-009` | Observado em 2026-10-06: `404 Not Found`: a rota `/api/v1/ingestao/previa` ainda não existe | Verde em 2026-10-06: `uv run pytest tests/test_app_ingestao_previa.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-003, FR-007, FR-008, FR-009, FR-010, FR-011, NFR-005, AC-010 | AC-010 na seção 6 | Publicar uma Base com conexões ativas em `tests/test_app_publicacao.py` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-007 FR-008 FR-009 FR-010 FR-011 NFR-005 AC-010` | Observado em 2026-10-06: `404 Not Found` já na criação das conexões (`/api/v1/conexoes`) e fachada sem `describe_collection` | Verde em 2026-10-06: `uv run pytest tests/test_app_publicacao.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-003, FR-008, FR-009, NFR-002, AC-011 | AC-011 na seção 6 | Bloquear a publicação quando a dimensão diverge em `tests/test_app_publicacao.py` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-008 FR-009 NFR-002 AC-011` | Observado em 2026-10-06: `404 Not Found` já na criação das conexões (`/api/v1/conexoes`) e fachada sem `describe_collection` | Verde em 2026-10-06: `uv run pytest tests/test_app_publicacao.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-003, FR-003, FR-008, FR-009, FR-011, NFR-002, AC-012 | AC-012 na seção 6 | Recusar conexão desativada ou de outra equipe na publicação em `tests/test_app_publicacao.py` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-003 FR-008 FR-009 FR-011 NFR-002 AC-012` | Observado em 2026-10-06: `404 Not Found` já na criação das conexões (`/api/v1/conexoes`) e fachada sem `describe_collection` | Verde em 2026-10-06: `uv run pytest tests/test_app_publicacao.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-003, FR-010, FR-011, NFR-001, NFR-005, AC-013 | AC-013 na seção 6 | Decifrar a chave somente no worker e repetir com os mesmos parâmetros em `tests/test_app_tasks_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-001 NFR-005 AC-013` | Observado em 2026-10-06: `404 Not Found` na criação das conexões e argumentos de job ainda com `embedding` e `vector_store` | Verde em 2026-10-06: `uv run pytest tests/test_app_tasks_conexoes.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-003, FR-010, FR-011, NFR-005, AC-014 | AC-014 na seção 6 | Executar Base legada com a configuração global em `tests/test_app_tasks_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-005 AC-014` | Observado em 2026-10-06: `TypeError: process_base_task() got an unexpected keyword argument 'conexao_embeddings_id'` | Verde em 2026-10-06: `uv run pytest tests/test_app_tasks_conexoes.py -q` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-002, US-004, FR-006, FR-013, FR-014, NFR-004, AC-015 | AC-015 na seção 6 | Percorrer as etapas preservando o preenchimento em `frontend/src/features/ingestao/FluxoIngestao.test.tsx` com marcador próprio `SPECSFY: SPEC-0026 US-002 US-004 FR-006 FR-013 FR-014 NFR-004 AC-015` | Observado em 2026-10-06: `@/features/ingestao/FluxoIngestao ainda não existe (comportamento ainda ausente)` | Verde em 2026-10-06: `npm run test:tdd -- src/features/ingestao/FluxoIngestao.test.tsx` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-004, FR-012, FR-013, FR-014, AC-016 | AC-016 na seção 6 | Substituir o envio atual e oferecer a base preparada em `frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx` com marcador próprio `SPECSFY: SPEC-0026 US-004 FR-012 FR-013 FR-014 AC-016` | Observado em 2026-10-06: `Unable to find an accessible element with the role "link" and name /nova base/i` | Verde em 2026-10-06: `npm run test:tdd -- src/app/(autenticado)/workspaces/[id]/page.test.tsx` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-002, US-003, FR-013, FR-014, NFR-004, AC-017 | AC-017 na seção 6 | Mostrar loading, vazio e erro nas etapas em `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` com marcador próprio `SPECSFY: SPEC-0026 US-002 US-003 FR-013 FR-014 NFR-004 AC-017` | Observado em 2026-10-06: `@/features/ingestao/EtapaPublicacao ainda não existe (comportamento ainda ausente)` | Verde em 2026-10-06: `npm run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-001, FR-012, FR-014, NFR-004, AC-018 | AC-018 na seção 6 | Listar e administrar conexões na interface em `frontend/src/features/conexoes/DataGridConexoes.test.tsx` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-012 FR-014 NFR-004 AC-018` | Observado em 2026-10-06: `@/features/conexoes/DataGridConexoes ainda não existe (comportamento ainda ausente)` | Verde em 2026-10-06: `npm run test:tdd -- src/features/conexoes/DataGridConexoes.test.tsx` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |
| US-003, FR-010, FR-014, AC-019 | AC-019 na seção 6 | Acompanhar inseridos, mantidos e removidos depois de publicar em `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-010 FR-014 AC-019` | Observado em 2026-10-06: `@/features/ingestao/EtapaPublicacao ainda não existe (comportamento ainda ausente)` | Verde em 2026-10-06: `npm run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx` | Regressão completa em 2026-10-06: backend `uv run pytest` e frontend `npm run test:tdd` sem falhas |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-001 | AC-002 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-001 | AC-003 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-002 | AC-001 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-002 | AC-002 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-002 | AC-003 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-003 | AC-004 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-003 | AC-005 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-003 | AC-012 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-004 | AC-001 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-004 | AC-002 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-004 | AC-004 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-004 | AC-005 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-004 | AC-006 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-005 | AC-007 | Integração | `tests/test_app_ingestao_previa.py` | Passed |
| FR-005 | AC-008 | Integração | `tests/test_app_ingestao_previa.py` | Passed |
| FR-005 | AC-009 | Integração | `tests/test_app_ingestao_previa.py` | Passed |
| FR-006 | AC-007 | Integração | `tests/test_app_ingestao_previa.py` | Passed |
| FR-006 | AC-009 | Integração | `tests/test_app_ingestao_previa.py` | Passed |
| FR-006 | AC-015 | Componente | `frontend/src/features/ingestao/FluxoIngestao.test.tsx` | Passed |
| FR-007 | AC-007 | Integração | `tests/test_app_ingestao_previa.py` | Passed |
| FR-007 | AC-008 | Integração | `tests/test_app_ingestao_previa.py` | Passed |
| FR-007 | AC-010 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-008 | AC-004 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-008 | AC-010 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-008 | AC-011 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-008 | AC-012 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-009 | AC-010 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-009 | AC-011 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-009 | AC-012 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-010 | AC-010 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-010 | AC-013 | Integração | `tests/test_app_tasks_conexoes.py` | Passed |
| FR-010 | AC-014 | Integração | `tests/test_app_tasks_conexoes.py` | Passed |
| FR-010 | AC-019 | Componente | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Passed |
| FR-011 | AC-010 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-011 | AC-012 | Integração | `tests/test_app_publicacao.py` | Passed |
| FR-011 | AC-013 | Integração | `tests/test_app_tasks_conexoes.py` | Passed |
| FR-011 | AC-014 | Integração | `tests/test_app_tasks_conexoes.py` | Passed |
| FR-012 | AC-006 | Integração | `tests/test_app_conexoes.py` | Passed |
| FR-012 | AC-016 | Componente | `frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx` | Passed |
| FR-012 | AC-018 | Componente | `frontend/src/features/conexoes/DataGridConexoes.test.tsx` | Passed |
| FR-013 | AC-015 | Componente | `frontend/src/features/ingestao/FluxoIngestao.test.tsx` | Passed |
| FR-013 | AC-016 | Componente | `frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx` | Passed |
| FR-013 | AC-017 | Componente | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Passed |
| FR-014 | AC-015 | Componente | `frontend/src/features/ingestao/FluxoIngestao.test.tsx` | Passed |
| FR-014 | AC-016 | Componente | `frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx` | Passed |
| FR-014 | AC-017 | Componente | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Passed |
| FR-014 | AC-018 | Componente | `frontend/src/features/conexoes/DataGridConexoes.test.tsx` | Passed |
| FR-014 | AC-019 | Componente | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Passed |
| NFR-001 | AC-001 | Integração | `tests/test_app_conexoes.py` | Passed |
| NFR-001 | AC-002 | Integração | `tests/test_app_conexoes.py` | Passed |
| NFR-001 | AC-013 | Integração | `tests/test_app_tasks_conexoes.py` | Passed |
| NFR-002 | AC-001 | Integração | `tests/test_app_conexoes.py` | Passed |
| NFR-002 | AC-003 | Integração | `tests/test_app_conexoes.py` | Passed |
| NFR-002 | AC-004 | Integração | `tests/test_app_conexoes.py` | Passed |
| NFR-002 | AC-005 | Integração | `tests/test_app_conexoes.py` | Passed |
| NFR-002 | AC-006 | Integração | `tests/test_app_conexoes.py` | Passed |
| NFR-002 | AC-011 | Integração | `tests/test_app_publicacao.py` | Passed |
| NFR-002 | AC-012 | Integração | `tests/test_app_publicacao.py` | Passed |
| NFR-003 | AC-007 | Integração | `tests/test_app_ingestao_previa.py` | Passed |
| NFR-003 | AC-008 | Integração | `tests/test_app_ingestao_previa.py` | Passed |
| NFR-003 | AC-009 | Integração | `tests/test_app_ingestao_previa.py` | Passed |
| NFR-004 | AC-015 | Componente | `frontend/src/features/ingestao/FluxoIngestao.test.tsx` | Passed |
| NFR-004 | AC-017 | Componente | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Passed |
| NFR-004 | AC-018 | Componente | `frontend/src/features/conexoes/DataGridConexoes.test.tsx` | Passed |
| NFR-005 | AC-010 | Integração | `tests/test_app_publicacao.py` | Passed |
| NFR-005 | AC-013 | Integração | `tests/test_app_tasks_conexoes.py` | Passed |
| NFR-005 | AC-014 | Integração | `tests/test_app_tasks_conexoes.py` | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed em 2026-10-06
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/review/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md`
- **Achados**: 4 US, 14 FR, 5 NFR e 19 AC; cada US, FR e NFR coberto por no mínimo 3 AC; nenhum BLOCKER e nenhum P1. A revisão semântica encontrou cinco lacunas P2 e P3, corrigidas nas seções de origem (FR-001, AC-001, AC-002, AC-004, AC-005, AC-013, seções 10, 16, 17 e 18) antes do gate.
- **FIND-PROD-001** [P2] [Resolved] FR-004 exige eventos de conexão, mas nenhum cenário conferia a gravação — Refs: FR-004, AC-001, AC-002, AC-004, AC-005 — Evidence: src/app/models.py:1 — Effect: teste do histórico ficaria sem critério — Suggestion: Then dos quatro cenários registra o evento; aplicada.
- **FIND-PROD-002** [P2] [Resolved] Definition of Done não citava STACK, DATABASE, PROJECT e RULES apesar de mudar stack, persistência e capacidade — Refs: NFR-005 — Evidence: .specsfy/DATABASE.md:1 — Effect: documentação de contexto poderia ficar desatualizada — Suggestion: itens adicionados à seção 18; aplicada.
- **FIND-ARCH-001** [P2] [Resolved] A adoção de ReUI estava como decisão em aberto dentro da spec — Refs: FR-013 — Evidence: INTERFACE.md:1 — Effect: tarefas de interface sem composição definida — Suggestion: DEC-014 decide composições próprias sobre shadcn/ui; aplicada.
- **FIND-SEC-001** [P2] [Resolved] A revalidação de URL contra SSRF no worker só existia como risco — Refs: FR-001, NFR-002, AC-013 — Evidence: src/app/tasks.py:1 — Effect: conexão alterada depois do cadastro poderia alcançar host interno — Suggestion: FR-001 e AC-013 exigem a revalidação; aplicada.
- **FIND-ARCH-003** [P2] [Resolved] A etapa Publicação deve bloquear por divergência de dimensão, mas nenhuma API permitia conhecer a dimensão da coleção antes de publicar (achado ao materializar o AC-017 na fase RED) — Refs: FR-009, AC-011, AC-017 — Evidence: src/app/routers/bases.py:1 — Effect: o botão só poderia bloquear depois de um 409 — Suggestion: endpoint somente leitura `GET /api/v1/ingestao/dimensao` (DEC-016); aplicada.
- **FIND-ARCH-002** [P3] [Accepted] `describe_scope` devolve mapa vazio também para destino inacessível, então a verificação de dimensão não distingue ausência de falha de acesso — Refs: FR-009, AC-011 — Evidence: src/pipeline/providers/vectorstores/qdrant.py:93 — Effect: erro de acesso surge na execução, sem gravar dados — Suggestion: aceito pela DEC-015 em vez de ampliar o contrato neutro.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed em 2026-10-06
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/review/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md`
- **Achados**: 43 tarefas (19 RED TDD, 18 de código, 1 OPS e 4 de documentação), 258 itens de checklist e 42 de 42 IDs cobertos. As 19 tarefas RED (T001–T019) estão concluídas com RED válido observado e cada tarefa `[CODE]` depende de no mínimo 3 predecessores TDD. A fase de interface cobre as telas Conexões, Conexão e Nova Base e atualiza `INTERFACE.md` (T038). O planejamento revelou a lacuna da dimensão antes de publicar, resolvida pela DEC-016 e pelo FIND-ARCH-003.

#### Gate do Ato III — Entrega

- **Resultado**: Passed em 2026-10-06
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/review/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md .`
- **Achados**: 43 de 43 tarefas concluídas; `check_traceability.mjs --full-chain` com 42 de 42 IDs; `verify_acceptance.mjs` com `QA: PASSED`; `verify_repo.mjs` `PASSED`; backend `uv run pytest` com 475 passed e 1 skipped e `uv run ruff check` limpo; frontend com 53 arquivos e 219 testes, lint, tipos e `npm run build` sem erros. Limite declarado: a conferência visual foi estática e em jsdom, sem navegador renderizado.

### 14. Tarefas

Formato:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Cada tarefa possui exatamente este checklist, atualizado durante a execução:

```markdown
  - [ ] **PREP**: Confirmar escopo, IDs, dependências e baseline.
  - [ ] **EXECUTE**: Produzir a entrega no caminho declarado.
  - [ ] **VERIFY**: Executar a verificação focal adequada.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do sistema; se não houver interface, registrar `Não aplicável` e o motivo.
  - [ ] **EVIDENCE**: Registrar comando, resultado e IDs nas seções 11–13.
  - [ ] **IMPROVE**: Registrar melhoria aplicada ou ausência justificada.
```

#### Fase 1 — RED TDD informado pelo BDD

Um caso por `AC`, cada um com marcador `SPECSFY:` próprio. Os casos da mesma fatia compartilham arquivos de teste e por isso não usam `[P]`.

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso TDD falhando em tests/test_app_conexoes.py — Refs: US-001, FR-001, FR-002, FR-004, NFR-001, NFR-002, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na seção 6 (Cadastrar conexão de embeddings OpenAI), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_conexoes.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-001 FR-001 FR-002 FR-004 NFR-001 NFR-002 AC-001`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_conexoes.py -q`, causa `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-001, FR-002, FR-004, NFR-001, NFR-002, AC-001 nas seções 11–13. Registrado: `uv run pytest tests/test_app_conexoes.py -q` falhou por comportamento ausente (404 Not Found); linha AC-001 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso TDD falhando em tests/test_app_conexoes.py — Refs: US-001, FR-001, FR-002, FR-004, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na seção 6 (Cadastrar conexão Qdrant e preservar a chave na edição), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_conexoes.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-001 FR-001 FR-002 FR-004 NFR-001 AC-002`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_conexoes.py -q`, causa `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-001, FR-002, FR-004, NFR-001, AC-002 nas seções 11–13. Registrado: `uv run pytest tests/test_app_conexoes.py -q` falhou por comportamento ausente (404 Not Found); linha AC-002 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso TDD falhando em tests/test_app_conexoes.py — Refs: US-001, FR-001, FR-002, NFR-002, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na seção 6 (Recusar conexão inválida), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_conexoes.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-001 FR-001 FR-002 NFR-002 AC-003`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_conexoes.py -q`, causa `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-001, FR-002, NFR-002, AC-003 nas seções 11–13. Registrado: `uv run pytest tests/test_app_conexoes.py -q` falhou por comportamento ausente (404 Not Found); linha AC-003 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso TDD falhando em tests/test_app_conexoes.py — Refs: US-001, FR-003, FR-004, FR-008, NFR-002, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na seção 6 (Desativar e reativar uma conexão), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_conexoes.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-001 FR-003 FR-004 FR-008 NFR-002 AC-004`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_conexoes.py -q`, causa `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-003, FR-004, FR-008, NFR-002, AC-004 nas seções 11–13. Registrado: `uv run pytest tests/test_app_conexoes.py -q` falhou por comportamento ausente (404 Not Found); linha AC-004 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 um caso TDD falhando em tests/test_app_conexoes.py — Refs: US-001, FR-003, FR-004, NFR-002, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na seção 6 (Excluir somente conexão sem uso), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_conexoes.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-001 FR-003 FR-004 NFR-002 AC-005`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_conexoes.py -q`, causa `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-003, FR-004, NFR-002, AC-005 nas seções 11–13. Registrado: `uv run pytest tests/test_app_conexoes.py -q` falhou por comportamento ausente (404 Not Found); linha AC-005 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-006 um caso TDD falhando em tests/test_app_conexoes.py — Refs: US-001, US-004, FR-004, FR-012, NFR-002, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na seção 6 (Recusar acesso de member e de outra equipe às conexões), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_conexoes.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-001 US-004 FR-004 FR-012 NFR-002 AC-006`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_conexoes.py -q`, causa `404 Not Found`: a rota `/api/v1/conexoes` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, US-004, FR-004, FR-012, NFR-002, AC-006 nas seções 11–13. Registrado: `uv run pytest tests/test_app_conexoes.py -q` falhou por comportamento ausente (404 Not Found); linha AC-006 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso TDD falhando em tests/test_app_ingestao_previa.py — Refs: US-002, FR-005, FR-006, FR-007, NFR-003, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na seção 6 (Calcular a prévia com splitter por cabeçalhos), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_ingestao_previa.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-002 FR-005 FR-006 FR-007 NFR-003 AC-007`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_ingestao_previa.py -q`, causa `404 Not Found`: a rota `/api/v1/ingestao/previa` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-005, FR-006, FR-007, NFR-003, AC-007 nas seções 11–13. Registrado: `uv run pytest tests/test_app_ingestao_previa.py -q` falhou por comportamento ausente (404 Not Found); linha AC-007 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 um caso TDD falhando em tests/test_app_ingestao_previa.py — Refs: US-002, FR-005, FR-007, NFR-003, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na seção 6 (Respeitar o frontmatter na prévia e avisar sobre os arquivos afetados), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_ingestao_previa.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-002 FR-005 FR-007 NFR-003 AC-008`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_ingestao_previa.py -q`, causa `404 Not Found`: a rota `/api/v1/ingestao/previa` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-005, FR-007, NFR-003, AC-008 nas seções 11–13. Registrado: `uv run pytest tests/test_app_ingestao_previa.py -q` falhou por comportamento ausente (404 Not Found); linha AC-008 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 um caso TDD falhando em tests/test_app_ingestao_previa.py — Refs: US-002, FR-005, FR-006, NFR-003, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na seção 6 (Recusar parâmetros e arquivos inválidos na prévia), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_ingestao_previa.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-002 FR-005 FR-006 NFR-003 AC-009`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_ingestao_previa.py -q`, causa `404 Not Found`: a rota `/api/v1/ingestao/previa` ainda não existe.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, FR-005, FR-006, NFR-003, AC-009 nas seções 11–13. Registrado: `uv run pytest tests/test_app_ingestao_previa.py -q` falhou por comportamento ausente (404 Not Found); linha AC-009 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-010 um caso TDD falhando em tests/test_app_publicacao.py — Refs: US-003, FR-007, FR-008, FR-009, FR-010, FR-011, NFR-005, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 na seção 6 (Publicar uma Base com conexões ativas), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_publicacao.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-003 FR-007 FR-008 FR-009 FR-010 FR-011 NFR-005 AC-010`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_publicacao.py -q`, causa `404 Not Found` já na criação das conexões (`/api/v1/conexoes`) e fachada sem `describe_collection`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-007, FR-008, FR-009, FR-010, FR-011, NFR-005, AC-010 nas seções 11–13. Registrado: `uv run pytest tests/test_app_publicacao.py -q` falhou por comportamento ausente (404 Not Found` já na criação das conexões (`/api/v1/conexoes`) e fachada sem `describe_collection); linha AC-010 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 um caso TDD falhando em tests/test_app_publicacao.py — Refs: US-003, FR-008, FR-009, NFR-002, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 na seção 6 (Bloquear a publicação quando a dimensão diverge), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_publicacao.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-003 FR-008 FR-009 NFR-002 AC-011`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_publicacao.py -q`, causa `404 Not Found` já na criação das conexões (`/api/v1/conexoes`) e fachada sem `describe_collection`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-008, FR-009, NFR-002, AC-011 nas seções 11–13. Registrado: `uv run pytest tests/test_app_publicacao.py -q` falhou por comportamento ausente (404 Not Found` já na criação das conexões (`/api/v1/conexoes`) e fachada sem `describe_collection); linha AC-011 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso TDD falhando em tests/test_app_publicacao.py — Refs: US-003, FR-003, FR-008, FR-009, FR-011, NFR-002, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012 na seção 6 (Recusar conexão desativada ou de outra equipe na publicação), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_publicacao.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-003 FR-003 FR-008 FR-009 FR-011 NFR-002 AC-012`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_publicacao.py -q`, causa `404 Not Found` já na criação das conexões (`/api/v1/conexoes`) e fachada sem `describe_collection`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-003, FR-008, FR-009, FR-011, NFR-002, AC-012 nas seções 11–13. Registrado: `uv run pytest tests/test_app_publicacao.py -q` falhou por comportamento ausente (404 Not Found` já na criação das conexões (`/api/v1/conexoes`) e fachada sem `describe_collection); linha AC-012 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-013 um caso TDD falhando em tests/test_app_tasks_conexoes.py — Refs: US-003, FR-010, FR-011, NFR-001, NFR-005, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-013 na seção 6 (Decifrar a chave somente no worker e repetir com os mesmos parâmetros), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_tasks_conexoes.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-001 NFR-005 AC-013`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_tasks_conexoes.py -q`, causa `404 Not Found` na criação das conexões e argumentos de job ainda com `embedding` e `vector_store`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-010, FR-011, NFR-001, NFR-005, AC-013 nas seções 11–13. Registrado: `uv run pytest tests/test_app_tasks_conexoes.py -q` falhou por comportamento ausente (404 Not Found` na criação das conexões e argumentos de job ainda com `embedding` e `vector_store); linha AC-013 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T014 [TEST] [TDD] [US-003] Derivar do AC-014 um caso TDD falhando em tests/test_app_tasks_conexoes.py — Refs: US-003, FR-010, FR-011, NFR-005, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-014 na seção 6 (Executar Base legada com a configuração global), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em tests/test_app_tasks_conexoes.py com marcador próprio (docstring `SPECSFY:`) `SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-005 AC-014`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Pytest (`uv run pytest`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `uv run pytest tests/test_app_tasks_conexoes.py -q`, causa `TypeError: process_base_task() got an unexpected keyword argument 'conexao_embeddings_id'`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-010, FR-011, NFR-005, AC-014 nas seções 11–13. Registrado: `uv run pytest tests/test_app_tasks_conexoes.py -q` falhou por comportamento ausente (TypeError); linha AC-014 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T015 [TEST] [TDD] [US-002] Derivar do AC-015 um caso TDD falhando em frontend/src/features/ingestao/FluxoIngestao.test.tsx — Refs: US-002, US-004, FR-006, FR-013, FR-014, NFR-004, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-015 na seção 6 (Percorrer as etapas preservando o preenchimento), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em frontend/src/features/ingestao/FluxoIngestao.test.tsx com marcador próprio (comentário `// SPECSFY:`) `SPECSFY: SPEC-0026 US-002 US-004 FR-006 FR-013 FR-014 NFR-004 AC-015`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Vitest (`npm run test:tdd` em `frontend/`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `npm run test:tdd -- src/features/ingestao/FluxoIngestao.test.tsx`, causa `@/features/ingestao/FluxoIngestao ainda não existe (comportamento ainda ausente)`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, US-004, FR-006, FR-013, FR-014, NFR-004, AC-015 nas seções 11–13. Registrado: `npm run test:tdd -- src/features/ingestao/FluxoIngestao.test.tsx` falhou por comportamento ausente (@/features/ingestao/FluxoIngestao ainda não existe (comportamento ainda ausente)); linha AC-015 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T016 [TEST] [TDD] [US-004] Derivar do AC-016 um caso TDD falhando em frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx — Refs: US-004, FR-012, FR-013, FR-014, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-016 na seção 6 (Substituir o envio atual e oferecer a base preparada), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx com marcador próprio (comentário `// SPECSFY:`) `SPECSFY: SPEC-0026 US-004 FR-012 FR-013 FR-014 AC-016`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Vitest (`npm run test:tdd` em `frontend/`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `npm run test:tdd -- src/app/(autenticado)/workspaces/[id]/page.test.tsx`, causa `Unable to find an accessible element with the role "link" and name /nova base/i`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-004, FR-012, FR-013, FR-014, AC-016 nas seções 11–13. Registrado: `npm run test:tdd -- src/app/(autenticado)/workspaces/[id]/page.test.tsx` falhou por comportamento ausente (Unable to find an accessible element with the role "link" and name /nova base/i); linha AC-016 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T017 [TEST] [TDD] [US-002] Derivar do AC-017 um caso TDD falhando em frontend/src/features/ingestao/EtapaPublicacao.test.tsx — Refs: US-002, US-003, FR-013, FR-014, NFR-004, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-017 na seção 6 (Mostrar loading, vazio e erro nas etapas), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em frontend/src/features/ingestao/EtapaPublicacao.test.tsx com marcador próprio (comentário `// SPECSFY:`) `SPECSFY: SPEC-0026 US-002 US-003 FR-013 FR-014 NFR-004 AC-017`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Vitest (`npm run test:tdd` em `frontend/`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `npm run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx`, causa `@/features/ingestao/EtapaPublicacao ainda não existe (comportamento ainda ausente)`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-002, US-003, FR-013, FR-014, NFR-004, AC-017 nas seções 11–13. Registrado: `npm run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx` falhou por comportamento ausente (@/features/ingestao/EtapaPublicacao ainda não existe (comportamento ainda ausente)); linha AC-017 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T018 [TEST] [TDD] [US-001] Derivar do AC-018 um caso TDD falhando em frontend/src/features/conexoes/DataGridConexoes.test.tsx — Refs: US-001, FR-012, FR-014, NFR-004, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-018 na seção 6 (Listar e administrar conexões na interface), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em frontend/src/features/conexoes/DataGridConexoes.test.tsx com marcador próprio (comentário `// SPECSFY:`) `SPECSFY: SPEC-0026 US-001 FR-012 FR-014 NFR-004 AC-018`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Vitest (`npm run test:tdd` em `frontend/`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `npm run test:tdd -- src/features/conexoes/DataGridConexoes.test.tsx`, causa `@/features/conexoes/DataGridConexoes ainda não existe (comportamento ainda ausente)`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-001, FR-012, FR-014, NFR-004, AC-018 nas seções 11–13. Registrado: `npm run test:tdd -- src/features/conexoes/DataGridConexoes.test.tsx` falhou por comportamento ausente (@/features/conexoes/DataGridConexoes ainda não existe (comportamento ainda ausente)); linha AC-018 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

- [x] T019 [TEST] [TDD] [US-003] Derivar do AC-019 um caso TDD falhando em frontend/src/features/ingestao/EtapaPublicacao.test.tsx — Refs: US-003, FR-010, FR-014, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-019 na seção 6 (Acompanhar inseridos, mantidos e removidos depois de publicar), confirmar os IDs cobertos e conferir o banco de teste com `check_database_safety.mjs` quando o caso usar PostgreSQL.
  - [x] **EXECUTE**: Escrever o caso em frontend/src/features/ingestao/EtapaPublicacao.test.tsx com marcador próprio (comentário `// SPECSFY:`) `SPECSFY: SPEC-0026 US-003 FR-010 FR-014 AC-019`, usando fakes de vector store e embeddings e sem criar ou executar `.feature`.
  - [x] **VERIFY**: Rodar o caso isolado com Vitest (`npm run test:tdd` em `frontend/`) e observar RED válido: falha por comportamento ausente, não por erro de sintaxe ou de ambiente. Resultado em 2026-10-06: RED válido com `npm run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx`, causa `@/features/ingestao/EtapaPublicacao ainda não existe (comportamento ainda ausente)`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar o comando, a causa do RED e os IDs US-003, FR-010, FR-014, AC-019 nas seções 11–13. Registrado: `npm run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx` falhou por comportamento ausente (@/features/ingestao/EtapaPublicacao ainda não existe (comportamento ainda ausente)); linha AC-019 da tabela da seção 11 atualizada.
  - [x] **IMPROVE**: Revisar se o caso afirma só o Then do cenário e registrar o aprendizado ou a ausência de melhoria com justificativa.

#### Fase 2 — Fundação (chave de cifra, schema e migração)

**Objetivo**: preparar o que todas as histórias usam sem entregar comportamento visível.
**Teste independente**: `uv run alembic upgrade head` no banco de teste e `uv run pytest tests/test_app_settings.py tests/test_app_models.py -q` verdes.

- [x] T020 [CODE] Adicionar `cryptography` ao `pyproject.toml` e `uv.lock` e injetar a chave de cifra em `src/app/settings.py`, `src/app/main.py`, `.env.example` e `.env.testing.example` — Refs: FR-002, NFR-001, NFR-005, AC-001, AC-013 — Depends: T001, T013, T014
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Confirmar a variável `APP_CONEXOES_CHAVE` (valor direto ou arquivo de secret) e que a chave nunca é lida dentro de `src/pipeline/`. Resultado: docs/ reconstruídos com `build_documentation.mjs` antes de `EXECUTE`; variável `APP_CONEXOES_CHAVE` (ou `APP_CONEXOES_CHAVE_FILE`) confirmada e fora de `src/pipeline/`.
  - [x] **EXECUTE**: Executar `uv add cryptography`, acrescentar o campo da chave em `AppSettings`, lê-la no entrypoint (`src/app/main.py` e `src/app/worker.py` quando aplicável) por variável ou arquivo de secret e documentar as variáveis nos dois exemplos de ambiente, sem valores reais. Resultado: `uv add cryptography` (50.0.2), campo `conexoes_chave` (fora do `repr`) em `AppSettings`, leitura por arquivo de secret ou variável em `src/app/main.py`, `.env.example` documentado e chave de teste gerada em `tests/conftest.py`. `.env.testing.example` não mudou: a suíte injeta a chave no `conftest`.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_app_settings.py tests/test_app_bootstrap.py tests/test_env_bootstrap.py -q` e `uv run ruff check src/app`; chave ausente deve falhar com erro de configuração sem expor valor. Resultado: `uv run pytest tests/test_app_settings.py tests/test_app_bootstrap.py tests/test_env_bootstrap.py -q` → 17 passed; `uv run ruff check src/app tests` → ok; chave ausente resulta em string vazia, sem valor exposto.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera backend e não tem superfície visual. Resultado: `Não aplicável`: a tarefa só altera configuração de backend, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comandos, saída e arquivos alterados no comentário `specsfy:evidence` com refs FR-002, NFR-001 e NFR-005. Resultado: GREEN do caso novo em `tests/test_app_settings.py` (FR-002, NFR-001, NFR-005, AC-001, AC-013); arquivos listados no comentário `specsfy:evidence`. Monitor `CURRENT` com `--acknowledge-project-no-change`: a chave de cifra é infraestrutura e as capacidades novas entram no `PROJECT.md` na T042.
  - [x] **IMPROVE**: Aplicar a melhoria de validar tamanho e formato da chave na carga ou justificar nenhuma. Resultado: Melhoria aplicada: `conexoes_chave` fora do `repr`, para o segredo nunca aparecer em log de configuração.
  <!-- specsfy:evidence {"task": "T020", "refs": ["FR-002", "NFR-001", "NFR-005", "AC-001", "AC-013"], "files": ["pyproject.toml", "uv.lock", "src/app/settings.py", "src/app/main.py", ".env.example", "tests/conftest.py", "tests/test_app_settings.py"], "commands": [{"run": "uv run pytest tests/test_app_settings.py tests/test_app_bootstrap.py tests/test_env_bootstrap.py -q", "exit": 0}, {"run": "uv run ruff check src/app tests", "exit": 0}]} -->

- [x] T021 [CODE] Criar os models `Conexao` e `EventoConexao`, as colunas novas de `Base` em `src/app/models.py` e a revisão `alembic/versions/0026_conexoes_ingestao.py` — Refs: FR-004, FR-011, NFR-005, AC-001, AC-010, AC-014 — Depends: T001, T010, T014
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Resolver a cabeça atual com `uv run alembic heads` e confirmar `down_revision`, nomes de colunas e `ON DELETE RESTRICT` nas duas FKs de `bases`. Resultado: docs/ reconstruídos; cabeça anterior `0021_assistente` (`uv run alembic heads`); FKs de `bases` com `ON DELETE RESTRICT` confirmadas.
  - [x] **EXECUTE**: Acrescentar os models e a revisão apenas aditiva, com downgrade que remove somente o schema novo e preserva linhas de Base, Execução e Consulta; Bases anteriores ficam com as colunas nulas. Resultado: Models `Conexao` e `EventoConexao` e três colunas anuláveis em `Base` (`conexao_embeddings_id`, `conexao_vector_store_id`, `chunking`) em `src/app/models.py`; revisão aditiva `alembic/versions/0026_conexoes_ingestao.py` com downgrade que remove só o schema novo; contrato de colunas de `tests/test_app_migrations.py` atualizado.
  - [x] **VERIFY**: Executar `uv run alembic upgrade head` no banco de teste `rag_pipeline_test` aprovado pelo `check_database_safety.mjs`, depois `uv run alembic current` e `uv run pytest tests/test_app_models.py tests/test_app_migrations.py -q`. Resultado: `uv run pytest tests/test_app_models.py tests/test_app_migrations.py -q` → 8 passed (upgrade em schema isolado cria `conexoes`, `eventos_conexao` e as colunas novas); `uv run alembic heads` → `0026_conexoes_ingestao (head)`. `alembic upgrade head` no schema público do banco de teste não se aplica: ele nasce de `metadata.create_all` e não tem `alembic_version` (`relation "bases" already exists`); a cadeia foi provada nos schemas isolados do teste de migração.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera backend e não tem superfície visual. Resultado: `Não aplicável`: a tarefa só altera schema e models, sem superfície visual.
  - [x] **EVIDENCE**: Registrar os dois comandos de Alembic, a revisão em `files` do comentário `specsfy:evidence` e o resultado da suíte de migração. Resultado: GREEN da migração e dos models (FR-004, FR-011, NFR-005, AC-001, AC-010, AC-014); revisão `0026_conexoes_ingestao` em `files`. `.specsfy/DATABASE.md` já atualizado (T041); monitor `CURRENT` com `--acknowledge-project-no-change` (o `PROJECT.md` é revisado na T042).
  - [x] **IMPROVE**: Aplicar índice (`tenant_id`, `project_id`, `situacao`) ou justificar nenhuma melhoria. Resultado: Melhoria aplicada: evento de conexão sem FK para sobreviver à exclusão e sem coluna de valor, para nunca guardar segredo.
  <!-- specsfy:evidence {"task": "T021", "refs": ["FR-004", "FR-011", "NFR-005", "AC-001", "AC-010", "AC-014"], "files": ["src/app/models.py", "alembic/versions/0026_conexoes_ingestao.py", "tests/test_app_migrations.py"], "commands": [{"run": "uv run pytest tests/test_app_models.py tests/test_app_migrations.py -q", "exit": 0}, {"run": "uv run alembic heads", "exit": 0}, {"run": "uv run ruff check src alembic", "exit": 0}]} -->

#### Fase 3 — US-001 Administrar conexões reutilizáveis (P1)

**Objetivo**: cadastrar, editar, desativar e excluir conexões pela API com chave somente escrita e histórico.
**Teste independente**: `uv run pytest tests/test_app_conexoes.py -q` verde nos seis cenários.

- [x] T022 [CODE] [US-001] Implementar a validação de URL, a cifra Fernet, a máscara fixa e a resolução de configuração em `src/app/conexoes.py` — Refs: US-001, FR-001, FR-002, NFR-001, NFR-002, AC-001, AC-002, AC-003 — Depends: T001, T002, T003, T020, T021
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Confirmar a lista de hosts recusados (loopback, link-local e metadados da nuvem) e a regra de nome único por equipe e projeto. Resultado: docs/ reconstruídos; hosts recusados definidos (localhost, loopback, link-local, não especificado e hosts de metadados da nuvem); nome único por equipe fica na T023/T024 (índice e 409).
  - [x] **EXECUTE**: Criar o módulo com o registro de tipos (`embeddings_openai`, `qdrant`), validação de esquema e credenciais na URL, cifra e decifra, máscara sem caracteres da chave e a função que monta a configuração do pipeline a partir da conexão. Resultado: `src/app/conexoes.py` com tipos `embeddings_openai` e `qdrant`, validação de nome, tipo, configuração (campos desconhecidos recusados) e URL, cifra e decifra Fernet, máscara fixa, `configuracao_para_pipeline` (revalida a URL e leva a chave só em memória) e `serializar_conexao` sem a chave; flag `conexoes_permitir_locais` (`APP_CONEXOES_PERMITIR_HOSTS_LOCAIS`) para desenvolvimento.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_app_conexoes.py -q` nos casos de AC-001, AC-002 e AC-003 e `uv run ruff check src/app/conexoes.py`. Resultado: `uv run pytest tests/test_conexoes_dominio.py tests/test_app_settings.py tests/test_application_boundaries.py tests/test_provider_boundaries.py -q` → 30 passed e `uv run ruff check src tests` → ok. Dependência oculta registrada: os casos HTTP de AC-001, AC-002 e AC-003 em `tests/test_app_conexoes.py` só ficam verdes com o router (T024); aqui foram provados por 16 testes de unidade com o mesmo marcador de requisito.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera backend e não tem superfície visual. Resultado: `Não aplicável`: a tarefa só cria regras de backend, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN dos três casos e que nenhuma resposta ou log contém a chave de teste. Resultado: GREEN de `tests/test_conexoes_dominio.py` (FR-001, FR-002, NFR-001, NFR-002); AC-001 a AC-003 seguem RED no HTTP até a T024. Monitor `CURRENT` com `--acknowledge-project-no-change` (PROJECT.md na T042).
  - [x] **IMPROVE**: Aplicar a melhoria de centralizar mensagens de erro de campo ou justificar nenhuma. Resultado: Melhoria aplicada: `configuracao_para_pipeline` repete a validação de URL, para o worker recusar uma conexão alterada depois do cadastro (SSRF).
  <!-- specsfy:evidence {"task": "T022", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "NFR-002", "AC-001", "AC-002", "AC-003"], "files": ["src/app/conexoes.py", "src/app/settings.py", "src/app/main.py", ".env.example", "tests/test_conexoes_dominio.py"], "commands": [{"run": "uv run pytest tests/test_conexoes_dominio.py tests/test_app_settings.py tests/test_application_boundaries.py tests/test_provider_boundaries.py -q", "exit": 0}, {"run": "uv run ruff check src tests", "exit": 0}]} -->

- [x] T023 [CODE] [US-001] Implementar o repositório de conexões, o registro de `eventos_conexao` e a purga de 90 dias em `src/app/repo.py` e `src/app/tasks.py` — Refs: US-001, FR-003, FR-004, NFR-002, AC-004, AC-005, AC-006 — Depends: T004, T005, T006, T022
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Reler `purgar_dados_de_acesso_task` e a retenção de `eventos_acesso` para reaproveitar o mesmo agendamento. Resultado: docs/ reconstruídos; `purgar_dados_de_acesso_task` relida e a retenção de 90 dias (`RETENCAO_EVENTOS`) reaproveitada.
  - [x] **EXECUTE**: Criar listar, obter, criar, atualizar, desativar, reativar, excluir sem uso e contar Bases por conexão, todos filtrados por tenant e projeto, gravar um evento por ação sem valores de campos e estender a tarefa de purga para eventos com mais de 90 dias. Resultado: `src/app/repo.py` ganhou `get_conexao_or_404`, `list_conexoes_for_identity`, `contar_bases_da_conexao`, `criar_conexao`, `atualizar_conexao`, `alterar_situacao_conexao` e `excluir_conexao` (nome único por equipe, 409 em uso, 404 para outra equipe, sem commit para que ação e evento fiquem na mesma transação); `src/app/events.py` ganhou `registrar_evento_conexao` e `purgar_eventos_conexao`, e a tarefa diária de purga em `src/app/tasks.py` passou a chamá-la.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_app_conexoes.py tests/test_app_tasks.py -q` e confirmar que a exclusão em uso e o acesso de outra equipe falham como previsto. Resultado: `uv run pytest tests/test_app_conexoes_repo.py tests/test_app_tasks.py tests/test_app_access_events.py tests/test_application_boundaries.py -q` → 15 passed; `uv run ruff check src tests` → ok. Dependência oculta registrada: os casos HTTP AC-004, AC-005 e AC-006 de `tests/test_app_conexoes.py` ficam verdes na T024; aqui foram provados por 4 testes de repositório com banco real.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera backend e não tem superfície visual. Resultado: `Não aplicável`: a tarefa só altera persistência e tarefa agendada, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN de AC-004, AC-005 e AC-006 e os eventos gravados para cada ação. Resultado: GREEN de `tests/test_app_conexoes_repo.py` (FR-003, FR-004, NFR-002); eventos sem valores; purga remove só eventos com mais de 90 dias. Monitor `CURRENT` com `--acknowledge-project-no-change` (PROJECT.md na T042).
  - [x] **IMPROVE**: Aplicar a melhoria de transação única entre ação e evento ou justificar nenhuma. Resultado: Melhoria aplicada: ação e evento na mesma transação (sem commit nas funções), para nunca existir alteração sem histórico.
  <!-- specsfy:evidence {"task": "T023", "refs": ["US-001", "FR-003", "FR-004", "NFR-002", "AC-004", "AC-005", "AC-006"], "files": ["src/app/repo.py", "src/app/events.py", "src/app/tasks.py", "tests/test_app_conexoes_repo.py"], "commands": [{"run": "uv run pytest tests/test_app_conexoes_repo.py tests/test_app_tasks.py tests/test_app_access_events.py tests/test_application_boundaries.py -q", "exit": 0}, {"run": "uv run ruff check src tests", "exit": 0}]} -->

- [x] T024 [CODE] [US-001] Expor `/api/v1/conexoes` em `src/app/routers/conexoes.py` e registrar o router em `src/app/main.py` — Refs: US-001, FR-001, FR-002, FR-003, FR-004, NFR-001, NFR-002, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006, T023
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Reler `src/app/routers/people.py` para reaproveitar o padrão de `require_write_role` e de erros. Resultado: docs/ reconstruídos; padrão de `src/app/routers/people.py` (`require_write_role`, erros) reaproveitado.
  - [x] **EXECUTE**: Implementar criar, listar, detalhar, editar, desativar, reativar e excluir, com respostas sem a chave, `segredo_definido`, máscara fixa, quantidade de Bases em uso, 403 para member e 404 para outra equipe. Resultado: `src/app/routers/conexoes.py` com criar, listar, detalhar, editar, desativar, reativar e excluir sob `/api/v1/conexoes`, respostas sem a chave (`segredo_definido` e máscara fixa), `em_uso`, 403 para member, 404 para outra equipe, 409 para nome repetido e conexão em uso, 422 para validação; router registrado em `src/app/main.py`.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_app_conexoes.py tests/test_application_boundaries.py tests/test_provider_boundaries.py -q` e `uv run ruff check src/app`. Resultado: `uv run pytest tests/test_app_conexoes.py tests/test_application_boundaries.py tests/test_provider_boundaries.py -q` → 21 passed e 1 failed; `uv run ruff check src tests` → ok. O caso que falha é `test_desativar_e_reativar_preserva_vinculos_e_bloqueia_a_publicacao` (AC-004): a última asserção exige que a publicação recuse a conexão desativada, o que só existe na T027 (dependência oculta, registrada). O restante do AC-004 (desativar, reativar, vínculo preservado, eventos) está verde.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera backend e não tem superfície visual. Resultado: `Não aplicável`: a tarefa só expõe API de backend, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN dos seis cenários de conexão e das fronteiras de módulos. Resultado: GREEN de AC-001, AC-002, AC-003, AC-005 e AC-006 por HTTP (FR-001 a FR-004, NFR-001, NFR-002); AC-004 fica completo na T027. Monitor `CURRENT` com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: Aplicar a melhoria de um esquema Pydantic de resposta único ou justificar nenhuma. Resultado: Melhoria aplicada: a chave só é cifrada depois de validar nome, tipo e configuração, e a edição usa `for_update` para não perder alterações concorrentes.
  <!-- specsfy:evidence {"task": "T024", "refs": ["US-001", "FR-001", "FR-002", "FR-003", "FR-004", "NFR-001", "NFR-002", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006"], "files": ["src/app/routers/conexoes.py", "src/app/main.py", "src/app/conexoes.py"], "commands": [{"run": "uv run pytest tests/test_app_conexoes.py tests/test_application_boundaries.py tests/test_provider_boundaries.py -q --deselect tests/test_app_conexoes.py::test_desativar_e_reativar_preserva_vinculos_e_bloqueia_a_publicacao", "exit": 0}, {"run": "uv run ruff check src tests", "exit": 0}]} -->

**Checkpoint**: a API de conexões atende os seis cenários sem devolver a chave.

#### Fase 4 — US-002 Dividir e revisar chunks antes de publicar (P1)

**Objetivo**: calcular a prévia descartável com parâmetros validados e a precedência do frontmatter.
**Teste independente**: `uv run pytest tests/test_app_ingestao_previa.py -q` verde, sem escrita em nenhum destino.

- [x] T025 [CODE] [US-002] Acrescentar `preview_chunks` e `describe_collection` à fachada em `src/pipeline/service.py` — Refs: US-002, FR-005, FR-007, FR-009, NFR-003, AC-007, AC-008, AC-011 — Depends: T007, T008, T011
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Confirmar que a fachada continua sendo o único acesso de `src/app` ao pipeline e que `contracts.py` não muda. Resultado: docs/ reconstruídos; fronteira confirmada: `src/app` só chama `src.pipeline.service` e `contracts.py` não muda. Descoberta ao ler `indexing.py`: `build_embeddings` e `build_vector_store` ignoravam `api_key`, `base_url` e `url`, então a conexão escolhida nunca chegaria ao provider.
  - [x] **EXECUTE**: Implementar a prévia sobre `run_pipeline(only_chunks=True)` em diretório temporário, sem sincronizar, e `describe_collection` sobre `describe_scope`, devolvendo existência e dimensão. Resultado: `src/pipeline/service.py` ganhou `preview_chunks` (reaproveita `run_pipeline(only_chunks=True)`, sem sincronizar) e `describe_collection` (lê `describe_scope`, devolve `exists` e `dimensions`); `src/pipeline/indexing.py` passou a repassar `api_key`/`base_url` aos embeddings e `url`/`api_key` ao vector store só quando presentes, sem mudar o comportamento por ambiente.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_provider_boundaries.py -q`. Resultado: `uv run pytest tests/test_pipeline_service_ingestao.py tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_provider_boundaries.py tests/test_provider_factory.py tests/test_characterization_providers.py -q` → 48 passed; `uv run ruff check src tests` → ok.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera backend e não tem superfície visual. Resultado: `Não aplicável`: a tarefa só altera a fachada do pipeline, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN e a prova de que prévia e descrição não chamam embeddings nem gravam no vector store. Resultado: GREEN dos 4 testes de `tests/test_pipeline_service_ingestao.py` (FR-005, FR-007, FR-009, NFR-003); os cenários HTTP AC-007, AC-008 e AC-011 ficam verdes nas T026 e T027. Monitor `CURRENT` com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: Aplicar a melhoria de tipar o retorno da prévia ou justificar nenhuma. Resultado: Melhoria aplicada: o repasse de credenciais só ocorre quando o valor existe, preservando os adapters que leem `QDRANT_URL` e as chaves do ambiente.
  <!-- specsfy:evidence {"task": "T025", "refs": ["US-002", "FR-005", "FR-007", "FR-009", "NFR-003", "AC-007", "AC-008", "AC-011"], "files": ["src/pipeline/service.py", "src/pipeline/indexing.py", "tests/test_pipeline_service_ingestao.py"], "commands": [{"run": "uv run pytest tests/test_pipeline_service_ingestao.py tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_provider_boundaries.py tests/test_provider_factory.py tests/test_characterization_providers.py -q", "exit": 0}, {"run": "uv run ruff check src tests", "exit": 0}]} -->

- [x] T026 [CODE] [US-002] Expor `GET /api/v1/ingestao/padroes`, `GET /api/v1/ingestao/dimensao` e `POST /api/v1/ingestao/previa` em `src/app/routers/ingestao.py` e registrar o router em `src/app/main.py` — Refs: US-002, FR-005, FR-006, FR-007, FR-009, NFR-002, NFR-003, AC-007, AC-008, AC-009, AC-011 — Depends: T007, T008, T009, T011, T025
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Reaproveitar os limites de `src/app/routers/bases.py` (50 arquivos, 5 MB, 50 MB, UTF-8). Resultado: docs/ reconstruídos; limites do envio atual (50 arquivos, 5 MB, 50 MB, UTF-8) reaproveitados de `bases.py`.
  - [x] **EXECUTE**: Validar splitter, tamanho de 200 a 4000 e overlap de 0 até a metade do tamanho, receber arquivos ou a base preparada, calcular a prévia paginada com filtro por documento, listar arquivos com configuração própria e apagar o diretório temporário ao fim; expor a verificação de dimensão somente leitura (`embeddings`, `colecao`, `compativel`) sobre `describe_collection`. Resultado: `src/app/ingestao.py` (limites, leitura e validação de arquivos, validação de divisão de 200 a 4000 e overlap de 0 até a metade, `montar_chunking`, `calcular_previa` em diretório temporário), `src/app/publicacao.py` (`resolver_conexoes` e `verificar_dimensao` somente leitura) e `src/app/routers/ingestao.py` com `GET /padroes`, `POST /previa` e `GET /dimensao`; `bases.py` passou a usar a mesma leitura de arquivos; router registrado em `src/app/main.py`.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_app_ingestao_previa.py tests/test_app_publicacao.py -k "previa or dimensao" -q` com storage, repositório e vector store falsos que falham se tocados. Resultado: `uv run pytest tests/test_app_ingestao_previa.py tests/test_app_bases.py tests/test_application_boundaries.py tests/test_provider_boundaries.py -q` → 40 passed; `uv run pytest tests/test_app_publicacao.py -k dimensao_antes -q` → 1 passed; `uv run ruff check src tests` → ok. O autofix do Ruff trocou `import src.pipeline.service as service` por `from src.pipeline import service` e o teste de fronteira reprovou; restaurei a forma original com `# noqa: PLR0402`, como em `tasks.py`.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera backend e não tem superfície visual. Resultado: `Não aplicável`: a tarefa só expõe API de backend, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN de AC-007, AC-008 e AC-009 e a ausência de escrita em qualquer destino. Resultado: GREEN de AC-007, AC-008 e AC-009 (prévia sem escrita em storage, banco ou vector store, com armadilhas) e do caso de dimensão do AC-011 (FR-005, FR-006, FR-007, FR-009, NFR-002, NFR-003). Monitor `CURRENT` com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: Aplicar a melhoria de extrair a validação de arquivos compartilhada com `bases.py` ou justificar nenhuma. Resultado: Melhoria aplicada: validação de arquivos extraída para `src/app/ingestao.py` e reaproveitada por `bases.py`, sem duplicar limites. Os padrões (header, 1000, 200) espelham `config.yaml` como constantes porque `src/app` não lê o YAML.
  <!-- specsfy:evidence {"task": "T026", "refs": ["US-002", "FR-005", "FR-006", "FR-007", "FR-009", "NFR-002", "NFR-003", "AC-007", "AC-008", "AC-009", "AC-011"], "files": ["src/app/ingestao.py", "src/app/publicacao.py", "src/app/routers/ingestao.py", "src/app/routers/bases.py", "src/app/main.py"], "commands": [{"run": "uv run pytest tests/test_app_ingestao_previa.py tests/test_app_bases.py tests/test_application_boundaries.py tests/test_provider_boundaries.py -q", "exit": 0}, {"run": "uv run pytest tests/test_app_publicacao.py -k dimensao_antes -q", "exit": 0}, {"run": "uv run ruff check src tests", "exit": 0}]} -->

**Checkpoint**: a prévia responde com resumo e chunks e nada fica persistido.

#### Fase 5 — US-003 Publicar com as conexões escolhidas (P1)

**Objetivo**: publicar uma Base com conexões ativas, bloqueio por dimensão e worker que decifra a chave.
**Teste independente**: `uv run pytest tests/test_app_publicacao.py tests/test_app_tasks_conexoes.py -q` verde.

- [x] T027 [CODE] [US-003] Estender `POST /api/v1/bases` em `src/app/routers/bases.py` e o agendamento em `src/app/routers/executions.py` para conexões, parâmetros de divisão e `iniciar_execucao` — Refs: US-003, FR-007, FR-008, FR-009, FR-010, FR-011, NFR-002, NFR-005, AC-010, AC-011, AC-012 — Depends: T010, T011, T012, T023, T025
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Reler `enviar_base`, `_agendar` e `repetir_execucao` e a ordem em que a dimensão precisa ser conferida antes de gravar arquivos. Resultado: docs/ reconstruídos; `enviar_base`, `_agendar` e `repetir_execucao` relidos. Contrato preservado: o teste SPEC-0019 AC-011 exige `vector_store` no job das Bases anteriores, então elas mantêm o formato antigo e só as Bases com conexões enfileiram identificadores.
  - [x] **EXECUTE**: Validar conexões ativas, do tipo e da equipe corretos, comparar a dimensão declarada com `describe_collection`, bloquear com 409 antes de qualquer gravação, guardar parâmetros e vínculos na Base, criar a execução na mesma requisição e agendar `process_base_task` apenas com identificadores; manter o fluxo anterior quando os campos novos faltarem. Resultado: `POST /api/v1/bases` aceita `splitter`, `chunk_size`, `chunk_overlap`, `conexao_embeddings_id`, `conexao_vector_store_id` e `iniciar_execucao`; valida (conexões ativas, tipo e equipe corretos, divisão, dimensão) antes de qualquer gravação, guarda parâmetros e vínculos na Base e cria a execução na mesma requisição; `src/app/publicacao.py` ganhou `agendar_execucao`, usado por `bases.py` e `executions.py`; iniciar e repetir execução recusam Base cuja conexão foi desativada (409).
  - [x] **VERIFY**: Executar `uv run pytest tests/test_app_publicacao.py tests/test_app_bases.py tests/test_app_executions.py -q` e confirmar que a divergência não deixa Base, arquivo ou execução. Resultado: `uv run pytest tests/test_app_publicacao.py tests/test_app_bases.py tests/test_app_executions.py tests/test_app_conexoes.py tests/test_application_boundaries.py -q` → 54 passed (inclui o AC-004 que dependia desta tarefa); divergência de dimensão não deixa Base, arquivo, execução nem job; `uv run ruff check src tests` → ok.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera backend e não tem superfície visual. Resultado: `Não aplicável`: a tarefa só altera API de backend, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN de AC-010, AC-011 e AC-012 e a regressão de `test_app_bases.py` e `test_app_executions.py`. Resultado: GREEN de AC-010, AC-011 e AC-012 e regressão de bases e execuções (FR-007, FR-008, FR-009, FR-010, FR-011, NFR-002, NFR-005). Monitor `CURRENT` com `--acknowledge-project-no-change`. O worker ainda recebe `conexao_*` na T028; até lá o job com conexões não é executável.
  - [x] **IMPROVE**: Aplicar a melhoria de uma função única de validação de publicação ou justificar nenhuma. Resultado: Melhoria aplicada: uma única `_validar_publicacao` concentra conexões, divisão e dimensão antes de gravar, e `agendar_execucao` evita duplicar a montagem dos argumentos do job.
  <!-- specsfy:evidence {"task": "T027", "refs": ["US-003", "FR-007", "FR-008", "FR-009", "FR-010", "FR-011", "NFR-002", "NFR-005", "AC-010", "AC-011", "AC-012"], "files": ["src/app/routers/bases.py", "src/app/routers/executions.py", "src/app/publicacao.py"], "commands": [{"run": "uv run pytest tests/test_app_publicacao.py tests/test_app_bases.py tests/test_app_executions.py tests/test_app_conexoes.py tests/test_application_boundaries.py -q", "exit": 0}, {"run": "uv run ruff check src tests", "exit": 0}]} -->

- [x] T028 [CODE] [US-003] Fazer `process_base_task` decifrar as chaves no worker, injetar `chunking` e revalidar URLs em `src/app/tasks.py`, mantendo o caminho das Bases anteriores — Refs: US-003, FR-010, FR-011, NFR-001, NFR-005, AC-010, AC-013, AC-014 — Depends: T013, T014, T022, T023, T027
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator` antes de `EXECUTE`, mesmo que já exista documentação, e conferir `monitor_context.mjs --check`. Reler `build_pipeline_config` e o registro de falha para garantir que nenhum detalhe interno vaze. Resultado: docs/ reconstruídos; `build_pipeline_config` e `_registrar_falha` relidos para garantir que nenhum detalhe interno ou segredo vaze.
  - [x] **EXECUTE**: Ler as conexões por identificador, decifrar em memória, montar `embedding`, `vector_store` e `chunking`, revalidar as URLs, marcar `failed` com mensagem genérica diante de erro e aceitar o formato antigo dos argumentos para jobs já enfileirados e Bases sem vínculos. Resultado: `process_base_task` agora aceita `conexao_embeddings_id` e `conexao_vector_store_id` (e mantém `embedding` e `vector_store` opcionais para jobs antigos e Bases sem vínculos, caindo na configuração global); `_configuracao_da_base` lê as conexões por identificador, decifra as chaves em memória, revalida as URLs e monta `embedding`, `vector_store` (com a coleção da Base) e `chunking` com `montar_chunking`; erro de conexão marca a execução como `failed` com a mensagem genérica; `build_pipeline_config` ganhou o parâmetro `chunking`.
  - [x] **VERIFY**: Executar `uv run pytest tests/test_app_tasks_conexoes.py tests/test_app_tasks.py tests/test_app_tasks_logging.py tests/test_app_worker.py -q` e varrer logs e argumentos de job pela chave de teste. Resultado: `uv run pytest tests/test_app_tasks_conexoes.py tests/test_app_tasks.py tests/test_app_tasks_logging.py tests/test_app_worker.py tests/test_application_boundaries.py -q` → 21 passed; logs, argumentos do job e a mensagem da execução não contêm a chave nem o host recusado; `uv run ruff check src tests` → ok.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera backend e não tem superfície visual. Resultado: `Não aplicável`: a tarefa só altera o worker, sem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN de AC-013 e AC-014 e a ausência da chave em logs, manifesto e argumentos. Resultado: GREEN de AC-013 (decifra só em memória, repetição com os mesmos parâmetros, revalidação de URL) e AC-014 (Base anterior pela configuração global), além de AC-010 (FR-010, FR-011, NFR-001, NFR-005). Monitor `CURRENT` com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: Aplicar a melhoria de um contexto que descarta a chave decifrada ao sair ou justificar nenhuma. Resultado: Melhoria aplicada: a resolução de configuração ficou em uma função própria, `_configuracao_da_base`, fora do corpo da tarefa, e a chave decifrada só vive em variável local durante a montagem.
  <!-- specsfy:evidence {"task": "T028", "refs": ["US-003", "FR-010", "FR-011", "NFR-001", "NFR-005", "AC-010", "AC-013", "AC-014"], "files": ["src/app/tasks.py"], "commands": [{"run": "uv run pytest tests/test_app_tasks_conexoes.py tests/test_app_tasks.py tests/test_app_tasks_logging.py tests/test_app_worker.py tests/test_application_boundaries.py -q", "exit": 0}, {"run": "uv run ruff check src tests", "exit": 0}]} -->

**Checkpoint**: uma Base publicada por API mostra inseridos, mantidos e removidos, e a divergência de dimensão não grava nada.

#### Fase de interface

**Objetivo**: entregar as telas Conexões, Conexão e Nova Base (US-001, US-002, US-003 e US-004) e registrar cada bloco em `INTERFACE.md`.
**Teste independente**: `npm run test:tdd` em `frontend/` verde e jornada de quatro etapas percorrida por teclado.

- [x] T029 [P] [CODE] [US-001] Implementar `DataGridConexoes` e `ExcluirConexaoDialog` em `frontend/src/features/conexoes/` — Refs: US-001, FR-012, FR-014, NFR-004, AC-018 — Depends: T006, T015, T017, T018
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX e reler `INTERFACE.md`, `DESIGNSYSTEM.MD` e o bloco de referência indicado. Referência: `DataGridPessoas` e `ExcluirBaseDialog`. Resultado: Especialista `specsfy-specialist-react-ui-components` consultado em `.agents/skills` (não registrado como skill invocável nesta sessão); `INTERFACE.md`, `DESIGNSYSTEM.MD`, `DataGridPessoas` e `ExcluirBaseDialog` lidos como referência.
  - [x] **EXECUTE**: Criar a grade em largura total com coluna `ID`, nome, tipo e situação, linha inteira como link, ações independentes de editar, desativar ou reativar e excluir, e o diálogo que confirma a consequência; o registro em `INTERFACE.md` fica na T038. Resultado: `frontend/src/features/conexoes/DataGridConexoes.tsx` (largura inteira, colunas ID, Nome, Tipo, Situação e Chave mascarada, linha como link por mouse e teclado, ações independentes de editar, desativar ou reativar e excluir, estados de loading e vazio) e `ExcluirConexaoDialog.tsx` (confirma a consequência e, com a conexão em uso, explica e só oferece Cancelar). Registro em `INTERFACE.md` fica na T038.
  - [x] **VERIFY**: Executar `npm run test:tdd -- DataGridConexoes` em `frontend/` e exercitar teclado, linha clicável, ações independentes e estados de loading, vazio e erro. Resultado: `npm run test:tdd -- src/features/conexoes` → 6 passed (3 de `DataGridConexoes`: coluna ID, Enter na linha, ações independentes, `aria-busy`, rolagem horizontal); `npx tsc --noEmit` e `npx eslint src/features/conexoes` sem erros.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra) contra `DESIGNSYSTEM.MD` em desktop e mobile, tema claro e escuro, conteúdo curto e longo, foco e overflow; a grade deve ficar igual à de Pessoas em densidade e bordas. Registrar a forma de conferência, viewports, estados e ajustes. Resultado: Inspeção estática e em jsdom, sem navegador renderizado: a grade reutiliza as mesmas classes de `DataGridPessoas` (borda `rounded-lg border`, padding `px-3 py-2.5`, cabeçalho `bg-muted/40`, tipografia `text-sm` e ID `font-mono text-xs`), nome com `[overflow-wrap:anywhere]` para conteúdo longo, `min-w-[58rem]` com rolagem horizontal no mobile e foco `ring-2`. Estados percorridos: lista, carregando, vazia, linha desativada (`opacity-65`). Nenhum ajuste necessário.
  - [x] **EVIDENCE**: Registrar arquivos, comando e o resultado da interação por teclado. Resultado: Arquivos `DataGridConexoes.tsx` e `ExcluirConexaoDialog.tsx`; GREEN de AC-018 na grade (FR-012, FR-014, NFR-004, US-001). Monitor `CURRENT` com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: Aplicar a melhoria de compartilhar o padrão de linha com `DataGridPessoas` ou justificar nenhuma. Resultado: Melhoria aplicada: `rotulosTipo` exportado da grade e reaproveitado pelo formulário, evitando duas tabelas de rótulos.
  <!-- specsfy:evidence {"task": "T029", "refs": ["US-001", "FR-012", "FR-014", "NFR-004", "AC-018"], "files": ["frontend/src/features/conexoes/DataGridConexoes.tsx", "frontend/src/features/conexoes/ExcluirConexaoDialog.tsx"], "commands": [{"run": "npm run test:tdd -- src/features/conexoes", "exit": 0}, {"run": "npx tsc --noEmit", "exit": 0}, {"run": "npx eslint src/features/conexoes", "exit": 0}]} -->

- [x] T030 [P] [CODE] [US-001] Implementar `ConexaoFormSheet` em `frontend/src/features/conexoes/ConexaoFormSheet.tsx` — Refs: US-001, FR-002, FR-012, FR-014, NFR-004, AC-018 — Depends: T002, T015, T018
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX e reler `INTERFACE.md`, `DESIGNSYSTEM.MD` e o bloco de referência indicado. Referência: `PessoaFormSheet` e `WorkspaceFormSheet`. Resultado: Padrão de `PessoaFormSheet` e `WorkspaceFormSheet` reutilizado (seletor nativo, erro abaixo do campo, foco no primeiro erro, descartar alterações).
  - [x] **EXECUTE**: Criar o painel lateral de criação e edição com campos por tipo, chave vazia e máscara na edição, erro de campo abaixo do campo com foco no primeiro erro e anúncio do resultado em `aria-live`. Resultado: `frontend/src/features/conexoes/ConexaoFormSheet.tsx`: painel lateral de criação e edição com campos por tipo (modelo, dimensões e URL base opcional para embeddings; URL para Qdrant), tipo travado na edição, chave vazia com máscara como placeholder e enviada só quando digitada, erros em vermelho abaixo do campo com `role=alert` e foco no primeiro erro. Teste novo `ConexaoFormSheet.test.tsx` com marcador de AC-018.
  - [x] **VERIFY**: Executar `npm run test:tdd -- ConexaoFormSheet` e exercitar validação, envio, falha do servidor e a garantia de que a chave não é preenchida na edição. Resultado: `npm run test:tdd -- src/features/conexoes` → 6 passed (3 de `ConexaoFormSheet`: criação com chave única, edição sem `segredo` quando não digitado, erro de campo com foco); `npx tsc --noEmit` e `npx eslint src/features/conexoes` sem erros. O ESLint rejeitou refs agrupadas em objeto (`react-hooks/refs`); troquei por refs individuais.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra) contra `DESIGNSYSTEM.MD` em desktop e mobile, tema claro e escuro, conteúdo curto e longo, foco e overflow; conferir o painel aberto, os erros em vermelho e o rodapé fixo. Registrar a forma de conferência, viewports, estados e ajustes. Resultado: Inspeção estática e em jsdom, sem navegador renderizado: mesmo `SheetContent` de `PessoaFormSheet` (largura máxima 32rem, rodapé com borda superior), rótulos `Label` + `Input` com `gap-1.5`, ajuda em `text-xs text-muted-foreground`, erro em `text-sm text-destructive`. Estados: criação, edição, erro de validação e salvando (`Button loading`). Nenhum ajuste necessário.
  - [x] **EVIDENCE**: Registrar arquivos, comando e resultado das interações. Resultado: Arquivos `ConexaoFormSheet.tsx` e `ConexaoFormSheet.test.tsx`; GREEN de AC-018 no formulário (FR-002, FR-012, FR-014, NFR-004, US-001).
  - [x] **IMPROVE**: Aplicar a melhoria de reaproveitar o rodapé do `Sheet` existente ou justificar nenhuma. Resultado: Melhoria aplicada: mapeamento da mensagem do servidor para o campo correto (`campoDoErro`), para o foco ir ao campo que causou a recusa.
  <!-- specsfy:evidence {"task": "T030", "refs": ["US-001", "FR-002", "FR-012", "FR-014", "NFR-004", "AC-018"], "files": ["frontend/src/features/conexoes/ConexaoFormSheet.tsx", "frontend/src/features/conexoes/ConexaoFormSheet.test.tsx"], "commands": [{"run": "npm run test:tdd -- src/features/conexoes", "exit": 0}, {"run": "npx tsc --noEmit", "exit": 0}, {"run": "npx eslint src/features/conexoes", "exit": 0}]} -->

- [x] T031 [CODE] [US-001] Criar as páginas `/conexoes` e `/conexoes/[id]`, `DetalheConexao` e o item de menu Conexões em `frontend/src/app/(autenticado)/layout.tsx` — Refs: US-001, US-004, FR-004, FR-012, FR-014, NFR-002, NFR-004, AC-006, AC-018 — Depends: T006, T018, T024, T029, T030
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX e reler `INTERFACE.md`, `DESIGNSYSTEM.MD` e o bloco de referência indicado. Referência: `/pessoas`, `/pessoas/[id]` e a regra `podeGerirPessoas` do layout; confirmar o `Breadcrumb` Equipe → Conexões → Conexão. Resultado: Especialista `specsfy-specialist-react-ui-components` consultado em `.agents/skills`; referências `/pessoas`, `/pessoas/[id]`, `PessoaFormSheet` e a regra `podeGerirPessoas` do layout relidas; trilha Equipe → Conexões → Conexão confirmada.
  - [x] **EXECUTE**: Criar `frontend/src/app/(autenticado)/conexoes/page.tsx`, `frontend/src/app/(autenticado)/conexoes/[id]/page.tsx` e `frontend/src/features/conexoes/DetalheConexao.tsx` com `PageHeader` único, `DetailLists`, recusa de `member` na URL direta e o item de menu visível somente a owner e admin. Resultado: `frontend/src/app/(autenticado)/conexoes/page.tsx` (lista com `PageHeader`, Nova conexão, formulário em painel lateral, exclusão por diálogo, aviso em `role=status` e erro com Tentar novamente), `conexoes/[id]/page.tsx` (detalhe com `DetailLists`, editar, desativar ou reativar e excluir), `DetalheConexao.tsx` e o layout `frontend/src/app/(autenticado)/layout.tsx` (item Conexões só para owner e admin, trilha de Conexões e da Nova Base). Member recebe aviso de permissão e a API de conexões nem é chamada.
  - [x] **VERIFY**: Executar `npm run test:tdd -- conexoes layout` e exercitar a navegação, o breadcrumb, o menu no mobile e a recusa de member. Resultado: `npm run test:tdd -- "src/app/(autenticado)/conexoes" "src/app/(autenticado)/layout" src/features/conexoes` → 26 passed (lista, recusa de member, desativar com anúncio, erro de carga, detalhe mascarado, 404, item de menu por papel e as duas trilhas novas); `npx tsc --noEmit` e `npx eslint` sem erros.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra) contra `DESIGNSYSTEM.MD` em desktop e mobile, tema claro e escuro, conteúdo curto e longo, foco e overflow; conferir lista, detalhe e menu no breakpoint mobile. Registrar a forma de conferência, viewports, estados e ajustes. Resultado: Inspeção estática e em jsdom, sem navegador renderizado: `PageHeader` único, `section` com `max-w-6xl` na lista e `max-w-5xl` no detalhe (iguais a Pessoas), `DetailLists` com bordas e `p-3`, item de menu no mesmo `nav` de Pessoas (`gap-4 text-sm`), trilha com os mesmos `[overflow-wrap:anywhere]`. Estados: lista, carregando, erro, permissão, 404, desativada. Nenhum ajuste necessário.
  - [x] **EVIDENCE**: Registrar arquivos, comando e o resultado das rotas por papel. Resultado: Arquivos das duas páginas, `DetalheConexao.tsx`, `layout.tsx` e testes; GREEN de AC-006 e AC-018 na interface (FR-004, FR-012, FR-014, NFR-002, NFR-004, US-001, US-004).
  - [x] **IMPROVE**: Aplicar a melhoria de extrair a regra de visibilidade do menu ou justificar nenhuma. Resultado: Melhoria aplicada: o detalhe reaproveita `DetailLists` e o mesmo tratamento de falha de Pessoas, sem criar componentes de cabeçalho ou de erro novos.
  <!-- specsfy:evidence {"task": "T031", "refs": ["US-001", "US-004", "FR-004", "FR-012", "FR-014", "NFR-002", "NFR-004", "AC-006", "AC-018"], "files": ["frontend/src/app/(autenticado)/conexoes/page.tsx", "frontend/src/app/(autenticado)/conexoes/[id]/page.tsx", "frontend/src/features/conexoes/DetalheConexao.tsx", "frontend/src/app/(autenticado)/layout.tsx"], "commands": [{"run": "npm run test:tdd -- \"src/app/(autenticado)/conexoes\" \"src/app/(autenticado)/layout\" src/features/conexoes", "exit": 0}, {"run": "npx tsc --noEmit", "exit": 0}, {"run": "npx eslint \"src/app/(autenticado)\" src/features/conexoes", "exit": 0}]} -->

- [x] T032 [CODE] [US-002] Implementar `useFluxoIngestao` e `BarraEtapas` em `frontend/src/features/ingestao/` — Refs: US-002, FR-013, FR-014, NFR-004, AC-015, AC-017 — Depends: T015, T016, T017
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX e reler `INTERFACE.md`, `DESIGNSYSTEM.MD` e o bloco de referência indicado. Referência: `useAssistente` e `api-client.ts`; confirmar o estado em memória e a saída protegida. Resultado: Especialista React UI consultado em `.agents/skills`; referências `useAssistente` e `api-client.ts` relidas; decisão: estado do fluxo só em memória do navegador, sem gravar nada no servidor antes de publicar.
  - [x] **EXECUTE**: Criar o hook com arquivos, valores, prévia, publicação e erros, preservando tudo ao voltar entre etapas, e `BarraEtapas` com `aria-current`, foco no título da etapa ao trocar e aviso antes de sair com alterações pendentes. Resultado: `frontend/src/lib/ingestao.ts` (limites de arquivo, padrões de fallback, `validarArquivos` e `validarDivisao`), `frontend/src/features/ingestao/useFluxoIngestao.ts` (etapas, arquivos, base preparada, divisão, prévia paginada, publicação por `POST /api/v1/bases`, invalidação da prévia a cada mudança) e `BarraEtapas.tsx` (`aria-current="step"`, só libera etapas já alcançadas). O foco no título da etapa e o aviso de saída ficam no `FluxoIngestao` (T037).
  - [x] **VERIFY**: Executar `npm run test:tdd -- useFluxoIngestao BarraEtapas` e exercitar avanço, retorno, recarga e saída protegida. Resultado: `npm run test:tdd -- src/features/ingestao/useFluxo src/features/ingestao/BarraEtapas` → 4 passed (preserva arquivos e valores ao voltar, invalida a prévia, envia arquivos e parâmetros sem segredo, teclado). O teste achou um defeito real, a deduplicação não cobria repetições no mesmo lote, e foi corrigido; `npx tsc --noEmit` e `npx eslint` sem erros.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra) contra `DESIGNSYSTEM.MD` em desktop e mobile, tema claro e escuro, conteúdo curto e longo, foco e overflow; conferir a barra de etapas nos estados ativo, concluído e desabilitado. Registrar a forma de conferência, viewports, estados e ajustes. Resultado: Inspeção estática e em jsdom, sem navegador renderizado: a barra usa `grid-cols-2 sm:grid-cols-4`, borda `rounded-lg border`, `px-3 py-2`, `text-sm`, a etapa atual com `border-primary bg-muted font-medium` e as futuras com `opacity-50`; rótulos com `[overflow-wrap:anywhere]`; foco `ring-2`. Estados: atual, alcançada, desabilitada. Nenhum ajuste necessário.
  - [x] **EVIDENCE**: Registrar arquivos, comando e resultado. Resultado: Arquivos `ingestao.ts`, `useFluxoIngestao.ts` e `BarraEtapas.tsx` com testes; GREEN do estado do fluxo (FR-013, FR-014, NFR-004, AC-015, AC-017).
  - [x] **IMPROVE**: Aplicar a melhoria de isolar o estado puro do efeito de rede ou justificar nenhuma. Resultado: Melhoria aplicada: validações de arquivo e divisão em `src/lib/ingestao.ts`, para as etapas Arquivos e Divisão compartilharem a mesma regra sem repetir limites.
  <!-- specsfy:evidence {"task": "T032", "refs": ["US-002", "FR-013", "FR-014", "NFR-004", "AC-015", "AC-017"], "files": ["frontend/src/lib/ingestao.ts", "frontend/src/features/ingestao/useFluxoIngestao.ts", "frontend/src/features/ingestao/BarraEtapas.tsx"], "commands": [{"run": "npm run test:tdd -- src/features/ingestao/useFluxo src/features/ingestao/BarraEtapas", "exit": 0}, {"run": "npx tsc --noEmit", "exit": 0}, {"run": "npx eslint src/lib src/features/ingestao", "exit": 0}]} -->

- [x] T033 [P] [CODE] [US-004] Implementar `EtapaArquivos` em `frontend/src/features/ingestao/EtapaArquivos.tsx` — Refs: US-004, FR-013, FR-014, NFR-004, AC-015, AC-016 — Depends: T015, T016, T017
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX e reler `INTERFACE.md`, `DESIGNSYSTEM.MD` e o bloco de referência indicado. Reaproveitar a validação e os limites de `UploadBaseSheet.tsx` antes de removê-lo. Resultado: Especialista React UI consultado; validação e limites de `UploadBaseSheet.tsx` reaproveitados em `src/lib/ingestao.ts` antes de removê-lo na T037.
  - [x] **EXECUTE**: Criar o seletor de múltiplos `.md` com os limites do backend, lista com remoção, a opção Usar base preparada e Próxima desabilitada sem arquivos. Resultado: `frontend/src/features/ingestao/EtapaArquivos.tsx`: seletor de múltiplos `.md` com limites do backend (50 arquivos, 5 MB, 50 MB), lista com remoção, erro em `Alert` e a opção Usar base preparada, que esconde o envio. O botão Próxima desabilitado sem arquivos fica no `FluxoIngestao` (T037).
  - [x] **VERIFY**: Executar `npm run test:tdd -- EtapaArquivos` e exercitar arquivo inválido, limite excedido, remoção e base preparada. Resultado: `npm run test:tdd -- src/features/ingestao/EtapaArquivos` → 3 passed (adiciona e remove, recusa `.txt` e arquivo acima de 5 MB sem adicionar nada, base preparada); `npx tsc --noEmit` e `npx eslint src/features/ingestao` sem erros.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra) contra `DESIGNSYSTEM.MD` em desktop e mobile, tema claro e escuro, conteúdo curto e longo, foco e overflow; conferir a lista com nomes curtos e longos e o estado vazio. Registrar a forma de conferência, viewports, estados e ajustes. Resultado: Inspeção estática e em jsdom, sem navegador renderizado: lista em `rounded-lg border` com `px-3 py-2` e nome com `[overflow-wrap:anywhere]` para nomes longos, ajuda em `text-xs text-muted-foreground`, `Input` de arquivo do sistema. Estados: vazio, com arquivos, erro e base preparada. Nenhum ajuste necessário.
  - [x] **EVIDENCE**: Registrar arquivos, comando e resultado. Resultado: Arquivos `EtapaArquivos.tsx` e `EtapaArquivos.test.tsx`; GREEN do envio e da base preparada (FR-013, FR-014, NFR-004, AC-015, AC-016, US-004).
  - [x] **IMPROVE**: Aplicar a melhoria de mover a validação para `frontend/src/lib/` ou justificar nenhuma. Resultado: Melhoria aplicada: a validação mora em `src/lib/ingestao.ts` e roda antes de adicionar à seleção, então uma seleção inválida nunca chega ao estado do fluxo.
  <!-- specsfy:evidence {"task": "T033", "refs": ["US-004", "FR-013", "FR-014", "NFR-004", "AC-015", "AC-016"], "files": ["frontend/src/features/ingestao/EtapaArquivos.tsx", "frontend/src/features/ingestao/EtapaArquivos.test.tsx"], "commands": [{"run": "npm run test:tdd -- src/features/ingestao/Etapa", "exit": 0}, {"run": "npx tsc --noEmit", "exit": 0}, {"run": "npx eslint src/features/ingestao", "exit": 0}]} -->

- [x] T034 [P] [CODE] [US-002] Implementar `EtapaDivisao` em `frontend/src/features/ingestao/EtapaDivisao.tsx` — Refs: US-002, FR-006, FR-007, FR-014, NFR-004, AC-015, AC-017 — Depends: T007, T009, T015, T017
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX e reler `INTERFACE.md`, `DESIGNSYSTEM.MD` e o bloco de referência indicado. Referência: `Select` e `Input` existentes e os padrões vindos de `GET /api/v1/ingestao/padroes`. Resultado: Especialista React UI consultado; `Select` nativo e `Input` do projeto e os padrões vindos de `GET /api/v1/ingestao/padroes` (via `useFluxoIngestao`) confirmados.
  - [x] **EXECUTE**: Criar o formulário de splitter, tamanho e overlap pré-preenchidos, com ajuda curta, validação em linha, erro abaixo do campo e o aviso que lista arquivos fora desses parâmetros. Resultado: `frontend/src/features/ingestao/EtapaDivisao.tsx`: estratégia (Markdown por cabeçalhos ou recursivo), tamanho e overlap pré-preenchidos, ajuda curta, validação em linha, erro abaixo do campo com `role=alert`, foco no primeiro campo inválido a cada tentativa de avançar e aviso dos arquivos cujo frontmatter traz `splitter`, `chunk_size_recommended` ou `chunk_overlap_recommended`. Sem seção avançada nem configuração por arquivo.
  - [x] **VERIFY**: Executar `npm run test:tdd -- EtapaDivisao` e exercitar limites, overlap maior que o tamanho e foco no primeiro erro. Resultado: `npm run test:tdd -- src/features/ingestao/EtapaDivisao` → 3 passed (campos e opções, erro com foco e `aria-invalid`, aviso do frontmatter); `npx tsc --noEmit` e `npx eslint src/features/ingestao` sem erros.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra) contra `DESIGNSYSTEM.MD` em desktop e mobile, tema claro e escuro, conteúdo curto e longo, foco e overflow; conferir erros, ajuda e o aviso de arquivos com configuração própria. Registrar a forma de conferência, viewports, estados e ajustes. Resultado: Inspeção estática e em jsdom, sem navegador renderizado: grade `md:grid-cols-2` (uma coluna no mobile), `Label` + `Input` com `gap-1.5`, ajuda `text-xs`, erro `text-sm text-destructive`, aviso em `Alert` na largura inteira. Estados: padrão, inválido com foco, aviso de configuração própria. Nenhum ajuste necessário.
  - [x] **EVIDENCE**: Registrar arquivos, comando e resultado. Resultado: Arquivos `EtapaDivisao.tsx` e `EtapaDivisao.test.tsx`; GREEN da divisão (FR-006, FR-007, FR-014, NFR-004, AC-015, AC-017, US-002).
  - [x] **IMPROVE**: Aplicar a melhoria de derivar os limites do endpoint em vez de repeti-los ou justificar nenhuma. Resultado: Melhoria aplicada: os limites vêm do endpoint por `padroes.limites` em vez de ficarem repetidos no componente.
  <!-- specsfy:evidence {"task": "T034", "refs": ["US-002", "FR-006", "FR-007", "FR-014", "NFR-004", "AC-015", "AC-017"], "files": ["frontend/src/features/ingestao/EtapaDivisao.tsx", "frontend/src/features/ingestao/EtapaDivisao.test.tsx"], "commands": [{"run": "npm run test:tdd -- src/features/ingestao/Etapa", "exit": 0}, {"run": "npx tsc --noEmit", "exit": 0}, {"run": "npx eslint src/features/ingestao", "exit": 0}]} -->

- [x] T035 [P] [CODE] [US-002] Implementar `EtapaPrevia` em `frontend/src/features/ingestao/EtapaPrevia.tsx` — Refs: US-002, FR-005, FR-014, NFR-003, NFR-004, AC-015, AC-017 — Depends: T015, T026
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX e reler `INTERFACE.md`, `DESIGNSYSTEM.MD` e o bloco de referência indicado. Referência: `ChunksFontes` para o texto truncado com ver mais. Resultado: Especialista React UI consultado; `ChunksFontes` relido para o texto truncado com ver mais; botões de paginação nomeados 'Página seguinte' e 'Página anterior' para não colidir com 'Próxima' do fluxo.
  - [x] **EXECUTE**: Criar o resumo com contagens e avisos, a lista paginada somente leitura com documento, posição, tamanho e texto truncado, o filtro por documento e os estados de cálculo, vazio e erro. Resultado: `frontend/src/features/ingestao/EtapaPrevia.tsx`: calcula a prévia ao entrar na etapa, mostra resumo (documentos, chunks, tamanho médio), avisos, filtro por documento, lista paginada somente leitura com documento, posição, tamanho e texto truncado com ver mais ou ver menos, estados de cálculo e vazio e falha em `Alert` com Tentar novamente, e resultado anunciado em `role=status`.
  - [x] **VERIFY**: Executar `npm run test:tdd -- EtapaPrevia` e exercitar paginação, filtro, texto longo e falha com Tentar novamente. Resultado: `npm run test:tdd -- src/features/ingestao/EtapaPrevia` → 3 passed (resumo e ver mais, paginação e filtro, cálculo ao entrar e falha); `npx tsc --noEmit` e `npx eslint src/features/ingestao` sem erros.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra) contra `DESIGNSYSTEM.MD` em desktop e mobile, tema claro e escuro, conteúdo curto e longo, foco e overflow; conferir a lista com chunks curtos e muito longos e a quebra de texto. Registrar a forma de conferência, viewports, estados e ajustes. Resultado: Inspeção estática e em jsdom, sem navegador renderizado: resumo em grade de 3 colunas com `gap-px bg-border`, lista `rounded-lg border` com `p-3`, texto com `whitespace-pre-wrap [overflow-wrap:anywhere]` para chunks curtos e muito longos, paginação com `Button outline sm`. Estados: calculando, resultado, vazio, erro e texto expandido. Nenhum ajuste necessário.
  - [x] **EVIDENCE**: Registrar arquivos, comando e resultado. Resultado: Arquivos `EtapaPrevia.tsx` e `EtapaPrevia.test.tsx`; GREEN da prévia (FR-005, FR-014, NFR-003, NFR-004, AC-015, AC-017, US-002).
  - [x] **IMPROVE**: Aplicar a melhoria de reaproveitar o truncamento de `ChunksFontes` ou justificar nenhuma. Resultado: Melhoria aplicada: o anúncio da prévia vai em região `role=status` somente para leitor de tela, sem poluir a tela.
  <!-- specsfy:evidence {"task": "T035", "refs": ["US-002", "FR-005", "FR-014", "NFR-003", "NFR-004", "AC-015", "AC-017"], "files": ["frontend/src/features/ingestao/EtapaPrevia.tsx", "frontend/src/features/ingestao/EtapaPrevia.test.tsx"], "commands": [{"run": "npm run test:tdd -- src/features/ingestao/Etapa", "exit": 0}, {"run": "npx tsc --noEmit", "exit": 0}, {"run": "npx eslint src/features/ingestao", "exit": 0}]} -->

- [x] T036 [CODE] [US-003] Implementar `EtapaPublicacao` em `frontend/src/features/ingestao/EtapaPublicacao.tsx` — Refs: US-003, FR-008, FR-009, FR-010, FR-014, NFR-004, AC-017, AC-019 — Depends: T017, T019, T027
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX e reler `INTERFACE.md`, `DESIGNSYSTEM.MD` e o bloco de referência indicado. Referência: `PainelProgresso`, `IndicadorProcessamento` e `Button loading`. Resultado: Especialista React UI consultado; `PainelProgresso`, `IndicadorProcessamento` e `Button loading` relidos; decisão: a etapa consulta `GET /api/v1/ingestao/dimensao` com espera de 250 ms e não bloqueia o botão enquanto verifica, porque o servidor repete a verificação antes de gravar.
  - [x] **EXECUTE**: Criar os dois `Select` de conexões ativas, a comparação de dimensões em linha, o campo de coleção, o resumo final e o botão Publicar desabilitado com a razão visível; orientar para Conexões sem conexão ativa e navegar para a Base com o `PainelProgresso`. Resultado: `frontend/src/features/ingestao/EtapaPublicacao.tsx`: duas listas de conexões ativas (auto-seleção quando só há uma), campo de coleção, dimensões em linha (incompatível, coleção nova ou compatível), resumo (arquivos, chunks, modelo, destino), Publicar desabilitado com a razão visível, orientação para Conexões quando não há conexão ativa, falha em `Alert` com Tentar novamente sem perder o preenchimento e, ao publicar, aviso em `role=status` e navegação para `/execucoes/{base_id}`, onde o `PainelProgresso` mostra inseridos, mantidos e removidos.
  - [x] **VERIFY**: Executar `npm run test:tdd -- EtapaPublicacao` e exercitar divergência de dimensão, conexão desativada, falha com Tentar novamente e o resultado anunciado. Resultado: `npm run test:tdd -- src/features/ingestao/EtapaPublicacao` → 4 passed (os 4 RED de AC-017 e AC-019 ficaram verdes): sem conexão ativa, dimensão divergente com as duas dimensões, falha com Tentar novamente e coleção preservada, navegação para a Base com anúncio; `npx tsc --noEmit` e `npx eslint src/features/ingestao` sem erros.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra) contra `DESIGNSYSTEM.MD` em desktop e mobile, tema claro e escuro, conteúdo curto e longo, foco e overflow; conferir o botão bloqueado, a razão visível e o resumo. Registrar a forma de conferência, viewports, estados e ajustes. Resultado: Inspeção estática e em jsdom, sem navegador renderizado: formulário em `md:grid-cols-2` (uma coluna no mobile), seletores e `Input` no mesmo padrão dos formulários do projeto, dimensões em `text-sm` (`text-destructive` quando incompatíveis), resumo em grade `gap-px bg-border` com `[overflow-wrap:anywhere]`, razão do bloqueio em `text-sm text-muted-foreground` sob o botão. Estados: carregando, sem conexão, bloqueado, divergente, publicando, falha e publicado. Nenhum ajuste necessário.
  - [x] **EVIDENCE**: Registrar arquivos, comando e resultado. Resultado: Arquivos `EtapaPublicacao.tsx` e `EtapaPublicacao.test.tsx`; GREEN de AC-017 e AC-019 (FR-008, FR-009, FR-010, FR-014, NFR-004, US-003).
  - [x] **IMPROVE**: Aplicar a melhoria de uma lista de razões de bloqueio única ou justificar nenhuma. Resultado: Melhoria aplicada: uma única expressão de razão de bloqueio decide o botão e o texto exibido, então o motivo visível nunca diverge da regra.
  <!-- specsfy:evidence {"task": "T036", "refs": ["US-003", "FR-008", "FR-009", "FR-010", "FR-014", "NFR-004", "AC-017", "AC-019"], "files": ["frontend/src/features/ingestao/EtapaPublicacao.tsx"], "commands": [{"run": "npm run test:tdd -- src/features/ingestao/EtapaPublicacao", "exit": 0}, {"run": "npx tsc --noEmit", "exit": 0}, {"run": "npx eslint src/features/ingestao", "exit": 0}]} -->

- [x] T037 [CODE] [US-004] Compor `FluxoIngestao` e criar `frontend/src/app/(autenticado)/workspaces/[id]/bases/nova/page.tsx`, trocar o botão em `frontend/src/app/(autenticado)/workspaces/[id]/page.tsx` e remover `frontend/src/features/bases/UploadBaseSheet.tsx` — Refs: US-004, FR-012, FR-013, FR-014, NFR-004, AC-015, AC-016, AC-017 — Depends: T016, T032, T033, T034, T035, T036
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX e reler `INTERFACE.md`, `DESIGNSYSTEM.MD` e o bloco de referência indicado. Localizar todos os consumidores de `UploadBaseSheet` com busca no repositório antes de remover. Resultado: Especialista React UI consultado; consumidores de `UploadBaseSheet` localizados por busca no repositório: só `workspaces/[id]/page.tsx` e o próprio teste (mais `INTERFACE.md` e `docs/`, tratados na T038 e pelo documentador).
  - [x] **EXECUTE**: Criar `FluxoIngestao.tsx` que compõe as etapas, a página com `PageHeader` e `Breadcrumb` Equipe → Workspaces → Workspace → Nova Base, o botão Nova Base visível somente a owner e admin, a recusa de member na URL direta e remover o sheet e seu teste e atualizar os casos de `frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx` que ainda abrem o painel Enviar base. Resultado: `FluxoIngestao.tsx` compõe BarraEtapas, as quatro etapas e o rodapé Voltar e Próxima (foco no título da etapa ao trocar, validação da divisão ao avançar, Próxima desabilitada sem arquivos, aviso antes de fechar a aba e ao seguir um link interno com alterações pendentes); página `workspaces/[id]/bases/nova/page.tsx` com `PageHeader`, recusa de member e Tentar novamente; a página do Workspace troca o botão Enviar base pelo link Nova Base (só owner e admin); `UploadBaseSheet.tsx` e seu teste removidos e os três casos de `workspaces/[id]/page.test.tsx` que abriam o painel foram atualizados.
  - [x] **VERIFY**: Executar `npm run test:tdd` completo em `frontend/` e `npm run lint`, e percorrer as quatro etapas por teclado até a página da Base. Resultado: `npm run test:tdd` completo em `frontend/` → 53 arquivos e 219 testes passando (inclui os 3 RED de AC-015 e o RED de AC-016); `npx tsc --noEmit`, `npx eslint src` e `npm run lint` sem erros. A jornada das quatro etapas até a página da Base é exercitada por teclado e por clique nos testes de `FluxoIngestao`, `EtapaPublicacao` e da página. Defeitos corrigidos no caminho: o frontend quebrava se `/ingestao/padroes` omitisse campos (agora mescla com os padrões locais) e meu teste de saída cancelava o próprio envio de arquivo.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra) contra `DESIGNSYSTEM.MD` em desktop e mobile, tema claro e escuro, conteúdo curto e longo, foco e overflow; conferir as duas colunas no desktop, uma coluna no mobile e a barra de etapas. Registrar a forma de conferência, viewports, estados e ajustes. Resultado: Inspeção estática e em jsdom, sem navegador renderizado: página com `max-w-5xl`, `PageHeader` único e ação Voltar ao Workspace, cartão da etapa em `rounded-lg border p-4`, rodapé com `border-t pt-4`, barra de etapas em `grid-cols-2 sm:grid-cols-4`, formulários em uma coluna no mobile e duas a partir de `md`. Estados percorridos: cada etapa, carregando, erro, member recusado. Conferência em navegador real fica para o fechamento (T043).
  - [x] **EVIDENCE**: Registrar arquivos criados e removidos, comandos e o resultado da jornada completa. Resultado: Arquivos criados e removidos listados no comentário `specsfy:evidence`; GREEN de AC-015, AC-016 e AC-017 (FR-012, FR-013, FR-014, NFR-004, US-004).
  - [x] **IMPROVE**: Aplicar a melhoria de remover estilos e testes órfãos do sheet ou justificar nenhuma. Resultado: Melhoria aplicada: remoção de estilos e testes órfãos do sheet e do `UploadBaseSheet.test.tsx`, e atualização dos testes da página do Workspace para o novo link.
  <!-- specsfy:evidence {"task": "T037", "refs": ["US-004", "FR-012", "FR-013", "FR-014", "NFR-004", "AC-015", "AC-016", "AC-017"], "files": ["frontend/src/features/ingestao/FluxoIngestao.tsx", "frontend/src/app/(autenticado)/workspaces/[id]/bases/nova/page.tsx", "frontend/src/app/(autenticado)/workspaces/[id]/page.tsx", "frontend/src/features/ingestao/useFluxoIngestao.ts"], "commands": [{"run": "npm run test:tdd", "exit": 0}, {"run": "npx tsc --noEmit", "exit": 0}, {"run": "npm run lint", "exit": 0}]} -->

- [x] T038 [DOC] Atualizar `INTERFACE.md` com os blocos, rotas e consumidores criados, reaproveitados e removidos (`UploadBaseSheet`) — Refs: US-001, US-002, US-003, US-004, FR-012, FR-013, FR-014, AC-016, AC-018 — Depends: T031, T037
  - [x] **PREP**: Reler `INTERFACE.md` e a tabela de blocos da seção 10 para listar finalidade, arquivo, API, estados, consumidores e regra de reaproveitamento. Resultado: `INTERFACE.md` e a tabela de blocos da seção 10 relidos; lista de blocos criados, reaproveitados e removidos montada a partir dos arquivos reais.
  - [x] **EXECUTE**: Registrar cada bloco novo e as telas Conexões, Conexão e Nova Base, remover `UploadBaseSheet` e atualizar a descrição da tela do Workspace. Resultado: `INTERFACE.md`: linha do `UploadBaseSheet` substituída por 12 linhas (`FluxoIngestao`, `useFluxoIngestao`, `BarraEtapas`, `EtapaArquivos`, `EtapaDivisao`, `EtapaPrevia`, `EtapaPublicacao`, `lib/ingestao`, `DataGridConexoes`, `ConexaoFormSheet`, `ExcluirConexaoDialog`, `DetalheConexao`) com finalidade, arquivo, API, estados, consumidores e regra de reuso; telas Nova Base, Conexões e Conexão acrescentadas; tela do Workspace passa a citar o link Nova Base; lista de telas entregues e de pastas de features atualizada; consumidor do `Sheet` corrigido.
  - [x] **VERIFY**: Conferir cada arquivo citado com `ls` e rodar `monitor_context.mjs --check`. Resultado: Todos os caminhos `frontend/src/...` citados em `INTERFACE.md` existem (verificação por laço de `ls`) e `monitor_context.mjs --check` retorna `CURRENT` com `--acknowledge-project-no-change`; a única menção restante a `UploadBaseSheet` é a nota de que o fluxo o substitui.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só atualiza documentação de interface; a conferência visual ficou nas tarefas das telas. Resultado: `Não aplicável`: a tarefa só atualiza documentação de interface; a conferência visual ficou nas tarefas das telas.
  - [x] **EVIDENCE**: Registrar o diff do `INTERFACE.md` e a saída do monitor. Resultado: Diff de `INTERFACE.md` e saída do monitor (US-001, US-002, US-003, US-004, FR-012, FR-013, FR-014, AC-016, AC-018).
  - [x] **IMPROVE**: Aplicar a melhoria de remover entradas obsoletas ou justificar nenhuma. Resultado: Melhoria aplicada: tela do Workspace e consumidores do `Sheet` corrigidos, para o registro não apontar mais para um componente removido.

#### Fase final — Operação, documentação e qualidade

- [x] T039 [OPS] Declarar a variável da chave de cifra e o secret do Swarm em `deploy/stack.prod.yml` e estender `tests/test_deploy_stack.py` — Refs: FR-002, NFR-001, NFR-005, AC-013 — Depends: T020
  - [x] **PREP**: Reler `deploy/stack.prod.yml` e o BACKLOG-0030; confirmar que o provisionamento do secret em produção segue naquele item e que `deploy/stack.local.yml` não é versionado com valores. Resultado: `deploy/stack.prod.yml` relido e o BACKLOG-0030 confirmado como dono do provisionamento do secret em produção; `deploy/stack.local.yml` não foi tocado e nenhum valor foi escrito.
  - [x] **EXECUTE**: Adicionar o secret externo e a variável apontando para o arquivo no serviço do backend e do worker, sem valor real, e acrescentar a afirmação correspondente ao teste da stack. Resultado: `deploy/stack.prod.yml`: secret externo `conexoes_chave` declarado, incluído nos secrets de aplicação e exportado como `APP_CONEXOES_CHAVE_FILE=/run/secrets/conexoes_chave` nos comandos do backend e do worker; nenhum valor de chave na stack. `tests/test_deploy_stack.py` passou a exigir o secret em `SECRETS_DE_PRODUCAO` e ganhou um caso próprio (secret externo, variável só no comando e nunca em `environment`).
  - [x] **VERIFY**: Executar `uv run pytest tests/test_deploy_stack.py tests/test_deploy_build_and_deploy_script.py -q`. Resultado: `uv run pytest tests/test_deploy_stack.py tests/test_deploy_build_and_deploy_script.py -q` → 11 passed; `uv run ruff check tests deploy` → ok; `deploy/*.sh` não enumera secrets, então o script de deploy não muda.
  - [x] **VISUAL**: `Não aplicável`: a tarefa só altera backend e não tem superfície visual. Resultado: `Não aplicável`: a tarefa só altera a definição da stack de produção, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando, resultado e a ausência de valor secreto no diff. Resultado: Diff sem valor secreto (só o nome `conexoes_chave` e o caminho do secret) e GREEN do teste da stack (FR-002, NFR-001, NFR-005, AC-013). Provisionar o secret no Swarm (`docker secret create conexoes_chave`) continua sendo o passo manual do BACKLOG-0030 antes do próximo deploy.
  - [x] **IMPROVE**: Aplicar a melhoria de documentar a recuperação por recadastro no `README.md` ou justificar nenhuma. Resultado: Melhoria aplicada: a chave é lida de arquivo (`APP_CONEXOES_CHAVE_FILE`), nunca de variável de ambiente, para não aparecer em `docker inspect`.

- [x] T040 [P] [DOC] Atualizar `.specsfy/STACK.md` com a dependência `cryptography` e a chave de cifra — Refs: FR-002, NFR-001, AC-001 — Depends: T020
  - [x] **PREP**: Ler `.specsfy/STACK.md` e `pyproject.toml` e confirmar a versão resolvida em `uv.lock`. Resultado: `.specsfy/STACK.md`, `pyproject.toml` e `uv.lock` lidos; versão resolvida `cryptography` 50.0.2.
  - [x] **EXECUTE**: Registrar a linha de cifra de segredos com evidência em `pyproject.toml`, `uv.lock` e `src/app/conexoes.py`, preservando o texto humano. Resultado: Linha 'Cifra de segredos das conexões de ingestão' acrescentada dentro do bloco gerenciado, com evidência em `pyproject.toml`, `uv.lock`, `src/app/settings.py` e `src/app/main.py`; `src/app/conexoes.py` será citado quando existir (T022).
  - [x] **VERIFY**: Executar `monitor_context.mjs --check` e conferir que não pede mais stack pendente. Resultado: `monitor_context.mjs --check` não aponta mais stack pendente.
  - [x] **VISUAL**: `Não aplicável`: documentação sem superfície visual. Resultado: `Não aplicável`: documentação sem superfície visual.
  - [x] **EVIDENCE**: Registrar o diff e a saída do monitor. Resultado: Diff de `.specsfy/STACK.md` com uma linha nova; monitor sem pendência de stack (FR-002, NFR-001, AC-001).
  - [x] **IMPROVE**: Nenhuma melhoria necessária: a tarefa é um registro pontual e o monitor valida a evidência. Resultado: Nenhuma melhoria necessária: o registro é pontual e o monitor valida a evidência.

- [x] T041 [P] [DOC] Atualizar `.specsfy/DATABASE.md` com `conexoes`, `eventos_conexao` e as colunas novas de `bases` — Refs: FR-004, FR-011, NFR-005, AC-001, AC-014 — Depends: T021
  - [x] **PREP**: Reler as regras de `.specsfy/RULES.md` sobre edição manual do `DATABASE.md` e o model final de `src/app/models.py`. Resultado: Regra de edição manual do `DATABASE.md` relida e `src/app/models.py` comparado campo a campo.
  - [x] **EXECUTE**: Acrescentar as duas tabelas, as colunas novas, a retenção de 90 dias dos eventos, a revisão `0026_conexoes_ingestao` e a linha de conexões em `Informações a guardar confirmadas`, sem rodar o scanner automático. Resultado: Linhas `conexoes` e `eventos_conexao`, colunas novas de `bases`, revisão `0026_conexoes_ingestao`, retenção de 90 dias e a linha confirmada de conexões em `Informações a guardar confirmadas`; scanner automático não executado.
  - [x] **VERIFY**: Comparar cada campo com `src/app/models.py` e executar `monitor_context.mjs --check`. Resultado: `monitor_context.mjs --check` sem pendência de persistência.
  - [x] **VISUAL**: `Não aplicável`: documentação sem superfície visual. Resultado: `Não aplicável`: documentação sem superfície visual.
  - [x] **EVIDENCE**: Registrar o diff e a saída do monitor. Resultado: Diff de `.specsfy/DATABASE.md` e monitor `CURRENT` (FR-004, FR-011, NFR-005, AC-001, AC-014).
  - [x] **IMPROVE**: Aplicar a melhoria de substituir a linha provisória de conexões pela versão confirmada ou justificar nenhuma. Resultado: Melhoria aplicada: a linha provisória de conexões foi substituída pela versão confirmada, com fontes atualizadas.

- [x] T042 [DOC] Registrar em `.specsfy/RULES.md` as regras de chave somente escrita cifrada e de argumentos de job sem segredo, e revisar `PROJECT.md` — Refs: FR-002, NFR-001, NFR-005, AC-013 — Depends: T028
  - [x] **PREP**: Reler `.specsfy/RULES.md` e `PROJECT.md`; usar `$specsfy-aux-rules` e preservar as regras existentes. Resultado: `.specsfy/RULES.md` e `PROJECT.md` relidos; regras existentes preservadas e somente decisões já confirmadas registradas, no padrão da skill `$specsfy-aux-rules`.
  - [x] **EXECUTE**: Acrescentar as duas regras confirmadas (DEC-003, DEC-009 e DEC-012) e atualizar `PROJECT.md` com as capacidades de conexões reutilizáveis e fluxo em etapas, ou registrar a justificativa de ausência de impacto material. Resultado: `.specsfy/RULES.md` ganhou três regras em Segurança e privacidade: chave de conexão somente escrita e cifrada com Fernet (sem rotação automática, secret do Swarm), nenhum segredo nos argumentos de job, e política de URLs de conexão (sem credenciais, sem loopback, link-local e metadados, exceção explícita de desenvolvimento). `PROJECT.md` ganhou o parágrafo da SPEC-0026 em Pessoas e contexto de uso e a capacidade nova em Capacidades principais.
  - [x] **VERIFY**: Executar `monitor_context.mjs --check`, repetindo com `--acknowledge-project-no-change` somente se a justificativa for registrada. Resultado: `monitor_context.mjs --check` → `CURRENT` sem `--acknowledge-project-no-change`, porque o `PROJECT.md` foi de fato revisado e atualizado.
  - [x] **VISUAL**: `Não aplicável`: documentação sem superfície visual. Resultado: `Não aplicável`: documentação sem superfície visual.
  - [x] **EVIDENCE**: Registrar o diff e a saída do monitor. Resultado: Diff de `.specsfy/RULES.md` e `PROJECT.md` e saída do monitor (FR-002, NFR-001, NFR-005, AC-013).
  - [x] **IMPROVE**: Nenhuma melhoria necessária: as regras apenas formalizam decisões já confirmadas. Resultado: Nenhuma melhoria necessária: as regras apenas formalizam decisões já confirmadas (DEC-003, DEC-009 e DEC-012) e o `PROJECT.md` já descreve a capacidade pelo resultado, não pelos arquivos.

- [x] T043 [TEST] Executar regressão e rastreabilidade com `.agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs` sobre `specs/review/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md` e fechar o Delivery Gate — Refs: US-001, US-002, US-003, US-004, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018, AC-019 — Depends: T028, T037, T038, T039, T040, T041, T042
  - [x] **PREP**: Confirmar o banco de teste com `check_database_safety.mjs` e listar suítes, checks e gates. Resultado: Banco de teste confirmado `SAFE` com `check_database_safety.mjs` antes de cada comando; suítes, checks e gates listados.
  - [x] **EXECUTE**: Executar `uv run ruff check`, `uv run pytest`, `npm run test:tdd` e `npm run lint` em `frontend/`, o verificador `check_traceability.mjs` e `verify_repo.mjs`. Resultado: `uv run ruff check`, `uv run pytest`, `npm run test:tdd`, `npm run lint`, `npx tsc --noEmit` e `npm run build` em `frontend/`, `check_traceability.mjs --full-chain`, `verify_acceptance.mjs` e `verify_repo.mjs`. A regressão achou dois testes quebrados por esta spec, corrigidos: `test_client_neutrality` (a baseline de dependências não tinha `cryptography`) e `test_docs_safety` (o contrato da fachada em `docs/architecture.md` não listava `preview_chunks` e `describe_collection`, e o texto de credenciais foi corrigido).
  - [x] **VERIFY**: Confirmar ausência de falhas, de marcadores sem spec e de requisito sem evidência. Resultado: Backend `uv run pytest` → 475 passed e 1 skipped (baseline antes da spec: 420 passed e 1 skipped); `uv run ruff check` → ok. Frontend `npm run test:tdd` → 53 arquivos e 219 testes passando, `npm run lint` e `npx tsc --noEmit` sem erros, `npm run build` compila e lista `/conexoes`, `/conexoes/[id]` e `/workspaces/[id]/bases/nova`. `check_traceability.mjs --full-chain` → 42 de 42 IDs, `verify_acceptance.mjs` → `QA: PASSED`, `verify_repo.mjs` → `PASSED`. Sem testes pulados novos nem tarefas abertas.
  - [x] **VISUAL**: Repassar a conferência visual final das telas Conexões, Conexão e Nova Base nos dois viewports e temas, registrando bordas, espaçamentos, margens, padding e tipografia. Resultado: Conferência final das telas Conexões, Conexão e Nova Base por inspeção estática e em jsdom, sem navegador renderizado (nenhum Chromium, Chrome ou Playwright existe neste ambiente): bordas (`rounded-lg border`), espaçamentos (`gap-4`, `gap-5`), margens e padding (`p-3`, `p-4`, `px-3 py-2.5`) e tipografia (`text-sm`, `text-xs`, `font-mono` no ID, `[overflow-wrap:anywhere]` para texto longo) reaproveitam os tokens de Pessoas e Workspaces; uma coluna no mobile e duas a partir de `md`. Limite declarado: a renderização real em viewport e tema escuro não foi observada; recomenda-se abrir as três telas em desktop e mobile antes de publicar.
  - [x] **EVIDENCE**: Registrar contagens e comandos finais nas seções 11–13. Resultado: Comandos e contagens acima; seções 11 e 12 com GREEN e `Passed` para os 19 AC e para cada FR e NFR; gate do Ato III registrado na seção 13.
  - [x] **IMPROVE**: Registrar a retrospectiva do processo e as melhorias aplicadas. Resultado: Retrospectiva: a fase RED descobriu a lacuna da dimensão antes da implementação (endpoint `/ingestao/dimensao`), e a regressão total pegou dois contratos congelados (dependências e fachada), que passam a documentar a spec. Melhoria para o processo: rodar a suíte completa já ao fechar a primeira tarefa que altera `pyproject.toml` ou a fachada.

### 15. Ordem de execução

- Caminho crítico: T001–T019 (RED) → T020/T021 (fundação) → T022 → T023 → T024 → T025 → T026 → T027 → T028 → T031 → T037 → T038 → T043.
- Tarefas paralelas: T029 e T030 (arquivos distintos, ambas dependem só de T018); T033, T034 e T035 (arquivos distintos, dependem só de T015, T016 e T026); T040 e T041 (documentos distintos). As demais compartilham arquivo, estado mutável ou dependência.
- Estratégia de MVP: US-001 completa (T020–T024 e T029–T031) é o primeiro marco demonstrável; US-002 e US-003 formam o segundo; a Nova Base em etapas (T032–T037) fecha a jornada e substitui o `UploadBaseSheet`.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Nova dependência Python `cryptography` (Fernet) para cifrar chaves; não consta em `uv.lock` e exige `uv add`.
- Chave de cifra fornecida ao entrypoint por secret do Docker Swarm ou variável de ambiente; o provisionamento do secret em produção segue o BACKLOG-0030 e `deploy/stack.prod.yml`.
- SPEC-0002, SPEC-0019, SPEC-0020 e SPEC-0025 já concluídas.
- Atualização manual de `.specsfy/DATABASE.md`, `.specsfy/STACK.md`, `INTERFACE.md` e `PROJECT.md` ao entregar.

#### Riscos

- Perda ou troca da chave de cifra torna as conexões ilegíveis → a recuperação documentada é recadastrar as chaves das conexões (rotação automática fora de escopo); erro de decifra gera falha genérica, nunca vaza valor.
- URL base ou URL Qdrant maliciosa (SSRF) por uma pessoa admin → validar esquema e recusar loopback, link-local e metadados da nuvem na API e novamente no worker; permitir exceção local somente por configuração explícita de desenvolvimento.
- Jobs já enfileirados no formato antigo durante a implantação → o worker aceita os dois formatos nesta entrega.
- Prévia de lote grande consome memória e CPU → reaproveitar os limites do envio atual e paginar a resposta.
- Duas chamadas de interface (criar e executar) deixariam Base sem execução → `iniciar_execucao` cria ambas na mesma requisição.
- Dois caminhos de envio com comportamentos diferentes → o `UploadBaseSheet` é removido e `INTERFACE.md` atualizado.

#### Suposições

- Padrões de divisão: splitter `header`, tamanho 1000 e overlap 200 como em `config.yaml`; os limites de 200 a 4000 e de 0 até a metade do tamanho foram confirmados em 2026-10-06.
- A dimensão do modelo é declarada na conexão de embeddings (inteiro obrigatório, padrão 1536) em vez de consultada ao provedor; coleção inexistente é criada com essa dimensão.
- A máscara é fixa, sem nenhum caractere da chave.
- A precedência segue o comportamento atual: frontmatter por arquivo prevalece sobre o formulário; a prévia lista os arquivos afetados.
- Cada publicação cria uma Base nova; adicionar a uma Base existente fica fora.
- "Usar base preparada" seleciona a base preparada no servidor, sem arquivos no navegador, e a prévia e a publicação a leem como hoje.
- A prévia reenvia os arquivos a cada cálculo, processa em diretório temporário e não guarda nada; limites iguais aos do envio atual.
- O nome da conexão é único por equipe e projeto.
- Esta entrega usa a cabeça atual das migrações; o identificador `down_revision` é resolvido na implementação.

### 17. Decisões

- **DEC-001**: A configuração de divisão é por Base, no envio, e não uma tela global — preserva Bases diferentes no mesmo Workspace com estratégias diferentes.
- **DEC-002**: Conexões reutilizáveis cadastradas pela interface, administradas por owner e admin da mesma equipe e projeto — alternativa descartada: somente conexões preparadas no servidor.
- **DEC-003**: Chave somente escrita, cifrada em repouso, nunca devolvida — alternativa descartada: referência a segredo do servidor (a entrega de secrets de produção segue no BACKLOG-0030).
- **DEC-004**: Dois tipos de conexão na primeira entrega, `embeddings_openai` e `qdrant`; Chroma, Pinecone e outros ficam no BACKLOG-0009.
- **DEC-005**: Bloquear a publicação quando a dimensão diverge, antes de gravar qualquer coisa — alternativa descartada: deixar o Qdrant recusar.
- **DEC-006**: Sem Record Manager próprio; reaproveitar a sincronização da SPEC-0002 e exibir inseridos, mantidos e removidos.
- **DEC-007**: Prévia descartável, sem persistência e sem edição de chunks — alternativa descartada: chunks persistidos e editáveis.
- **DEC-008**: Página com etapas substitui o `UploadBaseSheet`; menu Conexões com `DataGrid` e `Sheet`; nada guardado no servidor antes de publicar.
- **DEC-009**: O worker recebe identificadores de conexão e decifra em memória, porque argumentos de job ficam persistidos na fila.
- **DEC-011**: Alterações em conexões geram eventos próprios em `eventos_conexao`, sem a chave e com retenção de 90 dias — alternativas descartadas: só autoria e data na conexão, ou reaproveitar `eventos_acesso`.
- **DEC-012**: Chave de cifra única, fornecida como secret do Swarm ou variável de ambiente, sem rotação automática; trocar exige recadastrar as conexões — alternativas descartadas: duas chaves para rotação e serviço externo de segredos.
- **DEC-013**: Limites de divisão confirmados: tamanho de 200 a 4000 e overlap de 0 até a metade do tamanho, sempre menor que o tamanho.
- **DEC-014**: Nenhum bloco ReUI nesta entrega; composições próprias sobre as primitives shadcn/ui, como Pessoas e Workspaces — o registry `@reui` permanece configurado para uso futuro.
- **DEC-015**: A verificação de dimensão aceita a limitação de `describe_scope` (destino inacessível equivale a coleção ausente) em vez de ampliar o contrato neutro; o erro real surge na execução sem gravar dados.
- **DEC-016**: A etapa Publicação consulta `GET /api/v1/ingestao/dimensao` para mostrar as dimensões e bloquear Publicar; a publicação repete a mesma verificação no servidor, que continua sendo a garantia — alternativa descartada: descobrir a divergência só pelo 409 ao publicar.
- **DEC-010**: `POST /api/v1/bases` aceita `iniciar_execucao` para criar Base e execução na mesma requisição, evitando Base sem execução entre duas chamadas.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/STACK.md` registra a dependência `cryptography` e a chave de cifra, e `.specsfy/DATABASE.md` registra `conexoes`, `eventos_conexao` e as colunas novas de `bases`.
- [x] `PROJECT.md` é revisado pela mudança de capacidade (conexões e fluxo em etapas) e `.specsfy/RULES.md` recebe as regras novas confirmadas (chave somente escrita e cifrada, argumentos de job sem segredo).
- [x] `INTERFACE.md` lista cada bloco React criado, reaproveitado ou removido (`UploadBaseSheet`).
