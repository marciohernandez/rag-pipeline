# Especificação integrada: Chat com assistente especialista em RAG e no pipeline

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0021 |
| Slug | 0021-chat-assistente-especialista-rag-pipeline |
| Status | Complete |
| Effort | 7 |
| Effort updated at | 2026-09-24 |
| Effort rationale | Entrega de ponta a ponta com nova orquestração LangGraph, contrato neutro de LLM, persistência nova (duas tabelas e migration), indexação da documentação viva em coleção dedicada, isolamento por pessoa e tenant e um painel React global com requisitos de acessibilidade; sem segurança transversal como na SPEC-0020. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-09-24 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

Quem usa o sistema decide splitter, tamanho de chunk, overlap e estratégia de indexação sem orientação: as configurações existem apenas em config global e frontmatter, e a única conversa com LLM hoje é o `chat.py`, uma CLI que responde sobre o conteúdo já indexado de uma Base, não sobre como processar documentos. A origem é o backlog `specs/backlog/0022-chat-com-assistente-llm-para-ajudar-no-uso-do-sistema.md` (BACKLOG-0022), cuja ideia original pede um sistema com IA integrada de ponta a ponta; a pessoa usuária corrigiu o escopo em 2026-09-18 para um especialista em RAG e em cada etapa do processo do pipeline, não um assistente aberto a qualquer tema nem um guia de navegação.

#### Resultado desejado

Uma pessoa autenticada, em qualquer tela, abre um chat, pergunta "qual a melhor forma de processar os documentos que tenho?" ou "text splitter ou markdown splitter para ter um melhor RAG?" e recebe uma orientação ancorada na documentação viva do produto. Quando aponta uma Base existente, a orientação considera o conteúdo real dela. O assistente apenas orienta: nenhuma Base, Workspace, execução ou configuração é criada, alterada ou apagada por ele.

#### Métricas de sucesso

- Os 29 cenários AC desta spec passam em Pytest e Vitest, com RED observado antes da implementação.
- Cada resposta que usou trechos recuperados devolve ao menos uma fonte citada; resposta sem suporte na documentação admite a lacuna (verificado por AC-008 e AC-009).
- Da abertura de qualquer tela autenticada até uma pergunta enviada bastam duas interações: acionar o botão do assistente e enviar a mensagem.
- Zero escrita fora das tabelas do assistente em qualquer turno (AC-017).

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: como o repositório já integra LLM e recuperação → `chat.py` usa `ChatOpenAI` via OpenRouter com `LLM_MODEL` e `OPENROUTER_API_KEY`, e `src/pipeline/service.py` expõe `query_base`; a regra do projeto confina `ChatOpenAI` a `chat.py` como exceção temporária rastreada pelo BACKLOG-0010, portanto usar LLM em `src/app` exige um contrato neutro em `src/pipeline/providers/`.
- **R-002**: como o backend escopa dados por identidade → SPEC-0020 entregou `Identity` (pessoa, tenant, projeto, papel), `repo.get_base_or_404` e autoria por `criado_por`; conversas seguem o mesmo escopo, com a pessoa como dona.
- **R-003**: como o frontend hospeda telas globais → `frontend/src/app/(autenticado)/layout.tsx` é o shell único das telas autenticadas e já tem `Sheet`, `Dialog`, `Skeleton`, `Badge` e o cliente HTTP `frontend/src/lib/api-client.ts`; `Textarea` e `Select` não estão instalados.

#### Fontes e contexto consultados

- `specs/backlog/0022-chat-com-assistente-llm-para-ajudar-no-uso-do-sistema.md`, `specs/backlog/0010-provider-llm-plugavel.md`, `specs/backlog/0025-expor-configuracoes-de-ingestao-na-interface.md`.
- `chat.py`, `src/pipeline/service.py`, `src/pipeline/providers/contracts.py`, `src/pipeline/providers/factory.py`, `src/app/auth.py`, `src/app/repo.py`, `src/app/models.py`, `src/app/routers/queries.py`, `src/app/settings.py`.
- `frontend/src/app/(autenticado)/layout.tsx`, `frontend/src/components/`, `INTERFACE.md`, `DESIGNSYSTEM.MD`, `.specsfy/STACK.md`, `.specsfy/DATABASE.md`, `.specsfy/RULES.md`, `specs/completed/0020-autenticacao-real-por-pessoa/spec.md`.

#### Documentação consultada

- Definição: nenhuma documentação externa consultada.
- Implementação (2026-09-24, T037): docs do LangGraph v1+ (`docs.langchain.com/oss/python/langgraph/use-graph-api#conditional-branching` e `graph-api`) sobre `StateGraph`, `add_conditional_edges`, `START`/`END` e `compile().invoke`, consultadas pelo servidor MCP de docs da LangChain antes de escrever `src/pipeline/assistant.py`.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: a spec cobre só a fatia 1 (chat, histórico, memória de curto prazo) ou também a memória de longo prazo, agora que a autenticação por pessoa existe? → **A**: opção 1 escolhida pela pessoa: somente a fatia 1; a memória de longo prazo vira item de backlog próprio.
- **Q**: qual provedor de LLM? → **A**: decisão reversível assumida: reusar OpenRouter, como `chat.py`, atrás de um contrato neutro novo; o restante do BACKLOG-0010 (segundo provedor, migração do `chat.py`) permanece fora.
- **Q**: quais papéis usam o assistente? → **A**: decisão reversível assumida: owner, admin e member, porque o assistente só orienta e não executa ações.

#### Dúvidas abertas

- Nenhuma bloqueante. As suposições reversíveis estão na seção 16.

### 3. Escopo e atores

#### Incluído

- Botão global e painel lateral do assistente em todas as telas autenticadas, com nova conversa, histórico, retomada e exclusão de conversa.
- Conversa sobre estratégia de RAG e do pipeline, com memória de curto prazo (20 mensagens da mesma conversa).
- Conhecimento do produto por RAG sobre a documentação viva, com comando de indexação e fontes citadas.
- Análise opcional de uma Base do escopo da pessoa, com trechos reais no contexto.
- Contrato neutro de chat em `src/pipeline/providers/`, adapter OpenRouter e factory, e orquestração com LangGraph.
- Persistência de conversas e mensagens por pessoa, com migration.

#### Fora de escopo

- Memória de longo prazo entre conversas e a tela para ver e apagar itens de memória (fatia 2, backlog próprio a criar).
- Qualquer ação do assistente sobre o sistema: criar, alterar ou apagar Workspace, Base, execução ou configuração.
- Segundo provedor de LLM, migração do `chat.py` para o contrato neutro e o restante do BACKLOG-0010.
- Resposta em streaming, anexos de arquivo na conversa, compartilhamento de conversas entre pessoas e busca no histórico.
- Limite de taxa por pessoa e controle de custo por token.

#### Atores

- **Pessoa autenticada (owner, admin ou member)**: conversa com o assistente, gerencia as próprias conversas e pode apontar Bases do próprio escopo.
- **Assistente**: componente do sistema que responde por LLM; não tem ferramentas nem permissão de escrita.
- **Operador**: quem executa o comando de indexação da documentação e configura o provedor de LLM.

### 4. Princípios e restrições do projeto

- **PR-001**: nova orquestração de IA usa LangGraph v1+ e componentes LangChain v1+ (`.specsfy/RULES.md`).
- **PR-002**: imports de SDK de modelo ficam confinados a `src/pipeline/providers/`; `src/app` depende somente de `src.pipeline.service`; `src/pipeline` não importa `src.app` (verificado por `tests/test_provider_boundaries.py` e `tests/test_application_boundaries.py`).
- **PR-003**: nenhum segredo é versionado, logado ou devolvido em erro; a chave do provedor vem do ambiente.
- **PR-004**: a documentação de dados é mantida à mão em `.specsfy/DATABASE.md`; as duas tabelas novas exigem atualização manual e revisão de `docs/`.
- **PR-005**: testes nunca usam o banco de desenvolvimento; a migration é aplicada só no banco de teste (`rag_pipeline_test`) e nenhum comando destrutivo é executado.
- **PR-006**: cada caso de teste deriva do BDD desta spec e declara o próprio marcador `SPECSFY: SPEC-0021 <IDs>`; RED válido antes de qualquer implementação.
- **PR-007**: interface segue `DESIGNSYSTEM.MD` e `INTERFACE.md`, reaproveita os blocos existentes e registra cada bloco novo em `INTERFACE.md`.

### 5. Histórias de usuário

#### US-001 — Conversar com o assistente em qualquer tela (P1)

Como uma pessoa autenticada (owner, admin ou member), quero abrir o assistente a partir de qualquer tela e conversar livremente sobre RAG e o pipeline, para tirar dúvidas de estratégia sem sair do que estou fazendo.

**Por que P1**: Sem o assistente, a pessoa decide splitter, tamanho de chunk e overlap às cegas; é o núcleo do valor.
**Teste independente**: Abrir o painel em uma tela qualquer, enviar uma pergunta e receber uma resposta persistida.
**Requisitos**: FR-001, FR-003, FR-009, FR-010, NFR-002, NFR-003

#### US-002 — Manter histórico e iniciar novas conversas (P1)

Como uma pessoa autenticada, quero iniciar uma nova conversa, ver as conversas anteriores, retomá-las e apagá-las, para organizar minhas consultas por assunto e recuperar o que já foi orientado.

**Por que P1**: Sem histórico a pessoa perde a orientação a cada fechamento do painel.
**Teste independente**: Criar duas conversas, listar, reabrir a primeira e apagar a segunda.
**Requisitos**: FR-001, FR-002, FR-003

#### US-003 — Receber respostas ancoradas na documentação do produto (P1)

Como uma pessoa que usa o sistema, quero que o assistente responda sobre o que o sistema faz com base na documentação viva e cite a fonte, para confiar que ele não inventa recursos inexistentes.

**Por que P1**: Resposta inventada sobre o produto destrói a confiança no assistente inteiro.
**Teste independente**: Perguntar sobre uma etapa do pipeline descrita em docs/ e verificar trecho e fonte; perguntar sobre um recurso inexistente e verificar a admissão da lacuna.
**Requisitos**: FR-005, FR-006, FR-008, FR-011

#### US-004 — Analisar uma Base existente antes de recomendar (P2)

Como uma pessoa que já enviou documentos, quero apontar uma Base minha para o assistente analisar o conteúdo real antes de recomendar splitter e chunking, para receber uma recomendação que considera meus documentos e não apenas uma descrição minha.

**Por que P2**: Aprofunda a orientação, mas a conversa livre (US-001) já entrega valor sem ela.
**Teste independente**: Apontar uma Base com execução concluída e verificar que trechos reais compõem o contexto; apontar uma Base de outro escopo e verificar o 404.
**Requisitos**: FR-007, FR-008

#### US-005 — Manter o fio da conversa (P2)

Como uma pessoa em uma conversa longa, quero fazer perguntas de continuação que dependem do que já disse, para não precisar repetir o contexto a cada mensagem.

**Por que P2**: Melhora a fluidez; a memória de longo prazo entre conversas fica na fatia seguinte.
**Teste independente**: Descrever os documentos, perguntar "e o overlap ideal?" e verificar que o contexto inclui a descrição anterior.
**Requisitos**: FR-003, FR-004

### 6. Cenários BDD de aceite

#### AC-001 — Assistente disponível em qualquer tela autenticada

**Cobre**: US-001, FR-001, FR-009

```gherkin
@US-001 @FR-001 @FR-009 @AC-001
Feature: Assistente disponível em qualquer tela autenticada

  Scenario: Assistente disponível em qualquer tela autenticada
    Given uma pessoa autenticada em qualquer tela do shell (Workspaces, detalhe da Base ou Pessoas)
    When ela aciona o botão do assistente
    Then o painel do assistente abre sobre a tela atual sem trocar de rota e mostra o campo de mensagem
```

#### AC-002 — Mensagem enviada recebe resposta persistida

**Cobre**: US-001, FR-003, FR-009

```gherkin
@US-001 @FR-003 @FR-009 @AC-002
Feature: Mensagem enviada recebe resposta persistida

  Scenario: Mensagem enviada recebe resposta persistida
    Given uma pessoa autenticada com uma conversa aberta e um modelo de linguagem de teste que responde texto fixo
    When ela envia a pergunta "qual splitter usar para manuais em Markdown?"
    Then a resposta do assistente é devolvida e a pergunta e a resposta ficam gravadas na conversa, na ordem
```

#### AC-003 — Falha do provedor preserva o texto e não grava o par

**Cobre**: US-001, FR-003, FR-010, NFR-002

```gherkin
@US-001 @FR-003 @FR-010 @NFR-002 @AC-003
Feature: Falha do provedor preserva o texto e não grava o par

  Scenario: Falha do provedor preserva o texto e não grava o par
    Given uma conversa aberta e um provedor de linguagem que falha com um detalhe interno
    When a pessoa envia uma mensagem
    Then a API devolve 502 com mensagem genérica sem o detalhe do provedor, nenhuma mensagem nova é gravada e o painel mantém o texto digitado para reenvio
```

#### AC-004 — Sem sessão não há assistente

**Cobre**: US-001, FR-001, FR-009, NFR-001

```gherkin
@US-001 @FR-001 @FR-009 @NFR-001 @AC-004
Feature: Sem sessão não há assistente

  Scenario: Sem sessão não há assistente
    Given uma requisição sem sessão válida, ou a tela de login
    When ela chama qualquer endpoint do assistente ou abre o login
    Then a API responde 401 sem revelar dados e o login não exibe o botão do assistente
```

#### AC-005 — Histórico lista só as conversas da própria pessoa

**Cobre**: US-002, FR-002, NFR-001

```gherkin
@US-002 @FR-002 @NFR-001 @AC-005
Feature: Histórico lista só as conversas da própria pessoa

  Scenario: Histórico lista só as conversas da própria pessoa
    Given duas pessoas do mesmo tenant e projeto, cada uma com conversas próprias
    When uma delas lista o histórico
    Then ela vê apenas as próprias conversas, da mais recente para a mais antiga, com título e data
```

#### AC-006 — Nova conversa e retomada de conversa anterior

**Cobre**: US-002, FR-001, FR-002, FR-003

```gherkin
@US-002 @FR-001 @FR-002 @FR-003 @AC-006
Feature: Nova conversa e retomada de conversa anterior

  Scenario: Nova conversa e retomada de conversa anterior
    Given uma pessoa com uma conversa antiga no histórico
    When ela inicia uma nova conversa, envia a primeira mensagem e depois reabre a conversa antiga pelo histórico
    Then a nova conversa recebe como título o início da primeira mensagem e a conversa antiga reaparece com todas as suas mensagens
```

#### AC-007 — Apagar conversa exige confirmação e respeita a autoria

**Cobre**: US-002, FR-002, NFR-001

```gherkin
@US-002 @FR-002 @NFR-001 @AC-007
Feature: Apagar conversa exige confirmação e respeita a autoria

  Scenario: Apagar conversa exige confirmação e respeita a autoria
    Given uma conversa de uma pessoa e um owner do mesmo tenant
    When o owner tenta abrir ou apagar a conversa, e depois a autora a apaga
    Then o owner recebe 404 sem revelar a existência da conversa e, quando a autora confirma, a conversa e suas mensagens deixam de existir
```

#### AC-008 — Resposta ancorada na documentação do produto com fontes

**Cobre**: US-003, FR-005, FR-006

```gherkin
@US-003 @FR-005 @FR-006 @AC-008
Feature: Resposta ancorada na documentação do produto com fontes

  Scenario: Resposta ancorada na documentação do produto com fontes
    Given a coleção de conhecimento do produto com um trecho de docs/architecture.md sobre o fluxo de ingestão
    When a pessoa pergunta como o sistema processa um documento
    Then o prompt enviado ao modelo contém o trecho recuperado e a resposta devolve o arquivo de origem como fonte
```

#### AC-009 — Sem suporte na documentação o assistente admite e não inventa

**Cobre**: US-003, FR-005, FR-006

```gherkin
@US-003 @FR-005 @FR-006 @AC-009
Feature: Sem suporte na documentação o assistente admite e não inventa

  Scenario: Sem suporte na documentação o assistente admite e não inventa
    Given uma pergunta sobre um recurso que a documentação do produto não descreve
    When a recuperação volta vazia
    Then o prompt instrui o modelo a dizer que não encontrou o recurso na documentação e a não afirmar que ele existe
```

#### AC-010 — Assunto fora do escopo é recusado e nada é executado

**Cobre**: US-003, FR-006, FR-008

```gherkin
@US-003 @FR-006 @FR-008 @AC-010
Feature: Assunto fora do escopo é recusado e nada é executado

  Scenario: Assunto fora do escopo é recusado e nada é executado
    Given o grafo do assistente montado com o modelo de teste
    When a pessoa pede para criar uma Base ou para escrever um poema
    Then o prompt de sistema limita o assunto a RAG e ao pipeline, o modelo é chamado sem ferramentas e nenhuma escrita ocorre
```

#### AC-011 — Base apontada é analisada pelo conteúdo real

**Cobre**: US-004, FR-007, FR-008, NFR-001

```gherkin
@US-004 @FR-007 @FR-008 @NFR-001 @AC-011
Feature: Base apontada é analisada pelo conteúdo real

  Scenario: Base apontada é analisada pelo conteúdo real
    Given uma Base do próprio tenant e projeto com execução concluída e documentos indexados
    When a pessoa aponta a Base e pergunta qual chunking convém
    Then o contexto enviado ao modelo inclui o nome, os documentos e trechos reais da Base, e nenhuma Base, execução ou consulta é criada
```

#### AC-012 — Base de outro escopo não é analisada

**Cobre**: US-004, FR-007, NFR-001

```gherkin
@US-004 @FR-007 @NFR-001 @AC-012
Feature: Base de outro escopo não é analisada

  Scenario: Base de outro escopo não é analisada
    Given uma Base de outro tenant ou já apagada
    When a pessoa tenta apontá-la em uma mensagem
    Then a API responde 404 igual ao de uma Base inexistente e nenhum trecho dessa Base chega ao modelo
```

#### AC-013 — Base sem execução concluída é recusada com orientação

**Cobre**: US-004, FR-007, NFR-002

```gherkin
@US-004 @FR-007 @NFR-002 @AC-013
Feature: Base sem execução concluída é recusada com orientação

  Scenario: Base sem execução concluída é recusada com orientação
    Given uma Base do próprio escopo sem execução concluída com sucesso
    When a pessoa a aponta
    Then a API responde 409 informando que a Base ainda não tem conteúdo indexado, sem chamar o modelo
```

#### AC-014 — Pergunta de continuação usa as mensagens anteriores

**Cobre**: US-005, FR-003, FR-004

```gherkin
@US-005 @FR-003 @FR-004 @AC-014
Feature: Pergunta de continuação usa as mensagens anteriores

  Scenario: Pergunta de continuação usa as mensagens anteriores
    Given uma conversa em que a pessoa disse ter documentos em Markdown com seções longas
    When ela pergunta "e o overlap ideal para isso?"
    Then o contexto enviado ao modelo contém as mensagens anteriores da mesma conversa em ordem
```

#### AC-015 — Nada atravessa conversas diferentes

**Cobre**: US-005, FR-004, NFR-001

```gherkin
@US-005 @FR-004 @NFR-001 @AC-015
Feature: Nada atravessa conversas diferentes

  Scenario: Nada atravessa conversas diferentes
    Given duas conversas da mesma pessoa com assuntos diferentes
    When ela envia uma mensagem na segunda
    Then o contexto enviado ao modelo não contém nenhuma mensagem da primeira conversa
```

#### AC-016 — Janela de contexto limitada às 20 mensagens mais recentes

**Cobre**: US-005, FR-004, NFR-002

```gherkin
@US-005 @FR-004 @NFR-002 @AC-016
Feature: Janela de contexto limitada às 20 mensagens mais recentes

  Scenario: Janela de contexto limitada às 20 mensagens mais recentes
    Given uma conversa com 30 mensagens gravadas
    When a pessoa envia a mensagem seguinte
    Then somente as 20 mensagens mais recentes entram no contexto e a conversa gravada continua íntegra
```

#### AC-017 — Turno do assistente não altera nada do produto

**Cobre**: FR-008, NFR-001, NFR-004

```gherkin
@FR-008 @NFR-001 @NFR-004 @AC-017
Feature: Turno do assistente não altera nada do produto

  Scenario: Turno do assistente não altera nada do produto
    Given um banco com Workspaces, Bases e Execuções conhecidos
    When a pessoa conversa, inclusive pedindo ao assistente que apague uma Base
    Then as contagens e o conteúdo dessas tabelas permanecem idênticos e somente as tabelas do assistente recebem registros
```

#### AC-018 — Indexação da documentação é idempotente

**Cobre**: FR-011, NFR-004

```gherkin
@FR-011 @NFR-004 @AC-018
Feature: Indexação da documentação é idempotente

  Scenario: Indexação da documentação é idempotente
    Given os arquivos de documentação viva presentes no repositório e uma coleção de conhecimento vazia
    When o comando de indexação roda duas vezes seguidas
    Then a segunda execução mantém os mesmos pontos, registra contagens de inseridos, mantidos e removidos e não cria duplicatas
```

#### AC-019 — Falha na recuperação devolve erro genérico

**Cobre**: FR-010, FR-005, NFR-002

```gherkin
@FR-010 @FR-005 @NFR-002 @AC-019
Feature: Falha na recuperação devolve erro genérico

  Scenario: Falha na recuperação devolve erro genérico
    Given a busca vetorial indisponível
    When a pessoa envia uma mensagem
    Then a API responde 502 genérico sem detalhe do provedor e nada é gravado
```

#### AC-020 — Provedor lento é interrompido pelo limite de tempo

**Cobre**: FR-010, FR-012, NFR-002

```gherkin
@FR-010 @FR-012 @NFR-002 @AC-020
Feature: Provedor lento é interrompido pelo limite de tempo

  Scenario: Provedor lento é interrompido pelo limite de tempo
    Given um provedor de linguagem que não responde
    When o tempo limite de 30 segundos configurado é excedido
    Then a chamada é interrompida, o erro é traduzido para a falha genérica do assistente e o recurso da requisição é liberado
```

#### AC-021 — Sem conhecimento indexado o assistente avisa a limitação

**Cobre**: FR-011, FR-005

```gherkin
@FR-011 @FR-005 @AC-021
Feature: Sem conhecimento indexado o assistente avisa a limitação

  Scenario: Sem conhecimento indexado o assistente avisa a limitação
    Given a coleção de conhecimento do produto ainda não indexada
    When a pessoa faz uma pergunta
    Then a resposta informa que a documentação do produto não está disponível para consulta e a orientação restringe-se a conhecimento geral de RAG, sem afirmar recursos do sistema
```

#### AC-022 — Somente os documentos autorizados entram na indexação

**Cobre**: FR-011, NFR-001

```gherkin
@FR-011 @NFR-001 @AC-022
Feature: Somente os documentos autorizados entram na indexação

  Scenario: Somente os documentos autorizados entram na indexação
    Given um arquivo .env e um documento fora da lista dentro do repositório
    When o comando de indexação roda
    Then somente docs/, PROJECT.md, INTERFACE.md, .specsfy/STACK.md e .specsfy/DATABASE.md são lidos e nenhum segredo ou dado de tenant entra na coleção
```

#### AC-023 — Contrato neutro e adapter de linguagem escolhidos por configuração

**Cobre**: FR-012, FR-005, NFR-002

```gherkin
@FR-012 @FR-005 @NFR-002 @AC-023
Feature: Contrato neutro e adapter de linguagem escolhidos por configuração

  Scenario: Contrato neutro e adapter de linguagem escolhidos por configuração
    Given a configuração declarando provedor, modelo, chave e tempo limite
    When a factory monta o adapter de chat
    Then o adapter cumpre o contrato neutro, uma configuração incompleta falha com mensagem clara e a chave nunca aparece em mensagens de erro
```

#### AC-024 — SDK do modelo confinado ao pacote de providers

**Cobre**: FR-012

```gherkin
@FR-012 @AC-024
Feature: SDK do modelo confinado ao pacote de providers

  Scenario: SDK do modelo confinado ao pacote de providers
    Given o código-fonte de src/
    When a varredura estática de imports roda
    Then langchain_openai só aparece em src/pipeline/providers/ (e em chat.py, exceção registrada) e src/app importa somente src.pipeline.service
```

#### AC-025 — Painel operável por teclado com foco previsível

**Cobre**: US-001, NFR-003

```gherkin
@US-001 @NFR-003 @AC-025
Feature: Painel operável por teclado com foco previsível

  Scenario: Painel operável por teclado com foco previsível
    Given o painel fechado e o foco no botão do assistente
    When a pessoa o abre com Enter, navega com Tab e fecha com Esc
    Then o foco entra no painel, permanece preso nele enquanto aberto e volta ao botão ao fechar
```

#### AC-026 — Resposta e carregamento anunciados a tecnologia assistiva

**Cobre**: US-001, NFR-003

```gherkin
@US-001 @NFR-003 @AC-026
Feature: Resposta e carregamento anunciados a tecnologia assistiva

  Scenario: Resposta e carregamento anunciados a tecnologia assistiva
    Given uma mensagem enviada aguardando resposta
    When o assistente responde ou falha
    Then o estado de carregamento e a nova mensagem são anunciados em uma região aria-live e o erro aparece com role alert
```

#### AC-027 — Layout legível em mobile e com conteúdo longo

**Cobre**: US-001, NFR-003

```gherkin
@US-001 @NFR-003 @AC-027
Feature: Layout legível em mobile e com conteúdo longo

  Scenario: Layout legível em mobile e com conteúdo longo
    Given um viewport de 375 px e uma resposta longa com bloco de código
    When o painel é aberto
    Then o painel ocupa a largura útil, a rolagem é vertical dentro da lista e nenhum conteúdo gera rolagem horizontal da página
```

#### AC-028 — Mensagem vazia ou acima de 4000 caracteres é recusada

**Cobre**: FR-003, NFR-002

```gherkin
@FR-003 @NFR-002 @AC-028
Feature: Mensagem vazia ou acima de 4000 caracteres é recusada

  Scenario: Mensagem vazia ou acima de 4000 caracteres é recusada
    Given uma conversa aberta
    When a pessoa envia texto vazio ou com mais de 4000 caracteres
    Then a API responde 422 com mensagem clara, não chama o modelo e não grava nada
```

#### AC-029 — Log de turno sem conteúdo nem segredo

**Cobre**: FR-009, NFR-004

```gherkin
@FR-009 @NFR-004 @AC-029
Feature: Log de turno sem conteúdo nem segredo

  Scenario: Log de turno sem conteúdo nem segredo
    Given um turno concluído com Base apontada
    When o log estruturado do turno é inspecionado
    Then ele contém pessoa, conversa, se houve Base, duração e resultado, e não contém texto da pergunta, da resposta, trechos de documentos nem credenciais
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve exibir, em cada tela autenticada do frontend, um botão global que abre o painel do assistente sobre a tela atual, permitindo iniciar uma nova conversa e abrir o histórico, sem exibi-lo em Login e Nova senha.
- **FR-002**: O sistema deve persistir conversas por pessoa e oferecer criar, listar (somente as da pessoa autenticada, da mais recente para a mais antiga), abrir com suas mensagens e apagar com remoção das mensagens; o título nasce dos primeiros 60 caracteres da primeira mensagem.
- **FR-003**: O sistema deve receber uma mensagem de 1 a 4000 caracteres em uma conversa da pessoa, gerar a resposta do assistente e gravar o par pergunta e resposta na ordem, devolvendo ambos; em falha nada é gravado.
- **FR-004**: O sistema deve fornecer ao modelo, como memória de curto prazo, as 20 mensagens mais recentes da mesma conversa, e nenhuma mensagem de outra conversa.
- **FR-005**: O sistema deve recuperar trechos da documentação viva do produto em uma coleção dedicada, incluí-los no contexto como dados e devolver, com a resposta, os arquivos de origem usados; sem trechos relevantes, o modelo deve ser instruído a admitir a lacuna.
- **FR-006**: O sistema deve restringir o assistente, por prompt de sistema fixo, ao assunto RAG e ao pipeline de processamento de documentos (recebimento, chunking, splitter, embeddings, upsert e recuperação), recusando com cortesia assuntos fora desse escopo.
- **FR-007**: O sistema deve aceitar, por mensagem, uma Base opcional; quando presente, deve validá-la no escopo da identidade (tenant, projeto e não apagada), exigir ao menos uma execução concluída com sucesso e incluir no contexto o nome, os documentos e trechos reais recuperados da coleção da Base.
- **FR-008**: O sistema deve limitar o assistente a orientar: o modelo é chamado sem ferramentas e nenhum turno cria, altera ou apaga Workspace, Base, Execução, Consulta, Pessoa ou configuração; somente as tabelas do assistente recebem escrita.
- **FR-009**: O sistema deve exigir sessão válida em cada endpoint do assistente e permitir seu uso aos papéis owner, admin e member, escopando conversas pela pessoa autenticada.
- **FR-010**: O sistema deve traduzir falhas do modelo de linguagem, da recuperação vetorial ou do tempo limite em resposta 502 com mensagem genérica, sem detalhe do provedor, sem gravar o par e preservando a possibilidade de reenvio.
- **FR-011**: O sistema deve oferecer um comando idempotente que indexa, na coleção dedicada do assistente, somente docs/, PROJECT.md, INTERFACE.md, .specsfy/STACK.md e .specsfy/DATABASE.md, registrando contagens de pontos previstos, inseridos, mantidos e removidos; quando a coleção não existe, o assistente informa a limitação.
- **FR-012**: O sistema deve obter respostas do modelo por um contrato neutro de chat em src/pipeline/providers/, com adapter e factory configuráveis (provedor, modelo, chave, tempo limite), exposto a src/app somente pela fachada src.pipeline.service, sem importar SDK de modelo fora de src/pipeline/providers/.

#### Não funcionais

- **NFR-001**: Privacidade e isolamento: uma conversa só é visível à autora (inclusive owner e admin recebem 404), a Base apontada respeita o escopo da identidade e nenhum dado de outro tenant chega ao modelo. **Verificação**: testes de API com duas pessoas e dois tenants; inspeção do contexto enviado ao modelo de teste.
- **NFR-002**: Robustez: mensagem limitada a 4000 caracteres, janela de 20 mensagens, tempo limite de 30 segundos por chamada ao modelo e erros sem detalhe interno. **Verificação**: testes de validação, de janela e de timeout com provedor de teste.
- **NFR-003**: Acessibilidade: painel operável por teclado com foco preso e devolvido, Esc fecha, carregamento e resposta anunciados em região viva, erro com role alert e layout sem rolagem horizontal em 375 px. **Verificação**: testes Vitest com Testing Library e axe, mais conferência visual registrada na tarefa.
- **NFR-004**: Observabilidade: cada turno gera um registro estruturado com pessoa, conversa, presença de Base, duração e resultado, sem conteúdo de mensagens, trechos ou credenciais; a indexação registra contagens. **Verificação**: teste que inspeciona o log com caplog e procura conteúdo e segredos.

#### Erros e casos-limite

- Sessão ausente ou expirada em qualquer endpoint → 401, e o frontend limpa a sessão como nas demais telas.
- Conversa inexistente, de outra pessoa ou já apagada → 404 idêntico, sem revelar a existência.
- Base fora do escopo, de outro tenant ou apagada → 404; Base sem execução concluída → 409.
- Texto vazio ou acima de 4000 caracteres → 422 sem chamar o modelo.
- Falha do modelo, da recuperação ou tempo limite de 30 segundos → 502 genérico, sem gravar o par.
- Coleção de conhecimento ausente ou vazia → o assistente responde com aviso de limitação e conhecimento geral de RAG, sem afirmar recursos do sistema.
- Conteúdo de documentos ou de Base com instruções embutidas → tratado como dado; o modelo não tem ferramentas, então o pior efeito é uma resposta de texto incorreta.
- Duas mensagens simultâneas na mesma conversa → ambas são aceitas e ordenadas pela hora de criação; não há bloqueio nesta entrega.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend Python 3.12+ com FastAPI em `src/app/`, SQLAlchemy e Alembic (última revisão `0020_pessoas`), autenticação por Pessoa e Sessão (`src/app/auth.py`, `Identity`), pipeline em `src/pipeline/` acessado por `src/pipeline/service.py`, Qdrant como único vector store.
- Frontend Next.js 16 (App Router), React 19, TypeScript, Tailwind v4, shadcn/ui base-nova e Vitest; shell autenticado em `frontend/src/app/(autenticado)/layout.tsx`.
- `chat.py` é a única exceção ao confinamento de `ChatOpenAI` e não é alterado por esta spec.

#### Arquitetura e módulos

- `src/pipeline/providers/contracts.py`: novo Protocol `ChatModelAdapter` (`responder(mensagens, timeout) -> str`) e dataclass `ChatMessage(papel, conteudo)`.
- `src/pipeline/providers/llm/openrouter.py`: adapter que confina `ChatOpenAI`, lendo `LLM_MODEL`, `OPENROUTER_API_KEY` e o tempo limite; `ProviderFactory` ganha `create_chat_model` e o registro de LLM.
- `src/pipeline/assistant.py`: grafo LangGraph (`StateGraph`) com os nós `recuperar_conhecimento`, `recuperar_base` (condicional a `base_id`), `montar_prompt` e `responder`; o prompt de sistema é fixo e trata trechos como dados delimitados.
- `src/pipeline/service.py`: novas funções `assistant_reply(...)` e `index_assistant_knowledge(...)`, a única superfície vista por `src/app`.
- `index_assistant_docs.py` (raiz): entrypoint que chama `load_env()` e indexa a documentação viva, no padrão dos demais entrypoints.
- Injeção nos testes: `service.assistant_reply` recebe o adapter de chat pela factory de providers; os testes de API registram um adapter de teste na factory (mesmo mecanismo do oráculo em memória do vector store), sem SDK nem rede.
- `src/app/routers/assistente.py`: endpoints, validações, escopo por identidade e log de turno; registrado em `src/app/main.py`.
- `src/app/settings.py`: `AppSettings` recebe a configuração de LLM e o nome da coleção de conhecimento, injetados pelo entrypoint.

#### Migrations

- `alembic/versions/0021_assistente.py` cria `conversas_assistente` e `mensagens_assistente`, com `down_revision` `0020_pessoas`. Rollback: remover as duas tabelas, sem efeito sobre dados existentes. Compatível com o banco atual, pois só adiciona tabelas. Aplicada somente no banco de teste (`rag_pipeline_test`) durante a verificação, conforme as regras do projeto.

#### Models

- `ConversaAssistente` e `MensagemAssistente` em `src/app/models.py`, seguindo o padrão de `_novo_id` e `_agora`; a mensagem pertence à conversa com remoção em cascata.

#### Controllers e casos de uso

- `GET /conversas`, `POST /conversas`, `GET /conversas/{id}`, `POST /conversas/{id}/mensagens` e `DELETE /conversas/{id}` em `src/app/routers/assistente.py`; todos dependem de `get_identity`, sem exigir papel de escrita, e filtram por `pessoa_id`.
- O envio valida o texto, carrega a conversa da pessoa, valida a Base pelo `repo.get_base_or_404` e exige execução concluída, monta a configuração da coleção da Base como em `routers/queries.py`, chama `service.assistant_reply` e só então grava o par.

#### Views e experiência

- Painel lateral global em `frontend/src/features/assistente/`, montado no layout autenticado; estados de carregando, vazio, erro, sucesso e sem permissão descritos na seção 10.

#### Queries e repositórios

- Helpers em `src/app/repo.py`: `list_conversas_da_pessoa`, `get_conversa_or_404` (filtra por pessoa) e `list_mensagens_recentes`; índices por (`pessoa_id`, `atualizada_em`) e (`conversa_id`, `criada_em`); a listagem do histórico devolve no máximo 50 conversas.

#### Jobs e processamento assíncrono

- Não aplicável ao turno: a resposta é gerada na própria requisição. A indexação da documentação é um comando manual do operador, sem fila.

#### Estrutura de arquivos

```text
specs/in-progress/0021-chat-assistente-especialista-rag-pipeline/
  spec.md
alembic/versions/0021_assistente.py
index_assistant_docs.py
src/app/models.py
src/app/repo.py
src/app/routers/assistente.py
src/app/settings.py
src/pipeline/assistant.py
src/pipeline/service.py
src/pipeline/providers/contracts.py
src/pipeline/providers/factory.py
src/pipeline/providers/llm/openrouter.py
tests/test_app_assistente.py
tests/test_assistente_grafo.py
tests/test_assistente_indexacao.py
tests/test_llm_provider.py
tests/test_provider_boundaries.py
frontend/src/features/assistente/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `conversas_assistente` | `id` (texto gerado) | `tenant_id`, `project_id`, `pessoa_id`, `titulo` (até 60 caracteres, derivado da primeira mensagem; "Nova conversa" enquanto vazia), `criada_em`, `atualizada_em`; visível só à autora | Pertence a uma Pessoa; tem muitas mensagens |
| `mensagens_assistente` | `id` (texto gerado) | `conversa_id`, `papel` (pessoa ou assistente), `conteudo` (texto de até 4000 caracteres para a pessoa), `base_id` opcional sem chave estrangeira, `fontes` (lista JSON de arquivos citados), `criada_em`; imutável | Pertence a uma conversa, removida em cascata |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| `conversas_assistente` | inexistente | pessoa cria conversa ou envia a primeira mensagem | ativa | pertence à pessoa e ao escopo da identidade |
| `conversas_assistente` | ativa | par pergunta e resposta gravado | ativa (`atualizada_em` avança) | mensagens em ordem de `criada_em` |
| `conversas_assistente` | ativa | autora confirma apagar | removida | mensagens removidas junto; outra pessoa nunca apaga |

#### Migração e retenção

- Migration aditiva `0021_assistente`, sem migração de dados. Conversas permanecem até a autora apagar; desativar a pessoa não as apaga, mas ela deixa de acessá-las. O conteúdo enviado ao modelo (mensagem, trechos da documentação e trechos da Base apontada) sai para o provedor de LLM configurado, o mesmo padrão já aceito no `chat.py`.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. A entrega é um chat usado por pessoas dentro do frontend; API e persistência isoladas não a atendem.

#### Stack e convenções de interface

- Frontend `frontend/`: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, shadcn/ui preset base-nova sobre Base UI, registry ReUI configurado sem blocos instalados, Vitest com Testing Library e testes de acessibilidade por axe. Cliente HTTP único em `frontend/src/lib/api-client.ts`.
- Telas atuais preservadas: Login, Nova senha, Pessoas, Workspaces, detalhe do Workspace e detalhe da Base. O layout autenticado ganha apenas a montagem do launcher; nenhuma rota é criada nem alterada.
- Primitives a instalar por shadcn: `textarea` e `select`. Composições ReUI: nenhuma nova, porque os primitives locais atendem.

#### Telas e responsabilidades

- **Painel do assistente** (sobre qualquer tela autenticada): qualquer papel conversa, alterna entre a conversa atual e o histórico, inicia nova conversa e, opcionalmente, aponta uma Base. Entrada: texto e Base opcional; saída: mensagens e fontes citadas.
- Não há tela ou rota própria; o painel é uma camada sobre a tela corrente.

#### Fluxo de informação e navegação

- A pessoa aciona o botão do assistente em qualquer tela, o painel abre em Sheet lateral e mostra a última conversa ativa ou o estado vazio com sugestões de perguntas. Envia mensagem, vê o carregamento e recebe a resposta com fontes. Pelo cabeçalho do painel, abre o histórico, retoma uma conversa, apaga com confirmação ou inicia uma nova. Fechar o painel (Esc, botão de fechar) devolve o foco ao botão e preserva a tela de fundo sem recarregá-la.
- `Breadcrumb`: não aplicável ao painel, porque ele é uma camada sobre a tela atual e não uma tela de módulo; o `Breadcrumb` do shell continua refletindo a tela por baixo.

#### Menus e navegação principal

- Não há item de menu novo. O acesso é o botão global, visível a owner, admin e member em todas as telas autenticadas, fixo no canto inferior direito, com rótulo acessível "Abrir assistente". Em telas estreitas o painel ocupa a largura útil e o botão respeita a área segura inferior. Login e Nova senha não o exibem.

#### Formulários e ações

- **Campo de mensagem** (Textarea): obrigatório, 1 a 4000 caracteres, contador visível a partir de 3500, Enter envia e Shift+Enter quebra linha, botão Enviar como ação principal.
- **Base (opcional)** (Select): lista as Bases do escopo com a opção "Nenhuma"; ajuda curta informa que o assistente analisa o conteúdo da Base antes de recomendar.
- **Ações**: Nova conversa, abrir Histórico, retomar conversa, apagar conversa (confirmação em diálogo). Padrão: painel lateral com diálogo de confirmação para o apagar; não há página de formulário.
- Erros aparecem em `Alert` destrutivo dentro do painel, sem descartar o texto digitado.

#### Composição e disposição

- Hierarquia do painel: cabeçalho (título, Nova conversa, Histórico, fechar), lista de mensagens rolável, rodapé fixo com Base e campo de mensagem. Desktop: Sheet de largura fixa à direita; mobile (375 px): largura útil inteira. Mensagens da pessoa alinhadas à direita e do assistente à esquerda; fontes como `Badge` abaixo da resposta. Reaproveita `Sheet`, `Dialog`, `Skeleton`, `Badge`, `Button` e `Alert` existentes e os tokens de `globals.css`.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Assistente (global) | AssistenteLauncher | Botão fixo no canto inferior direito que abre o painel; oculto em Login e Nova senha | frontend/src/features/assistente/AssistenteLauncher.tsx | Button com ícone lucide | shadcn/ui (Button) e próprio | Novo; montado uma vez no layout autenticado |
| Assistente (global) | AssistentePainel | Compõe o painel, alterna entre conversa e histórico, controla foco e Esc | frontend/src/features/assistente/AssistentePainel.tsx | Sheet lateral | shadcn/ui (Sheet, já existente em components/ui/sheet.tsx) | Novo; reusa o Sheet de UploadBaseSheet como referência de padrão |
| Assistente (histórico) | ListaConversas | Lista as conversas da pessoa com título e data, abre e aciona apagar | frontend/src/features/assistente/ListaConversas.tsx | Lista de botões com Skeleton e estado vazio | shadcn/ui (Button, Skeleton) e próprio | Novo; lista simples, não é grade de registros |
| Assistente (histórico) | ApagarConversaDialog | Confirma a consequência antes de apagar uma conversa | frontend/src/features/assistente/ApagarConversaDialog.tsx | Dialog de confirmação | shadcn/ui (Dialog) | Estende o padrão de ExcluirBaseDialog |
| Assistente (conversa) | ListaMensagens | Rola as mensagens, anuncia carregamento e novas respostas em região viva | frontend/src/features/assistente/ListaMensagens.tsx | Região aria-live com Skeleton | shadcn/ui (Skeleton) e próprio | Novo |
| Assistente (conversa) | MensagemChat | Renderiza uma mensagem da pessoa ou do assistente e as fontes citadas | frontend/src/features/assistente/MensagemChat.tsx | Bolha com Badge de fonte | shadcn/ui (Badge) e próprio | Novo |
| Assistente (conversa) | ComposerMensagem | Campo de texto com contador, envio por Enter e Base opcional | frontend/src/features/assistente/ComposerMensagem.tsx | Textarea, Button e SeletorBase | shadcn/ui (Textarea, Button; Textarea a instalar) | Novo |
| Assistente (conversa) | SeletorBase | Escolhe opcionalmente uma Base do escopo para análise | frontend/src/features/assistente/SeletorBase.tsx | Select | shadcn/ui (Select, a instalar) | Novo; lê /api/v1/bases pelo cliente HTTP único |
| Assistente (global) | useAssistente | Estado de conversas e mensagens e chamadas ao cliente HTTP único | frontend/src/features/assistente/useAssistente.ts | Hook | próprio | Novo; usa apiJson de frontend/src/lib/api-client.ts |

- A lista corresponde ao que será registrado em `INTERFACE.md` na implementação; `Textarea` e `Select` são os únicos primitives novos a instalar e a instalação é uma tarefa própria.
- O launcher é montado uma vez em `frontend/src/app/(autenticado)/layout.tsx`; nenhuma página duplica o assistente.

#### Estados e acessibilidade

- **Carregando**: `Skeleton` na lista de conversas e indicador de "digitando" enquanto aguarda a resposta, com botão Enviar desabilitado.
- **Vazio**: sem conversas, estado vazio com três sugestões de pergunta; conversa nova sem mensagens mostra o mesmo convite.
- **Erro**: `Alert` com role alert e texto genérico, ação "Tentar novamente" que reenvia o texto preservado; 401 limpa a sessão e volta ao login.
- **Sucesso**: resposta anunciada em região aria-live polite, com fontes citadas.
- **Permissão insuficiente**: não há papel excluído; sessão inválida redireciona ao login como nas demais telas.
- **Teclado e foco**: abrir com Enter ou Espaço no botão, foco preso no painel enquanto aberto, Esc fecha e devolve o foco ao botão, ordem de tabulação cabeçalho, mensagens, Base, campo, Enviar. Rótulos explícitos em cada controle e contraste conforme o design system.
- `Breadcrumb`: mantido pelo shell, sem alteração.

#### Contrato CRUD

- Não aplicável como CRUD administrativo: o histórico é uma lista simples dentro do painel, sem tela de listagem de registros. Por isso o `PageHeader` compartilhado não é replicado (o painel tem cabeçalho próprio de Sheet) e não se usa `DataGrid`; a coluna `ID` não é exibida porque a conversa é identificada pelo título e pela data. A linha da conversa abre a conversa por mouse e teclado; as ações são abrir e apagar, e não há editar: o apagar respeita a autoria e confirma a consequência em diálogo antes de executar.
- Nenhum componente recorrente de cabeçalho ou grade é criado; os blocos novos são registrados em `INTERFACE.md`.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre durante a implementação, mesmo sem pedido da pessoa, lendo `DESIGNSYSTEM.MD`, `INTERFACE.md` e os componentes afetados, e confere bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho, altura de linha e quebra de texto) do painel, do botão e do diálogo.
- Registrar em cada tarefa de interface a forma de conferência, os viewports (375 px e desktop), os estados (vazio, carregando, resposta longa com bloco de código, erro, histórico vazio e cheio, foco), os achados e os ajustes; tarefas sem interface registram `Não aplicável` com o motivo concreto.

#### APIs expostas

- Prefixo `/api/v1/assistente`, autenticação por `Authorization: Bearer` da sessão, sem versão nova.
- `GET /conversas` → 200 com lista (`id`, `titulo`, `atualizada_em`), até 50, mais recentes primeiro.
- `POST /conversas` → 201 com `id` e `titulo` "Nova conversa".
- `GET /conversas/{id}` → 200 com `id`, `titulo` e `mensagens` (`id`, `papel`, `conteudo`, `fontes`, `base_id`, `criada_em`).
- `POST /conversas/{id}/mensagens` com `texto` e `base_id` opcional → 201 com `mensagem_pessoa` e `mensagem_assistente`.
- `DELETE /conversas/{id}` → 204.
- Erros: 401 sessão, 404 conversa ou Base fora do escopo, 409 Base sem execução concluída, 422 validação, 502 falha do modelo ou da recuperação.

#### APIs externas utilizadas

- OpenRouter (API compatível com OpenAI) por `ChatOpenAI`, autenticado por `OPENROUTER_API_KEY`, modelo em `LLM_MODEL`, tempo limite de 30 segundos, sem repetição automática e sem fallback: a falha vira 502 genérico.
- Qdrant, pelo contrato de vector store existente, para a coleção de conhecimento e a coleção da Base.

#### Documentação das APIs consultadas

- Nenhuma nesta definição; a consulta a LangGraph v1+, LangChain v1+ e OpenRouter é tarefa de planejamento e será registrada na seção 2.

#### Eventos e outros contratos

- Contrato neutro `ChatModelAdapter`/`ChatMessage` em `src/pipeline/providers/contracts.py`, com o adapter OpenRouter como única implementação. Não há eventos.

### 11. Estratégia TDD

- **Unidade**: grafo do assistente com modelo e recuperação de teste (`tests/test_assistente_grafo.py`), adapter e factory (`tests/test_llm_provider.py`), componentes React isolados.
- **Integração/contrato**: endpoints com banco de teste e sessão real por Pessoa (`tests/test_app_assistente.py`), indexação (`tests/test_assistente_indexacao.py`), varredura estática de fronteiras (`tests/test_provider_boundaries.py`).
- **BDD/aceite**: o Gherkin da seção 6 orienta os casos; cada caso TDD declara o próprio marcador `SPECSFY: SPEC-0021 <IDs>`, sem criar nem executar arquivo `.feature`.
- **Runner TDD**: Pytest para o backend (projeto Python, runner já existente) e Vitest para o frontend (`test:tdd` = `vitest run`, já materializado).
- **E2E**: não aplicável nesta entrega; a jornada é coberta por integração de API e por testes de componente. A prova real com provedor de LLM é verificação manual.
- **Verificação manual**: uma conversa real com o provedor configurado e a documentação indexada, porque o comportamento do modelo real não é determinístico e não pode ser afirmado por teste automatizado.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-009, AC-001 | AC-001 na seção 6 | test_launcher_aparece_nas_telas_autenticadas_e_abre_o_painel em frontend/src/features/assistente/AssistenteLauncher.test.tsx, marcador `SPECSFY: SPEC-0021 US-001 FR-001 FR-009 AC-001` | Observado em 2026-09-24: `npm --prefix frontend run test:tdd -- src/features/assistente/AssistenteLauncher.test.tsx` falha porque o layout autenticado ainda não renderiza o botão "Abrir assistente" (TestingLibraryElementError na asserção) | GREEN em 2026-09-24: `npm --prefix frontend run test:tdd -- src/features/assistente/AssistenteLauncher.test.tsx` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-001, FR-003, FR-009, AC-002 | AC-002 na seção 6 | test_enviar_mensagem_devolve_resposta_e_persiste_o_par em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 US-001 FR-003 FR-009 AC-002` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_enviar_mensagem_devolve_resposta_e_persiste_o_par` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-001, FR-003, FR-010, NFR-002, AC-003 | AC-003 na seção 6 | test_falha_do_provedor_devolve_502_generico_sem_gravar em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 US-001 FR-003 FR-010 NFR-002 AC-003` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_falha_do_provedor_devolve_502_generico_sem_gravar` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-001, FR-001, FR-009, NFR-001, AC-004 | AC-004 na seção 6 | test_endpoints_do_assistente_exigem_sessao_valida em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 US-001 FR-001 FR-009 NFR-001 AC-004` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_endpoints_do_assistente_exigem_sessao_valida` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-002, FR-002, NFR-001, AC-005 | AC-005 na seção 6 | test_listar_conversas_devolve_so_as_da_pessoa_mais_recentes_primeiro em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 US-002 FR-002 NFR-001 AC-005` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_listar_conversas_devolve_so_as_da_pessoa_mais_recentes_primeiro` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-002, FR-001, FR-002, FR-003, AC-006 | AC-006 na seção 6 | test_nova_conversa_e_retomada_do_historico_mantem_as_mensagens em frontend/src/features/assistente/AssistentePainel.test.tsx, marcador `SPECSFY: SPEC-0021 US-002 FR-001 FR-002 FR-003 AC-006` | Observado em 2026-09-24: `npm --prefix frontend run test:tdd -- src/features/assistente/AssistentePainel.test.tsx` falha porque `AssistentePainel` ainda não existe (falha explícita via `exigir` no corpo do teste) | GREEN em 2026-09-24: `npm --prefix frontend run test:tdd -- src/features/assistente/AssistentePainel.test.tsx` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-002, FR-002, NFR-001, AC-007 | AC-007 na seção 6 | test_apagar_conversa_so_pela_autora_e_outra_pessoa_recebe_404 em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 US-002 FR-002 NFR-001 AC-007` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_apagar_conversa_so_pela_autora_e_outra_pessoa_recebe_404` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-003, FR-005, FR-006, AC-008 | AC-008 na seção 6 | test_resposta_usa_trechos_recuperados_e_devolve_as_fontes em tests/test_assistente_grafo.py, marcador `SPECSFY: SPEC-0021 US-003 FR-005 FR-006 AC-008` | Observado em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q -k test_resposta_usa_trechos_recuperados_e_devolve_as_fontes` falha porque `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-003, FR-005, FR-006, AC-009 | AC-009 na seção 6 | test_sem_trechos_relevantes_instrui_o_modelo_a_admitir_lacuna em tests/test_assistente_grafo.py, marcador `SPECSFY: SPEC-0021 US-003 FR-005 FR-006 AC-009` | Observado em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q -k test_sem_trechos_relevantes_instrui_o_modelo_a_admitir_lacuna` falha porque `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-003, FR-006, FR-008, AC-010 | AC-010 na seção 6 | test_prompt_de_sistema_restringe_escopo_e_nao_expoe_ferramentas em tests/test_assistente_grafo.py, marcador `SPECSFY: SPEC-0021 US-003 FR-006 FR-008 AC-010` | Observado em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q -k test_prompt_de_sistema_restringe_escopo_e_nao_expoe_ferramentas` falha porque `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-004, FR-007, FR-008, NFR-001, AC-011 | AC-011 na seção 6 | test_base_apontada_inclui_chunks_reais_no_contexto_sem_escrever em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 US-004 FR-007 FR-008 NFR-001 AC-011` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_base_apontada_inclui_chunks_reais_no_contexto_sem_escrever` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-004, FR-007, NFR-001, AC-012 | AC-012 na seção 6 | test_base_de_outro_escopo_devolve_404_sem_vazar em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 US-004 FR-007 NFR-001 AC-012` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_base_de_outro_escopo_devolve_404_sem_vazar` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-004, FR-007, NFR-002, AC-013 | AC-013 na seção 6 | test_base_sem_execucao_concluida_devolve_409 em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 US-004 FR-007 NFR-002 AC-013` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_base_sem_execucao_concluida_devolve_409` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-005, FR-003, FR-004, AC-014 | AC-014 na seção 6 | test_mensagens_anteriores_da_conversa_entram_no_contexto em tests/test_assistente_grafo.py, marcador `SPECSFY: SPEC-0021 US-005 FR-003 FR-004 AC-014` | Observado em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q -k test_mensagens_anteriores_da_conversa_entram_no_contexto` falha porque `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-005, FR-004, NFR-001, AC-015 | AC-015 na seção 6 | test_contexto_nao_inclui_mensagens_de_outra_conversa em tests/test_assistente_grafo.py, marcador `SPECSFY: SPEC-0021 US-005 FR-004 NFR-001 AC-015` | Observado em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q -k test_contexto_nao_inclui_mensagens_de_outra_conversa` falha porque `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-005, FR-004, NFR-002, AC-016 | AC-016 na seção 6 | test_contexto_limita_a_janela_de_vinte_mensagens em tests/test_assistente_grafo.py, marcador `SPECSFY: SPEC-0021 US-005 FR-004 NFR-002 AC-016` | Observado em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q -k test_contexto_limita_a_janela_de_vinte_mensagens` falha porque `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| FR-008, NFR-001, NFR-004, AC-017 | AC-017 na seção 6 | test_turno_nao_altera_bases_workspaces_execucoes_nem_configuracao em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 FR-008 NFR-001 NFR-004 AC-017` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_turno_nao_altera_bases_workspaces_execucoes_nem_configuracao` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| FR-011, NFR-004, AC-018 | AC-018 na seção 6 | test_indexar_documentacao_duas_vezes_nao_duplica_pontos em tests/test_assistente_indexacao.py, marcador `SPECSFY: SPEC-0021 FR-011 NFR-004 AC-018` | Observado em 2026-09-24: `uv run pytest tests/test_assistente_indexacao.py -q -k test_indexar_documentacao_duas_vezes_nao_duplica_pontos` falha porque `service.index_assistant_knowledge` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_assistente_indexacao.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| FR-010, FR-005, NFR-002, AC-019 | AC-019 na seção 6 | test_falha_da_recuperacao_devolve_502_generico em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 FR-010 FR-005 NFR-002 AC-019` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_falha_da_recuperacao_devolve_502_generico` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| FR-010, FR-012, NFR-002, AC-020 | AC-020 na seção 6 | test_chamada_ao_modelo_respeita_timeout_configurado em tests/test_llm_provider.py, marcador `SPECSFY: SPEC-0021 FR-010 FR-012 NFR-002 AC-020` | Observado em 2026-09-24: `uv run pytest tests/test_llm_provider.py -q -k test_chamada_ao_modelo_respeita_timeout_configurado` falha porque `ChatMessage` ainda não existe em `contracts.py` (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_llm_provider.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| FR-011, FR-005, AC-021 | AC-021 na seção 6 | test_colecao_de_conhecimento_ausente_avisa_e_ainda_orienta em tests/test_assistente_grafo.py, marcador `SPECSFY: SPEC-0021 FR-011 FR-005 AC-021` | Observado em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q -k test_colecao_de_conhecimento_ausente_avisa_e_ainda_orienta` falha porque `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_assistente_grafo.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| FR-011, NFR-001, AC-022 | AC-022 na seção 6 | test_indexacao_le_apenas_a_lista_de_documentos_autorizados em tests/test_assistente_indexacao.py, marcador `SPECSFY: SPEC-0021 FR-011 NFR-001 AC-022` | Observado em 2026-09-24: `uv run pytest tests/test_assistente_indexacao.py -q -k test_indexacao_le_apenas_a_lista_de_documentos_autorizados` falha porque `service.index_assistant_knowledge` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_assistente_indexacao.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| FR-012, FR-005, NFR-002, AC-023 | AC-023 na seção 6 | test_factory_resolve_adapter_neutro_e_valida_configuracao em tests/test_llm_provider.py, marcador `SPECSFY: SPEC-0021 FR-012 FR-005 NFR-002 AC-023` | Observado em 2026-09-24: `uv run pytest tests/test_llm_provider.py -q -k test_factory_resolve_adapter_neutro_e_valida_configuracao` falha porque `ProviderFactory.create_chat_model` ainda não existe (AttributeError no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_llm_provider.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| FR-012, AC-024 | AC-024 na seção 6 | test_sdk_de_chat_so_e_importado_em_providers_e_app_usa_a_fachada em tests/test_provider_boundaries.py, marcador `SPECSFY: SPEC-0021 FR-012 AC-024` | Observado em 2026-09-24: `uv run pytest tests/test_provider_boundaries.py -q -k test_sdk_de_chat_so_e_importado_em_providers_e_app_usa_a_fachada` falha porque `service.py` sem `assistant_reply` e `index_assistant_knowledge` (asserção do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_provider_boundaries.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-001, NFR-003, AC-025 | AC-025 na seção 6 | test_painel_abre_e_fecha_por_teclado_e_devolve_o_foco em frontend/src/features/assistente/AssistentePainel.a11y.test.tsx, marcador `SPECSFY: SPEC-0021 US-001 NFR-003 AC-025` | Observado em 2026-09-24: `npm --prefix frontend run test:tdd -- src/features/assistente/AssistentePainel.a11y.test.tsx` falha porque `AssistenteLauncher` ainda não existe (falha explícita via `exigir` no corpo do teste) | GREEN em 2026-09-24: `npm --prefix frontend run test:tdd -- src/features/assistente/AssistentePainel.a11y.test.tsx` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-001, NFR-003, AC-026 | AC-026 na seção 6 | test_carregando_e_resposta_sao_anunciados_em_regiao_viva em frontend/src/features/assistente/ListaMensagens.a11y.test.tsx, marcador `SPECSFY: SPEC-0021 US-001 NFR-003 AC-026` | Observado em 2026-09-24: `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx` falha porque `ListaMensagens` ainda não existe (falha explícita via `exigir` no corpo do teste) | GREEN em 2026-09-24: `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| US-001, NFR-003, AC-027 | AC-027 na seção 6 | test_painel_em_viewport_estreito_e_mensagens_longas_sem_overflow_horizontal em frontend/src/features/assistente/AssistentePainel.test.tsx, marcador `SPECSFY: SPEC-0021 US-001 NFR-003 AC-027` | Observado em 2026-09-24: `npm --prefix frontend run test:tdd -- src/features/assistente/AssistentePainel.test.tsx` falha porque `AssistentePainel` ainda não existe (falha explícita via `exigir` no corpo do teste) | GREEN em 2026-09-24: `npm --prefix frontend run test:tdd -- src/features/assistente/AssistentePainel.test.tsx` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| FR-003, NFR-002, AC-028 | AC-028 na seção 6 | test_mensagem_vazia_ou_acima_do_limite_devolve_422 em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 FR-003 NFR-002 AC-028` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_mensagem_vazia_ou_acima_do_limite_devolve_422` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |
| FR-009, NFR-004, AC-029 | AC-029 na seção 6 | test_log_de_turno_registra_metadados_sem_conteudo em tests/test_app_assistente.py, marcador `SPECSFY: SPEC-0021 FR-009 NFR-004 AC-029` | Observado em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q -k test_log_de_turno_registra_metadados_sem_conteudo` falha porque `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste) | GREEN em 2026-09-24: `uv run pytest tests/test_app_assistente.py -q` passa | Regressão: `uv run pytest -q` (402 aprovados, 1 ignorado) e `npm --prefix frontend run test:tdd` (135 aprovados) |

#### Fechamento da T054 — 2026-09-28

- **Regressão**: `uv run pytest -q` → 402 aprovados, 1 skip opt-in preexistente da SPEC-0014 e 2 warnings de dependências; `npm --prefix frontend run test:tdd` → 31 arquivos e 135 testes aprovados; `uv run ruff check .`, `npm --prefix frontend run lint` e `npm --prefix frontend run typecheck` → saída 0.
- **Build**: `npm --prefix frontend run build -- --webpack` → compilação, TypeScript e 9 páginas estáticas aprovadas. O comando canônico com Turbopack foi impedido pelo ambiente ao tentar bind de porta (`Operation not permitted`), sem erro de código.
- **Rastreabilidade**: `check_traceability.mjs` → 50/50 IDs cobertos em 85 arquivos; os 29 ACs permanecem GREEN.
- **Indexação real**: `index_assistant_docs.py` sincronizou 460 chunks na coleção `assistente_conhecimento` (`previstos=460`, `inseridos=460`, `mantidos=0`, `removidos=0`).
- **Prova real autorizada**: com OpenRouter e o modelo padrão preexistente `openai/gpt-4o-mini`, a pergunta “Como o sistema processa um documento Markdown até a recuperação e quais fontes sustentam a resposta?” retornou orientação sobre recebimento, chunking, embeddings, upsert e recuperação, citando `docs/application.md`; “Qual a previsão do tempo para amanhã em Fortaleza?” foi recusada por estar fora do escopo de RAG e processamento de documentos.
- **Visual/DOM**: navegador indisponível na sessão (`browsers: []`); a revisão usou DOM renderizado pelos testes e inspeção dos componentes em 375 px e desktop, cobrindo resposta longa, erro, histórico, foco, bordas, espaçamento, padding, tipografia, quebra e overflow. Vitest/axe não encontrou violações aplicáveis.

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| US-001 | AC-001 | Componente | frontend/src/features/assistente/AssistenteLauncher.test.tsx | Passed |
| US-001 | AC-002 | Integração | tests/test_app_assistente.py | Passed |
| US-001 | AC-003 | Integração | tests/test_app_assistente.py | Passed |
| US-001 | AC-004 | Integração | tests/test_app_assistente.py | Passed |
| US-001 | AC-025 | Componente | frontend/src/features/assistente/AssistentePainel.a11y.test.tsx | Passed |
| US-001 | AC-026 | Componente | frontend/src/features/assistente/ListaMensagens.a11y.test.tsx | Passed |
| US-001 | AC-027 | Componente | frontend/src/features/assistente/AssistentePainel.test.tsx | Passed |
| US-002 | AC-005 | Integração | tests/test_app_assistente.py | Passed |
| US-002 | AC-006 | Componente | frontend/src/features/assistente/AssistentePainel.test.tsx | Passed |
| US-002 | AC-007 | Integração | tests/test_app_assistente.py | Passed |
| US-003 | AC-008 | Unidade | tests/test_assistente_grafo.py | Passed |
| US-003 | AC-009 | Unidade | tests/test_assistente_grafo.py | Passed |
| US-003 | AC-010 | Unidade | tests/test_assistente_grafo.py | Passed |
| US-004 | AC-011 | Integração | tests/test_app_assistente.py | Passed |
| US-004 | AC-012 | Integração | tests/test_app_assistente.py | Passed |
| US-004 | AC-013 | Integração | tests/test_app_assistente.py | Passed |
| US-005 | AC-014 | Unidade | tests/test_assistente_grafo.py | Passed |
| US-005 | AC-015 | Unidade | tests/test_assistente_grafo.py | Passed |
| US-005 | AC-016 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-001 | AC-001 | Componente | frontend/src/features/assistente/AssistenteLauncher.test.tsx | Passed |
| FR-001 | AC-004 | Integração | tests/test_app_assistente.py | Passed |
| FR-001 | AC-006 | Componente | frontend/src/features/assistente/AssistentePainel.test.tsx | Passed |
| FR-002 | AC-005 | Integração | tests/test_app_assistente.py | Passed |
| FR-002 | AC-006 | Componente | frontend/src/features/assistente/AssistentePainel.test.tsx | Passed |
| FR-002 | AC-007 | Integração | tests/test_app_assistente.py | Passed |
| FR-003 | AC-002 | Integração | tests/test_app_assistente.py | Passed |
| FR-003 | AC-003 | Integração | tests/test_app_assistente.py | Passed |
| FR-003 | AC-006 | Componente | frontend/src/features/assistente/AssistentePainel.test.tsx | Passed |
| FR-003 | AC-014 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-003 | AC-028 | Integração | tests/test_app_assistente.py | Passed |
| FR-004 | AC-014 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-004 | AC-015 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-004 | AC-016 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-005 | AC-008 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-005 | AC-009 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-005 | AC-019 | Integração | tests/test_app_assistente.py | Passed |
| FR-005 | AC-021 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-005 | AC-023 | Unidade | tests/test_llm_provider.py | Passed |
| FR-006 | AC-008 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-006 | AC-009 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-006 | AC-010 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-007 | AC-011 | Integração | tests/test_app_assistente.py | Passed |
| FR-007 | AC-012 | Integração | tests/test_app_assistente.py | Passed |
| FR-007 | AC-013 | Integração | tests/test_app_assistente.py | Passed |
| FR-008 | AC-010 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-008 | AC-011 | Integração | tests/test_app_assistente.py | Passed |
| FR-008 | AC-017 | Integração | tests/test_app_assistente.py | Passed |
| FR-009 | AC-001 | Componente | frontend/src/features/assistente/AssistenteLauncher.test.tsx | Passed |
| FR-009 | AC-002 | Integração | tests/test_app_assistente.py | Passed |
| FR-009 | AC-004 | Integração | tests/test_app_assistente.py | Passed |
| FR-009 | AC-029 | Integração | tests/test_app_assistente.py | Passed |
| FR-010 | AC-003 | Integração | tests/test_app_assistente.py | Passed |
| FR-010 | AC-019 | Integração | tests/test_app_assistente.py | Passed |
| FR-010 | AC-020 | Unidade | tests/test_llm_provider.py | Passed |
| FR-011 | AC-018 | Integração | tests/test_assistente_indexacao.py | Passed |
| FR-011 | AC-021 | Unidade | tests/test_assistente_grafo.py | Passed |
| FR-011 | AC-022 | Integração | tests/test_assistente_indexacao.py | Passed |
| FR-012 | AC-020 | Unidade | tests/test_llm_provider.py | Passed |
| FR-012 | AC-023 | Unidade | tests/test_llm_provider.py | Passed |
| FR-012 | AC-024 | Contrato | tests/test_provider_boundaries.py | Passed |
| NFR-001 | AC-004 | Integração | tests/test_app_assistente.py | Passed |
| NFR-001 | AC-005 | Integração | tests/test_app_assistente.py | Passed |
| NFR-001 | AC-007 | Integração | tests/test_app_assistente.py | Passed |
| NFR-001 | AC-011 | Integração | tests/test_app_assistente.py | Passed |
| NFR-001 | AC-012 | Integração | tests/test_app_assistente.py | Passed |
| NFR-001 | AC-015 | Unidade | tests/test_assistente_grafo.py | Passed |
| NFR-001 | AC-017 | Integração | tests/test_app_assistente.py | Passed |
| NFR-001 | AC-022 | Integração | tests/test_assistente_indexacao.py | Passed |
| NFR-002 | AC-003 | Integração | tests/test_app_assistente.py | Passed |
| NFR-002 | AC-013 | Integração | tests/test_app_assistente.py | Passed |
| NFR-002 | AC-016 | Unidade | tests/test_assistente_grafo.py | Passed |
| NFR-002 | AC-019 | Integração | tests/test_app_assistente.py | Passed |
| NFR-002 | AC-020 | Unidade | tests/test_llm_provider.py | Passed |
| NFR-002 | AC-023 | Unidade | tests/test_llm_provider.py | Passed |
| NFR-002 | AC-028 | Integração | tests/test_app_assistente.py | Passed |
| NFR-003 | AC-025 | Componente | frontend/src/features/assistente/AssistentePainel.a11y.test.tsx | Passed |
| NFR-003 | AC-026 | Componente | frontend/src/features/assistente/ListaMensagens.a11y.test.tsx | Passed |
| NFR-003 | AC-027 | Componente | frontend/src/features/assistente/AssistentePainel.test.tsx | Passed |
| NFR-004 | AC-017 | Integração | tests/test_app_assistente.py | Passed |
| NFR-004 | AC-018 | Integração | tests/test_assistente_indexacao.py | Passed |
| NFR-004 | AC-029 | Integração | tests/test_app_assistente.py | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/in-progress/0021-chat-assistente-especialista-rag-pipeline/spec.md`
- **Achados**: validação em 2026-09-24. Estrutura sem falhas; contagens US 5, FR 12, NFR 4, AC 29; cada US, FR e NFR cobre no mínimo três AC. Revisão semântica sem BLOCKER; os achados abaixo foram resolvidos ou aceitos com decisão registrada.
- **FIND-ARCH-001** [P2] [Resolved] LangGraph é exigido pela regra do projeto, mas só existe como dependência transitiva de langchain — Refs: FR-012 — Evidence: pyproject.toml — Effect: a implementação poderia depender de um pacote não declarado e a mudança de stack ficaria sem registro — Suggestion: declarar a dependência direta e citar STACK.md e PACKAGES.md na Definition of Done (feito na seção 16 e na seção 18).
- **FIND-ARCH-002** [P2] [Resolved] A Definition of Done não exigia a atualização de DATABASE.md, RULES.md e PROJECT.md apesar de nova persistência e nova regra de arquitetura — Refs: FR-002, FR-012 — Evidence: .specsfy/DATABASE.md — Effect: o mapa de dados manual ficaria defasado, como as regras do projeto já alertam — Suggestion: itens explícitos de DoD para STACK.md, DATABASE.md, RULES.md, PROJECT.md e INTERFACE.md (feito na seção 18).
- **FIND-ARCH-003** [P3] [Resolved] O risco sobre frontmatter estava incorreto: o loader aceita Markdown sem frontmatter; a dúvida real é ler arquivos de origens distintas em run_pipeline — Refs: FR-011 — Evidence: src/pipeline/loader.py — Effect: o planejamento poderia investigar o problema errado — Suggestion: risco reescrito na seção 16 para a leitura por diretório de entrada.
- **FIND-ARCH-004** [P3] [Resolved] Faltava dizer como os testes de API substituem o modelo de linguagem — Refs: FR-012, AC-002 — Evidence: src/pipeline/providers/factory.py — Effect: testes poderiam exigir rede ou SDK real — Suggestion: registrar adapter de teste na factory, como o oráculo em memória do vector store (feito na seção 8).
- **FIND-SEC-001** [P2] [Accepted] Não há limite de taxa nem controle de custo por pessoa — Refs: FR-003, NFR-002 — Evidence: src/app/routers/queries.py — Effect: uso abusivo por pessoa autenticada geraria custo no provedor — Suggestion: aceito nesta fatia pela DEC-007, com limites por turno e uso interno autenticado.
- **FIND-SEC-002** [P2] [Accepted] Trechos de documentos e de Bases entram no prompt e podem conter instruções embutidas — Refs: FR-007, FR-008 — Evidence: src/app/routers/queries.py — Effect: o modelo pode produzir texto enganoso, mas não tem ferramentas nem escrita — Suggestion: aceito pela DEC-003, com trechos delimitados como dados no prompt de sistema.
- **FIND-SEC-003** [P3] [Resolved] O isolamento da Base apontada dependia de reproduzir a montagem de escopo de routers/queries.py — Refs: FR-007, AC-012, NFR-001 — Evidence: src/app/tasks.py — Effect: divergência de escopo vazaria trechos entre tenants — Suggestion: reutilizar repo.get_base_or_404 e scope_project_id, coberto por AC-012 (registrado na seção 8 e na seção 16).

#### Gate do Ato II — Plano

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0021-chat-assistente-especialista-rag-pipeline/spec.md`
- **Achados**: validação estrita em 2026-09-24 sem erros. 54 tarefas (2 `[OPS]`, 29 `[TEST] [TDD]`, 16 `[CODE]`, 6 `[DOC]`, 1 `[TEST]` final), 50 de 50 IDs cobertos, interface validada. Os 29 predecessores TDD (T003 a T031) estão concluídos com RED válido registrado na seção 11 (24 casos Pytest e 5 Vitest). Sem tag `[MIGRATION]`, conforme `.specsfy/RULES.md`; T035 registra `alembic upgrade head` e `alembic current` no banco de teste. Contratos fixados pelos testes: `executar_turno`, `service.index_assistant_knowledge`, `ProviderFactory.create_chat_model` (`model`, `api_key`, `timeout`, `base_url`), papéis `sistema`/`pessoa`/`assistente` e `metadata["caminho_origem"]`.

#### Gate do Ato III — Entrega

- **Resultado**: Passed
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0021-chat-assistente-especialista-rag-pipeline/spec.md .`
- **Achados**: fechamento em 2026-09-28 com 50/50 IDs cobertos em 85 arquivos, 29/29 ACs GREEN, 402 testes Pytest aprovados (1 skip opt-in preexistente da SPEC-0014), 135 testes Vitest aprovados, Ruff/ESLint/TypeScript verdes, build Next.js com Webpack aprovado, documentação e monitor de contexto atuais, 460 chunks de conhecimento sincronizados e prova real OpenRouter aprovada para resposta com fonte e recusa fora do escopo. O Turbopack foi impedido exclusivamente pela restrição ambiental de bind de porta; a revisão visual foi feita por DOM renderizado e inspeção de componentes porque não havia navegador disponível.

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

#### Fase 0 — Setup mínimo

**Objetivo**: ter LangGraph e os primitives `textarea` e `select` disponíveis antes dos testes que dependem deles.
**Teste independente**: `uv run python -c "import langgraph"` e `ls frontend/src/components/ui/textarea.tsx frontend/src/components/ui/select.tsx` saem com código 0.

- [x] T001 [OPS] Declarar `langgraph` como dependência direta em ./pyproject.toml e sincronizar ./uv.lock — Refs: FR-012, NFR-002, AC-023 — Depends: none
  - [x] **PREP**: `langgraph` só constava como transitiva de `langchain` (1.1.10); baseline: suíte Python com 340 aprovados.
  - [x] **EXECUTE**: Declarado `langgraph>=1` em `dependencies` com `uv add`; lock resolveu 116 pacotes sem atualizar os demais.
  - [x] **VERIFY**: `uv run python -c "import langgraph"` saiu com código 0, versão 1.1.10. A consulta às docs LangChain/LangGraph v1+ fica registrada em T037.
  - [x] **VISUAL**: Não aplicável: a tarefa só altera dependências, sem superfície visual.
  - [x] **EVIDENCE**: Comandos `uv add "langgraph>=1"` e import com saída 0; arquivos `pyproject.toml` e `uv.lock`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: a dependência direta mínima já cobre o requisito (StateGraph v1).

- [x] T002 [OPS] Instalar os primitives shadcn `textarea` e `select` em frontend/src/components/ui/textarea.tsx e select.tsx — Refs: US-001, FR-003, FR-007, NFR-003 — Depends: none
  - [x] **PREP**: `components.json` (base-nova) confirmado e `textarea`/`select` ausentes; `INTERFACE.md` lido.
  - [x] **EXECUTE**: `npx shadcn@latest add textarea select` criou `textarea.tsx` e `select.tsx`; `axe-core@4.13.0` declarado como devDependency; ambos os primitives registrados em `INTERFACE.md`.
  - [x] **VERIFY**: `npm run lint` saiu com código 0; `typecheck` só acusa os três módulos de teste ainda inexistentes (T043, T046, T047), sem erro nos primitives.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia dos dois primitives contra os tokens do tema e o `Input` existente; sem tela alterada nesta tarefa, então nenhum ajuste.
  - [x] **EVIDENCE**: Arquivos `frontend/src/components/ui/textarea.tsx`, `select.tsx`, `frontend/package.json`, `INTERFACE.md`.
  - [x] **IMPROVE**: `axe-core` passou de dependência transitiva para direta, evitando quebra do teste AC-025 se o lint mudar de versão.

#### Fase 1 — RED TDD informado pelo BDD

Uma tarefa por `AC` (29). O RED aceito é o de comportamento ausente; erro de sintaxe, de coleta ou de fixture de infraestrutura obriga a corrigir o teste. Nos testes de frontend, importar o módulo ainda inexistente dentro do corpo do teste (importação tardia) para que a ausência apareça como falha do caso, não como erro de coleta. Nos testes de backend, importar `src.app.routers.assistente` e os novos models de forma tardia pelo mesmo motivo.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-001 o caso `test_launcher_aparece_nas_telas_autenticadas_e_abre_o_painel` em frontend/src/features/assistente/AssistenteLauncher.test.tsx — Refs: US-001, FR-001, FR-009, AC-001 — Depends: none
  - [x] **PREP**: Gherkin do AC-001 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_launcher_aparece_nas_telas_autenticadas_e_abre_o_painel` escrito em frontend/src/features/assistente/AssistenteLauncher.test.tsx com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `frontend/src/features/assistente/_apoio.ts`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `npm --prefix frontend run test:tdd -- src/features/assistente/AssistenteLauncher.test.tsx`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência de bordas, espaçamentos, margens, padding e tipografia ocorre nas tarefas de interface.
  - [x] **EVIDENCE**: RED registrado na linha do AC-001 da seção 11; causa: o layout autenticado ainda não renderiza o botão "Abrir assistente" (TestingLibraryElementError na asserção).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-002 o caso `test_enviar_mensagem_devolve_resposta_e_persiste_o_par` em tests/test_app_assistente.py — Refs: US-001, FR-003, FR-009, AC-002 — Depends: none
  - [x] **PREP**: Gherkin do AC-002 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_enviar_mensagem_devolve_resposta_e_persiste_o_par` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_enviar_mensagem_devolve_resposta_e_persiste_o_par`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-002 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-003 o caso `test_falha_do_provedor_devolve_502_generico_sem_gravar` em tests/test_app_assistente.py — Refs: US-001, FR-003, FR-010, NFR-002, AC-003 — Depends: none
  - [x] **PREP**: Gherkin do AC-003 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_falha_do_provedor_devolve_502_generico_sem_gravar` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_falha_do_provedor_devolve_502_generico_sem_gravar`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-003 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T006 [TEST] [TDD] [US-001] Derivar do AC-004 o caso `test_endpoints_do_assistente_exigem_sessao_valida` em tests/test_app_assistente.py — Refs: US-001, FR-001, FR-009, NFR-001, AC-004 — Depends: none
  - [x] **PREP**: Gherkin do AC-004 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_endpoints_do_assistente_exigem_sessao_valida` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_endpoints_do_assistente_exigem_sessao_valida`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-004 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-005 o caso `test_listar_conversas_devolve_so_as_da_pessoa_mais_recentes_primeiro` em tests/test_app_assistente.py — Refs: US-002, FR-002, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Gherkin do AC-005 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_listar_conversas_devolve_so_as_da_pessoa_mais_recentes_primeiro` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_listar_conversas_devolve_so_as_da_pessoa_mais_recentes_primeiro`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-005 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-006 o caso `test_nova_conversa_e_retomada_do_historico_mantem_as_mensagens` em frontend/src/features/assistente/AssistentePainel.test.tsx — Refs: US-002, FR-001, FR-002, FR-003, AC-006 — Depends: none
  - [x] **PREP**: Gherkin do AC-006 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_nova_conversa_e_retomada_do_historico_mantem_as_mensagens` escrito em frontend/src/features/assistente/AssistentePainel.test.tsx com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `frontend/src/features/assistente/_apoio.ts`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `npm --prefix frontend run test:tdd -- src/features/assistente/AssistentePainel.test.tsx`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência de bordas, espaçamentos, margens, padding e tipografia ocorre nas tarefas de interface.
  - [x] **EVIDENCE**: RED registrado na linha do AC-006 da seção 11; causa: `AssistentePainel` ainda não existe (falha explícita via `exigir` no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-007 o caso `test_apagar_conversa_so_pela_autora_e_outra_pessoa_recebe_404` em tests/test_app_assistente.py — Refs: US-002, FR-002, NFR-001, AC-007 — Depends: none
  - [x] **PREP**: Gherkin do AC-007 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_apagar_conversa_so_pela_autora_e_outra_pessoa_recebe_404` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_apagar_conversa_so_pela_autora_e_outra_pessoa_recebe_404`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-007 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-008 o caso `test_resposta_usa_trechos_recuperados_e_devolve_as_fontes` em tests/test_assistente_grafo.py — Refs: US-003, FR-005, FR-006, AC-008 — Depends: none
  - [x] **PREP**: Gherkin do AC-008 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_resposta_usa_trechos_recuperados_e_devolve_as_fontes` escrito em tests/test_assistente_grafo.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_assistente_grafo.py -q -k test_resposta_usa_trechos_recuperados_e_devolve_as_fontes`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-008 da seção 11; causa: `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-009 o caso `test_sem_trechos_relevantes_instrui_o_modelo_a_admitir_lacuna` em tests/test_assistente_grafo.py — Refs: US-003, FR-005, FR-006, AC-009 — Depends: none
  - [x] **PREP**: Gherkin do AC-009 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_sem_trechos_relevantes_instrui_o_modelo_a_admitir_lacuna` escrito em tests/test_assistente_grafo.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_assistente_grafo.py -q -k test_sem_trechos_relevantes_instrui_o_modelo_a_admitir_lacuna`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-009 da seção 11; causa: `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-010 o caso `test_prompt_de_sistema_restringe_escopo_e_nao_expoe_ferramentas` em tests/test_assistente_grafo.py — Refs: US-003, FR-006, FR-008, AC-010 — Depends: none
  - [x] **PREP**: Gherkin do AC-010 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_prompt_de_sistema_restringe_escopo_e_nao_expoe_ferramentas` escrito em tests/test_assistente_grafo.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_assistente_grafo.py -q -k test_prompt_de_sistema_restringe_escopo_e_nao_expoe_ferramentas`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-010 da seção 11; causa: `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T013 [TEST] [TDD] [US-004] Derivar do AC-011 o caso `test_base_apontada_inclui_chunks_reais_no_contexto_sem_escrever` em tests/test_app_assistente.py — Refs: US-004, FR-007, FR-008, NFR-001, AC-011 — Depends: none
  - [x] **PREP**: Gherkin do AC-011 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_base_apontada_inclui_chunks_reais_no_contexto_sem_escrever` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_base_apontada_inclui_chunks_reais_no_contexto_sem_escrever`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-011 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T014 [TEST] [TDD] [US-004] Derivar do AC-012 o caso `test_base_de_outro_escopo_devolve_404_sem_vazar` em tests/test_app_assistente.py — Refs: US-004, FR-007, NFR-001, AC-012 — Depends: none
  - [x] **PREP**: Gherkin do AC-012 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_base_de_outro_escopo_devolve_404_sem_vazar` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_base_de_outro_escopo_devolve_404_sem_vazar`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-012 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T015 [TEST] [TDD] [US-004] Derivar do AC-013 o caso `test_base_sem_execucao_concluida_devolve_409` em tests/test_app_assistente.py — Refs: US-004, FR-007, NFR-002, AC-013 — Depends: none
  - [x] **PREP**: Gherkin do AC-013 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_base_sem_execucao_concluida_devolve_409` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_base_sem_execucao_concluida_devolve_409`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-013 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T016 [TEST] [TDD] [US-005] Derivar do AC-014 o caso `test_mensagens_anteriores_da_conversa_entram_no_contexto` em tests/test_assistente_grafo.py — Refs: US-005, FR-003, FR-004, AC-014 — Depends: none
  - [x] **PREP**: Gherkin do AC-014 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_mensagens_anteriores_da_conversa_entram_no_contexto` escrito em tests/test_assistente_grafo.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_assistente_grafo.py -q -k test_mensagens_anteriores_da_conversa_entram_no_contexto`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-014 da seção 11; causa: `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T017 [TEST] [TDD] [US-005] Derivar do AC-015 o caso `test_contexto_nao_inclui_mensagens_de_outra_conversa` em tests/test_assistente_grafo.py — Refs: US-005, FR-004, NFR-001, AC-015 — Depends: none
  - [x] **PREP**: Gherkin do AC-015 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_contexto_nao_inclui_mensagens_de_outra_conversa` escrito em tests/test_assistente_grafo.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_assistente_grafo.py -q -k test_contexto_nao_inclui_mensagens_de_outra_conversa`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-015 da seção 11; causa: `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T018 [TEST] [TDD] [US-005] Derivar do AC-016 o caso `test_contexto_limita_a_janela_de_vinte_mensagens` em tests/test_assistente_grafo.py — Refs: US-005, FR-004, NFR-002, AC-016 — Depends: none
  - [x] **PREP**: Gherkin do AC-016 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_contexto_limita_a_janela_de_vinte_mensagens` escrito em tests/test_assistente_grafo.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_assistente_grafo.py -q -k test_contexto_limita_a_janela_de_vinte_mensagens`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-016 da seção 11; causa: `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T019 [TEST] [TDD] Derivar do AC-017 o caso `test_turno_nao_altera_bases_workspaces_execucoes_nem_configuracao` em tests/test_app_assistente.py — Refs: FR-008, NFR-001, NFR-004, AC-017 — Depends: none
  - [x] **PREP**: Gherkin do AC-017 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_turno_nao_altera_bases_workspaces_execucoes_nem_configuracao` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_turno_nao_altera_bases_workspaces_execucoes_nem_configuracao`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-017 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T020 [TEST] [TDD] Derivar do AC-018 o caso `test_indexar_documentacao_duas_vezes_nao_duplica_pontos` em tests/test_assistente_indexacao.py — Refs: FR-011, NFR-004, AC-018 — Depends: none
  - [x] **PREP**: Gherkin do AC-018 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_indexar_documentacao_duas_vezes_nao_duplica_pontos` escrito em tests/test_assistente_indexacao.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_assistente_indexacao.py -q -k test_indexar_documentacao_duas_vezes_nao_duplica_pontos`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-018 da seção 11; causa: `service.index_assistant_knowledge` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T021 [TEST] [TDD] Derivar do AC-019 o caso `test_falha_da_recuperacao_devolve_502_generico` em tests/test_app_assistente.py — Refs: FR-010, FR-005, NFR-002, AC-019 — Depends: none
  - [x] **PREP**: Gherkin do AC-019 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_falha_da_recuperacao_devolve_502_generico` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_falha_da_recuperacao_devolve_502_generico`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-019 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T022 [TEST] [TDD] Derivar do AC-020 o caso `test_chamada_ao_modelo_respeita_timeout_configurado` em tests/test_llm_provider.py — Refs: FR-010, FR-012, NFR-002, AC-020 — Depends: none
  - [x] **PREP**: Gherkin do AC-020 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_chamada_ao_modelo_respeita_timeout_configurado` escrito em tests/test_llm_provider.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_llm_provider.py -q -k test_chamada_ao_modelo_respeita_timeout_configurado`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-020 da seção 11; causa: `ChatMessage` ainda não existe em `contracts.py` (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T023 [TEST] [TDD] Derivar do AC-021 o caso `test_colecao_de_conhecimento_ausente_avisa_e_ainda_orienta` em tests/test_assistente_grafo.py — Refs: FR-011, FR-005, AC-021 — Depends: none
  - [x] **PREP**: Gherkin do AC-021 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_colecao_de_conhecimento_ausente_avisa_e_ainda_orienta` escrito em tests/test_assistente_grafo.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_assistente_grafo.py -q -k test_colecao_de_conhecimento_ausente_avisa_e_ainda_orienta`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-021 da seção 11; causa: `src.pipeline.assistant.executar_turno` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T024 [TEST] [TDD] Derivar do AC-022 o caso `test_indexacao_le_apenas_a_lista_de_documentos_autorizados` em tests/test_assistente_indexacao.py — Refs: FR-011, NFR-001, AC-022 — Depends: none
  - [x] **PREP**: Gherkin do AC-022 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_indexacao_le_apenas_a_lista_de_documentos_autorizados` escrito em tests/test_assistente_indexacao.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_assistente_indexacao.py -q -k test_indexacao_le_apenas_a_lista_de_documentos_autorizados`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-022 da seção 11; causa: `service.index_assistant_knowledge` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T025 [TEST] [TDD] Derivar do AC-023 o caso `test_factory_resolve_adapter_neutro_e_valida_configuracao` em tests/test_llm_provider.py — Refs: FR-012, FR-005, NFR-002, AC-023 — Depends: none
  - [x] **PREP**: Gherkin do AC-023 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_factory_resolve_adapter_neutro_e_valida_configuracao` escrito em tests/test_llm_provider.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_llm_provider.py -q -k test_factory_resolve_adapter_neutro_e_valida_configuracao`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-023 da seção 11; causa: `ProviderFactory.create_chat_model` ainda não existe (AttributeError no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T026 [TEST] [TDD] Derivar do AC-024 o caso `test_sdk_de_chat_so_e_importado_em_providers_e_app_usa_a_fachada` em tests/test_provider_boundaries.py — Refs: FR-012, AC-024 — Depends: none
  - [x] **PREP**: Gherkin do AC-024 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_sdk_de_chat_so_e_importado_em_providers_e_app_usa_a_fachada` escrito em tests/test_provider_boundaries.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_provider_boundaries.py -q -k test_sdk_de_chat_so_e_importado_em_providers_e_app_usa_a_fachada`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-024 da seção 11; causa: `service.py` sem `assistant_reply` e `index_assistant_knowledge` (asserção do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T027 [TEST] [TDD] [US-001] Derivar do AC-025 o caso `test_painel_abre_e_fecha_por_teclado_e_devolve_o_foco` em frontend/src/features/assistente/AssistentePainel.a11y.test.tsx — Refs: US-001, NFR-003, AC-025 — Depends: none
  - [x] **PREP**: Gherkin do AC-025 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_painel_abre_e_fecha_por_teclado_e_devolve_o_foco` escrito em frontend/src/features/assistente/AssistentePainel.a11y.test.tsx com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `frontend/src/features/assistente/_apoio.ts`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `npm --prefix frontend run test:tdd -- src/features/assistente/AssistentePainel.a11y.test.tsx`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência de bordas, espaçamentos, margens, padding e tipografia ocorre nas tarefas de interface.
  - [x] **EVIDENCE**: RED registrado na linha do AC-025 da seção 11; causa: `AssistenteLauncher` ainda não existe (falha explícita via `exigir` no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T028 [TEST] [TDD] [US-001] Derivar do AC-026 o caso `test_carregando_e_resposta_sao_anunciados_em_regiao_viva` em frontend/src/features/assistente/ListaMensagens.a11y.test.tsx — Refs: US-001, NFR-003, AC-026 — Depends: none
  - [x] **PREP**: Gherkin do AC-026 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_carregando_e_resposta_sao_anunciados_em_regiao_viva` escrito em frontend/src/features/assistente/ListaMensagens.a11y.test.tsx com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `frontend/src/features/assistente/_apoio.ts`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência de bordas, espaçamentos, margens, padding e tipografia ocorre nas tarefas de interface.
  - [x] **EVIDENCE**: RED registrado na linha do AC-026 da seção 11; causa: `ListaMensagens` ainda não existe (falha explícita via `exigir` no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T029 [TEST] [TDD] [US-001] Derivar do AC-027 o caso `test_painel_em_viewport_estreito_e_mensagens_longas_sem_overflow_horizontal` em frontend/src/features/assistente/AssistentePainel.test.tsx — Refs: US-001, NFR-003, AC-027 — Depends: none
  - [x] **PREP**: Gherkin do AC-027 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_painel_em_viewport_estreito_e_mensagens_longas_sem_overflow_horizontal` escrito em frontend/src/features/assistente/AssistentePainel.test.tsx com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `frontend/src/features/assistente/_apoio.ts`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `npm --prefix frontend run test:tdd -- src/features/assistente/AssistentePainel.test.tsx`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de frontend; a conferência de bordas, espaçamentos, margens, padding e tipografia ocorre nas tarefas de interface.
  - [x] **EVIDENCE**: RED registrado na linha do AC-027 da seção 11; causa: `AssistentePainel` ainda não existe (falha explícita via `exigir` no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T030 [TEST] [TDD] Derivar do AC-028 o caso `test_mensagem_vazia_ou_acima_do_limite_devolve_422` em tests/test_app_assistente.py — Refs: FR-003, NFR-002, AC-028 — Depends: none
  - [x] **PREP**: Gherkin do AC-028 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_mensagem_vazia_ou_acima_do_limite_devolve_422` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_mensagem_vazia_ou_acima_do_limite_devolve_422`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-028 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

- [x] T031 [TEST] [TDD] Derivar do AC-029 o caso `test_log_de_turno_registra_metadados_sem_conteudo` em tests/test_app_assistente.py — Refs: FR-009, NFR-004, AC-029 — Depends: none
  - [x] **PREP**: Gherkin do AC-029 lido na seção 6; IDs e nível confirmados; proteção do banco `SAFE` e runner do projeto (Pytest/Vitest) confirmado.
  - [x] **EXECUTE**: `test_log_de_turno_registra_metadados_sem_conteudo` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0021 …` na definição; nenhum `.feature` criado ou executado. Apoio compartilhado em `tests/_assistente.py`.
  - [x] **VERIFY**: RED válido observado em 2026-09-24 com `uv run pytest tests/test_app_assistente.py -q -k test_log_de_turno_registra_metadados_sem_conteudo`: o caso executa e falha por comportamento ausente, sem erro de sintaxe, de coleta ou de fixture.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa teste de backend, sem superfície visual.
  - [x] **EVIDENCE**: RED registrado na linha do AC-029 da seção 11; causa: `src.app.routers.assistente` ainda não existe (falha explícita no corpo do teste).
  - [x] **IMPROVE**: Importação tardia por `exigir` mantém o RED por comportamento ausente; nenhuma outra melhoria necessária.

#### Fase 2 — Fundação: contrato de chat, dados e migration (US-001, US-002, US-005)

**Objetivo**: contrato neutro de LLM confinado a `src/pipeline/providers/`, tabelas do assistente e helpers de escopo por pessoa.
**Teste independente**: `uv run pytest tests/test_llm_provider.py tests/test_provider_boundaries.py tests/test_app_models.py -q` passa.

- [x] T032 [CODE] Criar o contrato `ChatModelAdapter` e `ChatMessage` em src/pipeline/providers/contracts.py — Refs: FR-012, NFR-002, AC-020, AC-023, AC-024 — Depends: T001, T022, T025, T026
  - [x] **PREP**: REDs T022, T025 e T026 confirmados; baseline `uv run pytest -q` com 340 aprovados; `docs/` reconstruído com `build_documentation.mjs` antes de `EXECUTE`.
  - [x] **EXECUTE**: Adicionados `ChatMessage` e o Protocol `ChatModelAdapter` em `contracts.py`, `ChatProviderError` em `errors.py` e reexports em `providers/__init__.py`; nenhum import de SDK.
  - [x] **VERIFY**: Import dos três símbolos e `uv run ruff check src` com saída 0; `test_provider_boundaries.py`, `test_provider_factory.py` e `test_characterization_providers.py` sem regressão nos casos preexistentes (o caso AC-024 segue RED até T039).
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: Comandos com saída 0; arquivos `contracts.py`, `errors.py`, `providers/__init__.py`; `STACK.md` atualizado (LangGraph e contrato de chat) e `PROJECT.md` sem impacto material (o contrato é interno, sem mudar finalidade ou limites).
  - [x] **IMPROVE**: `ChatProviderError` nasceu como subclasse de `ProviderError`, assim a camada de aplicação captura um único tipo.
  <!-- specsfy:evidence {"task": "T032", "refs": ["FR-012", "NFR-002", "AC-020", "AC-023", "AC-024"], "files": ["src/pipeline/providers/contracts.py", "src/pipeline/providers/errors.py", "src/pipeline/providers/__init__.py"], "commands": [{"run": "uv run ruff check src", "exit": 0}, {"run": "uv run pytest tests/test_provider_boundaries.py tests/test_provider_factory.py tests/test_characterization_providers.py -q --deselect tests/test_provider_boundaries.py::test_sdk_de_chat_so_e_importado_em_providers_e_app_usa_a_fachada", "exit": 0}]} -->

- [x] T033 [CODE] Criar o adapter OpenRouter, a factory de chat e a configuração de LLM em src/pipeline/providers/llm/openrouter.py, factory.py e src/app/settings.py — Refs: FR-005, FR-010, FR-012, NFR-002, AC-020, AC-023, AC-024 — Depends: T032, T022, T025, T026
  - [x] **PREP**: REDs T022, T025 e T026 e T032 confirmados; `docs/` reconstruído; API `ChatOpenAI(model, api_key, base_url, timeout, max_retries)` conferida no SDK instalado (langchain-openai 1.2.1).
  - [x] **EXECUTE**: Criados `llm/openrouter.py` (adapter que confina `ChatOpenAI`, sem repetição e com erro genérico `ChatProviderError`), `ProviderFactory.create_chat_model` com registro `_CHAT_MODELS`, e `AppSettings` com `llm` e `conhecimento_collection` lidos do ambiente somente em `src/app/main.py` (`LLM_MODEL`, `OPENROUTER_API_KEY`, `APP_LLM_TIMEOUT`).
  - [x] **VERIFY**: `tests/test_llm_provider.py` (2 casos, incluindo a chamada real a um socket que nunca responde, interrompida em menos de 10 s), `test_provider_boundaries.py` (sem o caso AC-024, ainda RED até T039) e `test_app_settings.py` passam; `uv run ruff check src` com saída 0.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN de AC-020 e AC-023; `STACK.md` já registra o contrato e `PROJECT.md` sem impacto material (configuração interna do assistente).
  - [x] **IMPROVE**: A mensagem de erro do adapter só registra o tipo da exceção no log, porque mensagens de SDK podem ecoar cabeçalhos com a chave.
  <!-- specsfy:evidence {"task": "T033", "refs": ["FR-005", "FR-010", "FR-012", "NFR-002", "AC-020", "AC-023", "AC-024"], "files": ["src/pipeline/providers/llm/__init__.py", "src/pipeline/providers/llm/openrouter.py", "src/pipeline/providers/factory.py", "src/app/settings.py", "src/app/main.py"], "commands": [{"run": "uv run pytest tests/test_llm_provider.py tests/test_provider_boundaries.py tests/test_app_settings.py -q --deselect tests/test_provider_boundaries.py::test_sdk_de_chat_so_e_importado_em_providers_e_app_usa_a_fachada", "exit": 0}, {"run": "uv run ruff check src", "exit": 0}]} -->

- [x] T034 [CODE] Criar os models `ConversaAssistente` e `MensagemAssistente` em src/app/models.py — Refs: US-002, FR-002, NFR-001, AC-005, AC-007, AC-017 — Depends: T007, T009, T019
  - [x] **PREP**: REDs T007, T009 e T019 e baseline (379 aprovados, 1 falha preexistente de guarda corrigida) confirmados; Proteção do banco `SAFE` (`check_database_safety.mjs`) e `docs/` reconstruído antes de `EXECUTE`.
  - [x] **EXECUTE**: Declaradas `ConversaAssistente` e `MensagemAssistente` em `src/app/models.py` com `_novo_id`/`_agora`, índices (`pessoa_id`,`atualizada_em`) e (`conversa_id`,`criada_em`), `fontes` JSON e cascata em ORM e no banco.
  - [x] **VERIFY**: `uv run pytest tests/test_app_models.py tests/test_app_migrations.py -q` conclui com 8 aprovados; o comportamento de router segue RED até T040/T041.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN de estrutura; `DATABASE.md` reconciliado manualmente e `PROJECT.md` sem impacto material (só persistência interna do assistente).
  - [x] **IMPROVE**: `base_id` ficou sem chave estrangeira, como a seção 9 pede, para a mensagem sobreviver à exclusão lógica da Base.
  <!-- specsfy:evidence {"task": "T034", "refs": ["US-002", "FR-002", "NFR-001", "AC-005", "AC-007", "AC-017"], "files": ["src/app/models.py"], "commands": [{"run": "uv run pytest tests/test_app_models.py tests/test_app_migrations.py -q", "exit": 0}]} -->

- [x] T035 [CODE] Criar a revisão Alembic `0021_assistente` em alembic/versions/0021_assistente.py — Refs: US-002, FR-002, NFR-001, AC-005, AC-007, AC-017 — Depends: T034, T007, T009, T019
  - [x] **PREP**: REDs T007, T009 e T019 e a revisão `0020_pessoas` como `down_revision` confirmados; ambiente de scratch dedicado `rag_pipeline_alembic_schema_check`, diferente do banco de desenvolvimento; nenhum comando destrutivo foi executado.
  - [x] **EXECUTE**: Criada `alembic/versions/0021_assistente.py` com as duas tabelas, os índices e o `downgrade` que remove somente essas tabelas.
  - [x] **VERIFY**: `APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_alembic_schema_check uv run alembic upgrade head` (saída 0, `0020_pessoas -> 0021_assistente`) e `APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_alembic_schema_check uv run alembic current` mostrou `0021_assistente (head)`; `test_app_migrations.py` (incluindo os downgrades) passou com 8 aprovados. O banco `rag_pipeline_test` recebe as tabelas por `create_all`, então a migration roda no scratch, como as suítes da SPEC-0019 e da SPEC-0020.
  - [x] **VISUAL**: Não aplicável: revisão de banco, sem superfície visual.
  - [x] **EVIDENCE**: Comandos de `upgrade` e `current` com saída 0 registrados; ambos passaram pelo `check_database_safety.mjs` com resultado `SAFE`.
  - [x] **IMPROVE**: A revisão reaproveita o padrão de nomes de índice da `0020`, e o downgrade remove índice e tabela na ordem inversa.
  <!-- specsfy:evidence {"task": "T035", "refs": ["US-002", "FR-002", "NFR-001", "AC-005", "AC-007", "AC-017"], "files": ["alembic/versions/0021_assistente.py"], "commands": [{"run": "APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_alembic_schema_check uv run alembic upgrade head", "exit": 0}, {"run": "APP_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:55432/rag_pipeline_alembic_schema_check uv run alembic current", "exit": 0}, {"run": "uv run pytest tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}]} -->

- [x] T036 [CODE] Criar os helpers de conversas e mensagens em src/app/repo.py — Refs: US-002, US-005, FR-002, FR-004, NFR-001, AC-005, AC-007, AC-015, AC-016 — Depends: T034, T035, T007, T009, T017, T018
  - [x] **PREP**: REDs T007, T009, T017 e T018 (AC-005, AC-007, AC-015, AC-016) confirmados; T034 e T035 concluídas; `docs/` reconstruído.
  - [x] **EXECUTE**: Adicionados `list_conversas_da_pessoa` (até 50, mais recentes primeiro), `get_conversa_or_404` (404 idêntico para outra pessoa, tenant ou inexistente) e `list_mensagens_recentes` (20 mais recentes, ordem cronológica) em `src/app/repo.py`.
  - [x] **VERIFY**: `uv run ruff check src` e a suíte existente (379 aprovados, sem regressão) concluem com saída 0; os casos de API do assistente seguem RED até T040/T041.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: Suíte completa sem regressão e `ruff` com saída 0; `PROJECT.md` sem impacto material.
  - [x] **IMPROVE**: Os três helpers filtram por pessoa, tenant e projeto na própria consulta, sem deixar o isolamento para o router.
  <!-- specsfy:evidence {"task": "T036", "refs": ["US-002", "US-005", "FR-002", "FR-004", "NFR-001", "AC-005", "AC-007", "AC-015", "AC-016"], "files": ["src/app/repo.py"], "commands": [{"run": "uv run ruff check src", "exit": 0}, {"run": "uv run pytest tests/test_app_models.py tests/test_app_migrations.py -q", "exit": 0}]} -->

#### Fase 3 — US-001, US-002, US-003 e US-005: conhecimento, grafo e API (P1 e P2)

**Objetivo**: orquestração LangGraph com prompt fixo, recuperação da documentação, memória de 20 mensagens e endpoints escopados por pessoa.
**Teste independente**: `uv run pytest tests/test_assistente_grafo.py tests/test_assistente_indexacao.py tests/test_app_assistente.py -q` passa.

- [x] T037 [CODE] Criar o grafo LangGraph do assistente em src/pipeline/assistant.py — Refs: US-003, US-005, FR-004, FR-005, FR-006, FR-008, FR-011, NFR-001, NFR-002, AC-008, AC-009, AC-010, AC-014, AC-015, AC-016, AC-021 — Depends: T032, T010, T011, T012, T016, T017, T018, T023
  - [x] **PREP**: REDs T010, T011, T012, T016, T017, T018 e T023 (AC-008, 009, 010, 014, 015, 016, 021) confirmados; T032 concluída; docs do LangGraph v1+ consultadas e registradas na seção 2; `docs/` reconstruído.
  - [x] **EXECUTE**: Criado `src/pipeline/assistant.py` com `StateGraph` (`recuperar_conhecimento` → `recuperar_base` condicional → `montar_prompt` → `responder`), prompt de sistema fixo (escopo RAG e pipeline, apenas orienta, recusa cortês, trechos como dados delimitados), aviso de lacuna, aviso de coleção ausente, janela de 20 mensagens e modelo chamado sem ferramentas.
  - [x] **VERIFY**: `uv run pytest tests/test_assistente_grafo.py -q` com 7 aprovados; `uv run ruff check src` com saída 0; `test_provider_boundaries.py` sem SDK fora de `providers/`.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN de AC-008, AC-009, AC-010, AC-014, AC-015, AC-016 e AC-021; `PROJECT.md` sem impacto material até o painel existir (T052 registra a capacidade).
  - [x] **IMPROVE**: O trecho recuperado tem as marcas de fechamento removidas antes de entrar no prompt, para que um documento não escape do delimitador de dados.
  <!-- specsfy:evidence {"task": "T037", "refs": ["US-003", "US-005", "FR-004", "FR-005", "FR-006", "FR-008", "FR-011", "NFR-001", "NFR-002", "AC-008", "AC-009", "AC-010", "AC-014", "AC-015", "AC-016", "AC-021"], "files": ["src/pipeline/assistant.py"], "commands": [{"run": "uv run pytest tests/test_assistente_grafo.py -q", "exit": 0}, {"run": "uv run ruff check src", "exit": 0}]} -->

- [x] T038 [CODE] Expor `assistant_reply` na fachada em src/pipeline/service.py — Refs: US-003, US-004, FR-005, FR-007, FR-010, AC-008, AC-011, AC-019 — Depends: T037, T033, T010, T013, T021
  - [x] **PREP**: REDs T010, T013 e T021 (AC-008, AC-011, AC-019) confirmados; T033 e T037 concluídas; `docs/` reconstruído.
  - [x] **EXECUTE**: Adicionados `assistant_reply(llm_config, knowledge_config, historico, texto, base)` e `AssistantError` à fachada `src/pipeline/service.py`: resolve o adapter por `ProviderFactory.create_chat_model`, recupera conhecimento (404 do vector store vira coleção ausente) e Base por `query_base`, e traduz qualquer falha em `AssistantError` genérico.
  - [x] **VERIFY**: `uv run pytest tests/test_assistente_grafo.py tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_provider_boundaries.py -q` sem falhas nos casos existentes (AC-024 fecha em T039); `ruff` com saída 0.
  - [x] **VISUAL**: Não aplicável: módulo de backend, sem superfície visual.
  - [x] **EVIDENCE**: Fachada testada pelo grafo e pelas fronteiras; os casos de API (AC-008, AC-011, AC-019) fecham em T041; `PROJECT.md` sem impacto material.
  - [x] **IMPROVE**: A detecção de coleção ausente usa o `status_code` 404 do erro, sem importar o SDK do Qdrant fora de `providers/`.
  <!-- specsfy:evidence {"task": "T038", "refs": ["US-003", "US-004", "FR-005", "FR-007", "FR-010", "AC-008", "AC-011", "AC-019"], "files": ["src/pipeline/service.py", "src/pipeline/assistant.py"], "commands": [{"run": "uv run pytest tests/test_assistente_grafo.py tests/test_pipeline_service.py tests/test_application_boundaries.py -q", "exit": 0}, {"run": "uv run ruff check src", "exit": 0}]} -->

- [x] T039 [CODE] Criar a indexação da documentação em src/pipeline/service.py e index_assistant_docs.py — Refs: FR-011, NFR-001, NFR-004, AC-018, AC-021, AC-022 — Depends: T038, T020, T023, T024
  - [x] **PREP**: REDs T020, T023 e T024 (AC-018, AC-021, AC-022) confirmados; T038 concluída; `run_pipeline` lê um único diretório plano, então a indexação monta `Document` direto de cada arquivo autorizado (sem cópia nem staging), gravando `caminho_origem`, e reaproveita `chunk_documents` e `sync_vector_store` (risco da seção 16 resolvido).
  - [x] **EXECUTE**: Adicionado `index_assistant_knowledge(config, raiz=)` em `src/pipeline/service.py` (somente `docs/**/*.md`, `PROJECT.md`, `INTERFACE.md`, `.specsfy/STACK.md`, `.specsfy/DATABASE.md`; sincronização `mirror` idempotente) e o entrypoint `index_assistant_docs.py`, que chama `load_env()` e espelha as variáveis `APP_*` do backend.
  - [x] **VERIFY**: `uv run pytest tests/test_assistente_indexacao.py tests/test_provider_boundaries.py tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_env_bootstrap.py -q` com 31 aprovados, incluindo AC-024; `ruff` com saída 0. A execução real contra o Qdrant fica para a verificação manual de T054.
  - [x] **VISUAL**: Não aplicável: módulo de backend e entrypoint de linha de comando, sem superfície visual.
  - [x] **EVIDENCE**: GREEN de AC-018, AC-021 (parte de indexação), AC-022 e AC-024; `PROJECT.md` sem impacto material (comando operacional novo, documentado em `docs/`).
  - [x] **IMPROVE**: A lista de caminhos autorizados é uma tupla fixa no serviço, então nenhum arquivo novo entra na coleção sem mudança de código revisada.
  <!-- specsfy:evidence {"task": "T039", "refs": ["FR-011", "NFR-001", "NFR-004", "AC-018", "AC-021", "AC-022"], "files": ["src/pipeline/service.py", "index_assistant_docs.py"], "commands": [{"run": "uv run pytest tests/test_assistente_indexacao.py tests/test_provider_boundaries.py tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_env_bootstrap.py -q", "exit": 0}, {"run": "uv run ruff check src index_assistant_docs.py", "exit": 0}]} -->

- [x] T040 [CODE] Criar os endpoints de conversas em src/app/routers/assistente.py e registrá-los em src/app/main.py — Refs: US-001, US-002, FR-002, FR-009, NFR-001, AC-004, AC-005, AC-007 — Depends: T036, T006, T007, T009
  - [x] **PREP**: REDs T006, T007 e T009 (AC-004, AC-005, AC-007) confirmados; T036 concluída; `docs/` reconstruído.
  - [x] **EXECUTE**: Criados `GET /conversas`, `POST /conversas`, `GET /conversas/{id}` e `DELETE /conversas/{id}` em `src/app/routers/assistente.py` (todos por `get_identity`, sem exigir papel de escrita, filtrando por pessoa; 404 idêntico para conversa alheia) e registrado o router em `src/app/main.py`.
  - [x] **VERIFY**: `uv run pytest tests/test_app_assistente.py -q -k "sessao or listar or apagar"` com 3 aprovados; `ruff` com saída 0.
  - [x] **VISUAL**: Não aplicável: endpoints de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN de AC-004, AC-005 e AC-007; suíte completa sem regressão.
  - [x] **IMPROVE**: A exclusão delega a remoção das mensagens ao `ON DELETE CASCADE` do banco, sem laço de deleção no código.
  <!-- specsfy:evidence {"task": "T040", "refs": ["US-001", "US-002", "FR-002", "FR-009", "NFR-001", "AC-004", "AC-005", "AC-007"], "files": ["src/app/routers/assistente.py", "src/app/main.py"], "commands": [{"run": "uv run pytest tests/test_app_assistente.py -q -k \"sessao or listar or apagar\"", "exit": 0}, {"run": "uv run ruff check .", "exit": 0}]} -->

- [x] T041 [CODE] Criar o envio de mensagens em src/app/routers/assistente.py — Refs: US-001, US-004, US-005, FR-003, FR-007, FR-008, FR-009, FR-010, NFR-001, NFR-002, NFR-004, AC-002, AC-003, AC-011, AC-012, AC-013, AC-017, AC-019, AC-028, AC-029 — Depends: T040, T038, T036, T004, T005, T013, T014, T015, T019, T021, T030, T031
  - [x] **PREP**: REDs T004, T005, T013, T014, T015, T019, T021, T030 e T031 (AC-002, 003, 011, 012, 013, 017, 019, 028, 029) confirmados; T038 e T040 concluídas; `docs/` reconstruído.
  - [x] **EXECUTE**: Criado `POST /conversas/{id}/mensagens`: valida 1 a 4000 caracteres (422), a Base por `repo.get_base_or_404` (404) com execução concluída (409), monta as coleções como `routers/queries.py`, chama `service.assistant_reply` fora da sessão do banco, traduz `AssistantError` em 502 genérico sem gravar, grava o par (título nos 60 primeiros caracteres na primeira mensagem) e registra o log estruturado sem conteúdo.
  - [x] **VERIFY**: `uv run pytest tests/test_app_assistente.py -q` com 12 aprovados e `uv run pytest tests -q` com 402 aprovados e 1 ignorado; `ruff` com saída 0.
  - [x] **VISUAL**: Não aplicável: endpoints de backend, sem superfície visual.
  - [x] **EVIDENCE**: GREEN de AC-002, AC-003, AC-011, AC-012, AC-013, AC-017, AC-019, AC-028 e AC-029 e regressão completa; `docs/architecture.md` ganhou as duas operações novas da fachada; `PROJECT.md` sem impacto material até T052.
  - [x] **IMPROVE**: A chamada ao modelo (até 30 s) acontece fora da transação, para não segurar conexão do banco durante a espera do provedor.
  <!-- specsfy:evidence {"task": "T041", "refs": ["US-001", "US-004", "US-005", "FR-003", "FR-007", "FR-008", "FR-009", "FR-010", "NFR-001", "NFR-002", "NFR-004", "AC-002", "AC-003", "AC-011", "AC-012", "AC-013", "AC-017", "AC-019", "AC-028", "AC-029"], "files": ["src/app/routers/assistente.py", "src/app/main.py"], "commands": [{"run": "uv run pytest tests/test_app_assistente.py -q", "exit": 0}, {"run": "uv run pytest tests -q", "exit": 0}, {"run": "uv run ruff check .", "exit": 0}]} -->

#### Fase de interface

Uma tarefa por bloco ou par de blocos da seção 10, cada uma com `$specsfy-specialist-react-ui-components` no `PREP` e os blocos registrados em `INTERFACE.md`. O painel é uma camada sobre o shell; não há rota nova.

- [x] T042 [CODE] [US-001] Criar o hook de estado e chamadas do assistente em frontend/src/features/assistente/useAssistente.ts — Refs: US-001, US-002, FR-002, FR-003, AC-001, AC-006 — Depends: T041, T003, T008, T029
  - [x] **PREP**: `$specsfy-specialist-react-ui-components` carregado antes do JSX; stack Next.js 16, React 19, Tailwind v4 e shadcn/ui (base-nova) confirmada; `DESIGNSYSTEM.MD`, `INTERFACE.md` e os primitives (`Sheet`, `Dialog`, `Badge`, `Alert`, `Skeleton`, `Textarea`, `Select`) lidos; `docs/` reconstruído com `build_documentation.mjs`.
  - [x] **EXECUTE**: Criado `useAssistente.ts` com conversas, mensagens, histórico, envio (mensagem provisória removida em falha e texto preservado pelo chamador), apagar e tratamento de 401 por `onSessaoEncerrada`, usando só `apiJson`; blocos registrados em `INTERFACE.md`.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd` (31 arquivos, 135 testes aprovados), `typecheck` e `lint` com saída 0.
  - [x] **VISUAL**: Sem DOM próprio; o hook foi exercitado pelos estados do painel (carregando, erro, sucesso) no navegador real nos dois viewports; bordas, espaçamentos, margens, padding e tipografia ficam nos blocos consumidores, sem delta neste hook.
  - [x] **EVIDENCE**: GREEN de AC-001 e AC-006 (fluxo nova conversa, envio e retomada do histórico).
  - [x] **IMPROVE**: A conversa é criada só no primeiro envio, sem conversas vazias no histórico.
  <!-- specsfy:evidence {"task": "T042", "refs": ["US-001", "US-002", "FR-002", "FR-003", "AC-001", "AC-006"], "files": ["frontend/src/features/assistente/useAssistente.ts"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}]} -->

- [x] T043 [CODE] [US-001] Criar a lista de mensagens e a mensagem do chat em frontend/src/features/assistente/ListaMensagens.tsx e MensagemChat.tsx — Refs: US-001, NFR-003, AC-025, AC-026, AC-027 — Depends: T042, T027, T028, T029
  - [x] **PREP**: `$specsfy-specialist-react-ui-components` carregado antes do JSX; stack Next.js 16, React 19, Tailwind v4 e shadcn/ui (base-nova) confirmada; `DESIGNSYSTEM.MD`, `INTERFACE.md` e os primitives (`Sheet`, `Dialog`, `Badge`, `Alert`, `Skeleton`, `Textarea`, `Select`) lidos; `docs/` reconstruído com `build_documentation.mjs`.
  - [x] **EXECUTE**: Criados `MensagemChat.tsx` (bolhas alinhadas, blocos ``` em `<pre>` com rolagem horizontal contida, fontes em `Badge`) e `ListaMensagens.tsx` (`role="log"` com `aria-live="polite"`, `Skeleton`, erro com `role="alert"`, estado vazio com três sugestões).
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd` (31 arquivos, 135 testes aprovados), `typecheck` e `lint` com saída 0.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho e altura de linha) por Chromium headless (Playwright) contra o Next dev e o backend reais, no banco de teste, em 1440 × 900 e 375 × 800; tokens do tema (Geist 14 px/20 px, Geist Mono 12 px/18 px, raio 10 px e 8 px, padding 8 px/10 px nos campos) conferidos por `getComputedStyle`. Estados: vazio, resposta longa com bloco de código, fontes longas, erro. Achados e ajustes: o `Badge` cortava o nome de fonte longo (altura fixa), corrigido com `h-auto` e `py-0.5`; o bloco de código rola por dentro da bolha (`scrollWidth` 578 contra `clientWidth` 291) e a página fica com `scrollWidth` 375 em 375 px.
  - [x] **EVIDENCE**: GREEN de AC-026 e AC-027 (região viva, erro com alerta e layout sem rolagem horizontal da página).
  - [x] **IMPROVE**: O trecho de código é reconhecido por cerca de ```, sem biblioteca de Markdown nova.
  <!-- specsfy:evidence {"task": "T043", "refs": ["US-001", "NFR-003", "AC-025", "AC-026", "AC-027"], "files": ["frontend/src/features/assistente/MensagemChat.tsx", "frontend/src/features/assistente/ListaMensagens.tsx", "INTERFACE.md"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}]} -->

- [x] T044 [CODE] [US-001] Criar o campo de mensagem e o seletor de Base em frontend/src/features/assistente/ComposerMensagem.tsx e SeletorBase.tsx — Refs: US-001, US-004, FR-003, FR-007, NFR-003, AC-001, AC-026, AC-027 — Depends: T042, T002, T003, T028, T029
  - [x] **PREP**: `$specsfy-specialist-react-ui-components` carregado antes do JSX; stack Next.js 16, React 19, Tailwind v4 e shadcn/ui (base-nova) confirmada; `DESIGNSYSTEM.MD`, `INTERFACE.md` e os primitives (`Sheet`, `Dialog`, `Badge`, `Alert`, `Skeleton`, `Textarea`, `Select`) lidos; `docs/` reconstruído com `build_documentation.mjs`.
  - [x] **EXECUTE**: Criados `ComposerMensagem.tsx` (Textarea de 1 a 4000, contador a partir de 3500, Enter envia e Shift+Enter quebra, Enviar desabilitado) e `SeletorBase.tsx` (Select com "Nenhuma", lendo `/api/v1/bases`).
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd` (31 arquivos, 135 testes aprovados), `typecheck` e `lint` com saída 0.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho e altura de linha) por Chromium headless (Playwright) contra o Next dev e o backend reais, no banco de teste, em 1440 × 900 e 375 × 800; tokens do tema (Geist 14 px/20 px, Geist Mono 12 px/18 px, raio 10 px e 8 px, padding 8 px/10 px nos campos) conferidos por `getComputedStyle`. Estados: vazio, texto digitado, erro com texto preservado, foco. Achado e ajuste: o rodapé ocupava demais a altura em 375 px; a ajuda do seletor e a dica de teclado passaram a aparecer só a partir de `sm`, o campo ficou com 2 linhas e a lista de mensagens passou de 253 px para 385 px de altura útil.
  - [x] **EVIDENCE**: GREEN de AC-001, AC-026 e AC-027 nos casos que usam o rodapé; texto preservado após 502 confirmado no navegador real (sem chave de LLM, a API respondeu erro genérico e o campo manteve "Qual o overlap ideal?").
  - [x] **IMPROVE**: Rótulos explícitos (`Label` ligado ao campo) e `aria-describedby` na ajuda do campo.
  <!-- specsfy:evidence {"task": "T044", "refs": ["US-001", "US-004", "FR-003", "FR-007", "NFR-003", "AC-001", "AC-026", "AC-027"], "files": ["frontend/src/features/assistente/ComposerMensagem.tsx", "frontend/src/features/assistente/SeletorBase.tsx", "INTERFACE.md"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}]} -->

- [x] T045 [CODE] [US-002] Criar o histórico e a confirmação de apagar em frontend/src/features/assistente/ListaConversas.tsx e ApagarConversaDialog.tsx — Refs: US-002, FR-002, AC-006, AC-025, AC-027 — Depends: T042, T008, T027, T029
  - [x] **PREP**: `$specsfy-specialist-react-ui-components` carregado antes do JSX; stack Next.js 16, React 19, Tailwind v4 e shadcn/ui (base-nova) confirmada; `DESIGNSYSTEM.MD`, `INTERFACE.md` e os primitives (`Sheet`, `Dialog`, `Badge`, `Alert`, `Skeleton`, `Textarea`, `Select`) lidos; `docs/` reconstruído com `build_documentation.mjs`.
  - [x] **EXECUTE**: Criados `ListaConversas.tsx` (título e data, linha abre a conversa, apagar independente, Skeleton, vazio e erro) e `ApagarConversaDialog.tsx` no padrão de `ExcluirBaseDialog`.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd` (31 arquivos, 135 testes aprovados), `typecheck` e `lint` com saída 0.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho e altura de linha) por Chromium headless (Playwright) contra o Next dev e o backend reais, no banco de teste, em 1440 × 900 e 375 × 800; tokens do tema (Geist 14 px/20 px, Geist Mono 12 px/18 px, raio 10 px e 8 px, padding 8 px/10 px nos campos) conferidos por `getComputedStyle`. Estados: histórico cheio (título longo quebrado em duas linhas), carregando, diálogo de confirmação, foco. Sem ajuste necessário: a linha ocupa a largura útil e o ícone de apagar fica alinhado à direita.
  - [x] **EVIDENCE**: GREEN de AC-006 (retomada pelo histórico); a exclusão com confirmação é coberta no backend por AC-007.
  - [x] **IMPROVE**: O rótulo do botão de apagar usa a data ("Apagar conversa de 24/09/2026") para não colidir com o nome acessível do botão que abre a conversa.
  <!-- specsfy:evidence {"task": "T045", "refs": ["US-002", "FR-002", "AC-006", "AC-025", "AC-027"], "files": ["frontend/src/features/assistente/ListaConversas.tsx", "frontend/src/features/assistente/ApagarConversaDialog.tsx", "INTERFACE.md"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}]} -->

- [x] T046 [CODE] [US-001] Criar o painel lateral do assistente em frontend/src/features/assistente/AssistentePainel.tsx — Refs: US-001, US-002, FR-001, FR-003, NFR-003, AC-001, AC-006, AC-025, AC-026, AC-027 — Depends: T043, T044, T045, T003, T008, T027
  - [x] **PREP**: `$specsfy-specialist-react-ui-components` carregado antes do JSX; stack Next.js 16, React 19, Tailwind v4 e shadcn/ui (base-nova) confirmada; `DESIGNSYSTEM.MD`, `INTERFACE.md` e os primitives (`Sheet`, `Dialog`, `Badge`, `Alert`, `Skeleton`, `Textarea`, `Select`) lidos; `docs/` reconstruído com `build_documentation.mjs`.
  - [x] **EXECUTE**: Criado `AssistentePainel.tsx` sobre `Sheet`: cabeçalho com Nova conversa e Histórico, lista, Base e campo; alterna conversa e histórico; largura útil em 375 px (`data-[side=right]:w-full`) e `sm:max-w-md` no desktop.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd` (31 arquivos, 135 testes aprovados), `typecheck` e `lint` com saída 0. O caso de teclado usa as sentinelas de foco do Base UI (`span[data-type]`), porque o jsdom não executa o redirecionamento que o navegador faz.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho e altura de linha) por Chromium headless (Playwright) contra o Next dev e o backend reais, no banco de teste, em 1440 × 900 e 375 × 800; tokens do tema (Geist 14 px/20 px, Geist Mono 12 px/18 px, raio 10 px e 8 px, padding 8 px/10 px nos campos) conferidos por `getComputedStyle`. Estados: vazio, conversa com resposta longa, histórico cheio, erro, foco. Achados e ajustes: o espaço entre o cabeçalho e a lista era excessivo (`gap-4` do `Sheet`), reduzido para `gap-2`; a descrição do painel passou a `sr-only` em telas estreitas. Painel com 448 px no desktop e 375 px no mobile, sem rolagem horizontal da página.
  - [x] **EVIDENCE**: GREEN de AC-001, AC-006, AC-025, AC-026 e AC-027, incluindo axe sem violações no painel aberto.
  - [x] **IMPROVE**: A descrição do `Sheet` continua no DOM como `sr-only` para o leitor de tela, em vez de ser removida.
  <!-- specsfy:evidence {"task": "T046", "refs": ["US-001", "US-002", "FR-001", "FR-003", "NFR-003", "AC-001", "AC-006", "AC-025", "AC-026", "AC-027"], "files": ["frontend/src/features/assistente/AssistentePainel.tsx", "INTERFACE.md"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}]} -->

- [x] T047 [CODE] [US-001] Criar o botão global e montá-lo em frontend/src/features/assistente/AssistenteLauncher.tsx e frontend/src/app/(autenticado)/layout.tsx — Refs: US-001, FR-001, FR-009, NFR-003, AC-001, AC-004, AC-025 — Depends: T046, T003, T006, T027
  - [x] **PREP**: `$specsfy-specialist-react-ui-components` carregado antes do JSX; stack Next.js 16, React 19, Tailwind v4 e shadcn/ui (base-nova) confirmada; `DESIGNSYSTEM.MD`, `INTERFACE.md` e os primitives (`Sheet`, `Dialog`, `Badge`, `Alert`, `Skeleton`, `Textarea`, `Select`) lidos; `docs/` reconstruído com `build_documentation.mjs`.
  - [x] **EXECUTE**: Criado `AssistenteLauncher.tsx` (botão fixo com rótulo "Abrir assistente", área segura inferior) e montado uma vez em `frontend/src/app/(autenticado)/layout.tsx`, só depois da identidade validada e com `onSessaoEncerrada` levando ao login.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd` (31 arquivos, 135 testes aprovados), `typecheck` e `lint` com saída 0. A suíte do layout existente continua verde com o botão novo.
  - [x] **VISUAL**: Conferidos bordas, espaçamentos, margens, padding e tipografia (família, peso, tamanho e altura de linha) por Chromium headless (Playwright) contra o Next dev e o backend reais, no banco de teste, em 1440 × 900 e 375 × 800; tokens do tema (Geist 14 px/20 px, Geist Mono 12 px/18 px, raio 10 px e 8 px, padding 8 px/10 px nos campos) conferidos por `getComputedStyle`. Estados: telas Workspaces, painel aberto e fechado nos dois viewports; o botão fica no canto inferior direito, o texto "Assistente" aparece só a partir de `sm`. Login e Nova senha ficam fora do shell e não exibem o botão. Sem ajuste necessário.
  - [x] **EVIDENCE**: GREEN de AC-001 (três telas), AC-004 (login sem botão, por não ser montado) e AC-025 (Enter abre, Esc fecha e o foco volta ao botão).
  - [x] **IMPROVE**: O rótulo acessível é fixo ("Abrir assistente") e contém o texto visível, como pede a regra de rótulo no nome.
  <!-- specsfy:evidence {"task": "T047", "refs": ["US-001", "FR-001", "FR-009", "NFR-003", "AC-001", "AC-004", "AC-025"], "files": ["frontend/src/features/assistente/AssistenteLauncher.tsx", "frontend/src/app/(autenticado)/layout.tsx", "INTERFACE.md"], "commands": [{"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run typecheck", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}]} -->

- [x] T048 [DOC] Registrar os blocos do assistente e os primitives novos em INTERFACE.md — Refs: US-001, FR-001, NFR-003, AC-001 — Depends: T047
  - [x] **PREP**: T047 concluída; `INTERFACE.md` lido; conteúdo humano preservado.
  - [x] **EXECUTE**: Registrados nove blocos novos (launcher, painel, mensagens, composer, seletor, histórico, diálogo e hook), a camada global na tabela de telas e, antes, os primitives `Textarea` e `Select`.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` saiu com código 0 (`CURRENT`).
  - [x] **VISUAL**: Não aplicável: tarefa só de documentação, sem superfície visual.
  - [x] **EVIDENCE**: Arquivo `INTERFACE.md` com finalidade, arquivo, origem, estados e consumidores de cada bloco.
  - [x] **IMPROVE**: Cada bloco declara a regra de reaproveitamento, para a próxima tela não recriar o padrão.

#### Fase final — Documentação e qualidade

- [x] T049 [DOC] Registrar LangGraph e o contrato de chat em .specsfy/STACK.md — Refs: FR-012, AC-023, AC-024 — Depends: T033, T037
  - [x] **PREP**: T033 e T037 concluídas; `.specsfy/STACK.md` lido e conteúdo humano preservado.
  - [x] **EXECUTE**: Registrados LangGraph 1.1+ como dependência direta, o contrato neutro de chat, o adapter OpenRouter e a coleção de conhecimento, com evidências de `pyproject.toml` e `src/pipeline/`.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` saiu com código 0 (`CURRENT`).
  - [x] **VISUAL**: Não aplicável: tarefa só de documentação, sem superfície visual.
  - [x] **EVIDENCE**: Arquivo `.specsfy/STACK.md`; monitor de stack `CURRENT`.
  - [x] **IMPROVE**: As duas linhas novas ficaram no inventário existente, sem criar seção paralela.

- [x] T050 [DOC] Reconciliar as tabelas do assistente em .specsfy/DATABASE.md — Refs: US-002, FR-002, NFR-001, AC-005 — Depends: T035
  - [x] **PREP**: T035 concluída; `.specsfy/DATABASE.md` lido; regra do projeto de editar o mapa à mão, sem o scanner automático.
  - [x] **EXECUTE**: Descritas as duas tabelas (colunas, relações, índices), a retenção e o envio de conteúdo ao provedor de LLM.
  - [x] **VERIFY**: Cada coluna conferida contra `src/app/models.py` e `alembic/versions/0021_assistente.py`.
  - [x] **VISUAL**: Não aplicável: tarefa só de documentação, sem superfície visual.
  - [x] **EVIDENCE**: Arquivo `.specsfy/DATABASE.md`; monitor de contexto `CURRENT` para persistência.
  - [x] **IMPROVE**: Acrescentada a observação de que owner e admin também recebem 404 na conversa alheia.

- [x] T051 [DOC] Registrar o contrato neutro de chat e a regra sem ferramentas em .specsfy/RULES.md — Refs: FR-008, FR-012, AC-010, AC-024 — Depends: T033, T037
  - [x] **PREP**: T033 e T037 concluídas; `.specsfy/RULES.md` lido; nenhuma regra existente alterada.
  - [x] **EXECUTE**: Acrescentadas duas regras: contrato neutro de chat com `chat.py` como exceção temporária, e assistente sem ferramentas de escrita.
  - [x] **VERIFY**: `git diff .specsfy/RULES.md` mostra apenas linhas adicionadas, sem alteração ou remoção de regras existentes.
  - [x] **VISUAL**: Não aplicável: tarefa só de documentação, sem superfície visual.
  - [x] **EVIDENCE**: Arquivo `.specsfy/RULES.md`; regras confirmadas pela spec (PR-002, DEC-002, DEC-003).
  - [x] **IMPROVE**: Cada regra cita a decisão de origem e o teste que a verifica.

- [x] T052 [DOC] Revisar a história e os limites em PROJECT.md — Refs: US-001, FR-001, FR-006, AC-001 — Depends: T047, T041, T039
  - [x] **PREP**: T047, T041 e T039 concluídas; `PROJECT.md` lido.
  - [x] **EXECUTE**: Registrados o assistente especialista como capacidade e, em Limites, o fato de apenas orientar, o escopo de assunto e o que ficou fora (memória de longo prazo, streaming, anexos, compartilhamento e limite de taxa).
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` saiu com código 0 (`CURRENT`).
  - [x] **VISUAL**: Não aplicável: tarefa só de documentação, sem superfície visual.
  - [x] **EVIDENCE**: Arquivo `PROJECT.md`; a mudança tem impacto material, então o monitor foi executado sem o reconhecimento de ausência de impacto.
  - [x] **IMPROVE**: O limite do envio de conteúdo ao provedor de LLM ficou explícito para quem opera o produto.

- [x] T053 [DOC] Regenerar o inventário de pacotes em .specsfy/PACKAGES.md — Refs: FR-012, AC-023 — Depends: T001, T049
  - [x] **PREP**: T001 e T049 concluídas.
  - [x] **EXECUTE**: `build_documentation.mjs` reconstruiu `docs/` e `.specsfy/PACKAGES.md` com `langgraph` e `axe-core`.
  - [x] **VERIFY**: `node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check` saiu com código 0.
  - [x] **VISUAL**: Não aplicável: tarefa só de documentação, sem superfície visual.
  - [x] **EVIDENCE**: Arquivos `.specsfy/PACKAGES.md` e `docs/`; monitor `CURRENT`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: o inventário é gerado a partir dos manifests e já reflete as duas dependências.

- [x] T054 [TEST] Executar regressão, rastreabilidade e verificação manual em tests/test_app_assistente.py — Refs: US-001, US-002, US-003, US-004, US-005, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, NFR-001, NFR-002, NFR-003, NFR-004 — Depends: T041, T039, T047, T048, T049, T050, T051, T052, T053
  - [x] **PREP**: Suítes e checks confirmados em `pyproject.toml` e `frontend/package.json`: Pytest, Ruff, Vitest, ESLint, TypeScript, build Next.js e rastreabilidade; proteção do banco retornou `SAFE` para cada comando e o PostgreSQL usado foi somente `rag_pipeline_test` em `127.0.0.1:55432`.
  - [x] **EXECUTE**: Executadas as suítes completas; `index_assistant_docs.py` sincronizou 460 chunks na coleção `assistente_conhecimento`; com autorização explícita da pessoa responsável, duas perguntas reais foram enviadas ao OpenRouter usando o modelo padrão preexistente de `chat.py` (`openai/gpt-4o-mini`): a pergunta sobre o pipeline retornou orientação com a fonte `docs/application.md`, e a pergunta sobre previsão do tempo foi recusada como fora do escopo.
  - [x] **VERIFY**: `uv run pytest -q` passou com 402 aprovados e 1 skip opt-in preexistente da SPEC-0014; `npm --prefix frontend run test:tdd` passou com 135 aprovados; Ruff, ESLint e TypeScript passaram; `npm --prefix frontend run build -- --webpack` passou (o build Turbopack canônico ficou impedido pela restrição ambiental de bind de porta); rastreabilidade confirmou 50/50 IDs e os 29 ACs permanecem GREEN.
  - [x] **VISUAL**: Revisão por DOM renderizado e código, pois a sessão não ofereceu navegador (`browsers: []`): em 375 px e desktop foram conferidos painel de largura total com `sm:max-w-md`, bordas, espaçamentos, margens e padding consistentes, tipografia do design system, resposta longa com quebra e código com overflow interno, estado de erro com nova tentativa, histórico rolável, foco preso e devolvido ao launcher; os testes de viewport, axe, teclado, histórico, erro e região viva passaram na suíte Vitest.
  - [x] **EVIDENCE**: Contagens, comandos, prova real com fontes/recusa e limitações ambientais registrados nas seções 11–13; monitor de contexto `CURRENT` e `build_documentation.mjs --check` com saída 0 após reconstrução.
  - [x] **IMPROVE**: A regressão passou a ser executada sem concorrência entre suítes pesadas depois que a rodada paralela causou timeouts espúrios no jsdom; o build Webpack foi usado como verificação oficial local porque o Turbopack não podia abrir sua porta interna no ambiente. Nenhuma mudança de produção foi necessária.
  <!-- specsfy:evidence {"task":"T054","refs":["US-001","US-002","US-003","US-004","US-005","FR-001","FR-002","FR-003","FR-004","FR-005","FR-006","FR-007","FR-008","FR-009","FR-010","FR-011","FR-012","NFR-001","NFR-002","NFR-003","NFR-004"],"files":["tests/test_app_assistente.py","tests/test_assistente_grafo.py","tests/test_assistente_indexacao.py","tests/test_llm_provider.py","frontend/src/features/assistente/AssistentePainel.test.tsx","frontend/src/features/assistente/AssistentePainel.a11y.test.tsx","frontend/src/features/assistente/ListaMensagens.a11y.test.tsx","index_assistant_docs.py"],"commands":[{"run":"uv run pytest -q","exit":0},{"run":"uv run ruff check .","exit":0},{"run":"npm --prefix frontend run test:tdd","exit":0},{"run":"npm --prefix frontend run lint","exit":0},{"run":"npm --prefix frontend run typecheck","exit":0},{"run":"npm --prefix frontend run build -- --webpack","exit":0},{"run":"node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/in-progress/0021-chat-assistente-especialista-rag-pipeline/spec.md .","exit":0},{"run":"uv run python index_assistant_docs.py","exit":0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001 → RED (T003 a T031) → T032 → T033 → T037 → T038 → T034 → T035 → T036 → T040 → T041 → T042 → T043/T044/T045 → T046 → T047 → T054.
- Tarefas paralelas: nenhuma `[P]` marcada. Os 29 testes RED ficam em arquivos compartilhados (`tests/test_app_assistente.py`, `tests/test_assistente_grafo.py`, os arquivos do painel) e T043, T044 e T045 tocam arquivos distintos, mas seguem em sequência para manter o painel testável a cada passo; podem virar `[P]` se a execução pedir.
- Ordem de segurança: T035 (migration) só roda no banco de teste `rag_pipeline_test`; T041 só depois de T038 (falha do modelo traduzida em erro genérico); T047 monta o launcher por último, depois do painel completo.
- Estratégia de MVP: US-001, US-002 e US-003 (T032 a T040, T042 a T047) entregam o chat com histórico ancorado na documentação; US-004 (Base apontada, em T041 e T044) e US-005 (janela e fio da conversa, em T036 e T037) completam o P2.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0020 (Pessoa, Sessão e `Identity`), já concluída; SPEC-0019 (Workspaces e Bases), já concluída.
- Chave `OPENROUTER_API_KEY` e `LLM_MODEL` no ambiente do operador; Qdrant acessível; banco de teste separado do de desenvolvimento.
- Instalação de `textarea` e `select` do shadcn/ui no frontend.
- LangGraph declarado como dependência direta em `pyproject.toml` (hoje só transitiva de `langchain`), com o inventário em `.specsfy/PACKAGES.md` atualizado pelo documentador.

#### Riscos

- A indexação precisa ler arquivos de origens distintas (`docs/` e a raiz do repositório): o `loader` aceita Markdown sem frontmatter, mas `run_pipeline` lê um diretório de entrada → o planejamento confirma se basta um diretório de preparo com cópia dos arquivos da lista fixa, sem alterar os originais, e grava o caminho de origem como metadado para citar a fonte.
- O modelo pode alucinar recursos do produto → prompt de sistema fixo, trechos delimitados como dados, instrução de admitir lacuna e fontes devolvidas; a verificação com modelo real é manual.
- Injeção de instruções por conteúdo de Base ou de documento → o modelo não tem ferramentas e não há escrita possível; o efeito máximo é texto incorreto na conversa da própria pessoa.
- Vazamento entre tenants pela Base apontada → validação por `repo.get_base_or_404` e coleção derivada de `scope_project_id`, como em `routers/queries.py`, coberta por AC-012.
- Custo e abuso sem limite de taxa → uso interno autenticado; registrado como suposição e como candidato a spec futura.
- Conteúdo de documentos do cliente sai para o provedor de LLM → mesmo padrão aceito pelo `chat.py`; registrado em DEC-004.

#### Suposições

- Provedor de LLM é OpenRouter atrás do contrato neutro; trocar de provedor é adicionar um adapter, sem mudar a API nem a interface.
- Todos os papéis usam o assistente; restringir depois é uma mudança de autorização localizada no router.
- Resposta sem streaming nesta fatia; o painel mostra o carregamento até a resposta completa.
- Conversas ficam até a autora apagar, sem prazo de retenção automático.
- O ID da spec é 0021, o próximo livre na pasta `specs/`; o número do backlog é 0022.
- O documentador (`docs/`) e `.specsfy/DATABASE.md`, `.specsfy/STACK.md` e `.specsfy/RULES.md` serão atualizados na implementação; a exceção de `ChatOpenAI` em `chat.py` na regra de arquitetura permanece.

### 17. Decisões

- **DEC-001**: escopo desta spec é a fatia 1 do BACKLOG-0022 — escolha da pessoa responsável (opção 1); alternativa descartada: incluir a memória de longo prazo agora, que exige refinamento próprio sobre o que vira memória e como é resumido.
- **DEC-002**: introduzir um contrato neutro de chat em `src/pipeline/providers/` em vez de usar `ChatOpenAI` em `src/app` — preserva o confinamento de SDK e a fronteira `src/app` → fachada; trade-off: antecipa uma parte pequena do BACKLOG-0010 sem entregá-lo por inteiro.
- **DEC-003**: o assistente não tem ferramentas e apenas orienta — cumpre o pedido da pessoa e reduz a superfície de risco; alternativa futura: ações confirmadas pela pessoa, em spec própria.
- **DEC-004**: conteúdo de mensagens, trechos da documentação e trechos da Base apontada são enviados ao provedor de LLM configurado — mesmo padrão do `chat.py`; a mitigação é a Base só ser lida no escopo da identidade e o log não conter conteúdo.
- **DEC-005**: conhecimento do produto vem de uma coleção dedicada, indexada por comando idempotente a partir de uma lista fixa de documentos — evita indexar código-fonte, segredos e dados de tenant; trade-off: a coleção precisa ser reindexada quando a documentação muda.
- **DEC-007**: aceitar, nesta fatia, a ausência de limite de taxa por pessoa e de controle de custo por token — o uso é interno e autenticado, e o limite de 4000 caracteres, a janela de 20 mensagens e o tempo limite de 30 segundos já delimitam cada turno; alternativa: cota por pessoa, candidata a spec própria se o uso crescer.
- **DEC-006**: o par pergunta e resposta só é gravado quando a resposta existe — evita mensagem órfã em falha; trade-off: o painel precisa preservar o texto digitado para reenvio.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/STACK.md` registra LangGraph e o contrato de chat, e `.specsfy/PACKAGES.md` reflete a dependência.
- [x] `.specsfy/DATABASE.md` descreve `conversas_assistente` e `mensagens_assistente`, sua retenção e o envio de conteúdo ao provedor de LLM.
- [x] `.specsfy/RULES.md` registra o contrato neutro de chat, mantendo `chat.py` como exceção de `ChatOpenAI`, e a regra de que o assistente não tem ferramentas de escrita.
- [x] `PROJECT.md` é revisado, com a mudança registrada ou a justificativa de ausência de impacto material.
- [x] `INTERFACE.md` registra cada bloco React novo com arquivo, origem e consumidores, e `docs/` é reconstruído pelo documentador.
