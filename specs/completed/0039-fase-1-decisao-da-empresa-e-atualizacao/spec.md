# Especificação integrada: Fase 1: decisão da empresa e atualização dos Markdown

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0039 |
| Slug | 0039-fase-1-decisao-da-empresa-e-atualizacao |
| Status | Complete |
| Effort | 8 |
| Effort updated at | 2026-10-16 |
| Effort rationale | Interpretação de resposta livre por IA, localização exata do trecho, escrita com checkpoint humano, versionamento com histórico, reenvio à base vetorial, novo ciclo e liberação; alto risco de a IA reescrever mais que o pedido e dependência das SPEC-0037 e SPEC-0038. |
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

Depois que o relatório de contradições vai à empresa e ela decide o que vale, nada no sistema traz essa decisão de volta: os `.md` continuam contraditórios e a base vetorial indexaria informação não validada. Hoje a pessoa da consultoria teria de editar cada arquivo à mão e perderia o registro de quem decidiu o quê.

#### Resultado desejado

A pessoa cola a resposta da empresa; a IA propõe, contradição por contradição, qual versão vale; a pessoa confirma; o trecho que não vale é corrigido no próprio `.md` com histórico de versões e registro de decisões; uma nova análise mostra o que foi resolvido; e a coleção pode ser liberada como "revisada". Nenhuma escrita acontece sem confirmação humana explícita.

#### Métricas de sucesso

- Medido contra o gabarito de 3 ou 4 documentos reais da pessoa (fora do repositório): pelo menos 70% dos `.md` finais passam sem edição manual depois do primeiro ciclo. Verificação final opt-in na entrega (DEC-007): o gabarito ainda não foi entregue (é o mesmo das SPEC-0037 e SPEC-0038).
- 0 alterações em documentos sem confirmação humana registrada.
- 100% das correções aplicadas têm versão anterior preservada e registro de decisão.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: leitura do código das coleções e do envio (`src/app/models.py`, `src/app/colecoes.py`, `src/app/ingestao.py`, `src/app/routers/colecoes.py`) → o documento da coleção é identificado pelo nome do arquivo, tem uma versão atual (`DocumentoColecao`) e um novo envio com o mesmo nome o substitui e reindexa; é o caminho para publicar a versão corrigida (ver DEC-004).
- **R-002**: leitura da SPEC-0038 (`specs/review/0038-*/spec.md`, mergeada) e do código `src/app/contradicoes.py` → as ocorrências e seus trechos de origem são a entrada desta spec; o novo ciclo reutiliza a análise.

#### Fontes e contexto consultados

- `specs/backlog/0043-fase-1-conferencia-e-atualizacao.md` (Perguntas 1 a 8, interface e critérios).
- `specs/review/0037-*/spec.md` e `specs/review/0038-*/spec.md` (conexão de IA, domínio, papéis, relatório de contradições).
- `specs/milestones/M04.md`, `.specsfy/DATABASE.md` (versões do Markdown e decisões da empresa; situação e pendências por documento), `INTERFACE.md`, `DESIGNSYSTEM.MD`.
- `specs/completed/0030-*/spec.md` (coleções e envios acumulados) e `frontend/src/features/colecoes/`.

#### Documentação consultada

- Nenhuma documentação externa.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Como entra a resposta da empresa? → **A**: a pessoa cola o texto numa caixa ligada ao relatório; a IA propõe, por contradição, qual versão vale; anexos ficam para depois (backlog, Pergunta 1).
- **Q**: Como se confere? → **A**: a IA marca cada proposta "clara" ou "incerta"; as claras vêm pré-aprovadas num bloco e as incertas pedem decisão individual; nada muda sem confirmação (Pergunta 2).
- **Q**: Como se corrige? → **A**: o trecho que não vale é corrigido no próprio `.md` (Pergunta 3).
- **Q**: Como fica o histórico? → **A**: cada correção cria uma versão nova com a anterior preservada e um registro de decisões; é possível voltar a uma versão antiga (Pergunta 4).
- **Q**: Como é um novo ciclo? → **A**: cada reanálise é um clique em "Analisar contradições"; o sistema mostra o resolvido e o novo (Pergunta 5).
- **Q**: Como a coleção fica pronta? → **A**: botão "Liberar para a base" marca a coleção como "revisada"; pode liberar com contradições abertas, com aviso explícito (Pergunta 6).
- **Q**: Quem pode? → **A**: owner e admin fazem tudo; member consulta (Pergunta 7 e DEC-007 da SPEC-0037, 2026-10-16).
- **Q**: Qual a meta? → **A**: pelo menos 70% dos `.md` finais sem edição manual depois do primeiro ciclo, medido no gabarito (Pergunta 8).
- **Q**: Onde fica na interface? → **A**: na rota do relatório de contradições: caixa "Resposta da empresa", botão "Interpretar resposta", bloco de claras com "Confirmar todas", incertas individuais (Aceitar, Editar, Manter sem decisão), cartão "Corrigido" com "Ver versões", resumo de rodada, "Liberar para a base" com `Dialog` e histórico no detalhe do documento (2026-10-16, Interface, Perguntas 1 a 3).
- **Q**: E se a resposta não cobre tudo ou o trecho não é localizado? → **A**: fica "Sem decisão" e aberta; trecho não localizado vira "incerta" com mensagem e edição manual (2026-10-16, Interface, Pergunta 3).

#### Dúvidas abertas

- Nenhuma bloqueante. O gabarito e a confirmação da meta de 70% são verificação final opt-in na entrega, com o conjunto que a pessoa trouxer, e não condição da definição (DEC-007). A forma de localizar o trecho e o significado técnico de "revisada" entram como suposições reversíveis (seção 16).

### 3. Escopo e atores

#### Incluído

- Caixa de resposta da empresa e interpretação por IA, com proposta "clara" ou "incerta" por contradição.
- Conferência humana: bloco pré-aprovado, decisão individual (Aceitar, Editar, Manter sem decisão) e "Sem decisão".
- Aplicação da correção no `.md`, nova versão com a anterior preservada e registro de decisões.
- Volta a uma versão anterior com confirmação.
- Novo ciclo de análise com comparação (resolvido e novo).
- "Liberar para a base": marca a coleção como "revisada", com aviso quando há contradições abertas.
- Reenvio do `.md` corrigido à coleção (reindexação) quando a correção é aplicada.

#### Fora de escopo

- Detecção e relatório de contradições (SPEC-0038).
- Limpeza, domínio e conexão de IA (SPEC-0037).
- Anexos na resposta da empresa (imagem, PDF); a primeira versão aceita só texto colado.
- Contato com a empresa pelo sistema: a conferência com ela acontece fora.
- Papel novo de permissão.
- Alterar chunking, embeddings ou configuração da coleção.

#### Atores

- **Owner e admin (papel de escrita)**: colam a resposta, interpretam, confirmam, editam propostas, voltam versões e liberam a coleção.
- **Member**: consulta o relatório, as propostas e o histórico; não escreve.
- **IA de interpretação**: modelo externo da conexão do Workspace; mapeia a resposta às contradições e propõe a correção.
- **Empresa cliente**: decide fora do sistema; sua resposta entra como texto colado.

### 4. Princípios e restrições do projeto

- **PR-001**: nenhuma escrita em `.md` sem confirmação humana explícita registrada.
- **PR-002**: a correção altera somente o trecho alvo; o resto do documento permanece byte a byte igual.
- **PR-003**: o texto da resposta da empresa só vai à IA externa após o clique, com aviso e com a chave do Workspace ligada.
- **PR-004**: toda fronteira com IA passa pelo contrato `ChatModelAdapter`.
- **PR-005**: testes nunca usam o banco de desenvolvimento; usam a instância isolada de testes.
- **PR-006**: a interface reutiliza `PageHeader`, `Dialog`, `Alert`, `Badge`, `Button` e os blocos da SPEC-0038; novos blocos entram em `INTERFACE.md`.

### 5. Histórias de usuário

#### US-001 — Colar a resposta da empresa e receber propostas (P1)

Como owner ou admin, quero colar a resposta da empresa no relatório e receber uma proposta por contradição, para não mapear tudo à mão.

**Por que P1**: sem a resposta interpretada nada avança.
**Teste independente**: com IA simulada, colar uma resposta que cobre duas de três contradições e ver propostas e um "Sem decisão".
**Requisitos**: FR-001, FR-002, FR-008

#### US-002 — Conferir e confirmar as correções (P1)

Como owner ou admin, quero confirmar em bloco as propostas claras e decidir uma a uma as incertas, para manter o controle sobre o que muda.

**Por que P1**: é o checkpoint humano obrigatório.
**Teste independente**: confirmar o bloco de claras e deixar uma incerta sem decisão, e ver que só as claras mudam.
**Requisitos**: FR-003, FR-004

#### US-003 — Aplicar a correção com histórico e registro (P1)

Como owner ou admin, quero que a correção confirmada altere só o trecho e crie versão nova com registro de decisão, para auditar e poder voltar atrás.

**Por que P1**: sem histórico e registro a correção não é confiável.
**Teste independente**: confirmar uma correção e conferir a versão nova, a anterior preservada e o registro.
**Requisitos**: FR-004, FR-005, FR-008

#### US-004 — Rodar um novo ciclo e ver o que mudou (P2)

Como owner ou admin, quero reanalisar a coleção depois das correções e ver o que foi resolvido e o que apareceu de novo, para saber se posso liberar.

**Por que P2**: fecha o ciclo, mas depende das correções.
**Teste independente**: aplicar uma correção, reanalisar e ver a ocorrência marcada como resolvida.
**Requisitos**: FR-006

#### US-005 — Liberar a coleção para a base (P2)

Como owner ou admin, quero marcar a coleção como "revisada" com aviso quando ainda há contradições abertas, para sinalizar que ela segue à Fase 2.

**Por que P2**: é o marco final do M04, depois do ciclo.
**Teste independente**: liberar com e sem contradições abertas e conferir o aviso e a marca.
**Requisitos**: FR-007, FR-008

### 6. Cenários BDD de aceite

#### AC-001 — Interpretar a resposta gera propostas

**Cobre**: US-001, FR-001, FR-002, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @AC-001
Feature: Interpretação da resposta da empresa

  Scenario: resposta colada gera uma proposta por contradição
    Given um relatório com três contradições e a resposta da empresa colada na caixa
    When owner ou admin clica em "Interpretar resposta"
    Then cada contradição coberta recebe uma proposta com a versão que vale e a marca "clara" ou "incerta"
    And nenhum documento foi alterado
```

#### AC-002 — Sem chave de IA

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-002
Feature: Interpretação da resposta da empresa

  Scenario: Workspace sem IA externa permitida
    Given um Workspace com "permitir análise por IA externa" desligada e um modelo de IA espião
    When owner ou admin tenta interpretar a resposta
    Then o sistema avisa o motivo e não chama a IA
    And a pessoa pode decidir cada contradição à mão
```

#### AC-003 — Aviso de envio da resposta à IA

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-003
Feature: Interpretação da resposta da empresa

  Scenario: confirmação antes de enviar o texto à IA
    Given uma resposta colada e a IA permitida
    When owner ou admin clica em "Interpretar resposta"
    Then o sistema informa que o texto será enviado à IA configurada e qual é o provedor
    And a interpretação só começa depois da confirmação
```

#### AC-004 — Contradição não coberta fica sem decisão

**Cobre**: US-001, FR-002

```gherkin
@US-001 @FR-002 @AC-004
Feature: Interpretação da resposta da empresa

  Scenario: a resposta não cobre uma das contradições
    Given três contradições e uma resposta que fala só de duas
    When a interpretação termina
    Then a terceira fica "Sem decisão", continua aberta e destacada como pendente
```

#### AC-005 — Trecho não localizado vira incerta

**Cobre**: US-001, FR-002, FR-004, NFR-003

```gherkin
@US-001 @FR-002 @FR-004 @NFR-003 @AC-005
Feature: Localização do trecho

  Scenario: a IA não encontra o trecho exato a corrigir
    Given uma proposta cuja correção não corresponde a nenhum trecho do documento
    When a interpretação termina
    Then a proposta é marcada "incerta" com a mensagem "Não foi possível localizar o trecho; indique qual corrigir"
    And a pessoa pode editar o texto da correção antes de confirmar
```

#### AC-006 — Member não interpreta nem confirma

**Cobre**: US-001, FR-001, FR-008

```gherkin
@US-001 @FR-001 @FR-008 @AC-006
Feature: Permissões

  Scenario: member só consulta
    Given uma pessoa com papel member e um relatório com propostas
    When ela tenta interpretar, confirmar ou liberar
    Then cada ação é recusada por permissão insuficiente
    And ela consegue ver as propostas e o histórico
```

#### AC-007 — Nada grava antes da confirmação

**Cobre**: US-002, FR-003, NFR-002

```gherkin
@US-002 @FR-003 @NFR-002 @AC-007
Feature: Checkpoint humano

  Scenario: propostas claras só mudam o documento após confirmar o bloco
    Given duas propostas claras pré-aprovadas
    When a pessoa ainda não confirmou
    Then os documentos permanecem inalterados
    And ao clicar em "Confirmar todas" as duas correções são aplicadas
```

#### AC-008 — Incerta sem decisão não muda o documento

**Cobre**: US-002, FR-003, NFR-002

```gherkin
@US-002 @FR-003 @NFR-002 @AC-008
Feature: Checkpoint humano

  Scenario: proposta incerta ignorada
    Given uma proposta incerta sem decisão
    When a pessoa confirma o bloco de claras
    Then o documento da proposta incerta permanece inalterado
    And a contradição continua aberta
```

#### AC-009 — Editar e aceitar uma incerta

**Cobre**: US-002, FR-003, FR-004

```gherkin
@US-002 @FR-003 @FR-004 @AC-009
Feature: Decisão individual

  Scenario: pessoa edita o texto da correção e aceita
    Given uma proposta incerta
    When a pessoa edita o texto da correção e clica em "Aceitar"
    Then a correção com o texto editado é aplicada ao trecho indicado
    And o registro guarda que a proposta foi editada
```

#### AC-010 — Manter sem decisão

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-010
Feature: Decisão individual

  Scenario: pessoa escolhe manter sem decisão
    Given uma proposta incerta
    When a pessoa escolhe "Manter sem decisão"
    Then a contradição continua aberta e o documento permanece inalterado
```

#### AC-011 — Só o trecho alvo muda e a versão anterior é preservada

**Cobre**: US-003, FR-004, NFR-002

```gherkin
@US-003 @FR-004 @NFR-002 @AC-011
Feature: Aplicação da correção

  Scenario: correção confirmada altera apenas o trecho alvo
    Given um documento de 10 parágrafos e uma correção confirmada para o parágrafo 4
    When a correção é aplicada
    Then o novo conteúdo difere do anterior somente no parágrafo 4
    And a versão anterior permanece guardada
```

#### AC-012 — Registro de decisões

**Cobre**: US-003, FR-005

```gherkin
@US-003 @FR-005 @AC-012
Feature: Registro de decisões

  Scenario: toda correção deixa um registro completo
    Given uma correção confirmada por owner ou admin
    When ela é aplicada
    Then o registro mostra quem confirmou, quando, a contradição, a resposta da empresa que a justificou, a proposta da IA e a versão do documento
```

#### AC-013 — Voltar a uma versão anterior

**Cobre**: US-003, FR-004, FR-005, FR-008

```gherkin
@US-003 @FR-004 @FR-005 @FR-008 @AC-013
Feature: Histórico de versões

  Scenario: owner ou admin volta a uma versão antiga
    Given um documento com três versões
    When owner ou admin escolhe a versão 1 e confirma
    Then a versão 1 vira a versão atual como uma nova versão e o registro anota a volta
    And member não consegue voltar versão
```

#### AC-014 — Retenção do histórico

**Cobre**: US-003, FR-005, NFR-001

```gherkin
@US-003 @FR-005 @NFR-001 @AC-014
Feature: Retenção

  Scenario: versões antigas por 90 dias e registro enquanto a coleção existir
    Given versões antigas com 91 dias e registros de decisão da mesma coleção
    When a rotina de retenção roda e depois a coleção é apagada
    Then as versões antigas vencidas são apagadas e os registros permanecem enquanto a coleção existe
    And ao apagar a coleção resta somente um registro mínimo (quem apagou, quando, quantas decisões), sem texto da empresa
```

#### AC-015 — Correção reindexa o documento

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-015
Feature: Publicação da versão corrigida

  Scenario: a versão nova substitui a anterior na coleção
    Given um documento já indexado na coleção e uma correção aplicada
    When a nova versão é publicada
    Then a coleção passa a ter a versão corrigida do documento e seus vetores são atualizados
    And o documento não fica duplicado
```

#### AC-016 — Novo ciclo mostra resolvido e novo

**Cobre**: US-004, FR-006

```gherkin
@US-004 @FR-006 @AC-016
Feature: Novo ciclo

  Scenario: reanálise depois da correção
    Given uma correção aplicada e uma nova análise concluída
    When a pessoa abre o relatório
    Then vê quais ocorrências foram resolvidas e quais apareceram de novo desde a rodada anterior
```

#### AC-017 — Resumo da rodada acessível

**Cobre**: US-004, FR-006, NFR-004

```gherkin
@US-004 @FR-006 @NFR-004 @AC-017
Feature: Novo ciclo

  Scenario: resumo anunciado ao fim da rodada
    Given uma rodada de correção concluída
    When o resumo aparece
    Then é anunciado em role=status com as contagens de resolvidas, novas e abertas
```

#### AC-018 — Reanálise exige confirmação do envio à IA

**Cobre**: US-004, FR-006, NFR-001

```gherkin
@US-004 @FR-006 @NFR-001 @AC-018
Feature: Novo ciclo

  Scenario: cada reanálise repete o aviso
    Given um relatório com correções aplicadas
    When owner ou admin clica em "Analisar contradições" de novo
    Then o aviso de envio do conteúdo à IA aparece novamente e a análise só começa depois da confirmação
```

#### AC-019 — Liberar sem contradições abertas

**Cobre**: US-005, FR-007

```gherkin
@US-005 @FR-007 @AC-019
Feature: Liberar para a base

  Scenario: coleção sem abertas
    Given uma coleção sem contradições abertas
    When owner ou admin clica em "Liberar para a base" e confirma
    Then a coleção fica marcada como "revisada" com autor e data
```

#### AC-020 — Liberar com contradições abertas

**Cobre**: US-005, FR-007, NFR-004

```gherkin
@US-005 @FR-007 @NFR-004 @AC-020
Feature: Liberar para a base

  Scenario: aviso explícito acessível
    Given uma coleção com 3 contradições abertas
    When owner ou admin clica em "Liberar para a base"
    Then um diálogo informa que há 3 contradições abertas e só libera após a confirmação explícita
    And o diálogo prende o foco e é operável por teclado
```

#### AC-021 — Só owner e admin liberam

**Cobre**: US-005, FR-007, FR-008

```gherkin
@US-005 @FR-007 @FR-008 @AC-021
Feature: Liberar para a base

  Scenario: member não libera
    Given uma pessoa com papel member
    When ela tenta liberar a coleção
    Then a ação é recusada e o botão não aparece na tela
```

#### AC-022 — Celular e teclado

**Cobre**: US-002, NFR-004

```gherkin
@US-002 @NFR-004 @AC-022
Feature: Responsividade

  Scenario: bloco de claras e decisão individual em 375 pixels
    Given um viewport de 375 pixels e propostas com textos longos
    When a pessoa confere o bloco de claras e decide uma incerta
    Then os controles empilham sem rolagem horizontal e são operáveis por teclado
```

#### AC-023 — Claras aceitas sem edição no primeiro ciclo

**Cobre**: NFR-003

```gherkin
@NFR-003 @AC-023
Feature: Qualidade das propostas

  Scenario: corpus sintético com respostas claras
    Given um corpus sintético com respostas inequívocas e um modelo simulado
    When as propostas são geradas
    Then pelo menos 70% dos documentos corrigidos ficam iguais ao esperado sem edição manual
```

#### AC-024 — Clara só com trecho localizado

**Cobre**: NFR-003, FR-002

```gherkin
@NFR-003 @FR-002 @AC-024
Feature: Qualidade das propostas

  Scenario: proposta sem trecho localizado nunca é clara
    Given propostas cuja correção não corresponde a nenhum trecho do documento
    When as propostas são classificadas
    Then nenhuma delas é marcada "clara"
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve oferecer, na rota do relatório de contradições, uma caixa de texto "Resposta da empresa" e a ação "Interpretar resposta" para owner e admin, exigindo a chave "permitir análise por IA externa" ligada e uma conexão de IA do Workspace, e exibindo o aviso de envio do texto à IA configurada antes de começar.
- **FR-002**: O sistema deve mapear a resposta às contradições do relatório, produzindo para cada uma uma proposta com a versão que vale, o trecho alvo e o texto corrigido, marcada "clara" ou "incerta"; contradição não coberta fica "Sem decisão"; proposta sem trecho localizado nunca é "clara".
- **FR-003**: O sistema deve exigir confirmação humana para toda escrita: as propostas claras ficam num bloco pré-aprovado com "Confirmar todas"; as incertas pedem decisão individual (Aceitar, Editar ou Manter sem decisão); sem confirmação, nenhum documento muda.
- **FR-004**: O sistema deve aplicar a correção confirmada no próprio `.md` substituindo somente o trecho alvo, criar uma versão nova do documento com a anterior preservada, publicar a versão nova na coleção (reindexação do documento) e, quando o trecho não for localizado, manter a proposta como incerta com a mensagem e a edição manual.
- **FR-005**: O sistema deve registrar cada decisão (quem confirmou, quando, a contradição, a resposta da empresa que a justificou, a proposta da IA, se foi editada e a versão resultante), permitir voltar a uma versão anterior a partir do detalhe do documento com confirmação, guardar versões antigas por 90 dias e os registros enquanto a coleção existir, deixando apenas um registro mínimo quando a coleção for apagada.
- **FR-006**: O sistema deve permitir um novo ciclo por reanálise (SPEC-0038), repetindo o aviso de envio à IA, e mostrar ao fim da rodada um resumo do que foi resolvido, do que apareceu de novo e do que continua aberto.
- **FR-007**: O sistema deve oferecer "Liberar para a base" a owner e admin, que marca a coleção como "revisada" com autor e data; com contradições abertas exibe um `Dialog` com a contagem e exige confirmação explícita.
- **FR-008**: O sistema deve restringir a owner e admin interpretar, confirmar, editar, voltar versão e liberar, permitindo ao member apenas consultar relatório, propostas e histórico.

#### Não funcionais

- **NFR-001**: Privacidade: a resposta da empresa e o conteúdo dos documentos não vão à IA externa com a chave desligada nem antes da confirmação do aviso; textos não aparecem em logs; retenção de 90 dias para versões antigas. **Verificação**: provider espião, varredura de logs em teste e rotina de retenção com datas simuladas.
- **NFR-002**: Integridade: nenhuma escrita sem confirmação humana registrada e somente o trecho alvo muda. **Verificação**: teste que compara hashes e diff dos documentos antes e depois, incluindo caso sem confirmação.
- **NFR-003**: Qualidade: pelo menos 70% dos `.md` finais passam sem edição manual depois do primeiro ciclo (gabarito) e a IA marca "incerta" sempre que não localizar o trecho. **Verificação**: corpus sintético com modelo simulado e, quando entregue, o gabarito real (opt-in, fora do repositório).
- **NFR-004**: Acessibilidade e responsividade: avisos e resumos em `role=status`, diálogos que prendem o foco, controles operáveis por teclado e sem rolagem horizontal em 375 px. **Verificação**: testes de componente com Testing Library e conferência visual em desktop e mobile.

#### Erros e casos-limite

- Sem chave de IA → avisa e não interpreta; decisão manual disponível.
- IA indisponível ou resposta inválida → nada é gravado; tentar de novo.
- Trecho não localizado → incerta, edição manual e confirmação.
- Resposta que não cobre uma contradição → "Sem decisão", aberta.
- Documento alterado entre a análise e a confirmação (hash diferente) → a correção é recusada com aviso e a análise precisa ser refeita.
- Duas confirmações simultâneas no mesmo documento → a segunda é recusada.
- Liberar com contradições abertas → exige confirmação explícita.
- Apagar a coleção → apaga versões, decisões e texto da empresa, deixando só o registro mínimo.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI + SQLAlchemy + Alembic; worker Procrastinate; `ChatModelAdapter`; coleções com `DocumentoColecao` identificado por nome de arquivo e novo envio que o substitui e reindexa (R-001).
- Frontend Next.js: rota de contradições da SPEC-0038, `features/contradicoes/` e `features/colecoes/`.
- Depende da SPEC-0037 (conexão de IA, chave, papéis) e da SPEC-0038 (análises e ocorrências).

#### Arquitetura e módulos

- `src/pipeline/decisoes/` (novo, sem HTTP nem banco): `interpretacao.py` (resposta + ocorrências → propostas via `ChatModelAdapter`, saída estruturada), `localizacao.py` (encontra o trecho alvo no `.md` por correspondência exata e, depois, por semelhança alta; sem acerto vira incerta), `aplicacao.py` (substitui o trecho e devolve o novo `.md` e o diff) e `contratos.py` (`Proposta`, `Decisao`, `Localizacao`).
- `src/app/decisoes.py` (novo): orquestra interpretar, confirmar, aplicar, versionar, publicar via novo envio, voltar versão, liberar e retenção.
- Fluxo: resposta colada → confirmação do aviso → interpretação (em segundo plano) → propostas → confirmação humana → aplicação (verifica hash) → nova versão → publicação na coleção → registro → nova análise (SPEC-0038) → liberar.
- A fachada `service.py` expõe `interpretar_resposta`, `localizar_trecho` e `aplicar_correcao`.

#### Migrations

- Revisão `0039_decisoes_empresa`, encadeada após a da SPEC-0038: cria `respostas_empresa`, `propostas_correcao`, `decisoes_empresa`, `versoes_documento` e `registros_exclusao_decisoes`; acrescenta `revisada_em` e `revisada_por` em `colecoes`; downgrade na ordem inversa; sem backfill.

#### Models

- `RespostaEmpresa`: `id`, `colecao_id`, `analise_id`, `texto`, `criado_por`, `criado_em`.
- `PropostaCorrecao`: `id`, `resposta_id`, `ocorrencia_id`, `situacao` (`clara`, `incerta`, `sem_decisao`, `aceita`, `editada`, `mantida`), `documento_id`, `trecho_alvo`, `texto_corrigido`, `hash_documento`, `motivo` seguro.
- `DecisaoEmpresa`: `id`, `proposta_id`, `colecao_id`, `ocorrencia_id`, `confirmado_por`, `confirmado_em`, `editada`, `versao_resultante`, `resposta_trecho`.
- `VersaoDocumento`: `id`, `documento_id`, `numero`, `chave_armazenamento`, `hash`, `criado_em`, `expira_em` (90 dias para versões não atuais).
- `RegistroExclusaoDecisoes`: `id`, `colecao_id`, `apagado_por`, `apagado_em`, `decisoes` (quantidade); registro mínimo que resta quando a coleção é apagada, sem texto da empresa (AC-014).
- Arquivo: `src/app/models.py`.

#### Controllers e casos de uso

- `POST /api/v1/colecoes/{id}/decisoes/respostas` (cola e interpreta, 202; owner/admin; exige confirmação do aviso). Com `manual: true` registra a resposta sem chamar a IA (201), cria uma proposta "Sem decisão" por contradição aberta e permite decidir à mão com `editar` informando `arquivo`, `trecho_alvo` e `texto_corrigido` (caminho do AC-002).
- `GET /api/v1/colecoes/{id}/decisoes/propostas` (qualquer papel), `GET .../decisoes/registro` (registro de decisões, qualquer papel) e `GET .../decisoes/rodada` (`resolvidas`, `novas` e `abertas` entre a última análise e a anterior, qualquer papel).
- `POST /api/v1/colecoes/{id}/decisoes/propostas/confirmar` (lote de claras) e `POST .../propostas/{pid}/decisao` (`aceitar`, `editar`, `manter`).
- `GET /api/v1/colecoes/{id}/documentos/{documento_id}/versoes` e `POST .../versoes/{numero}/restaurar`.
- `POST /api/v1/colecoes/{id}/revisar` (liberar; owner/admin; confirma quando há abertas).
- Erros: 403, 404, 409 (hash divergente, concorrência, IA não permitida, liberar com abertas sem confirmação), 422 (sem confirmação, texto vazio ou acima de 20000 caracteres).

#### Views e experiência

- Detalhado na seção 10.

#### Queries e repositórios

- `src/app/repo.py`: propostas por resposta, decisões por coleção, versões por documento, contagem de ocorrências abertas por coleção e comparação entre análises; índices em `propostas_correcao(resposta_id)`, `decisoes_empresa(colecao_id)` e `versoes_documento(documento_id, numero)`.

#### Jobs e processamento assíncrono

- `interpretar_resposta_task(resposta_id)`: idempotente, falha vira "interpretação incompleta" com motivo seguro, nada gravado nos documentos.
- `purgar_versoes_task` (cron diário): apaga versões não atuais com mais de 90 dias.

#### Estrutura de arquivos

```text
specs/draft/0039-fase-1-decisao-da-empresa-e-atualizacao/
  spec.md
  research/
src/pipeline/decisoes/{__init__,contratos,interpretacao,localizacao,aplicacao}.py
src/app/decisoes.py
alembic/versions/0039_decisoes_empresa.py
tests/test_decisoes_interpretacao.py
tests/test_decisoes_localizacao.py
tests/test_decisoes_aplicacao.py
tests/test_decisoes_retencao.py
tests/test_router_decisoes.py
frontend/src/features/decisoes/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| RespostaEmpresa | `id` | texto colado 1–20000 caracteres, autor, data; apagada com a coleção | N:1 Colecao, N:1 AnaliseContradicao |
| PropostaCorrecao | `id` | `situacao`, trecho alvo, texto corrigido, hash do documento; `clara` exige trecho localizado | N:1 RespostaEmpresa, N:1 OcorrenciaContradicao |
| DecisaoEmpresa | `id` | autor, data, editada, versão resultante | 1:1 PropostaCorrecao |
| VersaoDocumento | `id`; único (`documento_id`, `numero`) | arquivo da versão, hash; não atual expira em 90 dias | N:1 DocumentoColecao |
| RegistroExclusaoDecisoes | `id` | quem apagou, quando, quantas decisões; sem texto da empresa | N:1 Colecao (apagada) |
| Colecao (extensão) | `id` | `revisada_em`, `revisada_por` | N:1 Pessoa |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| PropostaCorrecao | (nova) | interpretação | clara, incerta ou sem_decisao | `clara` exige trecho localizado |
| PropostaCorrecao | clara ou incerta | aceitar | aceita | confirmação humana registrada |
| PropostaCorrecao | incerta | editar e aceitar | editada | texto editado guardado |
| PropostaCorrecao | clara ou incerta | manter | mantida | documento inalterado |
| Colecao | (qualquer) | liberar | revisada | autor e data; contradições abertas confirmadas |

#### Migração e retenção

- Migration aditiva `0039_decisoes_empresa` com downgrade. Versões não atuais por 90 dias; registros de decisão enquanto a coleção existir; ao apagar a coleção apaga-se tudo e fica só o registro mínimo.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. Estende a rota do relatório de contradições e o detalhe do documento.

#### Stack e convenções de interface

- Next.js (App Router) + React + TypeScript + Tailwind, shadcn/ui (Base UI), testes com Vitest e Testing Library. Telas atuais afetadas: rota `.../colecoes/{colecaoId}/contradicoes` (SPEC-0038) e o detalhe do documento da coleção (`features/colecoes/`). Fontes: `INTERFACE.md`, `DESIGNSYSTEM.MD`.

#### Telas e responsabilidades

- **Relatório de contradições (estendido)**: colar a resposta, interpretar, conferir propostas, confirmar, ver "Corrigido" e o resumo da rodada, analisar de novo e liberar.
- **Detalhe do documento**: ver versões e voltar a uma versão anterior com confirmação.

#### Fluxo de informação e navegação

- A pessoa cola a resposta → confirma o aviso → vê as propostas → confirma o bloco de claras e decide as incertas → vê "Corrigido" nos cartões e o resumo → reanalisa → libera. O link "Ver versões" leva ao detalhe do documento; a trilha volta ao relatório.

#### Menus e navegação principal

- Sem item novo de menu: a funcionalidade vive na rota do relatório (acessada pelo botão da coleção) e no detalhe do documento, já alcançáveis pelos menus atuais.

#### Formulários e ações

- Caixa "Resposta da empresa" (1–20000 caracteres, contador, erro junto do campo com foco) e "Interpretar resposta"; por proposta: Aceitar, Editar (área de texto) e Manter sem decisão; "Confirmar todas" no bloco de claras; "Analisar contradições"; "Liberar para a base" com `Dialog`; "Voltar a esta versão" com `Dialog`.

#### Composição e disposição

- Caixa de resposta no topo do relatório; bloco "Propostas claras" com "Confirmar todas"; lista de incertas com decisão individual; cartões da SPEC-0038 ganham o selo "Corrigido". Em 375 px tudo empilha e o texto quebra sem rolagem horizontal.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Relatório | `CaixaRespostaEmpresa` | Texto da resposta, aviso de envio à IA e interpretação | `frontend/src/features/decisoes/CaixaRespostaEmpresa.tsx` | `Textarea`, `Button`, `Dialog` | shadcn/ui + próprio | Novo |
| Relatório | `BlocoPropostasClaras` | Lista pré-aprovada e "Confirmar todas" | `frontend/src/features/decisoes/BlocoPropostasClaras.tsx` | `Button`, `Badge` | shadcn/ui + próprio | Novo |
| Relatório | `PropostaIncerta` | Aceitar, Editar e Manter sem decisão | `frontend/src/features/decisoes/PropostaIncerta.tsx` | `Textarea`, `Button` | shadcn/ui + próprio | Novo |
| Relatório | `ResumoRodada` | Resolvidas, novas e abertas em `role=status` | `frontend/src/features/decisoes/ResumoRodada.tsx` | `Alert` | shadcn/ui + próprio | Novo |
| Relatório | `LiberarColecaoDialog` | Aviso com contagem de abertas e confirmação | `frontend/src/features/decisoes/LiberarColecaoDialog.tsx` | `Dialog`, `Button` | shadcn/ui + próprio | Novo; segue `ApagarColecaoDialog` |
| Relatório | `CartaoOcorrencia` | Selo "Corrigido" e link "Ver versões" | `frontend/src/features/contradicoes/CartaoOcorrencia.tsx` | `Badge` | próprio | Estende o bloco da SPEC-0038 |
| Documento | `VersoesDocumentoSheet` | Lista de versões e "Voltar a esta versão" | `frontend/src/features/decisoes/VersoesDocumentoSheet.tsx` | `Sheet`, `Dialog` | shadcn/ui + próprio | Novo; segue `ChunksDocumentoSheet` |

- Registrar cada bloco em `INTERFACE.md` com consumidores e origem; a página apenas compõe esses blocos.

#### Estados e acessibilidade

- Carregando com `aria-busy` e `Skeleton`; vazio sem propostas orienta a colar a resposta; erro em `Alert` com "Tentar novamente"; sucesso e resumos em `role=status`; permissão insuficiente esconde as ações de escrita mantendo a leitura.
- Diálogos prendem o foco e devolvem-no ao controle de origem; teclado em todos os controles; o `Breadcrumb` mantém a equipe visível e marca a página atual.

#### Contrato CRUD

- Não há CRUD de entidade nova com listagem própria: decisões e versões são registros de auditoria acessados por cartões e pelo detalhe do documento. A listagem de documentos continua com o `DataGrid` existente (`DataGridDocumentos`) em largura total, com a coluna `ID` visível, linha-link para o detalhe e as ações independentes de editar e apagar já existentes; o cabeçalho usa o `PageHeader` único. Os componentes novos entram em `INTERFACE.md`.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre em cada tarefa de interface, em desktop e 375 px, nos estados carregando, vazio, claras, incertas, "Sem decisão", erro e sucesso, conferindo bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD`. Tarefas de backend registram `Não aplicável` com motivo.

#### APIs expostas

- As rotas da seção 8, sob `/api/v1`, autenticadas por sessão, com `require_write_role` nas escritas.

#### APIs externas utilizadas

- IA de interpretação via `ChatModelAdapter` pela conexão do Workspace (SPEC-0037), com timeout e retry limitados; falha não grava nada.

#### Documentação das APIs consultadas

- Nenhuma documentação externa; contrato local `ChatModelAdapter`.

#### Eventos e outros contratos

- O `.md` corrigido mantém o contrato da SPEC-0002; a publicação usa o envio existente da coleção (SPEC-0030).

### 11. Estratégia TDD

- **Unidade**: localização do trecho, aplicação da correção com diff, classificação clara/incerta, montagem do resumo da rodada, componentes React isolados.
- **Integração/contrato**: rotas com banco isolado, tarefa de interpretação com provider falso, aplicação com verificação de hash, publicação via envio simulado, retenção com datas simuladas, migration `0039` com downgrade.
- **BDD/aceite**: o Gherkin da seção 6 informa o desenho de cada caso; nenhum `.feature` é criado.
- **Runner TDD**: projeto Python/Node misto sem PHP; usar os runners existentes: Pytest no backend e Vitest no frontend.
- **E2E**: jornada relatório → resposta → confirmação → versão nova → reanálise → liberar pelo cliente de teste da API, com provider falso; sem chamada externa real.
- **Verificação manual**: qualidade real da IA e o gabarito (opt-in, fora do repositório), pois dependem de provider pago e de dados que não podem ser versionados.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, NFR-001, AC-001 | AC-001 na seção 6 | tests/test_decisoes_interpretacao.py: propostas por contradição (`SPECSFY: SPEC-0039 AC-001`) | RED: `.venv/bin/python -m pytest tests/test_decisoes_interpretacao.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-001, FR-001, NFR-001, AC-002 | AC-002 na seção 6 | tests/test_router_decisoes.py: sem chave de IA (`SPECSFY: SPEC-0039 AC-002`) | RED: `.venv/bin/python -m pytest tests/test_router_decisoes.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-001, FR-001, NFR-001, AC-003 | AC-003 na seção 6 | frontend/src/features/decisoes/CaixaRespostaEmpresa.test.tsx: aviso e confirmação (`SPECSFY: SPEC-0039 AC-003`) | RED: `cd frontend && npx vitest run src/features/decisoes/CaixaRespostaEmpresa.test.tsx` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-001, FR-002, AC-004 | AC-004 na seção 6 | tests/test_decisoes_interpretacao.py: sem decisão (`SPECSFY: SPEC-0039 AC-004`) | RED: `.venv/bin/python -m pytest tests/test_decisoes_interpretacao.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-001, FR-002, FR-004, NFR-003, AC-005 | AC-005 na seção 6 | tests/test_decisoes_localizacao.py: trecho não localizado (`SPECSFY: SPEC-0039 AC-005`) | RED: `.venv/bin/python -m pytest tests/test_decisoes_localizacao.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-001, FR-001, FR-008, AC-006 | AC-006 na seção 6 | tests/test_router_decisoes.py: member recusado (`SPECSFY: SPEC-0039 AC-006`) | RED: `.venv/bin/python -m pytest tests/test_router_decisoes.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-002, FR-003, NFR-002, AC-007 | AC-007 na seção 6 | tests/test_decisoes_aplicacao.py: nada grava antes de confirmar (`SPECSFY: SPEC-0039 AC-007`) | RED: `.venv/bin/python -m pytest tests/test_decisoes_aplicacao.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-002, FR-003, NFR-002, AC-008 | AC-008 na seção 6 | tests/test_decisoes_aplicacao.py: incerta ignorada (`SPECSFY: SPEC-0039 AC-008`) | RED: `.venv/bin/python -m pytest tests/test_decisoes_aplicacao.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-002, FR-003, FR-004, AC-009 | AC-009 na seção 6 | tests/test_router_decisoes.py: editar e aceitar (`SPECSFY: SPEC-0039 AC-009`) | RED: `.venv/bin/python -m pytest tests/test_router_decisoes.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-002, FR-003, AC-010 | AC-010 na seção 6 | tests/test_router_decisoes.py: manter sem decisão (`SPECSFY: SPEC-0039 AC-010`) | RED: `.venv/bin/python -m pytest tests/test_router_decisoes.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-003, FR-004, NFR-002, AC-011 | AC-011 na seção 6 | tests/test_decisoes_aplicacao.py: só o trecho alvo muda (`SPECSFY: SPEC-0039 AC-011`) | RED: `.venv/bin/python -m pytest tests/test_decisoes_aplicacao.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-003, FR-005, AC-012 | AC-012 na seção 6 | tests/test_router_decisoes.py: registro de decisões (`SPECSFY: SPEC-0039 AC-012`) | RED: `.venv/bin/python -m pytest tests/test_router_decisoes.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-003, FR-004, FR-005, FR-008, AC-013 | AC-013 na seção 6 | tests/test_router_decisoes.py: voltar versão (`SPECSFY: SPEC-0039 AC-013`) | RED: `.venv/bin/python -m pytest tests/test_router_decisoes.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-003, FR-005, NFR-001, AC-014 | AC-014 na seção 6 | tests/test_decisoes_retencao.py: 90 dias e coleção apagada (`SPECSFY: SPEC-0039 AC-014`) | RED: `.venv/bin/python -m pytest tests/test_decisoes_retencao.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-003, FR-004, AC-015 | AC-015 na seção 6 | tests/test_decisoes_aplicacao.py: reindexa sem duplicar (`SPECSFY: SPEC-0039 AC-015`) | RED: `.venv/bin/python -m pytest tests/test_decisoes_aplicacao.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-004, FR-006, AC-016 | AC-016 na seção 6 | tests/test_router_decisoes.py: resolvidas e novas (`SPECSFY: SPEC-0039 AC-016`) | RED: `.venv/bin/python -m pytest tests/test_router_decisoes.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-004, FR-006, NFR-004, AC-017 | AC-017 na seção 6 | frontend/src/features/decisoes/ResumoRodada.test.tsx: resumo anunciado (`SPECSFY: SPEC-0039 AC-017`) | RED: `cd frontend && npx vitest run src/features/decisoes/ResumoRodada.test.tsx` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-004, FR-006, NFR-001, AC-018 | AC-018 na seção 6 | frontend/src/features/decisoes/CaixaRespostaEmpresa.test.tsx: aviso na reanálise (`SPECSFY: SPEC-0039 AC-018`) | RED: `cd frontend && npx vitest run src/features/decisoes/CaixaRespostaEmpresa.test.tsx` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-005, FR-007, AC-019 | AC-019 na seção 6 | tests/test_router_decisoes.py: liberar sem abertas (`SPECSFY: SPEC-0039 AC-019`) | RED: `.venv/bin/python -m pytest tests/test_router_decisoes.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-005, FR-007, NFR-004, AC-020 | AC-020 na seção 6 | frontend/src/features/decisoes/LiberarColecaoDialog.test.tsx: aviso com contagem (`SPECSFY: SPEC-0039 AC-020`) | RED: `cd frontend && npx vitest run src/features/decisoes/LiberarColecaoDialog.test.tsx` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-005, FR-007, FR-008, AC-021 | AC-021 na seção 6 | tests/test_router_decisoes.py: member não libera (`SPECSFY: SPEC-0039 AC-021`) | RED: `.venv/bin/python -m pytest tests/test_router_decisoes.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| US-002, NFR-004, AC-022 | AC-022 na seção 6 | frontend/src/features/decisoes/PropostaIncerta.test.tsx: 375 px e teclado (`SPECSFY: SPEC-0039 AC-022`) | RED: `cd frontend && npx vitest run src/features/decisoes/PropostaIncerta.test.tsx` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| NFR-003, AC-023 | AC-023 na seção 6 | tests/test_decisoes_interpretacao.py: corpus sintético (`SPECSFY: SPEC-0039 AC-023`) | RED: `.venv/bin/python -m pytest tests/test_decisoes_interpretacao.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |
| NFR-003, FR-002, AC-024 | AC-024 na seção 6 | tests/test_decisoes_localizacao.py: clara só com trecho (`SPECSFY: SPEC-0039 AC-024`) | RED: `.venv/bin/python -m pytest tests/test_decisoes_localizacao.py -q` em 2026-10-16, falha por comportamento ausente | GREEN: teste focal verde em 2026-10-16 | Regressão: pytest 770 passed, 1 skipped; vitest 278 passed |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | tests/test_decisoes_interpretacao.py | Passed |
| FR-001 | AC-002 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-001 | AC-003 | Componente | frontend/src/features/decisoes/CaixaRespostaEmpresa.test.tsx | Passed |
| FR-001 | AC-006 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-002 | AC-001 | Integração | tests/test_decisoes_interpretacao.py | Passed |
| FR-002 | AC-004 | Unidade | tests/test_decisoes_interpretacao.py | Passed |
| FR-002 | AC-005 | Unidade | tests/test_decisoes_localizacao.py | Passed |
| FR-002 | AC-024 | Unidade | tests/test_decisoes_localizacao.py | Passed |
| FR-003 | AC-007 | Integração | tests/test_decisoes_aplicacao.py | Passed |
| FR-003 | AC-008 | Integração | tests/test_decisoes_aplicacao.py | Passed |
| FR-003 | AC-009 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-003 | AC-010 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-004 | AC-005 | Unidade | tests/test_decisoes_localizacao.py | Passed |
| FR-004 | AC-009 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-004 | AC-011 | Unidade | tests/test_decisoes_aplicacao.py | Passed |
| FR-004 | AC-013 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-004 | AC-015 | Integração | tests/test_decisoes_aplicacao.py | Passed |
| FR-005 | AC-012 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-005 | AC-013 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-005 | AC-014 | Integração | tests/test_decisoes_retencao.py | Passed |
| FR-006 | AC-016 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-006 | AC-017 | Componente | frontend/src/features/decisoes/ResumoRodada.test.tsx | Passed |
| FR-006 | AC-018 | Componente | frontend/src/features/decisoes/CaixaRespostaEmpresa.test.tsx | Passed |
| FR-007 | AC-019 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-007 | AC-020 | Componente | frontend/src/features/decisoes/LiberarColecaoDialog.test.tsx | Passed |
| FR-007 | AC-021 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-008 | AC-006 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-008 | AC-013 | Contrato | tests/test_router_decisoes.py | Passed |
| FR-008 | AC-021 | Contrato | tests/test_router_decisoes.py | Passed |
| NFR-001 | AC-001 | Integração | tests/test_decisoes_interpretacao.py | Passed |
| NFR-001 | AC-002 | Contrato | tests/test_router_decisoes.py | Passed |
| NFR-001 | AC-003 | Componente | frontend/src/features/decisoes/CaixaRespostaEmpresa.test.tsx | Passed |
| NFR-002 | AC-007 | Integração | tests/test_decisoes_aplicacao.py | Passed |
| NFR-002 | AC-008 | Integração | tests/test_decisoes_aplicacao.py | Passed |
| NFR-002 | AC-011 | Unidade | tests/test_decisoes_aplicacao.py | Passed |
| NFR-003 | AC-005 | Unidade | tests/test_decisoes_localizacao.py | Passed |
| NFR-003 | AC-023 | Integração | tests/test_decisoes_interpretacao.py | Passed |
| NFR-003 | AC-024 | Unidade | tests/test_decisoes_localizacao.py | Passed |
| NFR-004 | AC-017 | Componente | frontend/src/features/decisoes/ResumoRodada.test.tsx | Passed |
| NFR-004 | AC-020 | Componente | frontend/src/features/decisoes/LiberarColecaoDialog.test.tsx | Passed |
| NFR-004 | AC-022 | Componente | frontend/src/features/decisoes/PropostaIncerta.test.tsx | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (2026-10-16)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0039-fase-1-decisao-da-empresa-e-atualizacao/spec.md`
- **Achados**: 0 BLOCKER. NOTE: R-002 e fontes apontavam para a pasta antiga da SPEC-0038 (corrigido). WARNING: o gabarito (meta de 70%) segue como verificação final opt-in (DEC-007).

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-16)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/planned/0039-fase-1-decisao-da-empresa-e-atualizacao/spec.md`
- **Achados**: 41 tarefas (24 TDD com RED válido, 14 código, 2 documentação, 1 operação); 41 de 41 IDs cobertos; nenhuma falha por sintaxe, importação ou ambiente: cada RED vem de comportamento ausente.

#### Gate do Ato III — Entrega

- **Resultado**: Passed (2026-10-16)
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/review/0039-fase-1-decisao-da-empresa-e-atualizacao/spec.md . --full-chain`
- **Achados**: 41 de 41 IDs cobertos; pytest 770 passed e 1 skipped; vitest 278 passed; `ruff`, ESLint, `tsc` e `npm run build` limpos. Revisão visual por inspeção de DOM e classes, sem navegador real. O gabarito (meta de 70%) segue como verificação final opt-in (DEC-007).

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso de teste falhando em tests/test_decisoes_interpretacao.py — Refs: US-001, FR-001, FR-002, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-001`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_decisoes_interpretacao.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso de teste falhando em tests/test_router_decisoes.py — Refs: US-001, FR-001, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-002`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_decisoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso de teste falhando em frontend/src/features/decisoes/CaixaRespostaEmpresa.test.tsx — Refs: US-001, FR-001, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-003`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: cd frontend && npx vitest run src/features/decisoes/CaixaRespostaEmpresa.test.tsx em 2026-10-16; causa do RED: componente ausente em frontend/src/features/decisoes.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso de teste falhando em tests/test_decisoes_interpretacao.py — Refs: US-001, FR-002, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-004`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_decisoes_interpretacao.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 um caso de teste falhando em tests/test_decisoes_localizacao.py — Refs: US-001, FR-002, FR-004, NFR-003, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-005`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_decisoes_localizacao.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-006 um caso de teste falhando em tests/test_router_decisoes.py — Refs: US-001, FR-001, FR-008, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-006`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_decisoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso de teste falhando em tests/test_decisoes_aplicacao.py — Refs: US-002, FR-003, NFR-002, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-007`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_decisoes_aplicacao.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 um caso de teste falhando em tests/test_decisoes_aplicacao.py — Refs: US-002, FR-003, NFR-002, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-008`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_decisoes_aplicacao.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 um caso de teste falhando em tests/test_router_decisoes.py — Refs: US-002, FR-003, FR-004, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-009`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_decisoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T010 [TEST] [TDD] [US-002] Derivar do AC-010 um caso de teste falhando em tests/test_router_decisoes.py — Refs: US-002, FR-003, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-010`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_decisoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 um caso de teste falhando em tests/test_decisoes_aplicacao.py — Refs: US-003, FR-004, NFR-002, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-011`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_decisoes_aplicacao.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso de teste falhando em tests/test_router_decisoes.py — Refs: US-003, FR-005, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-012`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_decisoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-013 um caso de teste falhando em tests/test_router_decisoes.py — Refs: US-003, FR-004, FR-005, FR-008, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-013`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_decisoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T014 [TEST] [TDD] [US-003] Derivar do AC-014 um caso de teste falhando em tests/test_decisoes_retencao.py — Refs: US-003, FR-005, NFR-001, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-014`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_decisoes_retencao.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T015 [TEST] [TDD] [US-003] Derivar do AC-015 um caso de teste falhando em tests/test_decisoes_aplicacao.py — Refs: US-003, FR-004, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-015`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_decisoes_aplicacao.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T016 [TEST] [TDD] [US-004] Derivar do AC-016 um caso de teste falhando em tests/test_router_decisoes.py — Refs: US-004, FR-006, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-016`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_decisoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T017 [TEST] [TDD] [US-004] Derivar do AC-017 um caso de teste falhando em frontend/src/features/decisoes/ResumoRodada.test.tsx — Refs: US-004, FR-006, NFR-004, AC-017 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-017`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: cd frontend && npx vitest run src/features/decisoes/ResumoRodada.test.tsx em 2026-10-16; causa do RED: componente ausente em frontend/src/features/decisoes.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T018 [TEST] [TDD] [US-004] Derivar do AC-018 um caso de teste falhando em frontend/src/features/decisoes/CaixaRespostaEmpresa.test.tsx — Refs: US-004, FR-006, NFR-001, AC-018 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-018`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: cd frontend && npx vitest run src/features/decisoes/CaixaRespostaEmpresa.test.tsx em 2026-10-16; causa do RED: componente ausente em frontend/src/features/decisoes.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T019 [TEST] [TDD] [US-005] Derivar do AC-019 um caso de teste falhando em tests/test_router_decisoes.py — Refs: US-005, FR-007, AC-019 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-019`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_decisoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T020 [TEST] [TDD] [US-005] Derivar do AC-020 um caso de teste falhando em frontend/src/features/decisoes/LiberarColecaoDialog.test.tsx — Refs: US-005, FR-007, NFR-004, AC-020 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-020`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: cd frontend && npx vitest run src/features/decisoes/LiberarColecaoDialog.test.tsx em 2026-10-16; causa do RED: componente ausente em frontend/src/features/decisoes.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T021 [TEST] [TDD] [US-005] Derivar do AC-021 um caso de teste falhando em tests/test_router_decisoes.py — Refs: US-005, FR-007, FR-008, AC-021 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-021`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_router_decisoes.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T022 [TEST] [TDD] [US-002] Derivar do AC-022 um caso de teste falhando em frontend/src/features/decisoes/PropostaIncerta.test.tsx — Refs: US-002, NFR-004, AC-022 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-022`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: cd frontend && npx vitest run src/features/decisoes/PropostaIncerta.test.tsx em 2026-10-16; causa do RED: componente ausente em frontend/src/features/decisoes.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T023 [TEST] [TDD] Derivar do AC-023 um caso de teste falhando em tests/test_decisoes_interpretacao.py — Refs: NFR-003, AC-023 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-023`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_decisoes_interpretacao.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

- [x] T024 [TEST] [TDD] Derivar do AC-024 um caso de teste falhando em tests/test_decisoes_localizacao.py — Refs: FR-002, NFR-003, AC-024 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0039 AC-024`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: .venv/bin/python -m pytest tests/test_decisoes_localizacao.py -q em 2026-10-16; causa do RED: módulo ausente em src.pipeline.decisoes/src.app.decisoes ou modelo/rota ainda inexistente.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados em tests/_fase1_decisoes.py.

#### Fase de fundação e backend

- [x] T025 [CODE] [US-003] Criar migration 0039_decisoes_empresa e modelos RespostaEmpresa, PropostaCorrecao, DecisaoEmpresa e VersaoDocumento em alembic/versions/0039_decisoes_empresa.py e src/app/models.py — Refs: US-003, US-005, FR-004, FR-005, FR-007, FR-008, NFR-001, AC-012, AC-013, AC-014, AC-019 — Depends: T012, T013, T014, T019
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_app_migrations.py tests/test_decisoes_retencao.py` e a regressão relacionada.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_app_migrations.py tests/test_decisoes_retencao.py -q` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T025", "refs": ["US-003", "US-005", "FR-004", "FR-005", "FR-007", "FR-008", "NFR-001", "AC-012", "AC-013", "AC-014", "AC-019"], "files": ["alembic/versions/0039_decisoes_empresa.py", "src/app/models.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_app_migrations.py tests/test_decisoes_retencao.py -q", "exit": 0}]} -->

- [x] T026 [DOC] Atualizar .specsfy/DATABASE.md com respostas_empresa, propostas_correcao, decisoes_empresa, versoes_documento e as colunas revisada_em e revisada_por de colecoes — Refs: AC-012, AC-013, AC-014, AC-019, FR-005, FR-007, NFR-001 — Depends: T025
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check`.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` em 2026-10-16: CURRENT; DATABASE.md descreve as 5 tabelas novas e as colunas de colecoes.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.

- [x] T027 [CODE] [US-001] Implementar contratos, localização do trecho e aplicação da correção em src/pipeline/decisoes/contratos.py, localizacao.py e aplicacao.py — Refs: US-001, US-003, FR-002, FR-004, NFR-002, NFR-003, AC-005, AC-011, AC-024 — Depends: T005, T011, T024
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_decisoes_localizacao.py tests/test_decisoes_aplicacao.py`.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_decisoes_localizacao.py tests/test_decisoes_aplicacao.py -q` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T027", "refs": ["US-001", "US-003", "FR-002", "FR-004", "NFR-002", "NFR-003", "AC-005", "AC-011", "AC-024"], "files": ["src/pipeline/decisoes/contratos.py", "src/pipeline/decisoes/localizacao.py", "src/pipeline/decisoes/aplicacao.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_decisoes_localizacao.py tests/test_decisoes_aplicacao.py -q", "exit": 0}]} -->

- [x] T028 [CODE] [US-001] Implementar a interpretação da resposta por IA em src/pipeline/decisoes/interpretacao.py — Refs: US-001, FR-001, FR-002, NFR-001, NFR-003, AC-001, AC-004, AC-023 — Depends: T001, T004, T023, T027
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_decisoes_interpretacao.py`.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_decisoes_interpretacao.py -q` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T028", "refs": ["US-001", "FR-001", "FR-002", "NFR-001", "NFR-003", "AC-001", "AC-004", "AC-023"], "files": ["src/pipeline/decisoes/interpretacao.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_decisoes_interpretacao.py -q", "exit": 0}]} -->

- [x] T029 [CODE] [US-001] Expor interpretar_resposta, localizar_trecho e aplicar_correcao na fachada src/pipeline/service.py — Refs: US-001, FR-001, FR-002, FR-004, NFR-001, NFR-003, AC-001, AC-005 — Depends: T001, T005, T028, T027
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_decisoes_interpretacao.py tests/test_decisoes_localizacao.py` e `tests/test_architecture.py`.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_decisoes_interpretacao.py tests/test_decisoes_localizacao.py tests/test_application_boundaries.py -q` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T029", "refs": ["US-001", "FR-001", "FR-002", "FR-004", "NFR-001", "NFR-003", "AC-001", "AC-005"], "files": ["src/pipeline/service.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_decisoes_interpretacao.py tests/test_decisoes_localizacao.py tests/test_application_boundaries.py -q", "exit": 0}]} -->

- [x] T030 [CODE] [US-001] Orquestrar a interpretação (chave de IA, aviso, tarefa interpretar_resposta_task) em src/app/decisoes.py e src/app/tasks.py — Refs: US-001, US-002, FR-001, FR-003, FR-004, FR-008, NFR-001, AC-002, AC-006, AC-009, AC-010 — Depends: T002, T006, T009, T010, T029, T025
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_router_decisoes.py -k 'AC-002 or AC-006 or AC-009 or AC-010'` e `tests/test_decisoes_interpretacao.py`.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_router_decisoes.py tests/test_decisoes_interpretacao.py -q` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T030", "refs": ["US-001", "US-002", "FR-001", "FR-003", "FR-004", "FR-008", "NFR-001", "AC-002", "AC-006", "AC-009", "AC-010"], "files": ["src/app/decisoes.py", "src/app/tasks.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_router_decisoes.py tests/test_decisoes_interpretacao.py -q", "exit": 0}]} -->

- [x] T031 [CODE] [US-002] Orquestrar confirmação, aplicação com verificação de hash, nova versão, publicação por novo envio e registro de decisão em src/app/decisoes.py — Refs: US-002, US-003, FR-003, FR-004, FR-005, NFR-002, AC-007, AC-008, AC-012, AC-015 — Depends: T007, T008, T012, T015, T030
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_decisoes_aplicacao.py tests/test_router_decisoes.py`.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_decisoes_aplicacao.py tests/test_router_decisoes.py -q` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T031", "refs": ["US-002", "US-003", "FR-003", "FR-004", "FR-005", "NFR-002", "AC-007", "AC-008", "AC-012", "AC-015"], "files": ["src/app/decisoes.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_decisoes_aplicacao.py tests/test_router_decisoes.py -q", "exit": 0}]} -->

- [x] T032 [CODE] [US-003] Orquestrar versões, restauração, comparação entre rodadas, liberação da coleção e retenção (purgar_versoes_task) em src/app/decisoes.py, src/app/repo.py e src/app/tasks.py — Refs: US-003, US-004, US-005, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-001, AC-013, AC-014, AC-016, AC-019, AC-021 — Depends: T013, T014, T016, T019, T021, T031
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_decisoes_retencao.py tests/test_router_decisoes.py`.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_decisoes_retencao.py tests/test_router_decisoes.py -q` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T032", "refs": ["US-003", "US-004", "US-005", "FR-004", "FR-005", "FR-006", "FR-007", "FR-008", "NFR-001", "AC-013", "AC-014", "AC-016", "AC-019", "AC-021"], "files": ["src/app/decisoes.py", "src/app/tasks.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_decisoes_retencao.py tests/test_router_decisoes.py -q", "exit": 0}]} -->

- [x] T033 [CODE] [US-001] Criar as rotas em src/app/routers/decisoes.py, registrá-las em src/app/main.py e limpar dados na exclusão da coleção em src/app/routers/colecoes.py — Refs: US-001, US-003, US-004, US-005, FR-001, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-001, AC-002, AC-006, AC-012, AC-013, AC-016, AC-019, AC-021 — Depends: T002, T006, T012, T013, T016, T019, T021, T032
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `tests/test_router_decisoes.py tests/test_router_colecoes.py`.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_router_decisoes.py tests/test_app_colecoes.py -q` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T033", "refs": ["US-001", "US-003", "US-004", "US-005", "FR-001", "FR-004", "FR-005", "FR-006", "FR-007", "FR-008", "NFR-001", "AC-002", "AC-006", "AC-012", "AC-013", "AC-016", "AC-019", "AC-021"], "files": ["src/app/routers/decisoes.py", "src/app/main.py", "src/app/routers/colecoes.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_router_decisoes.py tests/test_app_colecoes.py -q", "exit": 0}]} -->

#### Fase de interface

- [x] T034 [CODE] [US-001] Criar CaixaRespostaEmpresa em frontend/src/features/decisoes/CaixaRespostaEmpresa.tsx — Refs: US-001, US-004, FR-001, FR-006, NFR-001, AC-003, AC-018 — Depends: T003, T018, T033
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes`, ESLint e `tsc`.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia por inspeção de DOM e classes (sem navegador real) contra DESIGNSYSTEM.MD e INTERFACE.md, em desktop e 375 px: `flex-col sm:flex-row`, `min-w-0`, `break-words`/`[overflow-wrap:anywhere]` e nenhum `overflow-x`, nos estados carregando, vazio, erro, sucesso, claras, incertas e Sem decisão; `text-sm`, `gap-2/3` e `p-4` seguem os blocos da SPEC-0038; nenhum ajuste necessário além do empilhamento do grupo de ações.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T034", "refs": ["US-001", "US-004", "FR-001", "FR-006", "NFR-001", "AC-003", "AC-018"], "files": ["frontend/src/features/decisoes/CaixaRespostaEmpresa.tsx"], "commands": [{"run": "cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes", "exit": 0}]} -->

- [x] T035 [CODE] [US-002] Criar BlocoPropostasClaras e PropostaIncerta em frontend/src/features/decisoes/BlocoPropostasClaras.tsx e PropostaIncerta.tsx — Refs: US-002, NFR-004, AC-022 — Depends: T022, T033
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes`, ESLint e `tsc`.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia por inspeção de DOM e classes (sem navegador real) contra DESIGNSYSTEM.MD e INTERFACE.md, em desktop e 375 px: `flex-col sm:flex-row`, `min-w-0`, `break-words`/`[overflow-wrap:anywhere]` e nenhum `overflow-x`, nos estados carregando, vazio, erro, sucesso, claras, incertas e Sem decisão; `text-sm`, `gap-2/3` e `p-4` seguem os blocos da SPEC-0038; nenhum ajuste necessário além do empilhamento do grupo de ações.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T035", "refs": ["US-002", "NFR-004", "AC-022"], "files": ["frontend/src/features/decisoes/BlocoPropostasClaras.tsx", "frontend/src/features/decisoes/PropostaIncerta.tsx"], "commands": [{"run": "cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes", "exit": 0}]} -->

- [x] T036 [CODE] [US-004] Criar ResumoRodada e estender CartaoOcorrencia com o selo Corrigido e o link Ver versões em frontend/src/features/decisoes/ResumoRodada.tsx e frontend/src/features/contradicoes/CartaoOcorrencia.tsx — Refs: US-004, FR-001, FR-006, NFR-001, NFR-004, AC-016, AC-017, AC-018 — Depends: T016, T017, T018, T033
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes`, ESLint e `tsc`.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia por inspeção de DOM e classes (sem navegador real) contra DESIGNSYSTEM.MD e INTERFACE.md, em desktop e 375 px: `flex-col sm:flex-row`, `min-w-0`, `break-words`/`[overflow-wrap:anywhere]` e nenhum `overflow-x`, nos estados carregando, vazio, erro, sucesso, claras, incertas e Sem decisão; `text-sm`, `gap-2/3` e `p-4` seguem os blocos da SPEC-0038; nenhum ajuste necessário além do empilhamento do grupo de ações.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T036", "refs": ["US-004", "FR-001", "FR-006", "NFR-001", "NFR-004", "AC-016", "AC-017", "AC-018"], "files": ["frontend/src/features/decisoes/ResumoRodada.tsx", "frontend/src/features/contradicoes/CartaoOcorrencia.tsx"], "commands": [{"run": "cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes", "exit": 0}]} -->

- [x] T037 [CODE] [US-005] Criar LiberarColecaoDialog em frontend/src/features/decisoes/LiberarColecaoDialog.tsx — Refs: US-005, FR-007, NFR-004, AC-020 — Depends: T020, T033
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes`, ESLint e `tsc`.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia por inspeção de DOM e classes (sem navegador real) contra DESIGNSYSTEM.MD e INTERFACE.md, em desktop e 375 px: `flex-col sm:flex-row`, `min-w-0`, `break-words`/`[overflow-wrap:anywhere]` e nenhum `overflow-x`, nos estados carregando, vazio, erro, sucesso, claras, incertas e Sem decisão; `text-sm`, `gap-2/3` e `p-4` seguem os blocos da SPEC-0038; nenhum ajuste necessário além do empilhamento do grupo de ações.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T037", "refs": ["US-005", "FR-007", "NFR-004", "AC-020"], "files": ["frontend/src/features/decisoes/LiberarColecaoDialog.tsx"], "commands": [{"run": "cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes", "exit": 0}]} -->

- [x] T038 [CODE] [US-003] Criar VersoesDocumentoSheet e ligá-lo ao detalhe do documento em frontend/src/features/decisoes/VersoesDocumentoSheet.tsx — Refs: US-003, FR-004, FR-005, FR-008, AC-013 — Depends: T013, T033
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes`, ESLint e `tsc`.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia por inspeção de DOM e classes (sem navegador real) contra DESIGNSYSTEM.MD e INTERFACE.md, em desktop e 375 px: `flex-col sm:flex-row`, `min-w-0`, `break-words`/`[overflow-wrap:anywhere]` e nenhum `overflow-x`, nos estados carregando, vazio, erro, sucesso, claras, incertas e Sem decisão; `text-sm`, `gap-2/3` e `p-4` seguem os blocos da SPEC-0038; nenhum ajuste necessário além do empilhamento do grupo de ações.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T038", "refs": ["US-003", "FR-004", "FR-005", "FR-008", "AC-013"], "files": ["frontend/src/features/decisoes/VersoesDocumentoSheet.tsx", "frontend/src/features/colecoes/DataGridDocumentos.tsx"], "commands": [{"run": "cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes", "exit": 0}]} -->

- [x] T039 [CODE] [US-001] Compor os blocos na rota do relatório (frontend/src/features/contradicoes/RelatorioContradicoes.tsx) e na página da coleção, com papéis e estados — Refs: US-001, US-002, US-004, US-005, FR-001, FR-006, FR-007, NFR-001, NFR-004, AC-003, AC-017, AC-020, AC-022 — Depends: T003, T017, T020, T022, T034, T035, T036, T037, T038
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes`, ESLint e `tsc`.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia por inspeção de DOM e classes (sem navegador real) contra DESIGNSYSTEM.MD e INTERFACE.md, em desktop e 375 px: `flex-col sm:flex-row`, `min-w-0`, `break-words`/`[overflow-wrap:anywhere]` e nenhum `overflow-x`, nos estados carregando, vazio, erro, sucesso, claras, incertas e Sem decisão; `text-sm`, `gap-2/3` e `p-4` seguem os blocos da SPEC-0038; nenhum ajuste necessário além do empilhamento do grupo de ações.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes` em 2026-10-16: verde; IDs nas seções 11–13.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.
  <!-- specsfy:evidence {"task": "T039", "refs": ["US-001", "US-002", "US-004", "US-005", "FR-001", "FR-006", "FR-007", "NFR-001", "NFR-004", "AC-003", "AC-017", "AC-020", "AC-022"], "files": ["frontend/src/features/contradicoes/RelatorioContradicoes.tsx", "frontend/src/features/decisoes/PainelDecisaoEmpresa.tsx", "frontend/src/features/decisoes/useDecisoes.ts"], "commands": [{"run": "cd frontend && npx vitest run src/features/decisoes src/features/contradicoes src/features/colecoes", "exit": 0}]} -->

#### Fechamento

- [x] T040 [DOC] Atualizar INTERFACE.md, PROJECT.md, docs/architecture.md e specs.md com os blocos e operações da SPEC-0039 — Refs: AC-003, AC-017, AC-020, AC-022, FR-006, FR-007, NFR-004 — Depends: T039
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check`.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: `node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check` em 2026-10-16: exit 0; INTERFACE.md, PROJECT.md e docs/architecture.md atualizados.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.

- [x] T041 [OPS] Executar a regressão completa (pytest, vitest, ruff, ESLint, tsc, build) e a rastreabilidade da spec em specs/review/0039-fase-1-decisao-da-empresa-e-atualizacao/spec.md — Refs: NFR-001, NFR-002, NFR-003, NFR-004 — Depends: T040
  - [x] **PREP**: Confirmar o RED TDD dos predecessores e as dependências.
  - [x] **EXECUTE**: Implementar a menor mudança que torna o teste verde.
  - [x] **VERIFY**: Executar `.venv/bin/python -m pytest -q`, `npx vitest run`, `ruff check .`, `npm run build` e `check_traceability.mjs --full-chain`.
  - [x] **VISUAL**: Não aplicável: sem superfície visual.
  - [x] **EVIDENCE**: pytest completo, vitest completo, `ruff check .`, ESLint, `tsc`, `npm run build` e `check_traceability.mjs --full-chain` em 2026-10-16 (resultados na seção 12).
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a menor mudança já atende ao teste e segue o padrão das SPEC-0037 e SPEC-0038.

### 15. Ordem de execução

- Caminho crítico: T001–T024 (RED) → T025 (migration) → T027 (localização e aplicação) → T028 (interpretação) → T029 (fachada) → T030–T032 (orquestração) → T033 (rotas) → T034–T039 (interface) → T040 (documentação) → T041 (regressão).
- Tarefas paralelas: as tarefas `[TEST] [TDD]` não compartilham estado e podem ser escritas em paralelo; T034, T035, T036, T037 e T038 são componentes independentes.
- Estratégia de MVP: US-001, US-002 e US-003 primeiro (interpretar, confirmar e aplicar), depois US-004 e US-005.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0037: conexão de IA por Workspace, chave de IA externa, papéis (DEC-007) e resumo do domínio.
- SPEC-0038: análises e ocorrências com os trechos de origem; o novo ciclo reutiliza a análise.
- SPEC-0030 (coleções e envios) para publicar a versão corrigida; SPEC-0002 (contrato do `.md`).
- Gabarito de documentos reais, fora do repositório, para a meta de 70%.

#### Riscos

- A IA reescreve mais que o pedido → só o trecho alvo é substituído por localização determinística, com diff, confirmação humana e histórico.
- Corrigir o trecho errado quando há textos parecidos → localização exata primeiro; ambiguidade ou semelhança abaixo do limite vira "incerta".
- Documento muda entre a análise e a confirmação → verificação de hash recusa a correção.
- Vazamento da resposta da empresa → chave por Workspace, aviso antes do envio, provider espião nos testes e ausência de texto em logs.
- Coleção corrigida depois de "revisada" → nova versão é publicada por novo envio, e a marca "revisada" é mantida com aviso de que há alteração posterior (ver suposições).

#### Suposições

- "Revisada" não bloqueia consulta nem envio (DEC-006, confirmada em 2026-10-16).
- A correção localiza o trecho por correspondência exata e, na falta dela, por semelhança textual alta; abaixo do limite, a proposta é "incerta" e exige edição.
- "Revisada" é uma marca de estado da coleção (autor e data) e não bloqueia consulta nem envio; a versão corrigida é publicada à coleção por um novo envio do documento ao aplicar a correção, o que a reindexa.
- Correção após a liberação mantém "revisada" e mostra um aviso "alterada depois da revisão" até nova liberação.
- Uma resposta da empresa trata de uma análise específica; resposta nova exige reinterpretação.
- O texto da resposta tem até 20000 caracteres na primeira versão.

### 17. Decisões

- **DEC-001**: checkpoint humano em toda escrita — a IA propõe, a pessoa confirma; alternativa descartada: aplicar automaticamente as claras.
- **DEC-002**: substituir só o trecho alvo com localização determinística e hash do documento — evita reescritas amplas pela IA.
- **DEC-003**: histórico por versões numeradas com a anterior preservada por 90 dias e registro de decisões enquanto a coleção existir — alinhado a `.specsfy/DATABASE.md`.
- **DEC-004**: publicar a versão corrigida por novo envio do documento à coleção (mesmo nome de arquivo), reaproveitando a reindexação existente — alternativa descartada: pipeline de reindexação paralelo.
- **DEC-005**: papéis conforme a DEC-007 da SPEC-0037: owner e admin escrevem e liberam, member consulta.
- **DEC-006** (confirmada pela pessoa responsável em 2026-10-16, com nada em produção): "Liberar para a base" é uma marca de revisão e não uma operação de movimento de dados nem bloqueio de consulta — a coleção já é a base vetorial. Bloquear consultas até a revisão ou indexar só na liberação ficam para uma spec própria, se o requisito surgir.
- **DEC-007** (confirmada pela pessoa responsável em 2026-10-16): o gabarito é verificação final opt-in na entrega, com o conjunto que a pessoa trouxer, e não condição da definição; a meta de 70% é medida na entrega.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] `.specsfy/DATABASE.md` descreve as tabelas e colunas novas da migration `0039_decisoes_empresa`.
- [x] `PROJECT.md` foi revisado (decisão da empresa e liberação da coleção) e `INTERFACE.md` registra os blocos novos.
- [x] Testes e checks estáticos disponíveis passam.
