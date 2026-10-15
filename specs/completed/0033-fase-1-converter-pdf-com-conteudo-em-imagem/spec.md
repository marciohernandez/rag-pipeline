# Especificação integrada: Fase 1: converter PDF com conteúdo em imagem (OCR por página)

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0033 |
| Slug | 0033-fase-1-converter-pdf-com-conteudo-em-imagem |
| Status | Complete |
| Effort | 4 |
| Effort updated at | 2026-10-14T13:57:18.859Z |
| Effort rationale | O pymupdf4llm já faz o OCR; a entrega configura idioma e limite, acrescenta avisos, coluna com migration, campo de API e selo na lista. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-14 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

Uma pessoa relatou que um PDF de página web impressa gerou um `.md` só com o parágrafo do topo, perdendo o resto, que é imagem dentro do PDF. A investigação de 2026-10-14 mostrou que o `pymupdf4llm` 1.28.2 já faz OCR com o Tesseract quando ele está instalado, e que o defeito relatado coincide com a ausência do Tesseract naquele momento. Restam lacunas reais: o OCR roda sempre em inglês (`ocr_language="eng"`), então acentos saem errados ("CLÁUSULA" virou "CLXUSULA"); não há limite de páginas; sem Tesseract o PDF sai quase vazio e nada avisa a pessoa; e o campo `avisos` do `ConversionResult` é descartado por `process_conversion_document_task`.

#### Resultado desejado

PDF com páginas em imagem gera um `.md` com o texto reconhecido por OCR em português e inglês (`por+eng`), na ordem do documento, sem alterar o resultado de PDFs de texto. Quando o OCR devolve pouco texto, atinge o limite de páginas ou não pode rodar (Tesseract ausente ou erro na página), o documento continua baixável e aparece com o selo "Revisar" e o motivo na lista de documentos. Idioma, limite de páginas e o mínimo de texto ficam no `config.yaml`.

#### Métricas de sucesso

- 100% das páginas candidatas a OCR (sem texto útil ou com imagem embutida) de um PDF, até o limite configurado, passam por OCR no idioma configurado, medido por AC-001 e AC-003.
- 0 mudança no `.md` de PDFs que só têm texto, medido por AC-002 e pela regressão da SPEC-0023.
- 100% dos documentos com OCR fraco, limite atingido, Tesseract ausente ou falha de OCR aparecem com "Revisar" e motivo, medido por AC-004, AC-005, AC-006 e AC-010.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: O `pymupdf4llm` entrega texto de páginas só de imagem? → Sim, quando o Tesseract está instalado: ele decide o OCR por página, no idioma `eng` por padrão. Sem Tesseract, a página sai sem o texto da imagem. Impacto: o motor de OCR é o próprio `pymupdf4llm`; esta spec não cria um motor novo.
- **R-002**: Os avisos de conversão chegam à pessoa? → Não: `src/app/tasks.py` (`process_conversion_document_task`) ignora `resultado.avisos`, e `DocumentoConversao` não tem coluna para eles. Impacto: o sinal "Revisar" exige coluna nova, campo de API e selo na lista.
- **R-003**: O `pymupdf4llm.to_markdown` é configurável? → Aceita `ocr_language`, `use_ocr`, `force_ocr`, `ocr_dpi`, `ocr_function` e `pages` (`.venv/lib/python3.12/site-packages/pymupdf4llm/__init__.py`, `_layout_to_markdown`). Não expõe a confiança do OCR. Impacto: o idioma e o limite de páginas são controlados chamando a biblioteca página a página com `use_ocr` verdadeiro ou falso; o aviso de baixa confiança sai do escopo.

#### Fontes e contexto consultados

- `specs/inbox/2026-10-14-125322-converter-pdf-cujo-conteudo-esta-em-imagem-ocr-em-paginas-de-pdf.md` (recriada da memória do projeto).
- `specs/backlog/0045-fase-1-converter-pdf-com-conteudo-em-imagem.md` e suas Perguntas 1 a 7.
- `specs/backlog/0039-fase-1-receber-e-converter-formatos.md` (cedeu a detecção de PDF só de imagem a este item).
- `specs/completed/0023-fase-1-recebimento-e-processamento-de-documentos-ate-markdown/spec.md` (FR-003, NFR-001).
- `src/pipeline/conversion/converters/{pdf,image}.py`, `contracts.py`, `factory.py`, `src/app/tasks.py`, `src/app/models.py`, `src/app/routers/conversao.py`, `frontend/src/features/conversao/`, `INTERFACE.md`, `config.yaml`.
- Código instalado do `pymupdf4llm` 1.28.2 e verificação local com PDFs sintéticos (2026-10-14).

#### Documentação consultada

- Código-fonte do `pymupdf4llm` 1.28.2 instalado no ambiente virtual, assinatura de `to_markdown` e `_layout_to_markdown`. Sem documentação externa de rede.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Como tratar este item em relação ao backlog 0039? → **A**: Item novo e separado; o 0039 cede a detecção de PDF só de imagem (Pergunta 1 do backlog, opção 3).
- **Q**: Quando o OCR roda? → **A**: Página a página, só nas que não têm texto útil (Pergunta 2, opção 1).
- **Q**: Como avisar sobre qualidade? → **A**: "Revisar" quando o OCR devolve pouco texto (Pergunta 3, opção 3). A parte "baixa confiança" não é viável porque o `pymupdf4llm` não expõe a confiança; foi retirada (suposição reversível, seção 16).
- **Q**: Como limitar o custo? → **A**: Limite de páginas com OCR por documento, configurável (Pergunta 4, opção 1).
- **Q**: Qual idioma? → **A**: Configurável, padrão `por+eng`, valendo para PDF e imagem (Pergunta 5, opção 3).
- **Q**: Onde se ajusta? → **A**: Só no `config.yaml`; a tela de configurações da conversão vira item futuro (Pergunta 6, opção 3).
- **Q**: Como entregar o sinal "Revisar"? → **A**: Completo: guardar os avisos, devolvê-los na API e mostrar o selo na lista (Pergunta 7, opção 1).
- **Q**: Diante de o `pymupdf4llm` já fazer OCR, o que esta spec entrega? → **A**: Manter o `pymupdf4llm` como motor e entregar só o que falta: idioma, avisos, limite de páginas e a coluna `avisos` (Pergunta 1 da implementação, opção 1).

#### Dúvidas abertas

- Nenhuma. Os valores numéricos ainda sem fonte (limite de páginas, mínimo de texto) foram resolvidos como suposições reversíveis na seção 16.

### 3. Escopo e atores

#### Incluído

- Detecção de página candidata a OCR (sem texto útil ou com imagem embutida) e OCR do `pymupdf4llm` aplicado só nessas páginas, no idioma configurado, juntando o resultado na ordem das páginas.
- Limite de páginas com OCR por documento.
- Avisos estruturados (`ocr_pouco_texto`, `ocr_limite_de_paginas`, `ocr_falhou`) guardados por documento e devolvidos na API.
- Selo "Revisar" com motivo e páginas na lista de documentos de conversão.
- Seção `conversao` no `config.yaml`: idioma, limite de páginas e mínimo de texto; o OCR de imagem passa a usar o mesmo idioma.

#### Fora de escopo

- Motor de OCR próprio e aviso de baixa confiança (a biblioteca não expõe a confiança).
- Tela de configurações da conversão (item futuro, Pergunta 6).
- Reprocessar com IA e demais formatos (backlog 0039); reagrupar sequências (0040).
- Relatório de contradições (0042, 0043).
- Instalar o Tesseract na imagem de produção (backlog 0028); esta spec só registra a dependência e avisa quando ele falta.
- Estado novo de situação: "Revisar" não é uma situação do documento.

#### Atores

- **Owner e admin do Workspace**: enviam documentos para conversão e veem o selo "Revisar" (permissões da SPEC-0023 inalteradas).
- **Member**: apenas lê a lista e o selo.
- **Worker (Procrastinate)**: converte o documento, aplica o OCR e grava os avisos.
- **Tesseract local**: reconhece o texto das páginas pelo `pymupdf4llm`; nada é enviado a serviço externo.

### 4. Princípios e restrições do projeto

- **PR-001**: O conversor de PDF segue o contrato neutro `DocumentConverter` / `ConversionResult`; a aplicação não conhece `pymupdf` nem Tesseract (`src/pipeline/conversion/contracts.py`).
- **PR-002**: O processamento continua assíncrono no Procrastinate já configurado; nenhum mecanismo de fila novo.
- **PR-003**: Documento com aviso continua com situação `concluido` e baixável; o aviso nunca bloqueia nem remove o `.md`.
- **PR-004**: PDFs de exemplo reais têm dados pessoais e não entram no repositório; os testes geram PDFs sintéticos (`tests/_pdfs_spec0033.py`).
- **PR-005**: Nenhum teste usa o banco de desenvolvimento; a coluna nova nasce por migration Alembic e é exercitada só no banco de teste.

### 5. Histórias de usuário

#### US-001 — Ler o texto de páginas em imagem de um PDF (P1)

Como pessoa que prepara documentos para a base, quero que as páginas de um PDF que são imagem sejam lidas por OCR em português e inglês, para receber um `.md` com o conteúdo completo e os acentos corretos.

**Por que P1**: é o defeito relatado; sem isso, PDFs comuns do dia a dia saem quase vazios ou com acentos errados.
**Teste independente**: converter um PDF sintético de duas páginas (uma com texto, outra só com imagem de texto acentuado) e conferir os dois trechos no `.md`.
**Requisitos**: FR-001, FR-002, NFR-001, NFR-002

#### US-002 — Saber quando a leitura precisa de revisão (P2)

Como pessoa que prepara documentos, quero ver um selo "Revisar" com o motivo quando o OCR devolveu pouco texto, atingiu o limite, não pôde rodar ou falhou, para não confiar num `.md` incompleto.

**Por que P2**: protege a qualidade do que alimenta a base, mas só faz sentido depois do OCR estar configurado.
**Teste independente**: converter PDFs que provocam cada aviso e conferir o selo e o motivo na lista.
**Requisitos**: FR-003, FR-004, FR-006, FR-007, FR-008, NFR-003

#### US-003 — Ajustar o OCR sem mudar código (P2)

Como pessoa que administra o sistema, quero definir idioma, limite de páginas e mínimo de texto no `config.yaml`, para adequar o OCR aos documentos da operação.

**Por que P2**: o padrão resolve o caso comum; o ajuste atende exceções.
**Teste independente**: alterar o idioma no `config.yaml` e conferir que PDF e imagem usam o novo valor.
**Requisitos**: FR-004, FR-005

### 6. Cenários BDD de aceite

#### AC-001 — PDF misto lê as páginas em imagem por OCR em português

**Cobre**: US-001, FR-001, FR-002, NFR-001, NFR-002

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @NFR-002 @AC-001
Feature: OCR por página em PDF

  Scenario: Converter um PDF com uma página de texto e uma página só de imagem acentuada
    Given um PDF de duas páginas, a primeira com um parágrafo de texto nativo no topo e a imagem de "CLÁUSULA SEGUNDA" embaixo, e a segunda só com texto nativo
    When o documento é convertido
    Then o Markdown contém o parágrafo nativo da primeira página
    And o Markdown contém "CLÁUSULA SEGUNDA" com a acentuação correta, depois do parágrafo e antes do texto da segunda página
    And nenhuma chamada de rede é feita durante a conversão
```

#### AC-002 — PDF só de texto não passa por OCR

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-002
Feature: OCR por página em PDF

  Scenario: Converter um PDF com texto em todas as páginas
    Given um PDF cujas páginas têm texto nativo suficiente
    When o documento é convertido
    Then o OCR é desligado para todas as páginas
    And o Markdown é idêntico ao que o conversor gerava antes desta spec
    And o documento não recebe aviso
```

#### AC-003 — PDF inteiro em imagem é lido página a página

**Cobre**: US-001, FR-001, FR-002, NFR-001, NFR-003

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @NFR-003 @AC-003
Feature: OCR por página em PDF

  Scenario: Converter um PDF em que todas as páginas são imagem
    Given um PDF de três páginas, todas só com imagem de texto acentuado, dentro do limite de páginas
    When o documento é convertido
    Then o Markdown contém o texto reconhecido das três páginas na ordem original, com acentuação correta
    And a conversão ocorre no worker, sem bloquear a requisição de envio
```

#### AC-004 — OCR com pouco texto marca o documento para revisão

**Cobre**: US-002, FR-003, FR-006, FR-008

```gherkin
@US-002 @FR-003 @FR-006 @FR-008 @AC-004
Feature: Sinal de revisão

  Scenario: OCR devolve pouco texto
    Given um PDF cuja página em imagem não contém texto reconhecível
    When o documento é convertido
    Then o documento termina com situação "concluido"
    And o documento guarda um aviso "ocr_pouco_texto" com a página
    And a lista exibe o selo "Revisar" com o motivo e a página
    And o Markdown continua baixável
```

#### AC-005 — Limite de páginas com OCR

**Cobre**: US-002, FR-003, FR-004, NFR-003

```gherkin
@US-002 @FR-003 @FR-004 @NFR-003 @AC-005
Feature: Limite de páginas com OCR

  Scenario: PDF com mais páginas em imagem que o limite
    Given o limite de páginas com OCR configurado em 2
    And um PDF de cinco páginas, todas só com imagem
    When o documento é convertido
    Then apenas as duas primeiras páginas em imagem passam por OCR
    And o documento guarda o aviso "ocr_limite_de_paginas" com a quantidade de páginas não lidas
    And o selo "Revisar" informa que 3 páginas não foram lidas
```

#### AC-006 — Falha de OCR em uma página não derruba o documento

**Cobre**: US-002, FR-002, FR-003, FR-007, FR-008

```gherkin
@US-002 @FR-002 @FR-003 @FR-007 @FR-008 @AC-006
Feature: Resiliência do OCR

  Scenario: O OCR falha em uma página de um PDF de três páginas
    Given um PDF de três páginas, a segunda só com imagem
    And o OCR levanta um erro ao ler a segunda página
    When o documento é convertido
    Then o documento termina "concluido" com as páginas um e três no Markdown, na ordem
    And o documento guarda o aviso "ocr_falhou" com a página dois
    And a lista exibe "Revisar" com o motivo
```

#### AC-007 — Idioma configurado vale para PDF e imagem

**Cobre**: US-003, FR-004, FR-005

```gherkin
@US-003 @FR-004 @FR-005 @AC-007
Feature: Configuração do OCR

  Scenario: Alterar o idioma no config.yaml
    Given a seção "conversao" do config.yaml com idioma "eng"
    When um PDF com página em imagem e uma imagem JPG são convertidos
    Then o OCR de ambos usa o idioma "eng"
```

#### AC-008 — Sem a seção, valem os padrões

**Cobre**: US-003, FR-004, FR-005

```gherkin
@US-003 @FR-004 @FR-005 @AC-008
Feature: Configuração do OCR

  Scenario: config.yaml sem a seção conversao
    Given um config.yaml sem a seção "conversao"
    When o sistema carrega a configuração da conversão
    Then o idioma é "por+eng"
    And o limite de páginas com OCR é 50
    And o mínimo de texto útil por página é 40 caracteres
```

#### AC-009 — Valor inválido é rejeitado

**Cobre**: US-003, FR-004, FR-005

```gherkin
@US-003 @FR-004 @FR-005 @AC-009
Feature: Configuração do OCR

  Scenario: Limite de páginas inválido
    Given a seção "conversao" com limite de páginas 0 ou negativo, ou idioma vazio
    When o sistema carrega a configuração da conversão
    Then o carregamento falha com mensagem que indica o campo inválido
    And nenhum documento é convertido com valor inválido
```

#### AC-010 — Tesseract ausente

**Cobre**: US-002, FR-006, FR-007, NFR-001

```gherkin
@US-002 @FR-006 @FR-007 @NFR-001 @AC-010
Feature: Resiliência do OCR

  Scenario: O Tesseract não está disponível no ambiente
    Given um PDF com uma página de texto e uma página só de imagem
    And o Tesseract não está instalado
    When o documento é convertido
    Then o documento termina "concluido" com o texto nativo da primeira página
    And o documento guarda o aviso "ocr_falhou" para a segunda página com o motivo "Tesseract indisponível"
```

#### AC-011 — Falha de OCR num documento não afeta o lote

**Cobre**: US-002, FR-007, NFR-002, NFR-003

```gherkin
@US-002 @FR-007 @NFR-002 @NFR-003 @AC-011
Feature: Resiliência do OCR

  Scenario: Lote com dois PDFs, um com falha de OCR
    Given um lote com um PDF cujo OCR falha e um PDF só de texto
    When os dois documentos são convertidos
    Then o PDF só de texto fica "concluido" sem aviso e com o mesmo Markdown de antes
    And o outro fica "concluido" com aviso "ocr_falhou"
    And a situação do lote é "concluido"
```

#### AC-012 — A API devolve os avisos

**Cobre**: US-002, FR-006, FR-007, FR-008

```gherkin
@US-002 @FR-006 @FR-007 @FR-008 @AC-012
Feature: Avisos na API

  Scenario: Consultar um lote com documento que tem aviso
    Given um documento convertido com aviso "ocr_pouco_texto" na página 2
    When a pessoa consulta o lote por GET /api/v1/conversoes/{lote}
    Then o documento traz o campo "avisos" com código, página e mensagem
    And um documento sem aviso traz "avisos" como lista vazia
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O conversor de PDF deve classificar cada página como candidata a OCR quando a camada de texto tem menos de `minimo_texto_util` caracteres não brancos ou quando a página contém ao menos uma imagem embutida, e chamar o `pymupdf4llm` página a página, com OCR ligado (`use_ocr=True`, `ocr_language` do idioma configurado) nas candidatas, e com OCR desligado (`use_ocr=False`) nas demais; a decisão de reconhecer ou não o conteúdo da imagem fica com o `pymupdf4llm`.
- **FR-002**: O Markdown de um PDF deve reunir, na ordem das páginas, o resultado de cada página, sem duplicar o conteúdo de uma página.
- **FR-003**: O conversor deve devolver em `ConversionResult.avisos` um item estruturado (código, página e mensagem) para cada ocorrência de `ocr_pouco_texto` (página com OCR que devolve menos de `minimo_texto_util` caracteres), `ocr_limite_de_paginas` e `ocr_falhou`; OCR com boa leitura não gera aviso.
- **FR-004**: O conversor deve ligar o OCR em no máximo `limite_paginas_ocr` páginas por documento (padrão 50); as demais páginas candidatas não são lidas e geram `ocr_limite_de_paginas` com a quantidade não lida.
- **FR-005**: O sistema deve ler a seção `conversao` do `config.yaml` (`idioma`, `limite_paginas_ocr`, `minimo_texto_util`), validar os valores, aplicar os padrões (`por+eng`, 50, 40) quando ausente e usar o mesmo `idioma` no OCR de PDF e de imagem.
- **FR-006**: O sistema deve guardar os avisos por documento (`documentos_conversao.avisos`, lista JSON, padrão vazia) ao fim da conversão e devolvê-los no campo `avisos` de cada documento da API de conversão.
- **FR-007**: Uma falha de OCR em página, ou a ausência do Tesseract (`shutil.which("tesseract")` vazio), deve produzir `ocr_falhou` com a página e o motivo, sem interromper o documento, o lote nem as demais páginas, que seguem sem OCR; PDF corrompido ou protegido mantém o comportamento atual de falha na conversão.
- **FR-008**: A lista de documentos de conversão deve exibir o selo "Revisar" em cada documento com ao menos um aviso, mostrar o motivo e as páginas ao focar ou abrir o selo, e manter as ações de baixar, reenviar e apagar inalteradas.

#### Não funcionais

- **NFR-001**: O OCR roda localmente; nenhuma chamada de rede ou serviço externo ocorre durante a conversão. **Verificação**: teste que bloqueia `socket` durante a conversão de PDF com página em imagem e confirma o resultado.
- **NFR-002**: A conversão de PDF só de texto permanece idêntica: mesmo Markdown, sem aviso e com o OCR desligado em todas as páginas. **Verificação**: teste de regressão comparando o Markdown com a saída do `pymupdf4llm` para PDFs sintéticos de texto, mais a suíte de conversão da SPEC-0023.
- **NFR-003**: O custo do OCR fica limitado e fora da requisição HTTP: no máximo `limite_paginas_ocr` páginas por documento e execução só no worker. **Verificação**: teste de integração em que `POST /api/v1/conversoes` responde antes da conversão e teste do limite do AC-005.

#### Erros e casos-limite

- Página com texto nativo útil e sem imagem → mantém o texto nativo; OCR desligado.
- Página com texto nativo útil e imagem embutida (página web impressa) → candidata a OCR; texto e imagem entram no Markdown.
- Imagem do PDF sem texto reconhecível → página vazia no Markdown e aviso `ocr_pouco_texto`.
- Configuração com valor inválido → falha clara ao carregar; nenhum documento é convertido com ele.
- Tesseract sem o idioma configurado → `ocr_falhou` com o motivo, sem derrubar o documento.
- Documento apagado ou expirado → os avisos acompanham o registro, sem mudar a retenção da SPEC-0023.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Python 3.12, FastAPI, SQLAlchemy, Alembic em `alembic/versions/`, Procrastinate, pytest. Frontend Next.js com shadcn/ui e ReUI (`INTERFACE.md`).
- `PdfConverter` chama `pymupdf4llm.to_markdown(str(caminho))` uma vez para o documento; o OCR automático da biblioteca usa `ocr_language="eng"`. `ImageConverter` usa `pytesseract` com `idioma="por"` fixo. `ConverterFactory` instancia os conversores sem configuração.
- `process_conversion_document_task` chama `service.convert_document` e descarta `resultado.avisos`.
- Tesseract local com `por`, `eng` e `osd`; `pytesseract`, `pymupdf` e `pymupdf4llm` já estão no ambiente.

#### Arquitetura e módulos

- `src/pipeline/conversion/converters/pdf.py`: abre o PDF com `pymupdf`, mede o texto útil e as imagens embutidas de cada página, chama `pymupdf4llm.to_markdown(..., pages=[i], use_ocr=<bool>, ocr_language=<idioma>)` por página, aplica o limite de páginas com OCR, junta o Markdown na ordem e monta os avisos. Verifica `shutil.which("tesseract")` antes de ligar o OCR. Nenhum módulo de OCR novo.
- `src/pipeline/conversion/contracts.py`: `ConversionResult.avisos` passa de `list[str]` para itens com `codigo`, `pagina` e `mensagem` (dataclass `AvisoConversao`); o aviso `ocr_sem_texto_reconhecido` do `ImageConverter` migra para o mesmo formato.
- `src/pipeline/conversion/config.py` (novo): `ConversaoConfig` (`idioma`, `limite_paginas_ocr`, `minimo_texto_util`) e `carregar_config_conversao(config: dict)` que valida e aplica os padrões.
- `src/pipeline/conversion/factory.py`: injeta a configuração nos conversores de PDF e imagem.
- `config.yaml`: seção `conversao` documentada em português.

#### Migrations

- `alembic/versions/<rev>_documentos_conversao_avisos.py`: `ADD COLUMN avisos JSON NOT NULL DEFAULT '[]'` em `documentos_conversao`. Compatível com linhas existentes; o rollback remove a coluna (nunca executado contra o banco de desenvolvimento nos testes).

#### Models

- `DocumentoConversao.avisos: Mapped[list[dict]]` (JSON, padrão lista vazia) em `src/app/models.py`.

#### Controllers e casos de uso

- `src/app/tasks.py` (`process_conversion_document_task`): grava `documento.avisos` com `resultado.avisos` serializados; em falha, limpa os avisos.
- `src/app/routers/conversao.py` (`_serializar_documento`): inclui `avisos`; sem mudança de autorização.

#### Views e experiência

- `frontend/src/features/conversao/` (detalhes na seção 10).

#### Queries e repositórios

- Nenhuma consulta nova; `avisos` acompanha o documento nas consultas existentes.

#### Jobs e processamento assíncrono

- Mesmo job `process_conversion_document_task`, com o mesmo retry e a mesma idempotência; o reenvio de documento regrava os avisos.

#### Estrutura de arquivos

```text
specs/planned/0033-fase-1-converter-pdf-com-conteudo-em-imagem/
  spec.md
  research/
src/pipeline/conversion/config.py
src/pipeline/conversion/converters/pdf.py
src/pipeline/conversion/converters/image.py
alembic/versions/
tests/test_conversion_pdf_ocr.py
tests/test_conversion_config.py
frontend/src/features/conversao/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| DocumentoConversao | `id` (UUID) | Ganha `avisos`: lista JSON de `{codigo, pagina, mensagem}`; vazia por padrão; só os códigos `ocr_pouco_texto`, `ocr_limite_de_paginas`, `ocr_falhou` e `ocr_sem_texto_reconhecido` | N:1 com LoteConversao (inalterada) |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| DocumentoConversao | processando | conversão termina com avisos | concluido | `avisos` preenchida; situação não muda por causa de aviso |
| DocumentoConversao | processando | conversão falha | falhou | `avisos` vazia |
| DocumentoConversao | falhou | reenvio | fila | `avisos` regravada na nova conversão |

#### Migração e retenção

- Coluna nova com padrão `[]`; documentos antigos ficam sem aviso. Retenção de 7 dias da SPEC-0023 inalterada; os avisos vivem no registro, que é preservado após a purga dos arquivos.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. Mudança pequena: um selo "Revisar" na lista de documentos de conversão já existente. Não cria tela, rota nem item de menu.

#### Stack e convenções de interface

- Next.js (App Router), React, Tailwind, shadcn/ui e ReUI conforme `INTERFACE.md`. A aba "Conversão" de `/workspaces/[id]` consome `DataGridLotesConversao`, `PainelLoteConversao` e `situacao.ts`. Testes de interface em Vitest (`ListaDocumentosConversao.test.tsx`).

#### Telas e responsabilidades

- Aba Conversão do Workspace (`DataGridLotesConversao`): lista uma linha por documento; passa a mostrar o selo "Revisar" junto da situação.
- `PainelLoteConversao` (Sheet do lote): mostra, por documento com aviso, o motivo e as páginas.

#### Fluxo de informação e navegação

- Nada muda na chegada: aba Conversão do Workspace. A pessoa vê o selo na lista, abre o lote pela linha (clique ou teclado) e lê o motivo no painel; baixa o `.md` normalmente.

#### Menus e navegação principal

- Sem item de menu novo; o acesso continua pela aba Conversão em `/workspaces/[id]`.

#### Formulários e ações

- Nenhum formulário novo. As ações Baixar, Reenviar e Apagar permanecem independentes e inalteradas; o selo não é uma ação.

#### Composição e disposição

- O selo ocupa a coluna Situação, ao lado do `Badge` existente, e quebra para a linha de baixo em 375 px sem causar overflow horizontal. O motivo aparece em `Tooltip` ou `Popover` do selo e na lista de avisos do painel.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Aba Conversão | `DataGridLotesConversao` | Exibir o selo ao lado da situação | `frontend/src/features/conversao/DataGridLotesConversao.tsx` | `Badge` (variante `outline`) | shadcn/ui | Existente; estendido |
| Aba Conversão | `SeloRevisarDocumento` | Selo "Revisar" com motivo e páginas, acessível por teclado | `frontend/src/features/conversao/SeloRevisarDocumento.tsx` | `Badge` + `Tooltip` | shadcn/ui; próprio | Novo; reaproveitado pela grade e pelo painel |
| Sheet do lote | `PainelLoteConversao` | Listar o motivo e as páginas por documento | `frontend/src/features/conversao/PainelLoteConversao.tsx` | `Badge`, `Alert` | shadcn/ui | Existente; estendido |
| Ambas | `situacao.ts` | Rótulos dos códigos de aviso em português | `frontend/src/features/conversao/situacao.ts` | n/a | próprio | Existente; estendido |

- shadcn/ui fornece `Badge`, `Tooltip` e `Alert`; nenhuma composição ReUI nova é necessária porque a grade `DataGridLotesConversao` já a usa. `INTERFACE.md` registra `SeloRevisarDocumento` e a extensão dos blocos existentes.

#### Estados e acessibilidade

- Sem aviso: nada novo. Com aviso: selo "Revisar" visível; o motivo aparece por foco ou toque e fica disponível no painel do lote. O selo tem nome acessível ("Revisar: <motivo>"), é alcançável por Tab, e o aviso não depende só de cor. Loading, vazio, erro e permissão seguem a SPEC-0023.

#### Contrato CRUD

- Não há CRUD novo. A lista de documentos mantém o `PageHeader` único da aba, o `DataGrid` em largura total, a coluna `ID` visível, a linha inteira como link para o detalhe e as ações independentes de editar (reenviar) e apagar da SPEC-0023, com apagar confirmando a consequência. O selo "Revisar" não altera esse contrato.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre durante a implementação, mesmo sem pedido da pessoa, e confere bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra) do selo contra o `Badge` existente, em 375 px e em desktop, com motivo curto e longo, nos temas claro e escuro e com foco por teclado. Forma, viewport, estados, achados e ajustes são registrados nas tarefas de interface.

#### APIs expostas

- `GET /api/v1/conversoes` e `GET /api/v1/conversoes/{lote}`: cada documento ganha `avisos: [{codigo, pagina, mensagem}]` (lista vazia quando não há). Mudança aditiva, sem novo versionamento, mesma autenticação e papéis da SPEC-0023.

#### APIs externas utilizadas

- Nenhuma.

#### Documentação das APIs consultadas

- `pymupdf4llm.to_markdown` 1.28.2 (`pages`, `use_ocr`, `ocr_language`), conferido no código instalado.

#### Eventos e outros contratos

- Contrato interno: `ConversionResult.avisos: list[AvisoConversao]`; `config.yaml` seção `conversao` com `idioma`, `limite_paginas_ocr`, `minimo_texto_util`.

### 11. Estratégia TDD

- **Unidade**: `PdfConverter` (decisão de OCR por página, limite, junção em ordem, falhas) e o carregamento da seção `conversao`, com PDFs sintéticos gerados no teste (`tests/_pdfs_spec0033.py`); o Tesseract real lê as imagens e um espião em `pymupdf4llm.to_markdown` confere `use_ocr` e `ocr_language` por página.
- **Integração/contrato**: `process_conversion_document_task` grava `avisos`; o router devolve `avisos`; o OCR real do Tesseract em um PDF sintético com a imagem de um texto simples.
- **BDD/aceite**: os cenários AC-001 a AC-012 orientam o desenho dos casos TDD.
- **Runner TDD**: Pytest, já estabelecido no projeto; Vitest para o selo no frontend.
- **E2E**: Não aplicável; o fluxo é coberto por integração do router e da tarefa.
- **Verificação manual**: revisão visual do selo nos viewports e temas, inevitável para bordas, espaçamento e tipografia.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, NFR-001, NFR-002, AC-001 | AC-001 na seção 6 | `tests/test_conversion_pdf_ocr.py::test_spec_0033_ac_001_pdf_misto_le_pagina_em_imagem` | RED observado em 2026-10-14: o Markdown traz "Clausula" sem acentos: o OCR automático do pymupdf4llm roda em `eng`. | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-001, FR-001, NFR-002, AC-002 | AC-002 na seção 6 | `tests/test_conversion_pdf_ocr.py::test_spec_0033_ac_002_pdf_de_texto_nao_passa_por_ocr` | RED observado em 2026-10-14: a conversão chama o pymupdf4llm sem `use_ocr=False`; o conversor não controla o OCR. | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-001, FR-001, FR-002, NFR-001, NFR-003, AC-003 | AC-003 na seção 6 | `tests/test_conversion_pdf_ocr.py::test_spec_0033_ac_003_pdf_inteiro_em_imagem_na_ordem` e `tests/test_router_conversao.py::test_spec_0033_ac_003_envio_responde_antes_da_conversao` | RED observado em 2026-10-14: o texto sai sem acentos ("Primeira clausula: acao"): idioma `eng` fixo. | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-002, FR-003, FR-006, AC-004 | AC-004 na seção 6 | `tests/test_conversion_pdf_ocr.py::test_spec_0033_ac_004_ocr_sem_texto_gera_aviso`, `tests/test_task_process_conversion_document.py::test_spec_0033_ac_004_grava_avisos_do_documento` e `frontend/src/features/conversao/SeloRevisarDocumento.test.tsx::spec_0033_ac_004_exibe_selo_revisar` | RED observado em 2026-10-14: `avisos` vem vazio; `ocr_pouco_texto` não existe. No teste da tarefa, `DocumentoConversao` não tem o atributo `avisos`. | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-002, FR-003, FR-004, NFR-003, AC-005 | AC-005 na seção 6 | `tests/test_conversion_pdf_ocr.py::test_spec_0033_ac_005_limite_de_paginas_com_ocr` | RED observado em 2026-10-14: `PdfConverter` não aceita `config` e o módulo `src/pipeline/conversion/config.py` não existe. | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-002, FR-002, FR-003, FR-007, AC-006 | AC-006 na seção 6 | `tests/test_conversion_pdf_ocr.py::test_spec_0033_ac_006_falha_de_ocr_em_pagina` | RED observado em 2026-10-14: nenhum aviso `ocr_falhou` é produzido; a conversão não passa por página. | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-003, FR-005, AC-007 | AC-007 na seção 6 | `tests/test_conversion_config.py::test_spec_0033_ac_007_idioma_vale_para_pdf_e_imagem` | RED observado em 2026-10-14: o módulo `src/pipeline/conversion/config.py` não existe (FR-005). | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-003, FR-004, FR-005, AC-008 | AC-008 na seção 6 | `tests/test_conversion_config.py::test_spec_0033_ac_008_padroes_sem_a_secao` | RED observado em 2026-10-14: o módulo `src/pipeline/conversion/config.py` não existe (FR-005). | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-003, FR-004, FR-005, AC-009 | AC-009 na seção 6 | `tests/test_conversion_config.py::test_spec_0033_ac_009_rejeita_valor_invalido` | RED observado em 2026-10-14: o módulo `src/pipeline/conversion/config.py` não existe (FR-005); 4 variações inválidas parametrizadas. | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-002, FR-006, FR-007, NFR-001, AC-010 | AC-010 na seção 6 | `tests/test_conversion_pdf_ocr.py::test_spec_0033_ac_010_tesseract_ausente` | RED observado em 2026-10-14: nenhum aviso `ocr_falhou` com "Tesseract indisponível"; a ausência do Tesseract não é tratada. | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-002, FR-007, NFR-002, NFR-003, AC-011 | AC-011 na seção 6 | `tests/test_task_process_conversion_document.py::test_spec_0033_ac_011_falha_de_ocr_nao_afeta_o_lote` | RED observado em 2026-10-14: `DocumentoConversao` não tem o atributo `avisos` (FR-006). | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |
| US-002, FR-006, FR-007, AC-012 | AC-012 na seção 6 | `tests/test_router_conversao.py::test_spec_0033_ac_012_api_devolve_avisos` e `frontend/src/features/conversao/ListaDocumentosConversao.test.tsx::spec_0033_ac_012_exibe_motivo_do_aviso` | RED observado em 2026-10-14: `KeyError: 'avisos'`: a API não devolve o campo. | GREEN: suítes focais de PDF (9), configuração/imagem (8), worker/API (25) e interface (11) aprovadas. | Regressão da SPEC-0023 aprovada; PDFs de texto comparados literalmente; revisão em T019/T020. |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_001` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-001 | AC-002 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_002` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-001 | AC-003 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_003` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-002 | AC-001 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_001` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-002 | AC-003 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_003` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-002 | AC-006 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_006` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-003 | AC-004 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_004` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-003 | AC-005 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_005` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-003 | AC-006 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_006` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-004 | AC-005 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_005` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-004 | AC-008 | Unidade | `uv run pytest tests/test_conversion_config.py -k ac_008` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-004 | AC-009 | Unidade | `uv run pytest tests/test_conversion_config.py -k ac_009` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-005 | AC-007 | Integração | `uv run pytest tests/test_conversion_config.py -k ac_007` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-005 | AC-008 | Unidade | `uv run pytest tests/test_conversion_config.py -k ac_008` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-005 | AC-009 | Unidade | `uv run pytest tests/test_conversion_config.py -k ac_009` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-006 | AC-004 | Integração | `uv run pytest tests/test_task_process_conversion_document.py -k ac_004` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-006 | AC-010 | Integração | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_010` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-006 | AC-012 | Integração | `uv run pytest tests/test_router_conversao.py -k ac_012` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-007 | AC-006 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_006` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-007 | AC-010 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_010` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-007 | AC-011 | Integração | `uv run pytest tests/test_task_process_conversion_document.py -k ac_011` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-008 | AC-004 | Interface | `npm --prefix frontend run test -- SeloRevisarDocumento` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-008 | AC-006 | Interface | `npm --prefix frontend run test -- SeloRevisarDocumento` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| FR-008 | AC-012 | Interface | `npm --prefix frontend run test -- ListaDocumentosConversao` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| NFR-001 | AC-001 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_001` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| NFR-001 | AC-003 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_003` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| NFR-001 | AC-010 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_010` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| NFR-002 | AC-001 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_001` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| NFR-002 | AC-002 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_002` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| NFR-002 | AC-011 | Integração | `uv run pytest tests/test_task_process_conversion_document.py -k ac_011` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| NFR-003 | AC-003 | Integração | `uv run pytest tests/test_router_conversao.py -k ac_003` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| NFR-003 | AC-005 | Unidade | `uv run pytest tests/test_conversion_pdf_ocr.py -k ac_005` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |
| NFR-003 | AC-011 | Integração | `uv run pytest tests/test_task_process_conversion_document.py -k ac_011` | Passed — suítes focais aprovadas em T014–T020; 11 testes de interface e revisão visual em 375/1280 px, claro/escuro. |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed (2026-10-14, revalidado após a DEC-006)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/planned/0033-fase-1-converter-pdf-com-conteudo-em-imagem/spec.md`
- **Achados**: 0 BLOCKER, 1 WARNING resolvido e 1 NOTE. Cobertura: 3 US, 8 FR, 3 NFR e 12 AC, cada US, FR e NFR com ao menos 3 AC.
  - WARNING (resolvido): o FR-001 só ligava o OCR em páginas sem texto útil e perderia a imagem de uma página com parágrafo e imagem (o caso relatado); passou a incluir páginas com imagem embutida e o AC-001 cobre o caso.
  - NOTE: o mínimo de 40 caracteres e o limite de 50 páginas são suposições reversíveis; calibrar com PDFs reais fora do repositório.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-14)
- **Replanejamento**: T014 verifica AC-008 e AC-009 sem antecipar AC-007; T015 depende de T016 e inclui a injeção da configuração do entrypoint até a factory. Predecessores TDD existentes preservados, com RED registrado; `validate_tasks.mjs --allow-draft` aprovado (24 tarefas, 26 IDs).
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/planned/0033-fase-1-converter-pdf-com-conteudo-em-imagem/spec.md`
- **Achados**: 24 tarefas (14 TDD, 7 de código, 3 de documentação), cobertura de 26 de 26 IDs. T001 a T013 em RED válido: 17 falhas de backend e 4 de frontend, todas por comportamento ausente (idioma `eng`, ausência de `avisos`, módulo `config.py` e `SeloRevisarDocumento`). Nenhum predecessor TDD de tarefa de código está aberto.

#### Gate do Ato III — Entrega

- **Resultado**: Passed (2026-10-14)
- **Suíte final**: `uv run pytest -q`: exit 0, 586 passed, 1 skipped preexistente (SPEC-0014) e 2 avisos de depreciação, 883s. Nenhum teste da SPEC-0033 pulado. Lint, tipos, build, QA, rastreabilidade e evidência atual aprovados; 24/24 tarefas e 144/144 itens concluídos.
- **Verificações focais**: PDF/estrutura: 9 passed; configuração/imagem: 8 passed; worker/API: 25 passed; migration em schemas isolados: 6 passed; fronteiras/documentação: 21 passed; interface da conversão: 11 passed. AC-002 também foi repetido com comparação literal do Markdown (1 passed).
- **Frontend completo**: `npm --prefix frontend run test:tdd`: 236 passed em 58 arquivos. `npm --prefix frontend run lint`, `npm --prefix frontend run typecheck` e `npm --prefix frontend run build`: exit 0. Build final sem a página temporária de revisão.
- **Revisão visual**: Playwright sobre os componentes e CSS locais em 375×900 e 1280×900, temas claro/escuro, motivo curto/longo, foco, toque, Enter na linha e no selo. Sem overflow global; tabela com rolagem interna preservada. Bordas, espaçamentos, margens, padding e tipografia conferidos; imagens e métricas locais em `/tmp/spec0033-visual`. Harness temporário removido depois da conferência.
- **Regressão do backend**: execução intermediária de `uv run pytest -q`: 584 passed, 2 failed por `psycopg.errors.DiskFull` na memória compartilhada do PostgreSQL e 1 skipped preexistente. A fixture de migrations agora desliga paralelismo somente na sessão isolada, preservando schemas; os 6 testes de migration e a suíte completa final passaram depois da correção.
- **Falhas anteriores**: a suíte base apresentou 19 falhas (RED da SPEC-0033, lint dos testes e marcadores portugueses na spec); lint e marcadores corrigidos. O único teste pulado é a comparação paga da SPEC-0014, condicionada a `RUN_SPEC0014_REAL=1` e chave externa; nenhum cenário da SPEC-0033 é pulado.
- **Auditoria global**: `verify_repo.mjs . --boundary local --timeout-seconds 300 --max-output-bytes 65536` apontou gaps legados de rastreabilidade nas SPEC-0012/0013/0019/0023/0026, índices de pesquisa nas SPEC-0023/0030 e a SPEC-0031 em Draft. Gaps de marcadores nas SPEC-0012/0013/0019/0026 também aparecem no snapshot HEAD anterior em `/tmp/spec0033-baseline`; a SPEC-0033 passa em definição, plano, interface, evidência estrita, 26/26 IDs e QA dos 12 AC. A auditoria global não é declarada verde.
- **Documentação e contexto**: `build_documentation.mjs --project . --check` aprovado e `monitor_context.mjs --project . --check`: CURRENT; DATABASE.md, PROJECT.md, INTERFACE.md e contrato da fachada atualizados. Sem pacote novo nem alteração em stack/regras duráveis.
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/planned/0033-fase-1-converter-pdf-com-conteudo-em-imagem/spec.md .`
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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 o caso `test_spec_0033_ac_001_pdf_misto_le_pagina_em_imagem` falhando em tests/test_conversion_pdf_ocr.py — Refs: US-001, FR-001, FR-002, NFR-001, NFR-002, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): o Markdown traz "Clausula" sem acentos: o OCR automático do pymupdf4llm roda em `eng`.
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 o caso `test_spec_0033_ac_002_pdf_de_texto_nao_passa_por_ocr` falhando em tests/test_conversion_pdf_ocr.py — Refs: US-001, FR-001, NFR-002, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): a conversão chama o pymupdf4llm sem `use_ocr=False`; o conversor não controla o OCR.
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 os casos `test_spec_0033_ac_003_pdf_inteiro_em_imagem_na_ordem` e `test_spec_0033_ac_003_envio_responde_antes_da_conversao` falhando em tests/test_conversion_pdf_ocr.py e tests/test_router_conversao.py — Refs: US-001, FR-001, FR-002, NFR-001, NFR-003, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): o texto sai sem acentos ("Primeira clausula: acao"): idioma `eng` fixo.
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T004 [TEST] [TDD] [US-002] Derivar do AC-004 os casos `test_spec_0033_ac_004_ocr_fraco_gera_aviso` e `test_spec_0033_ac_004_grava_avisos_do_documento` falhando em tests/test_conversion_pdf_ocr.py e tests/test_task_process_conversion_document.py — Refs: US-002, FR-003, FR-006, FR-008, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): `avisos` vem vazio; `ocr_pouco_texto` não existe. No teste da tarefa, `DocumentoConversao` não tem o atributo `avisos`.
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-005 o caso `test_spec_0033_ac_005_limite_de_paginas_com_ocr` falhando em tests/test_conversion_pdf_ocr.py — Refs: US-002, FR-003, FR-004, NFR-003, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): `PdfConverter` não aceita `config` e o módulo `src/pipeline/conversion/config.py` não existe.
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 o caso `test_spec_0033_ac_006_falha_de_ocr_em_pagina` falhando em tests/test_conversion_pdf_ocr.py — Refs: US-002, FR-002, FR-003, FR-007, FR-008, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): nenhum aviso `ocr_falhou` é produzido; a conversão não passa por página.
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T007 [TEST] [TDD] [US-003] Derivar do AC-007 o caso `test_spec_0033_ac_007_idioma_vale_para_pdf_e_imagem` falhando em tests/test_conversion_config.py — Refs: US-003, FR-005, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): o módulo `src/pipeline/conversion/config.py` não existe (FR-005).
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T008 [TEST] [TDD] [US-003] Derivar do AC-008 o caso `test_spec_0033_ac_008_padroes_sem_a_secao` falhando em tests/test_conversion_config.py — Refs: US-003, FR-004, FR-005, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): o módulo `src/pipeline/conversion/config.py` não existe (FR-005).
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-009 o caso `test_spec_0033_ac_009_rejeita_valor_invalido` falhando em tests/test_conversion_config.py — Refs: US-003, FR-004, FR-005, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): o módulo `src/pipeline/conversion/config.py` não existe (FR-005); 4 variações inválidas parametrizadas.
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T010 [TEST] [TDD] [US-002] Derivar do AC-010 o caso `test_spec_0033_ac_010_tesseract_ausente` falhando em tests/test_conversion_pdf_ocr.py — Refs: US-002, FR-006, FR-007, NFR-001, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): nenhum aviso `ocr_falhou` com "Tesseract indisponível"; a ausência do Tesseract não é tratada.
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T011 [TEST] [TDD] [US-002] Derivar do AC-011 o caso `test_spec_0033_ac_011_falha_de_ocr_nao_afeta_o_lote` falhando em tests/test_task_process_conversion_document.py — Refs: US-002, FR-007, NFR-002, NFR-003, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): `DocumentoConversao` não tem o atributo `avisos` (FR-006).
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T012 [TEST] [TDD] [US-002] Derivar do AC-012 o caso `test_spec_0033_ac_012_api_devolve_avisos` falhando em tests/test_router_conversao.py — Refs: US-002, FR-006, FR-007, FR-008, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012 na seção 6 e confirmar regra, IDs e nível de teste.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0033`, usando PDF sintético gerado no teste e sem criar ou executar `.feature`.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `.venv/bin/python -m pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_config.py tests/test_task_process_conversion_document.py tests/test_router_conversao.py -k 0033 -q` (17 failed): `KeyError: 'avisos'`: a API não devolve o campo.
  - [x] **IMPROVE**: Cobertura revisada; PDFs sintéticos de `tests/_pdfs_spec0033.py`, sem dados reais.

- [x] T013 [TEST] [TDD] [US-002] Derivar do AC-004 o caso `spec_0033_ac_004_exibe_selo_revisar` falhando em frontend/src/features/conversao/SeloRevisarDocumento.test.tsx — Refs: US-002, FR-008, AC-004, AC-006, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-004, AC-006 e AC-012 e conferir os componentes atuais em `ListaDocumentosConversao.test.tsx`.
  - [x] **EXECUTE**: Escrever os casos de interface com marcador `// SPECSFY: SPEC-0033`: selo com motivo e página, motivo longo, documento sem aviso, foco por teclado e nome acessível; mais `spec_0033_ac_012_exibe_motivo_do_aviso` em ListaDocumentosConversao.test.tsx.
  - [x] **VERIFY**: RED válido observado: falha pelo comportamento ausente, não por sintaxe ou ambiente.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de componente; a conferência visual ocorre nas tarefas da fase de interface.
  - [x] **EVIDENCE**: RED observado em 2026-10-14 com `cd frontend && npx vitest run src/features/conversao` (4 failed, 7 passed): `SeloRevisarDocumento` ainda não existe e a lista não exibe o selo.
  - [x] **IMPROVE**: Cobertura revisada; os 7 testes preexistentes da SPEC-0023 continuam verdes.

#### Fase 2 — Fundação: contrato de avisos e configuração (US-003, P2)

**Objetivo**: avisos estruturados e seção `conversao` validada, base de PDF e imagem.
**Teste independente**: `uv run pytest tests/test_conversion_config.py -q` passa.

- [x] T014 [CODE] [US-003] Criar `AvisoConversao` em src/pipeline/conversion/contracts.py e o carregador validado da seção `conversao` em src/pipeline/conversion/config.py, com a seção documentada em config.yaml — Refs: US-003, FR-003, FR-004, FR-005, AC-007, AC-008, AC-009 — Depends: T007, T008, T009
  - [x] **PREP**: Contrato, configuração e RED de T007–T009 conferidos; documentação reconstruída no setup.
  - [x] **EXECUTE**: AvisoConversao e ConversaoConfig criados; aviso da imagem estruturado; padrões em config.yaml e config.example.yaml. PROJECT.md revisado: fundação interna ainda sem capacidade nova disponível; narrativa será atualizada em T023.
  - [x] **VERIFY**: 7 passed, 1 deselected: uv run pytest tests/test_conversion_config.py tests/test_conversion_image_ocr.py -k "not ac_007" -q (SAFE).
  - [x] **VISUAL**: Não aplicável: contrato e carregamento de configuração não renderizam interface.
  - [x] **EVIDENCE**: GREEN de AC-008/AC-009 e regressão da imagem (7 passed); configuração documentada no exemplo versionado e no arquivo local ignorado; build_documentation.mjs --check aprovado.
  - [x] **IMPROVE**: Validação também rejeita booleanos, decimais e seção não estruturada, evitando configurações ambíguas.
  <!-- specsfy:evidence {"task":"T014","refs":["US-003","FR-003","FR-004","FR-005","AC-007","AC-008","AC-009"],"files":["src/pipeline/conversion/contracts.py","src/pipeline/conversion/config.py","config.example.yaml"],"commands":[{"run":"uv run pytest tests/test_conversion_config.py tests/test_conversion_image_ocr.py -k 'not ac_007' -q","exit":0}]} -->

- [x] T015 [CODE] [US-003] Fazer o `ImageConverter` e a `ConverterFactory` usarem o idioma da configuração em src/pipeline/conversion/converters/image.py e src/pipeline/conversion/factory.py, injetado pela fachada src/pipeline/service.py e pelo entrypoint src/app/main.py via src/app/settings.py e src/app/tasks.py — Refs: US-003, FR-005, AC-007 — Depends: T007, T014, T016
  - [x] **PREP**: T014 e T016 concluídas; RED de AC-007 registrado; factory e facade lidas; config.yaml será resolvido no entrypoint e injetado sem violar a fronteira app/pipeline.
  - [x] **EXECUTE**: Idioma injetado por AppSettings e facade até PDF/imagem; config.yaml é lido no entrypoint; contratos e imports preservados; documentação reconstruída após a alteração.
  - [x] **VERIFY**: 8 passed: uv run pytest tests/test_conversion_config.py tests/test_conversion_image_ocr.py -q (SAFE), incluindo AC-007.
  - [x] **VISUAL**: Não aplicável: configuração e composição de conversores sem interface renderizada.
  - [x] **EVIDENCE**: GREEN de AC-007/AC-008/AC-009 e regressão de imagem. PROJECT.md revisado: configuração documentada; sem mudança adicional de finalidade.
  - [x] **IMPROVE**: Preservada a opção idioma do ImageConverter para compatibilidade; corrigida mensagem de formato desconhecido da factory, que unia lista e conjunto.
  <!-- specsfy:evidence {"task":"T015","refs":["US-003","FR-005","AC-007"],"files":["src/pipeline/conversion/converters/image.py","src/pipeline/conversion/factory.py","src/pipeline/service.py","src/app/main.py","src/app/settings.py","src/app/tasks.py"],"commands":[{"run":"uv run pytest tests/test_conversion_config.py tests/test_conversion_image_ocr.py -q","exit":0}]} -->

**Checkpoint**: alterar `idioma` no `config.yaml` muda o OCR da imagem; a seção ausente usa os padrões; valor inválido falha com mensagem.

#### Fase 3 — US-001 Ler o texto de páginas em imagem de um PDF (P1)

**Objetivo**: PDF com páginas em imagem gera `.md` completo, sem alterar PDFs de texto.
**Teste independente**: `uv run pytest tests/test_conversion_pdf_ocr.py -q` passa.

- [x] T016 [CODE] [US-001] Reescrever o `PdfConverter` em src/pipeline/conversion/converters/pdf.py para chamar o `pymupdf4llm` página a página com OCR só nas páginas candidatas, idioma configurado, limite de páginas, avisos e tolerância a falha — Refs: US-001, US-002, FR-001, FR-002, FR-003, FR-004, FR-007, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-010 — Depends: T001, T002, T003, T004, T005, T006, T010, T014
  - [x] **PREP**: RED de T001–T006/T010 conferido; assinatura instalada aceita pages, use_ocr e ocr_language; documentação atual e configuração concluída.
  - [x] **EXECUTE**: OCR por página implementado com idioma e limite; fallback sem OCR em falha preserva texto nativo. PROJECT.md registra a capacidade; docs/application.md descreve o algoritmo, reconstrução documental executada.
  - [x] **VERIFY**: 9 passed: uv run pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_structure.py -q; acentos, ordem, limite, falha, ausência do Tesseract e texto nativo aprovados.
  - [x] **VISUAL**: Não aplicável: conversor de PDF sem interface renderizada.
  - [x] **EVIDENCE**: GREEN de AC-001–AC-006/AC-010; PDFs sintéticos de boa leitura ajustados acima de 40 caracteres e imagem com quebra de linha para impedir recorte. PROJECT.md atualizado; documentação reconstruída e check aprovado.
  - [x] **IMPROVE**: Fallback sem OCR preserva a camada nativa da página que falhou, sem incluir exceções internas nas mensagens.
  <!-- specsfy:evidence {"task":"T016","refs":["US-001","US-002","FR-001","FR-002","FR-003","FR-004","FR-007","NFR-001","NFR-002","NFR-003","AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-010"],"files":["src/pipeline/conversion/converters/pdf.py"],"commands":[{"run":"uv run pytest tests/test_conversion_pdf_ocr.py tests/test_conversion_structure.py -q","exit":0}]} -->

**Checkpoint**: o PDF sintético de duas páginas (texto + imagem) converte com os dois trechos; o PDF só de texto sai idêntico.

#### Fase 4 — US-002 Saber quando a leitura precisa de revisão (P2)

**Objetivo**: os avisos são guardados por documento e devolvidos pela API.
**Teste independente**: `uv run pytest tests/test_task_process_conversion_document.py tests/test_router_conversao.py -q` passa.

- [x] T017 [CODE] [US-002] Acrescentar `avisos` ao `DocumentoConversao` em src/app/models.py com a migration em alembic/versions/ — Refs: US-002, FR-006, AC-004, AC-012 — Depends: T004, T011, T012
  - [x] **PREP**: RED de T004/T011/T012 conferido, modelo e cadeia Alembic lidos, documentação reconstruída; banco de teste separado validado SAFE.
  - [x] **EXECUTE**: Coluna JSON não anulável com padrões Python/lista e servidor/[]; revisão 0033_avisos_conversao sucede 0022_lotes_conversao. DATABASE.md atualizado manualmente; documentação reconstruída e monitor CURRENT.
  - [x] **VERIFY**: 6 passed: uv run pytest tests/test_app_migrations.py -q (SAFE). Cadeia upgrade head aplicada em schemas vazios do banco de teste; coluna avisos inspecionada como NOT NULL com padrão []. Nenhuma reversão executada.
  - [x] **VISUAL**: Não aplicável: alteração aditiva de schema sem superfície visual.
  - [x] **EVIDENCE**: Revisão 0033_avisos_conversao, arquivo 0033_documentos_conversao_avisos.py; migrações aprovadas. Persistência do resultado será verificada em T018, que acrescenta a escrita do worker.
  - [x] **IMPROVE**: Padrão também no servidor mantém documentos antigos compatíveis e permite inserções fora do ORM.
  <!-- specsfy:evidence {"task":"T017","refs":["US-002","FR-006","AC-004","AC-012"],"files":["src/app/models.py","alembic/versions/0033_documentos_conversao_avisos.py"],"commands":[{"run":"uv run pytest tests/test_app_migrations.py -q","exit":0}]} -->

- [x] T018 [CODE] [US-002] Gravar os avisos em `process_conversion_document_task` (src/app/tasks.py) e devolvê-los em `_serializar_documento` (src/app/routers/conversao.py) — Refs: US-002, FR-006, FR-007, NFR-002, NFR-003, AC-003, AC-004, AC-011, AC-012 — Depends: T003, T011, T012, T016, T017
  - [x] **PREP**: RED de T003/T011/T012 conferido; conversor e coluna entregues; worker e serializer lidos, documentação reconstruída antes da escrita.
  - [x] **EXECUTE**: Worker serializa dataclasses com asdict, limpa avisos em falha e API devolve lista vazia quando ausentes. Documentação reconstruída; PROJECT.md revisado sem capacidade adicional além da SPEC-0033.
  - [x] **VERIFY**: 25 passed: uv run pytest tests/test_task_process_conversion_document.py tests/test_router_conversao.py -q, SAFE; avisos guardados e devolvidos, lote e permissões preservados.
  - [x] **VISUAL**: Não aplicável: escrita no worker e contrato JSON da API não renderizam interface.
  - [x] **EVIDENCE**: GREEN de AC-003/AC-004/AC-011/AC-012 e regressão da SPEC-0023; build_documentation executado e monitor CURRENT.
  - [x] **IMPROVE**: Limpeza explícita dos avisos em falha evita mostrar motivos antigos após uma nova tentativa.
  <!-- specsfy:evidence {"task":"T018","refs":["US-002","FR-006","FR-007","NFR-002","NFR-003","AC-003","AC-004","AC-011","AC-012"],"files":["src/app/tasks.py","src/app/routers/conversao.py"],"commands":[{"run":"uv run pytest tests/test_task_process_conversion_document.py tests/test_router_conversao.py -q","exit":0}]} -->

**Checkpoint**: um documento com OCR fraco termina `concluido`, com `avisos` na API; o documento de texto do mesmo lote segue sem aviso.

#### Fase de interface

- [x] T019 [CODE] [US-002] Criar o bloco `SeloRevisarDocumento` em frontend/src/features/conversao/SeloRevisarDocumento.tsx e os rótulos dos códigos de aviso em frontend/src/features/conversao/situacao.ts — Refs: US-002, FR-008, AC-004, AC-006, AC-012 — Depends: T013, T018
  - [x] **PREP**: Seção 10, INTERFACE.md, design system, primitives Base UI e testes RED de T013 lidos. Usadas as skills React UI Components, UI Design, Design System e shadcn/ui; composição local Badge + Tooltip selecionada.
  - [x] **EXECUTE**: Selo composto por Badge outline e Tooltip Base UI local, sem dependência nova; rótulos e página em português, foco/hover/toque e propagação da linha protegida. INTERFACE.md registra a composição.
  - [x] **VERIFY**: 3 passed: npm --prefix frontend run test:tdd -- src/features/conversao/SeloRevisarDocumento.test.tsx; nome acessível, vazio e foco por Tab aprovados. Regressão completa da lista ocorre em T020.
  - [x] **VISUAL**: Playwright em harness local, 375×900 e 1280×900, claro/escuro, foco/hover/toque e motivos curtos/longos: bordas, espaçamentos, margens, padding e tipografia conferidos contra Badge. 8 screenshots e selo.json em /tmp/spec0033-visual sem overflow; fonte Geist, tamanho 12px, peso 500 e linha 16px, borda 1px, padding 2px/8px, margem 0. Popup contido no viewport.
  - [x] **EVIDENCE**: 3 testes focais aprovados; revisão visual registrada em /tmp/spec0033-visual/selo.json e screenshots. INTERFACE.md atualizado; documentação reconstruída. Acrescentado role tooltip explícito e teste do motivo por foco.
  - [x] **IMPROVE**: A conferência reforçou o teste de foco para verificar também o conteúdo visível do Tooltip; uso de tokens mantém paridade com Badge.
  <!-- specsfy:evidence {"task":"T019","refs":["US-002","FR-008","AC-004","AC-006","AC-012"],"files":["frontend/src/features/conversao/SeloRevisarDocumento.tsx","frontend/src/features/conversao/situacao.ts","frontend/src/components/ui/tooltip.tsx"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/features/conversao/SeloRevisarDocumento.test.tsx","exit":0}]} -->

- [x] T020 [CODE] [US-002] Exibir o selo e o motivo na lista e no painel do lote em frontend/src/features/conversao/DataGridLotesConversao.tsx e frontend/src/features/conversao/PainelLoteConversao.tsx — Refs: US-002, FR-008, AC-004, AC-006, AC-012 — Depends: T019
  - [x] **PREP**: Selo concluído, grade e painel existentes lidos; mesmas ações, PageHeader e permissões preservados; especialistas de UI carregados; documentação reconstruída.
  - [x] **EXECUTE**: Grade e painel reutilizam SeloRevisarDocumento, motivos por documento e avisos opcionais para compatibilidade. Enter na linha só atua no próprio tr; nome longo do painel quebra sem truncate. INTERFACE.md preservado e documentação reconstruída.
  - [x] **VERIFY**: 11 passed: npm --prefix frontend run test:tdd -- src/features/conversao; regressão de lista, situação, download, exclusão, reenvio e selo aprovada.
  - [x] **VISUAL**: Playwright em 375×900 e 1280×900, claro/escuro: bordas, espaçamentos, margens, padding e tipografia do selo, coluna Situação e painel conferidos; conteúdo curto/longo, foco e clique/Enter. Sem overflow global, tabela conserva rolagem interna; Enter no selo não abre lote, Enter na linha abre Sheet com motivo/páginas. Screenshots lista/painel em /tmp/spec0033-visual.
  - [x] **EVIDENCE**: 11 testes focais e revisão renderizada aprovados; arquivos da grade/painel e contrato DocumentoConversaoResumo com avisos opcionais atualizados. Documentação reconstruída e INTERFACE.md registra consumidores.
  - [x] **IMPROVE**: Linha ignora teclas vindas de controles internos; nome do arquivo no painel quebra em vez de truncar, melhorando a leitura de nomes longos no mobile.
  <!-- specsfy:evidence {"task":"T020","refs":["US-002","FR-008","AC-004","AC-006","AC-012"],"files":["frontend/src/features/conversao/DataGridLotesConversao.tsx","frontend/src/features/conversao/PainelLoteConversao.tsx"],"commands":[{"run":"npm --prefix frontend run test:tdd -- src/features/conversao","exit":0}]} -->

- [x] T021 [DOC] [US-002] Registrar `SeloRevisarDocumento` e as extensões de `DataGridLotesConversao`, `PainelLoteConversao` e `situacao.ts` em INTERFACE.md — Refs: US-002, FR-008, AC-004 — Depends: T019, T020
  - [x] **PREP**: Linhas existentes de conversão em INTERFACE.md lidas, componentes e consumidores conferidos.
  - [x] **EXECUTE**: INTERFACE.md registra selo, Tooltip, motivos e consumidores da grade/painel; mapa preserva a aba Conversão e as ações existentes.
  - [x] **VERIFY**: Arquivos e imports conferidos; 11 testes da conversão e revisão renderizada comprovam o mapa e o fluxo.
  - [x] **VISUAL**: Não aplicável: mapa documental; conferência das telas registrada em T019/T020.
  - [x] **EVIDENCE**: Blocos, origem Base UI/shadcn, API, estados, teclado e regras de reuso registrados em INTERFACE.md.
  - [x] **IMPROVE**: Registrada a independência entre aviso e situação para evitar que revisão bloqueie download.

**Checkpoint**: a aba Conversão mostra "Revisar" com o motivo num documento com aviso e nada num documento sem aviso.

#### Fase final — Qualidade e documentação

- [x] T022 [DOC] Registrar `documentos_conversao.avisos` e a migration em .specsfy/DATABASE.md — Refs: US-002, FR-006, AC-012 — Depends: T017
  - [x] **PREP**: Mapa de dados e coluna/migration conferidos; monitor CURRENT; regra local exige curadoria manual.
  - [x] **EXECUTE**: DATABASE.md registra JSON, padrão vazio, campos, códigos, páginas, revisão e retenção; conteúdo humano preservado, sem scanner incompatível com Python.
  - [x] **VERIFY**: monitor_context.mjs --project . --check retornou CURRENT; mapa conferido com model e migration.
  - [x] **VISUAL**: Não aplicável: documentação de persistência sem tela.
  - [x] **EVIDENCE**: Revisão 0033_avisos_conversao documentada; 6 testes de migration aprovados em schemas isolados.
  - [x] **IMPROVE**: Registrada a numeração humana das páginas e o caso pagina nula em imagens, evitando ambiguidade no contrato.

- [x] T023 [DOC] Revisar .specsfy/STACK.md, .specsfy/RULES.md e PROJECT.md e registrar a justificativa na evidência — Refs: US-001, FR-001, NFR-001 — Depends: T016
  - [x] **PREP**: PROJECT.md, STACK.md e RULES.md lidos; sem manifest ou dependência nova.
  - [x] **EXECUTE**: PROJECT.md registra OCR local por página e configuração. STACK.md revisado: pymupdf4llm, pymupdf e Tesseract/idiomas já existentes; nenhuma tecnologia nova. RULES.md revisado: arquitetura e política de segredos preservadas; nenhuma regra durável nova.
  - [x] **VERIFY**: Monitor CURRENT após documentação reconstruída; sem reconhecimento que oculte mudança narrativa, PROJECT.md foi atualizado.
  - [x] **VISUAL**: Não aplicável: revisão documental sem interface.
  - [x] **EVIDENCE**: Capacidade e limites da SPEC-0033 em PROJECT.md; stack e regras sem mudança justificada pelas dependências preexistentes.
  - [x] **IMPROVE**: Valores operacionais ficam no config.example.yaml versionado e no config.yaml local ignorado, preservando o contexto do operador.

- [x] T024 [TEST] Executar regressão e rastreabilidade em tests/test_conversion_pdf_ocr.py e frontend/src/features/conversao/SeloRevisarDocumento.test.tsx, e reconstruir docs/README.md com `$specsfy-documentator` — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012 — Depends: T015, T018, T020, T021, T022, T023
  - [x] **PREP**: Suítes Pytest/Vitest, Ruff, ESLint, tipos, build e rastreabilidade identificados; banco separado SAFE. Dependências entregues e harness temporário removido após revisão visual.
  - [x] **EXECUTE**: uv run pytest -q: 586 passed, 1 skipped preexistente, exit 0; npm --prefix frontend run test:tdd: 236 passed, exit 0. Ruff, ESLint, typecheck e build aprovados. Rastreamento completo e documentação reconstruída.
  - [x] **VERIFY**: 26/26 IDs cobertos com --full-chain, QA dos 12 AC Passed, evidências strict aprovadas, Definition/Plan/Interface/Research aprovados. Nenhum teste da SPEC-0033 pulado. Regressão da SPEC-0023 aprovada.
  - [x] **VISUAL**: Conferência final das screenshots e métricas Playwright em 375×900 e 1280×900, claro/escuro: bordas, espaçamentos, margens, padding e tipografia do selo, lista e painel coerentes; motivos curtos/longos, teclado/toque e ausência de overflow aprovados. Forma registrado como forma de inspeção nas evidências T019/T020, /tmp/spec0033-visual.
  - [x] **EVIDENCE**: Pytest completo: 586 passed/1 skipped em 883s; Vitest: 236 passed/58 arquivos. Comandos SAFE antes dos runners; revisão real em T019/T020; build final sem harness. Gaps da auditoria global em specs antigas registrados separadamente na seção 13.
  - [x] **IMPROVE**: Ajustada a sessão das migrations para inspeção sequencial do catálogo, eliminando DiskFull sem remover schemas; AC-002 compara Markdown literalmente e o teste do selo verifica o conteúdo do Tooltip por foco.

### 15. Ordem de execução

- Caminho crítico: T001–T013 (RED) → T014 → T016 → T015 → T017 → T018 → T019 → T020 → T021 → T024.
- Tarefas paralelas: T001 a T013 não compartilham arquivos de produção; T022 e T023 (documentação) são independentes de T019 e T020. T015 depende de T016 para verificar o idioma comum a PDF e imagem.
- Estratégia de MVP: T014 a T016 entregam US-001 (o defeito relatado); US-003 e US-002 vêm em seguida.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0023 (concluída): conversores, tarefa e lista de documentos.
- Tesseract com `por` e `eng` no ambiente do worker; na imagem de produção, a confirmação fica no backlog 0028.
- Alembic para a migration da coluna `avisos`.

#### Riscos

- O limiar de "texto útil" mal calibrado gera OCR desnecessário ou avisos em excesso → valor configurável e testado com PDFs sintéticos; ajuste posterior com PDFs reais fora do repositório.
- O comportamento do `pymupdf4llm` por página pode mudar entre versões → testes por página com PDFs sintéticos e versão fixada em `pyproject.toml`.
- Mudar o idioma padrão do OCR de imagem de `por` para `por+eng` altera resultados já entregues → configurável; a regressão da SPEC-0023 cobre o comportamento.
- OCR lento em PDFs grandes → limite de páginas e execução só no worker.
- Tesseract ausente na imagem de produção → o aviso `ocr_falhou` torna o problema visível; a instalação é tratada no backlog 0028.

#### Suposições

- Padrões: `idioma` `por+eng`; `limite_paginas_ocr` 50; `minimo_texto_util` 40 caracteres não brancos por página. Reversíveis pelo `config.yaml`.
- "Pouco texto" no OCR significa menos de `minimo_texto_util` caracteres não brancos devolvidos para a página.
- O aviso de baixa confiança do OCR foi retirado porque o `pymupdf4llm` não expõe a confiança (DEC-006); reversível se a biblioteca passar a expô-la.
- Aviso e situação são ortogonais: "Revisar" não cria estado novo de documento.
- Os motivos mostrados são os de `AvisoConversao.mensagem`, em português.

### 17. Decisões

- **DEC-001**: Item separado do 0039 — a correção é pequena e urgente; o 0039 depende de itens maiores, e uma única fonte evita divergência.
- **DEC-002**: OCR por página, só onde falta texto útil — preserva a fidelidade de tabelas e a velocidade nas páginas de texto; alternativas (PDF inteiro, todas as páginas) perdem fidelidade ou custam mais. Implementado chamando o `pymupdf4llm` página a página (DEC-006).
- **DEC-003**: "Revisar" como aviso persistido, não como situação — mantém o documento `concluido` e baixável; o custo é uma coluna JSON com migration.
- **DEC-004**: Configuração só no `config.yaml` — a tela de configurações da conversão fica para um item futuro, pois a SPEC-0029 não criou uma tela global.
- **DEC-006**: Manter o `pymupdf4llm` como motor de OCR (2026-10-14, Pergunta 1 da implementação, opção 1) — a biblioteca já faz OCR com Tesseract e aceita `ocr_language`, `use_ocr` e `pages`; escrever `ocr.py` próprio duplicaria o motor. Trade-off: o aviso de baixa confiança sai do escopo (a biblioteca não a expõe) e o limite de páginas é aplicado por nós, chamando a biblioteca página a página. Alternativa descartada: desligar o OCR automático e usar `pytesseract` próprio.
- **DEC-005**: Idioma único para PDF e imagem, padrão `por+eng` — evita um segundo ajuste fixo no código; o efeito sobre imagens é reversível pela configuração.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/DATABASE.md` registra a coluna `documentos_conversao.avisos` e a migration.
- [x] `.specsfy/STACK.md` e `.specsfy/RULES.md` revisados; sem tecnologia nova nem regra nova, registrar a justificativa na evidência.
- [x] `PROJECT.md` revisado (capacidade de OCR em PDF) e `INTERFACE.md` atualizado com `SeloRevisarDocumento`.
- [x] `$specsfy-documentator` executado após a implementação.

## Effort history

- 2026-10-14T13:57:18.859Z: 4 → 4. O pymupdf4llm já faz o OCR; a entrega configura idioma e limite, acrescenta avisos, coluna com migration, campo de API e selo na lista.
