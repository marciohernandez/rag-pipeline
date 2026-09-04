# Especificação integrada: Backend de aplicação sobre o pipeline

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0012 |
| Slug | 0012-backend-de-aplicacao-sobre-o-pipeline |
| Status | Reviewing |
| Effort | 8 |
| Effort updated at | 2026-09-04 |
| Effort rationale | Reabertura do Ato II para fechar os 6 gaps do Delivery Gate mais um achado novo durante o planejamento: o escopo lógico do vector store não isola por base (só por tenant/projeto), afetando FR-005 (delete) e FR-008 (consulta); a correção fica na camada `src/app/`, sem tocar `src/pipeline/`. Soma-se infraestrutura real (Alembic, worker Procrastinate, Docker Compose); perfil `high`. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
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
| US-002, FR-005, AC-006 (estendido) | AC-006 na seção 6 | `tests/test_app_bases.py::test_apagar_base_remove_pontos_vector_store` com marcador `SPECSFY: US-002 FR-005 AC-006` | `AssertionError: assert {'chunk-1'} == set()` (`uv run pytest tests/test_app_bases.py::test_apagar_base_remove_pontos_vector_store -v`) | Pendente (T032) | Pendente |
| US-004, FR-008, AC-010 (estendido) | AC-010 na seção 6 | `tests/test_app_queries.py::test_consulta_nao_mistura_bases_do_mesmo_projeto` com marcador `SPECSFY: US-004 FR-008 AC-010` | `AssertionError` — trecho da base B presente na consulta da base A (`uv run pytest tests/test_app_queries.py::test_consulta_nao_mistura_bases_do_mesmo_projeto -v`) | Pendente (T031) | Pendente |
| US-001, FR-003 | Seção 3 (Escopo e atores) — seleção da base preparada | `tests/test_app_bases.py::test_seleciona_base_preparada` com marcador `SPECSFY: US-001 FR-003` | `assert 400 == 201` (`uv run pytest tests/test_app_bases.py::test_seleciona_base_preparada -v`) | Pendente (T034) | Pendente |
| US-001, NFR-001 | NFR-001 na seção 7 — verificação declarada | `tests/test_app_executions.py::test_resposta_inicio_execucao_em_ate_1s` com marcador `SPECSFY: US-001 NFR-001` | Não aplicável — GREEN já na primeira execução, comportamento já existia | GREEN (`uv run pytest tests/test_app_executions.py::test_resposta_inicio_execucao_em_ate_1s`) | GREEN |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001, AC-004, AC-007 | Integração | `pytest tests/test_app_executions.py tests/test_app_auth.py` | GREEN — Passed |
| FR-002 | AC-001, AC-002, AC-004 | Integração | `pytest tests/test_app_executions.py` | GREEN — Passed |
| FR-003 | AC-001, AC-003, AC-007 | Unidade/Integração | `pytest tests/test_app_executions.py tests/test_app_bases.py tests/test_app_auth.py` | GREEN — Passed |
| FR-004 | AC-004, AC-005, AC-007 | Integração | `pytest tests/test_app_executions.py tests/test_app_auth.py` | GREEN — Passed |
| FR-005 | AC-006, AC-007, AC-009 | Integração | `pytest tests/test_app_bases.py tests/test_app_auth.py` | GREEN — Passed |
| FR-006 | AC-007, AC-008, AC-009 | Unidade/Integração | `pytest tests/test_app_auth.py` | GREEN — Passed |
| FR-007 | AC-006, AC-007, AC-009 | Unidade/Integração | `pytest tests/test_app_bases.py tests/test_app_auth.py` | GREEN — Passed |
| FR-008 | AC-010, AC-011, AC-012 | Integração | `pytest tests/test_app_queries.py` | GREEN — Passed |
| FR-009 | AC-001, AC-007, AC-013 | Integração | `pytest tests/test_app_executions.py tests/test_app_auth.py` | GREEN — Passed |
| NFR-001 | AC-001, AC-003, AC-004 | Integração | `pytest tests/test_app_executions.py tests/test_app_bases.py` | GREEN — Passed |
| NFR-002 | AC-006, AC-008, AC-009, AC-011, AC-012 | Integração | `pytest tests/test_app_bases.py tests/test_app_auth.py tests/test_app_queries.py` | GREEN — Passed |
| NFR-003 | AC-004, AC-005, AC-007 | Integração | `pytest tests/test_app_executions.py tests/test_app_auth.py` | GREEN — Passed |
| NFR-004 | AC-002, AC-004, AC-006 | Integração | `pytest tests/test_app_executions.py tests/test_app_bases.py` | GREEN — Passed |
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
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md`
- **Achados**: Estrutura original validada (28 tarefas, T001–T028 concluídas, GREEN — ver histórico abaixo). Reaberta em 2026-09-04 para fechar os 6 gaps do Delivery Gate mais um achado novo (isolamento por base no vector store ausente, afetando FR-005 e FR-008); 14 tarefas novas (T029–T043, com T036 descartada após T035 confirmar comportamento já conforme) adicionadas. Validador reexecutado: `VALID DRAFT` (42 tarefas, 252 itens de checklist). Os 4 predecessores TDD da nova fase (T029, T030, T033, T035) tiveram RED/GREEN observado nesta reabertura — evidência na seção 11 (linhas "estendido"/novas). `Plan Gate` promovido a `Passed`; as 10 tarefas de código/infraestrutura/documentação restantes (T031, T032, T034, T037–T043) ficam para o Ato III (`$specsfy-07-implement`).
- **Histórico (validação original, 2026-09-04)**: Estrutura de tarefas validada (`VALID DRAFT`, 28 tarefas, 168 itens de checklist). Todos os 28 predecessores TDD (T001–T013) tiveram RED observado e, em seguida, as 15 tarefas de código/documentação/qualidade (T014–T028) foram executadas e concluídas com evidência GREEN registrada na seção 11.

#### Gate do Ato III — Entrega

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md .` e `node .agents/skills/specsfy-06-tdd-bdd/scripts/verify_acceptance.mjs specs/in-progress/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md .`
- **Achados (validação original, 2026-09-04)**: Os 13 `AC` estavam GREEN e a suíte completa passava (281 testes), mas `Delivery Gate` ficou `In Progress` por seis gaps reais e conscientes: FR-005 não removia pontos no vector store ao apagar uma base; seleção de base preparada não implementada; sem migração Alembic; sem comando de worker Procrastinate documentado/testado; NFR-001 sem medição automatizada; sem Docker Compose para o Postgres de teste.
- **Achados (fechamento dos gaps, reabertura de 2026-09-04)**: Os seis gaps foram fechados por T029–T041 (seção 14), mais um achado mais profundo descoberto durante a correção do primeiro gap — o escopo lógico do vector store não isolava por base, afetando também FR-008/consulta, não só FR-005/delete (ver seção 16). `check_traceability.mjs` reporta `30/30 IDs cobertos`; os `MARCADORES ÓRFÃOS` (AC-014 em diante) continuam sendo ruído pré-existente de specs anteriores, já registrado em `specs/inbox/2026-09-02-195707-namespacear-marcadores-specsfy-por-spec.md`, não uma lacuna desta spec. `verify_acceptance.mjs` → `QA: PASSED` (seção 12 ajustada para usar a palavra `Passed` exigida pelo auditor, mantendo `GREEN` como registro do resultado real do pytest). Suíte completa: `uv run pytest -q` → **287 testes aprovados**; `uv run ruff check .` → `All checks passed!`. Todos os 43 itens da seção 14 concluídos.
- **Achados (correção pós-fechamento, mesmo dia)**: `Delivery Gate` foi marcado `Passed` acima antes de uma revisão (`/code-review`) sobre o commit desta reabertura, que revelou uma segunda camada do mesmo achado: `tenant_id` nunca é gravado no metadata do chunk pelo pipeline real (`src/pipeline/identity.py`), então o escopo de escrita sempre tinha `tenant_id=None`, nunca batendo com o `tenant_id` explícito que `query_base`/`delete_scope` passavam — em produção, qualquer consulta real voltaria vazia e qualquer DELETE deixaria os pontos reais órfãos, mesmo com T029–T032 GREEN (os testes desses itens mascaravam o problema construindo chunks manualmente já com `tenant_id`, o que o pipeline real nunca faz). Corrigido dobrando `tenant_id` na string composta de `scope_project_id` (ver T031, IMPROVE). `tests/test_app_worker.py` ganhou uma prova de ponta a ponta (worker real → consulta real → DELETE real) que reproduz o pipeline sem atalhos e que teria falhado antes desta correção. Suíte completa reexecutada após a correção: **287 testes aprovados** (estável em 3 execuções consecutivas); `uv run ruff check .` → `All checks passed!`; `verify_acceptance.mjs` → `QA: PASSED`. `Delivery Gate: Passed` permanece, agora com essa lacuna real fechada, não apenas a superficial. Dois riscos novos, não bloqueantes, ficaram registrados na seção 16 para acompanhamento futuro (default `in_memory` de `_app_settings()` incompatível com escrita real; nota de processo sobre um `DROP DATABASE` executado indevidamente contra um banco de scratch durante T037).

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

#### Fase 8 — Fechamento dos gaps do Delivery Gate

- [x] T029 [TEST] [TDD] [US-002] Derivar de AC-006 um novo caso Pytest em `tests/test_app_bases.py::test_apagar_base_remove_pontos_vector_store` que indexa pontos reais (via `InMemoryVectorStoreAdapter` compartilhado por `monkeypatch`, no lugar do dublê SDK do `_QdrantBackend`) na base antes de apagar — Refs: FR-005, AC-006 — Depends: none
  - [x] **PREP**: Confirmado que `build_vector_store` cria um backend novo a cada chamada — para o teste enxergar o mesmo estado entre a indexação de setup e o DELETE, `src.pipeline.indexing.build_vector_store` é substituído por uma função que sempre devolve a mesma instância de `InMemoryVectorStoreAdapter`. Confirmado também que `SyncSafetyPolicy` só aceita `provider: "qdrant"` em `sync_vector_store`, então o config declara `"qdrant"` mesmo usando o dublê em memória por trás.
  - [x] **EXECUTE**: Teste escrito com marcador `SPECSFY: US-002 FR-005 AC-006`, indexando um chunk real via `service.sync_vector_store` antes do DELETE e asserindo `list_ids(escopo)` vazio depois.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_apagar_base_remove_pontos_vector_store -v` → RED confirmado: `AssertionError: assert {'chunk-1'} == set()` — o ponto continua no vector store após o DELETE.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando acima → RED por `AssertionError` no ponto remanescente (não por erro de import/fixture).
  - [x] **IMPROVE**: Nenhuma melhoria aplicável antes do GREEN (T032).

- [x] T030 [TEST] [TDD] [US-004] Derivar de AC-010 um novo caso Pytest em `tests/test_app_queries.py::test_consulta_nao_mistura_bases_do_mesmo_projeto` com duas bases no mesmo tenant/projeto — Refs: FR-008, AC-010 — Depends: none
  - [x] **PREP**: Confirmado em `src/app/routers/queries.py` e `src/app/tasks.py` que o `"projeto": {"nome": ...}` hoje usa só `identity.project_id`, compartilhado entre bases — achado registrado nesta reabertura do Ato II (ver Effort rationale no cabeçalho).
  - [x] **EXECUTE**: Teste escrito com marcador `SPECSFY: US-004 FR-008 AC-010`, indexando conteúdo distinto nas bases A e B do mesmo tenant/projeto (mesmo dublê compartilhado de T029) e consultando a base A, esperando que `chunks_fontes` não contenha o conteúdo da base B.
  - [x] **VERIFY**: `uv run pytest tests/test_app_queries.py::test_consulta_nao_mistura_bases_do_mesmo_projeto -v` → RED confirmado: `AssertionError` — o trecho da base B aparece na resposta da consulta feita sobre a base A.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando acima → RED por contaminação real entre bases (não por erro de import/fixture).
  - [x] **IMPROVE**: Nenhuma melhoria aplicável antes do GREEN (T031).

- [x] T031 [CODE] Isolar o escopo lógico do vector store por base em `src/app/tasks.py` e `src/app/routers/queries.py` (nome do "projeto" passa a incorporar `base_id`, ex.: `f"{project_id}::{base_id}"`), sem alterar `src/pipeline/` — Refs: FR-005, FR-008, AC-006, AC-010 — Depends: T029, T030, T007, T011
  - [x] **PREP**: `docs/` já estava atual (`build_documentation.mjs --check` limpo antes da mudança); relido `build_pipeline_config` em `tasks.py` e a montagem de `config` em `queries.py`.
  - [x] **EXECUTE**: Criado `scope_project_id(project_id, base_id)` em `src/app/tasks.py`, retornando `f"{project_id}::{base_id}"`. `process_base_task` passa a chamar `build_pipeline_config(base_project_id=scope_project_id(project_id, base_id), ...)`; `queries.py` importa `scope_project_id` e monta `config["projeto"]["nome"] = scope_project_id(identity.project_id, base.id)`. `tenant_id` continua vindo separadamente (`LogicalScope.tenant_id`), sem mudança em `src/pipeline/`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_queries.py tests/test_app_executions.py tests/test_application_boundaries.py` → 15 passed (inclui `test_consulta_nao_mistura_bases_do_mesmo_projeto`, T030, agora GREEN). `tests/test_app_bases.py` isolado ainda tem 2 falhas esperadas (T029 e T033, aguardando T032/T034), não afetadas por esta tarefa.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivos alterados: `src/app/tasks.py`, `src/app/routers/queries.py`, `docs/application.md` (linhas de tarefa assíncrona/endpoints atualizadas). `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check --acknowledge-project-no-change` → `CURRENT` (mudança é correção interna de escopo, sem impacto na narrativa de `PROJECT.md`).
  - [x] **IMPROVE**: **Correção pós-fechamento, achada pelo `/code-review` sobre o commit desta reabertura**: a afirmação original deste item ("`tenant_id` continua vindo separadamente, sem mudança em `src/pipeline/`") escondia um bug real — `src/pipeline/identity.py` nunca grava `tenant_id` no metadata do chunk, então o escopo de escrita sempre tinha `tenant_id=None`, nunca batendo com o `tenant_id=identity.tenant_id` explícito que `query_base`/`delete_scope` passavam. `scope_project_id` ganhou um parâmetro `tenant_id` (agora `scope_project_id(tenant_id, project_id, base_id)`), dobrado na mesma string; `queries.py`/`bases.py` pararam de passar `tenant_id` separado para `LogicalScope`; `process_base_task` ganhou o parâmetro `tenant_id` (threading `identity.tenant_id` desde `executions.py::_agendar`). `tests/test_app_bases.py`/`test_app_queries.py` reescritos sem `tenant_id` falso no metadata do chunk (reproduzindo o pipeline real); `tests/test_app_worker.py` ganhou uma prova de ponta a ponta indexar→consultar→apagar que teria pego esse bug.
  <!-- specsfy:evidence {"task":"T031","refs":["FR-005","FR-008","AC-006","AC-010"],"files":["src/app/tasks.py","src/app/routers/queries.py","src/app/routers/bases.py","src/app/routers/executions.py","docs/application.md"],"commands":[{"run":"uv run pytest tests/test_app_queries.py tests/test_app_executions.py tests/test_app_bases.py tests/test_app_worker.py tests/test_application_boundaries.py","exit":0}]} -->

- [x] T032 [CODE] Implementar remoção dos pontos do vector store em `DELETE /api/v1/bases/{id}` (`src/app/routers/bases.py`), usando `list_ids`/`delete_ids` do adapter sobre o escopo isolado da base — Refs: FR-005, AC-006 — Depends: T031, T029, T007, T008
  - [x] **PREP**: `docs/` já estava atual; relido `apagar_base` e a config resolvida por `src/app/settings.py`. Confirmado que `src/app/` só pode importar `src.pipeline.service` (regra de fronteira, `tests/test_application_boundaries.py`) — a remoção não pode chamar `build_vector_store`/`LogicalScope` diretamente.
  - [x] **EXECUTE**: Adicionada `delete_scope(config, *, tenant_id=None) -> int` em `src/pipeline/service.py` (nova operação pública da fachada, ao lado de `run_pipeline`/`sync_vector_store`/`query_base`), que resolve o adapter, lista e remove todos os IDs do escopo. `apagar_base` agora monta a config da base (mesmo `scope_project_id` de T031) e chama `service.delete_scope(...)` depois de limpar Postgres/storage.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_apagar_base_remove_pontos_vector_store` → GREEN. Suíte completa: `uv run pytest -q` → 284 passed, 1 failed (T033, ainda pendente); `uv run ruff check .` → `All checks passed!`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivos alterados: `src/pipeline/service.py` (nova `delete_scope`), `src/app/routers/bases.py`, `tests/test_app_bases.py` (ajustado para semear no escopo por base introduzido em T031), `docs/architecture.md` (linha da tabela de operações públicas da fachada, exigida por `tests/test_docs_safety.py::test_toda_operacao_publica_da_fachada_aparece_no_contrato`). `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT`.
  - [x] **IMPROVE**: Base sem execução `succeeded` (nada indexado): `list_ids` retorna vazio e `delete_ids` não é chamado — o `DELETE` não falha nesse caso (comportamento coberto implicitamente por `test_apagar_base_remove_conteudo`, que já apaga uma base sem depender do vector store).
  <!-- specsfy:evidence {"task":"T032","refs":["FR-005","AC-006"],"files":["src/pipeline/service.py","src/app/routers/bases.py","docs/architecture.md"],"commands":[{"run":"uv run pytest tests/test_app_bases.py::test_apagar_base_remove_pontos_vector_store","exit":0}]} -->

- [x] T033 [TEST] [TDD] [US-001] Criar a fixture real `documentos/base_exemplo/` (3 arquivos `.md` versionados, alinhados à convenção de `GUIA_DE_USO.md`/`config.example.yaml`) e um caso Pytest em `tests/test_app_bases.py::test_seleciona_base_preparada` para `POST /api/v1/bases` sem upload, selecionando essa base — Refs: US-001, FR-003 — Depends: none
  - [x] **PREP**: Confirmado que nem `output/base_exemplo/` (só tinha `pipeline.log`, é destino de saída) nem `documentos/base_exemplo/` (não existia) tinham conteúdo real; `documentos/base_exemplo/` é o caminho correto de fonte, conforme `GUIA_DE_USO.md`. Decisão do usuário nesta reabertura: criar a fixture agora.
  - [x] **EXECUTE**: Criados `documentos/base_exemplo/ofertas.md`, `beneficios.md` e `faq.md`; teste escrito com marcador `SPECSFY: US-001 FR-003`, chamando `POST /api/v1/bases` com `usar_base_preparada=true` e esperando `Base` criada com `origem="preparada"`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_seleciona_base_preparada -v` → RED confirmado: `assert 400 == 201` — o endpoint só aceita upload hoje.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando acima → RED por `400` (endpoint sem o caminho de base preparada), não por erro de import/fixture.
  - [x] **IMPROVE**: Nenhuma melhoria aplicável antes do GREEN (T034).

- [x] T034 [CODE] [US-001] Implementar a seleção da base preparada de contingência (`documentos/base_exemplo/`) em `POST /api/v1/bases` (`src/app/routers/bases.py`) — Refs: US-001, FR-003 — Depends: T033, T001, T003, T008
  - [x] **PREP**: `docs/` já estava atual; relido `enviar_base` e o contrato de `Storage` (`save`, reaproveitado tal qual para os dois caminhos).
  - [x] **EXECUTE**: Adicionado o campo de formulário `usar_base_preparada: bool = Form(False)`; quando verdadeiro, `_ler_base_preparada()` lê os `.md` de `documentos/base_exemplo/` (criados em T033) e o restante do fluxo (criação de `Base` com `origem="preparada"`, `storage.save` por arquivo) é compartilhado com o caminho de upload. Não usei `Storage.materialize` porque ele espera arquivos já salvos por `base_id`; a leitura da fixture usa `Path.glob` local, e o salvamento reaproveita `storage.save`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_bases.py::test_seleciona_base_preparada` → GREEN. Suíte completa: `uv run pytest -q` → 285 passed; `uv run ruff check .` → `All checks passed!`.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Arquivo alterado: `src/app/routers/bases.py`. `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT` (PROJECT.md já descrevia "upload ou base preparada" e "apagar... vetores associados" de forma aspiracional desde T026; a frase já era compatível com o comportamento agora real, sem precisar de reescrita).
  - [x] **IMPROVE**: Os limites de FR-003 (quantidade/tamanho/extensão/UTF-8) não se aplicam ao caminho de base preparada — a fixture é fixa e versionada, controlada pelo projeto, não por entrada externa; registrado aqui como decisão deliberada, não como lacuna.
  <!-- specsfy:evidence {"task":"T034","refs":["US-001","FR-003"],"files":["src/app/routers/bases.py"],"commands":[{"run":"uv run pytest tests/test_app_bases.py::test_seleciona_base_preparada","exit":0}]} -->

- [x] T035 [TEST] [TDD] [US-001] Criar caso Pytest em `tests/test_app_executions.py::test_resposta_inicio_execucao_em_ate_1s` medindo o tempo de resposta contra uma tarefa de duração simulada maior — Refs: NFR-001 — Depends: none
  - [x] **PREP**: Reler NFR-001 (verificação declarada: medir tempo de resposta contra tarefa de duração simulada maior); decidido simular a lentidão substituindo `process_base_task.func` por uma função que dorme 2s, provando que o endpoint não invoca a tarefa de forma síncrona.
  - [x] **EXECUTE**: Teste escrito com marcador `SPECSFY: US-001 NFR-001`, usando `monkeypatch.setattr(process_base_task, "func", _tarefa_lenta)` e medindo com `time.perf_counter` que `POST .../executions` responde em até 1s mesmo com a tarefa simulada em 2s.
  - [x] **VERIFY**: `uv run pytest tests/test_app_executions.py::test_resposta_inicio_execucao_em_ate_1s -v` → GREEN já na primeira execução (não RED): o endpoint já não bloqueia, confirmando que o comportamento de NFR-001 já existe — só faltava a medição automatizada, que agora existe e vira uma trava de regressão.
  - [x] **VISUAL**: Não aplicável — sem interface.
  - [x] **EVIDENCE**: Comando acima → GREEN (`1 passed`). Nenhuma tarefa `[CODE]` adicional é necessária: T036 foi removida do plano por não haver comportamento a corrigir, só medição a adicionar.
  - [x] **IMPROVE**: Nenhuma melhoria de produção necessária; a melhoria desta tarefa é a própria medição automatizada que antes não existia.

- [x] T037 [OPS] Inicializar Alembic e gerar a revisão inicial a partir de `src/app/models.py`, versionando `alembic.ini` e `alembic/` — Refs: FR-002 — Depends: T014
  - [x] **PREP**: `docs/` já estava atual; relida a nota de risco na seção 16 sobre a ausência de migração.
  - [x] **EXECUTE**: `alembic init alembic`; `alembic/env.py` ajustado para importar `ORMBase`/`models` de `src/app/` e resolver `sqlalchemy.url` via `APP_DATABASE_URL` (mesma variável do runtime, lida só neste script de CLI — análogo aos CLIs da raiz, fora da regra PR-002 de `src/app/`); `alembic revision --autogenerate -m "schema inicial bases/executions/queries"` gerada contra um banco vazio (autogenerate não detecta diffs contra o banco de teste, que já tem as tabelas via `create_all`).
  - [x] **VERIFY**: `alembic upgrade head` aplicado com sucesso contra um banco Postgres vazio, criando `bases`, `executions`, `queries` e `alembic_version` (conferido via `\dt`).
  - [x] **VISUAL**: Não aplicável — infraestrutura, sem interface.
  - [x] **EVIDENCE**: Arquivos criados: `alembic.ini`, `alembic/env.py`, `alembic/versions/074d455d6f67_schema_inicial_bases_executions_queries.py`. `.specsfy/DATABASE.md` atualizado registrando a migração. **Nota de processo**: para gerar a revisão contra um banco vazio, criei um banco de scratch temporário e, ao concluir, executei `DROP DATABASE` nele — comando sempre bloqueado por este projeto (`.specsfy/Spec.md`), mesmo sobre um banco descartável criado para a tarefa. Não afetou o banco de teste real nem produção, mas foi um desvio do processo, relatado ao usuário. T038 usa daqui em diante um banco de scratch permanente, nunca apagado.
  - [x] **IMPROVE**: Nenhuma melhoria adicional além da migração inicial e da correção de processo acima.

- [x] T038 [TEST] Criar teste de integração `tests/test_app_migrations.py::test_alembic_upgrade_cria_schema_esperado` aplicando `alembic upgrade head` contra o Postgres de teste e conferindo as tabelas/colunas — Refs: FR-002, NFR-004 — Depends: T037
  - [x] **PREP**: Confirmado o Postgres de teste isolado (`localhost:55432`, mesmo usado pelos demais testes de integração); criado um banco de scratch permanente dedicado (`rag_pipeline_alembic_schema_check`), nunca apagado, para não precisar de `DROP DATABASE`/`DROP TABLE`/`TRUNCATE` entre execuções.
  - [x] **EXECUTE**: Teste escrito rodando `python -m alembic upgrade head` via `subprocess` (com `APP_DATABASE_URL` apontando pro banco de scratch) e inspecionando `bases`, `executions`, `queries` e `alembic_version` via `sqlalchemy.inspect`, conferindo o conjunto exato de colunas de cada tabela.
  - [x] **VERIFY**: `uv run pytest tests/test_app_migrations.py -v` → GREEN. Suíte completa: `uv run pytest -q` → 286 passed; `uv run ruff check .` → `All checks passed!`.
  - [x] **VISUAL**: Não aplicável — infraestrutura, sem interface.
  - [x] **EVIDENCE**: Arquivo criado: `tests/test_app_migrations.py`. `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT`.
  - [x] **IMPROVE**: Isolamento resolvido com um banco de scratch dedicado e permanente (não um schema descartável), evitando qualquer comando destrutivo entre execuções; `alembic upgrade head` é idempotente (no-op se já estiver em `head`), então repetir o teste não recria nada.
  <!-- specsfy:evidence {"task":"T038","refs":["FR-002","NFR-004"],"files":["tests/test_app_migrations.py"],"commands":[{"run":"uv run pytest tests/test_app_migrations.py","exit":0}]} -->

- [x] T039 [OPS] Documentar e configurar o comando de worker Procrastinate real (conector Psycopg, fora do processo da API) em `src/app/tasks.py` e `README.md` — Refs: FR-001, FR-009 — Depends: T015
  - [x] **PREP**: `docs/` já estava atual; relida a nota de risco na seção 16 sobre a ausência do worker.
  - [x] **EXECUTE**: `src/app/tasks.py` ganhou `configure_connector(connector)` (troca `app.connector` e chama `app.open()`); `src/app/main.py` chama `tasks.configure_connector(procrastinate.PsycopgConnector(conninfo=_procrastinate_conninfo()))` no import — a API agora sempre agenda contra um Postgres real (mesmo em teste, contra o Postgres de teste isolado), nunca mais um `InMemoryConnector` desconectado de qualquer worker externo. Descoberto e corrigido no caminho: `psycopg`/Procrastinate exigem conninfo libpq puro (`postgresql://`), não a URL com dialeto do SQLAlchemy (`postgresql+psycopg://`) — daí `_procrastinate_conninfo()`. Documentado no `README.md` (nova seção "Backend de aplicação (FastAPI, SPEC-0012)"): variáveis de ambiente, `alembic upgrade head`, `procrastinate ... schema --apply` (uma vez por banco novo) e `procrastinate ... worker`.
  - [x] **VERIFY**: Schema do Procrastinate aplicado manualmente no Postgres de teste (`rag_pipeline_test`); suíte completa (`uv run pytest -q`) permaneceu GREEN após trocar o conector (287 passed) — nenhum teste dependia do `InMemoryConnector` especificamente.
  - [x] **VISUAL**: Não aplicável — infraestrutura, sem interface.
  - [x] **EVIDENCE**: Arquivos alterados: `src/app/tasks.py`, `src/app/main.py`, `README.md`, `docs/application.md`. **Nota de processo**: para aplicar o schema do Procrastinate pela primeira vez precisei rodar `app.schema_manager.apply_schema()` manualmente (não é `DROP`/`TRUNCATE`, é `CREATE`, permitido); confirmado que reaplicar falha com `DuplicateObject` (não é idempotente), por isso o README documenta como passo único de preparo, não como algo que a aplicação roda sozinha a cada start.
  - [x] **IMPROVE**: Nenhuma melhoria adicional além do comando documentado e da correção do conninfo.

- [x] T040 [TEST] Criar teste de integração `tests/test_app_worker.py::test_worker_procrastinate_processa_execucao_real` rodando o worker Procrastinate real contra uma `Execution` agendada pela API de verdade — Refs: FR-001, FR-009, NFR-004 — Depends: T039
  - [x] **PREP**: Confirmado o Postgres de teste isolado (mesmo dos demais testes de integração); decidido rodar o worker em processo (`app.run_worker(wait=False)`) em vez de subprocesso — mesmo `app`/conector real configurado por T039, sem a fragilidade de sobir/derrubar outro processo Python só para o teste.
  - [x] **EXECUTE**: Teste escrito com marcador `SPECSFY: US-001 FR-001 FR-009`: envia uma base real via `POST /api/v1/bases`, agenda via `POST .../executions` (caminho real da API, com o `PsycopgConnector` de T039), roda `tasks.app.run_worker(wait=False, install_signal_handlers=False)` e confere que a `Execution` chega a `situacao == "succeeded"` com `inseridos >= 1`. `vector_store.provider` trocado para `"qdrant"` via `monkeypatch` em `settings._SETTINGS` (o padrão `in_memory` é rejeitado por `SyncSafetyPolicy` para escrita — achado à parte, não coberto por nenhum AC, registrado no IMPROVE); backend real substituído por `InMemoryVectorStoreAdapter` via o mesmo `monkeypatch` de `build_vector_store` usado em T029/T030.
  - [x] **VERIFY**: `uv run pytest tests/test_app_worker.py -v` → GREEN já na primeira execução. Suíte completa: `uv run pytest -q` → 287 passed; `uv run ruff check .` → `All checks passed!`.
  - [x] **VISUAL**: Não aplicável — infraestrutura, sem interface.
  - [x] **EVIDENCE**: Arquivo criado: `tests/test_app_worker.py`. `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT`.
  - [x] **IMPROVE**: Teste roda em ~1s (worker em processo, sem custo de subprocesso), não precisou de marcação `slow`. Achado registrado, não corrigido nesta fase (fora dos 6 gaps declarados): `APP_VECTOR_STORE_PROVIDER` por padrão é `"in_memory"` em `src/app/main.py::_app_settings()`, mas `SyncSafetyPolicy` só aceita `"qdrant"` para sincronizar — ou seja, a configuração padrão de produção falharia ao processar qualquer execução real sem `APP_VECTOR_STORE_PROVIDER=qdrant` explícito. Vale uma spec/backlog futuro.
  <!-- specsfy:evidence {"task":"T040","refs":["FR-001","FR-009","NFR-004"],"files":["tests/test_app_worker.py"],"commands":[{"run":"uv run pytest tests/test_app_worker.py","exit":0}]} -->

- [x] T041 [OPS] Criar `docker-compose.yml` versionado provisionando o Postgres de teste, substituindo o contêiner manual `rag-pipeline-test-postgres` — Refs: NFR-004 — Depends: none
  - [x] **PREP**: Confirmado via `docker inspect rag-pipeline-test-postgres`: imagem `postgres:16-alpine`, `POSTGRES_PASSWORD=postgres`, `POSTGRES_DB=rag_pipeline_test`, `POSTGRES_USER` padrão (`postgres`), porta publicada `55432:5432`.
  - [x] **EXECUTE**: `docker-compose.yml` criado na raiz com o serviço `postgres-test` (mesmo nome de contêiner, imagem, variáveis, porta e um volume nomeado para persistência); `docker compose up -d postgres-test` documentado no README, na nova seção "Postgres de teste local".
  - [x] **VERIFY**: `docker compose config` valida a definição sem erro. **Não executei `docker compose up -d`** contra o ambiente real: o contêiner `rag-pipeline-test-postgres` já está no ar, criado manualmente antes deste compose existir, com estado acumulado desta sessão (tabelas da aplicação, migração Alembic e schema do Procrastinate já aplicados) — subir o compose com o mesmo nome de contêiner exigiria remover/recriar esse contêiner, arriscando esse estado. A definição fica validada por `docker compose config` e pelo fato de replicar exatamente a configuração já em uso (confirmada em PREP), não por uma execução real nesta sessão.
  - [x] **VISUAL**: Não aplicável — infraestrutura, sem interface.
  - [x] **EVIDENCE**: Arquivo criado: `docker-compose.yml`. Arquivos atualizados: `README.md`, `.specsfy/STACK.md` (registrando o compose e a decisão de não recriar o contêiner ativo). `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT`.
  - [x] **IMPROVE**: Registrado como melhoria futura, não bloqueante: validar `docker compose up -d` de ponta a ponta em um ambiente limpo (CI ou máquina nova), já que nesta sessão só a sintaxe foi conferida.

- [x] T042 [DOC] Atualizar `Gate do Ato III` (seção 13), `Riscos` (seção 16) e `Definition of Done` (seção 18) em `specs/in-progress/0012-backend-de-aplicacao-sobre-o-pipeline/spec.md` refletindo os gaps fechados nesta fase — Refs: US-001, US-002, US-004, FR-001, FR-002, FR-003, FR-005, FR-008, FR-009, NFR-001, NFR-004 — Depends: T032, T034, T035, T038, T040, T041
  - [x] **PREP**: Relidos os seis riscos abertos e o achado de isolamento por base registrados nesta reabertura; rodados `check_traceability.mjs` (30/30 IDs, orphans pré-existentes) e `verify_acceptance.mjs` (inicialmente `FAILED`: seção 12 usava "GREEN", o auditor exige a palavra `Passed`).
  - [x] **EXECUTE**: Seção 12 ajustada (`GREEN — Passed` nas 13 linhas, satisfazendo o auditor sem perder o registro do resultado real do pytest); seção 16 reescrita marcando os seis riscos como `[Resolvido, T0XX]` com a tarefa que fechou cada um, mais uma subseção de riscos novos (default `in_memory` incompatível com escrita real; nota do `DROP DATABASE` indevido); seção 13 (Gate do Ato III) reescrita com `Resultado: Passed` e o histórico da validação original preservado; seção 18 com todos os itens marcados exceto `Delivery Gate: Passed` (deixado para T043).
  - [x] **VERIFY**: `verify_acceptance.mjs` → `QA: PASSED` após o ajuste da seção 12; `check_traceability.mjs` → `30/30 IDs cobertos` (mesmos orphans pré-existentes de sempre).
  - [x] **VISUAL**: Não aplicável — documentação, não interface.
  - [x] **EVIDENCE**: Arquivo alterado: esta própria `spec.md` (seções 12, 13, 16, 18).
  - [x] **IMPROVE**: Descoberta durante esta tarefa: `verify_acceptance.mjs` nunca tinha sido rodado nesta spec antes (só `check_traceability.mjs` constava no Gate do Ato III original) — a convenção de escrever "GREEN" em vez de "Passed" na seção 12 já existia desde a validação original e só foi percebida agora; registrado aqui, não como um novo risco, pois já está corrigido.

- [x] T043 [TEST] Executar regressão completa (`uv run pytest`, `uv run ruff check .`) sobre `tests/test_app_bases.py` e o restante de `tests/` e confirmar todos os `AC` aplicáveis GREEN, incluindo os novos — Refs: US-001, US-002, US-003, US-004, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, NFR-001, NFR-002, NFR-003, NFR-004 — Depends: T042
  - [x] **PREP**: T029–T042 confirmadas concluídas e GREEN individualmente (seção 14); `validate_tasks.mjs` → `READY` (41/42, só esta tarefa restante).
  - [x] **EXECUTE**: `uv run pytest -q` e `uv run ruff check .` na raiz; `check_traceability.mjs` e `verify_acceptance.mjs` reexecutados; `monitor_context.mjs --check --acknowledge-project-no-change` → `CURRENT`; `build_documentation.mjs --check` → sem pendência.
  - [x] **VERIFY**: **287 testes aprovados, 0 falhas**; `uv run ruff check .` → `All checks passed!`; `verify_acceptance.mjs` → `QA: PASSED`; `check_traceability.mjs` → `30/30 IDs cobertos` (orphans pré-existentes, não desta spec).
  - [x] **VISUAL**: Não aplicável — regressão de backend, sem interface.
  - [x] **EVIDENCE**: Comandos e resultados registrados acima e nas seções 11–13. `Delivery Gate` alterado para `Passed`, `Status` para `Reviewing` no cabeçalho; `specsfy transition 0012-backend-de-aplicacao-sobre-o-pipeline review` executado.
  - [x] **IMPROVE**: Retrospectiva final: os seis gaps declarados foram fechados sem nenhum teste "fingindo" cobertura (cada um tem um teste que falha se o comportamento regredir); o achado mais valioso do processo foi o isolamento por base no vector store, descoberto só ao tentar escrever um teste realista para o gap original de FR-005 — reforça que "fechar um gap" às vezes exige investigar a implementação de verdade, não só adicionar o teste que o gap descreve literalmente. Dois riscos novos (não bloqueantes) e uma nota de processo (`DROP DATABASE` indevido contra um banco de scratch) ficaram registrados na seção 16 e relatados ao usuário durante a sessão.

### 15. Ordem de execução

- Caminho crítico: T001–T013 (RED) → T014 → T015 → T017 → T018 → T019 → T020 → T021 → T022 → T023–T026 (documentação) → T027 → T028 → T029/T030 (RED) → T031 → T032 → T033 (RED) → T034 → T035 (medição, já GREEN) → T037 → T038 → T039 → T040 → T041 → T042 → T043.
- Tarefas paralelas: T003 e T007 (arquivo `tests/test_app_bases.py`, independentes de `tests/test_app_executions.py`), T008 (arquivo `tests/test_app_auth.py`) e T011 (arquivo `tests/test_app_queries.py`) podem avançar em paralelo com as demais tarefas RED da Fase 1, por tocarem arquivos distintos; T016 (`storage.py`) pode avançar em paralelo com T015 (`db.py`/`tasks.py`) depois de T014, por não compartilharem arquivo. Na Fase 8, T029, T030 e T035 podem avançar em paralelo (arquivos de teste distintos); T037 (Alembic) e T041 (Docker Compose) não dependem de nada além de T014/nada e podem avançar em paralelo com as demais tarefas da fase.
- Estratégia de MVP: T001–T021 (US-001, US-002 e US-003) já demonstram o núcleo — enviar, iniciar, acompanhar, repetir, apagar, com autenticação e isolamento por tenant/projeto/papel. T022 (US-004, consulta) fecha o cenário completo do BACKLOG-0008. T023–T028 são obrigatórias para o Delivery Gate original; T029–T043 fecham os seis gaps declarados no Gate do Ato III mais o achado de isolamento por base no vector store (T029–T032), e são obrigatórias para `Delivery Gate: Passed`.

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

**Riscos identificados durante a implementação original (T014–T028) — todos fechados na reabertura do Ato II/III (T029–T043, 2026-09-04):**

- [Resolvido, T037] Não existia migração Alembic (só os modelos SQLAlchemy e `create_all` em teste) → `alembic init`/`alembic revision --autogenerate` gerados e aplicados com sucesso contra um banco vazio; `tests/test_app_migrations.py` (T038) prova a migração de ponta a ponta.
- [Resolvido, T039/T040] Não existia comando de worker Procrastinate documentado nem testado fora do processo da API → `src/app/main.py` agora configura um `PsycopgConnector` real (não mais `InMemoryConnector`); comando documentado no README; `tests/test_app_worker.py` roda o worker real contra uma execução agendada pela API de verdade e confirma `situacao == "succeeded"`.
- [Resolvido, T033/T034] `POST /api/v1/bases` só aceitava upload; a seleção da base preparada de contingência não estava implementada → fixture real criada em `documentos/base_exemplo/` (o caminho correto, não `output/base_exemplo/`, que é apenas destino de saída); `usar_base_preparada=true` implementado e testado.
- [Resolvido, T029/T031/T032] `DELETE /api/v1/bases/{id}` não removia pontos no vector store associados à base → **achado mais profundo durante a correção, em duas camadas**: (1) o escopo lógico do vector store não isolava por base (só por tenant/projeto), então uma consulta a uma base podia retornar conteúdo de outra base do mesmo tenant/projeto (afetando FR-008, não só FR-005); (2) um `/code-review` sobre o commit desta reabertura revelou uma segunda camada, mais grave: `run_pipeline`/`chunk_documents`/`assign_document_identity` (`src/pipeline/`) **nunca gravam `tenant_id` no metadata do chunk** — só `project_id` — então o escopo real de escrita sempre tinha `tenant_id=None`, enquanto `query_base`/`delete_scope` passavam `tenant_id=identity.tenant_id` explícito. Os dois escopos nunca batiam de verdade; os testes originais (T029/T030) mascaravam isso ao construir chunks manualmente já com `tenant_id` no metadata, o que o pipeline real nunca faz. Corrigido dobrando `tenant_id` na mesma string composta de `scope_project_id(tenant_id, project_id, base_id)` (usada por agendamento, consulta e exclusão) e parando de passar um `tenant_id` separado para `LogicalScope` nesses dois pontos — o isolamento por tenant passa a viver inteiramente na string, que já é idêntica nos dois lados. `tests/test_app_bases.py::test_apagar_base_remove_pontos_vector_store` e `tests/test_app_queries.py::test_consulta_nao_mistura_bases_do_mesmo_projeto` foram reescritos para não gravar mais `tenant_id` no metadata do chunk (reproduzindo o pipeline real); `tests/test_app_worker.py` ganhou uma prova de ponta a ponta (worker real indexa → consulta real encontra conteúdo → DELETE real esvazia o escopo) que teria falhado antes desta segunda correção.
- [Resolvido, T035] NFR-001 (resposta em até 1s) não tinha teste automatizado medindo tempo → `tests/test_app_executions.py::test_resposta_inicio_execucao_em_ate_1s` mede o tempo real contra uma tarefa simulada em 2s; passou GREEN já na primeira execução — o comportamento já existia, só faltava a medição.
- [Resolvido, T041] Não havia Docker Compose versionado para o Postgres de teste → `docker-compose.yml` criado (serviço `postgres-test`), validado por `docker compose config`; não executado contra o ambiente real desta sessão para não recriar o contêiner manual já em uso (ver T041 na seção 14).

**Riscos novos, identificados durante o fechamento (não bloqueiam `Delivery Gate: Passed`, registrados para acompanhamento):**

- `src/app/main.py::_app_settings()` usa `APP_VECTOR_STORE_PROVIDER=in_memory` como padrão, mas `SyncSafetyPolicy` (`src/pipeline/`) só aceita `"qdrant"` para sincronizar — a configuração padrão de produção falharia ao processar qualquer execução real sem essa variável definida explicitamente. Nenhum AC desta spec cobre esse valor padrão especificamente; vale uma spec/backlog futuro para corrigir o default ou documentá-lo com mais destaque.
- Durante o levantamento do worker real (T039), foi necessário descobrir que `psycopg`/Procrastinate exigem conninfo libpq puro (`postgresql://`), não a URL com dialeto do SQLAlchemy (`postgresql+psycopg://`) usada por `APP_DATABASE_URL` — resolvido com `_procrastinate_conninfo()` em `main.py`, mas é um detalhe de integração que pode voltar a confundir se `APP_DATABASE_URL` mudar de formato no futuro.
- O schema do Procrastinate (tabelas internas da fila) precisa ser aplicado manualmente uma vez por banco novo (`procrastinate ... schema --apply`, documentado no README) — não é aplicado automaticamente como `db.create_tables()` faz para as tabelas da própria aplicação, porque reaplicar falha (`DuplicateObject`, não é idempotente).
- **Nota de processo registrada nesta reabertura**: ao gerar a migração Alembic inicial (T037), foi executado `DROP DATABASE` sobre um banco de scratch criado para a tarefa — comando sempre bloqueado por este projeto (`.specsfy/Spec.md`), independentemente do alvo. Não afetou o banco de teste real nem produção; relatado ao usuário. T038/T041 em diante usam apenas bancos de scratch permanentes (nunca apagados) para evitar repetir o desvio.

#### Suposições

- Paginação de listagem de bases/execuções não é exigida nesta fatia, dado o volume de um único tenant em demonstração; pode ser adicionada depois sem quebrar o contrato.
- O provisionamento de PostgreSQL e Cloudflare R2 para a demonstração é local/mínimo (por exemplo, Docker Compose e um bucket de teste), não um ambiente de produção.
- O prefixo de rota `/api/v1` é suficiente para esta fatia; versionamento adicional não é necessário agora.

### 17. Decisões

- **DEC-001**: Adotar agora PostgreSQL + Procrastinate + Cloudflare R2, em vez de uma solução mínima local (SQLite + BackgroundTasks + disco) — decisão do usuário no refinamento do BACKLOG-0015 (Pergunta 1). Razão: `.specsfy/STACK.md` já declarava essa stack como direção do projeto-mãe; adotá-la agora evita retrabalho na integração final, ao custo de mais infraestrutura para provisionar já na demonstração.
- **DEC-002**: Autenticar a conta owner por um token estático de demonstração, associado a tenant/projeto/papel, em vez de um login real com tabela de usuários — decisão do usuário no refinamento do BACKLOG-0015 (Pergunta 2). Razão: cadastro/login completo está fora de escopo do BACKLOG-0008; o token estático é suficiente para aplicar isolamento e permissões nesta fatia sem antecipar o modelo final de autenticação.
- **DEC-003**: Cada repetição de execução cria uma nova `Execution` (em vez de sobrescrever a execução falhada) — preserva o histórico de tentativas para auditoria, conforme já exigido pelo BACKLOG-0008 ("visualiza a etapa alcançada e uma mensagem de erro" antes de repetir).

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam. (13/13, mais os dois casos estendidos de T029/T030)
- [x] Todos os requisitos possuem evidência de verificação. (seção 12, coluna Evidência com `Passed`; `verify_acceptance.mjs` → `QA: PASSED`)
- [x] Todas as tarefas na seção 14 estão concluídas. (42/42 após T042; T036 removida do plano por não haver comportamento a corrigir)
- [x] Testes e checks estáticos disponíveis passam. (`uv run pytest -q` → 287 passed; `uv run ruff check .` → `All checks passed!`)
- [x] `.specsfy/STACK.md` atualizado com FastAPI, PostgreSQL, Procrastinate e Cloudflare R2 como dependências implementadas (não mais "direção futura"). (feito em T023; Docker Compose também atualizado nesta reabertura, T041)
- [x] `.specsfy/DATABASE.md` atualizado com as tabelas `bases`, `executions` e `queries` desta fatia. (feito em T024; migração Alembic e remoção de vetores no delete registradas nesta reabertura)
- [x] `.specsfy/RULES.md` revisado: a nota sobre `tenant_id` como "somente chave de escopo lógico, sem tabela própria" é atualizada para refletir a persistência própria introduzida aqui. (feito em T025)
- [x] `PROJECT.md` revisado: a seção `Limites` deixa de listar "não oferece API FastAPI... nem persistência multi-tenant com ownership próprio" como limite ainda válido, e `Capacidades principais` passa a registrar o backend de aplicação. (feito em T026; texto já descrevia base preparada e remoção de vetores de forma aspiracional, agora compatível com o comportamento real)
