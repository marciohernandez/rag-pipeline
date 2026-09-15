# Especificação integrada: Decidir onde o resumo de seção vive e revisar as regras de corte do chunker

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0014 |
| Slug | 0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker |
| Status | Planned |
| Effort | 4 |
| Effort updated at | 2026-09-15 |
| Effort rationale | Perfil `standard`: uma única decisão de design com prova comparativa real (3 alternativas × gabarito × embeddings reais), sem persistência nova nem interface, mas exigindo raciocínio sobre trade-off e integração com um provider externo pago. |
| ClickUp Task | |
| Milestones | M02 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-15 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

A busca plana atual faz o resumo de seção (`chunk_type: "section_summary"`,
gerado por `_section_summary_chunks` em `src/pipeline/chunker.py:148-232`)
competir em pé de igualdade com os chunks detalhados da mesma recuperação,
sem aproveitar sua estrutura como índice navegacional. Não existe hoje uma
decisão comparada, com evidência real, sobre onde esse resumo deveria viver
nem sobre quais regras de corte/tamanho do chunker deveriam mudar em
consequência dessa colocação.

#### Resultado desejado

Uma decisão registrada — com prova comparativa real contra o gabarito
versionado da base `vivo_gold_banda_larga_pf` — sobre qual das três
alternativas de colocação do resumo de seção usar (ou manter o comportamento
atual, se nenhuma alternativa superar), e quais parâmetros de corte/tamanho
do chunker mudam nessa alternativa. Essa decisão é o insumo direto para a
spec seguinte (BACKLOG-0017), que implementa a versão final de produção e
mede o efeito completo.

#### Métricas de sucesso

- As três alternativas comparadas produzem, cada uma, uma contagem de
  consultas aprovadas no gabarito completo de
  `documentos/vivo_gold_banda_larga_pf/consultas.yaml` (10 consultas) e um
  registro de ruído percebido.
- A decisão final (alternativa escolhida, "manter como está", ou limitação
  registrada) está documentada na seção 17 com justificativa, sem exigir
  interpretação adicional para a spec seguinte prosseguir.

### 2. Research e esclarecimentos

#### Researchs executados

- Não há claim externo crítico a verificar; a pesquisa desta spec é interna
  ao repositório (código e configuração já existentes), registrada abaixo.

#### Fontes e contexto consultados

- `src/pipeline/chunker.py:148-232` (`_section_summary_chunks`) — como o
  resumo de seção é gerado e concatenado hoje aos chunks detalhados.
- `src/pipeline/quality.py` — os seis sinais heurísticos hoje somente
  informativos (perda de estrutura, truncamento, duplicata exata, texto
  colapsado, conteúdo útil curto, distribuição de tamanho) e o agrupamento
  por `chunk_type` do relatório.
- `src/pipeline/validation.py` / `validate.py` — o gabarito versionado e o
  mecanismo de avaliação de consultas por categoria (`ampla`, `especifica`,
  `sem_resposta`), reaproveitado como instrumento de leitura desta spec.
- `documentos/vivo_gold_banda_larga_pf/consultas.yaml` — gabarito real usado
  na comparação (10 consultas, 8 documentos).
- `src/pipeline/providers/embeddings/fake.py` — confirmado que o provider
  `fake` deriva o vetor de SHA-256 do texto: determinístico, mas sem sinal
  semântico, portanto inadequado para provar diferença real de recuperação
  entre as três alternativas.
- `src/pipeline/providers/embeddings/huggingface.py` e ambiente local —
  confirmado que `sentence-transformers`/`langchain-huggingface` não estão
  instalados; usar essa via exigiria nova dependência e download de modelo.
- `config.yaml:115-120` — confirma `openai` como provider de embeddings já
  configurado em produção.
- `tests/test_qdrant_backend_operations.py` — padrão local de suíte que
  exercita comportamento real de um provider, usado como referência de estilo
  (aqui adaptado para um teste que consulta a API real da OpenAI em vez de um
  dublê).
- `specs/backlog/0016-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker.md`
  — brief de origem, já com o comportamento esperado, critérios de aceite e
  escopo refinados via `$specsfy-02-backlog`.
- `specs/milestones/M02.md` — condição de saída do marco que esta spec ajuda
  a cumprir.

#### Documentação consultada

- Nenhuma documentação externa foi consultada; toda fonte é código e
  configuração deste repositório.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo. Toda evidência consultada já está versionada no
  próprio repositório (código-fonte, configuração e o backlog de origem);
  nada precisou ser copiado para `research/`.

#### Dúvidas respondidas

- **Q**: o provider `fake` de embeddings (SHA-256, sem sinal semântico) serve
  para comparar as três alternativas? → **A**: Não. Confirmado por leitura de
  `fake.py`; usá-lo produziria ranking arbitrário em relação ao significado
  das consultas, invalidando a prova que esta spec existe para produzir.
- **Q**: qual provider de embeddings a comparação deve usar, já que `fake`
  está descartado e `huggingface` local não está instalado? → **A**: `openai`
  real, decisão confirmada por Marcio em 2026-09-15 (Pergunta 1 da
  descoberta) — mesmo provider já configurado em `config.yaml` para
  produção; volume pequeno (8 documentos, 10 consultas, 3 alternativas) torna
  o custo de API desprezível, e evita adicionar `sentence-transformers` como
  dependência nova só para este experimento de decisão. Ver DEC-002.

#### Dúvidas abertas

- Nenhuma bloqueante para o Definition Gate. A decisão substantiva sobre
  qual alternativa vence (ou se nenhuma vence) só é conhecida ao executar a
  comparação real durante o Ato III (tarefas T007–T009) e será registrada como
  `DEC-001` na seção 17 nesse momento — não é uma lacuna de definição, é o
  próprio resultado que a spec produz.

### 3. Escopo e atores

#### Incluído

- Implementar, de forma mínima (protótipo, não necessariamente código de
  produção final), as três alternativas de colocação do resumo de seção:
  (a) metadado anexado ao chunk detalhado da mesma seção; (b) chunk indexado
  com peso/sinal que evita competir em pé de igualdade com chunks detalhados;
  (c) índice de roteamento hierárquico separado da busca principal.
- Rodar cada alternativa contra o gabarito completo de
  `vivo_gold_banda_larga_pf/consultas.yaml`, usando o provider de embeddings
  `openai` real, sem gravar em Qdrant de produção nem alterar bases já
  indexadas.
- Registrar a decisão final — alternativa escolhida, "manter como está", ou
  limitação de evidência — com a justificativa e os parâmetros de
  `chunker.py` que mudam em consequência direta dessa escolha.
- Sinalizar explicitamente se a decisão afeta o agrupamento por `chunk_type`
  hoje usado pelo relatório de `src/pipeline/quality.py` (risco antecipado
  por BACKLOG-0005/SPEC-0006), sem implementar essa revisão aqui.

#### Fora de escopo

- Implementação de produção final da alternativa escolhida — fica para
  BACKLOG-0017/spec seguinte.
- Medição completa sobre a base inteira, outras bases, ou em escala — esta
  spec usa deliberadamente o gabarito pequeno já versionado.
- Detecção de contradição ou duplicação de conteúdo entre documentos
  diferentes — fora deste componente (limite declarado em `PROJECT.md`).
- Promover qualquer um dos seis sinais heurísticos de `quality.py` a bloqueio,
  quando não estiver diretamente ligado à colocação do resumo.
- Ingestão multi-formato (Fase 1) e qualquer mudança de interface — este
  componente não tem tela para esta funcionalidade.

#### Atores

- **Marcio e a equipe de consultoria**: opera e audita a recuperação do RAG
  Pipeline; é quem recebe e usa a decisão registrada por esta spec.

### 4. Princípios e restrições do projeto

- **PR-001**: Nenhum código desta spec importa SDK de vector store fora de
  `src/pipeline/providers/`; o protótipo reaproveita o adapter `in_memory` via
  factory quando precisar de um vector store, conforme a fronteira verificada
  por `tests/test_provider_boundaries.py`.
- **PR-002**: Nenhuma execução de teste desta spec grava em Qdrant de
  produção nem altera uma base já indexada, mesmo em caso de erro
  (`.specsfy/RULES.md`, política de segurança e privacidade).
- **PR-003**: Detecção de contradição ou duplicação de conteúdo entre
  documentos diferentes permanece fora deste componente (`PROJECT.md`,
  seção "Limites"); esta spec não a implementa mesmo que apareça como
  tentação ao comparar as alternativas.

### 5. Histórias de usuário

#### US-001 — Decidir a colocação do resumo de seção com evidência comparativa (P1)

Como Marcio e a equipe que opera o RAG Pipeline, quero comparar as três
alternativas de colocação do resumo de seção contra o gabarito real da base,
para decidir com evidência qual delas usar — ou manter o comportamento
atual — antes de comprometer a implementação final.

**Por que P1**: é a única história da spec e a condição de saída inteira da
primeira metade da M02 depende dela.
**Teste independente**: rodar a comparação (T001–T008) e ler a decisão
registrada na seção 17, sem depender de nenhuma parte de BACKLOG-0017.
**Requisitos**: FR-001, FR-002, FR-003

### 6. Cenários BDD de aceite

#### AC-001 — Comparar as três alternativas contra o gabarito completo

**Cobre**: US-001, FR-001, FR-002, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @AC-001
Feature: Comparar alternativas de colocação do resumo de seção

  Scenario Outline: Executar o protótipo de uma alternativa contra o gabarito real
    Given o gabarito de "documentos/vivo_gold_banda_larga_pf/consultas.yaml"
    And o protótipo da alternativa "<alternativa>" aplicado à mesma base, usando embeddings OpenAI reais
    When cada uma das 10 consultas do gabarito é avaliada contra o protótipo
    Then o número de consultas aprovadas e algum indício de ruído são registrados para "<alternativa>"
    And nenhuma escrita acontece em Qdrant de produção nem em base já indexada

    Examples:
      | alternativa           |
      | metadado               |
      | chunk_com_peso         |
      | indice_de_roteamento   |
```

#### AC-002 — Nenhuma alternativa supera o comportamento atual

**Cobre**: US-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-002 @FR-003 @NFR-001 @AC-002
Feature: Comparar alternativas de colocação do resumo de seção

  Scenario: Decisão de manter como está quando nenhuma alternativa supera o atual
    Given as três alternativas comparadas contra o gabarito completo
    When nenhuma delas aprova mais consultas nem reduz ruído em relação ao comportamento atual
    Then a decisão registrada na seção 17 é "manter como está"
    And a justificativa cita os números da comparação que sustentam a decisão
```

#### AC-003 — Decisão lista os parâmetros do chunker que mudam

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-003
Feature: Comparar alternativas de colocação do resumo de seção

  Scenario: Alternativa vencedora exige mudança de parâmetro do chunker
    Given uma alternativa vencedora identificada pela comparação
    When a decisão é registrada na seção 17
    Then a decisão lista exatamente quais parâmetros de src/pipeline/chunker.py mudam
    And descreve o novo comportamento esperado desses parâmetros
```

#### AC-004 — Decisão sinaliza impacto sobre o agrupamento por chunk_type

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-004
Feature: Comparar alternativas de colocação do resumo de seção

  Scenario: Alternativa escolhida muda a semântica de chunk_type
    Given uma alternativa escolhida que deixa de gerar chunk_type "section_summary" como hoje
    When a decisão é registrada na seção 17
    Then a decisão sinaliza explicitamente que o agrupamento por chunk_type em src/pipeline/quality.py precisa ser revisto
    And registra essa dependência para a spec seguinte, sem implementar a revisão aqui
```

#### AC-005 — Erro durante o protótipo não afeta produção

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-005
Feature: Comparar alternativas de colocação do resumo de seção

  Scenario: Falha durante a execução de uma alternativa
    Given o protótipo de uma alternativa em execução
    When ocorre um erro inesperado durante a avaliação de uma consulta
    Then nenhum resíduo é deixado em Qdrant de produção nem em base já indexada
    And o erro é registrado como resultado daquela alternativa, sem interromper a comparação das demais
```

#### AC-006 — Gabarito insuficiente para diferenciar as alternativas

**Cobre**: US-001, FR-001, FR-002, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @AC-006
Feature: Comparar alternativas de colocação do resumo de seção

  Scenario: Gabarito não cobre casos suficientes para decidir
    Given o gabarito de vivo_gold_banda_larga_pf/consultas.yaml
    When nenhuma das 10 consultas toca uma seção com resumo, tornando a comparação inconclusiva
    Then a spec registra essa limitação como decisão aberta na seção 17
    And não força a escolha de uma alternativa sem evidência
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O protótipo deve implementar as três alternativas de colocação
  do resumo de seção de forma isolada (não necessariamente como código de
  produção final), sem gravar em Qdrant de produção nem alterar bases já
  indexadas, mesmo em caso de erro durante a execução.
- **FR-002**: A comparação deve rodar cada alternativa contra o gabarito
  completo de `documentos/vivo_gold_banda_larga_pf/consultas.yaml`, usando o
  provider de embeddings `openai` real, e registrar, por alternativa, quantas
  consultas aprovam e algum indício de ruído; se o gabarito não permitir
  diferenciar as alternativas, a limitação é registrada em vez de forçar uma
  escolha.
- **FR-003**: A decisão final deve ser registrada na seção 17 desta spec,
  incluindo a alternativa escolhida (ou "manter como está"), a justificativa
  baseada nos números da comparação, quais parâmetros de `chunker.py` mudam
  em consequência, e se o agrupamento por `chunk_type` em `quality.py`
  precisa ser revisto pela spec seguinte — sem implementar essa mudança de
  produção final aqui.

#### Não funcionais

- **NFR-001**: Auditabilidade e isolamento — toda execução do protótipo é
  local e rastreável (números registrados na spec), sem tocar Qdrant de
  produção nem consumir credencial fora do fluxo já existente de
  `OPENAI_API_KEY`. **Verificação**: inspeção da spec (seções 12–13) e revisão
  de código confirmando que nenhuma escrita remota de produção ocorre.

#### Erros e casos-limite

- Ausência de `OPENAI_API_KEY` no ambiente de execução → o caso de teste que
  depende de embeddings reais é marcado `skip`, com motivo explícito, e não
  bloqueia a suíte geral (`uv run pytest`).
- Gabarito sem consulta que toque seção com resumo → limitação registrada
  como decisão aberta (AC-006), sem forçar escolha.
- Empate técnico entre as três alternativas → decisão prioriza a alternativa
  de menor custo de implementação para BACKLOG-0017, com a justificativa
  registrada.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- `src/pipeline/chunker.py:148-232` (`_section_summary_chunks`) gera o resumo
  de seção como `chunk_type: "section_summary"`, concatenado à lista de
  chunks detalhados antes da indexação.
- `src/pipeline/quality.py` calcula seis sinais heurísticos somente
  informativos e agrupa o relatório por `chunk_type`, incluindo
  `section_summary` como um tipo distinto.
- `src/pipeline/validation.py` / `validate.py` carregam o gabarito
  (`caminhos.consultas_referencia`), rodam cada consulta por categoria
  (`ampla`, `especifica`, `sem_resposta`) e retornam aprovação por critério.
- `src/pipeline/providers/` concentra os contratos, a factory e os adapters
  de embeddings/vector store; é o único lugar do repositório onde SDK externo
  pode ser importado (regra verificada por teste AST,
  `tests/test_provider_boundaries.py`).
- `config.yaml` já declara `embedding.provider: "openai"` para produção.

#### Arquitetura e módulos

- O protótipo das três alternativas vive como funções auxiliares locais na
  própria suíte de teste desta spec (`tests/test_spec0014_resumo_secao.py` ou
  um módulo de apoio sob `tests/`), sem alterar `src/pipeline/chunker.py`
  nesta spec — a implementação de produção da alternativa vencedora é
  responsabilidade da spec seguinte (BACKLOG-0017).
- Cada alternativa reaproveita a saída já existente de `chunker.py` (a lista
  de chunks, incluindo o `section_summary` atual) e a reorganiza localmente
  conforme a alternativa em avaliação, antes de indexar num
  `InMemoryVectorStoreAdapter` (via factory, respeitando PR-001) para a
  consulta de teste.
- A avaliação de cada consulta reaproveita a lógica de `validation.py`
  (`run_query_cases` ou equivalente) como instrumento de leitura, sem
  duplicar sua implementação.
- **Restrição de isolamento (FIND-ARCH-001, Resolved)**: o adapter de vector
  store e o de embeddings são construídos diretamente pela factory, com
  parâmetros literais no teste — nunca por `build_vector_store`/
  `build_embeddings` a partir de `config.get(...)` de um `config.yaml`
  carregado, cujo default de produção é `"qdrant"` (`src/app/main.py:69`,
  correção da auditoria pré-M2 do M01). Carregar o `config.yaml` real aqui
  apontaria o teste para o Qdrant de produção.

#### Migrations

- Não aplicável — nenhuma mudança de schema.

#### Models

- Não aplicável — nenhuma entidade persistente nova.

#### Controllers e casos de uso

- Não aplicável — esta spec não expõe rota HTTP nem comando de CLI novo; o
  resultado é a decisão registrada na própria spec.

#### Views e experiência

- Não aplicável — sem interface para pessoas (ver seção 10).

#### Queries e repositórios

- Não aplicável — nenhuma consulta a banco relacional.

#### Jobs e processamento assíncrono

- Não aplicável.

#### Estrutura de arquivos

```text
specs/draft/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/
  spec.md
tests/
  test_spec0014_resumo_secao.py
```

### 9. Modelo de dados

#### Entidades

- Não aplicável — nenhuma entidade nova ou persistida por esta spec.

#### Estados e transições

- Não aplicável.

#### Migração e retenção

- Não aplicável.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. Esta spec produz uma decisão de design
  registrada na própria spec (seção 17), consumida pela equipe e pela spec
  seguinte (BACKLOG-0017) — não há tela, CLI nova nem rota HTTP.

#### APIs expostas

- Não aplicável — nenhum endpoint novo.

#### APIs externas utilizadas

- **OpenAI Embeddings** (via `src/pipeline/providers/embeddings/openai.py`,
  já existente): usada pelo protótipo para gerar os vetores reais necessários
  para diferenciar as três alternativas com sinal semântico. Autenticação por
  `OPENAI_API_KEY` do `.env`, já usada em produção. Sem retry/timeout
  adicional além do que o adapter já implementa. Custo esperado desprezível
  (8 documentos, 10 consultas, 3 alternativas).

#### Documentação das APIs consultadas

- Nenhuma documentação externa nova consultada; o adapter OpenAI já existente
  é reaproveitado sem alteração de contrato.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: cada alternativa de colocação do resumo, isoladamente, e a
  lógica de decisão (vencedora / manter como está / limitação registrada).
- **Integração/contrato**: chamada real ao provider de embeddings `openai`
  contra o gabarito completo de `vivo_gold_banda_larga_pf`.
- **BDD/aceite**: os seis cenários da seção 6 orientam os casos TDD abaixo.
- **Runner TDD**: Python/Pytest, convenção já estabelecida no repositório
  (`uv run pytest`); não há Node nem PHP envolvidos nesta spec.
- **E2E**: Não aplicável — sem jornada de usuário ponta a ponta nesta spec.
- **Verificação manual**: leitura da decisão registrada na seção 17 ao final,
  para confirmar que a justificativa é compreensível sem contexto adicional.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, NFR-001, AC-001 | AC-001 na seção 6 | `tests/test_spec0014_resumo_secao.py::test_comparacao_alternativas[metadado/chunk_com_peso/indice_de_roteamento]` com marcador `SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-001` | RED: `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'` (3 variações) | Pending | Pending |
| US-001, FR-002, FR-003, NFR-001, AC-002 | AC-002 na seção 6 | `tests/test_spec0014_resumo_secao.py::test_decisao_manter_como_esta_quando_nenhuma_supera` com marcador `SPECSFY: US-001 FR-002 FR-003 NFR-001 AC-002` | RED: `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'` | Pending | Pending |
| US-001, FR-003, NFR-001, AC-003 | AC-003 na seção 6 | `tests/test_spec0014_resumo_secao.py::test_decisao_lista_parametros_chunker` com marcador `SPECSFY: US-001 FR-003 NFR-001 AC-003` | RED: `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'` | Pending | Pending |
| US-001, FR-003, NFR-001, AC-004 | AC-004 na seção 6 | `tests/test_spec0014_resumo_secao.py::test_decisao_sinaliza_impacto_chunk_type` com marcador `SPECSFY: US-001 FR-003 NFR-001 AC-004` | RED: `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'` | Pending | Pending |
| US-001, FR-001, NFR-001, AC-005 | AC-005 na seção 6 | `tests/test_spec0014_resumo_secao.py::test_erro_prototipo_nao_afeta_producao` com marcador `SPECSFY: US-001 FR-001 NFR-001 AC-005` | RED: `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'` | Pending | Pending |
| US-001, FR-001, FR-002, NFR-001, AC-006 | AC-006 na seção 6 | `tests/test_spec0014_resumo_secao.py::test_gabarito_insuficiente_registra_limitacao` com marcador `SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-006` | RED: `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'` | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | `uv run pytest tests/test_spec0014_resumo_secao.py::test_comparacao_alternativas` | Pending |
| FR-001 | AC-005 | Unidade | `uv run pytest tests/test_spec0014_resumo_secao.py::test_erro_prototipo_nao_afeta_producao` | Pending |
| FR-001 | AC-006 | Integração | `uv run pytest tests/test_spec0014_resumo_secao.py::test_gabarito_insuficiente_registra_limitacao` | Pending |
| FR-002 | AC-001 | Integração | `uv run pytest tests/test_spec0014_resumo_secao.py::test_comparacao_alternativas` | Pending |
| FR-002 | AC-002 | Unidade | `uv run pytest tests/test_spec0014_resumo_secao.py::test_decisao_manter_como_esta_quando_nenhuma_supera` | Pending |
| FR-003 | AC-002 | Unidade | `uv run pytest tests/test_spec0014_resumo_secao.py::test_decisao_manter_como_esta_quando_nenhuma_supera` | Pending |
| FR-003 | AC-003 | Unidade | `uv run pytest tests/test_spec0014_resumo_secao.py::test_decisao_lista_parametros_chunker` | Pending |
| FR-003 | AC-004 | Unidade | `uv run pytest tests/test_spec0014_resumo_secao.py::test_decisao_sinaliza_impacto_chunk_type` | Pending |
| NFR-001 | AC-001 | Integração | `uv run pytest tests/test_spec0014_resumo_secao.py -v` | Pending |
| NFR-001 | AC-005 | Unidade | `uv run pytest tests/test_spec0014_resumo_secao.py::test_erro_prototipo_nao_afeta_producao` | Pending |
| NFR-001 | AC-006 | Integração | `uv run pytest tests/test_spec0014_resumo_secao.py::test_gabarito_insuficiente_registra_limitacao` | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/spec.md` → VALID.
- **Achados**:

- **FIND-ARCH-001** [P1] [Resolved] Plano técnico e T007 não proibiam explicitamente carregar config.yaml real para construir o vector store do protótipo, cujo default de produção é qdrant — Refs: FR-001 — Evidence: src/app/main.py:69 — Effect: risco de escrita real em produção durante um experimento que deveria ser isolado — Suggestion: construir InMemoryVectorStoreAdapter e o adapter openai diretamente pela factory, nunca a partir de config.yaml carregado; corrigido na seção 8 e em T007.
- Cobertura mínima `US/FR/NFR ↔ 3 AC` confirmada por `validate_spec.mjs`
  (US-001: 6 AC; FR-001: 3; FR-002: 3; FR-003: 3; NFR-001: 6).

#### Gate do Ato II — Plano

- **Resultado**: PASSED
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/spec.md` → VALID.
- **Achados**: Nenhum bloqueante. T001–T006 (predecessores TDD) concluídos com RED registrado
  (`ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'`,
  `uv run pytest tests/test_spec0014_resumo_secao.py -v` → 8/8 falharam pelo
  motivo esperado). T007–T010 (código/execução real) permanecem abertos por
  decisão explícita de Marcio em 2026-09-15: seguir até a fronteira da
  implementação, sem implementar. Regressão completa (`uv run pytest -q`) →
  267 passed, 8 RED esperados desta spec, 27 failed + 10 errors pré-existentes
  em `tests/test_app_*.py`/`test_app_migrations.py` por ausência de Postgres
  local (`connection to server at "127.0.0.1", port 55432 failed`),
  inteiramente fora do escopo desta spec (não toca `src/app/`).
  `uv run ruff check .` → limpo.

#### Gate do Ato III — Entrega

- **Resultado**: Pending (RED materializado; GREEN e regressão final aguardam `$specsfy-07-implement`, deliberadamente não executado nesta etapa)
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/spec.md .`
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

- [x] T001 [TEST] [TDD] [US-001] [P] Derivar do AC-001 um caso Pytest parametrizado falhando em `tests/test_spec0014_resumo_secao.py::test_comparacao_alternativas` — Refs: US-001, FR-001, FR-002, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Confirmado o Gherkin da AC-001, os IDs e que `tests/_spec0014_resumo_secao.py` ainda não existe.
  - [x] **EXECUTE**: Escrito o caso parametrizado (`metadado`, `chunk_com_peso`, `indice_de_roteamento`) com marcador `SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-001`, sem criar `.feature`.
  - [x] **VERIFY**: RED observado nas três variações.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: `uv run pytest tests/test_spec0014_resumo_secao.py::test_comparacao_alternativas -v` → `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'` nas três variações (mesmo padrão de RED já aceito em SPEC-0012/T007 para módulo inexistente).
  - [x] **IMPROVE**: Nenhuma melhoria necessária; a granularidade por parametrize evitou duplicar o teste três vezes.

- [x] T002 [TEST] [TDD] [US-001] [P] Derivar do AC-002 um caso Pytest falhando em `tests/test_spec0014_resumo_secao.py::test_decisao_manter_como_esta_quando_nenhuma_supera` — Refs: US-001, FR-002, FR-003, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Confirmado o Gherkin da AC-002 e os IDs.
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: US-001 FR-002 FR-003 NFR-001 AC-002`, simulando um resultado de comparação sem vencedora clara.
  - [x] **VERIFY**: RED observado.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: `uv run pytest tests/test_spec0014_resumo_secao.py::test_decisao_manter_como_esta_quando_nenhuma_supera -v` → `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária nesta etapa.

- [x] T003 [TEST] [TDD] [US-001] [P] Derivar do AC-003 um caso Pytest falhando em `tests/test_spec0014_resumo_secao.py::test_decisao_lista_parametros_chunker` — Refs: US-001, FR-003, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Confirmado o Gherkin da AC-003 e os IDs.
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: US-001 FR-003 NFR-001 AC-003`.
  - [x] **VERIFY**: RED observado.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: `uv run pytest tests/test_spec0014_resumo_secao.py::test_decisao_lista_parametros_chunker -v` → `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária nesta etapa.

- [x] T004 [TEST] [TDD] [US-001] [P] Derivar do AC-004 um caso Pytest falhando em `tests/test_spec0014_resumo_secao.py::test_decisao_sinaliza_impacto_chunk_type` — Refs: US-001, FR-003, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Confirmado o Gherkin da AC-004 e os IDs.
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: US-001 FR-003 NFR-001 AC-004`.
  - [x] **VERIFY**: RED observado.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: `uv run pytest tests/test_spec0014_resumo_secao.py::test_decisao_sinaliza_impacto_chunk_type -v` → `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária nesta etapa.

- [x] T005 [TEST] [TDD] [US-001] [P] Derivar do AC-005 um caso Pytest falhando em `tests/test_spec0014_resumo_secao.py::test_erro_prototipo_nao_afeta_producao` — Refs: US-001, FR-001, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Confirmado o Gherkin da AC-005 e os IDs.
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: US-001 FR-001 NFR-001 AC-005`, com sentinela de produção via `monkeypatch` e simulação de erro na consulta 0.
  - [x] **VERIFY**: RED observado.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: `uv run pytest tests/test_spec0014_resumo_secao.py::test_erro_prototipo_nao_afeta_producao -v` → `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária nesta etapa.

- [x] T006 [TEST] [TDD] [US-001] [P] Derivar do AC-006 um caso Pytest falhando em `tests/test_spec0014_resumo_secao.py::test_gabarito_insuficiente_registra_limitacao` — Refs: US-001, FR-001, FR-002, NFR-001, AC-006 — Depends: none
  - [x] **PREP**: Confirmado o Gherkin da AC-006 e os IDs.
  - [x] **EXECUTE**: Escrito o caso com marcador `SPECSFY: US-001 FR-001 FR-002 NFR-001 AC-006`, com gabarito sintético (`tmp_path`) sem consulta que toque seção com resumo.
  - [x] **VERIFY**: RED observado.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: `uv run pytest tests/test_spec0014_resumo_secao.py::test_gabarito_insuficiente_registra_limitacao -v` → `ModuleNotFoundError: No module named 'tests._spec0014_resumo_secao'`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária nesta etapa.

#### Fase 2 — US-001 Decidir a colocação do resumo de seção com evidência comparativa (P1)

**Objetivo**: produzir a decisão registrada e comprovada que a spec seguinte
(BACKLOG-0017) consome como insumo direto.
**Teste independente**: `uv run pytest tests/test_spec0014_resumo_secao.py -v` e leitura da seção 17.

- [ ] T007 [CODE] [US-001] Implementar o harness das três alternativas e a lógica de decisão em `tests/test_spec0014_resumo_secao.py` — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006
  - [ ] **PREP**: Confirmar RED de T001–T006 e a fronteira de providers (PR-001).
  - [ ] **EXECUTE**: Implementar a menor mudança que torna T001–T006 GREEN, reaproveitando `chunker.py` e `validation.py`, com `OPENAI_API_KEY` real e `skip` documentado quando ausente. Construir o `InMemoryVectorStoreAdapter` e o adapter de embeddings `openai` diretamente pela factory, com parâmetros literais no teste — **nunca** por `build_vector_store(config.get("vector_store"), ...)` a partir de `config.yaml` carregado, cujo default de produção é `"qdrant"` (`src/app/main.py:69`); carregar esse arquivo aqui apontaria o teste para o Qdrant real.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_spec0014_resumo_secao.py -v` e a regressão completa.
  - [ ] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T007","refs":["US-001","FR-001","FR-002","FR-003","NFR-001","AC-001","AC-002","AC-003","AC-004","AC-005","AC-006"],"files":["tests/test_spec0014_resumo_secao.py"],"commands":[{"run":"uv run pytest tests/test_spec0014_resumo_secao.py -v","exit":0}]} -->

- [ ] T008 [CODE] [US-001] Executar a comparação real e registrar os números nas seções 12 e 13 de specs/defined/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/spec.md — Refs: US-001, FR-001, FR-002, AC-001 — Depends: T007
  - [ ] **PREP**: Confirmar `OPENAI_API_KEY` disponível no ambiente de execução.
  - [ ] **EXECUTE**: Rodar o harness real contra `vivo_gold_banda_larga_pf/consultas.yaml` e coletar aprovações/ruído por alternativa.
  - [ ] **VERIFY**: Conferir que nenhuma escrita ocorreu em Qdrant de produção.
  - [ ] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [ ] **EVIDENCE**: Registrar os números coletados nas seções 12–13.
  - [ ] **IMPROVE**: Registrar qualquer ajuste necessário no harness.
  <!-- specsfy:evidence {"task":"T008","refs":["US-001","FR-001","FR-002","AC-001"],"files":["specs/draft/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/spec.md"],"commands":[{"run":"uv run pytest tests/test_spec0014_resumo_secao.py::test_comparacao_alternativas -v","exit":0}]} -->

- [ ] T009 [CODE] [US-001] Registrar `DEC-001` na seção 17 de specs/defined/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/spec.md — Refs: US-001, FR-003, AC-002, AC-003, AC-004, AC-006 — Depends: T008
  - [ ] **PREP**: Reler os números de T008.
  - [ ] **EXECUTE**: Escrever `DEC-001` com a alternativa escolhida (ou "manter como está", ou limitação registrada), a justificativa, os parâmetros de `chunker.py` afetados e a sinalização sobre `chunk_type`/`quality.py`.
  - [ ] **VERIFY**: Confirmar que a decisão é compreensível sem contexto adicional (leitura isolada da seção 17).
  - [ ] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [ ] **EVIDENCE**: Registrar a decisão escrita.
  - [ ] **IMPROVE**: Nenhuma melhoria adicional identificada, ou registrar a encontrada.

#### Fase final — Qualidade

- [ ] T010 [TEST] Executar regressão completa e rastreabilidade em `tests/test_spec0014_resumo_secao.py` — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T009
  - [ ] **PREP**: Identificar suites e gates a executar (`uv run pytest`, `uv run ruff check`, `check_traceability.mjs`).
  - [ ] **EXECUTE**: Executar a regressão completa da suíte e a verificação de rastreabilidade.
  - [ ] **VERIFY**: Confirmar ausência de gaps de cobertura para os IDs desta spec.
  - [ ] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [ ] **EVIDENCE**: Registrar contagens e comandos finais.
  - [ ] **IMPROVE**: Registrar retrospectiva do processo.

### 15. Ordem de execução

- Caminho crítico: T001–T006 → T007 → T008 → T009 → T010.
- Tarefas paralelas: T001, T002, T003, T004, T005 e T006 podem ser escritas em
  paralelo — são casos independentes antes do harness existir.
- Estratégia de MVP: não aplicável (US-001 é a única história; a spec inteira
  é o menor conjunto entregável).

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- `OPENAI_API_KEY` configurada no ambiente de execução dos testes (já usada
  em produção; sem isso, o caso de comparação real é `skip`, não `fail`).
- Base e gabarito já versionados em `documentos/vivo_gold_banda_larga_pf/`.

#### Riscos

- O gabarito de 10 consultas pode não ter caso suficiente para diferenciar as
  três alternativas → mitigação: AC-006 registra essa limitação como decisão
  aberta em vez de forçar uma escolha sem evidência.
- Custo de API OpenAI, mesmo pequeno, é um custo real e recorrente a cada
  execução do teste de comparação → mitigação: o teste correspondente é
  isolado e pode ser pulado (`skip`) fora de uma execução deliberada da
  comparação.
- A decisão pode exigir revisão do agrupamento por `chunk_type` em
  `quality.py` (risco herdado de BACKLOG-0005/SPEC-0006) → mitigação: AC-004
  exige que essa dependência seja sinalizada explicitamente, não ignorada.

#### Suposições

- O volume de chamadas à API OpenAI para este experimento (8 documentos, 10
  consultas, 3 alternativas) tem custo desprezível — default reversível,
  documentado como decisão explícita em DEC-002, não como aceitação
  silenciosa de custo recorrente maior.

### 17. Decisões

- **DEC-001**: [Decisão final sobre a colocação do resumo de seção —
  registrada por T009, ao final do Ato III, com base nos números reais da
  comparação. Pending até a execução das tarefas.]
- **DEC-002**: Usar o provider de embeddings `openai` real (não `fake` nem
  `huggingface` local) para a comparação — razão: `fake` não tem sinal
  semântico (SHA-256 determinístico), tornando qualquer comparação sem
  validade; `huggingface` exigiria instalar `sentence-transformers` como
  dependência nova só para este experimento. Alternativas consideradas:
  `fake` (descartado por falta de sinal semântico), `huggingface` local
  (descartado por dependência nova e custo de instalação/inferência).
  Trade-off aceito: custo real de API, mitigado pelo volume pequeno.
  Confirmado por Marcio em 2026-09-15 (Pergunta 1 da descoberta desta spec).

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
