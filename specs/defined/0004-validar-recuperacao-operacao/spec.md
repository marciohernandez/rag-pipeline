# Especificação integrada: Validar recuperação e operação de ponta a ponta

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0004 |
| Slug | 0004-validar-recuperacao-operacao |
| Status | Defined |
| Effort | 5 |
| Effort updated at | 2026-09-01 |
| Effort rationale | Fatia vertical única sobre contratos que já existem: um comando somente leitura, um formato de gabarito novo, três desfechos e conferência remota. Não altera contrato existente nem escreve no destino, mas cobre dezesseis cenários e remove duas ferramentas em uso. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Pending |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-01 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

A idempotência local está comprovada por 141 asserções que rodam contra clientes falsos, mas nada no repositório prova que a base indexada no destino remoto corresponde ao manifesto gerado nem que ela responde ao que deveria responder. A SPEC-0003 substituiu toda a camada de providers e removeu `src/embedder.py`; desde então nenhuma execução real contra Qdrant e OpenAI foi observada. As duas ferramentas de diagnóstico existentes, `scripts/check_qdrant_connection.py` e `scripts/check_qdrant_search.py`, falam REST cru direto no destino, ignoram os contratos neutros e carregam o nome do cliente e uma pergunta de negócio fixos no código.

#### Resultado desejado

O operador executa um comando único, somente leitura, que aprova ou reprova uma base antes do consumo por aplicações RAG. O veredito distingue base divergente de ambiente indisponível, é legível na hora e fica gravado em formato estruturado para consumo posterior pelo backend do BACKLOG-0008.

#### Métricas de sucesso

- Uma base íntegra é aprovada com código de saída `0` e uma base com divergência de identidade é reprovada com código `1`, sem intervenção manual.
- Credencial ausente, escopo inexistente ou dimensão divergente encerram com código `2` sem executar nenhuma consulta remota.
- Nenhuma operação de escrita chega ao destino em qualquer caminho de execução, inclusive nos caminhos de falha.
- Nenhum identificador de cliente permanece no código das ferramentas de validação após a entrega.
- A suíte Pytest permanece verde e cobre os dezesseis cenários desta fatia sem exigir rede.

### 2. Research e esclarecimentos

#### Researchs executados

- Nenhum research externo foi necessário. Cada decisão desta fatia se apoia em código, configuração e documentos do próprio repositório, verificados durante o refinamento do BACKLOG-0006 em 2026-09-01. As três verificações materiais abaixo estão registradas como notas de proveniência local.
- **R-001** [high] `list_ids` e `query` pertencem ao contrato núcleo de cada adapter, permitindo conferência de identidade e recuperação neutras entre backends — Verdict: verified — Confidence: high — Evidence: research/verificacoes-locais.md#contrato-nucleo-dos-adapters — Budget: 1/3.
- **R-002** [high] `SearchResult.score` é preenchido com o valor nativo de cada integração, logo um limiar numérico único não é comparável entre Qdrant, ChromaDB e Pinecone — Verdict: verified — Confidence: high — Evidence: research/verificacoes-locais.md#score-nativo-por-provider — Budget: 1/3.
- **R-003** [medium] A base ativa tem 208 chunks em 7 documentos, volume no qual a leitura de identidades do escopo é barata — Verdict: verified — Confidence: high — Evidence: research/verificacoes-locais.md#volume-observado-na-base-ativa — Budget: 1/3.

#### Fontes e contexto consultados

- `specs/backlog/0006-validar-recuperacao-operacao.md`: brief refinado com as oito decisões confirmadas pelo usuário.
- `src/providers/contracts.py`: `list_ids(scope) -> set[str]` e `query(scope, embedding, k)` pertencem ao contrato núcleo de cada adapter; `SearchResult.score` é nativo de cada provider.
- `src/manifest.py`: `build_manifest` grava `chunk_ids`, `chunk_count`, `chunk_type_counts`, `documents` e `run_id`.
- `src/indexing.py`: `retrieve()` já recupera com escopo de projeto e tenant explícitos; `build_scope` e `build_vector_store` compõem o acesso.
- `src/safety.py`: precedente fail-closed da SPEC-0001, preservado por esta fatia.
- `scripts/check_qdrant_connection.py` e `scripts/check_qdrant_search.py`: protótipos com `COLLECTION` e pergunta de negócio fixos; usam códigos `2` para ambiente e `1` para falha.
- `config.yaml`: seções `projeto`, `caminhos`, `embedding` e `vector_store` da base ativa.
- `output/vivo_gold_banda_larga_pf/manifest.json`: 208 chunks, 7 documentos, 191 `detail` e 17 `section_summary`.
- `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md`, seção 13: formato esboçado das consultas de referência, adotado pela DEC-003.
- `.specsfy/RULES.md`, seção Operação: registro por execução sem credenciais, tokens ou URLs.
- `.gitignore`: `output/` não é versionado; `documentos/` é rastreado pelo git.

#### Documentação consultada

- Nenhuma documentação externa foi consultada nesta fatia.

#### Artefatos de pesquisa armazenados

- `specs/defined/0004-validar-recuperacao-operacao/research/verificacoes-locais.md`: notas de proveniência das inspeções locais de 2026-09-01, com comando, resultado e consequência para a spec. Não há artefato externo, porque nenhuma fonte externa foi consultada.

#### Dúvidas respondidas

- **Q**: Como a validação deve ser entregue? → **A**: comando CLI único, somente leitura, com a lógica em módulo Python reaproveitável pelo backend do BACKLOG-0008.
- **Q**: O que reprova a conferência entre manifesto e destino? → **A**: igualdade estrita dos conjuntos de `chunk_id`, com faltantes e órfãos separados no relatório.
- **Q**: Como o roteiro comprova que a recuperação está correta? → **A**: gabarito versionado por base, com `pergunta`, `deve_conter`, `documento_esperado` e categoria declarada em cada entrada.
- **Q**: Como o comando reporta o resultado? → **A**: relatório legível no stdout e JSON em `output/<base>/validation-<run_id>.json`.
- **Q**: Como distinguir os desfechos? → **A**: `0` aprovado, `1` reprovado após validar de fato, `2` quando não foi possível validar.
- **Q**: Como o comando descobre o que validar? → **A**: exclusivamente pelo `config.yaml`, com `caminhos.consultas_referencia`, escopo de `projeto.nome` e `--tenant` opcional.
- **Q**: O que fazer com os dois protótipos de diagnóstico? → **A**: removê-los nesta mesma fatia, depois que o comando cobrir preflight e consulta.
- **Q**: O que faz uma consulta sem resposta passar? → **A**: nenhum resultado atinge `validacao.limiar_minimo` declarado no config da base.

#### Dúvidas abertas

- Nenhuma lacuna de produto aplicável. O valor concreto do limiar da base Vivo depende de calibragem empírica durante a execução e a paginação de `list_ids` só se torna material em bases muito maiores; nenhum dos dois altera o comportamento especificado.

### 3. Escopo e atores

#### Incluído

- Comando único de validação somente leitura, com a lógica em módulo Python reaproveitável.
- Preflight de ambiente: conexão autenticada, existência do escopo e compatibilidade de dimensão.
- Conferência de identidade entre o manifesto da base e o destino remoto, separando faltantes de órfãos.
- Roteiro de consultas dirigido por gabarito versionado, com categorias ampla, específica e sem resposta.
- Relatório legível no stdout e resultado estruturado em JSON.
- Três desfechos distintos por código de saída.
- Remoção de `scripts/check_qdrant_connection.py` e `scripts/check_qdrant_search.py`.
- Entradas novas no `config.yaml`: `caminhos.consultas_referencia` e a seção `validacao`.

#### Fora de escopo

- Qualquer mutação no destino remoto, inclusive correção automática de divergência.
- APM, tracing distribuído e métricas em serviço externo, que pertencem ao projeto-mãe `rag-pipeline`.
- Front, backend HTTP e execução assíncrona, que pertencem ao BACKLOG-0008.
- LLM de geração ou avaliação por modelo, que pertence ao BACKLOG-0010.
- Paridade destrutiva de ChromaDB e Pinecone, que pertence ao BACKLOG-0009.
- Configuração de Ruff e gates de handoff, que pertencem aos BACKLOG-0007 e BACKLOG-0004.

#### Atores

- **Operador do pipeline**: executa a validação e decide aprovar ou não a base antes do consumo.
- **Equipe de consultoria**: audiência da demonstração; consome o relatório legível como evidência.
- **Backend do projeto-mãe**: consumidor programático do módulo e do JSON de resultado, a partir do BACKLOG-0008.

### 4. Princípios e restrições do projeto

- **PR-001**: a validação é somente leitura; nenhum caminho de execução envia escrita ou remoção ao destino.
- **PR-002**: o acesso ao destino ocorre exclusivamente pelos contratos de `src/providers/`; nenhum SDK de provider é importado fora desse pacote.
- **PR-003**: validação local completa precede qualquer acesso remoto, preservando o fail-closed da SPEC-0001 e da SPEC-0003.
- **PR-004**: relatório, JSON e log não contêm credenciais, tokens ou URLs de destino, conforme a seção Operação de `.specsfy/RULES.md`.
- **PR-005**: nenhum identificador de cliente, coleção ou pergunta de negócio fica fixo em código; a entrada vem da configuração da base.

### 5. Histórias de usuário

#### US-001 — Aprovar uma base antes do consumo (P1)

Como operador do pipeline, quero executar um comando único que aprove ou reprove a base indexada, para liberar seu consumo por aplicações RAG com evidência e sem risco de alteração.

**Por que P1**: nenhuma execução real foi observada desde a troca da camada de providers; sem esse veredito a demonstração do BACKLOG-0008 se apoia em suposição.
**Teste independente**: executar o comando sobre uma base íntegra e observar aprovação com código `0`, e sobre um ambiente sem credencial e observar código `2`.
**Requisitos**: FR-001, FR-002, FR-005, FR-006, FR-007, NFR-002, NFR-003, NFR-004

#### US-002 — Diagnosticar divergência entre manifesto e destino (P1)

Como operador do pipeline, quero saber exatamente quais chunks faltam e quais sobram no destino, para corrigir a indexação em vez de descobrir o problema durante uma consulta real.

**Por que P1**: indexação parcial e resíduo de execução antiga são silenciosos; contagem agregada não os revela.
**Teste independente**: remover um identificador do destino simulado e observar a reprovação com o faltante nomeado.
**Requisitos**: FR-003, FR-005, FR-006, NFR-001

#### US-003 — Comprovar o comportamento de recuperação (P1)

Como operador do pipeline, quero um roteiro de consultas com gabarito que prove que perguntas amplas, específicas e sem resposta se comportam como esperado, para demonstrar a base à equipe com um resultado verificável.

**Por que P1**: identidade correta não garante recuperação útil; é o comportamento que será apresentado.
**Teste independente**: executar o gabarito de uma base e observar cada consulta classificada como aprovada ou reprovada conforme sua categoria.
**Requisitos**: FR-004, FR-005, FR-006, FR-007

### 6. Cenários BDD de aceite

#### AC-001 — Base íntegra é aprovada

**Cobre**: US-001, FR-001, FR-005, FR-006, NFR-002

```gherkin
@US-001 @FR-001 @FR-005 @FR-006 @NFR-002 @AC-001
Feature: Veredito de uma base indexada

  Scenario: Base íntegra é aprovada
    Given um manifesto e um destino com exatamente os mesmos chunk_ids
    And um gabarito cujas consultas atendem ao que declaram
    When o operador executa a validação apontando para o config da base
    Then o relatório aprova a base
    And o resultado estruturado é gravado no diretório de saída
    And o comando encerra com código 0
```

#### AC-002 — Configuração incompleta falha antes do destino

**Cobre**: US-001, FR-001, FR-006, NFR-004

```gherkin
@US-001 @FR-001 @FR-006 @NFR-004 @AC-002
Feature: Entrada exclusiva pela configuração da base

  Scenario: Configuração sem gabarito declarado
    Given um config.yaml sem caminhos.consultas_referencia
    When o operador executa a validação
    Then o comando encerra com código 2
    And nenhum adapter de destino chega a ser criado
```

#### AC-003 — Preflight reprova ambiente indisponível

**Cobre**: US-001, FR-002, FR-006, NFR-003, NFR-004

```gherkin
@US-001 @FR-002 @FR-006 @NFR-003 @NFR-004 @AC-003
Feature: Preflight de ambiente

  Scenario: Dimensão do destino divergente da configurada
    Given um destino cujo escopo declara dimensão diferente de embedding.dimensions
    When o operador executa a validação
    Then o comando encerra com código 2
    And nenhuma consulta é executada
    And o destino não é preparado nem criado
    And a mensagem de erro não contém credenciais nem a URL do destino
```

#### AC-004 — Gabarito malformado bloqueia antes do acesso remoto

**Cobre**: US-001, FR-002, NFR-004

```gherkin
@US-001 @FR-002 @NFR-004 @AC-004
Feature: Validação local antes do acesso remoto

  Scenario: Gabarito com entrada sem categoria declarada
    Given um gabarito cuja primeira consulta não declara categoria
    When o operador executa a validação
    Then o comando encerra com código 2
    And nenhuma chamada remota é registrada
```

#### AC-005 — Indexação parcial reprova

**Cobre**: US-002, FR-003, FR-006, NFR-001

```gherkin
@US-002 @FR-003 @FR-006 @NFR-001 @AC-005
Feature: Conferência de identidade

  Scenario: Destino sem parte dos chunk_ids do manifesto
    Given um destino ao qual falta um chunk_id previsto no manifesto
    When o operador executa a validação
    Then o relatório lista o identificador faltante
    And nenhuma tentativa de corrigir o destino é feita
    And o comando encerra com código 1
```

#### AC-006 — Resíduo de execução antiga reprova

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-006
Feature: Conferência de identidade

  Scenario: Escopo com identificador ausente do manifesto
    Given um destino que contém um chunk_id fora do manifesto
    When o operador executa a validação
    Then o relatório lista o identificador órfão
    And o comando encerra com código 1
```

#### AC-007 — Conferência íntegra confirma as contagens

**Cobre**: US-002, FR-003, NFR-001

```gherkin
@US-002 @FR-003 @NFR-001 @AC-007
Feature: Conferência de identidade

  Scenario: Conjuntos idênticos entre manifesto e destino
    Given um manifesto com 208 chunk_ids e um destino com os mesmos identificadores
    When o operador executa a validação
    Then a conferência é aprovada sem faltantes nem órfãos
    And a contagem observada coincide com a do manifesto
    And nenhuma escrita é enviada ao destino
```

#### AC-008 — Consulta específica sem a fonte esperada reprova

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-008
Feature: Roteiro de consultas

  Scenario: Documento esperado ausente entre os resultados
    Given uma consulta específica que declara documento_esperado
    When esse documento não aparece entre os resultados recuperados
    Then a consulta é marcada como reprovada
    And o comando encerra com código 1
```

#### AC-009 — Consulta ampla sem cobertura reprova

**Cobre**: US-003, FR-004

```gherkin
@US-003 @FR-004 @AC-009
Feature: Roteiro de consultas

  Scenario: Fato declarado ausente dos resultados
    Given uma consulta ampla que declara vários itens em deve_conter
    When um desses itens não aparece em nenhum resultado recuperado
    Then a consulta é marcada como reprovada com o item ausente nomeado
    And o comando encerra com código 1
```

#### AC-010 — Consulta sem resposta que responde reprova

**Cobre**: US-003, FR-004, FR-006

```gherkin
@US-003 @FR-004 @FR-006 @AC-010
Feature: Roteiro de consultas

  Scenario: Resultado acima do limiar para pergunta sem resposta
    Given uma consulta declarada na categoria sem resposta
    When algum resultado atinge o limiar mínimo declarado na configuração da base
    Then a consulta é marcada como reprovada
    And o comando encerra com código 1
```

#### AC-011 — Saída dupla e estruturada

**Cobre**: US-001, US-002, US-003, FR-005, NFR-003

```gherkin
@US-001 @US-002 @US-003 @FR-005 @NFR-003 @AC-011
Feature: Relatório e resultado estruturado

  Scenario: Execução concluída produz as duas saídas
    Given uma base validada por completo
    When a execução termina
    Then o relatório legível apresenta preflight, conferência e cada consulta
    And o arquivo JSON contém preflight, faltantes, órfãos, contagens e o resultado consulta a consulta
    And nenhuma das duas saídas contém credenciais ou tokens
```

#### AC-012 — O registro não vaza segredo

**Cobre**: US-001, FR-005, NFR-003

```gherkin
@US-001 @FR-005 @NFR-003 @AC-012
Feature: Registro seguro

  Scenario: Execução com credenciais configuradas
    Given credenciais e URL de destino definidas no ambiente
    When a validação produz relatório, JSON e log
    Then nenhuma dessas saídas contém a chave, o token ou a URL do destino
```

#### AC-013 — Nenhuma escrita, inclusive nos caminhos de falha

**Cobre**: US-002, FR-002, NFR-001

```gherkin
@US-002 @FR-002 @NFR-001 @AC-013
Feature: Acesso somente leitura

  Scenario: Falha durante a conferência
    Given um destino que responde com divergência de identidade
    When a validação percorre preflight, conferência e encerramento
    Then nenhuma chamada de escrita, remoção ou preparação é enviada ao destino
    And o destino permanece inalterado
```

#### AC-014 — Verificação única após a remoção dos protótipos

**Cobre**: US-001, FR-001, FR-007, NFR-002

```gherkin
@US-001 @FR-001 @FR-007 @NFR-002 @AC-014
Feature: Uma única porta de entrada para validar

  Scenario: Protótipos aposentados
    Given a entrega concluída
    When o repositório é inspecionado
    Then scripts/check_qdrant_connection.py e scripts/check_qdrant_search.py não existem
    And nenhum identificador de cliente permanece no código de validação
    And o comando novo é a única ferramenta que valida uma base
```

#### AC-015 — Módulo reaproveitável sem a linha de comando

**Cobre**: US-003, FR-007

```gherkin
@US-003 @FR-007 @AC-015
Feature: Reaproveitamento pelo backend

  Scenario: Chamada direta ao módulo
    Given a configuração de uma base carregada em memória
    When o backend chama a função de validação sem passar pela linha de comando
    Then recebe o resultado estruturado equivalente ao do arquivo JSON
    And o código de saída permanece responsabilidade da camada de linha de comando
```

#### AC-016 — Acesso exclusivo pelos contratos neutros

**Cobre**: FR-007, NFR-002

```gherkin
@FR-007 @NFR-002 @AC-016
Feature: Fronteira de providers preservada

  Scenario: Inspeção estática do código de validação
    Given os módulos de validação entregues
    When os imports são inspecionados
    Then nenhum SDK de vector store ou de embeddings aparece fora de src/providers/
    And o acesso ao destino ocorre por list_ids e query dos contratos neutros
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve oferecer um comando único de validação somente leitura, cuja entrada venha exclusivamente do `config.yaml` da base, com escopo lógico derivado de `projeto.nome` e tenant opcional por argumento.
- **FR-002**: O sistema deve concluir a validação local e o preflight de ambiente antes de qualquer consulta, conferindo conexão autenticada, existência do escopo e compatibilidade de dimensão com `embedding.dimensions`. A conferência ocorre por leitura: o preflight não prepara, cria nem altera coleção, índice ou escopo, e não usa `ensure_ready`. O manifesto é localizado pela mesma resolução de `pipeline.py`, com `caminhos.manifest_file` e recurso ao diretório de `caminhos.chunks_file` quando a chave estiver ausente.
- **FR-003**: O sistema deve comparar o conjunto de `chunk_id` do manifesto com o conjunto devolvido pelo destino no escopo, exigindo igualdade estrita e relatando faltantes e órfãos separadamente.
- **FR-004**: O sistema deve executar cada consulta do gabarito e avaliá-la conforme a categoria declarada: ampla e específica pelos itens de `deve_conter` e por `documento_esperado`, e sem resposta pela ausência de resultado que atinja o limiar mínimo.
- **FR-005**: O sistema deve produzir relatório legível no stdout e resultado estruturado em `output/<base>/validation-<run_id>.json`, contendo preflight, faltantes, órfãos, contagens e o desfecho de cada consulta.
- **FR-006**: O sistema deve encerrar com `0` quando aprovar, `1` quando validar e encontrar divergência e `2` quando não for possível validar.
- **FR-007**: O sistema deve concentrar a lógica em módulo Python reaproveitável sem a camada de linha de comando e remover `scripts/check_qdrant_connection.py` e `scripts/check_qdrant_search.py`.

#### Não funcionais

- **NFR-001**: Nenhuma operação de escrita ou remoção é enviada ao destino em qualquer caminho de execução, incluindo chamadas de preparação como `ensure_ready`, que criam a coleção quando ela não existe. **Verificação**: adapters falsos com contador de preparação em zero e listas de escrita e remoção vazias nos cenários de aprovação, reprovação e impedimento.
- **NFR-002**: O acesso ao destino ocorre apenas pelos contratos de `src/providers/`, sem SDK de provider fora desse pacote. **Verificação**: inspeção estática de imports, no mesmo formato do teste de fronteira existente.
- **NFR-003**: Relatório, JSON e log não contêm credenciais, tokens ou URLs de destino. **Verificação**: inspeção das três saídas em teste com credenciais fictícias definidas.
- **NFR-004**: A validação local completa precede qualquer acesso remoto. **Verificação**: cenários de configuração e gabarito inválidos com contador de chamadas remotas em zero.

#### Erros e casos-limite

- Configuração, manifesto ou gabarito ausente → encerra com `2` antes de qualquer acesso remoto.
- Gabarito malformado, sem categoria ou sem critério declarado → encerra com `2`.
- Credencial ausente, destino inacessível, escopo inexistente ou dimensão divergente → encerra com `2` sem executar consultas e sem criar o escopo ausente.
- Divergência de identidade entre manifesto e destino → encerra com `1`, nomeando faltantes e órfãos.
- Consulta fora do que o gabarito declara → encerra com `1`, nomeando a consulta e o critério não atendido.
- Gabarito sem nenhuma consulta declarada → encerra com `2`, porque não haveria comportamento a comprovar.
- Manifesto de execução diferente da base configurada, detectado por `project_id` ou `collection_name` divergente → encerra com `2`.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Projeto Python gerenciado por uv, com Pytest como runner e módulos em `src/`.
- CLIs vivem na raiz: `pipeline.py`, `search.py`, `chat.py`, `demo_rag.py`, `upsert_from_chunks.py`.
- `src/providers/` concentra contratos neutros, factory e adapters desde a SPEC-0003; `src/safety.py` concentra a política fail-closed desde a SPEC-0001.
- `src/manifest.py` produz o manifesto exportado em `output/<base>/manifest.json`.
- `output/` não é versionado; `documentos/` é versionado.

#### Arquitetura e módulos

- `src/validation.py`: módulo novo com a lógica completa — carregamento e validação do gabarito, preflight, conferência de identidade, execução do roteiro e composição do resultado. Não importa SDK de provider e não escreve no destino.
- `validate.py`: camada de linha de comando na raiz; resolve argumentos, chama o módulo, imprime o relatório, grava o JSON e traduz o resultado em código de saída.
- Reuso: `src/config.py` para carregar a configuração, `src/indexing.py` para compor escopo e adapters, `src/providers/contracts.py` para os tipos neutros, `src/manifest.py` como origem dos identificadores previstos.
- Resolução do manifesto idêntica à de `pipeline.py`: `caminhos.manifest_file` quando declarado, senão `manifest.json` ao lado de `caminhos.chunks_file`. Ler caminho diferente do que o pipeline escreve produziria conferência sobre base errada.
- O caminho de validação não chama `ensure_ready`: no adapter Qdrant essa chamada cria a coleção ausente, o que seria escrita e transformaria escopo inexistente em base vazia aprovada. A existência do escopo é conferida por leitura.
- Ponto de extensão: a função de validação recebe a configuração já carregada e devolve o resultado estruturado, permitindo que o backend do BACKLOG-0008 a chame sem processo externo.

#### Migrations

- Não aplicável; a fatia não possui banco relacional nem schema versionado.

#### Models

- `ValidationReport`: resultado completo de uma execução, com desfecho, preflight, conferência e consultas.
- `ScopeComparison`: previstos, observados, faltantes e órfãos.
- `QueryCase`: uma entrada do gabarito, com pergunta, categoria e critérios declarados.
- `QueryOutcome`: resultado de uma consulta, com aprovação, critérios não atendidos e melhor score observado.
- Todos são estruturas imutáveis em `src/validation.py`, no mesmo estilo dos value objects de `src/providers/contracts.py`.

#### Controllers e casos de uso

- `validate_base(config, *, tenant_id=None) -> ValidationReport`: caso de uso principal, sem efeito colateral além da leitura.
- `load_query_cases(path) -> list[QueryCase]`: carrega e valida o gabarito localmente.
- `compare_scope(manifest, adapter, scope) -> ScopeComparison`: conferência de identidade por `list_ids`.
- `run_query_cases(cases, embeddings, adapter, scope, ...) -> list[QueryOutcome]`: roteiro de consultas.
- `main(argv) -> int` em `validate.py`: única camada que conhece códigos de saída.

#### Views e experiência

- Não aplicável; a saída é relatório de terminal e arquivo JSON.

#### Queries e repositórios

- Leitura de identidade por `VectorStoreAdapter.list_ids(scope)`.
- Recuperação por `VectorStoreAdapter.query(scope, embedding, k)`, com o vetor produzido por `EmbeddingAdapter.embed_query`.
- Nenhuma paginação explícita nesta fatia; o volume atual é de 208 identificadores por escopo.

#### Jobs e processamento assíncrono

- Não aplicável; a execução é síncrona e curta. A execução assíncrona pertence ao BACKLOG-0008.

#### Estrutura de arquivos

```text
specs/defined/0004-validar-recuperacao-operacao/
  spec.md
src/
  validation.py
validate.py
documentos/<base>/consultas.yaml
tests/
  test_validation.py
  test_provider_boundaries.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Gabarito | caminho declarado em `caminhos.consultas_referencia` | lista de consultas; arquivo obrigatório e não vazio | uma base possui um gabarito |
| QueryCase | posição e pergunta | `pergunta`, `categoria` em ampla, específica ou sem resposta, `deve_conter` opcional, `documento_esperado` opcional; categoria obrigatória e ao menos um critério para ampla e específica | pertence a um gabarito |
| ValidationReport | `run_id` do manifesto e instante da execução | desfecho, preflight, comparação de escopo e consultas | referencia um manifesto e um gabarito |
| ScopeComparison | escopo lógico | previstos, observados, faltantes, órfãos; aprovada quando faltantes e órfãos estão vazios | pertence a um relatório |
| QueryOutcome | pergunta | aprovada, critérios não atendidos, melhor score observado | pertence a um relatório |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| ValidationReport | iniciado | validação local falha | impedido | nenhuma chamada remota registrada |
| ValidationReport | iniciado | preflight falha | impedido | nenhuma consulta executada |
| ValidationReport | preflight aprovado | conferência ou consulta reprova | reprovado | destino inalterado |
| ValidationReport | preflight aprovado | conferência e consultas aprovam | aprovado | faltantes e órfãos vazios |
| ValidationReport | impedido, reprovado ou aprovado | encerramento | final | desfecho traduzido em 2, 1 ou 0 |

#### Migração e retenção

- O JSON de resultado é gravado em `output/<base>/`, que não é versionado; a retenção é local e livre, sem limpeza automática nesta fatia.
- O gabarito fica ao lado dos documentos da base, que já são versionados, e não cria exposição nova de dados.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega é um comando de terminal e um módulo Python, sem tela, formulário ou navegação visual. O front que consome este resultado pertence ao BACKLOG-0008.

#### Stack e convenções de interface

- CLI Python existente, mensagens em português e códigos de saída como contrato. `INTERFACE.md` confirma que não existe frontend neste repositório.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- O operador executa o comando no terminal apontando para a configuração da base; o relatório volta no mesmo terminal e o resultado estruturado fica no diretório de saída da base.

#### Menus e navegação principal

- Não aplicável; o comando é acessado diretamente por invocação no terminal, sem menu.

#### Formulários e ações

- Não aplicável; as entradas são o `config.yaml`, o gabarito declarado nele e o argumento opcional de tenant.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável; não existe React neste repositório.

#### Estados e acessibilidade

- Estados do terminal: validação local, preflight, conferência, execução das consultas, aprovação, reprovação com detalhe e impedimento com causa. As mensagens não dependem apenas de cor ou de emoji.

#### Contrato CRUD

- Não aplicável.

#### Revisão visual durante o desenvolvimento

- Não aplicável; nenhuma tarefa desta fatia possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir. Cada tarefa registra `VISUAL: Não aplicável — mudança sem superfície gráfica`.

#### APIs expostas

- `validate_base(config, *, tenant_id=None) -> ValidationReport`: contrato do módulo, consumido pela linha de comando e, futuramente, pelo backend.
- `validate.py --config <caminho> [--tenant <id>]`: contrato de linha de comando, com códigos `0`, `1` e `2`.

#### APIs externas utilizadas

- Nenhuma diretamente. O destino remoto é alcançado apenas pelos adapters existentes em `src/providers/`.

#### Documentação das APIs consultadas

- Nenhuma documentação externa foi consultada nesta fatia.

#### Eventos e outros contratos

- `output/<base>/validation-<run_id>.json`: contrato de saída estruturada consumido pelo BACKLOG-0007 e pelo BACKLOG-0008.
- `caminhos.consultas_referencia` e a seção `validacao` do `config.yaml`: contrato de entrada da base.

### 11. Estratégia TDD

- **Unidade**: carregamento e validação do gabarito, classificação de categoria, avaliação de critérios, comparação de conjuntos e tradução do desfecho em código de saída.
- **Integração/contrato**: módulo de validação contra adapters falsos de vector store e de embeddings, cobrindo aprovação, reprovação e impedimento.
- **BDD/aceite**: os dezesseis cenários da seção 6 informam casos Pytest próprios; não criar arquivos `.feature`.
- **Runner TDD**: Pytest, já adotado pelo projeto.
- **E2E**: execução da linha de comando com dependências falsas, verificando relatório, JSON e código de saída; acesso remoto real não é necessário para o gate.
- **Verificação manual**: uma execução real contra o destino configurado, feita pelo operador, para confirmar o preflight fora do ambiente de teste. É o único item inevitável, porque nenhuma suíte com clientes falsos prova conectividade real.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| AC-001 | AC-001 na seção 6 | caso com marcador `SPECSFY: AC-001` em tests/test_validation.py | Pending | Pending | Pending |
| AC-002 | AC-002 na seção 6 | caso com marcador `SPECSFY: AC-002` em tests/test_validation.py | Pending | Pending | Pending |
| AC-003 | AC-003 na seção 6 | caso com marcador `SPECSFY: AC-003` em tests/test_validation.py | Pending | Pending | Pending |
| AC-004 | AC-004 na seção 6 | caso com marcador `SPECSFY: AC-004` em tests/test_validation.py | Pending | Pending | Pending |
| AC-005 | AC-005 na seção 6 | caso com marcador `SPECSFY: AC-005` em tests/test_validation.py | Pending | Pending | Pending |
| AC-006 | AC-006 na seção 6 | caso com marcador `SPECSFY: AC-006` em tests/test_validation.py | Pending | Pending | Pending |
| AC-007 | AC-007 na seção 6 | caso com marcador `SPECSFY: AC-007` em tests/test_validation.py | Pending | Pending | Pending |
| AC-008 | AC-008 na seção 6 | caso com marcador `SPECSFY: AC-008` em tests/test_validation.py | Pending | Pending | Pending |
| AC-009 | AC-009 na seção 6 | caso com marcador `SPECSFY: AC-009` em tests/test_validation.py | Pending | Pending | Pending |
| AC-010 | AC-010 na seção 6 | caso com marcador `SPECSFY: AC-010` em tests/test_validation.py | Pending | Pending | Pending |
| AC-011 | AC-011 na seção 6 | caso com marcador `SPECSFY: AC-011` em tests/test_validation.py | Pending | Pending | Pending |
| AC-012 | AC-012 na seção 6 | caso com marcador `SPECSFY: AC-012` em tests/test_validation.py | Pending | Pending | Pending |
| AC-013 | AC-013 na seção 6 | caso com marcador `SPECSFY: AC-013` em tests/test_validation.py | Pending | Pending | Pending |
| AC-014 | AC-014 na seção 6 | caso com marcador `SPECSFY: AC-014` em tests/test_provider_boundaries.py | Pending | Pending | Pending |
| AC-015 | AC-015 na seção 6 | caso com marcador `SPECSFY: AC-015` em tests/test_validation.py | Pending | Pending | Pending |
| AC-016 | AC-016 na seção 6 | caso com marcador `SPECSFY: AC-016` em tests/test_provider_boundaries.py | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenários BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| US-001 | AC-001, AC-002, AC-003, AC-004, AC-011, AC-012, AC-014 | Contrato/CLI | `pytest tests/test_validation.py tests/test_provider_boundaries.py` | Pending |
| US-002 | AC-005, AC-006, AC-007, AC-011, AC-013 | Contrato | `pytest tests/test_validation.py` | Pending |
| US-003 | AC-008, AC-009, AC-010, AC-011, AC-015 | Contrato | `pytest tests/test_validation.py` | Pending |
| FR-001 | AC-001, AC-002, AC-014 | Unidade/CLI | `pytest tests/test_validation.py` | Pending |
| FR-002 | AC-003, AC-004, AC-013 | Unidade/segurança | `pytest tests/test_validation.py` | Pending |
| FR-003 | AC-005, AC-006, AC-007 | Contrato | `pytest tests/test_validation.py` | Pending |
| FR-004 | AC-008, AC-009, AC-010 | Contrato | `pytest tests/test_validation.py` | Pending |
| FR-005 | AC-001, AC-011, AC-012 | Contrato/CLI | `pytest tests/test_validation.py` | Pending |
| FR-006 | AC-001, AC-002, AC-003, AC-005, AC-010 | CLI | `pytest tests/test_validation.py` | Pending |
| FR-007 | AC-014, AC-015, AC-016 | Arquitetura | `pytest tests/test_provider_boundaries.py tests/test_validation.py` | Pending |
| NFR-001 | AC-005, AC-007, AC-013 | Segurança | `pytest tests/test_validation.py` com adapters falsos | Pending |
| NFR-002 | AC-001, AC-014, AC-016 | Arquitetura | `pytest tests/test_provider_boundaries.py` | Pending |
| NFR-003 | AC-003, AC-011, AC-012 | Segurança | `pytest tests/test_validation.py` com credenciais fictícias | Pending |
| NFR-004 | AC-002, AC-003, AC-004 | Segurança | `pytest tests/test_validation.py` com contador de chamadas remotas | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY — Passed em 2026-09-01
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0004-validar-recuperacao-operacao/spec.md`; `node .agents/skills/specsfy-04-validate/scripts/review_findings.mjs specs/defined/0004-validar-recuperacao-operacao/spec.md --root .`; `node .agents/skills/specsfy-03-specify/scripts/load_research.mjs specs/defined/0004-validar-recuperacao-operacao/spec.md`
- **Achados**: estrutura `VALID DRAFT` e, após o gate, `READY` no validador estrito; research `PASSED` com um artefato indexado e três claims verificadas; 3 US, 7 FR, 4 NFR, 16 AC e 8 DEC. Cada US, FR e NFR possui pelo menos três AC distintos declarados em `**Cobre**`. Três achados abertos na revisão foram corrigidos antes da aprovação; nenhum `P1 Open` permanece.
- **FIND-SEC-001** [P1] [Resolved] O preflight poderia conferir prontidão chamando `ensure_ready`, que cria a coleção ausente — Refs: FR-002, NFR-001 — Evidence: src/providers/vectorstores/qdrant.py:68 — Effect: escrita em destino durante uma validação declarada somente leitura, e um escopo inexistente seria criado vazio e aprovado em vez de encerrar com código 2 — Suggestion: resolvido proibindo `ensure_ready` no caminho de validação em FR-002 e na seção 8, estendendo NFR-001 às chamadas de preparação e cobrindo o comportamento em AC-003 e AC-013.
- **FIND-ARCH-001** [P2] [Resolved] A spec não declarava como o manifesto é localizado — Refs: FR-002, FR-003 — Evidence: pipeline.py:87 — Effect: a validação poderia ler um manifesto diferente do que o pipeline escreve, conferindo identidades da base errada — Suggestion: resolvido exigindo em FR-002 e na seção 8 a mesma resolução de `pipeline.py`, com `caminhos.manifest_file` e recurso ao diretório de `caminhos.chunks_file`.
- **FIND-PROD-001** [P2] [Resolved] A Definition of Done exige execução real observada, mas a seção 16 não listava acesso ao destino como dependência — Refs: FR-002 — Evidence: specs/defined/0004-validar-recuperacao-operacao/spec.md:18 — Effect: o Delivery Gate poderia ficar bloqueado por indisponibilidade de ambiente sem que a spec tivesse previsto a dependência — Suggestion: resolvido declarando credenciais válidas e destino acessível como dependência exclusiva da evidência manual, deixando explícito que a suíte automatizada não depende de rede.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0004-validar-recuperacao-operacao/spec.md`
- **Achados**: Pending; a seção 14 ainda não foi decomposta.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0004-validar-recuperacao-operacao/spec.md .`
- **Achados**: Pending.

### 14. Tarefas

Formato:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Checklist obrigatório por tarefa, na ordem `PREP`, `EXECUTE`, `VERIFY`,
`VISUAL`, `EVIDENCE` e `IMPROVE`. Esta fatia não possui superfície gráfica,
portanto cada `VISUAL` registra `Não aplicável` com o motivo concreto.

#### Fase 0 — Setup mínimo

- [ ] T001 [OPS] Declarar `caminhos.consultas_referencia` e a seção `validacao` com `limiar_minimo` e `top_k` em config.yaml — Refs: FR-001, FR-004 — Depends: none
  - [ ] **PREP**: Ler a seção `caminhos` atual de config.yaml e a resolução de manifesto em pipeline.py:87 para não colidir com chave existente.
  - [ ] **EXECUTE**: Acrescentar as chaves comentadas em config.yaml, com o caminho do gabarito da base ativa e os valores iniciais de limiar e top_k.
  - [ ] **VERIFY**: Carregar o arquivo com `uv run python -c "from src.config import load_config; load_config()"` e conferir as chaves novas.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar o comando e o trecho de configuração adicionado.
  - [ ] **IMPROVE**: Registrar melhoria aplicada nos comentários do arquivo ou justificar nenhuma.

#### Fase 1 — RED TDD informado pelo BDD

- [ ] T002 [TEST] [TDD] Derivar do AC-001 um caso Pytest falhando em tests/test_validation.py, cobrindo base íntegra aprovada com relatório, JSON gravado e código 0 — Refs: US-001, FR-001, FR-005, FR-006, NFR-002, AC-001 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-001 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-001` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_001` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T003 [TEST] [TDD] Derivar do AC-002 um caso Pytest falhando em tests/test_validation.py, cobrindo config sem `caminhos.consultas_referencia` encerrando com código 2 antes de criar adapter — Refs: US-001, FR-001, FR-006, NFR-004, AC-002 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-002 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-002` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_002` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T004 [TEST] [TDD] Derivar do AC-003 um caso Pytest falhando em tests/test_validation.py, cobrindo dimensão divergente encerrando com código 2, sem consulta, sem preparar destino e sem citar a URL — Refs: US-001, FR-002, FR-006, NFR-003, NFR-004, AC-003 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-003 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-003` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_003` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T005 [TEST] [TDD] Derivar do AC-004 um caso Pytest falhando em tests/test_validation.py, cobrindo gabarito com entrada sem categoria encerrando com código 2 e nenhuma chamada remota — Refs: US-001, FR-002, NFR-004, AC-004 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-004 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-004` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_004` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T006 [TEST] [TDD] Derivar do AC-005 um caso Pytest falhando em tests/test_validation.py, cobrindo chunk_id faltante reprovando com código 1, nomeando o faltante e sem tentar corrigir o destino — Refs: US-002, FR-003, FR-006, NFR-001, AC-005 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-005 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-005` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_005` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T007 [TEST] [TDD] Derivar do AC-006 um caso Pytest falhando em tests/test_validation.py, cobrindo chunk_id órfão no escopo reprovando com código 1 e nomeando o órfão — Refs: US-002, FR-003, AC-006 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-006 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-006` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_006` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T008 [TEST] [TDD] Derivar do AC-007 um caso Pytest falhando em tests/test_validation.py, cobrindo conjuntos idênticos aprovando a conferência, com contagem coincidente e sem escrita — Refs: US-002, FR-003, NFR-001, AC-007 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-007 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-007` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_007` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T009 [TEST] [TDD] Derivar do AC-008 um caso Pytest falhando em tests/test_validation.py, cobrindo consulta específica sem o documento_esperado nos resultados reprovando — Refs: US-003, FR-004, AC-008 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-008 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-008` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_008` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T010 [TEST] [TDD] Derivar do AC-009 um caso Pytest falhando em tests/test_validation.py, cobrindo item de deve_conter ausente reprovando a consulta ampla e nomeando o item — Refs: US-003, FR-004, AC-009 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-009 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-009` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_009` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T011 [TEST] [TDD] Derivar do AC-010 um caso Pytest falhando em tests/test_validation.py, cobrindo resultado acima do limiar em consulta sem resposta reprovando com código 1 — Refs: US-003, FR-004, FR-006, AC-010 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-010 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-010` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_010` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T012 [TEST] [TDD] Derivar do AC-011 um caso Pytest falhando em tests/test_validation.py, cobrindo relatório e JSON contendo preflight, conferência e cada consulta, sem credenciais — Refs: US-001, US-002, US-003, FR-005, NFR-003, AC-011 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-011 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-011` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_011` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T013 [TEST] [TDD] Derivar do AC-012 um caso Pytest falhando em tests/test_validation.py, cobrindo relatório, JSON e log livres de chave, token e URL de destino — Refs: US-001, FR-005, NFR-003, AC-012 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-012 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-012` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_012` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T014 [TEST] [TDD] Derivar do AC-013 um caso Pytest falhando em tests/test_validation.py, cobrindo nenhuma escrita, remoção ou preparação enviada ao destino no caminho de falha — Refs: US-002, FR-002, NFR-001, AC-013 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-013 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-013` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_013` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T015 [TEST] [TDD] Derivar do AC-014 um caso Pytest falhando em tests/test_provider_boundaries.py, cobrindo ausência dos dois protótipos e de identificador de cliente no código de validação — Refs: US-001, FR-001, FR-007, NFR-002, AC-014 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-014 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-014` em tests/test_provider_boundaries.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_provider_boundaries.py -k ac_014` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T016 [TEST] [TDD] Derivar do AC-015 um caso Pytest falhando em tests/test_validation.py, cobrindo módulo chamável sem a camada de linha de comando devolvendo resultado equivalente — Refs: US-003, FR-007, AC-015 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-015 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-015` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k ac_015` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.
- [ ] T017 [TEST] [TDD] Derivar do AC-016 um caso Pytest falhando em tests/test_provider_boundaries.py, cobrindo imports sem SDK de provider fora de src/providers/ no código de validação — Refs: FR-007, NFR-002, AC-016 — Depends: none
  - [ ] **PREP**: Ler o Gherkin do AC-016 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-016` em tests/test_provider_boundaries.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_provider_boundaries.py -k ac_016` e observar RED válido.
  - [ ] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [ ] **EVIDENCE**: Registrar o comando e a causa do RED na seção 11.
  - [ ] **IMPROVE**: Revisar a cobertura do cenário e registrar o aprendizado ou a ausência de melhoria.

#### Fase 2 — Fundação e implementação

- [ ] T018 [CODE] Implementar modelos e carregamento validado do gabarito em src/validation.py — Refs: FR-001, FR-004, NFR-004, AC-002, AC-004, AC-009 — Depends: T003, T005, T010
  - [ ] **PREP**: Confirmar RED de T003, T005 e T010 e reconstruir docs/ com `$specsfy-documentator` antes de editar.
  - [ ] **EXECUTE**: Criar `QueryCase`, `ValidationReport`, `ScopeComparison` e `QueryOutcome` e a leitura do gabarito, com validação local de categoria e critérios.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k "ac_002 or ac_004 or ac_009"` e observar GREEN.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar GREEN, arquivos alterados e IDs cobertos nas seções 11 e 12.
  - [ ] **IMPROVE**: Aplicar melhoria concreta no código entregue ou justificar a ausência.
  <!-- specsfy:evidence {"task":"T018","refs":["FR-001", "FR-004", "NFR-004", "AC-002", "AC-004", "AC-009"],"files":["src/validation.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_002 or ac_004 or ac_009\"","exit":0}]} -->
- [ ] T019 [CODE] Implementar o preflight sem preparação de destino em src/validation.py — Refs: FR-002, NFR-001, NFR-003, NFR-004, AC-003, AC-004, AC-013 — Depends: T004, T005, T014, T018
  - [ ] **PREP**: Confirmar RED de T004, T005 e T014 e reler qdrant.py:68 para não usar `ensure_ready` no caminho de leitura.
  - [ ] **EXECUTE**: Implementar conexão, existência do escopo por leitura e conferência de dimensão, encerrando com impedimento sem criar coleção.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k "ac_003 or ac_004 or ac_013"` e conferir contador de preparação em zero.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar GREEN, arquivos alterados e IDs cobertos nas seções 11 e 12.
  - [ ] **IMPROVE**: Aplicar melhoria concreta no código entregue ou justificar a ausência.
  <!-- specsfy:evidence {"task":"T019","refs":["FR-002", "NFR-001", "NFR-003", "NFR-004", "AC-003", "AC-004", "AC-013"],"files":["src/validation.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_003 or ac_004 or ac_013\"","exit":0}]} -->
- [ ] T020 [CODE] Implementar a conferência de identidade em src/validation.py — Refs: FR-003, NFR-001, AC-005, AC-006, AC-007 — Depends: T006, T007, T008, T019
  - [ ] **PREP**: Confirmar RED de T006, T007 e T008 e a resolução do manifesto declarada em FR-002.
  - [ ] **EXECUTE**: Comparar o conjunto de chunk_id do manifesto com `list_ids` do escopo, produzindo faltantes, órfãos e contagens.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k "ac_005 or ac_006 or ac_007"` e observar GREEN.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar GREEN, arquivos alterados e IDs cobertos nas seções 11 e 12.
  - [ ] **IMPROVE**: Aplicar melhoria concreta no código entregue ou justificar a ausência.
  <!-- specsfy:evidence {"task":"T020","refs":["FR-003", "NFR-001", "AC-005", "AC-006", "AC-007"],"files":["src/validation.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_005 or ac_006 or ac_007\"","exit":0}]} -->
- [ ] T021 [CODE] Implementar o roteiro de consultas por categoria em src/validation.py — Refs: FR-004, FR-006, AC-008, AC-009, AC-010 — Depends: T009, T010, T011, T020
  - [ ] **PREP**: Confirmar RED de T009, T010 e T011 e o contrato `query(scope, embedding, k)` dos adapters.
  - [ ] **EXECUTE**: Avaliar cada consulta pela categoria declarada, aplicando deve_conter, documento_esperado e o limiar mínimo da base.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k "ac_008 or ac_009 or ac_010"` e observar GREEN.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar GREEN, arquivos alterados e IDs cobertos nas seções 11 e 12.
  - [ ] **IMPROVE**: Aplicar melhoria concreta no código entregue ou justificar a ausência.
  <!-- specsfy:evidence {"task":"T021","refs":["FR-004", "FR-006", "AC-008", "AC-009", "AC-010"],"files":["src/validation.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_008 or ac_009 or ac_010\"","exit":0}]} -->
- [ ] T022 [CODE] Implementar relatório legível, JSON de resultado e a API do módulo em src/validation.py — Refs: FR-005, FR-007, NFR-003, AC-011, AC-012, AC-015 — Depends: T012, T013, T016, T021
  - [ ] **PREP**: Confirmar RED de T012, T013 e T016 e a regra de Operação de .specsfy/RULES.md sobre registro sem segredo.
  - [ ] **EXECUTE**: Compor o relatório legível e o JSON em output/<base>/validation-<run_id>.json e expor `validate_base` chamável sem a linha de comando.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k "ac_011 or ac_012 or ac_015"` e inspecionar as saídas geradas.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar GREEN, arquivos alterados e IDs cobertos nas seções 11 e 12.
  - [ ] **IMPROVE**: Aplicar melhoria concreta no código entregue ou justificar a ausência.
  <!-- specsfy:evidence {"task":"T022","refs":["FR-005", "FR-007", "NFR-003", "AC-011", "AC-012", "AC-015"],"files":["src/validation.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_011 or ac_012 or ac_015\"","exit":0}]} -->
- [ ] T023 [CODE] Implementar a camada de linha de comando e os desfechos em validate.py — Refs: US-001, FR-001, FR-006, AC-001, AC-002, AC-010 — Depends: T002, T003, T011, T022
  - [ ] **PREP**: Confirmar RED de T002, T003 e T011 e a convenção de argumentos de pipeline.py e search.py.
  - [ ] **EXECUTE**: Implementar `--config` e `--tenant`, a impressão do relatório e a tradução do desfecho em 0, 1 ou 2.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_validation.py -k "ac_001 or ac_002 or ac_010"` e conferir os três códigos de saída.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar GREEN, arquivos alterados e IDs cobertos nas seções 11 e 12.
  - [ ] **IMPROVE**: Aplicar melhoria concreta no código entregue ou justificar a ausência.
  <!-- specsfy:evidence {"task":"T023","refs":["US-001", "FR-001", "FR-006", "AC-001", "AC-002", "AC-010"],"files":["validate.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_001 or ac_002 or ac_010\"","exit":0}]} -->
- [ ] T024 [CODE] Remover os protótipos de diagnóstico em scripts/check_qdrant_connection.py e scripts/check_qdrant_search.py — Refs: FR-007, NFR-002, AC-001, AC-014, AC-016 — Depends: T002, T015, T017, T023
  - [ ] **PREP**: Confirmar que T023 cobre preflight e consulta e reconstruir docs/ com `$specsfy-documentator` antes de remover.
  - [ ] **EXECUTE**: Apagar os dois arquivos e conferir que nenhum documento ou script restante os referencia.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_provider_boundaries.py` e `uv run pytest` para a regressão completa.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar GREEN, arquivos alterados e IDs cobertos nas seções 11 e 12.
  - [ ] **IMPROVE**: Aplicar melhoria concreta no código entregue ou justificar a ausência.
  <!-- specsfy:evidence {"task":"T024","refs":["FR-007", "NFR-002", "AC-001", "AC-014", "AC-016"],"files":["tests/test_provider_boundaries.py"],"commands":[{"run":"uv run pytest tests/test_provider_boundaries.py","exit":0}]} -->

#### Fase 3 — Gabarito da base

- [ ] T025 [P] [OPS] Redigir o gabarito inicial em documentos/vivo_gold_banda_larga_pf/consultas.yaml — Refs: FR-004, AC-008, AC-009 — Depends: T018
  - [ ] **PREP**: Ler os sete documentos da base e a seção 13 de CONTEXTO_MELHORIA_RECUPERACAO_RAG.md para escolher perguntas representativas.
  - [ ] **EXECUTE**: Escrever ao menos uma consulta de cada categoria, com deve_conter e documento_esperado extraídos do conteúdo real da base.
  - [ ] **VERIFY**: Carregar o arquivo pelo módulo e conferir que todas as entradas passam na validação local.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar o comando de carga e o número de consultas por categoria.
  - [ ] **IMPROVE**: Registrar ajuste aplicado às perguntas após a primeira execução ou justificar nenhum.

#### Fase final — Qualidade e documentação

- [ ] T026 [DOC] Registrar as chaves novas de configuração em .specsfy/STACK.md — Refs: FR-001, FR-004 — Depends: T001, T023
  - [ ] **PREP**: Executar o monitor de contexto e localizar a seção de configuração estrutural de .specsfy/STACK.md.
  - [ ] **EXECUTE**: Descrever `caminhos.consultas_referencia`, `validacao.limiar_minimo` e `validacao.top_k` com sua evidência no repositório.
  - [ ] **VERIFY**: Executar o monitor de contexto novamente e exigir `CURRENT`.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar o comando do monitor e o trecho acrescentado.
  - [ ] **IMPROVE**: Registrar melhoria no texto da stack ou justificar nenhuma.
- [ ] T027 [DOC] Reconstruir docs/ e revisar PROJECT.md após a entrega — Refs: FR-007, NFR-002 — Depends: T024
  - [ ] **PREP**: Confirmar que T024 removeu os protótipos e listar os documentos afetados pela superfície nova.
  - [ ] **EXECUTE**: Executar `$specsfy-documentator` e revisar PROJECT.md quanto à capacidade nova de validação.
  - [ ] **VERIFY**: Executar o monitor de contexto e exigir `CURRENT`.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar o comando, os arquivos reconstruídos e a avaliação de impacto em PROJECT.md.
  - [ ] **IMPROVE**: Registrar melhoria na documentação ou justificar nenhuma.
- [ ] T028 [TEST] Executar regressão e rastreabilidade sobre tests/test_validation.py e a suíte completa — Refs: US-001, US-002, US-003, FR-006, NFR-001 — Depends: T024, T026, T027
  - [ ] **PREP**: Identificar suítes, checks e gates aplicáveis à fatia.
  - [ ] **EXECUTE**: Executar `uv run pytest` e os scripts de rastreabilidade e aceite da spec.
  - [ ] **VERIFY**: Confirmar ausência de gaps, de teste pulado e de marcador órfão desta fatia.
  - [ ] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [ ] **EVIDENCE**: Registrar contagens finais e comandos nas seções 12 e 13.
  - [ ] **IMPROVE**: Registrar a retrospectiva do processo desta fatia.

### 15. Ordem de execução

- Caminho crítico: T001 → (T002…T017 em RED) → T018 → T019 → T020 → T021 → T022 → T023 → T024 → T027 → T028.
- Tarefas paralelas: as dezesseis tarefas de RED não compartilham estado entre si e podem ser materializadas em qualquer ordem dentro da Fase 1; T025 corre em paralelo às tarefas de código porque só escreve o gabarito da base; T026 depende apenas de T001 e T023.
- Estratégia de MVP: T018 a T020 mais T023 já entregam preflight, conferência de identidade e os três desfechos, que é o veredito mínimo útil ao operador. A mesma spec exige o roteiro de consultas, a saída dupla e a remoção dos protótipos antes do Delivery Gate.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0001 concluída: política fail-closed e contagens auditáveis que esta fatia consome sem redefinir.
- SPEC-0003 concluída: contratos neutros, `list_ids` e `query` usados pela conferência e pelo roteiro.
- Uma base já indexada com manifesto correspondente em `output/<base>/manifest.json`.
- Um gabarito redigido para a base validada; sem ele o roteiro de consultas não tem o que comprovar.
- Credenciais válidas e destino acessível no momento da entrega, exigidos apenas pela evidência manual da Definition of Done. A suíte automatizada não depende de rede.

#### Riscos

- `SearchResult.score` é nativo de cada provider → o limiar mínimo vale para o provider configurado naquela base e não é comparável entre Qdrant, ChromaDB e Pinecone; a spec registra isso como limite conhecido, não como defeito.
- Gabarito desatualizado em relação à base → a validação reprova por motivo editorial; o relatório nomeia o critério não atendido para tornar a causa evidente.
- Divergência entre o manifesto local e a execução que realmente indexou o destino → conferência de `project_id` e `collection_name` antes de comparar identidades.
- Volume muito maior que o atual → `list_ids` sem paginação pode ficar caro; irrelevante nos 208 identificadores atuais e registrado para revisão futura.
- Remoção dos protótipos antes do comando novo estar completo → a ordem de execução coloca a remoção depois da cobertura de preflight e consulta.

#### Suposições

- Um `config.yaml` por base e um provider por base.
- O `manifest.json` presente em `output/<base>/` corresponde à última execução daquela base.
- O gabarito é curado à mão pelo operador, não gerado automaticamente.
- O número de resultados por consulta é declarado na seção `validacao` do `config.yaml`, com quatro como valor inicial, seguindo o `k` já usado pelas ferramentas de recuperação. Default reversível.
- O comando vive em `validate.py` na raiz, seguindo a convenção de `pipeline.py`, `search.py` e `chat.py`. Default reversível.

### 17. Decisões

- **DEC-001**: A entrega é um comando único somente leitura, com a lógica em módulo reaproveitável — serve ao operador agora e ao backend do BACKLOG-0008 depois, sem duplicar regra.
- **DEC-002**: A conferência exige igualdade estrita entre conjuntos de `chunk_id`, separando faltantes de órfãos — é a única regra que detecta indexação parcial e resíduo de execução antiga; contagem agregada aprovaria uma base com identidades trocadas.
- **DEC-003**: O gabarito é versionado por base, no formato esboçado na seção 13 de `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md` — reaproveita desenho já existente no projeto e permite aceite objetivo sem LLM.
- **DEC-004**: A saída é dupla, relatório legível e JSON no diretório da base — a alternativa de somente texto obrigaria consumidores a analisar texto livre; somente JSON prejudicaria a leitura durante a demonstração.
- **DEC-005**: Os desfechos são `0`, `1` e `2` — o gate do BACKLOG-0007 precisa distinguir base divergente de ambiente indisponível, e a convenção já existe nos protótipos removidos.
- **DEC-006**: A entrada vem exclusivamente do `config.yaml`, com escopo derivado de `projeto.nome` — evita repetir o hardcode de cliente que motivou o BACKLOG-0004 e permite trocar de base sem tocar em código.
- **DEC-007**: Os dois protótipos são removidos nesta fatia, depois que o comando cobrir preflight e consulta — duas respostas divergentes para "a base está íntegra" é pior que nenhuma.
- **DEC-008**: Uma consulta sem resposta passa quando nenhum resultado atinge `validacao.limiar_minimo` — testa o comportamento desejado de não responder com confiança fora da base; a alternativa sem limiar não detectaria resultado irrelevante com score alto.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Os dezesseis cenários `AC` passam com casos TDD próprios.
- [ ] Cada US, FR e NFR possui pelo menos três cenários e evidência executável.
- [ ] Nenhuma escrita chega ao destino em qualquer caminho, comprovado com adapters falsos.
- [ ] Relatório, JSON e log estão livres de credenciais, tokens e URLs de destino.
- [ ] `scripts/check_qdrant_connection.py` e `scripts/check_qdrant_search.py` foram removidos e nenhum identificador de cliente permanece no código de validação.
- [ ] O módulo de validação é chamável sem a camada de linha de comando.
- [ ] Uma execução real contra o destino configurado foi observada pelo operador e registrada como evidência manual.
- [ ] Pytest completo está verde.
- [ ] `.specsfy/STACK.md` registra as entradas novas de configuração quando aplicável e a documentação foi reconstruída com o monitor de contexto em `CURRENT`.
