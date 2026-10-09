# Especificação integrada: Expor no front as configurações do processamento

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0029 |
| Slug | 0029-expor-configuracoes-do-processamento-no-front |
| Status | Complete |
| Effort | 8 |
| Effort updated at | 2026-10-08 |
| Effort rationale | Seis estratégias de divisão com campos próprios, resumos, cabeçalhos, qualidade e destino guardados por Base, teste de conexão com rede e segredo cifrado, e mudanças em três etapas da interface e no formulário de conexões; cruza pipeline, backend, worker e frontend. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-08 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

Quem opera o pipeline pelo front só escolhe duas estratégias de divisão (por cabeçalhos e recursiva), tamanho e overlap. Resumos de seção, níveis de cabeçalho, mínimo útil de qualidade, status bloqueados, `batch_size` e `sync_mode` ficam presos em constantes do backend que espelham o `config.yaml`. A Prévia mostra sempre 10 chunks por página, com Voltar e Próxima no fim da lista. Os seletores das etapas ficam ilegíveis no tema escuro. E uma conexão cadastrada com erro, como um Qdrant sem a chave exigida, só falha na indexação, com a mensagem genérica "ver logs do worker". Em 2026-10-08, uma conexão Qdrant sem chave foi salva sem aviso e a execução falhou com 401.

#### Resultado desejado

No fluxo de Nova Base, a pessoa escolhe entre as estratégias do `langchain-text-splitters` aplicáveis a Markdown, vê só os campos de cada uma, ajusta resumos, cabeçalhos e qualidade, define `batch_size` e `sync_mode`, revisa a Prévia com as ações no topo e a quantidade de chunks por página que preferir, e cadastra conexões sem sair do fluxo. Ao salvar, cada conexão é testada como nas credenciais do n8n. A Base guarda o que foi usado, e Bases anteriores não mudam.

#### Métricas de sucesso

- 6 de 6 estratégias aceitas na Prévia e na publicação, medido por AC-002.
- 100% das Bases publicadas guardam as escolhas e geram na execução o mesmo total de chunks da Prévia, medido por AC-005.
- 0 mudança de resultado em Bases anteriores, medido por AC-006 e pela regressão.
- 100% das conexões salvas recebem um resultado de teste em até 15 segundos, e 0 ocorrência de chave em respostas ou logs, medido por AC-019, AC-020 e AC-021.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: Quais splitters a versão instalada oferece? → `langchain_text_splitters` expõe, entre outros, `MarkdownHeaderTextSplitter`, `MarkdownTextSplitter`, `ExperimentalMarkdownSyntaxTextSplitter`, `RecursiveCharacterTextSplitter`, `CharacterTextSplitter` e `TokenTextSplitter` (inspeção local com `uv run python -c "import langchain_text_splitters"`). Impacto: FR-001.
- **R-002**: `TokenTextSplitter` exige dependência nova? → Não: `tiktoken` já está em `uv.lock` e importa no ambiente. Impacto: FR-001, DEC-004.
- **R-003**: De onde vêm os padrões hoje? → `src/app` não lê o `config.yaml`; `src/app/ingestao.py` mantém `PADROES` e `montar_chunking` (resumos ligados, mínimo 3) espelhando o arquivo; cabeçalhos padrão vêm de `chunk_documents`; qualidade e contrato usam os padrões da fachada (`minimo_util` 60, nenhum status bloqueado). Impacto: FR-003, NFR-002.
- **R-004**: Breadcrumb e resumos dependem de chaves fixas? → Sim: `_build_heading_breadcrumb` e `_section_summary_chunks` em `src/pipeline/chunker.py` usam `titulo`, `secao` e `subsecao`. Impacto: FR-004 e DEC-003.
- **R-005**: Qual é o `sync_mode` atual de uma Base com conexão? → `append`: o destino da conexão não traz `sync_mode` e `src/pipeline/indexing.py` assume `append`; `namespace` e `index_name` são ignorados pelo adaptador Qdrant. Impacto: FR-006 e a correção registrada no backlog.
- **R-006**: `character` já tem significado? → Sim: no frontmatter, `character` segue a divisão recursiva (`chunk_documents`). Impacto: DEC-002 e AC-007.
- **R-007**: Existe formulário de conexão reutilizável? → Sim: `frontend/src/features/conexoes/ConexaoFormSheet.tsx` é um `Sheet` com criação e edição, usado pela tela Conexões. Impacto: FR-010.

#### Fontes e contexto consultados

- `specs/backlog/0036-expor-configuracoes-restantes-do-config-yaml-no-front.md`, brief refinado com as decisões de 2026-10-08.
- Capturas: `specs/inbox/2026-10-08-205918-expor-no-front-todas-as-configuracoes-do-config-yaml.md`, `specs/inbox/2026-10-08-214501-dropdown-da-etapa-divisao-com-texto-e-fundo-da-mesma-cor-no-tema-escuro.md`, `specs/inbox/2026-10-08-215112-rascunho-do-fluxo-de-nova-base-conexao-sem-sair-do-fluxo-e-ajustes-da-previa.md` e `specs/inbox/2026-10-08-221250-testar-a-conexao-ao-salvar-como-as-credenciais-do-n8n.md`.
- Código: `src/pipeline/chunker.py`, `src/pipeline/service.py`, `src/pipeline/indexing.py`, `src/pipeline/safety.py`, `src/pipeline/providers/vectorstores/qdrant.py`, `src/app/ingestao.py`, `src/app/routers/ingestao.py`, `src/app/routers/bases.py`, `src/app/routers/conexoes.py`, `src/app/conexoes.py`, `src/app/tasks.py` e `config.yaml`.
- Frontend: `frontend/src/features/ingestao/` (FluxoIngestao, EtapaDivisao, EtapaPrevia, EtapaPublicacao, useFluxoIngestao), `frontend/src/lib/ingestao.ts`, `frontend/src/features/conexoes/ConexaoFormSheet.tsx` e `frontend/src/app/globals.css`.
- `INTERFACE.md`, `DESIGNSYSTEM.MD`, `.specsfy/STACK.md`, `.specsfy/RULES.md` e `.specsfy/DATABASE.md`.
- Specs concluídas: SPEC-0026 (fluxo em etapas e conexões) e SPEC-0028 (exclusão pela coleção e conexão da Base).

#### Documentação consultada

- Nenhuma documentação externa: as estratégias foram conferidas no pacote instalado e no código local.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Quais grupos do `config.yaml` entram? → **A**: divisão, qualidade e contrato, e destino; ficam fora validação, log e caminhos.
- **Q**: Onde as configurações valem? → **A**: por Base, escolhidas no fluxo de Nova Base; os padrões atuais são o valor inicial.
- **Q**: Onde cada campo aparece? → **A**: divisão, resumos, cabeçalhos e Qualidade na etapa Divisão; destino na Publicação; campos pouco usados em bloco Avançado recolhido; o fluxo segue com quatro etapas.
- **Q**: Como ficam os campos de destino? → **A**: `batch_size` e `sync_mode` com padrão `append` e aviso sobre `mirror`; `namespace` e `index_name` não entram (corrige a resposta anterior, dada sobre informação errada do agente).
- **Q**: Quais estratégias? → **A**: as aplicáveis a Markdown sem dependência nova: cabeçalhos, Markdown, Markdown sintático, recursiva, por caractere e por tokens.
- **Q**: Ajustes da Prévia? → **A**: ações no topo e seletor de 10, 20, 50, 75 e 100 chunks por página.
- **Q** (2026-10-08, mudança tardia): "o markdown text splitter ele tem a opção 'split by headers' que quero ter também e no character text splitter", com prints do Flowise → **A**: opção 1: seletor Dividir por cabeçalhos até H1 a H6 nas três estratégias Markdown (com Desativado no Markdown recursivo), H4 a H6 no breadcrumb, resumos por título e seção, e separador livre no Por caractere.
- **Q**: Conexão sem sair do fluxo e teste ao salvar? → **A**: painel lateral na Publicação; ao salvar, o sistema testa e mostra sucesso ou o motivo, permitindo salvar mesmo com falha.

#### Dúvidas abertas

- Nenhuma bloqueante. A barra fixa ao rolar é suposição recomendada (seção 16).

### 3. Escopo e atores

#### Incluído

- Seis estratégias de divisão com campos próprios, na Prévia e na publicação.
- Resumos de seção (ligar e mínimo de subseções), níveis de cabeçalho, mínimo útil e status bloqueados.
- `batch_size` e `sync_mode` na Publicação, com aviso sobre `mirror`.
- Escolhas guardadas em `bases.chunking` e usadas pelo worker e pela repetição.
- Barra de ações no topo da Prévia e seletor de chunks por página.
- Contraste correto dos seletores nos dois temas.
- Teste da conexão ao criar e ao editar, sem bloquear o salvamento.
- Cadastro de conexão em painel lateral dentro da Publicação.

#### Fora de escopo

- Rascunho e retomada do fluxo de Nova Base (backlog próprio).
- Splitters de sentenças e NLP (NLTK, spaCy, Sentence Transformers), `SemanticChunker` e splitters de outros formatos (HTML, LaTeX, Python, JS, JSON, coreano).
- `namespace`, `index_name`, validação (`limiar_minimo`, `top_k`), log e caminhos do servidor.
- Tela global de configurações e edição da configuração de uma Base existente.
- Botão de logs da execução e motivo de falha legível na execução (captura `specs/inbox/2026-10-08-220405-botao-para-ver-os-logs-de-uma-execucao-que-falhou.md`).
- Consulta usando as conexões da Base (captura `specs/inbox/2026-10-08-221250-consulta-de-base-ignora-as-conexoes-vinculadas-a-base.md`).
- Separadores personalizados da estratégia recursiva e nomes personalizados de metadados de cabeçalho (os nomes dos níveis são fixos).

#### Atores

- **Owner e admin**: conduzem o fluxo de Nova Base e cadastram conexões; são os únicos papéis com acesso ao fluxo e à tela Conexões.
- **Worker**: executa e repete a indexação com as escolhas guardadas na Base.
- **Provedor de embeddings e Qdrant**: recebem as chamadas de teste e de indexação.

### 4. Princípios e restrições do projeto

- **PR-001**: `src/app/` depende somente da fachada `src.pipeline.service`; o teste de conexão e os splitters ficam em `src/pipeline/` (`.specsfy/RULES.md`).
- **PR-002**: Segredos de conexão só cifrados no Postgres e decifrados em memória; nunca em respostas, logs, argumentos de job ou mensagens de erro (SPEC-0026).
- **PR-003**: Nada é gravado no servidor antes de publicar; a Prévia continua descartável (SPEC-0026).
- **PR-004**: Em React, telas compostas por componentes; shadcn/ui e ReUI conforme `INTERFACE.md`; reaproveitar antes de criar.
- **PR-005**: Testes no Postgres de teste com rollback transacional; nenhuma chamada de rede real na suíte.
- **PR-006**: Uma branch por spec: `spec/0029-expor-configuracoes-do-processamento-no-front`.

### 5. Histórias de usuário

#### US-001 — Escolher a estratégia de divisão (P1)

Como owner ou admin, quero escolher entre as estratégias de divisão do LangChain aplicáveis a Markdown e ajustar os campos de cada uma, para testar a divisão que melhor serve à minha base.

**Por que P1**: a divisão define o que vai para o Qdrant; hoje só duas estratégias estão disponíveis.
**Teste independente**: calcular a Prévia com cada estratégia e publicar uma Base com a escolhida.
**Requisitos**: FR-001, FR-002, FR-003, FR-011, NFR-002, NFR-003

#### US-002 — Ajustar resumos, cabeçalhos e qualidade (P1)

Como owner ou admin, quero ligar ou desligar os resumos de seção, escolher os níveis de cabeçalho, o mínimo útil e os status bloqueados, para controlar os chunks sem editar arquivo no servidor.

**Por que P1**: são as opções do `config.yaml` que mudam o resultado e hoje não aparecem na tela.
**Teste independente**: calcular a Prévia variando cada opção e ver o efeito nos chunks e avisos.
**Requisitos**: FR-004, FR-005

#### US-003 — Definir o destino da indexação (P2)

Como owner ou admin, quero escolher o tamanho do lote de embeddings e o modo de sincronização, para controlar custo, ritmo e o que acontece na repetição.

**Por que P2**: os padrões atuais funcionam; o valor está em ajustar casos específicos.
**Teste independente**: publicar com `batch_size` 20 e `mirror` e conferir a execução e a repetição.
**Requisitos**: FR-006, NFR-002

#### US-004 — Revisar a Prévia com menos rolagem (P2)

Como owner ou admin, quero as ações da Prévia no topo e escolher quantos chunks ver por página, para revisar muitos chunks sem rolar até o fim.

**Por que P2**: melhora a revisão sem mudar o resultado.
**Teste independente**: abrir uma Prévia longa, trocar para 50 por página e avançar sem rolar.
**Requisitos**: FR-007, FR-008, NFR-003

#### US-005 — Cadastrar e testar conexões sem sair do fluxo (P1)

Como owner ou admin, quero cadastrar uma conexão dentro da Publicação e saber na hora se ela funciona, para não perder o trabalho nem descobrir o erro só na indexação.

**Por que P1**: em 2026-10-08 a falta da conexão interrompeu o fluxo, e uma conexão sem chave só falhou na indexação.
**Teste independente**: na Publicação sem conexões, cadastrar uma conexão pelo painel e ver o resultado do teste.
**Requisitos**: FR-009, FR-010, NFR-001, NFR-003

### 6. Cenários BDD de aceite

#### AC-001 — Cabeçalhos escolhidos guiam a divisão

**Cobre**: US-001, US-002, FR-001, FR-004

```gherkin
@US-001 @US-002 @FR-001 @FR-004 @AC-001
Feature: Configurar o processamento pelo front

  Scenario: Cabeçalhos escolhidos guiam a divisão
    Given dois arquivos Markdown com títulos #, ## e ###
    When a Prévia é calculada com a estratégia por cabeçalhos e Dividir por cabeçalhos até H2
    Then os chunks quebram apenas nos títulos # e ##, o breadcrumb mostra título e seção, e nenhum chunk traz a subseção como metadado
```

#### AC-002 — As seis estratégias são aceitas com seus próprios campos

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-002
Feature: Configurar o processamento pelo front

  Scenario: As seis estratégias são aceitas com seus próprios campos
    Given um arquivo Markdown válido
    When a Prévia é calculada com cada estratégia (header, markdown, markdown_syntax, recursive, character_split e token) e os campos próprios de cada uma
    Then cada resposta traz chunks gerados pelo splitter correspondente do langchain-text-splitters, e a estratégia por tokens respeita o tamanho medido em tokens do encoding escolhido
```

#### AC-003 — A etapa Divisão mostra só os campos da estratégia

**Cobre**: US-001, FR-002, FR-011, NFR-003

```gherkin
@US-001 @FR-002 @FR-011 @NFR-003 @AC-003
Feature: Configurar o processamento pelo front

  Scenario: A etapa Divisão mostra só os campos da estratégia
    Given a etapa Divisão aberta
    When a pessoa escolhe Por caractere, depois Por tokens e depois Markdown sintático
    Then aparecem respectivamente o separador personalizado em campo livre com tamanho e overlap, o encoding com tamanho e overlap em tokens, e só o seletor Dividir por cabeçalhos (H1 a H6) com a opção de remover cabeçalhos; em Markdown recursivo o seletor inclui Desativado; cada campo tem rótulo associado e é alcançável por teclado
```

#### AC-004 — Valores inválidos são recusados antes de gerar chunks

**Cobre**: US-001, FR-002, FR-003

```gherkin
@US-001 @FR-002 @FR-003 @AC-004
Feature: Configurar o processamento pelo front

  Scenario: Valores inválidos são recusados antes de gerar chunks
    Given a etapa Divisão
    When a pessoa informa tamanho fora de 200 a 4000 caracteres, overlap maior que a metade, estratégia desconhecida, nível de cabeçalho fora de H1 a H6 (ou Desativado fora da estratégia Markdown recursivo), separador vazio ou com mais de 10 caracteres, ou tamanho por tokens fora de 50 a 2000
    Then a tela mostra o erro em linha sem avançar, e a API devolve 422 com mensagem clara sem calcular a Prévia nem gravar nada
```

#### AC-005 — Publicar guarda as escolhas e repete os chunks da Prévia

**Cobre**: US-001, US-003, FR-003, FR-006

```gherkin
@US-001 @US-003 @FR-003 @FR-006 @AC-005
Feature: Configurar o processamento pelo front

  Scenario: Publicar guarda as escolhas e repete os chunks da Prévia
    Given uma Prévia calculada com estratégia markdown, tamanho 800, resumos desligados e batch_size 20
    When a pessoa publica a Base
    Then a Base guarda essas escolhas em `chunking`, a execução recebe as mesmas seções de configuração e o total de chunks previstos é igual ao total da Prévia
```

#### AC-006 — Base anterior continua igual

**Cobre**: US-001, FR-003, NFR-002

```gherkin
@US-001 @FR-003 @NFR-002 @AC-006
Feature: Configurar o processamento pelo front

  Scenario: Base anterior continua igual
    Given uma Base publicada antes desta entrega, com `chunking` contendo só splitter, tamanho e overlap
    When a execução é repetida
    Then o worker usa os padrões atuais (resumos ligados com mínimo 3, cabeçalhos #, ## e ###, batch_size 50 e sync_mode append) e o resultado não muda
```

#### AC-007 — Frontmatter do arquivo continua prevalecendo

**Cobre**: FR-001, FR-003, NFR-002

```gherkin
@FR-001 @FR-003 @NFR-002 @AC-007
Feature: Configurar o processamento pelo front

  Scenario: Frontmatter do arquivo continua prevalecendo
    Given um arquivo com `splitter: qa` e outro com `splitter: character` no frontmatter
    When a Prévia é calculada com a estratégia token
    Then o arquivo Q&A gera um chunk por par, o arquivo `character` mantém a divisão recursiva atual, e os dois aparecem em `arquivos_com_configuracao_propria`
```

#### AC-008 — Resumos de seção podem ser desligados

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-008
Feature: Configurar o processamento pelo front

  Scenario: Resumos de seção podem ser desligados
    Given um arquivo com uma seção que tem quatro subseções
    When a Prévia é calculada com resumos de seção desligados
    Then nenhum chunk tem `chunk_type` igual a `section_summary`
```

#### AC-009 — Mínimo de subseções controla os resumos

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-009
Feature: Configurar o processamento pelo front

  Scenario: Mínimo de subseções controla os resumos
    Given um arquivo com uma seção de duas subseções e outra de quatro
    When a Prévia é calculada com mínimo de 2 subseções e depois com estratégia recursive
    Then a primeira Prévia traz dois resumos, e com recursive o campo de resumos não se aplica e nenhum resumo é gerado
```

#### AC-010 — Mínimo útil altera os avisos de qualidade

**Cobre**: US-002, FR-005

```gherkin
@US-002 @FR-005 @AC-010
Feature: Configurar o processamento pelo front

  Scenario: Mínimo útil altera os avisos de qualidade
    Given um arquivo que gera um chunk com 50 caracteres úteis
    When a Prévia é calculada com mínimo útil 40 e depois com 60
    Then o aviso de chunk curto aparece só na segunda Prévia, sem bloquear a publicação
```

#### AC-011 — Status bloqueado tira documentos da indexação

**Cobre**: US-002, FR-005

```gherkin
@US-002 @FR-005 @AC-011
Feature: Configurar o processamento pelo front

  Scenario: Status bloqueado tira documentos da indexação
    Given dois arquivos, um com `status: rascunho` no frontmatter
    When a Prévia é calculada com o status bloqueado `rascunho`
    Then o arquivo em rascunho não gera chunks e aparece entre os documentos excluídos da Prévia
```

#### AC-012 — Valores de resumo e qualidade inválidos são recusados

**Cobre**: US-002, FR-004, FR-005

```gherkin
@US-002 @FR-004 @FR-005 @AC-012
Feature: Configurar o processamento pelo front

  Scenario: Valores de resumo e qualidade inválidos são recusados
    Given a etapa Divisão
    When a pessoa informa mínimo de subseções fora de 2 a 10, mínimo útil fora de 0 a 1000, status vazio, repetido ou com mais de 40 caracteres, ou mais de 20 status
    Then a API devolve 422 com a mensagem do campo e nada é calculado nem gravado
```

#### AC-013 — Publicação mostra os padrões do destino

**Cobre**: US-003, FR-006, NFR-003

```gherkin
@US-003 @FR-006 @NFR-003 @AC-013
Feature: Configurar o processamento pelo front

  Scenario: Publicação mostra os padrões do destino
    Given a etapa Publicação
    When ela abre
    Then batch_size aparece com 50 e sync_mode com append, e ao escolher mirror surge o aviso de que a repetição remove da coleção os chunks que deixarem de ser gerados
```

#### AC-014 — Destino escolhido chega à execução e à repetição

**Cobre**: US-003, FR-006, NFR-002

```gherkin
@US-003 @FR-006 @NFR-002 @AC-014
Feature: Configurar o processamento pelo front

  Scenario: Destino escolhido chega à execução e à repetição
    Given uma publicação com batch_size 20 e sync_mode mirror
    When o worker executa e depois a pessoa repete a execução
    Then a geração de embeddings usa lotes de 20, a sincronização usa mirror e a repetição reaproveita os dois valores guardados na Base
```

#### AC-015 — Destino inválido é recusado

**Cobre**: US-003, FR-006

```gherkin
@US-003 @FR-006 @AC-015
Feature: Configurar o processamento pelo front

  Scenario: Destino inválido é recusado
    Given a etapa Publicação
    When a pessoa publica com batch_size 0, batch_size acima de 500 ou sync_mode desconhecido
    Then a API devolve 422, nenhuma Base é criada e nenhum job é agendado
```

#### AC-016 — Ações da Prévia ficam no topo

**Cobre**: US-004, FR-007, FR-008, NFR-003

```gherkin
@US-004 @FR-007 @FR-008 @NFR-003 @AC-016
Feature: Configurar o processamento pelo front

  Scenario: Ações da Prévia ficam no topo
    Given uma Prévia com muitos chunks
    When a pessoa rola a lista
    Then Voltar, Próxima e o seletor de chunks por página ficam numa barra no topo da etapa, visível durante a rolagem e alcançável por teclado antes da lista
```

#### AC-017 — Seletor de chunks por página

**Cobre**: US-004, FR-007, FR-008

```gherkin
@US-004 @FR-007 @FR-008 @AC-017
Feature: Configurar o processamento pelo front

  Scenario: Seletor de chunks por página
    Given uma Prévia com 120 chunks
    When a pessoa escolhe 50 por página
    Then a lista mostra 50 chunks, a paginação passa a 3 páginas, a requisição envia `tamanho_pagina` 50 e a barra continua no topo
```

#### AC-018 — Trocar o tamanho da página preserva o contexto

**Cobre**: US-004, FR-007, FR-008

```gherkin
@US-004 @FR-007 @FR-008 @AC-018
Feature: Configurar o processamento pelo front

  Scenario: Trocar o tamanho da página preserva o contexto
    Given uma Prévia na página 3 filtrada por um documento
    When a pessoa escolhe 100 por página
    Then a Prévia volta à página 1 mantendo o filtro, só existem as opções 10, 20, 50, 75 e 100, e um erro de cálculo preserva as escolhas de divisão
```

#### AC-019 — Qdrant sem a chave exigida é salvo com teste falho

**Cobre**: US-005, FR-009, NFR-001

```gherkin
@US-005 @FR-009 @NFR-001 @AC-019
Feature: Configurar o processamento pelo front

  Scenario: Qdrant sem a chave exigida é salvo com teste falho
    Given um Qdrant que responde 401 sem chave de API
    When a pessoa cadastra uma conexão Qdrant sem chave
    Then a conexão é salva, a resposta traz o teste com sucesso falso e o motivo 'O servidor exige uma chave de API', e nenhum segredo aparece na resposta nem nos logs
```

#### AC-020 — Embeddings válidos passam no teste e a dimensão é conferida

**Cobre**: US-005, FR-009, NFR-001

```gherkin
@US-005 @FR-009 @NFR-001 @AC-020
Feature: Configurar o processamento pelo front

  Scenario: Embeddings válidos passam no teste e a dimensão é conferida
    Given um provedor de embeddings que devolve vetores de 1536 posições
    When a pessoa cadastra uma conexão declarando 1536 e depois edita para 3072
    Then o primeiro teste tem sucesso com dimensão 1536, o segundo falha com 'O modelo devolveu 1536 dimensões; a conexão declara 3072', e a chave não aparece na resposta nem nos logs
```

#### AC-021 — Servidor inalcançável falha dentro do tempo limite

**Cobre**: US-005, FR-009, NFR-001

```gherkin
@US-005 @FR-009 @NFR-001 @AC-021
Feature: Configurar o processamento pelo front

  Scenario: Servidor inalcançável falha dentro do tempo limite
    Given uma URL de Qdrant que não responde
    When a pessoa salva a conexão
    Then a conexão é salva em até 15 segundos, o teste falha com 'Não foi possível alcançar o servidor' e nenhuma exceção vaza a chave
```

#### AC-022 — Cadastrar conexão sem sair da Publicação

**Cobre**: US-005, FR-010, NFR-003

```gherkin
@US-005 @FR-010 @NFR-003 @AC-022
Feature: Configurar o processamento pelo front

  Scenario: Cadastrar conexão sem sair da Publicação
    Given a etapa Publicação sem conexão de embeddings ativa e com arquivos e divisão já escolhidos
    When a pessoa aciona Cadastrar conexão, preenche o painel lateral e salva com teste bem-sucedido
    Then o painel fecha, a nova conexão aparece selecionada, a mensagem 'Conexão testada com sucesso' é anunciada e arquivos, divisão e Prévia continuam na tela
```

#### AC-023 — Cancelar ou falhar no painel não perde o fluxo

**Cobre**: US-005, FR-009, FR-010

```gherkin
@US-005 @FR-009 @FR-010 @AC-023
Feature: Configurar o processamento pelo front

  Scenario: Cancelar ou falhar no painel não perde o fluxo
    Given o painel de nova conexão aberto na Publicação
    When a pessoa cancela, ou salva e o teste falha
    Then cancelar fecha o painel sem alterar nada; com falha o painel continua aberto informando que a conexão foi salva e o motivo, e ao fechar a conexão fica disponível na lista com o aviso de teste falho
```

#### AC-024 — Seletores legíveis no tema escuro

**Cobre**: US-001, FR-011, NFR-003

```gherkin
@US-001 @FR-011 @NFR-003 @AC-024
Feature: Configurar o processamento pelo front

  Scenario: Seletores legíveis no tema escuro
    Given o tema escuro
    When a pessoa abre o seletor de estratégia na Divisão e os seletores de conexão e de sync_mode na Publicação
    Then cada opção usa as cores de popover do tema, com texto e fundo contrastantes
```

#### AC-025 — Seletores legíveis no tema claro e por teclado

**Cobre**: FR-011, NFR-003

```gherkin
@FR-011 @NFR-003 @AC-025
Feature: Configurar o processamento pelo front

  Scenario: Seletores legíveis no tema claro e por teclado
    Given o tema claro
    When a pessoa navega pelas opções dos seletores com as setas do teclado
    Then as opções continuam legíveis e a escolha muda o valor do campo
```

#### AC-026 — O painel da Publicação usa o formulário de Conexões

**Cobre**: US-005, FR-009, FR-010

```gherkin
@US-005 @FR-009 @FR-010 @AC-026
Feature: Configurar o processamento pelo front

  Scenario: O painel da Publicação usa o formulário de Conexões
    Given a etapa Publicação
    When a pessoa abre Cadastrar conexão
    Then o painel é o mesmo `ConexaoFormSheet` da tela Conexões, com os mesmos campos, validações e exibição do resultado do teste
```

#### AC-027 — Markdown recursivo dividindo por cabeçalhos

**Cobre**: US-001, FR-001, FR-002, FR-004

```gherkin
@US-001 @FR-001 @FR-002 @FR-004 @AC-027
Feature: Configurar o processamento pelo front

  Scenario: Markdown recursivo dividindo por cabeçalhos
    Given um arquivo com títulos de H1 a H5 e trechos longos sob cada título
    When a Prévia é calculada com a estratégia markdown, tamanho 500 e Dividir por cabeçalhos até H4, e depois com Desativado
    Then na primeira nenhum chunk cruza um título de H1 a H4, cada chunk respeita o tamanho e o breadcrumb mostra até o quarto nível; na segunda a divisão segue só o MarkdownTextSplitter, sem breadcrumb
```

#### AC-028 — Separador personalizado no Por caractere

**Cobre**: US-001, FR-002

```gherkin
@US-001 @FR-002 @AC-028
Feature: Configurar o processamento pelo front

  Scenario: Separador personalizado no Por caractere
    Given um arquivo com blocos separados por linhas contendo três hífens
    When a Prévia é calculada com a estratégia character_split, separador `\n---\n` e tamanho 300
    Then os chunks se formam a partir dos blocos separados por `---`, a sequência `\n` é interpretada como quebra de linha e um separador vazio é recusado com 422
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve aceitar na Prévia e na publicação as estratégias `header` (`MarkdownHeaderTextSplitter` com divisão recursiva dos trechos longos e breadcrumb, como hoje), `markdown` (`MarkdownTextSplitter`, opcionalmente dividindo antes nos cabeçalhos até o nível escolhido, como o Split by Headers do Flowise), `markdown_syntax` (`ExperimentalMarkdownSyntaxTextSplitter`), `recursive` (`RecursiveCharacterTextSplitter`), `character_split` (`CharacterTextSplitter`) e `token` (`TokenTextSplitter`), mantendo `qa` e `character` (recursivo) como valores válidos apenas no frontmatter, que continua prevalecendo sobre o formulário.
- **FR-002**: O sistema deve exigir e validar, para cada estratégia, somente os seus campos: tamanho de 200 a 4000 caracteres e overlap de 0 até a metade para `header`, `markdown`, `recursive` e `character_split`; separador personalizado em campo livre de 1 a 10 caracteres para `character_split`, aceitando `\n` e `\t` como quebra de linha e tabulação (padrão parágrafo, `\n\n`); encoding `cl100k_base` ou `o200k_base`, tamanho de 50 a 2000 tokens e overlap de 0 até a metade para `token`; Dividir por cabeçalhos com um seletor de nível máximo de H1 a H6 para `header` e `markdown_syntax` (padrão H3) e de Desativado ou H1 a H6 para `markdown` (padrão Desativado); e a opção de remover cabeçalhos do texto para `markdown_syntax`; com erro em linha na tela e 422 na API.
- **FR-003**: O sistema deve receber as escolhas no campo opcional `processamento` (JSON) da Prévia e da publicação, guardá-las em `bases.chunking` junto de `splitter`, `chunk_size` e `chunk_overlap`, e montar a mesma configuração para a Prévia, a execução e a repetição; sem o campo, valem os padrões atuais.
- **FR-004**: O sistema deve permitir ligar ou desligar os resumos de seção (padrão ligado) e escolher o mínimo de subseções de 2 a 10 (padrão 3), aplicáveis só às estratégias `header` e `markdown_syntax`, e dividir nos cabeçalhos até o nível escolhido, com os metadados `titulo`, `secao`, `subsecao`, `nivel_4`, `nivel_5` e `nivel_6`; o breadcrumb mostra os níveis presentes até o escolhido, e os resumos continuam agrupados por título e seção.
- **FR-005**: O sistema deve permitir definir o mínimo útil de 0 a 1000 caracteres (padrão 60), que só gera avisos na Prévia, e até 20 status bloqueados de 1 a 40 caracteres sem repetição (padrão nenhum), excluindo da Prévia e da execução os documentos cujo `status` do frontmatter esteja na lista e informando-os na Prévia.
- **FR-006**: O sistema deve permitir escolher na Publicação `batch_size` de 1 a 500 (padrão 50) e `sync_mode` `append` ou `mirror` (padrão `append`), mostrar um aviso sobre o efeito do `mirror` na repetição, guardar os valores na Base e aplicá-los na execução e na repetição, recusando valores inválidos com 422 sem criar Base nem agendar job.
- **FR-007**: O sistema deve exibir Voltar, Próxima e o seletor de chunks por página numa barra no topo da etapa Prévia, fixa durante a rolagem e anterior à lista na ordem de foco.
- **FR-008**: O sistema deve oferecer na Prévia as quantidades 10, 20, 50, 75 e 100 chunks por página (padrão 10), enviar a escolha como `tamanho_pagina`, voltar à página 1 ao trocar e preservar o filtro por documento.
- **FR-009**: O sistema deve, ao criar ou editar uma conexão, testar o acesso em até 15 segundos (Qdrant: listagem de coleções com a chave; embeddings: um embedding curto conferindo a dimensão declarada), salvar a conexão mesmo se o teste falhar e devolver na resposta `teste` com `sucesso`, `mensagem` e, para embeddings, `dimensoes`.
- **FR-010**: O sistema deve oferecer na etapa Publicação a ação Cadastrar conexão, que abre o mesmo `ConexaoFormSheet` da tela Conexões; ao salvar, recarregar as conexões, selecionar a nova conexão no campo do tipo dela e preservar arquivos, divisão e Prévia.
- **FR-011**: O sistema deve exibir as opções dos seletores nativos das etapas Divisão e Publicação e do formulário de conexão com as cores de popover do tema, legíveis nos temas claro e escuro.

#### Não funcionais

- **NFR-001**: Segurança dos segredos no teste: a chave não aparece na resposta, nos logs, nem nas mensagens de erro do teste, e o teste não cria coleção nem grava pontos. **Verificação**: AC-019, AC-020 e AC-021 com chave conhecida e captura de logs.
- **NFR-002**: Compatibilidade: Bases anteriores e arquivos com configuração própria no frontmatter mantêm o resultado, e a repetição reaproveita as escolhas guardadas. **Verificação**: AC-006, AC-007 e AC-014 mais a regressão completa.
- **NFR-003**: Acessibilidade e legibilidade: campos com rótulo associado, ordem de foco com a barra antes da lista, aviso e resultado de teste anunciados por `aria-live`, e opções com contraste de pelo menos 4,5:1 nos dois temas. **Verificação**: AC-003, AC-013, AC-016, AC-022, AC-024 e AC-025 mais a revisão visual da tarefa T036.

#### Erros e casos-limite

- Estratégia de token sem acesso aos arquivos de encoding do `tiktoken` → a Prévia devolve erro claro e a publicação é bloqueada.
- Arquivo cujo `status` está bloqueado em uma publicação de arquivo único → a Prévia avisa que nenhum documento restou e Próxima fica desabilitada.
- Mínimo de subseções em estratégia sem cabeçalhos → o campo fica oculto e é ignorado.
- Teste de conexão com resposta 401 ou 403 → "O servidor exige uma chave de API" ou "O servidor recusou a chave informada".
- Teste de conexão com DNS, recusa ou tempo esgotado → "Não foi possível alcançar o servidor".
- Teste de embeddings com dimensão diferente → "O modelo devolveu N dimensões; a conexão declara M".
- Edição de conexão sem reenviar a chave → o teste usa a chave guardada.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI com SQLAlchemy, worker procrastinate e pipeline em `src/pipeline/` acessado só pela fachada `src.pipeline.service` (`.specsfy/STACK.md`).
- Frontend Next.js com React, Tailwind CSS, shadcn/ui e ReUI; testes com Vitest (`npm run test:tdd`) e Testing Library (`INTERFACE.md`).
- `bases.chunking` é JSON e hoje guarda `splitter`, `chunk_size` e `chunk_overlap` (SPEC-0026).

#### Arquitetura e módulos

- `src/pipeline/chunker.py`: despacho por estratégia com as seis opções, aceitando `headers_to_split_on` (derivado do nível máximo, de H1 a H6), `separator`, `encoding_name` e `strip_headers` na seção `chunking`; o breadcrumb passa a incluir `nivel_4` a `nivel_6` quando presentes; `character` do frontmatter continua recursivo.
- `src/pipeline/service.py`: `testar_conexao(tipo, configuracao)` na fachada, com tempo limite de 15 segundos, sem criar coleção, devolvendo sucesso, mensagem sanitizada e dimensão.
- `src/app/ingestao.py`: padrões e limites novos, `validar_processamento(dados)` e `montar_configuracao(processamento)` que devolve as seções `chunking`, `qualidade`, `contrato_markdown` e os ajustes de `embedding.batch_size` e `vector_store.sync_mode`.
- `src/app/routers/ingestao.py`: `GET /padroes` passa a devolver estratégias, campos por estratégia, padrões e limites novos; `POST /previa` aceita `processamento` e informa documentos excluídos por status.
- `src/app/routers/bases.py`: a publicação aceita `processamento`, valida e guarda em `bases.chunking`.
- `src/app/tasks.py`: `_configuracao_da_base` monta as seções a partir de `bases.chunking`, com padrões para chaves ausentes.
- `src/app/routers/conexoes.py` e `src/app/conexoes.py`: POST e PATCH chamam o teste depois de gravar e devolvem `teste`.

#### Migrations

- Não aplicável: `bases.chunking` já é JSON; as chaves novas são opcionais (DEC-001).

#### Models

- `Base.chunking` (`src/app/models.py`) passa a conter, além de `splitter`, `chunk_size` e `chunk_overlap`, as chaves opcionais `opcoes`, `resumos`, `qualidade`, `contrato` e `destino`.

#### Controllers e casos de uso

- `GET /api/v1/ingestao/padroes`, `POST /api/v1/ingestao/previa`, `POST /api/v1/bases` (publicação), `POST /api/v1/conexoes` e `PATCH /api/v1/conexoes/{id}`; autorização de escrita (owner e admin) inalterada.

#### Views e experiência

- Etapa Divisão, etapa Prévia, etapa Publicação e `ConexaoFormSheet`, detalhadas na seção 10.

#### Queries e repositórios

- Sem mudança em `src/app/repo.py`.

#### Jobs e processamento assíncrono

- `process_base_task` continua recebendo só identificadores; as escolhas vêm de `bases.chunking`, então a repetição as reaproveita sem argumento novo na fila.

#### Estrutura de arquivos

```text
specs/draft/0029-expor-configuracoes-do-processamento-no-front/
  spec.md
src/
  pipeline/chunker.py
  pipeline/service.py
  app/ingestao.py
  app/tasks.py
  app/conexoes.py
  app/routers/ingestao.py
  app/routers/bases.py
  app/routers/conexoes.py
frontend/src/
  lib/ingestao.ts
  features/ingestao/FluxoIngestao.tsx
  features/ingestao/useFluxoIngestao.ts
  features/ingestao/EtapaDivisao.tsx
  features/ingestao/EtapaPrevia.tsx
  features/ingestao/EtapaPublicacao.tsx
  features/conexoes/ConexaoFormSheet.tsx
tests/
  test_app_ingestao_estrategias.py
  test_app_conexoes_teste.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Base | `id` | `chunking` JSON: `splitter`, `chunk_size`, `chunk_overlap` e as chaves opcionais `opcoes` (`nivel_cabecalho` de 0 a 6, em que 0 é Desativado, `separador`, `encoding`, `remover_cabecalhos`), `resumos` (`ativo`, `minimo_subsecoes`), `qualidade` (`minimo_util`), `contrato` (`status_bloqueado`) e `destino` (`batch_size`, `sync_mode`) | pertence a um Workspace; referencia até duas Conexões |
| Conexão | `id` | sem mudança de schema; o resultado do teste não é guardado | usada por Bases |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Base | inexistente | publicação válida | publicada com `chunking` completo | nada é gravado antes de publicar |
| Conexão | inexistente ou ativa | salvar com teste falho | ativa | salvar não depende do resultado do teste |

#### Migração e retenção

- Não aplicável: chaves ausentes em `bases.chunking` usam os padrões atuais, então Bases anteriores não precisam de migração.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim.

#### Stack e convenções de interface

- Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui e ReUI, testes Vitest com Testing Library (`INTERFACE.md`, `frontend/package.json`).
- Telas preservadas: Nova Base em quatro etapas (`/workspaces/[id]/bases/nova`), Conexões (`/conexoes`) com `DataGridConexoes` e `ConexaoFormSheet`.
- O que muda: campos da etapa Divisão, barra e paginação da Prévia, campos de destino e ação Cadastrar conexão na Publicação, resultado do teste no `ConexaoFormSheet`, contraste dos seletores.

#### Telas e responsabilidades

- **Nova Base, etapa Divisão**: owner e admin escolhem estratégia e campos, resumos, cabeçalhos e Qualidade; saída: parâmetros validados.
- **Nova Base, etapa Prévia**: revisar chunks e avisos com tamanho de página escolhido; saída: decisão de voltar ou seguir.
- **Nova Base, etapa Publicação**: escolher conexões, coleção e destino, cadastrar conexão sem sair; saída: Base publicada.
- **Conexões**: criar e editar conexões, agora com resultado do teste.

#### Fluxo de informação e navegação

- A pessoa chega à Nova Base pelo Workspace, percorre Arquivos → Divisão → Prévia → Publicação e pode voltar a qualquer etapa anterior sem perder escolhas. Na Publicação, Cadastrar conexão abre o painel por cima da etapa e devolve a pessoa ao mesmo ponto.
- Breadcrumb: Equipe / Workspaces / <Workspace> / Nova Base, inalterado.

#### Menus e navegação principal

- Menu principal inalterado: Workspaces, Pessoas e Conexões (este para owner e admin). Nenhum item novo.

#### Formulários e ações

- **Divisão**: Estratégia de divisão (seletor com as seis opções e rótulos: Markdown por cabeçalhos, Markdown recursivo, Markdown sintático, Recursivo por caracteres, Por caractere, Por tokens); campos conforme FR-002; bloco Resumos (interruptor e mínimo de subseções) só para cabeçalhos e Markdown sintático; Dividir por cabeçalhos como seletor de nível máximo (H1 a H6, e Desativado em Markdown recursivo); separador personalizado em campo livre no Por caractere; bloco Qualidade recolhível com mínimo útil e status bloqueados (campo de inclusão com lista removível); validação em linha.
- **Prévia**: barra no topo com Voltar, Próxima e o seletor de chunks por página; documentos excluídos por status listados nos avisos.
- **Publicação**: bloco Avançado recolhido com `batch_size` e `sync_mode` e aviso do `mirror`; ação Cadastrar conexão ao lado dos seletores de conexão.
- **ConexaoFormSheet**: depois de salvar, mostra o resultado do teste; sucesso fecha o painel e a tela de origem anuncia "Conexão testada com sucesso"; falha mantém o painel aberto com "Conexão salva, mas o teste falhou: <motivo>" e as ações Editar e Fechar.

#### Composição e disposição

- Etapas em coluna única dentro do card do fluxo; campos em grade de duas colunas no desktop e uma coluna abaixo de 640px; a barra da Prévia é `sticky` no topo do card; o painel de conexão é o `Sheet` lateral existente.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Divisão | `EtapaDivisao` | estratégia, campos próprios, resumos, cabeçalhos e Qualidade | `frontend/src/features/ingestao/EtapaDivisao.tsx` | `Input`, `Label`, `Alert`, `Button`, `select` e checkbox nativos | shadcn/ui e próprio | extensão do bloco existente; sem `Switch` e `Collapsible` no projeto, usados checkbox nativo e botão com `aria-expanded` |
| Divisão | `ingestao` (lib) | rótulos, padrões e validação por estratégia | `frontend/src/lib/ingestao.ts` | utilitário | próprio | extensão |
| Fluxo | `useFluxoIngestao` | estado de processamento e tamanho de página | `frontend/src/features/ingestao/useFluxoIngestao.ts` | hook | próprio | extensão |
| Prévia | `FluxoIngestao` | barra de ações no topo | `frontend/src/features/ingestao/FluxoIngestao.tsx` | `Button` | shadcn/ui | extensão |
| Prévia | `EtapaPrevia` | seletor de chunks por página e avisos de exclusão | `frontend/src/features/ingestao/EtapaPrevia.tsx` | `Badge`, `Button`, `select` nativo | shadcn/ui e próprio | extensão |
| Publicação | `EtapaPublicacao` | destino, aviso do mirror e Cadastrar conexão | `frontend/src/features/ingestao/EtapaPublicacao.tsx` | `Input`, `Label`, `Alert`, `Button`, `select` nativo | shadcn/ui e próprio | extensão; bloco Avançado com botão `aria-expanded` |
| Divisão, Prévia, Publicação e Conexões | `seletor` | classe do select nativo legível nos dois temas | `frontend/src/features/ingestao/seletor.ts` | utilitário de estilo | próprio | novo, compartilhado |
| Publicação e Conexões | `ConexaoFormSheet` | criar, editar e mostrar o resultado do teste | `frontend/src/features/conexoes/ConexaoFormSheet.tsx` | `Sheet`, `Alert` | shadcn/ui | reaproveitado, estendido |

- Nenhuma composição ReUI nova: as etapas não são CRUD de lista. `INTERFACE.md` recebe os blocos estendidos na tarefa T035.

#### Estados e acessibilidade

- Loading: `IndicadorProcessamento` ao calcular a Prévia, ao salvar e testar a conexão e ao publicar.
- Vazio: Prévia sem documentos restantes após o filtro de status mostra aviso e desabilita Próxima.
- Erro: mensagens em linha nos campos; erro da API em `Alert`; teste falho no painel.
- Sucesso: "Conexão testada com sucesso" anunciado por `aria-live="polite"`.
- Permissão insuficiente: fluxo e Conexões continuam restritos a owner e admin.
- Teclado: barra da Prévia antes da lista na ordem de foco; painel com foco preso e retorno ao gatilho; seletores operáveis por setas.

#### Contrato CRUD

- O CRUD de Conexões existente é preservado: o mesmo `PageHeader` reutilizável na lista e no detalhe, a listagem em `DataGrid` (`DataGridConexoes`) em largura total com a coluna `ID` visível, a linha inteira como link para o detalhe e as ações independentes de editar e apagar, com confirmação antes de apagar.
- Esta entrega só estende o `ConexaoFormSheet` (criação e edição) com o resultado do teste; o painel reaproveitado na Publicação é o mesmo componente.
- `INTERFACE.md` registra o `ConexaoFormSheet` estendido e seus dois consumidores (tela Conexões e etapa Publicação).

#### Revisão visual durante o desenvolvimento

- A revisão visual acontece nas tarefas T031 a T034 e em T036, mesmo sem pedido, conferindo bordas, espaçamentos, margens, padding e tipografia nos temas claro e escuro, em 1280px e 390px, com conteúdo curto e longo.

#### APIs expostas

- `GET /api/v1/ingestao/padroes`: acrescenta `estrategias` (valor, rótulo e campos), padrões e limites de `opcoes`, `resumos`, `qualidade`, `contrato` e `destino`.
- `POST /api/v1/ingestao/previa`: aceita o campo de formulário opcional `processamento` (JSON) e devolve `documentos_excluidos`.
- `POST /api/v1/bases` (publicação): aceita `processamento`; 422 para valores inválidos.
- `POST /api/v1/conexoes` e `PATCH /api/v1/conexoes/{id}`: a resposta acrescenta `teste` com `sucesso`, `mensagem` e `dimensoes` (embeddings).

#### APIs externas utilizadas

- Qdrant: listagem de coleções no teste, com a chave quando houver; tempo limite de 15 segundos; sem retry.
- Provedor de embeddings compatível com OpenAI: um embedding curto no teste; tempo limite de 15 segundos; sem retry.

#### Documentação das APIs consultadas

- Nenhuma documentação externa; os contratos vêm do código local e do pacote instalado.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: validação de `processamento`, montagem da configuração e despacho por estratégia.
- **Integração/contrato**: endpoints de padrões, Prévia, publicação e conexões com Postgres de teste e a fachada de teste de conexão substituída por um falso; worker com `process_base_task`.
- **BDD/aceite**: o Gherkin da seção 6 orienta os testes; não há arquivos `.feature`.
- **Runner TDD**: backend com Pytest (`uv run pytest`) e Ruff; frontend com Vitest (`npm run test:tdd` em `frontend/`).
- **E2E**: Não aplicável como automação; a jornada é conferida pelo front em T036.
- **Verificação manual**: conferência visual e funcional no stack local, inevitável para contraste e rolagem.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, US-002, FR-001, FR-004, AC-001 | AC-001 na seção 6 | `test_previa_divide_so_nos_niveis_de_cabecalho_escolhidos` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-001 US-002 FR-001 FR-004 AC-001` | RED 2026-10-08: o campo `processamento` é ignorado e a divisão quebra em ### | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-001, FR-001, FR-002, AC-002 | AC-002 na seção 6 | `test_previa_aceita_as_seis_estrategias` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-001 FR-001 FR-002 AC-002` | RED 2026-10-08: 422 'Splitter desconhecido' para markdown, markdown_syntax, character_split e token | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-001, FR-002, FR-011, NFR-003, AC-003 | AC-003 na seção 6 | `mostra só os campos da estratégia escolhida` em frontend/src/features/ingestao/EtapaDivisao.test.tsx com marcador próprio `SPECSFY: SPEC-0029 US-001 FR-002 FR-011 NFR-003 AC-003` | RED 2026-10-08: o seletor só oferece duas estratégias e não existem os campos Separador, Encoding e Dividir por cabeçalhos | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-001, FR-002, FR-003, AC-004 | AC-004 na seção 6 | `test_previa_recusa_parametros_de_divisao_invalidos` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-001 FR-002 FR-003 AC-004` | RED 2026-10-08: nível de cabeçalho 7 e 0 aceitos com 200; os demais casos recusados hoje só por estratégia desconhecida | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-001, US-003, FR-003, FR-006, AC-005 | AC-005 na seção 6 | `test_publicacao_guarda_escolhas_e_execucao_repete_a_previa` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-001 US-003 FR-003 FR-006 AC-005` | RED 2026-10-08: 422 para a estratégia markdown na publicação; a Base não guarda resumos nem destino | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-001, FR-003, NFR-002, AC-006 | AC-006 na seção 6 | `test_base_anterior_repete_com_os_padroes_atuais` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-001 FR-003 NFR-002 AC-006` | RED 2026-10-08: caracterização: passa antes da mudança porque descreve o comportamento atual que deve ser preservado | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| FR-001, FR-003, NFR-002, AC-007 | AC-007 na seção 6 | `test_frontmatter_prevalece_sobre_a_estrategia_do_formulario` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 FR-001 FR-003 NFR-002 AC-007` | RED 2026-10-08: 422 'Splitter desconhecido' para a estratégia token | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-002, FR-004, AC-008 | AC-008 na seção 6 | `test_previa_sem_resumos_de_secao` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-002 FR-004 AC-008` | RED 2026-10-08: resumos sempre ligados: `section_summary` presente com `ativo` falso | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-002, FR-004, AC-009 | AC-009 na seção 6 | `test_minimo_de_subsecoes_controla_os_resumos` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-002 FR-004 AC-009` | RED 2026-10-08: mínimo de subseções ignorado: 1 resumo em vez de 2 | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-002, FR-005, AC-010 | AC-010 na seção 6 | `test_minimo_util_altera_os_avisos_da_previa` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-002 FR-005 AC-010` | RED 2026-10-08: a Prévia não traz aviso de conteúdo útil abaixo do mínimo | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-002, FR-005, AC-011 | AC-011 na seção 6 | `test_status_bloqueado_exclui_documentos` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-002 FR-005 AC-011` | RED 2026-10-08: status bloqueado ignorado: o arquivo em rascunho gera chunks e não há `documentos_excluidos` | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-002, FR-004, FR-005, AC-012 | AC-012 na seção 6 | `test_recusa_resumos_e_qualidade_invalidos` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-002 FR-004 FR-005 AC-012` | RED 2026-10-08: valores inválidos de resumos e qualidade aceitos com 200 | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-003, FR-006, NFR-003, AC-013 | AC-013 na seção 6 | `mostra os padrões do destino e o aviso do mirror` em frontend/src/features/ingestao/EtapaPublicacao.test.tsx com marcador próprio `SPECSFY: SPEC-0029 US-003 FR-006 NFR-003 AC-013` | RED 2026-10-08: não existe o bloco Avançado com tamanho do lote e modo de sincronização | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-003, FR-006, NFR-002, AC-014 | AC-014 na seção 6 | `test_destino_escolhido_chega_ao_worker_e_a_repeticao` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-003 FR-006 NFR-002 AC-014` | RED 2026-10-08: `batch_size` ausente na configuração do worker | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-003, FR-006, AC-015 | AC-015 na seção 6 | `test_publicacao_recusa_destino_invalido` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-003 FR-006 AC-015` | RED 2026-10-08: destino inválido aceito com 201 | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-004, FR-007, FR-008, NFR-003, AC-016 | AC-016 na seção 6 | `mantém as ações da Prévia no topo` em frontend/src/features/ingestao/FluxoIngestao.test.tsx com marcador próprio `SPECSFY: SPEC-0029 US-004 FR-007 FR-008 NFR-003 AC-016` | RED 2026-10-08: não existe a barra 'Ações da Prévia' no topo | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-004, FR-007, FR-008, AC-017 | AC-017 na seção 6 | `troca a quantidade de chunks por página` em frontend/src/features/ingestao/EtapaPrevia.test.tsx com marcador próprio `SPECSFY: SPEC-0029 US-004 FR-007 FR-008 AC-017` | RED 2026-10-08: a paginação usa 10 fixo: não mostra 'Página 1 de 3' com 50 por página | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-004, FR-007, FR-008, AC-018 | AC-018 na seção 6 | `preserva filtro e escolhas ao trocar o tamanho da página` em frontend/src/features/ingestao/FluxoIngestao.test.tsx com marcador próprio `SPECSFY: SPEC-0029 US-004 FR-007 FR-008 AC-018` | RED 2026-10-08: não existe o seletor 'Chunks por página' | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-005, FR-009, NFR-001, AC-019 | AC-019 na seção 6 | `test_qdrant_sem_chave_salva_com_teste_falho` em tests/test_app_conexoes_teste.py com marcador próprio `SPECSFY: SPEC-0029 US-005 FR-009 NFR-001 AC-019` | RED 2026-10-08: a resposta da criação não traz `teste` | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-005, FR-009, NFR-001, AC-020 | AC-020 na seção 6 | `test_embeddings_testa_e_confere_dimensao` em tests/test_app_conexoes_teste.py com marcador próprio `SPECSFY: SPEC-0029 US-005 FR-009 NFR-001 AC-020` | RED 2026-10-08: a resposta da criação e da edição não traz `teste` | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-005, FR-009, NFR-001, AC-021 | AC-021 na seção 6 | `test_servidor_inalcancavel_falha_no_tempo_limite` em tests/test_app_conexoes_teste.py com marcador próprio `SPECSFY: SPEC-0029 US-005 FR-009 NFR-001 AC-021` | RED 2026-10-08: a resposta da criação não traz `teste` | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-005, FR-010, NFR-003, AC-022 | AC-022 na seção 6 | `cadastra conexão no painel sem sair da Publicação` em frontend/src/features/ingestao/EtapaPublicacao.test.tsx com marcador próprio `SPECSFY: SPEC-0029 US-005 FR-010 NFR-003 AC-022` | RED 2026-10-08: não existe o botão Cadastrar conexão na Publicação | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-005, FR-009, FR-010, AC-023 | AC-023 na seção 6 | `cancelar ou falhar no painel preserva o fluxo` em frontend/src/features/ingestao/EtapaPublicacao.test.tsx com marcador próprio `SPECSFY: SPEC-0029 US-005 FR-009 FR-010 AC-023` | RED 2026-10-08: não existe o botão Cadastrar conexão na Publicação | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-001, FR-011, NFR-003, AC-024 | AC-024 na seção 6 | `usa as cores de popover nas opções dos seletores` em frontend/src/features/ingestao/EtapaDivisao.test.tsx com marcador próprio `SPECSFY: SPEC-0029 US-001 FR-011 NFR-003 AC-024` | RED 2026-10-08: não existe o seletor Dividir por cabeçalhos e as opções não usam as cores de popover | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| FR-011, NFR-003, AC-025 | AC-025 na seção 6 | `seletores funcionam no tema claro e por teclado` em frontend/src/features/ingestao/EtapaDivisao.test.tsx com marcador próprio `SPECSFY: SPEC-0029 FR-011 NFR-003 AC-025` | RED 2026-10-08: a opção token não existe no seletor de estratégia | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-005, FR-009, FR-010, AC-026 | AC-026 na seção 6 | `reaproveita o formulário de conexões no painel` em frontend/src/features/ingestao/EtapaPublicacao.test.tsx com marcador próprio `SPECSFY: SPEC-0029 US-005 FR-009 FR-010 AC-026` | RED 2026-10-08: não existe o botão Cadastrar conexão na Publicação | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-001, FR-001, FR-002, FR-004, AC-027 | AC-027 na seção 6 | `test_markdown_recursivo_divide_por_cabecalhos` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-001 FR-001 FR-002 FR-004 AC-027` | RED 2026-10-08: 422 'Splitter desconhecido' para a estratégia markdown | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |
| US-001, FR-002, AC-028 | AC-028 na seção 6 | `test_separador_personalizado_no_por_caractere` em tests/test_app_ingestao_estrategias.py com marcador próprio `SPECSFY: SPEC-0029 US-001 FR-002 AC-028` | RED 2026-10-08: 422 'Splitter desconhecido' para a estratégia character_split | GREEN 2026-10-09: `uv run pytest -q` (542 passed) e `npx vitest run` (229 passed) | Regressão 2026-10-09 sem falhas; ruff, lint e build ok |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_previa_divide_so_nos_niveis_de_cabecalho_escolhidos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-001 | AC-002 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_previa_aceita_as_seis_estrategias -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-001 | AC-007 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_frontmatter_prevalece_sobre_a_estrategia_do_formulario -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-002 | AC-002 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_previa_aceita_as_seis_estrategias -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-002 | AC-003 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaDivisao.test.tsx -t "mostra só os campos da estratégia escolhida"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-002 | AC-004 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_previa_recusa_parametros_de_divisao_invalidos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-003 | AC-004 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_previa_recusa_parametros_de_divisao_invalidos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-003 | AC-005 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_publicacao_guarda_escolhas_e_execucao_repete_a_previa -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-003 | AC-006 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_base_anterior_repete_com_os_padroes_atuais -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-003 | AC-007 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_frontmatter_prevalece_sobre_a_estrategia_do_formulario -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-004 | AC-001 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_previa_divide_so_nos_niveis_de_cabecalho_escolhidos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-004 | AC-008 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_previa_sem_resumos_de_secao -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-004 | AC-009 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_minimo_de_subsecoes_controla_os_resumos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-004 | AC-012 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_recusa_resumos_e_qualidade_invalidos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-005 | AC-010 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_minimo_util_altera_os_avisos_da_previa -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-005 | AC-011 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_status_bloqueado_exclui_documentos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-005 | AC-012 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_recusa_resumos_e_qualidade_invalidos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-006 | AC-005 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_publicacao_guarda_escolhas_e_execucao_repete_a_previa -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-006 | AC-013 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx -t "mostra os padrões do destino e o aviso do mirror"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-006 | AC-014 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_destino_escolhido_chega_ao_worker_e_a_repeticao -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-006 | AC-015 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_publicacao_recusa_destino_invalido -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-007 | AC-016 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/FluxoIngestao.test.tsx -t "mantém as ações da Prévia no topo"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-007 | AC-017 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaPrevia.test.tsx -t "troca a quantidade de chunks por página"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-007 | AC-018 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/FluxoIngestao.test.tsx -t "preserva filtro e escolhas ao trocar o tamanho da página"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-008 | AC-016 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/FluxoIngestao.test.tsx -t "mantém as ações da Prévia no topo"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-008 | AC-017 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaPrevia.test.tsx -t "troca a quantidade de chunks por página"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-008 | AC-018 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/FluxoIngestao.test.tsx -t "preserva filtro e escolhas ao trocar o tamanho da página"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-009 | AC-019 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_conexoes_teste.py::test_qdrant_sem_chave_salva_com_teste_falho -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-009 | AC-020 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_conexoes_teste.py::test_embeddings_testa_e_confere_dimensao -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-009 | AC-021 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_conexoes_teste.py::test_servidor_inalcancavel_falha_no_tempo_limite -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-009 | AC-023 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx -t "cancelar ou falhar no painel preserva o fluxo"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-009 | AC-026 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx -t "reaproveita o formulário de conexões no painel"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-010 | AC-022 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx -t "cadastra conexão no painel sem sair da Publicação"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-010 | AC-023 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx -t "cancelar ou falhar no painel preserva o fluxo"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-010 | AC-026 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx -t "reaproveita o formulário de conexões no painel"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-011 | AC-003 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaDivisao.test.tsx -t "mostra só os campos da estratégia escolhida"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-011 | AC-024 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaDivisao.test.tsx -t "usa as cores de popover nas opções dos seletores"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-011 | AC-025 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaDivisao.test.tsx -t "seletores funcionam no tema claro e por teclado"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-001 | AC-019 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_conexoes_teste.py::test_qdrant_sem_chave_salva_com_teste_falho -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-001 | AC-020 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_conexoes_teste.py::test_embeddings_testa_e_confere_dimensao -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-001 | AC-021 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_conexoes_teste.py::test_servidor_inalcancavel_falha_no_tempo_limite -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-002 | AC-006 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_base_anterior_repete_com_os_padroes_atuais -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-002 | AC-007 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_frontmatter_prevalece_sobre_a_estrategia_do_formulario -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-002 | AC-014 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_destino_escolhido_chega_ao_worker_e_a_repeticao -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-003 | AC-003 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaDivisao.test.tsx -t "mostra só os campos da estratégia escolhida"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-003 | AC-013 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx -t "mostra os padrões do destino e o aviso do mirror"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-003 | AC-016 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/FluxoIngestao.test.tsx -t "mantém as ações da Prévia no topo"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-003 | AC-022 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaPublicacao.test.tsx -t "cadastra conexão no painel sem sair da Publicação"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-003 | AC-024 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaDivisao.test.tsx -t "usa as cores de popover nas opções dos seletores"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| NFR-003 | AC-025 | Componente (Vitest, Testing Library) | `npm --prefix frontend run test:tdd -- src/features/ingestao/EtapaDivisao.test.tsx -t "seletores funcionam no tema claro e por teclado"` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-001 | AC-027 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_markdown_recursivo_divide_por_cabecalhos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-002 | AC-027 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_markdown_recursivo_divide_por_cabecalhos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-004 | AC-027 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_markdown_recursivo_divide_por_cabecalhos -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |
| FR-002 | AC-028 | Integração (Postgres de teste, fachada falsa) | `uv run pytest tests/test_app_ingestao_estrategias.py::test_separador_personalizado_no_por_caractere -v` | Passed 2026-10-09 (suíte completa e `check_traceability.mjs --full-chain` 47/47) |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (2026-10-08, revalidado após DEC-007)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0029-expor-configuracoes-do-processamento-no-front/spec.md`
- **Achados**: 0 BLOCKER; 1 WARNING aceito: limites numéricos e o comportamento do painel após o teste foram propostos pelo agente e seguem como suposições reversíveis na seção 16. A mudança DEC-007 (Dividir por cabeçalhos de H1 a H6 e separador livre) foi incorporada em FR-001, FR-002 e FR-004, com os novos AC-027 e AC-028. Cobertura: 5 US, 11 FR e 3 NFR, cada um com 3 ou mais AC (28 AC), e cada AC com tarefa TDD própria. DoD cita `.specsfy/DATABASE.md` e `INTERFACE.md`.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-08)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0029-expor-configuracoes-do-processamento-no-front/spec.md`
- **Achados**: 38 tarefas (28 de teste TDD, 8 de código, 1 de documentação e 1 de regressão); 47 de 47 IDs cobertos. RED observado em 28 de 28 casos, sendo AC-006 caracterização do comportamento atual. Backend: `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q` (30 failed, 10 passed); frontend: `npx vitest run src/features/ingestao` (10 failed, 21 passed). Banco de teste `SAFE`.

#### Gate do Ato III — Entrega

- **Resultado**: Passed (2026-10-09)
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0029-expor-configuracoes-do-processamento-no-front/spec.md .`
- **Achados**: 38/38 tarefas concluídas; rastreabilidade `--full-chain` 47/47 IDs; ruff limpo; pytest 542 passed e 1 skipped; vitest 229 passed; lint e build ok; publicação real com Prévia de 20 chunks e execução com 20 previstos e 20 inseridos; conferência visual sem ajustes.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 o caso `test_previa_divide_so_nos_niveis_de_cabecalho_escolhidos` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-001, US-002, FR-001, FR-004, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: o campo `processamento` é ignorado e a divisão quebra em ###.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 o caso `test_previa_aceita_as_seis_estrategias` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-001, FR-001, FR-002, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: 422 'Splitter desconhecido' para markdown, markdown_syntax, character_split e token.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 o caso `mostra só os campos da estratégia escolhida` falhando em frontend/src/features/ingestao/EtapaDivisao.test.tsx — Refs: US-001, FR-002, FR-011, NFR-003, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual acontece na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `npx vitest run src/features/ingestao (10 failed, 21 passed)`: o seletor só oferece duas estratégias e não existem os campos Separador, Encoding e Dividir por cabeçalhos.
  - [x] **IMPROVE**: Cobertura revisada; o caso acessa os símbolos novos de forma dinâmica para não quebrar os testes existentes do mesmo arquivo.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 o caso `test_previa_recusa_parametros_de_divisao_invalidos` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-001, FR-002, FR-003, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: nível de cabeçalho 7 e 0 aceitos com 200; os demais casos recusados hoje só por estratégia desconhecida.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 o caso `test_publicacao_guarda_escolhas_e_execucao_repete_a_previa` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-001, US-003, FR-003, FR-006, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: 422 para a estratégia markdown na publicação; a Base não guarda resumos nem destino.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-006 o caso `test_base_anterior_repete_com_os_padroes_atuais` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-001, FR-003, NFR-002, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: caracterização: passa antes da mudança porque descreve o comportamento atual que deve ser preservado.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T007 [TEST] [TDD] [US-001] Derivar do AC-007 o caso `test_frontmatter_prevalece_sobre_a_estrategia_do_formulario` falhando em tests/test_app_ingestao_estrategias.py — Refs: FR-001, FR-003, NFR-002, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: 422 'Splitter desconhecido' para a estratégia token.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 o caso `test_previa_sem_resumos_de_secao` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-002, FR-004, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: resumos sempre ligados: `section_summary` presente com `ativo` falso.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 o caso `test_minimo_de_subsecoes_controla_os_resumos` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-002, FR-004, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: mínimo de subseções ignorado: 1 resumo em vez de 2.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T010 [TEST] [TDD] [US-002] Derivar do AC-010 o caso `test_minimo_util_altera_os_avisos_da_previa` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-002, FR-005, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: a Prévia não traz aviso de conteúdo útil abaixo do mínimo.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T011 [TEST] [TDD] [US-002] Derivar do AC-011 o caso `test_status_bloqueado_exclui_documentos` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-002, FR-005, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: status bloqueado ignorado: o arquivo em rascunho gera chunks e não há `documentos_excluidos`.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T012 [TEST] [TDD] [US-002] Derivar do AC-012 o caso `test_recusa_resumos_e_qualidade_invalidos` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-002, FR-004, FR-005, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: valores inválidos de resumos e qualidade aceitos com 200.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-013 o caso `mostra os padrões do destino e o aviso do mirror` falhando em frontend/src/features/ingestao/EtapaPublicacao.test.tsx — Refs: US-003, FR-006, NFR-003, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual acontece na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `npx vitest run src/features/ingestao (10 failed, 21 passed)`: não existe o bloco Avançado com tamanho do lote e modo de sincronização.
  - [x] **IMPROVE**: Cobertura revisada; o caso acessa os símbolos novos de forma dinâmica para não quebrar os testes existentes do mesmo arquivo.

- [x] T014 [TEST] [TDD] [US-003] Derivar do AC-014 o caso `test_destino_escolhido_chega_ao_worker_e_a_repeticao` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-003, FR-006, NFR-002, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: `batch_size` ausente na configuração do worker.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T015 [TEST] [TDD] [US-003] Derivar do AC-015 o caso `test_publicacao_recusa_destino_invalido` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-003, FR-006, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: destino inválido aceito com 201.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T016 [TEST] [TDD] [US-004] Derivar do AC-016 o caso `mantém as ações da Prévia no topo` falhando em frontend/src/features/ingestao/FluxoIngestao.test.tsx — Refs: US-004, FR-007, FR-008, NFR-003, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual acontece na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `npx vitest run src/features/ingestao (10 failed, 21 passed)`: não existe a barra 'Ações da Prévia' no topo.
  - [x] **IMPROVE**: Cobertura revisada; o caso acessa os símbolos novos de forma dinâmica para não quebrar os testes existentes do mesmo arquivo.

- [x] T017 [TEST] [TDD] [US-004] Derivar do AC-017 o caso `troca a quantidade de chunks por página` falhando em frontend/src/features/ingestao/EtapaPrevia.test.tsx — Refs: US-004, FR-007, FR-008, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual acontece na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `npx vitest run src/features/ingestao (10 failed, 21 passed)`: a paginação usa 10 fixo: não mostra 'Página 1 de 3' com 50 por página.
  - [x] **IMPROVE**: Cobertura revisada; o caso acessa os símbolos novos de forma dinâmica para não quebrar os testes existentes do mesmo arquivo.

- [x] T018 [TEST] [TDD] [US-004] Derivar do AC-018 o caso `preserva filtro e escolhas ao trocar o tamanho da página` falhando em frontend/src/features/ingestao/FluxoIngestao.test.tsx — Refs: US-004, FR-007, FR-008, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual acontece na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `npx vitest run src/features/ingestao (10 failed, 21 passed)`: não existe o seletor 'Chunks por página'.
  - [x] **IMPROVE**: Cobertura revisada; o caso acessa os símbolos novos de forma dinâmica para não quebrar os testes existentes do mesmo arquivo.

- [x] T019 [TEST] [TDD] [US-005] Derivar do AC-019 o caso `test_qdrant_sem_chave_salva_com_teste_falho` falhando em tests/test_app_conexoes_teste.py — Refs: US-005, FR-009, NFR-001, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: a resposta da criação não traz `teste`.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T020 [TEST] [TDD] [US-005] Derivar do AC-020 o caso `test_embeddings_testa_e_confere_dimensao` falhando em tests/test_app_conexoes_teste.py — Refs: US-005, FR-009, NFR-001, AC-020 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: a resposta da criação e da edição não traz `teste`.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T021 [TEST] [TDD] [US-005] Derivar do AC-021 o caso `test_servidor_inalcancavel_falha_no_tempo_limite` falhando em tests/test_app_conexoes_teste.py — Refs: US-005, FR-009, NFR-001, AC-021 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: a resposta da criação não traz `teste`.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T022 [TEST] [TDD] [US-005] Derivar do AC-022 o caso `cadastra conexão no painel sem sair da Publicação` falhando em frontend/src/features/ingestao/EtapaPublicacao.test.tsx — Refs: US-005, FR-010, NFR-003, AC-022 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual acontece na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `npx vitest run src/features/ingestao (10 failed, 21 passed)`: não existe o botão Cadastrar conexão na Publicação.
  - [x] **IMPROVE**: Cobertura revisada; o caso acessa os símbolos novos de forma dinâmica para não quebrar os testes existentes do mesmo arquivo.

- [x] T023 [TEST] [TDD] [US-005] Derivar do AC-023 o caso `cancelar ou falhar no painel preserva o fluxo` falhando em frontend/src/features/ingestao/EtapaPublicacao.test.tsx — Refs: US-005, FR-009, FR-010, AC-023 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual acontece na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `npx vitest run src/features/ingestao (10 failed, 21 passed)`: não existe o botão Cadastrar conexão na Publicação.
  - [x] **IMPROVE**: Cobertura revisada; o caso acessa os símbolos novos de forma dinâmica para não quebrar os testes existentes do mesmo arquivo.

- [x] T024 [TEST] [TDD] [US-001] Derivar do AC-024 o caso `usa as cores de popover nas opções dos seletores` falhando em frontend/src/features/ingestao/EtapaDivisao.test.tsx — Refs: US-001, FR-011, NFR-003, AC-024 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual acontece na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `npx vitest run src/features/ingestao (10 failed, 21 passed)`: não existe o seletor Dividir por cabeçalhos e as opções não usam as cores de popover.
  - [x] **IMPROVE**: Cobertura revisada; o caso acessa os símbolos novos de forma dinâmica para não quebrar os testes existentes do mesmo arquivo.

- [x] T025 [TEST] [TDD] [US-001] Derivar do AC-025 o caso `seletores funcionam no tema claro e por teclado` falhando em frontend/src/features/ingestao/EtapaDivisao.test.tsx — Refs: FR-011, NFR-003, AC-025 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual acontece na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `npx vitest run src/features/ingestao (10 failed, 21 passed)`: a opção token não existe no seletor de estratégia.
  - [x] **IMPROVE**: Cobertura revisada; o caso acessa os símbolos novos de forma dinâmica para não quebrar os testes existentes do mesmo arquivo.

- [x] T026 [TEST] [TDD] [US-005] Derivar do AC-026 o caso `reaproveita o formulário de conexões no painel` falhando em frontend/src/features/ingestao/EtapaPublicacao.test.tsx — Refs: US-005, FR-009, FR-010, AC-026 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual acontece na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `npx vitest run src/features/ingestao (10 failed, 21 passed)`: não existe o botão Cadastrar conexão na Publicação.
  - [x] **IMPROVE**: Cobertura revisada; o caso acessa os símbolos novos de forma dinâmica para não quebrar os testes existentes do mesmo arquivo.

- [x] T037 [TEST] [TDD] [US-001] Derivar do AC-027 o caso `test_markdown_recursivo_divide_por_cabecalhos` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-001, FR-001, FR-002, FR-004, AC-027 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: 422 'Splitter desconhecido' para a estratégia markdown.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

- [x] T038 [TEST] [TDD] [US-001] Derivar do AC-028 o caso `test_separador_personalizado_no_por_caractere` falhando em tests/test_app_ingestao_estrategias.py — Refs: US-001, FR-002, AC-028 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-08 com `uv run pytest tests/test_app_ingestao_estrategias.py tests/test_app_conexoes_teste.py -q (30 failed, 10 passed)`: 422 'Splitter desconhecido' para a estratégia character_split.
  - [x] **IMPROVE**: Cobertura revisada; nenhuma chamada de rede real no caso.

#### Fase 2 — US-001 Escolher a estratégia de divisão (P1)

**Objetivo**: Prévia e publicação aceitam as seis estratégias com seus campos e guardam a escolha na Base.
**Teste independente**: `uv run pytest tests/test_app_ingestao_estrategias.py -k "estrategia or invalidos or guarda or anterior or frontmatter or niveis" -v`.

- [x] T027 [CODE] [US-001] Implementar as seis estratégias e o campo `processamento` na Prévia e na publicação em src/pipeline/chunker.py, src/app/ingestao.py, src/app/routers/ingestao.py e src/app/routers/bases.py — Refs: US-001, FR-001, FR-002, FR-003, NFR-002, AC-001, AC-002, AC-004, AC-005, AC-006, AC-007, AC-027, AC-028 — Depends: T001, T002, T004, T005, T006, T007, T037, T038
  - [x] **PREP**: RED confirmado nas tarefas TDD da fatia; `build_documentation.mjs --check` executado antes de editar.
  - [x] **EXECUTE**: Mudança implementada nos arquivos declarados.
  - [x] **VERIFY**: Testes focais e suíte completa do backend verdes.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN dos AC-001, AC-002, AC-004, AC-005, AC-006, AC-007, AC-027 e AC-028 com `uv run pytest tests/test_app_ingestao_estrategias.py -q` (37 passed); arquivos: `src/pipeline/chunker.py` (seis estratégias, breadcrumb até `nivel_6`), `src/app/ingestao.py` (`validar_parametros_divisao`, `montar_chunking`, `ler_processamento`), `src/app/routers/ingestao.py` e `src/app/routers/bases.py`.
  - [x] **IMPROVE**: Sem `processamento`, a Base continua guardando só a divisão, preservando o contrato da SPEC-0026 (`tests/test_app_publicacao.py`).
  <!-- specsfy:evidence {"task":"T027","refs":["US-001", "FR-001", "FR-002", "FR-003", "NFR-002", "AC-001", "AC-002", "AC-004", "AC-005", "AC-006", "AC-007", "AC-027", "AC-028"],"files":["src/pipeline/chunker.py", "src/app/ingestao.py", "src/app/routers/ingestao.py", "src/app/routers/bases.py"],"commands":[{"run":"uv run pytest -q","exit":0}]} -->

**Checkpoint**: a Prévia com cada estratégia devolve chunks do splitter correspondente e a Base publicada guarda a escolha.

#### Fase 3 — US-002 Resumos, cabeçalhos e qualidade (P1)

**Objetivo**: resumos de seção, níveis de cabeçalho, mínimo útil e status bloqueados controlados pelo formulário.
**Teste independente**: `uv run pytest tests/test_app_ingestao_estrategias.py -k "resumos or subsecoes or minimo_util or status" -v`.

- [x] T028 [CODE] [US-002] Aplicar resumos, níveis de cabeçalho, qualidade e status bloqueados na Prévia e no worker em src/app/ingestao.py e src/app/tasks.py — Refs: US-002, FR-004, FR-005, AC-008, AC-009, AC-010, AC-011, AC-012 — Depends: T008, T009, T010, T011, T012, T027
  - [x] **PREP**: RED confirmado nas tarefas TDD da fatia; `build_documentation.mjs --check` executado antes de editar.
  - [x] **EXECUTE**: Mudança implementada nos arquivos declarados.
  - [x] **VERIFY**: Testes focais e suíte completa do backend verdes.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN dos AC-008 a AC-012; a Prévia passa a avisar conteúdo útil curto e documentos excluídos por status; o worker recebe `qualidade` e `contrato_markdown`; arquivos: `src/app/ingestao.py`, `src/app/tasks.py` e `src/pipeline/quality.py` (mínimo útil 0 deixa de virar o padrão).
  - [x] **IMPROVE**: Corrigido em `src/pipeline/quality.py` o tratamento de `minimo_util` 0, que antes caía no padrão de 60.
  <!-- specsfy:evidence {"task":"T028","refs":["US-002", "FR-004", "FR-005", "AC-008", "AC-009", "AC-010", "AC-011", "AC-012"],"files":["src/app/ingestao.py", "src/app/tasks.py"],"commands":[{"run":"uv run pytest -q","exit":0}]} -->

**Checkpoint**: desligar resumos, mudar o mínimo útil ou bloquear um status altera a Prévia e a execução.

#### Fase 4 — US-003 Destino da indexação (P2)

**Objetivo**: batch_size e sync_mode escolhidos na publicação chegam ao worker e à repetição.
**Teste independente**: `uv run pytest tests/test_app_ingestao_estrategias.py -k "destino" -v`.

- [x] T029 [CODE] [US-003] Validar e repassar batch_size e sync_mode da Base ao worker em src/app/routers/bases.py e src/app/tasks.py — Refs: US-003, FR-006, NFR-002, AC-014, AC-015 — Depends: T014, T015, T028
  - [x] **PREP**: RED confirmado nas tarefas TDD da fatia; `build_documentation.mjs --check` executado antes de editar.
  - [x] **EXECUTE**: Mudança implementada nos arquivos declarados.
  - [x] **VERIFY**: Testes focais e suíte completa do backend verdes.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN dos AC-014 e AC-015; `batch_size` e `sync_mode` da Base chegam a `embedding` e `vector_store` no worker e na repetição; Bases sem `destino` seguem os padrões da fachada; arquivos: `src/app/routers/bases.py` e `src/app/tasks.py`.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: a repetição já lê a Base, então o destino não precisou de argumento novo na fila.
  <!-- specsfy:evidence {"task":"T029","refs":["US-003", "FR-006", "NFR-002", "AC-014", "AC-015"],"files":["src/app/routers/bases.py", "src/app/tasks.py"],"commands":[{"run":"uv run pytest -q","exit":0}]} -->

**Checkpoint**: uma Base publicada com batch_size 20 e mirror executa e repete com esses valores.

#### Fase 5 — US-005 Testar a conexão ao salvar (P1)

**Objetivo**: criar ou editar uma conexão testa o acesso e devolve o resultado sem bloquear o salvamento nem expor a chave.
**Teste independente**: `uv run pytest tests/test_app_conexoes_teste.py -v`.

- [x] T030 [CODE] [US-005] Implementar o teste de conexão na fachada e devolvê-lo em POST e PATCH de conexões em src/pipeline/service.py, src/app/conexoes.py, src/app/routers/conexoes.py e tests/conftest.py — Refs: US-005, FR-009, NFR-001, AC-019, AC-020, AC-021 — Depends: T019, T020, T021
  - [x] **PREP**: RED confirmado nas tarefas TDD da fatia; `build_documentation.mjs --check` executado antes de editar.
  - [x] **EXECUTE**: Mudança implementada nos arquivos declarados.
  - [x] **VERIFY**: Testes focais e suíte completa do backend verdes.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN dos AC-019, AC-020 e AC-021 com `uv run pytest tests/test_app_conexoes_teste.py -q` (3 passed); suíte completa `uv run pytest -q` com 543 passed e 1 skipped; arquivos: `src/pipeline/service.py` (`testar_conexao` com tempo limite de 15 s), `src/pipeline/providers/vectorstores/qdrant.py` (`testar_acesso`), `src/app/conexoes.py`, `src/app/routers/conexoes.py` e `tests/conftest.py` (fixture automática sem rede).
  - [x] **IMPROVE**: O teste do Qdrant foi movido para o provider para respeitar `tests/test_provider_boundaries.py`; a formatação acidental de nove arquivos não relacionados foi desfeita.
  <!-- specsfy:evidence {"task":"T030","refs":["US-005", "FR-009", "NFR-001", "AC-019", "AC-020", "AC-021"],"files":["src/pipeline/service.py", "src/app/conexoes.py", "src/app/routers/conexoes.py", "tests/conftest.py"],"commands":[{"run":"uv run pytest -q","exit":0}]} -->

**Checkpoint**: salvar uma conexão Qdrant sem a chave exigida grava a conexão e devolve o motivo do teste falho.

#### Fase de interface

- [x] T031 [CODE] [US-001] Implementar a etapa Divisão com estratégia, campos próprios, resumos, cabeçalhos e bloco Qualidade, e corrigir o contraste dos seletores em frontend/src/features/ingestao/EtapaDivisao.tsx, frontend/src/lib/ingestao.ts e frontend/src/features/ingestao/useFluxoIngestao.ts — Refs: US-001, US-002, FR-002, FR-004, FR-005, FR-011, NFR-003, AC-003, AC-024, AC-025 — Depends: T003, T024, T025, T028
  - [x] **PREP**: RED confirmado; stack e telas da seção 10 conferidas; primitives disponíveis lidas em `frontend/src/components/ui/` e `INTERFACE.md` antes de escrever TSX; `build_documentation.mjs --check` executado.
  - [x] **EXECUTE**: Mudança implementada e registrada em `INTERFACE.md`.
  - [x] **VERIFY**: `npx vitest run (229 passed), npm run lint limpo, npm run build ok`.
  - [x] **VISUAL**: Conferência manual pela pessoa responsável em 2026-10-09 no stack local (`localhost:3000`, bundle servido já com o código da SPEC-0029), na etapa Divisão (seis estratégias, campos próprios, bloco Qualidade e contraste dos seletores), nos temas claro e escuro, com janela maximizada e modo celular do DevTools em 390 px, navegação por Tab e conteúdo longo, conferindo bordas, espaçamentos, margens, padding, tipografia, foco e overflow. Resultado: "tudo ok"; nenhum ajuste necessário.
  - [x] **EVIDENCE**: GREEN dos AC-003, AC-024 e AC-025; arquivos: `frontend/src/features/ingestao/EtapaDivisao.tsx`, `frontend/src/lib/ingestao.ts`, `frontend/src/features/ingestao/useFluxoIngestao.ts` e o novo `frontend/src/features/ingestao/seletor.ts`; teste da SPEC-0026 atualizado para as seis estratégias (DEC-004). Conferência visual concluída ("tudo ok" em 2026-10-09); `npx vitest run` 53 arquivos/229 testes, `npm run lint` limpo, `npm run build` ok, `build_documentation.mjs --check` saída 0; `PROJECT.md` revisado com o parágrafo da SPEC-0029.
  - [x] **IMPROVE**: O estilo do select nativo foi centralizado em `seletor.ts` e aplicado também ao filtro da Prévia e ao Tipo do formulário de conexão; sem `Switch`, `Collapsible` ou `Checkbox` no projeto, foram usados checkbox nativo e botão com `aria-expanded`, sem nova dependência.
  <!-- specsfy:evidence {"task":"T031","refs":["US-001", "US-002", "FR-002", "FR-004", "FR-005", "FR-011", "NFR-003", "AC-003", "AC-024", "AC-025"],"files":["frontend/src/features/ingestao/EtapaDivisao.tsx", "frontend/src/lib/ingestao.ts", "frontend/src/features/ingestao/useFluxoIngestao.ts"],"commands":[{"run":"npm --prefix frontend run test:tdd","exit":0}]} -->

- [x] T032 [CODE] [US-004] Implementar a barra de ações no topo da Prévia e o seletor de chunks por página em frontend/src/features/ingestao/FluxoIngestao.tsx, frontend/src/features/ingestao/EtapaPrevia.tsx e frontend/src/features/ingestao/useFluxoIngestao.ts — Refs: US-004, FR-007, FR-008, NFR-003, AC-016, AC-017, AC-018 — Depends: T016, T017, T018, T031
  - [x] **PREP**: RED confirmado; stack e telas da seção 10 conferidas; primitives disponíveis lidas em `frontend/src/components/ui/` e `INTERFACE.md` antes de escrever TSX; `build_documentation.mjs --check` executado.
  - [x] **EXECUTE**: Mudança implementada e registrada em `INTERFACE.md`.
  - [x] **VERIFY**: `npx vitest run (229 passed), npm run lint limpo, npm run build ok`.
  - [x] **VISUAL**: Conferência manual pela pessoa responsável em 2026-10-09 no stack local (`localhost:3000`, bundle servido já com o código da SPEC-0029), na etapa Prévia (barra Voltar/Próxima e seletor de chunks por página no topo, filtro preservado, chunks longos), nos temas claro e escuro, com janela maximizada e modo celular do DevTools em 390 px, navegação por Tab e conteúdo longo, conferindo bordas, espaçamentos, margens, padding, tipografia, foco e overflow. Resultado: "tudo ok"; nenhum ajuste necessário.
  - [x] **EVIDENCE**: GREEN dos AC-016, AC-017 e AC-018; arquivos: `frontend/src/features/ingestao/FluxoIngestao.tsx`, `frontend/src/features/ingestao/EtapaPrevia.tsx` e `frontend/src/features/ingestao/useFluxoIngestao.ts`. Conferência visual concluída ("tudo ok" em 2026-10-09); `npx vitest run` 53 arquivos/229 testes, `npm run lint` limpo, `npm run build` ok, `build_documentation.mjs --check` saída 0; `PROJECT.md` revisado com o parágrafo da SPEC-0029.
  - [x] **IMPROVE**: Na Prévia o rodapé Voltar e Próxima dá lugar à barra do topo, evitando botões duplicados.
  <!-- specsfy:evidence {"task":"T032","refs":["US-004", "FR-007", "FR-008", "NFR-003", "AC-016", "AC-017", "AC-018"],"files":["frontend/src/features/ingestao/FluxoIngestao.tsx", "frontend/src/features/ingestao/EtapaPrevia.tsx", "frontend/src/features/ingestao/useFluxoIngestao.ts"],"commands":[{"run":"npm --prefix frontend run test:tdd","exit":0}]} -->

- [x] T033 [CODE] [US-003] Implementar os campos de destino (batch_size e sync_mode com aviso) na Publicação em frontend/src/features/ingestao/EtapaPublicacao.tsx — Refs: US-003, FR-006, NFR-003, AC-013 — Depends: T013, T029, T032
  - [x] **PREP**: RED confirmado; stack e telas da seção 10 conferidas; primitives disponíveis lidas em `frontend/src/components/ui/` e `INTERFACE.md` antes de escrever TSX; `build_documentation.mjs --check` executado.
  - [x] **EXECUTE**: Mudança implementada e registrada em `INTERFACE.md`.
  - [x] **VERIFY**: `npx vitest run (229 passed), npm run lint limpo, npm run build ok`.
  - [x] **VISUAL**: Conferência manual pela pessoa responsável em 2026-10-09 no stack local (`localhost:3000`, bundle servido já com o código da SPEC-0029), na etapa Publicação (bloco Avançado com batch_size, sync_mode e aviso do mirror), nos temas claro e escuro, com janela maximizada e modo celular do DevTools em 390 px, navegação por Tab e conteúdo longo, conferindo bordas, espaçamentos, margens, padding, tipografia, foco e overflow. Resultado: "tudo ok"; nenhum ajuste necessário.
  - [x] **EVIDENCE**: GREEN do AC-013; arquivo: `frontend/src/features/ingestao/EtapaPublicacao.tsx`; o destino segue no `processamento` da publicação; teste da SPEC-0026 atualizado para incluir o destino padrão. Conferência visual concluída ("tudo ok" em 2026-10-09); `npx vitest run` 53 arquivos/229 testes, `npm run lint` limpo, `npm run build` ok, `build_documentation.mjs --check` saída 0; `PROJECT.md` revisado com o parágrafo da SPEC-0029.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: os campos ficam no bloco Avançado recolhido, como decidido.
  <!-- specsfy:evidence {"task":"T033","refs":["US-003", "FR-006", "NFR-003", "AC-013"],"files":["frontend/src/features/ingestao/EtapaPublicacao.tsx"],"commands":[{"run":"npm --prefix frontend run test:tdd","exit":0}]} -->

- [x] T034 [CODE] [US-005] Abrir o ConexaoFormSheet na Publicação e exibir o resultado do teste no painel em frontend/src/features/ingestao/EtapaPublicacao.tsx e frontend/src/features/conexoes/ConexaoFormSheet.tsx — Refs: US-005, FR-009, FR-010, NFR-003, AC-022, AC-023, AC-026 — Depends: T022, T023, T026, T030, T033
  - [x] **PREP**: RED confirmado; stack e telas da seção 10 conferidas; primitives disponíveis lidas em `frontend/src/components/ui/` e `INTERFACE.md` antes de escrever TSX; `build_documentation.mjs --check` executado.
  - [x] **EXECUTE**: Mudança implementada e registrada em `INTERFACE.md`.
  - [x] **VERIFY**: `npx vitest run (229 passed), npm run lint limpo, npm run build ok`.
  - [x] **VISUAL**: Conferência manual pela pessoa responsável em 2026-10-09 no stack local (`localhost:3000`, bundle servido já com o código da SPEC-0029), na painel Nova conexão na Publicação (abertura, resultado do teste, cancelar preservando o fluxo), nos temas claro e escuro, com janela maximizada e modo celular do DevTools em 390 px, navegação por Tab e conteúdo longo, conferindo bordas, espaçamentos, margens, padding, tipografia, foco e overflow. Resultado: "tudo ok"; nenhum ajuste necessário.
  - [x] **EVIDENCE**: GREEN dos AC-022, AC-023 e AC-026; arquivos: `frontend/src/features/ingestao/EtapaPublicacao.tsx`, `frontend/src/features/conexoes/ConexaoFormSheet.tsx`, `frontend/src/features/conexoes/DataGridConexoes.tsx` (tipo `teste`) e as páginas `/conexoes` e `/conexoes/[id]` (aviso com o resultado do teste). Conferência visual concluída ("tudo ok" em 2026-10-09); `npx vitest run` 53 arquivos/229 testes, `npm run lint` limpo, `npm run build` ok, `build_documentation.mjs --check` saída 0; `PROJECT.md` revisado com o parágrafo da SPEC-0029.
  - [x] **IMPROVE**: As telas de Conexões passaram a anunciar o resultado do teste no aviso existente, sem componente novo.
  <!-- specsfy:evidence {"task":"T034","refs":["US-005", "FR-009", "FR-010", "NFR-003", "AC-022", "AC-023", "AC-026"],"files":["frontend/src/features/ingestao/EtapaPublicacao.tsx", "frontend/src/features/conexoes/ConexaoFormSheet.tsx"],"commands":[{"run":"npm --prefix frontend run test:tdd","exit":0}]} -->

#### Fase final — Documentação e qualidade

- [x] T035 [DOC] Registrar as chaves novas de `bases.chunking` em .specsfy/DATABASE.md e os blocos alterados em INTERFACE.md — Refs: FR-003, FR-006, FR-010, AC-005, AC-014, AC-022 — Depends: T027, T028, T029, T030, T031, T032, T033, T034
  - [x] **PREP**: Ler `.specsfy/DATABASE.md`, `INTERFACE.md` e os arquivos alterados.
  - [x] **EXECUTE**: Executar `$specsfy-aux-database` para as chaves de `bases.chunking` e atualizar `INTERFACE.md` com finalidade, arquivo, API, estados e consumidores dos blocos alterados.
  - [x] **VERIFY**: Executar `monitor_context.mjs --check` e conferir que DATABASE.md e INTERFACE.md correspondem ao código.
  - [x] **VISUAL**: Não aplicável: a tarefa só altera documentação.
  - [x] **EVIDENCE**: `.specsfy/DATABASE.md` (chaves novas de `bases.chunking`), `INTERFACE.md` (blocos estendidos e o novo `seletor`), `docs/architecture.md` e `docs/application.md`; `build_documentation.mjs --check` com saída 0 e `monitor_context.mjs --check` CURRENT.
  - [x] **IMPROVE**: `DATABASE.md` atualizado à mão no inventário existente, sem duplicar a linha de `bases`.

- [x] T036 [TEST] Executar regressão, lint, tipos, build, rastreabilidade e a conferência visual e funcional pelo front em tests/test_app_ingestao_estrategias.py — Refs: US-001, US-002, US-003, US-004, US-005, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018, AC-019, AC-020, AC-021, AC-022, AC-023, AC-024, AC-025, AC-026, AC-027, AC-028 — Depends: T035
  - [x] **PREP**: Suítes e checks identificados; `check_database_safety.mjs` SAFE para `uv run pytest -q` (Postgres de teste em `localhost:55432`).
  - [x] **EXECUTE**: `uv run ruff check .` sem achados; `uv run pytest -q` 542 passed, 1 skipped (a única falha, `test_spec_markers`, vinha do texto da SPEC-0030 e foi corrigida; reexecução 1 passed); `npm run lint` limpo; `npx vitest run` 53 arquivos/229 testes; `npm run build` ok; `check_traceability.mjs --full-chain` 47/47 IDs em 125 arquivos.
  - [x] **VERIFY**: Sem gaps. Publicação real em 2026-10-09 pela pessoa responsável no stack local: Base `Q&A.md` no Workspace `teste`, coleção `teste vivo`, estratégia por caractere; Prévia com 20 chunks e execução `succeeded` com previstos 20, inseridos 20, mantidos 0, removidos 0.
  - [x] **VISUAL**: Conferência final manual pela pessoa responsável ("tudo ok", 2026-10-09) das etapas Divisão, Prévia e Publicação e do painel de conexão, conferindo bordas, espaçamentos, margens, padding e tipografia nos temas claro e escuro, em tela larga e em 390 px; a captura da execução publicada no tema escuro não mostra desalinhamento nem overflow.
  - [x] **EVIDENCE**: Contagens e comandos registrados acima e no Gate do Ato III; `PROJECT.md` revisado com o parágrafo e a capacidade da SPEC-0029; `build_documentation.mjs --check` saída 0; `monitor_context.mjs --check` CURRENT.
  - [x] **IMPROVE**: Retrospectiva: o falso positivo do validador com a palavra portuguesa para "cada um" voltou a aparecer numa spec nova; a trava local `tests/test_spec_markers.py` pegou o problema na regressão, o que confirma sua utilidade até a correção no upstream.

### 15. Ordem de execução

- Caminho crítico: T001–T026, T037 e T038 (RED) → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T034 → T035 → T036.
- Tarefas paralelas: T001–T026 escrevem casos independentes; T030 (conexões) não compartilha arquivos com T027–T029 e pode correr em paralelo a elas, mas fica em sequência no plano por simplicidade de revisão.
- Estratégia de MVP: US-001 e US-005 (T027, T030, T031 e T034) entregam as estratégias e o teste de conexão; US-002, US-003 e US-004 completam.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0026 e SPEC-0028 concluídas; PR #29 integrado antes do merge desta branch.
- `langchain-text-splitters` e `tiktoken` já instalados.
- Stack local atualizado com autorização para a conferência final.

#### Riscos

- `tiktoken` baixa os arquivos de encoding na primeira utilização → erro claro na Prévia e verificação no stack local antes de concluir.
- Teste de embeddings gera uma chamada paga a cada salvamento → um único texto curto por teste.
- `ExperimentalMarkdownSyntaxTextSplitter` é experimental e pode mudar entre versões → teste de AC-002 fixa o comportamento esperado.
- Suíte acidentalmente fazendo rede no teste de conexão → fixture automática em `tests/conftest.py` substitui `service.testar_conexao`.
- Sem migration, `bases.chunking` acumula chaves heterogêneas → estrutura documentada em `.specsfy/DATABASE.md` (T035).

#### Suposições

- A barra de ações da Prévia fica fixa no topo durante a rolagem.
- Os padrões continuam constantes em `src/app/ingestao.py`, espelhando o `config.yaml`.
- O separador de `character_split` é livre, com padrão parágrafo (`\n\n`).
- Só owner e admin usam o fluxo e a tela Conexões.
- Limites propostos pelo agente, reversíveis e ainda não confirmados pela pessoa: tamanho por tokens de 50 a 2000; encodings `cl100k_base` e `o200k_base`; mínimo de subseções de 2 a 10; mínimo útil de 0 a 1000; até 20 status bloqueados de até 40 caracteres; `batch_size` de 1 a 500; tempo limite de 15 segundos no teste de conexão.
- No painel de conexão, sucesso fecha o painel e falha o mantém aberto com Editar e Fechar.

### 17. Decisões

- **DEC-001**: Guardar as escolhas novas em `bases.chunking` (JSON existente) — razão: evita migration enquanto o deploy não aplica migrations (captura `specs/inbox/2026-10-08-220019-stack-local-divergente-dos-arquivos-de-deploy-e-banco-sem-historico-de-migrations.md`); alternativa: coluna `processamento` nova; trade-off: nome da coluna mais estreito que o conteúdo.
- **DEC-002**: `CharacterTextSplitter` usa o valor novo `character_split`; `character` continua recursivo — razão: preservar arquivos que já usam `splitter: character` no frontmatter.
- **DEC-003**: Substituída por DEC-007 em 2026-10-08. Texto original: níveis de cabeçalho limitados a `#`, `##` e `###` com metadados fixos, porque breadcrumb e resumos dependem de `titulo`, `secao` e `subsecao`.
- **DEC-004**: Estratégias restritas às aplicáveis a Markdown sem dependência nova — decisão da pessoa em 2026-10-08.
- **DEC-005**: O teste de conexão roda depois de gravar e nunca bloqueia o salvamento — decisão da pessoa em 2026-10-08, como nas credenciais do n8n.
- **DEC-007**: Dividir por cabeçalhos como seletor de nível máximo de H1 a H6 nas três estratégias Markdown (Desativado só no Markdown recursivo), níveis 4 a 6 com metadados `nivel_4` a `nivel_6` no breadcrumb, resumos agrupados por título e seção, e separador livre no Por caractere — decisão da pessoa em 2026-10-08, com base no Split by Headers e no Custom Separator do Flowise. IDs impactados: FR-001, FR-002, FR-004, AC-001, AC-003, AC-004, AC-027 e AC-028; seções 2, 3, 8, 9, 10, 11, 12, 14 e 16.
- **DEC-006**: `sync_mode` padrão `append`, `namespace` e `index_name` fora — decisão da pessoa em 2026-10-08, após correção do agente.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Os cenários `AC` aplicáveis passam.
- [x] Os requisitos possuem evidência de verificação.
- [x] As tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/DATABASE.md` descreve as chaves novas de `bases.chunking`.
- [x] `INTERFACE.md` registra os blocos estendidos.
