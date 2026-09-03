# Especificação integrada: Remover hardcodes de cliente das ferramentas operacionais

| Campo | Valor |
| --- | --- |
| Formato | Specsfy/2.0 |
| ID | SPEC-0005 |
| Slug | 0005-remover-hardcodes-cliente |
| Status | Complete |
| Effort | 4 |
| Effort updated at | 2026-09-02 |
| Effort rationale | Recalibrado de 1 para 4 na promoção: além das oito ocorrências de texto, a fatia reestrutura a configuração versionada do repositório, cria duas guardas de regressão de naturezas diferentes e altera um teste existente de varredura documental. O risco está concentrado na saída de `config.yaml` do índice do Git, que muda o procedimento de quem clona o repositório. |
| ClickUp Task | |
| Milestones | M01 |
| Definition Gate | Passed |
| Plan Gate | Passed |
| Delivery Gate | Passed |
| Evidence Contract | 1 |
| Interface para pessoas | Não |
| Atualizada em | 2026-09-02 |

## Ato I — Definir

### 1. Problema e resultado

#### Problema

As três ferramentas operacionais de consulta trazem a identidade de um cliente antigo escrita no código, enquanto a base indexada pertence a outro. `chat.py:94` e `demo_rag.py:94` instruem o modelo a ser especialista em C6 Bank Empresas enquanto recuperam conteúdo de banda larga de telecomunicações, e `demo_rag.py:27` define como pergunta padrão executável uma consulta sobre cheque especial, de modo que `uv run python demo_rag.py` sem argumento interroga a base configurada sobre um produto que ela não cobre.

O acoplamento não se limita ao nome do cliente. Uma varredura por nome próprio encontra cinco ocorrências; incluindo conteúdo do domínio bancário sem o nome, são oito. A distinção importa porque a guarda que vier a ser criada precisa alcançar as duas formas.

Há ainda uma camada acima do código. O repositório versiona `config.yaml` com dez valores de um cliente real como default, entre eles `collection_name` e `namespace`, que endereçam o destino remoto. É dessa camada que nasce o risco de uso no destino errado registrado no BACKLOG-0004: quem clona o repositório recebe, já configurada, a coleção de produção de um cliente.

#### Resultado desejado

O operador aponta as ferramentas para qualquer base editando apenas a configuração, e cada mensagem, prompt e exemplo reflete a base efetivamente configurada. O repositório deixa de distribuir dados de um cliente como default, e uma guarda executável impede que o acoplamento retorne, inclusive para um cliente que ainda não existe.

#### Métricas de sucesso

- Nenhum identificador de cliente, por nome próprio ou conteúdo de domínio, permanece em `chat.py`, `demo_rag.py` e `search.py`, comprovado por guarda estática.
- A identidade apresentada ao operador e enviada ao modelo é derivada da configuração, comprovada por caso que usa uma configuração fictícia e verifica os valores dessa configuração na saída.
- O índice do Git não contém `config.yaml`, e contém um `config.example.yaml` sem identificador de cliente nem destino remoto real.
- A suíte completa permanece verde e nenhuma dependência é acrescentada a `pyproject.toml`.

### 2. Research e esclarecimentos

#### Researchs executados

- **R-001**: quantas e quais são as ocorrências de acoplamento a cliente nas ferramentas operacionais? → Oito, distribuídas em três arquivos. Cinco nomeiam o cliente e três acoplam por conteúdo do domínio bancário. A conclusão ampliou o escopo registrado no backlog, que citava cinco.
- **R-002**: a suíte depende dos valores de `config.yaml`? → Não. Nenhum teste lê valores desse arquivo. `tests/test_docs_safety.py:20` o inclui na lista de material publicado varrido em busca de comando destrutivo, o que exige apenas trocar o alvo da varredura.
- **R-003**: existe precedente local para separar valor de uso e exemplo versionado? → Sim. `.env` está no `.gitignore` e `.env.example` é versionado. A fatia espelha esse par.
- **R-004**: qual guarda o repositório já usa contra identificador de cliente? → `tests/test_validation_boundaries.py:31` mantém uma lista de identificadores conhecidos aplicada ao código de validação. O precedente é reaproveitado, mas a lista sozinha só alcança o nome que alguém registrar nela.
- **R-005**: a apresentação e a busca já divergem no código atual? → Sim. As três ferramentas derivam o escopo de busca da configuração em `chat.py:69`, `demo_rag.py:55` e `search.py:55`; a identidade fixa sobrevive apenas na apresentação e no prompt. A correção é local e não toca o fluxo de recuperação.

#### Fontes e contexto consultados

- `chat.py`, `demo_rag.py` e `search.py`: leitura integral, origem das oito ocorrências.
- `config.yaml`, `.gitignore`, `.env.example` e `src/config.py`: mecanismo de configuração e precedente de separação.
- `tests/test_validation_boundaries.py`, `tests/test_provider_boundaries.py` e `tests/test_docs_safety.py`: guardas estáticas existentes.
- `GUIA_DE_USO.md` e `README.md`: documentação operacional afetada.
- `specs/backlog/0004-remover-hardcodes-cliente.md`: item de origem, refinado em 2026-09-02.
- `specs/completed/0004-validar-recuperacao-operacao/spec.md`: fatia anterior, que criou o gabarito reaproveitado aqui.

#### Documentação consultada

- Nenhuma documentação externa foi consultada nesta fatia.

#### Artefatos de pesquisa armazenados

- `specs/completed/0005-remover-hardcodes-cliente/research/verificacoes-locais.md`: notas de proveniência das inspeções locais de 2026-09-02, com o comando executado, o resultado observado e a consequência para esta spec em cada uma das cinco verificações. Origem: o próprio repositório; sem licença de terceiros aplicável.
- Nenhum artefato externo. Nenhuma fonte fora do repositório foi consultada nesta fatia.

#### Dúvidas respondidas

- **Q**: De onde as ferramentas tiram a identidade da base? → **A**: De `projeto.nome` e `projeto.descricao`, já presentes em `config.yaml`. Nenhum campo novo é criado.
- **Q**: O escopo inclui a configuração versionada e o conteúdo do cliente? → **A**: Inclui a configuração; não inclui `documentos/`, cuja base foi validada pela SPEC-0004 e de quem o gabarito e o manifesto dependem.
- **Q**: Como `config.yaml` muda? → **A**: Um `config.example.yaml` neutro passa a ser versionado e `config.yaml` entra no `.gitignore`, espelhando o par `.env.example` e `.env`.
- **Q**: Como impedir a reincidência? → **A**: Duas guardas. Um caso positivo de derivação como principal, porque alcança nome de cliente ainda inexistente, e a extensão da lista de proibições como rede para literal fora do caminho exercitado.
- **Q**: Qual a pergunta padrão do demonstrativo? → **A**: A primeira consulta declarada no gabarito de `caminhos.consultas_referencia`.
- **Q**: O que acontece quando a configuração não fornece o texto? → **A**: `projeto.nome` continua obrigatório; `projeto.descricao` e o gabarito degradam para texto neutro com aviso. A degradação é proporcional porque as três ferramentas são somente leitura, e a política fail-closed do repositório protege mutação de estado remoto.

#### Dúvidas abertas

- Nenhuma.

### 3. Escopo e atores

#### Incluído

- Derivação da identidade da base em `chat.py` e `demo_rag.py` a partir de `projeto.nome` e `projeto.descricao`.
- Substituição da pergunta padrão executável de `demo_rag.py` pela primeira consulta do gabarito declarado na configuração.
- Neutralização dos exemplos de uso nos docstrings de `search.py` e `demo_rag.py`.
- Criação de `config.example.yaml` neutro versionado e remoção de `config.yaml` do índice do Git, com entrada correspondente no `.gitignore`.
- Guarda positiva de derivação e extensão da lista de proibições existente às três ferramentas.
- Atualização de `GUIA_DE_USO.md`, que hoje declara a limitação como conhecida, do `README.md` quanto ao passo de cópia da configuração, e de `tests/test_docs_safety.py` quanto ao arquivo varrido.

#### Fora de escopo

- `documentos/`, cujo conteúdo pertence a um cliente real mas sustenta a base validada pela SPEC-0004; alterá-lo invalidaria o gabarito e o manifesto daquela fatia.
- A troca do provider de LLM e a fronteira `ChatOpenAI` de `chat.py`, que pertencem ao BACKLOG-0010.
- Qualquer funcionalidade do MVP do projeto-mãe `rag-pipeline`.
- Reescrita do fluxo de recuperação, que já lê a configuração corretamente.
- Reescrita do histórico do Git. Retirar `config.yaml` do índice interrompe a
  distribuição do arquivo daqui em diante, mas `collection_name` e `namespace`
  do cliente permanecem recuperáveis nos commits anteriores. Nenhuma credencial
  está envolvida: `.env` nunca foi versionado. Remover os valores do histórico
  exigiria reescrever commits já publicados e é decisão própria, fora desta
  fatia.

#### Atores

- **Operador do pipeline**: prepara e consulta bases para clientes diferentes por linha de comando; precisa apontar as ferramentas para outra base sem editar código.
- **Mantenedor do componente**: responde pela prontidão do repositório para integração ao projeto-mãe; precisa que o repositório não distribua dados nem destino de um cliente.

### 4. Princípios e restrições do projeto

- **PR-001**: A configuração não sensível fica em `config.yaml` e as credenciais ficam fora do repositório; esta fatia não move segredo algum para arquivo versionado.
- **PR-002**: Imports de SDK de banco vetorial e de classes de embeddings permanecem confinados a `src/providers/`, com `ChatOpenAI` em `chat.py` como única exceção temporária já rastreada pelo BACKLOG-0010.
- **PR-003**: Nenhuma dependência nova é introduzida; a fatia usa apenas o que `pyproject.toml` já declara.
- **PR-004**: Componentes críticos seguem Red-Green-Refactor, com o caso escrito antes da implementação.

### 5. Histórias de usuário

#### US-001 — Apontar as ferramentas para outra base sem editar código (P1)

Como operador do pipeline, quero que mensagens, prompts e a pergunta padrão reflitam a base que eu configurei, para consultar a base de qualquer cliente sem abrir o código e sem receber respostas moldadas por um cliente diferente.

**Por que P1**: hoje o prompt instrui o modelo a ser especialista em um cliente enquanto o contexto recuperado é de outro, o que degrada a resposta e confunde quem demonstra a base.
**Teste independente**: montar uma configuração fictícia com nome e descrição arbitrários e observar esses valores na abertura e no prompt.
**Requisitos**: FR-001, FR-002, FR-003

#### US-002 — Não distribuir a configuração de um cliente no repositório (P1)

Como mantenedor do componente, quero que o repositório versione apenas um exemplo neutro de configuração, para que um clone novo não venha apontado para a coleção de produção de um cliente.

**Por que P1**: é a origem concreta do risco de uso no destino errado; hoje `collection_name` e `namespace` de um cliente real estão no controle de versão.
**Teste independente**: inspecionar o índice do Git e observar a ausência de `config.yaml` e a presença de um exemplo sem identificador de cliente.
**Requisitos**: FR-004, FR-006

#### US-003 — Impedir que o acoplamento retorne (P1)

Como mantenedor do componente, quero uma guarda executável que detecte a reintrodução de identidade de cliente, para não depender de revisão humana nem de memória sobre quais nomes procurar.

**Por que P1**: a fatia perde o valor se o próximo ajuste reintroduzir um literal; e uma lista de proibições sozinha não alcança um cliente futuro.
**Teste independente**: reintroduzir um literal de identidade em uma das ferramentas e observar a suíte reprovar.
**Requisitos**: FR-005, NFR-002, NFR-003

### 6. Cenários BDD de aceite

#### AC-001 — Chat apresenta e instrui a partir da configuração

**Cobre**: US-001, FR-001, NFR-001

```gherkin
@US-001 @FR-001 @NFR-001 @AC-001
Feature: Identidade derivada da configuração

  Scenario: Abertura e prompt refletem a base configurada
    Given uma configuração cujo projeto.nome e projeto.descricao são arbitrários
    When o operador inicia o chat
    Then a mensagem de abertura cita o nome configurado
    And o prompt do sistema cita a descrição configurada
    And nenhum identificador de outro cliente aparece na saída
```

#### AC-002 — Demonstrativo monta o prompt a partir da configuração

**Cobre**: US-001, FR-001, FR-002

```gherkin
@US-001 @FR-001 @FR-002 @AC-002
Feature: Identidade derivada da configuração

  Scenario: Prompt exibido pelo demonstrativo reflete a base configurada
    Given uma configuração cujo projeto.nome e projeto.descricao são arbitrários
    When o operador executa o demonstrativo
    Then o prompt exibido cita o nome e a descrição configurados
    And nenhum identificador de outro cliente aparece no prompt
```

#### AC-003 — Pergunta padrão vem da primeira consulta do gabarito

**Cobre**: US-001, FR-002, NFR-003

```gherkin
@US-001 @FR-002 @NFR-003 @AC-003
Feature: Pergunta padrão coerente com a base

  Scenario: Demonstrativo sem argumento usa o gabarito da base
    Given uma configuração cujo gabarito declara uma pergunta como primeira consulta
    When o operador executa o demonstrativo sem informar pergunta
    Then a pergunta usada é a primeira consulta do gabarito
```

#### AC-004 — Gabarito ausente degrada com aviso

**Cobre**: FR-002, FR-003

```gherkin
@FR-002 @FR-003 @AC-004
Feature: Degradação proporcional ao risco

  Scenario: Demonstrativo sem gabarito no caminho declarado
    Given uma configuração cujo caminho de gabarito não existe
    When o operador executa o demonstrativo sem informar pergunta
    Then uma pergunta neutra é usada
    And o operador é avisado de que a pergunta não veio do gabarito
    And o comando não falha
```

#### AC-005 — Descrição vazia degrada com aviso

**Cobre**: US-001, FR-001, FR-003

```gherkin
@US-001 @FR-001 @FR-003 @AC-005
Feature: Degradação proporcional ao risco

  Scenario: Configuração sem descrição do projeto
    Given uma configuração cujo projeto.descricao está vazio
    When o operador inicia o chat
    Then uma descrição neutra é usada no prompt
    And o operador é avisado de que a descrição não veio da configuração
```

#### AC-006 — Nome do projeto ausente encerra a execução

**Cobre**: FR-003, FR-005

```gherkin
@FR-003 @FR-005 @AC-006
Feature: Degradação proporcional ao risco

  Scenario: Configuração sem nome do projeto
    Given uma configuração sem projeto.nome
    When o operador executa qualquer uma das três ferramentas
    Then a execução encerra com mensagem clara sobre a chave ausente
    And nenhuma identidade de cliente é assumida como substituta
```

#### AC-007 — Configuração de uso fora do controle de versão

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-007
Feature: Repositório sem configuração de cliente

  Scenario: Índice do Git não contém a configuração de uso
    Given o repositório após a entrega
    When se inspeciona o índice do Git
    Then config.yaml não está versionado
    And o arquivo permanece disponível em disco para quem já o utiliza
```

#### AC-008 — Exemplo de configuração versionado e neutro

**Cobre**: US-002, FR-004

```gherkin
@US-002 @FR-004 @AC-008
Feature: Repositório sem configuração de cliente

  Scenario: Exemplo publicado não endereça destino real
    Given o repositório após a entrega
    When se inspeciona o exemplo de configuração versionado
    Then ele existe no índice do Git
    And não contém identificador de cliente
    And não contém nome de coleção nem namespace de destino real
```

#### AC-009 — Clone novo consegue configurar pelo caminho documentado

**Cobre**: US-002, FR-004, FR-006

```gherkin
@US-002 @FR-004 @FR-006 @AC-009
Feature: Repositório sem configuração de cliente

  Scenario: Procedimento de primeira configuração está publicado
    Given um clone novo do repositório, sem configuração de uso
    When a pessoa segue a documentação de operação
    Then existe um passo explícito de copiar o exemplo para a configuração de uso
    And o passo aparece junto do procedimento equivalente já existente para segredos
```

#### AC-010 — Guarda estática não encontra identificador de cliente

**Cobre**: US-003, FR-005, NFR-003

```gherkin
@US-003 @FR-005 @NFR-003 @AC-010
Feature: Guarda contra reincidência

  Scenario: Ferramentas operacionais livres de identidade escrita
    Given as três ferramentas operacionais
    When a guarda estática varre seus textos
    Then nenhum identificador de cliente conhecido é encontrado
    And a varredura alcança nome próprio e conteúdo de domínio
```

#### AC-011 — Guarda positiva reprova hardcode reintroduzido

**Cobre**: US-003, FR-005, NFR-002

```gherkin
@US-003 @FR-005 @NFR-002 @AC-011
Feature: Guarda contra reincidência

  Scenario: Identidade fixa substitui a derivação
    Given uma ferramenta cuja identidade deixou de ser lida da configuração
    When a guarda positiva monta a ferramenta com uma configuração fictícia
    Then a guarda reprova porque a saída não contém os valores daquela configuração
    And a reprovação independe do nome do cliente reintroduzido
```

#### AC-012 — Entrega não altera dependências nem fronteiras

**Cobre**: US-003, NFR-001, NFR-002, NFR-003

```gherkin
@US-003 @NFR-001 @NFR-002 @NFR-003 @AC-012
Feature: Entrega contida

  Scenario: Fronteiras e dependências permanecem como estão
    Given o repositório após a entrega
    When a suíte completa e a inspeção de dependências são executadas
    Then nenhuma dependência foi acrescentada ao manifesto
    And a fronteira de providers permanece verde, com a exceção já rastreada intacta
    And as duas guardas de regressão estão presentes e verdes
```

#### AC-013 — Documentação deixa de declarar a limitação

**Cobre**: FR-006, NFR-002

```gherkin
@FR-006 @NFR-002 @AC-013
Feature: Documentação coerente com o sistema

  Scenario: Limitação documentada não sobrevive à correção
    Given a documentação de operação, que declara a identidade fixa como limitação conhecida
    When a entrega é concluída
    Then a declaração da limitação não permanece publicada
    And a documentação descreve a identidade como derivada da configuração
```

#### AC-014 — Varredura documental acompanha a troca de arquivo

**Cobre**: FR-006, NFR-001

```gherkin
@FR-006 @NFR-001 @AC-014
Feature: Documentação coerente com o sistema

  Scenario: Varredura de material publicado alcança o exemplo
    Given a varredura de material publicado, que hoje inclui a configuração de uso
    When a configuração de uso sai do controle de versão
    Then a varredura passa a alcançar o exemplo versionado
    And nenhum material publicado deixa de ser verificado
```

### 7. Requisitos

#### Funcionais

- **FR-001**: O sistema deve derivar a identidade apresentada e a instrução enviada ao modelo de `projeto.nome` e `projeto.descricao` da configuração carregada, em `chat.py` e `demo_rag.py`, sem criar chave nova.
- **FR-002**: O sistema deve usar, como pergunta padrão de `demo_rag.py`, a primeira consulta declarada no gabarito indicado por `caminhos.consultas_referencia`.
- **FR-003**: O sistema deve exigir `projeto.nome` e encerrar com mensagem clara quando ele faltar; deve substituir `projeto.descricao` ausente e gabarito inexistente por texto neutro, avisando o operador em cada caso e sem interromper a execução.
- **FR-004**: O repositório deve versionar `config.example.yaml` sem identificador de cliente e sem endereçamento de destino real, e deve manter `config.yaml` fora do índice do Git, preservando o arquivo em disco.
- **FR-005**: O sistema não deve conter identificador de cliente escrito em `chat.py`, `demo_rag.py` e `search.py`, considerando nome próprio e conteúdo de domínio, inclusive em docstrings e valores padrão.
- **FR-006**: A documentação de operação deve descrever a identidade como derivada da configuração, publicar o passo de cópia do exemplo, e a varredura de material publicado deve alcançar o exemplo versionado.

#### Não funcionais

- **NFR-001**: A entrega não acrescenta dependência ao projeto. **Verificação**: inspeção do manifesto e do lockfile, exigindo ausência de dependência nova.
- **NFR-002**: A fronteira de providers permanece intacta, com a exceção de `ChatOpenAI` em `chat.py` inalterada e ainda rastreada pelo BACKLOG-0010. **Verificação**: a suíte de fronteira estática existente permanece verde.
- **NFR-003**: A guarda contra reincidência é executável e alcança identidade ainda não catalogada. **Verificação**: caso positivo que monta a ferramenta com configuração fictícia e exige na saída os valores dessa configuração, somado à lista de proibições estendida.

#### Erros e casos-limite

- `projeto.nome` ausente ou vazio: encerra com mensagem clara, em qualquer das três ferramentas.
- `projeto.descricao` ausente ou vazia: descrição neutra e aviso ao operador.
- Gabarito inexistente no caminho declarado: pergunta neutra e aviso, sem falha.
- Gabarito presente porém vazio ou malformado: mesmo tratamento do inexistente. A validação estrita do gabarito pertence a `validate.py` e não é replicada no demonstrativo.
- `caminhos.consultas_referencia` não declarado: tratado como gabarito inexistente.

## Ato II — Projetar e provar

### 8. Plano técnico

#### Contexto existente

As três ferramentas já leem a configuração para montar o escopo de busca: `chat.py:69`, `demo_rag.py:55` e `search.py:55` chamam `build_scope(cfg["projeto"]["nome"], args.tenant)`. O acoplamento sobrevive apenas na camada de apresentação e de geração, o que torna a correção local. `src/config.py` centraliza o carregamento e não precisa mudar.

#### Arquitetura e módulos

A identidade da base passa a ser um valor derivado da configuração, obtido por uma função pequena e compartilhada pelas ferramentas, em vez de literal em cada arquivo. Ela devolve nome e descrição já resolvidos, aplicando a degradação de FR-003 e emitindo o aviso correspondente. A função vive na camada de aplicação, junto do que hoje traduz configuração para os contratos, e não em `src/providers/`, que permanece restrito a adapters.

#### Migrations

Não aplicável. A fatia não possui persistência relacional; o componente não mantém schema próprio, conforme `.specsfy/DATABASE.md`.

#### Models

Não aplicável. A identidade derivada é um valor de leitura, sem ciclo de vida nem persistência.

#### Controllers e casos de uso

`chat.py` e `demo_rag.py` passam a compor a mensagem de abertura e o prompt a partir da identidade derivada. `demo_rag.py` resolve a pergunta padrão pelo gabarito. `search.py` altera apenas o docstring, por não montar prompt.

#### Views e experiência

Não aplicável. A entrega é operada por linha de comando e não possui superfície gráfica.

#### Queries e repositórios

Não aplicável. Nenhuma consulta ao banco vetorial muda; o escopo de busca já é derivado da configuração e permanece como está.

#### Jobs e processamento assíncrono

Não aplicável. A execução é síncrona e curta.

#### Estrutura de arquivos

```text
specs/completed/0005-remover-hardcodes-cliente/
  spec.md
chat.py
demo_rag.py
search.py
config.example.yaml
.gitignore
src/
  indexing.py
tests/
  test_client_neutrality.py
  test_docs_safety.py
GUIA_DE_USO.md
README.md
```

### 9. Modelo de dados

#### Entidades

Nenhuma entidade persistente é criada ou alterada. A fatia consome duas chaves já existentes da configuração, `projeto.nome` e `projeto.descricao`, e o gabarito de consultas já declarado por `caminhos.consultas_referencia`, criado pela SPEC-0004.

#### Estados e transições

Não aplicável. Nenhum registro muda de estado nesta fatia.

#### Migração e retenção

Não aplicável quanto a dados. Quanto a arquivos, `config.yaml` sai do índice do Git preservando a cópia em disco, e o exemplo versionado passa a ser a referência para uma configuração nova.

### 10. Interfaces e contratos

#### Interface para pessoas

Não. As três ferramentas são executadas por linha de comando por operadores do pipeline. A entrega altera texto exibido no terminal, valor padrão de argumento e configuração; não existe tela, rota, formulário, componente ou navegação envolvida, e o repositório não possui camada de interface, conforme `INTERFACE.md`.

#### Stack e convenções de interface

Não aplicável, pela ausência de interface para pessoas.

#### Telas e responsabilidades

Não aplicável, pela ausência de interface para pessoas.

#### Fluxo de informação e navegação

Não aplicável, pela ausência de interface para pessoas.

#### Menus e navegação principal

Não aplicável, pela ausência de interface para pessoas.

#### Formulários e ações

Não aplicável, pela ausência de interface para pessoas.

#### Composição e disposição

Não aplicável, pela ausência de interface para pessoas.

#### Blocos React e componentes selecionados

Não aplicável. O repositório não usa React e a fatia não introduz biblioteca de interface.

#### Estados e acessibilidade

Não aplicável quanto a tela. A saída de terminal preserva o comportamento atual, incluindo a forçagem de UTF-8 já presente em `chat.py` e `demo_rag.py`.

#### Contrato CRUD

Não aplicável. A fatia não administra registros.

#### Revisão visual durante o desenvolvimento

Não aplicável. Sem superfície gráfica, cada tarefa registra `VISUAL` como não aplicável com o motivo concreto.

#### APIs expostas

Nenhuma. A fatia não expõe endpoint.

#### APIs externas utilizadas

Nenhuma nova. `chat.py` continua usando o serviço de LLM já configurado, sem alteração de contrato, autenticação ou chamada.

#### Documentação das APIs consultadas

Nenhuma documentação externa foi consultada.

#### Eventos e outros contratos

O contrato relevante é a configuração: `projeto.nome` obrigatório, `projeto.descricao` opcional com degradação, e `caminhos.consultas_referencia` opcional para o demonstrativo.

### 11. Estratégia TDD

- **Unidade**: resolução da identidade a partir da configuração, cobrindo valor presente, valor vazio e chave ausente; resolução da pergunta padrão a partir do gabarito, cobrindo gabarito presente, ausente e malformado.
- **Integração/contrato**: composição da mensagem de abertura e do prompt nas ferramentas, com configuração fictícia, verificando que os valores dessa configuração aparecem na saída.
- **BDD/aceite**: os quatorze cenários da seção 6 informam casos Pytest próprios; não criar arquivos `.feature`.
- **Runner TDD**: Pytest, já adotado pelo projeto.
- **Estrutura de repositório**: os casos de AC-007 e AC-008 consultam o índice do Git por `git ls-files`, executado como subprocesso local, e conferem também a entrada correspondente no `.gitignore`. A dupla verificação evita um caso que passe por vacuidade em uma cópia sem `.git`; nessa situação o caso falha com mensagem explícita em vez de ser pulado, porque o gate de entrega não admite teste pulado.
- **E2E**: não aplicável; as ferramentas dependem de destino remoto e de modelo, e o comportamento sob prova é a composição do texto, verificável sem rede.
- **Verificação manual**: nenhuma inevitável. A saída de `config.yaml` do índice do Git é verificável por inspeção do próprio índice, sem execução remota.

#### Evidência RED-GREEN-REFACTOR

| IDs | BDD de referência | Teste TDD informado pelo BDD | RED observado | GREEN observado | Refactor/regressão |
| --- | --- | --- | --- | --- | --- |
| AC-001 a AC-014 | os quatorze cenários na seção 6 | `tests/test_client_neutrality.py`, um caso por AC com marcador `SPECSFY:` próprio | RED em 2026-09-02: `uv run pytest tests/test_client_neutrality.py` → 14 failed in 0.52s, todas por comportamento ausente (AssertionError), nenhuma por sintaxe, fixture, importação ou ambiente; suíte completa em 14 failed, 180 passed, sem regressão | GREEN em 2026-09-02 — T015 a T021: `uv run pytest tests/test_docs_safety.py tests/test_client_neutrality.py` → `19 passed`, incluindo os quatorze AC próprios | Refactors: import tardio evita ciclo; UTF-8 sem efeito colateral no import; argumento omitido distinguido por `None`; validação de identidade compartilhada; exemplo e docs neutros; varredura acompanha somente material publicado; regressão final permanece em T024 |

### 12. Plano de testes e rastreabilidade

| Requisito | Cenários BDD | Nível | Arquivo/comando esperado | Evidência |
| --- | --- | --- | --- | --- |
| US-001 | AC-001, AC-002, AC-003, AC-005 | Contrato/CLI | `pytest tests/test_client_neutrality.py` | T015–T017: 4/4 cenários verdes nos recortes focais |
| US-002 | AC-007, AC-008, AC-009 | Estrutura/repositório | `pytest tests/test_client_neutrality.py` | T019–T020: 3/3 cenários verdes |
| US-003 | AC-010, AC-011, AC-012 | Guarda estática e positiva | `pytest tests/test_client_neutrality.py` | T018/T024: 3/3 cenários verdes; suíte completa com 194 testes aprovados |
| FR-001 | AC-001, AC-002, AC-005 | Unidade/contrato | `pytest tests/test_client_neutrality.py` | T015–T017: 3/3 cenários verdes nos recortes focais |
| FR-002 | AC-002, AC-003, AC-004 | Unidade | `pytest tests/test_client_neutrality.py` | T015 e T017: 3/3 cenários verdes nos recortes focais |
| FR-003 | AC-004, AC-005, AC-006 | Unidade | `pytest tests/test_client_neutrality.py` | T015: 3/3 cenários verdes (`3 passed`) |
| FR-004 | AC-007, AC-008, AC-009 | Estrutura/repositório | `pytest tests/test_client_neutrality.py` | T019–T020: 3/3 cenários verdes |
| FR-005 | AC-006, AC-010, AC-011 | Guarda estática | `pytest tests/test_client_neutrality.py` | T015 e T018: 3/3 cenários verdes nos recortes focais |
| FR-006 | AC-009, AC-013, AC-014 | Documental | `pytest tests/test_client_neutrality.py tests/test_docs_safety.py` | T020–T021: 3/3 cenários verdes; `19 passed` na suíte combinada |
| NFR-001 | AC-001, AC-012, AC-014 | Dependências | `pytest tests/test_client_neutrality.py` | T016/T021/T024: 3/3 cenários verdes; dependências inalteradas |
| NFR-002 | AC-011, AC-012, AC-013 | Arquitetura | `pytest tests/test_provider_boundaries.py` | T016/T018/T020/T024: 3/3 cenários e fronteira verdes |
| NFR-003 | AC-003, AC-010, AC-012 | Guarda positiva | `pytest tests/test_client_neutrality.py` | T017/T018/T024: 3/3 cenários verdes |

### 13. Validações

#### Gate do Ato I — Definição

- **Resultado**: READY — Passed em 2026-09-02
- **Comando**: `node .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs specs/planned/0005-remover-hardcodes-cliente/spec.md`; `node .agents/skills/specsfy-03-specify/scripts/load_research.mjs specs/planned/0005-remover-hardcodes-cliente/spec.md`; `node .agents/skills/specsfy-04-validate/scripts/review_findings.mjs specs/planned/0005-remover-hardcodes-cliente/spec.md --root .`
- **Achados**: estrutura `READY` no validador estrito e research `PASSED` com um artefato indexado e cinco verificações locais. Contagem: 3 US, 6 FR, 3 NFR, 14 AC e 8 DEC. Cobertura conferida por varredura dos campos `**Cobre**`: cada história, requisito funcional e requisito não funcional possui ao menos três cenários distintos, sem identificador coberto que não esteja declarado. Três achados foram abertos nas lentes e corrigidos antes da aprovação; nenhum `P1 Open` permanece.
- **FIND-SEC-001** [P2] [Resolved] Retirar `config.yaml` do índice do Git não remove os valores do histórico — Refs: FR-004 — Evidence: config.yaml:132 — Effect: o resultado desejado poderia ser lido como remoção do endereçamento do repositório, quando `collection_name` e `namespace` continuam recuperáveis em cinco commits anteriores, incluindo o inicial — Suggestion: resolvido declarando o limite em `Fora de escopo` e o risco de leitura equivocada na seção 16, e registrando que nenhuma credencial está envolvida porque `.env` nunca foi versionado.
- **FIND-ARCH-001** [P2] [Resolved] A Definition of Done não citava `.specsfy/STACK.md`, embora a fatia altere o arquivo estrutural de configuração — Refs: FR-004, FR-006 — Evidence: .specsfy/STACK.md:18 — Effect: o inventário de stack continuaria descrevendo apenas `config.yaml`, que deixa de ser versionado, e a documentação divergiria do repositório — Suggestion: resolvido acrescentando à Definition of Done o item que exige o registro do par `config.example.yaml` versionado e `config.yaml` local.
- **FIND-PROD-001** [P3] [Resolved] Os cenários que inspecionam o índice do Git não declaravam mecanismo de verificação — Refs: FR-004 — Evidence: specs/completed/0005-remover-hardcodes-cliente/spec.md:1 — Effect: nenhum teste do repositório executa `git` hoje, e um caso mal desenhado passaria por vacuidade em uma cópia sem `.git`, aprovando a fatia sem prova — Suggestion: resolvido declarando na seção 11 a consulta por `git ls-files` somada à conferência do `.gitignore`, com falha explícita, e não teste pulado, quando o diretório de controle de versão não existir.
- Findings especializados, quando aplicáveis, seguem `FIND-PROD|ARCH|SEC-NNN`,
  severidade `P1|P2|P3`, estado `Open|Resolved|Accepted`, refs e evidência.

#### Gate do Ato II — Plano

- **Resultado**: READY — Passed em 2026-09-02
- **Comando**: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/planned/0005-remover-hardcodes-cliente/spec.md`; `uv run pytest tests/test_client_neutrality.py`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/planned/0005-remover-hardcodes-cliente/spec.md .`; replanejamento focal em 2026-09-02: `node .agents/skills/specsfy-05-tasks/scripts/validate_tasks.mjs specs/in-progress/0005-remover-hardcodes-cliente/spec.md --allow-draft`.
- **Achados**: plano com 25 tarefas — 15 `[TEST]`, 6 `[CODE]` e 4 `[DOC]` — cobrindo 26/26 IDs da especificação, sem tarefa órfã, dependência inválida ou ciclo. Os quatorze predecessores TDD estão concluídos com RED válido: `14 failed in 0.52s`, todas por comportamento ausente (`AssertionError`) e nenhuma por sintaxe, fixture, importação ou ambiente; a suíte completa ficou em `14 failed, 180 passed`, sem regressão sobre as fatias anteriores. A auditoria de rastreabilidade confirmou 26/26 IDs cobertos; o resultado `GAPS` decorre apenas de marcadores das SPEC-0003 e SPEC-0004 presentes em quinze arquivos de teste anteriores, nenhum deles emitido por `tests/test_client_neutrality.py`, que declara somente IDs desta fatia. Durante T015, o plano foi reaberto e aprovado novamente para substituir comandos que exigiam GREEN prematuro da suíte inteira por recortes focais compatíveis com as dependências de T015 a T019; após a primeira execução, AC-003 foi corretamente deslocado para o GREEN de T017 porque seu teste também verifica a remoção do literal em `demo_rag.py`. T024 continua responsável pela regressão completa.
- **FIND-PROD-002** [P3] [Resolved] T024 previa `uv run ruff check .`, mas Ruff não está declarado em `pyproject.toml` nem instalado no ambiente — Refs: NFR-001 — Evidence: pyproject.toml:22 — Effect: a tarefa de regressão falharia por ferramenta ausente, e instalar Ruff como dependência violaria NFR-001 — Suggestion: resolvido trocando o comando por `uvx ruff check .`, que executa a ferramenta de forma efêmera sem alterar o manifesto.

#### Gate do Ato III — Entrega

- **Resultado**: READY — Passed em 2026-09-02
- **Comando**: `uvx ruff check .`; `node .agents/skills/specsfy-setup/scripts/check_database_safety.mjs --project . --command "uv run pytest"`; `uv run pytest`; `node .agents/skills/specsfy-06-tdd-bdd/scripts/check_traceability.mjs specs/completed/0005-remover-hardcodes-cliente/spec.md <raiz-temporária-com-test_client_neutrality.py>`; `node .agents/skills/specsfy-documentator/scripts/build_documentation.mjs --project . --check`; `node .agents/skills/specsfy-setup/scripts/monitor_context.mjs --project . --check --paths <caminhos-da-entrega>`.
- **Achados**: 25/25 tarefas e 150/150 itens concluídos; Ruff completo `All checks passed`; proteção do banco `SAFE`; Pytest `194 passed`, nenhum teste pulado; rastreabilidade focal `26/26`, `RESULTADO: OK`; documentação em dia e monitor `CURRENT`. A varredura global também cobre `26/26`, mas retorna `GAPS` somente pelos marcadores das SPEC-0003 e SPEC-0004 em seus próprios arquivos, já registrados no Plan Gate e ausentes de `tests/test_client_neutrality.py`. Todos os AC, FR, NFR e itens da Definition of Done possuem evidência atual.

### 14. Tarefas

Formato:
`- <checkbox> TNNN [P?] [TIPO] [US-NNN?] Ação com caminho — Refs: IDs — Depends: IDs|none`

Checklist obrigatório por tarefa, na ordem `PREP`, `EXECUTE`, `VERIFY`,
`VISUAL`, `EVIDENCE` e `IMPROVE`. Esta fatia não possui superfície gráfica,
portanto cada `VISUAL` registra `Não aplicável` com o motivo concreto.

Runner TDD: Pytest, já adotado pelo repositório. Todos os casos novos ficam em
`tests/test_client_neutrality.py`, conforme a DEC-008, cada um com marcador
`SPECSFY:` próprio. Nenhuma tarefa cria ou executa arquivo `.feature`.

#### Fase 1 — RED TDD informado pelo BDD

- [x] T001 [TEST] [TDD] [US-001] Derivar do AC-001 um caso Pytest falhando em tests/test_client_neutrality.py que monta a abertura e o prompt de chat.py com configuração fictícia — Refs: US-001, FR-001, NFR-001, AC-001 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-001 e fixar a prova como presença dos valores da configuração fictícia na abertura e no prompt do sistema.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: US-001 FR-001 NFR-001 AC-001`, sem rede e sem instanciar o LLM.
  - [x] **VERIFY**: Observar RED por ausência da composição derivada em chat.py.
  - [x] **VISUAL**: Não aplicável — o caso verifica texto de terminal e o repositório não possui camada de interface, conforme a seção 10 e `INTERFACE.md`.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por `src.indexing.resolve_identity` ausente: a abertura e o prompt de chat.py continuam literais. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: a importação das ferramentas restaura `sys.stdout`, porque chat.py troca o stream no import e isso quebraria a captura das demais provas.

- [x] T002 [TEST] [TDD] [US-001] Derivar do AC-002 um caso Pytest falhando em tests/test_client_neutrality.py que confere o prompt exibido por demo_rag.py — Refs: US-001, FR-001, FR-002, AC-002 — Depends: none
  - [x] **PREP**: Ler o Gherkin do AC-002 e separar o que é composição do prompt do que é recuperação, que não muda nesta fatia.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: US-001 FR-001 FR-002 AC-002`, exigindo nome e descrição fictícios no texto montado.
  - [x] **VERIFY**: Observar RED por literal de cliente ainda presente no prompt de demo_rag.py.
  - [x] **VISUAL**: Não aplicável — a saída sob prova é texto de terminal, sem superfície gráfica no repositório.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por `src.indexing.resolve_identity` ausente: o prompt de demo_rag.py continua literal. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: o caso injeta o contexto pronto, isolando a composição do prompt do fluxo de recuperação, que não muda nesta fatia.

- [x] T003 [TEST] [TDD] [US-001] Derivar do AC-003 um caso Pytest falhando em tests/test_client_neutrality.py que exige a primeira consulta do gabarito como pergunta padrão — Refs: US-001, FR-002, NFR-003, AC-003 — Depends: none
  - [x] **PREP**: Confirmar em `src/validation.py` o formato do gabarito lido por `load_query_cases` e escrever um gabarito temporário no caso.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: US-001 FR-002 NFR-003 AC-003`, sem depender do gabarito real da base.
  - [x] **VERIFY**: Observar RED por `PERGUNTA_PADRAO` continuar literal em demo_rag.py.
  - [x] **VISUAL**: Não aplicável — o caso verifica valor padrão de argumento, sem elemento visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por `src.indexing.resolve_default_question` ausente: `PERGUNTA_PADRAO` continua literal. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: o gabarito do caso é escrito em `tmp_path`, sem depender do gabarito real da base validada pela SPEC-0004.

- [x] T004 [TEST] [TDD] Derivar do AC-004 um caso Pytest falhando em tests/test_client_neutrality.py para gabarito inexistente no caminho declarado — Refs: FR-002, FR-003, AC-004 — Depends: none
  - [x] **PREP**: Fixar as três formas equivalentes do caso-limite: caminho ausente, arquivo inexistente e gabarito vazio ou malformado.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: FR-002 FR-003 AC-004`, exigindo pergunta neutra, aviso ao operador e ausência de exceção.
  - [x] **VERIFY**: Observar RED por não existir resolução da pergunta padrão a partir da configuração.
  - [x] **VISUAL**: Não aplicável — a prova é o aviso em texto e o valor devolvido, sem interface.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por `src.indexing.resolve_default_question` ausente: não há degradação nem aviso para gabarito ilegível. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: as três formas do caso-limite (caminho ausente, arquivo inexistente e gabarito vazio) foram unificadas em um laço, evitando casos equivalentes.

- [x] T005 [TEST] [TDD] [US-001] Derivar do AC-005 um caso Pytest falhando em tests/test_client_neutrality.py para projeto.descricao vazia — Refs: US-001, FR-001, FR-003, AC-005 — Depends: none
  - [x] **PREP**: Fixar o texto neutro esperado e a exigência de aviso, sem tornar o texto configurável nesta fatia.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: US-001 FR-001 FR-003 AC-005`, cobrindo chave ausente e valor vazio.
  - [x] **VERIFY**: Observar RED por chat.py não degradar nem avisar.
  - [x] **VISUAL**: Não aplicável — a degradação é textual e o repositório não possui tela.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por `src.indexing.resolve_identity` ausente: descrição vazia não degrada nem avisa. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: chave ausente e valor vazio ficaram no mesmo caso, por exigirem a mesma degradação.

- [x] T006 [TEST] [TDD] Derivar do AC-006 um caso Pytest falhando em tests/test_client_neutrality.py exigindo encerramento claro sem projeto.nome — Refs: FR-003, FR-005, AC-006 — Depends: none
  - [x] **PREP**: Confirmar que hoje `cfg["projeto"]["nome"]` levanta `KeyError` cru nas três ferramentas e definir a mensagem esperada.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: FR-003 FR-005 AC-006`, exigindo mensagem sobre a chave ausente e nenhuma identidade substituta.
  - [x] **VERIFY**: Observar RED por erro genérico em vez de mensagem clara.
  - [x] **VISUAL**: Não aplicável — o caso verifica mensagem de erro em terminal.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por `src.indexing.resolve_identity` ausente: hoje a ausência de `projeto.nome` levanta KeyError cru. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: o caso exige `ValueError` com a chave citada, fixando um contrato firme em vez de aceitar qualquer exceção.

- [x] T007 [TEST] [TDD] [US-002] Derivar do AC-007 um caso Pytest falhando em tests/test_client_neutrality.py que consulta o índice do Git por config.yaml — Refs: US-002, FR-004, AC-007 — Depends: none
  - [x] **PREP**: Definir a consulta por `git ls-files` como subprocesso local e a falha explícita quando o diretório de controle de versão não existir, conforme a seção 11.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: US-002 FR-004 AC-007`, conferindo também a entrada correspondente no `.gitignore` e a permanência do arquivo em disco.
  - [x] **VERIFY**: Observar RED por config.yaml ainda versionado.
  - [x] **VISUAL**: Não aplicável — a prova é o estado do índice do Git, sem elemento visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por config.yaml ainda constar em `git ls-files`. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: sem diretório de controle de versão o caso falha explicitamente, em vez de ser pulado, porque o gate de entrega não admite teste pulado.

- [x] T008 [TEST] [TDD] [US-002] Derivar do AC-008 um caso Pytest falhando em tests/test_client_neutrality.py que exige config.example.yaml versionado e neutro — Refs: US-002, FR-004, AC-008 — Depends: none
  - [x] **PREP**: Reunir a lista de identificadores de cliente e as chaves de endereçamento remoto que o exemplo não pode conter.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: US-002 FR-004 AC-008`, exigindo presença no índice do Git, ausência de identificador e ausência de coleção ou namespace real.
  - [x] **VERIFY**: Observar RED por config.example.yaml ainda não existir.
  - [x] **VISUAL**: Não aplicável — a prova é o conteúdo de um arquivo YAML versionado.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por config.example.yaml ainda não existir no índice do Git. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: o exemplo é comparado com a configuração real, de modo que a prova não depende de uma lista fixa de valores proibidos.

- [x] T009 [TEST] [TDD] [US-002] Derivar do AC-009 um caso Pytest falhando em tests/test_client_neutrality.py que exige o passo de cópia publicado em README.md — Refs: US-002, FR-004, FR-006, AC-009 — Depends: none
  - [x] **PREP**: Localizar o procedimento equivalente já publicado para segredos e exigir o novo passo junto dele.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: US-002 FR-004 FR-006 AC-009`, verificando a instrução de copiar o exemplo para a configuração de uso.
  - [x] **VERIFY**: Observar RED por README.md não publicar o passo.
  - [x] **VISUAL**: Não aplicável — a prova é texto de documentação em Markdown.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por README.md não publicar o passo de cópia do exemplo. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: a proximidade entre os dois passos é medida por distância de linhas, provando o requisito de que o passo apareça junto do equivalente de segredos.

- [x] T010 [TEST] [TDD] [US-003] Derivar do AC-010 a guarda estática em tests/test_client_neutrality.py sobre chat.py, demo_rag.py e search.py — Refs: US-003, FR-005, NFR-003, AC-010 — Depends: none
  - [x] **PREP**: Estender a lista de `tests/test_validation_boundaries.py` com nome próprio e conteúdo de domínio bancário, cobrindo as oito ocorrências levantadas em R-001.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: US-003 FR-005 NFR-003 AC-010`, varrendo os três arquivos inteiros, docstrings e valores padrão incluídos.
  - [x] **VERIFY**: Observar RED apontando as ocorrências ainda presentes.
  - [x] **VISUAL**: Não aplicável — a varredura lê código-fonte, sem superfície gráfica.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED com sete marcadores em três arquivos: chat.py (c6 bank, c6 empresas, rag c6), demo_rag.py (c6 bank, cheque especial) e search.py (conta pj, cheque especial), cobrindo as oito ocorrências de R-001. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: a varredura é case-insensitive e cobre nome próprio e conteúdo de domínio, alcançando docstrings e valores padrão.

- [x] T011 [TEST] [TDD] [US-003] Derivar do AC-011 a guarda positiva de derivação em tests/test_client_neutrality.py — Refs: US-003, FR-005, NFR-002, AC-011 — Depends: none
  - [x] **PREP**: Definir o discriminador: a composição recebe configuração fictícia e a saída precisa conter aqueles valores, de modo que identidade fixa reprove mesmo com nome ainda não catalogado.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: US-003 FR-005 NFR-002 AC-011`, exercitando a composição derivada e um duplo de identidade fixa que precisa reprovar.
  - [x] **VERIFY**: Observar RED por não existir ponto único de composição derivada.
  - [x] **VISUAL**: Não aplicável — a guarda compara strings compostas, sem elemento visual.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por não existir ponto único de composição derivada para o duplo discriminar. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: o duplo usa um cliente fora da lista de proibições, provando que a reprovação independe do nome reintroduzido.

- [x] T012 [TEST] [TDD] [US-003] Derivar do AC-012 um caso Pytest em tests/test_client_neutrality.py que exige manifesto sem dependência nova e as duas guardas presentes — Refs: US-003, NFR-001, NFR-002, NFR-003, AC-012 — Depends: none
  - [x] **PREP**: Fixar o conjunto atual de dependências de `pyproject.toml` como baseline da comparação.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: US-003 NFR-001 NFR-002 NFR-003 AC-012`, conferindo baseline de dependências e existência das duas guardas.
  - [x] **VERIFY**: Observar RED por as guardas ainda não existirem.
  - [x] **VISUAL**: Não aplicável — a prova é o manifesto e a presença de casos de teste.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por src/indexing.py não expor a derivação, deixando a guarda positiva sem sujeito. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: a baseline de dependências foi extraída do próprio manifesto por tomllib, evitando divergência entre o caso e pyproject.toml.

- [x] T013 [TEST] [TDD] Derivar do AC-013 um caso Pytest falhando em tests/test_client_neutrality.py que reprova a limitação declarada em GUIA_DE_USO.md — Refs: FR-006, NFR-002, AC-013 — Depends: none
  - [x] **PREP**: Localizar em GUIA_DE_USO.md o trecho que declara a identidade fixa como limitação conhecida e definir a asserção sobre sua ausência.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: FR-006 NFR-002 AC-013`, exigindo também a descrição da identidade como derivada da configuração.
  - [x] **VERIFY**: Observar RED por a limitação continuar publicada.
  - [x] **VISUAL**: Não aplicável — a prova é texto de documentação em Markdown.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por GUIA_DE_USO.md ainda declarar a identidade fixa como limitação conhecida. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: a mesma lista de identificadores da guarda estática foi reaproveitada, evitando duas definições do que é conteúdo de cliente.

- [x] T014 [TEST] [TDD] Derivar do AC-014 um caso Pytest falhando em tests/test_client_neutrality.py que exige a varredura publicada alcançando config.example.yaml — Refs: FR-006, NFR-001, AC-014 — Depends: none
  - [x] **PREP**: Confirmar que `tests/test_docs_safety.py` hoje varre config.yaml e que o alvo precisa acompanhar a saída do índice do Git.
  - [x] **EXECUTE**: Escrever o caso com marcador `SPECSFY: FR-006 NFR-001 AC-014`, exigindo config.example.yaml na lista varrida e nenhum material publicado sem verificação.
  - [x] **VERIFY**: Observar RED por a lista ainda citar config.yaml.
  - [x] **VISUAL**: Não aplicável — a prova é a configuração de outro caso de teste.
  - [x] **EVIDENCE**: `uv run pytest tests/test_client_neutrality.py` — RED por tests/test_docs_safety.py ainda varrer config.yaml em vez do exemplo versionado. Registrado na seção 11.
  - [x] **IMPROVE**: Aplicada: o caso também exige que os demais materiais publicados continuem varridos, impedindo que a troca de alvo reduza a cobertura.

#### Fase 2 — US-001 Apontar as ferramentas para outra base sem editar código (P1)

**Objetivo**: mensagens, prompts e pergunta padrão passam a refletir a base configurada.
**Teste independente**: `uv run pytest tests/test_client_neutrality.py` com configuração fictícia mostra nome e descrição arbitrários na abertura e no prompt.

- [x] T015 [CODE] [US-001] Implementar a identidade derivada e a pergunta padrão em src/indexing.py — Refs: US-001, FR-001, FR-002, FR-003, AC-001, AC-002, AC-003, AC-004, AC-005, AC-006 — Depends: T001, T002, T003, T004, T005, T006
  - [x] **PREP**: RED confirmado em 2026-09-02 com `uv run pytest tests/test_client_neutrality.py` (14 falhas esperadas); `docs/` reconstruído e validado; DEC-007 confirmada, mantendo a resolução em `src/indexing.py`, fora de `src/providers/`.
  - [x] **EXECUTE**: `src/indexing.py` passou a expor `BaseIdentity`, `resolve_identity` e `resolve_default_question`, com nome obrigatório, degradação avisada e nenhuma chave ou dependência nova; `docs/` foi reconstruído e validado.
  - [x] **VERIFY**: `uv run pytest tests/test_client_neutrality.py -k 'ac_004 or ac_005 or ac_006'` → `3 passed, 11 deselected`; proteção do banco `SAFE` e monitor focal `CURRENT`.
  - [x] **VISUAL**: Não aplicável — a entrega é uma função de aplicação sem superfície gráfica, conforme a seção 10.
  - [x] **EVIDENCE**: GREEN, arquivo alterado e cobertura de US-001, FR-001, FR-002, FR-003 e AC-004 a AC-006 registrados nas seções 11 e 12; `PROJECT.md` revisado sem impacto material na narrativa.
  - [x] **IMPROVE**: Aplicada — o carregamento de `src.validation.load_query_cases` é tardio, preservando a fronteira compartilhada sem criar ciclo de importação entre validação e indexação.
  <!-- specsfy:evidence {"task":"T015","refs":["US-001","FR-001","FR-002","FR-003","AC-001","AC-002","AC-003","AC-004","AC-005","AC-006"],"files":["src/indexing.py"],"commands":[{"run":"uv run pytest tests/test_client_neutrality.py -k 'ac_004 or ac_005 or ac_006'","exit":0}]} -->

- [x] T016 [P] [CODE] [US-001] Compor abertura e prompt a partir da identidade derivada em chat.py — Refs: US-001, FR-001, FR-003, FR-005, AC-001, AC-005, AC-006 — Depends: T001, T005, T006, T015
  - [x] **PREP**: GREEN de T015 confirmado; `docs/` reconstruído; `tests/test_provider_boundaries.py` confirma `ChatOpenAI` em `chat.py` como a única exceção temporária, sem mudança de fronteira.
  - [x] **EXECUTE**: `chat.py` passou a usar `resolve_identity`, `montar_abertura` e `montar_template_sistema`; o escopo de recuperação e a fronteira de `ChatOpenAI` foram preservados; `docs/` foi reconstruído.
  - [x] **VERIFY**: `uv run pytest tests/test_client_neutrality.py tests/test_provider_boundaries.py -k 'ac_001 or ac_005 or ac_006 or provider'` → `7 passed, 11 deselected`; proteção do banco `SAFE`.
  - [x] **VISUAL**: Não aplicável — a saída é terminal e o repositório não possui camada de interface.
  - [x] **EVIDENCE**: GREEN de AC-001, AC-005 e AC-006, fronteira verde e arquivo alterado registrados nas seções 11 e 12; `PROJECT.md` revisado sem impacto narrativo material.
  - [x] **IMPROVE**: Aplicada — a configuração UTF-8 saiu do import e passou a usar `sys.stdout.reconfigure()` no início de `main()`, preservando o terminal sem fechar streams de captura ou de consumidores.
  <!-- specsfy:evidence {"task":"T016","refs":["US-001","FR-001","FR-003","FR-005","AC-001","AC-005","AC-006"],"files":["chat.py"],"commands":[{"run":"uv run pytest tests/test_client_neutrality.py tests/test_provider_boundaries.py -k 'ac_001 or ac_005 or ac_006 or provider'","exit":0}]} -->

- [x] T017 [P] [CODE] [US-001] Derivar prompt, pergunta padrão e exemplos de uso em demo_rag.py — Refs: US-001, FR-001, FR-002, FR-003, FR-005, AC-002, AC-003, AC-004 — Depends: T002, T003, T004, T015
  - [x] **PREP**: GREEN de T015 e baseline documental confirmados; as três ocorrências de `demo_rag.py` foram localizadas no prompt, em `PERGUNTA_PADRAO` e no exemplo do docstring.
  - [x] **EXECUTE**: `demo_rag.py` passou a compor o prompt pela identidade resolvida, usar a primeira consulta do gabarito quando o argumento é omitido e publicar exemplo neutro; `docs/` foi reconstruído.
  - [x] **VERIFY**: `uv run pytest tests/test_client_neutrality.py -k 'ac_002 or ac_003 or ac_004'` → `3 passed, 11 deselected`; proteção do banco `SAFE`.
  - [x] **VISUAL**: Não aplicável — o demonstrativo imprime texto em terminal, sem tela.
  - [x] **EVIDENCE**: GREEN de AC-002, AC-003 e AC-004, arquivo alterado e cobertura registrados nas seções 11 e 12; `PROJECT.md` revisado sem impacto narrativo material.
  - [x] **IMPROVE**: Aplicada — o parser usa `None` apenas para representar argumento omitido, permitindo distinguir a escolha do gabarito de uma pergunta informada explicitamente.
  <!-- specsfy:evidence {"task":"T017","refs":["US-001","FR-001","FR-002","FR-003","FR-005","AC-002","AC-003","AC-004"],"files":["demo_rag.py"],"commands":[{"run":"uv run pytest tests/test_client_neutrality.py -k 'ac_002 or ac_003 or ac_004'","exit":0}]} -->

- [x] T018 [P] [CODE] [US-001] Neutralizar os exemplos de uso do docstring em search.py — Refs: FR-005, AC-006, AC-010, AC-011 — Depends: T006, T010, T011, T015
  - [x] **PREP**: RED da guarda estática e baseline documental confirmados; `search.py` não monta prompt e apenas apresenta resultados, mas ainda acessava `projeto.nome` diretamente.
  - [x] **EXECUTE**: `search.py` recebeu exemplos neutros e passou a validar a identidade por `resolve_identity` antes de construir o escopo; `docs/` foi reconstruído.
  - [x] **VERIFY**: `uv run pytest tests/test_client_neutrality.py -k 'ac_006 or ac_010 or ac_011'` → `3 passed, 11 deselected`; proteção do banco `SAFE`.
  - [x] **VISUAL**: Não aplicável — a alteração é docstring e mensagem de terminal.
  - [x] **EVIDENCE**: GREEN de AC-006, AC-010 e AC-011, arquivo alterado e cobertura registrados nas seções 11 e 12; monitor focal `CURRENT`.
  - [x] **IMPROVE**: Aplicada — a busca reutiliza a mesma validação de identidade do chat e do demonstrativo, evitando `KeyError` cru e divergência de mensagem.
  <!-- specsfy:evidence {"task":"T018","refs":["FR-005","AC-006","AC-010","AC-011"],"files":["search.py"],"commands":[{"run":"uv run pytest tests/test_client_neutrality.py -k 'ac_006 or ac_010 or ac_011'","exit":0}]} -->

**Checkpoint**: com uma configuração fictícia, as três ferramentas apresentam somente a identidade dessa configuração.

#### Fase 3 — US-002 Não distribuir a configuração de um cliente no repositório (P1)

**Objetivo**: o repositório passa a versionar apenas um exemplo neutro de configuração.
**Teste independente**: `git ls-files` não retorna config.yaml e retorna config.example.yaml sem identificador de cliente.

- [x] T019 [CODE] [US-002] Criar config.example.yaml neutro, retirar config.yaml do índice do Git e registrar a exclusão no .gitignore — Refs: US-002, FR-004, AC-007, AC-008 — Depends: T007, T008, T009
  - [x] **PREP**: RED de T007 e T008 confirmado; `docs/` reconstruído; `config.yaml` conferido no índice e em disco antes da alteração, preservando sua cópia local conforme a seção 16.
  - [x] **EXECUTE**: `config.example.yaml` foi derivado com identidade, caminhos, coleção, índice e namespace neutros; `git rm --cached config.yaml` preservou o arquivo local; `.gitignore` passou a excluí-lo; documentação reconstruída.
  - [x] **VERIFY**: `uv run pytest tests/test_client_neutrality.py -k 'ac_007 or ac_008'` → `2 passed, 12 deselected`; `git ls-files` encontra o exemplo e rejeita `config.yaml`; proteção do banco `SAFE`.
  - [x] **VISUAL**: Não aplicável — a entrega são arquivos de configuração e a lista de exclusão do Git.
  - [x] **EVIDENCE**: GREEN de AC-007 e AC-008, arquivos alterados e cobertura de US-002/FR-004 registrados nas seções 11 e 12; `config.yaml` confirmado em disco.
  - [x] **IMPROVE**: Aplicada — o exemplo preserva os comentários operacionais completos, mas usa valores neutros também para caminhos, índice e frontmatter de exemplo, reduzindo risco de cópia parcial de dados reais.
  <!-- specsfy:evidence {"task":"T019","refs":["US-002","FR-004","AC-007","AC-008"],"files":["config.example.yaml",".gitignore"],"commands":[{"run":"uv run pytest tests/test_client_neutrality.py -k 'ac_007 or ac_008'","exit":0}]} -->

- [x] T020 [DOC] [US-002] Publicar o passo de cópia da configuração e retirar a limitação declarada em README.md e GUIA_DE_USO.md — Refs: US-002, FR-004, FR-006, NFR-002, AC-009, AC-013 — Depends: T009, T013, T019
  - [x] **PREP**: O passo de `.env.example` foi localizado em `README.md:39–41`, e a limitação de identidade fixa em `GUIA_DE_USO.md:576`; os exemplos de cliente alcançados pela mesma guarda também foram inventariados no guia.
  - [x] **EXECUTE**: `README.md` publica a cópia de `config.example.yaml` junto de `.env.example`; `GUIA_DE_USO.md` descreve a identidade derivada e usa exemplos neutros no procedimento inteiro.
  - [x] **VERIFY**: `uv run pytest tests/test_client_neutrality.py tests/test_docs_safety.py` → `19 passed`; proteção do banco `SAFE`.
  - [x] **VISUAL**: Não aplicável — a entrega é documentação em Markdown, sem superfície gráfica.
  - [x] **EVIDENCE**: AC-009 e AC-013 verdes; passos de cópia e identidade derivada registrados em `README.md` e `GUIA_DE_USO.md`, com cobertura atualizada na seção 12.
  - [x] **IMPROVE**: Aplicada — o procedimento cria primeiro a configuração local e depois o `.env`, deixando identidade/destino separados de credenciais desde a primeira execução.

**Checkpoint**: um clone novo segue a documentação, copia o exemplo e configura a própria base sem receber dados de cliente.

#### Fase 4 — US-003 Impedir que o acoplamento retorne (P1)

**Objetivo**: duas guardas executáveis sustentam a neutralidade, inclusive para cliente ainda inexistente.
**Teste independente**: reintroduzir identidade fixa em qualquer das três ferramentas faz a suíte reprovar.

- [x] T021 [CODE] [US-003] Acompanhar a troca de arquivo na varredura de material publicado em tests/test_docs_safety.py — Refs: FR-006, NFR-001, AC-014 — Depends: T009, T013, T014, T019
  - [x] **PREP**: RED de T014 reproduzido após T020; baseline documental reconstruída; `git ls-files` confirmou que `config.yaml` saiu do índice em T019 e o exemplo entrou.
  - [x] **EXECUTE**: `tests/test_docs_safety.py` passou a varrer `config.example.yaml` e manteve os três demais materiais publicados; `docs/` foi reconstruído.
  - [x] **VERIFY**: `uv run pytest tests/test_docs_safety.py tests/test_client_neutrality.py` → `19 passed`; proteção do banco `SAFE` e monitor focal `CURRENT`.
  - [x] **VISUAL**: Não aplicável — a alteração é a lista de arquivos varridos por um teste.
  - [x] **EVIDENCE**: AC-014 verde, arquivo alterado e cobertura de FR-006/NFR-001 registrados nas seções 11 e 12.
  - [x] **IMPROVE**: Aplicada — a troca foi restrita ao arquivo que deixou de ser publicado; README, guia e contexto técnico permanecem sob a mesma guarda.
  <!-- specsfy:evidence {"task":"T021","refs":["FR-006","NFR-001","AC-014"],"files":["tests/test_docs_safety.py"],"commands":[{"run":"uv run pytest tests/test_docs_safety.py tests/test_client_neutrality.py","exit":0}]} -->

- [x] T022 [DOC] [US-003] Registrar a neutralidade de cliente nas ferramentas operacionais em .specsfy/RULES.md — Refs: FR-005, NFR-003, AC-010, AC-011 — Depends: T018, T021
  - [x] **PREP**: `$specsfy-aux-rules` carregada; a convenção está confirmada por FR-005 e pela SPEC-0005 aprovada, sem necessidade de repetir a pergunta à pessoa responsável.
  - [x] **EXECUTE**: Regra acrescentada em `Código e qualidade`, citando as três ferramentas, a derivação por configuração e as guardas de `tests/test_client_neutrality.py`; nenhuma regra existente foi removida ou reescrita.
  - [x] **VERIFY**: Diff focal conferido e monitor de contexto executado com resultado `CURRENT`.
  - [x] **VISUAL**: Não aplicável — a entrega é documento de regras em Markdown.
  - [x] **EVIDENCE**: `add_rule.mjs` atualizou `.specsfy/RULES.md`; FR-005, NFR-003, AC-010 e AC-011 permanecem verdes na suíte combinada registrada na seção 12.
  - [x] **IMPROVE**: Aplicada — caminhos e chaves de configuração receberam formatação de código, tornando a regra inequívoca e diretamente verificável.

**Checkpoint**: a guarda positiva reprova identidade fixa mesmo quando o nome não está na lista de proibições.

#### Fase final — Qualidade

- [x] T023 [DOC] Registrar o par config.example.yaml versionado e config.yaml local em .specsfy/STACK.md — Refs: FR-004, FR-006, AC-008, AC-009 — Depends: T019, T020
  - [x] **PREP**: `$specsfy-aux-stack` carregada; as quatro linhas do inventário que citavam somente `config.yaml` foram localizadas, junto da introdução das chaves da validação.
  - [x] **EXECUTE**: O inventário agora distingue `config.example.yaml` neutro/versionado de `config.yaml` local/ignorado, preservando integralmente as decisões e observações humanas.
  - [x] **VERIFY**: `update_stack.mjs` executado e monitor de contexto focal confirmado como `CURRENT`.
  - [x] **VISUAL**: Não aplicável — a entrega é inventário técnico em Markdown.
  - [x] **EVIDENCE**: `.specsfy/STACK.md` atualizado com fontes executáveis para FR-004, FR-006, AC-008 e AC-009; nenhuma tecnologia ou dependência foi acrescentada.
  - [x] **IMPROVE**: Aplicada — embeddings e bancos vetoriais também passaram a citar explicitamente o par versionado/local, evitando evidência ambígua fora da linha genérica de configuração.

- [x] T024 [TEST] Executar regressão completa e rastreabilidade sobre tests/test_client_neutrality.py e a suíte — Refs: US-001, US-002, US-003, FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, NFR-001, NFR-002, NFR-003, AC-012 — Depends: T015, T016, T017, T018, T019, T020, T021, T022, T023
  - [x] **PREP**: Reunidos `uvx ruff check .`, `uv run pytest`, `tests/test_provider_boundaries.py` dentro da suíte e `check_traceability.mjs`; manifesto e lockfile serão comparados ao estado anterior pela guarda AC-012.
  - [x] **EXECUTE**: `uvx ruff check .`, `uv run pytest` e rastreabilidade global/focal executados; Ruff permaneceu efêmero e nenhuma dependência foi acrescentada.
  - [x] **VERIFY**: Ruff completo `All checks passed`; Pytest `194 passed` sem skips; rastreabilidade focal `26/26`, `OK`; guarda AC-012 confirmou o conjunto original de dependências.
  - [x] **VISUAL**: Não aplicável — nenhuma superfície gráfica foi criada ou alterada nesta fatia.
  - [x] **EVIDENCE**: Contagens, comandos, resultado e distinção entre rastreabilidade focal verde e marcadores globais de specs anteriores registrados nas seções 11, 12 e 13; monitor `CURRENT` após reconstrução documental.
  - [x] **IMPROVE**: Aplicada — `.agents` vendorizado foi excluído do Ruff, e o baseline do código do projeto foi corrigido mecanicamente; imports, modos executáveis sem shebang, `noqa` justificados e um valor não usado deixaram o gate realmente verde sem nova dependência.

- [x] T025 [DOC] Reconstruir docs/ e revisar PROJECT.md ao fechar a fatia — Refs: FR-006, NFR-001, AC-012, AC-013 — Depends: T024
  - [x] **PREP**: GREEN de T024 confirmado; caminhos de aplicação, configuração, documentação, regras, stack, testes e fonte normativa listados pelo diff e pelo monitor.
  - [x] **EXECUTE**: `$specsfy-documentator` reconstruiu `docs/` e `.specsfy/PACKAGES.md`; `PROJECT.md` passou a registrar identidade derivada e o par `config.example.yaml` versionado/`config.yaml` local.
  - [x] **VERIFY**: `build_documentation.mjs --check` passou e o monitor final retornou `CURRENT`.
  - [x] **VISUAL**: Não aplicável — a entrega é documentação projetada do código, sem interface.
  - [x] **EVIDENCE**: Comandos e arquivos atualizados registrados; a mudança material de procedimento e capacidade foi incorporada em `PROJECT.md`, sem criar documentação paralela.
  - [x] **IMPROVE**: Aplicada — a narrativa técnica agora diferencia explicitamente o exemplo distribuído da configuração operacional local, alinhando projeto, stack e guia.

### 15. Ordem de execução

- Caminho crítico: T001 a T014 (RED) → T015 → T016, T017, T018 → T019 → T020 → T021 → T022, T023 → T024 → T025.
- Tarefas paralelas: T016, T017 e T018 depois de T015, por tocarem arquivos distintos sem estado compartilhado. T001 a T014 não são paralelas entre si porque escrevem no mesmo `tests/test_client_neutrality.py`.
- Estratégia de MVP: US-001 sozinha já entrega valor demonstrável, porque as três ferramentas passam a refletir a base configurada antes de a configuração sair do controle de versão. US-002 e US-003 fecham o risco de distribuição e o de reincidência.

## Ato III — Entregar e validar

### 16. Dependências, riscos e suposições

#### Dependências

- Gabarito criado pela SPEC-0004 em `caminhos.consultas_referencia`, insumo da pergunta padrão. Já existe.
- Lista de identificadores de `tests/test_validation_boundaries.py`, precedente estendido nesta fatia. Já existe.
- Nenhuma dependência externa, de rede ou de credencial.

#### Riscos

- **Risco de procedimento**: a saída de `config.yaml` do índice muda o passo inicial de quem clona o repositório. Mitigado documentando a cópia do exemplo junto do procedimento equivalente já existente para segredos, e verificado por AC-009.
- **Risco de cobertura**: uma lista de proibições alcança apenas o identificador registrado nela. Mitigado pela guarda positiva de derivação, que independe do nome, conforme NFR-003 e AC-011.
- **Risco de escopo**: `chat.py` também é alvo do BACKLOG-0010. Mitigado por NFR-002, que exige a fronteira e a exceção de `ChatOpenAI` inalteradas.
- **Risco de leitura equivocada**: alguém pode concluir que o endereçamento do
  destino saiu do repositório. Ele sai do estado atual, não do histórico.
  Mitigado pela declaração explícita em `Fora de escopo` e por FR-004, que fala
  do índice do Git e não do histórico.

#### Suposições

- Retirar `config.yaml` do índice preserva o arquivo em disco, de modo que a configuração local em uso não é afetada. Suposição reversível: se a remoção afetasse o arquivo, a entrega restauraria a cópia antes de prosseguir.
- A primeira consulta de um gabarito é representativa da base, por ter sido escrita para comprovar a recuperação daquela base.
- O texto neutro de degradação não precisa ser configurável nesta fatia; caso venha a precisar, a mudança é aditiva.

### 17. Decisões

- **DEC-001**: A identidade vem de `projeto.nome` e `projeto.descricao`, sem chave nova. Alternativa descartada: seção própria de persona, que sobreporia o BACKLOG-0010 e ampliaria a superfície de configuração.
- **DEC-002**: `documentos/` fica fora do escopo. A base sustenta o gabarito e o manifesto validados pela SPEC-0004, e alterá-la invalidaria evidência recém-obtida.
- **DEC-003**: `config.example.yaml` versionado e `config.yaml` no `.gitignore`, espelhando o par já adotado para segredos. Alternativa descartada: manter a configuração versionada com placeholders, que deixaria a cópia local permanentemente divergente do repositório.
- **DEC-004**: Duas guardas de regressão, com o caso positivo de derivação como principal. Uma lista de proibições sozinha não protege contra um cliente futuro; um caso positivo sozinho não vê literal fora do caminho exercitado.
- **DEC-005**: A pergunta padrão do demonstrativo vem da primeira consulta do gabarito, reaproveitando artefato existente em vez de introduzir um literal novo.
- **DEC-006**: A degradação é proporcional ao risco, com `projeto.nome` obrigatório e os demais campos degradando com aviso. As três ferramentas são somente leitura, e a política fail-closed do repositório protege mutação de estado remoto.
- **DEC-007**: A identidade derivada vive na camada de aplicação, junto do que já traduz configuração para os contratos, e não em `src/providers/`, restrito a adapters por PR-002.
- **DEC-008**: Os casos desta fatia ficam em arquivo próprio, `tests/test_client_neutrality.py`, seguindo a prática já adotada nas fatias anteriores para evitar que marcadores de specs distintas se misturem na contagem de cobertura.

### 18. Definition of Done

- [x] `Definition Gate` está `Passed`.
- [x] `Plan Gate` está `Passed`.
- [x] `Delivery Gate` está `Passed`.
- [x] Os quatorze cenários `AC` passam com casos TDD próprios.
- [x] Cada história, requisito funcional e requisito não funcional possui pelo menos três cenários e evidência executável.
- [x] Nenhum identificador de cliente permanece nas três ferramentas operacionais, por nome próprio ou conteúdo de domínio.
- [x] A identidade apresentada e o prompt são derivados da configuração, comprovado com configuração fictícia.
- [x] `config.yaml` não está no índice do Git e `config.example.yaml` versionado não contém cliente nem destino real.
- [x] A documentação de operação descreve a identidade derivada e publica o passo de cópia da configuração.
- [x] Pytest completo está verde e nenhuma dependência foi acrescentada.
- [x] `.specsfy/STACK.md` registra a configuração como o par `config.example.yaml` versionado e `config.yaml` local, substituindo a linha que hoje inventaria apenas `config.yaml`.
- [x] A documentação foi reconstruída com o monitor de contexto em `CURRENT`.

## Effort history

- 2026-09-02: 1 → 4. Promoção do BACKLOG-0004: além das oito ocorrências de texto, a fatia reestrutura a configuração versionada, cria duas guardas de naturezas diferentes e altera um teste documental existente.
