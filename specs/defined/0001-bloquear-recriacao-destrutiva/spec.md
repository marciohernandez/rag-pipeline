# Especificação integrada: Bloquear recriação destrutiva e garantir sincronização segura

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0001 |
| Slug | 0001-bloquear-recriacao-destrutiva |
| Status | Defined |
| Effort | 6 |
| Effort updated at | 2026-09-01T01:03:53.659Z |
| Effort rationale | Revisão semântica acrescentou FR-007, três cenários e a guarda de remoção total, além de encapsular a política em SyncSafetyPolicy; o alcance passou de sete para dez arquivos entre código, testes e documentação. |
| ClickUp Task | |
| Milestones | M0 — Finalizar o componente rag-ingestion-pipeline |
| Definition Gate | Passed |
| Plan Gate | Pending |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-08-31 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O componente expõe hoje um caminho executável capaz de apagar amplamente a base
vetorial remota. A flag `--recreate` existe em `pipeline.py:51` e em
`upsert_from_chunks.py:39`, chega a `index_chunks` em `src/embedder.py:203` e
resulta em `client.delete_collection(collection)` no Qdrant
(`src/embedder.py:286-288`) ou em `index.delete(delete_all=True, namespace=...)`
no Pinecone (`src/embedder.py:394-399`).

A documentação operacional reforça esse caminho como procedimento normal e até
como forma de recuperação: `README.md:65`, `GUIA_DE_USO.md:519`,
`GUIA_DE_USO.md:543-550`, `GUIA_DE_USO.md:634`, `GUIA_DE_USO.md:663`,
`config.yaml:183` e `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md:425-437`.

Isso contraria o limite declarado em `PROJECT.md` ("operações remotas
destrutivas, incluindo recriação de coleção, exigem decisão explícita fora do
fluxo normal de sincronização") e a regra de operação de `.specsfy/RULES.md`.
Um erro de digitação no nome da collection, um `config.yaml` apontando para o
destino errado ou a simples repetição do procedimento documentado de
recuperação bastam para destruir a base de um cliente.

#### Resultado desejado

Nenhum fluxo normal do componente consegue recriar ou apagar amplamente a base
remota. O operador continua sincronizando de forma incremental e idempotente,
recebe erro explícito e sem mutação ao tentar a opção antiga, e encontra na
documentação apenas caminhos de atualização e recuperação não destrutivos.

#### Métricas de sucesso

- Zero chamadas de exclusão ampla (`delete_collection`, `delete_all`, remoção de
  índice ou namespace) alcançáveis pelo código de produção, comprovado por busca
  estática e por teste com cliente falso que registra chamadas.
- 100% das tentativas de uso da flag antiga terminam com código de saída
  diferente de zero e nenhuma chamada de mutação remota registrada.
- Zero ocorrências de `--recreate` como procedimento recomendado em `README.md`,
  `GUIA_DE_USO.md`, `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md` e `config.yaml`.
- Reexecução do pipeline sobre a mesma entrada mantém a contagem de pontos do
  escopo estável, com `inseridos = 0` e `removidos = 0` no registro da execução.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001** [critical] O caminho destrutivo é alcançável pelo fluxo normal das duas CLIs e termina em exclusão remota — Verdict: verified — Confidence: high — Evidence: research/auditoria-codigo/caminhos-destrutivos.md#caminho-destrutivo-alcancavel-pela-cli — Budget: 1/8
- **R-002** [critical] O modo espelho do Qdrant já limita a remoção ao `project_id` da execução e só ocorre depois do laço de upsert — Verdict: verified — Confidence: high — Evidence: research/auditoria-codigo/caminhos-destrutivos.md#modo-espelho-no-qdrant — Budget: 1/8
- **R-003** [critical] ChromaDB e Pinecone não possuem sincronização espelho equivalente neste componente e sequer leem `sync_mode` — Verdict: verified — Confidence: high — Evidence: research/auditoria-codigo/caminhos-destrutivos.md#providers-sem-paridade-de-espelho — Budget: 1/8
- **R-004** [high] A documentação publicada apresenta a recriação como procedimento de atualização e de recuperação — Verdict: verified — Confidence: high — Evidence: research/auditoria-codigo/caminhos-destrutivos.md#documentacao-que-recomenda-recriacao — Budget: 1/8

#### Fontes e contexto consultados

- `specs/backlog/0001-bloquear-recriacao-destrutiva.md`: brief refinado que originou esta spec.
- `pipeline.py`, `upsert_from_chunks.py`, `src/embedder.py`, `src/manifest.py`, `src/identity.py`: caminhos executáveis atuais.
- `tests/test_qdrant_sync.py`: cobertura existente do modo espelho.
- `PROJECT.md`, `.specsfy/RULES.md`, `.specsfy/STACK.md`, `.specsfy/DATABASE.md`: limites, regras e mapa de persistência confirmados.
- `README.md`, `GUIA_DE_USO.md`, `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md`, `config.yaml`: orientações operacionais publicadas.
- Linear `LEAD-88`: tracking do item no milestone M0.

#### Documentação consultada

- Nenhuma documentação externa foi consultada. Toda a evidência desta spec vem de arquivos deste repositório, copiados para `research/` porque esta própria entrega os altera.

#### Artefatos de pesquisa armazenados

- `specs/defined/0001-bloquear-recriacao-destrutiva/research/auditoria-codigo/caminhos-destrutivos.md`: trechos literais de `pipeline.py`, `upsert_from_chunks.py`, `src/embedder.py`, `README.md`, `GUIA_DE_USO.md`, `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md` e `config.yaml` no commit `5ba9a56`, lidos em 2026-08-31. Licença: código e documentação próprios do projeto, cópia integral permitida. Propósito: preservar o estado auditado, já que a implementação desta spec remove justamente esses trechos.

#### Dúvidas respondidas

- **Q**: Remover a flag antiga silenciosamente ou mantê-la como erro explícito? → **A**: Mantê-la reconhecida apenas para produzir erro de migração. Uma flag desconhecida no `argparse` já falha, mas com mensagem genérica; o erro explícito ensina o caminho seguro e evita que o operador procure outra forma de destruir a base. Registrado em `DEC-001`.
- **Q**: O modo espelho pode permanecer disponível? → **A**: Sim, no Qdrant, porque a remoção já é filtrada por `project_id` e posterior ao upsert. A garantia passa a ser explícita e testada. Registrado em `DEC-002`.
- **Q**: O que fazer com ChromaDB e Pinecone, que não têm paridade? → **A**: Bloqueio conservador. `sync_mode: mirror` é recusado antes de qualquer mutação nesses providers; eles continuam suportados apenas em modo `append`. Registrado em `DEC-003`.
- **Q**: A recuperação operacional passa a ser qual? → **A**: Nova execução idempotente do pipeline, apoiada pelo manifesto e por diagnóstico; nenhuma orientação de apagar a base. Registrado em `DEC-004`.

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Remoção do caminho destrutivo em `pipeline.py`, `upsert_from_chunks.py` e `src/embedder.py`.
- Erro explícito de migração quando a opção antiga for usada, antes de qualquer conexão, embedding ou mutação.
- Garantia testada de que o modo espelho só remove pontos obsoletos do `project_id` da execução e somente após upsert completo e bem-sucedido.
- Bloqueio conservador do modo espelho em providers sem garantia comprovada (ChromaDB e Pinecone).
- Bloqueio da sincronização cujo efeito prático seria a remoção total do escopo lógico.
- Registro auditável da sincronização com modo, escopo lógico e contagens, sem segredos.
- Atualização de `README.md`, `GUIA_DE_USO.md`, `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md` e dos comentários de `config.yaml`.
- Testes Pytest que comprovam o comportamento fail-closed.

#### Fora de escopo

- Contrato multi-tenant completo e `tenant_id` persistente (BACKLOG-0002).
- Modularização dos providers por Factory/Adapter (BACKLOG-0003).
- Remoção dos hardcodes de cliente (BACKLOG-0004).
- Identidade estável e idempotência no caminho ChromaDB, que hoje duplica registros a cada execução; a correção exige mudar a forma de escrita desse provider e é encaminhada ao BACKLOG-0003.
- Migração de dados entre providers e backup administrado pelo fornecedor.
- Autenticação, autorização e interface web.
- Qualquer ferramenta administrativa nova que execute exclusão ampla sob confirmação.

#### Atores

- **Operador do pipeline**: executa `pipeline.py` e `upsert_from_chunks.py` por linha de comando para preparar e atualizar bases vetoriais de clientes. Não deve dispor de caminho destrutivo no fluxo normal.
- **Mantenedor do componente**: evolui o código e depende de testes que impeçam a reintrodução do caminho destrutivo.
- **Integração futura `rag-pipeline`**: consumirá esta camada e herda a garantia de sincronização segura.

### 4. Princípios e restrições do projeto

- **PR-001**: Falhar fechado. Qualquer escopo, configuração ou manifesto inválido interrompe a execução antes de qualquer mutação remota (`PROJECT.md`, limites).
- **PR-002**: Operações remotas destrutivas ficam fora do fluxo normal de sincronização e não são oferecidas como caminho de recuperação (`PROJECT.md`, `.specsfy/RULES.md`).
- **PR-003**: Cada execução de sincronização registra modo, escopo lógico e contagens de pontos previstos, inseridos, mantidos e removidos, sem credenciais, tokens ou URLs de destino (`.specsfy/RULES.md`, Operação).
- **PR-004**: Componentes críticos seguem Red-Green-Refactor, com teste escrito antes da implementação, e Ruff mais Pytest verdes antes da integração (`.specsfy/RULES.md`, Testes e Código e qualidade).
- **PR-005**: Configuração sensível permanece fora do repositório e o acesso é centralizado (`.specsfy/RULES.md`, Segurança e privacidade).
- **PR-006**: Nenhuma biblioteca de interface é introduzida neste componente; ele permanece operado por CLI (`INTERFACE.md`, Base observada).

### 5. Histórias de usuário

#### US-001 — Sincronizar sem risco de perda ampla (P1)

Como operador do pipeline, quero que a sincronização atualize somente o escopo
lógico da execução, para nunca destruir dados válidos de outro projeto nem
perder a base ao repetir um comando.

**Por que P1**: é a proteção que separa uma atualização rotineira de uma perda
irreversível de base de cliente; bloqueia a conclusão do milestone M0.
**Teste independente**: executar o pipeline duas vezes sobre a mesma entrada e
observar contagem estável, `inseridos = 0` e `removidos = 0` na segunda
execução, com pontos de outro `project_id` intactos.
**Requisitos**: FR-003, FR-004, FR-005, FR-007, NFR-001, NFR-003

#### US-002 — Receber erro claro ao usar a opção antiga (P1)

Como operador do pipeline, quero que o comando destrutivo antigo falhe com uma
mensagem que explique o caminho seguro, para não procurar outra forma de
recriar a base.

**Por que P1**: o comando está publicado em README, guia e comentários de
configuração; sem erro explícito o operador repete o procedimento antigo.
**Teste independente**: executar `pipeline.py --recreate` e observar código de
saída diferente de zero, mensagem de migração e nenhuma conexão remota aberta.
**Requisitos**: FR-001, FR-002, NFR-001

#### US-003 — Recuperar uma base inconsistente sem apagar tudo (P1)

Como operador do pipeline, quero um procedimento de recuperação baseado em nova
execução idempotente e no manifesto, para corrigir uma base sem destruí-la.

**Por que P1**: hoje a documentação orienta explicitamente a recriação como
recuperação; sem substituir esse procedimento a proteção do código é contornada
pelo próprio guia.
**Teste independente**: seguir o procedimento publicado de recuperação e
confirmar que ele usa apenas execução idempotente, manifesto e diagnóstico.
**Requisitos**: FR-005, FR-006, NFR-002, NFR-003

### 6. Cenários BDD de aceite

#### AC-001 — Opção destrutiva rejeitada antes de qualquer mutação

**Cobre**: US-002, FR-001, FR-002, NFR-001

```gherkin
@US-002 @FR-001 @FR-002 @NFR-001 @AC-001
Feature: Bloqueio da opção de recriação

  Scenario: Execução com a flag antiga termina sem mutação
    Given uma configuração válida apontando para um banco vetorial remoto
    When o operador executa o pipeline com a opção de recriação
    Then a execução termina com código de saída diferente de zero
    And nenhuma exclusão de collection, índice ou namespace é solicitada
```

#### AC-002 — Nenhum cliente remoto nem embedding é criado na rejeição

**Cobre**: US-002, FR-001, FR-002, NFR-001

```gherkin
@US-002 @FR-001 @FR-002 @NFR-001 @AC-002
Feature: Bloqueio da opção de recriação

  Scenario: Rejeição ocorre antes de conectar e de gerar embeddings
    Given uma configuração válida apontando para um banco vetorial remoto
    When o operador executa o pipeline com a opção de recriação
    Then nenhum cliente de banco vetorial é instanciado
    And nenhuma chamada de geração de embeddings é realizada
```

#### AC-003 — Mensagem de migração indica o caminho seguro

**Cobre**: US-002, US-003, FR-001, FR-006

```gherkin
@US-002 @US-003 @FR-001 @FR-006 @AC-003
Feature: Bloqueio da opção de recriação

  Scenario: Erro explica a substituição do procedimento antigo
    Given um operador acostumado ao procedimento anterior de recriação
    When ele executa o pipeline com a opção de recriação
    Then a mensagem informa que a opção foi removida por política de segurança
    And indica a sincronização idempotente como caminho de atualização e recuperação
```

#### AC-004 — Reexecução idempotente não altera a base

**Cobre**: US-001, FR-003, NFR-002, NFR-003

```gherkin
@US-001 @FR-003 @NFR-002 @NFR-003 @AC-004
Feature: Sincronização incremental segura

  Scenario: Mesma entrada processada duas vezes
    Given uma execução anterior concluída para o mesmo project_id
    When os mesmos documentos são processados novamente
    Then nenhum ponto duplicado é criado
    And nenhum ponto válido é removido
    And o registro da execução informa zero pontos inseridos e zero removidos
```

#### AC-005 — Falha de upsert impede a limpeza de obsoletos

**Cobre**: US-001, FR-003, FR-004, NFR-001

```gherkin
@US-001 @FR-003 @FR-004 @NFR-001 @AC-005
Feature: Sincronização incremental segura

  Scenario: Upsert incompleto interrompe a execução
    Given pontos válidos e obsoletos no escopo do project_id da execução
    When o upsert de um lote de pontos atuais falha
    Then a execução termina em erro
    And a remoção dos pontos obsoletos não é iniciada
```

#### AC-006 — Isolamento entre projetos no modo espelho

**Cobre**: US-001, FR-003, FR-004, NFR-003

```gherkin
@US-001 @FR-003 @FR-004 @NFR-003 @AC-006
Feature: Sincronização incremental segura

  Scenario: Dois project_id na mesma collection
    Given pontos de dois project_id distintos na mesma collection
    When a sincronização em modo espelho conclui para um deles
    Then somente pontos obsoletos daquele project_id são removidos
    And todos os pontos do outro project_id permanecem inalterados
```

#### AC-007 — Escopo inválido bloqueia qualquer remoção

**Cobre**: US-001, US-003, FR-004, NFR-001

```gherkin
@US-001 @US-003 @FR-004 @NFR-001 @AC-007
Feature: Sincronização incremental segura

  Scenario: Escopo lógico ausente, vazio ou divergente
    Given uma execução cujo project_id está ausente, vazio ou divergente entre os chunks
    When a sincronização é solicitada
    Then a execução termina em erro antes de qualquer mutação remota
    And nenhuma remoção de pontos é solicitada
```

#### AC-008 — Modo espelho recusado em provider sem garantia

**Cobre**: US-001, FR-002, FR-005, NFR-001

```gherkin
@US-001 @FR-002 @FR-005 @NFR-001 @AC-008
Feature: Limite conservador por provider

  Scenario: Espelho pedido em provider sem sincronização comprovada
    Given uma configuração com sync_mode espelho e um provider sem essa garantia
    When a indexação é iniciada
    Then a execução termina em erro antes de qualquer mutação remota
    And a mensagem indica quais providers suportam o modo espelho
```

#### AC-009 — Provider sem garantia continua utilizável em modo append

**Cobre**: US-003, FR-002, FR-005, NFR-003

```gherkin
@US-003 @FR-002 @FR-005 @NFR-003 @AC-009
Feature: Limite conservador por provider

  Scenario: Indexação incremental permanece disponível
    Given uma configuração com sync_mode append em um provider sem garantia de espelho
    When a indexação é executada
    Then os pontos atuais são adicionados normalmente
    And nenhuma exclusão de dados existentes é solicitada
```

#### AC-010 — Registro auditável da sincronização

**Cobre**: US-001, FR-003, FR-006, NFR-002

```gherkin
@US-001 @FR-003 @FR-006 @NFR-002 @AC-010
Feature: Auditoria da sincronização

  Scenario: Execução concluída deixa registro verificável
    Given uma sincronização concluída com sucesso
    When o operador consulta o registro da execução
    Then encontra o modo, o escopo lógico e as contagens de pontos previstos, inseridos, mantidos e removidos
    And não encontra credenciais, tokens ou URL do destino remoto
```

#### AC-011 — Documentação e configuração sem caminho destrutivo

**Cobre**: US-003, FR-005, FR-006, NFR-002

```gherkin
@US-003 @FR-005 @FR-006 @NFR-002 @AC-011
Feature: Documentação operacional segura

  Scenario: Operador procura como atualizar a base
    Given os guias, o README e os comentários de configuração publicados no repositório
    When o operador procura o procedimento de atualização
    Then encontra somente fluxos idempotentes
    And não encontra nenhuma orientação para recriar ou limpar amplamente o destino remoto
```

#### AC-012 — Recuperação por nova execução idempotente

**Cobre**: US-003, FR-001, FR-006, NFR-002, NFR-003

```gherkin
@US-003 @FR-001 @FR-006 @NFR-002 @NFR-003 @AC-012
Feature: Documentação operacional segura

  Scenario: Operador procura como recuperar uma base inconsistente
    Given uma base vetorial suspeita de inconsistência
    When o operador consulta o procedimento de recuperação publicado
    Then encontra a reexecução idempotente apoiada pelo manifesto e pelo diagnóstico
    And não encontra a recriação da base como alternativa
```

#### AC-013 — Conjunto esperado vazio bloqueia a execução

**Cobre**: US-001, FR-004, FR-007, NFR-001

```gherkin
@US-001 @FR-004 @FR-007 @NFR-001 @AC-013
Feature: Proteção contra remoção total disfarçada de sincronização

  Scenario: Execução sem nenhum chunk esperado
    Given uma execução cujo conjunto esperado de chunks está vazio
    When a sincronização é solicitada em qualquer modo
    Then a execução termina em erro antes de qualquer mutação remota
    And nenhuma remoção de pontos é solicitada
```

#### AC-014 — Limpeza que abrangeria a totalidade do escopo é bloqueada

**Cobre**: US-001, FR-003, FR-007, NFR-001

```gherkin
@US-001 @FR-003 @FR-007 @NFR-001 @AC-014
Feature: Proteção contra remoção total disfarçada de sincronização

  Scenario: Nenhum ponto existente do escopo é esperado pela execução
    Given pontos existentes no escopo do project_id da execução
    And um conjunto esperado que não contém nenhum desses pontos
    When a sincronização em modo espelho chega à etapa de limpeza
    Then a execução termina em erro antes de remover qualquer ponto
    And o registro informa o total existente e o total esperado
```

#### AC-015 — Redução parcial legítima continua permitida

**Cobre**: US-001, FR-003, FR-007, NFR-003

```gherkin
@US-001 @FR-003 @FR-007 @NFR-003 @AC-015
Feature: Proteção contra remoção total disfarçada de sincronização

  Scenario: Documento removido da pasta de entrada
    Given pontos existentes no escopo do project_id da execução
    And um conjunto esperado que preserva parte desses pontos
    When a sincronização em modo espelho conclui
    Then apenas os pontos obsoletos do escopo são removidos
    And os pontos ainda esperados permanecem inalterados
```

### 7. Requisitos

#### Funcionais

- **FR-001**: A CLI deve reconhecer a opção antiga de recriação e encerrar a execução com código de saída diferente de zero e mensagem de migração, antes de instanciar cliente remoto, gerar embeddings ou alterar dados.
- **FR-002**: O código de produção não deve conter caminho alcançável que apague collection, índice ou namespace remoto por inteiro; a camada de indexação não expõe parâmetro que solicite essa exclusão.
- **FR-003**: No modo espelho, o sistema deve remover apenas pontos obsoletos pertencentes ao `project_id` da execução e somente após a conclusão bem-sucedida do upsert de todos os pontos novos ou alterados.
- **FR-004**: O sistema deve interromper a execução antes de qualquer mutação remota quando o escopo lógico for inválido: `project_id` ausente, vazio ou divergente entre chunks, `chunk_id` ausente ou duplicado, ou manifesto incompatível com o conjunto processado.
- **FR-005**: O sistema deve aceitar o modo espelho apenas em provider com garantia de escopo comprovada e recusar a configuração, antes de qualquer mutação, nos demais providers, mantendo neles o modo incremental.
- **FR-006**: `README.md`, `GUIA_DE_USO.md`, `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md` e os comentários de `config.yaml` devem descrever apenas atualização idempotente e recuperação não destrutiva, sem apresentar a recriação como procedimento.
- **FR-007**: O sistema deve interromper a execução antes de qualquer remoção quando o conjunto esperado da execução for vazio, ou quando a limpeza do modo espelho abrangeria a totalidade dos pontos existentes no escopo lógico, porque nesses casos a sincronização produz o mesmo efeito de uma recriação. Uma redução parcial legítima permanece permitida.

#### Não funcionais

- **NFR-001**: Segurança fail-closed — nenhuma chamada de mutação remota pode ocorrer antes da validação completa de opção, configuração e escopo. **Verificação**: teste Pytest com cliente falso que registra todas as chamadas e afirma lista vazia de mutações nos cenários de rejeição; busca estática por `delete_collection`, `delete_all` e equivalentes no código de produção.
- **NFR-002**: Auditabilidade sem exposição de segredos — cada execução de sincronização registra modo, escopo lógico e contagens de pontos previstos, inseridos, mantidos e removidos, sem credenciais, tokens ou URL do destino. **Verificação**: teste Pytest sobre os registros capturados (`caplog`) afirmando presença das contagens e ausência de segredos; inspeção dos guias publicados.
- **NFR-003**: Idempotência e preservação de volume no provider com identidade estável — reexecutar a sincronização sobre a mesma entrada no Qdrant não cria pontos duplicados nem remove pontos válidos, e o upsert permanece em lotes sem exigir recriação integral. **Verificação**: teste Pytest de dupla execução com cliente falso comparando o conjunto de IDs antes e depois e afirmando `inseridos = 0` e `removidos = 0`. **Limite conhecido**: o caminho ChromaDB usa `Chroma.from_documents` sem IDs estáveis (`research/auditoria-codigo/caminhos-destrutivos.md#providers-sem-paridade-de-espelho`) e duplica registros a cada execução; corrigir isso exige identidade estável nesse provider e fica fora desta fatia, encaminhado ao BACKLOG-0003.

#### Erros e casos-limite

- Opção antiga de recriação informada na CLI → erro de migração, código de saída diferente de zero, nenhuma conexão remota aberta.
- `project_id` ausente, vazio ou divergente entre chunks → execução encerrada em erro antes de qualquer mutação.
- `chunk_id` ausente ou duplicado → execução encerrada em erro antes de qualquer mutação.
- Manifesto incompleto ou divergente do conjunto processado → execução encerrada sem remover pontos.
- Falha parcial de embedding ou upsert → execução encerrada sem iniciar a limpeza de obsoletos.
- `sync_mode` inválido ou espelho em provider sem garantia → erro antes de instanciar cliente remoto.
- Destino remoto inacessível → falha relatada sem tentativa de recuperação destrutiva.
- Conjunto de obsoletos vazio → nenhuma chamada de remoção é emitida.
- Conjunto esperado vazio, por pasta de entrada vazia ou por falha silenciosa de carregamento → execução encerrada em erro antes de qualquer remoção.
- Limpeza que abrangeria todos os pontos existentes do escopo lógico → execução encerrada em erro, com o conjunto esperado e o existente informados no registro.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Python 3.12+ gerenciado por `uv`, LangChain, Pytest 8.3+ e clientes Qdrant, ChromaDB e Pinecone (`.specsfy/STACK.md`).
- `pipeline.py` orquestra carregamento, chunking, exportação, manifesto e indexação; `upsert_from_chunks.py` reindexa a partir de `chunks.json`.
- `src/embedder.py` concentra a criação de embeddings, a seleção de provider e a indexação; `index_chunks` é a única porta de escrita remota.
- `src/manifest.py` já produz o manifesto com `project_id`, `collection_name`, contagens e `chunk_ids`; `src/identity.py` gera identidades determinísticas.
- `tests/test_qdrant_sync.py` já exercita o modo espelho com cliente falso, o que estabelece o padrão de teste a ser estendido.
- Convenções locais: módulos focados em `src/`, configuração centralizada em `src/config.py` e `config.yaml`, logging por `logging` padrão.

#### Arquitetura e módulos

- **Camada de CLI** (`pipeline.py`, `upsert_from_chunks.py`): remove a flag destrutiva do fluxo e passa a reconhecê-la apenas para emitir o erro de migração antes de carregar documentos ou tocar o provider. A CLI não recebe mais o parâmetro de recriação ao chamar a indexação.
- **Guarda de política** (novo módulo `src/safety.py`): expõe uma classe `SyncSafetyPolicy` que encapsula a política de segurança da sincronização e é consumida pelas duas CLIs e pela indexação. Ela concentra a rejeição da opção antiga, a validação de `sync_mode` por provider, a validação do escopo lógico e a validação da proporção de remoção. A escolha por uma classe, em vez de funções soltas, atende à regra de orientação a objetos e encapsulamento de `.specsfy/RULES.md` (Arquitetura) e prepara o ponto de extensão que o BACKLOG-0002 usará para o escopo multi-tenant.
- **Camada de indexação** (`src/embedder.py`): `index_chunks` perde o parâmetro `recreate`; os blocos `delete_collection` do Qdrant e `delete(delete_all=True)` do Pinecone são removidos. A validação de escopo passa a ocorrer antes de instanciar o cliente. O modo espelho fica restrito ao Qdrant e a remoção de obsoletos continua posterior ao upsert, agora protegida por um sinal explícito de upsert completo. Antes de emitir qualquer `delete`, a indexação consulta a política com o total existente no escopo e o total esperado; conjunto esperado vazio ou remoção que abrangeria a totalidade do escopo interrompem a execução, porque o efeito seria equivalente ao da recriação que esta fatia elimina.
- **Registro auditável**: a indexação emite um registro final com modo, escopo lógico e contagens de previstos, inseridos, mantidos e removidos, sem segredos.
- Ponto de extensão preservado: a separação por provider permanece como está; a modularização por Factory/Adapter é responsabilidade do BACKLOG-0003 e não é antecipada aqui.

#### Migrations

- Não aplicável. Nenhuma mudança de schema local ou remoto. A collection e o namespace existentes permanecem intactos; nenhum dado é movido ou reescrito.

#### Models

- Não há models ORM. As estruturas de dados relevantes são o chunk (`src/chunker.py`, `src/identity.py`) e o manifesto (`src/manifest.py`), ambos preservados sem alteração de formato. A invariante reforçada é a de escopo: cada chunk de uma execução compartilha o mesmo `project_id` não vazio e possui `chunk_id` único e não vazio.

#### Controllers e casos de uso

- `pipeline.py::parse_args` e `pipeline.py::main`: entrada por argumentos de linha de comando e `config.yaml`; saída por código de processo e registros; sem autorização aplicável (execução local pelo operador).
- `upsert_from_chunks.py::main`: mesma entrada a partir de `chunks.json`; mesmo contrato de rejeição da opção antiga.
- `src/safety.py::SyncSafetyPolicy`: encapsula a política de segurança. Métodos `reject_destructive_option`, `assert_sync_mode_supported`, `assert_valid_scope` e `assert_removal_allowed`; entrada por argumentos da CLI, configuração e totais do escopo; saída por exceção específica com mensagem de migração ou de limite.
- `src/embedder.py::index_chunks`: entrada por chunks, configuração de embedding e de vector store; saída pelos pontos sincronizados e pelo registro auditável.

#### Views e experiência

- Não aplicável. O componente não possui interface para pessoas; a experiência do operador acontece por mensagens de CLI e registros, especificados na seção 10.

#### Queries e repositórios

- Leitura de escopo no Qdrant: `client.scroll` com filtro `metadata.project_id` e paginação por `offset`, limite 256 por página, apenas IDs (`with_payload=False`, `with_vectors=False`). Preservada como está.
- Escrita: `client.upsert` em lotes de `batch_size` com `wait=True`.
- Remoção de obsoletos: `client.delete` com `PointIdsList` em lotes, restrita ao conjunto `existentes_do_escopo − esperados_da_execução`, executada apenas após o upsert completo.
- Consistência: os IDs são determinísticos (`chunk_id`), o que torna o conjunto esperado comparável entre execuções.

#### Jobs e processamento assíncrono

- Não aplicável. A execução é síncrona por linha de comando.

#### Estrutura de arquivos

```text
specs/defined/0001-bloquear-recriacao-destrutiva/
  spec.md
  research/
src/
  safety.py          # novo: SyncSafetyPolicy com as guardas fail-closed
  embedder.py        # sem parâmetro e sem caminho destrutivo
pipeline.py          # rejeita a opção antiga antes de qualquer efeito
upsert_from_chunks.py
tests/
  test_safety.py     # novo: rejeição, sync_mode, escopo e proporção de remoção
  test_qdrant_sync.py
README.md
GUIA_DE_USO.md
CONTEXTO_MELHORIA_RECUPERACAO_RAG.md
config.yaml
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Chunk | `chunk_id` determinístico e não vazio | `page_content`, `metadata.project_id` não vazio e igual em toda a execução, `metadata.document_id`; `chunk_id` único no conjunto | Pertence a um documento; vira um ponto no banco vetorial |
| Manifesto de execução | `run_id` | `project_id`, `collection_name`, configuração de embedding, contagens e `chunk_ids` esperados | Consolida o conjunto esperado da execução; base da comparação de escopo |
| Ponto do banco vetorial | `chunk_id` como ID do ponto | Vetor e payload com `page_content` e `metadata` | Pertence ao escopo lógico `metadata.project_id`; comparado com o manifesto |
| Escopo lógico de sincronização | `project_id` | Conjunto de IDs existentes no destino filtrado por `metadata.project_id` | Delimita o universo elegível a remoção; nunca ultrapassa o `project_id` da execução |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Execução | Iniciada | Opção antiga de recriação detectada | Encerrada em erro | Nenhum cliente criado, nenhum embedding gerado, nenhuma mutação remota |
| Execução | Iniciada | Escopo ou `sync_mode` inválido | Encerrada em erro | Nenhuma mutação remota emitida |
| Execução | Iniciada | Conjunto esperado vazio | Encerrada em erro | Nenhuma mutação remota emitida |
| Execução | Upsert completo | Limpeza abrangeria a totalidade do escopo existente | Encerrada em erro | Nenhum ponto removido; totais existente e esperado registrados |
| Execução | Validada | Upsert dos pontos novos concluído | Upsert completo | Todos os lotes confirmados antes de qualquer remoção |
| Execução | Validada | Falha em um lote de upsert | Encerrada em erro | Limpeza de obsoletos não iniciada |
| Execução | Upsert completo | Modo espelho no provider suportado | Limpeza concluída | Removidos ⊆ existentes do mesmo `project_id` menos esperados |
| Execução | Upsert completo | Modo incremental | Concluída | Nenhuma remoção emitida |
| Ponto do escopo | Existente e esperado | Reexecução idempotente | Mantido | Não é reescrito nem removido |
| Ponto do escopo | Existente e não esperado | Limpeza em modo espelho após upsert completo | Removido | Pertence ao `project_id` da execução |
| Ponto de outro escopo | Existente | Qualquer execução | Inalterado | Nunca é lido para remoção nem removido |

#### Migração e retenção

- Não aplicável a esta entrega. Nenhum dado é migrado, reescrito ou expurgado. As definições de retenção e ownership dos documentos permanecem pendentes na descoberta do produto completo, conforme `.specsfy/DATABASE.md`.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. O componente é operado exclusivamente por linha de comando (`pipeline.py`, `search.py`, `chat.py`), conforme `INTERFACE.md` e `PROJECT.md`. A inspeção de interface não encontrou framework, roteamento, estilos, componentes, formulários nem testes de interface neste repositório. Esta entrega altera comportamento de CLI, camada de indexação e documentação; nenhuma tela é criada ou modificada.

#### Stack e convenções de interface

- Não aplicável: não existe camada de interface neste componente. A direção futura do projeto-mãe (Next.js, shadcn/ui, Tailwind) não é dependência atual e não autoriza introduzir biblioteca de interface aqui (`INTERFACE.md`, `PR-006`).

#### Telas e responsabilidades

- Não aplicável.

#### Fluxo de informação e navegação

- Não aplicável. O operador interage por comando e lê o resultado nos registros de execução e no arquivo de log configurado em `config.yaml`.

#### Menus e navegação principal

- Não aplicável. Não há menu; o acesso é direto pelos comandos `uv run python pipeline.py` e `uv run python upsert_from_chunks.py`, documentados em `README.md` e `GUIA_DE_USO.md`.

#### Formulários e ações

- Não aplicável. As entradas são argumentos de linha de comando e `config.yaml`.

#### Composição e disposição

- Não aplicável.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável | Não aplicável |

- Não aplicável: o projeto não é React e nenhuma biblioteca de interface é introduzida por esta entrega.
- `INTERFACE.md` permanece registrando ausência de interface; nenhuma atualização de componentes é gerada aqui.

#### Estados e acessibilidade

- Não aplicável a telas. Os estados observáveis pelo operador são de terminal: início da execução, progresso por lote, conclusão com contagens, e falha com mensagem específica e código de saída diferente de zero. As mensagens de erro são autoexplicativas e indicam o caminho seguro.

#### Contrato CRUD

- Não aplicável. Esta entrega não cria superfície CRUD.

#### Revisão visual durante o desenvolvimento

- Não aplicável, com motivo concreto: não existe superfície visual neste repositório. Cada tarefa registra `VISUAL: Não aplicável — componente CLI sem interface renderizada`, e a conferência é substituída pela inspeção das mensagens de terminal e dos registros de execução.

#### APIs expostas

- `uv run python pipeline.py [--config CAMINHO] [--only-chunks|--skip-index] [--input-dir DIR]` — sem autenticação (execução local); saída por registros e código de processo; a opção antiga de recriação retorna erro de migração com código diferente de zero.
- `uv run python upsert_from_chunks.py --provider PROVIDER [--chunks CAMINHO]` — mesmo contrato de rejeição da opção antiga.
- `src/embedder.py::index_chunks(chunks, embedding_cfg, vector_cfg, persist_dir, batch_size)` — contrato interno consumido pelas CLIs; o parâmetro de recriação deixa de existir, o que é uma quebra intencional de assinatura interna.
- Versionamento: não há API versionada publicada; a mudança de assinatura interna é registrada em `DEC-005`.

#### APIs externas utilizadas

- Qdrant (cliente `qdrant-client` 1.10.1): `get_collections`, `create_collection`, `count`, `scroll`, `upsert`, `delete` restrito a `PointIdsList`. `delete_collection` deixa de ser usado. Autenticação por variável de ambiente; timeout e retry conforme padrão do cliente; falha de conexão encerra a execução sem alternativa destrutiva.
- Pinecone (`pinecone`, `langchain-pinecone`): `describe_index`, `Index`, `add_documents`. `delete(delete_all=True)` deixa de ser usado.
- ChromaDB (`langchain-chroma`): `Chroma.from_documents` em modo incremental local.
- Providers de embeddings (OpenAI, OpenRouter, Hugging Face) conforme `config.yaml`, sem mudança nesta entrega.

#### Documentação das APIs consultadas

- Nenhuma documentação externa consultada. O comportamento dos clientes foi confirmado diretamente no código local em `src/embedder.py` e nos testes existentes em `tests/test_qdrant_sync.py`.

#### Eventos e outros contratos

- Contrato de registro auditável (produzido pela indexação, consumido por operador e por análise posterior): campos `modo`, `escopo lógico`, `previstos`, `inseridos`, `mantidos`, `removidos`. Compatibilidade: aditiva; nenhum campo existente é removido. Segredos são proibidos neste registro.

### 11. Estratégia TDD

- **Unidade**: guardas de `src/safety.py` (rejeição da opção antiga, validação de `sync_mode` por provider, validação de escopo lógico) e a composição das contagens do registro auditável.
- **Integração/contrato**: `src/embedder.py::index_chunks` exercitado com cliente falso que registra toda chamada, cobrindo ordem upsert → limpeza, isolamento por `project_id`, interrupção em falha de upsert e ausência total de chamadas de exclusão ampla.
- **BDD/aceite**: os cenários `AC-001` a `AC-012` da seção 6 são o contrato de referência que orienta o desenho dos casos TDD. Nenhum arquivo `.feature` é criado ou executado.
- **Runner TDD**: Pytest 8.3+, já presente em `pyproject.toml` e em `tests/`. Projeto Python sem PHP e sem Node; não há decisão de runner pendente.
- **E2E**: Não aplicável. A execução de ponta a ponta contra um destino remoto real depende de credenciais e de base de cliente; o cliente falso cobre o contrato sem risco de mutação real.
- **Verificação manual**: leitura final de `README.md`, `GUIA_DE_USO.md`, `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md` e `config.yaml` para confirmar a ausência do procedimento destrutivo. É inevitável porque a adequação editorial do texto não é verificável apenas por busca de termo; a busca automatizada complementa como rede de segurança.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-002, FR-001, FR-002, NFR-001, AC-001 | AC-001 na seção 6 | caso de rejeição sem mutação em tests/test_safety.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-002, FR-001, FR-002, NFR-001, AC-002 | AC-002 na seção 6 | caso de ausência de cliente e de embeddings em tests/test_safety.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-002, US-003, FR-001, FR-006, AC-003 | AC-003 na seção 6 | caso de mensagem de migração em tests/test_safety.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, FR-003, NFR-002, NFR-003, AC-004 | AC-004 na seção 6 | caso de dupla execução idempotente em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, FR-003, FR-004, NFR-001, AC-005 | AC-005 na seção 6 | caso de falha de upsert sem limpeza em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, FR-003, FR-004, NFR-003, AC-006 | AC-006 na seção 6 | caso de isolamento entre project_id em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, US-003, FR-004, NFR-001, AC-007 | AC-007 na seção 6 | caso de escopo inválido sem mutação em tests/test_safety.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, FR-002, FR-005, NFR-001, AC-008 | AC-008 na seção 6 | caso de espelho recusado por provider em tests/test_safety.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-003, FR-002, FR-005, NFR-003, AC-009 | AC-009 na seção 6 | caso de append preservado em provider sem garantia em tests/test_safety.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, FR-003, FR-006, NFR-002, AC-010 | AC-010 na seção 6 | caso de registro auditável sem segredos em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-003, FR-005, FR-006, NFR-002, AC-011 | AC-011 na seção 6 | caso de varredura documental sem termo destrutivo em tests/test_docs_safety.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-003, FR-001, FR-006, NFR-002, NFR-003, AC-012 | AC-012 na seção 6 | caso de procedimento de recuperação idempotente em tests/test_docs_safety.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, FR-004, FR-007, NFR-001, AC-013 | AC-013 na seção 6 | caso de conjunto esperado vazio em tests/test_safety.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, FR-003, FR-007, NFR-001, AC-014 | AC-014 na seção 6 | caso de limpeza total bloqueada em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |
| US-001, FR-003, FR-007, NFR-003, AC-015 | AC-015 na seção 6 | caso de redução parcial permitida em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | `tests/test_safety.py` | Pending |
| FR-001 | AC-002 | Unidade | `tests/test_safety.py` | Pending |
| FR-001 | AC-003 | Unidade | `tests/test_safety.py` | Pending |
| FR-001 | AC-012 | Unidade | `tests/test_docs_safety.py` | Pending |
| FR-002 | AC-001 | Unidade | `tests/test_safety.py` | Pending |
| FR-002 | AC-002 | Unidade | `tests/test_safety.py` | Pending |
| FR-002 | AC-008 | Integração/contrato | `tests/test_safety.py` | Pending |
| FR-002 | AC-009 | Integração/contrato | `tests/test_safety.py` | Pending |
| FR-003 | AC-004 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| FR-003 | AC-005 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| FR-003 | AC-006 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| FR-003 | AC-010 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| FR-003 | AC-014 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| FR-003 | AC-015 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| FR-004 | AC-005 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| FR-004 | AC-006 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| FR-004 | AC-007 | Unidade | `tests/test_safety.py` | Pending |
| FR-004 | AC-013 | Unidade | `tests/test_safety.py` | Pending |
| FR-005 | AC-008 | Unidade | `tests/test_safety.py` | Pending |
| FR-005 | AC-009 | Integração/contrato | `tests/test_safety.py` | Pending |
| FR-005 | AC-011 | Unidade | `tests/test_docs_safety.py` | Pending |
| FR-006 | AC-003 | Unidade | `tests/test_safety.py` | Pending |
| FR-006 | AC-010 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| FR-006 | AC-011 | Unidade | `tests/test_docs_safety.py` | Pending |
| FR-006 | AC-012 | Unidade | `tests/test_docs_safety.py` | Pending |
| FR-007 | AC-013 | Unidade | `tests/test_safety.py` | Pending |
| FR-007 | AC-014 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| FR-007 | AC-015 | Integração/contrato | `tests/test_qdrant_sync.py` | Pending |
| NFR-001 | AC-001 | Unidade | `uv run pytest tests/test_safety.py` | Pending |
| NFR-001 | AC-002 | Unidade | `uv run pytest tests/test_safety.py` | Pending |
| NFR-001 | AC-005 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |
| NFR-001 | AC-007 | Unidade | `uv run pytest tests/test_safety.py` | Pending |
| NFR-001 | AC-008 | Unidade | `uv run pytest tests/test_safety.py` | Pending |
| NFR-001 | AC-013 | Unidade | `uv run pytest tests/test_safety.py` | Pending |
| NFR-001 | AC-014 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |
| NFR-002 | AC-004 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |
| NFR-002 | AC-010 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |
| NFR-002 | AC-011 | Unidade | `uv run pytest tests/test_docs_safety.py` | Pending |
| NFR-002 | AC-012 | Unidade | `uv run pytest tests/test_docs_safety.py` | Pending |
| NFR-003 | AC-004 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |
| NFR-003 | AC-006 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |
| NFR-003 | AC-009 | Integração/contrato | `uv run pytest tests/test_safety.py` | Pending |
| NFR-003 | AC-012 | Unidade | `uv run pytest tests/test_docs_safety.py` | Pending |
| NFR-003 | AC-015 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed em 2026-08-31
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/defined/0001-bloquear-recriacao-destrutiva/spec.md`
- **Achados**: estrutura `VALID`; research `PASSED` com quatro claims, três críticas verificadas; cobertura mínima atendida com 3 US, 7 FR, 3 NFR e 15 AC, cada `US`, `FR` e `NFR` coberto por três ou mais cenários distintos. Três findings foram levantados na revisão semântica e todos foram resolvidos na fonte antes da aprovação; nenhum `P1 Open` permanece.
- **FIND-SEC-001** [P1] [Resolved] Uma execução cujo conjunto esperado fica vazio faria o modo espelho remover todos os pontos do escopo, reproduzindo o efeito da recriação que esta fatia elimina; hoje isso só falha como efeito colateral da validação de `project_id`, que uma refatoração pode remover sem que ninguém perceba — Refs: FR-003, FR-004, FR-007, AC-013, AC-014 — Evidence: specs/defined/0001-bloquear-recriacao-destrutiva/research/auditoria-codigo/caminhos-destrutivos.md:156 — Effect: perda ampla e irreversível da base de um cliente por pasta de entrada vazia ou falha silenciosa de carregamento, exatamente o risco que a spec existe para impedir — Suggestion: resolvido pela criação de FR-007, dos cenários AC-013 a AC-015 e da guarda `assert_removal_allowed` em `SyncSafetyPolicy`, com dois critérios objetivos e sem limiar arbitrário.
- **FIND-PROD-002** [P2] [Resolved] `NFR-003` prometia idempotência para toda a sincronização, mas o caminho ChromaDB escreve com `Chroma.from_documents` sem IDs estáveis e duplica registros a cada execução, tornando o requisito impossível de cumprir dentro do escopo declarado — Refs: NFR-003, AC-004, AC-009 — Evidence: specs/defined/0001-bloquear-recriacao-destrutiva/research/auditoria-codigo/caminhos-destrutivos.md:199 — Effect: requisito não verificável para um provider suportado, o que aprovaria um gate sobre promessa que a entrega não sustenta — Suggestion: resolvido delimitando `NFR-003` ao provider com identidade estável, declarando a duplicação do ChromaDB como limite conhecido em `DEC-008` e encaminhando a correção ao BACKLOG-0003.
- **FIND-ARCH-003** [P2] [Resolved] O plano previa as guardas como funções soltas em `src/safety.py`, o que conflita com a regra de orientação a objetos e encapsulamento confirmada pela pessoa responsável e registrada em `PR-001` — Refs: FR-001, FR-004, FR-005 — Evidence: .specsfy/RULES.md:14 — Effect: introdução de um módulo procedural novo contra uma regra explícita do projeto, criando precedente e dificultando a extensão multi-tenant do BACKLOG-0002 — Suggestion: resolvido encapsulando a política na classe `SyncSafetyPolicy`, com métodos nomeados por obrigação, conforme `DEC-006`.
- Findings especializados seguem `FIND-PROD|ARCH|SEC-NNN`, severidade `P1|P2|P3`,
  estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0001-bloquear-recriacao-destrutiva/spec.md`
- **Achados**: Pending. As tarefas da seção 14 são preliminares e serão consolidadas por `$specsfy-05-tasks`.

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0001-bloquear-recriacao-destrutiva/spec.md .`
- **Achados**: Pending. Nenhum RED foi observado até o momento.

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

- [ ] T001 [TEST] [TDD] [US-002] Derivar de AC-001, AC-002 e AC-003 casos Pytest falhando em tests/test_safety.py — Refs: US-002, FR-001, FR-002, FR-006, NFR-001, AC-001, AC-002, AC-003 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [ ] **EXECUTE**: Escrever os casos TDD com marcador próprio `SPECSFY:` por caso, usando cliente falso que registra chamadas; não criar nem executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido por ausência de `src/safety.py` e da rejeição na CLI.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED nas seções 11 e 12.
  - [ ] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [ ] T002 [TEST] [TDD] [US-001] Derivar de AC-004, AC-005, AC-006, AC-010, AC-014 e AC-015 casos Pytest falhando em tests/test_qdrant_sync.py — Refs: US-001, FR-003, FR-004, FR-006, FR-007, NFR-001, NFR-002, NFR-003, AC-004, AC-005, AC-006, AC-010, AC-014, AC-015 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec, o teste existente e confirmar regra, IDs e nível.
  - [ ] **EXECUTE**: Escrever os casos TDD com marcador próprio `SPECSFY:` por caso, estendendo o cliente falso para registrar ordem e tipo de chamada.
  - [ ] **VERIFY**: Observar RED válido nos pontos ainda não garantidos.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED nas seções 11 e 12.
  - [ ] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [ ] T003 [TEST] [TDD] [US-001] Derivar de AC-007, AC-008, AC-009 e AC-013 casos Pytest falhando em tests/test_safety.py — Refs: US-001, US-003, FR-002, FR-004, FR-005, FR-007, NFR-001, NFR-003, AC-007, AC-008, AC-009, AC-013 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar escopo inválido, conjunto esperado vazio e providers sem garantia.
  - [ ] **EXECUTE**: Escrever os casos TDD com marcador próprio `SPECSFY:` por caso.
  - [ ] **VERIFY**: Observar RED válido por ausência das guardas de escopo e de provider.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED nas seções 11 e 12.
  - [ ] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [ ] T004 [TEST] [TDD] [US-003] Derivar de AC-011 e AC-012 casos Pytest falhando em tests/test_docs_safety.py — Refs: US-003, FR-001, FR-005, FR-006, NFR-002, NFR-003, AC-011, AC-012 — Depends: none
  - [ ] **PREP**: Listar os arquivos documentais no escopo e os termos destrutivos a rastrear.
  - [ ] **EXECUTE**: Escrever os casos TDD com marcador próprio `SPECSFY:` por caso, varrendo README, guia, contexto e config.
  - [ ] **VERIFY**: Observar RED válido pelas ocorrências atuais.
  - [ ] **VISUAL**: Não aplicável — tarefa documental sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED nas seções 11 e 12.
  - [ ] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

#### Fase 2 — US-002 Receber erro claro ao usar a opção antiga (P1)

**Objetivo**: nenhuma execução consegue solicitar recriação e o operador é redirecionado ao caminho seguro.
**Teste independente**: `uv run pytest tests/test_safety.py` verde e `uv run python pipeline.py --recreate` terminando em erro sem conexão remota.

- [ ] T005 [CODE] [US-002] Criar a classe SyncSafetyPolicy em src/safety.py — Refs: US-002, FR-001, FR-002, FR-004, FR-005, FR-007, NFR-001, AC-001, AC-002, AC-003, AC-007, AC-008, AC-009, AC-013 — Depends: T001, T003
  - [ ] **PREP**: Confirmar RED TDD e as quatro guardas exigidas pela seção 8.
  - [ ] **EXECUTE**: Implementar `SyncSafetyPolicy` com rejeição da opção antiga, validação de `sync_mode` por provider, validação de escopo lógico e validação da proporção de remoção, com exceções e mensagens próprias.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_safety.py` e a regressão.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T005","refs":["US-002","FR-001","FR-002","FR-004","FR-005","FR-007","NFR-001","AC-001","AC-002","AC-003","AC-007","AC-008","AC-009","AC-013"],"files":["src/safety.py"],"commands":[{"run":"uv run pytest tests/test_safety.py","exit":0}]} -->

- [ ] T006 [CODE] [US-002] Aplicar a rejeição da opção antiga em pipeline.py e upsert_from_chunks.py — Refs: US-002, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003 — Depends: T005
  - [ ] **PREP**: Confirmar a ordem de execução para garantir rejeição antes de carregar documentos e de instanciar cliente.
  - [ ] **EXECUTE**: Reconhecer a opção antiga apenas para emitir erro de migração e remover sua propagação para a indexação.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_safety.py` e a regressão.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN, código de saída e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T006","refs":["US-002","FR-001","FR-002","NFR-001","AC-001","AC-002","AC-003"],"files":["pipeline.py","upsert_from_chunks.py"],"commands":[{"run":"uv run pytest tests/test_safety.py","exit":0}]} -->

**Checkpoint**: `uv run python pipeline.py --recreate` falha com mensagem de migração e sem nenhuma chamada remota.

#### Fase 3 — US-001 Sincronizar sem risco de perda ampla (P1)

**Objetivo**: a camada de indexação perde cada caminho destrutivo e mantém o espelho restrito e auditável.
**Teste independente**: `uv run pytest tests/test_qdrant_sync.py` verde, incluindo dupla execução idempotente e isolamento entre projetos.

- [ ] T007 [CODE] [US-001] Remover o parâmetro e os caminhos destrutivos de src/embedder.py — Refs: US-001, US-002, FR-002, FR-003, FR-005, NFR-001, AC-001, AC-005, AC-008, AC-009 — Depends: T005, T006
  - [ ] **PREP**: Mapear cada chamada destrutiva e cada uso do parâmetro removido.
  - [ ] **EXECUTE**: Remover o parâmetro de `index_chunks`, os blocos de exclusão de collection e de namespace, e aplicar as guardas antes de instanciar o cliente.
  - [ ] **VERIFY**: Executar `uv run pytest` e confirmar por busca estática a ausência de exclusão ampla no código de produção.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN, comando de busca estática e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T007","refs":["US-001","US-002","FR-002","FR-003","FR-005","NFR-001","AC-001","AC-005","AC-008","AC-009"],"files":["src/embedder.py"],"commands":[{"run":"uv run pytest","exit":0}]} -->

- [ ] T008 [CODE] [US-001] Garantir ordem upsert completo → limpeza, a guarda de remoção total e o registro auditável em src/embedder.py — Refs: US-001, FR-003, FR-004, FR-006, FR-007, NFR-002, NFR-003, AC-004, AC-005, AC-006, AC-010, AC-014, AC-015 — Depends: T002, T007
  - [ ] **PREP**: Confirmar RED dos casos de ordem, isolamento e auditoria.
  - [ ] **EXECUTE**: Tornar explícito o sinal de upsert completo antes da limpeza, consultar `SyncSafetyPolicy.assert_removal_allowed` com os totais existente e esperado, e emitir o registro com modo, escopo e contagens, sem segredos.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_qdrant_sync.py` e a regressão.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN, contagens observadas e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T008","refs":["US-001","FR-003","FR-004","FR-006","FR-007","NFR-002","NFR-003","AC-004","AC-005","AC-006","AC-010","AC-014","AC-015"],"files":["src/embedder.py"],"commands":[{"run":"uv run pytest tests/test_qdrant_sync.py","exit":0}]} -->

**Checkpoint**: reexecução sobre a mesma entrada registra zero inseridos e zero removidos, com pontos de outro `project_id` intactos.

#### Fase 4 — US-003 Recuperar uma base inconsistente sem apagar tudo (P1)

**Objetivo**: a documentação publicada deixa de ensinar o caminho destrutivo e passa a descrever a recuperação idempotente.
**Teste independente**: `uv run pytest tests/test_docs_safety.py` verde e leitura confirmando o novo procedimento.

- [ ] T009 [DOC] [US-003] Substituir o procedimento destrutivo em README.md, GUIA_DE_USO.md, CONTEXTO_MELHORIA_RECUPERACAO_RAG.md e config.yaml — Refs: US-003, FR-001, FR-005, FR-006, NFR-002, NFR-003, AC-003, AC-011, AC-012 — Depends: T006, T007, T008
  - [ ] **PREP**: Listar cada ocorrência e o texto que a substitui.
  - [ ] **EXECUTE**: Reescrever atualização e recuperação como fluxo idempotente apoiado por manifesto e diagnóstico; remover a recomendação de recriação.
  - [ ] **VERIFY**: Executar `uv run pytest tests/test_docs_safety.py` e reler os trechos alterados.
  - [ ] **VISUAL**: Não aplicável — tarefa documental sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar GREEN, arquivos alterados e trechos substituídos.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T009","refs":["US-003","FR-001","FR-005","FR-006","NFR-002","NFR-003","AC-003","AC-011","AC-012"],"files":["README.md","GUIA_DE_USO.md","CONTEXTO_MELHORIA_RECUPERACAO_RAG.md","config.yaml"],"commands":[{"run":"uv run pytest tests/test_docs_safety.py","exit":0}]} -->

**Checkpoint**: nenhum documento do repositório apresenta a recriação como procedimento de atualização ou de recuperação.

#### Fase final — Qualidade

- [ ] T010 [TEST] Executar Ruff, regressão Pytest e rastreabilidade — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015 — Depends: T005, T006, T007, T008, T009
  - [ ] **PREP**: Identificar suites, checks e gates aplicáveis.
  - [ ] **EXECUTE**: Executar `uv run ruff check .`, `uv run pytest` e o script de rastreabilidade.
  - [ ] **VERIFY**: Confirmar ausência de gaps entre requisitos, cenários e testes.
  - [ ] **VISUAL**: Não aplicável — componente CLI sem interface renderizada.
  - [ ] **EVIDENCE**: Registrar contagens e comandos finais nas seções 11 a 13.
  - [ ] **IMPROVE**: Registrar retrospectiva do processo.

### 15. Ordem de execução

- Caminho crítico: T001/T002/T003/T004 → T005 → T006 → T007 → T008 → T009 → T010.
- Tarefas paralelas: T001, T002, T003 e T004 podem ser escritas em paralelo, pois cobrem arquivos de teste distintos e não dependem de implementação.
- Estratégia de MVP: a menor entrega segura é US-002 mais T007, porque elimina o caminho destrutivo alcançável. US-001 consolida a garantia do espelho e US-003 fecha o vetor documental; nenhuma delas pode ficar de fora do milestone M0, já que o guia publicado reintroduz o risco na prática.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Identidades determinísticas e manifesto já implementados em `src/identity.py` e `src/manifest.py`; esta entrega os preserva e depende deles para comparar escopo.
- Padrão de cliente falso já estabelecido em `tests/test_qdrant_sync.py`.
- BACKLOG-0002 ampliará o contrato de escopo para multi-tenant sem reabrir esta proteção básica.
- BACKLOG-0003 deverá preservar estas garantias ao separar os adapters de providers.

#### Riscos

- Reintrodução futura do caminho destrutivo por outro provider ou refatoração → teste de contrato que afirma ausência de chamadas de exclusão ampla, executado na regressão.
- Operador com base já inconsistente esperando recriar para resolver → procedimento de recuperação idempotente publicado em `T009` e mensagem de migração explícita em `T006`.
- Quebra de assinatura interna de `index_chunks` afetando chamadas não mapeadas → busca por todos os chamadores antes de `T007` e regressão completa em `T010`.
- Documentação histórica (`CONTEXTO_MELHORIA_RECUPERACAO_RAG.md`, `PLANO_CHUNKS_RESUMO_QDRANT.md`) sendo lida como procedimento vigente → ajuste explícito do texto em `T009`.
- Pasta de entrada vazia ou falha silenciosa de carregamento transformando a sincronização em espelho no equivalente a uma recriação → `FR-007` bloqueia o conjunto esperado vazio e a remoção que abrangeria a totalidade do escopo, provado por `AC-013` e `AC-014`.
- Operador usando ChromaDB e acumulando duplicatas a cada execução, por ausência de identidade estável nesse provider → limite declarado em `NFR-003`, fora de escopo desta fatia e encaminhado ao BACKLOG-0003; a sincronização seguirá funcionando em modo incremental sem risco de perda.

#### Suposições

- O modo espelho continua desejável no Qdrant; a alternativa de removê-lo seria mais segura, mas perderia a capacidade de expurgar chunks obsoletos e não foi pedida. Reversível.
- A rejeição da opção antiga permanece indefinidamente, sem prazo de remoção; a mensagem é barata de manter e protege operadores com scripts antigos. Reversível.
- O registro auditável usa o `logging` já configurado em `src/config.py`, sem introduzir formato estruturado novo nesta entrega. Reversível; um formato estruturado pode ser tratado no BACKLOG-0007.
- Não há necessidade de ferramenta administrativa de exclusão sob confirmação neste milestone; se surgir, será um item de backlog próprio.
- A guarda de `FR-007` usa dois critérios objetivos, conjunto esperado vazio e remoção que abrange a totalidade do escopo existente, sem limiar percentual configurável. Um limiar exigiria calibração arbitrária e produziria falso bloqueio em expurgos legítimos grandes. Reversível caso a operação real mostre necessidade.

### 17. Decisões

- **DEC-001**: Reconhecer a opção antiga apenas para emitir erro de migração, em vez de removê-la silenciosamente — a falha genérica do parser não ensina o caminho seguro e levaria o operador a procurar outra forma de recriar a base. Trade-off: mantém um resíduo do vocabulário antigo na CLI.
- **DEC-002**: Preservar o modo espelho no Qdrant com garantia explícita e testada, em vez de eliminá-lo — a remoção já é filtrada por `project_id` e posterior ao upsert, e sem ela chunks obsoletos permaneceriam indefinidamente na base. Trade-off: mantém uma operação de remoção no código, que passa a exigir teste de contrato permanente.
- **DEC-003**: Recusar o modo espelho em ChromaDB e Pinecone antes de qualquer mutação, em vez de implementá-lo agora — a paridade de escopo não está comprovada nesses providers e implementá-la aqui ampliaria o escopo desta fatia. Trade-off: esses providers ficam limitados ao modo incremental até um item de backlog próprio.
- **DEC-004**: Adotar a reexecução idempotente apoiada por manifesto e diagnóstico como procedimento único de recuperação, em vez de manter a recriação sob confirmação — qualquer caminho destrutivo documentado reintroduz o risco que esta fatia elimina. Trade-off: uma base gravemente corrompida exigirá um procedimento administrativo específico, tratado fora deste milestone.
- **DEC-005**: Remover o parâmetro de recriação da assinatura de `index_chunks`, em vez de mantê-lo aceito e ignorado — um parâmetro ignorado esconde a mudança de política e permite que um chamador acredite estar recriando a base. Trade-off: quebra intencional de assinatura interna, coberta pela regressão.
- **DEC-006**: Concentrar as guardas na classe `SyncSafetyPolicy`, em `src/safety.py`, em vez de repetir as verificações nas duas CLIs e na indexação ou de expor funções soltas — atende à orientação a objetos, à coesão e ao baixo acoplamento exigidos em `.specsfy/RULES.md` e garante uma única fonte da política. Trade-off: adiciona um módulo novo ao componente.
- **DEC-007**: Bloquear a sincronização cujo efeito seria remover a totalidade do escopo lógico, em vez de confiar na validação incidental de `project_id` — hoje uma pasta de entrada vazia só falha porque o conjunto de `project_id` fica vazio, um efeito colateral que uma refatoração pode remover sem que ninguém perceba. A proteção passa a ser explícita e testada. Trade-off: um expurgo total legítimo deixa de ser possível pelo fluxo normal e exigirá procedimento administrativo próprio.
- **DEC-008**: Delimitar `NFR-003` ao provider com identidade estável e declarar a duplicação do ChromaDB como limite conhecido, em vez de prometer idempotência universal — o caminho Chroma escreve com `Chroma.from_documents` sem IDs próprios e corrigi-lo exige mudar a forma de escrita desse provider, o que pertence ao BACKLOG-0003. Trade-off: a fatia entrega garantia desigual entre providers, registrada de forma explícita em vez de implícita.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
- [ ] `uv run ruff check .` e `uv run pytest` executados e verdes.
- [ ] `.specsfy/DATABASE.md` revisado, porque o comportamento documentado do modo espelho no Qdrant passa a incluir a guarda de remoção total.
- [ ] `PROJECT.md` revisado quanto ao limite de operações remotas destrutivas, confirmando que o texto descreve o comportamento agora implementado.
- [ ] Busca estática confirma ausência de `delete_collection` e de `delete_all` no código de produção, excluindo `specs/` e `research/`.

## Effort history

- 2026-09-01T01:03:53.659Z: 5 → 6. Revisão semântica acrescentou FR-007, três cenários e a guarda de remoção total, além de encapsular a política em SyncSafetyPolicy; o alcance passou de sete para dez arquivos entre código, testes e documentação.
