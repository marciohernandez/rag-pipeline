# Especificação integrada: Gate automatizado de qualidade de chunks e metadados

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0006 |
| Slug | 0006-gate-qualidade-chunks-metadados |
| Status | Defined |
| Effort | 6 |
| Effort updated at | 2026-09-03 |
| Effort rationale | Recalibrado de 1 para 6 na promoção. A fatia cria um módulo novo com dois níveis de avaliação, seis invariantes determinísticos e seis sinais heurísticos, integra um ponto de bloqueio no caminho de indexação, acrescenta uma CLI no padrão da SPEC-0004, estende `config.yaml` e exige conjunto sintético de teste com cada defeito representado. O risco está concentrado em dois pontos: um invariante mal formulado bloqueia uma base saudável, e uma heurística mal calibrada afoga o relatório em falso positivo. Comparável à SPEC-0001 e à SPEC-0004, ambas 6. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Pending |
| Delivery Gate | Pending |
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
| US-001, FR-001, NFR-001, AC-001 | AC-001 na seção 6 | caso de chunk sem `chunk_id` em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-001, FR-001, AC-002 | AC-002 na seção 6 | caso de `chunk_id` duplicado em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-001, FR-001, AC-003 | AC-003 na seção 6 | caso de chunk só com breadcrumb em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-001, FR-001, AC-004 | AC-004 na seção 6 | caso de metadado de rastreabilidade ausente em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-001, FR-002, NFR-001, AC-005 | AC-005 na seção 6 | caso de truncamento que não bloqueia em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-002, FR-002, AC-006 | AC-006 na seção 6 | caso de duplicata exata relatada em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-002, FR-003, NFR-003, AC-007 | AC-007 na seção 6 | caso de mínimo sobre conteúdo útil em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-002, FR-003, AC-008 | AC-008 na seção 6 | caso de máximo derivado do frontmatter em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-002, FR-002, FR-004, NFR-003, AC-009 | AC-009 na seção 6 | caso de agrupamento por documento em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-002, FR-004, NFR-002, AC-010 | AC-010 na seção 6 | caso de arquivo próprio e manifesto intacto em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-003, FR-005, NFR-001, AC-011 | AC-011 na seção 6 | caso de diagnóstico isolado com dublê que falha em escrita em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-003, FR-005, AC-012 | AC-012 na seção 6 | caso dos três códigos de saída em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| FR-004, NFR-002, AC-013 | AC-013 na seção 6 | caso de varredura de segredo nas duas saídas em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| FR-003, NFR-003, AC-014 | AC-014 na seção 6 | guarda estática de neutralidade em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-003, FR-004, FR-005, NFR-002, AC-015 | AC-015 na seção 6 | caso de falha de gravação em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |
| US-003, FR-001, FR-005, AC-016 | AC-016 na seção 6 | caso de diagnóstico sem manifesto em `tests/test_quality_gate.py` | Observado em 2026-09-03 | Pending | Pending |

### 12. Plano de testes e rastreabilidade

Regressão completa da fatia: `uv run pytest`. Verificação estática: `uv run ruff check`.

| Requisito | Cenário BDD | Nível | Arquivo e comando focal | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-001 | AC-002 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-001 | AC-003 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-001 | AC-004 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-002 | AC-005 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-002 | AC-006 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-002 | AC-009 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-003 | AC-007 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-003 | AC-008 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-003 | AC-014 | Estático | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-004 | AC-009 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-004 | AC-010 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-004 | AC-013 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-004 | AC-015 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-005 | AC-011 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-005 | AC-012 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-005 | AC-015 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| NFR-001 | AC-001 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| NFR-001 | AC-005 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| NFR-001 | AC-011 | Estático e integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| NFR-002 | AC-010 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| NFR-002 | AC-013 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| NFR-002 | AC-015 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| NFR-003 | AC-007 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| NFR-003 | AC-009 | Unidade | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| NFR-003 | AC-014 | Estático | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-001 | AC-016 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |
| FR-005 | AC-016 | Integração | `tests/test_quality_gate.py` — `uv run pytest tests/test_quality_gate.py` | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY — 2026-09-03. A primeira passagem retornou `NOT READY` com dois `P1`; os seis achados foram corrigidos nas seções de origem e reavaliados.
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0006-gate-qualidade-chunks-metadados/spec.md --allow-draft` → `VALID DRAFT`
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/review_findings.mjs --spec specs/draft/0006-gate-qualidade-chunks-metadados/spec.md --root .` → `Reviews: FAILED`, com `FIND-ARCH-001` e `FIND-PROD-001` bloqueantes
- **Estrutura**: `VALID DRAFT`. Formato `Specsfy/2.0`, três atos na ordem, slug igual ao diretório, pacote restrito a `spec.md`.
- **Cobertura**: 3 `US`, 5 `FR`, 3 `NFR`, 15 `AC`. Todos os onze `US`/`FR`/`NFR` alcançam ao menos três `AC` distintos declarados em `**Cobre**`; nenhum `AC` referencia ID inexistente. A tabela RED-GREEN-REFACTOR prevê 15 casos TDD e repete a mesma cobertura mínima.
- **Achados**: seis registrados, todos `Resolved`. Nenhum `P1` aberto.

- **FIND-ARCH-001** [P1] [Resolved] `FR-001` inclui como invariante crítico a contagem do manifesto inconsistente com o número de chunks, mas `FR-005` define o comando de diagnóstico operando sobre um arquivo de chunks já gerado, sem manifesto disponível — Refs: FR-001, FR-005, AC-012 — Evidence: specs/draft/0006-gate-qualidade-chunks-metadados/spec.md:414 — Effect: a linha 418 da mesma spec declara `FR-005`; o comportamento do invariante no modo de diagnóstico é indefinido; a spec não diz se ele é pulado, se torna a avaliação impossível com código 2 ou se o comando passa a exigir o manifesto, e nem `AC-012` nem a lista de erros da seção 7 cobrem a condição — Suggestion: decidir o alcance do invariante de manifesto e refletir a decisão em `FR-001`, `FR-005`, em um `AC` próprio e na lista de erros e casos-limite — Status: Resolvido em 2026-09-03: `FR-001` passou a condicionar o invariante de contagem à disponibilidade do manifesto, `FR-005` declara o salto no comando de diagnóstico, `AC-016` cobre o comportamento, a lista de erros da seção 7 trata a condição e `DEC-009` registra a decisão e as alternativas

- **FIND-PROD-001** [P1] [Resolved] A Definition of Done preserva o checklist genérico do template e não é provável por comando nem evidência objetiva desta fatia — Refs: FR-005, NFR-003 — Evidence: .specsfy/STACK.md:19 — Effect: a seção 18 da spec e o `PROJECT.md` completam a evidência; `.specsfy/STACK.md` inventaria a interface operacional como `pipeline.py`, `search.py` e `chat.py` e a fatia acrescenta `quality.py`; `PROJECT.md` lista as capacidades do componente e a fatia acrescenta bloquear indexação por invariante e diagnosticar a preparação; nenhum item da DoD prova as métricas de sucesso da seção 1 — Suggestion: reescrever a seção 18 com itens específicos e verificáveis, citando a atualização de `.specsfy/STACK.md` e a revisão de `PROJECT.md` — Status: Resolvido em 2026-09-03: a seção 18 foi reescrita com vinte itens verificáveis, citando a atualização de `.specsfy/STACK.md`, a revisão de `PROJECT.md` e as métricas de sucesso da seção 1

- **FIND-PROD-002** [P2] [Resolved] `AC-012` encadeia três pares `When`/`Then` em um único `Scenario`, misturando os três códigos de saída — Refs: AC-012, FR-005 — Evidence: specs/draft/0006-gate-qualidade-chunks-metadados/spec.md:346 — Effect: dificulta observar um RED por comportamento e contraria o critério de cenário com `Given`, `When` e `Then` observáveis — Suggestion: converter em `Scenario Outline` com `Examples` ou dividir em três cenários — Status: Resolvido em 2026-09-03: `AC-012` virou `Scenario Outline` com um `Examples` por código de saída

- **FIND-PROD-003** [P2] [Resolved] O último `And` de `AC-004` generaliza o tratamento para `source_hash`, `project_id`, `chunk_hash` e `chunk_type` em vez de declarar um resultado observável — Refs: AC-004, FR-001 — Evidence: specs/draft/0006-gate-qualidade-chunks-metadados/spec.md:217 — Effect: quatro dos cinco metadados obrigatórios ficam sem cenário executável — Suggestion: converter em `Scenario Outline` com um `Examples` por metadado obrigatório — Status: Resolvido em 2026-09-03: `AC-004` virou `Scenario Outline` com um `Examples` por metadado obrigatório

- **FIND-PROD-004** [P2] [Resolved] A coluna `Arquivo/comando esperado` da matriz traz apenas o caminho do arquivo de teste, sem o comando executável — Refs: FR-001, FR-002, FR-003, FR-004, FR-005 — Evidence: specs/draft/0006-gate-qualidade-chunks-metadados/spec.md:631 — Effect: a matriz não liga requisito, cenário, nível, comando e evidência como o gate de verificação exige — Suggestion: registrar o comando focal `uv run pytest tests/test_quality_gate.py` e o seletor do caso onde couber — Status: Resolvido em 2026-09-03: a matriz da seção 12 passou a trazer o comando focal por linha, mais os comandos de regressão e verificação estática

- **FIND-PROD-005** [P3] [Resolved] O `Effort` foi recalibrado de 1 para 6 na promoção, mas a spec não traz a seção `Effort history` mantida pelas fatias anteriores — Refs: US-001 — Evidence: specs/completed/0005-remover-hardcodes-cliente/spec.md — Effect: a recalibração perde rastreabilidade e diverge da convenção local do repositório — Suggestion: acrescentar a seção `Effort history` com o registro datado da recalibração — Status: Resolvido em 2026-09-03: a seção `Effort history` foi acrescentada com o registro datado de 1 → 6
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`, severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/draft/0006-gate-qualidade-chunks-metadados/spec.md`
- **Achados**: Pending.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0006-gate-qualidade-chunks-metadados/spec.md .`
- **Achados**: Pending.

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

- [ ] T017 [CODE] [US-001] Implementar os seis invariantes críticos e `QualityGateError` em src/quality.py — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-016 — Depends: T001, T002, T003, T004, T016
  - [ ] **PREP**: Confirmar o RED de T001 a T004 e T016; reconstruir `docs/` com `$specsfy-documentator` antes de escrever; reler `FR-001` e `DEC-009`.
  - [ ] **EXECUTE**: Criar `src/quality.py` com `CriticalInvariant` como Strategy, uma implementação por invariante, `QualityGateError` e o esqueleto de `evaluate_quality`; condicionar o invariante de contagem à presença do manifesto.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_quality_gate.py` e observar GREEN nos casos de T001 a T004 e T016.
  - [ ] **VISUAL**: Não aplicável — o módulo não possui superfície visual; a saída legível ainda não existe nesta tarefa.
  - [ ] **EVIDENCE**: Registrar GREEN, arquivos alterados e IDs nas seções 11 e 12.
  - [ ] **IMPROVE**: Aplicar melhoria de desenho ou justificar que nenhuma foi necessária.
  <!-- specsfy:evidence {"task": "T017", "refs": ["US-001", "FR-001", "NFR-001", "AC-001", "AC-002", "AC-003", "AC-004", "AC-016"], "files": ["src/quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

- [ ] T018 [CODE] [US-001] Integrar o bloqueio do gate em pipeline.py entre o manifesto e a indexação — Refs: US-001, FR-001, FR-005, NFR-001, AC-005 — Depends: T017, T005
  - [ ] **PREP**: Confirmar o RED de T005 e o GREEN de T017; reconstruir `docs/` com `$specsfy-documentator`; reler o ponto de chamada em `pipeline.py:118-125`.
  - [ ] **EXECUTE**: Chamar `evaluate_quality` logo após `build_manifest`, antes do desvio de `--only-chunks`, e deixar `QualityGateError` interromper antes da etapa de indexação.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_quality_gate.py` e `uv run pytest`; confirmar que o modo `--only-chunks` também avalia.
  - [ ] **VISUAL**: Não aplicável — a integração é de fluxo de execução, sem elemento de interface.
  - [ ] **EVIDENCE**: Registrar GREEN, o comportamento nos dois modos e os arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de desenho ou justificar que nenhuma foi necessária.
  <!-- specsfy:evidence {"task": "T018", "refs": ["US-001", "FR-001", "FR-005", "NFR-001", "AC-005"], "files": ["pipeline.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

**Checkpoint**: executar o pipeline com um conjunto inválido e observar que nenhuma escrita ocorreu no destino.

#### Fase 3 — US-002 — Saber qual documento de origem revisar (P1)

**Objetivo**: o relatório aponta os arquivos de origem que degradam a preparação.
**Teste independente**: avaliar um conjunto com dois documentos defeituosos e observar que só eles aparecem apontados.

- [ ] T019 [CODE] [US-002] Implementar SizeThresholds com máximo derivado por documento e mínimo sobre conteúdo útil em src/quality.py — Refs: US-002, FR-003, NFR-003, AC-007, AC-008, AC-014 — Depends: T007, T008, T014, T017
  - [ ] **PREP**: Confirmar o RED de T007, T008 e T014; reconstruir `docs/` com `$specsfy-documentator`; reler `_get_splitter_config` em `src/chunker.py:26-38` e `DEC-004`.
  - [ ] **EXECUTE**: Implementar a derivação do máximo a partir do `chunk_size` efetivo mais a margem do breadcrumb, e o mínimo lido da configuração sobre o conteúdo útil, com padrão de 60.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_quality_gate.py` e observar GREEN em T007 e T008.
  - [ ] **VISUAL**: Não aplicável — cálculo de limiares, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar GREEN, o padrão aplicado e os arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de desenho ou justificar que nenhuma foi necessária.
  <!-- specsfy:evidence {"task": "T019", "refs": ["US-002", "FR-003", "NFR-003", "AC-007", "AC-008", "AC-014"], "files": ["src/quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

- [ ] T020 [CODE] [US-002] Implementar os seis sinais de qualidade em src/quality.py — Refs: US-002, FR-002, AC-005, AC-006 — Depends: T005, T006, T019
  - [ ] **PREP**: Confirmar o RED de T005 e T006 e o GREEN de T019; reconstruir `docs/` com `$specsfy-documentator`; reler a lista de sinais em `FR-002`.
  - [ ] **EXECUTE**: Implementar `QualitySignal` como Strategy e as seis regras: perda de estrutura, truncamento, duplicata exata, texto colapsado por tabulação, distribuição de tamanho e conteúdo útil abaixo do mínimo; nenhuma delas interrompe a execução.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_quality_gate.py` e observar GREEN em T005 e T006; confirmar que nenhum sinal levanta `QualityGateError`.
  - [ ] **VISUAL**: Não aplicável — regras de cálculo, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar GREEN, as contagens obtidas no conjunto sintético e os arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de desenho ou justificar que nenhuma foi necessária.
  <!-- specsfy:evidence {"task": "T020", "refs": ["US-002", "FR-002", "AC-005", "AC-006"], "files": ["src/quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

- [ ] T021 [CODE] [US-002] Implementar QualityReport com agrupamento por documento, render legível e resultado estruturado em src/quality.py — Refs: US-002, FR-004, NFR-002, AC-009, AC-010, AC-013 — Depends: T009, T010, T013, T020
  - [ ] **PREP**: Confirmar o RED de T009, T010 e T013 e o GREEN de T020; reconstruir `docs/` com `$specsfy-documentator`; reler o padrão de `render()` em `src/validation.py` e `DEC-006`.
  - [ ] **EXECUTE**: Agrupar os sinais por documento de origem, preservar o detalhe por chunk, implementar `render()` e a gravação em `output/<base>/quality-<uuid>.json`, sem tocar o `manifest.json` e sem registrar credencial ou URL de destino.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_quality_gate.py` e observar GREEN em T009, T010 e T013.
  - [ ] **VISUAL**: Não aplicável — a saída é texto de terminal; a conferência aplicável é a legibilidade do relatório, exercitada pelos casos de `render()`.
  - [ ] **EVIDENCE**: Registrar GREEN, o caminho do arquivo gerado e os arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de desenho ou justificar que nenhuma foi necessária.
  <!-- specsfy:evidence {"task": "T021", "refs": ["US-002", "FR-004", "NFR-002", "AC-009", "AC-010", "AC-013"], "files": ["src/quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

- [ ] T022 [CODE] Declarar a seção qualidade em config.yaml e config.example.yaml — Refs: FR-003, NFR-003, AC-014 — Depends: T014, T019
  - [ ] **PREP**: Confirmar o RED de T014 e o GREEN de T019; reconstruir `docs/` com `$specsfy-documentator`; reler a convenção de comentários das demais seções do `config.example.yaml`.
  - [ ] **EXECUTE**: Acrescentar a seção `qualidade` com o mínimo de conteúdo útil e a margem do breadcrumb, documentada, sem identidade de cliente e com o padrão explicitado.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_quality_gate.py` e observar GREEN em T014; confirmar que a configuração ausente cai no padrão de 60.
  - [ ] **VISUAL**: Não aplicável — arquivo de configuração, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar GREEN, as chaves acrescentadas e os arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de desenho ou justificar que nenhuma foi necessária.
  <!-- specsfy:evidence {"task": "T022", "refs": ["FR-003", "NFR-003", "AC-014"], "files": ["config.yaml", "config.example.yaml"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

**Checkpoint**: gerar o relatório sobre um conjunto sintético e conferir o agrupamento por documento.

#### Fase 4 — US-003 — Medir a qualidade sem indexar (P2)

**Objetivo**: o mantenedor itera nas regras de chunking sem tocar no destino remoto.
**Teste independente**: `uv run python quality.py --chunks <arquivo>` produz relatório e código de saída sem abrir conexão.

- [ ] T023 [CODE] [US-003] Implementar a CLI de diagnóstico em quality.py — Refs: US-003, FR-005, NFR-001, AC-011, AC-012, AC-016 — Depends: T011, T012, T016, T021
  - [ ] **PREP**: Confirmar o RED de T011, T012 e T016 e o GREEN de T021; reconstruir `docs/` com `$specsfy-documentator`; reler `validate.py` como padrão de CLI.
  - [ ] **EXECUTE**: Criar `quality.py` com `--config` e `--chunks`, chamando `evaluate_quality`, imprimindo `render()`, informando o caminho do resultado e retornando 0, 1 ou 2; pular o invariante de contagem e declarar o salto quando não houver manifesto.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_quality_gate.py` e observar GREEN em T011, T012 e T016.
  - [ ] **VISUAL**: Não aplicável — a superfície é linha de comando; a conferência aplicável é a legibilidade da saída, exercitada pelos casos da CLI.
  - [ ] **EVIDENCE**: Registrar GREEN, os três códigos de saída observados e os arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de desenho ou justificar que nenhuma foi necessária.
  <!-- specsfy:evidence {"task": "T023", "refs": ["US-003", "FR-005", "NFR-001", "AC-011", "AC-012", "AC-016"], "files": ["quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

- [ ] T024 [CODE] [US-003] Tratar a falha de gravação do resultado estruturado em src/quality.py e quality.py — Refs: US-003, FR-004, FR-005, NFR-002, AC-015 — Depends: T015, T021, T023
  - [ ] **PREP**: Confirmar o RED de T015 e o GREEN de T021 e T023; reconstruir `docs/` com `$specsfy-documentator`; reler a lista de erros e casos-limite da seção 7.
  - [ ] **EXECUTE**: Preservar o relatório legível no stdout quando a gravação falhar, informar a falha sem expor caminho de credencial e manter o desfecho da avaliação.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_quality_gate.py` e observar GREEN em T015.
  - [ ] **VISUAL**: Não aplicável — tratamento de erro em saída textual, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar GREEN, a mensagem produzida e os arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de desenho ou justificar que nenhuma foi necessária.
  <!-- specsfy:evidence {"task": "T024", "refs": ["US-003", "FR-004", "FR-005", "NFR-002", "AC-015"], "files": ["src/quality.py", "quality.py"], "commands": [{"run": "uv run pytest tests/test_quality_gate.py", "exit": 0}]} -->

**Checkpoint**: executar o diagnóstico isolado e conferir os três códigos de saída.

#### Fase final — Qualidade

- [ ] T025 [DOC] Registrar quality.py e a seção qualidade em .specsfy/STACK.md — Refs: FR-003, FR-005, NFR-003 — Depends: T022, T023
  - [ ] **PREP**: Confirmar o GREEN de T022 e T023; reler a linha 19 de `.specsfy/STACK.md`, que hoje inventaria a interface operacional como `pipeline.py`, `search.py` e `chat.py`.
  - [ ] **EXECUTE**: Acrescentar `quality.py` à linha de interface operacional e registrar a seção `qualidade` do `config.yaml` como configuração estrutural, preservando o conteúdo humano existente.
  - [ ] **VERIFY**: Executar `node .claude/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` e obter `CURRENT`.
  - [ ] **VISUAL**: Não aplicável — documento de contexto, sem superfície visual.
  - [ ] **EVIDENCE**: Registrar o comando do monitor, seu resultado e as linhas alteradas.
  - [ ] **IMPROVE**: Registrar melhoria de redação aplicada ou justificar a ausência.

- [ ] T026 [TEST] Executar regressão, rastreabilidade e revisão de PROJECT.md a partir de tests/test_quality_gate.py — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, NFR-002, NFR-003 — Depends: T018, T024, T025
  - [ ] **PREP**: Identificar a suíte completa, os checks estáticos e os gates; reler as métricas de sucesso da seção 1 e a Definition of Done da seção 18.
  - [ ] **EXECUTE**: Executar `uv run pytest`, `uv run ruff check` e o verificador de rastreabilidade; revisar `PROJECT.md` quanto à capacidade nova de bloquear a indexação e diagnosticar a preparação.
  - [ ] **VERIFY**: Confirmar suíte verde, ausência de achado novo do Ruff, nenhuma lacuna de rastreabilidade e cada item da seção 18 comprovado.
  - [ ] **VISUAL**: Não aplicável — a fatia não possui superfície visual; a conferência final aplicável é a legibilidade do relatório produzido por `render()`.
  - [ ] **EVIDENCE**: Registrar contagens, comandos, resultado da revisão de `PROJECT.md` e, se não houver impacto material, a justificativa.
  - [ ] **IMPROVE**: Registrar a retrospectiva do processo desta fatia.

### 15. Ordem de execução

- Caminho crítico: T001–T004 e T016 → T017 → T018 → T007/T008/T014 → T019 → T005/T006 → T020 → T009/T010/T013 → T021 → T011/T012 → T023 → T015 → T024 → T025 → T026.
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

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Os dezesseis cenários `AC` passam com casos TDD próprios em `tests/test_quality_gate.py`.
- [ ] Cada história, requisito funcional e requisito não funcional possui pelo menos três cenários e evidência executável.
- [ ] Os seis invariantes críticos interrompem a execução antes de qualquer escrita no vector store, com um caso de teste por invariante.
- [ ] Nenhum dos seis sinais de qualidade interrompe a execução, comprovado por caso que injeta cada defeito e observa a indexação concluída.
- [ ] Sobre um conjunto equivalente à base de referência, o relatório aponta os documentos com perda de estrutura e não aponta os saudáveis.
- [ ] O mínimo medido sobre conteúdo útil, com o padrão de 60 caracteres, sinaliza os chunks de conteúdo útil abaixo do limiar e não os que apenas parecem curtos pelo comprimento bruto.
- [ ] O máximo derivado do `chunk_size` efetivo não sinaliza chunk de documento que sobrescreveu o valor pelo frontmatter.
- [ ] O invariante de contagem do manifesto é pulado no comando de diagnóstico, com o salto declarado no relatório (`DEC-009`).
- [ ] `manifest.json` preserva exatamente os campos atuais, comprovado por caso que compara a estrutura antes e depois.
- [ ] Relatório legível e resultado estruturado não contêm credencial, token nem URL de destino, comprovado com configuração fictícia.
- [ ] A guarda de neutralidade de cliente alcança `src/quality.py` e `quality.py`.
- [ ] `uv run pytest` está verde e `uv run ruff check` não acusa achado novo.
- [ ] Nenhuma dependência foi acrescentada a `pyproject.toml`.
- [ ] `.specsfy/STACK.md` registra `quality.py` na linha de interface operacional, hoje limitada a `pipeline.py`, `search.py` e `chat.py`, e registra a seção `qualidade` do `config.yaml`.
- [ ] `PROJECT.md` foi revisto quanto à capacidade nova de bloquear a indexação por invariante de integridade e diagnosticar a qualidade da preparação; se a revisão concluir que não há impacto material, a justificativa fica registrada na evidência da tarefa.
- [ ] `config.example.yaml` documenta a seção `qualidade` sem identidade de cliente.
- [ ] A documentação foi reconstruída com o monitor de contexto em `CURRENT`.

## Effort history

- 2026-09-03: 1 → 6. Promoção do BACKLOG-0005. A fatia cria um módulo novo com dois níveis de avaliação, seis invariantes determinísticos e seis sinais heurísticos, integra um ponto de bloqueio no caminho de indexação, acrescenta uma CLI no padrão da SPEC-0004, estende `config.yaml` e exige conjunto sintético de teste com cada defeito representado.
