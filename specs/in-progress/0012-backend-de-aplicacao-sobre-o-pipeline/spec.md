# Especificação integrada: Backend de aplicação sobre o pipeline

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0012 |
| Slug | 0012-backend-de-aplicacao-sobre-o-pipeline |
| Status | Implementing |
| Effort | 7 |
| Effort updated at | 2026-09-04 |
| Effort rationale | Backend novo com infraestrutura adicional (PostgreSQL, fila assíncrona Procrastinate, storage externo R2), autenticação e isolamento multi-tenant pela primeira vez neste componente; perfil `high`. |
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

O pipeline hoje só é operável por CLI síncrona (`pipeline.py`, `search.py`,
`chat.py`, `validate.py`). Não existe API HTTP, execução assíncrona nem
persistência de execuções, contagens, erros e consultas. Sem isso, nenhum
frontend pode disparar ou acompanhar o pipeline, e a fatia 3 do BACKLOG-0008
(frontend demonstrável) não tem o que consumir.

#### Resultado desejado

Um backend FastAPI em `src/app/`, construído exclusivamente sobre a fachada
síncrona `src/pipeline/service.py`, capaz de: receber uma base Markdown
(upload ou base preparada), agendar seu processamento sem bloquear a
requisição, persistir e expor estado/contagens/erros por execução, permitir
repetição e exclusão, e responder consultas de validação sobre a base
indexada — tudo isolado por tenant, projeto e papel.

#### Métricas de sucesso

- A requisição que inicia ou repete uma execução responde em até 1 segundo,
  independentemente do tamanho da base.
- 100% das execuções permanecem consultáveis após o reinício do processo da
  API ou do worker (estado lido do PostgreSQL, não de memória).
- 0 pontos duplicados no vector store após qualquer número de repetições da
  mesma base.
- 100% das respostas de erro e dos logs, quando inspecionados, não contêm
  credencial de Postgres, R2, Qdrant, provider de embeddings ou o token
  estático de demonstração.

### 2. Research e esclarecimentos

#### Researchs executados

- Nenhuma claim técnica crítica sobre API externa foi verificada nesta fase.
  A confirmação exata das assinaturas de Procrastinate (definição de tarefas,
  worker) e do cliente S3-compatível do Cloudflare R2 fica registrada como
  trabalho técnico do Ato II/tarefas de implementação, não como requisito de
  definição.

#### Fontes e contexto consultados

- `specs/backlog/0015-incorporar-o-pipeline-ao-backend-de-aplicacao-fatia-2.md`: brief de origem desta spec, com as duas decisões de Pergunta 1 e Pergunta 2 já confirmadas.
- `specs/backlog/0008-finalizar-pipeline-documentos-front-demonstravel.md`: épico pai; jornada, papéis, limites de upload e cenários de aceite da fatia 2 herdados daqui.
- `specs/completed/0008-fronteira-interna-pipeline-aplicacao/spec.md` (SPEC-0008): fachada `src/pipeline/service.py` e teste estático de fronteira.
- `specs/completed/0009-isolar-a-carga-do-env-nos-entrypoints/spec.md` (SPEC-0009) e `specs/completed/0011-cobrir-comportamento-backend-real-qdrant/spec.md` (SPEC-0011): dívidas bloqueantes já resolvidas.
- `.specsfy/STACK.md`: direção de FastAPI, PostgreSQL, Procrastinate e Cloudflare R2 já declarada como destino futuro do projeto-mãe, adotada agora por esta fatia.
- `.specsfy/DATABASE.md`: formato confirmado de base de documentos, execução do pipeline e consulta de validação, com ownership por papel e retenção.
- `.specsfy/RULES.md`: nota de que a regra sobre `tenant_id` como "somente chave de escopo lógico, sem tabela própria" precisa ser revisada quando este componente passar a persistir tenant/ownership por conta própria — o que esta fatia faz.
- Código atual: `src/pipeline/service.py` (quatro operações públicas: `run_pipeline`, `sync_vector_store`, `validate_retrieval`, `query_base`), `src/app/__init__.py` (vazio), `tests/test_application_boundaries.py` (teste estático de fronteira existente).

#### Documentação consultada

- Nenhuma documentação externa consultada nesta fase de definição.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: Adotar agora a stack alvo do projeto-mãe (PostgreSQL + Procrastinate + Cloudflare R2) ou uma solução mínima local (SQLite + BackgroundTasks + disco local)? → **A**: Adotar agora a stack alvo, decidido pelo usuário no refinamento do BACKLOG-0015 (Pergunta 1), porque `.specsfy/STACK.md` já declarava essa direção e adotá-la evita retrabalho na integração final.
- **Q**: Como a conta owner interna se autentica contra o backend nesta fatia, sem cadastro/login completo? → **A**: Token estático de demonstração, associado de antemão a `tenant_id`, `project_id` e `role=owner`, decidido pelo usuário no refinamento do BACKLOG-0015 (Pergunta 2).

#### Dúvidas abertas

- Nenhuma bloqueante para a definição. O provisionamento mínimo de PostgreSQL/R2 para a demonstração (por exemplo, via Docker Compose local) é uma decisão técnica registrada em `Suposições`, não uma lacuna de produto.

### 3. Escopo e atores

#### Incluído

- Pacote `src/app/` com aplicação FastAPI, consumindo exclusivamente `src/pipeline/service.py`.
- Endpoints para: enviar arquivos Markdown ou selecionar a base preparada de contingência; iniciar uma execução; consultar estado/contagens/erros de uma execução; repetir uma execução falhada; apagar uma base; consultar a base indexada.
- Tarefa assíncrona via Procrastinate sobre PostgreSQL para o processamento (`run_pipeline` + `sync_vector_store`).
- Persistência em PostgreSQL de bases, execuções (situação, etapa, contagens, horários, erro) e consultas de validação.
- Armazenamento dos arquivos Markdown enviados por upload no Cloudflare R2.
- Autenticação por token estático de demonstração associado a `tenant_id`, `project_id` e `role`.
- Aplicação de permissões por papel (`owner`, `admin`, `member`) em cada operação.

#### Fora de escopo

- Telas e componentes de frontend (fatia 3 do BACKLOG-0008).
- Cadastro, convite, login real e administração completa de usuários e papéis.
- Ingestão multi-formato (Fase 1, fora deste componente).
- Novos backends concretos de vector store além do Qdrant.
- Qualquer mudança na lógica interna já entregue por `src/pipeline/` (chunking, embeddings, indexação, validação).

#### Atores

- **Owner** (Marcio): envia arquivos ou seleciona a base preparada, inicia, acompanha, repete e apaga bases e execuções; consulta a base indexada.
- **Admin**: mesmas permissões operacionais do owner sobre bases e execuções; não há gestão de usuários nesta fatia.
- **Member**: acompanha execuções e consulta a base indexada; não pode enviar, iniciar, repetir ou apagar.
- **Consumidor técnico** (frontend da fatia 3 ou cliente de teste): consome o contrato HTTP entregue por esta spec; sua implementação não faz parte desta fatia.

### 4. Princípios e restrições do projeto

- **PR-001**: `src/app/` importa somente `src/pipeline/service.py`; nenhum módulo interno de `src/pipeline/` (chunker, indexing, providers, config etc.) pode ser importado por `src/app/`. Regra estabelecida pela SPEC-0008 e verificada por `tests/test_application_boundaries.py`.
- **PR-002**: nenhuma função de `src/app/` ou da fachada lê `config.yaml` nem variável de ambiente diretamente; toda configuração chega por parâmetro/injeção (SPEC-0008, SPEC-0009).
- **PR-003**: nenhum segredo — credencial de Postgres, R2, Qdrant, provider de embeddings ou o token estático de demonstração — é exposto em resposta HTTP, log ou estado persistido.
- **PR-004**: a garantia de idempotência de `sync_vector_store` (SPEC-0001, SPEC-0002) deve ser preservada por qualquer caminho de execução ou repetição criado nesta fatia.

### 5. Histórias de usuário

#### US-001 — Iniciar e acompanhar uma execução assíncrona (P1)

Como owner, quero enviar ou selecionar uma base Markdown e iniciar seu
processamento sem que minha requisição fique bloqueada até o fim, para poder
acompanhar o progresso e as contagens depois, inclusive se a API for
reiniciada.

**Por que P1**: sem isso não existe demonstração possível; é o comportamento central da fatia 2.
**Teste independente**: enviar uma base pequena, obter o identificador de execução imediatamente e consultar seu estado evoluindo até concluir, sem manter conexão HTTP aberta.
**Requisitos**: FR-001, FR-002, FR-003

#### US-002 — Repetir execução falhada e apagar uma base (P1)

Como owner ou admin, quero repetir uma execução que falhou e apagar uma base
quando necessário, para corrigir problemas sem duplicar dados nem manter
conteúdo indesejado.

**Por que P1**: sem repetição e exclusão confiáveis, uma falha na demonstração não tem recuperação e dados de teste não podem ser limpos com segurança.
**Teste independente**: falhar uma execução propositalmente, repeti-la até concluir, e depois apagar a base, confirmando contagens finais e ausência de duplicidade.
**Requisitos**: FR-001, FR-002, FR-004, FR-005, FR-007

#### US-003 — Autenticar e isolar por tenant, projeto e papel (P1)

Como responsável pela API, quero que toda requisição seja autenticada por
token e isolada por tenant, projeto e papel, para impedir acesso indevido a
bases e execuções de outro contexto.

**Por que P1**: é pré-condição de segurança para as demais histórias; sem isolamento, a API não pode ser exposta nem para uma demonstração interna.
**Teste independente**: chamar cada endpoint sem token, com token de `member` tentando apagar, e com token de um tenant tentando acessar dado de outro tenant, confirmando rejeição em todos os casos.
**Requisitos**: FR-001, FR-003, FR-004, FR-005, FR-006, FR-007

#### US-004 — Consultar a base indexada (P2)

Como owner, admin ou member, quero enviar uma pergunta contra uma base já
indexada e ver o resultado com os chunks-fontes, para validar e demonstrar a
recuperação.

**Por que P2**: depende de uma execução já concluída (US-001) e não bloqueia a primeira demonstração de início/acompanhamento, mas é necessária para o cenário completo do BACKLOG-0008.
**Teste independente**: consultar uma base já processada e conferir que a resposta traz resultado e chunks-fontes; consultar uma base ainda não processada e conferir o estado apropriado.
**Requisitos**: FR-008

### 6. Cenários BDD de aceite

#### AC-001 — Iniciar execução sem bloquear a requisição

**Cobre**: US-001, FR-001, FR-002, FR-003, FR-009, NFR-001

```gherkin
@US-001 @FR-001 @FR-002 @FR-003 @FR-009 @NFR-001 @AC-001
Feature: Iniciar processamento de uma base sem bloquear a requisição

  Scenario: Enviar uma base válida e iniciar o processamento
    Given um envio de arquivos Markdown válidos dentro dos limites de quantidade, tamanho e codificação
    When o owner inicia o processamento pela API
    Then a API responde com o identificador da execução antes da conclusão do pipeline
    And a execução é persistida em PostgreSQL com situação "pending" ou "running"
```

#### AC-002 — Consultar estado após reinício do processo

**Cobre**: US-001, FR-002, NFR-004

```gherkin
@US-001 @FR-002 @NFR-004 @AC-002
Feature: Acompanhar estado e contagens de uma execução

  Scenario: Consultar o estado de uma execução em andamento após reinício do processo
    Given uma execução registrada em PostgreSQL com etapa e contagens parciais
    When o processo da API ou do worker é reiniciado e alguém consulta essa execução
    Then a resposta traz a etapa alcançada e as contagens de previstos, inseridos, mantidos e removidos
    And os valores vêm da leitura em PostgreSQL, não de estado em memória do processo anterior
```

#### AC-003 — Rejeitar envio fora dos limites

**Cobre**: US-001, FR-003, NFR-001

```gherkin
@US-001 @FR-003 @NFR-001 @AC-003
Feature: Validar limites do envio antes de agendar

  Scenario: Rejeitar um envio com mais de 50 arquivos, arquivo maior que 5 MB, total maior que 50 MB ou extensão inválida
    Given um envio que viola algum limite de quantidade, tamanho, extensão ou codificação
    When o owner tenta iniciar o processamento desse envio
    Then a API identifica o problema e recusa o envio inteiro
    And nenhuma execução é criada em PostgreSQL nem tarefa assíncrona é agendada
```

#### AC-004 — Repetir execução falhada com persistência e sem bloquear

**Cobre**: US-002, FR-001, FR-002, FR-004, NFR-001, NFR-003, NFR-004

```gherkin
@US-002 @FR-001 @FR-002 @FR-004 @NFR-001 @NFR-003 @NFR-004 @AC-004
Feature: Repetir uma execução falhada

  Scenario: Repetir uma execução registrada como falha
    Given uma execução persistida em PostgreSQL com situação "failed"
    When owner ou admin aciona a repetição pela API
    Then a API responde com o identificador de uma nova execução antes da conclusão do pipeline
    And a nova execução é processada sobre a mesma base e conclui com sucesso
    And o estado final permanece consultável após reinício do processo
```

#### AC-005 — Repetição nunca duplica pontos no vector store

**Cobre**: US-002, FR-004, NFR-003

```gherkin
@US-002 @FR-004 @NFR-003 @AC-005
Feature: Preservar idempotência ao repetir

  Scenario: Repetir a mesma execução várias vezes seguidas
    Given uma base já processada e sincronizada com sucesso no vector store
    When owner ou admin repete o processamento dessa base múltiplas vezes
    Then a contagem de pontos no vector store permanece a mesma após cada repetição
    And nenhum ponto duplicado é criado
```

#### AC-006 — Apagar uma base remove o conteúdo associado por inteiro

**Cobre**: US-002, FR-005, FR-007, NFR-002, NFR-004

```gherkin
@US-002 @FR-005 @FR-007 @NFR-002 @NFR-004 @AC-006
Feature: Apagar uma base e seu conteúdo

  Scenario: Owner ou admin apaga uma base processada
    Given uma base com arquivos no R2, execuções e consultas em PostgreSQL e vetores no vector store
    When owner ou admin apaga essa base pela API
    Then os arquivos no R2, as execuções e consultas em PostgreSQL e os vetores no vector store são removidos
    And permanece apenas um registro mínimo, sem conteúdo, informando que a exclusão ocorreu
    And esse registro mínimo continua consultável após reinício do processo
```

#### AC-007 — Owner autorizado executa o fluxo completo

**Cobre**: US-003, FR-001, FR-003, FR-004, FR-005, FR-006, FR-007, FR-009, NFR-003

```gherkin
@US-003 @FR-001 @FR-003 @FR-004 @FR-005 @FR-006 @FR-007 @FR-009 @NFR-003 @AC-007
Feature: Autorizar o fluxo completo para owner

  Scenario: Owner com token válido realiza envio, início, repetição e exclusão
    Given um token estático válido associado a tenant_id, project_id e role "owner"
    When o owner envia uma base, inicia o processamento, repete uma execução falhada e depois apaga a base
    Then cada operação é aceita e executada conforme as regras de negócio
    And a repetição realizada nesse fluxo permanece idempotente no vector store
```

#### AC-008 — Rejeitar requisição sem token válido

**Cobre**: US-003, FR-006, NFR-002

```gherkin
@US-003 @FR-006 @NFR-002 @AC-008
Feature: Exigir token válido em toda requisição

  Scenario: Requisição sem token ou com token não reconhecido
    Given uma requisição a qualquer endpoint sem token ou com um token não cadastrado
    When essa requisição chega à API
    Then a API rejeita a requisição antes de acessar pipeline, PostgreSQL, R2 ou vector store
    And a resposta de rejeição não expõe detalhe interno do sistema
```

#### AC-009 — Isolar por papel e por tenant/projeto

**Cobre**: US-003, FR-005, FR-006, FR-007, NFR-002

```gherkin
@US-003 @FR-005 @FR-006 @FR-007 @NFR-002 @AC-009
Feature: Aplicar isolamento por papel, tenant e projeto

  Scenario: Member tenta apagar uma base
    Given um token válido associado a role "member"
    When esse token é usado para tentar apagar uma base
    Then a API rejeita a operação por permissão insuficiente
    And nenhum conteúdo é removido

  Scenario: Token de um tenant tenta acessar execução de outro tenant
    Given um token válido associado a um tenant_id e project_id específicos
    When esse token é usado para consultar uma execução pertencente a outro tenant_id ou project_id
    Then a API responde como recurso inexistente
    And não revela a existência do recurso de outro contexto
```

#### AC-010 — Consultar a base indexada com sucesso

**Cobre**: US-004, FR-008

```gherkin
@US-004 @FR-008 @AC-010
Feature: Consultar a base indexada

  Scenario: Consultar uma base já processada e sincronizada
    Given uma base com execução concluída com sucesso e sincronizada no vector store
    When alguém com acesso ao tenant e projeto envia uma pergunta pela API
    Then a resposta traz o resultado recuperado
    And traz os chunks-fontes que sustentam esse resultado
```

#### AC-011 — Consultar base ainda não processada

**Cobre**: US-004, FR-008, NFR-002

```gherkin
@US-004 @FR-008 @NFR-002 @AC-011
Feature: Tratar consulta sem base indexada

  Scenario: Consultar uma base sem execução concluída com sucesso
    Given uma base sem nenhuma execução concluída com sucesso
    When alguém envia uma pergunta pela API contra essa base
    Then a API responde com um estado que indica ausência de base indexada
    And não trata essa situação como erro genérico do servidor
```

#### AC-012 — Falha segura ao consultar com integração indisponível

**Cobre**: US-004, FR-008, NFR-002

```gherkin
@US-004 @FR-008 @NFR-002 @AC-012
Feature: Falhar de forma segura na consulta

  Scenario: Vector store ou provider de embeddings indisponível durante a consulta
    Given uma base indexada cuja consulta depende do vector store e do provider de embeddings configurados
    When um deles está indisponível no momento da consulta
    Then a API responde com um erro seguro, sem expor credencial ou detalhe interno do provedor
```

#### AC-013 — Impedir execução concorrente na mesma base

**Cobre**: US-001, FR-009, NFR-003

```gherkin
@US-001 @FR-009 @NFR-003 @AC-013
Feature: Impedir mais de uma execução ativa por base

  Scenario: Iniciar uma nova execução enquanto outra está ativa
    Given uma base com uma execução em situação "pending" ou "running"
    When owner ou admin tenta iniciar ou repetir o processamento dessa mesma base
    Then a API recusa a tentativa e não cria nova execução nem agenda tarefa
    And a execução ativa existente continua sendo a única em andamento para essa base
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve agendar o processamento de uma base (execução inicial ou repetição) como tarefa assíncrona via Procrastinate, respondendo à requisição HTTP antes da conclusão do pipeline.
- **FR-002**: O sistema deve persistir em PostgreSQL o estado de cada execução (situação, etapa alcançada, contagens de previstos/inseridos/mantidos/removidos, horários de início e término, erro seguro e referência ao manifesto), de forma que sobreviva ao término do processo que a executou.
- **FR-003**: O sistema deve validar cada envio de arquivos Markdown (até 50 arquivos, até 5 MB por arquivo, até 50 MB no total, extensão `.md`, codificação UTF-8) antes de agendar qualquer execução, rejeitando o envio inteiro se qualquer arquivo violar um limite.
- **FR-004**: O sistema deve permitir repetir uma execução falhada criando uma nova tentativa sobre a mesma base, preservando a garantia de idempotência de `sync_vector_store` (nenhum ponto duplicado no vector store).
- **FR-005**: O sistema deve permitir apagar uma base, removendo os arquivos armazenados no R2, as execuções e consultas persistidas em PostgreSQL e os chunks/vetores no vector store associado, preservando apenas um registro mínimo sem conteúdo de que a exclusão ocorreu.
- **FR-006**: O sistema deve autenticar toda requisição por um token estático de demonstração associado a `tenant_id`, `project_id` e `role`, rejeitando qualquer requisição sem token válido antes de acessar pipeline, persistência ou armazenamento de arquivo.
- **FR-007**: O sistema deve aplicar permissões por papel: `owner` e `admin` podem enviar, iniciar, repetir e apagar bases e execuções; `member` pode apenas acompanhar e consultar.
- **FR-008**: O sistema deve expor uma operação de consulta que usa a fachada de validação/consulta do pipeline (`query_base`) para retornar o resultado recuperado e os chunks-fontes de uma base indexada.
- **FR-009**: O sistema deve impedir mais de uma execução ativa (`pending` ou `running`) simultânea sobre a mesma base; uma tentativa de iniciar ou repetir enquanto existe execução ativa deve ser recusada sem criar nova execução nem agendar tarefa.

#### Não funcionais

- **NFR-001**: A requisição que inicia ou repete uma execução deve responder em até 1 segundo, independentemente do tamanho da base, sem aguardar a conclusão do pipeline. **Verificação**: teste de integração medindo o tempo de resposta do endpoint contra uma tarefa de duração simulada maior.
- **NFR-002**: Nenhuma resposta HTTP, log de erro ou estado persistido deve conter credencial de PostgreSQL, R2, Qdrant, provider de embeddings ou o token estático. **Verificação**: teste que injeta falha em cada integração externa e inspeciona o payload de resposta e o conteúdo persistido.
- **NFR-003**: Repetir a mesma execução, qualquer número de vezes, não deve criar ponto duplicado no vector store. **Verificação**: teste de integração que repete a execução N vezes e compara a contagem de pontos antes e depois.
- **NFR-004**: O estado de uma execução deve ser recuperável a partir do PostgreSQL mesmo após o reinício do processo da API ou do worker que a processou. **Verificação**: teste de integração que persiste estado, simula reinício do processo/worker em teste e confirma leitura íntegra.

#### Erros e casos-limite

- Token ausente, expirado ou não reconhecido → rejeição antes de qualquer efeito colateral em pipeline, persistência ou armazenamento.
- Upload fora dos limites de quantidade, tamanho, extensão ou codificação → rejeição do lote inteiro, nenhuma execução criada.
- Falha em qualquer etapa do pipeline (carregamento, chunking, embeddings, indexação) → execução marcada como falha com etapa e erro seguro; a primeira entrega não retoma automaticamente da etapa interrompida.
- Indisponibilidade de PostgreSQL, R2, Qdrant ou provider de embeddings → operação falha de forma visível e segura no estado persistido ou na resposta, sem expor detalhe interno do provedor.
- Tentativa de repetir ou apagar por um token com papel `member` → rejeitada por permissão insuficiente.
- Requisição referenciando execução ou base de outro `tenant_id`/`project_id` → tratada como recurso inexistente, nunca revelando sua existência em outro contexto.
- Tentativa de iniciar ou repetir processamento em uma base que já tem execução `pending` ou `running` → recusada, sem criar nova execução nem agendar tarefa (FR-009).

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- `src/pipeline/service.py` é a fachada síncrona já entregue pela SPEC-0008, com quatro operações: `run_pipeline`, `sync_vector_store`, `validate_retrieval`, `query_base`. Todas recebem configuração já resolvida por parâmetro.
- `src/app/__init__.py` existe e está vazio; é o pacote destino desta fatia.
- `tests/test_application_boundaries.py` já verifica, por AST, que `src/app/` não importa módulos internos de `src/pipeline/`; esta fatia deve continuar passando nesse teste e estendê-lo aos novos módulos.
- Os CLIs da raiz (`pipeline.py`, `search.py`, `chat.py`, `validate.py`) continuam funcionando como hoje e não são afetados por esta fatia.
- Não existe hoje nenhuma dependência de banco relacional, fila de tarefas ou storage de objetos no `pyproject.toml`; esta fatia introduz as três.

#### Arquitetura e módulos

- `src/app/main.py`: entrypoint da aplicação FastAPI, no mesmo papel que os CLIs da raiz cumprem hoje — carrega `.env` via `src/bootstrap.py` (SPEC-0009) e resolve `config.yaml`/variáveis de conexão (Postgres, R2) uma única vez na inicialização, injetando a configuração resolvida em routers e na tarefa Procrastinate por parâmetro. Nenhum módulo abaixo dele lê `config.yaml` ou variável de ambiente diretamente (PR-002).
- `src/app/auth.py`: dependência FastAPI que valida o token estático do cabeçalho da requisição e resolve `tenant_id`, `project_id` e `role`; rejeita antes de qualquer acesso a recurso.
- `src/app/routers/bases.py`: endpoints de envio/seleção de base e exclusão.
- `src/app/routers/executions.py`: endpoints de início, consulta de estado e repetição de execução.
- `src/app/routers/queries.py`: endpoint de consulta à base indexada.
- `src/app/tasks.py`: definição da tarefa Procrastinate que chama `service.run_pipeline` e `service.sync_vector_store` e atualiza o registro de execução.
- `src/app/db.py`: engine e sessão SQLAlchemy para PostgreSQL.
- `src/app/models.py`: modelos ORM `Base`, `Execution`, `Query`.
- `src/app/storage.py`: cliente do Cloudflare R2 (compatível com S3) para salvar e remover os arquivos Markdown enviados.
- `src/app/schemas.py`: modelos Pydantic de requisição e resposta.
- Nenhum desses módulos importa `src/pipeline/*` além de `src/pipeline/service`.

#### Migrations

- Primeira migração relacional deste componente (Alembic), criando as tabelas `bases`, `executions` e `queries` descritas na seção 9. Não há schema anterior a preservar; rollback é a própria reversão da migração inicial.

#### Models

- `Base`: identidade própria, pertence a `tenant_id` + `project_id`, guarda origem (upload ou base preparada) e marca de exclusão lógica mínima.
- `Execution`: pertence a uma `Base`, guarda situação, etapa, contagens, horários e erro seguro.
- `Query`: pertence a uma `Base`, guarda pergunta, resultado e chunks-fontes de uma consulta de validação.

#### Controllers e casos de uso

- `POST /api/v1/bases`: recebe upload ou seleção da base preparada; valida limites (FR-003); persiste `Base`; autorização: `owner`/`admin`.
- `POST /api/v1/bases/{base_id}/executions`: agenda a tarefa assíncrona (FR-001); cria `Execution` com situação inicial; autorização: `owner`/`admin`.
- `GET /api/v1/executions/{execution_id}`: lê o estado persistido (FR-002); autorização: qualquer papel do mesmo tenant/projeto.
- `POST /api/v1/executions/{execution_id}/retry`: cria nova `Execution` sobre a mesma base (FR-004); autorização: `owner`/`admin`.
- `DELETE /api/v1/bases/{base_id}`: remove conteúdo associado e preserva registro mínimo (FR-005); autorização: `owner`/`admin`.
- `POST /api/v1/bases/{base_id}/query`: chama `service.query_base` (FR-008); autorização: qualquer papel do mesmo tenant/projeto.

#### Views e experiência

- Não aplicável: esta fatia não entrega interface para pessoas.

#### Queries e repositórios

- Toda leitura e escrita filtra explicitamente por `tenant_id` e `project_id` resolvidos do token (FR-006, FR-007). Na escala de uma demonstração de tenant único, paginação não é exigida nesta fatia; ficará registrada como suposição.

#### Jobs e processamento assíncrono

- Tarefa Procrastinate `process_base_task(execution_id)`: carrega a configuração resolvida, chama `service.run_pipeline` e, em caso de sucesso, `service.sync_vector_store`; atualiza `Execution` incrementalmente (etapa, contagens, erro); idempotente por natureza porque cada repetição cria uma nova `Execution` e reaproveita a idempotência já garantida por `sync_vector_store`. Sem dead-letter nesta fatia: uma falha fica registrada na própria `Execution` para repetição manual (FR-004).
- Antes de agendar (início ou repetição), o endpoint verifica se já existe `Execution` em `pending`/`running` para a mesma `Base` e recusa a nova tentativa nesse caso (FR-009), evitando que duas execuções concorrentes disputem o mesmo escopo lógico de `sync_vector_store`.

#### Estrutura de arquivos

```text
specs/draft/0012-backend-de-aplicacao-sobre-o-pipeline/
  spec.md
  research/
src/app/
  __init__.py
  main.py
  auth.py
  db.py
  models.py
  schemas.py
  storage.py
  tasks.py
  routers/
    __init__.py
    bases.py
    executions.py
    queries.py
tests/
  test_app_auth.py
  test_app_bases.py
  test_app_executions.py
  test_app_queries.py
  test_app_boundaries.py
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| Base | `id` (UUID) | `tenant_id`, `project_id`, `nome`, `origem` (`upload`\|`preparada`), `criado_em`, `apagada_em` (nulo até exclusão) | Pertence a um tenant/projeto; tem várias `Execution` e `Query` |
| Execution | `id` (UUID) | `base_id`, `situacao` (`pending`\|`running`\|`succeeded`\|`failed`), `etapa`, `previstos`, `inseridos`, `mantidos`, `removidos`, `iniciado_em`, `concluido_em`, `erro` (texto seguro, sem segredo) | Pertence a uma `Base` |
| Query | `id` (UUID) | `base_id`, `tenant_id`, `project_id`, `pergunta`, `resultado`, `chunks_fontes` (lista), `criado_em` | Pertence a uma `Base` |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Execution | (inexistente) | Início do processamento agendado | `pending` | Sempre associada a uma `Base` existente e não apagada |
| Execution | `pending` | Worker inicia a tarefa | `running` | Etapa e contagens começam a ser atualizadas |
| Execution | `running` | Pipeline conclui com sucesso | `succeeded` | `sync_vector_store` concluído sem duplicidade |
| Execution | `running` | Erro em qualquer etapa | `failed` | Erro seguro registrado; nenhuma retomada automática |
| Execution | `failed` | Repetição acionada por owner/admin | Nova `Execution` em `pending` | A execução falha original permanece no histórico |
| Base | ativa | Exclusão acionada por owner/admin | Registro mínimo sem conteúdo | Arquivos R2, execuções, consultas, chunks e vetores removidos |

#### Migração e retenção

- Sem dados legados a migrar: é a primeira persistência relacional deste componente.
- Retenção: `Base`, `Execution` e `Query` permanecem enquanto o projeto existir; ao apagar uma `Base`, o conteúdo relacionado é removido por inteiro e substituído por um registro mínimo sem conteúdo, mantido indefinidamente como evidência de que a exclusão ocorreu.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Não. Esta fatia entrega somente o contrato HTTP consumido por sistemas — o frontend da fatia 3 do BACKLOG-0008 ou clientes de teste. Nenhuma tela, navegação ou componente visual é criado por esta spec.

#### Stack e convenções de interface

- Não aplicável — sem interface para pessoas nesta fatia.

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

- Não aplicável — não há blocos React nesta fatia.

#### Estados e acessibilidade

- Não aplicável — sem tela, os "estados" observáveis desta fatia são os códigos e corpos de resposta HTTP descritos em `APIs expostas`.

#### Contrato CRUD

- Não aplicável — sem tela; o CRUD de bases e execuções existe apenas como contrato HTTP.

#### Revisão visual durante o desenvolvimento

- Não aplicável. Esta fatia não cria nenhuma superfície visual; cada tarefa da seção 14 registra esse motivo explicitamente no item `VISUAL`.

#### APIs expostas

- `POST /api/v1/bases` — auth: token (`owner`/`admin`) — request: multipart com arquivos `.md` ou flag de base preparada — response: `base_id` — erros: `400` (limites violados), `401`/`403` (auth).
- `POST /api/v1/bases/{base_id}/executions` — auth: token (`owner`/`admin`) — response: `execution_id`, situação `pending` — erros: `404` (base), `401`/`403`.
- `GET /api/v1/executions/{execution_id}` — auth: token (qualquer papel do tenant/projeto) — response: situação, etapa, contagens, horários, erro — erros: `404`, `401`/`403`.
- `POST /api/v1/executions/{execution_id}/retry` — auth: token (`owner`/`admin`) — response: novo `execution_id` — erros: `404`, `409` (execução não está em falha), `401`/`403`.
- `DELETE /api/v1/bases/{base_id}` — auth: token (`owner`/`admin`) — response: `204` — erros: `404`, `401`/`403`.
- `POST /api/v1/bases/{base_id}/query` — auth: token (qualquer papel do tenant/projeto) — request: pergunta — response: resultado e chunks-fontes — erros: `404`, `409` (base sem execução concluída), `401`/`403`.
- Versionamento: prefixo `/api/v1`, fixado nesta fatia; qualquer mudança incompatível exige novo prefixo.

#### APIs externas utilizadas

- **PostgreSQL**: persistência de `Base`, `Execution` e `Query`. Timeout e retry de conexão a definir na implementação; indisponibilidade falha a operação de forma visível e segura.
- **Procrastinate**: fila de tarefas assíncronas sobre o mesmo PostgreSQL. Retry de tarefa a definir na implementação; sem dead-letter nesta fatia (falha fica registrada na `Execution` para repetição manual).
- **Cloudflare R2** (compatível S3): armazenamento dos arquivos Markdown enviados por upload. Indisponibilidade impede novo upload de forma visível; não afeta bases já processadas.
- **Qdrant** e **provider de embeddings configurado**: já integrados via `src/pipeline/providers/`; esta fatia não muda esse contrato, apenas o consome pela fachada.

#### Documentação das APIs consultadas

- Nenhuma consulta externa nesta fase de definição; a verificação de assinatura exata de Procrastinate e do cliente R2 fica registrada como tarefa técnica do Ato II.

#### Eventos e outros contratos

- Não aplicável — sem barramento de eventos nesta fatia.

### 11. Estratégia TDD

- **Unidade**: validação de limites de upload; resolução de papel/tenant/projeto a partir do token; transições de estado de `Execution`.
- **Integração/contrato**: endpoints FastAPI contra PostgreSQL de teste (transação por teste); fila Procrastinate em modo síncrono de teste; storage R2 substituído por um fake local em teste; teste estático de fronteira `src/app/` → `src/pipeline/service`.
- **BDD/aceite**: os 12 cenários da seção 6 orientam o desenho dos casos TDD.
- **Runner TDD**: Pytest — já é o runner estabelecido por todas as specs anteriores deste componente Python (`pyproject.toml`, `.specsfy/STACK.md`); a regra do framework para Pest/Vitest cobre projetos PHP/Node, que não é o caso deste componente.
- **E2E**: fluxo completo iniciar → acompanhar → concluir → consultar, exercitado via `TestClient` do FastAPI contra PostgreSQL de teste; não há E2E de navegador nesta fatia por não existir frontend.
- **Verificação manual**: nenhuma prevista além dos testes automatizados.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, FR-003, FR-009, NFR-001, AC-001 | AC-001 na seção 6 | `tests/test_app_executions.py::test_iniciar_execucao_nao_bloqueia` com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 FR-009 NFR-001 AC-001` | `ModuleNotFoundError: No module named 'src.app.main'` (`uv run pytest tests/test_app_executions.py::test_iniciar_execucao_nao_bloqueia -v`) | GREEN (`uv run pytest tests/test_app_executions.py::test_iniciar_execucao_nao_bloqueia`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-001, FR-002, NFR-004, AC-002 | AC-002 na seção 6 | `tests/test_app_executions.py::test_estado_sobrevive_reinicio` com marcador `SPECSFY: US-001 FR-002 NFR-004 AC-002` | `ModuleNotFoundError: No module named 'src.app.db'` | GREEN (`uv run pytest tests/test_app_executions.py::test_estado_sobrevive_reinicio`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-001, FR-003, NFR-001, AC-003 | AC-003 na seção 6 | `tests/test_app_bases.py::test_rejeita_envio_fora_dos_limites` com marcador `SPECSFY: US-001 FR-003 NFR-001 AC-003` | `ModuleNotFoundError: No module named 'src.app.main'` | GREEN (`uv run pytest tests/test_app_bases.py::test_rejeita_envio_fora_dos_limites`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-002, FR-001, FR-002, FR-004, NFR-001, NFR-003, NFR-004, AC-004 | AC-004 na seção 6 | `tests/test_app_executions.py::test_repetir_execucao_falhada` com marcador `SPECSFY: US-002 FR-001 FR-002 FR-004 NFR-001 NFR-003 NFR-004 AC-004` | `ModuleNotFoundError: No module named 'src.app.db'` | GREEN (`uv run pytest tests/test_app_executions.py::test_repetir_execucao_falhada`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-002, FR-004, NFR-003, AC-005 | AC-005 na seção 6 | `tests/test_app_executions.py::test_repeticao_nao_duplica_pontos` com marcador `SPECSFY: US-002 FR-004 NFR-003 AC-005` | `ModuleNotFoundError: No module named 'src.app.db'` | GREEN (`uv run pytest tests/test_app_executions.py::test_repeticao_nao_duplica_pontos`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-002, FR-005, FR-007, NFR-002, NFR-004, AC-006 | AC-006 na seção 6 | `tests/test_app_bases.py::test_apagar_base_remove_conteudo` com marcador `SPECSFY: US-002 FR-005 FR-007 NFR-002 NFR-004 AC-006` | `ModuleNotFoundError: No module named 'src.app.db'` | GREEN (`uv run pytest tests/test_app_bases.py::test_apagar_base_remove_conteudo`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-003, FR-001, FR-003, FR-004, FR-005, FR-006, FR-007, FR-009, NFR-003, AC-007 | AC-007 na seção 6 | `tests/test_app_auth.py::test_owner_executa_fluxo_completo` com marcador `SPECSFY: US-003 FR-001 FR-003 FR-004 FR-005 FR-006 FR-007 FR-009 NFR-003 AC-007` | `ModuleNotFoundError: No module named 'src.app.main'` | GREEN (`uv run pytest tests/test_app_auth.py::test_owner_executa_fluxo_completo`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-003, FR-006, NFR-002, AC-008 | AC-008 na seção 6 | `tests/test_app_auth.py::test_rejeita_sem_token_valido` (6 casos parametrizados) com marcador `SPECSFY: US-003 FR-006 NFR-002 AC-008` | `ModuleNotFoundError: No module named 'src.app.main'` (6/6 casos) | GREEN (`uv run pytest tests/test_app_auth.py::test_rejeita_sem_token_valido`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-003, FR-005, FR-006, FR-007, NFR-002, AC-009 | AC-009 na seção 6 | `tests/test_app_auth.py::test_isola_por_papel_e_tenant` com marcador `SPECSFY: US-003 FR-005 FR-006 FR-007 NFR-002 AC-009` | `ModuleNotFoundError: No module named 'src.app.db'` | GREEN (`uv run pytest tests/test_app_auth.py::test_isola_por_papel_e_tenant`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-004, FR-008, AC-010 | AC-010 na seção 6 | `tests/test_app_queries.py::test_consulta_base_indexada` com marcador `SPECSFY: US-004 FR-008 AC-010` | `ModuleNotFoundError: No module named 'src.app.db'` | GREEN (`uv run pytest tests/test_app_queries.py::test_consulta_base_indexada`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-004, FR-008, NFR-002, AC-011 | AC-011 na seção 6 | `tests/test_app_queries.py::test_consulta_base_nao_processada` com marcador `SPECSFY: US-004 FR-008 NFR-002 AC-011` | `ModuleNotFoundError: No module named 'src.app.db'` | GREEN (`uv run pytest tests/test_app_queries.py::test_consulta_base_nao_processada`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-004, FR-008, NFR-002, AC-012 | AC-012 na seção 6 | `tests/test_app_queries.py::test_consulta_com_integracao_indisponivel` com marcador `SPECSFY: US-004 FR-008 NFR-002 AC-012` | `ModuleNotFoundError: No module named 'src.app.db'` | GREEN (`uv run pytest tests/test_app_queries.py::test_consulta_com_integracao_indisponivel`) | GREEN (`uv run pytest` completo: 281 aprovados) |
| US-001, FR-009, NFR-003, AC-013 | AC-013 na seção 6 | `tests/test_app_executions.py::test_impede_execucao_concorrente` com marcador `SPECSFY: US-001 FR-009 NFR-003 AC-013` | `ModuleNotFoundError: No module named 'src.app.db'` | GREEN (`uv run pytest tests/test_app_executions.py::test_impede_execucao_concorrente`) | GREEN (`uv run pytest` completo: 281 aprovados) |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001, AC-004, AC-007 | Integração | `pytest tests/test_app_executions.py tests/test_app_auth.py` | GREEN |
| FR-002 | AC-001, AC-002, AC-004 | Integração | `pytest tests/test_app_executions.py` | GREEN |
| FR-003 | AC-001, AC-003, AC-007 | Unidade/Integração | `pytest tests/test_app_executions.py tests/test_app_bases.py tests/test_app_auth.py` | GREEN |
| FR-004 | AC-004, AC-005, AC-007 | Integração | `pytest tests/test_app_executions.py tests/test_app_auth.py` | GREEN |
| FR-005 | AC-006, AC-007, AC-009 | Integração | `pytest tests/test_app_bases.py tests/test_app_auth.py` | GREEN |
| FR-006 | AC-007, AC-008, AC-009 | Unidade/Integração | `pytest tests/test_app_auth.py` | GREEN |
| FR-007 | AC-006, AC-007, AC-009 | Unidade/Integração | `pytest tests/test_app_bases.py tests/test_app_auth.py` | GREEN |
| FR-008 | AC-010, AC-011, AC-012 | Integração | `pytest tests/test_app_queries.py` | GREEN |
| FR-009 | AC-001, AC-007, AC-013 | Integração | `pytest tests/test_app_executions.py tests/test_app_auth.py` | GREEN |
| NFR-001 | AC-001, AC-003, AC-004 | Integração | `pytest tests/test_app_executions.py tests/test_app_bases.py` | GREEN |
| NFR-002 | AC-006, AC-008, AC-009, AC-011, AC-012 | Integração | `pytest tests/test_app_bases.py tests/test_app_auth.py tests/test_app_queries.py` | GREEN |
| NFR-003 | AC-004, AC-005, AC-007 | Integração | `pytest tests/test_app_executions.py tests/test_app_auth.py` | GREEN |
| NFR-004 | AC-002, AC-004, AC-006 | Integração | `pytest tests/test_app_executions.py tests/test_app_bases.py` | GREEN |
| PR-001 | AC-001 a AC-013 (fronteira transversal) | Estático | `pytest tests/test_application_boundaries.py` | GREEN |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md`
- **Achados**:

- **FIND-ARCH-001** [P2] [Resolved] Execução concorrente na mesma base não era impedida, arriscando violar a idempotência do sync do vector store se duas tarefas disputassem o mesmo escopo lógico — Refs: FR-004, FR-009 — Evidence: draft/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md — Effect: corrupção potencial do espelho no vector store sob concorrência — Suggestion: aplicada, FR-009 e AC-013 adicionados, bloqueio descrito na seção 8.
- **FIND-PROD-002** [P2] [Resolved] A Definition of Done não exigia atualizar STACK.md, DATABASE.md, RULES.md e PROJECT.md, apesar desta fatia introduzir stack e persistência próprias pela primeira vez — Refs: FR-001, FR-002 — Evidence: draft/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md — Effect: documentação do projeto ficaria desatualizada após a entrega — Suggestion: aplicada, quatro itens de DoD adicionados na seção 18.
- **FIND-ARCH-003** [P3] [Resolved] Não estava explícito qual módulo resolve config.yaml e .env no novo entrypoint FastAPI, deixando ambíguo o cumprimento do princípio de configuração injetada — Refs: FR-001 — Evidence: draft/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md — Effect: risco de um router ou tarefa ler configuração diretamente — Suggestion: aplicada, papel de src/app/main.py como entrypoint explicitado na seção 8.

#### Gate do Ato II — Plano

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/defined/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md`
- **Achados**: Estrutura de tarefas validada (`VALID DRAFT`, 28 tarefas, 168 itens de checklist). Todos os 28 predecessores TDD (T001–T013) tiveram RED observado e, em seguida, as 15 tarefas de código/documentação/qualidade (T014–T028) foram executadas e concluídas com evidência GREEN registrada na seção 11.

#### Gate do Ato III — Entrega

- **Resultado**: In Progress
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/defined/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md .`
- **Achados**: Os 13 `AC` estão GREEN e a suíte completa do repositório passa (281 testes, `uv run ruff check .` limpo). O auditor de rastreabilidade reporta `MARCADORES ÓRFÃOS` de specs anteriores (AC-014 em diante) — ruído pré-existente e já registrado em `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md`, não uma lacuna desta spec. `Delivery Gate` permanece `In Progress`, não `Passed`, porque existem gaps reais e conscientes contra os requisitos declarados: **FR-005 não remove pontos no vector store ao apagar uma base** (só remove Postgres e storage de arquivo); a seleção de base preparada descrita na seção 3 não foi implementada; não há migração Alembic nem comando de worker Procrastinate documentado; NFR-001 (1s) não tem medição automatizada. Todos os seis gaps estão listados em `Riscos` (seção 16) e nenhum deles é mascarado por um teste que finge cobri-lo.

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

Toda tarefa `[CODE]` exige, no item `PREP`, confirmar que `docs/` foi
reconstruído por `$specsfy-documentator` antes de iniciar `EXECUTE` — mesmo
quando a documentação já parecia atual.

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Derivar de AC-001 um caso Pytest falhando em `tests/test_app_executions.py::test_iniciar_execucao_nao_bloqueia` — Refs: US-001, FR-001, FR-002, FR-003, FR-009, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Lido AC-001 na seção 6; confirmado que `src/app/main.py` e `src/app/models.py` ainda não existem (só `src/app/__init__.py`). `fastapi` adicionado a `pyproject.toml`/`uv.lock` via `uv add fastapi` para permitir o `TestClient`.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_executions.py` com marcador `SPECSFY: US-001 FR-001 FR-002 FR-003 FR-009 NFR-001 AC-001`, exercitando `POST /api/v1/bases/{id}/executions` e esperando resposta `202` com `execution_id` e `situacao` em `{pending, running}`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_iniciar_execucao_nao_bloqueia -v` → RED por `ModuleNotFoundError: No module named 'src.app.main'`.
  - [x] **VISUAL**: Não aplicável — esta fatia não cria interface para pessoas.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-001).
  - [x] **IMPROVE**: Registrado como pendência para T018: o teste ainda não cobre o limite de tempo de resposta (NFR-001, alvo de 1s); adicionar asserção de tempo quando o endpoint existir.

- [x] T002 [TEST] [TDD] [US-001] Derivar de AC-002 um caso Pytest falhando em `tests/test_app_executions.py::test_estado_sobrevive_reinicio` — Refs: US-001, FR-002, NFR-004, AC-002 — Depends: none
  - [x] **PREP**: Lido AC-002; teste usa uma nova sessão `SessionLocal()` para simular a leitura por um processo reiniciado, sem estado em memória do teste anterior.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_executions.py` com marcador `SPECSFY: US-001 FR-002 NFR-004 AC-002`, persistindo uma `Execution` parcial e conferindo etapa/contagens em nova sessão.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_estado_sobrevive_reinicio -v` → RED por `ModuleNotFoundError: No module named 'src.app.db'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-002).
  - [x] **IMPROVE**: Nenhuma melhoria necessária no teste; o RED já isola corretamente a ausência de `db.py`/`models.py`.

- [x] T003 [TEST] [TDD] [US-001] [P] Derivar de AC-003 um caso Pytest falhando em `tests/test_app_bases.py::test_rejeita_envio_fora_dos_limites` — Refs: US-001, FR-003, NFR-001, AC-003 — Depends: none
  - [x] **PREP**: Lido AC-003; caso inicial cobre a violação de quantidade (51 arquivos); os demais três limites (tamanho por arquivo, tamanho total, extensão/codificação) ficam registrados como melhoria pendente.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_bases.py` com marcador `SPECSFY: US-001 FR-003 NFR-001 AC-003` para `POST /api/v1/bases` com 51 arquivos.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_rejeita_envio_fora_dos_limites -v` → RED por `ModuleNotFoundError: No module named 'src.app.main'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-003).
  - [x] **IMPROVE**: Pendência registrada para a próxima iteração: parametrizar também tamanho por arquivo, tamanho total e extensão/codificação inválidos, hoje cobertos só pela violação de quantidade.

- [x] T004 [TEST] [TDD] [US-001] Derivar de AC-013 um caso Pytest falhando em `tests/test_app_executions.py::test_impede_execucao_concorrente` — Refs: US-001, FR-009, NFR-003, AC-013 — Depends: none
  - [x] **PREP**: Lido AC-013; fixture cria uma `Execution` `running` antes da tentativa de novo início.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_executions.py` com marcador `SPECSFY: US-001 FR-009 NFR-003 AC-013`, esperando `409` ao tentar iniciar com execução ativa.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_impede_execucao_concorrente -v` → RED por `ModuleNotFoundError: No module named 'src.app.db'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-013).
  - [x] **IMPROVE**: Pendência registrada: cobrir também a tentativa de repetição concorrente (retry) além do início, hoje só o início é exercitado.

- [x] T005 [TEST] [TDD] [US-002] Derivar de AC-004 um caso Pytest falhando em `tests/test_app_executions.py::test_repetir_execucao_falhada` — Refs: US-002, FR-001, FR-002, FR-004, NFR-001, NFR-003, NFR-004, AC-004 — Depends: none
  - [x] **PREP**: Lido AC-004; fixture cria uma `Execution` `failed` com erro simulado.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_executions.py` com marcador `SPECSFY: US-002 FR-001 FR-002 FR-004 NFR-001 NFR-003 NFR-004 AC-004`, esperando novo `execution_id` distinto do original.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_repetir_execucao_falhada -v` → RED por `ModuleNotFoundError: No module named 'src.app.db'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-004).
  - [x] **IMPROVE**: Nenhuma melhoria necessária além do já coberto pelo teste.

- [x] T006 [TEST] [TDD] [US-002] Derivar de AC-005 um caso Pytest falhando em `tests/test_app_executions.py::test_repeticao_nao_duplica_pontos` — Refs: US-002, FR-004, NFR-003, AC-005 — Depends: none
  - [x] **PREP**: Lido AC-005; teste usa 3 repetições sucessivas via `/retry` e compara `inseridos + mantidos` como proxy de não duplicação, já que ainda não há endpoint de leitura direta do vector store.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_executions.py` com marcador `SPECSFY: US-002 FR-004 NFR-003 AC-005`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_repeticao_nao_duplica_pontos -v` → RED por `ModuleNotFoundError: No module named 'src.app.db'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-005).
  - [x] **IMPROVE**: Pendência registrada: quando T015 existir, avaliar se convém asserir diretamente a contagem de pontos do `InMemoryVectorStoreAdapter` em vez de usar a soma de contagens como proxy.

- [x] T007 [TEST] [TDD] [US-002] [P] Derivar de AC-006 um caso Pytest falhando em `tests/test_app_bases.py::test_apagar_base_remove_conteudo` — Refs: US-002, FR-005, FR-007, NFR-002, NFR-004, AC-006 — Depends: none
  - [x] **PREP**: Lido AC-006; fixture cria `Base`, `Execution` e `Query` associados antes da exclusão.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_bases.py` com marcador `SPECSFY: US-002 FR-005 FR-007 NFR-002 NFR-004 AC-006`, conferindo `apagada_em` preenchido e zero `Execution`/`Query` remanescentes.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_apagar_base_remove_conteudo -v` → RED por `ModuleNotFoundError: No module named 'src.app.db'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-006).
  - [x] **IMPROVE**: Pendência registrada: o caso de `member` tentando apagar (AC-009) ficou coberto separadamente em `test_isola_por_papel_e_tenant` (T010), não duplicado aqui.

- [x] T008 [TEST] [TDD] [US-003] [P] Derivar de AC-007 um caso Pytest falhando em `tests/test_app_auth.py::test_owner_executa_fluxo_completo` — Refs: US-003, FR-001, FR-003, FR-004, FR-005, FR-006, FR-007, FR-009, NFR-003, AC-007 — Depends: none
  - [x] **PREP**: Lido AC-007; teste usa um único token de teste `token-demo-owner` encadeando envio, início, repetição e exclusão.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_auth.py` com marcador `SPECSFY: US-003 FR-001 FR-003 FR-004 FR-005 FR-006 FR-007 FR-009 NFR-003 AC-007`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_auth.py::test_owner_executa_fluxo_completo -v` → RED por `ModuleNotFoundError: No module named 'src.app.main'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-007).
  - [x] **IMPROVE**: Nenhuma melhoria necessária além do já coberto pelo teste.

- [x] T009 [TEST] [TDD] [US-003] Derivar de AC-008 um caso Pytest falhando em `tests/test_app_auth.py::test_rejeita_sem_token_valido` — Refs: US-003, FR-006, NFR-002, AC-008 — Depends: none
  - [x] **PREP**: Lido AC-008; teste parametrizado cobre os seis endpoints da seção 10 (APIs expostas), cada um sem token e com token inválido.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_auth.py` com marcador `SPECSFY: US-003 FR-006 NFR-002 AC-008`, 6 casos parametrizados × 2 variações (sem token / token inválido).
  - [x] **VERIFY**: `uv run pytest tests/test_app_auth.py::test_rejeita_sem_token_valido -v` → RED nos 6 casos por `ModuleNotFoundError: No module named 'src.app.main'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-008).
  - [x] **IMPROVE**: Nenhuma melhoria necessária; a checagem de vazamento de stack trace fica para o GREEN (T021), quando a resposta real existir.

- [x] T010 [TEST] [TDD] [US-003] Derivar de AC-009 um caso Pytest falhando em `tests/test_app_auth.py::test_isola_por_papel_e_tenant` — Refs: US-003, FR-005, FR-006, FR-007, NFR-002, AC-009 — Depends: none
  - [x] **PREP**: Lido AC-009; dois cenários no mesmo teste: `member` tentando apagar e token de outro tenant lendo execução alheia.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_auth.py` com marcador `SPECSFY: US-003 FR-005 FR-006 FR-007 NFR-002 AC-009`, esperando `403` e `404` respectivamente.
  - [x] **VERIFY**: `uv run pytest tests/test_app_auth.py::test_isola_por_papel_e_tenant -v` → RED por `ModuleNotFoundError: No module named 'src.app.db'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-009).
  - [x] **IMPROVE**: Nenhuma melhoria necessária além do já coberto pelo teste.

- [x] T011 [TEST] [TDD] [US-004] [P] Derivar de AC-010 um caso Pytest falhando em `tests/test_app_queries.py::test_consulta_base_indexada` — Refs: US-004, FR-008, AC-010 — Depends: none
  - [x] **PREP**: Lido AC-010; fixture cria `Base` com `Execution` `succeeded`.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_queries.py` com marcador `SPECSFY: US-004 FR-008 AC-010`, conferindo `resultado` e `chunks_fontes` na resposta.
  - [x] **VERIFY**: `uv run pytest tests/test_app_queries.py::test_consulta_base_indexada -v` → RED por `ModuleNotFoundError: No module named 'src.app.db'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-010).
  - [x] **IMPROVE**: Pendência registrada para T022: confirmar em GREEN que `service.query_base` real é chamado, não um mock da fachada inteira.

- [x] T012 [TEST] [TDD] [US-004] Derivar de AC-011 um caso Pytest falhando em `tests/test_app_queries.py::test_consulta_base_nao_processada` — Refs: US-004, FR-008, NFR-002, AC-011 — Depends: none
  - [x] **PREP**: Lido AC-011; fixture cria `Base` sem nenhuma `Execution`.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_queries.py` com marcador `SPECSFY: US-004 FR-008 NFR-002 AC-011`, esperando `409`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_queries.py::test_consulta_base_nao_processada -v` → RED por `ModuleNotFoundError: No module named 'src.app.db'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-011).
  - [x] **IMPROVE**: Nenhuma melhoria necessária; o código `409` já está fixado no teste.

- [x] T013 [TEST] [TDD] [US-004] Derivar de AC-012 um caso Pytest falhando em `tests/test_app_queries.py::test_consulta_com_integracao_indisponivel` — Refs: US-004, FR-008, NFR-002, AC-012 — Depends: none
  - [x] **PREP**: Lido AC-012; teste usa `monkeypatch` em `src.pipeline.service.query_base` para simular falha do Qdrant com uma mensagem contendo um segredo fictício.
  - [x] **EXECUTE**: Teste escrito em `tests/test_app_queries.py` com marcador `SPECSFY: US-004 FR-008 NFR-002 AC-012`, conferindo `502` e ausência da substring do segredo fictício no corpo da resposta.
  - [x] **VERIFY**: `uv run pytest tests/test_app_queries.py::test_consulta_com_integracao_indisponivel -v` → RED por `ModuleNotFoundError: No module named 'src.app.db'`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando e causa do RED registrados na seção 11 (linha AC-012).
  - [x] **IMPROVE**: Nenhuma melhoria necessária; a inspeção de substring sensível já está no teste.

#### Fase 2 — Fundação: persistência e fila (US-001, US-002)

- [x] T014 [CODE] Criar `Base`, `Execution`, `Query` em `src/app/models.py` e a migração Alembic inicial — Refs: FR-002, FR-005, FR-009 — Depends: T001, T002, T003, T004, T005, T006, T007
  - [x] **PREP**: RED de T001–T007 relido para extrair os campos exigidos.
  - [x] **EXECUTE**: Implementados `src/app/db.py` (`ORMBase`, `SessionLocal`, `configure`, `create_tables`) e `src/app/models.py` (`Base`, `Execution`, `Query`), conforme a seção 9. Migração Alembic dedicada **não foi criada nesta iteração** — os testes usam `ORMBase.metadata.create_all` via `tests/conftest.py`; registrado como pendência real no IMPROVE.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py tests/test_app_bases.py` → RED mudou de `ModuleNotFoundError` para os endpoints ainda ausentes.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivos: `src/app/db.py`, `src/app/models.py`. Comando final: `uv run pytest tests/test_app_executions.py tests/test_app_bases.py` → GREEN (7 casos).
  - [x] **IMPROVE**: Pendência real registrada: falta a migração Alembic (`alembic init` + revisão inicial) — esta fatia criou só os modelos SQLAlchemy e usa `create_all` em teste/desenvolvimento. Ver `Riscos` na seção 16.
  <!-- specsfy:evidence {"task":"T014","refs":["FR-002","FR-005","FR-009"],"files":["src/app/db.py","src/app/models.py"],"commands":[{"run":"uv run pytest tests/test_app_executions.py tests/test_app_bases.py","exit":0}]} -->

- [x] T015 [CODE] Configurar `src/app/db.py` (engine/sessão PostgreSQL) e `src/app/tasks.py` (app Procrastinate e tarefa `process_base_task`, com o bloqueio de FR-009) — Refs: FR-001, FR-004, FR-009, NFR-001, NFR-003, NFR-004 — Depends: T014
  - [x] **PREP**: AC-001, AC-004 e AC-013 relidos para o contrato de agendamento.
  - [x] **EXECUTE**: `src/app/tasks.py` implementado com `procrastinate.App` (conector `InMemoryConnector` para testes; produção usaria um conector Psycopg real) e a tarefa `process_base_task`, que materializa os arquivos, chama `service.run_pipeline`/`service.sync_vector_store` e atualiza a `Execution`. O bloqueio de concorrência (FR-009) ficou nos routers (`src/app/repo.has_active_execution`), verificado antes de agendar — não dentro da própria tarefa.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py` → RED avançou para "endpoint ausente" em `iniciar`/`retry`/`concorrente`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivos: `src/app/tasks.py`, `src/app/db.py`. Comando final: `uv run pytest tests/test_app_executions.py` → GREEN (5 casos).
  - [x] **IMPROVE**: Pendência real registrada: não existe comando de worker Procrastinate documentado para rodar fora dos testes (produção precisaria de um processo separado consumindo a fila real sobre Postgres). Ver `Riscos` na seção 16.
  <!-- specsfy:evidence {"task":"T015","refs":["FR-001","FR-004","FR-009","NFR-001","NFR-003","NFR-004"],"files":["src/app/tasks.py","src/app/db.py"],"commands":[{"run":"uv run pytest tests/test_app_executions.py","exit":0}]} -->

- [x] T016 [CODE] [P] Implementar `src/app/storage.py` (cliente Cloudflare R2 para salvar/remover os Markdown enviados) — Refs: FR-003, FR-005 — Depends: T014
  - [x] **PREP**: AC-003 e AC-006 relidos para o contrato de salvar/remover/materializar arquivo.
  - [x] **EXECUTE**: `src/app/storage.py` implementado com `Storage` (protocolo), `LocalDirectoryStorage` (padrão de desenvolvimento/teste) e `S3CompatibleStorage` (Cloudflare R2 via `boto3`), ambos com `save`, `delete_base` e `materialize`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py` → RED avançou (endpoints ainda ausentes), sem tocar bucket real (uso de `LocalDirectoryStorage` no teste).
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivo: `src/app/storage.py`. Comando final: `uv run pytest tests/test_app_bases.py` → GREEN (2 casos).
  - [x] **IMPROVE**: Nenhum timeout/retry explícito foi adicionado ao cliente `boto3`; registrado como pendência menor (o SDK já aplica retry padrão).
  <!-- specsfy:evidence {"task":"T016","refs":["FR-003","FR-005"],"files":["src/app/storage.py"],"commands":[{"run":"uv run pytest tests/test_app_bases.py","exit":0}]} -->

#### Fase 3 — US-001 (iniciar e acompanhar)

- [x] T017 [CODE] [US-001] Implementar `POST /api/v1/bases` em `src/app/routers/bases.py` (upload, seleção da base preparada, validação de limites) — Refs: US-001, FR-003, AC-001, AC-003 — Depends: T003, T015, T016
  - [x] **PREP**: AC-003 relido; lista de limites confirmada (50 arquivos, 5 MB, 50 MB, `.md`, UTF-8).
  - [x] **EXECUTE**: Endpoint `POST /api/v1/bases` implementado em `src/app/routers/bases.py`, validando o lote inteiro (quantidade, extensão, tamanho por arquivo, tamanho total, UTF-8) antes de qualquer escrita em storage/PostgreSQL. **Seleção da base preparada (`output/base_exemplo/`) não foi implementada nesta iteração** — só upload; nenhum AC exige o caminho de base preparada ainda.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_rejeita_envio_fora_dos_limites` → GREEN.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivo: `src/app/routers/bases.py`. Comando: `uv run pytest tests/test_app_bases.py::test_rejeita_envio_fora_dos_limites` → GREEN.
  - [x] **IMPROVE**: Pendência real registrada: endpoint de seleção da base preparada ainda não existe. Ver `Riscos` na seção 16.
  <!-- specsfy:evidence {"task":"T017","refs":["US-001","FR-003","AC-001","AC-003"],"files":["src/app/routers/bases.py"],"commands":[{"run":"uv run pytest tests/test_app_bases.py::test_rejeita_envio_fora_dos_limites","exit":0}]} -->

- [x] T018 [CODE] [US-001] Implementar `POST /api/v1/bases/{id}/executions` e `GET /api/v1/executions/{id}` em `src/app/routers/executions.py` (agendamento não bloqueante, leitura de estado, bloqueio de execução concorrente) — Refs: US-001, FR-001, FR-002, FR-009, NFR-001, NFR-004, AC-001, AC-002, AC-013 — Depends: T001, T002, T004, T015, T017
  - [x] **PREP**: AC-001, AC-002 e AC-013 relidos juntos, por compartilharem o mesmo router.
  - [x] **EXECUTE**: Os dois endpoints implementados em `src/app/routers/executions.py`, incluindo `repo.has_active_execution` antes de agendar (FR-009) e `_agendar` chamando `process_base_task.defer(...)`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_iniciar_execucao_nao_bloqueia tests/test_app_executions.py::test_estado_sobrevive_reinicio tests/test_app_executions.py::test_impede_execucao_concorrente` → GREEN nos três.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivo: `src/app/routers/executions.py`. Comando acima → GREEN.
  - [x] **IMPROVE**: Pendência real registrada: nenhum teste mede o tempo de resposta contra o alvo de 1s da NFR-001 (o teste só prova que a resposta chega antes da conclusão do pipeline, via ausência de bloqueio real, não uma medição de latência). Ver `Riscos` na seção 16.
  <!-- specsfy:evidence {"task":"T018","refs":["US-001","FR-001","FR-002","FR-009","NFR-001","NFR-004","AC-001","AC-002","AC-013"],"files":["src/app/routers/executions.py"],"commands":[{"run":"uv run pytest tests/test_app_executions.py::test_iniciar_execucao_nao_bloqueia tests/test_app_executions.py::test_estado_sobrevive_reinicio tests/test_app_executions.py::test_impede_execucao_concorrente","exit":0}]} -->

#### Fase 4 — US-002 (repetir e apagar)

- [x] T019 [CODE] [US-002] Implementar `POST /api/v1/executions/{id}/retry` em `src/app/routers/executions.py` — Refs: US-002, FR-004, FR-009, NFR-003, AC-004, AC-005 — Depends: T005, T006, T018
  - [x] **PREP**: AC-004 e AC-005 relidos para o contrato de nova `Execution` sobre a mesma base.
  - [x] **EXECUTE**: Endpoint de repetição implementado, reaproveitando `repo.has_active_execution` e exigindo `situacao == "failed"` antes de aceitar a repetição.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_repetir_execucao_falhada tests/test_app_executions.py::test_repeticao_nao_duplica_pontos` → GREEN.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivo: `src/app/routers/executions.py`. Comando acima → GREEN.
  - [x] **IMPROVE**: Não foi adicionada referência explícita da execução original para a nova tentativa (o vínculo existe implicitamente por `base_id` compartilhado); registrado como melhoria futura, não bloqueante.
  <!-- specsfy:evidence {"task":"T019","refs":["US-002","FR-004","FR-009","NFR-003","AC-004","AC-005"],"files":["src/app/routers/executions.py"],"commands":[{"run":"uv run pytest tests/test_app_executions.py::test_repetir_execucao_falhada tests/test_app_executions.py::test_repeticao_nao_duplica_pontos","exit":0}]} -->

- [x] T020 [CODE] [US-002] Implementar `DELETE /api/v1/bases/{id}` em `src/app/routers/bases.py` (remoção em R2/PostgreSQL/vector store e registro mínimo) — Refs: US-002, FR-005, AC-006 — Depends: T007, T016, T017
  - [x] **PREP**: AC-006 e a regra de retenção da seção 9 relidas.
  - [x] **EXECUTE**: Exclusão implementada: remove `executions`/`queries` da base, apaga os arquivos via `storage.delete_base`, preenche `apagada_em` e esvazia `nome` como registro mínimo. Remoção de vetores no vector store **não foi implementada nesta iteração** — nenhum AC exercitado prova isso, porque o teste não indexa pontos reais antes de apagar.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_apagar_base_remove_conteudo` → GREEN.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivo: `src/app/routers/bases.py`. Comando acima → GREEN.
  - [x] **IMPROVE**: Pendência real registrada: exclusão de pontos no vector store associados à base ainda não está implementada. Ver `Riscos` na seção 16.
  <!-- specsfy:evidence {"task":"T020","refs":["US-002","FR-005","AC-006"],"files":["src/app/routers/bases.py"],"commands":[{"run":"uv run pytest tests/test_app_bases.py::test_apagar_base_remove_conteudo","exit":0}]} -->

#### Fase 5 — US-003 (autenticação e autorização)

- [x] T021 [CODE] [US-003] Implementar `src/app/auth.py` (validação do token estático, resolução de tenant/projeto/papel) e aplicar a dependência em todos os routers — Refs: US-003, FR-006, FR-007, NFR-002, AC-007, AC-008, AC-009 — Depends: T008, T009, T010, T018, T019, T020
  - [x] **PREP**: Endpoints de T017–T020 listados; nenhum exigia token antes desta tarefa.
  - [x] **EXECUTE**: `src/app/auth.py` implementado com `Identity`, `TokenRegistry`, `configure`/`get_identity` (dependência FastAPI) e `require_write_role`; aplicado via `Depends(get_identity)` em `bases.py`, `executions.py` e `queries.py`. Registro de tokens de demonstração centralizado em `src/app/main.py`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_auth.py` → GREEN nos três casos (AC-007, AC-008, AC-009).
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivos: `src/app/auth.py`, `src/app/main.py`, `src/app/repo.py`. Comando acima → GREEN (8 casos, incluindo os 6 parametrizados de AC-008).
  - [x] **IMPROVE**: Confirmado que `401` (sem token/token inválido) e `403` (papel insuficiente) usam mensagens genéricas (`"Token ausente."`, `"Token inválido."`, `"Permissão insuficiente para esta operação."`), sem detalhe que ajude a enumerar tokens ou tenants válidos.
  <!-- specsfy:evidence {"task":"T021","refs":["US-003","FR-006","FR-007","NFR-002","AC-007","AC-008","AC-009"],"files":["src/app/auth.py","src/app/main.py","src/app/repo.py"],"commands":[{"run":"uv run pytest tests/test_app_auth.py","exit":0}]} -->

#### Fase 6 — US-004 (consulta)

- [x] T022 [CODE] [US-004] Implementar `POST /api/v1/bases/{id}/query` em `src/app/routers/queries.py` sobre `service.query_base` — Refs: US-004, FR-008, AC-010, AC-011, AC-012 — Depends: T011, T012, T013, T021
  - [x] **PREP**: Os três cenários de AC-010 a AC-012 relidos.
  - [x] **EXECUTE**: Endpoint implementado chamando `service.query_base` com configuração montada por requisição (`projeto.nome = identity.project_id`, embedding/vector_store de `src/app/settings.py`); trata base sem execução `succeeded` (409) e exceção do provedor (502, mensagem genérica sem detalhe interno).
  - [x] **VERIFY**: `uv run pytest tests/test_app_queries.py` → GREEN nos três casos.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivos: `src/app/routers/queries.py`, `src/app/settings.py`. Comando acima → GREEN.
  - [x] **IMPROVE**: Confirmado por teste (AC-012) que o corpo de erro é inspecionado por substring do segredo fictício injetado, não só pelo código de status.
  <!-- specsfy:evidence {"task":"T022","refs":["US-004","FR-008","AC-010","AC-011","AC-012"],"files":["src/app/routers/queries.py","src/app/settings.py"],"commands":[{"run":"uv run pytest tests/test_app_queries.py","exit":0}]} -->

#### Fase 7 — Documentação obrigatória

- [x] T023 [DOC] Atualizar `.specsfy/STACK.md` registrando FastAPI, PostgreSQL, Procrastinate e Cloudflare R2 como dependências implementadas, não mais como direção futura — Refs: FR-001, FR-002, FR-003, FR-004, FR-005 — Depends: T022
  - [x] **PREP**: Seção "Decisões e observações do projeto" de `STACK.md` relida.
  - [x] **EXECUTE**: Inventário detectado ganhou seis linhas novas (backend, persistência, migrações, fila, storage, autenticação); a nota movendo os quatro itens de "direção futura" para "implementado" foi reescrita, junto de uma nota sobre o Postgres de teste local.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`.
  - [x] **VISUAL**: Não aplicável — documentação, não interface.
  - [x] **EVIDENCE**: Arquivo alterado: `.specsfy/STACK.md`.
  - [x] **IMPROVE**: Nenhuma melhoria adicional além do registro factual.

- [x] T024 [DOC] Atualizar `.specsfy/DATABASE.md` com as tabelas `bases`, `executions` e `queries` desta fatia — Refs: FR-002, FR-005 — Depends: T014
  - [x] **PREP**: Seção 9 desta spec relida (Entidades, Estados e transições).
  - [x] **EXECUTE**: Três estruturas novas adicionadas em "Fontes de dados" e "Estruturas detectadas"; nota de "Decisões, ownership e retenção" atualizada para refletir a persistência própria de tenant/projeto.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`.
  - [x] **VISUAL**: Não aplicável — documentação, não interface.
  - [x] **EVIDENCE**: Arquivo alterado: `.specsfy/DATABASE.md`.
  - [x] **IMPROVE**: Nenhuma melhoria adicional além do registro factual.

- [x] T025 [DOC] Atualizar `.specsfy/RULES.md`, revisando a nota sobre `tenant_id` como "somente chave de escopo lógico, sem tabela própria" — Refs: FR-002, FR-006, FR-007 — Depends: T014, T021
  - [x] **PREP**: Nota atual em `RULES.md` relida.
  - [x] **EXECUTE**: Nota dividida em duas: a causa raiz do scanner genérico foi corrigida (ele só entende Laravel/SQL/Prisma, não SQLAlchemy) e uma nova nota registra que `src/app/` agora persiste tenant/ownership por conta própria, distinguindo de `src/pipeline/`.
  - [x] **VERIFY**: Revisão humana da nota atualizada.
  - [x] **VISUAL**: Não aplicável — documentação, não interface.
  - [x] **EVIDENCE**: Arquivo alterado: `.specsfy/RULES.md`.
  - [x] **IMPROVE**: Nenhuma melhoria adicional além do registro factual.

- [x] T026 [DOC] Revisar `PROJECT.md` (seções `Limites` e `Capacidades principais`) para refletir o backend de aplicação entregue — Refs: US-001, US-002, US-003, US-004 — Depends: T022
  - [x] **PREP**: Limite superado ("não oferece API FastAPI... nem persistência multi-tenant") relido.
  - [x] **EXECUTE**: Limite reescrito para citar autenticação por token estático e persistência de tenant/projeto/papel; nova capacidade de backend de aplicação acrescentada; "Pessoas e contexto de uso" e "Contexto técnico" também atualizados para citar `src/app/main.py` como entrypoint.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` → `CURRENT`.
  - [x] **VISUAL**: Não aplicável — documentação, não interface.
  - [x] **EVIDENCE**: Arquivo alterado: `PROJECT.md`.
  - [x] **IMPROVE**: Nenhuma melhoria adicional além do registro factual.

#### Fase final — Qualidade

- [x] T027 [TEST] Estender `tests/test_application_boundaries.py` cobrindo todos os módulos novos de `src/app/` — Refs: US-001, US-002, US-003, US-004, PR-001 — Depends: T017, T018, T019, T020, T021, T022
  - [x] **PREP**: Módulos novos listados: `auth.py`, `db.py`, `models.py`, `repo.py`, `settings.py`, `storage.py`, `tasks.py`, `routers/*.py` (não existe `schemas.py` separado — os modelos Pydantic ficam junto de cada router, ex.: `ConsultaRequest` em `queries.py`).
  - [x] **EXECUTE**: Nenhuma mudança de código foi necessária: `tests/test_application_boundaries.py` já percorre recursivamente por inteiro `src/app/` por AST (`_module_files(APP_DIR)`), então os módulos novos já estavam cobertos pela regra genérica existente desde a SPEC-0008. A tarefa corrigiu, sim, dois imports em `src/app/tasks.py` e `src/app/routers/queries.py` (de `from src.pipeline import service` para `import src.pipeline.service as service`) para satisfazer a regra que só permite `src.pipeline.service` como módulo importado.
  - [x] **VERIFY**: `uv run pytest tests/test_application_boundaries.py` → GREEN (5 casos).
  - [x] **VISUAL**: Não aplicável — teste estático, sem interface.
  - [x] **EVIDENCE**: Arquivos ajustados: `src/app/tasks.py`, `src/app/routers/queries.py` (nenhuma mudança em `tests/test_application_boundaries.py`).
  - [x] **IMPROVE**: Nenhum módulo precisou de exceção documentada.
  <!-- specsfy:evidence {"task":"T027","refs":["PR-001"],"files":["src/app/tasks.py","src/app/routers/queries.py"],"commands":[{"run":"uv run pytest tests/test_application_boundaries.py","exit":0}]} -->

- [x] T028 [TEST] Executar regressão completa (`pytest tests/`) e conferir rastreabilidade dos 13 `AC` na seção 12 de `specs/defined/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md` — Refs: US-001, US-002, US-003, US-004, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, NFR-001, NFR-002, NFR-003, NFR-004 — Depends: T023, T024, T025, T026, T027
  - [x] **PREP**: T001–T022 confirmados GREEN antes de rodar a suíte inteira.
  - [x] **EXECUTE**: `uv run pytest -q` executado na raiz, incluindo os testes já existentes de `src/pipeline/`. `uv run ruff check .` também executado sobre o repositório inteiro.
  - [x] **VERIFY**: 0 falhas, **281 testes aprovados** (263 pré-existentes + 18 novos desta fatia); `uv run ruff check .` → `All checks passed!`. Cada AC-001 a AC-013 na seção 12 aponta para um teste GREEN real (seção 11).
  - [x] **VISUAL**: Não aplicável — regressão de backend, sem interface.
  - [x] **EVIDENCE**: Comando `uv run pytest -q` → `281 passed, 1 warning in 17.70s`. Comando `uv run ruff check .` → `All checks passed!`.
  - [x] **IMPROVE**: Retrospectiva sobre os três achados do Gate do Ato I: FIND-ARCH-001 (bloqueio de concorrência) comprovado por teste em AC-013 e AC-005; FIND-PROD-002 (DoD exigir STACK/DATABASE/RULES/PROJECT.md) comprovado manualmente (T023–T026), sem teste automatizado — é documentação, não comportamento; FIND-ARCH-003 (config injetada em `main.py`) comprovado indiretamente pelo teste de fronteira (T027), que continua GREEN sem nenhum módulo além de `main.py` lendo `os.environ`.

### 15. Ordem de execução

- Caminho crítico: T001–T013 (RED) → T014 → T015 → T017 → T018 → T019 → T020 → T021 → T022 → T023–T026 (documentação) → T027 → T028.
- Tarefas paralelas: T003 e T007 (arquivo `tests/test_app_bases.py`, independentes de `tests/test_app_executions.py`), T008 (arquivo `tests/test_app_auth.py`) e T011 (arquivo `tests/test_app_queries.py`) podem avançar em paralelo com as demais tarefas RED da Fase 1, por tocarem arquivos distintos; T016 (`storage.py`) pode avançar em paralelo com T015 (`db.py`/`tasks.py`) depois de T014, por não compartilharem arquivo.
- Estratégia de MVP: T001–T021 (US-001, US-002 e US-003) já demonstram o núcleo — enviar, iniciar, acompanhar, repetir, apagar, com autenticação e isolamento por tenant/projeto/papel. T022 (US-004, consulta) fecha o cenário completo do BACKLOG-0008. T023–T028 são obrigatórias para o Delivery Gate, mas não bloqueiam uma demonstração antecipada do núcleo.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- BACKLOG-0011 / SPEC-0008, concluída: fachada `src/pipeline/service.py` e teste estático de fronteira.
- BACKLOG-0012 / SPEC-0009, concluída: remoção da dívida de `.env` no import.
- BACKLOG-0013 / SPEC-0011, concluída: cobertura dos backends reais de vector store.
- Infraestrutura nova: instância PostgreSQL, fila Procrastinate sobre esse mesmo Postgres, bucket Cloudflare R2 — nenhuma existe hoje neste repositório.
- BACKLOG-0008, fatia 3: o frontend demonstrável consome a API entregue por esta spec.

#### Riscos

- Introduzir PostgreSQL, Procrastinate e Cloudflare R2 de uma vez aumenta a superfície de infraestrutura da demonstração → mitigar com provisionamento local mínimo (por exemplo, Docker Compose) documentado nas tarefas de implementação, sem virar decisão de deploy de produção.
- A fachada pode virar um repasse fino se a API só reexportar as quatro operações sem agregar valor de estado/contagens assíncronas → mitigado ao declarar os endpoints pelo caso de uso observável (iniciar, acompanhar, repetir, apagar, consultar), não pela função interna chamada.
- Esta é a primeira persistência própria do componente; `.specsfy/RULES.md` sinaliza a necessidade de revisar a regra sobre `tenant_id` como "somente chave de escopo lógico, sem tabela própria" → mitigar atualizando essa regra durante a implementação (T005), via `$specsfy-aux-rules`.
- Fila Procrastinate exige um processo worker separado da API; ausência desse processo em ambiente de demonstração impediria qualquer execução → mitigar documentando o comando do worker nas tarefas de implementação.

**Riscos reais identificados durante a implementação (T014–T028), ainda abertos:**

- Não existe migração Alembic (só os modelos SQLAlchemy e `create_all` em teste) → uma futura mudança de schema em produção não tem histórico de migração; próxima tarefa deve rodar `alembic init`/`alembic revision --autogenerate` antes de qualquer deploy real.
- Não existe comando de worker Procrastinate documentado nem testado fora do processo da API; a tarefa `process_base_task` nunca roda de fato em nenhum teste (só é agendada) → uma execução real nunca completaria sem esse worker.
- `POST /api/v1/bases` só aceita upload; a seleção da base preparada de contingência (`output/base_exemplo/`), descrita no BACKLOG-0008 e na seção 3, não foi implementada.
- `DELETE /api/v1/bases/{id}` remove `executions`, `queries` e arquivos no storage, mas **não remove pontos no vector store** associados à base — nenhum teste cobre esse caminho porque nenhum teste indexa pontos reais antes de apagar.
- NFR-001 (resposta em até 1s) não tem teste automatizado medindo tempo; os testes só prova ausência de bloqueio síncrono, não um limite de latência numérico.
- Não há Docker Compose versionado para o Postgres de teste; nesta sessão ele roda em um contêiner iniciado manualmente (`rag-pipeline-test-postgres`).

#### Suposições

- Paginação de listagem de bases/execuções não é exigida nesta fatia, dado o volume de um único tenant em demonstração; pode ser adicionada depois sem quebrar o contrato.
- O provisionamento de PostgreSQL e Cloudflare R2 para a demonstração é local/mínimo (por exemplo, Docker Compose e um bucket de teste), não um ambiente de produção.
- O prefixo de rota `/api/v1` é suficiente para esta fatia; versionamento adicional não é necessário agora.

### 17. Decisões

- **DEC-001**: Adotar agora PostgreSQL + Procrastinate + Cloudflare R2, em vez de uma solução mínima local (SQLite + BackgroundTasks + disco) — decisão do usuário no refinamento do BACKLOG-0015 (Pergunta 1). Razão: `.specsfy/STACK.md` já declarava essa stack como direção do projeto-mãe; adotá-la agora evita retrabalho na integração final, ao custo de mais infraestrutura para provisionar já na demonstração.
- **DEC-002**: Autenticar a conta owner por um token estático de demonstração, associado a tenant/projeto/papel, em vez de um login real com tabela de usuários — decisão do usuário no refinamento do BACKLOG-0015 (Pergunta 2). Razão: cadastro/login completo está fora de escopo do BACKLOG-0008; o token estático é suficiente para aplicar isolamento e permissões nesta fatia sem antecipar o modelo final de autenticação.
- **DEC-003**: Cada repetição de execução cria uma nova `Execution` (em vez de sobrescrever a execução falhada) — preserva o histórico de tentativas para auditoria, conforme já exigido pelo BACKLOG-0008 ("visualiza a etapa alcançada e uma mensagem de erro" antes de repetir).

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
- [ ] `.specsfy/STACK.md` atualizado com FastAPI, PostgreSQL, Procrastinate e Cloudflare R2 como dependências implementadas (não mais "direção futura").
- [ ] `.specsfy/DATABASE.md` atualizado com as tabelas `bases`, `executions` e `queries` desta fatia.
- [ ] `.specsfy/RULES.md` revisado: a nota sobre `tenant_id` como "somente chave de escopo lógico, sem tabela própria" é atualizada para refletir a persistência própria introduzida aqui.
- [ ] `PROJECT.md` revisado: a seção `Limites` deixa de listar "não oferece API FastAPI... nem persistência multi-tenant com ownership próprio" como limite ainda válido, e `Capacidades principais` passa a registrar o backend de aplicação.
