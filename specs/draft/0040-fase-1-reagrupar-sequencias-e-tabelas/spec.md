# Especificação integrada: Fase 1: reagrupar sequências e montar tabelas

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0040 |
| Slug | 0040-fase-1-reagrupar-sequencias-e-tabelas |
| Status | Draft |
| Effort | 7 |
| Effort updated at | 2026-10-16 |
| Effort rationale | Heurística de agrupamento por metadados, tela de aprovação com reordenação acessível, novo estado do lote, geração de um `.md` por grupo e pós-processamento de tabelas entre páginas; sem IA e sem nova política de privacidade, mas com muitos casos-limite de conversão. |
| ClickUp Task | |
| Milestones | M04 |
| Definition Gate | Pending |
| Plan Gate | Pending |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-16 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

Os documentos que as empresas entregam incluem prints de conversas, passo a passo de aplicativo e slides fotografados: imagens soltas que perdem a ordem e o agrupamento, e várias conversas ou tutoriais chegam misturados. Tabelas também se perdem na extração, principalmente quando continuam na página seguinte ou têm células mescladas. A conversão atual (SPEC-0023 e SPEC-0036) gera um `.md` por arquivo e não organiza nada disso.

#### Resultado desejado

Imagens enviadas juntas são agrupadas em sequências propostas pelo sistema e aprovadas pela pessoa, e cada grupo vira um `.md` único, com uma seção por imagem na ordem aprovada. Imagem isolada vira documento próprio. Tabelas simples saem como tabelas Markdown, tabelas que continuam na página seguinte são juntadas quando as colunas batem, e as complexas viram texto corrido com o documento marcado "Revisar". Nada é separado, reordenado ou juntado sem segurança ou aprovação.

#### Métricas de sucesso

- 100% dos grupos e ordens passam pela aprovação da pessoa antes de gerar `.md` (alvo: 0 `.md` gerados antes da confirmação).
- Com certeza total na proposta, a aprovação exige 1 clique.
- Nenhuma tabela é juntada ou convertida de forma silenciosa em caso de dúvida: toda incerteza gera o selo "Revisar" com o motivo.
- A taxa de acerto da proposta de grupos (nome, data e hora e pasta) é medida com prints reais antes de qualquer evolução com OCR. **Pendente**: depende de um conjunto de prints reais, fora do repositório (o mesmo tipo de gabarito das SPEC-0037 a 0039).

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: leitura do código da conversão (`src/app/routers/conversao.py`, `src/app/tasks.py`, `src/pipeline/conversion/`) → o envio cria um `DocumentoConversao` por arquivo e enfileira a conversão; já existe o estado `aguardando_abas` (Excel com várias abas) e o componente `SelecaoAbas`, que são o precedente de passo de aprovação no painel do lote; a conversão de imagem usa OCR (`converters/image.py`).
- **R-002**: leitura do contrato do Markdown (`specs/completed/0002-*/spec.md`) → o corpo do `.md` é texto livre e o frontmatter é opcional; a linha "Origem: <arquivo>" no corpo é compatível e já é usada por URL (SPEC-0036). A dúvida do backlog sobre o formato do marcador fica resolvida.

#### Fontes e contexto consultados

- `specs/backlog/0040-fase-1-reagrupar-sequencias-e-tabelas.md` (Perguntas 1 a 8, interface e critérios).
- `specs/draft/0037-*/spec.md` (relatório do lote e papéis), `specs/completed/0036-*/spec.md` e `specs/completed/0023-*/spec.md` (conversão e formatos), `specs/milestones/M04.md`, `.specsfy/DATABASE.md`, `INTERFACE.md`, `DESIGNSYSTEM.MD`, `frontend/src/features/conversao/`.

#### Documentação consultada

- Nenhuma documentação externa.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Como conciliar a pasta isolada do briefing e a mistura de prints? → **A**: o sistema propõe os grupos e a ordem; a pessoa ajusta e aprova antes de gerar os `.md` (backlog, Pergunta 1).
- **Q**: Que pistas a primeira entrega usa? → **A**: só nome do arquivo, data e hora e pasta de origem; a leitura do conteúdo por OCR fica como evolução (Pergunta 2).
- **Q**: Quando aparece a aprovação? → **A**: em cada envio com várias imagens; com certeza total vem tudo pré-aprovado e basta um clique (Pergunta 7).
- **Q**: Como são as tabelas? → **A**: simples viram tabela Markdown; complexas (células mescladas, aninhadas, cabeçalho de vários níveis) viram texto corrido, uma frase por linha, e o documento recebe "Revisar" (Pergunta 3). Tabela que continua na página seguinte é juntada sem o cabeçalho repetido quando as colunas batem; em dúvida não junta e marca "Revisar" (Pergunta 4).
- **Q**: Como a origem aparece no `.md`? → **A**: uma seção por imagem, na ordem aprovada, com "Origem: <arquivo>" (Pergunta 5), compatível com a SPEC-0002 (R-002).
- **Q**: E imagem ilegível? → **A**: o grupo é gerado com "imagem não legível: <arquivo>" no lugar, o documento recebe "Revisar" e o relatório do lote lista o arquivo (Pergunta 6).
- **Q**: E PDF? → **A**: um PDF gera um `.md`; dividir PDF de páginas-imagem pela tela de aprovação fica como evolução (Pergunta 8).
- **Q**: Onde fica a aprovação? → **A**: como um passo do lote de conversão, depois do envio e antes de gerar os `.md`, com cartões de grupo, "Mover para outro grupo", "Reordenar" por teclado e "Confirmar grupos" (2026-10-16, Interface, Pergunta 1).
- **Q**: Como aparece "Revisar" e quem aprova? → **A**: selo "Revisar" com o motivo, no padrão de `SeloRevisarDocumento`, e relatório do lote listando os arquivos; owner e admin aprovam, member consulta (2026-10-16, Interface, Pergunta 2; DEC-007 da SPEC-0037).

#### Dúvidas abertas

- **Pendente**: conjunto de prints reais para medir a taxa de acerto da proposta de grupos e calibrar o intervalo de tempo entre imagens.
- Nenhuma outra bloqueante. O critério de limite entre sequências, o de "tabela complexa" e o de "colunas batem" entram como suposições reversíveis (seção 16).

### 3. Escopo e atores

#### Incluído

- Proposta de grupos e ordem para imagens enviadas juntas, usando só nome, data e hora e pasta de origem.
- Passo de aprovação no painel do lote, com ajuste (mover e reordenar) e confirmação.
- Geração de um `.md` por grupo aprovado, com uma seção por imagem e "Origem: <arquivo>"; imagem isolada como documento próprio; imagem ilegível sinalizada.
- Tabelas: simples em Markdown, complexas em texto corrido com "Revisar", continuação entre páginas juntada quando as colunas batem.
- Miniaturas das imagens na tela de aprovação.
- Estado do lote aguardando aprovação, retomável.

#### Fora de escopo

- Agrupar ou ordenar pelo conteúdo (OCR de nome de contato, horário ou numeração de slide): evolução, depois de medir os acertos.
- Dividir PDF de páginas-imagem pela tela de aprovação.
- Limpeza, domínio, contradições e decisão da empresa (SPEC-0037 a 0039).
- Reordenação totalmente automática (fora da V1 do briefing).
- Tabela em imagem reconhecida por OCR como estrutura de tabela.
- Qualquer envio de imagem a IA externa.

#### Atores

- **Owner e admin (papel de escrita)**: enviam o lote, ajustam e aprovam os grupos e a ordem.
- **Member**: consulta o lote e os `.md` gerados; não aprova nem reordena.
- **Sistema**: propõe grupos, converte e pós-processa tabelas.

### 4. Princípios e restrições do projeto

- **PR-001**: nenhuma imagem é separada, agrupada ou reordenada sem aprovação registrada.
- **PR-002**: em dúvida sobre tabela, não juntar nem simplificar em silêncio: marcar "Revisar" com o motivo.
- **PR-003**: o agrupamento usa somente metadados locais, sem IA externa e sem enviar imagens a terceiros.
- **PR-004**: o `.md` gerado respeita o contrato da SPEC-0002 (corpo livre, sem exigir frontmatter).
- **PR-005**: testes nunca usam o banco de desenvolvimento; usam a instância isolada de testes.
- **PR-006**: a interface reutiliza `ConversaoSheet`, `SeloRevisarDocumento`, `Alert`, `Badge`, `Button` e o padrão de `SelecaoAbas`; novos blocos entram em `INTERFACE.md`.

### 5. Histórias de usuário

#### US-001 — Receber uma proposta de grupos e ordem (P1)

Como owner ou admin, quero que o sistema proponha os grupos e a ordem das imagens enviadas juntas, para não separar à mão prints de conversas misturadas.

**Por que P1**: sem a proposta a pessoa teria de organizar tudo manualmente.
**Teste independente**: enviar imagens de três conversas misturadas e ver três grupos propostos na ordem sugerida.
**Requisitos**: FR-001, FR-002

#### US-002 — Aprovar ou ajustar os grupos antes de gerar os `.md` (P1)

Como owner ou admin, quero conferir, mover e reordenar as imagens e confirmar os grupos, para que nada seja gerado sem a minha aprovação.

**Por que P1**: é o checkpoint humano que evita reordenação silenciosa.
**Teste independente**: ajustar um grupo, confirmar e ver que só então o `.md` é gerado.
**Requisitos**: FR-002, FR-003, FR-007, FR-008

#### US-003 — Tratar imagem isolada e imagem ilegível (P2)

Como pessoa da consultoria, quero que imagem isolada vire documento próprio e que imagem ilegível seja sinalizada, para não perder nem esconder problemas.

**Por que P2**: cobre os casos de borda do envio misto.
**Teste independente**: enviar uma imagem sem par e outra ilegível e ver o documento próprio e o aviso.
**Requisitos**: FR-003, FR-004, FR-008

#### US-004 — Receber tabelas como tabelas (P1)

Como pessoa da consultoria, quero tabelas simples como tabelas Markdown e as complexas como texto corrido marcado "Revisar", para não perder a estrutura nem aceitar uma tabela errada.

**Por que P1**: tabelas são comuns nos documentos de empresa e se perdem hoje.
**Teste independente**: converter um PDF e um DOCX com uma tabela simples e uma com células mescladas.
**Requisitos**: FR-005

#### US-005 — Juntar tabela que continua na página seguinte (P2)

Como pessoa da consultoria, quero que a tabela dividida entre páginas volte a ser uma só quando as colunas batem, para a base não ter uma tabela cortada.

**Por que P2**: melhora a qualidade, mas é menos frequente que a tabela simples.
**Teste independente**: converter um PDF com uma tabela que atravessa duas páginas.
**Requisitos**: FR-006

### 6. Cenários BDD de aceite

#### AC-001 — Três conversas misturadas

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-001
Feature: Proposta de grupos

  Scenario: imagens de três conversas misturadas viram três grupos propostos
    Given 12 imagens de três conversas, com pastas, prefixos de nome e horários diferentes, enviadas misturadas
    When o envio é processado
    Then o sistema propõe três grupos, cada um com suas imagens na ordem sugerida
    And a proposta usa somente nome, data e hora e pasta de origem
```

#### AC-002 — Prefixo, numeração e salto de tempo

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-002
Feature: Proposta de grupos

  Scenario: numeração contínua agrupa e salto de tempo separa
    Given imagens "print-01", "print-02", "print-03" tiradas em minutos seguidos e "print-04" tirada horas depois
    When o sistema propõe os grupos
    Then as três primeiras ficam no mesmo grupo na ordem da numeração
    And a quarta fica em outro grupo porque o intervalo passa do limite configurado
```

#### AC-003 — Sem pistas, sem certeza

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-003
Feature: Proposta de grupos

  Scenario: pistas ambíguas geram proposta incerta
    Given imagens com nomes genéricos, mesma pasta e horários sobrepostos
    When o sistema propõe os grupos
    Then a proposta é marcada como incerta
    And nenhum grupo vem pré-aprovado
```

#### AC-004 — Certeza total, um clique

**Cobre**: US-002, FR-002

```gherkin
@US-002 @FR-002 @AC-004
Feature: Aprovação dos grupos

  Scenario: proposta com certeza total vem pré-aprovada
    Given uma proposta em que nome, data e hora e pasta concordam para todos os grupos
    When owner ou admin abre a tela de aprovação
    Then todos os grupos vêm marcados
    And um clique em "Confirmar grupos" basta para gerar os documentos
```

#### AC-005 — Nada é gerado antes de confirmar

**Cobre**: US-002, FR-002, FR-008, NFR-001

```gherkin
@US-002 @FR-002 @FR-008 @NFR-001 @AC-005
Feature: Aprovação dos grupos

  Scenario: aprovação abandonada mantém o lote aguardando
    Given um envio com várias imagens e a tela de aprovação aberta
    When a pessoa fecha a tela sem confirmar
    Then o lote permanece "Aguardando grupos" e nenhum .md é gerado
    And ao reabrir os grupos propostos estão preservados
```

#### AC-006 — Mover e reordenar por teclado

**Cobre**: US-002, FR-002, NFR-004

```gherkin
@US-002 @FR-002 @NFR-004 @AC-006
Feature: Aprovação dos grupos

  Scenario: ajuste de grupo e de ordem sem mouse
    Given um grupo com três imagens e outro grupo
    When a pessoa move uma imagem para o outro grupo e reordena pelo teclado
    Then a mudança é anunciada em role=status
    And o foco permanece no cartão movido
```

#### AC-007 — Um `.md` por grupo, na ordem aprovada

**Cobre**: US-002, FR-003, NFR-001

```gherkin
@US-002 @FR-003 @NFR-001 @AC-007
Feature: Geração do Markdown do grupo

  Scenario: seção por imagem na ordem aprovada com a origem
    Given um grupo aprovado com as imagens B, A e C nessa ordem
    When os documentos são gerados
    Then existe um único .md do grupo com três seções na ordem B, A, C
    And cada seção traz "Origem: <arquivo>" com o nome da imagem
```

#### AC-008 — Imagem isolada vira documento próprio

**Cobre**: US-003, FR-003

```gherkin
@US-003 @FR-003 @AC-008
Feature: Imagem isolada

  Scenario: imagem sem par é um documento
    Given uma imagem que não pertence a nenhuma sequência
    When os grupos são confirmados
    Then a imagem gera seu próprio .md com "Origem: <arquivo>"
```

#### AC-009 — Imagem ilegível

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-009
Feature: Imagem ilegível

  Scenario: lugar da imagem sinalizado e documento marcado
    Given um grupo em que uma das imagens não tem texto reconhecível
    When o .md do grupo é gerado
    Then a seção dessa imagem traz "imagem não legível: <arquivo>"
    And o documento recebe o selo "Revisar" com o motivo
```

#### AC-010 — Falha em um grupo não derruba os demais

**Cobre**: US-003, FR-004, FR-008

```gherkin
@US-003 @FR-004 @FR-008 @AC-010
Feature: Resiliência

  Scenario: um grupo falha e os outros seguem
    Given três grupos aprovados em que a geração do segundo falha
    When os documentos são gerados
    Then o segundo fica "Falhou" com o motivo
    And os outros dois ficam concluídos
```

#### AC-011 — Relatório do lote lista os "Revisar"

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-011
Feature: Relatório do lote

  Scenario: documentos para revisar aparecem no relatório
    Given um lote com um documento de imagem ilegível e outro com tabela complexa
    When o relatório do lote é montado
    Then ambos aparecem listados com o motivo
```

#### AC-012 — Tabela simples

**Cobre**: US-004, FR-005

```gherkin
@US-004 @FR-005 @AC-012
Feature: Tabelas

  Scenario: tabela simples vira tabela Markdown
    Given um PDF e um DOCX com uma tabela de 3 colunas e cabeçalho simples
    When os documentos são convertidos
    Then cada um traz a tabela como tabela Markdown com o mesmo conteúdo
```

#### AC-013 — Tabela complexa

**Cobre**: US-004, FR-005

```gherkin
@US-004 @FR-005 @AC-013
Feature: Tabelas

  Scenario: tabela com cabeçalho de vários níveis vira texto corrido
    Given um PDF com uma tabela de cabeçalho em dois níveis
    When o documento é convertido
    Then a tabela aparece como texto corrido, uma frase por linha
    And o documento recebe "Revisar" com o motivo "tabela complexa virou texto"
```

#### AC-014 — Células mescladas em DOCX

**Cobre**: US-004, FR-005

```gherkin
@US-004 @FR-005 @AC-014
Feature: Tabelas

  Scenario: células mescladas contam como tabela complexa
    Given um DOCX com uma tabela de células mescladas
    When o documento é convertido
    Then a tabela é tratada como complexa e o documento recebe "Revisar"
```

#### AC-015 — Tabela contínua juntada

**Cobre**: US-005, FR-006

```gherkin
@US-005 @FR-006 @AC-015
Feature: Continuação de tabela

  Scenario: tabela que atravessa duas páginas com as mesmas colunas
    Given um PDF com uma tabela de 4 colunas que termina no fim da página 1 e continua no início da página 2
    When o documento é convertido
    Then o resultado traz uma única tabela com todas as linhas
```

#### AC-016 — Colunas não batem, não junta

**Cobre**: US-005, FR-006

```gherkin
@US-005 @FR-006 @AC-016
Feature: Continuação de tabela

  Scenario: tabelas consecutivas com colunas diferentes
    Given um PDF com uma tabela de 4 colunas no fim da página 1 e outra de 3 colunas no início da página 2
    When o documento é convertido
    Then as duas tabelas permanecem separadas
    And o documento recebe "Revisar" com o motivo "tabela não juntada"
```

#### AC-017 — Cabeçalho repetido removido

**Cobre**: US-005, FR-006

```gherkin
@US-005 @FR-006 @AC-017
Feature: Continuação de tabela

  Scenario: cabeçalho repetido na página seguinte não duplica
    Given uma tabela contínua cuja página 2 repete o cabeçalho
    When o documento é convertido
    Then a tabela junta tem o cabeçalho uma única vez
```

#### AC-018 — Member consulta e não aprova

**Cobre**: US-002, FR-007

```gherkin
@US-002 @FR-007 @AC-018
Feature: Permissões

  Scenario: member não aprova nem reordena
    Given uma pessoa com papel member e um lote aguardando grupos
    When ela tenta confirmar ou reordenar os grupos
    Then a ação é recusada por permissão insuficiente
    And ela consegue ver os grupos propostos
```

#### AC-019 — Recusa na API

**Cobre**: US-002, FR-007

```gherkin
@US-002 @FR-007 @AC-019
Feature: Permissões

  Scenario: confirmação sem papel de escrita
    Given uma chamada de confirmar grupos feita por member
    When a API a recebe
    Then responde permissão insuficiente e nenhum documento é gerado
```

#### AC-020 — Retenção de 7 dias

**Cobre**: FR-008, NFR-001

```gherkin
@FR-008 @NFR-001 @AC-020
Feature: Retenção

  Scenario: imagens e grupos expiram como os demais documentos
    Given um lote aguardando grupos há 8 dias e outro há 2 dias
    When a rotina de retenção roda
    Then as imagens e propostas do lote antigo são apagadas e as do recente permanecem
```

#### AC-021 — Celular

**Cobre**: US-002, NFR-004

```gherkin
@US-002 @NFR-004 @AC-021
Feature: Responsividade

  Scenario: tela de aprovação em 375 pixels
    Given um viewport de 375 pixels e nomes de arquivo muito longos
    When a pessoa abre a tela de aprovação
    Then os cartões empilham, as miniaturas se ajustam e o texto quebra sem rolagem horizontal
    And "Confirmar grupos" fica acessível sem rolagem do conteúdo
```

#### AC-022 — Proposta rápida sem OCR

**Cobre**: FR-001, NFR-003

```gherkin
@FR-001 @NFR-003 @AC-022
Feature: Desempenho

  Scenario: 50 imagens recebem a proposta sem rodar OCR
    Given um envio com 50 imagens
    When a proposta de grupos é calculada
    Then o cálculo usa somente metadados, sem OCR e sem leitura do conteúdo
    And termina dentro do limite de tempo configurado
```

#### AC-023 — Nada sai para fora

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-023
Feature: Privacidade

  Scenario: agrupamento sem chamadas externas
    Given um provider de IA espião e uma rede simulada sem saída
    When os grupos são propostos e confirmados
    Then nenhuma chamada a IA ou a serviço externo é feita
```

#### AC-024 — Ordem aprovada preservada

**Cobre**: FR-003, NFR-001

```gherkin
@FR-003 @NFR-001 @AC-024
Feature: Ordem aprovada

  Scenario: reenviar o documento para conversão mantém a ordem
    Given um grupo aprovado e já convertido
    When a pessoa pede para reenviar o documento para conversão
    Then o .md refeito mantém a ordem aprovada, sem reordenar
```

#### AC-025 — Member não vê os controles

**Cobre**: US-002, FR-007, NFR-004

```gherkin
@US-002 @FR-007 @NFR-004 @AC-025
Feature: Permissões

  Scenario: tela de aprovação em modo leitura para member
    Given uma pessoa com papel member
    When ela abre o lote aguardando grupos
    Then os botões "Confirmar grupos", "Mover" e "Reordenar" não aparecem
    And o aviso informa que a aprovação cabe a owner ou admin
```

#### AC-026 — Lote com 20 imagens em segundo plano

**Cobre**: US-002, FR-003, NFR-003

```gherkin
@US-002 @FR-003 @NFR-003 @AC-026
Feature: Desempenho

  Scenario: geração dos grupos em segundo plano com progresso
    Given 20 imagens em quatro grupos aprovados
    When os documentos são gerados
    Then a conversão roda em segundo plano
    And o painel mostra a situação de cada grupo e o progresso do lote
```

#### AC-027 — PDF longo com tabelas

**Cobre**: FR-006, NFR-003

```gherkin
@FR-006 @NFR-003 @AC-027
Feature: Desempenho

  Scenario: PDF de 100 páginas com tabelas respeita os limites existentes
    Given um PDF de 100 páginas com tabelas contínuas
    When o documento é convertido
    Then a junção de tabelas é feita dentro dos limites de tempo e de tamanho da conversão
    And não há leitura de páginas além das já extraídas
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve propor, para um envio com duas ou mais imagens, grupos e ordem usando somente nome do arquivo (prefixo e numeração), data e hora e pasta de origem, e marcar a proposta com "certeza total" quando as três pistas concordam em todos os grupos ou "incerta" nos demais casos.
- **FR-002**: O sistema deve exibir a proposta num passo de aprovação do lote de conversão, sem gerar nenhum `.md` antes de "Confirmar grupos"; com certeza total os grupos vêm pré-aprovados; a pessoa pode mover uma imagem para outro grupo e reordenar por mouse e teclado; a aprovação abandonada mantém o lote "Aguardando grupos" com a proposta preservada.
- **FR-003**: O sistema deve gerar um `.md` por grupo aprovado com uma seção por imagem na ordem aprovada, cada uma com "Origem: <arquivo>", e gerar um `.md` próprio para imagem isolada; a ordem aprovada é mantida em reenvios para conversão.
- **FR-004**: O sistema deve, quando uma imagem não tiver texto reconhecível, gerar o grupo com "imagem não legível: <arquivo>" no lugar da imagem, marcar o documento com "Revisar" e o motivo e listar o arquivo no relatório do lote.
- **FR-005**: O sistema deve converter tabela simples (colunas consistentes, cabeçalho de um nível, sem células mescladas) em tabela Markdown e converter tabela complexa (células mescladas, aninhadas ou cabeçalho de vários níveis) em texto corrido, uma frase por linha, marcando o documento com "Revisar" e o motivo.
- **FR-006**: O sistema deve juntar numa só tabela a tabela que termina no fim de uma página e continua no início da seguinte quando o número e a estrutura das colunas batem, removendo o cabeçalho repetido; em dúvida deve manter as tabelas separadas e marcar "Revisar" com o motivo "tabela não juntada".
- **FR-007**: O sistema deve restringir a owner e admin a confirmar, mover e reordenar grupos, mostrando ao member a proposta em modo leitura sem os controles.
- **FR-008**: O sistema deve processar a geração em segundo plano, isolar a falha de um grupo dos demais, e aplicar aos arquivos e propostas do lote a mesma expiração de 7 dias dos documentos de conversão.

#### Não funcionais

- **NFR-001**: Integridade: nenhuma imagem é separada, agrupada ou reordenada sem aprovação, e a ordem do `.md` é a aprovada. **Verificação**: testes que comparam a ordem aprovada com a do `.md` e verificam que não há geração antes da confirmação.
- **NFR-002**: Privacidade: o agrupamento usa somente metadados locais, sem IA externa nem serviço de rede. **Verificação**: provider espião e rede simulada nos testes.
- **NFR-003**: Desempenho: a proposta de 50 imagens não executa OCR e termina em até 2 segundos; lotes de 10 a 20 imagens geram em segundo plano com progresso; a junção de tabelas respeita os limites existentes de tempo e tamanho. **Verificação**: teste com 50 imagens sintéticas e medição de tempo; PDF de 100 páginas sintético.
- **NFR-004**: Acessibilidade e responsividade: controles operáveis por teclado, mudanças anunciadas em `role=status`, foco visível e sem rolagem horizontal em 375 px. **Verificação**: testes de componente com Testing Library e conferência visual em desktop e mobile.

#### Erros e casos-limite

- Imagem ilegível → aviso no lugar da imagem e "Revisar".
- Proposta incerta → nada pré-aprovado; a pessoa decide cada grupo.
- Aprovação abandonada → o lote aguarda e nada é gerado; expira em 7 dias.
- Envio com uma única imagem → sem tela de aprovação; documento próprio.
- Imagens sem data e hora ou fora de pasta → a proposta usa as pistas restantes e fica incerta.
- Tabela que não se junta com segurança → não junta, "Revisar".
- Falha na geração de um grupo → só aquele grupo fica "Falhou" com motivo.
- Imagem apagada do lote depois da proposta → o grupo é recalculado sem ela e a proposta volta a "incerta".

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI + SQLAlchemy + Alembic; worker Procrastinate; conversão por documento em `process_conversion_document_task`; conversores em `src/pipeline/conversion/converters/` (PDF por `pymupdf4llm`, DOCX por `python-docx`, imagem por OCR); estado `aguardando_abas` e `SelecaoAbas` como precedente (R-001).
- Frontend Next.js: `ConversaoSheet`, `PainelLoteConversao`, `DataGridLotesConversao`, `SeloRevisarDocumento`, `situacao.ts`.
- Depende da SPEC-0037 apenas para a lista de "Revisar" no relatório do lote e para a regra de papéis (DEC-007); a geração de grupos e tabelas funciona sem ela.

#### Arquitetura e módulos

- `src/pipeline/conversion/agrupamento.py` (novo, sem HTTP nem banco): `propor_grupos(arquivos)` recebe nome, data e hora e pasta de cada imagem e devolve grupos ordenados com a certeza.
- `src/pipeline/conversion/converters/grupo.py` (novo): `GrupoImagensConverter` converte cada imagem com `ImageConverter`, na ordem aprovada, e monta as seções com "Origem: <arquivo>" ou "imagem não legível: <arquivo>".
- `src/pipeline/conversion/tabelas.py` (novo): `normalizar_tabelas(paginas)` classifica tabelas em simples ou complexa, converte as complexas em texto corrido e junta tabelas contínuas entre páginas; usado pelos conversores de PDF e DOCX.
- `src/pipeline/conversion/config.py`: parâmetros do intervalo máximo entre imagens do mesmo grupo (padrão 10 minutos) e do tempo máximo da proposta.
- Fluxo: envio com ≥2 imagens → proposta de grupos → lote `aguardando_grupos` → aprovação → um `DocumentoConversao` por grupo e por imagem isolada → conversão em segundo plano → `.md` com origens e avisos.
- A fachada `service.py` expõe `propor_grupos_conversao`.

#### Migrations

- Revisão `0040_grupos_e_tabelas`, encadeada na última revisão aplicada no momento da implementação: cria `grupos_imagem`; acrescenta em `documentos_conversao` as colunas `grupo_id`, `posicao_no_grupo`, `modificado_em` e `pasta_origem`; downgrade na ordem inversa; sem backfill.

#### Models

- `GrupoImagem`: `id`, `lote_id`, `ordem`, `certeza` (`total`, `incerta`), `aprovado`, `documento_id` (documento do grupo, após aprovação).
- `DocumentoConversao`: novas colunas acima; valor de formato `grupo` para o documento do grupo; situação `aguardando_grupos` para as imagens aguardando. Arquivo: `src/app/models.py`.

#### Controllers e casos de uso

- `src/app/routers/conversao.py`: `POST /conversoes` passa a aceitar os metadados `modificado_em` e `pasta` por arquivo e, com ≥2 imagens, devolve o lote em `aguardando_grupos` com a proposta; novas rotas `GET /conversoes/{lote}/grupos`, `PUT /conversoes/{lote}/grupos` (ajuste do rascunho; owner/admin), `POST /conversoes/{lote}/grupos/confirmar` (owner/admin) e `GET /conversoes/{lote}/documentos/{id}/miniatura` (imagem reduzida autenticada).
- Erros: 403 (papel), 404, 409 (lote fora de `aguardando_grupos`), 422 (grupos inconsistentes, por exemplo imagem em dois grupos).

#### Views e experiência

- Detalhado na seção 10.

#### Queries e repositórios

- `src/app/repo.py`: grupos do lote com suas imagens ordenadas, atualização do rascunho, expiração; índice em `grupos_imagem(lote_id)` e `documentos_conversao(grupo_id)`. `_SITUACOES_DOCUMENTO_ATIVAS` e `recalcular_situacao_lote` passam a reconhecer `aguardando_grupos`.

#### Jobs e processamento assíncrono

- A geração do `.md` de cada grupo reaproveita `process_conversion_document_task` (formato `grupo`); idempotente; falha do grupo vira `falhou` com motivo seguro, sem afetar os demais. A expiração de 7 dias existente passa a apagar propostas e imagens de lotes que ficaram aguardando.

#### Estrutura de arquivos

```text
specs/draft/0040-fase-1-reagrupar-sequencias-e-tabelas/
  spec.md
  research/
src/pipeline/conversion/agrupamento.py
src/pipeline/conversion/tabelas.py
src/pipeline/conversion/converters/grupo.py
alembic/versions/0040_grupos_e_tabelas.py
tests/test_agrupamento_imagens.py
tests/test_conversion_grupo.py
tests/test_conversion_tabelas.py
tests/test_router_grupos.py
tests/test_grupos_retencao.py
frontend/src/features/conversao/{AprovacaoGrupos,CartaoGrupoImagens}.tsx
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| GrupoImagem | `id` | `ordem`, `certeza`, `aprovado`; cada imagem pertence a no máximo um grupo | N:1 LoteConversao, 1:N DocumentoConversao (imagens), 1:1 DocumentoConversao (do grupo) |
| DocumentoConversao (extensão) | `id` | `grupo_id`, `posicao_no_grupo` (a partir de 1, única por grupo), `modificado_em`, `pasta_origem` | N:1 GrupoImagem |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| LoteConversao | (novo, ≥2 imagens) | envio | aguardando_grupos | nenhum `.md` gerado |
| LoteConversao | aguardando_grupos | confirmar grupos | processando | cada imagem em exatamente um grupo ou isolada |
| GrupoImagem | proposto | ajuste | proposto | posições contíguas |
| GrupoImagem | proposto | confirmação | aprovado | autor e data registrados |
| DocumentoConversao (grupo) | fila | conversão concluída | concluido | seções na ordem aprovada |

#### Migração e retenção

- Migration aditiva `0040_grupos_e_tabelas` com downgrade. Retenção de 7 dias, igual aos documentos de conversão; o registro do lote permanece.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. Um passo de aprovação no lote de conversão e o selo "Revisar" com o motivo.

#### Stack e convenções de interface

- Next.js (App Router) + React + TypeScript + Tailwind, shadcn/ui (Base UI), testes com Vitest e Testing Library. Telas atuais afetadas: `ConversaoSheet` (envio e passos do lote), `PainelLoteConversao` e `DataGridLotesConversao`. Preservados: o fluxo de abas do Excel (`SelecaoAbas`), `SeloRevisarDocumento` e `situacao.ts`. Fontes: `INTERFACE.md`, `DESIGNSYSTEM.MD`, `frontend/src/features/conversao/`.

#### Telas e responsabilidades

- **Passo "Aprovar grupos" no lote**: owner/admin confere os grupos propostos, ajusta e confirma; member vê em modo leitura.
- **Painel do lote**: mostra "Aguardando grupos", o selo "Revisar" com o motivo e o progresso.

#### Fluxo de informação e navegação

- A pessoa envia imagens no `ConversaoSheet` → o lote entra em "Aguardando grupos" e o passo de aprovação aparece no mesmo painel → ajusta e confirma → o painel mostra os documentos em conversão e depois os `.md` com selos "Revisar" quando houver. A trilha de navegação atual volta à lista de lotes.

#### Menus e navegação principal

- Sem item novo de menu: o passo vive no painel de conversão, já acessível pela aba "Conversão de documentos" do Workspace.

#### Formulários e ações

- Ações por cartão de grupo: "Mover para outro grupo" (seletor), "Reordenar" (botões subir e descer, também por teclado) e, no rodapé, "Confirmar grupos" (principal). Sem campos de texto; o aviso de proposta incerta orienta a conferir. Validação: nenhum grupo vazio e cada imagem em um só grupo, com erro junto do cartão.

#### Composição e disposição

- Lista de cartões, um por grupo, com cabeçalho (nome do grupo e certeza) e as imagens como miniaturas numeradas na ordem sugerida; rodapé fixo com "Confirmar grupos". No celular os cartões empilham e as miniaturas se ajustam à largura.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Lote | `AprovacaoGrupos` | Compõe os cartões, o aviso de certeza e a confirmação | `frontend/src/features/conversao/AprovacaoGrupos.tsx` | `Alert`, `Button` | shadcn/ui + próprio | Novo; segue `SelecaoAbas` |
| Lote | `CartaoGrupoImagens` | Um grupo com miniaturas, mover e reordenar | `frontend/src/features/conversao/CartaoGrupoImagens.tsx` | `Select`, `Button`, `Badge` | shadcn/ui + próprio | Novo |
| Lote | `ConversaoSheet` | Exibe o passo quando o lote está aguardando grupos e envia os metadados dos arquivos | `frontend/src/features/conversao/ConversaoSheet.tsx` | `Sheet` | próprio | Estende o existente |
| Lote | `situacao.ts` | Rótulo e variante de "Aguardando grupos" | `frontend/src/features/conversao/situacao.ts` | `Badge` | próprio | Estende o existente |
| Lote | `SeloRevisarDocumento` | Motivos novos (tabela complexa, tabela não juntada, imagem não legível) | `frontend/src/features/conversao/SeloRevisarDocumento.tsx` | `Badge` | próprio | Estende o existente |

- Registrar cada bloco em `INTERFACE.md` com consumidores e origem; a página apenas compõe esses blocos.

#### Estados e acessibilidade

- Carregando as miniaturas com `Skeleton` e `aria-busy`; erro ao confirmar em `Alert` com "Tentar novamente"; confirmação anunciada em `role=status`; permissão insuficiente esconde os controles e mantém a leitura.
- Mover e reordenar por teclado, com a mudança anunciada e o foco preservado no cartão; miniaturas com texto alternativo igual ao nome do arquivo.

#### Contrato CRUD

- Não há CRUD de entidade nova: grupos são um passo de aprovação do lote. A superfície de lotes continua com o `PageHeader` único e o `DataGrid` existente (`DataGridLotesConversao`) em largura total, com a coluna `ID` visível, a linha inteira como link para o detalhe e as ações independentes de editar e apagar já existentes (apagar respeita a permissão e confirma a consequência). Os componentes novos entram em `INTERFACE.md`.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre em cada tarefa de interface, em desktop e 375 px, nos estados carregando, proposta incerta, proposta pré-aprovada, erro e sucesso, conferindo bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD`. Tarefas de backend registram `Não aplicável` com motivo.

#### APIs expostas

- As rotas da seção 8 e a extensão de `POST /conversoes`, sob `/api/v1`, autenticadas por sessão, com `require_write_role` nas escritas.

#### APIs externas utilizadas

- Nenhuma. O OCR é local (Tesseract) e nenhum dado sai do sistema.

#### Documentação das APIs consultadas

- Nenhuma documentação externa.

#### Eventos e outros contratos

- Saída do grupo: Markdown com uma seção por imagem e a linha "Origem: <arquivo>", compatível com a SPEC-0002.

### 11. Estratégia TDD

- **Unidade**: heurística de agrupamento (prefixo, numeração, intervalo de tempo, pasta), classificação de tabelas, junção entre páginas e montagem do `.md` do grupo, componentes React isolados.
- **Integração/contrato**: rotas com banco isolado, tarefa de conversão do grupo com OCR falso e com imagem real mínima, retenção com datas simuladas, migration `0040` com downgrade.
- **BDD/aceite**: o Gherkin da seção 6 informa o desenho de cada caso; nenhum `.feature` é criado.
- **Runner TDD**: projeto Python/Node misto sem PHP; usar os runners existentes: Pytest no backend e Vitest no frontend.
- **E2E**: jornada envio → proposta → aprovação → `.md` pelo cliente de teste da API, com OCR falso; sem rede.
- **Verificação manual**: acerto da proposta com prints reais (opt-in, fora do repositório), pois depende de dados que não podem ser versionados.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, NFR-002, AC-001 | AC-001 na seção 6 | tests/test_agrupamento_imagens.py: três conversas misturadas (`SPECSFY: SPEC-0040 AC-001`) | Pending | Pending | Pending |
| US-001, FR-001, NFR-002, AC-002 | AC-002 na seção 6 | tests/test_agrupamento_imagens.py: numeração e salto de tempo (`SPECSFY: SPEC-0040 AC-002`) | Pending | Pending | Pending |
| US-001, FR-001, FR-002, AC-003 | AC-003 na seção 6 | tests/test_agrupamento_imagens.py: proposta incerta (`SPECSFY: SPEC-0040 AC-003`) | Pending | Pending | Pending |
| US-002, FR-002, AC-004 | AC-004 na seção 6 | frontend/src/features/conversao/AprovacaoGrupos.test.tsx: pré-aprovado e um clique (`SPECSFY: SPEC-0040 AC-004`) | Pending | Pending | Pending |
| US-002, FR-002, FR-008, NFR-001, AC-005 | AC-005 na seção 6 | tests/test_router_grupos.py: nada gerado antes de confirmar (`SPECSFY: SPEC-0040 AC-005`) | Pending | Pending | Pending |
| US-002, FR-002, NFR-004, AC-006 | AC-006 na seção 6 | frontend/src/features/conversao/CartaoGrupoImagens.test.tsx: mover e reordenar por teclado (`SPECSFY: SPEC-0040 AC-006`) | Pending | Pending | Pending |
| US-002, FR-003, NFR-001, AC-007 | AC-007 na seção 6 | tests/test_conversion_grupo.py: seções na ordem aprovada com origem (`SPECSFY: SPEC-0040 AC-007`) | Pending | Pending | Pending |
| US-003, FR-003, AC-008 | AC-008 na seção 6 | tests/test_router_grupos.py: imagem isolada (`SPECSFY: SPEC-0040 AC-008`) | Pending | Pending | Pending |
| US-003, FR-004, AC-009 | AC-009 na seção 6 | tests/test_conversion_grupo.py: imagem não legível (`SPECSFY: SPEC-0040 AC-009`) | Pending | Pending | Pending |
| US-003, FR-004, FR-008, AC-010 | AC-010 na seção 6 | tests/test_router_grupos.py: falha isolada de um grupo (`SPECSFY: SPEC-0040 AC-010`) | Pending | Pending | Pending |
| US-003, FR-004, AC-011 | AC-011 na seção 6 | tests/test_conversion_grupo.py: relatório lista Revisar (`SPECSFY: SPEC-0040 AC-011`) | Pending | Pending | Pending |
| US-004, FR-005, AC-012 | AC-012 na seção 6 | tests/test_conversion_tabelas.py: tabela simples (`SPECSFY: SPEC-0040 AC-012`) | Pending | Pending | Pending |
| US-004, FR-005, AC-013 | AC-013 na seção 6 | tests/test_conversion_tabelas.py: tabela complexa em texto (`SPECSFY: SPEC-0040 AC-013`) | Pending | Pending | Pending |
| US-004, FR-005, AC-014 | AC-014 na seção 6 | tests/test_conversion_tabelas.py: células mescladas em DOCX (`SPECSFY: SPEC-0040 AC-014`) | Pending | Pending | Pending |
| US-005, FR-006, AC-015 | AC-015 na seção 6 | tests/test_conversion_tabelas.py: tabela contínua juntada (`SPECSFY: SPEC-0040 AC-015`) | Pending | Pending | Pending |
| US-005, FR-006, AC-016 | AC-016 na seção 6 | tests/test_conversion_tabelas.py: colunas diferentes não juntam (`SPECSFY: SPEC-0040 AC-016`) | Pending | Pending | Pending |
| US-005, FR-006, AC-017 | AC-017 na seção 6 | tests/test_conversion_tabelas.py: cabeçalho repetido removido (`SPECSFY: SPEC-0040 AC-017`) | Pending | Pending | Pending |
| US-002, FR-007, AC-018 | AC-018 na seção 6 | tests/test_router_grupos.py: member não aprova (`SPECSFY: SPEC-0040 AC-018`) | Pending | Pending | Pending |
| US-002, FR-007, AC-019 | AC-019 na seção 6 | tests/test_router_grupos.py: recusa na API (`SPECSFY: SPEC-0040 AC-019`) | Pending | Pending | Pending |
| FR-008, NFR-001, AC-020 | AC-020 na seção 6 | tests/test_grupos_retencao.py: 7 dias (`SPECSFY: SPEC-0040 AC-020`) | Pending | Pending | Pending |
| US-002, NFR-004, AC-021 | AC-021 na seção 6 | frontend/src/features/conversao/AprovacaoGrupos.test.tsx: 375 px (`SPECSFY: SPEC-0040 AC-021`) | Pending | Pending | Pending |
| FR-001, NFR-003, AC-022 | AC-022 na seção 6 | tests/test_agrupamento_imagens.py: 50 imagens sem OCR (`SPECSFY: SPEC-0040 AC-022`) | Pending | Pending | Pending |
| US-001, FR-001, NFR-002, AC-023 | AC-023 na seção 6 | tests/test_router_grupos.py: sem chamadas externas (`SPECSFY: SPEC-0040 AC-023`) | Pending | Pending | Pending |
| FR-003, NFR-001, AC-024 | AC-024 na seção 6 | tests/test_conversion_grupo.py: ordem preservada no reenvio (`SPECSFY: SPEC-0040 AC-024`) | Pending | Pending | Pending |
| US-002, FR-007, NFR-004, AC-025 | AC-025 na seção 6 | frontend/src/features/conversao/AprovacaoGrupos.test.tsx: member em modo leitura (`SPECSFY: SPEC-0040 AC-025`) | Pending | Pending | Pending |
| US-002, FR-003, NFR-003, AC-026 | AC-026 na seção 6 | tests/test_router_grupos.py: 20 imagens em segundo plano (`SPECSFY: SPEC-0040 AC-026`) | Pending | Pending | Pending |
| FR-006, NFR-003, AC-027 | AC-027 na seção 6 | tests/test_conversion_tabelas.py: PDF de 100 páginas (`SPECSFY: SPEC-0040 AC-027`) | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | tests/test_agrupamento_imagens.py | Pending |
| FR-001 | AC-002 | Unidade | tests/test_agrupamento_imagens.py | Pending |
| FR-001 | AC-003 | Unidade | tests/test_agrupamento_imagens.py | Pending |
| FR-001 | AC-022 | Unidade | tests/test_agrupamento_imagens.py | Pending |
| FR-001 | AC-023 | Contrato | tests/test_router_grupos.py | Pending |
| FR-002 | AC-003 | Unidade | tests/test_agrupamento_imagens.py | Pending |
| FR-002 | AC-004 | Componente | frontend/src/features/conversao/AprovacaoGrupos.test.tsx | Pending |
| FR-002 | AC-005 | Contrato | tests/test_router_grupos.py | Pending |
| FR-002 | AC-006 | Componente | frontend/src/features/conversao/CartaoGrupoImagens.test.tsx | Pending |
| FR-003 | AC-007 | Integração | tests/test_conversion_grupo.py | Pending |
| FR-003 | AC-008 | Contrato | tests/test_router_grupos.py | Pending |
| FR-003 | AC-024 | Integração | tests/test_conversion_grupo.py | Pending |
| FR-003 | AC-026 | Contrato | tests/test_router_grupos.py | Pending |
| FR-004 | AC-009 | Integração | tests/test_conversion_grupo.py | Pending |
| FR-004 | AC-010 | Contrato | tests/test_router_grupos.py | Pending |
| FR-004 | AC-011 | Integração | tests/test_conversion_grupo.py | Pending |
| FR-005 | AC-012 | Unidade | tests/test_conversion_tabelas.py | Pending |
| FR-005 | AC-013 | Unidade | tests/test_conversion_tabelas.py | Pending |
| FR-005 | AC-014 | Unidade | tests/test_conversion_tabelas.py | Pending |
| FR-006 | AC-015 | Unidade | tests/test_conversion_tabelas.py | Pending |
| FR-006 | AC-016 | Unidade | tests/test_conversion_tabelas.py | Pending |
| FR-006 | AC-017 | Unidade | tests/test_conversion_tabelas.py | Pending |
| FR-006 | AC-027 | Integração | tests/test_conversion_tabelas.py | Pending |
| FR-007 | AC-018 | Contrato | tests/test_router_grupos.py | Pending |
| FR-007 | AC-019 | Contrato | tests/test_router_grupos.py | Pending |
| FR-007 | AC-025 | Componente | frontend/src/features/conversao/AprovacaoGrupos.test.tsx | Pending |
| FR-008 | AC-005 | Contrato | tests/test_router_grupos.py | Pending |
| FR-008 | AC-010 | Contrato | tests/test_router_grupos.py | Pending |
| FR-008 | AC-020 | Integração | tests/test_grupos_retencao.py | Pending |
| NFR-001 | AC-005 | Contrato | tests/test_router_grupos.py | Pending |
| NFR-001 | AC-007 | Integração | tests/test_conversion_grupo.py | Pending |
| NFR-001 | AC-024 | Integração | tests/test_conversion_grupo.py | Pending |
| NFR-002 | AC-001 | Unidade | tests/test_agrupamento_imagens.py | Pending |
| NFR-002 | AC-002 | Unidade | tests/test_agrupamento_imagens.py | Pending |
| NFR-002 | AC-023 | Contrato | tests/test_router_grupos.py | Pending |
| NFR-003 | AC-022 | Unidade | tests/test_agrupamento_imagens.py | Pending |
| NFR-003 | AC-026 | Contrato | tests/test_router_grupos.py | Pending |
| NFR-003 | AC-027 | Integração | tests/test_conversion_tabelas.py | Pending |
| NFR-004 | AC-006 | Componente | frontend/src/features/conversao/CartaoGrupoImagens.test.tsx | Pending |
| NFR-004 | AC-021 | Componente | frontend/src/features/conversao/AprovacaoGrupos.test.tsx | Pending |
| NFR-004 | AC-025 | Componente | frontend/src/features/conversao/AprovacaoGrupos.test.tsx | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0040-fase-1-reagrupar-sequencias-e-tabelas/spec.md`
- **Achados**: Pending. Ponto aberto que impede o gate: conjunto de prints reais (fora do repositório) para medir o acerto da proposta e calibrar o intervalo de tempo.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/draft/0040-fase-1-reagrupar-sequencias-e-tabelas/spec.md`
- **Achados**: Pending.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0040-fase-1-reagrupar-sequencias-e-tabelas/spec.md .`
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

- Caminho crítico previsto: testes RED (seção 11) → tabelas (independentes) e agrupamento → persistência e migration → rotas e novo estado do lote → conversor do grupo → interface de aprovação → regressão.
- Tarefas paralelas: tabelas (US-004 e US-005) são independentes de grupos (US-001 a US-003) e podem ser feitas em paralelo.
- Estratégia de MVP: US-004 e US-001/US-002 primeiro; US-003 e US-005 depois.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0023 e SPEC-0036 (conversão e formatos), SPEC-0002 (contrato do `.md`).
- SPEC-0037 para listar documentos "Revisar" no relatório do lote e para os papéis (DEC-007); sem ela, o selo no painel já funciona.
- Conjunto de prints reais, fora do repositório, para medir e calibrar a proposta.

#### Riscos

- A heurística por nome, data e hora e pasta erra o limite entre sequências → a aprovação humana é obrigatória e a proposta é marcada incerta quando as pistas divergem.
- A junção de tabelas cola tabelas que não eram uma só → só junta quando a estrutura das colunas bate; em dúvida mantém separado e marca "Revisar".
- Metadados ausentes (arquivo sem data ou fora de pasta) → a proposta usa as pistas restantes e fica incerta.
- Tabela complexa perdida em texto corrido → o selo "Revisar" e o relatório do lote deixam a conferência explícita.

#### Suposições

- A data e hora do arquivo vêm do `lastModified` do navegador e a pasta do `webkitRelativePath` quando disponíveis; o cliente os envia por arquivo no envio.
- O limite padrão de tempo entre imagens do mesmo grupo é de 10 minutos, configurável e calibrável com prints reais.
- Pistas "concordam" quando prefixo comum, numeração contínua, mesma pasta e intervalo dentro do limite apontam para os mesmos grupos.
- Tabela complexa = células mescladas, aninhadas, número de colunas variável entre linhas ou cabeçalho de mais de um nível; "colunas batem" = mesmo número de colunas e, quando há cabeçalho, mesmos rótulos.
- Em reenvio para conversão, o grupo mantém os membros e a ordem aprovados.
- Miniaturas são servidas reduzidas pelo backend, só a quem tem acesso ao lote.

### 17. Decisões

- **DEC-001**: o sistema propõe e a pessoa aprova; nunca reordena em silêncio — concilia a pasta isolada do briefing com envios misturados.
- **DEC-002**: a primeira entrega usa só nome, data e hora e pasta — evita OCR e IA no agrupamento; OCR fica como evolução depois de medir os acertos.
- **DEC-003**: um `.md` por grupo, com uma seção por imagem e "Origem: <arquivo>" no corpo, compatível com a SPEC-0002 (R-002).
- **DEC-004**: tabela complexa vira texto corrido com "Revisar" — prefere sinalizar a entregar uma tabela errada.
- **DEC-005**: tabela contínua só é juntada com estrutura de colunas compatível; em dúvida, separada e "Revisar".
- **DEC-006**: papéis conforme a DEC-007 da SPEC-0037: owner e admin aprovam, member consulta.
- **DEC-007**: a tela de aprovação é um passo do `ConversaoSheet`, no padrão de `SelecaoAbas`, em vez de rota própria.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
