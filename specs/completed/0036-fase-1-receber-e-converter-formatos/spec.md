# Especificação integrada: Fase 1: receber e converter HTML, URL e planilhas com escolha de abas

Origem: `specs/backlog/0039-fase-1-receber-e-converter-formatos.md` (BACKLOG-0039).

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0036 |
| Slug | 0036-fase-1-receber-e-converter-formatos |
| Status | Complete |
| Effort | 6 |
| Effort updated at | 2026-10-15 |
| Effort rationale | Cinco histórias que cruzam backend, worker, migração, segurança de rede, IA e interface; sem tecnologia nova de alto risco, mas com SSRF e contrato multimodal retrocompatível verificado. |
| ClickUp Task | |
| Milestones | M04 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-15 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O sistema converte PDF, Word, PowerPoint, Excel e imagem em Markdown (SPEC-0023 e SPEC-0033), mas não aceita **página da web (URL)** nem **arquivo `.html`**, que são entradas comuns de quem prepara a base de conhecimento. O Excel é convertido inteiro, sem a pessoa poder descartar abas que não servem. Os tetos de tamanho são fixos no código (40 MB por arquivo, 50 MB por envio) e valem para o envio inteiro. Documento com leitura ruim só recebe o selo "revisar" nos casos do OCR de PDF, e não existe forma de pedir uma leitura melhor por IA sem enviar tudo a um serviço externo.

#### Resultado desejado

A pessoa da consultoria cola um endereço público ou envia um `.html` salvo e recebe um `.md` rastreável à origem; escolhe as abas do Excel antes de converter; vê quando um arquivo ou lote passa do limite sem perder os demais; e só aciona a IA, documento a documento, quando quiser. Tudo na tela de Conversão que já existe, com bibliotecas e OCR antes de qualquer LLM.

#### Métricas de sucesso

- 100% dos endereços da rede interna ou da própria máquina testados (direto, por redirecionamento e por DNS) são recusados, sem nenhuma conexão de saída.
- 0 chamadas ao provedor de IA sem o clique em Reprocessar com IA, verificado por teste.
- Conversão de URL e de `.html` com texto no HTML conclui sem LLM; a API responde ao envio de URL sem esperar a busca.
- Suíte da SPEC-0023 e da SPEC-0033 passa, com atualização exclusiva do teste de rejeição integral substituído por FR-006.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: o que a SPEC-0023 e a SPEC-0033 já entregam → PDF, PPT/PPTX, DOC/DOCX, XLS/XLSX e imagem já convertem de forma assíncrona (`src/app/routers/conversao.py`, `src/pipeline/conversion/`); esta spec cobre só HTML/URL, escolha de abas, tetos configuráveis, critério "revisar" geral e reprocessar com IA.
- **R-002**: onde ficam os limites hoje → constantes `MAX_ARQUIVOS=50`, `MAX_BYTES_POR_ARQUIVO=40 MB`, `MAX_BYTES_TOTAL=50 MB` em `src/app/routers/conversao.py`; o envio inteiro é recusado quando passa de um teto. O backlog citava 50 MB e 500 MB como referência de partida, o que diverge do código (ver DEC-005).
- **R-003**: acesso a LLM → `.specsfy/RULES.md` exige `ChatModelAdapter` via `ProviderFactory.create_chat_model` e a fachada `src.pipeline.service`. Verificado em `src/pipeline/providers/contracts.py:134`: `ChatMessage.conteudo` é `str`, ou seja, o contrato atual **não aceita imagem** (ver DEC-007).

#### Fontes e contexto consultados

- `specs/backlog/0039-fase-1-receber-e-converter-formatos.md` (decisões das Perguntas 2 a 8, 2026-10-13) e `specs/completed/0023-*`, `specs/completed/0033-*`.
- `src/app/routers/conversao.py`, `src/app/tasks.py` (`process_conversion_document_task`), `src/app/models.py` (`LoteConversao`, `DocumentoConversao`), `src/pipeline/conversion/` (factory, contratos, conversores, `ConversaoConfig`).
- `INTERFACE.md` (componentes `frontend/src/features/conversao/`), `.specsfy/RULES.md`, `pyproject.toml`.

#### Documentação consultada

- Nenhuma documentação externa consultada nesta fase; a biblioteca de extração de HTML é escolhida na implementação conforme DEC-003.

#### Artefatos de pesquisa armazenados

- Evidências locais em `specs/completed/0036-fase-1-receber-e-converter-formatos/research/`: referências primárias, resultados de testes/build, capturas Chromium e auditoria histórica em HEAD; sem credenciais ou dados de clientes.

#### Dúvidas respondidas

- **Q**: Como a pessoa informa a página? → **A**: cola um endereço ou envia `.html` salvo (backlog, Pergunta 2, opção 3).
- **Q**: Páginas que dependem de scripts? → **A**: só texto já presente no HTML; página vazia avisa e sugere salvar o `.html` (Pergunta 3, opção 3).
- **Q**: Quais endereços são permitidos? → **A**: qualquer `http`/`https` público; rede interna e da própria máquina bloqueadas (Pergunta 4, opção 1).
- **Q**: O que acontece acima do limite? → **A**: só o documento excedente é recusado (Pergunta 5, opção 2).
- **Q**: Como escolher abas do Excel? → **A**: lista com todas marcadas; só as marcadas viram `.md` (Pergunta 6, opção 1).
- **Q**: Quando usar IA? → **A**: nunca automaticamente; botão por documento (Pergunta 7, opção 3).

#### Dúvidas abertas

- Nenhuma bloqueante. Os pontos antes pendentes foram fechados por evidência do código ou por default reversível, registrados em DEC-003 a DEC-007 e em Suposições, e podem ser revistos pela pessoa responsável sem reabrir os atos.

### 3. Escopo e atores

#### Incluído

- Conversão de **URL pública** `http`/`https` e de **arquivo `.html`** em um `.md` por página.
- Bloqueio de endereços internos e da própria máquina, inclusive por redirecionamento e por DNS.
- Aviso "não consegui extrair o conteúdo" para página sem texto no HTML.
- **Escolha de abas** de planilhas `.xlsx` e `.xls` antes de converter.
- **Tetos** por arquivo e por lote configuráveis, com recusa só do excedente.
- Critério de "baixa qualidade" e selo "revisar" no relatório do lote para todos os formatos.
- **Reprocessar com IA**, documento a documento, por pedido explícito.
- Ajustes na tela de Conversão existente (Workspace) e na API `/api/v1/conversoes`.

#### Fora de escopo

- Navegador automático e execução de scripts da página (evolução futura).
- Crawling de links internos; só a URL explicitamente enviada.
- Acesso à API do Google (Google chega exportado como DOCX, PPTX ou XLSX).
- Detecção e OCR de PDF só de imagem (BACKLOG-0045 / SPEC-0033), reagrupamento de sequências (0040), filtro de domínio e limpeza (0041), contradições (0042, 0043).
- Download e armazenamento permanentes do conteúdo; a retenção de 7 dias da SPEC-0023 continua.

#### Atores

- **Pessoa da consultoria (owner ou admin)**: papéis de escrita (`PAPEIS_DE_ESCRITA` em `src/app/auth.py`); envia documentos e URLs, escolhe abas e confirma reprocessamento com IA.
- **Pessoa com papel `member`**: somente leitura; consulta e baixa, não envia nem reprocessa.
- **Worker**: busca a URL, converte e grava o `.md`; é o único componente que faz requisição de saída.

### 4. Princípios e restrições do projeto

- **PR-001**: a lógica fica em `src/pipeline/conversion/` por Factory/Adapter e `src/app` depende só da fachada `src.pipeline.service` (`.specsfy/RULES.md`).
- **PR-002**: respostas de LLM passam por `ChatModelAdapter` resolvido por `ProviderFactory.create_chat_model`, sem importar SDK direto em `src/app`.
- **PR-003**: bibliotecas e OCR antes de LLM; LLM somente por pedido da pessoa.
- **PR-004**: nenhum teste usa o banco de desenvolvimento nem comandos que apaguem banco ou schema; migrações são aditivas.
- **PR-005**: interface em React com componentes shadcn/ui; reutilizar `frontend/src/features/conversao/` e registrar mudanças em `INTERFACE.md`.
- **PR-006**: branch `spec/0036-fase-1-receber-e-converter-formatos`, uma spec por branch.

### 5. Histórias de usuário

#### US-001 — Converter uma página pela URL (P1)

Como pessoa da consultoria, quero colar o endereço de uma página pública, para receber o conteúdo dela em Markdown sem copiar e colar.

**Por que P1**: Documentos da web são entrada frequente e hoje não entram no pipeline.
**Teste independente**: Colar uma URL pública com texto no HTML e baixar o `.md` com a origem registrada.
**Requisitos**: FR-001, FR-002, FR-003, FR-009

#### US-002 — Converter um arquivo .html salvo (P2)

Como pessoa da consultoria, quero enviar um `.html` salvo pelo navegador, para converter páginas que dependem de scripts ou exigem login.

**Por que P2**: É o caminho de contingência quando a URL não entrega texto.
**Teste independente**: Enviar um `.html` salvo e baixar o `.md`.
**Requisitos**: FR-003, FR-004, FR-009

#### US-003 — Escolher as abas de uma planilha (P1)

Como pessoa da consultoria, quero marcar quais abas do Excel viram Markdown, para não indexar abas de apoio ou sem valor.

**Por que P1**: Planilhas reais misturam dados úteis e abas auxiliares.
**Teste independente**: Enviar uma planilha com três abas, desmarcar uma e confirmar.
**Requisitos**: FR-005

#### US-004 — Ver e respeitar os limites de tamanho (P2)

Como pessoa da consultoria, quero que apenas o arquivo grande demais seja recusado, para não perder o restante do envio.

**Por que P2**: Um arquivo fora do limite hoje derruba o envio inteiro.
**Teste independente**: Enviar dois arquivos, um acima do teto, e converter o outro.
**Requisitos**: FR-006

#### US-005 — Revisar e reprocessar com IA sob pedido (P2)

Como pessoa da consultoria, quero ver quais documentos têm leitura ruim e, só se eu quiser, reprocessá-los com IA, para melhorar a qualidade sem enviar nada a serviço externo por conta própria.

**Por que P2**: A empresa cliente pode ter dados sensíveis; a IA só entra com decisão explícita.
**Teste independente**: Ver o selo "revisar" e acionar a IA em um único documento.
**Requisitos**: FR-007, FR-008

### 6. Cenários BDD de aceite

#### AC-001 — Endereço público com texto no HTML gera um Markdown rastreável

**Cobre**: US-001, FR-001, FR-009, NFR-003

```gherkin
@US-001 @FR-001 @FR-009 @NFR-003 @AC-001
Feature: Endereço público com texto no HTML gera um Markdown rastreável

  Scenario: Endereço público com texto no HTML gera um Markdown rastreável
    Given uma pessoa com papel de escrita na tela de Conversão de um Workspace e uma página pública https com o texto no HTML
    When ela cola o endereço e confirma
    Then o envio é aceito sem esperar o download, o documento passa por fila e processando, e o `.md` final traz título e texto da página e a URL de origem registrada, sem uso de LLM
```

#### AC-002 — Uma URL gera um documento e links internos não são seguidos

**Cobre**: US-001, FR-001

```gherkin
@US-001 @FR-001 @AC-002
Feature: Uma URL gera um documento e links internos não são seguidos

  Scenario: Uma URL gera um documento e links internos não são seguidos
    Given uma página pública cujo HTML contém links para outras páginas do mesmo site
    When a página é convertida
    Then existe exatamente um documento e um `.md` para a URL enviada, e nenhuma requisição é feita aos endereços dos links
```

#### AC-003 — Falha de rede ou resposta de erro marca só o documento como falhou

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-003
Feature: Falha de rede ou resposta de erro marca só o documento como falhou

  Scenario: Falha de rede ou resposta de erro marca só o documento como falhou
    Given um endereço público que responde 404, 500 ou excede o tempo limite
    When o documento é processado
    Then o documento fica `falhou` com mensagem segura sem detalhe interno, o botão de reenviar fica disponível e os demais documentos do lote seguem
```

#### AC-004 — Endereço da rede interna ou da própria máquina é recusado

**Cobre**: US-001, FR-002, NFR-001

```gherkin
@US-001 @FR-002 @NFR-001 @AC-004
Feature: Endereço da rede interna ou da própria máquina é recusado

  Scenario: Endereço da rede interna ou da própria máquina é recusado
    Given endereços como `http://localhost`, `http://127.0.0.1`, `http://10.0.0.5`, `http://192.168.0.1`, `http://169.254.169.254` e `http://[::1]`
    When a pessoa tenta enviá-los
    Then cada um é recusado com mensagem clara, nenhum documento é criado e nenhuma conexão de saída é aberta
```

#### AC-005 — Redirecionamento para endereço interno é bloqueado

**Cobre**: US-001, FR-002, NFR-001

```gherkin
@US-001 @FR-002 @NFR-001 @AC-005
Feature: Redirecionamento para endereço interno é bloqueado

  Scenario: Redirecionamento para endereço interno é bloqueado
    Given uma página pública que responde 302 para um endereço da rede interna
    When o documento é processado
    Then o redirecionamento não é seguido, o documento fica `falhou` com mensagem segura e nenhuma requisição chega ao destino interno
```

#### AC-006 — Nome público que resolve para endereço interno é bloqueado

**Cobre**: FR-002, NFR-001, US-001

```gherkin
@FR-002 @NFR-001 @US-001 @AC-006
Feature: Nome público que resolve para endereço interno é bloqueado

  Scenario: Nome público que resolve para endereço interno é bloqueado
    Given um nome de domínio cujo DNS resolve para um endereço da rede interna
    When o endereço é validado antes da conexão
    Then a conexão é recusada porque a validação vale para o endereço resolvido, não só para o texto digitado
```

#### AC-007 — Página sem texto no HTML orienta salvar o .html

**Cobre**: US-001, FR-003

```gherkin
@US-001 @FR-003 @AC-007
Feature: Página sem texto no HTML orienta salvar o .html

  Scenario: Página sem texto no HTML orienta salvar o .html
    Given uma página pública cujo conteúdo só aparece depois de scripts, com o HTML sem texto útil
    When o documento é processado
    Then o documento fica `falhou` com a mensagem "não consegui extrair o conteúdo" e a sugestão de salvar o `.html` pelo navegador e enviá-lo, sem abrir navegador automático
```

#### AC-008 — Resposta que não é página HTML é recusada

**Cobre**: US-001, FR-003, FR-001

```gherkin
@US-001 @FR-003 @FR-001 @AC-008
Feature: Resposta que não é página HTML é recusada

  Scenario: Resposta que não é página HTML é recusada
    Given um endereço público que responde com tipo diferente de HTML, como um PDF ou uma imagem
    When o documento é processado
    Then o documento fica `falhou` com mensagem clara indicando que o endereço não é uma página, sem criar `.md` vazio
```

#### AC-009 — Resposta acima do teto recusa só aquele documento

**Cobre**: US-001, US-004, FR-006, NFR-001

```gherkin
@US-001 @US-004 @FR-006 @NFR-001 @AC-009
Feature: Resposta acima do teto recusa só aquele documento

  Scenario: Resposta acima do teto recusa só aquele documento
    Given um lote com duas URLs, uma delas com resposta acima do teto de tamanho configurado
    When o lote é processado
    Then só a URL excedente fica `falhou` com mensagem de tamanho e a outra conclui normalmente
```

#### AC-010 — Arquivo .html salvo gera um Markdown

**Cobre**: US-002, FR-004, FR-009

```gherkin
@US-002 @FR-004 @FR-009 @AC-010
Feature: Arquivo .html salvo gera um Markdown

  Scenario: Arquivo .html salvo gera um Markdown
    Given um arquivo `.html` salvo pelo navegador com o texto no HTML
    When a pessoa o envia na tela de Conversão
    Then o documento conclui com um `.md` do texto, com scripts e estilos descartados, sem uso de LLM
```

#### AC-011 — Arquivo .html sem texto útil orienta a pessoa

**Cobre**: US-002, FR-003, FR-004

```gherkin
@US-002 @FR-003 @FR-004 @AC-011
Feature: Arquivo .html sem texto útil orienta a pessoa

  Scenario: Arquivo .html sem texto útil orienta a pessoa
    Given um arquivo `.html` salvo cujo corpo não tem texto útil
    When ele é processado
    Then o documento fica `falhou` com a mensagem "não consegui extrair o conteúdo" e a orientação de salvar a página completa pelo navegador
```

#### AC-012 — Scripts do HTML nunca são executados

**Cobre**: US-002, FR-004, NFR-001

```gherkin
@US-002 @FR-004 @NFR-001 @AC-012
Feature: Scripts do HTML nunca são executados

  Scenario: Scripts do HTML nunca são executados
    Given um `.html` com `<script>` que tentaria abrir uma conexão ou ler arquivos
    When ele é convertido
    Then nenhum script é executado, nenhuma conexão de saída é aberta e o `.md` não contém o código do script
```

#### AC-013 — Planilha com várias abas mostra todas marcadas antes de converter

**Cobre**: US-003, FR-005, NFR-004, NFR-003

```gherkin
@US-003 @FR-005 @NFR-004 @NFR-003 @AC-013
Feature: Planilha com várias abas mostra todas marcadas antes de converter

  Scenario: Planilha com várias abas mostra todas marcadas antes de converter
    Given um arquivo `.xlsx` ou `.xls` com três abas
    When a pessoa o envia
    Then o documento fica `aguardando_abas`, a tela mostra as três abas com todas marcadas e nada é convertido até a confirmação
```

#### AC-014 — Só as abas marcadas viram Markdown

**Cobre**: US-003, FR-005

```gherkin
@US-003 @FR-005 @AC-014
Feature: Só as abas marcadas viram Markdown

  Scenario: Só as abas marcadas viram Markdown
    Given as três abas listadas e a pessoa desmarca uma
    When ela confirma
    Then o `.md` contém apenas as duas abas marcadas, cada uma em sua seção, e a aba desmarcada não aparece
```

#### AC-015 — Confirmar sem nenhuma aba marcada não é possível

**Cobre**: US-003, FR-005, NFR-004

```gherkin
@US-003 @FR-005 @NFR-004 @AC-015
Feature: Confirmar sem nenhuma aba marcada não é possível

  Scenario: Confirmar sem nenhuma aba marcada não é possível
    Given a pessoa desmarca todas as abas
    When ela tenta confirmar
    Then o botão Confirmar fica desabilitado ou a API responde 400, com mensagem anunciada para tecnologia assistiva, e o documento segue `aguardando_abas`
```

#### AC-016 — Arquivo acima do teto por arquivo é recusado e os demais seguem

**Cobre**: US-004, FR-006

```gherkin
@US-004 @FR-006 @AC-016
Feature: Arquivo acima do teto por arquivo é recusado e os demais seguem

  Scenario: Arquivo acima do teto por arquivo é recusado e os demais seguem
    Given um envio com dois arquivos, um acima do teto por arquivo
    When a pessoa envia
    Then só o arquivo excedente é recusado, com nome e limite na mensagem, e o outro é aceito e convertido
```

#### AC-017 — Envio acima do teto do lote recusa o excedente

**Cobre**: US-004, FR-006

```gherkin
@US-004 @FR-006 @AC-017
Feature: Envio acima do teto do lote recusa o excedente

  Scenario: Envio acima do teto do lote recusa o excedente
    Given arquivos cuja soma passa do teto do lote
    When a pessoa envia
    Then os arquivos que cabem no teto são aceitos na ordem do envio, os que ultrapassam são recusados com mensagem clara e nenhum documento aceito é perdido
```

#### AC-018 — Os tetos vêm de configuração

**Cobre**: US-004, FR-006, NFR-005

```gherkin
@US-004 @FR-006 @NFR-005 @AC-018
Feature: Os tetos vêm de configuração

  Scenario: Os tetos vêm de configuração
    Given tetos por arquivo e por lote alterados na configuração `conversao`
    When a pessoa envia arquivos perto dos novos valores
    Then a recusa e a aceitação seguem os valores configurados, e a interface exibe os mesmos valores da API
```

#### AC-019 — Leitura de baixa qualidade marca o documento como revisar

**Cobre**: US-005, FR-007

```gherkin
@US-005 @FR-007 @AC-019
Feature: Leitura de baixa qualidade marca o documento como revisar

  Scenario: Leitura de baixa qualidade marca o documento como revisar
    Given um documento convertido por biblioteca ou OCR cujo resultado cumpre o critério de baixa qualidade
    When o lote termina
    Then o documento aparece com o selo "revisar" e o motivo no relatório do lote, e o `.md` continua baixável
```

#### AC-020 — Documento de boa qualidade não recebe o selo

**Cobre**: US-005, FR-007, NFR-005

```gherkin
@US-005 @FR-007 @NFR-005 @AC-020
Feature: Documento de boa qualidade não recebe o selo

  Scenario: Documento de boa qualidade não recebe o selo
    Given um documento convertido sem nenhum aviso
    When o lote termina
    Then ele aparece sem o selo "revisar" e sem botão de reprocessar com IA em destaque
```

#### AC-021 — Reprocessar com IA acontece só por pedido, documento a documento

**Cobre**: US-005, FR-008, NFR-002

```gherkin
@US-005 @FR-008 @NFR-002 @AC-021
Feature: Reprocessar com IA acontece só por pedido, documento a documento

  Scenario: Reprocessar com IA acontece só por pedido, documento a documento
    Given um documento marcado "revisar" e uma pessoa com papel de escrita
    When ela confirma o aviso de envio e aciona Reprocessar com IA
    Then só aquele documento é enviado ao provedor de IA configurado, o `.md` é substituído e o documento registra que foi reprocessado com IA
```

#### AC-022 — Sem o pedido nada é enviado a serviço externo

**Cobre**: US-005, FR-008, FR-009, NFR-002

```gherkin
@US-005 @FR-008 @FR-009 @NFR-002 @AC-022
Feature: Sem o pedido nada é enviado a serviço externo

  Scenario: Sem o pedido nada é enviado a serviço externo
    Given um lote com documentos marcados "revisar"
    When o processamento termina sem ninguém acionar o reprocessamento
    Then nenhuma chamada ao provedor de IA é feita e o conteúdo dos documentos não sai do sistema
```

#### AC-023 — Falha da IA preserva o Markdown anterior

**Cobre**: US-005, FR-008

```gherkin
@US-005 @FR-008 @AC-023
Feature: Falha da IA preserva o Markdown anterior

  Scenario: Falha da IA preserva o Markdown anterior
    Given um reprocessamento com IA cujo provedor falha ou excede o tempo
    When o processamento termina
    Then o `.md` anterior é mantido, o documento continua "revisar", a mensagem é segura e a pessoa pode tentar de novo
```

#### AC-024 — Papel somente leitura não reprocessa com IA

**Cobre**: US-005, FR-008, NFR-002

```gherkin
@US-005 @FR-008 @NFR-002 @AC-024
Feature: Papel somente leitura não reprocessa com IA

  Scenario: Papel somente leitura não reprocessa com IA
    Given uma pessoa com papel `member`
    When ela tenta reprocessar com IA ou enviar uma URL
    Then a API responde 403 e a interface não mostra a ação
```

#### AC-025 — Formatos já suportados continuam convertendo

**Cobre**: FR-009, FR-007, NFR-005

```gherkin
@FR-009 @FR-007 @NFR-005 @AC-025
Feature: Formatos já suportados continuam convertendo

  Scenario: Formatos já suportados continuam convertendo
    Given documentos PDF, DOCX, PPTX, imagem e XLSX de uma só aba, como na SPEC-0023 e na SPEC-0033
    When são enviados após esta entrega
    Then a conversão e o selo "revisar" se comportam como antes, e a suíte da SPEC-0023 e da SPEC-0033 passa; somente o teste de rejeição integral do lote é atualizado conforme FR-006
```

#### AC-026 — Logs e mensagens não expõem credenciais da URL

**Cobre**: NFR-002, NFR-001, US-001

```gherkin
@NFR-002 @NFR-001 @US-001 @AC-026
Feature: Logs e mensagens não expõem credenciais da URL

  Scenario: Logs e mensagens não expõem credenciais da URL
    Given uma URL com usuário, senha ou token na query string e uma falha de busca
    When a falha é registrada
    Then o log e a mensagem à pessoa não contêm usuário, senha nem a query string da URL
```

#### AC-027 — Migração preserva lotes e documentos existentes

**Cobre**: NFR-005, FR-009, US-003

```gherkin
@NFR-005 @FR-009 @US-003 @AC-027
Feature: Migração preserva lotes e documentos existentes

  Scenario: Migração preserva lotes e documentos existentes
    Given lotes e documentos criados antes desta entrega
    When a migração é aplicada
    Then todos continuam listáveis e baixáveis, com as novas colunas vazias, sem reprocessamento
```

#### AC-028 — O envio de URL responde sem esperar a busca

**Cobre**: NFR-003, US-001, FR-001

```gherkin
@NFR-003 @US-001 @FR-001 @AC-028
Feature: O envio de URL responde sem esperar a busca

  Scenario: O envio de URL responde sem esperar a busca
    Given um endereço cuja resposta demora
    When a pessoa o envia
    Then a API responde 201 com o documento em `fila` e a busca acontece no worker, sem bloquear outras requisições
```

#### AC-029 — Campo de endereço é operável por teclado e anuncia erros

**Cobre**: NFR-004, US-001, FR-002

```gherkin
@NFR-004 @US-001 @FR-002 @AC-029
Feature: Campo de endereço é operável por teclado e anuncia erros

  Scenario: Campo de endereço é operável por teclado e anuncia erros
    Given a pessoa navega só pelo teclado na aba Endereço da tela de Conversão
    When ela digita um endereço interno e confirma
    Then o foco chega ao campo e ao botão pela ordem lógica, e o erro é anunciado em região `role=alert` ligada ao campo
```


### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve aceitar uma URL pública `http` ou `https` na tela de Conversão, buscá-la no worker e gerar exatamente um `.md` por URL, com título, texto e a URL de origem registrada, sem seguir links internos.
- **FR-002**: O sistema deve recusar endereços da rede interna e da própria máquina (loopback, privados, link-local, metadados de nuvem, IPv6 equivalente, `localhost`), validando o endereço resolvido antes da conexão e a cada redirecionamento, e conectando ao mesmo endereço validado para que uma segunda resolução de DNS não o troque.
- **FR-003**: O sistema deve marcar como `falhou` com a mensagem "não consegui extrair o conteúdo" e a sugestão de salvar o `.html` pelo navegador e enviá-lo quando a página ou o arquivo `.html` não tiver texto útil, ou quando a resposta não for uma página HTML.
- **FR-004**: O sistema deve converter um arquivo `.html` enviado em um `.md`, descartando scripts, estilos e conteúdo não textual, sem executar nada do arquivo.
- **FR-005**: O sistema deve, ao receber `.xlsx` ou `.xls` com duas ou mais abas, listar as abas com todas marcadas, aguardar a confirmação da pessoa e converter só as abas marcadas, exigindo ao menos uma.
- **FR-006**: O sistema deve aplicar tetos configuráveis por arquivo ou página e por lote, recusando só o documento excedente com mensagem clara e seguindo com os demais.
- **FR-007**: O sistema deve marcar "revisar" no relatório do lote o documento de qualquer formato cuja leitura cumprir o critério de baixa qualidade, com o motivo, sem usar IA.
- **FR-008**: O sistema deve reprocessar com IA um único documento quando uma pessoa com papel de escrita pedir, depois de confirmar o aviso de envio ao provedor, substituindo o `.md` apenas em caso de sucesso.
- **FR-009**: O sistema deve escolher a extração pelo conteúdo e pela biblioteca ou OCR antes de LLM, e manter inalterado o comportamento dos formatos já suportados.

#### Não funcionais

- **NFR-001**: Segurança da busca: tempo limite, tamanho máximo da resposta e número máximo de redirecionamentos configuráveis; nenhum script executado; cabeçalhos e corpo tratados como não confiáveis. **Verificação**: testes de unidade e integração com servidor falso e DNS simulado (AC-003, AC-004, AC-005, AC-006, AC-009, AC-012, AC-026).
- **NFR-002**: Privacidade: nenhum conteúdo de documento sai para provedor de IA sem o pedido explícito, e logs e mensagens não carregam credenciais nem query string de URL. **Verificação**: teste com provedor falso que falha se chamado (AC-021, AC-022, AC-024, AC-026).
- **NFR-003**: Desempenho: o envio de URL e a seleção de abas respondem sem esperar busca ou conversão, que ocorrem no worker. **Verificação**: teste de integração com busca lenta simulada (AC-001, AC-028).
- **NFR-004**: Acessibilidade: os controles novos (aba Endereço, lista de abas, confirmações) operam por teclado, têm rótulo e anunciam erros em `role=alert`. **Verificação**: testes de componente com Testing Library e revisão visual (AC-013, AC-015, AC-029).
- **NFR-005**: Compatibilidade: migração aditiva, API retrocompatível e suíte da SPEC-0023 e SPEC-0033 preservada, exceto o teste de rejeição integral do lote substituído pela aceitação parcial de FR-006. **Verificação**: execução da suíte existente e teste de migração (AC-018, AC-020, AC-025, AC-027).

#### Erros e casos-limite

- Planilha com uma só aba → segue direto para a fila, sem tela de seleção, como na SPEC-0023.
- Endereço malformado, sem esquema, com credenciais embutidas ou porta fora do padrão → recusado com mensagem clara.
- Nome que resolve para vários endereços, algum interno → recusado.
- Redirecionamento em cadeia acima do máximo → documento `falhou` com mensagem segura.
- Planilha protegida, corrompida ou sem abas → documento `falhou`, sem tela de seleção.
- Planilha confirmada depois de a retenção expirar → mensagem para reenviar o arquivo.
- Reprocessar com IA um documento que não está concluído → 409.
- Duas confirmações de abas para o mesmo documento → a segunda é ignorada com 409.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI em `src/app/` (`routers/conversao.py`, `tasks.py` com `process_conversion_document_task`), conversores em `src/pipeline/conversion/` despachados por `ConverterFactory.for_extension`, `XlsxConverter` converte todas as abas, `ConversaoConfig` guarda só idioma e limites de OCR. Armazenamento por `Storage`, retenção de 7 dias por `purgar_documentos_conversao_task`.
- Front em Next.js, `frontend/src/features/conversao/` (`ConversaoSheet`, `PainelLoteConversao`, `DataGridLotesConversao`, `SeloRevisarDocumento`).

#### Arquitetura e módulos

- `src/pipeline/conversion/converters/html.py` (`HtmlConverter`): recebe caminho, remove scripts/estilos, devolve `ConversionResult`; sem texto útil levanta erro de extração com a mensagem de FR-003.
- `src/pipeline/conversion/url_fetcher.py` (`UrlFetcher`): valida o esquema, resolve o DNS, bloqueia endereços não públicos, segue redirecionamentos validados, aplica tempo limite e tamanho máximo, devolve o HTML ao worker. Único ponto de saída de rede da conversão.
- `XlsxConverter` passa a aceitar uma lista de abas; `ConversaoConfig` ganha `max_bytes_arquivo`, `max_bytes_lote`, `timeout_url_s`, `max_bytes_url`, `max_redirecionamentos`.
- `src/pipeline/conversion/qualidade.py`: critério de baixa qualidade que gera `AvisoConversao` para formatos além do PDF (DEC-006).
- `src/pipeline/conversion/reprocessar_ia.py`: reprocessamento via `ChatModelAdapter` (DEC-007), exposto pela fachada `src/pipeline/service.py`. `src/pipeline/providers/contracts.py` e `providers/llm/openrouter.py` ganham partes de imagem opcionais em `ChatMessage`. `src/pipeline/providers/contracts.py` e `providers/llm/openrouter.py` ganham partes de imagem opcionais em `ChatMessage`.

#### Migrations

- Nova revisão Alembic aditiva em `documentos_conversao`: `origem_url` (texto, nulo), `abas_disponiveis` (JSON, nulo), `abas_selecionadas` (JSON, nulo), `reprocessado_ia_em` (data, nula). Rollback remove as colunas; documentos existentes ficam com valores nulos.

#### Models

- `DocumentoConversao` (`src/app/models.py`) ganha as quatro colunas; `situacao` ganha o valor `aguardando_abas`; `formato` aceita `html` e `url`.

#### Controllers e casos de uso

- `POST /api/v1/conversoes` aceita também `html` na lista de extensões e o campo `urls` (lista) no formulário; planilha entra em `aguardando_abas` com as abas lidas na hora.
- `POST /api/v1/conversoes/{lote}/documentos/{doc}/abas` com `{"abas": [...]}` confirma e enfileira a conversão.
- `POST /api/v1/conversoes/{lote}/documentos/{doc}/reprocessar-ia` enfileira o reprocessamento (papel de escrita).
- Tetos aplicados por documento em `enviar_conversoes`, no lugar da recusa do envio inteiro.

#### Views e experiência

- Ver seção 10.

#### Queries e repositórios

- `repo.py`: leitura e confirmação de abas, marcação de reprocessamento; listagem de lotes inalterada.

#### Jobs e processamento assíncrono

- `process_conversion_document_task` busca a URL (via `UrlFetcher`) quando o formato é `url`, respeita as abas selecionadas e nunca chama IA. Nova `reprocessar_documento_ia_task` com tentativa única e falha segura. Idempotência por situação do documento.

#### Estrutura de arquivos

```text
specs/planned/0036-fase-1-receber-e-converter-formatos/
  spec.md
  research/
src/pipeline/conversion/converters/html.py
src/pipeline/conversion/url_fetcher.py
src/pipeline/conversion/qualidade.py
src/pipeline/conversion/reprocessar_ia.py
src/app/routers/conversao.py
src/app/tasks.py
alembic/versions/<nova revisão>.py
frontend/src/features/conversao/
tests/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `DocumentoConversao` | `id` | Existentes mais `origem_url` (URL sem credenciais nem query string no registro), `abas_disponiveis`, `abas_selecionadas` (ao menos uma), `reprocessado_ia_em` | N:1 com `LoteConversao` |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| `DocumentoConversao` | (novo, planilha) | envio | `aguardando_abas` | nada é convertido antes da confirmação |
| `DocumentoConversao` | `aguardando_abas` | confirmar abas | `fila` | ao menos uma aba marcada |
| `DocumentoConversao` | (novo, demais) | envio | `fila` | teto respeitado |
| `DocumentoConversao` | `concluido` | reprocessar com IA | `processando` | só com pedido e papel de escrita |
| `DocumentoConversao` | `processando` | falha da IA | `concluido` | `.md` anterior preservado |

#### Migração e retenção

- Migração aditiva. A retenção de 7 dias da SPEC-0023 vale também para URL e `.html`; documento `aguardando_abas` expira como os demais, e a confirmação depois disso pede novo envio.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. A entrega muda a tela de Conversão do Workspace.

#### Stack e convenções de interface

- Next.js com App Router, React, TypeScript, shadcn/ui e Vitest (`frontend/package.json`); telas em `frontend/src/features/conversao/`. Preservar `ConversaoSheet`, `DataGridLotesConversao`, `PainelLoteConversao`, `SeloRevisarDocumento` e `situacao.ts`; alterar `ConversaoSheet` (aba Endereço), `PainelLoteConversao` (seleção de abas e reprocessar com IA) e `situacao.ts` (`aguardando_abas`).

#### Telas e responsabilidades

- **Conversão (aba do Workspace `/workspaces/[id]`)**: pessoa da consultoria envia arquivos ou URL, escolhe abas e acompanha o lote. Entrada: arquivos, endereços, abas; saída: `.md` por documento.

#### Fluxo de informação e navegação

- A pessoa abre "Converter documentos", escolhe Arquivos ou Endereço, envia; o lote aparece no mesmo `Sheet` e na lista. Planilha entra em "Aguardando abas": a pessoa marca, confirma e o documento segue para a fila. Documento "revisar" oferece Reprocessar com IA após confirmação. Breadcrumb existente do Workspace (equipe, módulo, tela) permanece.

#### Menus e navegação principal

- Sem novo item de menu: a tela continua acessada pela aba Conversão do Workspace, já presente no menu principal.

#### Formulários e ações

- Aba **Endereço**: campo de URL, botão Adicionar (várias URLs), lista removível; erro por linha. Aba **Arquivos**: `accept` inclui `.html`. Seleção de abas: lista de `Checkbox` rotulados, todas marcadas, Confirmar (desabilitado sem seleção). Reprocessar com IA: `Dialog` de confirmação informando que o conteúdo do documento será enviado ao provedor configurado. Padrão: `Sheet` já usado.

#### Composição e disposição

- `ConversaoSheet` ganha `Tabs` (Arquivos | Endereço). A seleção de abas aparece dentro do documento em `PainelLoteConversao`. Em 375 px, controles empilhados e sem rolagem horizontal; no desktop mantém `sm:max-w-lg`.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Conversão | `ConversaoSheet` | Abas Arquivos e Endereço, envio | `frontend/src/features/conversao/ConversaoSheet.tsx` | `Sheet`, `Tabs`, `Input`, `Button`, `Alert` | shadcn/ui | Estende o existente |
| Conversão | `EntradaEnderecos` | Campo, lista e validação de URLs | `frontend/src/features/conversao/EntradaEnderecos.tsx` | `Input`, `Button`, `Alert` | Próprio sobre shadcn/ui | Novo, extraído para não inflar a `ConversaoSheet` |
| Conversão | `SelecaoAbas` | Lista de abas, confirmar | `frontend/src/features/conversao/SelecaoAbas.tsx` | `Checkbox`, `Button`, `Alert` | Próprio sobre shadcn/ui | Novo |
| Conversão | `ReprocessarIaDialog` | Confirma envio ao provedor | `frontend/src/features/conversao/ReprocessarIaDialog.tsx` | `Dialog`, `Button`, `Alert` | Próprio sobre shadcn/ui; modelo `ApagarDocumentoDialog` | Novo |
| Conversão | `PainelLoteConversao` | Situação, abas, reprocessar | `frontend/src/features/conversao/PainelLoteConversao.tsx` | `Badge`, `Button` | Existente | Estende |
| Conversão | `DataGridLotesConversao` | Lista com ID, linha-link e ações | `frontend/src/features/conversao/DataGridLotesConversao.tsx` | tabela semântica | Existente | Estende com a ação Reprocessar |

- shadcn/ui fornece as primitives acima; nenhuma composição ReUI nova é necessária, pois o `DataGrid` próprio já existe. A lista final deve ser registrada em `INTERFACE.md`.

#### Estados e acessibilidade

- Loading (enviando, convertendo), vazio, erro por URL, sucesso, aguardando abas, permissão insuficiente (ações ocultas). Teclado em todos os controles, foco devolvido ao fechar diálogos, erros em `role=alert`, mudança de situação em `aria-live`.
- O Breadcrumb mantém a equipe visível e marca a tela atual.

#### Contrato CRUD

- Não há CRUD novo. Segue valendo o contrato da superfície: o `PageHeader` único do Workspace é reutilizado, sem markup próprio; o `DataGrid` (`DataGridLotesConversao`) ocupa a largura toda e mantém a coluna `ID` visível; a linha inteira é link para o painel por mouse e teclado; os botões independentes de editar e apagar continuam (apagar com confirmação e permissão), e esta entrega só acrescenta a ação Reprocessar com IA.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre em cada tarefa de interface, em 375 px e desktop, conferindo bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, nos estados vazio, erro, carregando, longo e curto.

#### APIs expostas

- `GET /api/v1/conversoes/limites` → 200 autenticado; retorna `max_arquivos`, `max_bytes_arquivo` e `max_bytes_lote` para a interface refletir FR-006, sem configuração secreta.

- `POST /api/v1/conversoes` (multipart; `arquivos`, `urls`, `workspace_id`) → 201; erros 400 por documento recusado indicados na resposta.
- `POST /api/v1/conversoes/{lote}/documentos/{doc}/abas` → 200 | 400 | 409.
- `POST /api/v1/conversoes/{lote}/documentos/{doc}/reprocessar-ia` → 202 | 403 | 409.
- Autenticação por `get_identity`; escrita exige `require_write_role`; compatível com os clientes atuais.

#### APIs externas utilizadas

- Páginas públicas buscadas por `UrlFetcher` (tempo limite, tamanho e redirecionamentos configuráveis; sem retry automático).
- Provedor de IA configurado, só no reprocessamento sob pedido, via `ChatModelAdapter`; timeout e falha segura.

#### Documentação das APIs consultadas

- Nenhuma externa nesta fase; contratos locais em `src/pipeline/providers/contracts.py`.

#### Eventos e outros contratos

- `AvisoConversao` (código, página, mensagem) reaproveitado para o motivo "revisar"; novo código para qualidade geral (DEC-006).

### 11. Estratégia TDD

- **Unidade**: `HtmlConverter`, `UrlFetcher` (bloqueio de endereço, redirecionamento, DNS simulado), `XlsxConverter` com abas, `qualidade`, `ConversaoConfig`.
- **Integração/contrato**: rotas de conversão com `TestClient`, worker com fila em memória, servidor HTTP falso para a busca e provedor de IA falso que falha se chamado sem pedido.
- **BDD/aceite**: Gherkin da seção 6 orienta os casos TDD; não há arquivos `.feature`.
- **Runner TDD**: Pytest para Python; Vitest (`npm run test:tdd` em `frontend/`) para componentes.
- **E2E**: Não aplicável; a revisão visual cobre a jornada na interface.
- **Verificação manual**: leitura real de uma página pública e de um provedor de IA real, por limitação das integrações; testes usam simulações.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-009, NFR-003, AC-001 | AC-001 na seção 6 | Caso `test_spec_0036_ac_001_url_publica_gera_markdown_rastreavel` em tests/test_conversion_html_url.py com marcador próprio `SPECSFY: AC-001` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-001, FR-001, AC-002 | AC-002 na seção 6 | Caso `test_spec_0036_ac_002_uma_url_um_documento_sem_seguir_links` em tests/test_conversion_html_url.py com marcador próprio `SPECSFY: AC-002` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-001, FR-001, NFR-001, AC-003 | AC-003 na seção 6 | Caso `test_spec_0036_ac_003_falha_de_rede_marca_so_o_documento` em tests/test_conversion_html_url.py com marcador próprio `SPECSFY: AC-003` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-001, FR-002, NFR-001, AC-004 | AC-004 na seção 6 | Caso `test_spec_0036_ac_004_enderecos_internos_sao_recusados` em tests/test_conversion_url_seguranca.py com marcador próprio `SPECSFY: AC-004` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-001, FR-002, NFR-001, AC-005 | AC-005 na seção 6 | Caso `test_spec_0036_ac_005_redirecionamento_para_rede_interna_e_bloqueado` em tests/test_conversion_url_seguranca.py com marcador próprio `SPECSFY: AC-005` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| FR-002, NFR-001, US-001, AC-006 | AC-006 na seção 6 | Caso `test_spec_0036_ac_006_dns_que_resolve_para_interno_e_bloqueado` em tests/test_conversion_url_seguranca.py com marcador próprio `SPECSFY: AC-006` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-001, FR-003, AC-007 | AC-007 na seção 6 | Caso `test_spec_0036_ac_007_pagina_sem_texto_orienta_salvar_html` em tests/test_conversion_html_url.py com marcador próprio `SPECSFY: AC-007` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-001, FR-003, FR-001, AC-008 | AC-008 na seção 6 | Caso `test_spec_0036_ac_008_resposta_que_nao_e_html_e_recusada` em tests/test_conversion_html_url.py com marcador próprio `SPECSFY: AC-008` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-001, US-004, FR-006, NFR-001, AC-009 | AC-009 na seção 6 | Caso `test_spec_0036_ac_009_resposta_acima_do_teto_recusa_so_aquela_url` em tests/test_conversion_limites.py com marcador próprio `SPECSFY: AC-009` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-002, FR-004, FR-009, AC-010 | AC-010 na seção 6 | Caso `test_spec_0036_ac_010_arquivo_html_gera_markdown_sem_scripts` em tests/test_conversion_html_url.py com marcador próprio `SPECSFY: AC-010` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-002, FR-003, FR-004, AC-011 | AC-011 na seção 6 | Caso `test_spec_0036_ac_011_html_sem_texto_util_orienta_a_pessoa` em tests/test_conversion_html_url.py com marcador próprio `SPECSFY: AC-011` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-002, FR-004, NFR-001, AC-012 | AC-012 na seção 6 | Caso `test_spec_0036_ac_012_scripts_do_html_nunca_sao_executados` em tests/test_conversion_url_seguranca.py com marcador próprio `SPECSFY: AC-012` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-003, FR-005, NFR-004, NFR-003, AC-013 | AC-013 na seção 6 | Caso `test_spec_0036_ac_013_planilha_com_varias_abas_aguarda_confirmacao` em tests/test_conversion_xlsx_abas.py com marcador próprio `SPECSFY: AC-013` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-003, FR-005, AC-014 | AC-014 na seção 6 | Caso `test_spec_0036_ac_014_so_as_abas_marcadas_viram_markdown` em tests/test_conversion_xlsx_abas.py com marcador próprio `SPECSFY: AC-014` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-003, FR-005, NFR-004, AC-015 | AC-015 na seção 6 | Caso `test_ac_015` em frontend/src/features/conversao/ConversaoFase1.test.tsx com marcador próprio `SPECSFY: AC-015` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-004, FR-006, AC-016 | AC-016 na seção 6 | Caso `test_spec_0036_ac_016_arquivo_acima_do_teto_e_recusado_e_o_outro_segue` em tests/test_conversion_limites.py com marcador próprio `SPECSFY: AC-016` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-004, FR-006, AC-017 | AC-017 na seção 6 | Caso `test_spec_0036_ac_017_lote_acima_do_teto_recusa_o_excedente` em tests/test_conversion_limites.py com marcador próprio `SPECSFY: AC-017` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-004, FR-006, NFR-005, AC-018 | AC-018 na seção 6 | Caso `test_spec_0036_ac_018_tetos_vem_da_configuracao` em tests/test_conversion_limites.py com marcador próprio `SPECSFY: AC-018` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-005, FR-007, AC-019 | AC-019 na seção 6 | Caso `test_spec_0036_ac_019_baixa_qualidade_marca_revisar` em tests/test_conversion_reprocessar_ia.py com marcador próprio `SPECSFY: AC-019` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-005, FR-007, NFR-005, AC-020 | AC-020 na seção 6 | Caso `test_spec_0036_ac_020_documento_bom_nao_recebe_selo` em tests/test_conversion_reprocessar_ia.py com marcador próprio `SPECSFY: AC-020` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-005, FR-008, NFR-002, AC-021 | AC-021 na seção 6 | Caso `test_spec_0036_ac_021_reprocessar_envia_so_aquele_documento` em tests/test_conversion_reprocessar_ia.py com marcador próprio `SPECSFY: AC-021` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-005, FR-008, FR-009, NFR-002, AC-022 | AC-022 na seção 6 | Caso `test_spec_0036_ac_022_sem_pedido_nada_vai_a_ia` em tests/test_conversion_reprocessar_ia.py com marcador próprio `SPECSFY: AC-022` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-005, FR-008, AC-023 | AC-023 na seção 6 | Caso `test_spec_0036_ac_023_falha_da_ia_preserva_o_markdown_anterior` em tests/test_conversion_reprocessar_ia.py com marcador próprio `SPECSFY: AC-023` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| US-005, FR-008, NFR-002, AC-024 | AC-024 na seção 6 | Caso `test_spec_0036_ac_024_member_nao_reprocessa_com_ia` em tests/test_conversion_reprocessar_ia.py com marcador próprio `SPECSFY: AC-024` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| FR-009, FR-007, NFR-005, AC-025 | AC-025 na seção 6 | Caso `test_spec_0036_ac_025_formatos_existentes_continuam_convertendo` em tests/test_router_conversao_fase1.py com marcador próprio `SPECSFY: AC-025` | Caracterização verde (comportamento já existente), protege contra regressão | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| NFR-002, NFR-001, US-001, AC-026 | AC-026 na seção 6 | Caso `test_spec_0036_ac_026_logs_e_mensagens_nao_expoem_credenciais` em tests/test_conversion_url_seguranca.py com marcador próprio `SPECSFY: AC-026` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| NFR-005, FR-009, US-003, AC-027 | AC-027 na seção 6 | Caso `test_spec_0036_ac_027_migracao_preserva_lotes_e_documentos` em tests/test_router_conversao_fase1.py com marcador próprio `SPECSFY: AC-027` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| NFR-003, US-001, FR-001, AC-028 | AC-028 na seção 6 | Caso `test_spec_0036_ac_028_envio_de_url_responde_sem_buscar` em tests/test_router_conversao_fase1.py com marcador próprio `SPECSFY: AC-028` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |
| NFR-004, US-001, FR-002, AC-029 | AC-029 na seção 6 | Caso `test_ac_029` em frontend/src/features/conversao/ConversaoFase1.test.tsx com marcador próprio `SPECSFY: AC-029` | Observado 2026-10-15: falha por comportamento ausente | GREEN 2026-10-15: Pytest/Vitest aprovados, evidências em research/ | Regressão completa aprovada |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-001 | AC-002 | Unidade | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-001 | AC-003 | Integração | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-001 | AC-008 | Unidade | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-001 | AC-028 | Integração | tests/test_router_conversao_fase1.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-002 | AC-004 | Unidade | tests/test_conversion_url_seguranca.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-002 | AC-005 | Integração | tests/test_conversion_url_seguranca.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-002 | AC-006 | Unidade | tests/test_conversion_url_seguranca.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-002 | AC-029 | Componente | frontend/src/features/conversao/ConversaoFase1.test.tsx | Passed — pytest-completo.log e vitest-completo.log |
| FR-003 | AC-007 | Integração | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-003 | AC-008 | Unidade | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-003 | AC-011 | Unidade | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-004 | AC-010 | Integração | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-004 | AC-011 | Unidade | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-004 | AC-012 | Unidade | tests/test_conversion_url_seguranca.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-005 | AC-013 | Integração | tests/test_conversion_xlsx_abas.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-005 | AC-014 | Integração | tests/test_conversion_xlsx_abas.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-005 | AC-015 | Componente | frontend/src/features/conversao/ConversaoFase1.test.tsx | Passed — pytest-completo.log e vitest-completo.log |
| FR-006 | AC-009 | Integração | tests/test_conversion_limites.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-006 | AC-016 | Integração | tests/test_conversion_limites.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-006 | AC-017 | Integração | tests/test_conversion_limites.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-006 | AC-018 | Unidade | tests/test_conversion_limites.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-007 | AC-019 | Integração | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-007 | AC-020 | Unidade | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-007 | AC-025 | Integração | tests/test_router_conversao_fase1.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-008 | AC-021 | Integração | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-008 | AC-022 | Integração | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-008 | AC-023 | Integração | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-008 | AC-024 | Integração | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-009 | AC-001 | Integração | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-009 | AC-010 | Integração | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-009 | AC-022 | Integração | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-009 | AC-025 | Integração | tests/test_router_conversao_fase1.py | Passed — pytest-completo.log e vitest-completo.log |
| FR-009 | AC-027 | Integração | tests/test_router_conversao_fase1.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-001 | AC-003 | Integração | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-001 | AC-004 | Unidade | tests/test_conversion_url_seguranca.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-001 | AC-005 | Integração | tests/test_conversion_url_seguranca.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-001 | AC-006 | Unidade | tests/test_conversion_url_seguranca.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-001 | AC-009 | Integração | tests/test_conversion_limites.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-001 | AC-012 | Unidade | tests/test_conversion_url_seguranca.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-001 | AC-026 | Unidade | tests/test_conversion_url_seguranca.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-002 | AC-021 | Integração | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-002 | AC-022 | Integração | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-002 | AC-024 | Integração | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-002 | AC-026 | Unidade | tests/test_conversion_url_seguranca.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-003 | AC-001 | Integração | tests/test_conversion_html_url.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-003 | AC-013 | Integração | tests/test_conversion_xlsx_abas.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-003 | AC-028 | Integração | tests/test_router_conversao_fase1.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-004 | AC-013 | Integração | tests/test_conversion_xlsx_abas.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-004 | AC-015 | Componente | frontend/src/features/conversao/ConversaoFase1.test.tsx | Passed — pytest-completo.log e vitest-completo.log |
| NFR-004 | AC-029 | Componente | frontend/src/features/conversao/ConversaoFase1.test.tsx | Passed — pytest-completo.log e vitest-completo.log |
| NFR-005 | AC-018 | Unidade | tests/test_conversion_limites.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-005 | AC-020 | Unidade | tests/test_conversion_reprocessar_ia.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-005 | AC-025 | Integração | tests/test_router_conversao_fase1.py | Passed — pytest-completo.log e vitest-completo.log |
| NFR-005 | AC-027 | Integração | tests/test_router_conversao_fase1.py | Passed — pytest-completo.log e vitest-completo.log |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (2026-10-15)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/planned/0036-fase-1-receber-e-converter-formatos/spec.md`
- **Achados**: formato válido; 5 US, 9 FR, 5 NFR e 29 AC, todos com no mínimo três AC. Revisão semântica trouxe três avisos resolvidos na própria spec: critério de "baixa qualidade" sem valor (agora DEC-006), contrato de chat só texto (agora DEC-007) e risco de troca de DNS entre validação e conexão (FR-002).
- **FIND-SEC-001** [P2] [Resolved] Validar o endereço e depois resolver o nome de novo permitiria trocar o destino por um interno — Refs: FR-002, NFR-001 — Evidence: src/app/routers/conversao.py — Effect: acesso à rede interna pelo worker — Suggestion: conectar ao endereço já validado (FR-002 e AC-006 atualizados)
- **FIND-ARCH-001** [P2] [Resolved] `ChatMessage` aceita só texto, o que bloquearia o reprocessamento com IA por imagem — Refs: FR-008 — Evidence: src/pipeline/providers/contracts.py — Effect: tarefa de IA inexequível sem mudar o contrato — Suggestion: estender o contrato de forma retrocompatível (DEC-007)
- **FIND-PROD-001** [P2] [Resolved] FR-007 não tinha critério mensurável de baixa qualidade — Refs: FR-007 — Evidence: src/pipeline/conversion/config.py — Effect: AC-019 não testável — Suggestion: sinais objetivos configuráveis (DEC-006)
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-15)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/planned/0036-fase-1-receber-e-converter-formatos/spec.md`
- **Achados**: 43 tarefas (30 TEST/TDD, 10 CODE/DOC, 3 interface/final), 48/48 IDs cobertos. RED observado em 28 dos 29 testes de AC; o AC-025 é caracterização verde do comportamento existente. Ajuste de plano: `member` é somente leitura (`PAPEIS_DE_ESCRITA`) e planilha de uma aba segue direta para a fila (FR-005, para preservar a SPEC-0023).

#### Aceite final da SPEC-0036

- READY em 2026-10-15: 29 AC com resultado QA Passed, 48/48 IDs com cadeia completa, 43 tarefas e 258 itens concluídos; evidência strict aprovada, revisão semântica sem bloqueador da fatia. FIND-ARCH-002 permanece como nota P3 de histórico externo ao alcance. Projeção global não foi declarada aprovada.

#### Gate do Ato III — Entrega

- **Resultado**: Passed para a SPEC-0036 (2026-10-15), com nota histórica global em FIND-ARCH-002.
- **Comandos e resultados**:
  - `uv run --with pytest-xdist pytest -q -n 4 -x`: 706 passed, 1 skipped, exit 0. Plugin usado apenas nesta execução, sem alterar manifests. O skip é o teste externo preexistente da SPEC-0014 sem OPENAI_API_KEY; nenhum AC desta fatia foi pulado.
  - `npm run test:tdd`: 245 passed, exit 0; teste focal do diálogo repetido após o ajuste de CSS: 3 passed.
  - `uv run ruff check`, `npm run lint`, `npm run typecheck`, `npm run build`: aprovados.
  - `check_traceability.mjs --full-chain`: 48/48 IDs, OK; `verify_evidence.mjs`: PASSED strict.
  - Página pública real do Python: 96.610 bytes de HTML convertidos em 31.866 caracteres de Markdown, sem LLM.
- **Revisão visual**: Chromium no build de produção, 375/1280 px, zoom 200% e emulação 400%; capturas e resultados em research/.
- **Integrações externas**: provedor real de IA não acionado; payload multimodal, falhas, privacidade e substituição de Markdown verificados com duplos e renderização real de PDF.
- **FIND-ARCH-002** [P3] [Open] O verificador global ainda aponta sete falhas históricas de trace/research nas SPEC-0012, 0013, 0019, 0023, 0026 e 0030 — Refs: NFR-005 — Evidence: specs/completed/0036-fase-1-receber-e-converter-formatos/research/gates-historicos-head.json — Effect: projeção global não está verde; nenhum requisito ou teste de aplicação desta fatia falha — Suggestion: reconciliar a documentação histórica em trabalho próprio. As mesmas sete falhas foram reproduzidas em HEAD; não foram ocultadas ou reclassificadas como aprovadas.
- **Projeção final**: SPEC-0036 Complete, 43/43 tarefas e 3/3 gates; repositório com 35/36 specs completas. A SPEC-0032 permanece aberta, fora desta entrega; nenhum deploy foi executado.
- **Escopo do gate**: provas de aplicação e rastreabilidade da SPEC-0036 aprovadas; as falhas globais preexistentes permanecem registradas, sem alterar specs concluídas ou suas evidências históricas.

#### Reconciliação de compatibilidade — 2026-10-15

- Revalidação Ato I: READY por `validate_spec.mjs --allow-draft`; os 29 AC mantêm os mesmos IDs e cobertura. DEC-009 usa a decisão explícita do backlog. A base Git não contém esta spec ainda não rastreada; `analyze_change --base HEAD` indisponível, comparação semântica registrada aqui.

- **FIND-PROD-002** [P2] [Resolved] AC-025/NFR-005 prometiam suíte antiga intacta, mas FR-006 substitui a recusa integral por decisão confirmada no backlog — Refs: FR-006, NFR-005, AC-025 — Evidence: tests/test_router_conversao.py — Effect: expectativas incompatíveis impediam a regressão — Suggestion: DEC-009 aplicada e gates revalidados, preservando os demais testes

- Revalidação Ato II: `validate_tasks.mjs` READY, 48/48 IDs, predecessores T009/T016/T017/T018 concluídos. RED de AC-017 preservado; teste legado substituído exclusivamente conforme DEC-009.

#### Ambiente de verificação — 2026-10-15

- O PostgreSQL de testes anterior acumulou 9.208 schemas e 971.280 relações. A suíte base foi interrompida por lentidão, sem atribuir suas falhas à mudança. Novo container local PostgreSQL 16 `rag-spec0036-test-postgres`, banco `rag_spec0036_test`, validado SAFE; nenhuma estrutura anterior foi apagada. Configuração original privada preservada em `/tmp/spec0036-env-testing-original`.

#### Verificação adicional de T041

- RED observado em 2026-10-15: `npm run test:tdd -- src/features/conversao/ReprocessarIaDialog.test.tsx`, 3 falhas por componente ausente. Cenários AC-021/AC-022/AC-023 informaram confirmação, cancelamento e falha segura do diálogo.

#### Regressão e compatibilidade em T043

- Snapshot de dependências de `test_client_neutrality.py` atualizado exclusivamente com Beautiful Soup/markdownify, já autorizadas em DEC-003. Snapshot de `contracts.py` atualizado pela extensão multimodal autorizada em DEC-007; comparação AST contra HEAD comprovou os demais contratos idênticos.
- Marcador português preexistente no problema foi substituído por “envio inteiro”; sem mudança de significado. Formatação Ruff das suítes RED recebidas será reconciliada sem alterar cenários.

#### Proteções complementares verificadas em T043

- RED: `uv run pytest -q tests/test_conversion_limites.py tests/test_conversion_reprocessar_ia.py -k 'teto_do_lote or job_repetido'`, 2 failed por comportamento ausente. FR-006 passa a reservar o tamanho da página sob bloqueio do lote; FR-008 só executa job no estado solicitado pelo endpoint. Fixture de falha AC-023 agora simula esse estado solicitado, preservando a mesma asserção de Markdown anterior intacto.
- Teste complementar do transporte inspeciona IP numérico, ausência de segunda resolução, Host e SNI com verificação TLS mantida; não depende da rede real.

#### Exibição de limites em T043

- RED adicional de AC-018: `npm run test:tdd -- src/features/conversao/ConversaoSheetLimites.test.tsx`, 1 failed porque limites inferiores a 1 MiB eram arredondados para zero. A interface passa a exibir bytes exatos nesses casos, preservando MB nos limites padrão.

#### Revisão de conformidade e estabilidade em T043

- IA não herda o teto de páginas do OCR, respeitando o fora de escopo de DEC-005. RED observado no teste `test_limite_de_ocr_nao_cria_limite_de_paginas_para_ia` antes da correção; a leitura de duas páginas com teto OCR 1 deve enviar as duas imagens.
- FR-003: resposta não HTML agora também preserva a expressão exigida de falha de extração, com orientação de envio do HTML.
- Falso positivo de teste legado: o número restrito 137 apareceu dentro de um UUID aleatório; a asserção foi limitada a valores numéricos completos, mantendo a proteção contra vazamento real.
- A cópia histórica de HEAD usada para provar as sete falhas de metadados foi removida após a auditoria. Ela havia sido incluída na varredura AST de providers; novas verificações ocorrem sem esse artefato.

#### Revisão visual final

- Build de produção inspecionado em Chromium em 375 e 1280 px, com teclado, erro, abas marcadas/desmarcadas, nome longo, confirmação, cancelamento, pending, reprocessamento e papel member.
- Emulação de zoom 400% de desktop (viewport CSS 320×225, escala 4): o diálogo ultrapassava a janela. A composição local passa a limitar altura e permitir rolagem interna, sem alterar o primitive global.
- Os testes completos de frontend passaram (245 casos); lint, tipos e build passaram. Ajustes finais de CSS são conferidos novamente no build de produção e nos testes do diálogo.
- A rodada paralela de Pytest encontrou apenas a medição de inicialização do SDK sob carga; o mesmo teste passou isoladamente em 3,84 s sem mudar a asserção. Fechamento usa o runner padrão.

#### Fechamento da qualidade após IA

- RED: teste AC-021 reforçado para uma resposta curta da IA, 1 failed antes da correção. A mesma avaliação determinística de FR-007 é aplicada após reprocessamento; selo só desaparece quando o texto não apresenta os sinais de baixa qualidade.
- O teste legado de timeout conserva sua asserção e o servidor que não responde; preparação do SDK foi movida para antes da medição de rede, evitando que importação fria sob carga seja confundida com falha de timeout.

#### Execução T030 — 2026-10-15

- PREP: Definition, Plan e interface READY; predecessores T009/T016/T017/T018 com RED registrado; documentação reconstruída. Branch própria criada.
- Revisão de PROJECT.md: os tetos configuráveis e a recusa parcial refinam a conversão existente sem mudar a finalidade ou os limites gerais do produto; sem alteração narrativa nesta tarefa.
- Baseline em execução: `uv run pytest -q`, após proteção SAFE. AC-009 depende também de T031/T033; seu GREEN será verificado com o worker de URL.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso de teste falhando em tests/test_conversion_html_url.py — Refs: US-001, FR-001, FR-009, NFR-003, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_html_url.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso de teste falhando em tests/test_conversion_html_url.py — Refs: US-001, FR-001, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_html_url.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso de teste falhando em tests/test_conversion_html_url.py — Refs: US-001, FR-001, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_html_url.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso de teste falhando em tests/test_conversion_url_seguranca.py — Refs: US-001, FR-002, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_url_seguranca.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 um caso de teste falhando em tests/test_conversion_url_seguranca.py — Refs: US-001, FR-002, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_url_seguranca.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-006 um caso de teste falhando em tests/test_conversion_url_seguranca.py — Refs: FR-002, NFR-001, US-001, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_url_seguranca.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T007 [TEST] [TDD] [US-001] Derivar do AC-007 um caso de teste falhando em tests/test_conversion_html_url.py — Refs: US-001, FR-003, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_html_url.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T008 [TEST] [TDD] [US-001] Derivar do AC-008 um caso de teste falhando em tests/test_conversion_html_url.py — Refs: US-001, FR-003, FR-001, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_html_url.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T009 [TEST] [TDD] [US-001] Derivar do AC-009 um caso de teste falhando em tests/test_conversion_limites.py — Refs: US-001, US-004, FR-006, NFR-001, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_limites.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T010 [TEST] [TDD] [US-002] Derivar do AC-010 um caso de teste falhando em tests/test_conversion_html_url.py — Refs: US-002, FR-004, FR-009, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_html_url.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T011 [TEST] [TDD] [US-002] Derivar do AC-011 um caso de teste falhando em tests/test_conversion_html_url.py — Refs: US-002, FR-003, FR-004, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_html_url.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T012 [TEST] [TDD] [US-002] Derivar do AC-012 um caso de teste falhando em tests/test_conversion_url_seguranca.py — Refs: US-002, FR-004, NFR-001, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_url_seguranca.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-013 um caso de teste falhando em tests/test_conversion_xlsx_abas.py — Refs: US-003, FR-005, NFR-004, NFR-003, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_xlsx_abas.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T014 [TEST] [TDD] [US-003] Derivar do AC-014 um caso de teste falhando em tests/test_conversion_xlsx_abas.py — Refs: US-003, FR-005, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_xlsx_abas.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T015 [TEST] [TDD] [US-003] Derivar do AC-015 um caso de teste falhando em frontend/src/features/conversao/ConversaoFase1.test.tsx — Refs: US-003, FR-005, NFR-004, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest frontend/src/features/conversao/ConversaoFase1.test.tsx` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T016 [TEST] [TDD] [US-004] Derivar do AC-016 um caso de teste falhando em tests/test_conversion_limites.py — Refs: US-004, FR-006, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_limites.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T017 [TEST] [TDD] [US-004] Derivar do AC-017 um caso de teste falhando em tests/test_conversion_limites.py — Refs: US-004, FR-006, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_limites.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T018 [TEST] [TDD] [US-004] Derivar do AC-018 um caso de teste falhando em tests/test_conversion_limites.py — Refs: US-004, FR-006, NFR-005, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_limites.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T019 [TEST] [TDD] [US-005] Derivar do AC-019 um caso de teste falhando em tests/test_conversion_reprocessar_ia.py — Refs: US-005, FR-007, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_reprocessar_ia.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T020 [TEST] [TDD] [US-005] Derivar do AC-020 um caso de teste falhando em tests/test_conversion_reprocessar_ia.py — Refs: US-005, FR-007, NFR-005, AC-020 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_reprocessar_ia.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T021 [TEST] [TDD] [US-005] Derivar do AC-021 um caso de teste falhando em tests/test_conversion_reprocessar_ia.py — Refs: US-005, FR-008, NFR-002, AC-021 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_reprocessar_ia.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T022 [TEST] [TDD] [US-005] Derivar do AC-022 um caso de teste falhando em tests/test_conversion_reprocessar_ia.py — Refs: US-005, FR-008, FR-009, NFR-002, AC-022 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_reprocessar_ia.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T023 [TEST] [TDD] [US-005] Derivar do AC-023 um caso de teste falhando em tests/test_conversion_reprocessar_ia.py — Refs: US-005, FR-008, AC-023 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_reprocessar_ia.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T024 [TEST] [TDD] [US-005] Derivar do AC-024 um caso de teste falhando em tests/test_conversion_reprocessar_ia.py — Refs: US-005, FR-008, NFR-002, AC-024 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_reprocessar_ia.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T025 [TEST] [TDD] [US-001] Derivar do AC-025 um caso de teste falhando em tests/test_router_conversao_fase1.py — Refs: FR-009, FR-007, NFR-005, AC-025 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_router_conversao_fase1.py`; resultado: verde, caracterização do comportamento existente (formatos da SPEC-0023 e da SPEC-0033), sem RED esperado.
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T026 [TEST] [TDD] [US-001] Derivar do AC-026 um caso de teste falhando em tests/test_conversion_url_seguranca.py — Refs: NFR-002, NFR-001, US-001, AC-026 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_conversion_url_seguranca.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T027 [TEST] [TDD] [US-003] Derivar do AC-027 um caso de teste falhando em tests/test_router_conversao_fase1.py — Refs: NFR-005, FR-009, US-003, AC-027 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_router_conversao_fase1.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T028 [TEST] [TDD] [US-001] Derivar do AC-028 um caso de teste falhando em tests/test_router_conversao_fase1.py — Refs: NFR-003, US-001, FR-001, AC-028 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest tests/test_router_conversao_fase1.py` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [x] T029 [TEST] [TDD] [US-001] Derivar do AC-029 um caso de teste falhando em frontend/src/features/conversao/ConversaoFase1.test.tsx — Refs: NFR-004, US-001, FR-002, AC-029 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [x] **EVIDENCE**: Comando `uv run pytest frontend/src/features/conversao/ConversaoFase1.test.tsx` (front: `npx vitest run`); causa do RED: comportamento ausente da SPEC-0036 (módulo, estado ou endpoint ainda não existe).
  - [x] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

#### Fase 2 — Entrega backend e worker

**Objetivo**: URL, HTML, abas, tetos, qualidade e IA no backend.
**Teste independente**: `uv run pytest tests/test_conversion_*.py tests/test_router_conversao*.py`.

- [x] T030 [CODE] [US-004] Estender `ConversaoConfig` com tetos e parâmetros de URL e qualidade e aplicar o teto por documento em src/pipeline/conversion/config.py e src/app/routers/conversao.py — Refs: US-004, FR-006, NFR-001, NFR-005, AC-009, AC-016, AC-017, AC-018 — Depends: T009, T016, T017, T018
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator`, confirmar RED dos predecessores TDD e dependências.
  - [x] **EXECUTE**: Adicionar `max_bytes_arquivo`, `max_bytes_lote`, `timeout_url_s`, `max_bytes_url`, `max_redirecionamentos` e limiares de qualidade (DEC-004, DEC-005, DEC-006); recusar só o documento excedente.
  - [x] **VERIFY**: Rodar os testes de limites e a suíte de conversão; DEC-009 atualiza somente a rejeição integral antiga para aceitação parcial.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [x] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.

Verificação focal: 3 passed em tests/test_conversion_limites.py (-k not ac_009); compatibilidade de mensagem 40 MB: 1 passed. ZIP e aceitação parcial passaram em execução relacionada; tentativas anteriores interrompidas após falhas já corrigidas. Regressão completa segue como gate T043.

<!-- specsfy:evidence {"task":"T030","refs":["US-004","FR-006","NFR-001","NFR-005","AC-009","AC-016","AC-017","AC-018"],"files":["src/pipeline/conversion/config.py","src/app/routers/conversao.py","tests/test_router_conversao.py"],"commands":[{"run":"uv run pytest -q tests/test_conversion_limites.py -k 'not ac_009'","exit":0},{"run":"uv run pytest -q tests/test_router_conversao.py::test_spec_0023_ac_005_rejeita_arquivo_acima_de_40_mb","exit":0}]} -->

Melhoria: leitura limitada a teto + 1 byte evita carregar arquivos inteiros acima do limite; erros HTTP mantêm texto compatível. GREEN de AC-009 depende da entrega do worker, não atestado nesta tarefa.


- [x] T031 [CODE] [US-001] Criar `UrlFetcher` com bloqueio de rede interna, DNS validado e redirecionamentos em src/pipeline/conversion/url_fetcher.py — Refs: US-001, FR-001, FR-002, NFR-001, AC-003, AC-004, AC-005, AC-006, AC-026 — Depends: T003, T004, T005, T006, T026, T030
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator`, confirmar RED dos predecessores TDD e dependências.
  - [x] **EXECUTE**: Implementar a validação do endereço resolvido, conexão ao IP validado, tempo limite, tamanho máximo, redirecionamentos e logs sem credenciais.
  - [x] **VERIFY**: Rodar os testes de segurança da busca.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [x] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.

Predecessores T003/T004/T005/T006/T026 têm RED; T030 concluída. Fontes OWASP/Python indexadas em research/busca-publica.md. Arquitetura preserva a fachada única.

PROJECT.md revisado: módulo interno de busca ainda não exposto à pessoa, sem mudança narrativa nesta tarefa.

3 testes de segurança passaram: AC-004, AC-005 e AC-006. AC-003/AC-026 serão exercitados com o worker em T033.

<!-- specsfy:evidence {"task":"T031","refs":["US-001","FR-001","FR-002","NFR-001","AC-003","AC-004","AC-005","AC-006","AC-026"],"files":["src/pipeline/conversion/url_fetcher.py","src/pipeline/conversion/contracts.py"],"commands":[{"run":"uv run pytest -q tests/test_conversion_url_seguranca.py -k 'ac_004 or ac_005 or ac_006'","exit":0}]} -->

Melhoria: validação de cada resposta DNS, limite de leitura streaming e mensagens de falha sem URL; nenhuma credencial é registrada.


- [x] T032 [CODE] [US-002] Criar `HtmlConverter` e registrá-lo na factory em src/pipeline/conversion/converters/html.py e src/pipeline/conversion/factory.py — Refs: US-002, FR-003, FR-004, FR-009, AC-007, AC-008, AC-010, AC-011, AC-012 — Depends: T007, T008, T010, T011, T012, T030
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator`, confirmar RED dos predecessores TDD e dependências.
  - [x] **EXECUTE**: Extrair texto com `beautifulsoup4` e `markdownify` (DEC-003), descartar scripts e estilos, e levantar a mensagem de FR-003 sem texto útil.
  - [x] **VERIFY**: Rodar os testes de HTML.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [x] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.

T007/T008/T010/T011/T012 com RED, T030 concluída; bibliotecas DEC-003 serão declaradas com o conversor; registro documental T037 permanece.

3 passed: AC-008 (resposta não HTML), AC-011 (HTML sem texto) e AC-012 (scripts não executados). Integração de AC-010 aguarda T033.

<!-- specsfy:evidence {"task":"T032","refs":["US-002","FR-003","FR-004","FR-009","AC-007","AC-008","AC-010","AC-011","AC-012"],"files":["src/pipeline/conversion/converters/html.py","src/pipeline/conversion/factory.py","pyproject.toml","uv.lock"],"commands":[{"run":"uv run pytest -q tests/test_conversion_html_url.py tests/test_conversion_url_seguranca.py -k 'ac_011 or ac_012 or ac_008'","exit":0}]} -->

Melhoria: remove também iframes, objetos, templates e imagens; nenhum recurso externo é buscado pelo parser local.


- [x] T033 [CODE] [US-001] Criar a migração, os models, o envio de `urls` e `.html` e a busca de URL no worker em alembic/versions/, src/app/models.py, src/app/routers/conversao.py e src/app/tasks.py — Refs: US-001, FR-001, NFR-003, NFR-005, AC-001, AC-002, AC-027, AC-028 — Depends: T001, T002, T027, T028, T031, T032
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator`, confirmar RED dos predecessores TDD e dependências.
  - [x] **EXECUTE**: Migração aditiva de `documentos_conversao`, novos formatos `html` e `url`, `origem_url` sem credenciais, e `process_conversion_document_task` buscando a URL pelo `UrlFetcher`.
  - [x] **VERIFY**: Rodar os testes do roteador e da migração.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [x] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.

Predecessores com RED e T031/T032 concluídas. Caminho real das migrações: alembic/versions/, conforme regra local; usar revisão aditiva após 0031_conteudo_documento.

21 passed: URL/HTML, segurança, tetos, API e preservação de registros pela migração. Upgrade head e current executados em schema exclusivo da instância de testes, ambos SAFE.

<!-- specsfy:evidence {"task":"T033","refs":["US-001","FR-001","NFR-003","NFR-005","AC-001","AC-002","AC-027","AC-028"],"files":["alembic/versions/0036_conversao_formatos.py","src/app/models.py","src/app/routers/conversao.py","src/app/tasks.py","src/pipeline/service.py"],"commands":[{"run":"uv run pytest -q tests/test_conversion_html_url.py tests/test_conversion_url_seguranca.py tests/test_conversion_limites.py tests/test_router_conversao_fase1.py -x","exit":0}]} -->

Melhoria: origem persistida e Markdown sem query string; URL completa fica somente no original sujeito à retenção, e requisições de saída continuam exclusivamente no worker.


- [x] T034 [CODE] [US-003] Aceitar abas no `XlsxConverter` e criar o estado `aguardando_abas` e o endpoint de confirmação em src/pipeline/conversion/converters/xlsx.py, src/app/routers/conversao.py e src/app/repo.py — Refs: US-003, FR-005, NFR-003, NFR-004, AC-013, AC-014, AC-015 — Depends: T013, T014, T015, T033
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator`, confirmar RED dos predecessores TDD e dependências.
  - [x] **EXECUTE**: Ler as abas no envio, guardar `abas_disponiveis`, exigir ao menos uma aba e converter só as marcadas.
  - [x] **VERIFY**: Rodar os testes de abas.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [x] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.

T013/T014/T015 com RED, T033 concluída. Planilha de uma aba continua diretamente na fila; multiaba exige confirmação.

4 passed em tests/test_conversion_xlsx_abas.py: espera, confirmação, extração seletiva e rejeição de seleção vazia/inexistente.

<!-- specsfy:evidence {"task":"T034","refs":["US-003","FR-005","NFR-003","NFR-004","AC-013","AC-014","AC-015"],"files":["src/pipeline/conversion/converters/xlsx.py","src/pipeline/service.py","src/app/routers/conversao.py","src/app/repo.py","src/app/tasks.py"],"commands":[{"run":"uv run pytest -q tests/test_conversion_xlsx_abas.py -x","exit":0}]} -->

Melhoria: workbook fechado em finally, bloqueio de linha na confirmação e expiração para documentos aguardando seleção.


- [x] T035 [CODE] [US-005] Criar o critério de baixa qualidade em src/pipeline/conversion/qualidade.py e aplicá-lo no worker — Refs: US-005, FR-007, NFR-005, AC-019, AC-020, AC-025 — Depends: T019, T020, T025, T033
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator`, confirmar RED dos predecessores TDD e dependências.
  - [x] **EXECUTE**: Gerar `AvisoConversao` com código `baixa_qualidade` conforme DEC-006, sem alterar os avisos do PDF.
  - [x] **VERIFY**: Rodar os testes de qualidade e a suíte da SPEC-0033.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [x] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.

T019/T020/T025 com RED ou caracterização; T033 concluída. Preservar avisos específicos de PDF.

3 passed: AC-019/AC-020/AC-025, incluindo PDF e XLSX legados sem alterar suas expectativas de conversão.

<!-- specsfy:evidence {"task":"T035","refs":["US-005","FR-007","NFR-005","AC-019","AC-020","AC-025"],"files":["src/pipeline/conversion/qualidade.py","src/pipeline/service.py","src/app/tasks.py"],"commands":[{"run":"uv run pytest -q tests/test_conversion_reprocessar_ia.py tests/test_router_conversao_fase1.py -k 'ac_019 or ac_020 or ac_025'","exit":0}]} -->

Nenhuma melhoria adicional necessária: função pura mantém o limiar configurável e não aciona IA.


- [x] T036 [CODE] [US-005] Estender `ChatMessage` com partes de imagem e criar o reprocessamento com IA em src/pipeline/providers/contracts.py, src/pipeline/providers/llm/openrouter.py, src/pipeline/conversion/reprocessar_ia.py, src/pipeline/service.py, src/app/routers/conversao.py e src/app/tasks.py — Refs: US-005, FR-008, FR-009, NFR-002, AC-021, AC-022, AC-023, AC-024 — Depends: T021, T022, T023, T024, T035
  - [x] **PREP**: Reconstruir `docs/` com `$specsfy-documentator`, confirmar RED dos predecessores TDD e dependências.
  - [x] **EXECUTE**: Contrato retrocompatível (DEC-007), endpoint 202/403/409, tarefa com falha segura e `.md` anterior preservado; nenhuma chamada sem pedido.
  - [x] **VERIFY**: Rodar os testes de IA e `tests/test_provider_boundaries.py`.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [x] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.

Predecessores T021/T022/T023/T024 com RED, T035 concluída. Especialista LangChain carregado; referências oficiais indexadas. Office depende do LibreOffice existente na imagem.

11 passed nos testes de IA e fronteiras; 3 passed na caracterização multimodal complementar (payload, renderização real de PDF e falha segura). Sem chamada a modelo real. A primeira tentativa complementar citava arquivo de storage inexistente e foi substituída pelo comando correto.

<!-- specsfy:evidence {"task":"T036","refs":["US-005","FR-008","FR-009","NFR-002","AC-021","AC-022","AC-023","AC-024"],"files":["src/pipeline/providers/contracts.py","src/pipeline/providers/llm/openrouter.py","src/pipeline/conversion/reprocessar_ia.py","src/pipeline/service.py","src/app/routers/conversao.py","src/app/tasks.py","src/app/storage.py","tests/test_conversion_multimodal.py"],"commands":[{"run":"uv run pytest -q tests/test_conversion_reprocessar_ia.py tests/test_provider_boundaries.py -x","exit":0},{"run":"uv run pytest -q tests/test_conversion_multimodal.py","exit":0}]} -->

Melhorias: gravação local atômica, parser de HTML sem recursos externos antes da renderização e tracing externo desabilitado durante o grafo. Falhas de LibreOffice/modelo mantêm o arquivo anterior.


- [x] T037 [DOC] Registrar `beautifulsoup4` e `markdownify` em pyproject.toml, .specsfy/STACK.md e .specsfy/PACKAGES.md — Refs: FR-004, NFR-005, AC-010 — Depends: T032
  - [x] **PREP**: Conferir o monitor de contexto e as dependências instaladas.
  - [x] **EXECUTE**: Adicionar as dependências e documentá-las.
  - [x] **VERIFY**: Rodar `monitor_context.mjs --check`.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado.
  - [x] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.

Dependências resolvidas em T032: beautifulsoup4 4.15.0 e markdownify 1.2.3, uv.lock atualizado.

Dependências e lockfile conferidos; monitor CURRENT. STACK.md e PACKAGES.md registram as bibliotecas.

Nenhuma melhoria adicional necessária: preservado o inventário humano fora do bloco gerado.


- [x] T038 [DOC] Registrar as novas colunas de `documentos_conversao` em .specsfy/DATABASE.md — Refs: FR-005, FR-001, NFR-005, AC-027 — Depends: T033
  - [x] **PREP**: Ler a migração criada.
  - [x] **EXECUTE**: Atualizar o quadro de persistência.
  - [x] **VERIFY**: Rodar `monitor_context.mjs --check`.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado.
  - [x] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.

Revisão 0036_conversao_formatos conferida com models e teste AC-027.

DATABASE.md registra as quatro colunas, o estado aguardando_abas, a revisão e a instância de testes; monitor CURRENT.

Nenhuma melhoria adicional necessária: mapa Python mantido manualmente, conforme regra local.


**Checkpoint**: cada história funciona pela API sem a interface.

#### Fase de interface

- [x] T039 [CODE] [US-001] Criar `EntradaEnderecos` e as abas Arquivos e Endereço em frontend/src/features/conversao/EntradaEnderecos.tsx e frontend/src/features/conversao/ConversaoSheet.tsx — Refs: US-001, FR-001, FR-002, NFR-004, AC-001, AC-029 — Depends: T029, T033
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components`, ler `INTERFACE.md` e `DESIGNSYSTEM.MD` e reconstruir `docs/` com `$specsfy-documentator`.
  - [x] **EXECUTE**: Implementar as abas com `Tabs`, campo e lista de URLs, aceitar `.html` e exibir erros em `role=alert`.
  - [x] **VERIFY**: Rodar `npm run test:tdd` e exercitar teclado e envio.
  - [x] **VISUAL**: Conferir 375 px e desktop, estados vazio, erro, carregando, texto curto e longo, bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD`.
  - [x] **EVIDENCE**: Registrar arquivos, comando e resultado da interação.
  - [x] **IMPROVE**: Aplicar melhoria de interface ou justificar nenhuma.

T029 com RED, T033 concluída. Skills React UI Components, UI Design, Design System e shadcn/ui carregadas. Reusar Input/Button/Alert/Tabs/Sheet; catálogo de forms e diálogos consultado sem introduzir Headless UI. INTERFACE.md e DESIGNSYSTEM.MD lidos.

Vitest AC-029 passou: teclado e erro associado ao campo. Typecheck passou após a alteração.

Chromium/Playwright, 375×900 e 1280×900; estados inicial e erro de endereço interno. Capturas em /tmp/spec0036-t039-{375,1280}.png; Geist, padding e bordas seguem primitives; largura interna sem overflow horizontal (280/280 e 383/383). Campo e botão empilhados em mobile. Revisão de conteúdo longo/loading seguirá em T043.

<!-- specsfy:evidence {"task":"T039","refs":["US-001","FR-001","FR-002","NFR-004","AC-001","AC-029"],"files":["frontend/src/features/conversao/EntradaEnderecos.tsx","frontend/src/features/conversao/ConversaoSheet.tsx","INTERFACE.md"],"commands":[{"run":"npm run test:tdd -- src/features/conversao/ConversaoFase1.test.tsx -t endereços","exit":0},{"run":"node /tmp/spec0036-browser/visual.cjs","exit":0}]} -->

Melhoria: limites exibidos vêm da API e nomes longos quebram dentro do Sheet; erro ligado ao campo por aria-describedby.


- [x] T040 [CODE] [US-003] Criar `SelecaoAbas` e integrá-la em frontend/src/features/conversao/SelecaoAbas.tsx e frontend/src/features/conversao/PainelLoteConversao.tsx, com o estado `aguardando_abas` em situacao.ts — Refs: US-003, FR-005, NFR-004, AC-013, AC-014, AC-015 — Depends: T015, T034
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components`, ler `INTERFACE.md` e `DESIGNSYSTEM.MD` e reconstruir `docs/` com `$specsfy-documentator`.
  - [x] **EXECUTE**: Lista de `Checkbox` rotulados, todos marcados, Confirmar desabilitado sem seleção.
  - [x] **VERIFY**: Rodar `npm run test:tdd` e exercitar teclado e confirmação.
  - [x] **VISUAL**: Conferir 375 px e desktop, estados vazio, erro, carregando, texto curto e longo, bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD`.
  - [x] **EVIDENCE**: Registrar arquivos, comando e resultado da interação.
  - [x] **IMPROVE**: Aplicar melhoria de interface ou justificar nenhuma.

T015 com RED, T034 concluída. Reusar painel existente e instalar somente a primitive Checkbox shadcn/Base UI na base já confirmada.

2 passed em ConversaoFase1.test.tsx; seleção inicial marcada e confirmação desabilitada sem abas, com alerta acessível.

Chromium 375×900/1280×900, abas marcadas, desmarcadas e título longo; sem overflow (280/280 e 383/383). Capturas /tmp/spec0036-t040-*.png. Ajuste aplicado: leading-5 no rótulo longo, preservando bordas, espaçamento e tokens da base.

<!-- specsfy:evidence {"task":"T040","refs":["US-003","FR-005","NFR-004","AC-013","AC-014","AC-015"],"files":["frontend/src/features/conversao/SelecaoAbas.tsx","frontend/src/features/conversao/PainelLoteConversao.tsx","frontend/src/features/conversao/DataGridLotesConversao.tsx","frontend/src/features/conversao/situacao.ts","frontend/src/components/ui/checkbox.tsx"],"commands":[{"run":"npm run test:tdd -- src/features/conversao/ConversaoFase1.test.tsx","exit":0},{"run":"node /tmp/spec0036-browser/visual-abas.cjs","exit":0}]} -->

Melhoria: fieldset e legend agrupam as opções e a altura de linha mantém legibilidade de nomes extensos.


- [x] T041 [CODE] [US-005] Criar `ReprocessarIaDialog` e a ação Reprocessar em frontend/src/features/conversao/ReprocessarIaDialog.tsx, frontend/src/features/conversao/DataGridLotesConversao.tsx e frontend/src/features/conversao/PainelLoteConversao.tsx — Refs: US-005, FR-008, NFR-002, AC-019, AC-021, AC-024 — Depends: T021, T024, T036
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components`, ler `INTERFACE.md` e `DESIGNSYSTEM.MD` e reconstruir `docs/` com `$specsfy-documentator`.
  - [x] **EXECUTE**: Diálogo que avisa o envio ao provedor, ação oculta para papel de leitura e estado de reprocessando.
  - [x] **VERIFY**: Rodar `npm run test:tdd` e exercitar o diálogo.
  - [x] **VISUAL**: Conferir 375 px e desktop, estados vazio, erro, carregando, texto curto e longo, bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD`.
  - [x] **EVIDENCE**: Registrar arquivos, comando e resultado da interação.
  - [x] **IMPROVE**: Aplicar melhoria de interface ou justificar nenhuma.

T021/T024 com RED, T036 concluída. Reusar Dialog e o padrão de ApagarDocumentoDialog; ação independente na linha e no painel, somente escrita.

3 passed no diálogo após RED: confirmação explícita, cancelamento sem envio e erro seguro. Typecheck passou.

Chromium 375×900 e 1280×900: aviso com nome longo, cancelamento, pending com botões desabilitados e estado Reprocessando com IA. Capturas /tmp/spec0036-t041-*.png. Diálogo respeita padding, raio, bordas, tipografia Geist e disposição vertical mobile; member sem ação.

<!-- specsfy:evidence {"task":"T041","refs":["US-005","FR-008","NFR-002","AC-019","AC-021","AC-024"],"files":["frontend/src/features/conversao/ReprocessarIaDialog.tsx","frontend/src/features/conversao/ReprocessarIaDialog.test.tsx","frontend/src/features/conversao/DataGridLotesConversao.tsx","frontend/src/features/conversao/PainelLoteConversao.tsx","src/app/routers/conversao.py"],"commands":[{"run":"npm run test:tdd -- src/features/conversao/ReprocessarIaDialog.test.tsx","exit":0},{"run":"node /tmp/spec0036-browser/visual-ia.cjs","exit":0}]} -->

Melhoria: ação compartilhada entre lista e painel; erro de transporte preserva diálogo, e situação de reprocessamento é derivada do estado existente sem nova coluna.


- [x] T042 [DOC] [US-001] Registrar blocos novos e alterados em INTERFACE.md — Refs: US-001, US-003, US-005, NFR-004, AC-029 — Depends: T039, T040, T041
  - [x] **PREP**: Listar os arquivos criados e alterados na fase de interface.
  - [x] **EXECUTE**: Registrar finalidade, arquivo, API, estados, consumidores e regra de reaproveitamento.
  - [x] **VERIFY**: Conferir a tabela contra o código.
  - [x] **VISUAL**: Não aplicável: a tarefa só atualiza o mapa de interface.
  - [x] **EVIDENCE**: Registrar a lista conferida.
  - [x] **IMPROVE**: Aplicar melhoria ou justificar nenhuma.

Conferidos quatro blocos de domínio, ação compartilhada, Checkbox e extensões do Sheet, painel e DataGrid.

Mapa conferido contra arquivos e consumidores reais; registro de primitives, APIs, permissões e estados atualizado.

Nenhuma melhoria adicional necessária: registro central preserva componentes existentes e documenta extensões.


#### Fase final — Qualidade

- [x] T043 [TEST] Executar regressão, Ruff, rastreabilidade e revisão de `PROJECT.md` em tests/ e frontend/ — Refs: US-001, US-002, US-003, US-004, US-005, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, NFR-001, NFR-002, NFR-003, NFR-004, NFR-005, AC-025 — Depends: T030, T031, T032, T033, T034, T035, T036, T037, T038, T042
  - [x] **PREP**: Identificar suítes, Ruff e gates.
  - [x] **EXECUTE**: Rodar a suíte Pytest, Ruff, `npm run test:tdd`, `check_traceability.mjs` e `verify_repo.mjs`.
  - [x] **VERIFY**: Confirmar ausência de gaps e a suíte da SPEC-0023 e da SPEC-0033, com a exceção de FR-006 registrada em DEC-009.
  - [x] **VISUAL**: Repassar a conferência visual final da tela de Conversão em 375 px e desktop: bordas, espaçamentos, margens, padding e tipografia.
  - [x] **EVIDENCE**: Registrar contagens e comandos finais; revisar `PROJECT.md` ou justificar ausência de impacto.
  - [x] **IMPROVE**: Registrar retrospectiva do processo.

Suítes Python/Node, Ruff, lint, tipos, build, rastreabilidade e revisão visual identificados. Regressão Python inicial: 663 passed, 1 skipped, 4 falhas a reconciliar (snapshots históricos, Ruff e marcador português preexistente na spec). Não atribuídas como falhas preexistentes do código sem prova.

Regressão completa, Ruff, Vitest, lint, tipos, build, rastreabilidade, revisão visual e auditoria global executados. Documentação reconstruída e check aprovado; PROJECT.md revisado e atualizado.

Fatia: 706 Pytest passed (1 skip externo anterior), 245 Vitest passed; Ruff/lint/tipos/build aprovados; rastreabilidade completa 48/48 e QA Passed. Verificador global: 7 falhas históricas reproduzidas em HEAD, registradas em FIND-ARCH-002; nenhuma atribuída como aprovada.

Build de produção revisado em 375/1280 px, 200% e emulação 400%; overflow horizontal ausente, diálogo limitado à janela com scroll interno (top 16, bottom 209 em altura 225), controles e rótulos acessíveis, erros/seleção/IA/pending/member conferidos. Capturas em research/.

<!-- specsfy:evidence {"task":"T043","refs":["US-001","US-002","US-003","US-004","US-005","FR-001","FR-002","FR-003","FR-004","FR-005","FR-006","FR-007","FR-008","FR-009","NFR-001","NFR-002","NFR-003","NFR-004","NFR-005","AC-025"],"files":["tests/test_conversion_http_transport.py","tests/test_conversion_multimodal.py","docs/conversao-fase1.md","PROJECT.md","specs/completed/0036-fase-1-receber-e-converter-formatos/research/pytest-completo.log","specs/completed/0036-fase-1-receber-e-converter-formatos/research/vitest-completo.log"],"commands":[{"run":"uv run --with pytest-xdist pytest -q -n 4 -x","exit":0},{"run":"uv run ruff check","exit":0},{"run":"npm run test:tdd","exit":0},{"run":"npm run lint","exit":0},{"run":"npm run typecheck","exit":0},{"run":"npm run build","exit":0}]} -->

Melhorias aplicadas: reserva de bytes por lote de URL, idempotência de IA, qualidade após IA, medição de rede sem importação fria, asserção numérica sem colisão com UUID e diálogo acessível em zoom. Pendências históricas isoladas por prova em HEAD, sem alterar fontes concluídas.


### 15. Ordem de execução

- Caminho crítico: testes RED → T030 (config e tetos) → T031 e T032 (busca e HTML) → T033 (migração e worker) → T034 e T036 (abas e IA) → interface → regressão.
- Tarefas paralelas: os testes da Fase 1 não compartilham estado e podem ser escritos em paralelo; abas (US-003) e qualidade (US-005) dependem só da migração.
- Estratégia de MVP: US-001 e US-003 (P1), depois US-002, US-004 e US-005.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0023 (conversão), SPEC-0033 (OCR e selo "revisar"), SPEC-0002 (contrato do `.md`), SPEC-0030 (envio por coleção).
- `beautifulsoup4` e `markdownify` (DEC-003) e, para IA, provedor de LLM já configurado com suporte a imagem.

#### Riscos

- SSRF por redirecionamento ou DNS → validação do endereço resolvido a cada salto e bloqueio de esquemas diferentes de `http`/`https`.
- Páginas que dependem de scripts chegam vazias → mensagem orientada e envio de `.html` como contingência.
- O contrato atual de chat é só texto → DEC-007 estende o contrato; o modelo configurado pode não aceitar imagem e então o reprocessamento falha com mensagem segura.
- Conteúdo da página pode conter instruções para a IA → o reprocessamento trata o texto como dado e só substitui o `.md`.

#### Suposições

- Página pública é buscada sem cookies, sem login e sem execução de scripts.
- Credenciais embutidas na URL são recusadas.
- Os valores de DEC-004, DEC-005 e DEC-006 são padrões iniciais, reversíveis por configuração.
- A SPEC-0036 é a numeração local; o BACKLOG-0039 permanece como proveniência.
- O aviso de envio ao provedor aparece a cada reprocessamento.

### 17. Decisões

- **DEC-001**: URL e `.html` entram na tela de Conversão existente — evita nova tela; decisão da Pergunta 2 do backlog.
- **DEC-002**: só texto presente no HTML; sem navegador automático — reduz risco e custo (Pergunta 3).
- **DEC-003**: extração de HTML com `beautifulsoup4` e `markdownify`, atrás de `HtmlConverter`; a troca por outra biblioteca não altera contratos. Registrar em `.specsfy/STACK.md` e `.specsfy/PACKAGES.md`. Default reversível.
- **DEC-004**: busca de URL com tempo limite de 10 s, resposta máxima de 5 MB e no máximo 5 redirecionamentos, todos em `ConversaoConfig`. Default reversível.
- **DEC-005**: tetos configuráveis em `ConversaoConfig` com os valores atuais do código (40 MB por arquivo, 50 MB por lote, 50 arquivos) como padrão. O 50 MB / 500 MB do backlog era referência não confirmada e não é adotado; limite de páginas fica fora desta entrega (o OCR já tem `limite_paginas_ocr`). Default reversível por configuração.
- **DEC-006**: "baixa qualidade" fora do PDF é medida por sinais objetivos, sem IA: texto extraído abaixo de `minimo_texto_util` caracteres em um documento ou aba com conteúdo, ou mais de 5% de caracteres de substituição (U+FFFD). Gera `AvisoConversao` com código `baixa_qualidade` e usa o selo "revisar" já existente. Limiares em `ConversaoConfig`. Default reversível.
- **DEC-007**: o contrato neutro é estendido de forma retrocompatível, com `ChatMessage` podendo carregar partes de imagem opcionais; o adapter OpenRouter as traduz. O reprocessamento envia ao provedor as páginas ou imagens do documento. Se o modelo configurado não aceitar imagem, o reprocessamento falha com mensagem segura (AC-023). A extensão do contrato é tarefa própria.
- **DEC-009**: A decisão confirmada no BACKLOG-0039, Pergunta 5, exige recusa apenas do excedente. A exigência anterior de preservar sem alterações o teste da SPEC-0023 que recusava o lote inteiro contradizia FR-006. Atualizar somente esse teste para 201, documentos aceitos e recusados; preservar os demais. Impacto: AC-017, AC-025, NFR-005, T030 e T043. Gates reabertos para reconciliar o aceite; RED original de AC-017 continua válido.

- **DEC-008**: planilha entra em `aguardando_abas` e usa o arquivo já armazenado, sem reenvio — escolha técnica reversível.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/STACK.md` e `.specsfy/PACKAGES.md` registram `beautifulsoup4` e `markdownify`.
- [x] `.specsfy/DATABASE.md` registra as novas colunas de `documentos_conversao`.
- [x] `INTERFACE.md` registra os blocos React novos e alterados.
- [x] `PROJECT.md` revisado (a Fase 1 passa a aceitar HTML e URL) ou justificativa registrada.
