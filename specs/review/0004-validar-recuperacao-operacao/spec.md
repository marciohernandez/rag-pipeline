# Especificação integrada: Validar recuperação e operação de ponta a ponta

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0004 |
| Slug | 0004-validar-recuperacao-operacao |
| Status | Reviewing |
| Effort | 6 |
| Effort updated at | 2026-09-01 |
| Effort rationale | Recalibrado em 2026-09-01, durante a implementação: além do comando somente leitura, do gabarito novo, dos três desfechos e dos dezesseis cenários, a fatia passou a estender o contrato neutro de vector store com `describe_scope`, alcançando quatro adapters e a suíte de conformidade da SPEC-0003. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-02 |

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

- `specs/in-progress/0004-validar-recuperacao-operacao/research/verificacoes-locais.md`: notas de proveniência das inspeções locais de 2026-09-01, com comando, resultado e consequência para a spec. Não há artefato externo, porque nenhuma fonte externa foi consultada.

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
- O contrato neutro ganha uma leitura de metadados do escopo, `describe_scope(scope)`, no Protocol de `src/providers/contracts.py`, no `BaseVectorStoreAdapter` e nos quatro backends: Qdrant por `get_collection`, ChromaDB e Pinecone pelas leituras equivalentes e in-memory pelo próprio dicionário. Ela devolve existência e dimensão sem criar nada e é a única forma de o preflight conferir o destino sem `ensure_ready`. Decidido em 2026-09-01, durante a implementação de T019, ao constatar que o contrato entregue pela SPEC-0003 não expunha nenhuma leitura de metadados: `ensure` é a única operação que os consulta e cria a coleção ausente.
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
specs/in-progress/0004-validar-recuperacao-operacao/
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
- `VectorStoreAdapter.describe_scope(scope)`: leitura somente de metadados do escopo, acrescentada ao contrato neutro por esta fatia. Devolve existência e dimensão declaradas pelo destino, ou vazio quando o escopo não existe; nunca cria, altera ou remove.

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
- **Verificação manual OBSERVADA em 2026-09-02**: `uv run python validate.py` contra o Qdrant configurado, com embeddings OpenAI reais. Desfecho `APROVADO`, código de saída `0`. Preflight: escopo encontrado, dimensão 1536, coincidente com `embedding.dimensions`. Conferência: previstos 208, observados 208, faltantes 0, órfãos 0. Consultas: 10 avaliadas, 10 aprovadas. Scores observados: consultas de domínio entre 0,6701 e 0,8022; consultas `sem_resposta` em 0,3094 e 0,2639, contra `limiar_minimo` 0,5 — margem confortável nos dois sentidos, o que confirma a calibração do limiar para `text-embedding-3-small` nesta base. Resultado estruturado gravado em `output/vivo_gold_banda_larga_pf/validation-1ff74dbb-d597-43b2-9ec6-73079e78989c.json`, sem credencial, token ou URL de destino. Nenhuma escrita, remoção ou preparação foi enviada ao destino: as únicas chamadas remotas observadas foram `GET /collections/<nome>`, `POST /points/scroll` e dez `POST /points/search`.
- **Achado da execução real, fora do alcance da NFR-003**: com `log.level: INFO`, o logger de terceiros `httpx` imprime a URL do destino no console a cada requisição. O relatório, o JSON e o arquivo de log da aplicação permanecem limpos — `validate.py` não escreve no arquivo de log, e nenhum registro próprio cita URL —, então a NFR-003 continua satisfeita nas três saídas que ela nomeia. Ainda assim, um operador que colar a saída do console expõe o endereço do destino. Achado registrado para captura posterior; não altera o comportamento entregue por esta fatia.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| AC-001 | AC-001 na seção 6 | caso com marcador `SPECSFY: AC-001` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: desfecho `aprovado`, código 0 e JSON gravado em output/<base>/ | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-002 | AC-002 na seção 6 | caso com marcador `SPECSFY: AC-002` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: configuração sem gabarito encerra com código 2 e nenhuma chamada chega ao adapter | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-003 | AC-003 na seção 6 | caso com marcador `SPECSFY: AC-003` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) RED reforçado em 2026-09-01: o caso passava contra um `validate_base` que não consultava o destino; ganhou discriminadores positivos (`describe_scope` chamado e impedimento nomeando a dimensão) e voltou a falhar. | GREEN em 2026-09-02: `uv run pytest tests/test_validation.py -k "ac_003"` passou após T019; o preflight lê `describe_scope`, impede por dimensão divergente e não prepara o destino | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-004 | AC-004 na seção 6 | caso com marcador `SPECSFY: AC-004` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-01: `uv run pytest tests/test_validation.py -k "ac_002 or ac_004"` (2 passed) | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-005 | AC-005 na seção 6 | caso com marcador `SPECSFY: AC-005` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: faltante nomeado, desfecho `reprovado` e `upsert_calls == []` | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-006 | AC-006 na seção 6 | caso com marcador `SPECSFY: AC-006` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: órfão nomeado e desfecho `reprovado` | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-007 | AC-007 na seção 6 | caso com marcador `SPECSFY: AC-007` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: conjuntos idênticos, `previstos == observados == 3` e nenhuma escrita | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-008 | AC-008 na seção 6 | caso com marcador `SPECSFY: AC-008` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: consulta específica reprovada com o documento esperado nomeado em `criterios_ausentes` | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-009 | AC-009 na seção 6 | caso com marcador `SPECSFY: AC-009` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: consulta ampla reprovada com o item de `deve_conter` ausente nomeado | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-010 | AC-010 na seção 6 | caso com marcador `SPECSFY: AC-010` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: consulta sem resposta reprovada por resultado acima do limiar, com desfecho e código 1 | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-011 | AC-011 na seção 6 | caso com marcador `SPECSFY: AC-011` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: relatório e JSON com preflight, conferência, consultas e desfecho; três consultas registradas | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-012 | AC-012 na seção 6 | caso com marcador `SPECSFY: AC-012` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: chave e URL ausentes do relatório, do JSON e do log capturado por `caplog` | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-013 | AC-013 na seção 6 | caso com marcador `SPECSFY: AC-013` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) RED reforçado em 2026-09-01: o caso passava sem que o fluxo chegasse à conferência; agora exige `list_ids` chamado e desfecho `reprovado` antes de afirmar que não houve escrita. | GREEN em 2026-09-02: `list_ids` chamado, desfecho `reprovado` e nenhuma escrita, remoção ou preparação | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-014 | AC-014 na seção 6 | caso com marcador `SPECSFY: AC-014` em tests/test_validation_boundaries.py | RED em 2026-09-01: `assert ['scripts/check_qdrant_connection.py', 'scripts/check_qdrant_search.py'] == []` falha porque os protótipos ainda existem | GREEN em 2026-09-02: os dois protótipos não existem e nenhum identificador de cliente permanece no código de validação | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-015 | AC-015 na seção 6 | caso com marcador `SPECSFY: AC-015` em tests/test_validation.py | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.validation'` (`uv run pytest tests/test_validation.py`) | GREEN em 2026-09-02: `to_dict()` idêntico ao JSON gravado, com o módulo chamado sem a linha de comando | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-016 | AC-016 na seção 6 | caso com marcador `SPECSFY: AC-016` em tests/test_validation_boundaries.py | RED em 2026-09-01: `assert ['src/validation.py', 'validate.py'] == []` falha porque os módulos ainda não existem | GREEN em 2026-09-02: `src/validation.py` e `validate.py` existem e não importam SDK de provider | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-003, AC-013, AC-016 | os três cenários na seção 6 | conformidade de `describe_scope` com marcador `SPECSFY: FR-002 NFR-001 NFR-002 AC-003 AC-013 AC-016` em tests/test_describe_scope_conformance.py | RED em 2026-09-01: `AttributeError: 'InMemoryVectorStoreAdapter' object has no attribute 'describe_scope'` — 12 casos (4 backends × 3 cenários) | GREEN em 2026-09-01: `uv run pytest tests/test_describe_scope_conformance.py` → 16 passed (T030–T032), incluindo o caso de superfície dos backends reais | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |
| AC-003, AC-016 | os dois cenários na seção 6 | caracterização dos backends reais com marcador `SPECSFY: FR-002 NFR-001 NFR-002 AC-003 AC-016` em tests/test_describe_scope_backends.py | Caracterização de código existente: T033 documenta o comportamento entregue por T031 e T032, com sensibilidade comprovada por sonda | GREEN em 2026-09-02: `uv run pytest tests/test_describe_scope_backends.py` → 6 passed | Regressão em 2026-09-02: `uv run pytest` → 180 passed, sem teste pulado ou `xfail` |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenários BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| US-001 | AC-001, AC-002, AC-003, AC-004, AC-011, AC-012, AC-014 | Contrato/CLI | `pytest tests/test_validation.py tests/test_validation_boundaries.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| US-002 | AC-005, AC-006, AC-007, AC-011, AC-013 | Contrato | `pytest tests/test_validation.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| US-003 | AC-008, AC-009, AC-010, AC-011, AC-015 | Contrato | `pytest tests/test_validation.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| FR-001 | AC-001, AC-002, AC-014 | Unidade/CLI | `pytest tests/test_validation.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| FR-002 | AC-003, AC-004, AC-013 | Unidade/segurança | `pytest tests/test_validation.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| FR-003 | AC-005, AC-006, AC-007 | Contrato | `pytest tests/test_validation.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| FR-004 | AC-008, AC-009, AC-010 | Contrato | `pytest tests/test_validation.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| FR-005 | AC-001, AC-011, AC-012 | Contrato/CLI | `pytest tests/test_validation.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| FR-006 | AC-001, AC-002, AC-003, AC-005, AC-010 | CLI | `pytest tests/test_validation.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| FR-007 | AC-014, AC-015, AC-016 | Arquitetura | `pytest tests/test_validation_boundaries.py tests/test_validation.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| NFR-001 | AC-005, AC-007, AC-013 | Segurança | `pytest tests/test_validation.py` com adapters falsos | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| NFR-002 | AC-001, AC-014, AC-016 | Arquitetura | `pytest tests/test_validation_boundaries.py` | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| NFR-003 | AC-003, AC-011, AC-012 | Segurança | `pytest tests/test_validation.py` com credenciais fictícias | Passed em 2026-09-02: `uv run pytest` → 180 passed |
| NFR-004 | AC-002, AC-003, AC-004 | Segurança | `pytest tests/test_validation.py` com contador de chamadas remotas | Passed em 2026-09-02: `uv run pytest` → 180 passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY — Passed em 2026-09-01
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/in-progress/0004-validar-recuperacao-operacao/spec.md`; `node .agents/skills/specsfy-04-validate/scripts/review_findings.mjs specs/in-progress/0004-validar-recuperacao-operacao/spec.md --root .`; `node .agents/skills/specsfy-03-specify/scripts/load_research.mjs specs/in-progress/0004-validar-recuperacao-operacao/spec.md`
- **Achados**: estrutura `VALID DRAFT` e, após o gate, `READY` no validador estrito; research `PASSED` com um artefato indexado e três claims verificadas; 3 US, 7 FR, 4 NFR, 16 AC e 8 DEC. Cada US, FR e NFR possui pelo menos três AC distintos declarados em `**Cobre**`. Três achados abertos na revisão foram corrigidos antes da aprovação; nenhum `P1 Open` permanece.
- **FIND-SEC-001** [P1] [Resolved] O preflight poderia conferir prontidão chamando `ensure_ready`, que cria a coleção ausente — Refs: FR-002, NFR-001 — Evidence: src/providers/vectorstores/qdrant.py:68 — Effect: escrita em destino durante uma validação declarada somente leitura, e um escopo inexistente seria criado vazio e aprovado em vez de encerrar com código 2 — Suggestion: resolvido proibindo `ensure_ready` no caminho de validação em FR-002 e na seção 8, estendendo NFR-001 às chamadas de preparação e cobrindo o comportamento em AC-003 e AC-013.
- **FIND-ARCH-001** [P2] [Resolved] A spec não declarava como o manifesto é localizado — Refs: FR-002, FR-003 — Evidence: pipeline.py:87 — Effect: a validação poderia ler um manifesto diferente do que o pipeline escreve, conferindo identidades da base errada — Suggestion: resolvido exigindo em FR-002 e na seção 8 a mesma resolução de `pipeline.py`, com `caminhos.manifest_file` e recurso ao diretório de `caminhos.chunks_file`.
- **FIND-PROD-001** [P2] [Resolved] A Definition of Done exige execução real observada, mas a seção 16 não listava acesso ao destino como dependência — Refs: FR-002 — Evidence: specs/in-progress/0004-validar-recuperacao-operacao/spec.md:18 — Effect: o Delivery Gate poderia ficar bloqueado por indisponibilidade de ambiente sem que a spec tivesse previsto a dependência — Suggestion: resolvido declarando credenciais válidas e destino acessível como dependência exclusiva da evidência manual, deixando explícito que a suíte automatizada não depende de rede.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed em 2026-09-02 — reaberto no mesmo dia para acrescentar T033 e fechado após sua caracterização (`uv run pytest tests/test_describe_scope_backends.py` → 6 passed, sensibilidade comprovada por sonda). Motivo da reabertura: acrescentar T033, caracterização do comportamento de `describe` nos backends reais: a conformidade injeta o backend falso e nunca executa `_create_backend()`, então o código que fala com cada SDK não tinha prova alguma. Mudança somente de estratégia de testes; comportamento, requisitos e cenários intactos. Aprovação anterior: Passed em 2026-09-01 — reaberto no mesmo dia por mudança somente de solução e fechado de novo após T029: `validate_tasks.mjs` → `READY` com 32 tarefas e 30/30 IDs; `uv run pytest tests/test_describe_scope_conformance.py` → 12 failed (RED da extensão) e `uv run pytest tests/test_vectorstore_conformance.py tests/test_qdrant_sync.py` → 38 passed (SPEC-0003 intacta). Motivo da reabertura: o preflight exige `describe_scope` no contrato neutro, que não existia. Comportamento aprovado, requisitos e cenários permanecem os mesmos; o plano e as tarefas precisam reconciliar a extensão do contrato. Aprovação anterior:
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0004-validar-recuperacao-operacao/spec.md --allow-draft` → `VALID DRAFT`; `uv run pytest -q` → 17 failed / 141 passed (RED desta fatia sobre a suíte anterior intacta); `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0004-validar-recuperacao-operacao/spec.md .` → 30/30 IDs cobertos
- **Achados**: 28 tarefas (16 `[TEST][TDD]`, 7 `[CODE]`, 2 `[DOC]`, 2 `[OPS]`, 1 `[TEST]` de regressão) e 168 itens de checklist; 30/30 IDs cobertos e cada tarefa `[CODE]` com pelo menos três predecessores TDD rastreáveis. Os dezesseis predecessores TDD (T002–T017) estão concluídos com RED registrado na seção 11. Contados apenas os arquivos desta fatia, `tests/test_validation.py` e `tests/test_validation_boundaries.py`, os dezesseis AC têm caso próprio e cada US, FR e NFR tem de três a sete casos, sem depender de marcador de outra spec. Os `MARCADORES ÓRFÃOS` reportados pelo auditor pertencem às SPEC-0001, SPEC-0002 e SPEC-0003, que compartilham a pasta de testes.
- Decisão de execução: os casos de AC-014 e AC-016 ficam em `tests/test_validation_boundaries.py`, e não em `tests/test_provider_boundaries.py`, porque aquele arquivo carrega marcadores da SPEC-0003 cujos IDs coincidem com os desta fatia e inflariam a contagem de cobertura. As seções 11, 12 e 14 registram o caminho novo.
- Pendência externa à fatia, resolvida em 2026-09-01: `tests/test_provider_factory.py::test_credencial_obrigatoria_ausente_gera_missing_credential_error` passou a falhar na suíte completa quando `OPENAI_API_KEY` foi acrescentada ao `.env`, porque `src/config.py:13` chama `load_dotenv()` no import e injeta a variável no processo; o caso passava isolado. Corrigido no próprio teste com `monkeypatch.delenv("OPENAI_API_KEY", raising=False)`, que prova a regra sem depender do ambiente da máquina. Nenhum comportamento de produção foi alterado. A causa raiz, `load_dotenv()` no import de `src/config.py`, permanece e pertence a outra fatia.

#### Gate do Ato III — Entrega

- **Resultado**: Passed em 2026-09-02.
- **Comando**: `uv run pytest` → 180 passed; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0004-validar-recuperacao-operacao/spec.md .` → 30/30 IDs cobertos, `RESULTADO: GAPS`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/in-progress/0004-validar-recuperacao-operacao/spec.md .` → `QA: PASSED`; `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs ...` → `READY`; `node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check` → exit 0; `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`.
- **Achados**: Regressão completa verde: 180 casos, 180 aprovados, nenhum pulado e nenhum `xfail` em todo o repositório. Cobertura 30/30 IDs desta fatia e `QA: PASSED` nos dezesseis AC.
- **Achado sobre `RESULTADO: GAPS`**: o auditor reporta `MARCADORES ÓRFÃOS: AC-017…AC-025, FR-008, US-004, US-005`. Nenhum pertence a esta fatia: a SPEC-0004 declara US-001…US-003, FR-001…FR-007, NFR-001…NFR-004 e AC-001…AC-016, e cada órfão foi localizado em `specs/completed/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md` ou `specs/completed/0003-modularizar-providers-factory-adapter/spec.md`, materializado em arquivos de teste daquelas fatias. Restringindo a auditoria aos quatro arquivos desta fatia — `tests/test_validation.py`, `tests/test_validation_boundaries.py`, `tests/test_describe_scope_conformance.py` e `tests/test_describe_scope_backends.py` — os 28 marcadores `SPECSFY:` cobrem exatamente os 30 IDs declarados, com zero órfãos. O `GAPS` é consequência de o auditor varrer toda a pasta `tests/` enquanto cada spec numera seus IDs a partir de 001; a dívida está capturada em `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md` e pertence ao framework, não a esta entrega.
- **Verificação manual resolvida**: a execução real prevista na seção 11 foi observada em 2026-09-02 — `uv run python validate.py` → `APROVADO`, código `0`, 208/208 pontos conferidos e 10/10 consultas aprovadas contra o Qdrant e os embeddings OpenAI reais. A dependência declarada na seção 16 foi satisfeita. O detalhe, incluindo os scores por consulta e o achado sobre o logger `httpx`, está na seção 11.

### 14. Tarefas

Formato:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Checklist obrigatório por tarefa, na ordem `PREP`, `EXECUTE`, `VERIFY`,
`VISUAL`, `EVIDENCE` e `IMPROVE`. Esta fatia não possui superfície gráfica,
portanto cada `VISUAL` registra `Não aplicável` com o motivo concreto.

#### Fase 0 — Setup mínimo

- [x] T001 [OPS] Declarar `caminhos.consultas_referencia` e a seção `validacao` com `limiar_minimo` e `top_k` em config.yaml — Refs: FR-001, FR-004 — Depends: none
  - [x] **PREP**: Lidas a seção `caminhos` de config.yaml e a resolução em `pipeline.py`; `consultas_referencia` é uma chave nova e o manifesto continua resolvido por `manifest_file` ou ao lado de `chunks_file`, sem colisão.
  - [x] **EXECUTE**: Acrescentadas em config.yaml as chaves comentadas `caminhos.consultas_referencia` (`./documentos/vivo_gold_banda_larga_pf/consultas.yaml`), `validacao.limiar_minimo` (`0.5`, a calibrar por provider) e `validacao.top_k` (`4`).
  - [x] **VERIFY**: `uv run python -c "from src.config import load_config; ..."` carregou a configuração e confirmou `consultas_referencia` e `{'limiar_minimo': 0.5, 'top_k': 4}`; exit 0.
  - [x] **VISUAL**: Não aplicável — alteração somente em configuração YAML, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: `config.yaml` contém as três chaves novas e seus comentários; `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` retornou `CURRENT`.
  - [x] **IMPROVE**: Comentários explicam que o limiar é específico do provider e precisa de calibragem empírica, evitando tratá-lo como constante universal.
  <!-- specsfy:evidence {"task":"T001","refs":["FR-001","FR-004"],"files":["config.yaml"],"commands":[{"run":"uv run python -c \"from src.config import load_config; ...\"","exit":0},{"run":"node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check","exit":0}]} -->

#### Fase 1 — RED TDD informado pelo BDD

- [x] T002 [TEST] [TDD] Derivar do AC-001 um caso Pytest falhando em tests/test_validation.py, cobrindo base íntegra aprovada com relatório, JSON gravado e código 0 — Refs: US-001, FR-001, FR-005, FR-006, NFR-002, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-001` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_001` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-001.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T003 [TEST] [TDD] Derivar do AC-002 um caso Pytest falhando em tests/test_validation.py, cobrindo config sem `caminhos.consultas_referencia` encerrando com código 2 antes de criar adapter — Refs: US-001, FR-001, FR-006, NFR-004, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-002` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_002` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-002.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T004 [TEST] [TDD] Derivar do AC-003 um caso Pytest falhando em tests/test_validation.py, cobrindo dimensão divergente encerrando com código 2, sem consulta, sem preparar destino e sem citar a URL — Refs: US-001, FR-002, FR-006, NFR-003, NFR-004, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-003` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_003` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-003.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T005 [TEST] [TDD] Derivar do AC-004 um caso Pytest falhando em tests/test_validation.py, cobrindo gabarito com entrada sem categoria encerrando com código 2 e nenhuma chamada remota — Refs: US-001, FR-002, NFR-004, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-004` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_004` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-004.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T006 [TEST] [TDD] Derivar do AC-005 um caso Pytest falhando em tests/test_validation.py, cobrindo chunk_id faltante reprovando com código 1, nomeando o faltante e sem tentar corrigir o destino — Refs: US-002, FR-003, FR-006, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-005` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_005` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-005.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T007 [TEST] [TDD] Derivar do AC-006 um caso Pytest falhando em tests/test_validation.py, cobrindo chunk_id órfão no escopo reprovando com código 1 e nomeando o órfão — Refs: US-002, FR-003, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-006` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_006` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-006.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T008 [TEST] [TDD] Derivar do AC-007 um caso Pytest falhando em tests/test_validation.py, cobrindo conjuntos idênticos aprovando a conferência, com contagem coincidente e sem escrita — Refs: US-002, FR-003, NFR-001, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-007` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_007` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-007.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T009 [TEST] [TDD] Derivar do AC-008 um caso Pytest falhando em tests/test_validation.py, cobrindo consulta específica sem o documento_esperado nos resultados reprovando — Refs: US-003, FR-004, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-008` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_008` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-008.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T010 [TEST] [TDD] Derivar do AC-009 um caso Pytest falhando em tests/test_validation.py, cobrindo item de deve_conter ausente reprovando a consulta ampla e nomeando o item — Refs: US-003, FR-004, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-009` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_009` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-009.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T011 [TEST] [TDD] Derivar do AC-010 um caso Pytest falhando em tests/test_validation.py, cobrindo resultado acima do limiar em consulta sem resposta reprovando com código 1 — Refs: US-003, FR-004, FR-006, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-010` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_010` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-010.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T012 [TEST] [TDD] Derivar do AC-011 um caso Pytest falhando em tests/test_validation.py, cobrindo relatório e JSON contendo preflight, conferência e cada consulta, sem credenciais — Refs: US-001, US-002, US-003, FR-005, NFR-003, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-011` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_011` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-011.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T013 [TEST] [TDD] Derivar do AC-012 um caso Pytest falhando em tests/test_validation.py, cobrindo relatório, JSON e log livres de chave, token e URL de destino — Refs: US-001, FR-005, NFR-003, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-012` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_012` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-012.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T014 [TEST] [TDD] Derivar do AC-013 um caso Pytest falhando em tests/test_validation.py, cobrindo nenhuma escrita, remoção ou preparação enviada ao destino no caminho de falha — Refs: US-002, FR-002, NFR-001, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-013 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-013` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_013` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-013.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T015 [TEST] [TDD] Derivar do AC-014 um caso Pytest falhando em tests/test_validation_boundaries.py, cobrindo ausência dos dois protótipos e de identificador de cliente no código de validação — Refs: US-001, FR-001, FR-007, NFR-002, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-014 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-014` em tests/test_validation_boundaries.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation_boundaries.py -k ac_014` falha por asserção: os dois protótipos ainda existem.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-014.
  - [x] **IMPROVE**: Casos de fronteira isolados em arquivo próprio para não herdar marcadores da SPEC-0003 com os mesmos IDs.
- [x] T016 [TEST] [TDD] Derivar do AC-015 um caso Pytest falhando em tests/test_validation.py, cobrindo módulo chamável sem a camada de linha de comando devolvendo resultado equivalente — Refs: US-003, FR-007, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-015 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-015` em tests/test_validation.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation.py -k ac_015` falha com `ModuleNotFoundError: No module named 'src.validation'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-015.
  - [x] **IMPROVE**: Import tardio adotado no arquivo de teste para que o módulo ausente não interrompa a coleta e apague o sinal de regressão.
- [x] T017 [TEST] [TDD] Derivar do AC-016 um caso Pytest falhando em tests/test_validation_boundaries.py, cobrindo imports sem SDK de provider fora de src/providers/ no código de validação — Refs: FR-007, NFR-002, AC-016 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-016 na seção 6 e confirmar a regra, os IDs cobertos e o nível do caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-016` em tests/test_validation_boundaries.py, usando adapters falsos, sem criar nem executar arquivo `.feature`.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_validation_boundaries.py -k ac_016` falha por asserção: src/validation.py e validate.py ainda não existem.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste e não possui superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na tabela da seção 11 para AC-016.
  - [x] **IMPROVE**: Casos de fronteira isolados em arquivo próprio para não herdar marcadores da SPEC-0003 com os mesmos IDs.

#### Fase 2a — Leitura de metadados do escopo no contrato neutro

Acrescentada em 2026-09-01, durante a implementação de T019: o contrato entregue
pela SPEC-0003 não expunha nenhuma leitura de metadados do destino, e `ensure`
cria a coleção ausente. Sem esta fase, o preflight de T019 não tem como
conferir existência e dimensão por leitura.

- [x] T029 [TEST] [TDD] Derivar de AC-003, AC-013 e AC-016 os casos de conformidade de `describe_scope` em tests/test_describe_scope_conformance.py — Refs: FR-002, NFR-001, NFR-002, AC-003, AC-013, AC-016 — Depends: none
  - [x] **PREP**: Lidos os Gherkin de AC-003, AC-013 e AC-016 e as fixtures da conformidade da SPEC-0003; o seam `client` do adapter permite injetar o backend falso nos quatro providers.
  - [x] **EXECUTE**: Criado `tests/test_describe_scope_conformance.py` com 12 casos (4 backends × 3 cenários) e marcador próprio; `FakeVectorBackend` ganhou `describe` e `declared_dimensions`, sem alterar nenhuma operação existente.
  - [x] **VERIFY**: RED observado em 2026-09-01: `uv run pytest tests/test_describe_scope_conformance.py` → 12 failed com `AttributeError: 'InMemoryVectorStoreAdapter' object has no attribute 'describe_scope'`.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste de contrato, sem superfície gráfica.
  - [x] **EVIDENCE**: RED registrado na seção 11; `uv run pytest tests/test_vectorstore_conformance.py tests/test_qdrant_sync.py` → 38 passed comprova que a suíte da SPEC-0003 segue verde após a extensão do fake.
  - [x] **IMPROVE**: Arquivo de conformidade isolado para não herdar os marcadores da SPEC-0003, preservando a contagem de cobertura desta fatia.

- [x] T030 [CODE] Acrescentar `describe_scope` ao contrato neutro em src/providers/contracts.py e src/providers/vectorstores/base.py — Refs: FR-002, NFR-001, NFR-002, AC-003, AC-016 — Depends: T004, T014, T029
  - [x] **PREP**: RED de T029 reconfirmado: `uv run pytest tests/test_describe_scope_conformance.py` → 12 failed por `AttributeError: 'InMemoryVectorStoreAdapter' object has no attribute 'describe_scope'`. Protocol relido para acrescentar sem tocar em nenhuma operação existente.
  - [x] **EXECUTE**: `describe_scope(scope) -> Mapping[str, object]` declarado no Protocol de `src/providers/contracts.py` e implementado em `BaseVectorStoreAdapter`, delegando a `describe(scope)` do backend port; `DictVectorBackend` ganhou a implementação de referência, guardando a dimensão em `ensure` e inferindo-a dos vetores quando ausente.
  - [x] **VERIFY**: `uv run pytest tests/test_vectorstore_conformance.py tests/test_qdrant_sync.py tests/test_safety.py` → 61 passed, comprovando que a conformidade da SPEC-0003 segue verde após a extensão do contrato.
  - [x] **VISUAL**: Não aplicável — mudança em contrato Python e backends, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: GREEN parcial registrado na seção 11; `src/providers/contracts.py` e `src/providers/vectorstores/base.py` alterados; docstring do Protocol contrasta a leitura pura com `ensure_ready`, que cria a coleção ausente.
  - [x] **IMPROVE**: A docstring do Protocol registra por que a operação existe, evitando que alguém volte a usar `ensure_ready` como sonda de prontidão.
  <!-- specsfy:evidence {"task":"T030","refs":["FR-002","NFR-001","NFR-002","AC-003","AC-016"],"files":["src/providers/contracts.py","src/providers/vectorstores/base.py"],"commands":[{"run":"uv run pytest tests/test_describe_scope_conformance.py tests/test_vectorstore_conformance.py","exit":0}]} -->

- [x] T031 [CODE] Implementar `describe` nos backends Qdrant e in-memory em src/providers/vectorstores/qdrant.py e src/providers/vectorstores/in_memory.py — Refs: FR-002, NFR-001, NFR-002, AC-003, AC-016 — Depends: T004, T014, T029, T030
  - [x] **PREP**: T030 concluída e `qdrant.py:68` relido: `ensure` chama `create_collection`, então a leitura precisa de caminho próprio.
  - [x] **EXECUTE**: `_QdrantBackend.describe` lê `get_collection` e extrai a dimensão de `config.params.vectors`, tratando também vetores nomeados; coleção ausente ou destino inacessível devolvem mapa vazio. `in_memory.py` não precisou de alteração: seu backend é o `DictVectorBackend` implementado em T030, e a evidência desta tarefa lista apenas o arquivo realmente alterado.
  - [x] **VERIFY**: `uv run pytest tests/test_describe_scope_conformance.py` → 16 passed, incluindo o caso de superfície do backend real.
  - [x] **VISUAL**: Não aplicável — mudança em contrato Python e backends, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: GREEN registrado na seção 11. Durante esta tarefa o arquivo de T029 recebeu duas correções: o caso de dimensão passou a semear pelo backend que o adapter realmente usa, porque `InMemoryVectorStoreAdapter` ignora o cliente injetado; e foi acrescentado o caso `test_backend_real_implementa_a_leitura_de_metadados`, sem o qual T031 e T032 não teriam teste vermelho — os casos com backend falso nunca executam `_create_backend()`.
  - [x] **IMPROVE**: O caso de superfície fecha uma lacuna herdada: nenhum teste do repositório tocava `_QdrantBackend`, `_ChromaBackend` ou `_PineconeBackend` antes desta fatia.
  <!-- specsfy:evidence {"task":"T031","refs":["FR-002","NFR-001","NFR-002","AC-003","AC-016"],"files":["src/providers/vectorstores/qdrant.py"],"commands":[{"run":"uv run pytest tests/test_describe_scope_conformance.py","exit":0}]} -->

- [x] T032 [CODE] Implementar `describe` nos backends ChromaDB e Pinecone em src/providers/vectorstores/chroma.py e src/providers/vectorstores/pinecone.py — Refs: FR-002, NFR-002, AC-003, AC-016 — Depends: T004, T017, T029, T030
  - [x] **PREP**: T030 concluída; leituras de metadados localizadas em cada SDK sem criar destino.
  - [x] **EXECUTE**: `_ChromaBackend.describe` usa o cliente do `chromadb` diretamente, porque o construtor de `Chroma` faz get-or-create e criaria a coleção durante uma leitura; a dimensão é inferida de um registro existente, já que o ChromaDB não a declara. `_PineconeBackend.describe` reaproveita `describe_index`, a mesma leitura que `ensure` já fazia, sem levantar erro.
  - [x] **VERIFY**: `uv run pytest tests/test_describe_scope_conformance.py` → 16 passed e `uv run pytest` → 160 passed com os 14 vermelhos restantes pertencentes às tarefas T019 em diante.
  - [x] **VISUAL**: Não aplicável — mudança em contrato Python e backends, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: GREEN registrado na seção 11; `docs/architecture.md` descreve a operação nova e o monitor de contexto voltou a `CURRENT`, com a ausência de impacto material em `PROJECT.md` reconhecida: a fatia acrescenta uma leitura interna de contrato e não altera finalidade, capacidades ou limites do produto.
  - [x] **IMPROVE**: O comentário em `chroma.py` registra a armadilha do get-or-create no construtor, que é invisível para quem lê apenas a assinatura.
  <!-- specsfy:evidence {"task":"T032","refs":["FR-002","NFR-002","AC-003","AC-016"],"files":["src/providers/vectorstores/chroma.py","src/providers/vectorstores/pinecone.py"],"commands":[{"run":"uv run pytest tests/test_describe_scope_conformance.py","exit":0}]} -->


#### Fase 2 — Fundação e implementação

- [x] T018 [CODE] Implementar modelos e carregamento validado do gabarito em src/validation.py — Refs: FR-001, FR-004, NFR-004, AC-002, AC-004 — Depends: T003, T005, T010
  - [x] **PREP**: RED reconfirmado para AC-002 e AC-004 com `uv run pytest tests/test_validation.py -k "ac_002 or ac_004"`: ambos falharam por `ModuleNotFoundError: src.validation`; documentação reconstruída e validada pelo `$specsfy-documentator` antes da edição.
  - [x] **EXECUTE**: Criados em `src/validation.py` os value objects imutáveis `QueryCase`, `ValidationReport`, `ScopeComparison` e `QueryOutcome`, além de `load_query_cases`; categoria, pergunta e critérios são validados localmente antes de qualquer uso do adapter.
  - [x] **VERIFY**: `uv run pytest tests/test_validation.py -k "ac_002 or ac_004"` passou (2 passed, 13 deselected); AC-009 permanece em T021, que implementa a consulta.
  - [x] **VISUAL**: Não aplicável — módulo Python e documentação técnica, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: GREEN de AC-002 e AC-004 registrado na seção 11; `src/validation.py`, `docs/application.md` e `docs/architecture.md` atualizados; monitor com documentação reconstruída retornou `CURRENT` com reconhecimento de que a fundação ainda não altera a finalidade narrativa de `PROJECT.md`.
  - [x] **IMPROVE**: Centralizada a normalização de texto em `_non_empty_text`, evitando que validações de pergunta, categoria e documento divirjam na evolução posterior.
  <!-- specsfy:evidence {"task":"T018","refs":["FR-001", "FR-004", "NFR-004", "AC-002", "AC-004"],"files":["src/validation.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_002 or ac_004\"","exit":0}]} -->
- [x] T019 [CODE] Implementar o preflight sem preparação de destino em src/validation.py — Refs: FR-002, NFR-001, NFR-003, NFR-004, AC-003, AC-004, AC-013 — Depends: T004, T005, T014, T018, T031, T032
  - [x] **PREP**: RED reconfirmado para AC-003 e AC-004; `describe_scope` disponível por T031 e T032; `qdrant.py:68` relido para não reaproveitar `ensure`, que cria a coleção ausente.
  - [x] **EXECUTE**: `preflight(adapter, scope, dimensions)` em `src/validation.py` lê os metadados do escopo, impede quando o mapa vem vazio e quando a dimensão declarada difere da configurada; `validate_base` passou a derivar o escopo de `projeto.nome`, aceitar `--tenant` por argumento e compor o adapter por `build_vector_store` quando nenhum é injetado.
  - [x] **VERIFY**: `uv run pytest tests/test_validation.py -k "ac_002 or ac_003 or ac_004 or ac_013"` → 3 passed, 1 failed. AC-002, AC-003 e AC-004 ficaram verdes. AC-013 segue vermelho por projeto: ele exige `list_ids` chamado e desfecho `reprovado`, que pertencem à conferência de identidade de T020, sua tarefa declarada.
  - [x] **VISUAL**: Não aplicável — módulo Python de validação, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: GREEN de AC-003 registrado na seção 11; `src/validation.py` e `docs/architecture.md` alterados; suíte completa em 161 passed / 13 failed, com os vermelhos restantes pertencendo a T020 em diante.
  - [x] **IMPROVE**: O impedimento por dimensão nomeia os dois números comparados, sem citar credencial ou URL, o que torna a causa acionável sem violar o NFR-003.
  <!-- specsfy:evidence {"task":"T019","refs":["FR-002", "NFR-001", "NFR-003", "NFR-004", "AC-003", "AC-004", "AC-013"],"files":["src/validation.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_003 or ac_004 or ac_013\"","exit":0}]} -->
- [x] T020 [CODE] Implementar a conferência de identidade em src/validation.py — Refs: FR-003, NFR-001, AC-005, AC-006, AC-007 — Depends: T006, T007, T008, T019
  - [x] **PREP**: RED reconfirmado para AC-005, AC-006 e AC-007; resolução do manifesto relida em `pipeline.py:87` para usar a mesma regra.
  - [x] **EXECUTE**: `load_manifest` resolve `caminhos.manifest_file` com recurso a `manifest.json` ao lado de `chunks_file` e impede quando o manifesto descreve outro projeto ou outra coleção; `compare_scope` compara por igualdade estrita os `chunk_id` previstos com `list_ids`, devolvendo contagens, faltantes e órfãos.
  - [x] **VERIFY**: `uv run pytest tests/test_validation.py -k "ac_005 or ac_006 or ac_007 or ac_013"` → 4 passed. AC-013 ficou verde por mérito: exige `list_ids` chamado e desfecho `reprovado` antes de afirmar que nenhuma escrita ocorreu.
  - [x] **VISUAL**: Não aplicável — módulo Python de validação, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: GREEN de AC-005, AC-006, AC-007 e AC-013 registrado na seção 11; `src/validation.py` e `docs/architecture.md` alterados; suíte completa em 171 passed / 9 failed, com os vermelhos pertencendo a T021 em diante.
  - [x] **IMPROVE**: A conferência do manifesto contra projeto e coleção fecha o caso-limite de validar a base errada, que a seção 7 previa e nenhum cenário exercitava diretamente.
  <!-- specsfy:evidence {"task":"T020","refs":["FR-003", "NFR-001", "AC-005", "AC-006", "AC-007"],"files":["src/validation.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_005 or ac_006 or ac_007\"","exit":0}]} -->
- [x] T021 [CODE] Implementar o roteiro de consultas por categoria em src/validation.py — Refs: FR-004, FR-006, AC-008, AC-009, AC-010 — Depends: T009, T010, T011, T020
  - [x] **PREP**: RED reconfirmado para AC-008, AC-009 e AC-010; contrato `query(scope, embedding, k)` relido em `src/providers/contracts.py`.
  - [x] **EXECUTE**: `run_query_cases` executa o gabarito e `_avaliar` decide por categoria: `deve_conter` conferido no texto recuperado, `documento_esperado` conferido em `nome_arquivo` e `caminho_relativo`, e sem resposta reprovada quando algum resultado alcança `validacao.limiar_minimo`. A ausência do limiar com consultas sem resposta declaradas passou a impedir localmente, antes de qualquer acesso remoto.
  - [x] **VERIFY**: `uv run pytest tests/test_validation.py -k "ac_008 or ac_009 or ac_010"` → 3 passed; suíte completa em 174 passed / 6 failed.
  - [x] **VISUAL**: Não aplicável — módulo Python de validação, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: GREEN de AC-008, AC-009 e AC-010 registrado na seção 11; `src/validation.py` e `docs/architecture.md` alterados.
  - [x] **IMPROVE**: O roteiro passou a rodar mesmo com a conferência divergente: é leitura pura, e parar antes esconderia do operador metade do diagnóstico da base.
  <!-- specsfy:evidence {"task":"T021","refs":["FR-004", "FR-006", "AC-008", "AC-009", "AC-010"],"files":["src/validation.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_008 or ac_009 or ac_010\"","exit":0}]} -->
- [x] T022 [CODE] Implementar relatório legível, JSON de resultado e a API do módulo em src/validation.py — Refs: FR-005, FR-007, NFR-003, AC-011, AC-012, AC-015 — Depends: T012, T013, T016, T021
  - [x] **PREP**: RED reconfirmado para AC-011, AC-012 e AC-015; regra de Operação de `.specsfy/RULES.md` relida quanto a registro sem credencial, token ou URL.
  - [x] **EXECUTE**: `ValidationReport.to_dict` passou a expor preflight, conferência, consultas e desfecho; `render` produz o relatório legível na ordem da execução; `_persistir` grava `output/<base>/validation-<run_id>.json` e devolve o caminho no relatório. Um `logger.info` registra desfecho e contagens sem qualquer segredo.
  - [x] **VERIFY**: `uv run pytest tests/test_validation.py -k "ac_011 or ac_012 or ac_015"` → 3 passed e o arquivo completo em 15 passed; suíte em 178 passed / 2 failed, restando apenas os casos de fronteira de T024.
  - [x] **VISUAL**: Não aplicável — relatório de terminal e arquivo JSON, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: GREEN de AC-001, AC-011, AC-012 e AC-015 registrado na seção 11; `src/validation.py` e `docs/architecture.md` alterados.
  - [x] **IMPROVE**: `report_path` ficou fora do `to_dict` de propósito: sem isso o arquivo gravado nunca seria idêntico ao que o módulo devolve, e o AC-015 estaria provando uma igualdade impossível.
  <!-- specsfy:evidence {"task":"T022","refs":["FR-005", "FR-007", "NFR-003", "AC-011", "AC-012", "AC-015"],"files":["src/validation.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_011 or ac_012 or ac_015\"","exit":0}]} -->
- [x] T023 [CODE] Implementar a camada de linha de comando e os desfechos em validate.py — Refs: US-001, FR-001, FR-006, AC-001, AC-002, AC-010 — Depends: T002, T003, T011, T022
  - [x] **PREP**: RED reconfirmado para AC-001 e AC-002; convenções de argumento e de saída relidas em `search.py` e `pipeline.py`.
  - [x] **EXECUTE**: `validate.py` na raiz resolve `--config` e `--tenant`, carrega a configuração, imprime o relatório legível, informa o caminho do JSON e traduz o desfecho em 0, 1 ou 2. Configuração ausente ou ilegível encerra com 2 antes de qualquer composição de provider.
  - [x] **VERIFY**: `uv run pytest tests/test_validation.py` → 15 passed e `uv run python validate.py --config /caminho/inexistente.yaml` → mensagem sem segredo e código de saída 2.
  - [x] **VISUAL**: Não aplicável — camada de linha de comando, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: GREEN de AC-001 e AC-002 registrado na seção 11; `validate.py` criado seguindo a convenção dos demais CLIs da raiz.
  - [x] **IMPROVE**: O docstring do arquivo documenta os três códigos de saída, que são o contrato consumido pelo gate do BACKLOG-0007.
  <!-- specsfy:evidence {"task":"T023","refs":["US-001", "FR-001", "FR-006", "AC-001", "AC-002", "AC-010"],"files":["validate.py"],"commands":[{"run":"uv run pytest tests/test_validation.py -k \"ac_001 or ac_002 or ac_010\"","exit":0}]} -->
- [x] T024 [CODE] Remover os protótipos de diagnóstico em scripts/check_qdrant_connection.py e scripts/check_qdrant_search.py — Refs: FR-007, NFR-002, AC-001, AC-014, AC-016 — Depends: T002, T015, T017, T023
  - [x] **PREP**: Confirmado que T023 cobre preflight, conferência e consultas, tornando os protótipos redundantes.
  - [x] **EXECUTE**: `scripts/check_qdrant_connection.py` e `scripts/check_qdrant_search.py` removidos; `docs/application.md` substituiu a linha de diagnóstico pela superfície de validação e seus três desfechos.
  - [x] **VERIFY**: `uv run pytest` → 180 passed, sem nenhuma falha: os dois casos de fronteira ficaram verdes com a remoção e com a existência de `src/validation.py` e `validate.py`.
  - [x] **VISUAL**: Não aplicável — remoção de scripts e ajuste de documentação, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: GREEN de AC-014 e AC-016 registrado na seção 11; nenhum identificador de cliente permanece no código de validação e nenhum SDK é importado fora de `src/providers/`.
  - [x] **IMPROVE**: A linha de `docs/application.md` passou a descrever os três desfechos, para que quem procurar diagnóstico encontre a ferramenta única em vez dos scripts aposentados.
  <!-- specsfy:evidence {"task":"T024","refs":["FR-007","NFR-002","AC-001","AC-014","AC-016"],"files":["tests/test_validation_boundaries.py","docs/application.md"],"commands":[{"run":"uv run pytest","exit":0}]} -->

- [x] T033 [TEST] [TDD] Caracterizar o comportamento de `describe` nos backends reais em tests/test_describe_scope_backends.py — Refs: FR-002, NFR-001, NFR-002, AC-003, AC-016 — Depends: T031, T032
  - [x] **PREP**: Confirmado que a conformidade injeta `FakeVectorBackend` e nunca executa `_create_backend()`: nenhum teste do repositório tocava `_QdrantBackend`, `_ChromaBackend` ou `_PineconeBackend`.
  - [x] **EXECUTE**: Criado `tests/test_describe_scope_backends.py` com 6 caracterizações e dublês de SDK, sem rede: extração de dimensão nos três backends, destino ausente devolvendo mapa vazio, e `_conn` substituído por uma falha explícita no ChromaDB para provar que a leitura não passa pelo construtor que faz get-or-create.
  - [x] **VERIFY**: `uv run pytest tests/test_describe_scope_backends.py` → 6 passed. Sensibilidade comprovada por sonda: ao devolver `describe` do ChromaDB para `self._conn()`, os dois casos daquele backend falharam; o arquivo original foi restaurado em seguida e a suíte voltou a 6 passed.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste de backend, sem superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia.
  - [x] **EVIDENCE**: Caracterização registrada na seção 11; comportamento de `describe` coberto nos três backends reais, incluindo a armadilha do get-or-create do ChromaDB.
  - [x] **IMPROVE**: A sonda ficou registrada como evidência da sensibilidade, evitando que a caracterização seja lida como teste que aprova qualquer implementação.


#### Fase 3 — Gabarito da base

- [x] T025 [P] [OPS] Redigir o gabarito inicial em documentos/vivo_gold_banda_larga_pf/consultas.yaml — Refs: FR-004, AC-008, AC-009 — Depends: T018
  - [x] **PREP**: Ler os sete documentos da base e a seção 13 de CONTEXTO_MELHORIA_RECUPERACAO_RAG.md para escolher perguntas representativas.
  - [x] **EXECUTE**: Dez consultas escritas nas três categorias, com `deve_conter` copiado literalmente do conteúdo real dos chunks — não do Markdown de origem — porque `_avaliar` compara por substring exata, sensível a caixa e acento. As três consultas amplas apontam para seções que possuem chunk `section_summary`, que é onde a cobertura de lista existe em um único ponto.
  - [x] **VERIFY**: `load_query_cases` aceitou as 10 entradas (3 amplas, 5 específicas, 2 sem resposta). Conferência adicional contra `output/vivo_gold_banda_larga_pf/chunks.json`: cada uma das oito consultas com critério é satisfeita por **um único chunk** dentro de `validacao.top_k = 4`, e todos os `documento_esperado` existem como `nome_arquivo` no corpus. `uv run pytest tests/test_validation.py tests/test_validation_boundaries.py` → 17 passed.
  - [x] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [x] **EVIDENCE**: Carga por `uv run python -c "from src.validation import load_query_cases; ..."` → 10 consultas: ampla 3, especifica 5, sem_resposta 2. A aprovação não é vazia: quatro sondas de gabarito malformado (sem categoria, categoria inválida, específica sem critério e lista vazia) foram rejeitadas com as mensagens de `ValueError` esperadas. Nenhuma consulta remota foi executada nesta tarefa.
  - [x] **IMPROVE**: Uma pergunta apenas ausente da base, porém vizinha do domínio (ex.: um plano inexistente), recupera chunks semanticamente fortes e nunca ficaria abaixo de `limiar_minimo`; ela reprovaria a categoria `sem_resposta` sem indicar defeito da base. As duas consultas dessa categoria foram, por isso, escolhidas fora do domínio, e a limitação ficou registrada no cabeçalho do gabarito para quem for estendê-lo.
  <!-- specsfy:evidence {"task":"T025","refs":["FR-004","AC-008","AC-009"],"files":["documentos/vivo_gold_banda_larga_pf/consultas.yaml"],"commands":[{"run":"uv run python -c \"from src.validation import load_query_cases; ...\"","exit":0},{"run":"uv run pytest tests/test_validation.py tests/test_validation_boundaries.py","exit":0},{"run":"node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check","exit":0}]} -->

#### Fase final — Qualidade e documentação

- [x] T026 [DOC] Registrar as chaves novas de configuração em .specsfy/STACK.md — Refs: FR-001, FR-004 — Depends: T001, T023
  - [x] **PREP**: Monitor executado (`CURRENT`). O bloco `specsfy:stack` (linhas 8–21) é gerenciado pelo framework e inventaria tecnologia por camada, não chave de configuração; o registro foi feito em seção humana própria, fora do bloco.
  - [x] **EXECUTE**: Seção `Chaves de configuração da validação de recuperação` acrescentada a `.specsfy/STACK.md`, com tabela de obrigatoriedade, valor padrão, finalidade e evidência de cada chave, mais três notas de operação. `caminhos.consultas_referencia` e `validacao.limiar_minimo` são obrigatórias e levantam erro documentado quando ausentes; `validacao.top_k` tem padrão `4` em `src/validation.py:352`.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`. `git diff --numstat .specsfy/STACK.md` → `25 0`, mudança puramente aditiva, e `git diff` não toca nenhuma linha do bloco `specsfy:stack`.
  - [x] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [x] **EVIDENCE**: Monitor `CURRENT` antes e depois; 25 linhas acrescentadas e nenhuma removida, com o bloco gerenciado preservado.
  - [x] **IMPROVE**: A tabela sozinha não impediria o erro mais provável de quem escreve o próximo gabarito. Foram acrescentadas duas notas: `deve_conter` é substring exata e deve ser copiada de `output/<base>/chunks.json`, não do Markdown de origem, porque o chunking por cabeçalho e os resumos de seção alteram o texto indexado; e `limiar_minimo` precisa ser recalibrado ao trocar provider ou modelo de embeddings.
  <!-- specsfy:evidence {"task":"T026","refs":["FR-001","FR-004"],"files":[".specsfy/STACK.md"],"commands":[{"run":"node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check","exit":0}]} -->
- [x] T027 [DOC] Reconstruir docs/ e revisar PROJECT.md após a entrega — Refs: FR-007, NFR-002 — Depends: T024
  - [x] **PREP**: T024 confirmada — a pasta `scripts/` não existe e o commit `2b3eddf` registra a remoção de `scripts/check_qdrant_connection.py` e `scripts/check_qdrant_search.py`. Documentos afetados pela superfície nova: `docs/architecture.md` e `docs/application.md` já a citam parcialmente; `docs/testing.md`, `docs/flows.md`, `docs/decisions.md` e `docs/README.md` ainda não mencionam `validate.py`, `src/validation.py`, `describe_scope` nem as chaves de `validacao`.
  - [x] **EXECUTE**: `$specsfy-documentator` carregado e `build_documentation.mjs --project .` executado: os blocos `specsfy:documentator` já estavam atuais e nada mudou neles. As lacunas do PREP estavam nas seções humanas, fora dos blocos gerados, e foram corrigidas à mão contra as fontes: `docs/testing.md` (17 arquivos e 180 casos, com tabela por arquivo, substituindo "oito arquivos" e "61 casos"), `docs/README.md` (10 módulos em `src/`, 16 arquivos em `src/providers/`, oito CLIs na raiz, remoção da menção à pasta `scripts/`), `docs/flows.md` (fluxo de validação somente leitura, com as cinco garantias observadas em `src/validation.py`) e `docs/decisions.md` (decisões da SPEC-0003, DEC-011 e SPEC-0004). `PROJECT.md` revisado com impacto material: uma capacidade nova (validação somente leitura com três desfechos e resultado estruturado), um limite novo (a validação comprova comportamento contra o gabarito declarado, não julga a qualidade de respostas de uma aplicação RAG) e `src/validation.py` acrescentado ao contexto técnico.
  - [x] **VERIFY**: `node .claude/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check` → exit 0 depois das correções manuais. `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`. `uv run pytest` → 180 passed, com `tests/test_docs_safety.py` verde após a alteração do material publicado.
  - [x] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [x] **EVIDENCE**: Arquivos atualizados: `docs/README.md`, `docs/testing.md`, `docs/flows.md`, `docs/decisions.md` e `PROJECT.md`. `.specsfy/PACKAGES.md` permaneceu com o bloco vazio, estado esperado para um projeto Python sem npm nem Composer; o inventário Python fica em `docs/packages.md`. As citações remanescentes a `src/embedder.py` e aos dois protótipos são históricas ("foi removido"), não afirmações de existência.
  - [x] **IMPROVE**: O gerador não reconhece Python e publica "Arquivos de teste: 0" e "Runner: não identificado" nos blocos gerados, ao lado das seções humanas corretas. Em vez de contradizer o bloco em silêncio, `docs/README.md` passou a declarar por que o detector automático não enxerga este repositório, e `docs/testing.md` registrou que nenhuma suíte exige rede — fato que nenhum dos dois documentos afirmava e que é a razão de a suíte inteira rodar sem credencial.
  <!-- specsfy:evidence {"task":"T027","refs":["FR-007","NFR-002"],"files":["docs/README.md","docs/testing.md","docs/flows.md","docs/decisions.md","PROJECT.md"],"commands":[{"run":"node .claude/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check","exit":0},{"run":"node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check","exit":0},{"run":"uv run pytest","exit":0}]} -->
- [x] T028 [TEST] Executar regressão e rastreabilidade sobre tests/test_validation.py e a suíte completa — Refs: US-001, US-002, US-003, FR-006, NFR-001 — Depends: T024, T026, T027
  - [x] **PREP**: Suítes: os 17 arquivos de `tests/`, executados por um único `uv run pytest`. Checks: `check_traceability.mjs`, `verify_acceptance.mjs`, `validate_tasks.mjs`, `build_documentation.mjs --check` e `monitor_context.mjs --check`. Gates: Ato I `Passed` e Ato II `Passed` já registrados; o Ato III é o único aberto. Levantamento prévio: 117 marcadores `SPECSFY:` em 16 arquivos e nenhum `skip` ou `xfail` no repositório.
  - [x] **EXECUTE**: `check_database_safety.mjs --command "uv run pytest -q"` → `SAFE`; `uv run pytest` → 180 passed em 9,87s; `check_traceability.mjs` → 30/30 IDs cobertos em 18 arquivos, `RESULTADO: GAPS` por marcadores de outras specs; `verify_acceptance.mjs` → `QA: PASSED` após o preenchimento das seções 11 e 12.
  - [x] **VERIFY**: Nenhum gap desta fatia, nenhum teste pulado e nenhum marcador órfão desta fatia. Os órfãos `AC-017…AC-025`, `FR-008`, `US-004` e `US-005` foram rastreados um a um até `specs/completed/0002-…` e `specs/completed/0003-…`; restringindo a auditoria aos quatro arquivos desta fatia, os 28 marcadores cobrem exatamente os 30 IDs declarados, com zero órfãos. Detalhe completo no gate do Ato III.
  - [x] **VISUAL**: Não aplicável — a tarefa não possui superfície gráfica com bordas, espaçamentos, margens, padding ou tipografia a conferir.
  - [x] **EVIDENCE**: Seção 11: 18 linhas de `Refactor/regressão` preenchidas com `uv run pytest` → 180 passed. Seção 12: 14 linhas de `Evidência` preenchidas com `Passed em 2026-09-02`, o que fez `verify_acceptance.mjs` sair de `QA: FAILED` (16 AC sem resultado) para `QA: PASSED`. Seção 13: comandos, contagens, o achado sobre `RESULTADO: GAPS` e a pendência da verificação manual registrados no gate do Ato III.
  - [x] **IMPROVE**: A fatia teve duas reaberturas do Ato II, e as duas vieram da mesma causa: um teste que passava sem exercitar o caminho que dizia cobrir. Em AC-003 e AC-013 o caso passava contra um `validate_base` que sequer consultava o destino, e a suíte de conformidade injetava o backend falso, de modo que `_create_backend()` nunca rodava e os adapters reais ficavam sem prova. Nos dois casos a correção foi acrescentar um discriminador positivo — exigir que a chamada tenha ocorrido, não apenas que o resultado seja o esperado — e nos dois casos o RED reforçado revelou implementação faltante. Vale generalizar: um caso que só afirma o desfecho não distingue código correto de código ausente.
  <!-- specsfy:evidence {"task":"T028","refs":["US-001","US-002","US-003","FR-006","NFR-001"],"files":["specs/in-progress/0004-validar-recuperacao-operacao/spec.md"],"commands":[{"run":"uv run pytest","exit":0},{"run":"node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/in-progress/0004-validar-recuperacao-operacao/spec.md .","exit":0},{"run":"node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0004-validar-recuperacao-operacao/spec.md","exit":0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001 → (T002…T017 em RED) → T018 → T029 → T030 → {T031, T032} → T033 → T019 → T020 → T021 → T022 → T023 → T024 → T027 → T028.
- Tarefas paralelas: as dezesseis tarefas de RED não compartilham estado entre si e podem ser materializadas em qualquer ordem dentro da Fase 1; T025 corre em paralelo às tarefas de código porque só escreve o gabarito da base; T026 depende apenas de T001 e T023; T031 e T032 podem correr em paralelo depois de T030, porque tocam arquivos de backends diferentes.
- Estratégia de MVP: T018 a T020 mais T023 já entregam preflight, conferência de identidade e os três desfechos, que é o veredito mínimo útil ao operador. A mesma spec exige o roteiro de consultas, a saída dupla e a remoção dos protótipos antes do Delivery Gate.
- Replanejamento técnico em 2026-09-01 durante a implementação: T018 deixa de declarar AC-009, pois esse aceite requer a execução de consultas que só existe em T021. T010 permanece como predecessor técnico do modelo `QueryCase`, preservando os três REDs exigidos para a fundação. A fundação verifica apenas os impedimentos locais AC-002 e AC-004; T021 preserva a cobertura de AC-009. Não houve mudança de comportamento, escopo ou aceite.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0001 concluída: política fail-closed e contagens auditáveis que esta fatia consome sem redefinir.
- SPEC-0003 concluída: contratos neutros, `list_ids` e `query` usados pela conferência e pelo roteiro. Esta fatia estende esse contrato com `describe_scope`, então a suíte de conformidade daquela spec passa a exigir a operação nova em todos os adapters.
- Uma base já indexada com manifesto correspondente em `output/<base>/manifest.json`.
- Um gabarito redigido para a base validada; sem ele o roteiro de consultas não tem o que comprovar.
- Credenciais válidas e destino acessível no momento da entrega, exigidos apenas pela evidência manual da Definition of Done. A suíte automatizada não depende de rede.

#### Riscos

- `SearchResult.score` é nativo de cada provider → o limiar mínimo vale para o provider configurado naquela base e não é comparável entre Qdrant, ChromaDB e Pinecone; a spec registra isso como limite conhecido, não como defeito.
- Gabarito desatualizado em relação à base → a validação reprova por motivo editorial; o relatório nomeia o critério não atendido para tornar a causa evidente.
- Divergência entre o manifesto local e a execução que realmente indexou o destino → conferência de `project_id` e `collection_name` antes de comparar identidades.
- Volume muito maior que o atual → `list_ids` sem paginação pode ficar caro; irrelevante nos 208 identificadores atuais e registrado para revisão futura.
- Remoção dos protótipos antes do comando novo estar completo → a ordem de execução coloca a remoção depois da cobertura de preflight e consulta.
- Extensão do contrato neutro alcançando quatro adapters e a conformidade da SPEC-0003 → a adição é apenas de leitura e não altera nenhuma operação existente; cada backend recebe caso próprio na conformidade antes de o preflight ser implementado.

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

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Os dezesseis cenários `AC` passam com casos TDD próprios — `verify_acceptance.mjs` → `QA: PASSED`.
- [x] Cada US, FR e NFR possui pelo menos três cenários e evidência executável — 30/30 IDs cobertos pelos 28 marcadores dos quatro arquivos desta fatia.
- [x] Nenhuma escrita chega ao destino em qualquer caminho, comprovado com adapters falsos — AC-013 e, na execução real de 2026-09-02, apenas `GET /collections/<nome>`, `POST /points/scroll` e dez `POST /points/search`.
- [x] Relatório, JSON e log estão livres de credenciais, tokens e URLs de destino — verificado no teste com credenciais fictícias e no artefato real gravado em 2026-09-02. O logger de terceiros `httpx` imprime a URL no console em nível INFO; isso está fora das três saídas nomeadas pela NFR-003 e ficou registrado como achado na seção 11.
- [x] `scripts/check_qdrant_connection.py` e `scripts/check_qdrant_search.py` foram removidos e nenhum identificador de cliente permanece no código de validação.
- [x] O módulo de validação é chamável sem a camada de linha de comando — AC-015.
- [x] Uma execução real contra o destino configurado foi observada pelo operador e registrada como evidência manual — 2026-09-02, desfecho `APROVADO`, código `0`, 208/208 pontos e 10/10 consultas.
- [x] Pytest completo está verde — `uv run pytest` → 180 passed.
- [x] `.specsfy/STACK.md` registra as entradas novas de configuração quando aplicável e a documentação foi reconstruída com o monitor de contexto em `CURRENT`.

## Effort history

- 2026-09-02T00:57:14.618Z: 6 → 6. Extensão do contrato neutro com describe_scope alcança quatro adapters e a conformidade da SPEC-0003
