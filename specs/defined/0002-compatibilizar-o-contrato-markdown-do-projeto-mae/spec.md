# Especificação integrada: Compatibilizar o contrato Markdown do projeto-mãe

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0002 |
| Slug | 0002-compatibilizar-o-contrato-markdown-do-projeto-mae |
| Status | Defined |
| Effort | 6 |
| Effort updated at | 2026-09-01 |
| Effort rationale | Toca quatro módulos (`identity`, `safety`, `chunker`, `embedder`) mais um módulo novo (`status_gate`), estende o escopo lógico de sincronização fail-closed e corrige um defeito real de parsing; volume e risco comparáveis ao SPEC-0001. |
| ClickUp Task | LEAD-87 |
| Milestones | M0 — Finalizar o componente rag-ingestion-pipeline |
| Definition Gate | Passed |
| Plan Gate | Pending |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-01 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O contrato de recepção de Markdown deste componente não preserva a identidade
nem o escopo declarados pelo `rag-pipeline`, e não trata o formato Q&A do
projeto-mãe. A auditoria de `src/identity.py`, `src/loader.py`,
`src/chunker.py` e `src/safety.py` encontrou:

- `document_id` recebido no frontmatter é sobrescrito incondicionalmente pela
  identidade determinística local: `document.metadata["document_id"] =
  stable_uuid(...)` em `src/identity.py:27`, sem checar se o valor já existe.
  Como `document_id` compõe a `base_key` de cada `chunk_id`
  (`src/identity.py:53-56`), a origem nunca consegue correlacionar seus
  registros com os IDs gerados aqui.
- `tenant_id` não participa da identidade nem do escopo lógico da
  sincronização. `SyncSafetyPolicy.assert_valid_scope` valida somente
  `project_id` e `chunk_id` (`src/safety.py:66-98`), e a remoção de obsoletos
  em modo espelho filtra apenas por `metadata.project_id`
  (`src/embedder.py:284-292`). Dois tenants compartilhando o mesmo
  `project_id` fariam a limpeza de um tenant apagar pontos do outro — uma via
  de perda de dados que o SPEC-0001 não cobre, porque `tenant_id` não existia
  no vocabulário do componente quando aquela guarda foi desenhada.
- `type`, `version` e `status` não têm efeito algum hoje: nenhum código lê
  esses campos além do repasse genérico de frontmatter feito por
  `_sanitize_metadata` (`src/loader.py:46-58`).
- O formato Q&A do projeto-mãe (blocos separados por `---`) colide com o
  delimitador de frontmatter YAML. O regex `^---\s*\n(.*?)\n---\s*\n` usado
  com `match()` (`src/loader.py:28-29`) engole o primeiro bloco de um
  documento Q&A que começa com `---` como se fosse YAML, descartando-o do
  `page_content`. Nenhum splitter reconhece `---`: os separadores do
  `RecursiveCharacterTextSplitter` são `["\n\n", "\n", " ", ""]`
  (`src/chunker.py:130-136`), então pares pergunta/resposta são cortados por
  tamanho, não por conteúdo.
- Os sete documentos hoje em `documentos/vivo_gold_banda_larga_pf/` não têm
  frontmatter algum: o contrato nunca foi exercitado na prática, e qualquer
  mudança precisa preservar esse caminho sem regressão.

O contrato do `rag-pipeline` ainda não está congelado — o projeto-mãe está em
estágio inicial —, então os valores permitidos de `type` e `status` não são
conhecidos. O componente precisa aceitar os cinco campos sem depender de uma
lista fechada de valores.

#### Resultado desejado

Um documento validado pelo `rag-pipeline` entra neste componente sem perder
`document_id`, sem misturar `tenant_id` entre bases, com `status`
reprovado excluído da indexação segundo uma lista configurável, e com pares
pergunta/resposta Q&A preservados inteiros em um único chunk cada. A base
atual, sem frontmatter, continua processada exatamente como hoje.

#### Métricas de sucesso

- 100% dos documentos com `document_id` no frontmatter mantêm esse valor como
  identidade do documento e de todos os seus chunks.
- Zero execuções de sincronização em modo espelho removem ponto de um
  `tenant_id` diferente do sincronizado.
- 100% dos documentos com `status` presente na lista bloqueante configurada
  são excluídos da indexação, com o motivo registrado em log e manifesto.
- 100% dos blocos Q&A separados por `++++` em um documento com
  `splitter: qa` viram exatamente um chunk cada, sem corte por tamanho.
- A suíte de regressão existente (37 casos em `tests/`) permanece verde após
  a mudança, comprovando que a base sem frontmatter não regride.

### 2. Research e esclarecimentos

#### Researchs executados

- Nenhuma pesquisa externa foi necessária. A investigação usou exclusivamente
  código local (`src/identity.py`, `src/loader.py`, `src/chunker.py`,
  `src/safety.py`, `src/embedder.py`, `src/manifest.py`, `config.yaml`,
  `pipeline.py`, `documentos/vivo_gold_banda_larga_pf/`) e o `spec.md` já
  entregue do SPEC-0001.

#### Fontes e contexto consultados

- `src/identity.py`, `src/loader.py`, `src/chunker.py`, `src/safety.py`,
  `src/embedder.py`, `src/manifest.py`, `pipeline.py`, `config.yaml`: contrato
  implementado hoje.
- `documentos/vivo_gold_banda_larga_pf/*.md`: sete documentos reais, todos
  sem frontmatter — restrição de compatibilidade retroativa.
- `specs/completed/0001-bloquear-recriacao-destrutiva/spec.md`: guarda de
  escopo entregue (`SyncSafetyPolicy`), que este item estende.
- `.specsfy/DATABASE.md`: confirma a ausência de tenant persistente no código
  atual e a exigência multi-tenant do projeto-mãe como restrição futura.
- `specs/backlog/0002-compatibilizar-contrato-markdown.md`: brief refinado
  com as oito decisões da entrevista de descoberta.

#### Documentação consultada

- Nenhuma. `briefing.md`, `tech_stack.md` e a constituição 1.2.1 do
  `rag-pipeline`, citados no backlog, não foram fornecidos nesta conversa;
  a Decisão 1 (abaixo) resolve essa ausência tratando o contrato do
  projeto-mãe como não congelado, em vez de bloquear a especificação.

#### Artefatos de pesquisa armazenados

- `specs/defined/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/research/auditoria-codigo/contrato-markdown-atual.md`: trechos literais de `src/identity.py`, `src/loader.py`, `src/chunker.py`, `src/safety.py`, `src/embedder.py` e a listagem de `documentos/vivo_gold_banda_larga_pf/` no commit `2d7c614`, lidos em 2026-09-01. Licença: código e documentação próprios do projeto, cópia integral permitida. Propósito: preservar o estado auditado do contrato atual, já que a implementação desta spec altera justamente esses trechos.

#### Dúvidas respondidas

- **Q**: O contrato do `rag-pipeline` já está congelado? → **A**: Não; os
  cinco campos são previstos, mas seus valores permitidos ainda podem mudar.
  O componente deve tolerar essa evolução sem quebrar.
- **Q**: Quem prevalece quando `document_id` vem no frontmatter? → **A**: A
  origem prevalece; ausência preserva a geração determinística atual.
- **Q**: Que papel tem `tenant_id` na sincronização? → **A**: Opcional,
  porém estrito quando presente — a totalidade do lote declara o mesmo `tenant_id` ou
  nenhum documento declara, e o escopo lógico passa a ser
  `tenant_id + project_id`.
- **Q**: Um `status` não aprovado deve bloquear a indexação? → **A**: Sim,
  por uma lista configurável em `config.yaml`, vazia por padrão
  (fail-open quando não configurada).
- **Q**: `version` participa da identidade do chunk? → **A**: Não; é
  metadado de auditoria, sem efeito sobre `chunk_id`.
- **Q**: Como o formato Q&A deve virar chunks? → **A**: Um chunk por bloco,
  sempre; o separador é `++++`, não `---`, para eliminar a colisão com o
  delimitador de frontmatter YAML.
- **Q**: `type` influencia o processamento? → **A**: Não; é metadado de
  auditoria e filtro de consulta.
- **Q**: Como o pipeline decide que um documento usa o splitter Q&A? →
  **A**: Por declaração explícita `splitter: qa` no frontmatter, reaproveitando
  o mecanismo já existente em `src/chunker.py:23`; nunca por detecção
  automática de conteúdo.

#### Dúvidas abertas

- Nenhuma lacuna aplicável. Os valores futuros de `type` e `status` seguem
  intencionalmente abertos (ver `Suposições`, seção 16) porque o projeto-mãe
  ainda não os congelou; isso não bloqueia esta especificação.

### 3. Escopo e atores

#### Incluído

- Precedência do `document_id` recebido no frontmatter sobre a geração
  determinística local, propagada a todos os `chunk_id` do documento.
- Extensão do escopo lógico de sincronização (`SyncSafetyPolicy`) para
  `tenant_id`, com validação fail-closed de lote uniforme e remoção de
  obsoletos filtrada por tenant.
- Gate configurável de bloqueio de indexação por `status`, fail-open por
  padrão.
- Passthrough de `type` e `version` como metadado auditável, sem efeito no
  processamento.
- Splitter Q&A ativado por `splitter: qa`, dividindo o corpo por `++++` em um
  chunk por bloco, sem corte por tamanho.

#### Fora de escopo

- Autenticação, autorização ou persistência multi-tenant no destino vetorial
  além do filtro de escopo lógico já descrito.
- Qualquer comportamento do `rag-pipeline` em si.
- Congelamento definitivo dos valores permitidos de `type` e `status`.
- Novas estratégias de chunking do LangChain além de header, caracteres e
  Q&A (Text Splitter genérico, outros splitters Markdown) — registrada como
  ideia futura no backlog, não escopo desta entrega.
- Reescrita dos sete documentos atuais para adotar frontmatter; a
  compatibilidade retroativa sem frontmatter é requisito, não a migração da
  base existente.

#### Atores

- **Equipe de integração `rag-pipeline` ↔ `rag-ingestion-pipeline`**:
  consome o contrato de frontmatter para validar que a identidade e o
  escopo declarados na origem sobrevivem até o banco vetorial.
- **Operador de bases multi-tenant**: executa `pipeline.py` e
  `upsert_from_chunks.py` sobre lotes que podem ou não declarar `tenant_id`,
  e depende do fail-closed para nunca misturar dados entre tenants.

### 4. Princípios e restrições do projeto

- **PR-001**: Nenhuma mutação remota ocorre antes de o escopo lógico ser
  validado — princípio fail-closed já estabelecido pelo SPEC-0001
  (`src/safety.py`), que esta entrega estende, não substitui.
- **PR-002**: O componente não fixa valores de negócio que pertencem ao
  projeto-mãe ainda não publicado; campos como `type` e `status` são tratados
  como extensíveis, não como enumeração fechada.
- **PR-003**: Compatibilidade retroativa é obrigatória — a base atual sem
  frontmatter não pode regredir em contagem de chunks, IDs ou comportamento.

### 5. Histórias de usuário

#### US-001 — Preservar a identidade do documento recebida do projeto-mãe (P1)

Como equipe de integração `rag-pipeline` ↔ `rag-ingestion-pipeline`, quero que
o `document_id` do frontmatter seja usado como identidade do documento e de
todos os seus chunks, para que a mesma origem tenha o mesmo ID no
projeto-mãe e no banco vetorial.

**Por que P1**: sem isso, a integração futura não consegue correlacionar
registros entre os dois componentes — é o requisito central do backlog.
**Teste independente**: processar um documento com `document_id` conhecido e
confirmar que ele aparece inalterado no documento e em cada chunk gerado.
**Requisitos**: FR-001, FR-002

#### US-002 — Isolar a sincronização por tenant (P1)

Como operador de bases multi-tenant, quero que o escopo de sincronização
inclua `tenant_id` quando presente, para que a limpeza de obsoletos nunca
afete outro tenant.

**Por que P1**: fecha uma via real de perda de dados entre tenants que o
SPEC-0001 não cobre.
**Teste independente**: sincronizar dois lotes de `tenant_id` diferentes no
mesmo `project_id` em modo espelho e confirmar que a remoção de um nunca
alcança pontos do outro.
**Requisitos**: FR-003, FR-004

#### US-003 — Bloquear indexação por status configurável (P2)

Como operador, quero que documentos com `status` não aprovado sejam
excluídos da indexação segundo uma lista configurável, para não publicar
conteúdo reprovado na base vetorial.

**Por que P2**: importante para qualidade, mas não bloqueia a integração
básica de identidade e escopo, por isso vem depois de US-001/US-002.
**Teste independente**: configurar um valor bloqueante e confirmar que um
documento com esse `status` não gera chunks indexados, com o motivo
registrado.
**Requisitos**: FR-005

#### US-004 — Processar documentos Q&A por blocos `++++` (P1)

Como equipe de integração, quero que um documento com `splitter: qa` divida
corretamente seu corpo por `++++`, para que cada par pergunta/resposta
permaneça íntegro em um único chunk.

**Por que P1**: corrige um defeito real de perda de conteúdo (colisão com o
delimitador de frontmatter) e destrava o formato Q&A do projeto-mãe.
**Teste independente**: processar um documento Q&A com três blocos e
confirmar exatamente três chunks, cada um com o par completo.
**Requisitos**: FR-006, FR-007

#### US-005 — Preservar `type` e `version` como metadado auditável (P2)

Como operador, quero que `type` e `version` do frontmatter fiquem
disponíveis no payload de cada chunk sem afetar o processamento, para
consulta e auditoria futura.

**Por que P2**: valor de auditoria, sem risco de perda de dados nem de
integração — a menor prioridade das cinco histórias.
**Teste independente**: processar um documento com `type` e `version`
declarados e confirmar que ambos aparecem em cada chunk, sem alterar
`chunk_id`, chunking ou bloqueio.
**Requisitos**: FR-008

### 6. Cenários BDD de aceite

#### AC-001 — document_id do frontmatter vira identidade do documento e dos chunks

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-001
Feature: Precedência de document_id recebido

  Scenario: Documento declara document_id no frontmatter
    Given um documento Markdown com document_id "doc-rag-pipeline-42" no frontmatter
    When o documento é carregado e chunkado
    Then o metadata do documento contém document_id "doc-rag-pipeline-42"
    And todos os chunks gerados contêm document_id "doc-rag-pipeline-42"
```

#### AC-002 — ausência de document_id preserva a geração determinística

**Cobre**: US-001, FR-001, FR-002, NFR-002

```gherkin
@US-001 @FR-001 @FR-002 @NFR-002 @AC-002
Feature: Precedência de document_id recebido

  Scenario: Documento sem document_id no frontmatter
    Given um documento Markdown sem document_id no frontmatter, como os da base atual
    When o documento é carregado e chunkado
    Then o document_id gerado é idêntico ao produzido pelo comportamento atual
    And o chunk_id de cada chunk continua determinístico e único
```

#### AC-003 — mudança de origem do document_id força reindexação consistente

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-003
Feature: Precedência de document_id recebido

  Scenario: Documento antes sem frontmatter passa a declarar document_id
    Given um documento já processado com document_id determinístico local
    When o mesmo documento é reprocessado com document_id externo no frontmatter
    Then todos os chunk_id do documento mudam de forma determinística
    And reprocessamentos repetidos do mesmo documento produzem os mesmos novos chunk_id
```

#### AC-004 — lote uniforme com tenant_id sincroniza normalmente

**Cobre**: US-002, FR-003

```gherkin
@US-002 @FR-003 @AC-004
Feature: Escopo lógico com tenant_id

  Scenario: Todos os chunks do lote declaram o mesmo tenant_id
    Given um lote de chunks com tenant_id "cliente-a" e project_id "base-x" em todos
    When a sincronização valida o escopo do lote
    Then o escopo lógico é aceito com tenant_id "cliente-a" e project_id "base-x"
    And a sincronização prossegue sem erro de escopo
```

#### AC-005 — lote com tenant_id divergente é recusado antes de mutação

**Cobre**: US-002, FR-003, NFR-001

```gherkin
@US-002 @FR-003 @NFR-001 @AC-005
Feature: Escopo lógico com tenant_id

  Scenario: Chunks do lote declaram tenant_id diferentes entre si
    Given um lote com chunks de tenant_id "cliente-a" e tenant_id "cliente-b"
    When a sincronização é chamada
    Then a validação de escopo rejeita o lote com InvalidSyncScopeError
    And nenhuma chamada ao cliente remoto é realizada
```

#### AC-006 — lote misto com e sem tenant_id é recusado antes de mutação

**Cobre**: US-002, FR-003, NFR-001

```gherkin
@US-002 @FR-003 @NFR-001 @AC-006
Feature: Escopo lógico com tenant_id

  Scenario: Parte do lote declara tenant_id e parte não declara
    Given um lote onde alguns chunks têm tenant_id "cliente-a" e outros não têm tenant_id
    When a sincronização é chamada
    Then a validação de escopo rejeita o lote com InvalidSyncScopeError
    And nenhuma chamada ao cliente remoto é realizada
```

#### AC-007 — remoção de obsoletos em modo espelho respeita o tenant_id

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-007
Feature: Escopo lógico com tenant_id

  Scenario: Dois tenants compartilham o mesmo project_id no destino remoto
    Given pontos remotos existentes de tenant_id "cliente-a" e tenant_id "cliente-b" no mesmo project_id
    When a sincronização em modo espelho conclui para o lote de tenant_id "cliente-a"
    Then somente pontos obsoletos de tenant_id "cliente-a" são removidos
    And os pontos de tenant_id "cliente-b" permanecem intactos
```

#### AC-008 — lote sem tenant_id preserva o comportamento atual

**Cobre**: US-002, FR-003, NFR-002

```gherkin
@US-002 @FR-003 @NFR-002 @AC-008
Feature: Escopo lógico com tenant_id

  Scenario: Nenhum chunk do lote declara tenant_id
    Given um lote de chunks sem tenant_id em nenhum metadata, como a base atual
    When a sincronização valida o escopo do lote
    Then o escopo é validado somente por project_id, como no comportamento atual
```

#### AC-009 — documento com status bloqueante é excluído da indexação

**Cobre**: US-003, FR-005, NFR-003

```gherkin
@US-003 @FR-005 @NFR-003 @AC-009
Feature: Bloqueio de indexação por status

  Scenario: Status do documento está na lista bloqueante configurada
    Given config.yaml com a lista bloqueante contendo "reprovado"
    And um documento com status "reprovado" no frontmatter
    When o pipeline processa o documento
    Then o documento não gera chunks indexados
    And o motivo da exclusão é registrado no log e no manifesto
```

#### AC-010 — documento com status fora da lista bloqueante é indexado normalmente

**Cobre**: US-003, FR-005, NFR-002

```gherkin
@US-003 @FR-005 @NFR-002 @AC-010
Feature: Bloqueio de indexação por status

  Scenario: Status do documento não está na lista bloqueante
    Given config.yaml com a lista bloqueante contendo "reprovado"
    And um documento com status "aprovado" no frontmatter
    When o pipeline processa o documento
    Then o documento é indexado normalmente
```

#### AC-011 — documento sem status é indexado normalmente (fail-open)

**Cobre**: US-003, FR-005, NFR-002

```gherkin
@US-003 @FR-005 @NFR-002 @AC-011
Feature: Bloqueio de indexação por status

  Scenario: Documento sem campo status no frontmatter
    Given um documento sem status no frontmatter, como os da base atual
    When o pipeline processa o documento
    Then o documento é indexado normalmente, sem alteração de comportamento
```

#### AC-012 — documento Q&A com splitter: qa divide por bloco ++++

**Cobre**: US-004, FR-006

```gherkin
@US-004 @FR-006 @AC-012
Feature: Chunking Q&A por blocos ++++

  Scenario: Documento Q&A com três blocos separados por ++++
    Given um documento com splitter "qa" no frontmatter e corpo com três blocos separados por ++++
    When o documento é chunkado
    Then exatamente três chunks são gerados
    And cada chunk corresponde a exatamente um bloco, sem corte por tamanho
```

#### AC-013 — documento Q&A que começa com ++++ não perde conteúdo

**Cobre**: US-004, FR-006

```gherkin
@US-004 @FR-006 @AC-013
Feature: Chunking Q&A por blocos ++++

  Scenario: Corpo do documento começa imediatamente com ++++
    Given um documento com splitter "qa" cujo corpo começa com ++++ logo após o frontmatter
    When o documento é carregado e chunkado
    Then nenhum bloco é descartado como frontmatter
    And todos os blocos do corpo aparecem como chunks
```

#### AC-014 — documento sem splitter: qa mantém comportamento mesmo com ++++ ou --- no corpo

**Cobre**: US-004, FR-007, NFR-002

```gherkin
@US-004 @FR-007 @NFR-002 @AC-014
Feature: Ativação explícita do splitter Q&A

  Scenario: Documento comum contém ++++ ou começa com --- no corpo
    Given um documento sem splitter "qa" no frontmatter cujo corpo contém ++++ ou começa com ---
    When o documento é carregado e chunkado
    Then o comportamento de parsing e chunking permanece o atual
    And nenhum tratamento especial de Q&A é aplicado
```

#### AC-015 — type e version aparecem no payload sem afetar identidade

**Cobre**: US-005, FR-008

```gherkin
@US-005 @FR-008 @AC-015
Feature: Passthrough de type e version

  Scenario: Documento declara type e version no frontmatter
    Given um documento com type "faq" e version "3" no frontmatter
    When o documento é chunkado
    Then todos os chunks do documento carregam type "faq" e version "3" no metadata
    And o chunk_id permanece determinado pelos demais campos, sem incluir type nem version
```

#### AC-016 — ausência de type/version preserva comportamento atual

**Cobre**: US-005, FR-008, NFR-002

```gherkin
@US-005 @FR-008 @NFR-002 @AC-016
Feature: Passthrough de type e version

  Scenario: Documento sem type nem version no frontmatter
    Given um documento sem type nem version no frontmatter, como os da base atual
    When o documento é chunkado
    Then nenhum campo type ou version aparece no metadata dos chunks
    And o processamento permanece idêntico ao comportamento atual
```

#### AC-017 — type e version não influenciam bloqueio nem escolha de splitter

**Cobre**: US-005, FR-008

```gherkin
@US-005 @FR-008 @AC-017
Feature: Passthrough de type e version

  Scenario: Documento declara type e version sem declarar status nem splitter
    Given um documento com type "procedimento", version "2" e sem status no frontmatter
    When o documento é processado
    Then a presença de type e version não altera a decisão de bloqueio
    And não altera a estratégia de chunking escolhida
```

#### AC-018 — remoção de obsoletos sem tenant_id no lote preserva filtro apenas por project_id

**Cobre**: US-002, FR-004, NFR-002

```gherkin
@US-002 @FR-004 @NFR-002 @AC-018
Feature: Escopo lógico com tenant_id

  Scenario: Sincronização em modo espelho sem tenant_id em nenhum chunk do lote
    Given um lote sem tenant_id em nenhum metadata, como a base atual
    When a sincronização em modo espelho conclui
    Then a remoção de obsoletos filtra somente por project_id, como no comportamento atual
```

#### AC-019 — bloco Q&A maior que chunk_size permanece inteiro

**Cobre**: US-004, FR-006

```gherkin
@US-004 @FR-006 @AC-019
Feature: Chunking Q&A por blocos ++++

  Scenario: Bloco Q&A ultrapassa o tamanho configurado de chunk
    Given um documento com splitter "qa" e um bloco entre ++++ maior que o chunk_size configurado
    When o documento é chunkado
    Then o bloco permanece como um único chunk
    And o splitter por caracteres não subdivide o bloco
```

#### AC-020 — documento sem splitter: qa com frontmatter delimitado por --- mantém parsing atual

**Cobre**: US-004, FR-007, NFR-002

```gherkin
@US-004 @FR-007 @NFR-002 @AC-020
Feature: Ativação explícita do splitter Q&A

  Scenario: Documento comum com frontmatter YAML no topo
    Given um documento sem splitter "qa" com frontmatter YAML delimitado por --- no topo
    When o documento é carregado
    Then o parsing de frontmatter continua funcionando exatamente como hoje
```

#### AC-021 — ausência de splitter: qa não ativa lógica Q&A mesmo com múltiplos blocos ++++

**Cobre**: US-004, FR-007

```gherkin
@US-004 @FR-007 @AC-021
Feature: Ativação explícita do splitter Q&A

  Scenario: Corpo com múltiplas ocorrências de ++++ sem splitter qa declarado
    Given um documento sem splitter "qa" cujo corpo contém múltiplas ocorrências de ++++
    When o documento é chunkado
    Then o splitter padrão configurado é aplicado
    And ++++ não é tratado como separador especial
```

#### AC-022 — log de bloqueio por status não expõe segredos

**Cobre**: US-003, FR-005, NFR-003

```gherkin
@US-003 @FR-005 @NFR-003 @AC-022
Feature: Bloqueio de indexação por status

  Scenario: Documento é excluído por status bloqueante
    Given um documento bloqueado por status presente na lista configurada
    When o pipeline registra o motivo da exclusão
    Then o registro contém o identificador do documento e o status
    And o registro não contém credencial nem valor de configuração sensível
```

#### AC-023 — manifesto reflete a contagem de documentos excluídos por status

**Cobre**: US-003, FR-005, NFR-003

```gherkin
@US-003 @FR-005 @NFR-003 @AC-023
Feature: Bloqueio de indexação por status

  Scenario: Execução com um documento bloqueado entre vários processados
    Given uma execução com um documento bloqueado por status entre vários documentos válidos
    When o manifesto da execução é gerado
    Then o manifesto registra a contagem de documentos excluídos por status
```

#### AC-024 — leitura de escopo não inclui pontos de outro tenant_id

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-024
Feature: Escopo lógico com tenant_id

  Scenario: Leitura do escopo existente antes do upsert
    Given pontos remotos existentes de tenant_id "cliente-a" e tenant_id "cliente-b" no mesmo project_id
    When a sincronização lê o escopo existente para o lote de tenant_id "cliente-a"
    Then a leitura retorna somente pontos de tenant_id "cliente-a"
    And pontos de tenant_id "cliente-b" não são contados como já indexados nem como candidatos à remoção
```

#### AC-025 — validação de tenant_id ocorre antes de qualquer cliente remoto ou embedding

**Cobre**: US-002, FR-003, NFR-001

```gherkin
@US-002 @FR-003 @NFR-001 @AC-025
Feature: Escopo lógico com tenant_id

  Scenario: Lote com tenant_id divergente antes de qualquer efeito remoto
    Given um lote com tenant_id divergente entre chunks
    When a sincronização é chamada
    Then a validação de escopo falha antes de qualquer instanciação de cliente do provider remoto
    And nenhum embedding é gerado
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve usar o `document_id` recebido no frontmatter
  como identidade do documento quando presente e não vazio; na ausência dele,
  deve manter a geração determinística atual a partir de `project_id` e
  caminho.
- **FR-002**: O sistema deve propagar o `document_id` resolvido (recebido ou
  gerado) para a composição do `chunk_id` de todos os chunks do documento,
  preservando unicidade dentro do escopo lógico.
- **FR-003**: O sistema deve validar, antes de qualquer mutação remota, que
  a totalidade do lote de sincronização declara o mesmo `tenant_id` ou que nenhum
  chunk do lote declara `tenant_id`; um lote com valores divergentes ou misto
  deve ser recusado.
- **FR-004**: Quando o lote declarar `tenant_id`, o sistema deve restringir a
  leitura de escopo e a remoção de obsoletos em modo espelho a
  `tenant_id + project_id`; na ausência de `tenant_id` no lote, deve manter o
  filtro atual por `project_id`.
- **FR-005**: O sistema deve excluir da indexação cada documento cujo
  `status` esteja presente em uma lista configurável de valores bloqueantes,
  registrando o motivo em log e no manifesto; documento com `status` ausente
  ou fora da lista deve ser indexado normalmente.
- **FR-006**: O sistema deve, para documento com `splitter: qa` no
  frontmatter, dividir o corpo pelo separador `++++` em exatamente um chunk
  por bloco não vazio, sem aplicar divisão por tamanho dentro de um bloco.
- **FR-007**: O sistema deve manter o comportamento de parsing e chunking
  atual para qualquer documento sem `splitter: qa` no frontmatter, mesmo que
  o corpo contenha `++++` ou comece com `---`.
- **FR-008**: O sistema deve incluir `type` e `version` do frontmatter, quando
  presentes, no metadata de todos os chunks do documento, sem que esses
  campos participem da composição do `chunk_id`, da decisão de bloqueio por
  `status` ou da escolha de estratégia de chunking.

#### Não funcionais

- **NFR-001**: Nenhuma mutação remota (upsert ou delete) deve ocorrer quando
  o escopo de `tenant_id` do lote for inválido (divergente ou misto).
  **Verificação**: teste unitário de `SyncSafetyPolicy` confirmando ausência
  de chamada ao cliente remoto antes da rejeição.
- **NFR-002**: A suíte de regressão existente deve permanecer verde após a
  mudança, e um documento sem frontmatter deve produzir a mesma contagem de
  chunks e os mesmos IDs de hoje. **Verificação**: `uv run pytest` completo e
  cenários dedicados de compatibilidade retroativa.
- **NFR-003**: Cada documento excluído por `status` bloqueante deve deixar
  rastro auditável (log estruturado e contagem no manifesto), sem expor
  credencial ou valor de configuração sensível. **Verificação**: inspeção do
  conteúdo do log e do manifesto em teste dedicado.

#### Erros e casos-limite

- Lote com `tenant_id` divergente entre chunks → `InvalidSyncScopeError`
  antes de qualquer chamada remota.
- Lote com mistura de chunks com e sem `tenant_id` → `InvalidSyncScopeError`
  antes de qualquer chamada remota.
- Documento com `splitter: qa` cujo corpo não contém nenhum `++++` → o
  documento inteiro vira um único chunk, tratado como um bloco só.
- Documento com frontmatter malformado para qualquer um dos cinco campos →
  segue o tratamento de erro já existente em `src/loader.py` (log e
  `metadata = {}` quando o YAML não parseia), sem ampliação nesta entrega.
- Lista bloqueante de `status` ausente ou vazia em `config.yaml` → nenhum
  documento é bloqueado (fail-open), preservando o comportamento atual.
- `tenant_id` presente no frontmatter mas vazio após normalização (string
  vazia ou apenas espaços, inclusive o resultado de `tenant_id: null` já
  sanitizado por `src/loader.py`) → tratado como ausente, pela mesma
  normalização (`_clean_identifier`) já aplicada a `project_id` e
  `chunk_id` em `src/safety.py`; não conta como declaração de `tenant_id`
  para a regra de uniformidade do lote.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

O pipeline é uma aplicação CLI Python modular. `src/loader.py` carrega
Markdown e extrai frontmatter YAML; `src/chunker.py` orquestra o chunking e
chama `src/identity.py` para atribuir identidade determinística;
`src/safety.py` concentra a política fail-closed de sincronização
(`SyncSafetyPolicy`, entregue pelo SPEC-0001); `src/embedder.py::index_chunks`
consome o escopo validado para ler, gravar e limpar pontos no Qdrant.
`src/manifest.py::build_manifest` consolida contagens para auditoria local.
O padrão já estabelecido de mesclar `doc.metadata` com o metadata específico
de cada chunk (`_split_by_headers` e `_split_by_characters`) é o mecanismo que
esta entrega reaproveita para propagar `type`, `version`, `tenant_id` e
`document_id` sem código adicional de repasse.

#### Arquitetura e módulos

- `src/identity.py`: `assign_document_identity` passa a preservar
  `document_id` já presente no metadata em vez de sobrescrevê-lo; a
  composição de `chunk_id` em `assign_chunk_identities` não muda de mecanismo,
  apenas herda o `document_id` resolvido.
- `src/safety.py`: `SyncSafetyPolicy.assert_valid_scope` passa a coletar
  `tenant_id` por chunk e a validar uniformidade, retornando `project_id` e
  `tenant_id` (ou `None`).
- `src/embedder.py`: `index_chunks` usa o `tenant_id` retornado para compor o
  filtro Qdrant (`project_filter`) usado em `scope_ids()`, tanto na leitura
  quanto na remoção de obsoletos.
- `src/chunker.py`: nova função `_split_by_qa` seguindo o mesmo padrão de
  `_split_by_headers`/`_split_by_characters` (mescla `doc.metadata`, gera um
  `Document` por bloco); `chunk_documents` passa a despachar para ela quando
  `doc.metadata.get("splitter") == "qa"`.
- `src/status_gate.py` (novo): função `filter_by_status(documents,
  blocked_statuses)` retornando os documentos mantidos e uma lista de
  registros de exclusão (`document_id`/`nome_arquivo`, `status`, motivo).
- `src/manifest.py`: `build_manifest` ganha um parâmetro opcional
  `excluded_documents` para registrar a contagem de exclusões por status,
  aditivo e compatível com as chamadas existentes.
- `config.yaml`: nova chave `contrato_markdown.status_bloqueado` (lista vazia
  por padrão).
- `pipeline.py`: insere a chamada a `filter_by_status` entre o carregamento
  (`load_markdown_documents`) e o chunking (`chunk_documents`), e repassa a
  lista de exclusões para `build_manifest`. O gate se aplica somente ao fluxo
  de carga original; `upsert_from_chunks.py` opera sobre `chunks.json` já
  filtrado por essa etapa e não precisa repetir a checagem.

#### Migrations

- Não aplicável. Nenhuma mudança de schema local ou remoto; nenhuma coleção
  ou namespace existente é alterado em sua estrutura.

#### Models

- Não há models ORM. As estruturas relevantes são o `Document` do LangChain
  (metadata como dicionário) e o manifesto (`src/manifest.py`), ambos
  estendidos de forma aditiva. Ver Modelo de dados (seção 9) para o contrato
  completo de metadata.

#### Controllers e casos de uso

- `pipeline.py::main`: entrada por `config.yaml` e argumentos de linha de
  comando; passa a incluir a etapa de bloqueio por status antes do chunking.
- `src/status_gate.py::filter_by_status`: entrada por documentos carregados e
  lista bloqueante; saída por documentos mantidos e registros de exclusão.
- `src/safety.py::SyncSafetyPolicy.assert_valid_scope`: entrada por chunks;
  saída por `project_id` e `tenant_id` validados, ou exceção antes de
  qualquer mutação.
- `src/embedder.py::index_chunks`: entrada por chunks e configuração; usa o
  escopo (incluindo `tenant_id`) para filtrar leitura e remoção no Qdrant.

#### Views e experiência

- Não aplicável. O componente não possui interface para pessoas; a
  experiência do operador acontece por mensagens de CLI e registros,
  detalhada na seção 10.

#### Queries e repositórios

- Leitura de escopo no Qdrant: `client.scroll` com filtro estendido para
  incluir `metadata.tenant_id` (via `FieldCondition`) quando o lote declarar
  `tenant_id`; mantém `metadata.project_id` sempre presente no filtro.
- Remoção de obsoletos: `client.delete` com `PointIdsList`, restrita ao
  mesmo escopo lido (`project_id` + `tenant_id` quando aplicável), após
  upsert completo — mecanismo do SPEC-0001 preservado sem alteração.
- Nenhuma nova query externa é introduzida; a extensão é apenas no filtro já
  existente.

#### Jobs e processamento assíncrono

- Não aplicável. A execução é síncrona por linha de comando.

#### Estrutura de arquivos

```text
specs/defined/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/
  spec.md
  research/
src/
  identity.py        # document_id do frontmatter tem precedência
  safety.py           # escopo estendido para tenant_id
  chunker.py           # novo _split_by_qa, despacho por splitter: qa
  embedder.py          # filtro Qdrant estendido para tenant_id
  status_gate.py        # novo: bloqueio de indexação por status
  manifest.py           # contagem de documentos excluídos por status
pipeline.py             # chama o gate de status antes do chunking
config.yaml              # nova lista contrato_markdown.status_bloqueado
tests/
  test_chunker.py       # document_id, splitter qa, passthrough type/version
  test_safety_policy.py  # escopo com tenant_id
  test_qdrant_sync.py     # remoção respeitando tenant_id
  test_status_gate.py      # novo: bloqueio por status
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Documento | `document_id` recebido ou determinístico, não vazio | `page_content`, frontmatter (`document_id`, `tenant_id`, `type`, `version`, `status`), `source_hash` | Origina um ou mais chunks; pertence a um `tenant_id` opcional |
| Chunk | `chunk_id` determinístico, único no escopo | `page_content`, `metadata.document_id`, `metadata.project_id`, `metadata.tenant_id` opcional, `metadata.type` opcional, `metadata.version` opcional, `chunk_type` | Pertence a um documento; vira um ponto no banco vetorial |
| Escopo lógico de sincronização | `project_id` + `tenant_id` opcional | Conjunto de IDs existentes no destino filtrado por ambos os campos quando `tenant_id` estiver em uso | Delimita o universo elegível a remoção; nunca cruza `tenant_id` quando declarado |
| Registro de exclusão por status | `nome_arquivo`/`caminho_relativo`, e `document_id` quando declarado no frontmatter | `status` observado, motivo, momento da exclusão | Não gera chunk; aparece apenas em log e no manifesto |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Documento | Carregado | `status` presente na lista bloqueante | Excluído da indexação | Nenhum chunk é gerado; exclusão registrada em log e manifesto |
| Documento | Carregado | `status` ausente ou fora da lista bloqueante | Segue para chunking | Comportamento idêntico ao atual |
| Execução de sincronização | Iniciada | `tenant_id` divergente ou misto no lote | Encerrada em erro | Nenhuma mutação remota emitida |
| Execução de sincronização | Validada | `tenant_id` uniforme (presente ou ausente) | Escopo confirmado | Leitura e remoção restritas ao escopo confirmado |
| Ponto do escopo | Existente, tenant_id "A" | Limpeza em modo espelho de tenant_id "A" | Reavaliado para remoção quando obsoleto | Nunca lido nem removido durante sincronização de tenant_id "B" |
| Chunk Q&A | Bloco entre `++++` | Chunking com `splitter: qa` | Um chunk por bloco | Nunca subdividido por tamanho |

#### Migração e retenção

- Não aplicável a esta entrega. Nenhum dado é migrado, reescrito ou
  expurgado. A primeira execução que adotar `document_id` externo para um
  documento já indexado gera novos `chunk_id` (ver AC-003); isso é uma
  reindexação completa e idempotente do Qdrant em modo espelho, não uma
  migração de schema.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. O componente é operado exclusivamente
  por linha de comando (`pipeline.py`, `upsert_from_chunks.py`), conforme
  `PROJECT.md` e `INTERFACE.md`. Esta entrega altera contrato de frontmatter,
  identidade, escopo de sincronização e chunking; nenhuma tela é criada ou
  modificada.

#### Stack e convenções de interface

- Não aplicável: não existe camada de interface neste componente.

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável. O operador interage por comando e lê o resultado nos
  registros de execução, no `chunks.json` e no manifesto.

#### Menus e navegação principal

- Não aplicável. Não há menu; o acesso é direto pelos comandos
  `uv run python pipeline.py` e `uv run python upsert_from_chunks.py`.

#### Formulários e ações

- Não aplicável. As entradas são o frontmatter dos documentos Markdown e
  `config.yaml` (nova lista `contrato_markdown.status_bloqueado`).

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável |

- Não aplicável: o projeto não é React e nenhuma biblioteca de interface é
  introduzida por esta entrega.

#### Estados e acessibilidade

- Não aplicável a telas. Os estados observáveis pelo operador são de
  terminal: documento excluído por status (mensagem específica), progresso de
  chunking e sincronização, e falha de escopo com mensagem e código de saída
  diferente de zero.

#### Contrato CRUD

- Não aplicável. Esta entrega não cria superfície CRUD.

#### Revisão visual durante o desenvolvimento

- Não aplicável, com motivo concreto: não existe superfície visual neste
  repositório. Cada tarefa registra `VISUAL: Não aplicável — componente CLI
  sem interface renderizada`.

#### APIs expostas

- `uv run python pipeline.py [--config CAMINHO] [--only-chunks|--skip-index]
  [--input-dir DIR]` — sem mudança de assinatura externa; passa a excluir
  documentos bloqueados por status antes do chunking.
- `src/status_gate.py::filter_by_status(documents, blocked_statuses)` —
  contrato interno novo, consumido por `pipeline.py`.
- `src/safety.py::SyncSafetyPolicy.assert_valid_scope(chunks)` — muda o tipo
  de retorno de `str` (`project_id`) para uma tupla `(project_id,
  tenant_id)`; quebra intencional de assinatura interna, registrada em
  `DEC-004`.
- `src/manifest.py::build_manifest(..., excluded_documents=None)` — parâmetro
  novo opcional, aditivo e retrocompatível.

#### APIs externas utilizadas

- Qdrant (`qdrant-client`): `scroll` e `delete` passam a incluir
  `metadata.tenant_id` no filtro quando aplicável; nenhuma chamada nova de
  API é introduzida.
- Nenhuma outra integração externa muda nesta entrega.

#### Documentação das APIs consultadas

- Nenhuma documentação externa consultada; o comportamento dos clientes foi
  confirmado no código local (`src/embedder.py`) e nos testes existentes.

#### Eventos e outros contratos

- Contrato do manifesto (`src/manifest.py`): ganha o campo aditivo
  `excluded_documents` (lista de `document_id`, `status`, motivo);
  compatibilidade aditiva, nenhum campo existente é removido.

### 11. Estratégia TDD

- **Unidade**: precedência de `document_id` e propagação para `chunk_id`
  (`src/identity.py` via `chunk_documents`); escopo com `tenant_id`
  (`SyncSafetyPolicy`); gate de status (`src/status_gate.py`); splitter Q&A e
  passthrough de `type`/`version` (`src/chunker.py`).
- **Integração/contrato**: remoção de obsoletos respeitando `tenant_id` em
  modo espelho Qdrant (`tests/test_qdrant_sync.py`).
- **BDD/aceite**: AC-001 a AC-023 na seção 6, usados para derivar cada caso
  TDD.
- **Runner TDD**: Pytest, já configurado no grupo `dev` de `pyproject.toml`.
- **E2E**: Não aplicável; a CLI já é exercitada ponta a ponta pelos testes de
  integração existentes.
- **Verificação manual**: Nenhuma inevitável; cada comportamento é
  verificável por teste automatizado.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, AC-001 | AC-001 na seção 6 | caso de precedência de document_id em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, FR-001, FR-002, NFR-002, AC-002 | AC-002 na seção 6 | caso de ausência de document_id em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, FR-001, FR-002, AC-003 | AC-003 na seção 6 | caso de reindexação consistente em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-002, FR-003, AC-004 | AC-004 na seção 6 | caso de lote uniforme com tenant_id em tests/test_safety_policy.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-002, FR-003, NFR-001, AC-005 | AC-005 na seção 6 | caso de tenant_id divergente em tests/test_safety_policy.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-002, FR-003, NFR-001, AC-006 | AC-006 na seção 6 | caso de lote misto em tests/test_safety_policy.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-002, FR-004, AC-007 | AC-007 na seção 6 | caso de remoção isolada por tenant_id em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-002, FR-004, AC-024 | AC-024 na seção 6 | caso de leitura de escopo isolada por tenant_id em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-002, FR-003, NFR-001, AC-025 | AC-025 na seção 6 | caso de validação antes de cliente/embedding em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-002, FR-003, NFR-002, AC-008 | AC-008 na seção 6 | caso de lote sem tenant_id em tests/test_safety_policy.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-002, FR-004, NFR-002, AC-018 | AC-018 na seção 6 | caso de remoção só por project_id em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-003, FR-005, NFR-003, AC-009 | AC-009 na seção 6 | caso de bloqueio por status em tests/test_status_gate.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-003, FR-005, NFR-002, AC-010 | AC-010 na seção 6 | caso de status fora da lista em tests/test_status_gate.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-003, FR-005, NFR-002, AC-011 | AC-011 na seção 6 | caso de ausência de status em tests/test_status_gate.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-003, FR-005, NFR-003, AC-022 | AC-022 na seção 6 | caso de log sem segredos em tests/test_status_gate.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-003, FR-005, NFR-003, AC-023 | AC-023 na seção 6 | caso de contagem no manifesto em tests/test_status_gate.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-004, FR-006, AC-012 | AC-012 na seção 6 | caso de três blocos Q&A em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-004, FR-006, AC-013 | AC-013 na seção 6 | caso de bloco inicial preservado em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-004, FR-006, AC-019 | AC-019 na seção 6 | caso de bloco maior que chunk_size em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-004, FR-007, NFR-002, AC-014 | AC-014 na seção 6 | caso de documento comum com ++++/--- em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-004, FR-007, NFR-002, AC-020 | AC-020 na seção 6 | caso de frontmatter padrão preservado em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-004, FR-007, AC-021 | AC-021 na seção 6 | caso de ativação só por splitter: qa em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-005, FR-008, AC-015 | AC-015 na seção 6 | caso de passthrough type/version em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-005, FR-008, NFR-002, AC-016 | AC-016 na seção 6 | caso de ausência de type/version em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-005, FR-008, AC-017 | AC-017 na seção 6 | caso de neutralidade de type/version em tests/test_chunker.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001, FR-002 | AC-001 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-001, FR-002, NFR-002 | AC-002 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-001, FR-002 | AC-003 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-003 | AC-004 | Unidade | `uv run pytest tests/test_safety_policy.py` | Pending |
| FR-003, NFR-001 | AC-005 | Unidade | `uv run pytest tests/test_safety_policy.py` | Pending |
| FR-003, NFR-001 | AC-006 | Unidade | `uv run pytest tests/test_safety_policy.py` | Pending |
| FR-004 | AC-007 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |
| FR-004 | AC-024 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |
| FR-003, NFR-001 | AC-025 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |
| FR-003, NFR-002 | AC-008 | Unidade | `uv run pytest tests/test_safety_policy.py` | Pending |
| FR-004, NFR-002 | AC-018 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |
| FR-005, NFR-003 | AC-009 | Unidade | `uv run pytest tests/test_status_gate.py` | Pending |
| FR-005, NFR-002 | AC-010 | Unidade | `uv run pytest tests/test_status_gate.py` | Pending |
| FR-005, NFR-002 | AC-011 | Unidade | `uv run pytest tests/test_status_gate.py` | Pending |
| FR-005, NFR-003 | AC-022 | Unidade | `uv run pytest tests/test_status_gate.py` | Pending |
| FR-005, NFR-003 | AC-023 | Unidade | `uv run pytest tests/test_status_gate.py` | Pending |
| FR-006 | AC-012 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-006 | AC-013 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-006 | AC-019 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-007, NFR-002 | AC-014 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-007, NFR-002 | AC-020 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-007 | AC-021 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-008 | AC-015 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-008, NFR-002 | AC-016 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |
| FR-008 | AC-017 | Unidade | `uv run pytest tests/test_chunker.py` | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (2026-09-01)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md --allow-draft` → `VALID DRAFT`; `node .agents/skills/specsfy-03-specify/scripts/load_research.mjs specs/defined/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md` → `PASSED`.
- **Achados**: Revisão semântica (lentes PROD/ARCH/SEC) encontrou quatro imprecisões corrigidas durante esta validação, nenhuma bloqueante ao final:
  - **FIND-ARCH-001** [P2] [Resolved] AC-004 e AC-007 citavam FR-004/NFR-001 em `**Cobre**` sem o cenário demonstrar essa propriedade — Refs: FR-004, NFR-001 — Evidence: spec.md §6 (AC-004, AC-007) — Effect: cobertura nominal, não real, entre requisito e teste — Suggestion/Resolução: removidas as tags indevidas e criados AC-024 (leitura de escopo isolada por tenant) e AC-025 (validação antes de cliente/embedding) como evidência genuína de FR-004 e NFR-001.
  - **FIND-PROD-001** [P3] [Resolved] entidade "Registro de exclusão por status" (seção 9) afirmava `document_id` como identidade, mas documentos excluídos por status nunca passam por `assign_document_identity` — Refs: FR-005 — Evidence: spec.md §9 — Effect: campo inexistente para documentos sem frontmatter — Suggestion/Resolução: identidade corrigida para `nome_arquivo`/`caminho_relativo`, com `document_id` apenas quando declarado.
  - **FIND-ARCH-002** [P3] [Resolved] escopo do gate de status entre `pipeline.py` e `upsert_from_chunks.py` não estava explícito — Refs: FR-005 — Evidence: spec.md §8 — Effect: ambiguidade de onde a checagem se aplica — Suggestion/Resolução: adicionada frase explícita de que o reupsert opera sobre `chunks.json` já filtrado.
  - **FIND-SEC-001** [P2] [Resolved] normalização de `tenant_id` vazio/nulo não estava definida para a regra de uniformidade do lote — Refs: FR-003 — Evidence: spec.md §7 (Erros e casos-limite) — Effect: implementação poderia tratar `tenant_id` vazio como declaração válida, quebrando o fallback para lote sem tenant — Suggestion/Resolução: adicionado caso explícito tratando string vazia/nula como ausência, pela mesma normalização de `project_id`/`chunk_id`.
  - Cobertura mínima confirmada por ferramenta: 5 US, 8 FR, 3 NFR, 25 AC; cada US/FR/NFR com ≥3 cenários em `**Cobre**` (`validate_spec.mjs` sem erros de `minimumBddErrors`).

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md`
- **Achados**: Pending.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md .`
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

#### Fase 1 — RED TDD informado pelo BDD (US-001, precedência de document_id)

- [ ] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso falhando em tests/test_chunker.py — Refs: US-001, FR-001, FR-002, AC-001 — Depends: none
  - [ ] **PREP**: Ler o AC-001 na seção 6 e confirmar o formato de frontmatter usado no caso.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-001`, afirmando que o `document_id` do frontmatter aparece no documento e em cada chunk.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso falhando em tests/test_chunker.py — Refs: US-001, FR-001, FR-002, NFR-002, AC-002 — Depends: none
  - [ ] **PREP**: Ler o AC-002 e confirmar o documento de referência sem frontmatter (base atual).
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-002`, afirmando `document_id` idêntico ao gerado hoje.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso falhando em tests/test_chunker.py — Refs: US-001, FR-001, FR-002, AC-003 — Depends: none
  - [ ] **PREP**: Ler o AC-003 e definir os dois processamentos sucessivos do mesmo documento.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-003`, afirmando `chunk_id` novo e determinístico entre execuções repetidas.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

#### Fase 2 — RED TDD informado pelo BDD (US-002, escopo com tenant_id — validação)

- [ ] T004 [TEST] [TDD] [US-002] Derivar do AC-004 um caso falhando em tests/test_safety_policy.py — Refs: US-002, FR-003, AC-004 — Depends: none
  - [ ] **PREP**: Ler o AC-004 e montar um lote com tenant_id uniforme.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-004`, afirmando aceitação do escopo com tenant_id e project_id retornados.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T005 [TEST] [TDD] [US-002] Derivar do AC-005 um caso falhando em tests/test_safety_policy.py — Refs: US-002, FR-003, NFR-001, AC-005 — Depends: none
  - [ ] **PREP**: Ler o AC-005 e montar um lote com tenant_id divergente entre chunks.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-005`, afirmando `InvalidSyncScopeError` sem chamada remota.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T006 [TEST] [TDD] [US-002] Derivar do AC-006 um caso falhando em tests/test_safety_policy.py — Refs: US-002, FR-003, NFR-001, AC-006 — Depends: none
  - [ ] **PREP**: Ler o AC-006 e montar um lote misto, com e sem tenant_id.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-006`, afirmando `InvalidSyncScopeError` sem chamada remota.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T007 [TEST] [TDD] [US-002] Derivar do AC-008 um caso falhando em tests/test_safety_policy.py — Refs: US-002, FR-003, NFR-002, AC-008 — Depends: none
  - [ ] **PREP**: Ler o AC-008 e montar um lote sem nenhum tenant_id (base atual).
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-008`, afirmando validação apenas por project_id, sem regressão.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

#### Fase 3 — RED TDD informado pelo BDD (US-002, escopo com tenant_id — leitura e remoção)

- [ ] T008 [TEST] [TDD] [US-002] Derivar do AC-007 um caso falhando em tests/test_qdrant_sync.py — Refs: US-002, FR-004, AC-007 — Depends: none
  - [ ] **PREP**: Ler o AC-007 e povoar o cliente falso com pontos de dois tenant_id no mesmo project_id.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-007`, afirmando remoção restrita ao tenant_id sincronizado.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T009 [TEST] [TDD] [US-002] Derivar do AC-018 um caso falhando em tests/test_qdrant_sync.py — Refs: US-002, FR-004, NFR-002, AC-018 — Depends: none
  - [ ] **PREP**: Ler o AC-018 e montar um lote sem tenant_id em modo espelho.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-018`, afirmando remoção filtrada só por project_id, sem regressão.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T010 [TEST] [TDD] [US-002] Derivar do AC-024 um caso falhando em tests/test_qdrant_sync.py — Refs: US-002, FR-004, AC-024 — Depends: none
  - [ ] **PREP**: Ler o AC-024 e povoar o cliente falso com pontos de dois tenant_id antes da leitura de escopo.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-024`, afirmando que a leitura de escopo retorna somente o tenant_id sincronizado.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T011 [TEST] [TDD] [US-002] Derivar do AC-025 um caso falhando em tests/test_qdrant_sync.py — Refs: US-002, FR-003, NFR-001, AC-025 — Depends: none
  - [ ] **PREP**: Ler o AC-025 e instrumentar o construtor de cliente remoto e o gerador de embeddings.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-025`, afirmando zero instanciações antes da rejeição do escopo inválido.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

#### Fase 4 — RED TDD informado pelo BDD (US-003, bloqueio por status)

- [ ] T012 [TEST] [TDD] [US-003] Derivar do AC-009 um caso falhando em tests/test_status_gate.py — Refs: US-003, FR-005, NFR-003, AC-009 — Depends: none
  - [ ] **PREP**: Ler o AC-009 e definir a lista bloqueante e o documento com status reprovado.
  - [ ] **EXECUTE**: Criar o arquivo de teste com marcador próprio `SPECSFY: AC-009`, afirmando ausência do módulo `src/status_gate.py` e exclusão esperada.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T013 [TEST] [TDD] [US-003] Derivar do AC-010 um caso falhando em tests/test_status_gate.py — Refs: US-003, FR-005, NFR-002, AC-010 — Depends: none
  - [ ] **PREP**: Ler o AC-010 e definir um status fora da lista bloqueante.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-010`, afirmando que o documento permanece indexado.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T014 [TEST] [TDD] [US-003] Derivar do AC-011 um caso falhando em tests/test_status_gate.py — Refs: US-003, FR-005, NFR-002, AC-011 — Depends: none
  - [ ] **PREP**: Ler o AC-011 e usar um documento sem campo status (base atual).
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-011`, afirmando indexação normal (fail-open).
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T015 [TEST] [TDD] [US-003] Derivar do AC-022 um caso falhando em tests/test_status_gate.py — Refs: US-003, FR-005, NFR-003, AC-022 — Depends: none
  - [ ] **PREP**: Ler o AC-022 e definir a captura do registro de exclusão via `caplog` ou equivalente.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-022`, afirmando presença do identificador e do status, e ausência de segredo.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T016 [TEST] [TDD] [US-003] Derivar do AC-023 um caso falhando em tests/test_status_gate.py — Refs: US-003, FR-005, NFR-003, AC-023 — Depends: none
  - [ ] **PREP**: Ler o AC-023 e montar uma execução com um documento bloqueado entre vários válidos.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-023`, afirmando a contagem de exclusões no manifesto.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

#### Fase 5 — RED TDD informado pelo BDD (US-004, chunking Q&A)

- [ ] T017 [TEST] [TDD] [US-004] Derivar do AC-012 um caso falhando em tests/test_chunker.py — Refs: US-004, FR-006, AC-012 — Depends: none
  - [ ] **PREP**: Ler o AC-012 e montar um documento com splitter "qa" e três blocos separados por `++++`.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-012`, afirmando exatamente três chunks, um por bloco.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T018 [TEST] [TDD] [US-004] Derivar do AC-013 um caso falhando em tests/test_chunker.py — Refs: US-004, FR-006, AC-013 — Depends: none
  - [ ] **PREP**: Ler o AC-013 e montar um documento com splitter "qa" cujo corpo começa imediatamente com `++++`.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-013`, afirmando que nenhum bloco é descartado.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T019 [TEST] [TDD] [US-004] Derivar do AC-014 um caso falhando em tests/test_chunker.py — Refs: US-004, FR-007, NFR-002, AC-014 — Depends: none
  - [ ] **PREP**: Ler o AC-014 e montar um documento sem splitter "qa" cujo corpo contém `++++` ou começa com `---`.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-014`, afirmando comportamento atual preservado.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T020 [TEST] [TDD] [US-004] Derivar do AC-019 um caso falhando em tests/test_chunker.py — Refs: US-004, FR-006, AC-019 — Depends: none
  - [ ] **PREP**: Ler o AC-019 e montar um bloco Q&A maior que o chunk_size configurado.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-019`, afirmando que o bloco permanece inteiro, sem subdivisão.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T021 [TEST] [TDD] [US-004] Derivar do AC-020 um caso falhando em tests/test_chunker.py — Refs: US-004, FR-007, NFR-002, AC-020 — Depends: none
  - [ ] **PREP**: Ler o AC-020 e montar um documento comum com frontmatter YAML delimitado por `---`.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-020`, afirmando parsing de frontmatter inalterado.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T022 [TEST] [TDD] [US-004] Derivar do AC-021 um caso falhando em tests/test_chunker.py — Refs: US-004, FR-007, AC-021 — Depends: none
  - [ ] **PREP**: Ler o AC-021 e montar um documento sem splitter "qa" com múltiplas ocorrências de `++++` no corpo.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-021`, afirmando que o splitter padrão é aplicado, ignorando `++++`.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

#### Fase 6 — RED TDD informado pelo BDD (US-005, passthrough de type/version)

- [ ] T023 [TEST] [TDD] [US-005] Derivar do AC-015 um caso falhando em tests/test_chunker.py — Refs: US-005, FR-008, AC-015 — Depends: none
  - [ ] **PREP**: Ler o AC-015 e montar um documento com type e version no frontmatter.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-015`, afirmando presença de type/version em todos os chunks sem alterar chunk_id.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T024 [TEST] [TDD] [US-005] Derivar do AC-016 um caso falhando em tests/test_chunker.py — Refs: US-005, FR-008, NFR-002, AC-016 — Depends: none
  - [ ] **PREP**: Ler o AC-016 e usar um documento sem type nem version (base atual).
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-016`, afirmando ausência desses campos e comportamento inalterado.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

- [ ] T025 [TEST] [TDD] [US-005] Derivar do AC-017 um caso falhando em tests/test_chunker.py — Refs: US-005, FR-008, AC-017 — Depends: none
  - [ ] **PREP**: Ler o AC-017 e montar um documento com type/version sem status nem splitter especial.
  - [ ] **EXECUTE**: Escrever o caso com marcador próprio `SPECSFY: AC-017`, afirmando neutralidade sobre bloqueio e escolha de splitter.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar cobertura e registrar aprendizado.

#### Fase 7 — US-001 Preservar a identidade do documento recebida do projeto-mãe (P1)

**Objetivo**: `document_id` do frontmatter vira identidade determinante.
**Teste independente**: `uv run pytest tests/test_chunker.py` verde para AC-001/AC-002/AC-003.

- [ ] T026 [CODE] [US-001] Implementar precedência de document_id em src/identity.py — Refs: US-001, FR-001, FR-002, AC-001, AC-002, AC-003 — Depends: T001, T002, T003
  - [ ] **PREP**: Confirmar RED de T001, T002 e T003; reconstruir e validar docs/ e .specsfy/PACKAGES.md com $specsfy-documentator antes de alterar produção.
  - [ ] **EXECUTE**: Ajustar `assign_document_identity` para preservar `document_id` já presente no metadata.
  - [ ] **VERIFY**: Executar testes focais e regressão de `tests/test_chunker.py`.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.

**Checkpoint**: reprocessar um documento com `document_id` conhecido e confirmar propagação em todos os chunks.

#### Fase 8 — US-002 Isolar a sincronização por tenant (P1)

**Objetivo**: escopo lógico de sincronização passa a incluir `tenant_id`.
**Teste independente**: `uv run pytest tests/test_safety_policy.py tests/test_qdrant_sync.py` verde.

- [ ] T027 [CODE] [US-002] Estender SyncSafetyPolicy.assert_valid_scope para tenant_id em src/safety.py — Refs: US-002, FR-003, AC-004, AC-005, AC-006, AC-008 — Depends: T004, T005, T006, T007
  - [ ] **PREP**: Confirmar RED de T004, T005, T006 e T007; reconstruir e validar docs/ e .specsfy/PACKAGES.md com $specsfy-documentator antes de alterar produção.
  - [ ] **EXECUTE**: Coletar `tenant_id` por chunk, validar uniformidade e retornar `(project_id, tenant_id)`.
  - [ ] **VERIFY**: Executar testes focais de `tests/test_safety_policy.py`.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.

- [ ] T028 [CODE] [US-002] Filtrar leitura e remoção de obsoletos por tenant_id em src/embedder.py — Refs: US-002, FR-003, FR-004, NFR-001, AC-007, AC-018, AC-024, AC-025 — Depends: T008, T009, T010, T011, T027
  - [ ] **PREP**: Confirmar RED de T008, T009, T010 e T011, e GREEN de T027; reconstruir e validar docs/ e .specsfy/PACKAGES.md com $specsfy-documentator antes de alterar produção.
  - [ ] **EXECUTE**: Compor `project_filter` com `metadata.tenant_id` quando presente, propagando para `scope_ids()`.
  - [ ] **VERIFY**: Executar testes focais de `tests/test_qdrant_sync.py`.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.

**Checkpoint**: sincronizar dois tenants no mesmo project_id e confirmar isolamento na remoção.

#### Fase 9 — US-003 Bloquear indexação por status configurável (P2)

**Objetivo**: documento com status bloqueante é excluído antes do chunking.
**Teste independente**: `uv run pytest tests/test_status_gate.py` verde.

- [ ] T029 [CODE] [US-003] Criar src/status_gate.py e integrar em pipeline.py e config.yaml — Refs: US-003, FR-005, NFR-003, AC-009, AC-010, AC-011, AC-022, AC-023 — Depends: T012, T013, T014, T015, T016
  - [ ] **PREP**: Confirmar RED de T012 a T016; reconstruir e validar docs/ e .specsfy/PACKAGES.md com $specsfy-documentator antes de alterar produção.
  - [ ] **EXECUTE**: Implementar `filter_by_status`, adicionar `contrato_markdown.status_bloqueado` em `config.yaml`, chamar o gate em `pipeline.py` entre carregamento e chunking, e estender `build_manifest` com `excluded_documents`.
  - [ ] **VERIFY**: Executar testes focais de `tests/test_status_gate.py` e regressão de `tests/test_manifest.py`.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.

**Checkpoint**: configurar um status bloqueante e confirmar exclusão registrada em log e manifesto.

#### Fase 10 — US-004 Processar documentos Q&A por blocos ++++ (P1)

**Objetivo**: `splitter: qa` divide o corpo por `++++` em um chunk por bloco.
**Teste independente**: `uv run pytest tests/test_chunker.py` verde para AC-012/AC-013/AC-014/AC-019/AC-020/AC-021.

- [ ] T030 [CODE] [US-004] Implementar _split_by_qa e despacho por splitter: qa em src/chunker.py — Refs: US-004, FR-006, FR-007, AC-012, AC-013, AC-014, AC-019, AC-020, AC-021 — Depends: T017, T018, T019, T020, T021, T022
  - [ ] **PREP**: Confirmar RED de T017 a T022; reconstruir e validar docs/ e .specsfy/PACKAGES.md com $specsfy-documentator antes de alterar produção.
  - [ ] **EXECUTE**: Criar `_split_by_qa` seguindo o padrão de mesclagem de metadata dos splitters existentes; despachar em `chunk_documents` quando `doc.metadata.get("splitter") == "qa"`.
  - [ ] **VERIFY**: Executar testes focais e regressão completa de `tests/test_chunker.py`.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.

**Checkpoint**: processar um documento Q&A de três blocos e confirmar três chunks íntegros.

#### Fase 11 — US-005 Preservar type e version como metadado auditável (P2)

**Objetivo**: `type` e `version` aparecem no payload sem afetar processamento.
**Teste independente**: `uv run pytest tests/test_chunker.py` verde para AC-015/AC-016/AC-017.

- [ ] T031 [CODE] [US-005] Confirmar e, se necessário, ajustar passthrough de type/version em src/chunker.py — Refs: US-005, FR-008, AC-015, AC-016, AC-017 — Depends: T023, T024, T025
  - [ ] **PREP**: Confirmar RED de T023, T024 e T025, e verificar se o merge de metadata existente já propaga os campos; reconstruir e validar docs/ e .specsfy/PACKAGES.md com $specsfy-documentator antes de alterar produção.
  - [ ] **EXECUTE**: Ajustar apenas se o RED revelar lacuna; caso o merge já propague, documentar a confirmação sem alterar código de produção.
  - [ ] **VERIFY**: Executar testes focais de `tests/test_chunker.py`.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados (ou ausência de alteração).
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.

**Checkpoint**: processar um documento com type/version e confirmar presença em todos os chunks sem efeito colateral.

#### Fase 12 — Contexto persistente do projeto

- [ ] T032 [DOC] Atualizar tenant_id, document_id e status na entidade de chunk em .specsfy/DATABASE.md — Refs: FR-001, FR-002, FR-003, FR-004, FR-005, FR-008 — Depends: T026, T027, T028, T029, T031
  - [ ] **PREP**: Confirmar os campos de metadata efetivamente implementados (document_id, tenant_id, status, type, version) e seu efeito no escopo lógico.
  - [ ] **EXECUTE**: Atualizar o inventário tabular de `.specsfy/DATABASE.md` com os novos campos e a regra de escopo por tenant_id, preservando decisões humanas existentes.
  - [ ] **VERIFY**: Revisar que a tabela reflete exatamente o código entregue, sem inferência não confirmada.
  - [ ] **VISUAL**: Não aplicável — documento técnico, sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar o diff aplicado a `.specsfy/DATABASE.md`.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.

#### Fase final — Qualidade

- [ ] T033 [TEST] Executar regressão completa e rastreabilidade sobre tests/test_chunker.py, tests/test_safety_policy.py, tests/test_qdrant_sync.py e tests/test_status_gate.py — Refs: US-001, US-002, US-003, US-004, US-005, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, NFR-001, NFR-002, NFR-003 — Depends: T026, T027, T028, T029, T030, T031, T032
  - [ ] **PREP**: Identificar suites, checks e gates aplicáveis.
  - [ ] **EXECUTE**: Executar `uv run pytest` completo e os scripts de rastreabilidade de `specsfy-06-tdd-bdd`.
  - [ ] **VERIFY**: Confirmar ausência de gaps entre AC, teste e implementação.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar contagens e comandos finais; revisar `PROJECT.md` quanto às capacidades de identidade, tenant e Q&A agora suportadas, registrando a revisão ou a ausência de impacto material.
  - [ ] **IMPROVE**: Registrar retrospectiva do processo.

### 15. Ordem de execução

- Caminho crítico: T001/T002/T003 → T026; T004/T005/T006/T007 → T027 →
  T008/T009/T010/T011 → T028; T012/T013/T014/T015/T016 → T029;
  T017/T018/T019/T020/T021/T022 → T030; T023/T024/T025 → T031;
  T026/T027/T028/T029/T031 → T032; todos → T033.
- Tarefas paralelas: T001 a T025 são as 25 tarefas RED, uma por cenário `AC`;
  são independentes entre si (fases de features distintas) e podem ser
  executadas em qualquer ordem ou em paralelo. Entre as tarefas `[CODE]`,
  T026, T027 e T029 também são independentes entre si.
- Estratégia de MVP: US-001 e US-004 (P1) entregam o valor central —
  identidade e formato Q&A. US-002 (P1) fecha o risco de segurança
  multi-tenant. US-003 e US-005 (P2) podem seguir depois sem bloquear a
  integração básica.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Nenhuma. Não depende de código ainda não entregue de outro backlog do M0.

#### Riscos

- A primeira execução após adotar `document_id` externo para um documento já
  indexado força reindexação completa desse documento (novos `chunk_id`) →
  mitigação: comunicar ao operador antes da mudança entrar em produção,
  aproveitando que o modo espelho é idempotente e seguro (SPEC-0001).
- Extensão do escopo lógico para `tenant_id` muda o retorno de
  `assert_valid_scope` → mitigação: `DEC-004` documenta a quebra de
  assinatura interna e T009 atualiza o único chamador conhecido
  (`src/embedder.py`).

#### Suposições

- Os valores permitidos de `type` e `status` permanecem em aberto até o
  projeto-mãe publicar seu contrato; esta entrega não os fixa, e a lista
  bloqueante de `status` é configurável justamente para acomodar essa
  incerteza sem exigir nova mudança de código.
- `project_id` continua vindo de `config.yaml` (`projeto.nome`), não do
  frontmatter; essa fonte é tratada por outro item (BACKLOG-0004) e está
  fora do escopo desta entrega.

### 17. Decisões

- **DEC-001**: `document_id` do frontmatter prevalece sobre a identidade
  local — decisão confirmada na descoberta do backlog; alternativa
  descartada foi manter a identidade local e gravar a origem como
  `source_document_id`, rejeitada por não sustentar correlação direta com o
  projeto-mãe.
- **DEC-002**: `tenant_id` é opcional, mas estrito quando presente (tudo ou
  nada no lote) — alternativa descartada foi torná-lo obrigatório, rejeitada
  por inviabilizar a base atual sem frontmatter.
- **DEC-003**: `status` bloqueia por lista configurável vazia por padrão
  (fail-open) — alternativa descartada foi uma lista fixa nesta spec,
  rejeitada por antecipar valores que o projeto-mãe ainda não definiu.
- **DEC-004**: `SyncSafetyPolicy.assert_valid_scope` muda de retornar `str`
  para retornar uma tupla `(project_id, tenant_id)` — quebra intencional de
  assinatura interna; único chamador (`src/embedder.py`) é atualizado na
  mesma entrega.
- **DEC-005**: separador de blocos Q&A é `++++`, não `---` — decisão do
  usuário durante a descoberta, que elimina na raiz a colisão com o
  delimitador de frontmatter YAML em vez de contornar o bug no parser.
- **DEC-006**: splitter Q&A ativa somente por `splitter: qa` explícito no
  frontmatter — alternativa descartada foi detecção automática pela
  presença de `++++` no corpo, rejeitada por criar comportamento implícito e
  difícil de prever.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
