# Especificação integrada: Decidir onde o resumo de seção vive e revisar as regras de corte do chunker

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0014 |
| Slug | 0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker |
| Status | Implementing |
| Effort | 6 |
| Effort updated at | 2026-09-15 |
| Effort rationale | Perfil `standard`: decisão de design com controle atual mais três alternativas, oráculo quantitativo de ruído, contratos distintos de recuperação, prova comparativa real e integração deliberada com provider externo pago, sem persistência nova nem interface. |
| ClickUp Task | |
| Milestones | M02 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | In Progress |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-15 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

A busca plana atual faz o resumo de seção (`chunk_type: "section_summary"`,
gerado por `_section_summary_chunks` em `src/pipeline/chunker.py:148-232`)
competir em pé de igualdade com os chunks detalhados da mesma recuperação,
sem aproveitar sua estrutura como índice navegacional. O baseline versionado
já aprova as 10 consultas do gabarito, e as três consultas amplas foram
escritas para serem satisfeitas por um `section_summary`. Portanto, contagem
de aprovações isolada não diferencia uma alternativa melhor e o antigo
"ruído percebido" não oferecia um oráculo reproduzível para decidir.

#### Resultado desejado

Uma decisão registrada — com o comportamento atual como controle e uma prova
comparativa reproduzível contra o mesmo corpus — sobre qual das três
alternativas de colocação do resumo de seção usar, ou se o comportamento atual
deve permanecer. A comparação preserva as 10 aprovações atuais, mede ruído por
uma regra objetiva, fixa previamente os parâmetros das estratégias e informa
quais parâmetros de chunking ou recuperação mudam. Essa decisão é o insumo
direto para a spec seguinte (BACKLOG-0017), que implementa a versão final de
produção e mede o efeito completo.

#### Métricas de sucesso

- O controle `atual` e as três alternativas são executados na mesma rodada,
  com o mesmo corpus, embeddings, consultas e parâmetros fixos:
  `text-embedding-3-small`, 1536 dimensões, `top_k=4` e limiar `0.5`.
- Uma estratégia só é elegível quando mantém 10/10 consultas aprovadas e não
  regride nenhuma consulta que o controle aprovou.
- O ruído operacional é a soma, por consulta, de: (a) resultados sem qualquer
  trecho de `deve_conter` nas categorias `ampla` e `especifica`; e (b)
  resultados com score maior ou igual a `0.5` em `sem_resposta`. A comparação
  também registra colisões em que resumo e detalhe da mesma seção aparecem no
  mesmo `top_k`.
- A decisão usa a ordem objetiva: menor ruído, depois menos colisões, depois
  menor custo de implementação (`atual=0`, `metadado=1`,
  `chunk_com_peso=2`, `indice_de_roteamento=3`). Uma alternativa precisa
  melhorar estritamente ruído ou colisões sem regressão; caso contrário,
  permanece o comportamento atual.
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
- `output/e2e_vivo_gold_banda_larga_pf/validation-6808524e-e8a4-4140-a983-5037dfd6df60.json`
  — baseline histórico aprovado em 10/10 consultas, 208 chunks observados e
  dimensão 1536; serve como evidência de contexto, mas o controle é recalculado
  na mesma rodada das alternativas.
- `output/e2e_vivo_gold_banda_larga_pf/chunks.json` — corpus histórico com 191
  chunks detalhados e 17 resumos de seção.
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
- **Q**: como decidir se o baseline já aprova 10/10 consultas? → **A**: exigir
  ausência de regressão e comparar ruído operacional e colisões por regras
  quantitativas fixadas antes da execução. Ver DEC-003.
- **Q**: como impedir que uma estratégia seja ajustada ao próprio gabarito? →
  **A**: parâmetros das três estratégias ficam congelados nesta definição; o
  gabarito é apenas o oráculo de capacidade e não será usado para busca de
  hiperparâmetros. Qualquer calibração posterior pertence à spec seguinte.

#### Dúvidas abertas

- Nenhuma bloqueante para o Definition Gate. A decisão substantiva sobre
  qual alternativa vence (ou se nenhuma vence) só é conhecida ao executar a
  comparação real durante o Ato III (tarefas T007–T009) e será registrada como
  `DEC-001` na seção 17 nesse momento — não é uma lacuna de definição, é o
  próprio resultado que a spec produz.

### 3. Escopo e atores

#### Incluído

- Implementar, de forma mínima (protótipo, não necessariamente código de
  produção final), o controle atual e as três alternativas de colocação do resumo de seção:
  (a) metadado anexado ao chunk detalhado da mesma seção; (b) chunk indexado
  com peso/sinal que evita competir em pé de igualdade com chunks detalhados;
  (c) índice de roteamento hierárquico separado da busca principal.
- Rodar o controle e cada alternativa contra o gabarito completo de
  `vivo_gold_banda_larga_pf/consultas.yaml`, usando o provider de embeddings
  `openai` real, sem gravar em Qdrant de produção nem alterar bases já
  indexadas.
- Reaproveitar na mesma rodada os embeddings de textos idênticos e registrar
  modelo, dimensões, parâmetros, hashes do corpus/gabarito e resultados por
  consulta, sem expor a credencial.
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

#### AC-001 — Comparar o controle e as três alternativas contra o gabarito completo

**Cobre**: US-001, FR-001, FR-002, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @AC-001
Feature: Comparar alternativas de colocação do resumo de seção

  Scenario: Executar a comparação reproduzível contra o gabarito real
    Given o gabarito de "documentos/vivo_gold_banda_larga_pf/consultas.yaml"
    And os parâmetros text-embedding-3-small, 1536 dimensões, top_k 4 e limiar 0.5 estão congelados
    When o controle atual e as alternativas metadado, chunk_com_peso e indice_de_roteamento avaliam as mesmas 10 consultas com os mesmos embeddings
    Then cada estratégia registra aprovações, regressões, ruído operacional e colisões por consulta
    And o relatório registra os hashes do corpus e do gabarito
    And nenhuma escrita acontece em Qdrant de produção nem em base já indexada
```

#### AC-002 — Nenhuma alternativa supera o comportamento atual

**Cobre**: US-001, FR-002, FR-003, NFR-001

```gherkin
@US-001 @FR-002 @FR-003 @NFR-001 @AC-002
Feature: Comparar alternativas de colocação do resumo de seção

  Scenario: Decisão de manter como está quando nenhuma alternativa supera o atual
    Given o controle atual com 10 de 10 consultas aprovadas
    And as três alternativas comparadas contra o mesmo controle
    When uma alternativa regride qualquer consulta ou nenhuma reduz estritamente ruído ou colisões
    Then a decisão registrada na seção 17 é "manter como está"
    And a justificativa cita aprovações, ruído, colisões e custo que sustentam a decisão
```

#### AC-003 — Decisão lista os parâmetros do chunker que mudam

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-003
Feature: Comparar alternativas de colocação do resumo de seção

  Scenario: Alternativa vencedora exige mudança de parâmetro do chunker
    Given uma alternativa elegível identificada pela regra objetiva de decisão
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
    Given o controle e as alternativas em execução isolada
    When ocorre um erro inesperado durante a geração de embeddings ou avaliação de uma consulta
    Then nenhum resíduo é deixado em Qdrant de produção nem em base já indexada
    And o erro é registrado sem ocultar resultados já concluídos
    And a comparação fica inconclusiva e nenhuma alternativa é escolhida
```

#### AC-006 — Evidência insuficiente não força uma alternativa

**Cobre**: US-001, FR-001, FR-002, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @NFR-001 @AC-006
Feature: Comparar alternativas de colocação do resumo de seção

  Scenario: Baseline inesperado ou comparação incompleta
    Given o baseline já aprovado em 10 de 10 consultas
    When a nova rodada não reproduz 10 de 10 ou alguma estratégia não conclui
    Then a spec registra a comparação como inconclusiva na seção 17
    And não força a escolha de uma alternativa sem evidência
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O protótipo deve implementar o controle `atual` e as três
  alternativas de colocação do resumo de seção de forma isolada, sem gravar em
  Qdrant de produção nem alterar bases já indexadas, mesmo em caso de erro.
- **FR-002**: A comparação deve rodar as quatro estratégias contra o gabarito
  completo de `documentos/vivo_gold_banda_larga_pf/consultas.yaml`, na mesma
  rodada e com os mesmos embeddings OpenAI reais, usando
  `text-embedding-3-small`, 1536 dimensões, `top_k=4` e limiar `0.5`. Por
  estratégia e consulta, deve registrar aprovação, regressão, ruído
  operacional e colisão resumo-detalhe, além dos hashes do corpus e gabarito.
- **FR-003**: A decisão final deve ser registrada na seção 17 desta spec,
  incluindo a alternativa escolhida, "manter como está" ou "inconclusiva".
  Nenhuma alternativa com regressão é elegível. Entre as elegíveis, a ordem é
  menor ruído, menos colisões e menor custo (`atual=0`, `metadado=1`,
  `chunk_com_peso=2`, `indice_de_roteamento=3`). A decisão também lista os
  parâmetros de `chunker.py` e recuperação afetados e se o agrupamento por
  `chunk_type` em `quality.py` precisa ser revisto, sem implementar a mudança
  final aqui.

#### Não funcionais

- **NFR-001**: Auditabilidade, isolamento e reprodutibilidade — cada execução
  registra configuração fixa, hashes, resultados por consulta e agregados,
  sem tocar Qdrant de produção nem consumir credencial fora do fluxo existente
  de `OPENAI_API_KEY`. A implementação deve construir somente o vector store
  `in_memory` pela factory e reutilizar embeddings idênticos dentro da rodada.
  **Verificação**: testes de contrato, inspeção da evidência e guarda que
  rejeita qualquer provider de vector store diferente de `in_memory`.

#### Erros e casos-limite

- Ausência de `RUN_SPEC0014_REAL=1` → a prova paga é marcada `skip` na suíte
  geral. T008 só executa deliberadamente com essa chave de ativação.
- Ausência de `OPENAI_API_KEY` na execução deliberada → a prova é marcada
  `skip`, mas T008 e o Delivery Gate permanecem pendentes.
- Falha da API ou baseline diferente de 10/10 → comparação inconclusiva, sem
  escolha de alternativa.
- Empate em aprovações, ruído e colisões → menor custo desempata entre
  alternativas; empate completo com o controle mantém o comportamento atual.

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

- O protótipo vive em `tests/spec0014/_harness.py`, exercitado por
  `tests/spec0014/test_resumo_secao.py`, sem alterar `src/pipeline/chunker.py`.
  A pasta dedicada permite que a rastreabilidade examine somente os marcadores
  desta spec, evitando colisão com IDs locais de specs anteriores.
- A rodada carrega a saída existente de `chunker.py` uma vez, calcula o
  `section_key` efêmero como
  `document_id|titulo|secao`, gera embeddings uma vez por texto único e
  reutiliza esses vetores nas quatro estratégias. Nenhum novo campo é
  persistido nesta spec.
- **Controle `atual`**: indexa juntos os 191 chunks detalhados e os 17 resumos
  de seção e retorna os quatro maiores scores de cosseno, reproduzindo a busca
  plana atual.
- **Alternativa `metadado`**: não vetoriza os 17 resumos. Anexa
  `section_summary_text` e `section_key` aos chunks detalhados elegíveis; na
  montagem do contexto, inclui o resumo uma única vez por seção recuperada,
  sem alterar o vetor ou o score do detalhe.
- **Alternativa `chunk_com_peso`**: indexa detalhe e resumo juntos, recupera
  12 candidatos e aplica `score_final = score_cosseno * 0.85` somente aos
  resumos antes de selecionar os quatro resultados. Score bruto e score final
  ficam registrados.
- **Alternativa `indice_de_roteamento`**: mantém um índice somente de resumos e
  outro somente de detalhes. Consulta o melhor resumo; quando seu score é
  maior ou igual a `0.5`, monta até quatro resultados com o resumo roteador
  mais os três melhores detalhes do mesmo `section_key`. Abaixo do limiar,
  retorna os quatro melhores detalhes globais.
- Os parâmetros acima são congelados antes da prova. Esta spec não realiza
  ajuste de peso, `candidate_k`, limiar ou quantidade de resultados usando o
  próprio gabarito.
- A avaliação de cada consulta reaproveita a lógica de `validation.py`
  para o veredito de aprovação e adiciona no harness somente os agregados de
  ruído e colisão definidos na seção 1.
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
specs/in-progress/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/
  spec.md
tests/spec0014/
  test_resumo_secao.py
  _harness.py
```

### 9. Modelo de dados

#### Entidades

- Nenhuma entidade persistente nova. O protótipo usa dois contratos efêmeros:
  `section_key` (`document_id|titulo|secao`) liga resumo e detalhes sem colisão
  entre documentos; `StrategyResult` registra configuração, resultados por
  consulta, aprovações, regressões, ruído e colisões.

#### Estados e transições

- `StrategyResult` pode ficar `concluido`, `falhou` ou `inconclusivo`. Qualquer
  falha da API, baseline diferente de 10/10 ou ausência da prova real impede a
  escolha de alternativa.

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
  para diferenciar as estratégias com sinal semântico. Autenticação por
  `OPENAI_API_KEY` do `.env`, carregado explicitamente por `load_env()` apenas
  no teste real ativado por `RUN_SPEC0014_REAL=1`. Modelo fixo
  `text-embedding-3-small`, dimensões 1536. Sem retry/timeout adicional além
  do adapter existente. A rodada reaproveita vetores por texto único para não
  multiplicar custo pelas quatro estratégias.

#### Documentação das APIs consultadas

- Nenhuma documentação externa nova consultada; o adapter OpenAI já existente
  é reaproveitado sem alteração de contrato.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: contratos estruturais das quatro estratégias, cálculo de ruído,
  guarda de isolamento e regra de decisão.
- **Integração/contrato**: uma rodada deliberada, ativada por
  `RUN_SPEC0014_REAL=1`, chama o provider `openai` e compara o controle com as
  três alternativas usando vetores compartilhados.
- **BDD/aceite**: os seis cenários da seção 6 orientam os casos TDD abaixo.
- **Runner TDD**: Python/Pytest, convenção já estabelecida no repositório
  (`uv run pytest`); não há Node nem PHP envolvidos nesta spec.
- **E2E**: Não aplicável — sem jornada de usuário ponta a ponta nesta spec.
- **Verificação manual**: leitura da decisão registrada na seção 17 ao final,
  para confirmar que a justificativa é compreensível sem contexto adicional.
- **Segurança da prova paga**: a suíte comum mantém a comparação real em
  `skip`; T008 usa explicitamente `RUN_SPEC0014_REAL=1`. A ausência da chave
  não quebra a suíte comum, mas impede concluir T008.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, NFR-001, AC-001 | AC-001 na seção 6 | Contratos e comparação real em `tests/spec0014/test_resumo_secao.py` | RED válido: 4 contratos falham por ausência de `tests.spec0014._harness`; prova real permanece em `skip` explícito | GREEN: `uv run pytest tests/spec0014/test_resumo_secao.py -v` -> 9 passed, 1 skipped | Passed |
| US-001, FR-002, FR-003, NFR-001, AC-002 | AC-002 na seção 6 | `test_decisao_rejeita_regressao_e_exige_melhoria_estrita` | RED válido: `ModuleNotFoundError` do harness ainda não implementado | GREEN: `uv run pytest tests/spec0014/test_resumo_secao.py -v` -> 9 passed, 1 skipped | Passed |
| US-001, FR-003, NFR-001, AC-003 | AC-003 na seção 6 | `test_decisao_lista_parametros_da_estrategia_vencedora` | RED válido: `ModuleNotFoundError` do harness ainda não implementado | GREEN: `uv run pytest tests/spec0014/test_resumo_secao.py -v` -> 9 passed, 1 skipped | Passed |
| US-001, FR-003, NFR-001, AC-004 | AC-004 na seção 6 | `test_decisao_sinaliza_impacto_em_chunk_type` | RED válido: `ModuleNotFoundError` do harness ainda não implementado | GREEN: `uv run pytest tests/spec0014/test_resumo_secao.py -v` -> 9 passed, 1 skipped | Passed |
| US-001, FR-001, NFR-001, AC-005 | AC-005 na seção 6 | `test_falha_nao_toca_qdrant_e_torna_comparacao_inconclusiva` | RED válido: `ModuleNotFoundError` do harness ainda não implementado | GREEN: `uv run pytest tests/spec0014/test_resumo_secao.py -v` -> 9 passed, 1 skipped | Passed |
| US-001, FR-001, FR-002, NFR-001, AC-006 | AC-006 na seção 6 | `test_empate_sem_evidencia_registra_limitacao` | RED válido: `ModuleNotFoundError` do harness ainda não implementado | GREEN: `uv run pytest tests/spec0014/test_resumo_secao.py -v` -> 9 passed, 1 skipped | Passed |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Integração | `RUN_SPEC0014_REAL=1 uv run pytest tests/spec0014/test_resumo_secao.py::test_comparacao_real_reproduzivel -v` | Passed |
| FR-001 | AC-005 | Unidade | `uv run pytest tests/spec0014/test_resumo_secao.py::test_falha_nao_toca_qdrant_e_torna_comparacao_inconclusiva` | Passed |
| FR-001 | AC-006 | Unidade | `uv run pytest tests/spec0014/test_resumo_secao.py::test_empate_sem_evidencia_registra_limitacao` | Passed |
| FR-002 | AC-001 | Unidade e integração | `uv run pytest tests/spec0014/test_resumo_secao.py -v` | Passed |
| FR-002 | AC-002 | Unidade | `uv run pytest tests/spec0014/test_resumo_secao.py::test_decisao_rejeita_regressao_e_exige_melhoria_estrita` | Passed |
| FR-003 | AC-002 | Unidade | `uv run pytest tests/spec0014/test_resumo_secao.py::test_decisao_rejeita_regressao_e_exige_melhoria_estrita` | Passed |
| FR-003 | AC-003 | Unidade | `uv run pytest tests/spec0014/test_resumo_secao.py::test_decisao_lista_parametros_da_estrategia_vencedora` | Passed |
| FR-003 | AC-004 | Unidade | `uv run pytest tests/spec0014/test_resumo_secao.py::test_decisao_sinaliza_impacto_em_chunk_type` | Passed |
| NFR-001 | AC-001 | Unidade e integração | `uv run pytest tests/spec0014/test_resumo_secao.py -v` | Passed |
| NFR-001 | AC-005 | Unidade | `uv run pytest tests/spec0014/test_resumo_secao.py::test_falha_nao_toca_qdrant_e_torna_comparacao_inconclusiva` | Passed |
| NFR-001 | AC-006 | Unidade | `uv run pytest tests/spec0014/test_resumo_secao.py::test_empate_sem_evidencia_registra_limitacao` | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY após atualização de comportamento em 2026-09-15.
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/spec.md --allow-draft` → `VALID DRAFT`; revisão de achados com `--root .` → `PASSED`.
- **Achados**:

- **FIND-ARCH-001** [P1] [Resolved] Plano técnico e T007 não proibiam explicitamente carregar config.yaml real para construir o vector store do protótipo, cujo default de produção é qdrant — Refs: FR-001 — Evidence: src/app/main.py:69 — Effect: risco de escrita real em produção durante um experimento que deveria ser isolado — Suggestion: construir InMemoryVectorStoreAdapter e o adapter openai diretamente pela factory, nunca a partir de config.yaml carregado; corrigido na seção 8 e em T007.
- **FIND-PROD-001** [P1] [Resolved] Baseline já aprovava 10/10 e ruído não possuía cálculo verificável — Refs: FR-002, FR-003 — Evidence: output/e2e_vivo_gold_banda_larga_pf/validation-6808524e-e8a4-4140-a983-5037dfd6df60.json — Effect: qualquer vencedor poderia ser escolhido por interpretação subjetiva — Suggestion: exigir ausência de regressão e usar ruído, colisões e custo em ordem objetiva; corrigido nas seções 1, 6 e 7.
- **FIND-ARCH-002** [P1] [Resolved] Metadado, peso e roteamento eram rótulos sem algoritmo comparável no adapter atual — Refs: FR-001, FR-002 — Evidence: src/pipeline/providers/vectorstores/base.py — Effect: implementações diferentes poderiam produzir conclusões incompatíveis — Suggestion: congelar representação, ranking, fallback e parâmetros de cada estratégia; corrigido na seção 8.
- **FIND-PROD-002** [P2] [Accepted] As consultas amplas foram construídas para validar o resumo atual — Refs: FR-002 — Evidence: documentos/vivo_gold_banda_larga_pf/consultas.yaml — Effect: o gabarito preserva a capacidade atual e não deve ser usado para ajustar parâmetros — Suggestion: tratá-lo como oráculo fixo de capacidade, recalcular o controle na mesma rodada e proibir calibração com essas consultas; decisão registrada em DEC-003.
- Cobertura mínima `US/FR/NFR ↔ 3 AC` confirmada: US-001 em 6 ACs;
  FR-001 em 3; FR-002 em 3; FR-003 em 3; NFR-001 em 6.

#### Gate do Ato II — Plano

- **Resultado**: READY — tarefas completas e RED materializado novamente em 2026-09-15.
- **Comandos**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs <spec.md> --allow-draft` → `VALID DRAFT`; `uv run pytest tests/spec0014/test_resumo_secao.py -v` → `9 failed, 1 skipped`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs <spec.md> tests/spec0014 --full-chain` → `11/11`, `OK`.
- **Achados**: As nove falhas decorrem exclusivamente da ausência deliberada de
  `tests/spec0014/_harness.py`, implementação atribuída a T007. A prova real
  paga permanece protegida por `RUN_SPEC0014_REAL=1` e não foi executada.

#### Gate do Ato III — Entrega

- **Resultado**: In Progress (T007 e T008 concluídos com GREEN e prova real; T009 registra `DEC-001`, T010 fecha regressão/rastreabilidade final antes de `Delivery Gate: Passed`)
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/spec.md tests/spec0014 --full-chain` → 11/11, OK.
- **Achados**: Nenhum bloqueante. `uv run pytest tests/spec0014/test_resumo_secao.py -v` → 9 passed, 1 skipped (T007). `RUN_SPEC0014_REAL=1 uv run pytest tests/spec0014/test_resumo_secao.py::test_comparacao_real_reproduzivel -v` → PASSED, 45.32s (T008). Regressão completa `uv run pytest -q` → 276 passed, 1 skipped, 27 failed + 10 errors pré-existentes (Postgres local ausente, fora do escopo). `uv run ruff check .` → limpo. Resultado real: as três alternativas regrediram (9/10) contra o controle (10/10); nenhuma é elegível — decisão objetiva é `atual` (manter como está), registrada em `DEC-001`.

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

- [x] T001 [TEST] [TDD] [US-001] [P] Derivar do AC-001 os contratos das quatro estratégias e a comparação real em `tests/spec0014/test_resumo_secao.py` — Refs: US-001, FR-001, FR-002, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Confirmados parâmetros congelados, oráculo de ruído e ausência de `tests/spec0014/_harness.py`.
  - [x] **EXECUTE**: Escritos casos para controle, metadado, peso, roteamento e prova real deliberada, cada qual com marcador `SPECSFY` próprio.
  - [x] **VERIFY**: RED válido observado nos quatro contratos; a prova real ficou em `skip` deliberado.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: `uv run pytest tests/spec0014/test_resumo_secao.py -v` → 9 failed, 1 skipped; linha do AC-001 atualizada na seção 11.
  - [x] **IMPROVE**: Casos verificam algoritmos e constantes, rejeitando implementação que devolva apenas o formato esperado.

- [x] T002 [TEST] [TDD] [US-001] [P] Derivar do AC-002 a regra sem regressão e com melhoria estrita em `tests/spec0014/test_resumo_secao.py` — Refs: US-001, FR-002, FR-003, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Confirmados baseline 10/10 e ordem objetiva de decisão.
  - [x] **EXECUTE**: Escritos casos que rejeitam regressão, exigem melhoria estrita e desempatam por custo.
  - [x] **VERIFY**: RED válido por ausência do comportamento de decisão no harness.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: Comando focal incluído na execução de 9 failed, 1 skipped; linha do AC-002 atualizada na seção 11.
  - [x] **IMPROVE**: Números sintéticos mantidos pequenos e inequívocos.

- [x] T003 [TEST] [TDD] [US-001] [P] Derivar do AC-003 a saída de parâmetros da estratégia vencedora em `tests/spec0014/test_resumo_secao.py` — Refs: US-001, FR-003, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Confirmados os parâmetros congelados da seção 8.
  - [x] **EXECUTE**: O caso exige parâmetros de chunking e recuperação aplicáveis na decisão.
  - [x] **VERIFY**: RED válido por ausência do harness.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: Comando focal incluído na execução de 9 failed, 1 skipped; linha do AC-003 atualizada na seção 11.
  - [x] **IMPROVE**: O contrato diferencia explicitamente parâmetro inalterado de parâmetro ausente.

- [x] T004 [TEST] [TDD] [US-001] [P] Derivar do AC-004 o impacto em `chunk_type` e `quality.py` em `tests/spec0014/test_resumo_secao.py` — Refs: US-001, FR-003, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Mapeadas as estratégias que removem ou separam `section_summary` da busca plana.
  - [x] **EXECUTE**: O caso exige sinalização estruturada do impacto e da revisão futura.
  - [x] **VERIFY**: RED válido por ausência do harness.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: Comando focal incluído na execução de 9 failed, 1 skipped; linha do AC-004 atualizada na seção 11.
  - [x] **IMPROVE**: O teste evita inferência por texto livre na decisão.

- [x] T005 [TEST] [TDD] [US-001] [P] Derivar do AC-005 a guarda contra provider de produção e falha inconclusiva em `tests/spec0014/test_resumo_secao.py` — Refs: US-001, FR-001, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Confirmado que a factory é a única criação permitida de vector store.
  - [x] **EXECUTE**: O caso intercepta `ProviderFactory.create_vector_store`, rejeita provider diferente de `in_memory`, simula erro e exige resultado inconclusivo.
  - [x] **VERIFY**: RED válido por ausência do harness.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: Comando focal incluído na execução de 9 failed, 1 skipped; linha do AC-005 atualizada na seção 11.
  - [x] **IMPROVE**: A sentinela intercepta a fronteira real da factory.

- [x] T006 [TEST] [TDD] [US-001] [P] Derivar do AC-006 empate e evidência insuficiente em `tests/spec0014/test_resumo_secao.py` — Refs: US-001, FR-001, FR-002, NFR-001, AC-006 — Depends: none
  - [x] **PREP**: Confirmadas as saídas `manter como está` e `inconclusiva`.
  - [x] **EXECUTE**: Escritos casos para empate completo e baseline inesperado.
  - [x] **VERIFY**: RED válido por ausência do harness.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: Comando focal incluído na execução de 9 failed, 1 skipped; linha do AC-006 atualizada na seção 11.
  - [x] **IMPROVE**: O contrato impede vencedor arbitrário em empate ou evidência insuficiente.

#### Fase 2 — US-001 Decidir a colocação do resumo de seção com evidência comparativa (P1)

**Objetivo**: produzir a decisão registrada e comprovada que a spec seguinte
(BACKLOG-0017) consome como insumo direto.
**Teste independente**: `uv run pytest tests/spec0014/test_resumo_secao.py -v` e leitura da seção 17.

- [x] T007 [CODE] [US-001] Implementar as quatro estratégias, métricas e decisão em `tests/spec0014/_harness.py` — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006
  - [x] **PREP**: Confirmado RED (9 failed, 1 skipped), a fronteira de providers (`tests/test_provider_boundaries.py`) e relidos `chunker.py`, `validation.py` e `providers/factory.py`/`contracts.py`. `build_documentation.mjs --check` → exit 0 (sem mudança material; decisão registrada em `USER-PROFILE.md`), dispensando a reconstrução completa.
  - [x] **EXECUTE**: Implementado `tests/spec0014/_harness.py` — `projetar_estrategia`, `reranquear_com_peso`, `comparar_todas` e `decidir`. Todo índice vem de `ProviderFactory.create_vector_store("in_memory")`; nenhum código lê `config.yaml` para escolher provider.
  - [x] **VERIFY**: `uv run pytest tests/spec0014/test_resumo_secao.py -v` → 9 passed, 1 skipped (prova real). Regressão completa `uv run pytest -q` → 276 passed, 1 skipped, 27 failed + 10 errors pré-existentes em `tests/test_app_*.py`/`test_app_migrations.py` (Postgres local ausente, confirmado idêntico ao baseline anterior, fora do escopo desta spec). `uv run ruff check .` → limpo.
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: GREEN confirmado; arquivo criado `tests/spec0014/_harness.py`. `monitor_context --check` → CURRENT.
  - [x] **IMPROVE**: Corrigido um byte nulo introduzido acidentalmente na escrita do arquivo (causava `SyntaxError` na importação) e três linhas acima de 100 colunas, ambos antes de comitar.
  <!-- specsfy:evidence {"task":"T007","refs":["US-001","FR-001","FR-002","FR-003","NFR-001","AC-001","AC-002","AC-003","AC-004","AC-005","AC-006"],"files":["tests/spec0014/_harness.py"],"commands":[{"run":"uv run pytest tests/spec0014/test_resumo_secao.py -v","exit":0}]} -->

- [x] T008 [TEST] [US-001] Executar deliberadamente a comparação real e registrar os números em `specs/in-progress/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/spec.md` — Refs: US-001, FR-001, FR-002, NFR-001, AC-001 — Depends: T007
  - [x] **PREP**: Confirmado `OPENAI_API_KEY` no `.env`; `RUN_SPEC0014_REAL=1` usado deliberadamente por decisão explícita de Marcio em 2026-09-15. PostgreSQL de teste não é necessário para esta tarefa (nenhum código de `src/app/` é exercitado).
  - [x] **EXECUTE**: Rodado `RUN_SPEC0014_REAL=1 uv run pytest tests/spec0014/test_resumo_secao.py::test_comparacao_real_reproduzivel -v` → PASSED (45.32s). Coletados os números reais chamando `comparar_todas(...)` diretamente uma segunda vez (o teste só afirma formato, não imprime valores) — **duas chamadas reais à API OpenAI no total nesta tarefa**, registrado por transparência.
  - [x] **VERIFY**: Controle `atual` reproduziu 10/10 (`aprovadas: 10, total: 10`). Nenhum provider diferente de `in_memory` foi construído (guarda de T005 não disparou). Métricas completas para as 4 estratégias (ruído, colisões, regressões).
  - [x] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [x] **EVIDENCE**: Números reais registrados na seção 12. `corpus_sha256=28a09960641d18ad47b1be90bcb46ee1be803224532e4fc34691d61da02c156f`, `gabarito_sha256=65eec51297952666232665edc8113ae9aa1e3d7e567b329b453806b1f204d9e7`. Resultado: **as três alternativas regrediram** (9/10 aprovadas, contra 10/10 do controle) — nenhuma é elegível pela regra "sem regressão"; a decisão objetiva (seção 17) é `atual` (manter como está).
  - [x] **IMPROVE**: Nenhum ajuste no harness — o resultado (nenhuma alternativa vence) é uma conclusão válida da prova, não um defeito do protótipo. Registrado como limite de escopo: os protótipos das três alternativas são mínimos (T007) e podem não ser a melhor implementação possível de cada ideia.

- [ ] T009 [DOC] [US-001] Registrar `DEC-001` na seção 17 de `specs/in-progress/0014-decidir-onde-o-resumo-de-secao-vive-e-revisar-as-regras-de-corte-do-chunker/spec.md` — Refs: US-001, FR-003, AC-002, AC-003, AC-004, AC-006 — Depends: T008
  - [ ] **PREP**: Reler os números de T008.
  - [ ] **EXECUTE**: Escrever `DEC-001` com a alternativa escolhida (ou "manter como está", ou limitação registrada), a justificativa, os parâmetros de `chunker.py` afetados e a sinalização sobre `chunk_type`/`quality.py`.
  - [ ] **VERIFY**: Confirmar que a decisão é compreensível sem contexto adicional (leitura isolada da seção 17).
  - [ ] **VISUAL**: Não aplicável — spec sem interface para pessoas.
  - [ ] **EVIDENCE**: Registrar a decisão escrita.
  - [ ] **IMPROVE**: Nenhuma melhoria adicional identificada, ou registrar a encontrada.

#### Fase final — Qualidade

- [ ] T010 [TEST] Executar regressão completa e rastreabilidade isolada em `tests/spec0014/` — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T009
  - [ ] **PREP**: Confirmar PostgreSQL de teste ativo e identificar `uv run pytest`, `uv run ruff check` e `check_traceability.mjs --full-chain`.
  - [ ] **EXECUTE**: Executar a regressão completa e conferir rastreabilidade usando `tests/spec0014` como raiz, sem absorver marcadores de outras specs.
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

- `OPENAI_API_KEY` configurada no `.env` e carregada explicitamente pelo teste
  real; `RUN_SPEC0014_REAL=1` confirma a intenção de consumir a API. Sem uma
  dessas condições, a prova é `skip` e T008 não pode ser concluída.
- Base e gabarito já versionados em `documentos/vivo_gold_banda_larga_pf/`.
- PostgreSQL de teste ativo antes da regressão completa de T010; a aplicação
  não usa esse banco no experimento, mas a suíte existente depende dele.

#### Riscos

- O gabarito de 10 consultas pode não diferenciar as estratégias e já foi
  construído para preservar a capacidade dos resumos atuais → mitigação:
  controle recalculado na mesma rodada, parâmetros congelados, ausência de
  regressão obrigatória e AC-006 sem escolha forçada.
- Custo de API OpenAI, mesmo pequeno, é um custo real e recorrente a cada
  execução deliberada → mitigação: flag explícita e cache em memória por texto
  único, sem multiplicar embeddings pelas quatro estratégias.
- A decisão pode exigir revisão do agrupamento por `chunk_type` em
  `quality.py` (risco herdado de BACKLOG-0005/SPEC-0006) → mitigação: AC-004
  exige que essa dependência seja sinalizada explicitamente, não ignorada.

#### Suposições

- O volume continua pequeno para uma execução deliberada, mas é proporcional
  aos textos únicos dos 208 chunks e às 10 consultas, não apenas à quantidade
  de documentos. O custo é registrado como decisão explícita em DEC-002.

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
- **DEC-003**: Tratar o gabarito existente como oráculo fixo de capacidade,
  não como conjunto para calibrar parâmetros. Recalcular o controle `atual` na
  mesma rodada, excluir qualquer estratégia com regressão e decidir pela ordem
  ruído, colisões e custo definida na seção 1. Razão: o baseline histórico já
  aprova 10/10 e as consultas amplas foram escritas para a capacidade dos
  resumos atuais; uma contagem isolada ou avaliação subjetiva não sustentaria
  uma escolha. Decisão autorizada por Marcio ao solicitar a aplicação das
  recomendações da auditoria em 2026-09-15.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
