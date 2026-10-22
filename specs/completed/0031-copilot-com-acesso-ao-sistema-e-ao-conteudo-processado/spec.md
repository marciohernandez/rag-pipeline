# Especificação integrada: Copilot com acesso ao sistema e ao conteúdo processado

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0031 |
| Slug | 0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado |
| Status | Complete |
| Effort | 8 |
| Effort updated at | 2026-10-09 |
| Effort rationale | Amplia o assistente de orientação sobre RAG para um copilot que consulta conteúdo indexado de todas as coleções, estado operacional e conteúdo processado; exige persistência nova no worker, ferramentas de consulta com isolamento por Workspace e papel, fontes clicáveis e mudança no painel existente. Sem ações de escrita. |
| ClickUp Task | |
| Milestones | M05 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-09 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

O assistente atual (SPEC-0021) só orienta sobre RAG e o pipeline: seu prompt manda recusar qualquer outro assunto e ele só enxerga a documentação fixa do produto e, quando a pessoa escolhe uma coleção, os trechos dela. Ele não consulta o estado do sistema (coleções, documentos, envios, falhas, configurações) nem o que foi processado antes de ir para a base vetorial. Pela formulação da pessoa: "quando escolho a coleção (está como opcional) ele não acessa as informações para responder. Eu quero um assistente (copilot) que tem acesso ao sistema inteiro, tudo que é feito, inclusive as informações que são processadas para envio à base vetorial. Assim posso perguntar qualquer coisa e ele responde."

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

- Nenhum artefato externo. Evidência visual própria da T035 (build real, API simulada e Chromium headless, 2026-10-15):
  - `research/t035-mobile-claro.png`: painel do assistente em 375 px, tema claro, com fontes estruturadas, nome longo e "não encontrei".
  - `research/t035-desktop-escuro.png`: o mesmo estado em 1280 px, tema escuro.
  - `research/t035-visual-medidas.json`: medidas dos quatro cenários (375 e 1280 px, claro e escuro): sem overflow da página nem do painel, 4 links com rótulo de destino, região viva ativa.

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
- **Q10** O que é restrito a admin além das credenciais de conexão? → **A**: só as configurações de conexão e a divisão; o restante (coleções, documentos, envios, falhas) segue as permissões do Workspace e do papel (opção 1, confirmada em 2026-10-15; a pessoa pediu recomendação e a aceitou).
- **Q11** Credenciais de conexão podem aparecer na resposta, nem para admin? → **A**: nunca; o copilot só informa se a conexão está configurada, sem mostrar valor algum, nem mascarado (opção 1, confirmada em 2026-10-15; recomendação aceita).
- **Q12** Qual o prazo do turno com busca em várias coleções? → **A**: sem número novo; vale o `timeout` do modelo já configurado e, se estourar, o copilot informa que não conseguiu buscar em todas (opção 1, confirmada em 2026-10-15; recomendação aceita). Medição real fica para ajuste após o primeiro uso.
- **Q13** O que fazer com texto convertido acima do limite de tamanho? → **A**: guardar truncado no limite (`CONTEUDO_MAX_CARACTERES`, padrão 2000000) com marcador `truncado`, trechos por inteiro e envio sem falha (opção 1, confirmada em 2026-10-15; recomendação aceita).
- **Q14** Qual a fronteira de isolamento do copilot? → **A**: tenant e projeto da identidade (como o resto do sistema); Workspace só como rótulo e contexto (opção 1, confirmada em 2026-10-15; recomendação aceita).

#### Dúvidas abertas

- Nenhuma. As três dúvidas anteriores foram respondidas em 2026-10-15 (Q10, Q11 e Q12).

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
- **PR-002**: Toda consulta nasce da identidade (tenant, projeto e papel; o "Workspace da pessoa" é o escopo de tenant e projeto, DEC-013); nenhum identificador vindo do modelo substitui o escopo da identidade.
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
    And um texto convertido acima do limite é guardado truncado com o marcador `truncado` e os trechos ficam por inteiro
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

#### AC-013 — dados de outro tenant ou projeto não aparecem

**Cobre**: US-005, FR-001, FR-003, FR-010, NFR-001

```gherkin
@US-005 @FR-001 @FR-003 @FR-010 @NFR-001 @AC-013
Feature: Copilot com acesso ao sistema e ao conteúdo processado

  Scenario: Isolamento entre tenants e projetos
    Given a pessoa do tenant A e uma coleção com envios e documentos no tenant B
    When a pessoa pergunta sobre o conteúdo ou o estado da coleção do tenant B
    Then o copilot responde que não encontrou
    And nenhum trecho, nome ou contagem do tenant B entra no contexto do modelo
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

- **FR-001**: O sistema deve buscar, para cada pergunta, nos trechos indexados de todas as coleções do escopo da pessoa (tenant e projeto, incluindo todos os seus Workspaces; DEC-013), sem exigir coleção selecionada.
- **FR-002**: O sistema deve responder com base no conteúdo recuperado, qualquer que seja o tema do documento, e recusar com cortesia pedidos sem relação com o produto e seu conteúdo.
- **FR-003**: O sistema deve permitir consultar o estado operacional do Workspace: coleções, documentos, envios (situação, etapa, contagens e erro seguro), execuções e configurações não secretas.
- **FR-004**: O worker deve gravar, para cada documento cuja sincronização o destino confirmou, o texto convertido e os trechos (ordem, texto e etiquetas), ligados ao documento da coleção e ao envio de origem.
- **FR-005**: O sistema deve manter uma única versão do conteúdo processado por documento: nova versão o substitui, e apagar o documento ou a coleção o apaga junto.
- **FR-006**: O copilot deve sugerir o passo e o link da tela correspondente quando a resposta envolver uma ação, sem executar nenhuma escrita.
- **FR-007**: O seletor de coleção do chat deve ser opcional e atuar como filtro que restringe a busca à coleção escolhida.
- **FR-008**: Cada resposta sustentada por conteúdo ou por dado do sistema deve trazer fontes com o documento, a coleção, o envio ou a tela de origem, cada uma navegável.
- **FR-009**: Quando nenhuma fonte sustentar a resposta, o copilot deve dizer que não encontrou e não afirmar nada sem base.
- **FR-010**: O sistema deve limitar toda consulta ao tenant, projeto e papel da identidade da pessoa (DEC-013), sem aceitar escopo vindo do modelo ou do texto da pergunta.
- **FR-011**: O sistema não deve incluir credenciais de conexão (chaves, senhas, URLs com credencial) no contexto do modelo, na resposta nem nos logs.

#### Não funcionais

- **NFR-001**: Isolamento: nenhum dado de outro tenant ou projeto, ou fora do alcance do papel, entra no contexto do modelo. **Verificação**: testes de API e de contexto com dois Workspaces e papéis admin e member (AC-004, AC-005, AC-007, AC-009, AC-013, AC-014).
- **NFR-002**: Desempenho: o turno com busca em até 10 coleções responde dentro do tempo limite já configurado do modelo, com o número de trechos recuperados limitado por turno. **Verificação**: teste com busca simulada em 10 coleções e inspeção do limite de trechos; o alvo é o tempo limite já configurado, sem número novo (Q12, confirmado em 2026-10-15).
- **NFR-003**: Acessibilidade: seletor, fontes e links operáveis por teclado, com rótulo que identifica o destino, e respostas anunciadas pela região de mensagens ao vivo. **Verificação**: testes de componente com `axe-core` e de teclado.
- **NFR-004**: Privacidade: credenciais não aparecem em prompt, resposta nem log, e o erro exposto é genérico. **Verificação**: teste que inspeciona o contexto enviado ao modelo e os logs com uma chave conhecida.

#### Erros e casos-limite

- Coleção sem documentos indexados selecionada como filtro → informa que a coleção ainda não tem documentos, sem consultar o modelo (comportamento atual preservado).
- Falha do modelo, da busca vetorial ou do tempo limite → mensagem genérica já usada, sem detalhe interno; nada é gravado como resposta.
- Documento enviado antes desta entrega, sem conteúdo processado guardado → o copilot informa a limitação e responde apenas pelo conteúdo indexado.
- Conexão desativada ou coleção apagada → a coleção sai da busca e das fontes; o copilot não a menciona como disponível.
- Pergunta ambígua sobre várias coleções → o copilot lista as coleções candidatas nas fontes e pede ao usuário que indique o filtro.
- Texto convertido muito longo → o contexto do modelo recebe apenas trechos limitados por turno; o texto completo não é enviado de uma vez.
- Texto convertido acima do limite `CONTEUDO_MAX_CARACTERES` (padrão 2000000 caracteres) → o texto é guardado truncado no limite com `truncado` verdadeiro, os trechos com etiquetas são guardados por inteiro, o envio não falha e o copilot informa que o texto está incompleto (DEC-012).

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
specs/completed/0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado/
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
| ConteudoDocumento (`conteudos_documento`) | `id` (texto de 36), `documento_id` único | `texto` (texto livre, Markdown convertido); `trechos` (JSON: lista de `ordem`, `texto`, `etiquetas` como pares rótulo/valor); `envio_id` (envio que gerou a versão); `truncado` (booleano; verdadeiro quando o texto passou do limite `CONTEUDO_MAX_CARACTERES` e foi cortado, padrão 2000000); `atualizado_em`. Uma versão por documento | 1:1 com `DocumentoColecao`; N:1 com `Envio` |
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

- A revisão visual ocorre durante a implementação, mesmo sem pedido, e confere bordas, espaçamentos, margens, padding e tipografia do painel nos estados (sem fontes, uma fonte, muitas fontes, nome longo, erro, sem resultado), em 375 px e 1280 px e nos temas claro e escuro. Registrar a forma de conferência, viewport, estados, achados e ajustes na tarefa.

#### APIs expostas

- `POST /api/v1/assistente/conversas/{id}/mensagens`: corpo `{ texto, colecao_id? }`; resposta `{ mensagem_pessoa, mensagem_assistente }` em que `fontes` passa a ser lista de objetos `{ tipo, rotulo, colecao_id?, documento?, envio_id?, rota }` (textos simples antigos continuam legíveis). Erros: 404 para coleção fora do escopo, 409 para coleção sem documentos, 502 genérico para falha do modelo. Mesma versão `/api/v1`; mudança compatível.

#### APIs externas utilizadas

- Provedor de chat configurado em `llm` (`ProviderFactory.create_chat_model`), com o `timeout` existente e sem retry novo; falha vira a mensagem genérica. Embeddings e Qdrant das conexões de cada coleção, já usados por `query_base`.

#### Documentação das APIs consultadas

- Nenhuma documentação externa consultada; contratos internos em `src/pipeline/service.py` e `src/app/routers/assistente.py`.

#### Eventos e outros contratos

- Contrato do grafo: `executar_turno(..., colecoes=None, estado=None, processado=None, base=None)` com callables que devolvem dados e fontes já filtrados pela identidade. Sem eventos novos.

### 11. Estratégia TDD

- **Unidade**: componentes React (`SeletorColecao`, `FontesDaResposta`, `ListaMensagens`) com Vitest e Testing Library, e o grafo do assistente (`tests/test_assistente_grafo.py`) com modelo e recuperadores de teste.
- **Integração/contrato**: API do assistente (`tests/test_app_assistente_contexto.py`, `tests/test_app_assistente.py`) com sessão real por pessoa, modelo e busca vetorial de teste; worker de envio (`tests/test_app_conteudo_documento.py`) com armazém e embeddings falsos; exclusão (`tests/test_app_colecoes_documentos.py`).
- **BDD/aceite**: o Gherkin da seção 6 orienta o desenho dos testes; não há arquivos `.feature`. Contratos fixados pelos testes: `tests/_copilot.py` (classificação `[CLASSIFICAR]`, `LIMITE_DE_TRECHOS`, `conteudo_max_caracteres`, forma de `ConteudoDocumento` e da fonte estruturada).
- **Runner TDD**: Pytest (`.venv/bin/python -m pytest`) e Ruff no backend; Vitest (`npm --prefix frontend run test:tdd`) no frontend.
- **E2E**: não aplicável; a jornada completa com modelo real fica para o ensaio de fechamento (T035).
- **Verificação manual**: a conferência visual do painel em 375 px e 1280 px, nos dois temas, nas tarefas de interface e na T035.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, US-004, FR-001, FR-002, FR-007, FR-008, NFR-002, AC-001 | AC-001 na seção 6 | `test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte` em tests/test_app_assistente_contexto.py com marcador próprio `SPECSFY: SPEC-0031 US-001 US-004 FR-001 FR-002 FR-007 FR-008 NFR-002 AC-001` | RED 2026-10-15: asserção: só a coleção de conhecimento recebeu busca; as coleções "Manuais" e "Políticas" não foram consultadas | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-001, FR-001, FR-007, NFR-003, AC-002 | AC-002 na seção 6 | `começa em Todas as coleções, filtra pelo teclado e limpa o filtro` em frontend/src/features/assistente/SeletorColecao.test.tsx com marcador próprio `SPECSFY: SPEC-0031 US-001 FR-001 FR-007 NFR-003 AC-002` | RED 2026-10-15: `TestingLibraryElementError`: não existe combobox com o nome "Filtrar por coleção (opcional)" | GREEN 2026-10-15: `npm --prefix frontend run test:tdd -- src/features/assistente/SeletorColecao.test.tsx` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-001, FR-001, FR-007, NFR-003, AC-002 | AC-002 na seção 6 | `test_filtro_de_colecao_restringe_busca_e_fontes` em tests/test_app_assistente_contexto.py com marcador próprio `SPECSFY: SPEC-0031 US-001 FR-001 FR-007 NFR-003 AC-002` | RED 2026-10-15: asserção: as fontes ainda não são objetos estruturados (`{}` vazio em vez de `prazo-politicas.md`); o filtro por `colecao_id` já existia e fica como caracterização | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-001, FR-002, FR-007, FR-008, NFR-002, AC-003 | AC-003 na seção 6 | `test_colecao_selecionada_responde_tema_fora_de_rag_dentro_do_prazo` em tests/test_app_assistente_contexto.py com marcador próprio `SPECSFY: SPEC-0031 US-001 FR-002 FR-007 FR-008 NFR-002 AC-003` | RED 2026-10-15: `Failed`: `src.app.assistente_contexto` ainda não existe (`LIMITE_DE_TRECHOS`) | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-002, FR-003, FR-006, FR-011, NFR-001, NFR-004, AC-004 | AC-004 na seção 6 | `test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro` em tests/test_app_assistente_contexto.py com marcador próprio `SPECSFY: SPEC-0031 US-002 FR-003 FR-006 FR-011 NFR-001 NFR-004 AC-004` | RED 2026-10-15: asserção: `failed` não aparece no contexto enviado ao modelo (o estado do envio não chega a ele) | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-002, FR-003, FR-006, NFR-001, AC-005 | AC-005 na seção 6 | `test_pedido_de_acao_orienta_sem_escrever` em tests/test_app_assistente_contexto.py com marcador próprio `SPECSFY: SPEC-0031 US-002 FR-003 FR-006 NFR-001 AC-005` | RED 2026-10-15: asserção: a rota da tela de documentos da coleção não aparece no contexto | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-002, US-005, FR-003, FR-011, NFR-004, AC-006 | AC-006 na seção 6 | `test_configuracao_expoe_modelo_e_divisao_sem_credenciais` em tests/test_app_assistente_contexto.py com marcador próprio `SPECSFY: SPEC-0031 US-002 US-005 FR-003 FR-011 NFR-004 AC-006` | RED 2026-10-15: asserção: `text-embedding-3-small` não aparece no contexto | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-003, FR-004, FR-005, NFR-001, AC-007 | AC-007 na seção 6 | `test_conclusao_do_documento_guarda_texto_e_trechos_com_etiquetas` em tests/test_app_conteudo_documento.py com marcador próprio `SPECSFY: SPEC-0031 US-003 FR-004 FR-005 NFR-001 AC-007` | RED 2026-10-15: `Failed`: `src.app.models.ConteudoDocumento` ainda não existe | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-003, FR-004, FR-005, NFR-001, AC-007 | AC-007 na seção 6 | `test_texto_acima_do_limite_e_guardado_truncado_com_marcador` em tests/test_app_conteudo_documento.py com marcador próprio `SPECSFY: SPEC-0031 US-003 FR-004 FR-005 NFR-001 AC-007` | RED 2026-10-15: `AssertionError`: `AppSettings.conteudo_max_caracteres` ainda não existe | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-003, FR-002, FR-004, NFR-002, AC-008 | AC-008 na seção 6 | `test_pergunta_por_etiqueta_lista_trechos_do_conteudo_guardado` em tests/test_app_assistente_contexto.py com marcador próprio `SPECSFY: SPEC-0031 US-003 FR-002 FR-004 NFR-002 AC-008` | RED 2026-10-15: `Failed`: `src.app.models.ConteudoDocumento` ainda não existe | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-003, FR-004, FR-005, NFR-001, AC-009 | AC-009 na seção 6 | `test_nova_versao_substitui_e_reenvio_identico_nao_altera` em tests/test_app_conteudo_documento.py com marcador próprio `SPECSFY: SPEC-0031 US-003 FR-004 FR-005 NFR-001 AC-009` | RED 2026-10-15: `Failed`: `src.app.models.ConteudoDocumento` ainda não existe | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-003, FR-005, FR-009, FR-010, AC-010 | AC-010 na seção 6 | `test_apagar_documento_e_colecao_remove_o_conteudo_guardado` em tests/test_app_colecoes_documentos.py com marcador próprio `SPECSFY: SPEC-0031 US-003 FR-005 FR-009 FR-010 AC-010` | RED 2026-10-15: `Failed`: `src.app.models.ConteudoDocumento` ainda não existe | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_colecoes_documentos.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-004, FR-002, FR-009, NFR-002, NFR-003, AC-011 | AC-011 na seção 6 | `test_sem_base_o_copilot_admite_que_nao_encontrou` em tests/test_assistente_grafo.py com marcador próprio `SPECSFY: SPEC-0031 US-004 FR-002 FR-009 NFR-002 NFR-003 AC-011` | RED 2026-10-15: `AssertionError`: `executar_turno` ainda não aceita `colecoes` (contrato dos recuperadores da SPEC-0031) | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_assistente_grafo.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-004, FR-002, FR-009, NFR-002, NFR-003, AC-011 | AC-011 na seção 6 | `anuncia a resposta de não encontrei pela região viva e sem violações do axe` em frontend/src/features/assistente/ListaMensagens.a11y.test.tsx com marcador próprio `SPECSFY: SPEC-0031 US-004 FR-002 FR-009 NFR-002 NFR-003 AC-011` | RED 2026-10-15: `Error`: Objects are not valid as a React child (fonte estruturada ainda renderizada como texto) | GREEN 2026-10-15: `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-004, FR-006, FR-008, NFR-003, AC-012 | AC-012 na seção 6 | `abre o destino da fonte pelo teclado com rótulo que identifica o destino` em frontend/src/features/assistente/FontesDaResposta.test.tsx com marcador próprio `SPECSFY: SPEC-0031 US-004 FR-006 FR-008 NFR-003 AC-012` | RED 2026-10-15: `AssertionError`: `@/features/assistente/FontesDaResposta` ainda não existe | GREEN 2026-10-15: `npm --prefix frontend run test:tdd -- src/features/assistente/FontesDaResposta.test.tsx` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-004, FR-006, FR-008, NFR-003, AC-012 | AC-012 na seção 6 | `test_resposta_traz_fontes_estruturadas_e_aceita_mensagens_antigas` em tests/test_app_assistente.py com marcador próprio `SPECSFY: SPEC-0031 US-004 FR-006 FR-008 NFR-003 AC-012` | RED 2026-10-15: asserção: as fontes ainda são texto simples (`[]`), sem objetos estruturados | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-005, FR-001, FR-003, FR-010, NFR-001, AC-013 | AC-013 na seção 6 | `test_outro_workspace_nao_entra_no_contexto` em tests/test_app_assistente_contexto.py com marcador próprio `SPECSFY: SPEC-0031 US-005 FR-001 FR-003 FR-010 NFR-001 AC-013` | RED 2026-10-15: asserção: a coleção do tenant dono não foi consultada (busca em todas as coleções ainda ausente), no controle positivo | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-005, FR-003, FR-010, NFR-001, AC-014 | AC-014 na seção 6 | `test_member_nao_recebe_configuracao_restrita_a_admin` em tests/test_app_assistente_contexto.py com marcador próprio `SPECSFY: SPEC-0031 US-005 FR-003 FR-010 NFR-001 AC-014` | RED 2026-10-15: asserção: `text-embedding-3-small` não aparece no contexto do admin (controle positivo) | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-005, FR-011, NFR-004, AC-015 | AC-015 na seção 6 | `test_credenciais_nao_entram_no_contexto_nem_nos_logs` em tests/test_app_assistente_contexto.py com marcador próprio `SPECSFY: SPEC-0031 US-005 FR-011 NFR-004 AC-015` | RED 2026-10-15: asserção: o contexto não traz a instrução de recusar `credenciais` | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |
| US-001, FR-002, FR-009, AC-016 | AC-016 na seção 6 | `test_assunto_fora_do_produto_e_recusado_sem_busca` em tests/test_assistente_grafo.py com marcador próprio `SPECSFY: SPEC-0031 US-001 FR-002 FR-009 AC-016` | RED 2026-10-15: `AssertionError`: `executar_turno` ainda não aceita `colecoes` | GREEN 2026-10-15: `.venv/bin/python -m pytest tests/test_assistente_grafo.py -q` | Pytest completo 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| US-001 | AC-001 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte -q` | Passed |
| US-001 | AC-002 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/SeletorColecao.test.tsx` | Passed |
| US-001 | AC-002 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_filtro_de_colecao_restringe_busca_e_fontes -q` | Passed |
| US-001 | AC-003 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_colecao_selecionada_responde_tema_fora_de_rag_dentro_do_prazo -q` | Passed |
| US-001 | AC-016 | Unidade | `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_assunto_fora_do_produto_e_recusado_sem_busca -q` | Passed |
| US-002 | AC-004 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro -q` | Passed |
| US-002 | AC-005 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pedido_de_acao_orienta_sem_escrever -q` | Passed |
| US-002 | AC-006 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_configuracao_expoe_modelo_e_divisao_sem_credenciais -q` | Passed |
| US-003 | AC-007 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_conclusao_do_documento_guarda_texto_e_trechos_com_etiquetas -q` | Passed |
| US-003 | AC-007 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_texto_acima_do_limite_e_guardado_truncado_com_marcador -q` | Passed |
| US-003 | AC-008 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_por_etiqueta_lista_trechos_do_conteudo_guardado -q` | Passed |
| US-003 | AC-009 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_nova_versao_substitui_e_reenvio_identico_nao_altera -q` | Passed |
| US-003 | AC-010 | Integração | `.venv/bin/python -m pytest tests/test_app_colecoes_documentos.py::test_apagar_documento_e_colecao_remove_o_conteudo_guardado -q` | Passed |
| US-004 | AC-001 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte -q` | Passed |
| US-004 | AC-011 | Unidade | `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_sem_base_o_copilot_admite_que_nao_encontrou -q` | Passed |
| US-004 | AC-011 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx` | Passed |
| US-004 | AC-012 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/FontesDaResposta.test.tsx` | Passed |
| US-004 | AC-012 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente.py::test_resposta_traz_fontes_estruturadas_e_aceita_mensagens_antigas -q` | Passed |
| US-005 | AC-006 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_configuracao_expoe_modelo_e_divisao_sem_credenciais -q` | Passed |
| US-005 | AC-013 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_outro_workspace_nao_entra_no_contexto -q` | Passed |
| US-005 | AC-014 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_member_nao_recebe_configuracao_restrita_a_admin -q` | Passed |
| US-005 | AC-015 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_credenciais_nao_entram_no_contexto_nem_nos_logs -q` | Passed |
| FR-001 | AC-001 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte -q` | Passed |
| FR-001 | AC-002 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/SeletorColecao.test.tsx` | Passed |
| FR-001 | AC-002 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_filtro_de_colecao_restringe_busca_e_fontes -q` | Passed |
| FR-001 | AC-013 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_outro_workspace_nao_entra_no_contexto -q` | Passed |
| FR-002 | AC-001 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte -q` | Passed |
| FR-002 | AC-003 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_colecao_selecionada_responde_tema_fora_de_rag_dentro_do_prazo -q` | Passed |
| FR-002 | AC-008 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_por_etiqueta_lista_trechos_do_conteudo_guardado -q` | Passed |
| FR-002 | AC-011 | Unidade | `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_sem_base_o_copilot_admite_que_nao_encontrou -q` | Passed |
| FR-002 | AC-011 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx` | Passed |
| FR-002 | AC-016 | Unidade | `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_assunto_fora_do_produto_e_recusado_sem_busca -q` | Passed |
| FR-003 | AC-004 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro -q` | Passed |
| FR-003 | AC-005 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pedido_de_acao_orienta_sem_escrever -q` | Passed |
| FR-003 | AC-006 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_configuracao_expoe_modelo_e_divisao_sem_credenciais -q` | Passed |
| FR-003 | AC-013 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_outro_workspace_nao_entra_no_contexto -q` | Passed |
| FR-003 | AC-014 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_member_nao_recebe_configuracao_restrita_a_admin -q` | Passed |
| FR-004 | AC-007 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_conclusao_do_documento_guarda_texto_e_trechos_com_etiquetas -q` | Passed |
| FR-004 | AC-007 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_texto_acima_do_limite_e_guardado_truncado_com_marcador -q` | Passed |
| FR-004 | AC-008 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_por_etiqueta_lista_trechos_do_conteudo_guardado -q` | Passed |
| FR-004 | AC-009 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_nova_versao_substitui_e_reenvio_identico_nao_altera -q` | Passed |
| FR-005 | AC-007 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_conclusao_do_documento_guarda_texto_e_trechos_com_etiquetas -q` | Passed |
| FR-005 | AC-007 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_texto_acima_do_limite_e_guardado_truncado_com_marcador -q` | Passed |
| FR-005 | AC-009 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_nova_versao_substitui_e_reenvio_identico_nao_altera -q` | Passed |
| FR-005 | AC-010 | Integração | `.venv/bin/python -m pytest tests/test_app_colecoes_documentos.py::test_apagar_documento_e_colecao_remove_o_conteudo_guardado -q` | Passed |
| FR-006 | AC-004 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro -q` | Passed |
| FR-006 | AC-005 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pedido_de_acao_orienta_sem_escrever -q` | Passed |
| FR-006 | AC-012 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/FontesDaResposta.test.tsx` | Passed |
| FR-006 | AC-012 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente.py::test_resposta_traz_fontes_estruturadas_e_aceita_mensagens_antigas -q` | Passed |
| FR-007 | AC-001 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte -q` | Passed |
| FR-007 | AC-002 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/SeletorColecao.test.tsx` | Passed |
| FR-007 | AC-002 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_filtro_de_colecao_restringe_busca_e_fontes -q` | Passed |
| FR-007 | AC-003 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_colecao_selecionada_responde_tema_fora_de_rag_dentro_do_prazo -q` | Passed |
| FR-008 | AC-001 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte -q` | Passed |
| FR-008 | AC-003 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_colecao_selecionada_responde_tema_fora_de_rag_dentro_do_prazo -q` | Passed |
| FR-008 | AC-012 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/FontesDaResposta.test.tsx` | Passed |
| FR-008 | AC-012 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente.py::test_resposta_traz_fontes_estruturadas_e_aceita_mensagens_antigas -q` | Passed |
| FR-009 | AC-010 | Integração | `.venv/bin/python -m pytest tests/test_app_colecoes_documentos.py::test_apagar_documento_e_colecao_remove_o_conteudo_guardado -q` | Passed |
| FR-009 | AC-011 | Unidade | `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_sem_base_o_copilot_admite_que_nao_encontrou -q` | Passed |
| FR-009 | AC-011 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx` | Passed |
| FR-009 | AC-016 | Unidade | `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_assunto_fora_do_produto_e_recusado_sem_busca -q` | Passed |
| FR-010 | AC-010 | Integração | `.venv/bin/python -m pytest tests/test_app_colecoes_documentos.py::test_apagar_documento_e_colecao_remove_o_conteudo_guardado -q` | Passed |
| FR-010 | AC-013 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_outro_workspace_nao_entra_no_contexto -q` | Passed |
| FR-010 | AC-014 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_member_nao_recebe_configuracao_restrita_a_admin -q` | Passed |
| FR-011 | AC-004 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro -q` | Passed |
| FR-011 | AC-006 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_configuracao_expoe_modelo_e_divisao_sem_credenciais -q` | Passed |
| FR-011 | AC-015 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_credenciais_nao_entram_no_contexto_nem_nos_logs -q` | Passed |
| NFR-001 | AC-004 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro -q` | Passed |
| NFR-001 | AC-005 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pedido_de_acao_orienta_sem_escrever -q` | Passed |
| NFR-001 | AC-007 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_conclusao_do_documento_guarda_texto_e_trechos_com_etiquetas -q` | Passed |
| NFR-001 | AC-007 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_texto_acima_do_limite_e_guardado_truncado_com_marcador -q` | Passed |
| NFR-001 | AC-009 | Integração | `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_nova_versao_substitui_e_reenvio_identico_nao_altera -q` | Passed |
| NFR-001 | AC-013 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_outro_workspace_nao_entra_no_contexto -q` | Passed |
| NFR-001 | AC-014 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_member_nao_recebe_configuracao_restrita_a_admin -q` | Passed |
| NFR-002 | AC-001 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte -q` | Passed |
| NFR-002 | AC-003 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_colecao_selecionada_responde_tema_fora_de_rag_dentro_do_prazo -q` | Passed |
| NFR-002 | AC-008 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_por_etiqueta_lista_trechos_do_conteudo_guardado -q` | Passed |
| NFR-002 | AC-011 | Unidade | `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_sem_base_o_copilot_admite_que_nao_encontrou -q` | Passed |
| NFR-002 | AC-011 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx` | Passed |
| NFR-003 | AC-002 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/SeletorColecao.test.tsx` | Passed |
| NFR-003 | AC-002 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_filtro_de_colecao_restringe_busca_e_fontes -q` | Passed |
| NFR-003 | AC-011 | Unidade | `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_sem_base_o_copilot_admite_que_nao_encontrou -q` | Passed |
| NFR-003 | AC-011 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx` | Passed |
| NFR-003 | AC-012 | Componente | `npm --prefix frontend run test:tdd -- src/features/assistente/FontesDaResposta.test.tsx` | Passed |
| NFR-003 | AC-012 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente.py::test_resposta_traz_fontes_estruturadas_e_aceita_mensagens_antigas -q` | Passed |
| NFR-004 | AC-004 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro -q` | Passed |
| NFR-004 | AC-006 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_configuracao_expoe_modelo_e_divisao_sem_credenciais -q` | Passed |
| NFR-004 | AC-015 | Integração | `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_credenciais_nao_entram_no_contexto_nem_nos_logs -q` | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: Passed (READY) em 2026-10-15
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/completed/0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado/spec.md`
- **Achados**: formato válido; 5 US, 11 FR e 4 NFR, 16 AC, cada ID com no mínimo 3 AC em `**Cobre**`; seção 10 completa para interface com pessoas. As três dúvidas abertas foram respondidas em 2026-10-15 (Q10, Q11, Q12; DEC-006 e DEC-011). Correção na própria etapa: a Definition of Done passou a exigir `.specsfy/DATABASE.md`, `PROJECT.md` e `.specsfy/RULES.md`. Sem BLOCKER.
- **FIND-ARCH-001** [P2] [Resolved] Limite de tamanho do texto convertido guardado por documento ainda não decidido (seção 16 delega às tarefas) — Refs: FR-005 — Evidence: src/app/tasks.py:243 — Effect: documentos muito grandes podem inflar o armazenamento do banco — Suggestion: fixar o limite e o comportamento ao exceder (truncar com aviso ou recusar guardar) em uma tarefa `[TEST]` antes do `[CODE]`.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed em 2026-10-15
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/completed/0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado/spec.md`
- **Achados**: 35 tarefas (20 `[TEST] [TDD]` com RED válido, 10 `[CODE]`, 4 `[DOC]` e a regressão final); 36 de 36 IDs cobertos; cada `US`, `FR`, `NFR` e a feature têm 3 ou mais casos TDD; `[CODE]` só depende de testes com RED. Decisões do plano: DEC-012 (limite do texto) e DEC-013 (isolamento por tenant e projeto). O teste de isolamento e o de `AC-014` têm controle positivo para não passarem sem a implementação. Contratos fixados em `tests/_copilot.py`.

#### Gate do Ato III — Entrega

- **Resultado**: Passed em 2026-10-15
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/completed/0031-copilot-com-acesso-ao-sistema-e-ao-conteudo-processado/spec.md . --full-chain`
- **Achados**: rastreabilidade 36/36 IDs; `verify_evidence` strict aprovado; Pytest 668 passed e 1 skipped anterior à spec; Vitest 239 passed; Ruff, ESLint e `tsc` limpos; build concluído; conferência visual no navegador em 375 e 1280 px, nos dois temas (`research/t035-*`); monitor CURRENT e `docs/` atual. Falhas conhecidas: nenhuma. Pendências fora do escopo: ensaio com o modelo de linguagem real e medição de latência com várias coleções (Q12), e conteúdo processado só para documentos enviados depois desta entrega.

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 o caso `test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte` falhando em tests/test_app_assistente_contexto.py — Refs: US-001, US-004, FR-001, FR-002, FR-007, FR-008, NFR-002, AC-001 — Depends: none
  - [x] **PREP**: Gherkin do AC-001 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte` escrito em tests/test_app_assistente_contexto.py com o marcador `SPECSFY: SPEC-0031 US-001 US-004 FR-001 FR-002 FR-007 FR-008 NFR-002 AC-001`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_sem_colecao_busca_em_todas_e_cita_a_fonte -q`: falhou por asserção: só a coleção de conhecimento recebeu busca; as coleções "Manuais" e "Políticas" não foram consultadas.
  - [x] **IMPROVE**: O caso usa `criar_base` duas vezes no mesmo tenant e fixa o contrato da fonte estruturada em `tests/_copilot.py`.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 o caso `começa em Todas as coleções, filtra pelo teclado e limpa o filtro` falhando em frontend/src/features/assistente/SeletorColecao.test.tsx — Refs: US-001, FR-001, FR-007, NFR-003, AC-002 — Depends: none
  - [x] **PREP**: Gherkin do AC-002 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo). Teste de interface: sem banco.
  - [x] **EXECUTE**: Caso `começa em Todas as coleções, filtra pelo teclado e limpa o filtro` escrito em frontend/src/features/assistente/SeletorColecao.test.tsx com o marcador `SPECSFY: SPEC-0031 US-001 FR-001 FR-007 NFR-003 AC-002`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features/assistente/SeletorColecao.test.tsx` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste de componente; a conferência visual ocorre na tarefa de interface que o torna GREEN.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `npm --prefix frontend run test:tdd -- src/features/assistente/SeletorColecao.test.tsx`: falhou por `TestingLibraryElementError`: não existe combobox com o nome "Filtrar por coleção (opcional)".
  - [x] **IMPROVE**: O teste antigo da SPEC-0030 ("Nenhuma") continua verde e será adaptado na T029 junto do rótulo novo.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-002 o caso `test_filtro_de_colecao_restringe_busca_e_fontes` falhando em tests/test_app_assistente_contexto.py — Refs: US-001, FR-001, FR-007, NFR-003, AC-002 — Depends: none
  - [x] **PREP**: Gherkin do AC-002 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_filtro_de_colecao_restringe_busca_e_fontes` escrito em tests/test_app_assistente_contexto.py com o marcador `SPECSFY: SPEC-0031 US-001 FR-001 FR-007 NFR-003 AC-002`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_filtro_de_colecao_restringe_busca_e_fontes -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_filtro_de_colecao_restringe_busca_e_fontes -q`: falhou por asserção: as fontes ainda não são objetos estruturados (`{}` vazio em vez de `prazo-politicas.md`); o filtro por `colecao_id` já existia e fica como caracterização.
  - [x] **IMPROVE**: Separei a prova do filtro (já existente) da prova da fonte estruturada para o RED apontar só o que falta.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-003 o caso `test_colecao_selecionada_responde_tema_fora_de_rag_dentro_do_prazo` falhando em tests/test_app_assistente_contexto.py — Refs: US-001, FR-002, FR-007, FR-008, NFR-002, AC-003 — Depends: none
  - [x] **PREP**: Gherkin do AC-003 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_colecao_selecionada_responde_tema_fora_de_rag_dentro_do_prazo` escrito em tests/test_app_assistente_contexto.py com o marcador `SPECSFY: SPEC-0031 US-001 FR-002 FR-007 FR-008 NFR-002 AC-003`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_colecao_selecionada_responde_tema_fora_de_rag_dentro_do_prazo -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_colecao_selecionada_responde_tema_fora_de_rag_dentro_do_prazo -q`: falhou por `Failed`: `src.app.assistente_contexto` ainda não existe (`LIMITE_DE_TRECHOS`).
  - [x] **IMPROVE**: O teto de trechos fica fixado entre 1 e 20 sem número mágico, para a implementação escolher o valor dentro da NFR-002.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-004 o caso `test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro` falhando em tests/test_app_assistente_contexto.py — Refs: US-002, FR-003, FR-006, FR-011, NFR-001, NFR-004, AC-004 — Depends: none
  - [x] **PREP**: Gherkin do AC-004 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro` escrito em tests/test_app_assistente_contexto.py com o marcador `SPECSFY: SPEC-0031 US-002 FR-003 FR-006 FR-011 NFR-001 NFR-004 AC-004`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_envio_com_falha_e_explicado_com_estado_etapa_e_erro_seguro -q`: falhou por asserção: `failed` não aparece no contexto enviado ao modelo (o estado do envio não chega a ele).
  - [x] **IMPROVE**: O caso usa `member`, para provar que o estado do envio não é restrito a admin (DEC-011).

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-005 o caso `test_pedido_de_acao_orienta_sem_escrever` falhando em tests/test_app_assistente_contexto.py — Refs: US-002, FR-003, FR-006, NFR-001, AC-005 — Depends: none
  - [x] **PREP**: Gherkin do AC-005 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_pedido_de_acao_orienta_sem_escrever` escrito em tests/test_app_assistente_contexto.py com o marcador `SPECSFY: SPEC-0031 US-002 FR-003 FR-006 NFR-001 AC-005`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pedido_de_acao_orienta_sem_escrever -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pedido_de_acao_orienta_sem_escrever -q`: falhou por asserção: a rota da tela de documentos da coleção não aparece no contexto.
  - [x] **IMPROVE**: A prova de que nada é escrito compara as contagens de Coleção, Documento, Envio e Workspace e conta só 2 mensagens novas.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-006 o caso `test_configuracao_expoe_modelo_e_divisao_sem_credenciais` falhando em tests/test_app_assistente_contexto.py — Refs: US-002, US-005, FR-003, FR-011, NFR-004, AC-006 — Depends: none
  - [x] **PREP**: Gherkin do AC-006 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_configuracao_expoe_modelo_e_divisao_sem_credenciais` escrito em tests/test_app_assistente_contexto.py com o marcador `SPECSFY: SPEC-0031 US-002 US-005 FR-003 FR-011 NFR-004 AC-006`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_configuracao_expoe_modelo_e_divisao_sem_credenciais -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_configuracao_expoe_modelo_e_divisao_sem_credenciais -q`: falhou por asserção: `text-embedding-3-small` não aparece no contexto.
  - [x] **IMPROVE**: Usei tamanho 811 e sobreposição 137 para não colidir com números que já aparecem no prompt.

- [x] T008 [TEST] [TDD] [US-003] Derivar do AC-007 o caso `test_conclusao_do_documento_guarda_texto_e_trechos_com_etiquetas` falhando em tests/test_app_conteudo_documento.py — Refs: US-003, FR-004, FR-005, NFR-001, AC-007 — Depends: none
  - [x] **PREP**: Gherkin do AC-007 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_conclusao_do_documento_guarda_texto_e_trechos_com_etiquetas` escrito em tests/test_app_conteudo_documento.py com o marcador `SPECSFY: SPEC-0031 US-003 FR-004 FR-005 NFR-001 AC-007`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_conclusao_do_documento_guarda_texto_e_trechos_com_etiquetas -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_conclusao_do_documento_guarda_texto_e_trechos_com_etiquetas -q`: falhou por `Failed`: `src.app.models.ConteudoDocumento` ainda não existe.
  - [x] **IMPROVE**: O contrato do registro (`ordem` a partir de 1, `etiquetas` como dicionário) ficou escrito no docstring de `tests/_copilot.py`.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-007 o caso `test_texto_acima_do_limite_e_guardado_truncado_com_marcador` falhando em tests/test_app_conteudo_documento.py — Refs: US-003, FR-004, FR-005, NFR-001, AC-007 — Depends: none
  - [x] **PREP**: Gherkin do AC-007 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_texto_acima_do_limite_e_guardado_truncado_com_marcador` escrito em tests/test_app_conteudo_documento.py com o marcador `SPECSFY: SPEC-0031 US-003 FR-004 FR-005 NFR-001 AC-007`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_texto_acima_do_limite_e_guardado_truncado_com_marcador -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_texto_acima_do_limite_e_guardado_truncado_com_marcador -q`: falhou por `AssertionError`: `AppSettings.conteudo_max_caracteres` ainda não existe.
  - [x] **IMPROVE**: O limite entra por `AppSettings`, injetado pelo entrypoint, porque `src/app` não lê o ambiente (regra do projeto); a variável de ambiente é lida em `src/app/main.py`.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-008 o caso `test_pergunta_por_etiqueta_lista_trechos_do_conteudo_guardado` falhando em tests/test_app_assistente_contexto.py — Refs: US-003, FR-002, FR-004, NFR-002, AC-008 — Depends: none
  - [x] **PREP**: Gherkin do AC-008 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_pergunta_por_etiqueta_lista_trechos_do_conteudo_guardado` escrito em tests/test_app_assistente_contexto.py com o marcador `SPECSFY: SPEC-0031 US-003 FR-002 FR-004 NFR-002 AC-008`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_por_etiqueta_lista_trechos_do_conteudo_guardado -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_pergunta_por_etiqueta_lista_trechos_do_conteudo_guardado -q`: falhou por `Failed`: `src.app.models.ConteudoDocumento` ainda não existe.
  - [x] **IMPROVE**: O teste grava o conteúdo direto no banco, assim não depende do worker (T008) para provar a consulta.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-009 o caso `test_nova_versao_substitui_e_reenvio_identico_nao_altera` falhando em tests/test_app_conteudo_documento.py — Refs: US-003, FR-004, FR-005, NFR-001, AC-009 — Depends: none
  - [x] **PREP**: Gherkin do AC-009 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_nova_versao_substitui_e_reenvio_identico_nao_altera` escrito em tests/test_app_conteudo_documento.py com o marcador `SPECSFY: SPEC-0031 US-003 FR-004 FR-005 NFR-001 AC-009`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_nova_versao_substitui_e_reenvio_identico_nao_altera -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py::test_nova_versao_substitui_e_reenvio_identico_nao_altera -q`: falhou por `Failed`: `src.app.models.ConteudoDocumento` ainda não existe.
  - [x] **IMPROVE**: O reenvio idêntico é provado por `atualizado_em` e `envio_id` inalterados, não só pela contagem de linhas.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-010 o caso `test_apagar_documento_e_colecao_remove_o_conteudo_guardado` falhando em tests/test_app_colecoes_documentos.py — Refs: US-003, FR-005, FR-009, FR-010, AC-010 — Depends: none
  - [x] **PREP**: Gherkin do AC-010 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_apagar_documento_e_colecao_remove_o_conteudo_guardado` escrito em tests/test_app_colecoes_documentos.py com o marcador `SPECSFY: SPEC-0031 US-003 FR-005 FR-009 FR-010 AC-010`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_colecoes_documentos.py::test_apagar_documento_e_colecao_remove_o_conteudo_guardado -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_colecoes_documentos.py::test_apagar_documento_e_colecao_remove_o_conteudo_guardado -q`: falhou por `Failed`: `src.app.models.ConteudoDocumento` ainda não existe.
  - [x] **IMPROVE**: O caso confere a ordem da exclusão (documento primeiro, coleção depois) e a resposta "não encontrei" entre as duas.

- [x] T013 [TEST] [TDD] [US-004] Derivar do AC-011 o caso `test_sem_base_o_copilot_admite_que_nao_encontrou` falhando em tests/test_assistente_grafo.py — Refs: US-004, FR-002, FR-009, NFR-002, NFR-003, AC-011 — Depends: none
  - [x] **PREP**: Gherkin do AC-011 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_sem_base_o_copilot_admite_que_nao_encontrou` escrito em tests/test_assistente_grafo.py com o marcador `SPECSFY: SPEC-0031 US-004 FR-002 FR-009 NFR-002 NFR-003 AC-011`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_sem_base_o_copilot_admite_que_nao_encontrou -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_sem_base_o_copilot_admite_que_nao_encontrou -q`: falhou por `AssertionError`: `executar_turno` ainda não aceita `colecoes` (contrato dos recuperadores da SPEC-0031).
  - [x] **IMPROVE**: A verificação por `inspect.signature` evita que o RED seja um `TypeError` de argumento inesperado.

- [x] T014 [TEST] [TDD] [US-004] Derivar do AC-011 o caso `anuncia a resposta de não encontrei pela região viva e sem violações do axe` falhando em frontend/src/features/assistente/ListaMensagens.a11y.test.tsx — Refs: US-004, FR-002, FR-009, NFR-002, NFR-003, AC-011 — Depends: none
  - [x] **PREP**: Gherkin do AC-011 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo). Teste de interface: sem banco.
  - [x] **EXECUTE**: Caso `anuncia a resposta de não encontrei pela região viva e sem violações do axe` escrito em frontend/src/features/assistente/ListaMensagens.a11y.test.tsx com o marcador `SPECSFY: SPEC-0031 US-004 FR-002 FR-009 NFR-002 NFR-003 AC-011`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste de componente; a conferência visual ocorre na tarefa de interface que o torna GREEN.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `npm --prefix frontend run test:tdd -- src/features/assistente/ListaMensagens.a11y.test.tsx`: falhou por `Error`: Objects are not valid as a React child (fonte estruturada ainda renderizada como texto).
  - [x] **IMPROVE**: A primeira versão passava sem implementação (a região viva já existe); incluí uma resposta com fonte estruturada para o teste exigir o comportamento novo.

- [x] T015 [TEST] [TDD] [US-004] Derivar do AC-012 o caso `abre o destino da fonte pelo teclado com rótulo que identifica o destino` falhando em frontend/src/features/assistente/FontesDaResposta.test.tsx — Refs: US-004, FR-006, FR-008, NFR-003, AC-012 — Depends: none
  - [x] **PREP**: Gherkin do AC-012 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo). Teste de interface: sem banco.
  - [x] **EXECUTE**: Caso `abre o destino da fonte pelo teclado com rótulo que identifica o destino` escrito em frontend/src/features/assistente/FontesDaResposta.test.tsx com o marcador `SPECSFY: SPEC-0031 US-004 FR-006 FR-008 NFR-003 AC-012`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd -- src/features/assistente/FontesDaResposta.test.tsx` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste de componente; a conferência visual ocorre na tarefa de interface que o torna GREEN.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `npm --prefix frontend run test:tdd -- src/features/assistente/FontesDaResposta.test.tsx`: falhou por `AssertionError`: `@/features/assistente/FontesDaResposta` ainda não existe.
  - [x] **IMPROVE**: O rótulo acessível fixa o formato "Abrir documento X da coleção Y".

- [x] T016 [TEST] [TDD] [US-004] Derivar do AC-012 o caso `test_resposta_traz_fontes_estruturadas_e_aceita_mensagens_antigas` falhando em tests/test_app_assistente.py — Refs: US-004, FR-006, FR-008, NFR-003, AC-012 — Depends: none
  - [x] **PREP**: Gherkin do AC-012 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_resposta_traz_fontes_estruturadas_e_aceita_mensagens_antigas` escrito em tests/test_app_assistente.py com o marcador `SPECSFY: SPEC-0031 US-004 FR-006 FR-008 NFR-003 AC-012`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente.py::test_resposta_traz_fontes_estruturadas_e_aceita_mensagens_antigas -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente.py::test_resposta_traz_fontes_estruturadas_e_aceita_mensagens_antigas -q`: falhou por asserção: as fontes ainda são texto simples (`[]`), sem objetos estruturados.
  - [x] **IMPROVE**: O caso grava uma conversa antiga com fonte em texto para provar a compatibilidade na mesma resposta.

- [x] T017 [TEST] [TDD] [US-005] Derivar do AC-013 o caso `test_outro_workspace_nao_entra_no_contexto` falhando em tests/test_app_assistente_contexto.py — Refs: US-005, FR-001, FR-003, FR-010, NFR-001, AC-013 — Depends: none
  - [x] **PREP**: Gherkin do AC-013 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_outro_workspace_nao_entra_no_contexto` escrito em tests/test_app_assistente_contexto.py com o marcador `SPECSFY: SPEC-0031 US-005 FR-001 FR-003 FR-010 NFR-001 AC-013`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_outro_workspace_nao_entra_no_contexto -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_outro_workspace_nao_entra_no_contexto -q`: falhou por asserção: a coleção do tenant dono não foi consultada (busca em todas as coleções ainda ausente), no controle positivo.
  - [x] **IMPROVE**: A primeira versão passava hoje porque nada era buscado entre coleções; o controle positivo do tenant dono prova a busca ampla e o isolamento juntos (DEC-013).

- [x] T018 [TEST] [TDD] [US-005] Derivar do AC-014 o caso `test_member_nao_recebe_configuracao_restrita_a_admin` falhando em tests/test_app_assistente_contexto.py — Refs: US-005, FR-003, FR-010, NFR-001, AC-014 — Depends: none
  - [x] **PREP**: Gherkin do AC-014 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_member_nao_recebe_configuracao_restrita_a_admin` escrito em tests/test_app_assistente_contexto.py com o marcador `SPECSFY: SPEC-0031 US-005 FR-003 FR-010 NFR-001 AC-014`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_member_nao_recebe_configuracao_restrita_a_admin -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_member_nao_recebe_configuracao_restrita_a_admin -q`: falhou por asserção: `text-embedding-3-small` não aparece no contexto do admin (controle positivo).
  - [x] **IMPROVE**: O mesmo teste compara admin e member sobre a mesma coleção, para a diferença vir só do papel.

- [x] T019 [TEST] [TDD] [US-005] Derivar do AC-015 o caso `test_credenciais_nao_entram_no_contexto_nem_nos_logs` falhando em tests/test_app_assistente_contexto.py — Refs: US-005, FR-011, NFR-004, AC-015 — Depends: none
  - [x] **PREP**: Gherkin do AC-015 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_credenciais_nao_entram_no_contexto_nem_nos_logs` escrito em tests/test_app_assistente_contexto.py com o marcador `SPECSFY: SPEC-0031 US-005 FR-011 NFR-004 AC-015`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_credenciais_nao_entram_no_contexto_nem_nos_logs -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_app_assistente_contexto.py::test_credenciais_nao_entram_no_contexto_nem_nos_logs -q`: falhou por asserção: o contexto não traz a instrução de recusar `credenciais`.
  - [x] **IMPROVE**: `caplog` em nível DEBUG cobre todos os loggers, não só `src.app.assistente`.

- [x] T020 [TEST] [TDD] [US-001] Derivar do AC-016 o caso `test_assunto_fora_do_produto_e_recusado_sem_busca` falhando em tests/test_assistente_grafo.py — Refs: US-001, FR-002, FR-009, AC-016 — Depends: none
  - [x] **PREP**: Gherkin do AC-016 lido na seção 6; `check_database_safety.mjs` SAFE para os testes Python (schema exclusivo por teste, sem comando destrutivo).
  - [x] **EXECUTE**: Caso `test_assunto_fora_do_produto_e_recusado_sem_busca` escrito em tests/test_assistente_grafo.py com o marcador `SPECSFY: SPEC-0031 US-001 FR-002 FR-009 AC-016`, sem criar nem executar `.feature`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_assunto_fora_do_produto_e_recusado_sem_busca -q` executado e RED observado.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa um teste, sem alterar tela.
  - [x] **EVIDENCE**: RED observado em 2026-10-15 com `.venv/bin/python -m pytest tests/test_assistente_grafo.py::test_assunto_fora_do_produto_e_recusado_sem_busca -q`: falhou por `AssertionError`: `executar_turno` ainda não aceita `colecoes`.
  - [x] **IMPROVE**: O contrato da classificação (`[CLASSIFICAR]` e `nenhuma`) ficou escrito em `tests/_copilot.py`.

#### Fase 2 — Persistência e worker (US-003)

- [x] T021 [CODE] [US-003] Criar a revisão Alembic `0031_conteudo_documento`, o modelo `ConteudoDocumento` e as funções de repositório para gravar, substituir, ler e apagar o conteúdo por documento em alembic/versions/0031_conteudo_documento.py, src/app/models.py e src/app/repo.py — Refs: US-003, FR-004, FR-005, FR-009, FR-010, NFR-001, AC-007, AC-009, AC-010 — Depends: T008, T009, T011, T012
  - [x] **PREP**: RED confirmado nas tarefas de teste predecessoras; `check_database_safety.mjs` SAFE para os comandos Pytest (schema exclusivo por teste); documentação reconstruída por `$specsfy-documentator` ao fim do lote (monitor CURRENT).
  - [x] **EXECUTE**: Revisão `0031_conteudo_documento` (sucede `0033_avisos_conversao`, aditiva, índice único em `documento_id`, índice em `envio_id`, downgrade só da tabela nova), modelo `ConteudoDocumento` e, em `src/app/repo.py`, `obter_conteudo`, `salvar_conteudo` (substitui: uma versão por documento), `apagar_conteudo_do_documento` e `apagar_conteudos_da_colecao`.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_migrations.py tests/test_app_models.py -q`: 8 passed; Ruff limpo em `src` e `alembic`.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN do schema (upgrade cria a tabela e o downgrade a remove) e dos modelos; os casos de AC-007, AC-009 e AC-010 passam nas tarefas T022 e T023. Arquivos: `alembic/versions/0031_conteudo_documento.py`, `src/app/models.py`, `src/app/repo.py`.
  - [x] **IMPROVE**: A chave estrangeira obriga a apagar o conteúdo antes do documento; isso virou duas funções de repositório separadas, e as rotas de exclusão as usam, em vez de depender de `ON DELETE CASCADE` implícito.
  <!-- specsfy:evidence {"task": "T021", "refs": ["US-003", "FR-004", "FR-005", "FR-009", "FR-010", "NFR-001", "AC-007", "AC-009", "AC-010"], "files": ["alembic/versions/0031_conteudo_documento.py", "src/app/models.py", "src/app/repo.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}]} -->

- [x] T022 [CODE] [US-003] Gravar o conteúdo processado no worker, na mesma transação da versão do documento, com o limite `CONTEUDO_MAX_CARACTERES` e o marcador `truncado`, em src/app/tasks.py e src/app/settings.py — Refs: US-003, FR-004, FR-005, NFR-001, AC-007, AC-009 — Depends: T008, T009, T011, T021
  - [x] **PREP**: RED confirmado nas tarefas de teste predecessoras; `check_database_safety.mjs` SAFE para os comandos Pytest (schema exclusivo por teste); documentação reconstruída por `$specsfy-documentator` ao fim do lote (monitor CURRENT).
  - [x] **EXECUTE**: `_registrar_documento` grava `ConteudoDocumento` junto da versão (mesma transação), com o texto lido do diretório materializado (`caminho_relativo`), trechos com `ordem` a partir de 1 e etiquetas do envio, e corta o texto em `AppSettings.conteudo_max_caracteres` (padrão 2000000, lido de `APP_CONTEUDO_MAX_CARACTERES` em `src/app/main.py`) marcando `truncado`; reenvio idêntico mantém o retorno antecipado e não regrava.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_app_conteudo_documento.py tests/test_app_colecoes_documentos.py tests/test_app_tasks.py tests/test_app_envios_sync.py -q`: 11 passed.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN de AC-007 (conteúdo, ordem, etiquetas e ausência de conteúdo quando o destino falha), do limite (`truncado`) e de AC-009 (nova versão substitui, reenvio idêntico não altera `atualizado_em` nem `envio_id`).
  - [x] **IMPROVE**: O limite entra por `AppSettings`, não por `os.environ` em `src/app`, para respeitar a regra de que só o entrypoint lê o ambiente; o caminho do arquivo é resolvido e confinado ao diretório do envio antes da leitura.
  <!-- specsfy:evidence {"task": "T022", "refs": ["US-003", "FR-004", "FR-005", "NFR-001", "AC-007", "AC-009"], "files": ["src/app/tasks.py", "src/app/settings.py", "src/app/main.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_app_conteudo_documento.py tests/test_app_colecoes_documentos.py tests/test_app_tasks.py tests/test_app_envios_sync.py -q", "exit": 0}]} -->

- [x] T023 [CODE] [US-003] Apagar o conteúdo guardado junto do documento e da coleção, na mesma transação, em src/app/routers/colecoes.py e src/app/colecoes.py — Refs: US-003, FR-005, FR-009, FR-010, AC-010 — Depends: T012, T021
  - [x] **PREP**: RED confirmado nas tarefas de teste predecessoras; `check_database_safety.mjs` SAFE para os comandos Pytest (schema exclusivo por teste); documentação reconstruída por `$specsfy-documentator` ao fim do lote (monitor CURRENT).
  - [x] **EXECUTE**: `apagar_documento` remove o conteúdo e depois o documento; `apagar_colecao` chama `repo.apagar_conteudos_da_colecao` antes de apagar os documentos, na mesma transação e só depois de o destino confirmar a exclusão.
  - [x] **VERIFY**: Suítes relacionadas (coleções, documentos, falhas e permissões) dentro do comando de 90 testes: 90 passed.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN de AC-010: o conteúdo de `manual.md` some primeiro, o de `guia.md` some com a coleção e a pergunta sobre o texto apagado recebe "não encontrei". Arquivos: `src/app/routers/colecoes.py`, `src/app/repo.py`.
  - [x] **IMPROVE**: Nenhuma melhoria necessária além da ordem de exclusão: o caso já cobre a falha do destino sem estado parcial (`test_app_colecoes_falhas.py` segue verde).
  <!-- specsfy:evidence {"task": "T023", "refs": ["US-003", "FR-005", "FR-009", "FR-010", "AC-010"], "files": ["src/app/routers/colecoes.py", "src/app/repo.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_app_assistente_contexto.py tests/test_app_assistente.py tests/test_app_conteudo_documento.py tests/test_app_colecoes_documentos.py tests/test_assistente_grafo.py tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_falhas.py tests/test_app_tasks.py tests/test_app_envios_sync.py tests/test_app_conexoes.py tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}]} -->

#### Fase 3 — Contexto e grafo do copilot (US-001, US-002, US-005)

- [x] T024 [CODE] [US-001] Criar `montar_contexto` com busca em todas as coleções do Workspace, filtro opcional, limite de trechos por turno e fontes estruturadas em src/app/assistente_contexto.py e src/app/repo.py — Refs: US-001, US-004, US-005, FR-001, FR-002, FR-003, FR-007, FR-008, FR-010, NFR-001, NFR-002, NFR-003, AC-001, AC-002, AC-013 — Depends: T001, T003, T017
  - [x] **PREP**: RED confirmado nas tarefas de teste predecessoras; `check_database_safety.mjs` SAFE para os comandos Pytest (schema exclusivo por teste); documentação reconstruída por `$specsfy-documentator` ao fim do lote (monitor CURRENT).
  - [x] **EXECUTE**: `ContextoDoTurno.colecoes` lista as coleções ativas do tenant e projeto da identidade (ou só a do filtro, 404 para outro escopo), ignora as sem documentos e as de conexão desativada, busca em paralelo (`query_base`, até 5 threads), ordena por pontuação e limita a `LIMITE_DE_TRECHOS` (12) e `LIMITE_DE_COLECOES` (10), devolvendo evidências com fonte estruturada.
  - [x] **VERIFY**: `tests/test_app_assistente_contexto.py` e `tests/test_application_boundaries.py` dentro do comando de 90 testes: 90 passed.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN de AC-001, AC-002 (filtro e fonte estruturada) e AC-013 (isolamento com controle positivo). Arquivo: `src/app/assistente_contexto.py`.
  - [x] **IMPROVE**: Falha de uma busca vetorial sobe como erro genérico do turno (sem resposta gravada), como na SPEC-0021, em vez de responder com cobertura parcial sem avisar.
  <!-- specsfy:evidence {"task": "T024", "refs": ["US-001", "US-004", "US-005", "FR-001", "FR-002", "FR-003", "FR-007", "FR-008", "FR-010", "NFR-001", "NFR-002", "NFR-003", "AC-001", "AC-002", "AC-013"], "files": ["src/app/assistente_contexto.py", "src/app/repo.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_app_assistente_contexto.py tests/test_app_assistente.py tests/test_app_conteudo_documento.py tests/test_app_colecoes_documentos.py tests/test_assistente_grafo.py tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_falhas.py tests/test_app_tasks.py tests/test_app_envios_sync.py tests/test_app_conexoes.py tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}]} -->

- [x] T025 [CODE] [US-002] Acrescentar ao contexto o estado operacional e as configurações por allowlist, com o limite por papel e sem credenciais, em src/app/assistente_contexto.py — Refs: US-002, US-005, FR-003, FR-006, FR-010, FR-011, NFR-001, NFR-004, AC-004, AC-006, AC-014, AC-015 — Depends: T005, T007, T018, T019, T024
  - [x] **PREP**: RED confirmado nas tarefas de teste predecessoras; `check_database_safety.mjs` SAFE para os comandos Pytest (schema exclusivo por teste); documentação reconstruída por `$specsfy-documentator` ao fim do lote (monitor CURRENT).
  - [x] **EXECUTE**: `_estado_operacional` devolve, por campos permitidos, coleções, documentos, envios (situação, etapa, contagens e erro seguro, com o passo "Repetir" e o link nos que falharam) e, só para owner e admin, o modelo de embeddings e a divisão; para member entra o aviso "Dado restrito a admin"; chaves, senhas e URLs nunca entram (a classe só lê `Conexao.configuracao["modelo"]`).
  - [x] **VERIFY**: `tests/test_app_assistente_contexto.py` e `tests/test_app_conexoes.py` dentro do comando de 90 testes: 90 passed.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN de AC-004, AC-005 (rota), AC-006, AC-014 (admin vê, member recebe "restrito a admin") e AC-015 (chaves ausentes do contexto, da resposta e do `caplog`).
  - [x] **IMPROVE**: O papel que vê a configuração é `owner` e `admin` (ambos têm papel de escrita), registrado em `.specsfy/RULES.md`; o aviso de restrição só aparece no contexto de `estado`, não em toda pergunta.
  <!-- specsfy:evidence {"task": "T025", "refs": ["US-002", "US-005", "FR-003", "FR-006", "FR-010", "FR-011", "NFR-001", "NFR-004", "AC-004", "AC-006", "AC-014", "AC-015"], "files": ["src/app/assistente_contexto.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_app_assistente_contexto.py tests/test_app_assistente.py tests/test_app_conteudo_documento.py tests/test_app_colecoes_documentos.py tests/test_assistente_grafo.py tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_falhas.py tests/test_app_tasks.py tests/test_app_envios_sync.py tests/test_app_conexoes.py tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}]} -->

- [x] T026 [CODE] [US-003] Acrescentar ao contexto a consulta ao conteúdo processado por documento e por etiqueta, com limite de trechos e aviso de texto truncado, em src/app/assistente_contexto.py e src/app/repo.py — Refs: US-003, FR-002, FR-004, FR-005, FR-009, FR-010, NFR-002, AC-008, AC-010 — Depends: T010, T012, T021, T024
  - [x] **PREP**: RED confirmado nas tarefas de teste predecessoras; `check_database_safety.mjs` SAFE para os comandos Pytest (schema exclusivo por teste); documentação reconstruída por `$specsfy-documentator` ao fim do lote (monitor CURRENT).
  - [x] **EXECUTE**: `_conteudo_processado` resolve os documentos citados pelo nome na pergunta (ou todos do escopo), lê `ConteudoDocumento`, filtra os trechos por etiquetas `rotulo=valor` da pergunta, limita a 12 trechos, avisa quando o texto está truncado e informa a limitação quando o documento não tem conteúdo guardado.
  - [x] **VERIFY**: `tests/test_app_assistente_contexto.py` e `tests/test_app_colecoes_documentos.py` dentro do comando de 90 testes: 90 passed.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN de AC-008 (trechos `categoria=produto` sem consultar a base vetorial) e da parte de AC-010 que exige "não encontrei" sem o texto apagado.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: a busca por etiqueta é feita em Python sobre o JSON de trechos, como decidido no plano, e o limite por turno já cobre documentos grandes.
  <!-- specsfy:evidence {"task": "T026", "refs": ["US-003", "FR-002", "FR-004", "FR-005", "FR-009", "FR-010", "NFR-002", "AC-008", "AC-010"], "files": ["src/app/assistente_contexto.py", "src/app/repo.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_app_assistente_contexto.py tests/test_app_assistente.py tests/test_app_conteudo_documento.py tests/test_app_colecoes_documentos.py tests/test_assistente_grafo.py tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_falhas.py tests/test_app_tasks.py tests/test_app_envios_sync.py tests/test_app_conexoes.py tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}]} -->

- [x] T027 [CODE] [US-001] Implementar no grafo os nós `classificar`, `recuperar_colecoes`, `recuperar_estado` e `recuperar_processado`, o prompt sem restrição a RAG, a recusa fora do produto e o "não encontrei" em src/pipeline/assistant.py e src/pipeline/service.py — Refs: US-001, US-002, US-004, FR-002, FR-003, FR-006, FR-007, FR-008, FR-009, NFR-001, NFR-002, NFR-003, AC-003, AC-005, AC-011, AC-016 — Depends: T004, T006, T013, T020
  - [x] **PREP**: RED confirmado nas tarefas de teste predecessoras; `check_database_safety.mjs` SAFE para os comandos Pytest (schema exclusivo por teste); documentação reconstruída por `$specsfy-documentator` ao fim do lote (monitor CURRENT).
  - [x] **EXECUTE**: O grafo ganhou `classificar` (uma chamada ao modelo com a marca `[CLASSIFICAR]`, resposta ilegível consulta tudo), `recuperar_colecoes`, `recuperar_estado` e `recuperar_processado` (no-op quando não escolhidos ou sem recuperador), prompt do copilot (sem restrição a RAG, recusa fora do produto, nunca informa credenciais, só orienta), blocos "não encontrei" e "recusa" e fontes estruturadas na resposta; `service.assistant_reply` aceita `colecoes`, `estado` e `processado`; sem eles o grafo se comporta como na SPEC-0021 e o modelo segue sem ferramentas.
  - [x] **VERIFY**: `.venv/bin/python -m pytest tests/test_assistente_grafo.py tests/test_pipeline_service.py tests/test_application_boundaries.py -q`: 23 passed.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN de AC-011 (grafo, "não encontrei" e não afirmar) e AC-016 (nenhum recuperador chamado e uma classificação), mais as suítes antigas do grafo sem alteração.
  - [x] **IMPROVE**: A fronteira `src.pipeline` continua sem importar `src.app`: os recuperadores chegam por parâmetro e `test_application_boundaries.py` segue verde.
  <!-- specsfy:evidence {"task": "T027", "refs": ["US-001", "US-002", "US-004", "FR-002", "FR-003", "FR-006", "FR-007", "FR-008", "FR-009", "NFR-001", "NFR-002", "NFR-003", "AC-003", "AC-005", "AC-011", "AC-016"], "files": ["src/pipeline/assistant.py", "src/pipeline/service.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_assistente_grafo.py tests/test_pipeline_service.py tests/test_application_boundaries.py -q", "exit": 0}]} -->

- [x] T028 [CODE] [US-004] Ligar a rota de mensagens ao contexto: `colecao_id` opcional, 404 para coleção de outro Workspace e `fontes` estruturadas compatíveis com mensagens antigas em src/app/routers/assistente.py — Refs: US-001, US-004, FR-001, FR-002, FR-006, FR-007, FR-008, NFR-002, NFR-003, AC-001, AC-002, AC-012 — Depends: T016, T024, T025, T026, T027
  - [x] **PREP**: RED confirmado nas tarefas de teste predecessoras; `check_database_safety.mjs` SAFE para os comandos Pytest (schema exclusivo por teste); documentação reconstruída por `$specsfy-documentator` ao fim do lote (monitor CURRENT).
  - [x] **EXECUTE**: A rota de mensagens valida `colecao_id` (404 para outro escopo, 409 sem documentos), cria o contexto da identidade e passa `colecoes`, `estado` e `processado` ao `assistant_reply`; grava `fontes` estruturadas (objetos) junto das antigas em texto, sem mudar o esquema da coluna JSON; falha do modelo ou da busca continua virando a mensagem genérica sem gravar resposta.
  - [x] **VERIFY**: `tests/test_app_assistente.py`, `tests/test_app_assistente_contexto.py` e `tests/test_app_colecoes_permissoes.py` dentro do comando de 90 testes: 90 passed.
  - [x] **VISUAL**: Não aplicável: a mudança é de backend e não altera tela; a superfície visual é conferida nas tarefas da Fase de interface.
  - [x] **EVIDENCE**: GREEN do contrato de fontes (AC-012, objetos e mensagens antigas) e, junto com T024, de AC-001 e AC-002 pela API.
  - [x] **IMPROVE**: A coleção apontada deixou de montar a configuração no roteador (`_colecao_apontada` só valida e lista documentos): a configuração agora nasce no contexto, uma vez por coleção.
  <!-- specsfy:evidence {"task": "T028", "refs": ["US-001", "US-004", "FR-001", "FR-002", "FR-006", "FR-007", "FR-008", "NFR-002", "NFR-003", "AC-001", "AC-002", "AC-012"], "files": ["src/app/routers/assistente.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_app_assistente_contexto.py tests/test_app_assistente.py tests/test_app_conteudo_documento.py tests/test_app_colecoes_documentos.py tests/test_assistente_grafo.py tests/test_pipeline_service.py tests/test_application_boundaries.py tests/test_app_colecoes_permissoes.py tests/test_app_colecoes.py tests/test_app_colecoes_falhas.py tests/test_app_tasks.py tests/test_app_envios_sync.py tests/test_app_conexoes.py tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}]} -->

#### Fase de interface

- [x] T029 [CODE] [US-001] Tornar o seletor um filtro opcional "Filtrar por coleção (opcional)" com "Todas as coleções" e limpar no painel do assistente, em frontend/src/features/assistente/SeletorColecao.tsx, frontend/src/features/assistente/useAssistente.ts e frontend/src/features/assistente/AssistentePainel.tsx — Refs: US-001, FR-001, FR-007, NFR-003, AC-002 — Depends: T002, T028
  - [x] **PREP**: RED confirmado nas tarefas de teste predecessoras; `check_database_safety.mjs` SAFE para os comandos Pytest (schema exclusivo por teste); documentação reconstruída por `$specsfy-documentator` ao fim do lote (monitor CURRENT). `$specsfy-specialist-react-ui-components` lido em `.agents/skills` (o carregador de skills não o registra) e `DESIGNSYSTEM.MD`, `INTERFACE.md` e os blocos do painel do assistente conferidos.
  - [x] **EXECUTE**: `SeletorColecao` com rótulo "Filtrar por coleção (opcional)", padrão "Todas as coleções" e botão "Limpar filtro" visível só com filtro; `useAssistente` ganhou o tipo `FonteDaResposta` e `MensagemAssistente.fontes` aceita objetos e textos; `AssistentePainel` não mudou (já enviava `colecao_id` ou `null`); testes antigos da SPEC-0030 adaptados ao novo rótulo.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd` 239 passed (59 arquivos), `npm run lint` limpo, `npx tsc --noEmit` limpo e `npm run build` concluído; teclado coberto pelo teste do seletor (abrir, escolher e limpar só por teclado).
  - [x] **VISUAL**: Inspeção do código renderizado e dos testes contra `DESIGNSYSTEM.MD`, conferindo bordas, espaçamentos, margens, padding e tipografia: o seletor reaproveita `Label`, `Select` e `Button ghost sm`, sem borda, margem ou padding novos (`gap-1` e `gap-2` como os vizinhos); a linha do rótulo com o botão usa `flex items-center justify-between gap-2` e o rótulo longo quebra em vez de estourar; tipografia herdada (`text-xs` para a dica, rótulo padrão). Conferência no navegador em 375 px e 1280 px, nos dois temas, com nome longo de coleção, fica registrada na T035.
  - [x] **EVIDENCE**: GREEN de AC-002 no frontend (padrão, escolha por teclado e limpar). Arquivos: `SeletorColecao.tsx`, `useAssistente.ts`, `SeletorColecao.test.tsx`.
  - [x] **IMPROVE**: A dica sob o seletor passou a dizer o que o filtro faz ("Sem filtro, o copilot busca em todas as coleções do seu projeto"), e o estado vazio da lista de mensagens deixou de limitar o assunto a RAG.
  <!-- specsfy:evidence {"task": "T029", "refs": ["US-001", "FR-001", "FR-007", "NFR-003", "AC-002"], "files": ["frontend/src/features/assistente/SeletorColecao.tsx", "frontend/src/features/assistente/useAssistente.ts", "frontend/src/features/assistente/AssistentePainel.tsx"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/assistente", "exit": 0}]} -->

- [x] T030 [CODE] [US-004] Criar `FontesDaResposta` com fontes como links por teclado, ligar em `MensagemChat` e anunciar respostas e "não encontrei" pela região ao vivo em frontend/src/features/assistente/FontesDaResposta.tsx, frontend/src/features/assistente/MensagemChat.tsx e frontend/src/features/assistente/ListaMensagens.tsx — Refs: US-004, FR-002, FR-006, FR-008, FR-009, NFR-002, NFR-003, AC-011, AC-012 — Depends: T014, T015, T028
  - [x] **PREP**: RED confirmado nas tarefas de teste predecessoras; `check_database_safety.mjs` SAFE para os comandos Pytest (schema exclusivo por teste); documentação reconstruída por `$specsfy-documentator` ao fim do lote (monitor CURRENT). `$specsfy-specialist-react-ui-components` lido em `.agents/skills` (o carregador de skills não o registra) e `DESIGNSYSTEM.MD`, `INTERFACE.md` e os blocos do painel do assistente conferidos.
  - [x] **EXECUTE**: `FontesDaResposta` (`Badge` com `Link` pelo `render`) renderiza fonte estruturada como link com rótulo acessível "Abrir documento X da coleção Y" (coleção e envio têm rótulo próprio) e texto simples como `Badge`; `MensagemChat` usa o bloco novo; a região `role="log"` com `aria-live="polite"` de `ListaMensagens` já anuncia as respostas e agora também as com fontes.
  - [x] **VERIFY**: `npm --prefix frontend run test:tdd` 239 passed, ESLint e `tsc` limpos e `npm run build` concluído; Tab percorre os links e o axe-core não aponta violações.
  - [x] **VISUAL**: Inspeção do código renderizado e dos testes contra `DESIGNSYSTEM.MD`, conferindo bordas, espaçamentos, margens, padding e tipografia: as fontes reaproveitam as classes do `Badge` anterior (`h-auto min-h-5 max-w-full py-0.5 [overflow-wrap:anywhere] whitespace-normal`, `gap-1`, `max-w-[92%]`), com foco visível herdado do `Badge`; rótulo longo quebra linha sem overflow e a lista continua `flex-wrap`, empilhando no mobile. Conferência no navegador em 375 px e 1280 px, nos dois temas, com muitas fontes, nome longo, erro e "não encontrei", fica registrada na T035.
  - [x] **EVIDENCE**: GREEN de AC-011 (região viva com fonte estruturada e sem violações do axe) e AC-012 (links por teclado com rótulo de destino). Arquivos: `FontesDaResposta.tsx`, `MensagemChat.tsx`, `useAssistente.ts` e os testes.
  - [x] **IMPROVE**: `rotuloAcessivel` ficou exportada para o rótulo ser o mesmo no teste e na tela; fontes em texto simples continuam sem link para não inventar um destino.
  <!-- specsfy:evidence {"task": "T030", "refs": ["US-004", "FR-002", "FR-006", "FR-008", "FR-009", "NFR-002", "NFR-003", "AC-011", "AC-012"], "files": ["frontend/src/features/assistente/FontesDaResposta.tsx", "frontend/src/features/assistente/MensagemChat.tsx", "frontend/src/features/assistente/useAssistente.ts"], "commands": [{"run": "npm --prefix frontend run test:tdd -- src/features/assistente", "exit": 0}]} -->

#### Fase final — Documentação e qualidade

- [x] T031 [DOC] Registrar `conteudos_documento` (campos, `truncado`, relação 1:1 com o documento, exclusão junto dele) e a revisão `0031_conteudo_documento` em .specsfy/DATABASE.md — Refs: US-003, FR-004, FR-005, FR-009, FR-010, NFR-001, AC-007, AC-009, AC-010 — Depends: T021, T022, T023
  - [x] **PREP**: Arquivo atual lido e conteúdo humano preservado; entregas das tarefas dependentes conferidas.
  - [x] **EXECUTE**: `.specsfy/DATABASE.md` ganhou a linha de `conteudos_documento` (campos, `truncado`, relação 1:1 com o documento, exclusão antes do documento) e a decisão da SPEC-0031 com a revisão `0031_conteudo_documento` e o limite `CONTEUDO_MAX_CARACTERES`.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check`: monitor `CURRENT` após a atualização.
  - [x] **VISUAL**: Não aplicável: a tarefa só atualiza documentação de contexto, sem alterar tela.
  - [x] **EVIDENCE**: `.specsfy/DATABASE.md` ganhou a linha de `conteudos_documento` (campos, `truncado`, relação 1:1 com o documento, exclusão antes do documento) e a decisão da SPEC-0031 com a revisão `0031_conteudo_documento` e o limite `CONTEUDO_MAX_CARACTERES`. Resultado do monitor: CURRENT; `docs/` reconstruído por `$specsfy-documentator` e `--check` aprovado.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: a atualização foi aditiva e preservou o conteúdo humano.

- [x] T032 [DOC] Registrar `FontesDaResposta` e as extensões de `SeletorColecao` e `MensagemChat` em INTERFACE.md — Refs: US-001, US-004, FR-001, FR-006, FR-007, FR-008, NFR-003, AC-002, AC-012 — Depends: T029, T030
  - [x] **PREP**: Arquivo atual lido e conteúdo humano preservado; entregas das tarefas dependentes conferidas.
  - [x] **EXECUTE**: `INTERFACE.md` ganhou `FontesDaResposta` e atualizou `MensagemChat`, `SeletorColecao`, `useAssistente` e a tela do assistente, com props, estados, consumidores e regra de reaproveitamento.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check`: monitor `CURRENT` após a atualização.
  - [x] **VISUAL**: Não aplicável: a tarefa só atualiza documentação de contexto, sem alterar tela.
  - [x] **EVIDENCE**: `INTERFACE.md` ganhou `FontesDaResposta` e atualizou `MensagemChat`, `SeletorColecao`, `useAssistente` e a tela do assistente, com props, estados, consumidores e regra de reaproveitamento. Resultado do monitor: CURRENT; `docs/` reconstruído por `$specsfy-documentator` e `--check` aprovado.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: a atualização foi aditiva e preservou o conteúdo humano.

- [x] T033 [DOC] Revisar PROJECT.md quanto à ampliação do assistente para copilot com acesso ao sistema e ao conteúdo processado — Refs: US-001, US-002, US-003, US-004, FR-001, FR-002, FR-003, FR-004, FR-006, FR-007, FR-008, FR-011, NFR-001, NFR-002, NFR-004, AC-001, AC-004, AC-008 — Depends: T028, T029, T030
  - [x] **PREP**: Arquivo atual lido e conteúdo humano preservado; entregas das tarefas dependentes conferidas.
  - [x] **EXECUTE**: `PROJECT.md` descreve o copilot (busca em todas as coleções do escopo, estado operacional, conteúdo processado, fontes clicáveis, sem ações) e ajusta o limite do assistente para "produto e conteúdo dos documentos".
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check`: monitor `CURRENT` após a atualização.
  - [x] **VISUAL**: Não aplicável: a tarefa só atualiza documentação de contexto, sem alterar tela.
  - [x] **EVIDENCE**: `PROJECT.md` descreve o copilot (busca em todas as coleções do escopo, estado operacional, conteúdo processado, fontes clicáveis, sem ações) e ajusta o limite do assistente para "produto e conteúdo dos documentos". Resultado do monitor: CURRENT; `docs/` reconstruído por `$specsfy-documentator` e `--check` aprovado.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: a atualização foi aditiva e preservou o conteúdo humano.

- [x] T034 [DOC] Registrar em .specsfy/RULES.md as regras confirmadas de credenciais fora do contexto do modelo (DEC-006) e de herança de Workspace e papel com restrição a admin só para conexão e divisão (DEC-003, DEC-011) — Refs: US-005, FR-003, FR-010, FR-011, NFR-001, NFR-004, AC-014, AC-015 — Depends: T025, T028
  - [x] **PREP**: Arquivo atual lido e conteúdo humano preservado; entregas das tarefas dependentes conferidas.
  - [x] **EXECUTE**: `.specsfy/RULES.md` ganhou, por `add_rule.mjs` na seção "Segurança e privacidade", a regra de credenciais fora do contexto do modelo (DEC-006) e a de consulta limitada a tenant, projeto e papel, com conexão e divisão restritas a owner e admin (DEC-003, DEC-011, DEC-013); a regra de assistente sem ferramentas de escrita não foi tocada.
  - [x] **VERIFY**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check`: monitor `CURRENT` após a atualização.
  - [x] **VISUAL**: Não aplicável: a tarefa só atualiza documentação de contexto, sem alterar tela.
  - [x] **EVIDENCE**: `.specsfy/RULES.md` ganhou, por `add_rule.mjs` na seção "Segurança e privacidade", a regra de credenciais fora do contexto do modelo (DEC-006) e a de consulta limitada a tenant, projeto e papel, com conexão e divisão restritas a owner e admin (DEC-003, DEC-011, DEC-013); a regra de assistente sem ferramentas de escrita não foi tocada. Resultado do monitor: CURRENT; `docs/` reconstruído por `$specsfy-documentator` e `--check` aprovado.
  - [x] **IMPROVE**: Nenhuma melhoria necessária: a atualização foi aditiva e preservou o conteúdo humano.

- [x] T035 [TEST] Executar regressão, lint, tipos, build, rastreabilidade e a conferência visual final em tests/test_app_assistente_contexto.py e frontend/src/features/assistente — Refs: US-001, US-002, US-003, US-004, US-005, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016 — Depends: T021, T022, T023, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T034
  - [x] **PREP**: T001–T034 concluídas, validadores de spec e tarefas READY e monitor CURRENT; `check_database_safety.mjs` SAFE para `.venv/bin/python -m pytest -q` (schema exclusivo por teste, sem comando destrutivo de schema).
  - [x] **EXECUTE**: Pytest completo (668 passed, 1 skipped anterior à spec), Ruff limpo, Vitest (59 arquivos, 239 passed), ESLint e `tsc` limpos, `npm run build` concluído, rastreabilidade `--full-chain` 36/36, `verify_evidence` strict e `$specsfy-documentator --check` aprovado.
  - [x] **VERIFY**: Rastreabilidade sem gaps, evidências `specsfy:evidence` válidas, nenhuma regressão e os 16 AC com teste GREEN; uma falha da suíte (`tests/test_spec_markers.py`) apontou uma palavra acentuada da própria spec como marcador não resolvido, foi corrigida e o teste passou.
  - [x] **VISUAL**: Conferência no navegador real (build de produção, API simulada e Chromium headless via CDP) em 375 e 1280 px, nos temas claro e escuro, com 4 fontes estruturadas (nome longo, envio, coleção e texto simples) e a resposta "não encontrei": bordas (`1px` do tema, raio `26px` do `Badge`), espaçamentos e margens (`gap-1`), padding (`2px 8px`) e tipografia (Geist, `12px`, peso 500, altura de linha `16px`, quebra normal) iguais às do `Badge` anterior; sem overflow da página nem do painel nos quatro cenários, rótulo longo quebrado em três linhas, seletor "Todas as coleções" com 32 px de altura e região `role="log"` viva. Dois textos do painel que ainda descreviam só RAG foram atualizados.
  - [x] **EVIDENCE**: Contagens e comandos acima; capturas e medidas em `research/t035-mobile-claro.png`, `research/t035-desktop-escuro.png` e `research/t035-visual-medidas.json` (indexadas na seção 2).
  - [x] **IMPROVE**: A conferência visual virou um roteiro reaproveitável (stub de API na porta do proxy compilado no build, Chromium headless e CDP); a retrospectiva anotou que `next start` compila o destino do proxy no build, e que uma suíte completa leva cerca de 20 minutos e deve rodar em segundo plano.
  <!-- specsfy:evidence {"task": "T035", "refs": ["US-001", "US-002", "US-003", "US-004", "US-005", "FR-001", "FR-002", "FR-003", "FR-004", "FR-005", "FR-006", "FR-007", "FR-008", "FR-009", "FR-010", "FR-011", "NFR-001", "NFR-002", "NFR-003", "NFR-004", "AC-001", "AC-002", "AC-003", "AC-004", "AC-005", "AC-006", "AC-007", "AC-008", "AC-009", "AC-010", "AC-011", "AC-012", "AC-013", "AC-014", "AC-015", "AC-016"], "files": ["tests/test_app_assistente_contexto.py", "frontend/src/features/assistente/FontesDaResposta.tsx"], "commands": [{"run": ".venv/bin/python -m pytest -q", "exit": 0}, {"run": ".venv/bin/ruff check .", "exit": 0}, {"run": "npm --prefix frontend run test:tdd", "exit": 0}, {"run": "npm --prefix frontend run lint", "exit": 0}, {"run": "npm --prefix frontend run build", "exit": 0}]} -->

### 15. Ordem de execução

- Caminho crítico: T001–T020 (RED) → T021 → T022 → T024 → T025 → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T034 → T035.
- Tarefas paralelas: Nenhuma marcada com `[P]`: os testes T001–T020 escrevem casos independentes, mas vários compartilham arquivos de teste e `assistente_contexto.py` é editado em T024, T025 e T026; T023 (exclusão) só depende de T012 e T021 e pode andar junto de T022, mas ambas alteram o fluxo do documento e seguem em ordem.
- Estratégia de MVP: US-001 e US-004 (T024, T027, T028, T029, T030) entregam o valor central e o defeito relatado; US-002 e US-005 (T025) acrescentam estado e limites de papel; US-003 (T021–T023, T026) entrega o conteúdo processado.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0030 (Coleções, concluída) e SPEC-0021 (assistente, concluída); correção `fix/assistente-colecao-selecionada` (5d23872). Persistência nova registrada em `.specsfy/DATABASE.md`.

#### Riscos

- Custo e latência de buscar em várias coleções por turno → limitar coleções e trechos por turno e classificar a pergunta antes de buscar (NFR-002).
- Injeção de instrução via conteúdo de documento → delimitar trechos como dado, sem ferramentas de escrita (PR-001) e sem escopo vindo do modelo (PR-002).
- Vazamento entre Workspaces ou de credenciais → filtro na fronteira `assistente_contexto` com allowlist e testes de contexto (NFR-001, NFR-004).
- Texto convertido grande aumenta o armazenamento → uma versão por documento e exclusão junto do documento; limite `CONTEUDO_MAX_CARACTERES` com truncamento marcado (DEC-012).
- Documentos antigos sem conteúdo guardado → informar a limitação (casos-limite).

#### Suposições

- O texto convertido é o conteúdo do arquivo Markdown do envio, lido do diretório materializado (reversível se a conversão passar a ocorrer em outra etapa).
- Alvo de latência do turno com busca em até 10 coleções: dentro do `timeout` do modelo já configurado (confirmado em 2026-10-15, Q12); se estourar, o copilot informa que não conseguiu buscar em todas.
- "Restrito a admin" abrange as configurações de conexão e a divisão (confirmado em 2026-10-15, DEC-011); a regra espelha o que a interface já restringe, e deve ser revista se a interface mudar.
- O copilot mantém o nome "assistente" na interface; "copilot" nomeia a capacidade nesta spec.

### 17. Decisões

- **DEC-001**: Escopo de acesso: conteúdo das coleções, estado operacional e conteúdo processado — escolhida pela pessoa (Pergunta 1).
- **DEC-002**: O worker persiste o texto convertido e os trechos com etiquetas, sem o arquivo original — Perguntas 2 e 9; alternativa descartada: reprocessar sob demanda (mais lento e caro).
- **DEC-003**: O copilot herda Workspace e papel da identidade — Pergunta 3; o modelo nunca fornece escopo.
- **DEC-004**: Seletor de coleção vira filtro opcional — Pergunta 4.
- **DEC-005**: Só consulta e sugestão de passo; sem ações de escrita — Pergunta 5; execução fica para item futuro.
- **DEC-006**: Credenciais nunca chegam ao modelo, à resposta nem aos logs — confirmada pela pessoa em 2026-10-15 (Pergunta 11, recomendação aceita): vale também para admin e sem valor mascarado; o copilot só diz se a conexão está configurada.
- **DEC-007**: Retenção enquanto o documento existir, uma versão — Pergunta 6.
- **DEC-008**: Fontes estruturadas e clicáveis; "não encontrei" sem base — Pergunta 7.
- **DEC-009**: O defeito da coleção selecionada foi corrigido antes da spec, em `fix/` — Pergunta 8 e commit 5d23872.
- **DEC-010**: O modelo continua sem ferramentas e a recuperação é feita por nós determinísticos do grafo — mantém a restrição da SPEC-0021 e reduz a superfície de ataque, ao custo de uma etapa de classificação.
- **DEC-011**: Restrito a admin = configurações de conexão e divisão; o resto do estado operacional segue Workspace e papel — Pergunta 10 (recomendação aceita pela pessoa); alternativas descartadas: ocultar falhas técnicas ou autoria dos membros.
- **DEC-012**: Texto convertido acima do limite é guardado truncado com o marcador `truncado`, trechos por inteiro, e o envio não falha — Pergunta 13 (recomendação aceita pela pessoa em 2026-10-15); alternativas descartadas: guardar só os trechos ou recusar guardar o conteúdo; resolve FIND-ARCH-001.
- **DEC-013**: A fronteira de isolamento do copilot é tenant e projeto da identidade, como o resto do sistema; "Workspace da pessoa" nesta spec significa esse escopo, que abrange todos os Workspaces do projeto, e o Workspace entra só como rótulo nas fontes e como contexto das coleções — Pergunta 14 (recomendação aceita pela pessoa em 2026-10-15); alternativas descartadas: Workspace estrito por tela e filtro opcional por Workspace. Motivo: a identidade não carrega Workspace e `get_colecao_or_404` e `GET /api/v1/colecoes` já isolam por tenant e projeto.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/DATABASE.md` reflete a persistência do conteúdo processado do documento (tabela, campos, relação com o documento e exclusão junto dele).
- [x] `PROJECT.md` foi revisado quanto à ampliação do assistente para copilot com acesso ao sistema e ao conteúdo processado, ou a justificativa de ausência de impacto está registrada na evidência.
- [x] `.specsfy/RULES.md` registra a regra confirmada de que credenciais nunca chegam ao modelo, à resposta nem aos logs (DEC-006) e a de que o copilot herda Workspace e papel (DEC-003, DEC-011), ou a justificativa de não promover regra nova está registrada.
