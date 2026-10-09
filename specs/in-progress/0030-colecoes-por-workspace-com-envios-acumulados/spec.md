# Especificação integrada: Coleções por Workspace com envios acumulados e identidade estável de documento

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0030 |
| Slug | 0030-colecoes-por-workspace-com-envios-acumulados |
| Status | Implementing |
| Effort | 9 |
| Effort updated at | 2026-10-09 |
| Effort rationale | Troca a unidade central do produto (Base → Coleção) em persistência, worker, fachada do pipeline, adapter Qdrant, API, assistente e quatro telas; introduz sincronização por documento, identidade estável, remoção individual e exclusão física de coleção, com descarte das Bases atuais sem comandos destrutivos de schema. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | In Progress |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-09 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

Cada upload cria uma Base nova (`src/app/routers/bases.py`, `POST /bases`) com escopo vetorial próprio `tenant::projeto::base_id` (`src/app/tasks.py`, `scope_project_id`). Mesmo quando duas Bases usam a mesma coleção do Qdrant, seus pontos ficam em escopos separados. Em 2026-10-08 verificamos três consequências:

- subir o mesmo arquivo duas vezes duplica os chunks na coleção, em qualquer `sync_mode`;
- o `mirror` só limpa o escopo do próprio upload e nunca remove versões enviadas antes;
- não existe forma de apagar um documento específico, apenas a Base inteira.

Há também um defeito de identidade: `document_id` deriva de `caminho_relativo`, que inclui a pasta temporária aleatória do worker (`base-<id>-XXXX/arquivo.md`, `src/pipeline/loader.py:88` + `src/pipeline/identity.py`). No teste de 2026-10-08, o mesmo `doc.md` recebeu `0093c04e-…` no primeiro envio e `9282e935-…` no segundo.

#### Resultado desejado

Dentro de um Workspace, a pessoa organiza os documentos em Coleções nomeadas. O nome da coleção é definido no primeiro envio, e os envios seguintes adicionam arquivos a ela. Reenviar um arquivo idêntico não duplica nem gera embedding. Reenviar um arquivo de mesmo nome com conteúdo novo substitui a versão anterior. Um documento obsoleto pode ser apagado sozinho. A consulta é feita sobre a coleção inteira.

#### Métricas de sucesso

- 0 chunk duplicado após reenviar o mesmo arquivo para a mesma coleção, medido por AC-004.
- 0 embedding gerado ao reenviar um arquivo idêntico, medido por AC-004 e NFR-002.
- 100% dos chunks da versão anterior removidos ao substituir um documento, e 0 chunk de outros documentos afetado, medido por AC-005 e AC-006.
- Apagar um documento remove exatamente os chunks dele, medido por AC-010.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: O mesmo arquivo enviado duas vezes recebe a mesma identidade? → Não. Execução local em 2026-10-08 com `load_markdown_documents` + `assign_document_identity` em duas pastas `base-7-XXXX`: `document_id` diferente em cada envio. Impacto: FR-004.
- **R-002**: O `mirror` remove documentos de uploads anteriores na mesma coleção? → Não. `synchronize` (`src/pipeline/providers/vectorstores/base.py:211`) só remove IDs ausentes dentro do `LogicalScope`, e cada Base tem escopo próprio. Impacto: FR-005, DEC-003.
- **R-003**: Quais pontos do sistema dependem de Base? → Upload (`routers/bases.py`), execução (`routers/executions.py`, `tasks.process_base_task`), consulta (`routers/queries.py`), exclusão (`apagar_base`), Workspace (`has_active_bases_for_workspace`), assistente (`SeletorBase`, `/api/v1/bases`) e telas `/workspaces/[id]`, `/workspaces/[id]/bases/nova`, `/execucoes/[id]`. Impacto: escopo e plano.

#### Fontes e contexto consultados

- Código: `src/app/models.py`, `src/app/routers/{bases,executions,queries,workspaces,ingestao}.py`, `src/app/tasks.py`, `src/pipeline/{loader,identity,indexing,service,safety}.py`, `src/pipeline/providers/vectorstores/{base,qdrant}.py`, `frontend/src/app/(autenticado)/workspaces/**`, `frontend/src/features/{bases,ingestao,assistente}/`.
- Contexto: `PROJECT.md`, `INTERFACE.md`, `DESIGNSYSTEM.MD`, `.specsfy/DATABASE.md` (seção `Informações a guardar confirmadas`: Coleção de documentos do Workspace, Documento da coleção, Envio de documentos para a coleção).
- Proveniência: `specs/inbox/2026-10-08-235030-colecoes-por-workspace-com-uploads-acumulados-e-identidade-estavel-de-documento.md`, `specs/backlog/0037-colecoes-por-workspace-com-uploads-acumulados.md`.

#### Documentação consultada

- Nenhuma documentação externa; a decisão usa somente o comportamento observado no código local.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: O que acontece com o conceito de Base? → **A**: A Coleção substitui a Base. O Workspace lista coleções; cada coleção mostra documentos e histórico de envios; a consulta é feita na coleção (backlog 0037, Pergunta 1).
- **Q**: O que fazer com as Bases atuais? → **A**: Descartar tudo e começar do zero, sem migração (Pergunta 2).
- **Q**: Manter `append`/`mirror` no envio? → **A**: Remover a escolha; cada envio segue a regra única (Pergunta 3).
- **Q**: A coleção pode ser renomeada? → **A**: Sim, só o nome exibido; o nome físico no Qdrant é fixo (Pergunta 4).
- **Q**: Por onde se sobe documentos? → **A**: Um fluxo único com dois pontos de entrada: Enviar documentos no Workspace e Adicionar documentos na coleção, com escolha ou criação da coleção na Publicação (Pergunta 5).
- **Q**: Como organizar o detalhe da coleção? → **A**: Abas Documentos | Envios | Consulta, abrindo em Documentos (Pergunta 6).
- **Q**: O que faz a linha de um documento? → **A**: Abre um painel lateral só de leitura com os chunks; as ações são Substituir e Apagar com confirmação (Pergunta 7).
- **Q**: Apagar coleção faz o quê no Qdrant? → **A**: Apaga a coleção física inteira, com confirmação por digitação do nome (Pergunta 8).
- **Q**: O chunking é fixo por coleção? → **A**: Não; é escolhido a cada envio ("posso usar documentos completamente diferentes", conversa de 2026-10-08).
- **Q**: O que acontece com o histórico de envios quando um documento é apagado ou substituído? → **A**: O histórico continua intacto (descoberta de dados, 2026-10-09).

#### Dúvidas abertas

- Nenhuma bloqueante. Os defaults reversíveis estão em Suposições (seção 16).

### 3. Escopo e atores

#### Incluído

- Entidade Coleção por Workspace, com nome exibido editável e nome físico fixo no Qdrant.
- Fluxo de envio (Arquivos → Divisão → Prévia → Publicação) com escolha de coleção existente ou criação de nova.
- Identidade estável de documento por coleção e nome do arquivo.
- Sincronização por documento: somar, manter ou substituir, sem `sync_mode`.
- Lista de documentos da coleção, painel com chunks, Substituir e Apagar documento.
- Histórico de envios por coleção, com detalhe e repetição de envio que falhou.
- Consulta por coleção na aba Consulta e no assistente.
- Renomear e apagar coleção, incluindo a coleção física no Qdrant.
- Descarte das Bases atuais e remoção da API e das telas de Base.

#### Fora de escopo

- Migrar Bases, execuções ou consultas atuais para coleções.
- Mover documento entre coleções ou entre Workspaces.
- Trocar o modelo de embedding ou as conexões de uma coleção existente.
- Renomear o nome físico no Qdrant.
- Manter versões anteriores de um documento consultáveis.
- Escolher `append` ou `mirror` na interface.

#### Atores

- **Owner e admin**: criam coleções no envio, enviam e substituem documentos, renomeiam e apagam coleções e documentos, repetem envios e consultam.
- **Member**: vê coleções, documentos, chunks, envios e consulta, sem ações de escrita.
- **Worker de ingestão**: processa cada envio em segundo plano e sincroniza os documentos com o Qdrant.

### 4. Princípios e restrições do projeto

- **PR-001**: `src/app/` importa somente a fachada `src/pipeline/service.py`; SDK de vetor e embeddings só em `src/pipeline/providers/` (testes AST existentes).
- **PR-002**: Nenhum comando apaga ou recria banco ou schema (`DROP TABLE`, `TRUNCATE`, `migrate:reset`, `RefreshDatabase` e equivalentes). Tabelas legadas permanecem; o descarte é feito por linhas, pelo caminho da aplicação.
- **PR-003**: Política fail-closed de `src/pipeline/safety.py` antes de qualquer mutação remota; a exclusão física de coleção é a única operação destrutiva nova e só ocorre pelo caso de uso de apagar coleção (DEC-005).
- **PR-004**: Chaves de conexão nunca aparecem em resposta, log ou tela (SPEC-0026/0029).
- **PR-005**: Interface em React com shadcn/ui e ReUI, `PageHeader` único, `DataGrid` em largura total com coluna ID, linha clicável e ações por linha (`DESIGNSYSTEM.MD`, `INTERFACE.md`).
- **PR-006**: Testes Python com Pytest; frontend com Vitest (`npm run test:tdd`). Testes nunca usam o banco de desenvolvimento.

### 5. Histórias de usuário

#### US-001 — Enviar documentos para uma coleção nova ou existente (P1)

Como owner ou admin, quero enviar arquivos escolhendo uma coleção do Workspace ou criando uma nova no próprio envio, para acumular documentos sob um mesmo nome.

**Por que P1**: é a mudança de modelo pedida e a base de todas as outras histórias.
**Teste independente**: criar a coleção "manuais" num envio com `a.md` e, num segundo envio, escolher "manuais" e mandar `b.md`; a coleção passa a listar `a.md` e `b.md`.
**Requisitos**: FR-001, FR-002, FR-003, FR-006, FR-007, FR-015

#### US-002 — Reenviar sem duplicar e substituir versões (P1)

Como owner ou admin, quero que um arquivo idêntico seja reconhecido e que um arquivo de mesmo nome com conteúdo novo substitua o anterior, para a coleção não ter duplicatas nem trechos desatualizados.

**Por que P1**: resolve o defeito que motivou a mudança.
**Teste independente**: reenviar `a.md` idêntico gera 0 embeddings e mantém os mesmos chunks; reenviar `a.md` alterado deixa só os chunks novos de `a.md`.
**Requisitos**: FR-004, FR-005

#### US-003 — Ver documentos, chunks e histórico da coleção (P2)

Como pessoa do projeto, quero ver os documentos da coleção, os chunks de cada um e o histórico de envios, para conferir o que está indexado e acompanhar o processamento.

**Por que P2**: dá visibilidade e é pré-requisito para a remoção individual.
**Teste independente**: abrir a coleção, ver a tabela de documentos, abrir o painel de chunks de `a.md` e a aba Envios com situação e contagens.
**Requisitos**: FR-008, FR-012

#### US-004 — Apagar um documento da coleção (P1)

Como owner ou admin, quero apagar um documento específico, para que a busca deixe de usar conteúdo obsoleto sem refazer a coleção.

**Por que P1**: sem isso, não há forma de remover conteúdo sem `mirror`, que foi retirado.
**Teste independente**: apagar `a.md` numa coleção com `a.md` e `b.md`; só os chunks de `a.md` saem e o histórico de envios continua igual.
**Requisitos**: FR-009

#### US-005 — Renomear e apagar uma coleção (P2)

Como owner ou admin, quero renomear uma coleção e apagá-la inteira quando não servir mais, para manter o Workspace organizado.

**Por que P2**: completa o ciclo de vida da coleção.
**Teste independente**: renomear "manuais" para "manuais técnicos" sem mudar o nome físico; apagar a coleção digitando o nome e confirmar que ela some do Workspace e do Qdrant.
**Requisitos**: FR-010, FR-011

#### US-006 — Consultar a coleção e começar sem Bases antigas (P2)

Como pessoa do projeto, quero consultar a coleção inteira na aba Consulta e no assistente, e não ver mais as Bases antigas, para trabalhar só no modelo novo.

**Por que P2**: substitui a consulta por Base e encerra o modelo antigo.
**Teste independente**: consultar "manuais" e receber chunks de `a.md` e `b.md`; a tela do Workspace não mostra Bases.
**Requisitos**: FR-013, FR-014

### 6. Cenários BDD de aceite

#### AC-001 — Criar coleção no primeiro envio

**Cobre**: US-001, FR-001, FR-002, FR-003, FR-006, FR-007, FR-015

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @FR-006 @FR-007 @FR-015 @AC-001
Feature: Envio de documentos para coleção

  Scenario: Owner cria a coleção ao publicar o primeiro envio
    Given o Workspace "Clientes" sem coleções e uma owner autenticada
    When ela envia "a.md" com divisão por cabeçalhos, escolhe "Nova coleção" com nome "manuais" e as conexões de embeddings e Qdrant e publica
    Then a Publicação não oferece escolha de modo de sincronização
    And o Workspace passa a listar a coleção "manuais" com 1 documento
    And a coleção guarda as conexões escolhidas e um nome físico que não muda
    And o envio registra a divisão por cabeçalhos
```

#### AC-002 — Adicionar documento a coleção existente com conexões herdadas

**Cobre**: US-001, FR-002, FR-003, FR-006, FR-007

```gherkin
@US-001 @FR-002 @FR-003 @FR-006 @FR-007 @AC-002
Feature: Envio de documentos para coleção

  Scenario: Admin adiciona arquivo pela tela da coleção
    Given a coleção "manuais" com "a.md"
    When um admin clica em "Adicionar documentos" na coleção, envia "b.md" com divisão recursiva e chega à Publicação
    Then a coleção "manuais" já vem escolhida e as conexões aparecem travadas com as da coleção
    And não há escolha de modo de sincronização
    And após publicar a coleção lista "a.md" e "b.md", cada um com a divisão usada
```

#### AC-003 — Bloqueios ao criar ou usar coleção

**Cobre**: US-001, FR-001, FR-003, FR-007, NFR-004

```gherkin
@US-001 @FR-001 @FR-003 @FR-007 @NFR-004 @AC-003
Feature: Envio de documentos para coleção

  Scenario Outline: Envio inválido é recusado antes de gravar
    Given a coleção "manuais" no Workspace "Clientes"
    When uma owner tenta publicar <situacao>
    Then o envio é recusado com a mensagem "<mensagem>"
    And nenhum ponto é gravado no Qdrant e nenhum documento é registrado

    Examples:
      | situacao | mensagem |
      | criando outra coleção chamada "Manuais" no mesmo Workspace | Já existe uma coleção com esse nome neste Workspace. |
      | para "manuais" informando outra conexão de embeddings | A coleção usa conexões fixas; envie sem trocar as conexões. |
      | para "manuais" depois que a conexão de embeddings da coleção passou a usar um modelo de outra dimensão | Dimensões incompatíveis: modelo 3072, coleção 1536. |
      | informando sync_mode "mirror" | Modo de sincronização não é aceito no envio. |
```

#### AC-004 — Reenviar arquivo idêntico não duplica

**Cobre**: US-002, FR-004, FR-005, NFR-002

```gherkin
@US-002 @FR-004 @FR-005 @NFR-002 @AC-004
Feature: Sincronização por documento

  Scenario: Mesmo arquivo enviado de novo
    Given a coleção "manuais" com "a.md" indexado em 12 chunks
    When uma owner envia de novo o mesmo "a.md", sem alterações
    Then o envio termina com previstos 12, inseridos 0, mantidos 12, removidos 0
    And nenhum embedding é gerado
    And a coleção continua com 12 chunks de "a.md" e o mesmo identificador de documento
```

#### AC-005 — Arquivo de mesmo nome com conteúdo novo substitui a versão

**Cobre**: US-002, FR-004, FR-005, FR-006

```gherkin
@US-002 @FR-004 @FR-005 @FR-006 @AC-005
Feature: Sincronização por documento

  Scenario: Nova versão de um documento
    Given a coleção "manuais" com "a.md" em 12 chunks e "b.md" em 5 chunks
    When uma owner envia "a.md" com uma seção alterada, usando divisão por caracteres
    Then "a.md" passa a ter somente os chunks da nova versão
    And os chunks antigos de "a.md" que não existem na nova versão são removidos
    And "b.md" continua com os mesmos 5 chunks
    And a linha de "a.md" mostra a divisão por caracteres e a data deste envio
```

#### AC-006 — Identidade não depende da pasta temporária

**Cobre**: US-002, FR-004, FR-005, NFR-002

```gherkin
@US-002 @FR-004 @FR-005 @NFR-002 @AC-006
Feature: Identidade estável de documento

  Scenario Outline: Identidade do documento
    Given o worker materializa o envio em uma pasta temporária com nome aleatório
    When o arquivo "a.md" é processado <condicao>
    Then o identificador do documento é <resultado>

    Examples:
      | condicao | resultado |
      | duas vezes na coleção "manuais" | o mesmo nos dois envios |
      | na coleção "manuais" e na coleção "politicas" | diferente entre as duas coleções |
      | com document_id "doc-42" no frontmatter | "doc-42" |
```

#### AC-007 — Envio que falha não altera documentos

**Cobre**: US-002, FR-005, FR-012, NFR-004

```gherkin
@US-002 @FR-005 @FR-012 @NFR-004 @AC-007
Feature: Sincronização por documento

  Scenario: Falha do Qdrant durante o envio
    Given a coleção "manuais" com "a.md" em 12 chunks
    And o Qdrant recusa gravações
    When uma owner envia uma nova versão de "a.md"
    Then o envio fica com situação "falhou" e mensagem segura, sem chave nem detalhe do provedor
    And o registro de "a.md" continua com 12 chunks e a data do envio anterior
    And a ação "Repetir" fica disponível para owner e admin
```

#### AC-008 — Ver documentos e chunks da coleção

**Cobre**: US-003, FR-008, FR-015, NFR-003

```gherkin
@US-003 @FR-008 @FR-015 @NFR-003 @AC-008
Feature: Detalhe da coleção

  Scenario: Member consulta os documentos
    Given a coleção "manuais" com "a.md" e "b.md"
    When um member abre a coleção
    Then a aba "Documentos" está ativa e mostra ID, nome do arquivo, chunks, divisão usada e último envio
    And não aparecem "Adicionar documentos", "Substituir", "Apagar" nem "Renomear"
    When ele ativa a linha de "a.md" pelo teclado
    Then um painel lateral somente leitura lista os chunks de "a.md" e devolve o foco à linha ao fechar
```

#### AC-009 — Histórico de envios

**Cobre**: US-003, FR-012, FR-009

```gherkin
@US-003 @FR-012 @FR-009 @AC-009
Feature: Detalhe da coleção

  Scenario: Aba Envios mostra cada envio
    Given a coleção "manuais" recebeu 3 envios, o último com falha
    When uma owner abre a aba "Envios"
    Then vê os 3 envios do mais recente ao mais antigo, com arquivos, divisão, situação, contagens, autor e datas
    And o envio com falha mostra a mensagem segura e a ação "Repetir"
    And ao abrir um envio a tela de detalhe acompanha o progresso enquanto ele está em processamento
```

#### AC-010 — Apagar um documento

**Cobre**: US-004, FR-009, FR-015, NFR-004

```gherkin
@US-004 @FR-009 @FR-015 @NFR-004 @AC-010
Feature: Remoção de documento

  Scenario: Owner apaga um documento obsoleto
    Given a coleção "manuais" com "a.md" em 12 chunks e "b.md" em 5 chunks
    When uma owner escolhe "Apagar" em "a.md"
    Then a confirmação informa que 12 chunks serão removidos
    When ela confirma
    Then "a.md" sai da lista e seus 12 chunks saem do Qdrant
    And "b.md" continua com 5 chunks
    And a aba "Envios" continua listando o envio que trouxe "a.md"
```

#### AC-011 — Falha ao apagar documento preserva o registro

**Cobre**: US-004, FR-009, NFR-001, NFR-004

```gherkin
@US-004 @FR-009 @NFR-001 @NFR-004 @AC-011
Feature: Remoção de documento

  Scenario: Qdrant indisponível ao apagar
    Given a coleção "manuais" com "a.md"
    And o Qdrant está indisponível
    When uma owner confirma apagar "a.md"
    Then o diálogo mostra "Não foi possível apagar o documento. Tente novamente." sem fechar
    And "a.md" continua na lista
    And nenhuma resposta nem log contém a chave da conexão
```

#### AC-012 — Member não apaga nem envia

**Cobre**: US-004, US-001, FR-010, FR-011, FR-015, NFR-001

```gherkin
@US-004 @US-001 @FR-010 @FR-011 @FR-015 @NFR-001 @AC-012
Feature: Permissões de coleção

  Scenario Outline: Member tenta ação de escrita pela API
    Given um member autenticado no projeto da coleção "manuais"
    When ele chama <acao>
    Then recebe 403 e nada muda

    Examples:
      | acao |
      | o envio de documentos para "manuais" |
      | a exclusão de "a.md" |
      | a renomeação de "manuais" |
      | a exclusão de "manuais" |
```

#### AC-013 — Renomear coleção

**Cobre**: US-005, FR-010, FR-001

```gherkin
@US-005 @FR-010 @FR-001 @AC-013
Feature: Ciclo de vida da coleção

  Scenario: Renomear só muda o nome exibido
    Given a coleção "manuais" com nome físico gravado na criação
    When uma admin renomeia para "manuais técnicos"
    Then o Workspace e o detalhe mostram "manuais técnicos"
    And o nome físico no Qdrant continua o mesmo e a consulta devolve os mesmos chunks
    When ela tenta renomear para o nome de outra coleção do Workspace
    Then vê "Já existe uma coleção com esse nome neste Workspace." e o nome não muda
```

#### AC-014 — Apagar coleção com confirmação por nome

**Cobre**: US-005, FR-011, FR-015

```gherkin
@US-005 @FR-011 @FR-015 @AC-014
Feature: Ciclo de vida da coleção

  Scenario: Owner apaga a coleção inteira
    Given a coleção "manuais" com 2 documentos e 17 chunks
    When uma owner escolhe "Apagar" na coleção
    Then o diálogo mostra o nome, 2 documentos e 17 chunks e mantém "Apagar" desabilitado
    When ela digita "manuais" e confirma
    Then a coleção física deixa de existir no Qdrant
    And a coleção, seus documentos, envios e arquivos guardados somem do Workspace
```

#### AC-015 — Falha ao apagar coleção não deixa estado parcial visível

**Cobre**: US-005, FR-011, NFR-004, NFR-001

```gherkin
@US-005 @FR-011 @NFR-004 @NFR-001 @AC-015
Feature: Ciclo de vida da coleção

  Scenario: Qdrant recusa a exclusão da coleção
    Given a coleção "manuais" e o Qdrant recusando a exclusão
    When uma owner confirma apagar "manuais"
    Then vê "Não foi possível apagar a coleção. Tente novamente." sem detalhe do provedor
    And a coleção continua listada e pode ser apagada de novo
```

#### AC-016 — Consultar a coleção inteira

**Cobre**: US-006, FR-013, FR-005

```gherkin
@US-006 @FR-013 @FR-005 @AC-016
Feature: Consulta por coleção

  Scenario: Consulta na aba e no assistente
    Given a coleção "manuais" com "a.md" e "b.md" e a coleção "politicas" com "c.md" no mesmo Workspace
    When um member pergunta na aba "Consulta" de "manuais"
    Then os chunks-fontes vêm somente de "a.md" e "b.md"
    And no assistente a escolha opcional lista coleções, e escolher "manuais" analisa a mesma coleção
```

#### AC-017 — Bases antigas descartadas e Workspace sem Bases

**Cobre**: US-006, FR-014, FR-013

```gherkin
@US-006 @FR-014 @FR-013 @AC-017
Feature: Descarte do modelo de Base

  Scenario: Operador descarta as Bases e a interface usa só coleções
    Given existem Bases ativas de teste com pontos no Qdrant
    When o operador executa o comando de descarte de Bases
    Then cada Base ativa tem seus pontos e arquivos removidos e fica marcada como apagada pelo caminho de exclusão existente
    And nenhuma tabela é apagada ou truncada
    And a tela do Workspace lista coleções, sem "Nova Base"
    And as rotas de API de Base deixam de existir
```

#### AC-018 — Workspace com coleções não pode ser apagado

**Cobre**: US-006, FR-014, FR-001

```gherkin
@US-006 @FR-014 @FR-001 @AC-018
Feature: Descarte do modelo de Base

  Scenario: Apagar Workspace com coleção ativa
    Given o Workspace "Clientes" com a coleção "manuais"
    When uma owner tenta apagar o Workspace
    Then vê "Workspace possui coleções ativas. Apague as coleções antes de continuar."
    And o Workspace continua listado
```

#### AC-019 — Isolamento entre tenants e Workspaces

**Cobre**: NFR-001, FR-013, FR-008, FR-010

```gherkin
@NFR-001 @FR-013 @FR-008 @FR-010 @AC-019
Feature: Isolamento de coleções

  Scenario Outline: Acesso fora do escopo
    Given a coleção "manuais" do tenant A
    When uma pessoa do tenant B chama <acao> para essa coleção
    Then recebe 404 sem revelar se a coleção existe

    Examples:
      | acao |
      | a leitura dos documentos |
      | a consulta |
      | a renomeação |
```

#### AC-020 — Custo de embeddings no reenvio misto

**Cobre**: NFR-002, FR-005, FR-006

```gherkin
@NFR-002 @FR-005 @FR-006 @AC-020
Feature: Sincronização por documento

  Scenario: Envio com arquivos novos, alterados e idênticos
    Given a coleção "manuais" com "a.md" em 12 chunks e "b.md" em 5 chunks
    When uma owner envia "a.md" idêntico, "b.md" com 1 chunk alterado e "c.md" novo com 4 chunks
    Then embeddings são gerados somente para o chunk alterado de "b.md" e os 4 chunks de "c.md"
```

#### AC-021 — Acessibilidade das telas da coleção

**Cobre**: NFR-003, FR-008, FR-002

```gherkin
@NFR-003 @FR-008 @FR-002 @AC-021
Feature: Acessibilidade

  Scenario: Navegação só por teclado
    Given o detalhe da coleção "manuais" aberto em 375 px e em 1280 px
    When uma pessoa navega só pelo teclado
    Then alcança as abas com as setas, as linhas com Tab e as ativa com Enter ou Espaço
    And a escolha entre "Coleção existente" e "Nova coleção" na Publicação é um grupo de opções rotulado
    And a verificação automática de acessibilidade não encontra violações nas telas da coleção
```

#### AC-022 — Estados vazios e de carregamento

**Cobre**: US-003, NFR-003, FR-008, FR-012, FR-014

```gherkin
@US-003 @NFR-003 @FR-008 @FR-012 @FR-014 @AC-022
Feature: Acessibilidade

  Scenario Outline: Estados da tela
    Given <estado>
    When uma owner abre <tela>
    Then vê <resultado>

    Examples:
      | estado | tela | resultado |
      | o Workspace sem coleções | o Workspace | "Nenhuma coleção ainda" com o botão "Enviar documentos" |
      | a coleção sem documentos | a aba Documentos | "Nenhum documento" com o botão "Adicionar documentos" |
      | a leitura em andamento | a aba Envios | linhas de carregamento anunciadas a leitores de tela |
      | a API indisponível | a aba Documentos | mensagem de erro com "Tentar novamente" |
      | as Bases antigas já descartadas | o Workspace | somente a lista de coleções, sem "Nova Base" nem Bases |
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve manter Coleções por Workspace, cada uma com nome exibido único no Workspace (sem diferenciar maiúsculas), nome físico no Qdrant gerado na criação e imutável, conexão de embeddings, conexão de Qdrant, autor e datas.
- **FR-002**: O fluxo de envio deve oferecer, na Publicação, "Coleção existente" (lista das coleções do Workspace) e "Nova coleção" (nome + conexões), e deve abrir com a coleção pré-selecionada quando iniciado por "Adicionar documentos" ou "Substituir" na coleção.
- **FR-003**: Um envio para coleção existente deve usar as conexões da coleção, recusar conexões diferentes e bloquear, antes de gravar, modelo cuja dimensão difira da coleção física.
- **FR-004**: O identificador do documento deve derivar da coleção e do nome do arquivo, ou do `document_id` do frontmatter quando presente, sem depender da pasta onde o arquivo é materializado.
- **FR-005**: Cada envio deve sincronizar cada documento enviado no escopo daquele documento: inserir chunks novos, manter chunks idênticos sem gerar embedding e remover chunks da versão anterior que não existem mais, sem alterar documentos que não foram enviados.
- **FR-006**: Cada envio deve guardar a divisão e o processamento escolhidos (estratégias da SPEC-0029), e cada documento deve mostrar a divisão e a data do envio que produziu sua versão atual.
- **FR-007**: A API e a interface de envio não devem aceitar nem exibir escolha de `sync_mode`.
- **FR-008**: O detalhe da coleção deve ter as abas Documentos, Envios e Consulta; a aba Documentos lista ID, nome do arquivo, chunks, divisão usada e último envio, e a linha abre um painel lateral somente leitura com os chunks do documento.
- **FR-009**: Apagar um documento deve remover do Qdrant somente os chunks daquele documento e seu registro, após confirmação com a quantidade de chunks, preservando o histórico de envios.
- **FR-010**: Renomear uma coleção deve alterar somente o nome exibido, respeitando a unicidade do FR-001.
- **FR-011**: Apagar uma coleção deve exigir a digitação do nome, apagar a coleção física no Qdrant e depois remover documentos, envios, consultas e arquivos guardados da coleção.
- **FR-012**: A aba Envios deve listar os envios da coleção com arquivos, divisão, situação, contagens, erro seguro, autor e datas, abrir o detalhe com acompanhamento de progresso e permitir repetir um envio que falhou.
- **FR-013**: A consulta deve operar sobre a coleção inteira, na aba Consulta e na escolha opcional do assistente, que passa a listar coleções em vez de Bases.
- **FR-014**: O sistema deve oferecer um comando operacional que descarta cada Base ativa pelo caminho de exclusão existente; as rotas e telas de Base devem ser removidas; e apagar um Workspace com coleções ativas deve ser bloqueado.
- **FR-015**: Somente owner e admin podem enviar, substituir, apagar documento, renomear e apagar coleção e repetir envio; member só lê e consulta.

#### Não funcionais

- **NFR-001**: Isolamento e sigilo: toda leitura e escrita de coleção, documento, envio e consulta é filtrada por tenant, projeto e Workspace, e nenhuma resposta, log ou tela expõe chaves de conexão. **Verificação**: testes de API com pessoas de outro tenant (404) e inspeção de respostas e logs capturados nos testes de falha.
- **NFR-002**: Custo: reenviar um arquivo idêntico gera 0 embeddings, e um envio misto gera embeddings somente para chunks novos ou alterados. **Verificação**: teste com provider de embeddings fake contando os textos enviados.
- **NFR-003**: Acessibilidade: telas da coleção e do envio operáveis só por teclado, com foco visível e devolvido ao fechar painéis e diálogos, sem overflow horizontal da página em 375 px. **Verificação**: testes Vitest com Testing Library e `vitest-axe`, mais revisão visual registrada na tarefa.
- **NFR-004**: Consistência: falha no Qdrant ou no worker não deixa registro local divergente; documento só muda de versão após a sincronização do documento concluir, e exclusões só removem registros locais depois de o Qdrant confirmar. **Verificação**: testes de integração com adapter que falha em pontos controlados.

#### Erros e casos-limite

- Nome de coleção vazio, só com espaços ou acima de 80 caracteres → envio recusado com mensagem associada ao campo.
- Dois arquivos com o mesmo nome no mesmo envio → envio recusado: "Há arquivos com o mesmo nome neste envio."
- Envio para coleção apagada entre a Prévia e a Publicação → 404 com "A coleção não existe mais."
- Envio ativo na coleção e novo envio pedido → aceito e enfileirado; envios da mesma coleção são processados um de cada vez.
- Apagar documento ou coleção enquanto há envio `queued` ou `running` na coleção → recusado com 409 e "Há um envio em processamento nesta coleção. Aguarde a conclusão para apagar."
- Coleção física ausente no Qdrant ao apagar documento ou coleção → tratada como já vazia, e os registros locais são removidos.
- Conexão da coleção desativada → envio, consulta e exclusão bloqueados com a mensagem de conexão desativada já existente.
- Documento com 0 chunks úteis após a divisão → o documento não é registrado e o envio informa o arquivo ignorado.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI em `src/app/` com SQLAlchemy, Alembic e Procrastinate; worker `process_base_task` em `src/app/tasks.py`; storage local ou R2 por chave (`src/app/storage.py`).
- Pipeline em `src/pipeline/`: `service.py` (fachada), `indexing.synchronize` com `LogicalScope(project_id, tenant_id)`, adapter Qdrant em `providers/vectorstores/qdrant.py`.
- Frontend Next.js em `frontend/` com shadcn/ui (base-nova) e ReUI; fluxo `FluxoIngestao` com quatro etapas e `useFluxoIngestao`.

#### Arquitetura e módulos

- **Escopo vetorial**: `scope_colecao(tenant, projeto, colecao_id)` substitui `scope_project_id(..., base_id)` como `project_id` lógico gravado em `metadata.project_id`. `LogicalScope` ganha `document_id: str | None`; `_scope_filter` do Qdrant acrescenta `metadata.document_id` quando presente.
- **Sincronização por documento**: novo caso de uso na fachada `service.sync_documents(config, chunks)` agrupa chunks por `document_id` e chama `synchronize(..., mode="mirror")` no escopo coleção + documento. Mantém o cálculo de embeddings só para ausentes.
- **Identidade**: `loader.py` passa a gravar `caminho_relativo` relativo à pasta de entrada (`file_path.relative_to(input_path)`), e `identity.assign_document_identity` deriva `document_id` de `(project_id lógico da coleção, caminho_relativo)`.
- **Exclusão de documento**: `service.delete_scope(config, document_id=...)`.
- **Exclusão de coleção**: `service.drop_collection(config)` → nova operação `drop()` no adapter Qdrant (`delete_collection`, 404 tratado como sucesso), autorizado por `SyncSafetyPolicy.assert_collection_drop_allowed(nome_fisico, prefixo)`, que só permite nomes com o prefixo de coleção do app.
- **Chunks do documento**: `service.list_document_chunks(config, document_id, limit)` via `scroll` com o filtro de escopo.
- **Consulta**: `service.query_base` recebe o escopo da coleção.
- **Nome físico**: `col-<workspace_id[:8]>-<colecao_id[:8]>`, gerado na criação.

#### Migrations

- `alembic/versions/0030_colecoes.py`: cria `colecoes`, `documentos_colecao` e `envios`; acrescenta `queries.colecao_id` (nullable) e torna `queries.base_id` nullable. Sem `DROP`, sem `TRUNCATE`; `bases` e `executions` permanecem como tabelas legadas. O downgrade remove somente o que esta revisão criou.

#### Models

- `Colecao` (`src/app/models.py`): `id`, `tenant_id`, `project_id`, `workspace_id` → `workspaces.id`, `nome`, `nome_normalizado`, `nome_fisico` (único), `conexao_embeddings_id`, `conexao_vector_store_id`, `dimensao`, `criado_por`, `criado_em`, `apagada_em`. Índice único parcial `(workspace_id, nome_normalizado)` onde `apagada_em IS NULL`.
- `DocumentoColecao`: `id`, `colecao_id`, `nome_arquivo`, `document_id`, `source_hash`, `chunks`, `chunking` (JSON), `ultimo_envio_id`, `atualizado_em`. Único `(colecao_id, nome_arquivo)`.
- `Envio`: `id`, `colecao_id`, `arquivos` (JSON), `processamento` (JSON), `metadados_chunk` (JSON), `situacao`, `etapa`, `previstos`, `inseridos`, `mantidos`, `removidos`, `erro`, `iniciado_em`, `concluido_em`, `criado_por`.

#### Controllers e casos de uso

- `src/app/routers/colecoes.py`: `GET /api/v1/workspaces/{id}/colecoes`, `GET|PATCH|DELETE /api/v1/colecoes/{id}`, `GET /api/v1/colecoes/{id}/documentos`, `GET /api/v1/colecoes/{id}/documentos/{doc_id}/chunks`, `DELETE /api/v1/colecoes/{id}/documentos/{doc_id}`, `GET /api/v1/colecoes/{id}/envios`, `POST /api/v1/colecoes/{id}/query`.
- `src/app/routers/envios.py`: `POST /api/v1/envios` (multipart: `colecao_id` ou `nova_colecao`, arquivos, processamento, metadados), `GET /api/v1/envios/{id}`, `POST /api/v1/envios/{id}/retry`.
- `src/app/colecoes.py`: regras de criação, unicidade, conexões fixas, dimensão, renomeação e exclusão.
- Removidos: `routers/bases.py`, `routers/executions.py` e `POST /bases/{id}/query` em `routers/queries.py`.
- `src/app/routers/assistente.py`: análise opcional passa a receber `colecao_id`.
- `src/app/descartar_bases.py` + comando `python -m src.app.descartar_bases`: percorre Bases ativas e aplica a rotina de exclusão existente (storage, `delete_scope`, remoção de execuções e consultas da Base, soft-delete).

#### Views e experiência

- Ver seção 10.

#### Queries e repositórios

- `src/app/repo.py`: `listar_colecoes(workspace)` com contagem de documentos, soma de chunks e último envio; `listar_documentos(colecao)` ordenado por nome; `listar_envios(colecao)` do mais recente ao mais antigo; `has_active_colecoes_for_workspace`. Todas filtram por tenant e projeto da identidade.

#### Jobs e processamento assíncrono

- `process_envio_task(envio_id)` substitui `process_base_task`: materializa os arquivos do envio, divide com o processamento do envio, chama `service.sync_documents` e atualiza `DocumentoColecao` documento a documento, só após a sincronização de cada documento. O job é enfileirado com `lock=f"colecao:{colecao_id}"` do Procrastinate, que serializa a execução dos envios da mesma coleção; `queueing_lock` não é usado porque recusaria o segundo envio em vez de enfileirá-lo. Repetir reutiliza os arquivos guardados.

#### Estrutura de arquivos

```text
specs/draft/0030-colecoes-por-workspace-com-envios-acumulados/
  spec.md
src/app/
  colecoes.py
  descartar_bases.py
  routers/colecoes.py
  routers/envios.py
src/pipeline/
  identity.py, loader.py, service.py, safety.py
  providers/vectorstores/base.py, qdrant.py
alembic/versions/0030_colecoes.py
frontend/src/app/(autenticado)/workspaces/[id]/
  page.tsx
  enviar/page.tsx
  colecoes/[colecaoId]/page.tsx
frontend/src/app/(autenticado)/envios/[id]/page.tsx
frontend/src/features/colecoes/
tests/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Colecao | `id` UUID | nome exibido 1–80 caracteres, único por Workspace sem diferenciar maiúsculas; `nome_fisico` imutável; conexões e dimensão fixas | N:1 Workspace; 1:N DocumentoColecao; 1:N Envio; 1:N Query |
| DocumentoColecao | `id` UUID; único `(colecao_id, nome_arquivo)` | `document_id` estável; `source_hash` da versão atual; `chunks` ≥ 1; `chunking` da versão atual | N:1 Colecao; N:1 Envio (último) |
| Envio | `id` UUID | situação `queued`/`running`/`succeeded`/`failed`; contagens ≥ 0; erro seguro | N:1 Colecao; referencia documentos por nome em `arquivos` |
| Query | `id` UUID | agora com `colecao_id`; `base_id` legado nullable | N:1 Colecao |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Envio | queued | worker inicia | running | um envio `running` por coleção |
| Envio | running | todos os documentos sincronizados | succeeded | contagens registradas |
| Envio | running | erro | failed | documentos já sincronizados mantêm a nova versão; os demais ficam inalterados |
| Envio | failed | Repetir | queued | reutiliza arquivos e processamento do envio |
| Colecao | ativa | apagar confirmado e Qdrant confirma | apagada | `apagada_em` preenchido; documentos, envios e consultas removidos |
| DocumentoColecao | presente | apagar confirmado e Qdrant confirma | removido | histórico de envios intacto |

#### Migração e retenção

- Sem migração de dados (decisão da Pergunta 2). As Bases atuais são descartadas pelo comando operacional (FR-014). Tabelas legadas ficam no schema.
- O histórico de envios permanece enquanto a coleção existir e sai com ela.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. Owner, admin e member usam o Workspace, o detalhe da coleção, o fluxo de envio e o detalhe do envio.

#### Stack e convenções de interface

- Next.js (App Router) + React + Tailwind v4 + shadcn/ui (base-nova, Base UI) + ReUI (`@reui/c-*`), `PageHeader` compartilhado, `DataGrid*` por domínio, `Sheet` para painéis e formulários curtos, diálogos de exclusão no padrão `ExcluirBaseDialog`, `apiJson` para HTTP, `getPapel()` para permissão. Testes com Vitest + Testing Library + `vitest-axe`.
- Telas atuais afetadas: `/workspaces/[id]` (lista Bases), `/workspaces/[id]/bases/nova` (fluxo), `/execucoes/[id]` (detalhe de execução), `/projeto` e o `SeletorBase` do assistente.

#### Telas e responsabilidades

- **Workspace** (`/workspaces/[id]`): lista as coleções e oferece Enviar documentos, Renomear e Apagar coleção.
- **Detalhe da coleção** (`/workspaces/[id]/colecoes/[colecaoId]`): abas Documentos, Envios e Consulta; ações Adicionar documentos, Renomear e Apagar.
- **Enviar documentos** (`/workspaces/[id]/enviar?colecao=<id>`): fluxo de quatro etapas; a Publicação escolhe ou cria a coleção.
- **Detalhe do envio** (`/envios/[id]`): progresso, contagens, erro e Repetir; substitui `/execucoes/[id]`.

#### Fluxo de informação e navegação

- Workspaces → Workspace → (linha) Detalhe da coleção → (linha) painel de chunks do documento.
- Workspace → Enviar documentos → Publicar → detalhe do envio → link "Ver coleção".
- Detalhe da coleção → Adicionar documentos ou Substituir → Enviar documentos com a coleção pré-selecionada.
- Aba Envios → (linha) detalhe do envio → "Voltar à coleção".
- Breadcrumb: `Workspaces / <Workspace> / <Coleção>`; no envio, `Workspaces / <Workspace> / Enviar documentos`; no detalhe do envio, `Workspaces / <Workspace> / <Coleção> / Envio`.

#### Menus e navegação principal

- Menu principal inalterado: Workspaces, Conexões e Pessoas (conforme papel). Coleções, envios e documentos são alcançados a partir do Workspace, por links das tabelas; não há item novo de menu.

#### Formulários e ações

- **Publicação**: grupo de opções "Coleção existente" | "Nova coleção". Existente: `Select` com as coleções do Workspace; conexões exibidas somente leitura. Nova: campo Nome (obrigatório, 1–80, ajuda "Nome visível no Workspace; pode ser alterado depois") e as duas conexões. A verificação de dimensão roda ao escolher. Botão Publicar desabilitado enquanto houver erro.
- **Renomear coleção** (`Sheet`): campo Nome com as mesmas regras; erro de duplicidade associado ao campo; valores preservados em falha.
- **Apagar documento** (diálogo): texto com o nome do arquivo e a quantidade de chunks; botão destrutivo.
- **Apagar coleção** (diálogo): nome, documentos e chunks; campo "Digite o nome da coleção para confirmar"; botão habilitado só com o nome exato.
- **Consulta**: campo de pergunta e botão Consultar; resultado com chunks-fontes, como na consulta atual.

#### Composição e disposição

- Workspace: `PageHeader` (título, descrição, ações) e `DataGridColecoes` em largura total.
- Detalhe da coleção: `PageHeader` com nome, conexões resumidas e ações; `Tabs` abaixo; cada aba ocupa a largura total. Em 375 px, as ações do cabeçalho quebram em linhas e as tabelas rolam horizontalmente dentro do próprio contêiner.
- Painel de chunks: `Sheet` à direita, `sm:max-w-xl`, lista rolável de chunks com seção e texto.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Workspace | `DataGridColecoes` | Lista coleções com ID, nome, documentos, chunks e último envio; ações Renomear e Apagar | `frontend/src/features/colecoes/DataGridColecoes.tsx` | Data Grid | ReUI | Novo, no padrão de `DataGridBases`, que é removido |
| Workspace / Detalhe | `RenomearColecaoSheet` | Formulário de nome exibido | `frontend/src/features/colecoes/RenomearColecaoSheet.tsx` | `Sheet`, `Input`, `Label` | shadcn/ui | Novo, no padrão de `WorkspaceFormSheet` |
| Workspace / Detalhe | `ApagarColecaoDialog` | Confirmação por digitação do nome | `frontend/src/features/colecoes/ApagarColecaoDialog.tsx` | `Dialog`, `Input` | shadcn/ui | Estende o padrão de `ExcluirBaseDialog` |
| Detalhe | `AbasColecao` | Alterna Documentos, Envios e Consulta, com a aba na URL (`?aba=`) | `frontend/src/features/colecoes/AbasColecao.tsx` | `Tabs` | shadcn/ui | Novo |
| Detalhe | `DataGridDocumentos` | Lista documentos; linha abre os chunks; ações Substituir e Apagar | `frontend/src/features/colecoes/DataGridDocumentos.tsx` | Data Grid | ReUI | Novo |
| Detalhe | `ChunksDocumentoSheet` | Chunks do documento, somente leitura | `frontend/src/features/colecoes/ChunksDocumentoSheet.tsx` | `Sheet`, `Skeleton`, `Alert` | shadcn/ui | Novo |
| Detalhe | `ApagarDocumentoDialog` | Confirmação com a quantidade de chunks | `frontend/src/features/colecoes/ApagarDocumentoDialog.tsx` | `Dialog` | shadcn/ui | Estende o padrão de `ExcluirBaseDialog` |
| Detalhe | `DataGridEnvios` | Histórico de envios; linha abre o detalhe do envio | `frontend/src/features/colecoes/DataGridEnvios.tsx` | Data Grid | ReUI | Novo |
| Detalhe | `ConsultaColecao` | Pergunta e chunks-fontes | `frontend/src/features/colecoes/ConsultaColecao.tsx` | `Textarea`, `Button`, `Alert` | shadcn/ui | Extrai a consulta existente da tela de Base |
| Enviar | `EtapaPublicacao` | Escolha ou criação de coleção | `frontend/src/features/ingestao/EtapaPublicacao.tsx` | `RadioGroup`, `Select`, `Input` | shadcn/ui | Estendido; remove `sync_mode` |
| Detalhe do envio | `DetalheEnvio` | Progresso, contagens, erro e Repetir | `frontend/src/features/envios/DetalheEnvio.tsx` | `Alert`, `Button`, `Spinner` | shadcn/ui | Adapta a tela de execução atual |
| Assistente | `SeletorColecao` | Escolha opcional da coleção para análise | `frontend/src/features/assistente/SeletorColecao.tsx` | `Select` | shadcn/ui | Substitui `SeletorBase` |
| Todas | `PageHeader` | Cabeçalho único | `frontend/src/components/PageHeader.tsx` | Próprio | Próprio | Reuso |

- Removidos: `DataGridBases`, `ExcluirBaseDialog` (padrão preservado nos novos diálogos), rota `bases/nova` e `SeletorBase`. `INTERFACE.md` é atualizado com cada bloco novo, removido ou estendido.

#### Estados e acessibilidade

- Carregando: linhas `Skeleton` com `aria-busy` e anúncio por `role="status"`.
- Vazio: Workspace sem coleções e coleção sem documentos ou envios com o botão de ação (só para owner e admin).
- Erro: `Alert` destrutivo com "Tentar novamente"; os diálogos mantêm o erro sem fechar.
- Sucesso: aviso curto após renomear, apagar ou publicar.
- Permissão: member não vê ações de escrita; a API devolve 403.
- Teclado: abas com setas; linhas com Enter e Espaço; painéis e diálogos prendem o foco, fecham com Esc e devolvem o foco ao elemento de origem.
- O breadcrumb usa `nav aria-label="Trilha"` e `aria-current="page"` na tela atual.

#### Contrato CRUD

- Coleção: criar (no envio), listar (Workspace), detalhar (abas), editar (Renomear) e apagar, todos com o mesmo `PageHeader`. Documento: listar, detalhar (painel), substituir e apagar; não há edição manual de conteúdo, porque editar é reenviar o arquivo.
- As listagens usam `DataGrid` em largura total, com coluna ID visível, linha inteira como link por mouse e teclado e ações independentes por linha.

#### Revisão visual durante o desenvolvimento

- Cada tarefa de interface confere bordas, espaçamentos, margens, padding, tipografia, alinhamento, overflow e foco em 375 px e 1280 px, nos temas claro e escuro, com conteúdo curto e longo (nomes de arquivo de 120 caracteres). A forma de conferência, o viewport, estados e ajustes ficam registrados no item `VISUAL` da tarefa.

#### APIs expostas

- `GET /api/v1/workspaces/{id}/colecoes` → `[{id, nome, documentos, chunks, ultimo_envio_em}]`.
- `GET /api/v1/colecoes/{id}` → coleção, nomes das conexões e dimensão; 404 fora do escopo.
- `PATCH /api/v1/colecoes/{id}` `{nome}` → 200; 409 por nome duplicado; 403 para member.
- `DELETE /api/v1/colecoes/{id}` `{confirmacao_nome}` → 204; 422 se o nome não confere; 409 com envio em processamento; 502 com mensagem segura quando o Qdrant recusa.
- `GET /api/v1/colecoes/{id}/documentos` → `[{id, nome_arquivo, chunks, chunking, ultimo_envio_em}]`.
- `GET /api/v1/colecoes/{id}/documentos/{doc_id}/chunks?limite=200` → `[{chunk_id, secao, texto}]`.
- `DELETE /api/v1/colecoes/{id}/documentos/{doc_id}` → 204; 409 com envio em processamento; 502 com mensagem segura quando o Qdrant recusa.
- `GET /api/v1/colecoes/{id}/envios` → lista de envios.
- `POST /api/v1/colecoes/{id}/query` `{pergunta, top_k}` → resultado com chunks-fontes.
- `POST /api/v1/envios` (multipart) → 201 `{envio_id, colecao_id}`; 409 por nome duplicado; 422 por `sync_mode`, conexões trocadas, dimensão incompatível ou arquivo repetido.
- `GET /api/v1/envios/{id}`, `POST /api/v1/envios/{id}/retry` → 202.
- Removidas: `/api/v1/bases*`, `/api/v1/executions*` e `/api/v1/bases/{id}/query`.

#### APIs externas utilizadas

- Qdrant via `qdrant-client` (já usado): `scroll`, `upsert`, `delete` por filtro e por IDs, `get_collection`, `create_collection` e o novo `delete_collection`. Os timeouts e tratamentos de erro seguem o adapter atual; 404 em `delete_collection` conta como sucesso.
- Embeddings OpenAI via conexão existente, sem mudança.

#### Documentação das APIs consultadas

- Nenhuma documentação externa nova; o uso de `delete_collection` segue a mesma assinatura do cliente já usado em `create_collection`.

#### Eventos e outros contratos

- Payload Qdrant: `metadata.project_id` = escopo da coleção; `metadata.document_id` estável; `metadata.nome_arquivo`. Job `process_envio_task(envio_id)` com `lock` por coleção.

### 11. Estratégia TDD

- **Unidade**: identidade (`tests/test_identity.py`), filtro de escopo com `document_id`, política de exclusão de coleção, regras de nome e unicidade.
- **Integração/contrato**: rotas de coleção e envio com banco de teste (`tests/conftest.py`) e adapter de vetor fake, worker `process_envio_task` com provider de embeddings que conta chamadas, descarte de Bases.
- **BDD/aceite**: os cenários AC-001 a AC-022 orientam os casos TDD; não há arquivos `.feature`.
- **Runner TDD**: Pytest no backend (`uv run pytest`); Vitest no frontend (`npm run test:tdd` em `frontend/`).
- **E2E**: Não aplicável; a jornada é coberta por testes de API e de componentes, com conferência manual pelo front no Delivery Gate.
- **Verificação manual**: revisão visual (seção 10) e um envio real contra o Qdrant local para confirmar a exclusão física da coleção.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-002, FR-004, AC-006 | AC-006 na seção 6 | `tests/test_identity.py::test_document_id_estavel_por_colecao_e_nome` | Observado em 2026-10-09: `document_id` muda com a pasta temporária | Pending | Pending |
| US-002, FR-005, NFR-002, AC-004 | AC-004 na seção 6 | `tests/test_app_envios_sync.py::test_reenvio_identico_nao_gera_embedding` | Observado em 2026-10-09: `POST /api/v1/envios` responde 404 | Pending | Pending |
| US-004, FR-009, AC-010 | AC-010 na seção 6 | `tests/test_app_colecoes_documentos.py::test_apagar_documento_remove_so_os_chunks_dele` | Observado em 2026-10-09: rota de coleção ausente (404) | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001, AC-003, AC-013, AC-018 | Integração | `tests/test_app_colecoes.py` | Pending |
| FR-002 | AC-001, AC-002, AC-021 | Integração + componente | `tests/test_app_envios.py`, `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Pending |
| FR-003 | AC-001, AC-002, AC-003 | Integração | `tests/test_app_envios.py` | Pending |
| FR-004 | AC-004, AC-005, AC-006 | Unidade | `tests/test_identity.py` | Pending |
| FR-005 | AC-004, AC-005, AC-006, AC-007, AC-016, AC-020 | Integração | `tests/test_app_envios_sync.py` | Pending |
| FR-006 | AC-001, AC-002, AC-005, AC-020 | Integração | `tests/test_app_envios.py` | Pending |
| FR-007 | AC-001, AC-002, AC-003 | Integração + componente | `tests/test_app_envios.py`, `EtapaPublicacao.test.tsx` | Pending |
| FR-008 | AC-008, AC-019, AC-021, AC-022 | Componente + integração | `frontend/src/features/colecoes/*.test.tsx`, `tests/test_app_colecoes.py` | Pending |
| FR-009 | AC-009, AC-010, AC-011 | Integração + componente | `tests/test_app_colecoes_documentos.py`, `ApagarDocumentoDialog.test.tsx` | Pending |
| FR-010 | AC-012, AC-013, AC-019 | Integração + componente | `tests/test_app_colecoes.py`, `RenomearColecaoSheet.test.tsx` | Pending |
| FR-011 | AC-012, AC-014, AC-015 | Integração + componente | `tests/test_app_colecoes.py`, `ApagarColecaoDialog.test.tsx` | Pending |
| FR-012 | AC-007, AC-009, AC-022 | Integração + componente | `tests/test_app_envios.py`, `DataGridEnvios.test.tsx` | Pending |
| FR-013 | AC-016, AC-017, AC-019 | Integração | `tests/test_app_colecoes_query.py` | Pending |
| FR-014 | AC-017, AC-018, AC-022 | Integração | `tests/test_app_descartar_bases.py` | Pending |
| FR-015 | AC-001, AC-008, AC-010, AC-012, AC-014 | Integração | `tests/test_app_colecoes_permissoes.py` | Pending |
| NFR-001 | AC-011, AC-012, AC-015, AC-019 | Integração | `tests/test_app_colecoes_permissoes.py` | Pending |
| NFR-002 | AC-004, AC-006, AC-020 | Integração | `tests/test_app_envios_sync.py` | Pending |
| NFR-003 | AC-008, AC-021, AC-022 | Componente (axe) | `frontend/src/features/colecoes/*.a11y.test.tsx` | Pending |
| NFR-004 | AC-003, AC-007, AC-010, AC-011, AC-015 | Integração | `tests/test_app_colecoes_falhas.py` | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (2026-10-09)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0030-colecoes-por-workspace-com-envios-acumulados/spec.md`
- **Cobertura**: 6 US, 15 FR, 4 NFR, 22 AC; todos os US, FR e NFR com 3 ou mais AC em `**Cobre**`; a feature inteira com 22 AC.
- **Achados**:
- **FIND-ARCH-001** [P2] [Resolved] o plano usava `queueing_lock`, que recusa o segundo job em vez de serializá-lo — Refs: FR-005, FR-012 — Evidence: src/app/tasks.py — Effect: o segundo envio para a mesma coleção falharia ao enfileirar — Suggestion: usar `lock` por coleção; corrigido na seção 8 (Jobs) e na seção 10 (Eventos).
- **FIND-PROD-001** [P2] [Resolved] apagar documento ou coleção durante um envio em processamento não tinha comportamento definido — Refs: FR-009, FR-011, NFR-004 — Evidence: src/app/routers/bases.py — Effect: o worker poderia regravar chunks de um documento apagado — Suggestion: recusar com 409; corrigido em Erros e casos-limite e nas APIs expostas.
- **FIND-PROD-002** [P2] [Resolved] a Definition of Done não citava os contextos afetados pela mudança de persistência, capacidade e interface — Refs: FR-001, FR-014 — Evidence: .specsfy/DATABASE.md — Effect: a entrega poderia fechar com o contexto desatualizado — Suggestion: incluir `DATABASE.md`, `PROJECT.md`, `INTERFACE.md` e o documentador na seção 18; corrigido.
- **FIND-ARCH-002** [P3] [Resolved] o exemplo de dimensão incompatível em AC-003 contradizia as conexões travadas — Refs: FR-003 — Evidence: src/app/routers/conexoes.py — Effect: cenário impossível no teste — Suggestion: descrever a conexão alterada depois da criação; corrigido.
- **FIND-SEC-001** [P3] [Accepted] a exclusão física de coleção é uma operação remota irreversível — Refs: FR-011, NFR-001 — Evidence: src/pipeline/safety.py — Effect: perda de vetores se acionada por engano — Suggestion: manter a confirmação por nome, o papel owner/admin e a restrição ao prefixo `col-`; aceita pela DEC-005.
- Suposições da seção 16 (permissões, unicidade de nome, bloqueio de Workspace, limite de 200 chunks, serialização por coleção) seguem regras já vigentes ou são defaults reversíveis; nenhuma muda escopo, dados ou segurança de forma material.

#### Gate do Ato II — Plano

- **Resultado**: READY (2026-10-09)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0030-colecoes-por-workspace-com-envios-acumulados/spec.md`
- **Cobertura**: 38 tarefas (24 `[TEST] [TDD]` com RED observado, 11 `[CODE]`, 2 `[DOC]` e 1 `[TEST]` de regressão); 47/47 IDs (6 US, 15 FR, 4 NFR, 22 AC) cobertos; interface nas tarefas OK.
- **Achados**:
- **FIND-PLAN-001** [P3] [Accepted] a spec cita `vitest-axe`, mas o projeto só tem `axe-core` — Refs: NFR-003 — Evidence: frontend/package.json — Effect: o teste de acessibilidade usa `axe-core` direto, como `AssistentePainel.a11y.test.tsx` — Suggestion: manter `axe-core` sem nova dependência.
- **FIND-PLAN-002** [P3] [Resolved] `tests/test_spec_markers.py` reprovava a SPEC-0029 concluída por causa de uma palavra portuguesa que o validador confunde com marcador pendente — Refs: PR-006 — Evidence: specs/completed/0029-expor-configuracoes-do-processamento-no-front/spec.md — Effect: a regressão falhava por texto, não por código — Suggestion: frase reescrita na T029; a trava local passou a ficar verde.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0030-colecoes-por-workspace-com-envios-acumulados/spec.md .`
- **Achados**: Pending.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 o caso `test_primeiro_envio_cria_colecao_com_conexoes_e_sem_sync_mode` falhando em tests/test_app_envios.py — Refs: US-001, FR-001, FR-002, FR-003, FR-006, FR-007, FR-015, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: `POST /api/v1/envios` responde 404 (rota ausente) e a coleção não existe.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 o caso `pré-seleciona a coleção e trava as conexões na Publicação` falhando em frontend/src/features/ingestao/EtapaPublicacao.test.tsx — Refs: US-001, FR-002, FR-003, FR-006, FR-007, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `npx vitest run src/features/colecoes src/features/ingestao/EtapaPublicacao.test.tsx (8 failed, 8 passed pré-existentes)`: a Publicação não tem o `radiogroup` "Coleção existente" / "Nova coleção" nem recebe `colecaoInicial`.
  - [x] **IMPROVE**: Cobertura revisada; componente ausente carregado por `exigir`, sem rede. A verificação de acessibilidade usa `axe-core` (já instalado), pois `vitest-axe` não está nas dependências.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 o caso `test_envio_invalido_e_recusado_antes_de_gravar` falhando em tests/test_app_envios.py — Refs: US-001, FR-001, FR-003, FR-007, NFR-004, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: `POST /api/v1/envios` responde 404; nenhuma das quatro recusas existe.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T004 [TEST] [TDD] [US-002] Derivar do AC-004 o caso `test_reenvio_identico_nao_gera_embedding` falhando em tests/test_app_envios_sync.py — Refs: US-002, FR-004, FR-005, NFR-002, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: o envio não existe (404), logo não há sincronização por documento nem contagem de embeddings.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-005 o caso `test_nova_versao_substitui_so_o_documento` falhando em tests/test_app_envios_sync.py — Refs: US-002, FR-004, FR-005, FR-006, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: o envio não existe (404); sem escopo por documento, a versão antiga não seria substituída.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 o caso `test_document_id_estavel_por_colecao_e_nome` falhando em tests/test_identity.py — Refs: US-002, FR-004, FR-005, NFR-002, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: `document_id` muda com a pasta temporária: `caminho_relativo` inclui `base-<id>-XXXX`.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 o caso `test_falha_do_qdrant_preserva_documento_e_permite_repetir` falhando em tests/test_app_colecoes_falhas.py — Refs: US-002, FR-005, FR-012, NFR-004, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: `POST /api/v1/envios` responde 404; `process_envio_task` e o Repetir do envio não existem.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T008 [TEST] [TDD] [US-003] Derivar do AC-008 o caso `member vê documentos sem ações e abre os chunks pelo teclado` falhando em frontend/src/features/colecoes/DataGridDocumentos.test.tsx — Refs: US-003, FR-008, FR-015, NFR-003, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `npx vitest run src/features/colecoes src/features/ingestao/EtapaPublicacao.test.tsx (8 failed, 8 passed pré-existentes)`: `@/features/colecoes/DataGridDocumentos` ainda não existe.
  - [x] **IMPROVE**: Cobertura revisada; componente ausente carregado por `exigir`, sem rede. A verificação de acessibilidade usa `axe-core` (já instalado), pois `vitest-axe` não está nas dependências.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-009 o caso `lista envios do mais recente ao mais antigo com Repetir` falhando em frontend/src/features/colecoes/DataGridEnvios.test.tsx — Refs: US-003, FR-012, FR-009, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `npx vitest run src/features/colecoes src/features/ingestao/EtapaPublicacao.test.tsx (8 failed, 8 passed pré-existentes)`: `@/features/colecoes/DataGridEnvios` ainda não existe.
  - [x] **IMPROVE**: Cobertura revisada; componente ausente carregado por `exigir`, sem rede. A verificação de acessibilidade usa `axe-core` (já instalado), pois `vitest-axe` não está nas dependências.

- [x] T010 [TEST] [TDD] [US-004] Derivar do AC-010 o caso `test_apagar_documento_remove_so_os_chunks_dele` falhando em tests/test_app_colecoes_documentos.py — Refs: US-004, FR-009, FR-015, NFR-004, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: a coleção e a rota `DELETE /colecoes/{id}/documentos/{doc_id}` não existem (404).
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T011 [TEST] [TDD] [US-004] Derivar do AC-011 o caso `mantém o diálogo aberto com erro seguro quando o Qdrant falha` falhando em frontend/src/features/colecoes/ApagarDocumentoDialog.test.tsx — Refs: US-004, FR-009, NFR-001, NFR-004, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `npx vitest run src/features/colecoes src/features/ingestao/EtapaPublicacao.test.tsx (8 failed, 8 passed pré-existentes)`: `@/features/colecoes/ApagarDocumentoDialog` ainda não existe.
  - [x] **IMPROVE**: Cobertura revisada; componente ausente carregado por `exigir`, sem rede. A verificação de acessibilidade usa `axe-core` (já instalado), pois `vitest-axe` não está nas dependências.

- [x] T012 [TEST] [TDD] [US-004] Derivar do AC-012 o caso `test_member_recebe_403_nas_acoes_de_escrita` falhando em tests/test_app_colecoes_permissoes.py — Refs: US-004, US-001, FR-010, FR-011, FR-015, NFR-001, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: o envio e as rotas de coleção respondem 404 em vez de 403 para member.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T013 [TEST] [TDD] [US-005] Derivar do AC-013 o caso `test_renomear_so_muda_nome_exibido_e_respeita_unicidade` falhando em tests/test_app_colecoes.py — Refs: US-005, FR-010, FR-001, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: `PATCH /api/v1/colecoes/{id}` não existe (404).
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T014 [TEST] [TDD] [US-005] Derivar do AC-014 o caso `test_apagar_colecao_remove_fisica_e_registros` falhando em tests/test_app_colecoes.py — Refs: US-005, FR-011, FR-015, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: `DELETE /api/v1/colecoes/{id}` e `service.drop_collection` não existem (404).
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T015 [TEST] [TDD] [US-005] Derivar do AC-015 o caso `test_qdrant_recusa_exclusao_nao_deixa_estado_parcial` falhando em tests/test_app_colecoes_falhas.py — Refs: US-005, FR-011, NFR-004, NFR-001, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: a coleção não existe (404); sem exclusão com erro seguro de 502.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T016 [TEST] [TDD] [US-006] Derivar do AC-016 o caso `test_consulta_so_devolve_chunks_da_colecao` falhando em tests/test_app_colecoes_query.py — Refs: US-006, FR-013, FR-005, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: `POST /api/v1/colecoes/{id}/query` não existe (404).
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T017 [TEST] [TDD] [US-006] Derivar do AC-017 o caso `test_descarte_usa_exclusao_existente_e_rotas_de_base_somem` falhando em tests/test_app_descartar_bases.py — Refs: US-006, FR-014, FR-013, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: `src.app.descartar_bases` não existe e as rotas de Base ainda respondem.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T018 [TEST] [TDD] [US-006] Derivar do AC-018 o caso `test_workspace_com_colecao_nao_pode_ser_apagado` falhando em tests/test_app_colecoes.py — Refs: US-006, FR-014, FR-001, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: o Workspace só é bloqueado por Bases ativas; a coleção não existe (404).
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T019 [TEST] [TDD] Derivar do AC-019 o caso `test_outro_tenant_recebe_404` falhando em tests/test_app_colecoes_permissoes.py — Refs: FR-013, FR-008, FR-010, NFR-001, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: as rotas de coleção respondem 404 mesmo para a própria equipe; sem isolamento a provar.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T020 [TEST] [TDD] Derivar do AC-020 o caso `test_envio_misto_gera_embeddings_so_do_necessario` falhando em tests/test_app_envios_sync.py — Refs: FR-005, FR-006, NFR-002, AC-020 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py -q (24 failed)`: o envio não existe (404), logo não há envio misto nem contagem de embeddings.
  - [x] **IMPROVE**: Cobertura revisada; o caso usa dublês de embeddings e Qdrant na fronteira de `src.pipeline.indexing`, sem rede.

- [x] T021 [TEST] [TDD] Derivar do AC-021 o caso `alcança abas, linhas e grupo de opções só pelo teclado e passa no axe` falhando em frontend/src/features/colecoes/DetalheColecao.a11y.test.tsx — Refs: FR-008, FR-002, NFR-003, AC-021 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `npx vitest run src/features/colecoes src/features/ingestao/EtapaPublicacao.test.tsx (8 failed, 8 passed pré-existentes)`: `@/features/colecoes/AbasColecao` ainda não existe.
  - [x] **IMPROVE**: Cobertura revisada; componente ausente carregado por `exigir`, sem rede. A verificação de acessibilidade usa `axe-core` (já instalado), pois `vitest-axe` não está nas dependências.

- [x] T022 [TEST] [TDD] [US-003] Derivar do AC-022 o caso `mostra estados vazio, carregando e erro das telas da coleção` falhando em frontend/src/features/colecoes/EstadosColecao.test.tsx — Refs: US-003, FR-008, FR-012, FR-014, NFR-003, AC-022 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `npx vitest run src/features/colecoes src/features/ingestao/EtapaPublicacao.test.tsx (8 failed, 8 passed pré-existentes)`: `@/features/colecoes/DataGridColecoes` ainda não existe.
  - [x] **IMPROVE**: Cobertura revisada; componente ausente carregado por `exigir`, sem rede. A verificação de acessibilidade usa `axe-core` (já instalado), pois `vitest-axe` não está nas dependências.

- [x] T023 [TEST] [TDD] [US-005] Derivar do AC-014 o caso `habilita Apagar coleção só com o nome exato digitado` falhando em frontend/src/features/colecoes/ApagarColecaoDialog.test.tsx — Refs: US-005, FR-011, FR-015, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `npx vitest run src/features/colecoes src/features/ingestao/EtapaPublicacao.test.tsx (8 failed, 8 passed pré-existentes)`: `@/features/colecoes/ApagarColecaoDialog` ainda não existe.
  - [x] **IMPROVE**: Cobertura revisada; componente ausente carregado por `exigir`, sem rede. A verificação de acessibilidade usa `axe-core` (já instalado), pois `vitest-axe` não está nas dependências.

- [x] T024 [TEST] [TDD] [US-005] Derivar do AC-015 o caso `mostra o erro seguro e mantém o diálogo quando a exclusão falha` falhando em frontend/src/features/colecoes/ApagarColecaoDialog.test.tsx — Refs: US-005, FR-011, NFR-004, NFR-001, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: RED observado em 2026-10-09 com `npx vitest run src/features/colecoes src/features/ingestao/EtapaPublicacao.test.tsx (8 failed, 8 passed pré-existentes)`: `@/features/colecoes/ApagarColecaoDialog` ainda não existe.
  - [x] **IMPROVE**: Cobertura revisada; componente ausente carregado por `exigir`, sem rede. A verificação de acessibilidade usa `axe-core` (já instalado), pois `vitest-axe` não está nas dependências.

#### Fase 2 — Fundação: identidade, escopo e modelo (P1)

**Objetivo**: o pipeline sincroniza por documento com identidade estável e o banco guarda coleções, documentos e envios.
**Teste independente**: `uv run pytest tests/test_identity.py tests/test_app_colecoes.py tests/test_qdrant_sync.py -q`.

- [x] T025 [CODE] [US-002] Implementar identidade estável, escopo por documento, `sync_documents`, `delete_scope`, `drop_collection`, `list_document_chunks` e a política de exclusão de coleção em src/pipeline/identity.py, src/pipeline/loader.py, src/pipeline/indexing.py, src/pipeline/service.py, src/pipeline/safety.py, src/pipeline/providers/vectorstores/base.py e src/pipeline/providers/vectorstores/qdrant.py — Refs: US-002, FR-004, FR-005, FR-009, FR-011, NFR-002, NFR-004, AC-004, AC-005, AC-006, AC-020 — Depends: T004, T005, T006, T020
  - [x] **PREP**: RED confirmado em T004, T005, T006 e T020; `check_database_safety.mjs` SAFE; `$specsfy-documentator` reconstrói `docs/` antes do fechamento.
  - [x] **EXECUTE**: `LogicalScope.document_id`, filtro de escopo do Qdrant, `drop`/`scope_records`, `index_documents`, `service.sync_documents|delete_scope(document_id)|list_document_chunks|drop_collection`, `SyncSafetyPolicy.assert_collection_drop_allowed`, `caminho_relativo` relativo à pasta de entrada e ID de chunk sem o hash do arquivo inteiro.
  - [x] **VERIFY**: `uv run pytest tests/test_identity.py tests/test_pipeline_colecoes.py` 6 passed; `tests/test_chunker.py tests/test_loader.py tests/test_pipeline_service.py tests/test_qdrant_sync.py tests/test_qdrant_backend_operations.py tests/test_vectorstore_conformance.py tests/test_provider_boundaries.py` verdes.
  - [x] **VISUAL**: Não aplicável: a mudança é de pipeline e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN do AC-006 (`document_id` igual entre pastas temporárias, diferente entre coleções, `doc-42` do frontmatter) e dos testes unitários novos em `tests/test_pipeline_colecoes.py` (escopo por documento, sincronização por documento, apagar por documento, listar chunks, recusa de coleção sem prefixo `col-`). Arquivos: `src/pipeline/providers/contracts.py`, `src/pipeline/providers/vectorstores/base.py`, `src/pipeline/providers/vectorstores/qdrant.py`, `src/pipeline/indexing.py`, `src/pipeline/service.py`, `src/pipeline/safety.py`, `src/pipeline/loader.py`, `src/pipeline/identity.py`. `PROJECT.md` revisado com o parágrafo da SPEC-0030.
  - [x] **IMPROVE**: Descoberta durante o AC-020: o hash do arquivo inteiro entrava na chave do `chunk_id` e trocava o ID de todos os chunks a cada edição; foi removido da chave, para que só o chunk alterado gere embedding (a CLI reindexa uma vez, registrado no `PROJECT.md`).
  <!-- specsfy:evidence {"task": "T025", "refs": ["US-002", "FR-004", "FR-005", "FR-009", "FR-011", "NFR-002", "NFR-004", "AC-004", "AC-005", "AC-006", "AC-020"], "files": ["src/pipeline/identity.py", "src/pipeline/loader.py", "src/pipeline/indexing.py", "src/pipeline/service.py", "src/pipeline/safety.py", "src/pipeline/providers/contracts.py", "src/pipeline/providers/vectorstores/base.py", "src/pipeline/providers/vectorstores/qdrant.py"], "commands": [{"run": "uv run pytest tests/test_identity.py tests/test_pipeline_colecoes.py -q", "exit": 0}]} -->

- [x] T026 [CODE] [US-001] Criar a migration `0030_colecoes`, os modelos `Colecao`, `DocumentoColecao` e `Envio`, os repositórios e as regras de coleção (nome único, conexões fixas, dimensão, renomear e apagar) em alembic/versions/0030_colecoes.py, src/app/models.py, src/app/repo.py e src/app/colecoes.py — Refs: US-001, FR-001, FR-003, NFR-001, AC-001, AC-003, AC-013, AC-018 — Depends: T001, T003, T013, T018
  - [x] **PREP**: RED confirmado em T001, T003, T013 e T018; `check_database_safety.mjs` SAFE para os testes de migration e modelos.
  - [x] **EXECUTE**: Migration `0030_colecoes` (sem `DROP` nem `TRUNCATE` de tabelas existentes), modelos `Colecao`, `Envio` e `DocumentoColecao`, `Query.colecao_id` e `base_id` nullable, repositórios (`get_colecao_or_404`, `get_envio_or_404`, `list_colecoes_for_workspace`, `list_documentos_da_colecao`, `list_envios_da_colecao`, `has_active_colecoes_for_workspace`, `has_envio_ativo`) e `src/app/colecoes.py` (nome único sem diferenciar maiúsculas, nome físico `col-<ws8>-<col8>`, conexões fixas, dimensão).
  - [x] **VERIFY**: `uv run pytest tests/test_app_migrations.py tests/test_app_models.py` 8 passed; `test_alembic_upgrade_cria_schema_esperado` atualizado para a coluna `queries.colecao_id`.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: Schema criado pelo upgrade da revisão `0030_colecoes` e pelos modelos; as regras de coleção são exercitadas pelos testes de API de T027 (AC-001, AC-003) e T028. Arquivos: `alembic/versions/0030_colecoes.py`, `src/app/models.py`, `src/app/repo.py`, `src/app/colecoes.py`. `DATABASE.md` fica para a T036.
  - [x] **IMPROVE**: A validação de conexões e dimensão ficou em `exigir_envio_possivel`, reaproveitada pelo envio novo e pelo Repetir, sem duplicar a regra.


**Checkpoint**: o pipeline entrega a identidade estável e o schema novo existe, sem tocar tabelas legadas.
  <!-- specsfy:evidence {"task": "T026", "refs": ["US-001", "FR-001", "FR-003", "NFR-001", "AC-001", "AC-003", "AC-013", "AC-018"], "files": ["alembic/versions/0030_colecoes.py", "src/app/models.py", "src/app/repo.py", "src/app/colecoes.py"], "commands": [{"run": "uv run pytest tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}]} -->

#### Fase 3 — US-001 e US-002 Enviar sem duplicar (P1)

**Objetivo**: envios acumulam documentos numa coleção e reenvios somam, mantêm ou substituem por documento.
**Teste independente**: `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_app_colecoes_falhas.py -q`.

- [x] T027 [CODE] [US-001] Implementar `POST /api/v1/envios`, o detalhe e o retry, as rotas de leitura de coleção (lista, detalhe, documentos e envios) e o worker `process_envio_task` com `lock` por coleção, sem `sync_mode` em src/app/routers/envios.py, src/app/routers/colecoes.py, src/app/tasks.py, src/app/publicacao.py, src/app/main.py e src/app/colecoes.py — Refs: US-001, US-002, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-012, FR-015, NFR-002, NFR-004, AC-001, AC-003, AC-004, AC-005, AC-007, AC-020 — Depends: T001, T003, T004, T005, T007, T020, T025, T026
  - [x] **PREP**: RED confirmado em T001, T003, T004, T005, T007 e T020; dependência oculta tornada explícita: as rotas de leitura de coleção entram aqui porque os testes de AC-001 e AC-003 as consultam.
  - [x] **EXECUTE**: Router de envios (criar, detalhar, repetir), rotas de leitura de coleção, `process_envio_task` (sincronização por documento, registro da versão só após a confirmação do destino, erro seguro) e `agendar_envio` com `lock=colecao:<id>`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_app_colecoes_falhas.py tests/test_identity.py` verdes (a exclusão da coleção do AC-015 depende da T028); regressão `tests/test_app_tasks*.py tests/test_app_worker.py tests/test_application_boundaries.py tests/test_provider_boundaries.py` 72 passed.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN dos AC-001, AC-003 (quatro recusas), AC-004 (0 embeddings no reenvio idêntico), AC-005 (substituição só do documento enviado), AC-007 (falha mantém a versão e permite Repetir) e AC-020 (5 embeddings no envio misto). `docs/` reconstruído e `monitor_context.mjs --check` CURRENT; `PROJECT.md` revisado.
  - [x] **IMPROVE**: A falha do AC-020 revelou que o `chunk_id` dependia do hash do arquivo (corrigido na T025); `sync_mode` é recusado também dentro de `processamento.destino` e removido do que o envio guarda.


**Checkpoint**: enviar `a.md` duas vezes não duplica nem gera embedding, e uma nova versão substitui só aquele documento.
  <!-- specsfy:evidence {"task": "T027", "refs": ["US-001", "US-002", "FR-001", "FR-002", "FR-003", "FR-004", "FR-005", "FR-006", "FR-007", "FR-012", "FR-015", "NFR-002", "NFR-004", "AC-001", "AC-003", "AC-004", "AC-005", "AC-007", "AC-020"], "files": ["src/app/routers/envios.py", "src/app/routers/colecoes.py", "src/app/tasks.py", "src/app/publicacao.py", "src/app/main.py", "src/app/colecoes.py"], "commands": [{"run": "uv run pytest tests/test_app_envios.py tests/test_app_envios_sync.py tests/test_identity.py -q", "exit": 0}]} -->

#### Fase 4 — US-003, US-004 e US-005 Documentos, envios e ciclo de vida (P1/P2)

**Objetivo**: a API lê documentos, chunks e envios, apaga documento, renomeia e apaga coleção, com permissão e isolamento.
**Teste independente**: `uv run pytest tests/test_app_colecoes.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes_falhas.py -q`.

- [x] T028 [CODE] [US-004] Implementar as rotas de coleção, documentos, chunks, consulta, renomear e apagar (documento e coleção) com permissão por papel e isolamento por tenant em src/app/routers/colecoes.py, src/app/colecoes.py e src/app/repo.py — Refs: US-003, US-004, US-005, FR-008, FR-009, FR-010, FR-011, FR-012, FR-015, NFR-001, NFR-004, AC-010, AC-012, AC-013, AC-014, AC-015, AC-019 — Depends: T010, T012, T013, T014, T015, T019, T025, T026, T027
  - [x] **PREP**: RED confirmado em T010, T012, T013, T014, T015 e T019; rotas de leitura já criadas na T027; `check_database_safety.mjs` SAFE.
  - [x] **EXECUTE**: `PATCH /colecoes/{id}`, `DELETE /colecoes/{id}` (confirmação por nome, Qdrant confirma antes dos registros locais), `DELETE /colecoes/{id}/documentos/{doc}`, `GET .../chunks` e `POST /colecoes/{id}/query`; 409 com envio em processamento; 502 com mensagem segura; `configuracao_da_colecao` bloqueia conexão desativada.
  - [x] **VERIFY**: `uv run pytest tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_query.py` 13 passed e 1 failed esperado (AC-018, bloqueio do Workspace, é da T029).
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN dos AC-010 (só os chunks do documento saem e o histórico de envios permanece), AC-012 (member 403 nas quatro ações), AC-013 (renomear só o nome exibido, 409 por duplicidade), AC-014 (confirmação por nome, coleção física e registros removidos), AC-015 (502 seguro, coleção continua listada) e AC-019 (404 para outro tenant); a consulta (AC-016) já responde. `docs/` reconstruído, monitor CURRENT; `PROJECT.md` revisado na T027.
  - [x] **IMPROVE**: A exclusão registra em log só o tipo da exceção do Qdrant, para a chave não vazar; a consulta de coleção devolve 409 enquanto não houver documentos indexados.


**Checkpoint**: apagar um documento remove só os chunks dele e apagar a coleção remove a coleção física e os registros locais.
  <!-- specsfy:evidence {"task": "T028", "refs": ["US-003", "US-004", "US-005", "FR-008", "FR-009", "FR-010", "FR-011", "FR-012", "FR-015", "NFR-001", "NFR-004", "AC-010", "AC-012", "AC-013", "AC-014", "AC-015", "AC-019"], "files": ["src/app/routers/colecoes.py", "src/app/colecoes.py", "src/app/repo.py"], "commands": [{"run": "uv run pytest tests/test_app_colecoes_falhas.py tests/test_app_colecoes_documentos.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes_query.py -q", "exit": 0}]} -->

#### Fase 5 — US-006 Consulta por coleção e fim das Bases (P2)

**Objetivo**: consulta e assistente usam coleções; Bases antigas são descartadas e suas rotas somem.
**Teste independente**: `uv run pytest tests/test_app_colecoes_query.py tests/test_app_descartar_bases.py tests/test_app_workspaces.py tests/test_app_assistente.py -q`.

- [x] T029 [CODE] [US-006] Implementar o bloqueio de apagar Workspace com coleções, o comando `descartar_bases`, a análise do assistente por `colecao_id` e a remoção das rotas de Base, execução e consulta por Base em src/app/descartar_bases.py, src/app/routers/workspaces.py, src/app/routers/assistente.py, src/app/routers/comum.py, src/app/tasks.py, src/app/publicacao.py, src/app/repo.py e src/app/main.py — Refs: US-006, FR-013, FR-014, FR-005, FR-001, AC-016, AC-017, AC-018 — Depends: T016, T017, T018, T028
  - [x] **PREP**: RED confirmado em T016, T017 e T018; a consulta por coleção já respondia desde a T028 e o escopo da tarefa foi ampliado para o assistente e a faxina do modelo de Base, tornada explícita na linha da tarefa.
  - [x] **EXECUTE**: Rotas `/api/v1/bases*`, `/api/v1/executions*` e `/bases/{id}/query` removidas (`routers/bases.py`, `executions.py`, `queries.py`); `process_base_task` e `agendar_execucao` removidos; helpers movidos para `routers/comum.py`; `src/app/descartar_bases.py` aplica a exclusão antiga (arquivos, `delete_scope`, execuções, consultas, soft-delete) a cada Base ativa e relata falhas; apagar Workspace com coleção ativa devolve 409; o assistente recebe `colecao_id`; contagem de uso e exclusão de conexão consideram coleções; funções de repo sem uso removidas.
  - [x] **VERIFY**: Suíte completa do backend verde (ver EVIDENCE) e `uv run ruff check src tests` limpo. Testes de Base, execução, publicação e consulta por Base foram removidos ou portados para o envio e a coleção (`test_app_envios_validacao.py`, `test_app_tasks_conexoes.py`, `test_app_tasks_logging.py`, `test_app_worker.py`, `test_app_assistente.py`, `test_app_auth.py`, `test_app_authorship.py`).
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN dos AC-016 (consulta só devolve chunks da coleção), AC-017 (descarte usa a exclusão existente e as rotas de Base respondem 404) e AC-018 (Workspace com coleção não é apagado, 409). `docs/` reconstruído, `docs/architecture.md` e `docs/application.md` atualizados, monitor CURRENT.
  - [x] **IMPROVE**: `apagar coleção` aceita corpo ausente e responde 422 por nome divergente, para que member receba 403 e não 422; a exclusão de conexão passa a remover as linhas já apagadas de coleções e Bases que só guardavam a chave estrangeira.


**Checkpoint**: `/api/v1/bases*` e `/api/v1/executions*` respondem 404, e a consulta de `manuais` não devolve chunks de `politicas`.
  <!-- specsfy:evidence {"task": "T029", "refs": ["US-006", "FR-013", "FR-014", "FR-005", "FR-001", "AC-016", "AC-017", "AC-018"], "files": ["src/app/descartar_bases.py", "src/app/routers/workspaces.py", "src/app/routers/assistente.py", "src/app/routers/comum.py", "src/app/tasks.py", "src/app/publicacao.py", "src/app/repo.py", "src/app/main.py"], "commands": [{"run": "uv run pytest -q", "exit": 0}]} -->

#### Fase de interface

- [x] T030 [CODE] [US-001] Implementar a Publicação com "Coleção existente" ou "Nova coleção", conexões travadas e sem `sync_mode`, e a rota Enviar documentos com coleção pré-selecionada em frontend/src/features/ingestao/EtapaPublicacao.tsx, frontend/src/features/ingestao/useFluxoIngestao.ts, frontend/src/features/ingestao/FluxoIngestao.tsx, frontend/src/lib/ingestao.ts, frontend/src/features/colecoes/tipos.ts e frontend/src/app/(autenticado)/workspaces/[id]/enviar/page.tsx — Refs: US-001, FR-002, FR-006, FR-007, NFR-003, AC-002 — Depends: T002, T027
  - [x] **PREP**: RED confirmado em T002; `$specsfy-specialist-react-ui-components` instalado com autorização da pessoa e carregado; `INTERFACE.md`, `DESIGNSYSTEM.MD` e os blocos da Publicação lidos; a página do detalhe do envio (`/envios/[id]`) passa para a T033, que a implementa junto do `DetalheEnvio`. `$specsfy-documentator` reconstruiu `docs/`.
  - [x] **EXECUTE**: `EtapaPublicacao` com `fieldset role="radiogroup"` (Coleção existente | Nova coleção), `Select` nativo das coleções do Workspace com conexões travadas e mostradas só como resumo, nome (1–80) e conexões para a nova coleção, lote como único campo de Avançado; `useFluxoIngestao.publicar` envia `POST /api/v1/envios` sem `sync_mode`; rota `/workspaces/[id]/enviar?colecao=<id>` (com `Suspense` por causa de `useSearchParams`) substitui `/bases/nova`; `usar_base_preparada` passou a ser aceito pelo envio.
  - [x] **VERIFY**: `npx vitest run src/features/ingestao` 31 passed (inclui o AC-002); `npm run lint` limpo; teclado e validação do formulário cobertos pelos testes de `EtapaPublicacao`.
  - [x] **VISUAL**: Inspeção do DOM renderizado nos testes e do código contra `DESIGNSYSTEM.MD`, conferindo bordas (`rounded-lg border` da `dl` de resumo), espaçamentos e margens (`gap-4`, `gap-2`), padding (`p-3`) e tipografia (`text-sm`, `text-xs text-muted-foreground`): o grupo de opções, os rótulos, o `Select` (classe `seletor`), o `Input` e os botões usam as mesmas classes dos blocos vizinhos da Divisão; sem largura fixa, e as colunas viram uma só abaixo de `md`. A conferência no navegador em 375 px e 1280 px, nos temas claro e escuro, com nomes longos, fica com a pessoa responsável no T038.
  - [x] **EVIDENCE**: GREEN do AC-002 (coleção pré-selecionada, conexões travadas, sem modo de sincronização, `onPublicar` com `colecaoId`); testes antigos da Publicação adaptados (dimensão em linha e modo de sincronização removidos, nome da nova coleção, destino sem `sync_mode`, redirecionamento para `/envios/<id>`). Arquivos: `frontend/src/features/ingestao/EtapaPublicacao.tsx`, `useFluxoIngestao.ts`, `FluxoIngestao.tsx`, `frontend/src/lib/ingestao.ts`, `frontend/src/features/colecoes/tipos.ts` e a página `enviar`. `docs/` reconstruído, monitor CURRENT, `PROJECT.md` revisado na T027.
  - [x] **IMPROVE**: Os tipos de coleção, documento e envio ficaram em `features/colecoes/tipos.ts` para as próximas telas reaproveitarem; o resumo da Publicação mostra o nome das conexões nos dois modos, sem repetir a lista.
  <!-- specsfy:evidence {"task": "T030", "refs": ["US-001", "FR-002", "FR-006", "FR-007", "NFR-003", "AC-002"], "files": ["frontend/src/features/ingestao/EtapaPublicacao.tsx", "frontend/src/features/ingestao/useFluxoIngestao.ts", "frontend/src/features/ingestao/FluxoIngestao.tsx", "frontend/src/lib/ingestao.ts", "frontend/src/features/colecoes/tipos.ts", "frontend/src/app/(autenticado)/workspaces/[id]/enviar/page.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/ingestao", "exit": 0}]} -->

- [x] T031 [CODE] [US-005] Implementar a tela do Workspace com `DataGridColecoes`, `RenomearColecaoSheet` e `ApagarColecaoDialog`, e remover `DataGridBases` e `ExcluirBaseDialog` em frontend/src/app/(autenticado)/workspaces/[id]/page.tsx, frontend/src/features/colecoes/DataGridColecoes.tsx, frontend/src/features/colecoes/RenomearColecaoSheet.tsx, frontend/src/features/colecoes/ApagarColecaoDialog.tsx e frontend/src/features/workspaces/ExcluirWorkspaceDialog.tsx — Refs: US-005, US-003, FR-010, FR-011, FR-015, NFR-003, AC-014, AC-015 — Depends: T023, T024, T028, T029, T030
  - [x] **PREP**: RED confirmado em T023 e T024; `$specsfy-specialist-react-ui-components` carregado; `INTERFACE.md`, `DESIGNSYSTEM.MD`, `DataGridBases`, `ExcluirBaseDialog` e `WorkspaceFormSheet` lidos para reaproveitar o padrão; `PageHeader` reaproveitado.
  - [x] **EXECUTE**: `DataGridColecoes` (ID, Nome, Documentos, Chunks, Último envio, ações Renomear e Apagar independentes, linha como destino por teclado, estado vazio com "Enviar documentos"), `RenomearColecaoSheet` (PATCH, erro de duplicidade no campo), `ApagarColecaoDialog` (nome digitado, 502 com mensagem segura) e a página do Workspace listando coleções; `ExcluirWorkspaceDialog` passa a bloquear por coleções; `features/bases` removida e a rota antiga de nova Base já substituída na T030. O teste de autoria da lista de Workspaces foi preservado em `DataGridWorkspaces.test.tsx`.
  - [x] **VERIFY**: `npx vitest run` em `src/app/(autenticado)/workspaces`, `src/features/workspaces` e `ApagarColecaoDialog.test.tsx`: 31 passed + 16 passed; `npx eslint` limpo nos diretórios alterados.
  - [x] **VISUAL**: Inspeção do DOM renderizado nos testes e do código contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, conferindo bordas (contêiner `rounded-lg border` com `overflow-x-auto`), espaçamentos e margens (`gap-4`, `mt-1`), padding (células `px-3 py-2.5`, cabeçalho `bg-muted/40`) e tipografia (`text-sm`, `text-xs text-muted-foreground`, `font-medium`): tabelas, painel lateral e diálogos repetem as classes das listagens e diálogos já publicados, o `PageHeader` é o único cabeçalho, o foco usa `ring-2 ring-ring` e textos longos quebram por `[overflow-wrap:anywhere]`. A conferência no navegador em 375 px e 1280 px, nos temas claro e escuro, com nomes de arquivo de 120 caracteres, fica com a pessoa responsável no T038.
  - [x] **EVIDENCE**: GREEN dos AC-014 e AC-015 no diálogo (Apagar só habilita com o nome exato; falha mantém o diálogo com a mensagem segura). Arquivos: `frontend/src/features/colecoes/DataGridColecoes.tsx`, `RenomearColecaoSheet.tsx`, `ApagarColecaoDialog.tsx`, `frontend/src/app/(autenticado)/workspaces/[id]/page.tsx`, `frontend/src/features/workspaces/ExcluirWorkspaceDialog.tsx`. `docs/` reconstruído e monitor CURRENT.
  - [x] **IMPROVE**: O texto de ajuda do Workspace (formulário, lista vazia, descrição da página) deixou de falar em Bases, para não contradizer o novo vocabulário.
  <!-- specsfy:evidence {"task": "T031", "refs": ["US-005", "US-003", "FR-010", "FR-011", "FR-015", "NFR-003", "AC-014", "AC-015"], "files": ["frontend/src/app/(autenticado)/workspaces/[id]/page.tsx", "frontend/src/features/colecoes/DataGridColecoes.tsx", "frontend/src/features/colecoes/RenomearColecaoSheet.tsx", "frontend/src/features/colecoes/ApagarColecaoDialog.tsx", "frontend/src/features/workspaces/ExcluirWorkspaceDialog.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/workspaces src/features/colecoes/ApagarColecaoDialog.test.tsx", "exit": 0}]} -->

- [x] T032 [CODE] [US-004] Implementar o detalhe da coleção com `AbasColecao`, `DataGridDocumentos`, `ChunksDocumentoSheet` e `ApagarDocumentoDialog`, com Adicionar documentos, Substituir, Renomear e Apagar, e a trilha do shell em frontend/src/app/(autenticado)/workspaces/[id]/colecoes/[colecaoId]/page.tsx, frontend/src/features/colecoes/AbasColecao.tsx, frontend/src/features/colecoes/DataGridDocumentos.tsx, frontend/src/features/colecoes/ChunksDocumentoSheet.tsx, frontend/src/features/colecoes/ApagarDocumentoDialog.tsx, frontend/src/components/ui/tabs.tsx e frontend/src/app/(autenticado)/layout.tsx — Refs: US-003, US-004, FR-008, FR-009, FR-015, NFR-003, AC-008, AC-011 — Depends: T008, T011, T028, T031
  - [x] **PREP**: RED confirmado em T008 e T011; `$specsfy-specialist-react-ui-components` carregado; o primitive `Tabs` não existia e foi adicionado com `shadcn add tabs` (base-nova, sem dependência nova); `INTERFACE.md` e `DESIGNSYSTEM.MD` lidos; a trilha do shell (`layout.tsx`) ganhou as rotas de coleção, envio e enviar documentos.
  - [x] **EXECUTE**: Página do detalhe (carrega coleção, documentos e envios, faz polling enquanto há envio ativo, `Suspense` por causa de `useSearchParams`), `AbasColecao` com `Tabs` e a aba na URL (`?aba=`), `DataGridDocumentos` (linha abre o painel; Substituir leva ao envio com a coleção; Apagar com confirmação; foco devolvido à linha), `ChunksDocumentoSheet` somente leitura com carregando, vazio e erro, e `ApagarDocumentoDialog`. Para member não há ações de escrita.
  - [x] **VERIFY**: `npx vitest run` completo: 56 arquivos, 224 testes passando; `npm run lint` limpo; `npm run build` ok; teclado coberto (Enter na linha, Esc devolve o foco, setas nas abas).
  - [x] **VISUAL**: Inspeção do DOM renderizado nos testes e do código contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, conferindo bordas (contêiner `rounded-lg border` com `overflow-x-auto`), espaçamentos e margens (`gap-4`, `mt-1`), padding (células `px-3 py-2.5`, cabeçalho `bg-muted/40`) e tipografia (`text-sm`, `text-xs text-muted-foreground`, `font-medium`): tabelas, painel lateral e diálogos repetem as classes das listagens e diálogos já publicados, o `PageHeader` é o único cabeçalho, o foco usa `ring-2 ring-ring` e textos longos quebram por `[overflow-wrap:anywhere]`. A conferência no navegador em 375 px e 1280 px, nos temas claro e escuro, com nomes de arquivo de 120 caracteres, fica com a pessoa responsável no T038.
  - [x] **EVIDENCE**: GREEN dos AC-008 (member vê documentos sem ações e abre os chunks pelo teclado) e AC-011 (falha ao apagar mantém o diálogo com a mensagem segura), mais os testes novos da página (owner, member, 404) e a conferência com `axe-core` nas abas Documentos e Envios. Arquivos: a página do detalhe, `AbasColecao.tsx`, `DataGridDocumentos.tsx`, `ChunksDocumentoSheet.tsx`, `ApagarDocumentoDialog.tsx`, `components/ui/tabs.tsx` e `layout.tsx`. `docs/` reconstruído, monitor CURRENT.
  - [x] **IMPROVE**: A trilha do shell passou a cobrir Coleção, Envio e Enviar documentos com testes de nome longo e de link; `ChunksFontes` foi movido para `features/colecoes` e deixou de depender de `chunk_id`, que a API não envia.
  <!-- specsfy:evidence {"task": "T032", "refs": ["US-003", "US-004", "FR-008", "FR-009", "FR-015", "NFR-003", "AC-008", "AC-011"], "files": ["frontend/src/app/(autenticado)/workspaces/[id]/colecoes/[colecaoId]/page.tsx", "frontend/src/features/colecoes/AbasColecao.tsx", "frontend/src/features/colecoes/DataGridDocumentos.tsx", "frontend/src/features/colecoes/ChunksDocumentoSheet.tsx", "frontend/src/features/colecoes/ApagarDocumentoDialog.tsx", "frontend/src/components/ui/tabs.tsx", "frontend/src/app/(autenticado)/layout.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}]} -->

- [x] T033 [CODE] [US-003] Implementar `DataGridEnvios` e o `DetalheEnvio` com progresso, contagens, erro seguro e Repetir, e a página do envio em frontend/src/features/colecoes/DataGridEnvios.tsx, frontend/src/features/envios/DetalheEnvio.tsx e frontend/src/app/(autenticado)/envios/[id]/page.tsx — Refs: US-003, FR-012, NFR-003, AC-009 — Depends: T009, T027, T032
  - [x] **PREP**: RED confirmado em T009; `PainelProgresso` e a página `/execucoes/[id]` lidos para reaproveitar o padrão (etapa, situação, contagens, polling de 3 s) antes de removê-los; `PageHeader` reaproveitado.
  - [x] **EXECUTE**: `DataGridEnvios` (mais recente primeiro, ID, arquivos, divisão, situação, contagens, autor, data, erro seguro e Repetir só para owner/admin num envio que falhou), `DetalheEnvio` e a página `/envios/[id]` com polling enquanto o envio está na fila ou processando e o link Ver coleção; `features/execucoes` e a rota `/execucoes/[id]` removidas.
  - [x] **VERIFY**: `npx vitest run` completo 224 passed (inclui `DataGridEnvios.test.tsx`, `DetalheEnvio.test.tsx` e a página do envio); `npm run lint` e `npm run build` verdes.
  - [x] **VISUAL**: Inspeção do DOM renderizado nos testes e do código contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, conferindo bordas (contêiner `rounded-lg border` com `overflow-x-auto`), espaçamentos e margens (`gap-4`, `mt-1`), padding (células `px-3 py-2.5`, cabeçalho `bg-muted/40`) e tipografia (`text-sm`, `text-xs text-muted-foreground`, `font-medium`): tabelas, painel lateral e diálogos repetem as classes das listagens e diálogos já publicados, o `PageHeader` é o único cabeçalho, o foco usa `ring-2 ring-ring` e textos longos quebram por `[overflow-wrap:anywhere]`. A conferência no navegador em 375 px e 1280 px, nos temas claro e escuro, com nomes de arquivo de 120 caracteres, fica com a pessoa responsável no T038.
  - [x] **EVIDENCE**: GREEN do AC-009 (envios do mais recente ao mais antigo, mensagem segura e Repetir no que falhou, abertura do detalhe por teclado). Testes de autoria e de círculo de processamento da antiga tela de execução foram portados para `DetalheEnvio`. Arquivos: `DataGridEnvios.tsx`, `DetalheEnvio.tsx` e a página do envio. `docs/` reconstruído, monitor CURRENT.
  - [x] **IMPROVE**: `varianteDaSituacao` é compartilhada entre a lista e o detalhe do envio, para a mesma situação ter sempre a mesma cor e rótulo.
  <!-- specsfy:evidence {"task": "T033", "refs": ["US-003", "FR-012", "NFR-003", "AC-009"], "files": ["frontend/src/features/colecoes/DataGridEnvios.tsx", "frontend/src/features/envios/DetalheEnvio.tsx", "frontend/src/app/(autenticado)/envios/[id]/page.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}]} -->

- [x] T034 [CODE] [US-006] Implementar `ConsultaColecao` na aba Consulta e o `SeletorColecao` do assistente, removendo `SeletorBase`, com a listagem `GET /api/v1/colecoes` em frontend/src/features/colecoes/ConsultaColecao.tsx, frontend/src/features/colecoes/ChunksFontes.tsx, frontend/src/features/assistente/SeletorColecao.tsx, frontend/src/features/assistente/useAssistente.ts e src/app/routers/colecoes.py — Refs: US-006, FR-013, NFR-003, AC-016 — Depends: T016, T029, T032
  - [x] **PREP**: RED confirmado em T016; `FormularioConsulta` e `SeletorBase` lidos para reaproveitar o padrão; o assistente não tem Workspace em contexto, então a decisão registrada foi acrescentar `GET /api/v1/colecoes` (coleções de todos os Workspaces do projeto), coberta por `test_lista_colecoes_do_projeto_para_o_assistente`.
  - [x] **EXECUTE**: `ConsultaColecao` (pergunta em `Textarea`, resultado com autor e chunks-fontes numa região `role=status`, mensagem segura e pergunta preservada em falha, 409 explicado), `SeletorColecao` (rótulo Workspace · coleção, só Nenhuma quando a leitura falha), `useAssistente` enviando `colecao_id`; `FormularioConsulta` e `SeletorBase` removidos.
  - [x] **VERIFY**: `npx vitest run` completo 224 passed (`ConsultaColecao.test.tsx`, `SeletorColecao.test.tsx`, painel do assistente); `uv run pytest tests/test_app_colecoes.py tests/test_app_assistente.py` verdes; lint e build verdes.
  - [x] **VISUAL**: Inspeção do DOM renderizado nos testes e do código contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, conferindo bordas (contêiner `rounded-lg border` com `overflow-x-auto`), espaçamentos e margens (`gap-4`, `mt-1`), padding (células `px-3 py-2.5`, cabeçalho `bg-muted/40`) e tipografia (`text-sm`, `text-xs text-muted-foreground`, `font-medium`): tabelas, painel lateral e diálogos repetem as classes das listagens e diálogos já publicados, o `PageHeader` é o único cabeçalho, o foco usa `ring-2 ring-ring` e textos longos quebram por `[overflow-wrap:anywhere]`. A conferência no navegador em 375 px e 1280 px, nos temas claro e escuro, com nomes de arquivo de 120 caracteres, fica com a pessoa responsável no T038.
  - [x] **EVIDENCE**: GREEN do AC-016 no front: a consulta usa a coleção inteira, mostra `Consultada por` e os arquivos de origem e o assistente lista coleções em vez de Bases. Arquivos: `ConsultaColecao.tsx`, `ChunksFontes.tsx`, `SeletorColecao.tsx`, `useAssistente.ts` e `src/app/routers/colecoes.py`. `docs/` reconstruído, monitor CURRENT.
  - [x] **IMPROVE**: Textos de Conexões (descrição, detalhe e diálogo de exclusão) passaram de Bases para coleções, para o vocabulário bater com o backend.
  <!-- specsfy:evidence {"task": "T034", "refs": ["US-006", "FR-013", "NFR-003", "AC-016"], "files": ["frontend/src/features/colecoes/ConsultaColecao.tsx", "frontend/src/features/colecoes/ChunksFontes.tsx", "frontend/src/features/assistente/SeletorColecao.tsx", "frontend/src/features/assistente/useAssistente.ts", "src/app/routers/colecoes.py"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}]} -->

- [x] T035 [CODE] [US-003] Garantir acessibilidade por teclado, estados vazio, carregando e erro e ausência de overflow nas telas da coleção e do envio em frontend/src/features/colecoes/, frontend/src/features/ingestao/EtapaPublicacao.tsx e frontend/src/features/envios/ — Refs: US-003, FR-002, FR-008, FR-012, FR-014, NFR-003, AC-021, AC-022 — Depends: T021, T022, T030, T031, T032, T033, T034
  - [x] **PREP**: RED confirmado em T021 e T022; os componentes das tarefas anteriores já passam os testes de teclado e de estados, então esta tarefa audita o conjunto antes de fechar a fase de interface.
  - [x] **EXECUTE**: Auditoria de acessibilidade e de estados das telas da coleção e do envio com `axe-core` (abas, linhas, grupo de opções da Publicação) e testes de estado: vazio (Nenhuma coleção ainda, Nenhum documento, Nenhum envio ainda), carregando anunciado por `role=status`, erro com Tentar novamente e ausência de Nova Base; nenhum ajuste de código foi necessário além dos já feitos nas tarefas T030 a T034.
  - [x] **VERIFY**: `npx vitest run` completo: 56 arquivos, 224 testes; `DetalheColecao.a11y.test.tsx` e `EstadosColecao.test.tsx` verdes; `npm run lint` e `npm run build` verdes.
  - [x] **VISUAL**: Inspeção do DOM renderizado nos testes e do código contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, conferindo bordas (contêiner `rounded-lg border` com `overflow-x-auto`), espaçamentos e margens (`gap-4`, `mt-1`), padding (células `px-3 py-2.5`, cabeçalho `bg-muted/40`) e tipografia (`text-sm`, `text-xs text-muted-foreground`, `font-medium`): tabelas, painel lateral e diálogos repetem as classes das listagens e diálogos já publicados, o `PageHeader` é o único cabeçalho, o foco usa `ring-2 ring-ring` e textos longos quebram por `[overflow-wrap:anywhere]`. A conferência no navegador em 375 px e 1280 px, nos temas claro e escuro, com nomes de arquivo de 120 caracteres, fica com a pessoa responsável no T038.
  - [x] **EVIDENCE**: GREEN dos AC-021 (setas nas abas, linhas por Enter, grupo de opções rotulado, axe sem violações em Documentos, Envios e Publicação) e AC-022 (estados vazio, carregando, erro e Workspace sem Bases).
  - [x] **IMPROVE**: A conferência com axe foi acrescentada também ao teste da página do detalhe, para pegar regressões de conjunto, não só de componente.
  <!-- specsfy:evidence {"task": "T035", "refs": ["US-003", "FR-002", "FR-008", "FR-012", "FR-014", "NFR-003", "AC-021", "AC-022"], "files": ["frontend/src/features/colecoes/DetalheColecao.a11y.test.tsx", "frontend/src/features/colecoes/EstadosColecao.test.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}]} -->

#### Fase final — Documentação e qualidade

- [x] T036 [DOC] Registrar `colecoes`, `documentos_colecao`, `envios`, `queries.colecao_id` e a revisão `0030_colecoes` em .specsfy/DATABASE.md — Refs: FR-001, FR-005, FR-011, FR-014, NFR-004, AC-001, AC-013, AC-017 — Depends: T026, T027, T028, T029
  - [x] **PREP**: `.specsfy/DATABASE.md`, os modelos e a migration `0030_colecoes` lidos; contexto do monitor de persistência conferido.
  - [x] **EXECUTE**: `$specsfy-aux-database` aplicado: linhas novas de `colecoes`, `documentos_colecao` e `envios`, `queries.colecao_id` e `base_id` anulável, `bases`/`executions` marcadas como legado, `mensagens_assistente.base_id` agora guardando a coleção, e a cadeia de revisões Alembic estendida até `0030_colecoes`.
  - [x] **VERIFY**: `monitor_context.mjs --check` CURRENT e `build_documentation.mjs --check` sem pendência; as colunas conferidas contra `src/app/models.py`.
  - [x] **VISUAL**: Não aplicável: a tarefa só altera documentação.
  - [x] **EVIDENCE**: `.specsfy/DATABASE.md` atualizado; monitor CURRENT; `docs/` reconstruído.
  - [x] **IMPROVE**: A nota sobre `mensagens_assistente.base_id` evita que a coluna legada seja lida como Base, já que a API a expõe como `colecao_id`.

- [x] T037 [DOC] Registrar os blocos de coleção em INTERFACE.md e a mudança de modelo e de identidade da CLI em PROJECT.md — Refs: FR-002, FR-008, FR-013, FR-014, NFR-003, AC-016, AC-021, AC-022 — Depends: T030, T031, T032, T033, T034, T035
  - [x] **PREP**: `INTERFACE.md`, `PROJECT.md`, `docs/` e os arquivos de interface criados, alterados e removidos nas tarefas T030 a T035 lidos.
  - [x] **EXECUTE**: `INTERFACE.md` atualizado com finalidade, arquivo, API, estados, consumidores e regra de reaproveitamento de cada bloco novo (`DataGridColecoes`, `RenomearColecaoSheet`, `ApagarColecaoDialog`, `AbasColecao`, `DataGridDocumentos`, `ChunksDocumentoSheet`, `ApagarDocumentoDialog`, `DataGridEnvios`, `ConsultaColecao`, `ChunksFontes`, `DetalheEnvio`, `SeletorColecao`, `Tabs`), estendido (`EtapaPublicacao`, `FluxoIngestao`, `ExcluirWorkspaceDialog`, trilha do shell) e removido (`DataGridBases`, `ExcluirBaseDialog`, `PainelProgresso`, `FormularioConsulta`, `SeletorBase`); `PROJECT.md` descreve Coleções no lugar de Bases e a reindexação única da CLI; `docs/frontend.md` e `docs/architecture.md` ajustados; `$specsfy-documentator` executado.
  - [x] **VERIFY**: `build_documentation.mjs --check` e `monitor_context.mjs --check` sem pendência.
  - [x] **VISUAL**: Não aplicável: a tarefa só altera documentação.
  - [x] **EVIDENCE**: `INTERFACE.md`, `PROJECT.md`, `docs/frontend.md`, `docs/architecture.md` e `docs/application.md` atualizados; `docs/` reconstruído; monitor CURRENT. `PROJECT.md` revisado com impacto material (Coleções no lugar de Bases).
  - [x] **IMPROVE**: As linhas de componentes removidos foram apagadas em vez de marcadas como obsoletas, e as mensagens que citam o componente antigo dizem "substitui" apenas onde ajuda a achar o sucessor.

- [ ] T038 [TEST] Executar regressão, lint, tipos, build, rastreabilidade e a conferência visual e funcional pelo front, incluindo um envio real e a exclusão física da coleção no Qdrant local, em tests/test_app_envios_sync.py — Refs: US-001, US-002, US-003, US-004, US-005, US-006, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016, AC-017, AC-018, AC-019, AC-020, AC-021, AC-022 — Depends: T036, T037
  - [x] **PREP**: Suítes e checks identificados; `check_database_safety.mjs` SAFE para `uv run pytest -q` (Postgres de teste em `localhost:55432`).
  - [x] **EXECUTE**: `uv run ruff check .` sem achados; `uv run pytest -q` 529 passed, 1 skipped (uma primeira rodada, executada junto do build do front, falhou por falta de memória compartilhada do Postgres de teste; a repetição isolada passou); `npm run lint` limpo; `npx vitest run` 56 arquivos/224 testes; `npm run build` ok; `check_traceability.mjs --full-chain` 47/47 IDs em 135 arquivos; `build_documentation.mjs --check` e `monitor_context.mjs --check` CURRENT. Envio real contra um Qdrant 1.10.1 descartável (`docker run`, porta 16333, removido ao fim): `sync_documents` inseriu 5 chunks, o reenvio idêntico gerou 0 embeddings (3 mantidos), a nova versão do documento a inseriu 1, manteve 1 e removeu 2, `delete_scope(document_id)` apagou só os 2 chunks do documento b, `drop_collection` recusou `rag_docs` (fora do prefixo `col-`), apagou `col-teste030-real0001` do Qdrant e repetir com a coleção ausente passou.
  - [x] **VERIFY**: Sem gaps de rastreabilidade (47/47). A conferência no stack local da pessoa (migration `0030_colecoes`, `python -m src.app.descartar_bases` e um envio real com OpenAI) depende do deploy e fica registrada como pendente no VISUAL.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia, repassando a conferência visual final com a pessoa responsável nas telas Workspace, detalhe da coleção, Enviar documentos e detalhe do envio, em 375 px e 1280 px, nos temas claro e escuro.
  - [ ] **EVIDENCE**: Registrar contagens, comandos e o resultado da conferência no Gate do Ato III.
  - [ ] **IMPROVE**: Registrar a retrospectiva do processo.

### 15. Ordem de execução

- Caminho crítico: T001–T024 (RED) → T025 → T026 → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T034 → T035 → T036 → T037 → T038.
- Tarefas paralelas: Nenhuma marcada com `[P]`; T001–T024 escrevem casos independentes, mas vários compartilham arquivos de teste, e T031–T034 só avançam depois das rotas de T028.
- Estratégia de MVP: US-001 + US-002 + US-004 (T025–T028, T030 e T032) entregam o valor central; US-003, US-005 e US-006 completam o ciclo.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0029 (em andamento) deve estar concluída antes da implementação: ela altera o fluxo de envio, `tasks.py`, `ingestao.py`, `bases.py` e `qdrant.py`, e seus processamentos (seis estratégias, resumos, cabeçalhos, qualidade) são reaproveitados por envio.

#### Riscos

- Mudar `caminho_relativo` altera o `document_id` de bases indexadas pela CLI → registrar no `PROJECT.md` e no changelog que a primeira sincronização da CLI após a mudança reindexa uma vez; a CLI continua em `mirror` no seu próprio escopo e remove a versão antiga.
- Exclusão física de coleção por engano → confirmação por digitação do nome, política que só permite nomes com o prefixo `col-` do app e teste que impede apagar coleções fora do prefixo.
- Envio grande com muitos documentos falhar no meio → sincronização e registro por documento; Repetir reprocessa e mantém sem embedding o que já está igual.
- Remover rotas de Base quebra o assistente → `SeletorColecao` e a rota do assistente fazem parte desta entrega.

#### Suposições

- Permissões seguem a regra atual: owner e admin escrevem, member lê (confirmar na validação).
- O nome exibido da coleção é único dentro do Workspace, sem diferenciar maiúsculas, com até 80 caracteres.
- O nome físico segue `col-<workspace_id[:8]>-<colecao_id[:8]>`.
- Apagar Workspace com coleções ativas é bloqueado, mantendo a regra atual aplicada às Bases.
- O painel de chunks mostra até 200 chunks por documento.
- Envios da mesma coleção são processados um de cada vez.

### 17. Decisões

- **DEC-001**: A Coleção substitui a Base como unidade do Workspace — escolhida pela pessoa (Pergunta 1). Alternativas: Base como "envio" dentro da coleção, ou manter o nome Base. Trade-off: troca de vocabulário e de rotas em troca de um modelo único.
- **DEC-002**: Descartar as Bases sem migração — escolhida pela pessoa (Pergunta 2), por serem dados de teste. O descarte usa o caminho da aplicação para respeitar PR-002.
- **DEC-003**: Sincronizar em `mirror` no escopo de cada documento e remover `sync_mode` da interface — a escolha da pessoa (Pergunta 3) é implementada assim porque o `mirror` por documento entrega "somar, manter, substituir" sem tocar outros documentos.
- **DEC-004**: Nome exibido editável e nome físico fixo — escolhida pela pessoa (Pergunta 4); evita mover vetores.
- **DEC-005**: Apagar coleção remove a coleção física no Qdrant — escolhida pela pessoa (Pergunta 8). É a decisão explícita de operação remota destrutiva exigida pelos Limites do `PROJECT.md`, restrita ao prefixo do app.
- **DEC-006**: Divisão escolhida por envio, conexões fixas por coleção — declaração da pessoa ("posso usar documentos completamente diferentes"); a busca depende do mesmo modelo de embedding, não do mesmo tamanho de chunk.
- **DEC-007**: Identidade por coleção e nome do arquivo — corrige R-001; o `document_id` do frontmatter mantém precedência, preservando o contrato da SPEC-0002.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
- [ ] `.specsfy/DATABASE.md` reflete as tabelas `colecoes`, `documentos_colecao`, `envios`, a coluna `queries.colecao_id` e a revisão `0030_colecoes` (`$specsfy-aux-database`).
- [ ] `PROJECT.md` descreve Coleções por Workspace no lugar de Bases e o efeito da nova identidade de documento na CLI.
- [ ] `INTERFACE.md` registra os blocos novos, estendidos e removidos da seção 10.
- [ ] `docs/` e `.specsfy/PACKAGES.md` foram reconstruídos por `$specsfy-documentator`.
