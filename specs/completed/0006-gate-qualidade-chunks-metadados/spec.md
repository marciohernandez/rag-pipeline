# Especificação integrada: Gate automatizado de qualidade de chunks e metadados

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0006 |
| Slug | 0006-gate-qualidade-chunks-metadados |
| Status | Complete |
| Effort | 6 |
| Effort updated at | 2026-09-03 |
| Effort rationale | Recalibrado de 1 para 6 na promoção. A fatia cria um módulo novo com dois níveis de avaliação, seis invariantes determinísticos e seis sinais heurísticos, integra um ponto de bloqueio no caminho de indexação, acrescenta uma CLI no padrão da SPEC-0004, estende `config.yaml` e exige conjunto sintético de teste com cada defeito representado. O risco está concentrado em dois pontos: um invariante mal formulado bloqueia uma base saudável, e uma heurística mal calibrada afoga o relatório em falso positivo. Comparável à SPEC-0001 e à SPEC-0004, ambas 6. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-03 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O pipeline prepara uma base para recuperação vetorial mas não prova a qualidade do que preparou. `src/manifest.py:71-81` bloqueia a indexação em quatro condições de identidade — nenhum chunk gerado, chunk sem `chunk_id`, `chunk_id` duplicado e contagem inconsistente — e nada além disso. Tamanho, conteúdo e completude dos metadados chegam ao vector store sem qualquer conferência.

A medição de 2026-09-03 sobre `output/vivo_gold_banda_larga_pf/chunks.json`, com 208 chunks e sete documentos, mostrou que o diagnóstico registrado no BACKLOG-0005 estava apontando o sintoma errado. A auditoria original identificou 65 chunks abaixo de 250 caracteres e 12 acima de 1000, e concluiu daí que havia um problema de tamanho. Os números se confirmam, mas não sustentam a conclusão:

- o menor chunk da base tem 99 caracteres e é `[Aplicativos e Conteúdos Incluídos > Música > Apple Music] ### Apple Music — 30 dias grátis.`, uma unidade semântica completa e perfeitamente recuperável;
- o maior tem 1046 caracteres, que é o `chunk_size` de 1000 mais o breadcrumb injetado por `src/chunker.py:104-110`. Nenhum chunk passa de 1200. O teto está sendo respeitado.

O dano real está em quatro defeitos que nenhuma regra de tamanho detecta:

1. **Perda de estrutura de headings.** Dois dos sete documentos escrevem heading dentro de bullet — `* ## **Ganhe R$50 em Vale Bonus**`, 37 ocorrências em um deles. O `MarkdownHeaderTextSplitter` não reconhece essa forma, então os títulos ficam invisíveis e todos os chunks do arquivo colapsam sob um único breadcrumb, sem `secao` nem `subsecao`. O defeito é de 94% e 73% dos chunks nesses dois arquivos, e de 0% nos outros cinco.
2. **Truncamento no meio da frase.** 14 dos 191 chunks `detail` terminam em frase incompleta, cortados pelo limite de tamanho. Exemplo: `"...A adesão ao Club Fan não tem custo para o"`. Todos estão dentro do limite, invisíveis para qualquer regra de tamanho.
3. **Duplicata exata.** Dois chunks byte a byte idênticos no mesmo caminho lógico, consequência direta da perda de estrutura descrita no item 1.
4. **Texto colapsado por tabulação.** Cinco linhas do documento de regulamento separam palavras por tabulação; o processamento as colapsa, produzindo `SaibamaissobreestebenefícioconsultandoseuRegulamento`.

A base indexada **não está falhando hoje**. A validação de 2026-09-02 registra `desfecho: aprovado`, 208 chunks previstos e observados, com as dez consultas do gabarito aprovadas — inclusive as duas que caem dentro dos documentos com estrutura perdida, com scores 0,779 e 0,754. Os defeitos são risco latente de qualidade, não falha presente de recuperação. Essa distinção é normativa nesta fatia: ela é o motivo de a duplicata exata ser sinal e não bloqueio.

#### Resultado desejado

O operador executa o pipeline e recebe duas garantias distintas. Um conjunto que viole um invariante determinístico de integridade não chega ao vector store, e o motivo do bloqueio identifica o invariante violado. Um conjunto íntegro é indexado normalmente e produz um relatório que aponta **quais documentos de origem revisar**, não quais chunks são curtos.

O mantenedor que ajusta as regras de chunking pode rodar a mesma avaliação isoladamente sobre os chunks já gerados, quantas vezes precisar, sem tocar no destino remoto.

#### Métricas de sucesso

- Os seis invariantes críticos interrompem a execução antes de qualquer escrita no vector store, comprovado por caso de teste por invariante.
- Nenhum dos seis sinais de qualidade interrompe a execução, comprovado por caso que injeta cada defeito e observa indexação concluída.
- Sobre a base de referência de 208 chunks, o relatório aponta os dois documentos com perda de estrutura e não aponta os cinco saudáveis.
- O mínimo medido sobre conteúdo útil, com o padrão de 60 caracteres, sinaliza 8 chunks na base de referência, contra os 65 da métrica bruta de 250.
- `manifest.json` permanece byte a byte com a mesma estrutura de campos após a introdução do gate.
- A suíte completa permanece verde e nenhuma dependência é acrescentada a `pyproject.toml`.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: os números da auditoria original se sustentam? → Sim quanto à contagem, não quanto à conclusão. 65 chunks abaixo de 250 e 12 acima de 1000 se confirmam em 208, mas o menor chunk é uma unidade semântica completa e o maior é o `chunk_size` configurado mais o breadcrumb. A métrica de tamanho é majoritariamente ruído.
- **R-002**: qual é a causa raiz da duplicata exata? → Heading dentro de bullet (`* ## **Título**`), em 37 ocorrências de um documento. O `MarkdownHeaderTextSplitter` não o reconhece, os títulos somem, os chunks colapsam sob um breadcrumb único e o rodapé repetido pela origem vira dois chunks idênticos.
- **R-003**: a duplicata exata é falha de integridade? → Não. `src/identity.py:69-70` desempata `chunk_id` por contador de ocorrência, então a sincronização idempotente permanece correta. Conteúdo duplicado com `chunk_id` distintos é ruído no top-k, não corrupção. Por isso é sinal, não bloqueio.
- **R-004**: um máximo global fixo é seguro? → Não. `src/chunker.py:26-38` permite que o frontmatter sobrescreva `chunk_size` por documento via `chunk_size_recommended`. Um máximo fixo passaria a acusar falso positivo assim que um documento declarasse outro valor. O máximo precisa ser derivado por documento.
- **R-005**: qual padrão de CLI de diagnóstico o repositório já usa? → `validate.py`, entregue pela SPEC-0004: relatório legível no stdout, resultado estruturado em `output/<base>/validation-<uuid>.json` e códigos de saída 0 aprovado, 1 reprovado, 2 não foi possível avaliar. Esta fatia espelha o padrão.
- **R-006**: o breadcrumb distorce a medição de tamanho? → Sim. `src/chunker.py:104-110` injeta o breadcrumb dentro do `page_content`. O menor chunk tem 99 caracteres brutos e cerca de 40 de texto real. Medir o mínimo sobre o bruto sinaliza 65 chunks; sobre o conteúdo útil, com limiar de 60, sinaliza 8.
- **R-007**: a perda de estrutura já prejudica a recuperação medida? → Não. As duas consultas do gabarito que caem nos documentos afetados passam, com 0,779 e 0,754. O defeito é risco latente.

#### Fontes e contexto consultados

- `src/chunker.py`, `src/identity.py`, `src/manifest.py`, `src/status_gate.py` e `pipeline.py`: geração, identidade, bloqueio atual e ponto de integração.
- `validate.py` e `src/validation.py`: padrão de CLI de diagnóstico da SPEC-0004.
- `config.yaml` e `config.example.yaml`: seção `chunking` e convenção de configuração versionada.
- `output/vivo_gold_banda_larga_pf/chunks.json`, `manifest.json` e `validation-1ff74dbb-d597-43b2-9ec6-73079e78989c.json`: base de referência medida.
- `documentos/vivo_gold_banda_larga_pf/*.md`: origem dos defeitos de estrutura e tabulação.
- `specs/backlog/0005-gate-qualidade-chunks-metadados.md`: item de origem, refinado em 2026-09-03.
- `specs/completed/0001-bloquear-recriacao-destrutiva/spec.md` e `specs/completed/0004-validar-recuperacao-operacao/spec.md`: precedentes de fail-closed e de CLI de diagnóstico.
- `.specsfy/RULES.md`: configuração centralizada, neutralidade de cliente, registro por execução e ausência de segredos.

#### Documentação consultada

- LangChain `MarkdownHeaderTextSplitter` e `RecursiveCharacterTextSplitter`, versão instalada em `.venv`, via leitura direta do comportamento observado em `src/chunker.py`. Tópico relevante: headings dentro de bullet não são reconhecidos como cabeçalho.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo. Toda a evidência desta fatia foi produzida por medição sobre arquivos do próprio repositório, e os números estão registrados nas seções 1 e 2 e no item de backlog de origem.

#### Dúvidas respondidas

- **Q**: o gate bloqueia ou apenas relata? → **A**: os dois, em níveis separados. Somente regras determinísticas bloqueiam; heurísticas relatam.
- **Q**: quais regras bloqueiam? → **A**: as seis de integridade e rastreabilidade listadas em FR-001. Truncamento, corrupção, tamanho, duplicata e metadados semânticos parciais não bloqueiam.
- **Q**: onde o gate roda? → **A**: embutido no `pipeline.py` entre chunking e indexação, e também como comando próprio de diagnóstico.
- **Q**: como os limiares de tamanho são definidos? → **A**: máximo derivado do `chunk_size` efetivo de cada documento mais a margem do breadcrumb; mínimo explícito em `config.yaml`, único por base, medido sobre conteúdo útil, padrão 60.
- **Q**: a duplicata exata bloqueia? → **A**: não. É sinal, por R-003 e R-007.
- **Q**: como o relatório se organiza? → **A**: por documento de origem, com o detalhe por chunk preservado no resultado estruturado.
- **Q**: onde o resultado é gravado? → **A**: em `output/<base>/quality-<uuid>.json`, fora do `manifest.json`, sem histórico agregado nesta fatia.
- **Q**: o gate roda no modo `--only-chunks`? → **A**: sim. Registrado como suposição S-001 e materializado em FR-005.
- **Q**: quais são os códigos de saída do diagnóstico? → **A**: 0, 1 e 2, no padrão da SPEC-0004. Registrado como suposição S-002 e materializado em FR-005 e AC-012.

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Avaliação determinística dos seis invariantes críticos sobre o conjunto local de chunks, antes de qualquer escrita no vector store.
- Cálculo dos seis sinais de qualidade, sem interromper a execução.
- Derivação do limite máximo de tamanho a partir do `chunk_size` efetivo de cada documento, somada a margem do breadcrumb.
- Limite mínimo configurável em `config.yaml`, medido sobre conteúdo útil, com padrão inicial de 60 caracteres.
- Integração do bloqueio no `pipeline.py`, entre a geração dos chunks e a indexação.
- Comando próprio de diagnóstico, com relatório legível no stdout e códigos de saída 0, 1 e 2.
- Resultado estruturado em `output/<base>/quality-<uuid>.json`, agrupado por documento e com detalhe por chunk.
- Testes das seis regras determinísticas e dos seis sinais, sobre conjunto sintético com cada defeito representado.

#### Fora de escopo

- Corrigir automaticamente os documentos de origem.
- Deduplicar, reescrever, reordenar ou rechunkar conteúdo.
- Alterar a estratégia de chunking, os separadores ou a geração de `section_summary`. Essa reanálise é objeto da captura `specs/inbox/2026-09-03-072811-reanalisar-a-quebra-de-chunks-e-onde-o-resumo-deve-viver.md`, ainda não promovida.
- Histórico agregado, tendência ou comparação de qualidade entre execuções.
- Veredito automático de severidade por arquivo. O relatório apresenta os números; o julgamento é do mantenedor.
- Qualquer interface gráfica. Por decisão registrada no BACKLOG-0008, o frontend pertence ao projeto-mãe `rag-pipeline`.
- Alterar o contrato de frontmatter, o `status_gate` ou a política de sincronização segura.

#### Atores

- **Operador da base**: executa o pipeline sobre uma base Markdown. Precisa que um conjunto inválido não alcance o vector store e que o motivo do bloqueio seja compreensível sem ler o código.
- **Mantenedor do chunking**: ajusta regras de divisão e limites. Precisa medir a qualidade da saída repetidamente, sem indexar, e saber qual documento de origem revisar.

### 4. Princípios e restrições do projeto

- **PR-001**: somente regras determinísticas bloqueiam a indexação. Regra heurística, sujeita a falso positivo, permanece no nível de sinal. Origem: decisão da Pergunta 2 do refinamento, sustentada por R-001 e R-007.
- **PR-002**: o gate é leitura pura sobre o conjunto local. Não abre conexão remota, não escreve no vector store e não executa comando destrutivo. Origem: `.specsfy/Spec.md`, proteção de banco, e a cultura fail-closed da SPEC-0001.
- **PR-003**: nenhum limiar, mensagem ou exemplo carrega identidade, produto ou domínio de cliente. Origem: `.specsfy/RULES.md`, regra de neutralidade verificada por `tests/test_client_neutrality.py`.
- **PR-004**: relatório e resultado estruturado nunca registram credenciais, tokens ou URLs de destino. Origem: `.specsfy/RULES.md`, seções de segurança e operação.
- **PR-005**: `src/manifest.py` preserva sua responsabilidade única de identidade e contagens. O gate estende o ponto de bloqueio, não o substitui, e não grava seu resultado dentro do manifesto.
- **PR-006**: a lógica de negócio é estruturada com orientação a objetos, módulo focado e baixo acoplamento; a variação entre regras usa Strategy. Origem: `.specsfy/RULES.md`, seção Arquitetura.
- **PR-007**: os testes seguem Red-Green-Refactor com Pytest, runner já adotado pelo repositório.

### 5. Histórias de usuário

#### US-001 — Impedir que um conjunto inválido alcance o vector store (P1)

Como operador da base, quero que o pipeline interrompa a execução quando o conjunto de chunks violar um invariante de integridade, para que o destino remoto nunca receba uma carga que eu não poderia rastrear depois.

**Por que P1**: uma carga com identidade quebrada é invisível até alguém consultar a base e não encontrar o que deveria estar lá; o custo de detectar tarde é reprocessar e ressincronizar o destino.
**Teste independente**: injetar um conjunto com `chunk_id` ausente, executar o pipeline e observar que nenhuma escrita ocorreu no destino e que o motivo identifica o invariante.
**Requisitos**: FR-001, NFR-001

#### US-002 — Saber qual documento de origem revisar (P1)

Como mantenedor do chunking, quero um relatório que agrupe os sinais de qualidade por documento de origem, para revisar os arquivos que realmente degradam a preparação em vez de percorrer uma lista de chunks isolados.

**Por que P1**: sem o eixo documento, o relatório vira ruído. Na base de referência, "65 chunks curtos" não indica ação, enquanto "dois de sete arquivos perdem 94% e 73% da estrutura" indica exatamente qual arquivo corrigir.
**Teste independente**: avaliar um conjunto em que dois documentos concentram os chunks sem `secao` e observar que só esses dois aparecem apontados.
**Requisitos**: FR-002, FR-003, FR-004, NFR-002, NFR-003

#### US-003 — Medir a qualidade sem indexar (P2)

Como mantenedor do chunking, quero executar a mesma avaliação isoladamente sobre os chunks já gerados, para iterar nas regras de divisão sem tocar no destino remoto a cada tentativa.

**Por que P2**: o valor depende de US-001 e US-002 existirem, mas sem ele o ciclo de ajuste exige indexar para medir, o que é caro e arriscado.
**Teste independente**: executar o comando de diagnóstico sobre um arquivo de chunks e observar relatório, resultado estruturado e ausência de qualquer escrita no destino.
**Requisitos**: FR-005, NFR-001

### 6. Cenários BDD de aceite

#### AC-001 — Bloqueio por chunk sem identidade

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-001
Feature: Bloqueio por invariante crítico

  Scenario: Interromper quando um chunk está sem chunk_id
    Given um conjunto de chunks em que um deles está sem chunk_id
    When o pipeline avalia o conjunto antes de indexar
    Then a execução é interrompida antes de qualquer escrita no vector store
    And o motivo identifica o invariante de chunk_id ausente
```

#### AC-002 — Bloqueio por identidade duplicada

**Cobre**: US-001, FR-001

```gherkin
@US-001 @FR-001 @AC-002
Feature: Bloqueio por invariante crítico

  Scenario: Interromper quando dois chunks compartilham o mesmo chunk_id
    Given um conjunto de chunks com chunk_id repetido
    When o pipeline avalia o conjunto antes de indexar
    Then a execução é interrompida
    And o motivo identifica o chunk_id duplicado
    And nenhum ponto é escrito no destino
```

#### AC-003 — Bloqueio por chunk sem conteúdo

**Cobre**: US-001, FR-001

```gherkin
@US-001 @FR-001 @AC-003
Feature: Bloqueio por invariante crítico

  Scenario: Interromper quando um chunk não tem conteúdo além do breadcrumb
    Given um chunk cujo page_content contém apenas o breadcrumb injetado
    When o pipeline avalia o conjunto antes de indexar
    Then a execução é interrompida
    And o motivo identifica o chunk sem conteúdo útil
```

#### AC-004 — Bloqueio por metadado de rastreabilidade ausente

**Cobre**: US-001, FR-001

```gherkin
@US-001 @FR-001 @AC-004
Feature: Bloqueio por invariante crítico

  Scenario Outline: Interromper quando falta um metadado obrigatório de rastreabilidade
    Given um chunk sem <metadado>
    When o pipeline avalia o conjunto antes de indexar
    Then a execução é interrompida
    And o motivo nomeia <metadado> como o metadado ausente

    Examples:
      | metadado    |
      | document_id |
      | source_hash |
      | project_id  |
      | chunk_hash  |
      | chunk_type  |
```

#### AC-005 — Sinal não interrompe a execução

**Cobre**: US-001, FR-002, NFR-001

```gherkin
@US-001 @FR-002 @NFR-001 @AC-005
Feature: Sinais de qualidade não bloqueiam

  Scenario: Indexar um conjunto íntegro que contém chunks truncados
    Given um conjunto íntegro em que catorze chunks terminam no meio da frase
    When o pipeline avalia o conjunto antes de indexar
    Then a indexação prossegue normalmente
    And o relatório registra o truncamento como sinal
```

#### AC-006 — Duplicata exata é relatada, não bloqueada

**Cobre**: US-002, FR-002

```gherkin
@US-002 @FR-002 @AC-006
Feature: Sinais de qualidade não bloqueiam

  Scenario: Prosseguir diante de conteúdo duplicado com identidades distintas
    Given dois chunks com conteúdo idêntico, chunk_ids distintos e o mesmo caminho lógico
    When o pipeline avalia o conjunto antes de indexar
    Then a indexação prossegue
    And o relatório registra a duplicata como sinal, identificando o documento de origem
```

#### AC-007 — Mínimo medido sobre o conteúdo útil

**Cobre**: US-002, FR-003, NFR-003

```gherkin
@US-002 @FR-003 @NFR-003 @AC-007
Feature: Limiares de tamanho

  Scenario: Descontar o breadcrumb antes de avaliar o mínimo
    Given um chunk cujo page_content tem noventa e nove caracteres, dos quais cinquenta e nove são breadcrumb
    And o mínimo configurado é sessenta caracteres
    When o gate avalia o tamanho desse chunk
    Then o chunk é sinalizado pelo conteúdo útil de quarenta caracteres
    And o comprimento bruto de noventa e nove caracteres não é usado nessa decisão
    And o limiar aplicado vem da configuração, não do código
```

#### AC-008 — Máximo derivado do documento

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-008
Feature: Limiares de tamanho

  Scenario: Respeitar o chunk_size declarado pelo frontmatter do documento
    Given um documento cujo frontmatter declara chunk_size_recommended de dois mil
    And um chunk desse documento com mil e quinhentos caracteres
    When o gate avalia o tamanho máximo
    Then o limite aplicado deriva de dois mil mais a margem do breadcrumb
    And o chunk não é sinalizado por ultrapassar o padrão global de mil
```

#### AC-009 — Relatório agrupado por documento

**Cobre**: US-002, FR-002, FR-004, NFR-003

```gherkin
@US-002 @FR-002 @FR-004 @NFR-003 @AC-009
Feature: Relatório de sinais

  Scenario: Apontar os documentos afetados e poupar os saudáveis
    Given uma base de sete documentos em que dois concentram os chunks sem secao
    When o gate publica o relatório
    Then os sinais aparecem agrupados por documento de origem
    And os dois documentos afetados aparecem com sua proporção de chunks sem secao
    And os cinco documentos saudáveis não são apontados como defeituosos
    And nenhum nome de cliente ou produto aparece escrito no código do relatório
```

#### AC-010 — Resultado estruturado em arquivo próprio

**Cobre**: US-002, FR-004, NFR-002

```gherkin
@US-002 @FR-004 @NFR-002 @AC-010
Feature: Artefatos da execução

  Scenario: Gravar o resultado sem alterar o manifesto
    Given uma execução em que o gate publicou seu relatório
    When o operador inspeciona os artefatos da execução
    Then o resultado estruturado está em output/<base>/quality-<uuid>.json
    And o detalhe por chunk está preservado nesse arquivo
    And o manifest.json preserva somente identidade e contagens
```

#### AC-011 — Diagnóstico isolado não toca o destino

**Cobre**: US-003, FR-005, NFR-001

```gherkin
@US-003 @FR-005 @NFR-001 @AC-011
Feature: Comando de diagnóstico

  Scenario: Avaliar chunks já gerados sem indexar
    Given um arquivo de chunks já gerado
    When o mantenedor executa o comando de diagnóstico sobre esse arquivo
    Then o relatório legível é apresentado
    And o resultado estruturado é gravado
    And nenhuma conexão com o vector store é aberta
    And nada é escrito no destino
```

#### AC-012 — Códigos de saída do diagnóstico

**Cobre**: US-003, FR-005

```gherkin
@US-003 @FR-005 @AC-012
Feature: Comando de diagnóstico

  Scenario Outline: Distinguir aprovado, reprovado e não avaliável
    Given uma entrada na condição <condicao>
    When o comando de diagnóstico avalia essa entrada
    Then o código de saída é <codigo>

    Examples:
      | condicao                                  | codigo |
      | conjunto íntegro                          | 0      |
      | conjunto que viola um invariante crítico  | 1      |
      | arquivo de chunks ausente ou malformado   | 2      |
```

#### AC-016 — Invariante de contagem no modo de diagnóstico

**Cobre**: US-003, FR-001, FR-005

```gherkin
@US-003 @FR-001 @FR-005 @AC-016
Feature: Comando de diagnóstico

  Scenario: Pular o invariante de contagem quando não há manifesto
    Given um arquivo de chunks íntegro e nenhum manifesto disponível
    When o mantenedor executa o comando de diagnóstico
    Then o invariante de contagem do manifesto é pulado
    And o relatório declara que ele foi pulado por ausência de manifesto
    And os outros cinco invariantes críticos são avaliados normalmente
    And o código de saída reflete apenas os invariantes efetivamente avaliados
```

#### AC-013 — Saída livre de segredos

**Cobre**: FR-004, NFR-002

```gherkin
@FR-004 @NFR-002 @AC-013
Feature: Segurança da saída

  Scenario: Não expor credencial nem destino remoto
    Given uma configuração que contém chave de API e URL do destino remoto
    When o gate publica o relatório legível e o resultado estruturado
    Then nenhuma credencial aparece em qualquer das duas saídas
    And nenhuma URL de destino aparece em qualquer das duas saídas
```

#### AC-014 — Neutralidade de cliente

**Cobre**: FR-003, NFR-003

```gherkin
@FR-003 @NFR-003 @AC-014
Feature: Neutralidade de cliente

  Scenario: Manter o módulo livre de identidade de cliente
    Given o módulo de qualidade e sua configuração
    When a guarda estática varre o código em busca de identificador de cliente
    Then nenhum nome de cliente, produto ou domínio aparece escrito no código
    And cada limiar aplicado vem da configuração da base
```

#### AC-015 — Falha ao gravar preserva o desfecho

**Cobre**: US-003, FR-004, FR-005, NFR-002

```gherkin
@US-003 @FR-004 @FR-005 @NFR-002 @AC-015
Feature: Situações de erro

  Scenario: Informar falha de escrita sem mascarar a avaliação
    Given uma avaliação concluída cujo destino de gravação está indisponível
    When o gate tenta gravar o resultado estruturado
    Then o relatório legível permanece apresentado no stdout
    And a falha de escrita é informada sem expor caminho de credencial
    And o desfecho da avaliação não é mascarado pela falha de gravação
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve avaliar seis invariantes determinísticos sobre o conjunto local de chunks, antes de qualquer escrita no vector store, e interromper a execução identificando o invariante violado quando algum falhar. Os invariantes são: nenhum chunk gerado; chunk sem `chunk_id`; `chunk_id` duplicado; contagem do manifesto inconsistente com o número de chunks, avaliada somente quando o manifesto estiver disponível; chunk com conteúdo vazio ou composto apenas pelo breadcrumb; chunk sem algum dos metadados de rastreabilidade obrigatórios `document_id`, `source_hash`, `project_id`, `chunk_hash` e `chunk_type`.
- **FR-002**: O sistema deve calcular seis sinais de qualidade sem interromper a execução: perda de estrutura, medida pela proporção de chunks sem `secao` e sem `subsecao` por documento; truncamento no meio da frase; duplicata exata de conteúdo no mesmo caminho lógico; texto colapsado por tabulação; distribuição de tamanho quebrada por `chunk_type`; conteúdo útil abaixo do mínimo configurado.
- **FR-003**: O sistema deve derivar o limite máximo de tamanho do `chunk_size` efetivo de cada documento, somada a margem do breadcrumb injetado, e aplicar como limite mínimo um valor configurado em `config.yaml`, único por base, medido sobre o conteúdo útil obtido descontando o breadcrumb do `page_content`, com padrão inicial de 60 caracteres quando a configuração não o declarar.
- **FR-004**: O sistema deve publicar um relatório legível agrupado por documento de origem e gravar o resultado estruturado em `output/<base>/quality-<uuid>.json`, preservando nele o detalhe por chunk, sem alterar `manifest.json` e sem registrar credenciais, tokens ou URLs de destino em qualquer das duas saídas.
- **FR-005**: O sistema deve expor a mesma avaliação como comando próprio de diagnóstico sobre um arquivo de chunks já gerado, sem abrir conexão com o vector store, retornando 0 quando aprovado, 1 quando reprovado e 2 quando não foi possível avaliar. Nesse modo não há manifesto, então o invariante de contagem é pulado e o relatório declara que foi pulado por ausência de manifesto; os outros cinco invariantes continuam sendo avaliados. A avaliação embutida também roda no modo `--only-chunks` do pipeline, onde o manifesto já existe e o invariante de contagem é avaliado normalmente.

#### Não funcionais

- **NFR-001**: A avaliação é leitura pura sobre o conjunto local: nenhuma escrita no vector store, nenhuma conexão remota e nenhum comando destrutivo, tanto no modo embutido quanto no comando de diagnóstico. **Verificação**: teste estático de AST confirmando ausência de import de SDK de banco vetorial no módulo, somado a caso que executa o diagnóstico com um dublê que falha se qualquer operação de escrita for chamada.
- **NFR-002**: Relatório legível e resultado estruturado não contêm credenciais, tokens nem URLs de destino, e os trechos de conteúdo citados limitam-se ao necessário para identificar o defeito. **Verificação**: caso que executa o gate com uma configuração contendo chave e URL fictícias e varre as duas saídas em busca desses valores.
- **NFR-003**: Nenhum limiar, mensagem, exemplo ou nome de arquivo do módulo carrega identidade, produto ou domínio de cliente; cada limiar aplicado vem da configuração da base. **Verificação**: guarda estática no padrão de `tests/test_client_neutrality.py`, estendida ao módulo de qualidade e à sua CLI.

#### Erros e casos-limite

- Arquivo de chunks ausente, ilegível ou malformado no comando de diagnóstico → informar a impossibilidade de avaliar, retornar 2 e não indexar.
- `config.yaml` sem o mínimo declarado → aplicar o padrão de 60 caracteres e registrar no relatório que o padrão foi usado.
- Documento sem `chunk_size` efetivo determinável → registrar a impossibilidade de derivar o máximo daquele documento e seguir avaliando os demais sinais.
- Falha ao gravar o resultado estruturado → preservar o relatório legível no stdout, informar a falha de escrita e não mascarar o desfecho da avaliação.
- Manifesto ausente no comando de diagnóstico → pular o invariante de contagem, declarar no relatório que ele foi pulado e avaliar os cinco invariantes restantes; a ausência de manifesto não é, por si, motivo de reprovação nem de código 2.
- Conjunto vazio → é o primeiro invariante crítico; interrompe antes de qualquer outro cálculo.
- Chunk sem `secao` e sem `subsecao` em documento que legitimamente só usa H1 → contabilizado na proporção por documento, sem veredito automático de defeito, conforme o limite de escopo que exclui severidade calculada.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Python 3.12 com `uv`, LangChain v1, Pytest e Ruff. Nenhuma dependência nova é necessária nesta fatia.
- `src/` contém módulos planos e focados: `chunker`, `identity`, `manifest`, `loader`, `indexing`, `safety`, `status_gate`, `validation`, `exporter`, `config`, e o pacote `providers/`.
- `pipeline.py` orquestra carregamento, filtro por status, chunking, exportação, manifesto e indexação, nessa ordem. O manifesto é construído e validado em `pipeline.py:118-125`, imediatamente antes do desvio de `--only-chunks` e da indexação.
- `validate.py` estabelece o padrão de CLI de diagnóstico: `parse_args`, `load_config`, chamada a um módulo de `src/`, `report.render()` no stdout, caminho do resultado estruturado e `sys.exit(exit_code(report))`.
- `src/validation.py` estabelece o padrão de objeto de relatório com `render()` e desfecho estruturado.
- Imports de SDK de banco vetorial são confinados a `src/providers/` por regra verificada em `tests/test_provider_boundaries.py`. O módulo de qualidade não importa nenhum deles.

#### Arquitetura e módulos

- **`src/quality.py`** — módulo novo, responsável por toda a avaliação. Exporta a fronteira usada pelo pipeline e pela CLI. Componentes:
  - `CriticalInvariant`: interface de uma regra determinística que recebe o conjunto e devolve a violação encontrada ou nada. Uma implementação por invariante de FR-001, no padrão Strategy exigido por PR-006.
  - `QualitySignal`: interface de um sinal, que recebe o conjunto e devolve ocorrências agrupáveis por documento. Uma implementação por sinal de FR-002.
  - `SizeThresholds`: encapsula a derivação do máximo por documento e o mínimo configurado sobre conteúdo útil (FR-003). Concentra o desconto do breadcrumb.
  - `QualityReport`: agrega desfecho, violação crítica quando houver, sinais agrupados por documento e detalhe por chunk. Expõe `render()` para o relatório legível e a serialização do resultado estruturado.
  - `QualityGateError`: exceção levantada quando um invariante crítico falha, no mesmo espírito de `ManifestValidationError`.
  - `evaluate_quality(chunks, chunking_cfg, quality_cfg) -> QualityReport`: fronteira única de avaliação.
- **`quality.py`** na raiz — CLI de diagnóstico, espelhando `validate.py`: lê `--config` e o caminho do arquivo de chunks, chama `evaluate_quality`, imprime `report.render()`, informa o caminho do resultado estruturado e retorna 0, 1 ou 2.
- **`pipeline.py`** — chamada a `evaluate_quality` logo após `build_manifest`, antes do desvio de `--only-chunks`, de modo que a avaliação também ocorra nesse modo (FR-005). `QualityGateError` interrompe a execução antes da etapa de indexação.
- **`config.yaml` e `config.example.yaml`** — nova seção `qualidade`, com o mínimo de conteúdo útil e a margem do breadcrumb, ambos com padrão documentado.

O gate não substitui `src/manifest.py`. O manifesto continua validando identidade e contagem no seu escopo; o módulo de qualidade avalia o conjunto de chunks e concentra os dois níveis. A sobreposição entre os quatro invariantes já existentes no manifesto e os de FR-001 é deliberada e resolvida na implementação: o gate é o ponto único de decisão, e a validação do manifesto permanece como rede de segurança da própria construção do manifesto.

#### Migrations

- Não aplicável. Este componente não possui schema relacional próprio, conforme `.specsfy/RULES.md`.

#### Models

- Não aplicável no sentido de ORM. As estruturas de dados desta fatia são objetos de valor em memória, descritos na seção 9.

#### Controllers e casos de uso

- `evaluate_quality` em `src/quality.py`: entrada é a lista de chunks, a configuração de chunking e a de qualidade; saída é `QualityReport`; sem autorização aplicável, por ser componente CLI local.
- `main` em `quality.py`: entrada são os argumentos de linha de comando; saída é o relatório no stdout e o código de saída.
- Bloco de avaliação em `pipeline.py`: entrada é o conjunto recém-gerado; efeito é interromper antes da indexação ou seguir publicando o relatório.

#### Views e experiência

- Não aplicável. A superfície é CLI, sem interface gráfica neste repositório.

#### Queries e repositórios

- Não aplicável. Nenhuma consulta a banco vetorial ou relacional ocorre nesta fatia.

#### Jobs e processamento assíncrono

- Não aplicável. A avaliação é síncrona e local.

#### Estrutura de arquivos

```text
specs/draft/0006-gate-qualidade-chunks-metadados/
  spec.md
  research/
src/
  quality.py
quality.py
pipeline.py
config.yaml
config.example.yaml
tests/
  test_quality_gate.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `QualityReport` | `run_id` (UUID da execução) | `desfecho` em `aprovado` ou `reprovado`; `impedimento` com o invariante violado ou nulo; `sinais` agrupados por documento; `detalhe_por_chunk`; `limiares_aplicados`; `gerado_em` | agrega muitos `DocumentSummary` e muitas `ChunkFinding` |
| `DocumentSummary` | `caminho_relativo` | `chunks`, `sem_secao`, `sem_subsecao`, contagem por sinal, distribuição de tamanho por `chunk_type` | pertence a um `QualityReport` |
| `ChunkFinding` | `chunk_id` | `sinal`, `documento`, `medida observada`, `limiar aplicado` quando houver | pertence a um `DocumentSummary` |
| `CriticalViolation` | `invariante` | `descrição`, `chunk_id` quando aplicável, `documento` quando aplicável | no máximo uma por `QualityReport` |
| `SizeThresholds` | derivado por documento | `minimo_util` da configuração; `maximo_derivado` = `chunk_size` efetivo + margem do breadcrumb | consultado por `ChunkFinding` |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| `QualityReport` | em avaliação | invariante crítico viola | `reprovado` | `impedimento` preenchido; nenhuma escrita ocorreu no destino |
| `QualityReport` | em avaliação | todos os invariantes passam | `aprovado` | `impedimento` nulo; sinais podem existir sem alterar o desfecho |
| `QualityReport` | `aprovado` | gravação do resultado falha | `aprovado` | desfecho preservado; falha de escrita informada; relatório legível apresentado |
| Execução do pipeline | chunks gerados | `QualityGateError` | interrompida | indexação não iniciada |
| Execução do pipeline | chunks gerados | avaliação aprovada | indexação | relatório publicado antes da escrita |

#### Migração e retenção

- O resultado estruturado é artefato de execução em `output/<base>/`, como o manifesto e a validação, e segue a mesma retenção do diretório de saída da base. Esta fatia não acumula histórico entre execuções e não introduz persistência nova, motivo pelo qual `$specsfy-data-discovery` não foi acionado.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. Este repositório não possui frontend, conforme `docs/frontend.md` e `INTERFACE.md`. A entrega é consumida por linha de comando pelo operador e pelo mantenedor. A demonstração gráfica do pipeline pertence ao projeto-mãe `rag-pipeline`, por decisão registrada no BACKLOG-0008.

#### Stack e convenções de interface

- Não aplicável. Não há camada de interface neste repositório: nenhum framework de front, roteamento, componente ou folha de estilo consta de `pyproject.toml` ou do código. A convenção de saída é textual, definida pelo padrão de `render()` estabelecido em `src/validation.py`.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável. O fluxo é de comando e saída textual, descrito em `APIs expostas`.

#### Menus e navegação principal

- Não aplicável. Não há menu; os dois pontos de acesso são o `pipeline.py`, que executa a avaliação como parte do fluxo, e o `quality.py`, invocado diretamente.

#### Formulários e ações

- Não aplicável. A entrada é composta por argumentos de linha de comando e pelo `config.yaml`.

#### Composição e disposição

- O relatório legível segue a composição do relatório da SPEC-0004: cabeçalho com desfecho e escopo, seção do impedimento quando houver, e seção de sinais agrupada por documento, com uma linha por documento e as contagens por sinal.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável |

- Não aplicável: o repositório não usa React, Tailwind, shadcn/ui nem ReUI, e esta fatia não introduz nenhum deles.

#### Estados e acessibilidade

- Os estados observáveis são textuais: avaliação aprovada, avaliação reprovada com impedimento nomeado, e impossibilidade de avaliar. Cada um corresponde a um código de saída distinto, o que torna os três discrimináveis por script e por pessoa.
- A saída não comunica resultado apenas por cor ou símbolo; cada estado é nomeado por extenso no texto.

#### Contrato CRUD

- Não aplicável. A fatia não administra registros e não expõe listagem, detalhe, criação ou edição.

#### Revisão visual durante o desenvolvimento

- O item `VISUAL` de cada tarefa é registrado como `Não aplicável`, com o motivo concreto: a entrega não possui superfície visual, apenas saída textual em terminal. A conferência aplicável no lugar é a legibilidade do relatório, verificada pelos casos que exercitam `render()`.

#### APIs expostas

- **Comando**: `uv run python quality.py [--config config.yaml] [--chunks <caminho>]`. Sem autenticação, por ser ferramenta local. Entrada: configuração e arquivo de chunks; quando `--chunks` for omitido, usa `caminhos.chunks_file` da configuração. Saída: relatório legível no stdout, caminho do resultado estruturado e código de saída 0, 1 ou 2. Erros: configuração inválida, arquivo ausente ou malformado retornam 2 com mensagem sem segredo.
- **Fronteira Python**: `evaluate_quality(chunks, chunking_cfg, quality_cfg) -> QualityReport` em `src/quality.py`, consumida por `pipeline.py` e por `quality.py`. Versionamento interno; nenhum contrato externo é publicado por esta fatia.

#### APIs externas utilizadas

- Nenhuma. A avaliação é local e não abre conexão de rede, conforme NFR-001.

#### Documentação das APIs consultadas

- Não aplicável. Nenhuma API externa foi consultada para esta fatia.

#### Eventos e outros contratos

- **Contrato do resultado estruturado**: `output/<base>/quality-<uuid>.json`, com `run_id`, `gerado_em`, `desfecho`, `impedimento`, `limiares_aplicados`, `documentos` e `chunks`. Produtor: o gate. Consumidor previsto: o mantenedor e, futuramente, o backend do projeto-mãe. Compatibilidade: aditiva; campos novos podem ser acrescentados sem remover os existentes.
- **Contrato preservado**: `manifest.json` mantém exatamente os campos atuais. Nenhum campo é acrescentado, removido ou renomeado por esta fatia.

### 11. Estratégia TDD

- **Unidade**: cada invariante de FR-001 e cada sinal de FR-002 isoladamente, sobre conjuntos sintéticos construídos com o defeito específico; derivação de limiares de FR-003.
- **Integração/contrato**: a fronteira `evaluate_quality` chamada por `pipeline.py`, verificando que a interrupção ocorre antes da etapa de indexação; a CLI `quality.py` verificando relatório, gravação e código de saída.
- **BDD/aceite**: os quinze cenários Gherkin da seção 6 são o contrato de referência que orienta o desenho dos casos TDD. Nenhum arquivo `.feature` é criado ou executado.
- **Runner TDD**: Pytest, runner já adotado pelo repositório. `uv run pytest`.
- **E2E**: não aplicável. A jornada completa com destino remoto é coberta pela SPEC-0004 e não é reexecutada aqui.
- **Verificação manual**: nenhuma. Todos os cenários são automatizáveis com conjuntos sintéticos e dublês.

Os casos desta fatia ficam concentrados em `tests/test_quality_gate.py`. Essa concentração é a mitigação vigente para a limitação de rastreabilidade registrada em `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md`: como os marcadores `SPECSFY:` não declaram a spec de origem e os IDs se repetem entre fatias, isolar a fatia em arquivo próprio evita que a contagem de cobertura misture specs.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, NFR-001, AC-001 | AC-001 na seção 6 | caso de chunk sem `chunk_id` em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-001, FR-001, AC-002 | AC-002 na seção 6 | caso de `chunk_id` duplicado em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-001, FR-001, AC-003 | AC-003 na seção 6 | caso de chunk só com breadcrumb em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-001, FR-001, AC-004 | AC-004 na seção 6 | caso de metadado de rastreabilidade ausente em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-001, FR-002, NFR-001, AC-005 | AC-005 na seção 6 | caso de truncamento que não bloqueia em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-002, FR-002, AC-006 | AC-006 na seção 6 | caso de duplicata exata relatada em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-002, FR-003, NFR-003, AC-007 | AC-007 na seção 6 | caso de mínimo sobre conteúdo útil em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-002, FR-003, AC-008 | AC-008 na seção 6 | caso de máximo derivado do frontmatter em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-002, FR-002, FR-004, NFR-003, AC-009 | AC-009 na seção 6 | caso de agrupamento por documento em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-002, FR-004, NFR-002, AC-010 | AC-010 na seção 6 | caso de arquivo próprio e manifesto intacto em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-003, FR-005, NFR-001, AC-011 | AC-011 na seção 6 | caso de diagnóstico isolado com dublê que falha em escrita em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-003, FR-005, AC-012 | AC-012 na seção 6 | caso dos três códigos de saída em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| FR-004, NFR-002, AC-013 | AC-013 na seção 6 | caso de varredura de segredo nas duas saídas em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| FR-003, NFR-003, AC-014 | AC-014 na seção 6 | guarda estática de neutralidade em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-003, FR-004, FR-005, NFR-002, AC-015 | AC-015 na seção 6 | caso de falha de gravação em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |
| US-003, FR-001, FR-005, AC-016 | AC-016 na seção 6 | caso de diagnóstico sem manifesto em `tests/test_quality_gate.py` | Observado em 2026-09-03 | GREEN em 2026-09-03 | `uv run pytest` → 216 passed |

### 12. Plano de testes e rastreabilidade

Regressão completa da fatia: `uv run pytest`. Verificação estática: `uv run ruff check`.

| Requisito | Cenário BDD | Nível | Arquivo e comando focal | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-001 | AC-002 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-001 | AC-003 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-001 | AC-004 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-002 | AC-005 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-002 | AC-006 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-002 | AC-009 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-003 | AC-007 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-003 | AC-008 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-003 | AC-014 | Estático | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-004 | AC-009 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-004 | AC-010 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-004 | AC-013 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-004 | AC-015 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-005 | AC-011 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-005 | AC-012 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-005 | AC-015 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| NFR-001 | AC-001 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| NFR-001 | AC-005 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| NFR-001 | AC-011 | Estático e integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| NFR-002 | AC-010 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| NFR-002 | AC-013 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| NFR-002 | AC-015 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| NFR-003 | AC-007 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| NFR-003 | AC-009 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| NFR-003 | AC-014 | Estático | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-001 | AC-016 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |
| FR-005 | AC-016 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY — 2026-09-03. A primeira passagem retornou `NOT READY` com dois `P1`; os seis achados foram corrigidos nas seções de origem e reavaliados.
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0006-gate-qualidade-chunks-metadados/spec.md --allow-draft` → `VALID DRAFT`
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/review_findings.mjs --spec specs/draft/0006-gate-qualidade-chunks-metadados/spec.md --root .` → `Reviews: FAILED`, com `FIND-ARCH-001` e `FIND-PROD-001` bloqueantes
- **Estrutura**: `VALID DRAFT`. Formato `Specsfy/2.0`, três atos na ordem, slug igual ao diretório, pacote restrito a `spec.md`.
- **Cobertura**: 3 `US`, 5 `FR`, 3 `NFR`, 15 `AC`. Todos os onze `US`/`FR`/`NFR` alcançam ao menos três `AC` distintos declarados em `**Cobre**`; nenhum `AC` referencia ID inexistente. A tabela RED-GREEN-REFACTOR prevê 15 casos TDD e repete a mesma cobertura mínima.
- **Achados**: seis registrados, todos `Resolved`. Nenhum `P1` aberto.

- **FIND-ARCH-001** [P1] [Resolved] `FR-001` inclui como invariante crítico a contagem do manifesto inconsistente com o número de chunks, mas `FR-005` define o comando de diagnóstico operando sobre um arquivo de chunks já gerado, sem manifesto disponível — Refs: FR-001, FR-005, AC-012 — Evidence: specs/completed/0006-gate-qualidade-chunks-metadados/spec.md:440 — Effect: a linha 418 da mesma spec declara `FR-005`; o comportamento do invariante no modo de diagnóstico é indefinido; a spec não diz se ele é pulado, se torna a avaliação impossível com código 2 ou se o comando passa a exigir o manifesto, e nem `AC-012` nem a lista de erros da seção 7 cobrem a condição — Suggestion: decidir o alcance do invariante de manifesto e refletir a decisão em `FR-001`, `FR-005`, em um `AC` próprio e na lista de erros e casos-limite — Status: Resolvido em 2026-09-03: `FR-001` passou a condicionar o invariante de contagem à disponibilidade do manifesto, `FR-005` declara o salto no comando de diagnóstico, `AC-016` cobre o comportamento, a lista de erros da seção 7 trata a condição e `DEC-009` registra a decisão e as alternativas

- **FIND-PROD-001** [P1] [Resolved] A Definition of Done preserva o checklist genérico do template e não é provável por comando nem evidência objetiva desta fatia — Refs: FR-005, NFR-003 — Evidence: .specsfy/STACK.md:19 — Effect: a seção 18 da spec e o `PROJECT.md` completam a evidência; `.specsfy/STACK.md` inventaria a interface operacional como `pipeline.py`, `search.py` e `chat.py` e a fatia acrescenta `quality.py`; `PROJECT.md` lista as capacidades do componente e a fatia acrescenta bloquear indexação por invariante e diagnosticar a preparação; nenhum item da DoD prova as métricas de sucesso da seção 1 — Suggestion: reescrever a seção 18 com itens específicos e verificáveis, citando a atualização de `.specsfy/STACK.md` e a revisão de `PROJECT.md` — Status: Resolvido em 2026-09-03: a seção 18 foi reescrita com vinte itens verificáveis, citando a atualização de `.specsfy/STACK.md`, a revisão de `PROJECT.md` e as métricas de sucesso da seção 1

- **FIND-PROD-002** [P2] [Resolved] `AC-012` encadeia três pares `When`/`Then` em um único `Scenario`, misturando os três códigos de saída — Refs: AC-012, FR-005 — Evidence: specs/completed/0006-gate-qualidade-chunks-metadados/spec.md:353 — Effect: dificulta observar um RED por comportamento e contraria o critério de cenário com `Given`, `When` e `Then` observáveis — Suggestion: converter em `Scenario Outline` com `Examples` ou dividir em três cenários — Status: Resolvido em 2026-09-03: `AC-012` virou `Scenario Outline` com um `Examples` por código de saída

- **FIND-PROD-003** [P2] [Resolved] O último `And` de `AC-004` generaliza o tratamento para `source_hash`, `project_id`, `chunk_hash` e `chunk_type` em vez de declarar um resultado observável — Refs: AC-004, FR-001 — Evidence: specs/completed/0006-gate-qualidade-chunks-metadados/spec.md:217 — Effect: quatro dos cinco metadados obrigatórios ficam sem cenário executável — Suggestion: converter em `Scenario Outline` com um `Examples` por metadado obrigatório — Status: Resolvido em 2026-09-03: `AC-004` virou `Scenario Outline` com um `Examples` por metadado obrigatório

- **FIND-PROD-004** [P2] [Resolved] A coluna `Arquivo/comando esperado` da matriz traz apenas o caminho do arquivo de teste, sem o comando executável — Refs: FR-001, FR-002, FR-003, FR-004, FR-005 — Evidence: specs/completed/0006-gate-qualidade-chunks-metadados/spec.md:659 — Effect: a matriz não liga requisito, cenário, nível, comando e evidência como o gate de verificação exige — Suggestion: registrar o comando focal `uv run pytest tests/test_quality_gate.py` e o seletor do caso onde couber — Status: Resolvido em 2026-09-03: a matriz da seção 12 passou a trazer o comando focal por linha, mais os comandos de regressão e verificação estática

- **FIND-PROD-005** [P3] [Resolved] O `Effort` foi recalibrado de 1 para 6 na promoção, mas a spec não traz a seção `Effort history` mantida pelas fatias anteriores — Refs: US-001 — Evidence: specs/completed/0005-remover-hardcodes-cliente/spec.md — Effect: a recalibração perde rastreabilidade e diverge da convenção local do repositório — Suggestion: acrescentar a seção `Effort history` com o registro datado da recalibração — Status: Resolvido em 2026-09-03: a seção `Effort history` foi acrescentada com o registro datado de 1 → 6
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`, severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: READY — 2026-09-03
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0006-gate-qualidade-chunks-metadados/spec.md` → `total=26 complete=16 tdd=17 code=8 checklist_items=156 checklist_complete=96 covered_spec_ids=27 required_spec_ids=27`
- **Comando**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. RED válido em todas as dezesseis tarefas TDD, com os 194 casos existentes preservados.
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0006-gate-qualidade-chunks-metadados/spec.md .` → `27/27 IDs cobertos em 20 arquivos de teste`.
- **Achados**: nenhum bloqueio. Uma correção durante o planejamento: T019 foi reprovada por ter apenas dois predecessores TDD rastreáveis, e recebeu T014 como terceiro, coerente porque é T019 que passa a ler os limiares da configuração em vez do código.
- **Achado não bloqueante**: o auditor de rastreabilidade também reporta `MARCADORES ÓRFÃOS` — nove cenários de aceite, três requisitos funcionais, um não funcional e duas histórias, todos numerados acima do conjunto desta fatia. Eles pertencem a `tests/test_chunker.py`, `tests/test_safety.py`, `tests/test_qdrant_sync.py`, `tests/test_embedding_conformance.py` e `tests/test_vectorstore_conformance.py`, arquivos das três primeiras specs do repositório. O auditor varre os vinte arquivos de teste contra o conjunto de identificadores desta spec, e os marcadores não declaram a spec de origem. A quinta spec, `Complete` com Delivery Gate aprovado, produz a mesma lista pelo mesmo motivo. Limitação registrada em `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md`; a mitigação vigente é o arquivo de teste próprio por fatia.
- **Nota de ferramental**: os localizadores em `Evidence` citam a spec pela pasta de estado atual. `review_findings.mjs` exige caminho local existente, então cada transição de pasta invalida esses localizadores e eles precisam ser reapontados junto com a movimentação.
- **Nota de ferramental**: os identificadores órfãos não são citados aqui em forma literal de propósito. O extrator de `validate_spec.mjs` casa qualquer ocorrência de `US`, `FR`, `NFR` ou `AC` seguida de número em qualquer ponto do corpo, inclusive dentro de prosa, e passaria a cobrar cenários de aceite para requisitos que esta spec não declara.

#### Gate do Ato III — Entrega

- **Resultado**: PASSED — 2026-09-03, com uma pendência externa declarada.
- **Comando**: `uv run pytest` → `221 passed`.
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/completed/0006-gate-qualidade-chunks-metadados/spec.md` → `total=26 complete=26 checklist_items=156 checklist_complete=156 covered_spec_ids=27 required_spec_ids=27`, `READY`.
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/completed/0006-gate-qualidade-chunks-metadados/spec.md .` → `27/27 IDs cobertos em 20 arquivos de teste`.
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/completed/0006-gate-qualidade-chunks-metadados/spec.md .` → `QA: PASSED`, com os dezesseis cenários de aceite com resultado registrado na seção 12.
- **Comando**: `node .claude/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`; `build_documentation.mjs --check` → saída 0.
- **Comando**: `uv run ruff check .` → `error: Failed to spawn: ruff`. Não executou.
- **Pendência externa aceita**: o item da Definition of Done que exige `uv run ruff check` sem achado novo permanece aberto. O Ruff é gate confirmado por `.specsfy/RULES.md`, mas não está instalado no ambiente; `docs/testing.md` registra a lacuna desde a SPEC-0004 e o BACKLOG-0007 é o responsável por instalá-lo e criar a esteira de integração contínua. Nenhuma ação desta fatia poderia fechar o item sem invadir aquele escopo e sem contradizer o item vizinho, que exige nenhuma dependência nova em `pyproject.toml`. Os outros dezenove itens estão comprovados. A aceitação desta pendência foi decidida explicitamente pela pessoa responsável em 2026-09-03.
- **Achados do fechamento**: a conferência item a item da Definition of Done expôs três lacunas de cobertura que os gates anteriores não pegaram — `FR-001` enumera seis invariantes críticos e a seção 6 cobria quatro; `FR-002` enumera seis sinais e havia caso para cinco; o cenário `AC-010` provava a ausência de `manifest.json` no diretório de saída, não a preservação da sua estrutura. Cinco casos foram acrescentados a `tests/test_quality_gate.py`, que passou de 22 para 27, e a suíte total de 216 para 221. A causa comum foi não conferir a cobertura item a item quando um requisito enumera vários itens; a regra corretiva está registrada no `IMPROVE` de T026.
- **Achado não bloqueante**: o auditor de rastreabilidade reporta marcadores órfãos pertencentes às três primeiras specs do repositório, pelo mesmo motivo já registrado no Gate do Ato II. A quinta spec, concluída, reproduz o comportamento.

##### Aceite final — 2026-09-03

- **Resultado**: `READY`. Formato `Specsfy/2.0`, três atos na ordem, slug igual ao diretório, pacote restrito a `spec.md` e nenhum `research/`, coerente com a declaração de que a fatia não consultou fonte externa.
- **Cobertura**: 3 `US`, 5 `FR`, 3 `NFR`, 16 `AC`, 9 `DEC`, 7 `PR`; todos os onze requisitos com ao menos três cenários de aceite. 26 tarefas concluídas, 156 itens de checklist, 27 de 27 identificadores cobertos, `QA: PASSED`, `uv run pytest` com 221 casos verdes.
- **Achado corrigido no aceite, severidade WARNING**: `evaluate_quality` avaliava cada sinal duas vezes — uma por `ocorrencias`, para a contagem, e outra por `chunks_afetados`, para o detalhe por chunk — e recalculava `sem_secao` por documento com a mesma regra já implementada por `PerdaDeEstrutura`. Duas fontes para o mesmo número podem divergir em qualquer mudança futura de heurística. A avaliação passou a ocorrer uma única vez, com contagem e detalhe derivados do mesmo resultado, e `sem_secao` passou a ler o sinal em vez de recontar. Refatoração sem mudança de comportamento: 221 casos verdes antes e depois, e a execução sobre a base de referência devolve as mesmas contagens.
- **Achado corrigido no aceite, severidade NOTE**: o parâmetro `output_dir` de `evaluate_quality` era o único sem anotação de tipo; passou a declarar `Path | str | None`.
- **Achado registrado, severidade NOTE**: `quality.py` importa `src.config`, que executa `load_dotenv()` no import e injeta o `.env` inteiro no processo. A CLI de diagnóstico não usa credencial alguma, então não há efeito observável nesta fatia, mas o acoplamento é o mesmo descrito em `specs/inbox/2026-09-02-195708-carregar-o-env-nos-entrypoints-em-vez-do-import-de-config.md`, ainda não promovido. Fora do escopo desta entrega.
- **Pendência externa mantida**: o item da Definition of Done que exige `uv run ruff check` continua aberto, com a justificativa registrada acima. O aceite reconhece a fatia como completa porque nenhuma ação dentro do seu escopo poderia fechá-lo; a responsabilidade permanece no BACKLOG-0007, que também é o dono da esteira de integração contínua.
- **Veredito**: nenhum `BLOCKER`. A fatia entrega o comportamento especificado, com evidência executável para cada requisito, e é aceita.

### 14. Tarefas

Formato:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Checklist obrigatório por tarefa, na ordem:

```markdown
  - [ ] **PREP**: Confirmar escopo, IDs, dependências e baseline.
  - [ ] **EXECUTE**: Produzir a entrega no caminho declarado.
  - [ ] **VERIFY**: Executar a verificação focal adequada.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do sistema; se não houver interface, registrar `Não aplicável` e o motivo.
  - [ ] **EVIDENCE**: Registrar comando, resultado e IDs nas seções 11–13.
  - [ ] **IMPROVE**: Registrar melhoria aplicada ou ausência justificada.
```

Runner: Pytest, já adotado pelo repositório. Comando focal de toda tarefa desta
seção: `uv run pytest tests/test_quality_gate.py`. Regressão: `uv run pytest`.
Todos os casos ficam em `tests/test_quality_gate.py`, isolando a fatia conforme
a mitigação registrada na seção 11.

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-001, FR-001, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-001 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que um chunk sem `chunk_id` interrompe a avaliação antes de qualquer escrita, com o marcador `# SPECSFY: US-001 FR-001 NFR-001 AC-001`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-001, FR-001, AC-002 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-002 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que dois chunks com o mesmo `chunk_id` interrompem a avaliação, com o marcador `# SPECSFY: US-001 FR-001 AC-002`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-001, FR-001, AC-003 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-003 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que um chunk cujo `page_content` é apenas o breadcrumb interrompe a avaliação, com o marcador `# SPECSFY: US-001 FR-001 AC-003`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-001, FR-001, AC-004 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-004 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que a ausência de cada metadado obrigatório interrompe a avaliação, parametrizado nos cinco casos do `Examples`, com o marcador `# SPECSFY: US-001 FR-001 AC-004`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 5 casos parametrizados em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-001, FR-002, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-005 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que um conjunto íntegro com chunks truncados prossegue para a indexação, com o marcador `# SPECSFY: US-001 FR-002 NFR-001 AC-005`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-002, FR-002, AC-006 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-006 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que conteúdo duplicado com `chunk_id` distintos não interrompe a avaliação, com o marcador `# SPECSFY: US-002 FR-002 AC-006`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-002, FR-003, NFR-003, AC-007 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-007 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que o mínimo é medido sobre o conteúdo útil, descontado o breadcrumb, com o marcador `# SPECSFY: US-002 FR-003 NFR-003 AC-007`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-002, FR-003, AC-008 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-008 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que o máximo deriva do `chunk_size` declarado pelo frontmatter do documento, com o marcador `# SPECSFY: US-002 FR-003 AC-008`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-002, FR-002, FR-004, NFR-003, AC-009 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-009 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que o relatório agrupa os sinais por documento de origem, com o marcador `# SPECSFY: US-002 FR-002 FR-004 NFR-003 AC-009`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T010 [TEST] [TDD] [US-002] Derivar do AC-010 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-002, FR-004, NFR-002, AC-010 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-010 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que o resultado estruturado é gravado em arquivo próprio da execução, com o marcador `# SPECSFY: US-002 FR-004 NFR-002 AC-010`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-003, FR-005, NFR-001, AC-011 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-011 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que o comando de diagnóstico avalia sem abrir conexão com o vector store, com o marcador `# SPECSFY: US-003 FR-005 NFR-001 AC-011`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-003, FR-005, AC-012 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-012 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que os três códigos de saída são distinguidos, parametrizado nos casos do `Examples`, com o marcador `# SPECSFY: US-003 FR-005 AC-012`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 3 casos parametrizados em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'quality'` — a CLI de diagnóstico ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T013 [TEST] [TDD] Derivar do AC-013 um caso Pytest falhando em tests/test_quality_gate.py — Refs: FR-004, NFR-002, AC-013 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-013 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que credencial e URL de destino não aparecem no relatório nem no resultado estruturado, com o marcador `# SPECSFY: FR-004 NFR-002 AC-013`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T014 [TEST] [TDD] Derivar do AC-014 um caso Pytest falhando em tests/test_quality_gate.py — Refs: FR-003, NFR-003, AC-014 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-014 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que nenhum identificador de cliente aparece em `src/quality.py` e `quality.py`, com o marcador `# SPECSFY: FR-003 NFR-003 AC-014`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `AssertionError: arquivo ausente: src/quality.py` — a guarda estática não encontra o módulo.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T015 [TEST] [TDD] [US-003] Derivar do AC-015 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-003, FR-004, FR-005, NFR-002, AC-015 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-015 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que uma falha de gravação preserva o relatório legível e informa o erro, com o marcador `# SPECSFY: US-003 FR-004 FR-005 NFR-002 AC-015`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

- [x] T016 [TEST] [TDD] [US-003] Derivar do AC-016 um caso Pytest falhando em tests/test_quality_gate.py — Refs: US-003, FR-001, FR-005, AC-016 — Depends: none
  - [x] **PREP**: Concluído. Lido o Gherkin de AC-016 na seção 6 e confirmar a regra, os IDs cobertos e o nível de teste.
  - [x] **EXECUTE**: Concluído. Escrito o caso que verifica que o invariante de contagem é pulado quando não há manifesto, com o marcador `# SPECSFY: US-003 FR-001 FR-005 AC-016`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: RED válido observado: 1 caso em `tests/test_quality_gate.py`, falhando por `ModuleNotFoundError: No module named 'src.quality'` — o módulo ainda não existe.
  - [x] **VISUAL**: Não aplicável — a tarefa só materializa teste automatizado, sem superfície visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_quality_gate.py` → 22 failed; `uv run pytest` → 22 failed, 194 passed. Linha correspondente atualizada na tabela da seção 11.
  - [x] **IMPROVE**: Aplicada: o import do módulo em construção é tardio, dentro de `_quality()` e `_cli()`, para que a ausência do módulo não quebre a coleta e apague o sinal de regressão dos 194 casos existentes.

#### Fase 2 — US-001 — Impedir que um conjunto inválido alcance o vector store (P1)

**Objetivo**: nenhuma carga que viole um invariante de integridade alcança o destino remoto.
**Teste independente**: `uv run pytest tests/test_quality_gate.py` com os casos de T001 a T004 e T016 verdes, e o pipeline interrompido antes da indexação.

- [x] T017 [CODE] [US-001] Implementar os seis invariantes críticos e `QualityGateError` em src/quality.py — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-016 — Depends: T001, T002, T003, T004, T016
  - [x] **PREP**: Concluído. RED de T001 a T004 e T016 confirmado (9 casos vermelhos por `ModuleNotFoundError: No module named 'src.quality'`); `FR-001` e `DEC-009` relidos.
  - [x] **EXECUTE**: Concluído. Criado `src/quality.py` com `CriticalInvariant` como Strategy, seis implementações — `conjunto_nao_vazio`, `chunk_id_presente`, `chunk_id_unico`, `contagem_do_manifesto`, `conteudo_alem_do_breadcrumb` e `metadados_de_rastreabilidade` —, `QualityGateError`, o helper `conteudo_util` e `evaluate_quality`. O invariante de contagem declara `exige_manifesto` e é pulado com aviso quando o manifesto é `None`.
  - [x] **VERIFY**: `uv run pytest tests/test_quality_gate.py` → 13 failed, 9 passed. Os 9 verdes são exatamente os alvos desta tarefa: AC-001, AC-002, AC-003, os cinco casos parametrizados de AC-004 e AC-016. `uv run pytest` → 13 failed, 203 passed.
  - [x] **VISUAL**: Não aplicável — o módulo não possui superfície visual e nesta tarefa nem produz saída legível; a conferência de legibilidade do relatório chega em T021.
  - [x] **EVIDENCE**: Registrado. `build_documentation.mjs --check` → exit 0; `monitor_context.mjs --check` → `CURRENT`. `PROJECT.md` revisado sem impacto material: o módulo existe mas nenhum caminho de execução o invoca ainda, então não há capacidade observável pelo operador nesta tarefa; a integração e a revisão narrativa pertencem a T018. Monitor repetido com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: Aplicada: `conteudo_util` nasceu como função pública do módulo em vez de detalhe de `SizeThresholds`, porque o invariante de conteúdo vazio e o sinal de conteúdo curto medem a mesma coisa; evita a duplicação que apareceria em T019. Achado registrado para o relato: `uv run ruff check` falha com `Failed to spawn: ruff` — o gate está confirmado em `.specsfy/RULES.md` mas não instalado, lacuna que `docs/testing.md` já atribui ao BACKLOG-0007.
  <!-- specsfy:evidence {"task": "T017", "refs": ["US-001", "FR-001", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-016"], "files": ["src/quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

- [x] T018 [CODE] [US-001] Integrar o bloqueio do gate em pipeline.py entre o manifesto e a indexação — Refs: US-001, FR-001, FR-005, NFR-001, AC-005 — Depends: T005, T017, T020
  - [x] **PREP**: Concluído. RED de T005 confirmado e GREEN de T017 e T020 conferido; ponto de chamada em `pipeline.py` relido após `build_manifest` e `export_manifest`.
  - [x] **EXECUTE**: Concluído. `evaluate_quality` é chamado em `pipeline.py` como etapa 4 de 5, depois do manifesto e antes do desvio de `--only-chunks`, recebendo o manifesto e o diretório de saída derivado de `chunks_file`. `QualityGateError` é convertido em `SystemExit(1)` com mensagem que nomeia o invariante e declara que nada foi escrito no destino. As contagens por sinal e os avisos vão para o log estruturado, sem segredo, conforme a regra de operação do projeto.
  - [x] **VERIFY**: `uv run pytest` → 9 failed, 207 passed, sem regressão. Execução real `uv run python pipeline.py --only-chunks` sobre a base de referência: a etapa 4 de 5 aparece antes do desvio e reporta os cinco sinais com as contagens exatas da medição do refinamento. Execução com `--input-dir` apontando para uma base sintética limpa: nenhum sinal emitido, apenas o aviso do limiar padrão — o gate não produz falso positivo em conteúdo saudável.
  - [x] **VISUAL**: Não aplicável — a integração é de fluxo de execução e log de terminal, sem elemento de interface.
  - [x] **EVIDENCE**: Registrado. `build_documentation.mjs --check` → exit 0; `monitor_context.mjs --check` → `CURRENT` sem reconhecimento de ausência de impacto. Diferente de T017, T019 e T020, esta tarefa muda capacidade observável: `PROJECT.md` recebeu a avaliação de qualidade em dois níveis na lista de capacidades principais, e `docs/application.md` registra as cinco etapas do `pipeline.py` e o cancelamento com código 1.
  - [x] **IMPROVE**: Observação registrada em vez de mudança: o invariante `conjunto_nao_vazio` nunca chega a disparar pelo caminho do `pipeline.py`, porque `build_manifest` já rejeita conjunto vazio antes, e um diretório sem `.md` é barrado ainda antes por `src/loader.py`. A sobreposição estava prevista como risco na seção 16; a ordem real de precedência é loader, manifesto e só então o gate. Não alterei nada porque o invariante continua necessário no comando de diagnóstico, onde não há manifesto. Ponto para o fechamento reconciliar em T026.
  <!-- specsfy:evidence {"task": "T018", "refs": ["US-001", "FR-001", "FR-005", "NFR-001", "AC-005"], "files": ["pipeline.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

**Checkpoint**: executar o pipeline com um conjunto inválido e observar que nenhuma escrita ocorreu no destino.

#### Fase 3 — US-002 — Saber qual documento de origem revisar (P1)

**Objetivo**: o relatório aponta os arquivos de origem que degradam a preparação.
**Teste independente**: avaliar um conjunto com dois documentos defeituosos e observar que só eles aparecem apontados.

- [x] T019 [CODE] [US-002] Implementar SizeThresholds com máximo derivado por documento e mínimo sobre conteúdo útil em src/quality.py — Refs: US-002, FR-003, NFR-003, AC-007, AC-008, AC-014 — Depends: T007, T008, T014, T017
  - [x] **PREP**: Concluído. RED de T007, T008 e T014 confirmado; `_get_splitter_config` em `src/chunker.py:26-38` e a `DEC-004` relidos. T014 permanece vermelho por depender de `quality.py`, que nasce em T023 — dependência tornada explícita na seção 15.
  - [x] **EXECUTE**: Concluído. Acrescentados a `src/quality.py` o value object `SizeThresholds`, com `para_documento`, e os helpers `_chunk_size_efetivo`, `_documento` e `_por_documento`. `_chunk_size_efetivo` reproduz a precedência do chunker — frontmatter sobre config — e a margem é o maior breadcrumb efetivamente injetado no documento, conforme a S-003. O mínimo vem da configuração e cai em `MINIMO_UTIL_PADRAO` de 60 com aviso registrado.
  - [x] **VERIFY**: `uv run pytest tests/test_quality_gate.py -k 'minimo or maximo'` → 2 passed. Suíte da fatia: 11 failed, 11 passed. Regressão `uv run pytest` → 11 failed, 205 passed, sem quebrar nenhum dos casos preexistentes.
  - [x] **VISUAL**: Não aplicável — cálculo de limiares, sem superfície visual.
  - [x] **EVIDENCE**: Registrado. `build_documentation.mjs --check` → exit 0; `monitor_context.mjs --check` → `CURRENT`. `docs/application.md` atualizado com a derivação do máximo e o mínimo configurável. `PROJECT.md` revisado sem impacto material: o módulo continua sem ser invocado por qualquer caminho de execução; a integração é T018.
  - [x] **IMPROVE**: Aplicada uma correção de teste, não de produção: o caso de AC-007 afirmava `len(breadcrumb) == 59` para uma string de 58 caracteres, e falhava na própria asserção auxiliar antes de exercitar o comportamento. Corrigido para 58; a regra provada — medir o mínimo sobre o conteúdo útil e não sobre o bruto — permanece idêntica.
  <!-- specsfy:evidence {"task": "T019", "refs": ["US-002", "FR-003", "NFR-003", "AC-007", "AC-008", "AC-014"], "files": ["src/quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

- [x] T020 [CODE] [US-002] Implementar os seis sinais de qualidade em src/quality.py — Refs: US-002, FR-002, AC-005, AC-006 — Depends: T005, T006, T019
  - [x] **PREP**: Concluído. RED de T005 e T006 confirmado e GREEN de T019 conferido; a lista de sinais de `FR-002` relida.
  - [x] **EXECUTE**: Concluído. `QualitySignal` como Strategy, com seis implementações — `PerdaDeEstrutura`, `TruncamentoDeFrase`, `DuplicataExata`, `TextoColapsado`, `ConteudoUtilCurto` e `TamanhoAcimaDoMaximo` — mais `distribuicao_de_tamanho` por `chunk_type`. `evaluate_quality` passou a compor as strategies e a agrupar tudo por documento; nenhuma delas levanta exceção. `TruncamentoDeFrase` exclui `section_summary`, lista, tabela e heading, que terminam legitimamente sem pontuação.
  - [x] **VERIFY**: `uv run pytest -k 'truncamento or duplicata'` → 2 passed. Suíte da fatia: 9 failed, 13 passed. Regressão `uv run pytest` → 9 failed, 207 passed. Nenhum sinal levanta `QualityGateError`: o caso de AC-005 confirma indexação aprovada com catorze chunks truncados.
  - [x] **VISUAL**: Não aplicável — regras de cálculo, sem superfície visual.
  - [x] **EVIDENCE**: Registrado. `build_documentation.mjs --check` → exit 0; `monitor_context.mjs --check` → `CURRENT`. Verificação independente contra a base de referência de 208 chunks: o gate reproduziu exatamente os números medidos no refinamento — 37 e 11 chunks sem `secao` nos dois documentos com heading dentro de bullet, 14 truncamentos, 2 chunks em duplicata exata, 5 com texto colapsado, 8 com conteúdo útil abaixo de 60 e nenhum acima do máximo derivado; desfecho `aprovado`. `PROJECT.md` revisado sem impacto material: o módulo segue sem ser invocado por qualquer caminho de execução.
  - [x] **IMPROVE**: Aplicada: o cálculo de tamanho que T019 havia escrito direto em `evaluate_quality` foi extraído para `ConteudoUtilCurto` e `TamanhoAcimaDoMaximo`, de modo que os seis sinais compartilhem a mesma interface e a função de fronteira apenas componha strategies. Sem isso, dois sinais viveriam fora do mecanismo declarado na seção 8.
  <!-- specsfy:evidence {"task": "T020", "refs": ["US-002", "FR-002", "AC-005", "AC-006"], "files": ["src/quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

- [x] T021 [CODE] [US-002] Implementar QualityReport com agrupamento por documento, render legível e resultado estruturado em src/quality.py — Refs: US-002, FR-004, NFR-002, AC-009, AC-010, AC-013 — Depends: T009, T010, T013, T020
  - [x] **PREP**: Concluído. RED de T009, T010 e T013 confirmado e GREEN de T020 conferido; padrão de `render()` em `src/validation.py` e a `DEC-006` relidos.
  - [x] **EXECUTE**: Concluído. `QualityReport` ganhou `to_dict()`, `render()`, `chunks`, `run_id` e `gerado_em`; `_gravar` escreve `output/<base>/quality-<uuid>.json` de forma atômica, no mesmo padrão de `export_manifest`. `to_dict()` publica apenas `limiares_aplicados`, nunca a configuração recebida, o que mantém credencial e destino remoto fora das duas saídas. O `manifest.json` não é tocado.
  - [x] **VERIFY**: `uv run pytest -k 'agrupa or estruturado or credencial'` → 3 passed. Suíte da fatia: 6 failed, 16 passed. Regressão `uv run pytest` → 6 failed, 210 passed. Sobre a base de referência restaurada, o relatório aponta os cinco documentos com sinal, atribui quatro sinais distintos ao arquivo de regulamento e declara os dois documentos saudáveis sem apontá-los; o detalhe estruturado traz 62 registros de chunk.
  - [x] **VISUAL**: Não aplicável como interface gráfica; a conferência equivalente foi feita na saída de terminal: cabeçalho, distribuição por tipo, bloco por documento com os sinais ordenados, contagem de documentos sem sinal e avisos ao final, sem truncar caminho de arquivo.
  - [x] **EVIDENCE**: Registrado. `build_documentation.mjs --check` → exit 0; `monitor_context.mjs --check` → `CURRENT` sem reconhecimento de ausência de impacto. `PROJECT.md` recebeu o relatório e o resultado estruturado na lista de capacidades; `docs/application.md` registra o caminho `output/<base>/quality-<uuid>.json`.
  - [x] **IMPROVE**: Aplicada: a interface de `QualitySignal` passou a expor `chunks_afetados`, e `ocorrencias` passou a ser uma implementação concreta que deriva a contagem desse detalhe. Sem isso o detalhe por chunk exigido pela FR-004 seria recalculado fora das strategies, duplicando cada heurística. Registro também um efeito colateral que causei durante a verificação de T018: `pipeline.py --input-dir` troca a entrada mas continua gravando nos caminhos de saída do `config.yaml`, então a execução com base sintética sobrescreveu o `chunks.json` da base de referência. A base foi regenerada com `uv run python pipeline.py --only-chunks`, voltando a 7 documentos, 208 chunks e as mesmas contagens; os documentos-fonte nunca foram tocados e `output/` é ignorado pelo Git. O comportamento do `--input-dir` é preexistente e fora do escopo desta fatia.
  <!-- specsfy:evidence {"task": "T021", "refs": ["US-002", "FR-004", "NFR-002", "AC-009", "AC-010", "AC-013"], "files": ["src/quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

- [x] T022 [CODE] Declarar a seção qualidade em config.yaml e config.example.yaml — Refs: FR-003, NFR-003, AC-014 — Depends: T014, T019, T023
  - [x] **PREP**: Concluído. RED de T014 confirmado e GREEN de T019 e T023 conferido; convenção de comentários das demais seções do `config.example.yaml` relida.
  - [x] **EXECUTE**: Concluído. Seção `qualidade` acrescentada a `config.yaml` e `config.example.yaml`, entre `contrato_markdown` e `chunking`, com `minimo_util: 60` documentado. Desvio deliberado do texto original da tarefa: a margem do breadcrumb **não** virou chave de configuração. Ela é derivada do maior breadcrumb efetivamente injetado em cada documento, conforme a suposição S-003 e o comportamento provado por AC-008; declará-la no arquivo criaria uma chave que nenhum código lê. O comentário da seção explica por que o máximo não aparece ali.
  - [x] **VERIFY**: `uv run pytest` → 216 passed, 0 failed. AC-014 verde. Execução real da CLI sobre a base de referência: o aviso `Mínimo de conteúdo útil não configurado` desapareceu da saída, comprovando que o valor passou a vir do arquivo e não do padrão.
  - [x] **VISUAL**: Não aplicável — arquivo de configuração, sem superfície visual. A conferência equivalente foi a ordem das seções e o estilo dos comentários, que seguem as demais seções do arquivo.
  - [x] **EVIDENCE**: Registrado. Chaves acrescentadas: `qualidade.minimo_util`. Arquivos alterados: `config.yaml` e `config.example.yaml`. Nenhum identificador de cliente foi introduzido; a guarda de T014 cobre os dois arquivos de código da fatia.
  - [x] **IMPROVE**: Aplicada: em vez de acrescentar a chave inerte da margem, o comentário do arquivo explica que o máximo é derivado por documento. Uma chave sem leitor seria pior que a ausência dela, porque sugeriria um controle que não existe.
  <!-- specsfy:evidence {"task": "T022", "refs": ["FR-003", "NFR-003", "AC-014"], "files": ["config.yaml", "config.example.yaml"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

**Checkpoint**: gerar o relatório sobre um conjunto sintético e conferir o agrupamento por documento.

#### Fase 4 — US-003 — Medir a qualidade sem indexar (P2)

**Objetivo**: o mantenedor itera nas regras de chunking sem tocar no destino remoto.
**Teste independente**: `uv run python quality.py --chunks <arquivo>` produz relatório e código de saída sem abrir conexão.

- [x] T023 [CODE] [US-003] Implementar a CLI de diagnóstico em quality.py — Refs: US-003, FR-005, NFR-001, AC-011, AC-012, AC-016 — Depends: T011, T012, T016, T021
  - [x] **PREP**: Concluído. RED de T011, T012 e T016 confirmado e GREEN de T021 conferido; `validate.py` relido como padrão de CLI.
  - [x] **EXECUTE**: Concluído. Criado `quality.py` com `--config`, `--chunks` e `--output-dir`, `carregar_chunks` lendo o formato de `src.exporter`, chamada a `evaluate_quality` com `manifest=None` e códigos 0, 1 e 2. Decisão de desenho registrada: a configuração é opcional quando `--chunks` é informado. `config.yaml` saiu do índice do Git pela SPEC-0005, então exigi-la tornaria a ferramenta inutilizável em clone limpo; sem ela os limiares caem nos padrões documentados e o relatório declara o aviso.
  - [x] **VERIFY**: `uv run pytest tests/test_quality_gate.py` → 1 failed, 21 passed; os três alvos (AC-011, AC-012 e AC-016) verdes, e AC-014 também, já que ambos os arquivos passaram a existir e estão livres de identidade de cliente. Regressão `uv run pytest` → 1 failed, 215 passed; o único vermelho é o alvo de T024. Execução real `uv run python quality.py --chunks output/<base>/chunks.json` → exit 0, relatório impresso e resultado estruturado gravado.
  - [x] **VISUAL**: Não aplicável como interface gráfica; a conferência equivalente foi feita na saída de terminal da CLI: aviso opcional, relatório completo, linha em branco e caminho do resultado estruturado, sem truncar caminho nem expor configuração.
  - [x] **EVIDENCE**: Registrado. `build_documentation.mjs --check` → exit 0; `monitor_context.mjs --check` → `CURRENT`. `.specsfy/STACK.md` passou a inventariar `validate.py` e `quality.py` na linha de interface operacional, que citava apenas `pipeline.py`, `search.py` e `chat.py`; `docs/application.md` ganhou a superfície de diagnóstico de qualidade.
  - [x] **IMPROVE**: Aplicada: a CLI degrada para os padrões quando a configuração não carrega, em vez de encerrar com código 2, e informa o aviso na saída. A alternativa — exigir `config.yaml` — reproduziria em `quality.py` o acoplamento que a SPEC-0005 removeu das outras ferramentas.
  <!-- specsfy:evidence {"task": "T023", "refs": ["US-003", "FR-005", "NFR-001", "AC-011", "AC-012", "AC-016"], "files": ["quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

- [x] T024 [CODE] [US-003] Tratar a falha de gravação do resultado estruturado em src/quality.py e quality.py — Refs: US-003, FR-004, FR-005, NFR-002, AC-015 — Depends: T015, T021, T023
  - [x] **PREP**: Concluído. RED de T015 confirmado e GREEN de T021 e T023 conferido; lista de erros e casos-limite da seção 7 relida.
  - [x] **EXECUTE**: Concluído. A chamada a `_gravar` em `evaluate_quality` passou a capturar `OSError`, zerar `report_path` e acrescentar um aviso aos já existentes. A mensagem usa `error.strerror`, que descreve a causa sem devolver o caminho completo à saída.
  - [x] **VERIFY**: `uv run pytest` → 216 passed, 0 failed. AC-015 verde: com o destino de gravação ocupado por um arquivo, o desfecho permanece `aprovado`, `report_path` fica `None`, o aviso de gravação aparece e `render()` continua produzindo o relatório.
  - [x] **VISUAL**: Não aplicável — tratamento de erro em saída textual, sem superfície visual. Conferido que o aviso entra na mesma lista dos demais e aparece ao final do relatório.
  - [x] **EVIDENCE**: Registrado. Arquivo alterado: `src/quality.py`. Toda a suíte da fatia ficou verde nesta tarefa: 22 casos, incluindo os cinco parametrizados de AC-004 e os três de AC-012.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária: a captura ficou restrita a `OSError` no único ponto de escrita do módulo, sem introduzir tratamento genérico que engoliria erro de programação.
  <!-- specsfy:evidence {"task": "T024", "refs": ["US-003", "FR-004", "FR-005", "NFR-002", "AC-015"], "files": ["src/quality.py", "quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

**Checkpoint**: executar o diagnóstico isolado e conferir os três códigos de saída.

#### Fase final — Qualidade

- [x] T025 [DOC] Registrar quality.py e a seção qualidade em .specsfy/STACK.md — Refs: FR-003, FR-005, NFR-003 — Depends: T022, T023
  - [x] **PREP**: Concluído. GREEN de T022 e T023 conferido; linha de interface operacional de `.specsfy/STACK.md` relida — ela inventariava apenas `pipeline.py`, `search.py` e `chat.py`.
  - [x] **EXECUTE**: Concluído. A linha passou a inventariar também `validate.py` e `quality.py`. `validate.py` estava ausente desde a SPEC-0004, lacuna corrigida de passagem. A seção `qualidade` do `config.yaml` já é coberta pelo registro de configuração estrutural do arquivo. Conteúdo humano preservado.
  - [x] **VERIFY**: `node .claude/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`.
  - [x] **VISUAL**: Não aplicável — documento de contexto, sem superfície visual.
  - [x] **EVIDENCE**: Registrado. Arquivo alterado: `.specsfy/STACK.md`, linha de interface operacional. Monitor `CURRENT` e `build_documentation.mjs --check` com saída 0.
  - [x] **IMPROVE**: Aplicada: além de `quality.py`, acrescentei `validate.py`, que a SPEC-0004 entregou sem registrar no inventário. Deixar a correção para depois manteria a projeção mentindo sobre duas ferramentas em vez de uma.

- [x] T026 [TEST] Executar regressão, rastreabilidade e revisão de PROJECT.md a partir de tests/test_quality_gate.py — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, NFR-002, NFR-003 — Depends: T018, T024, T025
  - [x] **PREP**: Concluído. Suíte, checks e gates identificados; métricas de sucesso da seção 1 e Definition of Done da seção 18 relidas item a item.
  - [x] **EXECUTE**: Concluído com três correções de cobertura que o próprio fechamento expôs. A conferência item a item da DoD mostrou que a seção 6 cobre quatro dos seis invariantes críticos e cinco dos seis sinais, e que o caso de AC-010 provava apenas a ausência de `manifest.json` no diretório de saída, não a preservação da sua estrutura. Foram acrescentados cinco casos a `tests/test_quality_gate.py`: conjunto vazio, contagem de manifesto inconsistente, texto colapsado, chunk acima do máximo derivado e comparação da estrutura do manifesto antes e depois. `PROJECT.md` revisado: as capacidades já haviam sido atualizadas em T018 e T021 e continuam corretas.
  - [x] **VERIFY**: `uv run pytest` → 221 passed, 0 failed. `check_traceability.mjs` → 27/27 IDs cobertos. `verify_acceptance.mjs` → `QA: PASSED`, com os dezesseis AC com resultado registrado na seção 12. `validate_tasks.mjs` estrito → READY. `monitor_context.mjs --check` → `CURRENT`. `build_documentation.mjs --check` → saída 0. `uv run ruff check .` → `error: Failed to spawn: ruff`; o binário não está instalado.
  - [x] **VISUAL**: Não aplicável — a fatia não possui superfície visual. A conferência final aplicável foi a legibilidade do relatório de `render()` executado sobre a base de referência de 208 chunks e sobre a saída da CLI.
  - [x] **EVIDENCE**: Registrado. Um item da Definition of Done permanece aberto e não pode ser fechado por esta fatia: `uv run ruff check` não executa porque o Ruff não está instalado no ambiente. O gate é confirmado por `.specsfy/RULES.md`, `docs/testing.md` já registrava a lacuna e o BACKLOG-0007 é o dono dela. Todos os demais dezenove itens estão comprovados. Marcadores órfãos reportados pelo auditor de rastreabilidade pertencem às três primeiras specs e reproduzem o comportamento já observado na SPEC-0005, concluída.
  - [x] **IMPROVE**: Retrospectiva da fatia. O que funcionou: medir a base real antes de escrever a spec derrubou a premissa original de que o problema era tamanho de chunk, e o gate implementado reproduziu os números da medição sem nenhum ajuste. O que custou caro: três defeitos de plano só apareceram na execução — T018 e T022 prometiam GREEN em testes que dependiam de arquivos criados depois, e a seção 6 não cobria dois invariantes e um sinal. A causa comum é a mesma: ao derivar tarefas e cenários dos requisitos, não conferi se cada item enumerado dentro de um requisito tinha cenário próprio. FR-001 declara seis invariantes e FR-002 seis sinais; a seção 6 cobria quatro e cinco. Regra para a próxima fatia: quando um requisito enumerar N itens, conferir a cobertura item a item antes de fechar o Definition Gate, não no fechamento da entrega.

### 15. Ordem de execução

- Caminho crítico: T001–T004 e T016 → T017 → T007/T008/T014 → T019 → T005/T006 → T020 → T018 → T009/T010/T013 → T021 → T011/T012 → T023 → T022 → T015 → T024 → T025 → T026.
- Dependência tornada explícita durante a execução: T018 integra o gate ao `pipeline.py` e seu cenário de aceite exige que o relatório já registre o truncamento como sinal, o que só existe depois de T020. A ordem original colocava T018 logo após T017 e deixaria a tarefa sem como cumprir seu `VERIFY`.
- Segunda dependência tornada explícita pelo mesmo motivo: T022 declara a seção `qualidade` na configuração e seu `VERIFY` espera GREEN na guarda de neutralidade, que só passa quando `quality.py` existir; por isso T022 agora depende também de T023.
- Tarefas paralelas: nenhuma marcada com `[P]`. As dezesseis tarefas de RED escrevem no mesmo `tests/test_quality_gate.py` e as quatro primeiras tarefas `[CODE]` escrevem no mesmo `src/quality.py`, então compartilham arquivo e não admitem paralelismo pelo critério do framework. T022 toca somente arquivos de configuração e poderia ser paralela, mas depende de T019 para conhecer as chaves.
- Estratégia de MVP: US-001 isolada já entrega valor — T001 a T004, T016, T017 e T018 bloqueiam conjunto inválido antes do destino. Um corte de escopo preserva essa fatia e adia US-003.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- `src/manifest.py`, entregue pela SPEC-0001: ponto de bloqueio pré-indexação existente, que esta fatia estende sem substituir.
- `src/chunker.py` e `src/identity.py`: fornecem `chunk_size` efetivo, breadcrumb, `chunk_hash` e `chunk_id`, insumos diretos dos invariantes e dos limiares.
- Padrão de CLI de diagnóstico da SPEC-0004, reaproveitado por FR-005.
- BACKLOG-0007 depende desta fatia como evidência de qualidade para encerrar o milestone M01.

#### Riscos

- Um invariante mal formulado bloqueia uma base saudável → cada invariante recebe caso de teste próprio com conjunto sintético mínimo, e nenhum invariante heurístico é admitido, por PR-001.
- A detecção de truncamento é heurística e tende a falso positivo em lista, tabela e heading → a medição já exclui esses casos; o critério recebe caso de teste com lista, tabela e heading representados, e permanece no nível de sinal, sem poder bloquear.
- O padrão de 60 caracteres foi calibrado sobre uma única base → o valor é configurável por base, e o relatório registra qual limiar foi aplicado.
- A sobreposição entre os invariantes de FR-001 e as validações de `src/manifest.py` pode produzir dupla checagem divergente → o gate é declarado ponto único de decisão em `Arquitetura e módulos`, e a validação do manifesto permanece restrita à construção do próprio manifesto.
- A captura de 2026-09-03 pode mudar a estratégia de quebra e transformar o `section_summary` em metadado → se isso for decidido antes desta fatia ser implementada, o recorte por `chunk_type` do relatório precisa ser revisto. As fatias são independentes: esta mede a quebra sem alterá-la.
- Os marcadores `SPECSFY:` não declaram a spec de origem e os IDs se repetem entre fatias → os casos desta fatia ficam concentrados em `tests/test_quality_gate.py`, mitigação já adotada pelas fatias anteriores.

#### Suposições

- **S-001**: a avaliação embutida também roda no modo `--only-chunks`, por ser exatamente o modo usado para ajustar o chunking sem indexar. Default reversível: se a execução se mostrar custosa nesse modo, um argumento pode desativá-la sem alterar o comportamento padrão.
- **S-002**: os códigos de saída do comando de diagnóstico seguem o padrão da SPEC-0004 — 0 aprovado, 1 reprovado, 2 não foi possível avaliar.
- **S-003**: a margem do breadcrumb usada na derivação do máximo é o comprimento do breadcrumb efetivamente injetado em cada chunk, não uma constante.
- **S-004**: `output/<base>/` é o diretório derivado de `caminhos.chunks_file`, como já ocorre com o manifesto e com o resultado da validação.
- **S-005**: nenhuma dependência nova é acrescentada a `pyproject.toml`; a avaliação usa somente a biblioteca padrão e o que já está instalado.

### 17. Decisões

- **DEC-001**: o gate tem dois níveis — invariantes críticos bloqueiam, sinais de qualidade relatam. Alternativas consideradas: bloquear qualquer violação, e apenas relatar sem bloquear. Trade-off: bloquear tudo reprovaria 31% da base de referência por um sintoma majoritariamente saudável; relatar tudo não impediria uma carga com identidade quebrada. O corte em dois níveis preserva as duas garantias.
- **DEC-002**: somente regras determinísticas bloqueiam. Alternativa considerada: incluir truncamento e texto corrompido no nível de bloqueio. Trade-off: as duas detecções são heurísticas e sujeitas a falso positivo; bloquear com heurística travaria uma base 93% saudável por causa de uma expressão regular.
- **DEC-003**: o gate roda embutido no `pipeline.py` e também como comando próprio. Alternativas: só embutido, só separado, ou resultado dentro do manifesto. Trade-off: o nível crítico precisa estar no caminho da indexação para bloquear de fato, e o nível de sinal só é útil se puder ser executado isoladamente durante o ajuste do chunking.
- **DEC-004**: o máximo é derivado do `chunk_size` efetivo de cada documento; o mínimo é configurado explicitamente. Alternativas: ambos fixos, ambos derivados, ou separados por `chunk_type`. Trade-off: um máximo fixo quebra quando o frontmatter sobrescreve `chunk_size`; um mínimo derivado por percentual seria um número inventado sem base observada; as faixas de `detail` e `section_summary` se sobrepõem e não justificam limiar próprio.
- **DEC-005**: duplicata exata de conteúdo é sinal, não bloqueio. Corrige a classificação inicial adotada durante o refinamento. Razão: `chunk_id` duplicado quebraria a sincronização idempotente e é integridade, mas conteúdo duplicado com `chunk_id` distintos é apenas ruído no top-k, e a validação de 2026-09-02 aprovou a base com esse defeito presente.
- **DEC-006**: o relatório se organiza por documento de origem, com detalhe por chunk preservado no resultado estruturado. Alternativa: organizar por chunk. Trade-off: na base de referência o defeito se concentra em dois de sete arquivos; o eixo documento gera ação, o eixo chunk gera uma lista de 65 itens sem conclusão.
- **DEC-007**: o resultado é gravado em arquivo próprio, fora do `manifest.json`, sem histórico agregado. Alternativas: seção dentro do manifesto, ou histórico acumulado. Trade-off: o manifesto preserva responsabilidade única, e desenhar série histórica antes de existir um consumidor para ela seria trabalho especulativo.
- **DEC-009**: o invariante de contagem do manifesto é avaliado somente quando há manifesto disponível. No comando de diagnóstico ele é pulado e o relatório declara o salto. Alternativas consideradas: exigir o manifesto e retornar 2 sem ele; aceitar um `--manifest` opcional; remover o invariante do gate e deixá-lo apenas em `src/manifest.py`. Trade-off: exigir o manifesto encareceria o ciclo de ajuste do chunking, que é a razão de o comando existir, e os outros cinco invariantes já cobrem a integridade do conjunto; a contagem só tem sentido quando existe um manifesto para conferir contra. Origem: `FIND-ARCH-001`.
- **DEC-008**: o mínimo é medido sobre o conteúdo útil, descontado o breadcrumb, com padrão inicial de 60 caracteres. Alternativas: 250 sobre o bruto, ou 120 sobre o útil. Trade-off: 250 bruto sinaliza 31% da base de referência e afoga o relatório; 60 sobre o útil sinaliza 8 chunks e isola os casos genuinamente pobres.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Os dezesseis cenários `AC` passam com casos TDD próprios em `tests/test_quality_gate.py`.
- [x] Cada história, requisito funcional e requisito não funcional possui pelo menos três cenários e evidência executável.
- [x] Os seis invariantes críticos interrompem a execução antes de qualquer escrita no vector store, com um caso de teste por invariante.
- [x] Nenhum dos seis sinais de qualidade interrompe a execução, comprovado por caso que injeta cada defeito e observa a indexação concluída.
- [x] Sobre um conjunto equivalente à base de referência, o relatório aponta os documentos com perda de estrutura e não aponta os saudáveis.
- [x] O mínimo medido sobre conteúdo útil, com o padrão de 60 caracteres, sinaliza os chunks de conteúdo útil abaixo do limiar e não os que apenas parecem curtos pelo comprimento bruto.
- [x] O máximo derivado do `chunk_size` efetivo não sinaliza chunk de documento que sobrescreveu o valor pelo frontmatter.
- [x] O invariante de contagem do manifesto é pulado no comando de diagnóstico, com o salto declarado no relatório (`DEC-009`).
- [x] `manifest.json` preserva exatamente os campos atuais, comprovado por caso que compara a estrutura antes e depois.
- [x] Relatório legível e resultado estruturado não contêm credencial, token nem URL de destino, comprovado com configuração fictícia.
- [x] A guarda de neutralidade de cliente alcança `src/quality.py` e `quality.py`.
- [x] `uv run pytest` está verde e `uv run ruff check` não acusa achado novo. **Histórico**: no aceite original, `uv run pytest` → 221 passed e o Ruff ainda não estava instalado; a pendência externa foi aceita e atribuída ao BACKLOG-0007. **Cumprido em 2026-09-03 pela SPEC-0007**: Ruff 0.16.5 foi fixado no grupo de desenvolvimento, os achados foram corrigidos e `uv run ruff check` passou, sem reabrir ou recalcular os gates desta spec concluída.
- [x] Nenhuma dependência foi acrescentada a `pyproject.toml`.
- [x] `.specsfy/STACK.md` registra `quality.py` na linha de interface operacional, hoje limitada a `pipeline.py`, `search.py` e `chat.py`, e registra a seção `qualidade` do `config.yaml`.
- [x] `PROJECT.md` foi revisto quanto à capacidade nova de bloquear a indexação por invariante de integridade e diagnosticar a qualidade da preparação; se a revisão concluir que não há impacto material, a justificativa fica registrada na evidência da tarefa.
- [x] `config.example.yaml` documenta a seção `qualidade` sem identidade de cliente.
- [x] A documentação foi reconstruída com o monitor de contexto em `CURRENT`.

## Effort history

- 2026-09-03: 1 → 6. Promoção do BACKLOG-0005. A fatia cria um módulo novo com dois níveis de avaliação, seis invariantes determinísticos e seis sinais heurísticos, integra um ponto de bloqueio no caminho de indexação, acrescenta uma CLI no padrão da SPEC-0004, estende `config.yaml` e exige conjunto sintético de teste com cada defeito representado.
