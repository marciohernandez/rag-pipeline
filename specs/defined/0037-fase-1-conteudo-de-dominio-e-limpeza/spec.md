# Especificação integrada: Fase 1: conteúdo de domínio e limpeza

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0037 |
| Slug | 0037-fase-1-conteudo-de-dominio-e-limpeza |
| Status | Defined |
| Effort | 8 |
| Effort updated at | 2026-10-16 |
| Effort rationale | Combina filtro em camadas com IA e confiança, duplicidade entre documentos, nova persistência com retenção, nova conexão por Workspace, privacidade e três pontos de interface; exige raciocínio sobre perda de informação e ordem de etapas. |
| ClickUp Task | |
| Milestones | M04 |
| Definition Gate | Passed |
| Plan Gate | Pending |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-16 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

A conversão da Fase 1 (SPEC-0023 e SPEC-0036) entrega Markdown fiel ao original, e o original traz acessórios (numeração de página, rodapés repetidos, menus, avisos de cookie, saudações) e repetições entre documentos. Esse ruído e essa duplicidade passam para a base vetorial na Fase 2 e pioram a recuperação. A pessoa da consultoria que prepara a base de conhecimento a partir de documentos de uma empresa cliente hoje remove isso à mão.

#### Resultado desejado

Cada lote convertido gera Markdown só com informação de domínio da empresa, sem acessórios e sem duplicidade, com toda exclusão registrada em log auditável e um relatório do lote que lista exclusões, dúvidas e duplicidades para conferência. Em caso de dúvida o conteúdo é mantido: perder informação real é pior que manter algum ruído.

#### Métricas de sucesso

- Medido contra o gabarito de 3 ou 4 documentos reais da pessoa (fora do repositório): nenhum trecho marcado como "deve ficar" é removido (alvo 0) e a maior parte do ruído marcado é removida. Verificação final opt-in na entrega (DEC-008): o gabarito ainda não foi entregue e o percentual mínimo de ruído removido será fixado com ele; até lá valem o alvo de 0 trechos "deve ficar" removidos e a verificação com corpus sintético.
- 100% das exclusões aparecem no log com motivo, arquivo e posição.
- 0 envios de texto a uma IA externa em Workspace com a chave "permitir análise por IA externa" desligada.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: leitura do código da conversão (`src/app/tasks.py`, `src/pipeline/conversion/`, `src/app/routers/conversao.py`) e do modelo de papéis → a limpeza entra depois da conversão de cada documento e antes da liberação do `.md`; `PAPEIS_DE_ESCRITA` é `{owner, admin}`, e não existe papel intermediário entre quem escreve e quem administra (ver DEC-007).

#### Fontes e contexto consultados

- `specs/backlog/0041-fase-1-conteudo-de-dominio-e-limpeza.md` (decisões das Perguntas 1 a 9 e da descoberta de dados de 2026-10-13).
- `specs/milestones/M04.md` (objetivo, condição de saída e exceção de 2026-10-16).
- `specs/completed/0023-*/spec.md` e `specs/completed/0036-*/spec.md` (conversão e formatos), `specs/completed/0002-*/spec.md` (contrato do Markdown), `specs/completed/0030-*/spec.md` (Workspaces e coleções).
- `.specsfy/DATABASE.md` (linhas de IA para análise, resumo do domínio, log de exclusões, relatórios e situação por documento).
- `INTERFACE.md`, `DESIGNSYSTEM.MD` e `frontend/src/features/{conversao,workspaces,conexoes}/`.

#### Documentação consultada

- Nenhuma documentação externa. O contrato do provider de IA é o `ChatModelAdapter` local (`src/pipeline/providers/contracts.py`).

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Quais as camadas do filtro? → **A**: regras fixas, IA com confiança, baixa confiança mantida e marcada; nada é descartado em silêncio (backlog, Pergunta 1).
- **Q**: Como se define o domínio da empresa? → **A**: a IA propõe a partir de uma amostra do lote, a pessoa confirma ou corrige, e o resumo fica no Workspace (Pergunta 5).
- **Q**: O que é duplicidade removível? → **A**: igualdade após normalização, ou semelhança de pelo menos 95% entre parágrafos ou seções com no mínimo 200 caracteres; abaixo disso só a igualdade normalizada. O que não atinge o critério vai ao relatório (Pergunta 9, limite configurável).
- **Q**: Onde a pessoa confirma o domínio? → **A**: no lote, antes da limpeza, e também numa seção "Domínio da empresa" em `/workspaces/[id]` com o mesmo componente (Interface, Pergunta 1).
- **Q**: Onde ficam o resultado, a conexão e a chave de IA? → **A**: contagens e download no painel do lote; conexão e chave na seção do Workspace (Interface, Perguntas 2 e 3).
- **Q**: Como o painel se comporta com IA fora do ar ou domínio não confirmado? → **A**: aviso no topo; IA fora segue só com regras fixas, domínio não confirmado impede a limpeza (Interface, Pergunta 4).
- **Q**: Como o andamento e a falha aparecem? → **A**: situação por documento, progresso do lote, motivo da falha e retomada só dos que falharam (Interface, Pergunta 6).
- **Q**: O sistema só tem owner, admin e member; como tratar "editor" versus "quem administra" (Interface, Pergunta 5)? → **A**: sem papel novo; owner e admin fazem tudo e member só consulta (2026-10-16, opção 1).
- **Q**: Qual a ordem entre a limpeza e a análise de contradições? → **A**: a análise (BACKLOG-0042) roda a pedido sobre os `.md` já limpos da coleção e usa o resumo do domínio como contexto; a limpeza nunca depende dela (2026-10-16, opção 1).
- **Q**: Como é no celular? → **A**: coluna única, aviso fixo no topo, textos longos quebram sem rolagem horizontal (Interface, Pergunta 7).

#### Dúvidas abertas

- Nenhuma bloqueante. O gabarito (3 ou 4 documentos, fora do repositório) e o percentual mínimo de ruído removido são verificação final opt-in na entrega, com o conjunto que a pessoa trouxer, e não condição da definição (DEC-008). Permissões e ordem com contradições foram resolvidas em 2026-10-16 (DEC-006 e DEC-007).

### 3. Escopo e atores

#### Incluído

- Limpeza em três camadas dentro do lote de conversão: regras fixas, avaliação por IA com grau de confiança e marcação de dúvidas.
- Remoção automática de duplicidade exata ou quase exata entre os documentos do lote, mantendo uma cópia e registrando as origens.
- Resumo do domínio por Workspace: proposta pela IA, confirmação ou correção, histórico de versões.
- Nova conexão do tipo "IA para análise de documentos", escolhida por Workspace, e a chave "permitir análise por IA externa".
- Log de exclusões e relatório do lote baixável junto dos `.md`, com retenção definida.
- Situação e contagens de dúvidas por documento no painel do lote.

#### Fora de escopo

- Detecção de contradições e seu relatório (BACKLOG-0042).
- Decisão da empresa, atualização e liberação dos `.md` (BACKLOG-0043).
- Sequências de imagens e tabelas (BACKLOG-0040).
- Q&A e expansão de perguntas (BACKLOG-0044).
- Tela própria de conferência, edição de trechos dentro do sistema e PDF do relatório (a conferência acontece fora do sistema na primeira versão).
- Remover informação apenas parecida, com outras palavras, sem decisão humana.
- Papel novo de permissão (ver DEC-007).

#### Atores

- **Owner e admin (papel de escrita)**: rodam o lote, confirmam ou corrigem o resumo do domínio, configuram a chave e a conexão de IA, baixam o relatório, veem o texto removido e o histórico do domínio.
- **Member**: só consulta o resumo vigente do domínio; não vê texto removido nem relatório de exclusões.
- **IA de análise**: modelo externo escolhido por Workspace; propõe o domínio e classifica seções, sem decisão final sobre dúvidas.

### 4. Princípios e restrições do projeto

- **PR-001**: em dúvida sobre relevância o conteúdo é mantido; nenhuma decisão de baixa confiança descarta informação.
- **PR-002**: nenhuma exclusão ocorre sem registro no log.
- **PR-003**: textos e arquivos de clientes, inclusive o gabarito, ficam fora do repositório; só o resumo do domínio aprovado, os logs e os relatórios são guardados no sistema, com retenção definida.
- **PR-004**: toda fronteira com IA passa pelo contrato `ChatModelAdapter`, sem credenciais nos logs (arquitetura LangChain-first e modular da constituição do projeto-mãe).
- **PR-005**: testes nunca usam o banco de desenvolvimento; usam a instância isolada de testes e transações restritas aos registros do caso.
- **PR-006**: interface reutiliza `PageHeader`, `Sheet`, `Dialog`, `Badge`, `Alert` e os padrões de `features/conversao` e `features/conexoes`; novos blocos entram em `INTERFACE.md`.

### 5. Histórias de usuário

#### US-001 — Remover ruído óbvio com regras fixas (P1)

Como pessoa da consultoria, quero que numeração de página, rodapés repetidos, menus, avisos de cookie e saudações sejam removidos do Markdown, para receber só o conteúdo do negócio sem depender de IA externa.

**Por que P1**: é a base da limpeza, funciona sem custo nem risco de privacidade e reduz o que a IA precisa avaliar.
**Teste independente**: processar um documento com ruído e informação de negócio em Workspace sem IA e conferir texto e log.
**Requisitos**: FR-001, FR-002, FR-009

#### US-002 — Definir o domínio da empresa do Workspace (P1)

Como pessoa da consultoria, quero que a IA proponha um resumo do domínio a partir dos documentos do lote e que eu o confirme ou corrija, para que a limpeza saiba o que é informação de negócio daquela empresa.

**Por que P1**: sem domínio confirmado a avaliação por IA não tem critério e a limpeza não começa.
**Teste independente**: abrir um lote em Workspace sem resumo, receber a proposta, confirmar e ver a versão vigente na página do Workspace.
**Requisitos**: FR-003, FR-004, FR-009

#### US-003 — Avaliar a relevância das seções restantes por IA (P1)

Como pessoa da consultoria, quero que uma IA avalie cada seção restante com um grau de confiança e que as dúvidas sejam mantidas e marcadas, para não perder informação real e saber o que conferir.

**Por que P1**: entrega o filtro de domínio e a garantia de não descartar em silêncio.
**Teste independente**: processar seções claramente irrelevantes, relevantes e ambíguas com um modelo simulado e conferir remoção, manutenção e marcação.
**Requisitos**: FR-002, FR-004, FR-005

#### US-004 — Eliminar duplicidade entre documentos (P1)

Como pessoa da consultoria, quero que o mesmo trecho em vários documentos permaneça uma só vez com as origens registradas, para não poluir a base com repetição.

**Por que P1**: duplicidade piora a recuperação e foi pedida desde a captura original.
**Teste independente**: processar dois documentos com um parágrafo igual e outro quase igual e conferir o resultado e o relatório.
**Requisitos**: FR-006, FR-007

#### US-005 — Acompanhar a limpeza e baixar o relatório do lote (P2)

Como pessoa da consultoria, quero ver no painel do lote a situação e as contagens de cada documento, os avisos de IA ou domínio e baixar o relatório junto dos `.md`, para conferir o que a limpeza fez.

**Por que P2**: permite a conferência humana, mas depende das camadas anteriores.
**Teste independente**: processar um lote com falha simulada em um documento e conferir situações, motivo, retomada e relatório baixado.
**Requisitos**: FR-007, FR-008, FR-009

### 6. Cenários BDD de aceite

#### AC-001 — Ruído óbvio sai e o negócio permanece

**Cobre**: US-001, FR-001, FR-002, NFR-002

```gherkin
@US-001 @FR-001 @FR-002 @NFR-002 @AC-001
Feature: Regras fixas de limpeza

  Scenario: ruído óbvio removido com informação de negócio preservada
    Given um documento convertido com número de página isolado, rodapé repetido em várias páginas e parágrafos sobre o negócio
    When o lote é limpo
    Then o número de página e o rodapé repetido não aparecem no Markdown limpo
    And todos os parágrafos sobre o negócio permanecem
    And cada remoção aparece no log com motivo, arquivo e posição
```

#### AC-002 — Número dentro de frase não é ruído

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-002
Feature: Regras fixas de limpeza

  Scenario: número dentro de uma frase e linha curta de negócio permanecem
    Given um documento com a frase "O plano básico custa 49 reais por mês" e uma linha isolada "42" que é número de página
    When o lote é limpo
    Then a frase permanece intacta
    And somente a linha isolada "42" é removida
```

#### AC-003 — Documento limpo passa sem alteração

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-003
Feature: Regras fixas de limpeza

  Scenario: documento sem ruído não muda e não gera exclusões
    Given um documento convertido só com informação de negócio
    When o lote é limpo
    Then o Markdown limpo é idêntico ao convertido
    And o log de exclusões do documento fica vazio
```

#### AC-004 — Retenção do texto removido e acesso restrito

**Cobre**: US-001, FR-002, FR-009, NFR-001

```gherkin
@US-001 @FR-002 @FR-009 @NFR-001 @AC-004
Feature: Log de exclusões

  Scenario: texto completo por 30 dias, depois só motivo, arquivo e posição
    Given uma exclusão registrada há 31 dias e outra há 5 dias
    When a rotina de retenção roda
    Then a exclusão antiga mantém motivo, arquivo e posição e perde o texto removido
    And a recente mantém o texto
    And uma pessoa com papel member não consegue ler o texto removido de nenhuma delas
```

#### AC-005 — Proposta e confirmação do domínio

**Cobre**: US-002, FR-003, FR-004, FR-009

```gherkin
@US-002 @FR-003 @FR-004 @FR-009 @AC-005
Feature: Resumo do domínio

  Scenario: Workspace sem resumo recebe proposta e a pessoa confirma
    Given um Workspace com IA externa permitida e sem resumo do domínio
    When a conversão do lote termina
    Then o lote fica aguardando a confirmação do domínio com um resumo proposto a partir de uma amostra dos documentos
    And ao owner ou admin confirmar o resumo ele vira a versão vigente com autor e data
    And a limpeza começa
```

#### AC-006 — Reajuste cria versão e o relatório a cita

**Cobre**: US-002, FR-003, FR-007, FR-009

```gherkin
@US-002 @FR-003 @FR-007 @FR-009 @AC-006
Feature: Resumo do domínio

  Scenario: reajuste gera nova versão e o relatório registra a versão usada
    Given um Workspace com a versão 1 do resumo vigente
    When owner ou admin corrige o resumo e um lote é limpo
    Then existe a versão 2 vigente e a versão 1 permanece no histórico
    And o relatório do lote cita a versão 2
    And um member consulta o resumo vigente mas não consegue listar o histórico
```

#### AC-007 — Domínio não confirmado bloqueia a limpeza

**Cobre**: US-002, FR-003, FR-008

```gherkin
@US-002 @FR-003 @FR-008 @AC-007
Feature: Resumo do domínio

  Scenario: sem confirmação a limpeza não começa
    Given um lote convertido em Workspace sem resumo confirmado
    When ninguém confirma o resumo
    Then nenhum documento do lote passa de "Aguardando limpeza"
    And o painel mostra o aviso "Confirmar domínio" com o motivo
```

#### AC-008 — Chave desligada não envia texto à IA

**Cobre**: US-003, FR-004, FR-005, NFR-001

```gherkin
@US-003 @FR-004 @FR-005 @NFR-001 @AC-008
Feature: Privacidade da análise por IA

  Scenario: Workspace com a chave desligada limpa só com regras fixas
    Given um Workspace com "permitir análise por IA externa" desligada e um modelo de IA espião
    When o lote é limpo
    Then o modelo de IA não recebe nenhuma chamada
    And só as regras fixas e a duplicidade são aplicadas
    And o relatório informa que a etapa de IA não rodou
```

#### AC-009 — Baixa confiança é mantida e marcada

**Cobre**: US-003, FR-002, FR-005, NFR-002

```gherkin
@US-003 @FR-002 @FR-005 @NFR-002 @AC-009
Feature: Avaliação por IA

  Scenario: remoção só com alta confiança e dúvida mantida
    Given uma seção que a IA classifica como ruído com confiança 0,95 e outra com confiança 0,55
    When o lote é limpo
    Then a primeira é removida e registrada no log com a confiança
    And a segunda permanece no Markdown e aparece no relatório como dúvida
```

#### AC-010 — IA indisponível não perde o lote

**Cobre**: US-003, FR-005, FR-008, NFR-003

```gherkin
@US-003 @FR-005 @FR-008 @NFR-003 @AC-010
Feature: Avaliação por IA

  Scenario: falha da IA mantém o conteúdo e segue com regras fixas
    Given um lote cujo provider de IA falha com indisponibilidade
    When o lote é limpo
    Then nenhuma seção é removida pela IA
    And os documentos ficam limpos só pelas regras fixas com o motivo "IA indisponível" visível
    And o relatório registra que a etapa de IA não rodou
```

#### AC-011 — Parágrafo repetido entre documentos

**Cobre**: US-004, FR-006, FR-007

```gherkin
@US-004 @FR-006 @FR-007 @AC-011
Feature: Duplicidade

  Scenario: mesmo parágrafo em dois documentos permanece uma vez
    Given dois documentos do lote com o mesmo parágrafo de 300 caracteres
    When o lote é limpo
    Then o parágrafo permanece no primeiro documento do lote
    And é removido do segundo
    And o relatório indica os dois arquivos de origem
```

#### AC-012 — Limite de semelhança e trecho curto

**Cobre**: US-004, FR-006, NFR-002

```gherkin
@US-004 @FR-006 @NFR-002 @AC-012
Feature: Duplicidade

  Scenario: semelhança de 96 por cento remove, 94 por cento e trecho curto permanecem
    Given um parágrafo de 400 caracteres com 96% de semelhança com outro de outro documento, um com 94% e dois trechos de 80 caracteres idênticos exceto por um valor numérico
    When o lote é limpo
    Then o de 96% é removido e registrado como duplicidade
    And o de 94% permanece
    And os trechos curtos com valor diferente permanecem
```

#### AC-013 — Lote grande em segundo plano com retomada

**Cobre**: US-005, FR-008, NFR-003

```gherkin
@US-005 @FR-008 @NFR-003 @AC-013
Feature: Andamento da limpeza

  Scenario: 50 documentos em segundo plano e retomada só dos que falharam
    Given um lote de 50 documentos convertidos em que 2 falham na limpeza
    When a limpeza roda e a pessoa pede "Tentar de novo"
    Then o painel mostra o progresso total durante o processamento
    And somente os 2 documentos que falharam são reprocessados
    And os 48 já limpos não são refeitos
```

#### AC-014 — Contagens e relatório baixável

**Cobre**: US-005, FR-007, FR-009, NFR-004

```gherkin
@US-005 @FR-007 @FR-009 @NFR-004 @AC-014
Feature: Relatório do lote

  Scenario: contagens por documento e download com o botão acessível por teclado
    Given um lote limpo com exclusões e dúvidas
    When owner ou admin abre o painel do lote
    Then cada documento mostra suas contagens de exclusões e dúvidas
    And "Baixar relatório do lote" é acionável por teclado e entrega o relatório junto dos .md
    And o relatório não contém o texto removido
```

#### AC-015 — Avisos de IA e de domínio no painel

**Cobre**: US-005, FR-008, NFR-004

```gherkin
@US-005 @FR-008 @NFR-004 @AC-015
Feature: Avisos do painel do lote

  Scenario: aviso explica o motivo e leva ao Workspace
    Given um Workspace com a IA desligada e o domínio já confirmado
    When a pessoa abre o painel do lote
    Then um aviso no topo diz que a limpeza seguirá só com regras fixas e porquê
    And o aviso traz um link para a seção "Domínio da empresa"
    And o aviso é anunciado por tecnologia assistiva com role=status
```

#### AC-016 — Celular sem rolagem horizontal

**Cobre**: US-002, US-005, NFR-004

```gherkin
@US-002 @US-005 @NFR-004 @AC-016
Feature: Responsividade

  Scenario: seção do domínio e aviso do lote em tela de 375 pixels
    Given um viewport de 375 pixels e um resumo do domínio com palavras muito longas
    When a pessoa abre a seção "Domínio da empresa" e o painel do lote
    Then a seção aparece em coluna única, o aviso fica no topo e "Confirmar domínio" ocupa a largura toda
    And nenhum elemento causa rolagem horizontal da página
```

#### AC-017 — Retenção de 90 dias do relatório

**Cobre**: US-005, FR-007, NFR-001

```gherkin
@US-005 @FR-007 @NFR-001 @AC-017
Feature: Relatório do lote

  Scenario: relatório vence em 90 dias
    Given um relatório criado há 91 dias e outro há 10 dias
    When a rotina de retenção roda
    Then o relatório antigo é apagado e o recente permanece
    And os registros do lote permanecem
```

#### AC-018 — Conexão de IA por Workspace

**Cobre**: US-003, FR-004, FR-009, NFR-001

```gherkin
@US-003 @FR-004 @FR-009 @NFR-001 @AC-018
Feature: Conexão de IA para análise

  Scenario: cadastro, seleção e sigilo da chave
    Given owner ou admin cadastra uma conexão do tipo "IA para análise de documentos" com chave
    When ele a seleciona na seção "Domínio da empresa" e liga a chave de IA externa
    Then apenas conexões ativas desse tipo aparecem no seletor
    And a chave nunca é devolvida pela API nem aparece em log
    And um member não consegue alterar a conexão nem a chave
```

#### AC-019 — Semelhante vai ao relatório

**Cobre**: US-004, FR-006, FR-007

```gherkin
@US-004 @FR-006 @FR-007 @AC-019
Feature: Duplicidade

  Scenario: informação parecida com outras palavras não é removida sozinha
    Given dois documentos com o mesmo fato escrito em palavras diferentes e semelhança abaixo do limite
    When o lote é limpo
    Then os dois trechos permanecem
    And o relatório lista o par como duplicidade provável para decisão humana
```

#### AC-020 — IA só avalia o que as regras deixaram

**Cobre**: US-003, FR-005, NFR-003

```gherkin
@US-003 @FR-005 @NFR-003 @AC-020
Feature: Custo da análise por IA

  Scenario: seções já removidas por regra não vão à IA
    Given um documento em que as regras fixas removem 40% das seções
    When a avaliação por IA roda
    Then o modelo recebe somente as seções restantes
    And as chamadas respeitam o tamanho máximo de lote por requisição configurado
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve aplicar regras fixas por documento que removam número de página isolado, linha repetida em várias páginas (rodapé e cabeçalho), itens de menu, avisos de cookie e saudações sociais, sem remover números, termos ou linhas curtas que façam parte de frases de negócio.
- **FR-002**: O sistema deve registrar, para toda remoção (regra, IA ou duplicidade), uma entrada de log com lote, arquivo, posição, motivo, camada, confiança (quando houver) e o trecho removido; o trecho completo é mantido por 30 dias e depois somente motivo, arquivo e posição; a entrada permanece com o registro do lote (que não pertence a uma coleção) e segue as retenções definidas.
- **FR-003**: O sistema deve manter por Workspace um resumo do domínio com histórico de versões: gerar uma proposta pela IA a partir de uma amostra dos documentos do lote quando não houver versão vigente, permitir confirmar ou corrigir (cada ajuste cria nova versão) e impedir que a limpeza comece enquanto não houver versão confirmada.
- **FR-004**: O sistema deve permitir, por Workspace, escolher uma conexão ativa do tipo "IA para análise de documentos" e ligar ou desligar "permitir análise por IA externa"; a chave da conexão é cifrada e nunca devolvida. Com a chave desligada ou sem conexão, nenhum texto sai para IA externa.
- **FR-005**: O sistema deve avaliar por IA cada seção que sobrou das regras fixas quanto à relevância para o domínio, atribuindo um grau de confiança; remover somente seção classificada como ruído com confiança igual ou superior ao limiar configurado (padrão 0,8) e manter e marcar como dúvida as demais, sem nunca descartar em silêncio; falha da IA mantém o conteúdo e segue só com regras fixas.
- **FR-006**: O sistema deve remover duplicidade entre os documentos do lote mantendo uma cópia (a do primeiro documento na ordem do lote) e registrando as origens: igualdade após normalização (caixa, espaços, pontuação, acentos), ou semelhança textual de pelo menos 95% entre parágrafos ou seções com no mínimo 200 caracteres; abaixo disso só a igualdade normalizada remove; o que não atinge o critério é listado no relatório como duplicidade provável. Os dois limites são configuráveis.
- **FR-007**: O sistema deve gerar, por lote, um relatório em Markdown com exclusões (sem o texto removido), dúvidas, duplicidades prováveis, se a IA foi usada e qual provedor, e a versão do domínio usada; baixável junto dos `.md` e guardado por 90 dias.
- **FR-008**: O sistema deve processar a limpeza em segundo plano com situação por documento ("Aguardando limpeza", "Limpando", "Limpo", "Limpo com dúvidas", "Falhou"), progresso do lote, motivo da falha por documento e retomada que reprocessa somente os documentos que falharam; documentos já limpos permanecem.
- **FR-009**: O sistema deve aplicar as permissões: owner e admin rodam o lote, confirmam e corrigem o domínio, configuram chave e conexão de IA, baixam o relatório e veem o texto removido e o histórico do domínio; member apenas consulta o resumo vigente e vê as contagens.

#### Não funcionais

- **NFR-001**: Privacidade e sigilo: nenhum texto vai à IA externa com a chave desligada; chaves e textos de clientes não aparecem em logs; retenção de 30 dias para o texto removido e de 90 dias para o relatório. **Verificação**: testes com provider espião, varredura de logs em teste e rotina de retenção com datas simuladas.
- **NFR-002**: Preservação da informação: nenhum trecho de negócio é removido por regra fixa ou por duplicidade abaixo do critério, e dúvida é sempre mantida. **Verificação**: testes com corpus sintético de "deve ficar" e, quando entregue, o gabarito real (alvo: 0 trechos "deve ficar" removidos).
- **NFR-003**: Desempenho e custo: um lote típico de 10 a 50 documentos, alguns longos, processa em segundo plano com progresso visível; a IA recebe somente as seções que as regras fixas deixaram, em requisições limitadas por tamanho; falha parcial não refaz os documentos concluídos. **Verificação**: teste com 50 documentos simulados e contagem de chamadas ao modelo espião.
- **NFR-004**: Acessibilidade e responsividade: as novas telas e avisos operam por teclado, usam `role=status` nos avisos, foco visível e funcionam em 375 px sem rolagem horizontal da página. **Verificação**: testes de componente com Testing Library e conferência visual em desktop e mobile.

#### Erros e casos-limite

- IA indisponível ou chave desligada → o lote segue só com regras fixas e o relatório informa que a etapa de IA não rodou.
- Resumo do domínio não confirmado → a limpeza não começa; o painel orienta a confirmar.
- Workspace sem conexão de IA nem resumo, com IA desligada → a pessoa escreve o resumo à mão; sem resumo a limpeza não começa.
- Documento ilegível ou falha na limpeza de um documento → ele fica "Falhou" com motivo; os demais seguem.
- Seção que a IA devolve sem classificação válida → tratada como dúvida (mantida e marcada).
- Documento vazio após as regras fixas → mantido como está e sinalizado como dúvida para o relatório (nunca zerado em silêncio).
- Apagar uma coleção → não afeta log nem relatório do lote, porque o lote não pertence a uma coleção; ambos seguem as retenções de 30 e 90 dias.
- Gabarito ou resumo com dados do cliente nunca entram no repositório.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI + SQLAlchemy + Alembic, worker Procrastinate (`src/app/tasks.py`), pipeline em `src/pipeline/` com fachada `src/pipeline/service.py`; provider de IA pelo contrato `ChatModelAdapter` (`src/pipeline/providers/contracts.py`, `llm/openrouter.py`).
- Conversão por documento em `process_conversion_document_task`; lote em `LoteConversao`/`DocumentoConversao`; situação do lote recalculada por `recalcular_situacao_lote`.
- Conexões em `src/app/conexoes.py` (`TIPOS`, chave cifrada com Fernet) e frontend em `features/conexoes`.
- Hoje a IA do reprocessamento usa `settings.llm` global; a limpeza passa a usar a conexão do Workspace.
- Testes: Pytest em banco isolado `rag_spec0036_test`; frontend com Vitest.

#### Arquitetura e módulos

- `src/pipeline/limpeza/` (novo, sem acesso a HTTP nem banco): `regras.py` (camada 1), `avaliacao_ia.py` (camada 2, grafo LangGraph simples sobre `ChatModelAdapter`, prompt com o resumo do domínio e saída estruturada com `relevante`/`ruido` e `confianca`), `duplicidade.py` (normalização e semelhança), `dominio.py` (proposta a partir de amostra), `relatorio.py` (montagem do Markdown) e `contratos.py` (dataclasses `SecaoAvaliada`, `Exclusao`, `ResultadoLimpeza`).
- `src/pipeline/conversion/` permanece responsável por converter; a limpeza roda como estágio posterior no worker.
- `src/app/limpeza.py` (novo): orquestra o estágio por lote (carrega domínio, conexão e chave, grava log, relatório e situações) e a rotina de retenção.
- Fluxo: conversão do documento → (quando todos os documentos do lote estão convertidos) o lote vai a `aguardando_dominio` se não há versão vigente, ou segue → limpeza por documento (regras, depois IA) → duplicidade do lote → relatório → documento "Limpo" ou "Limpo com dúvidas".
- Limiar de confiança, limites de semelhança e tamanho de requisição ficam em `ConversaoConfig`/`config.yaml` com padrões 0,8, 0,95 e 200 caracteres.
- A fachada `service.py` expõe `limpar_documento`, `deduplicar_lote`, `propor_dominio` e `montar_relatorio_lote`, mantendo a fronteira do pipeline.

#### Migrations

- Revisão `0037_limpeza_dominio` encadeada após `0036_conversao_formatos`: cria `dominios_workspace`, `exclusoes_limpeza`, `relatorios_lote`; acrescenta em `workspaces` as colunas `ia_externa_permitida` (bool, padrão falso) e `conexao_ia_id` (FK anulável para `conexoes`); acrescenta em `documentos_conversao` as colunas `limpeza_situacao`, `duvidas`, `exclusoes`, `limpeza_erro` e em `lotes_conversao` a coluna `dominio_versao_id`. Downgrade remove tudo na ordem inversa; sem perda de dados existentes (valores padrão).

#### Models

- `DominioWorkspace`: `id`, `workspace_id`, `versao`, `texto`, `vigente`, `aprovado_por`, `criado_em`; único (`workspace_id`, `versao`).
- `ExclusaoLimpeza`: `id`, `lote_id`, `documento_id`, `arquivo`, `posicao`, `motivo`, `camada` (`regra`, `ia`, `duplicidade`), `confianca` anulável, `trecho` anulável, `criado_em`.
- `RelatorioLote`: `id`, `lote_id` único, `conteudo`, `ia_usada`, `provedor`, `dominio_versao_id`, `contagens` (JSON), `criado_em`, `expira_em`.
- `Workspace`, `DocumentoConversao` e `LoteConversao` recebem as colunas da migration. Arquivo: `src/app/models.py`.
- `Conexao`: novo tipo `ia_analise` em `TIPOS` com configuração `modelo` e `url_base`, chave obrigatória; validação em `src/app/conexoes.py`.

#### Controllers e casos de uso

- `src/app/routers/workspaces.py`: `GET /api/v1/workspaces/{id}/dominio` (vigente, qualquer papel), `GET .../dominio/versoes` (owner/admin), `PUT .../dominio` (owner/admin; nova versão), `PATCH .../analise-ia` (owner/admin; `ia_externa_permitida`, `conexao_ia_id`).
- `src/app/routers/conversao.py`: `GET /conversoes/{lote}/dominio-proposto`, `POST /conversoes/{lote}/dominio/confirmar` (owner/admin; texto opcional corrigido), `POST /conversoes/{lote}/documentos/{id}/limpar` (retomada), `GET /conversoes/{lote}/relatorio` (Markdown) e inclusão do relatório no pacote de `.md`; `GET /conversoes/{lote}/exclusoes` (owner/admin, com texto removido).
- Os modelos de resposta de documento e lote ganham situação de limpeza, contagens, motivo da falha e avisos de IA/domínio.

#### Views e experiência

- Detalhado na seção 10. Estados loading/vazio/erro/sucesso seguem os padrões de `PainelLoteConversao`.

#### Queries e repositórios

- `src/app/repo.py`: versão vigente do domínio por Workspace, histórico, exclusões por lote com filtro de papel, contagens por documento, relatório por lote e expiração; índices em `exclusoes_limpeza(lote_id)` e `dominios_workspace(workspace_id, vigente)`.

#### Jobs e processamento assíncrono

- `limpar_documento_task(documento_id)`: idempotente (só age em "Aguardando limpeza" ou "Falhou" reenfileirado), retry limitado, falha vira "Falhou" com motivo seguro.
- `finalizar_limpeza_lote_task(lote_id)`: após o último documento limpo, executa a duplicidade do lote e monta o relatório uma única vez (bloqueio por linha do lote).
- `purgar_limpeza_task` (cron diário): zera `trecho` de exclusões com mais de 30 dias e apaga relatórios com mais de 90 dias.

#### Estrutura de arquivos

```text
specs/draft/0037-fase-1-conteudo-de-dominio-e-limpeza/
  spec.md
  research/
src/pipeline/limpeza/{__init__,contratos,regras,avaliacao_ia,duplicidade,dominio,relatorio}.py
src/app/limpeza.py
alembic/versions/0037_limpeza_dominio.py
tests/test_limpeza_regras.py
tests/test_limpeza_ia.py
tests/test_limpeza_duplicidade.py
tests/test_limpeza_dominio.py
tests/test_limpeza_retencao.py
tests/test_router_limpeza.py
frontend/src/features/workspaces/SecaoDominioEmpresa.tsx
frontend/src/features/conversao/ConfirmarDominio.tsx
frontend/src/features/conversao/AvisosLimpeza.tsx
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| DominioWorkspace | `id`; único (`workspace_id`, `versao`) | `texto` 1–4000 caracteres, `vigente`, `aprovado_por`, `criado_em`; uma única versão vigente por Workspace | N:1 Workspace, N:1 Pessoa |
| Workspace (extensão) | `id` | `ia_externa_permitida` (padrão falso), `conexao_ia_id` só de tipo `ia_analise` e ativa | N:1 Conexao opcional |
| ExclusaoLimpeza | `id` | `motivo`, `camada`, `confianca`, `posicao`, `trecho` (anulável após 30 dias) | N:1 LoteConversao, N:1 DocumentoConversao |
| RelatorioLote | `id`; `lote_id` único | `conteudo` Markdown sem texto removido, `ia_usada`, `provedor`, contagens, `expira_em` (90 dias) | 1:1 LoteConversao, N:1 DominioWorkspace |
| DocumentoConversao (extensão) | `id` | `limpeza_situacao`, `duvidas`, `exclusoes`, `limpeza_erro` | N:1 LoteConversao |
| Conexao (tipo novo) | `id` | tipo `ia_analise`, `modelo`, `url_base`, chave cifrada | reutiliza o cadastro existente |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| LoteConversao | concluído (conversão) | domínio ausente | aguardando_dominio | limpeza não começa |
| LoteConversao | aguardando_dominio | domínio confirmado | limpando | versão vigente existe |
| DocumentoConversao | aguardando_limpeza | tarefa inicia | limpando | uma tarefa por documento |
| DocumentoConversao | limpando | sem dúvidas | limpo | log completo |
| DocumentoConversao | limpando | com dúvidas | limpo_com_duvidas | dúvidas mantidas e marcadas |
| DocumentoConversao | limpando | erro | falhou_limpeza | conteúdo anterior preservado |
| DocumentoConversao | falhou_limpeza | "Tentar de novo" | aguardando_limpeza | só o que falhou |

#### Migração e retenção

- Migration aditiva `0037_limpeza_dominio` com downgrade; sem backfill (Workspaces existentes: IA desligada, sem domínio).
- Retenção: texto removido 30 dias, relatório 90 dias, versões do domínio enquanto o Workspace existir; o log (motivo, arquivo e posição) e o registro do lote permanecem como histórico; apagar uma coleção não os afeta, e a remoção do Workspace os retira.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. Três pontos: confirmação do domínio no lote, seção "Domínio da empresa" no Workspace e resultado da limpeza no painel do lote.

#### Stack e convenções de interface

- Next.js (App Router) + React + TypeScript + Tailwind, primitives shadcn/ui (Base UI) e composições próprias; testes com Vitest e Testing Library. Telas atuais afetadas: `/workspaces/[id]`, painel do lote (`ConversaoSheet`, `PainelLoteConversao`, `DataGridLotesConversao`) e `ConexaoFormSheet`. Fontes: `INTERFACE.md`, `DESIGNSYSTEM.MD`, `frontend/src/features/`.
- Preservado: `ConversaoSheet`, `DataGridLotesConversao`, `situacao.ts` e o fluxo de conversão; `ConexaoFormSheet` recebe o tipo novo.

#### Telas e responsabilidades

- **Painel do lote**: acompanhar a limpeza, ver contagens por documento, avisos de IA/domínio, "Confirmar domínio", "Tentar de novo" e "Baixar relatório do lote".
- **Passo de confirmação do domínio (no lote)**: owner/admin lê a proposta, edita e confirma.
- **Seção "Domínio da empresa" em `/workspaces/[id]`**: consultar e editar o resumo vigente, ver histórico (owner/admin), escolher a conexão de IA, ligar a chave, cadastrar conexão.

#### Fluxo de informação e navegação

- A pessoa envia o lote → vê a conversão → se falta domínio, o painel destaca "Confirmar domínio" → confirma → acompanha a limpeza → baixa o relatório. Os avisos linkam para a seção do Workspace e a trilha (Breadcrumb Equipe → Workspaces → Workspace) volta ao lote.

#### Menus e navegação principal

- Sem item novo de menu. A seção do domínio fica na página do Workspace já acessível por `Workspaces`; a conexão de IA é cadastrada em `Conexões` ou pelo atalho "Cadastrar conexão".

#### Formulários e ações

- Domínio: área de texto 1–4000 caracteres com contador, "Salvar" cria nova versão; erro de tamanho junto do campo com foco.
- IA: seletor de conexões ativas do tipo `ia_analise`, interruptor "Permitir análise por IA externa" e "Cadastrar conexão" (abre `ConexaoFormSheet`); apenas owner/admin.
- Confirmação do domínio: editar a proposta e "Confirmar domínio" no passo do lote (painel lateral existente).
- Ações do lote: "Tentar de novo" (por documento que falhou), "Baixar relatório do lote".

#### Composição e disposição

- Seção do Workspace: bloco com título, resumo, histórico recolhível e bloco de IA; no desktop em duas colunas, no mobile em coluna única com ações empilhadas.
- Painel do lote: aviso no topo (`Alert`), lista de documentos com `Badge` de situação e contagens, rodapé com "Baixar relatório do lote".

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Workspace | `SecaoDominioEmpresa` | Resumo vigente, edição, histórico, conexão e chave de IA | `frontend/src/features/workspaces/SecaoDominioEmpresa.tsx` | `Textarea`, `Select`, `Switch`, `Button`, `Alert` | shadcn/ui + próprio | Novo; extrai `FormularioDominio` reutilizado no lote |
| Workspace e lote | `FormularioDominio` | Campo do resumo com contador e salvar, compartilhado pela seção do Workspace e pelo passo do lote | `frontend/src/features/workspaces/FormularioDominio.tsx` | `Textarea`, `Button`, `Alert` | shadcn/ui + próprio | Novo; reusado por `SecaoDominioEmpresa` e `ConfirmarDominio` |
| Lote | `ConfirmarDominio` | Proposta, edição e confirmação no painel do lote | `frontend/src/features/conversao/ConfirmarDominio.tsx` | `Sheet`, `Textarea`, `Button` | shadcn/ui + próprio | Novo; reusa `FormularioDominio` |
| Lote | `AvisosLimpeza` | Avisos de IA fora, chave desligada e domínio não confirmado | `frontend/src/features/conversao/AvisosLimpeza.tsx` | `Alert` | shadcn/ui + próprio | Novo; segue `AvisoConversao` |
| Lote | `PainelLoteConversao` | Situação de limpeza, contagens, retomada e download | `frontend/src/features/conversao/PainelLoteConversao.tsx` | `Badge`, `Button` | próprio | Estende o existente |
| Lote | `situacao.ts` | Rótulos e variantes das novas situações | `frontend/src/features/conversao/situacao.ts` | `Badge` | próprio | Estende o existente |
| Conexões | `ConexaoFormSheet` | Tipo "IA para análise de documentos" | `frontend/src/features/conexoes/ConexaoFormSheet.tsx` | `Sheet`, `Select`, `Input` | próprio | Estende o existente |

- Registrar cada bloco criado ou reaproveitado em `INTERFACE.md` com consumidores e origem; telas apenas compõem esses blocos.

#### Estados e acessibilidade

- Carregando com `aria-busy` e `Skeleton`; vazio com instrução de como definir o domínio; erro em `Alert` com "Tentar novamente"; sucesso anunciado em `role=status`; permissão insuficiente esconde ações de escrita e mantém a leitura.
- Teclado: todos os controles alcançáveis, foco visível, nomes acessíveis; avisos com `role=status`. O `Breadcrumb` mantém a equipe visível e marca a página atual.

#### Contrato CRUD

- Não há CRUD de entidade nova com listagem própria: o domínio é um documento versionado por Workspace (consultar e editar, sem apagar versões) e a limpeza é uma ação sobre o lote. A superfície de lotes continua usando o `PageHeader` único e o `DataGrid` existente (`DataGridLotesConversao`) em largura total, com a coluna `ID` visível, a linha inteira como link para o detalhe e as ações independentes de editar e apagar já existentes (apagar respeita a permissão e confirma a consequência). Nada disso é replicado nas telas novas, que só compõem esses blocos. Componentes novos entram em `INTERFACE.md`.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre em cada tarefa de interface, mesmo sem pedido, em desktop e 375 px, nos estados carregando, vazio, aviso, erro, falha parcial e sucesso, conferindo bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD`. Tarefas de backend registram `Não aplicável` com motivo.

#### APIs expostas

- Rotas listadas em "Controllers e casos de uso", todas sob `/api/v1`, com a autenticação por sessão existente, `require_write_role` nas escritas, erros 403 (permissão), 404 (não encontrado), 409 (limpeza sem domínio confirmado) e 422 (tamanho do resumo).

#### APIs externas utilizadas

- IA de análise via `ChatModelAdapter` (provedor definido pela conexão do Workspace; hoje OpenRouter). Timeout e retry limitados, falha vira modo "só regras fixas"; nenhuma chamada com a chave desligada.

#### Documentação das APIs consultadas

- Nenhuma documentação externa; contrato local `ChatModelAdapter`.

#### Eventos e outros contratos

- Saída da limpeza: Markdown limpo no mesmo armazenamento do documento, respeitando o contrato da SPEC-0002; relatório em Markdown com seções fixas (exclusões, dúvidas, duplicidades prováveis, IA e versão do domínio).

### 11. Estratégia TDD

- **Unidade**: regras fixas, normalização e semelhança, montagem do relatório, parsing da saída da IA, componentes React isolados.
- **Integração/contrato**: rotas de domínio, análise de IA e relatório com banco isolado; tarefas do worker com provider de IA falso; retenção com datas simuladas; migration `0037` com downgrade.
- **BDD/aceite**: o Gherkin da seção 6 informa o desenho de cada caso; nenhum `.feature` é criado.
- **Runner TDD**: projeto Python/Node misto sem PHP; usar o runner existente do repositório: Pytest para o backend e Vitest para o frontend.
- **E2E**: jornada lote → domínio → limpeza → relatório pelo cliente de teste da API, com provider de IA falso; sem chamada externa real.
- **Verificação manual**: qualidade real da IA e o gabarito de 3 ou 4 documentos do cliente (opt-in, fora do repositório), pois dependem de provider pago e de dados que não podem ser versionados.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, NFR-002, AC-001 | AC-001 na seção 6 | tests/test_limpeza_regras.py: ruído removido e log (`SPECSFY: SPEC-0037 AC-001`) | Pending | Pending | Pending |
| US-001, FR-001, NFR-002, AC-002 | AC-002 na seção 6 | tests/test_limpeza_regras.py: número em frase permanece (`SPECSFY: SPEC-0037 AC-002`) | Pending | Pending | Pending |
| US-001, FR-001, FR-002, AC-003 | AC-003 na seção 6 | tests/test_limpeza_regras.py: documento limpo idêntico (`SPECSFY: SPEC-0037 AC-003`) | Pending | Pending | Pending |
| US-001, FR-002, FR-009, NFR-001, AC-004 | AC-004 na seção 6 | tests/test_limpeza_retencao.py: 30 dias e papel member (`SPECSFY: SPEC-0037 AC-004`) | Pending | Pending | Pending |
| US-002, FR-003, FR-004, FR-009, AC-005 | AC-005 na seção 6 | tests/test_limpeza_dominio.py: proposta e confirmação (`SPECSFY: SPEC-0037 AC-005`) | Pending | Pending | Pending |
| US-002, FR-003, FR-007, FR-009, AC-006 | AC-006 na seção 6 | tests/test_limpeza_dominio.py: versões e relatório (`SPECSFY: SPEC-0037 AC-006`) | Pending | Pending | Pending |
| US-002, FR-003, FR-008, AC-007 | AC-007 na seção 6 | tests/test_limpeza_dominio.py: bloqueio sem confirmação (`SPECSFY: SPEC-0037 AC-007`) | Pending | Pending | Pending |
| US-003, FR-004, FR-005, NFR-001, AC-008 | AC-008 na seção 6 | tests/test_limpeza_ia.py: chave desligada sem chamada (`SPECSFY: SPEC-0037 AC-008`) | Pending | Pending | Pending |
| US-003, FR-002, FR-005, NFR-002, AC-009 | AC-009 na seção 6 | tests/test_limpeza_ia.py: limiar de confiança (`SPECSFY: SPEC-0037 AC-009`) | Pending | Pending | Pending |
| US-003, FR-005, FR-008, NFR-003, AC-010 | AC-010 na seção 6 | tests/test_limpeza_ia.py: IA indisponível (`SPECSFY: SPEC-0037 AC-010`) | Pending | Pending | Pending |
| US-004, FR-006, FR-007, AC-011 | AC-011 na seção 6 | tests/test_limpeza_duplicidade.py: parágrafo igual (`SPECSFY: SPEC-0037 AC-011`) | Pending | Pending | Pending |
| US-004, FR-006, NFR-002, AC-012 | AC-012 na seção 6 | tests/test_limpeza_duplicidade.py: 96%, 94% e trecho curto (`SPECSFY: SPEC-0037 AC-012`) | Pending | Pending | Pending |
| US-005, FR-008, NFR-003, AC-013 | AC-013 na seção 6 | tests/test_router_limpeza.py: 50 documentos e retomada (`SPECSFY: SPEC-0037 AC-013`) | Pending | Pending | Pending |
| US-005, FR-007, FR-009, NFR-004, AC-014 | AC-014 na seção 6 | frontend/src/features/conversao/PainelLimpeza.test.tsx: contagens e download (`SPECSFY: SPEC-0037 AC-014`) | Pending | Pending | Pending |
| US-005, FR-008, NFR-004, AC-015 | AC-015 na seção 6 | frontend/src/features/conversao/AvisosLimpeza.test.tsx: aviso e link (`SPECSFY: SPEC-0037 AC-015`) | Pending | Pending | Pending |
| US-002, US-005, NFR-004, AC-016 | AC-016 na seção 6 | frontend/src/features/workspaces/SecaoDominioEmpresa.test.tsx: coluna única em 375 px (`SPECSFY: SPEC-0037 AC-016`) | Pending | Pending | Pending |
| US-005, FR-007, NFR-001, AC-017 | AC-017 na seção 6 | tests/test_limpeza_retencao.py: relatório de 90 dias (`SPECSFY: SPEC-0037 AC-017`) | Pending | Pending | Pending |
| US-003, FR-004, FR-009, NFR-001, AC-018 | AC-018 na seção 6 | tests/test_router_limpeza.py: conexão de IA e sigilo da chave (`SPECSFY: SPEC-0037 AC-018`) | Pending | Pending | Pending |
| US-004, FR-006, FR-007, AC-019 | AC-019 na seção 6 | tests/test_limpeza_duplicidade.py: semelhante vai ao relatório (`SPECSFY: SPEC-0037 AC-019`) | Pending | Pending | Pending |
| US-003, FR-005, NFR-003, AC-020 | AC-020 na seção 6 | tests/test_limpeza_ia.py: só seções restantes (`SPECSFY: SPEC-0037 AC-020`) | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | tests/test_limpeza_regras.py | Pending |
| FR-001 | AC-002 | Unidade | tests/test_limpeza_regras.py | Pending |
| FR-001 | AC-003 | Unidade | tests/test_limpeza_regras.py | Pending |
| FR-002 | AC-001 | Integração | tests/test_limpeza_regras.py | Pending |
| FR-002 | AC-004 | Integração | tests/test_limpeza_retencao.py | Pending |
| FR-002 | AC-009 | Integração | tests/test_limpeza_ia.py | Pending |
| FR-003 | AC-005 | Integração | tests/test_limpeza_dominio.py | Pending |
| FR-003 | AC-006 | Integração | tests/test_limpeza_dominio.py | Pending |
| FR-003 | AC-007 | Integração | tests/test_limpeza_dominio.py | Pending |
| FR-004 | AC-005 | Integração | tests/test_limpeza_dominio.py | Pending |
| FR-004 | AC-008 | Integração | tests/test_limpeza_ia.py | Pending |
| FR-004 | AC-018 | Contrato | tests/test_router_limpeza.py | Pending |
| FR-005 | AC-008 | Integração | tests/test_limpeza_ia.py | Pending |
| FR-005 | AC-009 | Unidade | tests/test_limpeza_ia.py | Pending |
| FR-005 | AC-010 | Integração | tests/test_limpeza_ia.py | Pending |
| FR-006 | AC-011 | Unidade | tests/test_limpeza_duplicidade.py | Pending |
| FR-006 | AC-012 | Unidade | tests/test_limpeza_duplicidade.py | Pending |
| FR-006 | AC-019 | Unidade | tests/test_limpeza_duplicidade.py | Pending |
| FR-007 | AC-006 | Integração | tests/test_limpeza_dominio.py | Pending |
| FR-007 | AC-011 | Integração | tests/test_limpeza_duplicidade.py | Pending |
| FR-007 | AC-014 | Componente | frontend/src/features/conversao/PainelLimpeza.test.tsx | Pending |
| FR-008 | AC-007 | Integração | tests/test_limpeza_dominio.py | Pending |
| FR-008 | AC-010 | Integração | tests/test_limpeza_ia.py | Pending |
| FR-008 | AC-013 | Integração | tests/test_router_limpeza.py | Pending |
| FR-009 | AC-004 | Contrato | tests/test_limpeza_retencao.py | Pending |
| FR-009 | AC-005 | Contrato | tests/test_limpeza_dominio.py | Pending |
| FR-009 | AC-014 | Contrato | tests/test_router_limpeza.py | Pending |
| NFR-001 | AC-004 | Integração | tests/test_limpeza_retencao.py | Pending |
| NFR-001 | AC-008 | Integração | tests/test_limpeza_ia.py | Pending |
| NFR-001 | AC-018 | Contrato | tests/test_router_limpeza.py | Pending |
| NFR-002 | AC-001 | Unidade | tests/test_limpeza_regras.py | Pending |
| NFR-002 | AC-002 | Unidade | tests/test_limpeza_regras.py | Pending |
| NFR-002 | AC-012 | Unidade | tests/test_limpeza_duplicidade.py | Pending |
| NFR-003 | AC-010 | Integração | tests/test_limpeza_ia.py | Pending |
| NFR-003 | AC-013 | Integração | tests/test_router_limpeza.py | Pending |
| NFR-003 | AC-020 | Unidade | tests/test_limpeza_ia.py | Pending |
| NFR-004 | AC-014 | Componente | frontend/src/features/conversao/PainelLimpeza.test.tsx | Pending |
| NFR-004 | AC-015 | Componente | frontend/src/features/conversao/AvisosLimpeza.test.tsx | Pending |
| NFR-004 | AC-016 | Componente | frontend/src/features/workspaces/SecaoDominioEmpresa.test.tsx | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0037-fase-1-conteudo-de-dominio-e-limpeza/spec.md`
- **Resultado**: READY em 2026-10-16, depois de NOT READY no mesmo dia (revisão semântica de `$specsfy-04-validate`; estrutura `VALID DRAFT`, 20 AC, cobertura mínima de 3 AC por US/FR/NFR atendida: 5 US, 9 FR, 4 NFR).
- **Achados**:
  - **BLOCKER FR-002 / seção 9 / Erros**: o log e o relatório "saem com a coleção", mas o lote de conversão não pertence a uma coleção (`LoteConversao` liga só a Workspace). Não há evento de "apagar a coleção" que apague esses registros, e nenhum AC testaria isso. Falta decidir o ciclo de vida do log e do relatório.
  - **WARNING métricas**: "a maior parte do ruído marcado é removida" não tem alvo numérico. Mitigado por DEC-008 (fixado com o gabarito); proposta provisória de 80%.
  - **WARNING NFR-003**: o alvo de desempenho é qualitativo (segundo plano com progresso); o AC-013 verifica 50 documentos, sem tempo máximo. Aceito para a primeira versão.
  - **Resolvido nesta revisão (não alteram requisito)**: Definition of Done passou a citar `.specsfy/DATABASE.md`, `PROJECT.md` e `INTERFACE.md`; `FormularioDominio` ganhou linha na tabela de blocos; risco de injeção de instruções no texto do documento foi registrado com mitigação.
  - **BLOCKER resolvido pela DEC-009**: log e relatório pertencem ao lote; FR-002, a seção 9 e Erros foram corrigidos e `.specsfy/DATABASE.md` foi alinhado.
  - **Warnings aceitos**: meta numérica de ruído removido fixada com o gabarito (DEC-008); NFR-003 qualitativo na primeira versão.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/draft/0037-fase-1-conteudo-de-dominio-e-limpeza/spec.md`
- **Achados**: Pending.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0037-fase-1-conteudo-de-dominio-e-limpeza/spec.md .`
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

As tarefas serão derivadas pela etapa `$specsfy-05-tasks` depois do Definition Gate; esta spec está em Draft e ainda não possui tarefas.

### 15. Ordem de execução

- Caminho crítico previsto: testes RED (seção 11) → módulos de regras e duplicidade → persistência e migration → avaliação por IA e domínio → rotas e worker → interface → regressão.
- Tarefas paralelas: a definir em `$specsfy-05-tasks`.
- Estratégia de MVP: US-001 e US-002 primeiro (regras fixas e domínio), depois US-003, US-004 e US-005.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0023 e SPEC-0036 (conversão e formatos), SPEC-0002 (contrato Markdown), SPEC-0030 (Workspaces e coleções) e o cadastro de Conexões da SPEC-0026.
- BACKLOG-0042 consome a saída desta spec.
- Gabarito de 3 ou 4 documentos reais, fora do repositório, para o teste de aceite final.

#### Riscos

- A IA classifica negócio como ruído com alta confiança → remoção só acima do limiar, log completo por 30 dias, relatório e limiar configurável calibrado com o gabarito.
- Semelhança de 95% apaga diferença real → trechos abaixo de 200 caracteres só removem por igualdade normalizada, e o limite é configurável.
- Custo e latência da IA em lotes grandes → regras fixas antes, requisições limitadas e processamento em segundo plano.
- Texto do documento tenta manipular a IA (por exemplo, instrução embutida para remover tudo) → o conteúdo do documento é enviado como dado delimitado, a saída da IA é validada contra um esquema estruturado, a remoção exige confiança acima do limiar e toda remoção fica no log recuperável por 30 dias.
- Vazamento de texto de cliente → chave por Workspace, provider espião nos testes e ausência de texto nos logs.

#### Suposições

- A cópia mantida na duplicidade é a do primeiro documento na ordem do lote.
- O limiar de confiança padrão é 0,8, configurável, calibrado depois com o gabarito.
- A amostra para a proposta do domínio reúne os primeiros trechos de até 5 documentos do lote, limitada por tamanho.
- "Editor" e "quem administra" coincidem com owner e admin (papel de escrita), sem papel intermediário novo (DEC-007, confirmada em 2026-10-16).
- A ordem é conversão → domínio → regras fixas → IA → duplicidade → relatório; a análise de contradições vem depois, a pedido (DEC-006, confirmada em 2026-10-16).
- Documentos de lotes anteriores não entram na duplicidade; ela vale dentro do lote.

### 17. Decisões

- **DEC-001**: filtro em três camadas com dúvida mantida — alternativa descartada: só IA, por custo, privacidade e risco de perda silenciosa.
- **DEC-002**: resumo do domínio versionado por Workspace e confirmado antes da limpeza — evita critério implícito e permite auditar a versão usada.
- **DEC-003**: conexão de IA por Workspace como novo tipo de Conexão, com chave cifrada e interruptor de IA externa — reaproveita o cadastro existente e concentra a decisão de privacidade em quem administra.
- **DEC-004**: duplicidade removida sozinha apenas por igualdade normalizada ou semelhança de pelo menos 95% em trechos de 200 ou mais caracteres; o restante vai ao relatório — prefere manter ruído a perder informação.
- **DEC-005**: conferência fora do sistema na primeira versão, por relatório baixável sem o texto removido — evita tela nova de edição.
- **DEC-006** (confirmada pela pessoa responsável em 2026-10-16): a limpeza roda antes da análise de contradições; a análise (BACKLOG-0042) é a pedido, sobre os `.md` já limpos da coleção.
- **DEC-007** (confirmada pela pessoa responsável em 2026-10-16): sem papel intermediário; owner e admin concentram as ações de escrita e administração e member só consulta, pois o sistema só tem `owner`, `admin` e `member` — a Pergunta 5 de Interface distinguia "editor" de "quem administra", e a pessoa responsável pode pedir um papel novo em outra spec.
- **DEC-008** (confirmada pela pessoa responsável em 2026-10-16): o gabarito de documentos reais é verificação final opt-in na entrega, com o conjunto que a pessoa trouxer, e não condição da definição — a definição, o plano e o código não dependem dele; os limiares ficam configuráveis para calibração.
- **DEC-009** (confirmada pela pessoa responsável em 2026-10-16): o log de exclusões e o relatório do lote pertencem ao lote de conversão, não a uma coleção; o relatório dura 90 dias, o texto removido 30 dias e o restante permanece com o registro do lote — corrige a descoberta de dados de 2026-10-13, que assumia um vínculo com a coleção.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
- [ ] `.specsfy/DATABASE.md` reflete as tabelas e colunas novas (`dominios_workspace`, `exclusoes_limpeza`, `relatorios_lote` e as extensões de `workspaces`, `documentos_conversao` e `lotes_conversao`).
- [ ] `PROJECT.md` foi revisado quanto à nova capacidade de limpeza e domínio, ou a ausência de impacto foi justificada na evidência da tarefa.
- [ ] `INTERFACE.md` registra os blocos novos e reaproveitados (seção 10).
