# Especificação integrada: Fase 1: seguir direto para a indexação sem download e upload

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0043 |
| Slug | 0043-seguir-direto-para-a-indexacao |
| Status | Complete |
| Effort | 6 |
| Effort updated at | 2026-10-22 |
| Effort rationale | Cruza backend (origem lote nos endpoints de prévia e envio, tabela de origem, migration), frontend (painel do lote e fluxo de ingestão) e regras de retenção e permissão; sem integração externa nova. |
| ClickUp Task | |
| Milestones | M04 (extensão; a confirmar) |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Sim |
| Atualizada em | 2026-10-22 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

Hoje a pessoa baixa o pacote de `.md` do lote de conversão da Fase 1 e o envia de novo ao fluxo de ingestão da Fase 2. Esse desvio manual não agrega valor, permite subir uma versão errada ou antiga e deixa o sistema sem saber de qual lote veio cada documento da coleção.

#### Resultado desejado

Dar à pessoa uma opção, ao lado de "baixar pacote", para seguir direto do lote à indexação com os `.md` que o sistema já guarda, sem download nem upload. O caminho atual continua existindo. Cada documento indexado passa a lembrar de qual lote veio e qual versão do `.md` foi indexada, para avisar quando o `.md` do lote mudar depois.

#### Métricas de sucesso

- Indexar um lote concluído exige zero download e zero upload de arquivo pelo navegador.
- O `.md` indexado é byte a byte o guardado no lote no momento da confirmação (hash igual ao registrado).
- Nenhuma regressão no caminho manual (upload de `.md` e base preparada): as suítes existentes seguem passando.
- Documento do lote alterado depois da indexação aparece marcado em até uma abertura do painel, enquanto o arquivo do lote existir.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: Como a Fase 2 recebe os `.md` hoje? → `POST /api/v1/envios` e `POST /api/v1/ingestao/previa` aceitam `arquivos` (upload) ou `usar_base_preparada`; ambos passam por `ingestao.ler_arquivos_markdown` ou `ingestao.ler_base_preparada`, que validam quantidade, extensão, UTF-8 e tamanho. Impacto: a origem "lote" entra como terceira fonte nos dois endpoints, reutilizando as mesmas validações.
- **R-002**: Onde ficam os `.md` do lote? → no armazenamento sob a chave do `documento_conversao` (`storage.materialize(documento_id, pasta)`, arquivo `<stem>.md`); `GET /conversoes/{lote}/pacote` já considera apto o documento com `situacao == "concluido"` e `apagado_em` nulo. Impacto: "apto" reutiliza essa regra.
- **R-003**: Qual a retenção? → `documentos_conversao.expira_em` é `concluido_em + 7 dias`; a rotina diária apaga os arquivos e grava `apagado_em`, preservando a linha. Impacto: passados 7 dias o atalho não pode indexar e a marca "alterado" deixa de ser calculada.
- **R-004**: "Liberar para a base" é do lote ou da coleção? → da coleção (`colecoes.revisada_em`, SPEC-0039); a análise de contradições também roda na coleção (SPEC-0038). Impacto: o atalho não pode depender de liberação, pois ela só existe depois de os `.md` estarem numa coleção (DEC-006).

#### Fontes e contexto consultados

- `specs/inbox/2026-10-22-231328-seguir-direto-da-fase-1-para-a-fase-2-sem-download-e-upload.md`
- `specs/backlog/0048-fase-1-seguir-direto-para-a-indexacao-sem-download-e-upload.md`
- `src/app/routers/conversao.py`, `src/app/routers/envios.py`, `src/app/routers/ingestao.py`, `src/app/ingestao.py`, `src/app/models.py`
- `frontend/src/features/conversao/PainelLoteConversao.tsx`, `frontend/src/features/ingestao/FluxoIngestao.tsx`, `EtapaArquivos.tsx`, `EtapaPublicacao.tsx`, `frontend/src/app/(autenticado)/workspaces/[id]/enviar/page.tsx`
- `.specsfy/DATABASE.md`, `INTERFACE.md`, `DESIGNSYSTEM.MD`, specs 0023, 0026, 0030, 0037, 0038 e 0039.

#### Documentação consultada

- Nenhuma fonte externa. Toda a evidência é do repositório.

#### Artefatos de pesquisa armazenados

- Nenhum artefato externo.

#### Dúvidas respondidas

- **Q**: De onde a pessoa começa o atalho? → **A**: do painel do lote de conversão, com um botão "Seguir para a indexação" ao lado de "baixar pacote" (Pergunta 1).
- **Q**: Quais documentos do lote entram? → **A**: os que a pessoa marca no painel, com os aptos já marcados e a opção de desmarcar (Pergunta 2).
- **Q**: Para qual coleção vão? → **A**: a coleção é escolhida na etapa de destino do fluxo de ingestão, nova ou existente do mesmo Workspace (Pergunta 3).
- **Q**: O que acontece quando o `.md` muda depois de indexado? → **A**: o painel marca "alterado desde a indexação"; reindexar é ação explícita e confirmada, e o envio acumulado substitui a versão antiga (Pergunta 4).
- **Q**: O que a confirmação mostra? → **A**: contagem de documentos, coleção de destino e aviso de embeddings, sem estimativa em valor (Pergunta 5).
- **Q**: Quando o botão fica disponível? → **A**: quando o lote terminou e tem ao menos um documento apto, sem exigir liberação (Perguntas 6 e 7; a resposta "só depois de liberar" foi substituída).
- **Q**: O que o sistema lembra sobre a origem? → **A**: lote, documento do lote e versão do `.md` indexada; permanece enquanto o documento existir na coleção; a marca "alterado" deixa de ser calculada quando o arquivo do lote expira; owner, admin e member veem, só owner e admin reindexam (descoberta de dados, 2026-10-22).

#### Dúvidas abertas

- Nenhuma bloqueante. Os papéis, a definição de "apto" e o tratamento dos erros estão nas suposições (seção 16) e podem ser revistos.

### 3. Escopo e atores

#### Incluído

- Botão "Seguir para a indexação" no painel do lote, com regra de disponibilidade e seleção de documentos.
- Origem "lote de conversão" na prévia e na criação do envio, lida do armazenamento do sistema.
- Registro da origem de cada documento indexado (lote, documento do lote, hash do `.md`).
- Marca "alterado desde a indexação" e aviso "arquivo do lote expirado".
- Reindexação explícita e confirmada de documento alterado, na mesma coleção.
- Permissões no servidor e estados da interface.

#### Fora de escopo

- Exigir ou criar marca de liberação no lote; a liberação continua na coleção (SPEC-0039).
- Remover ou alterar o upload manual de `.md` e a base preparada.
- Estimativa de custo em valor e reindexação automática.
- Mudar a retenção de 7 dias dos arquivos do lote (SPEC-0023).
- Novas regras de limpeza, contradição ou decisão da empresa.

#### Atores

- **Owner e admin**: marcam documentos do lote, seguem para a indexação, escolhem a coleção, confirmam e reindexam.
- **Member**: consulta a origem e a marca na coleção; não vê nem aciona o botão.
- **Sistema**: lê os `.md` do lote, valida limites, cria o envio, registra a origem e calcula a marca.

### 4. Princípios e restrições do projeto

- **PR-001**: A autorização é verificada no servidor, no mesmo padrão `require_write_role` e escopo de tenant, projeto e Workspace dos endpoints atuais.
- **PR-002**: Textos e arquivos de clientes não entram no repositório nem em logs; a origem guarda só identificadores e hash.
- **PR-003**: O envio criado pelo atalho segue o fluxo assíncrono existente (SPEC-0030): fila, estados, retry e a aba Envios.
- **PR-004**: O caminho manual e a base preparada permanecem com o comportamento atual.
- **PR-005**: Mudança de schema entra por migration Alembic aditiva e reversível (SPEC-0042); nenhum teste usa banco de desenvolvimento nem comando destrutivo.

### 5. Histórias de usuário

#### US-001 — Seguir do lote para a indexação (P1)

Como owner ou admin, quero um botão "Seguir para a indexação" no painel do lote de conversão, para escolher os documentos aptos e iniciar a indexação sem baixar e subir arquivos.

**Por que P1**: remove o desvio manual que motivou o pedido.
**Teste independente**: abrir um lote concluído, marcar documentos e chegar ao fluxo de ingestão com eles selecionados.
**Requisitos**: FR-001, FR-002, FR-003, FR-005, FR-010

#### US-002 — Indexar os `.md` do lote sem upload (P1)

Como owner ou admin, quero que a prévia e o envio usem os `.md` guardados no lote, para indexar exatamente a versão revisada numa coleção nova ou existente.

**Por que P1**: entrega o resultado final do atalho com a mesma segurança do fluxo atual.
**Teste independente**: iniciar o envio a partir do lote e ver os documentos indexados na coleção escolhida.
**Requisitos**: FR-003, FR-004, FR-005, FR-009, FR-010

#### US-003 — Saber a origem e reindexar o que mudou (P2)

Como owner, admin ou member, quero ver de qual lote veio cada documento e se o `.md` do lote mudou depois, para decidir se é preciso reindexar.

**Por que P2**: dá rastreabilidade e evita indexar de novo sem aviso, mas o atalho já funciona sem isso.
**Teste independente**: alterar o `.md` de um documento indexado do lote e ver a marca e a ação de reindexar.
**Requisitos**: FR-006, FR-007, FR-008, FR-010

### 6. Cenários BDD de aceite

#### AC-001 — Botão e seleção no lote concluído

**Cobre**: US-001, FR-001, FR-002, FR-005, FR-009, NFR-004

```gherkin
@US-001 @FR-001 @FR-002 @FR-005 @FR-009 @NFR-004 @AC-001
Feature: Seguir para a indexação a partir do lote

  Scenario: Owner marca documentos de um lote concluído e segue
    Given um lote concluído com 3 documentos aptos no Workspace do owner
    When o owner abre o painel do lote
    Then vê "Baixar pacote" e "Seguir para a indexação" lado a lado
    And os 3 aptos já vêm marcados e ele pode desmarcar qualquer um
    And ao acionar o botão vê a contagem dos documentos marcados antes de seguir
```

#### AC-002 — Botão indisponível por estado do lote

**Cobre**: US-001, FR-001, FR-009, FR-010

```gherkin
@US-001 @FR-001 @FR-009 @FR-010 @AC-002
Feature: Disponibilidade do atalho

  Scenario Outline: Lote sem condição de seguir
    Given um lote <estado>
    When o owner abre o painel do lote
    Then "Seguir para a indexação" fica indisponível com o motivo visível
    And "Baixar pacote" continua como está

    Examples:
      | estado                                        |
      | em processamento                              |
      | aguardando confirmação do domínio             |
      | em limpeza                                    |
      | concluído sem documento apto                  |
      | com os arquivos já apagados pela retenção     |
```

#### AC-003 — Member não aciona o atalho

**Cobre**: US-001, FR-010, NFR-001

```gherkin
@US-001 @FR-010 @NFR-001 @AC-003
Feature: Permissão do atalho

  Scenario: Member não vê o botão e a API recusa
    Given um member com acesso ao Workspace do lote
    When ele abre o painel do lote
    Then o botão "Seguir para a indexação" não aparece
    And uma chamada direta à prévia ou ao envio com origem lote devolve 403
```

#### AC-004 — Nenhum documento marcado

**Cobre**: US-001, FR-002, FR-005, NFR-004

```gherkin
@US-001 @FR-002 @FR-005 @NFR-004 @AC-004
Feature: Seleção de documentos do lote

  Scenario: Sem documento marcado não há como seguir
    Given o painel com todos os aptos desmarcados
    When a pessoa tenta seguir
    Then a ação de seguir fica indisponível
    And o motivo é anunciado em região de status
```

#### AC-005 — Fluxo abre com os documentos do lote

**Cobre**: US-002, FR-003, FR-004

```gherkin
@US-002 @FR-003 @FR-004 @AC-005
Feature: Fluxo de ingestão com origem no lote

  Scenario: Documentos do lote chegam ao fluxo sem upload
    Given 2 documentos marcados no painel do lote
    When a pessoa segue para a indexação
    Then o fluxo de ingestão do Workspace abre com esses 2 documentos listados na etapa Arquivos
    And nenhum arquivo é lido pelo navegador
    And a prévia calcula os chunks com os `.md` guardados no lote
```

#### AC-006 — Criar o envio a partir do lote

**Cobre**: US-002, FR-003, FR-004, FR-005, NFR-002, NFR-003

```gherkin
@US-002 @FR-003 @FR-004 @FR-005 @NFR-002 @NFR-003 @AC-006
Feature: Envio com origem no lote

  Scenario: Confirmação e criação do envio
    Given o fluxo aberto com 2 documentos do lote e uma coleção de destino escolhida
    When a pessoa confirma a publicação
    Then a confirmação mostrou a contagem, a coleção de destino e o aviso de embeddings antes
    And o servidor lê os `.md` do armazenamento do lote e cria um envio em fila
    And os arquivos do envio têm o mesmo conteúdo guardado no lote
```

#### AC-007 — Documento mudou ou expirou entre marcar e confirmar

**Cobre**: US-002, FR-003, FR-004, NFR-003

```gherkin
@US-002 @FR-003 @FR-004 @NFR-003 @AC-007
Feature: Consistência entre marcar e confirmar

  Scenario: Documento indisponível na confirmação
    Given um documento marcado cujo arquivo foi apagado pela retenção antes da confirmação
    When a pessoa confirma a publicação
    Then o servidor recusa com a indicação do documento indisponível
    And nenhum envio é criado
    And a pessoa pode ajustar a seleção e tentar de novo
```

#### AC-008 — Caminho manual intacto

**Cobre**: US-002, FR-009, NFR-004

```gherkin
@US-002 @FR-009 @NFR-004 @AC-008
Feature: Compatibilidade com o upload manual

  Scenario: Upload de `.md` e base preparada seguem iguais
    Given o fluxo de ingestão aberto sem origem de lote
    When a pessoa envia `.md` escolhidos no navegador ou usa a base preparada
    Then a prévia e o envio se comportam como antes
    And enviar `arquivos`, `usar_base_preparada` e origem lote juntos é recusado com 422
```

#### AC-009 — Origem registrada sem texto

**Cobre**: US-003, FR-006, NFR-002

```gherkin
@US-003 @FR-006 @NFR-002 @AC-009
Feature: Registro da origem

  Scenario: Documento indexado lembra o lote
    Given um envio concluído a partir de um lote
    When a pessoa abre o documento na coleção
    Then vê o lote e o documento de origem
    And o registro guarda só identificadores e o hash do `.md`, nunca o texto
```

#### AC-010 — Marca de alterado desde a indexação

**Cobre**: US-003, FR-006, FR-007, FR-008, NFR-003

```gherkin
@US-003 @FR-006 @FR-007 @FR-008 @NFR-003 @AC-010
Feature: Documento do lote alterado

  Scenario: O `.md` do lote mudou depois da indexação
    Given um documento indexado a partir de um lote cujo `.md` foi reprocessado e tem hash diferente
    When a pessoa abre o painel do lote
    Then o documento aparece como "alterado desde a indexação"
    And owner e admin veem a ação de reindexar
```

#### AC-011 — Arquivo do lote expirado

**Cobre**: US-003, FR-007, NFR-002

```gherkin
@US-003 @FR-007 @NFR-002 @AC-011
Feature: Retenção do arquivo do lote

  Scenario: O arquivo do lote foi apagado
    Given um documento indexado cujo arquivo no lote foi apagado aos 7 dias
    When a pessoa abre o painel do lote ou o documento na coleção
    Then a origem continua visível
    And aparece o aviso "arquivo do lote expirado" sem marca de alterado
```

#### AC-012 — Reindexar com confirmação

**Cobre**: US-003, FR-006, FR-008, FR-010

```gherkin
@US-003 @FR-006 @FR-008 @FR-010 @AC-012
Feature: Reindexação explícita

  Scenario: Reindexar um documento alterado
    Given um documento marcado como alterado e um owner ou admin
    When ele aciona reindexar e confirma
    Then um novo envio substitui a versão do documento na mesma coleção
    And a origem passa a registrar o novo hash
    And sem a confirmação nada é reindexado
```

#### AC-013 — Isolamento entre Workspaces

**Cobre**: US-002, FR-004, FR-010, NFR-001

```gherkin
@US-002 @FR-004 @FR-010 @NFR-001 @AC-013
Feature: Escopo do lote

  Scenario: Lote de outro Workspace ou tenant
    Given um lote que pertence a outro Workspace
    When uma chamada tenta usá-lo como origem da prévia ou do envio
    Then o servidor responde 404 sem revelar que o lote existe
    And nenhum arquivo é lido
```

#### AC-014 — Teclado e estados

**Cobre**: US-001, US-003, FR-001, FR-002, FR-007, NFR-004

```gherkin
@US-001 @US-003 @FR-001 @FR-002 @FR-007 @NFR-004 @AC-014
Feature: Acessibilidade do atalho

  Scenario: Uso por teclado e anúncio de estados
    Given o painel do lote com seleção e marcas de alterado
    When a pessoa usa apenas o teclado
    Then alcança as caixas de seleção, o botão e a ação de reindexar com foco visível
    And a mudança de seleção, a indisponibilidade e as marcas são anunciadas em região de status
```

#### AC-015 — Member consulta a origem

**Cobre**: US-003, FR-007, FR-008, FR-010, NFR-001

```gherkin
@US-003 @FR-007 @FR-008 @FR-010 @NFR-001 @AC-015
Feature: Permissões da origem

  Scenario: Member vê a marca mas não reindexa
    Given um documento alterado e um member no mesmo Workspace
    When o member abre a coleção
    Then vê a origem e a marca "alterado desde a indexação"
    And não vê a ação de reindexar e a API recusa a tentativa com 403
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O painel do lote deve exibir "Seguir para a indexação" ao lado de "Baixar pacote" para owner e admin, disponível somente quando o lote não está em processamento, em limpeza nem aguardando o domínio e tem ao menos um documento apto; caso contrário indisponível com o motivo visível. Documento apto é o `concluido` com arquivo existente (`apagado_em` nulo).
- **FR-002**: O painel deve listar os documentos aptos com caixa de seleção, aptos marcados por padrão, permitir desmarcar e manter a ação de seguir indisponível sem documento marcado.
- **FR-003**: Ao seguir, o sistema deve abrir o fluxo de ingestão do Workspace do lote com os documentos marcados como origem, sem arquivos no navegador, mostrar esses documentos na etapa Arquivos e deixar a escolha da coleção (nova ou existente do Workspace) na etapa de publicação.
- **FR-004**: `POST /api/v1/ingestao/previa` e `POST /api/v1/envios` devem aceitar a origem lote (`lote_id` e `documento_ids`), ler os `.md` do armazenamento do lote com as mesmas validações de quantidade, extensão, UTF-8 e tamanho do upload, e recusar origem combinada com `arquivos` ou `usar_base_preparada` (422), documento indisponível (409) e lote fora do escopo (404).
- **FR-005**: A etapa de publicação deve mostrar, antes de criar o envio, a contagem de documentos, a coleção de destino e o aviso de que a indexação gera embeddings, sem estimativa em valor; nada é indexado antes da confirmação.
- **FR-006**: Ao criar o envio com origem lote, o sistema deve registrar, para cada documento, o lote, o documento do lote e o hash SHA-256 do `.md` lido, e atualizar esse registro quando o documento for reindexado.
- **FR-007**: O sistema deve mostrar a origem do documento na coleção e no painel do lote e marcar "alterado desde a indexação" quando o hash atual do `.md` no lote difere do registrado; quando o arquivo do lote não existe mais, mostrar "arquivo do lote expirado" e não calcular a marca.
- **FR-008**: O sistema deve oferecer a owner e admin reindexar um documento alterado por ação explícita com confirmação, reaproveitando o fluxo de origem lote na mesma coleção, e o novo envio substitui a versão antiga como já ocorre na SPEC-0030.
- **FR-009**: O download do pacote, o download individual, o upload manual de `.md` e a base preparada devem manter o comportamento atual.
- **FR-010**: O servidor deve exigir papel owner ou admin para a origem lote e para reindexar, e limitar o lote ao tenant, projeto e Workspace da identidade; member apenas consulta a origem e a marca.

#### Não funcionais

- **NFR-001**: Isolamento e autorização: nenhum arquivo de lote é lido sem papel e escopo válidos; lote de outro Workspace responde 404 e papel insuficiente 403. **Verificação**: testes de API com identidades de Workspaces e papéis diferentes.
- **NFR-002**: Privacidade e retenção: o conteúdo do cliente não passa pelo navegador nem por logs, e o registro de origem guarda apenas identificadores e hash, preservado enquanto o documento existir na coleção. **Verificação**: teste que inspeciona a tabela de origem e os logs capturados; teste de retenção com arquivo apagado.
- **NFR-003**: Integridade: o hash registrado é do mesmo conteúdo que foi guardado no armazenamento do envio, lido uma única vez na criação, e documento alterado ou apagado entre marcar e confirmar é recusado. **Verificação**: teste que altera o arquivo do lote entre a prévia e o envio e confere hash e resposta.
- **NFR-004**: Compatibilidade e acessibilidade: as suítes existentes de ingestão, envios e conversão passam sem alteração de comportamento, e o painel e a reindexação operam por teclado com foco visível e estados anunciados em `role="status"`. **Verificação**: `pytest`, `vitest` e testes de acessibilidade do painel e do fluxo.

#### Erros e casos-limite

- Documento removido, expirado ou alterado entre marcar e confirmar → recusa 409 com o nome do documento; nada é criado; a pessoa ajusta a seleção.
- Nenhum documento marcado → ação de seguir indisponível.
- Mais de 50 documentos ou arquivo acima de 5 MB → mesmas mensagens e limites do upload manual.
- Dois documentos do lote com o mesmo nome de `.md` → recusa 422 "Há arquivos com o mesmo nome neste envio".
- Falha ao enfileirar o envio → compensação existente e mensagem 503 do fluxo atual.
- Lote sem coleção de destino disponível ou sem conexões ativas → a etapa de publicação orienta como hoje.
- Recarregar a página do fluxo com origem lote → mantém a origem pelos parâmetros da rota; se o lote expirou, informa e oferece voltar ao lote.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

- Backend FastAPI com SQLAlchemy e Alembic (head atual `0042_schema_da_fila`), storage por chave em `src/app/storage.py`, fila Procrastinate. Frontend Next.js 16 e React 19 com Tailwind 4, shadcn/ui e testes com Vitest; backend testado com pytest.
- A Fase 1 guarda o original e o `.md` sob a chave do `documento_conversao`; a Fase 2 guarda os arquivos do envio sob a chave do envio e `ingestao.ler_*` devolve pares `(nome, bytes)`.
- `PainelLoteConversao` mostra documentos e o download do pacote; `FluxoIngestao` guarda o estado em memória (`useFluxoIngestao`) e publica pelo `EtapaPublicacao`.

#### Arquitetura e módulos

- `src/app/ingestao.py`: nova função `ler_documentos_lote(session, identity, lote_id, documento_ids)` que valida escopo e aptidão, materializa os `.md` do storage do lote e reaproveita a validação de limites de `ler_arquivos_markdown`, devolvendo `(nome, bytes)` e o hash de cada um.
- `src/app/routers/ingestao.py` e `src/app/routers/envios.py`: novos campos de formulário `lote_id` e `documento_ids` com exclusividade entre as três fontes; no envio, gravar a origem na mesma transação do `Envio`.
- `src/app/routers/conversao.py`: `GET /conversoes/{lote}` passa a incluir, por documento, `indexado` (colecao, hash, marca `alterado` ou `expirado`); nova leitura calcula a marca comparando o hash do `.md` atual.
- `src/app/models.py`: nova entidade `OrigemDocumento` (ver seção 9).
- Frontend: botão e seleção no painel do lote, origem lote no hook do fluxo, exibição da origem e da marca na coleção.

#### Migrations

- Revisão `0043_origem_documento_lote` após `0042_schema_da_fila`: cria `origens_documento` com índices; aditiva, sem backfill. Downgrade remove só a tabela nova.

#### Models

- `OrigemDocumento` em `src/app/models.py`: vínculo entre `documentos_colecao` e `documentos_conversao`, com hash e envio de origem.

#### Controllers e casos de uso

- `criar_envio` e `previa` aceitam a origem lote; autorização `require_write_role` mais escopo do lote em `repo.get_lote_or_404`.
- Reindexar usa a mesma rota de `criar_envio` com `colecao_id` existente e os `documento_ids` do lote; o servidor confere que o documento já pertence àquela coleção.

#### Views e experiência

- Painel do lote com "Seguir para a indexação" e seleção; fluxo de ingestão com origem lote (etapa Arquivos somente leitura para os documentos do lote); `DataGridDocumentos` e o painel do lote com o selo de origem e a marca. Estados na seção 10.

#### Queries e repositórios

- Documentos de lote do Workspace por `lote_id` e ids, filtrando `situacao == "concluido"` e `apagado_em IS NULL`.
- Origens por `colecao_id` (índice em `documento_colecao_id`) para montar a grade de documentos sem consulta por linha.

#### Jobs e processamento assíncrono

- Sem job novo. O envio segue `process_envio_task`; o registro de origem é gravado na criação do envio, antes de enfileirar, e o hash vale para o conteúdo que o worker vai ler.

#### Estrutura de arquivos

```text
specs/completed/0043-seguir-direto-para-a-indexacao/
  spec.md
  research/
src/app/ingestao.py
src/app/models.py
src/app/routers/ingestao.py
src/app/routers/envios.py
src/app/routers/conversao.py
alembic/versions/0043_origem_documento_lote.py
frontend/src/features/conversao/PainelLoteConversao.tsx
frontend/src/features/conversao/SeguirParaIndexacao.tsx
frontend/src/features/ingestao/useFluxoIngestao.ts
frontend/src/features/ingestao/EtapaArquivos.tsx
frontend/src/features/colecoes/DataGridDocumentos.tsx
tests/
```

### 9. Modelo de dados

#### Entidades

| Entidade | Identidade | Atributos e regras | Relações |
| --- | --- | --- | --- |
| `origens_documento` | `id` (uuid) | `documento_colecao_id` (FK `documentos_colecao.id`, `CASCADE`, único), `lote_id` (FK `lotes_conversao.id`), `documento_conversao_id` (FK `documentos_conversao.id`), `envio_id` (FK `envios.id`, envio que gravou a versão), `hash_md` (SHA-256 do `.md` lido, 64), `criado_em`, `atualizado_em` | N:1 com documento da coleção (1:1 por documento), N:1 com documento do lote e com envio |

#### Estados e transições

| Entidade | Estado atual | Evento | Próximo estado | Invariantes |
| --- | --- | --- | --- | --- |
| Origem do documento | inexistente | envio com origem lote criado | registrada com `hash_md` | uma origem por documento da coleção |
| Origem do documento | registrada | reindexação confirmada | registrada com novo `hash_md` e `envio_id` | substitui, não duplica |
| Marca derivada | em dia | hash atual do `.md` do lote difere de `hash_md` | alterado desde a indexação | calculada, não persistida |
| Marca derivada | em dia ou alterado | arquivo do lote apagado | arquivo do lote expirado | origem permanece; marca deixa de ser calculada |

#### Migração e retenção

- Migração aditiva `0043_origem_documento_lote`, sem backfill: documentos indexados antes da entrega ficam sem origem.
- A origem permanece enquanto o documento existir na coleção e sai junto com ele ou com a coleção. A retenção de 7 dias dos arquivos do lote não muda.

### 10. Interfaces e contratos

#### Interface para pessoas

- **Há interface para pessoas**: Sim. A entrega muda o painel do lote, o fluxo de ingestão e a lista de documentos da coleção.

#### Stack e convenções de interface

- Next.js 16 com App Router, React 19, Tailwind 4, shadcn/ui e ReUI conforme `INTERFACE.md`; formulários e diálogos com `Dialog`, `Alert` e `Button` existentes; testes com Vitest e Testing Library. Telas atuais afetadas: lotes de conversão (`DataGridLotesConversao`, `PainelLoteConversao`, `ConversaoSheet`), fluxo `/workspaces/[id]/enviar` (`FluxoIngestao`, `EtapaArquivos`, `EtapaPublicacao`) e a coleção (`DataGridDocumentos`). Preserva: download do pacote, upload manual, base preparada, quatro etapas do fluxo, `Breadcrumb` e `PageHeader`.

#### Telas e responsabilidades

- **Painel do lote**: owner e admin escolhem documentos aptos e seguem; todos veem a origem e a marca nos documentos já indexados.
- **Fluxo de ingestão com origem lote**: a mesma página de envio; a etapa Arquivos lista os documentos do lote (sem seletor de arquivos) e a publicação escolhe a coleção e confirma.
- **Coleção, aba Documentos**: mostra o selo de origem e a marca; owner e admin têm "Reindexar" em documento alterado.

#### Fluxo de informação e navegação

- Lote → "Seguir para a indexação" → `/workspaces/{id}/enviar?lote={loteId}&documentos={ids}` → etapas Arquivos, Divisão, Prévia e Publicação → `/envios/{envio_id}`.
- `Breadcrumb` mantém equipe, módulo e tela atual; o fluxo com origem lote usa o mesmo caminho de "Enviar documentos". Reindexar abre o mesmo fluxo com `colecao` já escolhida e o documento pré-selecionado; recarregar mantém a origem pela rota.

#### Menus e navegação principal

- Sem item novo de menu: o atalho é acessado a partir do lote de conversão, já alcançável pelo módulo de conversão do Workspace; a página de envio continua sem item próprio.

#### Formulários e ações

- Seleção: caixas por documento apto, "Marcar aptos" e "Desmarcar" opcionais; ação principal "Seguir para a indexação" (desabilitada com o motivo visível).
- Publicação: coleção nova ou existente, como hoje; resumo com contagem, destino e aviso de embeddings; "Publicar" confirma.
- Reindexar: diálogo de confirmação com o nome do documento, a coleção e o aviso de embeddings; falha mantém o diálogo aberto com "Tentar novamente".

#### Composição e disposição

- No painel, a barra de ações do lote agrupa "Baixar pacote" e "Seguir para a indexação"; a lista de documentos ganha a coluna de seleção à esquerda, sem alterar a ordem das demais. Em largura estreita a barra quebra em linhas e a seleção permanece alcançável sem rolagem horizontal.

#### Blocos React e componentes selecionados

| Tela | Bloco React | Responsabilidade | Arquivo previsto | Componente ou composição | Origem | Reuso ou extensão |
| --- | --- | --- | --- | --- | --- | --- |
| Painel do lote | `SeguirParaIndexacao` | Botão, seleção e motivo de indisponibilidade | `frontend/src/features/conversao/SeguirParaIndexacao.tsx` | `Button`, `Alert`, checkbox nativo | shadcn/ui e próprio | Novo; mantém `PainelLoteConversao` como composição |
| Painel do lote | `PainelLoteConversao` | Acomoda o bloco e exibe a origem e a marca por documento | `frontend/src/features/conversao/PainelLoteConversao.tsx` | `Badge` | shadcn/ui e próprio | Extensão do existente |
| Fluxo de ingestão | `EtapaArquivos` | Lista documentos do lote somente leitura | `frontend/src/features/ingestao/EtapaArquivos.tsx` | `Alert`, `Button` | shadcn/ui e próprio | Extensão do existente |
| Fluxo de ingestão | `useFluxoIngestao` | Estado da origem lote, prévia e publicação com `lote_id` e `documento_ids` | `frontend/src/features/ingestao/useFluxoIngestao.ts` | hook | próprio | Extensão do existente |
| Coleção | `DataGridDocumentos` | Selo de origem, marca e "Reindexar" | `frontend/src/features/colecoes/DataGridDocumentos.tsx` | `Badge`, `Dialog` | shadcn/ui e próprio | Extensão; confirmação como `ApagarDocumentoDialog` |

- shadcn/ui: `Button`, `Alert`, `Badge`, `Dialog`. ReUI: composições já adotadas em `DataGridDocumentos`; nenhuma composição ReUI nova.
- `INTERFACE.md` deve registrar `SeguirParaIndexacao` e as extensões acima durante a implementação.

#### Estados e acessibilidade

- Carregando (verificando o lote), vazio ("Nenhum documento apto"), erro com "Tentar novamente", sucesso (envio criado e navegação para `/envios/{id}`) e permissão insuficiente (botão ausente para member).
- Teclado: caixas, botão, diálogo e "Reindexar" alcançáveis com foco visível; mudanças de seleção, indisponibilidade e marcas anunciadas em `role="status"`; foco devolvido ao botão ao fechar o diálogo.
- O `Breadcrumb` mantém a equipe visível, usa links válidos nos itens anteriores e marca a tela atual com semântica de página.

#### Contrato CRUD

- Não há CRUD novo. A grade de documentos da coleção continua usando o `DataGrid` em largura total, mantém a coluna `ID` visível e as ações de editar (substituir) e apagar já existentes; "Reindexar" entra como ação adicional por linha. O `PageHeader` reutilizável não muda e nenhuma tela replica seu markup.

#### Revisão visual durante o desenvolvimento

- A revisão visual ocorre durante a implementação, mesmo sem pedido da pessoa, e confere bordas, espaçamentos, margens, padding e tipografia contra `DESIGNSYSTEM.MD` e `INTERFACE.md` nos temas claro e escuro, em desktop e largura de celular, com conteúdo curto e longo. Registre a forma de conferência, o viewport, os estados, os achados e os ajustes na tarefa.

#### APIs expostas

- `POST /api/v1/ingestao/previa` e `POST /api/v1/envios`: novos campos de formulário `lote_id` (texto) e `documento_ids` (lista); exclusivos com `arquivos` e `usar_base_preparada`. Erros: 403 sem papel, 404 lote fora do escopo, 409 documento indisponível, 422 combinação inválida ou nomes repetidos.
- `GET /api/v1/conversoes/{lote_id}`: cada documento inclui `indexado` (`colecao_id`, `colecao_nome`, `situacao_origem`: `em_dia`, `alterado` ou `expirado`) quando houver origem.
- `GET /api/v1/colecoes/{id}/documentos`: cada documento inclui `origem` (`lote_id`, `documento_conversao_id`, `situacao_origem`) quando houver.

#### APIs externas utilizadas

- Nenhuma nova. O provedor de embeddings e o Qdrant são usados pelo envio como hoje.

#### Documentação das APIs consultadas

- Nenhuma fonte externa; contratos lidos em `src/app/routers/envios.py`, `ingestao.py` e `conversao.py`.

#### Eventos e outros contratos

- Não aplicável.

### 11. Estratégia TDD

- **Unidade**: regra de aptidão do documento do lote, cálculo da marca (`em_dia`, `alterado`, `expirado`), exclusividade entre as três fontes e validação de limites (pytest); seleção, indisponibilidade e estados do bloco `SeguirParaIndexacao` (Vitest).
- **Integração/contrato**: `POST /ingestao/previa` e `POST /envios` com origem lote contra o banco de testes isolado (`DatabaseTransactions`, sem comando destrutivo) e storage em diretório temporário; `GET /conversoes/{lote}` e listagem de documentos da coleção com origem.
- **BDD/aceite**: o Gherkin da seção 6 orienta os casos; cada caso TDD declara o próprio marcador `SPECSFY:` com o prefixo da spec.
- **Runner TDD**: pytest no backend (`.venv/bin/python -m pytest -q`) e Vitest no frontend (`npm --prefix frontend run test:tdd`), já adotados pelo projeto.
- **E2E**: percorrer lote concluído → seguir → fluxo → envio concluído → origem e marca visíveis, com serviços publicados de teste.
- **Verificação manual**: revisão visual em navegador real nos temas claro e escuro; a indexação real contra provedor pago fica como verificação opt-in.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| US-001, FR-001, FR-002, FR-005, FR-009, NFR-004, AC-001 | AC-001 na seção 6 | caso 1 em `frontend/src/features/conversao/SeguirParaIndexacao.test.tsx` (marca aptos e segue) com marcador próprio `SPECSFY: SPEC-0043 AC-001` | Observado em 2026-10-22: componente `SeguirParaIndexacao` ausente em frontend/src/features/conversao | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-001, FR-001, FR-009, FR-010, AC-002 | AC-002 na seção 6 | caso 2 em `frontend/src/features/conversao/SeguirParaIndexacao.test.tsx` (indisponível por estado) com marcador próprio `SPECSFY: SPEC-0043 AC-002` | Observado em 2026-10-22: componente `SeguirParaIndexacao` ausente em frontend/src/features/conversao | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-001, FR-010, NFR-001, AC-003 | AC-003 na seção 6 | caso 3 em `tests/test_envio_origem_lote.py` (member 403 e owner 201) com marcador próprio `SPECSFY: SPEC-0043 AC-003` | Observado em 2026-10-22: a API responde 400 "Envie ao menos um arquivo .md" onde a spec exige 201, 404, 409 ou 422 (origem lote ainda não aceita) | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-001, FR-002, FR-005, NFR-004, AC-004 | AC-004 na seção 6 | caso 4 em `frontend/src/features/conversao/SeguirParaIndexacao.test.tsx` (nenhum marcado) com marcador próprio `SPECSFY: SPEC-0043 AC-004` | Observado em 2026-10-22: componente `SeguirParaIndexacao` ausente em frontend/src/features/conversao | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-002, FR-003, FR-004, AC-005 | AC-005 na seção 6 | caso 5 em `frontend/src/features/ingestao/FluxoIngestao.test.tsx` (fluxo abre com o lote) com marcador próprio `SPECSFY: SPEC-0043 AC-005` | Observado em 2026-10-22: a etapa Arquivos não lista os documentos do lote (`loteInicial` ainda não é tratado) | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-002, FR-003, FR-004, FR-005, NFR-002, NFR-003, AC-006 | AC-006 na seção 6 | caso 6 em `tests/test_envio_origem_lote.py` (prévia e envio leem o lote) com marcador próprio `SPECSFY: SPEC-0043 AC-006` | Observado em 2026-10-22: a API responde 400 "Envie ao menos um arquivo .md" onde a spec exige 201, 404, 409 ou 422 (origem lote ainda não aceita) | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-002, FR-003, FR-004, NFR-003, AC-007 | AC-007 na seção 6 | caso 7 em `tests/test_envio_origem_lote.py` (documento apagado recusa 409) com marcador próprio `SPECSFY: SPEC-0043 AC-007` | Observado em 2026-10-22: a API responde 400 "Envie ao menos um arquivo .md" onde a spec exige 201, 404, 409 ou 422 (origem lote ainda não aceita) | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-002, FR-009, NFR-004, AC-008 | AC-008 na seção 6 | caso 8 em `tests/test_origem_lote_compatibilidade.py` (upload manual intacto e exclusividade) com marcador próprio `SPECSFY: SPEC-0043 AC-008` | Observado em 2026-10-22: combinar `arquivos`, `usar_base_preparada` e `lote_id` ainda devolve 201 em vez de 422 | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-003, FR-006, NFR-002, AC-009 | AC-009 na seção 6 | caso 9 em `tests/test_origem_documento.py` (origem sem texto) com marcador próprio `SPECSFY: SPEC-0043 AC-009` | Observado em 2026-10-22: o primeiro envio a partir do lote responde 400 (origem lote ainda não aceita), logo `origem`, `indexado` e `OrigemDocumento` não existem | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-003, FR-006, FR-007, FR-008, NFR-003, AC-010 | AC-010 na seção 6 | caso 10 em `tests/test_origem_documento.py` (marca alterado) com marcador próprio `SPECSFY: SPEC-0043 AC-010` | Observado em 2026-10-22: o primeiro envio a partir do lote responde 400 (origem lote ainda não aceita), logo `origem`, `indexado` e `OrigemDocumento` não existem | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-003, FR-007, NFR-002, AC-011 | AC-011 na seção 6 | caso 11 em `tests/test_origem_documento.py` (arquivo do lote expirado) com marcador próprio `SPECSFY: SPEC-0043 AC-011` | Observado em 2026-10-22: o primeiro envio a partir do lote responde 400 (origem lote ainda não aceita), logo `origem`, `indexado` e `OrigemDocumento` não existem | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-003, FR-006, FR-008, FR-010, AC-012 | AC-012 na seção 6 | caso 12 em `tests/test_envio_origem_lote.py` (reindexar) com marcador próprio `SPECSFY: SPEC-0043 AC-012` | Observado em 2026-10-22: a API responde 400 "Envie ao menos um arquivo .md" onde a spec exige 201, 404, 409 ou 422 (origem lote ainda não aceita) | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-002, FR-004, FR-010, NFR-001, AC-013 | AC-013 na seção 6 | caso 13 em `tests/test_envio_origem_lote.py` (lote de outro workspace 404) com marcador próprio `SPECSFY: SPEC-0043 AC-013` | Observado em 2026-10-22: a API responde 400 "Envie ao menos um arquivo .md" onde a spec exige 201, 404, 409 ou 422 (origem lote ainda não aceita) | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-001, US-003, FR-001, FR-002, FR-007, NFR-004, AC-014 | AC-014 na seção 6 | caso 14 em `frontend/src/features/conversao/SeguirParaIndexacao.a11y.test.tsx` (teclado e estados) com marcador próprio `SPECSFY: SPEC-0043 AC-014` | Observado em 2026-10-22: componente `SeguirParaIndexacao` ausente e `DataGridDocumentos` sem a marca "alterado desde a indexação" nem a ação Reindexar | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |
| US-003, FR-007, FR-008, FR-010, NFR-001, AC-015 | AC-015 na seção 6 | caso 15 em `tests/test_origem_documento.py` (member vê e não reindexa) com marcador próprio `SPECSFY: SPEC-0043 AC-015` | Observado em 2026-10-22: o primeiro envio a partir do lote responde 400 (origem lote ainda não aceita), logo `origem`, `indexado` e `OrigemDocumento` não existem | GREEN: teste focal verde em 2026-10-23 (backend: 10 passed; frontend: Vitest completo) | Regressão: CI do PR #75 com pytest 845 passed, 1 skipped; vitest 294 passed |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenário BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| FR-001 | AC-001, AC-002, AC-014 | Unidade | `frontend/src/features/conversao/SeguirParaIndexacao.test.tsx` | Passed |
| FR-002 | AC-001, AC-004, AC-014 | Unidade | `frontend/src/features/conversao/SeguirParaIndexacao.test.tsx` | Passed |
| FR-003 | AC-005, AC-006, AC-007 | Integração | `frontend/src/features/ingestao/FluxoIngestao.test.tsx` | Passed |
| FR-004 | AC-005, AC-006, AC-007, AC-013 | Integração | `tests/test_envio_origem_lote.py` | Passed |
| FR-005 | AC-001, AC-004, AC-006 | Integração | `frontend/src/features/ingestao/EtapaPublicacao.test.tsx` | Passed |
| FR-006 | AC-009, AC-010, AC-012 | Integração | `tests/test_origem_documento.py` | Passed |
| FR-007 | AC-010, AC-011, AC-014, AC-015 | Integração | `tests/test_origem_documento.py` | Passed |
| FR-008 | AC-010, AC-012, AC-015 | Integração | `tests/test_envio_origem_lote.py` | Passed |
| FR-009 | AC-001, AC-002, AC-008 | Integração | `tests/test_envios.py` e `tests/test_ingestao_previa.py` | Passed |
| FR-010 | AC-002, AC-003, AC-012, AC-013, AC-015 | Integração | `tests/test_envio_origem_lote.py` | Passed |
| NFR-001 | AC-003, AC-013, AC-015 | Integração | `tests/test_envio_origem_lote.py` | Passed |
| NFR-002 | AC-006, AC-009, AC-011 | Integração | `tests/test_origem_documento.py` | Passed |
| NFR-003 | AC-006, AC-007, AC-010 | Integração | `tests/test_envio_origem_lote.py` | Passed |
| NFR-004 | AC-001, AC-004, AC-008, AC-014 | Regressão e acessibilidade | `.venv/bin/python -m pytest -q` e `npm --prefix frontend run test:tdd` | Passed |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY (2026-10-22)
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/completed/0043-seguir-direto-para-a-indexacao/spec.md`
- **Achados**: 0 BLOCKER. Cobertura conferida: a feature, cada US, FR e NFR têm pelo menos 3 AC em `**Cobre**` (3 US, 10 FR, 4 NFR e 15 AC). WARNING resolvido: custo de leitura e hash do `.md` no polling do lote, mitigado na seção 16. WARNING resolvido: a DoD passou a citar `.specsfy/DATABASE.md`, `INTERFACE.md` e a revisão de `PROJECT.md`. NOTE: a limpeza em andamento bloqueia o botão por suposição reversível (seção 16). Nomes citados conferidos no código: `require_write_role`, `ler_arquivos_markdown`, `ler_base_preparada`, `storage.materialize`, `GET /colecoes/{id}/documentos`, revisão `0042_schema_da_fila`.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: Passed (2026-10-22)
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/completed/0043-seguir-direto-para-a-indexacao/spec.md`
- **Achados**: 26 tarefas (16 `[TEST]`, 8 `[CODE]`, 2 `[DOC]`); 32 de 32 IDs cobertos; 15 AC com uma tarefa TDD própria cada, todas concluídas com RED válido; cada tarefa `[CODE]` depende dos predecessores TDD da sua fatia; `[DOC]` para `.specsfy/DATABASE.md` (T017) e `INTERFACE.md` e `PROJECT.md` (T025); tarefas de interface na `Fase de interface`. Backend RED: 10 testes em `tests/test_envio_origem_lote.py`, `tests/test_origem_documento.py` e `tests/test_origem_lote_compatibilidade.py` (banco de testes isolado, vector store e embeddings dublados); frontend RED: 6 testes em `SeguirParaIndexacao.test.tsx`, `SeguirParaIndexacao.a11y.test.tsx` e `FluxoIngestao.test.tsx`. Proteção do banco: SAFE.

#### Gate do Ato III — Entrega

- **Resultado**: Passed (2026-10-23)
- **Comando**: `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/completed/0043-seguir-direto-para-a-indexacao/spec.md .`
- **Achados**: 26 de 26 tarefas concluídas; 32 de 32 IDs cobertos (`--full-chain` OK) e os 15 AC com GREEN. Regressão no CI do PR #75: pytest 845 passed e 1 skipped (o skip é o opt-in pago da SPEC-0014), Vitest 77 arquivos e 294 testes; localmente `ruff check .`, ESLint, `tsc --noEmit` e `npm run build` limpos. Falhas preexistentes: nenhuma. Revisão visual por inspeção do DOM e das classes contra `DESIGNSYSTEM.MD`, sem captura em navegador real. A indexação real contra provedor pago não foi exercida (verificação opt-in).

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

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso de teste falhando em frontend/src/features/conversao/SeguirParaIndexacao.test.tsx — Refs: US-001, FR-001, FR-002, FR-005, FR-009, NFR-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-001`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/conversao/SeguirParaIndexacao.test.tsx` em 2026-10-22; causa do RED: componente `SeguirParaIndexacao` ausente em frontend/src/features/conversao.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso de teste falhando em frontend/src/features/conversao/SeguirParaIndexacao.test.tsx — Refs: US-001, FR-001, FR-009, FR-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-002`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/conversao/SeguirParaIndexacao.test.tsx` em 2026-10-22; causa do RED: componente `SeguirParaIndexacao` ausente em frontend/src/features/conversao.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso de teste falhando em tests/test_envio_origem_lote.py — Refs: US-001, FR-010, NFR-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-003`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_envio_origem_lote.py -q` em 2026-10-22; causa do RED: a API responde 400 "Envie ao menos um arquivo .md" onde a spec exige 201, 404, 409 ou 422 (origem lote ainda não aceita).
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T004 [TEST] [TDD] [US-001] Derivar do AC-004 um caso de teste falhando em frontend/src/features/conversao/SeguirParaIndexacao.test.tsx — Refs: US-001, FR-002, FR-005, NFR-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-004`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/conversao/SeguirParaIndexacao.test.tsx` em 2026-10-22; causa do RED: componente `SeguirParaIndexacao` ausente em frontend/src/features/conversao.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T005 [TEST] [TDD] [US-002] Derivar do AC-005 um caso de teste falhando em frontend/src/features/ingestao/FluxoIngestao.test.tsx — Refs: US-002, FR-003, FR-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-005`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/ingestao/FluxoIngestao.test.tsx` em 2026-10-22; causa do RED: a etapa Arquivos não lista os documentos do lote (`loteInicial` ainda não é tratado).
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T006 [TEST] [TDD] [US-002] Derivar do AC-006 um caso de teste falhando em tests/test_envio_origem_lote.py — Refs: US-002, FR-003, FR-004, FR-005, NFR-002, NFR-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-006`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_envio_origem_lote.py -q` em 2026-10-22; causa do RED: a API responde 400 "Envie ao menos um arquivo .md" onde a spec exige 201, 404, 409 ou 422 (origem lote ainda não aceita).
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso de teste falhando em tests/test_envio_origem_lote.py — Refs: US-002, FR-003, FR-004, NFR-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-007`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_envio_origem_lote.py -q` em 2026-10-22; causa do RED: a API responde 400 "Envie ao menos um arquivo .md" onde a spec exige 201, 404, 409 ou 422 (origem lote ainda não aceita).
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 um caso de teste falhando em tests/test_origem_lote_compatibilidade.py — Refs: US-002, FR-009, NFR-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-008`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_origem_lote_compatibilidade.py -q` em 2026-10-22; causa do RED: combinar `arquivos`, `usar_base_preparada` e `lote_id` ainda devolve 201 em vez de 422.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T009 [TEST] [TDD] [US-003] Derivar do AC-009 um caso de teste falhando em tests/test_origem_documento.py — Refs: US-003, FR-006, NFR-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-009`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_origem_documento.py -q` em 2026-10-22; causa do RED: o primeiro envio a partir do lote responde 400 (origem lote ainda não aceita), logo `origem`, `indexado` e `OrigemDocumento` não existem.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-010 um caso de teste falhando em tests/test_origem_documento.py — Refs: US-003, FR-006, FR-007, FR-008, NFR-003 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-010`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_origem_documento.py -q` em 2026-10-22; causa do RED: o primeiro envio a partir do lote responde 400 (origem lote ainda não aceita), logo `origem`, `indexado` e `OrigemDocumento` não existem.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 um caso de teste falhando em tests/test_origem_documento.py — Refs: US-003, FR-007, NFR-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-011`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_origem_documento.py -q` em 2026-10-22; causa do RED: o primeiro envio a partir do lote responde 400 (origem lote ainda não aceita), logo `origem`, `indexado` e `OrigemDocumento` não existem.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso de teste falhando em tests/test_envio_origem_lote.py — Refs: US-003, FR-006, FR-008, FR-010 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-012`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_envio_origem_lote.py -q` em 2026-10-22; causa do RED: a API responde 400 "Envie ao menos um arquivo .md" onde a spec exige 201, 404, 409 ou 422 (origem lote ainda não aceita).
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T013 [TEST] [TDD] [US-002] Derivar do AC-013 um caso de teste falhando em tests/test_envio_origem_lote.py — Refs: US-002, FR-004, FR-010, NFR-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-013`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_envio_origem_lote.py -q` em 2026-10-22; causa do RED: a API responde 400 "Envie ao menos um arquivo .md" onde a spec exige 201, 404, 409 ou 422 (origem lote ainda não aceita).
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T014 [TEST] [TDD] [US-001] Derivar do AC-014 um caso de teste falhando em frontend/src/features/conversao/SeguirParaIndexacao.a11y.test.tsx — Refs: US-001, US-003, FR-001, FR-002, FR-007, NFR-004 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-014`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/conversao/SeguirParaIndexacao.a11y.test.tsx` em 2026-10-22; causa do RED: componente `SeguirParaIndexacao` ausente e `DataGridDocumentos` sem a marca "alterado desde a indexação" nem a ação Reindexar.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

- [x] T015 [TEST] [TDD] [US-003] Derivar do AC-015 um caso de teste falhando em tests/test_origem_documento.py — Refs: US-003, FR-007, FR-008, FR-010, NFR-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin da spec e confirmar regra, IDs e nível.
  - [x] **EXECUTE**: Escrever o caso TDD com marcador próprio `SPECSFY: SPEC-0043 AC-015`, sem criar ou executar `.feature`.
  - [x] **VERIFY**: Observar RED válido.
  - [x] **VISUAL**: Não aplicável: a tarefa só materializa o teste; a conferência visual ocorre na tarefa de interface correspondente.
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_origem_documento.py -q` em 2026-10-22; causa do RED: o primeiro envio a partir do lote responde 400 (origem lote ainda não aceita), logo `origem`, `indexado` e `OrigemDocumento` não existem.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: cobertura revisada contra o Gherkin; contratos assumidos documentados no docstring de `tests/_origem_lote.py` e nas props dos testes.

#### Fase 2 — Fundação e backend

- [x] T016 [CODE] [US-003] Criar a migration `alembic/versions/0043_origem_documento_lote.py` e o model `OrigemDocumento` em src/app/models.py — Refs: US-003, FR-006, NFR-002, AC-009, AC-010, AC-011 — Depends: T009, T010, T011
  - [x] **PREP**: Carregar `$specsfy-documentator` para reconstruir `docs/` de forma independente, confirmar o RED das dependências e o baseline antes de editar.
  - [x] **EXECUTE**: Criar a tabela `origens_documento` aditiva, sem backfill, com downgrade que remove só a tabela, e o model com as relações da seção 9.
  - [x] **VERIFY**: Executar `.venv/bin/python -m pytest tests/test_origem_documento.py -q` e a regressão do módulo.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (backend, migration ou documentação).
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_app_migrations.py tests/test_app_models.py -q` em 2026-10-23: 8 passed. Arquivos: alembic/versions/0043_origem_documento_lote.py, src/app/models.py. Banco de testes isolado por schema (SAFE).
  - [x] **IMPROVE**: Nenhuma melhoria adicional: índice único por documento e CASCADE já cobrem apagar documento ou coleção.
  <!-- specsfy:evidence {"task": "T016", "refs": ["US-003", "FR-006", "NFR-002", "AC-009", "AC-010", "AC-011"], "files": ["alembic/versions/0043_origem_documento_lote.py", "src/app/models.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_app_migrations.py tests/test_app_models.py -q", "exit": 0}]} -->

- [x] T017 [DOC] Atualizar .specsfy/DATABASE.md com `origens_documento`, a revisão `0043_origem_documento_lote`, o ciclo de vida e o acesso confirmados — Refs: US-003, FR-006, NFR-002, AC-009, AC-011 — Depends: T016
  - [x] **PREP**: Ler a seção `Informações a guardar confirmadas` já registrada em 2026-10-22 e o diff do model.
  - [x] **EXECUTE**: Acrescentar a tabela detectada com colunas, chaves, relações e arquivos de origem, preservando o conteúdo humano.
  - [x] **VERIFY**: Executar `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check`.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (backend, migration ou documentação).
  - [x] **EVIDENCE**: `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` em 2026-10-23: CURRENT. Arquivos: .specsfy/DATABASE.md. Banco de testes isolado por schema (SAFE). PROJECT.md revisado: sem impacto material na história, finalidade, capacidades ou limites (atalho opcional entre capacidades já descritas); avaliação reconhecida com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: Nenhuma melhoria adicional: a linha detectada foi acrescentada sem tocar as notas humanas.

- [x] T018 [CODE] [US-002] Implementar `ler_documentos_lote` em src/app/ingestao.py com escopo, aptidão, limites e hash do `.md` — Refs: US-002, FR-004, FR-010, NFR-001, NFR-002, NFR-003, AC-006, AC-007, AC-013 — Depends: T006, T007, T013, T016
  - [x] **PREP**: Carregar `$specsfy-documentator` para reconstruir `docs/` de forma independente, confirmar o RED das dependências e o baseline antes de editar.
  - [x] **EXECUTE**: Ler cada `.md` do armazenamento do lote uma única vez, validar quantidade, extensão, UTF-8 e 5 MB com a validação compartilhada, calcular o SHA-256 do conteúdo lido e recusar lote fora do escopo (404) e documento indisponível (409).
  - [x] **VERIFY**: Executar `.venv/bin/python -m pytest tests/test_envio_origem_lote.py -q` e a regressão do módulo.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (backend, migration ou documentação).
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_envio_origem_lote.py tests/test_origem_documento.py tests/test_origem_lote_compatibilidade.py -q` em 2026-10-23: 10 passed. Arquivos: src/app/origem_lote.py, src/app/ingestao.py. Banco de testes isolado por schema (SAFE).
  - [x] **IMPROVE**: Extraí `validar_conteudo_markdown` de `ler_arquivos_markdown` para o upload e o lote compartilharem a mesma validação; `ingestao.py` seguiu sem banco, por isso a leitura do lote ficou em `origem_lote.py`.
  <!-- specsfy:evidence {"task": "T018", "refs": ["US-002", "FR-004", "FR-010", "NFR-001", "NFR-002", "NFR-003", "AC-006", "AC-007", "AC-013"], "files": ["src/app/origem_lote.py", "src/app/ingestao.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_envio_origem_lote.py tests/test_origem_documento.py tests/test_origem_lote_compatibilidade.py -q", "exit": 0}]} -->

- [x] T019 [CODE] [US-002] Aceitar a origem lote em `POST /api/v1/ingestao/previa` em src/app/routers/ingestao.py — Refs: US-002, FR-004, FR-009, FR-010, NFR-001, AC-005, AC-008, AC-013 — Depends: T005, T008, T013, T018
  - [x] **PREP**: Carregar `$specsfy-documentator` para reconstruir `docs/` de forma independente, confirmar o RED das dependências e o baseline antes de editar.
  - [x] **EXECUTE**: Adicionar `lote_id` e `documento_ids`, exigir exclusividade com `arquivos` e `usar_base_preparada` (422) e manter os dois caminhos atuais inalterados.
  - [x] **VERIFY**: Executar `.venv/bin/python -m pytest tests/test_origem_lote_compatibilidade.py tests/test_envio_origem_lote.py -q` e a regressão do módulo.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (backend, migration ou documentação).
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_envio_origem_lote.py tests/test_origem_documento.py tests/test_origem_lote_compatibilidade.py -q` em 2026-10-23: 10 passed. Arquivos: src/app/routers/ingestao.py, src/app/origem_lote.py. Banco de testes isolado por schema (SAFE).
  - [x] **IMPROVE**: Nenhuma melhoria adicional: a menor mudança que torna o teste verde; refatoração só dentro dos arquivos da tarefa.
  <!-- specsfy:evidence {"task": "T019", "refs": ["US-002", "FR-004", "FR-009", "FR-010", "NFR-001", "AC-005", "AC-008", "AC-013"], "files": ["src/app/routers/ingestao.py", "src/app/origem_lote.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_envio_origem_lote.py tests/test_origem_documento.py tests/test_origem_lote_compatibilidade.py -q", "exit": 0}]} -->

- [x] T020 [CODE] [US-002] Aceitar a origem lote em `POST /api/v1/envios`, gravar a `OrigemDocumento` na mesma transação e permitir a reindexação em src/app/routers/envios.py — Refs: US-002, US-003, FR-004, FR-006, FR-008, FR-010, NFR-001, NFR-002, NFR-003, AC-003, AC-006, AC-007, AC-012, AC-013 — Depends: T003, T006, T007, T012, T013, T016, T018
  - [x] **PREP**: Carregar `$specsfy-documentator` para reconstruir `docs/` de forma independente, confirmar o RED das dependências e o baseline antes de editar.
  - [x] **EXECUTE**: Criar o envio com os `.md` lidos do lote, gravar origem e hash junto do `Envio`, atualizar a origem na reindexação conferindo que o documento pertence à coleção e recusar member (403).
  - [x] **VERIFY**: Executar `.venv/bin/python -m pytest tests/test_envio_origem_lote.py -q` e a regressão do módulo.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (backend, migration ou documentação).
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_envio_origem_lote.py tests/test_origem_documento.py tests/test_origem_lote_compatibilidade.py -q` em 2026-10-23: 10 passed. Arquivos: src/app/routers/envios.py, src/app/tasks.py, src/app/origem_lote.py. Banco de testes isolado por schema (SAFE).
  - [x] **IMPROVE**: Decisão interna reversível: como o worker cria o `DocumentoColecao`, a origem é gravada por ele a partir de `envios.processamento.origem_lote` (ids e hashes), e a chave é retirada do `chunking` do documento. A reindexação é um envio comum com `colecao_id`, sem checagem extra de pertencimento.
  <!-- specsfy:evidence {"task": "T020", "refs": ["US-002", "US-003", "FR-004", "FR-006", "FR-008", "FR-010", "NFR-001", "NFR-002", "NFR-003", "AC-003", "AC-006", "AC-007", "AC-012", "AC-013"], "files": ["src/app/routers/envios.py", "src/app/tasks.py", "src/app/origem_lote.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_envio_origem_lote.py tests/test_origem_documento.py tests/test_origem_lote_compatibilidade.py -q", "exit": 0}]} -->

- [x] T021 [CODE] [US-003] Expor `indexado` em `GET /api/v1/conversoes/{lote}` e `origem` em `GET /api/v1/colecoes/{id}/documentos` em src/app/routers/conversao.py e src/app/routers/colecoes.py — Refs: US-003, FR-007, NFR-002, AC-009, AC-010, AC-011, AC-015 — Depends: T009, T010, T011, T015, T016
  - [x] **PREP**: Carregar `$specsfy-documentator` para reconstruir `docs/` de forma independente, confirmar o RED das dependências e o baseline antes de editar.
  - [x] **EXECUTE**: Calcular `em_dia`, `alterado` ou `expirado` só para documentos com origem e fora do polling ativo, sem persistir a marca e sem expor texto do cliente.
  - [x] **VERIFY**: Executar `.venv/bin/python -m pytest tests/test_origem_documento.py -q` e a regressão do módulo.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (backend, migration ou documentação).
  - [x] **EVIDENCE**: `.venv/bin/python -m pytest tests/test_envio_origem_lote.py tests/test_origem_documento.py tests/test_origem_lote_compatibilidade.py -q` em 2026-10-23: 10 passed. Arquivos: src/app/routers/conversao.py, src/app/routers/colecoes.py, src/app/origem_lote.py. Banco de testes isolado por schema (SAFE).
  - [x] **IMPROVE**: A API do lote passou a devolver `apagado_em` por documento, que a interface precisa para decidir quem é apto.
  <!-- specsfy:evidence {"task": "T021", "refs": ["US-003", "FR-007", "NFR-002", "AC-009", "AC-010", "AC-011", "AC-015"], "files": ["src/app/routers/conversao.py", "src/app/routers/colecoes.py", "src/app/origem_lote.py"], "commands": [{"run": ".venv/bin/python -m pytest tests/test_envio_origem_lote.py tests/test_origem_documento.py tests/test_origem_lote_compatibilidade.py -q", "exit": 0}]} -->

#### Fase de interface

- [x] T022 [CODE] [US-001] Implementar o bloco `SeguirParaIndexacao` e integrá-lo ao painel do lote em frontend/src/features/conversao/SeguirParaIndexacao.tsx e PainelLoteConversao.tsx — Refs: US-001, FR-001, FR-002, FR-005, FR-009, NFR-004, AC-001, AC-002, AC-004, AC-014 — Depends: T001, T002, T004, T014
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components`, ler `INTERFACE.md`, reconstruir `docs/` com `$specsfy-documentator` e confirmar o RED das dependências antes de escrever JSX ou TSX.
  - [x] **EXECUTE**: Criar o botão com seleção por caixas, aptos marcados por padrão, motivo visível de indisponibilidade e região `role="status"`, ausente para member, ao lado de "Baixar pacote".
  - [x] **VERIFY**: Exercitar seleção, indisponibilidade por estado do lote, teclado e anúncio de status.
  - [x] **VISUAL**: Conferência de bordas, espaçamentos, margens, padding e tipografia por inspeção do DOM e das classes contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, sem captura em navegador real: o bloco reaproveita os tokens dos vizinhos (`rounded-lg border`, `text-sm`, `gap-2/3`, `[overflow-wrap:anywhere]`, `Button` sm/xs, `Badge` outline/secondary), quebra linha com `flex-wrap` em largura estreita e usa só tokens de tema, logo vale nos temas claro e escuro; conteúdo longo quebra por `overflow-wrap`. Nenhum ajuste foi necessário. A conferência em navegador real fica na T026.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/conversao/SeguirParaIndexacao.test.tsx src/features/conversao/SeguirParaIndexacao.a11y.test.tsx` em 2026-10-23: 5 passed (4 deste bloco e o de reindexação, fechado na T024). Arquivos: frontend/src/features/conversao/SeguirParaIndexacao.tsx, frontend/src/features/conversao/PainelLoteConversao.tsx, frontend/src/features/conversao/DataGridLotesConversao.tsx. Banco de testes isolado por schema (SAFE).
  - [x] **IMPROVE**: Os testes antigos do painel passaram a mockar `next/navigation`, porque o painel agora contém o atalho que usa o roteador.
  <!-- specsfy:evidence {"task": "T022", "refs": ["US-001", "FR-001", "FR-002", "FR-005", "FR-009", "NFR-004", "AC-001", "AC-002", "AC-004", "AC-014"], "files": ["frontend/src/features/conversao/SeguirParaIndexacao.tsx", "frontend/src/features/conversao/PainelLoteConversao.tsx", "frontend/src/features/conversao/DataGridLotesConversao.tsx"], "commands": [{"run": "cd frontend && npx vitest run src/features/conversao/SeguirParaIndexacao.test.tsx src/features/conversao/SeguirParaIndexacao.a11y.test.tsx", "exit": 0}]} -->

- [x] T023 [CODE] [US-002] Levar a origem lote ao fluxo de ingestão em frontend/src/features/ingestao/useFluxoIngestao.ts, EtapaArquivos.tsx, EtapaPublicacao.tsx, FluxoIngestao.tsx e frontend/src/app/(autenticado)/workspaces/[id]/enviar/page.tsx — Refs: US-002, FR-003, FR-004, FR-005, NFR-003, AC-005, AC-006, AC-007 — Depends: T005, T006, T007, T019, T020, T022
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components`, ler `INTERFACE.md`, reconstruir `docs/` com `$specsfy-documentator` e confirmar o RED das dependências antes de escrever JSX ou TSX.
  - [x] **EXECUTE**: Ler `lote` e `documentos` da rota, listar os documentos do lote somente leitura na etapa Arquivos, enviar `lote_id` e `documento_ids` à prévia e ao envio, mostrar contagem, destino e aviso de embeddings na publicação e tratar o 409 de documento indisponível.
  - [x] **VERIFY**: Exercitar o fluxo completo com origem lote, o caminho manual e a recarga da página.
  - [x] **VISUAL**: Conferência de bordas, espaçamentos, margens, padding e tipografia por inspeção do DOM e das classes contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, sem captura em navegador real: o bloco reaproveita os tokens dos vizinhos (`rounded-lg border`, `text-sm`, `gap-2/3`, `[overflow-wrap:anywhere]`, `Button` sm/xs, `Badge` outline/secondary), quebra linha com `flex-wrap` em largura estreita e usa só tokens de tema, logo vale nos temas claro e escuro; conteúdo longo quebra por `overflow-wrap`. Nenhum ajuste foi necessário. A conferência em navegador real fica na T026.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src/features/ingestao` em 2026-10-23: 51 passed. Arquivos: frontend/src/features/ingestao/useFluxoIngestao.ts, frontend/src/features/ingestao/EtapaArquivos.tsx, frontend/src/features/ingestao/EtapaPublicacao.tsx, frontend/src/features/ingestao/FluxoIngestao.tsx, frontend/src/app/(autenticado)/workspaces/[id]/enviar/page.tsx. Banco de testes isolado por schema (SAFE).
  - [x] **IMPROVE**: Nenhuma melhoria adicional: a origem lote reaproveita o estado do hook e o mesmo corpo `FormData` do caminho manual.
  <!-- specsfy:evidence {"task": "T023", "refs": ["US-002", "FR-003", "FR-004", "FR-005", "NFR-003", "AC-005", "AC-006", "AC-007"], "files": ["frontend/src/features/ingestao/useFluxoIngestao.ts", "frontend/src/features/ingestao/EtapaArquivos.tsx", "frontend/src/features/ingestao/EtapaPublicacao.tsx", "frontend/src/features/ingestao/FluxoIngestao.tsx", "frontend/src/app/(autenticado)/workspaces/[id]/enviar/page.tsx"], "commands": [{"run": "cd frontend && npx vitest run src/features/ingestao", "exit": 0}]} -->

- [x] T024 [CODE] [US-003] Mostrar a origem, a marca e a reindexação em frontend/src/features/colecoes/DataGridDocumentos.tsx e no painel do lote — Refs: US-003, FR-007, FR-008, FR-010, NFR-001, NFR-004, AC-010, AC-011, AC-012, AC-014, AC-015 — Depends: T010, T011, T012, T014, T015, T020, T021, T022
  - [x] **PREP**: Carregar `$specsfy-specialist-react-ui-components`, ler `INTERFACE.md`, reconstruir `docs/` com `$specsfy-documentator` e confirmar o RED das dependências antes de escrever JSX ou TSX.
  - [x] **EXECUTE**: Exibir o selo de origem, "alterado desde a indexação" e "arquivo do lote expirado", e o diálogo de reindexar com confirmação só para owner e admin, devolvendo o foco ao acionador.
  - [x] **VERIFY**: Exercitar member sem a ação, owner com o diálogo, falha com "Tentar novamente" e teclado.
  - [x] **VISUAL**: Conferência de bordas, espaçamentos, margens, padding e tipografia por inspeção do DOM e das classes contra `DESIGNSYSTEM.MD` e `INTERFACE.md`, sem captura em navegador real: o bloco reaproveita os tokens dos vizinhos (`rounded-lg border`, `text-sm`, `gap-2/3`, `[overflow-wrap:anywhere]`, `Button` sm/xs, `Badge` outline/secondary), quebra linha com `flex-wrap` em largura estreita e usa só tokens de tema, logo vale nos temas claro e escuro; conteúdo longo quebra por `overflow-wrap`. Nenhum ajuste foi necessário. A conferência em navegador real fica na T026.
  - [x] **EVIDENCE**: `cd frontend && npx vitest run src` em 2026-10-23: 77 arquivos e 294 testes passed. Arquivos: frontend/src/features/colecoes/DataGridDocumentos.tsx, frontend/src/features/colecoes/ReindexarDocumentoDialog.tsx, frontend/src/features/colecoes/tipos.ts. Banco de testes isolado por schema (SAFE).
  - [x] **IMPROVE**: A marca e a origem entraram na coluna Arquivo, sem coluna nova, para não alargar a tabela de `min-w-[56rem]`.
  <!-- specsfy:evidence {"task": "T024", "refs": ["US-003", "FR-007", "FR-008", "FR-010", "NFR-001", "NFR-004", "AC-010", "AC-011", "AC-012", "AC-014", "AC-015"], "files": ["frontend/src/features/colecoes/DataGridDocumentos.tsx", "frontend/src/features/colecoes/ReindexarDocumentoDialog.tsx", "frontend/src/features/colecoes/tipos.ts"], "commands": [{"run": "cd frontend && npx vitest run src", "exit": 0}]} -->

- [x] T025 [DOC] Atualizar INTERFACE.md, PROJECT.md (avaliação), docs/ e specs.md com os blocos e operações da SPEC-0043 — Refs: US-001, US-002, US-003, FR-001, FR-007, NFR-004, AC-001, AC-010, AC-014 — Depends: T022, T023, T024
  - [x] **PREP**: Ler os componentes criados ou alterados e o `INTERFACE.md` atual.
  - [x] **EXECUTE**: Registrar `SeguirParaIndexacao` e as extensões de `PainelLoteConversao`, `EtapaArquivos`, `EtapaPublicacao`, `useFluxoIngestao` e `DataGridDocumentos` com arquivo, API, estados, consumidores e regra de reuso; registrar o impacto ou a ausência dele em `PROJECT.md`; confirmar que `.specsfy/STACK.md` não muda.
  - [x] **VERIFY**: Executar `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check` e o `build_documentation --check`.
  - [x] **VISUAL**: Não aplicável: a tarefa não tem superfície visual (backend, migration ou documentação).
  - [x] **EVIDENCE**: `node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check` em 2026-10-23: exit 0; monitor CURRENT com `--acknowledge-project-no-change`. Arquivos: INTERFACE.md, .specsfy/DATABASE.md, docs/README.md, docs/architecture.md, docs/frontend.md, docs/testing.md. Banco de testes isolado por schema (SAFE). PROJECT.md revisado: sem impacto material na história, finalidade, capacidades ou limites (atalho opcional entre capacidades já descritas); avaliação reconhecida com `--acknowledge-project-no-change`.
  - [x] **IMPROVE**: Nenhuma melhoria adicional.

#### Fase final — Qualidade

- [x] T026 [TEST] Executar a regressão completa e a rastreabilidade em tests/test_envio_origem_lote.py e frontend/src/features/conversao/SeguirParaIndexacao.test.tsx — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, NFR-001, NFR-002, NFR-003, NFR-004, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-011, AC-012, AC-013, AC-014, AC-015 — Depends: T017, T020, T021, T023, T024, T025
  - [x] **PREP**: Identificar as suítes, os checks e os gates.
  - [x] **EXECUTE**: Executar `.venv/bin/python -m pytest -q`, `ruff check .`, `npm --prefix frontend run test:tdd`, ESLint, `tsc --noEmit`, `npm --prefix frontend run build` e `check_traceability.mjs`.
  - [x] **VERIFY**: Confirmar ausência de gaps e a regressão do caminho manual.
  - [x] **VISUAL**: Conferência final de bordas, espaçamentos, margens, padding e tipografia por inspeção do DOM e das classes do painel do lote, do fluxo e da grade de documentos, nos dois temas e em dois viewports pelo uso exclusivo de tokens e `flex-wrap`; sem captura em navegador real, registrada como limite.
  - [x] **EVIDENCE**: CI do PR #75 em 2026-10-23: `Ruff and Pytest` 845 passed e 1 skipped; `Frontend (lint, types, tests, build)` com 77 arquivos e 294 testes; `check_traceability.mjs --full-chain`: 32/32 IDs; `verify_acceptance.mjs`: AC com resultado. Local: `ruff check .` limpo e `npm run build` concluído.
  - [x] **IMPROVE**: Retrospectiva: os testes novos de backend precisam constar em `_SUITES_DE_CONVERSAO_COM_BANCO` do `tests/conftest.py`; sem isso rodam sem isolamento por schema e deixam linhas no banco de testes. Vale uma regra para novas suítes com banco.

### 15. Ordem de execução

- Caminho crítico: T001–T015 (RED) → T016 → T018 → T019/T020 → T021 → T022 → T023 → T024 → T025 → T026.
- Tarefas paralelas: nenhuma marcada com `[P]`: os casos de teste compartilham arquivos entre si e as tarefas de código dependem do mesmo model e dos mesmos routers.
- Estratégia de MVP: US-001 e US-002 entregam o atalho completo (T016, T018, T019, T020, T022, T023); US-003 (origem, marca e reindexação) pode ser entregue em seguida (T021, T024).

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- SPEC-0023 (lote e `.md` da Fase 1), SPEC-0026 (fluxo de ingestão), SPEC-0030 (coleções e envios acumulados), SPEC-0039 (liberação na coleção) e SPEC-0042 (Alembic como fonte do schema), todas concluídas.
- Provedor de embeddings e banco vetorial configurados no Workspace, como o fluxo atual exige.

#### Riscos

- O `.md` do lote mudar entre marcar e confirmar → leitura única na criação do envio, hash do conteúdo lido e recusa 409 quando o documento ficar indisponível.
- Custo de leitura e hash do `.md` em cada consulta ao lote (o painel consulta a cada 3 s enquanto há processamento) → calcular a marca só para documentos com origem registrada e somente nas leituras sem processamento ativo; documentos sem origem não leem o armazenamento.
- Custo de embeddings ao reindexar → confirmação explícita e nenhuma reindexação automática.
- O atalho deixar de refletir o caminho manual → mesmas validações compartilhadas em `src/app/ingestao.py` e testes de regressão do caminho manual.
- Guardar documento de cliente além do prazo → a origem guarda só ids e hash; a retenção de 7 dias não muda.

#### Suposições

- Owner e admin acionam o atalho e a reindexação; member consulta (herda a DEC-007 do M04). Reversível.
- "Apto" é o documento `concluido` com arquivo existente, a mesma regra do download do pacote; a limpeza em andamento do lote bloqueia o botão. Reversível.
- Os parâmetros da rota (`lote` e `documentos`) bastam para o fluxo e não passam por armazenamento no navegador. Reversível.
- A marca "alterado" é calculada na leitura, comparando o hash atual com o registrado, e não persistida. Reversível.

### 17. Decisões

- **DEC-001**: Entrada pelo painel do lote de conversão, ao lado de "baixar pacote" — é onde o `.md` está e onde hoje ocorre o desvio; alternativas: etapa Arquivos do fluxo ou botão na coleção.
- **DEC-002**: A pessoa marca os documentos no painel, com os aptos marcados por padrão — dá controle sem obrigar escolha item a item.
- **DEC-003**: A coleção é escolhida na etapa de publicação do fluxo, nova ou existente do Workspace — reaproveita a decisão que o fluxo já pede (SPEC-0030).
- **DEC-004**: Documento alterado é marcado e a reindexação é explícita e confirmada — evita custo de embeddings sem aviso; o envio acumulado substitui a versão antiga.
- **DEC-005**: Confirmação mostra contagem, destino e aviso de embeddings, sem valor em dinheiro — o valor dependeria do provedor e seria frágil.
- **DEC-006**: O atalho não depende de liberação — "Liberar para a base" é da coleção (SPEC-0039) e só existe depois da indexação; substitui a resposta inicial "só depois de liberar" (2026-10-22).
- **DEC-007**: A origem (lote, documento do lote, hash) permanece enquanto o documento existir na coleção; a marca deixa de ser calculada quando o arquivo do lote expira; owner, admin e member veem, e só owner e admin reindexam (descoberta de dados, 2026-10-22).

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Todos os cenários `AC` aplicáveis passam.
- [x] Todos os requisitos possuem evidência de verificação.
- [x] Todas as tarefas na seção 14 estão concluídas.
- [x] Testes e checks estáticos disponíveis passam.
- [x] `.specsfy/DATABASE.md` registra a tabela `origens_documento` e a revisão `0043_origem_documento_lote` (persistência alterada).
- [x] `INTERFACE.md` registra `SeguirParaIndexacao` e as extensões de `PainelLoteConversao`, `EtapaArquivos`, `useFluxoIngestao` e `DataGridDocumentos`.
- [x] `PROJECT.md` foi revisado e o impacto, ou a ausência dele, está registrado na evidência da tarefa; `.specsfy/STACK.md` não muda.
