# Especificação integrada: Fluxo de ingestão com etapas, conexões reutilizáveis e prévia de chunks

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0026 |
| Slug | 0026-fluxo-de-ingestao-com-etapas-e-conexoes |
| Status | Draft |
| Effort | 8 |
| Effort updated at | 2026-10-06 |
| Effort rationale | Nova tabela com segredo cifrado, mudança do worker para decifrar fora da fila, prévia sem estado, verificação de dimensão no vector store e quatro telas novas substituindo o envio atual; muitas decisões cruzam backend, pipeline e interface. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Pending |
| Plan Gate | Pending |
| Delivery Gate | Pending |
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
    Then a API responde 201 com a conexão ativa, sem a chave, com `segredo_definido` verdadeiro e a máscara fixa, e o banco guarda somente o texto cifrado
```

#### AC-002 — Cadastrar conexão Qdrant e preservar a chave na edição

**Cobre**: US-001, FR-001, FR-002, FR-004, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @FR-004 @NFR-001 @AC-002
Feature: Conexões reutilizáveis de ingestão

  Scenario: Cadastrar conexão Qdrant e preservar a chave na edição
    Given uma conexão Qdrant ativa com chave definida
    When uma pessoa admin edita o nome sem informar chave e depois edita informando uma nova chave
    Then a primeira edição mantém o texto cifrado anterior e a segunda o substitui; nenhuma resposta devolve a chave antiga ou a nova
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
    Then a conexão some das opções de publicação enquanto desativada, o vínculo e o histórico da Base permanecem, os vetores não são tocados e a reativação a devolve às opções
```

#### AC-005 — Excluir somente conexão sem uso

**Cobre**: US-001, FR-003, FR-004, NFR-002

```gherkin
@US-001 @FR-003 @FR-004 @NFR-002 @AC-005
Feature: Ciclo de vida das conexões

  Scenario: Excluir somente conexão sem uso
    Given uma conexão sem Base vinculada e outra vinculada a uma Base
    When uma pessoa owner tenta excluir as duas
    Then a primeira é removida com 204 e a segunda recebe 409 com a quantidade de Bases em uso e permanece intacta
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
    Then os argumentos do job contêm somente identificadores, o worker decifra as chaves em memória, os logs e o manifesto não contêm chaves, e a repetição reaproveita splitter, tamanho, overlap, coleção e vínculos da Base
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

- **FR-001**: O sistema deve permitir que owner e admin cadastrem conexões de dois tipos, `embeddings_openai` (nome, modelo, URL base opcional, dimensões inteiras maiores que 0 e chave) e `qdrant` (nome, URL e chave opcional), escopadas ao tenant e ao projeto da pessoa, validando esquema HTTP ou HTTPS, ausência de credenciais na URL e recusa de hosts de loopback, link-local e metadados da nuvem.
- **FR-002**: O sistema deve tratar a chave de cada conexão como somente escrita: cifrá-la antes de persistir com uma chave única fornecida ao entrypoint por secret do Docker Swarm ou variável de ambiente, sem rotação automática, nunca devolvê-la em resposta, log ou manifesto, expor apenas `segredo_definido` e uma máscara fixa sem caracteres da chave, preservar a chave quando a edição não informar outra e substituí-la quando informar.
- **FR-003**: O sistema deve permitir desativar e reativar uma conexão preservando vínculos, histórico e vetores já publicados, impedir que uma conexão desativada seja usada em nova publicação ou nova execução e permitir a exclusão definitiva somente de conexão sem Base vinculada, com 409 quando houver uso.
- **FR-004**: O sistema deve oferecer listagem, detalhe, edição, desativação, reativação e exclusão de conexões por `/api/v1/conexoes`, com `id`, `nome`, `tipo`, `situacao`, configuração não secreta, `segredo_definido`, quantidade de Bases em uso, autoria e datas, restritas a owner e admin da mesma equipe e projeto, e registrar em `eventos_conexao` cada criação, edição, troca de chave, desativação, reativação e exclusão com a pessoa autora, a ação e o horário, sem a chave e sem valores de campos secretos, retidos por 90 dias.
- **FR-005**: O sistema deve calcular a prévia dos chunks por `POST /api/v1/ingestao/previa` a partir de arquivos `.md` enviados ou da base preparada e dos parâmetros de divisão, devolvendo documentos, total de chunks, tamanho médio, avisos, arquivos com configuração própria e chunks paginados com documento de origem, posição, tamanho e texto, sem persistir nada.
- **FR-006**: O sistema deve validar os parâmetros de divisão: splitter `header` ou `recursive`, tamanho de chunk inteiro entre 200 e 4000 caracteres, overlap inteiro entre 0 e a metade do tamanho (sempre menor que o tamanho), com os limites expostos por `GET /api/v1/ingestao/padroes`, e pré-preencher os valores padrão de `config.yaml` (header, 1000 e 200).
- **FR-007**: O sistema deve manter a precedência atual do chunker: a configuração do frontmatter de cada arquivo (`splitter`, inclusive `qa`, `chunk_size_recommended` e `chunk_overlap_recommended`) prevalece sobre os parâmetros do formulário, e tanto a prévia quanto a execução aplicam exatamente a mesma regra.
- **FR-008**: O sistema deve estender `POST /api/v1/bases` para receber splitter, tamanho, overlap, `conexao_embeddings_id`, `conexao_vector_store_id`, coleção e `iniciar_execucao`, exigindo conexões ativas do tipo correto na mesma equipe e projeto, e quando `iniciar_execucao` for verdadeiro criar a execução na mesma requisição.
- **FR-009**: O sistema deve comparar, antes de criar qualquer registro, a dimensão declarada na conexão de embeddings com a dimensão da coleção obtida por `describe_scope` do vector store da conexão Qdrant, bloquear a publicação com 409 e mensagem clara quando divergirem e aceitar coleção inexistente.
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
- `GET /api/v1/ingestao/padroes` e `POST /api/v1/ingestao/previa`: `src/app/routers/ingestao.py`; a prévia grava os arquivos recebidos somente em diretório temporário do processo, apagado ao fim da requisição, sem tocar storage, banco, embeddings ou vector store.
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
specs/draft/0026-fluxo-de-ingestao-com-etapas-e-conexoes/
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

- shadcn/ui fornece as primitives já instaladas (`Button`, `Input`, `Label`, `Select`, `Sheet`, `Dialog`, `Alert`, `Badge`, `Skeleton`); nenhum bloco ReUI `@reui/c-*` é necessário: as composições acima são próprias sobre as primitives, e a adoção de ReUI fica registrada como decisão em aberto na validação.
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
| US-001, FR-001, FR-002, FR-004, NFR-001, NFR-002, AC-001 | AC-001 na seção 6 | Cadastrar conexão de embeddings OpenAI em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-001 FR-002 FR-004 NFR-001 NFR-002 AC-001` | Pending | Pending | Pending |
| US-001, FR-001, FR-002, FR-004, NFR-001, AC-002 | AC-002 na seção 6 | Cadastrar conexão Qdrant e preservar a chave na edição em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-001 FR-002 FR-004 NFR-001 AC-002` | Pending | Pending | Pending |
| US-001, FR-001, FR-002, NFR-002, AC-003 | AC-003 na seção 6 | Recusar conexão inválida em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-001 FR-002 NFR-002 AC-003` | Pending | Pending | Pending |
| US-001, FR-003, FR-004, FR-008, NFR-002, AC-004 | AC-004 na seção 6 | Desativar e reativar uma conexão em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-003 FR-004 FR-008 NFR-002 AC-004` | Pending | Pending | Pending |
| US-001, FR-003, FR-004, NFR-002, AC-005 | AC-005 na seção 6 | Excluir somente conexão sem uso em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-003 FR-004 NFR-002 AC-005` | Pending | Pending | Pending |
| US-001, US-004, FR-004, FR-012, NFR-002, AC-006 | AC-006 na seção 6 | Recusar acesso de member e de outra equipe às conexões em `tests/test_app_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-001 US-004 FR-004 FR-012 NFR-002 AC-006` | Pending | Pending | Pending |
| US-002, FR-005, FR-006, FR-007, NFR-003, AC-007 | AC-007 na seção 6 | Calcular a prévia com splitter por cabeçalhos em `tests/test_app_ingestao_previa.py` com marcador próprio `SPECSFY: SPEC-0026 US-002 FR-005 FR-006 FR-007 NFR-003 AC-007` | Pending | Pending | Pending |
| US-002, FR-005, FR-007, NFR-003, AC-008 | AC-008 na seção 6 | Respeitar o frontmatter na prévia e avisar sobre os arquivos afetados em `tests/test_app_ingestao_previa.py` com marcador próprio `SPECSFY: SPEC-0026 US-002 FR-005 FR-007 NFR-003 AC-008` | Pending | Pending | Pending |
| US-002, FR-005, FR-006, NFR-003, AC-009 | AC-009 na seção 6 | Recusar parâmetros e arquivos inválidos na prévia em `tests/test_app_ingestao_previa.py` com marcador próprio `SPECSFY: SPEC-0026 US-002 FR-005 FR-006 NFR-003 AC-009` | Pending | Pending | Pending |
| US-003, FR-007, FR-008, FR-009, FR-010, FR-011, NFR-005, AC-010 | AC-010 na seção 6 | Publicar uma Base com conexões ativas em `tests/test_app_publicacao.py` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-007 FR-008 FR-009 FR-010 FR-011 NFR-005 AC-010` | Pending | Pending | Pending |
| US-003, FR-008, FR-009, NFR-002, AC-011 | AC-011 na seção 6 | Bloquear a publicação quando a dimensão diverge em `tests/test_app_publicacao.py` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-008 FR-009 NFR-002 AC-011` | Pending | Pending | Pending |
| US-003, FR-003, FR-008, FR-009, FR-011, NFR-002, AC-012 | AC-012 na seção 6 | Recusar conexão desativada ou de outra equipe na publicação em `tests/test_app_publicacao.py` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-003 FR-008 FR-009 FR-011 NFR-002 AC-012` | Pending | Pending | Pending |
| US-003, FR-010, FR-011, NFR-001, NFR-005, AC-013 | AC-013 na seção 6 | Decifrar a chave somente no worker e repetir com os mesmos parâmetros em `tests/test_app_tasks_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-001 NFR-005 AC-013` | Pending | Pending | Pending |
| US-003, FR-010, FR-011, NFR-005, AC-014 | AC-014 na seção 6 | Executar Base legada com a configuração global em `tests/test_app_tasks_conexoes.py` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-005 AC-014` | Pending | Pending | Pending |
| US-002, US-004, FR-006, FR-013, FR-014, NFR-004, AC-015 | AC-015 na seção 6 | Percorrer as etapas preservando o preenchimento em `frontend/src/features/ingestao/FluxoIngestao.test.tsx` com marcador próprio `SPECSFY: SPEC-0026 US-002 US-004 FR-006 FR-013 FR-014 NFR-004 AC-015` | Pending | Pending | Pending |
| US-004, FR-012, FR-013, FR-014, AC-016 | AC-016 na seção 6 | Substituir o envio atual e oferecer a base preparada em `frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx` com marcador próprio `SPECSFY: SPEC-0026 US-004 FR-012 FR-013 FR-014 AC-016` | Pending | Pending | Pending |
| US-002, US-003, FR-013, FR-014, NFR-004, AC-017 | AC-017 na seção 6 | Mostrar loading, vazio e erro nas etapas em `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` com marcador próprio `SPECSFY: SPEC-0026 US-002 US-003 FR-013 FR-014 NFR-004 AC-017` | Pending | Pending | Pending |
| US-001, FR-012, FR-014, NFR-004, AC-018 | AC-018 na seção 6 | Listar e administrar conexões na interface em `frontend/src/features/conexoes/DataGridConexoes.test.tsx` com marcador próprio `SPECSFY: SPEC-0026 US-001 FR-012 FR-014 NFR-004 AC-018` | Pending | Pending | Pending |
| US-003, FR-010, FR-014, AC-019 | AC-019 na seção 6 | Acompanhar inseridos, mantidos e removidos depois de publicar em `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` com marcador próprio `SPECSFY: SPEC-0026 US-003 FR-010 FR-014 AC-019` | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-001 | AC-002 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-001 | AC-003 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-002 | AC-001 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-002 | AC-002 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-002 | AC-003 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-003 | AC-004 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-003 | AC-005 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-003 | AC-012 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-004 | AC-001 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-004 | AC-002 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-004 | AC-004 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-004 | AC-005 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-004 | AC-006 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-005 | AC-007 | Integração | `tests/test_app_ingestao_previa.py` | Pending |
| FR-005 | AC-008 | Integração | `tests/test_app_ingestao_previa.py` | Pending |
| FR-005 | AC-009 | Integração | `tests/test_app_ingestao_previa.py` | Pending |
| FR-006 | AC-007 | Integração | `tests/test_app_ingestao_previa.py` | Pending |
| FR-006 | AC-009 | Integração | `tests/test_app_ingestao_previa.py` | Pending |
| FR-006 | AC-015 | Componente | `frontend/src/features/ingestao/FluxoIngestao.test.tsx` | Pending |
| FR-007 | AC-007 | Integração | `tests/test_app_ingestao_previa.py` | Pending |
| FR-007 | AC-008 | Integração | `tests/test_app_ingestao_previa.py` | Pending |
| FR-007 | AC-010 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-008 | AC-004 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-008 | AC-010 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-008 | AC-011 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-008 | AC-012 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-009 | AC-010 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-009 | AC-011 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-009 | AC-012 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-010 | AC-010 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-010 | AC-013 | Integração | `tests/test_app_tasks_conexoes.py` | Pending |
| FR-010 | AC-014 | Integração | `tests/test_app_tasks_conexoes.py` | Pending |
| FR-010 | AC-019 | Componente | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Pending |
| FR-011 | AC-010 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-011 | AC-012 | Integração | `tests/test_app_publicacao.py` | Pending |
| FR-011 | AC-013 | Integração | `tests/test_app_tasks_conexoes.py` | Pending |
| FR-011 | AC-014 | Integração | `tests/test_app_tasks_conexoes.py` | Pending |
| FR-012 | AC-006 | Integração | `tests/test_app_conexoes.py` | Pending |
| FR-012 | AC-016 | Componente | `frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx` | Pending |
| FR-012 | AC-018 | Componente | `frontend/src/features/conexoes/DataGridConexoes.test.tsx` | Pending |
| FR-013 | AC-015 | Componente | `frontend/src/features/ingestao/FluxoIngestao.test.tsx` | Pending |
| FR-013 | AC-016 | Componente | `frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx` | Pending |
| FR-013 | AC-017 | Componente | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Pending |
| FR-014 | AC-015 | Componente | `frontend/src/features/ingestao/FluxoIngestao.test.tsx` | Pending |
| FR-014 | AC-016 | Componente | `frontend/src/app/(autenticado)/workspaces/[id]/page.test.tsx` | Pending |
| FR-014 | AC-017 | Componente | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Pending |
| FR-014 | AC-018 | Componente | `frontend/src/features/conexoes/DataGridConexoes.test.tsx` | Pending |
| FR-014 | AC-019 | Componente | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Pending |
| NFR-001 | AC-001 | Integração | `tests/test_app_conexoes.py` | Pending |
| NFR-001 | AC-002 | Integração | `tests/test_app_conexoes.py` | Pending |
| NFR-001 | AC-013 | Integração | `tests/test_app_tasks_conexoes.py` | Pending |
| NFR-002 | AC-001 | Integração | `tests/test_app_conexoes.py` | Pending |
| NFR-002 | AC-003 | Integração | `tests/test_app_conexoes.py` | Pending |
| NFR-002 | AC-004 | Integração | `tests/test_app_conexoes.py` | Pending |
| NFR-002 | AC-005 | Integração | `tests/test_app_conexoes.py` | Pending |
| NFR-002 | AC-006 | Integração | `tests/test_app_conexoes.py` | Pending |
| NFR-002 | AC-011 | Integração | `tests/test_app_publicacao.py` | Pending |
| NFR-002 | AC-012 | Integração | `tests/test_app_publicacao.py` | Pending |
| NFR-003 | AC-007 | Integração | `tests/test_app_ingestao_previa.py` | Pending |
| NFR-003 | AC-008 | Integração | `tests/test_app_ingestao_previa.py` | Pending |
| NFR-003 | AC-009 | Integração | `tests/test_app_ingestao_previa.py` | Pending |
| NFR-004 | AC-015 | Componente | `frontend/src/features/ingestao/FluxoIngestao.test.tsx` | Pending |
| NFR-004 | AC-017 | Componente | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Pending |
| NFR-004 | AC-018 | Componente | `frontend/src/features/conexoes/DataGridConexoes.test.tsx` | Pending |
| NFR-005 | AC-010 | Integração | `tests/test_app_publicacao.py` | Pending |
| NFR-005 | AC-013 | Integração | `tests/test_app_tasks_conexoes.py` | Pending |
| NFR-005 | AC-014 | Integração | `tests/test_app_tasks_conexoes.py` | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md`
- **Achados**: Pending. Sem dúvida bloqueante; aguarda a validação semântica da `$specsfy-04-validate`.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/draft/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md`
- **Achados**: Pending.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0026-fluxo-de-ingestao-com-etapas-e-conexoes/spec.md .`
- **Achados**: Pending.

### 14. Tarefas

Pendente: a decomposição em tarefas é produzida por `$specsfy-05-tasks` depois que o Definition Gate for `Passed`. Formato esperado:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Cada tarefa terá o checklist `PREP`, `EXECUTE`, `VERIFY`, `VISUAL`, `EVIDENCE` e `IMPROVE`, nessa ordem.

### 15. Ordem de execução

- Pendente: definida por `$specsfy-05-tasks`. Sequência prevista: migração e modelos, cifra e rotas de conexões, prévia, publicação com verificação de dimensão, worker com decifra, telas de Conexões, fluxo em etapas, remoção do `UploadBaseSheet` e atualização de `INTERFACE.md`.

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
- **DEC-010**: `POST /api/v1/bases` aceita `iniciar_execucao` para criar Base e execução na mesma requisição, evitando Base sem execução entre duas chamadas.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
