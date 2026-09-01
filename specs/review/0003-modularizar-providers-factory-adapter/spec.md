# Especificação integrada: Modularizar providers com Factory e Adapter

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0003 |
| Slug | 0003-modularizar-providers-factory-adapter |
| Status | Reviewing |
| Effort | 7 |
| Effort updated at | 2026-09-01 |
| Effort rationale | Refatoração ampla em caminho crítico: contratos neutros, seis adapters, cinco consumidores, segurança fail-closed, recuperação escopada, duas integrações LangChain novas e suíte de conformidade. |
| ClickUp Task | |
| Milestones | M0 — Finalizar o componente rag-ingestion-pipeline |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-01 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

`src/embedder.py` concentra criação de embeddings, acesso a Qdrant, ChromaDB e Pinecone, sincronização, recuperação e condicionais por fornecedor. O Qdrant possui espelho idempotente e contagens, enquanto ChromaDB duplica registros e Pinecone opera em `append` sem contagens. Essa fronteira monolítica dificulta trocar providers, testar segurança e preservar comportamento entre backends.

#### Resultado desejado

Embeddings e vector stores tornam-se plugins intercambiáveis sobre contratos neutros, factories e adapters isolados. O pipeline e seus consumidores não importam SDKs de provider, a política fail-closed precede qualquer acesso remoto, sincronizações produzem contagens exatas e consultas são isoladas por `project_id` e `tenant_id`.

#### Métricas de sucesso

- Os três vector stores e os três providers de embeddings atuais passam nas respectivas suítes de conformidade.
- Uma segunda sincronização sem mudanças registra `inseridos=0`, `mantidos=previstos` e `removidos=0` em backends `append`.
- Nenhum import de SDK de vector store ou classe de embeddings existe fora de `src/providers/`.
- Consultas de dois tenants no mesmo projeto nunca retornam resultados cruzados.
- A suíte Pytest permanece verde; Ruff deve ficar verde quando for configurado pelo BACKLOG-0007.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001** [critical] O LangChain aceita IDs explícitos nos contratos de adição e remoção de documentos, permitindo identidade estável no ChromaDB — Verdict: verified — Confidence: high — Evidence: research/langchain-vectorstore-api.md#ids-fornecidos — Budget: 1/3.
- **R-002** [high] A assinatura exata de `QdrantVectorStore` aplicável ao `qdrant-client==1.10.1` está comprovada pela referência consultada — Verdict: unverifiable — Confidence: low — Evidence: research/langchain-vectorstore-api.md#limite-da-consulta — Budget: 1/3.
- Impacto de R-002: a implementação deve reconfirmar a API antes de codificar; a spec fixa comportamento, não assinatura de construtor.
- **R-003** [high] Integrações dedicadas substituem os imports legados de Qdrant e Hugging Face — Verdict: verified — Confidence: high — Evidence: research/langchain-vectorstore-api.md#integracoes-dedicadas — Budget: 1/3.

#### Fontes e contexto consultados

- `specs/backlog/0003-modularizar-providers-factory-adapter.md`: brief promovido e decisões confirmadas.
- `src/embedder.py`, `src/safety.py`, `pipeline.py`, `search.py`, `chat.py`, `upsert_from_chunks.py`, `demo_rag.py`: fronteira atual e consumidores.
- `tests/test_safety.py`, `tests/test_safety_policy.py`, `tests/test_qdrant_sync.py`: comportamento protegido pela SPEC-0001.
- `specs/completed/0001-bloquear-recriacao-destrutiva/spec.md`: precedente de segurança, espelho e auditabilidade.
- `.specsfy/RULES.md`, `.specsfy/STACK.md`, `.specsfy/DATABASE.md`, `PROJECT.md`: regras e contexto persistente.
- Verificação local: `config.yaml` usa Qdrant; `output/vivo_gold_banda_larga_pf/chroma_db` não existe e nenhum `chroma.sqlite3` do projeto foi encontrado fora da `.venv`.

#### Documentação consultada

- LangChain Python API Reference, estado consultado em 2026-09-01, via Context7; IDs em vector stores e integrações dedicadas.
- `.agents/skills/specsfy-specialist-langchain/references/langgraph-v1.md`; migração local de imports v0 para pacotes dedicados.

#### Artefatos de pesquisa armazenados

- `specs/defined/0003-modularizar-providers-factory-adapter/research/langchain-vectorstore-api.md`: metadados, achados próprios e limite da consulta, sem reprodução de conteúdo externo.

#### Dúvidas respondidas

- **Q**: Quais providers entram? → **A**: Qdrant, ChromaDB e Pinecone; OpenAI, OpenRouter e Hugging Face.
- **Q**: Como calcular contagens em `append`? → **A**: todos os adapters relêem IDs do escopo antes do upsert e produzem contagens exatas.
- **Q**: Como isolar recuperação? → **A**: `project_id` é obrigatório; `tenant_id` é explícito quando aplicável e sua ausência consulta somente registros sem tenant.
- **Q**: Como tratar ChromaDB legado? → **A**: não existe base local a migrar; destinos novos usam `chunk_id`. Legado inesperado bloqueia a escrita e permanece intacto.
- **Q**: O LLM de chat entra? → **A**: não; pertence ao BACKLOG-0010, e `ChatOpenAI` permanece exceção temporária em `chat.py`.

#### Dúvidas abertas

- Nenhuma lacuna de produto aplicável. A assinatura exata das integrações LangChain será verificada tecnicamente antes da implementação, sem mudar os requisitos.

### 3. Escopo e atores

#### Incluído

- Contratos neutros para embeddings e vector stores, com tipos de escopo, registro, resultado, contagem e exceções.
- Factory por nome, validação local por adapter e clientes remotos lazy.
- Adapters para OpenAI, OpenRouter, Hugging Face, Qdrant, ChromaDB e Pinecone.
- Adapter in-memory e fake determinístico de embeddings para conformidade.
- `list_ids(scope)` no núcleo; `delete_ids(ids)` apenas na extensão `mirror`.
- Contagens exatas nos três backends; `mirror` preservado apenas em Qdrant.
- ChromaDB novo com IDs `chunk_id` e bloqueio de legado incompatível.
- Recuperação escopada em `search.py`, `chat.py` e `demo_rag.py`.
- Migração dos cinco consumidores e remoção de `src/embedder.py` sem shim.
- Migração para `langchain-huggingface`, substituindo `langchain_community.embeddings.HuggingFaceEmbeddings`.
- Substituição do import legado `langchain_community.vectorstores.Qdrant`. O acesso ao Qdrant permanece pelo SDK `qdrant-client`, sem adotar `langchain-qdrant` (ver DEC-011).
- Suíte de conformidade e teste estático de dependências.

#### Fora de escopo

- `mirror` e remoção de obsoletos em ChromaDB/Pinecone (BACKLOG-0009).
- Provider plugável de LLM e remoção de `ChatOpenAI` de `chat.py` (BACKLOG-0010).
- Migração, limpeza ou exclusão de ChromaDB legado.
- Novo adapter real, inclusive Postgres/pgvector.
- Mudanças no schema de `config.yaml` ou nos metadados de chunks.
- Hardcodes de cliente (BACKLOG-0004), CI/Ruff (BACKLOG-0007) e escopo do projeto-mãe.

#### Atores

- **Mantenedor do componente**: adiciona, troca e testa providers sem alterar o pipeline.
- **Operador do CLI**: sincroniza e consulta uma base com escopo explícito e recebe erros seguros e contagens auditáveis.
- **Equipe do `rag-pipeline`**: integra o componente por contratos estáveis sem absorver SDKs de fornecedores.

### 4. Princípios e restrições do projeto

- **PR-001**: Factory/Adapter cria providers; Strategy representa diferenças de capacidade; dependências apontam para contratos estáveis.
- **PR-002**: `SyncSafetyPolicy` continua central em `src/safety.py` e precede cliente remoto ou mutação.
- **PR-003**: cada sincronização registra modo, escopo e `previstos/inseridos/mantidos/removidos`, sem segredos ou URL de destino.
- **PR-004**: Python 3.12+, uv, LangChain v1+, Pytest e Red-Green-Refactor permanecem a base.
- **PR-005**: providers são plugins; o pipeline e consumidores não conhecem SDK, collection, point, payload, namespace, scroll ou index.
- **PR-006**: não há interface web nem autenticação neste componente; `tenant_id` é somente escopo lógico explícito.
- **PR-007**: nenhuma operação migra, limpa, recria ou apaga ChromaDB legado nesta fatia.

### 5. Histórias de usuário

#### US-001 — Trocar providers sem alterar o pipeline (P1)

Como mantenedor, quero providers de embeddings e vector stores atrás de contratos e factories, para adicionar ou trocar fornecedor sem modificar o pipeline e seus consumidores.

**Por que P1**: é a fronteira arquitetural que desbloqueia a evolução do componente e os backlogs 0009/0010.
**Teste independente**: executar conformidade com adapters in-memory/fakes e verificar estaticamente os imports.
**Requisitos**: FR-001, FR-002, FR-003, FR-008, NFR-003, NFR-004.

#### US-002 — Sincronizar com segurança e contagens exatas (P1)

Como operador, quero sincronização fail-closed e auditável em qualquer backend suportado, para reexecutar o pipeline sem duplicação silenciosa, remoção indevida ou contagens enganosas.

**Por que P1**: altera caminho crítico de mutação remota protegido pela SPEC-0001.
**Teste independente**: executar primeira sincronização, reexecução e falhas com clientes falsos dos três backends.
**Requisitos**: FR-002, FR-004, FR-005, FR-006, FR-008, NFR-001, NFR-002, NFR-004.

#### US-003 — Recuperar somente o escopo autorizado (P1)

Como operador, quero informar projeto e tenant nas consultas, para que resultados de outro escopo lógico nunca apareçam na recuperação.

**Por que P1**: evita cruzamento de dados entre tenants que compartilham um projeto.
**Teste independente**: consultar fixtures de dois tenants e do escopo sem tenant em cada adapter.
**Requisitos**: FR-006, FR-007, FR-008, NFR-001, NFR-003, NFR-004.

### 6. Cenários BDD de aceite

#### AC-001 — Factory e adapters substituíveis

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-003, NFR-004

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-003 @NFR-004 @AC-001
Feature: Providers plugáveis

  Scenario: Criar cada provider suportado pela mesma factory
    Given configurações locais válidas para os seis providers suportados
    When a factory recebe o nome de cada provider
    Then devolve um adapter que satisfaz o contrato da sua família
    And nenhum consumidor conhece o SDK concreto
```

#### AC-002 — Erros locais antes de acesso remoto

**Cobre**: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-003

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @NFR-001 @NFR-003 @AC-002
Feature: Validação local de providers

  Scenario: Provider, configuração ou credencial inválida
    Given nome desconhecido, configuração incompleta ou credencial obrigatória ausente
    When o provider é solicitado
    Then ocorre UnknownProviderError, InvalidProviderConfigError ou MissingCredentialError
    And nenhum cliente remoto é criado
```

#### AC-003 — Corte limpo e imports confinados

**Cobre**: US-001, FR-001, FR-003, FR-007, NFR-003, NFR-004

```gherkin
@US-001 @FR-001 @FR-003 @FR-007 @NFR-003 @NFR-004 @AC-003
Feature: Boundary estável de providers

  Scenario: Consumidores usam somente contratos
    Given a modularização concluída
    When o repositório é inspecionado estaticamente
    Then src/embedder.py e seus imports não existem
    And SDKs de vector store e classes de embeddings aparecem somente em src/providers
    And ChatOpenAI em chat.py permanece a única exceção rastreada pelo BACKLOG-0010
```

#### AC-004 — Conformidade do núcleo

**Cobre**: US-001, US-002, FR-001, FR-002, FR-003, FR-008, NFR-003, NFR-004

```gherkin
@US-001 @US-002 @FR-001 @FR-002 @FR-003 @FR-008 @NFR-003 @NFR-004 @AC-004
Feature: Contrato comum verificável

  Scenario: Todos os vector stores passam pelo núcleo completo
    Given adapters Qdrant, ChromaDB, Pinecone e in-memory com dependências falsas
    When a suíte de conformidade executa ensure_ready, list_ids, upsert e query
    Then nenhuma asserção do núcleo é pulada
    And somente Qdrant e in-memory executam a extensão mirror
```

#### AC-005 — Qdrant preserva espelho e contagens

**Cobre**: US-002, FR-004, FR-006, FR-008, NFR-001, NFR-002, NFR-004

```gherkin
@US-002 @FR-004 @FR-006 @FR-008 @NFR-001 @NFR-002 @NFR-004 @AC-005
Feature: Sincronização Qdrant preservada

  Scenario: Espelho confirma antes de remover obsoletos
    Given um escopo Qdrant válido com pontos esperados e obsoletos
    When uma sincronização mirror conclui todos os upserts e relê o escopo
    Then remove somente os IDs obsoletos após confirmar todos os esperados
    And registra as quatro contagens exatas
```

#### AC-006 — Reexecução append com contagens exatas

**Cobre**: US-002, FR-004, FR-005, FR-008, NFR-002, NFR-004

```gherkin
@US-002 @FR-004 @FR-005 @FR-008 @NFR-002 @NFR-004 @AC-006
Feature: Append auditável

  Scenario: Reexecutar entrada inalterada em ChromaDB ou Pinecone
    Given uma entrada já sincronizada com IDs estáveis
    When o operador repete a sincronização em append
    Then inseridos é 0
    And mantidos é igual a previstos
    And removidos é 0
```

#### AC-007 — Fail-closed uniforme

**Cobre**: US-002, FR-002, FR-004, FR-006, FR-008, NFR-001, NFR-002

```gherkin
@US-002 @FR-002 @FR-004 @FR-006 @FR-008 @NFR-001 @NFR-002 @AC-007
Feature: Guardas antes do provider

  Scenario: Escopo ou modo de sincronização inválido
    Given qualquer um dos três backends e um lote vazio, divergente ou duplicado
    When a sincronização é iniciada
    Then SyncSafetyPolicy encerra a execução com erro específico
    And nenhum cliente remoto ou mutação é observado
```

#### AC-008 — ChromaDB novo não duplica

**Cobre**: US-002, FR-004, FR-005, FR-008, NFR-002, NFR-004

```gherkin
@US-002 @FR-004 @FR-005 @FR-008 @NFR-002 @NFR-004 @AC-008
Feature: Identidade estável no ChromaDB

  Scenario: Duas execuções em destino novo
    Given um destino ChromaDB vazio
    When a mesma entrada é sincronizada duas vezes
    Then cada registro usa chunk_id como identidade
    And o volume não aumenta na segunda execução
```

#### AC-009 — Legado ou releitura não confiável bloqueia

**Cobre**: US-002, FR-004, FR-005, FR-006, FR-008, NFR-001, NFR-002, NFR-004

```gherkin
@US-002 @FR-004 @FR-005 @FR-006 @FR-008 @NFR-001 @NFR-002 @NFR-004 @AC-009
Feature: Contagens e legado fail-closed

  Scenario: IDs legados ou releitura incompleta
    Given ChromaDB com IDs incompatíveis ou provider incapaz de completar list_ids do escopo
    When uma sincronização é solicitada
    Then a execução bloqueia antes do upsert
    And não publica contagens aproximadas
    And orienta um destino ChromaDB novo quando houver legado
```

#### AC-010 — Consulta isolada por tenant

**Cobre**: US-003, FR-006, FR-007, FR-008, NFR-001, NFR-003, NFR-004

```gherkin
@US-003 @FR-006 @FR-007 @FR-008 @NFR-001 @NFR-003 @NFR-004 @AC-010
Feature: Recuperação escopada

  Scenario: Dois tenants compartilham o mesmo projeto
    Given registros dos tenants A e B sob o mesmo project_id
    When o consumidor consulta com tenant_id A
    Then somente resultados do tenant A são retornados
    And o consumidor não constrói filtro específico de SDK
```

#### AC-011 — Ausência de tenant é escopo estrito

**Cobre**: US-003, FR-006, FR-007, FR-008, NFR-001, NFR-003, NFR-004

```gherkin
@US-003 @FR-006 @FR-007 @FR-008 @NFR-001 @NFR-003 @NFR-004 @AC-011
Feature: Recuperação sem tenant

  Scenario: Projeto contém registros tenantizados e sem tenant
    Given registros com e sem tenant_id no mesmo project_id
    When o consumidor consulta sem tenant_id
    Then somente registros sem tenant são retornados
    And omitir tenant_id não equivale a omitir o filtro
```

#### AC-012 — Consulta sem projeto falha localmente

**Cobre**: US-003, FR-002, FR-006, FR-007, FR-008, NFR-001, NFR-003, NFR-004

```gherkin
@US-003 @FR-002 @FR-006 @FR-007 @FR-008 @NFR-001 @NFR-003 @NFR-004 @AC-012
Feature: Validação do escopo de recuperação

  Scenario: project_id ausente ou vazio
    Given uma consulta sem project_id válido
    When search.py, chat.py ou demo_rag.py tenta recuperar resultados
    Then a execução termina com erro de escopo
    And nenhum cliente remoto ou consulta é observado
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve definir contratos neutros de fornecedor para embeddings e vector stores, incluindo `LogicalScope`, registros, resultados, contagens e exceções, sem tipos exclusivos de SDK.
- **FR-002**: A factory deve despachar somente pelo nome; cada adapter deve validar configuração/credenciais localmente e adiar qualquer cliente remoto até após a validação do escopo.
- **FR-003**: Os seis providers atuais devem existir em módulos isolados sob `src/providers/`; o pipeline e consumidores dependem somente dos contratos.
- **FR-004**: Cada vector store deve implementar `ensure_ready`, `list_ids(scope)`, `upsert` e `query`; somente Qdrant e in-memory implementam `delete_ids`/`mirror` nesta fatia.
- **FR-005**: Destino ChromaDB novo deve usar `chunk_id`; IDs legados incompatíveis devem bloquear antes do upsert e permanecer inalterados.
- **FR-006**: Sincronização e recuperação devem validar `project_id`/`tenant_id` e modos antes de qualquer acesso remoto; a `SyncSafetyPolicy` central deve preservar as garantias da SPEC-0001.
- **FR-007**: `pipeline.py`, `upsert_from_chunks.py`, `search.py`, `chat.py` e `demo_rag.py` devem usar factories/adapters; consultas exigem `project_id` e aceitam `tenant_id` explícito, cuja ausência alcança somente registros sem tenant.
- **FR-008**: A suíte deve testar o núcleo em todos os adapters, `mirror` nos adapters capazes, contagens exatas, fail-closed, isolamento de consulta, determinismo de embeddings e confinamento de imports.

#### Não funcionais

- **NFR-001**: Nenhum escopo inválido, modo incompatível, legado ChromaDB ou credencial/configuração inválida pode provocar acesso ou mutação remota. **Verificação**: Pytest com clientes falsos e listas de chamadas vazias.
- **NFR-002**: Cada sincronização concluída deve registrar modo, escopo e contagens numéricas exatas de previstos, inseridos, mantidos e removidos, sem credenciais, tokens ou URL. **Verificação**: Pytest com `caplog` na primeira execução e reexecução dos três backends.
- **NFR-003**: Imports de SDK de vector store e classes de embeddings devem ficar confinados a `src/providers/`; `ChatOpenAI` em `chat.py` é a única exceção temporária. **Verificação**: teste estático sobre AST/imports.
- **NFR-004**: A mudança deve preservar batch size, paginação completa de escopo, dimensões/distância/payload, resultados de recuperação e comportamento Qdrant/Pinecone observados. **Verificação**: caracterização e conformidade Pytest; Pytest completo verde e Ruff verde quando disponível.

#### Erros e casos-limite

- Provider desconhecido → `UnknownProviderError`, sem ler segredo ou acessar rede.
- Configuração incompleta → `InvalidProviderConfigError`; credencial obrigatória ausente → `MissingCredentialError`.
- `project_id`/`chunk_id` ausente, lote vazio/duplicado/divergente ou mistura de tenants → erro de escopo antes do cliente.
- `mirror` fora de Qdrant/in-memory → `UnsupportedSyncModeError`.
- Confirmação incompleta antes de remoção → `UnsafeRemovalError`.
- `list_ids` incompleto, não paginado ou não isolável → sincronização bloqueada e nenhuma contagem aproximada.
- ChromaDB legado → bloqueio antes do upsert e orientação para destino vazio.
- Dimensão Pinecone divergente → erro em `ensure_ready`, depois de validações locais/de escopo e antes do upsert.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Python 3.12+ com uv, LangChain 1.2+, Pytest; Qdrant, ChromaDB e Pinecone.
- `src/embedder.py` concentra factories, clientes, sincronização e leitura.
- `src/safety.py` já contém `SyncSafetyPolicy`; Qdrant usa escopo paginado e espelho.
- `qdrant-client==1.10.1` exige preservar seleção de porta HTTP/HTTPS do helper atual.
- Não há framework de interface nem banco relacional próprio.

#### Arquitetura e módulos

- `src/providers/contracts.py`: Protocols e value objects neutros (`LogicalScope`, `VectorRecord`, `SearchResult`, `SyncCounts`, contratos de embeddings/vector store).
- `src/providers/errors.py`: `ProviderError`, `UnknownProviderError`, `InvalidProviderConfigError`, `MissingCredentialError` e erros do provider quando necessários.
- `src/providers/factory.py`: registro e despacho por nome, sem ler segredos nem criar cliente remoto.
- `src/providers/embeddings/*`: adapters OpenAI, OpenRouter, Hugging Face e fake; métodos determinísticos no fake.
- `src/providers/vectorstores/base.py`: orquestração comum de sync, cálculo exato de conjuntos e emissão de `SyncCounts`; chama `SyncSafetyPolicy` antes de `ensure_ready`.
- `src/providers/vectorstores/qdrant.py`: preserva cliente, paginação, filtros, payload, dimensão, distância e mirror.
- `src/providers/vectorstores/chroma.py`: IDs `chunk_id` em destinos novos, detecção de legado e ausência estrita de tenant.
- `src/providers/vectorstores/pinecone.py`: preserva ID estável atual, namespace, dimensão e append.
- `src/providers/vectorstores/in_memory.py`: referência completa, sem SDK, para núcleo e mirror.
- Clientes remotos são lazy: construtor/validação local não acessa rede; `ensure_ready` e `query` recebem escopo já validado.
- Consumidores convertem entrada/saída na fronteira da aplicação; não constroem filtros de SDK.

#### Migrations

- Não aplicável a schema. `pyproject.toml`/`uv.lock` recebem `langchain-huggingface`.
- Não há migração ChromaDB. Destino legado é preservado e bloqueado; o operador escolhe outro `collection_name` ou `persist_directory` vazio usando a configuração existente.

#### Models

- `LogicalScope`: `project_id` obrigatório e `tenant_id` opcional; `None` significa somente registros sem tenant.
- `VectorRecord`: ID lógico, conteúdo, vetor e metadados independentes de SDK.
- `SearchResult`: conteúdo, metadados e score normalizados.
- `SyncCounts`: previstos, inseridos, mantidos e removidos; inteiros não negativos e coerentes com os conjuntos observados.

#### Controllers e casos de uso

- `pipeline.py` e `upsert_from_chunks.py`: carregam configuração/chunks e chamam o serviço de sincronização por contratos.
- `search.py`, `chat.py`, `demo_rag.py`: criam `LogicalScope`, geram embedding de consulta e chamam `query`; `tenant_id` é entrada explícita opcional.
- `chat.py` mantém a cadeia LCEL e `ChatOpenAI`; a adaptação da recuperação não introduz agente ou LangGraph.

#### Views e experiência

- Não aplicável. A experiência é CLI: sucesso com contagens/resultados e falha com mensagem específica e código diferente de zero.

#### Queries e repositórios

- `list_ids(scope)` pagina até exaustão e nunca omite o filtro de ausência de tenant.
- `query(embedding, k, scope)` aplica o mesmo escopo lógico e retorna `SearchResult` neutro.
- Falha de paginação/filtro bloqueia o fluxo; não há fallback sem escopo.

#### Jobs e processamento assíncrono

- Não aplicável; o processamento permanece síncrono em lote.

#### Estrutura de arquivos

```text
src/providers/
  __init__.py
  contracts.py
  errors.py
  factory.py
  embeddings/
    __init__.py
    base.py
    openai.py
    openrouter.py
    huggingface.py
    fake.py
  vectorstores/
    __init__.py
    base.py
    qdrant.py
    chroma.py
    pinecone.py
    in_memory.py
tests/
  test_provider_factory.py
  test_embedding_conformance.py
  test_vectorstore_conformance.py
  test_provider_boundaries.py
  test_safety.py
  test_qdrant_sync.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `LogicalScope` | `project_id` + presença/valor de `tenant_id` | projeto obrigatório; tenant ausente é escopo próprio | Filtra IDs, sync e query |
| `VectorRecord` | ID lógico do adapter | conteúdo, vetor e metadados; ID não vazio | Pertence a um escopo |
| `SyncCounts` | execução | quatro inteiros exatos e não negativos | Derivado dos conjuntos esperado/existente/final |
| `ProviderCapabilities` | nome do adapter | núcleo obrigatório; `mirror` somente quando implementado | Orienta a Strategy sem métodos falsos |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Sincronização | Validada localmente | Escopo válido | Destino pronto | Nenhum cliente antes do escopo |
| Sincronização append | IDs existentes lidos | Upsert de ausentes/esperados | Concluída | `removidos=0`; contagens exatas |
| Sincronização mirror | Esperados upsertados | Confirmação completa | Obsoletos removidos | Somente Qdrant/in-memory |
| ChromaDB | Legado incompatível | Solicitar sync | Bloqueada | Nenhuma mutação; destino preservado |
| Consulta | Escopo validado | Query | Resultados escopados | Sem cruzamento de projeto/tenant |

#### Migração e retenção

- Não há nova persistência do domínio. Formatos de chunks, manifesto, payload e retenção permanecem os documentados em `.specsfy/DATABASE.md`.
- Bases ChromaDB legadas não são alteradas nem removidas.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. A entrega altera módulos Python e CLIs existentes, sem tela, formulário ou navegação visual.

#### Stack e convenções de interface

- CLI Python existente; mensagens em português e códigos de saída preservados. `INTERFACE.md` confirma ausência de frontend.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- O operador executa pipeline, busca ou chat pelo terminal; configuração e argumentos formam o escopo e o resultado volta no mesmo terminal.

#### Menus e navegação principal

- Não aplicável; os CLIs são acessados diretamente por comando.

#### Formulários e ações

- Não aplicável; entradas são argumentos CLI e `config.yaml` existente.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

- Não aplicável; não existe React neste repositório.

#### Estados e acessibilidade

- Estados do terminal: validação, progresso em lote, sucesso com contagens, ausência de resultados e erro recuperável. Mensagens não dependem apenas de cor ou emoji.

#### Contrato CRUD

- Não aplicável.

#### Revisão visual durante o desenvolvimento

- Não aplicável; cada tarefa futura deve registrar `VISUAL: Não aplicável — mudança sem superfície gráfica`.

#### APIs expostas

- `EmbeddingAdapter.embed_documents(texts)` e `embed_query(text)` retornam vetores.
- `VectorStoreAdapter.ensure_ready`, `list_ids`, `upsert`, `query` e `capabilities` usam tipos neutros.
- `MirrorCapableVectorStore.delete_ids` existe somente nos adapters capazes.
- `ProviderFactory` recebe nome e settings locais; não aceita segredos como critério de despacho.

#### APIs externas utilizadas

- OpenAI/OpenRouter para embeddings; Hugging Face local; Qdrant, Pinecone e ChromaDB por integrações dedicadas. Baseline local: `langchain==1.2.18`, `langchain-openai==1.2.1`, `langchain-chroma==1.1.0`, `langchain-pinecone==0.2.13` e `qdrant-client==1.10.1`; `langchain-qdrant`/`langchain-huggingface` serão resolvidos por uv e conferidos antes da implementação.
- Autenticação permanece por variáveis de ambiente. Timeout/retry não muda nesta fatia; falhas do SDK são propagadas sem revelar segredo.

#### Documentação das APIs consultadas

- LangChain Python API Reference, 2026-09-01; evidência em `research/langchain-vectorstore-api.md`.
- A implementação deve confirmar símbolos/assinaturas de `langchain-huggingface` na referência canônica antes de codificar. A assinatura de `langchain-qdrant` permaneceu não comprovada (R-002) e a DEC-011 resolveu manter `qdrant-client`.

#### Eventos e outros contratos

- O log final de sincronização é contrato observável: modo, escopo e quatro contagens; sem segredo ou URL.
- `config.yaml` e metadados de chunks permanecem compatíveis.

### 11. Estratégia TDD

- **Unidade**: factories, validação local, `LogicalScope`, cálculo de `SyncCounts`, detecção Chroma legado e fake de embeddings.
- **Integração/contrato**: núcleo contra todos os adapters com clientes falsos; extensão mirror; isolamento por tenant; imports estáticos.
- **BDD/aceite**: os doze cenários da seção 6 informam casos Pytest próprios; não criar arquivos `.feature`.
- **Runner TDD**: Pytest, já adotado pelo projeto.
- **E2E**: CLIs com dependências falsas para sincronização e recuperação; acesso real externo não é necessário para o gate.
- **Verificação manual**: conferir mensagens dos CLIs e compatibilidade de `config.yaml`; nenhuma revisão visual.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| AC-001 | AC-001 na seção 6 | `tests/test_provider_factory.py` com marcador `SPECSFY: AC-001` | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.providers'` (`uv run pytest tests/test_provider_factory.py`) | GREEN em 2026-09-01: `uv run pytest tests/test_provider_factory.py` → 17 passed (T016–T018) | Pending |
| AC-002 | AC-002 na seção 6 | `tests/test_provider_factory.py` com marcador `SPECSFY: AC-002` | RED em 2026-09-01: 4 casos falham — `ModuleNotFoundError: No module named 'src.providers'` ao importar `errors`/`factory` | GREEN em 2026-09-01: `uv run pytest tests/test_provider_factory.py` → 17 passed; `UnknownProviderError`/`InvalidProviderConfigError`/`MissingCredentialError` são `ProviderError` e ocorrem antes de qualquer cliente | Pending |
| AC-003 | AC-003 na seção 6 | `tests/test_provider_boundaries.py` com marcador `SPECSFY: AC-003` | RED em 2026-09-01: `src/embedder.py` ainda existe e SDKs não estão confinados (`test_embedder_monolitico_foi_removido`, `test_sdks_de_provider_confinados_a_src_providers`) | GREEN em 2026-09-01: `uv run pytest tests/test_provider_boundaries.py` → 4 passed; `src/embedder.py` removido, nenhum módulo o importa, SDKs confinados a `src/providers/` e `ChatOpenAI` em `chat.py` como única exceção | Pending |
| AC-004 | AC-004 na seção 6 | `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-004` | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.providers'` na conformidade de vector store e de embeddings | GREEN em 2026-09-01: `uv run pytest tests/test_vectorstore_conformance.py` → 26 passed; núcleo completo nos 4 backends, nenhuma asserção pulada, mirror só em qdrant/in_memory | Pending |
| AC-005 | AC-005 na seção 6 | `tests/test_qdrant_sync.py` com marcador `SPECSFY: AC-005` | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.providers'` no serviço `synchronize` (mirror confirma esperados + quatro contagens; bloqueio por confirmação incompleta) | GREEN em 2026-09-01: `uv run pytest tests/test_qdrant_sync.py` → 13 passed; contagens `(2,1,1,1)`, remoção só de obsoletos após confirmação e `UnsafeRemovalError` quando a releitura não confirma | Pending |
| AC-006 | AC-006 na seção 6 | `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-006` | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.providers'` na reexecução append (`inseridos=0`, `mantidos=previstos`, `removidos=0`) | GREEN em 2026-09-01: `uv run pytest tests/test_vectorstore_conformance.py -k "chroma or pinecone"` → reexecução append com `inseridos=0`, `mantidos=previstos`, `removidos=0` | Pending |
| AC-007 | AC-007 na seção 6 | `tests/test_safety.py` com marcador `SPECSFY: AC-007` | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.providers'` no fail-closed uniforme dos três backends (lote vazio/duplicado/tenants misturados e mirror fora do Qdrant) | GREEN em 2026-09-01: `uv run pytest tests/test_safety.py -k "escopo_invalido or mirror_fora_do_qdrant"` → 12 passed; `ensure_ready_calls == 0` e `upsert_calls == []` nos 3 backends | Pending |
| AC-008 | AC-008 na seção 6 | `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-008` | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.providers'` (ChromaDB novo com `chunk_id`, sem crescimento na segunda execução) | GREEN em 2026-09-01: `uv run pytest tests/test_vectorstore_conformance.py -k chroma` → 8 passed; identidade `chunk_id` e `list_ids` estável na 2ª execução | Pending |
| AC-009 | AC-009 na seção 6 | `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-009` | RED em 2026-09-01: `ModuleNotFoundError` de `src.providers`/`tests._fakes_vectorstore` (legado incompatível e releitura incompleta bloqueiam antes do upsert) | GREEN em 2026-09-01: `LegacyDestinationError` (legado) e `UnreliableScopeReadError` (releitura incompleta) bloqueiam com `upsert_calls == []` | Pending |
| AC-010 | AC-010 na seção 6 | `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-010` | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.providers'` (`query` isola por tenant; assinatura sem `filter`/`where`) | GREEN em 2026-09-01: `query` isola por tenant nos 4 backends e a assinatura é `(scope, embedding, k)`, sem `filter`/`where` | Pending |
| AC-011 | AC-011 na seção 6 | `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-011` | RED em 2026-09-01: `ModuleNotFoundError: No module named 'src.providers'` (`query` sem tenant retorna só registros sem tenant) | GREEN em 2026-09-01: `query` sem tenant devolve só registros sem tenant; `com-tenant` ausente do resultado | Pending |
| AC-012 | AC-012 na seção 6 | `tests/test_safety.py` com marcador `SPECSFY: AC-012` | RED em 2026-09-01: `ModuleNotFoundError` de `src.providers` + `search.py`/`chat.py`/`demo_rag.py` ainda não montam `LogicalScope` antes de recuperar | GREEN em 2026-09-01: `search.py`/`chat.py`/`demo_rag.py` montam `LogicalScope` antes de recuperar; `project_id` vazio/None gera `InvalidScopeError` com `query_calls == []` | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenários BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| US-001 | AC-001, AC-003, AC-004 | Contrato/estático | `pytest tests/test_provider_factory.py tests/test_provider_boundaries.py tests/test_vectorstore_conformance.py` | Passed — `uv run pytest tests/test_provider_factory.py tests/test_provider_boundaries.py tests/test_vectorstore_conformance.py` → 47 passed |
| US-002 | AC-005, AC-006, AC-007, AC-008, AC-009 | Contrato/integração | `pytest tests/test_safety.py tests/test_qdrant_sync.py tests/test_vectorstore_conformance.py` | Passed — `uv run pytest tests/test_safety.py tests/test_qdrant_sync.py tests/test_vectorstore_conformance.py` → 61 passed |
| US-003 | AC-010, AC-011, AC-012 | Contrato/CLI | `pytest tests/test_vectorstore_conformance.py tests/test_safety.py` | Passed — `uv run pytest tests/test_vectorstore_conformance.py tests/test_safety.py` → 49 passed |
| FR-001 | AC-001, AC-002, AC-004 | Unidade/contrato | `tests/test_provider_factory.py`, `tests/test_vectorstore_conformance.py` | Passed — `uv run pytest tests/test_provider_factory.py tests/test_vectorstore_conformance.py` → 43 passed |
| FR-002 | AC-001, AC-002, AC-007, AC-012 | Unidade/segurança | `tests/test_provider_factory.py`, `tests/test_safety.py` | Passed — `uv run pytest tests/test_provider_factory.py tests/test_safety.py` → 40 passed |
| FR-003 | AC-001, AC-002, AC-003, AC-004 | Arquitetura | `tests/test_provider_boundaries.py` | Passed — `uv run pytest tests/test_provider_boundaries.py` → 4 passed (varredura AST, sensibilidade comprovada por sonda) |
| FR-004 | AC-005, AC-006, AC-007, AC-008, AC-009 | Contrato | `tests/test_vectorstore_conformance.py`, `tests/test_qdrant_sync.py` | Passed — `uv run pytest tests/test_vectorstore_conformance.py tests/test_qdrant_sync.py` → 38 passed |
| FR-005 | AC-006, AC-008, AC-009 | Contrato | `tests/test_vectorstore_conformance.py` | Passed — `uv run pytest tests/test_vectorstore_conformance.py` → 26 passed |
| FR-006 | AC-005, AC-007, AC-009, AC-010, AC-011, AC-012 | Segurança/contrato | `tests/test_safety.py`, `tests/test_vectorstore_conformance.py` | Passed — `uv run pytest tests/test_safety.py tests/test_vectorstore_conformance.py` → 49 passed |
| FR-007 | AC-003, AC-010, AC-011, AC-012 | CLI/arquitetura | `tests/test_provider_boundaries.py`, `tests/test_safety.py` | Passed — `uv run pytest tests/test_provider_boundaries.py tests/test_safety.py` → 27 passed |
| FR-008 | AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012 | Regressão | `pytest` | Passed — `uv run pytest` → 141 passed |
| NFR-001 | AC-002, AC-005, AC-007, AC-009, AC-010, AC-011, AC-012 | Segurança | `pytest` com clientes falsos | Passed — `uv run pytest` → 141 passed, com clientes falsos e listas de chamadas vazias (`ensure_ready_calls == 0`, `upsert_calls == []`, `deleted_ids == []`, `query_calls == []`) |
| NFR-002 | AC-005, AC-006, AC-007, AC-008, AC-009 | Observabilidade | `pytest` com `caplog` | Passed — `uv run pytest tests/test_qdrant_sync.py` → 12 passed, com `caplog` provando as quatro contagens e ausência de URL/API key no registro |
| NFR-003 | AC-001, AC-002, AC-003, AC-004, AC-010, AC-011, AC-012 | Arquitetura | teste AST/imports | Passed — `uv run pytest tests/test_provider_boundaries.py` → 4 passed; SDKs confinados a `src/providers/` e `ChatOpenAI` em `chat.py` como única exceção |
| NFR-004 | AC-001, AC-003, AC-004, AC-005, AC-006, AC-008, AC-009, AC-010, AC-011, AC-012 | Compatibilidade | caracterização + `pytest`; Ruff quando configurado | Passed — `uv run pytest tests/test_characterization_providers.py` → 13 passed (caracterização migrada) e `uv run pytest` → 141 passed; Ruff pendente do BACKLOG-0007 |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY — Passed em 2026-09-01
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0003-modularizar-providers-factory-adapter/spec.md`; `node .agents/skills/specsfy-04-validate/scripts/review_findings.mjs specs/defined/0003-modularizar-providers-factory-adapter/spec.md --root .`
- **Achados**: estrutura `VALID DRAFT`; research `PASSED`; reviews `PASSED`; 3 US, 8 FR, 4 NFR e 12 AC. Cada US/FR/NFR possui pelo menos três AC distintos em `**Cobre**`. Nenhum `P1 Open`.
- **FIND-PROD-001** [P2] [Resolved] Contagens `inseridos/mantidos` em backends append estavam semanticamente ambíguas — Refs: FR-004, NFR-002 — Evidence: specs/defined/0003-modularizar-providers-factory-adapter/spec.md:225 — Effect: logs poderiam chamar cada upsert de inserção e aprovar reexecução com números enganosos — Suggestion: resolvido por `list_ids(scope)` no núcleo e AC-006 com contagens exatas.
- **FIND-ARCH-001** [P1] [Resolved] O contrato de recuperação poderia interpretar `tenant_id` ausente como ausência de filtro — Refs: FR-006, FR-007, NFR-001 — Evidence: specs/defined/0003-modularizar-providers-factory-adapter/spec.md:302 — Effect: consulta cruzaria tenants do mesmo projeto — Suggestion: resolvido definindo ausência como escopo exclusivo sem tenant e cobrindo AC-011.
- **FIND-SEC-001** [P1] [Resolved] A primeira escrita estável em ChromaDB legado poderia duplicar conteúdo ou incentivar exclusão insegura — Refs: FR-005, FR-006, NFR-001 — Evidence: specs/defined/0003-modularizar-providers-factory-adapter/spec.md:271 — Effect: duplicação silenciosa ou perda de dados — Suggestion: resolvido por detecção e bloqueio anterior ao upsert em AC-009, preservando a base.

#### Gate do Ato II — Plano

- **Resultado**: Pending — reaberto em 2026-09-01 pela DEC-011 (mudança somente de solução). Aprovação anterior:
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0003-modularizar-providers-factory-adapter/spec.md --allow-draft` → `VALID DRAFT`; `uv run pytest -q` → 67 failed / 75 passed (RED SPEC-0003 + SPEC-0001 intacta)
- **Achados** (reconciliação DEC-011): 38 tarefas (13 `[TEST][TDD]`, 19 `[CODE]`, 4 `[DOC]`, 2 `[OPS]`); T037 e T038 acrescentadas para remover a dependência descartada e corrigir o inventário, ambas sem predecessor TDD por não alterarem comportamento. Achados da aprovação original: 36 tarefas (13 `[TEST][TDD]`, 19 `[CODE]`, 3 `[DOC]`, 1 `[OPS]`), 27/27 IDs cobertos, cada AC com tarefa TDD distinta e ≥3 casos TDD por feature/US/FR/NFR. Os 13 predecessores TDD (T003–T015) estão concluídos com RED registrado na seção 11. `check_traceability.mjs` reporta 27/27 IDs cobertos; os `MARCADORES ÓRFÃOS` reportados pertencem às specs 0001 e 0002, que compartilham arquivos de teste com esta fatia, e não são lacuna dela. Validador estrito sem `--allow-draft`: `READY`.

#### Gate do Ato III — Entrega

- **Resultado**: Passed em 2026-09-01
- **Comando**: `uv run pytest` → 141 passed; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0003-modularizar-providers-factory-adapter/spec.md . --full-chain`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/in-progress/0003-modularizar-providers-factory-adapter/spec.md .` → `QA: PASSED`; `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0003-modularizar-providers-factory-adapter/spec.md` → `READY`; `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`
- **Achados** (fechamento após a reconciliação da DEC-011): 38/38 tarefas concluídas com 228/228 itens de checklist; `verify_evidence.mjs` sem filtro → `PASSED (strict)` para as 19 tarefas `[CODE]`. Nenhuma tarefa aberta, nenhum teste pulado ou marcado como falha esperada, nenhum placeholder em produção. Achados da conferência anterior: 36/36 tarefas concluídas com 216/216 itens de checklist. Suíte completa verde (141 passed, nenhum skip ou xfail). Rastreabilidade 27/27 com `uncovered: []`, `broken_chains: []` e `insufficient_cases: {}`; 89 casos de feature. Aceite `QA: PASSED` com os 15 requisitos da seção 12 marcados `Passed` e comando registrado. Os `MARCADORES ÓRFÃOS` reportados pertencem à SPEC-0001 (três critérios de aceite, 28/28 coberta) e à SPEC-0002 (os demais critérios e as duas histórias dela, 41/41 coberta); é artefato de arquivos de teste compartilhados, não lacuna desta fatia. Ruff continua pendente do BACKLOG-0007.
- **FIND-DEL-001** [P2] [Resolved] `langchain-qdrant` foi adicionado como dependência em T001, mas nenhum módulo o importa — Refs: FR-003, NFR-004 — Evidence: `grep -rn "langchain_qdrant" src/ tests/ *.py` retorna apenas a lista de módulos proibidos do teste de fronteira — Effect: a seção 3 declara "Migração para `langchain-huggingface` e `langchain-qdrant`" e a DEC-009 previa integrações dedicadas nas duas famílias; a metade Qdrant não foi entregue, deixando uma dependência instalada e sem uso — Suggestion: decidir entre (a) migrar `src/providers/vectorstores/qdrant.py` para `langchain-qdrant` após confirmar a assinatura pendente do R-002, ou (b) manter `qdrant-client` direto e ajustar escopo e DEC-009 por `$specsfy-update-spec`, removendo a dependência não usada. Resolvido em 2026-09-01 pela opção (b): a DEC-011 registrou a decisão, T037 removeu a dependência e T038 corrigiu o inventário.

### 14. Tarefas

Formato:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Checklist obrigatório por tarefa, na ordem `PREP`, `EXECUTE`, `VERIFY`,
`VISUAL`, `EVIDENCE`, `IMPROVE`. Toda tarefa sem superfície gráfica registra
`VISUAL: Não aplicável — mudança sem superfície gráfica`.

#### Fase 0 — Setup mínimo

- [x] T001 [OPS] Adicionar a integração dedicada de embeddings em `./pyproject.toml` com `uv add` e resolver `./uv.lock` sem alterar outras versões — Refs: FR-003, NFR-004 — Depends: none
  - [x] **PREP**: Conferido baseline de `./pyproject.toml` (sem `langchain-qdrant`/`langchain-huggingface`) e as versões da seção 10 (`langchain==1.2.18`, `qdrant-client==1.10.1`).
  - [x] **EXECUTE**: `uv add langchain-qdrant langchain-huggingface` → `Resolved 135 packages`, `Installed 2 packages`. Diff de `pyproject.toml` acrescenta só `langchain-huggingface>=1.2.2` e `langchain-qdrant>=1.0.0`; demais restrições inalteradas.
  - [x] **VERIFY**: `uv sync` → `Checked 132 packages`, sem conflito; `uv run python -c "import langchain_qdrant, langchain_huggingface"` → exit 0.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: `uv add langchain-qdrant langchain-huggingface` → `+ langchain-huggingface==1.2.2`, `+ langchain-qdrant==1.0.0`; `git diff pyproject.toml` = +2 linhas; `uv.lock` re-resolvido (135 pacotes).
  - [x] **IMPROVE**: Nenhuma além do escopo; confirmado que `qdrant-client` permanece `==1.10.1`, sem bump transitivo forçado pela integração dedicada.
  - **Reconciliado pela DEC-011 (2026-09-01)**: a evidência acima é histórica e permanece verdadeira — as duas dependências foram de fato adicionadas nesta tarefa. A integração dedicada do Qdrant foi depois descartada e sua remoção é entregue por T037; apenas `langchain-huggingface` permanece no escopo desta tarefa.

- [x] T002 [DOC] Atualizar `.specsfy/STACK.md` e `.specsfy/PACKAGES.md` com as integrações dedicadas e versões resolvidas — Refs: NFR-004 — Depends: T001
  - [x] **PREP**: Lidos os blocos `specsfy:stack:*` de `.specsfy/STACK.md`, `.specsfy/PACKAGES.md` (vazio por desenho, aponta `docs/packages.md`) e o inventário Python de `docs/packages.md`.
  - [x] **EXECUTE**: `.specsfy/STACK.md`: linha Qdrant agora cita `langchain-qdrant 1.0.0`, nova linha para `langchain-huggingface 1.2.2`, e nota humana sobre a substituição dos imports legados. `docs/packages.md`: linhas de Vetores/Embeddings atualizadas com as duas integrações dedicadas. Texto humano preservado.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `Context monitor: CURRENT` (exit 0).
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Monitor `CURRENT`; `.specsfy/STACK.md` +2 linhas de inventário e +1 bullet humano; `docs/packages.md` +2 linhas na tabela de dependências diretas.
  - [x] **IMPROVE**: Registrada a pendência técnica (reconfirmar assinatura de `QdrantVectorStore` para `qdrant-client==1.10.1`) na nota humana de `STACK.md`, para T024 não re-descobrir o risco R-002.
  - **Reconciliado pela DEC-011 (2026-09-01)**: o registro acima é histórico. A correção das linhas que ainda citam a integração dedicada do Qdrant em `.specsfy/STACK.md` e `docs/packages.md` é entregue por T038.

#### Fase 1 — Caracterização do comportamento atual

- [x] T003 [TEST] Caracterizar `src/embedder.py` e os cinco consumidores em `tests/test_characterization_providers.py` com dependências falsas — Refs: FR-007, NFR-004 — Depends: none
  - [x] **PREP**: Mapeados entradas, saídas e efeitos observáveis de `pipeline.py`, `upsert_from_chunks.py`, `search.py`, `chat.py` e `demo_rag.py`; `demo_rag.py`/`chat.py` têm efeitos no import, então a fronteira deles é caracterizada pela fonte.
  - [x] **EXECUTE**: Escritos 13 casos: despacho e erros locais de `get_embeddings`/`get_vector_store`, sincronização Qdrant mirror com as quatro contagens, `batch_size`, guardas fail-closed (lote vazio, `chunk_id` duplicado, tenants misturados, mirror fora do Qdrant) e fronteira dos cinco consumidores; sem acesso remoto real.
  - [x] **VERIFY**: `uv run pytest tests/test_characterization_providers.py -q` → `13 passed in 3.45s` contra o código atual.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: `uv run pytest tests/test_characterization_providers.py -q` → 13 passed; comportamento atual congelado para NFR-004 (dimensões `[0.1,0.2,0.3]`, payload `page_content`+`metadata`, log `previstos/inseridos/mantidos/removidos`, remoção só de obsoletos, escopo inválido antes de cliente/embedding).
  - [x] **IMPROVE**: A verificação de fronteira dos consumidores passou de `import_module` para leitura de fonte após `demo_rag.py` executar o fluxo RAG no import; evita falso vermelho por ambiente sem credenciais.

#### Fase 2 — RED TDD informado pelo BDD

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pytest falhando em `tests/test_provider_factory.py` com marcador `SPECSFY: AC-001` — Refs: US-001, FR-001, FR-002, FR-003, NFR-003, NFR-004, AC-001 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-001 (criar cada provider suportado pela mesma factory, adapter satisfaz o contrato da família, consumidor não conhece o SDK).
  - [x] **EXECUTE**: Escritos casos parametrizados em `tests/test_provider_factory.py` com marcador `SPECSFY: ... AC-001`: `ProviderFactory.create_embedding`/`create_vector_store` por nome para os seis providers + `in_memory`/`fake`, `delete_ids`/`supports_mirror` só em qdrant/in_memory, despacho sem depender de segredo. Sem `.feature`.
  - [x] **VERIFY**: RED válido — `uv run pytest tests/test_provider_factory.py -q` falha com `ModuleNotFoundError: No module named 'src.providers'`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-001): RED em 2026-09-01 por `src.providers` ausente.
  - [x] **IMPROVE**: Removido um caso tautológico da suíte de conformidade; a checagem de "nenhuma operação do núcleo pulada" ficou concentrada no assert `exercised == set(CORE_METHODS)`.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pytest falhando em `tests/test_provider_factory.py` com marcador `SPECSFY: AC-002` — Refs: US-001, FR-001, FR-002, FR-003, NFR-001, NFR-003, AC-002 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-002 (nome desconhecido, config incompleta ou credencial ausente geram `UnknownProviderError`/`InvalidProviderConfigError`/`MissingCredentialError` e nenhum cliente remoto).
  - [x] **EXECUTE**: Escritos 4 casos com marcador `SPECSFY: ... AC-002`: nome desconhecido, config incompleta (Pinecone sem `index_name`), credencial ausente (OpenAI sem `api_key`), erro local antes de cliente (URL Qdrant inválida). Todos assertam `isinstance(erro, ProviderError)`.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError: No module named 'src.providers'` ao importar `src.providers.errors`/`factory`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-002): RED em 2026-09-01.
  - [x] **IMPROVE**: Nenhuma além do ajuste comum a T004; a hierarquia de erros ficou explícita nos asserts para guiar `errors.py`.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pytest falhando em `tests/test_provider_boundaries.py` com marcador `SPECSFY: AC-003` — Refs: US-001, FR-001, FR-003, FR-007, NFR-003, NFR-004, AC-003 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-003 (repositório inspecionado estaticamente: `src/embedder.py` e imports não existem; SDKs e classes de embeddings só em `src/providers`; `ChatOpenAI` em `chat.py` é a única exceção).
  - [x] **EXECUTE**: Escrito `tests/test_provider_boundaries.py` com varredura AST de cada módulo (exclui `.venv`, `tests/`, `src/providers/`): `test_embedder_monolitico_foi_removido`, `test_nenhum_consumidor_importa_embedder`, `test_sdks_de_provider_confinados_a_src_providers`, `test_chatopenai_em_chat_py_e_a_unica_excecao`. Marcador `SPECSFY: ... AC-003`.
  - [x] **VERIFY**: RED válido — `src/embedder.py` ainda existe e `qdrant_client`/`langchain_chroma`/`OpenAIEmbeddings` etc. aparecem fora de `src/providers/`. O guard de `ChatOpenAI` já passa (invariante que deve permanecer verde).
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-003): RED em 2026-09-01.
  - [x] **IMPROVE**: A lista de módulos/símbolos proibidos e a exceção `chat.py::ChatOpenAI` ficaram em constantes no topo do arquivo para revisão fácil.

- [x] T007 [TEST] [TDD] [US-001] Derivar do AC-004 um caso Pytest falhando em `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-004` — Refs: US-001, US-002, FR-001, FR-002, FR-003, FR-008, NFR-003, NFR-004, AC-004 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-004 (todos os vector stores passam pelo núcleo `ensure_ready`/`list_ids`/`upsert`/`query`; nenhuma asserção pulada; só Qdrant e in-memory executam mirror).
  - [x] **EXECUTE**: Escrito `tests/test_vectorstore_conformance.py` parametrizado por `in_memory|qdrant|chroma|pinecone` (núcleo completo com `exercised == set(CORE_METHODS)`, isolamento por escopo, extensão mirror só nos capazes) e `tests/test_embedding_conformance.py` (fake determinístico e dimensão). Marcador `SPECSFY: ... AC-004`. O seam `settings['client']` + `tests/_fakes_vectorstore.py` será materializado no GREEN (T023–T027).
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError: No module named 'src.providers'` (e `tests._fakes_vectorstore` ainda ausente).
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-004): RED em 2026-09-01.
  - [x] **IMPROVE**: Extração do helper `_make_adapter` para um único ponto de construção com cliente falso, reaproveitável pelas fatias AC-006/AC-008..AC-011.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-005 um caso Pytest falhando em `tests/test_qdrant_sync.py` com marcador `SPECSFY: AC-005` — Refs: US-002, FR-004, FR-006, FR-008, NFR-001, NFR-002, NFR-004, AC-005 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-005 e o espelho idempotente protegido pela SPEC-0001 (confirma todos os esperados antes de remover obsoletos; registra as quatro contagens).
  - [x] **EXECUTE**: Adicionada a seção SPEC-0003 em `tests/test_qdrant_sync.py`: `test_espelho_confirma_todos_os_esperados_antes_de_remover_e_registra_quatro_contagens` (contagens `(2,1,1,1)`, remove só `obsoleto`, `confirmed_before_delete`) e `test_espelho_bloqueia_remocao_quando_o_destino_nao_confirma_os_esperados` (`UnsafeRemovalError`, sem delete). Serviço `synchronize(adapter, scope, records, mode="mirror")`.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError: No module named 'src.providers'`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-005): RED em 2026-09-01.
  - [x] **IMPROVE**: A confirmação pré-remoção virou flag observável (`confirmed_before_delete`) no fake, evitando espiar ordem de chamadas internas.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-006 um caso Pytest falhando em `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-006` — Refs: US-002, FR-004, FR-005, FR-008, NFR-002, NFR-004, AC-006 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-006 (entrada já sincronizada com IDs estáveis; repetir append → `inseridos=0`, `mantidos=previstos`, `removidos=0`).
  - [x] **EXECUTE**: `test_reexecucao_append_sem_mudanca_zera_insercoes_e_remocoes` parametrizado por `chroma|pinecone` em `tests/test_vectorstore_conformance.py`, marcador `SPECSFY: ... AC-006`; primeira execução `(3,3,_,0)`, segunda `previstos=3 inseridos=0 mantidos=3 removidos=0`, `list_ids` estável.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError: No module named 'src.providers'` ao importar `synchronize`/`SyncCounts`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-006): RED em 2026-09-01.
  - [x] **IMPROVE**: Reuso de `_make_adapter`/`_record` da fatia AC-004; a asserção usa os quatro campos de `SyncCounts` por nome para fixar o contrato do value object.

- [x] T010 [TEST] [TDD] [US-002] Derivar do AC-007 um caso Pytest falhando em `tests/test_safety.py` com marcador `SPECSFY: AC-007` — Refs: US-002, FR-002, FR-004, FR-006, FR-008, NFR-001, NFR-002, AC-007 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-007 e a `SyncSafetyPolicy` central de `src/safety.py` (qualquer dos três backends + lote vazio/divergente/duplicado → erro específico, nenhum cliente ou mutação).
  - [x] **EXECUTE**: Seção SPEC-0003 em `tests/test_safety.py`: `test_escopo_invalido_encerra_antes_de_qualquer_cliente_remoto` (matriz 3 backends × 3 casos) e `test_modo_mirror_fora_do_qdrant_encerra_antes_do_cliente` (`UnsupportedSyncModeError`), assertando `ensure_ready_calls == 0`, `upsert_calls == []`, `deleted_ids == []`. Marcador `SPECSFY: ... AC-007`.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError: No module named 'src.providers'`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-007): RED em 2026-09-01.
  - [x] **IMPROVE**: O serviço `synchronize` aceita `SyncSafetyError` ou `ProviderError` no caso genérico, deixando o mapeamento fino do erro para a implementação sem afrouxar a guarda "antes do cliente".

- [x] T011 [TEST] [TDD] [US-002] Derivar do AC-008 um caso Pytest falhando em `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-008` — Refs: US-002, FR-004, FR-005, FR-008, NFR-002, NFR-004, AC-008 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-008 (destino ChromaDB vazio; sincronizar a mesma entrada duas vezes; cada registro usa `chunk_id` como identidade; volume não aumenta na segunda execução).
  - [x] **EXECUTE**: `test_chroma_destino_novo_usa_chunk_id_e_nao_cresce_na_segunda_execucao` em `tests/test_vectorstore_conformance.py`, marcador `SPECSFY: ... AC-008`; `list_ids` após 1ª execução `{chunk-a, chunk-b}` e igual após a 2ª.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError: No module named 'src.providers'`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-008): RED em 2026-09-01.
  - [x] **IMPROVE**: A identidade `chunk_id` é verificada por `list_ids` (contrato neutro), não por atributo interno do backend.

- [x] T012 [TEST] [TDD] [US-002] Derivar do AC-009 um caso Pytest falhando em `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-009` — Refs: US-002, FR-004, FR-005, FR-006, FR-008, NFR-001, NFR-002, NFR-004, AC-009 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-009 (ChromaDB com IDs incompatíveis ou provider incapaz de completar `list_ids` → bloqueia antes do upsert; não publica contagens aproximadas; orienta destino novo quando houver legado).
  - [x] **EXECUTE**: `test_chroma_com_ids_legados_incompativeis_bloqueia_antes_do_upsert` (`LegacyDestinationError`, mensagem cita "destino", sem upsert) e `test_releitura_incompleta_do_escopo_bloqueia_sem_contagem_aproximada` (`UnreliableScopeReadError`, sem upsert). Marcador `SPECSFY: ... AC-009`.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError` de `src.providers` / `tests._fakes_vectorstore`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-009): RED em 2026-09-01.
  - [x] **IMPROVE**: Dois erros distintos (`LegacyDestinationError` vs `UnreliableScopeReadError`) separam legado incompatível de releitura incompleta, orientando mensagens diferentes na implementação.

- [x] T013 [TEST] [TDD] [US-003] Derivar do AC-010 um caso Pytest falhando em `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-010` — Refs: US-003, FR-006, FR-007, FR-008, NFR-001, NFR-003, NFR-004, AC-010 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-010 (registros dos tenants A e B sob o mesmo `project_id`; consulta com `tenant_id` A retorna só A; consumidor não constrói filtro de SDK).
  - [x] **EXECUTE**: `test_query_retorna_somente_o_tenant_solicitado` parametrizado pelos quatro backends + `test_query_aceita_apenas_escopo_logico_sem_filtro_de_sdk` (assinatura `query` ⊆ `{scope, embedding, k}`, sem `filter`/`where`). Marcador `SPECSFY: ... AC-010`.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError: No module named 'src.providers'`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-010): RED em 2026-09-01.
  - [x] **IMPROVE**: A ausência de filtro de SDK é provada pela introspecção da assinatura, tornando o requisito verificável sem depender do backend real.

- [x] T014 [TEST] [TDD] [US-003] Derivar do AC-011 um caso Pytest falhando em `tests/test_vectorstore_conformance.py` com marcador `SPECSFY: AC-011` — Refs: US-003, FR-006, FR-007, FR-008, NFR-001, NFR-003, NFR-004, AC-011 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-011 (registros com e sem `tenant_id` no mesmo `project_id`; consulta sem `tenant_id` retorna só os sem tenant; omitir `tenant_id` ≠ omitir o filtro).
  - [x] **EXECUTE**: `test_query_sem_tenant_alcanca_somente_registros_sem_tenant` parametrizado pelos quatro backends; asserta `ids == {"sem-tenant"}` e `"com-tenant" not in ids`. Marcador `SPECSFY: ... AC-011`.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError: No module named 'src.providers'`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-011): RED em 2026-09-01.
  - [x] **IMPROVE**: A asserção negativa explícita (`"com-tenant" not in ids`) fixa a diferença entre "sem tenant" e "sem filtro" no próprio teste.

- [x] T015 [TEST] [TDD] [US-003] Derivar do AC-012 um caso Pytest falhando em `tests/test_safety.py` com marcador `SPECSFY: AC-012` — Refs: US-003, FR-002, FR-006, FR-007, FR-008, NFR-001, NFR-003, NFR-004, AC-012 — Depends: none
  - [x] **PREP**: Lido o Gherkin do AC-012 (consulta sem `project_id` válido → erro de escopo; nenhum cliente remoto ou consulta observado).
  - [x] **EXECUTE**: Seção SPEC-0003 em `tests/test_safety.py`: `test_recuperacao_sem_project_id_valido_falha_localmente` (`"" | "   " | None` → `InvalidScopeError`), `test_query_nao_e_alcancada_quando_o_escopo_e_invalido` (`backend.query_calls == []`) e `test_consumidores_de_recuperacao_constroem_logical_scope_antes_de_query` (fonte de `search.py`/`chat.py`/`demo_rag.py` menciona `LogicalScope`). Marcador `SPECSFY: ... AC-012`.
  - [x] **VERIFY**: RED válido — `ModuleNotFoundError` de `src.providers` e `AssertionError: search.py não monta escopo lógico antes de recuperar`.
  - [x] **VISUAL**: Não aplicável — tarefa só materializa teste, sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado na seção 11 (linha AC-012): RED em 2026-09-01.
  - [x] **IMPROVE**: Novo erro `InvalidScopeError` (recuperação) separado de `InvalidSyncScopeError` (sincronização) da SPEC-0001, sem sobrepor a política existente.

#### Fase 3 — Fundação: contratos, erros e factory

- [x] T016 [CODE] [US-001] Definir value objects e Protocols neutros em `src/providers/contracts.py` — Refs: US-001, FR-001, NFR-003, NFR-004, AC-001, AC-002, AC-003, AC-004 — Depends: T004, T005, T006, T007
  - [x] **PREP**: Confirmado RED de T004/T005/T006/T007 (`ModuleNotFoundError: No module named 'src.providers'`) e a modelagem da seção 9; `docs/` compatível.
  - [x] **EXECUTE**: `src/providers/contracts.py` com `LogicalScope` (valida `project_id`, normaliza `tenant_id` estrito, `""`/espaços/None → `InvalidScopeError`), `VectorRecord`, `SearchResult`, `SyncCounts` (inteiros não negativos por `__post_init__`), `ProviderCapabilities` e os Protocols `EmbeddingAdapter`/`VectorStoreAdapter`/`MirrorCapableVectorStore`, sem tipos de SDK. `src/providers/__init__.py` reexporta contratos, erros e factory.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_factory.py -q` → `17 passed`; monitor de contexto `CURRENT`.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13; `17 passed` cobre AC-001/AC-002 via contratos + factory.
  - [x] **IMPROVE**: `SyncCounts.__post_init__` rejeita `bool` além de negativos, evitando `previstos=True` passar como inteiro.
  <!-- specsfy:evidence {"task":"T016","refs":["US-001","FR-001","NFR-003","NFR-004","AC-001","AC-002","AC-003","AC-004"],"files":["src/providers/contracts.py","src/providers/__init__.py"],"commands":[{"run":"uv run pytest tests/test_provider_factory.py","exit":0}]} -->

- [x] T017 [CODE] [US-001] Definir a hierarquia de exceções em `src/providers/errors.py` — Refs: US-001, FR-001, FR-002, AC-001, AC-002, AC-007 — Depends: T004, T005, T010
  - [x] **PREP**: Confirmado RED de T004/T005/T010 e os erros listados nas seções 7–8; `docs/` compatível.
  - [x] **EXECUTE**: `src/providers/errors.py` com `ProviderError` base e `UnknownProviderError`, `InvalidProviderConfigError`, `MissingCredentialError`, `InvalidScopeError`, `LegacyDestinationError`, `UnreliableScopeReadError`. `UnsupportedSyncModeError`/`UnsafeRemovalError` reaproveitados de `src/safety.py` (SPEC-0001) sem duplicar.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_factory.py -q` → `17 passed`; casos AC-002 reconhecem `UnknownProviderError`/`InvalidProviderConfigError`/`MissingCredentialError` como `ProviderError`.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13; hierarquia validada por `isinstance(erro, ProviderError)` nos testes.
  - [x] **IMPROVE**: Dois erros distintos para o bloqueio da recuperação (`LegacyDestinationError` vs `UnreliableScopeReadError`) já previstos aqui, evitando retrabalho em T025/T026.
  <!-- specsfy:evidence {"task":"T017","refs":["US-001","FR-001","FR-002","AC-001","AC-002","AC-007"],"files":["src/providers/errors.py"],"commands":[{"run":"uv run pytest tests/test_provider_factory.py","exit":0}]} -->

- [x] T018 [CODE] [US-001] Implementar registro e despacho por nome em `src/providers/factory.py` sem ler segredo nem criar cliente remoto — Refs: US-001, FR-002, FR-003, NFR-001, AC-001, AC-002 — Depends: T016, T017, T004, T005
  - [x] **PREP**: Confirmado RED de T004/T005 e a regra lazy da seção 8; `docs/` compatível.
  - [x] **EXECUTE**: `src/providers/factory.py` com `ProviderFactory.create_embedding`/`create_vector_store`, registros por família e `importlib` lazy; nome desconhecido → `UnknownProviderError`. Escafolados os módulos de adapter (`embeddings/{openai,openrouter,huggingface,fake}.py`, `vectorstores/{qdrant,chroma,pinecone,in_memory}.py`) com validação local (`InvalidProviderConfigError`/`MissingCredentialError`), `capabilities()` correto e cliente adiado; os corpos são completados por T019–T026. Pacotes `embeddings/__init__.py` e `vectorstores/__init__.py` criados.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_factory.py -q` → `17 passed` (despacho, validação local, `mirror` só em qdrant/in_memory, tipos distintos); `uv run pytest -q` → 46 failed / 96 passed (RED restante é T019+; SPEC-0001 intacta); monitor `CURRENT` com `--acknowledge-project-no-change`.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13. Avaliação `PROJECT.md`: sem impacto material nesta fatia — a camada de providers ainda é esqueleto, `src/embedder.py` permanece e as capacidades/limites narrados ("gerar embeddings por providers configuráveis", "extensibilidade por providers") já constam; a revisão narrativa real ocorre no gate final, após T033/T034 removerem o monólito.
  - [x] **IMPROVE**: `_resolve` unificou o despacho das duas famílias com mensagem de erro que lista as opções válidas, em vez de dois blocos `if/elif` duplicados.
  <!-- specsfy:evidence {"task":"T018","refs":["US-001","FR-002","FR-003","NFR-001","AC-001","AC-002"],"files":["src/providers/factory.py","src/providers/embeddings/__init__.py","src/providers/vectorstores/__init__.py"],"commands":[{"run":"uv run pytest tests/test_provider_factory.py","exit":0}]} -->

#### Fase 4 — Adapters de embeddings

- [x] T019 [CODE] [US-001] Implementar `src/providers/embeddings/base.py` e o fake determinístico `src/providers/embeddings/fake.py` — Refs: US-001, FR-001, FR-003, FR-008, AC-004 — Depends: T016, T018, T007
  - [x] **PREP**: Confirmados os contratos de T016 e o determinismo exigido pela seção 11 (`embed_query == embed_documents([text])[0]`, entradas diferentes → vetores diferentes); `docs/` compatível.
  - [x] **EXECUTE**: `src/providers/embeddings/base.py` (`BaseEmbeddingAdapter`: `embed_documents`/`embed_query` derivam de `_embed`). `src/providers/embeddings/fake.py`: `_deterministic_vector` deriva o vetor de SHA-256 (`counter:texto`), honra `dimensions` e nunca acessa rede.
  - [x] **VERIFY**: `uv run pytest tests/test_embedding_conformance.py -q` → `3 passed`; `uv run pytest tests/test_embedding_conformance.py tests/test_provider_factory.py -q` → `20 passed`.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13; determinismo e dimensão do fake comprovados.
  - [x] **IMPROVE**: A expansão do digest por `counter` gera qualquer `dimensions` sem colisão de índice, em vez de fatiar um único hash de 32 bytes.
  <!-- specsfy:evidence {"task":"T019","refs":["US-001","FR-001","FR-003","FR-008","AC-004"],"files":["src/providers/embeddings/base.py","src/providers/embeddings/fake.py","src/providers/embeddings/__init__.py"],"commands":[{"run":"uv run pytest tests/test_embedding_conformance.py","exit":0}]} -->

- [x] T020 [CODE] [US-001] Implementar os adapters `src/providers/embeddings/openai.py` e `src/providers/embeddings/openrouter.py` com validação local e cliente lazy — Refs: US-001, FR-002, FR-003, NFR-003, AC-001, AC-002 — Depends: T018, T019, T004, T005
  - [x] **PREP**: Confirmada a resolução de credencial por `api_key` de config ou variável de ambiente (`OPENAI_API_KEY`/`OPENROUTER_API_KEY`) e o baseline `langchain-openai==1.2.1`; `docs/` compatível.
  - [x] **EXECUTE**: `openai.py`: `OpenAIEmbeddingAdapter(BaseEmbeddingAdapter)` valida credencial no construtor, monta `OpenAIEmbeddings` só no primeiro `embed_*` (`_ensure_client`), repassa `model`/`dimensions`/`base_url`. `openrouter.py`: `OpenRouterEmbeddingAdapter` herda tudo, trocando `_env_var` e `_default_base_url`. Import do SDK confinado a `openai.py`.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_factory.py tests/test_embedding_conformance.py -q` → `20 passed`; `uv run pytest -q` → 43 failed / 99 passed (RED restante é T022+; SPEC-0001 intacta).
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13; construção sem rede confirmada (nenhum cliente até `embed_*`).
  - [x] **IMPROVE**: `OpenRouter` reduzido a duas linhas de configuração por herança, sem duplicar `_build_client`/`_embed`.
  <!-- specsfy:evidence {"task":"T020","refs":["US-001","FR-002","FR-003","NFR-003","AC-001","AC-002"],"files":["src/providers/embeddings/openai.py","src/providers/embeddings/openrouter.py"],"commands":[{"run":"uv run pytest tests/test_provider_factory.py tests/test_embedding_conformance.py","exit":0}]} -->

- [x] T021 [CODE] [US-001] Implementar `src/providers/embeddings/huggingface.py` sobre `langchain-huggingface` com carga local lazy — Refs: US-001, FR-002, FR-003, NFR-003, AC-001, AC-002 — Depends: T001, T018, T019, T004, T005
  - [x] **PREP**: Reconfirmado o símbolo `langchain_huggingface.HuggingFaceEmbeddings(model_name=...)` (pacote `langchain-huggingface==1.2.2` resolvido em T001); `docs/` compatível.
  - [x] **EXECUTE**: `huggingface.py`: `HuggingFaceEmbeddingAdapter(BaseEmbeddingAdapter)` valida o nome do modelo no construtor e carrega `HuggingFaceEmbeddings` só no primeiro `embed_*` (`_ensure_client`); import do SDK confinado à própria rotina. Sem credencial (execução local).
  - [x] **VERIFY**: `uv run pytest tests/test_provider_factory.py tests/test_embedding_conformance.py -q` → `20 passed` (inclui `create_embedding("huggingface", ...)` sem carga de modelo).
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13; versão resolvida `langchain-huggingface==1.2.2`.
  - [x] **IMPROVE**: Import do SDK movido para dentro de `_ensure_client`, garantindo que o teste estático de boundaries (T034) veja o import só em `src/providers/`.
  <!-- specsfy:evidence {"task":"T021","refs":["US-001","FR-002","FR-003","NFR-003","AC-001","AC-002"],"files":["src/providers/embeddings/huggingface.py"],"commands":[{"run":"uv run pytest tests/test_provider_factory.py tests/test_embedding_conformance.py","exit":0}]} -->

#### Fase 5 — Adapters de vector store

- [x] T022 [CODE] [US-002] Implementar `src/providers/vectorstores/base.py` com orquestração de sync, cálculo exato de `SyncCounts` e chamada a `SyncSafetyPolicy` antes de `ensure_ready` — Refs: US-002, FR-004, FR-006, FR-008, NFR-001, NFR-002, AC-004, AC-006, AC-007, AC-009 — Depends: T007, T009, T010, T012, T016
  - [x] **PREP**: Confirmado RED de T007/T009/T010/T012 e as garantias da SPEC-0001 em `src/safety.py` (`assert_sync_mode_supported`, `assert_removal_allowed`); `docs/` compatível.
  - [x] **EXECUTE**: `src/providers/vectorstores/base.py` com o *backend port* (`ensure`/`scope_ids`/`write`/`remove`/`search`), `BaseVectorStoreAdapter`, `MirrorMixin` (`capabilities().supports_mirror` derivado por `isinstance`), `DictVectorBackend` e o serviço `synchronize`: valida modo → valida lote (vazio, id duplicado, tenants divergentes/mistos, tenant ≠ escopo) → `ensure_ready` → `list_ids` → upsert só dos ausentes → em `mirror`, relê e chama `assert_removal_allowed` antes de remover obsoletos → emite `SyncCounts` e log `modo/escopo/previstos/inseridos/mantidos/removidos` sem segredo nem URL. `synchronize` reexportado em `src/providers/__init__.py`. `tests/_fakes_vectorstore.py` materializa o seam `settings['client']`.
  - [x] **VERIFY**: `uv run pytest tests/test_safety.py -k "escopo_invalido or mirror_fora_do_qdrant" -q` → `12 passed` (3 backends × 3 lotes inválidos + mirror fora do Qdrant), com `ensure_ready_calls == 0` e `upsert_calls == []`.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13; guardas provadas antes de qualquer acesso ao destino.
  - [x] **IMPROVE**: `capabilities()` passou a derivar `supports_mirror` de `isinstance(self, MirrorMixin)`, eliminando a duplicação do flag em cada adapter e impedindo divergência entre a capacidade declarada e a operação existente. O comando de VERIFY do plano (`-k AC_007`) não selecionava caso algum (marcadores são comentários, não nomes) e foi substituído por um filtro real.
  <!-- specsfy:evidence {"task":"T022","refs":["US-002","FR-004","FR-006","FR-008","NFR-001","NFR-002","AC-004","AC-006","AC-007","AC-009"],"files":["src/providers/vectorstores/base.py","src/providers/vectorstores/__init__.py","src/providers/__init__.py"],"commands":[{"run":"uv run pytest tests/test_safety.py -k \"escopo_invalido or mirror_fora_do_qdrant\"","exit":0}]} -->

- [x] T023 [CODE] [US-002] Implementar `src/providers/vectorstores/in_memory.py` como referência completa do núcleo e do mirror, sem SDK — Refs: US-001, US-002, FR-004, FR-008, AC-004 — Depends: T022, T007
  - [x] **PREP**: Confirmado o contrato do núcleo e da extensão mirror na seção 10; `docs/` compatível.
  - [x] **EXECUTE**: `InMemoryVectorStoreAdapter(MirrorMixin, BaseVectorStoreAdapter)` sobre `DictVectorBackend`, com chaveamento por `(project_id, tenant_id)`. Herda `ensure_ready`/`list_ids`/`upsert`/`query`/`capabilities` e `delete_ids`; nunca usa cliente externo.
  - [x] **VERIFY**: `uv run pytest tests/test_vectorstore_conformance.py -k in_memory -q` → `8 passed`, incluindo núcleo completo, isolamento de escopo e mirror.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13; adapter serve de oráculo do contrato.
  - [x] **IMPROVE**: O backend em memória ficou em `base.py` (`DictVectorBackend`) e o adapter reduziu-se a 4 linhas, evitando uma segunda implementação de store.
  <!-- specsfy:evidence {"task":"T023","refs":["US-001","US-002","FR-004","FR-008","AC-004"],"files":["src/providers/vectorstores/in_memory.py"],"commands":[{"run":"uv run pytest tests/test_vectorstore_conformance.py -k in_memory","exit":0}]} -->

- [x] T024 [CODE] [US-002] Implementar `src/providers/vectorstores/qdrant.py` sobre `qdrant-client` (DEC-011) preservando cliente, seleção de porta HTTP/HTTPS, paginação, payload, dimensão, distância e mirror — Refs: US-002, FR-004, FR-006, NFR-002, NFR-004, AC-005 — Depends: T001, T022, T008
  - [x] **PREP**: Reconfirmado o risco R-002: o adapter fala com o SDK `qdrant-client==1.10.1` (`QdrantClient`, `scroll`, `upsert`, `delete`, `search`), que é a API comprovada pelo `src/embedder.py` atual, em vez de fixar a assinatura não verificada de `QdrantVectorStore`. `langchain-qdrant` fica disponível para a fatia de recuperação sem virar dependência de assinatura. `docs/` compatível.
  - [x] **EXECUTE**: `QdrantVectorStoreAdapter(MirrorMixin, BaseVectorStoreAdapter)` com validação local (collection + URL HTTP(S)) e `_QdrantBackend` lazy: `_build_client` preserva a seleção de porta (443/80 quando ausente), `scope_ids` pagina até exaustão com filtro `metadata.project_id`/`metadata.tenant_id` e converte falha em `UnreliableScopeReadError`, `write` mantém o payload `page_content` + `metadata`, `ensure` cria a collection com `VectorParams(size, Distance.COSINE)` e `remove` usa `PointIdsList`.
  - [x] **VERIFY**: `uv run pytest tests/test_qdrant_sync.py tests/test_vectorstore_conformance.py -k qdrant -q` → `21 passed` (espelho confirma esperados, contagens `(2,1,1,1)`, bloqueio por confirmação incompleta e regressão da SPEC-0001).
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13; nenhum acesso remoto real necessário (backend falso injetado por `settings['client']`).
  - [x] **IMPROVE**: A paginação passou a envolver `scroll` em `try/except` que levanta `UnreliableScopeReadError`, fechando o caso "releitura incompleta" também no Qdrant, não só no Pinecone.
  <!-- specsfy:evidence {"task":"T024","refs":["US-002","FR-004","FR-006","NFR-002","NFR-004","AC-005"],"files":["src/providers/vectorstores/qdrant.py"],"commands":[{"run":"uv run pytest tests/test_qdrant_sync.py tests/test_vectorstore_conformance.py -k qdrant","exit":0}]} -->

- [x] T025 [CODE] [US-002] Implementar `src/providers/vectorstores/chroma.py` com identidade `chunk_id`, detecção e bloqueio de legado incompatível e ausência estrita de tenant — Refs: US-002, US-003, FR-004, FR-005, FR-006, AC-008, AC-009, AC-011 — Depends: T022, T011, T012, T014
  - [x] **PREP**: Confirmado RED de T011/T012/T014 e o baseline `langchain-chroma==1.1.0`; `docs/` compatível.
  - [x] **EXECUTE**: `ChromaVectorStoreAdapter(BaseVectorStoreAdapter)` — sem `MirrorMixin`, portanto sem `delete_ids` e com `supports_mirror=False`. `list_ids` consulta `incompatible_ids(scope)` e levanta `LegacyDestinationError` orientando um destino novo, antes de qualquer upsert, deixando a base intacta. `_ChromaBackend` usa `add_documents(ids=[chunk_id])` para identidade estável e monta o `where` com `tenant_id` explícito (`""` quando ausente), de modo que omitir tenant não omite o filtro.
  - [x] **VERIFY**: `uv run pytest tests/test_vectorstore_conformance.py -k chroma -q` → `8 passed` (AC-008 sem crescimento na 2ª execução, AC-009 bloqueio de legado, AC-011 escopo estrito sem tenant).
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13; `backend.upsert_calls == []` no cenário de legado comprova o bloqueio anterior ao upsert.
  - [x] **IMPROVE**: `_is_chunk_id` valida a identidade por UUID (formato real gerado por `src/identity.py`), em vez de heurística textual, tornando a detecção de legado determinística.
  <!-- specsfy:evidence {"task":"T025","refs":["US-002","US-003","FR-004","FR-005","FR-006","AC-008","AC-009","AC-011"],"files":["src/providers/vectorstores/chroma.py"],"commands":[{"run":"uv run pytest tests/test_vectorstore_conformance.py -k chroma","exit":0}]} -->

- [x] T026 [CODE] [US-002] Implementar `src/providers/vectorstores/pinecone.py` preservando namespace, ID estável e append, com releitura de IDs do escopo para contagens exatas — Refs: US-002, FR-004, FR-005, NFR-002, AC-006 — Depends: T022, T009
  - [x] **PREP**: Confirmado RED de T009 e o baseline `langchain-pinecone==0.2.13`; `docs/` compatível.
  - [x] **EXECUTE**: `PineconeVectorStoreAdapter(BaseVectorStoreAdapter)` — sem `MirrorMixin` (append apenas). Validação local exige `index_name`, `namespace` e credencial. `_PineconeBackend` prefixa os IDs por `project_id|tenant|` para isolar o escopo dentro do namespace, pagina `list(prefix=...)` em `scope_ids` e converte falha em `UnreliableScopeReadError` sem publicar contagem aproximada; `ensure` compara a dimensão do índice com a dos embeddings antes do upsert.
  - [x] **VERIFY**: `uv run pytest tests/test_vectorstore_conformance.py -k pinecone -q` → `6 passed` (AC-006: reexecução append com `inseridos=0`, `mantidos=previstos`, `removidos=0`; AC-009: releitura incompleta bloqueia sem upsert).
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Registrado nas seções 11–13; contagens exatas produzidas pela releitura de escopo do próprio serviço `synchronize`.
  - [x] **IMPROVE**: A releitura devolve o `chunk_id` puro (`split("|")[-1]`), de modo que o cálculo de conjuntos em `synchronize` continua no espaço de IDs lógicos, sem vazar o prefixo do namespace para o contrato neutro.
  <!-- specsfy:evidence {"task":"T026","refs":["US-002","FR-004","FR-005","NFR-002","AC-006"],"files":["src/providers/vectorstores/pinecone.py"],"commands":[{"run":"uv run pytest tests/test_vectorstore_conformance.py -k pinecone","exit":0}]} -->

#### Fase 6 — Conformidade e observabilidade

- [x] T027 [CODE] [US-002] Completar a suíte de conformidade de vector store e embeddings em `tests/test_vectorstore_conformance.py` e `tests/test_embedding_conformance.py` até GREEN para todos os adapters — Refs: US-001, US-002, US-003, FR-008, NFR-003, NFR-004, AC-004, AC-006, AC-008, AC-009, AC-010, AC-011 — Depends: T019, T023, T024, T025, T026, T007, T009, T011, T012, T013, T014
  - [x] **PREP**: Confirmado que os quatro adapters executam o núcleo (`ensure_ready`/`list_ids`/`upsert`/`query`) e que só `qdrant`/`in_memory` expõem `delete_ids`; `docs/` compatível.
  - [x] **EXECUTE**: Suíte parametrizada por `in_memory|qdrant|chroma|pinecone` com `FakeVectorBackend` injetado por `settings['client']`; o assert `exercised == set(CORE_METHODS)` impede que qualquer passo do núcleo seja pulado. Conformidade de embeddings cobre dimensão, determinismo e separação de entradas.
  - [x] **VERIFY**: `uv run pytest tests/test_vectorstore_conformance.py tests/test_embedding_conformance.py -q` → `29 passed` (26 de vector store + 3 de embeddings), 4 adapters cobertos.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: 29 casos; adapters cobertos: `in_memory`, `qdrant`, `chroma`, `pinecone`; mirror exercitado apenas nos dois capazes.
  - [x] **IMPROVE**: `DictVectorBackend.search` passou a ordenar por similaridade de cosseno real (`_cosine`) e a devolver `score` verdadeiro, em vez de fatiar o dicionário e fixar `score=1.0`. O adapter in-memory vira um oráculo fiel de ranking para a conformidade, sem alterar o conjunto de resultados por escopo.
  <!-- specsfy:evidence {"task":"T027","refs":["US-001","US-002","US-003","FR-008","NFR-003","NFR-004","AC-004","AC-006","AC-008","AC-009","AC-010","AC-011"],"files":["tests/test_vectorstore_conformance.py","tests/test_embedding_conformance.py"],"commands":[{"run":"uv run pytest tests/test_vectorstore_conformance.py tests/test_embedding_conformance.py","exit":0}]} -->

- [x] T028 [CODE] [US-002] Levar `tests/test_qdrant_sync.py` a GREEN para o espelho preservado e as quatro contagens — Refs: US-002, FR-004, FR-006, NFR-002, NFR-004, AC-005 — Depends: T024, T008
  - [x] **PREP**: Confirmado RED de T008 e a paridade com o comportamento caracterizado em T003 (espelho remove só obsoletos, quatro contagens no log, falha de upsert nunca inicia limpeza); `docs/` compatível.
  - [x] **EXECUTE**: A seção SPEC-0003 do arquivo exercita o novo adapter via `synchronize` + `FakeVectorBackend`, enquanto os 11 casos da SPEC-0001 continuam cobrindo `src/embedder.py` sem alteração — nenhuma cobertura foi perdida. As fixtures legadas migram em T033, junto com a remoção do módulo.
  - [x] **VERIFY**: `uv run pytest tests/test_qdrant_sync.py -q` → `13 passed` (11 da SPEC-0001 + 2 da SPEC-0003).
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: 13 passed; contagens `(previstos, inseridos, mantidos, removidos) == (2, 1, 1, 1)` e `confirmed_before_delete is True` provam a confirmação anterior à remoção.
  - [x] **IMPROVE**: Nenhuma alteração foi necessária no arquivo nesta tarefa: os casos SPEC-0003 já haviam sido desenhados em T008 e ficaram verdes com o adapter de T024. Registrado que a limpeza das fixtures que fazem monkeypatch de `src.embedder` pertence a T033, para não remover cobertura antes do corte.
  <!-- specsfy:evidence {"task":"T028","refs":["US-002","FR-004","FR-006","NFR-002","NFR-004","AC-005"],"files":["tests/test_qdrant_sync.py"],"commands":[{"run":"uv run pytest tests/test_qdrant_sync.py","exit":0}]} -->

- [x] T029 [CODE] [US-002] Levar `tests/test_safety.py` a GREEN para fail-closed uniforme e validação de escopo de recuperação — Refs: US-002, US-003, FR-002, FR-006, NFR-001, NFR-002, AC-007, AC-012 — Depends: T022, T010, T015
  - [x] **PREP**: Confirmado RED de T010/T015 e o contrato de log da NFR-002 (modo, escopo e quatro contagens, sem credencial, token ou URL); `docs/` compatível.
  - [x] **EXECUTE**: `synchronize` valida modo e lote antes de tocar o destino nos três backends, e `LogicalScope` recusa `project_id` vazio/`None` antes de qualquer consulta. O log final de `synchronize` publica somente `modo`, `escopo` e as quatro contagens.
  - [x] **VERIFY**: `uv run pytest tests/test_safety.py -k "escopo_invalido or mirror_fora_do_qdrant or recuperacao_sem_project_id or escopo_e_invalido" -q` → `16 passed`; `uv run pytest tests/test_safety_policy.py -q` → `14 passed`.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: 16 + 14 casos verdes com `ensure_ready_calls == 0`, `upsert_calls == []`, `deleted_ids == []` e `query_calls == []`. **Escopo remanescente declarado**: o caso `test_consumidores_de_recuperacao_constroem_logical_scope_antes_de_query`, no mesmo arquivo, ainda falha porque `search.py`/`chat.py`/`demo_rag.py` não montam `LogicalScope`; essa fronteira pertence a T031/T032 e o arquivo inteiro é reverificado em T036.
  - [x] **IMPROVE**: `_validate_batch` passou a recusar registro com `chunk_id` ausente ou vazio antes do destino, fechando o caso-limite da seção 7 que nenhum AC exercitava diretamente.
  <!-- specsfy:evidence {"task":"T029","refs":["US-002","US-003","FR-002","FR-006","NFR-001","NFR-002","AC-007","AC-012"],"files":["tests/test_safety.py","src/providers/vectorstores/base.py"],"commands":[{"run":"uv run pytest tests/test_safety.py -k \"escopo_invalido or mirror_fora_do_qdrant or recuperacao_sem_project_id or escopo_e_invalido\"","exit":0},{"run":"uv run pytest tests/test_safety_policy.py","exit":0}]} -->

#### Fase 7 — Consumidores e corte limpo

- [x] T030 [CODE] [US-002] Migrar `pipeline.py` e `upsert_from_chunks.py` para o serviço de sincronização por contratos/factory — Refs: US-002, FR-007, NFR-004, AC-007 — Depends: T022, T024, T010, T003
  - [x] **PREP**: Confirmada a caracterização de T003 (contagens do espelho, `batch_size`, guardas fail-closed) e que nenhum dos dois scripts importa SDK; `docs/` compatível.
  - [x] **EXECUTE**: Criado `src/indexing.py`, o serviço de aplicação que é a única fronteira a conhecer o formato de `config.yaml` e de chunk: compõe adapters pela `ProviderFactory`, converte `Document` em `VectorRecord`, deriva o `LogicalScope` pela `SyncSafetyPolicy` e delega a `synchronize`. `pipeline.py` e `upsert_from_chunks.py` passaram a importar `index_chunks` desse serviço e agora registram as quatro contagens devolvidas.
  - [x] **VERIFY**: `uv run pytest tests/test_characterization_providers.py tests/test_qdrant_sync.py -q` → `25 passed`.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: 25 casos verdes; paridade com T003 mantida (mesmas contagens, mesmo `batch_size`, mesmas guardas). **Decisão registrada**: `src/indexing.py` não constava da estrutura de arquivos da seção 8; é composição interna reversível, sem novo comportamento, AC ou interface pública, e evita duplicar a tradução config→providers nos dois CLIs.
  - [x] **IMPROVE**: `synchronize` ganhou os parâmetros opcionais `dimensions` e `embed`, de modo que embeddings são gerados **somente** para os registros ausentes no destino. Sem isso a migração teria passado a embeddar o lote inteiro a cada execução — uma regressão de custo em relação ao `embedder.py` anterior (NFR-004).
  <!-- specsfy:evidence {"task":"T030","refs":["US-002","FR-007","NFR-004","AC-007"],"files":["pipeline.py","upsert_from_chunks.py","src/indexing.py"],"commands":[{"run":"uv run pytest tests/test_characterization_providers.py tests/test_qdrant_sync.py","exit":0}]} -->

- [x] T031 [CODE] [US-003] Migrar `search.py` e `demo_rag.py` para `LogicalScope` + `query`, com `project_id` obrigatório e `tenant_id` explícito opcional — Refs: US-003, FR-006, FR-007, NFR-003, AC-010, AC-011, AC-012 — Depends: T023, T025, T013, T014, T015, T003
  - [x] **PREP**: Confirmado RED de T013/T014/T015 e a origem do escopo: `project_id` vem de `projeto.nome` e `tenant_id` do novo argumento `--tenant`; `docs/` compatível.
  - [x] **EXECUTE**: `search.py` e `demo_rag.py` passaram a montar `LogicalScope` por `build_scope`, gerar o vetor da pergunta com `embed_query` e chamar `adapter.query(scope, vetor, k)`; nenhum filtro de SDK é construído no consumidor. Ambos ganharam `--tenant` e exibem o escopo em uso.
  - [x] **VERIFY**: `uv run pytest tests/test_vectorstore_conformance.py tests/test_safety.py tests/test_characterization_providers.py -q` → `62 passed`.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: 62 casos verdes, incluindo `test_consumidores_de_recuperacao_constroem_logical_scope_antes_de_query`, que estava RED desde T015.
  - [x] **IMPROVE**: `demo_rag.py` deixou de executar o fluxo RAG inteiro no import: o script foi reorganizado em `main()` sob `if __name__ == "__main__"`, com `argparse`. Isso remove o efeito colateral que impedia importar o módulo em teste e mantém a mesma execução por linha de comando.
  <!-- specsfy:evidence {"task":"T031","refs":["US-003","FR-006","FR-007","NFR-003","AC-010","AC-011","AC-012"],"files":["search.py","demo_rag.py"],"commands":[{"run":"uv run pytest tests/test_vectorstore_conformance.py tests/test_safety.py tests/test_characterization_providers.py","exit":0}]} -->

- [x] T032 [CODE] [US-003] Adaptar a recuperação de `chat.py` para contratos/`LogicalScope`, preservando a cadeia LCEL e `ChatOpenAI` como exceção rastreada pelo BACKLOG-0010 — Refs: US-003, FR-007, NFR-003, AC-003, AC-012 — Depends: T023, T015, T003
  - [x] **PREP**: Confirmado que a adaptação não introduz agente nem LangGraph: a cadeia LCEL e `ChatOpenAI` permanecem como estão; `docs/` compatível.
  - [x] **EXECUTE**: Em `chat.py`, `store.as_retriever(...)` foi trocado por um `RunnableLambda` que monta o vetor da pergunta e chama `store.query(scope, vetor, k)` dentro do escopo autorizado. A cadeia `{"context": retriever | format_docs, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()` ficou intacta; `format_docs` passou a ler `SearchResult.content`. Adicionados `--tenant`, `--k` e `--config`.
  - [x] **VERIFY**: `uv run pytest tests/test_safety.py tests/test_characterization_providers.py -k "consumidores or logical_scope" -q` → `2 passed`; suíte completa `uv run pytest -q` → `141 passed`.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: `ChatOpenAI` em `chat.py` segue sendo a única exceção, agora comprovada pelo teste estático `test_chatopenai_em_chat_py_e_a_unica_excecao` (BACKLOG-0010).
  - [x] **IMPROVE**: O comando de VERIFY do plano usava `-k "chat or AC_012"`, que não selecionava caso algum (marcadores `SPECSFY:` são comentários, não nomes de teste); substituído por um filtro real sobre os nomes existentes.
  <!-- specsfy:evidence {"task":"T032","refs":["US-003","FR-007","NFR-003","AC-003","AC-012"],"files":["chat.py"],"commands":[{"run":"uv run pytest tests/test_safety.py tests/test_characterization_providers.py -k \"consumidores or logical_scope\"","exit":0}]} -->

- [x] T033 [CODE] [US-001] Remover `src/embedder.py` sem shim e migrar as fixtures que faziam monkeypatch de `embedder.get_embeddings` — Refs: US-001, FR-003, FR-007, NFR-004, AC-003 — Depends: T030, T031, T032, T006
  - [x] **PREP**: Confirmado por varredura AST que nenhum módulo fora de `tests/` importava `src.embedder` após T030–T032; `docs/` compatível.
  - [x] **EXECUTE**: `src/embedder.py` removido com `git rm`, sem shim. As fixtures migraram para o stack novo, preservando cada garantia da SPEC-0001: `tests/test_safety.py` passou a espionar `indexing.build_vector_store`/`build_embeddings` em vez de `embedder._get_qdrant_client`/`get_embeddings`; `tests/test_qdrant_sync.py` trocou os dublês com formato do SDK Qdrant pelo `FakeVectorBackend` neutro e chama `indexing.index_chunks`; `tests/test_characterization_providers.py` foi reapontado para a fronteira nova mantendo os mesmos comportamentos congelados. `FakeVectorBackend` ganhou o interruptor `fail_write` para preservar o caso "falha de upsert nunca inicia a limpeza".
  - [x] **VERIFY**: `uv run pytest -q` → `141 passed`, zero falhas.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: 141 casos verdes sem `src/embedder.py`. As 10 garantias da SPEC-0001 continuam cobertas: espelho remove só obsoletos, falha de upsert não remove nada, reexecução idêntica não altera a base, isolamento por projeto e por tenant, log com as quatro contagens e sem segredo, remoção bloqueada sem confirmação, substituição total permitida e tenant inválido bloqueado antes do provider.
  - [x] **IMPROVE**: `scope_from_chunks` passou a delegar a `SyncSafetyPolicy.assert_valid_scope` em vez de reimplementar a validação de escopo. Isso eliminou a duplicação de regra e corrigiu uma lacuna real de ordem: `chunk_id` duplicado agora bloqueia **antes** de qualquer provider ser composto, como exige a NFR-001.
  <!-- specsfy:evidence {"task":"T033","refs":["US-001","FR-003","FR-007","NFR-004","AC-003"],"files":["tests/test_safety.py","tests/test_qdrant_sync.py","tests/test_characterization_providers.py","tests/_fakes_vectorstore.py","src/indexing.py"],"commands":[{"run":"uv run pytest","exit":0}]} -->

- [x] T034 [CODE] [US-001] Levar `tests/test_provider_boundaries.py` a GREEN: nenhum import de SDK de vector store ou classe de embeddings fora de `src/providers/` e `ChatOpenAI` como única exceção — Refs: US-001, FR-001, FR-003, FR-007, NFR-003, AC-003 — Depends: T006, T033
  - [x] **PREP**: Confirmado RED de T006 e a lista de módulos varridos (cada arquivo `*.py` do repositório fora de `.venv`, `build`, `dist`, `__pycache__`, `tests/` e `src/providers/`); `docs/` compatível.
  - [x] **EXECUTE**: O teste estático afirma as quatro condições do AC-003: `src/embedder.py` não existe, nenhum módulo importa `src.embedder`, SDKs de vector store e classes de embeddings só aparecem em `src/providers/`, e `ChatOpenAI` em `chat.py` é a única exceção.
  - [x] **VERIFY**: `uv run pytest tests/test_provider_boundaries.py -q` → `4 passed`. **Sensibilidade comprovada**: um arquivo-sonda com `import qdrant_client` na raiz fez `test_sdks_de_provider_confinados_a_src_providers` falhar, e o teste voltou a passar após removê-lo — o verde não é vacuoso.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: 4 casos verdes; árvore de imports resultante confina `qdrant_client`, `chromadb`, `pinecone`, `langchain_qdrant`, `langchain_chroma`, `langchain_pinecone` e `langchain_huggingface` a `src/providers/`.
  - [x] **IMPROVE**: `_imports` passou a devolver o caminho do módulo além do símbolo, o que permitiu substituir a checagem textual anterior — que relia o arquivo inteiro duas vezes por import e gerava duplicatas — por comparação direta de módulo em conjuntos ordenados.
  <!-- specsfy:evidence {"task":"T034","refs":["US-001","FR-001","FR-003","FR-007","NFR-003","AC-003"],"files":["tests/test_provider_boundaries.py"],"commands":[{"run":"uv run pytest tests/test_provider_boundaries.py","exit":0}]} -->

#### Fase de reconciliação — DEC-011

- [x] T037 [OPS] Remover `langchain-qdrant` de `./pyproject.toml` e `./uv.lock`, mantendo `qdrant-client` como única via de acesso ao Qdrant — Refs: FR-003, NFR-004 — Depends: T024
  - [x] **PREP**: `grep -rn "langchain_qdrant" src/ *.py` não encontrou nenhum import; DEC-011 relida e confirmada como origem da remoção.
  - [x] **EXECUTE**: `uv remove langchain-qdrant` → `Resolved 134 packages`, `Uninstalled 1 package: langchain-qdrant==1.0.0`. O diff de `./pyproject.toml` frente à base passou a conter apenas `+ "langchain-huggingface>=1.2.2"`; nenhuma outra restrição mudou e `./uv.lock` foi re-resolvido.
  - [x] **VERIFY**: `uv run pytest -q` → `141 passed`; nenhuma dependência declarada permanece sem uso (`langchain-huggingface` é importado por `src/providers/embeddings/huggingface.py`).
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: `uv remove langchain-qdrant` + `git diff pyproject.toml` (uma linha adicionada, nenhuma removida além da própria dependência) + suíte verde com 141 casos.
  - [x] **IMPROVE**: Nenhuma além do escopo. A remoção foi conferida por varredura de import em vez de leitura do manifesto, o que também prova que o adapter Qdrant não passou a depender da integração por caminho indireto.

- [x] T038 [DOC] Corrigir em `.specsfy/STACK.md` e `docs/packages.md` as linhas que ainda declaram a integração dedicada do Qdrant — Refs: NFR-004 — Depends: T037
  - [x] **PREP**: Localizadas a linha de inventário do Qdrant e a nota humana criadas por T002 em `.specsfy/STACK.md`, além da linha de Vetores em `docs/packages.md`.
  - [x] **EXECUTE**: `.specsfy/STACK.md` volta a declarar `Qdrant Client 1.10.1` sozinho e a nota humana passa a explicar a DEC-011 (por que a integração dedicada foi descartada e removida), acrescentando a regra de confinamento de SDKs. `docs/packages.md` registra `qdrant-client` como única via de acesso. O registro de `langchain-huggingface` foi preservado nos dois arquivos.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`; `grep -rn "langchain-qdrant" .specsfy/ docs/` não retorna nenhuma declaração obsoleta.
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Monitor `CURRENT`; inventário de `.specsfy/STACK.md` e `docs/packages.md` alinhado à DEC-011; `uv run pytest -q` → 141 passed.
  - [x] **IMPROVE**: Escopo ampliado por uma inconsistência encontrada durante a conferência: `.specsfy/STACK.md`, `.specsfy/DATABASE.md`, `docs/application.md` e `docs/architecture.md` ainda apontavam para `src/embedder.py`, e `docs/architecture.md` afirmava que esse módulo "ainda concentra criação de providers e persistência" — falso desde T033. As referências passaram a apontar `src/providers/**` e `src/indexing.py`. O monitor de contexto não pegou isso porque só compara caminhos alterados, não a veracidade do texto.

#### Fase final — Qualidade e documentação

- [x] T035 [DOC] Registrar em `.specsfy/RULES.md` o confinamento de SDKs de provider em `src/providers/` como regra confirmada, via `$specsfy-aux-rules` — Refs: NFR-003 — Depends: T034
  - [x] **PREP**: Lido `.specsfy/RULES.md`; a regra proposta foi apresentada à pessoa responsável e confirmada em 2026-09-01 antes da gravação.
  - [x] **EXECUTE**: Regra adicionada na seção `Arquitetura`, logo após a regra de Factory/Adapter, sem alterar nem remover nenhuma regra existente: SDKs de banco vetorial e classes de embeddings confinados a `src/providers/`, com `ChatOpenAI` em `chat.py` como única exceção temporária (BACKLOG-0010) e verificação por teste estático de AST.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `Context monitor: CURRENT` (exit 0).
  - [x] **VISUAL**: Não aplicável — mudança sem superfície gráfica.
  - [x] **EVIDENCE**: Uma regra adicionada em `.specsfy/RULES.md`; confirmação explícita da pessoa responsável registrada nesta tarefa.
  - [x] **IMPROVE**: A regra aponta o teste que a verifica (`tests/test_provider_boundaries.py`), de modo que ela é auditável por execução e não apenas por leitura.

- [x] T036 [TEST] Executar regressão total, rastreabilidade e verificação de contexto e revisar `PROJECT.md` — Refs: US-001, US-002, US-003, FR-008, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012 — Depends: T027, T028, T029, T033, T034
  - [x] **PREP**: Identificados as suítes (`uv run pytest`), os checks (`check_traceability.mjs --full-chain`, `verify_acceptance.mjs`, `verify_evidence.mjs`, `validate_tasks.mjs`, `monitor_context.mjs`) e o Delivery Gate.
  - [x] **EXECUTE**: `uv run pytest` → **141 passed**. Seção 12 preenchida com comando e resultado por requisito. `docs/` e `.specsfy/PACKAGES.md` reconstruídos por `$specsfy-documentator`. `PROJECT.md` revisado de fato: capacidades ganharam a troca de provider sem alterar pipeline, as contagens exatas em qualquer backend e a recuperação escopada; o contexto técnico passou a descrever `src/providers/`, `src/indexing.py` e a remoção do `src/embedder.py`.
  - [x] **VERIFY**: `uv run pytest` → 141 passed, 0 falhas. `verify_acceptance.mjs` → `QA: PASSED`. `check_traceability.mjs --full-chain` → 27/27 IDs, `uncovered: []`, `broken_chains: []`, `insufficient_cases: {}`, 89 casos de feature. `monitor_context.mjs --check` → `CURRENT` (exit 0), sem `--acknowledge-project-no-change`.
  - [x] **VISUAL**: Não aplicável — a entrega altera módulos Python e CLIs, sem tela, formulário ou navegação; `Interface para pessoas` é `Não` no cabeçalho.
  - [x] **EVIDENCE**: 141 casos verdes; 12/12 AC com RED e GREEN registrados na seção 11; 15/15 requisitos com `Passed` e comando na seção 12. **Marcadores órfãos**: `check_traceability` da SPEC-0003 lista critérios e histórias que não são desta fatia; verificado que três critérios pertencem à SPEC-0001 (28/28 coberta) e os demais, com as duas histórias correspondentes, à SPEC-0002 (41/41 coberta). É artefato de arquivos de teste compartilhados entre specs, não lacuna desta fatia. Ruff permanece pendente do BACKLOG-0007.
  - [x] **IMPROVE**: Retrospectiva — (1) a reescrita de `test_qdrant_sync.py` em T033 removeu o marcador `AC-018` e quebrou a rastreabilidade da SPEC-0002, já concluída; detectado por rodar o checker contra as outras specs e corrigido restaurando o marcador no caso equivalente. Lição: ao reescrever um arquivo de teste compartilhado, verificar a rastreabilidade de **todas** as specs que o referenciam, não só a atual. (2) Dois comandos de VERIFY do plano usavam `-k` sobre marcadores `SPECSFY:`, que são comentários e não nomes de teste; passavam sem selecionar caso algum. Substituídos por filtros reais e registrado em T022/T032.

### 15. Ordem de execução

- Caminho crítico: T001 → (T004…T015 RED) → T016 → T017 → T018 → T019 → T022 → T023 → {T024, T025, T026} → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T034 → T036.
- Tarefas paralelas: T003 corre em paralelo à Fase 2; T020 e T021 após T019; T024, T025 e T026 após T022 e seus RED; T035 após T034. Nenhuma dessas compartilha arquivo ou estado mutável.
- Reconciliação da DEC-011: T037 → T038, ambas depois de T024 e antes do fechamento do Delivery Gate em T036.
- Estratégia de MVP: contratos + factory + fake/in-memory + Qdrant + OpenAI preservando `pipeline.py` (T016–T020, T022–T024, T028, T030). A mesma spec exige concluir os seis providers, os cinco consumidores e a remoção de `src/embedder.py` antes do Delivery Gate.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0001 concluída: `SyncSafetyPolicy`, espelho Qdrant e contagens protegidas.
- `langchain-huggingface` deve ser adicionado e resolvido por uv. `langchain-qdrant` foi descartado pela DEC-011; `qdrant-client==1.10.1` permanece a única via de acesso ao Qdrant.
- BACKLOG-0009 e BACKLOG-0010 dependem desta entrega, mas não a bloqueiam.

#### Riscos

- API `langchain-qdrant` incompatível com `qdrant-client==1.10.1` → **risco materializado e encerrado pela DEC-011**: a assinatura não foi comprovada (R-002, `unverifiable`), então o adapter preserva o helper e o SDK atuais em vez de adotar a integração dedicada.
- `list_ids` incompleto ou caro → paginação obrigatória, testes de múltiplas páginas e bloqueio em falha.
- Filtro de tenant ausente interpretado como sem filtro → caso de conformidade obrigatório em cada backend.
- Testes atuais fazem monkeypatch de `embedder.get_embeddings` → migrar fixtures sem perder cobertura da SPEC-0001.
- ChromaDB legado inesperado → detectar, bloquear e preservar; nunca migrar ou limpar automaticamente.
- Corte limpo amplo → caracterização dos cinco consumidores e execução da regressão completa.

#### Suposições

- Não há consumidor externo da API de `src/embedder.py`; os cinco scripts do repositório são a superfície completa observada.
- `config.yaml` e metadados de chunks permanecem estáveis; `project_id` vem de `projeto.nome` e `tenant_id` é argumento explícito nos CLIs de recuperação.
- Qdrant + OpenAI são o alvo operacional inicial; ChromaDB/Pinecone continuam suportados e verificáveis.
- Não existe base ChromaDB local a migrar no estado observado em 2026-09-01.

### 17. Decisões

- **DEC-001**: Usar contratos neutros + Factory + Adapter, em vez de condicionais centralizadas — reduz acoplamento e torna substituição verificável.
- **DEC-002**: Colocar `list_ids(scope)` no núcleo e `delete_ids` apenas na extensão `mirror` — todos produzem contagens exatas sem fingir capacidade destrutiva.
- **DEC-003**: Factory apenas despacha; adapter valida settings localmente; cliente remoto é lazy — preserva fallback/configuração própria e fail-closed.
- **DEC-004**: Manter `SyncSafetyPolicy` em `src/safety.py` — evita duplicar política nos adapters.
- **DEC-005**: Preservar `mirror` somente em Qdrant/in-memory; ChromaDB/Pinecone ficam em append — paridade destrutiva pertence ao BACKLOG-0009.
- **DEC-006**: ChromaDB novo usa `chunk_id`; legado incompatível bloqueia e permanece intacto — não existe migração segura necessária no estado atual.
- **DEC-007**: Toda recuperação exige `project_id`; ausência de tenant corresponde somente ao escopo sem tenant — evita vazamento por omissão de filtro.
- **DEC-008**: Remover `src/embedder.py` sem shim e migrar os cinco consumidores — não há consumidor externo observado.
- **DEC-009**: Migrar imports para pacotes LangChain dedicados, reconfirmando assinaturas na implementação — elimina imports legados sem fixar API não comprovada. **Revisada pela DEC-011**: aplicada integralmente a Hugging Face; para o Qdrant, a reconfirmação falhou e prevaleceu a cláusula “sem fixar API não comprovada”.
- **DEC-010**: LLM permanece fora; `ChatOpenAI` em `chat.py` é exceção temporária — BACKLOG-0010 separa a terceira família.
- **DEC-011** (2026-09-01, revisão pós-implementação): Não adotar `langchain-qdrant`; o adapter Qdrant acessa o destino pelo SDK `qdrant-client==1.10.1`. Motivo: o R-002 permaneceu `unverifiable` durante toda a fatia, e a API que o `src/embedder.py` já usava em produção é a única comprovada para essa versão. Trocar por uma assinatura não confirmada elevaria o risco sem ganho observável — o comportamento exigido pelos AC-005, AC-010 e AC-011 é idêntico nas duas vias. A dependência não usada é removida de `pyproject.toml`/`uv.lock`. Substitui a metade Qdrant da DEC-009; a metade Hugging Face permanece válida e entregue. Resolve FIND-DEL-001.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Os doze cenários `AC` passam com casos TDD próprios.
- [x] Cada US, FR e NFR possui pelo menos três cenários e evidência executável.
- [x] As seis integrações e os adapters in-memory/fake passam na conformidade aplicável.
- [x] Nenhum cliente remoto é criado antes das validações locais e de escopo.
- [x] Contagens exatas e isolamento por projeto/tenant estão comprovados nos três backends.
- [x] `src/embedder.py` foi removido e os cinco consumidores usam contratos/factories.
- [x] Imports legados de Qdrant/Hugging Face foram substituídos; SDKs estão confinados a `src/providers/`; `langchain-huggingface` está em uso e nenhuma dependência declarada permanece sem uso.
- [x] `.specsfy/STACK.md` e `.specsfy/PACKAGES.md` refletem as integrações adicionadas e suas versões resolvidas.
- [x] Pytest completo está verde; Ruff está verde quando configurado pelo BACKLOG-0007.
- [x] Documentação foi reconstruída e o monitor de contexto está `CURRENT`.
