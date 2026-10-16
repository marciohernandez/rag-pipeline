# Especificação integrada: Fase 1: detectar contradições e relatório

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0038 |
| Slug | 0038-fase-1-detectar-contradicoes-e-relatorio |
| Status | Reviewing |
| Effort | 8 |
| Effort updated at | 2026-10-16 |
| Effort rationale | Análise cruzada com IA sobre coleções inteiras, agrupamento por assunto, processamento em partes com retomada, relatório em tela, Markdown e PDF, privacidade e dependência da SPEC-0037; exige raciocínio sobre falsos alarmes e contradições perdidas. |
| ClickUp Task | |
| Milestones | M04 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-16 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

Áreas diferentes da mesma empresa dão informações conflitantes nos documentos que entregam (por exemplo, cancelamento em 7 dias no comercial e em 15 dias no marketing; preços e descontos). Se esses documentos entram na base vetorial como estão, o RAG responde de forma incoerente. Hoje a pessoa da consultoria teria de ler todos os `.md` e comparar à mão.

#### Resultado desejado

Um relatório de contradições da coleção, em que cada ocorrência traz o assunto, uma etiqueta, os trechos lado a lado, os arquivos de origem e a explicação da divergência, para a pessoa conferir com a empresa o que vale. O sistema detecta e relata; nunca corrige nada sozinho.

#### Métricas de sucesso

- Medido contra o gabarito de 3 ou 4 documentos reais da pessoa (fora do repositório): pelo menos 90% das contradições reais marcadas são capturadas. Verificação final opt-in na entrega (DEC-007): o gabarito ainda não foi entregue (é o mesmo da SPEC-0037).
- 100% das ocorrências do relatório trazem pelo menos dois trechos com o arquivo de origem de cada um.
- 0 alterações em qualquer documento da coleção causadas pela análise.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: leitura do código das coleções (`src/app/models.py`, `src/app/routers/colecoes.py`) → o `.md` completo de cada documento da coleção vive no armazenamento do último envio (`DocumentoColecao.ultimo_envio_id`); `ConteudoDocumento.texto` pode estar truncado e por isso não serve de fonte única da análise (a confirmar na tarefa de leitura).
- **R-002**: conferência das dependências do projeto → não há biblioteca de PDF dedicada; `pymupdf` já é dependência e gera PDF a partir de HTML (ver DEC-004).

#### Fontes e contexto consultados

- `specs/backlog/0042-fase-1-detectar-contradicoes-e-relatorio.md` (Perguntas 1 a 8, interface e critérios).
- `specs/review/0037-fase-1-conteudo-de-dominio-e-limpeza/spec.md` (já na `main`; conexão de IA por Workspace, resumo do domínio, papéis, retenção).
- `specs/milestones/M04.md`, `.specsfy/DATABASE.md` (linhas de IA para análise, relatórios e situação por documento), `INTERFACE.md`, `DESIGNSYSTEM.MD`.
- `specs/completed/0030-*/spec.md` (coleções), `specs/completed/0031-*/spec.md` (conteúdo processado) e `frontend/src/features/colecoes/`.

#### Documentação consultada

- Nenhuma documentação externa.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Como detecta? → **A**: agrupa os trechos por assunto e a IA julga só os pares do mesmo assunto, com a chave de IA do Workspace (backlog, Pergunta 1).
- **Q**: Quando roda? → **A**: só quando a pessoa clica em "Analisar contradições", com aviso de que o conteúdo será enviado à IA configurada (Pergunta 2).
- **Q**: Entre quais documentos? → **A**: todos os `.md` da coleção, os que já estavam e os que chegaram agora (Pergunta 3).
- **Q**: O que conta como contradição? → **A**: conflito direto, diferença de versão e duplicidade; etiquetas "conflito", "versão desatualizada" e "duplicado" (Pergunta 4).
- **Q**: Como é o relatório? → **A**: um cartão por ocorrência com assunto, etiqueta, trechos lado a lado, arquivo de origem (e imagem, quando vier de print) e explicação, organizado por assunto com valores e prazos no topo (Pergunta 5); tela no sistema com download em `.md` e PDF (Pergunta 6).
- **Q**: Qual a meta de qualidade? → **A**: capturar pelo menos 90% das contradições reais, medido contra o gabarito (Pergunta 7).
- **Q**: O que acontece em falha? → **A**: sem chave de IA avisa e não começa; se cair, guarda o analisado e retoma de onde parou; coleção grande vai em partes; o analisado aparece com aviso de que não terminou (Pergunta 8).
- **Q**: Ordem com a limpeza? → **A**: a análise roda a pedido sobre os `.md` já limpos, usando o resumo do domínio como contexto (2026-10-16).
- **Q**: Onde fica na interface? → **A**: botão no cabeçalho da página da coleção e relatório em rota própria `.../colecoes/{colecaoId}/contradicoes`, com aviso de andamento, filtro por etiqueta e cartões lado a lado (2026-10-16, Interface, Perguntas 1 a 4).
- **Q**: Quem pode o quê? → **A**: owner e admin iniciam, continuam e baixam; member só consulta (2026-10-16, DEC-007 da SPEC-0037).

#### Dúvidas abertas

- Nenhuma bloqueante. O gabarito e a confirmação da meta de 90% são verificação final opt-in na entrega, com o conjunto que a pessoa trouxer, e não condição da definição (DEC-007). Agrupamento por assunto, tamanho das partes e imagem de origem entram como suposições reversíveis (seção 16).

### 3. Escopo e atores

#### Incluído

- Ação "Analisar contradições" por coleção, a pedido, com aviso de envio do conteúdo à IA.
- Extração de afirmações por documento, agrupamento por assunto e julgamento da IA só dentro de cada assunto.
- Ocorrências com etiqueta, impacto, trechos de origem e explicação.
- Processamento em partes, em segundo plano, com progresso, guarda do já analisado e retomada.
- Rota do relatório com agrupamento por assunto, ordem por impacto, filtro por etiqueta e estados.
- Download do relatório em Markdown e em PDF; retenção de 90 dias.

#### Fora de escopo

- Registrar a decisão da empresa, corrigir os `.md` e liberar a coleção (BACKLOG-0043).
- Limpeza, domínio e conexão de IA (SPEC-0037); esta spec as consome.
- Sequências de imagens e tabelas (BACKLOG-0040); a referência a imagem de origem só existe quando o próprio `.md` a trouxer.
- Análise automática ao fim do lote e análise de coleções ainda não limpas.
- Qualquer alteração de documento, vetor ou coleção pela análise.

#### Atores

- **Owner e admin (papel de escrita)**: iniciam e continuam a análise, consultam o relatório e baixam o `.md` e o PDF.
- **Member**: consulta a rota do relatório; não inicia, não continua e não baixa.
- **IA de análise**: modelo externo da conexão do Workspace; extrai afirmações e julga pares do mesmo assunto.

### 4. Princípios e restrições do projeto

- **PR-001**: o sistema detecta e relata; nenhuma escrita em documento ou vetor.
- **PR-002**: o conteúdo dos documentos só vai à IA externa após o clique e com aviso, e só com a chave do Workspace ligada.
- **PR-003**: textos de clientes não aparecem em logs; o relatório guarda trechos por 90 dias e depois é apagado.
- **PR-004**: toda fronteira com IA passa pelo contrato `ChatModelAdapter` (LangChain-first e modular).
- **PR-005**: testes nunca usam o banco de desenvolvimento; usam a instância isolada de testes.
- **PR-006**: a interface reutiliza `PageHeader`, `Alert`, `Badge`, `Button` e os padrões de `features/colecoes`; novos blocos entram em `INTERFACE.md`.

### 5. Histórias de usuário

#### US-001 — Pedir a análise de contradições da coleção (P1)

Como owner ou admin, quero clicar em "Analisar contradições" na coleção, para que o sistema compare os documentos entre si com a IA do Workspace.

**Por que P1**: sem o pedido não há relatório.
**Teste independente**: com IA simulada, iniciar a análise de uma coleção de três documentos e ver o relatório.
**Requisitos**: FR-001, FR-002, FR-006, FR-009

#### US-002 — Receber ocorrências com origem (P1)

Como pessoa da consultoria, quero cada contradição com assunto, etiqueta, trechos lado a lado, arquivos de origem e explicação, para conferir com a empresa o que vale.

**Por que P1**: é o valor central do item.
**Teste independente**: coleção com duas políticas de cancelamento diferentes gera uma ocorrência "conflito" com os dois arquivos.
**Requisitos**: FR-003, FR-004

#### US-003 — Análise que sobrevive a falhas e a coleções grandes (P1)

Como pessoa da consultoria, quero que a análise guarde o que já analisou, retome de onde parou e processe coleções grandes em partes, para não perder trabalho nem esperar sem ver nada.

**Por que P1**: a coleção real pode ter dezenas de documentos e a IA pode falhar no meio.
**Teste independente**: derrubar o provider no meio e continuar a análise sem refazer os assuntos concluídos.
**Requisitos**: FR-005, FR-006, FR-007

#### US-004 — Baixar o relatório (P2)

Como owner ou admin, quero baixar o relatório em Markdown e em PDF, para levá-lo à empresa fora do sistema.

**Por que P2**: a conferência com a empresa acontece fora do sistema.
**Teste independente**: baixar os dois formatos de uma análise concluída e conferir o conteúdo.
**Requisitos**: FR-008, FR-009

#### US-005 — Consultar o relatório na tela (P2)

Como pessoa do Workspace, quero ver o relatório numa rota própria, ordenado por impacto e filtrável por etiqueta, para localizar primeiro o que mais importa.

**Por que P2**: a leitura confortável depende das ocorrências já existirem.
**Teste independente**: abrir a rota com ocorrências de etiquetas diferentes e filtrar.
**Requisitos**: FR-007, FR-009

### 6. Cenários BDD de aceite

#### AC-001 — Conflito direto entre dois arquivos

**Cobre**: US-001, US-002, FR-001, FR-003, FR-004, NFR-002

```gherkin
@US-001 @US-002 @FR-001 @FR-003 @FR-004 @NFR-002 @AC-001
Feature: Relatório de contradições

  Scenario: política de cancelamento diferente em dois arquivos
    Given uma coleção com "comercial.md" dizendo cancelamento em 7 dias e "marketing.md" dizendo 15 dias
    When owner ou admin clica em "Analisar contradições"
    Then o relatório traz uma ocorrência "conflito" com o assunto cancelamento
    And os dois trechos aparecem lado a lado com os nomes "comercial.md" e "marketing.md" e a explicação da divergência
    And nenhum documento da coleção foi alterado
```

#### AC-002 — Versão desatualizada

**Cobre**: US-002, FR-003, FR-004, NFR-002

```gherkin
@US-002 @FR-003 @FR-004 @NFR-002 @AC-002
Feature: Relatório de contradições

  Scenario: mesma informação em versões diferentes
    Given dois arquivos sobre a tabela de preços com datas e valores diferentes
    When a análise termina
    Then a ocorrência recebe a etiqueta "versão desatualizada"
    And indica qual trecho tem a data mais antiga
    And os arquivos permanecem inalterados
```

#### AC-003 — Duplicado entre arquivos

**Cobre**: US-002, FR-003, FR-004

```gherkin
@US-002 @FR-003 @FR-004 @AC-003
Feature: Relatório de contradições

  Scenario: mesma informação repetida em dois arquivos
    Given dois arquivos com o mesmo fato escrito de forma equivalente
    When a análise termina
    Then a ocorrência recebe a etiqueta "duplicado" e lista os dois arquivos de origem
```

#### AC-004 — Sem chave de IA não começa

**Cobre**: US-001, FR-001, FR-006, NFR-001

```gherkin
@US-001 @FR-001 @FR-006 @NFR-001 @AC-004
Feature: Início da análise

  Scenario: Workspace sem IA externa permitida
    Given um Workspace com "permitir análise por IA externa" desligada e um modelo de IA espião
    When owner ou admin tenta analisar a coleção
    Then o sistema avisa o motivo e não inicia a análise
    And o modelo de IA não recebe nenhuma chamada
```

#### AC-005 — Só owner e admin iniciam

**Cobre**: US-001, FR-001, FR-009

```gherkin
@US-001 @FR-001 @FR-009 @AC-005
Feature: Permissões da análise

  Scenario: member não inicia nem continua a análise
    Given uma pessoa com papel member
    When ela tenta iniciar ou continuar uma análise
    Then recebe recusa por permissão insuficiente
    And nenhuma análise é criada
```

#### AC-006 — Aviso de envio à IA

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-006
Feature: Início da análise

  Scenario: confirmação antes de enviar o conteúdo à IA
    Given uma coleção pronta para análise
    When owner ou admin clica em "Analisar contradições"
    Then o sistema informa que o conteúdo será enviado à IA configurada e qual é o provedor
    And a análise só começa depois da confirmação
```

#### AC-007 — Só pares do mesmo assunto vão à IA

**Cobre**: US-001, FR-002, NFR-003

```gherkin
@US-001 @FR-002 @NFR-003 @AC-007
Feature: Agrupamento por assunto

  Scenario: a IA julga apenas afirmações do mesmo assunto
    Given afirmações sobre cancelamento em dois arquivos e sobre horário de atendimento em outros dois
    When a análise roda
    Then a IA recebe um julgamento por assunto com somente as afirmações daquele assunto
    And o número de julgamentos é menor que o de todos os pares possíveis
```

#### AC-008 — Assuntos diferentes não são comparados

**Cobre**: FR-002, FR-003, NFR-002

```gherkin
@FR-002 @FR-003 @NFR-002 @AC-008
Feature: Agrupamento por assunto

  Scenario: números diferentes de assuntos diferentes não geram ocorrência
    Given um arquivo com "atendimento até 18h" e outro com "cancelamento em 7 dias"
    When a análise termina
    Then nenhuma ocorrência é criada entre esses dois trechos
```

#### AC-009 — Assunto escrito de formas diferentes

**Cobre**: US-001, FR-002, NFR-003

```gherkin
@US-001 @FR-002 @NFR-003 @AC-009
Feature: Agrupamento por assunto

  Scenario: "prazo de cancelamento" e "cancelamento: prazo" viram o mesmo assunto
    Given duas afirmações com o assunto escrito de formas equivalentes após a normalização
    When as afirmações são agrupadas
    Then ficam no mesmo grupo e são julgadas juntas
```

#### AC-010 — Retomada sem refazer

**Cobre**: US-003, FR-005, NFR-003

```gherkin
@US-003 @FR-005 @NFR-003 @AC-010
Feature: Análise resiliente

  Scenario: queda no meio e retomada
    Given uma análise de 10 assuntos em que o provider de IA cai após 6
    When owner ou admin clica em "Continuar análise"
    Then só os 4 assuntos restantes são julgados
    And as ocorrências dos 6 primeiros permanecem sem duplicar
```

#### AC-011 — Relatório parcial com aviso

**Cobre**: US-003, FR-005, FR-007, NFR-004

```gherkin
@US-003 @FR-005 @FR-007 @NFR-004 @AC-011
Feature: Análise resiliente

  Scenario: análise incompleta aparece com aviso acessível
    Given uma análise interrompida com 6 de 10 assuntos concluídos
    When a pessoa abre a rota do relatório
    Then vê as ocorrências já analisadas com o aviso "Análise incompleta (6 de 10 assuntos)" e o motivo
    And o aviso é anunciado por tecnologia assistiva com role=status
```

#### AC-012 — Coleção grande em partes

**Cobre**: US-003, FR-005, NFR-003

```gherkin
@US-003 @FR-005 @NFR-003 @AC-012
Feature: Análise resiliente

  Scenario: coleção com 50 documentos é processada em partes com progresso
    Given uma coleção com 50 documentos
    When a análise roda em segundo plano
    Then as afirmações são extraídas em partes limitadas por tamanho
    And o progresso "X de Y assuntos" avança e as ocorrências concluídas já aparecem
```

#### AC-013 — IA indisponível não marca como resolvido

**Cobre**: US-003, FR-005, FR-006

```gherkin
@US-003 @FR-005 @FR-006 @AC-013
Feature: Falha da IA

  Scenario: provider indisponível
    Given a IA de análise falha com indisponibilidade
    When a análise roda
    Then a análise fica "Incompleta" com o motivo "IA indisponível"
    And nenhum assunto não analisado é tratado como sem contradição
```

#### AC-014 — Coleção vazia

**Cobre**: US-001, FR-006

```gherkin
@US-001 @FR-006 @AC-014
Feature: Início da análise

  Scenario: coleção sem documentos
    Given uma coleção sem documentos
    When owner ou admin tenta analisar
    Then o sistema avisa que não há o que analisar e não chama a IA
```

#### AC-015 — Impacto no topo e filtro por etiqueta

**Cobre**: US-005, FR-007

```gherkin
@US-005 @FR-007 @AC-015
Feature: Rota do relatório

  Scenario: valores e prazos primeiro e filtro por etiqueta
    Given ocorrências sobre preço, prazo e horário, com etiquetas diferentes
    When a pessoa abre o relatório e filtra por "conflito"
    Then as ocorrências de maior impacto (valores e prazos) aparecem no topo
    And só as de etiqueta "conflito" permanecem visíveis
```

#### AC-016 — Nenhuma contradição

**Cobre**: US-005, FR-004, FR-007

```gherkin
@US-005 @FR-004 @FR-007 @AC-016
Feature: Rota do relatório

  Scenario: análise sem ocorrências
    Given uma análise concluída sem contradições em 8 documentos
    When a pessoa abre o relatório
    Then a tela diz "Nenhuma contradição encontrada" e que 8 documentos foram analisados
```

#### AC-017 — Download em Markdown

**Cobre**: US-004, FR-008

```gherkin
@US-004 @FR-008 @AC-017
Feature: Download do relatório

  Scenario: relatório em Markdown
    Given uma análise concluída com ocorrências
    When owner ou admin baixa o relatório em Markdown
    Then o arquivo traz as ocorrências agrupadas por assunto com etiqueta, trechos, arquivos de origem e explicação
```

#### AC-018 — Download em PDF

**Cobre**: US-004, FR-008

```gherkin
@US-004 @FR-008 @AC-018
Feature: Download do relatório

  Scenario: relatório em PDF
    Given uma análise concluída com ocorrências
    When owner ou admin baixa o relatório em PDF
    Then recebe um PDF legível com o mesmo conteúdo do relatório em Markdown
```

#### AC-019 — Member consulta mas não baixa

**Cobre**: US-004, US-005, FR-008, FR-009

```gherkin
@US-004 @US-005 @FR-008 @FR-009 @AC-019
Feature: Permissões do relatório

  Scenario: member vê a tela e não baixa
    Given uma pessoa com papel member e uma análise concluída
    When ela abre a rota do relatório e tenta baixar
    Then vê as ocorrências
    And o download em Markdown e em PDF é recusado por permissão insuficiente
```

#### AC-020 — Retenção e metadados do relatório

**Cobre**: US-004, FR-009, NFR-001

```gherkin
@US-004 @FR-009 @NFR-001 @AC-020
Feature: Retenção do relatório

  Scenario: relatório guarda provedor e versão do domínio e vence em 90 dias
    Given uma análise concluída há 91 dias e outra há 10 dias
    When a rotina de retenção roda
    Then a análise antiga e suas ocorrências são apagadas e a recente permanece
    And o relatório recente informa o provedor de IA e a versão do domínio usada
```

#### AC-021 — Celular e teclado

**Cobre**: US-005, FR-007, NFR-004

```gherkin
@US-005 @FR-007 @NFR-004 @AC-021
Feature: Responsividade

  Scenario: cartões em 375 pixels
    Given um viewport de 375 pixels e trechos com palavras muito longas
    When a pessoa abre o relatório
    Then os trechos empilham, um sobre o outro, e o texto quebra sem rolagem horizontal da página
    And os filtros e botões são operáveis por teclado
```

#### AC-022 — Foco e anúncio do andamento

**Cobre**: US-005, NFR-004

```gherkin
@US-005 @NFR-004 @AC-022
Feature: Acessibilidade

  Scenario: andamento e conclusão anunciados
    Given uma análise em andamento
    When o progresso muda e a análise conclui
    Then a mudança é anunciada em role=status
    And o foco permanece no controle usado e o botão "Analisar contradições" exibe estado de carregamento
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve permitir que owner e admin iniciem a análise de contradições de uma coleção a pedido, exigindo antes a chave "permitir análise por IA externa" ligada e uma conexão de IA do Workspace, e exibindo o aviso de envio do conteúdo à IA configurada com o provedor; member não inicia nem continua.
- **FR-002**: O sistema deve extrair afirmações dos `.md` da coleção, agrupá-las por assunto normalizado e enviar à IA um julgamento por assunto contendo somente as afirmações daquele assunto.
- **FR-003**: O sistema deve classificar cada ocorrência detectada com uma das etiquetas "conflito", "versão desatualizada" ou "duplicado", sem comparar afirmações de assuntos diferentes.
- **FR-004**: O sistema deve registrar, por ocorrência, assunto, etiqueta, impacto, pelo menos dois trechos com o arquivo de origem de cada um (e a referência de imagem quando o `.md` a trouxer) e a explicação da divergência.
- **FR-005**: O sistema deve processar a análise em segundo plano, em partes limitadas por tamanho, guardando o progresso por assunto, mostrando o progresso e as ocorrências já concluídas, e retomando de onde parou sem refazer os assuntos concluídos nem duplicar ocorrências.
- **FR-006**: O sistema deve tratar sem perder dados a ausência de chave de IA, a IA indisponível e a coleção vazia: avisar o motivo, não iniciar quando não houver o que analisar, e marcar como "Incompleta" a análise interrompida sem tratar assunto não analisado como sem contradição.
- **FR-007**: O sistema deve exibir o relatório numa rota própria da coleção com o aviso de andamento ou de análise incompleta, ocorrências agrupadas por assunto com as de maior impacto (valores e prazos) no topo, filtro por etiqueta, cartões com trechos lado a lado e o estado "Nenhuma contradição encontrada".
- **FR-008**: O sistema deve permitir que owner e admin baixem o relatório em Markdown e em PDF com o mesmo conteúdo; member não baixa.
- **FR-009**: O sistema deve guardar o relatório por 90 dias com provedor de IA e versão do domínio usada, apagá-lo depois, apagá-lo junto com a coleção, e restringir início, continuação e download a owner e admin, permitindo a consulta ao member.

#### Não funcionais

- **NFR-001**: Privacidade: nenhum conteúdo vai à IA externa com a chave desligada nem antes da confirmação; trechos de documentos não aparecem em logs; retenção de 90 dias. **Verificação**: provider espião, varredura de logs em teste e rotina de retenção com datas simuladas.
- **NFR-002**: Integridade e qualidade: a análise nunca altera documento, vetor ou coleção; captura pelo menos 90% das contradições reais do gabarito. **Verificação**: teste que compara hashes dos documentos antes e depois; medição contra o gabarito (opt-in, fora do repositório).
- **NFR-003**: Escala e custo: o número de julgamentos é limitado pelo agrupamento por assunto, a extração roda em partes de tamanho limitado e a análise é idempotente por assunto. **Verificação**: contagem de chamadas ao modelo espião com 50 documentos simulados.
- **NFR-004**: Acessibilidade e responsividade: avisos em `role=status`, controles operáveis por teclado, foco visível e sem rolagem horizontal em 375 px. **Verificação**: testes de componente com Testing Library e conferência visual em desktop e mobile.

#### Erros e casos-limite

- Chave de IA desligada ou sem conexão → avisa e não começa.
- IA indisponível ou resposta inválida → análise "Incompleta", assuntos pendentes preservados, retomada disponível.
- Coleção sem documentos ou sem afirmações extraíveis → avisa que não há o que analisar.
- Documento ilegível ou truncado → ignorado na análise com aviso no relatório, sem interromper os demais.
- Afirmação sem assunto claro → não entra em ocorrência; contada como "não classificada" no relatório.
- Duas análises simultâneas na mesma coleção → a segunda é recusada enquanto a primeira estiver ativa.
- Apagar a coleção → apaga análises e ocorrências, sem deixar texto de cliente.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI + SQLAlchemy + Alembic; worker Procrastinate (`src/app/tasks.py`); fachada do pipeline em `src/pipeline/service.py`; provider de IA pelo contrato `ChatModelAdapter`.
- Coleções e documentos: `Colecao`, `DocumentoColecao` (com `ultimo_envio_id`) e armazenamento por envio; `ConteudoDocumento.texto` pode vir truncado (R-001).
- Frontend Next.js: página da coleção em `frontend/src/app/(autenticado)/workspaces/[id]/colecoes/[colecaoId]/page.tsx` e `features/colecoes/`.
- Depende da SPEC-0037: conexão de IA por Workspace, chave de IA externa, resumo do domínio e a regra de papéis (DEC-007).

#### Arquitetura e módulos

- `src/pipeline/contradicoes/` (novo, sem HTTP nem banco): `afirmacoes.py` (extração por documento com saída estruturada), `assuntos.py` (normalização e agrupamento, reutilizando a semelhança textual da SPEC-0037), `julgamento.py` (julga um assunto e devolve ocorrências com etiqueta, impacto e explicação), `relatorio.py` (Markdown e PDF) e `contratos.py` (`Afirmacao`, `Ocorrencia`, `Etiqueta`).
- `src/app/contradicoes.py` (novo): lê os `.md` da coleção, orquestra partes, grava progresso e ocorrências, aplica retenção.
- Fluxo: pedido → verificação de chave, conexão e coleção → análise `em_andamento` → extração em partes → agrupamento por assunto → um julgamento por assunto → ocorrências gravadas → análise `concluida` ou `incompleta`.
- Parâmetros em configuração: tamanho máximo de cada parte, máximo de afirmações por julgamento e palavras de alto impacto (valores, prazos).
- A fachada `service.py` expõe `extrair_afirmacoes`, `agrupar_assuntos`, `julgar_assunto` e `montar_relatorio_contradicoes`.

#### Migrations

- Revisão `0038_contradicoes`, encadeada após a revisão `0037_limpeza_dominio` (`down_revision = "0037_limpeza_dominio"`): cria `analises_contradicao` e `ocorrencias_contradicao`; downgrade remove na ordem inversa; sem backfill.

#### Models

- `AnaliseContradicao`: `id`, `colecao_id`, `situacao` (`em_andamento`, `concluida`, `incompleta`), `motivo` seguro, `iniciada_por`, `provedor`, `dominio_versao_id`, `total_assuntos`, `concluidos`, `documentos_analisados`, `criado_em`, `concluido_em`, `expira_em`.
- `OcorrenciaContradicao`: `id`, `analise_id`, `assunto`, `assunto_normalizado`, `etiqueta`, `impacto`, `trechos` (JSON com arquivo, documento, trecho e referência de imagem opcional), `explicacao`, `criado_em`; único (`analise_id`, `assunto_normalizado`, `chave_trechos`) para idempotência.
- Arquivo: `src/app/models.py`.

#### Controllers e casos de uso

- `src/app/routers/colecoes.py` (ou novo `contradicoes.py`): `POST /api/v1/colecoes/{id}/contradicoes/analises` (202; owner/admin; exige confirmação do aviso), `POST /api/v1/colecoes/{id}/contradicoes/analises/{aid}/continuar`, `GET /api/v1/colecoes/{id}/contradicoes` (última análise com ocorrências, `?etiqueta=`; qualquer papel), `GET /api/v1/colecoes/{id}/contradicoes/relatorio?formato=md|pdf` (owner/admin).
- Erros: 403 (papel), 404 (coleção), 409 (análise ativa ou IA não permitida), 422 (coleção vazia).

#### Views e experiência

- Detalhado na seção 10.

#### Queries e repositórios

- `src/app/repo.py`: análise mais recente da coleção, ocorrências por análise com filtro de etiqueta e ordenação por impacto, assuntos concluídos da análise, expiração; índices em `ocorrencias_contradicao(analise_id)` e `analises_contradicao(colecao_id, criado_em)`.

#### Jobs e processamento assíncrono

- `analisar_contradicoes_task(analise_id)`: processa uma parte por execução, se reenfileira até o fim; idempotente por assunto; falha vira `incompleta` com motivo seguro.
- `purgar_contradicoes_task` (cron diário): apaga análises e ocorrências com mais de 90 dias.

#### Estrutura de arquivos

```text
specs/draft/0038-fase-1-detectar-contradicoes-e-relatorio/
  spec.md
  research/
src/pipeline/contradicoes/{__init__,contratos,afirmacoes,assuntos,julgamento,relatorio}.py
src/app/contradicoes.py
alembic/versions/0038_contradicoes.py
tests/test_contradicoes_assuntos.py
tests/test_contradicoes_julgamento.py
tests/test_contradicoes_analise.py
tests/test_contradicoes_relatorio.py
tests/test_router_contradicoes.py
frontend/src/app/(autenticado)/workspaces/[id]/colecoes/[colecaoId]/contradicoes/page.tsx
frontend/src/features/contradicoes/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| AnaliseContradicao | `id` | `situacao`, `motivo`, `provedor`, `dominio_versao_id`, progresso, `expira_em` (90 dias); uma ativa por coleção | N:1 Colecao, N:1 Pessoa |
| OcorrenciaContradicao | `id`; único (`analise_id`, `assunto_normalizado`, `chave_trechos`) | `etiqueta` (`conflito`, `versao_desatualizada`, `duplicado`), `impacto`, `trechos` com pelo menos 2 itens, `explicacao` | N:1 AnaliseContradicao |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| AnaliseContradicao | (nova) | pedido confirmado | em_andamento | chave de IA ligada e coleção com documentos |
| AnaliseContradicao | em_andamento | todos os assuntos julgados | concluida | ocorrências gravadas |
| AnaliseContradicao | em_andamento | falha ou IA indisponível | incompleta | assuntos pendentes preservados |
| AnaliseContradicao | incompleta | "Continuar análise" | em_andamento | só assuntos pendentes |

#### Migração e retenção

- Migration aditiva `0038_contradicoes` com downgrade. Retenção de 90 dias; apagada junto com a coleção.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. Botão na página da coleção e rota própria do relatório.

#### Stack e convenções de interface

- Next.js (App Router) + React + TypeScript + Tailwind, shadcn/ui (Base UI), testes com Vitest e Testing Library. Telas atuais afetadas: página da coleção (`workspaces/[id]/colecoes/[colecaoId]/page.tsx`) e seu cabeçalho; `features/colecoes/` preservado. Fontes: `INTERFACE.md`, `DESIGNSYSTEM.MD`.

#### Telas e responsabilidades

- **Página da coleção**: ganha o botão "Analisar contradições" no cabeçalho (owner/admin), com `Dialog` de aviso de envio à IA.
- **Relatório de contradições** (`.../colecoes/{colecaoId}/contradicoes`): consultar o andamento e as ocorrências, filtrar por etiqueta, continuar a análise e baixar.

#### Fluxo de informação e navegação

- A pessoa abre a coleção → clica em "Analisar contradições" → confirma o aviso → é levada à rota do relatório, que acompanha o progresso → consulta, filtra e baixa. A trilha (Equipe → Workspaces → Workspace → Coleção → Contradições) volta à coleção.

#### Menus e navegação principal

- Sem item novo de menu principal: a rota é acessada pelo botão da coleção e pela trilha de navegação, pois pertence à coleção.

#### Formulários e ações

- Ações: "Analisar contradições" (com confirmação), "Continuar análise" (quando incompleta), filtro por etiqueta (grupo de botões de alternância), "Baixar Markdown" e "Baixar PDF" (owner/admin). Sem campos de formulário além do filtro.

#### Composição e disposição

- Cabeçalho com `PageHeader` único, aviso de andamento no topo, filtros, e lista de assuntos com cartões; cada cartão traz assunto e etiqueta no topo, dois trechos lado a lado (empilhados no celular), nome do arquivo e explicação.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Coleção | `BotaoAnalisarContradicoes` | Botão e `Dialog` de aviso e confirmação | `frontend/src/features/contradicoes/BotaoAnalisarContradicoes.tsx` | `Button`, `Dialog` | shadcn/ui + próprio | Novo; segue `ApagarColecaoDialog` |
| Relatório | `RelatorioContradicoes` | Compõe aviso, filtros, assuntos e estados | `frontend/src/features/contradicoes/RelatorioContradicoes.tsx` | `PageHeader` único | próprio | Novo; reusa `PageHeader` |
| Relatório | `AvisoAnalise` | Andamento, incompleta e motivo | `frontend/src/features/contradicoes/AvisoAnalise.tsx` | `Alert` | shadcn/ui + próprio | Novo; segue `AvisosLimpeza` (SPEC-0037) |
| Relatório | `FiltroEtiquetas` | Filtro por etiqueta | `frontend/src/features/contradicoes/FiltroEtiquetas.tsx` | `Button` (alternância) | shadcn/ui + próprio | Novo |
| Relatório | `CartaoOcorrencia` | Assunto, etiqueta, trechos lado a lado e explicação | `frontend/src/features/contradicoes/CartaoOcorrencia.tsx` | `Badge` | shadcn/ui + próprio | Novo; extensível pela SPEC da BACKLOG-0043 |
| Relatório | `situacaoContradicao.ts` | Rótulos e variantes de etiqueta e situação | `frontend/src/features/contradicoes/situacaoContradicao.ts` | `Badge` | próprio | Novo; segue `situacao.ts` |

- Registrar cada bloco em `INTERFACE.md` com consumidores e origem; a página apenas compõe esses blocos.

#### Estados e acessibilidade

- Carregando com `aria-busy` e `Skeleton`; vazio "Nenhuma contradição encontrada" com o número de documentos analisados; erro em `Alert` com "Tentar novamente"; incompleta com "Continuar análise"; permissão insuficiente esconde as ações de escrita mantendo a leitura.
- Avisos em `role=status`, foco visível e preservado, teclado em todos os controles; o `Breadcrumb` mantém a equipe visível e marca a página atual.

#### Contrato CRUD

- Não há CRUD de entidade nova: o relatório é leitura de resultado de análise. O cabeçalho usa o `PageHeader` único; a listagem de coleções continua com o `DataGrid` existente (`DataGridColecoes`), largura total, coluna `ID`, linha-link e ações independentes de editar e apagar, sem mudanças. Os novos componentes entram em `INTERFACE.md`.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre em cada tarefa de interface, em desktop e 375 px, nos estados carregando, andamento, incompleta, vazio, erro e sucesso, conferindo bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD`. Tarefas de backend registram `Não aplicável` com motivo.

#### APIs expostas

- As quatro rotas da seção 8, sob `/api/v1`, autenticadas por sessão, com `require_write_role` nas escritas e no download.

#### APIs externas utilizadas

- IA de análise via `ChatModelAdapter` pela conexão do Workspace (SPEC-0037). Timeout e retry limitados; falha vira análise `incompleta`; nenhuma chamada com a chave desligada.

#### Documentação das APIs consultadas

- Nenhuma documentação externa; contrato local `ChatModelAdapter`.

#### Eventos e outros contratos

- Relatório Markdown com seções fixas (assunto, etiqueta, impacto, trechos, explicação, IA e versão do domínio) e PDF gerado do mesmo conteúdo.

### 11. Estratégia TDD

- **Unidade**: normalização e agrupamento de assuntos, ordenação por impacto, montagem do relatório, parsing da saída da IA, componentes React isolados.
- **Integração/contrato**: rotas com banco isolado, tarefa do worker com provider de IA falso e retomada, retenção com datas simuladas, migration `0038` com downgrade.
- **BDD/aceite**: o Gherkin da seção 6 informa o desenho de cada caso; nenhum `.feature` é criado.
- **Runner TDD**: projeto Python/Node misto sem PHP; usar os runners existentes: Pytest no backend e Vitest no frontend.
- **E2E**: jornada coleção → análise → relatório → download pelo cliente de teste da API, com provider falso; sem chamada externa real.
- **Verificação manual**: qualidade real da IA e o gabarito (opt-in, fora do repositório), pois dependem de provider pago e de dados que não podem ser versionados.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, US-002, FR-001, FR-003, FR-004, NFR-002, AC-001 | AC-001 na seção 6 | tests/test_contradicoes_analise.py: conflito entre dois arquivos (`SPECSFY: SPEC-0038 AC-001`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-002, FR-003, FR-004, NFR-002, AC-002 | AC-002 na seção 6 | tests/test_contradicoes_julgamento.py: versão desatualizada (`SPECSFY: SPEC-0038 AC-002`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-002, FR-003, FR-004, AC-003 | AC-003 na seção 6 | tests/test_contradicoes_julgamento.py: duplicado (`SPECSFY: SPEC-0038 AC-003`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-001, FR-001, FR-006, NFR-001, AC-004 | AC-004 na seção 6 | tests/test_router_contradicoes.py: sem chave de IA (`SPECSFY: SPEC-0038 AC-004`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-001, FR-001, FR-009, AC-005 | AC-005 na seção 6 | tests/test_router_contradicoes.py: member recusado (`SPECSFY: SPEC-0038 AC-005`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-001, FR-001, NFR-001, AC-006 | AC-006 na seção 6 | frontend/src/features/contradicoes/BotaoAnalisarContradicoes.test.tsx: aviso e confirmação (`SPECSFY: SPEC-0038 AC-006`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-001, FR-002, NFR-003, AC-007 | AC-007 na seção 6 | tests/test_contradicoes_assuntos.py: um julgamento por assunto (`SPECSFY: SPEC-0038 AC-007`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| FR-002, FR-003, NFR-002, AC-008 | AC-008 na seção 6 | tests/test_contradicoes_assuntos.py: assuntos diferentes (`SPECSFY: SPEC-0038 AC-008`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-001, FR-002, NFR-003, AC-009 | AC-009 na seção 6 | tests/test_contradicoes_assuntos.py: normalização do assunto (`SPECSFY: SPEC-0038 AC-009`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-003, FR-005, NFR-003, AC-010 | AC-010 na seção 6 | tests/test_contradicoes_analise.py: retomada sem refazer (`SPECSFY: SPEC-0038 AC-010`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-003, FR-005, FR-007, NFR-004, AC-011 | AC-011 na seção 6 | frontend/src/features/contradicoes/AvisoAnalise.test.tsx: incompleta acessível (`SPECSFY: SPEC-0038 AC-011`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-003, FR-005, NFR-003, AC-012 | AC-012 na seção 6 | tests/test_contradicoes_analise.py: 50 documentos em partes (`SPECSFY: SPEC-0038 AC-012`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-003, FR-005, FR-006, AC-013 | AC-013 na seção 6 | tests/test_contradicoes_analise.py: IA indisponível (`SPECSFY: SPEC-0038 AC-013`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-001, FR-006, AC-014 | AC-014 na seção 6 | tests/test_router_contradicoes.py: coleção vazia (`SPECSFY: SPEC-0038 AC-014`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-005, FR-007, AC-015 | AC-015 na seção 6 | frontend/src/features/contradicoes/RelatorioContradicoes.test.tsx: impacto e filtro (`SPECSFY: SPEC-0038 AC-015`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-005, FR-004, FR-007, AC-016 | AC-016 na seção 6 | frontend/src/features/contradicoes/RelatorioContradicoes.test.tsx: estado vazio (`SPECSFY: SPEC-0038 AC-016`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-004, FR-008, AC-017 | AC-017 na seção 6 | tests/test_contradicoes_relatorio.py: Markdown (`SPECSFY: SPEC-0038 AC-017`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-004, FR-008, AC-018 | AC-018 na seção 6 | tests/test_contradicoes_relatorio.py: PDF (`SPECSFY: SPEC-0038 AC-018`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-004, US-005, FR-008, FR-009, AC-019 | AC-019 na seção 6 | tests/test_router_contradicoes.py: member consulta e não baixa (`SPECSFY: SPEC-0038 AC-019`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-004, FR-009, NFR-001, AC-020 | AC-020 na seção 6 | tests/test_contradicoes_analise.py: retenção e metadados (`SPECSFY: SPEC-0038 AC-020`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-005, FR-007, NFR-004, AC-021 | AC-021 na seção 6 | frontend/src/features/contradicoes/CartaoOcorrencia.test.tsx: 375 px e teclado (`SPECSFY: SPEC-0038 AC-021`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |
| US-005, NFR-004, AC-022 | AC-022 na seção 6 | frontend/src/features/contradicoes/AvisoAnalise.test.tsx: anúncio de andamento (`SPECSFY: SPEC-0038 AC-022`) | Observado em 2026-10-16: falha por comportamento ausente (módulo ou componente inexistente) | Passed em 2026-10-16 | Regressão: pytest 743 passed e vitest 265 passed |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | tests/test_contradicoes_analise.py | Passed |
| FR-001 | AC-004 | Contrato | tests/test_router_contradicoes.py | Passed |
| FR-001 | AC-005 | Contrato | tests/test_router_contradicoes.py | Passed |
| FR-001 | AC-006 | Componente | frontend/src/features/contradicoes/BotaoAnalisarContradicoes.test.tsx | Passed |
| FR-002 | AC-007 | Unidade | tests/test_contradicoes_assuntos.py | Passed |
| FR-002 | AC-008 | Unidade | tests/test_contradicoes_assuntos.py | Passed |
| FR-002 | AC-009 | Unidade | tests/test_contradicoes_assuntos.py | Passed |
| FR-003 | AC-001 | Integração | tests/test_contradicoes_analise.py | Passed |
| FR-003 | AC-002 | Unidade | tests/test_contradicoes_julgamento.py | Passed |
| FR-003 | AC-003 | Unidade | tests/test_contradicoes_julgamento.py | Passed |
| FR-004 | AC-001 | Integração | tests/test_contradicoes_analise.py | Passed |
| FR-004 | AC-002 | Unidade | tests/test_contradicoes_julgamento.py | Passed |
| FR-004 | AC-003 | Unidade | tests/test_contradicoes_julgamento.py | Passed |
| FR-005 | AC-010 | Integração | tests/test_contradicoes_analise.py | Passed |
| FR-005 | AC-012 | Integração | tests/test_contradicoes_analise.py | Passed |
| FR-005 | AC-013 | Integração | tests/test_contradicoes_analise.py | Passed |
| FR-006 | AC-004 | Contrato | tests/test_router_contradicoes.py | Passed |
| FR-006 | AC-013 | Integração | tests/test_contradicoes_analise.py | Passed |
| FR-006 | AC-014 | Contrato | tests/test_router_contradicoes.py | Passed |
| FR-007 | AC-011 | Componente | frontend/src/features/contradicoes/AvisoAnalise.test.tsx | Passed |
| FR-007 | AC-015 | Componente | frontend/src/features/contradicoes/RelatorioContradicoes.test.tsx | Passed |
| FR-007 | AC-016 | Componente | frontend/src/features/contradicoes/RelatorioContradicoes.test.tsx | Passed |
| FR-008 | AC-017 | Unidade | tests/test_contradicoes_relatorio.py | Passed |
| FR-008 | AC-018 | Unidade | tests/test_contradicoes_relatorio.py | Passed |
| FR-008 | AC-019 | Contrato | tests/test_router_contradicoes.py | Passed |
| FR-009 | AC-005 | Contrato | tests/test_router_contradicoes.py | Passed |
| FR-009 | AC-019 | Contrato | tests/test_router_contradicoes.py | Passed |
| FR-009 | AC-020 | Integração | tests/test_contradicoes_analise.py | Passed |
| NFR-001 | AC-004 | Contrato | tests/test_router_contradicoes.py | Passed |
| NFR-001 | AC-006 | Componente | frontend/src/features/contradicoes/BotaoAnalisarContradicoes.test.tsx | Passed |
| NFR-001 | AC-020 | Integração | tests/test_contradicoes_analise.py | Passed |
| NFR-002 | AC-001 | Integração | tests/test_contradicoes_analise.py | Passed |
| NFR-002 | AC-002 | Unidade | tests/test_contradicoes_julgamento.py | Passed |
| NFR-002 | AC-008 | Unidade | tests/test_contradicoes_assuntos.py | Passed |
| NFR-003 | AC-007 | Unidade | tests/test_contradicoes_assuntos.py | Passed |
| NFR-003 | AC-010 | Integração | tests/test_contradicoes_analise.py | Passed |
| NFR-003 | AC-012 | Integração | tests/test_contradicoes_analise.py | Passed |
| NFR-004 | AC-011 | Componente | frontend/src/features/contradicoes/AvisoAnalise.test.tsx | Passed |
| NFR-004 | AC-021 | Componente | frontend/src/features/contradicoes/CartaoOcorrencia.test.tsx | Passed |
| NFR-004 | AC-022 | Componente | frontend/src/features/contradicoes/AvisoAnalise.test.tsx | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed (READY, 2026-10-16)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0038-fase-1-detectar-contradicoes-e-relatorio/spec.md`
- **Achados**: 0 BLOCKER. Cobertura conferida: feature, cada US, FR e NFR têm pelo menos 3 AC em `**Cobre**`. NOTE: nomes citados conferidos no código (`require_write_role`, `DocumentoColecao.ultimo_envio_id`, revisão `0037_limpeza_dominio`). WARNING aceito: qualidade real da IA e meta de 90% só medidas no gabarito opt-in (DEC-007).

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-16)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0038-fase-1-detectar-contradicoes-e-relatorio/spec.md`
- **Achados**: 37 tarefas (22 TDD, 11 código, 3 doc/ops); 40 de 40 IDs cobertos; 22 testes RED observados (20 em Pytest e 12 casos em Vitest, todos por comportamento ausente). Contratos assumidos documentados em `tests/_fase1_contradicoes.py`.

#### Gate do Ato III — Entrega

- **Resultado**: Passed (2026-10-16)
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0038-fase-1-detectar-contradicoes-e-relatorio/spec.md . --full-chain`
- **Achados**: 37 de 37 tarefas concluídas; pytest 743 passed e 1 skipped; vitest 265 passed; ruff, ESLint, `tsc` e build limpos. Revisão visual por inspeção de DOM e classes (sem navegador real). A medição do gabarito (meta de 90%, parâmetros de agrupamento e tamanho das partes) permanece como verificação final opt-in (DEC-007).

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso de teste falhando em tests/test_contradicoes_analise.py — Refs: US-001, US-002, FR-001, FR-003, FR-004, NFR-002, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-001`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_analise.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T002 [TEST] [TDD] [US-002] Derivar do AC-002 um caso de teste falhando em tests/test_contradicoes_julgamento.py — Refs: US-002, FR-003, FR-004, NFR-002, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-002`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_julgamento.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T003 [TEST] [TDD] [US-002] Derivar do AC-003 um caso de teste falhando em tests/test_contradicoes_julgamento.py — Refs: US-002, FR-003, FR-004, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-003`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_julgamento.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso de teste falhando em tests/test_router_contradicoes.py — Refs: US-001, FR-001, FR-006, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-004`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_contradicoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 um caso de teste falhando em tests/test_router_contradicoes.py — Refs: US-001, FR-001, FR-009, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-005`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_contradicoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-006 um caso de teste falhando em frontend/src/features/contradicoes/BotaoAnalisarContradicoes.test.tsx — Refs: US-001, FR-001, NFR-001, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-006`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: npx vitest run frontend/src/features/contradicoes/BotaoAnalisarContradicoes.test.tsx em 2026-10-16; causa do RED: componente em frontend/src/features/contradicoes ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T007 [TEST] [TDD] [US-001] Derivar do AC-007 um caso de teste falhando em tests/test_contradicoes_assuntos.py — Refs: US-001, FR-002, NFR-003, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-007`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_assuntos.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T008 [TEST] [TDD] Derivar do AC-008 um caso de teste falhando em tests/test_contradicoes_assuntos.py — Refs: FR-002, FR-003, NFR-002, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-008`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_assuntos.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T009 [TEST] [TDD] [US-001] Derivar do AC-009 um caso de teste falhando em tests/test_contradicoes_assuntos.py — Refs: US-001, FR-002, NFR-003, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-009`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_assuntos.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-010 um caso de teste falhando em tests/test_contradicoes_analise.py — Refs: US-003, FR-005, NFR-003, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-010`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_analise.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 um caso de teste falhando em frontend/src/features/contradicoes/AvisoAnalise.test.tsx — Refs: US-003, FR-005, FR-007, NFR-004, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-011`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: npx vitest run frontend/src/features/contradicoes/AvisoAnalise.test.tsx em 2026-10-16; causa do RED: componente em frontend/src/features/contradicoes ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso de teste falhando em tests/test_contradicoes_analise.py — Refs: US-003, FR-005, NFR-003, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-012`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_analise.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-013 um caso de teste falhando em tests/test_contradicoes_analise.py — Refs: US-003, FR-005, FR-006, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-013`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_analise.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T014 [TEST] [TDD] [US-001] Derivar do AC-014 um caso de teste falhando em tests/test_router_contradicoes.py — Refs: US-001, FR-006, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-014`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_contradicoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T015 [TEST] [TDD] [US-005] Derivar do AC-015 um caso de teste falhando em frontend/src/features/contradicoes/RelatorioContradicoes.test.tsx — Refs: US-005, FR-007, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-015`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: npx vitest run frontend/src/features/contradicoes/RelatorioContradicoes.test.tsx em 2026-10-16; causa do RED: componente em frontend/src/features/contradicoes ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T016 [TEST] [TDD] [US-005] Derivar do AC-016 um caso de teste falhando em frontend/src/features/contradicoes/RelatorioContradicoes.test.tsx — Refs: US-005, FR-004, FR-007, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-016`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: npx vitest run frontend/src/features/contradicoes/RelatorioContradicoes.test.tsx em 2026-10-16; causa do RED: componente em frontend/src/features/contradicoes ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T017 [TEST] [TDD] [US-004] Derivar do AC-017 um caso de teste falhando em tests/test_contradicoes_relatorio.py — Refs: US-004, FR-008, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-017`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_relatorio.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T018 [TEST] [TDD] [US-004] Derivar do AC-018 um caso de teste falhando em tests/test_contradicoes_relatorio.py — Refs: US-004, FR-008, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-018`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_relatorio.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T019 [TEST] [TDD] [US-004] Derivar do AC-019 um caso de teste falhando em tests/test_router_contradicoes.py — Refs: US-004, US-005, FR-008, FR-009, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-019`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_contradicoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T020 [TEST] [TDD] [US-004] Derivar do AC-020 um caso de teste falhando em tests/test_contradicoes_analise.py — Refs: US-004, FR-009, NFR-001, AC-020 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-020`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_contradicoes_analise.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.contradicoes/src.app.contradicoes ou modelo AnaliseContradicao ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T021 [TEST] [TDD] [US-005] Derivar do AC-021 um caso de teste falhando em frontend/src/features/contradicoes/CartaoOcorrencia.test.tsx — Refs: US-005, FR-007, NFR-004, AC-021 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-021`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: npx vitest run frontend/src/features/contradicoes/CartaoOcorrencia.test.tsx em 2026-10-16; causa do RED: componente em frontend/src/features/contradicoes ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.

- [x] T022 [TEST] [TDD] [US-005] Derivar do AC-022 um caso de teste falhando em frontend/src/features/contradicoes/AvisoAnalise.test.tsx — Refs: US-005, NFR-004, AC-022 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0038 AC-022`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: npx vitest run frontend/src/features/contradicoes/AvisoAnalise.test.tsx em 2026-10-16; causa do RED: componente em frontend/src/features/contradicoes ausente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_contradicoes.py.


#### Fase 2 — Entrega GREEN

- [x] T023 [CODE] [US-003] Criar migration e modelos de análise e ocorrência em alembic/versions/0038_contradicoes.py e src/app/models.py — Refs: AC-010, AC-012, AC-020, FR-005, FR-009, NFR-001, NFR-003, US-003, US-004 — Depends: T010, T012, T020
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_app_migrations.py tests/test_contradicoes_analise.py` e a regressão relacionada.
  - [x] **VISUAL**: Não aplicável: persistência sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_app_migrations.py tests/test_contradicoes_analise.py -q` em 2026-10-16: 20 testes verdes (migration 0038 com upgrade/downgrade e retenção); IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T023", "refs": ["AC-010", "AC-012", "AC-020", "FR-005", "FR-009", "NFR-001", "NFR-003", "US-003", "US-004"], "files": ["alembic/versions/0038_contradicoes.py", "src/app/models.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_app_migrations.py tests/test_contradicoes_analise.py -q", "exit": 0}]} -->

- [x] T024 [DOC] Atualizar .specsfy/DATABASE.md com analises_contradicao e ocorrencias_contradicao — Refs: AC-010, AC-012, AC-020, FR-005, FR-009, NFR-001, NFR-003, US-003, US-004 — Depends: T023
  - [x] **PREP**: Confirmar escopo, IDs e dependências.
  - [x] **EXECUTE**: Produzir a entrega no caminho declarado.
  - [x] **VERIFY**: Executar o check correspondente.
  - [x] **VISUAL**: Não aplicável: documentação de persistência.
  - [x] **EVIDENCE**: Documento atualizado e conferido; `build_documentation.mjs --check` exit 0 e `monitor_context.mjs --check` CURRENT em 2026-10-16.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.

- [x] T025 [CODE] [US-001] Implementar contratos, normalização e agrupamento por assunto em src/pipeline/contradicoes/contratos.py e assuntos.py — Refs: AC-007, AC-008, AC-009, FR-002, FR-003, NFR-002, NFR-003, US-001 — Depends: T007, T008, T009
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_contradicoes_assuntos.py` e a regressão relacionada.
  - [x] **VISUAL**: Não aplicável: lógica pura sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_contradicoes_assuntos.py -q` em 2026-10-16: 3 passed; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T025", "refs": ["AC-007", "AC-008", "AC-009", "FR-002", "FR-003", "NFR-002", "NFR-003", "US-001"], "files": ["src/pipeline/contradicoes/contratos.py", "src/pipeline/contradicoes/assuntos.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_contradicoes_assuntos.py -q", "exit": 0}]} -->

- [x] T026 [CODE] [US-001] Implementar extração de afirmações e julgamento por assunto em src/pipeline/contradicoes/afirmacoes.py e julgamento.py — Refs: AC-001, AC-002, AC-003, FR-001, FR-003, FR-004, NFR-002, US-001, US-002 — Depends: T001, T002, T003, T025
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_contradicoes_julgamento.py` e a regressão relacionada.
  - [x] **VISUAL**: Não aplicável: lógica de IA sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_contradicoes_julgamento.py -q` em 2026-10-16: 3 passed; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T026", "refs": ["AC-001", "AC-002", "AC-003", "FR-001", "FR-003", "FR-004", "NFR-002", "US-001", "US-002"], "files": ["src/pipeline/contradicoes/afirmacoes.py", "src/pipeline/contradicoes/julgamento.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_contradicoes_julgamento.py -q", "exit": 0}]} -->

- [x] T027 [CODE] [US-004] Implementar relatório em Markdown e PDF em src/pipeline/contradicoes/relatorio.py — Refs: AC-016, AC-017, AC-018, FR-004, FR-007, FR-008, US-004, US-005 — Depends: T016, T017, T018, T025
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_contradicoes_relatorio.py` e a regressão relacionada.
  - [x] **VISUAL**: Não aplicável: geração de arquivo; o PDF será inspecionado como texto extraído.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_contradicoes_relatorio.py -q` em 2026-10-16: 3 passed; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T027", "refs": ["AC-016", "AC-017", "AC-018", "FR-004", "FR-007", "FR-008", "US-004", "US-005"], "files": ["src/pipeline/contradicoes/relatorio.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_contradicoes_relatorio.py -q", "exit": 0}]} -->

- [x] T028 [CODE] [US-001] Expor a fachada em src/pipeline/service.py (extrair_afirmacoes, agrupar_assuntos, julgar_assunto, montar_relatorio_contradicoes) — Refs: AC-007, FR-002, NFR-003, US-001 — Depends: T007, T025, T026, T027
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_contradicoes_assuntos.py tests/test_architecture.py` e a regressão relacionada.
  - [x] **VISUAL**: Não aplicável: fachada sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_contradicoes_assuntos.py tests/test_application_boundaries.py tests/test_provider_boundaries.py tests/test_validation_boundaries.py -q` em 2026-10-16: suítes de fronteira e agrupamento passed; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T028", "refs": ["AC-007", "FR-002", "NFR-003", "US-001"], "files": ["src/pipeline/service.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_contradicoes_assuntos.py tests/test_application_boundaries.py tests/test_provider_boundaries.py tests/test_validation_boundaries.py -q", "exit": 0}]} -->

- [x] T029 [CODE] [US-001] Orquestrar a análise em partes, retomada e retenção em src/app/contradicoes.py, src/app/repo.py e src/app/tasks.py — Refs: AC-001, AC-010, AC-012, AC-013, AC-020, FR-001, FR-003, FR-004, FR-005, FR-006, FR-009, NFR-001, NFR-002, NFR-003, US-001, US-002, US-003, US-004 — Depends: T010, T012, T013, T020, T001, T023, T028
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_contradicoes_analise.py` e a regressão relacionada.
  - [x] **VISUAL**: Não aplicável: processamento em segundo plano.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_contradicoes_analise.py -q` em 2026-10-16: 5 passed; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T029", "refs": ["AC-001", "AC-010", "AC-012", "AC-013", "AC-020", "FR-001", "FR-003", "FR-004", "FR-005", "FR-006", "FR-009", "NFR-001", "NFR-002", "NFR-003", "US-001", "US-002", "US-003", "US-004"], "files": ["src/app/contradicoes.py", "src/app/repo.py", "src/app/tasks.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_contradicoes_analise.py -q", "exit": 0}]} -->

- [x] T030 [CODE] [US-001] Criar as rotas de análise, relatório e download em src/app/routers/contradicoes.py e registrá-las em src/app/main.py — Refs: AC-004, AC-005, AC-014, AC-019, FR-001, FR-006, FR-008, FR-009, NFR-001, US-001, US-004, US-005 — Depends: T004, T005, T014, T019, T029
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_router_contradicoes.py` e a regressão relacionada.
  - [x] **VISUAL**: Não aplicável: API sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_router_contradicoes.py -q` em 2026-10-16: 6 passed; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T030", "refs": ["AC-004", "AC-005", "AC-014", "AC-019", "FR-001", "FR-006", "FR-008", "FR-009", "NFR-001", "US-001", "US-004", "US-005"], "files": ["src/app/routers/contradicoes.py", "src/app/main.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_router_contradicoes.py -q", "exit": 0}]} -->


#### Fase de interface

- [x] T031 [CODE] [US-003] Criar rótulos de etiqueta e AvisoAnalise em frontend/src/features/contradicoes/situacaoContradicao.ts e AvisoAnalise.tsx — Refs: AC-011, AC-022, FR-005, FR-007, NFR-004, US-003, US-005 — Depends: T011, T022, T030
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `frontend vitest AvisoAnalise` e a regressão relacionada.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do Alert contra DESIGNSYSTEM.MD em 375 px e desktop nos estados andamento, incompleta, concluída e erro. Resultado (2026-10-16): conferido por inspeção de DOM e classes contra DESIGNSYSTEM.MD, sem navegador real (limitação registrada); sem divergências.
  - [x] **EVIDENCE**: `npx vitest run src/features/contradicoes/AvisoAnalise.test.tsx` em 2026-10-16: 3 passed; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T031", "refs": ["AC-011", "AC-022", "FR-005", "FR-007", "NFR-004", "US-003", "US-005"], "files": ["frontend/src/features/contradicoes/situacaoContradicao.ts", "frontend/src/features/contradicoes/AvisoAnalise.tsx"], "commands": [{"run": "npx vitest run src/features/contradicoes/AvisoAnalise.test.tsx", "exit": 0}]} -->

- [x] T032 [CODE] [US-001] Criar BotaoAnalisarContradicoes com aviso de envio à IA em frontend/src/features/contradicoes/BotaoAnalisarContradicoes.tsx — Refs: AC-006, FR-001, NFR-001, US-001 — Depends: T006, T030
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `frontend vitest BotaoAnalisarContradicoes` e a regressão relacionada.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do Dialog e dos botões, além do foco, contra DESIGNSYSTEM.MD em 375 px e desktop. Resultado (2026-10-16): conferido por inspeção de DOM e classes contra DESIGNSYSTEM.MD, sem navegador real (limitação registrada); sem divergências.
  - [x] **EVIDENCE**: `npx vitest run src/features/contradicoes/BotaoAnalisarContradicoes.test.tsx` em 2026-10-16: 3 passed; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T032", "refs": ["AC-006", "FR-001", "NFR-001", "US-001"], "files": ["frontend/src/features/contradicoes/BotaoAnalisarContradicoes.tsx"], "commands": [{"run": "npx vitest run src/features/contradicoes/BotaoAnalisarContradicoes.test.tsx", "exit": 0}]} -->

- [x] T033 [CODE] [US-005] Criar CartaoOcorrencia com trechos lado a lado em frontend/src/features/contradicoes/CartaoOcorrencia.tsx — Refs: AC-015, AC-016, AC-021, FR-004, FR-007, NFR-004, US-005 — Depends: T015, T016, T021, T030
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `frontend vitest CartaoOcorrencia` e a regressão relacionada.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia, quebra de palavras longas e empilhamento em 375 px contra DESIGNSYSTEM.MD. Resultado (2026-10-16): conferido por inspeção de DOM e classes contra DESIGNSYSTEM.MD, sem navegador real (limitação registrada); sem divergências.
  - [x] **EVIDENCE**: `npx vitest run src/features/contradicoes/CartaoOcorrencia.test.tsx` em 2026-10-16: 3 passed; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T033", "refs": ["AC-015", "AC-016", "AC-021", "FR-004", "FR-007", "NFR-004", "US-005"], "files": ["frontend/src/features/contradicoes/CartaoOcorrencia.tsx"], "commands": [{"run": "npx vitest run src/features/contradicoes/CartaoOcorrencia.test.tsx", "exit": 0}]} -->

- [x] T034 [CODE] [US-005] Criar FiltroEtiquetas, RelatorioContradicoes e a rota .../colecoes/[colecaoId]/contradicoes/page.tsx e ligar o botão ao cabeçalho da coleção — Refs: AC-015, AC-016, FR-004, FR-007, US-005 — Depends: T015, T016, T031, T032, T033
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `frontend vitest RelatorioContradicoes` e a regressão relacionada.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do PageHeader e dos filtros, estados vazio/erro/carregando e navegação por teclado em 375 px e desktop. Resultado (2026-10-16): conferido por inspeção de DOM e classes contra DESIGNSYSTEM.MD, sem navegador real (limitação registrada); sem divergências.
  - [x] **EVIDENCE**: `npx vitest run src/features/contradicoes` em 2026-10-16: 12 passed (4 arquivos); IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.
  <!-- specsfy:evidence {"task": "T034", "refs": ["AC-015", "AC-016", "FR-004", "FR-007", "US-005"], "files": ["frontend/src/features/contradicoes/FiltroEtiquetas.tsx", "frontend/src/features/contradicoes/RelatorioContradicoes.tsx", "frontend/src/app/(autenticado)/workspaces/[id]/colecoes/[colecaoId]/contradicoes/page.tsx", "frontend/src/app/(autenticado)/workspaces/[id]/colecoes/[colecaoId]/page.tsx"], "commands": [{"run": "npx vitest run src/features/contradicoes", "exit": 0}]} -->

- [x] T035 [DOC] Registrar os blocos novos em INTERFACE.md e as operações da fachada em docs/architecture.md — Refs: AC-015, AC-016, FR-004, FR-007, US-005 — Depends: T034
  - [x] **PREP**: Confirmar escopo, IDs e dependências.
  - [x] **EXECUTE**: Produzir a entrega no caminho declarado.
  - [x] **VERIFY**: Executar o check correspondente.
  - [x] **VISUAL**: Não aplicável: documentação.
  - [x] **EVIDENCE**: Documento atualizado e conferido; `build_documentation.mjs --check` exit 0 e `monitor_context.mjs --check` CURRENT em 2026-10-16.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.

- [x] T036 [DOC] Revisar PROJECT.md e reconstruir docs/ com o documentador — Refs: AC-015, AC-016, FR-004, FR-007, US-005 — Depends: T035
  - [x] **PREP**: Confirmar escopo, IDs e dependências.
  - [x] **EXECUTE**: Produzir a entrega no caminho declarado.
  - [x] **VERIFY**: Executar o check correspondente.
  - [x] **VISUAL**: Não aplicável: documentação.
  - [x] **EVIDENCE**: Documento atualizado e conferido; `build_documentation.mjs --check` exit 0 e `monitor_context.mjs --check` CURRENT em 2026-10-16.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.

- [x] T037 [OPS] Executar a regressão completa (pytest, ruff, vitest, eslint, tsc, build) e a rastreabilidade com tests/test_spec_markers.py — Refs: AC-015, AC-016, FR-004, FR-007, US-005 — Depends: T036
  - [x] **PREP**: Confirmar escopo, IDs e dependências.
  - [x] **EXECUTE**: Produzir a entrega no caminho declarado.
  - [x] **VERIFY**: Executar o check correspondente.
  - [x] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia por inspeção de DOM e classes nos estados do relatório; registrar a limitação de não haver navegador real. Resultado (2026-10-16): conferido por inspeção de DOM e classes contra DESIGNSYSTEM.MD, sem navegador real (limitação registrada); sem divergências.
  - [x] **EVIDENCE**: pytest completo: 743 passed, 1 skipped (opt-in pago); vitest: 265 passed; ruff, ESLint, tsc e `npm run build` limpos; `check_traceability --full-chain` e `verify_acceptance` conferidos nas seções 12 e 13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão da SPEC-0037.

### 15. Ordem de execução

- Caminho crítico: T001–T022 (RED) → T023 (migration) → T025 (assuntos) → T026/T027 (julgamento e relatório) → T028 (fachada) → T029 (orquestração) → T030 (rotas) → T031–T034 (interface) → T035/T036 (documentação) → T037 (regressão).
- Tarefas paralelas: as tarefas `[TEST] [TDD]` não compartilham estado e podem ser escritas em paralelo; T026 e T027 não compartilham arquivos; T031, T032 e T033 são componentes independentes.
- Estratégia de MVP: US-001 e US-002 primeiro (análise e ocorrências), depois US-003, US-004 e US-005.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0037: conexão de IA por Workspace, chave de IA externa, resumo do domínio, papéis e a regra de limpeza anterior à análise.
- SPEC-0030 (coleções) e SPEC-0031 (conteúdo processado).
- BACKLOG-0043 consome as ocorrências desta spec.
- Gabarito de documentos reais, fora do repositório, para a meta de 90%.

#### Riscos

- Falso alarme enche o relatório → agrupamento por assunto, etiquetas e filtro; a decisão final é sempre da empresa.
- Contradição perdida passa para a base → meta de 90% medida contra o gabarito e relatório que marca assuntos "não classificados".
- Custo e latência da IA em coleções grandes → um julgamento por assunto, partes limitadas e processamento em segundo plano.
- Vazamento de conteúdo de cliente → chave por Workspace, aviso antes do envio, provider espião nos testes e ausência de texto em logs.

#### Suposições

- Os `.md` analisados são os da versão atual de cada documento da coleção, lidos do armazenamento do último envio.
- O agrupamento por assunto usa o assunto normalizado (caixa, acentos, pontuação e ordem de palavras) mais a semelhança textual da SPEC-0037; reversível se o gabarito mostrar agrupamentos ruins.
- O tamanho de cada parte e o máximo de afirmações por julgamento são configuráveis, com padrões a calibrar no gabarito.
- Impacto alto significa afirmação com valor monetário, percentual ou prazo; a lista de palavras é configurável.
- A referência de imagem de origem só aparece quando o próprio `.md` a trouxer (BACKLOG-0040 amplia isso).
- Apenas uma análise ativa por coleção por vez.

### 17. Decisões

- **DEC-001**: detectar por afirmações agrupadas por assunto e um julgamento por assunto — alternativa descartada: comparar todos os pares, por custo quadrático.
- **DEC-002**: análise só a pedido, sobre os `.md` já limpos, com aviso de envio à IA — evita falsas contradições de ruído e vazamento sem consentimento.
- **DEC-003**: a análise nunca escreve nos documentos; a correção é da BACKLOG-0043.
- **DEC-004**: PDF gerado com `pymupdf` (já dependência) a partir do mesmo conteúdo do Markdown — alternativa descartada: nova biblioteca de PDF, por mais uma dependência; reversível.
- **DEC-005**: papéis conforme a DEC-007 da SPEC-0037: owner e admin escrevem e baixam, member consulta.
- **DEC-006**: relatório guardado por 90 dias e apagado com a coleção — alinhado a `.specsfy/DATABASE.md`.
- **DEC-007** (confirmada pela pessoa responsável em 2026-10-16): o gabarito é verificação final opt-in na entrega, com o conjunto que a pessoa trouxer, e não condição da definição; a meta de 90% é medida na entrega e os parâmetros seguem configuráveis.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
