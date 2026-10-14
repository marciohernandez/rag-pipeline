# Especificação integrada: Fase 1: recebimento e processamento de documentos até Markdown

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0023 |
| Slug | 0023-fase-1-recebimento-e-processamento-de-documentos-ate-markdown |
| Status | Planned |
| Effort | 7 |
| Effort updated at | 2026-09-28 |
| Effort rationale | Cinco formatos de extração (PDF, DOCX, PPTX, XLSX, imagem via OCR) mais normalização de formatos legados (DOC/PPT/XLS), duas tabelas novas, um router novo, um job periódico de retenção e uma superfície de interface nova (aba, Sheet, grid, painel de progresso por documento) — cruza `src/pipeline/`, `src/app/` e `frontend/`. Perfil `high`. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-14 |


## Ato I — Definir

### 1. Problema e resultado

#### Problema

Hoje o único ponto de entrada de conteúdo é `POST /api/v1/bases`, que exige arquivos `.md` já prontos (rejeita qualquer outra extensão e exige UTF-8 válido). Não existe nenhuma etapa que receba um documento original (PDF, PPT, DOC/DOCX, XLS/XLSX, imagem) e produza o Markdown que hoje precisa ser preparado manualmente antes do upload — o loader do pipeline (`src/pipeline/loader.py`) também só lê `.md` já existentes em uma pasta local.

#### Resultado desejado

Marcio e a equipe de consultoria enviam um ou mais documentos originais pela tela do Workspace e recebem automaticamente, em segundo plano, um Markdown estruturado por documento — pronto para seguir manualmente para o fluxo de Base já existente (Fase 2), sem preparação manual prévia.

#### Métricas de sucesso

- Um documento em qualquer um dos formatos aceitos (PDF, PPT, DOC/DOCX, XLS/XLSX, JPG/PNG) é convertido em `.md` sem intervenção manual, do envio ao download.
- Falha em um documento do lote nunca impede o download dos `.md` dos demais documentos do mesmo lote.
- Nenhum documento ou `.md` gerado fica acessível fora do Workspace/tenant/projeto de quem o enviou.

### 2. Research e esclarecimentos

#### Researchs executados

- Nenhuma pesquisa externa formal foi necessária: a escolha de bibliotecas de extração (seção 8) parte de conhecimento consolidado sobre as bibliotecas Python citadas e do padrão de extensão já usado neste repositório (`ProviderFactory`, `src/pipeline/providers/factory.py`). Sem claim `critical` pendente.

#### Fontes e contexto consultados

- `specs/backlog/0033-fase-1-recebimento-e-processamento-de-documentos-ate-markdown.md`: brief completo do refinamento, com decisões já confirmadas com a pessoa (formatos, limites, retenção, independência do fluxo de Base, interface).
- `specs/inbox/2026-09-28-141836-fase-1-recebimento-e-processamento-de-documentos-ate-markdown.md`: captura de origem.
- `.specsfy/DATABASE.md` (linha 122, bloco `conversation-data`): estrutura de dados do "Lote de conversão de documentos" já confirmada via `$specsfy-data-discovery`.
- `src/pipeline/loader.py`, `src/app/routers/bases.py`, `src/app/tasks.py`, `src/app/storage.py`, `src/app/models.py`, `src/pipeline/service.py`, `src/pipeline/providers/factory.py`: comportamento e padrões atuais evidenciando o que falta e o que deve ser reaproveitado.
- `specs/completed/0008-fronteira-interna-pipeline-aplicacao/spec.md` (SPEC-0008): contrato de fronteira `src/pipeline/` ↔ `src/app/` que esta entrega deve seguir.
- `PROJECT.md` (linhas 5-7 e 118-121): confirma a contradição já registrada no backlog entre a visão consolidada (Fase 1 em escopo) e a seção de limites desatualizada.
- `INTERFACE.md`: mapa de componentes existentes (`UploadBaseSheet`, `DataGridBases`, `PainelProgresso`, `PageHeader`, `Sheet`, `Badge`) usado como base de reuso para a nova interface.
- `frontend/src/features/execucoes/PainelProgresso.tsx`: padrão de polling, `Badge` por situação e ação condicionada a papel, reaproveitado pelo painel de progresso do lote.

#### Documentação consultada

- Nenhuma documentação externa online foi consultada nesta especificação; as bibliotecas citadas na seção 8 (`pymupdf4llm`, `python-docx`, `python-pptx`, `openpyxl`, `pytesseract`, LibreOffice headless) são de conhecimento consolidado do agente e serão confirmadas por teste focal (RED/GREEN) na implementação, não por leitura de documentação externa nesta etapa.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo armazenado em `research/`.

#### Dúvidas respondidas

- **Q**: A conversão é uma funcionalidade independente da criação de Base? → **A**: Sim, independente; unificação é direção futura (backlog, Pergunta 1).
- **Q**: Quais formatos são aceitos? → **A**: PDF, PPT, DOC/DOCX, XLS/XLSX e imagens via OCR (backlog, Pergunta 2).
- **Q**: O Markdown preserva estrutura? → **A**: Sim — títulos viram cabeçalhos, tabelas viram tabelas Markdown, slides viram seções (backlog, Pergunta 3).
- **Q**: Falha em um documento cancela o lote? → **A**: Não; os demais seguem, a falha é reportada com opção de reenviar ou seguir sem ele (backlog, Pergunta 5).
- **Q**: Onde vive a tela? → **A**: `/workspaces/[id]`, seção/aba separada da criação de Base, em painel lateral (`Sheet`), como `UploadBaseSheet` (backlog, Interface Perguntas 1-2).
- **Q**: Como funciona o download? → **A**: Individual por arquivo e "baixar todos" em pacote único (backlog, Interface Pergunta 3).
- **Q**: Quanto tempo os arquivos ficam disponíveis? → **A**: 7 dias após o processamento daquele documento terminar (sucesso ou falha definitiva); o registro do lote permanece para histórico (`$specsfy-data-discovery`, `.specsfy/DATABASE.md` linha 122).
- **Q**: Como as bibliotecas de extração leem formatos binários legados (`.doc`, `.ppt`, `.xls`), já que `python-docx`/`python-pptx`/`openpyxl` só leem os formatos OOXML modernos? → **A**: normalização prévia via LibreOffice headless (`soffice --headless --convert-to docx|pptx|xlsx`) antes de aplicar o conversor OOXML correspondente — decisão técnica registrada em DEC-006 (seção 17), reversível e sem impacto no contrato observável pela pessoa.

#### Dúvidas abertas

- Nenhuma. Os pontos ainda sem valor exato no backlog (limite de tamanho por arquivo, idioma do OCR) foram resolvidos como suposições reversíveis (seção 16), como o próprio backlog já autorizava.

### 3. Escopo e atores

#### Incluído

- Painel de envio de documentos originais na tela de Workspace (`/workspaces/[id]`), em seção/aba separada da criação de Base.
- Processamento assíncrono por documento, reaproveitando o Procrastinate já configurado.
- Extração e conversão para Markdown preservando estrutura, para PDF, PPT, DOC/DOCX, XLS/XLSX e imagens (OCR).
- Acompanhamento da situação de cada documento do lote (fila, processando, concluído, falhou).
- Falha isolada por documento, sem cancelar os demais do lote; reenvio do documento que falhou.
- Download do `.md` individual e em pacote único por lote.
- Retenção de 7 dias com apagamento automático do documento original e do `.md`, preservando o registro do lote para histórico.
- Registro do lote e dos documentos em `.specsfy/DATABASE.md` (já feito) e nas tabelas correspondentes.

#### Fora de escopo

- Qualquer alteração em `POST /api/v1/bases` ou no fluxo de criação de Base.
- Unificação futura entre o fluxo de conversão e o fluxo de Base (direção futura declarada, não requisito agora).
- Revisão ou edição do `.md` dentro do sistema antes do download.
- Curadoria cruzada, detecção de contradições ou loop de feedback humano (já fora de escopo do `PROJECT.md`).
- Correção da contradição de `PROJECT.md` sobre o escopo do projeto-mãe como requisito funcional — permanece um ajuste documental, registrado como tarefa de documentação na entrega, não como comportamento novo.

#### Atores

- **Pessoa com permissão de escrita no Workspace** (papel `owner` ou `admin`, mesmo padrão de quem hoje cria uma Base): envia documentos, acompanha o processamento, baixa os `.md`, reenvia documento que falhou.
- **Pessoa com acesso de leitura ao Workspace** (papel `member`): visualiza lotes e documentos já enviados por outras pessoas do mesmo Workspace, sem poder enviar novos documentos.
- **Worker Procrastinate**: processa cada documento e o job periódico de retenção, fora do ciclo de requisição HTTP.

### 4. Princípios e restrições do projeto

- **PR-001**: A extração/conversão vive em `src/pipeline/` (ou módulo equivalente exposto pela fachada `src/pipeline/service.py`); `src/app/` a consome apenas por essa fachada, sem importar módulo interno de `src/pipeline/conversion/` diretamente — mesmo contrato de fronteira da SPEC-0008.
- **PR-002**: Reaproveitar o Procrastinate já configurado (`src/app/tasks.py`) para o processamento assíncrono; não criar um novo mecanismo de fila.
- **PR-003**: Reaproveitar o protocolo `Storage` já existente (`src/app/storage.py`, `S3CompatibleStorage`/`LocalDirectoryStorage`) chaveando pelo id do documento de conversão, sem alterar sua interface.
- **PR-004**: Este fluxo não cria, altera nem depende de nenhuma Base; `POST /api/v1/bases` permanece inalterado.
- **PR-005**: Mesma permissão de escrita e mesmo escopo de visibilidade por Workspace já usados por Base (`require_write_role`, `repo.get_workspace_or_404`).

### 5. Histórias de usuário

#### US-001 — Enviar documentos para conversão em lote (P1)

Como pessoa com permissão de escrita no Workspace, quero enviar um ou mais documentos originais em formatos variados pelo painel do Workspace, para receber automaticamente seus Markdown sem precisar convertê-los manualmente antes.

**Por que P1**: sem isso a entrega não existe — é o evento que dispara o fluxo inteiro.
**Teste independente**: enviar um PDF avulso pelo painel e observar o lote e o documento criados com situação `fila`.
**Requisitos**: FR-001, FR-002, FR-003, FR-008

#### US-002 — Acompanhar a situação de cada documento do lote (P1)

Como pessoa que enviou um lote, quero ver a situação de cada documento (na fila, processando, concluído, falhou) enquanto ele processa, para saber quando o resultado está pronto sem recarregar a página manualmente.

**Por que P1**: sem visibilidade da situação, a pessoa não sabe quando pode baixar nem o que falhou.
**Teste independente**: consultar `GET /api/v1/conversoes/{lote_id}` durante o processamento e observar a situação de cada documento evoluir.
**Requisitos**: FR-002, FR-004

#### US-003 — Baixar os Markdown gerados, individualmente ou em pacote (P1)

Como pessoa que enviou um lote, quero baixar cada `.md` gerado individualmente ou baixar todos de uma vez, para decidir depois, fora do sistema, o que sobe manualmente no fluxo de Base.

**Por que P1**: é o resultado observável que entrega o valor da história — sem download, a conversão não tem uso prático.
**Teste independente**: com um lote concluído, baixar um `.md` individual e depois baixar o pacote com todos.
**Requisitos**: FR-005

#### US-004 — Reenviar um documento que falhou sem afetar os demais do lote (P2)

Como pessoa que enviou um lote com um documento que falhou, quero reenviar apenas esse documento (ou seguir sem ele), para não precisar reenviar o lote inteiro por causa de um único arquivo problemático.

**Por que P2**: melhora a recuperação de erro, mas o lote já é utilizável sem essa ação (os documentos com sucesso já podem ser baixados).
**Teste independente**: com um documento `falhou`, acionar o reenvio e observar sua situação voltar a `fila` e progredir de novo, sem afetar os documentos já `concluido`.
**Requisitos**: FR-002, FR-006

#### US-005 — Ver cada documento convertido numa lista única, com sua situação (P1)

Como pessoa que acompanha as conversões do Workspace, quero uma lista com uma linha por documento, mostrando se ele já foi convertido em Markdown, ainda está na fila ou falhou, para saber o estado de cada arquivo sem abrir lote por lote.

**Por que P1**: a situação por documento é a informação que a pessoa procura ao abrir a aba; escondê-la dentro de um lote expandido e em valores técnicos crus obriga a abrir cada lote para descobrir o que já está pronto.
**Teste independente**: com dois lotes no Workspace, abrir a aba "Conversão de documentos" e observar uma linha por documento, cada uma com a situação em rótulo legível, sem expandir nenhum lote.
**Requisitos**: FR-004, FR-009

### 6. Cenários BDD de aceite

#### AC-001 — Converter documentos de formatos variados com sucesso

**Cobre**: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001

```gherkin
@US-001 @US-002 @US-003 @FR-001 @FR-002 @FR-003 @FR-004 @FR-005 @NFR-001 @AC-001
Feature: Conversão de documentos originais em Markdown

  Scenario: Converter documentos de formatos variados com sucesso
    Given a pessoa está no Workspace com permissão de escrita
    When ela envia um PDF, uma planilha XLSX e uma imagem JPG pelo painel de conversão
    Then a resposta do envio retorna imediatamente, sem esperar o processamento
    And o lote é processado em segundo plano
    And cada documento aparece com sua situação (fila, processando, concluído)
    And ao concluir, a pessoa baixa o .md de cada um individualmente ou baixa todos em um pacote único
    And nenhuma Base é criada ou alterada por esse envio
```

#### AC-002 — Falha parcial não derruba o lote

**Cobre**: US-002, US-004, FR-002, FR-004, FR-006, NFR-003

```gherkin
@US-002 @US-004 @FR-002 @FR-004 @FR-006 @NFR-003 @AC-002
Feature: Conversão de documentos originais em Markdown

  Scenario: Um documento falha sem derrubar o lote inteiro
    Given um lote com três documentos, um deles um PDF corrompido
    When o processamento de todos os documentos termina
    Then os dois documentos válidos aparecem concluídos com seus .md disponíveis
    And o documento corrompido aparece como falhou, com um motivo seguro e sem detalhe interno da biblioteca
    And a pessoa pode reenviar apenas esse documento ou seguir sem ele
```

#### AC-003 — Preservar estrutura na conversão de DOCX e XLSX

**Cobre**: US-001, FR-003

```gherkin
@US-001 @FR-003 @AC-003
Feature: Conversão de documentos originais em Markdown

  Scenario: Preservar estrutura na conversão
    Given um DOCX com títulos e uma tabela, e uma XLSX com duas planilhas
    When cada documento é convertido
    Then o .md do DOCX usa cabeçalhos Markdown para os títulos e uma tabela Markdown equivalente à tabela original
    And o .md da XLSX tem uma seção por planilha, cada uma com uma tabela Markdown das células
```

#### AC-004 — Rejeitar formato não suportado

**Cobre**: US-001, FR-001

```gherkin
@US-001 @FR-001 @AC-004
Feature: Conversão de documentos originais em Markdown

  Scenario: Rejeitar formato não suportado
    Given um arquivo .zip enviado ao painel de conversão
    When a pessoa tenta enviar esse arquivo
    Then o sistema recusa o arquivo antes de iniciar qualquer processamento
    And informa que a extensão não é suportada, sem criar lote nem documento
```

#### AC-005 — Limite de tamanho por arquivo ou por lote excedido

**Cobre**: FR-001

```gherkin
@FR-001 @AC-005
Feature: Conversão de documentos originais em Markdown

  Scenario: Recusar envio acima dos limites
    Given um arquivo de 45 MB ou um lote cuja soma passa de 50 MB ou tem mais de 50 arquivos
    When a pessoa tenta enviar esse lote
    Then o sistema recusa o envio antes de iniciar o processamento
    And informa qual limite foi excedido, no mesmo padrão de mensagem já usado por Base
```

#### AC-006 — Reenviar documento que falhou

**Cobre**: US-004, FR-002, FR-006, NFR-003

```gherkin
@US-004 @FR-002 @FR-006 @NFR-003 @AC-006
Feature: Conversão de documentos originais em Markdown

  Scenario: Reenviar apenas o documento que falhou
    Given um documento com situação falhou, dentro da janela de retenção de 7 dias
    When a pessoa aciona reenviar esse documento
    Then a situação do documento volta para fila e depois processa de novo
    And os demais documentos do lote, já concluídos, permanecem inalterados e disponíveis
```

#### AC-007 — Baixar todos os .md do lote em um pacote único

**Cobre**: US-003, FR-005

```gherkin
@US-003 @FR-005 @AC-007
Feature: Conversão de documentos originais em Markdown

  Scenario: Baixar todos os .md concluídos em um pacote
    Given um lote com dois documentos concluídos e um documento falhou
    When a pessoa aciona "baixar todos"
    Then ela recebe um único pacote contendo os .md dos dois documentos concluídos
    And o documento falhou não entra no pacote
```

#### AC-008 — Baixar o .md de um documento individualmente

**Cobre**: US-003, FR-005

```gherkin
@US-003 @FR-005 @AC-008
Feature: Conversão de documentos originais em Markdown

  Scenario: Baixar um .md individual
    Given um documento concluído dentro da janela de retenção
    When a pessoa aciona baixar esse documento
    Then ela recebe o arquivo .md gerado para aquele documento específico
```

#### AC-009 — Isolamento entre Workspaces e tenants

**Cobre**: FR-008, NFR-002

```gherkin
@FR-008 @NFR-002 @AC-009
Feature: Conversão de documentos originais em Markdown

  Scenario: Pessoa de outro Workspace ou tenant não acessa o lote
    Given um lote pertencente ao Workspace A
    When uma pessoa autenticada sem vínculo com o Workspace A tenta consultar ou baixar esse lote
    Then a API recusa o acesso, no mesmo padrão de escopo já usado por Base
```

#### AC-010 — Permissão de escrita controla quem pode enviar

**Cobre**: FR-008

```gherkin
@FR-008 @AC-010
Feature: Conversão de documentos originais em Markdown

  Scenario: Member não pode enviar, mas pode visualizar
    Given uma pessoa com papel member no Workspace, sem permissão de escrita
    When ela tenta enviar documentos pelo painel de conversão
    Then o envio é recusado por permissão insuficiente
    And essa mesma pessoa consegue visualizar os lotes já existentes do Workspace
```

#### AC-011 — Consultar situação de um lote em processamento

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-011
Feature: Conversão de documentos originais em Markdown

  Scenario: Consultar a situação de um lote em andamento
    Given um lote recém-enviado, ainda com documentos em fila ou processando
    When a pessoa consulta o lote
    Then a resposta traz a situação geral do lote e a situação individual de cada documento
```

#### AC-012 — OCR extrai texto de imagem

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-012
Feature: Conversão de documentos originais em Markdown

  Scenario: Extrair texto de uma imagem por OCR
    Given uma imagem JPG com texto em português
    When o documento é convertido
    Then o .md gerado contém o texto reconhecido por OCR, em melhor esforço
    And uma imagem sem texto reconhecível não bloqueia o lote, apenas resulta em .md com conteúdo mínimo ou aviso
```

#### AC-013 — Apagar arquivos após 7 dias mantendo o registro do lote

**Cobre**: FR-007, NFR-002

```gherkin
@FR-007 @NFR-002 @AC-013
Feature: Conversão de documentos originais em Markdown

  Scenario: Apagar arquivos após o prazo de retenção
    Given um documento processado com sucesso há mais de 7 dias
    When o job periódico de retenção roda
    Then o documento original e o .md gerado são apagados do armazenamento
    And o registro do lote continua mostrando quais arquivos existiram e seu resultado
```

#### AC-014 — Registro do lote permanece consultável após expiração

**Cobre**: FR-007

```gherkin
@FR-007 @AC-014
Feature: Conversão de documentos originais em Markdown

  Scenario: Consultar histórico após a expiração dos arquivos
    Given um lote cujos arquivos já foram apagados pela retenção de 7 dias
    When a pessoa consulta esse lote
    Then ela ainda vê nome, formato e resultado de cada documento do lote
    And nenhum link de download funciona para os documentos expirados
```

#### AC-015 — Tentar baixar arquivo expirado

**Cobre**: FR-007, NFR-002

```gherkin
@FR-007 @NFR-002 @AC-015
Feature: Conversão de documentos originais em Markdown

  Scenario: Tentar baixar um documento expirado
    Given um documento cujo prazo de retenção já expirou
    When a pessoa tenta baixar o .md ou o original desse documento
    Then o sistema informa que o arquivo não está mais disponível
    And orienta a reenviar o documento original para gerar um novo .md
```

#### AC-016 — Seguir sem reenviar documento que falhou

**Cobre**: US-004, FR-006

```gherkin
@US-004 @FR-006 @AC-016
Feature: Conversão de documentos originais em Markdown

  Scenario: Seguir sem reenviar um documento que falhou
    Given um lote com um documento falhou e dois documentos concluídos
    When a pessoa decide não reenviar o documento que falhou
    Then ela continua podendo baixar os dois documentos concluídos, individualmente ou em pacote
    And o documento que falhou permanece registrado com seu motivo, sem bloquear o restante
```

#### AC-017 — Envio de lote grande retorna imediatamente

**Cobre**: NFR-001

```gherkin
@NFR-001 @AC-017
Feature: Conversão de documentos originais em Markdown

  Scenario: Envio de lote grande não bloqueia a requisição
    Given um lote com 50 documentos no limite de tamanho permitido
    When a pessoa envia esse lote
    Then a API responde com o lote criado antes de qualquer documento terminar de processar
    And o processamento de cada documento continua em segundo plano, fora da requisição HTTP
```

#### AC-018 — Mensagem de erro não expõe detalhe interno

**Cobre**: NFR-003

```gherkin
@NFR-003 @AC-018
Feature: Conversão de documentos originais em Markdown

  Scenario: Erro de extração não vaza detalhe interno
    Given um documento cuja conversão lança uma exceção da biblioteca de extração
    When a falha é registrada
    Then o motivo exposto à pessoa é genérico e seguro
    And o detalhe técnico (tipo da exceção, origem no código) só aparece no log do worker
```

#### AC-019 — Pessoa sem vínculo ao Workspace não acessa lote nem arquivo

**Cobre**: FR-008, NFR-002

```gherkin
@FR-008 @NFR-002 @AC-019
Feature: Conversão de documentos originais em Markdown

  Scenario: Pessoa sem vínculo ao Workspace tenta acessar por id direto
    Given o id de um lote ou de um documento de outro Workspace
    When uma pessoa sem vínculo com esse Workspace tenta acessá-lo diretamente pela API
    Then a API responde como recurso não encontrado, sem revelar sua existência
```

#### AC-020 — Listar uma linha por documento com situação legível

**Cobre**: US-005, FR-004, FR-009

```gherkin
@US-005 @FR-004 @FR-009 @AC-020
Feature: Conversão de documentos originais em Markdown

  Scenario: A aba lista cada documento com sua situação em rótulo legível
    Given o Workspace tem um lote com um documento convertido, um na fila e um que falhou, e outro lote com um documento processando
    When a pessoa abre a aba "Conversão de documentos"
    Then a lista mostra uma linha por documento, quatro no total, e não uma linha por lote
    And cada linha mostra a coluna ID, o arquivo, o formato, o lote, a data de criação e quem criou
    And a situação de cada linha aparece como rótulo legível em português: "Na fila", "Processando", "Convertido" ou "Falhou"
    And os valores técnicos internos da situação não são exibidos
```

#### AC-021 — Agir sobre um documento direto na linha

**Cobre**: US-005, US-003, US-004, FR-005, FR-006, FR-009

```gherkin
@US-005 @US-003 @US-004 @FR-005 @FR-006 @FR-009 @AC-021
Feature: Conversão de documentos originais em Markdown

  Scenario: Baixar, reenviar e abrir o lote a partir da linha do documento
    Given a lista de documentos da aba "Conversão de documentos", com um documento convertido e um que falhou
    When a pessoa com permissão de escrita aciona "Baixar" na linha do convertido
    Then o .md desse documento é baixado sem abrir o lote
    When ela aciona "Reenviar" na linha do que falhou
    Then somente esse documento volta para "Na fila", sem afetar os demais
    When ela abre a linha, por clique ou por teclado
    Then o painel do lote desse documento abre, com o download do pacote de todos os convertidos
    And uma pessoa sem permissão de escrita vê as linhas e pode baixar, mas não vê "Reenviar"
```

#### AC-022 — Estado vazio da aba com ação para converter

**Cobre**: US-005, US-001, FR-009

```gherkin
@US-005 @US-001 @FR-009 @AC-022
Feature: Conversão de documentos originais em Markdown

  Scenario: Aba sem nenhum documento convertido oferece a ação de converter
    Given o Workspace ainda não tem nenhum lote de conversão
    When uma pessoa com permissão de escrita abre a aba "Conversão de documentos"
    Then a lista mostra a mensagem de vazio e um botão "Converter documentos"
    And acionar esse botão abre o mesmo painel de envio do botão "Converter documentos" do cabeçalho
    And uma pessoa sem permissão de escrita vê a mensagem de vazio sem o botão
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve validar, antes de iniciar qualquer processamento, que cada arquivo enviado tem extensão aceita (`.pdf`, `.ppt`, `.pptx`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.jpg`, `.jpeg`, `.png`), respeita o limite de 40 MB por arquivo, 50 MB no total do envio e 50 arquivos por lote — rejeitando o envio inteiro com mensagem explícita quando qualquer regra for violada.
- **FR-002**: O sistema deve criar um lote de conversão e processar cada documento do lote de forma assíncrona e independente, de modo que a falha de um documento não impeça o processamento nem a conclusão dos demais.
- **FR-003**: O sistema deve extrair o conteúdo de cada documento e convertê-lo em Markdown preservando estrutura quando o formato permitir: títulos viram cabeçalhos, tabelas (PDF, DOCX, XLS/XLSX) viram tabelas Markdown, cada slide de PPT/PPTX vira uma seção, e texto de imagem é extraído por OCR em melhor esforço.
- **FR-004**: O sistema deve expor a situação de cada documento (fila, processando, concluído, falhou) e a situação geral do lote (processando, concluído, concluído com falhas), incluindo o motivo de cada falha.
- **FR-005**: O sistema deve permitir o download do Markdown gerado, individualmente por documento ou em um pacote único com todos os documentos concluídos do lote.
- **FR-006**: O sistema deve permitir reenviar um documento específico que falhou, reprocessando-o sem afetar os demais documentos do lote.
- **FR-007**: O sistema deve apagar automaticamente o documento original e o Markdown gerado 7 dias após o processamento daquele documento terminar (sucesso ou falha definitiva), preservando o registro do lote (quais arquivos existiram e seu resultado) para histórico mesmo após o apagamento.
- **FR-008**: O sistema deve restringir o envio de documentos à mesma permissão de escrita hoje usada para criar uma Base no Workspace, e restringir a visibilidade do lote e de seus documentos ao mesmo escopo de Workspace/tenant/projeto já usado por Base.
- **FR-009**: A aba "Conversão de documentos" deve listar uma linha por documento (e não por lote), com as colunas ID, Arquivo, Formato, Situação, Lote, Criado em e Criado por, ordenadas do mais recente ao mais antigo. A situação deve ser exibida como `Badge` com rótulo em português ("Na fila", "Processando", "Convertido", "Falhou") em toda a superfície, nunca como valor técnico cru. Cada linha oferece, de forma independente, baixar o `.md` (documento convertido e não expirado) e reenviar (documento que falhou, só com permissão de escrita); a linha inteira abre o painel do lote do documento, por mouse e por teclado. Sem documentos, a lista mostra a mensagem de vazio e, com permissão de escrita, o botão "Converter documentos", que abre o mesmo painel de envio do cabeçalho.

#### Não funcionais

- **NFR-001**: O envio de um lote não deve bloquear a requisição HTTP esperando o processamento, mesmo em lotes grandes ou com OCR lento. **Verificação**: teste de integração confirma que `POST /api/v1/conversoes` responde com o lote criado antes de qualquer documento atingir situação terminal, e observação de tempo de resposta.
- **NFR-002**: Nenhum documento, `.md` gerado ou registro de lote deve ficar acessível fora do Workspace/tenant/projeto de quem o enviou, inclusive por id direto, e o apagamento automático em 7 dias deve reduzir a janela de exposição do conteúdo. **Verificação**: teste de integração de acesso cruzado entre Workspaces/tenants e teste de expiração.
- **NFR-003**: O motivo de falha de um documento deve ser diagnosticável no log do worker sem expor credencial ou detalhe interno de biblioteca na resposta da API, seguindo o mesmo padrão já aplicado a `_registrar_falha`/`execution.erro` em `src/app/tasks.py`. **Verificação**: teste de integração inspeciona a mensagem retornada pela API e o log estruturado do worker.

#### Erros e casos-limite

- Documento com extensão não suportada → recusado antes do processamento, com mensagem explícita; nenhum lote nem documento é criado para ele.
- Arquivo acima de 40 MB, ou lote acima de 50 MB/50 arquivos → recusado no envio inteiro, mesmo padrão de mensagem já usado por Base.
- Documento corrompido ou ilegível (ex.: PDF corrompido, imagem sem texto reconhecível) → marcado como `falhou`, com motivo seguro, sem afetar os demais do lote.
- Reenvio de documento cujo original já expirou (mais de 7 dias) → recusado, orientando o reenvio do documento original completo (novo envio, não um reenvio no mesmo lote).
- Download de documento expirado → recusado, mesma orientação acima.
- Falha ao agendar o processamento de um documento (Procrastinate indisponível) → documento permanece `fila` com aviso, mesmo espírito da falha de agendamento já tratada em `UploadBaseSheet`/execuções de Base.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- `src/pipeline/loader.py` só lê arquivos `.md` já existentes em um diretório; não há nenhuma capacidade de extração de outros formatos no pipeline hoje.
- `src/app/routers/bases.py::enviar_base` valida extensão/tamanho/quantidade e usa `Storage` (`src/app/storage.py`) para persistir arquivos antes de criar o registro no banco — padrão que esta entrega replica para o lote de conversão.
- `src/app/tasks.py` já configura um `procrastinate.App` com `configure_connector` chamado uma vez no entrypoint (`src/app/main.py`), e já tem um job periódico (`purgar_dados_de_acesso_task`, `@app.periodic(cron="0 3 * * *")`) que esta entrega replica para a retenção de 7 dias.
- `src/app/storage.py` define o protocolo `Storage` (`save`, `delete_base`, `materialize`) chaveado por um id de pasta arbitrário — hoje usado com `base_id`, mas seu contrato não presume nada sobre o significado do id, permitindo reuso direto com `documento_id`.
- `src/pipeline/providers/factory.py` (`ProviderFactory`) já estabelece o padrão de despacho por configuração/chave usado neste repositório para pontos de extensão — o `ConverterFactory` desta entrega segue o mesmo padrão, despachando por extensão de arquivo em vez de configuração de provider.
- `src/pipeline/service.py` é a fachada estável consumida por `src/app/` (SPEC-0008); a nova capacidade de conversão é exposta por ela, sem que `src/app/` importe `src/pipeline/conversion/` diretamente.
- Nenhuma biblioteca de extração de documento (PDF/DOCX/PPTX/XLSX/OCR) está hoje em `pyproject.toml`; esta entrega adiciona as primeiras.

#### Arquitetura e módulos

- Novo módulo `src/pipeline/conversion/`, seguindo o padrão de extensão já usado por `src/pipeline/providers/`:
  - `contracts.py`: `ConversionResult` (dataclass: `markdown: str`, `avisos: list[str]`), protocolo `DocumentConverter` (`converter(self, caminho: Path) -> ConversionResult`), `UnsupportedFormatError`, `ConversionError`.
  - `factory.py`: `ConverterFactory.for_extension(extensao: str) -> DocumentConverter`, despacho por extensão normalizada (minúscula, sem ponto), incluindo a normalização de formatos legados antes do despacho (ver decisão abaixo).
  - `converters/pdf.py`: `PdfConverter`, usa `pymupdf4llm` para extrair Markdown preservando cabeçalhos (por heurística de fonte) e tabelas.
  - `converters/docx.py`: `DocxConverter`, usa `python-docx`; percorre parágrafos (`style.name` iniciando em `"Heading"` vira `#`/`##`/...) e tabelas (`table.rows`/`table.columns` viram linhas de tabela Markdown).
  - `converters/pptx.py`: `PptxConverter`, usa `python-pptx`; cada slide vira uma seção `## Slide {n}: {título do placeholder de título, quando houver}`, com o texto dos demais placeholders como corpo.
  - `converters/xlsx.py`: `XlsxConverter`, usa `openpyxl`; cada planilha vira uma seção `## {nome da planilha}` com uma tabela Markdown das células preenchidas.
  - `converters/image.py`: `ImageConverter`, usa `Pillow` + `pytesseract` (Tesseract OCR), idioma padrão `por` (português), melhor esforço, sem bloquear por baixa confiança (suposição confirmada no backlog).
  - `legacy_office.py`: `normalizar_formato_legado(caminho: Path, extensao: str) -> Path`, chama `soffice --headless --convert-to docx|pptx|xlsx --outdir <tmp> <arquivo>` (LibreOffice) para `.doc`→`.docx`, `.ppt`→`.pptx`, `.xls`→`.xlsx` antes de delegar ao conversor OOXML correspondente — ver DEC-006 (seção 17) e risco associado (seção 16).
- `src/pipeline/service.py` ganha `convert_document(caminho: Path, extensao: str) -> ConversionResult`, delegando a `ConverterFactory`, adicionada a `__all__`.
- Novo router `src/app/routers/conversao.py`, prefixo `/api/v1`, mesmo padrão de `bases.py` (`Depends(get_identity)`, `require_write_role`, `SessionLocal`).
- Novas tarefas em `src/app/tasks.py`: `process_conversion_document_task` (por documento) e `purgar_documentos_conversao_task` (periódica diária).
- Novas funções em `src/app/repo.py`: `list_lotes_for_identity`, `get_lote_or_404`, `get_documento_or_404`, `recalcular_situacao_lote`.

#### Migrations

- Nova revisão Alembic (`alembic/versions/`, nome sugerido `00XX_lotes_conversao`) criando `lotes_conversao` e `documentos_conversao` (seção 9), com índice em `(workspace_id, criado_em)` para listagem e em `(lote_id)` para os documentos. Sem alteração em tabelas existentes; rollback remove as duas tabelas novas.

#### Models

- `LoteConversao` (`src/app/models.py`), `__tablename__ = "lotes_conversao"`: pertence a um Workspace e a uma Pessoa; `situacao` é recalculada a cada atualização de documento filho (não computada em tempo real na leitura), evitando uma agregação cara a cada `GET`.
- `DocumentoConversao` (`src/app/models.py`), `__tablename__ = "documentos_conversao"`: pertence a um `LoteConversao` (`ON DELETE CASCADE` não se aplica — lote nunca é apagado, só seus arquivos); guarda `expira_em` calculado no momento da conclusão (`concluido_em + 7 dias`) e `apagado_em` preenchido pelo job de retenção.

#### Controllers e casos de uso

- `POST /api/v1/conversoes` (multipart: `arquivos[]`, `workspace_id`): `require_write_role`; valida extensão/tamanho/quantidade (FR-001); cria `LoteConversao` (`situacao="processando"`) e um `DocumentoConversao` por arquivo (`situacao="fila"`); salva cada original no `Storage` chaveado por `documento_id`; agenda `process_conversion_document_task` por documento; devolve 201 com o lote e seus documentos serializados. Arquivo: `src/app/routers/conversao.py`.
- `GET /api/v1/conversoes?workspace_id=`: lista lotes do Workspace (qualquer papel com acesso), mais recentes primeiro. Arquivo: `src/app/routers/conversao.py`.
- `GET /api/v1/conversoes/{lote_id}`: detalhe do lote com todos os documentos e situações (usado pelo polling do frontend). 404 fora do escopo do Workspace/tenant (AC-019). Arquivo: `src/app/routers/conversao.py`.
- `GET /api/v1/conversoes/{lote_id}/documentos/{documento_id}/markdown`: baixa o `.md`; 404 se não `concluido` ou se `apagado_em` preenchido (AC-015). Arquivo: `src/app/routers/conversao.py`.
- `GET /api/v1/conversoes/{lote_id}/pacote`: monta um `.zip` em memória (`zipfile`, biblioteca padrão) com os `.md` de todos os documentos `concluido` ainda não expirados do lote. Arquivo: `src/app/routers/conversao.py`.
- `POST /api/v1/conversoes/{lote_id}/documentos/{documento_id}/reenviar`: `require_write_role`; 400 se o documento não está `falhou` ou já expirou (`apagado_em` preenchido ou `expira_em` vencido); senão volta `situacao="fila"`, limpa `erro` e `expira_em` (só é regravado numa nova conclusão), reagenda `process_conversion_document_task` reusando o original já salvo. Arquivo: `src/app/routers/conversao.py`.

#### Views e experiência

- Ver seção 10 (Interfaces e contratos) para telas, componentes e estados.

#### Queries e repositórios

- `repo.list_lotes_for_identity(session, identity, workspace_id)`: filtra por `tenant_id`/`project_id`/`workspace_id` do identity, mesmo padrão de `list_bases_for_identity`.
- `repo.get_lote_or_404(session, lote_id, identity)` / `repo.get_documento_or_404(session, lote_id, documento_id, identity)`: 404 sem revelar existência fora do escopo (AC-019), mesmo padrão de `get_workspace_or_404`.
- `repo.recalcular_situacao_lote(session, lote_id)`: lê a situação de todos os `DocumentoConversao` do lote e grava a situação agregada do `LoteConversao` (`processando` se algum `fila`/`processando`; `concluido_com_falhas` se todos terminais e algum `falhou`; senão `concluido`). Chamada dentro da mesma transação que atualiza a situação do documento, ao final de `process_conversion_document_task`.

#### Jobs e processamento assíncrono

- `process_conversion_document_task(documento_id: str)` (`src/app/tasks.py`, `@app.task`): carrega o `DocumentoConversao`; materializa o original do `Storage` em arquivo temporário (`tempfile`, mesmo padrão de `process_base_task`); marca `situacao="processando"`; chama `service.convert_document(caminho, formato)`; em sucesso, salva o `.md` no `Storage`, marca `situacao="concluido"`, `concluido_em=agora()`, `expira_em=concluido_em + 7 dias`; em exceção, aplica o mesmo padrão de `_registrar_falha` (log com tipo/origem, sem credencial) e marca `situacao="falhou"` com mensagem genérica (NFR-003); em qualquer caso, chama `repo.recalcular_situacao_lote`.
- `purgar_documentos_conversao_task` (`@app.periodic(cron="0 3 * * *")`, mesmo horário de `purgar_dados_de_acesso_task`): para cada `DocumentoConversao` com `expira_em <= agora()` e `apagado_em is None`, remove original e `.md` do `Storage` (`storage.delete_base(documento_id)`, reaproveitando a operação existente) e grava `apagado_em`; nunca apaga a linha do banco (histórico, FR-007).

#### Estrutura de arquivos

```text
specs/draft/0023-fase-1-recebimento-e-processamento-de-documentos-ate-markdown/
  spec.md
  research/
src/
  pipeline/
    conversion/
      __init__.py
      contracts.py
      factory.py
      legacy_office.py
      converters/
        __init__.py
        pdf.py
        docx.py
        pptx.py
        xlsx.py
        image.py
    service.py            # + convert_document()
  app/
    models.py              # + LoteConversao, DocumentoConversao
    repo.py                 # + funções de lote/documento de conversão
    tasks.py                 # + process_conversion_document_task, purgar_documentos_conversao_task
    routers/
      conversao.py           # novo
      __init__.py            # registra o novo router (mesmo padrão de bases.py)
  alembic/versions/
    00XX_lotes_conversao.py  # novo
frontend/src/
  features/
    conversao/
      ConversaoSheet.tsx
      DataGridLotesConversao.tsx
      PainelLoteConversao.tsx
  app/(autenticado)/workspaces/[id]/page.tsx  # + Tabs Bases/Conversão
  components/ui/tabs.tsx      # primitive shadcn/ui nova
tests/
  test_conversion_pdf.py
  test_conversion_docx.py
  test_conversion_pptx.py
  test_conversion_xlsx.py
  test_conversion_image_ocr.py
  test_conversion_legacy_office.py
  test_router_conversao.py
  test_task_process_conversion_document.py
  test_task_purgar_documentos_conversao.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `LoteConversao` | `id` (UUID) | `tenant_id`, `project_id`, `workspace_id` (FK `workspaces.id`), `criado_por` (FK `pessoas.id`, nullable — autoria histórica ausente segue o mesmo padrão de `Base`), `criado_em`, `situacao` (`processando`\|`concluido`\|`concluido_com_falhas`) | Pertence a um Workspace e a uma Pessoa; tem muitos `DocumentoConversao` |
| `DocumentoConversao` | `id` (UUID) | `lote_id` (FK `lotes_conversao.id`), `nome_arquivo`, `formato` (extensão normalizada), `tamanho_bytes`, `situacao` (`fila`\|`processando`\|`concluido`\|`falhou`), `erro` (texto seguro, nullable), `criado_em`, `concluido_em` (nullable), `expira_em` (nullable, setado ao concluir), `apagado_em` (nullable, setado pela retenção) | Pertence a um `LoteConversao`; sem relação com `Base` |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| `DocumentoConversao` | `fila` | worker inicia o processamento | `processando` | — |
| `DocumentoConversao` | `processando` | conversão termina sem erro | `concluido` | `expira_em` gravado (`concluido_em + 7d`) |
| `DocumentoConversao` | `processando` | conversão lança exceção | `falhou` | `erro` gravado com mensagem segura; `expira_em` gravado (contagem de retenção também vale para falha definitiva) |
| `DocumentoConversao` | `falhou` | pessoa aciona reenviar, dentro da retenção | `fila` | `erro` limpo; `expira_em` limpo até nova conclusão |
| `DocumentoConversao` | `concluido`/`falhou` | job de retenção, `expira_em` vencido | (mesmo estado) | `apagado_em` gravado; arquivos removidos do Storage; linha permanece |
| `LoteConversao` | `processando` | cada documento chega a estado terminal, nenhum `falhou` | `concluido` | — |
| `LoteConversao` | `processando` | cada documento chega a estado terminal, algum `falhou` | `concluido_com_falhas` | — |
| `LoteConversao` | `concluido`/`concluido_com_falhas` | pessoa reenvia um documento `falhou` | `processando` | — |

#### Migração e retenção

- Migração aditiva: uma revisão Alembic cria as duas tabelas novas; nenhuma tabela existente muda. Rollback remove as duas tabelas.
- Retenção: `purgar_documentos_conversao_task` roda diariamente e apaga apenas os arquivos no `Storage` (original e `.md`) de documentos com `expira_em` vencido; a linha em `documentos_conversao` nunca é apagada, preservando o histórico do lote (FR-007).

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. Marcio e a equipe de consultoria enviam documentos e acompanham/baixam o resultado por uma tela nova dentro do Workspace.

#### Stack e convenções de interface

- Next.js (App Router) + React + TypeScript + Tailwind CSS + shadcn/ui + ReUI — mesma stack do restante de `frontend/src/`, confirmada em `.specsfy/STACK.md` e `INTERFACE.md`.
- Telas autenticadas em `frontend/src/app/(autenticado)/`; componentes de domínio por área em `frontend/src/features/<área>/`; chamadas à API por `apiJson` (`frontend/src/lib/api-client.ts`).
- Tela afetada existente: `/workspaces/[id]` (`frontend/src/app/(autenticado)/workspaces/[id]/page.tsx`), hoje com `PageHeader`, `DataGridBases`, `UploadBaseSheet`, `WorkspaceFormSheet`, `ExcluirWorkspaceDialog`. Será preservada integralmente; a nova capacidade entra como uma aba adicional, sem alterar o comportamento de Base.
- Primitive nova necessária: `Tabs`/`TabsList`/`TabsTrigger`/`TabsContent` (shadcn/ui) — ainda não existe em `frontend/src/components/ui/`; instalar antes de compor a tela (carregar `$specsfy-specialist-shadcn-ui`).

#### Telas e responsabilidades

- `/workspaces/[id]` (estendida): agora com duas abas — a de coleções (comportamento atual, preservado) e "Conversão de documentos" (nova). A aba nova lista os documentos convertidos do Workspace, uma linha por documento, e permite abrir o painel de envio. (Revisão de 2026-10-14, FR-009: antes a lista era uma linha por lote.)
- Não há rota própria para o detalhe de um lote: o acompanhamento e o download acontecem no mesmo painel/aba, conforme decisão confirmada no backlog ("a pessoa acompanha a situação de cada documento... no mesmo painel").

#### Fluxo de informação e navegação

- Workspace → aba "Conversão de documentos" → botão "Converter documentos" abre `ConversaoSheet` (painel lateral) → pessoa seleciona arquivos e envia → o envio (201) mantém o painel aberto mostrando o lote recém-criado com a lista de documentos e polling a cada 3 s (mesmo intervalo de `/execucoes/[id]`) enquanto houver documento `fila`/`processando` → ao concluir, a pessoa baixa individualmente ou aciona "Baixar todos" → fecha o painel e os documentos do lote passam a aparecer na listagem da aba, uma linha por documento, disponíveis para download e reenvio dentro da retenção. Da lista, a pessoa baixa o `.md` ou reenvia pela própria linha, ou abre a linha para ver o painel do lote (`PainelLoteConversao`) e baixar o pacote (FR-009).
- `Breadcrumb`: mesma equipe/Workspace já mostrado hoje em `/workspaces/[id]`; a aba não altera o `Breadcrumb`, só o conteúdo abaixo do `PageHeader`.

#### Menus e navegação principal

- Nenhum item novo no menu principal. O acesso segue o mesmo padrão de Base (SPEC-0019): chega-se pelo Workspace já presente no menu, sem entrada própria para "conversão de documentos".

#### Formulários e ações

- `ConversaoSheet`: input de arquivo múltiplo (`accept=".pdf,.ppt,.pptx,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"`), lista removível dos arquivos selecionados com nome e tamanho, validação client-side de extensão e dos limites (40 MB/arquivo, 50 MB total, 50 arquivos) antes do envio, no mesmo padrão de mensagem de erro já usado por `UploadBaseSheet`. Ação principal "Converter" desabilitada sem Workspace resolvido ou sem arquivo selecionado; "Convertendo…" desabilita os controles até a resposta da API.
- Painel de acompanhamento (dentro do mesmo `Sheet`, após o envio): lista de documentos com `Badge` de situação (mesmas variantes de `PainelProgresso`: `default`=concluído, `destructive`=falhou, `secondary`=fila/processando) e rótulos em português ("Na fila", "Processando", "Convertido", "Falhou") também na situação do lote ("Processando", "Concluído", "Concluído com falhas"), botão "Baixar" por documento concluído, botão "Reenviar" por documento falhou (mesma restrição de papel de escrita), botão "Baixar todos" habilitado quando houver ao menos um documento concluído.

#### Composição e disposição

- `Tabs` (shadcn/ui) dentro de `/workspaces/[id]`, logo abaixo do `PageHeader`, alternando "Bases" (conteúdo atual) e "Conversão de documentos" (novo). Em mobile, as abas empilham com rolagem horizontal contida, sem overflow da página — mesmo padrão de largura contida já usado por `DataGridBases`.
- A listagem usa uma tabela semântica em largura total, uma linha por documento, com a coluna `ID` do documento sempre visível, seguindo o padrão de `DataGridBases`. Colunas: ID, Arquivo, Formato, Situação (`Badge` com rótulo em português), Lote, Criado em, Criado por e Ações (Baixar, Reenviar). A linha inteira, por mouse e teclado, abre `PainelLoteConversao` do lote do documento num painel lateral (não há rota de detalhe própria); as ações da linha são independentes e não abrem o painel (FR-009).
- Vazio: mensagem e, com permissão de escrita, botão "Converter documentos" no corpo da tabela, que abre o mesmo `ConversaoSheet` do cabeçalho — mesmo padrão do vazio da aba de coleções.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Workspace (aba Conversão) | `ConversaoSheet` | Formulário de envio multi-formato e painel de acompanhamento pós-envio | `frontend/src/features/conversao/ConversaoSheet.tsx` | `Sheet`, `Badge`, `Button`, `Alert` | shadcn/ui (primitives) | Modelado em `UploadBaseSheet`; bloco novo |
| Workspace (aba Conversão) | `DataGridLotesConversao` | Lista os documentos do Workspace (uma linha por documento), coluna `ID` visível, ações por linha e painel do lote ao abrir a linha | `frontend/src/features/conversao/DataGridLotesConversao.tsx` | tabela semântica + `Skeleton` + `Badge` + `Sheet` | Próprio | Modelado em `DataGridBases`; revisado em 2026-10-14 (FR-009) |
| Workspace (aba Conversão) | `PainelLoteConversao` | Situação por documento, download individual/pacote, ação de reenviar | `frontend/src/features/conversao/PainelLoteConversao.tsx` | `Badge`, `Button` | shadcn/ui (`Badge`) | Modelado em `PainelProgresso`; bloco novo |
| Workspace `/workspaces/[id]` | `Tabs`/`TabsList`/`TabsTrigger`/`TabsContent` | Alterna "Bases" e "Conversão de documentos" | `frontend/src/components/ui/tabs.tsx` | `Tabs` | shadcn/ui | Primitive nova, ainda não instalada no projeto |

- Registrar cada arquivo criado ou reaproveitado acima em `INTERFACE.md` ao implementar, com consumidores e regra de reuso, conforme já feito para `UploadBaseSheet`/`PainelProgresso`.

#### Estados e acessibilidade

- Carregando: `Skeleton` na listagem de lotes (mesmo padrão de `DataGridBases`), `aria-busy` e texto para leitor de tela.
- Vazio: mensagem contextual convidando a converter o primeiro documento, com o botão "Converter documentos" quando houver permissão de escrita (mesmo padrão do vazio da aba de coleções).
- Erro: `Alert role="alert"` com mensagem segura (sem detalhe interno, NFR-003); erro do envio preserva os arquivos já selecionados no formulário.
- Sucesso: painel de acompanhamento com `role="status"`/`aria-live` na região de situação (mesmo padrão já usado por `FormularioConsulta`/`ChunksFontes`), para que leitores de tela anunciem a mudança de situação sem exigir foco manual.
- Permissão insuficiente: botão "Converter documentos" não aparece para `member`; a aba de conversão continua visível e legível para leitura (AC-010).
- Teclado: linha do lote expansível por Enter/Espaço (`tabIndex=0`, `focus-visible:ring`, mesmo padrão de `DataGridBases`); `Sheet` mantém foco preso e Esc fecha (herdado da primitive).
- Conteúdo longo: nome de arquivo longo quebra sem gerar overflow horizontal da página, mesmo padrão já aplicado em `DataGridBases`/`PainelProgresso`.

#### Contrato CRUD

- Esta superfície reaproveita `PageHeader` (cabeçalho único já existente de `/workspaces/[id]`, sem duplicar markup) e usa `DataGrid`/tabela semântica em largura total para a listagem de lotes, com a coluna `ID` do lote sempre visível, mesma exigência geral de listagem do framework.
- Não é, porém, um CRUD clássico: não há ação de **editar** nem de **apagar** um lote ou um documento pela pessoa (o lote é um registro de processamento, análogo a `Execution`, que também não oferece editar/apagar diretamente — só "Repetir" para falha). O único mecanismo de remoção é a retenção automática de 7 dias (FR-007), comportamento do sistema, não uma ação de apagar disparada pela pessoa; a única ação equivalente disponível é "Reenviar" um documento `falhou` (US-004), que substitui editar/apagar nesta superfície.
- Componentes reaproveitados e novos (`PageHeader`, `DataGrid`, `Sheet`, `Badge`) e seus consumidores seguem registrados em `INTERFACE.md` ao implementar, mesma regra de extensão já aplicada a `UploadBaseSheet`/`PainelProgresso`.

#### Revisão visual durante o desenvolvimento

- A implementação da aba, do `Sheet` e do painel de progresso exige a conferência visual obrigatória (bordas, espaçamentos, margens, padding, tipografia) nos viewports mobile (375 px) e desktop, nos estados carregando/vazio/erro/sucesso/permissão insuficiente, comparando com `DESIGNSYSTEM.MD` e os componentes equivalentes já existentes (`UploadBaseSheet`, `PainelProgresso`, `DataGridBases`). Essa conferência é registrada na tarefa de interface durante a implementação (seção 14, a ser detalhada por `$specsfy-05-tasks`).

#### APIs expostas

- `POST /api/v1/conversoes` — multipart (`arquivos[]`, `workspace_id`); requer sessão + papel de escrita; 201 com lote e documentos; 400 para extensão/tamanho/quantidade inválidos; erros seguem o padrão de `HTTPException` já usado em `bases.py`.
- `GET /api/v1/conversoes?workspace_id=` — lista lotes do Workspace; requer sessão com acesso ao Workspace.
- `GET /api/v1/conversoes/{lote_id}` — detalhe do lote e documentos; 404 fora de escopo.
- `GET /api/v1/conversoes/{lote_id}/documentos/{documento_id}/markdown` — baixa o `.md`; 404 se não concluído ou expirado.
- `GET /api/v1/conversoes/{lote_id}/pacote` — baixa `.zip` com os `.md` concluídos e não expirados.
- `POST /api/v1/conversoes/{lote_id}/documentos/{documento_id}/reenviar` — requer papel de escrita; 400 se o documento não está `falhou` ou já expirou.
- Sem versionamento próprio além do prefixo `/api/v1` já usado por o backend inteiro.

#### APIs externas utilizadas

- Nenhuma API externa é chamada por esta entrega. Toda a extração roda localmente (bibliotecas Python + binário LibreOffice headless + binário Tesseract OCR), sem enviar conteúdo de documento a um serviço de terceiros — reforça NFR-002/privacidade já declarada no backlog.

#### Documentação das APIs consultadas

- Não aplicável; nenhuma API externa consultada.

#### Eventos e outros contratos

- Não aplicável; nenhum evento assíncrono além das tarefas Procrastinate já descritas na seção 8.

### 11. Estratégia TDD

- **Unidade**: cada `DocumentConverter` (`src/pipeline/conversion/converters/*.py`) testado isoladamente com um arquivo de exemplo fixo do formato; `ConverterFactory.for_extension` testado para despacho correto e para `UnsupportedFormatError`.
- **Integração/contrato**: `process_conversion_document_task` (fluxo completo: Storage → conversão → Storage → banco), `purgar_documentos_conversao_task` (expiração real do Storage), e o router `src/app/routers/conversao.py` (validação, permissão, escopo por Workspace/tenant).
- **BDD/aceite**: os 22 cenários `AC-001`–`AC-022` da seção 6 orientam o desenho dos casos TDD; cada `AC` mapeia para ao menos um teste de integração no nível do router ou da tarefa.
- **Runner TDD**: Pytest 8.3+, já estabelecido no projeto (`pyproject.toml`, `tool.pytest.ini_options`); sem decisão a confirmar.
- **E2E**: fluxo completo enviar → acompanhar → baixar exercitado por teste de integração do router + tarefa (sem depender de LibreOffice/Tesseract reais em qualquer teste — usar fixtures de arquivo real para os formatos OOXML e, para `.doc`/`.ppt`/`.xls`/OCR, isolar o binário externo conforme decisão tomada na materialização TDD).
- **Verificação manual**: revisão visual da aba/`Sheet`/painel de progresso nos viewports e estados da seção 10 (inevitável para conferência de bordas, espaçamento e tipografia, que teste automatizado não cobre).

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, AC-001 | AC-001 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_001_converte_pdf_xlsx_jpg_sem_criar_base` | `uv run pytest tests/test_router_conversao.py -k ac_001 -q` → 1 falha: `ImportError` para `process_conversion_document_task`, capacidade ainda ausente em `src/app/tasks.py` | Pending | Pending |
| US-002, US-004, FR-002, FR-004, FR-006, NFR-003, AC-002 | AC-002 na seção 6 | `tests/test_task_process_conversion_document.py::test_spec_0023_ac_002_falha_parcial_nao_interrompe_o_lote` | `uv run pytest tests/test_task_process_conversion_document.py -k ac_002 -q` → 1 falha: `AttributeError` porque `process_conversion_document_task` ainda não existe em `src/app/tasks.py` | Pending | Pending |
| US-001, FR-003, AC-003 | AC-003 na seção 6 | `tests/test_conversion_structure.py::test_spec_0023_ac_003_docx_preserva_titulos_e_tabela` e `::test_spec_0023_ac_003_xlsx_cria_secao_para_cada_planilha` | `uv run pytest tests/test_conversion_structure.py -k ac_003 -q` → 2 falhas: `ModuleNotFoundError` porque `src.pipeline.conversion` ainda não existe | Pending | Pending |
| US-001, FR-001, AC-004 | AC-004 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_004_rejeita_zip_sem_criar_lote` | `uv run pytest tests/test_router_conversao.py -k ac_004 -q` → 1 falha: resposta `404 Not Found` em vez de `400`, pois `POST /api/v1/conversoes` ainda não existe | Pending | Pending |
| FR-001, AC-005 | AC-005 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_005_rejeita_arquivo_acima_de_40_mb`, `::test_spec_0023_ac_005_rejeita_lote_acima_de_50_mb` e `::test_spec_0023_ac_005_rejeita_lote_acima_de_50_arquivos` | `uv run pytest tests/test_router_conversao.py -k ac_005 -q` → 3 falhas: resposta `404 Not Found` em vez de `400` nos três limites, pois `POST /api/v1/conversoes` ainda não existe | Pending | Pending |
| US-004, FR-002, FR-006, NFR-003, AC-006 | AC-006 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_006_reenvia_somente_documento_falho` | `uv run pytest tests/test_router_conversao.py -k ac_006 -q` → 1 falha: resposta `404 Not Found` em vez de `200`, pois `POST /api/v1/conversoes/{lote_id}/documentos/{documento_id}/reenviar` ainda não existe | Pending | Pending |
| US-003, FR-005, AC-007 | AC-007 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_007_baixa_pacote_apenas_com_markdown_concluido` | `uv run pytest tests/test_router_conversao.py -k ac_007 -q` → 1 falha: resposta `404 Not Found` em vez de `200`, pois `GET /api/v1/conversoes/{lote_id}/pacote` ainda não existe | Pending | Pending |
| US-003, FR-005, AC-008 | AC-008 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_008_baixa_markdown_individual_concluido` | `uv run pytest tests/test_router_conversao.py -k ac_008 -q` → 1 falha: resposta `404 Not Found` em vez de `200`, pois `GET /api/v1/conversoes/{lote_id}/documentos/{documento_id}/markdown` ainda não existe | Pending | Pending |
| FR-008, NFR-002, AC-009 | AC-009 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_009_outro_tenant_nao_consulta_nem_baixa_lote` | `uv run pytest tests/test_router_conversao.py -k ac_009 -q` → 1 falha: o acesso do dono respondeu `404` em vez de `200`, provando que a rota ainda não existe antes de avaliar o isolamento externo | Pending | Pending |
| FR-008, AC-010 | AC-010 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_010_member_nao_envia_mas_visualiza_lotes` | `uv run pytest tests/test_router_conversao.py -k ac_010 -q` → 1 falha: o envio por member respondeu `404` em vez do `403` de permissão, pois a rota ainda não existe | Pending | Pending |
| US-002, FR-004, AC-011 | AC-011 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_011_consulta_situacao_do_lote_e_documentos` | `uv run pytest tests/test_router_conversao.py -k ac_011 -q` → 1 falha: a consulta do lote respondeu `404` em vez de `200` | Pending | Pending |
| US-001, FR-003, NFR-001, AC-012 | AC-012 na seção 6 | `tests/test_conversion_image_ocr.py::test_spec_0023_ac_012_ocr_reconhece_texto_em_portugues` e `::test_spec_0023_ac_012_imagem_sem_texto_retorna_markdown_minimo` | `uv run pytest tests/test_conversion_image_ocr.py -k ac_012 -q` → 2 falhas: `ModuleNotFoundError` porque `src.pipeline.conversion` ainda não existe | Pending | Pending |
| FR-007, NFR-002, AC-013 | AC-013 na seção 6 | `tests/test_task_purgar_documentos_conversao.py::test_spec_0023_ac_013_purga_arquivos_mas_preserva_registros` | `uv run pytest tests/test_task_purgar_documentos_conversao.py -k ac_013 -q` → 1 falha: `purgar_documentos_conversao_task` ainda não existe em `src.app.tasks` | Pending | Pending |
| FR-007, AC-014 | AC-014 na seção 6 | `tests/test_task_purgar_documentos_conversao.py::test_spec_0023_ac_014_historico_continua_consultavel_apos_purga` | `uv run pytest tests/test_task_purgar_documentos_conversao.py -k ac_014 -q` → 1 falha: `ImportError` para `purgar_documentos_conversao_task` | Pending | Pending |
| FR-007, NFR-002, AC-015 | AC-015 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_015_download_expirado_orienta_reenvio` | `uv run pytest tests/test_router_conversao.py -k ac_015 -q` → 1 falha: o `404` genérico não informa indisponibilidade nem orienta reenvio | Pending | Pending |
| US-004, FR-006, AC-016 | AC-016 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_016_falha_nao_bloqueia_downloads_concluidos` | `uv run pytest tests/test_router_conversao.py -k ac_016 -q` → 1 falha: o pacote respondeu `404` em vez de `200` | Pending | Pending |
| NFR-001, AC-017 | AC-017 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_017_envio_de_50_documentos_retorna_em_fila` | `uv run pytest tests/test_router_conversao.py -k ac_017 -q` → 1 falha: o envio respondeu `404` em vez de `201` | Pending | Pending |
| NFR-003, AC-018 | AC-018 na seção 6 | `tests/test_task_process_conversion_document.py::test_spec_0023_ac_018_falha_expoe_mensagem_segura_e_loga_tipo_e_origem` | `uv run pytest tests/test_task_process_conversion_document.py -k ac_018 -q` → 1 falha: `process_conversion_document_task` ainda não existe em `src.app.tasks` | Pending | Pending |
| FR-008, NFR-002, AC-019 | AC-019 na seção 6 | `tests/test_router_conversao.py::test_spec_0023_ac_019_ids_de_outro_tenant_parecem_inexistentes` | `uv run pytest tests/test_router_conversao.py -k ac_019 -q` → 1 falha: o acesso do dono respondeu `404` em vez de `200`, impedindo falso positivo pelo `404` externo | Pending | Pending |
| US-001, FR-003 | DEC-006 e normalização legada na seção 8 | `tests/test_conversion_legacy_office.py::test_spec_0023_legacy_doc_e_normalizado_para_docx`, `::test_spec_0023_legacy_ppt_e_normalizado_para_pptx` e `::test_spec_0023_legacy_xls_e_normalizado_para_xlsx` | `uv run pytest tests/test_conversion_legacy_office.py -k legacy -q` → 3 falhas: `ModuleNotFoundError` porque `src.pipeline.conversion` ainda não existe; `soffice` disponível em `/usr/bin/soffice` e isolado por seam no teste | Pending | Pending |
| US-005, FR-004, FR-009, AC-020 | AC-020 na seção 6 | `frontend/src/features/conversao/ListaDocumentosConversao.test.tsx::lista uma linha por documento com situação em rótulo legível` | `cd frontend && npm run test:tdd -- ListaDocumentosConversao` → 1 falha: `AssertionError`, a tabela ainda tem colunas de lote e duas linhas | Pending | Pending |
| US-005, US-003, US-004, FR-005, FR-006, FR-009, AC-021 | AC-021 na seção 6 | `frontend/src/features/conversao/ListaDocumentosConversao.test.tsx::baixa, reenvia e abre o painel do lote...` e `::não oferece reenviar a quem não tem permissão de escrita` | `cd frontend && npm run test:tdd -- ListaDocumentosConversao` → 2 falhas: linha do documento inexistente e 2 linhas em vez de 4 | Pending | Pending |
| US-005, US-001, FR-009, AC-022 | AC-022 na seção 6 | `frontend/src/features/conversao/ListaDocumentosConversao.test.tsx::mostra o vazio com o botão Converter documentos conforme o papel` | `cd frontend && npm run test:tdd -- ListaDocumentosConversao` → 1 falha: não há botão "Converter documentos" no vazio | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001, AC-004, AC-005 | Integração | `tests/test_router_conversao.py` | GREEN em T035 — `uv run pytest tests/test_router_conversao.py -k "ac_001 or ac_004 or ac_005" -q` |
| FR-002 | AC-001, AC-002, AC-006 | Integração | `tests/test_router_conversao.py`, `tests/test_task_process_conversion_document.py` | GREEN em T033/T035/T038 — AC-001/AC-006 via router, AC-002 via `process_conversion_document_task` |
| FR-003 | AC-001, AC-003, AC-012 | Unidade + integração | `tests/test_router_conversao.py`, `tests/test_conversion_structure.py`, `tests/test_conversion_image_ocr.py`, `tests/test_conversion_legacy_office.py` | GREEN completo — AC-001 fechado em T035 (router); AC-003 GREEN em T023/T025; AC-012 GREEN em T026; formatos legados GREEN em T027/T028 |
| FR-004 | AC-001, AC-002, AC-011 | Integração | `tests/test_router_conversao.py`, `tests/test_task_process_conversion_document.py` | GREEN em T033/T035/T036 |
| FR-005 | AC-001, AC-007, AC-008 | Integração | `tests/test_router_conversao.py` | GREEN em T035/T037 |
| FR-006 | AC-002, AC-006, AC-016 | Integração | `tests/test_task_process_conversion_document.py`, `tests/test_router_conversao.py` | GREEN em T033/T038 |
| FR-007 | AC-013, AC-014, AC-015 | Integração | `tests/test_task_purgar_documentos_conversao.py`, `tests/test_router_conversao.py` | GREEN completo — AC-013/AC-014 em T034 (AC-014 desbloqueado pelo router em T035-T037); AC-015 em T037 |
| FR-008 | AC-009, AC-010, AC-019 | Integração | `tests/test_router_conversao.py` | GREEN em T035/T036 |
| NFR-001 | AC-001, AC-012, AC-017 | Unidade + integração | `tests/test_router_conversao.py`, `tests/test_conversion_image_ocr.py` | GREEN em T026/T035 (AC-017 incluso no `POST /conversoes`) |
| NFR-002 | AC-009, AC-013, AC-015, AC-019 | Integração | `tests/test_router_conversao.py`, `tests/test_task_purgar_documentos_conversao.py` | GREEN completo em T034/T036/T037 |
| NFR-003 | AC-002, AC-006, AC-018 | Integração | `tests/test_task_process_conversion_document.py`, `tests/test_router_conversao.py` | GREEN em T033/T038 |
| FR-009 | AC-020, AC-021, AC-022 | Componente (frontend) | `frontend/src/features/conversao/*.test.tsx` (a definir em `$specsfy-05-tasks`) | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (2026-10-14), revalidação após a revisão de 2026-10-14 (US-005, FR-009, AC-020–AC-022, DEC-008).
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0023-fase-1-recebimento-e-processamento-de-documentos-ate-markdown/spec.md --allow-draft` → `VALID DRAFT`; revisão semântica manual com as lentes PROD/ARCH/SEC.
- **Achados**: sem `BLOCKER` e sem `P1 Open`. Cobertura mínima confirmada: 5 US, 9 FR, 3 NFR, cada um com ≥3 `AC` distintos em `**Cobre**` (US-005: AC-020/021/022; FR-009: AC-020/021/022). Sem mudança de API, de persistência ou de stack, então `STACK.md` e `DATABASE.md` seguem válidos e a Definition of Done não ganha item novo.
- **FIND-PROD-002** [P3] [Open] A lista por documento cresce com lotes grandes (até 50 arquivos por lote) e a spec não define filtro nem paginação — Refs: FR-009, DEC-008 — Evidence: seção 17, DEC-008 — Effect: lista longa no Workspace com muitos lotes — Suggestion: tratar filtro e paginação como evolução futura, já registrado como efeito aceito na DEC-008.
- **FIND-ARCH-002** [P3] [Open] A matriz da seção 12 e as tarefas da seção 14 ainda não cobrem US-005/FR-009 — Refs: FR-009, US-005 — Evidence: seções 12 e 14 — Effect: nenhum teste nem tarefa cobre a revisão até o Ato II — Suggestion: `$specsfy-05-tasks` reconcilia a matriz e acrescenta tarefas, o que já é o próximo passo do fluxo.

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-14), replanejamento após a revisão da lista por documento (US-005, FR-009).
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0023-fase-1-recebimento-e-processamento-de-documentos-ate-markdown/spec.md` e `validate_interface_tasks.mjs` → válidos.
- **Achados**: plano com 56 tarefas (T001–T047 preservadas, T048–T056 novas), 39/39 IDs cobertos. T048–T050 materializadas em RED válido (4 falhas em `ListaDocumentosConversao.test.tsx`); implementação liberada a partir de T051.

#### Gate do Ato III — Entrega

- **Resultado**: Pending (reaberto em 2026-10-14; o Delivery Gate de 2026-09-30 comprovou o escopo anterior à revisão).

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um teste de integração falhando em tests/test_router_conversao.py (envio de PDF+XLSX+JPG, resposta imediata, polling até concluído, download individual e em pacote) — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Gherkin do AC-001 e IDs cobertos confirmados; fatia usa PDF, XLSX e JPG reais.
  - [x] **EXECUTE**: Criado `tests/test_router_conversao.py` com marcador próprio `SPECSFY:` e fixtures reais em `tests/fixtures/spec0023/`, sem arquivo `.feature`.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_001 -q` → RED válido (1 falha) por `ImportError`: `process_conversion_document_task` ainda não existe em `src/app/tasks.py`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste de API, sem alteração de tela.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13, cobrindo US-001/US-002/US-003, FR-001–FR-005, NFR-001 e AC-001.
  - [x] **IMPROVE**: O teste cobre os três formatos do cenário, comprova resposta antes do processamento, polling, downloads individual/em pacote e ausência de criação de Base.

- [x] T002 [TEST] [TDD] [US-002] [US-004] Derivar do AC-002 um teste de integração falhando em tests/test_task_process_conversion_document.py (lote com PDF corrompido entre dois documentos válidos) — Refs: US-002, US-004, FR-002, FR-004, FR-006, NFR-003, AC-002 — Depends: none
  - [x] **PREP**: Gherkin do AC-002 confirmado: dois PDFs válidos devem concluir e um PDF corrompido deve falhar sem interromper o lote.
  - [x] **EXECUTE**: Criado `tests/test_task_process_conversion_document.py` com marcador próprio `SPECSFY:`, três documentos persistidos e chamada individual de `process_conversion_document_task`.
  - [x] **VERIFY**: `uv run pytest tests/test_task_process_conversion_document.py -k ac_002 -q` → RED válido (1 falha) por `AttributeError`: `process_conversion_document_task` ainda não existe em `src/app/tasks.py`.
  - [x] **VISUAL**: Não aplicável — teste de tarefa assíncrona de backend, sem alteração de interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13, cobrindo US-002/US-004, FR-002/FR-004/FR-006, NFR-003 e AC-002.
  - [x] **IMPROVE**: O teste executa os três documentos mesmo após a falha intermediária, exige dois resultados concluídos, lote `concluido_com_falhas`, mensagem segura e original corrompido preservado para reenvio.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um teste de unidade falhando em tests/test_conversion_structure.py (DOCX com título e tabela; XLSX com duas planilhas) — Refs: US-001, FR-003, AC-003 — Depends: none
  - [x] **PREP**: Gherkin do AC-003 confirmado e fixtures reais `estrutura.docx`/`duas-planilhas.xlsx` geradas em `tests/fixtures/spec0023/`.
  - [x] **EXECUTE**: Criados dois casos em `tests/test_conversion_structure.py`, cada um com marcador próprio `SPECSFY:`, chamando `DocxConverter` e `XlsxConverter` diretamente.
  - [x] **VERIFY**: `uv run pytest tests/test_conversion_structure.py -k ac_003 -q` → RED válido (2 falhas) por `ModuleNotFoundError`: `src.pipeline.conversion` ainda não existe.
  - [x] **VISUAL**: Não aplicável — testes unitários do pipeline de extração, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13, cobrindo US-001, FR-003 e AC-003.
  - [x] **IMPROVE**: As fixtures exercitam estrutura real: DOCX com dois níveis de título e tabela; XLSX com duas planilhas e tabelas distintas.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um teste de integração falhando em tests/test_router_conversao.py (upload de .zip recusado) — Refs: US-001, FR-001, AC-004 — Depends: none
  - [x] **PREP**: Lista de extensões aceita em FR-001 confirmada; `.zip` não pertence ao conjunto suportado.
  - [x] **EXECUTE**: Adicionado caso com marcador próprio `SPECSFY:` que envia um ZIP válido e exige rejeição antes de persistência ou storage.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_004 -q` → RED válido (1 falha): API respondeu `404` em vez de `400` porque a rota ainda não existe.
  - [x] **VISUAL**: Não aplicável — teste de validação de API, sem alteração de interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13, cobrindo US-001, FR-001 e AC-004.
  - [x] **IMPROVE**: O caso usa um ZIP estruturalmente válido e também exige zero lotes, zero documentos e nenhum arquivo persistido, evitando falso positivo baseado apenas na extensão.

- [x] T005 [TEST] [TDD] Derivar do AC-005 um teste de integração falhando em tests/test_router_conversao.py (arquivo de 45 MB e lote acima de 50 MB/50 arquivos) — Refs: FR-001, AC-005 — Depends: none
  - [x] **PREP**: Confirmados na seção 7 os três limites: 40 MB por arquivo, 50 MB no total do envio e 50 arquivos por lote.
  - [x] **EXECUTE**: Adicionados três casos com marcador próprio `SPECSFY:` para arquivo de 45 MB, lote de 52 MB e lote com 51 arquivos, exigindo `400` e mensagem do limite correspondente.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_005 -q` → RED válido (3 falhas): a API respondeu `404` em vez de `400` porque a rota ainda não existe.
  - [x] **VISUAL**: Não aplicável — teste de validação de API, sem alteração de interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13, cobrindo FR-001 e AC-005; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: Os três limites foram isolados em casos independentes e cada caso também exige ausência de lote, documento e arquivo persistido após a rejeição.

- [x] T006 [TEST] [TDD] [US-004] Derivar do AC-006 um teste de integração falhando em tests/test_router_conversao.py (reenviar documento falhou) — Refs: US-004, FR-002, FR-006, NFR-003, AC-006 — Depends: none
  - [x] **PREP**: Gherkin e endpoint confirmados: somente documento `falhou` dentro da retenção volta à `fila`, limpa `erro`/`expira_em`, muda o lote para `processando` e é reagendado sem alterar documentos concluídos.
  - [x] **EXECUTE**: Adicionado caso com marcador próprio `SPECSFY:` chamando `POST .../reenviar`; o caminho GREEN prepara lote com um documento falho e outro concluído em persistência real assim que modelos e tarefa predecessores existirem.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_006 -q` → RED válido (1 falha): a API respondeu `404` em vez de `200` porque a rota de reenvio ainda não existe.
  - [x] **VISUAL**: Não aplicável — teste de integração de API, sem alteração de interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13, cobrindo US-004, FR-002, FR-006, NFR-003 e AC-006; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: O caso exige também lote de volta a `processando`, limpeza dos campos de falha/retenção, reagendamento exclusivo e preservação do documento já concluído.

- [x] T007 [TEST] [TDD] [US-003] Derivar do AC-007 um teste de integração falhando em tests/test_router_conversao.py (baixar todos os .md concluídos em um pacote) — Refs: US-003, FR-005, AC-007 — Depends: none
  - [x] **PREP**: Gherkin e contrato do endpoint confirmados: o pacote inclui somente `.md` de documentos `concluido` e ainda não expirados; documento `falhou` fica fora.
  - [x] **EXECUTE**: Adicionado caso com marcador próprio `SPECSFY:` preparando dois documentos concluídos e um falho, chamando `GET .../pacote` e abrindo o ZIP para conferir nomes e bytes.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_007 -q` → RED válido (1 falha): a API respondeu `404` em vez de `200` porque a rota de pacote ainda não existe.
  - [x] **VISUAL**: Não aplicável — teste de integração de API e arquivo ZIP, sem alteração de interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13, cobrindo US-003, FR-005 e AC-007; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: Além da lista de nomes, o teste valida os bytes dos dois Markdown dentro do ZIP, evitando falso positivo por entradas vazias ou trocadas.

- [x] T008 [TEST] [TDD] [US-003] Derivar do AC-008 um teste de integração falhando em tests/test_router_conversao.py (baixar um .md individual) — Refs: US-003, FR-005, AC-008 — Depends: none
  - [x] **PREP**: Contrato do endpoint individual confirmado na seção 8: somente documento `concluido` e dentro da retenção entrega seu Markdown.
  - [x] **EXECUTE**: Adicionado caso com marcador `SPECSFY:`, preparando documento concluído e não expirado em banco/Storage quando os modelos estiverem disponíveis e chamando `GET .../documentos/{id}/markdown`.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_008 -q` → RED válido (1 falha): a API respondeu `404` em vez de `200` porque a rota de download individual ainda não existe.
  - [x] **VISUAL**: Não aplicável — teste de integração de API, sem alteração de interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13, cobrindo US-003, FR-005 e AC-008; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: O teste exige os bytes exatos do Markdown e o nome `relatorio.md` no `Content-Disposition`, evitando falso positivo por arquivo vazio, trocado ou sem nome.

- [x] T009 [TEST] [TDD] Derivar do AC-009 um teste de integração falhando em tests/test_router_conversao.py (pessoa de outro Workspace/tenant não acessa o lote) — Refs: FR-008, NFR-002, AC-009 — Depends: none
  - [x] **PREP**: Reaproveitado o padrão de isolamento por tenant/projeto de `get_workspace_or_404` e das suítes de Base.
  - [x] **EXECUTE**: Adicionado caso `SPECSFY:` em que o dono e uma identidade de outro tenant consultam o mesmo lote e pacote.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_009 -q` → RED válido: o acesso de controle do dono recebeu `404` em vez de `200`.
  - [x] **VISUAL**: Não aplicável — teste de integração de API, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: Incluído acesso positivo do dono para impedir falso positivo causado pelo `404` de uma rota inexistente.

- [x] T010 [TEST] [TDD] Derivar do AC-010 um teste de integração falhando em tests/test_router_conversao.py (member sem permissão de escrita não envia, mas visualiza) — Refs: FR-008, AC-010 — Depends: none
  - [x] **PREP**: Reaproveitado o papel `member` real e o contrato de `require_write_role` já usado por Base.
  - [x] **EXECUTE**: Adicionado caso `SPECSFY:` que exige `403` no `POST` e `200` na listagem pelo mesmo member.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_010 -q` → RED válido: o envio recebeu `404` em vez do `403` de permissão.
  - [x] **VISUAL**: Não aplicável — teste de integração de API, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: Um único caso prova simultaneamente a restrição de escrita e a preservação da leitura.

- [x] T011 [TEST] [TDD] [US-002] Derivar do AC-011 um teste de integração falhando em tests/test_router_conversao.py (consultar situação de lote em andamento) — Refs: US-002, FR-004, AC-011 — Depends: none
  - [x] **PREP**: Confirmado o contrato do detalhe de lote e os estados `fila`, `processando` e agregado `processando`.
  - [x] **EXECUTE**: Adicionado caso `SPECSFY:` com dois documentos em estados diferentes e asserção do mapa nome→situação.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_011 -q` → RED válido: o detalhe respondeu `404` em vez de `200`.
  - [x] **VISUAL**: Não aplicável — teste de integração de API, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: A asserção por nome evita aceitar uma lista correta em quantidade, mas com estados associados aos documentos errados.

- [x] T012 [TEST] [TDD] [US-001] Derivar do AC-012 um teste de unidade falhando em tests/test_conversion_image_ocr.py (JPG com texto em português e imagem sem texto reconhecível) — Refs: US-001, FR-003, NFR-001, AC-012 — Depends: none
  - [x] **PREP**: Reutilizada a fixture JPG com texto português e gerada imagem PGM branca determinística no diretório temporário.
  - [x] **EXECUTE**: Criados dois casos `SPECSFY:` chamando `ImageConverter(idioma="por")` diretamente.
  - [x] **VERIFY**: `uv run pytest tests/test_conversion_image_ocr.py -k ac_012 -q` → RED válido (2 falhas): `src.pipeline.conversion` ainda não existe.
  - [x] **VISUAL**: Não aplicável — teste de unidade do pipeline de extração, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; Tesseract português reconheceu previamente a fixture como “Documento de teste em português”.
  - [x] **IMPROVE**: Separados o reconhecimento positivo e o melhor esforço sem texto, evitando que uma única fixture esconda um bloqueio do lote.

- [x] T013 [TEST] [TDD] Derivar do AC-013 um teste de integração falhando em tests/test_task_purgar_documentos_conversao.py (apagar após 7 dias, registro permanece) — Refs: FR-007, NFR-002, AC-013 — Depends: none
  - [x] **PREP**: Confirmado o contrato diário de retenção: apagar original e Markdown, marcar `apagado_em` e preservar as linhas.
  - [x] **EXECUTE**: Criado caso `SPECSFY:` com documento expirado e arquivos reais no Storage temporário, chamando a tarefa periódica.
  - [x] **VERIFY**: `uv run pytest tests/test_task_purgar_documentos_conversao.py -k ac_013 -q` → RED válido: `purgar_documentos_conversao_task` ainda não existe.
  - [x] **VISUAL**: Não aplicável — teste de tarefa periódica de backend, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: O teste confere simultaneamente ausência dos arquivos e permanência de lote, documento, nome e situação.

- [x] T014 [TEST] [TDD] Derivar do AC-014 um teste de integração falhando em tests/test_task_purgar_documentos_conversao.py (histórico do lote consultável após expiração) — Refs: FR-007, AC-014 — Depends: none
  - [x] **PREP**: Confirmada a invariável de que `DocumentoConversao` permanece após a remoção dos arquivos.
  - [x] **EXECUTE**: Criado caso `SPECSFY:` que purga, consulta o lote e exige nome, formato e resultado, além de download indisponível.
  - [x] **VERIFY**: `uv run pytest tests/test_task_purgar_documentos_conversao.py -k ac_014 -q` → RED válido: a tarefa de purga ainda não existe.
  - [x] **VISUAL**: Não aplicável — teste de integração de backend, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: A mesma fixture prova o histórico consultável e o bloqueio do arquivo, cobrindo os dois lados da retenção.

- [x] T015 [TEST] [TDD] Derivar do AC-015 um teste de integração falhando em tests/test_router_conversao.py (tentar baixar documento expirado) — Refs: FR-007, NFR-002, AC-015 — Depends: none
  - [x] **PREP**: Confirmado o `404` com mensagem de indisponibilidade e orientação de reenvio.
  - [x] **EXECUTE**: Criado caso `SPECSFY:` com `expira_em` vencido e `apagado_em` preenchido chamando o download Markdown.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_015 -q` → RED válido: o `404` genérico não contém indisponibilidade nem reenvio.
  - [x] **VISUAL**: Não aplicável — teste de integração de API, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: O oráculo verifica o conteúdo seguro e acionável da resposta, não apenas o status `404`.

- [x] T016 [TEST] [TDD] [US-004] Derivar do AC-016 um teste de integração falhando em tests/test_router_conversao.py (seguir sem reenviar documento que falhou) — Refs: US-004, FR-006, AC-016 — Depends: none
  - [x] **PREP**: Confirmado que nenhuma ação de reenvio é pré-condição para baixar os documentos concluídos.
  - [x] **EXECUTE**: Criado caso `SPECSFY:` com dois concluídos e um falho, baixando o pacote e consultando o motivo preservado.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_016 -q` → RED válido: o pacote respondeu `404` em vez de `200`.
  - [x] **VISUAL**: Não aplicável — teste de integração de API/ZIP, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: O ZIP precisa conter exatamente os dois Markdown, enquanto o detalhe mantém o documento falho e sua mensagem.

- [x] T017 [TEST] [TDD] Derivar do AC-017 um teste de integração falhando em tests/test_router_conversao.py (envio de 50 documentos retorna antes do processamento terminar) — Refs: NFR-001, AC-017 — Depends: none
  - [x] **PREP**: Preparadas 50 partes multipart PDF pequenas, dentro dos limites individuais e total.
  - [x] **EXECUTE**: Criado caso `SPECSFY:` medindo resposta abaixo de 5 s, 50 documentos em `fila` e 50 agendamentos.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_017 -q` → RED válido: o envio respondeu `404` em vez de `201`.
  - [x] **VISUAL**: Não aplicável — teste de integração de API, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: Além do tempo, o caso prova que nenhum documento terminou durante a requisição e que todos foram enfileirados.

- [x] T018 [TEST] [TDD] Derivar do AC-018 um teste de integração falhando em tests/test_task_process_conversion_document.py (mensagem de erro segura, sem detalhe interno) — Refs: NFR-003, AC-018 — Depends: none
  - [x] **PREP**: Reaproveitado o padrão de `_registrar_falha`: mensagem persistida genérica e log apenas com tipo e origem.
  - [x] **EXECUTE**: Criado caso `SPECSFY:` que injeta `RuntimeError` com DSN fictícia, inspeciona o documento e captura o log.
  - [x] **VERIFY**: `uv run pytest tests/test_task_process_conversion_document.py -k ac_018 -q` → RED válido: `process_conversion_document_task` ainda não existe.
  - [x] **VISUAL**: Não aplicável — teste de integração de worker, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: O teste exige tipo/origem no log e proíbe o segredo tanto no banco quanto no log.

- [x] T019 [TEST] [TDD] Derivar do AC-019 um teste de integração falhando em tests/test_router_conversao.py (id direto de lote/documento de outro Workspace responde como não encontrado) — Refs: FR-008, NFR-002, AC-019 — Depends: none
  - [x] **PREP**: Reaproveitado o contrato `404` sem revelar existência de `get_workspace_or_404`.
  - [x] **EXECUTE**: Criado caso `SPECSFY:` com IDs diretos de lote e documento, acesso positivo do dono e tentativas de outro tenant.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k ac_019 -q` → RED válido: o acesso de controle do dono recebeu `404` em vez de `200`.
  - [x] **VISUAL**: Não aplicável — teste de integração de API, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: O controle positivo impede que duas respostas `404` de rotas inexistentes sejam aceitas como isolamento.

- [x] T020 [TEST] [TDD] [US-001] Derivar da seção 8 (normalização de formatos legados) um teste de unidade falhando em tests/test_conversion_legacy_office.py (.doc, .ppt e .xls normalizados via LibreOffice antes da extração) — Refs: US-001, FR-003 — Depends: none
  - [x] **PREP**: Confirmado DEC-006, o comando `soffice --headless --convert-to` e o mapeamento `.doc`→`.docx`, `.ppt`→`.pptx`, `.xls`→`.xlsx`.
  - [x] **EXECUTE**: Criados três casos `SPECSFY:` que interceptam o processo externo, validam o comando/arquivo e delegam ao conversor OOXML equivalente.
  - [x] **VERIFY**: `uv run pytest tests/test_conversion_legacy_office.py -k legacy -q` → RED válido (3 falhas): `src.pipeline.conversion` ainda não existe.
  - [x] **VISUAL**: Não aplicável — teste de unidade do pipeline de extração, sem interface.
  - [x] **EVIDENCE**: RED registrado nas seções 11–13; `soffice` detectado em `/usr/bin/soffice`; proteção do banco `SAFE` e `ruff check` aprovado.
  - [x] **IMPROVE**: O binário é isolado por seam em CI, enquanto o teste ainda verifica o comando exato, a saída OOXML e sua extração.

#### Fase 5 — Revisão de 2026-10-14: RED TDD da lista por documento (US-005, FR-009)

- [x] T048 [TEST] [TDD] [US-005] Derivar do AC-020 um teste de componente falhando em frontend/src/features/conversao/ListaDocumentosConversao.test.tsx (uma linha por documento, colunas e rótulos legíveis de situação) — Refs: US-005, FR-004, FR-009, AC-020 — Depends: none
  - [x] **PREP**: Gherkin e IDs do AC confirmados na seção 6.
  - [x] **EXECUTE**: Teste em `frontend/src/features/conversao/ListaDocumentosConversao.test.tsx` com marcador próprio `SPECSFY:`; sem arquivo `.feature`.
  - [x] **VERIFY**: `cd frontend && npm run test:tdd -- ListaDocumentosConversao` → RED válido: `AssertionError` porque a tabela ainda tem cabeçalhos de lote (ID, Situação, Documentos, Criado em, Criado por) e duas linhas, não uma por documento.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste de comportamento, sem alterar tela.
  - [x] **EVIDENCE**: RED registrado na seção 11.
  - [x] **IMPROVE**: O teste exige quatro linhas, os sete cabeçalhos e os rótulos legíveis, e proíbe os valores crus; falha pela capacidade ausente, não por ambiente.

- [x] T049 [TEST] [TDD] [US-005] [US-003] [US-004] Derivar do AC-021 um teste de componente falhando em frontend/src/features/conversao/ListaDocumentosConversao.test.tsx (baixar, reenviar e abrir o painel do lote pela linha; papel sem escrita) — Refs: US-005, US-003, US-004, FR-005, FR-006, FR-009, AC-021 — Depends: T048
  - [x] **PREP**: Gherkin e IDs do AC confirmados na seção 6.
  - [x] **EXECUTE**: Teste em `frontend/src/features/conversao/ListaDocumentosConversao.test.tsx` com marcador próprio `SPECSFY:`; sem arquivo `.feature`.
  - [x] **VERIFY**: `cd frontend && npm run test:tdd -- ListaDocumentosConversao` → RED válido nos dois casos de AC-021: `TestingLibraryElementError` (linha do documento `relatorio.pdf` inexistente) e `AssertionError` (2 linhas em vez de 4) para o papel member.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste de comportamento, sem alterar tela.
  - [x] **EVIDENCE**: RED registrado na seção 11.
  - [x] **IMPROVE**: O caso exercita Baixar, Reenviar e a abertura por Enter na linha, e um segundo caso cobre o papel sem escrita; os dois falham pela ação ainda ausente.

- [x] T050 [TEST] [TDD] [US-005] [US-001] Derivar do AC-022 um teste de componente falhando em frontend/src/features/conversao/ListaDocumentosConversao.test.tsx (estado vazio com botão "Converter documentos" conforme o papel) — Refs: US-005, US-001, FR-009, AC-022 — Depends: T049
  - [x] **PREP**: Gherkin e IDs do AC confirmados na seção 6.
  - [x] **EXECUTE**: Teste em `frontend/src/features/conversao/ListaDocumentosConversao.test.tsx` com marcador próprio `SPECSFY:`; sem arquivo `.feature`.
  - [x] **VERIFY**: `cd frontend && npm run test:tdd -- ListaDocumentosConversao` → RED válido: `TestingLibraryElementError` — não existe botão "Converter documentos" no estado vazio.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste de comportamento, sem alterar tela.
  - [x] **EVIDENCE**: RED registrado na seção 11.
  - [x] **IMPROVE**: O caso cobre owner (botão chama `onConverter`) e member (sem botão); falha porque o vazio hoje só tem texto.

#### Fase 2 — Fundação: extração e conversão de documentos (pipeline)

**Objetivo**: transformar um documento original em Markdown estruturado, respeitando a fronteira `src/pipeline/`↔`src/app/` da SPEC-0008.
**Teste independente**: `uv run pytest tests/test_conversion_structure.py tests/test_conversion_image_ocr.py tests/test_conversion_legacy_office.py` fica GREEN.

- [x] T021 [CODE] Criar contratos do conversor em src/pipeline/conversion/contracts.py (ConversionResult, DocumentConverter, UnsupportedFormatError, ConversionError) — Refs: FR-003 — Depends: T001, T003, T012
  - [x] **PREP**: Arquitetura da seção 8 e predecessores TDD (T001, T003, T012) confirmados — todos já RED válido.
  - [x] **EXECUTE**: Criados `src/pipeline/conversion/__init__.py` e `src/pipeline/conversion/contracts.py` com `ConversionResult` (dataclass frozen), `DocumentConverter` (Protocol `runtime_checkable`), `ConversionError` e `UnsupportedFormatError`, seguindo o padrão de `src/pipeline/providers/contracts.py`.
  - [x] **VERIFY**: `uv run python -c "from src.pipeline.conversion.contracts import ConversionResult, DocumentConverter, UnsupportedFormatError, ConversionError"` → sem erro.
  - [x] **VISUAL**: Não aplicável — módulo interno sem interface.
  - [x] **EVIDENCE**: Arquivo criado e import confirmado acima; `uv run ruff check src/pipeline/conversion/` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — contrato mínimo e já tipado conforme o padrão de `providers/contracts.py`.
<!-- specsfy:evidence {"task":"T021","refs":["FR-003"],"files":["src/pipeline/conversion/__init__.py","src/pipeline/conversion/contracts.py"],"commands":[{"run":"uv run python -c \"from src.pipeline.conversion.contracts import ConversionResult, DocumentConverter, UnsupportedFormatError, ConversionError\"","exit":0},{"run":"uv run ruff check src/pipeline/conversion/","exit":0}]} -->

- [x] T022 [P] [CODE] [US-001] Implementar PdfConverter com pymupdf4llm em src/pipeline/conversion/converters/pdf.py — Refs: FR-003, AC-001 — Depends: T021, T001, T003, T012
  - [x] **PREP**: DEC-002 confirmada (pymupdf4llm para heurística de cabeçalho/tabela em PDF).
  - [x] **EXECUTE**: Implementado `PdfConverter.converter` chamando `pymupdf4llm.to_markdown(str(caminho))`, com exceções do SDK convertidas em `ConversionError`. Dependência `pymupdf4llm>=1.28.2` adicionada via `uv add` (nenhuma biblioteca de extração existia antes desta entrega, conforme seção 8).
  - [x] **VERIFY**: T001 (`tests/test_router_conversao.py -k ac_001`) depende também de models/router/tasks ainda não implementados (Fase 3-5); o avanço observável nesta fase é `uv run pytest tests/test_conversion_structure.py tests/test_conversion_image_ocr.py tests/test_conversion_legacy_office.py -q` → 7 passed (GREEN completo do escopo de conversão isolada).
  - [x] **VISUAL**: Não aplicável — conversor de backend sem interface.
  - [x] **EVIDENCE**: `uv add pymupdf4llm python-docx python-pptx openpyxl Pillow pytesseract` → 16 pacotes instalados; `uv run ruff check src/pipeline/conversion/` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — heurística delegada inteiramente ao `pymupdf4llm`, sem lógica própria a ajustar.
<!-- specsfy:evidence {"task":"T022","refs":["FR-003","AC-001"],"files":["src/pipeline/conversion/converters/pdf.py"],"commands":[{"run":"uv run pytest tests/test_conversion_structure.py tests/test_conversion_image_ocr.py tests/test_conversion_legacy_office.py -q","exit":0}]} -->

- [x] T023 [P] [CODE] [US-001] Implementar DocxConverter (títulos e tabelas) em src/pipeline/conversion/converters/docx.py — Refs: FR-003, AC-003 — Depends: T021, T001, T003, T012
  - [x] **PREP**: DEC-001 confirmada (extração custom via python-docx); mapeamento `style.name` iniciando em `"Heading "` → `#`/`##`/... pelo número do nível.
  - [x] **EXECUTE**: Implementado `DocxConverter.converter` com `_iter_block_items` (percorre `document.element.body` preservando a ordem real de parágrafos e tabelas) e `_table_to_markdown` (cabeçalho + separador + linhas).
  - [x] **VERIFY**: `uv run pytest tests/test_conversion_structure.py -k docx -q` → 1 passed (GREEN).
  - [x] **VISUAL**: Não aplicável — conversor de backend sem interface.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/pipeline/conversion/converters/docx.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — fidelidade de tabela já cobre células vazias via `celula.text.strip()`.
<!-- specsfy:evidence {"task":"T023","refs":["FR-003","AC-003"],"files":["src/pipeline/conversion/converters/docx.py"],"commands":[{"run":"uv run pytest tests/test_conversion_structure.py -k docx -q","exit":0}]} -->

- [x] T024 [P] [CODE] [US-001] Implementar PptxConverter (slide vira seção) em src/pipeline/conversion/converters/pptx.py — Refs: FR-003, AC-001 — Depends: T021, T001, T003, T012
  - [x] **PREP**: Mapeamento slide → `## Slide {n}: {título}` da seção 8 confirmado.
  - [x] **EXECUTE**: Implementado `PptxConverter.converter` com python-pptx: `slide.shapes.title` vira o título da seção (quando presente) e os demais `shapes` com `text_frame` não vazio viram o corpo.
  - [x] **VERIFY**: AC-001 depende do router/models (Fase 3-5, ainda não implementados); validado indiretamente por `tests/test_conversion_legacy_office.py::test_spec_0023_legacy_ppt_e_normalizado_para_pptx`, que exercita `PptxConverter` sobre um PPTX real — `uv run pytest tests/test_conversion_legacy_office.py -k legacy -q` → 3 passed.
  - [x] **VISUAL**: Não aplicável — conversor de backend sem interface.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/pipeline/conversion/converters/pptx.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária.
<!-- specsfy:evidence {"task":"T024","refs":["FR-003","AC-001"],"files":["src/pipeline/conversion/converters/pptx.py"],"commands":[{"run":"uv run pytest tests/test_conversion_legacy_office.py -k legacy -q","exit":0}]} -->

- [x] T025 [P] [CODE] [US-001] Implementar XlsxConverter (planilha vira seção com tabela) em src/pipeline/conversion/converters/xlsx.py — Refs: FR-003, AC-003 — Depends: T021, T001, T003, T012
  - [x] **PREP**: Mapeamento planilha → `## {nome}` + tabela Markdown da seção 8 confirmado.
  - [x] **EXECUTE**: Implementado `XlsxConverter.converter` com `openpyxl.load_workbook(read_only=True, data_only=True)`, uma seção por `worksheet.title` e tabela Markdown das células preenchidas (`_planilha_para_tabela`).
  - [x] **VERIFY**: `uv run pytest tests/test_conversion_structure.py -k xlsx -q` → 1 passed (GREEN).
  - [x] **VISUAL**: Não aplicável — conversor de backend sem interface.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/pipeline/conversion/converters/xlsx.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária.
<!-- specsfy:evidence {"task":"T025","refs":["FR-003","AC-003"],"files":["src/pipeline/conversion/converters/xlsx.py"],"commands":[{"run":"uv run pytest tests/test_conversion_structure.py -k xlsx -q","exit":0}]} -->

- [x] T026 [P] [CODE] [US-001] Implementar ImageConverter (OCR pytesseract, idioma por) em src/pipeline/conversion/converters/image.py — Refs: FR-003, NFR-001, AC-012 — Depends: T021, T001, T003, T012
  - [x] **PREP**: Idioma padrão `por` e melhor esforço sem bloqueio (seção 16) confirmados.
  - [x] **EXECUTE**: Implementado `ImageConverter` (dataclass, `idioma: str = "por"`) com Pillow (`Image.open`) + `pytesseract.image_to_string`; texto vazio após OCR retorna Markdown mínimo com aviso `ocr_sem_texto_reconhecido`, sem levantar erro.
  - [x] **VERIFY**: `uv run pytest tests/test_conversion_image_ocr.py -k ac_012 -q` → 2 passed (GREEN).
  - [x] **VISUAL**: Não aplicável — conversor de backend sem interface.
  - [x] **EVIDENCE**: Comando acima; `tesseract-ocr`/`tesseract-ocr-por` disponíveis nesta máquina (`/usr/bin/tesseract`, idiomas `eng`, `osd`, `por`); `uv run ruff check src/pipeline/conversion/converters/image.py` → All checks passed.
  - [x] **IMPROVE**: Melhoria aplicada — imagem sem texto reconhecido não é tratada como erro: devolve `ConversionResult` com Markdown mínimo e um aviso em `avisos`, preservando o melhor esforço sem bloquear o lote.
<!-- specsfy:evidence {"task":"T026","refs":["FR-003","NFR-001","AC-012"],"files":["src/pipeline/conversion/converters/image.py"],"commands":[{"run":"uv run pytest tests/test_conversion_image_ocr.py -k ac_012 -q","exit":0}]} -->

- [x] T027 [CODE] Implementar normalizar_formato_legado (LibreOffice headless) em src/pipeline/conversion/legacy_office.py — Refs: FR-003 — Depends: T021, T001, T003, T012, T020
  - [x] **PREP**: DEC-006 confirmada; comando `soffice --headless --convert-to <destino> --outdir <tmp> <origem>`.
  - [x] **EXECUTE**: Implementado `normalizar_formato_legado(caminho, extensao) -> Path`: mapeia `.doc`→`.docx`, `.ppt`→`.pptx`, `.xls`→`.xlsx`; cria diretório temporário com `tempfile.mkdtemp`; chama `subprocess.run` com `timeout=60` e `check=False`, levantando `ConversionError` em timeout, erro de SO ou `returncode != 0`.
  - [x] **VERIFY**: `soffice` disponível nesta máquina (`/usr/bin/soffice`) — não foi necessário skip. `uv run pytest tests/test_conversion_legacy_office.py -k legacy -q` → 3 passed (GREEN).
  - [x] **VISUAL**: Não aplicável — conversor de backend sem interface.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/pipeline/conversion/legacy_office.py` → All checks passed.
  - [x] **IMPROVE**: Timeout de 60s aplicado (`_TIMEOUT_SEGUNDOS`) para não bloquear indefinidamente um `soffice` travado; sem retry — falha de conversão já sobe como `ConversionError` tratável pelo chamador.
<!-- specsfy:evidence {"task":"T027","refs":["FR-003"],"files":["src/pipeline/conversion/legacy_office.py"],"commands":[{"run":"uv run pytest tests/test_conversion_legacy_office.py -k legacy -q","exit":0}]} -->

- [x] T028 [CODE] Implementar ConverterFactory.for_extension em src/pipeline/conversion/factory.py (despacha por extensão, normaliza formato legado antes de delegar) — Refs: FR-003 — Depends: T021, T022, T023, T024, T025, T026, T027, T001, T003, T012
  - [x] **PREP**: Padrão de despacho de `ProviderFactory` (`src/pipeline/providers/factory.py`) confirmado e reaproveitado.
  - [x] **EXECUTE**: Implementado `ConverterFactory.for_extension(extensao)` com dicionário `_CONVERSORES` (pdf/docx/pptx/xlsx/jpg/jpeg/png) e adapter interno `_ExtensaoConverter` que chama `normalizar_formato_legado` para `doc`/`ppt`/`xls` antes de delegar ao conversor OOXML equivalente; extensão desconhecida levanta `UnsupportedFormatError` listando as opções.
  - [x] **VERIFY**: `uv run pytest tests/test_conversion_structure.py tests/test_conversion_image_ocr.py tests/test_conversion_legacy_office.py -q` → 7 passed (GREEN completo).
  - [x] **VISUAL**: Não aplicável — módulo interno sem interface.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/pipeline/conversion/` → All checks passed.
  - [x] **IMPROVE**: Melhoria aplicada — mensagem de `UnsupportedFormatError` lista as extensões suportadas (conversores diretos + legados), facilitando o diagnóstico.
<!-- specsfy:evidence {"task":"T028","refs":["FR-003"],"files":["src/pipeline/conversion/factory.py"],"commands":[{"run":"uv run pytest tests/test_conversion_structure.py tests/test_conversion_image_ocr.py tests/test_conversion_legacy_office.py -q","exit":0}]} -->

- [x] T029 [CODE] Expor convert_document na fachada em src/pipeline/service.py — Refs: FR-003 — Depends: T028, T001, T003, T012
  - [x] **PREP**: PR-001 (fronteira `src/pipeline/`↔`src/app/`) e o padrão de `__all__` do arquivo confirmados.
  - [x] **EXECUTE**: Adicionado `convert_document(caminho: _Path, extensao: str) -> _ConversionResult`, delegando a `ConverterFactory.for_extension`, incluído em `__all__`; imports de `ConversionResult`/`ConverterFactory` seguem o padrão de alias com underscore já usado no arquivo.
  - [x] **VERIFY**: `uv run python -c "from src.pipeline.service import convert_document"` → sem erro.
  - [x] **VISUAL**: Não aplicável — módulo interno sem interface.
  - [x] **EVIDENCE**: Comando acima; `docs/architecture.md` atualizado com a linha de contrato de `convert_document` (exigido por `tests/test_docs_safety.py::test_toda_operacao_publica_da_fachada_aparece_no_contrato`); `uv run ruff check src/pipeline/service.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária.
<!-- specsfy:evidence {"task":"T029","refs":["FR-003"],"files":["src/pipeline/service.py"],"commands":[{"run":"uv run python -c \"from src.pipeline.service import convert_document\"","exit":0}]} -->

#### Fase 3 — Fundação: persistência e processamento assíncrono

**Objetivo**: registrar o lote e cada documento, e processar/expirar cada um sem bloquear a requisição.
**Teste independente**: `uv run pytest tests/test_task_process_conversion_document.py tests/test_task_purgar_documentos_conversao.py` fica GREEN.

- [x] T030 [CODE] Criar migration Alembic para lotes_conversao e documentos_conversao em alembic/versions/0022_lotes_conversao.py — Refs: FR-002, FR-004, FR-007 — Depends: T001, T002, T013
  - [x] **PREP**: Modelo de dados da seção 9 e índices `(workspace_id, criado_em)`/`(lote_id)` confirmados.
  - [x] **EXECUTE**: Criado `alembic/versions/0022_lotes_conversao.py` (revision `0022_lotes_conversao`, down_revision `0021_assistente`) com `upgrade`/`downgrade` criando `lotes_conversao` (+ índice `ix_lotes_conversao_workspace_criado`) e `documentos_conversao` (+ índice `ix_documentos_conversao_lote`); nenhuma tabela existente é alterada. `situacao` usa `String(30)` em `lotes_conversao` (cobre `concluido_com_falhas`, 21 caracteres) e `String(20)` em `documentos_conversao`.
  - [x] **VERIFY**: Banco de teste isolado (`rag_pipeline_test`, porta 55432) estava com `alembic_version=0020_pessoas` embora `conversas_assistente`/`mensagens_assistente` (SPEC-0021) já existissem com schema idêntico ao de `0021_assistente.py` — divergência pré-existente entre o registro de revisão e o schema real, não causada por esta tarefa; corrigida com `alembic stamp 0021_assistente` antes de aplicar a nova migration. `APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test uv run alembic upgrade head` → `Running upgrade 0021_assistente -> 0022_lotes_conversao` (exit 0); `uv run alembic current` → `0022_lotes_conversao (head)`.
  - [x] **VISUAL**: Não aplicável — migration de schema, sem interface.
  - [x] **EVIDENCE**: Comandos e revisão acima; `uv run ruff check alembic/versions/0022_lotes_conversao.py` → All checks passed.
  - [x] **IMPROVE**: Nenhum ajuste de índice adicional — os dois índices da seção 9 (`workspace_id, criado_em` e `lote_id`) já cobrem a listagem de lotes e a consulta de documentos por lote.
<!-- specsfy:evidence {"task":"T030","refs":["FR-002","FR-004","FR-007"],"files":["alembic/versions/0022_lotes_conversao.py"],"commands":[{"run":"APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test uv run alembic upgrade head","exit":0},{"run":"APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_test uv run alembic current","exit":0}]} -->

- [x] T031 [CODE] Criar models LoteConversao e DocumentoConversao em src/app/models.py — Refs: FR-002, FR-004, FR-007 — Depends: T030, T001, T002, T013
  - [x] **PREP**: Atributos e relações da seção 9 (Entidades) confirmados.
  - [x] **EXECUTE**: Implementadas `LoteConversao` e `DocumentoConversao` seguindo o padrão de `Base`/`Execution`: `workspace`/`autor` via `relationship(foreign_keys=[...])` sem `back_populates` (mesmo padrão de `Execution.autor`, sem tocar `Workspace`/`Pessoa`); `LoteConversao.documentos`/`DocumentoConversao.lote` com `back_populates` bidirecional, contido nas duas classes novas. Adicionadas a `__all__`.
  - [x] **VERIFY**: `uv run python -c "from src.app.models import LoteConversao, DocumentoConversao"` → sem erro; `configure_mappers()` do SQLAlchemy também confirmado sem erro (relações válidas).
  - [x] **VISUAL**: Não aplicável — model de backend sem interface.
  - [x] **EVIDENCE**: Comandos acima; `uv run ruff check src/app/models.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — índices e constraints já definidos na migration T030 (`ix_lotes_conversao_workspace_criado`, `ix_documentos_conversao_lote`).
<!-- specsfy:evidence {"task":"T031","refs":["FR-002","FR-004","FR-007"],"files":["src/app/models.py"],"commands":[{"run":"uv run python -c \"from src.app.models import LoteConversao, DocumentoConversao\"","exit":0},{"run":"uv run ruff check src/app/models.py","exit":0}]} -->

- [x] T032 [CODE] Implementar list_lotes_for_identity, get_lote_or_404, get_documento_or_404 e recalcular_situacao_lote em src/app/repo.py — Refs: FR-004, FR-008 — Depends: T031, T001, T011, T009
  - [x] **PREP**: Padrão de `get_workspace_or_404`/`list_bases_for_identity` confirmado e reaproveitado.
  - [x] **EXECUTE**: Implementadas as quatro funções: `list_lotes_for_identity` filtra por `tenant_id`/`project_id`/`workspace_id` opcional, mais recentes primeiro; `get_lote_or_404` e `get_documento_or_404` seguem o padrão 404-sem-revelar-existência de `get_workspace_or_404` (o documento também exige `lote_id` correspondente); `recalcular_situacao_lote` lê as `situacao` dos documentos do lote e grava `processando`/`concluido_com_falhas`/`concluido` sem commitar — a transação fica a cargo de `process_conversion_document_task` (T033), conforme seção 8.
  - [x] **VERIFY**: `uv run python -c "from src.app.repo import list_lotes_for_identity, get_lote_or_404, get_documento_or_404, recalcular_situacao_lote"` → sem erro.
  - [x] **VISUAL**: Não aplicável — repositório de backend sem interface.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/app/repo.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária — consultas já são de baixo custo (uma por lote, mesmo padrão de `list_bases_for_identity`).
<!-- specsfy:evidence {"task":"T032","refs":["FR-004","FR-008"],"files":["src/app/repo.py"],"commands":[{"run":"uv run python -c \"from src.app.repo import list_lotes_for_identity, get_lote_or_404, get_documento_or_404, recalcular_situacao_lote\"","exit":0},{"run":"uv run ruff check src/app/repo.py","exit":0}]} -->

- [x] T033 [CODE] Implementar process_conversion_document_task em src/app/tasks.py — Refs: FR-002, FR-003, FR-004, NFR-003 — Depends: T029, T031, T032, T001, T002, T012
  - [x] **PREP**: Padrão de `process_base_task`/`_registrar_falha` confirmado e reaproveitado.
  - [x] **EXECUTE**: Implementada `process_conversion_document_task(*, documento_id)` com `@app.task`: marca `processando`, materializa o original via `storage.materialize`, chama `service.convert_document(caminho, documento.formato)`, salva `{stem}.md` na mesma chave do Storage, marca `concluido`/`falhou` e sempre grava `concluido_em`/`expira_em` (+7 dias, inclusive em falha, por FR-007) antes de `recalcular_situacao_lote` (T032) na mesma transação. Erro seguro via `_registrar_falha_documento` (mesmo padrão de `_registrar_falha`: tipo+origem no log, mensagem genérica persistida). **Dependência oculta revelada**: `LocalDirectoryStorage.materialize` só copiava `*.md` (suficiente para `Base`, que só recebe Markdown); `S3CompatibleStorage.materialize` já copiava qualquer objeto. Corrigido `src/app/storage.py` para copiar qualquer arquivo (`glob("*")` + `is_file()`), alinhando as duas implementações do protocolo — sem isso o original (PDF/DOCX/...) nunca chegava ao conversor.
  - [x] **VERIFY**: `uv run pytest tests/test_task_process_conversion_document.py -v` → 2 passed (GREEN); `uv run pytest tests/test_app_bases.py -q` → 21 passed (sem regressão em `Base` após a mudança em `storage.py`).
  - [x] **VISUAL**: Não aplicável — tarefa assíncrona de backend.
  - [x] **EVIDENCE**: Comandos acima; `uv run ruff check src/app/tasks.py src/app/storage.py` → All checks passed.
  - [x] **IMPROVE**: Melhoria aplicada — alinhamento de `LocalDirectoryStorage.materialize` com `S3CompatibleStorage.materialize` (ambas agora copiam qualquer arquivo, não só `*.md`), documentado acima como dependência oculta revelada por esta tarefa.
<!-- specsfy:evidence {"task":"T033","refs":["FR-002","FR-003","FR-004","NFR-003"],"files":["src/app/tasks.py","src/app/storage.py"],"commands":[{"run":"uv run pytest tests/test_task_process_conversion_document.py -v","exit":0},{"run":"uv run pytest tests/test_app_bases.py -q","exit":0}]} -->

- [x] T034 [CODE] Implementar purgar_documentos_conversao_task em src/app/tasks.py — Refs: FR-007, NFR-002 — Depends: T031, T032, T013, T014, T015
  - [x] **PREP**: Padrão de `purgar_dados_de_acesso_task` (`@app.periodic`) confirmado e reaproveitado.
  - [x] **EXECUTE**: Implementada `purgar_documentos_conversao_task(_timestamp)` com `@app.periodic(cron="0 3 * * *")` + `@app.task`: seleciona `DocumentoConversao` com `expira_em <= agora()` e `apagado_em is None`, chama `storage.delete_base(documento.id)` e grava `apagado_em`; a linha nunca é removida. **Dependência oculta revelada**: o teste AC-013 chama `storage.list_files(documento_id)`, ausente do protocolo `Storage` — adicionado a `Storage`, `LocalDirectoryStorage` e `S3CompatibleStorage` em `src/app/storage.py` (lista os nomes de arquivo sob uma chave; `S3CompatibleStorage` pagina `list_objects_v2`).
  - [x] **VERIFY**: `uv run pytest tests/test_task_purgar_documentos_conversao.py -v` → AC-013 (`test_spec_0023_ac_013_purga_arquivos_mas_preserva_registros`) passed; AC-014 (`test_spec_0023_ac_014_historico_continua_consultavel_apos_purga`), na época desta tarefa, ainda dependia do router da Fase 4 (T035-T038, fora do `Depends` de T034) e falhava com `404` em `GET /api/v1/conversoes/{lote_id}`. Revalidado após T035-T037: `uv run pytest tests/test_task_purgar_documentos_conversao.py -v` → 2 passed (GREEN completo).
  - [x] **VISUAL**: Não aplicável — tarefa periódica de backend.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/app/tasks.py src/app/storage.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária além do `list_files` já registrado como dependência oculta.
<!-- specsfy:evidence {"task":"T034","refs":["FR-007","NFR-002"],"files":["src/app/tasks.py","src/app/storage.py"],"commands":[{"run":"uv run pytest tests/test_task_purgar_documentos_conversao.py::test_spec_0023_ac_013_purga_arquivos_mas_preserva_registros -q","exit":0},{"run":"uv run ruff check src/app/tasks.py src/app/storage.py","exit":0}]} -->

#### Fase 4 — US-001/US-002/US-003/US-004 — API de conversão

**Objetivo**: expor o envio, o acompanhamento, o download e o reenvio de documentos pela API.
**Teste independente**: `uv run pytest tests/test_router_conversao.py` fica GREEN.

- [x] T035 [CODE] [US-001] Implementar POST /api/v1/conversoes em src/app/routers/conversao.py e registrar o router em src/app/main.py — Refs: FR-001, FR-002, FR-008 — Depends: T033, T032, T004, T005, T009
  - [x] **PREP**: Padrão de `enviar_base` (`bases.py`) confirmado e reaproveitado para validação e criação.
  - [x] **EXECUTE**: Criado `src/app/routers/conversao.py` com `POST /api/v1/conversoes`: `require_write_role`, valida Workspace (`_workspace_do_envio`, mesmo padrão de `_workspace_do_upload`), valida cada arquivo (10 extensões aceitas, 40 MB/arquivo, 50 MB/lote, 50 arquivos/lote), cria `LoteConversao` + um `DocumentoConversao` por arquivo (`situacao="fila"`), salva cada original no Storage chaveado por `documento.id` e agenda `process_conversion_document_task.defer(documento_id=...)` — resposta devolvida antes do processamento (NFR-001). Registrado `app.include_router(conversao.router)` em `src/app/main.py`.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k "ac_004 or ac_005" -q` → 4 passed (GREEN).
  - [x] **VISUAL**: Não aplicável — endpoint de API sem tela própria.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/app/routers/conversao.py src/app/main.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária além das mensagens já explícitas por limite (extensão, 40 MB, 50 MB, 50 arquivos).
<!-- specsfy:evidence {"task":"T035","refs":["FR-001","FR-002","FR-008"],"files":["src/app/routers/conversao.py","src/app/main.py"],"commands":[{"run":"uv run pytest tests/test_router_conversao.py -k \"ac_004 or ac_005\" -q","exit":0},{"run":"uv run ruff check src/app/routers/conversao.py src/app/main.py","exit":0}]} -->

- [x] T036 [CODE] [US-002] Implementar GET /api/v1/conversoes e GET /api/v1/conversoes/{lote_id} em src/app/routers/conversao.py — Refs: FR-004, FR-008, NFR-002 — Depends: T035, T011, T009, T019
  - [x] **PREP**: Formato de resposta do polling (seção 10) confirmado: lote com `situacao` agregada e `documentos[]` com `situacao` individual.
  - [x] **EXECUTE**: Implementados `GET /api/v1/conversoes` (`repo.list_lotes_for_identity`, filtro opcional por `workspace_id`) e `GET /api/v1/conversoes/{lote_id}` (`repo.get_lote_or_404`); ambos usam `_serializar_lote`/`_serializar_documento` e o 404 de `get_lote_or_404`/`get_workspace_or_404` sem revelar existência fora do escopo (AC-019).
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k "ac_009 or ac_011 or ac_019" -q` → 3 passed (GREEN).
  - [x] **VISUAL**: Não aplicável — endpoint de API sem tela própria.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/app/routers/conversao.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária.
<!-- specsfy:evidence {"task":"T036","refs":["FR-004","FR-008","NFR-002"],"files":["src/app/routers/conversao.py"],"commands":[{"run":"uv run pytest tests/test_router_conversao.py -k \"ac_009 or ac_011 or ac_019\" -q","exit":0}]} -->

- [x] T037 [CODE] [US-003] Implementar download individual e em pacote em src/app/routers/conversao.py — Refs: FR-005, FR-007 — Depends: T035, T007, T008, T015
  - [x] **PREP**: Uso de `zipfile` em memória (seção 8) confirmado.
  - [x] **EXECUTE**: Implementados `GET .../documentos/{id}/markdown` (materializa a chave do documento em diretório temporário via `storage.materialize`, lê `{stem}.md`; 404 com "indisponível"/"reenvie" se não `concluido` ou `apagado_em` preenchido — AC-015) e `GET .../pacote` (materializa cada documento `concluido`/não apagado em subpasta própria e grava seu `.md` num `zipfile.ZipFile` em memória, `Content-Type: application/zip`). Nenhuma função nova no protocolo `Storage`: reaproveita `materialize` (já ajustado em T033 para copiar qualquer arquivo).
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k "ac_007 or ac_008 or ac_015" -q` → 3 passed (GREEN).
  - [x] **VISUAL**: Não aplicável — endpoint de API sem tela própria.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/app/routers/conversao.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária.
<!-- specsfy:evidence {"task":"T037","refs":["FR-005","FR-007"],"files":["src/app/routers/conversao.py"],"commands":[{"run":"uv run pytest tests/test_router_conversao.py -k \"ac_007 or ac_008 or ac_015\" -q","exit":0}]} -->

- [x] T038 [CODE] [US-004] Implementar POST /api/v1/conversoes/{lote_id}/documentos/{documento_id}/reenviar em src/app/routers/conversao.py — Refs: FR-002, FR-006 — Depends: T035, T034, T002, T006, T016
  - [x] **PREP**: Limpeza de `erro`/`expira_em` ao voltar para `fila` (seção 8) confirmada.
  - [x] **EXECUTE**: Implementado `POST .../reenviar`: `require_write_role`; 400 se `documento.situacao != "falhou"` ou `apagado_em` preenchido; senão `situacao="fila"`, `erro=None`, `expira_em=None`, `concluido_em=None`, chama `recalcular_situacao_lote` (volta o lote a `processando`) e reagenda `process_conversion_document_task.defer(documento_id=...)` reusando o original já salvo no Storage.
  - [x] **VERIFY**: `uv run pytest tests/test_router_conversao.py -k "ac_006 or ac_016" -q` → 2 passed (GREEN).
  - [x] **VISUAL**: Não aplicável — endpoint de API sem tela própria.
  - [x] **EVIDENCE**: Comando acima; `uv run ruff check src/app/routers/conversao.py` → All checks passed.
  - [x] **IMPROVE**: Nenhuma melhoria necessária.
<!-- specsfy:evidence {"task":"T038","refs":["FR-002","FR-006"],"files":["src/app/routers/conversao.py"],"commands":[{"run":"uv run pytest tests/test_router_conversao.py -k \"ac_006 or ac_016\" -q","exit":0}]} -->

#### Fase de interface

- [x] T039 [CODE] [US-001] [US-002] Instalar a primitive Tabs (shadcn/ui) e compor a aba "Conversão de documentos" em frontend/src/components/ui/tabs.tsx e frontend/src/app/(autenticado)/workspaces/[id]/page.tsx — Refs: US-001, US-002 — Depends: T035, T036, T001, T004, T011
  - [x] **PREP**: Confirmado em `INTERFACE.md`/`ls frontend/src/components/ui/` que `Tabs` não existia. `$specsfy-specialist-shadcn-ui` carregado via Skill; `$specsfy-specialist-react-ui-components` existe em `.agents/skills/` mas não está na listagem de skills carregáveis desta sessão — seu `SKILL.md` foi lido diretamente como referência (fluxo, padrões e antipadrões) em substituição à invocação formal.
  - [x] **EXECUTE**: `npx shadcn@latest add tabs` criou `frontend/src/components/ui/tabs.tsx` (`Tabs`/`TabsList`/`TabsTrigger`/`TabsContent` sobre `@base-ui/react/tabs`). Composto em `workspaces/[id]/page.tsx`: `Tabs defaultValue="bases"` logo abaixo do `PageHeader`, com `TabsTrigger` "Bases" (conteúdo atual, preservado) e "Conversão de documentos" (novo `DataGridLotesConversao`); estado de `lotes` buscado no mesmo `Promise.all` de workspace/bases; botão "Converter documentos" adicionado ao bloco de ações já restrito a `podeEscrever` (owner/admin), ao lado de "Enviar base".
  - [x] **VERIFY**: `npm run test:tdd -- Workspace` → 5 arquivos, 27 passed (inclui a troca de aba via `page.test.tsx`, atualizado para a 3ª chamada `fetch` de `/api/v1/conversoes`). `npm run typecheck` e `npm run build` → OK.
  - [x] **VISUAL**: Revisão manual com Playwright headless (dev server real, backend contra o banco de teste isolado) em 375 px e 1440 px: bordas, espaçamentos, margens, padding e tipografia das abas (`TabsList`/`TabsTrigger`) consistentes com `PageHeader`/`DataGridBases` existentes; abas empilham sem overflow horizontal da página no mobile. Evidência em `T042` (mesma sessão de revisão cobre as quatro tarefas da Fase de interface).
  - [x] **EVIDENCE**: Comandos acima; `npm run lint` → sem erros.
  - [x] **IMPROVE**: Nenhuma melhoria adicional de acessibilidade necessária — `Tabs`/`TabsTrigger` do shadcn/ui já trazem navegação por teclado (setas, Home/End) e `aria-selected` do Base UI.
<!-- specsfy:evidence {"task":"T039","refs":["US-001","US-002"],"files":["frontend/src/components/ui/tabs.tsx","frontend/src/app/(autenticado)/workspaces/[id]/page.tsx"],"commands":[{"run":"npm run test:tdd -- Workspace","exit":0},{"run":"npm run build","exit":0}]} -->

- [x] T040 [P] [CODE] [US-001] Implementar ConversaoSheet.tsx (formulário de envio e painel de acompanhamento) em frontend/src/features/conversao/ConversaoSheet.tsx — Refs: US-001, FR-001, FR-005 — Depends: T035, T037, T001, T004, T007
  - [x] **PREP**: `UploadBaseSheet.tsx` lido como modelo (validação client-side espelhando o backend, `Sheet` contextual, erro preservando seleção).
  - [x] **EXECUTE**: Implementado `ConversaoSheet` sobre `Sheet`: input `type="file" multiple accept=".pdf,.ppt,.pptx,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"`, lista removível com nome+tamanho, validação client-side (10 extensões, 40 MB/arquivo, 50 MB total, 50 arquivos) antes do `POST /api/v1/conversoes` (`FormData`); após 201, o formulário é substituído por `PainelLoteConversao` no mesmo `Sheet` (sem fechar), que assume o polling.
  - [x] **VERIFY**: `npm run typecheck` e `npm run lint` → OK (corrigido `react-hooks/set-state-in-effect`: o reset ao fechar foi removido porque o componente já desmonta/remonta via renderização condicional no pai, como `UploadBaseSheet`). Exercitado manualmente via Playwright: seleção de arquivo, envio e transição para o painel de acompanhamento sem fechar o `Sheet` (ver T042).
  - [x] **VISUAL**: Bordas, espaçamentos, margens, padding e tipografia do `Sheet` conferidos em 375 px e desktop, nos estados vazio/arquivo selecionado/enviando/painel de acompanhamento, comparando com `UploadBaseSheet` — evidência consolidada (screenshots) em T042.
  - [x] **EVIDENCE**: Arquivo criado: `frontend/src/features/conversao/ConversaoSheet.tsx`; comandos acima.
  - [x] **IMPROVE**: Melhoria aplicada — erro de envio (`Alert`) preserva a seleção de arquivos ao invés de limpá-la, mesmo padrão de `UploadBaseSheet`.
<!-- specsfy:evidence {"task":"T040","refs":["US-001","FR-001","FR-005"],"files":["frontend/src/features/conversao/ConversaoSheet.tsx"],"commands":[{"run":"npm run typecheck","exit":0},{"run":"npm run lint","exit":0}]} -->

- [x] T041 [P] [CODE] [US-002] Implementar DataGridLotesConversao.tsx em frontend/src/features/conversao/DataGridLotesConversao.tsx — Refs: US-002, FR-004 — Depends: T036, T001, T011, T002
  - [x] **PREP**: `DataGridBases.tsx` lido como modelo (tabela semântica, coluna `ID` sempre visível, largura contida com rolagem interna).
  - [x] **EXECUTE**: Implementada tabela semântica com colunas ID/Situação/Documentos/Criado em/Criado por; linha com `tabIndex=0`, `aria-expanded`, `aria-controls` e `aria-label` expande (não navega — sem rota própria, seção 10) para uma segunda `<tr>` com `PainelLoteConversao` num `<td colSpan>`. **Defeito corrigido durante a revisão visual**: a primeira versão sobrescrevia o `role` nativo de `<tr>` para `role="button"`, quebrando a semântica de tabela para leitor de tela (perde contagem de linhas/colunas); removido, mantendo o `role="row"` nativo com `aria-expanded`.
  - [x] **VERIFY**: `npm run typecheck`/`npm run lint` → OK. Exercitado por Playwright: carregando (`Skeleton`), vazio, expansão por clique e teclado (Enter/Espaço) em duas linhas diferentes simultaneamente (ver `desktop-09-estados-concluido-falhou.png`).
  - [x] **VISUAL**: Bordas, espaçamentos, margens, padding e tipografia da tabela conferidos em 375 px e desktop (cabeçalho, linha, linha expandida), comparando com `DataGridBases` — evidência consolidada (screenshots) em T042.
  - [x] **EVIDENCE**: Arquivo criado: `frontend/src/features/conversao/DataGridLotesConversao.tsx`; comandos acima.
  - [x] **IMPROVE**: Correção de acessibilidade aplicada (remoção do `role="button"` indevido sobre `<tr>`, achado nesta revisão).
<!-- specsfy:evidence {"task":"T041","refs":["US-002","FR-004"],"files":["frontend/src/features/conversao/DataGridLotesConversao.tsx"],"commands":[{"run":"npm run typecheck","exit":0},{"run":"npm run lint","exit":0}]} -->

- [x] T042 [P] [CODE] [US-002] [US-003] [US-004] Implementar PainelLoteConversao.tsx (situação por documento, download, reenviar) em frontend/src/features/conversao/PainelLoteConversao.tsx — Refs: US-002, US-003, US-004, FR-004, FR-005, FR-006 — Depends: T036, T037, T038, T002, T007, T016
  - [x] **PREP**: `PainelProgresso.tsx` lido como modelo (`Badge` por situação, polling, ação condicionada a papel).
  - [x] **EXECUTE**: Implementado `PainelLoteConversao` com `Badge` por situação (`default`=concluído, `destructive`=falhou, `secondary`=fila/processando), polling a cada 3 s via `setInterval` enquanto houver documento `fila`/`processando`, "Baixar" por documento concluído e "Baixar todos" (habilitado só com ao menos um concluído) via `apiFetch` + `Blob`/`URL.createObjectURL`, "Reenviar" por documento falhou restrito a `podeEscrever`. Reusado tanto por `ConversaoSheet` (logo após o envio) quanto pela linha expandida de `DataGridLotesConversao`.
  - [x] **VERIFY**: `npm run typecheck`/`npm run lint` → OK (corrigido `react-hooks/refs`: mutação de `ref.current` durante o render movida para dentro de `useEffect`). Região `role="status"`/`aria-live="polite"` envolve o painel inteiro, confirmada nos screenshots.
  - [x] **VISUAL**: Bordas, espaçamentos, margens, padding e tipografia do painel conferidos nos estados fila/processando/concluído/falhou, comparando com `PainelProgresso`. Revisão visual completa com Playwright headless contra o dev server real (`npm run dev` + `uv run uvicorn`, banco de teste isolado porta 55432, pessoa owner e member reais criadas via `security.hash_senha`) em 375 px e 1440 px: aba vazia, `ConversaoSheet` vazio/com arquivo selecionado/painel pós-envio (situação `fila`), lote expandido na listagem, estados `concluido` (Badge escura, "Baixar" habilitado, "Baixar todos" habilitado) e `falhou` (Badge clara/destrutiva, mensagem de erro inline, "Reenviar" visível) forçados diretamente no banco de teste para observação, e a aba completa para `member` (sem "Converter documentos", listagem permanece legível — AC-010). Nenhum erro de console em nenhuma captura. Sem overflow horizontal da página no mobile (a tabela usa rolagem interna contida, mesmo padrão de `DataGridBases`); `Sheet` ocupa a largura útil no mobile sem quebrar layout. Dados de revisão removidos do banco de teste ao final (autorizado explicitamente, já que a exclusão em massa aciona o classificador automático).
  - [x] **EVIDENCE**: Arquivo criado: `frontend/src/features/conversao/PainelLoteConversao.tsx`; `npm run build` → sucesso (rota `/workspaces/[id]` gerada); `npm run test:tdd` (suíte completa) → 135 passed; regressão completa do backend após a revisão (`uv run pytest -q`) → 427 passed, mesmas 10 falhas pré-existentes e não relacionadas (SPEC-0022 e marcador em `test_spec_markers.py`).
  - [x] **IMPROVE**: Correção de acessibilidade aplicada (mutação de ref durante o render movida para `useEffect`, evitando possível dessincronia de callback).
<!-- specsfy:evidence {"task":"T042","refs":["US-002","US-003","US-004","FR-004","FR-005","FR-006"],"files":["frontend/src/features/conversao/PainelLoteConversao.tsx"],"commands":[{"run":"npm run build","exit":0},{"run":"npm run test:tdd","exit":0}]} -->

- [x] T043 [DOC] Atualizar INTERFACE.md com ConversaoSheet, DataGridLotesConversao, PainelLoteConversao e a primitive Tabs — Refs: US-001 — Depends: T039, T040, T041, T042
  - [x] **PREP**: Linhas de `UploadBaseSheet`/`PainelProgresso`/`DataGridBases`/`ExcluirWorkspaceDialog` relidas como modelo de formato.
  - [x] **EXECUTE**: Adicionadas cinco linhas à tabela "Blocos criados e reaproveitáveis" (`Tabs`, `ConversaoSheet`, `DataGridLotesConversao`, `PainelLoteConversao`) e atualizada a linha de `/workspaces/[id]` em "Telas e composição" com os novos componentes, a nova chamada de API e os estados de abas no mobile.
  - [x] **VERIFY**: Os quatro arquivos de T039–T042 (`tabs.tsx`, `ConversaoSheet.tsx`, `DataGridLotesConversao.tsx`, `PainelLoteConversao.tsx`) aparecem em `INTERFACE.md`.
  - [x] **VISUAL**: Não aplicável — tarefa de documentação, sem alteração de tela.
  - [x] **EVIDENCE**: Diff aplicado em `INTERFACE.md` (seções "Blocos criados e reaproveitáveis" e "Telas e composição").
  - [x] **IMPROVE**: Nenhuma melhoria necessária.
<!-- specsfy:evidence {"task":"T043","refs":["US-001"],"files":["INTERFACE.md"],"commands":[{"run":"grep -c 'ConversaoSheet\\|DataGridLotesConversao\\|PainelLoteConversao\\|tabs.tsx' INTERFACE.md","exit":0}]} -->

- [ ] T051 [CODE] [US-005] Criar o helper de rótulos de situação em frontend/src/features/conversao/situacao.ts (Na fila, Processando, Convertido, Falhou; lote: Processando, Concluído, Concluído com falhas) — Refs: US-005, FR-004, FR-009, AC-020 — Depends: T048, T049, T050
  - [ ] **PREP**: `$specsfy-specialist-react-ui-components` registrado antes da implementação; `variantePorSituacao` de `PainelLoteConversao` relido para extrair o mapeamento existente.
  - [ ] **EXECUTE**: Criar `situacao.ts` com `rotuloSituacaoDocumento`, `rotuloSituacaoLote` e a variante de `Badge` por situação, e passar `PainelLoteConversao` a usá-los.
  - [ ] **VERIFY**: `cd frontend && npm run typecheck && npm run lint` → OK; `npm run test:tdd -- ListaDocumentosConversao -t ac_020` ainda RED até T052.
  - [ ] **VISUAL**: Conferir no `PainelLoteConversao` que `Badge` mantém bordas, espaçamentos, margens, padding e tipografia, e que rótulos mais longos ("Concluído com falhas") não quebram o layout em 375 px.
  - [ ] **EVIDENCE**: Arquivo criado e comandos acima registrados.
  - [ ] **IMPROVE**: Declarar a melhoria aplicada ao concluir.

- [ ] T052 [CODE] [US-005] Reescrever DataGridLotesConversao.tsx para uma linha por documento, com colunas ID, Arquivo, Formato, Situação, Lote, Criado em, Criado por e Ações, e painel do lote aberto pela linha, em frontend/src/features/conversao/DataGridLotesConversao.tsx — Refs: US-005, US-003, US-004, FR-004, FR-005, FR-006, FR-009, AC-020, AC-021 — Depends: T051, T048, T049, T050
  - [ ] **PREP**: `$specsfy-specialist-react-ui-components` registrado; `DataGridColecoes`, `DataGridBases` e o `DataGridLotesConversao` atual relidos como modelo; `INTERFACE.md` e `DESIGNSYSTEM.MD` lidos.
  - [ ] **EXECUTE**: Achatar `lote.documentos` em linhas ordenadas por `criado_em` decrescente; Situação com `Badge`; ações Baixar e Reenviar independentes (sem abrir o painel); linha inteira abre `PainelLoteConversao` num `Sheet`, por clique e por Enter/Espaço; coluna ID sempre visível.
  - [ ] **VERIFY**: `cd frontend && npm run test:tdd -- ListaDocumentosConversao -t ac_020` e `-t ac_021` → GREEN; `npm run typecheck && npm run lint` → OK.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia da tabela e do painel em 375 px e 1440 px, nos estados carregando, vazio, convertido, falhou, nome de arquivo longo e permissão de leitura, comparando com `DataGridBases` e `DataGridColecoes`.
  - [ ] **EVIDENCE**: Arquivo alterado e comandos acima registrados.
  - [ ] **IMPROVE**: Declarar a melhoria aplicada ao concluir.

- [ ] T053 [CODE] [US-005] [US-001] Incluir o botão "Converter documentos" no estado vazio e ligá-lo ao mesmo gatilho do cabeçalho em frontend/src/features/conversao/DataGridLotesConversao.tsx e frontend/src/app/(autenticado)/workspaces/[id]/page.tsx — Refs: US-005, US-001, FR-009, AC-022 — Depends: T052, T048, T049, T050
  - [ ] **PREP**: Vazio de `DataGridColecoes` relido como modelo do botão e da mensagem para quem não escreve.
  - [ ] **EXECUTE**: Receber `onConverter` e `podeEscrever` no grid; renderizar o botão no vazio apenas com permissão de escrita; a página passa `() => setConverterAberto(true)`.
  - [ ] **VERIFY**: `cd frontend && npm run test:tdd -- ListaDocumentosConversao -t ac_022` → GREEN; `npm run test:tdd` completo e `npm run build` → OK.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do vazio da aba nos dois papéis em 375 px e 1440 px, iguais aos do vazio da aba de coleções.
  - [ ] **EVIDENCE**: Arquivos alterados e comandos acima registrados.
  - [ ] **IMPROVE**: Declarar a melhoria aplicada ao concluir.

- [ ] T054 [DOC] Atualizar INTERFACE.md com a lista por documento, `situacao.ts` e o botão no vazio — Refs: US-005, FR-009 — Depends: T051, T052, T053
  - [ ] **PREP**: Linhas atuais de `DataGridLotesConversao` e `PainelLoteConversao` em `INTERFACE.md` relidas.
  - [ ] **EXECUTE**: Atualizar a linha de `DataGridLotesConversao` (uma linha por documento, colunas, ações, painel), adicionar `situacao.ts` com consumidores e atualizar a linha de `/workspaces/[id]`.
  - [ ] **VERIFY**: `grep -c 'situacao.ts' INTERFACE.md` → pelo menos 1.
  - [ ] **VISUAL**: Não aplicável — tarefa de documentação, sem alteração de tela.
  - [ ] **EVIDENCE**: Diff aplicado em `INTERFACE.md`.
  - [ ] **IMPROVE**: Declarar a melhoria aplicada ao concluir.


#### Fase de documentação

- [x] T044 [DOC] Atualizar .specsfy/STACK.md com pymupdf4llm, python-docx, python-pptx, openpyxl, pytesseract/Pillow, LibreOffice e Tesseract OCR — Refs: FR-003 — Depends: T029
  - [x] **PREP**: Inventário de `.specsfy/STACK.md` e `pyproject.toml` relidos após T021–T029.
  - [x] **EXECUTE**: Já aplicado no checkpoint de contexto da Fase 2 (antes de T030), via `$specsfy-aux-stack` + edição manual complementar (o script `update_stack.mjs` não detecta automaticamente bibliotecas novas de `pyproject.toml` fora das categorias já mapeadas, mesmo padrão já registrado para a stack de frontend): linha "Conversão de documentos para Markdown" com as 6 bibliotecas Python e suas versões, mais nota em "Decisões e observações" sobre os binários de sistema LibreOffice (`soffice`) e Tesseract OCR (`tesseract-ocr`/`tesseract-ocr-por`), confirmados em `/usr/bin/tesseract` e `/usr/bin/soffice` nesta máquina.
  - [x] **VERIFY**: `grep -E 'pymupdf4llm|python-docx|python-pptx|openpyxl|pytesseract|pillow' .specsfy/STACK.md` → todas as 6 dependências de `pyproject.toml` aparecem.
  - [x] **VISUAL**: Não aplicável — tarefa de documentação, sem alteração de tela.
  - [x] **EVIDENCE**: Diff já aplicado em `.specsfy/STACK.md` (linha do inventário + nota de binários de sistema); comando de verificação acima.
  - [x] **IMPROVE**: Nenhuma melhoria aplicável nesta tarefa.
<!-- specsfy:evidence {"task":"T044","refs":["FR-003"],"files":[".specsfy/STACK.md"],"commands":[{"run":"grep -E 'pymupdf4llm|python-docx|python-pptx|openpyxl|pytesseract|pillow' .specsfy/STACK.md","exit":0}]} -->

- [x] T045 [DOC] Atualizar .specsfy/DATABASE.md com lotes_conversao e documentos_conversao como persistência real — Refs: FR-002, FR-007 — Depends: T031
  - [x] **PREP**: Linha de descoberta ("Lote de conversão de documentos", seção "Informações a guardar confirmadas") relida.
  - [x] **EXECUTE**: Complementada a tabela técnica "Estruturas detectadas" (bloco `specsfy:database`) com duas linhas novas — `lotes_conversao` e `documentos_conversao` — campos, tipos, relações e evidência de código; a linha de descoberta em linguagem cotidiana foi preservada intacta (conteúdo humano fora do bloco gerenciado).
  - [x] **VERIFY**: `grep -c 'lotes_conversao\|documentos_conversao' .specsfy/DATABASE.md` → 2 linhas (as duas novas linhas técnicas; a linha de descoberta preexistente usa linguagem cotidiana, "Lote de conversão de documentos", sem os nomes técnicos), ambas apontando para `src/app/models.py` e `alembic/versions/0022_lotes_conversao.py`.
  - [x] **VISUAL**: Não aplicável — tarefa de documentação, sem alteração de tela.
  - [x] **EVIDENCE**: Diff aplicado em `.specsfy/DATABASE.md` (tabela "Estruturas detectadas"); comando de verificação acima.
  - [x] **IMPROVE**: Nenhuma melhoria aplicável nesta tarefa.
<!-- specsfy:evidence {"task":"T045","refs":["FR-002","FR-007"],"files":[".specsfy/DATABASE.md"],"commands":[{"run":"grep -c 'lotes_conversao\\|documentos_conversao' .specsfy/DATABASE.md","exit":0}]} -->

- [x] T046 [DOC] Corrigir a seção Limites de PROJECT.md removendo a contradição sobre ingestão multi-formato — Refs: US-001 — Depends: T035
  - [x] **PREP**: `PROJECT.md` relido: história/motivação (topo, "Fase 1: ingestão multi-formato...") e seção Limites (bullet "processa atualmente arquivos `.md`... sem a ingestão multi-formato prevista").
  - [x] **EXECUTE**: Reescrito o bullet de limite: preserva o fato técnico real (`src/pipeline/loader.py` continua lendo só `.md`) e acrescenta que a SPEC-0023 entrega a ingestão multi-formato como capacidade própria (`src/pipeline/conversion/`, `POST /api/v1/conversoes`), sem criar/alterar Base. Restante do texto humano da seção preservado.
  - [x] **VERIFY**: Releitura da seção Limites confirma ausência de contradição com a visão consolidada do topo ("Fase 1: ingestão multi-formato..." agora reflete capacidade real, não apenas planejada).
  - [x] **VISUAL**: Não aplicável — tarefa de documentação, sem alteração de tela.
  - [x] **EVIDENCE**: Diff aplicado em `PROJECT.md` (seção Limites).
  - [x] **IMPROVE**: Nenhuma melhoria aplicável nesta tarefa.
<!-- specsfy:evidence {"task":"T046","refs":["US-001"],"files":["PROJECT.md"],"commands":[{"run":"grep -c 'ingestão multi-formato' PROJECT.md","exit":0}]} -->

#### Fase final — Qualidade

- [x] T047 [TEST] Executar regressão completa e rastreabilidade em tests/test_router_conversao.py e demais suítes de tests/ — Refs: US-001, US-002, US-003, US-004, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-001, NFR-002, NFR-003 — Depends: T029, T033, T034, T038, T039, T040, T041, T042, T043, T044, T045, T046
  - [x] **PREP**: Suítes identificadas: `uv run pytest` (backend completo), `uv run ruff check .` (lint/estático Python), `npm run typecheck`/`npm run lint`/`npm run test:tdd`/`npm run build` (frontend).
  - [x] **EXECUTE**: Suíte completa executada; matriz de rastreabilidade da seção 12 revisada — todas as linhas atualizadas para GREEN ao longo de T021–T038 já refletem o estado real. Confirmado por grep que `AC-001` a `AC-019` (todos os 19 critérios de aceite da spec) aparecem com marcador `SPECSFY:` em pelo menos um teste executável dentre `test_router_conversao.py`, `test_conversion_structure.py`, `test_conversion_image_ocr.py`, `test_conversion_legacy_office.py`, `test_task_process_conversion_document.py` e `test_task_purgar_documentos_conversao.py`.
  - [x] **VERIFY**: `uv run pytest -q` → 427 passed, 10 failed, 1 skipped. As 10 falhas são integralmente pré-existentes e sem relação com esta entrega: 9 em `test_deploy_build_and_deploy_script.py`/`test_deploy_stack.py` (SPEC-0022, Docker Swarm, spec paralela não implementada nesta sessão) e 1 em `test_spec_markers.py` (marcador de pendência no texto normativo das specs 0022/0023; as ocorrências da 0023 foram reescritas no fechamento, as da 0022 pertencem à outra spec). Todos os testes de SPEC-0023 (router, tasks, conversion, purge) estão GREEN — 0 falha e 0 gap de rastreabilidade entre `AC` e teste dentro do escopo desta entrega. `uv run ruff check .` → All checks passed. Frontend: `npm run typecheck` → OK; `npm run lint` → sem erros; `npm run test:tdd` → 31 arquivos, 135 passed; `npm run build` → sucesso, rota `/workspaces/[id]` gerada.
  - [x] **VISUAL**: Conferência final de bordas, espaçamentos, margens, padding e tipografia repassada nos viewports 375 px e 1440 px e nos estados vazio/carregando/`fila`/`processando`/`concluido`/`falhou`/permissão insuficiente da aba/`Sheet`/painel de conversão (mesma sessão de revisão de T039–T042, com Playwright headless contra o dev server real). Ajuste residual: nenhum além dos dois já corrigidos durante a implementação (remoção do `role="button"` indevido em `DataGridLotesConversao` e da mutação de ref durante o render em `PainelLoteConversao`, ambos registrados em T041/T042).
  - [x] **EVIDENCE**: Contagens finais acima; comandos: `uv run pytest -q`, `uv run ruff check .`, `npm run typecheck`, `npm run lint`, `npm run test:tdd`, `npm run build`.
  - [x] **IMPROVE**: Retrospectiva do processo — (1) `LocalDirectoryStorage.materialize`/`list_files` estavam incompletos para qualquer uso além de Base (só `.md`); corrigidos e alinhados a `S3CompatibleStorage` durante T033/T034, revelando uma dependência oculta que o plano original não previa. (2) O banco de teste isolado estava com `alembic_version` uma revisão atrás do schema real (T030); corrigido com `alembic stamp` antes de aplicar a migration nova, documentado como pré-existente. (3) A suíte de regressão do frontend (`page.test.tsx`) precisou de atualização por causa da 3ª chamada `fetch` introduzida pela nova aba — mudança de tela sempre revisa os testes de tela que ela estende, não só os testes da própria feature nova.

- [ ] T055 [DOC] Revisar PROJECT.md, STACK.md e DATABASE.md após a revisão da lista por documento — Refs: US-005, FR-009 — Depends: T054
  - [ ] **PREP**: Mudança é só de frontend: sem dependência nova, sem tabela, campo ou migration.
  - [ ] **EXECUTE**: Revisar os três arquivos; sem impacto material em `STACK.md` e `DATABASE.md`; registrar a justificativa para `PROJECT.md`.
  - [ ] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`.
  - [ ] **VISUAL**: Não aplicável — tarefa de documentação, sem alteração de tela.
  - [ ] **EVIDENCE**: Justificativa registrada na evidência.
  - [ ] **IMPROVE**: Declarar a melhoria aplicada ao concluir.

- [ ] T056 [TEST] Executar regressão do frontend e rastreabilidade após a revisão da lista por documento em frontend/src/features/conversao/ListaDocumentosConversao.test.tsx e demais suítes — Refs: US-005, FR-009, AC-020, AC-021, AC-022 — Depends: T052, T053, T054, T055
  - [ ] **PREP**: Suítes identificadas: `npm run typecheck`, `npm run lint`, `npm run test:tdd`, `npm run build` e `uv run pytest -q` para garantir ausência de regressão no backend.
  - [ ] **EXECUTE**: Executar as suítes e `check_traceability.mjs`; atualizar a matriz da seção 12 para GREEN em FR-009 e US-005.
  - [ ] **VERIFY**: Todos os comandos com saída 0; falhas pré-existentes e não relacionadas listadas pelo nome, sem mascarar.
  - [ ] **VISUAL**: Conferência final de bordas, espaçamentos, margens, padding e tipografia da aba em 375 px e 1440 px, nos estados vazio, carregando, convertido, falhou e permissão de leitura, comparando com `DESIGNSYSTEM.MD`.
  - [ ] **EVIDENCE**: Contagens finais e comandos registrados nas seções 11–13.
  - [ ] **IMPROVE**: Declarar a melhoria aplicada ao concluir.


### 15. Ordem de execução

- Caminho crítico: T001/T003/T012 (TDD de fundação) → T021 → T022–T027 `[P]` → T028 → T029 → T030 → T031 → T032 → T033 → T035 → T036 → T037 → T038 → T039 → T040/T041/T042 `[P]` → T043 → T047.
- Tarefas paralelas: T001–T020 entre si (nenhum arquivo de produção compartilhado); T022–T026 entre si (converters independentes, mesma dependência comum T021); T040/T041/T042 entre si (componentes React independentes, mesma dependência comum T039); T044/T045/T046 entre si (arquivos de documentação distintos).
- Revisão de 2026-10-14 (US-005, FR-009): T048 → T049 → T050 (RED) → T051 → T052 → T053 → T054 → T055 → T056. T051 e T052 mexem em arquivos distintos mas T052 depende do helper; sem `[P]`.
- Estratégia de MVP: US-001 + US-002 + US-003 (T001–T037, T039–T041, T043–T046 aplicáveis) formam o menor conjunto entregável e demonstrável — enviar, acompanhar e baixar. US-004 (T002, T006, T016, T038, T042 na parte de reenvio) agrega valor incremental sem bloquear a entrega das três primeiras.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0008 (concluída), fronteira `src/pipeline/`/`src/app/`: a nova extração deve respeitar a fachada de casos de uso já estabelecida (PR-001).
- Procrastinate e `Storage` já configurados (SPEC-0012): reaproveitados sem alteração de contrato (PR-002, PR-003).
- Novas dependências de sistema a incluir na imagem/ambiente: Tesseract OCR (binário `tesseract-ocr` + pacote de idioma `tesseract-ocr-por`) e LibreOffice headless (binário `soffice`, para normalizar `.doc`/`.ppt`/`.xls`) — impacto direto no build da imagem Docker do roadmap de deploy já aberto em M03 (BACKLOG-0028 a 0032); registrar essa dependência quando aquele backlog for especificado.

#### Riscos

- OCR de imagem é inerentemente mais lento e menos preciso que extração de texto nativo → mitigação: melhor esforço, sem bloqueio por baixa confiança (decisão já confirmada no backlog).
- LibreOffice headless aumenta significativamente o tamanho e o tempo de build da imagem Docker, e pode ter custo de memória/concorrência sob carga → mitigação: processar um documento por vez via fila (já é o desenho, um job por documento) e aplicar timeout por conversão na tarefa.
- `PROJECT.md` ainda declara, na seção de limites, que a ingestão multi-formato está "prevista para o projeto-mãe" e fora de escopo — texto desatualizado frente à consolidação já registrada no topo do mesmo arquivo. Mitigação: corrigir esse texto como tarefa de documentação da própria entrega (seção 14, a detalhar por `$specsfy-05-tasks`), não como requisito funcional novo.
- Biblioteca de extração pode divergir de biblioteca para biblioteca na fidelidade de preservação de estrutura (ex.: tabelas complexas em PDF) → mitigação: AC-003 e AC-012 cobrem casos representativos; casos residuais de baixa fidelidade ficam documentados como limitação conhecida, não bloqueiam a entrega.

#### Suposições

- Limite de 40 MB por arquivo de conversão (acima dos 5 MB de Base), com 50 MB total e 50 arquivos mantidos — valor sugerido pelo backlog como exemplo, default reversível.
- Idioma padrão do OCR é português (`por`), melhor esforço, sem bloqueio por baixa confiança.
- Reenvio de um documento reprocessa o original já armazenado (sem exigir novo upload), desde que dentro da janela de retenção de 7 dias; fora dela, exige um novo envio via `POST /api/v1/conversoes`.
- A situação do `LoteConversao` é um campo persistido, recalculado a cada atualização de um `DocumentoConversao` filho, e não computada em tempo real a cada leitura.
- Documentos legados (`.doc`, `.ppt`, `.xls`) são normalizados para o formato OOXML equivalente via LibreOffice headless antes da extração estruturada, mantendo o mesmo conversor OOXML para ambas as variantes de um mesmo tipo.

### 17. Decisões

- **DEC-001**: Extração custom por formato (`python-docx`, `python-pptx`, `openpyxl`) em vez de uma biblioteca "tudo em um" — dá controle direto sobre a fidelidade de cabeçalhos/tabelas exigida pelo backlog e evita depender do comportamento interno pouco previsível de uma única biblioteca genérica para os cinco formatos.
- **DEC-002**: PDF usa `pymupdf4llm` especificamente (diferente do custom dos demais formatos) porque PDF não tem semântica estrutural explícita — a detecção de título/tabela depende de heurística (tamanho de fonte, posição), que essa biblioteca já implementa; reescrever essa heurística do zero não traria benefício sobre reaproveitá-la.
- **DEC-003**: `Storage` existente é reaproveitado chaveando por `documento_id` em vez de criar um novo mecanismo de armazenamento — seu contrato (`save`/`delete_base`/`materialize`) já é agnóstico ao significado do id da pasta.
- **DEC-004**: Processamento assíncrono é um job por documento (não um job por lote) — isola a falha de um documento sem exigir lógica extra de "continuar após erro" dentro de um job único, e permite reenviar um documento sem reprocessar os demais.
- **DEC-005**: A tela reaproveita o mesmo painel (`Sheet`) para envio e acompanhamento, sem rota própria de detalhe do lote — decisão já confirmada no backlog ("no mesmo painel"); evita criar uma rota nova só para leitura de um recurso sem ações próprias de navegação.
- **DEC-006**: Formatos legados (`.doc`, `.ppt`, `.xls`) são normalizados via LibreOffice headless antes da extração, em vez de excluí-los do escopo ou usar bibliotecas dedicadas por formato legado — mantém fiel a decisão já confirmada com a pessoa no backlog ("formatos aceitos são PDF, PPT, DOC/DOCX, XLS/XLSX..."), ao custo de uma nova dependência de sistema pesada (risco registrado na seção 16).
- **DEC-007**: A situação do lote é recalculada e persistida a cada atualização de um documento filho, em vez de computada por agregação a cada leitura — evita uma consulta agregada em toda consulta de listagem/polling, ao custo de uma escrita extra por transição de documento (já ocorre dentro da mesma transação).
- **DEC-008**: A lista da aba passa a ter uma linha por documento, achatando `lote.documentos` no frontend, em vez de uma linha por lote com a situação do lote — a situação por documento é o que a pessoa procura ao abrir a aba. Opção escolhida pela pessoa em 2026-10-14 entre resumo no lote, linha por documento e status só na aba de coleções. Sem mudança de API: `GET /api/v1/conversoes` já devolve os documentos de cada lote. O lote continua visível como coluna e como painel aberto pela linha, para preservar o download do pacote e o contexto de quem enviou e quando. Impacta FR-004, FR-009, US-002, US-005. Efeito colateral aceito: um lote com muitos arquivos alonga a lista; filtro e paginação ficam como evolução futura. Rótulos em português substituem os valores técnicos crus (`concluido`, `concluido_com_falhas`) na interface.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/STACK.md` atualizado com as novas dependências estruturais (`pymupdf4llm`, `python-docx`, `python-pptx`, `openpyxl`, `pytesseract`/`Pillow`, LibreOffice headless, Tesseract OCR) via `$specsfy-aux-stack`.
- [x] `.specsfy/DATABASE.md` atualizado com `lotes_conversao`/`documentos_conversao` como persistência real (hoje só a descoberta de dados está lá) via `$specsfy-aux-database`.
