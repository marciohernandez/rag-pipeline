# Especificação integrada: Cobrir o comportamento do backend real do Qdrant

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0011 |
| Slug | 0011-cobrir-comportamento-backend-real-qdrant |
| Status | Complete |
| Effort | 3 |
| Effort updated at | 2026-09-04 |
| Effort rationale | Caracterização mecânica seguindo padrão já existente (`tests/test_describe_scope_backends.py`, T033 da SPEC-0004): um dublê mínimo por operação, sem lógica nova de produção. Risco real está em cobrir corretamente a tradução de argumentos (filtro de escopo, `PointStruct`, `PointIdsList`) e o caminho de erro de `scope_ids`, não em complexidade estrutural. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-07 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

Nenhum teste do repositório exercita o `_QdrantBackend` real
(`src/pipeline/providers/vectorstores/qdrant.py`). Toda a suíte de
conformidade (`tests/test_vectorstore_conformance.py`,
`tests/test_qdrant_sync.py`) injeta `FakeVectorBackend`/`DictVectorBackend`
como cliente, então `_create_backend()` nunca roda e o código que traduz
`ensure`, `write`, `search`, `scope_ids` e `remove` para o SDK
`qdrant-client` só é executado em produção. A SPEC-0004 cobriu a superfície de
`describe` contra um cliente-dublê (`tests/test_describe_scope_backends.py`);
as outras quatro operações do port seguem sem prova de comportamento.

#### Resultado desejado

Erro de tradução entre o contrato neutro e o SDK do Qdrant passa a falhar em
`uv run pytest`, sem exigir rede, antes de aparecer numa sincronização real.

#### Métricas de sucesso

- `_QdrantBackend` real tem caso de teste próprio para `ensure`, `write`,
  `search`, `scope_ids` (incluindo paginação e erro) e `remove`, todos
  passando sem rede.
- `uv run pytest` permanece verde na suíte inteira após a inclusão dos novos
  casos.

### 2. Research e esclarecimentos

#### Researchs executados

- Nenhuma pesquisa externa; a fonte é o código já implementado em
  `src/pipeline/providers/vectorstores/qdrant.py` e `base.py`, e o padrão de
  teste já aprovado em `tests/test_describe_scope_backends.py`.

#### Fontes e contexto consultados

- `src/pipeline/providers/vectorstores/qdrant.py`: implementação real do
  `_QdrantBackend` e do `QdrantVectorStoreAdapter`.
- `src/pipeline/providers/vectorstores/base.py`: `BaseVectorStoreAdapter`,
  `MirrorMixin` e `synchronize`, que chamam o backend real por
  `_resolve_backend()`.
- `tests/test_describe_scope_backends.py`: padrão aprovado de dublê mínimo
  por operação, usado pela SPEC-0004 para caracterizar `describe`.
- `specs/backlog/0013-cobrir-o-comportamento-dos-backends-reais-de-vector-store.md`:
  brief refinado com regras de negócio e critérios de aceite já decididos.
- `specs/completed/0010-enxugar-providers-concretos-qdrant/spec.md`: confirma
  que Qdrant é o único provider concreto restante.

#### Documentação consultada

- Nenhuma documentação externa consultada; a API do `qdrant-client` usada
  (`get_collections`, `create_collection`, `scroll`, `upsert`, `delete`,
  `search`) já está em uso no código de produção existente.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: o dublê deve imitar o SDK inteiro ou só os métodos usados? → **A**:
  só o subconjunto explícito de métodos usados por operação, seguindo
  `_ClienteQdrant` em `tests/test_describe_scope_backends.py` (decidido no
  refinamento do BACKLOG-0013).
- **Q**: os testes devem provar os argumentos enviados ao SDK ou só a
  tradução da resposta? → **A**: os dois lados — argumento exato enviado e
  resposta traduzida de volta ao contrato neutro (decidido no refinamento do
  BACKLOG-0013).

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Teste de comportamento do `_QdrantBackend` real para `ensure`, `write`,
  `search`, `scope_ids` (paginação completa e caminho de erro) e `remove`
  (via `MirrorMixin.delete_ids`), com cliente-dublê injetado por `_conn()`,
  sem rede.
- Registro da nova baseline de regressão (`uv run pytest`) com os casos
  adicionados.

#### Fora de escopo

- ChromaDB e Pinecone — removidos pela SPEC-0010; não existem mais no
  projeto.
- `describe` — já coberto pela SPEC-0004 em
  `tests/test_describe_scope_backends.py`.
- Teste de integração contra um Qdrant real com rede.
- Qualquer mudança de comportamento de produção do adapter, do
  `_QdrantBackend` ou do `MirrorMixin`.
- Interface para pessoas — este componente não tem tela; é operado por CLI
  já existente (`pipeline.py`, `search.py`).

#### Atores

- **Pessoa que opera o pipeline**: executa sincronizações e depende de o CI
  capturar erro de tradução com o SDK antes de uma execução real.
- **Pessoa que troca de provider de banco vetorial**: precisa que a
  tradução de argumentos e respostas do backend Qdrant esteja provada, para
  usar o mesmo padrão ao avaliar um provider futuro.

### 4. Princípios e restrições do projeto

- **PR-001**: o dublê do SDK imita somente o subconjunto de métodos
  efetivamente chamado por cada operação (`get_collections`,
  `create_collection`, `scroll`, `upsert`, `delete`, `search`); não criar um
  fake genérico e reutilizável do SDK inteiro.
- **PR-002**: esta entrega é caracterização por teste; não altera
  comportamento de produção do adapter, do `_QdrantBackend` nem do
  `MirrorMixin`.
- **PR-003**: cada teste substitui apenas `_conn()` via `monkeypatch`,
  seguindo exatamente o padrão de `tests/test_describe_scope_backends.py`.

### 5. Histórias de usuário

#### US-001 — Provar a tradução do backend real do Qdrant sem rede (P1)

Como pessoa que opera o pipeline ou troca de provider de banco vetorial,
quero que `ensure`, `write`, `search`, `scope_ids` e `remove` do
`_QdrantBackend` real sejam exercitados contra um cliente-dublê, para que
erro de tradução com o SDK apareça no teste em vez de numa sincronização em
produção.

**Por que P1**: dívida declarada bloqueante pelo BACKLOG-0011 — precisa ser
resolvida antes de incorporar o pipeline a um backend assíncrono, para não
mover erro de tradução de SDK para dentro de execuções de produção.
**Teste independente**: `uv run pytest tests/test_qdrant_backend_operations.py`
passa isoladamente, sem rede e sem depender de outra suíte.
**Requisitos**: FR-001, FR-002, FR-003, FR-004, FR-005

### 6. Cenários BDD de aceite

#### AC-001 — `ensure` cria a coleção quando ausente

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-001
Feature: Tradução de ensure para o SDK do Qdrant

  Scenario: Coleção ausente é criada com os parâmetros corretos
    Given um cliente-dublê cujo get_collections não lista a coleção configurada
    When _QdrantBackend.ensure é chamado com dimensions=8
    Then create_collection é chamado com vectors_config de tamanho 8 e distância COSINE
```

#### AC-002 — `ensure` é idempotente

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-002
Feature: Tradução de ensure para o SDK do Qdrant

  Scenario: Coleção existente não é recriada
    Given um cliente-dublê cujo get_collections já lista a coleção configurada
    When _QdrantBackend.ensure é chamado
    Then create_collection não é chamado
```

#### AC-003 — `ensure` propaga falha do SDK sem mascarar

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-003
Feature: Tradução de ensure para o SDK do Qdrant

  Scenario: Falha ao listar coleções não é convertida
    Given um cliente-dublê cujo get_collections levanta uma exceção do SDK
    When _QdrantBackend.ensure é chamado
    Then a exceção original se propaga sem tradução, ao contrário de describe
```

#### AC-004 — `write` traduz registros para PointStruct

**Cobre**: US-001, FR-002, NFR-001

```gherkin
@US-001 @FR-002 @NFR-001 @AC-004
Feature: Tradução de write para o SDK do Qdrant

  Scenario: Registros viram PointStruct com id, vetor e payload corretos
    Given uma lista de VectorRecord com conteúdo e metadados
    When _QdrantBackend.write é chamado
    Then upsert recebe PointStruct com id, vector e payload (page_content e metadata) equivalentes, com wait=True
```

#### AC-005 — `write` é no-op em lista vazia

**Cobre**: US-001, FR-002, NFR-001

```gherkin
@US-001 @FR-002 @NFR-001 @AC-005
Feature: Tradução de write para o SDK do Qdrant

  Scenario: Lista vazia não aciona o SDK
    Given uma lista vazia de VectorRecord
    When _QdrantBackend.write é chamado
    Then upsert não é chamado
```

#### AC-006 — `write` preserva ordem e contagem exatos

**Cobre**: US-001, FR-002, NFR-001

```gherkin
@US-001 @FR-002 @NFR-001 @AC-006
Feature: Tradução de write para o SDK do Qdrant

  Scenario: Múltiplos registros mantêm ordem e contagem no envio
    Given uma lista com múltiplos VectorRecord em uma ordem específica
    When _QdrantBackend.write é chamado
    Then o PointStruct enviado ao SDK tem a mesma contagem e a mesma ordem dos registros recebidos
```

#### AC-007 — `search` traduz o filtro com tenant e a resposta

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-007
Feature: Tradução de search para o SDK do Qdrant

  Scenario: Filtro de escopo com tenant e resposta traduzida
    Given um escopo lógico com project_id e tenant_id e um cliente-dublê que devolve hits com payload
    When _QdrantBackend.search é chamado com um embedding e k
    Then o filtro enviado ao SDK contém as condições de project_id e tenant_id
    And cada hit devolvido é traduzido para SearchResult com content, metadata e score
```

#### AC-008 — `search` sem tenant filtra somente por project_id

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-008
Feature: Tradução de search para o SDK do Qdrant

  Scenario: Escopo sem tenant_id envia filtro só com project_id
    Given um escopo lógico com tenant_id igual a None
    When _QdrantBackend.search é chamado
    Then o filtro enviado ao SDK contém somente a condição de project_id
```

#### AC-009 — `search` sem resultados devolve lista vazia

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-009
Feature: Tradução de search para o SDK do Qdrant

  Scenario: SDK sem hits não causa erro
    Given um cliente-dublê cujo search devolve uma lista vazia de hits
    When _QdrantBackend.search é chamado
    Then o resultado traduzido é uma lista vazia de SearchResult
```

#### AC-010 — `scope_ids` agrega todas as páginas

**Cobre**: US-001, FR-004, NFR-001

```gherkin
@US-001 @FR-004 @NFR-001 @AC-010
Feature: Paginação de scope_ids no Qdrant

  Scenario: Múltiplas páginas são agregadas até o fim
    Given um cliente-dublê cujo scroll devolve páginas sucessivas com offset não nulo até a última
    When _QdrantBackend.scope_ids é chamado
    Then o conjunto retornado contém os ids de todas as páginas
```

#### AC-011 — `scope_ids` com uma única página

**Cobre**: US-001, FR-004, NFR-001

```gherkin
@US-001 @FR-004 @NFR-001 @AC-011
Feature: Paginação de scope_ids no Qdrant

  Scenario: Primeira página já devolve offset nulo
    Given um cliente-dublê cujo scroll devolve offset None já na primeira chamada
    When _QdrantBackend.scope_ids é chamado
    Then o conjunto retornado contém exatamente os ids dessa única página, com uma só chamada a scroll
```

#### AC-012 — `scope_ids` traduz falha do SDK em erro de domínio

**Cobre**: US-001, FR-004, NFR-001

```gherkin
@US-001 @FR-004 @NFR-001 @AC-012
Feature: Paginação de scope_ids no Qdrant

  Scenario: Falha do SDK durante a paginação bloqueia a sincronização
    Given um cliente-dublê cujo scroll levanta uma exceção do SDK
    When _QdrantBackend.scope_ids é chamado
    Then UnreliableScopeReadError é levantada, encadeada a partir da exceção original
```

#### AC-013 — `remove` traduz ids para PointIdsList

**Cobre**: US-001, FR-005, NFR-001

```gherkin
@US-001 @FR-005 @NFR-001 @AC-013
Feature: Tradução de remove para o SDK do Qdrant

  Scenario: Ids viram PointIdsList
    Given uma lista de ids a remover
    When _QdrantBackend.remove é chamado
    Then delete é chamado com PointIdsList contendo os ids e wait=True
```

#### AC-014 — `remove` é no-op em lista vazia

**Cobre**: US-001, FR-005, NFR-001

```gherkin
@US-001 @FR-005 @NFR-001 @AC-014
Feature: Tradução de remove para o SDK do Qdrant

  Scenario: Lista vazia não aciona o SDK
    Given uma lista vazia de ids
    When _QdrantBackend.remove é chamado
    Then delete não é chamado
```

#### AC-015 — `remove` aceita um iterable não-list

**Cobre**: US-001, FR-005, NFR-001

```gherkin
@US-001 @FR-005 @NFR-001 @AC-015
Feature: Tradução de remove para o SDK do Qdrant

  Scenario: Generator de ids é totalmente consumido e traduzido
    Given um generator (não uma lista) produzindo múltiplos ids
    When _QdrantBackend.remove é chamado
    Then delete recebe PointIdsList com todos os ids do generator
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve provar, com cliente-dublê e sem rede, que
  `_QdrantBackend.ensure` cria a coleção com os parâmetros corretos quando
  ausente e não a recria quando já existe.
- **FR-002**: O sistema deve provar, com cliente-dublê e sem rede, que
  `_QdrantBackend.write` traduz `VectorRecord` para `PointStruct` com
  `id`/`vector`/`payload` corretos e `wait=True`, e não chama o SDK quando a
  lista de registros está vazia.
- **FR-003**: O sistema deve provar, com cliente-dublê e sem rede, que
  `_QdrantBackend.search` envia o filtro de escopo (`project_id` e, quando
  presente, `tenant_id`) ao SDK e traduz cada hit devolvido para
  `SearchResult`.
- **FR-004**: O sistema deve provar, com cliente-dublê e sem rede, que
  `_QdrantBackend.scope_ids` agrega os ids de todas as páginas de `scroll`
  até `offset` ser `None`, e que uma falha do SDK durante a paginação
  levanta `UnreliableScopeReadError` encadeada a partir da exceção original.
- **FR-005**: O sistema deve provar, com cliente-dublê e sem rede, que
  `_QdrantBackend.remove` traduz uma lista de ids para `PointIdsList` com
  `wait=True`, e não chama o SDK quando a lista de ids está vazia.

#### Não funcionais

- **NFR-001**: Os testes desta fatia não podem depender de rede nem de uma
  instância real do Qdrant. **Verificação**: inspeção dos casos em
  `tests/test_qdrant_backend_operations.py` — cada um substitui `_conn()`
  por um dublê local e nenhum importa `QdrantClient` real; execução de
  `uv run pytest tests/test_qdrant_backend_operations.py` em CI, sem serviço
  externo configurado.

#### Erros e casos-limite

- Falha do SDK (`get_collections`) em `ensure` → propaga sem tradução, ao
  contrário de `describe` (AC-003).
- `write` chamado com lista vazia de registros → `upsert` não é chamado
  (AC-005).
- `search` sem hits do SDK → devolve lista vazia sem erro (AC-009).
- `scope_ids` com uma única página → agrega corretamente sem chamada extra
  (AC-011).
- Falha do SDK (`scroll`) durante a paginação de `scope_ids` → levanta
  `UnreliableScopeReadError` encadeada, sincronização bloqueada (AC-012).
- `remove` chamado com lista vazia de ids → `delete` não é chamado (AC-014).
- `remove` chamado com um iterable não-list (generator) → todos os ids são
  consumidos e traduzidos (AC-015).
- `ensure` chamado quando a coleção já existe → `create_collection` não é
  chamado (AC-002).

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Stack Python 3.12 + uv + Pytest 8.3, sem framework web (`.specsfy/STACK.md`).
- `_QdrantBackend` já implementado em
  `src/pipeline/providers/vectorstores/qdrant.py`; nenhuma mudança de
  produção prevista nesta fatia.
- Padrão de teste já aprovado pela SPEC-0004 em
  `tests/test_describe_scope_backends.py`: função auxiliar `_qdrant(monkeypatch, cliente)`
  constrói o backend real e substitui `_conn()` pelo dublê.

#### Arquitetura e módulos

- Novo arquivo de teste `tests/test_qdrant_backend_operations.py`, seguindo
  a mesma auxiliar `_qdrant(monkeypatch, cliente)` (ou importação da já
  existente em `tests/test_describe_scope_backends.py`, se a duplicação for
  evitável sem acoplar os dois arquivos).
- Cada cenário cria uma classe-dublê mínima local ao teste, expondo somente
  os métodos do SDK exercitados por aquela operação, e registra as chamadas
  recebidas em uma lista (`self.chamadas` ou equivalente) para permitir a
  asserção dos argumentos enviados.

#### Migrations

- Não aplicável.

#### Models

- Não aplicável — usa os contratos já definidos (`VectorRecord`,
  `LogicalScope`, `SearchResult`) em `src/pipeline/providers/contracts.py`.

#### Controllers e casos de uso

- Não aplicável — não há camada de controller neste componente.

#### Views e experiência

- Não aplicável — sem interface para pessoas.

#### Queries e repositórios

- Não aplicável — `scope_ids` e `search` já existem como métodos do backend
  sob teste; esta fatia não cria nova consulta.

#### Jobs e processamento assíncrono

- Não aplicável.

#### Estrutura de arquivos

```text
specs/completed/0011-cobrir-comportamento-backend-real-qdrant/
  spec.md
  research/
tests/
  test_qdrant_backend_operations.py
```

### 9. Modelo de dados

#### Entidades

- Não aplicável — nenhuma entidade nova; a fatia caracteriza comportamento
  sobre os contratos já definidos (`VectorRecord`, `LogicalScope`,
  `SearchResult`) em `src/pipeline/providers/contracts.py`.

#### Estados e transições

- Não aplicável.

#### Migração e retenção

- Não aplicável.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. Este componente é uma biblioteca de
  sincronização vetorial operada por CLI já existente (`pipeline.py`,
  `search.py`, `chat.py`). Esta fatia acrescenta somente testes internos ao
  `_QdrantBackend`; não cria, altera nem expõe tela, comando novo ou saída
  visível a uma pessoa usuária.

#### Stack e convenções de interface

- Não aplicável.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável.

#### Menus e navegação principal

- Não aplicável.

#### Formulários e ações

- Não aplicável.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável.

#### Estados e acessibilidade

- Não aplicável.

#### Contrato CRUD

- Não aplicável.

#### Revisão visual durante o desenvolvimento

- Não aplicável — nenhuma superfície visual é criada ou alterada por esta
  fatia; cada tarefa registrará `Não aplicável` com este motivo no item
  `VISUAL`.

#### APIs expostas

- Não aplicável — nenhuma API nova.

#### APIs externas utilizadas

- **SDK `qdrant-client` 1.10.1**: já em uso por `_QdrantBackend`; esta fatia
  não chama o SDK real, apenas prova a tradução contra um dublê local dos
  métodos `get_collections`, `create_collection`, `scroll`, `upsert`,
  `delete` e `search`. Autenticação, timeout, retry e fallback contra o
  serviço real não são material aqui — nenhum teste desta fatia toca rede
  ou credencial; a exceção de rede/indisponibilidade coberta é somente a
  já presente no código de produção (`scroll` falhando dentro de
  `scope_ids`, AC-012), reproduzida pelo dublê sem I/O real.

#### Documentação das APIs consultadas

- Nenhuma consulta externa; a assinatura usada já está fixada no código de
  produção existente.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: cada operação do `_QdrantBackend` real (`ensure`, `write`,
  `search`, `scope_ids`, `remove`) contra um cliente-dublê local, sem rede.
- **Integração/contrato**: nenhuma fronteira nova; a conformidade do
  contrato neutro já está coberta por `tests/test_vectorstore_conformance.py`
  e `tests/test_qdrant_sync.py`.
- **BDD/aceite**: os sete cenários Gherkin da seção 6 orientam os casos TDD.
- **Runner TDD**: Pytest 8.3+ (`uv run pytest`), conforme
  `.specsfy/RULES.md` e `pyproject.toml` — projeto Python sem Laravel.
- **E2E**: Não aplicável — sem rede, sem Qdrant real.
- **Verificação manual**: nenhuma prevista; toda prova é automatizada.

Esta fatia caracteriza comportamento já implementado em produção — não há
código novo a escrever para os cenários passarem. Cada caso segue o padrão
de T033 da SPEC-0004 (`tests/test_describe_scope_backends.py`): a ausência de
prova é o problema, não a ausência de comportamento. O "RED" observado é a
inexistência do teste (a suíte falha ao ser coletada por arquivo/`nodeid`
ausente); o "GREEN" é o teste passando contra o código real, comprovando que
a implementação já traduz corretamente. Para as guardas e laços mais sujeitos
a teste vazio (idempotência de `ensure`, no-op de `write`/`remove`, paginação
e tradução de erro de `scope_ids`, filtro de `tenant_id` em `search`), a
sensibilidade foi comprovada por sonda: o comportamento de produção foi
temporariamente mutado (guarda removida, condição de tenant apagada, tradução
de erro suprimida), o caso correspondente falhou como esperado, e o código
foi restaurado (`git checkout --`) antes do GREEN final.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, NFR-001, AC-001 | AC-001 na seção 6 | `test_ensure_cria_colecao_quando_ausente` com marcador `SPECSFY: FR-001 NFR-001 AC-001` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: `uv run pytest tests/test_qdrant_backend_operations.py::test_ensure_cria_colecao_quando_ausente` → passed; sensibilidade garantida pela asserção exata de `vectors_config.size`/`distance` e da ordem de chamadas | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-001, NFR-001, AC-002 | AC-002 na seção 6 | `test_ensure_nao_recria_colecao_existente` com marcador `SPECSFY: FR-001 NFR-001 AC-002` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sonda — guarda de idempotência removida (`if True`) fez o caso falhar (`create_collection` chamado indevidamente), restaurada em seguida | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-001, NFR-001, AC-003 | AC-003 na seção 6 | `test_ensure_propaga_falha_do_sdk` com marcador `SPECSFY: FR-001 NFR-001 AC-003` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sensibilidade garantida por `pytest.raises(RuntimeError, match=...)` — só passa se a exceção não for mascarada | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-002, NFR-001, AC-004 | AC-004 na seção 6 | `test_write_traduz_pointstruct` com marcador `SPECSFY: FR-002 NFR-001 AC-004` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sensibilidade garantida pela asserção exata de `id`/`vector`/`payload`/`wait` no `PointStruct` real enviado | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-002, NFR-001, AC-005 | AC-005 na seção 6 | `test_write_lista_vazia_e_no_op` com marcador `SPECSFY: FR-002 NFR-001 AC-005` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sonda — guarda `if not records: return` removida fez `upsert` ser chamado indevidamente, restaurada em seguida | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-002, NFR-001, AC-006 | AC-006 na seção 6 | `test_write_preserva_ordem_e_contagem` com marcador `SPECSFY: FR-002 NFR-001 AC-006` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sensibilidade garantida pela asserção de contagem e ordem exatas dos ids no `PointStruct` | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-003, NFR-001, AC-007 | AC-007 na seção 6 | `test_search_traduz_filtro_com_tenant_e_resposta` com marcador `SPECSFY: FR-003 NFR-001 AC-007` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sonda — condição de `tenant_id` removida de `_scope_filter` fez o caso falhar, restaurada em seguida | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-003, NFR-001, AC-008 | AC-008 na seção 6 | `test_search_sem_tenant_filtra_so_project_id` com marcador `SPECSFY: FR-003 NFR-001 AC-008` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sensibilidade garantida pela asserção exata das chaves do filtro (`{"metadata.project_id"}`) | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-003, NFR-001, AC-009 | AC-009 na seção 6 | `test_search_sem_hits_devolve_lista_vazia` com marcador `SPECSFY: FR-003 NFR-001 AC-009` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sensibilidade garantida pela asserção `resultados == []` | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-004, NFR-001, AC-010 | AC-010 na seção 6 | `test_scope_ids_agrega_paginas` com marcador `SPECSFY: FR-004 NFR-001 AC-010` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sonda — retorno antecipado na primeira página fez o caso falhar (perdeu o id da segunda página), restaurada em seguida | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-004, NFR-001, AC-011 | AC-011 na seção 6 | `test_scope_ids_pagina_unica` com marcador `SPECSFY: FR-004 NFR-001 AC-011` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sensibilidade garantida pela asserção de uma única chamada a `scroll` | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-004, NFR-001, AC-012 | AC-012 na seção 6 | `test_scope_ids_traduz_falha_do_sdk` com marcador `SPECSFY: FR-004 NFR-001 AC-012` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sonda — encadeamento para `UnreliableScopeReadError` removido fez o caso falhar com `RuntimeError` cru, restaurada em seguida | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-005, NFR-001, AC-013 | AC-013 na seção 6 | `test_remove_traduz_pointidslist` com marcador `SPECSFY: FR-005 NFR-001 AC-013` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sensibilidade garantida pela asserção exata de `points`/`wait` no `PointIdsList` real enviado | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-005, NFR-001, AC-014 | AC-014 na seção 6 | `test_remove_lista_vazia_e_no_op` com marcador `SPECSFY: FR-005 NFR-001 AC-014` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sonda — guarda `if not identifiers: return` removida fez `delete` ser chamado indevidamente, restaurada em seguida | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| US-001, FR-005, NFR-001, AC-015 | AC-015 na seção 6 | `test_remove_aceita_generator` com marcador `SPECSFY: FR-005 NFR-001 AC-015` em tests/test_qdrant_backend_operations.py | Caracterização de código existente: teste ausente até 2026-09-04 | GREEN em 2026-09-04: passed; sensibilidade garantida pela asserção dos ids do generator no `PointIdsList` traduzido | Regressão em 2026-09-04: `uv run pytest` → 263 passed |
| FR-002, NFR-001, AC-006 (regressão 2026-09-07) | AC-006 na seção 6 (estendido) | `test_write_loteia_upsert_acima_do_limite` com marcador `SPECSFY: FR-002 NFR-001 AC-006` em tests/test_qdrant_backend_operations.py | RED 2026-09-07 revertendo a correção: `AttributeError`/lote único — `write` mandava todos os pontos num `upsert` só | GREEN 2026-09-07: `_UPSERT_BATCH = 64`; `130` registros → lotes `[64, 64, 3]`, ordem e contagem globais preservadas | Regressão 2026-09-07: `uv run pytest` → 300 passed |
| FR-002, NFR-001 (regressão 2026-09-07) | NFR-001 na seção 7 (verificação declarada) | `test_build_client_define_timeout_explicito` com marcador `SPECSFY: FR-002 NFR-001` em tests/test_qdrant_backend_operations.py | RED 2026-09-07 revertendo a correção: `KeyError: 'timeout'` — `QdrantClient` criado sem `timeout` explícito | GREEN 2026-09-07: `_CLIENT_TIMEOUT = 60` passado ao `QdrantClient` | Regressão 2026-09-07: `uv run pytest` → 300 passed |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k ensure_cria` | Passed |
| FR-001 | AC-002 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k ensure_nao_recria` | Passed |
| FR-001 | AC-003 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k ensure_propaga_falha` | Passed |
| FR-002 | AC-004 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k write_traduz` | Passed |
| FR-002 | AC-005 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k write_lista_vazia` | Passed |
| FR-002 | AC-006 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k write_preserva_ordem` | Passed |
| FR-003 | AC-007 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k search_traduz_filtro_com_tenant` | Passed |
| FR-003 | AC-008 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k search_sem_tenant` | Passed |
| FR-003 | AC-009 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k search_sem_hits` | Passed |
| FR-004 | AC-010 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k agrega_paginas` | Passed |
| FR-004 | AC-011 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k pagina_unica` | Passed |
| FR-004 | AC-012 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k falha_do_sdk` | Passed |
| FR-005 | AC-013 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k remove_traduz` | Passed |
| FR-005 | AC-014 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k remove_lista_vazia` | Passed |
| FR-005 | AC-015 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k remove_aceita_generator` | Passed |
| NFR-001 | AC-001–AC-015 | Inspeção + CI | `uv run pytest tests/test_qdrant_backend_operations.py` sem serviço externo configurado | Passed — 15 passed, sem import de `QdrantClient` real |
| FR-002 (regressão 2026-09-07) | AC-006 estendido + NFR-001 | Unidade | `uv run pytest tests/test_qdrant_backend_operations.py -k "loteia_upsert or define_timeout"` | Passed — 2 passed; lote de `upsert` em blocos de `_UPSERT_BATCH` e `timeout` explícito no cliente (correção interna de confiabilidade, ver seção 13) |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed em 2026-09-04 — `READY`.
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0011-cobrir-comportamento-backend-real-qdrant/spec.md --allow-draft` → `VALID DRAFT`; `node .agents/skills/specsfy-04-validate/scripts/review_findings.mjs specs/draft/0011-cobrir-comportamento-backend-real-qdrant/spec.md` → `Reviews: PASSED` (nenhum finding registrado).
- **Achados**: Nenhum `BLOCKER`. Cobertura mínima confirmada: US-001 com 15 AC, cada FR (FR-001 a FR-005) com exatamente 3 AC distintos declarados em `**Cobre**`, NFR-001 coberto pelos 15 AC. Revisão semântica (`references/quality-gates.md`): problema/ator/resultado explícitos; escopo e fora de escopo sem contradição; research declara ausência de fonte externa de forma consistente com o código já implementado; requisitos são obrigações verificáveis, não soluções vagas; erros e limites materiais cobertos (falha do SDK em `ensure` e `scope_ids`, listas vazias em `write`/`remove`, página única, ausência de hits); plano técnico nomeia o único arquivo de teste a criar; `Interface para pessoas: Não` justificada (CLI existente, sem tela nova). Nenhuma mudança de stack ou persistência — dispensa revisão de `.specsfy/STACK.md`/`.specsfy/DATABASE.md`.

#### Gate do Ato II — Plano

- **Resultado**: Passed em 2026-09-04.
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0011-cobrir-comportamento-backend-real-qdrant/spec.md --allow-draft` → `VALID DRAFT` (total=16, complete=15, checklist_items=96, checklist_complete=90, covered_spec_ids=22/22); repetido sem `--allow-draft` após `Plan Gate: Passed` → `READY`.
- **Achados**: 16 tarefas (15 `[TEST][TDD]`, uma por AC, T001–T015; 1 `[TEST]` de fechamento, T016) e 96 itens de checklist; 22/22 IDs cobertos. Nenhuma tarefa `[CODE]` nesta fatia — é caracterização pura, sem predecessor TDD pendente para código de produção. T001–T015 concluídas com GREEN registrado na seção 11, incluindo sensibilidade comprovada por sonda de mutação nos seis pontos de maior risco (idempotência de `ensure`, no-op de `write`/`remove`, paginação e erro de `scope_ids`, filtro de `tenant_id`). T016 (regressão e rastreabilidade finais) permanece aberta para o Ato III.

#### Gate do Ato III — Entrega

- **Resultado**: Passed em 2026-09-04.
- **Comando**: `uv run pytest` → 263 passed; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0011-cobrir-comportamento-backend-real-qdrant/spec.md .` → 22/22 IDs cobertos, `RESULTADO: GAPS`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/review/0011-cobrir-comportamento-backend-real-qdrant/spec.md .` → `QA: PASSED`; `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0011-cobrir-comportamento-backend-real-qdrant/spec.md` → `READY`; `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`; `node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check` → exit 0; `uv run ruff check` → limpo.
- **Achados**: Regressão completa verde: 263 casos, 263 aprovados, nenhum pulado e nenhum `xfail` no repositório inteiro (248 pré-existentes + 15 desta fatia). Cobertura 22/22 IDs desta fatia (US-001, FR-001–005, NFR-001, AC-001–015), todos com GREEN registrado na seção 11 e sensibilidade comprovada por sonda nos seis pontos de maior risco.
- **Achado sobre `RESULTADO: GAPS`**: o auditor reporta vinte marcadores órfãos. Os identificadores completos ficam fora deste texto de propósito: o validador estrito lê qualquer ocorrência da forma `TIPO-NNN` no corpo da spec como declaração desta fatia, e citá-los aqui os transformaria em requisitos fantasmas sem cenário (mesma armadilha evitada no Gate do Ato III da SPEC-0004). Nenhum pertence a esta fatia, que declara uma história, cinco requisitos funcionais, um não funcional e quinze critérios de aceite, todos numerados a partir de 001. Cada órfão foi localizado em arquivos de outras specs que compartilham a pasta `tests/` (confirmado por `grep` em `tests/test_application_boundaries.py`, `tests/test_characterization_providers.py`, `tests/test_chunker.py` e outros). O `GAPS` é consequência de o auditor varrer toda a pasta `tests/` enquanto cada spec numera seus IDs a partir de 001 — mesma dívida de framework documentada em `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md`; não afeta `tests/test_qdrant_backend_operations.py`, que cobre exatamente os 22 IDs desta fatia sem órfão próprio.
- **Evidence Contract**: nenhuma tarefa `[CODE]` nesta fatia — é caracterização pura de comportamento já implementado, sem mudança de produção. Por isso não há comentário `specsfy:evidence` por tarefa, mesmo com `Evidence Contract: 1` declarado no cabeçalho (mesmo padrão de T033 na SPEC-0004, também `[TEST]` sem código de produção associado).
- **Achados posteriores (2026-09-07) — correção interna de confiabilidade, gates preservados**: Um teste de ponta a ponta real (pipeline → OpenAI → Qdrant, base de ~208 chunks) revelou dois defeitos de confiabilidade em `src/pipeline/providers/vectorstores/qdrant.py`, ambos **fora do contrato neutro caracterizado por esta fatia** (tradução `PointStruct`/filtros/erros continua idêntica; contagens do espelho idempotente inalteradas): (1) `_build_client` criava `QdrantClient` sem `timeout`, herdando o padrão de ~5 s do SDK REST — curto demais para endpoint publicado por proxy, causando `httpx.WriteTimeout`; (2) `_QdrantBackend.write` enviava todos os pontos num único `upsert`, agravando (1) em bases grandes. Classificação (`$specsfy-update-spec`, matriz de mudança): correção interna reversível sem efeito observável no contrato — **não reabre atos**; `Definition/Plan/Delivery Gate` permanecem `Passed`, `Status: Complete`. Correção: `_CLIENT_TIMEOUT = 60` no cliente e `_UPSERT_BATCH = 64` loteando o `upsert`, preservando ordem e contagem globais. Regressão adicionada a `tests/test_qdrant_backend_operations.py`: `test_write_loteia_upsert_acima_do_limite` (estende AC-006) e `test_build_client_define_timeout_explicito` (NFR-001) — RED observado revertendo a correção (`KeyError: 'timeout'` / lote único), GREEN após. `uv run pytest -q` → 300 passed; `uv run ruff check .` → limpo. `PROJECT.md` sem impacto material (a narrativa já descreve a sincronização com Qdrant; a correção é de resiliência do transporte); `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT`. Ver seção 11 (linhas "regressão 2026-09-07") e seção 16.

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

#### Fase 1 — Caracterização informada pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 o caso `test_ensure_cria_colecao_quando_ausente` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-001, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-001 e o padrão de `tests/test_describe_scope_backends.py`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-001 NFR-001 AC-001`, dublê mínimo expondo `get_collections` e `create_collection`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real (caracterização de código existente).
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre o dublê de `ensure`.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 o caso `test_ensure_nao_recria_colecao_existente` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-001, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-002 e o padrão de `tests/test_describe_scope_backends.py`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-001 NFR-001 AC-002`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre a idempotência de `ensure`.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 o caso `test_ensure_propaga_falha_do_sdk` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-001, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-003 e confirmar que `ensure` não tem `try/except` ao redor de `get_collections`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-001 NFR-001 AC-003`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre o contraste com `describe`.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 o caso `test_write_traduz_pointstruct` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-002, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-004 e o formato de `PointStruct` produzido por `write`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-002 NFR-001 AC-004`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre a tradução de payload.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 o caso `test_write_lista_vazia_e_no_op` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-002, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-005 e a guarda `if not records: return` em `write`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-002 NFR-001 AC-005`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre o no-op de `write`.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-006 o caso `test_write_preserva_ordem_e_contagem` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-002, NFR-001, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-006 e a compreensão de lista que monta os `PointStruct` em `write`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-002 NFR-001 AC-006`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre a correspondência 1:1 de `write`.

- [x] T007 [TEST] [TDD] [US-001] Derivar do AC-007 o caso `test_search_traduz_filtro_com_tenant_e_resposta` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-003, NFR-001, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-007 e a construção do filtro de escopo em `_scope_filter`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-003 NFR-001 AC-007`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre a tradução do filtro com tenant.

- [x] T008 [TEST] [TDD] [US-001] Derivar do AC-008 o caso `test_search_sem_tenant_filtra_so_project_id` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-003, NFR-001, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-008 e o ramo condicional de `tenant_id` em `_scope_filter`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-003 NFR-001 AC-008`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre o filtro sem tenant.

- [x] T009 [TEST] [TDD] [US-001] Derivar do AC-009 o caso `test_search_sem_hits_devolve_lista_vazia` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-003, NFR-001, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-009 e o laço de tradução de hits em `search`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-003 NFR-001 AC-009`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre o caminho sem resultado.

- [x] T010 [TEST] [TDD] [US-001] Derivar do AC-010 o caso `test_scope_ids_agrega_paginas` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-004, NFR-001, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-010 e o laço de paginação de `scope_ids`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-004 NFR-001 AC-010`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre a paginação completa.

- [x] T011 [TEST] [TDD] [US-001] Derivar do AC-011 o caso `test_scope_ids_pagina_unica` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-004, NFR-001, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-011 e a condição `if offset is None: return found` em `scope_ids`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-004 NFR-001 AC-011`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre o caso de página única.

- [x] T012 [TEST] [TDD] [US-001] Derivar do AC-012 o caso `test_scope_ids_traduz_falha_do_sdk` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-004, NFR-001, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-012 e o `try/except` que encadeia `UnreliableScopeReadError` em `scope_ids`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-004 NFR-001 AC-012`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre o caminho de erro.

- [x] T013 [TEST] [TDD] [US-001] Derivar do AC-013 o caso `test_remove_traduz_pointidslist` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-005, NFR-001, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-013 e o formato de `PointIdsList` produzido por `remove`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-005 NFR-001 AC-013`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre a tradução de remoção.

- [x] T014 [TEST] [TDD] [US-001] Derivar do AC-014 o caso `test_remove_lista_vazia_e_no_op` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-005, NFR-001, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-014 e a guarda `if not identifiers: return` em `remove`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-005 NFR-001 AC-014`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre o no-op de `remove`.

- [x] T015 [TEST] [TDD] [US-001] Derivar do AC-015 o caso `test_remove_aceita_generator` em tests/test_qdrant_backend_operations.py — Refs: US-001, FR-005, NFR-001, AC-015 — Depends: none
  - [x] **PREP**: Ler o Gherkin de AC-015 e a conversão `identifiers = list(ids)` em `remove`.
  - [x] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: FR-005 NFR-001 AC-015`.
  - [x] **VERIFY**: Observar o caso passando contra o `_QdrantBackend` real.
  - [x] **VISUAL**: Não aplicável — tarefa só cria teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e resultado na seção 11.
  - [x] **IMPROVE**: Registrar aprendizado sobre a aceitação de iterables.

#### Fase final — Qualidade

- [x] T016 [TEST] Executar regressão e rastreabilidade completas em tests/test_qdrant_backend_operations.py e specs/in-progress/0011-cobrir-comportamento-backend-real-qdrant/spec.md — Refs: US-001, FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015 — Depends: T001, T002, T003, T004, T005, T006, T007, T008, T009, T010, T011, T012, T013, T014, T015
  - [x] **PREP**: Confirmado que T001–T015 estão com GREEN registrado na seção 11, incluindo sensibilidade comprovada por sonda nos seis pontos de maior risco.
  - [x] **EXECUTE**: Executado `uv run pytest` completo e `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0011-cobrir-comportamento-backend-real-qdrant/spec.md .`.
  - [x] **VERIFY**: `uv run pytest` → 263 passed, sem teste pulado ou `xfail`. `check_traceability.mjs` → 22/22 IDs desta fatia cobertos em `tests/test_qdrant_backend_operations.py`; `RESULTADO: GAPS` reportado, mas os únicos marcadores órfãos pertencem a outras specs que compartilham a pasta `tests/` com numeração própria a partir de 001 — dívida de framework já registrada em `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md` e não a esta entrega (mesmo padrão documentado no Gate do Ato III da SPEC-0004; identificadores completos omitidos aqui de propósito, ver achado na seção 13). Nenhum órfão referencia `tests/test_qdrant_backend_operations.py`.
  - [x] **VISUAL**: Não aplicável — nenhuma superfície visual nesta fatia.
  - [x] **EVIDENCE**: Contagens e comandos registrados no Gate do Ato III (seção 13).
  - [x] **IMPROVE**: Nenhuma melhoria de processo necessária — o padrão de caracterização com sonda de mutação (herdado da SPEC-0004) se mostrou suficiente para provar sensibilidade sem exigir mudança de produção.

### 15. Ordem de execução

- Caminho crítico: T001–T015 (todas paralelizáveis entre si, cada uma cria um
  caso de teste independente no mesmo arquivo) → T016.
- Tarefas paralelas: T001 a T015 — cada uma deriva um único AC, sem
  dependência entre si; podem ser feitas em qualquer ordem, respeitando
  apenas que T016 depende de todas.
- Estratégia de MVP: entregar todas as cinco operações e seus 15 cenários
  juntos; a fatia não é divisível em incrementos menores sem deixar uma
  operação do backend real sem prova.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- **BACKLOG-0014 / SPEC-0010** (enxugar providers concretos para Qdrant):
  entregue e `Complete`; o escopo Qdrant-only já é realidade no código.
- Contrato, backend port e adapter Qdrant entregues pela SPEC-0003.
- Padrão de dublê aprovado pela SPEC-0004
  (`tests/test_describe_scope_backends.py`).

#### Riscos

- Dublê desalinhado com uma futura mudança de assinatura do `qdrant-client`
  → mitigado por cobrir só os métodos e argumentos realmente usados pelo
  código de produção, sem reimplementar a API completa do SDK.
- Duplicação de setup entre `test_describe_scope_backends.py` e o novo
  arquivo → mitigado por reaproveitar a mesma auxiliar `_qdrant(monkeypatch, cliente)`
  quando a tarefa T001 avaliar a extração for viável sem acoplar os dois
  arquivos.
- **[Mitigado, 2026-09-07]** Confiabilidade do `write` real sob carga: o
  `upsert` num único request e o `timeout` implícito de ~5 s do SDK REST
  faziam bases grandes falharem com `httpx.WriteTimeout` contra endpoint
  atrás de proxy — não é erro de tradução (o foco desta fatia), mas de
  resiliência. Corrigido com `_UPSERT_BATCH`/`_CLIENT_TIMEOUT` e coberto por
  regressão (seção 11, linhas "regressão 2026-09-07"); classificado como
  correção interna, sem reabrir atos (seção 13).

#### Suposições

- O ambiente de CI já executa `uv run pytest` sem acesso a um Qdrant real
  (confirmado por `.github/workflows/ci.yml` e `.specsfy/STACK.md`); nenhum
  ajuste de pipeline é necessário para esta fatia.

### 17. Decisões

- **DEC-001**: o dublê do SDK imita somente o subconjunto de métodos usados
  por operação — razão: menor superfície de manutenção, alinhado ao padrão
  já aprovado pela SPEC-0004; alternativa descartada: fake genérico e
  reutilizável do `qdrant-client` inteiro, rejeitada por aumentar o custo de
  manutenção sem benefício de cobertura.
- **DEC-002**: cada teste prova tanto o argumento enviado ao SDK quanto a
  tradução da resposta — razão: cobre regressão de payload incorreto (ex.:
  escopo errado no filtro), não só erro de parsing da resposta; trade-off:
  testes um pouco mais verbosos por registrarem as chamadas recebidas pelo
  dublê.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam — 15/15 `AC` verdes em `tests/test_qdrant_backend_operations.py`.
- [x] Todos os requisitos possuem evidência de verificação — FR-001 a FR-005 e NFR-001 registrados na seção 12 como `Passed`.
- [x] Todas as tarefas na seção 14 estão concluídas — T001–T016, 16/16, 96/96 itens de checklist.
- [x] Testes e checks estáticos disponíveis passam — `uv run pytest` → 263 passed; `uv run ruff check` → limpo.
