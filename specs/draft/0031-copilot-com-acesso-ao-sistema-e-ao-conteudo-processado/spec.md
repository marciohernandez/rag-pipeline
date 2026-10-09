# Especificação integrada: Copilot com acesso ao sistema e ao conteúdo processado

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0031 |
| Slug | 0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado |
| Status | Draft |
| Effort | 8 |
| Effort updated at | 2026-10-09 |
| Effort rationale | Amplia o assistente de orientação sobre RAG para um copilot que consulta conteúdo indexado de todas as coleções, estado operacional e conteúdo processado; exige persistência nova no worker, ferramentas de consulta com isolamento por Workspace e papel, fontes clicáveis e mudança no painel existente. Sem ações de escrita. |
| ClickUp Task | |
| Milestones | |
| Definition Gate | Pending |
| Plan Gate | Pending |
| Delivery Gate | Pending |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-09 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O assistente atual (SPEC-0021) só orienta sobre RAG e o pipeline: seu prompt manda recusar qualquer outro assunto e ele só enxerga a documentação fixa do produto e, quando a pessoa escolhe uma coleção, os trechos dela. Ele não consulta o estado do sistema (coleções, documentos, envios, falhas, configurações) nem o que foi processado antes de ir para a base vetorial. Pela formulação da pessoa: "quando escolho a coleção (está como opcional) ele não acessa as informações para responder. Eu quero um assistente (copilot) que tem acesso a todo o sistema, tudo que é feito, inclusive as informações que são processadas para envio à base vetorial. Assim posso perguntar qualquer coisa e ele responde."

O defeito de a coleção selecionada não responder foi reproduzido e corrigido à parte em `fix/assistente-colecao-selecionada` (commit 5d23872): o prompt recusava perguntas sobre o conteúdo por não serem sobre RAG, e as fontes ignoravam os trechos da coleção. Esta spec parte desse comportamento corrigido.

#### Resultado desejado

A pessoa autenticada pergunta pelo chat qualquer coisa sobre o conteúdo indexado de suas coleções, o que foi processado de cada documento e o que acontece no produto, e recebe respostas com fontes clicáveis, limitadas ao Workspace e ao papel dela. O copilot só consulta e sugere o passo; quem executa é a pessoa.

#### Métricas de sucesso

- 100% dos cenários AC-001 a AC-016 passam nos testes automatizados.
- 0 ocorrências de dado de outro Workspace ou de credencial no contexto enviado ao modelo, verificadas por teste de contexto (AC-013, AC-015).
- Toda resposta sustentada por conteúdo traz ao menos uma fonte navegável (AC-001, AC-012).
- Resposta sem base disponível é declarada como não encontrada em 100% dos casos de teste (AC-011).

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: Por que a coleção selecionada não respondia? → O prompt de `src/pipeline/assistant.py` restringia o assunto a RAG; a busca vetorial usa o mesmo escopo da escrita (`scope_colecao`). Corrigido em 5d23872 com teste RED→GREEN em `tests/test_assistente_grafo.py`.
- **R-002**: Onde persistir o conteúdo processado? → `_registrar_documento` em `src/app/tasks.py` recebe os trechos de cada documento após a confirmação do destino; é o ponto único em que a versão do documento é gravada.

#### Fontes e contexto consultados

- `specs/backlog/0038-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado.md` e `.specsfy/DATABASE.md` ("Conteúdo processado do documento da coleção"): decisões da pessoa em 2026-10-09.
- `src/pipeline/assistant.py`, `src/pipeline/service.py::assistant_reply`, `src/app/routers/assistente.py`, `src/app/tasks.py`, `src/app/models.py`, `INTERFACE.md` e `frontend/src/features/assistente/`.
- `specs/completed/0021-chat-assistente-especialista-rag-pipeline/spec.md` e `specs/completed/0030-colecoes-por-workspace-com-envios-acumulados/spec.md`.

#### Documentação consultada

- Nenhuma documentação externa; apenas fontes do repositório.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q1** Que informações o copilot acessa? → **A**: conteúdo das coleções, estado operacional e o material do pipeline antes da publicação.
- **Q2** Como acessar o material anterior à publicação? → **A**: o worker persiste o resultado do processamento.
- **Q3** O que cada pessoa pode ver? → **A**: o que o Workspace e o papel dela já permitem.
- **Q4** O seletor de coleção continua necessário? → **A**: não; vira filtro opcional.
- **Q5** O copilot executa ações? → **A**: não; consulta e sugere o passo.
- **Q6** Por quanto tempo guardar o conteúdo processado? → **A**: enquanto o documento existir, uma versão.
- **Q7** Como mostrar a origem? → **A**: fontes clicáveis em cada resposta.
- **Q8** O relato da coleção selecionada? → **A**: corrigir antes da spec, em branch `fix/`.
- **Q9** O que guardar de cada documento? → **A**: texto convertido e trechos com etiquetas, sem o arquivo original.

#### Dúvidas abertas

- Confirmar com a pessoa a regra de nunca expor credenciais de conexão, nem a admin (hoje é inferência, registrada em FR-011 e DEC-006).
- Confirmar o prazo-alvo de resposta do turno com busca em várias coleções (NFR-002 usa um alvo suposto).
- Definir quais dados "restritos a admin" o copilot reconhece além das configurações de conexão (AC-014).

### 3. Escopo e atores

#### Incluído

- Busca no conteúdo indexado de todas as coleções do Workspace, sem exigir seleção; o seletor passa a ser um filtro opcional.
- Consulta ao estado operacional: coleções, documentos, envios (situação, etapa, contagens e erro seguro), execuções e configurações não secretas.
- Persistência, pelo worker, do texto convertido e dos trechos com etiquetas de cada documento (uma versão por documento).
- Respostas com fontes clicáveis, "não encontrei" quando não houver base e sugestão do passo com link para a tela.
- Isolamento por Workspace e papel, e exclusão de credenciais do contexto.

#### Fora de escopo

- Ações de escrita pelo copilot (criar, apagar, repetir envio, alterar configuração).
- Memória de longo prazo entre conversas (BACKLOG-0027).
- Histórico de versões substituídas do conteúdo processado e prazo fixo de retenção.
- Guardar o arquivo original (continua só no armazenamento do envio).
- Preenchimento retroativo do conteúdo processado de documentos já enviados antes desta entrega.

#### Atores

- **Pessoa admin ou member autenticada**: pergunta pelo chat; vê somente o que seu Workspace e papel permitem.
- **Worker de envio**: grava o conteúdo processado de cada documento após a confirmação do destino.
- **Copilot (modelo de linguagem)**: recebe somente contexto já filtrado pela identidade; não executa ações.

### 4. Princípios e restrições do projeto

- **PR-001**: O copilot não recebe ferramentas de escrita; nenhum nó altera estado fora do próprio grafo (herda a restrição da SPEC-0021).
- **PR-002**: Toda consulta nasce da identidade (tenant, projeto, Workspace e papel); nenhum identificador vindo do modelo substitui o escopo da identidade.
- **PR-003**: Credenciais existem só em memória do worker e das chamadas ao provedor; nunca entram em prompt, resposta ou log.
- **PR-004**: Testes não usam o banco de desenvolvimento e não executam comandos destrutivos de schema; o schema novo usa migração Alembic versionada.
- **PR-005**: A interface reutiliza os componentes registrados em `INTERFACE.md` antes de criar outros.

### 5. Histórias de usuário

#### US-001 — Perguntar sobre o conteúdo sem escolher coleção (P1)

Como pessoa usuária, quero perguntar pelo chat sobre o conteúdo dos meus documentos sem precisar escolher uma coleção, para obter respostas de qualquer parte do meu Workspace.

**Por que P1**: é o defeito relatado e o valor central do copilot.
**Teste independente**: com duas coleções indexadas, uma pergunta sem seleção é respondida com fonte da coleção certa.
**Requisitos**: FR-001, FR-002, FR-007, FR-009

#### US-002 — Consultar o estado do sistema e receber orientação (P1)

Como pessoa usuária, quero perguntar o que está acontecendo no produto (envios, falhas, configurações), para entender e saber o próximo passo.

**Por que P1**: sem isso o copilot não vê "tudo o que é feito" no sistema.
**Teste independente**: um envio com falha é explicado com situação, etapa e erro seguro, e o copilot sugere "Repetir" com link.
**Requisitos**: FR-003, FR-006, FR-011

#### US-003 — Consultar o conteúdo processado dos documentos (P2)

Como pessoa usuária, quero perguntar sobre o texto convertido e sobre os trechos (com suas etiquetas) de cada documento, para conferir o que foi enviado à base vetorial.

**Por que P2**: depende da persistência nova; amplia a conferência do processamento.
**Teste independente**: após um envio, a pergunta por trechos com uma etiqueta lista os trechos corretos; reenviar substitui e apagar remove.
**Requisitos**: FR-002, FR-004, FR-005, FR-009

#### US-004 — Confiar nas respostas por suas fontes (P1)

Como pessoa usuária, quero ver de onde veio cada resposta e abrir a origem, para verificar e confiar no que o copilot diz.

**Por que P1**: um copilot com acesso amplo sem fontes verificáveis arrisca respostas sem lastro.
**Teste independente**: uma resposta mostra fontes navegáveis por teclado; sem base, o copilot declara que não encontrou.
**Requisitos**: FR-006, FR-008, FR-009

#### US-005 — Ter meus dados isolados por Workspace e papel (P1)

Como responsável pelo produto, quero que o copilot só mostre o que o Workspace e o papel de quem pergunta permitem e nunca revele credenciais, para que o acesso amplo não contorne permissões.

**Por que P1**: risco de segurança e privacidade do acesso amplo.
**Teste independente**: perguntas sobre outro Workspace, sobre dado restrito a admin e sobre chave de conexão não revelam nada.
**Requisitos**: FR-010, FR-011

### 6. Cenários BDD de aceite

#### AC-001 — pergunta sem escolher coleção é respondida com fonte

**Cobre**: US-001, US-004, FR-001, FR-002, FR-007, FR-008, NFR-002

```gherkin
@US-001 @US-004 @FR-001 @FR-002 @FR-007 @FR-008 @NFR-002 @AC-001
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Pergunta sobre o conteúdo sem escolher coleção
    Given um Workspace com as coleções "Manuais" e "Políticas" indexadas e nenhuma coleção selecionada no chat
    When a pessoa pergunta "qual a garantia do modelo X?" e o manual do modelo X está em "Manuais"
    Then o copilot responde com base no trecho do manual
    And a resposta traz a fonte com o documento e a coleção "Manuais"
```

#### AC-002 — o seletor de coleção apenas restringe a busca

**Cobre**: US-001, FR-001, FR-007, NFR-003

```gherkin
@US-001 @FR-001 @FR-007 @NFR-003 @AC-002
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Seletor funciona como filtro opcional
    Given as coleções "Manuais" e "Políticas" com um documento sobre prazo de entrega cada
    When a pessoa seleciona "Políticas" no seletor, operável por teclado, e pergunta sobre prazo de entrega
    Then a resposta e as fontes vêm somente de "Políticas"
    And limpar a seleção volta a buscar em todas as coleções do Workspace
```

#### AC-003 — coleção selecionada responde sobre qualquer tema do conteúdo

**Cobre**: US-001, FR-002, FR-007, FR-008, NFR-002

```gherkin
@US-001 @FR-002 @FR-007 @FR-008 @NFR-002 @AC-003
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Coleção selecionada responde sobre o conteúdo mesmo fora do tema RAG
    Given a coleção "Manuais" selecionada e indexada com um manual de produto
    When a pessoa pergunta algo que só o manual responde, sem relação com RAG
    Then o copilot responde pelo conteúdo recuperado e não recusa o assunto
    And a resposta cita o documento de origem
    And a resposta chega dentro do prazo do turno
```

#### AC-004 — envio com falha é explicado com o estado real

**Cobre**: US-002, FR-003, FR-006, FR-011, NFR-001, NFR-004

```gherkin
@US-002 @FR-003 @FR-006 @FR-011 @NFR-001 @NFR-004 @AC-004
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Pergunta sobre um envio com falha
    Given um envio da coleção "Manuais" com situação "failed" e a etapa "indexando"
    When a pessoa pergunta "por que o meu último envio falhou?"
    Then o copilot informa a situação, a etapa e a mensagem de erro segura do envio
    And sugere "Repetir" com o link da tela de envios da coleção
    And a resposta não traz detalhe interno de provedor nem credencial
```

#### AC-005 — pedido de ação é orientado e não executado

**Cobre**: US-002, FR-003, FR-006, NFR-001

```gherkin
@US-002 @FR-003 @FR-006 @NFR-001 @AC-005
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Pedido de ação de escrita
    Given a coleção "Manuais" com o documento "manual.md"
    When a pessoa pede "apague o documento manual.md"
    Then o copilot explica o passo e indica o link da tela de documentos
    And o documento continua existindo e nenhuma escrita acontece no sistema
```

#### AC-006 — configurações são consultáveis sem segredos

**Cobre**: US-002, US-005, FR-003, FR-011, NFR-004

```gherkin
@US-002 @US-005 @FR-003 @FR-011 @NFR-004 @AC-006
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Consulta de configuração e conexões
    Given uma coleção com conexão de embeddings e de Qdrant com chaves cadastradas
    When a pessoa pergunta qual modelo de embeddings e qual divisão a coleção usa
    Then o copilot informa modelo, tamanho do trecho e sobreposição
    And nenhuma chave, senha ou URL com credencial aparece na resposta
```

#### AC-007 — envio concluído guarda o conteúdo processado

**Cobre**: US-003, FR-004, FR-005, NFR-001

```gherkin
@US-003 @FR-004 @FR-005 @NFR-001 @AC-007
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Persistência do conteúdo ao concluir o documento
    Given um envio com o arquivo "manual.md" de 3 trechos etiquetados com categoria "produto"
    When o destino confirma a sincronização do documento
    Then o texto convertido e os 3 trechos, na ordem e com as etiquetas, ficam guardados ligados ao documento e ao envio
    And um documento cuja sincronização falha não tem conteúdo novo guardado
```

#### AC-008 — copilot responde sobre trechos e etiquetas

**Cobre**: US-003, FR-002, FR-004, NFR-002

```gherkin
@US-003 @FR-002 @FR-004 @NFR-002 @AC-008
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Pergunta sobre como o documento foi dividido
    Given o documento "manual.md" processado com trechos etiquetados
    When a pessoa pergunta "quais trechos de manual.md têm a etiqueta categoria=produto?"
    Then o copilot lista os trechos com a etiqueta pedida a partir do conteúdo guardado
    And cita o documento e a coleção como fonte
```

#### AC-009 — nova versão substitui o conteúdo guardado

**Cobre**: US-003, FR-004, FR-005, NFR-001

```gherkin
@US-003 @FR-004 @FR-005 @NFR-001 @AC-009
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Reenvio de uma nova versão
    Given o documento "manual.md" com conteúdo guardado da versão 1
    When a pessoa envia a versão 2 do mesmo arquivo e o destino confirma
    Then o conteúdo guardado passa a ser o da versão 2 e só existe uma versão por documento
    And um reenvio idêntico não altera o conteúdo guardado
```

#### AC-010 — apagar documento ou coleção apaga o conteúdo guardado

**Cobre**: US-003, FR-005, FR-009, FR-010

```gherkin
@US-003 @FR-005 @FR-009 @FR-010 @AC-010
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Exclusão remove o conteúdo e o copilot deixa de responder por ele
    Given os documentos "manual.md" e "guia.md" com conteúdo guardado na coleção "Manuais"
    When a pessoa apaga "manual.md" e depois apaga a coleção
    Then o conteúdo guardado de "manual.md" é removido primeiro e o de "guia.md" depois, junto com a coleção
    And uma pergunta sobre o texto apagado recebe a resposta de que não foi encontrado
```

#### AC-011 — sem base para responder o copilot admite

**Cobre**: US-004, FR-002, FR-009, NFR-002, NFR-003

```gherkin
@US-004 @FR-002 @FR-009 @NFR-002 @NFR-003 @AC-011
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Pergunta sem resposta nas fontes
    Given nenhuma coleção, documento ou registro do Workspace que responda à pergunta
    When a pessoa pergunta algo que o produto não contém
    Then o copilot responde que não encontrou e não afirma nada sem base
    And a resposta é anunciada pela região de mensagens ao vivo do chat
```

#### AC-012 — fontes e sugestões levam ao destino pelo teclado

**Cobre**: US-004, FR-006, FR-008, NFR-003

```gherkin
@US-004 @FR-006 @FR-008 @NFR-003 @AC-012
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Fonte clicável
    Given uma resposta com fonte de documento e uma sugestão de tela
    When a pessoa ativa a fonte ou o link pelo teclado
    Then a aplicação abre a tela do documento, do envio ou da coleção correspondente
    And o foco e o rótulo do link permitem identificar o destino com leitor de tela
```

#### AC-013 — dados de outro Workspace não aparecem

**Cobre**: US-005, FR-001, FR-003, FR-010, NFR-001

```gherkin
@US-005 @FR-001 @FR-003 @FR-010 @NFR-001 @AC-013
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Isolamento entre Workspaces
    Given a pessoa do Workspace A e uma coleção com envios e documentos no Workspace B
    When a pessoa pergunta sobre o conteúdo ou o estado da coleção do Workspace B
    Then o copilot responde que não encontrou
    And nenhum trecho, nome ou contagem do Workspace B entra no contexto do modelo
```

#### AC-014 — o papel limita o que o copilot mostra

**Cobre**: US-005, FR-003, FR-010, NFR-001

```gherkin
@US-005 @FR-003 @FR-010 @NFR-001 @AC-014
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Pessoa member consulta algo restrito a admin
    Given uma pessoa com papel member e um dado de configuração visível apenas a admin
    When a pessoa pergunta sobre esse dado
    Then o copilot informa que não pode mostrá-lo para o papel dela
    And o dado não entra no contexto do modelo
```

#### AC-015 — credenciais nunca chegam ao modelo nem à resposta

**Cobre**: US-005, FR-011, NFR-004

```gherkin
@US-005 @FR-011 @NFR-004 @AC-015
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Credenciais fora do contexto
    Given uma conexão com chave de API cadastrada e uma pessoa admin
    When a pessoa pergunta pela chave da conexão ou tenta fazer o copilot revelá-la
    Then o copilot recusa informar credenciais
    And o contexto enviado ao modelo e os registros de log não contêm a chave
```

#### AC-016 — assunto sem relação com o produto é recusado

**Cobre**: US-001, FR-002, FR-009

```gherkin
@US-001 @FR-002 @FR-009 @AC-016
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Pedido sem relação com o produto
    Given o chat aberto
    When a pessoa pede "escreva um poema sobre o mar"
    Then o copilot recusa com cortesia e diz que ajuda com o produto e seu conteúdo
    And nenhuma busca em coleção é feita para esse pedido
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve buscar, para cada pergunta, nos trechos indexados de todas as coleções do Workspace da pessoa, sem exigir coleção selecionada.
- **FR-002**: O sistema deve responder com base no conteúdo recuperado, qualquer que seja o tema do documento, e recusar com cortesia pedidos sem relação com o produto e seu conteúdo.
- **FR-003**: O sistema deve permitir consultar o estado operacional do Workspace: coleções, documentos, envios (situação, etapa, contagens e erro seguro), execuções e configurações não secretas.
- **FR-004**: O worker deve gravar, para cada documento cuja sincronização o destino confirmou, o texto convertido e os trechos (ordem, texto e etiquetas), ligados ao documento da coleção e ao envio de origem.
- **FR-005**: O sistema deve manter uma única versão do conteúdo processado por documento: nova versão o substitui, e apagar o documento ou a coleção o apaga junto.
- **FR-006**: O copilot deve sugerir o passo e o link da tela correspondente quando a resposta envolver uma ação, sem executar nenhuma escrita.
- **FR-007**: O seletor de coleção do chat deve ser opcional e atuar como filtro que restringe a busca à coleção escolhida.
- **FR-008**: Cada resposta sustentada por conteúdo ou por dado do sistema deve trazer fontes com o documento, a coleção, o envio ou a tela de origem, cada uma navegável.
- **FR-009**: Quando nenhuma fonte sustentar a resposta, o copilot deve dizer que não encontrou e não afirmar nada sem base.
- **FR-010**: O sistema deve limitar toda consulta ao tenant, projeto, Workspace e papel da identidade da pessoa, sem aceitar escopo vindo do modelo ou do texto da pergunta.
- **FR-011**: O sistema não deve incluir credenciais de conexão (chaves, senhas, URLs com credencial) no contexto do modelo, na resposta nem nos logs.

#### Não funcionais

- **NFR-001**: Isolamento: nenhum dado de outro Workspace ou fora do alcance do papel entra no contexto do modelo. **Verificação**: testes de API e de contexto com dois Workspaces e papéis admin e member (AC-004, AC-005, AC-007, AC-009, AC-013, AC-014).
- **NFR-002**: Desempenho: o turno com busca em até 10 coleções responde dentro do tempo limite já configurado do modelo, com o número de trechos recuperados limitado por turno. **Verificação**: teste com busca simulada em 10 coleções e inspeção do limite de trechos; alvo de latência a confirmar (ver dúvidas abertas).
- **NFR-003**: Acessibilidade: seletor, fontes e links operáveis por teclado, com rótulo que identifica o destino, e respostas anunciadas pela região de mensagens ao vivo. **Verificação**: testes de componente com `axe-core` e de teclado.
- **NFR-004**: Privacidade: credenciais não aparecem em prompt, resposta nem log, e o erro exposto é genérico. **Verificação**: teste que inspeciona o contexto enviado ao modelo e os logs com uma chave conhecida.

#### Erros e casos-limite

- Coleção sem documentos indexados selecionada como filtro → informa que a coleção ainda não tem documentos, sem consultar o modelo (comportamento atual preservado).
- Falha do modelo, da busca vetorial ou do tempo limite → mensagem genérica já usada, sem detalhe interno; nada é gravado como resposta.
- Documento enviado antes desta entrega, sem conteúdo processado guardado → o copilot informa a limitação e responde apenas pelo conteúdo indexado.
- Conexão desativada ou coleção apagada → a coleção sai da busca e das fontes; o copilot não a menciona como disponível.
- Pergunta ambígua sobre várias coleções → o copilot lista as coleções candidatas nas fontes e pede ao usuário que indique o filtro.
- Texto convertido muito longo → o contexto do modelo recebe apenas trechos limitados por turno; o texto completo não é enviado de uma vez.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI + Celery + SQLAlchemy/Alembic (PostgreSQL), pipeline em `src/pipeline/` e aplicação em `src/app/`; o grafo LangGraph do assistente (`src/pipeline/assistant.py`) não conhece `src.app` e recebe dependências por parâmetro; `src/pipeline/service.py::assistant_reply` monta o turno.
- O assistente hoje chama o modelo sem ferramentas, com dois blocos de contexto: documentação fixa do produto e, com coleção apontada, trechos dela (`src/app/routers/assistente.py::_colecao_apontada`).
- Conversas e mensagens ficam em `conversas_assistente` e `mensagens_assistente`; `fontes` é uma coluna JSON de lista de textos.
- O worker `process_envio_task` (`src/app/tasks.py`) grava a versão do documento em `_registrar_documento` depois que o destino confirma a sincronização.
- Frontend Next.js (app router), React, shadcn/ui (Base UI) e componentes de domínio em `frontend/src/features/assistente/`; testes com Vitest e `axe-core`.

#### Arquitetura e módulos

- O modelo continua sem ferramentas (PR-001). O grafo ganha nós de recuperação determinísticos, cada um alimentado por uma dependência injetada: `recuperar_colecoes` (busca nas coleções do Workspace), `recuperar_estado` (estado operacional) e `recuperar_processado` (texto e trechos guardados). Um nó `classificar` decide quais recuperações a pergunta exige, para limitar custo e contexto; perguntas fora do produto não disparam nenhuma busca (AC-016).
- Módulo novo `src/app/assistente_contexto.py` (fronteira app): a partir da identidade, lista as coleções do Workspace, monta `configuracao_da_colecao` de cada uma, executa `query_base` com limite total de trechos por turno, consulta estado e conteúdo processado por repositório e devolve **dados já filtrados** e as fontes estruturadas. Nenhum identificador de escopo vem do modelo (FR-010).
- `src/pipeline/assistant.py` recebe esses callables e continua livre de `src.app`; `service.assistant_reply` passa a aceitar `colecoes`, `estado` e `processado` além de `base`.
- Credenciais: `assistente_contexto` só devolve campos allowlisted (nomes, estados, contagens, modelo, divisão); configurações de conexão nunca saem do worker/provedor (FR-011).
- `src/app/tasks.py::_registrar_documento` passa a gravar o conteúdo processado na mesma transação da versão do documento.
- Apagar documento e coleção (`src/app/routers/colecoes.py`) removem o conteúdo processado na mesma transação.

#### Migrations

- Revisão Alembic `0031_conteudo_documento` cria a tabela `conteudos_documento` (ver seção 9). Ordem: criar tabela e índice único; sem backfill. `downgrade` remove a tabela; nenhuma coluna existente muda. Compatível com documentos antigos, que ficam sem conteúdo guardado (limitação informada pelo copilot).
- Testes rodam em schema exclusivo e sem comandos destrutivos de schema (PR-004).

#### Models

- `ConteudoDocumento` em `src/app/models.py`: uma linha por `DocumentoColecao`, com texto convertido, trechos ordenados com etiquetas, envio de origem e data. Invariantes: `documento_id` único; só existe para documento cuja sincronização foi confirmada.
- `MensagemAssistente.fontes` (JSON) passa a aceitar objetos de fonte além de textos; mensagens antigas continuam válidas.

#### Controllers e casos de uso

- `POST /api/v1/assistente/conversas/{id}/mensagens` (`src/app/routers/assistente.py`): `colecao_id` fica opcional e atua como filtro; sem ele, o caso de uso busca em todas as coleções do Workspace da identidade. Autorização: identidade da sessão; 404 para coleção de outro Workspace.
- Caso de uso `montar_contexto(identity, texto, colecao_id)` em `src/app/assistente_contexto.py`: decide, valida escopo e devolve contexto e fontes; testável sem modelo.
- `process_envio_task`/`_registrar_documento` em `src/app/tasks.py`: lê o texto convertido do diretório materializado do envio e os trechos do grupo do documento; grava em `ConteudoDocumento` com a versão.

#### Views e experiência

- Painel do assistente (`AssistentePainel`): seletor passa a "Filtrar por coleção (opcional)", com valor padrão "Todas as coleções"; mensagens do assistente exibem fontes como links (ver seção 10). Estados: loading, vazio, erro e "não encontrei" seguem o padrão do painel; acessibilidade em seção 10.

#### Queries e repositórios

- `src/app/repository.py`: listar coleções do Workspace e da identidade; listar documentos, envios e execuções por coleção, com filtros e limite; buscar `ConteudoDocumento` por documento e por etiqueta (filtro em Python sobre o JSON de trechos, com limite de trechos por turno). Índice único em `conteudos_documento.documento_id`. Consistência: leitura após commit do worker; sem leitura de versão parcial.

#### Jobs e processamento assíncrono

- `process_envio_task` já é idempotente por documento (`source_hash`): reenvio idêntico não regrava conteúdo (AC-009). A gravação do conteúdo acontece junto da versão do documento, portanto uma falha do destino não deixa conteúdo novo (AC-007). Retry do envio herda o comportamento existente.

#### Estrutura de arquivos

```text
specs/draft/0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado/
  spec.md
  research/
alembic/versions/0031_conteudo_documento.py
src/app/assistente_contexto.py
src/app/models.py               (ConteudoDocumento)
src/app/tasks.py                (_registrar_documento)
src/app/repository.py
src/app/routers/assistente.py
src/app/routers/colecoes.py     (exclusão do conteúdo)
src/pipeline/assistant.py
src/pipeline/service.py
frontend/src/features/assistente/
tests/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| ConteudoDocumento (`conteudos_documento`) | `id` (texto de 36), `documento_id` único | `texto` (texto livre, Markdown convertido); `trechos` (JSON: lista de `ordem`, `texto`, `etiquetas` como pares rótulo/valor); `envio_id` (envio que gerou a versão); `atualizado_em`. Uma versão por documento | 1:1 com `DocumentoColecao`; N:1 com `Envio` |
| Fonte de resposta (dentro de `MensagemAssistente.fontes`) | posição na lista | `tipo` (documento, envio, coleção ou tela), `rotulo`, `colecao_id`, `documento`, `envio_id`, `rota`. Texto simples antigo continua aceito | N:1 com `MensagemAssistente` |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| ConteudoDocumento | inexistente | destino confirma a sincronização do documento | gravado (versão atual) | só existe junto da versão confirmada |
| ConteudoDocumento | gravado | nova versão confirmada com conteúdo diferente | gravado (substituído) | uma versão por documento |
| ConteudoDocumento | gravado | reenvio idêntico | gravado (inalterado) | sem regravação nem novo embedding |
| ConteudoDocumento | gravado | documento ou coleção apagado | removido | removido na mesma transação do documento |

#### Migração e retenção

- Migração aditiva (tabela nova), sem backfill: documentos enviados antes ficam sem conteúdo guardado até o próximo envio que os altere. Retenção: enquanto o documento existir, uma versão; nenhum prazo fixo.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. O painel do assistente existente muda (seletor e fontes) e não há tela nova.

#### Stack e convenções de interface

- Next.js (app router) com React, shadcn/ui (Base UI) e ReUI conforme `INTERFACE.md`; componentes de domínio em `frontend/src/features/assistente/`; Vitest com `axe-core` (`AssistentePainel.a11y.test.tsx`). Telas atuais afetadas: `AssistentePainel`, `SeletorColecao`, `MensagemChat`, `ListaMensagens`.

#### Telas e responsabilidades

- **Painel do assistente** (camada global, aberto por `AssistenteLauncher`): pessoa autenticada pergunta e lê respostas com fontes. Entrada: texto até 4000 caracteres e filtro opcional de coleção. Saída: resposta, fontes clicáveis e sugestão de passo com link.

#### Fluxo de informação e navegação

- A pessoa abre o painel, pergunta (com ou sem filtro), lê a resposta e ativa uma fonte; a fonte leva à tela de destino (`/workspaces/{ws}/colecoes/{id}` para coleção ou documento, `/envios/{id}` para envio) e o painel permanece disponível ao voltar. `Breadcrumb` de cada destino segue o padrão existente (equipe, módulo, tela atual); o painel não tem `Breadcrumb` próprio.

#### Menus e navegação principal

- Sem mudança de menu: o acesso continua pelo `AssistenteLauncher` fixo no canto inferior direito, em todas as telas autenticadas, com o mesmo comportamento responsivo (painel lateral em desktop, tela cheia em mobile, como hoje).

#### Formulários e ações

- Campo de mensagem inalterado. Seletor: rótulo "Filtrar por coleção (opcional)", opção inicial "Todas as coleções" e opção de limpar; ação principal "Enviar" no `ComposerMensagem`. Padrão: painel lateral (`Sheet`), sem modal novo.

#### Composição e disposição

- Mantém a hierarquia atual do painel (cabeçalho, lista, seletor, composer). Fontes aparecem abaixo de cada resposta como lista de links com rótulo "documento — coleção". Conteúdo longo quebra linha sem overflow horizontal; em mobile as fontes empilham.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Painel do assistente | `SeletorColecao` | Filtro opcional com "Todas as coleções" e limpar | `frontend/src/features/assistente/SeletorColecao.tsx` | `Select` | shadcn/ui (Base UI) | Existente, estendido com opção "Todas" |
| Painel do assistente | `MensagemChat` | Exibir a resposta e as fontes | `frontend/src/features/assistente/MensagemChat.tsx` | `Badge` | shadcn/ui | Existente, fontes viram links |
| Painel do assistente | `FontesDaResposta` | Lista de fontes navegáveis com rótulo e destino | `frontend/src/features/assistente/FontesDaResposta.tsx` | `Badge` com `Link` | Próprio sobre shadcn/ui | Novo, para isolar a lista de `MensagemChat` |
| Painel do assistente | `useAssistente` | Enviar com `colecao_id` opcional e tratar fontes estruturadas e antigas | `frontend/src/features/assistente/useAssistente.ts` | Hook | Próprio | Existente, estendido |

- Shadcn/ui e ReUI: nenhuma composição ReUI nova; as primitives usadas são `Select`, `Badge` e `Sheet`, já registradas em `INTERFACE.md`. `INTERFACE.md` recebe o novo bloco `FontesDaResposta` e a extensão de `SeletorColecao` e `MensagemChat`.

#### Estados e acessibilidade

- Loading no envio da pergunta (indicador existente), vazio da conversa, erro genérico, sucesso com fontes e "não encontrei" como mensagem comum na região `role="log"` `aria-live="polite"`. Permissão insuficiente aparece como resposta textual do copilot, não como erro de tela.
- Seletor e links de fonte operáveis por teclado, com rótulo que inclui o tipo e o destino (ex.: "Abrir documento manual.md da coleção Manuais"); foco visível; o `Breadcrumb` dos destinos segue o padrão.

#### Contrato CRUD

- Não há CRUD nesta entrega: o conteúdo processado é somente leitura para o copilot e nenhuma entidade nova é administrada por tela. Por isso não se cria `PageHeader`, `DataGrid`, coluna `ID`, linha-link nem ações de editar e apagar; as listagens existentes de Coleções, Documentos e Envios (SPEC-0030) seguem o contrato CRUD já registrado em `INTERFACE.md` e são apenas destino das fontes.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre durante a implementação, mesmo sem pedido, e confere bordas, espaçamentos, margens, padding e tipografia do painel nos estados (sem fontes, uma fonte, muitas fontes, nome longo, erro, sem resultado), em 375 px e 1280 px e nos temas claro e escuro. Registrar método, viewport, estados, achados e ajustes na tarefa.

#### APIs expostas

- `POST /api/v1/assistente/conversas/{id}/mensagens`: corpo `{ texto, colecao_id? }`; resposta `{ mensagem_pessoa, mensagem_assistente }` em que `fontes` passa a ser lista de objetos `{ tipo, rotulo, colecao_id?, documento?, envio_id?, rota }` (textos simples antigos continuam legíveis). Erros: 404 para coleção fora do escopo, 409 para coleção sem documentos, 502 genérico para falha do modelo. Mesma versão `/api/v1`; mudança compatível.

#### APIs externas utilizadas

- Provedor de chat configurado em `llm` (`ProviderFactory.create_chat_model`), com o `timeout` existente e sem retry novo; falha vira a mensagem genérica. Embeddings e Qdrant das conexões de cada coleção, já usados por `query_base`.

#### Documentação das APIs consultadas

- Nenhuma documentação externa consultada; contratos internos em `src/pipeline/service.py` e `src/app/routers/assistente.py`.

#### Eventos e outros contratos

- Contrato do grafo: `executar_turno(..., colecoes=None, estado=None, processado=None, base=None)` com callables que devolvem dados e fontes já filtrados pela identidade. Sem eventos novos.

### 11. Estratégia TDD

- **Unidade**: [regras e componentes].
- **Integração/contrato**: [fronteiras].
- **BDD/aceite**: [Gherkin de referência que orienta o entendimento e o desenho dos testes TDD].
- **Runner TDD**: [PHP = Pest; Node = decisão confirmada com o usuário e
  materializada em `test:tdd`; outra stack = runner existente ou decisão explícita].
- **E2E**: [jornadas essenciais ou “Não aplicável”.]
- **Verificação manual**: [somente o inevitável, com motivo].

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, NFR-001, AC-001 | [AC-001 na seção 6] | [caso 1 em tests/Feature/RecursoTest.php com marcador próprio `SPECSFY:`] | Pending | Pending | Pending |
| US-001, FR-001, NFR-001, AC-002 | [AC-002 na seção 6] | [caso 2 em tests/Feature/RecursoTest.php com marcador próprio `SPECSFY:`] | Pending | Pending | Pending |
| US-001, FR-001, NFR-001, AC-003 | [AC-003 na seção 6] | [caso 3 em tests/Feature/RecursoTest.php com marcador próprio `SPECSFY:`] | Pending | Pending | Pending |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001 | Unidade | [tests/arquivo] | Pending |
| FR-001 | AC-002 | [nível] | [tests/arquivo] | Pending |
| FR-001 | AC-003 | [nível] | [tests/arquivo] | Pending |
| NFR-001 | AC-001 | [nível] | [comando] | Pending |
| NFR-001 | AC-002 | [nível] | [comando] | Pending |
| NFR-001 | AC-003 | [nível] | [comando] | Pending |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/draft/0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado/spec.md`
- **Achados**: [Pending.]
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/draft/0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado/spec.md`
- **Achados**: [Pending.]

#### Gate do Ato III — Entrega

- **Resultado**: Pending
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/draft/0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado/spec.md .`
- **Achados**: [Pending.]

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

- [ ] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pest falhando em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-001 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [ ] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [ ] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pest falhando em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-002 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [ ] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

- [ ] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pest falhando em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-003 — Depends: none
  - [ ] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível de teste.
  - [ ] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY:`, sem criar ou executar `.feature`.
  - [ ] **VERIFY**: Observar RED válido.
  - [ ] **VISUAL**: Conferir a interface afetada ou registrar `Não aplicável` porque a tarefa só materializa teste.
  - [ ] **EVIDENCE**: Registrar comando e causa do RED.
  - [ ] **IMPROVE**: Revisar a cobertura e registrar aprendizado.

#### Fase 2 — US-001 [título] (P1)

**Objetivo**: [valor entregue].
**Teste independente**: [comando e resultado].

- [ ] T004 [CODE] [US-001] Implementar comportamento em app/Services/RecursoService.php — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-003 — Depends: T001, T002, T003
  - [ ] **PREP**: Confirmar RED TDD e dependências.
  - [ ] **EXECUTE**: Implementar a menor mudança.
  - [ ] **VERIFY**: Executar testes focais e regressão.
  - [ ] **VISUAL**: Conferir bordas, espaçamentos, margens, padding e tipografia do sistema na interface afetada; registrar `Não aplicável` com motivo quando não houver superfície visual.
  - [ ] **EVIDENCE**: Registrar GREEN e arquivos alterados.
  - [ ] **IMPROVE**: Aplicar melhoria de processo ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T004","refs":["US-001","FR-001","NFR-001","AC-001","AC-002","AC-003"],"files":["app/Services/RecursoService.php"],"commands":[{"run":"comando focal","exit":0}]} -->

**Checkpoint**: [como demonstrar a história isoladamente].

#### Fase de interface

- [ ] T005 [CODE] [US-001] Implementar a tela de [responsabilidade] em src/features/recurso/ListaRecurso.tsx — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-003 — Depends: T001, T002, T003
  - [ ] **PREP**: Confirmar stack, tela atual, fluxo, formulário e estados definidos na seção 10; em React, carregar `$specsfy-specialist-react-ui-components` antes de escrever JSX ou TSX.
  - [ ] **EXECUTE**: Implementar os blocos React, tela, ações e formulário conforme a composição acordada; registrar cada bloco e componente em `INTERFACE.md`.
  - [ ] **VERIFY**: Exercitar Breadcrumb, navegação, validações, feedback e teclado.
  - [ ] **VISUAL**: Conferir PageHeader reutilizado, DataGrid em largura total, coluna `ID`, link da linha, ações de editar e apagar, bordas, espaçamentos, margens, padding e tipografia nos estados e viewports relevantes.
  - [ ] **EVIDENCE**: Registrar arquivos, comando e resultado da interação.
  - [ ] **IMPROVE**: Aplicar melhoria de interface ou justificar nenhuma.
  <!-- specsfy:evidence {"task":"T005","refs":["US-001","FR-001","NFR-001","AC-001","AC-002","AC-003"],"files":["src/features/recurso/ListaRecurso.tsx"],"commands":[{"run":"comando focal","exit":0}]} -->

#### Fase final — Qualidade

- [ ] T006 [TEST] Executar regressão e rastreabilidade em tests/Feature/RecursoTest.php — Refs: US-001, FR-001, NFR-001, AC-001, AC-002, AC-003 — Depends: T004, T005
  - [ ] **PREP**: Identificar suites, checks e gates.
  - [ ] **EXECUTE**: Executar regressão e rastreabilidade.
  - [ ] **VERIFY**: Confirmar ausência de gaps.
  - [ ] **VISUAL**: Repassar a conferência visual final ou registrar `Não aplicável` com motivo concreto.
  - [ ] **EVIDENCE**: Registrar contagens e comandos finais.
  - [ ] **IMPROVE**: Registrar retrospectiva do processo.

### 15. Ordem de execução

- Caminho crítico: T001/T002/T003 → T004 → T005 → T006.
- Tarefas paralelas: [IDs e motivo, ou “Nenhuma”.]
- Estratégia de MVP: [menor conjunto de histórias entregável].

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0030 (Coleções, concluída) e SPEC-0021 (assistente, concluída); correção `fix/assistente-colecao-selecionada` (5d23872). Persistência nova registrada em `.specsfy/DATABASE.md`.

#### Riscos

- Custo e latência de buscar em várias coleções por turno → limitar coleções e trechos por turno e classificar a pergunta antes de buscar (NFR-002).
- Injeção de instrução via conteúdo de documento → delimitar trechos como dado, sem ferramentas de escrita (PR-001) e sem escopo vindo do modelo (PR-002).
- Vazamento entre Workspaces ou de credenciais → filtro na fronteira `assistente_contexto` com allowlist e testes de contexto (NFR-001, NFR-004).
- Texto convertido grande aumenta o armazenamento → uma versão por documento e exclusão junto do documento; limite de tamanho a definir nas tarefas.
- Documentos antigos sem conteúdo guardado → informar a limitação (casos-limite).

#### Suposições

- O texto convertido é o conteúdo do arquivo Markdown do envio, lido do diretório materializado (reversível se a conversão passar a ocorrer em outra etapa).
- Alvo de latência do turno com busca em até 10 coleções: dentro do `timeout` do modelo já configurado (a confirmar).
- "Restrito a admin" abrange as configurações de conexão e a divisão; a lista final entra nas tarefas (a confirmar).
- O copilot mantém o nome "assistente" na interface; "copilot" nomeia a capacidade nesta spec.

### 17. Decisões

- **DEC-001**: Escopo de acesso: conteúdo das coleções, estado operacional e conteúdo processado — escolhida pela pessoa (Pergunta 1).
- **DEC-002**: O worker persiste o texto convertido e os trechos com etiquetas, sem o arquivo original — Perguntas 2 e 9; alternativa descartada: reprocessar sob demanda (mais lento e caro).
- **DEC-003**: O copilot herda Workspace e papel da identidade — Pergunta 3; o modelo nunca fornece escopo.
- **DEC-004**: Seletor de coleção vira filtro opcional — Pergunta 4.
- **DEC-005**: Só consulta e sugestão de passo; sem ações de escrita — Pergunta 5; execução fica para item futuro.
- **DEC-006**: Credenciais nunca chegam ao modelo, à resposta nem aos logs — inferência a confirmar (Pergunta 3 não a cobriu).
- **DEC-007**: Retenção enquanto o documento existir, uma versão — Pergunta 6.
- **DEC-008**: Fontes estruturadas e clicáveis; "não encontrei" sem base — Pergunta 7.
- **DEC-009**: O defeito da coleção selecionada foi corrigido antes da spec, em `fix/` — Pergunta 8 e commit 5d23872.
- **DEC-010**: O modelo continua sem ferramentas e a recuperação é feita por nós determinísticos do grafo — mantém a restrição da SPEC-0021 e reduz a superfície de ataque, ao custo de uma etapa de classificação.

### 18. Definition of Done

- [ ] `Definition Gate` está `Passed`.
- [ ] `Plan Gate` está `Passed`.
- [ ] `Delivery Gate` está `Passed`.
- [ ] Todos os cenários `AC` aplicáveis passam.
- [ ] Todos os requisitos possuem evidência de verificação.
- [ ] Todas as tarefas na seção 14 estão concluídas.
- [ ] Testes e checks estáticos disponíveis passam.
