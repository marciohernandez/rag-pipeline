# Especificação integrada: Bloquear recriação destrutiva e garantir sincronização segura

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0001 |
| Slug | 0001-bloquear-recriacao-destrutiva |
| Status | Complete |
| Effort | 6 |
| Effort updated at | 2026-09-01T01:03:53.659Z |
| Effort rationale | Revisão semântica acrescentou FR-007, três cenários e a guarda de remoção total, além de encapsular a política em SyncSafetyPolicy; o alcance passou de sete para dez arquivos entre código, testes e documentação. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
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

- `specs/review/0001-bloquear-recriacao-destrutiva/research/auditoria-codigo/caminhos-destrutivos.md`: trechos literais de `pipeline.py`, `upsert_from_chunks.py`, `src/embedder.py`, `README.md`, `GUIA_DE_USO.md`, `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md` e `config.yaml` no commit `5ba9a56`, lidos em 2026-08-31. Licença: código e documentação próprios do projeto, cópia integral permitida. Propósito: preservar o estado auditado, já que a implementação desta spec remove justamente esses trechos.

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
- Bloqueio da limpeza quando não há nada a indexar ou quando o destino não confirma os pontos esperados após o upsert.
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

#### AC-014 — Limpeza bloqueada quando o conjunto esperado não está confirmado

**Cobre**: US-001, FR-003, FR-007, NFR-001

```gherkin
@US-001 @FR-003 @FR-007 @NFR-001 @AC-014
Feature: Proteção contra remoção sem inserção correspondente

  Scenario: Upsert termina sem erro mas o destino não recebeu tudo
    Given uma sincronização em modo espelho com pontos obsoletos no escopo
    When o upsert termina sem erro e o destino não contém cada ponto esperado
    Then a execução termina em erro antes de remover qualquer ponto
    And o registro informa o total esperado e o total confirmado
```

#### AC-015 — Substituição total do escopo permanece permitida

**Cobre**: US-001, FR-003, FR-007, NFR-003

```gherkin
@US-001 @FR-003 @FR-007 @NFR-003 @AC-015
Feature: Proteção contra remoção sem inserção correspondente

  Scenario: Cada documento do projeto é editado na mesma execução
    Given pontos existentes no escopo do project_id da execução
    And um conjunto esperado confirmado no destino que não reaproveita nenhum ponto anterior
    When a sincronização em modo espelho conclui
    Then os pontos anteriores do escopo são removidos
    And o escopo permanece com os pontos esperados da execução
```

### 7. Requisitos

#### Funcionais

- **FR-001**: A CLI deve reconhecer a opção antiga de recriação e encerrar a execução com código de saída diferente de zero e mensagem de migração, antes de instanciar cliente remoto, gerar embeddings ou alterar dados.
- **FR-002**: O código de produção não deve conter caminho alcançável que apague collection, índice ou namespace remoto por inteiro; a camada de indexação não expõe parâmetro que solicite essa exclusão.
- **FR-003**: No modo espelho, o sistema deve remover apenas pontos obsoletos pertencentes ao `project_id` da execução e somente após a conclusão bem-sucedida do upsert de todos os pontos novos ou alterados.
- **FR-004**: O sistema deve interromper a execução antes de qualquer mutação remota quando o escopo lógico for inválido: `project_id` ausente, vazio ou divergente entre chunks, `chunk_id` ausente ou duplicado, ou manifesto incompatível com o conjunto processado.
- **FR-005**: O sistema deve aceitar o modo espelho apenas em provider com garantia de escopo comprovada e recusar a configuração, antes de qualquer mutação, nos demais providers, mantendo neles o modo incremental.
- **FR-006**: `README.md`, `GUIA_DE_USO.md`, `CONTEXTO_MELHORIA_RECUPERACAO_RAG.md` e os comentários de `config.yaml` devem descrever apenas atualização idempotente e recuperação não destrutiva, sem apresentar a recriação como procedimento.
- **FR-007**: O sistema deve interromper a execução antes de qualquer remoção quando o conjunto esperado da execução for vazio, e deve confirmar no destino a presença de cada ponto esperado após o upsert antes de remover qualquer ponto obsoleto. A substituição total do escopo permanece permitida quando o conjunto esperado é não vazio e está confirmado no destino.

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
- Upsert relatado como concluído sem que o destino contenha cada ponto esperado → execução encerrada em erro antes da limpeza, com o total esperado e o total confirmado informados no registro.

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
- **Camada de indexação** (`src/embedder.py`): `index_chunks` perde o parâmetro `recreate`; os blocos `delete_collection` do Qdrant e `delete(delete_all=True)` do Pinecone são removidos. A validação de escopo passa a ocorrer antes de instanciar o cliente. O modo espelho fica restrito ao Qdrant e a remoção de obsoletos continua posterior ao upsert, agora protegida por um sinal explícito de upsert completo. Antes de emitir qualquer `delete`, a indexação consulta a política duas vezes: um conjunto esperado vazio interrompe a execução antes de tocar o destino, e a limpeza só é liberada depois de reler o escopo e confirmar a presença de cada ponto esperado. A substituição total continua permitida, porque os pontos novos já estão confirmados quando os antigos saem.
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
specs/review/0001-bloquear-recriacao-destrutiva/
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
| Execução | Upsert completo | Releitura do escopo não confirma cada ponto esperado | Encerrada em erro | Nenhum ponto removido; totais esperado e confirmado registrados |
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
| US-002, FR-001, FR-002, NFR-001, AC-001 | AC-001 na seção 6 | caso de rejeição sem mutação em tests/test_safety.py com marcador próprio `SPECSFY:` | RED observado antes de T017 | GREEN em T017: rejeição durante o parse, antes de `load_config` | Regressão focal: passed |
| US-002, FR-001, FR-002, NFR-001, AC-002 | AC-002 na seção 6 | caso de ausência de cliente e de embeddings em tests/test_safety.py com marcador próprio `SPECSFY:` | RED observado antes de T017 | GREEN em T017: nenhum cliente nem embedding acionado | Regressão focal: passed |
| US-002, US-003, FR-001, FR-006, AC-003 | AC-003 na seção 6 | caso de mensagem de migração em tests/test_safety.py com marcador próprio `SPECSFY:` | RED observado antes de T017 | GREEN em T017: mensagem contém `--recreate` e `idempotente` | CLI real encerrou com código 2 e mensagem segura |
| US-001, FR-003, NFR-002, NFR-003, AC-004 | AC-004 na seção 6 | caso de dupla execução idempotente em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | RED das contagens observado antes de T019 | GREEN em T019: zero upserts/deletes e quatro contagens registradas | Regressão Qdrant: 8 passed |
| US-001, FR-003, FR-004, NFR-001, AC-005 | AC-005 na seção 6 | caso de falha de upsert sem limpeza em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Caracterização verde antes de T019 | GREEN preservado: falha interrompe antes da confirmação e limpeza | Regressão Qdrant: 8 passed |
| US-001, FR-003, FR-004, NFR-003, AC-006 | AC-006 na seção 6 | caso de isolamento entre project_id em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Caracterização verde antes de T019 | GREEN preservado: leitura e remoção filtradas pelo project_id | Regressão Qdrant: 8 passed |
| US-001, US-003, FR-004, NFR-001, AC-007 | AC-007 na seção 6 | caso de escopo inválido sem mutação em tests/test_safety.py com marcador próprio `SPECSFY:` | RED observado antes de T018 | GREEN em T018: escopo recusado antes de embeddings e cliente | Regressão de segurança: 7 passed |
| US-001, FR-002, FR-005, NFR-001, AC-008 | AC-008 na seção 6 | caso de espelho recusado por provider em tests/test_safety.py com marcador próprio `SPECSFY:` | RED observado antes de T018 | GREEN em T018: espelho restrito ao Qdrant antes de mutação | Regressão de segurança: 7 passed |
| US-003, FR-002, FR-005, NFR-003, AC-009 | AC-009 na seção 6 | caso de append preservado em provider sem garantia em tests/test_safety.py com marcador próprio `SPECSFY:` | RED observado antes de T018 | GREEN em T018: append Chroma preservado e assinatura sem `recreate` | Regressão de segurança: 7 passed |
| US-001, FR-003, FR-006, NFR-002, AC-010 | AC-010 na seção 6 | caso de registro auditável sem segredos em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | RED observado antes de T019 | GREEN em T019: modo, escopo e contagens sem URL ou credencial | Regressão Qdrant: 8 passed |
| US-003, FR-005, FR-006, NFR-002, AC-011 | AC-011 na seção 6 | caso de varredura documental sem termo destrutivo em tests/test_docs_safety.py com marcador próprio `SPECSFY:` | RED observado nas quatro fontes antes de T020 | GREEN em T020: zero termos destrutivos nas fontes publicadas | Regressão documental: 5 passed |
| US-003, FR-001, FR-006, NFR-002, NFR-003, AC-012 | AC-012 na seção 6 | caso de procedimento de recuperação idempotente em tests/test_docs_safety.py com marcador próprio `SPECSFY:` | RED por ausência de procedimento idempotente | GREEN em T020: guia usa manifesto e reexecução idempotente | Revisão manual coerente com a CLI |
| US-001, FR-004, FR-007, NFR-001, AC-013 | AC-013 na seção 6 | caso de conjunto esperado vazio em tests/test_safety.py com marcador próprio `SPECSFY:` | RED observado antes de T018 | GREEN em T018: conjunto vazio recusado antes do destino | Regressão de segurança: 7 passed |
| US-001, FR-003, FR-007, NFR-001, AC-014 | AC-014 na seção 6 | caso de limpeza total bloqueada em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | RED observado antes de T019 | GREEN em T019: destino incompleto bloqueia antes de delete | Regressão Qdrant: 8 passed |
| US-001, FR-003, FR-007, NFR-003, AC-015 | AC-015 na seção 6 | caso de substituição total permitida em tests/test_qdrant_sync.py com marcador próprio `SPECSFY:` | Caracterização verde antes de T019 | GREEN preservado: novos IDs confirmados liberam remoção dos anteriores | Regressão Qdrant: 8 passed |
| US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, NFR-001, NFR-003, AC-001, AC-002, AC-003, AC-007, AC-008, AC-009, AC-013, AC-014, AC-015 | ACs correspondentes na seção 6 | contrato unitário de `SyncSafetyPolicy` em tests/test_safety_policy.py, com seis definições marcadas `SPECSFY:` e dez casos coletados | `env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_safety_policy.py`: 10 falhas por `SyncSafetyPolicy ainda não foi implementada` | 10 passed em 0,06 s após criar `src/safety.py` | Regressão focal repetida após separar normalização de tokens e preservação de identificadores; 10 passed |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001, FR-002, NFR-001 | AC-001 | Integração CLI | `tests/test_safety.py` | Passed — regressão Pytest 37/37 |
| FR-001, FR-002, NFR-001 | AC-002 | Integração CLI | `tests/test_safety.py` | Passed — regressão Pytest 37/37 |
| FR-001, FR-006 | AC-003 | Integração CLI | `tests/test_safety.py` | Passed — regressão Pytest 37/37 |
| FR-003, NFR-002, NFR-003 | AC-004 | Integração/contrato | `tests/test_qdrant_sync.py` | Passed — regressão Pytest 37/37 |
| FR-003, FR-004, NFR-001 | AC-005 | Integração/contrato | `tests/test_qdrant_sync.py` | Passed — regressão Pytest 37/37 |
| FR-003, FR-004, NFR-003 | AC-006 | Integração/contrato | `tests/test_qdrant_sync.py` | Passed — regressão Pytest 37/37 |
| FR-004, NFR-001 | AC-007 | Unidade/integração | `tests/test_safety.py`, `tests/test_safety_policy.py` | Passed — regressão Pytest 37/37 |
| FR-002, FR-005, NFR-001 | AC-008 | Unidade/integração | `tests/test_safety.py`, `tests/test_safety_policy.py` | Passed — regressão Pytest 37/37 |
| FR-002, FR-005, NFR-003 | AC-009 | Unidade/integração | `tests/test_safety.py`, `tests/test_safety_policy.py` | Passed — regressão Pytest 37/37 |
| FR-003, FR-006, NFR-002 | AC-010 | Integração/contrato | `tests/test_qdrant_sync.py` | Passed — regressão Pytest 37/37 |
| FR-005, FR-006, NFR-002 | AC-011 | Unidade documental | `tests/test_docs_safety.py` | Passed — regressão Pytest 37/37 |
| FR-001, FR-006, NFR-002, NFR-003 | AC-012 | Unidade documental | `tests/test_docs_safety.py` | Passed — regressão Pytest 37/37 |
| FR-004, FR-007, NFR-001 | AC-013 | Unidade/integração | `tests/test_safety.py`, `tests/test_safety_policy.py` | Passed — regressão Pytest 37/37 |
| FR-003, FR-007, NFR-001 | AC-014 | Unidade/integração | `tests/test_qdrant_sync.py`, `tests/test_safety_policy.py` | Passed — regressão Pytest 37/37 |
| FR-003, FR-007, NFR-003 | AC-015 | Unidade/integração | `tests/test_qdrant_sync.py`, `tests/test_safety_policy.py` | Passed — regressão Pytest 37/37 |
| FR-001 | AC-001 | Unidade | `tests/test_safety.py` | RED observado |
| FR-001 | AC-002 | Unidade | `tests/test_safety.py` | RED observado |
| FR-001 | AC-003 | Unidade | `tests/test_safety.py` | RED observado |
| FR-001 | AC-012 | Unidade | `tests/test_docs_safety.py` | RED observado |
| FR-002 | AC-001 | Unidade | `tests/test_safety.py` | RED observado |
| FR-002 | AC-002 | Unidade | `tests/test_safety.py` | RED observado |
| FR-002 | AC-008 | Integração/contrato | `tests/test_safety.py` | RED observado |
| FR-002 | AC-009 | Integração/contrato | `tests/test_safety.py` | RED observado |
| FR-003 | AC-004 | Integração/contrato | `tests/test_qdrant_sync.py` | RED observado |
| FR-003 | AC-005 | Integração/contrato | `tests/test_qdrant_sync.py` | Caracterização verde |
| FR-003 | AC-006 | Integração/contrato | `tests/test_qdrant_sync.py` | Caracterização verde |
| FR-003 | AC-010 | Integração/contrato | `tests/test_qdrant_sync.py` | RED observado |
| FR-003 | AC-014 | Integração/contrato | `tests/test_qdrant_sync.py` | RED observado |
| FR-003 | AC-015 | Integração/contrato | `tests/test_qdrant_sync.py` | Caracterização verde |
| FR-004 | AC-005 | Integração/contrato | `tests/test_qdrant_sync.py` | Caracterização verde |
| FR-004 | AC-006 | Integração/contrato | `tests/test_qdrant_sync.py` | Caracterização verde |
| FR-004 | AC-007 | Unidade | `tests/test_safety.py` | RED observado |
| FR-004 | AC-013 | Unidade | `tests/test_safety.py` | RED observado |
| FR-005 | AC-008 | Unidade | `tests/test_safety.py` | RED observado |
| FR-005 | AC-009 | Integração/contrato | `tests/test_safety.py` | RED observado |
| FR-005 | AC-011 | Unidade | `tests/test_docs_safety.py` | RED observado |
| FR-006 | AC-003 | Unidade | `tests/test_safety.py` | RED observado |
| FR-006 | AC-010 | Integração/contrato | `tests/test_qdrant_sync.py` | RED observado |
| FR-006 | AC-011 | Unidade | `tests/test_docs_safety.py` | RED observado |
| FR-006 | AC-012 | Unidade | `tests/test_docs_safety.py` | RED observado |
| FR-007 | AC-013 | Unidade | `tests/test_safety.py` | RED observado |
| FR-007 | AC-014 | Integração/contrato | `tests/test_qdrant_sync.py` | RED observado |
| FR-007 | AC-015 | Integração/contrato | `tests/test_qdrant_sync.py` | Caracterização verde |
| NFR-001 | AC-001 | Unidade | `uv run pytest tests/test_safety.py` | RED observado |
| NFR-001 | AC-002 | Unidade | `uv run pytest tests/test_safety.py` | RED observado |
| NFR-001 | AC-005 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Caracterização verde |
| NFR-001 | AC-007 | Unidade | `uv run pytest tests/test_safety.py` | RED observado |
| NFR-001 | AC-008 | Unidade | `uv run pytest tests/test_safety.py` | RED observado |
| NFR-001 | AC-013 | Unidade | `uv run pytest tests/test_safety.py` | RED observado |
| NFR-001 | AC-014 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | RED observado |
| NFR-002 | AC-004 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | RED observado |
| NFR-002 | AC-010 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | RED observado |
| NFR-002 | AC-011 | Unidade | `uv run pytest tests/test_docs_safety.py` | RED observado |
| NFR-002 | AC-012 | Unidade | `uv run pytest tests/test_docs_safety.py` | RED observado |
| NFR-003 | AC-004 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | RED observado |
| NFR-003 | AC-006 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Caracterização verde |
| NFR-003 | AC-009 | Integração/contrato | `uv run pytest tests/test_safety.py` | RED observado |
| NFR-003 | AC-012 | Unidade | `uv run pytest tests/test_docs_safety.py` | RED observado |
| NFR-003 | AC-015 | Integração/contrato | `uv run pytest tests/test_qdrant_sync.py` | Caracterização verde |
| FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, NFR-001, NFR-003 | AC-001, AC-002, AC-003, AC-007, AC-008, AC-009, AC-013, AC-014, AC-015 | Unidade | `env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_safety_policy.py` | RED: 10 falhas pela ausência explícita de `SyncSafetyPolicy`; GREEN/refactor: 10 passed em 0,06 s; proteção do banco `SAFE` |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed em 2026-08-31, na segunda avaliação. A primeira aprovação foi invalidada no mesmo dia por mudança de comportamento em FR-007, AC-014 e AC-015, registrada em DEC-007 e classificada por `analyze_change.mjs --mode impact` como reabertura de Ato I
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/review/0001-bloquear-recriacao-destrutiva/spec.md`
- **Achados**: estrutura `VALID`; research `PASSED` com quatro claims, três críticas verificadas; cobertura mínima atendida com 3 US, 7 FR, 3 NFR e 15 AC, cada `US`, `FR` e `NFR` coberto por três ou mais cenários distintos. Quatro findings foram levantados e todos resolvidos na fonte antes da aprovação; nenhum `P1 Open` permanece.
- **FIND-SEC-001** [P1] [Resolved] Uma execução cujo conjunto esperado fica vazio faria o modo espelho remover todos os pontos do escopo, reproduzindo o efeito da recriação que esta fatia elimina; hoje isso só falha como efeito colateral da validação de `project_id`, que uma refatoração pode remover sem que ninguém perceba — Refs: FR-003, FR-004, FR-007, AC-013, AC-014 — Evidence: specs/review/0001-bloquear-recriacao-destrutiva/research/auditoria-codigo/caminhos-destrutivos.md:156 — Effect: perda ampla e irreversível da base de um cliente por pasta de entrada vazia ou falha silenciosa de carregamento, exatamente o risco que a spec existe para impedir — Suggestion: resolvido pela criação de FR-007, dos cenários AC-013 a AC-015 e da guarda `assert_removal_allowed` em `SyncSafetyPolicy`; a primeira redação bloqueava pela proporção removida e foi corrigida em DEC-007 para conjunto esperado não vazio mais confirmação no destino.
- **FIND-PROD-002** [P2] [Resolved] `NFR-003` prometia idempotência para toda a sincronização, mas o caminho ChromaDB escreve com `Chroma.from_documents` sem IDs estáveis e duplica registros a cada execução, tornando o requisito impossível de cumprir dentro do escopo declarado — Refs: NFR-003, AC-004, AC-009 — Evidence: specs/review/0001-bloquear-recriacao-destrutiva/research/auditoria-codigo/caminhos-destrutivos.md:199 — Effect: requisito não verificável para um provider suportado, o que aprovaria um gate sobre promessa que a entrega não sustenta — Suggestion: resolvido delimitando `NFR-003` ao provider com identidade estável, declarando a duplicação do ChromaDB como limite conhecido em `DEC-008` e encaminhando a correção ao BACKLOG-0003.
- **FIND-ARCH-003** [P2] [Resolved] O plano previa as guardas como funções soltas em `src/safety.py`, o que conflita com a regra de orientação a objetos e encapsulamento confirmada pela pessoa responsável e registrada em `PR-001` — Refs: FR-001, FR-004, FR-005 — Evidence: .specsfy/RULES.md:14 — Effect: introdução de um módulo procedural novo contra uma regra explícita do projeto, criando precedente e dificultando a extensão multi-tenant do BACKLOG-0002 — Suggestion: resolvido encapsulando a política na classe `SyncSafetyPolicy`, com métodos nomeados por obrigação, conforme `DEC-006`.
- **FIND-PROD-004** [P2] [Resolved] A primeira redação de FR-007 bloqueava a limpeza que abrangesse a totalidade do escopo, mas o `chunk_id` deriva do `source_hash` do documento inteiro, de modo que editar cada documento de um projeto troca todos os IDs e transforma uma substituição de rotina em erro; o próprio teste existente `test_upserts_new_points_then_removes_only_stale_points` passaria a falhar — Refs: FR-007, AC-014, AC-015 — Evidence: src/identity.py:56 — Effect: falso bloqueio de uma operação legítima e frequente, com o operador levado a procurar um caminho alternativo fora do fluxo seguro — Suggestion: resolvido em DEC-007 trocando o critério de proporção por conjunto esperado não vazio mais confirmação dos pontos esperados no destino, o que também passa a detectar o upsert que relata sucesso sem gravar tudo.
- Findings especializados seguem `FIND-PROD|ARCH|SEC-NNN`, severidade `P1|P2|P3`,
  estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed em 2026-09-01 após explicitar a fixture necessária à confirmação pós-upsert.
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0001-bloquear-recriacao-destrutiva/spec.md --allow-draft`
- **Achados**: `VALID DRAFT`, com 23 tarefas, 19 concluídas, 17 TDD, 4 de código, 138 itens de checklist, 114 concluídos e 28/28 IDs cobertos. A suíte Qdrant apresentou 3 falhas pelo comportamento ausente e 5 caracterizações verdes. T019 agora inclui explicitamente o ajuste do cliente falso legado para reproduzir no `scroll` a visibilidade dos pontos aceitos por `upsert`, sem introduzir exceção específica para testes no código de produção.

#### Gate do Ato III — Entrega

- **Resultado**: Passed em 2026-09-01.
- **Comando**: `env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0001-bloquear-recriacao-destrutiva/spec.md . --full-chain`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/in-progress/0001-bloquear-recriacao-destrutiva/spec.md .`.
- **Achados**: Pytest passou 37/37; rastreabilidade passou 28/28 IDs em sete arquivos, inclusive com cadeia completa; QA retornou `PASSED` para AC-001 a AC-015. As buscas estáticas não encontraram `delete_collection` ou `delete_all` no código de produção nem os três termos destrutivos nas quatro fontes publicadas. Ruff permanece ausente e encaminhado ao BACKLOG-0007. `.specsfy/DATABASE.md`, `PROJECT.md`, `docs/` e `.specsfy/PACKAGES.md` foram revisados; o monitor terminou `CURRENT`. No aceite final em `review`, `validate_spec.mjs` retornou `READY`, `review_findings.mjs --root .` retornou `PASSED` para quatro findings resolvidos e `verify_repo.mjs` retornou `PASSED` na fronteira local, incluindo spec, tarefas, catálogo de skills e canários.

### 14. Tarefas

Formato:
`- [ ] TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Cada tarefa mantém o checklist `PREP`, `EXECUTE`, `VERIFY`, `VISUAL`, `EVIDENCE` e
`IMPROVE`, nessa ordem. O runner é Pytest, já presente em `pyproject.toml` e em
`tests/`; nenhum arquivo `.feature` é criado ou executado.

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-002] Derivar do AC-001 um caso Pytest falhando em tests/test_safety.py, cobrindo a rejeição da opção destrutiva sem nenhuma mutação remota — Refs: US-002, FR-001, FR-002, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Ler o AC-001 na seção 6 e desenhar o cliente falso que registra cada chamada emitida.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-001`, afirmando código de saída diferente de zero e lista de mutações vazia.
  - [x] **VERIFY**: Observar RED por ausência da guarda: hoje a flag executa a exclusão.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-001 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-001 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T002 [TEST] [TDD] [US-002] Derivar do AC-002 um caso Pytest falhando em tests/test_safety.py, cobrindo a ausência de cliente remoto e de embeddings na rejeição — Refs: US-002, FR-001, FR-002, NFR-001, AC-002 — Depends: none
  - [x] **PREP**: Ler o AC-002 e definir os pontos de instrumentação do construtor do cliente e do gerador de embeddings.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-002`, afirmando zero instanciações de cliente e zero chamadas de embedding.
  - [x] **VERIFY**: Observar RED por ausência da guarda: hoje o cliente é criado antes de qualquer verificação.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-002 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-002 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T003 [TEST] [TDD] [US-002] Derivar do AC-003 um caso Pytest falhando em tests/test_safety.py, cobrindo a mensagem de migração que indica o caminho seguro — Refs: US-002, US-003, FR-001, FR-006, AC-003 — Depends: none
  - [x] **PREP**: Ler o AC-003 e definir o conteúdo mínimo verificável da mensagem, sem fixar redação literal frágil.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-003`, afirmando menção à remoção por política e à sincronização idempotente.
  - [x] **VERIFY**: Observar RED por ausência da mensagem: hoje a flag executa em silêncio.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-003 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-003 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso Pytest falhando em tests/test_qdrant_sync.py, cobrindo a reexecução idempotente sem alteração da base — Refs: US-001, FR-003, NFR-002, NFR-003, AC-004 — Depends: none
  - [x] **PREP**: Ler o AC-004 e estender o cliente falso existente para acumular estado entre duas execuções.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-004`, afirmando zero inseridos, zero removidos e conjunto de IDs idêntico.
  - [x] **VERIFY**: Observar RED pela ausência das contagens exigidas no registro da execução.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-004 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-004 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 um caso Pytest falhando em tests/test_qdrant_sync.py, cobrindo a interrupção antes da limpeza quando o upsert falha — Refs: US-001, FR-003, FR-004, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Ler o AC-005 e preparar o cliente falso para falhar em um lote intermediário de upsert.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-005`, afirmando erro propagado e nenhuma chamada de remoção registrada.
  - [x] **VERIFY**: Observar RED enquanto a ordem segura não estiver explícita e coberta.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-005 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-005 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-006 um caso Pytest falhando em tests/test_qdrant_sync.py, cobrindo o isolamento entre dois project_id na mesma collection — Refs: US-001, FR-003, FR-004, NFR-003, AC-006 — Depends: none
  - [x] **PREP**: Ler o AC-006 e povoar o cliente falso com pontos de dois escopos lógicos distintos.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-006`, afirmando que nenhum ponto do outro escopo é lido para remoção nem removido.
  - [x] **VERIFY**: Observar RED enquanto a garantia de isolamento não estiver coberta por teste próprio.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-006 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-006 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T007 [TEST] [TDD] [US-001] Derivar do AC-007 um caso Pytest falhando em tests/test_safety.py, cobrindo o bloqueio de remoção quando o escopo lógico é inválido — Refs: US-001, US-003, FR-004, NFR-001, AC-007 — Depends: none
  - [x] **PREP**: Ler o AC-007 e enumerar as variações: project_id ausente, vazio e divergente entre chunks.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-007`, afirmando erro antes de qualquer mutação em cada variação.
  - [x] **VERIFY**: Observar RED por ausência da guarda dedicada fora da camada de indexação.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-007 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-007 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T008 [TEST] [TDD] [US-001] Derivar do AC-008 um caso Pytest falhando em tests/test_safety.py, cobrindo a recusa do modo espelho em provider sem garantia — Refs: US-001, FR-002, FR-005, NFR-001, AC-008 — Depends: none
  - [x] **PREP**: Ler o AC-008 e listar os providers sem paridade comprovada segundo a evidência em `research/`.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-008`, afirmando erro antes de qualquer mutação e menção aos providers suportados.
  - [x] **VERIFY**: Observar RED porque hoje `sync_mode` é ignorado fora do caminho Qdrant.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-008 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-008 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-009 um caso Pytest falhando em tests/test_safety.py, cobrindo a preservação do modo incremental em provider sem garantia — Refs: US-003, FR-002, FR-005, NFR-003, AC-009 — Depends: none
  - [x] **PREP**: Ler o AC-009 e separar o que continua permitido do que passa a ser recusado.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-009`, afirmando adição normal dos pontos e nenhuma exclusão solicitada.
  - [x] **VERIFY**: Observar RED enquanto a distinção entre recusar espelho e preservar append não estiver coberta.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-009 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-009 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T010 [TEST] [TDD] [US-001] Derivar do AC-010 um caso Pytest falhando em tests/test_qdrant_sync.py, cobrindo o registro auditável da sincronização sem segredos — Refs: US-001, FR-003, FR-006, NFR-002, AC-010 — Depends: none
  - [x] **PREP**: Ler o AC-010 e definir a captura dos registros por `caplog` e os segredos que não podem aparecer.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-010`, afirmando presença de modo, escopo e quatro contagens, e ausência de credencial e URL.
  - [x] **VERIFY**: Observar RED porque o registro atual não informa previstos, mantidos e removidos de forma consolidada.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-010 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-010 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 um caso Pytest falhando em tests/test_docs_safety.py, cobrindo a ausência de procedimento destrutivo na documentação publicada — Refs: US-003, FR-005, FR-006, NFR-002, AC-011 — Depends: none
  - [x] **PREP**: Ler o AC-011 e fixar a lista de arquivos varridos e os termos rastreados, excluindo `specs/` e `research/`.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-011`, afirmando zero ocorrências de recomendação de recriação nos arquivos publicados.
  - [x] **VERIFY**: Observar RED pelas ocorrências atuais em README, guia, contexto e configuração.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal, os arquivos varridos e a causa do RED nas linhas de AC-011 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-011 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso Pytest falhando em tests/test_docs_safety.py, cobrindo a presença do procedimento de recuperação idempotente — Refs: US-003, FR-001, FR-006, NFR-002, NFR-003, AC-012 — Depends: none
  - [x] **PREP**: Ler o AC-012 e definir os marcadores textuais que comprovam o procedimento por manifesto e reexecução.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-012`, afirmando presença do procedimento idempotente e ausência da recriação como alternativa.
  - [x] **VERIFY**: Observar RED porque o procedimento publicado hoje é a recriação.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-012 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-012 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T013 [TEST] [TDD] [US-001] Derivar do AC-013 um caso Pytest falhando em tests/test_safety.py, cobrindo o bloqueio da execução com conjunto esperado vazio — Refs: US-001, FR-004, FR-007, NFR-001, AC-013 — Depends: none
  - [x] **PREP**: Ler o AC-013 e confirmar que a proteção não pode depender do efeito colateral da validação de project_id.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-013`, afirmando erro dedicado e nenhuma mutação remota com conjunto esperado vazio.
  - [x] **VERIFY**: Observar RED porque hoje só existe a falha incidental por conjunto de project_id vazio.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-013 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-013 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T014 [TEST] [TDD] [US-001] Derivar do AC-014 um caso Pytest falhando em tests/test_qdrant_sync.py, cobrindo o bloqueio da limpeza quando o destino não confirma os pontos esperados — Refs: US-001, FR-003, FR-007, NFR-001, AC-014 — Depends: none
  - [x] **PREP**: Ler o AC-014 e montar o cliente falso cujo upsert relata sucesso sem registrar cada ponto esperado.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-014`, afirmando erro antes da primeira remoção e totais esperado e confirmado no registro.
  - [x] **VERIFY**: Observar RED porque hoje a limpeza confia no upsert sem reler o destino.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-014 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-014 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T015 [TEST] [TDD] [US-001] Derivar do AC-015 um caso Pytest falhando em tests/test_qdrant_sync.py, cobrindo a permissão da substituição total confirmada — Refs: US-001, FR-003, FR-007, NFR-003, AC-015 — Depends: none
  - [x] **PREP**: Ler o AC-015 e montar o cenário de substituição total, em que nenhum ponto anterior é reaproveitado.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: AC-015`, afirmando remoção dos pontos anteriores e permanência dos pontos esperados no escopo.
  - [x] **VERIFY**: Confirmar que o comportamento já existe hoje e registrar o caso como caracterização que protege a substituição total contra a guarda nova.
  - [x] **VISUAL**: Não aplicável — a tarefa materializa teste em um componente de linha de comando, sem superfície visual; a conferência equivalente é a leitura da mensagem de erro e do registro produzidos pelo caso.
  - [x] **EVIDENCE**: Registrar o comando focal e a causa do RED nas linhas de AC-015 das seções 11 e 12.
  - [x] **IMPROVE**: Registrar o que o desenho de AC-015 revelou sobre a cobertura vizinha ou justificar que nada mudou.

- [x] T023 [TEST] [TDD] [US-001] Materializar o contrato unitário de SyncSafetyPolicy em tests/test_safety_policy.py — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-004, FR-005, FR-007, NFR-001, AC-001, AC-002, AC-003, AC-007, AC-008, AC-009, AC-013 — Depends: T001, T002, T003, T007, T008, T009, T013
  - [x] **PREP**: Cada função de `SyncSafetyPolicy` foi relacionada aos cenários aprovados, sem antecipar a integração com CLI, clientes remotos ou embeddings; nível unitário confirmado por `references/test-levels.md`.
  - [x] **EXECUTE**: Criados testes unitários para `reject_destructive_option`, `assert_sync_mode_supported`, `assert_valid_scope` e `assert_removal_allowed`, incluindo caminhos permitidos e mensagens de falha verificáveis.
  - [x] **VERIFY**: `env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_safety_policy.py` coletou dez casos e observou RED pela ausência explícita de `SyncSafetyPolicy`, sem falha de infraestrutura.
  - [x] **VISUAL**: Não aplicável — a política não possui superfície visual; a conferência equivalente foi o relatório focal do Pytest.
  - [x] **EVIDENCE**: O comando, a proteção do banco `SAFE`, as dez falhas e os IDs cobertos foram registrados nas seções 11 a 13.
  - [x] **IMPROVE**: A separação entre contrato unitário e integração tornou verificável a ordem T023 → T016 → T017/T018 e eliminou a expectativa incorreta de GREEN de integração em T016.
#### Fase 2 — US-002 Receber erro claro ao usar a opção antiga (P1)

**Objetivo**: nenhuma execução consegue solicitar recriação e o operador é redirecionado ao caminho seguro.
**Teste independente**: `uv run pytest tests/test_safety.py` verde e `uv run python pipeline.py --recreate` terminando em erro sem abrir conexão remota.

- [x] T016 [CODE] [US-002] Criar a classe SyncSafetyPolicy em src/safety.py — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-004, FR-005, FR-007, NFR-001, AC-001, AC-002, AC-003, AC-007, AC-008, AC-009, AC-013 — Depends: T001, T002, T003, T007, T008, T009, T013, T023
  - [x] **PREP**: RED focal confirmado com dez falhas em `tests/test_safety_policy.py`; `docs/` e `.specsfy/PACKAGES.md` foram reconstruídos e validados por `$specsfy-documentator` antes da alteração de produção.
  - [x] **EXECUTE**: Implementada `SyncSafetyPolicy` com `reject_destructive_option`, `assert_sync_mode_supported`, `assert_valid_scope` e `assert_removal_allowed`, cada grupo com exceção e mensagem próprias, sem tocar em `src/embedder.py`.
  - [x] **VERIFY**: `env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_safety_policy.py` confirmou GREEN com 10/10 casos; os sete casos de integração permanecem sob responsabilidade de T017 e T018.
  - [x] **VISUAL**: Não aplicável — o componente é operado por linha de comando e não possui tela; a conferência equivalente foi a leitura das mensagens exercitadas pelo teste focal.
  - [x] **EVIDENCE**: GREEN, `src/safety.py`, os IDs cobertos, a reconstrução documental e o monitor `CURRENT` foram registrados nas seções 11 a 13.
  - [x] **IMPROVE**: A política ficou coesa em uma classe e o refactor separou tokens normalizados de identificadores, preservando IDs sensíveis a capitalização sem alterar o contrato.
  <!-- specsfy:evidence {"task":"T016","refs":["US-001","US-002","US-003","FR-001","FR-002","FR-004","FR-005","FR-007","NFR-001","AC-001","AC-002","AC-003","AC-007","AC-008","AC-009","AC-013"],"files":["src/safety.py"],"commands":[{"run":"env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_safety_policy.py","exit":0}]} -->

- [x] T017 [CODE] [US-002] Aplicar a rejeição da opção antiga em pipeline.py e em upsert_from_chunks.py — Refs: US-002, FR-001, FR-002, NFR-001, AC-001, AC-002, AC-003 — Depends: T001, T002, T003, T016
  - [x] **PREP**: GREEN de T016 confirmado; `main` foi mapeado para executar a guarda durante o parse, antes de `load_config`, `load_dotenv`, documentos, cliente ou embeddings; `docs/` foi reconstruído e validado por `$specsfy-documentator`.
  - [x] **EXECUTE**: `SyncSafetyPolicy.reject_destructive_option` foi consumida durante o parse das duas CLIs e a propagação de `recreate` para `index_chunks` foi removida.
  - [x] **VERIFY**: O comando focal passou 3/3 casos; `env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run python pipeline.py --recreate` encerrou com código 2 e mensagem de migração.
  - [x] **VISUAL**: Não aplicável — o componente é operado por linha de comando e não possui tela; a conferência equivalente confirmou a mensagem renderizada no terminal.
  - [x] **EVIDENCE**: GREEN, código de saída 2, `pipeline.py`, `upsert_from_chunks.py`, reconstrução documental e monitor `CURRENT` registrados.
  - [x] **IMPROVE**: A validação foi concentrada em `parse_args`, garantindo uma única saída padrão do argparse e eliminando o parâmetro destrutivo das chamadas de indexação.
  <!-- specsfy:evidence {"task":"T017","refs":["US-002","FR-001","FR-002","NFR-001","AC-001","AC-002","AC-003"],"files":["pipeline.py","upsert_from_chunks.py"],"commands":[{"run":"env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_safety.py -k 'pipeline_rejeita or reupsert_rejeita or mensagem_de_migracao'","exit":0}]} -->

**Checkpoint**: `uv run python pipeline.py --recreate` falha com mensagem de migração, sem abrir conexão remota e sem gerar embeddings.

#### Fase 3 — US-001 Sincronizar sem risco de perda ampla (P1)

**Objetivo**: a camada de indexação perde cada caminho destrutivo e mantém o espelho restrito, ordenado e auditável.
**Teste independente**: `uv run pytest tests/test_qdrant_sync.py` verde, incluindo reexecução idempotente, isolamento entre projetos e bloqueio da remoção total.

- [x] T018 [CODE] [US-001] Remover o parâmetro recreate e os caminhos destrutivos de src/embedder.py — Refs: US-001, US-002, FR-002, FR-003, FR-005, NFR-001, AC-001, AC-005, AC-008, AC-009 — Depends: T001, T005, T008, T009, T016, T017
  - [x] **PREP**: Os únicos chamadores de produção de `index_chunks` foram confirmados em `pipeline.py` e `upsert_from_chunks.py`, já sem propagação de `recreate`; cada uso restante foi localizado e `docs/` foi reconstruído e validado por `$specsfy-documentator`.
  - [x] **EXECUTE**: O parâmetro `recreate`, o bloco `delete_collection` do Qdrant e o bloco `delete(delete_all=True)` do Pinecone foram removidos; `SyncSafetyPolicy` valida modo e escopo antes de embeddings e clientes.
  - [x] **VERIFY**: `env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_safety.py` passou 7/7; `rg` retornou vazio para `delete_collection|delete_all` no código Python de produção.
  - [x] **VISUAL**: Não aplicável — o componente é operado por linha de comando e não possui tela; a conferência equivalente foi a saída da suíte de segurança e da busca estática.
  - [x] **EVIDENCE**: GREEN 7/7, busca estática vazia, `src/embedder.py`, reconstrução documental e monitor `CURRENT` registrados.
  - [x] **IMPROVE**: A validação comum foi movida para antes da criação de embeddings e de qualquer provider, reduzindo a superfície fail-open e removendo validações Qdrant duplicadas.
  <!-- specsfy:evidence {"task":"T018","refs":["US-001","US-002","FR-002","FR-003","FR-005","NFR-001","AC-001","AC-005","AC-008","AC-009"],"files":["src/embedder.py"],"commands":[{"run":"env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_safety.py","exit":0}]} -->

- [x] T019 [CODE] [US-001] Garantir a ordem upsert completo para limpeza, a confirmação dos pontos esperados no destino e o registro auditável em src/embedder.py — Refs: US-001, FR-003, FR-004, FR-006, FR-007, NFR-002, NFR-003, AC-004, AC-005, AC-006, AC-010, AC-014, AC-015 — Depends: T004, T005, T006, T010, T014, T015, T018
  - [x] **PREP**: A suíte Qdrant confirmou 3 falhas por comportamento ausente e 5 caracterizações verdes; a interface de `assert_removal_allowed` foi revisada e `docs/` foi reconstruído e validado por `$specsfy-documentator`.
  - [x] **EXECUTE**: O fluxo relê o escopo após todos os upserts, consulta `assert_removal_allowed`, remove somente depois da confirmação e registra modo, project_id e contagens; `FakeClient.upsert` agora torna pontos gravados visíveis ao `scroll`.
  - [x] **VERIFY**: `env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_qdrant_sync.py` passou 8/8; a regressão conjunta de segurança passou 25/25. A regressão completa permanece em T022, após as tarefas documentais.
  - [x] **VISUAL**: Não aplicável — o componente é operado por linha de comando e não possui tela; a conferência equivalente validou o registro auditável capturado e as chamadas do cliente falso.
  - [x] **EVIDENCE**: GREEN 8/8, regressão 25/25, contagens da reexecução idempotente, `src/embedder.py`, fixture ajustada, documentação reconstruída e monitor `CURRENT` registrados.
  - [x] **IMPROVE**: A leitura paginada foi encapsulada em `scope_ids`, reduzindo duplicação e tornando explícitas as duas fotografias do escopo: antes do upsert e antes da limpeza.
  <!-- specsfy:evidence {"task":"T019","refs":["US-001","FR-003","FR-004","FR-006","FR-007","NFR-002","NFR-003","AC-004","AC-005","AC-006","AC-010","AC-014","AC-015"],"files":["src/embedder.py","tests/test_qdrant_sync.py"],"commands":[{"run":"env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_qdrant_sync.py","exit":0}]} -->

**Checkpoint**: reexecução sobre a mesma entrada registra zero inseridos e zero removidos, com pontos de outro `project_id` intactos e a remoção total bloqueada.

#### Fase 4 — US-003 Recuperar uma base inconsistente sem apagar tudo (P1)

**Objetivo**: a documentação publicada deixa de ensinar o caminho destrutivo e passa a descrever a recuperação idempotente.
**Teste independente**: `uv run pytest tests/test_docs_safety.py` verde e leitura confirmando o novo procedimento.

- [x] T020 [DOC] [US-003] Substituir o procedimento destrutivo em README.md, GUIA_DE_USO.md, CONTEXTO_MELHORIA_RECUPERACAO_RAG.md e config.yaml — Refs: US-003, FR-001, FR-005, FR-006, NFR-002, NFR-003, AC-003, AC-011, AC-012 — Depends: T011, T012, T017, T018, T019
  - [x] **PREP**: As ocorrências foram confirmadas em README.md, GUIA_DE_USO.md, CONTEXTO_MELHORIA_RECUPERACAO_RAG.md e config.yaml; a suíte documental registrou cinco falhas antes da edição.
  - [x] **EXECUTE**: Atualização e recuperação foram reescritas como fluxo idempotente apoiado por chunks, manifesto, confirmação e diagnóstico; a recomendação destrutiva foi removida das quatro fontes e o limite incremental de Pinecone/ChromaDB foi explicitado.
  - [x] **VERIFY**: `env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_docs_safety.py` passou 5/5; a releitura confirmou coerência com a mensagem de sincronização idempotente da CLI.
  - [x] **VISUAL**: Não aplicável — a tarefa altera texto de documentação, sem superfície visual renderizada; a conferência equivalente foi editorial e automatizada.
  - [x] **EVIDENCE**: GREEN 5/5, busca vazia pelos termos proibidos, quatro arquivos alterados, documentação técnica reconstruída e monitor `CURRENT` registrados.
  - [x] **IMPROVE**: O guia agora diferencia claramente o espelho Qdrant do modo incremental de Pinecone/ChromaDB, evitando prometer remoção automática onde ela não existe.
  <!-- specsfy:evidence {"task":"T020","refs":["US-003","FR-001","FR-005","FR-006","NFR-002","NFR-003","AC-003","AC-011","AC-012"],"files":["README.md","GUIA_DE_USO.md","CONTEXTO_MELHORIA_RECUPERACAO_RAG.md","config.yaml"],"commands":[{"run":"env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest tests/test_docs_safety.py","exit":0}]} -->

**Checkpoint**: nenhum documento publicado apresenta a recriação como procedimento de atualização ou de recuperação.

#### Fase 5 — Contexto persistente do projeto

- [x] T021 [DOC] Atualizar o comportamento do modo espelho em .specsfy/DATABASE.md — Refs: FR-003, FR-007, AC-014, AC-015 — Depends: T019
  - [x] **PREP**: A seção `Decisões, ownership e retenção` foi comparada com o fluxo implementado em T019 e com o contrato de `SyncSafetyPolicy`.
  - [x] **EXECUTE**: `$specsfy-aux-database` registrou que a remoção exige escopo válido, conjunto esperado não vazio, upsert completo e confirmação no destino, preservando a substituição total confirmada; migrations internas de `.venv` detectadas automaticamente foram excluídas por não pertencerem ao domínio.
  - [x] **VERIFY**: O monitor retornou `CURRENT` com os caminhos revisados, a reconstrução documental e a ausência de mudança narrativa em `PROJECT.md` explicitamente informadas.
  - [x] **VISUAL**: Não aplicável — a tarefa altera texto de documentação, sem superfície visual renderizada; a conferência equivalente foi a comparação entre mapa, código e testes.
  - [x] **EVIDENCE**: `.specsfy/DATABASE.md`, o comando do monitor e o resultado `CURRENT` foram registrados.
  - [x] **IMPROVE**: O mapa agora descreve as duas provas objetivas da limpeza e evita incorporar schemas internos de dependências como se fossem estruturas do domínio.
  <!-- specsfy:evidence {"task":"T021","refs":["FR-003","FR-007","AC-014","AC-015"],"files":[".specsfy/DATABASE.md"],"commands":[{"run":"node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --paths src/embedder.py src/safety.py .specsfy/DATABASE.md docs/README.md .specsfy/PACKAGES.md --acknowledge-project-no-change --check","exit":0}]} -->

#### Fase final — Qualidade

- [x] T022 [TEST] Executar regressão Pytest e rastreabilidade sobre tests/test_safety.py, tests/test_qdrant_sync.py e tests/test_docs_safety.py — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015 — Depends: T016, T017, T018, T019, T020, T021
  - [x] **PREP**: As suítes e os três gates foram identificados; Ruff continua ausente de `pyproject.toml` e `uv.lock`, conforme o alcance do BACKLOG-0007.
  - [x] **EXECUTE**: A regressão Pytest, a rastreabilidade normal e `--full-chain` e o auditor de aceite foram executados sobre a spec em `in-progress`.
  - [x] **VERIFY**: Não há lacuna: 28/28 IDs cobertos, AC-001 a AC-015 com resultado `Passed`; `PROJECT.md` mantém o limite correto para operações remotas destrutivas, sem necessidade de mudança material.
  - [x] **VISUAL**: Não aplicável — a entrega não possui interface renderizada; a conferência equivalente abrangeu mensagens CLI, registros, documentação e matrizes de aceite.
  - [x] **EVIDENCE**: Foram registrados 37/37 testes, rastreabilidade 28/28, QA `PASSED`, buscas estáticas vazias e monitor `CURRENT` nas seções 11 a 13.
  - [x] **IMPROVE**: FIND-SEC-001 mostrou que uma falha incidental não é uma guarda; a entrega passou a nomear e testar diretamente conjunto vazio e confirmação pós-upsert, além de separar testes unitários dos de integração.
  <!-- specsfy:evidence {"task":"T022","refs":["US-001","US-002","US-003","FR-001","FR-002","FR-003","FR-004","FR-005","FR-006","FR-007","NFR-001","NFR-002","NFR-003","AC-001","AC-002","AC-003","AC-004","AC-005","AC-006","AC-007","AC-008","AC-009","AC-010","AC-011","AC-012","AC-013","AC-014","AC-015"],"files":["tests/test_safety.py","tests/test_safety_policy.py","tests/test_qdrant_sync.py","tests/test_docs_safety.py"],"commands":[{"run":"env UV_CACHE_DIR=/tmp/rag-ingestion-uv-cache uv run pytest","exit":0},{"run":"node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0001-bloquear-recriacao-destrutiva/spec.md . --full-chain","exit":0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001 a T015 → T023 → T016 → T017 → T018 → T019 → T020 → T021 → T022.
- Tarefas paralelas: nenhuma tarefa recebe `[P]`, porque as tarefas TDD compartilham arquivo dentro de cada grupo. Os três arquivos de teste são independentes entre si, então os grupos T001/T002/T003/T007/T008/T009/T013 em `tests/test_safety.py`, T004/T005/T006/T010/T014/T015 em `tests/test_qdrant_sync.py` e T011/T012 em `tests/test_docs_safety.py` podem ser escritos em qualquer ordem relativa, um grupo por vez em cada arquivo.
- Estratégia de MVP: a menor entrega segura é T016 mais T017 mais T018, que elimina cada caminho destrutivo alcançável. T019 consolida a garantia do espelho e T020 fecha o vetor documental; nenhuma delas pode ficar de fora do milestone M0, porque o guia publicado reintroduz o risco na prática.

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
- Pasta de entrada vazia, falha silenciosa de carregamento ou upsert que relata sucesso sem gravar tudo, deixando a limpeza esvaziar ou mutilar o escopo → `FR-007` bloqueia o conjunto esperado vazio e exige a confirmação dos pontos esperados no destino antes de remover, provado por `AC-013` e `AC-014`.
- Operador usando ChromaDB e acumulando duplicatas a cada execução, por ausência de identidade estável nesse provider → limite declarado em `NFR-003`, fora de escopo desta fatia e encaminhado ao BACKLOG-0003; a sincronização seguirá funcionando em modo incremental sem risco de perda.

#### Suposições

- O modo espelho continua desejável no Qdrant; a alternativa de removê-lo seria mais segura, mas perderia a capacidade de expurgar chunks obsoletos e não foi pedida. Reversível.
- A rejeição da opção antiga permanece indefinidamente, sem prazo de remoção; a mensagem é barata de manter e protege operadores com scripts antigos. Reversível.
- O registro auditável usa o `logging` já configurado em `src/config.py`, sem introduzir formato estruturado novo nesta entrega. Reversível; um formato estruturado pode ser tratado no BACKLOG-0007.
- Não há necessidade de ferramenta administrativa de exclusão sob confirmação neste milestone; se surgir, será um item de backlog próprio.
- A guarda de `FR-007` usa dois critérios objetivos, conjunto esperado vazio e confirmação dos pontos esperados no destino, sem limiar percentual configurável. Um limiar exigiria calibração arbitrária e bloquearia substituições legítimas. A releitura de confirmação custa uma varredura adicional do escopo por execução em modo espelho, aceitável no volume atual. Reversível caso a operação real mostre necessidade.

### 17. Decisões

- **DEC-001**: Reconhecer a opção antiga apenas para emitir erro de migração, em vez de removê-la silenciosamente — a falha genérica do parser não ensina o caminho seguro e levaria o operador a procurar outra forma de recriar a base. Trade-off: mantém um resíduo do vocabulário antigo na CLI.
- **DEC-002**: Preservar o modo espelho no Qdrant com garantia explícita e testada, em vez de eliminá-lo — a remoção já é filtrada por `project_id` e posterior ao upsert, e sem ela chunks obsoletos permaneceriam indefinidamente na base. Trade-off: mantém uma operação de remoção no código, que passa a exigir teste de contrato permanente.
- **DEC-003**: Recusar o modo espelho em ChromaDB e Pinecone antes de qualquer mutação, em vez de implementá-lo agora — a paridade de escopo não está comprovada nesses providers e implementá-la aqui ampliaria o escopo desta fatia. Trade-off: esses providers ficam limitados ao modo incremental até um item de backlog próprio.
- **DEC-004**: Adotar a reexecução idempotente apoiada por manifesto e diagnóstico como procedimento único de recuperação, em vez de manter a recriação sob confirmação — qualquer caminho destrutivo documentado reintroduz o risco que esta fatia elimina. Trade-off: uma base gravemente corrompida exigirá um procedimento administrativo específico, tratado fora deste milestone.
- **DEC-005**: Remover o parâmetro de recriação da assinatura de `index_chunks`, em vez de mantê-lo aceito e ignorado — um parâmetro ignorado esconde a mudança de política e permite que um chamador acredite estar recriando a base. Trade-off: quebra intencional de assinatura interna, coberta pela regressão.
- **DEC-006**: Concentrar as guardas na classe `SyncSafetyPolicy`, em `src/safety.py`, em vez de repetir as verificações nas duas CLIs e na indexação ou de expor funções soltas — atende à orientação a objetos, à coesão e ao baixo acoplamento exigidos em `.specsfy/RULES.md` e garante uma única fonte da política. Trade-off: adiciona um módulo novo ao componente.
- **DEC-007**: Condicionar a limpeza a duas provas objetivas, conjunto esperado não vazio e pontos esperados confirmados no destino, em vez de bloquear pela proporção removida — como o `chunk_id` deriva do `source_hash` do documento inteiro (`src/identity.py`), editar cada documento de um projeto troca todos os IDs, e um bloqueio por proporção transformaria essa operação de rotina em erro. O risco real não é remover demais, é remover sem ter inserido. A confirmação também detecta o upsert que relata sucesso sem gravar tudo, que hoje nada percebe. Trade-off: uma releitura adicional do escopo por execução em modo espelho.
- **DEC-008**: Delimitar `NFR-003` ao provider com identidade estável e declarar a duplicação do ChromaDB como limite conhecido, em vez de prometer idempotência universal — o caminho Chroma escreve com `Chroma.from_documents` sem IDs próprios e corrigi-lo exige mudar a forma de escrita desse provider, o que pertence ao BACKLOG-0003. Trade-off: a fatia entrega garantia desigual entre providers, registrada de forma explícita em vez de implícita.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `uv run pytest` executado e verde; a suíte inclui os quinze casos derivados dos cenários AC.
- [x] Ruff permanece fora desta fatia: ele não está instalado no ambiente e sua adoção, junto do workflow de integração contínua, é escopo do BACKLOG-0007.
- [x] `.specsfy/DATABASE.md` revisado, porque o comportamento documentado do modo espelho no Qdrant passa a incluir a guarda de remoção total.
- [x] `PROJECT.md` revisado quanto ao limite de operações remotas destrutivas, confirmando que o texto descreve o comportamento agora implementado.
- [x] Busca estática confirma ausência de `delete_collection` e de `delete_all` no código de produção, excluindo `specs/` e `research/`.

## Effort history

- 2026-09-01T01:03:53.659Z: 5 → 6. Revisão semântica acrescentou FR-007, três cenários e a guarda de remoção total, além de encapsular a política em SyncSafetyPolicy; o alcance passou de sete para dez arquivos entre código, testes e documentação.
