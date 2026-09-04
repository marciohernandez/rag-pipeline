# Especificação integrada: Enxugar providers concretos para Qdrant, mantendo o contrato multi-provider aberto

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0010 |
| Slug | 0010-enxugar-providers-concretos-qdrant |
| Status | Implementing |
| Effort | 3 |
| Effort updated at | 2026-09-04 |
| Effort rationale | Remoção ampla mas mecânica: apaga dois módulos de adapter, três entradas de registro, três dependências e reduz ~4 arquivos de teste parametrizados; troca dois defaults e um `choices` de CLI. Sem lógica nova. O risco real é (a) deixar referência órfã a Chroma/Pinecone e (b) o teste que prova "mirror rejeitado para provider incapaz" perder seu sujeito quando os dois únicos provedores restantes são mirror-capable. Ambos endereçados por AC estático e por um dublê sintético. Regressão coberta por `uv run pytest` + `ruff`. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | In Progress |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-04 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O projeto carrega três implementações concretas de vector store —
`QdrantVectorStoreAdapter`, `ChromaVectorStoreAdapter` e
`PineconeVectorStoreAdapter` em `src/pipeline/providers/vectorstores/` — mais os
SDKs `chromadb`, `langchain-chroma` e `langchain-pinecone` e as suítes de
conformidade que as exercitam. Apenas o Qdrant está escolhido para uso. Chroma e
Pinecone são superfície não usada: dependências instaladas, código que só roda
em produção, `provider` com default `"chroma"` em `src/pipeline/indexing.py` e
`pipeline.py`, e ramos condicionais espalhados por `factory.py`,
`providers/vectorstores/base.py` e `safety.py`. Essa superfície infla a árvore
de dependências, o tempo de CI e o custo de manutenção, e é a origem do
BACKLOG-0013 (cobrir os backends reais), que ficaria maior por incluir dois
provedores que não serão usados.

#### Resultado desejado

O projeto passa a ser Qdrant-only na prática, sem ChromaDB nem Pinecone no
código, nos testes ou nas dependências, mas com a arquitetura multi-provider
intacta: contrato neutro, backend port, `ProviderFactory` extensível e
`InMemoryVectorStoreAdapter` como oráculo de referência permanecem. Adicionar um
provedor no futuro volta a ser um módulo novo mais um registro, sem redesenho.
Pedir um provedor removido falha com erro claro; a suíte e o `ruff` continuam
verdes; a nova baseline de regressão fica registrada.

#### Métricas de sucesso

- Zero ocorrências de `chromadb`, `langchain-chroma`, `langchain-pinecone`,
  `ChromaVectorStoreAdapter`, `PineconeVectorStoreAdapter`, `_ChromaBackend` e
  `_PineconeBackend` em `src/` (exceto `src/chunk.egg-info/`), `tests/` e
  `pyproject.toml`.
- `uv run pytest` verde e `uv run ruff check .` sem achados após a fatia.
- Nova baseline de regressão da SPEC-0010 declarada em `docs/architecture.md`
  com a justificativa da redução.
- Nenhuma alteração em `providers/contracts.py`, na classe
  `BaseVectorStoreAdapter` ou na assinatura pública de `ProviderFactory` além da
  remoção de entradas de registro.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: Quais arquivos referenciam Chroma ou Pinecone? → Varredura em
  `src/`, `tests/`, `pyproject.toml` e entrypoints da raiz: adapters
  `chroma.py`/`pinecone.py`; registros em `factory._VECTOR_STORES`,
  `base._REAL_PROVIDERS`, `safety.SyncSafetyPolicy._SUPPORTED_PROVIDERS`;
  defaults `provider="chroma"` em `indexing.py` e `pipeline.py`; `choices` em
  `upsert_from_chunks.py`; strings de path `./output/chroma_db` em `pipeline.py`
  e `demo_rag.py`; parametrização e casos dedicados em
  `test_vectorstore_conformance.py`, `test_describe_scope_conformance.py`,
  `test_describe_scope_backends.py`, `test_characterization_providers.py`;
  dependências `chromadb`, `langchain-chroma`, `langchain-pinecone`.
- **R-002**: O teste que prova a rejeição de `mirror` fora do Qdrant depende de
  um provedor real incapaz de mirror? → Sim:
  `test_characterization_providers.py::test_index_chunks_mirror_fora_do_qdrant_bloqueia_antes_de_compor_provider`
  usa `provider="chroma"`, e `test_vectorstore_conformance.py` marca
  `MIRROR_CAPABLE = {"in_memory", "qdrant"}` sobre `BACKENDS` que inclui
  chroma/pinecone. Após a remoção não sobra provedor real sem mirror; a garantia
  precisa ser preservada com um adapter-dublê sintético que declara
  `supports_mirror = False`.
- **R-003**: A baseline de regressão pode diminuir? → Sim, é o caso legítimo:
  `docs/architecture.md` registra baselines históricas (238 na SPEC-0008, 255 na
  SPEC-0009) e `tests/test_ci_gates.py` apenas confere que o número e a palavra
  "baseline" aparecem na documentação; nada trava o valor atual. A SPEC-0010
  registra a nova baseline e a razão da redução.

#### Fontes e contexto consultados

- `src/pipeline/providers/vectorstores/*.py`, `factory.py`, `contracts.py`,
  `errors.py`.
- `src/pipeline/safety.py`, `src/pipeline/indexing.py`, `src/pipeline/loader.py`.
- Entrypoints da raiz: `pipeline.py`, `upsert_from_chunks.py`, `demo_rag.py`.
- `tests/test_vectorstore_conformance.py`, `tests/test_describe_scope_conformance.py`,
  `tests/test_describe_scope_backends.py`, `tests/test_characterization_providers.py`,
  `tests/test_provider_factory.py`, `tests/test_ci_gates.py`,
  `tests/_fakes_vectorstore.py`.
- `pyproject.toml`, `docs/architecture.md`, `docs/packages.md`,
  `docs/integrations.md`, `docs/decisions.md`.
- `specs/backlog/0014-enxugar-providers-concretos-qdrant.md` (brief de origem).

#### Documentação consultada

- Nenhuma documentação externa. A fatia é interna ao repositório.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo. Toda evidência é o código versionado do próprio
  repositório, citado por caminho nas seções acima.

#### Dúvidas respondidas

- **Q**: "Tirar Chroma e Pinecone do projeto" remove também a abstração
  multi-provider? → **A**: Não. Remove só as implementações concretas ainda não
  escolhidas e suas dependências; contrato, port, factory e `in_memory`
  permanecem (decisão do usuário, refinamento de 2026-09-04).
- **Q**: Qual passa a ser o `provider` default? → **A**: `"qdrant"` em
  `indexing.py` e `pipeline.py`; `choices` do CLI reduzido a `["qdrant"]`.
- **Q**: A conformidade continua parametrizada? → **A**: Sim, sobre
  `in_memory` + `qdrant`, provando as cinco operações do port.

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Remover `src/pipeline/providers/vectorstores/chroma.py` e `pinecone.py`.
- Remover as entradas `"chroma"` e `"pinecone"` de `ProviderFactory._VECTOR_STORES`,
  de `_REAL_PROVIDERS` em `providers/vectorstores/base.py` e de
  `SyncSafetyPolicy._SUPPORTED_PROVIDERS` em `safety.py`.
- Remover `chromadb`, `langchain-chroma` e `langchain-pinecone` de
  `pyproject.toml`.
- Trocar o default de `provider` de `"chroma"` para `"qdrant"` em
  `src/pipeline/indexing.py` e `pipeline.py`; reduzir `choices` do argumento
  `--provider` de `upsert_from_chunks.py` para `["qdrant"]`; substituir as
  strings de caminho `./output/chroma_db` por um default neutro
  (`./output/vector_store`) em `pipeline.py` e `demo_rag.py`.
- Reduzir a parametrização das suítes de conformidade
  (`test_vectorstore_conformance.py`, `test_describe_scope_conformance.py`) para
  `("in_memory", "qdrant")` e remover os casos dedicados a Chroma e Pinecone.
- Remover os casos de `describe` de Chroma e Pinecone em
  `test_describe_scope_backends.py`, preservando os do Qdrant.
- Preservar a garantia "modo `mirror` só em provedor capaz" com um
  adapter-dublê sintético sem `MirrorMixin` em substituição ao uso de
  `provider="chroma"`.
- Atualizar `.specsfy/STACK.md` (via `$specsfy-aux-stack`) e regenerar `docs/` e
  `.specsfy/PACKAGES.md` (via `$specsfy-documentator`); registrar a nova
  baseline de regressão em `docs/architecture.md`.

#### Fora de escopo

- Escolher ou adicionar qualquer provedor novo.
- Redesenhar o contrato neutro, o backend port ou a assinatura da
  `ProviderFactory`.
- Qualquer mudança no comportamento do adapter Qdrant (esta fatia não toca em
  `qdrant.py` além de nada — ele permanece intacto).
- Cobertura de comportamento dos backends reais (BACKLOG-0013 / spec futura).
- Limpeza de texto de ajuda, exemplos e comentários que não sejam os defaults e
  `choices` citados.
- Remoção de `langchain-community` ou outros pacotes compartilhados.

#### Atores

- **Mantenedor do pipeline**: reduz dependências e superfície de código; quer a
  suíte verde e nenhuma referência órfã.
- **Integrador de `src/app/`**: consome a `ProviderFactory`; quer o contrato
  multi-provider preservado e extensível.
- **Operador do pipeline**: roda a indexação; quer o caminho padrão funcionando
  com Qdrant sem configuração extra.

### 4. Princípios e restrições do projeto

- **PR-001**: A abstração multi-provider (contrato neutro em `contracts.py`,
  backend port, `ProviderFactory`, `InMemoryVectorStoreAdapter` como oráculo) é
  preservada; nenhuma simplificação da abstração é permitida nesta fatia.
- **PR-002**: Testes não acessam rede nem serviço externo; o Qdrant permanece
  exercitado por dublê de SDK e pela suíte de conformidade existente.
- **PR-003**: Proibido `migrate:fresh`, `DROP`, `TRUNCATE` e equivalentes; não
  se aplica persistência relacional nesta fatia, mas a regra permanece.
- **PR-004**: A baseline de regressão só diminui com autorização explícita
  registrada na spec e justificada em `docs/architecture.md`.
- **PR-005**: Não reutilizar nem renumerar IDs; o adapter Qdrant não é alterado.

### 5. Histórias de usuário

#### US-001 — Remover a superfície não usada de Chroma e Pinecone (P1)

Como mantenedor do pipeline, quero que ChromaDB e Pinecone saiam do código, dos
testes e das dependências, para reduzir a árvore de pacotes, o tempo de CI e o
custo de manutenção sem perder nada em uso.

**Por que P1**: bloqueia o BACKLOG-0013 e reduz o risco de erro de integração em
código nunca exercitado; é pré-requisito da fronteira interna (SPEC-0008).
**Teste independente**: após a fatia, `grep -rE 'chromadb|langchain-chroma|langchain-pinecone|ChromaVectorStoreAdapter|PineconeVectorStoreAdapter'`
em `src/` (exceto `src/chunk.egg-info/`), `tests/` e `pyproject.toml` retorna
vazio, e `uv run pytest` continua verde.
**Requisitos**: FR-001, FR-005, NFR-001, NFR-002

#### US-002 — Preservar o contrato multi-provider aberto (P1)

Como integrador de `src/app/`, quero que o contrato neutro, o backend port e a
`ProviderFactory` continuem extensíveis com `in_memory` e `qdrant` como provas
vivas, para poder adicionar um provedor no futuro sem redesenho.

**Por que P1**: o usuário declarou que vai usar multi-provider e quer o projeto
aberto para isso; a remoção não pode degradar a abstração.
**Teste independente**: a suíte de conformidade roda sobre `("in_memory", "qdrant")`
e prova `ensure`, `list_ids`, `upsert`, `query` e `delete_ids`/`mirror`; pedir
`ProviderFactory.create_vector_store("chroma")` levanta `UnknownProviderError`
com a mensagem listando `in_memory, qdrant`.
**Requisitos**: FR-002, FR-004, NFR-003

#### US-003 — Caminho padrão funcionando com Qdrant (P1)

Como operador do pipeline, quero que o fluxo padrão de indexação use Qdrant sem
eu precisar declarar `provider`, para que nada quebre por o default antigo
apontar para um provedor removido.

**Por que P1**: sem isso, o caminho feliz do pipeline falha imediatamente após a
remoção.
**Teste independente**: `build_vector_store` com `vector_cfg` sem a chave
`provider` devolve um adapter Qdrant; `python upsert_from_chunks.py --help`
lista apenas `qdrant` em `--provider`.
**Requisitos**: FR-003, NFR-001

### 6. Cenários BDD de aceite

#### AC-001 — Registro de vector stores sem Chroma e Pinecone

**Cobre**: US-001, FR-001, FR-002, FR-004, NFR-002

```gherkin
@US-001 @FR-001 @FR-002 @FR-004 @NFR-002 @AC-001
Feature: Registro de providers de vector store enxuto

  Scenario: a factory conhece apenas os providers mantidos
    Given o módulo src.pipeline.providers.factory carregado
    When leio as chaves de ProviderFactory._VECTOR_STORES
    Then o conjunto é exatamente {"qdrant", "in_memory"}
    And não há import de chroma nem de pinecone no módulo
```

#### AC-002 — Pedir "chroma" falha com erro claro

**Cobre**: US-002, FR-001, FR-002, FR-004

```gherkin
@US-002 @FR-001 @FR-002 @FR-004 @AC-002
Feature: Provider removido é rejeitado

  Scenario: create_vector_store("chroma") levanta UnknownProviderError
    Given a ProviderFactory
    When chamo ProviderFactory.create_vector_store("chroma", {})
    Then é levantado UnknownProviderError
    And a mensagem lista as opções "in_memory, qdrant"
```

#### AC-003 — Pedir "pinecone" falha com erro claro

**Cobre**: US-001, FR-001, FR-002, NFR-002

```gherkin
@US-001 @FR-001 @FR-002 @NFR-002 @AC-003
Feature: Provider removido é rejeitado

  Scenario: create_vector_store("pinecone") levanta UnknownProviderError
    Given a ProviderFactory
    When chamo ProviderFactory.create_vector_store("pinecone", {})
    Then é levantado UnknownProviderError
    And a mensagem não menciona "pinecone" como opção válida
```

#### AC-004 — Dependências removidas do manifesto

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-004
Feature: Manifesto sem SDKs de Chroma e Pinecone

  Scenario: pyproject.toml não declara chromadb, langchain-chroma nem langchain-pinecone
    Given o conteúdo de pyproject.toml
    When procuro por "chromadb", "langchain-chroma" e "langchain-pinecone"
    Then nenhuma das três strings aparece na lista de dependencies
    And "qdrant-client" continua declarado
```

#### AC-005 — Varredura estática do repositório limpa

**Cobre**: US-001, FR-001, NFR-002

```gherkin
@US-001 @FR-001 @NFR-002 @AC-005
Feature: Nenhuma referência órfã a Chroma ou Pinecone

  Scenario: src e tests não citam os símbolos removidos
    Given os diretórios src/ (exceto src/chunk.egg-info/) e tests/
    When procuro por "_ChromaBackend", "_PineconeBackend", "ChromaVectorStoreAdapter" e "PineconeVectorStoreAdapter"
    Then não há nenhuma ocorrência
    And os arquivos src/pipeline/providers/vectorstores/chroma.py e pinecone.py não existem
```

#### AC-006 — Caminho padrão de indexação usa Qdrant

**Cobre**: US-003, FR-003, NFR-001

```gherkin
@US-003 @FR-003 @NFR-001 @AC-006
Feature: Default de provider é qdrant

  Scenario: build_vector_store sem provider na config devolve adapter Qdrant
    Given um vector_cfg sem a chave "provider" e com collection_name e url válidos
    When chamo build_vector_store(vector_cfg, persist_dir)
    Then o adapter retornado tem provider == "qdrant"
    And nenhuma exceção de provider desconhecido é levantada
```

#### AC-007 — CLI rejeita provider removido

**Cobre**: US-003, FR-003, FR-002

```gherkin
@US-003 @FR-003 @FR-002 @AC-007
Feature: upsert_from_chunks só aceita qdrant

  Scenario: --provider chroma é recusado pelo argparse
    Given o parser de upsert_from_chunks.py
    When invoco com "--provider chroma"
    Then o parser encerra com erro de escolha inválida
    And o texto de ajuda de --provider lista apenas "qdrant"
```

#### AC-008 — Conformidade prova o contrato sobre in_memory e qdrant

**Cobre**: US-002, FR-004, NFR-001

```gherkin
@US-002 @FR-004 @NFR-001 @AC-008
Feature: Suíte de conformidade parametrizada enxuta

  Scenario: as cinco operações do port passam para in_memory e qdrant
    Given a suíte test_vectorstore_conformance com BACKENDS == ("in_memory", "qdrant")
    When executo uv run pytest tests/test_vectorstore_conformance.py
    Then todos os casos passam
    And nenhum caso é parametrizado com "chroma" ou "pinecone"
```

#### AC-009 — Rejeição de mirror para provedor incapaz continua provada

**Cobre**: US-002, FR-004, NFR-003

```gherkin
@US-002 @FR-004 @NFR-003 @AC-009
Feature: Modo mirror exige garantia de escopo

  Scenario: synchronize com mode="mirror" sobre adapter sem MirrorMixin é bloqueado
    Given um adapter-dublê sintético cujo capabilities().supports_mirror é False
    When chamo synchronize(adapter, escopo, registros, mode="mirror")
    Then é levantado UnsupportedSyncModeError
    And a mensagem orienta usar "append"
```

#### AC-010 — Regressão e ruff verdes após a fatia

**Cobre**: US-001, US-003, FR-005, NFR-001

```gherkin
@US-001 @US-003 @FR-005 @NFR-001 @AC-010
Feature: Suíte estável após a remoção

  Scenario: pytest e ruff passam e a baseline nova está registrada
    Given o repositório após a remoção de Chroma e Pinecone
    When executo "uv run pytest" e "uv run ruff check ."
    Then ambos terminam com exit 0
    And docs/architecture.md declara a baseline de regressão da SPEC-0010 com a razão da redução
```

#### AC-011 — Documentação derivada sem Chroma e Pinecone

**Cobre**: FR-005, NFR-002

```gherkin
@FR-005 @NFR-002 @AC-011
Feature: docs e PACKAGES refletem o projeto Qdrant-only

  Scenario: a documentação regenerada não lista ChromaDB nem Pinecone como destinos
    Given docs/packages.md, docs/integrations.md e docs/architecture.md regenerados
    When procuro por "ChromaDB" e "Pinecone" como destino vetorial ativo
    Then não aparecem como destino suportado
    And o diagrama de arquitetura mostra apenas Qdrant e o backend em memória
```

#### AC-012 — Contrato e factory intactos exceto remoção de entradas

**Cobre**: US-002, FR-004, NFR-003

```gherkin
@US-002 @FR-004 @NFR-003 @AC-012
Feature: Abstração multi-provider preservada

  Scenario: o diff não altera contracts.py nem a superfície pública da factory
    Given o diff da fatia
    When inspeciono src/pipeline/providers/contracts.py e a classe ProviderFactory
    Then contracts.py não muda
    And a única mudança em factory.py é a remoção das entradas "chroma" e "pinecone" de _VECTOR_STORES
```

#### AC-013 — Defaults de provider trocados para qdrant

**Cobre**: US-003, FR-003, NFR-001

```gherkin
@US-003 @FR-003 @NFR-001 @AC-013
Feature: Nenhum default aponta para provider removido

  Scenario: indexing.py e pipeline.py usam "qdrant" como default
    Given src/pipeline/indexing.py e pipeline.py
    When procuro por vector_cfg.get("provider", ...)
    Then o valor default é "qdrant" em toda ocorrência
    And não há string "chroma" nesses dois arquivos
```

#### AC-014 — Baseline de regressão registrada e justificada

**Cobre**: FR-005, NFR-001, NFR-003

```gherkin
@FR-005 @NFR-001 @NFR-003 @AC-014
Feature: Baseline da SPEC-0010 documentada

  Scenario: a nova contagem mínima e a razão da redução estão em docs/architecture.md
    Given a suíte após a remoção de Chroma e Pinecone
    When leio a seção "Baseline de regressão" de docs/architecture.md
    Then há um número declarado como baseline mínima da SPEC-0010
    And o texto explica que a redução decorre da remoção autorizada de Chroma e Pinecone
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve deixar de conter os adapters
  `ChromaVectorStoreAdapter` e `PineconeVectorStoreAdapter`, os backends
  `_ChromaBackend` e `_PineconeBackend`, as entradas `"chroma"`/`"pinecone"` em
  `_VECTOR_STORES`, `_REAL_PROVIDERS` e
  `SyncSafetyPolicy._SUPPORTED_PROVIDERS`, e as dependências `chromadb`,
  `langchain-chroma` e `langchain-pinecone` em `pyproject.toml`.
- **FR-002**: `ProviderFactory.create_vector_store` deve levantar
  `UnknownProviderError` para `"chroma"` e `"pinecone"`, com mensagem que lista
  apenas os providers mantidos (`in_memory`, `qdrant`).
- **FR-003**: O default de `provider` deve ser `"qdrant"` em
  `src/pipeline/indexing.py` e `pipeline.py`; o argumento `--provider` de
  `upsert_from_chunks.py` deve aceitar apenas `"qdrant"`; os caminhos default
  `./output/chroma_db` devem ser substituídos por um nome neutro em `pipeline.py`
  e `demo_rag.py`.
- **FR-004**: O contrato neutro (`contracts.py`), o backend port, a classe
  `BaseVectorStoreAdapter`, a `ProviderFactory` e o `InMemoryVectorStoreAdapter`
  devem permanecer sem alteração funcional; a suíte de conformidade deve rodar
  sobre `("in_memory", "qdrant")` provando as cinco operações do port, e a
  garantia "modo `mirror` exige `supports_mirror`" deve continuar provada por um
  adapter-dublê sintético.
- **FR-005**: A documentação derivada (`.specsfy/STACK.md`,
  `.specsfy/PACKAGES.md`, `docs/architecture.md`, `docs/packages.md`,
  `docs/integrations.md`, `docs/decisions.md`) deve refletir o projeto
  Qdrant-only, e `docs/architecture.md` deve registrar a baseline de regressão
  da SPEC-0010 com a justificativa da redução.

#### Não funcionais

- **NFR-001**: Nenhuma regressão. **Verificação**: `uv run pytest` termina com
  exit 0 e `uv run ruff check .` sem achados, executados na raiz do repositório.
- **NFR-002**: Ausência estática comprovável. **Verificação**: teste que
  varre `src/` (exceto `src/chunk.egg-info/`), `tests/` e `pyproject.toml` e
  falha se encontrar `chromadb`, `langchain-chroma`, `langchain-pinecone`,
  `_ChromaBackend`, `_PineconeBackend`, `ChromaVectorStoreAdapter` ou
  `PineconeVectorStoreAdapter`.
- **NFR-003**: Extensibilidade preservada. **Verificação**: inspeção do diff —
  `contracts.py` inalterado; mudanças em `factory.py`, `base.py` e `safety.py`
  limitadas à remoção de entradas; a suíte de conformidade continua
  parametrizável por uma tupla de nomes de provider.

#### Erros e casos-limite

- Config com `vector_store.provider: "chroma"` ou `"pinecone"` →
  `UnknownProviderError` com as opções restantes, sem stack trace de `ImportError`.
- `upsert_from_chunks.py --provider pinecone` → `argparse` encerra com erro de
  escolha inválida (exit 2).
- `synchronize(..., mode="mirror")` sobre adapter sem `MirrorMixin` →
  `UnsupportedSyncModeError` orientando `append`.
- Remoção de `chroma.py`/`pinecone.py` deixando import em teste →
  `ModuleNotFoundError` na coleta; endereçado reduzindo os testes na mesma fatia.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Projeto Python ≥ 3.12, gerência por `uv`, testes `pytest` (`testpaths = ["tests"]`),
  lint `ruff==0.16.5`. Sem PHP, sem Node de produção.
- `src/pipeline/providers/vectorstores/` contém `base.py` (contrato + backend
  port + `synchronize`), `in_memory.py`, `qdrant.py`, `chroma.py`, `pinecone.py`.
- `ProviderFactory` em `src/pipeline/providers/factory.py` despacha por nome via
  `_VECTOR_STORES` e `importlib`.
- `SyncSafetyPolicy` em `src/pipeline/safety.py` valida provider e modo antes de
  qualquer cliente; `_SUPPORTED_PROVIDERS = {"qdrant","chroma","pinecone"}`,
  `_MIRROR_PROVIDERS = {"qdrant"}`.
- `_REAL_PROVIDERS = frozenset({"qdrant","chroma","pinecone"})` em `base.py`
  decide quando aplicar `policy.assert_sync_mode_supported`.
- `src/pipeline/indexing.py` e `pipeline.py` leem `vector_cfg.get("provider", "chroma")`.
- Conformidade parametrizada: `test_vectorstore_conformance.py`
  (`BACKENDS = ("in_memory","qdrant","chroma","pinecone")`,
  `APPEND_BACKENDS = ("chroma","pinecone")`, casos dedicados a chunk_id do
  Chroma e a `UnreliableScopeReadError` do Pinecone),
  `test_describe_scope_conformance.py` (`BACKENDS` idem + mapa de backends),
  `test_describe_scope_backends.py` (casos `describe` de Qdrant, Chroma e
  Pinecone), `test_characterization_providers.py`
  (`test_vector_store_chroma_nao_acessa_rede`,
  `test_index_chunks_mirror_fora_do_qdrant_bloqueia_antes_de_compor_provider`
  com `provider="chroma"`).
- `docs/` é regenerado por `$specsfy-documentator`; `docs/architecture.md` tem a
  seção "Baseline de regressão"; `tests/test_ci_gates.py` confere que os números
  de baseline aparecem na documentação (não travam o valor atual).

#### Arquitetura e módulos

- **Remoção pura**: apagar `chroma.py` e `pinecone.py`. Nenhum outro módulo de
  `providers/` importa esses arquivos diretamente (o acoplamento é só via
  `_VECTOR_STORES` com `importlib`, resolvido em runtime).
- **Registros**: editar três conjuntos literais —
  `factory._VECTOR_STORES`, `base._REAL_PROVIDERS`,
  `safety.SyncSafetyPolicy._SUPPORTED_PROVIDERS` — para `{"qdrant"}` (+
  `"in_memory"` onde aplicável em `_VECTOR_STORES`).
- **Defaults de consumo**: `indexing.py` e `pipeline.py` passam a
  `vector_cfg.get("provider", "qdrant")`; `upsert_from_chunks.py`
  `choices=["qdrant"]`; `pipeline.py`/`demo_rag.py` default de
  `vector_store_dir` vira `./output/vector_store`.
- **Dependências**: remover as três linhas de `pyproject.toml`; rodar
  `uv lock` para atualizar o lockfile.
- **Preservação do contrato**: `contracts.py` e `BaseVectorStoreAdapter`
  intactos; `MirrorMixin` intacto; `InMemoryVectorStoreAdapter` intacto;
  `qdrant.py` intacto.
- **Ponto de extensão documentado**: `docs/architecture.md` ganha um parágrafo
  curto "Como adicionar um provider" (módulo novo + entrada em `_VECTOR_STORES`
  + parametrizar a conformance).

#### Migrations

- Não aplicável. Sem schema relacional nesta fatia.

#### Models

- Não aplicável.

#### Controllers e casos de uso

- Não aplicável (sem camada web). Os "casos de uso" tocados são funções de
  módulo: `build_vector_store` / `index_chunks` em `src/pipeline/indexing.py` e
  a composição em `pipeline.py`, apenas na troca de default.

#### Views e experiência

- Não aplicável. `Interface para pessoas: Não`.

#### Queries e repositórios

- Não aplicável.

#### Jobs e processamento assíncrono

- Não aplicável.

#### Estrutura de arquivos

```text
specs/in-progress/0010-enxugar-providers-concretos-qdrant/
  spec.md
  research/                     # sem artefatos externos

src/pipeline/providers/vectorstores/
  chroma.py                     # REMOVER
  pinecone.py                   # REMOVER
  base.py                       # editar _REAL_PROVIDERS
  factory.py  (../factory.py)   # editar _VECTOR_STORES
src/pipeline/
  safety.py                     # editar _SUPPORTED_PROVIDERS
  indexing.py                   # default provider -> "qdrant"
pipeline.py                     # default provider + path neutro
upsert_from_chunks.py           # choices=["qdrant"]
demo_rag.py                     # path neutro
pyproject.toml                  # remover 3 dependências + uv lock

tests/
  test_provider_removal.py            # NOVO — NFR-002, FR-001, FR-002 (estático)
  test_vectorstore_conformance.py     # BACKENDS/APPEND_BACKENDS + remover casos chroma/pinecone
  test_describe_scope_conformance.py  # BACKENDS + mapa de backends
  test_describe_scope_backends.py     # remover blocos Chroma e Pinecone
  test_characterization_providers.py  # substituir provider="chroma" por dublê sintético; remover teste chroma-rede
  test_ci_gates.py                    # adicionar marcador de baseline SPEC-0010
  _fakes_vectorstore.py               # eventual FakeNonMirrorAdapter sintético

docs/architecture.md            # baseline SPEC-0010 + "Como adicionar um provider"
.specsfy/STACK.md               # via $specsfy-aux-stack
.specsfy/PACKAGES.md            # via $specsfy-documentator
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Não aplicável | — | Esta fatia não cria, altera nem remove entidades de dados persistidas. | — |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Não aplicável | — | — | — | — |

#### Migração e retenção

- Não aplicável.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega é uma limpeza interna de código,
  dependências e testes; não há tela, rota renderizada ou fluxo visual. O único
  contato humano é a linha de comando `upsert_from_chunks.py`, cuja única
  mudança é reduzir as escolhas do argumento `--provider`.

#### Stack e convenções de interface

- Não aplicável. Sem camada de interface no repositório.

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

- Não aplicável. Projeto Python sem React.

#### Estados e acessibilidade

- Não aplicável.

#### Contrato CRUD

- Não aplicável.

#### Revisão visual durante o desenvolvimento

- `Não aplicável`: a fatia não tem superfície visual. Todas as tarefas registram
  `VISUAL: Não aplicável` com o motivo "limpeza de código, dependências e testes,
  sem interface renderizada".

#### APIs expostas

- Nenhuma API HTTP. A "API" interna é a assinatura de
  `ProviderFactory.create_vector_store(name, settings)`, preservada; apenas o
  conjunto de `name` aceitos encolhe.

#### APIs externas utilizadas

- Removidas: SDKs `chromadb`/`langchain-chroma` (ChromaDB) e `langchain-pinecone`
  (Pinecone). Mantida: `qdrant-client==1.10.1` (Qdrant), usada de forma lazy
  dentro de `_QdrantBackend`.

#### Documentação das APIs consultadas

- Nenhuma. Sem consulta a documentação externa.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: rejeição da factory para `"chroma"`/`"pinecone"`
  (`UnknownProviderError` + texto da mensagem); default `"qdrant"` em
  `build_vector_store` sem `provider`; `choices` do parser de
  `upsert_from_chunks.py`.
- **Integração/contrato**: suíte de conformidade parametrizada sobre
  `("in_memory", "qdrant")` provando `ensure`/`list_ids`/`upsert`/`query` e a
  extensão `mirror`; rejeição de `mirror` por adapter-dublê sintético sem
  `MirrorMixin`; `describe` do Qdrant preservado em
  `test_describe_scope_backends.py`.
- **Estático**: varredura de `src/` (exceto `src/chunk.egg-info/`), `tests/` e
  `pyproject.toml` por símbolos e dependências removidos; ausência dos arquivos
  `chroma.py` e `pinecone.py`; `contracts.py` inalterado no diff.
- **BDD/aceite**: os Gherkin da seção 6 são o contrato de referência que orienta
  o desenho dos casos TDD; nenhum arquivo `.feature` é criado ou executado.
- **Runner TDD**: `pytest` (runner existente do repositório), via
  `uv run pytest`. Projeto sem PHP e sem Node; nenhuma decisão nova de runner.
- **E2E**: Não aplicável.
- **Verificação manual**: `python upsert_from_chunks.py --help` para conferir o
  texto de ajuda de `--provider` (inevitável porque o texto é gerado pelo
  argparse); registrado como evidência.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, FR-004, NFR-002, AC-001 | AC-001 na seção 6 | `tests/test_provider_removal.py::test_vector_store_registry_has_only_maintained_providers`, marcador próprio `SPECSFY:` | RED 2026-09-04 — `_VECTOR_STORES` ainda inclui `chroma`/`pinecone` | GREEN 2026-09-04 — `_VECTOR_STORES` reduzido a `{qdrant, in_memory}` (T015) | T022: `uv run pytest` → 248 passed; `ruff check .` limpo |
| US-002, FR-001, FR-002, FR-004, AC-002 | AC-002 na seção 6 | `tests/test_provider_removal.py::test_create_vector_store_chroma_raises_unknown_provider`, marcador próprio | RED 2026-09-04 — `create_vector_store("chroma")` ainda sucede | GREEN 2026-09-04 — `create_vector_store("chroma")` levanta `UnknownProviderError` (T015) | T022: `uv run pytest` → 248 passed |
| US-001, FR-001, FR-002, NFR-002, AC-003 | AC-003 na seção 6 | `tests/test_provider_removal.py::test_create_vector_store_pinecone_raises_unknown_provider`, marcador próprio | RED 2026-09-04 — `create_vector_store("pinecone")` ainda sucede | GREEN 2026-09-04 — `create_vector_store("pinecone")` levanta `UnknownProviderError` (T015) | T022: `uv run pytest` → 248 passed |
| US-001, FR-001, NFR-002, AC-004 | AC-004 na seção 6 | `tests/test_provider_removal.py::test_pyproject_has_no_chroma_or_pinecone_deps`, marcador próprio | RED 2026-09-04 — `chromadb`, `langchain-chroma`, `langchain-pinecone` ainda em `pyproject.toml` | GREEN 2026-09-04 — `pyproject.toml` sem os 3 pacotes; `uv.lock` regenerado (T016) | T022: `uv run pytest` → 248 passed |
| US-001, FR-001, NFR-002, AC-005 | AC-005 na seção 6 | `tests/test_provider_removal.py::test_repo_has_no_chroma_or_pinecone_symbols`, marcador próprio | RED 2026-09-04 — `_ChromaBackend`/`_PineconeBackend` e `chroma.py`/`pinecone.py` presentes em `src/` | GREEN 2026-09-04 — símbolos removidos de `src/` (T015) e de `tests/` (T018) | T022: `uv run pytest` → 248 passed |
| US-003, FR-003, NFR-001, AC-006 | AC-006 na seção 6 | `tests/test_characterization_providers.py::test_build_vector_store_default_provider_is_qdrant`, marcador próprio | RED 2026-09-04 — sem `provider`, `build_vector_store` devolve adapter `chroma` | GREEN 2026-09-04 — default `provider` vira `"qdrant"` em `indexing.py`/`pipeline.py` (T017) | T022: `uv run pytest` → 248 passed |
| US-003, FR-003, FR-002, AC-007 | AC-007 na seção 6 | `tests/test_provider_removal.py::test_upsert_cli_only_accepts_qdrant`, marcador próprio | RED 2026-09-04 — `--provider` aceita `chroma`; help lista chroma/pinecone | GREEN 2026-09-04 — `choices` do CLI reduzido a `["qdrant"]` (T017) | T022: `uv run pytest` → 248 passed |
| US-002, FR-004, NFR-001, AC-008 | AC-008 na seção 6 | `tests/test_vectorstore_conformance.py::test_backends_parametrization_excludes_removed_providers`, marcador próprio | RED 2026-09-04 — `BACKENDS` = `("in_memory","qdrant","chroma","pinecone")` | GREEN 2026-09-04 — `BACKENDS`/`APPEND_BACKENDS` reduzidos a `(in_memory, qdrant)` (T018) | T022: `uv run pytest` → 248 passed |
| US-002, FR-004, NFR-003, AC-009 | AC-009 na seção 6 | `tests/test_characterization_providers.py::test_mirror_rejected_for_non_mirror_adapter`, marcador próprio | GREEN imediato 2026-09-04 — comportamento já existe em `_validate_mode`; caso de caracterização que protege a garantia quando T018 remover o subject `provider="chroma"` (RED transitório: `FakeNonMirrorAdapter` ausente antes da fixture desta tarefa) | GREEN 2026-09-04 — `FakeNonMirrorAdapter` consolidado em `_fakes_vectorstore.py`; `synchronize(mode="mirror")` bloqueia via `capabilities().supports_mirror` (T018) | T022: `uv run pytest` → 248 passed |
| US-001, US-003, FR-005, NFR-001, AC-010 | AC-010 na seção 6 | `tests/test_ci_gates.py::test_spec0010_provider_removal_baseline_is_recorded`, marcador próprio | RED 2026-09-04 — baseline da SPEC-0010 ausente em `docs/architecture.md` | GREEN 2026-09-04 — baseline SPEC-0010 (248) registrada em `docs/architecture.md` (T020) | T022: `uv run pytest` → 248 passed |
| FR-005, NFR-002, AC-011 | AC-011 na seção 6 | `tests/test_provider_removal.py::test_docs_do_not_list_chroma_or_pinecone_as_active_targets`, marcador próprio | RED 2026-09-04 — `docs/packages.md`, `docs/integrations.md`, `docs/architecture.md` citam ChromaDB/Pinecone | GREEN 2026-09-04 — docs regeneradas/editadas sem citar ChromaDB/Pinecone como ativos (T020) | T022: `uv run pytest` → 248 passed |
| US-002, FR-004, NFR-003, AC-012 | AC-012 na seção 6 | `tests/test_provider_removal.py::test_contracts_module_unchanged_and_factory_surface_stable`, marcador próprio | RED 2026-09-04 — `chroma`/`pinecone` ainda em `_VECTOR_STORES` (sha256 de `contracts.py` confere) | GREEN 2026-09-04 — `contracts.py` inalterado (sha256 confere); `_VECTOR_STORES` sem chroma/pinecone (T015) | T022: `uv run pytest` → 248 passed |
| US-003, FR-003, NFR-001, AC-013 | AC-013 na seção 6 | `tests/test_provider_removal.py::test_no_default_points_to_removed_provider`, marcador próprio | RED 2026-09-04 — default `"chroma"` em `indexing.py` e `pipeline.py` | GREEN 2026-09-04 — defaults `"qdrant"`; sem string `"chroma"` nos dois arquivos (T017) | T022: `uv run pytest` → 248 passed |
| FR-005, NFR-001, NFR-003, AC-014 | AC-014 na seção 6 | `tests/test_ci_gates.py::test_spec0010_baseline_reduction_is_justified`, marcador próprio | RED 2026-09-04 — seção "Baseline de regressão" não explica a redução por remoção de Chroma/Pinecone | GREEN 2026-09-04 — seção de baseline explica a redução por remoção de Chroma/Pinecone (T020) | T022: `uv run pytest` → 248 passed |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-001 | AC-004 | Estático | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-001 | AC-005 | Estático | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-002 | AC-002 | Unidade | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-002 | AC-003 | Unidade | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-002 | AC-007 | Unidade | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-003 | AC-006 | Integração | `tests/test_characterization_providers.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-003 | AC-013 | Estático | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-003 | AC-007 | Unidade | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-004 | AC-008 | Contrato | `uv run pytest tests/test_vectorstore_conformance.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-004 | AC-009 | Contrato | `tests/test_characterization_providers.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-004 | AC-012 | Estático | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-005 | AC-010 | Regressão | `uv run pytest` + `uv run ruff check .` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-005 | AC-011 | Estático | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| FR-005 | AC-014 | Inspeção | `tests/test_ci_gates.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| NFR-001 | AC-006 | Integração | `uv run pytest tests/test_characterization_providers.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| NFR-001 | AC-010 | Regressão | `uv run pytest` (exit 0) | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| NFR-001 | AC-013 | Estático | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| NFR-002 | AC-004 | Estático | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| NFR-002 | AC-005 | Estático | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| NFR-002 | AC-011 | Estático | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| NFR-003 | AC-009 | Contrato | `tests/test_characterization_providers.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| NFR-003 | AC-012 | Estático | `tests/test_provider_removal.py` | Passed — `uv run pytest` 248 passed, `ruff check .` limpo (confirmado após T020; T022 refaz a regressão final) |
| NFR-003 | AC-014 | Inspeção | `tests/test_ci_gates.py` | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed — 2026-09-04
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/in-progress/0010-enxugar-providers-concretos-qdrant/spec.md` → `VALID`
- **Achados**:
  - Estrutural: `VALID DRAFT` e depois `VALID`; três atos na ordem, slug igual ao
    diretório, pacote restrito a `spec.md` (sem `research/` porque não houve
    fonte externa).
  - Cobertura: US 3 · FR 5 · NFR 3 · AC 14. Cada `US`, `FR` e `NFR` tem ≥ 3 `AC`
    em `**Cobre**` (mínimo observado: 3; FR-001/FR-004/NFR-001/NFR-002/US-001 com 5).
  - Comportamento: jornadas P1 (US-001/US-002/US-003) com caminho feliz
    (AC-001, AC-006, AC-008) e falha material (AC-002, AC-003, AC-007, AC-009).
  - `NOTE` resolvido nesta validação: DoD passou a citar `.specsfy/STACK.md`,
    `.specsfy/PACKAGES.md`, revisão de `PROJECT.md` e a não aplicabilidade de
    `.specsfy/DATABASE.md`, porque a fatia remove dependências (mudança de stack).
  - Sem `BLOCKER`. Sem findings especializados de produto, arquitetura ou
    segurança (remoção interna, sem superfície nova).
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed — 2026-09-04
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0010-enxugar-providers-concretos-qdrant/spec.md` → `READY`
- **Achados**:
  - 22 tarefas: 14 `[TEST][TDD]` (T001–T014, uma por AC) + 4 `[CODE]` (T015–T018)
    + 3 `[DOC]` (T019–T021) + 1 `[TEST]` de fechamento (T022).
  - Cobertura: 25/25 IDs (US/FR/NFR/AC). Cada `US`, `FR` e `NFR` com ≥ 3
    predecessores TDD; cada `AC` com ao menos um caso.
  - RED registrado na seção 11 para os 14 casos. 13 falharam pelo
    comportamento ausente (Chroma/Pinecone ainda no projeto); AC-009 é caso de
    caracterização (comportamento já existe) e protege a garantia de `mirror`
    após a remoção do subject `provider="chroma"`.
  - `check_traceability.mjs` → 25/25 IDs da SPEC-0010 cobertos; "marcadores
    órfãos" listados são de specs anteriores nos mesmos arquivos de teste
    (exit 0, condição idêntica à SPEC-0009).
  - Predecessores TDD de todas as tarefas `[CODE]` concluídos com RED.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0010-enxugar-providers-concretos-qdrant/spec.md .`
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

Todos os casos usam `pytest` (`uv run pytest`), runner já estabelecido do
repositório, com um marcador `SPECSFY:` próprio por caso. Nenhum arquivo
`.feature` é criado ou executado. As tarefas de teste não compartilham
dependência mútua de comportamento; não recebem `[P]` apenas porque várias
escrevem no mesmo arquivo novo `tests/test_provider_removal.py`.

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 o caso `test_vector_store_registry_has_only_maintained_providers` em `tests/test_provider_removal.py` — Refs: US-001, FR-001, FR-004, NFR-002, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 e confirmar as chaves esperadas de `ProviderFactory._VECTOR_STORES`.
  - [x] **EXECUTE**: Escrever o caso asseverando `{"qdrant","in_memory"}` e ausência de import de chroma/pinecone no módulo; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py -k registry_has_only_maintained` → RED (chaves ainda incluem chroma/pinecone).
  - [x] **VISUAL**: `Não aplicável` — a tarefa só materializa teste, sem superfície visual.
  - [x] **EVIDENCE**: Registrar comando e causa do RED na seção 11.
  - [x] **IMPROVE**: Revisar cobertura e registrar aprendizado ou ausência justificada.

- [x] T002 [TEST] [TDD] [US-002] Derivar do AC-002 o caso `test_create_vector_store_chroma_raises_unknown_provider` em `tests/test_provider_removal.py` — Refs: US-002, FR-001, FR-002, FR-004, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 e o texto atual de `UnknownProviderError`.
  - [x] **EXECUTE**: Escrever o caso esperando `UnknownProviderError` com mensagem listando `in_memory, qdrant`; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py -k chroma_raises_unknown` → RED (hoje `create_vector_store("chroma")` sucede).
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 o caso `test_create_vector_store_pinecone_raises_unknown_provider` em `tests/test_provider_removal.py` — Refs: US-001, FR-001, FR-002, NFR-002, AC-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-003.
  - [x] **EXECUTE**: Escrever o caso esperando `UnknownProviderError` sem "pinecone" como opção válida; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py -k pinecone_raises_unknown` → RED.
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 o caso `test_pyproject_has_no_chroma_or_pinecone_deps` em `tests/test_provider_removal.py` — Refs: US-001, FR-001, NFR-002, AC-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-004 e a lista `dependencies` de `pyproject.toml`.
  - [x] **EXECUTE**: Escrever o caso falhando se `chromadb`, `langchain-chroma` ou `langchain-pinecone` aparecerem em `dependencies`, e exigindo `qdrant-client`; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py -k pyproject_has_no_chroma` → RED (três deps presentes).
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 o caso `test_repo_has_no_chroma_or_pinecone_symbols` em `tests/test_provider_removal.py` — Refs: US-001, FR-001, NFR-002, AC-005 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-005 e listar os símbolos alvo (`_ChromaBackend`, `_PineconeBackend`, `ChromaVectorStoreAdapter`, `PineconeVectorStoreAdapter`).
  - [x] **EXECUTE**: Escrever o caso varrendo `src/` (exceto `src/chunk.egg-info/`), `tests/` e `pyproject.toml`, e checando ausência de `chroma.py`/`pinecone.py`; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py -k has_no_chroma_or_pinecone_symbols` → RED.
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T006 [TEST] [TDD] [US-003] Derivar do AC-006 o caso `test_build_vector_store_default_provider_is_qdrant` em `tests/test_characterization_providers.py` — Refs: US-003, FR-003, NFR-001, AC-006 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-006 e a assinatura de `build_vector_store`.
  - [x] **EXECUTE**: Escrever o caso com `vector_cfg` sem a chave `provider`, esperando adapter com `provider == "qdrant"`; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_characterization_providers.py -k default_provider_is_qdrant` → RED (default atual é `"chroma"`).
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T007 [TEST] [TDD] [US-003] Derivar do AC-007 o caso `test_upsert_cli_only_accepts_qdrant` em `tests/test_provider_removal.py` — Refs: US-003, FR-002, FR-003, AC-007 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-007 e o parser de `upsert_from_chunks.py`.
  - [x] **EXECUTE**: Escrever o caso esperando `SystemExit` para `--provider chroma` e apenas `qdrant` no help de `--provider`; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py -k cli_only_accepts_qdrant` → RED (`choices` ainda inclui chroma/pinecone).
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 o caso `test_backends_parametrization_excludes_removed_providers` em `tests/test_vectorstore_conformance.py` — Refs: US-002, FR-004, NFR-001, AC-008 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-008 e localizar `BACKENDS` e `APPEND_BACKENDS`.
  - [x] **EXECUTE**: Escrever o caso asseverando que nenhuma tupla de parametrização contém `"chroma"` ou `"pinecone"`; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_vectorstore_conformance.py -k parametrization_excludes_removed` → RED.
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 o caso `test_mirror_rejected_for_non_mirror_adapter` em `tests/test_characterization_providers.py`, com `FakeNonMirrorAdapter` em `tests/_fakes_vectorstore.py` — Refs: US-002, FR-004, NFR-003, AC-009 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-009 e a lógica de `_validate_mode`/`capabilities()` em `providers/vectorstores/base.py`.
  - [x] **EXECUTE**: Adicionar `FakeNonMirrorAdapter` (sem `MirrorMixin`, `supports_mirror = False`) e o caso esperando `UnsupportedSyncModeError` para `synchronize(..., mode="mirror")`; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_characterization_providers.py -k mirror_rejected_for_non_mirror` → RED (dublê ainda não existe).
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T010 [TEST] [TDD] [US-001] Derivar do AC-010 o caso `test_spec0010_provider_removal_baseline_is_recorded` em `tests/test_ci_gates.py` — Refs: US-001, US-003, FR-005, NFR-001, AC-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-010 e o padrão dos marcadores `_BASELINE_MINIMA`/`_SPEC0009_BASELINE`.
  - [x] **EXECUTE**: Escrever o caso exigindo um número declarado como baseline mínima da SPEC-0010 junto da palavra "baseline" em `docs/architecture.md`; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_ci_gates.py -k spec0010_provider_removal_baseline` → RED (texto ainda não existe).
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T011 [TEST] [TDD] [US-001] Derivar do AC-011 o caso `test_docs_do_not_list_chroma_or_pinecone_as_active_targets` em `tests/test_provider_removal.py` — Refs: FR-005, NFR-002, AC-011 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-011 e as menções atuais em `docs/packages.md`, `docs/integrations.md`, `docs/architecture.md`.
  - [x] **EXECUTE**: Escrever o caso falhando se ChromaDB ou Pinecone aparecerem como destino vetorial ativo nessas páginas; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py -k docs_do_not_list_chroma` → RED.
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T012 [TEST] [TDD] [US-002] Derivar do AC-012 o caso `test_contracts_module_unchanged_and_factory_surface_stable` em `tests/test_provider_removal.py` — Refs: US-002, FR-004, NFR-003, AC-012 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-012; capturar o conteúdo atual de `providers/contracts.py` e a lista de métodos públicos de `ProviderFactory`.
  - [x] **EXECUTE**: Escrever o caso asseverando `contracts.py` byte a byte igual ao snapshot e a superfície pública de `ProviderFactory` inalterada (métodos `create_embedding`, `create_vector_store`); marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py -k contracts_module_unchanged` → RED enquanto o snapshot esperado não estiver fixado (o caso nasce RED por falta do baseline embutido).
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-013 o caso `test_no_default_points_to_removed_provider` em `tests/test_provider_removal.py` — Refs: US-003, FR-003, NFR-001, AC-013 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-013 e as ocorrências de `vector_cfg.get("provider", ...)` em `src/pipeline/indexing.py` e `pipeline.py`.
  - [x] **EXECUTE**: Escrever o caso asseverando default `"qdrant"` em toda ocorrência e ausência da string `"chroma"` nos dois arquivos; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py -k no_default_points_to_removed` → RED (default atual `"chroma"`).
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

- [x] T014 [TEST] [TDD] [US-001] Derivar do AC-014 o caso `test_spec0010_baseline_reduction_is_justified` em `tests/test_ci_gates.py` — Refs: FR-005, NFR-001, NFR-003, AC-014 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-014 e a seção "Baseline de regressão" de `docs/architecture.md`.
  - [x] **EXECUTE**: Escrever o caso exigindo, na seção "Baseline de regressão", texto que explique que a redução decorre da remoção autorizada de Chroma e Pinecone; marcador `SPECSFY:` próprio.
  - [x] **VERIFY**: `uv run pytest tests/test_ci_gates.py -k spec0010_baseline_reduction` → RED.
  - [x] **VISUAL**: `Não aplicável` — só materializa teste.
  - [x] **EVIDENCE**: Registrar comando e causa do RED.
  - [x] **IMPROVE**: Registrar aprendizado ou ausência justificada.

#### Fase 2 — US-001 / US-002 / US-003 — Remoção e ajuste (P1)

**Objetivo**: tornar o projeto Qdrant-only preservando a abstração multi-provider.
**Teste independente**: `uv run pytest tests/test_provider_removal.py` e a suíte
completa verdes; `grep` dos símbolos removidos vazio.

- [x] T015 [CODE] [US-001] Remover `src/pipeline/providers/vectorstores/chroma.py` e `pinecone.py` e limpar as entradas `"chroma"`/`"pinecone"` de `factory._VECTOR_STORES`, `base._REAL_PROVIDERS` e `safety.SyncSafetyPolicy._SUPPORTED_PROVIDERS` — Refs: US-001, US-002, FR-001, FR-002, FR-004, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-005, AC-012 — Depends: T001, T002, T003, T005, T012
  - [x] **PREP**: Confirmado RED de T001/T002/T003/T005/T012; único ponto de referência em produção eram as strings de registro em `factory.py` (via `importlib`, não import direto) — sem consumidor a quebrar.
  - [x] **EXECUTE**: Apagados os dois arquivos; editados os três conjuntos literais para `{"qdrant"}` (+ `"in_memory"` em `_VECTOR_STORES`).
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py` → T001/T002/T003/T012 GREEN imediato. T005 (AC-005) ficou parcialmente RED porque `tests/` ainda citava os símbolos removidos — fechado no T018, que amplia o escopo original.
  - [x] **VISUAL**: `Não aplicável` — limpeza de código, sem interface renderizada.
  - [x] **EVIDENCE**: Suíte completa após T015 isolado: 58 failed / 227 passed (todas as 58 falhas eram os casos chroma/pinecone ainda não limpos em T016–T018).
  - [x] **IMPROVE**: Nenhuma melhoria adicional — remoção mecânica sem efeito colateral em produção.
  <!-- specsfy:evidence {"task":"T015","refs":["US-001","US-002","FR-001","FR-002","FR-004","NFR-002","NFR-003","AC-001","AC-002","AC-003","AC-005","AC-012"],"files":["src/pipeline/providers/factory.py","src/pipeline/providers/vectorstores/base.py","src/pipeline/safety.py"],"commands":[{"run":"uv run pytest tests/test_provider_removal.py -k \"registry_has_only_maintained or chroma_raises_unknown or pinecone_raises_unknown or contracts_module_unchanged\"","exit":0}]} -->

- [x] T016 [CODE] [US-001] Remover `chromadb`, `langchain-chroma` e `langchain-pinecone` de `pyproject.toml` e regenerar `uv.lock` com `uv lock`, conferindo por `tests/test_provider_removal.py` — Refs: US-001, FR-001, NFR-002, AC-004 — Depends: T004, T015
  - [x] **PREP**: Confirmado RED de T004; nenhum import remanescente usava os três pacotes fora dos arquivos já apagados no T015.
  - [x] **EXECUTE**: Removidas as 3 linhas de `dependencies`; `uv lock` e `uv sync` executados.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py -k pyproject_has_no_chroma` → GREEN; `uv sync` sem erro.
  - [x] **VISUAL**: `Não aplicável` — manifesto de dependências, sem interface.
  - [x] **EVIDENCE**: `uv.lock` reduziu 1065 linhas (remoção transitiva incl. `simsimd`, `uvicorn`, `uvloop`, `watchfiles`, `websockets` e outros só usados por Chroma/Pinecone).
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.
  <!-- specsfy:evidence {"task":"T016","refs":["US-001","FR-001","NFR-002","AC-004"],"files":["pyproject.toml","uv.lock"],"commands":[{"run":"uv lock","exit":0},{"run":"uv run pytest tests/test_provider_removal.py -k pyproject_has_no_chroma","exit":0}]} -->

- [x] T017 [CODE] [US-003] Trocar o default de `provider` para `"qdrant"` em `src/pipeline/indexing.py` e `pipeline.py`; reduzir `choices` de `--provider` para `["qdrant"]` em `upsert_from_chunks.py`; substituir `./output/chroma_db` por `./output/vector_store` em `pipeline.py` e `demo_rag.py` — Refs: US-003, FR-002, FR-003, NFR-001, AC-006, AC-007, AC-013 — Depends: T006, T007, T013
  - [x] **PREP**: Confirmado RED de T006/T007/T013; localizadas todas as ocorrências de `"chroma"` nos quatro arquivos, incl. o branch `if provider == "pinecone"` de display em `pipeline.py`.
  - [x] **EXECUTE**: Trocas aplicadas; `pipeline.py` simplificado para exibir só `Qdrant: <collection>` (removido branch morto de Chroma/Pinecone); variável `vector_store_dir` removida por ficar sem uso após a simplificação (evitava F841 do ruff).
  - [x] **VERIFY**: `uv run pytest tests/test_provider_removal.py tests/test_characterization_providers.py -k "cli_only_accepts_qdrant or no_default_points or default_provider_is_qdrant"` → GREEN; `python upsert_from_chunks.py --help` mostra só `qdrant`.
  - [x] **VISUAL**: `Não aplicável` — CLI e defaults de configuração, sem interface renderizada.
  - [x] **EVIDENCE**: Corrigido bug no próprio teste T013 (`test_no_default_points_to_removed_provider`): a regex original também capturava o default de `embedding_cfg.get("provider", "openrouter")`; restrita a `vector_cfg.get(...)`.
  - [x] **IMPROVE**: Ajuste de teste registrado acima; nenhuma melhoria adicional de produção necessária.
  <!-- specsfy:evidence {"task":"T017","refs":["US-003","FR-002","FR-003","NFR-001","AC-006","AC-007","AC-013"],"files":["src/pipeline/indexing.py","pipeline.py","upsert_from_chunks.py","demo_rag.py","tests/test_provider_removal.py"],"commands":[{"run":"uv run pytest tests/test_provider_removal.py -k \"cli_only_accepts_qdrant or no_default_points\"","exit":0}]} -->

- [x] T018 [CODE] [US-002] Reduzir a conformidade para `("in_memory", "qdrant")` em `test_vectorstore_conformance.py` e `test_describe_scope_conformance.py`, remover os casos dedicados a Chroma/Pinecone (chunk_id, `LegacyDestinationError`, `UnreliableScopeReadError` do Pinecone, mapa de backends) e os blocos Chroma/Pinecone de `test_describe_scope_backends.py`; substituir `provider="chroma"` por `FakeNonMirrorAdapter` no teste de mirror e remover `test_vector_store_chroma_nao_acessa_rede`. **Escopo ampliado na execução** (correção interna de plano) para incluir `test_safety.py`, `test_safety_policy.py`, `test_provider_factory.py` e `test_client_neutrality.py`, que também citavam chroma/pinecone e não constavam da tarefa original — Refs: US-002, FR-004, NFR-001, NFR-003, AC-008, AC-009 — Depends: T008, T009, T015
  - [x] **PREP**: Confirmado RED de T008/T009. A execução revelou que o escopo descrito na tarefa estava incompleto: `tests/test_safety.py`, `tests/test_safety_policy.py`, `tests/test_provider_factory.py` e `tests/test_client_neutrality.py` também tinham parametrização ou baseline fixa com `chroma`/`pinecone`, não listados originalmente. Ampliado o escopo para os quatro arquivos — correção interna de plano, mesmo comportamento, nenhum AC alterado.
  - [x] **EXECUTE**: Editadas as 4 suítes previstas + as 4 descobertas (8 no total); `FakeNonMirrorAdapter` consolidado em `tests/_fakes_vectorstore.py`. Reframing documentado inline: `test_safety.py`/`test_safety_policy.py` (SPEC-0001) passaram a provar rejeição de provider **removido** (mensagem "não suportado") em vez de "modo espelho não suportado" por `chroma` — a garantia de fail-closed antes do destino é a mesma; `test_provider_factory.py` (SPEC-0003) perdeu os 2 providers do dicionário de fixtures; `test_client_neutrality.py` (SPEC-0005) teve sua baseline de dependências congelada atualizada.
  - [x] **VERIFY**: `uv run pytest` → 248 passed, 0 failed (as 3 falhas restantes eram exclusivamente as do T020, fechadas depois); `uv run ruff check .` → limpo (4 achados corrigidos: `UP037` em `_fakes_vectorstore.py`, `F401` em `test_describe_scope_backends.py`, 2× `PLW1510` em `test_provider_removal.py`).
  - [x] **VISUAL**: `Não aplicável` — suítes de teste, sem interface.
  - [x] **EVIDENCE**: Nota de risco preservada em comentário nos arquivos: a checagem "`mirror` exige `_MIRROR_PROVIDERS`" em `safety.py` ficou inalcançável (só sobrou `qdrant`, que é mirror-capable) — não é regressão, é defesa redundante agora coberta a montante pela checagem `capabilities().supports_mirror` em `synchronize`, provada por `test_mirror_rejected_for_non_mirror_adapter` (AC-009).
  - [x] **IMPROVE**: Escopo da tarefa corrigido e documentado; ruff aplicado a todos os arquivos tocados.
  <!-- specsfy:evidence {"task":"T018","refs":["US-002","FR-004","NFR-001","NFR-003","AC-008","AC-009"],"files":["tests/test_vectorstore_conformance.py","tests/test_describe_scope_conformance.py","tests/test_describe_scope_backends.py","tests/test_characterization_providers.py","tests/_fakes_vectorstore.py","tests/test_safety.py","tests/test_safety_policy.py","tests/test_provider_factory.py","tests/test_client_neutrality.py"],"commands":[{"run":"uv run pytest","exit":0},{"run":"uv run ruff check .","exit":0}]} -->

#### Fase 3 — Documentação, stack e regras

- [x] T019 [DOC] [US-001] Atualizar `.specsfy/STACK.md` via `$specsfy-aux-stack` para refletir a remoção de `chromadb`, `langchain-chroma` e `langchain-pinecone` e o Qdrant como único destino vetorial concreto — Refs: US-001, FR-005, NFR-002 — Depends: T016
  - [x] **PREP**: Confirmar T016 concluída; ler `.specsfy/STACK.md` atual.
  - [x] **EXECUTE**: `$specsfy-aux-stack` rodado; `update_stack.mjs` sem alteração no bloco `specsfy:stack`; edição manual da linha "Bancos vetoriais alternativos" → "Abstração de vector store" (contrato neutro + `ProviderFactory` + `in_memory`) e nova decisão SPEC-0010 na seção humana.
  - [x] **VERIFY**: `monitor_context.mjs --project . --check` confirmou `.specsfy/STACK.md` fora da lista de pendências após a edição (só restava `docs/`, fechado no T020).
  - [x] **VISUAL**: `Não aplicável` — documento Markdown de contexto, sem interface.
  - [x] **EVIDENCE**: Comando `monitor_context.mjs --project . --check` e trechos alterados registrados no EXECUTE acima.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária — atualização pontual e suficiente.
  <!-- specsfy:evidence {"task":"T019","refs":["US-001","FR-005","NFR-002"],"files":[".specsfy/STACK.md"],"commands":[{"run":"node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check","exit":0}]} -->

- [x] T020 [DOC] [US-001] Rodar `$specsfy-documentator` para regenerar `docs/` e `.specsfy/PACKAGES.md`; registrar em `docs/architecture.md` a baseline de regressão da SPEC-0010 (contagem nova + razão da redução) e um parágrafo "Como adicionar um provider" — Refs: US-001, FR-005, NFR-001, NFR-002, NFR-003, AC-010, AC-011, AC-014 — Depends: T015, T016, T017, T018, T019
  - [x] **PREP**: Confirmado T015–T019; contagem pré-remoção era 271 (SPEC-0009).
  - [x] **EXECUTE**: `$specsfy-documentator` (`build_documentation.mjs`) rodado — blocos `specsfy:documentator` sem mudança de conteúdo (curtos por desenho). Correções manuais no conteúdo humano que o código não sustentava mais: `docs/packages.md`, `docs/integrations.md`, `docs/decisions.md`, `docs/architecture.md` (diagrama + texto de `describe`), `docs/application.md`, `docs/database.md`, `docs/testing.md`, `docs/README.md`. Seção "Baseline de regressão" ganhou o parágrafo da SPEC-0010; seção nova "Como adicionar um provider" adicionada.
  - [x] **VERIFY**: `uv run pytest` → 248 passed (0 failed); `uv run ruff check .` → limpo; `build_documentation.mjs --project . --check` → sem achados. Um bug do próprio teste T011 (`test_docs_do_not_list_chroma_or_pinecone_as_active_targets`) apareceu e foi corrigido: a checagem por substring simples reprovava a própria menção histórica "removido pela SPEC-0010"; passou a avaliar por parágrafo com marcador de remoção.
  - [x] **VISUAL**: `Não aplicável` — documentação Markdown, sem interface renderizada.
  - [x] **EVIDENCE**: Ver comandos e resultados no VERIFY; baseline nova (248) e razão da redução registradas em `docs/architecture.md`. `monitor_context.mjs` deixou de listar `docs/` como pendente; só resta `PROJECT.md` (T022).
  - [x] **IMPROVE**: Teste AC-011 corrigido de checagem literal por substring para checagem por parágrafo com marcador de contexto — evita falso positivo em menção histórica futura.
  <!-- specsfy:evidence {"task":"T020","refs":["US-001","FR-005","NFR-001","NFR-002","NFR-003","AC-010","AC-011","AC-014"],"files":["docs/architecture.md","docs/packages.md","docs/integrations.md","docs/decisions.md","docs/application.md","docs/database.md","docs/testing.md","docs/README.md","tests/test_provider_removal.py"],"commands":[{"run":"uv run pytest","exit":0}]} -->

- [x] T021 [DOC] [US-002] Registrar em `.specsfy/RULES.md`, via `$specsfy-aux-rules`, a convenção confirmada: o projeto mantém a abstração multi-provider de vector store com Qdrant como único provider concreto; adicionar um provider é módulo novo + entrada em `_VECTOR_STORES` + parametrização da conformidade — Refs: US-002, FR-004 — Depends: T015
  - [x] **PREP**: Confirmado T015; lido `.specsfy/RULES.md` — sem duplicata da disciplina de baseline (PR-004, que é do contrato central, não deste arquivo).
  - [x] **EXECUTE**: `$specsfy-aux-rules` (`add_rule.mjs`) adicionou a regra na seção "Arquitetura" (linha 25), preservando as regras existentes.
  - [x] **VERIFY**: `grep` confirma a regra nova presente; `monitor_context.mjs --project . --check` → `PENDING` só por `PROJECT.md` (esperado; fecha em T022).
  - [x] **VISUAL**: `Não aplicável` — documento Markdown de regras.
  - [x] **EVIDENCE**: Regra adicionada: "Manter Qdrant como único provider concreto de vector store; a abstração multi-provider [...] permanece aberta [...]. ChromaDB e Pinecone foram removidos pela SPEC-0010 [...]". **Conflito sinalizado e resolvido com confirmação do usuário**: duas menções pré-existentes desatualizadas — cabeçalho do arquivo ("bancos vetoriais Qdrant, ChromaDB e Pinecone") e a regra de confinamento de imports em "Arquitetura" (listava `chromadb`, `pinecone`, `langchain-chroma`, `langchain-pinecone`) — foram atualizadas após autorização explícita. `uv run pytest` → 248 passed; `uv run ruff check .` limpo após a edição.
  - [x] **IMPROVE**: Nenhuma melhoria adicional necessária.
  <!-- specsfy:evidence {"task":"T021","refs":["US-002","FR-004"],"files":[".specsfy/RULES.md"],"commands":[{"run":"grep -n \"único provider concreto de vector store\" .specsfy/RULES.md","exit":0}]} -->

#### Fase final — Qualidade

- [ ] T022 [TEST] Executar regressão completa, rastreabilidade e revisão de `PROJECT.md` — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014 — Depends: T019, T020, T021
  - [ ] **PREP**: Identificar suítes, `ruff` e o script de rastreabilidade; abrir `PROJECT.md`.
  - [ ] **EXECUTE**: `uv run pytest`; `uv run ruff check .`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0010-enxugar-providers-concretos-qdrant/spec.md .`; revisar `PROJECT.md` — a finalidade e as capacidades seguem válidas (abstração multi-provider preservada); se não houver impacto material, registrar a justificativa nesta evidência.
  - [ ] **VERIFY**: pytest exit 0, ruff sem achados, rastreabilidade sem gaps, `PROJECT.md` avaliado.
  - [ ] **VISUAL**: `Não aplicável` — sem superfície visual em toda a fatia.
  - [ ] **EVIDENCE**: Registrar contagens finais, comandos e a avaliação de `PROJECT.md` na seção 12.
  - [ ] **IMPROVE**: Registrar retrospectiva do processo.

### 15. Ordem de execução

- Caminho crítico: T001..T014 (RED, sem dependência mútua) → T015 → T016 →
  T017/T018 → T019 → T020 → T021 → T022.
- Tarefas paralelas em prática: T001..T014 materializam RED em quatro arquivos
  de teste (`test_provider_removal.py`, `test_characterization_providers.py`,
  `test_vectorstore_conformance.py`, `test_ci_gates.py`) sem dependência mútua
  de comportamento; não recebem `[P]` porque várias compartilham
  `test_provider_removal.py`. Depois de T015, T017 e T018 tocam arquivos
  distintos e podem avançar em paralelo; T016 precisa vir logo após T015 para
  não deixar `uv.lock` inconsistente.
- Estratégia de MVP: T001–T005 + T012 + T015 já entregam o núcleo (adapters e
  registros removidos, factory rejeitando os nomes, contrato preservado); as
  demais fecham dependências, defaults, conformidade, documentação e regras.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Contrato, backend port e adapters entregues pela SPEC-0003 (não podem ser
  quebrados).
- Padrão de baseline de regressão estabelecido por SPEC-0008 e SPEC-0009 em
  `docs/architecture.md` e `tests/test_ci_gates.py`.
- `$specsfy-aux-stack` e `$specsfy-documentator` para a fase de documentação.

#### Riscos

- Referência órfã a Chroma/Pinecone sobrevive à remoção → mitigada por AC-005 e
  AC-011 como varredura estática executável.
- O teste "mirror rejeitado fora do Qdrant" perde o sujeito (só sobram
  provedores mirror-capable) → mitigada pelo `FakeNonMirrorAdapter` sintético
  (AC-009).
- Redução da baseline confundida com regressão → mitigada por PR-004, AC-010 e
  AC-014, que exigem registro e justificativa explícitos.
- `uv lock` puxa mudança transitiva ampla → mitigada por revisão do diff de
  `uv.lock` na evidência de T006 e pela regressão de T010.

#### Suposições

- `src/chunk.egg-info/*` é artefato gerado e não conta como ocorrência nas
  varreduras (default reversível; ajustável no teste se o build mudar).
- Nenhum consumidor externo ao repositório importa `ChromaVectorStoreAdapter` ou
  `PineconeVectorStoreAdapter` hoje.
- `./output/vector_store` é um nome de diretório default aceitável para
  substituir `./output/chroma_db`; ajustável sem impacto de comportamento.
- `langchain-community` e demais pacotes `langchain-*` permanecem porque servem a
  outras camadas do pipeline.

### 17. Decisões

- **DEC-001**: Remover apenas as implementações concretas não escolhidas
  (ChromaDB, Pinecone) e suas dependências, preservando a abstração
  multi-provider (contrato, port, `ProviderFactory`, `in_memory`). Alternativa
  descartada: remover também a abstração e tornar o Qdrant o único caminho
  codificado — rejeitada porque o usuário declarou que vai usar multi-provider e
  quer o projeto aberto para novos provedores.
- **DEC-002**: `provider` default passa a `"qdrant"`. Alternativas: exigir
  `provider` explícito (mais atrito no caminho feliz) ou default `"in_memory"`
  (esconde erro de configuração de produção) — descartadas por DEC-002 escolher
  o provedor real efetivamente usado.
- **DEC-003**: Preservar a garantia "modo `mirror` exige `supports_mirror`" com
  um adapter-dublê sintético em vez de manter um provedor real incapaz de
  mirror só para o teste. Trade-off: um fake a mais em `tests/`, contra manter
  um SDK inteiro.
- **DEC-004**: Autorizar a redução da baseline de regressão, registrando a nova
  contagem e a razão em `docs/architecture.md` (PR-004). Sem essa decisão a
  remoção seria lida como regressão pela disciplina de baseline do projeto.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam (`uv run pytest`, `uv run ruff check .`).
- [ ] `.specsfy/STACK.md` atualizado (via `$specsfy-aux-stack`) refletindo a
  remoção de `chromadb`, `langchain-chroma` e `langchain-pinecone`; `.specsfy/PACKAGES.md`
  e `docs/` regenerados por `$specsfy-documentator`.
- [ ] `PROJECT.md` revisado: a finalidade e as capacidades do projeto seguem
  válidas (a abstração multi-provider é preservada); se não houver impacto
  material, a justificativa fica registrada na evidência de T009.
- [ ] `.specsfy/DATABASE.md` não se aplica — a fatia não altera persistência;
  justificativa registrada na evidência de T010.
- [ ] `docs/architecture.md` registra a baseline de regressão da SPEC-0010 com a
  razão da redução (DEC-004).
